# -----------------------------------------------------------------------------
# ResearchAgent Backend Server (Phase 2: Agent Integration)
#
# This file implements the main WebSocket server for the ResearchAgent.
# It's now updated to import the LangGraph agent and use it to process
# incoming user messages, streaming the LLM's response back to the client.
#
# Usage:
# Run this file via Docker Compose, which handles the environment.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
import json
from dotenv import load_dotenv
import websockets

# --- Local Imports ---
# Import the compiled agent graph from our agent module.
from .langgraph_agent import agent_graph

# --- Configuration ---
# Load environment variables from the .env file in the project root.
load_dotenv()

# Set up basic logging to see server events in the console.
# The logging level is configured via the LOG_LEVEL environment variable.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- WebSocket Handler ---
async def agent_handler(websocket, path):
    """
    Handles incoming WebSocket connections, runs the agent, and streams responses.
    """
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        # Listen for messages from the client.
        async for message in websocket:
            logger.info(f"Received message from client.")
            try:
                # The agent expects a dictionary with a 'question' key.
                inputs = {"question": message}
                logger.info(f"Invoking agent with input: {inputs}")

                # Use ainvoke_stream to get a stream of events from the graph.
                # This is crucial for our real-time UI updates.
                async for event in agent_graph.astream_events(inputs, version="v1"):
                    # We are interested in the 'direct_qa' node's completion event.
                    if event["event"] == "on_chain_end" and event["name"] == "direct_qa":
                        # The final state of the node contains the answer.
                        node_output = event["data"]["output"]
                        final_answer = node_output.get("answer", "No answer found.")

                        # Create a JSON response to send to the client.
                        # This structured format is easier for the frontend to parse.
                        response = {
                            "type": "final_answer",
                            "data": final_answer
                        }
                        await websocket.send(json.dumps(response))
                        logger.info("Sent final answer to client.")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Inform the client about the error.
                error_response = {
                    "type": "error",
                    "data": str(e)
                }
                await websocket.send(json.dumps(error_response))

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the handler: {e}", exc_info=True)


# --- Main Server Function ---
async def main():
    """
    Starts the WebSocket server.
    """
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8765))
    max_size = int(os.getenv("WEBSOCKET_MAX_SIZE_BYTES", 16 * 1024 * 1024))
    ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", 20))
    ping_timeout = int(os.getenv("WEBSOCKET_PING_TIMEOUT", 30))

    logger.info(f"Starting ResearchAgent WebSocket server at ws://{host}:{port}")

    # Start the server with the agent_handler and recommended settings.
    async with websockets.serve(
        agent_handler,
        host,
        port,
        max_size=max_size,
        ping_interval=ping_interval,
        ping_timeout=ping_timeout
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
