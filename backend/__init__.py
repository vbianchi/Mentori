# -----------------------------------------------------------------------------
# ResearchAgent Tools Package Initializer (Phase 17 - Startup FIX)
#
# This version temporarily removes the ToolExecutor instantiation to bypass a
# persistent library import error and allow the server to start.
#
# Key Architectural Changes:
# 1. ToolExecutor Removed: The import and instantiation of ToolExecutor have
#    been commented out. The agent does not currently use this, as the
#    worker node is a placeholder, so this is safe to do for debugging the
#    UI flow. This will be restored when we implement the real tool calls.
# -----------------------------------------------------------------------------

import os
import importlib
import logging
import json
from langchain_core.tools import BaseTool
import sys
from typing import Type
# from langgraph.prebuilt.tool_executor import ToolExecutor # Temporarily removed

logger = logging.getLogger(__name__)

# --- Module Cache for Live Reloading ---
_MODULE_CACHE = {}


def get_available_tools():
    """
    Scans the 'tools' directory, imports all modules, and returns a fresh
    list of all discovered Python-based tool objects.
    """
    all_tools = []
    
    # --- Load Python "Engine" Tools ---
    tools_dir = os.path.dirname(__file__)
    logger.debug(f"Dynamically scanning for Python tools in: {tools_dir}")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"backend.tools.{filename[:-3]}"
            try:
                if module_name in _MODULE_CACHE:
                    module = importlib.reload(_MODULE_CACHE[module_name])
                    logger.debug(f"Reloaded module: {module_name}")
                else:
                    module = importlib.import_module(module_name)
                    logger.debug(f"Imported new module: {module_name}")
                
                _MODULE_CACHE[module_name] = module
                
                if hasattr(module, 'tools') and isinstance(getattr(module, 'tools'), list):
                    tool_list = getattr(module, 'tools')
                    for tool_instance in tool_list:
                        if isinstance(tool_instance, BaseTool):
                            logger.debug(f"Discovered engine tool: '{tool_instance.name}' from {filename}")
                            all_tools.append(tool_instance)
                
                elif hasattr(module, 'tool') and isinstance(getattr(module, 'tool'), BaseTool):
                    tool_instance = getattr(module, 'tool')
                    logger.debug(f"Discovered engine tool: '{tool_instance.name}' from {filename}")
                    all_tools.append(tool_instance)

            except Exception as e:
                logger.error(f"Failed to load or reload tool(s) from {filename}: {e}", exc_info=True)

    logger.info(f"Live scan complete. Found {len(all_tools)} total tools.")
    return all_tools

# --- tool_executor is temporarily removed to solve startup issues ---
# tool_executor = ToolExecutor(get_available_tools())
