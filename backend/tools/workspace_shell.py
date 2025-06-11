# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed Workspace Shell
#
# This file defines a robust, sandboxed shell tool for the agent.
# It uses a Pydantic schema to clearly define its expected arguments.
# -----------------------------------------------------------------------------

import os
import logging
import asyncio
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Pydantic Schema for Robust Argument Parsing ---
class ShellInput(BaseModel):
    command: str = Field(description="The shell command to execute.")

# --- Security Helper ---
def _resolve_path(workspace_path: str) -> str:
    abs_workspace_path = os.path.abspath(workspace_path)
    if not abs_workspace_path.startswith(os.path.abspath("/app/workspace")):
        raise PermissionError("Attempted to access a directory outside of the main workspace.")
    return abs_workspace_path

# --- Core Tool Logic ---
async def run_shell_command(command: str, workspace_path: str) -> str:
    """Asynchronously executes a shell command in the secure workspace."""
    if not command:
        return "Error: No command provided."
    
    try:
        # Securely resolve the workspace path to use as the Current Working Directory (CWD)
        cwd = _resolve_path(workspace_path)
        logger.info(f"Executing shell command in '{cwd}': `{command}`")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd # Execute the command in the sandboxed directory
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        
        stdout_str = stdout.decode(errors='ignore').strip()
        stderr_str = stderr.decode(errors='ignore').strip()

        if process.returncode == 0:
            logger.info(f"Command finished successfully. Output: {stdout_str[:100]}")
            return stdout_str if stdout_str else "Command executed successfully with no output."
        else:
            logger.error(f"Command failed with exit code {process.returncode}. Stderr: {stderr_str}")
            return f"Error: Command failed with exit code {process.returncode}\n---STDERR---\n{stderr_str}"

    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
tool = StructuredTool.from_function(
    func=run_shell_command,
    name="workspace_shell",
    description="Executes a single, non-interactive shell command within the current task's secure workspace. Use it for tasks like running scripts, managing files, and version control.",
    args_schema=ShellInput
)
