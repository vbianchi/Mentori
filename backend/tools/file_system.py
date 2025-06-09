# -----------------------------------------------------------------------------
# ResearchAgent Tool: Sandboxed File System
#
# FIX: Added a robust model_validator to ReadFileInput. This allows the
# planner to use 'file', 'filename', or 'file_path' interchangeably when
# specifying the file to read, making the tool more resilient.
# -----------------------------------------------------------------------------

import os
import logging
from typing import Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, model_validator, ConfigDict

logger = logging.getLogger(__name__)

# --- Security Helper ---
def _resolve_path(workspace_path: str, file_path: str) -> str:
    abs_workspace_path = os.path.abspath(workspace_path)
    abs_file_path = os.path.abspath(os.path.join(abs_workspace_path, file_path))
    if not abs_file_path.startswith(abs_workspace_path):
        raise PermissionError(f"Attempted to access file '{file_path}' outside of the designated workspace.")
    return abs_file_path

# --- Pydantic Schemas for Robust Argument Parsing ---
class WriteFileInput(BaseModel):
    content: str = Field(..., description="The full content to write to the file.")
    file: Optional[str] = None
    file_path: Optional[str] = None
    filename: Optional[str] = None
    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    def consolidate_file_path(cls, values):
        if isinstance(values, dict):
            path = values.get('file') or values.get('file_path') or values.get('filename')
            if path is None:
                raise ValueError("A file path must be provided using one of 'file', 'file_path', or 'filename'.")
            
            values['file'] = path
            values.pop('file_path', None)
            values.pop('filename', None)
            
        return values

class ReadFileInput(BaseModel):
    file_path: Optional[str] = None
    model_config = ConfigDict(extra='allow')
    
    @model_validator(mode='before')
    def consolidate_file_path(cls, values):
        """Consolidates various possible key names for a file path into the canonical 'file_path' field."""
        if isinstance(values, dict):
            # Prioritize 'file_path', then 'file', then 'filename'
            path = values.get('file_path') or values.get('file') or values.get('filename')
            if path is None:
                raise ValueError("A file path must be provided using one of 'file', 'file_path', or 'filename'.")
            
            # Set the canonical 'file_path' field and remove the others to avoid confusion
            values['file_path'] = path
            values.pop('file', None)
            values.pop('filename', None)
        
        # If the direct input is a string, assign it to 'file_path'
        elif isinstance(values, str):
            return {'file_path': values}
            
        return values


class ListFilesInput(BaseModel):
    directory: str = Field(default=".", description="The directory within the workspace to list files from. Use '.' for the root.")
    model_config = ConfigDict(extra='allow')

# --- Tool Functions ---
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

def read_file(file_path: str, workspace_path: str) -> str:
    """Reads the content of a file from within the secure workspace."""
    try:
        full_path = _resolve_path(workspace_path, file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{file_path}'."
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
write_file_tool = StructuredTool.from_function(
    func=write_file, name="write_file",
    description="Writes content to a specified file within the agent's workspace.",
    args_schema=WriteFileInput
)
read_file_tool = StructuredTool.from_function(
    func=read_file, name="read_file",
    description="Reads the entire content of a specified file from the agent's workspace. Can take a string or a JSON object with 'file_path', 'file', or 'filename'.",
    args_schema=ReadFileInput
)
list_files_tool = StructuredTool.from_function(
    func=list_files, name="list_files",
    description="Lists all files and subdirectories within a specified directory in the agent's workspace.",
    args_schema=ListFilesInput
)

tools = [write_file_tool, read_file_tool, list_files_tool]