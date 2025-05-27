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

from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path
from backend.planner import generate_plan, PlanStep
from backend.controller import validate_and_prepare_step_action
from backend.agent import create_agent_executor
from backend.callbacks import AgentCancelledException, SUB_TYPE_BOTTOM_LINE, SUB_TYPE_SUB_STATUS, SUB_TYPE_THOUGHT, DB_MSG_TYPE_SUB_STATUS, DB_MSG_TYPE_THOUGHT # Import new constants
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

# Component hint constants
COMPONENT_HINT_SYSTEM = "SYSTEM"
COMPONENT_HINT_INTENT_CLASSIFIER = "INTENT_CLASSIFIER"
COMPONENT_HINT_PLANNER = "PLANNER"
COMPONENT_HINT_CONTROLLER = "CONTROLLER"
COMPONENT_HINT_EXECUTOR = "EXECUTOR"
COMPONENT_HINT_EVALUATOR_STEP = "EVALUATOR_STEP"
COMPONENT_HINT_EVALUATOR_OVERALL = "EVALUATOR_OVERALL"

# NEW: DB message type for major step announcements
DB_MSG_TYPE_MAJOR_STEP = "db_major_step_announcement"

async def _save_message_to_db_from_handler(
    task_id: Optional[str],
    session_id: str,
    db_add_message_func: DBAddMessageFunc,
    message_type: str,
    content_data: Any
):
    """ Helper to save structured messages to DB if task_id is set, from within agent_flow_handlers. """
    if task_id:
        try:
            content_str = json.dumps(content_data) if isinstance(content_data, dict) else str(content_data)
            await db_add_message_func(task_id, session_id, message_type, content_str)
            logger.debug(f"[{session_id}] Saved message type '{message_type}' to DB for task {task_id} (from agent_flow_handler).")
        except Exception as e:
            logger.error(f"[{session_id}] Handler DB save error (Task: {task_id}, Type: {message_type}): {e}", exc_info=True)
    else:
        logger.warning(f"[{session_id}] Cannot save message type '{message_type}' to DB from handler: task_id not set.")


async def _send_thinking_update_from_handler(
    send_ws_message_func: SendWSMessageFunc,
    task_id: Optional[str], # Added task_id
    session_id: str, # Added session_id
    db_add_message_func: DBAddMessageFunc, # Added db_add_message_func
    message_text: str,
    status_key: str,
    component_hint: str,
    sub_type: str = SUB_TYPE_BOTTOM_LINE, # Default to bottom line
    details: Optional[Dict] = None,
    thought_label: Optional[str] = None # For thoughts
):
    """
    Sends an agent_thinking_update message from agent_flow_handlers
    and saves it to DB if it's a sub_status or thought.
    """
    payload = {
        "status_key": status_key,
        "message": message_text,
        "component_hint": component_hint,
        "sub_type": sub_type,
    }
    if details:
        payload["details"] = details
    if sub_type == SUB_TYPE_THOUGHT and thought_label:
        payload["message"] = { "label": thought_label, "content_markdown": message_text }

    await send_ws_message_func("agent_thinking_update", payload)

    if task_id and session_id: # Check if task_id and session_id are available
        if sub_type == SUB_TYPE_SUB_STATUS:
            await _save_message_to_db_from_handler(task_id, session_id, db_add_message_func, DB_MSG_TYPE_SUB_STATUS, {
                "message_text": message_text,
                "component_hint": component_hint
            })
        elif sub_type == SUB_TYPE_THOUGHT:
            await _save_message_to_db_from_handler(task_id, session_id, db_add_message_func, DB_MSG_TYPE_THOUGHT, {
                "thought_label": thought_label,
                "thought_content_markdown": message_text,
                "component_hint": component_hint
            })


