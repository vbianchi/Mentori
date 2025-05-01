# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex
import uuid
# Use Any for type hint robustness
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
# Check LangChain migration guide for ConversationBufferWindowMemory
from langchain.memory import ConversationBufferWindowMemory # Keep for now, verify in LangChain docs
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
# ----------------------

# Configure logging based on settings
log_level = settings.log_level
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n' # Added newline
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to {log_level}")

# --- Initialize Base LLM using Default from Settings ---
try:
    default_llm_instance = get_llm(settings, provider=settings.default_provider, model_name=settings.default_model_name)
    logger.info(f"Default Base LLM initialized successfully: {settings.default_llm_id}")
except Exception as llm_e:
    logging.critical(f"FATAL: Failed during startup LLM initialization: {llm_e}", exc_info=True)
    exit(1)


# --- Global state ---
connected_clients: Dict[str, Dict[str, Any]] = {}
session_data: Dict[str, Dict[str, Any]] = {} # Added 'cancellation_requested' flag here

# --- File Server Constants ---
FILE_SERVER_LISTEN_HOST = "0.0.0.0"
FILE_SERVER_CLIENT_HOST = settings.file_server_hostname
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
    # await send_ws_message_func("status_message", f"Running direct command: {command[:60]}...") # Removed chat status
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
    # elif success: await send_ws_message_func("status_message", f"Direct command finished successfully.") # Removed chat status
    return success

# --- File Server Handler ---
async def handle_workspace_file(request: web.Request) -> web.Response:
    """Handles requests for files within a specific task's workspace."""
    task_id = request.match_info.get('task_id')
    filename = request.match_info.get('filename')
    session_id = request.headers.get("X-Session-ID", "unknown") # Get session ID if available
    if not task_id or not filename:
        logger.warning(f"[{session_id}] File server request missing task_id or filename.")
        raise web.HTTPBadRequest(text="Task ID and filename required")
    # Basic validation for task_id format
    if not re.match(r"^[a-zA-Z0-9_.-]+$", task_id):
        logger.error(f"[{session_id}] Invalid task_id format rejected: {task_id}")
        raise web.HTTPForbidden(text="Invalid task ID format.")
    # Basic validation for filename (prevent path traversal)
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        logger.error(f"[{session_id}] Invalid filename path components detected: {filename}")
        raise web.HTTPForbidden(text="Invalid filename path components.")
    try:
        task_workspace = get_task_workspace_path(task_id)
        # Sanitize filename again just in case
        safe_filename = Path(filename).name # Get only the final component
        file_path = (task_workspace / safe_filename).resolve()
        # Ensure the final path is still within the intended workspace
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
    # Use FileResponse for efficient sending
    return FileResponse(path=file_path)


# --- File Upload Handler ---
def sanitize_filename(filename: str) -> str:
    """Removes potentially dangerous characters and path components."""
    if not filename:
        return f"uploaded_file_{uuid.uuid4().hex[:8]}"
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    # Keep only alphanumeric, underscore, hyphen, dot, space
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Basic check for empty filename after sanitization
    if not filename:
        filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    # Ensure it's just a filename, not a path (remove leading/trailing dots/underscores/hyphens)
    filename = filename.strip('._-')
    if not filename:
        filename = f"uploaded_file_{uuid.uuid4().hex[:8]}"
    return Path(filename).name # Use Path().name for final safety

