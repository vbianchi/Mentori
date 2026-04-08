import os
import subprocess
import logging
import sys
from typing import List

logger = logging.getLogger(__name__)

# Default scientific packages to install in every user environment
DEFAULT_PACKAGES = [
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scipy",
    "scikit-learn",
    "requests"
]

def _run_uv_command(args: List[str], cwd: str) -> str:
    """Run a uv command in the specified directory."""
    try:
        # Check if uv is installed
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("uv is not installed or not in PATH")

    cmd = ["uv"] + args
    logger.info(f"Running uv command: {' '.join(cmd)} in {cwd}")
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "UV_CACHE_DIR": "/tmp/uv_cache"} # Optional: explicit cache
    )
    
    if result.returncode != 0:
        error_msg = f"uv command failed: {result.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    return result.stdout

def ensure_venv(path_identifier: str) -> str:
    """
    Ensure a .venv exists at the specified path (usually user workspace root).
    Returns the path to the python executable.
    
    Args:
        path_identifier: The absolute path where .venv should exist (e.g. /data/workspace/user_id)
    """
    venv_path = os.path.join(path_identifier, ".venv")
    python_exec = os.path.join(venv_path, "bin", "python")
    
    if not os.path.isdir(path_identifier):
         os.makedirs(path_identifier, exist_ok=True)

    # 1. Create venv if missing
    if not os.path.exists(python_exec):
        logger.info(f"Creating User Venv in {path_identifier}")
        _run_uv_command(["venv", ".venv"], cwd=path_identifier)
        
    # 2. Install default packages (idempotent via uv)
    logger.info(f"Ensuring default packages in {path_identifier}")
    _run_uv_command(["pip", "install"] + DEFAULT_PACKAGES, cwd=path_identifier)
    
    return python_exec

from backend.mcp.decorator import mentori_tool

@mentori_tool(category="system", agent_role="handyman", is_llm_based=False)
def install_package(
    package_name: str, 
    workspace_path: str = None, 
    user_id: str = None # Injected by tool server
) -> str:
    """
    Install a specific python package into the User's shared environment.
    
    Args:
        package_name: Name of the package to install.
        workspace_path: Task-specific workspace path (injected).
        user_id: The ID of the current user (injected).
        
    Returns:
        Success message or error.
    """
    # Resolve User Root
    from backend.config import settings
    
    target_path = workspace_path
    
    # Best effort to find User Root
    if user_id:
        # Construct path: WORKSPACE_DIR + user_id
        # We need to make sure WORKSPACE_DIR is absolute/correct
        base_ws = os.environ.get("WORKSPACE_DIR", settings.WORKSPACE_DIR)
        target_path = os.path.join(base_ws, user_id)
        
    elif workspace_path:
        # Fallback heuristic: If we don't have user_id, assume workspace_path is valid
        # But ideally we always want user_id injection.
        pass
        
    if not target_path:
        return "Error: Could not resolve user environment path. Missing user_id."

    python_exec = ensure_venv(target_path)
    
    logger.info(f"Installing {package_name} in User Env: {target_path}")
    _run_uv_command(["pip", "install", package_name], cwd=target_path)
    
    return f"Successfully installed {package_name} in user environment"

def get_python_executable(workspace_path: str) -> str:
    """
    Get the path to the isolated python executable. 
    Does NOT create it if missing (use ensure_venv for that).
    Returns system python if venv not found (fallback).
    """
    venv_python = os.path.join(workspace_path, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

# For imports checks
import sys
