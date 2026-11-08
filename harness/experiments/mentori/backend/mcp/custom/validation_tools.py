"""
Validation Tools for agent operations.

These tools allow agents to validate their work before returning results.
"""

import os
import ast
from PIL import Image
from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_session_context


@mentori_tool(category="validation", agent_role=None, is_llm_based=False, secrets=["workspace_path"])
def verify_file_exists(path: str, workspace_path: str = None) -> str:
    """
    Verify that a file exists in the workspace.

    Use this tool to confirm that a file you created actually exists.

    Args:
        path: File path relative to workspace

    Returns:
        Confirmation message or error if file doesn't exist
    """
    # Get workspace from injected secret or session context
    ctx = get_session_context()
    workspace = workspace_path or (ctx.workspace_path if ctx else None)

    if not workspace:
        return f"ERROR: No workspace configured. Cannot resolve path '{path}'"

    full_path = os.path.join(workspace, path)

    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        if os.path.isfile(full_path):
            return f"VERIFIED: File '{path}' exists ({size} bytes)"
        else:
            return f"VERIFIED: Directory '{path}' exists"
    else:
        return f"ERROR: File '{path}' does not exist at {full_path}"


@mentori_tool(category="validation", agent_role=None, is_llm_based=False)
def validate_python_syntax(code: str) -> str:
    """
    Check Python code for syntax errors without executing it.

    Use this tool to verify your Python code is syntactically correct
    before considering the task complete.

    Args:
        code: Python code to validate

    Returns:
        Validation result - either "VALID" or error details
    """
    try:
        ast.parse(code)
        return "VALID: Python syntax is correct"
    except SyntaxError as e:
        return f"SYNTAX ERROR at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"VALIDATION ERROR: {str(e)}"


@mentori_tool(category="validation", agent_role=None, is_llm_based=False, secrets=["workspace_path"])
def verify_image_valid(path: str, workspace_path: str = None) -> str:
    """
    Verify that an image file is valid and readable.

    Use this tool to confirm that an image you created can be opened
    and is a valid image format.

    Args:
        path: Image file path relative to workspace

    Returns:
        Image details or error if invalid
    """
    # Get workspace from injected secret or session context
    ctx = get_session_context()
    workspace = workspace_path or (ctx.workspace_path if ctx else None)

    if not workspace:
        return f"ERROR: No workspace configured. Cannot resolve path '{path}'"

    full_path = os.path.join(workspace, path)

    if not os.path.exists(full_path):
        return f"ERROR: Image file '{path}' does not exist"

    try:
        with Image.open(full_path) as img:
            width, height = img.size
            mode = img.mode
            format_name = img.format

            return (
                f"VALID: Image '{path}' is valid\n"
                f"  Format: {format_name}\n"
                f"  Size: {width}x{height}\n"
                f"  Mode: {mode}"
            )
    except Exception as e:
        return f"ERROR: Could not open image '{path}': {str(e)}"


@mentori_tool(category="validation", agent_role=None, is_llm_based=False, secrets=["workspace_path"])
def verify_json_valid(path: str, workspace_path: str = None) -> str:
    """
    Verify that a JSON file is valid and parseable.

    Args:
        path: JSON file path relative to workspace

    Returns:
        Validation result with structure info or error
    """
    import json

    # Get workspace from injected secret or session context
    ctx = get_session_context()
    workspace = workspace_path or (ctx.workspace_path if ctx else None)

    if not workspace:
        return f"ERROR: No workspace configured. Cannot resolve path '{path}'"

    full_path = os.path.join(workspace, path)

    if not os.path.exists(full_path):
        return f"ERROR: JSON file '{path}' does not exist"

    try:
        with open(full_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict):
            keys = list(data.keys())[:5]
            return f"VALID: JSON file '{path}' contains object with keys: {keys}"
        elif isinstance(data, list):
            return f"VALID: JSON file '{path}' contains array with {len(data)} items"
        else:
            return f"VALID: JSON file '{path}' contains: {type(data).__name__}"

    except json.JSONDecodeError as e:
        return f"JSON ERROR at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"ERROR: Could not read JSON '{path}': {str(e)}"


@mentori_tool(category="validation", agent_role=None, is_llm_based=False, secrets=["workspace_path"])
def verify_csv_valid(path: str, workspace_path: str = None) -> str:
    """
    Verify that a CSV file is valid and readable.

    Args:
        path: CSV file path relative to workspace

    Returns:
        Validation result with structure info or error
    """
    import csv

    # Get workspace from injected secret or session context
    ctx = get_session_context()
    workspace = workspace_path or (ctx.workspace_path if ctx else None)

    if not workspace:
        return f"ERROR: No workspace configured. Cannot resolve path '{path}'"

    full_path = os.path.join(workspace, path)

    if not os.path.exists(full_path):
        return f"ERROR: CSV file '{path}' does not exist"

    try:
        with open(full_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            row_count = sum(1 for _ in reader) + 1  # +1 for header

        if headers:
            return (
                f"VALID: CSV file '{path}'\n"
                f"  Columns: {len(headers)} - {headers[:5]}{'...' if len(headers) > 5 else ''}\n"
                f"  Rows: {row_count}"
            )
        else:
            return f"WARNING: CSV file '{path}' appears to be empty"

    except Exception as e:
        return f"ERROR: Could not read CSV '{path}': {str(e)}"
