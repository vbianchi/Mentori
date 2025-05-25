# backend/message_handlers.py
import logging

from .message_processing.task_handlers import (
    process_context_switch,
    process_new_task,
    process_delete_task,
    process_rename_task
)
from .message_processing.agent_flow_handlers import (
    process_user_message,
    process_execute_confirmed_plan,
    process_cancel_plan_proposal, # ADDED
    _update_plan_file_step_status 
)
from .message_processing.config_handlers import (
    process_set_llm,
    process_get_available_models,
    process_set_session_role_llm
)
from .message_processing.operational_handlers import (
    process_cancel_agent,
    process_get_artifacts_for_task,
    process_run_command,
    process_action_command
)

logger = logging.getLogger(__name__)
logger.info("message_handlers.py: All processing functions imported from message_processing sub-package.")

__all__ = [
    "process_context_switch",
    "process_new_task",
    "process_delete_task",
    "process_rename_task",
    "process_user_message",
    "process_execute_confirmed_plan",
    "process_cancel_plan_proposal", # ADDED
    "_update_plan_file_step_status", 
    "process_set_llm",
    "process_get_available_models",
    "process_set_session_role_llm",
    "process_cancel_agent",
    "process_get_artifacts_for_task",
    "process_run_command",
    "process_action_command"
]
