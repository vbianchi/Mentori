# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 7: Final Answer Handling)
#
# This version updates the server to handle the output from the new
# `Final_Answer_Agent` node in the graph.
#
# 1. New Message Type: The WebSocket handler can now send a `final_answer`
#    message type to the client, distinguishing it from the `direct_answer`.
# 2. Updated Output Parsing: The logic that processes the final graph event
#    now checks for output from both 'Librarian' (for direct QA) and
#    'Final_Answer_Agent' (for synthesized plan summaries).
# 3. New Configurable Model: The HTTP server now exposes the
#    `FINAL_ANSWER_LLM_ID` so it can be configured from the frontend.
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
        name_parts = name.replace('-', ' ').split()
        formatted_name = ' '.join(part.capitalize() for part in name_parts)
        return f"{provider.capitalize()} {formatted_name}"
    except:
        return model_id

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
        """
        Parses the .env file to build a structured response with all available
        models and the user-configured default model for each agent role.
        """
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
            logger.warning("No models found in .env. Using a single safe fallback.")

        global_default_llm = os.getenv("DEFAULT_LLM_ID", safe_fallback_model)

        default_models = {
            "PLANNER_LLM_ID": os.getenv("PLANNER_LLM_ID", global_default_llm),
            "CONTROLLER_LLM_ID": os.getenv("CONTROLLER_LLM_ID", global_default_llm),
            "EXECUTOR_LLM_ID": os.getenv("EXECUTOR_LLM_ID", global_default_llm),
            "EVALUATOR_LLM_ID": os.getenv("EVALUATOR_LLM_ID", global_default_llm),
            "ROUTER_LLM_ID": os.getenv("ROUTER_LLM_ID", global_default_llm),
            "FINAL_ANSWER_LLM_ID": os.getenv("FINAL_ANSWER_LLM_ID", "gemini::gemini-1.5-pro-latest") # Added
        }

        response_data = {
            "available_models": available_models,
            "default_models": default_models
        }
        self._send_json_response(200, response_data)

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

# --- WebSocket Handler (Upgraded) ---
async def agent_handler(websocket):
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info("Received new message from client.")
            try:
                data = json.loads(message)
                prompt = data.get("prompt")
                llm_config = data.get("llm_config", {})

                if not prompt:
                    logger.warning("Received payload without a prompt.")
                    continue

                initial_state = {
                    "messages": [HumanMessage(content=prompt)],
                    "llm_config": llm_config,
                }

                config = {"recursion_limit": 100}

                logger.info(f"Invoking agent with prompt: {prompt[:100]}...")
                logger.debug(f"Using LLM config for this run: {llm_config}")
                logger.debug(f"Graph config: {config}")

                last_event = None
                async for event in agent_graph.astream_events(initial_state, config=config, version="v1"):
                    last_event = event
                    event_type = event["event"]
                    if event_type in ["on_chain_start", "on_chain_end"]:
                        response = { "type": "agent_event", "event": event_type, "name": event["name"], "data": event['data'] }
                        await websocket.send(json.dumps(response, default=str))

                if last_event and last_event["event"] == "on_chain_end":
                    final_output = last_event.get("data", {}).get("output")
                    logger.debug(f"DEBUG: Final output structure from graph: {final_output}")

                    answer = None
                    answer_type = None

                    # --- THE FIX: Check for output from EITHER final node ---
                    if isinstance(final_output, list):
                        for node_output in final_output:
                            if isinstance(node_output, dict):
                                if 'Librarian' in node_output:
                                    librarian_result = node_output.get('Librarian')
                                    if isinstance(librarian_result, dict) and 'answer' in librarian_result:
                                        answer = librarian_result.get('answer')
                                        answer_type = "direct_answer"
                                        break
                                elif 'Final_Answer_Agent' in node_output:
                                    final_answer_result = node_output.get('Final_Answer_Agent')
                                    if isinstance(final_answer_result, dict) and 'answer' in final_answer_result:
                                        answer = final_answer_result.get('answer')
                                        answer_type = "final_answer"
                                        break
                    # --- End of Fix ---

                    if answer and answer_type:
                        logger.info(f"Found answer of type '{answer_type}': {answer[:100]}...")
                        answer_response = {"type": answer_type, "data": answer}
                        await websocket.send(json.dumps(answer_response))
                    else:
                        logger.info("Agent run completed without a direct answer (assumed plan).")

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from message: {message}")
                await websocket.send(json.dumps({"type": "error", "data": "Invalid JSON format received."}))
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send(json.dumps({"type": "error", "data": str(e)}))

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
