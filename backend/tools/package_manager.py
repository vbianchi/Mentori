# -----------------------------------------------------------------------------
# ResearchAgent Tool: Secure Package Manager (pip_install)
#
# This version includes a critical fix to allow installation within our
# Docker environment.
#
# FIX: The `uv pip install` command requires the `--system` flag to allow it
#      to install packages into the global Python environment inside the
#      Docker container. Without this flag, it defaults to looking for a
#      virtual environment, which doesn't exist yet, causing the installation
#      to fail.
# -----------------------------------------------------------------------------

import asyncio
import logging
from packaging.requirements import Requirement, InvalidRequirement
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# --- Asynchronous Sub-function for Execution ---
async def _execute_install(command: list[str]) -> str:
    """Helper function to run the installation command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300) # 5-minute timeout for installs
    
    stdout_str = stdout.decode(errors='ignore').strip()
    stderr_str = stderr.decode(errors='ignore').strip()

    if process.returncode == 0:
        logger.info(f"Package installation finished successfully. Output: {stdout_str[:200]}")
        # Sometimes pip/uv prints success messages to stderr, so we include both
        return f"Successfully installed package.\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"
    else:
        logger.error(f"Package installation failed with exit code {process.returncode}. Stderr: {stderr_str}")
        return f"Error: Command failed with exit code {process.returncode}\n---STDOUT---\n{stdout_str}\n---STDERR---\n{stderr_str}"

# --- Core Tool Logic (Synchronous Wrapper) ---
def pip_install(package: str) -> str:
    """
    Installs a Python package into the environment using the uv package manager.
    The input must be a valid package name and optional version specifier
    (e.g., 'pandas', 'numpy==1.2.3', 'scikit-learn>=1.0').
    """
    if not package or not isinstance(package, str):
        return "Error: Invalid input. A package name must be provided as a string."
    
    # --- Security Validation ---
    try:
        requirement = Requirement(package)
        safe_package_str = str(requirement)
    except InvalidRequirement:
        logger.error(f"Invalid package specifier provided: '{package}'. Aborting installation.")
        return f"Error: Invalid package specifier '{package}'. Please provide a valid package name and optional version (e.g., 'pandas' or 'pandas==1.2.3')."
    
    try:
        # --- THIS IS THE FIX ---
        # We add the `--system` flag to explicitly authorize installation
        # into the main Docker environment's Python.
        command = ["uv", "pip", "install", "--system", safe_package_str]
        
        logger.info(f"Executing secure package installation: `{' '.join(command)}`")
        return asyncio.run(_execute_install(command))
    except Exception as e:
        logger.error(f"An unexpected error occurred during package installation: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
tool = StructuredTool.from_function(
    func=pip_install,
    name="pip_install",
    description="Installs a single Python package from PyPI into the agent's environment using the 'uv' package manager. The input must be a string containing a valid package name and an optional version specifier (e.g., 'pandas', 'numpy>=1.2.3', 'scikit-learn==2.4.1')."
)
