# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (with Models API)
#
# CORRECTION: The `_handle_file_upload` function has been updated to fix a
# `TypeError` from the deprecated `cgi` module. The check for the uploaded
# file is now more explicit (`file_item.value`) instead of relying on a
# direct boolean evaluation (`not file_item`), which is not supported.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
import json
import threading
import cgi
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import websockets
from langchain_core.messages import HumanMessage

# --- Local Imports ---
from .langgraph_agent import agent_graph
from .tools.file_system import _resolve_path

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
        # Capitalize provider and replace dashes in name with spaces
        name_parts = name.replace('-', ' ').split()
        formatted_name = ' '.join(part.capitalize() for part in name_parts)
        return f"{provider.capitalize()} {formatted_name}"
    except:
        return model_id # Fallback to the raw ID if parsing fails

# --- HTTP File Server for Workspace ---

class WorkspaceHTTPHandler(BaseHTTPRequestHandler):
    """A simple HTTP handler for workspace interactions."""

    def do_GET(self):
        """Routes GET requests to the appropriate handler."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/models':
            self._handle_get_models()
        elif parsed_path.path == '/files':
            self._handle_list_files(parsed_path)
        elif parsed_path.path == '/file-content':
            self._handle_get_file_content(parsed_path)
        else:
            self._send_json_response(404, {'error': 'Not Found'})

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/upload':
            self._handle_file_upload()
        else:
            self._send_json_response(404, {'error': 'Not Found'})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _handle_get_models(self):
        """Reads LLM model IDs from environment variables and returns them."""
        logger.info("Serving list of available models.")
        models = []
        model_ids = set()
        
        free_tier_model = "gemini::gemini-1.5-flash-latest"
        models.append({"id": free_tier_model, "name": format_model_name(free_tier_model)})
        model_ids.add(free_tier_model)
        
        for key, value in os.environ.items():
            if key.endswith("_LLM_ID") and value:
                if value not in model_ids:
                    models.append({"id": value, "name": format_model_name(value)})
                    model_ids.add(value)

        self._send_json_response(200, models)

    def _handle_list_files(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        subdir = query_components.get("path", [None])[0]
        if not subdir:
            return self._send_json_response(400, {"error": "Missing 'path' query parameter."})
        base_workspace = "/app/workspace"
        try:
            full_path = _resolve_path(base_workspace, subdir)
            if os.path.isdir(full_path):
                 self._send_json_response(200, {"files": os.listdir(full_path)})
            else:
                self._send_json_response(404, {"error": f"Directory '{subdir}' not found."})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_get_file_content(self, parsed_path):
        query_components = parse_qs(parsed_path.query)
        workspace_id = query_components.get("path", [None])[0]
        filename = query_components.get("filename", [None])[0]
        if not workspace_id or not filename:
            return self._send_json_response(400, {"error": "Missing 'path' or 'filename' parameter."})
        try:
            workspace_dir = f"/app/workspace/{workspace_id}"
            full_path = _resolve_path(workspace_dir, filename)
            with open(full_path, 'r', encoding='utf-8') as f:
                 content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self._send_json_response(500, {"error": f"Error reading file: {e}"})

    def _handle_file_upload(self):
        try:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            workspace_id = form.getvalue('workspace_id')
            file_item = form['file']
            
            # --- FIX: Explicitly check the file_item's value and filename ---
            if not workspace_id or not hasattr(file_item, 'filename') or not file_item.filename:
                return self._send_json_response(400, {'error': 'Missing workspace_id or file.'})

            filename = os.path.basename(file_item.filename)
            workspace_dir = f"/app/workspace/{workspace_id}"
            full_path = _resolve_path(workspace_dir, filename)

            with open(full_path, 'wb') as f:
                f.write(file_item.file.read())

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

# --- WebSocket Handler ---
async def agent_handler(websocket):
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info("Received new message from client.")
            try:
                payload = json.loads(message)
                prompt_text = payload.get("prompt")
                models_config = payload.get("models", {})

                if not prompt_text:
                    logger.warning("Received payload without a prompt.")
                    continue

                initial_state = {
                    "messages": [HumanMessage(content=json.dumps(payload))],
                }

                logger.info(f"Invoking agent with prompt: {prompt_text[:100]}...")
                logger.info(f"Using models: {models_config}")

                async for event in agent_graph.astream_events(initial_state, version="v1"):
                    event_type = event["event"]
                    if event_type in ["on_chain_start", "on_chain_end"]:
                        response = { "type": "agent_event", "event": event_type, "name": event["name"], "data": event['data'] }
                        await websocket.send(json.dumps(response, default=str))

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from message: {message}")
                error_response = {"type": "error", "data": "Invalid JSON format received."}
                await websocket.send(json.dumps(error_response))
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                error_response = {"type": "error", "data": str(e)}
                await websocket.send(json.dumps(error_response))

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the handler: {e}", exc_info=True)

# --- Main Server Function ---
async def main():
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))

    logger.info(f"Starting ResearchAgent WebSocket server at ws://{host}:{port}")
    async with websockets.serve(agent_handler, host, port, max_size=None):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        logger.info("Executing main function to start servers.")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down gracefully.")
