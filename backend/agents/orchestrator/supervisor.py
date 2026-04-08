"""
Supervisor Agent module for the Orchestrator.

The Supervisor Agent provides quality-based evaluation of step results,
going beyond simple pass/fail to assess whether results actually help
achieve the goal.

Key responsibilities:
- Evaluate result quality (0-100 score)
- Identify issues with results
- Suggest micro-adjustments for low-quality results
- Decide whether to retry, continue, or escalate

Phase 2A implementation.
"""

import json
from typing import List, Dict, Any, Optional, Callable, Awaitable

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import get_logger
from backend.agents.orchestrator.schemas import (
    PlanStep,
    StepResult,
    SupervisorEvaluation,
    MicroAdjustment,
)
from backend.agents.orchestrator.prompts import (
    SUPERVISOR_EVALUATION_PROMPT,
    SUPERVISOR_MICRO_ADJUSTMENT_PROMPT,
)

logger = get_logger(__name__)


def _get_index_context(tool_name: str, tool_args: dict, user_id: Optional[str]) -> str:
    """
    Look up the actual document list for RAG steps so the supervisor knows
    the real index size instead of guessing.

    Returns a formatted string ready to inject into the evaluation prompt,
    or an empty string when not applicable / on any error.
    """
    _RAG_TOOLS = {"smart_query", "cross_document_analysis", "deep_research_rlm",
                  "query_documents", "inspect_document_index"}
    if tool_name not in _RAG_TOOLS:
        return ""

    index_name = tool_args.get("index_name")
    if not index_name or not user_id:
        return ""

    try:
        from pathlib import Path
        from backend.retrieval.models import UserCollection, IndexStatus
        from backend.database import engine as db_engine
        from sqlmodel import Session, select

        with Session(db_engine) as session:
            idx = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id)
                .where(UserCollection.name == index_name)
                .where(UserCollection.status == IndexStatus.READY)
            ).first()

        if not idx:
            return ""

        doc_names = [Path(p).name for p in idx.file_paths]
        if not doc_names:
            return ""

        names_list = "\n".join(f"  {i+1}. {n}" for i, n in enumerate(doc_names))
        return (
            f"## Index Ground Truth\n"
            f"Index '{index_name}' contains exactly **{len(doc_names)} document(s)**:\n"
            f"{names_list}\n"
            f"A COMPLETE result MUST include findings for ALL {len(doc_names)} document(s) above.\n"
            f"Do NOT penalise for 'missing documents' if all {len(doc_names)} are covered."
        )
    except Exception as exc:
        logger.debug(f"_get_index_context failed (non-critical): {exc}")
        return ""


