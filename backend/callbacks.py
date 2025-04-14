# backend/callbacks.py
import logging
import datetime # Import datetime
from typing import Any, Dict, List, Optional, Union, Sequence
from uuid import UUID
import json
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult # Keep this if used, or remove if not
# *** ADDED IMPORT for BaseMessage ***
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish

logger = logging.getLogger(__name__)

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """Async Callback handler for streaming LangChain events over WebSocket."""

    def __init__(self, session_id: str, send_ws_message_func):
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        # Generate timestamp prefix once during init for consistency in logs from this handler instance
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        self.log_prefix = f"[{timestamp}][{self.session_id[:8]}]"
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Log when LLM starts."""
        pass # Keep it less verbose for now

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Handle new token stream from LLM - not typically used in agents directly."""
        pass

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Log when LLM ends."""
        pass

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log LLM errors."""
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        await self.send_ws_message("monitor_log", f"{self.log_prefix} [LLM Error] {error}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]], # Type hint uses BaseMessage now imported
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""
        pass

    # --- Tool Callbacks ---
    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Log when tool starts."""
        tool_name = serialized.get("name", "Unknown Tool")
        logger.info(f"[{self.session_id}] Agent starting tool: {tool_name} with input: {input_str}")
        # Update timestamp for this specific log
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{self.session_id[:8]}]"
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Start] Using '{tool_name}' with input: '{input_str}'")
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when tool ends."""
        logger.info(f"[{self.session_id}] Tool finished. Output length: {len(output)}")
        formatted_output = f"\n---\n{output.strip()}\n---"
        # Update timestamp for this specific log
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{self.session_id[:8]}]"
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Output] Tool returned:{formatted_output}")
        await self.send_ws_message("status_message", "Agent finished using tool.")

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log tool errors."""
        logger.error(f"[{self.session_id}] Tool Error: {error}", exc_info=True)
        # Update timestamp for this specific log
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        log_prefix = f"[{timestamp}][{self.session_id[:8]}]"
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Error] {error}")
        await self.send_ws_message("status_message", "Error occurred during tool execution.")

    # --- Agent Action/Finish Callbacks ---
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        pass

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        pass

