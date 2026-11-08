#!/usr/bin/env python3
"""
V4-7.5: Distiller Prompt Engineering Ablation (T3, experiment 9)

Tests whether structured prompt improvements can close the distiller gap
identified in V4-7 (best model: 73.6% number retention).

7 variants tested:
  - baseline:  Original _DISTILL_PROMPT (from observation_distiller.py)
  - F1:        Few-shot examples (2 input→output pairs showing number preservation)
  - F2:        Dynamic word budget (scales with number density in input)
  - F3:        Simplified format (no rigid headers, focus on preserving content)
  - F1_F3:     Few-shot + simplified format
  - F2_F3:     Dynamic budget + simplified format
  - F1_F2_F3:  All three fixes combined

Models: the submitted list (MODELS) under exp_04's t3_model rule, plus gemini-3-flash-preview (D198 O7b; ruling Q4 of 1
November: baseline and F1, draw 1), each checked against the lock (exp_04's model_matrix rules)
Dataset: 97 items from V4-7 distiller benchmark

Reanalysis (audit F4, plan row B13; D49, D66, D67, D77; LOCK.toml [text]):
  - Every call runs inside a run context: one run per (variant, model), run_id exp_04b__<variant>__<model key>, sink
    findings/runs/<run_id>/ holding answers.jsonl (one line per key, written here), run_identity.json (written by
    experiment.context) and calls.jsonl (one line per model call, written by the lock adapter); no ctx/ sidecar,
    since no tool server runs (rc.dump is not called). One context per (item, draw), draws 1, 2, 3 (D49, as
    exp_04). A key already stored is skipped, so a run always resumes.
  - No options and no think are passed: the lock sets every value and the thinking (D66, the maker's default). F2's
    dynamic output limit (num_predict 1,200 to 2,400) was recorded as caller_asked and never sent, so it is gone; F2's
    word budget in the prompt stays. The observation is sent whole (LOCK [text]; audit F4: was 12,000 characters),
    and the distillation is stored whole.
  - The word budget of F2, F2_F3 and F1_F2_F3, min(900, max(400, 200 + 12 * n_numbers)), counts the distinct numbers
    of the observation it is sent with. With the 12,000-character cut removed, n_numbers now counts the whole
    observation, so on an item longer than 12,000 characters the budget can be higher than the submitted run's
    (up to the 900 cap). The formula is unchanged.
  - A lock refusal stops the run with nothing stored for its key (Q38, D69); a failed call is stored with its error.
  - The dataset is read from DATASET_PATH and written only by --build-dataset (from the V4-4 results, as exp_04's
    --build-dataset writes the same file). --dry-run and a run never write it: a missing dataset is reported by
    --dry-run and refuses a run. --datasets <folder> (T3-9) reads the distiller's items from a frozen folder instead,
    checked by sha256 and count against its MANIFEST.json (exp_04's load_frozen), and DATASET_PATH is not read.
  - --counts-only (D195): no summary is computed, logged or printed; the log holds counts of answers only. The answers
    files are written as they are without it. Without it the summary is logged and printed, as before.

Usage (from experiments/mentori):
    # Build the dataset from the V4-4 results (no model call)
    uv run python publication/scripts/exp_04b_distiller_ablation.py --build-dataset

    # The matrix and the work list: no model call, no file written
    uv run python publication/scripts/exp_04b_distiller_ablation.py --dry-run

    # Run all variants on every model the lock runs
    uv run python publication/scripts/exp_04b_distiller_ablation.py --ollama-url http://127.0.0.1:21441

    # Smoke test (5 items, draw 1, one variant, one model)
    uv run python publication/scripts/exp_04b_distiller_ablation.py --ollama-url http://127.0.0.1:21441 \\
        --variants F1 --models gemma3:27b --max-items 5 --draws 1
"""

import argparse
import asyncio
import json
import logging
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from exp_common import RESULTS_DIR
from backend.agents.model_router import ModelRouter
from backend.agents import lock_adapter  # noqa: F401  (puts the reanalysis root on sys.path for experiments.runner)
from backend.agents.orchestrator.observation_distiller import _DISTILL_PROMPT

from experiments.runner import experiment as ex
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError, load as load_lock

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_04b_distiller_ablation")
logger.setLevel(logging.INFO)

