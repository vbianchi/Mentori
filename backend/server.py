# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (with File API)
#
# This version is updated to include a new API endpoint: /file-content
# This allows the frontend to securely request and display the content of a
# specific file from within the agent's sandboxed workspace.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import websockets
from langchain_core.messages import HumanMessage

# --- Local Imports ---
from .langgraph_agent import agent_graph
# Import the security helper from the file system tool
from .tools.file_system import _resolve_path 

# --- Configuration ---
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- HTTP File Server for Workspace ---

class WorkspaceHTTPHandler(BaseHTTPRequestHandler):
    """A simple HTTP handler for workspace interactions."""

    def do_GET(self):
        """Routes GET requests to the appropriate handler."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/files':
            self._handle_list_files(parsed_path)
        elif parsed_path.path == '/file-content':
            self._handle_get_file_content(parsed_path)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests for development."""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()


    def _send_json_response(self, status_code, data):
        """Helper to send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # For development
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _handle_list_files(self, parsed_path):
        """Handles the /files endpoint to list directory contents."""
        query_components = parse_qs(parsed_path.query)
        subdir = query_components.get("path", [None])[0]

        if not subdir:
            self._send_json_response(400, {"error": "Missing 'path' query parameter."})
            return

        base_workspace = "/app/workspace"
        
        try:
            # We don't need to resolve the path here since listdir is not recursive,
            # but we do need to construct the full path for the OS call.
            full_path = os.path.join(base_workspace, subdir)
            # Security check to prevent path traversal (e.g., /files?path=../)
            if not os.path.abspath(full_path).startswith(os.path.abspath(base_workspace)):
                 self._send_json_response(403, {"error": "Access denied. Path is outside the workspace."})
                 return

            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                self._send_json_response(200, {"files": files})
            else:
                self._send_json_response(404, {"error": f"Directory '{subdir}' not found."})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
            
    def _handle_get_file_content(self, parsed_path):
        """Handles the /file-content endpoint to read a specific file."""
        query_components = parse_qs(parsed_path.query)
        workspace_id = query_components.get("path", [None])[0]
        filename = query_components.get("filename", [None])[0]

        if not workspace_id or not filename:
            self._send_json_response(400, {"error": "Missing 'path' or 'filename' query parameter."})
            return
            
        try:
            # Use the already existing security helper to resolve and validate the path
            workspace_dir = f"/app/workspace/{workspace_id}"
            full_path = _resolve_path(workspace_dir, filename)

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*') # For development
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except PermissionError as e:
            self._send_json_response(403, {"error": str(e)})
        except FileNotFoundError:
             self._send_json_response(404, {"error": f"File '{filename}' not found."})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})


def run_http_server():
    """Starts the HTTP server in a separate thread."""
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("FILE_SERVER_PORT", 8766))
    server_address = (host, port)
    httpd = HTTPServer(server_address, WorkspaceHTTPHandler)
    logger.info(f"Starting HTTP file server at http://{host}:{port}")
    httpd.serve_forever()

# --- WebSocket Handler ---
async def agent_handler(websocket):
    """Handles incoming WebSocket connections and runs the agent."""
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info("Received new message from client.")
            try:
                inputs = {"messages": [HumanMessage(content=message)]}
                logger.info(f"Invoking agent with input: {message[:100]}...")

                async for event in agent_graph.astream_events(inputs, version="v1"):
                    event_type = event["event"]
                    # We stream all major node events to the frontend
                    if event_type in ["on_chain_start", "on_chain_end"]:
                        response = {
                            "type": "agent_event",
                            "event": event_type,
                            "name": event["name"],
                            "data": event['data']
                        }
                        await websocket.send(json.dumps(response, default=str))

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
    """Starts both the WebSocket and HTTP servers."""
    # Start the HTTP server in a daemon thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Configure and start the WebSocket server
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))
    max_size = int(os.getenv("WEBSOCKET_MAX_SIZE_BYTES", 16 * 1024 * 1024))
    ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", 20))
    ping_timeout = int(os.getenv("WEBSOCKET_PING_TIMEOUT", 30))

    logger.info(f"Starting ResearchAgent WebSocket server at ws://{host}:{port}")

    async with websockets.serve(
        agent_handler, host, port, max_size=max_size,
        ping_interval=ping_interval, ping_timeout=ping_timeout
    ):
        await asyncio.Future()  # Run forever

# --- Entry Point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down gracefully.")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)

