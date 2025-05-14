import logging
import json
import datetime
from typing import Dict, Any, Callable, Coroutine, Optional, List
import asyncio
import shutil 

# LangChain Imports
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig 

# Project Imports
from backend.config import settings
from backend.llm_setup import get_llm
from backend.tools import get_dynamic_tools, get_task_workspace_path, BASE_WORKSPACE_ROOT
from backend.planner import generate_plan, PlanStep
from backend.controller import validate_and_prepare_step_action
from backend.agent import create_agent_executor
from backend.callbacks import AgentCancelledException
from backend.intent_classifier import classify_intent
from backend.evaluator import evaluate_plan_outcome, EvaluationResult
# db_utils functions and server-specific helpers (like execute_shell_command) will be passed as callables

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
    # ... (Content from previous message_handlers_py_evaluator_integration, unchanged) ...
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
    # ... (Content from message_handlers_py_evaluator_integration, unchanged) ...
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
    
    await send_ws_message_func("agent_thinking_update", {"status": "Classifying intent..."})
    selected_provider = session_data_entry.get("selected_llm_provider", settings.default_provider)
    selected_model_name = session_data_entry.get("selected_llm_model_name", settings.default_model_name)
    intent_llm: Optional[BaseChatModel] = None
    try:
        llm_instance = get_llm(settings, provider=selected_provider, model_name=selected_model_name)
        if not isinstance(llm_instance, BaseChatModel):
            logger.warning(f"LLM for intent classification is not BaseChatModel, it's {type(llm_instance)}.")
        intent_llm = llm_instance # type: ignore
    except Exception as llm_init_err:
        logger.error(f"[{session_id}] Failed to initialize LLM for intent classification: {llm_init_err}", exc_info=True)
        await add_monitor_log_func(f"Error initializing LLM for intent classification: {llm_init_err}", "error_system")
        await send_ws_message_func("status_message", "Error: Failed to prepare for intent classification.")
        await send_ws_message_func("agent_message", "Sorry, I couldn't figure out how to approach your request.")
        await send_ws_message_func("agent_thinking_update", {"status": "Intent classification failed."})
        return

    dynamic_tools = get_dynamic_tools(active_task_id)
    tools_summary_for_intent = "\n".join([f"- {tool.name}: {tool.description.split('.')[0]}" for tool in dynamic_tools])
    
    classified_intent = await classify_intent(user_input_content, intent_llm, tools_summary_for_intent)
    await add_monitor_log_func(f"Intent classified as: {classified_intent}", "system_intent_classified")

    if classified_intent == "PLAN":
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan..."})
        planner_llm = intent_llm 
        
        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content,
            llm=planner_llm, # type: ignore
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

        direct_qa_llm = intent_llm 
        direct_qa_memory = session_data_entry["memory"]
        direct_qa_callback_handler = session_data_entry["callback_handler"]
        
        try:
            agent_executor_direct = create_agent_executor(
                llm=direct_qa_llm, # type: ignore
                tools=dynamic_tools, 
                memory=direct_qa_memory,
                max_iterations=settings.agent_max_iterations 
            )
            
            logger.info(f"[{session_id}] Invoking AgentExecutor directly for QA with input: '{user_input_content[:100]}...'")
            
            direct_qa_task = asyncio.create_task(
                agent_executor_direct.ainvoke(
                    {"input": user_input_content},
                    config=RunnableConfig(callbacks=[direct_qa_callback_handler])
                )
            )
            connected_clients_entry["agent_task"] = direct_qa_task
            
            await direct_qa_task 

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
            connected_clients_entry["agent_task"] = None 
            await send_ws_message_func("agent_thinking_update", {"status": "Idle."}) 

    else: 
        logger.error(f"[{session_id}] Unknown intent classified: {classified_intent}. Defaulting to planning.")
        await add_monitor_log_func(f"Error: Unknown intent '{classified_intent}'. Defaulting to PLAN.", "error_system")
        await send_ws_message_func("agent_thinking_update", {"status": "Generating plan (fallback)..."})
        planner_llm = intent_llm
        human_plan_summary, structured_plan_steps = await generate_plan(
            user_query=user_input_content, llm=planner_llm, available_tools_summary=tools_summary_for_intent
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
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    # ... (Content from message_handlers_py_evaluator_integration, unchanged) ...
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
    preliminary_final_answer = "Plan execution completed." 
    step_execution_details_list = [] 

    original_user_query = session_data_entry.get("original_user_query", "No original query context available.")
    if not original_user_query:
            await add_monitor_log_func(f"Warning: Original user query not found in session data for controller context.", "warning_system")

    for i, step_dict in enumerate(confirmed_plan_steps_dicts):
        session_data_entry["current_plan_step_index"] = i
        current_step_detail = { 
            "step_number": i + 1, "description": "N/A", "controller_tool": "N/A", 
            "controller_input": "N/A", "controller_reasoning": "N/A", "controller_confidence": 0.0,
            "executor_input": "N/A", "executor_output": "N/A", "error": None
        }
        
        try:
            current_plan_step_obj = PlanStep(**step_dict)
            current_step_detail["description"] = current_plan_step_obj.description
        except Exception as pydantic_err:
            logger.error(f"[{session_id}] Failed to parse step dictionary into PlanStep object: {pydantic_err}. Step data: {step_dict}", exc_info=True)
            error_msg = f"Error: Corrupted plan step {i+1}. Skipping. Details: {pydantic_err}"
            await add_monitor_log_func(error_msg, "error_plan_step")
            current_step_detail["error"] = error_msg
            step_execution_details_list.append(current_step_detail)
            plan_failed = True; break
        
        step_description = current_plan_step_obj.description
        step_tool_suggestion_planner = current_plan_step_obj.tool_to_use or "None"
        
        await send_ws_message_func("agent_thinking_update", {
            "status": f"Controller validating Step {i+1}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."
        })
        await add_monitor_log_func(f"Controller: Validating Plan Step {i+1}: {step_description} (Planner hint: {step_tool_suggestion_planner})", "system_controller_start")

        step_llm_provider = session_data_entry.get("selected_llm_provider", settings.default_provider)
        step_llm_model_name = session_data_entry.get("selected_llm_model_name", settings.default_model_name)
        current_step_llm: Optional[BaseChatModel] = None 
        try:
            llm_instance = get_llm(settings, provider=step_llm_provider, model_name=step_llm_model_name)
            if not isinstance(llm_instance, BaseChatModel):
                logger.warning(f"LLM for step {i+1} is not BaseChatModel, it's {type(llm_instance)}.")
            current_step_llm = llm_instance # type: ignore
        except Exception as llm_err:
            logger.error(f"[{session_id}] Failed to init LLM for Controller/Executor (step {i+1}): {llm_err}")
            error_msg = f"Error: Failed to init LLM for step {i+1}. Skipping step. Details: {llm_err}"
            await add_monitor_log_func(error_msg, "error_system")
            current_step_detail["error"] = error_msg
            step_execution_details_list.append(current_step_detail)
            plan_failed = True; break
        
        step_tools = get_dynamic_tools(active_task_id)

        validated_tool_name, formulated_tool_input, controller_message, controller_confidence = await validate_and_prepare_step_action(
            original_user_query=original_user_query,
            plan_step=current_plan_step_obj,
            available_tools=step_tools,
            llm=current_step_llm # type: ignore
        )
        current_step_detail.update({ 
            "controller_tool": validated_tool_name, "controller_input": formulated_tool_input,
            "controller_reasoning": controller_message, "controller_confidence": controller_confidence
        })

        await add_monitor_log_func(f"Controller Output (Step {i+1}): Tool='{validated_tool_name}', Input='{str(formulated_tool_input)[:100]}...', Confidence={controller_confidence:.2f}. Reasoning: {controller_message}", "system_controller_output")

        if controller_confidence < 0.7: 
            await add_monitor_log_func(f"Warning: Controller confidence for step {i+1} is low ({controller_confidence:.2f}). Proceeding with caution.", "warning_controller")
        
        if validated_tool_name is None and "Error in Controller" in controller_message:
            logger.error(f"[{session_id}] Controller failed for step {i+1}: {controller_message}")
            error_msg = f"Error: Controller failed to process step {i+1}. Reason: {controller_message}. Skipping step."
            await add_monitor_log_func(error_msg, "error_controller")
            current_step_detail["error"] = error_msg 
            step_execution_details_list.append(current_step_detail) 
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
        current_step_detail["executor_input"] = agent_input_for_step 
        
        await send_ws_message_func("agent_thinking_update", {
            "status": f"Executor running Step {i+1}/{len(confirmed_plan_steps_dicts)}: {step_description[:40]}..."
        })
        await add_monitor_log_func(f"Executing Plan Step {i+1} (via Executor): {step_description}", "system_plan_step_start")
        
        step_memory = session_data_entry["memory"]
        step_callback_handler = session_data_entry["callback_handler"]
        
        try:
            step_agent_executor = create_agent_executor(
                llm=current_step_llm, # type: ignore 
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
            current_step_detail["executor_output"] = step_output 
            await add_monitor_log_func(f"Plan Step {i+1} (Executor) completed. Output: {str(step_output)[:200]}...", "system_plan_step_end")

        except AgentCancelledException as ace:
            logger.warning(f"[{session_id}] Plan execution cancelled by user during step {i+1}.")
            await send_ws_message_func("status_message", "Plan execution cancelled.")
            error_msg = f"Plan execution cancelled by user during step {i+1}."
            await add_monitor_log_func(error_msg, "system_cancel")
            current_step_detail["error"] = error_msg 
            plan_failed = True
        except Exception as step_exec_e:
            logger.error(f"[{session_id}] Error executing plan step {i+1} ('{step_description}'): {step_exec_e}", exc_info=True)
            error_msg = f"Error executing plan step {i+1}: {step_exec_e}"
            await add_monitor_log_func(error_msg, "error_plan_step")
            await send_ws_message_func("status_message", f"Error in step {i+1}. Stopping plan.")
            current_step_detail["error"] = error_msg 
            plan_failed = True
        finally:
            connected_clients_entry["agent_task"] = None
            step_execution_details_list.append(current_step_detail) 
            if plan_failed: break 

        if session_data_entry.get('cancellation_requested', False): 
            logger.warning(f"[{session_id}] Cancellation detected after step {i+1}. Stopping plan.")
            await send_ws_message_func("status_message", "Plan execution cancelled.")
            if not current_step_detail.get("error"):
                 current_step_detail["error"] = "Cancelled by user after step completion."
            plan_failed = True; break 
    
    session_data_entry["plan_execution_active"] = False
    session_data_entry["current_plan_step_index"] = -1 

    summary_lines = []
    for detail in step_execution_details_list:
        summary_lines.append(f"Step {detail['step_number']}: {detail['description']}")
        summary_lines.append(f"  Controller Action: Tool='{detail['controller_tool']}', Input='{str(detail['controller_input'])[:100]}', Confidence={detail['controller_confidence']:.2f}")
        if detail.get("controller_reasoning"): 
             summary_lines.append(f"  Controller Reasoning: {detail['controller_reasoning']}")
        summary_lines.append(f"  Executor Input (to ReAct): {str(detail['executor_input'])[:150]}...")
        if detail['error']:
            summary_lines.append(f"  Outcome: Error - {str(detail['error'])[:200]}...")
        else:
            summary_lines.append(f"  Outcome (Executor Output): {str(detail['executor_output'])[:200]}...")
        summary_lines.append("-" * 20)
    executed_plan_summary_str = "\n".join(summary_lines)
    if not step_execution_details_list:
        executed_plan_summary_str = "No steps were attempted or recorded."

    if plan_failed:
        preliminary_final_answer = "Plan execution stopped due to error or cancellation."
        await send_ws_message_func("agent_thinking_update", {"status": "Plan stopped."})
    else:
        preliminary_final_answer = "All plan steps attempted." 
        await send_ws_message_func("agent_thinking_update", {"status": "Plan executed. Evaluating outcome..."})
        logger.info(f"[{session_id}] Successfully attempted all {len(confirmed_plan_steps_dicts)} plan steps. Now evaluating.")

    final_overall_answer = preliminary_final_answer 
    evaluator_llm: Optional[BaseChatModel] = None
    try:
        eval_llm_provider = session_data_entry.get("selected_llm_provider", settings.default_provider)
        eval_llm_model_name = session_data_entry.get("selected_llm_model_name", settings.default_model_name)
        llm_instance_eval = get_llm(settings, provider=eval_llm_provider, model_name=eval_llm_model_name)
        if not isinstance(llm_instance_eval, BaseChatModel):
            logger.warning(f"LLM for evaluator is not BaseChatModel, it's {type(llm_instance_eval)}.")
        evaluator_llm = llm_instance_eval # type: ignore
        
        await add_monitor_log_func("Invoking Evaluator to assess overall outcome.", "system_evaluator_start")
        evaluation_result = await evaluate_plan_outcome(
            original_user_query=original_user_query,
            executed_plan_summary=executed_plan_summary_str,
            final_agent_answer=preliminary_final_answer, 
            llm=evaluator_llm # type: ignore
        )

        if evaluation_result:
            final_overall_answer = evaluation_result.assessment
            log_msg = (
                f"Evaluator Result: Success={evaluation_result.overall_success}, "
                f"Confidence={evaluation_result.confidence_score:.2f}. "
                f"Assessment: {evaluation_result.assessment}"
            )
            await add_monitor_log_func(log_msg, "system_evaluator_output")
            if not evaluation_result.overall_success and evaluation_result.suggestions_for_replan:
                await add_monitor_log_func(f"Evaluator Suggestions: {evaluation_result.suggestions_for_replan}", "system_evaluator_suggestions")
        else:
            await add_monitor_log_func("Evaluator failed to produce a result. Using preliminary answer.", "error_evaluator")
    except Exception as eval_err:
        logger.error(f"[{session_id}] Error during evaluation phase: {eval_err}", exc_info=True)
        await add_monitor_log_func(f"Error during evaluation phase: {eval_err}. Using preliminary answer.", "error_evaluator")
    
    await send_ws_message_func("agent_message", final_overall_answer)
    await add_monitor_log_func(f"Final Overall Outcome: {final_overall_answer}", "system_plan_end") 
    await send_ws_message_func("status_message", "Processing complete.")
    await send_ws_message_func("agent_thinking_update", {"status": "Idle."}) 


async def process_new_task(
    session_id: str,
    data: Dict[str, Any], 
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    get_artifacts_func: GetArtifactsFunc 
) -> None:
    # ... (Content from message_handlers_py_extended, unchanged) ...
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
    
    session_data_entry["current_task_id"] = None 
    if "callback_handler" in session_data_entry:
        session_data_entry["callback_handler"].set_task_id(None)
    if "memory" in session_data_entry:
        session_data_entry["memory"].clear()
    
    await add_monitor_log_func("Cleared context for new task.", "system_new_task")
    await send_ws_message_func("update_artifacts", []) 


async def process_delete_task(
    session_id: str,
    data: Dict[str, Any], 
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_delete_task_func: DBDeleteTaskFunc, 
    get_artifacts_func: GetArtifactsFunc 
) -> None:
    # ... (Content from message_handlers_py_extended, unchanged) ...
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
                await asyncio.to_thread(shutil.rmtree, task_workspace_to_delete) 
                logger.info(f"[{session_id}] Successfully deleted workspace directory: {task_workspace_to_delete}")
                await add_monitor_log_func(f"Workspace directory deleted: {task_workspace_to_delete.name}", "system_delete_success")
            else:
                logger.warning(f"[{session_id}] Workspace directory not found or invalid for deletion: {task_workspace_to_delete}")
        except Exception as ws_del_e:
            logger.error(f"[{session_id}] Error deleting workspace directory {task_workspace_to_delete}: {ws_del_e}")
            await add_monitor_log_func(f"Error deleting workspace directory: {ws_del_e}", "error_delete")
        
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
    data: Dict[str, Any], 
    session_data_entry: Dict[str, Any], 
    connected_clients_entry: Dict[str, Any], 
    send_ws_message_func: SendWSMessageFunc, 
    add_monitor_log_func: AddMonitorLogFunc,
    db_rename_task_func: DBRenameTaskFunc 
) -> None:
    # ... (Content from message_handlers_py_extended, unchanged) ...
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

# --- MODIFIED: Added remaining handlers ---

async def process_set_llm(
    session_id: str,
    data: Dict[str, Any],
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], # Not used but kept for signature consistency
    send_ws_message_func: SendWSMessageFunc, # Not used but kept
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    """Handles the 'set_llm' message from the client."""
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
                logger.info(f"[{session_id}] Set session LLM to: {provider}::{model_name_from_id}")
                await add_monitor_log_func(f"Session LLM set to {provider}::{model_name_from_id}", "system_llm_set")
            else:
                logger.warning(f"[{session_id}] Received request to set invalid/unavailable LLM ID: {llm_id}")
                await add_monitor_log_func(f"Attempted to set invalid LLM: {llm_id}", "error_llm_set")
        except ValueError:
            logger.warning(f"[{session_id}] Received invalid LLM ID format in set_llm: {llm_id}")
            await add_monitor_log_func(f"Received invalid LLM ID format: {llm_id}", "error_llm_set")
    else:
        logger.warning(f"[{session_id}] Received invalid 'set_llm' message content: {data}")

async def process_get_available_models(
    session_id: str,
    data: Dict[str, Any], # Not used
    session_data_entry: Dict[str, Any], # Not used
    connected_clients_entry: Dict[str, Any], # Not used
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc # Not strictly needed but good for consistency
) -> None:
    """Handles the 'get_available_models' request from the client."""
    logger.info(f"[{session_id}] Received request for available models.")
    await send_ws_message_func("available_models", {
        "gemini": settings.gemini_available_models,
        "ollama": settings.ollama_available_models,
        "default_llm_id": settings.default_llm_id
    })
    # No specific monitor log needed here as it's a passive info request

async def process_cancel_agent(
    session_id: str,
    data: Dict[str, Any], # Not used
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any],
    send_ws_message_func: SendWSMessageFunc, # Not used but kept
    add_monitor_log_func: AddMonitorLogFunc # Not used but kept
) -> None:
    """Handles the 'cancel_agent' message from the client."""
    logger.warning(f"[{session_id}] Received request to cancel current operation.")
    session_data_entry['cancellation_requested'] = True
    logger.info(f"[{session_id}] Cancellation requested flag set to True.")
    
    agent_task_to_cancel = connected_clients_entry.get("agent_task")
    if agent_task_to_cancel and not agent_task_to_cancel.done():
        agent_task_to_cancel.cancel() # Attempt to cancel the asyncio task
        logger.info(f"[{session_id}] asyncio.Task.cancel() called for active task.")
    else:
        logger.info(f"[{session_id}] No active asyncio task found to cancel, or task already done. Flag will be checked by callbacks/plan loop.")

