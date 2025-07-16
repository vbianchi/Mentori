# -----------------------------------------------------------------------------
# Mentor::i Tool: Secure, Venv-Aware Package Manager
#
# This version completes the logic for Phase 11 by making the package
# installer aware of the per-task virtual environments.
#
# Key Features:
# - Venv-Aware: The `--system` flag has been removed. The tool now executes
#   the `uv pip install` command with the `cwd` (current working directory)
#   set to the task's specific workspace. `uv` automatically detects and
#   installs packages into the `.venv` found in that directory.
# - Sandboxed Installation: This ensures that packages installed for Task A
#   are completely isolated from Task B, preventing dependency conflicts.
# - Parameter Update: The function signature is updated to accept the
#   `workspace_path`, which is passed down to the execution helper.
# -----------------------------------------------------------------------------

import asyncio
import logging
import os
from packaging.requirements import Requirement, InvalidRequirement
from langchain_core.tools import StructuredTool
from .file_system import _resolve_path

logger = logging.getLogger(__name__)

# --- Asynchronous Sub-function for Execution ---
async def _execute_install(command: list[str], cwd: str) -> str:
    """Helper function to run the installation command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd, # Execute the command in the specified workspace directory
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
    
    stdout_str = stdout.decode(errors='ignore').strip()
    stderr_str = stderr.decode(errors='ignore').strip()

    if process.returncode == 0:
        logger.info(f"Package installation into '{cwd}' finished successfully.")
        return f"Successfully installed package into the task's virtual environment.\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"
    else:
        logger.error(f"Package installation failed in '{cwd}' with exit code {process.returncode}. Stderr: {stderr_str}")
        return f"Error: Command failed with exit code {process.returncode}\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"

# --- Core Tool Logic (Synchronous Wrapper) ---
def pip_install(package: str, workspace_path: str) -> str:
    """
    Installs a Python package into the task's dedicated virtual environment
    using the uv package manager. The input must be a valid package name and
    optional version specifier (e.g., 'pandas', 'numpy==1.2.3').
    """
    if not package or not isinstance(package, str):
        return "Error: Invalid input. A package name must be provided as a string."
    
    try:
        # --- Security Validation ---
        requirement = Requirement(package)
        safe_package_str = str(requirement)
    except InvalidRequirement:
        logger.error(f"Invalid package specifier provided: '{package}'. Aborting installation.")
        return f"Error: Invalid package specifier '{package}'. Please provide a valid package name and optional version (e.g., 'pandas' or 'pandas==1.2.3')."
    
    try:
        abs_workspace_path = _resolve_path(workspace_path, "")
        
        # The command no longer needs the `--system` flag.
        command = ["uv", "pip", "install", safe_package_str]
        
        logger.info(f"Executing venv-aware package installation in '{abs_workspace_path}': `{' '.join(command)}`")
        # Pass the workspace path as the current working directory for the subprocess.
        return asyncio.run(_execute_install(command, cwd=abs_workspace_path))
    except Exception as e:
        logger.error(f"An unexpected error occurred during package installation: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
# The tool now requires workspace_path, which will be passed automatically for sandboxed tools.
tool = StructuredTool.from_function(
    func=pip_install,
    name="pip_install",
    description="Installs a single Python package from PyPI into the current task's dedicated virtual environment. Use this before running any script that has external dependencies. The input must be a string containing a valid package name and an optional version specifier (e.g., 'pandas', 'numpy>=1.2.3')."
)
