# backend/mcp/custom/code_execution.py
"""
Code execution tools for agent operations.

Security-focused tools that allow agents to:
- Run whitelisted bash commands (for Handyman)
- Execute Python code in a sandboxed environment (for Coder)
"""
import subprocess
import sys
import os
import re
import tempfile
import shlex
import ast
from typing import Optional
from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# === BASH COMMAND TOOL ===

# Whitelisted command prefixes (safe read-only or contained operations)
ALLOWED_BASH_COMMANDS = {
    # File inspection (read-only)
    "ls", "cat", "head", "tail", "wc", "file", "stat",
    # Search (read-only)
    "grep", "find", "tree", "which", "whereis",
    # Directory info
    "pwd", "du", "df",
    # Text processing (read-only)
    "sort", "uniq", "cut", "awk", "sed",  # Note: sed is read-only unless -i
    # Python related
    "python", "python3", "pip", "pip3",
    # Environment
    "echo", "env", "printenv", "date", "whoami",
    # Compression (read-only inspection)
    "unzip", "tar",  # Only with list flags
}

# Patterns that are ALWAYS blocked (security critical)
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b",           # rm -rf
    r"\brm\s+-r\b",            # rm -r
    r"\brm\s+.*\*",            # rm with wildcard
    r"\bsudo\b",               # sudo anything
    r"\bsu\b",                 # switch user
    r"\bchmod\b",              # permission changes
    r"\bchown\b",              # ownership changes
    r"\bcurl\s+.*\|\s*sh",     # curl pipe to shell
    r"\bwget\s+.*\|\s*sh",     # wget pipe to shell
    r"\bcurl\s+.*\|\s*bash",   # curl pipe to bash
    r"\bwget\s+.*\|\s*bash",   # wget pipe to bash
    r"\beval\b",               # eval is dangerous
    r"\bexec\b",               # exec is dangerous
    r"\bmkfs\b",               # filesystem creation
    r"\bdd\b",                 # disk destroyer
    r"\b>\s*/dev/",            # writing to devices
    r"\.\.\/",                 # path traversal
    r"\$\(",                   # command substitution
    r"`.*`",                   # backtick command substitution
]


