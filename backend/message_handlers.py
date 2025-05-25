# backend/message_handlers.py
# This file now acts as a central point for importing and re-exporting
# the specific message processing functions from the message_processing sub-package.

import logging

# Import all process_... functions from their respective modules
# within the message_processing sub-package.
from .message_processing.task_handlers import (
    process_context_switch,
    process_new_task,
    process_delete_task,
    process_rename_task
)
from .message_processing.agent_flow_handlers import (
    process_user_message,
    process_execute_confirmed_plan,
    _update_plan_file_step_status # Helper, might not be needed for direct export if only used internally
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

# Optional: Define __all__ if you want to control "from backend.message_handlers import *" behavior.
# This makes it explicit what this module exports.
__all__ = [
    "process_context_switch",
    "process_new_task",
    "process_delete_task",
    "process_rename_task",
    "process_user_message",
    "process_execute_confirmed_plan",
    "_update_plan_file_step_status", # Exporting helper if it's used by other modules outside message_processing
    "process_set_llm",
    "process_get_available_models",
    "process_set_session_role_llm",
    "process_cancel_agent",
    "process_get_artifacts_for_task",
    "process_run_command",
    "process_action_command"
]

# The actual function definitions are now in their respective files
# within the backend/message_processing/ directory.
# This file primarily serves to gather them for easier import by server.py
# or other parts of the application if needed.

# Note: The type hints for passed-in functions (SendWSMessageFunc, etc.)
# are defined within each specific handler module now, or they could be
# centralized in a types.py file if preferred for larger projects.
# For this refactor, keeping them in each handler file is acceptable.

