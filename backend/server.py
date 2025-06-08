# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 1: Echo Server)
#
# This file implements the main WebSocket server for the ResearchAgent.
# For this initial phase, it's a simple echo server that listens for a
# message and sends it back to the client. This verifies our core
# communication infrastructure.
#
# Usage:
# Run this file directly (python -m backend.server) or via Docker Compose.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
from dotenv import load_dotenv
import websockets

# --- Configuration ---
# Load environment variables from the .env file in the project root.
load_dotenv()

# Set up basic logging to see server events in the console.
# The logging level is configured via the LOG_LEVEL environment variable.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# --- WebSocket Handler ---
async def echo_handler(websocket, path):
    """
    Handles incoming WebSocket connections.
    For Phase 1, it simply echoes any received message back to the client.
    """
    logging.info(f"Client connected from {websocket.remote_address}")
    try:
        # Listen for messages from the client indefinitely.
        async for message in websocket:
            logging.info(f"Received message: {message}")
            # Echo the received message back to the client.
            await websocket.send(f"Echo: {message}")
            logging.info(f"Echoed message back to client.")
    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"Client disconnected: {e.k}")
    except Exception as e:
        logging.error(f"An error occurred in the handler: {e}")

# --- Main Server Function ---
async def main():
    """
    Starts the WebSocket server.
    """
    # Retrieve server configuration from environment variables.
    # We provide sensible defaults if the variables are not set.
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))

    # Get WebSocket-specific settings
    max_size = int(os.getenv("WEBSOCKET_MAX_SIZE_BYTES", 16 * 1024 * 1024)) # 16MB default
    ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", 20))
    ping_timeout = int(os.getenv("WEBSOCKET_PING_TIMEOUT", 30))


    logging.info(f"Starting WebSocket echo server at ws://{host}:{port}")

    # Start the server with the specified handler and settings.
    async with websockets.serve(
        echo_handler,
        host,
        port,
        max_size=max_size,
        ping_interval=ping_interval,
        ping_timeout=ping_timeout
    ):
        # The server runs forever until the process is stopped.
        await asyncio.Future()

# --- Entry Point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server shut down gracefully.")
    except Exception as e:
        logging.critical(f"Server failed to start: {e}")