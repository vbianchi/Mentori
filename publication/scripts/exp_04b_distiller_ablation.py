#!/usr/bin/env python3
"""
V4-7.5: Distiller Prompt Engineering Ablation

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

Models: llama3:8b (fast, below par) + nemotron-3-nano:30b (current best)
Dataset: 97 items from V4-7 distiller benchmark

Usage:
    # Run all variants on both models
    uv run python publication/scripts/exp_04b_distiller_ablation.py

    # Run specific variant
    uv run python publication/scripts/exp_04b_distiller_ablation.py --variants baseline F1 F2

    # Smoke test (5 items)
    uv run python publication/scripts/exp_04b_distiller_ablation.py --max-items 5

    # Specific port
    uv run python publication/scripts/exp_04b_distiller_ablation.py --port 11435

    # Single model
    uv run python publication/scripts/exp_04b_distiller_ablation.py --models llama3:8b
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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from exp_common import RESULTS_DIR, save_final_results
from backend.agents.model_router import ModelRouter
from backend.agents.orchestrator.observation_distiller import _DISTILL_PROMPT

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_04b_distiller_ablation")
logger.setLevel(logging.INFO)

V4_4_RESULTS_PATH = RESULTS_DIR / "v4_4_generation_latest.json"
DATASET_PATH = RESULTS_DIR / "v4_7_bench_distiller_dataset.json"

NUM_CTX = 24576
NUM_PREDICT_DEFAULT = 1200

# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────

MODELS = [
    ("ollama::llama3:8b", "8B"),              # Meta
    ("ollama::gpt-oss:20b", "20B"),           # GPT-OSS
    ("ollama::devstral-small-2:24b", "24B"),  # Mistral
    ("ollama::gemma3:27b", "27B"),            # Google
    ("ollama::qwen3-coder:latest", "30B"),    # Qwen
    ("ollama::nemotron-3-nano:30b", "30B"),   # NVIDIA
    ("ollama::olmo-3:32b", "32B"),            # AI2
]

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


def build_prompt(variant: str, tool_name: str, raw_content: str) -> tuple:
    """Build prompt for a given variant. Returns (prompt, num_predict)."""

    content = raw_content[:12000]
    n_numbers = len(extract_numbers(content))

    if variant == "baseline":
        prompt = _DISTILL_PROMPT.format(tool_name=tool_name, raw_content=content)
        return prompt, NUM_PREDICT_DEFAULT

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
        return prompt, NUM_PREDICT_DEFAULT

    elif variant == "F2":
        # Dynamic word budget
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        num_predict = min(2400, max(1200, 600 + 8 * n_numbers))
        prompt = _DISTILL_PROMPT.format(tool_name=tool_name, raw_content=content)
        # Patch the word limit in the prompt
        prompt = prompt.replace("≤ 600 words", f"≤ {word_budget} words")
        prompt = prompt.replace("≤ 35 words", f"≤ 50 words")
        return prompt, num_predict

    elif variant == "F3":
        # Simplified format
        prompt = f"""You are condensing a tool observation for a multi-agent research assistant.

<tool_name>{tool_name}</tool_name>

<raw_observation>
{content}
</raw_observation>

