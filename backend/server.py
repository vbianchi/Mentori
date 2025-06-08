# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Corrected)
#
# This version implements the user's correct finding: the `path` argument
# has been removed from the `agent_handler` function signature to match
# the current `websockets` library API.
# -----------------------------------------------------------------------------

# --- Verification Step ---
print("--- EXECUTING LATEST SERVER.PY (v_correct_handler) ---")

import asyncio
import logging
import os
import json
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

# --- WebSocket Handler ---
# === FIX: The 'path' argument has been removed as it is no longer passed by the library ===
async def agent_handler(websocket):
    """
    Handles incoming WebSocket connections, runs the agent, and streams all
    graph events back to the client.
    """
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info("Received new message from client.")
            try:
                inputs = {"messages": [HumanMessage(content=message)]}
                logger.info(f"Invoking agent with input: {message[:100]}...")

                async for event in agent_graph.astream_events(inputs, version="v1"):
                    event_type = event["event"]
                    event_name = event["name"]
                    
                    if event_type in ["on_chain_start", "on_chain_end"]:
                        response = {
                            "type": "agent_event",
                            "event": event_type,
                            "name": event_name,
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
    """Starts the WebSocket server."""
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))
    
    max_size = int(os.getenv("WEBSOCKET_MAX_SIZE_BYTES", 16 * 1024 * 1024))
    ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", 20))
    ping_timeout = int(os.getenv("WEBSOCKET_PING_TIMEOUT", 30))

    logger.info(f"Starting ResearchAgent WebSocket server at ws://{host}:{port}")

    async with websockets.serve(
        agent_handler, # Pass the handler directly
        host,
        port,
        max_size=max_size,
        ping_interval=ping_interval,
        ping_timeout=ping_timeout
    ):
        await asyncio.Future()

# --- Entry Point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down gracefully.")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)
