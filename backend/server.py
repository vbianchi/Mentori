# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex 
import uuid
from typing import Optional, List, Dict, Any, Set, Tuple
from pathlib import Path
import os
import signal
import re
import functools
import warnings
import aiofiles
import unicodedata

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
from langchain_core.language_models.base import BaseLanguageModel
# -------------------------

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT, TEXT_EXTENSIONS
from backend.agent import create_agent_executor
from backend.callbacks import WebSocketCallbackHandler, AgentCancelledException
from backend.db_utils import (
    init_db, add_task, add_message, get_messages_for_task,
    delete_task_and_messages, rename_task_in_db
)
from backend.planner import generate_plan, PlanStep

# ----------------------

log_level = settings.log_level
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to {log_level}")

try:
    default_llm_instance_for_startup_checks = get_llm(settings, provider=settings.default_provider, model_name=settings.default_model_name)
    logger.info(f"Default Base LLM for startup checks initialized successfully: {settings.default_llm_id}")
except Exception as llm_e:
    logging.critical(f"FATAL: Failed during startup LLM initialization: {llm_e}", exc_info=True)
    exit(1)

connected_clients: Dict[str, Dict[str, Any]] = {}
session_data: Dict[str, Dict[str, Any]] = {}

FILE_SERVER_LISTEN_HOST = "0.0.0.0"
FILE_SERVER_CLIENT_HOST = settings.file_server_hostname
FILE_SERVER_PORT = 8766
logger.info(f"File server will listen on {FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT}")
logger.info(f"File server URLs constructed for client will use: http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}")

async def read_stream(stream, stream_name, session_id, send_ws_message_func, db_add_message_func, current_task_id):
    # ... (unchanged)
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

async def execute_shell_command(command: str, session_id: str, send_ws_message_func: callable, db_add_message_func: callable, current_task_id: Optional[str]) -> bool:
    # ... (unchanged)
    log_prefix_base = f"[{session_id[:8]}]"; timestamp_start = datetime.datetime.now().isoformat(timespec='milliseconds')
    start_log_content = f"[Direct Command] Executing: {command}"
    logger.info(f"[{session_id}] {start_log_content}")
    await send_ws_message_func("monitor_log", f"[{timestamp_start}]{log_prefix_base} {start_log_content}")
    if current_task_id:
        try: await db_add_message_func(current_task_id, session_id, "monitor_direct_cmd_start", command)
        except Exception as db_err: logger.error(f"[{session_id}] Failed to save direct cmd start to DB: {db_err}")
    process = None; success = False; status_msg = "failed"; return_code = -1
    cwd = str(BASE_WORKSPACE_ROOT.resolve()); logger.info(f"[{session_id}] Direct command CWD: {cwd}")
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
        stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr", session_id, send_ws_message_func, db_add_message_func, current_task_id))
        TIMEOUT_SECONDS = settings.direct_command_timeout
        proc_wait_task = asyncio.create_task(process.wait())
        done, pending = await asyncio.wait([stdout_task, stderr_task, proc_wait_task], timeout=TIMEOUT_SECONDS, return_when=asyncio.ALL_COMPLETED)
        if proc_wait_task not in done:
            logger.error(f"[{session_id}] Timeout executing direct command: {command}"); status_msg = f"failed (Timeout after {TIMEOUT_SECONDS}s)"; success = False
            if process and process.returncode is None:
                try: process.terminate()
                except ProcessLookupError: pass
                await process.wait()
            for task_to_cancel in pending: task_to_cancel.cancel() # Renamed variable to avoid conflict
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
    return success

async def handle_workspace_file(request: web.Request) -> web.Response:
    # ... (unchanged)
    task_id = request.match_info.get('task_id')
    filename = request.match_info.get('filename')
    session_id = request.headers.get("X-Session-ID", "unknown")
    if not task_id or not filename:
        logger.warning(f"[{session_id}] File server request missing task_id or filename.")
        raise web.HTTPBadRequest(text="Task ID and filename required")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id):
        logger.error(f"[{session_id}] Invalid task_id format rejected: {task_id}")
        raise web.HTTPForbidden(text="Invalid task ID format.")
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        logger.error(f"[{session_id}] Invalid filename path components detected: {filename}")
        raise web.HTTPForbidden(text="Invalid filename path components.")
    try:
        task_workspace = get_task_workspace_path(task_id)
        safe_filename = Path(filename).name
        file_path = (task_workspace / safe_filename).resolve()
        if not file_path.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
            logger.error(f"[{session_id}] Security Error: Access attempt outside base workspace! Req: {file_path}, Base: {BASE_WORKSPACE_ROOT.resolve()}")
            raise web.HTTPForbidden(text="Access denied - outside base workspace.")
    except (ValueError, OSError) as e:
        logger.error(f"[{session_id}] Error resolving task workspace for file access: {e}")
        raise web.HTTPInternalServerError(text="Error accessing task workspace.")
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error validating file path: {e}. Req: {filename}", exc_info=True)
        raise web.HTTPInternalServerError(text="Error validating file path")
    if not file_path.is_file():
        logger.warning(f"[{session_id}] File not found request: {file_path}")
        raise web.HTTPNotFound(text=f"File not found: {filename}")
    logger.info(f"[{session_id}] Serving file: {file_path}")
    return FileResponse(path=file_path)

