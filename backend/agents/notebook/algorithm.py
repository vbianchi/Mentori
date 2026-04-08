# backend/agents/notebook/algorithm.py
"""
Algorithm Agent for pre-coding planning.

The AlgorithmAgent converts a user request into a structured algorithm
before the coder agent starts writing code. This ensures:
1. Complex tasks are broken into manageable steps
2. Expected outputs and validation criteria are defined
3. The coder agent has a clear plan to follow

By default generates a single algorithm (N_CANDIDATES=1). When N_CANDIDATES>1
(set via monkeypatch in coder_v2 benchmark), generates multiple candidates
and uses a judge LLM call to select and merge the best steps.
"""

import json
import re
from typing import Optional, Dict, Any, List

from backend.agents.model_router import ModelRouter
from backend.agents.notebook.schema import (
    Algorithm,
    AlgorithmStep,
    KernelState,
    NotebookState,
)
from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# Number of algorithm candidates to generate. When N_CANDIDATES=1 (default),
# a single LLM call is used. When monkeypatched to >1 (e.g. by coder_v2
# benchmark configs), generates N candidates and uses a judge to pick the best.
N_CANDIDATES = 1

ALGORITHM_SYSTEM_PROMPT = """You are an algorithm designer. Your job is to convert a user's coding request into a clear, step-by-step algorithm that a coder agent can follow.

## Context

You will receive:
1. The user's request
2. The current notebook state (existing cells with their code)
3. The current kernel state (available variables)
4. Memory context (previous work done in this session)
5. Available data files in the workspace (with shapes and column names)

## CRITICAL: Reuse Existing Work

**This is the most important rule**: ALWAYS check the notebook state and kernel variables FIRST.

- If the user asks to MODIFY something (e.g., "make it a clustered heatmap", "change the colors"):
  1. Find the existing cell that creates what needs to be modified
  2. Create steps to EDIT that cell, NOT create new cells from scratch
  3. Reuse ALL existing variables (data, figures, etc.)

- If variables already exist in the kernel (like `df`, `data`, `fig`):
  1. DO NOT reload or recreate them
  2. Reference them directly in your steps

- If a visualization exists and needs modification:
  1. Use the existing figure/axes if possible
  2. Or modify the existing cell that created it

## Your Task

Create a MINIMAL algorithm that:
1. **Reuses** all existing variables and data from kernel state
2. **Modifies** existing cells when the user wants changes (not create new ones)
3. **Only creates new cells** for genuinely new functionality

## Guidelines

- Keep steps atomic - one logical operation per step
- NEVER recreate data that already exists
- NEVER reimport libraries that are already imported
- If data files are listed in workspace, use EXACT file paths — NEVER generate synthetic data
- For modifications: plan to EDIT the existing cell, not add new ones
- For visualizations, always include plt.savefig() to save the plot

## Output Format

You MUST respond with valid JSON in this exact format:

```json
{
  "task_summary": "Brief summary of the task",
  "is_modification": true/false,
  "modifies_cells": ["cell_id1"],
  "prerequisites": ["list", "of", "required", "variables"],
  "steps": [
    {
      "step_number": 1,
      "description": "What this step does",
      "rationale": "WHY this step is needed for the user's request",
      "action": "edit_cell or add_cell",
      "target_cell_id": "optional - cell to edit if action is edit_cell",
      "expected_output": "What the output should be",
      "validation_criteria": "How to verify it worked",
      "cell_type": "code"
    }
  ],
  "expected_final_output": "Description of final result",
  "estimated_cells": 5
}
```

Respond ONLY with the JSON, no additional text or explanation.
"""

ALGORITHM_JUDGE_PROMPT = """You are an algorithm judge. You will review {n} candidate algorithms for the same coding request and build the BEST final algorithm by selecting and combining the strongest steps from each.

## User Request
{user_request}

## Candidate Algorithms

{candidates_text}

## Your Task

1. Compare the candidates against the user's request
2. For each step in the final algorithm, pick the best version from the candidates (or merge ideas if one candidate has a better rationale but another has a better description)
3. Ensure the final algorithm is complete, logical, and minimal

## Evaluation Criteria
- **Completeness**: Does the algorithm address ALL parts of the user's request?
- **Rationale quality**: Are the "why" explanations sound and relevant?
- **Step ordering**: Is the sequence logical (e.g., import → load → process → visualize → save)?
- **Minimality**: No redundant or unnecessary steps
- **Reuse**: Does it properly reuse existing variables/cells when available?

## Output Format

Respond with the final algorithm in this exact JSON format:

```json
{{
  "task_summary": "Brief summary",
  "prerequisites": ["required", "variables"],
  "steps": [
    {{
      "step_number": 1,
      "description": "What this step does",
      "rationale": "Why this step is needed",
      "expected_output": "Expected output",
      "validation_criteria": "How to verify",
      "cell_type": "code"
    }}
  ],
  "expected_final_output": "Description of final result",
  "estimated_cells": 5
}}
```

Respond ONLY with the JSON, no additional text.
"""


