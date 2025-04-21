# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid
from typing import Optional # For type hinting

# LangChain Imports
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage # Keep for type hints if needed
from langchain_core.agents import AgentAction, AgentFinish
# -------------------------

# Project Imports
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
from backend.tools import agent_tools # WORKSPACE_ROOT not needed here now
from backend.agent import create_agent_executor
from backend.callbacks import WebSocketCallbackHandler
# *** ADDED Import for DB Utils ***
from backend.db_utils import init_db, add_task, add_message, get_messages_for_task
# ----------------------

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Settings, Initialize LLM (at startup) ---
# Keep LLM initialization global as it's usually stateless
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    logger.info("Base LLM initialized successfully.")
    # DB initialization moved to main() async context
except Exception as e:
    logger.critical(f"FATAL: Failed during startup initialization: {e}", exc_info=True); exit(1)

# --- Global state ---
connected_clients = {} # Maps session_id -> websocket
# Store agent executor, callback handler, and current_task_id per session ID
session_data = {} # Maps session_id -> {"agent_executor": AgentExecutor, "callback_handler": WebSocketCallbackHandler, "current_task_id": str | None}


# --- Helper: Read Stream from Subprocess (Used by direct run_command) ---
# Accepts send_ws_message_func and db_add_message_func to safely send messages/save logs
async def read_stream(stream, stream_name, session_id, send_ws_message_func, db_add_message_func, current_task_id):
    """Reads lines from a stream and sends them over WebSocket via the provided sender func."""
    log_prefix_base = f"[{session_id[:8]}]" # Base prefix for logs from this session
    while True:
        # Relying on send_ws_message_func to handle closed state is better
        try:
            line = await stream.readline()
        except Exception as e:
            logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}")
            break
        if not line:
            break # End of stream

        line_content = line.decode(errors='replace').rstrip()
        log_content = f"[{stream_name}] {line_content}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        # Use the passed-in sender function (which handles closed connections)
        await send_ws_message_func("monitor_log", f"[{timestamp}]{log_prefix_base} {log_content}")
        # Save to DB
        if current_task_id:
             # Log type distinguishes stdout/stderr, content is the line
             try:
                 await db_add_message_func(current_task_id, session_id, f"monitor_{stream_name}", line_content)
             except Exception as db_err:
                  logger.error(f"[{session_id}] Failed to save {stream_name} log to DB: {db_err}")
    logger.debug(f"[{session_id}] {stream_name} stream finished.")

# --- Helper: Execute Shell Command (Used only by direct run_command) ---
# Uses send_ws_message_func and db_add_message_func passed from handler
async def execute_shell_command(command: str, session_id, send_ws_message_func, db_add_message_func, current_task_id) -> bool:
    """Executes a shell command asynchronously and streams output via send_ws_message_func."""
    log_prefix_base = f"[{session_id[:8]}]"; timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    start_log_content = f"[Direct Command] Executing: {command}"
    logger.info(f"[{session_id}] {start_log_content}")
    await send_ws_message_func("monitor_log", f"[{timestamp_start}]{log_prefix_base} {start_log_content}")
    await send_ws_message_func("status_message", f"Running direct command: {command[:60]}...")
    # Save command start to DB
    if current_task_id:
        try: await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_start", command)
        except Exception as db_err: logger.error(f"[{session_id}] Failed to save direct cmd start to DB: {db_err}")

    process = None
    success = False # Default to failure
    status_msg = "failed"
    try:
        # Note: Runs from project root.
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        # Pass db_add_message_func and task_id to read_stream
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        await asyncio.gather(stdout_task, stderr_task)
        return_code = await process.wait(); success = return_code == 0; status_msg = "succeeded" if success else f"failed (Code: {return_code})"
    except FileNotFoundError: status_msg = "failed (Not Found)"; cmd_part = command.split()[0] if command else "Unknown"; logger.warning(f"[{session_id}] Direct command not found: {cmd_part}")
    except Exception as e: status_msg = f"failed ({type(e).__name__})"; logger.error(f"[{session_id}] Error running direct command '{command}': {e}", exc_info=True)
    finally:
         if process and process.returncode is None:
              try: process.terminate(); await process.wait(); logger.warning(f"[{session_id}] Terminated direct command process.")
              except: pass
         # Log final status
         timestamp_end = datetime.datetime.now().isoformat(timespec='milliseconds')
         finish_log_content = f"[Direct Command] Finished '{command[:60]}...', {status_msg}."
         await send_ws_message_func("monitor_log", f"[{timestamp_end}]{log_prefix_base} {finish_log_content}")
         if current_task_id:
             try: await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_end", f"Command: {command} | Status: {status_msg}")
             except Exception as db_err: logger.error(f"[{session_id}] Failed to save direct cmd end to DB: {db_err}")

         if not success and status_msg.startswith("failed"): await send_ws_message_func("status_message", f"Error: Direct command {status_msg}")

    return success


# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages for a user session."""
    session_id = str(uuid.uuid4())
    logger.info(f"Client connected from {websocket.remote_address}. Assigning Session ID: {session_id}")
    connected_clients[session_id] = websocket
    # Initialize current_task_id for this session
    current_task_id: Optional[str] = None # This will be set by context_switch

    # --- Helper to send messages safely (bound to this handler's websocket and session_id) ---
    async def send_ws_message(msg_type: str, content: str):
        # Check if the specific websocket for this handler is still connected and known
        # Relies on exception handling within the try block for closed connections
        if session_id in connected_clients and connected_clients[session_id] == websocket:
            try:
                await websocket.send(json.dumps({"type": msg_type, "content": content}))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"[{session_id}] WebSocket closed while trying to send message (in helper).")
                # Clean up immediately if detected closed during send
                if session_id in connected_clients: del connected_clients[session_id]
                if session_id in session_data: del session_data[session_id]
            except Exception as e:
                logger.error(f"[{session_id}] Error sending WebSocket message (in helper): {e}", exc_info=True)
        else:
             # Only log warning if we expected the client to be there
             # logger.warning(f"[{session_id}] Attempted to send message but WebSocket is not connected/valid in registry.")
             pass

    # --- Helper to add timestamped monitor log AND save to DB ---
    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"):
         timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
         log_prefix = f"[{timestamp}][{session_id[:8]}]"
         full_content = f"{log_prefix} {text}"
         await send_ws_message("monitor_log", full_content) # Send to UI
         # Save to DB if associated with a task
         # Use the 'current_task_id' tracked directly in the handler's scope
         if current_task_id: # Check if a task context is active
             try:
                 # Pass the handler-scoped current_task_id
                 await add_message(current_task_id, session_id, log_type, text) # Save original text
             except Exception as db_err:
                 logger.error(f"[{session_id}] Failed to save monitor log to DB for task {current_task_id}: {db_err}")
         #else: logger.debug(f"[{session_id}] Monitor log not saved to DB (no active task).") # Optional debug

    # --- Create Session-Specific Memory, Callback Handler, and Agent ---
    agent_executor: AgentExecutor = None # Initialize
    ws_callback_handler: WebSocketCallbackHandler = None
    try:
        memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
        )
        # Pass the database add_message function (imported from db_utils) to the callback handler
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message, add_message)

        # Create agent executor, passing memory
        agent_executor = create_agent_executor(llm, agent_tools, memory)
        # Store executor, handler, and initialize current_task_id
        session_data[session_id] = {
            "agent_executor": agent_executor,
            "callback_handler": ws_callback_handler,
            "current_task_id": None # Start with no task selected for this session
        }
        logger.info(f"[{session_id}] Created AgentExecutor with session memory and WebSocket callback handler.")
    except Exception as e:
        logger.error(f"[{session_id}] Failed to create agent/memory/callback for session: {e}", exc_info=True)
        try: await websocket.close(code=1011, reason="Agent setup failed") # Attempt to notify client
        except: pass # Ignore errors if already closed
        if session_id in connected_clients: del connected_clients[session_id] # Clean up client entry
        # Don't clean session_data here, it wasn't fully added
        return # End handler for this connection


    # --- Main Try Block for Handler ---
    try:
        # Send initial connection messages
        await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready with LLM: {settings.ai_provider}.")
        await add_monitor_log_and_save(f"New client connection: {websocket.remote_address}", "system_connect") # Uses helper

        # --- Message Processing Loop ---
        async for message in websocket:
            logger.info(f"[{session_id}] Received message: {message}")
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content") # Used by user_message
                task_id_from_frontend = data.get("taskId") # Sent by context_switch
                task_title_from_frontend = data.get("task") # Sent by context_switch

                # Update current task ID for the session based on frontend messages
                if message_type == "context_switch" and task_id_from_frontend:
                     current_task_id = task_id_from_frontend # Update handler's tracked task ID
                     if session_id in session_data:
                         session_data[session_id]["current_task_id"] = current_task_id
                         # Also update the task ID in the callback handler instance
                         session_data[session_id]["callback_handler"].set_task_id(current_task_id)
                         # Lazily add task to DB if it doesn't exist (using IGNORE)
                         await add_task(task_id_from_frontend, task_title_from_frontend or f"Task {task_id_from_frontend}", datetime.datetime.now(datetime.timezone.utc).isoformat())
                         await add_monitor_log_and_save(f"Switched context to task ID: {current_task_id} ('{task_title_from_frontend}')", "system_context_switch")
                         # Clear memory for the new task context
                         if "agent_executor" in session_data[session_id]:
                             try:
                                 session_data[session_id]["agent_executor"].memory.clear()
                                 logger.info(f"[{session_id}] Cleared conversation memory for agent.")
                                 await send_ws_message("status_message", "Context cleared. Ready for task.")
                             except Exception as mem_e: logger.error(f"[{session_id}] Failed to clear memory: {mem_e}"); await send_ws_message("status_message", "Error clearing memory.")
                         # TODO (Phase 2): Load history for this task_id here
                     else:
                          logger.error(f"[{session_id}] Received context_switch but session data missing!")


                elif message_type == "new_task":
                     # Frontend handles creating task in UI/localStorage.
                     # Backend just clears context here. Selection via context_switch sets the active task.
                     current_task_id = None # No task active until selected
                     if session_id in session_data:
                         session_data[session_id]["current_task_id"] = None
                         session_data[session_id]["callback_handler"].set_task_id(None)
                         if "agent_executor" in session_data[session_id]: session_data[session_id]["agent_executor"].memory.clear()
                     await add_monitor_log_and_save("Received 'new_task'. Cleared context.", "system_new_task")
                     await send_ws_message("status_message", "Ready for new task goal.")


                # --- USER MESSAGE -> Trigger Agent ---
                elif message_type == "user_message":
                    # Use the task_id tracked in the handler's scope
                    active_task_id = current_task_id # Use the variable directly available in this scope
                    if not active_task_id:
                         logger.warning(f"[{session_id}] Received user message but no task is active.")
                         await send_ws_message("status_message", "Please select or create a task first.")
                         continue # Skip processing

                    # Save user message to DB
                    await add_message(active_task_id, session_id, "user", content)
                    await add_monitor_log_and_save(f"Received user input: {content}", "user_input") # Log receipt
                    await send_ws_message("status_message", f"Processing input: '{content[:60]}...'")

                    if session_id not in session_data: continue # Safety check

                    current_agent_executor = session_data[session_id]["agent_executor"]
                    current_callback_handler = session_data[session_id]["callback_handler"]

                    try:
                        # Run agent asynchronously with the callback handler
                        async for chunk in current_agent_executor.astream_log(
                            {"input": content}, # Pass input to the agent
                            config={"callbacks": [current_callback_handler]}, # Crucial for WS updates & DB saving
                        ):
                            # Callbacks handle UI updates and DB saving for tool/LLM/finish events
                            pass # Just consume the stream

                        # Log stream completion (Callback handler handles final answer message)
                        await add_monitor_log_and_save("Agent stream finished.", "system_agent_end")

                    except Exception as e:
                        # Handle errors during the agent execution itself
                        error_msg = f"CRITICAL Error during agent execution: {e}"
                        logger.error(f"[{session_id}] {error_msg}", exc_info=True)
                        await add_monitor_log_and_save(error_msg, "error_agent") # Save error log
                        await send_ws_message("status_message", "Error during task processing.")
                        # Send specific error to user if helpful, otherwise generic
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred while processing your request: {type(e).__name__}")
                        # Save agent error message to DB
                        if active_task_id: # Ensure task id exists before saving error
                            await add_message(active_task_id, session_id, "error_agent", f"{type(e).__name__}: {e}")


                # --- Other message types ---
                elif message_type == "run_command": # Direct command execution
                     command = data.get("command")
                     active_task_id = current_task_id # Get current task for logging
                     await add_monitor_log_and_save(f"Received direct 'run_command'. Executing: {command}", "system_direct_cmd")
                     if command:
                          # Pass add_message for logging within execute_shell_command
                          await execute_shell_command(command, session_id, send_ws_message, add_message, active_task_id)
                     else:
                          await add_monitor_log_and_save("Error: Received 'run_command' with no command.", "error_direct_cmd")

                elif message_type == "action_command": # Placeholder for UI actions
                     await add_monitor_log_and_save(f"Received action command: {data.get('command')} (Not implemented).", "system_action_cmd")

                # Note: new_task and context_switch handled above before user_message check

                else: # Unknown message type
                     logger.warning(f"[{session_id}] Unknown message type received: {message_type}")
                     await add_monitor_log_and_save(f"Received unknown message type: {message_type}", "error_unknown_msg")

            # --- Error handling for message processing ---
            except json.JSONDecodeError:
                 logger.error(f"[{session_id}] Non-JSON message: {message}")
                 await add_monitor_log_and_save("Error: Received invalid message format.", "error_json")
            except Exception as e:
                 logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                 await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing")

    # --- Connection Closed Handling ---
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client disconnected: {websocket.remote_address} (Session: {session_id})")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"Connection closed error: {websocket.remote_address} (Session: {session_id}) - {e}")
    except Exception as e:
        # Catch any unexpected errors in the handler's main try block
        logger.error(f"Unhandled error in handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
        # Try to inform client if possible before cleaning up
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass # Ignore errors during close if already closed
    finally:
        # --- Cleanup session data on disconnect ---
        logger.info(f"Cleaning up for session {session_id}")
        if session_id in connected_clients:
            del connected_clients[session_id]
        if session_id in session_data:
            # Potentially add cleanup for agent resources if needed (e.g., closing browser for playwright)
            del session_data[session_id]
            logger.info(f"Cleaned up session data for {session_id}.")
        logger.info(f"Client removed: {websocket.remote_address} (Session: {session_id})")


async def main():
    host = "localhost"; port = 8765;
    logger.info("Initializing database...")
    # *** Initialize DB within the async main function ***
    await init_db()
    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        # Setup logging only if run directly
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
    except Exception as e:
        # Log critical errors during startup
        logger.critical(f"Server failed to start or encountered critical error: {e}", exc_info=True)

