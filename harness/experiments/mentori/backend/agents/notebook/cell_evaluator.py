"""
Cell Evaluator for Notebook Coder V2.

Evaluates cell outputs against expected outputs from algorithm steps.
Provides specific feedback for retries rather than generic quality scores.
"""

import json
import logging
import re
import base64
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.model_router import ModelRouter
    from backend.agents.notebook.schema import Cell, AlgorithmStep

from backend.agents.notebook.prompts_v2 import (
    CELL_EVALUATION_PROMPT,
    CELL_EVALUATION_VISION_PROMPT,
    build_validation_criteria_string,
)

from backend.agents import lock_adapter  # noqa: F401  (puts the repository root on sys.path)
from experiments.runner.lock import LockError
from experiments.runner.run_context import RunContextError

logger = logging.getLogger(__name__)

# A lock refusal or a missing run context is our own setup, never a failed evaluation (D69 Q38)
SETUP_ERRORS = (LockError, RunContextError)

# The evaluator's statuses (Class X, fix_design/limits.md cell_evaluator.py:247-257, :557-562, :640-671; A5):
# "ok" the reply gave a score; "error" the evaluation call failed; "unparsed" the reply gave no JSON with an integer
# score. Neither "error" nor "unparsed" is a score: score is None (it was 60, or a keyword guess such as "good" = 75).
EVAL_STATUSES = ("ok", "error", "unparsed")


@dataclass
class CellEvaluation:
    """Result of evaluating a cell against expected output."""
    score: Optional[int]  # 0-100; None when status is "error" or "unparsed"
    meets_expectations: bool  # score >= 70
    should_retry: bool  # score < 50
    feedback: str  # Specific actionable feedback
    matched_criteria: List[str]  # Criteria that passed
    missing_criteria: List[str]  # Criteria that failed
    issues: List[str]  # Specific problems found
    status: str = "ok"  # EVAL_STATUSES

    @property
    def is_acceptable(self) -> bool:
        """Score >= 50 is acceptable (won't force retry). An evaluation with no score (status "error" or "unparsed")
        is accepted without retry, as Mentori accepted a failed evaluation (it scored it 60): coder_v2's control
        flow is unchanged, and the record carries the status and no score. D75 Q59 keeps this as built: no score
        means no retry; the count per model is reported with the coder_v2 rows."""
        if self.score is None:
            return True
        return self.score >= 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "status": self.status,
            "meets_expectations": self.meets_expectations,
            "should_retry": self.should_retry,
            "feedback": self.feedback,
            "matched_criteria": self.matched_criteria,
            "missing_criteria": self.missing_criteria,
            "issues": self.issues,
        }


@dataclass
class VisionEvaluation:
    """Result of vision-based evaluation for plots/visualizations."""
    has_data: bool
    visualization_type: str
    has_labels: bool
    has_title: bool
    visual_quality: str  # "good", "acceptable", "poor"
    matches_expected: bool
    issues: List[str]
    score: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_data": self.has_data,
            "visualization_type": self.visualization_type,
            "has_labels": self.has_labels,
            "has_title": self.has_title,
            "visual_quality": self.visual_quality,
            "matches_expected": self.matches_expected,
            "issues": self.issues,
            "score": self.score,
        }


async def evaluate_cell(
    cell: "Cell",
    step: "AlgorithmStep",
    model_router: "ModelRouter",
    model_identifier: str,
    vision_model: Optional[str] = None,
) -> CellEvaluation:
    """
    Evaluate a cell's output against the expected output from an algorithm step.

    Args:
        cell: The executed cell to evaluate
        step: The algorithm step with expected_output and validation_criteria
        model_router: Router for LLM calls
        model_identifier: Model to use for evaluation
        vision_model: Optional vision model for plot evaluation

    Returns:
        CellEvaluation with score, feedback, and retry recommendation
    """
    # Debug: Log cell info
    cell_id = cell.id if hasattr(cell, 'id') else (cell.get('id', 'unknown') if isinstance(cell, dict) else 'unknown')
    cell_status = cell.status if hasattr(cell, 'status') else (cell.get('status', 'unknown') if isinstance(cell, dict) else 'unknown')
    cell_outputs = cell.outputs if hasattr(cell, 'outputs') else (cell.get('outputs', []) if isinstance(cell, dict) else [])
    logger.info(f"evaluate_cell: cell_id={cell_id[:8] if cell_id else 'unknown'}, status={cell_status}, outputs_count={len(cell_outputs) if cell_outputs else 0}")
    if cell_outputs:
        for i, out in enumerate(cell_outputs[:3]):
            out_type = out.output_type if hasattr(out, 'output_type') else (out.get('output_type', '?') if isinstance(out, dict) else '?')
            logger.info(f"  output[{i}]: type={out_type}, has_text={hasattr(out, 'text') or (isinstance(out, dict) and 'text' in out)}")
    else:
        logger.warning(f"evaluate_cell: NO OUTPUTS for cell {cell_id[:8] if cell_id else 'unknown'}!")

    # First, check for obvious failures
    quick_eval = _quick_evaluation(cell, step)
    if quick_eval is not None:
        return quick_eval

    # Check if this is a visualization that needs vision evaluation
    has_image_output = _cell_has_image_output(cell)
    if has_image_output and vision_model:
        vision_eval = await _evaluate_with_vision(
            cell, step, model_router, vision_model
        )
        # Combine vision and code evaluation
        code_eval = await _evaluate_with_llm(cell, step, model_router, model_identifier)
        return _combine_evaluations(code_eval, vision_eval)

    # Standard LLM evaluation
    return await _evaluate_with_llm(cell, step, model_router, model_identifier)


