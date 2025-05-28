# backend/message_processing/agent_flow_handlers.py
import logging
import json
import datetime
from typing import Dict, Any, Callable, Coroutine, Optional, List
import asyncio
from pathlib import Path
import aiofiles
import re
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.callbacks.base import BaseCallbackHandler 

from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path
from backend.planner import generate_plan, PlanStep
from backend.controller import validate_and_prepare_step_action
from backend.agent import create_agent_executor
from backend.callbacks import (
    WebSocketCallbackHandler, 
    AgentCancelledException, 
    SUB_TYPE_BOTTOM_LINE, SUB_TYPE_SUB_STATUS, SUB_TYPE_THOUGHT, 
    DB_MSG_TYPE_SUB_STATUS, DB_MSG_TYPE_THOUGHT,
    LOG_SOURCE_INTENT_CLASSIFIER, LOG_SOURCE_PLANNER, LOG_SOURCE_CONTROLLER,
    LOG_SOURCE_EXECUTOR, LOG_SOURCE_EVALUATOR_STEP, LOG_SOURCE_EVALUATOR_OVERALL,
    LOG_SOURCE_SYSTEM, LOG_SOURCE_LLM_CORE 
)
from backend.intent_classifier import classify_intent
from backend.evaluator import (
    evaluate_plan_outcome, EvaluationResult,
    evaluate_step_outcome_and_suggest_correction, StepCorrectionOutcome
)

logger = logging.getLogger(__name__)

SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]

MAX_STEP_RETRIES = settings.agent_max_step_retries
DB_MSG_TYPE_MAJOR_STEP = "db_major_step_announcement"

async def _save_message_to_db_from_handler(
    task_id: Optional[str], session_id: str, db_add_message_func: DBAddMessageFunc,
    message_type: str, content_data: Any
):
    if task_id:
        try:
            content_str = json.dumps(content_data) if isinstance(content_data, dict) else str(content_data)
            await db_add_message_func(task_id, session_id, message_type, content_str)
        except Exception as e:
            logger.error(f"[{session_id}] Handler DB save error (Task: {task_id}, Type: {message_type}): {e}", exc_info=True)

async def _send_thinking_update_from_handler(
    send_ws_message_func: SendWSMessageFunc, task_id: Optional[str], session_id: str,
    db_add_message_func: DBAddMessageFunc, message_text: str, status_key: str,
    component_hint: str, sub_type: str = SUB_TYPE_BOTTOM_LINE,
    details: Optional[Dict] = None, thought_label: Optional[str] = None
):
    payload = {
        "status_key": status_key, "message": message_text,
        "component_hint": component_hint, "sub_type": sub_type,
    }
    if details: payload["details"] = details
    if sub_type == SUB_TYPE_THOUGHT and thought_label:
        payload["message"] = { "label": thought_label, "content_markdown": message_text }

    await send_ws_message_func("agent_thinking_update", payload)

    if task_id and session_id and (sub_type == SUB_TYPE_SUB_STATUS or sub_type == SUB_TYPE_THOUGHT) :
        db_type = DB_MSG_TYPE_SUB_STATUS if sub_type == SUB_TYPE_SUB_STATUS else DB_MSG_TYPE_THOUGHT
        db_content = {"message_text": message_text, "component_hint": component_hint} if sub_type == SUB_TYPE_SUB_STATUS \
                     else {"thought_label": thought_label, "thought_content_markdown": message_text, "component_hint": component_hint}
        await _save_message_to_db_from_handler(task_id, session_id, db_add_message_func, db_type, db_content)

