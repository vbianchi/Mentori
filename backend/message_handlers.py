import logging
import json
import datetime
from typing import Dict, Any, Callable, Coroutine, Optional, List
import asyncio
import shutil
from pathlib import Path
import aiofiles # For async file writing
import re # For updating plan file

# LangChain Imports
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool # For type hinting available_tools

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT
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

# --- Type Hints for Passed-in Functions ---
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
DBAddTaskFunc = Callable[[str, str, str], Coroutine[Any, Any, None]]
DBGetMessagesFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, Any]]]]
DBDeleteTaskFunc = Callable[[str], Coroutine[Any, Any, bool]]
DBRenameTaskFunc = Callable[[str, str], Coroutine[Any, Any, bool]]
GetArtifactsFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, str]]]]
ExecuteShellCommandFunc = Callable[[str, str, SendWSMessageFunc, DBAddMessageFunc, Optional[str]], Coroutine[Any, Any, bool]]

# --- Configuration for Step Retries ---
MAX_STEP_RETRIES = settings.agent_max_step_retries # Use from .env via config

async def _update_plan_file_step_status(
    task_workspace_path: Path,
    plan_filename: str,
    step_number: int, # 1-indexed
    status_char: str # "x" for done, "!" for error, "-" for cancelled/skipped
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
        # Regex to find a markdown list item like: "- [ ] 1. Description" or "- [x] 1. ..." etc.
        # It looks for the start of a list item, optional whitespace, the checkbox, optional whitespace,
        # the step number followed by a period, then at least one space, and then any characters.
        step_pattern = re.compile(rf"^\s*-\s*\[\s*[ x!-]?\s*\]\s*{re.escape(str(step_number))}\.\s+.*", re.IGNORECASE)
        # Regex to specifically target the checkbox content for replacement
        checkbox_pattern = re.compile(r"(\s*-\s*\[)\s*[ x!-]?\s*(\])")


        for line_no, line_content in enumerate(lines):
            if not found_step and step_pattern.match(line_content):
                # Replace only the character inside the checkbox
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


async def process_context_switch(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc,
    db_add_task_func: DBAddTaskFunc, db_get_messages_func: DBGetMessagesFunc,
    get_artifacts_func: GetArtifactsFunc
) -> None:
    task_id_from_frontend = data.get("taskId")
    task_title_from_frontend = data.get("task")

    logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")

    session_data_entry['cancellation_requested'] = False
    session_data_entry['current_plan_structured'] = None
    session_data_entry['current_plan_human_summary'] = None
    session_data_entry['current_plan_step_index'] = -1
    session_data_entry['plan_execution_active'] = False
    session_data_entry['original_user_query'] = None
    session_data_entry['active_plan_filename'] = None

    existing_agent_task = connected_clients_entry.get("agent_task")
    if existing_agent_task and not existing_agent_task.done():
        logger.warning(f"[{session_id}] Cancelling active agent/plan task due to context switch.")
        existing_agent_task.cancel()
        await send_ws_message_func("status_message", "Operation cancelled due to task switch.")
        await add_monitor_log_func("Agent/Plan operation cancelled due to context switch.", "system_cancel")
        connected_clients_entry["agent_task"] = None

    session_data_entry["current_task_id"] = task_id_from_frontend
    if "callback_handler" in session_data_entry:
        session_data_entry["callback_handler"].set_task_id(task_id_from_frontend)

    await db_add_task_func(task_id_from_frontend, task_title_from_frontend or f"Task {task_id_from_frontend}", datetime.datetime.now(datetime.timezone.utc).isoformat())

    try:
        _ = get_task_workspace_path(task_id_from_frontend)
        logger.info(f"[{session_id}] Ensured workspace directory exists for task: {task_id_from_frontend}")
    except (ValueError, OSError) as ws_path_e:
        logger.error(f"[{session_id}] Failed to get/create workspace path for task {task_id_from_frontend} during context switch: {ws_path_e}")

    await add_monitor_log_func(f"Switched context to task ID: {task_id_from_frontend} ('{task_title_from_frontend}')", "system_context_switch")

    if "memory" in session_data_entry:
        try:
            session_data_entry["memory"].clear()
            logger.info(f"[{session_id}] Cleared agent memory for new task context.")
        except Exception as mem_e:
            logger.error(f"[{session_id}] Failed to clear memory on context switch: {mem_e}")

    history_messages = await db_get_messages_func(task_id_from_frontend)
    chat_history_for_memory = []
    if history_messages:
        logger.info(f"[{session_id}] Loading {len(history_messages)} history messages for task {task_id_from_frontend}.")
        await send_ws_message_func("history_start", f"Loading {len(history_messages)} messages...")
        for i, msg_hist in enumerate(history_messages):
            db_msg_type = msg_hist.get('message_type', 'unknown')
            db_content_hist = msg_hist.get('content', '')
            db_timestamp = msg_hist.get('timestamp', datetime.datetime.now().isoformat())
            ui_msg_type = None
            content_to_send = db_content_hist
            send_to_chat = False

            if db_msg_type == "user_input":
                ui_msg_type = "user"; send_to_chat = True
                chat_history_for_memory.append(HumanMessage(content=db_content_hist))
            elif db_msg_type in ["agent_finish", "agent_message", "agent", "agent_final_assessment"]: # Ensure agent_final_assessment is handled
                ui_msg_type = "agent_message"; send_to_chat = True
                chat_history_for_memory.append(AIMessage(content=db_content_hist))
            elif db_msg_type == "artifact_generated":
                pass # Do not send to chat, but could be logged to monitor if desired
            elif db_msg_type.startswith(("monitor_", "error_", "system_", "tool_", "agent_thought_", "monitor_user_input", "llm_token_usage")):
                ui_msg_type = "monitor_log"
                log_prefix_hist = f"[{db_timestamp}][{session_id[:8]}]" # Reconstruct a similar prefix
                # Make type indicator more compact for history logs
                type_indicator_hist = f"[{db_msg_type.replace('monitor_', '').replace('error_', 'ERR_').replace('system_', 'SYS_').replace('agent_thought_action', 'THOUGHT_ACT').replace('agent_thought_final', 'THOUGHT_FIN').replace('monitor_user_input', 'USER_INPUT_LOG').replace('llm_token_usage', 'TOKEN_LOG').upper()}]"
                content_to_send = f"{log_prefix_hist} [History]{type_indicator_hist} {db_content_hist}"
                send_to_chat = False # Monitor logs are not re-sent to chat, only to monitor
            else:
                # Unknown type, log to monitor for debugging
                send_to_chat = False # Don't send to chat
                logger.warning(f"[{session_id}] Unknown history message type '{db_msg_type}' encountered.")
                await send_ws_message_func("monitor_log", f"[{db_timestamp}][{session_id[:8]}] [History][UNKNOWN_TYPE: {db_msg_type}] {db_content_hist}")

            if ui_msg_type:
                if send_to_chat:
                    await send_ws_message_func(ui_msg_type, content_to_send)
                elif ui_msg_type == "monitor_log": # Ensure monitor logs from history go to monitor
                    await send_ws_message_func("monitor_log", content_to_send)
                await asyncio.sleep(0.005) # Small delay to allow UI to process messages

        await send_ws_message_func("history_end", "History loaded.")
        logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")

        # Repopulate agent memory
        MAX_MEMORY_RELOAD = settings.agent_memory_window_k
        if "memory" in session_data_entry:
            try:
                # Filter for only HumanMessage and AIMessage for memory repopulation
                # This ensures system messages or other types don't clutter agent memory
                relevant_memory_messages = [m for m in chat_history_for_memory if isinstance(m, (HumanMessage, AIMessage))]
                session_data_entry["memory"].chat_memory.messages = relevant_memory_messages[-MAX_MEMORY_RELOAD:]
                logger.info(f"[{session_id}] Repopulated agent memory with last {len(session_data_entry['memory'].chat_memory.messages)} relevant messages.")
            except Exception as mem_load_e:
                logger.error(f"[{session_id}] Failed to repopulate memory from history: {mem_load_e}")
    else:
        await send_ws_message_func("history_end", "No history found.")
        logger.info(f"[{session_id}] No history found for task {task_id_from_frontend}.")

    logger.info(f"[{session_id}] Getting current artifacts from filesystem for task {task_id_from_frontend}...")
    current_artifacts = await get_artifacts_func(task_id_from_frontend)
    await send_ws_message_func("update_artifacts", current_artifacts)
    logger.info(f"[{session_id}] Sent current artifact list ({len(current_artifacts)} items) for task {task_id_from_frontend}.")


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
    session_data_entry['active_plan_filename'] = None # Reset active plan file for new query

    await send_ws_message_func("agent_thinking_update", {"status": "Classifying intent..."})

    dynamic_tools = get_dynamic_tools(active_task_id)
    tools_summary_for_intent = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])

    # Determine LLM for Intent Classification
    intent_llm_id_override = session_data_entry.get("session_intent_classifier_llm_id")
    intent_provider = settings.intent_classifier_provider
    intent_model_name = settings.intent_classifier_model_name
    if intent_llm_id_override:
        try:
            intent_provider, intent_model_name = intent_llm_id_override.split("::", 1)
            logger.info(f"[{session_id}] Using session override for Intent Classifier: {intent_llm_id_override}")
        except ValueError:
            logger.warning(f"[{session_id}] Invalid session LLM ID format for Intent Classifier '{intent_llm_id_override}'. Using system default.")
    # LLM instance for intent is fetched inside classify_intent based on these provider/model_name

    classified_intent = await classify_intent(
        user_input_content,
        # Pass provider and model_name to classify_intent if it needs to fetch its own LLM
        # For now, assuming classify_intent uses the settings or is passed an LLM instance
        available_tools_summary=tools_summary_for_intent
    )
    await add_monitor_log_func(f"Intent classified as: {classified_intent}", "system_intent_classified")

    if classified_intent == "PLAN":
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan..."})

        # Determine LLM for Planner
        planner_llm_id_override = session_data_entry.get("session_planner_llm_id")
        planner_provider = settings.planner_provider
        planner_model_name = settings.planner_model_name
        if planner_llm_id_override:
            try:
                planner_provider, planner_model_name = planner_llm_id_override.split("::", 1)
                logger.info(f"[{session_id}] Using session override for Planner: {planner_llm_id_override}")
            except ValueError:
                logger.warning(f"[{session_id}] Invalid session LLM ID format for Planner '{planner_llm_id_override}'. Using system default.")
        # LLM instance for planner is fetched inside generate_plan

        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content,
            available_tools_summary=tools_summary_for_intent
            # Pass planner_provider and planner_model_name if generate_plan needs to fetch its own LLM
        )

        if human_plan_summary and structured_plan_steps:
            session_data_entry["current_plan_human_summary"] = human_plan_summary
            session_data_entry["current_plan_structured"] = structured_plan_steps
            session_data_entry["current_plan_step_index"] = 0 # Start at the first step
            session_data_entry["plan_execution_active"] = False # Not active until confirmed

            await send_ws_message_func("display_plan_for_confirmation", {
                "human_summary": human_plan_summary,
                "structured_plan": structured_plan_steps # Send as list of dicts
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

        # Use session-selected Executor LLM or system default for Executor
        executor_provider = session_data_entry.get("selected_llm_provider", settings.executor_default_provider)
        executor_model_name = session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name)
        logger.info(f"[{session_id}] Using LLM for Direct QA (Executor role): {executor_provider}::{executor_model_name}")

        direct_qa_llm: Optional[BaseChatModel] = None
        try:
            # Get LLM instance using the determined provider and model
            llm_instance = get_llm(settings, provider=executor_provider, model_name=executor_model_name, requested_for_role="DirectQA_Executor")
            if not isinstance(llm_instance, BaseChatModel): # Ensure it's a chat model if create_react_agent expects one
                logger.warning(f"LLM for Direct QA is not BaseChatModel, it's {type(llm_instance)}. This might cause issues if a chat model is strictly required.")
            direct_qa_llm = llm_instance # type: ignore
        except Exception as llm_init_err:
            logger.error(f"[{session_id}] Failed to initialize LLM for Direct QA: {llm_init_err}", exc_info=True)
            await add_monitor_log_func(f"Error initializing LLM for Direct QA: {llm_init_err}", "error_system")
            await send_ws_message_func("status_message", "Error: Failed to prepare for answering.")
            await send_ws_message_func("agent_message", "Sorry, I couldn't initialize my reasoning module to answer.")
            await send_ws_message_func("agent_thinking_update", {"status": "Direct QA failed."})
            return

        direct_qa_memory = session_data_entry["memory"]
        direct_qa_callback_handler = session_data_entry["callback_handler"]

        try:
            agent_executor_direct = create_agent_executor(
                llm=direct_qa_llm, # type: ignore
                tools=dynamic_tools,
                memory=direct_qa_memory,
                max_iterations=settings.agent_max_iterations # Use from settings
            )

            logger.info(f"[{session_id}] Invoking AgentExecutor directly for QA with input: '{user_input_content[:100]}...'")

            direct_qa_task = asyncio.create_task(
                agent_executor_direct.ainvoke(
                    {"input": user_input_content},
                    config=RunnableConfig(callbacks=[direct_qa_callback_handler])
                )
            )
            connected_clients_entry["agent_task"] = direct_qa_task

            await direct_qa_task # Wait for the agent to finish

        except AgentCancelledException:
            logger.warning(f"[{session_id}] Direct QA execution cancelled by user.")
            await send_ws_message_func("status_message", "Direct QA cancelled.")
            await add_monitor_log_func("Direct QA cancelled by user.", "system_cancel")
        except Exception as e:
            logger.error(f"[{session_id}] Error during direct QA execution: {e}", exc_info=True)
            await add_monitor_log_func(f"Error during direct QA: {e}", "error_direct_qa")
            await send_ws_message_func("agent_message", f"Sorry, I encountered an error trying to answer directly: {e}")
            await send_ws_message_func("status_message", "Error during direct processing.")
        finally:
            connected_clients_entry["agent_task"] = None # Clear the task
            await send_ws_message_func("agent_thinking_update", {"status": "Idle."}) # Reset UI status

    else: # Should not happen if classify_intent is robust
        logger.error(f"[{session_id}] Unknown intent classified: {classified_intent}. Defaulting to planning.")
        await add_monitor_log_func(f"Error: Unknown intent '{classified_intent}'. Defaulting to PLAN.", "error_system")
        # Fallback to planning (similar to PLAN block)
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan (fallback)..."})
        # ... (rest of fallback planning logic as before) ...
        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content, available_tools_summary=tools_summary_for_intent
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
            await add_monitor_log_func(f"Plan generated (fallback). Summary: {human_plan_summary}. Steps: {len(structured_plan_steps)}. Awaiting user confirmation.", "system_plan_generated")
            await send_ws_message_func("status_message", "Plan generated. Please review and confirm.")
            await send_ws_message_func("agent_thinking_update", {"status": "Awaiting plan confirmation..."})
        else:
            logger.error(f"[{session_id}] Failed to generate a plan (fallback) for query: {user_input_content}")
            await add_monitor_log_func(f"Error: Failed to generate a plan (fallback).", "error_system")
            await send_ws_message_func("status_message", "Error: Could not generate a plan for your request (fallback).")
            await send_ws_message_func("agent_message", "I'm sorry, I couldn't create a plan for that request. Please try rephrasing or breaking it down.")
            await send_ws_message_func("agent_thinking_update", {"status": "Planning failed."})


async def process_execute_confirmed_plan(
    session_id: str,
    data: Dict[str, Any],
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_add_message_func: DBAddMessageFunc # Added db_add_message_func to parameters
) -> None:
    logger.info(f"[{session_id}] Received 'execute_confirmed_plan'.")
    active_task_id = session_data_entry.get("current_task_id")
    if not active_task_id:
        logger.warning(f"[{session_id}] 'execute_confirmed_plan' received but no active task.")
        await send_ws_message_func("status_message", "Error: No active task to execute plan for.")
        return

    # The plan should be a list of step dictionaries
    confirmed_plan_steps_dicts = data.get("confirmed_plan")
    if not confirmed_plan_steps_dicts or not isinstance(confirmed_plan_steps_dicts, list):
        logger.error(f"[{session_id}] Invalid or missing plan in 'execute_confirmed_plan' message. Data received: {data}")
        await send_ws_message_func("status_message", "Error: Invalid plan received for execution.")
        return

    # Store the confirmed plan (list of dicts) in session_data
    session_data_entry["current_plan_structured"] = confirmed_plan_steps_dicts
    session_data_entry["current_plan_step_index"] = 0 # Start at the first step
    session_data_entry["plan_execution_active"] = True
    session_data_entry['cancellation_requested'] = False # Reset cancellation flag

    await add_monitor_log_func(f"User confirmed plan. Starting execution of {len(confirmed_plan_steps_dicts)} steps.", "system_plan_confirmed")
    await send_ws_message_func("status_message", "Plan confirmed. Executing steps...")

    # Save plan to a file
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    plan_filename = f"_plan_{timestamp_str}.md"
    session_data_entry['active_plan_filename'] = plan_filename # Store for updating status

    plan_markdown_content = [f"# Agent Plan for Task: {active_task_id}\n"]
    plan_markdown_content.append(f"## Plan ID: {timestamp_str}\n")
    original_query_for_plan_file = session_data_entry.get('original_user_query', 'N/A')
    plan_markdown_content.append(f"## Original User Query:\n{original_query_for_plan_file}\n")
    plan_markdown_content.append(f"## Plan Summary (from Planner):\n{session_data_entry.get('current_plan_human_summary', 'N/A')}\n")
    plan_markdown_content.append("## Steps:\n")
    for i, step_data_dict in enumerate(confirmed_plan_steps_dicts):
        # Ensure step_data_dict is actually a dict before accessing keys
        desc = step_data_dict.get('description', 'N/A') if isinstance(step_data_dict, dict) else 'N/A (Invalid Step Format)'
        tool_sugg = step_data_dict.get('tool_to_use', 'None') if isinstance(step_data_dict, dict) else 'N/A'
        input_instr = step_data_dict.get('tool_input_instructions', 'None') if isinstance(step_data_dict, dict) else 'N/A'
        expected_out = step_data_dict.get('expected_outcome', 'N/A') if isinstance(step_data_dict, dict) else 'N/A'

        plan_markdown_content.append(f"- [ ] {i+1}. **{desc}**")
        plan_markdown_content.append(f"    - Tool Suggestion (Planner): `{tool_sugg}`")
        plan_markdown_content.append(f"    - Input Instructions (Planner): `{input_instr}`")
        plan_markdown_content.append(f"    - Expected Outcome (Planner): `{expected_out}`\n")

    task_workspace_path = get_task_workspace_path(active_task_id)
    try:
        plan_file_path = task_workspace_path / plan_filename
        async with aiofiles.open(plan_file_path, 'w', encoding='utf-8') as f:
            await f.write("\n".join(plan_markdown_content))
        logger.info(f"[{session_id}] Saved confirmed plan to {plan_file_path}")
        await add_monitor_log_func(f"Confirmed plan saved to artifact: {plan_filename}", "system_info")
        await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})
    except Exception as e:
        logger.error(f"[{session_id}] Failed to save plan to file '{plan_filename}': {e}", exc_info=True)
        await add_monitor_log_func(f"Error saving plan to file '{plan_filename}': {e}", "error_system")

    # --- Plan Execution Loop ---
    plan_failed_definitively = False
    preliminary_final_answer_from_last_step = "Plan execution completed." # Default if all steps pass but no specific output from last
    step_execution_details_list = [] # For overall evaluation summary

    original_user_query = session_data_entry.get("original_user_query", "No original query context available.")

    for i, step_dict_from_plan in enumerate(confirmed_plan_steps_dicts):
        session_data_entry["current_plan_step_index"] = i # Update current step index
        current_step_number = i + 1 # 1-indexed for user display
        current_step_detail_log = { # For overall summary
            "step_number": current_step_number, "description": "N/A",
            "controller_tool_initial": "N/A", "controller_input_initial": "N/A",
            "controller_reasoning_initial": "N/A", "controller_confidence_initial": 0.0,
            "attempts": [], "final_status_char": " " # Default to pending
        }
        current_plan_step_obj: Optional[PlanStep] = None

        try:
            current_plan_step_obj = PlanStep(**step_dict_from_plan)
            current_step_detail_log["description"] = current_plan_step_obj.description
        except Exception as pydantic_err: # Catch Pydantic validation error
            logger.error(f"[{session_id}] Failed to parse step dictionary into PlanStep object: {pydantic_err}. Step data: {step_dict_from_plan}", exc_info=True)
            error_msg = f"Error: Corrupted plan step {current_step_number}. Skipping. Details: {pydantic_err}"
            await add_monitor_log_func(error_msg, "error_plan_step")
            current_step_detail_log["attempts"].append({
                "attempt_number": 1, "controller_tool": "N/A", "controller_input": "N/A",
                "controller_reasoning": "Plan step parsing error", "controller_confidence": 0.0,
                "executor_input": "N/A", "executor_output": "N/A", "error": error_msg,
                "step_eval_achieved": False, "step_eval_assessment": "Plan step parsing error",
                "status_char_for_attempt": "!"
            })
            current_step_detail_log["final_status_char"] = "!"
            step_execution_details_list.append(current_step_detail_log)
            plan_failed_definitively = True; break # Stop plan execution

        if not current_plan_step_obj: # Should be caught by above, but as a safeguard
             logger.critical(f"[{session_id}] CRITICAL: current_plan_step_obj is None after successful parsing for step {current_step_number}. This indicates a logic error.")
             plan_failed_definitively = True; break


        step_description = current_plan_step_obj.description
        step_tools: List[BaseTool] = get_dynamic_tools(active_task_id) # Get tools for current task context

        retry_count_for_current_step = 0
        step_succeeded_after_attempts = False
        last_step_correction_suggestion: Optional[StepCorrectionOutcome] = None

        while retry_count_for_current_step <= MAX_STEP_RETRIES:
            attempt_number = retry_count_for_current_step + 1
            attempt_log_detail = { # For this specific attempt
                "attempt_number": attempt_number, "controller_tool": "N/A", "controller_input": "N/A",
                "controller_reasoning": "N/A", "controller_confidence": 0.0,
                "executor_input": "N/A", "executor_output": "N/A", "error": None,
                "step_eval_achieved": False, "step_eval_assessment": "Not evaluated yet",
                "status_char_for_attempt": " " # Default to pending for this attempt
            }

            # 1. Controller: Validate step and prepare tool input
            plan_step_for_controller_call = current_plan_step_obj.copy(deep=True) # Use a copy for potential modification
            if retry_count_for_current_step > 0 and last_step_correction_suggestion:
                await send_ws_message_func("agent_thinking_update", {"status": f"Controller re-validating Step {current_step_number} (Retry {retry_count_for_current_step})..."})
                await add_monitor_log_func(f"Controller: Re-validating Step {current_step_number} (Retry {retry_count_for_current_step}) based on Step Evaluator feedback.", "system_controller_retry")
                # Apply suggestions from Step Evaluator
                plan_step_for_controller_call.tool_to_use = last_step_correction_suggestion.suggested_new_tool_for_retry
                plan_step_for_controller_call.tool_input_instructions = last_step_correction_suggestion.suggested_new_input_instructions_for_retry
                # TODO: Consider using suggested_revised_step_description if implemented
            else: # First attempt for this step
                await send_ws_message_func("agent_thinking_update", {"status": f"Controller validating Step {current_step_number}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."})
                await add_monitor_log_func(f"Controller: Validating Plan Step {current_step_number}: {step_description} (Planner hint: {current_plan_step_obj.tool_to_use or 'None'})", "system_controller_start")

            # Determine LLM for Controller
            controller_llm_id_override = session_data_entry.get("session_controller_llm_id")
            controller_provider = settings.controller_provider
            controller_model_name = settings.controller_model_name
            if controller_llm_id_override:
                try: controller_provider, controller_model_name = controller_llm_id_override.split("::", 1); logger.info(f"[{session_id}] Using session override for Controller: {controller_llm_id_override}")
                except ValueError: logger.warning(f"[{session_id}] Invalid session LLM ID format for Controller '{controller_llm_id_override}'. Using system default.")
            # LLM instance for controller is fetched inside validate_and_prepare_step_action

            validated_tool_name, formulated_tool_input, controller_message, controller_confidence = await validate_and_prepare_step_action(
                original_user_query=original_user_query,
                plan_step=plan_step_for_controller_call, # Pass the (potentially modified) copy
                available_tools=step_tools
                # LLM is fetched internally by validate_and_prepare_step_action
            )

            attempt_log_detail.update({
                "controller_tool": validated_tool_name, "controller_input": formulated_tool_input,
                "controller_reasoning": controller_message, "controller_confidence": controller_confidence
            })
            if retry_count_for_current_step == 0: # Log initial controller output only once for the step
                current_step_detail_log.update({
                    "controller_tool_initial": validated_tool_name, "controller_input_initial": formulated_tool_input,
                    "controller_reasoning_initial": controller_message, "controller_confidence_initial": controller_confidence
                })

            await add_monitor_log_func(f"Controller Output (Step {current_step_number}, Attempt {attempt_number}): Tool='{validated_tool_name}', Input='{str(formulated_tool_input)[:100]}...', Confidence={controller_confidence:.2f}. Reasoning: {controller_message}", "system_controller_output")

            if controller_confidence < 0.7 and validated_tool_name: # If a tool is chosen with low confidence
                await add_monitor_log_func(f"Warning: Controller confidence for step {current_step_number} (Attempt {attempt_number}) is low ({controller_confidence:.2f}). Proceeding.", "warning_controller")

            if validated_tool_name is None and "Error in Controller" in controller_message: # Controller itself errored
                error_msg = f"Error: Controller failed for step {current_step_number} (Attempt {attempt_number}). Reason: {controller_message}."
                await add_monitor_log_func(error_msg, "error_controller")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"
                plan_failed_definitively = True; break # Break from retry loop, will also break outer loop

            # 2. Executor: Run the step
            agent_input_for_executor: str
            if validated_tool_name: # If controller decided a tool is needed
                agent_input_for_executor = (
                    f"Your current sub-task is: \"{step_description}\".\n"
                    f"The precise expected output for THIS sub-task is: \"{current_plan_step_obj.expected_outcome}\".\n" # Use original expected outcome
                    f"The Controller has determined you MUST use the tool '{validated_tool_name}' "
                    f"with the following exact input: '{formulated_tool_input}'.\n"
                    f"Execute this and report the result, ensuring your final answer for this sub-task directly fulfills the stated 'precise expected output'."
                )
            else: # No tool, direct LLM generation/reasoning for this step
                agent_input_for_executor = (
                    f"Your current sub-task is: \"{step_description}\".\n"
                    f"The precise expected output for THIS sub-task is: \"{current_plan_step_obj.expected_outcome}\".\n" # Use original expected outcome
                    f"The Controller has determined no specific tool is required for this step. "
                    f"Provide a direct answer or perform analysis based on conversation history and this sub-task description, ensuring your final answer for this sub-task directly fulfills the stated 'precise expected output'."
                )
            attempt_log_detail["executor_input"] = agent_input_for_executor # Log the input to executor

            await send_ws_message_func("agent_thinking_update", {"status": f"Executor running Step {current_step_number} (Attempt {attempt_number})..."})
            await add_monitor_log_func(f"Executing Plan Step {current_step_number} (Attempt {attempt_number}): {step_description}", "system_plan_step_start")

            # Determine LLM for Executor (can be session-specific or system default for Executor)
            executor_provider = session_data_entry.get("selected_llm_provider", settings.executor_default_provider)
            executor_model_name = session_data_entry.get("selected_llm_model_name", settings.executor_default_model_name)
            step_executor_llm: Optional[BaseChatModel] = None
            try:
                llm_instance_exec = get_llm(settings, provider=executor_provider, model_name=executor_model_name, requested_for_role="Executor_PlanStep")
                step_executor_llm = llm_instance_exec # type: ignore
            except Exception as llm_err:
                error_msg = f"Error: Failed to init LLM for Executor (Step {current_step_number}, Attempt {attempt_number}). Details: {llm_err}"
                await add_monitor_log_func(error_msg, "error_system")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"; plan_failed_definitively = True; break

            step_memory = session_data_entry["memory"]
            step_callback_handler = session_data_entry["callback_handler"]
            step_executor_output_str = "Executor did not produce output." # Default

            try:
                step_agent_executor = create_agent_executor(
                    llm=step_executor_llm, tools=step_tools, memory=step_memory, max_iterations=settings.agent_max_iterations
                )
                agent_step_task = asyncio.create_task(
                    step_agent_executor.ainvoke({"input": agent_input_for_executor}, config=RunnableConfig(callbacks=[step_callback_handler]))
                )
                connected_clients_entry["agent_task"] = agent_step_task
                step_result_from_executor = await agent_step_task
                step_executor_output_str = step_result_from_executor.get("output", "Step completed, no specific output from ReAct agent.")
                attempt_log_detail["executor_output"] = step_executor_output_str # Log actual output
                await add_monitor_log_func(f"Plan Step {current_step_number} (Attempt {attempt_number}, Executor) completed. Output: {str(step_executor_output_str)[:200]}...", "system_plan_step_end")

            except AgentCancelledException as ace:
                error_msg = f"Plan execution cancelled by user during step {current_step_number} (Attempt {attempt_number})."
                logger.warning(f"[{session_id}] {error_msg}")
                await send_ws_message_func("status_message", "Plan execution cancelled.")
                await add_monitor_log_func(error_msg, "system_cancel")
                attempt_log_detail["error"] = error_msg; attempt_log_detail["status_char_for_attempt"] = "-"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "-" # Mark step as cancelled in plan file
                plan_failed_definitively = True; break # Break from retry loop and outer loop
            except Exception as step_exec_e:
                error_msg = f"Error executing plan step {current_step_number} (Attempt {attempt_number}): {step_exec_e}"
                logger.error(f"[{session_id}] {error_msg}", exc_info=True)
                await add_monitor_log_func(error_msg, "error_plan_step")
                step_executor_output_str = error_msg # Use error as output for evaluator
                attempt_log_detail["error"] = error_msg; attempt_log_detail["executor_output"] = error_msg # Log error
            finally:
                connected_clients_entry["agent_task"] = None # Clear the task

            # 3. Step Evaluator: Assess outcome and suggest corrections if needed
            await add_monitor_log_func(f"Step Evaluator: Assessing outcome of Step {current_step_number} (Attempt {attempt_number})...", "system_step_eval_start")
            # Determine LLM for Step Evaluator
            evaluator_llm_id_override = session_data_entry.get("session_evaluator_llm_id")
            evaluator_provider = settings.evaluator_provider
            evaluator_model_name = settings.evaluator_model_name
            if evaluator_llm_id_override:
                try: evaluator_provider, evaluator_model_name = evaluator_llm_id_override.split("::", 1); logger.info(f"[{session_id}] Using session override for Step Evaluator: {evaluator_llm_id_override}")
                except ValueError: logger.warning(f"[{session_id}] Invalid session LLM ID format for Step Evaluator '{evaluator_llm_id_override}'. Using system default.")
            # LLM instance for step evaluator is fetched inside evaluate_step_outcome_and_suggest_correction

            last_step_correction_suggestion = await evaluate_step_outcome_and_suggest_correction(
                original_user_query=original_user_query,
                plan_step_being_evaluated=current_plan_step_obj, # Original step definition
                controller_tool_used=validated_tool_name, # What controller decided for this attempt
                controller_tool_input=formulated_tool_input, # What controller decided for this attempt
                step_executor_output=step_executor_output_str, # Actual output from executor
                available_tools=step_tools
                # LLM is fetched internally
            )

            if last_step_correction_suggestion:
                attempt_log_detail["step_eval_achieved"] = last_step_correction_suggestion.step_achieved_goal
                attempt_log_detail["step_eval_assessment"] = last_step_correction_suggestion.assessment_of_step
                await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Goal Achieved: {last_step_correction_suggestion.step_achieved_goal}. Assessment: {last_step_correction_suggestion.assessment_of_step}", "system_step_eval_output")

                if last_step_correction_suggestion.step_achieved_goal:
                    attempt_log_detail["status_char_for_attempt"] = "x" # Mark this attempt as success
                    step_succeeded_after_attempts = True
                    current_step_detail_log["final_status_char"] = "x" # Mark overall step as success
                    current_step_detail_log["attempts"].append(attempt_log_detail)
                    break # Exit retry loop for this step
                else: # Step failed this attempt
                    if last_step_correction_suggestion.is_recoverable_via_retry and retry_count_for_current_step < MAX_STEP_RETRIES:
                        await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Suggests RETRY. Tool: '{last_step_correction_suggestion.suggested_new_tool_for_retry}', Input Hint: '{last_step_correction_suggestion.suggested_new_input_instructions_for_retry}', Confidence: {last_step_correction_suggestion.confidence_in_correction}", "system_step_eval_suggest_retry")
                        attempt_log_detail["status_char_for_attempt"] = "!" # Mark this attempt as failed
                        current_step_detail_log["attempts"].append(attempt_log_detail)
                        retry_count_for_current_step += 1 # Increment and continue retry loop
                    else: # Not recoverable or retries exhausted
                        await add_monitor_log_func(f"Step Evaluator (Step {current_step_number}, Att. {attempt_number}): Step failed and is not recoverable or retries exhausted.", "system_step_eval_unrecoverable")
                        attempt_log_detail["status_char_for_attempt"] = "!" # Mark this attempt as failed
                        current_step_detail_log["attempts"].append(attempt_log_detail)
                        current_step_detail_log["final_status_char"] = "!" # Mark overall step as failed
                        plan_failed_definitively = True; break # Break from retry loop and outer loop
            else: # Step Evaluator itself failed
                await add_monitor_log_func(f"Error: Step Evaluator failed for Step {current_step_number} (Attempt {attempt_number}). Assuming step failed.", "error_step_eval")
                attempt_log_detail["error"] = attempt_log_detail.get("error") or "Step Evaluator failed to produce an outcome."
                attempt_log_detail["step_eval_assessment"] = "Step Evaluator failed."
                attempt_log_detail["status_char_for_attempt"] = "!"
                current_step_detail_log["attempts"].append(attempt_log_detail)
                current_step_detail_log["final_status_char"] = "!"
                plan_failed_definitively = True; break # Break from retry loop and outer loop

            # Check for cancellation request after each attempt
            if session_data_entry.get('cancellation_requested', False):
                logger.warning(f"[{session_id}] Cancellation detected after step {current_step_number} (Attempt {attempt_number}). Stopping plan.")
                await send_ws_message_func("status_message", "Plan execution cancelled.")
                if not attempt_log_detail.get("error"): # If no other error, mark as cancelled
                    attempt_log_detail["error"] = "Cancelled by user after step attempt."
                attempt_log_detail["status_char_for_attempt"] = "-" # Mark this attempt as cancelled
                current_step_detail_log["attempts"].append(attempt_log_detail) # Add the cancelled attempt
                current_step_detail_log["final_status_char"] = "-" # Mark overall step as cancelled
                plan_failed_definitively = True; break # Break from retry loop and outer loop
        
        # This append should be outside the while loop, after all attempts for the current step are done
        step_execution_details_list.append(current_step_detail_log)

        # Update plan file with the final status of this step
        active_plan_filename_local = session_data_entry.get('active_plan_filename')
        if active_plan_filename_local and active_task_id: # Ensure these are valid
            await _update_plan_file_step_status(
                task_workspace_path, active_plan_filename_local,
                current_step_number, current_step_detail_log.get("final_status_char", "?") # Use final status
            )
            await send_ws_message_func("trigger_artifact_refresh", {"taskId": active_task_id})

        if plan_failed_definitively:
            break # Break from the main loop over plan steps

        if step_succeeded_after_attempts:
            # The successful output is already in memory via ReAct agent's callback handler
            # Store the output of the last successful attempt for potential use by Overall Evaluator
            last_successful_attempt = next((att for att in reversed(current_step_detail_log["attempts"]) if att["status_char_for_attempt"] == "x"), None)
            if last_successful_attempt:
                preliminary_final_answer_from_last_step = last_successful_attempt.get("executor_output", preliminary_final_answer_from_last_step)


    # --- Plan Execution Finished (or stopped) ---
    session_data_entry["plan_execution_active"] = False
    session_data_entry["current_plan_step_index"] = -1 # Reset

    # Prepare summary for Overall Plan Evaluator
    summary_lines_for_overall_eval = []
    for step_log in step_execution_details_list:
        summary_lines_for_overall_eval.append(f"Step {step_log['step_number']}: {step_log['description']}")
        summary_lines_for_overall_eval.append(f"  Initial Controller: Tool='{step_log['controller_tool_initial']}', Input='{str(step_log['controller_input_initial'])[:100]}', Confidence={step_log['controller_confidence_initial']:.2f}")
        for i_att, attempt in enumerate(step_log["attempts"]):
            summary_lines_for_overall_eval.append(f"  Attempt {i_att+1}:")
            if attempt.get("controller_tool"): # Only show if a tool was chosen for this attempt
                 summary_lines_for_overall_eval.append(f"    Controller: Tool='{attempt['controller_tool']}', Input='{str(attempt['controller_input'])[:100]}'")
            summary_lines_for_overall_eval.append(f"    Executor Output: {str(attempt['executor_output'])[:150]}...")
            if attempt.get("error"):
                summary_lines_for_overall_eval.append(f"    Error for Attempt: {str(attempt['error'])[:150]}...")
            summary_lines_for_overall_eval.append(f"    Step Evaluator Assessment: Achieved={attempt.get('step_eval_achieved', 'N/A')}, Detail: {attempt.get('step_eval_assessment', 'N/A')[:100]}...")
            summary_lines_for_overall_eval.append(f"    Attempt Status: [{attempt.get('status_char_for_attempt', '?')}]")
        summary_lines_for_overall_eval.append(f"  Final Step Status: [{step_log.get('final_status_char', '?')}]")
        summary_lines_for_overall_eval.append("-" * 20)

    executed_plan_summary_str = "\n".join(summary_lines_for_overall_eval)
    if not step_execution_details_list: # Should not happen if plan had steps
        executed_plan_summary_str = "No steps were attempted or recorded."


    # Determine final message based on plan execution outcome
    if plan_failed_definitively:
        # Use the last error message or a generic failure message
        last_error_message = "Plan execution stopped due to error or cancellation."
        # Find the last error from attempts for a more specific message
        for step_log in reversed(step_execution_details_list):
            for attempt in reversed(step_log.get("attempts", [])):
                if attempt.get("error"):
                    last_error_message = f"Plan stopped. Last error: {str(attempt['error'])[:200]}"
                    break
            if last_error_message != "Plan execution stopped due to error or cancellation.": break
        final_message_to_user = last_error_message
        await send_ws_message_func("agent_thinking_update", {"status": "Plan stopped."})
    else:
        # Use the output of the last successfully executed step as preliminary answer
        final_message_to_user = preliminary_final_answer_from_last_step
        await send_ws_message_func("agent_thinking_update", {"status": "Plan executed. Evaluating overall outcome..."})
        logger.info(f"[{session_id}] Successfully attempted all plan steps (or those before a definitive failure). Now evaluating overall plan.")

    # Overall Plan Evaluation
    await add_monitor_log_func("Invoking Overall Plan Evaluator to assess final outcome.", "system_evaluator_start")
    # Determine LLM for Overall Evaluator
    overall_eval_llm_id_override = session_data_entry.get("session_evaluator_llm_id")
    overall_eval_provider = settings.evaluator_provider
    overall_eval_model_name = settings.evaluator_model_name
    if overall_eval_llm_id_override:
        try: overall_eval_provider, overall_eval_model_name = overall_eval_llm_id_override.split("::", 1); logger.info(f"[{session_id}] Using session override for Overall Evaluator: {overall_eval_llm_id_override}")
        except ValueError: logger.warning(f"[{session_id}] Invalid session LLM ID format for Overall Evaluator '{overall_eval_llm_id_override}'. Using system default.")
    # LLM instance for overall evaluator is fetched inside evaluate_plan_outcome

    overall_evaluation_result = await evaluate_plan_outcome(
        original_user_query=original_user_query,
        executed_plan_summary=executed_plan_summary_str,
        final_agent_answer=final_message_to_user # Pass the last step's output or error message
        # LLM is fetched internally
    )

    if overall_evaluation_result:
        final_message_to_user = overall_evaluation_result.assessment # Override with evaluator's assessment
        log_msg = (
            f"Overall Plan Evaluator Result: Success={overall_evaluation_result.overall_success}, "
            f"Confidence={overall_evaluation_result.confidence_score:.2f}. "
            f"Assessment: {overall_evaluation_result.assessment}"
        )
        await add_monitor_log_func(log_msg, "system_evaluator_output")
        if not overall_evaluation_result.overall_success and overall_evaluation_result.suggestions_for_replan:
            await add_monitor_log_func(f"Overall Plan Evaluator Suggestions for future re-plan: {overall_evaluation_result.suggestions_for_replan}", "system_evaluator_suggestions")
    else: # Overall Evaluator failed
        await add_monitor_log_func("Error: Overall Plan Evaluator failed to produce a result. Using last available answer/error message.", "error_evaluator")
        # final_message_to_user remains as the output from the last step or error

    # Send the final message to UI and save it
    await send_ws_message_func("agent_message", final_message_to_user)
    if active_task_id: # Ensure active_task_id is valid
        # Use "agent_message" to ensure it's reloaded into chat correctly
        await db_add_message_func(active_task_id, session_id, "agent_message", final_message_to_user)
        logger.info(f"[{session_id}] Saved final agent message (Overall Evaluator's assessment or last step output) to DB for task {active_task_id}.")
    
    await add_monitor_log_func(f"Final Overall Outcome Sent to User: {final_message_to_user}", "system_plan_end")
    await send_ws_message_func("status_message", "Processing complete.")
    await send_ws_message_func("agent_thinking_update", {"status": "Idle."})


