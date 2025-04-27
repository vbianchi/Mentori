# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
import signal
import re


# --- Web Server Imports ---
from aiohttp import web
from aiohttp.web import FileResponse
import aiohttp_cors
# -------------------------

# LangChain Imports
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.runnables import RunnableConfig
# -------------------------

# Project Imports
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT, TEXT_EXTENSIONS
from backend.agent import create_agent_executor
from backend.callbacks import WebSocketCallbackHandler # Import updated handler
from backend.db_utils import init_db, add_task, add_message, get_messages_for_task, delete_task_and_messages
# ----------------------

# Setup logging
logger = logging.getLogger(__name__)

# --- Load Settings, Initialize LLM ---
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    logger.info("Base LLM initialized successfully.")
except Exception as e:
    logging.critical(f"FATAL: Failed during startup initialization: {e}", exc_info=True)
    exit(1)

# --- Global state ---
connected_clients: Dict[str, Dict[str, Any]] = {}
session_data: Dict[str, Dict[str, Any]] = {}

# --- File Server Constants ---
FILE_SERVER_LISTEN_HOST = "0.0.0.0"
FILE_SERVER_CLIENT_HOST = os.getenv("FILE_SERVER_HOSTNAME", "localhost")
FILE_SERVER_PORT = 8766
logger.info(f"File server will listen on {FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT}")
logger.info(f"File server URLs constructed for client will use: http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}")


# --- Helper: Read Stream from Subprocess ---
async def read_stream(stream, stream_name, session_id, send_ws_message_func, db_add_message_func, current_task_id):
    """Reads lines from a stream and sends them over WebSocket via the provided sender func."""
    log_prefix_base = f"[{session_id[:8]}]"
    while True:
        try: line = await stream.readline()
        except Exception as e: logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}"); break
        if not line: break
        line_content = line.decode(errors='replace').rstrip(); log_content = f"[{stream_name}] {line_content}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message_func("monitor_log", f"[{timestamp}]{log_prefix_base} {log_content}")
        if current_task_id:
            try: await db_add_message_func(current_task_id, session_id, f"monitor_{stream_name}", line_content)
            except Exception as db_err: logger.error(f"[{session_id}] Failed to save {stream_name} log to DB: {db_err}")
    logger.debug(f"[{session_id}] {stream_name} stream finished.")


# --- Helper: Execute Shell Command ---
async def execute_shell_command(command: str, session_id: str, send_ws_message_func: callable, db_add_message_func: callable, current_task_id: Optional[str]) -> bool:
    """Executes a shell command asynchronously and streams output via send_ws_message_func."""
    log_prefix_base = f"[{session_id[:8]}]"; timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    start_log_content = f"[Direct Command] Executing: {command}"
    logger.info(f"[{session_id}] {start_log_content}")
    await send_ws_message_func("monitor_log", f"[{timestamp_start}]{log_prefix_base} {start_log_content}")
    await send_ws_message_func("status_message", f"Running direct command: {command[:60]}...")
    if current_task_id:
        try: await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_start", command)
        except Exception as db_err: logger.error(f"[{session_id}] Failed to save direct cmd start to DB: {db_err}")
    process = None; success = False; status_msg = "failed"; return_code = -1
    cwd = str(BASE_WORKSPACE_ROOT.resolve()); logger.info(f"[{session_id}] Direct command CWD: {cwd}")
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        TIMEOUT_SECONDS = 120; proc_wait_task = asyncio.create_task(process.wait())
        done, pending = await asyncio.wait([stdout_task, stderr_task, proc_wait_task], timeout=TIMEOUT_SECONDS, return_when=asyncio.ALL_COMPLETED)
        if proc_wait_task not in done:
             logger.error(f"[{session_id}] Timeout executing direct command: {command}"); status_msg = f"failed (Timeout after {TIMEOUT_SECONDS}s)"; success = False
             if process and process.returncode is None:
                  try: process.terminate()
                  except ProcessLookupError: pass
                  await process.wait()
             for task in pending: task.cancel()
             await asyncio.gather(*pending, return_exceptions=True)
        else:
             return_code = proc_wait_task.result(); await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
             success = return_code == 0; status_msg = "succeeded" if success else f"failed (Code: {return_code})"
    except FileNotFoundError: cmd_part = command.split()[0] if command else "Unknown"; status_msg = f"failed (Command Not Found: {cmd_part})"; logger.warning(f"[{session_id}] Direct command not found: {cmd_part}"); success = False
    except Exception as e: status_msg = f"failed ({type(e).__name__})"; logger.error(f"[{session_id}] Error running direct command '{command}': {e}", exc_info=True); success = False
    timestamp_end = datetime.datetime.now().isoformat(timespec='milliseconds')
    finish_log_content = f"[Direct Command] Finished '{command[:60]}...', {status_msg}."
    await send_ws_message_func("monitor_log", f"[{timestamp_end}]{log_prefix_base} {finish_log_content}")
    if current_task_id:
        try: await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_end", f"Command: {command} | Status: {status_msg}")
        except Exception as db_err: logger.error(f"[{session_id}] Failed to save direct cmd end to DB: {db_err}")
    if not success and status_msg.startswith("failed"): await send_ws_message_func("status_message", f"Error: Direct command {status_msg}")
    elif success: await send_ws_message_func("status_message", f"Direct command finished successfully.")
    return success