def sanitize_filename(filename: str) -> str:
    # ... (unchanged)
    if not filename: return f"uploaded_file_{uuid.uuid4().hex[:8]}"
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    filename = re.sub(r'\s+', '_', filename)
    if not filename: filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    filename = filename.strip('._-')
    if not filename: filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    return Path(filename).name

async def handle_file_upload(request: web.Request) -> web.Response:
    # ... (unchanged)
    task_id = request.match_info.get('task_id')
    session_id = request.headers.get("X-Session-ID", "unknown")
    logger.info(f"[{session_id}] Received file upload request for task: {task_id}")
    if not task_id:
        logger.error(f"[{session_id}] File upload request missing task_id.")
        return web.json_response({'status': 'error', 'message': 'Task ID required'}, status=400)
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id):
        logger.error(f"[{session_id}] Invalid task_id format for upload: {task_id}")
        return web.json_response({'status': 'error', 'message': 'Invalid task ID format'}, status=400)
    try:
        task_workspace = get_task_workspace_path(task_id)
    except (ValueError, OSError) as e:
        logger.error(f"[{session_id}] Error getting/creating workspace for task {task_id} during upload: {e}")
        return web.json_response({'status': 'error', 'message': 'Error accessing task workspace'}, status=500)
    reader = None; saved_files = []; errors = []
    try:
        reader = await request.multipart()
    except Exception as e:
        logger.error(f"[{session_id}] Error reading multipart form data for task {task_id}: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'message': f'Failed to read upload data: {e}'}, status=400)
    if not reader:
         return web.json_response({'status': 'error', 'message': 'No multipart data received'}, status=400)
    while True:
        part = await reader.next()
        if part is None: logger.debug(f"[{session_id}] Finished processing multipart parts for task {task_id}."); break
        if part.name == 'file' and part.filename:
            original_filename = part.filename
            safe_filename = sanitize_filename(original_filename)
            save_path = (task_workspace / safe_filename).resolve()
            logger.info(f"[{session_id}] Processing uploaded file: '{original_filename}' -> '{safe_filename}' for task {task_id}")
            if not save_path.is_relative_to(task_workspace.resolve()):
                logger.error(f"[{session_id}] Security Error: Upload path resolves outside task workspace! Task: {task_id}, Orig: '{original_filename}', Safe: '{safe_filename}', Resolved: {save_path}")
                errors.append({'filename': original_filename, 'message': 'Invalid file path detected'}); continue
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[{session_id}] Attempting to open {save_path} for writing.")
                async with aiofiles.open(save_path, 'wb') as f:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk: break
                        await f.write(chunk)
                logger.info(f"[{session_id}] Successfully saved uploaded file to: {save_path}")
                saved_files.append({'filename': safe_filename})
                target_session_id = None
                logger.debug(f"[{session_id}] Searching for active session for task {task_id}...")
                for sid, sdata in session_data.items():
                    if sdata.get("current_task_id") == task_id:
                        target_session_id = sid
                        logger.debug(f"[{session_id}] Found target session {target_session_id} for task {task_id}.")
                        break
                if target_session_id:
                    logger.debug(f"[{session_id}] Attempting DB logging for uploaded file {safe_filename}...")
                    try:
                        await add_message(task_id, target_session_id, "artifact_generated", safe_filename)
                        logger.info(f"[{session_id}] Saved 'artifact_generated' message to DB for {safe_filename}.")
                        if target_session_id in connected_clients:
                             client_info = connected_clients[target_session_id]
                             send_func = client_info.get("send_ws_message")
                             if send_func:
                                 logger.info(f"[{target_session_id}] Sending trigger_artifact_refresh for task {task_id}")
                                 await send_func("trigger_artifact_refresh", {"taskId": task_id})
                             else: logger.warning(f"[{session_id}] Send function not found for target session {target_session_id} to send refresh trigger.")
                        else: logger.warning(f"[{session_id}] Target session {target_session_id} not found in connected_clients.")
                    except Exception as db_log_err:
                         logger.error(f"[{session_id}] Error during DB logging or WS notification after file upload for {safe_filename}: {db_log_err}", exc_info=True)
                else: logger.warning(f"[{session_id}] Could not find active session for task {task_id} to notify about upload.")
            except Exception as e:
                logger.error(f"[{session_id}] Error saving uploaded file '{safe_filename}' for task {task_id}: {e}", exc_info=True)
                errors.append({'filename': original_filename, 'message': f'Server error saving file: {type(e).__name__}'})
        else: logger.warning(f"[{session_id}] Received non-file part or part without filename in upload: Name='{part.name}', Filename='{part.filename}'")
    logger.debug(f"[{session_id}] Finished processing all parts. Errors: {len(errors)}, Saved: {len(saved_files)}")
    try:
        if errors:
            response_data = {'status': 'error', 'message': 'Some files failed to upload.', 'errors': errors, 'saved': saved_files}
            status_code = 400 if not saved_files else 207
            logger.info(f"[{session_id}] Returning error/partial success response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
        elif not saved_files:
            response_data = {'status': 'error', 'message': 'No valid files were uploaded.'}
            status_code = 400
            logger.info(f"[{session_id}] Returning no valid files error response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
        else:
            response_data = {'status': 'success', 'message': f'Successfully uploaded {len(saved_files)} file(s).', 'saved': saved_files}
            status_code = 200
            logger.info(f"[{session_id}] Returning success response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
    except Exception as return_err:
        logger.error(f"[{session_id}] CRITICAL ERROR constructing final JSON response for upload: {return_err}", exc_info=True)
        return web.Response(status=500, text="Internal server error creating upload response.")

async def get_artifacts(task_id: str) -> List[Dict[str, str]]:
    # ... (unchanged)
    logger.debug(f"Scanning workspace for artifacts for task: {task_id}")
    artifacts = []
    try:
        task_workspace_path = get_task_workspace_path(task_id)
        artifact_patterns = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.pdf'] + [f'*{ext}' for ext in TEXT_EXTENSIONS]
        all_potential_artifacts = []
        for pattern in artifact_patterns:
            for file_path in task_workspace_path.glob(pattern):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        all_potential_artifacts.append((file_path, mtime))
                    except FileNotFoundError: continue
        sorted_files = sorted(all_potential_artifacts, key=lambda x: x[1], reverse=True)
        for file_path, _ in sorted_files:
            relative_filename = str(file_path.relative_to(task_workspace_path))
            artifact_type = 'unknown'
            file_suffix = file_path.suffix.lower()
            if file_suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']: artifact_type = 'image'
            elif file_suffix in TEXT_EXTENSIONS: artifact_type = 'text'
            elif file_suffix == '.pdf': artifact_type = 'pdf'
            if artifact_type != 'unknown':
                artifact_url = f"http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}/workspace_files/{task_id}/{relative_filename}"
                artifacts.append({"type": artifact_type, "url": artifact_url, "filename": relative_filename})
        logger.info(f"Found {len(artifacts)} artifacts for task {task_id}.")
    except Exception as e:
        logger.error(f"Error scanning artifacts for task {task_id}: {e}", exc_info=True)
    return artifacts

async def setup_file_server():
    # ... (unchanged)
    app = web.Application()
    app['client_max_size'] = 100 * 1024**2
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions( allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods=["GET", "POST", "OPTIONS"])
    })
    get_resource = app.router.add_resource('/workspace_files/{task_id}/{filename:.+}')
    get_route = get_resource.add_route('GET', handle_workspace_file)
    cors.add(get_route)
    post_resource = app.router.add_resource('/upload/{task_id}')
    post_route = post_resource.add_route('POST', handle_file_upload)
    cors.add(post_route)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, FILE_SERVER_LISTEN_HOST, FILE_SERVER_PORT)
    logger.info(f"Starting file server listening on http://{FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT}")
    return site, runner

async def handler(websocket: Any):
    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id}] Connection attempt from {websocket.remote_address}...")

    async def send_ws_message_for_session(msg_type: str, content: Any):
        # ... (unchanged)
        logger.debug(f"[{session_id}] Attempting to send WS message: Type='{msg_type}', Content='{str(content)[:100]}...'")
        client_info = connected_clients.get(session_id)
        if client_info:
            ws = client_info.get("websocket")
            if ws:
                try:
                    await ws.send(json.dumps({"type": msg_type, "content": content})) # For most messages, content is the value
                    logger.debug(f"[{session_id}] Successfully sent WS message type '{msg_type}'.")
                except (ConnectionClosedOK, ConnectionClosedError) as close_exc:
                    logger.warning(f"[{session_id}] WS already closed when trying to send type '{msg_type}'. Error: {close_exc}")
                except Exception as e:
                    logger.error(f"[{session_id}] Error sending WS message type '{msg_type}': {e}", exc_info=True)
            else: logger.warning(f"[{session_id}] Websocket object not found for session when trying to send type '{msg_type}'.")
        else: logger.warning(f"[{session_id}] Session not found in connected_clients when trying to send type '{msg_type}'.")


    connected_clients[session_id] = {"websocket": websocket, "agent_task": None, "send_ws_message": send_ws_message_for_session}
    logger.info(f"[{session_id}] Client added to connected_clients dict with send function.")

    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"):
        # ... (unchanged)
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{session_id[:8]}]"
        full_content = f"{log_prefix} {text}"
        await send_ws_message_for_session("monitor_log", full_content)
        active_task_id = session_data.get(session_id, {}).get("current_task_id")
        if active_task_id:
            try:
                await add_message(active_task_id, session_id, log_type, text)
            except Exception as db_err:
                logger.error(f"[{session_id}] Failed to save monitor log '{log_type}' to DB: {db_err}")

    ws_callback_handler: Optional[WebSocketCallbackHandler] = None
    memory: Optional[ConversationBufferWindowMemory] = None
    session_setup_ok = False
    try:
        # ... (session setup logic remains the same, including planner state init) ...
        logger.info(f"[{session_id}] Starting session setup...")
        logger.debug(f"[{session_id}] Creating ConversationBufferWindowMemory (K={settings.agent_memory_window_k})...")
        memory = ConversationBufferWindowMemory(
            k=settings.agent_memory_window_k, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
        )
        logger.debug(f"[{session_id}] Memory object created.")
        logger.debug(f"[{session_id}] Creating WebSocketCallbackHandler...")
        db_add_func = functools.partial(add_message)
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message_for_session, db_add_func, session_data)
        logger.debug(f"[{session_id}] Callback handler created.")
        logger.debug(f"[{session_id}] Storing session data...")
        session_data[session_id] = {
            "memory": memory,
            "callback_handler": ws_callback_handler,
            "current_task_id": None,
            "selected_llm_provider": settings.default_provider,
            "selected_llm_model_name": settings.default_model_name,
            "cancellation_requested": False,
            "current_plan_structured": None,
            "current_plan_human_summary": None,
            "current_plan_step_index": -1,
            "plan_execution_active": False
        }
        logger.info(f"[{session_id}] Session setup complete.")
        session_setup_ok = True
    except Exception as e:
        # ... (error handling for session setup) ...
        logger.error(f"[{session_id}] CRITICAL ERROR during session setup: {e}", exc_info=True)
        if websocket and not websocket.closed:
            try: await websocket.close(code=1011, reason="Session setup failed")
            except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket during setup failure: {close_e}")
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        return
    if not session_setup_ok:
        logger.error(f"[{session_id}] Halting handler because session setup failed.")
        return

    try:
        # ... (initial messages to client remain the same) ...
        status_llm_info = f"LLM: {settings.default_provider} ({settings.default_model_name})"
        logger.info(f"[{session_id}] Sending initial status message...");
        await send_ws_message_for_session("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready. {status_llm_info}.")
        await send_ws_message_for_session("available_models", {
           "gemini": settings.gemini_available_models,
           "ollama": settings.ollama_available_models,
           "default_llm_id": settings.default_llm_id
        })
        logger.info(f"[{session_id}] Sent available_models to client.")
        logger.info(f"[{session_id}] Initial status message sent."); await add_monitor_log_and_save(f"New client connection: {websocket.remote_address}", "system_connect")
        logger.info(f"[{session_id}] Added system_connect log.")


        logger.info(f"[{session_id}] Entering message processing loop...")
        async for message_str in websocket:
            logger.debug(f"[{session_id}] Received raw message: {message_str[:200]}{'...' if len(message_str)>200 else ''}")
            try:
                data = json.loads(message_str)
                message_type = data.get("type")
                # --- MODIFIED: Get 'content' key only if it's expected to be a dict ---
                # For 'execute_confirmed_plan', the relevant data is at the top level.
                content_payload = data.get("content") # This will be None if 'content' key doesn't exist
                # --- END MODIFIED ---

                task_id_from_frontend = data.get("taskId") # Used by context_switch, delete_task
                task_title_from_frontend = data.get("task") # Used by context_switch

                current_task_id = session_data.get(session_id, {}).get("current_task_id")
                logger.debug(f"[{session_id}] Processing message type: {message_type}, Task Context: {current_task_id}")

                if message_type == "context_switch" and task_id_from_frontend:
                    # ... (context_switch logic, including resetting planner state)
                    logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")
                    if session_id in session_data:
                        session_data[session_id]['cancellation_requested'] = False
                        session_data[session_id]['current_plan_structured'] = None
                        session_data[session_id]['current_plan_human_summary'] = None
                        session_data[session_id]['current_plan_step_index'] = -1
                        session_data[session_id]['plan_execution_active'] = False
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                            logger.warning(f"[{session_id}] Cancelling active agent/plan task due to context switch.")
                            existing_agent_task.cancel()
                            await send_ws_message_for_session("status_message", "Operation cancelled due to task switch.")
                            await add_monitor_log_and_save("Agent/Plan operation cancelled due to context switch.", "system_cancel")
                            connected_clients[session_id]["agent_task"] = None
                        session_data[session_id]["current_task_id"] = task_id_from_frontend
                        session_data[session_id]["callback_handler"].set_task_id(task_id_from_frontend)
                        await add_task(task_id_from_frontend, task_title_from_frontend or f"Task {task_id_from_frontend}", datetime.datetime.now(datetime.timezone.utc).isoformat())
                        try: _ = get_task_workspace_path(task_id_from_frontend); logger.info(f"[{session_id}] Ensured workspace directory exists for task: {task_id_from_frontend}")
                        except (ValueError, OSError) as ws_path_e: logger.error(f"[{session_id}] Failed to get/create workspace path for task {task_id_from_frontend} during context switch: {ws_path_e}")
                        await add_monitor_log_and_save(f"Switched context to task ID: {task_id_from_frontend} ('{task_title_from_frontend}')", "system_context_switch")
                        if "memory" in session_data[session_id]:
                            try: session_data[session_id]["memory"].clear(); logger.info(f"[{session_id}] Cleared agent memory for new task context.")
                            except Exception as mem_e: logger.error(f"[{session_id}] Failed to clear memory on context switch: {mem_e}")
                        history_messages = await get_messages_for_task(task_id_from_frontend)
                        chat_history_for_memory = []
                        if history_messages:
                            logger.info(f"[{session_id}] Loading {len(history_messages)} history messages for task {task_id_from_frontend}.")
                            await send_ws_message_for_session("history_start", f"Loading {len(history_messages)} messages...")
                            for i, msg_hist in enumerate(history_messages):
                                db_msg_type = msg_hist.get('message_type', 'unknown')
                                db_content_hist = msg_hist.get('content', '') # Renamed to avoid conflict
                                db_timestamp = msg_hist.get('timestamp', datetime.datetime.now().isoformat())
                                ui_msg_type = None; content_to_send = db_content_hist; send_to_chat = False
                                if db_msg_type == "user_input": ui_msg_type = "user"; send_to_chat = True; chat_history_for_memory.append(HumanMessage(content=db_content_hist))
                                elif db_msg_type in ["agent_finish", "agent_message", "agent"]: ui_msg_type = "agent_message"; send_to_chat = True; chat_history_for_memory.append(AIMessage(content=db_content_hist))
                                elif db_msg_type == "artifact_generated": pass
                                elif db_msg_type.startswith(("monitor_", "error_", "system_", "tool_", "agent_thought_", "monitor_user_input", "llm_token_usage")):
                                    ui_msg_type = "monitor_log"
                                    log_prefix_hist = f"[{db_timestamp}][{session_id[:8]}]"
                                    type_indicator_hist = f"[{db_msg_type.replace('monitor_', '').replace('error_', 'ERR_').replace('system_', 'SYS_').replace('agent_thought_action', 'THOUGHT_ACT').replace('agent_thought_final', 'THOUGHT_FIN').replace('monitor_user_input', 'USER_INPUT_LOG').replace('llm_token_usage', 'TOKEN_LOG').upper()}]"
                                    content_to_send = f"{log_prefix_hist} [History]{type_indicator_hist} {db_content_hist}"
                                    send_to_chat = False
                                else: send_to_chat = False; logger.warning(f"[{session_id}] Unknown history message type '{db_msg_type}' encountered."); await send_ws_message_for_session("monitor_log", f"[{db_timestamp}][{session_id[:8]}] [History][UNKNOWN_TYPE: {db_msg_type}] {db_content_hist}")
                                if ui_msg_type:
                                    if send_to_chat: await send_ws_message_for_session(ui_msg_type, content_to_send)
                                    elif ui_msg_type == "monitor_log": await send_ws_message_for_session("monitor_log", content_to_send)
                                    await asyncio.sleep(0.005)
                            await send_ws_message_for_session("history_end", "History loaded.")
                            logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")
                            MAX_MEMORY_RELOAD = settings.agent_memory_window_k
                            if "memory" in session_data[session_id]:
                                try: session_data[session_id]["memory"].chat_memory.messages = chat_history_for_memory[-MAX_MEMORY_RELOAD:]; logger.info(f"[{session_id}] Repopulated agent memory with last {len(session_data[session_id]['memory'].chat_memory.messages)} messages.")
                                except Exception as mem_load_e: logger.error(f"[{session_id}] Failed to repopulate memory from history: {mem_load_e}")
                        else: await send_ws_message_for_session("history_end", "No history found."); logger.info(f"[{session_id}] No history found for task {task_id_from_frontend}.")
                        logger.info(f"[{session_id}] Getting current artifacts from filesystem for task {task_id_from_frontend}...")
                        current_artifacts = await get_artifacts(task_id_from_frontend)
                        await send_ws_message_for_session("update_artifacts", current_artifacts)
                        logger.info(f"[{session_id}] Sent current artifact list ({len(current_artifacts)} items) for task {task_id_from_frontend}.")
                    else: logger.error(f"[{session_id}] Context switch received but no session data found!"); await send_ws_message_for_session("status_message", "Error: Session data lost. Please refresh.")

                elif message_type == "user_message":
                    # ... (user_message logic up to planner call remains the same) ...
                    # Ensure content_payload is used for user_input_content
                    user_input_content = ""
                    if isinstance(content_payload, str): user_input_content = content_payload # Use content_payload
                    else: logger.warning(f"[{session_id}] Received non-string content for user_message: {type(content_payload)}. Ignoring."); continue
                    
                    # ... (rest of user_message logic for planning)
                    active_task_id = session_data.get(session_id, {}).get("current_task_id")
                    if not active_task_id:
                        logger.warning(f"[{session_id}] User message received but no task active.")
                        await send_ws_message_for_session("status_message", "Please select or create a task first.")
                        continue
                    if connected_clients.get(session_id, {}).get("agent_task") or session_data.get(session_id, {}).get("plan_execution_active"):
                        logger.warning(f"[{session_id}] User message received while agent/plan is already running for task {active_task_id}.")
                        await send_ws_message_for_session("status_message", "Agent is busy. Please wait or stop the current process.")
                        continue

                    await add_message(active_task_id, session_id, "user_input", user_input_content)
                    await add_monitor_log_and_save(f"User Input: {user_input_content}", "monitor_user_input")

                    if session_id not in session_data: logger.error(f"[{session_id}] User message for task {active_task_id} but no session data found!"); continue

                    session_data[session_id]['cancellation_requested'] = False
                    await send_ws_message_for_session("agent_thinking_update", {"status": "Generating plan..."})

                    selected_provider = session_data[session_id].get("selected_llm_provider", settings.default_provider)
                    selected_model_name = session_data[session_id].get("selected_llm_model_name", settings.default_model_name)
                    planner_llm: Optional[BaseChatModel] = None
                    try:
                        planner_llm = get_llm(settings, provider=selected_provider, model_name=selected_model_name)
                    except Exception as llm_init_err:
                        logger.error(f"[{session_id}] Failed to initialize LLM for planner: {llm_init_err}", exc_info=True)
                        await add_monitor_log_and_save(f"Error initializing LLM for planner: {llm_init_err}", "error_system")
                        await send_ws_message_for_session("status_message", "Error: Failed to prepare for planning.")
                        await send_ws_message_for_session("agent_message", f"Sorry, could not initialize the planning module.")
                        continue
                    
                    dynamic_tools = get_dynamic_tools(active_task_id)
                    tools_summary_for_planner = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])

                    human_plan_summary, structured_plan_steps = await generate_plan(
                        user_query=user_input_content,
                        llm=planner_llm,
                        available_tools_summary=tools_summary_for_planner
                    )

                    if human_plan_summary and structured_plan_steps:
                        session_data[session_id]["current_plan_human_summary"] = human_plan_summary
                        session_data[session_id]["current_plan_structured"] = structured_plan_steps
                        session_data[session_id]["current_plan_step_index"] = 0
                        session_data[session_id]["plan_execution_active"] = False

                        await send_ws_message_for_session("display_plan_for_confirmation", {
                            "human_summary": human_plan_summary,
                            "structured_plan": structured_plan_steps
                        })
                        await add_monitor_log_and_save(f"Plan generated. Summary: {human_plan_summary}. Steps: {len(structured_plan_steps)}. Awaiting user confirmation.", "system_plan_generated")
                        await send_ws_message_for_session("status_message", "Plan generated. Please review and confirm.")
                        await send_ws_message_for_session("agent_thinking_update", {"status": "Awaiting plan confirmation..."})
                    else:
                        logger.error(f"[{session_id}] Failed to generate a plan for query: {user_input_content}")
                        await add_monitor_log_and_save(f"Error: Failed to generate a plan.", "error_system")
                        await send_ws_message_for_session("status_message", "Error: Could not generate a plan for your request.")
                        await send_ws_message_for_session("agent_message", "I'm sorry, I couldn't create a plan for that request. Please try rephrasing or breaking it down.")
                        await send_ws_message_for_session("agent_thinking_update", {"status": "Planning failed."})


                elif message_type == "execute_confirmed_plan":
                    logger.info(f"[{session_id}] Received 'execute_confirmed_plan'.")
                    active_task_id = session_data.get(session_id, {}).get("current_task_id")
                    if not active_task_id:
                        logger.warning(f"[{session_id}] 'execute_confirmed_plan' received but no active task.")
                        await send_ws_message_for_session("status_message", "Error: No active task to execute plan for.")
                        continue

                    # --- MODIFIED: Get 'confirmed_plan' directly from 'data' ---
                    confirmed_plan = data.get("confirmed_plan") # Not from content_payload
                    # --- END MODIFIED ---

                    if not confirmed_plan or not isinstance(confirmed_plan, list):
                        logger.error(f"[{session_id}] Invalid or missing plan in 'execute_confirmed_plan' message. Data received: {data}")
                        await send_ws_message_for_session("status_message", "Error: Invalid plan received for execution.")
                        continue

                    session_data[session_id]["current_plan_structured"] = confirmed_plan
                    session_data[session_id]["current_plan_step_index"] = 0
                    session_data[session_id]["plan_execution_active"] = True
                    session_data[session_id]['cancellation_requested'] = False

                    await add_monitor_log_and_save(f"User confirmed plan. Starting execution of {len(confirmed_plan)} steps.", "system_plan_confirmed")
                    await send_ws_message_for_session("status_message", "Plan confirmed. Executing steps...")

                    logger.warning(f"[{session_id}] PLAN EXECUTION LOOP NOT YET IMPLEMENTED.")
                    await send_ws_message_for_session("agent_thinking_update", {"status": "Starting plan execution (dev placeholder)..."})
                    await asyncio.sleep(2)
                    session_data[session_id]["plan_execution_active"] = False
                    session_data[session_id]["current_plan_step_index"] = -1
                    await send_ws_message_for_session("agent_thinking_update", {"status": "Plan execution finished (dev placeholder)."})
                    await send_ws_message_for_session("status_message", "Plan execution complete (placeholder).")

                # ... (other message types: new_task, delete_task, rename_task, set_llm, cancel_agent, get_artifacts_for_task, run_command, action_command, unknown)
                elif message_type == "new_task":
                    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context.")
                    current_task_id = None
                    if session_id in session_data:
                        session_data[session_id]['cancellation_requested'] = False
                        session_data[session_id]['current_plan_structured'] = None
                        session_data[session_id]['current_plan_human_summary'] = None
                        session_data[session_id]['current_plan_step_index'] = -1
                        session_data[session_id]['plan_execution_active'] = False
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                                logger.warning(f"[{session_id}] Cancelling active agent/plan task due to new task.")
                                existing_agent_task.cancel()
                                await send_ws_message_for_session("status_message", "Operation cancelled for new task.")
                                await add_monitor_log_and_save("Agent/Plan operation cancelled due to new task creation.", "system_cancel")
                                connected_clients[session_id]["agent_task"] = None
                        session_data[session_id]["current_task_id"] = None
                        session_data[session_id]["callback_handler"].set_task_id(None)
                        if "memory" in session_data[session_id]: session_data[session_id]["memory"].clear()
                        await add_monitor_log_and_save("Cleared context for new task.", "system_new_task")
                        await send_ws_message_for_session("update_artifacts", [])
                    else: logger.error(f"[{session_id}] 'new_task' signal received but no session data found!")

                elif message_type == "delete_task" and task_id_from_frontend:
                    logger.warning(f"[{session_id}] Received request to delete task: {task_id_from_frontend}")
                    await add_monitor_log_and_save(f"Received request to delete task: {task_id_from_frontend}", "system_delete_request")
                    deleted = await delete_task_and_messages(task_id_from_frontend)
                    if deleted:
                        await add_monitor_log_and_save(f"Task {task_id_from_frontend} deleted successfully from DB.", "system_delete_success")
                        task_workspace_to_delete : Optional[Path] = None
                        try:
                            task_workspace_to_delete = get_task_workspace_path(task_id_from_frontend)
                            if task_workspace_to_delete.exists() and task_workspace_to_delete.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
                                import shutil; await asyncio.to_thread(shutil.rmtree, task_workspace_to_delete)
                                logger.info(f"[{session_id}] Successfully deleted workspace directory: {task_workspace_to_delete}")
                                await add_monitor_log_and_save(f"Workspace directory deleted: {task_workspace_to_delete.name}", "system_delete_success")
                            else: logger.warning(f"[{session_id}] Workspace directory not found or invalid for deletion: {task_workspace_to_delete}")
                        except Exception as ws_del_e: logger.error(f"[{session_id}] Error deleting workspace directory {task_workspace_to_delete}: {ws_del_e}"); await add_monitor_log_and_save(f"Error deleting workspace directory: {ws_del_e}", "error_delete")
                        active_task_id_check = session_data.get(session_id, {}).get("current_task_id")
                        if active_task_id_check == task_id_from_frontend:
                            current_task_id = None
                            if session_id in session_data:
                                session_data[session_id]['cancellation_requested'] = False
                                session_data[session_id]['current_plan_structured'] = None
                                session_data[session_id]['current_plan_human_summary'] = None
                                session_data[session_id]['current_plan_step_index'] = -1
                                session_data[session_id]['plan_execution_active'] = False
                                existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                                if existing_agent_task and not existing_agent_task.done(): existing_agent_task.cancel()
                                connected_clients[session_id]["agent_task"] = None; session_data[session_id]["current_task_id"] = None; session_data[session_id]["callback_handler"].set_task_id(None)
                                if "memory" in session_data[session_id]: session_data[session_id]["memory"].clear()
                                await add_monitor_log_and_save("Cleared context as active task was deleted.", "system_context_clear")
                                await send_ws_message_for_session("update_artifacts", [])
                    else: await send_ws_message_for_session("status_message", f"Failed to delete task {task_id_from_frontend[:8]}..."); await add_monitor_log_and_save(f"Failed to delete task {task_id_from_frontend} from DB.", "error_delete")

                elif message_type == "rename_task":
                    task_id_to_rename = data.get("taskId"); new_name = data.get("newName") # Using data directly
                    if not task_id_to_rename or not new_name: logger.warning(f"[{session_id}] Received invalid rename_task message: {data}"); await add_monitor_log_and_save(f"Error: Received invalid rename request (missing taskId or newName).", "error_system"); continue
                    logger.info(f"[{session_id}] Received request to rename task {task_id_to_rename} to '{new_name}'."); await add_monitor_log_and_save(f"Received rename request for task {task_id_to_rename} to '{new_name}'.", "system_rename_request")
                    renamed_in_db = await rename_task_in_db(task_id_to_rename, new_name)
                    if renamed_in_db: logger.info(f"[{session_id}] Successfully renamed task {task_id_to_rename} in database."); await add_monitor_log_and_save(f"Task {task_id_to_rename} renamed to '{new_name}' in DB.", "system_rename_success")
                    else: logger.error(f"[{session_id}] Failed to rename task {task_id_to_rename} in database."); await add_monitor_log_and_save(f"Failed to rename task {task_id_to_rename} in DB.", "error_db")

                elif message_type == "set_llm":
                    llm_id = data.get("llm_id") # Using data directly
                    if llm_id and isinstance(llm_id, str):
                        try:
                            provider, model_name = llm_id.split("::", 1); is_valid = False
                            if provider == 'gemini' and model_name in settings.gemini_available_models: is_valid = True
                            elif provider == 'ollama' and model_name in settings.ollama_available_models: is_valid = True
                            if is_valid:
                                if session_id in session_data:
                                    session_data[session_id]["selected_llm_provider"] = provider
                                    session_data[session_id]["selected_llm_model_name"] = model_name
                                    logger.info(f"[{session_id}] Set session LLM to: {provider}::{model_name}")
                                    await add_monitor_log_and_save(f"Session LLM set to {provider}::{model_name}", "system_llm_set")
                                else: logger.error(f"[{session_id}] Cannot set LLM: Session data not found.")
                            else: logger.warning(f"[{session_id}] Received request to set invalid/unavailable LLM ID: {llm_id}"); await add_monitor_log_and_save(f"Attempted to set invalid LLM: {llm_id}", "error_llm_set")
                        except ValueError: logger.warning(f"[{session_id}] Received invalid LLM ID format in set_llm: {llm_id}"); await add_monitor_log_and_save(f"Received invalid LLM ID format: {llm_id}", "error_llm_set")
                    else: logger.warning(f"[{session_id}] Received invalid 'set_llm' message content: {data}")

                elif message_type == "get_available_models":
                     logger.info(f"[{session_id}] Received request for available models.")
                     await send_ws_message_for_session("available_models", {
                         "gemini": settings.gemini_available_models,
                         "ollama": settings.ollama_available_models,
                         "default_llm_id": settings.default_llm_id
                     })

                elif message_type == "cancel_agent":
                    logger.warning(f"[{session_id}] Received request to cancel current operation.")
                    if session_id in session_data:
                        session_data[session_id]['cancellation_requested'] = True
                        logger.info(f"[{session_id}] Cancellation requested flag set to True.")
                        agent_task_to_cancel = connected_clients.get(session_id, {}).get("agent_task")
                        if agent_task_to_cancel and not agent_task_to_cancel.done():
                            agent_task_to_cancel.cancel()
                            logger.info(f"[{session_id}] asyncio.Task.cancel() called for active task.")
                        else:
                            logger.info(f"[{session_id}] No active asyncio task found to cancel, or task already done. Flag will be checked by callbacks/plan loop.")
                    else:
                        logger.error(f"[{session_id}] Cannot set cancellation flag: Session data not found.")

                elif message_type == "get_artifacts_for_task":
                    task_id_to_refresh = data.get("taskId") # Using data directly
                    if not task_id_to_refresh: logger.warning(f"[{session_id}] Received get_artifacts_for_task without taskId."); continue
                    logger.info(f"[{session_id}] Received request to refresh artifacts for task: {task_id_to_refresh}")
                    if task_id_to_refresh == current_task_id:
                        artifacts = await get_artifacts(task_id_to_refresh)
                        await send_ws_message_for_session("update_artifacts", artifacts)
                        logger.info(f"[{session_id}] Sent updated artifact list for task {task_id_to_refresh}.")
                    else: logger.warning(f"[{session_id}] Received artifact refresh request for non-active task ({task_id_to_refresh} vs {current_task_id}). Ignoring.")

                elif message_type == "run_command":
                    command_to_run = data.get("command") # Using data directly
                    if command_to_run and isinstance(command_to_run, str):
                        active_task_id_for_cmd = session_data.get(session_id, {}).get("current_task_id")
                        await add_monitor_log_and_save(f"Received direct 'run_command'. Executing: {command_to_run} (Task Context: {active_task_id_for_cmd})", "system_direct_cmd")
                        await execute_shell_command(command_to_run, session_id, send_ws_message_for_session, add_message, active_task_id_for_cmd)
                    else: logger.warning(f"[{session_id}] Received 'run_command' with invalid/missing command content."); await add_monitor_log_and_save("Error: 'run_command' received with no command specified.", "error_direct_cmd")

                elif message_type == "action_command":
                    action = data.get("command") # Using data directly
                    if action and isinstance(action, str):
                        logger.info(f"[{session_id}] Received action command: {action} (Not implemented).")
                        await add_monitor_log_and_save(f"Received action command: {action} (Handler not implemented).", "system_action_cmd")
                    else: logger.warning(f"[{session_id}] Received 'action_command' with invalid/missing command content.")


                else:
                    logger.warning(f"[{session_id}] Unknown message type received: {message_type}")
                    await add_monitor_log_and_save(f"Received unknown message type: {message_type}", "error_unknown_msg")

            except json.JSONDecodeError: logger.error(f"[{session_id}] Received non-JSON message: {message_str[:200]}{'...' if len(message_str)>200 else ''}"); await add_monitor_log_and_save("Error: Received invalid message format (not JSON).", "error_json")
            except asyncio.CancelledError: logger.info(f"[{session_id}] Message processing loop cancelled."); raise
            except Exception as e:
                logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                try: await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing"); await send_ws_message_for_session("status_message", f"Error processing message: {type(e).__name__}")
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
             logger.warning(f"[{session_id}] Cancelling active task during cleanup.")
             agent_task.cancel()
             try: await agent_task
             except asyncio.CancelledError: pass
             except AgentCancelledException: pass
             except Exception as cancel_e: logger.error(f"[{session_id}] Error waiting for task cancellation during cleanup: {cancel_e}")
         if session_id in connected_clients: del connected_clients[session_id]
         if session_id in session_data: del session_data[session_id]
         logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}. Active clients: {len(connected_clients)}")


