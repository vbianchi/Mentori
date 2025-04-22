# backend/callbacks.py
import logging
import datetime # Import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine # Import Callable, Coroutine
from uuid import UUID
import json

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage # Correct import location
from langchain_core.agents import AgentAction, AgentFinish

logger = logging.getLogger(__name__)

# Define the type hint for the async add_message function expected from db_utils
AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for streaming LangChain agent events
    (like tool usage and final answers) over a WebSocket connection
    and saving them to the database.
    """
    # Callback properties control which methods are called by LangChain.
    always_verbose: bool = True # Set True if you want verbose logging from handler itself
    ignore_llm: bool = False
    ignore_chain: bool = True # Often too verbose for UI/DB
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: callable, db_add_message_func: AddMessageFunc):
        """
        Initializes the callback handler.

        Args:
            session_id: The unique ID for the current WebSocket session.
            send_ws_message_func: An async function to send messages over the WebSocket.
            db_add_message_func: An async function to save messages to the database.
        """
        super().__init__() # Initialize the base handler
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func # Store the async function for saving
        self.current_task_id: Optional[str] = None # Track the active task ID for DB saving
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    # Method to update the current task ID context (called from server.py)
    def set_task_id(self, task_id: Optional[str]):
        """Updates the task ID currently associated with this handler instance."""
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        """Generates a standard log prefix with current timestamp and session ID."""
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        # Use shortened session ID for brevity in logs sent to UI/DB
        return f"[{timestamp}][{self.session_id[:8]}]"

    # --- Helper to save message to DB ---
    async def _save_message(self, msg_type: str, content: str):
        """Saves a message to the database if a task context is active."""
        if self.current_task_id:
            try:
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, content)
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback failed to save message (type: {msg_type}) to DB for task {self.current_task_id}: {e}")
        # else: logger.debug(f"[{self.session_id}] Message not saved to DB (no active task in callback).") # Optional debug


    # --- LLM Callbacks ---
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        # Optional: Log LLM start or save prompt
        pass

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log LLM errors to UI monitor and DB."""
        log_prefix = self._get_log_prefix()
        error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True) # Log full traceback to console
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self._save_message("error_llm", error_content) # Save error to DB

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        # Optional: Log chat model start
        pass

    # --- Tool Callbacks ---
    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Log when tool starts to UI monitor and DB."""
        log_prefix = self._get_log_prefix()
        tool_name = serialized.get("name", "Unknown Tool")
        log_content = f"[Tool Start] Using '{tool_name}' with input: '{input_str}'"
        logger.info(f"[{self.session_id}] {log_content}") # Log to backend console
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}") # Send to UI monitor
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...") # Send to UI status
        # Save tool start event to DB
        await self._save_message("tool_input", f"{tool_name}:::{input_str}")

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when tool ends to UI monitor and DB."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Tool finished. Output length: {len(output)}")
        # Truncate potentially long output for UI monitor display
        monitor_output = output[:1000] + "..." if len(output) > 1000 else output
        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        log_content = f"[Tool Output] Tool returned:{formatted_output}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}") # Send formatted to UI monitor
        await self.send_ws_message("status_message", "Agent finished using tool.") # Send to UI status
        # Save full tool output to DB
        await self._save_message("tool_output", output)

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log tool errors to UI monitor and DB."""
        log_prefix = self._get_log_prefix()
        error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] Tool Error: {error}", exc_info=True)
        error_content = f"[Tool Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}") # Send to UI monitor
        await self.send_ws_message("status_message", "Error occurred during tool execution.") # Send to UI status
        # Save tool error to DB
        await self._save_message("error_tool", error_content)

    # --- Agent Finish Callback ---
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end, sending the final answer to chat and saving to DB."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Return values: {finish.return_values}")
        # Extract the final answer text
        final_answer = finish.return_values.get("output", None)

        if isinstance(final_answer, str):
            # Save final answer to DB FIRST
            await self._save_message("agent_finish", final_answer)
            # Log that we are sending the answer
            log_content = f"[Agent Finish] Sending final answer to UI."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
            # *** Send final answer to chat panel ***
            logger.info(f"Attempting to send agent_message (Final Answer): {final_answer[:100]}...")
            await self.send_ws_message("agent_message", final_answer)
            logger.info(f"Sent agent_message (Final Answer).")
            # Update status in chat panel
            await self.send_ws_message("status_message", "Task processing complete.")
        else:
            # Fallback if parsing fails
            logger.warning(f"[{self.session_id}] Could not parse final answer string from AgentFinish: {finish.return_values}")
            fallback_message = "Processing complete. See Monitor panel for execution details."
            await self._save_message("agent_finish_fallback", fallback_message) # Save fallback
            log_content = "[Agent Finish] Could not parse final answer text. Sending fallback."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
            # Send fallback answer to chat panel
            logger.info(f"Attempting to send agent_message (Fallback): {fallback_message}")
            await self.send_ws_message("agent_message", fallback_message)
            logger.info(f"Sent agent_message (Fallback).")
            # Update status in chat panel
            await self.send_ws_message("status_message", "Task processing complete (check monitor).")

    # --- Other Callbacks (Keep as pass for now) ---
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None: pass
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any: pass
    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    # Add other on_ methods if needed (on_chain_start, on_retriever_start etc.)

