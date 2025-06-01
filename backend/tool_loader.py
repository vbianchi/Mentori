# backend/tool_loader.py
import json
import logging
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import os # <<< Added for os.makedirs
import re # <<< Added for re.sub

from langchain_core.tools import BaseTool
# No longer importing get_task_workspace_path from standard_tools

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = Path(__file__).parent / "tool_config.json"
RUNTIME_TASK_WORKSPACE_PLACEHOLDER = "__RUNTIME_TASK_WORKSPACE__"

# <<< --- MOVED UTILITIES HERE --- >>>
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent # tool_loader.py is in backend/
    BASE_WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
    os.makedirs(BASE_WORKSPACE_ROOT, exist_ok=True)
    logger.info(f"Base workspace directory ensured at: {BASE_WORKSPACE_ROOT} (from tool_loader.py)")
except OSError as e:
    logger.error(f"Could not create base workspace directory (from tool_loader.py): {e}", exc_info=True)
    raise OSError(f"Required base workspace directory {BASE_WORKSPACE_ROOT} could not be created.") from e
except Exception as e:
    logger.error(f"Error resolving project/workspace path (from tool_loader.py): {e}", exc_info=True)
    raise

def get_task_workspace_path(task_id: Optional[str], create_if_not_exists: bool = True) -> Path:
    logger.debug(f"get_task_workspace_path (in tool_loader.py) called for task_id: '{task_id}', create_if_not_exists: {create_if_not_exists}")
    if not task_id or not isinstance(task_id, str):
        msg = f"Invalid or missing task_id ('{task_id}') provided for workspace path."
        logger.error(msg)
        raise ValueError(msg)
    sane_task_id = re.sub(r'[^\w\-.]', '_', task_id)
    if not sane_task_id:
        msg = f"Task_id '{task_id}' resulted in an empty sanitized ID. Cannot create workspace."
        logger.error(msg)
        raise ValueError(msg)
    if ".." in sane_task_id or "/" in sane_task_id or "\\" in sane_task_id:
        msg = f"Invalid characters detected in sanitized task_id: {sane_task_id} (original: {task_id}). Denying workspace path creation."
        logger.error(msg)
        raise ValueError(msg)
    task_workspace = BASE_WORKSPACE_ROOT / sane_task_id
    if create_if_not_exists:
        try:
            if not task_workspace.exists():
                os.makedirs(task_workspace, exist_ok=True)
                logger.info(f"Created task workspace directory: {task_workspace} (from tool_loader.py)")
            else:
                logger.debug(f"Task workspace directory already exists: {task_workspace} (from tool_loader.py)")
        except OSError as e:
            logger.error(f"Could not create task workspace directory at {task_workspace}: {e}", exc_info=True)
            raise OSError(f"Could not create task workspace {task_workspace}: {e}") from e
    elif not task_workspace.exists():
        logger.warning(f"Task workspace directory does not exist and create_if_not_exists is False: {task_workspace} (from tool_loader.py)")
    return task_workspace
# <<< --- END MOVED UTILITIES --- >>>

class ToolLoadingError(Exception):
    """Custom exception for errors during tool loading."""
    pass

