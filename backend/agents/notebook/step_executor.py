"""
Step Executor for Notebook Coder V2.

Executes a single algorithm step by having the LLM generate code
and executing it in the notebook.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, AsyncGenerator, Callable, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from backend.agents.model_router import ModelRouter
    from backend.agents.notebook.schema import (
        AlgorithmStep,
        Cell,
        NotebookState,
        KernelState,
    )
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.kernel import NotebookKernel

from backend.agents.notebook.prompts_v2 import (
    STEP_EXECUTION_PROMPT,
    STEP_EXECUTION_RETRY_SECTION,
    build_kernel_state_summary,
    build_validation_criteria_string,
    build_algorithm_context,
    build_previous_steps_with_code,
)
from backend.agents.notebook.api_introspector import introspect_step, format_recovery_hint

logger = logging.getLogger(__name__)


# Text-based tool descriptions for models that don't support native tool calling
PROMPT_TOOLS_SECTION = """

## Available Tools
You can call tools by responding with a JSON block in this exact format:
```json
{"tool_call": {"name": "TOOL_NAME", "arguments": {"arg1": "value1"}}}
```

Available tools:
1. **add_cell** - Add a new cell to the notebook
   Arguments: {"source": "code or markdown content", "cell_type": "code" or "markdown"}
   Required: source

2. **execute_cell** - Execute a cell and get its output
   Arguments: {"cell_id": "ID of the cell to execute"}
   Required: cell_id

3. **edit_cell** - Edit the source of an existing cell
   Arguments: {"cell_id": "ID of the cell", "source": "new source code"}
   Required: cell_id, source

You MUST call add_cell first to create cells, then execute_cell to run them.
Respond with exactly one tool_call JSON block per response. Do NOT include any other text before the JSON block.
"""

# Judge prompts for cell-level multi-candidate strategies
CELL_JUDGE_PICK = """You are a code quality judge. You are given {n} candidate code cells
for a notebook step. Pick the BEST one.

## Step Description
{step_description}

## Expected Output
{expected_output}

{candidates_section}

Evaluate correctness, syntax, and alignment with the step description.
Respond with ONLY the number of the best candidate (1, 2, or 3). Nothing else."""

CELL_JUDGE_COMBINE = """You are a code synthesis judge. You are given {n} candidate code cells
for a notebook step. Write a FINAL version combining the best ideas.

## Step Description
{step_description}

## Expected Output
{expected_output}

{candidates_section}

