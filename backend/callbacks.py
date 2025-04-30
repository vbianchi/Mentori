# backend/callbacks.py
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json
from pathlib import Path
import os
import re

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish

# Project Imports
# *** MODIFIED: Import settings ***
from backend.config import settings # Import the loaded settings instance
from backend.tools import TEXT_EXTENSIONS, get_task_workspace_path

logger = logging.getLogger(__name__)

# Define type hints
AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]

# --- File Server Constants (Now primarily for logging/reference, hostname from settings) ---
# *** MODIFIED: Use hostname from settings ***
FILE_SERVER_CLIENT_HOST = settings.file_server_hostname
FILE_SERVER_PORT = 8766

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for streaming LangChain agent events
    and saving them to the database. Logs artifact creation from write_file.
    """
    always_verbose: bool = True
    ignore_llm: bool = False
    ignore_chain: bool = True
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: SendWSMessageFunc, db_add_message_func: AddMessageFunc):
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
        """Helper to save messages to DB, requires current_task_id to be set."""
        if self.current_task_id:
            try:
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, content)
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {msg_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{msg_type}' to DB: current_task_id not set.")

    # --- LLM Callbacks ---
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None: pass
    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self._save_message("error_llm", error_content)

    async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any) -> Any: pass

    # --- Tool Callbacks ---
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); tool_name = serialized.get("name", "Unknown Tool")
        log_input = input_str[:500] + "..." if len(input_str) > 500 else input_str
        log_content = f"[Tool Start] Using '{tool_name}' with input: '{log_input}'"
        logger.info(f"[{self.session_id}] {log_content}")
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")
        await self._save_message("tool_input", f"{tool_name}:::{log_input}")

    async def on_tool_end(self, output: str, name: str = "Unknown Tool", **kwargs: Any) -> None:
        """
        Run when tool ends successfully. Handles general logging and
        logs explicit artifact creation for 'write_file'.
        """
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Tool '{name}' finished. Output length: {len(output)}")
        monitor_output = output # Default monitor output

        # --- Artifact Logging for write_file ---
        success_prefix = "SUCCESS::write_file:::"
        if name == "write_file" and output.startswith(success_prefix):
            try:
                if len(output) > len(success_prefix):
                    relative_path_str = output[len(success_prefix):]
                    logger.info(f"[{self.session_id}] Detected successful write_file: '{relative_path_str}'")
                    # Save artifact generation event to DB
                    await self._save_message("artifact_generated", relative_path_str)
                    # Log to monitor
                    await self.send_ws_message("monitor_log", f"{log_prefix} [ARTIFACT_GENERATED] {relative_path_str} (via {name})")
                    # Modify output message shown in monitor log for clarity
                    monitor_output = f"Successfully wrote file: '{relative_path_str}'"
                else:
                    raise ValueError("Output string matched prefix but was not longer than prefix.")
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output}': {parse_err}", exc_info=True)
                monitor_output = output # Fallback if parsing failed
        else:
            # Truncate long outputs for monitor display if not write_file success
            monitor_output = output[:1000] + "..." if len(output) > 1000 else output

        # Format and send monitor log entry using the potentially modified monitor_output
        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        log_content = f"[Tool Output] Tool '{name}' returned:{formatted_output}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", f"Agent finished using tool: {name}.")
        # Save the full original output to the database
        await self._save_message("tool_output", output)

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "Unknown Tool", **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] Tool '{name}' Error: {error}", exc_info=True)
        error_content = f"[Tool Error] Tool '{name}' failed: {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", f"Error occurred during tool execution: {name}.")
        await self._save_message("error_tool", f"{name}::{error_type_name}::{error}")

    # --- Agent Finish Callback ---
    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Return values: {finish.return_values}")
        final_answer = finish.return_values.get("output", None)
        if isinstance(final_answer, str):
            await self._save_message("agent_finish", final_answer)
            log_content = f"[Agent Finish] Sending final answer to UI."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
            logger.info(f"[{self.session_id}] Attempting to send agent_message (Final Answer): {final_answer[:100]}...")
            await self.send_ws_message("agent_message", final_answer)
            logger.info(f"[{self.session_id}] Sent agent_message (Final Answer).")
            await self.send_ws_message("status_message", "Task processing complete.")
        else:
            logger.warning(f"[{self.session_id}] Could not parse final answer string from AgentFinish: {finish.return_values}")
            fallback_message = "Processing complete. See Monitor panel for execution details."
            await self._save_message("agent_finish_fallback", fallback_message)
            log_content = "[Agent Finish] Could not parse final answer text. Sending fallback."
            await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
            logger.info(f"[{self.session_id}] Attempting to send agent_message (Fallback): {fallback_message}")
            await self.send_ws_message("agent_message", fallback_message)
            logger.info(f"[{self.session_id}] Sent agent_message (Fallback).")
            await self.send_ws_message("status_message", "Task processing complete (check monitor).")

    # --- Other Callbacks ---
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None: pass
    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any: pass
    async def on_text(self, text: str, **kwargs: Any) -> Any: pass