def _quick_evaluation(cell: "Cell", step: "AlgorithmStep") -> Optional[CellEvaluation]:
    """
    Quick checks for obvious pass/fail cases without LLM.

    Returns None if LLM evaluation is needed.
    """
    # Check for execution errors
    errors = _extract_cell_errors(cell)
    if errors:
        return CellEvaluation(
            score=15,
            meets_expectations=False,
            should_retry=True,
            feedback=f"Cell execution failed with error: {errors[0]}",   # whole (cuts.md :145, D25)
            matched_criteria=[],
            missing_criteria=["No errors"],
            issues=errors,
        )

    # Check for empty output when output was expected
    outputs = _extract_cell_outputs(cell)
    if step.expected_output and "display" in step.expected_output.lower():
        if not outputs:
            return CellEvaluation(
                score=25,
                meets_expectations=False,
                should_retry=True,
                feedback="Cell produced no output but display was expected. Add print() or display() call.",
                matched_criteria=[],
                missing_criteria=["Output displayed"],
                issues=["No output produced"],
            )

    # Check cell status
    status = getattr(cell, 'status', None) or (cell.get('status') if isinstance(cell, dict) else None)
    has_output = bool(outputs) or _cell_has_image_output(cell)

    # Cell was never executed — immediate fail
    if status == 'idle' and not has_output:
        return CellEvaluation(
            score=0,
            meets_expectations=False,
            should_retry=True,
            feedback="Cell was never executed. It needs to be run.",
            matched_criteria=[],
            missing_criteria=["Cell execution"],
            issues=["Cell status is idle with no outputs"],
        )

    if status == 'success':
        # Cell executed without errors
        expected = (step.expected_output or "").lower()

        # Quick-accept cells with no expected output (variable assignments, imports)
        # These are intermediate steps that don't need LLM verification
        if not expected or not has_output:
            score = 65
            feedback = "Cell executed successfully (no visible output - likely variable assignment or import)"
            logger.info(f"Quick-accept: no expected output or no visible output, score={score}")
            return CellEvaluation(
                score=score,
                meets_expectations=False,
                should_retry=False,
                feedback=feedback,
                matched_criteria=["Execution successful"],
                missing_criteria=[],
                issues=[],
            )

        # For cells WITH expected output, fall through to LLM evaluation
        # so we actually verify correctness, not just "it ran without errors"
        logger.info(f"Cell executed successfully with output - falling through to LLM evaluation for correctness check")

    # LLM evaluation for: successful cells with expected output, and edge cases
    logger.info(f"_quick_evaluation returning None: status={status}, has_output={has_output}, falling through to LLM evaluation")
    return None


