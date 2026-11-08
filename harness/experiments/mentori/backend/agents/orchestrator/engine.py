"""
Main orchestration engine for Mentori.

This module provides the `orchestrated_chat` function which replaces the
legacy `chat_loop` with a structured, multi-phase orchestration system.

Phases:
0. Analysis: Decide direct answer vs plan
1. Planning: Generate structured execution plan
2. Execution: Execute steps via specialized agents
3. Synthesis: Combine results into final answer

All phases emit events for UI transparency and save to history for audit trail.

Reanalysis (records.md F13 to F16, limits.md Class X; Q22 to Q26, Q38, Q39, D68, D69): besides Mentori's events, the
engine yields record events an experiment stores (Mentori's own consumers ignore unknown types):
    record_memory     the memory context the analyser and planner were given, whole (memory_context_injected)
    record_analysis   the analyser's decision with its status ("ok", "error", "unparsed")
    record_plan       the plan's generation status, the steps planned and whether max_steps cut them
    record_step       one per step attempt: StepResult.to_record() with the step's tool, role and description
The supervisor_evaluation and micro_adjustment events carry status (and attempt_no); the complete event carries
plan_status and answer_source ("content", "thinking_fallback" (Q26), "direct_answer", or None when there is no
answer). A failure in synthesis or the direct answer is an error event, never answer text. A lock refusal, in this
process or inside a tool (run_records.ToolRefusal), is not caught here: it leaves orchestrated_chat (Q38), as itself
and not in the MCP session's ExceptionGroup when it is the group's only error (D79 Q135; _stop_unwrapped). The memory
consolidation that Mentori starts in the background after the answer is kept; its task is in MEMORY_TASKS under the
task_id, and it returns its outcome, so an experiment can wait for it and record it.

Q92 (D75), Mentori's memory defect kept as built and stated: the memory step never uses the librarian's reply. Mentori
reads the key "content" of router.generate's reply, whose text is under "response" (memory.py; cuts.md M1), so every
consolidation outcome is "unparsed" and the note saved is Mentori's fallback. The librarian call is made, and counts in
the answer's calls and tokens, either way. It cannot affect any answer: each answer starts in a new, empty workspace
(Q22, D68), so no note reaches a later answer.

D52 (Figure 4) and D75 (Q82 to Q88, Q93): the set-up's switches (SessionContext.orchestrator_switches, resolved by
schemas.resolve_switches; a key left out is Mentori as built) switch one phase off in turn:
    analyser "off"            no analyser call; analysis status "switched_off", decision needs_plan: every question goes
                              to the planner and the tools (Q83 a)
    analyser "factual_to_documents"  the analyser runs with prompts.ANALYZER_FACTUAL_TO_DOCUMENTS (Q87 b)
    planner "off"             no planner call; the fixed plan of fixed_plan(): one step, smart_query with the question
                              as query and the session's index, by the editor role, mode left at its default "auto";
                              record_plan generation_status "switched_off" (Q84 a)
    supervisor "off"          no evaluation, no micro-adjustment, no retry: each step runs once and the plan moves on;
                              each attempt's supervisor_evaluation event has status "switched_off" and carries in
                              heuristic what Mentori's text pre-check would have said, not acted on (Q85 a)
    synthesiser "off"         no synthesis call; the answer is format_steps_with_results(plan steps, step results), the
                              text synthesis would have read (each step's last attempt, its content as stored, in plan
                              order); answer_source "steps_text" (Q86 b)
    distiller, distiller_trigger   read by the executor (Q82)
A set-up naming an unknown switch or value stops the run (run_records.RunStop). The supervisor's "Previous Steps
Context" leaves out the attempt it is judging (Q88). An unreachable tool server stops the run (RunStop, Q93): nothing in
the run restarts it, so every later question could only fail the same way.
"""

import asyncio
import re
import uuid
from contextlib import AsyncExitStack, asynccontextmanager
from typing import List, Dict, Any, AsyncGenerator, Optional, Union

from mcp import ClientSession
from mcp.client.sse import sse_client

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import (
    SessionContext,
    set_session_context,
    get_logger,
)
from backend.config import settings
from backend.agents.orchestrator.schemas import (
    OrchestratorState,
    PlanStatus,
    StepStatus,
    CollaborationContext,
    StepResult,
    MAX_STEP_RETRIES,
    AnalysisResult,
    ExecutionPlan,
    PlanStep,
    SwitchError,
    resolve_switches,
)
from backend.agents.orchestrator.prompts import format_steps_with_results
from backend.agents.orchestrator import run_records as rr
from backend.agents.orchestrator.planner import (
    analyze_query,
    generate_plan,
)
from backend.agents.orchestrator.supervisor import (
    _detect_obvious_failure,
    evaluate_step_quality,
    suggest_micro_adjustment,
    update_supervisor_tracking,
)
from backend.agents.orchestrator.executor import (
    execute_step,
    get_model_for_role,
    parse_thinking_mode,
    get_base_model,
    get_agent_display_name,
)
from backend.agents.orchestrator.coder import execute_coder_step
from backend.agents.orchestrator.synthesizer import (
    synthesize_answer,
    generate_direct_answer,
)
from backend.agents.orchestrator.memory import (
    TaskMemoryVault,
    consolidate_session_memory,
)
from backend.mcp.agent_tools import is_tool_allowed, agent_tool_registry
from pathlib import Path

logger = get_logger(__name__)

# The background memory consolidation of each answer, by task_id; its result is the consolidation's outcome
MEMORY_TASKS: Dict[str, "asyncio.Task"] = {}


