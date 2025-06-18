# -----------------------------------------------------------------------------
# ResearchAgent Tools Package Initializer (Upgraded)
#
# This loader is now upgraded to be more flexible. It can discover modules
# that provide either a single `tool` variable or a list of tools in a
# `tools` variable.
#
# To add a new tool or set of tools:
# - Create a new .py file in the `backend/tools/` directory.
# - In that file, define your Tool objects.
# - To export a single tool, assign it to a variable named `tool`.
# - To export multiple tools from one file, assign them as a list to a
#   variable named `tools`.
# -----------------------------------------------------------------------------

import os
import importlib
import logging
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

def load_all_tools():
    """
    Scans the 'tools' directory, imports all tool modules, and returns
    a list of all discovered tool objects.
    """
    all_tools = []
    tools_dir = os.path.dirname(__file__)
    
    logger.info(f"Scanning for tools in: {tools_dir}")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"backend.tools.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                
                # --- New Logic: Check for a list of tools first ---
                if hasattr(module, 'tools') and isinstance(getattr(module, 'tools'), list):
                    tool_list = getattr(module, 'tools')
                    for tool_instance in tool_list:
                        if isinstance(tool_instance, BaseTool):
                            logger.info(f"Successfully loaded tool: '{tool_instance.name}' from {filename}")
                            all_tools.append(tool_instance)
                
                # --- Fallback: Check for a single tool variable ---
                elif hasattr(module, 'tool') and isinstance(getattr(module, 'tool'), BaseTool):
                    tool_instance = getattr(module, 'tool')
                    logger.info(f"Successfully loaded tool: '{tool_instance.name}' from {filename}")
                    all_tools.append(tool_instance)

            except Exception as e:
                logger.error(f"Failed to load tool(s) from {filename}: {e}", exc_info=True)

    logger.info(f"Loaded a total of {len(all_tools)} tools.")
    return all_tools

# Load tools on package import
available_tools = load_all_tools()

def get_available_tools():
    """Returns the list of pre-loaded tools."""
    return available_tools