# --- File Server Handler ---
async def handle_workspace_file(request: web.Request) -> web.Response:
    task_id = request.match_info.get('task_id'); filename = request.match_info.get('filename')
    session_id = request.headers.get("X-Session-ID", "unknown")
    if not task_id or not filename: logger.warning(f"[{session_id}] File server request missing task_id or filename."); raise web.HTTPBadRequest(text="Task ID and filename required")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id): logger.error(f"[{session_id}] Invalid task_id format rejected: {task_id}"); raise web.HTTPForbidden(text="Invalid task ID format.")
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"): logger.error(f"[{session_id}] Invalid filename path components detected: {filename}"); raise web.HTTPForbidden(text="Invalid filename path components.")
    try:
        task_workspace = get_task_workspace_path(task_id); file_path = (task_workspace / filename).resolve()
        if not file_path.is_relative_to(BASE_WORKSPACE_ROOT.resolve()): logger.error(f"[{session_id}] Security Error: Access attempt outside base workspace! Req: {file_path}, Base: {BASE_WORKSPACE_ROOT.resolve()}"); raise web.HTTPForbidden(text="Access denied - outside base workspace.")
    except (ValueError, OSError) as e: logger.error(f"[{session_id}] Error resolving task workspace for file access: {e}"); raise web.HTTPInternalServerError(text="Error accessing task workspace.")
    except Exception as e: logger.error(f"[{session_id}] Unexpected error validating file path: {e}. Req: {filename}", exc_info=True); raise web.HTTPInternalServerError(text="Error validating file path")
    if not file_path.is_file(): logger.warning(f"[{session_id}] File not found request: {file_path}"); raise web.HTTPNotFound(text=f"File not found: {filename}")
    logger.info(f"[{session_id}] Serving file: {file_path}"); return FileResponse(path=file_path)

# --- Setup File Server ---
async def setup_file_server():
    """Sets up and returns the aiohttp file server runner with CORS."""
    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults={"http://localhost:8000": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods=["GET"])})
    resource = app.router.add_resource('/workspace_files/{task_id}/{filename:.+}')
    route = resource.add_route('GET', handle_workspace_file); cors.add(route)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, FILE_SERVER_LISTEN_HOST, FILE_SERVER_PORT)
    logger.info(f"Starting file server listening on http://{FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT} (allowing http://localhost:8000)")
    return site, runner

# --- WebSocket Handler ---
try:
    from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
    from websockets.server import WebSocketServerProtocol
    WebSocketProtocolType = WebSocketServerProtocol
except ImportError:
    logger.warning("Could not import specific websocket types, using generic hints.")
    from websockets.legacy.server import WebSocketServerProtocol as LegacyWebSocketServerProtocol # type: ignore
    WebSocketProtocolType = LegacyWebSocketServerProtocol # type: ignore
    ConnectionClosedOK = websockets.exceptions.ConnectionClosedOK # type: ignore
    ConnectionClosedError = websockets.exceptions.ConnectionClosedError # type: ignore

