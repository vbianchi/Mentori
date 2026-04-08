#!/usr/bin/env python3
"""
V4 Human Evaluation Sampler

Samples 50 answers from V4-4 results (stratified by config × category) and
exports them to a CSV for human rating. Two raters score each answer on:

  - Correctness (0-5)
  - Completeness (0-5)
  - Faithfulness (0-5)
  - Overall quality (0-5)

The CSV is anonymized (config names are masked) to prevent rater bias.

Usage:
    # Generate the CSV (runs anywhere — pure Python, no API calls)
    uv run python publication/scripts/analysis_human_eval_sampler.py

    # Custom sample size
    uv run python publication/scripts/analysis_human_eval_sampler.py --n 100

    # Include specific configs only
    uv run python publication/scripts/analysis_human_eval_sampler.py --configs single_pass rlm_10 verified_pass

    # After rating: compute inter-rater agreement
    uv run python publication/scripts/analysis_human_eval_sampler.py --analyze rated_answers.csv
"""

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from exp_common import V4_RESULTS_DIR

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

V4_4_RESULTS = V4_RESULTS_DIR / "v4_4_generation_latest.json"
OUTPUT_DIR = V4_RESULTS_DIR
SEED = 42

ALL_CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
ANSWERABLE_CATEGORIES = ["factual_recall", "conceptual", "technical", "cross_document", "synthesis"]

# Anonymization mapping (shuffled at runtime with seed)
CONFIG_CODES = {}


def _build_anonymization(configs: List[str], seed: int = SEED):
    """Create a randomized config → code mapping."""
    global CONFIG_CODES
    rng = random.Random(seed)
    codes = [f"Strategy_{chr(65+i)}" for i in range(len(configs))]
    rng.shuffle(codes)
    CONFIG_CODES = dict(zip(configs, codes))
    return CONFIG_CODES


# ─────────────────────────────────────────────────────────────
# Sampling
# ─────────────────────────────────────────────────────────────

def stratified_sample(
    results: List[Dict],
    n: int = 50,
    configs: Optional[List[str]] = None,
    seed: int = SEED,
) -> List[Dict]:
    """Stratified sample: proportional to config × category."""
    rng = random.Random(seed)
    configs = configs or ALL_CONFIGS

    # Filter to answerable + requested configs
    pool = [
        r for r in results
        if r.get("answerable", True)
        and r.get("config") in configs
        and r.get("category") in ANSWERABLE_CATEGORIES
    ]

    if not pool:
        print("ERROR: No results match the filter criteria")
        return []

    # Group by config × category
    groups = defaultdict(list)
    for r in pool:
        key = (r["config"], r["category"])
        groups[key].append(r)

    # Calculate proportional allocation
    total_pool = len(pool)
    sampled = []
    remaining = n

    # Sort groups for deterministic ordering
    sorted_keys = sorted(groups.keys())

    for key in sorted_keys:
        group = groups[key]
        # Proportional allocation (at least 1 per group if possible)
        alloc = max(1, round(len(group) / total_pool * n))
        alloc = min(alloc, remaining, len(group))
        if alloc > 0:
            sampled.extend(rng.sample(group, alloc))
            remaining -= alloc
        if remaining <= 0:
            break

    # If we still have budget, fill from largest groups
    if remaining > 0:
        used_ids = {r["question_id"] + "|" + r["config"] for r in sampled}
        extras = [r for r in pool if r["question_id"] + "|" + r["config"] not in used_ids]
        rng.shuffle(extras)
        sampled.extend(extras[:remaining])

    # Final shuffle
    rng.shuffle(sampled)
    return sampled[:n]


# ─────────────────────────────────────────────────────────────
# Export to CSV
# ─────────────────────────────────────────────────────────────

