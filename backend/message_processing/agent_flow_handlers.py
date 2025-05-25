# backend/message_processing/agent_flow_handlers.py
import logging
import json
import datetime
from typing import Dict, Any, Callable, Coroutine, Optional, List
import asyncio
from pathlib import Path
import aiofiles 
import re 

# LangChain Imports
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool 

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path 
from backend.planner import generate_plan, PlanStep 
from backend.controller import validate_and_prepare_step_action
from backend.agent import create_agent_executor
from backend.callbacks import AgentCancelledException 
from backend.intent_classifier import classify_intent
from backend.evaluator import (
    evaluate_plan_outcome, EvaluationResult,
    evaluate_step_outcome_and_suggest_correction, StepCorrectionOutcome
)

logger = logging.getLogger(__name__)

# Type Hints for Passed-in Functions
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]

MAX_STEP_RETRIES = settings.agent_max_step_retries


async def _update_plan_file_step_status(
    task_workspace_path: Path,
    plan_filename: str,
    step_number: int, 
    status_char: str 
) -> None:
    """Helper to update a step's status in the plan Markdown file."""
    if not plan_filename:
        logger.warning("Cannot update plan file: no active plan filename.")
        return

    plan_file_path = task_workspace_path / plan_filename
    if not await asyncio.to_thread(plan_file_path.exists):
        logger.warning(f"Plan file {plan_file_path} not found for updating step {step_number}.")
        return

    try:
        async with aiofiles.open(plan_file_path, 'r', encoding='utf-8') as f_read:
            lines = await f_read.readlines()

        updated_lines = []
        found_step = False
        step_pattern = re.compile(rf"^\s*-\s*\[\s*[ x!-]?\s*\]\s*{re.escape(str(step_number))}\.\s+.*", re.IGNORECASE)
        checkbox_pattern = re.compile(r"(\s*-\s*\[)\s*[ x!-]?\s*(\])")

        for line_no, line_content in enumerate(lines):
            if not found_step and step_pattern.match(line_content):
                updated_line = checkbox_pattern.sub(rf"\g<1>{status_char}\g<2>", line_content, count=1)
                updated_lines.append(updated_line)
                found_step = True
                logger.info(f"Updated plan file for step {step_number} to status '[{status_char}]'. Line: {updated_line.strip()}")
            else:
                updated_lines.append(line_content)

        if found_step:
            async with aiofiles.open(plan_file_path, 'w', encoding='utf-8') as f_write:
                await f_write.writelines(updated_lines)
        else:
            logger.warning(f"Step {step_number} pattern not found in plan file {plan_file_path} for status update. Regex was: {step_pattern.pattern}")
            if len(lines) > 0:
                logger.debug("First few lines of plan file for debugging update failure:")
                for i, l in enumerate(lines[:5]):
                    logger.debug(f"  Line {i+1}: {l.strip()}")
    except Exception as e:
        logger.error(f"Error updating plan file {plan_file_path} for step {step_number}: {e}", exc_info=True)