async def process_new_task(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, get_artifacts_func: GetArtifactsFunc
) -> None:
    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context.")

    session_data_entry['cancellation_requested'] = False
    session_data_entry['current_plan_structured'] = None
    session_data_entry['current_plan_human_summary'] = None
    session_data_entry['current_plan_step_index'] = -1
    session_data_entry['plan_execution_active'] = False
    session_data_entry['original_user_query'] = None
    session_data_entry['active_plan_filename'] = None

    existing_agent_task = connected_clients_entry.get("agent_task")
    if existing_agent_task and not existing_agent_task.done():
        logger.warning(f"[{session_id}] Cancelling active agent/plan task due to new task.")
        existing_agent_task.cancel()
        await send_ws_message_func("status_message", "Operation cancelled for new task.")
        await add_monitor_log_func("Agent/Plan operation cancelled due to new task creation.", "system_cancel")
        connected_clients_entry["agent_task"] = None

    session_data_entry["current_task_id"] = None
    if "callback_handler" in session_data_entry:
        session_data_entry["callback_handler"].set_task_id(None)
    if "memory" in session_data_entry:
        session_data_entry["memory"].clear()

    await add_monitor_log_func("Cleared context for new task.", "system_new_task")
    await send_ws_message_func("update_artifacts", [])


