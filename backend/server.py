# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 12.4: Rename Endpoint - COMPLETE)
#
# This version completes the "Interactive Workbench" API by adding the
# final required endpoint for renaming files and folders.
#
# 1. New `do_PUT` Method: A `do_PUT` handler is added to handle rename
#    operations, routed to `/api/workspace/items`.
# 2. Rename Logic: The new `_handle_rename_workspace_item` method parses
#    a JSON body containing `old_path` and `new_path`.
# 3. Validation & Security: The method includes checks to ensure the
#    source path exists and the destination path does *not* exist, preventing
#    errors and accidental overwrites. It uses `os.rename` to perform the
#    operation securely within the workspace.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
import json
import threading
import cgi
import shutil
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

# --- Configuration ---
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper to format model names ---
def format_model_name(model_id):
    """Creates a user-friendly name from a model ID."""
    try:
        provider, name = model_id.split("::")
        name_parts = name.replace('-', ' ').split()
        formatted_name = ' '.join(part.capitalize() for part in name_parts)
        return f"{provider.capitalize()} {formatted_name}"
    except:
        return model_id

# --- Workspace Deletion Helper ---
def _safe_delete_workspace(task_id: str):
    """Safely and recursively deletes a task's workspace directory."""
    try:
        workspace_path = _resolve_path("/app/workspace", task_id)
        if not os.path.abspath(workspace_path).startswith(os.path.abspath("/app/workspace")):
            raise PermissionError("Security check failed: Attempt to delete directory outside of workspace.")
        if os.path.isdir(workspace_path):
            shutil.rmtree(workspace_path)
            logger.info(f"Task '{task_id}': Successfully deleted workspace directory: {workspace_path}")
            return True
        else:
            logger.warning(f"Task '{task_id}': Workspace directory not found for deletion: {workspace_path}")
            return False
    except Exception as e:
        logger.error(f"Task '{task_id}': Error deleting workspace: {e}", exc_info=True)
        return False

