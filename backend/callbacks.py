import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json
import re

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult, ChatGenerationChunk, GenerationChunk
from langchain_core.messages import BaseMessage, AIMessageChunk
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document

# Project Imports
from backend.config import settings

logger = logging.getLogger(__name__)

class AgentCancelledException(Exception):
    """Custom exception to signal agent cancellation via callbacks."""
    pass

AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]

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
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def set_task_id(self, task_id: Optional[str]):
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    async def _save_message(self, msg_type: str, content: str):
        if self.current_task_id:
            try:
                await self.db_add_message(self.current_task_id, self.session_id, msg_type, str(content))
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {msg_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{msg_type}' to DB: current_task_id not set.")

    def _check_cancellation(self, step_name: str):
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
        
        # Determine role if possible (e.g., from kwargs if main flow passes it)
        role_hint = kwargs.get("metadata", {}).get("component_name", "LLM")
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_PROCESSING", "message": f"Thinking ({role_hint})..."})
        
        prompt_summary = str(prompts)[:200] + "..." if len(str(prompts)) > 200 else str(prompts)
        await self.send_ws_message("monitor_log", {
            "text": f"{self._get_log_prefix()} [LLM Core Start] Role: {role_hint}, Prompts: {prompt_summary}",
            "log_source": f"LLM_CORE_START_{role_hint.upper()}"
        })

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        try:
            self._check_cancellation("Chat Model execution")
        except AgentCancelledException:
            raise
        role_hint = kwargs.get("metadata", {}).get("component_name", "ChatModel")
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_PROCESSING", "message": f"Thinking ({role_hint})..."})
        
        message_summary = str(messages)[:200] + "..." if len(str(messages)) > 200 else str(messages)
        await self.send_ws_message("monitor_log", {
            "text": f"{self._get_log_prefix()} [Chat Model Core Start] Role: {role_hint}, Messages: {message_summary}",
            "log_source": f"LLM_CORE_START_{role_hint.upper()}"
        })

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        pass

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        input_tokens: Optional[int] = None; output_tokens: Optional[int] = None; total_tokens: Optional[int] = None
        model_name: str = "unknown_model"; source_for_tokens = "unknown"
        try: 
            if response.llm_output and isinstance(response.llm_output, dict):
                llm_output_data = response.llm_output; source_for_tokens = "llm_output"
                model_name = llm_output_data.get('model_name', llm_output_data.get('model', model_name))
                if 'token_usage' in llm_output_data and isinstance(llm_output_data['token_usage'], dict):
                    usage_dict = llm_output_data['token_usage']
                    input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens')); output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens')); total_tokens = usage_dict.get('total_tokens')
                elif 'usage_metadata' in llm_output_data and isinstance(llm_output_data['usage_metadata'], dict):
                    usage_dict = llm_output_data['usage_metadata']
                    input_tokens = usage_dict.get('prompt_token_count'); output_tokens = usage_dict.get('candidates_token_count'); total_tokens = usage_dict.get('total_token_count')
                elif 'eval_count' in llm_output_data: 
                    output_tokens = llm_output_data.get('eval_count'); input_tokens = llm_output_data.get('prompt_eval_count')
            if (input_tokens is None and output_tokens is None) and response.generations:
                for gen_list in response.generations:
                    if not gen_list: continue
                    first_gen = gen_list[0]; source_for_tokens = "generations"
                    if hasattr(first_gen, 'message') and hasattr(first_gen.message, 'usage_metadata') and first_gen.message.usage_metadata:
                        usage_metadata = first_gen.message.usage_metadata
                        if isinstance(usage_metadata, dict):
                            input_tokens = usage_metadata.get('prompt_token_count', usage_metadata.get('input_tokens')); output_tokens = usage_metadata.get('candidates_token_count', usage_metadata.get('output_tokens')); total_tokens = usage_metadata.get('total_token_count')
                            if hasattr(first_gen.message, 'response_metadata') and isinstance(first_gen.message.response_metadata, dict): model_name = first_gen.message.response_metadata.get('model_name', model_name)
                            if not model_name or model_name == "unknown_model": model_name = getattr(first_gen, 'generation_info', {}).get('model_name', model_name)
                            break
                    elif hasattr(first_gen, 'generation_info') and first_gen.generation_info:
                        gen_info = first_gen.generation_info
                        if isinstance(gen_info, dict):
                            model_name = gen_info.get('model', model_name)
                            if 'token_usage' in gen_info and isinstance(gen_info['token_usage'], dict):
                                usage_dict = gen_info['token_usage']
                                input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens')); output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens')); total_tokens = usage_dict.get('total_tokens')
                            elif 'eval_count' in gen_info: output_tokens = gen_info.get('eval_count'); input_tokens = gen_info.get('prompt_eval_count')
                            break
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
            if total_tokens is None: total_tokens = input_tokens + output_tokens
            else: total_tokens = int(total_tokens)
            token_usage_payload = {"model_name": str(model_name), "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens, "source": source_for_tokens}
            if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
                usage_str = f"Model: {model_name}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens} (Source: {source_for_tokens})"
                log_content_tokens = f"[LLM Token Usage] {usage_str}"
                await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {log_content_tokens}", "log_source": "LLM_TOKEN_USAGE"})
                await self.send_ws_message("llm_token_usage", token_usage_payload)
                await self._save_message("llm_token_usage", json.dumps(token_usage_payload))
        except Exception as e:
            logger.error(f"[{self.session_id}] Error processing token usage in on_llm_end: {e}", exc_info=True)
        
        role_hint = kwargs.get("metadata", {}).get("component_name", "LLM")
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_COMPLETED", "message": f"Thinking ({role_hint}) complete."})

    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        role_hint = kwargs.get("metadata", {}).get("component_name", "LLM")
        logger.error(f"[{self.session_id}] LLM Error ({role_hint}): {error}", exc_info=True)
        error_content = f"[LLM Core Error] ({role_hint}) {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {error_content}", "log_source": f"LLM_CORE_ERROR_{role_hint.upper()}"})
        await self.send_ws_message("status_message", f"Error during LLM call ({role_hint}).")
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_ERROR", "message": f"Error in LLM ({role_hint})."})
        await self._save_message("error_llm", error_content)

    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None: pass

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        self.current_tool_name = serialized.get("name", "UnknownTool")
        try:
            self._check_cancellation(f"Tool execution ('{self.current_tool_name}')")
        except AgentCancelledException:
            self.current_tool_name = None 
            raise
        
        log_prefix = self._get_log_prefix()
        log_input_summary = input_str[:150] + "..." if len(str(input_str)) > 150 else input_str
        monitor_log_content = f"[Tool Start] Using tool '{self.current_tool_name}' with input: '{input_str}'"
        
        await self.send_ws_message("monitor_log", {
            "text": f"{log_prefix} {monitor_log_content}",
            "log_source": f"TOOL_START_{self.current_tool_name.upper()}"
        })
        
        user_friendly_tool_name = self.current_tool_name.replace("_", " ").title()
        await self.send_ws_message("agent_thinking_update", {
            "status_key": "TOOL_USING", 
            "message": f"Using {user_friendly_tool_name}...",
            "details": {"tool_name": self.current_tool_name, "input_summary": log_input_summary}
        })
        await self._save_message("tool_input", f"{self.current_tool_name}:::{input_str}")

    async def on_tool_end(self, output: str, name: str = "UnknownTool", **kwargs: Any) -> None:
        tool_name_for_log = name
        if name == "UnknownTool" and self.current_tool_name:
            tool_name_for_log = self.current_tool_name
        
        log_prefix = self._get_log_prefix()
        output_str = str(output)
        monitor_output_summary = output_str[:1000] + "..." if len(output_str) > 1000 else output_str
        log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' returned:\n---\n{monitor_output_summary.strip()}\n---"
        final_log_source = f"TOOL_OUTPUT_{tool_name_for_log.upper()}"

        success_prefix = "SUCCESS::write_file:::"
        if tool_name_for_log == "write_file" and output_str.startswith(success_prefix):
            try:
                if len(output_str) > len(success_prefix):
                    relative_path_str = output_str[len(success_prefix):]
                    await self._save_message("artifact_generated", relative_path_str)
                    await self.send_ws_message("monitor_log", {
                        "text": f"{log_prefix} [ARTIFACT_GENERATED] {relative_path_str} (via {tool_name_for_log})",
                        "log_source": "ARTIFACT_GENERATED"
                    })
                    log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' successfully wrote file: '{relative_path_str}'"
                    if self.current_task_id:
                        await self.send_ws_message("trigger_artifact_refresh", {"taskId": self.current_task_id})
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
        
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {log_content_tool_end}", "log_source": final_log_source})
        
        user_friendly_tool_name = tool_name_for_log.replace("_", " ").title()
        await self.send_ws_message("agent_thinking_update", {
            "status_key": "TOOL_COMPLETED", 
            "message": f"{user_friendly_tool_name} finished.",
            "details": {"tool_name": tool_name_for_log, "output_summary": output_str[:100]+"..." if output_str else "No output."}
        })
        await self._save_message("tool_output", output_str)
        self.current_tool_name = None 

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "UnknownTool", **kwargs: Any) -> None:
        actual_tool_name = name
        if name == "UnknownTool" and self.current_tool_name:
            actual_tool_name = self.current_tool_name
        
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__; error_str = str(error)
        user_friendly_tool_name = actual_tool_name.replace("_", " ").title()
        
        if isinstance(error, AgentCancelledException):
            logger.warning(f"[{self.session_id}] Tool '{actual_tool_name}' execution cancelled by AgentCancelledException.")
            await self.send_ws_message("agent_thinking_update", {"status_key": "TOOL_CANCELLED", "message": f"Tool {user_friendly_tool_name} cancelled."})
            await self.send_ws_message("monitor_log", {
                "text": f"{log_prefix} [Tool Cancelled] Tool '{actual_tool_name}' execution stopped by user request.",
                "log_source": f"TOOL_CANCELLED_{actual_tool_name.upper()}"
            })
            self.current_tool_name = None 
            raise error

        logger.error(f"[{self.session_id}] Tool '{actual_tool_name}' Error: {error_str}", exc_info=True)
        monitor_error_content = f"[Tool Error] Tool '{actual_tool_name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {monitor_error_content}", "log_source": f"TOOL_ERROR_{actual_tool_name.upper()}"})
        await self.send_ws_message("status_message", f"Error with tool: {actual_tool_name}.") # This goes to chat
        await self.send_ws_message("agent_thinking_update", {
            "status_key": "TOOL_ERROR", 
            "message": f"Error with {user_friendly_tool_name}.",
            "details": {"tool_name": actual_tool_name, "error_type": error_type_name}
        })
        await self._save_message("error_tool", f"{actual_tool_name}::{error_type_name}::{error_str}")
        self.current_tool_name = None 

    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        thought = ""
        if action.log:
            thought_match = re.search(r"Thought:(.*?)(Action:|$)", action.log, re.S | re.IGNORECASE)
            if thought_match: thought = thought_match.group(1).strip()
        
        if thought:
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought] {thought}", "log_source": "EXECUTOR_THOUGHT"})
            await self._save_message("agent_thought_action", thought)
        
        action_details_log = f"[Executor Action] Action: {action.tool}, Input: {str(action.tool_input)[:500]}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {action_details_log}", "log_source": "EXECUTOR_ACTION"})
        
        # More specific status will come from on_tool_start if a tool is called
        # If LLM tries to answer directly, on_agent_finish will handle the output.
        # This generic update might be useful if there are multiple thought/action cycles before a tool or final answer.
        await self.send_ws_message("agent_thinking_update", {"status_key": "AGENT_EXECUTING_LOGIC", "message": "Processing..."})

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        final_thought_in_step = ""
        if finish.log:
            thought_match = re.search(r"Thought:(.*?)(Final Answer:)", finish.log, re.S | re.IGNORECASE)
            if thought_match: final_thought_in_step = thought_match.group(1).strip()
        
        if final_thought_in_step:
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought Final Step] {final_thought_in_step}", "log_source": "EXECUTOR_THOUGHT_FINAL_STEP"})
            await self._save_message("agent_thought_final", final_thought_in_step)
        
        step_output_content = finish.return_values.get("output", "No specific output from agent step.")
        if not isinstance(step_output_content, str): step_output_content = str(step_output_content)
            
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Step Output] {step_output_content}", "log_source": "EXECUTOR_STEP_OUTPUT"})
        await self._save_message("agent_executor_step_finish", step_output_content)

        await self.send_ws_message("agent_thinking_update", {"status_key": "EXECUTOR_STEP_COMPLETED", "message": "Agent processing step complete."})
        self.current_tool_name = None

    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any: pass
    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any: pass
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any: pass

