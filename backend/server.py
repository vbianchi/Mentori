# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import uuid
from typing import Optional, List, Dict, Any, Callable, Coroutine
from pathlib import Path
import os
import signal
import re
import functools
import warnings 
import aiofiles
import unicodedata
import urllib.parse

# --- Web Server Imports ---
from aiohttp import web
from aiohttp.web import FileResponse 
import aiohttp_cors
# -------------------------

# LangChain Imports
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.language_models.base import BaseLanguageModel 
from langchain_core.language_models.chat_models import BaseChatModel 

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
from backend.message_handlers import ( 
    process_context_switch, process_user_message,
    process_execute_confirmed_plan, process_new_task,
    process_delete_task, process_rename_task,
    process_set_llm, process_get_available_models,
    process_cancel_agent, process_get_artifacts_for_task,
    process_run_command, process_action_command,
    process_set_session_role_llm,
    process_cancel_plan_proposal 
)

# Define Type Aliases for callback functions used in MessageHandler hint
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
DBAddTaskFunc = Callable[[str, str, str], Coroutine[Any, Any, None]]
DBGetMessagesFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, Any]]]]
DBDeleteTaskFunc = Callable[[str], Coroutine[Any, Any, bool]]
DBRenameTaskFunc = Callable[[str, str], Coroutine[Any, Any, bool]]
GetArtifactsFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, str]]]]
ExecuteShellCommandFunc = Callable[[str, str, SendWSMessageFunc, DBAddMessageFunc, Optional[str]], Coroutine[Any, Any, bool]]


log_level = settings.log_level
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to {log_level}")

try:
    default_llm_instance_for_startup_checks: BaseLanguageModel = get_llm(settings, provider=settings.default_provider, model_name=settings.default_model_name)
    logger.info(f"Default Base LLM for startup checks initialized successfully: {settings.default_provider}::{settings.default_model_name}")
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
    log_prefix_base = f"[{session_id[:8]}]"
    while True:
        try: line = await stream.readline()
        except Exception as e: logger.error(f"[{session_id}] Error reading stream {stream_name}: {e}"); break
        if not line: break
        line_content = line.decode(errors='replace').rstrip(); 
        log_content = f"[{stream_name}] {line_content}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message_func("monitor_log", f"[{timestamp}]{log_prefix_base} {log_content}")
        if current_task_id:
            try: await db_add_message_func(current_task_id, session_id, f"monitor_{stream_name}", line_content)
            except Exception as db_err: logger.error(f"[{session_id}] Failed to save {stream_name} log to DB: {db_err}")
    logger.debug(f"[{session_id}] {stream_name} stream finished.")


