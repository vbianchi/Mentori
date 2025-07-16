# -----------------------------------------------------------------------------
# Mentor::i Tools Package Initializer (Phase 14.2: Tool Forge Removed)
#
# This version fixes a NameError caused by a syntax error in the previous
# version.
#
# Key Architectural Changes:
# 1. Syntax Correction: Removed the invalid `[cite: 462]` text that was
#    causing a `NameError` during module loading.
# -----------------------------------------------------------------------------

import os
import importlib
import logging
import json
from langchain_core.tools import BaseTool
import sys
from typing import Type

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
    logger.info(f"Dynamically scanning for Python tools in: {tools_dir}")

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
                
                # MODIFIED: Corrected line that was causing the NameError
                _MODULE_CACHE[module_name] = module
                
                if hasattr(module, 'tools') and isinstance(getattr(module, 'tools'), list):
                    tool_list = getattr(module, 'tools')
                    for tool_instance in tool_list:
                        if isinstance(tool_instance, BaseTool):
                            logger.info(f"Discovered engine tool: '{tool_instance.name}' from {filename}")
                            all_tools.append(tool_instance)
                
                elif hasattr(module, 'tool') and isinstance(getattr(module, 'tool'), BaseTool):
                    tool_instance = getattr(module, 'tool')
                    logger.info(f"Discovered engine tool: '{tool_instance.name}' from {filename}")
                    all_tools.append(tool_instance)

            except Exception as e:
                logger.error(f"Failed to load or reload tool(s) from {filename}: {e}", exc_info=True)

    logger.info(f"Live scan complete. Found {len(all_tools)} total tools.")
    return all_tools
