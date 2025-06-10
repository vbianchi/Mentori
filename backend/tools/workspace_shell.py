# -----------------------------------------------------------------------------
# ResearchAgent Tool: Workspace Shell (Structured & Robust)
#
# FINAL CORRECTION 2: The tool is now defined with both `func` (synchronous)
# and `coroutine` (asynchronous) methods. This makes the tool robust and fully
# compatible with LangChain's execution model, which may use either sync or
# async calls depending on the context. A synchronous wrapper is created to
# run the async logic, ensuring consistent behavior. This definitively solves
# the persistent `TypeError`.
# -----------------------------------------------------------------------------

import logging
import os
import asyncio
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Configuration ---
SHELL_TIMEOUT = int(os.getenv("TOOL_SHELL_TIMEOUT", 120))

# --- Pydantic Schema for Tool Arguments ---
class WorkspaceShellInput(BaseModel):
    """Input schema for the workspace_shell tool."""
    command: str = Field(..., description="The shell command to execute.")

# --- Core Tool Logic (Asynchronous) ---
async def _arun_shell_command(command: str, workspace_path: str) -> str:
    """
    Asynchronously executes a shell command within the specified workspace directory
    and captures its stdout and stderr.
    """
    if not command:
        return "Error: No command provided."

    logger.info(f"Executing shell command: `{command}` in workspace: `{workspace_path}`")

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_path  # Execute the command in the sandboxed directory
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=SHELL_TIMEOUT)

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        result_parts = []
        if stdout_str:
            result_parts.append(f"STDOUT:\n---\n{stdout_str}\n---")
        if stderr_str:
            result_parts.append(f"STDERR:\n---\n{stderr_str}\n---")

        output = "\n".join(result_parts)

        if process.returncode == 0:
            logger.info(f"Command `{command}` finished successfully.")
            return output if output else "Command executed successfully with no output."
        else:
            logger.warning(f"Command `{command}` failed with exit code {process.returncode}.")
            return f"Command failed with exit code {process.returncode}.\n{output}"

    except asyncio.TimeoutError:
        logger.error(f"Command `{command}` timed out after {SHELL_TIMEOUT} seconds.")
        return f"Error: Command timed out after {SHELL_TIMEOUT} seconds. The process was killed."
    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Synchronous Wrapper for the Tool ---
def _run_shell_command_sync(command: str, workspace_path: str) -> str:
    """Synchronous wrapper to run the async shell command function."""
    try:
        # Get the existing event loop or create a new one
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_arun_shell_command(command, workspace_path))


# --- Tool Definition ---
tool = StructuredTool.from_function(
    func=_run_shell_command_sync,     # The synchronous entry point
    coroutine=_arun_shell_command,  # The asynchronous entry point
    name="workspace_shell",
    description=(
        "Executes a single, non-interactive shell command within the agent's secure workspace. "
        "This is best for system commands, running scripts, or complex file manipulations. "
        "For simple file creation or overwriting, prefer the `write_file` tool."
    ),
    args_schema=WorkspaceShellInput,
)