async def handler(websocket: WebSocketProtocolType):
    """Handles incoming WebSocket connections and messages for a user session."""
    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id}] Connection attempt from {websocket.remote_address}...")
    connected_clients[session_id] = {"websocket": websocket, "agent_task": None}
    logger.info(f"[{session_id}] Client added to connected_clients dict.")

    async def send_ws_message(msg_type: str, content: Any):
        logger.debug(f"[{session_id}] Attempting to send WS message: Type='{msg_type}', Content='{str(content)[:100]}...'")
        if session_id in connected_clients:
            ws = connected_clients[session_id].get("websocket")
            if ws:
                try:
                    await ws.send(json.dumps({"type": msg_type, "content": content}))
                    logger.debug(f"[{session_id}] Successfully sent WS message type '{msg_type}'.")
                except (ConnectionClosedOK, ConnectionClosedError) as close_exc: logger.warning(f"[{session_id}] WS already closed when trying to send type '{msg_type}'. Error: {close_exc}")
                except Exception as e: logger.error(f"[{session_id}] Error sending WS message type '{msg_type}': {e}", exc_info=True)
            else: logger.warning(f"[{session_id}] Websocket object not found for session when trying to send type '{msg_type}'.")
        else: logger.warning(f"[{session_id}] Session not found in connected_clients when trying to send type '{msg_type}'.")

    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"):
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds'); log_prefix = f"[{timestamp}][{session_id[:8]}]"; full_content = f"{log_prefix} {text}"
        await send_ws_message("monitor_log", full_content)
        active_task_id = session_data.get(session_id, {}).get("current_task_id")
        if active_task_id:
            try: await add_message(active_task_id, session_id, log_type, text);
            except Exception as db_err: logger.error(f"[{session_id}] Failed to save monitor log '{log_type}' to DB: {db_err}")

    ws_callback_handler: Optional[WebSocketCallbackHandler] = None; memory: Optional[ConversationBufferWindowMemory] = None; session_setup_ok = False
    try:
        logger.info(f"[{session_id}] Starting session setup...")
        logger.debug(f"[{session_id}] Creating ConversationBufferWindowMemory...")
        memory = ConversationBufferWindowMemory(k=10, memory_key="chat_history", input_key="input", output_key="output", return_messages=True)
        logger.debug(f"[{session_id}] Memory object created.")
        logger.debug(f"[{session_id}] Creating WebSocketCallbackHandler...")
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message, add_message) # Pass the updated send_ws_message
        logger.debug(f"[{session_id}] Callback handler created.")
        logger.debug(f"[{session_id}] Storing session data...")
        session_data[session_id] = {"memory": memory, "callback_handler": ws_callback_handler, "current_task_id": None}
        logger.info(f"[{session_id}] Session setup complete."); session_setup_ok = True
    except Exception as e:
        logger.error(f"[{session_id}] CRITICAL ERROR during session setup: {e}", exc_info=True)
        if websocket and not websocket.closed:
            try: await websocket.close(code=1011, reason="Session setup failed")
            except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket during setup failure: {close_e}")
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        return

    if not session_setup_ok: logger.error(f"[{session_id}] Halting handler because session setup failed."); return

    try:
        logger.info(f"[{session_id}] Sending initial status message..."); await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready. LLM: {settings.ai_provider} ({settings.gemini_model_name if settings.ai_provider == 'gemini' else settings.ollama_model_name}).")
        logger.info(f"[{session_id}] Initial status message sent."); await add_monitor_log_and_save(f"New client connection: {websocket.remote_address}", "system_connect")
        logger.info(f"[{session_id}] Added system_connect log.")

        logger.info(f"[{session_id}] Entering message processing loop...")
        async for message in websocket:
            logger.debug(f"[{session_id}] Received raw message: {message[:200]}{'...' if len(message)>200 else ''}")
            try:
                data = json.loads(message); message_type = data.get("type"); content = data.get("content")
                task_id_from_frontend = data.get("taskId"); task_title_from_frontend = data.get("task")
                current_task_id = session_data.get(session_id, {}).get("current_task_id")
                logger.debug(f"[{session_id}] Processing message type: {message_type}, Task Context: {current_task_id}")

                # --- CONTEXT SWITCH ---
                if message_type == "context_switch" and task_id_from_frontend:
                    logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")
                    if session_id in session_data:
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                            logger.warning(f"[{session_id}] Cancelling active agent task due to context switch.")
                            existing_agent_task.cancel(); await send_ws_message("status_message", "Operation cancelled due to task switch.")
                            await add_monitor_log_and_save("Agent operation cancelled due to context switch.", "system_cancel"); connected_clients[session_id]["agent_task"] = None
                        session_data[session_id]["current_task_id"] = task_id_from_frontend
                        session_data[session_id]["callback_handler"].set_task_id(task_id_from_frontend)
                        await add_task(task_id_from_frontend, task_title_from_frontend or f"Task {task_id_from_frontend}", datetime.datetime.now(datetime.timezone.utc).isoformat())
                        await add_monitor_log_and_save(f"Switched context to task ID: {task_id_from_frontend} ('{task_title_from_frontend}')", "system_context_switch")
                        if "memory" in session_data[session_id]:
                            try: session_data[session_id]["memory"].clear(); logger.info(f"[{session_id}] Cleared agent memory for new task context.")
                            except Exception as mem_e: logger.error(f"[{session_id}] Failed to clear memory on context switch: {mem_e}")
                        await send_ws_message("status_message", "Loading history...")
                        history_messages = await get_messages_for_task(task_id_from_frontend)
                        artifacts_from_history = []; chat_history_for_memory = []
                        if history_messages:
                            logger.info(f"[{session_id}] Loading {len(history_messages)} history messages for task {task_id_from_frontend}.")
                            await send_ws_message("history_start", f"Loading {len(history_messages)} messages...")
                            for i, msg in enumerate(history_messages):
                                db_msg_type = msg.get('message_type', 'unknown'); db_content = msg.get('content', ''); db_timestamp = msg.get('timestamp', datetime.datetime.now().isoformat())
                                ui_msg_type = None; content_to_send = db_content
                                if db_msg_type == "user_input": ui_msg_type = "user"; chat_history_for_memory.append(HumanMessage(content=db_content))
                                elif db_msg_type in ["agent_finish", "agent_message", "agent"]: ui_msg_type = "agent_message"; chat_history_for_memory.append(AIMessage(content=db_content))
                                elif db_msg_type == "artifact_generated":
                                     filename = db_content
                                     try:
                                         task_ws_path = get_task_workspace_path(task_id_from_frontend); file_path = (task_ws_path / filename).resolve()
                                         if not file_path.is_relative_to(task_ws_path.resolve()): continue
                                         artifact_type = 'unknown'; file_suffix = file_path.suffix.lower()
                                         if file_suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']: artifact_type = 'image'
                                         elif file_suffix in TEXT_EXTENSIONS: artifact_type = 'text'
                                         if artifact_type != 'unknown' and file_path.exists():
                                             relative_filename = str(file_path.relative_to(task_ws_path))
                                             artifact_url = f"http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}/workspace_files/{task_id_from_frontend}/{relative_filename}"
                                             artifacts_from_history.append({"type": artifact_type, "url": artifact_url, "filename": relative_filename})
                                             log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; await send_ws_message("monitor_log", f"{log_prefix} [History][ARTIFACT] {relative_filename} (Type: {artifact_type})")
                                         else: logger.warning(f"[{session_id}] Artifact file from history not found or unknown type: {file_path}"); log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; await send_ws_message("monitor_log", f"{log_prefix} [History][ARTIFACT_MISSING] {filename}")
                                     except (ValueError, OSError) as path_err: logger.error(f"[{session_id}] Error resolving task workspace path for history artifact {filename}: {path_err}")
                                     except Exception as artifact_err: logger.error(f"[{session_id}] Error processing artifact from history {filename}: {artifact_err}")
                                     ui_msg_type = None
                                elif db_msg_type.startswith(("monitor_", "error_", "system_", "tool_")):
                                    ui_msg_type = "monitor_log"; log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; type_indicator = f"[{db_msg_type.replace('monitor_', '').replace('error_', 'ERR_').replace('system_', 'SYS_').upper()}]"; content_to_send = f"{log_prefix} [History]{type_indicator} {db_content}"
                                if ui_msg_type: await send_ws_message(ui_msg_type, content_to_send); await asyncio.sleep(0.005)
                            await send_ws_message("history_end", "History loaded."); logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")
                            MAX_MEMORY_RELOAD = 10
                            if "memory" in session_data[session_id]:
                                try: session_data[session_id]["memory"].chat_memory.messages = chat_history_for_memory[-MAX_MEMORY_RELOAD:]; logger.info(f"[{session_id}] Repopulated agent memory with last {len(session_data[session_id]['memory'].chat_memory.messages)} messages.")
                                except Exception as mem_load_e: logger.error(f"[{session_id}] Failed to repopulate memory from history: {mem_load_e}")
                            if artifacts_from_history: logger.info(f"[{session_id}] Sending {len(artifacts_from_history)} artifacts from history."); await send_ws_message("update_artifacts", artifacts_from_history)
                            else: await send_ws_message("update_artifacts", [])
                        else: await send_ws_message("history_end", "No history found."); await send_ws_message("update_artifacts", []); logger.info(f"[{session_id}] No history found for task {task_id_from_frontend}.")
                        await send_ws_message("status_message", "History loaded. Ready.")
                    else: logger.error(f"[{session_id}] Context switch received but no session data found!"); await send_ws_message("status_message", "Error: Session data lost. Please refresh.")

                # --- NEW TASK ---
                elif message_type == "new_task":
                    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context."); current_task_id = None
                    if session_id in session_data:
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                            logger.warning(f"[{session_id}] Cancelling active agent task due to new task."); existing_agent_task.cancel()
                            await send_ws_message("status_message", "Operation cancelled for new task."); await add_monitor_log_and_save("Agent operation cancelled due to new task creation.", "system_cancel"); connected_clients[session_id]["agent_task"] = None
                        session_data[session_id]["current_task_id"] = None; session_data[session_id]["callback_handler"].set_task_id(None)
                        if "memory" in session_data[session_id]:
                            try: session_data[session_id]["memory"].clear(); logger.info(f"[{session_id}] Cleared agent memory for new task.")
                            except Exception as mem_e: logger.error(f"[{session_id}] Failed to clear memory for new task: {mem_e}")
                        await add_monitor_log_and_save("Cleared context for new task.", "system_new_task")
                        await send_ws_message("status_message", "Ready for new task goal."); await send_ws_message("update_artifacts", [])
                    else: logger.error(f"[{session_id}] 'new_task' signal received but no session data found!")

                # --- USER MESSAGE ---
                elif message_type == "user_message":
                    active_task_id = session_data.get(session_id, {}).get("current_task_id")
                    if not active_task_id: logger.warning(f"[{session_id}] User message received but no task active."); await send_ws_message("status_message", "Please select or create a task first."); continue
                    if connected_clients.get(session_id, {}).get("agent_task") and not connected_clients[session_id]["agent_task"].done(): logger.warning(f"[{session_id}] User message received while agent is already running for task {active_task_id}."); await send_ws_message("status_message", "Agent is busy. Please wait for the current operation to complete."); continue
                    await add_message(active_task_id, session_id, "user_input", content); await send_ws_message("status_message", f"Processing input: '{content[:60]}...'"); await add_monitor_log_and_save(f"User Input: {content}", "user_input")
                    if session_id not in session_data: logger.error(f"[{session_id}] User message for task {active_task_id} but no session data found!"); continue

                    session_memory = session_data[session_id]["memory"]; session_callback_handler = session_data[session_id]["callback_handler"]
                    request_agent_executor: Optional[AgentExecutor] = None
                    try:
                        dynamic_agent_tools = get_dynamic_tools(active_task_id)
                        request_agent_executor = create_agent_executor(llm, dynamic_agent_tools, session_memory)
                        logger.info(f"[{session_id}] Created request-specific AgentExecutor for task {active_task_id}")
                    except Exception as agent_create_e:
                        logger.error(f"[{session_id}] Failed to create agent executor for task {active_task_id}: {agent_create_e}", exc_info=True)
                        await add_monitor_log_and_save(f"Error creating agent: {agent_create_e}", "error_system"); await send_ws_message("status_message", "Error: Failed to set up agent.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred while setting up the agent: {type(agent_create_e).__name__}"); continue

                    # --- REMOVED Post-Run Artifact Scan ---
                    # Artifacts are now handled by the callback handler for write_file

                    agent_task: Optional[asyncio.Task] = None
                    try:
                        config = RunnableConfig(callbacks=[session_callback_handler])
                        agent_coro = request_agent_executor.ainvoke({"input": content}, config=config)
                        agent_task = asyncio.create_task(agent_coro)
                        connected_clients[session_id]["agent_task"] = agent_task
                        result = await agent_task
                        logger.info(f"[{session_id}] Agent execution completed successfully for task {active_task_id}.")
                        # Final answer/status is sent by the callback handler's on_agent_finish

                    except asyncio.CancelledError: logger.warning(f"[{session_id}] Agent task for task {active_task_id} was cancelled.")
                    except Exception as e:
                        error_msg = f"CRITICAL Error during agent execution: {e}"; logger.error(f"[{session_id}] {error_msg}", exc_info=True)
                        await add_monitor_log_and_save(error_msg, "error_agent"); await send_ws_message("status_message", "Error during task processing.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred: {type(e).__name__}")
                        if active_task_id: await add_message(active_task_id, session_id, "error_agent", f"{type(e).__name__}: {e}")
                    finally:
                        if session_id in connected_clients: connected_clients[session_id]["agent_task"] = None

                # --- DELETE TASK ---
                elif message_type == "delete_task" and task_id_from_frontend:
                    logger.warning(f"[{session_id}] Received request to delete task: {task_id_from_frontend}")
                    await add_monitor_log_and_save(f"Received request to delete task: {task_id_from_frontend}", "system_delete_request")
                    deleted = await delete_task_and_messages(task_id_from_frontend)
                    if deleted:
                        await send_ws_message("status_message", f"Task {task_id_from_frontend[:8]}... deleted."); await add_monitor_log_and_save(f"Task {task_id_from_frontend} deleted successfully from DB.", "system_delete_success")
                        task_workspace_to_delete : Optional[Path] = None
                        try:
                            task_workspace_to_delete = get_task_workspace_path(task_id_from_frontend)
                            if task_workspace_to_delete.exists() and task_workspace_to_delete.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
                                import shutil; await asyncio.to_thread(shutil.rmtree, task_workspace_to_delete)
                                logger.info(f"[{session_id}] Successfully deleted workspace directory: {task_workspace_to_delete}"); await add_monitor_log_and_save(f"Workspace directory deleted: {task_workspace_to_delete.name}", "system_delete_success")
                            else: logger.warning(f"[{session_id}] Workspace directory not found or invalid for deletion: {task_workspace_to_delete}")
                        except (ValueError, OSError) as path_err: logger.error(f"[{session_id}] Error resolving task workspace path for deletion {task_id_from_frontend}: {path_err}"); await add_monitor_log_and_save(f"Error finding workspace directory for deletion: {path_err}", "error_delete")
                        except Exception as ws_del_e: logger.error(f"[{session_id}] Error deleting workspace directory {task_workspace_to_delete}: {ws_del_e}"); await add_monitor_log_and_save(f"Error deleting workspace directory: {ws_del_e}", "error_delete")
                        active_task_id = session_data.get(session_id, {}).get("current_task_id")
                        if active_task_id == task_id_from_frontend:
                            current_task_id = None
                            if session_id in session_data:
                                existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                                if existing_agent_task and not existing_agent_task.done(): logger.warning(f"[{session_id}] Cancelling active agent task due to active task deletion."); existing_agent_task.cancel(); connected_clients[session_id]["agent_task"] = None
                                session_data[session_id]["current_task_id"] = None; session_data[session_id]["callback_handler"].set_task_id(None)
                                if "memory" in session_data[session_id]: session_data[session_id]["memory"].clear()
                                await send_ws_message("status_message", "Active task deleted. Select or create a new task."); await add_monitor_log_and_save("Cleared context as active task was deleted.", "system_context_clear"); await send_ws_message("update_artifacts", [])
                    else: await send_ws_message("status_message", f"Failed to delete task {task_id_from_frontend[:8]}..."); await add_monitor_log_and_save(f"Failed to delete task {task_id_from_frontend} from DB.", "error_delete")

                # --- Other message types ---
                elif message_type == "run_command":
                    command_to_run = data.get("command")
                    if command_to_run: active_task_id_for_cmd = session_data.get(session_id, {}).get("current_task_id"); await add_monitor_log_and_save(f"Received direct 'run_command'. Executing: {command_to_run} (Task Context: {active_task_id_for_cmd})", "system_direct_cmd"); await execute_shell_command(command_to_run, session_id, send_ws_message, add_message, active_task_id_for_cmd)
                    else: logger.warning(f"[{session_id}] Received 'run_command' with no command content."); await add_monitor_log_and_save("Error: 'run_command' received with no command specified.", "error_direct_cmd")
                elif message_type == "action_command":
                    action = data.get("command"); logger.info(f"[{session_id}] Received action command: {action} (Not implemented)."); await add_monitor_log_and_save(f"Received action command: {action} (Handler not implemented).", "system_action_cmd"); await send_ws_message("status_message", f"Action '{action}' not implemented.")
                else: logger.warning(f"[{session_id}] Unknown message type received: {message_type}"); await add_monitor_log_and_save(f"Received unknown message type: {message_type}", "error_unknown_msg")

            except json.JSONDecodeError: logger.error(f"[{session_id}] Received non-JSON message: {message[:200]}{'...' if len(message)>200 else ''}"); await add_monitor_log_and_save("Error: Received invalid message format (not JSON).", "error_json")
            except asyncio.CancelledError: logger.info(f"[{session_id}] Message processing loop cancelled."); raise
            except Exception as e:
                logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                try: await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing"); await send_ws_message("status_message", f"Error processing message: {type(e).__name__}")
                except Exception as inner_e: logger.error(f"[{session_id}] Further error during error reporting: {inner_e}")

    except (ConnectionClosedOK, ConnectionClosedError) as ws_close_exc:
        if isinstance(ws_close_exc, ConnectionClosedOK): logger.info(f"Client disconnected normally: {websocket.remote_address} (Session: {session_id}) - Code: {ws_close_exc.code}, Reason: {ws_close_exc.reason}")
        else: logger.warning(f"Connection closed abnormally: {websocket.remote_address} (Session: {session_id}) - Code: {ws_close_exc.code}, Reason: {ws_close_exc.reason}")
    except asyncio.CancelledError:
         logger.info(f"WebSocket handler for session {session_id} cancelled.")
         if not websocket.closed: await websocket.close(code=1012, reason="Server shutting down")
    except Exception as e:
        logger.error(f"Unhandled error in WebSocket handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
        try:
            if not websocket.closed: await websocket.close(code=1011, reason="Internal server error")
        except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket after unhandled handler error: {close_e}")
    finally:
        logger.info(f"Cleaning up resources for session {session_id}")
        agent_task = connected_clients.get(session_id, {}).get("agent_task")
        if agent_task and not agent_task.done():
            logger.warning(f"[{session_id}] Cancelling agent task during cleanup."); agent_task.cancel()
            try: await agent_task
            except asyncio.CancelledError: pass
            except Exception as cancel_e: logger.error(f"[{session_id}] Error waiting for agent task cancellation during cleanup: {cancel_e}")
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}. Active clients: {len(connected_clients)}")