Write the final synthesized code. Output ONLY the code, no explanation, no markdown fences."""


# Limited tool schema for step execution - only notebook operations
STEP_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_cell",
            "description": "Add a new cell to the notebook",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "The code or markdown content for the cell"
                    },
                    "cell_type": {
                        "type": "string",
                        "enum": ["code", "markdown"],
                        "description": "Type of cell to create"
                    }
                },
                "required": ["source"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_cell",
            "description": "Execute a cell and get its output",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "ID of the cell to execute"
                    }
                },
                "required": ["cell_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_cell",
            "description": "Edit the source of an existing cell",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell_id": {
                        "type": "string",
                        "description": "ID of the cell to edit"
                    },
                    "source": {
                        "type": "string",
                        "description": "New source code for the cell"
                    }
                },
                "required": ["cell_id", "source"]
            }
        }
    },
]


@dataclass
class StepExecutionResult:
    """Result of executing a single algorithm step."""
    success: bool
    cells_created: List["Cell"]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    variables_created: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    tool_calls_made: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "cells_created": [c.id if hasattr(c, 'id') else c.get('id', '') for c in self.cells_created],
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "variables_created": self.variables_created,
            "files_created": self.files_created,
            "tool_calls_made": self.tool_calls_made,
        }


async def execute_step(
    step: "AlgorithmStep",
    notebook: Any,  # Notebook object passed directly
    notebook_manager: "NotebookManager",
    kernel: "NotebookKernel",
    model_router: "ModelRouter",
    model_identifier: str,
    previous_results: List[StepExecutionResult],
    algorithm: Optional[Dict[str, Any]] = None,
    retry_feedback: Optional[str] = None,
    event_callback: Optional[Callable] = None,
    max_tool_calls: int = 5,
    environment_context: Optional[str] = None,
    cell_strategy: str = "single",
    introspect: bool = True,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a single algorithm step.

    This is an async generator that yields events during execution
    and finally yields a special event with the result.

    Args:
        step: The algorithm step to execute
        notebook_manager: Manager for notebook operations
        kernel: Jupyter kernel for execution
        model_router: Router for LLM calls
        model_identifier: Model to use
        previous_results: Results from previous steps
        algorithm: The full algorithm dict for context
        retry_feedback: Feedback from failed previous attempt
        event_callback: Callback for emitting events
        max_tool_calls: Maximum tool calls before stopping

    Yields:
        Events: cell_added, cell_event, tool_call, etc.
        Final: {"type": "_step_result", "result": StepExecutionResult}
    """
    import time
    start_time = time.time()

    cells_created: List["Cell"] = []
    tool_calls_made = 0
    transient_retries = 0
    max_transient_retries = 3
    last_cell_id = None

    # Get current kernel state
    kernel_state = await kernel.get_kernel_variables()
    kernel_state_summary = build_kernel_state_summary(kernel_state.to_dict() if kernel_state else {})

    # Build prompt with full algorithm context
    validation_criteria = step.validation_criteria or []
    if isinstance(validation_criteria, str):
        validation_criteria = [validation_criteria]

    # ── API Introspection (V2-8: introspect_with_recovery, 77% pass rate) ────
    # Ask the model to declare its intended API calls before generating code.
    # Run on every attempt (including retries) so the scratchpad always reflects
    # the model's current plan, which is then cross-referenced with any error.
    api_scratchpad = ""
    if introspect:
        api_scratchpad = await introspect_step(
            model_router=model_router,
            model_identifier=model_identifier,
            step_description=step.description,
            expected_output=step.expected_output or "Complete the step",
            kernel_state_summary=kernel_state_summary,
        )

    api_scratchpad_section = ""
    if api_scratchpad:
        api_scratchpad_section = (
            "## API PLAN (pre-committed before writing code)\n"
            f"{api_scratchpad}\n\n"
        )

    retry_section = ""
    if retry_feedback:
        recovery_hint = format_recovery_hint(api_scratchpad, retry_feedback)
        retry_section = STEP_EXECUTION_RETRY_SECTION.format(
            attempt=len([r for r in previous_results if not r.success]) + 1,
            feedback=retry_feedback,
            recovery_hint=recovery_hint,
        )

    # Build algorithm context so agent knows the full picture
    algorithm_dict = algorithm.to_dict() if hasattr(algorithm, 'to_dict') else (algorithm or {})
    total_steps = len(algorithm_dict.get('steps', [])) if algorithm_dict else step.step_number

    prompt = STEP_EXECUTION_PROMPT.format(
        step_number=step.step_number,
        total_steps=total_steps,
        description=step.description,
        expected_output=step.expected_output or "Complete the step",
        validation_criteria=build_validation_criteria_string(validation_criteria),
        kernel_state=kernel_state_summary,
        previous_steps_summary=build_previous_steps_with_code(previous_results),
        algorithm_context=build_algorithm_context(algorithm_dict, step.step_number),
        api_scratchpad_section=api_scratchpad_section,
        retry_section=retry_section,
        environment_context=environment_context or "No workspace files listed.",
    )

    messages = [{"role": "user", "content": prompt}]

    # Emit step start
    if event_callback:
        await event_callback({
            "type": "step_execution_start",
            "step_number": step.step_number,
            "description": step.description,
        })

    # Track whether to use prompt-based tool calling (fallback for models
    # that don't support Ollama's native XML tool format, e.g. qwen3-coder)
    use_prompt_tools = False

    # ReAct loop for this step (limited iterations)
    while tool_calls_made < max_tool_calls:
        try:
            if use_prompt_tools:
                # Prompt-based tool calling: embed tool descriptions in prompt
                prompt_messages = list(messages)
                if prompt_messages and prompt_messages[0]["role"] == "user":
                    prompt_messages[0] = {
                        "role": "user",
                        "content": prompt_messages[0]["content"] + PROMPT_TOOLS_SECTION,
                    }
                # Strip any 'tool_calls' from assistant messages and 'tool' role messages
                clean_messages = []
                for m in prompt_messages:
                    if m.get("role") == "tool":
                        clean_messages.append({
                            "role": "user",
                            "content": f"Tool result from {m.get('name', 'unknown')}: {m.get('content', '')}",
                        })
                    elif m.get("role") == "assistant" and "tool_calls" in m:
                        clean_messages.append({
                            "role": "assistant",
                            "content": m.get("content", ""),
                        })
                    else:
                        clean_messages.append(m)

                response = await model_router.chat(
                    model_identifier=model_identifier,
                    messages=clean_messages,
                    options={
                        "temperature": 0.2,
                        "num_predict": 3000,
                    },
                    # No tools= parameter!
                )

                # Parse tool calls from response text
                content = response.get("message", {}).get("content", "")
                tool_calls = _extract_tool_calls_from_text(content)
            else:
                # Native tool calling
                response = await model_router.chat(
                    model_identifier=model_identifier,
                    messages=messages,
                    options={
                        "temperature": 0.2,
                        "num_predict": 3000,
                    },
                    tools=STEP_TOOLS_SCHEMA,
                )

                tool_calls = _extract_tool_calls(response)

            if not tool_calls:
                # No more tool calls - step is done
                break

            # Execute each tool call
            for tool_call in tool_calls:
                tool_calls_made += 1
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("arguments", {})

                # Emit tool call event (use 'arguments' to match frontend expectations)
                yield {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "step_number": step.step_number,
                }

                # Execute tool
                result = None
                if tool_name == "add_cell":
                    # Multi-candidate logic: if cell_strategy is not single,
                    # intercept the first code cell to generate alternatives
                    if cell_strategy != "single" and tool_args.get("cell_type", "code") == "code" and not cells_created:
                        source_code = await _judge_cell_candidates(
                            original_source=tool_args.get("source", ""),
                            step=step,
                            model_router=model_router,
                            model_identifier=model_identifier,
                            messages=messages,
                            strategy=cell_strategy,
                            use_prompt_tools=use_prompt_tools,
                        )
                        tool_args = dict(tool_args)
                        tool_args["source"] = source_code

                    result, cell = await _execute_add_cell(
                        notebook, notebook_manager, tool_args, event_callback
                    )
                    if cell:
                        cell_id_short = (cell.id if hasattr(cell, 'id') else cell.get('id', ''))[:8]
                        logger.info(f"add_cell: Created cell {cell_id_short}, appending to cells_created (current len={len(cells_created)})")
                        cells_created.append(cell)
                        last_cell_id = cell.id if hasattr(cell, 'id') else cell.get('id')

                elif tool_name == "execute_cell":
                    cell_id = tool_args.get("cell_id", last_cell_id)
                    # Use generator to stream cell events in real-time
                    outputs = []
                    async for cell_event in _execute_cell_generator(
                        kernel, notebook, notebook_manager, cell_id
                    ):
                        if cell_event.get("type") == "_cell_result":
                            # Final result from cell execution
                            result, outputs = cell_event["result"]
                        else:
                            # Yield cell_event immediately for real-time streaming
                            yield cell_event
                    # Check for files created in output
                    if outputs:
                        files = _detect_files_in_output(outputs)
                        # We'll collect these later

                elif tool_name == "edit_cell":
                    result = await _execute_edit_cell(
                        notebook, notebook_manager, tool_args, event_callback
                    )

                else:
                    result = f"Unknown tool: {tool_name}"

                # Yield tool result event
                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "result": str(result)[:500],
                    "step_number": step.step_number,
                }

                # Add tool result to messages for next iteration
                assistant_msg = {
                    "role": "assistant",
                    "content": f"Called {tool_name}",
                    "tool_calls": [tool_call],
                }
                # Preserve _gemini_parts for Gemini thought_signature support
                gemini_parts = response.get("message", {}).get("_gemini_parts")
                if gemini_parts:
                    assistant_msg["_gemini_parts"] = gemini_parts
                messages.append(assistant_msg)
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": str(result),
                })

        except Exception as e:
            error_str = str(e)
            is_xml_error = "XML syntax error" in error_str
            is_transient = is_xml_error or any(s in error_str for s in [
                "Ollama error (500)",
                "Server disconnected", "timed out",
            ])
            if is_xml_error and not use_prompt_tools:
                # Switch to prompt-based tool calling on XML errors
                logger.warning(
                    f"XML tool calling not supported by model, switching to prompt-based tools: {e}"
                )
                use_prompt_tools = True
                transient_retries = 0  # Reset retries for the new approach
                continue
            if is_transient and transient_retries < max_transient_retries:
                transient_retries += 1
                logger.warning(f"Transient LLM error (retry {transient_retries}/{max_transient_retries}): {e}")
                import asyncio
                await asyncio.sleep(1 * transient_retries)  # backoff
                continue
            logger.error(f"Error in step execution: {e}")
            yield {
                "type": "_step_result",
                "result": StepExecutionResult(
                    success=False,
                    cells_created=cells_created,
                    error_message=str(e),
                    execution_time=time.time() - start_time,
                    tool_calls_made=tool_calls_made,
                ),
            }
            return

    # Determine success based on cell execution
    success = False
    error_message = None

    if cells_created:
        # Check last cell status
        last_cell = cells_created[-1]
        status = getattr(last_cell, 'status', None) or last_cell.get('status', 'idle')
        success = status == 'success'
        if status == 'error':
            error_message = _extract_error_from_cell(last_cell)

    # Get variables created (compare kernel state before/after)
    new_kernel_state = await kernel.get_kernel_variables()
    variables_created = _get_new_variables(kernel_state, new_kernel_state)

    # Detect files created
    files_created = []
    for cell in cells_created:
        if hasattr(cell, 'outputs'):
            outputs = cell.outputs or []
        elif isinstance(cell, dict):
            outputs = cell.get('outputs', [])
        else:
            outputs = []
        files_created.extend(_detect_files_in_output(outputs))

    # Save notebook
    notebook_manager.save_notebook(notebook)

    # Yield final result
    yield {
        "type": "_step_result",
        "result": StepExecutionResult(
            success=success,
            cells_created=cells_created,
            error_message=error_message,
            execution_time=time.time() - start_time,
            variables_created=variables_created,
            files_created=files_created,
            tool_calls_made=tool_calls_made,
        ),
    }


