# -----------------------------------------------------------------------------
# ResearchAgent Tool: Workspace Shell
#
# This tool allows the agent to execute shell commands non-interactively.
#
# Correction: The `Tool` definition now only provides the `coroutine` argument
# to prevent "cannot pickle 'coroutine' object" errors during state transitions.
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
        return f"Error: Command timed out after {SHE_TIMEOUT} seconds. The process was killed."
    except Exception as e:
        logger.error(f"An unexpected error occurred while running command `{command}`: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"

# --- Tool Definition ---
# === FIX: Removed the synchronous `func` argument ===
# Defining the tool as async-only by providing just the `coroutine`
# is the robust way to handle this and prevents serialization issues.
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
    coroutine=_run_shell_command,
)
