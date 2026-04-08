# backend/agents/notebook/task_supervisor.py
"""
Task-Level Supervisor for tracking overall task completion.

Unlike the cell-level CoderSupervisor which evaluates individual cells,
this supervisor tracks progress against the algorithm and determines
when the overall task is complete.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from backend.agents.model_router import ModelRouter
from backend.agents.notebook.schema import (
    Algorithm,
    AlgorithmStep,
    NotebookState,
    KernelState,
    SupervisorEvaluation,
)
from backend.agents.session_context import get_logger

logger = get_logger(__name__)


TASK_EVALUATION_PROMPT = """You are evaluating whether a coding task has been completed.

## Task Description
{task_summary}

## Algorithm Steps to Complete
{algorithm_steps}

## Current Notebook State
{notebook_state}

## Cells Executed (with evaluations)
{cell_evaluations}

## Kernel Variables
{kernel_state}

## Your Task

Determine whether ALL algorithm steps have been completed successfully.

A step is complete if:
1. A cell was executed that implements the step's description
2. The cell execution was successful (no errors)
3. The cell evaluation score is >= 50 (acceptable)

Respond with JSON only:

```json
{{
  "all_steps_complete": true,
  "completed_steps": [1, 2, 3],
  "incomplete_steps": [],
  "overall_score": 85,
  "summary": "Brief summary of completion status",
  "should_stop": true,
  "reason": "Why agent should stop (or continue)"
}}
```

