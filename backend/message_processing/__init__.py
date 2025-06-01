# backend/message_processing/__init__.py

import logging # <--- ADDED IMPORT

# Import functions from the handler modules to make them easily accessible
# when importing from the message_processing package.

from .task_handlers import (
    process_context_switch,
    process_new_task,
    process_delete_task,
    process_rename_task
)
from .agent_flow_handlers import (
    process_user_message,
    process_execute_confirmed_plan,
    _update_plan_file_step_status # Helper, might not be needed for direct export if only used internally
)
from .config_handlers import (
    process_set_llm,
    process_get_available_models,
    process_set_session_role_llm
)
from .operational_handlers import (
    process_cancel_agent,
    process_get_artifacts_for_task,
    process_run_command,
    process_action_command
)

# You can define __all__ to specify what gets imported with "from . import *"
# For now, direct imports are fine.
# __all__ = [
#     "process_context_switch", "process_new_task", "process_delete_task", "process_rename_task",
#     "process_user_message", "process_execute_confirmed_plan",
#     "process_set_llm", "process_get_available_models", "process_set_session_role_llm",
#     "process_cancel_agent", "process_get_artifacts_for_task", "process_run_command", "process_action_command"
# ]

logger = logging.getLogger(__name__)
logger.debug("message_processing package initialized.")