async def handle_file_upload(request: web.Request) -> web.Response:
    """Handles file uploads to a specific task's workspace."""
    task_id = request.match_info.get('task_id')
    session_id = request.headers.get("X-Session-ID", "unknown") # Get session ID if available
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

    reader = None
    saved_files = []
    errors = []
    try:
        reader = await request.multipart()
    except Exception as e:
        logger.error(f"[{session_id}] Error reading multipart form data for task {task_id}: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'message': f'Failed to read upload data: {e}'}, status=400)

    if not reader:
         return web.json_response({'status': 'error', 'message': 'No multipart data received'}, status=400)

    # Process each part of the multipart request
    while True:
        part = await reader.next()
        if part is None:
            logger.debug(f"[{session_id}] Finished processing multipart parts for task {task_id}.")
            break

        if part.name == 'file' and part.filename:
            original_filename = part.filename
            safe_filename = sanitize_filename(original_filename)
            save_path = (task_workspace / safe_filename).resolve()
            logger.info(f"[{session_id}] Processing uploaded file: '{original_filename}' -> '{safe_filename}' for task {task_id}")

            # Security Check: Ensure save path is within the workspace
            if not save_path.is_relative_to(task_workspace.resolve()):
                logger.error(f"[{session_id}] Security Error: Upload path resolves outside task workspace! Task: {task_id}, Orig: '{original_filename}', Safe: '{safe_filename}', Resolved: {save_path}")
                errors.append({'filename': original_filename, 'message': 'Invalid file path detected'})
                continue # Skip this file

            try:
                # Ensure parent directories exist (though workspace should exist)
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # Stream file content asynchronously
                logger.debug(f"[{session_id}] Attempting to open {save_path} for writing.")
                async with aiofiles.open(save_path, 'wb') as f:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        await f.write(chunk)
                logger.info(f"[{session_id}] Successfully saved uploaded file to: {save_path}")
                saved_files.append({'filename': safe_filename})

                # --- Notify frontend via WebSocket ---
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
                        # Save artifact info to DB
                        await add_message(task_id, target_session_id, "artifact_generated", safe_filename)
                        logger.info(f"[{session_id}] Saved 'artifact_generated' message to DB for {safe_filename}.")

                        # Removed the failing add_monitor_log_and_save call here

                        # Send trigger message to the specific session
                        if target_session_id in connected_clients:
                             client_info = connected_clients[target_session_id]
                             send_func = client_info.get("send_ws_message")
                             if send_func:
                                 logger.info(f"[{target_session_id}] Sending trigger_artifact_refresh for task {task_id}")
                                 # Use the stored send function for this session
                                 await send_func("trigger_artifact_refresh", {"taskId": task_id})
                             else:
                                 logger.warning(f"[{session_id}] Send function not found for target session {target_session_id} to send refresh trigger.")
                        else:
                            logger.warning(f"[{session_id}] Target session {target_session_id} not found in connected_clients.")

                    except Exception as db_log_err:
                         logger.error(f"[{session_id}] Error during DB logging or WS notification after file upload for {safe_filename}: {db_log_err}", exc_info=True)
                         # Continue processing other files, but note the error

                else:
                    logger.warning(f"[{session_id}] Could not find active session for task {task_id} to notify about upload.")


            except Exception as e:
                logger.error(f"[{session_id}] Error saving uploaded file '{safe_filename}' for task {task_id}: {e}", exc_info=True)
                errors.append({'filename': original_filename, 'message': f'Server error saving file: {type(e).__name__}'})
        else:
            logger.warning(f"[{session_id}] Received non-file part or part without filename in upload: Name='{part.name}', Filename='{part.filename}'")

    logger.debug(f"[{session_id}] Finished processing all parts. Errors: {len(errors)}, Saved: {len(saved_files)}")
    try:
        if errors:
            response_data = {'status': 'error', 'message': 'Some files failed to upload.', 'errors': errors, 'saved': saved_files}
            status_code = 400 if not saved_files else 207 # 207 Multi-Status if partial success
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
        # Fallback response if JSON construction fails
        return web.Response(status=500, text="Internal server error creating upload response.")
# --- END File Upload Handler ---


# --- Get Artifacts Helper ---
async def get_artifacts(task_id: str) -> List[Dict[str, str]]:
    """Scans the task workspace and returns a list of viewable artifacts."""
    logger.debug(f"Scanning workspace for artifacts for task: {task_id}")
    artifacts = []
    try:
        task_workspace_path = get_task_workspace_path(task_id)
        artifact_patterns = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg'] + [f'*{ext}' for ext in TEXT_EXTENSIONS]
        all_potential_artifacts = []
        for pattern in artifact_patterns:
            for file_path in task_workspace_path.glob(pattern):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        all_potential_artifacts.append((file_path, mtime))
                    except FileNotFoundError:
                        continue # File might have been deleted between glob and stat

        # Sort by modification time, newest first
        sorted_files = sorted(all_potential_artifacts, key=lambda x: x[1], reverse=True)

        for file_path, _ in sorted_files:
            relative_filename = str(file_path.relative_to(task_workspace_path))
            artifact_type = 'unknown'
            file_suffix = file_path.suffix.lower()
            if file_suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']: artifact_type = 'image'
            elif file_suffix in TEXT_EXTENSIONS: artifact_type = 'text'
            elif file_suffix == '.pdf': artifact_type = 'pdf' # Handle PDF if needed

            if artifact_type != 'unknown':
                artifact_url = f"http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}/workspace_files/{task_id}/{relative_filename}"
                artifacts.append({"type": artifact_type, "url": artifact_url, "filename": relative_filename})

        logger.info(f"Found {len(artifacts)} artifacts for task {task_id}.")
    except Exception as e:
        logger.error(f"Error scanning artifacts for task {task_id}: {e}", exc_info=True)
    return artifacts
# --- END Get Artifacts Helper ---


# --- Setup File Server ---
async def setup_file_server():
    """Sets up and returns the aiohttp file server runner with CORS."""
    app = web.Application()
    # Allow larger request bodies for file uploads (e.g., 100MB)
    app['client_max_size'] = 100 * 1024**2 # Default is 2MB

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions( allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods=["GET", "POST", "OPTIONS"]) # Added POST & OPTIONS
    })

    # Add route for serving files
    get_resource = app.router.add_resource('/workspace_files/{task_id}/{filename:.+}')
    get_route = get_resource.add_route('GET', handle_workspace_file)
    cors.add(get_route)

    # Add route for uploading files
    post_resource = app.router.add_resource('/upload/{task_id}')
    post_route = post_resource.add_route('POST', handle_file_upload)
    # Ensure CORS applies to the upload route as well
    cors.add(post_route) # Use default CORS settings which now include POST

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, FILE_SERVER_LISTEN_HOST, FILE_SERVER_PORT)
    logger.info(f"Starting file server listening on http://{FILE_SERVER_LISTEN_HOST}:{FILE_SERVER_PORT}")
    return site, runner

# --- WebSocket Handler ---
# Use standard type hint as specific imports can be fragile across versions
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
# WebSocketProtocolType = Any # Use simple Any type hint to avoid deprecation warnings


