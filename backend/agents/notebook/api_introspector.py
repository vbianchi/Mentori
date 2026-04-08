"""
API Introspector for Coder V2.

Implements the introspect_with_recovery algorithm from V2-8 benchmark:
  Before writing code the model declares every API call it plans to make.
  This scratchpad is injected into the step execution prompt, forcing the
  model to commit to correct method signatures BEFORE generating code.

V2-8 result: introspect_with_recovery → 77% avg pass rate (vs 46% free_form).
The mechanism prevents hallucinated method names and wrong argument orders.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Prompt ────────────────────────────────────────────────────────────────────

INTROSPECTION_PROMPT = """You are planning Python code for one step in a Jupyter notebook.

## Step to implement
{step_description}

## Expected output
{expected_output}

## Variables currently in kernel (already available — do NOT recreate)
{kernel_state}

---

Before writing any code, list EVERY Python function or method you plan to call.
For each entry write the EXACT call signature and what it returns.

Format — one entry per line, no preamble or explanation:
  - package.Class.method(arg1: type, arg2=default) → return_type

Rules:
  - Only list calls you are CERTAIN exist in standard or common scientific libraries
  - Use the full dotted path (e.g. pandas.DataFrame.corr, not just corr)
  - For instance methods use: object_name.method(…)
  - 3–10 entries is typical; do not exceed 15
  - If a library might not be installed, flag it: [CHECK: library_name]"""


# ── Public API ────────────────────────────────────────────────────────────────

async def introspect_step(
    model_router,
    model_identifier: str,
    step_description: str,
    expected_output: str,
    kernel_state_summary: str,
) -> str:
    """
    Ask the model to plan its API usage before writing code.

    Returns a compact scratchpad string that is injected into the step
    execution prompt.  On any failure returns "" so the caller degrades
    gracefully to the standard (non-introspected) prompt.

    Args:
        model_router: ModelRouter instance
        model_identifier: Model to call (same model used for step execution)
        step_description: The step description from the algorithm
        expected_output: Expected output for this step
        kernel_state_summary: Pre-built kernel state string (from build_kernel_state_summary)

    Returns:
        Scratchpad text listing planned API calls, or "" on failure.
    """
    prompt = INTROSPECTION_PROMPT.format(
        step_description=step_description,
        expected_output=expected_output or "Complete the step successfully",
        kernel_state=kernel_state_summary or "No variables defined yet",
    )
    try:
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "num_predict": 500},
        )
        scratchpad = response.get("message", {}).get("content", "").strip()
        if scratchpad:
            logger.info(
                f"API introspection completed ({len(scratchpad)} chars): "
                f"{scratchpad[:120]}..."
            )
        return scratchpad
    except Exception as e:
        logger.warning(
            f"API introspection failed — degrading to standard prompt: {e}"
        )
        return ""


def format_recovery_hint(api_scratchpad: str, error_message: str) -> str:
    """
    Build a targeted recovery hint by cross-referencing the API plan with
    the actual error.  Returned string is embedded in the retry section.

    Args:
        api_scratchpad: The original introspection output
        error_message: The error from the failed cell execution

    Returns:
        Hint string, or "" if no scratchpad is available.
    """
    if not api_scratchpad:
        return ""
    return (
        "Cross-reference the error against your API plan above.\n"
        "Common causes:\n"
        "  - Wrong method name or module path (check the plan)\n"
        "  - Incorrect argument type or order\n"
        "  - Library not installed — use [CHECK: library] markers as a hint\n"
        "Correct the specific call that failed, not the whole cell."
    )