async def process_delete_task(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_delete_task_func: DBDeleteTaskFunc,
    get_artifacts_func: GetArtifactsFunc
) -> None:
    task_id_to_delete = data.get("taskId")
    if not task_id_to_delete:
        logger.warning(f"[{session_id}] 'delete_task' message missing taskId.")
        await add_monitor_log_func("Error: 'delete_task' received without taskId.", "error_system")
        return

    logger.warning(f"[{session_id}] Received request to delete task: {task_id_to_delete}")
    await add_monitor_log_func(f"Received request to delete task: {task_id_to_delete}", "system_delete_request")

    deleted_from_db = await db_delete_task_func(task_id_to_delete)

    workspace_deletion_successful = False
    if deleted_from_db:
        await add_monitor_log_func(f"Task {task_id_to_delete} DB entries deleted successfully.", "system_delete_success")
        task_workspace_to_delete: Optional[Path] = None
        try:
            task_workspace_to_delete = get_task_workspace_path(task_id_to_delete, create_if_not_exists=False) # Don't create if deleting
            if task_workspace_to_delete.exists():
                # Security check: ensure the path is within the base workspace root
                if task_workspace_to_delete.resolve().is_relative_to(BASE_WORKSPACE_ROOT.resolve()) and \
                   BASE_WORKSPACE_ROOT.resolve() != task_workspace_to_delete.resolve(): # Prevent deleting base itself
                    logger.info(f"[{session_id}] Attempting to delete workspace directory: {task_workspace_to_delete}")
                    await asyncio.to_thread(shutil.rmtree, task_workspace_to_delete)
                    logger.info(f"[{session_id}] Successfully deleted workspace directory: {task_workspace_to_delete}")
                    await add_monitor_log_func(f"Workspace directory deleted: {task_workspace_to_delete.name}", "system_delete_success")
                    workspace_deletion_successful = True
                else:
                    logger.warning(f"[{session_id}] Workspace directory {task_workspace_to_delete} is not safely within the base workspace or is the base itself. Deletion skipped for security.")
                    await add_monitor_log_func(f"Workspace directory {task_workspace_to_delete.name} deletion skipped (security check).", "warning_system")
            else:
                logger.info(f"[{session_id}] Workspace directory not found for task {task_id_to_delete}, no deletion needed: {task_workspace_to_delete}")
                await add_monitor_log_func(f"Workspace for task {task_id_to_delete} not found. No directory to delete.", "system_info")
                workspace_deletion_successful = True # Considered successful as there's nothing to delete
        except Exception as ws_del_e:
            logger.error(f"[{session_id}] Error during workspace directory deletion for task {task_id_to_delete} (path: {task_workspace_to_delete}): {ws_del_e}", exc_info=True)
            await add_monitor_log_func(f"Error deleting workspace directory for task {task_id_to_delete}: {str(ws_del_e)}", "error_delete")
            await send_ws_message_func("status_message", f"Task DB deleted, but workspace folder for {task_id_to_delete[:8]} failed to delete.")

        if session_data_entry.get("current_task_id") == task_id_to_delete:
            session_data_entry['cancellation_requested'] = False
            session_data_entry['current_plan_structured'] = None
            session_data_entry['current_plan_human_summary'] = None
            session_data_entry['current_plan_step_index'] = -1
            session_data_entry['plan_execution_active'] = False
            session_data_entry['original_user_query'] = None
            session_data_entry['active_plan_filename'] = None
            existing_agent_task = connected_clients_entry.get("agent_task")
            if existing_agent_task and not existing_agent_task.done():
                existing_agent_task.cancel()
            connected_clients_entry["agent_task"] = None
            session_data_entry["current_task_id"] = None
            if "callback_handler" in session_data_entry:
                session_data_entry["callback_handler"].set_task_id(None)
            if "memory" in session_data_entry:
                session_data_entry["memory"].clear()
            await add_monitor_log_func("Cleared context as active task was deleted.", "system_context_clear")
            await send_ws_message_func("update_artifacts", [])
    else:
        await send_ws_message_func("status_message", f"Failed to delete task {task_id_to_delete[:8]} from database.")
        await add_monitor_log_func(f"Failed to delete task {task_id_to_delete} from DB.", "error_delete")


