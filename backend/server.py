# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path # Import Path
import os # Import os

# --- Web Server Imports ---
from aiohttp import web
# *** CORRECTED IMPORT for FileResponse ***
from aiohttp.web import FileResponse
# -------------------------

# LangChain Imports
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage
from langchain_core.agents import AgentAction, AgentFinish
# Import RunnableConfig
from langchain_core.runnables import RunnableConfig
# -------------------------

# Project Imports
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
# Import the factory function and helpers
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT
from backend.agent import create_agent_executor
from backend.callbacks import WebSocketCallbackHandler
# Import DB Utils
from backend.db_utils import init_db, add_task, add_message, get_messages_for_task, delete_task_and_messages
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
    logger.critical(f"FATAL: Failed during startup initialization: {e}", exc_info=True); exit(1)

# --- Global state ---
connected_clients = {} # Maps session_id -> websocket
session_data = {} # Maps session_id -> {"memory": BaseMemory, "callback_handler": WebSocketCallbackHandler, "current_task_id": str | None}

# --- File Server Constants ---
FILE_SERVER_HOST = "localhost"
FILE_SERVER_PORT = 8766 # Different port from WebSocket

# --- Helper: Read Stream from Subprocess ---
async def read_stream(stream, stream_name, session_id, send_ws_message_func, db_add_message_func, current_task_id):
    """Reads lines from a stream and sends them over WebSocket via the provided sender func."""
    log_prefix_base = f"[{session_id[:8]}]"
    while True:
        try:
            line = await stream.readline()
        except Exception as e:
            logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}")
            break
        if not line: break

        line_content = line.decode(errors='replace').rstrip()
        log_content = f"[{stream_name}] {line_content}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message_func("monitor_log", f"[{timestamp}]{log_prefix_base} {log_content}")

        # Save to DB
        if current_task_id:
             try:
                 await db_add_message_func(current_task_id, session_id, f"monitor_{stream_name}", line_content)
             except Exception as db_err:
                  logger.error(f"[{session_id}] Failed to save {stream_name} log to DB: {db_err}")
    logger.debug(f"[{session_id}] {stream_name} stream finished.")

# --- Helper: Execute Shell Command ---
async def execute_shell_command(command: str, session_id, send_ws_message_func, db_add_message_func, current_task_id) -> bool:
    """Executes a shell command asynchronously and streams output via send_ws_message_func."""
    log_prefix_base = f"[{session_id[:8]}]"; timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    start_log_content = f"[Direct Command] Executing: {command}"
    logger.info(f"[{session_id}] {start_log_content}")
    await send_ws_message_func("monitor_log", f"[{timestamp_start}]{log_prefix_base} {start_log_content}")
    await send_ws_message_func("status_message", f"Running direct command: {command[:60]}...")

    # Save command start to DB
    if current_task_id:
        try:
            await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_start", command)
        except Exception as db_err:
            logger.error(f"[{session_id}] Failed to save direct cmd start to DB: {db_err}")

    process = None; success = False; status_msg = "failed"
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        await asyncio.gather(stdout_task, stderr_task)
        return_code = await process.wait(); success = return_code == 0; status_msg = "succeeded" if success else f"failed (Code: {return_code})"
    except FileNotFoundError: status_msg = "failed (Not Found)"; cmd_part = command.split()[0] if command else "Unknown"; logger.warning(f"[{session_id}] Direct command not found: {cmd_part}")
    except Exception as e: status_msg = f"failed ({type(e).__name__})"; logger.error(f"[{session_id}] Error running direct command '{command}': {e}", exc_info=True)
    finally:
         # Ensure process termination block is indented
         if process and process.returncode is None:
              try:
                  process.terminate()
                  await process.wait()
                  logger.warning(f"[{session_id}] Terminated direct command process.")
              except Exception as term_e:
                  logger.error(f"[{session_id}] Error terminating process: {term_e}")
                  pass # Ignore errors during cleanup termination

         # Log final status
         timestamp_end = datetime.datetime.now().isoformat(timespec='milliseconds')
         finish_log_content = f"[Direct Command] Finished '{command[:60]}...', {status_msg}."
         await send_ws_message_func("monitor_log", f"[{timestamp_end}]{log_prefix_base} {finish_log_content}")

         # Save command end to DB
         if current_task_id:
             try:
                 await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_end", f"Command: {command} | Status: {status_msg}")
             except Exception as db_err:
                 logger.error(f"[{session_id}] Failed to save direct cmd end to DB: {db_err}")

         if not success and status_msg.startswith("failed"): await send_ws_message_func("status_message", f"Error: Direct command {status_msg}")

    return success


