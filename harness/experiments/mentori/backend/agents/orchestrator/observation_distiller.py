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
from typing import Optional, Callable, Awaitable, Dict, Any

from backend.agents import lock_adapter  # noqa: F401  (puts the repository on sys.path for experiments.runner)
from backend.agents.orchestrator import run_records as rr
from experiments.runner.lock import load as load_lock

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

# The distiller fires when an observation would occupy more than this fraction
# of the synthesis model's context window.  Using 0.40 means a single step
# result is allowed to consume up to 40% of the available context before we
# compress it; the remaining 60% is reserved for other steps, the system
# prompt, and the synthesis output.
_DISTILL_FRACTION = 0.40

# The distiller's call carries no output cap (cuts.md observation_distiller.py:43, D25): the 1,200-token num_predict
# is removed, and the lock sets every value of the call. On Gemini that cap was shared with thinking (LIST.md Figure 4).


def _distill_threshold_chars() -> int:
    """
    The distillation threshold in characters: 0.40 x the lock's num_ctx x 4 characters per token (limits.md #25).
    Mentori read the context window from the admin database (token_utils.get_min_context_window, default 131,072);
    the experiments read it from LOCK.toml [generation] num_ctx, 131,072, which gives 209,712 characters.
    """
    return int(load_lock().d["generation"]["num_ctx"] * _DISTILL_FRACTION) * 4  # tokens → chars


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


# D52 (Figure 4, "distiller prompt F1"): prompt F1 of publication/scripts/exp_04b_distiller_ablation.py (worked
# examples that keep every number), copied byte for byte, the observation whole in both (exp_04b's 12,000-character
# cut is gone, audit F4). check_orchestrator pins the two prompts equal on observations under and over 12,000 characters.
_FEWSHOT_EXAMPLES = """
<example_1>
<input>
The study by Nguyen et al. (2024) in paper 39_zoonotic_southeast_asia.pdf analyzed 847 zoonotic spillover events across 11 countries between 2012-2023. Key findings include: influenza A (H5N1) accounted for 23.4% of events (n=198), followed by rabies at 18.7% (n=158) and leptospirosis at 15.2% (n=129). The case fatality rate for H5N1 was 52.8% (95% CI: 44.1-61.3%), significantly higher than the regional average of 12.3% (p<0.001). Risk factors identified via multivariate logistic regression included live animal market exposure (OR=3.42, 95% CI: 2.11-5.54), poultry farming (OR=2.87, 95% CI: 1.93-4.27), and proximity to bat roosts <2km (OR=2.15, 95% CI: 1.44-3.21). The authors note that surveillance coverage varied from 12% in Myanmar to 89% in Thailand, creating reporting bias. Figure 3 shows the spatiotemporal distribution across the study period. Table 2 presents the full regression model with 16 covariates.
</input>
<output>
**KEY FINDINGS**
- 847 zoonotic spillover events across 11 countries (2012-2023); H5N1 dominated at 23.4% (n=198), rabies 18.7% (n=158), leptospirosis 15.2% (n=129)
- H5N1 case fatality rate 52.8% (95% CI: 44.1-61.3%), vs regional average 12.3% (p<0.001)
- Top risk factors: live animal market exposure (OR=3.42), poultry farming (OR=2.87), bat roost proximity <2km (OR=2.15)
- Surveillance coverage ranged 12% (Myanmar) to 89% (Thailand) — reporting bias acknowledged

**SOURCES CITED**
- 39_zoonotic_southeast_asia.pdf (Nguyen et al. 2024) — Figure 3, Table 2

**GAPS OR CAVEATS**
- Surveillance coverage disparity (12-89%) creates reporting bias across countries
</output>
</example_1>

<example_2>
<input>
Analysis of AMR patterns in 03_amr_livestock.pdf reveals that resistance rates for E. coli isolates from broilers were: ampicillin 78.3%, tetracycline 71.2%, ciprofloxacin 45.6%, and cefotaxime 12.8%. The MIC90 values were 256 μg/mL, 128 μg/mL, 4 μg/mL, and 8 μg/mL respectively. Compared to the 2019 baseline, ciprofloxacin resistance increased by 8.4 percentage points (from 37.2% to 45.6%). The EUCAST breakpoint for ciprofloxacin is >0.5 μg/mL. A total of 342 isolates were tested from 28 farms across 3 regions.
</input>
<output>
**KEY FINDINGS**
- E. coli resistance in broilers: ampicillin 78.3%, tetracycline 71.2%, ciprofloxacin 45.6%, cefotaxime 12.8% (n=342 isolates, 28 farms, 3 regions)
- MIC90 values: ampicillin 256 μg/mL, tetracycline 128 μg/mL, ciprofloxacin 4 μg/mL, cefotaxime 8 μg/mL
- Ciprofloxacin resistance rose 8.4pp from 2019 baseline (37.2% → 45.6%); EUCAST breakpoint >0.5 μg/mL

**SOURCES CITED**
- 03_amr_livestock.pdf

**GAPS OR CAVEATS**
- None explicitly stated
</output>
</example_2>
"""