IMPORTANT: If all steps are done, set `should_stop: true`. If work remains, set `should_stop: false`.
"""


@dataclass
class StepStatus:
    """Status of a single algorithm step."""
    step_number: int
    description: str
    is_complete: bool = False
    cell_id: Optional[str] = None  # Cell that implements this step
    evaluation_score: Optional[int] = None
    notes: str = ""


@dataclass
class TaskCompletionStatus:
    """Overall task completion status."""
    is_complete: bool
    completed_steps: List[int]
    incomplete_steps: List[int]
    overall_score: int
    summary: str
    should_stop: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_complete": self.is_complete,
            "completed_steps": self.completed_steps,
            "incomplete_steps": self.incomplete_steps,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "should_stop": self.should_stop,
            "reason": self.reason
        }


class TaskSupervisor:
    """
    Supervisor that tracks overall task completion.

    Compares executed cells against algorithm steps to determine
    when the task is complete and the agent should stop.
    """

    def __init__(
        self,
        model_router: ModelRouter,
        model_identifier: str,
        algorithm: Optional[Algorithm] = None
    ):
        """
        Initialize the task supervisor.

        Args:
            model_router: Router for LLM calls
            model_identifier: Model to use for evaluation
            algorithm: The algorithm being followed (if any)
        """
        self.model_router = model_router
        self.model_identifier = model_identifier
        self.algorithm = algorithm

        # Track step completion
        self._step_statuses: Dict[int, StepStatus] = {}
        self._cell_evaluations: List[Dict[str, Any]] = []
        self._completion_checks: int = 0

        # Initialize step tracking from algorithm
        if algorithm:
            for step in algorithm.steps:
                self._step_statuses[step.step_number] = StepStatus(
                    step_number=step.step_number,
                    description=step.description
                )

    def record_cell_evaluation(
        self,
        cell_id: str,
        source_summary: str,
        evaluation: SupervisorEvaluation,
        algorithm_step: Optional[int] = None
    ) -> None:
        """
        Record a cell evaluation for task progress tracking.

        Args:
            cell_id: ID of the evaluated cell
            source_summary: Summary of what the cell does
            evaluation: The cell-level evaluation
            algorithm_step: Which algorithm step this cell implements (if known)
        """
        record = {
            "cell_id": cell_id,
            "source_summary": source_summary,
            "score": evaluation.score,
            "is_acceptable": evaluation.is_acceptable,
            "issues": evaluation.issues,
            "has_plot": evaluation.has_plot,
            "plot_assessment": evaluation.plot_assessment,
            "data_quality": evaluation.data_quality
        }
        self._cell_evaluations.append(record)

        # If linked to an algorithm step, update step status
        if algorithm_step and algorithm_step in self._step_statuses:
            status = self._step_statuses[algorithm_step]
            if evaluation.is_acceptable and evaluation.score >= 50:
                status.is_complete = True
                status.cell_id = cell_id
                status.evaluation_score = evaluation.score
                logger.info(f"Algorithm step {algorithm_step} marked complete (cell {cell_id[:8]})")

    def compile_final_report(self) -> str:
        """
        Compile a final report of the task execution.

        Aggregates all cell evaluations, specifically highlighting:
        - Generated plots and their quality
        - Key data quality metrics
        - Overall task success
        """
        lines = ["# Task Execution Report", ""]

        # 1. Executive Summary
        completed = self.get_completed_step_count()
        total = self.get_total_step_count()
        if self.algorithm:
            lines.append(f"**Task**: {self.algorithm.task_summary}")
            lines.append(f"**Progress**: {completed}/{total} steps completed")
        else:
            lines.append(f"**Cells Executed**: {len(self._cell_evaluations)}")

        avg_score = sum(e["score"] for e in self._cell_evaluations) / len(self._cell_evaluations) if self._cell_evaluations else 0
        lines.append(f"**Overall Quality Score**: {avg_score:.1f}/100")
        lines.append("")

        # 2. Key References (Plots & Tables)
        lines.append("## Generated Artifacts")
        lines.append("")

        plots = [e for e in self._cell_evaluations if e.get("has_plot")]
        if plots:
            lines.append("### Figures")
            for i, plot in enumerate(plots, 1):
                cell_id_short = plot['cell_id'][:8]
                assessment = plot.get('plot_assessment') or "Plot generated successfully"
                lines.append(f"**Figure {i}** (Cell `{cell_id_short}`): {assessment}")
            lines.append("")

        # 3. Step validation details
        lines.append("## Execution Details")
        lines.append("")

        for i, eval_rec in enumerate(self._cell_evaluations, 1):
            status = "✅" if eval_rec["is_acceptable"] else "⚠️"
            cell_id_short = eval_rec['cell_id'][:8]
            lines.append(f"### Cell {i} (`{cell_id_short}`) {status}")
            lines.append(f"- **Action**: {eval_rec['source_summary']}")
            if eval_rec['has_plot']:
                lines.append(f"- **Visuals**: {eval_rec.get('plot_assessment', 'Plot generated')}")
            if eval_rec['data_quality'] and eval_rec['data_quality'] != "N/A":
                lines.append(f"- **Data Quality**: {eval_rec['data_quality']}")
            lines.append("")

        return "\n".join(lines)

    def get_completed_step_count(self) -> int:
        """Get the number of completed algorithm steps."""
        return sum(1 for s in self._step_statuses.values() if s.is_complete)

    def get_total_step_count(self) -> int:
        """Get the total number of algorithm steps."""
        return len(self._step_statuses)

    def are_all_steps_complete(self) -> bool:
        """Quick check if all algorithm steps are marked complete."""
        if not self._step_statuses:
            return False
        return all(s.is_complete for s in self._step_statuses.values())

    async def evaluate_task_completion(
        self,
        notebook_state: NotebookState,
        kernel_state: Optional[KernelState] = None
    ) -> TaskCompletionStatus:
        """
        Evaluate whether the overall task is complete.

        Uses LLM to assess whether all algorithm steps have been
        implemented by the executed cells.

        Args:
            notebook_state: Current notebook state
            kernel_state: Current kernel state (optional)

        Returns:
            TaskCompletionStatus with completion assessment
        """
        self._completion_checks += 1

        # If no algorithm, fall back to simple heuristics
        if not self.algorithm:
            return self._evaluate_without_algorithm(notebook_state)

        # Build evaluation prompt
        task_summary = self.algorithm.task_summary

        algorithm_steps = "\n".join([
            f"{s.step_number}. {s.description}"
            for s in self.algorithm.steps
        ])

        cell_evals = "\n".join([
            f"- Cell {e['cell_id'][:8]}: {e['source_summary']} (score={e['score']}, ok={e['is_acceptable']})"
            for e in self._cell_evaluations
        ]) or "No cells executed yet."

        kernel_str = kernel_state.to_context_string() if kernel_state else "No kernel state available."

        prompt = TASK_EVALUATION_PROMPT.format(
            task_summary=task_summary,
            algorithm_steps=algorithm_steps,
            notebook_state=notebook_state.to_context_string(),
            cell_evaluations=cell_evals,
            kernel_state=kernel_str
        )

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            full_response = ""
            async for chunk in self.model_router.chat_stream(
                model_identifier=self.model_identifier,
                messages=messages,
                tools=None,
                think=False
            ):
                try:
                    data = json.loads(chunk)
                    if "message" in data and "content" in data["message"]:
                        full_response += data["message"]["content"]
                except json.JSONDecodeError:
                    pass

            # Parse response
            status = self._parse_completion_response(full_response)

            if status:
                logger.info(f"Task completion check: complete={status.is_complete}, should_stop={status.should_stop}")
                return status

        except Exception as e:
            logger.error(f"Task completion evaluation failed: {e}")

        # Default: don't stop
        return TaskCompletionStatus(
            is_complete=False,
            completed_steps=[],
            incomplete_steps=list(self._step_statuses.keys()),
            overall_score=50,
            summary="Could not evaluate task completion",
            should_stop=False,
            reason="Evaluation failed, continuing"
        )

    def _evaluate_without_algorithm(self, notebook_state: NotebookState) -> TaskCompletionStatus:
        """
        Evaluate completion when no algorithm is available.

        Uses simple heuristics:
        - If there are successful cells, task may be complete
        - If all cells have errors, task is not complete
        """
        successful_cells = [
            c for c in notebook_state.cells_summary
            if c.get("status") == "success" and c.get("cell_type") == "code"
        ]
        error_cells = [
            c for c in notebook_state.cells_summary
            if c.get("error")
        ]

        if successful_cells and not error_cells:
            return TaskCompletionStatus(
                is_complete=True,
                completed_steps=[],
                incomplete_steps=[],
                overall_score=75,
                summary=f"{len(successful_cells)} cells executed successfully",
                should_stop=False,  # Without algorithm, let agent decide
                reason="Cells executed but no algorithm to verify completion"
            )

        return TaskCompletionStatus(
            is_complete=False,
            completed_steps=[],
            incomplete_steps=[],
            overall_score=25 if error_cells else 50,
            summary="No algorithm to track, using heuristics",
            should_stop=False,
            reason="Continue until agent decides to stop"
        )

    def _parse_completion_response(self, response: str) -> Optional[TaskCompletionStatus]:
        """Parse LLM response into TaskCompletionStatus."""
        # Try direct JSON parse
        try:
            data = json.loads(response.strip())
            return self._dict_to_status(data)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return self._dict_to_status(data)
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in text
        json_match = re.search(r'\{[\s\S]*"should_stop"[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._dict_to_status(data)
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse task completion response: {response[:500]}...")
        return None

    def _dict_to_status(self, data: Dict[str, Any]) -> TaskCompletionStatus:
        """Convert dictionary to TaskCompletionStatus."""
        return TaskCompletionStatus(
            is_complete=data.get("all_steps_complete", False),
            completed_steps=data.get("completed_steps", []),
            incomplete_steps=data.get("incomplete_steps", []),
            overall_score=data.get("overall_score", 50),
            summary=data.get("summary", ""),
            should_stop=data.get("should_stop", False),
            reason=data.get("reason", "")
        )

    def get_progress_summary(self) -> str:
        """Get a human-readable progress summary."""
        if not self.algorithm:
            return f"No algorithm tracked. {len(self._cell_evaluations)} cells evaluated."

        completed = self.get_completed_step_count()
        total = self.get_total_step_count()

        return f"Progress: {completed}/{total} algorithm steps complete"

    def format_completion_message(self) -> str:
        """
        Format a completion message for injection into agent context.

        Used to tell the agent that the task is complete and it should
        provide a final summary instead of continuing.
        """
        if not self.algorithm:
            return ""

        completed = self.get_completed_step_count()
        total = self.get_total_step_count()

        if completed == total:
            return """
## Task Completion Notice

✅ **ALL ALGORITHM STEPS COMPLETE**

You have successfully completed all {total} steps in the algorithm.

**STOP and provide a final summary.** Do not:
- Execute more cells
- Create additional files
- Re-execute successful cells
- Add documentation cells (unless explicitly requested)

Respond with a concise summary of what was accomplished and the key outputs.
""".format(total=total)

        return ""