V4_4_RESULTS_PATH = RESULTS_DIR / "v4_4_generation_latest.json"
DATASET_PATH = RESULTS_DIR / "v4_7_bench_distiller_dataset.json"

EXPERIMENT = "exp_04b"
FIGURE = 4                      # draws 1, 2, 3 (D49), as exp_04
ANSWERS = "answers.jsonl"       # <sink>/answers.jsonl, one line per (item, draw), appended through run_context.append
RUNS_ROOT = ex.RUNS
REFUSALS = (LockError, rc.RunContextError)   # Q38 (D69): a setup error; the run stops, nothing stored for the key

# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────

# The submitted list, kept as the record of what ran; model_list() applies exp_04's t3_model and the lock to it (audit
# F4). The Gemini line is not the submitted list's: it is D198 O7b, for Supplementary Figure 13 (ruling Q4, 1 November).
MODELS = [
    ("ollama::llama3:8b", "8B"),              # Meta
    ("ollama::gpt-oss:20b", "20B"),           # GPT-OSS
    ("ollama::devstral-small-2:24b", "24B"),  # Mistral
    ("ollama::gemma3:27b", "27B"),            # Google
    ("ollama::qwen3-coder:latest", "30B"),    # Qwen
    ("ollama::nemotron-3-nano:30b", "30B"),   # NVIDIA
    ("ollama::olmo-3:32b", "32B"),            # AI2
    ("gemini::gemini-3-flash-preview", "API"),   # D198 O7b
]
THINKING = None   # D66: the distiller runs at its maker's default thinking, the lock's generator rule


def model_list(lock=None):
    """(entries, refused): MODELS under exp_04's t3_model, entries the lock runs at THINKING, refused (model identifier,
    the lock's reason) for the others. The lock file only; no server."""
    from exp_04_component_bench import lock_check, t3_model
    lock = lock or load_lock()
    entries, refused = [], []
    for model_id, size in MODELS:
        model_id = t3_model(model_id)
        if model_id is None:
            continue
        try:
            lock_check(lock, model_id, THINKING)
        except LockError as e:
            refused.append((model_id, str(e)))
            continue
        entries.append((model_id, size))
    return entries, refused


def model_short_for(model_id: str) -> str:
    """The model's part of a run_id: the tag with ':' as '-' ('gemma3-27b'), as exp_04's model_key."""
    return model_id.split("::", 1)[-1].replace(":", "-").replace("/", "_")


# ─────────────────────────────────────────────────────────────
# Number & source extraction (from V4-7)
# ─────────────────────────────────────────────────────────────

def extract_numbers(text: str) -> set:
    if not text:
        return set()
    return set(re.findall(r"\d+(?:\.\d+)?(?:%|‰)?", text))


def extract_sources(text: str) -> set:
    if not text:
        return set()
    patterns = [
        r"\b\d{2}_\w+\.pdf\b",
        r"\b[\w-]+\.pdf\b",
        r"\b[A-Z][a-z]+ et al\.?,? \d{4}\b",
    ]
    sources = set()
    for pattern in patterns:
        sources.update(re.findall(pattern, text))
    return sources


# ─────────────────────────────────────────────────────────────
# Prompt Variants
# ─────────────────────────────────────────────────────────────

# --- F1: Few-shot examples ---
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

# --- F3: Simplified format ---
_SIMPLIFIED_FORMAT = """Condense the observation into a brief summary. Your ONLY priority is preserving information:

1. Keep ALL numbers exactly as they appear (percentages, p-values, sample sizes, odds ratios, confidence intervals, counts)
2. Keep ALL document names and author citations
3. Drop filler text, repetition, and non-essential narrative

Write in compact bullet points. No headers required — just the essential facts with their numbers."""


