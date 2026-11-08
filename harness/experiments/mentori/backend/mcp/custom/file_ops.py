
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union, Dict
from backend.config import BASE_DIR, settings
from backend.logging_config import logger
from backend.mcp.decorator import mentori_tool

# Constants
WORKSPACE_ROOT = Path(settings.WORKSPACE_DIR)

class FileOpsError(Exception):
    """Base exception for file operation errors."""
    pass

class SecurityError(FileOpsError):
    """Raised when an operation attempts to access files outside the allowed scope."""
    pass

def _get_user_root(user_id: str) -> Path:
    """Returns the root directory for a specific user."""
    return WORKSPACE_ROOT / str(user_id)

def _validate_path(path: Union[str, Path], user_id: str, workspace_path: Optional[str] = None) -> Path:
    """
    Validates that a path is safe and within the user's workspace.
    
    Args:
        path: The path to validate (absolute or relative).
        user_id: The ID of the user performing the operation.
        workspace_path: Optional task-specific workspace path. If provided, relative paths
                       will be resolved against this folder.
        
    Returns:
        Path: The resolved absolute path.
        
    Raises:
        SecurityError: If the path is outside the user's workspace.
    """
    user_root = _get_user_root(user_id).resolve()
    
    # Determine the base directory for relative path resolution
    # If workspace_path is provided (task context), use that. Otherwise use user_root.
    base_dir = Path(workspace_path).resolve() if workspace_path else user_root
    
    path_obj = Path(path)
    
    if path_obj.is_absolute():
        try:
            resolved_path = path_obj.resolve()
        except OSError:
            resolved_path = path_obj.resolve()
    else:
        # Resolve relative paths against the task folder (base_dir)
        resolved_path = (base_dir / path_obj).resolve()

    # The Core Security Check:
    # ensure resolved_path starts with user_root (user's isolation boundary)
    # Note: We alway check against user_root, even if using task-specific base_dir
    # because task folders are children of user_root.
    if not str(resolved_path).startswith(str(user_root)):
        logger.warning(f"Security Alert: User {user_id} attempted access to {resolved_path}")
        raise SecurityError(f"Access denied: Path {path} is outside your workspace.")
        
    return resolved_path

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def list_files(path: str, user_id: str, workspace_path: str = None) -> str:
    """
    List contents of a directory in your workspace.

    IMPORTANT - Path Format:
    - Use RELATIVE paths (e.g., "." for current task folder, "output")
    - Paths are relative to your current TASK directory (if active)
    - To list user root, you may need to use absolute path or navigate up (if allowed)
    
    Args:
        path: Relative directory path (use "." for current task root)
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        String listing of files and directories.
    """
    try:
        results = list_directory_data(path, user_id, workspace_path)
        # Format as string to match previous expected output for simple agent use
        output = []
        for item in results:
            output.append(f"{item['path']} ({item['type']})")
        return "\n".join(output)
    except Exception as e:
        return f"Error: {str(e)}"

def list_directory_data(path: str, user_id: str, workspace_path: str = None) -> List[Dict[str, str]]:
    """
    Internal structured list function.
    """
    target_path = _validate_path(path, user_id, workspace_path)
    
    if not target_path.exists():
        raise FileOpsError(f"Directory not found: {path}")
    if not target_path.is_dir():
        raise FileOpsError(f"Path is not a directory: {path}")
        
    results = []
    try:
        for item in target_path.iterdir():
            results.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item)
            })
    except PermissionError:
        raise FileOpsError(f"Permission denied accessing directory: {path}")
        
    # Sort by type (dirs first) then name
    results.sort(key=lambda x: (x["type"] != "directory", x["name"]))
    return results

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def read_file(path: str, user_id: str, workspace_path: str = None) -> str:
    """
    Read the contents of a file in your workspace.

    IMPORTANT - Path Format:
    - Use RELATIVE paths (e.g., "notes.txt", "outputs/data.csv")
    - Paths are relative to your current TASK directory
    
    Args:
        path: Relative file path
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        The file contents as a string.
    """
    target_path = _validate_path(path, user_id, workspace_path)
    
    if not target_path.exists():
        raise FileOpsError(f"File not found: {path}")
    if not target_path.is_file():
        raise FileOpsError(f"Not a file: {path}")
        
    try:
        return target_path.read_text(encoding="utf-8")
    except Exception as e:
        raise FileOpsError(f"Failed to read file: {str(e)}")

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def write_file(path: str, content: str, user_id: str, workspace_path: str = None) -> str:
    """
    Write or create a file in your workspace with the given content.

    IMPORTANT - Path Format:
    - Use RELATIVE paths (e.g., "output.txt", "results/data.csv")
    - Paths are relative to your current TASK directory
    - Parent directories will be created automatically
    
    Args:
        path: Relative file path
        content: The content to write
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        The absolute path where the file was written.
    """
    target_path = _validate_path(path, user_id, workspace_path)
    
    if target_path.is_dir():
        raise FileOpsError(f"Cannot write to a directory: {path}")
        
    try:
        # Ensure parent exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return str(target_path)
    except Exception as e:
        raise FileOpsError(f"Failed to write file: {str(e)}")

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def move_file(source: str, destination: str, user_id: str, workspace_path: str = None) -> str:
    """
    Move or rename a file or directory within your workspace.

    Args:
        source: Relative path to source (relative to TASK dir)
        destination: Relative path to destination (relative to TASK dir)
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        New path of the moved item.
    """
    src_path = _validate_path(source, user_id, workspace_path)
    dst_path = _validate_path(destination, user_id, workspace_path)
    
    if not src_path.exists():
        raise FileOpsError(f"Source not found: {source}")
        
    try:
        new_path = shutil.move(str(src_path), str(dst_path))
        return str(new_path)
    except Exception as e:
        raise FileOpsError(f"Move failed: {str(e)}")

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def delete_path(path: str, user_id: str, workspace_path: str = None) -> bool:
    """
    Delete a file or directory (including all contents) from your workspace.

    Args:
        path: Relative path to delete (relative to TASK dir)
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        True if deletion was successful.
    """
    target_path = _validate_path(path, user_id, workspace_path)
    
    if not target_path.exists():
        raise FileOpsError(f"Path not found: {path}")
        
    try:
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        return True
    except Exception as e:
        raise FileOpsError(f"Deletion failed: {str(e)}")

@mentori_tool(category="filesystem", agent_role="handyman", is_llm_based=False)
def create_directory(path: str, user_id: str, workspace_path: str = None) -> str:
    """
    Create a new directory in your workspace.

    Args:
        path: Relative path (relative to TASK dir)
        user_id: Injected user ID
        workspace_path: Injected task workspace path

    Returns:
        The absolute path where the directory was created.
    """
    target_path = _validate_path(path, user_id, workspace_path)
    
    try:
        target_path.mkdir(parents=True, exist_ok=True)
        return str(target_path)
    except Exception as e:
        raise FileOpsError(f"Failed to create directory: {str(e)}")

