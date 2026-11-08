# backend/agents/notebook/tools.py
"""
Internal tools for the coder agent.

These tools are NOT exposed via MCP - they are internal to the coder loop
and provide notebook manipulation capabilities.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

from backend.agents.notebook.schema import (
    Cell,
    CellOutput,
    CellType,
    KernelState,
    Notebook,
    NotebookState,
)
from backend.agents.notebook.kernel import KernelRegistry
from backend.agents.notebook.manager import NotebookManager
from backend.agents.session_context import get_logger

logger = get_logger(__name__)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "data": self.data
        }
        if self.error:
            result["error"] = self.error
        if self.message:
            result["message"] = self.message
        return result

    def to_llm_string(self) -> str:
        """Format for LLM consumption."""
        if self.success:
            if self.message:
                return f"Success: {self.message}"
            return f"Success: {self.data}"
        else:
            return f"Error: {self.error}"


# Tool schema definitions for LLM
CODER_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_cell",
            "description": "Add a new cell to the notebook. Use this to write new code or markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "The code or markdown content for the cell"
                    },
                    "cell_type": {
                        "type": "string",
                        "enum": ["code", "markdown"],
                        "default": "code",
                        "description": "Type of cell: 'code' for Python code, 'markdown' for documentation"
                    }
                },
                "required": ["source"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_cell",
            "description": "Execute a code cell and see its output. Run this after adding or editing a cell to verify it works.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "The ID of the cell to execute (from get_notebook_state or add_cell response)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Execution timeout in seconds. Default 600s (10 minutes). Increase for long-running tasks.",
                        "default": 600
                    }
                },
                "required": ["cell_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_cell",
            "description": "Edit an existing cell's source. Use this to fix errors or modify code. After editing, execute the cell to verify the fix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "The ID of the cell to edit"
                    },
                    "source": {
                        "type": "string",
                        "description": "The new source content for the cell"
                    }
                },
                "required": ["cell_id", "source"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_cell",
            "description": "Delete a cell from the notebook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "The ID of the cell to delete"
                    }
                },
                "required": ["cell_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notebook_state",
            "description": "Get the current state of the notebook including all cells, their outputs, and execution status. Use this to see what code exists and plan next steps.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cell",
            "description": "Get the full content of a specific cell including its complete source code and outputs. Use this when you need to examine a cell in detail, especially when get_notebook_state shows truncated content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "The ID of the cell to retrieve (can be partial ID like first 8 characters)"
                    }
                },
                "required": ["cell_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kernel_state",
            "description": "Get the current state of the Jupyter kernel including all variables, their types, shapes, and values. Use this to understand what data is available in memory before writing code that uses it.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_notebook",
            "description": "Create a new notebook and switch to it. Use this to start a fresh notebook for a different analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the new notebook (without .ipynb extension)"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_notebook",
            "description": "Switch to a different existing notebook. Use get_notebook_state to see available notebooks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the notebook to switch to"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace. Use this to export results, create reports, or save data files. The file will be saved relative to the task workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path for the file (e.g., 'report.md', 'results/analysis.csv'). Do not use absolute paths."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file in the workspace. Use this to view existing files or data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "final_answer",
            "description": "Signal that the task is complete and provide a final summary. Use this when ALL requested work is done. Do NOT use this if there are remaining steps or errors to fix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A concise summary of what was accomplished, including key outputs and any important findings"
                    },
                    "outputs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of outputs created (files, plots, variables, etc.)"
                    }
                },
                "required": ["summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_notebook",
            "description": "Analyze an existing notebook to understand its structure, imports, data flow, and purpose. Use this when you need to understand what an existing notebook does before modifying it or answering questions about it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notebook_name": {
                        "type": "string",
                        "description": "Name of the notebook to analyze (optional - defaults to current notebook)"
                    }
                },
                "required": []
            }
        }
    }
]


class CoderTools:
    """
    Tool implementations for the coder agent.

    Manages notebook operations and kernel execution.
    """

    def __init__(
        self,
        notebook_manager: NotebookManager,
        notebook: Notebook
    ):
        """
        Initialize coder tools.

        Args:
            notebook_manager: Manager for notebook file operations
            notebook: Current active notebook
        """
        self.manager = notebook_manager
        self.notebook = notebook
        self._kernel = None  # Lazy loaded

    async def _get_kernel(self):
        """Get or create kernel for the current notebook."""
        if self._kernel is None or not self._kernel.is_alive():
            full_path = self.manager.get_full_notebook_path(self.notebook.name)
            working_dir = self.manager.get_workspace_path()

            self._kernel = await KernelRegistry.get_kernel(full_path, working_dir)

        return self._kernel

    def set_notebook(self, notebook: Notebook) -> None:
        """Switch to a different notebook (clears kernel reference)."""
        self.notebook = notebook
        self._kernel = None  # Will get new kernel on next execution

    def _find_cell(self, cell_id: str) -> Optional[Cell]:
        """
        Find a cell by exact ID or prefix.
        
        Args:
            cell_id: Full UUID or prefix (min 4 chars)
            
        Returns:
            Cell object or None
        """
        if not cell_id:
            return None
            
        # 1. Try exact match first
        cell = self.notebook.get_cell(cell_id)
        if cell:
            return cell
            
        # 2. Try prefix match
        # Only allow prefix match if it's reasonably specific (at least 4 chars)
        if len(cell_id) >= 4:
            candidates = []
            for c in self.notebook.cells:
                if c.id.startswith(cell_id):
                    candidates.append(c)
            
            # Only return if ambiguous match (single candidate)
            # If multiple cells match the prefix, we can't be sure which one it is
            if len(candidates) == 1:
                return candidates[0]
                
        return None

    # --- Tool Implementations ---

    async def add_cell(
        self,
        source: str,
        cell_type: str = "code",
        **kwargs
    ) -> ToolResult:
        """
        Add a new cell to the notebook.

        Args:
            source: Cell content
            cell_type: "code" or "markdown"

        Returns:
            ToolResult with cell info
        """
        try:
            # Handle 'type' alias for 'cell_type' (common hallucination)
            if "type" in kwargs and cell_type == "code":
                cell_type = kwargs["type"]

            # Validate cell type
            if cell_type not in ("code", "markdown"):
                cell_type = "code"

            cell = self.notebook.add_cell(
                source=source,
                cell_type=cell_type
            )

            # Save notebook
            self.manager.save_notebook(self.notebook)

            logger.info(f"Added {cell_type} cell: {cell.id[:8]}")

            return ToolResult(
                success=True,
                data={
                    "cell_id": cell.id,
                    "cell_type": cell.cell_type,
                    "index": len(self.notebook.cells) - 1
                },
                message=f"Added {cell_type} cell with id={cell.id}. Use execute_cell(cell_id=\"{cell.id}\") to run it."
            )

        except Exception as e:
            logger.error(f"Failed to add cell: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def execute_cell(
        self,
        cell_id: str,
        timeout: int = 600
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute a cell and stream outputs.

        Yields events as execution progresses:
        - {"type": "execution_start", "cell_id": ...}
        - {"type": "output", "cell_id": ..., "output": CellOutput}
        - {"type": "execution_complete", "cell_id": ..., "status": ...}

        Args:
            cell_id: ID of cell to execute
            timeout: Execution timeout in seconds
        """
        # Find cell (support partial IDs)
        cell = self._find_cell(cell_id)

        if not cell:
            # Provide helpful error with actual cell IDs
            actual_ids = [c.id for c in self.notebook.cells]
            id_list = "\n".join([f"  - {cid}" for cid in actual_ids]) if actual_ids else "  (no cells in notebook)"
            yield {
                "type": "execution_error",
                "cell_id": cell_id,
                "error": f"Cell not found: '{cell_id}'\n\n**Available cell IDs:**\n{id_list}\n\nUse one of these EXACT IDs."
            }
            return

        if cell.cell_type != "code":
            yield {
                "type": "execution_complete",
                "cell_id": cell_id,
                "status": "success",
                "message": "Markdown cells don't need execution"
            }
            return

        # Clear previous outputs
        cell.clear_outputs()
        cell.status = "running"

        yield {
            "type": "execution_start",
            "cell_id": cell_id
        }

        try:
            # Get kernel
            kernel = await self._get_kernel()

            # Execute and collect outputs
            has_error = False

            async for output in kernel.execute(cell.source, timeout=timeout):
                cell.outputs.append(output)

                if output.output_type == "error":
                    has_error = True

                yield {
                    "type": "output",
                    "cell_id": cell_id,
                    "output": output.to_dict()
                }

            # Update cell status
            cell.status = "error" if has_error else "success"
            cell.execution_count = kernel.execution_count

            # Save notebook
            self.manager.save_notebook(self.notebook)

            # Format output summary for LLM
            output_summary = cell.get_output_text(max_length=1000)
            error_msg = cell.get_error()

            yield {
                "type": "execution_complete",
                "cell_id": cell_id,
                "status": cell.status,
                "execution_count": cell.execution_count,
                "output_summary": output_summary,
                "error": error_msg,
                "has_images": cell.has_images()
            }

        except Exception as e:
            cell.status = "error"
            error_output = CellOutput(
                output_type="error",
                ename=type(e).__name__,
                evalue=str(e),
                traceback=[f"{type(e).__name__}: {e}"]
            )
            cell.outputs.append(error_output)

            self.manager.save_notebook(self.notebook)

            logger.error(f"Cell execution failed: {e}")

            yield {
                "type": "execution_complete",
                "cell_id": cell_id,
                "status": "error",
                "error": str(e)
            }

    async def edit_cell(
        self,
        cell_id: str,
        source: str
    ) -> ToolResult:
        """
        Edit a cell's source.

        Clears outputs and resets status (cell needs re-execution).

        Args:
            cell_id: ID of cell to edit
            source: New source content

        Returns:
            ToolResult
        """
        cell = self._find_cell(cell_id)
        if not cell:
            return ToolResult(
                success=False,
                data=None,
                error=f"Cell not found: {cell_id}"
            )

        try:
            old_source = cell.source
            cell.source = source
            cell.clear_outputs()  # Clear outputs since source changed

            self.manager.save_notebook(self.notebook)

            logger.info(f"Edited cell: {cell_id[:8]}")

            return ToolResult(
                success=True,
                data={
                    "cell_id": cell_id,
                    "cell_type": cell.cell_type
                },
                message=f"Cell {cell_id} updated. Use execute_cell(cell_id=\"{cell_id}\") to run the new code."
            )

        except Exception as e:
            logger.error(f"Failed to edit cell: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def delete_cell(self, cell_id: str) -> ToolResult:
        """
        Delete a cell from the notebook.

        Args:
            cell_id: ID of cell to delete

        Returns:
            ToolResult
        """
        cell = self._find_cell(cell_id)
        if not cell or not self.notebook.delete_cell(cell.id):
            return ToolResult(
                success=False,
                data=None,
                error=f"Cell not found: {cell_id}"
            )

        self.manager.save_notebook(self.notebook)

        logger.info(f"Deleted cell: {cell_id[:8]}")

        return ToolResult(
            success=True,
            data={"cell_id": cell_id},
            message=f"Cell {cell_id[:8]} deleted."
        )

    async def get_notebook_state(self) -> ToolResult:
        """
        Get current notebook state.

        Returns:
            ToolResult with NotebookState
        """
        state = self.manager.get_notebook_state(self.notebook)

        return ToolResult(
            success=True,
            data={
                "notebook_name": state.notebook_name,
                "total_cells": state.total_cells,
                "cells": state.cells_summary,
                "available_notebooks": state.available_notebooks
            },
            message=state.to_context_string()
        )

    async def get_cell(self, cell_id: str) -> ToolResult:
        """
        Get full content of a specific cell.

        Args:
            cell_id: ID of the cell (can be partial)

        Returns:
            ToolResult with complete cell content
        """
        # Find cell (support partial IDs)
        cell = self._find_cell(cell_id)

        if not cell:
            return ToolResult(
                success=False,
                data=None,
                error=f"Cell not found: {cell_id}"
            )

        # Format full output text
        output_text = cell.get_output_text(max_length=10000)  # Allow longer output for this tool
        error_text = cell.get_error()

        # Build readable content
        content_lines = [
            f"## Cell: {cell.id}",
            f"**Type**: {cell.cell_type}",
            f"**Status**: {cell.status}",
        ]

        if cell.execution_count:
            content_lines.append(f"**Execution Count**: [{cell.execution_count}]")

        content_lines.extend([
            "",
            "### Source Code",
            "```python" if cell.cell_type == "code" else "```markdown",
            cell.source,
            "```",
        ])

        if output_text:
            content_lines.extend([
                "",
                "### Output",
                "```",
                output_text,
                "```",
            ])

        if error_text:
            content_lines.extend([
                "",
                "### Error",
                "```",
                error_text,
                "```",
            ])

        if cell.has_images():
            content_lines.append("\n*(Cell contains image output)*")

        formatted_content = "\n".join(content_lines)

        return ToolResult(
            success=True,
            data={
                "cell_id": cell.id,
                "cell_type": cell.cell_type,
                "status": cell.status,
                "execution_count": cell.execution_count,
                "source": cell.source,
                "output": output_text,
                "error": error_text,
                "has_images": cell.has_images()
            },
            message=formatted_content
        )

    async def get_kernel_state(self) -> ToolResult:
        """
        Get current kernel state including all variables.

        Returns:
            ToolResult with KernelState information
        """
        try:
            kernel = await self._get_kernel()
            kernel_state = await kernel.get_kernel_variables()

            return ToolResult(
                success=True,
                data={
                    "is_alive": kernel_state.is_alive,
                    "execution_count": kernel_state.execution_count,
                    "variables": {
                        name: var.to_dict()
                        for name, var in kernel_state.variables.items()
                    }
                },
                message=kernel_state.to_context_string()
            )

        except Exception as e:
            logger.error(f"Failed to get kernel state: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def create_notebook(self, name: str) -> ToolResult:
        """
        Create a new notebook and switch to it.

        Args:
            name: Name for the new notebook

        Returns:
            ToolResult
        """
        try:
            # Create new notebook
            notebook = self.manager.create_notebook(name)

            # Switch to it
            self.set_notebook(notebook)
            self.manager.set_active_notebook(name)

            # Stop old kernel (new notebook gets fresh kernel)
            if self._kernel:
                old_path = self._kernel.notebook_path
                await KernelRegistry.stop_kernel(old_path)
                self._kernel = None

            logger.info(f"Created and switched to notebook: {name}")

            return ToolResult(
                success=True,
                data={
                    "notebook_name": notebook.name,
                    "notebook_path": notebook.path
                },
                message=f"Created new notebook '{name}' and switched to it."
            )

        except FileExistsError:
            return ToolResult(
                success=False,
                data=None,
                error=f"Notebook '{name}' already exists. Use switch_notebook to switch to it."
            )
        except Exception as e:
            logger.error(f"Failed to create notebook: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def switch_notebook(self, name: str) -> ToolResult:
        """
        Switch to a different notebook.

        Args:
            name: Name of notebook to switch to

        Returns:
            ToolResult
        """
        try:
            # Load the notebook
            notebook = self.manager.load_notebook(name)

            # Switch to it
            self.set_notebook(notebook)
            self.manager.set_active_notebook(name)

            # Stop old kernel
            if self._kernel:
                old_path = self._kernel.notebook_path
                await KernelRegistry.stop_kernel(old_path)
                self._kernel = None

            logger.info(f"Switched to notebook: {name}")

            state = self.manager.get_notebook_state(notebook)

            return ToolResult(
                success=True,
                data={
                    "notebook_name": notebook.name,
                    "notebook_path": notebook.path,
                    "total_cells": len(notebook.cells)
                },
                message=f"Switched to notebook '{name}'.\n\n{state.to_context_string()}"
            )

        except FileNotFoundError:
            available = self.manager.list_notebooks()
            return ToolResult(
                success=False,
                data={"available_notebooks": available},
                error=f"Notebook '{name}' not found. Available: {', '.join(available) if available else 'none'}"
            )
        except Exception as e:
            logger.error(f"Failed to switch notebook: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


    async def write_file(self, path: str, content: str) -> ToolResult:
        """
        Write content to a file in the workspace.

        Args:
            path: Relative path for the file
            content: Content to write

        Returns:
            ToolResult
        """
        import os
        from pathlib import Path

        try:
            # Security: ensure path is relative and within workspace
            if os.path.isabs(path):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Absolute paths are not allowed. Use a relative path."
                )

            # Normalize and validate path
            clean_path = os.path.normpath(path)
            if clean_path.startswith('..'):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Path cannot escape the workspace directory."
                )

            # Build full path
            workspace = Path(self.manager.get_workspace_path())
            full_path = workspace / clean_path

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            full_path.write_text(content, encoding='utf-8')

            logger.info(f"Wrote file: {clean_path} ({len(content)} bytes)")

            return ToolResult(
                success=True,
                data={
                    "path": clean_path,
                    "bytes_written": len(content)
                },
                message=f"Successfully wrote {len(content)} bytes to '{clean_path}'."
            )

        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def read_file(self, path: str) -> ToolResult:
        """
        Read content from a file in the workspace.

        Args:
            path: Relative path to the file

        Returns:
            ToolResult with file content
        """
        import os
        from pathlib import Path

        try:
            # Security: ensure path is relative and within workspace
            if os.path.isabs(path):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Absolute paths are not allowed. Use a relative path."
                )

            clean_path = os.path.normpath(path)
            if clean_path.startswith('..'):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Path cannot escape the workspace directory."
                )

            workspace = Path(self.manager.get_workspace_path())
            full_path = workspace / clean_path

            if not full_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {clean_path}"
                )

            if full_path.is_dir():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is a directory, not a file: {clean_path}"
                )

            # Read the file (limit size for safety)
            file_size = full_path.stat().st_size
            max_size = 100 * 1024  # 100KB limit

            if file_size > max_size:
                content = full_path.read_text(encoding='utf-8')[:max_size]
                content += f"\n\n... [truncated, file is {file_size} bytes]"
            else:
                content = full_path.read_text(encoding='utf-8')

            logger.info(f"Read file: {clean_path} ({file_size} bytes)")

            return ToolResult(
                success=True,
                data={
                    "path": clean_path,
                    "content": content,
                    "size": file_size
                },
                message=content
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data=None,
                error=f"Cannot read binary file: {path}"
            )
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


    async def final_answer(
        self,
        summary: str,
        outputs: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Signal task completion with a final summary.

        This is a special tool that signals the coder loop to stop.
        The summary will be used as the final response to the user.

        Args:
            summary: Summary of what was accomplished
            outputs: List of outputs created

        Returns:
            ToolResult (the coder loop handles the actual termination)
        """
        logger.info(f"final_answer called: {summary[:100]}...")

        return ToolResult(
            success=True,
            data={
                "summary": summary,
                "outputs": outputs or [],
                "is_final": True
            },
            message=f"Task complete.\n\n{summary}"
        )

    async def analyze_notebook(
        self,
        notebook_name: Optional[str] = None
    ) -> ToolResult:
        """
        Analyze a notebook to understand its structure and contents.

        Extracts:
        - Imports and libraries used
        - Data files loaded/created
        - Variable definitions and data flow
        - Visualization cells
        - Current state (executed vs pending)

        Args:
            notebook_name: Name of notebook to analyze (defaults to current)

        Returns:
            ToolResult with structured analysis
        """
        import re

        try:
            # Get notebook to analyze
            if notebook_name and notebook_name != self.notebook.name:
                try:
                    notebook = self.manager.load_notebook(notebook_name)
                except FileNotFoundError:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Notebook '{notebook_name}' not found"
                    )
            else:
                notebook = self.notebook

            # Collect analysis data
            imports = []
            data_files = {"loaded": [], "created": []}
            visualizations = []
            key_variables = []
            markdown_headings = []
            errors = []

            # Patterns for detection
            import_pattern = re.compile(r'^(?:import|from)\s+(\S+)', re.MULTILINE)
            read_file_pattern = re.compile(r'(?:pd\.read_|open\(|np\.load|json\.load|csv\.reader|read_csv|read_excel|read_json|load)\s*[\(\[\'"]([^\)\]\'"]+)', re.IGNORECASE)
            write_file_pattern = re.compile(r'(?:\.to_csv|\.to_excel|\.savefig|\.save|write\(|dump\(|\.to_json)\s*[\(\[\'"]([^\)\]\'"]+)', re.IGNORECASE)
            plot_patterns = [
                r'plt\.',
                r'\.plot\(',
                r'sns\.',
                r'fig,\s*ax',
                r'\.hist\(',
                r'\.scatter\(',
                r'\.bar\(',
            ]
            assignment_pattern = re.compile(r'^(\w+)\s*=', re.MULTILINE)
            heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)

            executed_count = 0
            error_count = 0

            for cell in notebook.cells:
                source = cell.source

                if cell.cell_type == "markdown":
                    # Extract headings
                    headings = heading_pattern.findall(source)
                    markdown_headings.extend(headings)
                    continue

                # Track execution status
                if cell.status == "success":
                    executed_count += 1
                elif cell.status == "error":
                    error_count += 1
                    error_msg = cell.get_error()
                    if error_msg:
                        errors.append({
                            "cell_id": cell.id[:8],
                            "error": error_msg
                        })

                # Extract imports
                found_imports = import_pattern.findall(source)
                for imp in found_imports:
                    # Get base module name
                    base_module = imp.split('.')[0]
                    if base_module not in imports:
                        imports.append(base_module)

                # Extract file operations
                loaded = read_file_pattern.findall(source)
                data_files["loaded"].extend([f for f in loaded if f not in data_files["loaded"]])

                created = write_file_pattern.findall(source)
                data_files["created"].extend([f for f in created if f not in data_files["created"]])

                # Check for visualizations
                for pattern in plot_patterns:
                    if re.search(pattern, source):
                        vis_type = "plot"
                        if 'hist' in pattern:
                            vis_type = "histogram"
                        elif 'scatter' in pattern:
                            vis_type = "scatter"
                        elif 'bar' in pattern:
                            vis_type = "bar chart"
                        elif 'sns' in pattern:
                            vis_type = "seaborn plot"
                        visualizations.append({
                            "cell_id": cell.id[:8],
                            "type": vis_type,
                            "has_output": cell.has_images()
                        })
                        break

                # Extract variable assignments (first few per cell)
                assignments = assignment_pattern.findall(source)
                for var in assignments[:3]:  # Limit per cell
                    if var not in ['_', '__'] and not var.startswith('_'):
                        if var not in key_variables:
                            key_variables.append(var)

            # Build analysis summary
            analysis = {
                "notebook_name": notebook.name,
                "total_cells": len(notebook.cells),
                "code_cells": len([c for c in notebook.cells if c.cell_type == "code"]),
                "markdown_cells": len([c for c in notebook.cells if c.cell_type == "markdown"]),
                "executed_cells": executed_count,
                "error_cells": error_count,
                "imports": imports[:20],  # Limit
                "data_files": data_files,
                "visualizations": visualizations,
                "key_variables": key_variables[:20],  # Limit
                "sections": markdown_headings[:10],  # Limit
                "errors": errors
            }

            # Build readable message
            lines = [
                f"## Notebook Analysis: {notebook.name}",
                "",
                f"**Structure**: {analysis['code_cells']} code cells, {analysis['markdown_cells']} markdown cells",
                f"**Execution State**: {executed_count} executed, {error_count} with errors",
            ]

            if markdown_headings:
                lines.append("")
                lines.append("**Sections**:")
                for heading in markdown_headings[:5]:
                    lines.append(f"  - {heading}")

            if imports:
                lines.append("")
                lines.append(f"**Libraries Used**: {', '.join(imports[:10])}")

            if data_files["loaded"]:
                lines.append("")
                lines.append("**Data Loaded**:")
                for f in data_files["loaded"][:5]:
                    lines.append(f"  - {f}")

            if data_files["created"]:
                lines.append("")
                lines.append("**Files Created**:")
                for f in data_files["created"][:5]:
                    lines.append(f"  - {f}")

            if visualizations:
                lines.append("")
                lines.append(f"**Visualizations**: {len(visualizations)} plots/charts")

            if key_variables:
                lines.append("")
                lines.append(f"**Key Variables**: {', '.join(key_variables[:10])}")

            if errors:
                lines.append("")
                lines.append("**Errors to Fix**:")
                for err in errors:
                    lines.append(f"  - Cell {err['cell_id']}: {err['error']}")

            message = "\n".join(lines)

            logger.info(f"Analyzed notebook: {notebook.name}")

            return ToolResult(
                success=True,
                data=analysis,
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to analyze notebook: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


def get_tool_names() -> List[str]:
    """Get list of available tool names."""
    return [t["function"]["name"] for t in CODER_TOOLS_SCHEMA]
