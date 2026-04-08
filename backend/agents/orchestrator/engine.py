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
"""

import asyncio
import re
from contextlib import AsyncExitStack
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
)
from backend.agents.orchestrator.planner import (
    analyze_query,
    generate_plan,
)
from backend.agents.orchestrator.supervisor import (
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

    # Ensure standard task directories exist
    workspace_path = Path(session_context.workspace_path)
    (workspace_path / "outputs").mkdir(parents=True, exist_ok=True)
    (workspace_path / "files").mkdir(parents=True, exist_ok=True)

    # Load memory vault for this task (Phase 2B)
    memory_context = ""
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

    # Connect to MCP Tool Server
    async with AsyncExitStack() as stack:
        try:
            logger.info(f"Connecting to Tool Server at {settings.TOOL_SERVER_URL}...")

            transport = await stack.enter_async_context(
                sse_client(f"{settings.TOOL_SERVER_URL}/sse")
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
            yield {"type": "error", "message": err}
            return

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
        async for event in _run_and_stream(analyze_query(
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
            yield {"type": "complete", "content": final_answer, "final_answer_length": len(final_answer)}

            # Trigger memory consolidation in background (Phase 2B)
            async def _consolidate_direct_answer():
                try:
                    librarian_model = session_context.agent_roles.get("librarian") or session_context.agent_roles.get("default")
                    if librarian_model:
                        await consolidate_session_memory(
                            task_id=session_context.task_id,
                            user_id=session_context.user_id,
                            workspace_path=Path(session_context.workspace_path),
                            user_query=state.user_query,
                            plan=None,  # No plan for direct answer
                            step_results=[],
                            final_answer=final_answer,
                            model_router=model_router,
                            librarian_model=librarian_model,
                            event_callback=emit_event,
                        )
                        logger.info("Memory consolidation complete (direct answer)")
                except Exception as e:
                    logger.warning(f"Memory consolidation failed: {e}")

            asyncio.create_task(_consolidate_direct_answer())
            return

        # ========================================
        # PHASE 1: PLANNING
        # ========================================
        state.phase = "planning"
        yield {"type": "status", "status": "Planning", "detail": "Creating execution plan..."}
        yield {"type": "orchestrator_thinking_start", "phase": "planning"}

        plan = None
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

        # Check for empty plan
        if not plan.steps:
            yield {"type": "error", "message": "Failed to generate a valid plan. Please try rephrasing your question."}
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
                )
            else:
                # Use standard executor for non-coding steps
                step_generator = execute_step(
                    step=step,
                    model_router=model_router,
                    session_context=session_context,
                    mcp_session=mcp_session,
                    previous_results=state.step_results,
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
            else:
                # Shouldn't happen, but handle gracefully
                logger.error(f"No result received from step {step.step_id}")
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
            yield {"type": "orchestrator_thinking_start", "phase": "supervising"}
            yield {"type": "status", "status": "Supervising", "detail": f"Evaluating step {step.step_id} quality..."}

            # Use Supervisor for quality-based evaluation
            supervisor_eval = None
            async for event in _run_and_stream(evaluate_step_quality(
                step=step,
                result=result,
                goal=plan.goal,
                previous_results=state.step_results,
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

            # Emit supervisor evaluation event for frontend
            yield {
                "type": "supervisor_evaluation",
                "step_id": step.step_id,
                "quality_score": supervisor_eval.quality_score,
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
            if supervisor_eval.should_retry and step.retry_count < 3:
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

        # Disable thinking for synthesis - we just need the final answer, not reasoning
        # With [think:high], some models get stuck in reasoning mode and produce empty content
        synthesis_think = False

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

        # Fallback: If model produced thinking but no content (common with [think:high]),
        # use the thinking as the final answer
        if not final_answer.strip() and final_thinking.strip():
            logger.warning("Synthesis produced thinking but no content - using thinking as answer")
            final_answer = final_thinking
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
        }

        # Trigger memory consolidation in background (Phase 2B)
        async def _consolidate_orchestrated():
            try:
                librarian_model = session_context.agent_roles.get("librarian") or session_context.agent_roles.get("default")
                if librarian_model:
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
                            "content": (r.get("content", "") or "")[:1000],  # Truncate long content
                            "success": r.get("success", False),
                            "summary": r.get("summary", ""),
                            "step_description": plan_step.description if plan_step else "Unknown step",
                        })

                    await consolidate_session_memory(
                        task_id=session_context.task_id,
                        user_id=session_context.user_id,
                        workspace_path=Path(session_context.workspace_path),
                        user_query=state.user_query,
                        plan=plan,
                        step_results=step_results_dicts,
                        final_answer=final_answer,
                        model_router=model_router,
                        librarian_model=librarian_model,
                        event_callback=emit_event,
                    )
                    logger.info("Memory consolidation complete (orchestrated)")
            except Exception as e:
                logger.warning(f"Memory consolidation failed: {e}")

        asyncio.create_task(_consolidate_orchestrated())
