# -----------------------------------------------------------------------------
# ResearchAgent Tools Package Initializer (Phase 13.3: Live Reloading)
#
# This definitive version enables the "Tool Forge" by implementing live
# reloading of tools. The agent can now discover and use custom-built tools
# without requiring a server restart.
#
# Key Architectural Changes:
# 1. Dynamic `get_available_tools()`: This function no longer returns a
#    statically loaded list. It now performs a live scan of the tools
#    directory every time it's called.
# 2. Module Reloading with `importlib`: It intelligently tracks already
#    imported modules. If it encounters a tool module that has been loaded
#    before, it uses `importlib.reload()` to ensure the latest version of
#    the code is used. This is critical for allowing users to edit and
#    update their custom tools in the future.
# 3. Decoupled Loading: The `available_tools` variable has been removed.
#    Loading is now fully on-demand, triggered by the agent at the start
#    of each run, making the system more robust and dynamic.
# -----------------------------------------------------------------------------

import os
import importlib
import logging
from langchain_core.tools import BaseTool
import sys

logger = logging.getLogger(__name__)

# --- Module Cache for Live Reloading ---
# This dictionary will keep track of modules we've already imported.
_MODULE_CACHE = {}

def get_available_tools():
    """
    Scans the 'tools' directory, imports all tool modules, reloads them if
    necessary, and returns a fresh list of all discovered tool objects.
    """
    all_tools = []
    tools_dir = os.path.dirname(__file__)
    
    logger.info(f"Dynamically scanning for tools in: {tools_dir}")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"backend.tools.{filename[:-3]}"
            try:
                # --- Live Reloading Logic ---
                if module_name in _MODULE_CACHE:
                    # If we've seen this module before, reload it to pick up changes
                    module = importlib.reload(_MODULE_CACHE[module_name])
                    logger.debug(f"Reloaded module: {module_name}")
                else:
                    # Otherwise, import it for the first time
                    module = importlib.import_module(module_name)
                    logger.debug(f"Imported new module: {module_name}")
                
                # Store the imported/reloaded module in our cache
                _MODULE_CACHE[module_name] = module
                
                # --- Tool Discovery (no change) ---
                if hasattr(module, 'tools') and isinstance(getattr(module, 'tools'), list):
                    tool_list = getattr(module, 'tools')
                    for tool_instance in tool_list:
                        if isinstance(tool_instance, BaseTool):
                            logger.info(f"Discovered tool: '{tool_instance.name}' from {filename}")
                            all_tools.append(tool_instance)
                
                elif hasattr(module, 'tool') and isinstance(getattr(module, 'tool'), BaseTool):
                    tool_instance = getattr(module, 'tool')
                    logger.info(f"Discovered tool: '{tool_instance.name}' from {filename}")
                    all_tools.append(tool_instance)

            except Exception as e:
                logger.error(f"Failed to load or reload tool(s) from {filename}: {e}", exc_info=True)

    logger.info(f"Live scan complete. Found {len(all_tools)} tools.")
    return all_tools