async def handler(websocket: Any): # Use Any type hint
    """Handles incoming WebSocket connections and messages for a user session."""
    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id}] Connection attempt from {websocket.remote_address}...")

    # --- Nested Helper Function to Send WS Messages ---
    async def send_ws_message_for_session(msg_type: str, content: Any):
        """Safely sends a JSON message over the WebSocket for THIS session."""
        logger.debug(f"[{session_id}] Attempting to send WS message: Type='{msg_type}', Content='{str(content)[:100]}...'")
        # Check if the specific websocket connection still exists
        client_info = connected_clients.get(session_id)
        if client_info:
            ws = client_info.get("websocket")
            # *** MODIFIED: Remove ws.closed check ***
            if ws:
                try:
                    await ws.send(json.dumps({"type": msg_type, "content": content}))
                    logger.debug(f"[{session_id}] Successfully sent WS message type '{msg_type}'.")
                except (ConnectionClosedOK, ConnectionClosedError) as close_exc:
                    logger.warning(f"[{session_id}] WS already closed when trying to send type '{msg_type}'. Error: {close_exc}")
                except Exception as e:
                    logger.error(f"[{session_id}] Error sending WS message type '{msg_type}': {e}", exc_info=True)
            else:
                 logger.warning(f"[{session_id}] Websocket object not found for session when trying to send type '{msg_type}'.")
        else:
            logger.warning(f"[{session_id}] Session not found in connected_clients when trying to send type '{msg_type}'.")

    connected_clients[session_id] = {"websocket": websocket, "agent_task": None, "send_ws_message": send_ws_message_for_session}
    logger.info(f"[{session_id}] Client added to connected_clients dict with send function.")


    # --- Nested Helper Function to Add Monitor Log and Save to DB ---
    # This function now uses the send_ws_message_for_session defined above
    async def add_monitor_log_and_save(text: str, log_type: str = "monitor_log"):
        """Adds a log entry to the monitor panel and saves it to the database."""
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{session_id[:8]}]"
        full_content = f"{log_prefix} {text}"
        await send_ws_message_for_session("monitor_log", full_content) # Use session-specific sender
        active_task_id = session_data.get(session_id, {}).get("current_task_id")
        if active_task_id:
            try:
                # Save with the specific log_type passed in
                await add_message(active_task_id, session_id, log_type, text)
            except Exception as db_err:
                logger.error(f"[{session_id}] Failed to save monitor log '{log_type}' to DB: {db_err}")

    # --- Session Setup (Memory, Callback Handler) ---
    ws_callback_handler: Optional[WebSocketCallbackHandler] = None
    memory: Optional[ConversationBufferWindowMemory] = None
    session_setup_ok = False
    try:
        logger.info(f"[{session_id}] Starting session setup...")
        logger.debug(f"[{session_id}] Creating ConversationBufferWindowMemory (K={settings.agent_memory_window_k})...")
        # *** TODO (2c): Verify ConversationBufferWindowMemory usage with LangChain docs ***
        memory = ConversationBufferWindowMemory(
            k=settings.agent_memory_window_k, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
        )
        logger.debug(f"[{session_id}] Memory object created.")
        logger.debug(f"[{session_id}] Creating WebSocketCallbackHandler...")
        db_add_func = functools.partial(add_message)
        # Pass the session-specific sender function to the callback handler
        ws_callback_handler = WebSocketCallbackHandler(session_id, send_ws_message_for_session, db_add_func, session_data)
        logger.debug(f"[{session_id}] Callback handler created.")
        logger.debug(f"[{session_id}] Storing session data...")
        session_data[session_id] = {
            "memory": memory,
            "callback_handler": ws_callback_handler,
            "current_task_id": None,
            "selected_llm_provider": settings.default_provider,
            "selected_llm_model_name": settings.default_model_name,
            "cancellation_requested": False # Initialize cancellation flag
        }
        logger.info(f"[{session_id}] Session setup complete.")
        session_setup_ok = True
    except Exception as e:
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

    # --- Main Message Processing Loop ---
    try:
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
        async for message in websocket:
            logger.debug(f"[{session_id}] Received raw message: {message[:200]}{'...' if len(message)>200 else ''}")
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")
                task_id_from_frontend = data.get("taskId")
                task_title_from_frontend = data.get("task")

                current_task_id = session_data.get(session_id, {}).get("current_task_id")
                logger.debug(f"[{session_id}] Processing message type: {message_type}, Task Context: {current_task_id}")

                # --- CONTEXT SWITCH ---
                if message_type == "context_switch" and task_id_from_frontend:
                    logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")
                    if session_id in session_data:
                        # Reset cancellation flag on context switch
                        session_data[session_id]['cancellation_requested'] = False
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                            logger.warning(f"[{session_id}] Cancelling active agent task due to context switch.")
                            existing_agent_task.cancel()
                            await send_ws_message_for_session("status_message", "Operation cancelled due to task switch.")
                            await add_monitor_log_and_save("Agent operation cancelled due to context switch.", "system_cancel")
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
                        # await send_ws_message_for_session("status_message", "Loading history...") # Removed chat status
                        history_messages = await get_messages_for_task(task_id_from_frontend)
                        artifacts_from_history = []
                        chat_history_for_memory = []
                        if history_messages:
                            logger.info(f"[{session_id}] Loading {len(history_messages)} history messages for task {task_id_from_frontend}.")
                            await send_ws_message_for_session("history_start", f"Loading {len(history_messages)} messages...")
                            for i, msg in enumerate(history_messages):
                                db_msg_type = msg.get('message_type', 'unknown')
                                db_content = msg.get('content', '')
                                db_timestamp = msg.get('timestamp', datetime.datetime.now().isoformat())
                                ui_msg_type = None
                                content_to_send = db_content
                                send_to_chat = False # Default to NOT sending to chat

                                # Determine the UI message type and if it should go to chat
                                if db_msg_type == "user_input":
                                    ui_msg_type = "user"
                                    send_to_chat = True # Send actual user input to chat
                                    chat_history_for_memory.append(HumanMessage(content=db_content))
                                elif db_msg_type in ["agent_finish", "agent_message", "agent"]:
                                    ui_msg_type = "agent_message"
                                    send_to_chat = True # Send agent messages to chat
                                    chat_history_for_memory.append(AIMessage(content=db_content))
                                elif db_msg_type == "artifact_generated":
                                    # Process artifact but don't send to chat or monitor directly here
                                    # (Monitor log is handled separately, artifact list is sent at end)
                                    filename = db_content
                                    try:
                                        task_ws_path = get_task_workspace_path(task_id_from_frontend)
                                        file_path = (task_ws_path / filename).resolve()
                                        if not file_path.is_relative_to(task_ws_path.resolve()): logger.warning(f"[{session_id}] History artifact path outside workspace: {file_path}"); continue
                                        artifact_type = 'unknown'
                                        file_suffix = file_path.suffix.lower()
                                        if file_suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']: artifact_type = 'image'
                                        elif file_suffix in TEXT_EXTENSIONS: artifact_type = 'text'
                                        if artifact_type != 'unknown' and file_path.exists():
                                            relative_filename = str(file_path.relative_to(task_ws_path))
                                            artifact_url = f"http://{FILE_SERVER_CLIENT_HOST}:{FILE_SERVER_PORT}/workspace_files/{task_id_from_frontend}/{relative_filename}"
                                            artifacts_from_history.append({"type": artifact_type, "url": artifact_url, "filename": relative_filename})
                                            # Log artifact generation to monitor
                                            log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; await send_ws_message_for_session("monitor_log", f"{log_prefix} [History][ARTIFACT] {relative_filename} (Type: {artifact_type})")
                                        else:
                                            logger.warning(f"[{session_id}] Artifact file from history not found or unknown type: {file_path}")
                                            log_prefix = f"[{db_timestamp}][{session_id[:8]}]"; await send_ws_message_for_session("monitor_log", f"{log_prefix} [History][ARTIFACT_MISSING] {filename}")
                                    except Exception as artifact_err:
                                        logger.error(f"[{session_id}] Error processing artifact from history {filename}: {artifact_err}")
                                elif db_msg_type.startswith(("monitor_", "error_", "system_", "tool_", "agent_thought_", "monitor_user_input")):
                                    ui_msg_type = "monitor_log" # All these go ONLY to monitor
                                    log_prefix = f"[{db_timestamp}][{session_id[:8]}]"
                                    # Create a more readable type indicator for the monitor log
                                    type_indicator = f"[{db_msg_type.replace('monitor_', '').replace('error_', 'ERR_').replace('system_', 'SYS_').replace('agent_thought_action', 'THOUGHT_ACT').replace('agent_thought_final', 'THOUGHT_FIN').replace('monitor_user_input', 'USER_INPUT_LOG').upper()}]"
                                    content_to_send = f"{log_prefix} [History]{type_indicator} {db_content}"
                                    send_to_chat = False # Ensure these never go to chat
                                else:
                                    # Handle truly unknown types
                                    send_to_chat = False
                                    logger.warning(f"[{session_id}] Unknown history message type '{db_msg_type}' encountered.")
                                    await send_ws_message_for_session("monitor_log", f"[{db_timestamp}][{session_id[:8]}] [History][UNKNOWN_TYPE: {db_msg_type}] {db_content}")

                                # Send message to UI if applicable
                                if ui_msg_type:
                                    if send_to_chat:
                                        await send_ws_message_for_session(ui_msg_type, content_to_send)
                                    elif ui_msg_type == "monitor_log": # Send monitor logs only via monitor_log type
                                        await send_ws_message_for_session("monitor_log", content_to_send)
                                    await asyncio.sleep(0.005) # Slight delay for smoother loading

                            await send_ws_message_for_session("history_end", "History loaded.")
                            logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")
                            MAX_MEMORY_RELOAD = settings.agent_memory_window_k
                            if "memory" in session_data[session_id]:
                                try: session_data[session_id]["memory"].chat_memory.messages = chat_history_for_memory[-MAX_MEMORY_RELOAD:]; logger.info(f"[{session_id}] Repopulated agent memory with last {len(session_data[session_id]['memory'].chat_memory.messages)} messages.")
                                except Exception as mem_load_e: logger.error(f"[{session_id}] Failed to repopulate memory from history: {mem_load_e}")
                            if artifacts_from_history: logger.info(f"[{session_id}] Sending {len(artifacts_from_history)} artifacts from history."); await send_ws_message_for_session("update_artifacts", artifacts_from_history)
                            else: await send_ws_message_for_session("update_artifacts", [])
                        else: await send_ws_message_for_session("history_end", "No history found."); await send_ws_message_for_session("update_artifacts", []); logger.info(f"[{session_id}] No history found for task {task_id_from_frontend}.")
                        # await send_ws_message_for_session("status_message", "History loaded. Ready.") # Removed chat status
                    else: logger.error(f"[{session_id}] Context switch received but no session data found!"); await send_ws_message_for_session("status_message", "Error: Session data lost. Please refresh.")

                # --- NEW TASK ---
                elif message_type == "new_task":
                    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context.")
                    current_task_id = None
                    if session_id in session_data:
                        # Reset cancellation flag on new task
                        session_data[session_id]['cancellation_requested'] = False
                        existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                        if existing_agent_task and not existing_agent_task.done():
                                logger.warning(f"[{session_id}] Cancelling active agent task due to new task.")
                                existing_agent_task.cancel()
                                await send_ws_message_for_session("status_message", "Operation cancelled for new task.")
                                await add_monitor_log_and_save("Agent operation cancelled due to new task creation.", "system_cancel")
                                connected_clients[session_id]["agent_task"] = None
                        session_data[session_id]["current_task_id"] = None
                        session_data[session_id]["callback_handler"].set_task_id(None)
                        if "memory" in session_data[session_id]: session_data[session_id]["memory"].clear()
                        await add_monitor_log_and_save("Cleared context for new task.", "system_new_task")
                        await send_ws_message_for_session("update_artifacts", [])
                    else: logger.error(f"[{session_id}] 'new_task' signal received but no session data found!")

                # --- USER MESSAGE ---
                elif message_type == "user_message":
                    active_task_id = session_data.get(session_id, {}).get("current_task_id")
                    if not active_task_id:
                        logger.warning(f"[{session_id}] User message received but no task active.")
                        await send_ws_message_for_session("status_message", "Please select or create a task first.")
                        continue
                    if connected_clients.get(session_id, {}).get("agent_task") and not connected_clients[session_id]["agent_task"].done():
                        logger.warning(f"[{session_id}] User message received while agent is already running for task {active_task_id}.")
                        await send_ws_message_for_session("status_message", "Agent is busy. Please wait or stop the current process.")
                        continue

                    user_input_content = ""
                    if isinstance(content, str): user_input_content = content
                    else: logger.warning(f"[{session_id}] Received non-string content for user_message: {type(content)}. Ignoring."); continue

                    # Save the actual user input to DB
                    await add_message(active_task_id, session_id, "user_input", user_input_content)
                    # Save monitor log with distinct type
                    await add_monitor_log_and_save(f"User Input: {user_input_content}", "monitor_user_input")

                    if session_id not in session_data: logger.error(f"[{session_id}] User message for task {active_task_id} but no session data found!"); continue

                    # Reset cancellation flag before starting a new agent run
                    session_data[session_id]['cancellation_requested'] = False

                    # --- Prepare for Agent Execution ---
                    session_memory = session_data[session_id]["memory"]
                    session_callback_handler = session_data[session_id]["callback_handler"]
                    request_agent_executor: Optional[AgentExecutor] = None
                    request_llm: Optional[BaseLanguageModel] = None

                    try:
                        selected_provider = session_data[session_id].get("selected_llm_provider", settings.default_provider)
                        selected_model_name = session_data[session_id].get("selected_llm_model_name", settings.default_model_name)
                        logger.info(f"[{session_id}] Using LLM for this request: {selected_provider}::{selected_model_name}")
                        try:
                            request_llm = get_llm(settings, provider=selected_provider, model_name=selected_model_name)
                        except Exception as llm_init_err:
                            logger.error(f"[{session_id}] Failed to initialize selected LLM ({selected_provider}::{selected_model_name}): {llm_init_err}", exc_info=True)
                            await add_monitor_log_and_save(f"Error initializing selected LLM: {llm_init_err}", "error_system")
                            await send_ws_message_for_session("status_message", "Error: Failed to use selected LLM. Check configuration.")
                            await send_ws_message_for_session("agent_message", f"Sorry, could not use the selected LLM ({selected_model_name}). Please check the backend configuration or select another model.")
                            continue

                        dynamic_agent_tools = get_dynamic_tools(active_task_id)

                        request_agent_executor = create_agent_executor(
                            llm=request_llm, tools=dynamic_agent_tools, memory=session_memory, max_iterations=settings.agent_max_iterations
                        )
                        logger.info(f"[{session_id}] Created request-specific AgentExecutor for task {active_task_id}")
                    except Exception as agent_create_e:
                        logger.error(f"[{session_id}] Failed to create agent executor for task {active_task_id}: {agent_create_e}", exc_info=True)
                        await add_monitor_log_and_save(f"Error creating agent: {agent_create_e}", "error_system")
                        await send_ws_message_for_session("status_message", "Error: Failed to set up agent.")
                        await send_ws_message_for_session("agent_message", f"Sorry, an internal error occurred while setting up the agent: {type(agent_create_e).__name__}")
                        continue

                    # --- Artifact Scan (PRE-RUN) ---
                    task_workspace_path: Optional[Path] = None
                    files_before_run: Set[Path] = set()
                    artifact_patterns = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg'] + [f'*{ext}' for ext in TEXT_EXTENSIONS]
                    try:
                        task_workspace_path = get_task_workspace_path(active_task_id)
                        for pattern in artifact_patterns: files_before_run.update(f.relative_to(task_workspace_path) for f in task_workspace_path.glob(pattern) if f.is_file())
                        logger.debug(f"Files before agent run: {files_before_run}")
                    except Exception as file_scan_e: logger.error(f"[{session_id}] Error scanning workspace before agent run: {file_scan_e}"); files_before_run = set(); task_workspace_path = None

                    # --- Execute Agent ---
                    agent_task: Optional[asyncio.Task] = None
                    try:
                        config = RunnableConfig(callbacks=[session_callback_handler])
                        agent_coro = request_agent_executor.ainvoke({"input": user_input_content}, config=config)
                        agent_task = asyncio.create_task(agent_coro, name=f"agent_task_{session_id}_{active_task_id}") # Give task a name

                        # Store the reference
                        if session_id in connected_clients:
                            connected_clients[session_id]["agent_task"] = agent_task
                            logger.info(f"[{session_id}] Stored agent_task reference for task {active_task_id}. Ref: {agent_task}")
                        else:
                            logger.error(f"[{session_id}] CRITICAL: Cannot store agent_task reference, session_id not in connected_clients!")

                        result = await agent_task
                        logger.info(f"[{session_id}] Agent execution completed successfully for task {active_task_id}.")

                        # --- Artifact Scan (POST-RUN) & Update ---
                        if task_workspace_path:
                            try:
                                current_artifacts_in_ws = await get_artifacts(active_task_id) # Use helper
                                if current_artifacts_in_ws:
                                    logger.info(f"[{session_id}] Sending final update_artifacts message with {len(current_artifacts_in_ws)} artifacts.")
                                    await send_ws_message_for_session("update_artifacts", current_artifacts_in_ws)
                                else:
                                    logger.info(f"[{session_id}] No artifacts found in workspace post-run, sending empty update.")
                                    await send_ws_message_for_session("update_artifacts", [])
                            except Exception as artifact_scan_e:
                                logger.error(f"[{session_id}] Error during post-run artifact scan/update: {artifact_scan_e}")
                        else:
                            logger.warning(f"[{session_id}] Skipping post-run artifact scan/update due to invalid task workspace path.")


                    except AgentCancelledException as ace:
                        logger.warning(f"[{session_id}] Caught AgentCancelledException for task {active_task_id}: {ace}")
                        try:
                            await send_ws_message_for_session("status_message", "Processing cancelled by user.") # Inform UI
                            await add_monitor_log_and_save(f"Agent task stopped by user request: {ace}", "system_cancel")
                            logger.info(f"[{session_id}] Successfully sent AgentCancelledException status messages.")
                        except Exception as cancel_log_err:
                            logger.error(f"[{session_id}] Error sending AgentCancelledException status messages: {cancel_log_err}", exc_info=True)

                    except asyncio.CancelledError:
                        logger.warning(f"[{session_id}] Caught asyncio.CancelledError for task {active_task_id}.")
                        try:
                            await send_ws_message_for_session("status_message", "Processing cancelled by user.") # Inform UI
                            await add_monitor_log_and_save("Agent task cancelled by user request (asyncio).", "system_cancel")
                            logger.info(f"[{session_id}] Successfully sent asyncio.CancelledError status messages.")
                        except Exception as cancel_log_err:
                            logger.error(f"[{session_id}] Error sending asyncio.CancelledError status messages: {cancel_log_err}", exc_info=True)

                    except Exception as e:
                        error_msg = f"CRITICAL Error during agent execution: {e}"
                        logger.error(f"[{session_id}] {error_msg}", exc_info=True)
                        await add_monitor_log_and_save(error_msg, "error_agent")
                        await send_ws_message_for_session("status_message", f"Error during task processing: {type(e).__name__}")
                        await send_ws_message_for_session("agent_message", f"Sorry, an internal error occurred: {type(e).__name__}")
                        if active_task_id: await add_message(active_task_id, session_id, "error_agent", f"{type(e).__name__}: {e}")
                    finally:
                        # Keep the existing finally logic (checking cancellation_requested flag)
                        if session_id in connected_clients:
                            agent_task_ref_before_clear = connected_clients[session_id].get("agent_task")
                            cancellation_was_requested = session_data.get(session_id, {}).get('cancellation_requested', False)

                            logger.info(f"[{session_id}] In finally block for agent execution (Task: {active_task_id}). Cancellation requested: {cancellation_was_requested}. Agent task ref before clearing: {agent_task_ref_before_clear}")

                            if not cancellation_was_requested:
                                connected_clients[session_id]["agent_task"] = None
                                logger.debug(f"[{session_id}] Cleared agent_task reference in finally block (no cancellation requested).")
                            else:
                                logger.info(f"[{session_id}] Skipping agent_task reference clear in finally block due to pending cancellation request.")
                                if session_id in session_data:
                                    session_data[session_id]['cancellation_requested'] = False # Reset flag
                        else:
                            logger.warning(f"[{session_id}] Session not found in connected_clients during finally block for agent execution.")

                # --- DELETE TASK ---
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
                        active_task_id_check = session_data.get(session_id, {}).get("current_task_id") # Re-check active task id
                        if active_task_id_check == task_id_from_frontend:
                            current_task_id = None # Update local variable
                            if session_id in session_data:
                                # Reset cancellation flag if active task is deleted
                                session_data[session_id]['cancellation_requested'] = False
                                existing_agent_task = connected_clients.get(session_id, {}).get("agent_task")
                                if existing_agent_task and not existing_agent_task.done(): existing_agent_task.cancel()
                                connected_clients[session_id]["agent_task"] = None; session_data[session_id]["current_task_id"] = None; session_data[session_id]["callback_handler"].set_task_id(None)
                                if "memory" in session_data[session_id]: session_data[session_id]["memory"].clear()
                                await add_monitor_log_and_save("Cleared context as active task was deleted.", "system_context_clear")
                                await send_ws_message_for_session("update_artifacts", [])
                    else: await send_ws_message_for_session("status_message", f"Failed to delete task {task_id_from_frontend[:8]}..."); await add_monitor_log_and_save(f"Failed to delete task {task_id_from_frontend} from DB.", "error_delete")

                # --- RENAME TASK ---
                elif message_type == "rename_task":
                    task_id_to_rename = data.get("taskId")
                    new_name = data.get("newName")
                    if not task_id_to_rename or not new_name: logger.warning(f"[{session_id}] Received invalid rename_task message: {data}"); await add_monitor_log_and_save(f"Error: Received invalid rename request (missing taskId or newName).", "error_system"); continue
                    logger.info(f"[{session_id}] Received request to rename task {task_id_to_rename} to '{new_name}'."); await add_monitor_log_and_save(f"Received rename request for task {task_id_to_rename} to '{new_name}'.", "system_rename_request")
                    renamed_in_db = await rename_task_in_db(task_id_to_rename, new_name)
                    if renamed_in_db: logger.info(f"[{session_id}] Successfully renamed task {task_id_to_rename} in database."); await add_monitor_log_and_save(f"Task {task_id_to_rename} renamed to '{new_name}' in DB.", "system_rename_success")
                    else: logger.error(f"[{session_id}] Failed to rename task {task_id_to_rename} in database."); await add_monitor_log_and_save(f"Failed to rename task {task_id_to_rename} in DB.", "error_db")

                # --- SET LLM ---
                elif message_type == "set_llm":
                    llm_id = data.get("llm_id")
                    if llm_id and isinstance(llm_id, str):
                        try:
                            provider, model_name = llm_id.split("::", 1)
                            is_valid = False
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

                # --- GET AVAILABLE MODELS ---
                elif message_type == "get_available_models":
                     logger.info(f"[{session_id}] Received request for available models.")
                     await send_ws_message_for_session("available_models", {
                         "gemini": settings.gemini_available_models,
                         "ollama": settings.ollama_available_models,
                         "default_llm_id": settings.default_llm_id
                     })

                # *** Handle Cancel Agent Request ***
                elif message_type == "cancel_agent":
                    logger.warning(f"[{session_id}] Received request to cancel agent task.")
                    # Set the flag first
                    if session_id in session_data:
                        session_data[session_id]['cancellation_requested'] = True
                        logger.info(f"[{session_id}] Cancellation requested flag set to True.")
                    else:
                        logger.error(f"[{session_id}] Cannot set cancellation flag: Session data not found.")

                    # Now attempt to cancel the task if it exists and is running
                    session_state = connected_clients.get(session_id, {})
                    logger.info(f"[{session_id}] Checking session state in connected_clients for cancel request: {session_state}")
                    agent_task_to_cancel = session_state.get("agent_task")

                    if agent_task_to_cancel:
                        logger.info(f"[{session_id}] Found agent task to cancel: {agent_task_to_cancel.get_name()} (Done: {agent_task_to_cancel.done()})")
                        if not agent_task_to_cancel.done():
                            # Attempt cancellation via the task object (might not work if blocked)
                            agent_task_to_cancel.cancel()
                            logger.info(f"[{session_id}] asyncio.Task.cancel() called for agent task.")
                            # The actual stop should happen via AgentCancelledException raised by callbacks
                        else:
                             logger.warning(f"[{session_id}] Agent task was already done, cannot cancel.")
                             await send_ws_message_for_session("status_message", "Process already finished.")
                             # Reset flag if task was already done when cancel arrived
                             if session_id in session_data: session_data[session_id]['cancellation_requested'] = False
                    else:
                        logger.warning(f"[{session_id}] No running agent task found in connected_clients to cancel.")
                        await send_ws_message_for_session("status_message", "No active process found to cancel.")
                        # Reset flag if no task was found
                        if session_id in session_data: session_data[session_id]['cancellation_requested'] = False

                # --- Get Artifacts Request ---
                elif message_type == "get_artifacts_for_task":
                    task_id_to_refresh = data.get("taskId")
                    if not task_id_to_refresh:
                        logger.warning(f"[{session_id}] Received get_artifacts_for_task without taskId.")
                        continue
                    logger.info(f"[{session_id}] Received request to refresh artifacts for task: {task_id_to_refresh}")
                    # Ensure the request is for the session's current task for security/consistency
                    if task_id_to_refresh == current_task_id:
                        artifacts = await get_artifacts(task_id_to_refresh)
                        await send_ws_message_for_session("update_artifacts", artifacts)
                        logger.info(f"[{session_id}] Sent updated artifact list for task {task_id_to_refresh}.")
                    else:
                        logger.warning(f"[{session_id}] Received artifact refresh request for non-active task ({task_id_to_refresh} vs {current_task_id}). Ignoring.")

                # --- Other message types ---
                elif message_type == "run_command":
                    command_to_run = data.get("command")
                    if command_to_run and isinstance(command_to_run, str):
                        active_task_id_for_cmd = session_data.get(session_id, {}).get("current_task_id")
                        await add_monitor_log_and_save(f"Received direct 'run_command'. Executing: {command_to_run} (Task Context: {active_task_id_for_cmd})", "system_direct_cmd")
                        await execute_shell_command(command_to_run, session_id, send_ws_message_for_session, add_message, active_task_id_for_cmd)
                    else: logger.warning(f"[{session_id}] Received 'run_command' with invalid/missing command content."); await add_monitor_log_and_save("Error: 'run_command' received with no command specified.", "error_direct_cmd")

                elif message_type == "action_command":
                    action = data.get("command")
                    if action and isinstance(action, str):
                        logger.info(f"[{session_id}] Received action command: {action} (Not implemented).")
                        await add_monitor_log_and_save(f"Received action command: {action} (Handler not implemented).", "system_action_cmd")
                    else: logger.warning(f"[{session_id}] Received 'action_command' with invalid/missing command content.")


                # --- Unknown message type ---
                else:
                    logger.warning(f"[{session_id}] Unknown message type received: {message_type}")
                    await add_monitor_log_and_save(f"Received unknown message type: {message_type}", "error_unknown_msg")

            # --- Error Handling for Message Processing ---
            except json.JSONDecodeError: logger.error(f"[{session_id}] Received non-JSON message: {message[:200]}{'...' if len(message)>200 else ''}"); await add_monitor_log_and_save("Error: Received invalid message format (not JSON).", "error_json")
            except asyncio.CancelledError: logger.info(f"[{session_id}] Message processing loop cancelled."); raise
            except Exception as e:
                logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                try: await add_monitor_log_and_save(f"Error processing message: {e}", "error_processing"); await send_ws_message_for_session("status_message", f"Error processing message: {type(e).__name__}")
                except Exception as inner_e: logger.error(f"[{session_id}] Further error during error reporting: {inner_e}")

    # --- WebSocket Closure Handling ---
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

    # --- Session Cleanup ---
    finally:
         logger.info(f"Cleaning up resources for session {session_id}")
         agent_task = connected_clients.get(session_id, {}).get("agent_task")
         if agent_task and not agent_task.done():
             logger.warning(f"[{session_id}] Cancelling agent task during cleanup.")
             agent_task.cancel()
             try: await agent_task
             except asyncio.CancelledError: pass
             except AgentCancelledException: pass # Also catch our custom exception during cleanup
             except Exception as cancel_e: logger.error(f"[{session_id}] Error waiting for agent task cancellation during cleanup: {cancel_e}")
         if session_id in connected_clients: del connected_clients[session_id]
         if session_id in session_data: del session_data[session_id]
         logger.info(f"Cleaned up session data for {session_id}. Client removed: {websocket.remote_address}. Active clients: {len(connected_clients)}")


