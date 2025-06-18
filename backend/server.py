# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 12.5: True Concurrency - DEFINITIVE FIX)
#
# This version implements the final, robust architecture for true concurrency
# using a simple, direct broadcast model. This resolves all previously
# identified bugs with duplicate messages and connection handling.
#
# Key Architectural Changes:
# 1. Simple, Direct Broadcast (`broadcast_event`):
#    - The complex queueing system has been removed.
#    - A single `broadcast_event` function now iterates through a simple set
#      of all `ACTIVE_CONNECTIONS` and attempts to send the event directly
#      to each one.
# 2. Resilient Sending: The send operation is wrapped in a try/except block.
#    If a client has disconnected, the `ConnectionClosed` error is caught
#    gracefully, and that client is simply ignored, preventing any crashes.
# 3. Decoupled Agent Execution: The `agent_execution_wrapper` remains fully
#    decoupled and runs as a background task. It now calls the simple
#    `broadcast_event` function to report its progress.
# 4. Correct State Management: This is the definitive, stable architecture
#    that supports concurrent runs and robustly handles client connections
#    without message duplication.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
import json
import threading
import cgi
import shutil
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import websockets
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

# --- Local Imports ---
from .langgraph_agent import agent_graph
from .tools.file_system import _resolve_path
from .tools import get_available_tools

# --- Configuration & Globals ---
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RUNNING_AGENTS = {}
ACTIVE_CONNECTIONS = set()

# --- Helper Functions (No changes) ---
def format_model_name(model_id):
    try:
        provider, name = model_id.split("::")
        name_parts = name.replace('-', ' ').split()
        formatted_name = ' '.join(part.capitalize() for part in name_parts)
        return f"{provider.capitalize()} {formatted_name}"
    except: return model_id
def _safe_delete_workspace(task_id: str):
    try:
        workspace_path = _resolve_path("/app/workspace", task_id)
        if not os.path.abspath(workspace_path).startswith(os.path.abspath("/app/workspace")): raise PermissionError("Security check failed.")
        if os.path.isdir(workspace_path):
            shutil.rmtree(workspace_path)
            logger.info(f"Task '{task_id}': Successfully deleted workspace directory.")
        else: logger.warning(f"Task '{task_id}': Workspace directory not found for deletion.")
    except Exception as e: logger.error(f"Task '{task_id}': Error deleting workspace: {e}", exc_info=True)