def _is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed based on whitelist and blocklist.
    Returns (is_allowed, reason).
    """
    command_lower = command.lower().strip()

    # Check blocked patterns first (highest priority)
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command_lower):
            return False, f"Command matches blocked pattern: {pattern}"

    # Extract the base command (first word)
    parts = shlex.split(command)
    if not parts:
        return False, "Empty command"

    base_cmd = os.path.basename(parts[0])  # Handle /usr/bin/ls -> ls

    # Check if base command is whitelisted
    if base_cmd not in ALLOWED_BASH_COMMANDS:
        return False, f"Command '{base_cmd}' is not in the allowed list. Allowed: {', '.join(sorted(ALLOWED_BASH_COMMANDS))}"

    # Special checks for specific commands
    if base_cmd == "sed" and "-i" in parts:
        return False, "sed with -i (in-place edit) is not allowed"

    if base_cmd in ("tar", "unzip"):
        # Only allow listing operations
        if base_cmd == "tar" and "-t" not in command and "--list" not in command:
            if "-x" in command or "--extract" in command:
                return False, "tar extraction requires explicit approval. Use -t to list contents first."
        if base_cmd == "unzip" and "-l" not in command:
            return False, "unzip extraction requires explicit approval. Use -l to list contents first."

    return True, "OK"


@mentori_tool(category="system", agent_role="handyman", is_llm_based=False, secrets=["workspace_path", "user_id"])
def run_bash(
    command: str, 
    working_dir: str = ".", 
    timeout: int = 30,
    workspace_path: str = None, # Injected
    user_id: str = None         # Injected
) -> str:
    """
    Execute a bash command in a controlled environment.

    Only whitelisted commands are allowed (ls, cat, grep, find, python, etc.).
    Dangerous operations like rm -rf, sudo, and shell injections are blocked.
    
    The command normally runs in your task directory.

    Args:
        command: The bash command to execute
        working_dir: Directory to run the command in (default: "." which is task dir)
        timeout: Maximum execution time in seconds (default: 30, max: 120)

    Returns:
        Command output (stdout + stderr) or error message
    """
    # Validate command
    is_allowed, reason = _is_command_allowed(command)
    if not is_allowed:
        logger.warning(f"Blocked bash command: {command} - Reason: {reason}")
        return f"Error: Command not allowed. {reason}"

    # Clamp timeout
    timeout = min(max(timeout, 1), 120)

    # Resolve working directory
    # 1. If defaults to ".", use workspace_path (Task Dir)
    if working_dir == ".":
        if workspace_path:
            working_dir = workspace_path
        elif user_id:
            # Fallback to user root if no task path
            from backend.config import settings
            base_ws = os.environ.get("WORKSPACE_DIR", settings.WORKSPACE_DIR)
            working_dir = os.path.join(base_ws, user_id)
    
    # 2. If it's a relative path, anchor it!
    # If we have workspace_path, anchor to that.
    if not os.path.isabs(working_dir):
        if workspace_path:
             working_dir = os.path.join(workspace_path, working_dir)
        elif user_id:
             from backend.config import settings
             base_ws = os.environ.get("WORKSPACE_DIR", settings.WORKSPACE_DIR)
             working_dir = os.path.join(base_ws, user_id, working_dir)
        else:
             working_dir = os.path.abspath(working_dir)

    if not os.path.isdir(working_dir):
        # Auto-create if it's the task dir and missing? 
        # Better just error if the dir requested doesn't exist.
        return f"Error: Working directory does not exist: {working_dir}"

    logger.info(f"Executing bash command: {command} in {working_dir}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n--- stderr ---\n"
            output += result.stderr

        if result.returncode != 0:
            output = f"Command exited with code {result.returncode}\n{output}"

        # Truncate very long output
        if len(output) > 10000:
            output = output[:10000] + "\n... (output truncated)"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Bash command failed: {e}")
        return f"Error executing command: {str(e)}"


# === PYTHON EXECUTION TOOL ===

# Imports that are blocked in sandboxed Python execution
BLOCKED_PYTHON_IMPORTS = [
    "os.system", "os.popen", "os.spawn",
    "subprocess", "commands",
    "shutil.rmtree",
    "importlib",
    "__import__",
]

BLOCKED_PYTHON_PATTERNS = [
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bcompile\s*\(",
    r"\bopen\s*\([^)]*['\"][wa]['\"]",  # open with write/append mode
    r"\b__import__\s*\(",
    r"from\s+os\s+import\s+(system|popen|spawn)",
    r"import\s+subprocess",
    r"from\s+subprocess\s+import",
]


def _validate_python_code(code: str) -> tuple[bool, str]:
    """
    Validate Python code for potentially dangerous operations.
    Returns (is_safe, reason).
    """
    for pattern in BLOCKED_PYTHON_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Code contains blocked pattern: {pattern}"

    for blocked in BLOCKED_PYTHON_IMPORTS:
        if blocked in code:
            return False, f"Code contains blocked import/call: {blocked}"

    return True, "OK"


@mentori_tool(category="code", agent_role="coder", is_llm_based=False, secrets=["workspace_path", "user_id"])
def execute_python(
    code: str,
    working_dir: str = ".",
    workspace_path: str = None, # Injected by tool server
    user_id: str = None,        # Injected by tool server
    timeout: int = 60,
    capture_plots: bool = False
) -> str:
    """
    Execute Python code in a sandboxed subprocess.

    The code runs in an isolated subprocess with:
    - No access to dangerous modules (subprocess, os.system, etc.)
    - Timeout protection
    - Stdout/stderr capture

    Args:
        code: Python code to execute
        working_dir: Directory to run the code in
        workspace_path: Root of the user's workspace (system injected)
        timeout: Maximum execution time in seconds (default: 60, max: 300)
        capture_plots: If True, saves matplotlib plots to files (future feature)

    Returns:
        Execution output or error message
    """
    # Validate code
    is_safe, reason = _validate_python_code(code)
    if not is_safe:
        logger.warning(f"Blocked Python code: {reason}")
        return f"Error: Code validation failed. {reason}"

    # Clamp timeout
    timeout = min(max(timeout, 1), 300)

    # Resolve working directory logic
    # If workspace_path is provided (via injection), use it as base for specific resolutions
    # If working_dir is "." or empty, it means "workspace root".
    
    # Fallback if not injected (e.g. testing)
    if not workspace_path:
        workspace_path = os.environ.get("WORKSPACE_DIR", ".")

    if not working_dir or working_dir == ".":
         working_dir = workspace_path
    
    if not os.path.isabs(working_dir):
        # Interpret relative paths relative to workspace_path
        working_dir = os.path.abspath(os.path.join(workspace_path, working_dir))

    if not os.path.isdir(working_dir):
        try:
             os.makedirs(working_dir, exist_ok=True)
        except:
             return f"Error: Working directory does not exist: {working_dir}"

    logger.info(f"Executing Python code ({len(code)} chars) in {working_dir}")

    # Resolve Python executable (Isolated User Environment)
    from backend.mcp.custom import dependencies
    from backend.config import settings
    
    # We want to find the User's Root Environment: <workspace_root>/<user_id>
    # If user_id is injected, we use that. 
    # If not, we fall back to workspace_path (which might be <user_root>/<task_id>).
    
    target_env_path = None
    
    if user_id:
        base_ws = os.environ.get("WORKSPACE_DIR", settings.WORKSPACE_DIR)
        target_env_path = os.path.join(base_ws, user_id)
    elif workspace_path:
        # If we have workspace_path but no user_id, we MUST find the User Root,
        # otherwise we create a venv inside the task folder (BAD).
        # Heuristic: workspace_path is usually .../user_id/task_id
        # So parent is user_id.
        parent = os.path.dirname(workspace_path)
        # Verify it looks like a user folder (inside workspace root)
        # This is a bit weak but better than the bug.
        target_env_path = parent
    else:
        # Fallback to working_dir resolution - likely unsafe or tests
        target_env_path = working_dir

    try:
        # Pass the resolved target to ensure_venv
        python_exec = dependencies.ensure_venv(target_env_path)
        logger.info(f"Using isolated python execution: {python_exec}")
    except Exception as e:
        logger.error(f"Failed to ensure venv at {target_env_path}: {e}")
        python_exec = sys.executable  # Fallback to system

    # Write code to a temporary file
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            dir=working_dir,
            delete=False
        ) as f:
            # Add safety wrapper
            safe_code = f'''# Sandboxed execution
import sys
import warnings
import types
warnings.filterwarnings('ignore')

# Restrict dangerous operations at runtime
import builtins
_original_import = builtins.__import__

def _safe_import(name, *args, **kwargs):
    blocked = ['subprocess', 'commands']
    if name in blocked:
        m = types.ModuleType(name)
        def _deny(*args, **kwargs):
            raise ImportError(f"Usage of '{{name}}' is not allowed in sandbox")
        # Allow attribute access but deny call/usage?
        # A simple module is fine for import. But if they access 'subprocess.run', it returns None usually.
        # Better: make everything raise.
        # For now, just a bare module is enough to pass 'import subprocess'.
        return m
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _safe_import

# User code below
{code}
'''
            f.write(safe_code)
            temp_file = f.name

        # Execute in subprocess
        result = subprocess.run(
            [python_exec, temp_file],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
                # Ensure VIRTUAL_ENV is set for the subprocess
                "VIRTUAL_ENV": os.path.dirname(os.path.dirname(python_exec)) if ".venv" in python_exec else "",
                "PATH": f"{os.path.dirname(python_exec)}:{os.environ.get('PATH', '')}"
            }
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            # Filter out common warnings
            stderr = result.stderr
            if "UserWarning" not in stderr and "DeprecationWarning" not in stderr:
                if output:
                    output += "\n--- stderr ---\n"
                output += stderr

        if result.returncode != 0:
            output = f"Execution failed (exit code {result.returncode})\n{output}"

        # Truncate very long output
        if len(output) > 500000:
            output = output[:500000] + "\n... (output truncated)"

        return output if output else "(code executed successfully, no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Python execution failed: {e}")
        return f"Error executing Python code: {str(e)}"
    finally:
        # Clean up temp file
        try:
            if 'temp_file' in locals():
                os.unlink(temp_file)
        except:
            pass


@mentori_tool(category="code", agent_role="coder", is_llm_based=False, secrets=["workspace_path", "user_id"])
def write_code(
    path: str,
    content: str,
    verify_execution: bool = False,
    user_id: str = None,
    workspace_path: str = None
) -> str:
    """
    Write code to a file with syntax validation and optional verification.

    Features:
    - Validates syntax for Python files (.py) using AST.
    - Optionally executes the code to verify it runs without crashing.
    - Writes to file only if checks pass.
    
    Args:
        path: Relative path to the file (e.g., "script.py")
        content: The code content
        verify_execution: If True, executes the code (dry run) before saving. 
                         Only applies to Python. Default: False.
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        Status message (e.g., "Successfully saved to ...")
    """
    # 1. Path Security & Resolution
    # We reuse the logic from file_ops for consistency, importing locally to avoid circular deps
    try:
        from backend.mcp.custom.file_ops import _validate_path, FileOpsError, SecurityError
        target_path = _validate_path(path, user_id, workspace_path)
    except ImportError:
        # Fallback if file_ops not found (unlikely)
        return "Error: Internal dependency failure (file_ops)."
    except (FileOpsError, SecurityError) as e:
        return f"Error: {str(e)}"

    # 2. Language Detection & Syntax Check
    filename = str(target_path)
    is_python = filename.endswith(".py")
    
    if is_python:
        try:
            ast.parse(content)
        except SyntaxError as e:
            return f"SyntaxError: Code is invalid Python.\nUpdate your code and try again.\nDetails: {e}"
        except Exception as e:
             return f"Validation Error: {e}"

    # 3. Execution Verification (Optional, Python only)
    if verify_execution and is_python:
        logger.info(f"Verifying code execution for {path}...")
        
        # We use execute_python logic. We can call it directly since it's in this module.
        # Note: execute_python writes its own temp file, so we don't need to save target_path yet.
        
        # Use a short timeout for verification to prevent hangs
        verification_result = execute_python(
            code=content,
            working_dir=os.path.dirname(filename), # Run in target dir context
            workspace_path=workspace_path,
            user_id=user_id,
            timeout=10 
        )
        
        # Check for failure indications in the output
        # execute_python returns string output. We need to heuristically check for errors.
        # It prefixes "Error:" or "Execution failed" on errors.
        if verification_result.startswith("Error:") or "Execution failed" in verification_result:
            return f"Verification Failed. File NOT saved.\nOutput:\n{verification_result}"
            
        logger.info(f"Verification successful for {path}")

    elif verify_execution and not is_python:
        # Warn but proceed
        logger.info(f"Skipping verification for non-Python file: {path}")

    # 4. Write to File
    if target_path.is_dir():
        return f"Error: Path is a directory: {path}"

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        
        msg = f"Successfully saved to {path}"
        if verify_execution and is_python:
            msg += " (Verified)"
        elif verify_execution:
            msg += " (Verification skipped: not .py)"
            
        return msg
        
    except Exception as e:
        return f"Error writing file: {str(e)}"

