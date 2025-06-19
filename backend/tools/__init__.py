# -----------------------------------------------------------------------------
# ResearchAgent Tools Package Initializer (Phase 14.2: Blueprint Loading)
#
# This version updates the tool loader to be aware of "Blueprint Tools."
#
# Key Architectural Changes:
# 1. Scans `tool_blueprints` Directory: The `get_available_tools` function now
#    has a second loop that scans the `backend/tool_blueprints` directory
#    for any `.json` files.
# 2. `BlueprintTool` Class: A new placeholder class is defined that inherits
#    from LangChain's `BaseTool`. Its only purpose is to act as a container
#    so that JSON blueprints can be represented in the same way as regular
#    Python tools, with a `name` and `description`.
# 3. Unified Tool List: The function now returns a single list containing
#    both the dynamically loaded Python "Engine Tools" and the newly
#    loaded JSON "Blueprint Tools", making all capabilities discoverable by
#    the agent's planner.
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

# --- Placeholder Class for Blueprint Tools ---
class BlueprintTool(BaseTool):
    """A placeholder tool representing a multi-step JSON blueprint."""
    plan: dict
    
    # Blueprints are not executed directly, so this method should not be called.
    def _run(self, *args, **kwargs):
        raise NotImplementedError("BlueprintTools are not meant to be run directly.")
    
    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("BlueprintTools are not meant to be run directly.")

def get_available_tools():
    """
    Scans the 'tools' and 'tool_blueprints' directories, imports or loads all
    modules/files, and returns a fresh list of all discovered tool objects.
    """
    all_tools = []
    
    # --- 1. Load Python "Engine" Tools ---
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

    # --- 2. Load JSON "Blueprint" Tools ---
    blueprints_dir = os.path.join(tools_dir, '..', 'tool_blueprints')
    logger.info(f"Dynamically scanning for JSON blueprints in: {blueprints_dir}")
    
    if os.path.isdir(blueprints_dir):
        for filename in os.listdir(blueprints_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(blueprints_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        blueprint_data = json.load(f)
                    
                    if blueprint_data.get("type") == "blueprint":
                        blueprint_tool = BlueprintTool(
                            name=blueprint_data.get("name"),
                            description=blueprint_data.get("description"),
                            plan=blueprint_data.get("plan", {})
                        )
                        logger.info(f"Discovered blueprint tool: '{blueprint_tool.name}' from {filename}")
                        all_tools.append(blueprint_tool)

                except Exception as e:
                    logger.error(f"Failed to load blueprint from {filename}: {e}", exc_info=True)


    logger.info(f"Live scan complete. Found {len(all_tools)} total tools.")
    return all_tools
