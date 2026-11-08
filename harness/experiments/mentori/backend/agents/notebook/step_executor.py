"""
Step Executor for Notebook Coder V2.

Executes a single algorithm step by having the LLM generate code
and executing it in the notebook.
"""

import ast
import io
import json
import logging
import re
import tokenize
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
from backend.agents.notebook.kernel import EXEC_TIMEOUT
from backend.agents import lock_adapter
from backend.agents.models.utils import parse_model_identifier
# lock_adapter puts the repository root on sys.path, so experiments.runner imports from here on
from experiments.runner.lock import LockError
from experiments.runner.run_context import RunContextError

logger = logging.getLogger(__name__)

# A lock refusal or a missing run context is our own setup, never a failed step: it is re-raised past every
# recovery below (D69 Q38).
SETUP_ERRORS = (LockError, RunContextError)

# Counts of Mentori's coder as submitted, kept and stated (fix_design/limits.md Class M, "named parameters to keep and
# state", row 46-154): tool calls per step, and retries of a call that failed with a transient error.
MAX_TOOL_CALLS_PER_STEP = 5
MAX_TRANSIENT_RETRIES = 3

# A stated pick of a best-of-n judge (Class X, fix_design/limits.md "pick best"): the reply's first non-empty line is
# the candidate number alone, optionally as "Candidate N", in bold or followed by a full stop; an explanation may
# follow on later lines (the live run of 15 October had "2\n\nCandidate 2 is the best ..."). D75 Q58: a first line
# that names exactly one number, in range, is also the stated pick ("The best candidate is 2.", "Candidate 2 is
# best"); a line naming two numbers ("1. Candidate 2 is best") stays "unparsed", as does anything else.
_STATED_PICK = re.compile(r"^(?:candidate\s*)?#?\s*(\d+)\s*\.?$", re.IGNORECASE)
# A number standing as a word of its own ("python3" or "v2" names none); "Candidate2" is read as "Candidate 2"
_NUMBER = re.compile(r"(?<![^\W\d_])(?<!\d)\d+(?![\w])")