async def execute_shell_command(command: str, session_id: str, send_ws_message_func: SendWSMessageFunc, db_add_message_func: DBAddMessageFunc, current_task_id: Optional[str]) -> bool:
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
            logger.error(f"[{session_id}] Timeout executing direct command: {command}"); 
            status_msg = f"failed (Timeout after {TIMEOUT_SECONDS}s)"; success = False
            if process and process.returncode is None:
                try: process.terminate()
                except ProcessLookupError: pass
                await process.wait()
            for task_to_cancel in pending: task_to_cancel.cancel()
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
    # <<< START CHANGE 1 >>>
    # Added critical debug logging at the start of the handler
    session_id_from_header = request.headers.get("X-Session-ID", "unknown_file_request_session") # Get session ID earlier for logging
    logger.critical(f"CRITICAL_DEBUG: [{session_id_from_header}] handle_workspace_file REACHED. Method: {request.method}, Path: {request.path}")
    logger.info(f"[{session_id_from_header}] Request headers for handle_workspace_file: {dict(request.headers)}")
    # <<< END CHANGE 1 >>>

    task_id = request.match_info.get('task_id')
    filename = request.match_info.get('filename')
    # session_id already retrieved above for logging
    logger.info(f"[{session_id_from_header}] File server: Received request for task_id='{task_id}', filename='{filename}'")
    if not task_id or not filename:
        logger.warning(f"[{session_id_from_header}] File server request missing task_id or filename.")
        raise web.HTTPBadRequest(text="Task ID and filename required")
    
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id): 
        logger.error(f"[{session_id_from_header}] Invalid task_id format rejected: {task_id}")
        raise web.HTTPForbidden(text="Invalid task ID format.")
    
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        logger.error(f"[{session_id_from_header}] Invalid filename path components detected: {filename}")
        raise web.HTTPForbidden(text="Invalid filename path components.")

    try:
        task_workspace = get_task_workspace_path(task_id, create_if_not_exists=False)
        safe_filename = Path(filename).name 
        
        file_path = (task_workspace / safe_filename).resolve()
        logger.debug(f"[{session_id_from_header}] File server: Resolved file path: {file_path}")

        if not file_path.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
            logger.error(f"[{session_id_from_header}] Security Error: Access attempt outside base workspace! Req: {file_path}, Base: {BASE_WORKSPACE_ROOT.resolve()}")
            raise web.HTTPForbidden(text="Access denied - outside base workspace.")
            
    except ValueError as ve: 
        logger.error(f"[{session_id_from_header}] File server: Invalid task_id for file access: {ve}")
        raise web.HTTPBadRequest(text=f"Invalid task ID: {ve}")
    except OSError as e: 
        logger.error(f"[{session_id_from_header}] File server: Error resolving task workspace for file access: {e}")
        raise web.HTTPInternalServerError(text="Error accessing task workspace.")
    except Exception as e: 
        logger.error(f"[{session_id_from_header}] File server: Unexpected error validating file path: {e}. Req: {filename}", exc_info=True)
        raise web.HTTPInternalServerError(text="Error validating file path")

    if not file_path.is_file(): 
        logger.warning(f"[{session_id_from_header}] File server: File not found request: {file_path}")
        raise web.HTTPNotFound(text=f"File not found: {filename}")
    
    logger.info(f"[{session_id_from_header}] File server: Serving file: {file_path}")
    return FileResponse(path=file_path)


def sanitize_filename(filename: str) -> str:
    if not filename:
        return f"uploaded_file_{uuid.uuid4().hex[:8]}"
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    filename = re.sub(r'\s+', '_', filename)
    if not filename:
        filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    filename = filename.strip('._-')
    if not filename: 
        filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    return Path(filename).name 

