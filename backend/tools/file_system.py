# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed File System (Simplified & Robust)
#
# FINAL CORRECTION: The Pydantic models have been simplified to use explicit
# argument names (`file_path`, `content`) without complex validators. The
# underlying tool functions (`write_file`, `read_file`) have been updated to
# match these argument names. This aligns the tool's definition with the
# direct-call logic in the executor, resolving the `TypeError`.
#
# Additionally, the tool descriptions have been significantly improved to
# provide clearer guidance to the planner, encouraging it to use the correct
# tool for each task (e.g., `write_file` for content creation).
# -----------------------------------------------------------------------------

import os
import logging
import asyncio
from typing import Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Security Helper ---
def _resolve_path(workspace_path: str, file_path: str) -> str:
    """Validates and resolves a file path against the secure workspace directory."""
    abs_workspace_path = os.path.abspath(workspace_path)
    # Prevent directory traversal attacks
    if ".." in file_path:
        raise PermissionError(f"File path cannot contain '..'. Access denied.")
    abs_file_path = os.path.abspath(os.path.join(abs_workspace_path, file_path))
    if not abs_file_path.startswith(abs_workspace_path):
        raise PermissionError(f"Attempted to access file '{file_path}' outside of the designated workspace.")
    return abs_file_path

# --- Simplified & Explicit Pydantic Schemas ---
class WriteFileInput(BaseModel):
    """Input schema for the write_file tool."""
    file_path: str = Field(..., description="The relative path to the file within the workspace.")
    content: str = Field(..., description="The full content to write to the file.")

class ReadFileInput(BaseModel):
    """Input schema for the read_file tool."""
    file_path: str = Field(..., description="The relative path to the file to read from within the workspace.")

class ListFilesInput(BaseModel):
    """Input schema for the list_files tool."""
    directory: str = Field(default=".", description="The relative directory path to list files from. Defaults to the workspace root.")

# --- Asynchronous Tool Functions (primary implementation) ---
async def _awrite_file(file_path: str, content: str, workspace_path: str) -> str:
    """Asynchronously writes content to a file within the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # Use async file I/O if available, otherwise wrap sync I/O
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{file_path}'."
    except Exception as e:
        logger.error(f"Error in _awrite_file: {e}", exc_info=True)
        return f"Error writing file: {e}"

async def _aread_file(file_path: str, workspace_path: str) -> str:
    """Asynchronously reads the content of a file from within the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, file_path)
        # Use async file I/O if available, otherwise wrap sync I/O
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{file_path}'."
    except Exception as e:
        logger.error(f"Error in _aread_file: {e}", exc_info=True)
        return f"Error reading file: {e}"

async def _alist_files(directory: str, workspace_path: str) -> str:
    """Asynchronously lists all files and directories within a given path in the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, directory)
        if not os.path.isdir(full_path): return f"Error: '{directory}' is not a valid directory."
        items = os.listdir(full_path)
        return "\n".join(items) if items else f"The directory '{directory}' is empty."
    except Exception as e:
        logger.error(f"Error in _alist_files: {e}", exc_info=True)
        return f"Error listing files: {e}"

# --- Synchronous Wrappers (for compatibility) ---
def _write_file_sync(file_path: str, content: str, workspace_path: str) -> str:
    """Synchronous wrapper for _awrite_file."""
    return asyncio.run(_awrite_file(file_path, content, workspace_path))

def _read_file_sync(file_path: str, workspace_path: str) -> str:
    """Synchronous wrapper for _aread_file."""
    return asyncio.run(_aread_file(file_path, workspace_path))

def _list_files_sync(directory: str, workspace_path: str) -> str:
    """Synchronous wrapper for _alist_files."""
    return asyncio.run(_alist_files(directory, workspace_path))

# --- Tool Definitions with Improved Descriptions ---
write_file_tool = StructuredTool.from_function(
    func=_write_file_sync,
    coroutine=_awrite_file,
    name="write_file",
    description="The primary tool for creating or completely overwriting a text file. Use this to save content like code, poems, or data to a specific file.",
    args_schema=WriteFileInput
)

read_file_tool = StructuredTool.from_function(
    func=_read_file_sync,
    coroutine=_aread_file,
    name="read_file",
    description="Reads and returns the entire content of a specified text file from the workspace.",
    args_schema=ReadFileInput
)

list_files_tool = StructuredTool.from_function(
    func=_list_files_sync,
    coroutine=_alist_files,
    name="list_files",
    description="Lists all files and subdirectories within a specified directory. Essential for checking if a file exists or getting an overview of the workspace.",
    args_schema=ListFilesInput
)

# Export a list of all tools in this module
tools = [write_file_tool, read_file_tool, list_files_tool]