# --- HTTP File Server for Workspace ---
class WorkspaceHTTPHandler(BaseHTTPRequestHandler):
    # --- GET Requests Handler ---
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')

        if path == '/api/models':
            self._handle_get_models()
        elif path == '/api/tools':
            self._handle_get_tools()
        elif path == '/api/workspace/items':
            self._handle_get_workspace_items(parsed_path)
        elif path == '/file-content':
            self._handle_get_file_content(parsed_path)
        else:
            self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known API routes."})

    # --- POST Requests Handler ---
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')

        if path == '/api/workspace/folders':
            self._handle_create_folder()
        elif path == '/upload': 
            self._handle_file_upload()
        else: 
            self._send_json_response(404, {'error': f"Not Found: The POST path '{path}' does not match any known API routes."})
    
    # --- DELETE Requests Handler ---
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')

        if path == '/api/workspace/items':
            self._handle_delete_workspace_item(parsed_path)
        else:
            self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known DELETE routes."})

    # --- NEW: PUT Requests Handler ---
    def do_PUT(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')

        if path == '/api/workspace/items':
            self._handle_rename_workspace_item()
        else:
            self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known PUT routes."})

    # --- OPTIONS Requests Handler (for CORS) ---
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()
    
    # --- Internal Helper Methods ---
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _handle_get_models(self):
        # ... (no changes in this method)
        logger.info("Parsing .env to serve available and default models.")
        available_models = []
        model_ids = set()
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
        if not available_models:
            available_models.append({"id": safe_fallback_model, "name": format_model_name(safe_fallback_model)})
        global_default_llm = os.getenv("DEFAULT_LLM_ID", safe_fallback_model)
        default_models = {
            "ROUTER_LLM_ID": os.getenv("ROUTER_LLM_ID", global_default_llm),
            "CHIEF_ARCHITECT_LLM_ID": os.getenv("CHIEF_ARCHITECT_LLM_ID", global_default_llm),
            "SITE_FOREMAN_LLM_ID": os.getenv("SITE_FOREMAN_LLM_ID", global_default_llm),
            "PROJECT_SUPERVISOR_LLM_ID": os.getenv("PROJECT_SUPERVISOR_LLM_ID", global_default_llm),
            "EDITOR_LLM_ID": os.getenv("EDITOR_LLM_ID", "gemini::gemini-1.5-pro-latest")
        }
        response_data = { "available_models": available_models, "default_models": default_models }
        self._send_json_response(200, response_data)

    def _handle_get_tools(self):
        # ... (no changes in this method)
        logger.info("Serving available tools list.")
        try:
            loaded_tools = get_available_tools()
            formatted_tools = [
                {"name": tool.name, "description": tool.description}
                for tool in loaded_tools
            ]
            editor_tool = {
                "name": "The Editor",
                "description": "Use a powerful language model to perform tasks like rewriting, summarizing, or analyzing text."
            }
            all_tools = [editor_tool] + formatted_tools
            self._send_json_response(200, {"tools": all_tools})
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}", exc_info=True)
            self._send_json_response(500, {"error": "Could not retrieve tools."})

    def _handle_get_workspace_items(self, parsed_path):
        # ... (no changes in this method)
        logger.info("Serving structured workspace items list.")
        query_components = parse_qs(parsed_path.query)
        subdir = query_components.get("path", [None])[0]

        if not subdir:
            return self._send_json_response(400, {"error": "Missing 'path' query parameter."})

        base_workspace = "/app/workspace"
        try:
            full_path = _resolve_path(base_workspace, subdir)
            if not os.path.isdir(full_path):
                return self._send_json_response(404, {"error": f"Directory not found: '{subdir}'"})

            items = []
            for item_name in os.listdir(full_path):
                item_path = os.path.join(full_path, item_name)
                item_type = 'directory' if os.path.isdir(item_path) else 'file'
                try:
                    item_size = os.path.getsize(item_path) if item_type == 'file' else 0
                except OSError:
                    item_size = 0
                
                items.append({"name": item_name, "type": item_type, "size": item_size})
            
            self._send_json_response(200, {"items": items})

        except Exception as e:
            logger.error(f"Error listing workspace items for path '{subdir}': {e}", exc_info=True)
            self._send_json_response(500, {"error": str(e)})

    def _handle_delete_workspace_item(self, parsed_path):
        # ... (no changes in this method)
        logger.info("Handling request to delete workspace item.")
        query_components = parse_qs(parsed_path.query)
        item_path_str = query_components.get("path", [None])[0]

        if not item_path_str:
            return self._send_json_response(400, {"error": "Missing 'path' query parameter."})

        base_workspace = "/app/workspace"
        try:
            full_path = _resolve_path(base_workspace, item_path_str)
            
            if not os.path.exists(full_path):
                return self._send_json_response(404, {"error": f"Item not found: '{item_path_str}'"})

            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                logger.info(f"Successfully deleted directory: {full_path}")
            else:
                os.remove(full_path)
                logger.info(f"Successfully deleted file: {full_path}")
            
            self._send_json_response(200, {"message": f"Successfully deleted item: '{item_path_str}'"})

        except PermissionError as e:
            logger.warning(f"Permission denied while trying to delete '{item_path_str}': {e}")
            self._send_json_response(403, {"error": str(e)})
        except Exception as e:
            logger.error(f"Error deleting workspace item '{item_path_str}': {e}", exc_info=True)
            self._send_json_response(500, {"error": str(e)})
    
    def _handle_create_folder(self):
        # ... (no changes in this method)
        try:
            content_length = int(self.headers['Content-Length'])
            if content_length == 0:
                return self._send_json_response(400, {'error': 'Request body is empty.'})
            
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            
            new_path_str = body.get('path')
            if not new_path_str:
                return self._send_json_response(400, {'error': "Request body must contain a 'path' key."})

            base_workspace = "/app/workspace"
            full_path = _resolve_path(base_workspace, new_path_str)

            if os.path.exists(full_path):
                return self._send_json_response(409, {'error': f"Conflict: An item already exists at '{new_path_str}'."})

            os.makedirs(full_path)
            logger.info(f"Successfully created directory: {full_path}")
            self._send_json_response(201, {'message': f"Folder '{new_path_str}' created successfully."})

        except json.JSONDecodeError:
            self._send_json_response(400, {'error': 'Invalid JSON in request body.'})
        except Exception as e:
            logger.error(f"Error creating folder: {e}", exc_info=True)
            self._send_json_response(500, {'error': str(e)})

    # --- NEW METHOD for Renaming Items ---
    def _handle_rename_workspace_item(self):
        """Handles requests to rename a file or directory."""
        try:
            content_length = int(self.headers['Content-Length'])
            if content_length == 0:
                return self._send_json_response(400, {'error': 'Request body is empty.'})
            
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            
            old_path_str = body.get('old_path')
            new_path_str = body.get('new_path')

            if not old_path_str or not new_path_str:
                return self._send_json_response(400, {'error': "Request body must contain 'old_path' and 'new_path' keys."})

            base_workspace = "/app/workspace"
            old_full_path = _resolve_path(base_workspace, old_path_str)
            new_full_path = _resolve_path(base_workspace, new_path_str)

            if not os.path.exists(old_full_path):
                return self._send_json_response(404, {'error': f"Source item not found: '{old_path_str}'."})
            
            if os.path.exists(new_full_path):
                return self._send_json_response(409, {'error': f"Destination already exists: '{new_path_str}'."})

            os.rename(old_full_path, new_full_path)
            logger.info(f"Successfully renamed '{old_full_path}' to '{new_full_path}'")
            self._send_json_response(200, {'message': f"Item renamed successfully to '{new_path_str}'."})

        except json.JSONDecodeError:
            self._send_json_response(400, {'error': 'Invalid JSON in request body.'})
        except Exception as e:
            logger.error(f"Error renaming item: {e}", exc_info=True)
            self._send_json_response(500, {'error': str(e)})


    def _handle_get_file_content(self, parsed_path):
        # ... (no changes in this method)
        query_components = parse_qs(parsed_path.query)
        workspace_id = query_components.get("path", [None])[0]
        filename = query_components.get("filename", [None])[0]
        if not workspace_id or not filename: return self._send_json_response(400, {"error": "Missing 'path' or 'filename' parameter."})
        try:
            workspace_dir = f"/app/workspace/{workspace_id}"
            full_path = _resolve_path(workspace_dir, filename)
            with open(full_path, 'r', encoding='utf-8') as f: content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e: self._send_json_response(500, {"error": f"Error reading file: {e}"})

    def _handle_file_upload(self):
        # ... (no changes in this method)
        try:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            workspace_id = form.getvalue('workspace_id')
            file_item = form['file']
            if not workspace_id or not hasattr(file_item, 'filename') or not file_item.filename: return self._send_json_response(400, {'error': 'Missing workspace_id or file.'})
            filename = os.path.basename(file_item.filename)
            workspace_dir = f"/app/workspace/{workspace_id}"
            full_path = _resolve_path(workspace_dir, filename)
            with open(full_path, 'wb') as f: f.write(file_item.file.read())
            logger.info(f"Uploaded '{filename}' to workspace '{workspace_id}'")
            self._send_json_response(200, {'message': f"File '{filename}' uploaded successfully."})
        except Exception as e:
            logger.error(f"File upload failed: {e}", exc_info=True)
            self._send_json_response(500, {'error': f'Server error during file upload: {e}'})

