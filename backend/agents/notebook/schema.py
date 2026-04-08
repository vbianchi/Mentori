# backend/agents/notebook/schema.py
"""
Data models for the notebook-based coder agent.

These models represent the in-memory state of notebooks, cells,
and outputs. They are converted to/from nbformat for persistence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import uuid


# Type aliases for clarity
CellStatus = Literal["idle", "queued", "running", "success", "error"]
CellType = Literal["code", "markdown"]
OutputType = Literal["stream", "execute_result", "display_data", "error"]


@dataclass
class CellOutput:
    """
    Single output from a cell execution.

    Maps to nbformat output types:
    - stream: stdout/stderr text
    - execute_result: return value of last expression
    - display_data: rich display (images, HTML, etc.)
    - error: exception information
    """
    output_type: OutputType

    # Content data - keys are MIME types (text/plain, image/png, text/html, etc.)
    data: Dict[str, Any] = field(default_factory=dict)

    # For stream outputs
    stream_name: Optional[str] = None  # "stdout" or "stderr"
    text: Optional[str] = None  # Stream text content

    # For error outputs
    ename: Optional[str] = None  # Exception name (e.g., "ValueError")
    evalue: Optional[str] = None  # Exception value/message
    traceback: Optional[List[str]] = None  # Formatted traceback lines

    # Execution count (for execute_result)
    execution_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"output_type": self.output_type}

        if self.output_type == "stream":
            result["name"] = self.stream_name or "stdout"
            result["text"] = self.text or ""
        elif self.output_type == "error":
            result["ename"] = self.ename or "Error"
            result["evalue"] = self.evalue or ""
            result["traceback"] = self.traceback or []
        else:
            # execute_result or display_data
            result["data"] = self.data
            if self.execution_count is not None:
                result["execution_count"] = self.execution_count
            result["metadata"] = {}

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellOutput":
        """Create from dictionary (e.g., from nbformat)."""
        output_type = data.get("output_type", "stream")

        if output_type == "stream":
            return cls(
                output_type="stream",
                stream_name=data.get("name", "stdout"),
                text=data.get("text", "")
            )
        elif output_type == "error":
            return cls(
                output_type="error",
                ename=data.get("ename"),
                evalue=data.get("evalue"),
                traceback=data.get("traceback", [])
            )
        else:
            return cls(
                output_type=output_type,
                data=data.get("data", {}),
                execution_count=data.get("execution_count")
            )

    def get_text_content(self) -> str:
        """Get plain text representation of this output."""
        if self.output_type == "stream":
            return self.text or ""
        elif self.output_type == "error":
            return f"{self.ename}: {self.evalue}"
        else:
            # Prefer text/plain, fall back to other formats
            if "text/plain" in self.data:
                return self.data["text/plain"]
            elif "text/html" in self.data:
                return "[HTML output]"
            elif "image/png" in self.data or "image/jpeg" in self.data:
                return "[Image output]"
            return str(self.data)

    def has_image(self) -> bool:
        """Check if this output contains an image."""
        return any(
            mime in self.data
            for mime in ["image/png", "image/jpeg", "image/svg+xml"]
        )


@dataclass
class Cell:
    """
    A notebook cell (code or markdown).

    Maintains execution state and outputs for code cells.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cell_type: CellType = "code"
    source: str = ""
    outputs: List[CellOutput] = field(default_factory=list)
    execution_count: Optional[int] = None
    status: CellStatus = "idle"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_nbformat_cell(self) -> Dict[str, Any]:
        """Convert to nbformat cell dict."""
        cell = {
            "id": self.id,
            "cell_type": self.cell_type,
            "source": self.source,
            "metadata": {
                **self.metadata,
                "mentori_status": self.status  # Custom metadata
            }
        }

        if self.cell_type == "code":
            cell["execution_count"] = self.execution_count
            cell["outputs"] = [o.to_dict() for o in self.outputs]

        return cell

    @classmethod
    def from_nbformat_cell(cls, cell_data: Dict[str, Any]) -> "Cell":
        """Create from nbformat cell dict."""
        cell_type = cell_data.get("cell_type", "code")
        metadata = cell_data.get("metadata", {})
        status = metadata.pop("mentori_status", "idle")

        outputs = []
        if cell_type == "code":
            for out_data in cell_data.get("outputs", []):
                outputs.append(CellOutput.from_dict(out_data))

        return cls(
            id=cell_data.get("id", str(uuid.uuid4())),
            cell_type=cell_type,
            source=cell_data.get("source", ""),
            outputs=outputs,
            execution_count=cell_data.get("execution_count"),
            status=status,
            metadata=metadata
        )

    def clear_outputs(self) -> None:
        """Clear outputs and reset execution state."""
        self.outputs = []
        self.execution_count = None
        self.status = "idle"

    def get_output_text(self, max_length: int = 500) -> str:
        """Get combined text output, truncated if needed."""
        texts = []
        for output in self.outputs:
            text = output.get_text_content()
            if text:
                texts.append(text)

        combined = "\n".join(texts)
        if len(combined) > max_length:
            return combined[:max_length] + "... (truncated)"
        return combined

    def get_error(self) -> Optional[str]:
        """Get error message if cell failed."""
        for output in self.outputs:
            if output.output_type == "error":
                return f"{output.ename}: {output.evalue}"
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.to_nbformat_cell()

    def has_images(self) -> bool:
        """Check if any output contains images."""
        return any(o.has_image() for o in self.outputs)


