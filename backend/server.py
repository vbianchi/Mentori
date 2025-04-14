# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import uuid # To generate unique IDs for sessions

# --- LangChain Imports ---
from langchain.agents import AgentExecutor
from langchain.callbacks.base import AsyncCallbackHandler
# Import a specific Memory type
from langchain.memory import ConversationBufferWindowMemory
# -------------------------

# --- Project Imports ---
from backend.config import load_settings, Settings
from backend.llm_setup import get_llm
from backend.tools import agent_tools
# Agent creation function now needs LLM, tools, AND memory
from backend.agent import create_agent_executor
# ----------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Settings and Initialize LLM (at startup) ---
# Keep LLM initialization global as it's usually stateless
try:
    settings: Settings = load_settings()
    llm = get_llm(settings)
    logger.info("Base LLM initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Failed during LLM setup: {e}", exc_info=True)
    exit(1)

connected_clients = {} # Store clients by unique ID
# Store memory and agent instances per connection ID
# This ensures conversations are isolated
session_data = {}

# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    # Generate a unique ID for this connection/session
    session_id = str(uuid.uuid4())
    logger.info(f"Client connected from {websocket.remote_address}. Assigning Session ID: {session_id}")
    connected_clients[session_id] = websocket

    # --- Create Session-Specific Memory and Agent ---
    try:
        # Create memory for this session (k=5 remembers last 5 turns)
        memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history", # Must match the key expected by the prompt
            input_key="input",        # Must match the key used for user input
            output_key="output"       # Must match the key used for agent output
            # return_messages=True # Set True if using Chat specific prompt templates/models that need Message objects
            )
        logger.info(f"[{session_id}] Created ConversationBufferWindowMemory (k=5)")

        # Create agent executor for this session, passing the session's memory
        agent_executor: AgentExecutor = create_agent_executor(llm, agent_tools, memory)
        logger.info(f"[{session_id}] Created AgentExecutor with session memory.")

        session_data[session_id] = {"memory": memory, "agent_executor": agent_executor}
    except Exception as e:
        logger.error(f"[{session_id}] Failed to create agent/memory for session: {e}", exc_info=True)
        # Close connection if agent setup fails
        await websocket.close(code=1011, reason="Agent setup failed")
        del connected_clients[session_id] # Clean up client entry
        return # End handler for this connection

    # --- Helper to send messages safely ---
    async def send_ws_message(msg_type: str, content: str):
        # ... (send_ws_message remains the same) ...
        try:
            await websocket.send(json.dumps({"type": msg_type, "content": content}))
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"[{session_id}] WebSocket closed while trying to send message.")
        except Exception as e:
            logger.error(f"[{session_id}] Error sending WebSocket message: {e}", exc_info=True)


    try:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await send_ws_message("status_message", f"Connected (Session: {session_id[:8]}...). Agent Ready with LLM: {settings.ai_provider}.")
        await send_ws_message("monitor_log", f"[{timestamp}] New client connection: {websocket.remote_address} (Session: {session_id})")

        async for message in websocket:
            logger.info(f"[{session_id}] Received message: {message}")
            log_prefix = f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}][{session_id[:8]}]"
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                # --- USER MESSAGE -> Trigger Agent ---
                if message_type == "user_message":
                    await send_ws_message("monitor_log", f"{log_prefix} Received user input: {content}")
                    await send_ws_message("status_message", f"Processing input: '{content[:60]}...'")

                    # Get the agent executor for this session
                    current_agent_executor = session_data[session_id]["agent_executor"]

                    # --- Run Agent Asynchronously and Stream Logs ---
                    try:
                        final_answer = None # Variable to store the final answer if found
                        # Use astream_log, LangChain automatically uses the memory object
                        async for chunk in current_agent_executor.astream_log(
                            {"input": content}, # Only 'input' is needed here
                            include_names=["ChatGoogleGenerativeAI", "Ollama", "ShellTool"]
                        ):
                            # --- Stream Parsing Logic (mostly the same) ---
                            for op in chunk.ops:
                                path = op.get("path")
                                value = op.get("value")

                                if isinstance(value, dict):
                                     # Log Tool Start
                                     if path.endswith("/streamed_output_str") and "/logs/ShellTool/final_output" not in path:
                                         tool_input = value
                                         await send_ws_message("monitor_log", f"{log_prefix} [Tool Start] Using ShellTool with input: {tool_input}")
                                         await send_ws_message("status_message", f"Running shell command...")

                                     # Log Tool Output/Observation
                                     elif path.endswith("/final_output") and "/logs/ShellTool" in path:
                                          tool_output = value.get("output", str(value)) if isinstance(value, dict) else str(value)
                                          await send_ws_message("monitor_log", f"{log_prefix} [Tool Output] ShellTool returned: {tool_output.strip()}")
                                          await send_ws_message("status_message", "Shell command finished.")

                                     # Log Final Answer from Agent
                                     elif path == "/final_output":
                                          # Ensure we capture the correct final answer structure
                                          if isinstance(value, dict) and "output" in value:
                                               final_answer = value["output"]
                                          elif isinstance(value, str): # Fallback if it's just a string
                                               final_answer = value
                                          else: # Handle unexpected structure
                                               final_answer = str(value)

                                          logger.info(f"[{session_id}] Agent final answer received: {final_answer}")
                                          await send_ws_message("agent_message", f"Final Answer: {final_answer}")
                                          await send_ws_message("status_message", "Task processing complete.")


                        # --- Ensure Memory is Updated (LangChain AgentExecutor usually handles this, but explicit can be safer) ---
                        # Note: Normally, just running the agent executor with memory attached *should* update it.
                        # If issues arise, you might need manual saving (less common now).
                        # E.g., session_memory.save_context({"input": content}, {"output": final_answer or "No final answer found"})
                        # logger.info(f"[{session_id}] Memory updated.")

                        await send_ws_message("monitor_log", f"{log_prefix} Agent processing finished.")
                        if final_answer is None:
                             logger.warning(f"[{session_id}] Agent finished but no '/final_output' detected in stream.")
                             await send_ws_message("status_message", "Agent finished, but final answer structure unclear.")
                             await send_ws_message("agent_message", "(Agent finished, but no explicit final answer was parsed from the stream.)")


                    except Exception as e:
                        # ... (Handle agent execution error) ...
                        logger.error(f"[{session_id}] Error during agent execution: {e}", exc_info=True)
                        await send_ws_message("monitor_log", f"{log_prefix} CRITICAL Error during agent execution: {e}")
                        await send_ws_message("status_message", "Error during task processing.")
                        await send_ws_message("agent_message", f"Sorry, an internal error occurred: {e}")


                # --- OTHER MESSAGE TYPES ---
                elif message_type == "new_task" or message_type == "context_switch":
                     # Clear the memory for this session when a new task/context starts
                     if session_id in session_data:
                          session_data[session_id]["memory"].clear()
                          logger.info(f"[{session_id}] Cleared conversation memory due to '{message_type}'.")
                     await send_ws_message("monitor_log", f"{log_prefix} Received '{message_type}'. Memory cleared. Ready for new task.")
                     await send_ws_message("status_message", "Memory cleared. Ready for new task.")
                # ... (action_command, unknown type logic remains the same) ...
                elif message_type == "action_command":
                     await send_ws_message("monitor_log", f"{log_prefix} Received action command: {data.get('command')} (Not implemented yet).")
                else:
                     logger.warning(f"[{session_id}] Unknown message type received: {message_type}")
                     await send_ws_message("monitor_log", f"{log_prefix} Received unknown message type: {message_type}")

            # ... (Error handling for message parsing remains the same) ...
            except json.JSONDecodeError: # ...
                 logger.error(f"[{session_id}] Received non-JSON message: {message}", exc_info=True)
                 await send_ws_message("monitor_log", f"{log_prefix} Error: Received non-JSON message.")
            except Exception as e: # ...
                 logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
                 await send_ws_message("monitor_log", f"{log_prefix} Error processing message: {type(e).__name__} - {e}")

    # ... (Connection closed handling) ...
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client disconnected: {websocket.remote_address} (Session: {session_id})")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"Connection closed with error: {websocket.remote_address} (Session: {session_id}) - {e}")
    except Exception as e:
        logger.error(f"Unhandled error in handler for {websocket.remote_address} (Session: {session_id}): {e}", exc_info=True)
    finally:
        # --- Clean up session data on disconnect ---
        if session_id in connected_clients:
            del connected_clients[session_id]
        if session_id in session_data:
            del session_data[session_id]
            logger.info(f"Cleaned up session data for {session_id}")
        logger.info(f"Client removed: {websocket.remote_address} (Session: {session_id})")


async def main():
    # ... (main function remains the same) ...
    host = "localhost"
    port = 8765
    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    # ... (__main__ block remains the same) ...
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
    except Exception as e:
        logger.critical(f"Server failed to start or encountered critical error: {e}", exc_info=True)

