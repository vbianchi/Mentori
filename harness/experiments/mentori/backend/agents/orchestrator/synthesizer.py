"""
Synthesis module for the Orchestrator.

Handles:
- Final answer synthesis from step results
- Direct answer generation (when no plan is needed)
- Response streaming with visible thinking
"""

import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Union

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext, get_logger
from backend.agents.orchestrator.schemas import OrchestratorState, ExecutionPlan
from backend.agents.orchestrator.prompts import (
    ORCHESTRATOR_SYNTHESIZER_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    DIRECT_ANSWER_PROMPT,
    format_conversation_context,
    format_steps_with_results,
    format_user_context,
    last_attempt,
)
from backend.agents.orchestrator import run_records as rr

logger = get_logger(__name__)

# Mentori's count of recent conversation messages in the direct-answer prompt (cuts.md prompts.py:797), kept and
# stated; exp_03 sends one message per question, so it does not bind there
DIRECT_ANSWER_MESSAGES = 10


def _failure_event(phase: str, e: BaseException) -> Dict[str, Any]:
    """A synthesis or direct-answer failure as an error event (limits.md Class X, records.md F16; A5): never a chunk,
    so no error text reaches the answer."""
    return {"type": "error", "phase": phase, "message": f"{phase} failed: {e}", **rr.failure(e)}


async def synthesize_answer(
    state: OrchestratorState,
    model_router: ModelRouter,
    model_identifier: str,
    session_context: SessionContext,
    think: Union[bool, str] = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Synthesize the final answer from completed plan steps.

    Phase 3 of orchestration.

    Streams both thinking (for UI visibility) and final answer chunks.

    Args:
        state: Current orchestrator state with step results
        model_router: Router for LLM calls
        model_identifier: Model to use
        session_context: Current session context
        think: Thinking mode

    Yields:
        Events: orchestrator_thinking (for thinking), chunk (for answer)
    """
    if not state.plan or not state.step_results:
        logger.warning("Synthesis called without plan or results")
        # records.md F16 (A5): Mentori sent "I apologize, but I couldn't complete the analysis." as the answer;
        # it is an error event now, and the answer stays empty
        yield {"type": "error", "phase": "synthesis", "status": "no_results",
               "message": "Synthesis called without plan or results", "error": None,
               "call_status": None, "call_seq": None}
        return

    # Format step results for the prompt
    steps_with_results = format_steps_with_results(
        state.plan.steps,
        state.step_results
    )

    # Format user context for personalization
    user_context = format_user_context(session_context)

    # Build synthesis prompt
    prompt = ORCHESTRATOR_SYNTHESIZER_PROMPT.format(
        user_query=state.user_query,
        plan_goal=state.plan.goal,
        steps_with_results=steps_with_results,
        user_context=user_context,
    )

    # P1-E-3/E-4: Stable system prefix + dynamic user suffix.
    # The stable system message enables KV-cache reuse across synthesis calls;
    # only the XML-tagged task context (user message) changes per query.
    synthesis_messages = [
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    logger.info(f"Synthesizing answer from {len(state.step_results)} step results...")

    # A6, D37: the passages the prompt holds whole, from the attempt of each step that synthesis reads (Q23)
    read = [last_attempt(state.step_results, s.step_id) for s in state.plan.steps]
    rr.set_passages(rr.passages_carried(r for r in read if r))
    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=synthesis_messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Stream thinking
                    if "thinking" in delta:
                        yield {
                            "type": "orchestrator_thinking",
                            "content": delta["thinking"],
                            "phase": "synthesizing"
                        }

                    # Stream answer content
                    if "content" in delta:
                        yield {
                            "type": "chunk",
                            "content": delta["content"]
                        }

                # Handle token usage from final chunk
                if data.get("done") is True and "eval_count" in data:
                    yield {
                        "type": "token_usage",
                        "token_usage": {
                            "input": data.get("prompt_eval_count", 0),
                            "output": data.get("eval_count", 0),
                            "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                        },
                        "source": "orchestrator:synthesis"
                    }

                # Handle Gemini-style token usage
                if "usage" in data:
                    usage = data["usage"]
                    yield {
                        "type": "token_usage",
                        "token_usage": {
                            "input": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                            "output": usage.get("output_tokens", usage.get("completion_tokens", 0)),
                            "total": usage.get("total_tokens", 0),
                        },
                        "source": "orchestrator:synthesis"
                    }

            except json.JSONDecodeError:
                continue

    except rr.REFUSALS:
        raise  # Q38 (D69): a lock refusal is a setup error and fails the question
    except Exception as e:
        logger.error(f"Error during synthesis: {e}")
        yield _failure_event("synthesis", e)   # limits.md Class X: was a chunk "[Error during synthesis: ...]"


async def generate_direct_answer(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    session_context: SessionContext,
    think: Union[bool, str] = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate a direct answer without going through the planning phase.

    Used when the query analysis determines no tools are needed
    (e.g., greetings, meta questions, simple clarifications).

    Args:
        model_router: Router for LLM calls
        model_identifier: Model to use
        messages: Full conversation history
        session_context: Current session context
        think: Thinking mode

    Yields:
        Events: orchestrator_thinking (for thinking), chunk (for answer)
    """
    # Extract user query
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break

    # Format conversation context
    conversation_context = format_conversation_context(messages, max_messages=DIRECT_ANSWER_MESSAGES)

    # Format user context for personalization
    user_context = format_user_context(session_context)

    # Build direct answer prompt
    prompt = DIRECT_ANSWER_PROMPT.format(
        user_query=user_query,
        conversation_context=conversation_context,
        user_context=user_context,
    )

    direct_messages = [
        {"role": "system", "content": "You are Mentori Lead Researcher, a helpful scientific assistant."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Generating direct answer for: {user_query[:50]}...")

    rr.set_passages([])   # A6, D37: the direct answer's prompt carries no passage
    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=direct_messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Stream thinking
                    if "thinking" in delta:
                        yield {
                            "type": "orchestrator_thinking",
                            "content": delta["thinking"],
                            "phase": "direct_answer"
                        }

                    # Stream answer content
                    if "content" in delta:
                        yield {
                            "type": "chunk",
                            "content": delta["content"]
                        }

                # Handle token usage
                if data.get("done") is True and "eval_count" in data:
                    yield {
                        "type": "token_usage",
                        "token_usage": {
                            "input": data.get("prompt_eval_count", 0),
                            "output": data.get("eval_count", 0),
                            "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                        },
                        "source": "orchestrator:direct"
                    }

                if "usage" in data:
                    usage = data["usage"]
                    yield {
                        "type": "token_usage",
                        "token_usage": {
                            "input": usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                            "output": usage.get("output_tokens", usage.get("completion_tokens", 0)),
                            "total": usage.get("total_tokens", 0),
                        },
                        "source": "orchestrator:direct"
                    }

            except json.JSONDecodeError:
                continue

    except rr.REFUSALS:
        raise  # Q38 (D69): a lock refusal is a setup error and fails the question
    except Exception as e:
        logger.error(f"Error during direct answer: {e}")
        # limits.md Class X (A5): was a chunk "I apologize, but I encountered an error: ..."
        yield _failure_event("direct_answer", e)
