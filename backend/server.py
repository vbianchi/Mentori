# backend/server.py
# ... (imports remain the same) ...
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage
from langchain_core.agents import AgentAction, AgentFinish
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
from backend.tools import agent_tools
from backend.agent import create_agent_executor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ... (Load Settings, Initialize LLM remain the same) ...
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    logger.info("Base LLM initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Failed during LLM setup: {e}", exc_info=True)
    exit(1)

connected_clients = {}
session_data = {}

# --- Helper: Read Stream from Subprocess ---
async def read_stream(stream, stream_name, session_id, send_ws_message_func):
    """Reads lines from a stream and sends them over WebSocket via the provided sender func."""
    log_prefix_base = f"[{session_id[:8]}]"
    while True:
        # ... (Connection check removed as send_ws_message_func handles it) ...
        try:
            line = await stream.readline()
        except Exception as e:
            logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}")
            break
        if not line: break

        log_content = f"[{stream_name}] {line.decode(errors='replace').rstrip()}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        full_log_msg = f"[{timestamp}]{log_prefix_base} {log_content}"

        # *** ADDED LOGGING BEFORE SEND ***
        logger.info(f"[{session_id}] Attempting to send monitor_log (from read_stream): {log_content[:100]}...")
        await send_ws_message_func("monitor_log", full_log_msg)

    logger.debug(f"[{session_id}] {stream_name} stream finished.")


# --- Helper: Execute Shell Command ---
async def execute_shell_command(command: str, session_id, send_ws_message_func) -> bool:
    """Executes a shell command asynchronously and streams output via send_ws_message_func."""
    log_prefix_base = f"[{session_id[:8]}]"
    timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    logger.info(f"[{session_id}] Executing command: {command}")
    start_log_msg = f"[{timestamp_start}]{log_prefix_base} [Command] Executing: {command}"
    status_start_msg = f"Running: {command[:60]}..."

    # *** ADDED LOGGING BEFORE SEND ***
    logger.info(f"[{session_id}] Attempting to send monitor_log: {start_log_msg}")
    await send_ws_message_func("monitor_log", start_log_msg)
    logger.info(f"[{session_id}] Attempting to send status_message: {status_start_msg}")
    await send_ws_message_func("status_message", status_start_msg)

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
        finish_log_msg = f"[{timestamp_end}]{log_prefix_base} [Command] Finished '{command[:60]}...', {status_msg}."

        # *** ADDED LOGGING BEFORE SEND ***
        logger.info(f"[{session_id}] Attempting to send monitor_log: {finish_log_msg}")
        await send_ws_message_func("monitor_log", finish_log_msg)
        return success

    except FileNotFoundError:
        # ... (error handling with logging before send) ...
        cmd_part = command.split()[0] if command else "Unknown"
        timestamp_err = datetime.datetime.now().isoformat(timespec='milliseconds')
        error_log_msg = f"[{timestamp_err}]{log_prefix_base} [Command Error] Command not found: {cmd_part}"
        error_status_msg = f"Error: Command not found."
        logger.info(f"[{session_id}] Attempting to send monitor_log: {error_log_msg}")
        await send_ws_message_func("monitor_log", error_log_msg)
        logger.info(f"[{session_id}] Attempting to send status_message: {error_status_msg}")
        await send_ws_message_func("status_message", error_status_msg)
        return False
    except Exception as e:
        # ... (error handling with logging before send) ...
        timestamp_err = datetime.datetime.now().isoformat(timespec='milliseconds')
        logger.error(f"[{session_id}] Error running command '{command}': {e}", exc_info=True)
        error_log_msg = f"[{timestamp_err}]{log_prefix_base} [Command Error] Error running command: {e}"
        error_status_msg = f"Error executing command."
        logger.info(f"[{session_id}] Attempting to send monitor_log: {error_log_msg}")
        await send_ws_message_func("monitor_log", error_log_msg)
        logger.info(f"[{session_id}] Attempting to send status_message: {error_status_msg}")
        await send_ws_message_func("status_message", error_status_msg)
        return False
    finally:
         # ... (process termination logic) ...
         if process and process.returncode is None:
              try:
                   process.terminate(); await process.wait()
                   logger.warning(f"[{session_id}] Terminated command process.")
              except: pass # Ignore errors during cleanup