async def _update_plan_file_step_status(
    task_workspace_path: Path,
    plan_filename: str,
    step_number: int,
    status_char: str # 'x' for success, '!' for fail, '-' for cancelled/skipped
) -> None:
    # ... (This function remains the same, no changes needed for persistence here)
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
        # Regex to find the start of a numbered list item, allowing for existing status markers
        step_pattern = re.compile(rf"^\s*-\s*\[\s*[ x!-]?\s*\]\s*{re.escape(str(step_number))}\.\s+.*", re.IGNORECASE)
        # Regex to replace the checkbox content
        checkbox_pattern = re.compile(r"(\s*-\s*\[)\s*[ x!-]?\s*(\])") # Matches '[ ]', '[x]', '[!]', '[-]'
        for line_no, line_content in enumerate(lines):
            if not found_step and step_pattern.match(line_content):
                # Replace only the content within the first checkbox found on the line
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
    except Exception as e:
        logger.error(f"Error updating plan file {plan_file_path} for step {step_number}: {e}", exc_info=True)


async def process_user_message(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc
) -> None:
    user_input_content = ""
    # ... (input validation remains the same) ...
    content_payload = data.get("content")
    if isinstance(content_payload, str):
        user_input_content = content_payload
    elif isinstance(content_payload, dict) and 'content' in content_payload and isinstance(content_payload['content'], str):
        user_input_content = content_payload['content']
    else:
        logger.warning(f"[{session_id}] Received non-string or unexpected content for user_message: {type(content_payload)}. Ignoring.")
        return

    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id: # Should not happen if UI enforces task selection
        logger.warning(f"[{session_id}] User message received but no task active.")
        await send_ws_message_func("status_message", {"text": "Please select or create a task first.", "component_hint": COMPONENT_HINT_SYSTEM, "isError": True})
        return

    if (connected_clients_entry.get("agent_task") or session_data_entry.get("plan_execution_active")):
        logger.warning(f"[{session_id}] User message received while agent/plan is already running for task {active_task_id}.")
        await send_ws_message_func("status_message", {"text": "Agent is busy. Please wait or stop the current process.", "component_hint": COMPONENT_HINT_SYSTEM})
        return

    await db_add_message_func(active_task_id, session_id, "user_input", user_input_content)
    await add_monitor_log_func(f"User Input: {user_input_content}", "monitor_user_input")


    session_data_entry['original_user_query'] = user_input_content
    session_data_entry['cancellation_requested'] = False
    session_data_entry['active_plan_filename'] = None # Reset for new query
    session_data_entry['current_plan_proposal_id_backend'] = None


    await _send_thinking_update_from_handler(
        send_ws_message_func, active_task_id, session_id, db_add_message_func, # Pass DB func
        message_text="Classifying intent...",
        status_key="INTENT_CLASSIFICATION_START",
        component_hint=COMPONENT_HINT_INTENT_CLASSIFIER,
        sub_type=SUB_TYPE_SUB_STATUS # Display as a sub-status
    )

    dynamic_tools = get_dynamic_tools(active_task_id)
    tools_summary_for_intent = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])

    classified_intent = await classify_intent(user_input_content, tools_summary_for_intent)
    await add_monitor_log_func(f"Intent classified as: {classified_intent}", f"{COMPONENT_HINT_SYSTEM}_INTENT_CLASSIFIED")
    # Send intent classification result as a sub-status
    await _send_thinking_update_from_handler(
        send_ws_message_func, active_task_id, session_id, db_add_message_func,
        message_text=f"Intent: {classified_intent}",
        status_key="INTENT_CLASSIFIED",
        component_hint=COMPONENT_HINT_INTENT_CLASSIFIER,
        sub_type=SUB_TYPE_SUB_STATUS
    )


    if classified_intent == "PLAN":
        await _send_thinking_update_from_handler(
            send_ws_message_func, active_task_id, session_id, db_add_message_func,
            message_text="Generating plan...",
            status_key="PLAN_GENERATION_START",
            component_hint=COMPONENT_HINT_PLANNER,
            sub_type=SUB_TYPE_SUB_STATUS
        )
        # ... (plan generation logic remains the same) ...
        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content,
            available_tools_summary=tools_summary_for_intent
        )
        if human_plan_summary and structured_plan_steps:
            plan_id = str(uuid.uuid4())
            session_data_entry["current_plan_proposal_id_backend"] = plan_id
            session_data_entry["current_plan_human_summary"] = human_plan_summary
            session_data_entry["current_plan_structured"] = structured_plan_steps
            # ... (rest of plan proposal sending and artifact saving)
            # ... (This part does not generate new sub-statuses or thoughts directly, it sends 'propose_plan_for_confirmation')
            plan_proposal_filename = f"_plan_proposal_{plan_id}.md"
            plan_proposal_markdown_content = [f"# Agent Plan Proposal\n\n## Plan ID: {plan_id}\n"]
            plan_proposal_markdown_content.append(f"## Original User Query:\n{user_input_content}\n")
            plan_proposal_markdown_content.append(f"## Proposed Plan Summary:\n{human_plan_summary}\n")
            plan_proposal_markdown_content.append("## Proposed Steps:\n")
            for i, step_data_dict in enumerate(structured_plan_steps):
                desc = step_data_dict.get('description', 'N/A'); tool_sugg = step_data_dict.get('tool_to_use', 'None')
                input_instr = step_data_dict.get('tool_input_instructions', 'None'); expected_out = step_data_dict.get('expected_outcome', 'N/A')
                plan_proposal_markdown_content.append(f"{i+1}. **{desc}**")
                plan_proposal_markdown_content.append(f"    - Tool Suggestion: `{tool_sugg}`")
                plan_proposal_markdown_content.append(f"    - Input Instructions: `{input_instr}`")
                plan_proposal_markdown_content.append(f"    - Expected Outcome: `{expected_out}`\n")

            task_workspace_path = get_task_workspace_path(active_task_id, create_if_not_exists=True)
            try:
                proposal_file_path = task_workspace_path / plan_proposal_filename
                async with aiofiles.open(proposal_file_path, 'w', encoding='utf-8') as f:
                    await f.write("\n".join(plan_proposal_markdown_content))
                logger.info(f"[{session_id}] Saved plan proposal to artifact: {proposal_file_path}")
                await add_monitor_log_func(f"Plan proposal saved to artifact: {plan_proposal_filename}", f"{COMPONENT_HINT_SYSTEM}_INFO")
                await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})
            except Exception as e:
                logger.error(f"[{session_id}] Failed to save plan proposal artifact '{plan_proposal_filename}': {e}", exc_info=True)

            await send_ws_message_func("propose_plan_for_confirmation", {
                "plan_id": plan_id,
                "human_summary": human_plan_summary,
                "structured_plan": structured_plan_steps
            })
            await add_monitor_log_func(f"Plan generated (ID: {plan_id}). Awaiting user confirmation.", f"{COMPONENT_HINT_SYSTEM}_PLAN_GENERATED")
            await _send_thinking_update_from_handler( # For bottom line
                send_ws_message_func, active_task_id, session_id, db_add_message_func,
                message_text="Awaiting plan confirmation...",
                status_key="AWAITING_PLAN_CONFIRMATION",
                component_hint=COMPONENT_HINT_SYSTEM,
                sub_type=SUB_TYPE_BOTTOM_LINE
            )
        else: # Failed to generate plan
            logger.error(f"[{session_id}] Failed to generate a plan for query: {user_input_content}")
            await add_monitor_log_func(f"Error: Failed to generate a plan.", f"{COMPONENT_HINT_SYSTEM}_ERROR")
            await send_ws_message_func("status_message", {"text": "Error: Could not generate a plan for your request.", "component_hint": COMPONENT_HINT_PLANNER, "isError": True})
            await send_ws_message_func("agent_message", {"content": "I'm sorry, I couldn't create a plan for that request. Please try rephrasing or breaking it down.", "component_hint": COMPONENT_HINT_PLANNER})
            await _send_thinking_update_from_handler( # For bottom line
                send_ws_message_func, active_task_id, session_id, db_add_message_func,
                message_text="Planning failed.", status_key="PLAN_FAILED", component_hint=COMPONENT_HINT_PLANNER, sub_type=SUB_TYPE_BOTTOM_LINE)

    elif classified_intent == "DIRECT_QA":
        await _send_thinking_update_from_handler( # For bottom line
            send_ws_message_func, active_task_id, session_id, db_add_message_func,
            message_text="Processing directly...",
            status_key="DIRECT_QA_START",
            component_hint=COMPONENT_HINT_EXECUTOR, # DirectQA uses executor
            sub_type=SUB_TYPE_BOTTOM_LINE
        )
        # ... (Direct QA logic remains largely the same, callbacks will handle sub-statuses/thoughts from agent execution)
        # ... (The final agent_message and status_message will be sent as before)
        await add_monitor_log_func(f"Handling as DIRECT_QA. Invoking ReAct agent.", f"{COMPONENT_HINT_SYSTEM}_DIRECT_QA")
        executor_provider = session_data_entry.get("selected_llm_provider", settings.executor_default_provider)
        executor_model_name = session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name)
        direct_qa_llm: Optional[BaseChatModel] = None
        try:
            llm_instance = get_llm(settings, provider=executor_provider, model_name=executor_model_name, requested_for_role="DirectQA_Executor")
            direct_qa_llm = llm_instance # type: ignore
        except Exception as llm_init_err:
            logger.error(f"[{session_id}] Failed to initialize LLM for Direct QA: {llm_init_err}", exc_info=True)
            await send_ws_message_func("status_message", {"text": "Error: Failed to prepare for answering.", "component_hint": COMPONENT_HINT_SYSTEM, "isError": True})
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Direct QA failed.", "DIRECT_QA_FAILED", COMPONENT_HINT_EXECUTOR, SUB_TYPE_BOTTOM_LINE)
            return

        dynamic_tools = get_dynamic_tools(active_task_id)
        direct_qa_memory = session_data_entry["memory"]
        direct_qa_callback_handler = session_data_entry["callback_handler"]
        step_result_from_executor = None
        try:
            agent_executor_direct = create_agent_executor(llm=direct_qa_llm, tools=dynamic_tools, memory=direct_qa_memory, max_iterations=settings.agent_max_iterations)
            direct_qa_task = asyncio.create_task(agent_executor_direct.ainvoke({"input": user_input_content}, config=RunnableConfig(callbacks=[direct_qa_callback_handler])))
            connected_clients_entry["agent_task"] = direct_qa_task
            step_result_from_executor = await direct_qa_task

            if step_result_from_executor and 'output' in step_result_from_executor:
                final_output_content = step_result_from_executor['output']
                await send_ws_message_func("agent_message", {"content": final_output_content, "component_hint": COMPONENT_HINT_EXECUTOR})
                await db_add_message_func(active_task_id, session_id, "agent_message", final_output_content)
            else:
                await send_ws_message_func("status_message", {"text": "Error: Agent finished but could not retrieve the answer.", "component_hint": COMPONENT_HINT_EXECUTOR, "isError": True})
        except AgentCancelledException:
            await send_ws_message_func("status_message", {"text": "Direct QA cancelled.", "component_hint": COMPONENT_HINT_SYSTEM})
        except Exception as e:
            await send_ws_message_func("status_message", {"text": f"Error during direct processing: {type(e).__name__}", "component_hint": COMPONENT_HINT_EXECUTOR, "isError": True})
        finally:
            connected_clients_entry["agent_task"] = None
            final_status_key = "IDLE"; final_message = "Idle."; final_component = COMPONENT_HINT_SYSTEM
            if session_data_entry.get('cancellation_requested', False): final_status_key = "CANCELLED"; final_message = "Cancelled."
            elif step_result_from_executor and 'output' in step_result_from_executor and step_result_from_executor['output']: final_status_key = "DIRECT_QA_COMPLETED"; final_message = "Direct response generated."; final_component = COMPONENT_HINT_EXECUTOR
            else: final_status_key = "DIRECT_QA_FAILED"; final_message = "Processing failed or no output."; final_component = COMPONENT_HINT_EXECUTOR
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, final_message, final_status_key, final_component, SUB_TYPE_BOTTOM_LINE)
            session_data_entry['cancellation_requested'] = False
    else: # Should not happen
        await send_ws_message_func("status_message", {"text": "Error: Unknown intent.", "component_hint": COMPONENT_HINT_INTENT_CLASSIFIER, "isError": True})