def run_http_server():
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("FILE_SERVER_PORT", 8766))
    server_address = (host, port)
    httpd = HTTPServer(server_address, WorkspaceHTTPHandler)
    logger.info(f"Starting HTTP file server at http://{host}:{port}")
    httpd.serve_forever()


# --- WebSocket Handlers ---
async def run_agent_handler(websocket, data):
    # ... (no changes in this method)
    prompt = data.get("prompt")
    llm_config = data.get("llm_config", {})
    task_id = data.get("task_id")

    if not prompt or not task_id:
        return

    initial_state = { "messages": [HumanMessage(content=prompt)], "llm_config": llm_config, "task_id": task_id }
    config = {"recursion_limit": 100, "configurable": {"thread_id": task_id}}

    logger.info(f"Task '{task_id}': Invoking agent with prompt: {prompt[:100]}...")
    
    async for event in agent_graph.astream_events(initial_state, config=config, version="v1"):
        event_type = event["event"]
        if event_type in ["on_chain_start", "on_chain_end"] and event["name"] in ["Chief_Architect", "Handyman", "Site_Foreman", "Worker", "Project_Supervisor", "Editor"]:
            response = {"type": "agent_event", "event": event_type, "name": event["name"], "data": event['data'], "task_id": task_id}
            await websocket.send(json.dumps(response, default=str))

    current_state = agent_graph.get_state(config)
    next_node = current_state.next if current_state else None

    if next_node and "human_in_the_loop_node" in next_node:
        logger.info(f"Task '{task_id}': Graph paused for human approval.")
        plan = current_state.values.get("plan")
        await websocket.send(json.dumps({"type": "plan_approval_request", "plan": plan, "task_id": task_id}))
    else:
        final_state = agent_graph.get_state(config)
        if final_state and (answer := final_state.values.get("answer")):
            final_answer_message = {"type": "final_answer", "data": answer, "task_id": task_id}
            
            if final_state.values.get("current_track") == "SIMPLE_TOOL_USE":
                logger.info(f"Task '{task_id}': Handyman track complete. Sending workspace refresh signal.")
                final_answer_message["refresh_workspace"] = True

            await websocket.send(json.dumps(final_answer_message))


