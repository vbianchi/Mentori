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

import anyio
import httpx
from mcp import ClientSession
from mcp.shared.exceptions import McpError
from mcp.types import CONNECTION_CLOSED

from backend.config import settings
from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext, get_logger, inject_session_secrets, set_session_context
from backend.mcp.registry import registry
from backend.agents.orchestrator.schemas import PlanStep, StepResult, StepStatus, resolve_switches
from backend.agents.orchestrator.observation_distiller import distill_observation, should_distill
from backend.agents import lock_adapter  # noqa: F401  (puts the repository on sys.path for experiments.runner)
from backend.agents.orchestrator import run_records as rr
from experiments.runner import run_context as rc

logger = get_logger(__name__)

# Q128 (D78): how long the one check of the tool server waits to connect and for each line it reads
TOOL_SERVER_CHECK_S = 10.0


def _transport_error(e: BaseException) -> bool:
    """Q128 (D78): the tool call failed because the MCP session or its connection to the tool server closed: mcp fails
    a call in flight with McpError CONNECTION_CLOSED when the server's stream ends, and a send on the closed session
    raises anyio's ClosedResourceError, BrokenResourceError or EndOfStream."""
    if isinstance(e, McpError):
        return getattr(e.error, "code", None) == CONNECTION_CLOSED
    return isinstance(e, (anyio.ClosedResourceError, anyio.BrokenResourceError, anyio.EndOfStream))


