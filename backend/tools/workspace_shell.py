# -----------------------------------------------------------------------------
# ResearchAgent Tool: Workspace Shell
#
# Correction: The Tool constructor now includes a placeholder `func` argument
# to satisfy the class requirements, while keeping the `coroutine` for
# proper async execution. This resolves the startup TypeError.
# -----------------------------------------------------------------------------

import logging
import os
import asyncio
from langchain_core.tools import Tool

logger = logging.getLogger(__name__)

# --- Configuration ---
SHELL_TIMEOUT = int(os.getenv("TOOL_SHELL_TIMEOUT", 120))

# --- Core Tool Logic ---
async def _run_shell_command(command: str) -> str:
    """
    Asynchronously executes a shell command and captures its stdout and stderr.
    """
    if not command:
        return "Error: No command provided."
        
    logger.info(f"Executing shell command: `{command}`")
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
            return f"Command finished with exit code 0.\n{output}"
        else:
            logger.warning(f"Command `{command}` failed with exit code {process.returncode}.")
            return f"Command failed with exit code {process.returncode}.\n{output}"

    except asyncio.TimeoutError:
        logger.error(f"Command `{command}` timed out after {SHELL_TIMEOUT} seconds.")
        return f"Error: Command timed out after {SHELL_TIMEOUT} seconds. The process was killed."
    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# === FIX: Added a placeholder for the required `func` argument ===
def _placeholder_sync_func(*args, **kwargs):
    """This is a placeholder and should never be called."""
    raise NotImplementedError("This tool can only be used asynchronously.")

# --- Tool Definition ---
tool = Tool(
    name="workspace_shell",
    description=(
        "A tool to execute a single, non-interactive shell command in the agent's workspace. "
        "Useful for a wide range of tasks including: file system operations (ls, pwd, cat, mkdir), "
        "running scripts (python script.py, Rscript analysis.R), package management (pip install, uv pip install), "
        "and version control (git clone, git status). "
        "Input must be a single, valid shell command string. "
        "Returns the command's stdout, stderr, and exit code."
    ),
    func=_placeholder_sync_func, # Satisfy the constructor requirement
    coroutine=_run_shell_command, # Specify the actual async function to run
)
