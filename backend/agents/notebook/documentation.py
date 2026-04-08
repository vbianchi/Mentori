"""
Documentation Generator for Notebook Coder V2.

Handles automatic export of notebooks to HTML/Markdown formats
and generation of summary cells.
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.schema import Algorithm, Notebook
    from backend.agents.notebook.cell_registry import CellRegistry

logger = logging.getLogger(__name__)


async def export_notebook(
    notebook_path: Path,
    output_dir: Path,
    formats: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """
    Export notebook to various formats using nbconvert.

    Args:
        notebook_path: Path to the .ipynb file
        output_dir: Directory to save exports
        formats: List of formats to export ("html", "markdown", "pdf")
                 Defaults to ["html"]

    Returns:
        Dict mapping format -> output file path
    """
    if formats is None:
        formats = ["html"]

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}

    for fmt in formats:
        try:
            output_path = await _run_nbconvert(notebook_path, output_dir, fmt)
            if output_path and output_path.exists():
                outputs[fmt] = output_path
                logger.info(f"Exported notebook to {fmt}: {output_path}")
        except Exception as e:
            logger.warning(f"Failed to export notebook to {fmt}: {e}")

    return outputs


async def _run_nbconvert(
    notebook_path: Path,
    output_dir: Path,
    fmt: str,
) -> Optional[Path]:
    """Run nbconvert in subprocess."""
    # Map format to nbconvert template
    format_map = {
        "html": "html",
        "markdown": "markdown",
        "md": "markdown",
        "pdf": "pdf",
        "latex": "latex",
        "script": "script",
    }

    nbconvert_format = format_map.get(fmt.lower(), fmt)
    output_name = notebook_path.stem

    # Build command
    cmd = [
        "jupyter", "nbconvert",
        "--to", nbconvert_format,
        "--output-dir", str(output_dir),
        "--output", output_name,
        str(notebook_path),
    ]

    # Add format-specific options
    if nbconvert_format == "html":
        cmd.extend(["--template", "classic"])  # Clean HTML template

    try:
        # Run in thread pool to avoid blocking
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.warning(f"nbconvert stderr: {result.stderr}")
            return None

        # Determine output file extension
        ext_map = {
            "html": ".html",
            "markdown": ".md",
            "pdf": ".pdf",
            "latex": ".tex",
            "script": ".py",
        }
        ext = ext_map.get(nbconvert_format, f".{fmt}")
        output_path = output_dir / f"{output_name}{ext}"

        return output_path if output_path.exists() else None

    except subprocess.TimeoutExpired:
        logger.warning(f"nbconvert timed out for {notebook_path}")
        return None
    except FileNotFoundError:
        logger.warning("jupyter nbconvert not found, skipping export")
        return None


def generate_summary_markdown(
    algorithm: "Algorithm",
    cell_registry: "CellRegistry",
    execution_time: float,
) -> str:
    """
    Generate summary markdown content for the final notebook cell.

    Args:
        algorithm: The algorithm that was executed
        cell_registry: Registry of cells created
        execution_time: Total execution time in seconds

    Returns:
        Markdown string for summary cell
    """
    lines = [
        "---",
        "",
        "## Summary",
        "",
        f"**Task**: {algorithm.task_summary}",
        "",
    ]

    # Steps completed
    if algorithm.steps:
        completed = sum(
            1 for step in algorithm.steps
            if cell_registry.get_entry_by_step(step.step_number)
        )
        lines.append(f"**Steps completed**: {completed}/{len(algorithm.steps)}")
        lines.append("")

    # Cells created
    if cell_registry:
        lines.append(f"**Cells created**: {len(cell_registry)}")
        lines.append("")

    # Key variables
    all_vars = cell_registry.get_all_variables()
    if all_vars:
        lines.append("**Key variables**:")
        for var in all_vars[:10]:
            lines.append(f"- `{var}`")
        lines.append("")

    # Files created
    all_files = cell_registry.get_all_files()
    if all_files:
        lines.append("**Files created**:")
        for f in all_files:
            lines.append(f"- `{f}`")
        lines.append("")

    # Expected output
    if algorithm.expected_final_output:
        lines.append(f"**Expected output**: {algorithm.expected_final_output}")
        lines.append("")

    # Execution info
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    if execution_time > 0:
        mins, secs = divmod(int(execution_time), 60)
        time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        lines.append(f"*Execution time: {time_str}*")

    return "\n".join(lines)


async def add_summary_cell(
    notebook: "Notebook",
    notebook_manager: "NotebookManager",
    algorithm: "Algorithm",
    cell_registry: "CellRegistry",
    execution_time: float = 0.0,
) -> Any:
    """
    Add a summary markdown cell to the end of the notebook.

    Args:
        notebook: The notebook to add cell to
        notebook_manager: Notebook manager instance
        algorithm: Algorithm that was executed
        cell_registry: Registry of created cells
        execution_time: Total execution time

    Returns:
        The created cell
    """
    content = generate_summary_markdown(algorithm, cell_registry, execution_time)

    cell = notebook.add_cell(content, "markdown")
    notebook_manager.save_notebook(notebook)

    logger.info("Added summary cell to notebook")
    return cell


def generate_report_markdown(
    algorithm: "Algorithm",
    cell_registry: "CellRegistry",
    notebook_path: Path,
) -> str:
    """
    Generate a standalone markdown report from the notebook execution.

    This creates a report that can be shared separately from the notebook.

    Args:
        algorithm: Algorithm that was executed
        cell_registry: Registry of created cells
        notebook_path: Path to the notebook file

    Returns:
        Complete markdown report as string
    """
    lines = [
        f"# Analysis Report: {algorithm.task_summary}",
        "",
        f"*Generated from: `{notebook_path.name}`*",
        f"*Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
    ]

    # Approach section
    lines.append("## Approach")
    lines.append("")
    for step in algorithm.steps:
        lines.append(f"### Step {step.step_number}: {step.description}")
        lines.append("")

        # Check if this step was executed
        entry = cell_registry.get_entry_by_step(step.step_number)
        if entry:
            status = "✅" if entry.evaluation_score >= 70 else "⚠️" if entry.evaluation_score >= 50 else "❌"
            lines.append(f"**Status**: {status} (Score: {entry.evaluation_score})")
            if entry.actual_output_summary:
                lines.append(f"**Result**: {entry.actual_output_summary}")
            if entry.files_created:
                lines.append(f"**Files**: {', '.join(entry.files_created)}")
        else:
            lines.append("**Status**: Not executed")
        lines.append("")

    # Results section
    lines.append("## Results")
    lines.append("")

    # Variables created
    all_vars = cell_registry.get_all_variables()
    if all_vars:
        lines.append("### Variables")
        lines.append("")
        lines.append("| Variable | Created by |")
        lines.append("|----------|------------|")
        for entry in cell_registry.entries.values():
            for var in entry.variables_created:
                lines.append(f"| `{var}` | Step {entry.algorithm_step} |")
        lines.append("")

    # Files created
    all_files = cell_registry.get_all_files()
    if all_files:
        lines.append("### Artifacts")
        lines.append("")
        for entry in cell_registry.entries.values():
            for f in entry.files_created:
                lines.append(f"- **`{f}`** - Created in Step {entry.algorithm_step}: {entry.purpose}")
        lines.append("")

    # Conclusion
    if algorithm.expected_final_output:
        lines.append("## Expected Output")
        lines.append("")
        lines.append(algorithm.expected_final_output)
        lines.append("")

    return "\n".join(lines)


async def save_report(
    algorithm: "Algorithm",
    cell_registry: "CellRegistry",
    notebook_path: Path,
    output_dir: Path,
) -> Path:
    """
    Save a standalone markdown report.

    Args:
        algorithm: Algorithm that was executed
        cell_registry: Registry of created cells
        notebook_path: Path to the notebook
        output_dir: Directory to save report

    Returns:
        Path to the saved report
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    report_content = generate_report_markdown(algorithm, cell_registry, notebook_path)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"report_{notebook_path.stem}_{timestamp}.md"
    report_path = output_dir / report_name

    report_path.write_text(report_content)
    logger.info(f"Saved report to {report_path}")

    return report_path


def check_nbconvert_available() -> bool:
    """Check if nbconvert is available."""
    try:
        result = subprocess.run(
            ["jupyter", "nbconvert", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
