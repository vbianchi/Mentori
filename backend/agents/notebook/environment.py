"""
Environment gathering for Notebook Coder V2.

Inspects the workspace filesystem to provide the LLM with information
about available data files (paths, shapes, column names, dtypes).
No LLM call — pure filesystem inspection.
"""

import logging
from pathlib import Path
from typing import Optional

from backend.agents.orchestrator.prompts import format_workspace_files

logger = logging.getLogger(__name__)

# Data file extensions to inspect with pandas
DATA_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet"}

# Maximum number of data files to preview
MAX_DATA_FILES = 20


def gather_environment(workspace_path: Path, user_request: str = "") -> str:
    """
    Gather workspace environment information for the coder LLM.

    Lists all workspace files and reads shape/columns/dtypes for data files.
    Pure filesystem operation — no LLM call.

    Args:
        workspace_path: Path to the task workspace directory.
        user_request: The user's request (unused for now, reserved for future filtering).

    Returns:
        Formatted string with workspace files and data file details.
    """
    parts = []

    # Section 1: All workspace files (reuse orchestrator helper)
    file_listing = format_workspace_files(str(workspace_path))
    parts.append(f"## Workspace Files (on disk — NOT yet loaded in kernel)\n{file_listing}")

    # Section 2: Data file details (shape, columns, dtypes)
    data_files = _find_data_files(workspace_path)

    if data_files:
        details = []
        for path in data_files[:MAX_DATA_FILES]:
            detail = _inspect_data_file(path, workspace_path)
            if detail:
                details.append(detail)

        if details:
            parts.append("\n## Data File Details\n" + "\n".join(details))

    return "\n\n".join(parts)


def _find_data_files(workspace_path: Path) -> list:
    """Find data files in workspace root, files/, and data/ subdirectories."""
    search_dirs = [
        workspace_path,
        workspace_path / "files",
        workspace_path / "data",
    ]

    seen = set()
    data_files = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in sorted(search_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in DATA_EXTENSIONS:
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    data_files.append(path)

    return data_files


def _inspect_data_file(path: Path, workspace_path: Path) -> Optional[str]:
    """Read shape, columns, and dtypes from a single data file."""
    try:
        import pandas as pd

        rel_path = path.relative_to(workspace_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(path, nrows=0)
            nrows = sum(1 for _ in open(path)) - 1  # fast row count
            shape_str = f"{nrows} rows x {len(df.columns)} columns"
        elif suffix == ".tsv":
            df = pd.read_csv(path, sep="\t", nrows=0)
            nrows = sum(1 for _ in open(path)) - 1
            shape_str = f"{nrows} rows x {len(df.columns)} columns"
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(path, nrows=0)
            # For Excel, read full to get row count
            df_full = pd.read_excel(path)
            shape_str = f"{len(df_full)} rows x {len(df_full.columns)} columns"
        elif suffix == ".json":
            df = pd.read_json(path)
            shape_str = f"{len(df)} rows x {len(df.columns)} columns"
        elif suffix == ".parquet":
            df = pd.read_parquet(path)
            shape_str = f"{len(df)} rows x {len(df.columns)} columns"
        else:
            return None

        # Build columns + dtypes string
        col_dtypes = [f"{col} ({df[col].dtype})" for col in df.columns]
        cols_str = ", ".join(col_dtypes)

        return f"### {rel_path} (ON DISK — must be loaded with pd.read_csv() or similar)\nShape: {shape_str}\nColumns: {cols_str}"

    except Exception as e:
        rel_path = path.relative_to(workspace_path)
        logger.warning(f"Failed to inspect {rel_path}: {e}")
        return f"### {rel_path}\n(Could not read: {e})"