def build_algorithm_prompt(
    user_request: str,
    notebook_state: NotebookState,
    kernel_state: Optional[KernelState] = None,
    memory_context: Optional[str] = None,
    environment_context: Optional[str] = None,
) -> str:
    """Build the user prompt for algorithm generation."""
    parts = [f"## User Request\n\n{user_request}"]

    # Add environment context (workspace files + data file details)
    if environment_context:
        parts.append(
            f"\n\n## Available Data Files (ON DISK — not yet in kernel memory)\n\n{environment_context}\n\n"
            "IMPORTANT: These files are ON DISK and must be loaded explicitly (e.g. pd.read_csv('files/filename.csv')). "
            "They are NOT already in kernel memory. You MUST include a step to load them. "
            "Use the EXACT file paths shown above. DO NOT generate synthetic data."
        )

    # Add memory context FIRST if available - this is critical for follow-ups
    if memory_context:
        parts.append(f"\n\n## Previous Work (IMPORTANT - Reuse this!)\n\n{memory_context}")

    parts.append(f"\n\n## Current Notebook State\n\n{notebook_state.to_context_string()}")

    if kernel_state and kernel_state.variables:
        parts.append(f"\n\n## Current Kernel State (Variables Available)\n\nThese variables are ALREADY in memory - DO NOT recreate them:\n{kernel_state.to_context_string()}")
    else:
        parts.append("\n\n## Current Kernel State\n\nNo variables defined yet.")

    # Add instruction based on context
    if memory_context or (kernel_state and kernel_state.variables):
        parts.append("\n\n## Your Task\n\nAnalyze the user's request in context of the EXISTING work above. If this is a follow-up or modification request, create steps that MODIFY existing cells rather than creating everything from scratch. Respond with JSON only.")
    else:
        parts.append("\n\n## Your Task\n\nCreate an algorithm to accomplish the user's request. Respond with JSON only.")

    return "\n".join(parts)


async def _stream_llm_response(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
) -> str:
    """Stream an LLM response and return the full text."""
    full_response = ""
    async for chunk in model_router.chat_stream(
        model_identifier=model_identifier,
        messages=messages,
        tools=None,
        think=False
    ):
        try:
            data = json.loads(chunk)
            if isinstance(data, dict) and "message" in data:
                msg = data["message"]
                if isinstance(msg, dict) and "content" in msg:
                    full_response += msg["content"]
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Error parsing chunk: {chunk}, {e}")
            pass
    logger.info(f"ALGORITHM RAW Stream Output ({len(full_response)} chars): {full_response[:500]}")
    return full_response


async def _generate_single_algorithm(
    model_router: ModelRouter,
    model_identifier: str,
    messages: List[Dict[str, str]],
    candidate_num: int,
) -> Optional[Algorithm]:
    """Generate a single algorithm candidate."""
    try:
        full_response = await _stream_llm_response(model_router, model_identifier, messages)
        algorithm = parse_algorithm_response(full_response)
        if algorithm:
            logger.info(f"Candidate {candidate_num}: {len(algorithm.steps)} steps")
            return algorithm
        else:
            logger.warning(f"Candidate {candidate_num}: failed to parse")
            return None
    except Exception as e:
        logger.warning(f"Candidate {candidate_num} generation failed: {e}")
        return None


def _algorithm_to_candidate_text(algorithm: Algorithm, idx: int) -> str:
    """Format an algorithm as text for the judge prompt."""
    lines = [f"### Candidate {idx}"]
    lines.append(f"**Summary**: {algorithm.task_summary}")
    lines.append(f"**Steps** ({len(algorithm.steps)}):")
    for step in algorithm.steps:
        rationale = ""
        # Check if step has rationale (stored in description or as extra field)
        step_dict = step.to_dict()
        if "rationale" in step_dict:
            rationale = f" — *Why*: {step_dict['rationale']}"
        lines.append(
            f"  {step.step_number}. {step.description}{rationale}"
            f"\n     Expected: {step.expected_output or 'N/A'}"
        )
    lines.append(f"**Final output**: {algorithm.expected_final_output or 'N/A'}")
    return "\n".join(lines)


