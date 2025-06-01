# backend/message_processing/operational_handlers.py
import logging
from typing import Dict, Any, Callable, Coroutine, Optional
import asyncio # Added for asyncio.sleep

# Project Imports
# (Type hints for passed functions will be defined here or imported)

logger = logging.getLogger(__name__)

# Type Hints for Passed-in Functions
SendWSMessageFunc = Callable[[str, Any], Coroutine[Any, Any, None]]
AddMonitorLogFunc = Callable[[str, str], Coroutine[Any, Any, None]]
GetArtifactsFunc = Callable[[str], Coroutine[Any, Any, None]] # Returns list, but None for coroutine itself
DBAddMessageFunc = Callable[[str, str, str, str], Coroutine[Any, Any, None]]
ExecuteShellCommandFunc = Callable[[str, str, SendWSMessageFunc, DBAddMessageFunc, Optional[str]], Coroutine[Any, Any, bool]]


async def process_cancel_agent(
    session_id: str, data: Dict[str, Any], session_data_entry: Dict[str, Any],
    connected_clients_entry: Dict[str, Any], send_ws_message_func: SendWSMessageFunc,
    add_monitor_log_func: AddMonitorLogFunc
) -> None:
    logger.warning(f"[{session_id}] Received request to cancel current operation.")
    session_data_entry['cancellation_requested'] = True
    # *** MODIFIED: Added critical debug log ***
    logger.critical(f"CRITICAL_DEBUG_CANCEL_HANDLER: [{session_id}] process_cancel_agent: Set cancellation_requested = True.")

    agent_task_to_cancel = connected_clients_entry.get("agent_task")
    if agent_task_to_cancel:
        # *** MODIFIED: Added detailed task logging ***
        task_name = agent_task_to_cancel.get_name() if hasattr(agent_task_to_cancel, 'get_name') else "Unknown Task Name"
        task_done = agent_task_to_cancel.done()
        task_cancelled_state = agent_task_to_cancel.cancelled() # Check if already cancelled
        logger.critical(f"CRITICAL_DEBUG_CANCEL_HANDLER: [{session_id}] process_cancel_agent: Found agent_task: Name='{task_name}', Done={task_done}, Cancelled_State={task_cancelled_state}. Attempting .cancel().")

        if not task_done:
            agent_task_to_cancel.cancel()
            logger.info(f"[{session_id}] asyncio.Task.cancel() called for active agent/plan task: {task_name}.")
            try:
                # Give a very brief moment for the cancellation to potentially propagate
                # if the task is currently in an awaitable point that respects cancellation.
                await asyncio.sleep(0.01) 
                logger.critical(f"CRITICAL_DEBUG_CANCEL_HANDLER: [{session_id}] process_cancel_agent: After .cancel() and sleep, task: Name='{task_name}', Done={agent_task_to_cancel.done()}, Cancelled_State={agent_task_to_cancel.cancelled()}.")
            except Exception as e_sleep: # Should not happen with asyncio.sleep(0.01) but good practice
                logger.error(f"[{session_id}] Error during sleep after cancel: {e_sleep}")
        else:
            logger.warning(f"[{session_id}] Agent task '{task_name}' was already done, cannot cancel.")
    else:
        logger.warning(f"[{session_id}] No active asyncio task found in connected_clients_entry to cancel.")


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
        logger.warning(f"[{session_id}] Received artifact refresh request for non-active task ({task_id_to_refresh} vs {active_task_id}). Ignoring for this session.")


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
        logger.info(f"[{session_id}] Received action command: {action} (Currently placeholder - Not fully implemented).")
        await add_monitor_log_func(f"Received action command: {action} (Handler not fully implemented).", "system_action_cmd")
    else:
        logger.warning(f"[{session_id}] Received 'action_command' with invalid/missing command content.")