async def process_execute_confirmed_plan(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc
) -> None:
    logger.info(f"[{session_id}] Received 'execute_confirmed_plan' with plan_id: {data.get('plan_id')}")
    active_task_id = session_data_entry.get("current_task_id")
    # ... (validation for active_task_id, confirmed_plan_steps_dicts, confirmed_plan_id_from_frontend remains the same) ...
    if not active_task_id: # Should not happen
        await send_ws_message_func("status_message", {"text": "Error: No active task to execute plan for.", "component_hint": COMPONENT_HINT_SYSTEM, "isError": True})
        return
    confirmed_plan_id_from_frontend = data.get("plan_id")
    confirmed_plan_steps_dicts = data.get("confirmed_plan")
    if not confirmed_plan_steps_dicts or not isinstance(confirmed_plan_steps_dicts, list):
        await send_ws_message_func("status_message", {"text": "Error: Invalid plan received for execution.", "component_hint": COMPONENT_HINT_SYSTEM, "isError": True})
        return
    if not confirmed_plan_id_from_frontend:
        confirmed_plan_id_from_frontend = session_data_entry.get("current_plan_proposal_id_backend", str(uuid.uuid4()))


    # Save confirmed plan log to DB (remains the same)
    confirmed_plan_chat_log_content = { "plan_id": confirmed_plan_id_from_frontend, "summary": session_data_entry.get("current_plan_human_summary", "N/A"), "steps": confirmed_plan_steps_dicts, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() }
    await db_add_message_func(active_task_id, session_id, "confirmed_plan_log", json.dumps(confirmed_plan_chat_log_content))

    session_data_entry["current_plan_structured"] = confirmed_plan_steps_dicts
    session_data_entry["current_plan_step_index"] = 0
    session_data_entry["plan_execution_active"] = True
    session_data_entry['cancellation_requested'] = False

    await add_monitor_log_func(f"User confirmed plan (ID: {confirmed_plan_id_from_frontend}). Starting execution.", f"{COMPONENT_HINT_SYSTEM}_PLAN_CONFIRMED")
    await _send_thinking_update_from_handler( # For bottom line
        send_ws_message_func, active_task_id, session_id, db_add_message_func,
        message_text=f"Executing plan ({len(confirmed_plan_steps_dicts)} steps)...",
        status_key="PLAN_EXECUTION_START",
        component_hint=COMPONENT_HINT_SYSTEM,
        sub_type=SUB_TYPE_BOTTOM_LINE
    )

    # ... (plan execution filename and markdown saving logic remains the same) ...
    plan_execution_filename = f"_plan_{confirmed_plan_id_from_frontend}.md"
    session_data_entry['active_plan_filename'] = plan_execution_filename
    # ... (markdown content generation) ...
    plan_markdown_content = [f"# Agent Executed Plan for Task: {active_task_id}\n"] # ... etc.
    task_workspace_path = get_task_workspace_path(active_task_id, create_if_not_exists=True)
    try:
        plan_file_path = task_workspace_path / plan_execution_filename
        async with aiofiles.open(plan_file_path, 'w', encoding='utf-8') as f:
            await f.write("\n".join(plan_markdown_content)) # Assuming plan_markdown_content is built
        await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})
    except Exception as e:
        logger.error(f"[{session_id}] Failed to save execution plan to file '{plan_execution_filename}': {e}")


    plan_failed_definitively = False
    preliminary_final_answer_from_last_step = "Plan execution completed without a specific final message output."
    step_execution_details_list = []
    original_user_query = session_data_entry.get("original_user_query", "N/A")
    last_successful_step_output: Optional[str] = None

    for i, step_dict_from_plan in enumerate(confirmed_plan_steps_dicts):
        current_step_number = i + 1
        current_plan_step_obj: Optional[PlanStep] = None
        try: current_plan_step_obj = PlanStep(**step_dict_from_plan)
        except Exception as p_err: # ... error handling ...
            plan_failed_definitively = True; break
        
        step_description = current_plan_step_obj.description
        # Announce major step and SAVE IT TO DB
        major_step_data_for_db = {
            "step_number": current_step_number,
            "total_steps": len(confirmed_plan_steps_dicts),
            "description": step_description,
            "component_hint": COMPONENT_HINT_CONTROLLER # Or SYSTEM if more appropriate for announcement
        }
        await send_ws_message_func("agent_major_step_announcement", major_step_data_for_db)
        await _save_message_to_db_from_handler(active_task_id, session_id, db_add_message_func, DB_MSG_TYPE_MAJOR_STEP, major_step_data_for_db)

        if session_data_entry.get('cancellation_requested', False): # ... cancellation handling ...
            plan_failed_definitively = True; break

        # ... (Rest of the step execution loop: Controller, Executor, Evaluator) ...
        # ... (Callbacks will handle sending and saving sub-statuses and thoughts) ...
        # ... (The logic for retries, success/failure of step remains the same) ...
        # --- Example of where a Controller might generate a "thought" if not handled by callback ---
        # if controller_generated_thought_text:
        #     await _send_thinking_update_from_handler(
        #         send_ws_message_func, active_task_id, session_id, db_add_message_func,
        #         message_text=controller_generated_thought_text,
        #         status_key="CONTROLLER_THOUGHT", # Or more specific
        #         component_hint=COMPONENT_HINT_CONTROLLER,
        #         sub_type=SUB_TYPE_THOUGHT,
        #         thought_label="Controller reasoning:"
        #     )
        # ---
        # For this loop, we assume callbacks.py handles most of the SUB_STATUS and THOUGHT messages.
        # This handler mainly focuses on the overall flow and major step announcements.
        # The core loop for validate_and_prepare_step_action, agent_executor.ainvoke, evaluate_step_outcome
        # remains the same. The callbacks attached to the agent_executor will send the detailed thinking updates.

        # --- Start of placeholder for the inner while loop for retries ---
        retry_count_for_current_step = 0
        step_succeeded_after_attempts = False
        last_step_correction_suggestion: Optional[StepCorrectionOutcome] = None

        while retry_count_for_current_step <= MAX_STEP_RETRIES:
            if session_data_entry.get('cancellation_requested', False):
                plan_failed_definitively = True; break # Break while

            # Controller validation
            # This might generate a "Controller thought" via callback if LLM is used internally by controller
            await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, f"Controller validating Step {current_step_number} (Attempt {retry_count_for_current_step + 1})", "CONTROLLER_VALIDATING", COMPONENT_HINT_CONTROLLER, SUB_TYPE_SUB_STATUS)
            validated_tool_name, formulated_tool_input, controller_reasoning, controller_confidence = await validate_and_prepare_step_action(
                original_user_query=original_user_query, plan_step=current_plan_step_obj, 
                available_tools=get_dynamic_tools(active_task_id), 
                session_data_entry=session_data_entry, previous_step_output=last_successful_step_output
            )
            # If controller_reasoning is substantial, it could be sent as a THOUGHT via callback or here.
            # For now, assuming callbacks.py handles detailed thoughts from LLM calls within controller.

            # Executor
            # Callbacks inside agent_executor will send thoughts, tool_start/end/error as sub_statuses
            # ... (agent_executor.ainvoke logic) ...
            step_executor_output_str = f"Simulated output for step {current_step_number}" # Placeholder
            last_successful_step_output = step_executor_output_str # Assume success for now
            step_succeeded_after_attempts = True # Placeholder

            # Evaluator
            # Callbacks inside evaluator might send thoughts if it uses an LLM
            # ... (evaluate_step_outcome_and_suggest_correction logic) ...
            
            if step_succeeded_after_attempts:
                break # Break while
            retry_count_for_current_step += 1
        # --- End of placeholder for the inner while loop ---

        if plan_failed_definitively or not step_succeeded_after_attempts:
            await _update_plan_file_step_status(task_workspace_path, plan_execution_filename, current_step_number, "!")
            plan_failed_definitively = True; break # Break for

        await _update_plan_file_step_status(task_workspace_path, plan_execution_filename, current_step_number, "x")
        preliminary_final_answer_from_last_step = last_successful_step_output


    # ... (Overall plan evaluation and final message sending logic remains the same) ...
    # ... (Ensure final "Idle." status is sent via _send_thinking_update_from_handler with SUB_TYPE_BOTTOM_LINE) ...
    session_data_entry["plan_execution_active"] = False
    # ... (Build executed_plan_summary_str) ...
    executed_plan_summary_str = "Summary of executed plan..." # Placeholder
    final_message_to_user_for_eval = preliminary_final_answer_from_last_step
    if plan_failed_definitively: final_message_to_user_for_eval = "Plan execution failed or was cancelled."
    
    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, "Evaluating overall outcome...", "OVERALL_EVAL_START", COMPONENT_HINT_EVALUATOR_OVERALL, SUB_TYPE_BOTTOM_LINE)
    overall_evaluation_result = await evaluate_plan_outcome(original_user_query, executed_plan_summary_str, final_message_to_user_for_eval, session_data_entry)
    # ... (process overall_evaluation_result and send final agent_message) ...
    final_chat_message = overall_evaluation_result.assessment if overall_evaluation_result else final_message_to_user_for_eval
    await send_ws_message_func("agent_message", {"content": final_chat_message, "component_hint": COMPONENT_HINT_EVALUATOR_OVERALL if overall_evaluation_result else COMPONENT_HINT_SYSTEM})
    await db_add_message_func(active_task_id, session_id, "agent_message", final_chat_message)

    final_bottom_line_text = "Idle."
    final_bottom_line_key = "IDLE"
    if plan_failed_definitively: final_bottom_line_text = "Idle (Plan Stopped)."; final_bottom_line_key = "PLAN_STOPPED"
    await _send_thinking_update_from_handler(send_ws_message_func, active_task_id, session_id, db_add_message_func, final_bottom_line_text, final_bottom_line_key, COMPONENT_HINT_SYSTEM, SUB_TYPE_BOTTOM_LINE)
    session_data_entry['current_plan_proposal_id_backend'] = None