# --- HTTP File Server Class (No changes) ---
class WorkspaceHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '/api/models': self._handle_get_models()
        elif path == '/api/tools': self._handle_get_tools()
        elif path == '/api/workspace/items': self._handle_get_workspace_items(parsed_path)
        elif path == '/file-content': self._handle_get_file_content(parsed_path)
        elif path == '/api/workspace/raw': self._handle_get_raw_file(parsed_path)
        else: self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known API routes."})
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '/api/workspace/folders': self._handle_create_folder()
        elif path == '/upload': self._handle_file_upload()
        else: self._send_json_response(404, {'error': f"Not Found: The POST path '{path}' does not match any known API routes."})
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '/api/workspace/items': self._handle_delete_workspace_item(parsed_path)
        else: self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known DELETE routes."})
    def do_PUT(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '/api/workspace/items': self._handle_rename_workspace_item()
        else: self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known PUT routes."})
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    def _handle_get_models(self):
        logger.info("Parsing .env to serve available and default models.")
        available_models, model_ids = [], set()
        def parse_and_add_models(env_var, provider_prefix):
            models_str = os.getenv(env_var)
            if models_str:
                for model_name in models_str.split(','):
                    model_name = model_name.strip()
                    if model_name:
                        full_id = f"{provider_prefix}::{model_name}"
                        if full_id not in model_ids:
                            available_models.append({"id": full_id, "name": format_model_name(full_id)})
                            model_ids.add(full_id)
        parse_and_add_models("GEMINI_AVAILABLE_MODELS", "gemini")
        parse_and_add_models("OLLAMA_AVAILABLE_MODELS", "ollama")
        safe_fallback_model = "gemini::gemini-1.5-flash-latest"
        if not available_models: available_models.append({"id": safe_fallback_model, "name": format_model_name(safe_fallback_model)})
        global_default_llm = os.getenv("DEFAULT_LLM_ID", safe_fallback_model)
        default_models = {"ROUTER_LLM_ID": os.getenv("ROUTER_LLM_ID", global_default_llm), "CHIEF_ARCHITECT_LLM_ID": os.getenv("CHIEF_ARCHITECT_LLM_ID", global_default_llm), "SITE_FOREMAN_LLM_ID": os.getenv("SITE_FOREMAN_LLM_ID", global_default_llm), "PROJECT_SUPERVISOR_LLM_ID": os.getenv("PROJECT_SUPERVISOR_LLM_ID", global_default_llm), "EDITOR_LLM_ID": os.getenv("EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")}
        self._send_json_response(200, {"available_models": available_models, "default_models": default_models})
    def _handle_get_tools(self):
        logger.info("Serving available tools list.")
        try:
            loaded_tools = get_available_tools()
            formatted_tools = [{"name": tool.name, "description": tool.description} for tool in loaded_tools]
            editor_tool = {"name": "The Editor", "description": "Use a powerful language model to perform tasks like rewriting, summarizing, or analyzing text."}
            self._send_json_response(200, {"tools": [editor_tool] + formatted_tools})
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}", exc_info=True)
            self._send_json_response(500, {"error": "Could not retrieve tools."})
    def _handle_get_workspace_items(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        subdir = query_components.get("path", [None])[0]
        if not subdir: return self._send_json_response(400, {"error": "Missing 'path' query parameter."})
        base_workspace, items = "/app/workspace", []
        try:
            full_path = _resolve_path(base_workspace, subdir)
            if not os.path.isdir(full_path): return self._send_json_response(404, {"error": f"Directory not found: '{subdir}'"})
            for item_name in os.listdir(full_path):
                item_path = os.path.join(full_path, item_name)
                item_type = 'directory' if os.path.isdir(item_path) else 'file'
                try: item_size = os.path.getsize(item_path) if item_type == 'file' else 0
                except OSError: item_size = 0
                items.append({"name": item_name, "type": item_type, "size": item_size})
            self._send_json_response(200, {"items": items})
        except Exception as e:
            logger.error(f"Error listing workspace items for path '{subdir}': {e}", exc_info=True)
            self._send_json_response(500, {"error": str(e)})
    def _handle_delete_workspace_item(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        item_path_str = query_components.get("path", [None])[0]
        if not item_path_str: return self._send_json_response(400, {"error": "Missing 'path' query parameter."})
        base_workspace = "/app/workspace"
        try:
            full_path = _resolve_path(base_workspace, item_path_str)
            if not os.path.exists(full_path): return self._send_json_response(404, {"error": f"Item not found: '{item_path_str}'"})
            if os.path.isdir(full_path): shutil.rmtree(full_path)
            else: os.remove(full_path)
            logger.info(f"Successfully deleted item: {full_path}")
            self._send_json_response(200, {"message": f"Successfully deleted item: '{item_path_str}'"})
        except Exception as e:
            logger.error(f"Error deleting item '{item_path_str}': {e}", exc_info=True)
            self._send_json_response(500, {"error": str(e)})
    def _handle_create_folder(self):
        try:
            content_length = int(self.headers['Content-Length'])
            if content_length == 0: return self._send_json_response(400, {'error': 'Request body is empty.'})
            body = json.loads(self.rfile.read(content_length))
            new_path_str = body.get('path')
            if not new_path_str: return self._send_json_response(400, {'error': "Request body must contain a 'path' key."})
            full_path = _resolve_path("/app/workspace", new_path_str)
            if os.path.exists(full_path): return self._send_json_response(409, {'error': f"Conflict: An item already exists at '{new_path_str}'."})
            os.makedirs(full_path)
            logger.info(f"Successfully created directory: {full_path}")
            self._send_json_response(201, {'message': f"Folder '{new_path_str}' created successfully."})
        except Exception as e:
            logger.error(f"Error creating folder: {e}", exc_info=True)
            self._send_json_response(500, {'error': str(e)})
    def _handle_rename_workspace_item(self):
        try:
            content_length = int(self.headers['Content-Length'])
            if content_length == 0: return self._send_json_response(400, {'error': 'Request body is empty.'})
            body = json.loads(self.rfile.read(content_length))
            old_path_str, new_path_str = body.get('old_path'), body.get('new_path')
            if not old_path_str or not new_path_str: return self._send_json_response(400, {'error': "Request body must contain 'old_path' and 'new_path' keys."})
            base_workspace = "/app/workspace"
            old_full_path = _resolve_path(base_workspace, old_path_str)
            new_full_path = _resolve_path(base_workspace, new_path_str)
            if not os.path.exists(old_full_path): return self._send_json_response(404, {'error': f"Source item not found: '{old_path_str}'."})
            if os.path.exists(new_full_path): return self._send_json_response(409, {'error': f"Destination already exists: '{new_path_str}'."})
            os.rename(old_full_path, new_full_path)
            logger.info(f"Successfully renamed '{old_full_path}' to '{new_full_path}'")
            self._send_json_response(200, {'message': f"Item renamed successfully to '{new_path_str}'."})
        except Exception as e:
            logger.error(f"Error renaming item: {e}", exc_info=True)
            self._send_json_response(500, {'error': str(e)})
    def _handle_get_file_content(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        workspace_id, filename = query_components.get("path", [None])[0], query_components.get("filename", [None])[0]
        if not workspace_id or not filename: return self._send_json_response(400, {"error": "Missing 'path' or 'filename' parameter."})
        try:
            full_path = _resolve_path(f"/app/workspace/{workspace_id}", filename)
            with open(full_path, 'r', encoding='utf-8') as f: content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e: self._send_json_response(500, {"error": f"Error reading file: {e}"})
    def _handle_get_raw_file(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        file_path_str = query_components.get("path", [None])[0]
        if not file_path_str: return self.send_error(400, "Missing 'path' query parameter.")
        try:
            full_path = _resolve_path("/app/workspace", file_path_str)
            if not os.path.isfile(full_path): return self.send_error(404, "File not found.")
            content_type, _ = mimetypes.guess_type(full_path)
            self.send_response(200)
            self.send_header('Content-type', content_type or 'application/octet-stream')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(full_path, 'rb') as f: self.wfile.write(f.read())
        except Exception as e:
            logger.error(f"Error serving raw file '{file_path_str}': {e}", exc_info=True)
            self.send_error(500, "Internal Server Error")
    def _handle_file_upload(self):
        try:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            workspace_id, file_item = form.getvalue('workspace_id'), form['file']
            if not workspace_id or not hasattr(file_item, 'filename') or not file_item.filename: return self._send_json_response(400, {'error': 'Missing workspace_id or file.'})
            filename = os.path.basename(file_item.filename)
            full_path = _resolve_path(f"/app/workspace/{workspace_id}", filename)
            with open(full_path, 'wb') as f: f.write(file_item.file.read())
            logger.info(f"Uploaded '{filename}' to workspace '{workspace_id}'")
            self._send_json_response(200, {'message': f"File '{filename}' uploaded successfully."})
        except Exception as e:
            logger.error(f"File upload failed: {e}", exc_info=True)
            self._send_json_response(500, {'error': f'Server error during file upload: {e}'})

def run_http_server():
    httpd = HTTPServer((os.getenv("BACKEND_HOST", "0.0.0.0"), int(os.getenv("FILE_SERVER_PORT", 8766))), WorkspaceHTTPHandler)
    logger.info(f"Starting HTTP file server on port {httpd.server_port}")
    httpd.serve_forever()


# --- WebSocket Core Logic ---

async def broadcast_event(event):
    """Sends an event to all active WebSocket connections."""
    if ACTIVE_CONNECTIONS:
        message = json.dumps(event, default=str)
        # Create a list of tasks for sending messages to all clients
        tasks = [conn.send(message) for conn in ACTIVE_CONNECTIONS]
        # Gather and run all send tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Failed to send message to a client: {result}")

async def agent_execution_wrapper(input_state, config):
    """Runs the agent and broadcasts events."""
    global RUNNING_AGENTS
    task_id = config["configurable"]["thread_id"]
    try:
        logger.info(f"Task '{task_id}': Agent execution starting.")
        await broadcast_event({"type": "agent_started", "task_id": task_id})
        
        async for event in agent_graph.astream_events(input_state, config):
            event_type = event["event"]
            if event_type in ["on_chain_start", "on_chain_end"] and event.get("name") in ["Chief_Architect", "Handyman", "Site_Foreman", "Worker", "Project_Supervisor", "Editor"]:
                await broadcast_event({"type": "agent_event", "event": event_type, "name": event.get("name"), "data": event['data'], "task_id": task_id})
        
        current_state = agent_graph.get_state(config)
        if current_state.next and "human_in_the_loop_node" in current_state.next:
            logger.info(f"Task '{task_id}': Paused for human approval.")
            await broadcast_event({"type": "plan_approval_request", "plan": current_state.values.get("plan"), "task_id": task_id})
        else:
            final_state = agent_graph.get_state(config)
            if final_state and (answer := final_state.values.get("answer")):
                final_answer_message = {"type": "final_answer", "data": answer, "task_id": task_id}
                if final_state.values.get("current_track") == "SIMPLE_TOOL_USE": final_answer_message["refresh_workspace"] = True
                await broadcast_event(final_answer_message)
            await broadcast_event({"type": "agent_stopped", "task_id": task_id, "message": "Agent run finished successfully."})
            
    except asyncio.CancelledError:
        logger.info(f"Task '{task_id}': Agent execution cancelled by user.")
        await broadcast_event({"type": "agent_stopped", "task_id": task_id, "message": "Agent run stopped by user."})
    except Exception as e:
        logger.error(f"Task '{task_id}': An error occurred during agent execution: {e}", exc_info=True)
        await broadcast_event({"type": "agent_stopped", "task_id": task_id, "message": f"An error occurred: {str(e)}"})
    finally:
        if task_id in RUNNING_AGENTS: del RUNNING_AGENTS[task_id]
        logger.info(f"Task '{task_id}': Cleaned up from RUNNING_AGENTS.")

async def run_agent_handler(data):
    global RUNNING_AGENTS
    task_id, prompt = data.get("task_id"), data.get("prompt")
    if not prompt or not task_id: return
    if task_id in RUNNING_AGENTS:
        logger.warning(f"Task '{task_id}': Agent is already running.")
        return await broadcast_event({"type": "error", "message": "Agent is already running for this task.", "task_id": task_id})

    config = {"recursion_limit": 100, "configurable": {"thread_id": task_id}}
    initial_state = {"messages": [HumanMessage(content=prompt)], "llm_config": data.get("llm_config", {}), "task_id": task_id}
    
    logger.info(f"Task '{task_id}': Creating background task for new agent run.")
    agent_task = asyncio.create_task(agent_execution_wrapper(initial_state, config))
    RUNNING_AGENTS[task_id] = agent_task

async def resume_agent_handler(data):
    global RUNNING_AGENTS
    task_id, feedback = data.get("task_id"), data.get("feedback")
    if not task_id or not feedback: return
    if task_id in RUNNING_AGENTS:
        logger.warning(f"Task '{task_id}': Agent is already running, cannot resume.")
        return

    config = {"recursion_limit": 100, "configurable": {"thread_id": task_id}}
    update_values = {"user_feedback": feedback}
    if (plan := data.get("plan")) is not None: update_values["plan"] = plan
    agent_graph.update_state(config, update_values)
    
    logger.info(f"Task '{task_id}': Creating background task to resume agent execution.")
    agent_task = asyncio.create_task(agent_execution_wrapper(None, config))
    RUNNING_AGENTS[task_id] = agent_task

async def handle_stop_agent(data):
    global RUNNING_AGENTS
    task_id = data.get("task_id")
    if not task_id: return
    
    logger.info(f"Task '{task_id}': Received request to stop agent.")
    if task_id in RUNNING_AGENTS:
        RUNNING_AGENTS[task_id].cancel()
    else:
        logger.warning(f"Task '{task_id}': Stop requested, but no running agent found.")
        await broadcast_event({"type": "agent_stopped", "task_id": task_id, "message": "Agent was not running."})

async def handle_task_create(data):
    if not (task_id := data.get("task_id")): return
    logger.info(f"Task '{task_id}': Received create task request.")
    os.makedirs(f"/app/workspace/{task_id}", exist_ok=True)

async def handle_task_delete(data):
    global RUNNING_AGENTS
    if not (task_id := data.get("task_id")): return
    logger.info(f"Task '{task_id}': Received delete task request.")
    if task_id in RUNNING_AGENTS: RUNNING_AGENTS[task_id].cancel()
    _safe_delete_workspace(task_id)

async def message_router(websocket):
    global ACTIVE_CONNECTIONS
    ACTIVE_CONNECTIONS.add(websocket)
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected. Total clients: {len(ACTIVE_CONNECTIONS)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")
                handlers = {"run_agent": run_agent_handler, "resume_agent": resume_agent_handler, "stop_agent": handle_stop_agent, "task_create": handle_task_create, "task_delete": handle_task_delete}
                if message_type in handlers: await handlers[message_type](data)
                else: logger.warning(f"Received unknown message type: '{message_type}'")
            except Exception as e: logger.error(f"Error processing message: {e}", exc_info=True)
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {client_id} disconnected: {e.code}")
    finally:
        logger.info(f"Cleaning up for client {client_id}")
        ACTIVE_CONNECTIONS.remove(websocket)
        logger.info(f"Client removed. Total clients: {len(ACTIVE_CONNECTIONS)}")

async def main():
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    async with websockets.serve(message_router, os.getenv("BACKEND_HOST", "0.0.0.0"), int(os.getenv("BACKEND_PORT", 8765))):
        logger.info("ResearchAgent server is running.")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down.")