async def _update_plan_file_step_status(
    task_workspace_path: Path, 
    plan_filename: str, 
    step_number: int, 
    status_char: str,
    current_task_id: Optional[str], 
    send_ws_message_func: Optional[SendWSMessageFunc] 
) -> None:
    if not plan_filename: return
    plan_file_path = task_workspace_path / plan_filename
    if not await asyncio.to_thread(plan_file_path.exists): return
    try:
        async with aiofiles.open(plan_file_path, 'r', encoding='utf-8') as f_read: lines = await f_read.readlines()
        updated_lines = []
        found_step = False
        step_pattern = re.compile(rf"^\s*-\s*\[\s*[ x!-]?\s*\]\s*{re.escape(str(step_number))}\.\s+.*", re.IGNORECASE)
        checkbox_pattern = re.compile(r"(\s*-\s*\[)\s*[ x!-]?\s*(\])") 
        for line_content in lines:
            if not found_step and step_pattern.match(line_content):
                updated_lines.append(checkbox_pattern.sub(rf"\g<1>{status_char}\g<2>", line_content, count=1))
                found_step = True
            else:
                updated_lines.append(line_content)
        if found_step:
            async with aiofiles.open(plan_file_path, 'w', encoding='utf-8') as f_write: await f_write.writelines(updated_lines)
            logger.info(f"Updated plan file '{plan_file_path.name}' for step {step_number} with status '{status_char}'.")
            if current_task_id and send_ws_message_func:
                # <<< START MODIFICATION - Added debug log >>>
                logger.critical(f"DEBUG_ARTIFACT_REFRESH: [agent_flow_handlers.py/_update_plan_file_step_status] Plan file '{plan_filename}' updated. About to send 'trigger_artifact_refresh' for task {current_task_id}")
                # <<< END MODIFICATION >>>
                await send_ws_message_func("trigger_artifact_refresh", {"taskId": current_task_id})
        else: 
            logger.warning(f"Step {step_number} pattern not found in plan file {plan_file_path} for status update. Regex: {step_pattern.pattern}")
    except Exception as e: 
        logger.error(f"Error updating plan file {plan_file_path} for step {step_number}: {e}", exc_info=True)