async def process_get_artifacts_for_task(
    session_id: str,
    data: Dict[str, Any], # Contains taskId
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], # Not used
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, # Not strictly needed
    get_artifacts_func: GetArtifactsFunc
) -> None:
    """Handles the 'get_artifacts_for_task' request from the client."""
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
    session_id: str,
    data: Dict[str, Any], # Contains command
    session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], # Not used
    send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc,
    db_add_message_func: DBAddMessageFunc, # For execute_shell_command
    execute_shell_command_func: ExecuteShellCommandFunc # Passed from server.py
) -> None:
    """Handles the 'run_command' message from the client."""
    command_to_run = data.get("command")
    if command_to_run and isinstance(command_to_run, str):
        active_task_id_for_cmd = session_data_entry.get("current_task_id")
        await add_monitor_log_func(f"Received direct 'run_command'. Executing: {command_to_run} (Task Context: {active_task_id_for_cmd})", "system_direct_cmd")
        await execute_shell_command_func(
            command_to_run, 
            session_id, 
            send_ws_message_func, # This send_ws_message_func is from the handler's scope
            db_add_message_func,  # This db_add_message_func is from the handler's scope
            active_task_id_for_cmd
        )
    else:
        logger.warning(f"[{session_id}] Received 'run_command' with invalid/missing command content.")
        await add_monitor_log_func("Error: 'run_command' received with no command specified.", "error_direct_cmd")

async def process_action_command(
    session_id: str,
    data: Dict[str, Any], # Contains command
    session_data_entry: Dict[str, Any], # Not used
    connected_clients_entry: Dict[str, Any], # Not used
    send_ws_message_func: SendWSMessageFunc, # Not used
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    """Handles placeholder 'action_command' messages."""
    action = data.get("command")
    if action and isinstance(action, str):
        logger.info(f"[{session_id}] Received action command: {action} (Not implemented).")
        await add_monitor_log_func(f"Received action command: {action} (Handler not implemented).", "system_action_cmd")
    else:
        logger.warning(f"[{session_id}] Received 'action_command' with invalid/missing command content.")