async def resume_agent_handler(websocket, data):
    # ... (no changes in this method)
    task_id = data.get("task_id")
    feedback = data.get("feedback")
    new_plan = data.get("plan")

    if not task_id or not feedback:
        return

    logger.info(f"Task '{task_id}': Resuming agent with user feedback: '{feedback}'.")
    config = {"recursion_limit": 100, "configurable": {"thread_id": task_id}}
    
    update_values = {"user_feedback": feedback}
    if new_plan and isinstance(new_plan, list):
        logger.info(f"Task '{task_id}': User provided a modified plan.")
        update_values["plan"] = new_plan

    agent_graph.update_state(config, update_values)
    
    async for event in agent_graph.astream_events(None, config=config, version="v1"):
        event_type = event["event"]
        if event_type in ["on_chain_start", "on_chain_end"] and event["name"] in ["Site_Foreman", "Worker", "Project_Supervisor", "Editor"]:
            response = {"type": "agent_event", "event": event_type, "name": event["name"], "data": event['data'], "task_id": task_id}
            await websocket.send(json.dumps(response, default=str))
    
    final_state = agent_graph.get_state(config)
    if final_state and (answer := final_state.values.get("answer")):
        await websocket.send(json.dumps({"type": "final_answer", "data": answer, "task_id": task_id}))


async def handle_task_create(websocket, data):
    # ... (no changes in this method)
    task_id = data.get("task_id")
    if not task_id: return
    logger.info(f"Task '{task_id}': Received create task request.")
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)


async def handle_task_delete(websocket, data):
    # ... (no changes in this method)
    task_id = data.get("task_id")
    if not task_id: return
    logger.info(f"Task '{task_id}': Received delete task request.")
    _safe_delete_workspace(task_id)


async def message_router(websocket):
    # ... (no changes in this method)
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "run_agent":
                    await run_agent_handler(websocket, data)
                elif message_type == "resume_agent":
                    await resume_agent_handler(websocket, data)
                elif message_type == "task_create":
                    await handle_task_create(websocket, data)
                elif message_type == "task_delete":
                    await handle_task_delete(websocket, data)
                else:
                    logger.warning(f"Received unknown message type: '{message_type}'")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from message: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the handler: {e}", exc_info=True)


async def main():
    # ... (no changes in this method)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))
    logger.info(f"Starting ResearchAgent WebSocket server at ws://{host}:{port}")
    async with websockets.serve(message_router, host, port, max_size=None):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down gracefully.")
