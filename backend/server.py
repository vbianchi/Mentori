# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 12.1: Smart Workspace API - FIX)
#
# This version fixes a routing bug from the previous iteration.
#
# 1. Robust Path Matching: The `do_GET` method now strips any trailing
#    slashes from the request path before attempting to match it to a
#    handler. This prevents errors if the browser or client adds a
#    trailing `/` to the URL (e.g., `/api/workspace/items/`).
# 2. Diagnostic 404 Message: The final "Not Found" error message has been
#    upgraded to include the path that the server failed to route. This
#    will make any future routing bugs much easier to identify.
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
        # --- FIX: Normalize the path to be more robust ---
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
            # --- FIX: Improved error message for easier debugging ---
            self._send_json_response(404, {'error': f"Not Found: The path '{path}' does not match any known API routes."})


    # --- POST Requests Handler ---
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/upload': self._handle_file_upload()
        else: self._send_json_response(404, {'error': 'Not Found'})
    
    # --- OPTIONS Requests Handler (for CORS) ---
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE') # Allow all methods we'll use
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
        """Serves the list of available tools, plus a special one for the Editor."""
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
        """Handles requests to list items in the workspace with structured details."""
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
                    # Get size for files, 0 for directories
                    item_size = os.path.getsize(item_path) if item_type == 'file' else 0
                except OSError:
                    # Handle cases like broken symlinks where size cannot be retrieved
                    item_size = 0
                
                items.append({"name": item_name, "type": item_type, "size": item_size})
            
            # Respond with a structured list of items
            self._send_json_response(200, {"items": items})

        except Exception as e:
            logger.error(f"Error listing workspace items for path '{subdir}': {e}", exc_info=True)
            self._send_json_response(500, {"error": str(e)})
    
    def _handle_get_file_content(self, parsed_path):
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
    task_id = data.get("task_id")
    if not task_id: return
    logger.info(f"Task '{task_id}': Received create task request.")
    workspace_path = f"/app/workspace/{task_id}"
    os.makedirs(workspace_path, exist_ok=True)


async def handle_task_delete(websocket, data):
    task_id = data.get("task_id")
    if not task_id: return
    logger.info(f"Task '{task_id}': Received delete task request.")
    _safe_delete_workspace(task_id)


async def message_router(websocket):
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