async def _evaluate_with_llm(
    cell: "Cell",
    step: "AlgorithmStep",
    model_router: "ModelRouter",
    model_identifier: str,
) -> CellEvaluation:
    """Evaluate cell using LLM."""
    # Build prompt
    cell_source = cell.source if hasattr(cell, 'source') else str(cell.get('source', ''))
    cell_outputs = _extract_cell_outputs(cell)
    cell_errors = _extract_cell_errors(cell)

    validation_criteria = step.validation_criteria or []
    if isinstance(validation_criteria, str):
        validation_criteria = [validation_criteria]

    prompt = CELL_EVALUATION_PROMPT.format(
        expected_output=step.expected_output or "Complete the step successfully",
        validation_criteria=build_validation_criteria_string(validation_criteria),
        cell_source=cell_source,  # whole (cuts.md :229, D25; was 1,500 characters)
        cell_output="\n".join(cell_outputs),  # whole (cuts.md :230, D25; was 2,000 characters)
        cell_errors="\n".join(cell_errors) if cell_errors else "None",
    )

    try:
        # No options (cuts.md :240): the lock sets every setting
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = _extract_response_text(response)
        return _parse_evaluation_response(response_text, validation_criteria)

    except SETUP_ERRORS:
        raise   # D69 Q38
    except Exception as e:
        # The failed call is recorded with its status in calls.jsonl; the evaluation is status "error" with no
        # score (it was 60, "assuming acceptable"; Class X, A5)
        logger.warning(f"LLM evaluation failed: {e}")
        return CellEvaluation(
            score=None,
            meets_expectations=False,
            should_retry=False,
            feedback="Evaluation failed",
            matched_criteria=[],
            missing_criteria=[],
            issues=[f"Evaluation error: {type(e).__name__}: {e}"],
            status="error",
        )


async def _evaluate_with_vision(
    cell: "Cell",
    step: "AlgorithmStep",
    model_router: "ModelRouter",
    vision_model: str,
) -> VisionEvaluation:
    """Evaluate visualization output using vision model."""
    # Extract image from cell outputs
    image_data = _extract_image_from_cell(cell)
    if not image_data:
        return VisionEvaluation(
            has_data=False,
            visualization_type="unknown",
            has_labels=False,
            has_title=False,
            visual_quality="poor",
            matches_expected=False,
            issues=["No image output found"],
            score=30,
        )

    validation_criteria = step.validation_criteria or []
    if isinstance(validation_criteria, str):
        validation_criteria = [validation_criteria]

    prompt = CELL_EVALUATION_VISION_PROMPT.format(
        expected_output=step.expected_output or "A visualization",
        validation_criteria=build_validation_criteria_string(validation_criteria),
    )

    try:
        # Call vision model with image
        response = await model_router.chat(
            model_identifier=vision_model,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_data],  # Base64 encoded image
            }],
            options={
                "temperature": 0.3,
                "num_predict": 500,
            }
        )

        response_text = _extract_response_text(response)
        return _parse_vision_response(response_text)

    except Exception as e:
        logger.warning(f"Vision evaluation failed: {e}")
        return VisionEvaluation(
            has_data=True,  # Assume image has something
            visualization_type="unknown",
            has_labels=False,
            has_title=False,
            visual_quality="acceptable",
            matches_expected=True,  # Give benefit of doubt
            issues=[f"Vision evaluation error: {str(e)}"],
            score=60,
        )


def _combine_evaluations(
    code_eval: CellEvaluation,
    vision_eval: VisionEvaluation,
) -> CellEvaluation:
    """Combine code and vision evaluations."""
    # Weight: 70% code, 30% vision
    combined_score = int(0.7 * code_eval.score + 0.3 * vision_eval.score)

    # Combine issues
    all_issues = code_eval.issues + vision_eval.issues

    # Check for critical vision failures
    if not vision_eval.has_data:
        combined_score = min(combined_score, 30)
        all_issues.insert(0, "Visualization appears blank/empty")

    return CellEvaluation(
        score=combined_score,
        meets_expectations=combined_score >= 70,
        should_retry=combined_score < 50,
        feedback=code_eval.feedback,
        matched_criteria=code_eval.matched_criteria,
        missing_criteria=code_eval.missing_criteria,
        issues=all_issues,
    )