async def process_user_message(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc
) -> None:
    user_input_content = ""
    content_payload = data.get("content")
    if isinstance(content_payload, str):
        user_input_content = content_payload
    elif isinstance(content_payload, dict) and 'content' in content_payload and isinstance(content_payload['content'], str):
        user_input_content = content_payload['content']
    else:
        logger.warning(f"[{session_id}] Received non-string or unexpected content for user_message: {type(content_payload)}. Ignoring.")
        return

    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id:
        logger.warning(f"[{session_id}] User message received but no task active.")
        await send_ws_message_func("status_message", "Please select or create a task first.")
        return

    if (connected_clients_entry.get("agent_task") or
        session_data_entry.get("plan_execution_active")):
        logger.warning(f"[{session_id}] User message received while agent/plan is already running for task {active_task_id}.")
        await send_ws_message_func("status_message", "Agent is busy. Please wait or stop the current process.")
        return

    await db_add_message_func(active_task_id, session_id, "user_input", user_input_content)
    await add_monitor_log_func(f"User Input: {user_input_content}", "monitor_user_input")

    session_data_entry['original_user_query'] = user_input_content
    session_data_entry['cancellation_requested'] = False
    session_data_entry['active_plan_filename'] = None 

    await send_ws_message_func("agent_thinking_update", {"status": "Classifying intent..."})

    dynamic_tools = get_dynamic_tools(active_task_id)
    tools_summary_for_intent = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])

    classified_intent = await classify_intent(user_input_content, tools_summary_for_intent)
    await add_monitor_log_func(f"Intent classified as: {classified_intent}", "system_intent_classified")

    if classified_intent == "PLAN":
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan..."})
        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content,
            available_tools_summary=tools_summary_for_intent
        )
        if human_plan_summary and structured_plan_steps:
            session_data_entry["current_plan_human_summary"] = human_plan_summary
            session_data_entry["current_plan_structured"] = structured_plan_steps
            session_data_entry["current_plan_step_index"] = 0
            session_data_entry["plan_execution_active"] = False
            await send_ws_message_func("display_plan_for_confirmation", {
                "human_summary": human_plan_summary,
                "structured_plan": structured_plan_steps
            })
            await add_monitor_log_func(f"Plan generated. Summary: {human_plan_summary}. Steps: {len(structured_plan_steps)}. Awaiting user confirmation.", "system_plan_generated")
            await send_ws_message_func("status_message", "Plan generated. Please review and confirm.")
            await send_ws_message_func("agent_thinking_update", {"status": "Awaiting plan confirmation..."})
        else:
            logger.error(f"[{session_id}] Failed to generate a plan for query: {user_input_content}")
            await add_monitor_log_func(f"Error: Failed to generate a plan.", "error_system")
            await send_ws_message_func("status_message", "Error: Could not generate a plan for your request.")
            await send_ws_message_func("agent_message", "I'm sorry, I couldn't create a plan for that request. Please try rephrasing or breaking it down.")
            await send_ws_message_func("agent_thinking_update", {"status": "Planning failed."})

    elif classified_intent == "DIRECT_QA":
        await send_ws_message_func("agent_thinking_update", {"status": "Processing directly..."})
        await add_monitor_log_func(f"Handling as DIRECT_QA. Invoking ReAct agent.", "system_direct_qa")
        executor_provider = session_data_entry.get("selected_llm_provider", settings.executor_default_provider)
        executor_model_name = session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name)
        logger.info(f"[{session_id}] Using LLM for Direct QA (Executor role): {executor_provider}::{executor_model_name}")
        direct_qa_llm: Optional[BaseChatModel] = None
        try:
            llm_instance = get_llm(settings, provider=executor_provider, model_name=executor_model_name, requested_for_role="DirectQA_Executor")
            if not isinstance(llm_instance, BaseChatModel): logger.warning(f"LLM for Direct QA is not BaseChatModel, it's {type(llm_instance)}.")
            direct_qa_llm = llm_instance # type: ignore
        except Exception as llm_init_err:
            logger.error(f"[{session_id}] Failed to initialize LLM for Direct QA: {llm_init_err}", exc_info=True)
            await add_monitor_log_func(f"Error initializing LLM for Direct QA: {llm_init_err}", "error_system")
            await send_ws_message_func("status_message", "Error: Failed to prepare for answering.")
            await send_ws_message_func("agent_message", "Sorry, I couldn't initialize my reasoning module to answer.")
            await send_ws_message_func("agent_thinking_update", {"status": "Direct QA failed."}); return
        direct_qa_memory = session_data_entry["memory"]
        direct_qa_callback_handler = session_data_entry["callback_handler"]
        try:
            agent_executor_direct = create_agent_executor(llm=direct_qa_llm, tools=dynamic_tools, memory=direct_qa_memory, max_iterations=settings.agent_max_iterations) # type: ignore
            logger.info(f"[{session_id}] Invoking AgentExecutor directly for QA with input: '{user_input_content[:100]}...'")
            direct_qa_task = asyncio.create_task(agent_executor_direct.ainvoke({"input": user_input_content}, config=RunnableConfig(callbacks=[direct_qa_callback_handler])))
            connected_clients_entry["agent_task"] = direct_qa_task; await direct_qa_task
        except AgentCancelledException: logger.warning(f"[{session_id}] Direct QA execution cancelled by user."); await send_ws_message_func("status_message", "Direct QA cancelled."); await add_monitor_log_func("Direct QA cancelled by user.", "system_cancel")
        except Exception as e: logger.error(f"[{session_id}] Error during direct QA execution: {e}", exc_info=True); await add_monitor_log_func(f"Error during direct QA: {e}", "error_direct_qa"); await send_ws_message_func("agent_message", f"Sorry, I encountered an error trying to answer directly: {e}"); await send_ws_message_func("status_message", "Error during direct processing.")
        finally: connected_clients_entry["agent_task"] = None; await send_ws_message_func("agent_thinking_update", {"status": "Idle."})
    else: 
        logger.error(f"[{session_id}] Unknown intent classified: {classified_intent}. Defaulting to planning."); await add_monitor_log_func(f"Error: Unknown intent '{classified_intent}'. Defaulting to PLAN.", "error_system")
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan (fallback)..."})
        human_plan_summary, structured_plan_steps = await generate_plan(user_query=user_input_content, available_tools_summary=tools_summary_for_intent)
        if human_plan_summary and structured_plan_steps:
            session_data_entry["current_plan_human_summary"] = human_plan_summary; session_data_entry["current_plan_structured"] = structured_plan_steps
            session_data_entry["current_plan_step_index"] = 0; session_data_entry["plan_execution_active"] = False
            await send_ws_message_func("display_plan_for_confirmation", {"human_summary": human_plan_summary, "structured_plan": structured_plan_steps})
            await add_monitor_log_func(f"Plan generated (fallback). Summary: {human_plan_summary}. Steps: {len(structured_plan_steps)}. Awaiting user confirmation.", "system_plan_generated"); await send_ws_message_func("status_message", "Plan generated. Please review and confirm."); await send_ws_message_func("agent_thinking_update", {"status": "Awaiting plan confirmation..."})
        else:
            logger.error(f"[{session_id}] Failed to generate a plan (fallback) for query: {user_input_content}"); await add_monitor_log_func(f"Error: Failed to generate a plan (fallback).", "error_system")
            await send_ws_message_func("status_message", "Error: Could not generate a plan for your request (fallback)."); await send_ws_message_func("agent_message", "I'm sorry, I couldn't create a plan for that request. Please try rephrasing or breaking it down."); await send_ws_message_func("agent_thinking_update", {"status": "Planning failed."})