def build_prompt(variant: str, tool_name: str, raw_content: str) -> str:
    """Build prompt for a given variant. The observation goes in whole (LOCK [text]; audit F4: was 12,000
    characters). No output limit is returned: the lock sets num_predict (audit F4)."""

    content = raw_content
    n_numbers = len(extract_numbers(content))

    if variant == "baseline":
        prompt = _DISTILL_PROMPT.format(tool_name=tool_name, raw_content=content)
        return prompt

    elif variant == "F1":
        # Few-shot + original structure
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

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
        return prompt

    elif variant == "F2":
        # Dynamic word budget
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        prompt = _DISTILL_PROMPT.format(tool_name=tool_name, raw_content=content)
        # Patch the word limit in the prompt
        prompt = prompt.replace("≤ 600 words", f"≤ {word_budget} words")
        prompt = prompt.replace("≤ 35 words", f"≤ 50 words")
        return prompt

    elif variant == "F3":
        # Simplified format
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

<raw_observation>
{content}
</raw_observation>

{_SIMPLIFIED_FORMAT}"""
        return prompt

    elif variant == "F1_F3":
        # Few-shot + simplified format
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

Here are examples of good distillations:
{_FEWSHOT_EXAMPLES}

Now distill this observation:

<raw_observation>
{content}
</raw_observation>

{_SIMPLIFIED_FORMAT}"""
        return prompt

    elif variant == "F2_F3":
        # Dynamic budget + simplified format
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

<raw_observation>
{content}
</raw_observation>

Condense the observation into ≤ {word_budget} words. Your ONLY priority is preserving information:

1. Keep ALL numbers exactly as they appear (percentages, p-values, sample sizes, odds ratios, confidence intervals, counts)
2. Keep ALL document names and author citations
3. Drop filler text, repetition, and non-essential narrative

Write in compact bullet points. No headers required — just the essential facts with their numbers."""
        return prompt

    elif variant == "F1_F2_F3":
        # All three fixes
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

Here are examples of good distillations:
{_FEWSHOT_EXAMPLES}

Now distill this observation:

<raw_observation>
{content}
</raw_observation>

Condense into ≤ {word_budget} words. Your ONLY priority is preserving information:

1. Keep ALL numbers exactly as they appear (percentages, p-values, sample sizes, odds ratios, confidence intervals, counts)
2. Keep ALL document names and author citations
3. Drop filler text, repetition, and non-essential narrative

Write in compact bullet points. No headers required — just the essential facts with their numbers."""
        return prompt

    else:
        raise ValueError(f"Unknown variant: {variant}")


ALL_VARIANTS = ["baseline", "F1", "F2", "F3", "F1_F3", "F2_F3", "F1_F2_F3"]


# ─────────────────────────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────────────────────────

def load_dataset() -> Optional[List[Dict]]:
    """The distiller dataset at DATASET_PATH, or None when it does not exist. Reads only; --build-dataset writes it."""
    if not DATASET_PATH.exists():
        return None
    logger.info(f"Loading dataset from {DATASET_PATH}")
    with open(DATASET_PATH) as f:
        return json.load(f)


def build_dataset() -> List[Dict]:
    """Builds the distiller dataset from the V4-4 results (exp_04's build_distiller_dataset) and writes it to
    DATASET_PATH. The only writer of the dataset here (--build-dataset); no model call."""
    if not V4_4_RESULTS_PATH.exists():
        raise SystemExit(f"cannot build the dataset: {V4_4_RESULTS_PATH} does not exist")
    logger.info("Building distiller dataset from V4-4 results...")
    with open(V4_4_RESULTS_PATH) as f:
        v4_4 = json.load(f)
    pqr = v4_4.get("per_question_results", [])

    from exp_04_component_bench import build_distiller_dataset
    dataset = build_distiller_dataset(pqr)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATASET_PATH, "w") as f:
        json.dump(dataset, f, indent=2)
    logger.info(f"Saved dataset: {len(dataset)} items → {DATASET_PATH}")
    return dataset


def no_dataset_message() -> str:
    return f"no dataset: {DATASET_PATH} does not exist (build it with --build-dataset)"


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

def get_response_text(response: dict) -> str:
    msg = response.get("message", {})
    if isinstance(msg, dict):
        return msg.get("content", "")
    return str(msg) if msg else ""


def extract_tokens(response: dict) -> tuple:
    inp = response.get("prompt_eval_count", 0)
    out = response.get("eval_count", 0)
    if not inp and not out:
        usage = response.get("usage", {})
        inp = usage.get("input_tokens", usage.get("prompt_tokens", 0))
        out = usage.get("output_tokens", usage.get("completion_tokens", 0))
    return inp or 0, out or 0