async def process_rename_task(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_rename_task_func: DBRenameTaskFunc
) -> None:
    task_id_to_rename = data.get("taskId")
    new_name = data.get("newName")

    if not task_id_to_rename or not new_name:
        logger.warning(f"[{session_id}] Received invalid rename_task message: {data}")
        await add_monitor_log_func(f"Error: Received invalid rename request (missing taskId or newName).", "error_system")
        return

    logger.info(f"[{session_id}] Received request to rename task {task_id_to_rename} to '{new_name}'.")
    await add_monitor_log_func(f"Received rename request for task {task_id_to_rename} to '{new_name}'.", "system_rename_request")

    renamed_in_db = await db_rename_task_func(task_id_to_rename, new_name)

    if renamed_in_db:
        logger.info(f"[{session_id}] Successfully renamed task {task_id_to_rename} in database.")
        await add_monitor_log_func(f"Task {task_id_to_rename} renamed to '{new_name}' in DB.", "system_rename_success")
    else:
        logger.error(f"[{session_id}] Failed to rename task {task_id_to_rename} in database.")
        await add_monitor_log_func(f"Failed to rename task {task_id_to_rename} in DB.", "error_db")

async def process_set_llm(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    llm_id = data.get("llm_id")
    if llm_id and isinstance(llm_id, str):
        try:
            provider, model_name_from_id = llm_id.split("::", 1)
            is_valid = False
            if provider == 'gemini' and model_name_from_id in settings.gemini_available_models:
                is_valid = True
            elif provider == 'ollama' and model_name_from_id in settings.ollama_available_models:
                is_valid = True

            if is_valid:
                session_data_entry["selected_llm_provider"] = provider
                session_data_entry["selected_llm_model_name"] = model_name_from_id
                logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) set to: {provider}::{model_name_from_id}")
                await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) set to {provider}::{model_name_from_id}", "system_llm_set")
            else: # User selected an empty value (e.g. "Use System Default (Executor)")
                session_data_entry["selected_llm_provider"] = settings.executor_default_provider
                session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
                logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) reset to system default: {settings.executor_default_provider}::{settings.executor_default_model_name}")
                await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) reset to system default.", "system_llm_set")

        except ValueError: # Handles if llm_id is not in "provider::model" format
            logger.warning(f"[{session_id}] Invalid LLM ID format in set_llm: {llm_id}. Resetting to executor default.")
            session_data_entry["selected_llm_provider"] = settings.executor_default_provider
            session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
            await add_monitor_log_func(f"Received invalid session LLM ID format: {llm_id}. Reset to default.", "error_llm_set")
    elif llm_id == "": # Explicitly chosen "Use System Default (Executor)"
        session_data_entry["selected_llm_provider"] = settings.executor_default_provider
        session_data_entry["selected_llm_model_name"] = settings.executor_default_model_name
        logger.info(f"[{session_id}] Session LLM (for Executor/DirectQA) explicitly set to system default: {settings.executor_default_provider}::{settings.executor_default_model_name}")
        await add_monitor_log_func(f"Session LLM (for Executor/DirectQA) set to system default.", "system_llm_set")
    else:
        logger.warning(f"[{session_id}] Received invalid 'set_llm' message content: {data}")


