"""
Step execution module for the Orchestrator.

Handles:
- Executing individual plan steps via MCP tools
- Agent role resolution and model selection
- Result collection and formatting
- Error handling for tool calls
"""

import json
import re
import inspect
from typing import List, Dict, Any, Optional, Callable, Awaitable, Union, AsyncGenerator
from datetime import datetime

from mcp import ClientSession

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext, get_logger, inject_session_secrets, set_session_context
from backend.mcp.registry import registry
from backend.agents.orchestrator.schemas import PlanStep, StepResult, StepStatus
from backend.agents.orchestrator.observation_distiller import distill_observation, should_distill

logger = get_logger(__name__)


def parse_thinking_mode(model_identifier: str) -> Union[bool, str]:
    """
    Parse thinking mode from model identifier.

    Examples:
        "ollama::qwen3:8b" → False
        "ollama::qwen3:8b[think]" → True
        "ollama::gpt-oss:7b[think:high]" → "high"

    Args:
        model_identifier: Full model identifier with optional [think] suffix

    Returns:
        False (no thinking), True (boolean thinking), or level string
    """
    if not model_identifier or "[think" not in model_identifier:
        return False

    # Extract thinking suffix
    match = re.search(r'\[think(?::(\w+))?\]', model_identifier)
    if match:
        level = match.group(1)
        return level if level else True
    return False


def get_base_model(model_identifier: str) -> str:
    """
    Remove thinking suffix from model identifier.

    "ollama::qwen3:8b[think:high]" → "ollama::qwen3:8b"
    """
    if not model_identifier:
        return model_identifier
    return re.sub(r'\[think(?::\w+)?\]', '', model_identifier)


def get_model_for_role(role: str, agent_roles: Dict[str, str]) -> str:
    """
    Get model identifier for a specific agent role.

    Falls back to 'default' if role not configured.

    Args:
        role: Agent role name (e.g., "handyman", "vision")
        agent_roles: User's agent role configuration

    Returns:
        Model identifier string
    """
    model = agent_roles.get(role)
    if model and model.strip():
        return model

    # Fallback to default
    default_model = agent_roles.get("default")
    if default_model and default_model.strip():
        logger.info(f"Role '{role}' not configured, using default model")
        return default_model

    # Ultimate fallback
    logger.warning(f"Neither '{role}' nor 'default' role configured")
    return "ollama::llama3:8b"


