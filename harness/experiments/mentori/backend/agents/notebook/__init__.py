# backend/agents/notebook/__init__.py
"""
Notebook-based Coder Agent package.

This package provides a Jupyter notebook-based coding environment
for the Mentori coder agent. It enables iterative, cell-by-cell
code execution with persistent kernel state.
"""

from backend.agents.notebook.schema import (
    Cell,
    CellOutput,
    Notebook,
    NotebookState,
    CellStatus,
    CellType,
    OutputType,
)
from backend.agents.notebook.kernel import NotebookKernel, KernelRegistry
from backend.agents.notebook.manager import NotebookManager
from backend.agents.notebook.coder_loop import coder_loop
from backend.agents.notebook.coder_v2 import coder_loop_v2

__all__ = [
    # Schema
    "Cell",
    "CellOutput",
    "Notebook",
    "NotebookState",
    "CellStatus",
    "CellType",
    "OutputType",
    # Kernel
    "NotebookKernel",
    "KernelRegistry",
    # Manager
    "NotebookManager",
    # Loop
    "coder_loop",
    "coder_loop_v2",
]
