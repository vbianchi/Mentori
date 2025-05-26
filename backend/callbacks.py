import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Sequence, Callable, Coroutine
from uuid import UUID
import json
import os # Not strictly needed by this file after path moved
import re

# LangChain Core Imports
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult, ChatGenerationChunk, GenerationChunk
from langchain_core.messages import BaseMessage, AIMessageChunk
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document

# Project Imports
from backend.config import settings
# from backend.tools import TEXT_EXTENSIONS, get_task_workspace_path # Not directly used here

logger = logging.getLogger(__name__)

# --- Define Custom Exception for Cancellation ---
class AgentCancelledException(Exception):
    """Custom exception to signal agent cancellation via callbacks."""
    pass
# ---------------------------------------------

# Define type hints
AddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]


class WebSocketCallbackHandler(AsyncCallbackHandler):
    """
    Async Callback handler for LangChain agent events.
    - Sends concise thinking status updates to the chat UI.
    - Sends final agent messages (determined by agent_flow_handlers) to the chat UI.
    - Sends detailed monitor logs for all steps.
    - Extracts and sends LLM token usage.
    - Handles cancellation requests.
    - Logs artifact creation from write_file and triggers UI refresh.
    - Saves relevant events to the database.
    """
    always_verbose: bool = True # Set to True to get all events, even if not explicitly handled
    ignore_llm: bool = False
    ignore_chain: bool = True # Usually too verbose for chains unless specifically needed
    ignore_agent: bool = False
    ignore_retriever: bool = True
    ignore_chat_model: bool = False

    def __init__(self, session_id: str, send_ws_message_func: SendWSMessageFunc, db_add_message_func: AddMessageFunc, session_data_ref: Dict[str, Any]):
        super().__init__()
        self.session_id = session_id
        self.send_ws_message = send_ws_message_func
        self.db_add_message = db_add_message_func
        self.session_data = session_data_ref # Shared dict for session-specific data like cancellation flags
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
            # This case should ideally not happen if session_data is managed correctly
            logger.error(f"[{self.session_id}] Cannot check cancellation flag: Session data not found for session in shared dict.")


    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        try:
            self._check_cancellation("LLM execution")
        except AgentCancelledException:
            raise # Re-raise to stop LangChain processing
        
        # Attempt to identify role for better status message (simplified)
        # llm_role = kwargs.get('invocation_params', {}).get('_tags', []) # This might not always be present or easy to parse
        # role_str = f" ({llm_role[0]})" if llm_role else ""
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_PROCESSING", "message": "Agent is thinking..."})
        # Detailed prompt logging (if desired) should go to monitor_log
        # For example:
        # log_content = f"[LLM Start] Prompts: {str(prompts)[:500]}..." # Be careful with prompt length
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} {log_content}")


    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        try:
            self._check_cancellation("Chat Model execution")
        except AgentCancelledException:
            raise
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_PROCESSING", "message": "Agent is thinking..."})
        # monitor_log_content = f"[Chat Model Start] Messages: {str(messages)[:500]}..."
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} {monitor_log_content}")

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        # Could be used for streaming to UI if implemented later
        pass

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix()
        logger.debug(f"[{self.session_id}] on_llm_end received response. Run ID: {run_id}")

        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        total_tokens: Optional[int] = None
        model_name: str = "unknown_model"
        source_for_tokens = "unknown"

        try: # Token parsing logic (remains the same as provided initially)
            if response.llm_output and isinstance(response.llm_output, dict):
                llm_output_data = response.llm_output
                source_for_tokens = "llm_output"
                model_name = llm_output_data.get('model_name', llm_output_data.get('model', model_name))
                if 'token_usage' in llm_output_data and isinstance(llm_output_data['token_usage'], dict):
                    usage_dict = llm_output_data['token_usage']
                    input_tokens = usage_dict.get('prompt_tokens', usage_dict.get('input_tokens'))
                    output_tokens = usage_dict.get('completion_tokens', usage_dict.get('output_tokens'))
                    total_tokens = usage_dict.get('total_tokens')
                elif 'usage_metadata' in llm_output_data and isinstance(llm_output_data['usage_metadata'], dict): # Gemini
                    usage_dict = llm_output_data['usage_metadata']
                    input_tokens = usage_dict.get('prompt_token_count')
                    output_tokens = usage_dict.get('candidates_token_count')
                    total_tokens = usage_dict.get('total_token_count')
                elif 'eval_count' in llm_output_data: # Ollama
                    output_tokens = llm_output_data.get('eval_count')
                    input_tokens = llm_output_data.get('prompt_eval_count')

            if (input_tokens is None and output_tokens is None) and response.generations:
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
                            elif 'eval_count' in gen_info: # Ollama via generation_info
                                output_tokens = gen_info.get('eval_count')
                                input_tokens = gen_info.get('prompt_eval_count')
                            break
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
            if total_tokens is None: total_tokens = input_tokens + output_tokens
            else: total_tokens = int(total_tokens)

            token_usage_payload = {
                "model_name": str(model_name), "input_tokens": input_tokens,
                "output_tokens": output_tokens, "total_tokens": total_tokens,
                "source": source_for_tokens
            }
            if input_tokens > 0 or output_tokens > 0 or total_tokens > 0:
                usage_str = f"Model: {model_name}, Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens} (Source: {source_for_tokens})"
                log_content_tokens = f"[LLM Token Usage] {usage_str}"
                await self.send_ws_message("monitor_log", f"{log_prefix} {log_content_tokens}")
                await self.send_ws_message("llm_token_usage", token_usage_payload) # For UI display
                await self._save_message("llm_token_usage", json.dumps(token_usage_payload))
                logger.info(f"[{self.session_id}] {log_content_tokens} - Sent to client.")
        except Exception as e:
            logger.error(f"[{self.session_id}] Error processing token usage in on_llm_end: {e}", exc_info=True)
        
        # Clear generic "Agent is thinking..." if an LLM call just finished. More specific status will follow.
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_COMPLETED", "message": "Processing complete."})


    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        logger.error(f"[{self.session_id}] LLM Error: {error}", exc_info=True)
        error_content = f"[LLM Error] {error_type_name}: {error}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {error_content}")
        await self.send_ws_message("status_message", "Error during LLM call.") # This is a chat message
        await self.send_ws_message("agent_thinking_update", {"status_key": "LLM_ERROR", "message": "Error during LLM call."})
        await self._save_message("error_llm", error_content)

    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        # chain_name = serialized.get("name", "Unknown Chain")
        # await self.send_ws_message("agent_thinking_update", {"status_key": "CHAIN_START", "message": f"Starting: {chain_name}..."})
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Chain Start] Name: {chain_name}, Inputs: {str(inputs)[:200]}...")
        pass 

    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        # chain_name = kwargs.get("name", "Unknown Chain") # Name might be in kwargs for on_chain_end
        # await self.send_ws_message("agent_thinking_update", {"status_key": "CHAIN_END", "message": f"Finished: {chain_name}."})
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Chain End] Name: {chain_name}, Outputs: {str(outputs)[:200]}...")
        pass
        
    async def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        # chain_name = kwargs.get("name", "Unknown Chain")
        # error_type_name = type(error).__name__
        # error_content = f"[Chain Error] Name: {chain_name} - {error_type_name}: {error}"
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} {error_content}")
        # await self.send_ws_message("status_message", f"Error in chain: {chain_name}.")
        # await self.send_ws_message("agent_thinking_update", {"status_key": "CHAIN_ERROR", "message": f"Error in {chain_name}."})
        pass


    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        self.current_tool_name = serialized.get("name", "Unknown Tool")
        try:
            self._check_cancellation(f"Tool execution ('{self.current_tool_name}')")
        except AgentCancelledException:
            self.current_tool_name = None 
            raise
        
        log_prefix = self._get_log_prefix()
        log_input_summary = input_str[:150] + "..." if len(str(input_str)) > 150 else input_str
        
        # Monitor Log: Detailed
        monitor_log_content = f"[Tool Start] Using tool '{self.current_tool_name}' with input: '{input_str}'" # Full input to monitor
        await self.send_ws_message("monitor_log", f"{log_prefix} {monitor_log_content}")
        
        # Agent Thinking Update: Concise
        # TODO: Consider a mapping for more user-friendly tool names if needed
        user_friendly_tool_name = self.current_tool_name.replace("_", " ").title()
        await self.send_ws_message("agent_thinking_update", {
            "status_key": "TOOL_USING", 
            "message": f"Using {user_friendly_tool_name}...",
            "details": {"tool_name": self.current_tool_name, "input_summary": log_input_summary}
        })
        
        await self._save_message("tool_input", f"{self.current_tool_name}:::{input_str}") # Save full input

    async def on_tool_end(self, output: str, name: str = "Unknown Tool", **kwargs: Any) -> None:
        tool_name_for_log = name
        if name == "Unknown Tool" and self.current_tool_name:
            tool_name_for_log = self.current_tool_name
        
        log_prefix = self._get_log_prefix()
        output_str = str(output)
        logger.info(f"[{self.session_id}] Tool '{tool_name_for_log}' finished. Output length: {len(output_str)}")

        # Monitor Log: Detailed
        # Sanitize output for monitor log if extremely long, but generally log full output.
        monitor_output_summary = output_str[:1000] + "..." if len(output_str) > 1000 else output_str
        formatted_monitor_output = f"\n---\n{monitor_output_summary.strip()}\n---"
        log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' returned:{formatted_monitor_output}" # Full output to monitor
        
        # Handle artifact generation specifically for write_file
        success_prefix = "SUCCESS::write_file:::"
        if tool_name_for_log == "write_file" and output_str.startswith(success_prefix):
            try:
                if len(output_str) > len(success_prefix):
                    relative_path_str = output_str[len(success_prefix):]
                    logger.info(f"[{self.session_id}] Detected successful write_file: '{relative_path_str}'")
                    await self._save_message("artifact_generated", relative_path_str) # DB log
                    # Add to monitor log as well
                    await self.send_ws_message("monitor_log", f"{log_prefix} [ARTIFACT_GENERATED] {relative_path_str} (via {tool_name_for_log})")
                    log_content_tool_end = f"[Tool Output] Tool '{tool_name_for_log}' successfully wrote file: '{relative_path_str}'" # More specific monitor log
                    if self.current_task_id:
                        logger.info(f"[{self.session_id}] Triggering artifact refresh for task {self.current_task_id} after {tool_name_for_log}.")
                        await self.send_ws_message("trigger_artifact_refresh", {"taskId": self.current_task_id})
                else:
                    logger.warning(f"[{self.session_id}] write_file output matched prefix but had no filename: '{output_str}'")
            except Exception as parse_err:
                logger.error(f"[{self.session_id}] Error processing write_file success output '{output_str}': {parse_err}", exc_info=True)
        
        await self.send_ws_message("monitor_log", f"{log_prefix} {log_content_tool_end}")
        
        # Agent Thinking Update: Concise
        user_friendly_tool_name = tool_name_for_log.replace("_", " ").title()
        await self.send_ws_message("agent_thinking_update", {
            "status_key": "TOOL_COMPLETED", 
            "message": f"{user_friendly_tool_name} finished.",
            "details": {"tool_name": tool_name_for_log, "output_summary": output_str[:100]+"..." if output_str else "No output."}
        })
        
        await self._save_message("tool_output", output_str) # Save full output to DB
        self.current_tool_name = None 

    async def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str = "Unknown Tool", **kwargs: Any) -> None:
        actual_tool_name = name
        if name == "Unknown Tool" and self.current_tool_name:
            actual_tool_name = self.current_tool_name
        
        if isinstance(error, AgentCancelledException): # This is a controlled stop
            logger.warning(f"[{self.session_id}] Tool '{actual_tool_name}' execution cancelled by AgentCancelledException.")
            await self.send_ws_message("agent_thinking_update", {"status_key": "TOOL_CANCELLED", "message": f"Tool {actual_tool_name} cancelled."})
            # No 'status_message' to chat for graceful cancel, monitor log is enough
            await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Tool Cancelled] Tool '{actual_tool_name}' execution stopped by user request.")
            self.current_tool_name = None 
            raise error # Re-raise to stop LangChain processing

        log_prefix = self._get_log_prefix(); error_type_name = type(error).__name__
        error_str = str(error)
        
        logger.error(f"[{self.session_id}] Tool '{actual_tool_name}' Error: {error_str}", exc_info=True)
        
        # Monitor Log: Detailed
        monitor_error_content = f"[Tool Error] Tool '{actual_tool_name}' failed: {error_type_name}: {error_str}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {monitor_error_content}")
        
        # Status Message to Chat: Concise
        await self.send_ws_message("status_message", f"Error with tool: {actual_tool_name}.")
        
        # Agent Thinking Update: Concise
        user_friendly_tool_name = actual_tool_name.replace("_", " ").title()
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
        # Simplified thought extraction, focusing on the thought leading to the current action
        if action.log:
            log_lines = action.log.strip().split('\n')
            # Regex to find the last "Thought:" before an "Action:"
            thought_match = re.search(r"Thought:(.*?)(Action:|$)", action.log, re.S | re.IGNORECASE)
            if thought_match:
                thought = thought_match.group(1).strip()
        
        # Monitor Log: Detailed agent thought and action
        if thought:
            logger.debug(f"[{self.session_id}] Extracted thought (Action): {thought}")
            await self.send_ws_message("monitor_log", f"{log_prefix} [AGENT_THOUGHT_ACTION] {thought}")
        
        action_details_log = f"[AGENT_ACTION] Action: {action.tool}, Input: {str(action.tool_input)[:500]}"
        await self.send_ws_message("monitor_log", f"{log_prefix} {action_details_log}")
        
        # Agent Thinking Update: Very generic, as on_tool_start will provide more specifics if a tool is called.
        # If no tool is called (e.g., LLM tries to answer directly after a thought), this might be the only update.
        await self.send_ws_message("agent_thinking_update", {"status_key": "AGENT_PROCESSING_ACTION", "message": "Processing..."})
        
        if thought: await self._save_message("agent_thought_action", thought)
        # Action and input are implicitly saved via on_tool_start if a tool is used.

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        # This 'finish' is for the ReAct agent's current step execution.
        # The 'output' here is what the Executor returns to the Controller/StepEvaluator.
        # It's NOT necessarily the final message to the user.
        log_prefix = self._get_log_prefix()
        logger.info(f"[{self.session_id}] Agent Executor Step Finish. Log: {finish.log}")

        final_thought_in_step = ""
        if finish.log:
            # Regex to find the last "Thought:" before "Final Answer:"
            thought_match = re.search(r"Thought:(.*?)(Final Answer:)", finish.log, re.S | re.IGNORECASE)
            if thought_match:
                final_thought_in_step = thought_match.group(1).strip()
        
        # Monitor Log: Detailed final thought and step output
        if final_thought_in_step:
            logger.debug(f"[{self.session_id}] Extracted final thought for step: {final_thought_in_step}")
            await self.send_ws_message("monitor_log", f"{log_prefix} [AGENT_THOUGHT_FINAL_STEP] {final_thought_in_step}")
        
        step_output_content = finish.return_values.get("output", "No specific output from agent step.")
        if not isinstance(step_output_content, str):
            step_output_content = str(step_output_content)
            
        await self.send_ws_message("monitor_log", f"{log_prefix} [EXECUTOR_STEP_OUTPUT] {step_output_content}")
        await self._save_message("agent_executor_step_finish", step_output_content) # Save step output to DB

        # Agent Thinking Update: Signal step completion
        await self.send_ws_message("agent_thinking_update", {"status_key": "EXECUTOR_STEP_COMPLETED", "message": "Agent processing step complete."})
        
        # DO NOT send agent_message or status_message("Task processing complete") here.
        # This will be handled by the main agent flow (agent_flow_handlers.py) after evaluation.
        logger.info(f"[{self.session_id}] Executor step output logged. Main flow will handle user-facing messages.")
        self.current_tool_name = None


    async def on_text(self, text: str, **kwargs: Any) -> Any:
        # This callback is for generic text from the LLM, not usually a primary part of ReAct flow output.
        # Could be useful for debugging if unexpected text appears.
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [LLM Text] {text}")
        pass

    async def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> Any:
        # await self.send_ws_message("agent_thinking_update", {"status_key": "RETRIEVER_START", "message": f"Searching documents for: {query[:50]}..."})
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Retriever Start] Query: {query}")
        pass

    async def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any:
        # await self.send_ws_message("agent_thinking_update", {"status_key": "RETRIEVER_END", "message": f"Found {len(documents)} documents."})
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} [Retriever End] Found {len(documents)} documents. First doc: {str(documents[0])[:200]}..." if documents else "No documents found.")
        pass
        
    async def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        # error_type_name = type(error).__name__
        # error_content = f"[Retriever Error] {error_type_name}: {error}"
        # await self.send_ws_message("monitor_log", f"{self._get_log_prefix()} {error_content}")
        # await self.send_ws_message("status_message", "Error during document retrieval.")
        # await self.send_ws_message("agent_thinking_update", {"status_key": "RETRIEVER_ERROR", "message": "Error retrieving documents."})
        pass

