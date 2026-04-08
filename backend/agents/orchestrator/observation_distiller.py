"""
Observation Distiller — P1-E-1 Context Engineering.

Compresses large tool outputs (≥2 000 chars / ~500 tokens) into a structured
summary before they enter the synthesis context window.

Motivation (V2-5 scaling collapse):
  rlm_20 degrades from 70% → 10% at s100 (100-paper corpus) because raw tool
  outputs fill the context and displace task-critical information.
  Distilling each observation to ≤600 words prevents this crowding effect.

Usage::

    from backend.agents.orchestrator.observation_distiller import distill_observation

    compact = await distill_observation(
        tool_name="deep_research_rlm",
        raw_content=result_content,
        model_router=model_router,
        model_identifier=librarian_model,
    )
    # compact is ≤~400 words; raw_content available for UI display separately
"""

import logging
from typing import Optional, Callable, Awaitable

from backend.agents.token_utils import get_min_context_window, estimate_tokens

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

# The distiller fires when an observation would occupy more than this fraction
# of the synthesis model's context window.  Using 0.40 means a single step
# result is allowed to consume up to 40% of the available context before we
# compress it; the remaining 60% is reserved for other steps, the system
# prompt, and the synthesis output.
_DISTILL_FRACTION = 0.40

# Hard cap on distillation output (num_predict for the distiller call)
DISTILL_MAX_OUTPUT_TOKENS = 1200


def _distill_threshold_chars() -> int:
    """
    Compute the distillation threshold in characters based on the admin-set
    minimum context window.  Called once per step evaluation (cheap DB read
    with SQLite; result could be cached if needed).
    """
    return int(get_min_context_window() * _DISTILL_FRACTION) * 4  # tokens → chars


# ── Prompt ────────────────────────────────────────────────────────────────────

_DISTILL_PROMPT = """You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

<raw_observation>
{raw_content}
</raw_observation>

Summarize the observation above in ≤ 600 words. Use this structure:

**KEY FINDINGS**
- (3-10 bullets, each ≤ 35 words; preserve specific numbers, names, technical terms)
- If the observation covers multiple documents, add a sub-header before each document's findings:
  **document_name.pdf**: finding 1 / finding 2 / ...

**SOURCES CITED**
- (list document filenames and page/section numbers that appear in the text)

**GAPS OR CAVEATS**
- (1-3 short bullets — only if the tool explicitly flagged limitations or missing data)

Rules:
- Do NOT add interpretation beyond what appears in the text
- Preserve all quantitative results exactly (percentages, p-values, sample sizes)
- Preserve author names and publication years
- EVERY document mentioned in the observation must appear in KEY FINDINGS
- If the text is already a summary or very short, return it verbatim"""


# ── Public API ────────────────────────────────────────────────────────────────

async def distill_observation(
    tool_name: str,
    raw_content: str,
    model_router,
    model_identifier: str,
    event_callback: Optional[Callable[..., Awaitable[None]]] = None,
) -> str:
    """
    Compress a tool observation to ≤600 words if it exceeds the threshold.

    On any failure (model unavailable, timeout, parse error) the function
    degrades gracefully: returns the raw content truncated to 2 000 chars.

    Args:
        tool_name: Name of the tool that produced the observation (for context)
        raw_content: Full text returned by the tool
        model_router: ModelRouter instance
        model_identifier: Model to use for distillation (librarian role preferred)
        event_callback: Optional async callback to emit token_usage events

    Returns:
        Compact observation string (distilled or original if short enough)
    """
    threshold = _distill_threshold_chars()
    if not raw_content or len(raw_content) <= threshold:
        return raw_content

    logger.info(
        f"Distilling {tool_name} output: {len(raw_content)} chars → target ≤600 words"
    )

    prompt = _DISTILL_PROMPT.format(
        tool_name=tool_name,
        raw_content=raw_content[:12000],  # cap input to avoid runaway cost
    )

    try:
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.0,
                "num_predict": DISTILL_MAX_OUTPUT_TOKENS,
            },
        )

        # Emit token usage from non-streaming chat() response
        if event_callback:
            inp = response.get("prompt_eval_count", 0)
            out = response.get("eval_count", 0)
            # Gemini / OpenAI fallback
            if not inp and not out:
                usage = response.get("usage", {})
                inp = usage.get("input_tokens", usage.get("prompt_tokens", 0))
                out = usage.get("output_tokens", usage.get("completion_tokens", 0))
            if inp or out:
                try:
                    await event_callback({
                        "type": "token_usage",
                        "token_usage": {"input": inp, "output": out, "total": inp + out},
                        "source": "distiller",
                    })
                except Exception:
                    pass  # Never let telemetry break distillation

        distilled = response.get("message", {}).get("content", "").strip()

        if distilled:
            logger.info(
                f"Distillation complete: {len(raw_content)} → {len(distilled)} chars"
            )
            return f"[Distilled from {len(raw_content):,} chars — full output in tool_result event]\n\n{distilled}"

        # Empty response — fall through to truncation fallback
        logger.warning("Distillation returned empty response, using truncation fallback")

    except Exception as e:
        logger.warning(f"Distillation failed ({e}), using truncation fallback")

    # Truncation fallback: truncate to the dynamic threshold with marker
    threshold = _distill_threshold_chars()
    truncated = raw_content[:threshold]
    return f"{truncated}\n\n[... output truncated from {len(raw_content):,} chars — see tool_result event for full content]"


def should_distill(raw_content: str) -> bool:
    """Return True if the content is large enough to warrant distillation."""
    return bool(raw_content) and len(raw_content) > _distill_threshold_chars()