# --- WebSocket Handler ---
async def handler(websocket):
    session_id = str(uuid.uuid4())
    logger.info(f"Client connected from {websocket.remote_address}. Assigning Session ID: {session_id}")
    connected_clients[session_id] = websocket

    # --- Create Session-Specific Memory and Agent ---
    try:
        memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
        )
        agent_executor: AgentExecutor = create_agent_executor(llm, agent_tools, memory)
        session_data[session_id] = {"memory": memory, "agent_executor": agent_executor}
        logger.info(f"[{session_id}] Created AgentExecutor with session memory.")
    except Exception as e:
        logger.error(f"[{session_id}] Failed to create agent/memory for session: {e}", exc_info=True)
        try: await websocket.close(code=1011, reason="Agent setup failed")
        except: pass
        if session_id in connected_clients: del connected_clients[session_id]
        return

    # --- Helper to send messages safely ---
    async def send_ws_message(msg_type: str, content: str):
        if session_id in connected_clients and connected_clients[session_id] == websocket:
            try:
                await websocket.send(json.dumps({"type": msg_type, "content": content}))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"[{session_id}] WebSocket closed while trying to send message (in helper).")
            except Exception as e:
                logger.error(f"[{session_id}] Error sending WebSocket message (in helper): {e}", exc_info=True)
        else:
             logger.warning(f"[{session_id}] Attempted to send message but WebSocket is not connected/valid in registry.")

    # --- Helper to add timestamped monitor log ---
    async def add_monitor_log(text: str):
         timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
         log_prefix = f"[{timestamp}][{session_id[:8]}]"
         # *** ADDED LOGGING BEFORE SEND ***
         logger.info(f"[{session_id}] Attempting to send monitor_log (via helper): {text[:100]}...")
         await send_ws_message("monitor_log", f"{log_prefix} {text}")

    try:
        # --- Initial connection messages ---
        await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready with LLM: {settings.ai_provider}.")
        await add_monitor_log(f"New client connection: {websocket.remote_address}") # Uses helper which logs attempt

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
                         logger.error(f"[{session_id}] Session data not found!")
                         await send_ws_message("status_message", "Error: Session data lost. Please reconnect.")
                         await websocket.close(code=1011, reason="Session data lost")
                         continue

                    current_agent_executor = session_data[session_id]["agent_executor"]

                    try:
                        final_answer_text = None # Reset for each run
                        async for chunk in current_agent_executor.astream_log(
                            {"input": content},
                            include_names=["ChatGoogleGenerativeAI", "Ollama", "ShellTool"]
                        ):
                            for op in chunk.ops:
                                path = op.get("path")
                                value = op.get("value")
                                if not path or value is None: continue

                                # Log Tool Usage Details to Monitor
                                if "/logs/ShellTool" in path:
                                    if path.endswith("/streamed_output_str") and "/final_output" not in path:
                                        tool_input = value if isinstance(value, str) else json.dumps(value)
                                        await add_monitor_log(f"[Tool Start] Agent requesting ShellTool with input: '{tool_input}'") # Uses helper
                                        await send_ws_message("status_message", f"Agent running shell command...")
                                    elif path.endswith("/final_output"):
                                        # Stdout/err was already streamed by read_stream called by execute_shell_command
                                        await add_monitor_log(f"[Tool End] ShellTool invocation finished.") # Uses helper
                                        await send_ws_message("status_message", "Agent finished shell command.")

                                # Attempt to Extract Final Answer
                                elif path == "/final_output":
                                    # ... (final answer parsing logic remains the same) ...
                                    logger.debug(f"[{session_id}] Raw final_output chunk value: {value}")
                                    parsed_answer = None
                                    if isinstance(value, dict):
                                        if "output" in value: parsed_answer = value["output"]
                                        elif "return_values" in value and isinstance(value.get("return_values"), dict) and "output" in value["return_values"]: parsed_answer = value["return_values"]["output"]
                                        elif isinstance(value.get("actions"), list) and value["actions"] and isinstance(value["actions"][0], AgentFinish): parsed_answer = value["actions"][0].return_values.get("output")
                                    elif isinstance(value, str): parsed_answer = value
                                    elif isinstance(value, AgentFinish): parsed_answer = value.return_values.get("output")

                                    if isinstance(parsed_answer, str):
                                        final_answer_text = parsed_answer
                                        logger.info(f"[{session_id}] Agent final answer extracted: {final_answer_text}")
                                        await send_ws_message("agent_message", f"{final_answer_text}")
                                        await send_ws_message("status_message", "Task processing complete.")
                                    else:
                                        logger.warning(f"[{session_id}] Could not extract text from final_output chunk. Value: {value}")
                                        final_answer_text = "Processing complete. See Monitor panel for execution details."

                        # After Stream Ends
                        await add_monitor_log("Agent stream finished.") # Uses helper
                        if final_answer_text == "Processing complete. See Monitor panel for execution details." or final_answer_text is None:
                             logger.info(f"[{session_id}] Sending fallback final answer message.")
                             await send_ws_message("agent_message", "Processing complete. See Monitor panel for execution details.")
                             await send_ws_message("status_message", "Task processing complete (check monitor).")

                    except Exception as e:
                        # ... (Agent execution error handling) ...
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
                # ... (new_task, context_switch, action_command, unknown type remain the same, using helpers where appropriate) ...
                elif message_type == "new_task" or message_type == "context_switch":
                     if session_id in session_data: session_data[session_id]["memory"].clear(); logger.info(f"[{session_id}] Cleared memory.")
                     await add_monitor_log(f"Received '{message_type}'. Memory cleared."); await send_ws_message("status_message", "Memory cleared. Ready for new task.")
                elif message_type == "action_command":
                     await add_monitor_log(f"Received action command: {data.get('command')} (Not implemented).")
                else:
                     logger.warning(f"[{session_id}] Unknown message type: {message_type}"); await add_monitor_log(f"Received unknown message type: {message_type}")

            # ... (Message parsing / generic error handling) ...
            except json.JSONDecodeError: logger.error(f"[{session_id}] Non-JSON message: {message}"); await add_monitor_log("Error: Received non-JSON message.")
            except Exception as e: logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True); await add_monitor_log(f"Error processing message: {e}")

    # --- Connection Closed Handling ---
    # ... (remain the same) ...
    except websockets.exceptions.ConnectionClosedOK: logger.info(f"Client disconnected: {websocket.remote_address} (Session: {session_id})")
    except websockets.exceptions.ConnectionClosedError as e: logger.warning(f"Connection closed error: {websocket.remote_address} (Session: {session_id}) - {e}")
    except Exception as e: logger.error(f"Unhandled error in handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
    finally: # Cleanup
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}")


async def main():
    # ... (main function remains the same) ...
    host = "localhost"; port = 8765; logger.info(f"Starting WebSocket server on ws://{host}:{port}");
    async with websockets.serve(handler, host, port): await asyncio.Future()

if __name__ == "__main__":
    # ... (__main__ block remains the same) ...
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt: logger.info("Server stopped manually.")
    except Exception as e: logger.critical(f"Server failed to start: {e}", exc_info=True)