# --- Main Application Entry Point ---
async def main():
    """Initializes DB, starts file server and WebSocket server, handles shutdown."""
    await init_db()
    file_server_site, file_server_runner = await setup_file_server()
    await file_server_site.start()
    logger.info("File server started.")
    ws_host = "0.0.0.0"
    ws_port = 8765
    logger.info(f"Starting WebSocket server on ws://{ws_host}:{ws_port}")

    # Define shutdown_event before server start
    shutdown_event = asyncio.Event()

    # Use standard websockets.serve
    websocket_server = await websockets.serve(
        handler, ws_host, ws_port, max_size=settings.websocket_max_size_bytes,
        ping_interval=settings.websocket_ping_interval, ping_timeout=settings.websocket_ping_timeout
    )
    logger.info("WebSocket server started.")

    # --- Graceful Shutdown Handling ---
    loop = asyncio.get_running_loop()
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    original_sigterm_handler = signal.getsignal(signal.SIGTERM)
    def signal_handler(sig, frame): logger.info(f"Received signal {sig}. Initiating shutdown..."); shutdown_event.set(); signal.signal(signal.SIGINT, original_sigint_handler); signal.signal(signal.SIGTERM, original_sigterm_handler)
    try: loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT, None); loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM, None)
    except NotImplementedError: logger.warning("Signal handlers not available on this platform (Windows?). Use Ctrl+C.")
    logger.info("Application servers running. Press Ctrl+C to stop.")

    # Keep server running until shutdown signal
    await shutdown_event.wait()

    # --- Perform Cleanup ---
    logger.info("Shutdown signal received. Stopping servers...")
    logger.info("Stopping WebSocket server..."); websocket_server.close(); await websocket_server.wait_closed(); logger.info("WebSocket server stopped.")
    logger.info("Stopping file server..."); await file_server_runner.cleanup(); logger.info("File server stopped.")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks: logger.info(f"Cancelling {len(tasks)} outstanding tasks..."); [task.cancel() for task in tasks]; await asyncio.gather(*tasks, return_exceptions=True); logger.info("Outstanding tasks cancelled.")

# --- Script Execution ---
if __name__ == "__main__":
    # Suppress LangSmith warning
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith API key.*")
    warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmithMissingAPIKeyWarning.*")
    # OR configure LangSmith via environment variables:
    # os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    # os.environ["LANGCHAIN_API_KEY"] = "YOUR_API_KEY"
    # os.environ["LANGCHAIN_PROJECT"] = "YOUR_PROJECT_NAME" # Optional

    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("Server stopped manually (KeyboardInterrupt).")
    except Exception as e: logging.critical(f"Server failed to start or crashed: {e}", exc_info=True); exit(1)

