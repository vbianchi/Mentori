# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed File System
#
# Definitive Fix: This version is simplified. All complex Pydantic aliasing
# has been removed. The tool now has a simple, clear function signature.
# The responsibility for handling variations in the Planner's output is
# moved to the Executor node in the agent graph, which is a more robust design.
# -----------------------------------------------------------------------------

import os
import logging
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# --- Security Helper ---
def _resolve_path(workspace_path: str, file_path: str) -> str:
    abs_workspace_path = os.path.abspath(workspace_path)
    abs_file_path = os.path.abspath(os.path.join(abs_workspace_path, file_path))
    if not abs_file_path.startswith(abs_workspace_path):
        raise PermissionError(f"Attempted to access file '{file_path}' outside of the designated workspace.")
    return abs_file_path

# --- Tool Functions with Canonical Argument Names ---
def write_file(content: str, file: str, workspace_path: str) -> str:
    """Writes content to a file within the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, file)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{file}'."
    except Exception as e:
        return f"Error writing file: {e}"

def read_file(file: str, workspace_path: str) -> str:
    """Reads the content of a file from within the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, file)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{file}'."
    except Exception as e:
        return f"Error reading file: {e}"

def list_files(directory: str, workspace_path: str) -> str:
    """Lists all files and directories within a given path in the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, directory)
        if not os.path.isdir(full_path): return f"Error: '{directory}' is not a valid directory."
        items = os.listdir(full_path)
        return "\n".join(items) if items else f"The directory '{directory}' is empty."
    except Exception as e:
        return f"Error listing files: {e}"

# --- Tool Definitions ---
# LangChain's `from_function` will now correctly infer the simple arguments.
write_file_tool = StructuredTool.from_function(
    func=write_file, name="write_file",
    description="Writes content to a specified file within the agent's workspace. The input must be a dictionary with 'content' and 'file' keys."
)
read_file_tool = StructuredTool.from_function(
    func=read_file, name="read_file",
    description="Reads the entire content of a specified file from the agent's workspace."
)
list_files_tool = StructuredTool.from_function(
    func=list_files, name="list_files",
    description="Lists all files and subdirectories within a specified directory in the agent's workspace. Use '.' for the current directory."
)

tools = [write_file_tool, read_file_tool, list_files_tool]