async def process_get_available_models(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    logger.info(f"[{session_id}] Received request for available models.")
    await send_ws_message_func("available_models", {
        "gemini": settings.gemini_available_models,
        "ollama": settings.ollama_available_models,
        "default_executor_llm_id": f"{settings.executor_default_provider}::{settings.executor_default_model_name}",
        "role_llm_defaults": {
            "intent_classifier": f"{settings.intent_classifier_provider}::{settings.intent_classifier_model_name}",
            "planner": f"{settings.planner_provider}::{settings.planner_model_name}",
            "controller": f"{settings.controller_provider}::{settings.controller_model_name}",
            "evaluator": f"{settings.evaluator_provider}::{settings.evaluator_model_name}",
        }
    })

async def process_cancel_agent(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    logger.warning(f"[{session_id}] Received request to cancel current operation.")
    session_data_entry['cancellation_requested'] = True
    logger.info(f"[{session_id}] Cancellation requested flag set to True.")

    agent_task_to_cancel = connected_clients_entry.get("agent_task")
    if agent_task_to_cancel and not agent_task_to_cancel.done():
        agent_task_to_cancel.cancel()
        logger.info(f"[{session_id}] asyncio.Task.cancel() called for active task.")
    else:
        logger.info(f"[{session_id}] No active asyncio task found to cancel, or task already done.")

async def process_get_artifacts_for_task(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, get_artifacts_func: GetArtifactsFunc
) -> None:
    task_id_to_refresh = data.get("taskId")
    if not task_id_to_refresh:
        logger.warning(f"[{session_id}] Received get_artifacts_for_task without taskId.")
        return

    logger.info(f"[{session_id}] Received request to refresh artifacts for task: {task_id_to_refresh}")
    active_task_id = session_data_entry.get("current_task_id")
    if task_id_to_refresh == active_task_id:
        artifacts = await get_artifacts_func(task_id_to_refresh)
        await send_ws_message_func("update_artifacts", artifacts)
        logger.info(f"[{session_id}] Sent updated artifact list for task {task_id_to_refresh}.")
    else:
        logger.warning(f"[{session_id}] Received artifact refresh request for non-active task ({task_id_to_refresh} vs {active_task_id}). Ignoring.")

async def process_run_command(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, db_add_message_func: DBAddMessageFunc,
    execute_shell_command_func: ExecuteShellCommandFunc
) -> None:
    command_to_run = data.get("command")
    if command_to_run and isinstance(command_to_run, str):
        active_task_id_for_cmd = session_data_entry.get("current_task_id")
        await add_monitor_log_func(f"Received direct 'run_command'. Executing: {command_to_run} (Task Context: {active_task_id_for_cmd})", "system_direct_cmd")
        await execute_shell_command_func(
            command_to_run,
            session_id,
            send_ws_message_func,
            db_add_message_func,
            active_task_id_for_cmd
        )
    else:
        logger.warning(f"[{session_id}] Received 'run_command' with invalid/missing command content.")
        await add_monitor_log_func("Error: 'run_command' received with no command specified.", "error_direct_cmd")

async def process_action_command(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    action = data.get("command")
    if action and isinstance(action, str):
        logger.info(f"[{session_id}] Received action command: {action} (Not implemented).")
        await add_monitor_log_func(f"Received action command: {action} (Handler not implemented).", "system_action_cmd")
    else:
        logger.warning(f"[{session_id}] Received 'action_command' with invalid/missing command content.")

async def process_set_session_role_llm(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    role = data.get("role")
    llm_id_override = data.get("llm_id")

    if not role or role not in ["intent_classifier", "planner", "controller", "evaluator"]:
        logger.warning(f"[{session_id}] Invalid or missing 'role' in set_session_role_llm: {role}")
        await add_monitor_log_func(f"Error: Invalid role specified for LLM override: {role}", "error_system")
        return

    session_override_key = f"session_{role}_llm_id" # e.g., session_planner_llm_id

    if llm_id_override == "": # User selected "Use System Default"
        session_data_entry[session_override_key] = None # Clear the override
        logger.info(f"[{session_id}] Cleared session LLM override for role '{role}'. Will use system default.")
        await add_monitor_log_func(f"Session LLM for role '{role}' reset to system default.", "system_llm_set")
    elif llm_id_override and isinstance(llm_id_override, str):
        try:
            provider, model_name = llm_id_override.split("::", 1)
            is_valid = False
            # Validate against available models from settings
            if provider == 'gemini' and model_name in settings.gemini_available_models:
                is_valid = True
            elif provider == 'ollama' and model_name in settings.ollama_available_models:
                is_valid = True

            if is_valid:
                session_data_entry[session_override_key] = llm_id_override
                logger.info(f"[{session_id}] Session LLM override for role '{role}' set to: {llm_id_override}")
                await add_monitor_log_func(f"Session LLM for role '{role}' overridden to {llm_id_override}.", "system_llm_set")
            else:
                logger.warning(f"[{session_id}] Attempt to set invalid/unavailable LLM ID '{llm_id_override}' for role '{role}'. Override not applied.")
                await add_monitor_log_func(f"Attempt to set invalid LLM '{llm_id_override}' for role '{role}' ignored.", "error_llm_set")
        except ValueError: # llm_id was not in "provider::model" format
            logger.warning(f"[{session_id}] Invalid LLM ID format for role '{role}': {llm_id_override}")
            await add_monitor_log_func(f"Invalid LLM ID format for role '{role}': {llm_id_override}", "error_llm_set")
    else:
        logger.warning(f"[{session_id}] Invalid 'llm_id' in set_session_role_llm for role '{role}': {llm_id_override}")

