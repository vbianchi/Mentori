# -----------------------------------------------------------------------------
# ResearchAgent Tools Package Initializer
#
# This file serves as a dynamic "plug-and-play" loader for all tools
# located in the `backend/tools` directory.
#
# How it works:
# 1. It scans the directory for all Python files (excluding this one).
# 2. It dynamically imports each file as a module.
# 3. It looks for a variable named `tool` within each module.
# 4. It collects all valid `Tool` objects into a single list.
#
# To add a new tool:
# - Create a new .py file in the `backend/tools/` directory.
# - In that file, define a LangChain `Tool` or `BaseTool` object.
# - Assign that object to a variable named `tool`.
# The loader will automatically discover and register it.
# -----------------------------------------------------------------------------

import os
import importlib
import logging
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

def load_all_tools():
    """
    Scans the 'tools' directory, imports all tool modules, and returns
    a list of their `tool` objects.
    """
    all_tools = []
    tools_dir = os.path.dirname(__file__)
    
    logger.info(f"Scanning for tools in: {tools_dir}")

    for filename in os.listdir(tools_dir):
        # Consider only Python files that are not this __init__.py file
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"backend.tools.{filename[:-3]}"
            try:
                # Dynamically import the module
                module = importlib.import_module(module_name)
                
                # Look for a variable named 'tool' in the imported module
                tool_instance = getattr(module, 'tool', None)
                
                if isinstance(tool_instance, BaseTool):
                    logger.info(f"Successfully loaded tool: '{tool_instance.name}' from {filename}")
                    all_tools.append(tool_instance)
                elif tool_instance is not None:
                    logger.warning(f"Found a 'tool' variable in {filename} but it is not a valid Tool object.")

            except Exception as e:
                logger.error(f"Failed to load tool from {filename}: {e}", exc_info=True)

    logger.info(f"Loaded a total of {len(all_tools)} tools.")
    return all_tools

# Load tools on package import to make them available globally within the app
available_tools = load_all_tools()

# You can also define a function to get them if you prefer deferred loading,
# but pre-loading is fine for our current architecture.
def get_available_tools():
    """Returns the list of pre-loaded tools."""
    return available_tools
