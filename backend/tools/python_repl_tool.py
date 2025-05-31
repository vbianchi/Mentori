# backend/tools/python_repl_tool.py
import logging
import asyncio
from typing import Optional, Type

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field
from langchain_experimental.utilities import PythonREPL # Assuming this is the one used

logger = logging.getLogger(__name__)

# Attempt to initialize the PythonREPL utility once
try:
    python_repl_utility_instance = PythonREPL()
    logger.info("PythonREPL utility instance created successfully for PythonREPLTool.")
except ImportError:
    logger.warning("Could not import PythonREPL from langchain_experimental.utilities. Python_REPL tool will not be available.")
    python_repl_utility_instance = None
except Exception as e:
    logger.error(f"Error initializing PythonREPL utility: {e}", exc_info=True)
    python_repl_utility_instance = None


class PythonREPLInput(BaseModel):
    command: str = Field(description="A single, simple Python expression or a very short, self-contained snippet of Python code to execute.")

class PythonREPLTool(BaseTool):
    name: str = "Python_REPL"
    description: str = (
        "Executes a single, simple Python expression or a very short, self-contained snippet of Python code. "
        "Input MUST be valid Python code that can be evaluated as a single block. "
        "Use this for straightforward operations like basic arithmetic (e.g., '2 + 2', '10 / 5 * 2'), "
        "simple string manipulations, or quick checks. "
        "**DO NOT use this for defining multi-line functions or classes, complex scripts, file I/O, or installing packages.** "
        "For writing and then running Python scripts, use the `write_file` tool followed by the `workspace_shell` "
        "tool (e.g., 'python your_script_name.py'). "
        "Output will be the result of the expression or `print()` statements. "
        "**Security Note:** This executes code directly in the backend environment. Be extremely cautious."
    )
    args_schema: Type[BaseModel] = PythonREPLInput

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        logger.info(f"Tool '{self.name}' executing command: '{command}'")
        if python_repl_utility_instance is None:
            logger.error(f"Tool '{self.name}': PythonREPL utility not available.")
            raise ToolException("PythonREPL utility is not available. Check server logs for import/init errors.")
        if not isinstance(command, str) or not command.strip():
            logger.error(f"Tool '{self.name}': Received invalid input. Expected a non-empty command string.")
            raise ToolException("Invalid input. Expected a non-empty Python command string.")
        try:
            # PythonREPL.run is synchronous
            result = python_repl_utility_instance.run(command)
            logger.info(f"Tool '{self.name}' command executed. Output length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Tool '{self.name}': Error executing command '{command}': {e}", exc_info=True)
            # Return the error message as a string, as REPL often does
            return f"Error in Python REPL: {type(e).__name__}: {str(e)}"

    async def _arun(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        logger.info(f"Tool '{self.name}' asynchronously executing command: '{command}'")
        if python_repl_utility_instance is None:
            logger.error(f"Tool '{self.name}': PythonREPL utility not available for async execution.")
            raise ToolException("PythonREPL utility is not available. Check server logs for import/init errors.")
        if not isinstance(command, str) or not command.strip():
            logger.error(f"Tool '{self.name}': Received invalid input for async. Expected a non-empty command string.")
            raise ToolException("Invalid input for async. Expected a non-empty Python command string.")
        try:
            # Run the synchronous PythonREPL.run in a thread pool
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,  # Uses the default thread pool executor
                python_repl_utility_instance.run,
                command
            )
            logger.info(f"Tool '{self.name}' async command executed. Output length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Tool '{self.name}': Error executing async command '{command}': {e}", exc_info=True)
            return f"Error in Python REPL (async): {type(e).__name__}: {str(e)}"