@dataclass
class Notebook:
    """
    In-memory notebook representation.

    Manages cells and converts to/from .ipynb format.
    """
    path: str  # Relative path within task workspace (e.g., "notebooks/main.ipynb")
    name: str  # Display name (e.g., "main")
    cells: List[Cell] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    kernel_name: str = "python3"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure default metadata."""
        if "kernelspec" not in self.metadata:
            self.metadata["kernelspec"] = {
                "display_name": "Python 3",
                "language": "python",
                "name": self.kernel_name
            }
        if "language_info" not in self.metadata:
            self.metadata["language_info"] = {
                "name": "python",
                "version": "3.11"
            }

    def add_cell(
        self,
        source: str,
        cell_type: CellType = "code",
        position: Optional[int] = None
    ) -> Cell:
        """Add a new cell, optionally at a specific position."""
        cell = Cell(cell_type=cell_type, source=source)

        if position is None:
            self.cells.append(cell)
        else:
            self.cells.insert(position, cell)

        self.modified_at = datetime.now()
        return cell

    def get_cell(self, cell_id: str) -> Optional[Cell]:
        """Find cell by ID."""
        for cell in self.cells:
            if cell.id == cell_id:
                return cell
        return None

    def get_cell_index(self, cell_id: str) -> Optional[int]:
        """Get index of cell by ID."""
        for i, cell in enumerate(self.cells):
            if cell.id == cell_id:
                return i
        return None

    def delete_cell(self, cell_id: str) -> bool:
        """Delete cell by ID. Returns True if found and deleted."""
        for i, cell in enumerate(self.cells):
            if cell.id == cell_id:
                self.cells.pop(i)
                self.modified_at = datetime.now()
                return True
        return False

    def to_nbformat(self) -> Dict[str, Any]:
        """Convert to nbformat v4 notebook dict."""
        return {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": self.metadata,
            "cells": [cell.to_nbformat_cell() for cell in self.cells]
        }

    @classmethod
    def from_nbformat(cls, data: Dict[str, Any], path: str, name: str) -> "Notebook":
        """Create from nbformat dict."""
        cells = [
            Cell.from_nbformat_cell(c)
            for c in data.get("cells", [])
        ]

        return cls(
            path=path,
            name=name,
            cells=cells,
            metadata=data.get("metadata", {}),
            kernel_name=data.get("metadata", {}).get("kernelspec", {}).get("name", "python3")
        )

    def get_code_cells(self) -> List[Cell]:
        """Get only code cells."""
        return [c for c in self.cells if c.cell_type == "code"]

    def get_last_error(self) -> Optional[str]:
        """Get the most recent error from any cell."""
        for cell in reversed(self.cells):
            error = cell.get_error()
            if error:
                return error
        return None


@dataclass
class NotebookState:
    """
    Notebook state snapshot for injecting into LLM context.

    This is a condensed view of the notebook that gives the agent
    enough information to reason about what to do next.
    """
    notebook_name: str
    notebook_path: str
    total_cells: int
    cells_summary: List[Dict[str, Any]]  # Condensed cell info
    last_execution_error: Optional[str] = None
    available_notebooks: List[str] = field(default_factory=list)

    @classmethod
    def from_notebook(
        cls,
        notebook: Notebook,
        available_notebooks: Optional[List[str]] = None,
        max_source_preview: int = 100,
        max_output_preview: int = 200
    ) -> "NotebookState":
        """Create state snapshot from a notebook."""
        cells_summary = []

        for cell in notebook.cells:
            # Truncate source for preview
            source_preview = cell.source
            if len(source_preview) > max_source_preview:
                source_preview = source_preview[:max_source_preview] + "..."

            # Get output preview
            output_preview = cell.get_output_text(max_output_preview)

            summary = {
                "id": cell.id,
                "cell_type": cell.cell_type,
                "status": cell.status,
                "source": source_preview,
                "execution_count": cell.execution_count,
                "has_output": len(cell.outputs) > 0,
                "output_preview": output_preview if output_preview else None,
                "error": cell.get_error(),
                "has_images": cell.has_images()
            }
            cells_summary.append(summary)

        return cls(
            notebook_name=notebook.name,
            notebook_path=notebook.path,
            total_cells=len(notebook.cells),
            cells_summary=cells_summary,
            last_execution_error=notebook.get_last_error(),
            available_notebooks=available_notebooks or []
        )

    def to_context_string(self) -> str:
        """Format as string for injection into LLM context."""
        if self.total_cells == 0:
            lines = [f"Notebook: {self.notebook_name} (empty - no cells yet)"]
        else:
            lines = [f"Notebook: {self.notebook_name} ({self.total_cells} cells)"]
            lines.append("")

            for i, cell in enumerate(self.cells_summary):
                status_icon = {
                    "idle": "⚪",
                    "queued": "🔵",
                    "running": "🟡",
                    "success": "🟢",
                    "error": "🔴"
                }.get(cell["status"], "⚪")

                # Format source preview
                source_preview = cell["source"].replace("\n", " ").strip()

                # Cell header
                exec_num = f"[{cell['execution_count']}]" if cell["execution_count"] else "[ ]"
                lines.append(
                    f"{i+1}. {status_icon} {cell['cell_type'].upper()} {exec_num} | id={cell['id'][:8]}"
                )
                lines.append(f"   Source: {source_preview}")

                # Output/error info
                if cell["error"]:
                    lines.append(f"   ❌ Error: {cell['error']}")
                elif cell["output_preview"]:
                    out_preview = cell["output_preview"].replace("\n", " ")[:80]
                    lines.append(f"   Output: {out_preview}")
                elif cell["has_images"]:
                    lines.append(f"   Output: [Contains image(s)]")

                lines.append("")

        if self.last_execution_error:
            lines.append(f"⚠️ Last error: {self.last_execution_error}")

        if self.available_notebooks:
            lines.append("")
            lines.append(f"Available notebooks: {', '.join(self.available_notebooks)}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notebook_name": self.notebook_name,
            "notebook_path": self.notebook_path,
            "total_cells": self.total_cells,
            "cells_summary": self.cells_summary,
            "last_execution_error": self.last_execution_error,
            "available_notebooks": self.available_notebooks,
        }


@dataclass
class VariableInfo:
    """Information about a variable in the kernel."""
    name: str
    var_type: str  # e.g., "DataFrame", "ndarray", "int"
    shape: Optional[str] = None  # For arrays/dataframes
    length: Optional[int] = None  # For lists, dicts
    columns: Optional[List[str]] = None  # For DataFrames
    value_preview: Optional[str] = None  # For simple types
    created_in_cell: Optional[int] = None  # Execution count when created
    dtype: Optional[str] = None  # For arrays/series (e.g., "float64", "int32")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"name": self.name, "type": self.var_type}
        if self.shape:
            result["shape"] = self.shape
        if self.length is not None:
            result["length"] = self.length
        if self.columns:
            result["columns"] = self.columns[:10]  # First 10 columns
            if len(self.columns) > 10:
                result["columns_truncated"] = True
        if self.value_preview:
            result["value"] = self.value_preview
        if self.dtype:
            result["dtype"] = self.dtype
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableInfo":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            var_type=data.get("type", "unknown"),
            shape=data.get("shape"),
            length=data.get("len"),
            columns=data.get("columns"),
            value_preview=data.get("value"),
            dtype=data.get("dtype"),
        )


@dataclass
class KernelState:
    """
    Current state of the Jupyter kernel (variables, their types, values).

    This gives the LLM awareness of what data is available in the kernel.
    """
    variables: Dict[str, VariableInfo] = field(default_factory=dict)
    is_alive: bool = True
    execution_count: int = 0
    last_updated: Optional[datetime] = None

    @classmethod
    def from_introspection(cls, introspection_result: Dict[str, Any], exec_count: int = 0) -> "KernelState":
        """Create from kernel introspection result."""
        variables = {}
        for name, info in introspection_result.items():
            variables[name] = VariableInfo.from_dict({"name": name, **info})

        return cls(
            variables=variables,
            is_alive=True,
            execution_count=exec_count,
            last_updated=datetime.now()
        )

    def to_context_string(self) -> str:
        """Format kernel state for LLM context."""
        if not self.variables:
            return "Kernel State: No variables defined yet."

        lines = [f"Kernel State ({len(self.variables)} variables):"]
        lines.append("")

        # Group by type for better readability
        dataframes = []
        arrays = []
        models = []
        others = []

        for name, var in self.variables.items():
            if var.var_type == "DataFrame":
                dataframes.append(var)
            elif var.var_type in ("ndarray", "Series"):
                arrays.append(var)
            elif "Classifier" in var.var_type or "Regressor" in var.var_type or "Model" in var.var_type:
                models.append(var)
            else:
                others.append(var)

        if dataframes:
            lines.append("DataFrames:")
            for var in dataframes:
                cols = f", columns={var.columns[:5]}..." if var.columns else ""
                lines.append(f"  • {var.name}: {var.shape}{cols}")

        if arrays:
            lines.append("Arrays:")
            for var in arrays:
                lines.append(f"  • {var.name}: {var.var_type} {var.shape or ''}")

        if models:
            lines.append("Models:")
            for var in models:
                lines.append(f"  • {var.name}: {var.var_type}")

        if others:
            lines.append("Other:")
            for var in others:
                val = f" = {var.value_preview}" if var.value_preview else ""
                size = f" (len={var.length})" if var.length else ""
                lines.append(f"  • {var.name}: {var.var_type}{size}{val}")

        return "\n".join(lines)

    def get_dataframes(self) -> List[VariableInfo]:
        """Get all DataFrame variables."""
        return [v for v in self.variables.values() if v.var_type == "DataFrame"]

    def get_variable(self, name: str) -> Optional[VariableInfo]:
        """Get a specific variable by name."""
        return self.variables.get(name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "variables": [var.to_dict() for var in self.variables.values()],
            "is_alive": self.is_alive,
            "execution_count": self.execution_count,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class AlgorithmStep:
    """A single step in the algorithm."""
    step_number: int
    description: str
    rationale: Optional[str] = None  # WHY this step is needed
    expected_output: Optional[str] = None
    validation_criteria: Optional[List[str]] = None  # V2: List instead of string
    cell_type: CellType = "code"
    keywords: List[str] = field(default_factory=list)  # V2: For cell registry indexing
    estimated_complexity: str = "moderate"  # V2: "simple", "moderate", "complex"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = {
            "step_number": self.step_number,
            "description": self.description,
            "expected_output": self.expected_output,
            "validation_criteria": self.validation_criteria,
            "cell_type": self.cell_type,
            "keywords": self.keywords,
            "estimated_complexity": self.estimated_complexity,
        }
        if self.rationale:
            d["rationale"] = self.rationale
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlgorithmStep":
        """Create from dictionary."""
        # Handle both old (string) and new (list) validation_criteria formats
        validation = data.get("validation_criteria")
        if isinstance(validation, str):
            validation = [validation] if validation else []
        elif validation is None:
            validation = []

        return cls(
            step_number=data.get("step_number", 0),
            description=data.get("description", ""),
            rationale=data.get("rationale"),
            expected_output=data.get("expected_output"),
            validation_criteria=validation,
            cell_type=data.get("cell_type", "code"),
            keywords=data.get("keywords", []),
            estimated_complexity=data.get("estimated_complexity", "moderate"),
        )


@dataclass
class Algorithm:
    """
    Algorithm generated by the Algorithm Agent before coding starts.

    Contains a structured plan for the coding task.
    """
    task_summary: str
    steps: List[AlgorithmStep] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # Required variables/data
    expected_final_output: Optional[str] = None
    estimated_cells: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_summary": self.task_summary,
            "steps": [s.to_dict() for s in self.steps],
            "prerequisites": self.prerequisites,
            "expected_final_output": self.expected_final_output,
            "estimated_cells": self.estimated_cells,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Algorithm":
        """Create from dictionary."""
        steps = [AlgorithmStep.from_dict(s) for s in data.get("steps", [])]
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            task_summary=data.get("task_summary", ""),
            steps=steps,
            prerequisites=data.get("prerequisites", []),
            expected_final_output=data.get("expected_final_output"),
            estimated_cells=data.get("estimated_cells", 0),
            created_at=created_at
        )

    def to_context_string(self) -> str:
        """Format algorithm for injection into LLM context."""
        lines = [f"## Algorithm for: {self.task_summary}"]
        lines.append("")

        if self.prerequisites:
            lines.append("**Prerequisites:**")
            for prereq in self.prerequisites:
                lines.append(f"  - {prereq}")
            lines.append("")

        lines.append("**Steps:**")
        for step in self.steps:
            cell_marker = "📝" if step.cell_type == "markdown" else "💻"
            lines.append(f"{step.step_number}. {cell_marker} {step.description}")
            if step.expected_output:
                lines.append(f"   → Expected: {step.expected_output}")
            if step.validation_criteria:
                criteria_str = step.validation_criteria if isinstance(step.validation_criteria, str) else "; ".join(step.validation_criteria)
                lines.append(f"   ✓ Validate: {criteria_str}")
        lines.append("")

        if self.expected_final_output:
            lines.append(f"**Final Output:** {self.expected_final_output}")

        return "\n".join(lines)

    def to_markdown_cell(self) -> str:
        """
        Generate markdown content for the first notebook cell (V2).

        Creates a self-documenting notebook where the algorithm/plan
        is visible as the first cell.
        """
        lines = [
            f"# {self.task_summary}",
            "",
            "This notebook implements the following analysis plan:",
            "",
        ]

        if self.prerequisites:
            lines.append("## Prerequisites")
            lines.append("")
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")

        lines.append("## Approach")
        lines.append("")

        for step in self.steps:
            lines.append(f"### Step {step.step_number}: {step.description}")
            lines.append("")
            if step.expected_output:
                lines.append(f"**Expected output**: {step.expected_output}")
                lines.append("")
            if step.validation_criteria:
                criteria = step.validation_criteria if isinstance(step.validation_criteria, list) else [step.validation_criteria]
                if criteria:
                    lines.append("**Validation**:")
                    for c in criteria:
                        lines.append(f"- {c}")
                    lines.append("")

        if self.expected_final_output:
            lines.append("## Expected Final Output")
            lines.append("")
            lines.append(self.expected_final_output)
            lines.append("")

        lines.append("---")
        lines.append("*Algorithm generated automatically. Cells below implement each step.*")

        return "\n".join(lines)


@dataclass
class SupervisorEvaluation:
    """
    Quality evaluation from the Coder Supervisor.

    Evaluates code cells after execution to determine if they're correct
    and complete, or if they need to be retried.
    """
    cell_id: str
    score: int  # 0-100
    is_acceptable: bool  # True if score >= 50
    correctness: str  # Assessment of correctness
    completeness: str  # Assessment of completeness
    data_quality: str  # Assessment of data quality (if applicable)
    issues: List[str] = field(default_factory=list)  # List of issues found
    suggestions: List[str] = field(default_factory=list)  # Suggestions for improvement
    should_retry: bool = False  # True if cell should be retried
    has_plot: bool = False  # True if output contains a plot
    plot_assessment: Optional[str] = None  # Assessment of plot quality (if applicable)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cell_id": self.cell_id,
            "score": self.score,
            "is_acceptable": self.is_acceptable,
            "correctness": self.correctness,
            "completeness": self.completeness,
            "data_quality": self.data_quality,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "should_retry": self.should_retry,
            "has_plot": self.has_plot,
            "plot_assessment": self.plot_assessment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupervisorEvaluation":
        """Create from dictionary."""
        return cls(
            cell_id=data.get("cell_id", ""),
            score=data.get("score", 0),
            is_acceptable=data.get("is_acceptable", False),
            correctness=data.get("correctness", ""),
            completeness=data.get("completeness", ""),
            data_quality=data.get("data_quality", ""),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            should_retry=data.get("should_retry", False),
            has_plot=data.get("has_plot", False),
            plot_assessment=data.get("plot_assessment")
        )

    def to_feedback_string(self) -> str:
        """Format evaluation as feedback for the coder agent."""
        lines = [f"## Cell Evaluation (Score: {self.score}/100)"]

        if self.is_acceptable:
            lines.append("✅ **PASSED** - Cell output is acceptable")
        else:
            lines.append("❌ **NEEDS IMPROVEMENT** - Cell should be retried")

        lines.append("")
        lines.append(f"**Correctness**: {self.correctness}")
        lines.append(f"**Completeness**: {self.completeness}")

        if self.data_quality:
            lines.append(f"**Data Quality**: {self.data_quality}")

        if self.has_plot and self.plot_assessment:
            lines.append(f"**Plot Assessment**: {self.plot_assessment}")

        if self.issues:
            lines.append("")
            lines.append("**Issues Found:**")
            for issue in self.issues:
                lines.append(f"  - {issue}")

        if self.suggestions and not self.is_acceptable:
            lines.append("")
            lines.append("**Suggestions:**")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")

        return "\n".join(lines)
