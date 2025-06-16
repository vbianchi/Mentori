# -----------------------------------------------------------------------------
# ResearchAgent Tool: Virtual Environment Manager
#
# This file provides a tool for creating isolated Python virtual environments
# for each task. This is a core component of Phase 11: The Secure,
# Extensible Environment.
#
# Key Features:
# - Idempotent: The tool first checks if a `.venv` directory already exists
#   within the task's workspace. If it does, the tool reports success without
#   trying to create a new one, preventing errors.
# - Sandboxed: The operation is strictly confined to the task's unique
#   workspace directory, ensuring environments are isolated.
# - Asynchronous Execution: Uses `asyncio` to run the `uv venv` command in a
#   non-blocking way, capturing all output and errors for robust reporting.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
from langchain_core.tools import StructuredTool
from .file_system import _resolve_path # Re-using the security helper

logger = logging.getLogger(__name__)

# --- Asynchronous Sub-function for Execution ---
async def _execute_venv_creation(command: list[str], cwd: str) -> str:
    """Helper function to run the venv creation command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd, # Execute the command in the specified workspace directory
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120) # 2-minute timeout
    
    stdout_str = stdout.decode(errors='ignore').strip()
    stderr_str = stderr.decode(errors='ignore').strip()

    if process.returncode == 0:
        logger.info(f"Virtual environment created successfully in '{cwd}'.")
        return f"Successfully created virtual environment.\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"
    else:
        logger.error(f"Venv creation failed in '{cwd}' with exit code {process.returncode}. Stderr: {stderr_str}")
        return f"Error: Command failed with exit code {process.returncode}\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"

# --- Core Tool Logic (Synchronous Wrapper) ---
def create_virtual_environment(workspace_path: str) -> str:
    """
    Creates a new Python virtual environment (`.venv`) in the current task's
    workspace using the `uv` command. If an environment already exists,
    it reports success without creating a new one.
    """
    try:
        # Resolve the absolute path for the workspace securely
        abs_workspace_path = _resolve_path(workspace_path, "")
        venv_path = os.path.join(abs_workspace_path, ".venv")

        # --- Idempotency Check ---
        if os.path.isdir(venv_path):
            logger.info(f"Virtual environment already exists at '{venv_path}'. No action taken.")
            return "Success: A virtual environment already exists in this workspace."

        command = ["uv", "venv"]
        logger.info(f"Creating new virtual environment in '{abs_workspace_path}'")
        
        # Use asyncio.run() to execute the async helper function from a sync context
        return asyncio.run(_execute_venv_creation(command, cwd=abs_workspace_path))
    except Exception as e:
        logger.error(f"An unexpected error occurred while creating virtual environment: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
# This tool is sandboxed and will receive the workspace_path automatically.
tool = StructuredTool.from_function(
    func=create_virtual_environment,
    name="create_virtual_environment",
    description="Creates a dedicated Python virtual environment (`.venv`) for the current task. This is a necessary first step before installing any packages for a project. If an environment already exists, it will report success."
)