async def handle_file_upload(request: web.Request) -> web.Response:
    session_id = request.headers.get("X-Session-ID", "unknown_upload_session") 
    task_id_from_matchinfo = request.match_info.get('task_id')
    logger.critical(f"CRITICAL_DEBUG: [{session_id}] handle_file_upload REACHED for task_id: '{task_id_from_matchinfo}' with method: {request.method}")
    logger.info(f"[{session_id}] File Upload: Received headers: {dict(request.headers)}")

    task_id = request.match_info.get('task_id')
    logger.info(f"[{session_id}] File Upload: Received request for task_id: '{task_id}'")

    if not task_id:
        logger.error(f"[{session_id}] File Upload: Missing task_id.")
        return web.json_response({'status': 'error', 'message': 'Task ID required'}, status=400)
    
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id):
        logger.error(f"[{session_id}] File Upload: Invalid task_id format: '{task_id}'")
        return web.json_response({'status': 'error', 'message': 'Invalid task ID format'}, status=400)

    task_workspace: Path
    try:
        task_workspace = get_task_workspace_path(task_id, create_if_not_exists=True)
        logger.info(f"[{session_id}] File Upload: Ensured task workspace exists at: {task_workspace}")
    except ValueError as ve:
        logger.error(f"[{session_id}] File Upload: Invalid task_id for workspace creation: {ve}")
        return web.json_response({'status': 'error', 'message': f'Invalid task ID for workspace: {ve}'}, status=400)
    except OSError as e:
        logger.error(f"[{session_id}] File Upload: Error getting/creating workspace for task {task_id}: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'message': 'Error accessing/creating task workspace'}, status=500)
    
    reader = None
    saved_files = []
    errors = []

    try:
        reader = await request.multipart()
    except Exception as e: 
        logger.error(f"[{session_id}] File Upload: Error reading multipart form data for task {task_id}: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'message': f'Failed to read upload data: {e}'}, status=400)

    if not reader:
        return web.json_response({'status': 'error', 'message': 'No multipart data received'}, status=400)

    while True:
        part = await reader.next()
        if part is None:
            logger.debug(f"[{session_id}] File Upload: Finished processing multipart parts for task {task_id}.")
            break

        if part.name == 'file' and part.filename: 
            original_filename = part.filename
            safe_filename = sanitize_filename(original_filename) 
            
            save_path = (task_workspace / safe_filename).resolve() 
            logger.info(f"[{session_id}] File Upload: Processing uploaded file: '{original_filename}' -> '{safe_filename}' for task {task_id}. Target path: {save_path}")

            if not save_path.is_relative_to(task_workspace.resolve()):
                logger.error(f"[{session_id}] File Upload: Security Error - Upload path resolves outside task workspace! Task: {task_id}, Orig: '{original_filename}', Safe: '{safe_filename}', Resolved: {save_path}, Workspace: {task_workspace.resolve()}")
                errors.append({'filename': original_filename, 'message': 'Invalid file path detected (path traversal attempt).'})
                continue 

            try:
                save_path.parent.mkdir(parents=True, exist_ok=True) 
                
                logger.debug(f"[{session_id}] File Upload: Attempting to open {save_path} for writing.")
                async with aiofiles.open(save_path, 'wb') as f:
                    while True:
                        chunk = await part.read_chunk() 
                        if not chunk:
                            break
                        await f.write(chunk)
                logger.info(f"[{session_id}] File Upload: Successfully saved uploaded file to: {save_path}")
                saved_files.append({'filename': safe_filename}) 

                target_session_id_for_ws_notify = None
                for sid_iter, sdata_val_iter in session_data.items(): 
                    if sdata_val_iter.get("current_task_id") == task_id:
                        target_session_id_for_ws_notify = sid_iter
                        logger.debug(f"[{session_id}] File Upload: Found active session {target_session_id_for_ws_notify} for task {task_id} for WS notification.")
                        break
                
                if target_session_id_for_ws_notify:
                    try:
                        await add_message(task_id, target_session_id_for_ws_notify, "artifact_generated", safe_filename)
                        logger.info(f"[{session_id}] File Upload: Saved 'artifact_generated' message to DB for {safe_filename} (session: {target_session_id_for_ws_notify}).")
                        
                        client_info_for_ws = connected_clients.get(target_session_id_for_ws_notify)
                        if client_info_for_ws:
                            send_func_for_ws = client_info_for_ws.get("send_ws_message")
                            if send_func_for_ws:
                                logger.info(f"[{target_session_id_for_ws_notify}] File Upload: Sending trigger_artifact_refresh for task {task_id}")
                                await send_func_for_ws("trigger_artifact_refresh", {"taskId": task_id})
                            else: logger.warning(f"[{session_id}] File Upload: Send function not found for target session {target_session_id_for_ws_notify} to send refresh trigger.")
                        else: logger.warning(f"[{session_id}] File Upload: Target session {target_session_id_for_ws_notify} not found in connected_clients for WS notification.")
                    except Exception as db_log_err:
                        logger.error(f"[{session_id}] File Upload: Error during DB logging or WS notification after file upload for {safe_filename}: {db_log_err}", exc_info=True)
                else:
                    logger.warning(f"[{session_id}] File Upload: Could not find an active session for task {task_id} to notify about upload of {safe_filename} via WebSocket.")

            except Exception as e:
                logger.error(f"[{session_id}] File Upload: Error saving uploaded file '{safe_filename}' for task {task_id}: {e}", exc_info=True)
                errors.append({'filename': original_filename, 'message': f'Server error saving file: {type(e).__name__}'})
        else:
            logger.warning(f"[{session_id}] File Upload: Received non-file part or part without filename in upload: Name='{part.name if hasattr(part, 'name') else 'N/A'}', Filename='{part.filename if hasattr(part, 'filename') else 'N/A'}'")
    
    logger.debug(f"[{session_id}] File Upload: Finished processing all parts. Errors: {len(errors)}, Saved: {len(saved_files)}")

    try:
        if errors:
            response_data = {'status': 'error', 'message': 'Some files failed to upload.', 'errors': errors, 'saved': saved_files}
            status_code = 400 if not saved_files else 207 
            logger.info(f"[{session_id}] File Upload: Returning error/partial success response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
        elif not saved_files:
            response_data = {'status': 'error', 'message': 'No valid files were uploaded.'}
            status_code = 400
            logger.info(f"[{session_id}] File Upload: Returning no valid files error response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
        else: 
            response_data = {'status': 'success', 'message': f'Successfully uploaded {len(saved_files)} file(s).', 'saved': saved_files}
            status_code = 200
            logger.info(f"[{session_id}] File Upload: Returning success response: Status={status_code}, Data={response_data}")
            return web.json_response(response_data, status=status_code)
    except Exception as return_err: 
        logger.error(f"[{session_id}] File Upload: CRITICAL ERROR constructing final JSON response for upload: {return_err}", exc_info=True)
        return web.Response(status=500, text="Internal server error creating upload response.")


async def get_artifacts(task_id: str) -> List[Dict[str, str]]:
    logger.debug(f"Scanning workspace for artifacts for task: {task_id}")
    artifacts = []
    try:
        task_workspace_path = get_task_workspace_path(task_id, create_if_not_exists=False) 
        if not task_workspace_path.exists():
            logger.warning(f"Artifact scan: Workspace for task {task_id} does not exist at {task_workspace_path}. Returning empty list.")
            return []
            
        artifact_patterns = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.pdf'] + [f'*{ext}' for ext in TEXT_EXTENSIONS]
        all_potential_artifacts = []
        for pattern in artifact_patterns:
            for file_path in task_workspace_path.glob(pattern):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        all_potential_artifacts.append((file_path, mtime))
                    except FileNotFoundError: 
                        logger.warning(f"File disappeared during artifact scan: {file_path}")
                        continue
        
        sorted_files = sorted(all_potential_artifacts, key=lambda x: x[1], reverse=True)

        for file_path, _ in sorted_files:
            relative_filename = str(file_path.relative_to(task_workspace_path))
            artifact_type = 'unknown'
            file_suffix = file_path.suffix.lower()

            if file_suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']: artifact_type = 'image'
            elif file_suffix in TEXT_EXTENSIONS: artifact_type = 'text'
            elif file_suffix == '.pdf': artifact_type = 'pdf'

            if artifact_type != 'unknown':
                encoded_filename = urllib.parse.quote(relative_filename) 
                artifact_url = f"http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}/workspace_files/{task_id}/{encoded_filename}"
                artifacts.append({"type": artifact_type, "url": artifact_url, "filename": relative_filename})
        logger.info(f"Found {len(artifacts)} artifacts for task {task_id}.")
    except ValueError as ve: 
        logger.error(f"Error scanning artifacts for task {task_id} due to invalid task ID: {ve}")
    except Exception as e:
        logger.error(f"Error scanning artifacts for task {task_id}: {e}", exc_info=True)
    return artifacts

async def setup_file_server():
    app = web.Application()
    app['client_max_size'] = 100 * 1024**2  

    logger.info("FILE_SERVER: Configuring CORS...")
    cors = aiohttp_cors.setup(app, defaults={ 
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers=("Content-Type", "X-Session-ID", "Authorization", "X-Requested-With", "Accept", "Origin"), 
            allow_methods=["GET", "POST", "OPTIONS"] 
        )
    })
    logger.info("FILE_SERVER: Default CORS options set.")

    logger.info(f"FILE_SERVER: Configuring /workspace_files/{{task_id}}/{{filename:.+}} GET route with handler: {handle_workspace_file.__name__}")
    get_resource = app.router.add_resource('/workspace_files/{task_id}/{filename:.+}') 
    get_route = get_resource.add_route('GET', handle_workspace_file)
    logger.info(f"FILE_SERVER: Route {get_route} for GET /workspace_files added.")
    
    cors.add(get_route, {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            # <<< START CHANGE 2 >>>
            allow_headers="*", # Changed from specific list to wildcard for GET route
            # <<< END CHANGE 2 >>>
            allow_methods=["GET", "OPTIONS"], 
        )
    })
    logger.info(f"FILE_SERVER: Explicit CORS configured for GET /workspace_files/{{task_id}}/{{filename}} route (allow_headers='*').")

    logger.info(f"FILE_SERVER: About to configure /upload/{{task_id}} POST route with handler: {handle_file_upload.__name__}")
    post_resource = app.router.add_resource('/upload/{task_id}')
    post_route = post_resource.add_route('POST', handle_file_upload)
    logger.info(f"FILE_SERVER: Route {post_route} for POST /upload/{{task_id}} added to router.")
    
    cors.add(post_route, {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*", 
            allow_headers=("Content-Type", "X-Session-ID", "Authorization", "X-Requested-With", "Accept", "Origin"), 
            allow_methods=["POST", "OPTIONS"], 
        )
    })
    logger.info(f"FILE_SERVER: Explicit CORS configured for POST /upload/{{task_id}} route.")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, FILE_SERVER_LISTEN_HOST, FILE_SERVER_PORT)
    logger.info(f"Starting file server listening on http://{FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT}")
    return site, runner


