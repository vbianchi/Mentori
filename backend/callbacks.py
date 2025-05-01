# backend/callbacks.py
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json
from pathlib import Path
import os
import re # Import regex module

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document

# Project Imports
from backend.config import settings
from backend.tools import TEXT_EXTENSIONS, get_task_workspace_path

logger = logging.getLogger(__name__)

# --- Define Custom Exception for Cancellation ---
class AgentCancelledException(Exception):
    """Custom exception to signal agent cancellation via callbacks."""
    pass
# ---------------------------------------------

# Define type hints
AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]

# File Server Constants
FILE_SERVER_CLIENT_HOST = settings.file_server_hostname
FILE_SERVER_PORT = 8766

class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for streaming LangChain agent events
    and saving them to the database. Logs artifact creation from write_file.
    Sends agent thoughts to the monitor panel.
    Checks for cancellation requests before LLM/Tool starts.
    """
    # Configuration for which callbacks to ignore/activate
    # Set these to False to activate the respective callback logs (can be verbose)
    always_verbose: bool = True # Set to True to enable custom logging via methods below
    ignore_llm: bool = False # *** MODIFIED: Need on_llm_start ***
    ignore_chain: bool = True
    ignore_agent: bool = False # We need on_agent_action and on_agent_finish
    ignore_retriever: bool = True
    ignore_chat_model: bool = False # *** MODIFIED: Need on_chat_model_start ***

    # *** MODIFIED: Accept session_data ***
    def __init__(self, session_id: str, send_ws_message_func: SendWSMessageFunc, db_add_message_func: AddMessageFunc, session_data_ref: Dict[str, Any]):
        super().__init__()
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func
        self.session_data = session_data_ref # Store reference to global session data
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
                # Ensure content is string before saving
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, str(content))
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {msg_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{msg_type}' to DB: current_task_id not set.")

    # --- Check Cancellation Helper ---
    def _check_cancellation(self, step_name: str):
        """Checks the cancellation flag and raises AgentCancelledException if set."""
        if self.session_id in self.session_data:
            if self.session_data[self.session_id].get('cancellation_requested', False):
                logger.warning(f"[{self.session_id}] Cancellation detected in callback before {step_name}. Raising AgentCancelledException.")
                raise AgentCancelledException("Cancellation requested by user.")
        else:
            # This shouldn't happen in normal operation
            logger.error(f"[{self.session_id}] Cannot check cancellation flag: Session data not found for session.")


    # --- LLM Callbacks ---
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Check for cancellation before starting LLM call."""
        try:
            self._check_cancellation("LLM execution")
        except AgentCancelledException:
            raise # Re-raise to stop the chain

        # Original logging (optional, can be kept or removed)
        # log_prefix = self._get_log_prefix()
        # logger.debug(f"{log_prefix} [LLM Start] Prompts: {prompts[:1]}...") # Log only first prompt for brevity

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        """Check for cancellation before starting Chat Model call."""
        try:
            self._check_cancellation("Chat Model execution")
        except AgentCancelledException:
            raise # Re-raise to stop the chain

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None: pass # Often too verbose
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None: pass

    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self._save_message("error_llm", error_content)

    # --- Chain Callbacks ---
    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None: pass

    # --- Tool Callbacks ---
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Check for cancellation before starting Tool call."""
        tool_name = serialized.get("name", "Unknown Tool")
        try:
            self._check_cancellation(f"Tool execution ('{tool_name}')")
        except AgentCancelledException:
            raise # Re-raise to stop the chain

        # Original logging
        log_prefix = self._get_log_prefix()
        # Truncate potentially long input strings for logging
        log_input = input_str[:500] + "..." if len(str(input_str)) > 500 else input_str
        log_content = f"[Tool Start] Using '{tool_name}' with input: '{log_input}'"
        logger.info(f"[{self.session_id}] {log_content}")
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", f"Agent using tool: {tool_name}...")
        await self._save_message("tool_input", f"{tool_name}:::{log_input}") # Save potentially truncated input

    async def on_tool_end(self, output: str, name: str = "Unknown Tool", **kwargs: Any) -> None:
        """ Run when tool ends successfully. """
        log_prefix = self._get_log_prefix()
        output_str = str(output) # Ensure output is string
        logger.info(f"[{self.session_id}] Tool '{name}' finished. Output length: {len(output_str)}")
        monitor_output = output_str # Default monitor output

        # --- Artifact Logging for write_file ---
        success_prefix = "SUCCESS::write_file:::"
        if name == "write_file" and output_str.startswith(success_prefix):
            try:
                if len(output_str) > len(success_prefix):
                    relative_path_str = output_str[len(success_prefix):]
                    logger.info(f"[{self.session_id}] Detected successful write_file: '{relative_path_str}'")
                    await self._save_message("artifact_generated", relative_path_str)
                    await self.send_ws_message("monitor_log", f"{log_prefix} [ARTIFACT_GENERATED] {relative_path_str} (via {name})")
                    monitor_output = f"Successfully wrote file: '{relative_path_str}'"
                else:
                    raise ValueError("Output string matched prefix but was not longer than prefix.")
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
                monitor_output = output_str # Fallback if parsing failed
        else:
            # Truncate long outputs for monitor display if not write_file success
            monitor_output = output_str[:1000] + "..." if len(output_str) > 1000 else output_str

        # Format and send monitor log entry
        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        log_content = f"[Tool Output] Tool '{name}' returned:{formatted_output}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("status_message", f"Agent finished using tool: {name}.")
        # Save the full original output to the database
        await self._save_message("tool_output", output_str)

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "Unknown Tool", **kwargs: Any) -> None:
        # *** ADDED: Check if it's our custom cancellation exception ***
        if isinstance(error, AgentCancelledException):
             logger.warning(f"[{self.session_id}] Tool '{name}' execution cancelled by AgentCancelledException.")
             # Optionally send a specific monitor log for this?
             # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Tool Cancelled] Tool '{name}' stopped due to user request.")
             # Re-raise the exception so the agent execution stops
             raise error

        # Original error handling
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        error_str = str(error)
        logger.error(f"[{self.session_id}] Tool '{name}' Error: {error_str}", exc_info=True)
        error_content = f"[Tool Error] Tool '{name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", f"Error occurred during tool execution: {name}.")
        await self._save_message("error_tool", f"{name}::{error_type_name}::{error_str}")

    # --- Agent Action/Finish Callbacks ---

    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action, send thought to monitor."""
        log_prefix = self._get_log_prefix()
        # Extract thought from the action's log string
        thought = ""
        if action.log:
            log_lines = action.log.strip().split('\n')
            thought_lines = []
            # Iterate backwards to find the last 'Thought:' block before the 'Action:'
            in_thought = False
            for line in reversed(log_lines):
                 if line.strip().startswith("Action:"):
                     in_thought = False # Stop if we hit Action before Thought
                     continue
                 if line.strip().startswith("Thought:"):
                     in_thought = True
                     # Handle potential empty thought after colon
                     thought_part = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                     thought_lines.append(thought_part)
                     break # Found the start of the last thought
                 if in_thought:
                     thought_lines.append(line) # Add subsequent lines of the thought

            if thought_lines:
                 thought = "\n".join(reversed(thought_lines)).strip() # Join lines in correct order

        if thought:
            logger.debug(f"[{self.session_id}] Extracted thought (Action): {thought}")
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Thought (Action)] {thought}")
            await self._save_message("agent_thought_action", thought)
        else:
            logger.warning(f"[{self.session_id}] Could not extract thought from agent action log: {action.log}")
            # Optionally send the raw log if thought extraction fails
            # await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Action Log] {action.log}")

        # Note: on_tool_start will log the actual tool usage immediately after this

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent finish, send final thought to monitor and answer to chat."""
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Log: {finish.log}") # Log the full finish log

        # --- Extract and Send Final Thought ---
        final_thought = ""
        if finish.log:
            # Try to find the last "Thought:" block before "Final Answer:"
            # Use re.S (DOTALL) to make '.' match newlines
            match = re.search(r"Thought:(.*?)(?=Final Answer:)", finish.log, re.S | re.IGNORECASE)
            if match:
                final_thought = match.group(1).strip()
                logger.debug(f"[{self.session_id}] Extracted final thought: {final_thought}")
                await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Thought (Final)] {final_thought}")
                await self._save_message("agent_thought_final", final_thought)
            else:
                logger.warning(f"[{self.session_id}] Could not extract final thought from agent finish log.")
                # Optionally send the raw log if thought extraction fails
                # await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish Log (No Thought Extracted)] {finish.log}")
        # ------------------------------------

        # --- Process Final Answer ---
        final_answer = finish.return_values.get("output", None)
        if isinstance(final_answer, str):
            await self._save_message("agent_finish", final_answer)
            log_content = f"[Agent Finish] Sending final answer to UI." # Keep this concise
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

    # --- Other Callbacks (Keep minimal if not used) ---
    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any: pass
    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any: pass # type: ignore
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any: pass