def _extract_cell_outputs(cell: Any) -> List[str]:
    """Extract text outputs from cell."""
    outputs = []

    # Handle both dict and object formats
    if hasattr(cell, 'outputs'):
        cell_outputs = cell.outputs
    elif isinstance(cell, dict):
        cell_outputs = cell.get('outputs', [])
    else:
        return outputs

    for output in cell_outputs:
        # Handle CellOutput objects
        if hasattr(output, 'output_type'):
            output_type = output.output_type

            # Stream output
            if output_type == 'stream':
                text = output.text or ''
                if text:
                    outputs.append(text)

            # Execute result / display data
            elif output_type in ('execute_result', 'display_data'):
                data = getattr(output, 'data', {}) or {}
                if 'text/plain' in data:
                    outputs.append(data['text/plain'])
                elif 'text/html' in data:
                    # Strip HTML tags for text comparison
                    html = data['text/html']
                    text = re.sub(r'<[^>]+>', '', html)
                    outputs.append(text)   # whole (cuts.md :381/:402, D25; was 500 characters)

        # Handle dict outputs (from saved notebooks)
        elif isinstance(output, dict):
            output_type = output.get('output_type', '')

            # Stream output
            if output_type == 'stream':
                text = output.get('text', '')
                if text:
                    outputs.append(text)

            # Execute result / display data
            elif output_type in ('execute_result', 'display_data'):
                data = output.get('data', {})
                if 'text/plain' in data:
                    outputs.append(data['text/plain'])
                elif 'text/html' in data:
                    # Strip HTML tags for text comparison
                    html = data['text/html']
                    text = re.sub(r'<[^>]+>', '', html)
                    outputs.append(text)   # whole (cuts.md :381/:402, D25; was 500 characters)

    return outputs


def _extract_cell_errors(cell: Any) -> List[str]:
    """Extract error messages from cell."""
    errors = []

    if hasattr(cell, 'outputs'):
        cell_outputs = cell.outputs
    elif isinstance(cell, dict):
        cell_outputs = cell.get('outputs', [])
    else:
        return errors

    for output in cell_outputs:
        # Handle CellOutput objects
        if hasattr(output, 'output_type'):
            if output.output_type == 'error':
                ename = output.ename or 'Error'
                evalue = output.evalue or ''
                traceback = output.traceback or []
                errors.append(f"{ename}: {evalue}")
                if traceback:
                    # The whole traceback, ANSI codes removed (cuts.md :431/:445, D25; it kept the last line,
                    # cut to 200 characters)
                    errors.append("\n".join(re.sub(r'\x1b\[[0-9;]*m', '', str(line)) for line in traceback))

        # Handle dict outputs
        elif isinstance(output, dict):
            if output.get('output_type') == 'error':
                ename = output.get('ename', 'Error')
                evalue = output.get('evalue', '')
                traceback = output.get('traceback', [])
                errors.append(f"{ename}: {evalue}")
                if traceback:
                    # The whole traceback, ANSI codes removed (cuts.md :431/:445, D25; it kept the last line,
                    # cut to 200 characters)
                    errors.append("\n".join(re.sub(r'\x1b\[[0-9;]*m', '', str(line)) for line in traceback))

    # Also check status
    status = getattr(cell, 'status', None) or (cell.get('status') if isinstance(cell, dict) else None)
    if status == 'error' and not errors:
        errors.append("Cell execution failed")

    # Check for error patterns in stream output (some kernels send errors as stream)
    if not errors:
        for output in (cell_outputs or []):
            if hasattr(output, 'output_type'):
                otype = output.output_type
                text = getattr(output, 'text', '') or ''
            elif isinstance(output, dict):
                otype = output.get('output_type', '')
                text = output.get('text', '')
            else:
                continue
            if otype == 'stream' and text:
                # Look for Python error patterns in stream output
                for pattern in ['Traceback (most recent call last)', 'NameError:', 'TypeError:',
                                'ValueError:', 'KeyError:', 'FileNotFoundError:', 'ImportError:',
                                'AttributeError:', 'IndexError:', 'ModuleNotFoundError:']:
                    if pattern in text:
                        errors.append(f"Error in output: {text.strip()}")   # whole (cuts.md :469, D25)
                        break

    return errors


def _cell_has_image_output(cell: Any) -> bool:
    """Check if cell has image output."""
    if hasattr(cell, 'outputs'):
        cell_outputs = cell.outputs
    elif isinstance(cell, dict):
        cell_outputs = cell.get('outputs', [])
    else:
        return False

    for output in cell_outputs:
        # Handle CellOutput objects
        if hasattr(output, 'data'):
            data = output.data or {}
            if any(k.startswith('image/') for k in data.keys()):
                return True
        # Handle dict outputs
        elif isinstance(output, dict):
            data = output.get('data', {})
            if any(k.startswith('image/') for k in data.keys()):
                return True

    return False


