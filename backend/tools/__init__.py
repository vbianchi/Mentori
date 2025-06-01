# backend/tools/__init__.py

# <<< NEW IMPORT --- >>>
import logging
# <<< --- END NEW IMPORT --- >>>

# Import names that server.py and other modules might be expecting
# directly from the backend.tools package.

from .standard_tools import (
    get_dynamic_tools,
    TEXT_EXTENSIONS,
    # Specific tool classes defined in standard_tools.py if they need to be directly accessible
    # e.g., ReadFileTool, WriteFileTool, TaskWorkspaceShellTool (though these are now loaded via config)
)

from backend.tool_loader import get_task_workspace_path, BASE_WORKSPACE_ROOT


# Individual tool classes are in their own modules and loaded via tool_config.json.
# They generally don't need to be re-exported here unless something specifically
# tries to import, e.g., `from backend.tools import TavilyAPISearchTool`.
# For now, we assume direct imports like `from backend.tools.tavily_search_tool import TavilyAPISearchTool`
# are used if a specific tool class is needed outside of the dynamic loading mechanism.

logger = logging.getLogger(__name__)
logger.debug("backend.tools package initialized.")
