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
from langchain_core.outputs import LLMResult, ChatGenerationChunk, GenerationChunk
from langchain_core.messages import BaseMessage, AIMessageChunk
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
    Async Callback handler for LangChain agent events.
    - Sends thinking status updates to the chat UI.
    - Sends final agent messages to the chat UI.
    - Sends monitor logs for all steps.
    - Extracts and sends LLM token usage.
    - Handles cancellation requests.
    - Logs artifact creation from write_file and triggers UI refresh.
    - Saves relevant events to the database.
    """
    always_verbose: bool = True
    ignore_llm: bool = False
    ignore_chain: bool = True
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: SendWSMessageFunc, db_add_message_func: AddMessageFunc, session_data_ref: Dict[str, Any]):
        super().__init__()
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func
        self.session_data = session_data_ref # Reference to the main session_data dict
        self.current_task_id: Optional[str] = None # Set by set_task_id from server
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def set_task_id(self, task_id: Optional[str]):
        """Sets the current task ID for this callback handler."""
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        """Returns a standardized log prefix with timestamp and session ID."""
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    async def _save_message(self, msg_type: str, content: str):
        """Saves a message to the database if a task ID is set."""
        if self.current_task_id:
            try:
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, str(content))
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {msg_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{msg_type}' to DB: current_task_id not set.")

    def _check_cancellation(self, step_name: str):
        """Checks if cancellation has been requested and raises AgentCancelledException if so."""
        current_session_specific_data = self.session_data.get(self.session_id)
        if current_session_specific_data:
            if current_session_specific_data.get('cancellation_requested', False):
                logger.warning(f"[{self.session_id}] Cancellation detected in callback before {step_name}. Raising AgentCancelledException.")
                raise AgentCancelledException("Cancellation requested by user.")
        else:
            logger.error(f"[{self.session_id}] Cannot check cancellation flag: Session data not found for session in shared dict.")


    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try:
            self._check_cancellation("LLM execution")
        except AgentCancelledException:
            raise
        # logger.debug(f"[{self.session_id}] on_llm_start. Prompts: {prompts[:1]}...")


    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        try:
            self._check_cancellation("Chat Model execution")
        except AgentCancelledException:
            raise
        # logger.debug(f"[{self.session_id}] on_chat_model_start. Messages: {messages}")

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Handle new token from LLM, if streaming is implemented for thoughts/final answer."""
        pass

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        # ... (existing content - no changes needed) ...
        log_prefix = self._get_log_prefix()
        logger.debug(f"[{self.session_id}] on_llm_end received response. Run ID: {run_id}")
        logger.debug(f"[{self.session_id}] LLMResult object: {response}")

        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        total_tokens: Optional[int] = None
        model_name: str = "unknown_model"
        source_for_tokens = "unknown"

        try:
            if response.llm_output and isinstance(response.llm_output, dict):
                llm_output_data = response.llm_output
                source_for_tokens = "llm_output"
                logger.debug(f"[{self.session_id}] Trying to extract tokens from response.llm_output: {llm_output_data}")

                model_name = llm_output_data.get('model_name', llm_output_data.get('model', model_name))

                if 'token_usage' in llm_output_data and isinstance(llm_output_data['token_usage'], dict):
                    usage_dict = llm_output_data['token_usage']
                    input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens'))
                    output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens'))
                    total_tokens = usage_dict.get('total_tokens')
                    logger.info(f"[{self.session_id}] Tokens from llm_output.token_usage: In={input_tokens}, Out={output_tokens}, Total={total_tokens}")
                elif 'usage_metadata' in llm_output_data and isinstance(llm_output_data['usage_metadata'], dict): # Gemini
                    usage_dict = llm_output_data['usage_metadata']
                    input_tokens = usage_dict.get('prompt_token_count')
                    output_tokens = usage_dict.get('candidates_token_count')
                    total_tokens = usage_dict.get('total_token_count')
                    logger.info(f"[{self.session_id}] Tokens from llm_output.usage_metadata (Gemini): In={input_tokens}, Out={output_tokens}, Total={total_tokens}")
                elif 'eval_count' in llm_output_data: # Ollama
                    output_tokens = llm_output_data.get('eval_count')
                    input_tokens = llm_output_data.get('prompt_eval_count')
                    logger.info(f"[{self.session_id}] Tokens from llm_output (Ollama): Eval(Out)={output_tokens}, PromptEval(In)={input_tokens}")

            if (input_tokens is None and output_tokens is None) and response.generations:
                logger.debug(f"[{self.session_id}] llm_output was None or no tokens found. Trying response.generations.")
                for gen_list in response.generations:
                    if not gen_list: continue
                    first_gen = gen_list[0]
                    source_for_tokens = "generations"

                    if hasattr(first_gen, 'message') and hasattr(first_gen.message, 'usage_metadata') and first_gen.message.usage_metadata:
                        usage_metadata = first_gen.message.usage_metadata
                        if isinstance(usage_metadata, dict):
                            input_tokens = usage_metadata.get('prompt_token_count', usage_metadata.get('input_tokens'))
                            output_tokens = usage_metadata.get('candidates_token_count', usage_metadata.get('output_tokens'))
                            total_tokens = usage_metadata.get('total_token_count')
                            if hasattr(first_gen.message, 'response_metadata') and isinstance(first_gen.message.response_metadata, dict):
                                model_name = first_gen.message.response_metadata.get('model_name', model_name)
                            if not model_name or model_name == "unknown_model":
                                model_name = getattr(first_gen, 'generation_info', {}).get('model_name', model_name)
                            logger.info(f"[{self.session_id}] Tokens from generations.message.usage_metadata (Gemini-like): In={input_tokens}, Out={output_tokens}, Total={total_tokens}, Model={model_name}")
                            break
                    elif hasattr(first_gen, 'generation_info') and first_gen.generation_info:
                        gen_info = first_gen.generation_info
                        if isinstance(gen_info, dict):
                            model_name = gen_info.get('model', model_name)
                            if 'token_usage' in gen_info and isinstance(gen_info['token_usage'], dict):
                                usage_dict = gen_info['token_usage']
                                input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens'))
                                output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens'))
                                total_tokens = usage_dict.get('total_tokens')
                                logger.info(f"[{self.session_id}] Tokens from generations.generation_info.token_usage: In={input_tokens}, Out={output_tokens}, Total={total_tokens}, Model={model_name}")
                            elif 'eval_count' in gen_info: # Ollama output tokens
                                output_tokens = gen_info.get('eval_count')
                                input_tokens = gen_info.get('prompt_eval_count')
                                logger.info(f"[{self.session_id}] Tokens from generations.generation_info (Ollama-like): Eval(Out)={output_tokens}, PromptEval(In)={input_tokens}, Model={model_name}")
                            break
            else:
                if not response.generations:
                    logger.warning(f"[{self.session_id}] response.generations is empty or None.")


            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0

            if total_tokens is None:
                total_tokens = input_tokens + output_tokens
            else:
                total_tokens = int(total_tokens)

            token_usage_payload = {
                "model_name": str(model_name),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "source": source_for_tokens
            }

            if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
                usage_str = f"Model: {model_name}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens} (Source: {source_for_tokens})"
                log_content = f"[LLM Token Usage] {usage_str}"
                await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
                await self.send_ws_message("llm_token_usage", token_usage_payload)
                await self._save_message("llm_token_usage", json.dumps(token_usage_payload))
                logger.info(f"[{self.session_id}] {log_content} - Sent to client.")
            else:
                logger.info(f"[{self.session_id}] Token usage resulted in all zeros for model '{model_name}' from source '{source_for_tokens}'. Not sending update.")

        except Exception as e:
            logger.error(f"[{self.session_id}] Error processing token usage in on_llm_end: {e}", exc_info=True)


    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        # ... (existing content - no changes needed) ...
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error occurred during LLM call.")
        await self.send_ws_message("agent_thinking_update", {"status": "Error during LLM call."})
        await self._save_message("error_llm", error_content)

    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None: pass

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        # ... (existing content - no changes needed) ...
        tool_name = serialized.get("name", "Unknown Tool")
        try:
            self._check_cancellation(f"Tool execution ('{tool_name}')")
        except AgentCancelledException:
            raise
        log_prefix = self._get_log_prefix()
        log_input = input_str[:500] + "..." if len(str(input_str)) > 500 else input_str
        log_content = f"[Tool Start] Using '{tool_name}' with input: '{log_input}'"
        logger.info(f"[{self.session_id}] {log_content}")
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("agent_thinking_update", {"status": f"Using tool: {tool_name}..."})
        await self._save_message("tool_input", f"{tool_name}:::{log_input}")

    async def on_tool_end(self, output: str, name: str = "Unknown Tool", **kwargs: Any) -> None:
        # ... (existing content - no changes needed) ...
        log_prefix = self._get_log_prefix()
        output_str = str(output)
        logger.info(f"[{self.session_id}] Tool '{name}' finished. Output length: {len(output_str)}")

        monitor_output = output_str

        success_prefix = "SUCCESS::write_file:::"
        if name == "write_file" and output_str.startswith(success_prefix):
            try:
                if len(output_str) > len(success_prefix):
                    relative_path_str = output_str[len(success_prefix):]
                    logger.info(f"[{self.session_id}] Detected successful write_file: '{relative_path_str}'")
                    await self._save_message("artifact_generated", relative_path_str)
                    await self.send_ws_message("monitor_log", f"{log_prefix} [ARTIFACT_GENERATED] {relative_path_str} (via {name})")
                    monitor_output = f"Successfully wrote file: '{relative_path_str}'"

                    if self.current_task_id:
                        logger.info(f"[{self.session_id}] Triggering artifact refresh for task {self.current_task_id} after {name}.")
                        await self.send_ws_message("trigger_artifact_refresh", {"taskId": self.current_task_id})
                    else:
                        logger.warning(f"[{self.session_id}] Cannot trigger artifact refresh for {name}: current_task_id not set in callback handler.")
                else:
                    logger.warning(f"[{self.session_id}] write_file output matched prefix but had no filename: '{output_str}'")
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
        else:
            monitor_output = output_str[:1000] + "..." if len(output_str) > 1000 else output_str

        formatted_output = f"\n---\n{monitor_output.strip()}\n---"
        log_content = f"[Tool Output] Tool '{name}' returned:{formatted_output}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content}")
        await self.send_ws_message("agent_thinking_update", {"status": f"Processed tool: {name}."})
        await self._save_message("tool_output", output_str)

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "Unknown Tool", **kwargs: Any) -> None:
        """Handle error from tool."""
        # MODIFIED: Attempt to get a more specific tool name if 'name' is generic
        actual_tool_name = name
        if name == "Unknown Tool" and "serialized" in kwargs and isinstance(kwargs["serialized"], dict):
            actual_tool_name = kwargs["serialized"].get("name", name)
            if actual_tool_name != name:
                 logger.info(f"[{self.session_id}] Resolved 'Unknown Tool' to '{actual_tool_name}' from serialized data for error reporting.")


        if isinstance(error, AgentCancelledException):
            logger.warning(f"[{self.session_id}] Tool '{actual_tool_name}' execution cancelled by AgentCancelledException.")
            await self.send_ws_message("agent_thinking_update", {"status": f"Tool cancelled: {actual_tool_name}."})
            raise error

        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        error_str = str(error)
        # Use actual_tool_name in logging and messages
        logger.error(f"[{self.session_id}] Tool '{actual_tool_name}' Error: {error_str}", exc_info=True)
        error_content = f"[Tool Error] Tool '{actual_tool_name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", f"Error occurred during tool execution: {actual_tool_name}.")
        await self.send_ws_message("agent_thinking_update", {"status": f"Error with tool: {actual_tool_name}."})
        await self._save_message("error_tool", f"{actual_tool_name}::{error_type_name}::{error_str}")


    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        # ... (existing content - no changes needed) ...
        log_prefix = self._get_log_prefix()
        thought = ""
        if action.log:
            log_lines = action.log.strip().split('\n')
            thought_lines = []
            in_thought = False
            for line in reversed(log_lines):
                stripped_line = line.strip()
                if stripped_line.startswith("Action:"):
                    in_thought = False
                    continue
                if stripped_line.startswith("Thought:"):
                    in_thought = True
                    thought_part = stripped_line.split(":", 1)[1].strip() if ":" in stripped_line else stripped_line
                    thought_lines.append(thought_part)
                    break
                if in_thought:
                    thought_lines.append(line)

            if thought_lines:
                thought = "\n".join(reversed(thought_lines)).strip()

        if thought:
            logger.debug(f"[{self.session_id}] Extracted thought (Action): {thought}")
            await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Thought (Action)] {thought}")
            await self._save_message("agent_thought_action", thought)
            await self.send_ws_message("agent_thinking_update", {"status": "Thinking..."})
        else:
            logger.warning(f"[{self.session_id}] Could not extract thought from agent action log: {action.log}")
            await self.send_ws_message("agent_thinking_update", {"status": "Processing..."})

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        # ... (existing content - no changes needed) ...
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Finish. Log: {finish.log}")

        final_thought = ""
        if finish.log:
            match = re.search(r"Thought:(.*?)(?=Final Answer:)", finish.log, re.S | re.IGNORECASE)
            if match:
                final_thought = match.group(1).strip()
                logger.debug(f"[{self.session_id}] Extracted final thought: {final_thought}")
                await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Thought (Final)] {final_thought}")
                await self._save_message("agent_thought_final", final_thought)
            else:
                logger.warning(f"[{self.session_id}] Could not extract final thought from agent finish log.")

        final_answer_content = finish.return_values.get("output", "No final output provided by agent.")
        if not isinstance(final_answer_content, str):
            final_answer_content = str(final_answer_content)

        await self._save_message("agent_finish", final_answer_content)
        await self.send_ws_message("monitor_log", f"{log_prefix} [Agent Finish] Sending complete final answer.")
        await self.send_ws_message("agent_message", final_answer_content)
        await self.send_ws_message("status_message", "Task processing complete.")
        logger.info(f"[{self.session_id}] Sent complete agent_message. Final answer saved to DB.")


    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any: pass
    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any: pass
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any: pass