def _f1_prompt(tool_name: str, content: str) -> str:
    """exp_04b_distiller_ablation.build_prompt("F1", ...)'s prompt, with the observation whole."""
    return f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

Here are examples of good distillations that preserve all numbers:
{_FEWSHOT_EXAMPLES}

Now distill this observation following the same pattern:

<raw_observation>
{content}
</raw_observation>

Summarize in ≤ 600 words using the same KEY FINDINGS / SOURCES CITED / GAPS structure.

Rules:
- Preserve ALL quantitative results exactly (percentages, p-values, sample sizes, odds ratios, CIs)
- Preserve author names and publication years
- EVERY document mentioned must appear in the summary
- Do NOT add interpretation beyond what appears in the text"""


def distiller_prompt(tool_name: str, raw_content: str, variant: str = "on") -> str:
    """The distiller's prompt for a D52 switch value: Mentori's (_DISTILL_PROMPT) for "on", prompt F1 for "F1"."""
    if variant == "F1":
        return _f1_prompt(tool_name, raw_content)
    if variant != "on":
        raise ValueError(f"distiller prompt {variant!r}: the prompts are 'on' (Mentori's) and 'F1' (D52)")
    return _DISTILL_PROMPT.format(tool_name=tool_name, raw_content=raw_content)


# ── Public API ────────────────────────────────────────────────────────────────

async def distill_observation(
    tool_name: str,
    raw_content: str,
    model_router,
    model_identifier: str,
    event_callback: Optional[Callable[..., Awaitable[None]]] = None,
    variant: str = "on",
    outcome: Optional[Dict[str, Any]] = None,
    passages: Optional[list] = None,
    every_step: bool = False,
) -> str:
    """
    Compress a tool observation to ≤600 words if it exceeds the threshold.

    The model reads the whole observation (D25: the 12,000-character input cut is removed). On a failed or empty
    distillation the whole observation is passed on and the failure recorded (Q25, D68): Mentori cut it to the
    threshold instead. A lock refusal raises (Q38, D69).

    Args:
        tool_name: Name of the tool that produced the observation (for context)
        raw_content: Full text returned by the tool
        model_router: ModelRouter instance
        model_identifier: Model to use for distillation (librarian role preferred)
        event_callback: Optional async callback to emit token_usage events
        variant: the prompt, "on" (Mentori's) or "F1" (D52)
        outcome: a dict this call fills: status ("below_threshold", "distilled", "empty" or "failed"), variant,
            threshold_chars, raw_chars, out_chars, error (failure's text), call_status, call_seq
        passages: the passage ids raw_content holds whole (A6, D37), set for the call
        every_step: Q82 (D75)'s stress condition (switch distiller_trigger "every_step"): any non-empty observation is
            distilled, not only one above the threshold; not Mentori's default. outcome["trigger"] records it

    Returns:
        Compact observation string (distilled, or the whole observation)
    """
    record = outcome if outcome is not None else {}   # not "out": the token block below uses out
    threshold = _distill_threshold_chars()
    record.update({"variant": variant, "threshold_chars": threshold, "raw_chars": len(raw_content or ""),
                "out_chars": len(raw_content or ""), "error": None, "call_status": None, "call_seq": None,
                "trigger": "every_step" if every_step else "threshold"})
    if not raw_content or (len(raw_content) <= threshold and not every_step):
        record["status"] = "below_threshold"
        return raw_content

    logger.info(
        f"Distilling {tool_name} output: {len(raw_content)} chars → target ≤600 words"
    )

    prompt = distiller_prompt(tool_name, raw_content, variant)

    rr.set_passages(passages or [])
    try:
        response = await model_router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": prompt}],
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
            result = f"[Distilled from {len(raw_content):,} chars — full output in tool_result event]\n\n{distilled}"
            record.update({"status": "distilled", "out_chars": len(result)})
            return result

        logger.warning("Distillation returned empty response; passing the whole observation (Q25)")
        record["status"] = "empty"

    except rr.REFUSALS:
        raise  # Q38 (D69): a lock refusal is a setup error and fails the question
    except Exception as e:
        logger.warning(f"Distillation failed ({e}); passing the whole observation (Q25)")
        fail = rr.failure(e)
        record.update({"status": "failed", "error": fail["error"], "call_status": fail["call_status"],
                    "call_seq": fail["call_seq"]})

    # Q25 (D68): a failed or empty distillation passes the whole observation on; outcome["status"] is "failed" or
    # "empty", and the step's record gives distill_failed True (StepResult.to_record)
    return raw_content


def should_distill(raw_content: str) -> bool:
    """Return True if the content is large enough to warrant distillation."""
    return bool(raw_content) and len(raw_content) > _distill_threshold_chars()
