# backend/callbacks.py
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence
from uuid import UUID
import json

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish

logger = logging.getLogger(__name__)

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for streaming LangChain agent events
    (like tool usage and final answers) over a WebSocket connection
    and saving them to the database.
    """
    always_verbose: bool = True
    ignore_llm: bool = False
    ignore_chain: bool = True
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: callable, db_add_message_func: callable):
        """
        Initializes the callback handler.

        Args:
            session_id: The unique ID for the current WebSocket session.
            send_ws_message_func: An async function to send messages over WebSocket.
            db_add_message_func: An async function to save messages to the database.
        """
        super().__init__()
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func
        self.current_task_id: Optional[str] = None # Initialize task ID as None
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    # --- Method to update the current task ID ---
    def set_task_id(self, task_id: Optional[str]):
        """Updates the task ID the handler should associate messages with."""
        logger.info(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    # --- Helper to get log prefix ---
    def _get_log_prefix(self) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    # --- Helper to save message to DB (if task ID is set) ---
    async def _save_message(self, msg_type: str, content: str):
        if self.current_task_id:
            try:
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, content)
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback failed to save message (type: {msg_type}) to DB for task {self.current_task_id}: {e}")
        # else: logger.debug(f"[{self.session_id}] Message not saved to DB (no active task in callback).") # Optional debug

    # --- LLM Callbacks ---
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None: pass
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        logger.error(f"LLM Error: {error}", exc_info=True)
        await self.send_ws_message("monitor_log", f"{log_prefix} [LLM Error] {type(error).__name__}: {error}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self._save_message("error_llm", f"{type(error).__name__}: {error}")

    async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any) -> Any: pass

    # --- Tool Callbacks ---
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        tool_name = serialized.get("name", "Unknown Tool")
        logger.info(f"Agent starting tool: {tool_name} with input: {input_str}")
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Start] Using '{tool_name}' with input: '{input_str}'")
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")
        await self._save_message("tool_input", f"{tool_name}:::{input_str}") # Save tool input

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        logger.info(f"Tool finished. Output length: {len(output)}")
        monitor_output = output[:1000] + "..." if len(output) > 1000 else output
        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Output] Tool returned:{formatted_output}")
        await self.send_ws_message("status_message", "Agent finished using tool.")
        await self._save_message("tool_output", output) # Save full tool output

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        logger.error(f"Tool Error: {error}", exc_info=True)
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Error] {type(error).__name__}: {error}")
        await self.send_ws_message("status_message", "Error occurred during tool execution.")
        await self._save_message("tool_error", f"{type(error).__name__}: {error}")

    # --- Agent Finish Callback ---
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        logger.info(f"Agent Finish. Return values: {finish.return_values}")
        final_answer = finish.return_values.get("output", None)

        if isinstance(final_answer, str):
            await self._save_message("agent_finish", final_answer) # Save final answer to DB
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish] Sending final answer to UI.")
            logger.info(f"Attempting to send agent_message (Final Answer): {final_answer[:100]}...")
            await self.send_ws_message("agent_message", final_answer)
            logger.info(f"Sent agent_message (Final Answer).")
            await self.send_ws_message("status_message", "Task processing complete.")
        else:
            logger.warning(f"Could not parse final answer string from AgentFinish: {finish.return_values}")
            fallback_message = "Processing complete. See Monitor panel for execution details."
            await self._save_message("agent_finish_fallback", fallback_message) # Save fallback
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish] Could not parse final answer text. Sending fallback.")
            logger.info(f"Attempting to send agent_message (Fallback): {fallback_message}")
            await self.send_ws_message("agent_message", fallback_message)
            logger.info(f"Sent agent_message (Fallback).")
            await self.send_ws_message("status_message", "Task processing complete (check monitor).")

    # --- Other Callbacks (Keep as pass for now) ---
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None: pass
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any: pass
    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    # Add other on_ methods if needed (on_chain_start, etc.)