def parse_stated_pick(reply: str, n: int) -> Optional[int]:
    """The candidate number (1 to n) the judge's reply states on its first non-empty line, or None when that line
    states no single pick: the line is the number alone (optionally "Candidate N", bold, a full stop), or it names
    exactly one number and that number is in range (D75 Q58). The first digit anywhere in the text is not a pick (it
    took "1" from "1. Candidate 2 is best")."""
    lines = [ln for ln in (reply or "").splitlines() if ln.strip()]
    text = lines[0].strip().strip("*_`").strip() if lines else ""
    m = _STATED_PICK.match(text)
    if m:
        k = int(m.group(1))
        return k if 1 <= k <= n else None
    numbers = _NUMBER.findall(re.sub(r"(?i)(candidate)(?=\d)", r"\1 ", text))
    if len(numbers) != 1:
        return None
    k = int(numbers[0])
    return k if 1 <= k <= n else None


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
    max_tool_calls: int = MAX_TOOL_CALLS_PER_STEP,
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
    max_transient_retries = MAX_TRANSIENT_RETRIES
    # D80 V1, D81: a step on Gemini retries nothing (the submitted Gemini chat never raised, 96e2193
    # models/gemini.py:305-317, so no Gemini failure reached the recovery below)
    on_gemini = parse_model_identifier(model_identifier).provider == "gemini"
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
    # D80 V1: the transient failure the next call retries, written into that call's record (None on a first try)
    retrying = None
    # D83 Q156: the retry the turn's own call was made under (None on a first try). A best-of-3 round started by that
    # turn is redone whole, so its candidate calls and its pick call go under the same retry scope: candidate k sends
    # d * 1000 + k + 1,000,000 * r and the pick d + 1,000,000 * r (the turn's own seed, another prompt), each record
    # carrying the retry number and the seed sent
    round_retry = None

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
                clean_messages = _prompt_tools_messages(prompt_messages)

                # No options (cuts.md step_executor.py:331, D25): the lock sets every setting
                with lock_adapter.retry(retrying):
                    round_retry, retrying = retrying, None
                    response = await model_router.chat(
                        model_identifier=model_identifier,
                        messages=clean_messages,
                        # No tools= parameter!
                    )

                # Parse tool calls from response text
                content = response.get("message", {}).get("content", "")
                tool_calls = _extract_tool_calls_from_text(content)
            else:
                # Native tool calling. D80 V1: an add_cell written as text is read as the call (read_text_tool_call)
                with lock_adapter.retry(retrying), lock_adapter.text_tool_calls(read_text_tool_call):
                    round_retry, retrying = retrying, None
                    response = await model_router.chat(
                        model_identifier=model_identifier,
                        messages=messages,
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
                        # D83 Q156: a redone best-of-3 round is redone whole, under the turn's retry (see round_retry);
                        # the combined strategy keeps its calls outside it (Q156 names best-of-3 only)
                        with lock_adapter.retry(round_retry if cell_strategy == "best_of_3" else None):
                            source_code, candidates_record = await _judge_cell_candidates(
                                original_source=tool_args.get("source", ""),
                                step=step,
                                model_router=model_router,
                                model_identifier=model_identifier,
                                messages=messages,
                                strategy=cell_strategy,
                                use_prompt_tools=use_prompt_tools,
                            )
                        # The candidates, the judge's reply and its pick go to the answer's record (A5, A6)
                        yield {"type": "cell_candidates", "step_number": step.step_number, **candidates_record}
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

                # Add tool result to messages for next iteration. The tool call goes back in the provider's shape,
                # {"function": {"name", "arguments"}}, as lock_adapter returns it and Ollama's chat API reads it
                # (cuts.md M3, D25): the parsed {"name", "arguments"} sent before has no "function" key, and Ollama
                # 0.40.2 drops its arguments, so the code the model wrote never reached it again (probe, 15 October,
                # qwen3-coder:30b: 352 prompt tokens with that shape, 341 with no call, 1,067 with this one).
                # In prompt-tools mode _prompt_tools_messages writes the call as text.
                sent_call = {"function": {"name": tool_name, "arguments": tool_call.get("arguments", {})}}
                if tool_call.get("thought_signature"):
                    sent_call["thought_signature"] = tool_call["thought_signature"]
                assistant_msg = {
                    "role": "assistant",
                    "content": f"Called {tool_name}",
                    "tool_calls": [sent_call],
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

        except SETUP_ERRORS:
            raise   # our own setup (D69 Q38), never a failed step
        except Exception as e:
            # A failed model call (lock_adapter.LockCallError) keeps Mentori's recovery below; its record, with the
            # call's status, is already in the run's calls.jsonl (the rule D69 Q39 sets for a call inside a tool)
            error_str = str(e)
            is_xml_error = "XML syntax error" in error_str
            # D80 V1 (audit F34): under the lock an Ollama tool-call parse error comes inside a 200 stream and an
            # Ollama stall is status stalled, so neither text holds "(500)" or "timed out"; LockCallError.transient
            # names them, and (D81 Q138) an HTTP 500 and a dropped connection, and (D83 Q155) any other error sent
            # inside the stream (a mid-answer crash) and a stream with no final chunk. It is None for a Gemini call
            lock_transient = e.transient if isinstance(e, lock_adapter.LockCallError) else None
            is_transient = is_xml_error or lock_transient is not None or any(s in error_str for s in [
                "Ollama error (500)",
                "Server disconnected", "timed out",
            ])
            # D81 (the last D80 V1 finding): the whole decision is gated on the provider, so a Gemini failure whose
            # text holds "timed out" (gemini_client's "URLError: <urlopen error timed out>") is neither retried nor
            # switched to prompt tools: the step fails on its first call, as the submitted Gemini client made it
            if on_gemini or (isinstance(e, lock_adapter.LockCallError) and e.record.get("provider") == "gemini"):
                is_xml_error = is_transient = False
                lock_transient = None
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
                failed = getattr(e, "record", None) or {}
                retrying = {"attempt": transient_retries, "of": max_transient_retries,
                            "reason": lock_transient or ("XML syntax error" if is_xml_error else error_str[:200]),
                            "failed_seq": failed.get("seq"), "failed_ctx_uid": failed.get("ctx_uid"),
                            "failed_call_site": failed.get("call_site")}
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
) -> tuple:
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
        (the winning/combined source code, the record for the answer: strategy, the candidates whole, every
        candidate call that failed, and the judge's reply with its pick, "unparsed" when it states none)
    """
    candidates = [original_source]
    record: Dict[str, Any] = {"strategy": strategy, "candidate_errors": []}

    # Generate additional candidates by re-calling the LLM. Candidate k (2, 3) sends seed draw * 1000 + k (Q32, D68):
    # these calls repeat the first call's messages, so under one seed they would repeat its reply. The first
    # candidate is the step's own call (seed draw).
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
                clean_messages = _prompt_tools_messages(prompt_messages)

                with lock_adapter.candidate(i + 2):
                    response = await model_router.chat(
                        model_identifier=model_identifier,
                        messages=clean_messages,
                    )
                content = response.get("message", {}).get("content", "")
                alt_calls = _extract_tool_calls_from_text(content)
            else:
                # D80 V1: an add_cell written as text is read as the candidate's call, as in the step's own call
                with lock_adapter.candidate(i + 2), lock_adapter.text_tool_calls(read_text_tool_call):
                    response = await model_router.chat(
                        model_identifier=model_identifier,
                        messages=messages,
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

        except SETUP_ERRORS:
            raise   # D69 Q38
        except Exception as e:
            # Mentori goes on with the candidates it has; the failure is recorded (A5)
            logger.warning(f"Failed to generate alternative candidate {i+2}: {e}")
            record["candidate_errors"].append({"candidate": i + 2, "error": f"{type(e).__name__}: {e}"})

    record["candidates"] = list(candidates)
    record["n_candidates"] = len(candidates)

    # If we only got the original, return it
    if len(candidates) <= 1:
        logger.info(f"Cell strategy '{strategy}': only 1 candidate available, using it")
        record["pick"] = None
        return original_source, record

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
        )
        judge_text = judge_response.get("message", {}).get("content", "").strip()
        record["judge_reply"] = judge_text
        # Only a stated pick counts (Class X, limits.md "pick best"); the first digit anywhere is no longer read.
        # An unparsed reply is recorded as pick "unparsed" and the cell keeps Mentori's fallback, the first
        # candidate, recorded as picked_fallback 1 (D75 Q58: kept, the count reported per model).
        picked = parse_stated_pick(judge_text, n)
        if picked is None:
            record["pick"] = "unparsed"
            record["picked_fallback"] = 1
            logger.info("Cell judge stated no pick; running candidate 1 (recorded as unparsed)")
            return candidates[0], record
        record["pick"] = picked
        logger.info(f"Cell judge picked candidate {picked}")
        return candidates[picked - 1], record

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
        )
        combined_text = judge_response.get("message", {}).get("content", "")
        record["judge_reply"] = combined_text
        # Try to extract code block
        code_match = re.search(r'```python\s*(.*?)```', combined_text, re.DOTALL)
        if code_match:
            result = code_match.group(1).strip()
        else:
            result = combined_text.strip()
        record["pick"] = "combined"
        logger.info(f"Cell judge wrote combined cell ({len(result)} chars)")
        return result, record


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
        async for output in kernel.execute(source, timeout=EXEC_TIMEOUT):   # Q34 (D68)
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

        # Yield final result. The message states the cell's status: it said "Executed successfully" also when the
        # cell had failed (cuts.md step_executor.py:820)
        output_summary = _summarize_outputs(outputs)
        said = "Executed successfully." if status == "success" else f"Executed with status {status}."
        yield {"type": "_cell_result", "result": (f"{said} Output: {output_summary}", outputs)}

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


# D80 V1 (audit F35) and D81 (Q137): a native-tools reply with no native call is read as the call only in the shapes
# gpt-oss:20b writes it at high thinking (32 of 162 step replies in S4's copy of exp_05__coder_v2_n1, COUNTERCHECKS
# A5), and only when the reply is the call and nothing else. Three forms, one per reply:
#   json    {"name": "add_cell" | "functions.add_cell", "arguments": {...}}: one or more such objects, bare or inside
#           ```json fences, whitespace between.
#   header  gpt-oss's harmony header, the recipient in the role or the channel section ("The recipient might be
#           defined in the role or channel section of the header", developers.openai.com/cookbook/articles/
#           openai-harmony, read 16 October): "assistant to=functions.add_cell" or "commentary to=functions.add_cell",
#           an optional ":", then the arguments as one JSON object; one or more such pairs, bare, whitespace between.
#   python  a Python call, bare or as the one block of a ```python fence: every statement is a step tool's call,
#           functions.add_cell(...) or add_cell(...), standing alone or assigned to one name (cell_id = ...), and
#           no other call appears anywhere (comments are Python's and pass). add_cell's arguments are keywords, each
#           value read by ast.literal_eval (never eval), or one dict literal (functions.add_cell({...})) read the same
#           way. Another call's arguments are never evaluated; its source is recorded.
# Each call names a step tool (the "functions." prefix is the gpt-oss namespace; no other prefix); exactly one names
# add_cell, and its arguments fit STEP_TOOLS_SCHEMA (keys among its properties, source given, strings, cell_type in
# its enum). Only that add_cell is read: the other calls (execute_cell, edit_cell) name cells by placeholders such as
# "${cell_id}" or by a variable, and are recorded as not read. Anything else is not read: prose before, after or
# between the calls (a "**Step 2**" line included), a statement that is not a step tool's call (cell_id =
# result["cell_id"]), another name (assistant.functions.add_cell, run_code), a wrapper ({"functions": [...]},
# {"commentary": [...]}), two forms mixed in one reply.
_STEP_TOOLS = {t["function"]["name"]: t["function"]["parameters"] for t in STEP_TOOLS_SCHEMA}
_FENCE_JSON = re.compile(r"```json[ \t]*\n")
_HEADER = re.compile(r"(?:assistant|commentary) to=functions\.([A-Za-z_]\w*)[ \t]*:?")
_FENCE_PYTHON = re.compile(r"\s*```python[ \t]*\n(.*?)\n?[ \t]*```\s*", re.DOTALL)


def _no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate keys {sorted(k for k in set(keys) if keys.count(k) > 1)}")
    return dict(pairs)


def _skip(text: str, j: int) -> int:
    while j < len(text) and text[j].isspace():
        j += 1
    return j


def _text_call_objects(text: str) -> Optional[tuple]:
    """(the JSON objects, fenced) when the text is only JSON objects, bare or in ```json fences; else None."""
    dec = json.JSONDecoder(object_pairs_hook=_no_duplicate_keys)
    objs, fenced, n = [], False, len(text)
    i = _skip(text, 0)
    try:
        while i < n:
            m = _FENCE_JSON.match(text, i)
            if m:
                fenced, i = True, _skip(text, m.end())
                while i < n and not text.startswith("```", i):
                    obj, i = dec.raw_decode(text, i)
                    objs.append(obj)
                    i = _skip(text, i)
                if not text.startswith("```", i):
                    return None                     # a fence never closed
                i = _skip(text, i + 3)
            else:
                obj, i = dec.raw_decode(text, i)
                objs.append(obj)
                i = _skip(text, i)
    except ValueError:
        return None
    return (objs, fenced) if objs and all(isinstance(o, dict) for o in objs) else None


def _json_form(text: str) -> Optional[tuple]:
    """([(name as written, arguments)], fenced, extra) for the json form, else None."""
    found = _text_call_objects(text)
    if found is None:
        return None
    objs, fenced = found
    if any(set(o) != {"name", "arguments"} or not isinstance(o["name"], str) or not isinstance(o["arguments"], dict)
           for o in objs):
        return None
    return [(o["name"], o["arguments"]) for o in objs], fenced, {}


def _header_form(text: str) -> Optional[tuple]:
    """([(name as written, arguments)], False, extra) for gpt-oss's header form, else None."""
    dec = json.JSONDecoder(object_pairs_hook=_no_duplicate_keys)
    calls, n = [], len(text)
    i = _skip(text, 0)
    try:
        while i < n:
            m = _HEADER.match(text, i)
            if not m:
                return None
            args, i = dec.raw_decode(text, _skip(text, m.end()))
            if not isinstance(args, dict):
                return None
            calls.append(("functions." + m.group(1), args))
            i = _skip(text, i)
    except ValueError:
        return None
    return (calls, False, {}) if calls else None


def _fits_schema(args: Dict[str, Any], params: Dict[str, Any]) -> bool:
    props = params.get("properties", {})
    if set(args) - set(props) or any(r not in args for r in params.get("required", [])):
        return False
    for k, v in args.items():
        if not isinstance(v, str) or ("enum" in props[k] and v not in props[k]["enum"]):
            return False
    return True


def _literal_args(call: "ast.Call") -> Optional[Dict[str, Any]]:
    """add_cell's arguments from its keywords, or from its one dict literal, by ast.literal_eval; else None."""
    try:
        if call.keywords and not call.args:
            if any(kw.arg is None for kw in call.keywords):          # **kwargs
                return None
            return {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
        if len(call.args) == 1 and not call.keywords and isinstance(call.args[0], ast.Dict):
            keys = call.args[0].keys
            if any(not (isinstance(k, ast.Constant) and isinstance(k.value, str)) for k in keys):
                return None                                         # **unpacking or a key that is not a string
            if len({k.value for k in keys}) != len(keys):
                return None                                         # a duplicate key, as the json form refuses it
            return ast.literal_eval(call.args[0])
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None
    return None


def _keeps_result(node: "ast.AST", result_name: Optional[str]) -> bool:
    """D83 Q154: node only keeps a value from add_cell's result: the name add_cell's result was assigned to, or one
    subscript of it by a constant (result["cell_id"]); no call, no attribute, nothing else."""
    if result_name is None:
        return False
    if isinstance(node, ast.Name):
        return node.id == result_name
    return (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == result_name
            and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, (str, int))
            and not isinstance(node.slice.value, bool))


def _python_form(text: str) -> Optional[tuple]:
    """([(name as written, arguments or None)], fenced, extra) for the Python-call form, else None. Only add_cell's
    arguments are read (None when they cannot be); every other call carries its source in extra["sources"].
    D83 Q154: a statement that is not a call is accepted only when it keeps a value from add_cell's result, after
    add_cell's result was assigned to a name (result = functions.add_cell(...) then cell_id = result["cell_id"]);
    each such line goes to extra["kept"] as (its position among the statements, its source). The name holds add_cell's
    result only until a later statement assigns to it again: after r = functions.execute_cell(...) or r = r["cell_id"],
    a line keeping from r is refused, and with it the reply (review of 17 Oct, F2). A reply holding an assignment
    expression (:=, ast.NamedExpr) anywhere is refused: it can rebind add_cell's result name inside another call's
    arguments (functions.execute_cell(cell_id=(r := "0"))), unseen by the statement-level tracking above (review of
    D83 wave B, S2). No stored text-call reply holds one."""
    m = _FENCE_PYTHON.fullmatch(text)
    code = m.group(1) if m else text
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None
    if any(isinstance(n, ast.NamedExpr) for n in ast.walk(tree)):
        return None                                                 # a walrus can rebind the result's name unseen
    calls, sources, kept, order = [], [], [], []
    result_name = None                                              # the name add_cell's result was assigned to
    for pos, st in enumerate(tree.body):
        if isinstance(st, ast.Expr):
            node, target = st.value, None
        elif isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            node, target = st.value, st.targets[0].id
        else:
            return None
        if not isinstance(node, ast.Call):
            if target is not None and _keeps_result(node, result_name):
                kept.append((pos, ast.get_source_segment(code, st)))   # D83 Q154: a line that only keeps the result
                if target == result_name:
                    result_name = None                              # r = r["cell_id"]: r no longer holds the result
                continue
            return None
        f = node.func
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "functions":
            name = "functions." + f.attr
        elif isinstance(f, ast.Name):
            name = f.id
        else:
            return None                                             # assistant.functions.add_cell, obj.method
        if any(isinstance(x, ast.Call) for a in node.args + [k.value for k in node.keywords] for x in ast.walk(a)):
            return None                                             # a call inside the arguments names another
        args = _literal_args(node) if name.removeprefix("functions.") == "add_cell" else None
        if name.removeprefix("functions.") == "add_cell" and target is not None:
            result_name = target
        elif target is not None and target == result_name:
            result_name = None                                      # rebound to another call's result
        calls.append((name, args))
        sources.append(ast.get_source_segment(code, node))
        order.append(pos)
    if not calls:
        return None
    try:
        comments = sum(t.type == tokenize.COMMENT for t in tokenize.generate_tokens(io.StringIO(code).readline))
    except (tokenize.TokenError, SyntaxError):
        comments = None
    return calls, m is not None, {"sources": sources, "comments": comments, "kept": kept, "order": order}


def read_text_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """D80 V1, D81 Q137: the add_cell call a reply wrote as text, in one of the forms above, or None. Returns
    {"calls": [the call in Ollama's shape, {"function": {"name": "add_cell", "arguments"}}], "form": "json", "header"
    or "python", "names_written": every call's name as written, "fenced": bool, "not_read": the other calls ({"name",
    "arguments"} for json and header, {"name", "source"} for python, where D83 Q154's lines that only keep add_cell's
    result are {"name": None, "source"}, all in the reply's order)}, and for python "comments": the comment count;
    lock_adapter records it as tool_calls_from_text."""
    text = text or ""
    for form, parse in (("json", _json_form), ("header", _header_form), ("python", _python_form)):
        found = parse(text)
        if found is not None:
            break
    else:
        return None
    calls, fenced, extra = found
    if any(name.removeprefix("functions.") not in _STEP_TOOLS for name, _ in calls):
        return None
    adds = [i for i, (name, _) in enumerate(calls) if name.removeprefix("functions.") == "add_cell"]
    if len(adds) != 1:
        return None
    args = calls[adds[0]][1]
    if not isinstance(args, dict) or not _fits_schema(args, _STEP_TOOLS["add_cell"]):
        return None
    if form == "python":
        # the other calls, and (D83 Q154) the lines that only keep add_cell's result, name None, in the reply's order
        others = [(extra["order"][i], {"name": name, "source": extra["sources"][i]})
                  for i, (name, _) in enumerate(calls) if i != adds[0]]
        others += [(pos, {"name": None, "source": src}) for pos, src in extra["kept"]]
        not_read = [entry for _, entry in sorted(others, key=lambda x: x[0])]
    else:
        not_read = [{"name": name, "arguments": a} for i, (name, a) in enumerate(calls) if i != adds[0]]
    out = {"calls": [{"function": {"name": "add_cell", "arguments": dict(args)}}], "form": form,
           "names_written": [name for name, _ in calls], "fenced": fenced, "not_read": not_read}
    if form == "python":
        out["comments"] = extra["comments"]
    return out


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
    """The cell's outputs as the coder sees them after execute_cell: every output whole (cuts.md
    step_executor.py:1020, D25; it kept the first 3 outputs, 50 characters of stdout and an error's name only).
    Outputs are CellOutput objects or their dicts (a saved notebook): both are read through the dict form.
    stdout and stderr streams, the text/plain of a result or display (an image or another type is named), and an
    error's name, value and ANSI-stripped traceback."""
    parts = []
    for o in outputs:
        o = o.to_dict() if hasattr(o, "to_dict") else o if isinstance(o, dict) else {}
        t = o.get("output_type")
        if t == "stream":
            parts.append(o.get("text") or "")
        elif t in ("execute_result", "display_data"):
            d = o.get("data") or {}
            parts.append(d.get("text/plain") or ("[image output]" if any(k.startswith("image/") for k in d)
                                                 else "[non-text output]"))
        elif t == "error":
            tb = "\n".join(re.sub(r"\x1b\[[0-9;]*m", "", str(x)) for x in (o.get("traceback") or []))
            parts.append(f"{o.get('ename')}: {o.get('evalue')}\n{tb}")
    return "\n".join(parts) or "No output"


def _prompt_tools_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The messages for prompt-based tool calling: a tool result becomes a user turn, and an assistant turn with
    tool calls carries each call as the JSON block PROMPT_TOOLS_SECTION asks for, whole (cuts.md M3, D25). It kept
    only "Called <tool>", so the model lost the code it had written."""
    clean = []
    for m in messages:
        if m.get("role") == "tool":
            clean.append({
                "role": "user",
                "content": f"Tool result from {m.get('name', 'unknown')}: {m.get('content', '')}",
            })
        elif m.get("role") == "assistant" and "tool_calls" in m:
            blocks = []
            for tc in m.get("tool_calls") or []:
                f = tc.get("function", tc)
                call = {"tool_call": {"name": f.get("name", ""), "arguments": _parse_arguments(f.get("arguments", {}))}}
                blocks.append("```json\n" + json.dumps(call, ensure_ascii=False) + "\n```")
            clean.append({"role": "assistant", "content": "\n".join(blocks) or m.get("content", "")})
        else:
            clean.append(m)
    return clean


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
