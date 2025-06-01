# backend/callbacks.py
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json
import re
import asyncio # Added for asyncio.sleep

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult, ChatGenerationChunk, GenerationChunk
from langchain_core.messages import BaseMessage, AIMessageChunk
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document

# Project Imports
from backend.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class AgentCancelledException(Exception):
    """Custom exception to signal agent cancellation via callbacks."""
    pass

AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]

LOG_SOURCE_INTENT_CLASSIFIER = "INTENT_CLASSIFIER"
LOG_SOURCE_PLANNER = "PLANNER"
LOG_SOURCE_CONTROLLER = "CONTROLLER"
LOG_SOURCE_EXECUTOR = "EXECUTOR"
LOG_SOURCE_EVALUATOR_STEP = "EVALUATOR_STEP"
LOG_SOURCE_EVALUATOR_OVERALL = "EVALUATOR_OVERALL"
LOG_SOURCE_TOOL_PREFIX = "TOOL"
LOG_SOURCE_LLM_CORE = "LLM_CORE"
LOG_SOURCE_SYSTEM = "SYSTEM"
LOG_SOURCE_UI_EVENT = "UI_EVENT"
LOG_SOURCE_WARNING = "WARNING"
LOG_SOURCE_ERROR = "ERROR"
LOG_SOURCE_ARTIFACT = "ARTIFACT"

SUB_TYPE_BOTTOM_LINE = "bottom_line"
SUB_TYPE_SUB_STATUS = "sub_status"
SUB_TYPE_THOUGHT = "thought"

DB_MSG_TYPE_SUB_STATUS = "db_agent_sub_status"
DB_MSG_TYPE_THOUGHT = "db_agent_thought"
DB_MSG_TYPE_TOOL_RESULT_FOR_CHAT = "db_tool_result_for_chat"


# Tools whose direct output should be sent to chat
TEXT_OUTPUT_TOOLS_FOR_CHAT: List[str] = [
    "read_file",
    "web_page_reader",
    "pubmed_search",
    "tavily_search_api",
    "deep_research_synthesizer",
    "workspace_shell",
    "Python_REPL",
    "playwright_web_search"
]

# Tools for which a confirmation message (derived from output) should be sent to chat
CONFIRMATION_ONLY_TOOLS_FOR_CHAT: List[str] = [
    "write_file",
    "python_package_installer"
]