async def _judge_cell_candidates(
    original_source: str,
    step: "AlgorithmStep",
    model_router: "ModelRouter",
    model_identifier: str,
    messages: List[Dict[str, str]],
    strategy: str = "best_of_3",
    use_prompt_tools: bool = False,
    n_extra: int = 2,
) -> str:
    """Generate additional cell candidates and judge them.

    Args:
        original_source: The first candidate's source code (from initial LLM call)
        step: Current algorithm step for context
        model_router: Router for LLM calls
        model_identifier: Model to use
        messages: Current conversation messages (for context)
        strategy: 'best_of_3' or 'combined'
        use_prompt_tools: Whether to use prompt-based tools (no native tools)
        n_extra: Number of additional candidates to generate

    Returns:
        The winning/combined source code
    """
    candidates = [original_source]

    # Generate additional candidates by re-calling the LLM with higher temperature
    for i in range(n_extra):
        try:
            if use_prompt_tools:
                # Use prompt-based calling for additional candidates
                prompt_messages = list(messages)
                if prompt_messages and prompt_messages[0]["role"] == "user":
                    prompt_messages[0] = {
                        "role": "user",
                        "content": prompt_messages[0]["content"] + PROMPT_TOOLS_SECTION,
                    }
                # Strip tool-related message roles
                clean_messages = []
                for m in prompt_messages:
                    if m.get("role") == "tool":
                        clean_messages.append({
                            "role": "user",
                            "content": f"Tool result from {m.get('name', 'unknown')}: {m.get('content', '')}",
                        })
                    elif m.get("role") == "assistant" and "tool_calls" in m:
                        clean_messages.append({
                            "role": "assistant",
                            "content": m.get("content", ""),
                        })
                    else:
                        clean_messages.append(m)

                response = await model_router.chat(
                    model_identifier=model_identifier,
                    messages=clean_messages,
                    options={"temperature": 0.7, "num_predict": 3000},
                )
                content = response.get("message", {}).get("content", "")
                alt_calls = _extract_tool_calls_from_text(content)
            else:
                response = await model_router.chat(
                    model_identifier=model_identifier,
                    messages=messages,
                    options={"temperature": 0.7, "num_predict": 3000},
                    tools=STEP_TOOLS_SCHEMA,
                )
                alt_calls = _extract_tool_calls(response)

            # Find the add_cell call in the response
            for tc in alt_calls:
                if tc.get("name") == "add_cell":
                    alt_source = tc.get("arguments", {}).get("source", "")
                    if alt_source:
                        candidates.append(alt_source)
                    break
            else:
                # No add_cell found, try extracting code from content
                content = response.get("message", {}).get("content", "")
                if content:
                    import re as _re
                    code_match = _re.search(r'```python\s*(.*?)```', content, _re.DOTALL)
                    if code_match:
                        candidates.append(code_match.group(1).strip())

        except Exception as e:
            logger.warning(f"Failed to generate alternative candidate {i+2}: {e}")

    # If we only got the original, return it
    if len(candidates) <= 1:
        logger.info(f"Cell strategy '{strategy}': only 1 candidate available, using it")
        return original_source

    n = len(candidates)
    logger.info(f"Cell strategy '{strategy}': {n} candidates generated, judging...")

    # Build candidates section for judge
    candidates_section = ""
    for i, c in enumerate(candidates, 1):
        candidates_section += f"## Candidate {i}\n```python\n{c}\n```\n\n"

    step_desc = step.description if hasattr(step, 'description') else str(step)
    expected = step.expected_output if hasattr(step, 'expected_output') else ""

    if strategy == "best_of_3":
        judge_prompt = CELL_JUDGE_PICK.format(
            n=n,
            step_description=step_desc,
            expected_output=expected or "Complete the step",
            candidates_section=candidates_section,
        )
        judge_response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": judge_prompt}],
            options={"temperature": 0.0, "num_predict": 100},
        )
        judge_text = judge_response.get("message", {}).get("content", "").strip()
        pick_match = re.search(r'[123]', judge_text)
        picked = int(pick_match.group()) if pick_match else 1
        picked = max(1, min(picked, n))
        logger.info(f"Cell judge picked candidate {picked}")
        return candidates[picked - 1]

    else:  # combined
        judge_prompt = CELL_JUDGE_COMBINE.format(
            n=n,
            step_description=step_desc,
            expected_output=expected or "Complete the step",
            candidates_section=candidates_section,
        )
        judge_response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": judge_prompt}],
            options={"temperature": 0.1, "num_predict": 3000},
        )
        combined_text = judge_response.get("message", {}).get("content", "")
        # Try to extract code block
        code_match = re.search(r'```python\s*(.*?)```', combined_text, re.DOTALL)
        if code_match:
            result = code_match.group(1).strip()
        else:
            result = combined_text.strip()
        logger.info(f"Cell judge wrote combined cell ({len(result)} chars)")
        return result