# --- File Server Handler ---
async def handle_workspace_file(request: web.Request) -> web.Response:
    """aiohttp handler to serve files from the workspace."""
    task_id = request.match_info.get('task_id')
    filename = request.match_info.get('filename')
    session_id = request.headers.get("X-Session-ID", "unknown") # Optional: Pass session ID if needed for logging

    if not task_id or not filename:
        logger.warning(f"[{session_id}] File server request missing task_id or filename.")
        raise web.HTTPBadRequest(text="Task ID and filename required")

    # **Security:** Basic validation to prevent path traversal
    if ".." in task_id or "/" in task_id or "\\" in task_id or \
       ".." in filename or "/" in filename or "\\" in filename:
        logger.error(f"[{session_id}] Invalid characters or path traversal attempt in file request: task='{task_id}', file='{filename}'")
        raise web.HTTPForbidden(text="Invalid path components")

    # Construct the full path relative to the base workspace
    # Use the helper to ensure the task directory exists conceptually
    task_workspace = get_task_workspace_path(task_id)
    file_path = (task_workspace / filename).resolve()

    # **Security:** Double-check the resolved path is still within the BASE_WORKSPACE_ROOT
    try:
        # Check if file_path is within BASE_WORKSPACE_ROOT
        if not file_path.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
             logger.error(f"[{session_id}] Security Error: Attempt to access file outside base workspace! Requested: {file_path}, Base: {BASE_WORKSPACE_ROOT.resolve()}")
             raise web.HTTPForbidden(text="Access denied")
    except ValueError: # is_relative_to raises ValueError if paths are on different drives (Windows)
        logger.error(f"[{session_id}] Security Error: Path comparison failed (different drives?). Requested: {file_path}")
        raise web.HTTPForbidden(text="Access denied")
    except Exception as e: # Catch other potential errors
        logger.error(f"[{session_id}] Security Error: Unexpected error validating path: {e}. Requested: {file_path}", exc_info=True)
        raise web.HTTPInternalServerError(text="Error validating file path")


    if not file_path.is_file():
        logger.warning(f"[{session_id}] File not found request: {file_path}")
        raise web.HTTPNotFound(text=f"File not found: {filename}")

    logger.info(f"[{session_id}] Serving file: {file_path}")
    # Use FileResponse for efficient serving
    return FileResponse(path=file_path)


# --- Setup File Server ---
async def setup_file_server():
    """Sets up and returns the aiohttp file server runner."""
    app = web.Application()
    # Route to serve files: /workspace_files/{task_id}/{filename}
    app.router.add_get('/workspace_files/{task_id}/{filename}', handle_workspace_file)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, FILE_SERVER_HOST, FILE_SERVER_PORT)
    logger.info(f"Starting file server on http://{FILE_SERVER_HOST}:{FILE_SERVER_PORT}")
    return site, runner


# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages for a user session."""
    session_id = str(uuid.uuid4())
    logger.info(f"Client connected from {websocket.remote_address}. Assigning Session ID: {session_id}")
    connected_clients[session_id] = websocket
    # current_task_id is now stored in session_data

    # --- Helper to send messages safely ---
    async def send_ws_message(msg_type: str, content: Any): # Allow Any content for image display
        if session_id in connected_clients and connected_clients[session_id] == websocket:
            try: await websocket.send(json.dumps({"type": msg_type, "content": content}))
            except websockets.exceptions.ConnectionClosed: logger.warning(f"[{session_id}] WS closed trying to send."); # Cleanup handled in finally
            except Exception as e: logger.error(f"[{session_id}] Error sending WS message: {e}", exc_info=True)

    # --- Helper to add timestamped monitor log AND save to DB ---
    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"):
         timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
         log_prefix = f"[{timestamp}][{session_id[:8]}]"
         full_content = f"{log_prefix} {text}"
         await send_ws_message("monitor_log", full_content)
         active_task_id = session_data.get(session_id, {}).get("current_task_id")
         if active_task_id:
             try: await add_message(active_task_id, session_id, log_type, text);
             except Exception as db_err: logger.error(f"[{session_id}] Failed to save monitor log to DB: {db_err}")

    # --- Create Session-Specific Memory and Callback Handler ---
    ws_callback_handler: WebSocketCallbackHandler = None
    memory: ConversationBufferWindowMemory = None
    try:
        memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True)
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message, add_message)
        session_data[session_id] = {"memory": memory, "callback_handler": ws_callback_handler, "current_task_id": None}
        logger.info(f"[{session_id}] Created session memory and WebSocket callback handler.")
    except Exception as e:
        logger.error(f"[{session_id}] Failed to create memory/callback: {e}", exc_info=True)
        try: await websocket.close(code=1011, reason="Session setup failed");
        except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket: {close_e}"); pass
        if session_id in connected_clients: del connected_clients[session_id];
        return

    # --- Main Try Block for Handler ---
    try:
        await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready with LLM: {settings.ai_provider}.")
        await add_monitor_log_and_save(f"New client connection: {websocket.remote_address}", "system_connect")

        # --- Message Processing Loop ---
        async for message in websocket:
            logger.info(f"[{session_id}] Received message: {message}")
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")
                task_id_from_frontend = data.get("taskId")
                task_title_from_frontend = data.get("task")

                # Get current task ID for this session
                current_task_id = session_data.get(session_id, {}).get("current_task_id")

                # --- CONTEXT SWITCH ---
                if message_type == "context_switch" and task_id_from_frontend:
                     logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")
                     current_task_id = task_id_from_frontend

                     if session_id in session_data:
                         session_data[session_id]["current_task_id"] = current_task_id
                         session_data[session_id]["callback_handler"].set_task_id(current_task_id)
                         await add_task(task_id_from_frontend, task_title_from_frontend or f"Task {task_id_from_frontend}", datetime.datetime.now(datetime.timezone.utc).isoformat())
                         await add_monitor_log_and_save(f"Switched context to task ID: {current_task_id} ('{task_title_from_frontend}')", "system_context_switch")
                         if "memory" in session_data[session_id]:
                             try:
                                 session_data[session_id]["memory"].clear()
                                 logger.info(f"[{session_id}] Cleared agent memory.")
                             except Exception as mem_e:
                                 logger.error(f"[{session_id}] Failed to clear memory: {mem_e}")

                         await send_ws_message("status_message", "Loading history...")
                         history_messages = await get_messages_for_task(current_task_id)
                         if history_messages:
                             logger.info(f"[{session_id}] Sending {len(history_messages)} history messages.")
                             await send_ws_message("history_start", f"Loading {len(history_messages)} messages...")
                             for i, msg in enumerate(history_messages):
                                 db_msg_type = msg['message_type']; db_content = msg['content']; db_timestamp = msg['timestamp']
                                 ui_msg_type = None; content_to_send = db_content
                                 if db_msg_type == "user_input": ui_msg_type = "user"
                                 elif db_msg_type == "agent_finish" or db_msg_type == "agent": ui_msg_type = "agent_message"
                                 elif db_msg_type.startswith("monitor_") or db_msg_type.startswith("error_") or db_msg_type.startswith("system_") or db_msg_type in ["tool_input", "tool_output", "tool_error"]:
                                     ui_msg_type = "monitor_log"; log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; log_type_indicator = f"[{db_msg_type.upper()}]" if not db_msg_type.startswith("monitor_") else ""; content_to_send = f"{log_prefix} [History]{log_type_indicator} {db_content}"
                                 if ui_msg_type: logger.info(f"[{session_id}] Sending history msg {i+1}/{len(history_messages)}: Type='{ui_msg_type}', Content='{content_to_send[:50]}...'"); await send_ws_message(ui_msg_type, content_to_send); await asyncio.sleep(0.01)
                                 else: logger.warning(f"[{session_id}] Skipping hist msg type: {db_msg_type}")
                             await send_ws_message("history_end", "History loaded.")
                             await send_ws_message("status_message", "History loaded. Ready.")
                         else: await send_ws_message("status_message", "No history. Ready."); logger.info(f"[{session_id}] No history found.")
                     else: logger.error(f"[{session_id}] Context switch for missing session!")

                # --- NEW TASK ---
                elif message_type == "new_task":
                     current_task_id = None
                     if session_id in session_data:
                         session_data[session_id]["current_task_id"] = None
                         session_data[session_id]["callback_handler"].set_task_id(None)
                         if "memory" in session_data[session_id]:
                             try:
                                 session_data[session_id]["memory"].clear()
                                 logger.info(f"[{session_id}] Cleared agent memory.")
                             except Exception as mem_e:
                                 logger.error(f"[{session_id}] Failed to clear memory: {mem_e}")
                     await add_monitor_log_and_save("Received 'new_task'. Clearing context.", "system_new_task")
                     await send_ws_message("status_message", "Ready for new task goal.")

                # --- USER MESSAGE -> Trigger Agent ---
                elif message_type == "user_message":
                    active_task_id = current_task_id
                    if not active_task_id:
                         logger.warning(f"[{session_id}] User message but no task active.")
                         await send_ws_message("status_message", "Please select or create a task first.")
                         continue

                    await add_message(active_task_id, session_id, "user_input", content)
                    await add_monitor_log_and_save(f"Received user input: {content}", "user_input")
                    await send_ws_message("status_message", f"Processing input: '{content[:60]}...'")

                    if session_id not in session_data: continue

                    # Create agent executor dynamically
                    try:
                        session_memory = session_data[session_id]["memory"]
                        session_callback_handler = session_data[session_id]["callback_handler"]
                        dynamic_agent_tools = get_dynamic_tools(active_task_id)
                        request_agent_executor = create_agent_executor(llm, dynamic_agent_tools, session_memory)
                        logger.info(f"[{session_id}] Created request-specific AgentExecutor for task {active_task_id}")
                    except Exception as agent_create_e:
                         logger.error(f"[{session_id}] Failed to create agent executor: {agent_create_e}", exc_info=True)
                         await add_monitor_log_and_save(f"Error creating agent: {agent_create_e}", "error_system")
                         await send_ws_message("status_message", "Error setting up agent.")
                         await send_ws_message("agent_message", f"Sorry, internal error setting up agent.")
                         continue

                    # Store list of files before agent run to detect new ones
                    task_workspace_path = get_task_workspace_path(active_task_id)
                    files_before = set(f.name for f in task_workspace_path.glob('*.png') if f.is_file())

                    try:
                        # Use astream_log() - Callbacks handle UI updates and DB saving
                        config = RunnableConfig(callbacks=[session_callback_handler])
                        async for chunk in request_agent_executor.astream_log(
                            {"input": content}, config=config
                        ):
                            pass # Callbacks handle everything

                        # Check for new PNG files after successful run
                        files_after = set(f.name for f in task_workspace_path.glob('*.png') if f.is_file())
                        new_files = files_after - files_before
                        if new_files:
                            logger.info(f"[{session_id}] Detected new PNG files: {new_files}")
                            for filename in new_files:
                                image_url = f"http://{FILE_SERVER_HOST}:{FILE_SERVER_PORT}/workspace_files/{active_task_id}/{filename}"
                                await add_monitor_log_and_save(f"Generated image: {filename}", "system_image_generated")
                                await send_ws_message("display_image", {"url": image_url, "filename": filename})
                                break # Only display the first new image for now

                        # await add_monitor_log_and_save("Agent stream finished.", "system_agent_end") # Callback handles final status

                    except Exception as e:
                        error_msg = f"CRITICAL Error during agent execution: {e}"
                        logger.error(f"[{session_id}] {error_msg}", exc_info=True)
                        await add_monitor_log_and_save(error_msg, "error_agent")
                        await send_ws_message("status_message", "Error during task processing.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred: {type(e).__name__}")
                        if active_task_id: await add_message(active_task_id, session_id, "error_agent", f"{type(e).__name__}: {e}")


                # --- DELETE TASK ---
                elif message_type == "delete_task" and task_id_from_frontend:
                     # ... (delete logic remains the same) ...
                     logger.warning(f"[{session_id}] Received request to delete task: {task_id_from_frontend}")
                     await add_monitor_log_and_save(f"Received request to delete task: {task_id_from_frontend}", "system_delete_request")
                     deleted = await delete_task_and_messages(task_id_from_frontend)
                     if deleted:
                         await send_ws_message("status_message", f"Task {task_id_from_frontend[:8]}... deleted.")
                         await add_monitor_log_and_save(f"Task {task_id_from_frontend} deleted successfully.", "system_delete_success")
                         if current_task_id == task_id_from_frontend:
                             current_task_id = None
                             if session_id in session_data: session_data[session_id]["current_task_id"] = None; session_data[session_id]["callback_handler"].set_task_id(None)
                             await send_ws_message("status_message", "Active task deleted. Select or create a new task.")
                     else:
                         await send_ws_message("status_message", f"Failed to delete task {task_id_from_frontend[:8]}...")
                         await add_monitor_log_and_save(f"Failed to delete task {task_id_from_frontend}.", "error_delete")

                # --- Other message types ---
                elif message_type == "run_command": # Direct command execution
                     # ... (remains the same) ...
                     command = data.get("command"); active_task_id = current_task_id
                     await add_monitor_log_and_save(f"Received direct 'run_command'. Executing: {command}", "system_direct_cmd")
                     if command: await execute_shell_command(command, session_id, send_ws_message, add_message, active_task_id)
                     else: await add_monitor_log_and_save("Error: 'run_command' with no command.", "error_direct_cmd")
                elif message_type == "action_command": # Placeholder
                     await add_monitor_log_and_save(f"Received action command: {data.get('command')} (Not implemented).", "system_action_cmd")
                else: # Unknown
                     logger.warning(f"[{session_id}] Unknown message type: {message_type}"); await add_monitor_log_and_save(f"Unknown message type: {message_type}", "error_unknown_msg")

            # --- Error handling for message processing ---
            except json.JSONDecodeError: logger.error(f"[{session_id}] Non-JSON message: {message}"); await add_monitor_log_and_save("Error: Received invalid message format.", "error_json")
            except Exception as e: logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True); await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing")

    # --- Connection Closed Handling ---
    except websockets.exceptions.ConnectionClosedOK: logger.info(f"Client disconnected: {websocket.remote_address} (Session: {session_id})")
    except websockets.exceptions.ConnectionClosedError as e: logger.warning(f"Connection closed error: {websocket.remote_address} (Session: {session_id}) - {e}")
    except Exception as e:
        logger.error(f"Unhandled error in handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
        try: await websocket.close(code=1011, reason="Internal server error");
        except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket: {close_e}"); pass
    finally: # Cleanup
        logger.info(f"Cleaning up for session {session_id}")
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}")


async def main():
    # --- Start File Server ---
    file_server_site, file_server_runner = await setup_file_server()
    await file_server_site.start()
    logger.info("File server started.")

    # --- Start WebSocket Server ---
    ws_host = "localhost"; ws_port = 8765;
    logger.info(f"Starting WebSocket server on ws://{ws_host}:{ws_port}")
    websocket_server = await websockets.serve(handler, ws_host, ws_port)
    logger.info("WebSocket server started.")

    try:
        # Keep both servers running
        await asyncio.gather(
            websocket_server.wait_closed(),
            # Keep file server running (no specific wait_closed needed for TCPSite)
            asyncio.Future() # Runs forever until cancelled
        )
    except asyncio.CancelledError:
         logger.info("Servers shutting down...")
    finally:
        # --- Cleanup Servers ---
        logger.info("Stopping WebSocket server...")
        websocket_server.close()
        await websocket_server.wait_closed()
        logger.info("WebSocket server stopped.")

        logger.info("Stopping file server...")
        await file_server_runner.cleanup() # Clean up aiohttp runner
        logger.info("File server stopped.")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)