async def _consolidate(session_context: SessionContext, **kwargs) -> Dict[str, Any]:
    """Mentori's background memory consolidation, returning its outcome: status "ok", "unparsed", "error" (the
    librarian's call failed; Mentori's fallback memory is saved) or "refused" (a lock refusal: a setup error, Q38),
    with the error. Mentori only logged a failure."""
    outcome: Dict[str, Any] = {"status": None, "error": None}
    try:
        # the run context's librarian, no 'default' fallback (executor.get_model_for_role)
        librarian_model = get_model_for_role("librarian")
        await consolidate_session_memory(
            task_id=session_context.task_id,
            user_id=session_context.user_id,
            workspace_path=Path(session_context.workspace_path),
            librarian_model=librarian_model,
            outcome=outcome,
            **kwargs,
        )
        logger.info("Memory consolidation complete")
    except rr.REFUSALS as e:
        logger.error(f"Memory consolidation refused: {e}")
        outcome.update({"status": "refused", "error": f"{type(e).__name__}: {e}"})
    except Exception as e:
        logger.warning(f"Memory consolidation failed: {e}")
        if outcome.get("status") in (None, "ok", "unparsed"):
            outcome.update({"status": "error", "error": f"{type(e).__name__}: {e}"})
    return outcome


# D79 Q135 (O1): the stops the entry point classifies (exp_03's SETUP_ERRORS): SetupError, with ToolRefusal and RunStop,
# and the lock's refusals
STOPS = (rr.SetupError, *rr.REFUSALS)


def _leaves(group: BaseExceptionGroup) -> List[BaseException]:
    return [leaf for e in group.exceptions for leaf in (_leaves(e) if isinstance(e, BaseExceptionGroup) else [e])]


@asynccontextmanager
async def _stop_unwrapped():
    """D79 Q135 (O1): mcp's sse_client and ClientSession are anyio task groups, so an exception leaving the session
    reaches the caller in an ExceptionGroup, nested once per group, which the entry point's except clauses miss. A group
    whose only leaf (through any nesting) is one of STOPS is re-raised as that leaf, its traceback kept: its own cause
    kept when it has one, else the group as its cause. Any other group (no stop, several leaves) leaves unchanged."""
    try:
        yield
    except BaseExceptionGroup as group:
        found = _leaves(group)
        if len(found) != 1 or not isinstance(found[0], STOPS):
            raise
        if found[0].__cause__ is None:
            raise found[0] from group
        raise found[0]


def _get_task_manager():
    """Lazy import to avoid circular import."""
    from backend.agents.task_manager import task_manager
    return task_manager