{_SIMPLIFIED_FORMAT}"""
        return prompt, NUM_PREDICT_DEFAULT

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
        return prompt, NUM_PREDICT_DEFAULT

    elif variant == "F2_F3":
        # Dynamic budget + simplified format
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        num_predict = min(2400, max(1200, 600 + 8 * n_numbers))
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
        return prompt, num_predict

    elif variant == "F1_F2_F3":
        # All three fixes
        word_budget = min(900, max(400, 200 + 12 * n_numbers))
        num_predict = min(2400, max(1200, 600 + 8 * n_numbers))
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
        return prompt, num_predict

    else:
        raise ValueError(f"Unknown variant: {variant}")


ALL_VARIANTS = ["baseline", "F1", "F2", "F3", "F1_F3", "F2_F3", "F1_F2_F3"]


# ─────────────────────────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────────────────────────

def load_dataset() -> List[Dict]:
    """Load distiller dataset (built by V4-7)."""
    if DATASET_PATH.exists():
        logger.info(f"Loading dataset from {DATASET_PATH}")
        with open(DATASET_PATH) as f:
            return json.load(f)

    # Build from V4-4 results
    logger.info("Building distiller dataset from V4-4 results...")
    with open(V4_4_RESULTS_PATH) as f:
        v4_4 = json.load(f)
    pqr = v4_4.get("per_question_results", [])

    from exp_04_component_bench import build_distiller_dataset
    dataset = build_distiller_dataset(pqr)

    with open(DATASET_PATH, "w") as f:
        json.dump(dataset, f, indent=2)
    logger.info(f"Saved dataset: {len(dataset)} items → {DATASET_PATH}")
    return dataset


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
    """Run one distiller variant on one item."""
    prompt, num_predict = build_prompt(
        variant, item["tool_name"], item["raw_content"]
    )

    t0 = time.time()
    try:
        response = await router.chat(
            model_identifier=model_id,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0,
                "num_predict": num_predict,
                "num_ctx": NUM_CTX,
            },
            think=False,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        if not text.strip():
            return {
                "variant": variant,
                "question_id": item["question_id"],
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
            "number_retention": round(number_retention, 3),
            "source_retention": round(source_retention, 3),
            "word_count": word_count,
            "compression_ratio": round(compression_ratio, 3),
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "error": None,
        }

    except Exception as e:
        return {
            "variant": variant,
            "question_id": item["question_id"],
            "number_retention": 0,
            "source_retention": 0,
            "word_count": 0,
            "compression_ratio": 0,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "error": str(e),
        }


def _inter_path(model_short: str, variant: str) -> Path:
    """Intermediate result file for resume support."""
    return RESULTS_DIR / f"v4_7_5_inter_{model_short}_{variant}.json"


def _load_inter(model_short: str, variant: str) -> Optional[List[Dict]]:
    """Load completed intermediate results for a model+variant.

    Checks both dash-normalized and legacy colon-named files for
    backward compatibility with runs started before filename sanitization.
    """
    path = _inter_path(model_short, variant)
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return data.get("per_item", [])
    # Backward compat: scan for any file matching the variant with a similar model name
    # Handles colon↔dash mismatches (e.g., llama3:8b vs llama3-8b)
    for candidate in RESULTS_DIR.glob(f"v4_7_5_inter_*_{variant}.json"):
        # Normalize both names by removing colons and dashes for comparison
        cand_model = candidate.stem.replace(f"v4_7_5_inter_", "").replace(f"_{variant}", "")
        if cand_model.replace(":", "").replace("-", "") == model_short.replace(":", "").replace("-", ""):
            with open(candidate) as f:
                data = json.load(f)
            return data.get("per_item", [])
    return None


def _save_inter(model_short: str, variant: str, results: List[Dict]):
    """Save intermediate results after each variant completes."""
    path = _inter_path(model_short, variant)
    with open(path, "w") as f:
        json.dump({"per_item": results}, f, indent=2, default=str)


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
    port: int,
    max_items: Optional[int] = None,
):
    """Run all variants × models × items with resume support."""

    items = dataset[:max_items] if max_items else dataset

    router = ModelRouter()
    if port != 11434:
        router.base_url = f"http://localhost:{port}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = {}

    for model_id, model_size in models:
        model_short = (
            model_id.replace("ollama::", "").replace(":latest", "")
            .replace("gemini::", "").replace("gemini-3-flash-preview", "Gemini")
            .replace(":", "-")  # sanitize colons for safe filenames
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"Model: {model_short} ({model_size})")
        logger.info(f"{'='*60}")

        model_results = {}

        for variant in variants:
            # --- Resume: check for completed intermediate ---
            existing = _load_inter(model_short, variant)
            if existing and len(existing) >= len(items):
                summary = _compute_summary(existing)
                model_results[variant] = {"summary": summary, "per_item": existing}
                logger.info(f"\n  Variant: {variant} — RESUMED ({len(existing)} items cached)")
                logger.info(f"  → {variant}: num_ret={summary.get('mean_number_retention', 0):.3f} "
                            f"src_ret={summary.get('mean_source_retention', 0):.3f} "
                            f"words={summary.get('mean_word_count', 0):.0f}")
                continue

            # --- Run from scratch ---
            logger.info(f"\n  Variant: {variant} ({len(items)} items)")
            results = []
            errors = 0

            for idx, item in enumerate(items):
                result = await run_single(item, variant, router, model_id)
                results.append(result)
                if result.get("error"):
                    errors += 1

                if (idx + 1) % 10 == 0 or idx == len(items) - 1:
                    valid = [r for r in results if not r.get("error")]
                    avg_nr = statistics.mean([r["number_retention"] for r in valid]) if valid else 0
                    avg_sr = statistics.mean([r["source_retention"] for r in valid]) if valid else 0
                    logger.info(
                        f"    [{idx+1}/{len(items)}] "
                        f"num_ret={avg_nr:.3f} src_ret={avg_sr:.3f} "
                        f"errors={errors}"
                    )

            # Save intermediate for resume
            _save_inter(model_short, variant, results)

            summary = _compute_summary(results)
            model_results[variant] = {"summary": summary, "per_item": results}

            logger.info(f"  → {variant}: num_ret={summary.get('mean_number_retention', 0):.3f} "
                        f"src_ret={summary.get('mean_source_retention', 0):.3f} "
                        f"words={summary.get('mean_word_count', 0):.0f} "
                        f"lat={summary.get('mean_latency_s', 0):.1f}s")

        all_results[model_short] = model_results

    # Save final results
    output = {
        "experiment": "v4_7_5_distiller_ablation",
        "timestamp": timestamp,
        "n_items": len(items),
        "variants": variants,
        "models": [m[0] for m in models],
        "results": all_results,
    }

    out_path = RESULTS_DIR / f"v4_7_5_distiller_ablation_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"\nResults saved: {out_path}")

    # Also save as latest
    latest_path = RESULTS_DIR / "v4_7_5_distiller_ablation_latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Latest link: {latest_path}")

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
    parser = argparse.ArgumentParser(description="V4-7.5: Distiller prompt ablation")
    parser.add_argument("--variants", nargs="+", default=ALL_VARIANTS,
                        choices=ALL_VARIANTS, help="Variants to test")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Model short names (e.g. llama3:8b nemotron-3-nano:30b)")
    parser.add_argument("--port", type=int, default=11434, help="Ollama port")
    parser.add_argument("--max-items", type=int, default=None, help="Limit items for smoke test")
    args = parser.parse_args()

    # Filter models if specified
    models = MODELS
    if args.models:
        models = [
            (mid, size) for mid, size in MODELS
            if any(m in mid for m in args.models)
        ]
        if not models:
            print(f"No matching models for: {args.models}")
            print(f"Available: {[m[0] for m in MODELS]}")
            sys.exit(1)

    dataset = load_dataset()
    logger.info(f"Dataset: {len(dataset)} items")
    logger.info(f"Variants: {args.variants}")
    logger.info(f"Models: {[m[0] for m in models]}")

    n_evals = len(dataset) * len(args.variants) * len(models)
    if args.max_items:
        n_evals = args.max_items * len(args.variants) * len(models)
    logger.info(f"Total evals: {n_evals}")

    asyncio.run(run_experiment(
        dataset=dataset,
        variants=args.variants,
        models=models,
        port=args.port,
        max_items=args.max_items,
    ))


if __name__ == "__main__":
    main()
