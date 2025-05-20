# This file makes the 'tools' directory a Python package.

# Import names from your standard_tools.py (or common_tools.py, etc.)
# so they can be imported directly from backend.tools
# For example, if your original tools.py was renamed to standard_tools.py:
from .standard_tools import (
    get_dynamic_tools,
    get_task_workspace_path,
    BASE_WORKSPACE_ROOT,
    TEXT_EXTENSIONS,
    # Add other specific tool classes or functions if they were directly imported elsewhere
    # e.g., ReadFileTool, WriteFileTool, PubMedSearchTool, etc.
    # However, it's often cleaner if get_dynamic_tools is the main entry point
    # for accessing tool instances.
)

# You can also import your new Playwright tool here if you want it to be
# accessible via `from backend.tools import PlaywrightSearchTool`,
# though it's often imported directly where instantiated.
# from .playwright_search import PlaywrightSearchTool

# The primary goal here is to make the names that server.py and other modules
# were expecting from the old `backend.tools.py` available again.