class WebSocketCallbackHandler(AsyncCallbackHandler):
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
        self.session_data = session_data_ref
        self.current_task_id: Optional[str] = None
        self.current_tool_name: Optional[str] = None
        self.current_agent_role_hint: Optional[str] = None
        self.current_tool_input_str: Optional[str] = None
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def set_task_id(self, task_id: Optional[str]):
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    async def _save_message_to_db(self, message_type: str, content_data: Any):
        if self.current_task_id:
            try:
                content_str = json.dumps(content_data) if isinstance(content_data, dict) else str(content_data)
                await self.db_add_message(self.current_task_id, self.session_id, message_type, content_str)
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {message_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{message_type}' to DB: current_task_id not set.")

    async def _send_thinking_update(self, message_text: str, status_key: str, component_hint: str, sub_type: str = SUB_TYPE_BOTTOM_LINE, details: Optional[Dict] = None, thought_label: Optional[str] = None):
        payload = {
            "status_key": status_key,
            "message": message_text,
            "component_hint": component_hint,
            "sub_type": sub_type,
        }
        if details: payload["details"] = details
        if sub_type == SUB_TYPE_THOUGHT and thought_label:
            payload["message"] = { "label": thought_label, "content_markdown": message_text }

        await self.send_ws_message("agent_thinking_update", payload)

        if self.current_task_id and (sub_type == SUB_TYPE_SUB_STATUS or sub_type == SUB_TYPE_THOUGHT):
            db_type = DB_MSG_TYPE_SUB_STATUS if sub_type == SUB_TYPE_SUB_STATUS else DB_MSG_TYPE_THOUGHT
            db_content = {"message_text": message_text, "component_hint": component_hint} if sub_type == SUB_TYPE_SUB_STATUS \
                         else {"thought_label": thought_label, "thought_content_markdown": message_text, "component_hint": component_hint}
            await self._save_message_to_db(db_type, db_content)

    def _check_cancellation(self, step_name: str, check_point: str = "INITIAL"):
        # Access the session-specific data using self.session_data (which is session_data[session_id])
        # Ensure self.session_data is correctly referencing the specific session's data dictionary
        session_specific_data_for_check = self.session_data # In callbacks, self.session_data IS session_data[session_id]
        
        cancel_flag_value = False
        if session_specific_data_for_check and isinstance(session_specific_data_for_check, dict):
            cancel_flag_value = session_specific_data_for_check.get('cancellation_requested', False)
        else:
            # This case should not happen if session_data is managed correctly in server.py
            logger.error(f"CRITICAL_ERROR_CANCEL_CHECK: [{self.session_id}] _check_cancellation for '{step_name}' ({check_point}): self.session_data is not a dict or is None! Type: {type(session_specific_data_for_check)}")
            # Potentially raise an error or return, as state is inconsistent
            return # Avoid proceeding if session data is not as expected

        logger.critical(f"CRITICAL_DEBUG_CANCEL_CHECK: [{self.session_id}] _check_cancellation for '{step_name}' ({check_point}): cancellation_requested flag is currently {cancel_flag_value}")

        if cancel_flag_value: # Use the fetched value
            logger.critical(f"CRITICAL_DEBUG_CANCEL_RAISE: [{self.session_id}] _check_cancellation: CANCELLATION DETECTED for step '{step_name}' ({check_point}). RAISING AgentCancelledException NOW!")
            raise AgentCancelledException(f"Cancellation requested by user before {step_name} ({check_point}).")


    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        self._check_cancellation("LLM execution", "Initial Check")
        await asyncio.sleep(0) # Yield control briefly
        self._check_cancellation("LLM execution", "Post-Yield Check")

        metadata = kwargs.get("metadata", {})
        self.current_agent_role_hint = metadata.get("component_name", LOG_SOURCE_LLM_CORE)
        logger.critical(f"CRITICAL_DEBUG: [{self.session_id}] on_llm_start: ENTERED for role_hint: {self.current_agent_role_hint}. Metadata: {metadata}")

        component_hint_for_status = self.current_agent_role_hint if self.current_agent_role_hint != LOG_SOURCE_LLM_CORE else "LLM"
        await self._send_thinking_update(f"Thinking ({component_hint_for_status})...", "LLM_PROCESSING_START", self.current_agent_role_hint, SUB_TYPE_BOTTOM_LINE)
        prompt_summary = str(prompts)[:200] + "..." if len(str(prompts)) > 200 else str(prompts)
        await self.send_ws_message("monitor_log", {"text": f"{self._get_log_prefix()} [LLM Core Start] Role: {self.current_agent_role_hint}, Prompts: {prompt_summary}", "log_source": f"{LOG_SOURCE_LLM_CORE}_START_{self.current_agent_role_hint.upper()}"})


    async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any) -> Any:
        self._check_cancellation("Chat Model execution", "Initial Check")
        await asyncio.sleep(0) # Yield control briefly
        self._check_cancellation("Chat Model execution", "Post-Yield Check")

        metadata = kwargs.get("metadata", {})
        self.current_agent_role_hint = metadata.get("component_name", LOG_SOURCE_LLM_CORE)
        logger.critical(f"CRITICAL_DEBUG: [{self.session_id}] on_chat_model_start: ENTERED for role_hint: {self.current_agent_role_hint}. Metadata: {metadata}")

        component_hint_for_status = self.current_agent_role_hint if self.current_agent_role_hint != LOG_SOURCE_LLM_CORE else "ChatModel"
        await self._send_thinking_update(f"Thinking ({component_hint_for_status})...", "LLM_PROCESSING_START", self.current_agent_role_hint, SUB_TYPE_BOTTOM_LINE)
        message_summary = str(messages)[:200] + "..." if len(str(messages)) > 200 else str(messages)
        await self.send_ws_message("monitor_log", {"text": f"{self._get_log_prefix()} [Chat Model Core Start] Role: {self.current_agent_role_hint}, Messages: {message_summary}", "log_source": f"{LOG_SOURCE_LLM_CORE}_START_{self.current_agent_role_hint.upper()}"})

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None: pass

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        total_tokens: Optional[int] = None
        model_name: str = "unknown_model"
        source_for_tokens = "unknown"

        logger.critical(f"CRITICAL_DEBUG: [{self.session_id}] on_llm_end: ENTERED for role_hint: {self.current_agent_role_hint}")
        logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Full response object type: {type(response)}")

        if response.llm_output is not None:
            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): response.llm_output IS PRESENT. Type: {type(response.llm_output)}. Content: {str(response.llm_output)[:500]}...")
        else:
            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): response.llm_output IS NONE.")

        if response.generations is not None and len(response.generations) > 0:
            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): response.generations IS PRESENT and NOT EMPTY (length {len(response.generations)}).")
            for i, gen_list in enumerate(response.generations):
                logger.debug(f"DEBUG: Generation list {i} (length {len(gen_list)}) for role {self.current_agent_role_hint}:")
                if gen_list:
                    for j, gen_item in enumerate(gen_list):
                        logger.debug(f"DEBUG:   Item {j} type: {type(gen_item)}")
                        if hasattr(gen_item, 'text'): logger.debug(f"DEBUG:     Item {j} text: {str(gen_item.text)[:100]}...")
                        if hasattr(gen_item, 'message'):
                            logger.debug(f"DEBUG:     Item {j} message type: {type(gen_item.message)}")
                            if hasattr(gen_item.message, 'content'): logger.debug(f"DEBUG:       Item {j} message content: {str(gen_item.message.content)[:100]}...")
                            if hasattr(gen_item.message, 'additional_kwargs'): logger.debug(f"DEBUG:       Item {j} message additional_kwargs: {gen_item.message.additional_kwargs}")
                            if hasattr(gen_item.message, 'usage_metadata'): logger.debug(f"DEBUG:       Item {j} message usage_metadata: {gen_item.message.usage_metadata}")
                            if hasattr(gen_item.message, 'response_metadata'): logger.debug(f"DEBUG:       Item {j} message response_metadata: {gen_item.message.response_metadata}")
                        if hasattr(gen_item, 'generation_info'): logger.debug(f"DEBUG:     Item {j} generation_info: {gen_item.generation_info}")
        else:
            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): response.generations IS NONE or EMPTY.")


        try:
            if response.llm_output and isinstance(response.llm_output, dict):
                llm_output_data = response.llm_output
                source_for_tokens = "llm_output"
                model_name = llm_output_data.get('model_name', llm_output_data.get('model', model_name))
                logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Processing llm_output. Model name from llm_output: {model_name}")

                if 'token_usage' in llm_output_data and isinstance(llm_output_data['token_usage'], dict):
                    usage_dict_from_llm_output = llm_output_data['token_usage']
                    input_tokens = usage_dict_from_llm_output.get('prompt_tokens', usage_dict_from_llm_output.get('input_tokens'))
                    output_tokens = usage_dict_from_llm_output.get('completion_tokens', usage_dict_from_llm_output.get('output_tokens'))
                    total_tokens = usage_dict_from_llm_output.get('total_tokens')
                elif 'usage_metadata' in llm_output_data and isinstance(llm_output_data['usage_metadata'], dict):
                    usage_metadata_from_llm_output = llm_output_data['usage_metadata']
                    input_tokens = usage_metadata_from_llm_output.get('input_tokens', usage_metadata_from_llm_output.get('prompt_token_count'))
                    output_tokens = usage_metadata_from_llm_output.get('output_tokens', usage_metadata_from_llm_output.get('candidates_token_count'))
                    total_tokens = usage_metadata_from_llm_output.get('total_tokens', usage_metadata_from_llm_output.get('total_token_count'))
                elif 'eval_count' in llm_output_data:
                    output_tokens = llm_output_data.get('eval_count')
                    input_tokens = llm_output_data.get('prompt_eval_count')

            if (input_tokens is None or output_tokens is None) and response.generations:
                logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Tokens not found or incomplete in llm_output, trying response.generations.")
                for gen_list in response.generations:
                    if not gen_list: continue
                    first_gen = gen_list[0]
                    source_for_tokens = "generations"
                    
                    if hasattr(first_gen, 'message') and hasattr(first_gen.message, 'usage_metadata') and first_gen.message.usage_metadata:
                        usage_metadata_from_gen = first_gen.message.usage_metadata
                        if isinstance(usage_metadata_from_gen, dict):
                            input_tokens = usage_metadata_from_gen.get('input_tokens', usage_metadata_from_gen.get('prompt_token_count'))
                            output_tokens = usage_metadata_from_gen.get('output_tokens', usage_metadata_from_gen.get('candidates_token_count'))
                            total_tokens = usage_metadata_from_gen.get('total_tokens', usage_metadata_from_gen.get('total_token_count'))
                            if hasattr(first_gen.message, 'response_metadata') and isinstance(first_gen.message.response_metadata, dict):
                                model_name = first_gen.message.response_metadata.get('model_name', model_name)
                            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Tokens from generations.message.usage_metadata (Gemini/ChatChunk): In={input_tokens}, Out={output_tokens}, Total={total_tokens}, Model={model_name}")
                            break
                    elif hasattr(first_gen, 'generation_info') and first_gen.generation_info:
                        gen_info = first_gen.generation_info
                        if isinstance(gen_info, dict):
                            model_name = gen_info.get('model', model_name)
                            if 'token_usage' in gen_info and isinstance(gen_info['token_usage'], dict):
                                usage_dict_from_gen_info = gen_info['token_usage']
                                input_tokens = usage_dict_from_gen_info.get('prompt_tokens', usage_dict_from_gen_info.get('input_tokens'))
                                output_tokens = usage_dict_from_gen_info.get('completion_tokens', usage_dict_from_gen_info.get('output_tokens'))
                                total_tokens = usage_dict_from_gen_info.get('total_tokens')
                            elif 'eval_count' in gen_info:
                                output_tokens = gen_info.get('eval_count')
                                input_tokens = gen_info.get('prompt_eval_count')
                            elif 'usage_metadata' in gen_info and isinstance(gen_info['usage_metadata'], dict):
                                usage_metadata_nested = gen_info['usage_metadata']
                                input_tokens = usage_metadata_nested.get('input_tokens', usage_metadata_nested.get('prompt_token_count'))
                                output_tokens = usage_metadata_nested.get('output_tokens', usage_metadata_nested.get('candidates_token_count'))
                                total_tokens = usage_metadata_nested.get('total_tokens', usage_metadata_nested.get('total_token_count'))
                            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Tokens from generations.generation_info (Ollama/Other): In={input_tokens}, Out={output_tokens}, Total={total_tokens}, Model={model_name}")
                            break
            
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
            if total_tokens is None: total_tokens = input_tokens + output_tokens
            else: total_tokens = int(total_tokens)

            logger.debug(f"[{self.session_id}] on_llm_end (Role: {self.current_agent_role_hint}): Final parsed tokens before sending: In={input_tokens}, Out={output_tokens}, Total={total_tokens}, Model={model_name}, Source={source_for_tokens}")

            if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
                token_usage_payload = {
                    "model_name": str(model_name),
                    "role_hint": self.current_agent_role_hint or LOG_SOURCE_LLM_CORE,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "source": source_for_tokens
                }
                usage_str = f"Model: {model_name}, Role: {token_usage_payload['role_hint']}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens} (Source: {source_for_tokens})"
                await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [LLM Token Usage] {usage_str}", "log_source": f"{LOG_SOURCE_LLM_CORE}_TOKEN_USAGE"})
                logger.info(f"[{self.session_id}] Sending 'llm_token_usage' message with payload: {token_usage_payload}")
                await self.send_ws_message("llm_token_usage", token_usage_payload)
                await self._save_message_to_db("llm_token_usage", token_usage_payload)
            else:
                logger.warning(f"[{self.session_id}] on_llm_end: No positive token counts found (In={input_tokens}, Out={output_tokens}, Total={total_tokens}). 'llm_token_usage' message will NOT be sent for role_hint: {self.current_agent_role_hint}.")
        except Exception as e:
            logger.error(f"[{self.session_id}] Error processing token usage in on_llm_end for role_hint {self.current_agent_role_hint}: {e}", exc_info=True)
        
        role_hint_for_status = self.current_agent_role_hint or LOG_SOURCE_LLM_CORE
        component_hint_for_status = role_hint_for_status if role_hint_for_status != LOG_SOURCE_LLM_CORE else "LLM"
        await self._send_thinking_update(f"Thinking ({component_hint_for_status}) complete.", "LLM_PROCESSING_END", role_hint_for_status, SUB_TYPE_BOTTOM_LINE)
        self.current_agent_role_hint = None

    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        role_hint = self.current_agent_role_hint or LOG_SOURCE_LLM_CORE
        component_hint_for_status = role_hint if role_hint != LOG_SOURCE_LLM_CORE else "LLM"
        logger.error(f"[{self.session_id}] LLM Error ({component_hint_for_status}): {error}", exc_info=True)
        error_content_for_db = f"LLM Core Error ({component_hint_for_status}) {error_type_name}: {error}"
        
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {error_content_for_db}", "log_source": f"{LOG_SOURCE_LLM_CORE}_ERROR_{role_hint.upper()}"})
        await self._send_thinking_update(f"Error in LLM ({component_hint_for_status}).", "LLM_ERROR", role_hint, SUB_TYPE_BOTTOM_LINE, details={"error_type": error_type_name, "error_message": str(error)[:100]})
        await self._save_message_to_db(f"error_llm_{role_hint.lower()}", {"error": error_content_for_db})
        self.current_agent_role_hint = None

    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None: pass

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        self.current_tool_name = serialized.get("name", "UnknownTool")
        self.current_tool_input_str = input_str
        
        self._check_cancellation(f"Tool execution ('{self.current_tool_name}')", "Initial Check")
        await asyncio.sleep(0) # Yield control briefly
        self._check_cancellation(f"Tool execution ('{self.current_tool_name}')", "Post-Yield Check")
        # If AgentCancelledException is raised, it will propagate up and be handled by the agent flow.

        log_prefix = self._get_log_prefix()
        log_input_summary = input_str[:150] + "..." if len(str(input_str)) > 150 else input_str
        monitor_log_content = f"[Tool Start] Using tool '{self.current_tool_name}' with input: '{input_str}'"
        tool_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{self.current_tool_name.upper()}_START"
        
        await self.send_ws_message("monitor_log", { "text": f"{log_prefix} {monitor_log_content}", "log_source": tool_log_source })
        user_friendly_tool_name = self.current_tool_name.replace("_", " ").title()
        await self._send_thinking_update(f"Using {user_friendly_tool_name}...", "TOOL_USING", f"{LOG_SOURCE_TOOL_PREFIX}_{self.current_tool_name.upper()}", SUB_TYPE_SUB_STATUS, details={"tool_name": self.current_tool_name, "input_summary": log_input_summary})
        await self._save_message_to_db(f"tool_input_{self.current_tool_name}", {"tool_name": self.current_tool_name, "input": input_str})

    async def on_tool_end(self, output: str, name: str = "UnknownTool", **kwargs: Any) -> None:
        tool_name_for_log = name if name != "UnknownTool" else self.current_tool_name or "UnknownTool"
        log_prefix = self._get_log_prefix(); output_str = str(output)
        monitor_output_summary = output_str[:1000] + "..." if len(output_str) > 1000 else output_str
        log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' returned:\n---\n{monitor_output_summary.strip()}\n---"
        final_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{tool_name_for_log.upper()}_OUTPUT"

        logger.critical(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] Entered for tool: '{tool_name_for_log}'. Output starts with: '{output_str[:50]}...'")
        success_prefix = "SUCCESS::write_file:::"
        if tool_name_for_log == "write_file":
            logger.critical(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] Tool is 'write_file'. Checking output prefix.")
            if output_str.startswith(success_prefix):
                logger.critical(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] 'write_file' output STARTS WITH success_prefix.")
                try:
                    if len(output_str) > len(success_prefix):
                        relative_path_str = output_str[len(success_prefix):]
                        await self._save_message_to_db("artifact_generated", {"path": relative_path_str, "tool": tool_name_for_log})
                        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [{LOG_SOURCE_ARTIFACT.upper()}_GENERATED] {relative_path_str} (via {tool_name_for_log})", "log_source": f"{LOG_SOURCE_ARTIFACT}_{tool_name_for_log.upper()}"})
                        log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' successfully wrote file: '{relative_path_str}'"
                        if self.current_task_id:
                            logger.critical(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] write_file SUCCESS. About to send 'trigger_artifact_refresh' for task {self.current_task_id}")
                            await self.send_ws_message("trigger_artifact_refresh", {"taskId": self.current_task_id})
                        else:
                            logger.warning(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] write_file SUCCESS but current_task_id is None. Cannot trigger refresh.")
                    else:
                        logger.warning(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] 'write_file' output starts with prefix but is too short: '{output_str}'")
                except Exception as parse_err:
                    logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
            else:
                logger.warning(f"DEBUG_ARTIFACT_REFRESH: [callbacks.py/on_tool_end] 'write_file' output DOES NOT start with success_prefix. Output: '{output_str[:100]}...'")
        
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {log_content_tool_end}", "log_source": final_log_source})
        await self._save_message_to_db(f"tool_output_{tool_name_for_log}", {"tool_name": tool_name_for_log, "output": output_str})
        
        tool_output_for_chat_content = output_str
        artifact_filename_for_chat = None
        tool_input_summary_for_chat = str(self.current_tool_input_str)[:150] + "..." if self.current_tool_input_str else "N/A"

        if tool_name_for_log in TEXT_OUTPUT_TOOLS_FOR_CHAT:
            if tool_name_for_log == "read_file":
                artifact_filename_for_chat = self.current_tool_input_str
        
        elif tool_name_for_log in CONFIRMATION_ONLY_TOOLS_FOR_CHAT:
            if tool_name_for_log == "write_file":
                if output_str.startswith(success_prefix) and len(output_str) > len(success_prefix):
                    parsed_filename = output_str[len(success_prefix):]
                    tool_output_for_chat_content = f"File '{parsed_filename}' written successfully to workspace."
                    artifact_filename_for_chat = parsed_filename
                else:
                    tool_output_for_chat_content = f"Attempted to write file. Status: {output_str}"
            elif tool_name_for_log == "python_package_installer":
                tool_output_for_chat_content = output_str
        
        if tool_name_for_log in TEXT_OUTPUT_TOOLS_FOR_CHAT or tool_name_for_log in CONFIRMATION_ONLY_TOOLS_FOR_CHAT:
            chat_payload = {
                "tool_name": tool_name_for_log,
                "tool_input_summary": tool_input_summary_for_chat,
                "tool_output_content": tool_output_for_chat_content,
                "status": "success",
                "artifact_filename": artifact_filename_for_chat,
                "original_length": len(tool_output_for_chat_content),
                "is_truncated": False
            }
            await self.send_ws_message("tool_result_for_chat", chat_payload)
            await self._save_message_to_db(DB_MSG_TYPE_TOOL_RESULT_FOR_CHAT, chat_payload)
            logger.info(f"[{self.session_id}] Sent and saved 'tool_result_for_chat' for tool '{tool_name_for_log}'.")
        
        user_friendly_tool_name = tool_name_for_log.replace("_", " ").title()
        await self._send_thinking_update(f"{user_friendly_tool_name} finished.", "TOOL_COMPLETED", f"{LOG_SOURCE_TOOL_PREFIX}_{tool_name_for_log.upper()}", SUB_TYPE_SUB_STATUS, details={"tool_name": tool_name_for_log, "output_summary": output_str[:100]+"..." if output_str else "No output."})
        
        self.current_tool_name = None
        self.current_tool_input_str = None

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "UnknownTool", **kwargs: Any) -> None:
        actual_tool_name = name if name != "UnknownTool" else self.current_tool_name or "UnknownTool"
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__; error_str = str(error)
        user_friendly_tool_name = actual_tool_name.replace("_", " ").title()
        tool_error_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_ERROR"
        
        if isinstance(error, AgentCancelledException):
            logger.warning(f"[{self.session_id}] Tool '{actual_tool_name}' execution cancelled by callback.")
            await self._send_thinking_update(f"Tool {user_friendly_tool_name} cancelled.", "TOOL_CANCELLED", f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_CANCELLED", SUB_TYPE_SUB_STATUS)
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Tool Cancelled] Tool '{actual_tool_name}' execution stopped by callback.", "log_source": f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_CANCELLED"})
            self.current_tool_name = None; self.current_tool_input_str = None; raise error

        logger.error(f"[{self.session_id}] Tool '{actual_tool_name}' Error: {error_str}", exc_info=True)
        monitor_error_content = f"[Tool Error] Tool '{actual_tool_name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {monitor_error_content}", "log_source": tool_error_log_source})
        await self._send_thinking_update(f"Error with {user_friendly_tool_name}. (Retrying or evaluating...)", "TOOL_ERROR", tool_error_log_source, SUB_TYPE_SUB_STATUS, details={"tool_name": actual_tool_name, "error_type": error_type_name, "error_message": error_str[:200]})
        await self._save_message_to_db(f"error_tool_{actual_tool_name}", {"tool_name": actual_tool_name, "error_type": error_type_name, "error_message": error_str})
        self.current_tool_name = None
        self.current_tool_input_str = None

    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        thought_content = ""; action_log = action.log or ""
        thought_match = re.search(r"Thought:(.*?)(Action:|$)", action_log, re.S | re.IGNORECASE)
        if thought_match: thought_content = thought_match.group(1).strip()
        
        if thought_content:
            await self._send_thinking_update(thought_content, "AGENT_THOUGHT", LOG_SOURCE_EXECUTOR, SUB_TYPE_THOUGHT, thought_label="Executor thought:")
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought] {thought_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_THOUGHT"})
        else:
            logger.warning(f"[{self.session_id}] Could not extract thought from agent action log: {action_log[:200]}...")
        
        action_details_log = f"[Executor Action] Action: {action.tool}, Input: {str(action.tool_input)[:500]}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {action_details_log}", "log_source": f"{LOG_SOURCE_EXECUTOR}_ACTION"})
        await self._send_thinking_update("Processing action...", "AGENT_EXECUTING_LOGIC", LOG_SOURCE_EXECUTOR, SUB_TYPE_BOTTOM_LINE)

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        final_thought_content = ""; finish_log = finish.log or ""
        thought_match = re.search(r"Thought:(.*?)(Final Answer:)", finish_log, re.S | re.IGNORECASE)
        if thought_match: final_thought_content = thought_match.group(1).strip()
        
        if final_thought_content:
            await self._send_thinking_update(final_thought_content, "AGENT_FINAL_THOUGHT", LOG_SOURCE_EXECUTOR, SUB_TYPE_THOUGHT, thought_label="Executor final thought for step:")
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought Final Step] {final_thought_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_THOUGHT_FINAL"})
        else:
            logger.warning(f"[{self.session_id}] Could not extract final thought from agent finish log.")
        
        step_output_content = finish.return_values.get("output", "No specific output from agent step.")
        if not isinstance(step_output_content, str): step_output_content = str(step_output_content)
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Step Output] {step_output_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_STEP_OUTPUT"})
        await self._save_message_to_db("agent_executor_step_finish", {"output": step_output_content})
        await self._send_thinking_update("Agent processing step complete.", "EXECUTOR_STEP_COMPLETED", LOG_SOURCE_EXECUTOR, SUB_TYPE_SUB_STATUS)
        self.current_tool_name = None
        self.current_tool_input_str = None

    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any: pass
    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any: pass
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any: pass

