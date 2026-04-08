#!/usr/bin/env python3
"""
V4 Flip Rate Analysis
=====================
Analyzes how self-correction strategies (verified_pass, multi_hop) change
correctness outcomes compared to single_pass baseline.

Computes:
1. Outcome transition matrix: CC, CI (harmful flip), IC (helpful flip), II
2. Flip rate = harmful / (harmful + helpful) — proportion of flips that hurt
3. Net flip rate = (harmful - helpful) / total
4. Breakdown by question category (FR, CO, TE, CD, SY, OOD)
5. McNemar's test for statistical significance of outcome changes
6. Sensitivity analysis at correctness thresholds >= 3 and >= 4
7. Comparison with Snell et al. (2025) 38% harmful revision rate

Usage:
    uv run python publication/scripts/analysis_fliprate.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import numpy as np
from scipy import stats

# Project path setup
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RESULTS_DIR = Path(__file__).resolve().parent / "results_v4"
V4_4_PATH = RESULTS_DIR / "v4_4_generation_latest.json"
OUTPUT_PATH = RESULTS_DIR / "v4_fliprate_analysis.json"

CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
CATEGORY_ABBREV = {
    "factual_recall": "FR",
    "conceptual": "CO",
    "technical": "TE",
    "cross_document": "CD",
    "synthesis": "SY",
    "out_of_domain": "OOD",
}


def load_data():
    """Load V4-4 generation results and build lookup by (question_id, config)."""
    with open(V4_4_PATH) as f:
        data = json.load(f)

    lookup = {}
    for r in data["per_question_results"]:
        key = (r["question_id"], r["config"])
        lookup[key] = r

    # Get unique question IDs with their categories
    questions = {}
    for r in data["per_question_results"]:
        if r["question_id"] not in questions:
            questions[r["question_id"]] = {
                "category": r["category"],
                "answerable": r["answerable"],
                "difficulty": r.get("difficulty"),
            }

    return lookup, questions, data


def is_correct(result, threshold=4):
    """Check if a result is correct based on judge correctness score."""
    if result is None:
        return False
    scores = result.get("judge_scores")
    if scores is None:
        return False
    return scores.get("correctness", 0) >= threshold


def compute_transitions(lookup, questions, baseline_config, test_config, threshold=4):
    """Compute the transition matrix between baseline and test config.

    Returns dict with:
        CC: correct -> correct (preserved)
        CI: correct -> incorrect (harmful flip)
        IC: incorrect -> correct (helpful flip)
        II: incorrect -> incorrect (both fail)
        by_category: same breakdown per category
        questions_detail: per-question outcomes
    """
    transitions = {"CC": 0, "CI": 0, "IC": 0, "II": 0}
    by_category = defaultdict(lambda: {"CC": 0, "CI": 0, "IC": 0, "II": 0})
    details = []

    for qid, qinfo in questions.items():
        baseline = lookup.get((qid, baseline_config))
        test = lookup.get((qid, test_config))

        if baseline is None or test is None:
            continue

        b_correct = is_correct(baseline, threshold)
        t_correct = is_correct(test, threshold)

        if b_correct and t_correct:
            outcome = "CC"
        elif b_correct and not t_correct:
            outcome = "CI"
        elif not b_correct and t_correct:
            outcome = "IC"
        else:
            outcome = "II"

        transitions[outcome] += 1
        by_category[qinfo["category"]][outcome] += 1

        b_score = baseline.get("judge_scores", {}).get("correctness", 0)
        t_score = test.get("judge_scores", {}).get("correctness", 0)

        details.append({
            "question_id": qid,
            "category": qinfo["category"],
            "outcome": outcome,
            "baseline_score": b_score,
            "test_score": t_score,
            "score_delta": t_score - b_score,
        })

    return transitions, dict(by_category), details


def compute_mcnemar(transitions):
    """McNemar's test on the off-diagonal (discordant) cells.

    Tests whether the proportion of CI (harmful) vs IC (helpful) flips
    differs significantly from chance.
    """
    b = transitions["CI"]  # harmful flips
    c = transitions["IC"]  # helpful flips

    if b + c == 0:
        return {"chi2": 0.0, "p_value": 1.0, "n_discordant": 0, "note": "no discordant pairs"}

    # McNemar's test with continuity correction
    chi2 = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0
    p_value = 1 - stats.chi2.cdf(chi2, df=1)

    # Exact binomial test (more appropriate for small samples)
    exact_p = stats.binomtest(b, b + c, 0.5).pvalue if (b + c) > 0 else 1.0

    return {
        "chi2": round(chi2, 4),
        "p_value_chi2": round(p_value, 6),
        "p_value_exact": round(exact_p, 6),
        "n_discordant": b + c,
        "harmful_flips": b,
        "helpful_flips": c,
    }


def compute_flip_metrics(transitions):
    """Compute flip rate metrics from transition counts."""
    total = sum(transitions.values())
    harmful = transitions["CI"]
    helpful = transitions["IC"]
    total_flips = harmful + helpful

    metrics = {
        "total_questions": total,
        "correct_correct": transitions["CC"],
        "correct_incorrect": transitions["CI"],
        "incorrect_correct": transitions["IC"],
        "incorrect_incorrect": transitions["II"],
        "total_flips": total_flips,
        "baseline_accuracy": round((transitions["CC"] + transitions["CI"]) / total, 4) if total > 0 else 0,
        "test_accuracy": round((transitions["CC"] + transitions["IC"]) / total, 4) if total > 0 else 0,
    }

    if total_flips > 0:
        metrics["flip_rate_harmful"] = round(harmful / total_flips, 4)
        metrics["flip_rate_helpful"] = round(helpful / total_flips, 4)
        metrics["net_flip_pct"] = round((harmful - helpful) / total * 100, 2)
    else:
        metrics["flip_rate_harmful"] = 0.0
        metrics["flip_rate_helpful"] = 0.0
        metrics["net_flip_pct"] = 0.0

    return metrics


def format_comparison(name, transitions, by_category, details, mcnemar_result):
    """Format a complete comparison result."""
    metrics = compute_flip_metrics(transitions)

    # Category breakdown
    cat_breakdown = {}
    for cat in sorted(by_category.keys()):
        cat_trans = by_category[cat]
        cat_metrics = compute_flip_metrics(cat_trans)
        cat_breakdown[cat] = {
            "abbrev": CATEGORY_ABBREV.get(cat, cat),
            **cat_metrics,
        }

    # Score delta statistics
    deltas = [d["score_delta"] for d in details]
    if deltas:
        delta_stats = {
            "mean": round(np.mean(deltas), 3),
            "median": round(float(np.median(deltas)), 1),
            "std": round(np.std(deltas), 3),
            "min": int(np.min(deltas)),
            "max": int(np.max(deltas)),
        }
    else:
        delta_stats = {}

    # Harmful flip details (most interesting for analysis)
    harmful_details = sorted(
        [d for d in details if d["outcome"] == "CI"],
        key=lambda x: x["score_delta"],
    )

    return {
        "comparison": name,
        "overall": metrics,
        "by_category": cat_breakdown,
        "mcnemar_test": mcnemar_result,
        "score_delta_stats": delta_stats,
        "harmful_flip_questions": harmful_details,
        "helpful_flip_questions": sorted(
            [d for d in details if d["outcome"] == "IC"],
            key=lambda x: -x["score_delta"],
        ),
    }


def print_comparison(comp):
    """Pretty-print a comparison result."""
    m = comp["overall"]
    name = comp["comparison"]

    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    print(f"  Total questions: {m['total_questions']}")
    print(f"  Baseline accuracy: {m['baseline_accuracy']:.1%}")
    print(f"  Test accuracy:     {m['test_accuracy']:.1%}")
    print(f"  Accuracy delta:    {m['test_accuracy'] - m['baseline_accuracy']:+.1%}")
    print()
    print(f"  Transition matrix:")
    print(f"    Correct->Correct   (CC): {m['correct_correct']:>4}")
    print(f"    Correct->Incorrect (CI): {m['correct_incorrect']:>4}  <- HARMFUL flips")
    print(f"    Incorrect->Correct (IC): {m['incorrect_correct']:>4}  <- HELPFUL flips")
    print(f"    Incorrect->Incorrect(II): {m['incorrect_incorrect']:>4}")
    print()
    print(f"  Total flips: {m['total_flips']}")
    if m["total_flips"] > 0:
        print(f"  Harmful flip rate: {m['flip_rate_harmful']:.1%} of all flips are harmful")
        print(f"  Helpful flip rate: {m['flip_rate_helpful']:.1%} of all flips are helpful")
        print(f"  Net flip impact:   {m['net_flip_pct']:+.1f}% of questions changed for the worse")

    # McNemar's
    mc = comp["mcnemar_test"]
    print(f"\n  McNemar's test:")
    print(f"    Discordant pairs: {mc['n_discordant']}")
    print(f"    Harmful: {mc['harmful_flips']}, Helpful: {mc['helpful_flips']}")
    print(f"    chi2 = {mc['chi2']:.3f}, p = {mc['p_value_chi2']:.4f} (asymptotic)")
    print(f"    Exact binomial p = {mc['p_value_exact']:.4f}")
    sig = "SIGNIFICANT" if mc["p_value_exact"] < 0.05 else "not significant"
    print(f"    -> {sig} at alpha=0.05")

    # Score delta
    ds = comp["score_delta_stats"]
    if ds:
        print(f"\n  Score delta (test - baseline):")
        print(f"    Mean: {ds['mean']:+.3f}, Median: {ds['median']:+.1f}, SD: {ds['std']:.3f}")
        print(f"    Range: [{ds['min']}, {ds['max']}]")

    # Category breakdown
    print(f"\n  By category:")
    print(f"    {'Cat':<6} {'N':>4} {'CC':>4} {'CI':>4} {'IC':>4} {'II':>4} {'Harm%':>7} {'BaseAcc':>8} {'TestAcc':>8}")
    print(f"    {'-'*55}")
    for cat, cm in sorted(comp["by_category"].items(), key=lambda x: x[0]):
        abbr = cm["abbrev"]
        n = cm["total_questions"]
        harm_rate = f"{cm['flip_rate_harmful']:.0%}" if cm["total_flips"] > 0 else "n/a"
        print(
            f"    {abbr:<6} {n:>4} {cm['correct_correct']:>4} "
            f"{cm['correct_incorrect']:>4} {cm['incorrect_correct']:>4} "
            f"{cm['incorrect_incorrect']:>4} {harm_rate:>7} "
            f"{cm['baseline_accuracy']:>7.0%} {cm['test_accuracy']:>7.0%}"
        )

    # Top harmful flips
    if comp["harmful_flip_questions"]:
        print(f"\n  Top harmful flips (score dropped most):")
        for d in comp["harmful_flip_questions"][:5]:
            print(f"    {d['question_id']:<30} {d['baseline_score']}->{d['test_score']} (delta={d['score_delta']:+d})")


def main():
    print("=" * 70)
    print("  V4 Flip Rate Analysis")
    print("  Comparing self-correction strategies vs single_pass baseline")
    print("=" * 70)

    lookup, questions, raw_data = load_data()
    print(f"\nLoaded {len(raw_data['per_question_results'])} results, {len(questions)} unique questions")

    all_results = {}

    # Main comparisons: verified_pass and multi_hop vs single_pass
    comparisons = [
        ("verified_pass vs single_pass", "single_pass", "verified_pass"),
        ("multi_hop vs single_pass", "single_pass", "multi_hop"),
        ("rlm_5 vs single_pass", "single_pass", "rlm_5"),
        ("rlm_10 vs single_pass", "single_pass", "rlm_10"),
        ("rlm_20 vs single_pass", "single_pass", "rlm_20"),
    ]

    for threshold in [4, 3]:
        threshold_key = f"threshold_{threshold}"
        all_results[threshold_key] = {}

        print(f"\n{'#'*70}")
        print(f"  THRESHOLD: correctness >= {threshold}")
        print(f"{'#'*70}")

        for name, baseline, test in comparisons:
            transitions, by_category, details = compute_transitions(
                lookup, questions, baseline, test, threshold=threshold
            )
            mcnemar_result = compute_mcnemar(transitions)
            comp = format_comparison(name, transitions, by_category, details, mcnemar_result)
            print_comparison(comp)
            all_results[threshold_key][name] = comp

    # Snell et al. comparison
    print(f"\n{'='*70}")
    print("  Comparison with Snell et al. (2025)")
    print(f"{'='*70}")

    vp = all_results["threshold_4"]["verified_pass vs single_pass"]["overall"]
    snell_rate = 0.38
    our_rate = vp["flip_rate_harmful"]
    print(f"  Snell et al. finding: beam search revises {snell_rate:.0%} of correct answers incorrectly")
    print(f"  Our verified_pass:    {our_rate:.0%} of all flips are harmful (threshold>=4)")
    if vp["total_flips"] > 0:
        # What fraction of originally-correct answers were revised incorrectly?
        baseline_correct = vp["correct_correct"] + vp["correct_incorrect"]
        if baseline_correct > 0:
            revision_rate = vp["correct_incorrect"] / baseline_correct
            print(f"  Our revision damage rate: {revision_rate:.1%} of correct answers were broken")
            print(f"    (Snell reports {snell_rate:.0%} — {'similar' if abs(revision_rate - snell_rate) < 0.10 else 'different' } magnitude)")

    # Cross-strategy comparison table
    print(f"\n{'='*70}")
    print("  Cross-Strategy Flip Summary (threshold >= 4)")
    print(f"{'='*70}")
    print(f"  {'Strategy':<30} {'Flips':>6} {'Harm':>5} {'Help':>5} {'HarmRate':>9} {'NetImpact':>10} {'p(exact)':>9}")
    print(f"  {'-'*75}")
    for name, _, _ in comparisons:
        c = all_results["threshold_4"][name]
        m = c["overall"]
        mc = c["mcnemar_test"]
        harm_r = f"{m['flip_rate_harmful']:.0%}" if m["total_flips"] > 0 else "n/a"
        sig = "*" if mc["p_value_exact"] < 0.05 else ""
        print(
            f"  {name:<30} {m['total_flips']:>6} {m['correct_incorrect']:>5} "
            f"{m['incorrect_correct']:>5} {harm_r:>9} {m['net_flip_pct']:>+9.1f}% "
            f"{mc['p_value_exact']:>8.4f}{sig}"
        )

    # Save results
    output = {
        "experiment": "v4_fliprate_analysis",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "source_file": "v4_4_generation_latest.json",
        "description": "Flip rate analysis: how self-correction strategies change correctness outcomes vs single_pass",
        "methodology": {
            "baseline": "single_pass",
            "test_configs": ["verified_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20"],
            "thresholds": [3, 4],
            "flip_rate_definition": "harmful_flips / (harmful_flips + helpful_flips)",
            "revision_damage_rate": "harmful_flips / baseline_correct_count",
            "mcnemar_test": "exact binomial on discordant pairs (CI vs IC)",
            "reference": "Snell et al. (2025) — beam search revises 38% of correct answers incorrectly",
        },
        "results": all_results,
        "n_questions": len(questions),
        "n_results": len(raw_data["per_question_results"]),
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
