# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (with File API)
#
# This version is updated to include a secondary HTTP server. This server
# provides a simple API endpoint for the frontend to securely list the
# contents of the agent's sandboxed workspace directories.
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

# --- Configuration ---
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- HTTP File Server for Workspace ---

class WorkspaceHTTPHandler(BaseHTTPRequestHandler):
    """A simple HTTP handler to list files in the workspace."""
    
    def do_GET(self):
        if self.path.startswith('/files'):
            self._handle_list_files()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def _handle_list_files(self):
        """Handles the /files endpoint to list directory contents."""
        query_components = parse_qs(urlparse(self.path).query)
        subdir = query_components.get("path", [None])[0]

        if not subdir:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'path' query parameter."}).encode())
            return

        # --- Security Check ---
        base_workspace = os.path.abspath("/app/workspace")
        requested_path = os.path.abspath(os.path.join(base_workspace, subdir))

        if not requested_path.startswith(base_workspace):
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Access denied. Path is outside the workspace."}).encode())
            return
        
        try:
            if os.path.isdir(requested_path):
                files = os.listdir(requested_path)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*') # For development
                self.end_headers()
                self.wfile.write(json.dumps({"files": files}).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Directory '{subdir}' not found."}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

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