def _extract_image_from_cell(cell: Any) -> Optional[str]:
    """Extract base64 image data from cell outputs."""
    if hasattr(cell, 'outputs'):
        cell_outputs = cell.outputs
    elif isinstance(cell, dict):
        cell_outputs = cell.get('outputs', [])
    else:
        return None

    for output in cell_outputs:
        # Handle CellOutput objects
        if hasattr(output, 'data'):
            data = output.data or {}
            # Prefer PNG
            if 'image/png' in data:
                return data['image/png']
            elif 'image/jpeg' in data:
                return data['image/jpeg']
        # Handle dict outputs
        elif isinstance(output, dict):
            data = output.get('data', {})
            # Prefer PNG
            if 'image/png' in data:
                return data['image/png']
            elif 'image/jpeg' in data:
                return data['image/jpeg']

    return None


def _extract_response_text(response: Any) -> str:
    """Extract text from various response formats."""
    if isinstance(response, dict):
        if "message" in response and "content" in response["message"]:
            return response["message"]["content"]
        elif "response" in response:
            return response["response"]
        elif "content" in response:
            return response["content"]
        return str(response)
    elif hasattr(response, "content"):
        return response.content
    return str(response)


def _parse_evaluation_response(
    response_text: str,
    validation_criteria: List[str],
) -> CellEvaluation:
    """Parse LLM evaluation response into CellEvaluation."""
    # Try to extract JSON
    data = _extract_json(response_text)

    if not isinstance(data, dict):
        # No JSON: status "unparsed", no score (it guessed one from keywords, "good" = 75; Class X, A5)
        logger.warning("Could not parse evaluation JSON")
        return _unparsed_evaluation(response_text, data)

    score = data.get("score")
    if isinstance(score, str):
        # A number written as text is read as that number ("72" or "72.5"); text that is not a number has no score
        try:
            score = float(score.strip())
        except ValueError:
            score = None
    if isinstance(score, bool) or not isinstance(score, (int, float)) or score != score:
        # A reply with no numeric score is "unparsed" (a missing or unreadable score was 60; Class X, A5). A stated
        # number, integer or not, is used as given, as the submitted parser used it.
        logger.warning(f"Evaluation JSON has no numeric score: {data.get('score')!r}")
        return _unparsed_evaluation(response_text, data)
    if isinstance(score, float) and score.is_integer():
        score = int(score)

    score = max(0, min(100, score))  # Clamp to 0-100

    return CellEvaluation(
        score=score,
        meets_expectations=data.get("meets_expectations", score >= 70),
        should_retry=data.get("should_retry", score < 50),
        feedback=data.get("feedback", "No specific feedback"),
        matched_criteria=data.get("matched_criteria", []),
        missing_criteria=data.get("missing_criteria", []),
        issues=data.get("issues", []),
    )


def _parse_vision_response(response_text: str) -> VisionEvaluation:
    """Parse vision model response into VisionEvaluation."""
    data = _extract_json(response_text)

    if not data:
        # Default to acceptable if we can't parse
        return VisionEvaluation(
            has_data=True,
            visualization_type="unknown",
            has_labels=True,
            has_title=True,
            visual_quality="acceptable",
            matches_expected=True,
            issues=[],
            score=70,
        )

    score = data.get("score", 70)
    if isinstance(score, str):
        try:
            score = int(score)
        except ValueError:
            score = 70

    return VisionEvaluation(
        has_data=data.get("has_data", True),
        visualization_type=data.get("visualization_type", "unknown"),
        has_labels=data.get("has_labels", False),
        has_title=data.get("has_title", False),
        visual_quality=data.get("visual_quality", "acceptable"),
        matches_expected=data.get("matches_expected", True),
        issues=data.get("issues", []),
        score=score,
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from text, handling markdown code blocks."""
    # Try markdown code block first
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try direct JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding JSON object in text
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _unparsed_evaluation(text: str, data: Optional[Dict[str, Any]]) -> CellEvaluation:
    """The evaluation of a reply that gave no integer score: status "unparsed", score None, no retry; the reply is
    kept whole in feedback (cuts.md :667, D25; it was cut to 200 characters). It replaces the keyword guess that
    read "good" as 75 and "error" as 30 (Class X, fix_design/limits.md cell_evaluator.py:640-671). Lists the JSON
    gave are kept."""
    data = data if isinstance(data, dict) else {}
    return CellEvaluation(
        score=None,
        meets_expectations=False,
        should_retry=False,
        feedback=text if text else "See evaluation details",
        matched_criteria=data.get("matched_criteria", []) if isinstance(data.get("matched_criteria"), list) else [],
        missing_criteria=data.get("missing_criteria", []) if isinstance(data.get("missing_criteria"), list) else [],
        issues=data.get("issues", []) if isinstance(data.get("issues"), list) else [],
        status="unparsed",
    )
