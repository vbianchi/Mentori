"""
Plan generation module for the Orchestrator.

Handles:
- Query analysis (Phase 0): Decide direct answer vs plan
- Plan generation (Phase 1): Create structured execution plan

Uses the ModelRouter for LLM calls and emits events for UI transparency.
"""

import json
import re
import uuid
from typing import List, Dict, Any, Optional, Callable, Awaitable

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext, get_logger
from backend.agents.orchestrator.schemas import (
    ExecutionPlan,
    PlanStep,
    AnalysisResult,
)
from backend.agents.orchestrator.prompts import (
    ORCHESTRATOR_ANALYZER_PROMPT,
    ORCHESTRATOR_PLANNER_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    format_tools_for_prompt,
    format_conversation_context,
    format_user_context,
    format_workspace_files,
)

logger = get_logger(__name__)


def _parse_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from LLM response.

    Handles various formats:
    - Pure JSON
    - JSON wrapped in markdown code blocks
    - JSON with leading/trailing text
    """
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


def _extract_user_query(messages: List[Dict[str, str]]) -> str:
    """Extract the most recent user query from messages."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


async def analyze_query(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    tools: List[Any],
    session_context: SessionContext,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    memory_context: str = "",
) -> AnalysisResult:
    """
    Analyze the user's query to decide if it needs a plan or direct answer.

    Phase 0 of orchestration.

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use (with thinking suffix parsed)
        messages: Conversation history
        tools: Available MCP tools
        session_context: Current session context
        think: Thinking mode (False, True, or level string)
        event_callback: Async function to emit events for UI

    Returns:
        AnalysisResult with decision, reasoning, and complexity
    """
    user_query = _extract_user_query(messages)

    # Format conversation context (last few messages for context awareness)
    conversation_context = format_conversation_context(messages, max_messages=5)

    # Format user context for personalization
    user_context = format_user_context(session_context)

    # Build the analysis prompt with conversation context, memory, and user context
    prompt = ORCHESTRATOR_ANALYZER_PROMPT.format(
        user_query=user_query,
        conversation_context=conversation_context,
        memory_context=memory_context if memory_context else "(No previous sessions in this task)",
        user_context=user_context
    )

    # Create messages for the LLM
    analysis_messages = [
        {"role": "system", "content": "You are a query analyzer. Respond only with JSON."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Analyzing query: {user_query[:100]}...")

    # Collect thinking and response
    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=analysis_messages,
            tools=None,  # No tools for analysis
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
                                "type": "orchestrator_thinking",
                                "content": thinking_chunk,
                                "phase": "analyzing"
                            })

                    # Collect content
                    if "content" in delta:
                        full_content += delta["content"]

                # Handle token usage (Ollama final chunk)
                if data.get("done") is True and "eval_count" in data:
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": data.get("prompt_eval_count", 0),
                                "output": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            },
                            "source": "orchestrator:analyze"
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
                            "source": "orchestrator:analyze"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Error during query analysis: {e}")
        # Default to needs_plan on error (safer)
        return AnalysisResult(
            decision="needs_plan",
            reasoning=f"Analysis failed ({str(e)}), defaulting to plan mode",
            complexity="simple",
            thinking=full_thinking,
        )

    # Parse the JSON response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        result = AnalysisResult.from_dict(parsed, thinking=full_thinking)
        logger.info(f"Analysis result: {result.decision} ({result.complexity})")
        return result
    else:
        # Fallback: try to infer from content
        logger.warning(f"Could not parse analysis JSON, inferring from content")
        decision = "direct_answer" if "direct_answer" in full_content.lower() else "needs_plan"
        return AnalysisResult(
            decision=decision,
            reasoning="Inferred from response",
            complexity="simple",
            thinking=full_thinking,
        )


