# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed Workspace Shell (Pickle Fix)
#
# CORRECTION: This is the definitive fix for the "cannot pickle 'coroutine'
# object" error.
#
# - The `run_shell_command` function is now a regular synchronous `def`.
# - Inside the function, `asyncio.run()` is used to execute the async
#   subprocess logic.
#
# This change encapsulates the tool's asynchronicity, presenting a simple,
# synchronous interface to LangGraph. This prevents coroutine objects from
# leaking into the graph's state, resolving the pickling error.
# -----------------------------------------------------------------------------

import os
import logging
import asyncio
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# --- Security Helper ---
def _resolve_path(workspace_path: str) -> str:
    abs_workspace_path = os.path.abspath(workspace_path)
    if not abs_workspace_path.startswith(os.path.abspath("/app/workspace")):
        raise PermissionError("Attempted to access a directory outside of the main workspace.")
    return abs_workspace_path

# --- Asynchronous Sub-function ---
# We keep the actual process execution async.
async def _execute_subprocess(command: str, cwd: str) -> str:
    """Helper function to run the command asynchronously."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd
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

# --- Core Tool Logic (Now Synchronous) ---
def run_shell_command(command: str, workspace_path: str) -> str:
    """
    Synchronously executes a shell command in the secure workspace by running
    its own async event loop.
    """
    if not command:
        return "Error: No command provided."
    
    try:
        cwd = _resolve_path(workspace_path)
        logger.info(f"Executing shell command in '{cwd}': `{command}`")
        # Use asyncio.run() to execute the async helper function
        return asyncio.run(_execute_subprocess(command, cwd))
    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
# No changes needed here. It now correctly points to a synchronous function.
tool = StructuredTool.from_function(
    func=run_shell_command,
    name="workspace_shell",
    description="Executes a single, non-interactive shell command within the current task's secure workspace. Use it for tasks like running scripts, managing files, and version control."
)