def load_tools_from_config(
    config_path: Path = CONFIG_FILE_PATH,
    current_task_id: Optional[str] = None
) -> List[BaseTool]:
    loaded_tools: List[BaseTool] = []
    tool_configs: List[Dict[str, Any]] = []

    logger.info(f"Attempting to load tool configurations from: {config_path}")
    if not config_path.exists():
        logger.error(f"Tool configuration file not found at {config_path}.")
        raise ToolLoadingError(f"Tool configuration file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            tool_configs = json.load(f)
        if not isinstance(tool_configs, list):
            logger.error(f"Tool configuration file {config_path} does not contain a list of tool objects.")
            raise ToolLoadingError(f"Invalid format: {config_path} must contain a JSON list.")
        logger.info(f"Successfully read and parsed tool configurations from {config_path}. Found {len(tool_configs)} tool definition(s).")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from tool configuration file {config_path}: {e}", exc_info=True)
        raise ToolLoadingError(f"Invalid JSON in {config_path}: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error reading tool configuration file {config_path}: {e}", exc_info=True)
        raise ToolLoadingError(f"Could not read {config_path}: {e}") from e

    task_workspace_path_for_tools: Optional[Path] = None # Renamed for clarity within this function
    if current_task_id:
        try:
            # Uses the get_task_workspace_path now defined in this file
            task_workspace_path_for_tools = get_task_workspace_path(current_task_id, create_if_not_exists=True)
            logger.info(f"Resolved task workspace path for task '{current_task_id}': {task_workspace_path_for_tools}")
        except ValueError as ve:
            logger.error(f"Invalid task_id '{current_task_id}' for resolving workspace path: {ve}. Task-specific tools may fail to load.")
        except OSError as oe:
            logger.error(f"OSError resolving or creating workspace path for task '{current_task_id}': {oe}. Task-specific tools may fail to load.")
        except Exception as e:
            logger.error(f"Unexpected error resolving workspace for task '{current_task_id}': {e}. Task-specific tools may fail to load.", exc_info=True)

    for config in tool_configs:
        tool_name = config.get("tool_name")
        is_enabled = config.get("enabled", True)

        if not tool_name:
            logger.warning(f"Skipping tool configuration due to missing 'tool_name': {config}")
            continue

        if not is_enabled:
            logger.info(f"Tool '{tool_name}' is disabled in the configuration. Skipping.")
            continue

        logger.info(f"Processing configuration for tool: '{tool_name}'")
        module_path_str = config.get("module_path")
        class_name_str = config.get("class_name")
        init_params = config.get("initialization_params", {})

        if not module_path_str or not class_name_str:
            logger.error(f"Tool '{tool_name}' configuration is missing 'module_path' or 'class_name'. Skipping.")
            continue

        processed_init_params = {}
        can_instantiate = True
        for key, value in init_params.items():
            if value == RUNTIME_TASK_WORKSPACE_PLACEHOLDER:
                if task_workspace_path_for_tools:
                    processed_init_params[key] = task_workspace_path_for_tools
                    logger.debug(f"For tool '{tool_name}', injecting runtime task_workspace: {task_workspace_path_for_tools} for param '{key}'.")
                else:
                    logger.error(f"Tool '{tool_name}' requires runtime task_workspace for param '{key}', but current_task_id was not provided or workspace path resolution failed. Skipping tool.")
                    can_instantiate = False
                    break
            else:
                processed_init_params[key] = value

        if not can_instantiate:
            continue

        try:
            logger.debug(f"Attempting to import module: '{module_path_str}' for tool '{tool_name}'")
            module = importlib.import_module(module_path_str)
            logger.debug(f"Successfully imported module '{module_path_str}'.")

            logger.debug(f"Attempting to get class '{class_name_str}' from module '{module_path_str}' for tool '{tool_name}'")
            tool_class = getattr(module, class_name_str)
            logger.debug(f"Successfully retrieved class '{class_name_str}'.")

            logger.debug(f"Attempting to instantiate tool '{tool_name}' with processed params: {processed_init_params}")
            tool_instance = tool_class(**processed_init_params)
            logger.info(f"Successfully instantiated tool: '{tool_name}' of type {type(tool_instance)}")

            loaded_tools.append(tool_instance)

        except ImportError:
            logger.error(f"Failed to import module '{module_path_str}' for tool '{tool_name}'. Check PYTHONPATH and module path.", exc_info=True)
        except AttributeError:
            logger.error(f"Class '{class_name_str}' not found in module '{module_path_str}' for tool '{tool_name}'.", exc_info=True)
        except TypeError as e:
            logger.error(f"Error instantiating tool '{tool_name}' with class '{class_name_str}'. Check 'initialization_params' and class constructor. Error: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading tool '{tool_name}': {e}", exc_info=True)

    logger.info(f"Tool loading process complete. Successfully loaded {len(loaded_tools)} tools.")
    return loaded_tools

if __name__ == "__main__":
    # ... (test harness remains the same, but will now use the local get_task_workspace_path) ...
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Running tool_loader.py directly for testing...")
    logger.info("\n--- Test 1: Loading tools without current_task_id ---")
    try:
        tools_no_task = load_tools_from_config()
        for tool in tools_no_task: logger.info(f"Loaded (no task_id): {tool.name}")
        if not any(t.name in ["read_file", "write_file", "workspace_shell"] for t in tools_no_task): logger.info("Correctly did not load task-specific tools when no task_id provided.")
        else: logger.warning("Task-specific tools were loaded even without a task_id, check placeholder logic.")
    except ToolLoadingError as e: logger.error(f"ToolLoadingError during test (no task_id): {e}")
    except Exception as e: logger.error(f"General error during tool_loader.py test (no task_id): {e}", exc_info=True)

    logger.info("\n--- Test 2: Loading tools WITH current_task_id ---")
    dummy_task_id_for_test = "test_task_for_loader_123"
    try:
        tools_with_task = load_tools_from_config(current_task_id=dummy_task_id_for_test)
        for tool in tools_with_task:
            logger.info(f"Loaded (with task_id '{dummy_task_id_for_test}'): {tool.name}")
            if hasattr(tool, 'task_workspace'): logger.info(f"  > {tool.name} has task_workspace: {tool.task_workspace}")
        expected_task_tools = {"read_file", "write_file", "workspace_shell"}
        loaded_task_tool_names = {t.name for t in tools_with_task if hasattr(t, 'task_workspace')}
        if expected_task_tools.issubset(loaded_task_tool_names): logger.info(f"Successfully loaded task-specific tools for task_id '{dummy_task_id_for_test}'.")
        else: logger.warning(f"Missing some task-specific tools for task_id '{dummy_task_id_for_test}'. Expected: {expected_task_tools}, Got: {loaded_task_tool_names}")
    except ToolLoadingError as e: logger.error(f"ToolLoadingError during test (with task_id): {e}")
    except Exception as e: logger.error(f"General error during tool_loader.py test (with task_id): {e}", exc_info=True)

