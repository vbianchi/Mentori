# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import shlex # For parsing command strings if needed later, maybe not needed now

# --- LangChain Imports ---
from langchain.agents import AgentExecutor
from langchain.callbacks.base import AsyncCallbackHandler # For potential custom callbacks later
# -------------------------

# --- Project Imports ---
from backend.config import load_settings, Settings
# from backend.llm_planners import get_planner, LLMPlanner # No longer needed
from backend.llm_setup import get_llm # Import LLM setup function
from backend.tools import agent_tools # Import the list of tools
from backend.agent import create_agent_executor # Import agent creation function
# ----------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Settings, Initialize LLM and Agent Executor (at startup) ---
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    agent_executor: AgentExecutor = create_agent_executor(llm, agent_tools)
    logger.info("LangChain Agent Executor initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Failed during LangChain setup: {e}", exc_info=True)
    exit(1) # Exit if core components fail to initialize

connected_clients = set()

# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    logger.info(f"Client connected from {websocket.remote_address}")
    connected_clients.add(websocket)
    # No need for current_task/plan state here anymore, agent manages its own state

    # --- Helper to send messages safely ---
    async def send_ws_message(msg_type: str, content: str):
        """Safely sends a JSON message over the WebSocket."""
        try:
            await websocket.send(json.dumps({"type": msg_type, "content": content}))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket closed while trying to send message.")
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}", exc_info=True)

    try:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message("status_message", f"Connected to backend (Agent Ready with LLM: {settings.ai_provider}).")
        await send_ws_message("monitor_log", f"[{timestamp}] New client connection: {websocket.remote_address}")

        async for message in websocket:
            logger.info(f"Received message: {message}")
            log_prefix = f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}]"
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                # --- USER MESSAGE -> Trigger Agent ---
                if message_type == "user_message":
                    await send_ws_message("monitor_log", f"{log_prefix} Received user task: {content}")
                    await send_ws_message("status_message", f"Acknowledged task: '{content[:60]}...'. Agent starting...")

                    # --- Run Agent Asynchronously and Stream Logs ---
                    try:
                        # Use astream_log for detailed intermediate steps
                        async for chunk in agent_executor.astream_log(
                            {"input": content},
                            include_names=["ChatGoogleGenerativeAI", "Ollama", "ShellTool"] # Specify components to log, adjust as needed
                        ):
                            # chunk is an Operation object from LogEntryPatch
                            # We can parse it to see actions, tool inputs/outputs etc.
                            # print(f"--- Agent Log Chunk ---")
                            # print(chunk)
                            # print("------")

                            # Send relevant parts to frontend
                            # This parsing logic can be complex depending on desired detail level
                            # Example: Send agent actions and tool outputs to monitor
                            for op in chunk.ops:
                                path = op.get("path")
                                value = op.get("value")

                                if isinstance(value, dict):
                                     # Log LLM Input/Output Chunks (can be verbose)
                                     # if path.startswith("/logs/ChatGoogleGenerativeAI") or path.startswith("/logs/Ollama"):
                                     #      # logger.debug(f"LLM Log: {path} = {value}")
                                     #      pass # Avoid sending raw LLM logs for now

                                     # Log Tool Start
                                     if path.endswith("/streamed_output_str") and "/logs/ShellTool/final_output" not in path:
                                         tool_input = value # Input to the tool
                                         await send_ws_message("monitor_log", f"{log_prefix} [Tool Start] Using ShellTool with input: {tool_input}")
                                         await send_ws_message("status_message", f"Running shell command...")

                                     # Log Tool Output/Observation
                                     elif path.endswith("/final_output") and "/logs/ShellTool" in path:
                                          # Check if value is a dict with 'output' key
                                          tool_output = value.get("output", str(value)) if isinstance(value, dict) else str(value)
                                          await send_ws_message("monitor_log", f"{log_prefix} [Tool Output] ShellTool returned: {tool_output.strip()}")
                                          await send_ws_message("status_message", "Shell command finished.")

                                     # Log Final Answer from Agent
                                     elif path == "/final_output":
                                          final_answer = value.get("output", str(value)) if isinstance(value, dict) else str(value)
                                          logger.info(f"Agent final answer: {final_answer}")
                                          await send_ws_message("agent_message", f"Final Answer: {final_answer}")
                                          await send_ws_message("status_message", "Task processing complete.")


                        # Add a final confirmation log after stream finishes
                        await send_ws_message("monitor_log", f"{log_prefix} Agent processing finished for task: {content}")

                    except Exception as e:
                        logger.error(f"Error during agent execution: {e}", exc_info=True)
                        await send_ws_message("monitor_log", f"{log_prefix} CRITICAL Error during agent execution: {e}")
                        await send_ws_message("status_message", "Error during task processing.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred while processing the task: {e}")


                # --- COMMAND EXECUTION (Direct - Keep for testing?) ---
                elif message_type == "run_command":
                    # Note: Agent should ideally handle commands via ShellTool now.
                    # Keep this for direct testing if desired, but use ShellTool via agent preferably.
                    command = data.get("command")
                    await send_ws_message("monitor_log", f"{log_prefix} Received direct 'run_command' (use agent preferably). Executing: {command}")
                    if command:
                        # We need a way to execute shell commands here now
                        # Option 1: Instantiate ShellTool here (less ideal)
                        # Option 2: Keep the old execute_shell_command helper (requires refactoring it back in or importing)
                        # Let's just log for now, as agent should handle this.
                         await send_ws_message("monitor_log", f"{log_prefix} Direct command execution via this message type is discouraged. Use the agent.")
                         await send_ws_message("status_message", "Direct command ignored. Please use agent task input.")
                    else:
                        await send_ws_message("monitor_log", f"{log_prefix} Error: Received 'run_command' with no command.")


                # --- OTHER MESSAGE TYPES ---
                elif message_type == "new_task" or message_type == "context_switch":
                     # Agent state is managed internally, just acknowledge context clear
                     await send_ws_message("monitor_log", f"{log_prefix} Received '{message_type}'. Ready for new task.")
                     await send_ws_message("status_message", "Ready for new task.")
                elif message_type == "action_command":
                     # This might be used later to trigger specific agent actions if needed
                     await send_ws_message("monitor_log", f"{log_prefix} Received action command: {data.get('command')} (Not implemented yet).")


                else: # Unknown message type
                     logger.warning(f"Unknown message type received: {message_type}")
                     await send_ws_message("monitor_log", f"{log_prefix} Received unknown message type: {message_type}")

            # ... (Error handling for message parsing remains the same) ...
            except json.JSONDecodeError: # ...
                 logger.error(f"Received non-JSON message: {message}", exc_info=True)
                 await send_ws_message("monitor_log", f"{log_prefix} Error: Received non-JSON message.")
            except Exception as e: # ...
                 logger.error(f"Error processing message: {e}", exc_info=True)
                 await send_ws_message("monitor_log", f"{log_prefix} Error processing message: {type(e).__name__} - {e}")

    # ... (Connection closed handling remains the same) ...
    except websockets.exceptions.ConnectionClosedOK: # ...
        logger.info(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e: # ...
        logger.warning(f"Connection closed with error: {websocket.remote_address} - {e}")
    except Exception as e: # ...
        logger.error(f"Unhandled error in handler for {websocket.remote_address}: {e}", exc_info=True)
    finally: # ...
        if websocket in connected_clients:
             connected_clients.remove(websocket)
        logger.info(f"Client removed: {websocket.remote_address}")


async def main():
    host = "localhost"
    port = 8765
    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        # Setup logging for when run directly
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
    except Exception as e:
        logger.critical(f"Server failed to start or encountered critical error: {e}", exc_info=True)