async def run_single(
    item: Dict,
    variant: str,
    router: ModelRouter,
    model_id: str,
) -> Dict:
    """Run one distiller variant on one item, inside the item's run context."""
    prompt = build_prompt(variant, item["tool_name"], item["raw_content"])

    t0 = time.time()
    try:
        response = await router.chat(
            model_identifier=model_id,
            messages=[{"role": "user", "content": prompt}],
        )   # audit F4: no options, no think; the lock sets every value and the thinking (D66)
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        if not text.strip():
            return {
                "variant": variant,
                "question_id": item["question_id"],
                "distilled": text,
                "number_retention": 0,
                "source_retention": 0,
                "word_count": 0,
                "compression_ratio": 0,
                "latency_s": round(latency, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "error": "Empty response",
            }

        raw_numbers = set(item.get("numbers", []))
        raw_sources = set(item.get("sources", []))
        dist_numbers = extract_numbers(text)
        dist_sources = extract_sources(text)

        number_retention = (
            len(raw_numbers & dist_numbers) / len(raw_numbers)
            if raw_numbers else 1.0
        )
        source_retention = (
            len(raw_sources & dist_sources) / len(raw_sources)
            if raw_sources else 1.0
        )

        word_count = len(text.split())
        compression_ratio = len(text) / item["raw_length"] if item["raw_length"] > 0 else 0

        return {
            "variant": variant,
            "question_id": item["question_id"],
            "distilled": text,              # whole (LOCK [text] stored_text)
            "number_retention": round(number_retention, 3),
            "source_retention": round(source_retention, 3),
            "word_count": word_count,
            "compression_ratio": round(compression_ratio, 3),
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "error": None,
        }

    except REFUSALS:
        raise   # Q38 (D69): a lock refusal is a setup error, never the distiller's stored outcome
    except Exception as e:
        return {
            "variant": variant,
            "question_id": item["question_id"],
            "distilled": "",
            "number_retention": 0,
            "source_retention": 0,
            "word_count": 0,
            "compression_ratio": 0,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "error": str(e),
        }


def read_answers(path: Path) -> List[Dict]:
    """The records of a run's answers.jsonl (empty when it does not exist); a line that is not an answer record, or
    a key stored twice, is refused (exp_04's read_answers)."""
    from exp_04_component_bench import read_answers as _read
    return _read(path)


def work_list(items: List[Dict], variants: List[str], models: List[tuple], draws: tuple,
              runs_root: Path = RUNS_ROOT) -> List[Dict]:
    """Every (model, variant, draw, item) in run order, with its run_id, item_id, answer key and whether the key is
    stored. Reads the answers files; writes nothing."""
    from exp_04_component_bench import item_id_for
    out = []
    for model_id, model_size in models:
        ms = model_short_for(model_id)
        for variant in variants:
            rid = ex.run_id(EXPERIMENT, variant, ms)
            stored = {r["answer_key"] for r in read_answers(Path(runs_root) / rid / ANSWERS)}
            for draw in draws:
                for idx, item in enumerate(items):
                    iid = item_id_for(item, idx)
                    key = ex.answer_key(ms, iid, draw)
                    out.append({"model_id": model_id, "model_short": ms, "variant": variant, "run_id": rid,
                                "draw": draw, "item": item, "item_id": iid, "key": key, "present": key in stored})
    return out


def _compute_summary(results: List[Dict]) -> Dict:
    """Compute summary stats from a list of per-item results."""
    valid = [r for r in results if not r.get("error")]
    errors = sum(1 for r in results if r.get("error"))
    if not valid:
        return {}
    return {
        "n": len(valid),
        "n_errors": errors,
        "mean_number_retention": round(statistics.mean([r["number_retention"] for r in valid]), 4),
        "mean_source_retention": round(statistics.mean([r["source_retention"] for r in valid]), 4),
        "mean_word_count": round(statistics.mean([r["word_count"] for r in valid]), 1),
        "mean_compression_ratio": round(statistics.mean([r["compression_ratio"] for r in valid]), 3),
        "mean_latency_s": round(statistics.mean([r["latency_s"] for r in valid]), 1),
        "mean_tokens_out": round(statistics.mean([r["tokens_out"] for r in valid]), 0),
    }


async def run_experiment(
    dataset: List[Dict],
    variants: List[str],
    models: List[tuple],
    base_url: str,
    draws: tuple = ex.draws(FIGURE),
    max_items: Optional[int] = None,
    runs_root: Path = RUNS_ROOT,
    router=None,
    counts_only: bool = False,
):
    """Run all variants x models x draws x items, one run context per (item, draw) (audit F4). A stored key is
    skipped. The answers files are the record; the summary is computed from them and printed. counts_only (D195):
    no summary is computed, logged or printed, only the number of answers each run holds for this work list."""

    items = dataset[:max_items] if max_items else dataset
    router = router or ModelRouter()
    work = work_list(items, variants, models, draws, runs_root)
    all_results = {}

    for model_id, model_size in models:
        model_short = model_short_for(model_id)
        logger.info(f"\n{'='*60}")
        logger.info(f"Model: {model_short} ({model_size})")
        logger.info(f"{'='*60}")

        model_results = {}

        for variant in variants:
            rid = ex.run_id(EXPERIMENT, variant, model_short)
            sink = ex.sink(rid, runs_root)
            mine = [w for w in work if w["run_id"] == rid]
            pending = [w for w in mine if not w["present"]]
            logger.info(f"\n  Variant: {variant} ({len(items)} items x draws {list(draws)}; "
                        f"{len(mine) - len(pending)} stored)")

            for n, w in enumerate(pending, 1):
                # One run context per (item, draw): every call goes through the lock (D67)
                ctx = ex.context(EXPERIMENT, variant, w["item_id"], w["draw"], {"distiller": model_id}, THINKING,
                                 base_url=base_url, run=rid, sink=sink, judge=False)
                with rc.run(ctx):
                    try:
                        result = await run_single(w["item"], variant, router, model_id)
                    except REFUSALS as e:
                        raise SystemExit(f"run {rid} stopped at {w['key']}: {type(e).__name__}: {e} (Q38: a lock "
                                         f"refusal is a setup error; nothing stored for the key)") from e
                    result.update({"answer_key": w["key"], "item_key": w["item_id"], "draw": w["draw"],
                                   "model_id": model_id, "thinking": THINKING})
                    rc.append(result, ANSWERS)
                if n % 10 == 0 or n == len(pending):
                    logger.info(f"    [{len(mine) - len(pending) + n}/{len(mine)}] stored")

            keys = {w["key"] for w in mine}
            results = [r for r in read_answers(sink / ANSWERS) if r["answer_key"] in keys]
            if counts_only:                     # D195: no summary computed, logged or printed
                model_results[variant] = {"n": len(results), "run_id": rid}
                print(f"{rid}: {len(results)} answers")
                continue
            summary = _compute_summary(results)
            model_results[variant] = {"summary": summary, "run_id": rid}

            logger.info(f"  → {variant}: num_ret={summary.get('mean_number_retention', 0):.3f} "
                        f"src_ret={summary.get('mean_source_retention', 0):.3f} "
                        f"words={summary.get('mean_word_count', 0):.0f} "
                        f"lat={summary.get('mean_latency_s', 0):.1f}s")

        all_results[model_short] = model_results

    output = {
        "experiment": "v4_7_5_distiller_ablation",
        "n_items": len(items),
        "draws": list(draws),
        "variants": variants,
        "models": [m[0] for m in models],
        "results": all_results,
    }
    if counts_only:
        return output

    # Print summary table
    print("\n" + "=" * 80)
    print("V4-7.5 DISTILLER ABLATION — RESULTS")
    print("=" * 80)
    for model_short, model_results in all_results.items():
        print(f"\n  {model_short}:")
        print(f"  {'Variant':<12} {'NumRet':>8} {'SrcRet':>8} {'Words':>7} {'Lat(s)':>7} {'TokOut':>7}")
        print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*7} {'-'*7} {'-'*7}")
        for variant in variants:
            s = model_results.get(variant, {}).get("summary", {})
            if s:
                print(f"  {variant:<12} {s['mean_number_retention']:>8.3f} "
                      f"{s['mean_source_retention']:>8.3f} "
                      f"{s['mean_word_count']:>7.0f} "
                      f"{s['mean_latency_s']:>7.1f} "
                      f"{s['mean_tokens_out']:>7.0f}")
    print()

    return output


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4-7.5: Distiller prompt ablation (T3; under the lock)")
    parser.add_argument("--variants", nargs="+", default=ALL_VARIANTS,
                        choices=ALL_VARIANTS, help="Variants to test")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Model short names (e.g. gemma3:27b nemotron-3-nano:30b)")
    parser.add_argument("--draws", nargs="+", type=int, default=list(ex.draws(FIGURE)),
                        choices=list(ex.draws(FIGURE)), help="Draws to run (default 1 2 3, D49)")
    parser.add_argument("--ollama-url", default=None,
                        help="The Ollama server the run contexts name (required for a run)")
    parser.add_argument("--runs-root", type=Path, default=None,
                        help="Write each run's sink under this directory instead of findings/runs (smoke tests)")
    parser.add_argument("--max-items", type=int, default=None, help="Limit items for smoke test")
    parser.add_argument("--build-dataset", action="store_true",
                        help="Build the dataset from the V4-4 results and write it (no model call); the only writer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the models and the work list; no model call, no file written")
    parser.add_argument("--datasets", type=Path, default=None,
                        help="A frozen folder with MANIFEST.json (T3-9): the items come from it, checked by sha256")
    parser.add_argument("--counts-only", action="store_true",
                        help="D195: compute, log and print no summary, only counts of answers")
    args = parser.parse_args()
    if args.build_dataset and args.datasets:
        parser.error("--build-dataset writes the built dataset; --datasets reads a frozen one")
    if args.build_dataset:
        build_dataset()
        return
    if not args.dry_run and not args.ollama_url:
        parser.error("--ollama-url is required for a run (the run context names the Ollama server)")
    draws = tuple(sorted(set(args.draws)))
    runs_root = args.runs_root or RUNS_ROOT

    # Every model is checked against the lock first; a refused one stops a run before any call
    models, refused = model_list()
    if args.models:
        models = [(mid, size) for mid, size in models if any(m in mid for m in args.models)]
        refused = [(mid, why) for mid, why in refused if any(m in mid for m in args.models)]
        if not models and not refused:
            print(f"No matching models for: {args.models}")
            print(f"Available: {[m[0] for m in model_list()[0]]}")
            sys.exit(1)

    if args.dry_run:
        print(f"exp_04b dry run: draws {list(draws)}; thinking: the lock's generator rule (D66)")
        print(f"{len(models)} models the lock runs: {', '.join(m[0] for m in models)}")
        print(f"{len(refused)} models the lock refuses:")
        for mid, why in refused:
            print(f"  {mid:<40} {why}")
    elif refused:
        raise SystemExit("the lock does not run " + "; ".join(f"{m} ({why})" for m, why in refused)
                         + ". Nothing was started: leave them out with --models, or add their lock rows.")

    if args.datasets:
        from exp_04_component_bench import load_frozen
        dataset = load_frozen(args.datasets, ["distiller"])["distiller"]
    else:
        dataset = load_dataset()   # reads only; a missing dataset is reported (--dry-run) or refuses the run
    if dataset is None:
        if args.dry_run:
            print(no_dataset_message())
            return
        raise SystemExit(no_dataset_message() + ". Nothing was started.")
    items = dataset[:args.max_items] if args.max_items else dataset
    if args.dry_run:
        work = work_list(items, args.variants, models, draws, runs_root)
        print(f"{len(items)} items x {len(args.variants)} variants x {len(models)} models x {len(draws)} draws = "
              f"{len(work)} answers, {sum(w['present'] for w in work)} stored")
        return

    logger.info(f"Dataset: {len(dataset)} items")
    logger.info(f"Variants: {args.variants}")
    logger.info(f"Models: {[m[0] for m in models]}")
    logger.info(f"Total evals: {len(items) * len(args.variants) * len(models) * len(draws)}")

    asyncio.run(run_experiment(
        dataset=dataset,
        variants=args.variants,
        models=models,
        base_url=args.ollama_url,
        draws=draws,
        max_items=args.max_items,
        runs_root=runs_root,
        counts_only=args.counts_only,
    ))


if __name__ == "__main__":
    main()
