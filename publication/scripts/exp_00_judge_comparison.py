#!/usr/bin/env python3
"""
V4-0 Phase 3: Judge Model Evaluation

Reads Phase 2 answers (90 raw answers from 6 generation models × 15 questions),
scores them with multiple candidate judge models, and compares judge agreement
against a strong reference judge.

Usage:
  # Run all candidate judges against Phase 2 answers
  %(prog)s

  # Use specific reference judge
  %(prog)s --reference "gemini::gemini-3-flash-preview"

  # Only run specific candidate judges
  %(prog)s --judges "ollama::gemma3:27b" "ollama::qwen3-coder:latest"

  # Resume from intermediate results
  %(prog)s --resume
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ── Project path setup ──
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from exp_common import (
    JUDGE_MODEL,
    judge_answer,
    load_ground_truth,
    save_intermediate,
    load_intermediate,
    find_admin_user_id,
    configure_gemini_from_admin,
    V4_GROUND_TRUTH,
    V4_RESULTS_DIR,
    save_v4_results,
    save_v4_markdown,
)

logger = logging.getLogger("exp_00_judge_comparison")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

# ── Constants ──

PHASE2_FILE = V4_RESULTS_DIR / "v4_0_phase2_latest.json"
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_0_judge_intermediate.json"

# Reference judge: strong model used as ground-truth baseline
DEFAULT_REFERENCE = "gemini::gemini-3-flash-preview"

# Candidate local judges to evaluate
DEFAULT_CANDIDATES = [
    "ollama::gpt-oss:20b",          # current default judge
    "ollama::gpt-oss:120b",         # larger variant
    "ollama::gemma3:27b",           # strong in Phase 2
    "ollama::qwen3-coder:latest",   # fastest model
    "ollama::nemotron-3-nano:30b",  # high-citation model
]

SCORE_DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]


# ── Helpers ──

def load_phase2_answers(path: Path) -> List[Dict[str, Any]]:
    """Load Phase 2 merged results."""
    data = json.load(open(path))
    results = data["per_question_results"]
    # Filter to completed answers only
    valid = [r for r in results if r.get("completed") and r.get("final_answer")]
    logger.info(f"Loaded {len(valid)} valid answers from {len(results)} total ({path.name})")
    return valid


def build_gt_lookup(gt_path: Path) -> Dict[str, Dict]:
    """Build question ID → ground truth lookup."""
    questions = load_ground_truth(gt_path, answerable_only=False)
    return {q["id"]: q for q in questions}


def parse_think_from_model(model_id: str):
    """Parse think parameter from model identifier.

    Examples:
        "ollama::gpt-oss:20b" -> ("ollama::gpt-oss:20b", False)
        "ollama::gpt-oss:20b[think:high]" -> ("ollama::gpt-oss:20b", "high")
        "ollama::qwen3-coder:latest[think:true]" -> ("ollama::qwen3-coder:latest", True)
        "gemini::gemini-3-flash-preview" -> ("gemini::gemini-3-flash-preview", None)  # use default
    """
    import re
    match = re.search(r'\[think:(\w+)\]', model_id)
    if match:
        clean = re.sub(r'\[think:\w+\]', '', model_id)
        val = match.group(1)
        if val == "true":
            return clean, True
        elif val == "false":
            return clean, False
        else:
            return clean, val  # "low", "medium", "high"
    # Default: gemini uses its default (None), ollama models get False
    if model_id.startswith("gemini::"):
        return model_id, None
    return model_id, False


async def score_answer_with_judge(
    answer: Dict[str, Any],
    gt: Dict[str, Any],
    judge_model: str,
    router,
) -> Dict[str, Any]:
    """Score a single answer with a specific judge model.

    judge_model can include [think:...] suffix, e.g.:
        "ollama::gpt-oss:20b[think:high]"
        "ollama::qwen3-coder:latest[think:true]"
    """
    clean_model, use_think = parse_think_from_model(judge_model)
    scores = await judge_answer(
        question=answer["question"],
        expected=gt.get("expected_answer", ""),
        concepts=gt.get("expected_concepts", []),
        generated=answer["final_answer"],
        router=router,
        answerable=answer.get("answerable", True),
        judge_model=clean_model,
        think=use_think,
    )
    return scores


def compute_agreement_metrics(
    ref_scores: List[Dict],
    cand_scores: List[Dict],
) -> Dict[str, Any]:
    """Compute agreement metrics between reference and candidate judge."""
    metrics = {}

    for dim in SCORE_DIMS:
        ref_vals = [s.get(dim, 0) for s in ref_scores]
        cand_vals = [s.get(dim, 0) for s in cand_scores]

        ref_arr = np.array(ref_vals, dtype=float)
        cand_arr = np.array(cand_vals, dtype=float)

        # Mean absolute error
        mae = float(np.mean(np.abs(ref_arr - cand_arr)))

        # Pearson correlation
        if np.std(ref_arr) > 0 and np.std(cand_arr) > 0:
            pearson = float(np.corrcoef(ref_arr, cand_arr)[0, 1])
        else:
            pearson = 0.0

        # Spearman rank correlation
        from scipy.stats import spearmanr
        if len(set(ref_vals)) > 1 and len(set(cand_vals)) > 1:
            spearman, sp_pval = spearmanr(ref_arr, cand_arr)
            spearman = float(spearman)
        else:
            spearman = 0.0

        # Exact agreement rate
        exact = float(np.mean(ref_arr == cand_arr))

        # Pass/fail agreement (correctness >= 3 = pass)
        if dim == "correctness":
            ref_pass = ref_arr >= 3
            cand_pass = cand_arr >= 3
            pass_agree = float(np.mean(ref_pass == cand_pass))
            metrics["pass_fail_agreement"] = round(pass_agree, 3)

        metrics[f"{dim}_mae"] = round(mae, 3)
        metrics[f"{dim}_pearson"] = round(pearson, 3)
        metrics[f"{dim}_spearman"] = round(spearman, 3)
        metrics[f"{dim}_exact_agree"] = round(exact, 3)

    # Composite score (average MAE across dimensions, lower is better)
    avg_mae = np.mean([metrics[f"{d}_mae"] for d in SCORE_DIMS])
    avg_pearson = np.mean([metrics[f"{d}_pearson"] for d in SCORE_DIMS])
    metrics["avg_mae"] = round(float(avg_mae), 3)
    metrics["avg_pearson"] = round(float(avg_pearson), 3)

    return metrics


def generate_report(
    reference_model: str,
    candidate_results: Dict[str, Dict],
    n_answers: int,
) -> str:
    """Generate markdown report comparing judge models."""
    lines = [
        "# V4-0 Phase 3: Judge Model Evaluation",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Reference judge**: `{reference_model}`",
        f"**Answers scored**: {n_answers}",
        f"**Candidates**: {len(candidate_results)}",
        "",
        "## Summary",
        "",
        "| Judge Model | Avg MAE | Avg Pearson | Pass/Fail Agree | Correctness MAE | Best Dim |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]

    # Sort by avg_mae (lower is better)
    ranked = sorted(candidate_results.items(), key=lambda x: x[1]["metrics"]["avg_mae"])

    for judge_model, data in ranked:
        m = data["metrics"]
        # Find best dimension (lowest MAE)
        best_dim = min(SCORE_DIMS, key=lambda d: m[f"{d}_mae"])
        lines.append(
            f"| `{judge_model}` | {m['avg_mae']:.3f} | {m['avg_pearson']:.3f} | "
            f"{m.get('pass_fail_agreement', '-'):.1%} | {m['correctness_mae']:.3f} | {best_dim} |"
        )

    lines.extend(["", "## Per-Dimension Detail", ""])

    for judge_model, data in ranked:
        m = data["metrics"]
        lines.append(f"### `{judge_model}`")
        lines.append("")
        lines.append("| Dimension | MAE | Pearson | Spearman | Exact Agree |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for dim in SCORE_DIMS:
            lines.append(
                f"| {dim} | {m[f'{dim}_mae']:.3f} | {m[f'{dim}_pearson']:.3f} | "
                f"{m[f'{dim}_spearman']:.3f} | {m[f'{dim}_exact_agree']:.1%} |"
            )
        lines.append("")

    # Score distributions
    lines.extend(["## Score Distributions", ""])
    lines.append(f"### Reference: `{reference_model}`")
    lines.append("")
    lines.append("| Dimension | Mean | Std | Min | Max |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")

    # Use first candidate's ref_scores (they're all the same)
    if ranked:
        first_data = ranked[0][1]
        ref_scores = first_data.get("ref_scores", [])
        if ref_scores:
            for dim in SCORE_DIMS:
                vals = [s.get(dim, 0) for s in ref_scores]
                arr = np.array(vals, dtype=float)
                lines.append(
                    f"| {dim} | {np.mean(arr):.2f} | {np.std(arr):.2f} | "
                    f"{np.min(arr):.0f} | {np.max(arr):.0f} |"
                )
    lines.append("")

    # Winner
    if ranked:
        winner = ranked[0][0]
        lines.extend([
            "## Recommendation",
            "",
            f"**Best judge**: `{winner}` (lowest average MAE: {ranked[0][1]['metrics']['avg_mae']:.3f})",
            "",
        ])

    return "\n".join(lines)


# ── Main experiment ──

async def run_judge_comparison(
    phase2_file: Path = PHASE2_FILE,
    reference_model: str = DEFAULT_REFERENCE,
    candidate_models: Optional[List[str]] = None,
    resume: bool = False,
    run_id: Optional[str] = None,
):
    """Run judge model comparison experiment."""
    from backend.agents.model_router import ModelRouter

    if candidate_models is None:
        candidate_models = DEFAULT_CANDIDATES

    intermediate_file = (
        V4_RESULTS_DIR / f"v4_0_judge_intermediate_{run_id}.json"
        if run_id else INTERMEDIATE_FILE
    )

    # Load Phase 2 answers
    answers = load_phase2_answers(phase2_file)
    if not answers:
        logger.error("No valid Phase 2 answers found")
        sys.exit(1)

    # Load ground truth for expected answers
    gt_lookup = build_gt_lookup(V4_GROUND_TRUTH)

    # Filter answers to those with GT entries
    valid_answers = []
    for a in answers:
        qid = a["question_id"]
        if qid in gt_lookup:
            valid_answers.append(a)
        else:
            logger.warning(f"No GT entry for {qid}, skipping")
    answers = valid_answers
    logger.info(f"Scoring {len(answers)} answers with {len(candidate_models) + 1} judge models")

    configure_gemini_from_admin()
    router = ModelRouter()

    # Resume support
    if resume and intermediate_file.exists():
        intermediate = load_intermediate(intermediate_file)
    else:
        intermediate = {"ref_scores": {}, "cand_scores": {}, "completed_keys": []}

    completed = set(intermediate.get("completed_keys", []))

    # All judges to run (reference + candidates)
    all_judges = [reference_model] + candidate_models

    total = len(all_judges) * len(answers)
    done = 0

    for judge_model in all_judges:
        is_ref = judge_model == reference_model
        label = "REF" if is_ref else "CAND"
        score_bucket = "ref_scores" if is_ref else "cand_scores"

        if score_bucket not in intermediate:
            intermediate[score_bucket] = {}

        if not is_ref and judge_model not in intermediate[score_bucket]:
            intermediate[score_bucket][judge_model] = {}

        logger.info(f"\n{'='*60}")
        logger.info(f"[{label}] JUDGE: {judge_model}")
        logger.info(f"{'='*60}")

        for a in answers:
            qid = a["question_id"]
            gen_model = a["model"]
            key = f"{judge_model}|{gen_model}|{qid}"

            if key in completed:
                done += 1
                continue

            done += 1
            gt = gt_lookup[qid]
            logger.info(f"  [{done}/{total}] {label} {judge_model} scoring {gen_model} | {qid}")

            try:
                scores = await score_answer_with_judge(a, gt, judge_model, router)
                corr = scores.get("correctness", "?")
                logger.info(f"    -> correctness={corr}")
            except Exception as e:
                logger.error(f"    -> ERROR: {e}")
                scores = {dim: 0 for dim in SCORE_DIMS}
                scores["justification"] = f"Error: {e}"

            # Store result keyed by "gen_model|qid"
            result_key = f"{gen_model}|{qid}"
            if is_ref:
                intermediate[score_bucket][result_key] = scores
            else:
                intermediate[score_bucket][judge_model][result_key] = scores

            completed.add(key)
            intermediate["completed_keys"] = list(completed)

            save_intermediate(intermediate, intermediate_file)

    # ── Compute metrics ──
    logger.info("\nComputing agreement metrics...")

    ref_scores_dict = intermediate["ref_scores"]
    candidate_results = {}

    for cand_model in candidate_models:
        cand_scores_dict = intermediate["cand_scores"].get(cand_model, {})

        # Align scores by key
        common_keys = sorted(set(ref_scores_dict.keys()) & set(cand_scores_dict.keys()))
        if not common_keys:
            logger.warning(f"No common scored answers for {cand_model}")
            continue

        ref_list = [ref_scores_dict[k] for k in common_keys]
        cand_list = [cand_scores_dict[k] for k in common_keys]

        metrics = compute_agreement_metrics(ref_list, cand_list)

        candidate_results[cand_model] = {
            "metrics": metrics,
            "n_scored": len(common_keys),
            "ref_scores": ref_list,
            "cand_scores": cand_list,
        }

        logger.info(
            f"  {cand_model}: MAE={metrics['avg_mae']:.3f}, "
            f"Pearson={metrics['avg_pearson']:.3f}, "
            f"Pass/Fail={metrics.get('pass_fail_agreement', 0):.1%}"
        )

    # ── Generate report ──
    report = generate_report(reference_model, candidate_results, len(answers))

    # ── Save results ──
    output_data = {
        "experiment": "v4_0_judge_comparison",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "reference_model": reference_model,
        "candidate_models": candidate_models,
        "n_answers": len(answers),
        "candidate_metrics": {
            model: {
                "metrics": data["metrics"],
                "n_scored": data["n_scored"],
            }
            for model, data in candidate_results.items()
        },
        "all_scores": {
            "reference": intermediate["ref_scores"],
            "candidates": intermediate["cand_scores"],
        },
    }

    json_path, _ = save_v4_results(output_data, "v4_0_judge")
    md_path = save_v4_markdown(report, "v4_0_judge")

    print(f"\n{'='*70}")
    print("V4-0 Phase 3 COMPLETE: Judge Model Evaluation")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(report[:4000])

    # Cleanup intermediate
    if intermediate_file.exists():
        intermediate_file.unlink()
        logger.info("Cleaned up intermediate file")


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(
        description="V4-0 Phase 3: Judge Model Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--phase2-file", type=Path, default=PHASE2_FILE,
        help=f"Phase 2 merged results file (default: {PHASE2_FILE.name})",
    )
    parser.add_argument(
        "--reference", default=DEFAULT_REFERENCE,
        help=f"Reference judge model (default: {DEFAULT_REFERENCE})",
    )
    parser.add_argument(
        "--judges", nargs="+", default=None,
        help="Candidate judge models (default: 5 preset candidates)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate results",
    )
    parser.add_argument(
        "--run-id", default=None,
        help="Run ID for parallel execution (namespaces intermediate file)",
    )

    args = parser.parse_args()

    asyncio.run(run_judge_comparison(
        phase2_file=args.phase2_file,
        reference_model=args.reference,
        candidate_models=args.judges,
        resume=args.resume,
        run_id=args.run_id,
    ))


if __name__ == "__main__":
    main()