def export_csv(sampled: List[Dict], output_path: Path, anonymize: bool = True):
    """Export sampled answers to a CSV for human rating."""
    configs_used = list({r["config"] for r in sampled})
    code_map = _build_anonymization(configs_used) if anonymize else {c: c for c in configs_used}

    # Also save the key (for later de-anonymization)
    key_path = output_path.with_suffix(".key.json")
    key_data = {
        "anonymization": {v: k for k, v in code_map.items()},
        "seed": SEED,
        "n_sampled": len(sampled),
        "timestamp": datetime.now().isoformat(),
    }
    with open(key_path, "w") as f:
        json.dump(key_data, f, indent=2)

    headers = [
        "eval_id",
        "strategy",  # anonymized
        "category",
        "question",
        "generated_answer",
        "expected_answer",
        "expected_concepts",
        # Rater 1
        "r1_correctness",
        "r1_completeness",
        "r1_faithfulness",
        "r1_overall",
        "r1_notes",
        # Rater 2
        "r2_correctness",
        "r2_completeness",
        "r2_faithfulness",
        "r2_overall",
        "r2_notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for i, r in enumerate(sampled, 1):
            concepts = r.get("expected_concepts", [])
            if isinstance(concepts, list):
                concepts = "; ".join(concepts)

            answer = r.get("generated_answer", "")
            # Truncate very long answers for readability
            if len(answer) > 3000:
                answer = answer[:3000] + "\n[... truncated for review ...]"

            writer.writerow([
                f"E{i:03d}",
                code_map.get(r["config"], r["config"]),
                r.get("category", "unknown"),
                r.get("question", ""),
                answer,
                r.get("expected_answer", ""),
                concepts,
                "", "", "", "", "",  # Rater 1 columns
                "", "", "", "", "",  # Rater 2 columns
            ])

    print(f"Exported {len(sampled)} answers to {output_path}")
    print(f"Anonymization key saved to {key_path}")
    return output_path


# ─────────────────────────────────────────────────────────────
# Post-rating analysis
# ─────────────────────────────────────────────────────────────

def analyze_ratings(csv_path: Path):
    """Compute inter-rater agreement from completed CSV."""
    import statistics

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Load de-anonymization key
    key_path = csv_path.with_suffix("").with_suffix(".key.json")
    code_map = {}
    if key_path.exists():
        with open(key_path) as f:
            key_data = json.load(f)
            code_map = key_data.get("anonymization", {})

    dimensions = ["correctness", "completeness", "faithfulness", "overall"]
    r1_scores = {d: [] for d in dimensions}
    r2_scores = {d: [] for d in dimensions}
    agreements = {d: [] for d in dimensions}

    for row in rows:
        for dim in dimensions:
            r1_val = row.get(f"r1_{dim}", "").strip()
            r2_val = row.get(f"r2_{dim}", "").strip()
            if r1_val and r2_val:
                try:
                    r1 = int(r1_val)
                    r2 = int(r2_val)
                    r1_scores[dim].append(r1)
                    r2_scores[dim].append(r2)
                    agreements[dim].append(abs(r1 - r2) <= 1)  # Within ±1
                except ValueError:
                    pass

    print("\n=== Inter-Rater Agreement Analysis ===\n")
    for dim in dimensions:
        if not r1_scores[dim]:
            print(f"  {dim}: No ratings found")
            continue
        n = len(r1_scores[dim])
        r1_mean = statistics.mean(r1_scores[dim])
        r2_mean = statistics.mean(r2_scores[dim])
        agree_pct = sum(agreements[dim]) / n * 100

        # Spearman correlation
        try:
            from scipy.stats import spearmanr
            rho, p = spearmanr(r1_scores[dim], r2_scores[dim])
            corr_str = f"ρ={rho:.3f} (p={p:.4f})"
        except ImportError:
            corr_str = "(install scipy for correlation)"

        print(f"  {dim}:")
        print(f"    N rated: {n}")
        print(f"    R1 mean: {r1_mean:.2f}, R2 mean: {r2_mean:.2f}")
        print(f"    Agreement (±1): {agree_pct:.1f}%")
        print(f"    Spearman: {corr_str}")

    # De-anonymize and show per-strategy means
    if code_map:
        print("\n=== Per-Strategy Means (de-anonymized) ===\n")
        strategy_scores = defaultdict(lambda: defaultdict(list))
        for row in rows:
            strategy_code = row.get("strategy", "")
            real_name = code_map.get(strategy_code, strategy_code)
            for dim in dimensions:
                for prefix in ["r1", "r2"]:
                    val = row.get(f"{prefix}_{dim}", "").strip()
                    if val:
                        try:
                            strategy_scores[real_name][dim].append(int(val))
                        except ValueError:
                            pass

        for strategy in sorted(strategy_scores.keys()):
            scores = strategy_scores[strategy]
            parts = [f"{dim}: {statistics.mean(v):.2f}" for dim, v in scores.items() if v]
            print(f"  {strategy}: {', '.join(parts)}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4 Human Evaluation Sampler")
    parser.add_argument("--n", type=int, default=50, help="Number of answers to sample")
    parser.add_argument("--configs", nargs="+", choices=ALL_CONFIGS, help="Configs to include")
    parser.add_argument("--no-anonymize", action="store_true", help="Don't anonymize config names")
    parser.add_argument("--analyze", type=str, help="Analyze a completed rating CSV")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    args = parser.parse_args()

    if args.analyze:
        analyze_ratings(Path(args.analyze))
        return

    # Load V4-4 results
    if not V4_4_RESULTS.exists():
        print(f"ERROR: V4-4 results not found at {V4_4_RESULTS}")
        sys.exit(1)

    with open(V4_4_RESULTS) as f:
        data = json.load(f)

    results = data.get("per_question_results", data.get("results", []))
    print(f"Loaded {len(results)} results from V4-4")

    # Load ground truth to get expected_answer and expected_concepts
    gt_path = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"
    gt_lookup = {}
    if gt_path.exists():
        with open(gt_path) as f:
            gt_data = json.load(f)
        for q in gt_data.get("questions", []):
            gt_lookup[q["id"]] = q
        print(f"Loaded {len(gt_lookup)} ground truth questions")

    # Enrich results with generated_answer (from generation.answer) and GT fields
    for r in results:
        # Generated answer lives inside generation dict
        if not r.get("generated_answer"):
            gen = r.get("generation", {})
            r["generated_answer"] = gen.get("answer", "") if isinstance(gen, dict) else ""
        # Expected answer/concepts come from ground truth
        qid = r.get("question_id", "")
        gt = gt_lookup.get(qid, {})
        if not r.get("expected_answer"):
            r["expected_answer"] = gt.get("expected_answer", "")
        if not r.get("expected_concepts"):
            r["expected_concepts"] = gt.get("expected_concepts", [])

    # Sample
    sampled = stratified_sample(results, n=args.n, configs=args.configs, seed=args.seed)
    print(f"Sampled {len(sampled)} answers (stratified by config × category)")

    # Show distribution
    from collections import Counter
    config_dist = Counter(r["config"] for r in sampled)
    cat_dist = Counter(r["category"] for r in sampled)
    print(f"  By config: {dict(config_dist)}")
    print(f"  By category: {dict(cat_dist)}")

    # Export
    timestamp = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"v4_human_eval_{timestamp}.csv"
    export_csv(sampled, output_path, anonymize=not args.no_anonymize)


if __name__ == "__main__":
    main()
