# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid

# --- LangChain Imports ---
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage # Keep for type hints if needed
from langchain_core.agents import AgentAction, AgentFinish
# -------------------------

# --- Project Imports ---
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
from backend.tools import agent_tools
from backend.agent import create_agent_executor
# *** Import the Callback Handler ***
from backend.callbacks import WebSocketCallbackHandler
# ----------------------

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Settings, Initialize LLM (at startup) ---
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    logger.info("Base LLM initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Failed during LLM setup: {e}", exc_info=True)
    exit(1) # Exit if core components fail to initialize

# --- Global state for connections and sessions ---
connected_clients = {} # Maps session_id -> websocket
session_data = {} # Maps session_id -> {"agent_executor": AgentExecutor, "callback_handler": WebSocketCallbackHandler}

# --- Helper: Read Stream from Subprocess (Used by direct run_command) ---
async def read_stream(stream, stream_name, session_id, send_ws_message_func):
    """Reads lines from a stream and sends them over WebSocket via the provided sender func."""
    log_prefix_base = f"[{session_id[:8]}]"
    while True:
        try:
            line = await stream.readline()
        except Exception as e:
            logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}")
            break
        if not line:
            break # End of stream

        log_content = f"[{stream_name}] {line.decode(errors='replace').rstrip()}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        # Use the passed-in sender function (which handles closed connections)
        await send_ws_message_func("monitor_log", f"[{timestamp}]{log_prefix_base} {log_content}")

    logger.debug(f"[{session_id}] {stream_name} stream finished.")

# --- Helper: Execute Shell Command (Used by direct run_command) ---
async def execute_shell_command(command: str, session_id, send_ws_message_func) -> bool:
    """Executes a shell command asynchronously and streams output via send_ws_message_func."""
    log_prefix_base = f"[{session_id[:8]}]"
    timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    logger.info(f"[{session_id}] Direct Execute command: {command}")
    await send_ws_message_func("monitor_log", f"[{timestamp_start}]{log_prefix_base} [Direct Command] Executing: {command}")
    await send_ws_message_func("status_message", f"Running direct command: {command[:60]}...")
    process = None
    try:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        # Pass the sender function down to read_stream
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout", session_id, send_ws_message_func))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr", session_id, send_ws_message_func))
        await asyncio.gather(stdout_task, stderr_task)

        return_code = await process.wait()
        success = return_code == 0
        status_msg = "succeeded" if success else f"failed (Code: {return_code})"
        timestamp_end = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message_func("monitor_log", f"[{timestamp_end}]{log_prefix_base} [Direct Command] Finished '{command[:60]}...', {status_msg}.")
        return success
    except FileNotFoundError:
        cmd_part = command.split()[0] if command else "Unknown"; timestamp_err = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message_func("monitor_log", f"[{timestamp_err}]{log_prefix_base} [Direct Command Error] Command not found: {cmd_part}"); await send_ws_message_func("status_message", f"Error: Command not found."); return False
    except Exception as e:
        timestamp_err = datetime.datetime.now().isoformat(timespec='milliseconds'); logger.error(f"[{session_id}] Error running direct command '{command}': {e}", exc_info=True)
        await send_ws_message_func("monitor_log", f"[{timestamp_err}]{log_prefix_base} [Direct Command Error] Error running command: {e}"); await send_ws_message_func("status_message", f"Error executing direct command."); return False
    finally:
         if process and process.returncode is None:
              try: process.terminate(); await process.wait(); logger.warning(f"[{session_id}] Terminated direct command process.")
              except: pass


# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    session_id = str(uuid.uuid4())
    logger.info(f"Client connected from {websocket.remote_address}. Assigning Session ID: {session_id}")
    connected_clients[session_id] = websocket

    # --- Helper to send messages safely (bound to this handler's websocket and session_id) ---
    async def send_ws_message(msg_type: str, content: str):
        # Check if the specific websocket for this handler is still connected and known
        # Relies on exception handling for closed connections now, removed .closed check
        if session_id in connected_clients and connected_clients[session_id] == websocket:
            try:
                await websocket.send(json.dumps({"type": msg_type, "content": content}))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"[{session_id}] WebSocket closed while trying to send message (in helper).")
            except Exception as e:
                logger.error(f"[{session_id}] Error sending WebSocket message (in helper): {e}", exc_info=True)
        else:
             logger.warning(f"[{session_id}] Attempted to send message but WebSocket is not connected/valid in registry.")

    # --- Helper to add timestamped monitor log (uses safe sender) ---
    async def add_monitor_log(text: str):
         timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
         log_prefix = f"[{timestamp}][{session_id[:8]}]"
         await send_ws_message("monitor_log", f"{log_prefix} {text}")

    # --- Create Session-Specific Memory, Callback Handler, and Agent ---
    agent_executor: AgentExecutor = None
    try:
        memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
        )
        # Create Callback Handler for this session, passing the sender function
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message)

        # Create agent executor, passing memory
        agent_executor = create_agent_executor(llm, agent_tools, memory)
        # Store executor and handler (memory is implicitly managed by executor)
        session_data[session_id] = {"agent_executor": agent_executor, "callback_handler": ws_callback_handler}
        logger.info(f"[{session_id}] Created AgentExecutor with session memory and WebSocket callback handler.")

    except Exception as e:
        logger.error(f"[{session_id}] Failed to create agent/memory/callback for session: {e}", exc_info=True)
        try: await websocket.close(code=1011, reason="Agent setup failed")
        except: pass
        if session_id in connected_clients: del connected_clients[session_id]
        return

    try:
        await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready with LLM: {settings.ai_provider}.")
        await add_monitor_log(f"New client connection: {websocket.remote_address}") # Uses helper

        # --- Message Processing Loop ---
        async for message in websocket:
            logger.info(f"[{session_id}] Received message: {message}")
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                if message_type == "user_message":
                    await add_monitor_log(f"Received user input: {content}") # Uses helper
                    await send_ws_message("status_message", f"Processing input: '{content[:60]}...'")

                    if session_id not in session_data: # Safety check
                         logger.error(f"[{session_id}] Session data missing!"); await send_ws_message("status_message", "Error: Session lost."); await websocket.close(1011); continue

                    current_agent_executor = session_data[session_id]["agent_executor"]
                    current_callback_handler = session_data[session_id]["callback_handler"]

                    try:
                        # --- Run agent with callback handler ---
                        # Callbacks handle tool logs and final answer sending
                        # Use invoke for single output or stream/astream for chunks
                        # astream_log gives most detail including intermediate steps
                        async for chunk in current_agent_executor.astream_log(
                            {"input": content},
                            config={"callbacks": [current_callback_handler]}, # Pass handler
                            include_names=["ShellTool"] # Optional: Filter logs if needed
                        ):
                            # We primarily rely on callbacks now, but could process
                            # intermediate LLM thoughts from the stream here if desired.
                            pass # Consume the stream

                        # --- After Stream Ends ---
                        # Final status/logging is handled within on_agent_finish callback
                        await add_monitor_log("Agent stream finished.") # Uses helper

                    except Exception as e:
                        logger.error(f"[{session_id}] Error during agent execution: {e}", exc_info=True)
                        await add_monitor_log(f"CRITICAL Error during agent execution: {e}") # Uses helper
                        await send_ws_message("status_message", "Error during task processing.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred: {e}")


                # --- Other message types ---
                elif message_type == "run_command": # Direct command execution
                     command = data.get("command")
                     await add_monitor_log(f"Received direct 'run_command'. Executing: {command}") # Uses helper
                     if command:
                          # Call execute_shell_command directly, passing the handler's send_ws_message
                          await execute_shell_command(command, session_id, send_ws_message)
                     else:
                          await add_monitor_log("Error: Received 'run_command' with no command.") # Uses helper
                elif message_type == "new_task" or message_type == "context_switch":
                     if session_id in session_data: session_data[session_id]["memory"].clear(); logger.info(f"[{session_id}] Cleared memory.")
                     await add_monitor_log(f"Received '{message_type}'. Memory cleared."); await send_ws_message("status_message", "Memory cleared. Ready for new task.") # Uses helper
                elif message_type == "action_command":
                     await add_monitor_log(f"Received action command: {data.get('command')} (Not implemented).") # Uses helper
                else:
                     logger.warning(f"[{session_id}] Unknown message type: {message_type}"); await add_monitor_log(f"Received unknown message type: {message_type}") # Uses helper

            except json.JSONDecodeError: logger.error(f"[{session_id}] Non-JSON message: {message}"); await add_monitor_log("Error: Received non-JSON message.") # Uses helper
            except Exception as e: logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True); await add_monitor_log(f"Error processing message: {e}") # Uses helper

    # --- Connection Closed Handling ---
    except websockets.exceptions.ConnectionClosedOK: logger.info(f"Client disconnected: {websocket.remote_address} (Session: {session_id})")
    except websockets.exceptions.ConnectionClosedError as e: logger.warning(f"Connection closed error: {websocket.remote_address} (Session: {session_id}) - {e}")
    except Exception as e: logger.error(f"Unhandled error in handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
    finally: # Cleanup
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}")


async def main():
    host = "localhost"; port = 8765; logger.info(f"Starting WebSocket server on ws://{host}:{port}");
    async with websockets.serve(handler, host, port): await asyncio.Future()

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt: logger.info("Server stopped manually.")
    except Exception as e: logger.critical(f"Server failed to start: {e}", exc_info=True)