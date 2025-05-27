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
from backend.config import settings # For settings if needed

logger = logging.getLogger(__name__)

class AgentCancelledException(Exception):
    """Custom exception to signal agent cancellation via callbacks."""
    pass

AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]

# Standardized Log Source/Component Hint Constants
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

# NEW: Sub-types for agent_thinking_update messages
SUB_TYPE_BOTTOM_LINE = "bottom_line"
SUB_TYPE_SUB_STATUS = "sub_status"
SUB_TYPE_THOUGHT = "thought"

# NEW: DB message types for new persistent chat items
DB_MSG_TYPE_SUB_STATUS = "db_agent_sub_status"
DB_MSG_TYPE_THOUGHT = "db_agent_thought"


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
        self.db_add_message = db_add_message_func # This is the function to save to DB
        self.session_data = session_data_ref
        self.current_task_id: Optional[str] = None
        self.current_tool_name: Optional[str] = None
        self.current_agent_role_hint: Optional[str] = None
        logger.info(f"[{self.session_id}] WebSocketCallbackHandler initialized.")

    def set_task_id(self, task_id: Optional[str]):
        logger.debug(f"[{self.session_id}] Callback handler task ID set to: {task_id}")
        self.current_task_id = task_id

    def _get_log_prefix(self) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        return f"[{timestamp}][{self.session_id[:8]}]"

    async def _save_message_to_db(self, message_type: str, content_data: Any):
        """ Helper to save structured messages to DB if task_id is set. """
        if self.current_task_id:
            try:
                content_str = json.dumps(content_data) if isinstance(content_data, dict) else str(content_data)
                await self.db_add_message(self.current_task_id, self.session_id, message_type, content_str)
                logger.debug(f"[{self.session_id}] Saved message type '{message_type}' to DB for task {self.current_task_id}.")
            except Exception as e:
                logger.error(f"[{self.session_id}] Callback DB save error (Task: {self.current_task_id}, Type: {message_type}): {e}", exc_info=True)
        else:
            logger.warning(f"[{self.session_id}] Cannot save message type '{message_type}' to DB: current_task_id not set.")
            
    async def _send_thinking_update(self, message_text: str, status_key: str, component_hint: str, sub_type: str = SUB_TYPE_BOTTOM_LINE, details: Optional[Dict] = None, thought_label: Optional[str] = None):
        """
        Sends an agent_thinking_update message and saves it to DB if it's a sub_status or thought.
        For thoughts, message_text is the markdown content, thought_label is the prefix like "Controller thought:".
        """
        payload = {
            "status_key": status_key,
            "message": message_text, # For sub_status, this is the text; for thought, this is the markdown content
            "component_hint": component_hint,
            "sub_type": sub_type,
        }
        if details:
            payload["details"] = details
        if sub_type == SUB_TYPE_THOUGHT and thought_label:
            # For thoughts, the 'message' field in payload is the content_markdown.
            # The frontend will expect statusUpdateObject.message.label and statusUpdateObject.message.content_markdown
            payload["message"] = { "label": thought_label, "content_markdown": message_text }


        await self.send_ws_message("agent_thinking_update", payload)

        if self.current_task_id:
            if sub_type == SUB_TYPE_SUB_STATUS:
                await self._save_message_to_db(DB_MSG_TYPE_SUB_STATUS, {
                    "message_text": message_text, # The actual text for the sub-status
                    "component_hint": component_hint
                })
            elif sub_type == SUB_TYPE_THOUGHT:
                 await self._save_message_to_db(DB_MSG_TYPE_THOUGHT, {
                    "thought_label": thought_label,
                    "thought_content_markdown": message_text, # message_text is the markdown content here
                    "component_hint": component_hint
                })

    def _check_cancellation(self, step_name: str):
        current_session_specific_data = self.session_data.get(self.session_id)
        if current_session_specific_data:
            if current_session_specific_data.get('cancellation_requested', False):
                logger.warning(f"[{self.session_id}] Cancellation detected in callback before {step_name}. Raising AgentCancelledException.")
                raise AgentCancelledException("Cancellation requested by user.")
        else:
            logger.error(f"[{self.session_id}] Cannot check cancellation flag: Session data not found for session in shared dict.")


    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try: self._check_cancellation("LLM execution")
        except AgentCancelledException: raise 

        self.current_agent_role_hint = kwargs.get("metadata", {}).get("component_name", LOG_SOURCE_LLM_CORE)
        component_hint_for_status = self.current_agent_role_hint if self.current_agent_role_hint != LOG_SOURCE_LLM_CORE else "LLM"

        await self._send_thinking_update(
            message_text=f"Thinking ({component_hint_for_status})...",
            status_key="LLM_PROCESSING_START",
            component_hint=self.current_agent_role_hint,
            sub_type=SUB_TYPE_BOTTOM_LINE # This is a bottom line update
        )
        
        prompt_summary = str(prompts)[:200] + "..." if len(str(prompts)) > 200 else str(prompts)
        await self.send_ws_message("monitor_log", {
            "text": f"{self._get_log_prefix()} [LLM Core Start] Role: {self.current_agent_role_hint}, Prompts: {prompt_summary}",
            "log_source": f"{LOG_SOURCE_LLM_CORE}_START_{self.current_agent_role_hint.upper()}"
        })

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        try: self._check_cancellation("Chat Model execution")
        except AgentCancelledException: raise

        self.current_agent_role_hint = kwargs.get("metadata", {}).get("component_name", LOG_SOURCE_LLM_CORE)
        component_hint_for_status = self.current_agent_role_hint if self.current_agent_role_hint != LOG_SOURCE_LLM_CORE else "ChatModel"

        await self._send_thinking_update(
            message_text=f"Thinking ({component_hint_for_status})...",
            status_key="LLM_PROCESSING_START",
            component_hint=self.current_agent_role_hint,
            sub_type=SUB_TYPE_BOTTOM_LINE # Bottom line update
        )
        
        message_summary = str(messages)[:200] + "..." if len(str(messages)) > 200 else str(messages)
        await self.send_ws_message("monitor_log", {
            "text": f"{self._get_log_prefix()} [Chat Model Core Start] Role: {self.current_agent_role_hint}, Messages: {message_summary}",
            "log_source": f"{LOG_SOURCE_LLM_CORE}_START_{self.current_agent_role_hint.upper()}"
        })

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None: pass

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        # Token usage processing (remains the same)
        input_tokens: Optional[int] = None; output_tokens: Optional[int] = None; total_tokens: Optional[int] = None
        model_name: str = "unknown_model"; source_for_tokens = "unknown"
        try: 
            # ... (existing token parsing logic - no changes needed here) ...
            if response.llm_output and isinstance(response.llm_output, dict):
                llm_output_data = response.llm_output; source_for_tokens = "llm_output"
                model_name = llm_output_data.get('model_name', llm_output_data.get('model', model_name))
                if 'token_usage' in llm_output_data and isinstance(llm_output_data['token_usage'], dict):
                    usage_dict = llm_output_data['token_usage']
                    input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens')); output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens')); total_tokens = usage_dict.get('total_tokens')
                elif 'usage_metadata' in llm_output_data and isinstance(llm_output_data['usage_metadata'], dict): # Gemini specific
                    usage_dict = llm_output_data['usage_metadata']
                    input_tokens = usage_dict.get('prompt_token_count'); output_tokens = usage_dict.get('candidates_token_count'); total_tokens = usage_dict.get('total_token_count')
                elif 'eval_count' in llm_output_data: # Ollama specific
                    output_tokens = llm_output_data.get('eval_count'); input_tokens = llm_output_data.get('prompt_eval_count')
            if (input_tokens is None and output_tokens is None) and response.generations:
                for gen_list in response.generations:
                    if not gen_list: continue
                    first_gen = gen_list[0]; source_for_tokens = "generations"
                    if hasattr(first_gen, 'message') and hasattr(first_gen.message, 'usage_metadata') and first_gen.message.usage_metadata: # Gemini AIMessage
                        usage_metadata = first_gen.message.usage_metadata
                        if isinstance(usage_metadata, dict):
                            input_tokens = usage_metadata.get('prompt_token_count', usage_dict.get('input_tokens')); output_tokens = usage_metadata.get('candidates_token_count', usage_dict.get('output_tokens')); total_tokens = usage_metadata.get('total_token_count')
                            if hasattr(first_gen.message, 'response_metadata') and isinstance(first_gen.message.response_metadata, dict): model_name = first_gen.message.response_metadata.get('model_name', model_name)
                            if not model_name or model_name == "unknown_model": model_name = getattr(first_gen, 'generation_info', {}).get('model_name', model_name) # Fallback
                            break
                    elif hasattr(first_gen, 'generation_info') and first_gen.generation_info: # Ollama
                        gen_info = first_gen.generation_info
                        if isinstance(gen_info, dict):
                            model_name = gen_info.get('model', model_name)
                            if 'token_usage' in gen_info and isinstance(gen_info['token_usage'], dict): # Standard Langchain
                                usage_dict = gen_info['token_usage']
                                input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens')); output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens')); total_tokens = usage_dict.get('total_tokens')
                            elif 'eval_count' in gen_info: # Ollama specific in generation_info
                                output_tokens = gen_info.get('eval_count'); input_tokens = gen_info.get('prompt_eval_count')
                            break
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
            if total_tokens is None: total_tokens = input_tokens + output_tokens
            else: total_tokens = int(total_tokens)

            if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
                token_usage_payload = {"model_name": str(model_name), "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens, "source": source_for_tokens}
                usage_str = f"Model: {model_name}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens} (Source: {source_for_tokens})"
                log_content_tokens = f"[LLM Token Usage] {usage_str}"
                await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {log_content_tokens}", "log_source": f"{LOG_SOURCE_LLM_CORE}_TOKEN_USAGE"})
                await self.send_ws_message("llm_token_usage", token_usage_payload)
                await self._save_message_to_db("llm_token_usage", token_usage_payload) # Save structured token usage
        except Exception as e:
            logger.error(f"[{self.session_id}] Error processing token usage in on_llm_end: {e}", exc_info=True)
        
        role_hint = self.current_agent_role_hint or LOG_SOURCE_LLM_CORE
        component_hint_for_status = role_hint if role_hint != LOG_SOURCE_LLM_CORE else "LLM"
        await self._send_thinking_update(
            message_text=f"Thinking ({component_hint_for_status}) complete.",
            status_key="LLM_PROCESSING_END",
            component_hint=role_hint,
            sub_type=SUB_TYPE_BOTTOM_LINE # Bottom line update
        )
        self.current_agent_role_hint = None

    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        role_hint = self.current_agent_role_hint or LOG_SOURCE_LLM_CORE
        component_hint_for_status = role_hint if role_hint != LOG_SOURCE_LLM_CORE else "LLM"
        logger.error(f"[{self.session_id}] LLM Error ({component_hint_for_status}): {error}", exc_info=True)
        error_content_for_db = f"LLM Core Error ({component_hint_for_status}) {error_type_name}: {error}"
        
        await self.send_ws_message("monitor_log", {
            "text": f"{log_prefix} {error_content_for_db}",
            "log_source": f"{LOG_SOURCE_LLM_CORE}_ERROR_{role_hint.upper()}"
        })
        await self._send_thinking_update(
            message_text=f"Error in LLM ({component_hint_for_status}).",
            status_key="LLM_ERROR",
            component_hint=role_hint,
            sub_type=SUB_TYPE_BOTTOM_LINE, # Bottom line update
            details={"error_type": error_type_name, "error_message": str(error)[:100]}
        )
        await self._save_message_to_db(f"error_llm_{role_hint.lower()}", {"error": error_content_for_db})
        self.current_agent_role_hint = None

    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None: pass
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None: pass

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        self.current_tool_name = serialized.get("name", "UnknownTool")
        try: self._check_cancellation(f"Tool execution ('{self.current_tool_name}')")
        except AgentCancelledException: self.current_tool_name = None; raise
        
        log_prefix = self._get_log_prefix()
        log_input_summary = input_str[:150] + "..." if len(str(input_str)) > 150 else input_str
        monitor_log_content = f"[Tool Start] Using tool '{self.current_tool_name}' with input: '{input_str}'"
        tool_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{self.current_tool_name.upper()}_START"
        
        await self.send_ws_message("monitor_log", { "text": f"{log_prefix} {monitor_log_content}", "log_source": tool_log_source })
        
        user_friendly_tool_name = self.current_tool_name.replace("_", " ").title()
        await self._send_thinking_update( # This will be a SUB_STATUS message
            message_text=f"Using {user_friendly_tool_name}...",
            status_key="TOOL_USING", # Frontend might not use status_key for sub-statuses
            component_hint=f"{LOG_SOURCE_TOOL_PREFIX}_{self.current_tool_name.upper()}",
            sub_type=SUB_TYPE_SUB_STATUS, # Display as a new sub-status line
            details={"tool_name": self.current_tool_name, "input_summary": log_input_summary}
        )
        # Save tool input to DB (as before, but using helper)
        await self._save_message_to_db(f"tool_input_{self.current_tool_name}", {"tool_name": self.current_tool_name, "input": input_str})


    async def on_tool_end(self, output: str, name: str = "UnknownTool", **kwargs: Any) -> None:
        tool_name_for_log = name
        if name == "UnknownTool" and self.current_tool_name: tool_name_for_log = self.current_tool_name
        
        log_prefix = self._get_log_prefix()
        output_str = str(output)
        monitor_output_summary = output_str[:1000] + "..." if len(output_str) > 1000 else output_str
        log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' returned:\n---\n{monitor_output_summary.strip()}\n---"
        final_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{tool_name_for_log.upper()}_OUTPUT"

        success_prefix = "SUCCESS::write_file:::" # Specific to write_file tool
        if tool_name_for_log == "write_file" and output_str.startswith(success_prefix):
            try:
                if len(output_str) > len(success_prefix):
                    relative_path_str = output_str[len(success_prefix):]
                    await self._save_message_to_db("artifact_generated", {"path": relative_path_str, "tool": tool_name_for_log})
                    await self.send_ws_message("monitor_log", {
                        "text": f"{log_prefix} [{LOG_SOURCE_ARTIFACT.upper()}_GENERATED] {relative_path_str} (via {tool_name_for_log})",
                        "log_source": f"{LOG_SOURCE_ARTIFACT}_{tool_name_for_log.upper()}"
                    })
                    log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' successfully wrote file: '{relative_path_str}'"
                    if self.current_task_id:
                        await self.send_ws_message("trigger_artifact_refresh", {"taskId": self.current_task_id})
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
        
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {log_content_tool_end}", "log_source": final_log_source})
        
        user_friendly_tool_name = tool_name_for_log.replace("_", " ").title()
        await self._send_thinking_update( # This will be a SUB_STATUS message
            message_text=f"{user_friendly_tool_name} finished.",
            status_key="TOOL_COMPLETED",
            component_hint=f"{LOG_SOURCE_TOOL_PREFIX}_{tool_name_for_log.upper()}",
            sub_type=SUB_TYPE_SUB_STATUS, # Display as a new sub-status line
            details={"tool_name": tool_name_for_log, "output_summary": output_str[:100]+"..." if output_str else "No output."}
        )
        await self._save_message_to_db(f"tool_output_{tool_name_for_log}", {"tool_name": tool_name_for_log, "output": output_str})
        self.current_tool_name = None

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "UnknownTool", **kwargs: Any) -> None:
        actual_tool_name = name
        if name == "UnknownTool" and self.current_tool_name: actual_tool_name = self.current_tool_name
        
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__; error_str = str(error)
        user_friendly_tool_name = actual_tool_name.replace("_", " ").title()
        tool_error_log_source = f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_ERROR"
        
        if isinstance(error, AgentCancelledException):
            logger.warning(f"[{self.session_id}] Tool '{actual_tool_name}' execution cancelled by AgentCancelledException.")
            await self._send_thinking_update(
                message_text=f"Tool {user_friendly_tool_name} cancelled.",
                status_key="TOOL_CANCELLED",
                component_hint=f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_CANCELLED",
                sub_type=SUB_TYPE_SUB_STATUS # Show as a sub-status
            )
            await self.send_ws_message("monitor_log", {
                "text": f"{log_prefix} [Tool Cancelled] Tool '{actual_tool_name}' execution stopped by user request.",
                "log_source": f"{LOG_SOURCE_TOOL_PREFIX}_{actual_tool_name.upper()}_CANCELLED"
            })
            self.current_tool_name = None
            raise error

        logger.error(f"[{self.session_id}] Tool '{actual_tool_name}' Error: {error_str}", exc_info=True)
        monitor_error_content = f"[Tool Error] Tool '{actual_tool_name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {monitor_error_content}", "log_source": tool_error_log_source})
        
        await self._send_thinking_update( # This will be a SUB_STATUS message
            message_text=f"Error with {user_friendly_tool_name}. (Retrying or evaluating next steps...)",
            status_key="TOOL_ERROR",
            component_hint=tool_error_log_source,
            sub_type=SUB_TYPE_SUB_STATUS, # Show as a sub-status
            details={"tool_name": actual_tool_name, "error_type": error_type_name, "error_message": error_str[:200]}
        )
        await self._save_message_to_db(f"error_tool_{actual_tool_name}", {"tool_name": actual_tool_name, "error_type": error_type_name, "error_message": error_str})
        self.current_tool_name = None

    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        thought_content = ""
        if action.log:
            thought_match = re.search(r"Thought:(.*?)(Action:|$)", action.log, re.S | re.IGNORECASE)
            if thought_match: thought_content = thought_match.group(1).strip()
        
        if thought_content:
            # Send thought as a distinct "thought" message
            await self._send_thinking_update(
                message_text=thought_content, # This is the markdown content for the thought
                status_key="AGENT_THOUGHT", # Frontend might not use status_key for thoughts
                component_hint=LOG_SOURCE_EXECUTOR,
                sub_type=SUB_TYPE_THOUGHT,
                thought_label="Executor thought:" # Label for the thought box
            )
            # Also log to monitor
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought] {thought_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_THOUGHT"})
            # No need to call _save_message_to_db here, _send_thinking_update handles it for thoughts

        action_details_log = f"[Executor Action] Action: {action.tool}, Input: {str(action.tool_input)[:500]}"
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} {action_details_log}", "log_source": f"{LOG_SOURCE_EXECUTOR}_ACTION"})
        
        # This provides a generic "processing" update to the bottom line if no tool_start follows immediately
        await self._send_thinking_update(
            message_text="Processing action...",
            status_key="AGENT_EXECUTING_LOGIC",
            component_hint=LOG_SOURCE_EXECUTOR,
            sub_type=SUB_TYPE_BOTTOM_LINE
        )

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        log_prefix = self._get_log_prefix()
        final_thought_in_step_content = ""
        if finish.log:
            thought_match = re.search(r"Thought:(.*?)(Final Answer:)", finish.log, re.S | re.IGNORECASE)
            if thought_match: final_thought_in_step_content = thought_match.group(1).strip()
        
        if final_thought_in_step_content:
            await self._send_thinking_update(
                message_text=final_thought_in_step_content,
                status_key="AGENT_FINAL_THOUGHT",
                component_hint=LOG_SOURCE_EXECUTOR,
                sub_type=SUB_TYPE_THOUGHT,
                thought_label="Executor final thought for step:"
            )
            await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Thought Final Step] {final_thought_in_step_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_THOUGHT_FINAL"})

        step_output_content = finish.return_values.get("output", "No specific output from agent step.")
        if not isinstance(step_output_content, str): step_output_content = str(step_output_content)
            
        await self.send_ws_message("monitor_log", {"text": f"{log_prefix} [Executor Step Output] {step_output_content}", "log_source": f"{LOG_SOURCE_EXECUTOR}_STEP_OUTPUT"})
        await self._save_message_to_db("agent_executor_step_finish", {"output": step_output_content}) # Save structured output

        await self._send_thinking_update( # This will be a SUB_STATUS message
            message_text="Agent processing step complete.",
            status_key="EXECUTOR_STEP_COMPLETED",
            component_hint=LOG_SOURCE_EXECUTOR,
            sub_type=SUB_TYPE_SUB_STATUS
        )
        self.current_tool_name = None

    async def on_text(self, text: str, **kwargs: Any) -> Any: pass
    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any: pass
    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any: pass
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any: pass

