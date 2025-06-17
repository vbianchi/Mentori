# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed Workspace Shell (Venv-Aware FIX)
#
# This version fixes a critical bug where the shell would use the global
# Python interpreter instead of the task's dedicated virtual environment,
# causing "ModuleNotFoundError" for installed packages.
#
# 1. Venv-Aware Command Execution: The `run_shell_command` function now
#    inspects the command it receives.
# 2. Automatic Path Correction: If the command starts with "python ", the
#    tool automatically prepends the full path to the Python executable
#    within the task's own `.venv` directory (e.g.,
#    `/app/workspace/task_123/.venv/bin/python`).
# 3. Seamless Integration: This ensures that any Python scripts executed by
#    the agent run with the correct interpreter and have access to all the
#    packages installed via the `pip_install` tool, resolving the bug.
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
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300) # Increased timeout to 5 mins for long installs
    
    stdout_str = stdout.decode(errors='ignore').strip()
    stderr_str = stderr.decode(errors='ignore').strip()

    if process.returncode == 0:
        logger.info(f"Command finished successfully. Output: {stdout_str[:200]}")
        return stdout_str if stdout_str else "Command executed successfully with no output."
    else:
        logger.error(f"Command failed with exit code {process.returncode}. Stderr: {stderr_str}")
        return f"Error: Command failed with exit code {process.returncode}\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"

# --- Core Tool Logic (Synchronous Wrapper) ---
def run_shell_command(command: str, workspace_path: str) -> str:
    """
    Synchronously executes a shell command in the secure, venv-aware workspace.
    If the command starts with 'python', it automatically uses the virtual
    environment's Python interpreter.
    """
    if not command:
        return "Error: No command provided."
    
    try:
        cwd = _resolve_path(workspace_path)
        
        # --- THIS IS THE FIX ---
        # Check if the command is a python command
        if command.strip().startswith("python "):
            venv_python_path = os.path.join(cwd, ".venv", "bin", "python")
            if os.path.exists(venv_python_path):
                # Replace "python" with the full path to the venv's python
                modified_command = f"{venv_python_path} {command.strip()[len('python '):]}"
                logger.info(f"Executing venv-aware python command in '{cwd}': `{modified_command}`")
                command = modified_command
            else:
                logger.warning(f"Virtual environment python not found at '{venv_python_path}'. Falling back to system python.")

        else:
            logger.info(f"Executing shell command in '{cwd}': `{command}`")

        # Use asyncio.run() to execute the async helper function
        return asyncio.run(_execute_subprocess(command, cwd))
    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
# The description is updated to reflect the new venv-aware capability.
tool = StructuredTool.from_function(
    func=run_shell_command,
    name="workspace_shell",
    description="Executes a single, non-interactive shell command within the current task's secure workspace. It is venv-aware: if the command starts with 'python', it automatically uses the interpreter from the task's dedicated virtual environment, ensuring access to installed packages."
)