async def process_user_message(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc
) -> None:
    content_payload = data.get("content")
    user_input_content = content_payload if isinstance(content_payload, str) else (content_payload.get('content') if isinstance(content_payload, dict) and isinstance(content_payload.get('content'), str) else "")
    if not user_input_content: return logger.warning(f"[{session_id}] Empty user message.")

    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id:
        return await send_ws_message_func("status_message", {"text": "Please select or create a task first.", "component_hint": LOG_SOURCE_SYSTEM, "isError": True})
    if connected_clients_entry.get("agent_task") or session_data_entry.get("plan_execution_active"):
        return await send_ws_message_func("status_message", {"text": "Agent is busy. Please wait or stop the current process.", "component_hint": LOG_SOURCE_SYSTEM})

    await db_add_message_func(active_task_id, session_id, "user_input", user_input_content)
    await add_monitor_log_func(f"User Input: {user_input_content}", "monitor_user_input")

    session_data_entry.update({'original_user_query': user_input_content, 'cancellation_requested': False, 'active_plan_filename': None, 'current_plan_proposal_id_backend': None})
    
    retrieved_callback_handler: Optional[WebSocketCallbackHandler] = session_data_entry.get("callback_handler")
    logger.critical(f"CRITICAL_DEBUG: AGENT_FLOW_HANDLER (process_user_message) - Retrieved 'callback_handler' from session_data_entry. Type: {type(retrieved_callback_handler).__name__ if retrieved_callback_handler else 'None'}. Is it None? {retrieved_callback_handler is None}")
    
    callbacks_for_invoke: List[BaseCallbackHandler] = []
    if not retrieved_callback_handler: 
        logger.error(f"[{session_id}] Callback handler NOT FOUND in session_data_entry for process_user_message. Token counting for some roles may fail.")
    else:
        callbacks_for_invoke.append(retrieved_callback_handler)
        logger.critical(f"CRITICAL_DEBUG: AGENT_FLOW_HANDLER (process_user_message) - Populated callbacks_for_invoke with: {[type(cb).__name__ for cb in callbacks_for_invoke]}")

    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Classifying intent...", "INTENT_CLASSIFICATION_START", LOG_SOURCE_INTENT_CLASSIFIER, SUB_TYPE_SUB_STATUS)
    dynamic_tools = get_dynamic_tools(active_task_id)
    tools_summary = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])
    
    classified_intent = await classify_intent(
        user_input_content, 
        tools_summary,
        retrieved_callback_handler 
    )

    await add_monitor_log_func(f"Intent classified as: {classified_intent}", f"{LOG_SOURCE_SYSTEM}_INTENT_CLASSIFIED")
    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Intent: {classified_intent}", "INTENT_CLASSIFIED", LOG_SOURCE_INTENT_CLASSIFIER, SUB_TYPE_SUB_STATUS)

    if classified_intent == "PLAN":
        await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Generating plan...", "PLAN_GENERATION_START", LOG_SOURCE_PLANNER, SUB_TYPE_SUB_STATUS)
        human_summary, steps = await generate_plan(
            user_input_content, 
            tools_summary,
            retrieved_callback_handler 
        )
        if human_summary and steps:
            plan_id = str(uuid.uuid4())
            session_data_entry.update({"current_plan_proposal_id_backend": plan_id, "current_plan_human_summary": human_summary, "current_plan_structured": steps})
            plan_proposal_filename = f"_plan_proposal_{plan_id}.md"
            task_workspace_path = get_task_workspace_path(active_task_id, create_if_not_exists=True)
            plan_proposal_markdown_content = [f"# Agent Plan Proposal\n\n## Plan ID: {plan_id}\n## Original User Query:\n{user_input_content}\n## Proposed Plan Summary:\n{human_summary}\n## Proposed Steps:\n"]
            for i, step_data_dict in enumerate(steps):
                desc = step_data_dict.get('description', 'N/A'); tool_sugg = step_data_dict.get('tool_to_use', 'None')
                input_instr = step_data_dict.get('tool_input_instructions', 'None'); expected_out = step_data_dict.get('expected_outcome', 'N/A')
                plan_proposal_markdown_content.append(f"{i+1}. **{desc}**\n    - Tool Suggestion: `{tool_sugg}`\n    - Input Instructions: `{input_instr}`\n    - Expected Outcome: `{expected_out}`\n")
            try:
                proposal_file_path = task_workspace_path / plan_proposal_filename
                async with aiofiles.open(proposal_file_path, 'w', encoding='utf-8') as f: await f.write("\n".join(plan_proposal_markdown_content))
                logger.critical(f"DEBUG_ARTIFACT_REFRESH: [agent_flow_handlers.py/process_user_message] Plan proposal '{plan_proposal_filename}' saved. About to send 'trigger_artifact_refresh' for task {active_task_id}")
                await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id}) 
            except Exception as e: logger.error(f"[{session_id}] Failed to save plan proposal artifact '{plan_proposal_filename}': {e}")

            await send_ws_message_func("propose_plan_for_confirmation", {"plan_id": plan_id, "human_summary": human_summary, "structured_plan": steps})
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Awaiting plan confirmation...", "AWAITING_PLAN_CONFIRMATION", LOG_SOURCE_SYSTEM, SUB_TYPE_BOTTOM_LINE)
        else:
            await send_ws_message_func("status_message", {"text": "Error: Could not generate a plan.", "component_hint": LOG_SOURCE_PLANNER, "isError": True})
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Planning failed.", "PLAN_FAILED", LOG_SOURCE_PLANNER, SUB_TYPE_BOTTOM_LINE)
    elif classified_intent == "DIRECT_QA":
        direct_qa_role_hint = LOG_SOURCE_EXECUTOR + "_DirectQA" 
        await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Processing directly...", "DIRECT_QA_START", direct_qa_role_hint, SUB_TYPE_BOTTOM_LINE)
        executor_llm = get_llm(
            settings, 
            provider=session_data_entry.get("selected_llm_provider", settings.executor_default_provider), 
            model_name=session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name), 
            requested_for_role=direct_qa_role_hint,
            callbacks=callbacks_for_invoke 
        )
        agent_executor = create_agent_executor(llm=executor_llm, tools=get_dynamic_tools(active_task_id), memory=session_data_entry["memory"], max_iterations=settings.agent_max_iterations) 
        final_state = "DIRECT_QA_FAILED"; final_msg = "Direct QA error." 
        try:
            result = await agent_executor.ainvoke(
                {"input": user_input_content}, 
                config=RunnableConfig(
                    callbacks=callbacks_for_invoke, 
                    metadata={"component_name": direct_qa_role_hint} 
                )
            )
            if result and 'output' in result:
                await send_ws_message_func("agent_message", {"content": result['output'], "component_hint": direct_qa_role_hint})
                await db_add_message_func(active_task_id, session_id, "agent_message", result['output'])
                final_state = "DIRECT_QA_COMPLETED"; final_msg = "Direct response generated."
            else:
                 logger.warning(f"[{session_id}] Direct QA finished but no output in result: {result}")
                 final_msg = "Direct QA completed without specific output." 
        except AgentCancelledException:
            final_state = "CANCELLED"; final_msg = "Direct QA cancelled."
            await send_ws_message_func("status_message", {"text": final_msg, "component_hint": LOG_SOURCE_SYSTEM})
        except Exception as e:
            logger.error(f"[{session_id}] Direct QA error: {e}", exc_info=True)
            final_msg = f"Direct QA error: {type(e).__name__}"
            await send_ws_message_func("status_message", {"text": final_msg, "component_hint": direct_qa_role_hint, "isError": True})
        finally:
            connected_clients_entry["agent_task"] = None
            session_data_entry['cancellation_requested'] = False
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, final_msg, final_state, direct_qa_role_hint if final_state.startswith("DIRECT") else LOG_SOURCE_SYSTEM, SUB_TYPE_BOTTOM_LINE)