async def process_execute_confirmed_plan(
    session_id: str,
    data: Dict[str, Any],
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_add_message_func: DBAddMessageFunc 
) -> None:
    logger.info(f"[{session_id}] Received 'execute_confirmed_plan'.")
    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id:
        logger.warning(f"[{session_id}] 'execute_confirmed_plan' received but no active task.")
        await send_ws_message_func("status_message", "Error: No active task to execute plan for.")
        return

    confirmed_plan_steps_dicts = data.get("confirmed_plan")
    if not confirmed_plan_steps_dicts or not isinstance(confirmed_plan_steps_dicts, list):
        logger.error(f"[{session_id}] Invalid or missing plan in 'execute_confirmed_plan' message. Data received: {data}")
        await send_ws_message_func("status_message", "Error: Invalid plan received for execution.")
        return

    session_data_entry["current_plan_structured"] = confirmed_plan_steps_dicts
    session_data_entry["current_plan_step_index"] = 0
    session_data_entry["plan_execution_active"] = True
    session_data_entry['cancellation_requested'] = False

    await add_monitor_log_func(f"User confirmed plan. Starting execution of {len(confirmed_plan_steps_dicts)} steps.", "system_plan_confirmed")
    await send_ws_message_func("status_message", "Plan confirmed. Executing steps...")

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    plan_filename = f"_plan_{timestamp_str}.md"
    session_data_entry['active_plan_filename'] = plan_filename
    plan_markdown_content = [f"# Agent Plan for Task: {active_task_id}\n", f"## Plan ID: {timestamp_str}\n"]
    original_query_for_plan_file = session_data_entry.get('original_user_query', 'N/A')
    plan_markdown_content.append(f"## Original User Query:\n{original_query_for_plan_file}\n")
    plan_markdown_content.append(f"## Plan Summary (from Planner):\n{session_data_entry.get('current_plan_human_summary', 'N/A')}\n")
    plan_markdown_content.append("## Steps:\n")
    for i, step_data_dict in enumerate(confirmed_plan_steps_dicts):
        desc = step_data_dict.get('description', 'N/A') if isinstance(step_data_dict, dict) else 'N/A (Invalid Step Format)'
        tool_sugg = step_data_dict.get('tool_to_use', 'None') if isinstance(step_data_dict, dict) else 'N/A'
        input_instr = step_data_dict.get('tool_input_instructions', 'None') if isinstance(step_data_dict, dict) else 'N/A'
        expected_out = step_data_dict.get('expected_outcome', 'N/A') if isinstance(step_data_dict, dict) else 'N/A'
        plan_markdown_content.append(f"- [ ] {i+1}. **{desc}**"); plan_markdown_content.append(f"    - Tool Suggestion (Planner): `{tool_sugg}`"); plan_markdown_content.append(f"    - Input Instructions (Planner): `{input_instr}`"); plan_markdown_content.append(f"    - Expected Outcome (Planner): `{expected_out}`\n")
    task_workspace_path = get_task_workspace_path(active_task_id)
    try:
        plan_file_path = task_workspace_path / plan_filename
        async with aiofiles.open(plan_file_path, 'w', encoding='utf-8') as f: await f.write("\n".join(plan_markdown_content))
        logger.info(f"[{session_id}] Saved confirmed plan to {plan_file_path}")
        await add_monitor_log_func(f"Confirmed plan saved to artifact: {plan_filename}", "system_info")
        await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})
    except Exception as e: logger.error(f"[{session_id}] Failed to save plan to file '{plan_filename}': {e}", exc_info=True); await add_monitor_log_func(f"Error saving plan to file '{plan_filename}': {e}", "error_system")

    plan_failed_definitively = False
    preliminary_final_answer_from_last_step = "Plan execution completed."
    step_execution_details_list = []
    original_user_query = session_data_entry.get("original_user_query", "No original query context available.")
    
    # --- ADDED: Variable to store previous step's output ---
    last_successful_step_output: Optional[str] = None 
    # --- END ADDITION ---

    for i, step_dict_from_plan in enumerate(confirmed_plan_steps_dicts):
        session_data_entry["current_plan_step_index"] = i; current_step_number = i + 1
        current_step_detail_log = {"step_number": current_step_number, "description": "N/A", "controller_tool_initial": "N/A", "controller_input_initial": "N/A", "controller_reasoning_initial": "N/A", "controller_confidence_initial": 0.0, "attempts": [], "final_status_char": " "}
        current_plan_step_obj: Optional[PlanStep] = None
        try: current_plan_step_obj = PlanStep(**step_dict_from_plan); current_step_detail_log["description"] = current_plan_step_obj.description
        except Exception as pydantic_err: 
            logger.error(f"[{session_id}] Failed to parse step dictionary into PlanStep object: {pydantic_err}. Step data: {step_dict_from_plan}", exc_info=True)
            error_msg = f"Error: Corrupted plan step {current_step_number}. Skipping. Details: {pydantic_err}"
            await add_monitor_log_func(error_msg, "error_plan_step")
            current_step_detail_log["attempts"].append({"attempt_number": 1, "controller_tool": "N/A", "controller_input": "N/A", "controller_reasoning": "Plan step parsing error", "controller_confidence": 0.0, "executor_input": "N/A", "executor_output": "N/A", "error": error_msg, "step_eval_achieved": False, "step_eval_assessment": "Plan step parsing error", "status_char_for_attempt": "!"})
            current_step_detail_log["final_status_char"] = "!"
            step_execution_details_list.append(current_step_detail_log)
            plan_failed_definitively = True
            break 
        if not current_plan_step_obj: 
            logger.critical(f"[{session_id}] CRITICAL: current_plan_step_obj is None after successful parsing for step {current_step_number}. This indicates a logic error.")
            plan_failed_definitively = True
            break
        step_description = current_plan_step_obj.description; step_tools: List[BaseTool] = get_dynamic_tools(active_task_id)
        retry_count_for_current_step = 0; step_succeeded_after_attempts = False; last_step_correction_suggestion: Optional[StepCorrectionOutcome] = None
        
        while retry_count_for_current_step <= MAX_STEP_RETRIES:
            attempt_number = retry_count_for_current_step + 1
            attempt_log_detail = {"attempt_number": attempt_number, "controller_tool": "N/A", "controller_input": "N/A", "controller_reasoning": "N/A", "controller_confidence": 0.0, "executor_input": "N/A", "executor_output": "N/A", "error": None, "step_eval_achieved": False, "step_eval_assessment": "Not evaluated yet", "status_char_for_attempt": " "}
            plan_step_for_controller_call = current_plan_step_obj.copy(deep=True)
            if retry_count_for_current_step > 0 and last_step_correction_suggestion:
                await send_ws_message_func("agent_thinking_update", {"status": f"Controller re-validating Step {current_step_number} (Retry {retry_count_for_current_step})..."}); await add_monitor_log_func(f"Controller: Re-validating Step {current_step_number} (Retry {retry_count_for_current_step}) based on Step Evaluator feedback.", "system_controller_retry")
                plan_step_for_controller_call.tool_to_use = last_step_correction_suggestion.suggested_new_tool_for_retry; plan_step_for_controller_call.tool_input_instructions = last_step_correction_suggestion.suggested_new_input_instructions_for_retry
            else: await send_ws_message_func("agent_thinking_update", {"status": f"Controller validating Step {current_step_number}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."}); await add_monitor_log_func(f"Controller: Validating Plan Step {current_step_number}: {step_description} (Planner hint: {current_plan_step_obj.tool_to_use or 'None'})", "system_controller_start")
            
            # --- MODIFIED: Pass previous_step_output and session_data_entry to controller ---
            validated_tool_name, formulated_tool_input, controller_message, controller_confidence = await validate_and_prepare_step_action(
                original_user_query=original_user_query, 
                plan_step=plan_step_for_controller_call, 
                available_tools=step_tools,
                session_data_entry=session_data_entry, # Pass session data for LLM selection
                previous_step_output=last_successful_step_output 
            )
            # --- END MODIFICATION ---

            attempt_log_detail.update({"controller_tool": validated_tool_name, "controller_input": formulated_tool_input, "controller_reasoning": controller_message, "controller_confidence": controller_confidence})
            if retry_count_for_current_step == 0: current_step_detail_log.update({"controller_tool_initial": validated_tool_name, "controller_input_initial": formulated_tool_input, "controller_reasoning_initial": controller_message, "controller_confidence_initial": controller_confidence})
            await add_monitor_log_func(f"Controller Output (Step {current_step_number}, Attempt {attempt_number}): Tool='{validated_tool_name}', Input='{str(formulated_tool_input)[:100]}...', Confidence={controller_confidence:.2f}. Reasoning: {controller_message}", "system_controller_output")
            if controller_confidence < 0.7 and validated_tool_name: await add_monitor_log_func(f"Warning: Controller confidence for step {current_step_number} (Attempt {attempt_number}) is low ({controller_confidence:.2f}). Proceeding.", "warning_controller")
            if validated_tool_name is None and "Error in Controller" in controller_message: 
                error_msg = f"Error: Controller failed for step {current_step_number} (Attempt {attempt_number}). Reason: {controller_message}."
                await add_monitor_log_func(error_msg, "error_controller")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"
                plan_failed_definitively = True
                break
            
            agent_input_for_executor: str
            if validated_tool_name: agent_input_for_executor = (f"Your current sub-task is: \"{step_description}\".\n" f"The precise expected output for THIS sub-task is: \"{current_plan_step_obj.expected_outcome}\".\n" f"The Controller has determined you MUST use the tool '{validated_tool_name}' " f"with the following exact input: '{formulated_tool_input}'.\n" f"Execute this and report the result, ensuring your final answer for this sub-task directly fulfills the stated 'precise expected output'.")
            else: agent_input_for_executor = (f"Your current sub-task is: \"{step_description}\".\n" f"The precise expected output for THIS sub-task is: \"{current_plan_step_obj.expected_outcome}\".\n" f"The Controller has determined no specific tool is required for this step. " f"Provide a direct answer or perform analysis based on conversation history and this sub-task description, ensuring your final answer for this sub-task directly fulfills the stated 'precise expected output'.")
            attempt_log_detail["executor_input"] = agent_input_for_executor
            await send_ws_message_func("agent_thinking_update", {"status": f"Executor running Step {current_step_number} (Attempt {attempt_number})..."}); await add_monitor_log_func(f"Executing Plan Step {current_step_number} (Attempt {attempt_number}): {step_description}", "system_plan_step_start")
            executor_provider = session_data_entry.get("selected_llm_provider", settings.executor_default_provider); executor_model_name = session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name)
            step_executor_llm: Optional[BaseChatModel] = None
            try: llm_instance_exec = get_llm(settings, provider=executor_provider, model_name=executor_model_name, requested_for_role="Executor_PlanStep"); step_executor_llm = llm_instance_exec # type: ignore
            except Exception as llm_err: 
                error_msg = f"Error: Failed to init LLM for Executor (Step {current_step_number}, Attempt {attempt_number}). Details: {llm_err}"
                await add_monitor_log_func(error_msg, "error_system")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"
                plan_failed_definitively = True
                break
            
            step_memory = session_data_entry["memory"]; step_callback_handler = session_data_entry["callback_handler"]; step_executor_output_str = "Executor did not produce output."
            try:
                step_agent_executor = create_agent_executor(llm=step_executor_llm, tools=step_tools, memory=step_memory, max_iterations=settings.agent_max_iterations)
                agent_step_task = asyncio.create_task(step_agent_executor.ainvoke({"input": agent_input_for_executor}, config=RunnableConfig(callbacks=[step_callback_handler])))
                connected_clients_entry["agent_task"] = agent_step_task; step_result_from_executor = await agent_step_task
                step_executor_output_str = step_result_from_executor.get("output", "Step completed, no specific output from ReAct agent.")
                attempt_log_detail["executor_output"] = step_executor_output_str; await add_monitor_log_func(f"Plan Step {current_step_number} (Attempt {attempt_number}, Executor) completed. Output: {str(step_executor_output_str)[:200]}...", "system_plan_step_end")
            except AgentCancelledException as ace: 
                error_msg = f"Plan execution cancelled by user during step {current_step_number} (Attempt {attempt_number})."; logger.warning(f"[{session_id}] {error_msg}"); await send_ws_message_func("status_message", "Plan execution cancelled."); await add_monitor_log_func(error_msg, "system_cancel")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "-"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "-"
                plan_failed_definitively = True
                break
            except Exception as step_exec_e: 
                error_msg = f"Error executing plan step {current_step_number} (Attempt {attempt_number}): {step_exec_e}"; logger.error(f"[{session_id}] {error_msg}", exc_info=True); await add_monitor_log_func(error_msg, "error_plan_step")
                step_executor_output_str = error_msg; attempt_log_detail["error"] = error_msg; attempt_log_detail["executor_output"] = error_msg
            finally: connected_clients_entry["agent_task"] = None
            
            await add_monitor_log_func(f"Step Evaluator: Assessing outcome of Step {current_step_number} (Attempt {attempt_number})...", "system_step_eval_start")
            last_step_correction_suggestion = await evaluate_step_outcome_and_suggest_correction(original_user_query=original_user_query, plan_step_being_evaluated=current_plan_step_obj, controller_tool_used=validated_tool_name, controller_tool_input=formulated_tool_input, step_executor_output=step_executor_output_str, available_tools=step_tools, session_data_entry=session_data_entry)
            if last_step_correction_suggestion:
                attempt_log_detail["step_eval_achieved"] = last_step_correction_suggestion.step_achieved_goal; attempt_log_detail["step_eval_assessment"] = last_step_correction_suggestion.assessment_of_step
                await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Goal Achieved: {last_step_correction_suggestion.step_achieved_goal}. Assessment: {last_step_correction_suggestion.assessment_of_step}", "system_step_eval_output")
                if last_step_correction_suggestion.step_achieved_goal: 
                    attempt_log_detail["status_char_for_attempt"] = "x"; step_succeeded_after_attempts = True
                    current_step_detail_log["final_status_char"] = "x"; current_step_detail_log["attempts"].append(attempt_log_detail)
                    last_successful_step_output = step_executor_output_str # Capture output for next step
                    break 
                else:
                    if last_step_correction_suggestion.is_recoverable_via_retry and retry_count_for_current_step < MAX_STEP_RETRIES: 
                        await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Suggests RETRY. Tool: '{last_step_correction_suggestion.suggested_new_tool_for_retry}', Input Hint: '{last_step_correction_suggestion.suggested_new_input_instructions_for_retry}', Confidence: {last_step_correction_suggestion.confidence_in_correction}", "system_step_eval_suggest_retry")
                        attempt_log_detail["status_char_for_attempt"] = "!"
                        current_step_detail_log["attempts"].append(attempt_log_detail)
                        retry_count_for_current_step += 1
                    else: 
                        await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Step failed and is not recoverable or retries exhausted.", "system_step_eval_unrecoverable")
                        attempt_log_detail["status_char_for_attempt"] = "!"
                        current_step_detail_log["attempts"].append(attempt_log_detail)
                        current_step_detail_log["final_status_char"] = "!"
                        plan_failed_definitively = True
                        break
            else: 
                await add_monitor_log_func(f"Error: Step Evaluator failed for Step {current_step_number} (Attempt {attempt_number}). Assuming step failed.", "error_step_eval")
                attempt_log_detail["error"] = attempt_log_detail.get("error") or "Step Evaluator failed to produce an outcome."
                attempt_log_detail["step_eval_assessment"] = "Step Evaluator failed."
                attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"
                plan_failed_definitively = True
                break
            if session_data_entry.get('cancellation_requested', False): 
                logger.warning(f"[{session_id}] Cancellation detected after step {current_step_number} (Attempt {attempt_number}). Stopping plan.")
                await send_ws_message_func("status_message", "Plan execution cancelled.")
                if not attempt_log_detail.get("error"): attempt_log_detail["error"] = "Cancelled by user after step attempt."
                attempt_log_detail["status_char_for_attempt"] = "-"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "-"
                plan_failed_definitively = True
                break
        
        step_execution_details_list.append(current_step_detail_log)
        active_plan_filename_local = session_data_entry.get('active_plan_filename')
        if active_plan_filename_local and active_task_id: 
            await _update_plan_file_step_status(task_workspace_path, active_plan_filename_local, current_step_number, current_step_detail_log.get("final_status_char", "?"))
            await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})
        if plan_failed_definitively: 
            break
        if step_succeeded_after_attempts: 
            # last_successful_step_output is already set if step_achieved_goal was true
            preliminary_final_answer_from_last_step = last_successful_step_output # Use the captured output
        else: # If step failed all retries, clear last_successful_step_output for next iteration
            last_successful_step_output = None


    session_data_entry["plan_execution_active"] = False; session_data_entry["current_plan_step_index"] = -1
    summary_lines_for_overall_eval = []
    for step_log in step_execution_details_list:
        summary_lines_for_overall_eval.append(f"Step {step_log['step_number']}: {step_log['description']}"); summary_lines_for_overall_eval.append(f"  Initial Controller: Tool='{step_log['controller_tool_initial']}', Input='{str(step_log['controller_input_initial'])[:100]}', Confidence={step_log['controller_confidence_initial']:.2f}")
        for i_att, attempt in enumerate(step_log["attempts"]):
            summary_lines_for_overall_eval.append(f"  Attempt {i_att+1}:");
            if attempt.get("controller_tool"): summary_lines_for_overall_eval.append(f"    Controller: Tool='{attempt['controller_tool']}', Input='{str(attempt['controller_input'])[:100]}'")
            summary_lines_for_overall_eval.append(f"    Executor Output: {str(attempt['executor_output'])[:150]}...");
            if attempt.get("error"): summary_lines_for_overall_eval.append(f"    Error for Attempt: {str(attempt['error'])[:150]}...")
            summary_lines_for_overall_eval.append(f"    Step Evaluator Assessment: Achieved={attempt.get('step_eval_achieved', 'N/A')}, Detail: {attempt.get('step_eval_assessment', 'N/A')[:100]}..."); summary_lines_for_overall_eval.append(f"    Attempt Status: [{attempt.get('status_char_for_attempt', '?')}]")
        summary_lines_for_overall_eval.append(f"  Final Step Status: [{step_log.get('final_status_char', '?')}]"); summary_lines_for_overall_eval.append("-" * 20)
    executed_plan_summary_str = "\n".join(summary_lines_for_overall_eval)
    if not step_execution_details_list: executed_plan_summary_str = "No steps were attempted or recorded."
    
    if plan_failed_definitively: 
        final_message_to_user = "Plan execution stopped due to error or cancellation."
        for step_log in reversed(step_execution_details_list):
            for attempt in reversed(step_log.get("attempts", [])):
                if attempt.get("error"): final_message_to_user = f"Plan stopped. Last error: {str(attempt['error'])[:200]}"; break
            if final_message_to_user != "Plan execution stopped due to error or cancellation.": break
        await send_ws_message_func("agent_thinking_update", {"status": "Plan stopped."})
    else: 
        final_message_to_user = preliminary_final_answer_from_last_step
        await send_ws_message_func("agent_thinking_update", {"status": "Plan executed. Evaluating overall outcome..."})
        logger.info(f"[{session_id}] Successfully attempted all plan steps (or those before a definitive failure). Now evaluating overall plan.")
    
    await add_monitor_log_func("Invoking Overall Plan Evaluator to assess final outcome.", "system_evaluator_start")
    overall_evaluation_result = await evaluate_plan_outcome(original_user_query=original_user_query, executed_plan_summary=executed_plan_summary_str, final_agent_answer=final_message_to_user, session_data_entry=session_data_entry)
    if overall_evaluation_result:
        final_message_to_user = overall_evaluation_result.assessment
        log_msg = (f"Overall Plan Evaluator Result: Success={overall_evaluation_result.overall_success}, " f"Confidence={overall_evaluation_result.confidence_score:.2f}. " f"Assessment: {overall_evaluation_result.assessment}")
        await add_monitor_log_func(log_msg, "system_evaluator_output")
        if not overall_evaluation_result.overall_success and overall_evaluation_result.suggestions_for_replan: await add_monitor_log_func(f"Overall Plan Evaluator Suggestions for future re-plan: {overall_evaluation_result.suggestions_for_replan}", "system_evaluator_suggestions")
    else: await add_monitor_log_func("Error: Overall Plan Evaluator failed to produce a result. Using last available answer/error message.", "error_evaluator")
    
    await send_ws_message_func("agent_message", final_message_to_user)
    if active_task_id: await db_add_message_func(active_task_id, session_id, "agent_message", final_message_to_user); logger.info(f"[{session_id}] Saved final agent message to DB for task {active_task_id}.")
    await add_monitor_log_func(f"Final Overall Outcome Sent to User: {final_message_to_user}", "system_plan_end")
    await send_ws_message_func("status_message", "Processing complete.")
    await send_ws_message_func("agent_thinking_update", {"status": "Idle."})

