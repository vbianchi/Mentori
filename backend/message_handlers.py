import logging
import json
import datetime
from typing import Dict, Any, Callable, Coroutine, Optional, List
import asyncio
import shutil # For deleting workspace directories

# LangChain Imports
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig # For execute_confirmed_plan

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT # Added BASE_WORKSPACE_ROOT
from backend.planner import generate_plan, PlanStep
from backend.controller import validate_and_prepare_step_action
from backend.agent import create_agent_executor # For execute_confirmed_plan
from backend.callbacks import AgentCancelledException # For execute_confirmed_plan

logger = logging.getLogger(__name__)

# --- Type Hints for Passed-in Functions ---
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
DBAddTaskFunc = Callable[[str, str, str], Coroutine[Any, Any, None]]
DBGetMessagesFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, Any]]]]
DBDeleteTaskFunc = Callable[[str], Coroutine[Any, Any, bool]] # For delete_task
DBRenameTaskFunc = Callable[[str, str], Coroutine[Any, Any, bool]] # For rename_task
GetArtifactsFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, str]]]]


async def process_context_switch(
    session_id: str,
    data: Dict[str, Any],
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_add_message_func: DBAddMessageFunc, 
    db_add_task_func: DBAddTaskFunc,
    db_get_messages_func: DBGetMessagesFunc,
    get_artifacts_func: GetArtifactsFunc
) -> None:
    # ... (Content from message_handlers_py_asyncio_fix, unchanged) ...
    task_id_from_frontend = data.get("taskId")
    task_title_from_frontend = data.get("task")

    logger.info(f"[{session_id}] Switching context to Task ID: {task_id_from_frontend}")
    
    session_data_entry['cancellation_requested'] = False
    session_data_entry['current_plan_structured'] = None
    session_data_entry['current_plan_human_summary'] = None
    session_data_entry['current_plan_step_index'] = -1
    session_data_entry['plan_execution_active'] = False
    session_data_entry['original_user_query'] = None 

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
            elif db_msg_type in ["agent_finish", "agent_message", "agent"]:
                ui_msg_type = "agent_message"; send_to_chat = True
                chat_history_for_memory.append(AIMessage(content=db_content_hist))
            elif db_msg_type == "artifact_generated":
                pass 
            elif db_msg_type.startswith(("monitor_", "error_", "system_", "tool_", "agent_thought_", "monitor_user_input", "llm_token_usage")):
                ui_msg_type = "monitor_log"
                log_prefix_hist = f"[{db_timestamp}][{session_id[:8]}]"
                type_indicator_hist = f"[{db_msg_type.replace('monitor_', '').replace('error_', 'ERR_').replace('system_', 'SYS_').replace('agent_thought_action', 'THOUGHT_ACT').replace('agent_thought_final', 'THOUGHT_FIN').replace('monitor_user_input', 'USER_INPUT_LOG').replace('llm_token_usage', 'TOKEN_LOG').upper()}]"
                content_to_send = f"{log_prefix_hist} [History]{type_indicator_hist} {db_content_hist}"
                send_to_chat = False
            else:
                send_to_chat = False
                logger.warning(f"[{session_id}] Unknown history message type '{db_msg_type}' encountered.")
                await send_ws_message_func("monitor_log", f"[{db_timestamp}][{session_id[:8]}] [History][UNKNOWN_TYPE: {db_msg_type}] {db_content_hist}")

            if ui_msg_type:
                if send_to_chat:
                    await send_ws_message_func(ui_msg_type, content_to_send)
                elif ui_msg_type == "monitor_log": 
                    await send_ws_message_func("monitor_log", content_to_send)
                await asyncio.sleep(0.005) 

        await send_ws_message_func("history_end", "History loaded.")
        logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")
        
        MAX_MEMORY_RELOAD = settings.agent_memory_window_k
        if "memory" in session_data_entry:
            try:
                session_data_entry["memory"].chat_memory.messages = chat_history_for_memory[-MAX_MEMORY_RELOAD:]
                logger.info(f"[{session_id}] Repopulated agent memory with last {len(session_data_entry['memory'].chat_memory.messages)} messages.")
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
    session_id: str,
    data: Dict[str, Any], 
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_add_message_func: DBAddMessageFunc 
) -> None:
    # ... (Content from message_handlers_py_asyncio_fix, unchanged) ...
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
    await send_ws_message_func("agent_thinking_update", {"status": "Generating plan..."})

    selected_provider = session_data_entry.get("selected_llm_provider", settings.default_provider)
    selected_model_name = session_data_entry.get("selected_llm_model_name", settings.default_model_name)
    planner_llm: Optional[BaseChatModel] = None
    try:
        llm_instance = get_llm(settings, provider=selected_provider, model_name=selected_model_name)
        if not isinstance(llm_instance, BaseChatModel):
                logger.warning(f"LLM for planner is not BaseChatModel, it's {type(llm_instance)}. This might cause issues if planner expects chat-specific features.")
        planner_llm = llm_instance # type: ignore
    except Exception as llm_init_err:
        logger.error(f"[{session_id}] Failed to initialize LLM for planner: {llm_init_err}", exc_info=True)
        await add_monitor_log_func(f"Error initializing LLM for planner: {llm_init_err}", "error_system")
        await send_ws_message_func("status_message", "Error: Failed to prepare for planning.")
        await send_ws_message_func("agent_message", f"Sorry, could not initialize the planning module.")
        return 
    
    dynamic_tools = get_dynamic_tools(active_task_id) 
    tools_summary_for_planner = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])

    human_plan_summary, structured_plan_steps = await generate_plan(
        user_query=user_input_content,
        llm=planner_llm, # type: ignore
        available_tools_summary=tools_summary_for_planner
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


async def process_execute_confirmed_plan(
    session_id: str,
    data: Dict[str, Any], # Contains confirmed_plan
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
    # Note: db_add_message_func is implicitly available via add_monitor_log_func's closure
    # or could be passed explicitly if add_monitor_log_func doesn't save all desired message types.
    # For now, assuming add_monitor_log_func handles DB saving for its logs.
) -> None:
    """Handles the 'execute_confirmed_plan' message from the client."""
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
    
    plan_failed = False
    final_overall_answer = "Plan execution completed." # Default

    original_user_query = session_data_entry.get("original_user_query", "No original query context available.")
    if not original_user_query:
            await add_monitor_log_func(f"Warning: Original user query not found in session data for controller context.", "warning_system")

    for i, step_dict in enumerate(confirmed_plan_steps_dicts):
        session_data_entry["current_plan_step_index"] = i
        
        try:
            current_plan_step_obj = PlanStep(**step_dict)
        except Exception as pydantic_err:
            logger.error(f"[{session_id}] Failed to parse step dictionary into PlanStep object: {pydantic_err}. Step data: {step_dict}", exc_info=True)
            await add_monitor_log_func(f"Error: Corrupted plan step {i+1}. Skipping.", "error_plan_step")
            plan_failed = True; break
        
        step_description = current_plan_step_obj.description
        step_tool_suggestion_planner = current_plan_step_obj.tool_to_use or "None"
        
        await send_ws_message_func("agent_thinking_update", {
            "status": f"Controller validating Step {i+1}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."
        })
        await add_monitor_log_func(f"Controller: Validating Plan Step {i+1}: {step_description} (Planner hint: {step_tool_suggestion_planner})", "system_controller_start")

        step_llm_provider = session_data_entry.get("selected_llm_provider", settings.default_provider)
        step_llm_model_name = session_data_entry.get("selected_llm_model_name", settings.default_model_name)
        controller_llm: Optional[BaseChatModel] = None
        try:
            llm_instance_ctrl = get_llm(settings, provider=step_llm_provider, model_name=step_llm_model_name)
            if not isinstance(llm_instance_ctrl, BaseChatModel):
                logger.warning(f"LLM for controller is not BaseChatModel, it's {type(llm_instance_ctrl)}.")
            controller_llm = llm_instance_ctrl # type: ignore
        except Exception as llm_err:
            logger.error(f"[{session_id}] Failed to init LLM for Controller (step {i+1}): {llm_err}")
            await add_monitor_log_func(f"Error: Failed to init LLM for Controller (step {i+1}). Skipping step.", "error_system")
            plan_failed = True; break
        
        step_tools = get_dynamic_tools(active_task_id)

        validated_tool_name, formulated_tool_input, controller_message, controller_confidence = await validate_and_prepare_step_action(
            original_user_query=original_user_query,
            plan_step=current_plan_step_obj,
            available_tools=step_tools,
            llm=controller_llm # type: ignore
        )

        await add_monitor_log_func(f"Controller Output (Step {i+1}): Tool='{validated_tool_name}', Input='{str(formulated_tool_input)[:100]}...', Confidence={controller_confidence:.2f}. Reasoning: {controller_message}", "system_controller_output")

        if controller_confidence < 0.7: # Example threshold
            await add_monitor_log_func(f"Warning: Controller confidence for step {i+1} is low ({controller_confidence:.2f}). Proceeding with caution.", "warning_controller")
        
        if validated_tool_name is None and "Error in Controller" in controller_message:
            logger.error(f"[{session_id}] Controller failed for step {i+1}: {controller_message}")
            await add_monitor_log_func(f"Error: Controller failed to process step {i+1}. Reason: {controller_message}. Skipping step.", "error_controller")
            plan_failed = True; break
        
        agent_input_for_step: str
        if validated_tool_name:
            agent_input_for_step = (
                f"Your current sub-task is: \"{step_description}\".\n"
                f"The Controller has determined you MUST use the tool '{validated_tool_name}' "
                f"with the following exact input: '{formulated_tool_input}'.\n"
                f"Do not attempt to use other tools or inputs for this immediate action. Execute this and report the result."
            )
            await add_monitor_log_func(f"Executor (Step {i+1}): Instructed to use tool '{validated_tool_name}' with specific input.", "system_executor_instructed")
        else:
            agent_input_for_step = (
                f"Your current sub-task is: \"{step_description}\".\n"
                f"The Controller has determined no specific tool is required for this step. "
                f"Please provide a direct answer or perform the necessary analysis based on the conversation history and this sub-task description."
            )
            await add_monitor_log_func(f"Executor (Step {i+1}): Instructed to respond directly (no tool from Controller).", "system_executor_direct")
        
        await send_ws_message_func("agent_thinking_update", {
            "status": f"Executor running Step {i+1}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."
        })
        await add_monitor_log_func(f"Executing Plan Step {i+1} (via Executor): {step_description}", "system_plan_step_start")

        step_executor_llm: Optional[BaseChatModel] = None
        try:
            llm_instance_exec = get_llm(settings, provider=step_llm_provider, model_name=step_llm_model_name)
            if not isinstance(llm_instance_exec, BaseChatModel):
                logger.warning(f"LLM for executor is not BaseChatModel, it's {type(llm_instance_exec)}.")
            step_executor_llm = llm_instance_exec # type: ignore
        except Exception as llm_err:
            logger.error(f"[{session_id}] Failed to init LLM for Executor (step {i+1}): {llm_err}")
            await add_monitor_log_func(f"Error: Failed to init LLM for Executor (step {i+1}). Skipping step.", "error_system")
            plan_failed = True; break
        
        step_memory = session_data_entry["memory"]
        step_callback_handler = session_data_entry["callback_handler"]
        
        try:
            step_agent_executor = create_agent_executor(
                llm=step_executor_llm, # type: ignore
                tools=step_tools,
                memory=step_memory,
                max_iterations=settings.agent_max_iterations
            )
            
            logger.info(f"[{session_id}] Invoking AgentExecutor for step {i+1} with input: '{agent_input_for_step[:100]}...'")
            
            agent_step_task = asyncio.create_task(
                step_agent_executor.ainvoke(
                    {"input": agent_input_for_step},
                    config=RunnableConfig(callbacks=[step_callback_handler])
                )
            )
            connected_clients_entry["agent_task"] = agent_step_task
            
            step_result = await agent_step_task
            
            step_output = step_result.get("output", "Step completed, no specific output from ReAct agent.")
            await add_monitor_log_func(f"Plan Step {i+1} (Executor) completed. Output: {str(step_output)[:200]}...", "system_plan_step_end")

        except AgentCancelledException:
            logger.warning(f"[{session_id}] Plan execution cancelled by user during step {i+1}.")
            await send_ws_message_func("status_message", "Plan execution cancelled.")
            await add_monitor_log_func(f"Plan execution cancelled by user during step {i+1}.", "system_cancel")
            plan_failed = True; break
        except Exception as step_exec_e:
            logger.error(f"[{session_id}] Error executing plan step {i+1} ('{step_description}'): {step_exec_e}", exc_info=True)
            await add_monitor_log_func(f"Error executing plan step {i+1}: {step_exec_e}", "error_plan_step")
            await send_ws_message_func("status_message", f"Error in step {i+1}. Stopping plan.")
            plan_failed = True; break
        finally:
            connected_clients_entry["agent_task"] = None

        if session_data_entry.get('cancellation_requested', False):
            logger.warning(f"[{session_id}] Cancellation detected after step {i+1}. Stopping plan.")
            await send_ws_message_func("status_message", "Plan execution cancelled.")
            plan_failed = True; break
    
    session_data_entry["plan_execution_active"] = False
    session_data_entry["current_plan_step_index"] = -1

    if plan_failed:
        final_overall_answer = "Plan execution stopped due to error or cancellation."
        await send_ws_message_func("agent_thinking_update", {"status": "Plan stopped."})
    else:
        final_overall_answer = "All plan steps executed." # TODO: Evaluator call
        await send_ws_message_func("agent_thinking_update", {"status": "Plan executed."})
        logger.info(f"[{session_id}] Successfully executed all {len(confirmed_plan_steps_dicts)} plan steps.")
    
    await send_ws_message_func("agent_message", final_overall_answer)
    await add_monitor_log_func(f"Overall Plan Execution: {final_overall_answer}", "system_plan_end")
    await send_ws_message_func("status_message", "Plan execution finished.")


async def process_new_task(
    session_id: str,
    data: Dict[str, Any], # Not strictly used by this handler, but kept for consistency
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    get_artifacts_func: GetArtifactsFunc # For sending empty artifact list
) -> None:
    """Handles the 'new_task' signal from the client."""
    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context.")
    
    session_data_entry['cancellation_requested'] = False
    session_data_entry['current_plan_structured'] = None
    session_data_entry['current_plan_human_summary'] = None
    session_data_entry['current_plan_step_index'] = -1
    session_data_entry['plan_execution_active'] = False
    session_data_entry['original_user_query'] = None

    existing_agent_task = connected_clients_entry.get("agent_task")
    if existing_agent_task and not existing_agent_task.done():
        logger.warning(f"[{session_id}] Cancelling active agent/plan task due to new task.")
        existing_agent_task.cancel()
        await send_ws_message_func("status_message", "Operation cancelled for new task.")
        await add_monitor_log_func("Agent/Plan operation cancelled due to new task creation.", "system_cancel")
        connected_clients_entry["agent_task"] = None
    
    session_data_entry["current_task_id"] = None # Signal that no task is active
    if "callback_handler" in session_data_entry:
        session_data_entry["callback_handler"].set_task_id(None)
    if "memory" in session_data_entry:
        session_data_entry["memory"].clear()
    
    await add_monitor_log_func("Cleared context for new task.", "system_new_task")
    await send_ws_message_func("update_artifacts", []) # Send empty artifact list


async def process_delete_task(
    session_id: str,
    data: Dict[str, Any], # Contains task_id_from_frontend
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_delete_task_func: DBDeleteTaskFunc, # Specific DB function
    get_artifacts_func: GetArtifactsFunc # For sending empty artifact list if active task deleted
) -> None:
    """Handles the 'delete_task' message from the client."""
    task_id_to_delete = data.get("taskId")
    if not task_id_to_delete:
        logger.warning(f"[{session_id}] 'delete_task' message missing taskId.")
        await add_monitor_log_func("Error: 'delete_task' received without taskId.", "error_system")
        return

    logger.warning(f"[{session_id}] Received request to delete task: {task_id_to_delete}")
    await add_monitor_log_func(f"Received request to delete task: {task_id_to_delete}", "system_delete_request")
    
    deleted_from_db = await db_delete_task_func(task_id_to_delete)
    
    if deleted_from_db:
        await add_monitor_log_func(f"Task {task_id_to_delete} deleted successfully from DB.", "system_delete_success")
        task_workspace_to_delete: Optional[Path] = None
        try:
            task_workspace_to_delete = get_task_workspace_path(task_id_to_delete, create=False)
            if task_workspace_to_delete.exists() and task_workspace_to_delete.is_relative_to(BASE_WORKSPACE_ROOT.resolve()):
                await asyncio.to_thread(shutil.rmtree, task_workspace_to_delete) # Run blocking shutil.rmtree in a thread
                logger.info(f"[{session_id}] Successfully deleted workspace directory: {task_workspace_to_delete}")
                await add_monitor_log_func(f"Workspace directory deleted: {task_workspace_to_delete.name}", "system_delete_success")
            else:
                logger.warning(f"[{session_id}] Workspace directory not found or invalid for deletion: {task_workspace_to_delete}")
        except Exception as ws_del_e:
            logger.error(f"[{session_id}] Error deleting workspace directory {task_workspace_to_delete}: {ws_del_e}")
            await add_monitor_log_func(f"Error deleting workspace directory: {ws_del_e}", "error_delete")
        
        # If the deleted task was the active one for this session, clear context
        if session_data_entry.get("current_task_id") == task_id_to_delete:
            session_data_entry['cancellation_requested'] = False
            session_data_entry['current_plan_structured'] = None
            session_data_entry['current_plan_human_summary'] = None
            session_data_entry['current_plan_step_index'] = -1
            session_data_entry['plan_execution_active'] = False
            session_data_entry['original_user_query'] = None
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
        await send_ws_message_func("status_message", f"Failed to delete task {task_id_to_delete[:8]}...")
        await add_monitor_log_func(f"Failed to delete task {task_id_to_delete} from DB.", "error_delete")


async def process_rename_task(
    session_id: str,
    data: Dict[str, Any], # Contains taskId, newName
    session_data_entry: Dict[str, Any], # Not directly used but passed for consistency
    connected_clients_entry: Dict[str, Any], # Not directly used
    send_ws_message_func: SendWSMessageFunc, # Not directly used
    add_monitor_log_func: AddMonitorLogFunc,
    db_rename_task_func: DBRenameTaskFunc # Specific DB function
) -> None:
    """Handles the 'rename_task' message from the client."""
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