async def process_execute_confirmed_plan(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc
) -> None:
    logger.info(f"[{session_id}] Received 'execute_confirmed_plan' with plan_id: {data.get('plan_id')}")
    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id: return await send_ws_message_func("status_message", {"text": "Error: No active task.", "component_hint": LOG_SOURCE_SYSTEM, "isError": True})

    retrieved_callback_handler: Optional[WebSocketCallbackHandler] = session_data_entry.get("callback_handler")
    logger.critical(f"CRITICAL_DEBUG: AGENT_FLOW_HANDLER (process_execute_confirmed_plan) - Retrieved 'callback_handler' from session_data_entry. Type: {type(retrieved_callback_handler).__name__ if retrieved_callback_handler else 'None'}. Is it None? {retrieved_callback_handler is None}")
    
    callbacks_for_invoke: List[BaseCallbackHandler] = []
    if not retrieved_callback_handler:
        logger.error(f"[{session_id}] Callback handler not found in session_data_entry for process_execute_confirmed_plan. Token counting for some roles may fail.")
    else:
        callbacks_for_invoke.append(retrieved_callback_handler)
        logger.critical(f"CRITICAL_DEBUG: AGENT_FLOW_HANDLER (process_execute_confirmed_plan) - Populated callbacks_for_invoke with: {[type(cb).__name__ for cb in callbacks_for_invoke]}")


    confirmed_plan_id = data.get("plan_id")
    confirmed_steps = data.get("confirmed_plan")
    if not confirmed_steps or not isinstance(confirmed_steps, list) or not confirmed_plan_id:
        return await send_ws_message_func("status_message", {"text": "Error: Invalid plan for execution.", "component_hint": LOG_SOURCE_SYSTEM, "isError": True})

    await db_add_message_func(active_task_id, session_id, "confirmed_plan_log", json.dumps({"plan_id": confirmed_plan_id, "summary": session_data_entry.get("current_plan_human_summary", "N/A"), "steps": confirmed_steps, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}))
    session_data_entry.update({"current_plan_structured": confirmed_steps, "current_plan_step_index": 0, "plan_execution_active": True, 'cancellation_requested': False})
    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Executing plan ({len(confirmed_steps)} steps)...", "PLAN_EXECUTION_START", LOG_SOURCE_SYSTEM, SUB_TYPE_BOTTOM_LINE)

    plan_execution_filename = f"_plan_{confirmed_plan_id}.md"
    session_data_entry['active_plan_filename'] = plan_execution_filename
    task_workspace_path = get_task_workspace_path(active_task_id, create_if_not_exists=True)
    plan_markdown_content_list = [f"# Agent Executed Plan: {confirmed_plan_id}\n## Original Query:\n{session_data_entry.get('original_user_query', 'N/A')}\n## Steps:\n"]
    for i, step_data in enumerate(confirmed_steps):
        plan_markdown_content_list.append(f"- [ ] {i+1}. **{step_data.get('description')}** (Planner Tool: {step_data.get('tool_to_use', 'None')}, Expected: {step_data.get('expected_outcome')})\n")
    try:
        async with aiofiles.open(task_workspace_path / plan_execution_filename, 'w', encoding='utf-8') as f:
            await f.write("".join(plan_markdown_content_list))
        logger.critical(f"DEBUG_ARTIFACT_REFRESH: [agent_flow_handlers.py/process_execute_confirmed_plan] Main plan file '{plan_execution_filename}' saved. About to send 'trigger_artifact_refresh' for task {active_task_id}")
        await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id}) 
    except Exception as e: logger.error(f"Error saving execution plan artifact: {e}")

    plan_failed = False
    final_eval_answer = "Plan completed." 
    last_successful_step_output: Optional[str] = None
    original_user_query = session_data_entry.get("original_user_query", "N/A")
    step_execution_summary_for_overall_eval = [] 

    for i, step_data_dict in enumerate(confirmed_steps):
        current_step_num = i + 1
        session_data_entry["current_plan_step_index"] = i
        current_plan_step_obj: Optional[PlanStep] = None
        try: current_plan_step_obj = PlanStep(**step_data_dict)
        except Exception as p_err:
            logger.error(f"[{session_id}] Invalid step data for step {current_step_num}: {p_err}. Data: {step_data_dict}", exc_info=True)
            plan_failed = True; final_eval_answer = f"Error: Plan corrupted at step {current_step_num}."; break
        
        major_step_payload = {"step_number": current_step_num, "total_steps": len(confirmed_steps), "description": current_plan_step_obj.description, "component_hint": LOG_SOURCE_CONTROLLER}
        await send_ws_message_func("agent_major_step_announcement", major_step_payload)
        await _save_message_to_db_from_handler(active_task_id, session_id, db_add_message_func, DB_MSG_TYPE_MAJOR_STEP, major_step_payload)

        if session_data_entry.get('cancellation_requested', False):
            logger.warning(f"[{session_id}] Cancellation detected before step {current_step_num}.")
            plan_failed = True; final_eval_answer = "Plan execution cancelled by user."; break
        
        step_succeeded_this_round = False; retry_count = 0
        current_step_attempt_log = [] 
        effective_plan_step_for_controller = current_plan_step_obj.copy(deep=True)

        while retry_count <= MAX_STEP_RETRIES:
            if session_data_entry.get('cancellation_requested', False): plan_failed = True; final_eval_answer = "Plan execution cancelled by user."; break
            
            attempt_msg = f" (Attempt {retry_count + 1})" if retry_count > 0 else ""
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Controller validating Step {current_step_num}{attempt_msg}", "CONTROLLER_VALIDATING", LOG_SOURCE_CONTROLLER, SUB_TYPE_SUB_STATUS)
            
            tool_name, tool_input, controller_reasoning, confidence = await validate_and_prepare_step_action(
                original_user_query, effective_plan_step_for_controller, get_dynamic_tools(active_task_id), 
                session_data_entry, last_successful_step_output,
                retrieved_callback_handler 
            )
            current_step_attempt_log.append(f"Attempt {retry_count+1}: Controller decided Tool='{tool_name}', Input='{str(tool_input)[:50]}...', Confidence={confidence:.2f}. Reasoning: {controller_reasoning}")
            if controller_reasoning and len(controller_reasoning) > 10: 
                 await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, controller_reasoning, "CONTROLLER_THOUGHT", LOG_SOURCE_CONTROLLER, SUB_TYPE_THOUGHT, thought_label=f"Controller reasoning (Step {current_step_num}{attempt_msg}):")

            if tool_name is None and "Error in Controller" in controller_reasoning:
                logger.error(f"[{session_id}] Controller error for step {current_step_num}: {controller_reasoning}")
                plan_failed = True; final_eval_answer = f"Controller error at step {current_step_num}: {controller_reasoning}"; break 

            executor_input_str = f"Your current sub-task is: \"{effective_plan_step_for_controller.description}\".\nThe precise expected output for THIS sub-task is: \"{effective_plan_step_for_controller.expected_outcome}\".\n"
            if tool_name:
                executor_input_str += f"The Controller has determined you MUST use the tool '{tool_name}' with the following exact input: '{tool_input}'. Execute this and report the result."
            else:
                executor_input_str += "The Controller has determined no specific tool is required. Provide a direct answer or perform analysis."
            
            step_executor_output_str = f"Executor error or no output for step {current_step_num}{attempt_msg}." 
            try:
                executor_llm = get_llm(
                    settings, 
                    provider=session_data_entry.get("selected_llm_provider", settings.executor_default_provider), 
                    model_name=session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name),
                    requested_for_role=f"{LOG_SOURCE_EXECUTOR}_Step{current_step_num}",
                    callbacks=callbacks_for_invoke 
                )
                agent_executor_instance = create_agent_executor(llm=executor_llm, tools=get_dynamic_tools(active_task_id), memory=session_data_entry["memory"], max_iterations=settings.agent_max_iterations) 
                
                agent_run_task = asyncio.create_task(agent_executor_instance.ainvoke(
                    {"input": executor_input_str}, 
                    config=RunnableConfig(
                        callbacks=callbacks_for_invoke, 
                        metadata={"component_name": LOG_SOURCE_EXECUTOR} 
                    )
                ))
                connected_clients_entry["agent_task"] = agent_run_task
                executor_result_dict = await agent_run_task
                step_executor_output_str = executor_result_dict.get("output", f"Step {current_step_num}{attempt_msg} completed, no specific output from ReAct agent.")
            except AgentCancelledException:
                logger.warning(f"[{session_id}] Agent execution cancelled during step {current_step_num}{attempt_msg}.")
                plan_failed = True; final_eval_answer = "Plan execution cancelled by user."; break
            except Exception as e:
                logger.error(f"[{session_id}] Step {current_step_num}{attempt_msg} execution error: {e}", exc_info=True)
                step_executor_output_str = f"Error during step {current_step_num}{attempt_msg} execution: {type(e).__name__} - {str(e)[:100]}"
            finally:
                connected_clients_entry["agent_task"] = None
            if plan_failed: break 

            current_step_attempt_log.append(f"Executor Output: {str(step_executor_output_str)[:100]}...")
            
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Step Evaluator assessing Step {current_step_num}{attempt_msg} outcome...", "STEP_EVAL_START", LOG_SOURCE_EVALUATOR_STEP, SUB_TYPE_SUB_STATUS)
            eval_outcome = await evaluate_step_outcome_and_suggest_correction(
                original_user_query, current_plan_step_obj, 
                tool_name, tool_input, step_executor_output_str, 
                get_dynamic_tools(active_task_id), session_data_entry,
                retrieved_callback_handler 
            )
            
            if eval_outcome:
                current_step_attempt_log.append(f"Evaluator: Achieved={eval_outcome.step_achieved_goal}. Assessment: {eval_outcome.assessment_of_step}")
                if eval_outcome.step_achieved_goal:
                    step_succeeded_this_round = True; last_successful_step_output = step_executor_output_str; break 
                elif eval_outcome.is_recoverable_via_retry and retry_count < MAX_STEP_RETRIES:
                    effective_plan_step_for_controller.tool_to_use = eval_outcome.suggested_new_tool_for_retry
                    effective_plan_step_for_controller.tool_input_instructions = eval_outcome.suggested_new_input_instructions_for_retry
                    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Step {current_step_num} failed, attempting retry {retry_count + 1}. Evaluator: {eval_outcome.assessment_of_step}", "STEP_RETRYING", LOG_SOURCE_EVALUATOR_STEP, SUB_TYPE_SUB_STATUS)
                else: 
                    plan_failed = True; final_eval_answer = f"Step {current_step_num} failed and is not recoverable. Evaluator: {eval_outcome.assessment_of_step}"; break
            else: 
                logger.error(f"[{session_id}] Step Evaluator failed for step {current_step_num}{attempt_msg}.")
                plan_failed = True; final_eval_answer = f"Error: Step Evaluator failed for step {current_step_num}."; break
            retry_count += 1
        
        step_execution_summary_for_overall_eval.append(f"Step {current_step_num}: {current_plan_step_obj.description}\n  Status: {'Success' if step_succeeded_this_round else 'Failed'}\n  Attempts:\n    " + "\n    ".join(current_step_attempt_log))
        await _update_plan_file_step_status(
            task_workspace_path, 
            plan_execution_filename, 
            current_step_num, 
            "x" if step_succeeded_this_round else "!",
            active_task_id, 
            send_ws_message_func 
        )
        if not step_succeeded_this_round: plan_failed = True 
        if plan_failed: break 
        
    session_data_entry["plan_execution_active"] = False
    executed_plan_summary_str = "\n---\n".join(step_execution_summary_for_overall_eval) if step_execution_summary_for_overall_eval else "No steps were fully processed to summarize."

    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Evaluating overall outcome...", "OVERALL_EVAL_START", LOG_SOURCE_EVALUATOR_OVERALL, SUB_TYPE_BOTTOM_LINE)
    overall_eval_result = await evaluate_plan_outcome(
        original_user_query, executed_plan_summary_str, 
        final_eval_answer, session_data_entry,
        retrieved_callback_handler 
    )
    
    final_chat_message_content = final_eval_answer 
    if overall_eval_result:
        final_chat_message_content = overall_eval_result.assessment
        if not overall_eval_result.overall_success and overall_eval_result.suggestions_for_replan:
            final_chat_message_content += "\nSuggestions for improvement: " + "; ".join(overall_eval_result.suggestions_for_replan)
    
    await send_ws_message_func("agent_message", {"content": final_chat_message_content, "component_hint": LOG_SOURCE_EVALUATOR_OVERALL if overall_eval_result else LOG_SOURCE_SYSTEM})
    await db_add_message_func(active_task_id, session_id, "agent_message", final_chat_message_content)
    
    final_bottom_line_status_key = "IDLE"; final_bottom_line_message = "Idle."
    if plan_failed: final_bottom_line_status_key = "PLAN_STOPPED"; final_bottom_line_message = "Idle (Plan Stopped/Failed)."
    elif overall_eval_result and not overall_eval_result.overall_success: final_bottom_line_status_key = "PLAN_COMPLETED_ISSUES"; final_bottom_line_message = "Idle (Plan completed with issues)."
    
    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, final_bottom_line_message, final_bottom_line_status_key, LOG_SOURCE_SYSTEM, SUB_TYPE_BOTTOM_LINE)
    session_data_entry.update({'current_plan_proposal_id_backend': None, 'current_plan_human_summary': None})


async def process_cancel_plan_proposal(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    plan_id_to_cancel = data.get("plan_id")
    if not plan_id_to_cancel: return
    if session_data_entry.get("current_plan_proposal_id_backend") == plan_id_to_cancel:
        session_data_entry.update({'current_plan_proposal_id_backend': None, 'current_plan_human_summary': None, 'current_plan_structured': None, 'plan_execution_active': False})
        await add_monitor_log_func(f"Plan proposal (ID: {plan_id_to_cancel}) cancelled.", f"{LOG_SOURCE_SYSTEM}_PLAN_CANCELLED")
        dummy_db_add = lambda tid, sid, mtype, cont: asyncio.sleep(0) # type: ignore
        await _send_thinking_update_from_handler(send_ws_message_func, session_data_entry.get("current_task_id"), session_id, dummy_db_add, "Idle.", "IDLE", LOG_SOURCE_SYSTEM, SUB_TYPE_BOTTOM_LINE)
        await send_ws_message_func("status_message", {"text": f"Plan proposal cancelled.", "component_hint": LOG_SOURCE_SYSTEM})