async def generate_plan(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    tools: List[Any],
    session_context: SessionContext,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    memory_context: str = "",
) -> ExecutionPlan:
    """
    Generate an execution plan for the user's query.

    Phase 1 of orchestration.

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use
        messages: Conversation history
        tools: Available MCP tools
        session_context: Current session context
        think: Thinking mode
        event_callback: Async function to emit events

    Returns:
        ExecutionPlan with steps to execute
    """
    user_query = _extract_user_query(messages)

    # Get available indexes from session context
    if session_context.available_indexes:
        available_indexes = "\n".join([
            f"- **{idx['name']}**: {idx['description'] or 'No description'} ({idx['file_count']} files)"
            for idx in session_context.available_indexes
        ])
    else:
        available_indexes = "(No document indexes available - user needs to create one first)"
    workspace_path = session_context.workspace_path

    # Format tools description
    tools_description = format_tools_for_prompt(tools)

    # Format conversation context (last few messages)
    conversation_context = format_conversation_context(messages, max_messages=5)

    # Format user context for personalization
    user_context = format_user_context(session_context)

    # Format workspace files for context
    workspace_files = format_workspace_files(workspace_path)

    # Build the planning prompt with memory context and user context
    prompt = ORCHESTRATOR_PLANNER_PROMPT.format(
        tools_description=tools_description,
        available_indexes=available_indexes,
        workspace_path=workspace_path,
        workspace_files=workspace_files,
        user_query=user_query,
        conversation_context=conversation_context,
        memory_context=memory_context if memory_context else "(No previous sessions in this task)",
        user_context=user_context
    )

    # P1-E-3/E-4: Stable system role (KV-cache aligned) + dynamic XML user message.
    plan_messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    logger.info(f"Generating plan for: {user_query[:100]}...")

    # Collect thinking and response
    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=plan_messages,
            tools=None,  # No tools for planning
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Stream thinking to UI
                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "orchestrator_thinking",
                                "content": thinking_chunk,
                                "phase": "planning"
                            })

                    # Collect content
                    if "content" in delta:
                        full_content += delta["content"]

                # Handle token usage (Ollama final chunk)
                if data.get("done") is True and "eval_count" in data:
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": data.get("prompt_eval_count", 0),
                                "output": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            },
                            "source": "orchestrator:plan"
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
                            "source": "orchestrator:plan"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Error during plan generation: {e}")
        # Return a minimal error plan
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            goal="Error occurred during planning",
            steps=[],
            reasoning=f"Planning failed: {str(e)}",
        )

    # Parse the JSON response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        # Add plan_id if not present
        if "plan_id" not in parsed:
            parsed["plan_id"] = str(uuid.uuid4())

        plan = ExecutionPlan.from_dict(parsed)
        plan.reasoning = full_thinking if full_thinking else parsed.get("reasoning", "")

        logger.info(f"Plan generated with {len(plan.steps)} steps")
        return plan
    else:
        logger.error(f"Could not parse plan JSON. Content: {full_content[:500]}")
        # Return empty plan
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            goal="Failed to parse plan",
            steps=[],
            reasoning=f"Could not parse LLM response: {full_content[:200]}",
        )


async def evaluate_step_result(
    model_router: ModelRouter,
    model_identifier: str,
    step: PlanStep,
    result_content: str,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """
    Evaluate whether a step succeeded and if we should continue.

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use
        step: The step that was executed
        result_content: The result from the tool
        think: Thinking mode
        event_callback: Async function to emit events

    Returns:
        Dictionary with success, summary, should_continue, reasoning, issues
    """
    from backend.agents.orchestrator.prompts import ORCHESTRATOR_EVALUATOR_PROMPT

    # Build evaluation prompt
    prompt = ORCHESTRATOR_EVALUATOR_PROMPT.format(
        step_id=step.step_id,
        step_description=step.description,
        tool_name=step.tool_name,
        expected_output=step.expected_output,
        step_result=result_content[:2000],  # Truncate very long results
    )

    eval_messages = [
        {"role": "system", "content": "You are a step evaluator. Respond only with JSON."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Evaluating step {step.step_id}...")

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

                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "orchestrator_thinking",
                                "content": thinking_chunk,
                                "phase": "evaluating"
                            })

                    if "content" in delta:
                        full_content += delta["content"]

                # Handle token usage (Ollama final chunk)
                if data.get("done") is True and "eval_count" in data:
                    if event_callback:
                        await event_callback({
                            "type": "token_usage",
                            "token_usage": {
                                "input": data.get("prompt_eval_count", 0),
                                "output": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                            },
                            "source": "orchestrator:evaluate"
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
                            "source": "orchestrator:evaluate"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Error during step evaluation: {e}")
        return {
            "success": False,
            "summary": f"Evaluation failed: {str(e)}",
            "should_continue": False,
            "reasoning": str(e),
            "issues": [str(e)],
            "thinking": full_thinking,
        }

    # Parse response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        parsed["thinking"] = full_thinking
        return parsed
    else:
        # Default to success and continue if we can't parse
        # (Better to continue than to fail on evaluation)
        return {
            "success": True,
            "summary": "Evaluation response could not be parsed, assuming success",
            "should_continue": True,
            "reasoning": "Defaulting to continue",
            "issues": ["Could not parse evaluation response"],
            "thinking": full_thinking,
        }