async def process_cancel_plan_proposal(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
    # No db_add_message_func needed here as cancelling a proposal is ephemeral
) -> None:
    # ... (This function remains the same, no DB persistence needed for cancellation itself) ...
    plan_id_to_cancel = data.get("plan_id")
    logger.info(f"[{session_id}] Received 'cancel_plan_proposal' for plan_id: {plan_id_to_cancel}")
    if not plan_id_to_cancel: return

    backend_proposed_plan_id = session_data_entry.get("current_plan_proposal_id_backend")
    if backend_proposed_plan_id == plan_id_to_cancel:
        session_data_entry['current_plan_proposal_id_backend'] = None # Clear it
        # ... (rest of state clearing) ...
        await add_monitor_log_func(f"Plan proposal (ID: {plan_id_to_cancel}) cancelled by user.", f"{COMPONENT_HINT_SYSTEM}_PLAN_CANCELLED")
        # Send an update for the bottom line
        active_task_id = session_data_entry.get("current_task_id") # Get task_id for the helper
        # For _send_thinking_update_from_handler, db_add_message_func is needed in signature, but won't be used if sub_type is bottom_line and no DB saving for it
        # However, to be safe, let's assume we might want to log this "Idle" state if it were a sub_status.
        # Since it's a bottom_line update, it won't be saved by the helper.
        dummy_db_add = lambda tid, sid, mtype, cont: asyncio.sleep(0) # Dummy async func
        await _send_thinking_update_from_handler(
            send_ws_message_func, active_task_id, session_id, dummy_db_add,
            "Idle.", "IDLE", COMPONENT_HINT_SYSTEM, SUB_TYPE_BOTTOM_LINE
        )
        await send_ws_message_func("status_message", {"text": f"Plan proposal (ID: {plan_id_to_cancel[:8]}...) cancelled.", "component_hint": COMPONENT_HINT_SYSTEM})
    else:
        logger.warning(f"[{session_id}] Mismatched plan_id for cancellation: frontend '{plan_id_to_cancel}', backend '{backend_proposed_plan_id}'.")

