# backend/tool_loader.py
import json
import logging
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# Define the path to the tool configuration file relative to this loader file.
# This assumes tool_loader.py is in backend/ and tool_config.json is also in backend/
CONFIG_FILE_PATH = Path(__file__).parent / "tool_config.json"

class ToolLoadingError(Exception):
    """Custom exception for errors during tool loading."""
    pass

def load_tools_from_config(
    config_path: Path = CONFIG_FILE_PATH,
    # task_id: Optional[str] = None # Reserved for future use if loader handles task-specific tools
) -> List[BaseTool]:
    """
    Loads and instantiates tools based on the provided JSON configuration file.

    Args:
        config_path: Path to the JSON configuration file for tools.
        # task_id: Optional task ID, currently unused but planned for task-specific tools.

    Returns:
        A list of successfully instantiated BaseTool objects.

    Raises:
        ToolLoadingError: If the configuration file cannot be read or parsed,
                          or if a critical error occurs during tool instantiation.
    """
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

    for config in tool_configs:
        tool_name = config.get("tool_name")
        is_enabled = config.get("enabled", True) # Default to True if not specified

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

        try:
            logger.debug(f"Attempting to import module: '{module_path_str}' for tool '{tool_name}'")
            module = importlib.import_module(module_path_str)
            logger.debug(f"Successfully imported module '{module_path_str}'.")

            logger.debug(f"Attempting to get class '{class_name_str}' from module '{module_path_str}' for tool '{tool_name}'")
            tool_class = getattr(module, class_name_str)
            logger.debug(f"Successfully retrieved class '{class_name_str}'.")

            # Here, we could potentially inspect tool_class.__init__ or use a marker
            # in the config to decide if task_id needs to be passed for task-specific tools.
            # For Phase 1, we are assuming general tools that don't need task_id at init.

            logger.debug(f"Attempting to instantiate tool '{tool_name}' with params: {init_params}")
            tool_instance = tool_class(**init_params)
            logger.info(f"Successfully instantiated tool: '{tool_name}' of type {type(tool_instance)}")

            # Optionally, we can update the tool's description if the config provides one
            # that should override the class's default description.
            # For now, we rely on the tool class defining its own description.
            # if "description_for_agent" in config:
            #     tool_instance.description = config["description_for_agent"]

            loaded_tools.append(tool_instance)

        except ImportError:
            logger.error(f"Failed to import module '{module_path_str}' for tool '{tool_name}'. Check PYTHONPATH and module path.", exc_info=True)
        except AttributeError:
            logger.error(f"Class '{class_name_str}' not found in module '{module_path_str}' for tool '{tool_name}'.", exc_info=True)
        except TypeError as e: # Catches errors like unexpected keyword arguments during instantiation
            logger.error(f"Error instantiating tool '{tool_name}' with class '{class_name_str}'. Check 'initialization_params' and class constructor. Error: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading tool '{tool_name}': {e}", exc_info=True)
            # Depending on policy, we might want to raise an error here or just skip the tool.
            # For now, we'll log and skip.

    logger.info(f"Tool loading process complete. Successfully loaded {len(loaded_tools)} tools.")
    return loaded_tools

if __name__ == "__main__":
    # Basic test for the loader
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Running tool_loader.py directly for testing...")
    # Create a dummy config file for testing if needed, or point to the real one
    # For this test, ensure backend/tool_config.json exists and is configured for at least one tool.
    
    # Ensure the dummy tool_config.json is in the same directory as this script for this test
    # Or adjust path to point to backend/tool_config.json
    test_config_path = Path(__file__).parent / "tool_config.json" # Assumes it's next to this file for test
    
    if not test_config_path.exists():
        logger.warning(f"Test config {test_config_path} not found. Creating a dummy one for testing.")
        dummy_config_content = [
            {
                "tool_name": "tavily_search_api_test_from_loader", # Different name to avoid conflict if real one is loaded
                "module_path": "backend.tools.tavily_search_tool", # Adjust if your structure is different
                "class_name": "TavilyAPISearchTool",
                "description_for_agent": "Test Tavily Search (loaded dynamically).",
                "input_schema_description": "Query string.",
                "output_description": "Search results.",
                "initialization_params": {}, 
                "enabled": True 
            }
        ]
        try:
            with open(test_config_path, 'w') as f_test:
                json.dump(dummy_config_content, f_test, indent=2)
            logger.info(f"Dummy test config created at {test_config_path}")
        except Exception as e:
            logger.error(f"Failed to create dummy test config: {e}")
            test_config_path = CONFIG_FILE_PATH # Fallback to actual config if dummy creation fails

    try:
        # Test with the actual config file path expected by the application
        # This requires that your PYTHONPATH is set up correctly if running this file directly,
        # or that the backend.tools modules are discoverable.
        # For a more isolated test, you might mock imports or use simpler dummy tool classes.
        # tools = load_tools_from_config(config_path=CONFIG_FILE_PATH)
        
        # Using the test_config_path for this direct run:
        tools = load_tools_from_config(config_path=test_config_path)
        
        if tools:
            logger.info(f"--- Dynamically Loaded Tools ({len(tools)}) ---")
            for tool in tools:
                logger.info(f"Tool Name: {tool.name}")
                logger.info(f"  Description: {tool.description}")
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    logger.info(f"  Args Schema: {tool.args_schema.schema_json(indent=2)}")
                logger.info("-" * 20)
        else:
            logger.info("No tools were loaded by the test.")
            
    except ToolLoadingError as e:
        logger.error(f"ToolLoadingError during test: {e}")
    except Exception as e:
        logger.error(f"General error during tool_loader.py test: {e}", exc_info=True)

    # Clean up dummy config if created
    if test_config_path.name != CONFIG_FILE_PATH.name and "dummy_config_content" in locals():
        try:
            # test_config_path.unlink() # Commented out to allow inspection of the dummy file after test run
            # logger.info(f"Dummy test config {test_config_path} removed.")
            pass
        except Exception as e_del:
            logger.warning(f"Could not remove dummy test config {test_config_path}: {e_del}")

