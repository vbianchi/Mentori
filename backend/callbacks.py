# backend/callbacks.py
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
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
    always_verbose: bool = True
    ignore_llm: bool = False
    ignore_chain: bool = True
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: callable, db_add_message_func: AddMessageFunc):
        super().__init__()
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func
        self.current_task_id: Optional[str] = None
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def set_task_id(self, task_id: Optional[str]):
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    async def _save_message(self, msg_type: str, content: str):
        if self.current_task_id:
            try: await self.db_add_message(self.current_task_id, self.session_id, msg_type, content)
            except Exception as e: logger.error(f"[{self.session_id}] Callback DB save error: {e}")

    # --- LLM Callbacks ---
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None: pass
    # *** REMOVED on_llm_new_token ***
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self._save_message("error_llm", error_content)

    async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any) -> Any: pass

    # --- Tool Callbacks ---
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        tool_name = serialized.get("name", "Unknown Tool")
        log_content = f"[Tool Start] Using '{tool_name}' with input: '{input_str}'"
        logger.info(f"[{self.session_id}] {log_content}")
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")
        await self._save_message("tool_input", f"{tool_name}:::{input_str}")

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Tool finished. Output length: {len(output)}")
        monitor_output = output[:1000] + "..." if len(output) > 1000 else output
        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        log_content = f"[Tool Output] Tool returned:{formatted_output}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", "Agent finished using tool.")
        await self._save_message("tool_output", output)

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] Tool Error: {error}", exc_info=True)
        error_content = f"[Tool Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during tool execution.")
        await self._save_message("error_tool", error_content)

    # --- Agent Finish Callback ---
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end. Saves answer, sends final answer AND status to UI."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Return values: {finish.return_values}")
        final_answer = finish.return_values.get("output", None)

        if isinstance(final_answer, str):
            await self._save_message("agent_finish", final_answer) # Save final answer to DB
            log_content = f"[Agent Finish] Sending final answer to UI."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}") # Log finish event
            # *** RESTORED sending agent_message to UI ***
            logger.info(f"Attempting to send agent_message (Final Answer): {final_answer[:100]}...")
            await self.send_ws_message("agent_message", final_answer)
            logger.info(f"Sent agent_message (Final Answer).")
            await self.send_ws_message("status_message", "Task processing complete.") # Update status
        else:
            logger.warning(f"[{self.session_id}] Could not parse final answer string from AgentFinish: {finish.return_values}")
            fallback_message = "Processing complete. See Monitor panel for execution details."
            await self._save_message("agent_finish_fallback", fallback_message) # Save fallback
            log_content = "[Agent Finish] Could not parse final answer text. Sending fallback."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}") # Log fallback event
            # *** RESTORED sending agent_message to UI ***
            logger.info(f"Attempting to send agent_message (Fallback): {fallback_message}")
            await self.send_ws_message("agent_message", fallback_message)
            logger.info(f"Sent agent_message (Fallback).")
            await self.send_ws_message("status_message", "Task processing complete (check monitor).") # Update status

    # --- Other Callbacks ---
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None: pass
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any: pass
    async def on_text(self, text: str, **kwargs: Any) -> Any: pass