async def _execute_add_cell(
    notebook: Any,
    notebook_manager: "NotebookManager",
    args: Dict[str, Any],
    event_callback: Optional[Callable],
) -> tuple:
    """Execute add_cell tool."""
    source = args.get("source", "")
    cell_type = args.get("cell_type", "code")

    cell = notebook.add_cell(source, cell_type)
    notebook_manager.save_notebook(notebook)

    cell_id = cell.id if hasattr(cell, 'id') else cell.get('id', '')
    cell_index = len(notebook.cells) - 1  # Cell was just added at end

    # Emit cell added event
    if event_callback:
        await event_callback({
            "type": "cell_added",
            "cell_id": cell_id,
            "cell_type": cell_type,
            "index": cell_index,
            "source": source,
        })

    return f"Cell {cell_id[:8]} added successfully", cell


async def _execute_cell_generator(
    kernel: "NotebookKernel",
    notebook: Any,
    notebook_manager: "NotebookManager",
    cell_id: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a cell and yield events as execution progresses.

    This is an async generator that yields cell_event dicts for real-time streaming.
    The final yield is a special "_cell_result" event with the result tuple.

    Yields:
        {"type": "cell_event", "event": {...}} for each execution event
        {"type": "_cell_result", "result": (message, outputs)} as final event
    """
    # Find cell
    cell = None
    full_cell_id = cell_id  # Will be updated to full ID if found
    for c in notebook.cells:
        cid = c.id if hasattr(c, 'id') else c.get('id', '')
        if cid == cell_id or cid.startswith(cell_id):
            cell = c
            full_cell_id = cid  # Use the FULL cell ID for events
            break

    if not cell:
        yield {"type": "_cell_result", "result": (f"Cell {cell_id} not found", [])}
        return

    # Get cell source
    source = cell.source if hasattr(cell, 'source') else cell.get('source', '')

    # Emit execution start - use FULL cell ID so frontend can match
    yield {
        "type": "cell_event",
        "event": {
            "type": "execution_start",
            "cell_id": full_cell_id,
        }
    }

    # Execute
    try:
        outputs = []
        async for output in kernel.execute(source):
            outputs.append(output)
            # Emit output event immediately for real-time streaming
            yield {
                "type": "cell_event",
                "event": {
                    "type": "output",
                    "cell_id": full_cell_id,
                    "output": output.to_dict() if hasattr(output, 'to_dict') else output,
                }
            }

        # Update cell with outputs
        logger.info(f"_execute_cell: Cell {cell_id[:8]} executed, captured {len(outputs)} outputs")
        for i, out in enumerate(outputs[:3]):
            out_type = out.output_type if hasattr(out, 'output_type') else (out.get('output_type', '?') if isinstance(out, dict) else '?')
            logger.info(f"  output[{i}]: type={out_type}")

        if hasattr(cell, 'outputs'):
            cell.outputs = outputs
            cell.status = 'success'
            logger.info(f"_execute_cell: Set cell.outputs (len={len(cell.outputs)}) on Cell object")
        else:
            cell['outputs'] = [o.to_dict() if hasattr(o, 'to_dict') else o for o in outputs]
            cell['status'] = 'success'
            logger.info(f"_execute_cell: Set cell['outputs'] (len={len(cell['outputs'])}) on dict")

        # Check for errors in outputs
        _ERROR_PATTERNS = ['Traceback (most recent call last)', 'NameError:', 'TypeError:',
                           'ValueError:', 'KeyError:', 'FileNotFoundError:', 'ImportError:',
                           'AttributeError:', 'IndexError:', 'ModuleNotFoundError:']
        for output in outputs:
            output_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type', '')
            if output_type == 'error':
                if hasattr(cell, 'status'):
                    cell.status = 'error'
                else:
                    cell['status'] = 'error'
                break
            # Also detect errors in stream output
            if output_type == 'stream':
                text = (output.text if hasattr(output, 'text') else output.get('text', '')) or ''
                if any(pat in text for pat in _ERROR_PATTERNS):
                    if hasattr(cell, 'status'):
                        cell.status = 'error'
                    else:
                        cell['status'] = 'error'
                    logger.warning(f"Detected error pattern in stream output for cell {cell_id[:8]}")
                    break

        notebook_manager.save_notebook(notebook)

        # Emit completion
        status = cell.status if hasattr(cell, 'status') else cell.get('status', 'success')
        yield {
            "type": "cell_event",
            "event": {
                "type": "execution_complete",
                "cell_id": full_cell_id,
                "status": status,
                "output_summary": _summarize_outputs(outputs),
                "has_images": any(
                    (hasattr(o, 'data') and any(k.startswith('image/') for k in (o.data or {}).keys()))
                    or (isinstance(o, dict) and any(k.startswith('image/') for k in o.get('data', {}).keys()))
                    for o in outputs
                ),
            }
        }

        # Yield final result
        output_summary = _summarize_outputs(outputs)
        yield {"type": "_cell_result", "result": (f"Executed successfully. Output: {output_summary}", outputs)}

    except Exception as e:
        if hasattr(cell, 'status'):
            cell.status = 'error'
        else:
            cell['status'] = 'error'

        yield {
            "type": "cell_event",
            "event": {
                "type": "execution_complete",
                "cell_id": full_cell_id,
                "status": "error",
                "error": str(e),
            }
        }

        yield {"type": "_cell_result", "result": (f"Execution failed: {e}", [])}


async def _execute_edit_cell(
    notebook: Any,
    notebook_manager: "NotebookManager",
    args: Dict[str, Any],
    event_callback: Optional[Callable],
) -> str:
    """Execute edit_cell tool."""
    cell_id = args.get("cell_id", "")
    source = args.get("source", "")

    # Find and update cell
    for cell in notebook.cells:
        cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
        if cid == cell_id or cid.startswith(cell_id):
            if hasattr(cell, 'source'):
                cell.source = source
                cell.outputs = []
                cell.status = 'idle'
            else:
                cell['source'] = source
                cell['outputs'] = []
                cell['status'] = 'idle'

            notebook_manager.save_notebook(notebook)

            if event_callback:
                await event_callback({
                    "type": "cell_edited",
                    "cell_id": cid,
                    "source": source,
                })

            return f"Cell {cid[:8]} edited successfully"

    return f"Cell {cell_id} not found"


def _extract_tool_calls(response: Any) -> List[Dict[str, Any]]:
    """Extract tool calls from LLM response."""
    tool_calls = []

    if isinstance(response, dict):
        # Check for tool_calls in message
        message = response.get("message", {})
        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    tc_dict = {
                        "name": func.get("name", ""),
                        "arguments": _parse_arguments(func.get("arguments", {})),
                    }
                    # Preserve thought_signature for Gemini 3 models
                    ts = tc.get("thought_signature") or func.get("thought_signature")
                    if ts:
                        tc_dict["thought_signature"] = ts
                    tool_calls.append(tc_dict)

        # Check for direct tool_calls
        if "tool_calls" in response:
            for tc in response["tool_calls"]:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    tc_dict = {
                        "name": func.get("name", ""),
                        "arguments": _parse_arguments(func.get("arguments", {})),
                    }
                    # Preserve thought_signature for Gemini 3 models
                    ts = tc.get("thought_signature") or func.get("thought_signature")
                    if ts:
                        tc_dict["thought_signature"] = ts
                    tool_calls.append(tc_dict)

    return tool_calls


def _parse_arguments(args: Any) -> Dict[str, Any]:
    """Parse tool arguments from various formats."""
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {}
    return {}


def _extract_tool_calls_from_text(content: str) -> List[Dict[str, Any]]:
    """Extract tool calls from LLM response text (prompt-based tool calling).

    Parses JSON blocks like: {"tool_call": {"name": "add_cell", "arguments": {...}}}
    Also handles raw function-call patterns from qwen3-coder.
    """
    tool_calls = []
    if not content:
        return tool_calls

    # Strategy 1: Look for ```json ... ``` blocks containing tool_call
    json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            tc = parsed.get("tool_call", parsed)
            name = tc.get("name", "")
            arguments = tc.get("arguments", {})
            if name and name in ("add_cell", "execute_cell", "edit_cell"):
                tool_calls.append({
                    "name": name,
                    "arguments": _parse_arguments(arguments),
                })
        except (json.JSONDecodeError, AttributeError):
            continue

    if tool_calls:
        return tool_calls

    # Strategy 2: Look for inline {"tool_call": ...} patterns
    tc_matches = re.findall(
        r'\{[^{}]*"tool_call"\s*:\s*\{[^{}]*"name"\s*:\s*"(\w+)"[^{}]*"arguments"\s*:\s*(\{[^{}]*\})[^{}]*\}[^{}]*\}',
        content
    )
    for name, args_str in tc_matches:
        if name in ("add_cell", "execute_cell", "edit_cell"):
            tool_calls.append({
                "name": name,
                "arguments": _parse_arguments(args_str),
            })

    if tool_calls:
        return tool_calls

    # Strategy 3: Look for any JSON object with "name" and "arguments"/"source"
    json_objects = re.findall(r'\{[^{}]*"name"\s*:\s*"(add_cell|execute_cell|edit_cell)"[^{}]*\}', content)
    for match_str in json_objects:
        # Try to extract the full JSON object
        idx = content.find(f'"name": "{match_str}"')
        if idx < 0:
            idx = content.find(f'"name":"{match_str}"')
        if idx >= 0:
            # Find enclosing braces
            start = content.rfind('{', 0, idx)
            if start >= 0:
                depth = 0
                for i in range(start, len(content)):
                    if content[i] == '{':
                        depth += 1
                    elif content[i] == '}':
                        depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(content[start:i+1])
                            tool_calls.append({
                                "name": obj.get("name", match_str),
                                "arguments": _parse_arguments(obj.get("arguments", {})),
                            })
                        except json.JSONDecodeError:
                            pass
                        break

    return tool_calls




def _summarize_outputs(outputs: List[Any]) -> str:
    """Create brief summary of cell outputs."""
    summaries = []

    for output in outputs[:3]:  # Limit to first 3
        if hasattr(output, 'output_type'):
            output_type = output.output_type
        elif isinstance(output, dict):
            output_type = output.get('output_type', 'unknown')
        else:
            continue

        if output_type == 'stream':
            text = (output.text if hasattr(output, 'text') else output.get('text', '')) or ''
            summaries.append(f"[stdout: {text[:50]}...]")
        elif output_type == 'execute_result':
            summaries.append("[result displayed]")
        elif output_type == 'display_data':
            summaries.append("[visualization]")
        elif output_type == 'error':
            ename = output.ename if hasattr(output, 'ename') else output.get('ename', 'Error')
            summaries.append(f"[error: {ename}]")

    return " ".join(summaries) if summaries else "No output"


def _extract_error_from_cell(cell: Any) -> Optional[str]:
    """Extract error message from cell outputs."""
    outputs = getattr(cell, 'outputs', None) or cell.get('outputs', [])

    for output in outputs:
        output_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type', '')
        if output_type == 'error':
            ename = output.ename if hasattr(output, 'ename') else output.get('ename', 'Error')
            evalue = output.evalue if hasattr(output, 'evalue') else output.get('evalue', '')
            return f"{ename}: {evalue}"

    return None


def _get_new_variables(
    old_state: Optional[Any],
    new_state: Optional[Any],
) -> List[str]:
    """Get variables created between kernel states."""
    if not old_state or not new_state:
        return []

    old_vars = set()
    new_vars = set()

    # KernelState.variables is Dict[str, VariableInfo], keys are variable names
    if hasattr(old_state, 'variables') and isinstance(old_state.variables, dict):
        old_vars = set(old_state.variables.keys())
    if hasattr(new_state, 'variables') and isinstance(new_state.variables, dict):
        new_vars = set(new_state.variables.keys())

    return list(new_vars - old_vars)


def _detect_files_in_output(outputs: List[Any]) -> List[str]:
    """Detect file paths mentioned in outputs."""
    files = []
    file_pattern = r'(?:saved|wrote|created|output)[:\s]+[\'"`]?([^\s\'"`\n]+\.\w+)'

    for output in outputs:
        text = ""
        if hasattr(output, 'text'):
            text = output.text or ""
        elif isinstance(output, dict):
            text = output.get('text', '')
            data = output.get('data', {})
            if 'text/plain' in data:
                text += data['text/plain']

        matches = re.findall(file_pattern, text, re.IGNORECASE)
        files.extend(matches)

    return files
