# backend/agents/notebook/manager.py
"""
Notebook file management for the coder agent.

Handles loading, saving, creating, and tracking notebooks for tasks.
Notebooks are stored as .ipynb files in the task workspace.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import nbformat
from nbformat import v4 as nbf

from backend.agents.notebook.schema import Notebook, Cell, NotebookState
from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# File to track active notebook for a task
ACTIVE_NOTEBOOK_FILE = ".active_notebook"


class NotebookManager:
    """
    Manages notebook files for a task.

    Handles:
    - Creating new notebooks
    - Loading/saving .ipynb files
    - Tracking active notebook per task
    - Listing available notebooks
    """

    def __init__(self, workspace_path: str, task_id: str):
        """
        Initialize notebook manager.

        Args:
            workspace_path: Root path of the task workspace
            task_id: Task identifier (used for default notebook naming)
        """
        self.workspace_path = Path(workspace_path)
        self.task_id = task_id
        self.notebooks_dir = self.workspace_path / "notebooks"

        # Ensure notebooks directory exists
        self.notebooks_dir.mkdir(parents=True, exist_ok=True)

    def _generate_default_name(self) -> str:
        """Generate default notebook name: {task_id}_{date}.ipynb"""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{self.task_id}_{date_str}"

    def _get_notebook_path(self, name: str) -> Path:
        """Get full path for a notebook by name (without .ipynb extension)."""
        # Remove .ipynb if provided
        name = name.replace(".ipynb", "")
        return self.notebooks_dir / f"{name}.ipynb"

    def _get_relative_path(self, name: str) -> str:
        """Get relative path for a notebook (for storage in Notebook.path)."""
        name = name.replace(".ipynb", "")
        return f"notebooks/{name}.ipynb"

    def get_or_create_default(self) -> Notebook:
        """
        Get active notebook or create a default one.

        Returns the currently active notebook for this task.
        If no notebook exists, creates one with the default name.
        """
        # Check for active notebook
        active_name = self.get_active_notebook_name()

        if active_name:
            # Try to load it
            try:
                return self.load_notebook(active_name)
            except FileNotFoundError:
                logger.warning(f"Active notebook '{active_name}' not found, creating new")

        # No active notebook or it was deleted - create default
        default_name = self._generate_default_name()

        # Check if default already exists
        if self._get_notebook_path(default_name).exists():
            notebook = self.load_notebook(default_name)
        else:
            notebook = self.create_notebook(default_name)

        # Set as active
        self.set_active_notebook(default_name)

        return notebook

    def create_notebook(self, name: str) -> Notebook:
        """
        Create a new empty notebook.

        Args:
            name: Notebook name (without .ipynb extension)

        Returns:
            New Notebook instance
        """
        name = name.replace(".ipynb", "")
        path = self._get_notebook_path(name)
        relative_path = self._get_relative_path(name)

        if path.exists():
            raise FileExistsError(f"Notebook '{name}' already exists")

        logger.info(f"Creating new notebook: {name}")

        notebook = Notebook(
            path=relative_path,
            name=name,
            cells=[],
            created_at=datetime.now(),
            modified_at=datetime.now()
        )

        # Save immediately
        self.save_notebook(notebook)

        return notebook

    def load_notebook(self, name: str) -> Notebook:
        """
        Load a notebook from .ipynb file.

        Args:
            name: Notebook name (with or without .ipynb extension)

        Returns:
            Notebook instance
        """
        name = name.replace(".ipynb", "")
        path = self._get_notebook_path(name)
        relative_path = self._get_relative_path(name)

        if not path.exists():
            raise FileNotFoundError(f"Notebook '{name}' not found at {path}")

        logger.info(f"Loading notebook: {name}")

        with open(path, "r", encoding="utf-8") as f:
            nb_data = nbformat.read(f, as_version=4)

        # Convert nbformat to our Notebook class
        notebook = Notebook.from_nbformat(
            data=nb_data,
            path=relative_path,
            name=name
        )

        return notebook

    def save_notebook(self, notebook: Notebook) -> None:
        """
        Save a notebook to .ipynb file.

        Args:
            notebook: Notebook instance to save
        """
        path = self._get_notebook_path(notebook.name)

        logger.debug(f"Saving notebook: {notebook.name}")

        # Update modified time
        notebook.modified_at = datetime.now()

        # Convert to nbformat
        nb_data = notebook.to_nbformat()

        # Validate notebook
        try:
            nbformat.validate(nb_data)
        except nbformat.ValidationError as e:
            logger.warning(f"Notebook validation warning: {e}")
            # Continue anyway - minor validation issues are ok

        # Write with nbformat to ensure proper format
        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(nbformat.from_dict(nb_data), f)

    def delete_notebook(self, name: str) -> bool:
        """
        Delete a notebook file.

        Args:
            name: Notebook name

        Returns:
            True if deleted, False if not found
        """
        name = name.replace(".ipynb", "")
        path = self._get_notebook_path(name)

        if not path.exists():
            return False

        logger.info(f"Deleting notebook: {name}")
        path.unlink()

        # If this was the active notebook, clear active
        if self.get_active_notebook_name() == name:
            self._clear_active_notebook()

        return True

    def list_notebooks(self) -> List[str]:
        """
        List all notebooks in the task workspace.

        Returns:
            List of notebook names (without .ipynb extension)
        """
        notebooks = []

        for path in self.notebooks_dir.glob("*.ipynb"):
            notebooks.append(path.stem)  # Name without extension

        return sorted(notebooks)

    def notebook_exists(self, name: str) -> bool:
        """Check if a notebook exists."""
        name = name.replace(".ipynb", "")
        return self._get_notebook_path(name).exists()

    # Active notebook tracking

    def get_active_notebook_name(self) -> Optional[str]:
        """
        Get the name of the currently active notebook.

        Returns:
            Notebook name or None if no active notebook
        """
        active_file = self.workspace_path / ACTIVE_NOTEBOOK_FILE

        if not active_file.exists():
            return None

        try:
            with open(active_file, "r") as f:
                data = json.load(f)
                return data.get("name")
        except (json.JSONDecodeError, IOError):
            return None

    def set_active_notebook(self, name: str) -> None:
        """
        Set the active notebook for this task.

        Args:
            name: Notebook name to set as active
        """
        name = name.replace(".ipynb", "")
        active_file = self.workspace_path / ACTIVE_NOTEBOOK_FILE

        data = {
            "name": name,
            "set_at": datetime.now().isoformat()
        }

        with open(active_file, "w") as f:
            json.dump(data, f)

        logger.debug(f"Set active notebook: {name}")

    def _clear_active_notebook(self) -> None:
        """Clear the active notebook setting."""
        active_file = self.workspace_path / ACTIVE_NOTEBOOK_FILE

        if active_file.exists():
            active_file.unlink()

    # State generation

    def get_notebook_state(self, notebook: Notebook) -> NotebookState:
        """
        Get notebook state for LLM context injection.

        Args:
            notebook: Current notebook

        Returns:
            NotebookState snapshot
        """
        available = self.list_notebooks()

        return NotebookState.from_notebook(
            notebook=notebook,
            available_notebooks=available
        )

    # Utility methods

    def get_workspace_path(self) -> str:
        """Get the workspace path (for kernel working directory)."""
        return str(self.workspace_path)

    def get_full_notebook_path(self, name: str) -> str:
        """Get full absolute path to a notebook."""
        return str(self._get_notebook_path(name))
