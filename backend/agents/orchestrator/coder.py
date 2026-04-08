"""
Coder Agent module for the Orchestrator.

The Coder Agent is a reasoning agent that:
1. Designs algorithms step-by-step before coding
2. Generates code based on the algorithm
3. Executes code with self-correction on errors
4. Escalates to human when stuck

This provides transparency into the coding process and enables
more reliable code generation through structured reasoning.

Phase 2A+ implementation.
"""

import json
import re
from typing import Dict, Any, Optional, Callable, Awaitable, AsyncGenerator, List

from backend.agents.model_router import ModelRouter
from backend.agents.session_context import SessionContext, get_logger
from backend.agents.orchestrator.schemas import PlanStep, StepResult
from backend.agents.orchestrator.prompts import (
    CODER_ALGORITHM_PROMPT,
    CODER_GENERATION_PROMPT,
    CODER_ERROR_ANALYSIS_PROMPT,
)

logger = get_logger(__name__)

# Maximum self-correction attempts before asking for help
MAX_RETRY_ATTEMPTS = 3


def _parse_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM response."""
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


def _extract_code_from_response(content: str) -> str:
    """Extract Python code from LLM response."""
    if not content:
        return ""

    # Try to extract from python code block
    python_block = re.search(r'```python\s*([\s\S]*?)\s*```', content)
    if python_block:
        return python_block.group(1).strip()

    # Try generic code block
    generic_block = re.search(r'```\s*([\s\S]*?)\s*```', content)
    if generic_block:
        return generic_block.group(1).strip()

    # If no code blocks, return trimmed content
    return content.strip()


async def design_algorithm(
    step: PlanStep,
    previous_results: List[Dict[str, Any]],
    plan_goal: str,
    model_router: ModelRouter,
    model_identifier: str,
    session_context: SessionContext,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """
    Phase 1: Design the algorithm before coding.

    The Coder thinks through the problem and creates a step-by-step
    algorithm skeleton that will guide code generation.

    Args:
        step: The plan step with task description
        previous_results: Results from previous steps (for context)
        plan_goal: The overall goal we're trying to achieve
        model_router: Router for LLM calls
        model_identifier: Model to use
        session_context: Current session context
        think: Thinking mode
        event_callback: Callback to emit events

    Returns:
        Dict with algorithm steps and reasoning
    """
    # Format previous results for context
    context_parts = []
    for prev in previous_results[-3:]:  # Last 3 results
        step_id = prev.get("step_id", "unknown")
        content = prev.get("content", "")[:500]  # Truncate
        context_parts.append(f"- {step_id}: {content}")
    previous_context = "\n".join(context_parts) if context_parts else "(No previous results)"

    # Build the algorithm design prompt
    prompt = CODER_ALGORITHM_PROMPT.format(
        task_description=step.description,
        plan_goal=plan_goal,
        previous_results=previous_context,
        workspace_path=session_context.workspace_path,
        tool_args=json.dumps(step.tool_args, indent=2),
    )

    messages = [
        {"role": "system", "content": "You are the Coder Agent. Design algorithms step-by-step before writing code."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Coder designing algorithm for step {step.step_id}...")

    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Collect and stream thinking
                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "coder_thinking",
                                "phase": "algorithm",
                                "content": thinking_chunk,
                                "step_id": step.step_id,
                            })

                    # Collect content
                    if "content" in delta:
                        content_chunk = delta["content"]
                        full_content += content_chunk
                        if event_callback:
                            await event_callback({
                                "type": "coder_algorithm_chunk",
                                "content": content_chunk,
                                "step_id": step.step_id,
                            })

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
                            "source": "coder:algorithm"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Algorithm design error: {e}")
        return {
            "success": False,
            "algorithm_steps": [],
            "reasoning": f"Failed to design algorithm: {str(e)}",
            "thinking": full_thinking,
        }

    # Parse the algorithm from response
    parsed = _parse_json_from_response(full_content)

    if parsed:
        algorithm = {
            "success": True,
            "algorithm_steps": parsed.get("steps", parsed.get("algorithm_steps", [])),
            "reasoning": parsed.get("reasoning", ""),
            "data_requirements": parsed.get("data_requirements", []),
            "output_format": parsed.get("output_format", ""),
            "thinking": full_thinking,
        }
    else:
        # Fallback: try to extract steps from plain text
        algorithm = {
            "success": True,
            "algorithm_steps": [full_content],  # Use raw content as single step
            "reasoning": "Algorithm extracted from response",
            "thinking": full_thinking,
        }

    # Emit algorithm complete event
    if event_callback:
        await event_callback({
            "type": "coder_algorithm_complete",
            "step_id": step.step_id,
            "algorithm": algorithm,
        })

    logger.info(f"Algorithm designed with {len(algorithm.get('algorithm_steps', []))} steps")
    return algorithm


async def generate_code(
    step: PlanStep,
    algorithm: Dict[str, Any],
    previous_results: List[Dict[str, Any]],
    model_router: ModelRouter,
    model_identifier: str,
    session_context: SessionContext,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    error_context: Optional[str] = None,  # For retries
) -> Dict[str, Any]:
    """
    Phase 2: Generate code based on the algorithm.

    Takes the algorithm skeleton and produces executable Python code.

    Args:
        step: The plan step
        algorithm: The algorithm from Phase 1
        previous_results: Previous step results for context
        model_router: Router for LLM calls
        model_identifier: Model to use
        session_context: Current session context
        think: Thinking mode
        event_callback: Callback to emit events
        error_context: If retrying, the error from previous attempt

    Returns:
        Dict with generated code and metadata
    """
    # Format algorithm steps
    algorithm_steps = algorithm.get("algorithm_steps", [])
    if isinstance(algorithm_steps, list):
        algorithm_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(algorithm_steps))
    else:
        algorithm_text = str(algorithm_steps)

    # Format previous results for data context
    data_context_parts = []
    for prev in previous_results[-3:]:
        step_id = prev.get("step_id", "unknown")
        content = prev.get("content", "")[:500]
        data_context_parts.append(f"Result from {step_id}:\n{content}")
    data_context = "\n\n".join(data_context_parts) if data_context_parts else "(No previous data)"

    # Build the code generation prompt
    prompt = CODER_GENERATION_PROMPT.format(
        task_description=step.description,
        algorithm=algorithm_text,
        data_context=data_context,
        workspace_path=session_context.workspace_path,
        output_requirements=algorithm.get("output_format", "Save results to appropriate files"),
        error_context=error_context or "(First attempt - no previous errors)",
    )

    messages = [
        {"role": "system", "content": "You are the Coder Agent. Write clean, executable Python code based on the algorithm."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Coder generating code for step {step.step_id}...")

    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    # Collect and stream thinking
                    if "thinking" in delta:
                        thinking_chunk = delta["thinking"]
                        full_thinking += thinking_chunk
                        if event_callback:
                            await event_callback({
                                "type": "coder_thinking",
                                "phase": "generation",
                                "content": thinking_chunk,
                                "step_id": step.step_id,
                            })

                    # Collect content (code)
                    if "content" in delta:
                        content_chunk = delta["content"]
                        full_content += content_chunk
                        if event_callback:
                            await event_callback({
                                "type": "coder_code_chunk",
                                "content": content_chunk,
                                "step_id": step.step_id,
                            })

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
                            "source": "coder:generation"
                        })

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Code generation error: {e}")
        return {
            "success": False,
            "code": "",
            "explanation": f"Failed to generate code: {str(e)}",
            "thinking": full_thinking,
        }

    # Extract code from response
    code = _extract_code_from_response(full_content)

    result = {
        "success": bool(code),
        "code": code,
        "raw_response": full_content,
        "thinking": full_thinking,
    }

    # Emit code complete event
    if event_callback:
        await event_callback({
            "type": "coder_code_complete",
            "step_id": step.step_id,
            "code": code,
            "code_length": len(code),
        })

    logger.info(f"Code generated: {len(code)} characters")
    return result


async def analyze_error(
    step: PlanStep,
    code: str,
    error_message: str,
    attempt_number: int,
    model_router: ModelRouter,
    model_identifier: str,
    think: bool | str = False,
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """
    Analyze an execution error and suggest a fix.

    Args:
        step: The plan step
        code: The code that failed
        error_message: The error message from execution
        attempt_number: Current retry attempt number
        model_router: Router for LLM calls
        model_identifier: Model to use
        think: Thinking mode
        event_callback: Callback to emit events

    Returns:
        Dict with error analysis and suggested fix
    """
    prompt = CODER_ERROR_ANALYSIS_PROMPT.format(
        task_description=step.description,
        code=code,
        error_message=error_message,
        attempt_number=attempt_number,
        max_attempts=MAX_RETRY_ATTEMPTS,
    )

    messages = [
        {"role": "system", "content": "You are the Coder Agent analyzing an error. Be concise and focus on the fix."},
        {"role": "user", "content": prompt}
    ]

    logger.info(f"Coder analyzing error for step {step.step_id} (attempt {attempt_number})...")

    full_thinking = ""
    full_content = ""

    try:
        async for chunk in model_router.chat_stream(
            model_identifier=model_identifier,
            messages=messages,
            tools=None,
            think=think,
        ):
            try:
                data = json.loads(chunk)
                if "message" in data:
                    delta = data["message"]

                    if "thinking" in delta:
                        full_thinking += delta["thinking"]

                    if "content" in delta:
                        full_content += delta["content"]

            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Error analysis failed: {e}")
        return {
            "can_fix": False,
            "diagnosis": f"Error analysis failed: {str(e)}",
            "fix_description": "",
            "needs_human_help": True,
        }

    # Parse the analysis
    parsed = _parse_json_from_response(full_content)

    if parsed:
        analysis = {
            "can_fix": parsed.get("can_fix", False),
            "diagnosis": parsed.get("diagnosis", "Unknown error"),
            "fix_description": parsed.get("fix_description", ""),
            "needs_human_help": parsed.get("needs_human_help", False),
            "human_help_question": parsed.get("human_help_question", ""),
            "thinking": full_thinking,
        }
    else:
        analysis = {
            "can_fix": False,
            "diagnosis": full_content[:500] if full_content else "Could not analyze error",
            "fix_description": "",
            "needs_human_help": True,
            "thinking": full_thinking,
        }

    # Emit error analysis event
    if event_callback:
        await event_callback({
            "type": "coder_error_analysis",
            "step_id": step.step_id,
            "attempt_number": attempt_number,
            "can_fix": analysis["can_fix"],
            "diagnosis": analysis["diagnosis"],
            "needs_human_help": analysis["needs_human_help"],
        })

    return analysis


async def execute_coder_step(
    step: PlanStep,
    model_router: ModelRouter,
    session_context: SessionContext,
    mcp_session,  # ClientSession
    previous_results: List[Dict[str, Any]],
    plan_goal: str,
    collaboration_context=None,  # For HITL
    event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a complete Coder step with all phases.

    This is the main entry point for Coder execution. It:
    1. Designs the algorithm
    2. Generates code
    3. Executes with retry loop
    4. Escalates to human if needed

    Args:
        step: The plan step to execute
        model_router: Router for LLM calls
        session_context: Current session context
        mcp_session: MCP client session for tool calls
        previous_results: Results from previous steps
        plan_goal: The overall goal
        collaboration_context: For HITL interactions
        event_callback: Callback to emit events

    Yields:
        Events for UI updates and final _step_result
    """
    from backend.agents.orchestrator.executor import (
        get_model_for_role,
        parse_thinking_mode,
        get_base_model,
        get_agent_display_name,
    )

    # Get model configuration for coder
    agent_model = get_model_for_role("coder", session_context.agent_roles)
    agent_think = parse_thinking_mode(agent_model)
    base_model = get_base_model(agent_model)

    logger.info(f"Coder executing step {step.step_id} with model {base_model}")

    # Yield coder start event
    yield {
        "type": "coder_start",
        "step_id": step.step_id,
        "description": step.description,
        "agent_name": "Coder Agent",
        "agent_model": base_model,
        "thinking_level": agent_think if isinstance(agent_think, str) else ("enabled" if agent_think else None),
    }

    # ========================================
    # PHASE 1: ALGORITHM DESIGN
    # ========================================
    yield {
        "type": "coder_phase",
        "phase": "algorithm",
        "step_id": step.step_id,
        "status": "starting",
    }

    algorithm = await design_algorithm(
        step=step,
        previous_results=previous_results,
        plan_goal=plan_goal,
        model_router=model_router,
        model_identifier=base_model,
        session_context=session_context,
        think=agent_think,
        event_callback=event_callback,
    )

    if not algorithm.get("success"):
        yield {
            "type": "_step_result",
            "result": StepResult(
                step_id=step.step_id,
                success=False,
                content="",
                summary="Failed to design algorithm",
                agent_thinking=algorithm.get("thinking", ""),
                error=algorithm.get("reasoning", "Algorithm design failed"),
            )
        }
        return

    # ========================================
    # PHASE 2 & 3: CODE GENERATION + EXECUTION (with retry loop)
    # ========================================
    attempt = 0
    last_error = None
    final_result = None

    while attempt < MAX_RETRY_ATTEMPTS:
        attempt += 1

        yield {
            "type": "coder_phase",
            "phase": "generation",
            "step_id": step.step_id,
            "attempt": attempt,
            "status": "starting",
        }

        # Generate code
        code_result = await generate_code(
            step=step,
            algorithm=algorithm,
            previous_results=previous_results,
            model_router=model_router,
            model_identifier=base_model,
            session_context=session_context,
            think=agent_think,
            event_callback=event_callback,
            error_context=last_error,
        )

        if not code_result.get("success") or not code_result.get("code"):
            last_error = "Failed to generate code"
            continue

        code = code_result["code"]

        # ========================================
        # PHASE 3: EXECUTION
        # ========================================
        yield {
            "type": "coder_phase",
            "phase": "execution",
            "step_id": step.step_id,
            "attempt": attempt,
            "status": "starting",
        }

        yield {
            "type": "tool_call",
            "tool_call": {"name": "execute_python", "arguments": {"code": code[:500] + "..." if len(code) > 500 else code}},
            "step_id": step.step_id,
            "agent_role": "coder",
        }

        # Execute via MCP
        try:
            mcp_result = await mcp_session.call_tool(
                name="execute_python",
                arguments={"code": code},
            )

            # Extract content from MCP result
            result_content = ""
            for content in mcp_result.content:
                if hasattr(content, "text"):
                    result_content += content.text
                else:
                    result_content += "[Binary Content]"

            yield {
                "type": "tool_result",
                "tool_result": {"name": "execute_python", "content": result_content[:1000]},
                "step_id": step.step_id,
            }

            # Check for execution errors
            if _is_execution_error(result_content):
                last_error = result_content
                logger.warning(f"Coder execution error (attempt {attempt}): {result_content[:200]}")

                yield {
                    "type": "coder_retry",
                    "step_id": step.step_id,
                    "attempt": attempt,
                    "max_attempts": MAX_RETRY_ATTEMPTS,
                    "error": result_content[:500],
                }

                # Analyze error if we have more attempts
                if attempt < MAX_RETRY_ATTEMPTS:
                    error_analysis = await analyze_error(
                        step=step,
                        code=code,
                        error_message=result_content,
                        attempt_number=attempt,
                        model_router=model_router,
                        model_identifier=base_model,
                        think=agent_think,
                        event_callback=event_callback,
                    )

                    if error_analysis.get("needs_human_help"):
                        # TODO: Implement HITL for Coder
                        # For now, just log and continue trying
                        logger.info(f"Coder needs human help: {error_analysis.get('human_help_question')}")

                continue  # Retry

            # Success!
            final_result = StepResult(
                step_id=step.step_id,
                success=True,
                content=result_content,
                summary=f"Code executed successfully (attempt {attempt})",
                agent_thinking=algorithm.get("thinking", "") + "\n" + code_result.get("thinking", ""),
                error=None,
            )

            yield {
                "type": "coder_success",
                "step_id": step.step_id,
                "attempt": attempt,
            }

            break  # Exit retry loop

        except Exception as e:
            last_error = str(e)
            logger.error(f"MCP tool execution failed: {e}")

            yield {
                "type": "coder_retry",
                "step_id": step.step_id,
                "attempt": attempt,
                "max_attempts": MAX_RETRY_ATTEMPTS,
                "error": str(e),
            }

    # If we exhausted retries without success
    if final_result is None:
        # TODO: Implement HITL escalation here
        yield {
            "type": "coder_failed",
            "step_id": step.step_id,
            "attempts": attempt,
            "last_error": last_error,
        }

        final_result = StepResult(
            step_id=step.step_id,
            success=False,
            content="",
            summary=f"Coder failed after {attempt} attempts",
            agent_thinking=algorithm.get("thinking", ""),
            error=last_error,
        )

    # Yield final result
    yield {
        "type": "_step_result",
        "result": final_result,
    }


def _is_execution_error(result: str) -> bool:
    """Check if the execution result indicates an error."""
    if not result:
        return False

    result_lower = result.lower()

    error_indicators = [
        "traceback (most recent call last)",
        "error:",
        "exception:",
        "syntaxerror:",
        "nameerror:",
        "typeerror:",
        "valueerror:",
        "keyerror:",
        "indexerror:",
        "importerror:",
        "modulenotfounderror:",
        "attributeerror:",
        "filenotfounderror:",
        "zerodivisionerror:",
        "runtimeerror:",
    ]

    for indicator in error_indicators:
        if indicator in result_lower:
            return True

    return False