def _parse_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from LLM response.

    Handles various formats:
    - Pure JSON
    - JSON wrapped in markdown code blocks
    - JSON with leading/trailing text
    """
    import re

    if not content:
        return None

    content = content.strip()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code blocks
    code_block_patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]

    for pattern in code_block_patterns:
        match = re.search(pattern, content)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try finding JSON object in the text
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, content)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _format_previous_steps_summary(previous_results: List[Dict[str, Any]]) -> str:
    """Format previous step results for context."""
    if not previous_results:
        return "(No previous steps)"

    lines = []
    for result in previous_results[-3:]:  # Last 3 steps for context
        step_id = result.get("step_id", "unknown")
        summary = result.get("summary", "No summary")
        success = "✓" if result.get("success") else "✗"
        lines.append(f"- {step_id} [{success}]: {summary[:100]}...")

    return "\n".join(lines)


def _detect_obvious_failure(result: StepResult) -> Optional[SupervisorEvaluation]:
    """
    Pre-check for obvious failures before LLM evaluation.

    Returns a low-quality SupervisorEvaluation if clear error patterns are detected,
    or None to proceed with LLM evaluation.
    """
    if not result.content:
        return SupervisorEvaluation(
            quality_score=10,
            issues=["Result is empty"],
            suggestion="Check tool arguments and try again",
            should_retry=True,
            should_escalate=False,
            reasoning="Tool returned empty result",
            thinking="[Heuristic] Empty result detected"
        )

    # Check if StepResult already indicates failure
    if not result.success or result.error:
        error_msg = result.error or "Unknown error"
        return SupervisorEvaluation(
            quality_score=0,
            issues=[f"Tool reported failure: {error_msg[:100]}"],
            suggestion="Review error message and adjust tool arguments",
            should_retry=True,
            should_escalate=False,
            reasoning=f"Tool execution failed: {error_msg}",
            thinking=f"[Heuristic] StepResult.success=False, error={error_msg}"
        )

    content_lower = result.content.lower().strip()

    # Check for error prefixes
    error_prefixes = ["error:", "failed:", "failure:", "exception:"]
    for prefix in error_prefixes:
        if content_lower.startswith(prefix):
            return SupervisorEvaluation(
                quality_score=10,
                issues=[f"Result indicates error: {result.content[:100]}"],
                suggestion="Analyze error message and adjust approach",
                should_retry=True,
                should_escalate=False,
                reasoning=f"Tool returned error message: {result.content[:200]}",
                thinking=f"[Heuristic] Error prefix detected: {prefix}"
            )

    # Check for common API/auth failures
    auth_failure_patterns = [
        "invalid api key",
        "authentication failed",
        "authorization failed",
        "access denied",
        "http 401",
        "http 403",
    ]
    for pattern in auth_failure_patterns:
        if pattern in content_lower:
            return SupervisorEvaluation(
                quality_score=5,
                issues=[f"Authentication/authorization error: {pattern}"],
                suggestion=None,  # Can't fix automatically
                should_retry=False,  # Don't retry auth errors
                should_escalate=True,  # Needs user intervention
                reasoning=f"Tool failed with auth error - user needs to check API keys/permissions",
                thinking=f"[Heuristic] Auth failure pattern detected: {pattern}"
            )

    return None


async def evaluate_step_quality(
    step: PlanStep,
    result: StepResult,
    goal: str,
    previous_results: List[Dict[str, Any]],
    model_router: ModelRouter,
    model_identifier: str,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    user_id: Optional[str] = None,
) -> SupervisorEvaluation:
    """
    Evaluate the quality of a step result using the Supervisor Agent.

    This goes beyond pass/fail to assess:
    - Relevance to the goal
    - Completeness of information
    - Whether we're making progress

    Args:
        step: The step that was executed
        result: The result from executing the step
        goal: The overall plan goal
        previous_results: Results from previous steps (for context)
        model_router: Router for LLM calls
        model_identifier: Model to use for evaluation
        think: Thinking mode
        event_callback: Optional callback to emit events

    Returns:
        SupervisorEvaluation with quality score, issues, and recommendations
    """
    # Pre-check for obvious failures (saves LLM call)
    obvious_failure = _detect_obvious_failure(result)
    if obvious_failure:
        logger.info(f"Supervisor detected obvious failure for step {step.step_id}: {obvious_failure.issues}")
        return obvious_failure

    # Look up actual index metadata for RAG tools (prevents false coverage rejections)
    index_ctx = _get_index_context(step.tool_name, step.tool_args, user_id)
    index_context_section = (index_ctx + "\n") if index_ctx else ""

    # Format the prompt
    prompt = SUPERVISOR_EVALUATION_PROMPT.format(
        goal=goal,
        step_id=step.step_id,
        step_description=step.description,
        tool_name=step.tool_name,
        tool_args=json.dumps(step.tool_args, indent=2),
        expected_output=step.expected_output,
        index_context=index_context_section,
        result_content=result.content[:10000] if result.content else "(Empty result)",
        previous_steps_summary=_format_previous_steps_summary(previous_results),
    )

    eval_messages = [
        {"role": "system", "content": "You are a quality-focused Supervisor Agent. Respond only with JSON."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Supervisor evaluating step {step.step_id} quality...")

    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=eval_messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Collect thinking
                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "supervisor_thinking",
                                "content": thinking_chunk,
                                "step_id": step.step_id,
                            })

                    # Collect content
                    if "content" in delta:
                        full_content += delta["content"]

                # Handle token usage
                if data.get("done") is True and "eval_count" in data:
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": data.get("prompt_eval_count", 0),
                                "output": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            },
                            "source": "supervisor:evaluate"
                        })

                # Handle Gemini-style token usage
                if "usage" in data:
                    usage = data["usage"]
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                                "output": usage.get("output_tokens", usage.get("completion_tokens", 0)),
                                "total": usage.get("total_tokens", 0),
                            },
                            "source": "supervisor:evaluate"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Supervisor evaluation error: {e}")
        # Return a default "uncertain" evaluation on error
        return SupervisorEvaluation(
            quality_score=50,
            issues=[f"Evaluation failed: {str(e)}"],
            suggestion=None,
            should_retry=False,
            should_escalate=False,
            reasoning="Could not evaluate quality due to an error. Proceeding with caution.",
            thinking=full_thinking,
        )

    # Parse the JSON response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        evaluation = SupervisorEvaluation.from_dict(parsed, thinking=full_thinking)

        # Apply retry logic based on step retry count
        if evaluation.quality_score < 70 and step.retry_count < 3:
            evaluation.should_retry = True
            evaluation.should_escalate = False
        elif evaluation.quality_score < 50 or step.retry_count >= 3:
            evaluation.should_retry = False
            evaluation.should_escalate = True

        logger.info(
            f"Supervisor evaluation: quality={evaluation.quality_score}, "
            f"retry={evaluation.should_retry}, escalate={evaluation.should_escalate}"
        )
        return evaluation
    else:
        logger.warning("Could not parse supervisor evaluation JSON, using defaults")
        # Default to cautious proceed
        return SupervisorEvaluation(
            quality_score=60,
            issues=["Could not parse evaluation response"],
            suggestion=None,
            should_retry=False,
            should_escalate=False,
            reasoning="Evaluation parsing failed. Proceeding with moderate confidence.",
            thinking=full_thinking,
        )


async def suggest_micro_adjustment(
    step: PlanStep,
    result: StepResult,
    issues: List[str],
    previous_adjustments: List[str],
    model_router: ModelRouter,
    model_identifier: str,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> MicroAdjustment:
    """
    Suggest a micro-adjustment to improve step results on retry.

    Micro-adjustments are small, targeted changes to tool arguments
    that might get better results without completely changing the approach.

    Args:
        step: The step that needs adjustment
        result: The result that had quality issues
        issues: List of issues identified by the supervisor
        previous_adjustments: Adjustments already tried (to avoid repeating)
        model_router: Router for LLM calls
        model_identifier: Model to use
        think: Thinking mode
        event_callback: Optional callback to emit events

    Returns:
        MicroAdjustment with adjusted arguments and reasoning
    """
    # Format the prompt
    prompt = SUPERVISOR_MICRO_ADJUSTMENT_PROMPT.format(
        step_description=step.description,
        tool_name=step.tool_name,
        original_args=json.dumps(step.tool_args, indent=2),
        result_summary=result.summary[:500] if result.summary else "(No summary)",
        issues="\n".join(f"- {issue}" for issue in issues) if issues else "(No specific issues)",
        attempt_number=step.retry_count + 1,
        previous_adjustments="\n".join(f"- {adj}" for adj in previous_adjustments) if previous_adjustments else "(None)",
    )

    adj_messages = [
        {"role": "system", "content": "You are suggesting targeted improvements. Respond only with JSON."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Supervisor suggesting micro-adjustment for step {step.step_id}...")

    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=adj_messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "supervisor_thinking",
                                "content": thinking_chunk,
                                "step_id": step.step_id,
                            })

                    if "content" in delta:
                        full_content += delta["content"]

                # Handle token usage
                if data.get("done") is True and "eval_count" in data:
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": data.get("prompt_eval_count", 0),
                                "output": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            },
                            "source": "supervisor:adjust"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Micro-adjustment suggestion error: {e}")
        # Return original args as fallback
        return MicroAdjustment(
            original_args=step.tool_args,
            adjusted_args=step.tool_args,
            adjustment_reasoning=f"Could not generate adjustment: {str(e)}",
            attempt_number=step.retry_count + 1,
            adjustment_type="none",
        )

    # Parse the JSON response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        # Merge adjusted args with original (in case LLM omitted some)
        adjusted_args = {**step.tool_args, **parsed.get("adjusted_args", {})}

        adjustment = MicroAdjustment(
            original_args=step.tool_args,
            adjusted_args=adjusted_args,
            adjustment_reasoning=parsed.get("adjustment_reasoning", "Adjustment suggested"),
            attempt_number=step.retry_count + 1,
            adjustment_type=parsed.get("adjustment_type", "parameter_tweak"),
        )

        logger.info(f"Micro-adjustment suggested: {adjustment.adjustment_type}")
        return adjustment
    else:
        logger.warning("Could not parse micro-adjustment JSON, using original args")
        return MicroAdjustment(
            original_args=step.tool_args,
            adjusted_args=step.tool_args,
            adjustment_reasoning="Could not parse adjustment suggestion",
            attempt_number=step.retry_count + 1,
            adjustment_type="none",
        )


def should_trigger_reflection(
    steps_since_last_reflection: int,
    consecutive_low_quality: int,
    same_tool_streak: int,
    time_elapsed_seconds: float = 0,
    reflection_interval: int = 3,
    low_quality_threshold: int = 2,
    same_tool_threshold: int = 3,
    time_threshold_seconds: float = 120,
) -> bool:
    """
    Determine if we should trigger metacognitive reflection.

    Reflection is a periodic self-check to detect rabbit holes and
    strategic issues. This function checks various triggers.

    Args:
        steps_since_last_reflection: Steps completed since last reflection
        consecutive_low_quality: Steps in a row with quality < threshold
        same_tool_streak: Consecutive calls to the same tool
        time_elapsed_seconds: Time since task started
        reflection_interval: Trigger reflection every N steps
        low_quality_threshold: Trigger after N consecutive low-quality results
        same_tool_threshold: Trigger after N consecutive same-tool calls
        time_threshold_seconds: Trigger after N seconds

    Returns:
        True if reflection should be triggered
    """
    # Regular interval trigger
    if steps_since_last_reflection >= reflection_interval:
        logger.info(f"Reflection trigger: {steps_since_last_reflection} steps since last reflection")
        return True

    # Low quality streak trigger
    if consecutive_low_quality >= low_quality_threshold:
        logger.info(f"Reflection trigger: {consecutive_low_quality} consecutive low-quality results")
        return True

    # Same tool streak trigger (possible rabbit hole)
    if same_tool_streak >= same_tool_threshold:
        logger.info(f"Reflection trigger: {same_tool_streak} consecutive calls to same tool")
        return True

    # Time-based trigger
    if time_elapsed_seconds > time_threshold_seconds:
        logger.info(f"Reflection trigger: {time_elapsed_seconds:.0f}s elapsed")
        return True

    return False


def update_supervisor_tracking(
    state: "OrchestratorState",
    step: PlanStep,
    evaluation: SupervisorEvaluation,
) -> None:
    """
    Update the orchestrator state's supervisor tracking fields.

    Call this after each step evaluation to maintain accurate tracking
    for reflection triggers.

    Args:
        state: The orchestrator state to update
        step: The step that was just executed
        evaluation: The supervisor's evaluation of the step
    """
    # Update steps since reflection
    state.steps_since_reflection += 1

    # Update low quality streak
    if evaluation.quality_score < 70:
        state.consecutive_low_quality += 1
    else:
        state.consecutive_low_quality = 0

    # Update same tool streak
    if state.last_tool_name == step.tool_name:
        state.same_tool_streak += 1
    else:
        state.same_tool_streak = 1
        state.last_tool_name = step.tool_name