def resolve_step_arguments(
    step: PlanStep,
    previous_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Resolve step arguments by injecting results from previous steps.

    The orchestrator (not the agent) handles this to ensure:
    1. Agents get concrete values, not references
    2. Context is properly managed
    3. Results flow correctly between steps

    Example:
        tool_args = {"query": "summarize {{step_1.result}}"}
        previous_results = [{"step_id": "step_1", "content": "Found 5 papers..."}]
        → {"query": "summarize Found 5 papers..."}

    Args:
        step: The step with tool_args to resolve
        previous_results: Results from previously completed steps

    Returns:
        Dictionary with resolved argument values
    """
    resolved = {}

    for key, value in step.tool_args.items():
        if isinstance(value, str):
            # Look for {{step_N.result}} patterns
            for prev in previous_results:
                step_id = prev.get("step_id", "")
                placeholder = f"{{{{{step_id}.result}}}}"
                if placeholder in value:
                    prev_content = prev.get("content", "")
                    value = value.replace(placeholder, prev_content)
                    logger.debug(f"Resolved {placeholder} in arg '{key}'")
        resolved[key] = value

    return resolved


async def execute_step(
    step: PlanStep,
    model_router: ModelRouter,
    session_context: SessionContext,
    mcp_session: ClientSession,
    previous_results: List[Dict[str, Any]],
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a single plan step via the appropriate agent and MCP tool.

    This is an async generator that yields events immediately for real-time UI updates.
    The final yield is always a "_step_result" event containing the StepResult.

    Flow:
    1. Yield step_start event immediately
    2. Yield tool_call event immediately
    3. Execute MCP tool (long-running)
    4. Yield tool_result event
    5. Yield _step_result event (final, contains StepResult)

    Args:
        step: The PlanStep to execute
        model_router: Router for LLM calls
        session_context: Current session context
        mcp_session: MCP client session for tool calls
        previous_results: Results from previous steps (for argument resolution)
        event_callback: Optional callback (not used, events are yielded instead)

    Yields:
        Events: step_start, tool_call, tool_result, token_usage, _step_result (final)
    """
    # CRITICAL: Set session context for async generator
    # ContextVars don't automatically propagate into async generators,
    # so we must explicitly set the context to enable secret injection
    set_session_context(session_context)

    step.status = StepStatus.IN_PROGRESS
    step.started_at = datetime.now()

    # Get model for this agent role
    agent_model = get_model_for_role(step.agent_role, session_context.agent_roles)
    agent_think = parse_thinking_mode(agent_model)
    base_model = get_base_model(agent_model)

    logger.info(f"Executing step {step.step_id} with {step.agent_role} agent (model: {base_model})")

    # Yield step start event IMMEDIATELY
    yield {
        "type": "step_start",
        "step_id": step.step_id,
        "description": step.description,
        "agent_role": step.agent_role,
        "agent_name": get_agent_display_name(step.agent_role),
        "agent_model": base_model,
        "thinking_level": agent_think if isinstance(agent_think, str) else ("enabled" if agent_think else None),
        "tool_name": step.tool_name,
    }

    # Resolve arguments (inject previous step results)
    resolved_args = resolve_step_arguments(step, previous_results)
    step.tool_args = resolved_args

    # Get tool metadata for session/secret injection
    local_meta = registry.get_tool(step.tool_name)

    # ALWAYS inject session context (user_id, workspace_path, etc.) AND secrets
    # This is critical for file tools that need user_id but don't have secrets
    final_args = resolved_args.copy()
    required_secrets = local_meta.secrets if local_meta else []

    if local_meta:
        try:
            sig = inspect.signature(local_meta.func)
            final_args = inject_session_secrets(
                agent_args=resolved_args,
                tool_signature=sig,
                tool_secrets=required_secrets  # May be empty, but session values still injected
            )
            logger.info(f"[SESSION_INJECT] Tool {step.tool_name}: injected session context + secrets={required_secrets}")
        except Exception as e:
            logger.error(f"[SESSION_INJECT] FAILED for {step.tool_name}: {type(e).__name__}: {e}")
            # Continue with original args - the tool will report missing params

    # Verify secrets were injected (debug logging for recurring issues)
    for secret_name in required_secrets:
        if secret_name in final_args and final_args[secret_name]:
            logger.info(f"[SECRET_VERIFY] {secret_name}: PRESENT (len={len(str(final_args[secret_name]))})")
        else:
            logger.error(f"[SECRET_VERIFY] {secret_name}: MISSING after injection! Check user settings.")

    # Verify critical session params for file tools
    if step.tool_name in ["write_file", "read_file", "list_files", "delete_path", "move_file", "create_directory"]:
        if "user_id" in final_args:
            logger.info(f"[SESSION_VERIFY] user_id: PRESENT for {step.tool_name}")
        else:
            logger.error(f"[SESSION_VERIFY] user_id: MISSING for {step.tool_name}! File operation will fail.")

    # Yield tool call event IMMEDIATELY (before the actual execution)
    yield {
        "type": "tool_call",
        "tool_call": {"name": step.tool_name, "arguments": resolved_args},
        "step_id": step.step_id,
        "agent_role": step.agent_role,
    }

    # Strip None values from args — FastMCP pydantic validation rejects
    # explicit None for Optional[str] params that the LLM set to null.
    # Omitting the key lets the default kick in instead.
    final_args = {k: v for k, v in final_args.items() if v is not None}

    # Emit tool_progress priming events for long-running tools.
    # The tool server is MCP-synchronous (no streaming), so these fire before
    # the call to give the user context about what will happen during the wait.
    if step.tool_name == "web_search":
        query = final_args.get("query", "")
        if final_args.get("llm_deep"):
            yield {"type": "tool_progress", "message": "Mode: deep research (up to 5 search iterations + synthesis)", "step": 0, "total_steps": 5}
        elif final_args.get("llm_filter"):
            yield {"type": "tool_progress", "message": "Mode: filtered search (LLM relevance scoring)", "step": 0, "total_steps": 0}
        else:
            n = final_args.get("max_results", 5)
            yield {"type": "tool_progress", "message": f"Mode: raw search (top {n} results)", "step": 0, "total_steps": 0}
        if query:
            yield {"type": "tool_progress", "message": f"Query: \"{query[:120]}\"", "step": 0, "total_steps": 0}

    elif step.tool_name == "deep_research_rlm":
        query = final_args.get("query", "")
        max_turns = final_args.get("max_turns", 10)
        index_name = final_args.get("index_name", "")
        yield {"type": "tool_progress", "message": f"RLM iterative analysis (up to {max_turns} turns)", "step": 0, "total_steps": max_turns}
        if index_name:
            yield {"type": "tool_progress", "message": f"Index: {index_name}", "step": 0, "total_steps": max_turns}
        if query:
            yield {"type": "tool_progress", "message": f"Query: \"{query[:120]}\"", "step": 0, "total_steps": max_turns}

    elif step.tool_name == "query_documents":
        query = final_args.get("query", "")
        mode = final_args.get("retrieval_mode", "single_pass")
        index_name = final_args.get("index_name", "")
        yield {"type": "tool_progress", "message": f"Retrieval mode: {mode}", "step": 0, "total_steps": 0}
        if index_name:
            yield {"type": "tool_progress", "message": f"Index: {index_name}", "step": 0, "total_steps": 0}
        if query:
            yield {"type": "tool_progress", "message": f"Query: \"{query[:120]}\"", "step": 0, "total_steps": 0}

    # Execute the tool via MCP
    try:
        logger.info(f"Calling tool {step.tool_name} via MCP...")

        mcp_result = await mcp_session.call_tool(
            name=step.tool_name,
            arguments=final_args,
        )

        # Extract content from MCP result
        result_content = ""
        for content in mcp_result.content:
            if hasattr(content, "text"):
                result_content += content.text
            else:
                result_content += "[Binary Content]"

        logger.info(f"Tool {step.tool_name} completed. Result length: {len(result_content)}")

        # Extract token usage if present
        token_usage = None
        token_pattern = re.compile(r'<!--TOOL_TOKEN_USAGE:(\{[^}]+\})-->')
        match = token_pattern.search(result_content)
        if match:
            try:
                token_usage = json.loads(match.group(1))
                result_content = token_pattern.sub('', result_content).rstrip()
            except json.JSONDecodeError:
                pass

        # ── Observation Distillation (P1-E-1 Context Engineering) ────────────
        # Large tool outputs are compressed before entering the context window.
        # The raw output is preserved in the tool_result event (for UI) and in
        # StepResult.raw_content (audit trail) but NOT re-injected into later
        # LLM calls — directly addresses the V2-5 scaling collapse.
        raw_content = result_content
        if should_distill(result_content):
            distiller_model = get_model_for_role("librarian", session_context.agent_roles)
            result_content = await distill_observation(
                tool_name=step.tool_name,
                raw_content=result_content,
                model_router=model_router,
                model_identifier=distiller_model,
                event_callback=event_callback,
            )

        # Yield tool result event (always carries the full raw output for UI)
        yield {
            "type": "tool_result",
            "tool_result": {"name": step.tool_name, "content": raw_content[:5000] + ("..." if len(raw_content) > 5000 else "")},
            "step_id": step.step_id,
        }

        # Yield token usage if present
        if token_usage:
            yield {
                "type": "token_usage",
                "token_usage": {
                    "input": token_usage.get("input", 0),
                    "output": token_usage.get("output", 0),
                    "total": token_usage.get("total", 0),
                },
                "source": f"tool:{step.tool_name}",
            }

        step.completed_at = datetime.now()
        step.result = result_content

        # Detect soft failures (tool returned error message instead of crashing)
        detected_error = _detect_error_in_result(result_content)
        actual_success = detected_error is None

        if detected_error:
            logger.warning(f"Tool {step.tool_name} returned soft error: {detected_error[:100]}")
            step.status = StepStatus.FAILED
            step.error = detected_error
        else:
            step.status = StepStatus.COMPLETED

        # Yield final result event (special type for engine to capture)
        yield {
            "type": "_step_result",
            "result": StepResult(
                step_id=step.step_id,
                success=actual_success,
                content=result_content,           # distilled (context window)
                summary=_generate_result_summary(raw_content),  # summary from full raw
                agent_thinking="",
                error=detected_error,
                token_usage=token_usage,
                raw_content=raw_content,           # full output (UI / audit only)
            )
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Tool {step.tool_name} failed: {error_msg}")

        step.status = StepStatus.FAILED
        step.completed_at = datetime.now()
        step.error = error_msg

        # Yield error event
        yield {
            "type": "step_failed",
            "step_id": step.step_id,
            "error": error_msg,
            "will_retry": False,
        }

        # Yield final result event
        yield {
            "type": "_step_result",
            "result": StepResult(
                step_id=step.step_id,
                success=False,
                content="",
                summary=f"Tool execution failed: {error_msg}",
                agent_thinking="",
                error=error_msg,
                token_usage=None,
            )
        }


def _detect_error_in_result(content: str) -> Optional[str]:
    """
    Detect soft failures in tool result content.

    Tools may return error messages as strings instead of raising exceptions.
    This function detects common error patterns and returns the error message
    if found, or None if the result appears successful.

    Args:
        content: Tool result content to check

    Returns:
        Error message if detected, None if result appears successful
    """
    if not content:
        return None

    content_lower = content.lower().strip()

    # Pattern 1: Starts with "Error:" or similar
    error_prefixes = [
        "error:",
        "error -",
        "failed:",
        "failure:",
        "exception:",
    ]
    for prefix in error_prefixes:
        if content_lower.startswith(prefix):
            return content.strip()

    # Pattern 2: HTTP error codes
    http_error_patterns = [
        r"http\s*[45]\d{2}",  # HTTP 4xx or 5xx
        r"status\s*code[:\s]*[45]\d{2}",
        r"\(http\s*[45]\d{2}\)",
    ]
    for pattern in http_error_patterns:
        if re.search(pattern, content_lower):
            return content.strip()

    # Pattern 3: Common error phrases (only if short message - likely an error response)
    if len(content) < 500:
        error_phrases = [
            "access denied",
            "permission denied",
            "not found",
            "invalid api key",
            "authentication failed",
            "authorization failed",
            "missing required",
            "is missing",
            "could not",
            "unable to",
            "operation failed",
        ]
        for phrase in error_phrases:
            if phrase in content_lower:
                return content.strip()

    # Pattern 4: Empty or near-empty results that indicate failure
    if len(content.strip()) < 10 and "error" in content_lower:
        return content.strip()

    return None


def _generate_result_summary(content: str, max_length: int = 200) -> str:
    """
    Generate a brief summary of the tool result.

    For MVP, this is just a truncated version. In future phases,
    this could use an LLM to generate a proper summary.

    Args:
        content: Full tool result content
        max_length: Maximum summary length

    Returns:
        Brief summary string
    """
    if not content:
        return "Empty result"

    # Clean up whitespace
    content = " ".join(content.split())

    if len(content) <= max_length:
        return content

    # Truncate and add ellipsis
    return content[:max_length - 3] + "..."


# Agent display names for UI
AGENT_DISPLAY_NAMES = {
    "lead_researcher": "Lead Researcher",
    "supervisor": "Supervisor Agent",
    "coder": "Coder Agent",
    "handyman": "Handyman Agent",
    "editor": "Editor Agent",
    "vision": "Vision Agent",
    "transcriber": "Transcriber Agent",
    "default": "Default Agent"
}


def get_agent_display_name(role: str) -> str:
    """Get human-readable display name for an agent role."""
    if not role:
        return "Unknown Agent"
    return AGENT_DISPLAY_NAMES.get(role, role.replace("_", " ").title() + " Agent")
