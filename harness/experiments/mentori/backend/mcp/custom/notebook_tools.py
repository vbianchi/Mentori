# backend/mcp/custom/notebook_tools.py
"""
Notebook inspection and editing tools for the lead_researcher orchestrator.

These tools allow the orchestrator to READ and WRITE notebook cells — reading
what the coder agent produced and editing cells with properly formatted code.

Architecture note:
  The coder agent has NATIVE (in-process) access to NotebookKernel and
  NotebookManager and doesn't need MCP tools. These tools bridge the GAP:

      Coder executes cells →  .ipynb file on disk  → orchestrator reads/writes via these tools

  WHY write_notebook_cell instead of run_bash:
    run_bash JSON-encodes the source string, which collapses \n into spaces
    and breaks multi-line code. write_notebook_cell uses NotebookManager
    (Python API) which handles source strings natively with correct line breaks.

All tools are READ-ONLY (no kernel interaction). They parse the .ipynb JSON
and return human-readable summaries the orchestrator can reason over.

Usage examples:
  list_notebooks()
      → "analysis.ipynb, figures.ipynb"

  read_notebook("analysis.ipynb")
      → Full markdown: cells, source, truncated outputs

  get_notebook_cell("analysis.ipynb", "3f5901c1")
      → Source + all outputs of that cell
"""

import json
from pathlib import Path
from typing import Optional

from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# Max characters to include per output before truncating
_OUTPUT_TRUNCATE_CHARS = 2000
# Max characters for full notebook read (protect context window)
_NOTEBOOK_MAX_CHARS = 12000


def _format_cell_output(outputs: list, truncate: int = _OUTPUT_TRUNCATE_CHARS) -> str:
    """Render cell outputs to a compact human-readable string."""
    if not outputs:
        return ""

    parts = []
    for out in outputs:
        otype = out.get("output_type", "")
        if otype == "stream":
            text = "".join(out.get("text", "")) if isinstance(out.get("text"), list) else out.get("text", "")
            if text:
                parts.append(f"[stdout]\n{text[:truncate]}")
        elif otype == "error":
            ename = out.get("ename", "Error")
            evalue = out.get("evalue", "")
            tb = out.get("traceback", [])
            # Strip ANSI from traceback
            clean_tb = "\n".join(
                line.encode("ascii", "ignore").decode() for line in tb[:5]
            )
            parts.append(f"[error] {ename}: {evalue}\n{clean_tb}")
        elif otype in ("execute_result", "display_data"):
            data = out.get("data", {})
            # Prefer text/plain; note image presence but don't include base64
            if "text/plain" in data:
                text = "".join(data["text/plain"]) if isinstance(data["text/plain"], list) else data["text/plain"]
                parts.append(f"[result]\n{text[:truncate]}")
            elif "text/html" in data:
                html = "".join(data["text/html"]) if isinstance(data["text/html"], list) else data["text/html"]
                parts.append(f"[html output — {len(html)} chars]")
            if "image/png" in data or "image/jpeg" in data or "image/svg+xml" in data:
                parts.append("[image output — use Vision tools to analyse]")
    return "\n".join(parts)