async def _tool_server_answers(timeout_s: float = TOOL_SERVER_CHECK_S) -> bool:
    """Q128 (D78): one check of the tool server, as the runner checks it at start (experiments/runner/experiment.py
    _serves): GET {TOOL_SERVER_URL}/sse answers 200 and sends the endpoint event within its first 5 lines."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            async with client.stream("GET", f"{settings.TOOL_SERVER_URL}/sse",
                                     headers={"Accept": "text/event-stream"}) as resp:
                if resp.status_code != 200:
                    return False
                n = 0
                async for line in resp.aiter_lines():
                    if line.strip() == "event: endpoint":
                        return True
                    n += 1
                    if n >= 5:
                        return False
                return False
    except (httpx.HTTPError, OSError):
        return False


def _tool_record(tool_name: str, calls_off: int, retrievals_off: int, tools_off: int) -> Dict[str, Any]:
    """What the tool call wrote to the run's sink (run_records): the model calls made inside the tool, with their
    status (Q39, D69), its retrieve() records, smart_query's route, and the passages query_documents returned
    whole (A6, D37)."""
    tool_recs = rr.since(rr.TOOL_RECORDS, tools_off)
    routes = [r for r in tool_recs if r.get("kind") == "route"]
    routing = routes[-1].get("route") if routes else None
    # The tool's output is query_documents' passages verbatim only when the step is query_documents, or smart_query
    # routed to it; a query_documents call inside another tool (deep_research) feeds a model, not the output
    verbatim = tool_name == "query_documents" or (tool_name == "smart_query" and bool(routing)
                                                  and routing.get("tool_name") == "query_documents")
    passage_ids: List[str] = []
    for r in tool_recs:
        if verbatim and r.get("kind") == "returned_passages":
            for i in r.get("passages") or []:
                if i and i not in passage_ids:
                    passage_ids.append(i)
    retrieval_keys = ("query", "query_type", "collection", "top_k", "reranked", "n_returned", "passages")
    return {
        "tool_calls": [rr.call_summary(c) for c in rr.since(rr.CALLS, calls_off)],
        "retrievals": [{k: r.get(k) for k in retrieval_keys} for r in rr.since(rr.RETRIEVALS, retrievals_off)],
        "routing": routing,
        "passage_ids": passage_ids,
    }


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


def get_model_for_role(role: str, agent_roles: Optional[Dict[str, str]] = None) -> str:
    """
    Get model identifier for a specific agent role.

    Reanalysis (step 3, D67): the role's model is the run context's, run_context.agent_model(role), the one lookup
    the tools use too. There is no 'default' fallback and no built-in model (the copy fell back to 'default', then to
    ollama::llama3:8b): a role the run names no model for raises LockError, and a lookup outside a run context
    raises RunContextError. agent_roles (the session's) is not read; the callers still pass it.

    Args:
        role: Agent role name (e.g., "handyman", "vision")
        agent_roles: Not read (see above)

    Returns:
        Model identifier string
    """
    return rc.agent_model(role)


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

    # Q89 (D75): a step's last attempt is its result, as for synthesis (Q23, prompts.last_attempt). Mentori replaced
    # the placeholder with the first match, the attempt the supervisor rejected when the step was retried
    latest: Dict[str, Dict[str, Any]] = {}
    for prev in previous_results:
        latest[prev.get("step_id", "")] = prev

    for key, value in step.tool_args.items():
        if isinstance(value, str):
            # Look for {{step_N.result}} patterns
            for step_id, prev in latest.items():
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
    attempt_no: int = 1,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a single plan step via the appropriate agent and MCP tool.

    Reanalysis: the MCP result's isError is read. A lock refusal inside the tool (isError with the tool server's
    TOOL_REFUSAL_MARKER) raises run_records.ToolRefusal and fails the question (Q38, D69); a tool error with
    RUN_STOP_MARKER (the reranker failed to load) raises run_records.RunStop (A4), as does a tool call whose
    connection closed while the tool server, checked once, does not answer (Q128, D78); any other tool error keeps
    Mentori's recovery, the text going to the planner's later phases as before, and is recorded on the step
    (is_error, and every model call made inside the tool with its status: Q39, D69). The StepResult carries the
    step's record (attempt_no, arguments, routing, raw and distilled output, passages; records.md F14, F15).

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

    # Get model for this agent role. Q90 (D75): a role the run does not know (the planner wrote one outside its four)
    # is looked up as "default", as Mentori fell back; the role is used only for this lookup and the display label, so
    # nothing sent changes. The role as written stays in step.agent_role, the one used is recorded (agent_role_used)
    role_used = step.agent_role if step.agent_role in rc.current().agent_roles else "default"
    if role_used != step.agent_role:
        logger.warning(f"Step {step.step_id}: agent role {step.agent_role!r} unknown to the run, looked up as 'default'")
    agent_model = get_model_for_role(role_used, session_context.agent_roles)
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
            # Continue with original args - the tool will report missing params (a tool that takes task_id and
            # gets none is refused by the tool server, so the question fails as a setup error: Q38)
    # The names of the values injected, for the record; their values (user id, secrets) are never stored. A name the
    # plan gave and the session overwrote (inject_session_secrets replaces user_id, task_id and the other session
    # values) is listed too, since tool_args keeps the plan's value, not the one sent
    injected = sorted(k for k in final_args if k not in resolved_args or final_args[k] != resolved_args[k])

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

    # Where the tool's records start in the run's sink (run_records): read back after the call
    offsets = (rr.offset(rr.CALLS), rr.offset(rr.RETRIEVALS), rr.offset(rr.TOOL_RECORDS))
    record = {"attempt_no": attempt_no, "tool_args": dict(resolved_args), "injected": injected,
              "agent_role_used": role_used}

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

        # Q38 (D69): a lock refusal inside the tool fails the question; Q39: any other isError is recorded and the
        # text goes on as Mentori's recovery expects
        if rr.is_refusal_result(mcp_result):
            raise rr.ToolRefusal(f"{step.tool_name}: {result_content}")
        # A4 (D67): an error after which the run cannot go on (the reranker failed to load) stops the run
        if rr.is_run_stop_result(mcp_result):
            raise rr.RunStop(f"{step.tool_name}: {result_content}")
        record.update(_tool_record(step.tool_name, *offsets))
        record["is_error"] = bool(getattr(mcp_result, "isError", False))

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
        # D52: the Figure 4 set-up's distiller switch ("on" as built, "off", "F1") and Q82's trigger ("threshold" as
        # built; "every_step", the stress condition that distils every non-empty output); schemas.ORCHESTRATOR_SWITCHES
        switches = resolve_switches(session_context.orchestrator_switches)
        distiller, every_step = switches["distiller"], switches["distiller_trigger"] == "every_step"
        over = should_distill(result_content)
        record["over_distill_threshold"] = over   # Q82: whether Mentori's threshold was passed, under any switch
        distill_outcome = None
        if distiller != "off" and (over or (every_step and bool(result_content))):
            distiller_model = get_model_for_role("librarian", session_context.agent_roles)
            distill_outcome = {}
            result_content = await distill_observation(
                tool_name=step.tool_name,
                raw_content=result_content,
                model_router=model_router,
                model_identifier=distiller_model,
                event_callback=event_callback,
                variant=distiller,
                outcome=distill_outcome,
                passages=record["passage_ids"],
                every_step=every_step,
            )
        elif distiller == "off" and (over or (every_step and bool(result_content))):
            distill_outcome = {"status": "switched_off", "variant": "off", "raw_chars": len(result_content)}
        record["distill"] = distill_outcome
        record["distilled"] = bool(distill_outcome and distill_outcome.get("status") == "distilled")

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

        # Detect soft failures (tool returned error message instead of crashing). Q91 (D75): Mentori's check decides
        # the step's success, as built; the truth is recorded beside it, and the analysis of where answers are lost
        # reads these flags, not Mentori's label
        detected_error = _detect_error_in_result(result_content)
        actual_success = detected_error is None
        pattern, _ = _error_check(result_content)
        record.update({"tool_error_text": tool_error_text(raw_content), "error_check_pattern": pattern,
                       "short_phrase_fired": pattern == "short_phrase"})

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
                summary=_generate_result_summary(raw_content),  # display only (Q24: no prompt reads it)
                agent_thinking="",
                error=detected_error,
                token_usage=token_usage,
                raw_content=raw_content,           # full output (UI / audit only)
                **record,
            )
        }

    except (rr.SetupError, *rr.REFUSALS):
        raise  # Q38 (D69): a lock refusal, in the tool or in the distiller, is a setup error and fails the question;
               # A4: RunStop stops the run
    except Exception as e:
        # Q128 (D78): the session or its connection closed during the tool call, and the tool server, checked once,
        # does not answer: the run stops (RunStop, as Q93 at connection) before the answer is stored, so the question
        # stays to do. A server that answers leaves the failure to Mentori's recovery below
        if _transport_error(e) and not await _tool_server_answers():
            raise rr.RunStop(f"tool server: {step.tool_name} failed as its connection closed "
                             f"({type(e).__name__}: {e}), and {settings.TOOL_SERVER_URL}/sse does not answer") from e
        error_msg = str(e)
        logger.error(f"Tool {step.tool_name} failed: {error_msg}")
        # Mentori's recovery (a failed step) is kept; the record keeps what the sink shows of the call (Q39)
        if "tool_calls" not in record:
            try:
                record.update(_tool_record(step.tool_name, *offsets))
            except Exception as read_error:   # logged only: the step's error text goes into later prompts
                logger.error(f"Tool records of {step.tool_name} unreadable: {type(read_error).__name__}: {read_error}")

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
                **{k: v for k, v in record.items() if k not in ("distill", "distilled")},
            )
        }


def _detect_error_in_result(content: str) -> Optional[str]:
    """
    Detect soft failures in tool result content.

    Tools may return error messages as strings instead of raising exceptions.
    This function detects common error patterns and returns the error message
    if found, or None if the result appears successful.

    Reanalysis (Q91, D75): Mentori's check, kept as built (it misses "[Error] ..." and labels a short result holding
    "not found" or "could not" a failure); _error_check says which of its patterns fired, for the step's record.

    Args:
        content: Tool result content to check

    Returns:
        Error message if detected, None if result appears successful
    """
    pattern, _ = _error_check(content)
    return content.strip() if pattern else None


# smart_query's prefix before the dispatched tool's text (rag_tools.py smart_query: "**Strategy**: ...\n**Reason**:
# ...\n\n")
_SMART_QUERY_PREFIX = re.compile(r"\A\s*\*\*Strategy\*\*:[^\n]*\n\*\*Reason\*\*:.*?\n\n", re.S)


def tool_error_text(content: Optional[str]) -> bool:
    """Q91 (D75): True when the tool's text is an error, that is starts with "[Error]" (the form every rag tool returns
    a failure in, rag_tools.py), after smart_query's "**Strategy**" prefix when there is one."""
    text = _SMART_QUERY_PREFIX.sub("", content or "", count=1)
    return text.lstrip().startswith("[Error]")


def _error_check(content: str):
    """Mentori's soft-failure check (_detect_error_in_result), returning which pattern fired, "prefix", "http",
    "short_phrase" or "near_empty", and what matched; (None, None) when none did. The patterns and their order are
    Mentori's, unchanged."""
    if not content:
        return None, None

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
            return "prefix", prefix

    # Pattern 2: HTTP error codes
    http_error_patterns = [
        r"http\s*[45]\d{2}",  # HTTP 4xx or 5xx
        r"status\s*code[:\s]*[45]\d{2}",
        r"\(http\s*[45]\d{2}\)",
    ]
    for pattern in http_error_patterns:
        if re.search(pattern, content_lower):
            return "http", pattern

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
                return "short_phrase", phrase

    # Pattern 4: Empty or near-empty results that indicate failure
    if len(content.strip()) < 10 and "error" in content_lower:
        return "near_empty", "error"

    return None, None


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