async def generate_algorithm(
    model_router: ModelRouter,
    model_identifier: str,
    user_request: str,
    notebook_state: NotebookState,
    kernel_state: Optional[KernelState] = None,
    memory_context: Optional[str] = None,
    status_callback: Optional[Any] = None,
    environment_context: Optional[str] = None,
) -> Optional[Algorithm]:
    """
    Generate an algorithm to accomplish the user's request.

    When N_CANDIDATES=1 (default), uses a single LLM call.
    When N_CANDIDATES>1 (set via monkeypatch by coder_v2 benchmark configs),
    generates N candidates and uses a judge LLM call to pick the best.

    Args:
        status_callback: Optional async callable(detail: str) to emit UI status updates.
    """
    logger.info(f"Generating algorithm for request: {user_request[:100]}...")
    if memory_context:
        logger.info(f"Including memory context ({len(memory_context)} chars)")

    async def _emit_status(detail: str):
        if status_callback:
            await status_callback(detail)

    user_prompt = build_algorithm_prompt(user_request, notebook_state, kernel_state, memory_context, environment_context)
    messages = [
        {"role": "system", "content": ALGORITHM_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # Generate N_CANDIDATES candidates
    candidates: List[Algorithm] = []
    for i in range(1, N_CANDIDATES + 1):
        logger.info(f"Generating candidate {i}/{N_CANDIDATES}...")
        await _emit_status(f"Generating plan candidate {i}/{N_CANDIDATES}...")
        algorithm = await _generate_single_algorithm(
            model_router, model_identifier, messages, i
        )
        if algorithm:
            candidates.append(algorithm)

    if not candidates:
        logger.error("All algorithm candidates failed to generate")
        return None

    if len(candidates) == 1:
        logger.info(f"Algorithm generated: {len(candidates[0].steps)} steps")
        return candidates[0]

    # Multi-candidate: judge picks the best from all candidates
    await _emit_status(f"Judging {len(candidates)} candidates and merging final plan...")
    logger.info(f"Judging {len(candidates)} candidates...")
    try:
        candidates_text = "\n\n".join(
            _algorithm_to_candidate_text(alg, i + 1)
            for i, alg in enumerate(candidates)
        )
        judge_prompt = ALGORITHM_JUDGE_PROMPT.format(
            n=len(candidates),
            user_request=user_request,
            candidates_text=candidates_text,
        )
        judge_messages = [{"role": "user", "content": judge_prompt}]

        judge_response = await _stream_llm_response(
            model_router, model_identifier, judge_messages
        )
        final_algorithm = parse_algorithm_response(judge_response)

        if final_algorithm:
            logger.info(
                f"Judge selected final algorithm: {len(final_algorithm.steps)} steps "
                f"(from {len(candidates)} candidates)"
            )
            return final_algorithm
        else:
            logger.warning("Judge failed to produce valid algorithm, using best candidate")
    except Exception as e:
        logger.warning(f"Judge call failed: {e}, using best candidate")

    # Fallback: pick the candidate with the most steps (more thorough)
    best = max(candidates, key=lambda a: len(a.steps))
    logger.info(f"Fallback: using candidate with {len(best.steps)} steps")
    return best


def parse_algorithm_response(response: str) -> Optional[Algorithm]:
    """
    Parse the LLM response into an Algorithm object.

    Handles various response formats including:
    - Pure JSON
    - JSON in markdown code blocks
    - JSON with surrounding text
    """
    # Try direct parsing first
    try:
        data = json.loads(response.strip())
        if isinstance(data, dict):
            return Algorithm.from_dict(data)
    except (json.JSONDecodeError, AttributeError):
        pass

    # Try extracting from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict):
                return Algorithm.from_dict(data)
        except (json.JSONDecodeError, AttributeError):
            pass

    # Try finding JSON object anywhere in text
    json_match = re.search(r'\{[\s\S]*"task_summary"[\s\S]*\}', response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict):
                return Algorithm.from_dict(data)
        except (json.JSONDecodeError, AttributeError):
            pass

    logger.warning(f"Could not parse algorithm from response: {response[:500]}...")
    return None


def should_generate_algorithm(user_request: str) -> bool:
    """
    Determine if the request is complex enough to warrant algorithm generation.

    Simple requests (like "run cell 3") don't need an algorithm.
    Used by coder_loop v1.
    """
    simple_patterns = [
        "run cell",
        "execute cell",
        "delete cell",
        "show notebook",
        "what variables",
        "what cells",
        "help",
    ]

    request_lower = user_request.lower()
    for pattern in simple_patterns:
        if pattern in request_lower:
            return False

    return True