async def main():
    # ... (unchanged)
    await init_db()
    file_server_site, file_server_runner = await setup_file_server()
    await file_server_site.start()
    logger.info("File server started.")
    ws_host = "0.0.0.0"
    ws_port = 8765
    logger.info(f"Starting WebSocket server on ws://{ws_host}:{ws_port}")
    shutdown_event = asyncio.Event()
    websocket_server = await websockets.serve(
        handler, ws_host, ws_port, max_size=settings.websocket_max_size_bytes,
        ping_interval=settings.websocket_ping_interval, ping_timeout=settings.websocket_ping_timeout
    )
    logger.info("WebSocket server started.")
    loop = asyncio.get_running_loop()
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    original_sigterm_handler = signal.getsignal(signal.SIGTERM)
    def signal_handler(sig, frame): logger.info(f"Received signal {sig}. Initiating shutdown..."); shutdown_event.set(); signal.signal(signal.SIGINT, original_sigint_handler); signal.signal(signal.SIGTERM, original_sigterm_handler)
    try: loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT, None); loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM, None)
    except NotImplementedError: logger.warning("Signal handlers not available on this platform (Windows?). Use Ctrl+C.")
    logger.info("Application servers running. Press Ctrl+C to stop.")
    await shutdown_event.wait()
    logger.info("Shutdown signal received. Stopping servers...")
    logger.info("Stopping WebSocket server..."); websocket_server.close(); await websocket_server.wait_closed(); logger.info("WebSocket server stopped.")
    logger.info("Stopping file server..."); await file_server_runner.cleanup(); logger.info("File server stopped.")
    tasks_to_cancel = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()] # Renamed variable
    if tasks_to_cancel: logger.info(f"Cancelling {len(tasks_to_cancel)} outstanding tasks..."); [task_to_cancel_item.cancel() for task_to_cancel_item in tasks_to_cancel]; await asyncio.gather(*tasks_to_cancel, return_exceptions=True); logger.info("Outstanding tasks cancelled.")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith API key.*")
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmithMissingAPIKeyWarning.*")
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("Server stopped manually (KeyboardInterrupt).")
    except Exception as e: logging.critical(f"Server failed to start or crashed: {e}", exc_info=True); exit(1)