def _extract_user_query(messages: List[Dict[str, str]]) -> str:
    """Extract the most recent user query from messages."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def fixed_plan(user_query: str, session_context: SessionContext) -> ExecutionPlan:
    """Q84 (a) (D75): the plan with the planner switched off, the same for every question: one step, smart_query (the
    tool the planner's prompt assigns every document question to, prompts.py) with the question as its query and the
    session's index, run by the editor role, mode left at smart_query's default "auto" so its router chooses the
    strategy as in the full pipeline. The goal synthesis and the supervisor read is the question itself. A session
    with no index is a setup error."""
    index_name = (session_context.rag_preferences or {}).get("default_index") or next(
        (i.get("name") for i in (session_context.available_indexes or []) if i.get("name")), None)
    if not index_name:
        raise rr.SetupError("planner switched off: the session names no index for the fixed smart_query step")
    step = PlanStep(
        step_id="step_1",
        description="Search the documents for the question (fixed step: planner switched off)",
        agent_role="editor",
        tool_name="smart_query",
        tool_args={"query": user_query, "index_name": index_name},
        expected_output="Information from the documents that answers the question",
        reasoning="Planner switched off (D52): a fixed one-step plan",
    )
    return ExecutionPlan(plan_id=str(uuid.uuid4()), goal=user_query, steps=[step],
                         reasoning="Planner switched off (D52): a fixed one-step plan", generation_status="switched_off")


def _supervisor_previous(step_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Q88 (D75): what the supervisor gets as previous results. Mentori passed every stored result, the attempt being
    judged last, and the supervisor shows the last PREVIOUS_STEPS_SHOWN of them, so it showed the current attempt and
    the PREVIOUS_STEPS_SHOWN - 1 results before it. Q126 (D78): every stored result but the current attempt is passed,
    and the supervisor's own window then shows the PREVIOUS_STEPS_SHOWN results before the attempt (it was
    step_results[-PREVIOUS_STEPS_SHOWN:-1], one fewer than Mentori's constant whenever a plan had four or more)."""
    return step_results[:-1]


def _silent_precheck(result: StepResult) -> Optional[Dict[str, Any]]:
    """Q85 (a) (D75): what Mentori's text pre-check (supervisor._detect_obvious_failure) would have said about a step
    result, for the record only: None when it passes (Mentori would then call the model), else its verdict."""
    ev = _detect_obvious_failure(result)
    if ev is None:
        return None
    return {"quality_score": ev.quality_score, "issues": ev.issues, "should_retry": ev.should_retry,
            "should_escalate": ev.should_escalate, "reasoning": ev.reasoning}


async def orchestrated_chat(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    session_context: SessionContext,
    max_steps: int = 10,
    think: Union[bool, str] = False,
    history_log: Optional[List[Dict]] = None,
    display_model: Optional[str] = None,
    token_budget: Optional[int] = None,
    collaboration_context: Optional[CollaborationContext] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main orchestration loop for multi-agent chat execution.

    Replaces chat_loop.py with a structured, phase-based approach:
    - Phase 0: Analyze query (direct answer vs needs plan)
    - Phase 1: Generate plan (if needed)
    - Phase 2: Execute steps sequentially
    - Phase 3: Synthesize final answer

    All thinking is streamed to UI. All phases save to history_log for full audit trail.

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use for orchestrator (with thinking suffix)
        messages: Conversation history
        session_context: Current session context with user settings
        max_steps: Maximum number of plan steps to execute
        think: Thinking mode (False, True, or level string)
        history_log: List to append all messages to (for persistence)
        display_model: Model name to show in UI
        token_budget: Optional token budget limit

    Yields:
        Events for UI: session_info, orchestrator_thinking, plan_generated,
                       step_start, tool_call, tool_result, step_complete,
                       chunk, token_usage, status, error, complete
    """
    # Set session context for this execution
    set_session_context(session_context)

    # D52 (D75): the set-up's switches; a misnamed one stops the run (it would otherwise run as Mentori as built)
    try:
        switches = resolve_switches(session_context.orchestrator_switches)
    except SwitchError as e:
        raise rr.RunStop(f"orchestrator switches: {e}") from e

    # Ensure standard task directories exist
    workspace_path = Path(session_context.workspace_path)
    (workspace_path / "outputs").mkdir(parents=True, exist_ok=True)
    (workspace_path / "files").mkdir(parents=True, exist_ok=True)

    # Load memory vault for this task (Phase 2B)
    memory_context = ""
    memory_error = None
    vault = None
    try:
        vault = TaskMemoryVault(
            task_id=session_context.task_id,
            user_id=session_context.user_id,
            workspace_path=Path(session_context.workspace_path),
        ).load()
        memory_context = vault.get_context_for_injection()
        if vault.sessions:
            logger.info(f"Memory vault loaded: {len(vault.sessions)} sessions, {vault.total_token_count} tokens")
    except Exception as e:
        logger.warning(f"Failed to load memory vault: {e}")
        memory_error = f"{type(e).__name__}: {e}"

    # Q22 (D68; records.md F13): the memory the analyser and planner are given, whole, for the answer's record
    yield {
        "type": "record_memory",
        "workspace": str(workspace_path),
        "memory_context_injected": memory_context or "(No previous sessions in this task)",
        "sessions": len(vault.sessions) if vault else 0,
        "error": memory_error,
    }

    # Initialize state
    state = OrchestratorState(
        task_id=session_context.task_id,
        user_query=_extract_user_query(messages),
    )

    # Yield session info
    yield {
        "type": "session_info",
        "session_info": {
            "model": display_model or model_identifier,
            "agent_role": "lead_researcher",
            "agent_roles": session_context.agent_roles,
            "orchestrated": True,
        }
    }

    # Yield memory loaded event if vault has sessions (Phase 2B)
    if memory_context and memory_context != "(No previous sessions in this task)":
        yield {
            "type": "memory_loaded",
            "session_count": len(vault.sessions) if vault else 0,
            "total_tokens": vault.total_token_count if vault else 0,
            "max_tokens": vault.max_context_tokens if vault else 8000,
        }

    # Connect to MCP Tool Server (D79 Q135: a stop leaving the session is unwrapped from the task groups' group)
    async with _stop_unwrapped(), AsyncExitStack() as stack:
        try:
            logger.info(f"Connecting to Tool Server at {settings.TOOL_SERVER_URL}...")

            # limits.md #142: no read timeout on the tool server's stream. mcp's default (300 s) ended any tool call
            # that ran longer, model calls inside it included; the lock sets no total time on a call
            # (LOCK.toml [generation] timeout "none"; a stalled call is the runner's to record)
            transport = await stack.enter_async_context(
                sse_client(f"{settings.TOOL_SERVER_URL}/sse", sse_read_timeout=None)
            )
            read_stream, write_stream = transport

            mcp_session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await mcp_session.initialize()

            mcp_tools_result = await mcp_session.list_tools()
            all_mcp_tools = mcp_tools_result.tools

            # Filter tools for lead_researcher (orchestrator) role
            # This removes execute_python and write_code which should use coder mode
            mcp_tools = [
                tool for tool in all_mcp_tools
                if is_tool_allowed(tool.name, "lead_researcher")
            ]

            filtered_count = len(all_mcp_tools) - len(mcp_tools)
            if filtered_count > 0:
                logger.info(f"Filtered {filtered_count} tools not allowed for orchestrator")

            logger.info(f"Connected. Discovered {len(all_mcp_tools)} tools, {len(mcp_tools)} available for orchestrator.")

        except Exception as e:
            err = f"Failed to connect to Tool Server: {e}"
            logger.error(err)
            # phase "tool_server": the run's set-up failed, not the system under test. Q93 (a) (D75): the run stops
            # (RunStop, as A4's reranker load failure): the server is started once per run and nothing restarts it.
            # The entry point records it as a setup error, so the question stays to do, and stops the run
            yield {"type": "error", "phase": "tool_server", "message": err}
            raise rr.RunStop(f"tool server: {err}") from e

        # Create async event callback and streaming helper
        event_queue: asyncio.Queue = asyncio.Queue()

        async def emit_event(event: Dict[str, Any]):
            """Callback to emit events from sub-functions."""
            await event_queue.put(event)

        async def _run_and_stream(coro):
            """Run a coroutine while concurrently draining the event queue."""
            task = asyncio.create_task(coro)
            
            while not task.done():
                # Create a task for getting the next event
                get_task = asyncio.create_task(event_queue.get())
                
                # Wait for either the main task to finish OR a new event to arrive
                done, pending = await asyncio.wait(
                    {task, get_task}, 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if get_task in done:
                    # We got an event! Yield it.
                    event = get_task.result()
                    
                    # Track token usage globally
                    if event.get("type") == "token_usage":
                         usage = event.get("token_usage", {})
                         state.total_tokens += usage.get("total", 0)
                         
                    yield event
                else:
                    # Main task finished, cancel the get wait
                    get_task.cancel()
            
            # Drain any remaining events after task completion
            while not event_queue.empty():
                event = await event_queue.get()
                if event.get("type") == "token_usage":
                     usage = event.get("token_usage", {})
                     state.total_tokens += usage.get("total", 0)
                yield event
                
            # Yield result wrapped in a special event
            yield {"type": "_internal_return", "value": await task}

        # ========================================
        # PHASE 0: QUERY ANALYSIS
        # ========================================
        state.phase = "analyzing"
        yield {"type": "status", "status": "Analyzing", "detail": "Understanding your request..."}
        yield {"type": "orchestrator_thinking_start", "phase": "analyzing"}

        analysis = None
        if switches["analyser"] == "off":
            # Q83 (a) (D75): the gate removed; every question goes to the planner and the tools, no model call
            analysis = AnalysisResult(decision="needs_plan", reasoning="Analyser switched off (D52)", complexity="",
                                      status="switched_off")
        else:
            async for event in _run_and_stream(analyze_query(
                model_router=model_router,
                model_identifier=model_identifier,
                messages=messages,
                tools=mcp_tools,
                session_context=session_context,
                think=think,
                event_callback=emit_event,
                memory_context=memory_context,
                prompt_variant=switches["analyser"],   # "on" (Mentori's prompt) or "factual_to_documents" (Q87)
            )):
                if event.get("type") == "_internal_return":
                    analysis = event["value"]
                else:
                    yield event

        # Save analysis to history
        if history_log is not None:
            history_log.append({
                "role": "assistant",
                "content": "",
                "thinking": analysis.thinking,
                "metadata_blob": {
                    "phase": "analyzing",
                    "decision": analysis.decision,
                    "complexity": analysis.complexity,
                    "reasoning": analysis.reasoning,
                    "agent_name": "Lead Researcher",
                    "model_name": display_model or model_identifier,
                }
            })

        logger.info(f"Analysis decision: {analysis.decision} (complexity: {analysis.complexity})")
        yield {
            "type": "record_analysis",
            "decision": analysis.decision,
            "complexity": analysis.complexity,
            "reasoning": analysis.reasoning,
            "status": analysis.status,
            "error": analysis.error,
        }

        # ========================================
        # DIRECT ANSWER PATH (skip planning)
        # ========================================
        if analysis.decision == "direct_answer":
            yield {
                "type": "direct_answer_mode",
                "reason": analysis.reasoning,
            }

            state.phase = "direct_answer"
            yield {"type": "status", "status": "Responding", "detail": "Generating response..."}

            final_answer = ""
            final_thinking = ""

            # generate_direct_answer is an async generator, so we iterate it directly
            # but we define a wrapper to hook into token counting if needed?
            # Actually, the generator yields events directly.
            async for event in generate_direct_answer(
                model_router=model_router,
                model_identifier=model_identifier,
                messages=messages,
                session_context=session_context,
                think=think,
            ):
                if event.get("type") == "token_usage":
                     usage = event.get("token_usage", {})
                     state.total_tokens += usage.get("total", 0)
                yield event
                
                if event.get("type") == "chunk":
                    final_answer += event["content"]
                if event.get("type") == "orchestrator_thinking":
                    final_thinking += event["content"]

            state.final_answer = final_answer

            # Save to history
            if history_log is not None:
                history_log.append({
                    "role": "assistant",
                    "content": final_answer,
                    "thinking": final_thinking,
                    "metadata_blob": {
                        "phase": "direct_answer",
                        "agent_name": "Lead Researcher",
                        "model_name": display_model or model_identifier,
                    }
                })

            yield {"type": "status", "status": "Ready", "detail": "Done."}
            yield {"type": "fs_update", "path": "/"}
            yield {"type": "complete", "content": final_answer, "final_answer_length": len(final_answer),
                   "plan_status": None, "answer_source": "direct_answer" if final_answer else None}

            # Trigger memory consolidation in background (Phase 2B); its outcome is kept (MEMORY_TASKS)
            MEMORY_TASKS[session_context.task_id] = asyncio.create_task(_consolidate(
                session_context,
                user_query=state.user_query,
                plan=None,  # No plan for direct answer
                step_results=[],
                final_answer=final_answer,
                model_router=model_router,
                event_callback=emit_event,
            ))
            return

        # ========================================
        # PHASE 1: PLANNING
        # ========================================
        state.phase = "planning"
        yield {"type": "status", "status": "Planning", "detail": "Creating execution plan..."}
        yield {"type": "orchestrator_thinking_start", "phase": "planning"}

        plan = None
        if switches["planner"] == "off":
            plan = fixed_plan(state.user_query, session_context)   # Q84 (a) (D75): no model call
        else:
            async for event in _run_and_stream(generate_plan(
                model_router=model_router,
                model_identifier=model_identifier,
                messages=messages,
                tools=mcp_tools,
                session_context=session_context,
                think=think,
                event_callback=emit_event,
                memory_context=memory_context,
            )):
                if event.get("type") == "_internal_return":
                    plan = event["value"]
                else:
                    yield event

        state.plan = plan

        # Yield plan info
        yield {
            "type": "plan_generated",
            "plan": plan.to_dict(),
        }

        # Save plan to history
        if history_log is not None:
            history_log.append({
                "role": "assistant",
                "content": f"**Execution Plan:**\n{plan.to_markdown()}",
                "thinking": plan.reasoning,
                "metadata_blob": {
                    "phase": "planning",
                    "plan_id": plan.plan_id,
                    "num_steps": len(plan.steps),
                    "plan": plan.to_dict(),
                    "agent_name": "Lead Researcher",
                    "model_name": display_model or model_identifier,
                }
            })

        logger.info(f"Plan generated: {plan.plan_id} with {len(plan.steps)} steps")
        # limits.md Class X and #27/#133: how the plan came to be, and whether max_steps cuts it (recorded when it binds)
        yield {
            "type": "record_plan",
            "generation_status": plan.generation_status,
            "generation_error": plan.generation_error,
            "steps_planned": len(plan.steps),
            "max_steps": max_steps,
            "steps_cut": max(0, len(plan.steps) - max_steps),
            "plan": plan.to_dict(),
        }

        # Check for empty plan
        if not plan.steps:
            # limits.md Class X: the empty plan is a failed plan, and the answer records it (plan_status "failed")
            plan.status = PlanStatus.FAILED
            yield {"type": "error", "phase": "planning", "status": plan.generation_status,
                   "plan_status": plan.status.value,
                   "message": "Failed to generate a valid plan. Please try rephrasing your question."}
            return

        # Limit steps
        if len(plan.steps) > max_steps:
            logger.warning(f"Plan has {len(plan.steps)} steps, limiting to {max_steps}")
            plan.steps = plan.steps[:max_steps]

        # ========================================
        # PHASE 1.5: PLAN APPROVAL (Collaboration)
        # ========================================
        # If configured to require approval OR if the plan explicitly requests it
        if session_context.require_plan_approval or plan.requires_confirmation:
            yield {
                "type": "plan_approval_required", 
                "plan": plan.to_dict(),
                "reasoning": plan.reasoning
            }
            
            # Wait for user approval
            if collaboration_context:
                state.pending_collaboration = {"tool": "present_plan", "plan_id": plan.plan_id}
                
                # Check if we already have a response (rare but possible in race conditions)
                if not collaboration_context.response_ready.is_set():
                    yield {"type": "paused", "reason": "Waiting for plan approval"}
                    logger.info("Paused execution, waiting for plan approval...")
                    await collaboration_context.response_ready.wait()
                    logger.info("Resumed from collaboration wait")
                
                response = collaboration_context.pending_response
                collaboration_context.reset()
                state.pending_collaboration = None
                
                if response:
                    logger.info(f"User response to plan: {response.action}")

                    if response.action == "abort":
                        logger.info(f"Task {session_context.task_id} aborted by user during plan approval")
                        yield {"type": "cancelled", "reason": "Task stopped by user"}
                        return

                    if response.action == "reject":
                        yield {"type": "plan_rejected", "reason": "Plan rejected by user"}
                        return

                    elif response.action == "modify":
                        # TODO: Handle plan modification logic
                        # For now, just log and proceed (or maybe replan?)
                        yield {"type": "status", "status": "Plan Modified", "detail": "Executing modified plan..."}
                        # Assume modifications applied to plan object elsewhere or here?
                        # For MVP, we'll assume approval for now
                        pass

                    # Emit resumed event after plan approval
                    yield {"type": "resumed", "detail": "Plan approved, starting execution"}
                    
        # ========================================
        # PHASE 2: EXECUTION
        # ========================================
        state.phase = "executing"
        plan.status = PlanStatus.IN_PROGRESS
        yield {"type": "status", "status": "Executing", "detail": f"Running {len(plan.steps)} steps..."}

        cumulative_tokens = 0

        while not plan.is_complete():
            # Check for task cancellation
            task_manager = _get_task_manager()
            if task_manager.is_cancelled(session_context.task_id):
                logger.info(f"Task {session_context.task_id} cancelled, stopping execution")
                yield {"type": "cancelled", "reason": "Task stopped by user"}
                return

            step = plan.current_step()
            if step is None:
                break

            # COLLABORATION TOOL INTERCEPTION
            COLLABORATION_TOOLS = ["ask_user", "present_plan", "share_progress", "report_failure", "propose_pivot"]
            if step.tool_name in COLLABORATION_TOOLS and collaboration_context:
                yield {
                    "type": "collaboration_required",
                    "tool": step.tool_name,
                    "payload": step.tool_args,
                    "step_id": step.step_id
                }
                
                state.pending_collaboration = {"tool": step.tool_name, "args": step.tool_args, "step_id": step.step_id}

                # Wait for user response
                logger.info(f"[ENGINE-COLLAB] Yielding paused event, waiting for response_ready...")
                yield {"type": "paused", "reason": f"Waiting for user input on {step.tool_name}"}
                await collaboration_context.response_ready.wait()
                logger.info(f"[ENGINE-COLLAB] response_ready was set! Woke up from wait.")

                response = collaboration_context.pending_response
                logger.info(f"[ENGINE-COLLAB] Got response: {response}")
                collaboration_context.reset()
                state.pending_collaboration = None

                # Check if this was a cancellation
                if response and response.action == "abort":
                    logger.info(f"[ENGINE-COLLAB] Task {session_context.task_id} aborted by user during collaboration")
                    yield {"type": "cancelled", "reason": "Task stopped by user"}
                    return

                # Emit resumed event to signal continuation
                logger.info(f"[ENGINE-COLLAB] Yielding resumed event...")
                yield {"type": "resumed", "step_id": step.step_id, "detail": "Collaboration complete, processing your response..."}

                # Get the user's clarification
                user_content = str(response.response) if response else "No response provided"
                original_question = step.tool_args.get("question", "the previous question")

                # Log the ask_user step as completed
                if history_log is not None:
                    history_log.append({
                        "role": "assistant",
                        "content": f"**Step {step.step_id}**: {step.description}\n\n**Asked user**: {original_question}",
                        "tool_calls": [{"function": {"name": step.tool_name, "arguments": step.tool_args}}],
                        "metadata_blob": {"phase": "executing", "step_id": step.step_id, "agent_name": "Lead Researcher"}
                    })
                    history_log.append({
                        "role": "tool",
                        "content": user_content,
                        "name": step.tool_name
                    })

                yield {
                    "type": "step_complete",
                    "step_id": step.step_id,
                    "status": "completed",
                    "summary": f"User clarified: {user_content[:100]}..."
                }

                # === RE-PLAN with the user's clarification ===
                # The key insight: when user clarifies something, we should generate
                # a NEW plan that incorporates their clarification, not blindly continue.

                yield {"type": "status", "status": "Re-planning", "detail": "Creating new plan with your clarification..."}
                yield {"type": "orchestrator_thinking_start", "phase": "planning"}

                # Build updated messages with the clarification context
                clarification_context = f"\n\n**User Clarification**: The agent asked: \"{original_question}\"\nThe user responded: \"{user_content}\"\n\nPlease create a plan that addresses the user's original request with this clarification in mind."

                # Create updated messages for re-planning
                updated_messages = messages.copy()
                # Append the clarification as additional context
                if updated_messages and updated_messages[-1].get("role") == "user":
                    # Append to the last user message
                    updated_messages[-1] = {
                        **updated_messages[-1],
                        "content": updated_messages[-1].get("content", "") + clarification_context
                    }
                else:
                    # Add as new user message
                    updated_messages.append({
                        "role": "user",
                        "content": clarification_context
                    })

                # Generate a new plan (without event streaming for simplicity)
                logger.info(f"[ENGINE-COLLAB] Calling generate_plan for re-planning...")
                try:
                    new_plan = await generate_plan(
                        model_router=model_router,
                        model_identifier=model_identifier,
                        messages=updated_messages,
                        tools=mcp_tools,  # Use the same tools as the original plan
                        session_context=session_context,
                        think=think,
                        event_callback=None,  # Skip streaming for re-plan
                        memory_context=memory_context,
                    )
                    logger.info(f"[ENGINE-COLLAB] Re-plan generated successfully: {new_plan.goal if new_plan else 'None'}")
                except Exception as e:
                    logger.error(f"[ENGINE-COLLAB] Re-plan FAILED with error: {e}", exc_info=True)
                    raise

                # Replace the current plan with the new one
                plan = new_plan
                state.plan = plan

                logger.info(f"[ENGINE-COLLAB] Yielding plan_generated event...")
                yield {
                    "type": "plan_generated",
                    "plan": plan.to_dict(),
                    "reasoning": plan.reasoning,
                    "replanned": True,
                    "clarification": user_content
                }

                # Log the new plan to history
                if history_log is not None:
                    plan_md = f"**Re-planned after user clarification**\n\n**Goal:** {plan.goal}\n\n**Steps:**\n"
                    for i, s in enumerate(plan.steps, 1):
                        plan_md += f"{i}. {s.description} (Agent: {s.agent_role}, Tool: {s.tool_name})\n"
                    history_log.append({
                        "role": "assistant",
                        "content": plan_md,
                        "metadata_blob": {"phase": "replanning", "agent_name": "Lead Researcher"}
                    })

                yield {"type": "status", "status": "Executing", "detail": f"Running {len(plan.steps)} steps..."}

                # Continue execution with the new plan (loop will pick up first step)
                continue

            # Execute the step - route to Coder agent for coding tasks
            result = None
            # Q23 (D68): which attempt of this step this is; every attempt is recorded under its number
            attempt_no = 1 + sum(1 for r in state.step_results if r.get("step_id") == step.step_id)

            # Check if this is a Coder step (execute_python with coder role)
            # The Coder Agent handles the full workflow: algorithm → code → execute → retry
            is_coder_step = (
                step.agent_role == "coder" and
                step.tool_name == "execute_python"
            )
            if is_coder_step:
                logger.info(f"Routing step {step.step_id} to Coder Agent (execute_python)")

            if is_coder_step:
                # Use the Coder Agent with algorithm design + code generation
                logger.info(f"Routing step {step.step_id} to Coder Agent")
                step_generator = execute_coder_step(
                    step=step,
                    model_router=model_router,
                    session_context=session_context,
                    mcp_session=mcp_session,
                    previous_results=state.step_results,
                    plan_goal=plan.goal,
                    collaboration_context=collaboration_context,
                    event_callback=emit_event,
                    attempt_no=attempt_no,
                )
            else:
                # Use standard executor for non-coding steps
                step_generator = execute_step(
                    step=step,
                    model_router=model_router,
                    session_context=session_context,
                    mcp_session=mcp_session,
                    previous_results=state.step_results,
                    attempt_no=attempt_no,
                )

            async for event in step_generator:
                event_type = event.get("type", "unknown")
                if event_type == "_step_result":
                    # Capture the final result
                    result = event["result"]
                else:
                    # Yield event immediately to frontend
                    if event_type == "token_usage":
                         usage = event.get("token_usage", {})
                         state.total_tokens += usage.get("total", 0)
                         cumulative_tokens += usage.get("total", 0)

                    yield event

            # Add result to state
            if result:
                state.add_step_result(result)
                # records.md F14: the attempt's record, raw_content included, before to_dict() drops it
                yield {
                    "type": "record_step",
                    "step": {
                        "step_id": step.step_id,
                        "description": step.description,
                        "agent_role": step.agent_role,
                        "tool_name": step.tool_name,
                        **result.to_record(),
                    },
                }
            else:
                # Shouldn't happen, but handle gracefully
                logger.error(f"No result received from step {step.step_id}")
                yield {"type": "error", "phase": "executing", "status": "no_result",
                       "message": f"No result received from step {step.step_id}"}
                break

            # Save step to history
            if history_log is not None:
                history_log.append({
                    "role": "assistant",
                    "content": f"**Step {step.step_id}**: {step.description}\n\n**Result**: {result.summary}",
                    "thinking": result.agent_thinking,
                    "tool_calls": [{"function": {"name": step.tool_name, "arguments": step.tool_args}}],
                    "metadata_blob": {
                        "phase": "executing",
                        "step_id": step.step_id,
                        "agent_role": step.agent_role,
                        "tool_name": step.tool_name,
                        "success": result.success,
                        "agent_name": get_agent_display_name(step.agent_role), 
                        # We need to get model name from router or context ideally?
                        # executor.py knows it. Ideally execute_step should yield it in step_start?
                        # It definitely yields session_info sometimes.
                    }
                })
                # Also save tool result
                history_log.append({
                    "role": "tool",
                    "content": result.content,
                    "name": step.tool_name,
                })

            # Yield step completion
            yield {
                "type": "step_complete" if result.success else "step_failed",
                "step_id": step.step_id,
                "status": "completed" if result.success else "failed",
                "summary": result.summary,
            }

            # Check token budget
            if token_budget and cumulative_tokens > token_budget:
                yield {
                    "type": "budget_exceeded",
                    "tokens_used": cumulative_tokens,
                    "budget": token_budget,
                    "message": f"Token budget exceeded: {cumulative_tokens}/{token_budget}"
                }
                logger.warning(f"Token budget exceeded: {cumulative_tokens}/{token_budget}")
                break

            # ========================================
            # STEP EVALUATION (Phase 2A: Supervisor Agent)
            # ========================================
            if switches["supervisor"] == "off":
                # Q85 (a) (D75): the whole phase off, no evaluation, no retry; the step runs once and the plan moves
                # on. What Mentori's text pre-check would have said is recorded, not acted on
                yield {
                    "type": "supervisor_evaluation",
                    "step_id": step.step_id,
                    "attempt_no": attempt_no,
                    "quality_score": None,
                    "control_score": None,
                    "status": "switched_off",
                    "error": None,
                    "issues": [],
                    "should_retry": False,
                    "should_escalate": False,
                    "reasoning": None,
                    "heuristic": _silent_precheck(result),
                }
                plan.advance()
                continue

            yield {"type": "orchestrator_thinking_start", "phase": "supervising"}
            yield {"type": "status", "status": "Supervising", "detail": f"Evaluating step {step.step_id} quality..."}

            # Use Supervisor for quality-based evaluation
            supervisor_eval = None
            async for event in _run_and_stream(evaluate_step_quality(
                step=step,
                result=result,
                goal=plan.goal,
                # Q88 (D75): the attempt being judged is the last stored result; it is under "Actual Result" and left
                # out of "Previous Steps Context" (earlier steps, and an earlier rejected attempt of this step, stay)
                previous_results=_supervisor_previous(state.step_results),
                model_router=model_router,
                model_identifier=model_identifier,
                think=think,
                event_callback=emit_event,
                user_id=session_context.user_id,
            )):
                if event.get("type") == "_internal_return":
                    supervisor_eval = event["value"]
                else:
                    yield event

            # Emit supervisor evaluation event for frontend. quality_score is None when the evaluation failed or was
            # unparsed; control_score is the value Mentori's control flow used (A5; SupervisorEvaluation.to_dict)
            eval_record = supervisor_eval.to_dict()
            yield {
                "type": "supervisor_evaluation",
                "step_id": step.step_id,
                "attempt_no": attempt_no,
                "quality_score": eval_record["quality_score"],
                "control_score": eval_record["control_score"],
                "status": eval_record["status"],
                "error": eval_record["error"],
                "issues": supervisor_eval.issues,
                "should_retry": supervisor_eval.should_retry,
                "should_escalate": supervisor_eval.should_escalate,
                "reasoning": supervisor_eval.reasoning,
            }

            # Save evaluation to history
            if history_log is not None:
                history_log.append({
                    "role": "assistant",
                    "content": "",
                    "thinking": supervisor_eval.thinking,
                    "metadata_blob": {
                        "phase": "supervising",
                        "step_id": step.step_id,
                        "quality_score": supervisor_eval.quality_score,
                        "issues": supervisor_eval.issues,
                        "should_retry": supervisor_eval.should_retry,
                        "should_escalate": supervisor_eval.should_escalate,
                        "agent_name": "Supervisor",
                        "model_name": display_model or model_identifier,
                    }
                })

            # Update supervisor tracking for reflection triggers
            update_supervisor_tracking(state, step, supervisor_eval)

            # ========================================
            # MICRO-ADJUSTMENT RETRY LOOP
            # ========================================
            if supervisor_eval.should_retry and step.retry_count < MAX_STEP_RETRIES:
                # Get micro-adjustment suggestion
                previous_adjustments = []  # Track adjustments for this step

                adjustment = None
                async for event in _run_and_stream(suggest_micro_adjustment(
                    step=step,
                    result=result,
                    issues=supervisor_eval.issues,
                    previous_adjustments=previous_adjustments,
                    model_router=model_router,
                    model_identifier=model_identifier,
                    think=think,
                    event_callback=emit_event,
                )):
                    if event.get("type") == "_internal_return":
                        adjustment = event["value"]
                    else:
                        yield event

                # Emit micro-adjustment event
                yield {
                    "type": "micro_adjustment",
                    "step_id": step.step_id,
                    "attempt_number": step.retry_count + 1,
                    "adjustment_type": adjustment.adjustment_type,
                    "adjustment_reasoning": adjustment.adjustment_reasoning,
                    "original_args": adjustment.original_args,
                    "adjusted_args": adjustment.adjusted_args,
                    "status": adjustment.status,
                    "error": adjustment.error,
                }

                # Apply adjustment and retry
                step.tool_args = adjustment.adjusted_args
                step.retry_count += 1
                previous_adjustments.append(adjustment.adjustment_reasoning)

                logger.info(f"Retrying step {step.step_id} (attempt {step.retry_count}) with adjustment: {adjustment.adjustment_type}")

                # Don't advance - will re-execute this step on next loop iteration
                continue

            # Check if we need to escalate (P3-A: Human-in-the-Loop)
            if supervisor_eval.should_escalate:
                logger.warning(f"Step {step.step_id} needs escalation (quality: {supervisor_eval.quality_score})")

                if collaboration_context:
                    # Pause execution — emit event and wait for user decision
                    yield {
                        "type": "human_intervention_required",
                        "step_id": step.step_id,
                        "step_description": step.description,
                        "reason": f"Quality score {supervisor_eval.quality_score}/100 after {step.retry_count} retries",
                        "issues": supervisor_eval.issues,
                        "attempts": step.retry_count,
                    }
                    yield {"type": "paused", "reason": f"Waiting for user decision on step {step.step_id}"}

                    if not collaboration_context.response_ready.is_set():
                        await collaboration_context.response_ready.wait()

                    response = collaboration_context.pending_response
                    collaboration_context.reset()

                    if response:
                        logger.info(f"User intervention decision for step {step.step_id}: {response.action}")

                        if response.action == "abort":
                            yield {"type": "cancelled", "reason": "Task aborted by user after step failure"}
                            return

                        elif response.action == "skip":
                            yield {"type": "human_intervention_resolved", "step_id": step.step_id, "action": "skip"}
                            yield {"type": "resumed", "detail": "Skipping failed step, continuing with plan..."}
                            plan.advance()
                            continue

                        elif response.action == "retry":
                            step.retry_count = 0  # Reset so supervisor allows retries again
                            yield {"type": "human_intervention_resolved", "step_id": step.step_id, "action": "retry"}
                            yield {"type": "resumed", "detail": "Retrying step from scratch..."}
                            continue  # Re-execute same step without advancing

                # No collaboration context, or user gave no actionable response — count as failure
                state.consecutive_failures += 1
                if state.consecutive_failures >= state.max_failures:
                    yield {
                        "type": "error",
                        "message": f"Quality issues after retries. Issues: {', '.join(supervisor_eval.issues)}",
                        "phase": "executing"
                    }
                    plan.status = PlanStatus.FAILED
                    break

            # Good quality - reset failure counter and advance
            if supervisor_eval.is_good_quality():
                state.consecutive_failures = 0

            # Advance to next step
            plan.advance()

        # Check if plan completed successfully
        if plan.is_complete():
            plan.status = PlanStatus.COMPLETED

        # ========================================
        # PHASE 3: SYNTHESIS
        # ========================================
        state.phase = "synthesizing"
        yield {"type": "status", "status": "Synthesizing", "detail": "Combining results..."}
        yield {"type": "orchestrator_thinking_start", "phase": "synthesizing"}

        final_answer = ""
        final_thinking = ""
        synthesis_failed = False   # A5: a synthesis error event; its partial text or thinking is never the answer

        # Disable thinking for synthesis - we just need the final answer, not reasoning
        # With [think:high], some models get stuck in reasoning mode and produce empty content
        synthesis_think = False

        if switches["synthesiser"] == "off":
            # Q86 (b) (D75): no model call; the answer is exactly the text synthesis would have read
            # (format_steps_with_results: each step's last attempt, Q23, its content as stored, Q24, in plan order)
            if not state.plan or not state.step_results:
                yield {"type": "error", "phase": "synthesis", "status": "no_results",
                       "message": "Synthesiser switched off and no step results", "error": None,
                       "call_status": None, "call_seq": None}
                synthesis_failed = True
            else:
                final_answer = format_steps_with_results(state.plan.steps, state.step_results)
                yield {"type": "chunk", "content": final_answer}
        else:
            # synthesize_answer is an async generator
            async for event in synthesize_answer(
                state=state,
                model_router=model_router,
                model_identifier=model_identifier,
                session_context=session_context,
                think=synthesis_think,
            ):
                if event.get("type") == "token_usage":
                     usage = event.get("token_usage", {})
                     state.total_tokens += usage.get("total", 0)
                yield event

                if event.get("type") == "chunk":
                    final_answer += event["content"]
                if event.get("type") == "orchestrator_thinking":
                    final_thinking += event["content"]
                if event.get("type") == "error":
                    synthesis_failed = True

        # Fallback: If model produced thinking but no content (common with [think:high]),
        # use the thinking as the final answer. Q26 (D68): Mentori's fallback is kept, and the answer records that
        # its text came from thinking (answer_source "thinking_fallback"; calls.md R7). After a synthesis error
        # event it is not taken (A5: a failed call's thinking never becomes the answer)
        answer_source = "content" if final_answer.strip() else None
        if switches["synthesiser"] == "off" and final_answer.strip():
            answer_source = "steps_text"   # Q86: the steps' text, no synthesis call
        if not final_answer.strip() and final_thinking.strip() and not synthesis_failed:
            logger.warning("Synthesis produced thinking but no content - using thinking as answer")
            final_answer = final_thinking
            answer_source = "thinking_fallback"
            # Emit the thinking content as chunks for the frontend
            yield {"type": "chunk", "content": final_thinking}

        state.final_answer = final_answer
        state.phase = "complete"

        # Save final answer to history
        if history_log is not None:
            history_log.append({
                "role": "assistant",
                "content": final_answer,
                "thinking": final_thinking,
                "metadata_blob": {
                    "phase": "synthesizing",
                    "plan_id": plan.plan_id if plan else None,
                    "total_steps": len(state.step_results),
                    "agent_name": "Lead Researcher",
                    "model_name": display_model or model_identifier,
                }
            })
            logger.info(f"Orchestration complete. History has {len(history_log)} entries.")

        # Final status
        yield {"type": "status", "status": "Ready", "detail": "Done."}
        yield {"type": "fs_update", "path": "/"}
        yield {
            "type": "complete",
            "content": final_answer,
            "final_answer_length": len(final_answer),
            "total_steps": len(state.step_results),
            "total_tokens": state.total_tokens,
            "plan_status": plan.status.value,
            "answer_source": answer_source,
        }

        # Trigger memory consolidation in background (Phase 2B); its outcome is kept (MEMORY_TASKS)
        # Build step_id -> PlanStep lookup for tool info
        step_lookup = {s.step_id: s for s in plan.steps} if plan and plan.steps else {}

        # Convert step results to dict format for memory
        # Note: state.step_results already contains dicts (via StepResult.to_dict())
        step_results_dicts = []
        for r in state.step_results:
            step_id = r.get("step_id", "")
            plan_step = step_lookup.get(step_id)
            step_results_dicts.append({
                "step_id": step_id,
                "tool_name": plan_step.tool_name if plan_step else "unknown",
                "tool_args": plan_step.tool_args if plan_step else {},
                "content": r.get("content", "") or "",   # D25 (cuts.md engine.py:986): whole
                "success": r.get("success", False),
                "summary": r.get("summary", ""),
                "step_description": plan_step.description if plan_step else "Unknown step",
            })

        MEMORY_TASKS[session_context.task_id] = asyncio.create_task(_consolidate(
            session_context,
            user_query=state.user_query,
            plan=plan,
            step_results=step_results_dicts,
            final_answer=final_answer,
            model_router=model_router,
            event_callback=emit_event,
        ))