async def handler(websocket: Any): 
    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id}] Connection attempt from {websocket.remote_address}...")

    async def send_ws_message_for_session(msg_type: str, content: Any):
        logger.debug(f"[{session_id}] Attempting to send WS message: Type='{msg_type}', Content='{str(content)[:100]}...'")
        client_info = connected_clients.get(session_id)
        if client_info:
            ws = client_info.get("websocket")
            if ws: 
                try:
                    await ws.send(json.dumps({"type": msg_type, "content": content}))
                    logger.debug(f"[{session_id}] Successfully sent WS message type '{msg_type}'.")
                except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError) as close_exc:
                    logger.warning(f"[{session_id}] WS already closed when trying to send type '{msg_type}'. Error: {close_exc}")
                except Exception as e: 
                    logger.error(f"[{session_id}] Error sending WS message type '{msg_type}': {e}", exc_info=True)
            else: logger.warning(f"[{session_id}] Websocket object not found for session when trying to send type '{msg_type}'.")
        else: logger.warning(f"[{session_id}] Session not found in connected_clients when trying to send type '{msg_type}'.")


    connected_clients[session_id] = {"websocket": websocket, "agent_task": None, "send_ws_message": send_ws_message_for_session}
    logger.info(f"[{session_id}] Client added to connected_clients dict with send function.")

    try:
        await send_ws_message_for_session("session_established", {"session_id": session_id})
        logger.info(f"[{session_id}] Sent 'session_established' message to client with full ID.")
    except Exception as e:
        logger.error(f"[{session_id}] Failed to send 'session_established' message: {e}", exc_info=True)

    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"): 
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{session_id[:8]}]"
        
        type_indicator_for_log_entry = f"[{log_type.upper().replace('MONITOR_', '').replace('ERROR_', 'ERR_').replace('SYSTEM_', 'SYS_')}]"
        if log_type == "monitor_log" and not text.startswith("["): 
            type_indicator_for_log_entry = "[INFO]"

        full_content_for_ui = f"{log_prefix} {type_indicator_for_log_entry} {text}"
        await send_ws_message_for_session("monitor_log", full_content_for_ui)
        
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
            "selected_llm_provider": settings.executor_default_provider, 
            "selected_llm_model_name": settings.executor_default_model_name, 
            "cancellation_requested": False,
            "current_plan_structured": None,
            "current_plan_human_summary": None,
            "current_plan_step_index": -1,
            "plan_execution_active": False,
            "original_user_query": None,
            "active_plan_filename": None,
            "current_plan_proposal_id_backend": None,
            "session_intent_classifier_llm_id": None, 
            "session_planner_llm_id": None,
            "session_controller_llm_id": None,
            "session_evaluator_llm_id": None,
        }
        logger.info(f"[{session_id}] Session setup complete.")
        session_setup_ok = True
    except Exception as e:
        logger.error(f"[{session_id}] CRITICAL ERROR during session setup: {e}", exc_info=True)
        if websocket: 
            try: await websocket.close(code=1011, reason="Session setup failed")
            except Exception as close_e: logger.error(f"[{session_id}] Error closing websocket during setup failure: {close_e}")
        if session_id in connected_clients: del connected_clients[session_id]
        if session_id in session_data: del session_data[session_id]
        return
    if not session_setup_ok:
        logger.error(f"[{session_id}] Halting handler because session setup failed.")
        return

    MessageHandler = Callable[..., Coroutine[Any, Any, None]] 
    
    message_handler_map: Dict[str, MessageHandler] = {
        "context_switch": process_context_switch,      
        "user_message": process_user_message,          
        "execute_confirmed_plan": process_execute_confirmed_plan, 
        "cancel_plan_proposal": process_cancel_plan_proposal, 
        "new_task": process_new_task,                  
        "delete_task": process_delete_task,            
        "rename_task": process_rename_task,            
        "set_llm": process_set_llm,                    
        "get_available_models": process_get_available_models, 
        "cancel_agent": process_cancel_agent,          
        "get_artifacts_for_task": process_get_artifacts_for_task, 
        "run_command": process_run_command,            
        "action_command": process_action_command,      
        "set_session_role_llm": process_set_session_role_llm, 
    }

    try:
        status_llm_info = f"Executor LLM: {settings.executor_default_provider} ({settings.executor_default_model_name})"
        logger.info(f"[{session_id}] Sending initial status message..."); await send_ws_message_for_session("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready. {status_llm_info}.")
        
        role_llm_defaults = {
            "intent_classifier": f"{settings.intent_classifier_provider}::{settings.intent_classifier_model_name}",
            "planner": f"{settings.planner_provider}::{settings.planner_model_name}",
            "controller": f"{settings.controller_provider}::{settings.controller_model_name}",
            "evaluator": f"{settings.evaluator_provider}::{settings.evaluator_model_name}",
        }
        await send_ws_message_for_session("available_models", {
           "gemini": settings.gemini_available_models,
           "ollama": settings.ollama_available_models,
           "default_executor_llm_id": f"{settings.executor_default_provider}::{settings.executor_default_model_name}", 
           "role_llm_defaults": role_llm_defaults
        })
        logger.info(f"[{session_id}] Sent available_models (with role defaults) to client.")
        await add_monitor_log_and_save(f"New client connection: {websocket.remote_address}", "system_connect")
        logger.info(f"[{session_id}] Added system_connect log.")


        logger.info(f"[{session_id}] Entering message processing loop...")
        async for message_str in websocket:
            logger.debug(f"[{session_id}] Received raw message: {message_str[:200]}{'...' if len(message_str)>200 else ''}")
            try:
                parsed_data = json.loads(message_str) 
                message_type = parsed_data.get("type")
                
                handler_func = message_handler_map.get(message_type)
                if handler_func:
                    session_data_entry = session_data.get(session_id)
                    connected_clients_entry = connected_clients.get(session_id)

                    if not session_data_entry or not connected_clients_entry:
                        logger.error(f"[{session_id}] Critical: session_data or connected_clients entry missing for active session. Type: {message_type}")
                        await send_ws_message_for_session("status_message", "Error: Session integrity issue. Please refresh.")
                        continue

                    handler_args: Dict[str, Any] = { 
                        "session_id": session_id, "data": parsed_data, 
                        "session_data_entry": session_data_entry, "connected_clients_entry": connected_clients_entry,
                        "send_ws_message_func": send_ws_message_for_session, 
                        "add_monitor_log_func": add_monitor_log_and_save,
                    }
                    
                    if message_type in ["context_switch", "user_message", "run_command", "execute_confirmed_plan"]: 
                        handler_args["db_add_message_func"] = add_message
                    if message_type == "context_switch": 
                        handler_args["db_add_task_func"] = add_task
                        handler_args["db_get_messages_func"] = get_messages_for_task
                        handler_args["get_artifacts_func"] = get_artifacts
                    elif message_type == "new_task" or message_type == "delete_task" or message_type == "get_artifacts_for_task": 
                        handler_args["get_artifacts_func"] = get_artifacts
                    if message_type == "delete_task": 
                        handler_args["db_delete_task_func"] = delete_task_and_messages
                    elif message_type == "rename_task": 
                        handler_args["db_rename_task_func"] = rename_task_in_db
                    elif message_type == "run_command": 
                        handler_args["execute_shell_command_func"] = execute_shell_command
                    
                    await handler_func(**handler_args) 
                
                else: 
                    logger.warning(f"[{session_id}] Unknown message type received: {message_type}")
                    await add_monitor_log_and_save(f"Received unknown message type: {message_type}", "error_unknown_msg")

            except json.JSONDecodeError: 
                logger.error(f"[{session_id}] Received non-JSON message: {message_str[:200]}{'...' if len(message_str)>200 else ''}")
                await add_monitor_log_and_save("Error: Received invalid message format (not JSON).", "error_json")
            except asyncio.CancelledError: 
                logger.info(f"[{session_id}] Message processing loop cancelled."); raise
            except Exception as e:
                logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                try: 
                    await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing")
                    await send_ws_message_for_session("status_message", f"Error processing message: {type(e).__name__}")
                except Exception as inner_e: 
                    logger.error(f"[{session_id}] Further error during error reporting: {inner_e}")

    except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError) as ws_close_exc:
        if isinstance(ws_close_exc, websockets.exceptions.ConnectionClosedOK): 
            logger.info(f"Client disconnected normally: {websocket.remote_address} (Session: {session_id}) - Code: {ws_close_exc.code}, Reason: {ws_close_exc.reason}")
        else: 
            logger.warning(f"Connection closed abnormally: {websocket.remote_address} (Session: {session_id}) - Code: {ws_close_exc.code}, Reason: {ws_close_exc.reason}")
    except asyncio.CancelledError:
        logger.info(f"WebSocket handler for session {session_id} cancelled.")
        if websocket and websocket.open: 
             await websocket.close(code=1012, reason="Server shutting down")
    except Exception as e:
        logger.error(f"Unhandled error in WebSocket handler: {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
        try:
            if websocket and websocket.open: 
                await websocket.close(code=1011, reason="Internal server error")
        except Exception as close_e: 
            logger.error(f"[{session_id}] Error closing websocket after unhandled handler error: {close_e}")
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
    await init_db()
    file_server_site, file_server_runner = await setup_file_server()
    await file_server_site.start()
    logger.info("File server started.")

    ws_host = "0.0.0.0"; ws_port = 8765
    logger.info(f"Starting WebSocket server on ws://{ws_host}:{ws_port}")
    shutdown_event = asyncio.Event()
    
    stop_serving = asyncio.Future() 

    async def serve_websockets():
        async with websockets.serve(
            handler, 
            ws_host, 
            ws_port, 
            max_size=settings.websocket_max_size_bytes, 
            ping_interval=settings.websocket_ping_interval, 
            ping_timeout=settings.websocket_ping_timeout
        ) as server:
            logger.info("WebSocket server started and serving.")
            await stop_serving 
            logger.info("WebSocket server received stop signal, closing.")
        logger.info("WebSocket server fully stopped.")

    server_task = asyncio.create_task(serve_websockets())
    
    loop = asyncio.get_running_loop()
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    original_sigterm_handler = signal.getsignal(signal.SIGTERM)

    def signal_handler_wrapper(sig, frame):
        logger.info(f"Received signal {sig}. Initiating shutdown...")
        if not stop_serving.done():
            stop_serving.set_result(None) 
        
        signal.signal(signal.SIGINT, original_sigint_handler)
        signal.signal(signal.SIGTERM, original_sigterm_handler)
        

    try: 
        loop.add_signal_handler(signal.SIGINT, functools.partial(signal_handler_wrapper, signal.SIGINT, None))
        loop.add_signal_handler(signal.SIGTERM, functools.partial(signal_handler_wrapper, signal.SIGTERM, None))
    except NotImplementedError: 
        logger.warning("Signal handlers not available on this platform (e.g., Windows without ProactorEventLoop). Use Ctrl+C if available, or send SIGTERM.")
    
    logger.info("Application servers running. Press Ctrl+C to stop (or send SIGTERM).")
    
    try:
        await server_task 
    except asyncio.CancelledError:
        logger.info("Main server task was cancelled.")
    
    logger.info("Shutdown signal processed. Stopping remaining components...")
    
    logger.info("Stopping file server..."); 
    await file_server_runner.cleanup(); 
    logger.info("File server stopped.")
    
    tasks_to_cancel = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    if tasks_to_cancel:
        logger.info(f"Cancelling {len(tasks_to_cancel)} outstanding tasks...")
        for task_to_cancel_item in tasks_to_cancel: 
            task_to_cancel_item.cancel()
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        logger.info("Outstanding tasks cancelled.")
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith API key.*")
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmithMissingAPIKeyWarning.*")
    try: 
        asyncio.run(main())
    except KeyboardInterrupt: 
        logger.info("Server stopped manually (KeyboardInterrupt).")
    except Exception as e: 
        logging.critical(f"Server failed to start or crashed: {e}", exc_info=True); exit(1)

