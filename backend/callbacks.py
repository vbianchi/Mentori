# backend/callbacks.py
import logging
import datetime # Import datetime
from typing import Any, Dict, List, Optional, Union, Sequence
from uuid import UUID
import json

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage # Correct import location
from langchain_core.agents import AgentAction, AgentFinish

logger = logging.getLogger(__name__)

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for streaming LangChain agent events
    (like tool usage and final answers) over a WebSocket connection.
    """

    def __init__(self, session_id: str, send_ws_message_func: callable):
        """
        Initializes the callback handler.

        Args:
            session_id: The unique ID for the current WebSocket session.
            send_ws_message_func: An async function (like the one defined in the handler)
                                  that takes (message_type: str, content: str) and sends
                                  it over the correct WebSocket.
        """
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def _get_log_prefix(self) -> str:
        """Generates a standard log prefix with current timestamp and session ID."""
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    # --- LLM Callbacks (Optional Logging) ---
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        # log_prefix = self._get_log_prefix()
        # logger.debug(f"{log_prefix} LLM Start: {prompts}")
        # await self.send_ws_message("monitor_log", f"{log_prefix} [LLM Start] Calling LLM...")
        pass # Keep monitor clean for now

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log LLM errors."""
        log_prefix = self._get_log_prefix()
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        await self.send_ws_message("monitor_log", f"{log_prefix} [LLM Error] {error}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
         # log_prefix = self._get_log_prefix()
         # logger.debug(f"{log_prefix} Chat Model Start.")
         # await self.send_ws_message("monitor_log", f"{log_prefix} [Chat LLM Start] Calling Chat Model...")
         pass # Keep monitor clean

    # --- Tool Callbacks (Essential for Monitor Panel) ---
    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Log when tool starts, send to monitor."""
        log_prefix = self._get_log_prefix()
        tool_name = serialized.get("name", "Unknown Tool")
        logger.info(f"[{self.session_id}] Agent starting tool: {tool_name} with input: {input_str}")
        # Send tool start info to frontend monitor
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Start] Using '{tool_name}' with input: '{input_str}'")
        # Update status in chat panel
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when tool ends, send output to monitor."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Tool finished. Output length: {len(output)}")
        # Format output nicely for the monitor log
        formatted_output = f"\n---\n{output.strip()}\n---"
        # Send tool output to frontend monitor
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Output] Tool returned:{formatted_output}")
        # Update status in chat panel
        await self.send_ws_message("status_message", "Agent finished using tool.")

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Log tool errors."""
        log_prefix = self._get_log_prefix()
        logger.error(f"[{self.session_id}] Tool Error: {error}", exc_info=True)
        # Send tool error info to frontend monitor
        await self.send_ws_message("monitor_log", f"{log_prefix} [Tool Error] {error}")
        # Update status in chat panel
        await self.send_ws_message("status_message", "Error occurred during tool execution.")

    # --- Agent Finish Callback (Essential for Chat Panel) ---
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end, sending the final answer to chat."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Return values: {finish.return_values}")
        # Extract the final answer text
        final_answer = finish.return_values.get("output", None)

        if isinstance(final_answer, str):
            # Send final answer to monitor log for record
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish] Sending final answer to UI.")
            # Send final answer to chat panel
            await self.send_ws_message("agent_message", final_answer)
            # Update status in chat panel
            await self.send_ws_message("status_message", "Task processing complete.")
        else:
            # Fallback if parsing fails
            logger.warning(f"[{self.session_id}] Could not parse final answer string from AgentFinish: {finish.return_values}")
            fallback_message = "Processing complete. See Monitor panel for execution details."
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish] Could not parse final answer text. Sending fallback.")
            await self.send_ws_message("agent_message", fallback_message)
            await self.send_ws_message("status_message", "Task processing complete (check monitor).")