def _load_notebook_json(workspace_path: str, notebook_name: str) -> dict:
    """Load raw .ipynb JSON. Raises FileNotFoundError if not found."""
    name = notebook_name.replace(".ipynb", "")
    nb_path = Path(workspace_path) / "notebooks" / f"{name}.ipynb"
    if not nb_path.exists():
        raise FileNotFoundError(
            f"Notebook '{name}.ipynb' not found in {workspace_path}/notebooks/. "
            f"Use list_notebooks() to see available notebooks."
        )
    with open(nb_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Tools ────────────────────────────────────────────────────────────────────

@mentori_tool(
    category="notebook",
    agent_role=None,
    is_llm_based=False,
    secrets=["workspace_path"],
)
def list_notebooks(workspace_path: str = None) -> str:
    """
    List all Jupyter notebooks in the current task workspace.

    Returns the names of all .ipynb files, their kernel, and cell counts.
    Call this first to discover which notebooks the coder agent has created.

    Returns:
        Human-readable list of notebooks with metadata.
    """
    if not workspace_path:
        return "[Error] workspace_path not available."

    nb_dir = Path(workspace_path) / "notebooks"
    if not nb_dir.exists():
        return "No notebooks directory found. The coder agent has not created any notebooks yet."

    notebooks = sorted(nb_dir.glob("*.ipynb"))
    if not notebooks:
        return "No notebooks found in this task workspace yet."

    lines = [f"# Notebooks in this task workspace\n"]
    for nb_path in notebooks:
        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                nb = json.load(f)
            cells = nb.get("cells", [])
            code_cells = sum(1 for c in cells if c.get("cell_type") == "code")
            kernel = nb.get("metadata", {}).get("kernelspec", {}).get("display_name", "unknown")
            executed = sum(
                1 for c in cells
                if c.get("cell_type") == "code" and c.get("execution_count") is not None
            )
            lines.append(
                f"- **{nb_path.stem}.ipynb**  |  kernel: {kernel}  "
                f"|  {len(cells)} cells ({code_cells} code, {executed} executed)"
            )
        except Exception as e:
            lines.append(f"- {nb_path.name} [error reading: {e}]")

    return "\n".join(lines)


@mentori_tool(
    category="notebook",
    agent_role=None,
    is_llm_based=False,
    secrets=["workspace_path"],
)
def read_notebook(
    notebook_name: str,
    workspace_path: str = None,
) -> str:
    """
    Read the full content of a Jupyter notebook as structured markdown.

    Returns all cells (source code + outputs) in readable form. Cell outputs
    are truncated to keep the response concise. Images are noted but not
    included (use Vision tools if you need to analyse a plot).

    Use this to understand what the coder agent computed, what errors occurred,
    and what results were produced.

    Args:
        notebook_name: Name of the notebook (with or without .ipynb extension)

    Returns:
        Markdown representation of the notebook with all cells and their outputs.
    """
    if not workspace_path:
        return "[Error] workspace_path not available."

    try:
        nb = _load_notebook_json(workspace_path, notebook_name)
    except FileNotFoundError as e:
        return f"[Error] {e}"

    cells = nb.get("cells", [])
    kernel = nb.get("metadata", {}).get("kernelspec", {}).get("display_name", "unknown")
    name = notebook_name.replace(".ipynb", "")

    lines = [
        f"# Notebook: {name}.ipynb",
        f"**Kernel:** {kernel}  |  **Cells:** {len(cells)}\n",
    ]

    for i, cell in enumerate(cells, 1):
        ctype = cell.get("cell_type", "code")
        cell_id = cell.get("id", "")[:8]
        exec_count = cell.get("execution_count")
        source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")

        status_tag = ""
        outputs = cell.get("outputs", [])
        has_error = any(o.get("output_type") == "error" for o in outputs)
        if has_error:
            status_tag = " ⚠ error"
        elif exec_count is not None:
            status_tag = " ✓ executed"

        exec_label = f"[{exec_count}]" if exec_count is not None else "[ ]"

        lines.append(f"## Cell {i} ({ctype}) {exec_label} id={cell_id}{status_tag}")

        if source.strip():
            lang = "r" if kernel.lower() == "r" or "ir" in kernel.lower() else "python"
            lines.append(f"```{lang if ctype == 'code' else 'markdown'}\n{source}\n```")
        else:
            lines.append("*(empty cell)*")

        if outputs:
            out_text = _format_cell_output(outputs)
            if out_text:
                lines.append(f"\n**Output:**\n{out_text}")

        lines.append("")  # blank line between cells

    full = "\n".join(lines)

    # Protect context window for very large notebooks
    if len(full) > _NOTEBOOK_MAX_CHARS:
        full = (
            full[:_NOTEBOOK_MAX_CHARS]
            + f"\n\n[... notebook truncated at {_NOTEBOOK_MAX_CHARS} chars. "
            f"Use get_notebook_cell() to read specific cells.]"
        )

    return full


@mentori_tool(
    category="notebook",
    agent_role=None,
    is_llm_based=False,
    secrets=["workspace_path"],
)
def get_notebook_cell(
    notebook_name: str,
    cell_id: str,
    workspace_path: str = None,
) -> str:
    """
    Get the full source and all outputs of a specific notebook cell by its ID.

    Cell IDs are the short hex strings shown in the notebook viewer (e.g. "3f5901c1").
    Use list_notebooks() + read_notebook() to discover cell IDs first.

    Args:
        notebook_name: Name of the notebook (with or without .ipynb extension)
        cell_id: Cell ID (full UUID or the first 8 characters shown in the viewer)

    Returns:
        Cell source code and all outputs in readable form.
    """
    if not workspace_path:
        return "[Error] workspace_path not available."

    try:
        nb = _load_notebook_json(workspace_path, notebook_name)
    except FileNotFoundError as e:
        return f"[Error] {e}"

    cells = nb.get("cells", [])
    kernel = nb.get("metadata", {}).get("kernelspec", {}).get("display_name", "unknown")

    # Match by full ID or prefix
    matched = None
    for cell in cells:
        cid = cell.get("id", "")
        if cid == cell_id or cid.startswith(cell_id):
            matched = cell
            break

    if not matched:
        # Also try by 0-based index if the user passed a number
        if cell_id.isdigit():
            idx = int(cell_id)
            if 0 <= idx < len(cells):
                matched = cells[idx]

    if not matched:
        available = ", ".join(c.get("id", "")[:8] for c in cells[:10])
        return (
            f"[Error] Cell '{cell_id}' not found in {notebook_name}.\n"
            f"Available cell IDs (first 8 chars): {available}\n"
            f"Tip: Use read_notebook('{notebook_name}') to see all cell IDs."
        )

    ctype = matched.get("cell_type", "code")
    full_id = matched.get("id", cell_id)
    exec_count = matched.get("execution_count")
    source = "".join(matched.get("source", [])) if isinstance(matched.get("source"), list) else matched.get("source", "")
    outputs = matched.get("outputs", [])

    lang = "r" if kernel.lower() == "r" or "ir" in kernel.lower() else "python"
    exec_label = f"[{exec_count}]" if exec_count is not None else "[ ]"

    lines = [
        f"# Cell {exec_label}  |  type={ctype}  |  id={full_id}  |  kernel={kernel}",
        "",
        f"## Source",
        f"```{lang if ctype == 'code' else 'markdown'}\n{source}\n```",
    ]

    if outputs:
        out_text = _format_cell_output(outputs, truncate=4000)
        lines.append(f"\n## Output\n{out_text}")
    else:
        lines.append("\n## Output\n*(no output — cell not yet executed or markdown cell)*")

    return "\n".join(lines)


@mentori_tool(
    category="notebook",
    agent_role=None,
    is_llm_based=False,
    secrets=["workspace_path", "task_id"],
)
def write_notebook_cell(
    notebook_name: str,
    cell_id: str,
    source: str,
    workspace_path: str = None,
    task_id: str = None,
) -> str:
    """
    Update the source code of an existing notebook cell, preserving correct line breaks.

    Use this instead of run_bash for cell modifications. run_bash JSON-encodes
    the source string which collapses newlines into spaces and breaks multi-line
    code. This tool uses NotebookManager (Python API) which handles source
    strings natively.

    The cell's previous outputs are cleared (cell must be re-executed to
    generate new output).

    Args:
        notebook_name: Name of the notebook (with or without .ipynb extension)
        cell_id: Cell ID (full UUID or the 8-char prefix shown in the viewer)
        source: New source code for the cell (plain multi-line string)

    Returns:
        Confirmation message with cell ID and notebook name.
    """
    if not workspace_path:
        return "[Error] workspace_path not available."

    try:
        from backend.agents.notebook.manager import NotebookManager
    except ImportError as e:
        return f"[Error] Cannot import NotebookManager: {e}"

    try:
        manager = NotebookManager(workspace_path, task_id or "unknown")
        notebook = manager.load_notebook(notebook_name)
    except FileNotFoundError:
        return (
            f"[Error] Notebook '{notebook_name}' not found. "
            f"Use list_notebooks() to see available notebooks."
        )
    except Exception as e:
        return f"[Error] Failed to load notebook: {e}"

    # Find cell by full ID or prefix
    matched = None
    for cell in notebook.cells:
        if cell.id == cell_id or cell.id.startswith(cell_id):
            matched = cell
            break

    if not matched and cell_id.isdigit():
        idx = int(cell_id)
        if 0 <= idx < len(notebook.cells):
            matched = notebook.cells[idx]

    if not matched:
        available = ", ".join(c.id[:8] for c in notebook.cells[:10])
        return (
            f"[Error] Cell '{cell_id}' not found in '{notebook_name}'.\n"
            f"Available cell IDs (first 8 chars): {available}"
        )

    full_id = matched.id
    matched.source = source
    matched.clear_outputs()
    matched.status = "idle"

    try:
        manager.save_notebook(notebook)
    except Exception as e:
        return f"[Error] Failed to save notebook: {e}"

    line_count = source.count('\n') + 1
    logger.info(
        f"[NOTEBOOK_WRITE] Updated cell {full_id[:8]} in {notebook_name} "
        f"({line_count} lines)"
    )
    return (
        f"Cell {full_id[:8]} in '{notebook_name}' updated successfully "
        f"({line_count} lines). Outputs cleared — use the Run button or "
        f"run_notebook_cell to execute."
    )


@mentori_tool(
    category="notebook",
    agent_role=None,
    is_llm_based=False,
    secrets=["workspace_path", "task_id"],
)
def add_notebook_cell(
    notebook_name: str,
    source: str,
    cell_type: str = "code",
    workspace_path: str = None,
    task_id: str = None,
) -> str:
    """
    Append a new cell to the end of a notebook with correctly formatted source code.

    Use this instead of run_bash to add new cells. Preserves all newlines and
    indentation in the source string.

    Args:
        notebook_name: Name of the notebook (with or without .ipynb extension)
        source: Source code or markdown text for the new cell
        cell_type: "code" (default) or "markdown"

    Returns:
        Confirmation with the new cell's ID.
    """
    if not workspace_path:
        return "[Error] workspace_path not available."

    if cell_type not in ("code", "markdown"):
        return "[Error] cell_type must be 'code' or 'markdown'."

    try:
        from backend.agents.notebook.manager import NotebookManager
    except ImportError as e:
        return f"[Error] Cannot import NotebookManager: {e}"

    try:
        manager = NotebookManager(workspace_path, task_id or "unknown")
        notebook = manager.load_notebook(notebook_name)
    except FileNotFoundError:
        return (
            f"[Error] Notebook '{notebook_name}' not found. "
            f"Use list_notebooks() to see available notebooks."
        )
    except Exception as e:
        return f"[Error] Failed to load notebook: {e}"

    try:
        cell = notebook.add_cell(source=source, cell_type=cell_type)
        manager.save_notebook(notebook)
    except Exception as e:
        return f"[Error] Failed to add cell: {e}"

    line_count = source.count('\n') + 1
    logger.info(
        f"[NOTEBOOK_ADD] Added {cell_type} cell {cell.id[:8]} to {notebook_name} "
        f"({line_count} lines)"
    )
    return (
        f"New {cell_type} cell added to '{notebook_name}'. "
        f"Cell ID: {cell.id} | {line_count} lines. "
        f"Use the Run button or run_notebook_cell to execute."
    )
