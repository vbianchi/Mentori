# backend/message_processing/task_handlers.py
import logging
import datetime
import shutil # For shutil.rmtree
from pathlib import Path
import asyncio # For asyncio.to_thread

from typing import Dict, Any, Callable, Coroutine, Optional, List

# LangChain Imports
from langchain_core.messages import AIMessage, HumanMessage

# Project Imports
from backend.config import settings 
from backend.tools import get_task_workspace_path, BASE_WORKSPACE_ROOT 


logger = logging.getLogger(__name__)

# Type Hints for Passed-in Functions
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
DBAddTaskFunc = Callable[[str, str, str], Coroutine[Any, Any, None]]
DBGetMessagesFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, Any]]]]
DBDeleteTaskFunc = Callable[[str], Coroutine[Any, Any, bool]]
DBRenameTaskFunc = Callable[[str, str], Coroutine[Any, Any, bool]]
GetArtifactsFunc = Callable[[str], Coroutine[Any, Any, List[Dict[str, str]]]]


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
    session_data_entry['current_plan_proposal_id_backend'] = None


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
            elif db_msg_type in ["agent_finish", "agent_message", "agent", "agent_final_assessment"]:
                ui_msg_type = "agent_message"; send_to_chat = True
                chat_history_for_memory.append(AIMessage(content=db_content_hist))
            # --- MODIFICATION START: Handle confirmed_plan_log for history ---
            elif db_msg_type == "confirmed_plan_log":
                ui_msg_type = "confirmed_plan_log"; send_to_chat = True 
                # content_to_send is already db_content_hist (the JSON string)
                # No need to add this to agent's short-term ReAct memory, 
                # but it will be rendered in chat.
            # --- MODIFICATION END ---
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
                    # Send with the determined ui_msg_type (e.g., 'user', 'agent_message', 'confirmed_plan_log')
                    await send_ws_message_func(ui_msg_type, content_to_send) 
                elif ui_msg_type == "monitor_log": 
                    await send_ws_message_func("monitor_log", content_to_send)
                await asyncio.sleep(0.005) 

        await send_ws_message_func("history_end", "History loaded.")
        logger.info(f"[{session_id}] Finished sending {len(history_messages)} history messages.")

        MAX_MEMORY_RELOAD = settings.agent_memory_window_k
        if "memory" in session_data_entry:
            try:
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


async def process_new_task(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc, get_artifacts_func: GetArtifactsFunc
) -> None:
    logger.info(f"[{session_id}] Received 'new_task' signal. Clearing context for UI.")

    session_data_entry['cancellation_requested'] = False
    session_data_entry['current_plan_structured'] = None
    session_data_entry['current_plan_human_summary'] = None
    session_data_entry['current_plan_step_index'] = -1
    session_data_entry['plan_execution_active'] = False
    session_data_entry['original_user_query'] = None
    session_data_entry['active_plan_filename'] = None
    session_data_entry['current_plan_proposal_id_backend'] = None


    existing_agent_task = connected_clients_entry.get("agent_task")
    if existing_agent_task and not existing_agent_task.done():
        logger.warning(f"[{session_id}] Cancelling active agent/plan task due to new task signal.")
        existing_agent_task.cancel()
        await send_ws_message_func("status_message", "Operation cancelled for new task.")
        await add_monitor_log_func("Agent/Plan operation cancelled due to new task creation signal.", "system_cancel")
        connected_clients_entry["agent_task"] = None

    session_data_entry["current_task_id"] = None
    if "callback_handler" in session_data_entry: 
        session_data_entry["callback_handler"].set_task_id(None)
    if "memory" in session_data_entry:
        session_data_entry["memory"].clear()

    await add_monitor_log_func("Cleared context for new task signal. Awaiting new task context switch from client.", "system_new_task")
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
            task_workspace_to_delete = get_task_workspace_path(task_id_to_delete, create_if_not_exists=False)
            if task_workspace_to_delete.exists():
                if task_workspace_to_delete.resolve().is_relative_to(BASE_WORKSPACE_ROOT.resolve()) and \
                   BASE_WORKSPACE_ROOT.resolve() != task_workspace_to_delete.resolve():
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
                workspace_deletion_successful = True 
        except Exception as ws_del_e:
            logger.error(f"[{session_id}] Error during workspace directory deletion for task {task_id_to_delete} (path: {task_workspace_to_delete}): {ws_del_e}", exc_info=True)
            await add_monitor_log_func(f"Error deleting workspace directory for task {task_id_to_delete}: {str(ws_del_e)}", "error_delete")
            await send_ws_message_func("status_message", f"Task DB deleted, but workspace folder for {task_id_to_delete[:8]} failed to delete.")

        if session_data_entry.get("current_task_id") == task_id_to_delete:
            logger.info(f"[{session_id}] Active task {task_id_to_delete} was deleted. Clearing session context.")
            session_data_entry['cancellation_requested'] = False
            session_data_entry['current_plan_structured'] = None
            session_data_entry['current_plan_human_summary'] = None
            session_data_entry['current_plan_step_index'] = -1
            session_data_entry['plan_execution_active'] = False
            session_data_entry['original_user_query'] = None
            session_data_entry['active_plan_filename'] = None
            session_data_entry['current_plan_proposal_id_backend'] = None
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
        await add_monitor_log_func(f"Failed to delete task {task_id_to_delete} from DB.", "error_db")


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