async def main():
    await init_db()
    file_server_site, file_server_runner = await setup_file_server()
    await file_server_site.start()
    logger.info("File server started.")
    ws_host = "0.0.0.0"; ws_port = 8765
    logger.info(f"Starting WebSocket server on ws://{ws_host}:{ws_port}")
    websocket_server = await websockets.serve(handler, ws_host, ws_port, max_size=2**24, ping_interval=20, ping_timeout=30) # Increased timeout
    logger.info("WebSocket server started.")
    shutdown_event = asyncio.Event(); loop = asyncio.get_running_loop()
    original_sigint_handler = signal.getsignal(signal.SIGINT); original_sigterm_handler = signal.getsignal(signal.SIGTERM)
    def signal_handler(sig, frame): logger.info(f"Received signal {sig}. Initiating shutdown..."); shutdown_event.set(); signal.signal(signal.SIGINT, original_sigint_handler); signal.signal(signal.SIGTERM, original_sigterm_handler)
    try: loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT, None); loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM, None)
    except NotImplementedError: logger.warning("Signal handlers not available on this platform (Windows?). Use Ctrl+C.")
    logger.info("Application servers running. Press Ctrl+C to stop."); await shutdown_event.wait()
    logger.info("Shutdown signal received. Stopping servers...")
    logger.info("Stopping WebSocket server..."); websocket_server.close(); await websocket_server.wait_closed(); logger.info("WebSocket server stopped.")
    logger.info("Stopping file server..."); await file_server_runner.cleanup(); logger.info("File server stopped.")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks: logger.info(f"Cancelling {len(tasks)} outstanding tasks..."); [task.cancel() for task in tasks]; await asyncio.gather(*tasks, return_exceptions=True); logger.info("Outstanding tasks cancelled.")

if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]: log_level = "INFO"
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info(f"Logging level set to {log_level}")
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("Server stopped manually (KeyboardInterrupt).")
    except Exception as e: logging.critical(f"Server failed to start or crashed: {e}", exc_info=True); exit(1)
