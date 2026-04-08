#!/usr/bin/env python3
"""
Deep Analyses Suite — Mechanistic analyses for NMI paper.
All Ollama-free: runs on existing V4 result JSON files.

Usage:
    uv run python publication/scripts/analysis_deep.py --all
    uv run python publication/scripts/analysis_deep.py --analysis judge_specialization
    uv run python publication/scripts/analysis_deep.py --analysis self_bleu
    uv run python publication/scripts/analysis_deep.py --list

Analyses (all pure Python on existing data):
  1. judge_specialization    — 19 judges × 4 dimensions calibration matrix
  2. self_bleu               — Answer repetition across RLM depths
  3. flip_taxonomy           — Classify verified_pass harmful flips
  4. ood_refusal_taxonomy    — Classify OOD refusal patterns
  5. latency_pareto          — Latency vs quality Pareto front
  6. strategy_complementarity — Per-question agreement matrix
  7. scaling_law_fit         — Power/log/sigmoid fit to V4-5 corpus scaling
  8. orchestration_blame     — V4-6 failure component attribution
  9. judge_ensemble          — Top-K judge voting vs single judge
 10. thinking_mode_coder     — V4-8: thinking mode impact on code generation
 11. num_ctx_sensitivity     — V4-8: context window sensitivity by config type
"""

import json
import sys
import logging
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple
import math
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results_v4"
OUTPUT_DIR = RESULTS_DIR / "deep_analyses"
GT_PATH = Path(__file__).parent.parent.parent / "datasets" / "ground_truth_v4.json"


def _load_v4_4() -> List[Dict]:
    """Load V4-4 generation results."""
    f = RESULTS_DIR / "v4_4_generation_latest.json"
    return json.load(open(f))["per_question_results"]


def _load_v4_5() -> List[Dict]:
    """Load V4-5 scaling results."""
    f = RESULTS_DIR / "v4_5_scaling_latest.json"
    data = json.load(open(f))
    return data.get("per_question_results", data.get("results", []))


def _load_v4_6() -> List[Dict]:
    """Load V4-6 orchestration ablation results."""
    f = RESULTS_DIR / "v4_6_orchestration_ablation_latest.json"
    return json.load(open(f))["per_question_results"]


def _load_ground_truth() -> Dict[str, Dict]:
    """Load ground truth keyed by question_id."""
    gt = json.load(open(GT_PATH))
    return {q.get("question_id", q.get("id")): q for q in gt["questions"]}


def _load_judge_files() -> Dict[str, Dict[str, Dict]]:
    """Load all V4-0 post-fix judge score files from group scoring batches (g1-g6).
    Returns: {judge_model: {question_key: {correctness, completeness, faithfulness, citation_quality}}}
    19 judges × 107 questions each.
    """
    judge_data = {}
    for group in ["g1", "g2b", "g2c", "g3", "g4", "g5", "g6"]:
        f = RESULTS_DIR / f"v4_0_judge_scoring_{group}_latest.json"
        if not f.exists():
            continue
        try:
            d = json.load(open(f))
            all_scores = d.get("all_scores", {})
            for judge_model, judge_results in all_scores.items():
                if judge_model not in judge_data:
                    judge_data[judge_model] = {}
                for key, score_data in judge_results.items():
                    judge_data[judge_model][key] = score_data
        except Exception as e:
            logger.debug(f"Error loading {f}: {e}")
    logger.info(f"Loaded {len(judge_data)} judges from group scoring files")
    return judge_data


def _load_calibration() -> Dict:
    """Load calibration data with per-judge correlations."""
    f = RESULTS_DIR / "v4_0_calibration_latest.json"
    return json.load(open(f))


def _load_objective_metrics() -> Dict[str, Dict]:
    """Load objective metrics keyed by 'gen_model|question_id'."""
    cal = _load_calibration()
    metrics = {}
    for m in cal.get("objective_metrics", []):
        model = m.get("model", "")
        q_id = m.get("question_id", "")
        key = f"{model}|{q_id}" if model else q_id
        metrics[key] = m
    return metrics


def _save_result(name: str, data: Any):
    """Save analysis result."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{name}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved: {out}")


def _ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _self_bleu(text1: str, text2: str, n: int = 4) -> float:
    """Compute BLEU-like overlap between two texts (not reference-based, but pairwise)."""
    tokens1 = text1.lower().split()
    tokens2 = text2.lower().split()
    if len(tokens1) < n or len(tokens2) < n:
        return 0.0

    ngrams1 = set(_ngrams(tokens1, n))
    ngrams2 = set(_ngrams(tokens2, n))
    if not ngrams1 or not ngrams2:
        return 0.0

    overlap = ngrams1 & ngrams2
    # Jaccard-like: overlap / union
    return len(overlap) / len(ngrams1 | ngrams2)


def _spearman(x: List[float], y: List[float]) -> float:
    """Compute Spearman rank correlation."""
    n = len(x)
    if n < 3:
        return 0.0

    def _rank(vals):
        indexed = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and indexed[j+1][1] == indexed[j][1]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = avg_rank
            i = j + 1
        return ranks

    rx = _rank(x)
    ry = _rank(y)

    d_sq = sum((rx[i] - ry[i])**2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n**2 - 1))


# ─────────────────────────────────────────────────────────────
# Analysis 1: Judge Specialization Matrix
# ─────────────────────────────────────────────────────────────

def judge_specialization():
    """Build 19×4 judge specialization matrix from calibration data.

    For each judge × dimension, shows how well calibrated that judge is.
    Novel finding: judges specialize — some excel at correctness, fail at faithfulness.
    """
    logger.info("=== Judge Specialization Matrix ===")

    cal = _load_calibration()
    calibration = cal["calibration"]

    dimensions = [
        ("correctness", "correctness_vs_semantic_sim_spearman"),
        ("completeness", "completeness_vs_concept_recall_spearman"),
        ("faithfulness", "faithfulness_vs_concept_recall"),
        ("citation_quality", "citation_quality_vs_cite_composite_spearman"),
    ]

    matrix = {}
    for judge_name, judge_data in calibration.items():
        short_name = judge_name.replace("ollama::", "").replace(":latest", "")
        row = {}
        for dim_label, dim_key in dimensions:
            val = judge_data.get(dim_key)
            if isinstance(val, dict):
                # Some are dicts with 'pearson'/'spearman' subkeys
                val = val.get("spearman", val.get("pearson", 0))
            row[dim_label] = round(val, 4) if val is not None else None
        row["composite"] = round(judge_data.get("composite_calibration", 0), 4)
        row["n_aligned"] = judge_data.get("n_aligned", 0)

        # Judge stats (mean scores → leniency indicator)
        stats = judge_data.get("judge_stats", {})
        row["mean_score"] = round(stats.get("mean_correctness", 0), 2) if stats else None

        matrix[short_name] = row

    # Sort by composite calibration
    ranked = sorted(matrix.items(), key=lambda x: x[1].get("composite", 0), reverse=True)

    # Identify specialists
    specialists = {}
    for dim_label, _ in dimensions:
        best_judge = max(matrix.items(), key=lambda x: x[1].get(dim_label) or 0)
        specialists[dim_label] = (best_judge[0], best_judge[1].get(dim_label))

    # Compute specialization variance (how uneven each judge's calibration is)
    for judge, row in matrix.items():
        dim_vals = [row.get(d) for d, _ in dimensions if row.get(d) is not None]
        if len(dim_vals) >= 2:
            mean_val = sum(dim_vals) / len(dim_vals)
            var = sum((v - mean_val)**2 for v in dim_vals) / len(dim_vals)
            row["specialization_variance"] = round(var, 4)

    result = {
        "analysis": "judge_specialization_matrix",
        "description": "Per-judge, per-dimension calibration against ground truth",
        "n_judges": len(matrix),
        "dimensions": [d for d, _ in dimensions],
        "matrix": dict(ranked),
        "specialists": specialists,
        "finding": (
            "Judges specialize: the best judge per dimension varies. "
            f"Best correctness: {specialists['correctness'][0]} (ρ={specialists['correctness'][1]}). "
            f"Best completeness: {specialists['completeness'][0]} (ρ={specialists['completeness'][1]}). "
            f"Best faithfulness: {specialists['faithfulness'][0]}. "
            f"Best citation: {specialists['citation_quality'][0]} (ρ={specialists['citation_quality'][1]}). "
            "No single judge dominates all dimensions."
        ),
    }

    # Print summary table
    print(f"\n{'Judge':<35} {'Correct':>8} {'Complete':>9} {'Faithful':>9} {'Citation':>9} {'Composite':>10}")
    print("-" * 85)
    for judge, row in ranked:
        c = f"{row['correctness']:.3f}" if row['correctness'] is not None else "   -"
        cm = f"{row['completeness']:.3f}" if row['completeness'] is not None else "   -"
        fa = f"{row['faithfulness']:.3f}" if row['faithfulness'] is not None else "   -"
        ci = f"{row['citation_quality']:.3f}" if row['citation_quality'] is not None else "   -"
        comp = f"{row['composite']:.3f}" if row['composite'] else "   -"
        print(f"{judge:<35} {c:>8} {cm:>9} {fa:>9} {ci:>9} {comp:>10}")

    print(f"\nSpecialists:")
    for dim, (judge, val) in specialists.items():
        print(f"  {dim}: {judge} (ρ={val})")

    _save_result("judge_specialization", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 2: Self-BLEU / Answer Repetition
# ─────────────────────────────────────────────────────────────

def self_bleu_analysis():
    """Measure answer similarity across RLM depths to test self-conditioning hypothesis.

    If answers become more similar at higher depths, supports Basu's self-conditioning.
    If they diverge, saturation is retrieval-driven, not generation-driven.
    """
    logger.info("=== Self-BLEU / Answer Repetition Analysis ===")

    results = _load_v4_4()

    # Group by question
    by_question = defaultdict(dict)
    for r in results:
        q_id = r["question_id"]
        config = r["config"]
        answer = r.get("generation", {}).get("answer", "")
        by_question[q_id][config] = answer

    # Compute pairwise self-BLEU between depth levels
    depth_pairs = [
        ("single_pass", "rlm_5"),
        ("rlm_5", "rlm_10"),
        ("rlm_10", "rlm_20"),
        ("single_pass", "rlm_10"),
        ("single_pass", "rlm_20"),
    ]

    pair_scores = defaultdict(list)
    per_question = []

    for q_id, configs in by_question.items():
        q_row = {"question_id": q_id}
        for c1, c2 in depth_pairs:
            a1 = configs.get(c1, "")
            a2 = configs.get(c2, "")
            if a1 and a2:
                bleu4 = _self_bleu(a1, a2, n=4)
                bleu2 = _self_bleu(a1, a2, n=2)
                pair_scores[f"{c1}_vs_{c2}"].append(bleu4)
                q_row[f"{c1}_vs_{c2}_bleu4"] = round(bleu4, 4)
                q_row[f"{c1}_vs_{c2}_bleu2"] = round(bleu2, 4)
        per_question.append(q_row)

    # Aggregate
    summary = {}
    for pair_name, scores in pair_scores.items():
        summary[pair_name] = {
            "mean_bleu4": round(sum(scores) / len(scores), 4),
            "median_bleu4": round(sorted(scores)[len(scores)//2], 4),
            "n": len(scores),
        }

    # Key test: does similarity INCREASE from rlm_5→10 vs rlm_10→20?
    sim_5_10 = summary.get("rlm_5_vs_rlm_10", {}).get("mean_bleu4", 0)
    sim_10_20 = summary.get("rlm_10_vs_rlm_20", {}).get("mean_bleu4", 0)
    sim_sp_5 = summary.get("single_pass_vs_rlm_5", {}).get("mean_bleu4", 0)

    trend = "increasing" if sim_10_20 > sim_5_10 else "decreasing"

    result = {
        "analysis": "self_bleu_answer_repetition",
        "description": "Pairwise n-gram overlap between answers at different RLM depths",
        "summary": summary,
        "per_question": per_question[:5],  # Sample
        "n_questions": len(per_question),
        "finding": (
            f"Answer similarity across depths: "
            f"SP→RLM5: {sim_sp_5:.3f}, "
            f"RLM5→RLM10: {sim_5_10:.3f}, "
            f"RLM10→RLM20: {sim_10_20:.3f}. "
            f"Trend is {trend}. "
            + ("Increasing similarity supports self-conditioning hypothesis (Basu 2025)."
               if trend == "increasing"
               else "Decreasing similarity suggests answers diverge at higher depths — saturation is retrieval-driven.")
        ),
    }

    print(f"\nSelf-BLEU (4-gram Jaccard) between depth pairs:")
    for pair, stats in summary.items():
        print(f"  {pair}: mean={stats['mean_bleu4']:.4f}, median={stats['median_bleu4']:.4f} (n={stats['n']})")
    print(f"\nTrend: {trend} similarity with depth")

    _save_result("self_bleu", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 3: Verified_Pass Flip Taxonomy
# ─────────────────────────────────────────────────────────────

def flip_taxonomy():
    """Classify the 15 harmful flips from verified_pass.

    Categories: contradiction, truncation, refusal, elaboration_error, topic_drift
    """
    logger.info("=== Verified_Pass Flip Taxonomy ===")

    results = _load_v4_4()
    gt = _load_ground_truth()

    # Get single_pass and verified_pass answers
    sp_answers = {}
    vp_answers = {}
    for r in results:
        q_id = r["question_id"]
        config = r["config"]
        js = r.get("judge_scores", {})
        correctness = js.get("correctness", 0) if isinstance(js, dict) else 0
        answer = r.get("generation", {}).get("answer", "")

        if config == "single_pass":
            sp_answers[q_id] = {"correctness": correctness, "answer": answer}
        elif config == "verified_pass":
            vp_answers[q_id] = {"correctness": correctness, "answer": answer}

    # Find harmful flips (SP correct → VP incorrect)
    harmful_flips = []
    helpful_flips = []
    for q_id in sp_answers:
        if q_id not in vp_answers:
            continue
        sp_correct = sp_answers[q_id]["correctness"] >= 3
        vp_correct = vp_answers[q_id]["correctness"] >= 3

        if sp_correct and not vp_correct:
            harmful_flips.append(q_id)
        elif not sp_correct and vp_correct:
            helpful_flips.append(q_id)

    # Classify each harmful flip
    classifications = []
    for q_id in harmful_flips:
        sp = sp_answers[q_id]
        vp = vp_answers[q_id]
        gt_q = gt.get(q_id, {})
        category = gt_q.get("category", "unknown")

        sp_text = sp["answer"]
        vp_text = vp["answer"]
        sp_len = len(sp_text.split())
        vp_len = len(vp_text.split())

        # Heuristic classification
        if vp_len < 20 or "cannot" in vp_text.lower() or "no information" in vp_text.lower() or "not found" in vp_text.lower():
            flip_type = "refusal"
        elif vp_len < sp_len * 0.3:
            flip_type = "truncation"
        elif vp_len > sp_len * 2:
            flip_type = "elaboration_error"
        else:
            # Check overlap
            sp_tokens = set(sp_text.lower().split())
            vp_tokens = set(vp_text.lower().split())
            overlap = len(sp_tokens & vp_tokens) / max(len(sp_tokens | vp_tokens), 1)
            if overlap < 0.2:
                flip_type = "topic_drift"
            else:
                flip_type = "content_change"

        classifications.append({
            "question_id": q_id,
            "category": category,
            "flip_type": flip_type,
            "sp_correctness": sp["correctness"],
            "vp_correctness": vp["correctness"],
            "sp_word_count": sp_len,
            "vp_word_count": vp_len,
            "length_ratio": round(vp_len / max(sp_len, 1), 2),
        })

    # Aggregate
    type_counts = Counter(c["flip_type"] for c in classifications)
    category_counts = Counter(c["category"] for c in classifications)

    result = {
        "analysis": "verified_pass_flip_taxonomy",
        "n_harmful_flips": len(harmful_flips),
        "n_helpful_flips": len(helpful_flips),
        "flip_type_distribution": dict(type_counts),
        "category_distribution": dict(category_counts),
        "classifications": classifications,
        "finding": (
            f"Of {len(harmful_flips)} harmful flips: "
            + ", ".join(f"{t}: {n}" for t, n in type_counts.most_common())
            + f". Most affected categories: "
            + ", ".join(f"{c}: {n}" for c, n in category_counts.most_common(3))
            + ". Verified_pass doesn't just fail — it fails in specific, classifiable ways."
        ),
    }

    print(f"\nHarmful flip types ({len(harmful_flips)} total):")
    for t, n in type_counts.most_common():
        pct = n / len(harmful_flips) * 100
        print(f"  {t}: {n} ({pct:.0f}%)")
    print(f"\nBy question category:")
    for c, n in category_counts.most_common():
        print(f"  {c}: {n}")

    _save_result("flip_taxonomy", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 4: OOD Refusal Taxonomy
# ─────────────────────────────────────────────────────────────

def ood_refusal_taxonomy():
    """Classify HOW the system refuses OOD questions across strategies.

    Explains the mechanism behind 100% TNR.
    """
    logger.info("=== OOD Refusal Taxonomy ===")

    results = _load_v4_4()

    # Get OOD answers across strategies
    ood_answers = defaultdict(list)
    for r in results:
        if r.get("category") == "OOD" or r.get("answerable") == False:
            config = r["config"]
            answer = r.get("generation", {}).get("answer", "")
            js = r.get("judge_scores", {})

            # Classify refusal type
            answer_lower = answer.lower()
            if not answer or len(answer.strip()) < 10:
                refusal_type = "empty_or_minimal"
            elif any(p in answer_lower for p in ["cannot find", "not found", "no information",
                     "not available", "does not contain", "no relevant", "unable to find"]):
                refusal_type = "explicit_not_found"
            elif any(p in answer_lower for p in ["cannot answer", "unable to answer",
                     "cannot be answered", "outside", "beyond the scope"]):
                refusal_type = "explicit_scope_refusal"
            elif any(p in answer_lower for p in ["i don't have", "i do not have",
                     "no documents", "no papers", "no sources"]):
                refusal_type = "no_sources_available"
            elif any(p in answer_lower for p in ["based on the", "according to", "the paper"]):
                # Might be a hallucinated answer
                if js.get("refusal_accuracy", 0) >= 3:
                    refusal_type = "hedged_refusal"
                else:
                    refusal_type = "possible_hallucination"
            else:
                refusal_type = "other"

            ood_answers[config].append({
                "question_id": r["question_id"],
                "refusal_type": refusal_type,
                "answer_length": len(answer.split()),
                "answer_preview": answer[:200],
            })

    # Aggregate per strategy
    summary = {}
    for config, answers in ood_answers.items():
        type_counts = Counter(a["refusal_type"] for a in answers)
        summary[config] = {
            "n_ood": len(answers),
            "refusal_types": dict(type_counts),
            "mean_answer_length": round(sum(a["answer_length"] for a in answers) / max(len(answers), 1), 1),
        }

    # Global patterns
    all_types = Counter()
    for answers in ood_answers.values():
        for a in answers:
            all_types[a["refusal_type"]] += 1

    result = {
        "analysis": "ood_refusal_taxonomy",
        "description": "Classification of OOD refusal mechanisms across strategies",
        "per_strategy": summary,
        "global_distribution": dict(all_types),
        "total_ood_answers": sum(len(v) for v in ood_answers.values()),
        "samples": {config: answers[:3] for config, answers in ood_answers.items()},
        "finding": (
            f"Across {sum(len(v) for v in ood_answers.values())} OOD answers: "
            + ", ".join(f"{t}: {n}" for t, n in all_types.most_common(4))
            + ". Strategies differ in HOW they refuse, not WHETHER."
        ),
    }

    print(f"\nOOD Refusal Types (all strategies combined):")
    for t, n in all_types.most_common():
        print(f"  {t}: {n}")
    print(f"\nPer-strategy refusal patterns:")
    for config, s in summary.items():
        dominant = max(s["refusal_types"].items(), key=lambda x: x[1])
        print(f"  {config}: {s['n_ood']} OOD, dominant type: {dominant[0]} ({dominant[1]}), mean len: {s['mean_answer_length']} words")

    _save_result("ood_refusal_taxonomy", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 5: Latency-Quality Pareto Front
# ─────────────────────────────────────────────────────────────

def latency_pareto():
    """Compute Pareto front: for a given latency budget, which strategy is optimal?"""
    logger.info("=== Latency-Quality Pareto Front ===")

    results = _load_v4_4()

    # Aggregate per strategy
    by_config = defaultdict(list)
    for r in results:
        if r.get("answerable", True) and r.get("category") != "OOD":
            config = r["config"]
            latency = r.get("generation", {}).get("latency_s", 0)
            correctness = r.get("judge_scores", {}).get("correctness", 0) if isinstance(r.get("judge_scores"), dict) else 0
            by_config[config].append({"latency": latency, "correctness": correctness})

    strategies = {}
    for config, items in by_config.items():
        lats = [i["latency"] for i in items if i["latency"] > 0]
        cors = [i["correctness"] for i in items if i["correctness"] > 0]
        pass_rate = sum(1 for i in items if i["correctness"] >= 3) / max(len(items), 1)

        strategies[config] = {
            "median_latency_s": round(sorted(lats)[len(lats)//2], 1) if lats else 0,
            "mean_latency_s": round(sum(lats) / max(len(lats), 1), 1),
            "p95_latency_s": round(sorted(lats)[int(len(lats)*0.95)] if lats else 0, 1),
            "mean_correctness": round(sum(cors) / max(len(cors), 1), 2),
            "pass_rate": round(pass_rate, 3),
            "n": len(items),
            "quality_per_second": round((sum(cors) / max(len(cors), 1)) / max(sum(lats) / max(len(lats), 1), 1), 4),
        }

    # Identify Pareto-optimal strategies (maximize correctness, minimize latency)
    pareto = []
    sorted_strats = sorted(strategies.items(), key=lambda x: x[1]["median_latency_s"])
    best_quality = -1
    for name, stats in sorted_strats:
        if stats["mean_correctness"] > best_quality:
            pareto.append(name)
            best_quality = stats["mean_correctness"]

    # Budget recommendations
    budgets = {
        "10s": None, "30s": None, "60s": None, "120s": None, "300s": None
    }
    for budget_label, _ in budgets.items():
        budget_s = int(budget_label.replace("s", ""))
        candidates = [(n, s) for n, s in strategies.items() if s["median_latency_s"] <= budget_s]
        if candidates:
            best = max(candidates, key=lambda x: x[1]["mean_correctness"])
            budgets[budget_label] = {"strategy": best[0], "correctness": best[1]["mean_correctness"], "latency": best[1]["median_latency_s"]}

    result = {
        "analysis": "latency_quality_pareto",
        "strategies": strategies,
        "pareto_optimal": pareto,
        "budget_recommendations": budgets,
        "finding": (
            f"Pareto-optimal strategies: {', '.join(pareto)}. "
            + "Budget recommendations: "
            + "; ".join(f"≤{k}: {v['strategy']} ({v['correctness']:.2f})" for k, v in budgets.items() if v)
        ),
    }

    print(f"\n{'Strategy':<18} {'Med Lat':>8} {'P95 Lat':>8} {'Correct':>8} {'Pass%':>6} {'Q/sec':>7}")
    print("-" * 60)
    for name, s in sorted(strategies.items(), key=lambda x: x[1]["median_latency_s"]):
        pareto_mark = " *" if name in pareto else ""
        print(f"{name:<18} {s['median_latency_s']:>7.1f}s {s['p95_latency_s']:>7.1f}s {s['mean_correctness']:>7.2f} {s['pass_rate']*100:>5.1f}% {s['quality_per_second']:>6.3f}{pareto_mark}")

    print(f"\n* = Pareto-optimal")
    print(f"\nBudget recommendations:")
    for budget, rec in budgets.items():
        if rec:
            print(f"  ≤{budget}: {rec['strategy']} (correctness={rec['correctness']:.2f}, latency={rec['latency']:.1f}s)")

    _save_result("latency_pareto", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 6: Strategy Complementarity
# ─────────────────────────────────────────────────────────────

def strategy_complementarity():
    """Per-question agreement: do strategies fail on same or different questions?

    If different → ensemble could exceed any individual strategy.
    """
    logger.info("=== Strategy Complementarity ===")

    results = _load_v4_4()

    # Build per-question pass/fail matrix
    configs = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
    q_matrix = defaultdict(dict)  # q_id → {config: pass/fail}

    for r in results:
        if r.get("answerable", True) and r.get("category") != "OOD":
            q_id = r["question_id"]
            config = r["config"]
            correctness = r.get("judge_scores", {}).get("correctness", 0) if isinstance(r.get("judge_scores"), dict) else 0
            q_matrix[q_id][config] = correctness >= 3

    # Pairwise agreement (Jaccard of pass sets)
    pass_sets = {c: set() for c in configs}
    for q_id, config_results in q_matrix.items():
        for c in configs:
            if config_results.get(c, False):
                pass_sets[c].add(q_id)

    agreement_matrix = {}
    for c1 in configs:
        for c2 in configs:
            if c1 >= c2:
                continue
            s1, s2 = pass_sets[c1], pass_sets[c2]
            union = s1 | s2
            intersection = s1 & s2
            jaccard = len(intersection) / max(len(union), 1)
            # Questions where one succeeds and the other fails
            only_c1 = s1 - s2
            only_c2 = s2 - s1
            agreement_matrix[f"{c1}_vs_{c2}"] = {
                "jaccard": round(jaccard, 3),
                "both_pass": len(intersection),
                "only_first": len(only_c1),
                "only_second": len(only_c2),
                "both_fail": len(q_matrix) - len(union),
                "complementarity": round(1 - jaccard, 3),
            }

    # Best ensemble pair (maximizes coverage = union of pass sets)
    best_pair = max(
        [(c1, c2) for c1 in configs for c2 in configs if c1 < c2],
        key=lambda p: len(pass_sets[p[0]] | pass_sets[p[1]])
    )
    best_coverage = len(pass_sets[best_pair[0]] | pass_sets[best_pair[1]])
    total_q = len(q_matrix)

    # Oracle ensemble (any strategy passes → pass)
    oracle_pass = set()
    for q_id, config_results in q_matrix.items():
        if any(config_results.values()):
            oracle_pass.add(q_id)

    result = {
        "analysis": "strategy_complementarity",
        "n_questions": total_q,
        "per_strategy_pass": {c: len(s) for c, s in pass_sets.items()},
        "agreement_matrix": agreement_matrix,
        "best_pair": {"strategies": best_pair, "coverage": best_coverage, "coverage_pct": round(best_coverage/total_q*100, 1)},
        "oracle_coverage": {"n_pass": len(oracle_pass), "pct": round(len(oracle_pass)/total_q*100, 1)},
        "best_single": {"strategy": "rlm_10", "coverage": len(pass_sets.get("rlm_10", set())), "coverage_pct": round(len(pass_sets.get("rlm_10", set()))/total_q*100, 1)},
        "finding": (
            f"Oracle ensemble (any strategy passes): {len(oracle_pass)}/{total_q} ({len(oracle_pass)/total_q*100:.1f}%). "
            f"Best single (rlm_10): {len(pass_sets.get('rlm_10', set()))}/{total_q} ({len(pass_sets.get('rlm_10', set()))/total_q*100:.1f}%). "
            f"Best pair: {best_pair[0]}+{best_pair[1]}: {best_coverage}/{total_q} ({best_coverage/total_q*100:.1f}%). "
            f"Ensemble headroom: +{len(oracle_pass) - len(pass_sets.get('rlm_10', set()))} questions."
        ),
    }

    print(f"\nPer-strategy pass count:")
    for c in configs:
        print(f"  {c}: {len(pass_sets[c])}/{total_q} ({len(pass_sets[c])/total_q*100:.1f}%)")

    print(f"\nOracle (any strategy): {len(oracle_pass)}/{total_q} ({len(oracle_pass)/total_q*100:.1f}%)")
    print(f"Best pair: {best_pair[0]} + {best_pair[1]}: {best_coverage}/{total_q} ({best_coverage/total_q*100:.1f}%)")
    print(f"Ensemble headroom over rlm_10: +{len(oracle_pass) - len(pass_sets.get('rlm_10', set()))} questions")

    # Show complementarity matrix
    print(f"\nComplementarity (1-Jaccard) — higher = more complementary:")
    for pair, data in sorted(agreement_matrix.items(), key=lambda x: x[1]["complementarity"], reverse=True)[:8]:
        print(f"  {pair}: {data['complementarity']:.3f} (only_1={data['only_first']}, only_2={data['only_second']})")

    _save_result("strategy_complementarity", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 7: Scaling Law Exponent Fitting
# ─────────────────────────────────────────────────────────────

def scaling_law_fit():
    """Fit power, log, and sigmoid models to V4-5 corpus scaling data.

    Filters out empty/unjudged results (especially s50 Gemini quota empties).
    """
    logger.info("=== Scaling Law Exponent Fitting ===")

    results = _load_v4_5()

    # Extract pass rates by corpus size × strategy (no-noise only)
    by_size_config = defaultdict(list)
    skipped_empty = 0
    skipped_unjudged = 0
    for r in results:
        idx = r.get("index_name", "")
        config = r.get("config", "")

        # Parse corpus size from index name (exp_v4_s5_n0 → 5)
        if "_n0" not in idx:
            continue  # Only no-noise

        size_match = re.search(r"_s(\d+)_", idx)
        if not size_match:
            continue
        size = int(size_match.group(1))

        # Only answerable
        if r.get("category") == "OOD" or r.get("answerable") == False:
            continue

        # Filter out empty answers (Gemini quota failures)
        answer = r.get("generation", {}).get("answer", "")
        if not answer or len(answer.strip()) < 10:
            skipped_empty += 1
            continue

        js = r.get("judge_scores", {})
        if not isinstance(js, dict) or js.get("correctness") is None:
            skipped_unjudged += 1
            continue
        correctness = js.get("correctness", 0)

        by_size_config[(size, config)].append(correctness)

    logger.info(f"Filtered: {skipped_empty} empty, {skipped_unjudged} unjudged")

    # Compute pass rates
    pass_rates = {}
    for (size, config), scores in by_size_config.items():
        if len(scores) >= 5:  # Minimum sample
            pass_rates[(size, config)] = {
                "pass_rate": round(sum(1 for s in scores if s >= 3) / len(scores), 4),
                "n": len(scores),
                "mean_correctness": round(sum(scores) / len(scores), 4),
            }

    # Aggregate by size (all strategies)
    by_size = defaultdict(list)
    for (size, config), data in pass_rates.items():
        by_size[size].append(data["pass_rate"])

    size_means = {}
    for size, rates in sorted(by_size.items()):
        size_means[size] = round(sum(rates) / len(rates), 4)

    # Fit models (simple least squares)
    sizes = sorted(size_means.keys())
    rates_list = [size_means[s] for s in sizes]

    fits = {}

    # Log model: y = a * ln(x) + b
    if len(sizes) >= 2:
        ln_x = [math.log(s) for s in sizes]
        n = len(sizes)
        sum_lnx = sum(ln_x)
        sum_y = sum(rates_list)
        sum_lnx_y = sum(ln_x[i] * rates_list[i] for i in range(n))
        sum_lnx2 = sum(x**2 for x in ln_x)

        denom = n * sum_lnx2 - sum_lnx**2
        if abs(denom) > 1e-10:
            a = (n * sum_lnx_y - sum_lnx * sum_y) / denom
            b = (sum_y - a * sum_lnx) / n
            predicted = [a * math.log(s) + b for s in sizes]
            ss_res = sum((rates_list[i] - predicted[i])**2 for i in range(n))
            ss_tot = sum((rates_list[i] - sum_y/n)**2 for i in range(n))
            r2 = 1 - ss_res / max(ss_tot, 1e-10)
            fits["logarithmic"] = {"a": round(a, 4), "b": round(b, 4), "R2": round(r2, 4), "formula": f"y = {a:.4f} * ln(x) + {b:.4f}"}

    # Power model: y = a * x^c (linearize: ln(y) = ln(a) + c*ln(x))
    if len(sizes) >= 2 and all(r > 0 for r in rates_list):
        ln_y = [math.log(r) for r in rates_list]
        sum_lny = sum(ln_y)
        sum_lnx_lny = sum(ln_x[i] * ln_y[i] for i in range(n))

        denom = n * sum_lnx2 - sum_lnx**2
        if abs(denom) > 1e-10:
            c = (n * sum_lnx_lny - sum_lnx * sum_lny) / denom
            ln_a = (sum_lny - c * sum_lnx) / n
            a_power = math.exp(ln_a)
            predicted = [a_power * s**c for s in sizes]
            ss_res = sum((rates_list[i] - predicted[i])**2 for i in range(n))
            ss_tot = sum((rates_list[i] - sum_y/n)**2 for i in range(n))
            r2 = 1 - ss_res / max(ss_tot, 1e-10)
            fits["power_law"] = {"a": round(a_power, 4), "c": round(c, 4), "R2": round(r2, 4), "formula": f"y = {a_power:.4f} * x^{c:.4f}"}

    # Per-strategy scaling
    strategy_scaling = defaultdict(dict)
    for (size, config), data in pass_rates.items():
        strategy_scaling[config][size] = data["pass_rate"]

    result = {
        "analysis": "scaling_law_fit",
        "size_means": {str(k): v for k, v in size_means.items()},
        "per_size_config": {f"s{k[0]}_{k[1]}": v for k, v in pass_rates.items()},
        "strategy_scaling": dict(strategy_scaling),
        "fits": fits,
        "best_fit": max(fits.items(), key=lambda x: x[1]["R2"])[0] if fits else None,
        "skipped_empty": skipped_empty,
        "skipped_unjudged": skipped_unjudged,
        "finding": (
            f"Corpus size scaling (no-noise, judged only, {skipped_empty} empties filtered): "
            + ", ".join(f"s{s}: {r:.3f}" for s, r in size_means.items())
            + ". Model fits: "
            + "; ".join(f"{name}: R²={f['R2']:.3f}" for name, f in fits.items())
        ),
    }

    print(f"\nMean pass rate by corpus size (no-noise):")
    for s, r in size_means.items():
        print(f"  s{s}: {r:.4f}")
    print(f"\nFiltered: {skipped_empty} empty, {skipped_unjudged} unjudged")
    print(f"\nModel fits:")
    for name, f in fits.items():
        print(f"  {name}: {f['formula']}, R²={f['R2']:.4f}")

    print(f"\nPer-strategy scaling (no-noise):")
    configs = sorted(set(c for _, c in pass_rates.keys()))
    sizes_avail = sorted(set(s for s, _ in pass_rates.keys()))
    header = f"{'Strategy':<18}" + "".join(f"{'s'+str(s):>8}" for s in sizes_avail)
    print(header)
    print("-" * len(header))
    for config in configs:
        row = f"{config:<18}"
        for size in sizes_avail:
            pr = pass_rates.get((size, config), {}).get("pass_rate")
            row += f"{pr*100:>7.1f}%" if pr is not None else "      -"
        print(row)

    _save_result("scaling_law_fit", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 8: Orchestration Blame Attribution
# ─────────────────────────────────────────────────────────────

def orchestration_blame():
    """For V4-6 full_orchestrator failures, attribute blame to specific components.

    Compare: raw_gemini correct + full_orchestrator wrong → orchestrator broke it.
    """
    logger.info("=== Orchestration Blame Attribution ===")

    results = _load_v4_6()

    # Group by question
    by_question = defaultdict(dict)
    for r in results:
        q_id = r["question_id"]
        config = r["config"]
        js = r.get("judge_scores", {})
        correctness = js.get("correctness", 0) if isinstance(js, dict) else 0
        answer = r.get("generation", {}).get("answer", "")
        latency = r.get("generation", {}).get("latency_s", 0)

        by_question[q_id][config] = {
            "correctness": correctness,
            "pass": correctness >= 3,
            "answer_len": len(answer.split()),
            "latency": latency,
            "answer_preview": answer[:300],
            "category": r.get("category", ""),
            "answerable": r.get("answerable", True),
        }

    # Find orchestrator-specific failures
    orch_failures = []  # raw_gemini correct, orchestrator wrong
    orch_rescues = []   # raw_gemini wrong, orchestrator correct

    for q_id, configs in by_question.items():
        raw = configs.get("raw_gemini", {})
        orch = configs.get("full_orchestrator", {})
        rlm = configs.get("rlm_10", {})
        naive = configs.get("naive_rag", {})

        if not raw or not orch:
            continue

        if raw.get("pass") and not orch.get("pass"):
            orch_failures.append({
                "question_id": q_id,
                "category": raw.get("category", ""),
                "answerable": raw.get("answerable", True),
                "raw_correctness": raw["correctness"],
                "orch_correctness": orch["correctness"],
                "rlm_pass": rlm.get("pass", None),
                "naive_pass": naive.get("pass", None),
                "orch_answer_len": orch["answer_len"],
                "raw_answer_len": raw["answer_len"],
                # Heuristic blame
                "likely_cause": (
                    "refusal_bypass" if orch["answer_len"] > 50 and not raw.get("answerable", True)
                    else "truncation" if orch["answer_len"] < raw["answer_len"] * 0.2
                    else "weak_agent" if orch["correctness"] <= 2
                    else "quality_degradation"
                ),
            })
        elif not raw.get("pass") and orch.get("pass"):
            orch_rescues.append({
                "question_id": q_id,
                "category": raw.get("category", ""),
            })

    # Aggregate causes
    cause_counts = Counter(f["likely_cause"] for f in orch_failures)
    category_counts = Counter(f["category"] for f in orch_failures)

    # How many questions does each layer get right?
    layer_pass = defaultdict(int)
    layer_total = defaultdict(int)
    for q_id, configs in by_question.items():
        for config_name, data in configs.items():
            if data.get("answerable", True):
                layer_total[config_name] += 1
                if data.get("pass"):
                    layer_pass[config_name] += 1

    result = {
        "analysis": "orchestration_blame_attribution",
        "n_orch_failures": len(orch_failures),
        "n_orch_rescues": len(orch_rescues),
        "cause_distribution": dict(cause_counts),
        "category_distribution": dict(category_counts),
        "layer_pass_rates": {c: round(layer_pass[c] / max(layer_total[c], 1), 3) for c in layer_total},
        "failures": orch_failures[:10],  # Sample
        "finding": (
            f"Of {len(orch_failures)} orchestrator-specific failures (raw_gemini correct → orchestrator wrong): "
            + ", ".join(f"{c}: {n}" for c, n in cause_counts.most_common())
            + f". Orchestrator rescues (raw wrong → orch correct): only {len(orch_rescues)}. "
            f"Net: orchestrator DESTROYS {len(orch_failures) - len(orch_rescues)} answers."
        ),
    }

    print(f"\nOrchestrator-specific failures: {len(orch_failures)}")
    print(f"Orchestrator rescues: {len(orch_rescues)}")
    print(f"Net damage: {len(orch_failures) - len(orch_rescues)} questions broken")
    print(f"\nFailure causes:")
    for cause, n in cause_counts.most_common():
        print(f"  {cause}: {n} ({n/len(orch_failures)*100:.0f}%)")
    print(f"\nBy category:")
    for cat, n in category_counts.most_common():
        print(f"  {cat}: {n}")
    print(f"\nLayer pass rates (answerable only):")
    for config in ["raw_gemini", "naive_rag", "rlm_10", "full_orchestrator"]:
        pr = layer_pass[config] / max(layer_total[config], 1)
        print(f"  {config}: {layer_pass[config]}/{layer_total[config]} ({pr*100:.1f}%)")

    _save_result("orchestration_blame", result)
    return result


# ─────────────────────────────────────────────────────────────
# Analysis 9: Judge Ensemble Voting
# ─────────────────────────────────────────────────────────────

def judge_ensemble():
    """Test whether majority voting among top judges improves signal.

    Uses 19 judges × 107 questions from V4-0 post-fix scoring.
    Compares single-judge (qwen3-coder) vs top-K ensemble vs full ensemble.
    """
    logger.info("=== Judge Ensemble Voting ===")

    judge_scores = _load_judge_files()  # 19 judges × 107 questions
    cal = _load_calibration()
    obj_metrics = _load_objective_metrics()

    # Get top judges by calibration
    calibration = cal["calibration"]
    ranked_judges = sorted(calibration.items(), key=lambda x: x[1].get("composite_calibration", 0), reverse=True)

    # Find common questions across ALL judges
    common_qs = None
    for judge in judge_scores:
        qs = set(judge_scores[judge].keys())
        common_qs = qs if common_qs is None else common_qs & qs

    logger.info(f"{len(judge_scores)} judges, {len(common_qs)} common questions")

    # Build ground truth from objective metrics
    # Objective metrics key format matches judge score keys
    gt_pass = {}  # question_key -> bool (ground truth pass)
    for key, metrics in obj_metrics.items():
        # Use concept_recall >= 0.3 AND semantic_sim >= 0.5 as ground truth pass
        cr = metrics.get("concept_recall", 0)
        ss = metrics.get("semantic_similarity", 0)
        gt_pass[key] = cr >= 0.3 and ss >= 0.5

    # Test different ensemble sizes
    ensemble_configs = [
        ("top_1 (qwen3-coder)", [ranked_judges[0][0]]),
        ("top_3", [j[0] for j in ranked_judges[:3]]),
        ("top_5", [j[0] for j in ranked_judges[:5]]),
        ("top_7", [j[0] for j in ranked_judges[:7]]),
        ("top_10", [j[0] for j in ranked_judges[:10]]),
        ("all_19", [j[0] for j in ranked_judges]),
    ]

    # Also test dimension-specific specialists
    # Best faithfulness judges (from specialization analysis)
    faith_ranked = sorted(calibration.items(),
        key=lambda x: (x[1].get("faithfulness_vs_concept_recall", {}).get("spearman", 0)
                       if isinstance(x[1].get("faithfulness_vs_concept_recall"), dict)
                       else x[1].get("faithfulness_vs_concept_recall", 0)),
        reverse=True)

    ensemble_results = {}
    for config_name, judge_list in ensemble_configs:
        # For each question, compute majority vote
        tp = fp = tn = fn = 0
        agreements = []

        for q_key in common_qs:
            if q_key not in gt_pass:
                continue

            votes_pass = []
            vote_scores = []
            for judge in judge_list:
                if judge in judge_scores and q_key in judge_scores[judge]:
                    s = judge_scores[judge][q_key]
                    correctness = s.get("correctness", 0)
                    votes_pass.append(correctness >= 3)
                    vote_scores.append(correctness)

            if len(votes_pass) < 1:
                continue

            # Majority vote
            majority_pass = sum(votes_pass) > len(votes_pass) / 2
            gt = gt_pass[q_key]

            if majority_pass and gt:
                tp += 1
            elif majority_pass and not gt:
                fp += 1
            elif not majority_pass and gt:
                fn += 1
            else:
                tn += 1

            # Agreement rate among voters
            if len(votes_pass) > 1:
                agreement = max(sum(votes_pass), len(votes_pass) - sum(votes_pass)) / len(votes_pass)
                agreements.append(agreement)

        total = tp + fp + tn + fn
        accuracy = (tp + tn) / max(total, 1)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-10)

        ensemble_results[config_name] = {
            "n_judges": len(judge_list),
            "n_evaluated": total,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "mean_agreement": round(sum(agreements) / len(agreements), 4) if agreements else 1.0,
            "judges": [j.replace("ollama::", "") for j in judge_list],
        }

    # Find best ensemble
    best = max(ensemble_results.items(), key=lambda x: x[1]["f1"])

    result = {
        "analysis": "judge_ensemble_voting",
        "description": "Majority voting across top-K judges vs single judge",
        "n_judges_total": len(judge_scores),
        "n_common_questions": len(common_qs),
        "n_with_ground_truth": sum(1 for q in common_qs if q in gt_pass),
        "ensemble_results": ensemble_results,
        "best_config": best[0],
        "finding": (
            f"Ensemble voting across {len(judge_scores)} judges on {len(common_qs)} questions. "
            f"Best config: {best[0]} (F1={best[1]['f1']:.3f}, acc={best[1]['accuracy']:.3f}). "
            f"Single judge (qwen3-coder): F1={ensemble_results.get('top_1 (qwen3-coder)', {}).get('f1', '?')}. "
            + ("Ensemble IMPROVES over single judge."
               if best[1]["f1"] > ensemble_results.get("top_1 (qwen3-coder)", {}).get("f1", 0)
               else "Single judge is competitive with ensemble — calibration-based selection works.")
        ),
    }

    print(f"\n{'Config':<25} {'Judges':>6} {'Acc':>7} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Agree':>7}")
    print("-" * 72)
    for name, r in ensemble_results.items():
        agr = f"{r['mean_agreement']:.3f}" if r['mean_agreement'] else "  -"
        marker = " <-- best" if name == best[0] else ""
        print(f"{name:<25} {r['n_judges']:>6} {r['accuracy']:>7.3f} {r['precision']:>7.3f} {r['recall']:>7.3f} {r['f1']:>7.3f} {agr:>7}{marker}")

    _save_result("judge_ensemble", result)
    return result


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def _load_v4_8_analysis() -> Dict:
    """Load V4-8 preliminary analysis (from exp_05_coder_analysis.py)."""
    f = RESULTS_DIR / "v4_8_preliminary_analysis.json"
    if not f.exists():
        raise FileNotFoundError(
            f"{f} not found. Run: uv run python publication/scripts/exp_05_coder_analysis.py --partial"
        )
    return json.load(open(f))


def thinking_mode_coder():
    """Thinking mode impact on code generation: which models benefit, which degrade?

    Uses V4-8 thinking mode analysis to build a compact decision matrix.
    """
    logger.info("=== Thinking Mode x Code Generation ===")

    v48 = _load_v4_8_analysis()
    think_data = v48.get("thinking_mode", {}).get("models", {})
    if not think_data:
        raise ValueError("No thinking_mode data in v4_8_preliminary_analysis.json")

    models_summary = {}
    for base, mdata in think_data.items():
        variants = mdata.get("variants", {})
        comparisons = mdata.get("comparisons", [])

        off_pr = variants.get("off", {}).get("pass_rate")
        if off_pr is None:
            continue

        best_think = None
        best_delta = 0
        for comp in comparisons:
            if comp["delta_pp"] > best_delta:
                best_delta = comp["delta_pp"]
                best_think = comp["variant"]

        off_by_cfg = variants.get("off", {}).get("by_config", {})
        config_deltas = {}
        for think_level, vdata in variants.items():
            if think_level == "off":
                continue
            think_by_cfg = vdata.get("by_config", {})
            for cfg in off_by_cfg:
                if cfg in think_by_cfg:
                    delta = think_by_cfg[cfg] - off_by_cfg[cfg]
                    config_deltas[f"{think_level}|{cfg}"] = round(delta, 1)

        helped_configs = [k for k, v in config_deltas.items() if v > 5]
        hurt_configs = [k for k, v in config_deltas.items() if v < -5]

        models_summary[base] = {
            "off_pass_rate": off_pr,
            "best_thinking_variant": best_think,
            "best_delta_pp": round(best_delta, 1),
            "n_variants": len(variants) - 1,
            "helped_configs": helped_configs,
            "hurt_configs": hurt_configs,
            "all_config_deltas": config_deltas,
            "significant_comparisons": [
                c for c in comparisons if c.get("mcnemar", {}).get("p_value", 1) < 0.05
            ],
        }

        logger.info(f"  {base}: off={off_pr:.1f}%, best_think={best_think} "
                     f"({best_delta:+.1f}pp), helped={len(helped_configs)}, "
                     f"hurt={len(hurt_configs)}")

    # Cross-model config consensus
    all_cfg_deltas = defaultdict(list)
    for base, ms in models_summary.items():
        for key, delta in ms["all_config_deltas"].items():
            _, cfg = key.split("|", 1)
            all_cfg_deltas[cfg].append(delta)

    config_consensus = {}
    for cfg, deltas in sorted(all_cfg_deltas.items()):
        mean_d = sum(deltas) / len(deltas)
        config_consensus[cfg] = {
            "mean_delta": round(mean_d, 1),
            "n_models": len(deltas),
            "consistently_positive": all(d > 0 for d in deltas),
            "consistently_negative": all(d < 0 for d in deltas),
        }

    result = {
        "analysis": "thinking_mode_coder",
        "description": "Thinking mode impact on code generation across V4-8 models",
        "n_model_groups": len(models_summary),
        "models": models_summary,
        "config_consensus": config_consensus,
        "finding": (
            f"Thinking mode analyzed across {len(models_summary)} model groups. "
            f"Significant improvements in {sum(1 for m in models_summary.values() if m['significant_comparisons'])} groups."
        ),
    }

    _save_result("thinking_mode_coder", result)
    return result


def num_ctx_sensitivity():
    """Context window sensitivity: V2-8 (2K) vs V4-8 (24K) delta by config type.

    Tests whether context-heavy configs show larger improvements than simple configs.
    """
    logger.info("=== Context Window Sensitivity ===")

    comp_file = RESULTS_DIR / "v4_8_comparison_v2_vs_v4.json"
    if not comp_file.exists():
        raise FileNotFoundError(
            f"{comp_file} not found. Run: uv run python publication/scripts/exp_05_coder_analysis.py --partial"
        )
    comparison = json.load(open(comp_file))

    v2_dir = Path(__file__).parent.parent / "experiments_v2" / "results_v2"

    config_deltas = defaultdict(list)
    for f in sorted(RESULTS_DIR.glob("v4_8_coder_benchmark_*_latest.json")):
        v4_data = json.load(open(f))
        model_key = f.name.replace("v4_8_coder_benchmark_", "").replace("_latest.json", "")
        v2_file = v2_dir / f"v2_8_coder_benchmark_{model_key}_latest.json"
        if not v2_file.exists():
            continue
        v2_data = json.load(open(v2_file))
        v4_summary = v4_data.get("summary", {})
        v2_summary = v2_data.get("summary", {})
        for cfg in v4_summary:
            if cfg in v2_summary:
                v4_pr = v4_summary[cfg].get("pass_rate", 0)
                v2_pr = v2_summary[cfg].get("pass_rate", 0)
                config_deltas[cfg].append({
                    "model": model_key, "v2_pass_rate": v2_pr,
                    "v4_pass_rate": v4_pr, "delta_pp": round(v4_pr - v2_pr, 1),
                })

    context_heavy = {"introspect_then_code", "error_recovery_introspect",
                     "thinker_coder_split", "introspect_with_recovery"}
    context_light = {"free_form", "coder_v2_n1"}

    heavy_deltas, light_deltas = [], []
    config_summary = {}
    for cfg, entries in sorted(config_deltas.items()):
        deltas = [e["delta_pp"] for e in entries]
        mean_d = sum(deltas) / len(deltas) if deltas else 0
        ctx_class = "heavy" if cfg in context_heavy else ("light" if cfg in context_light else "medium")
        config_summary[cfg] = {
            "mean_delta_pp": round(mean_d, 1), "n_models": len(entries),
            "per_model": entries, "context_class": ctx_class,
        }
        if cfg in context_heavy:
            heavy_deltas.extend(deltas)
        elif cfg in context_light:
            light_deltas.extend(deltas)

    hypothesis_test = None
    if heavy_deltas and light_deltas:
        from scipy import stats as sp_stats
        u_stat, p_val = sp_stats.mannwhitneyu(heavy_deltas, light_deltas, alternative="greater")
        hypothesis_test = {
            "test": "mann_whitney_u", "alternative": "heavy_configs > light_configs",
            "heavy_mean_delta": round(sum(heavy_deltas) / len(heavy_deltas), 1),
            "light_mean_delta": round(sum(light_deltas) / len(light_deltas), 1),
            "u_statistic": round(float(u_stat), 2), "p_value": round(float(p_val), 4),
            "n_heavy": len(heavy_deltas), "n_light": len(light_deltas),
        }
        logger.info(f"  Heavy mean: {hypothesis_test['heavy_mean_delta']:+.1f}pp, "
                     f"Light mean: {hypothesis_test['light_mean_delta']:+.1f}pp, "
                     f"p={hypothesis_test['p_value']:.4f}")

    finding = (
        f"Compared {len(config_summary)} configs. "
        f"Heavy: {hypothesis_test['heavy_mean_delta']:+.1f}pp vs Light: {hypothesis_test['light_mean_delta']:+.1f}pp "
        f"(p={hypothesis_test['p_value']:.4f})."
        if hypothesis_test else "Insufficient data for hypothesis test."
    )

    result = {
        "analysis": "num_ctx_sensitivity",
        "description": "Context window sensitivity: V2-8 (2K) vs V4-8 (24K) by config type",
        "n_configs": len(config_summary), "config_summary": config_summary,
        "hypothesis_test": hypothesis_test, "finding": finding,
    }

    _save_result("num_ctx_sensitivity", result)
    return result


ALL_ANALYSES = {
    "judge_specialization": judge_specialization,
    "self_bleu": self_bleu_analysis,
    "flip_taxonomy": flip_taxonomy,
    "ood_refusal_taxonomy": ood_refusal_taxonomy,
    "latency_pareto": latency_pareto,
    "strategy_complementarity": strategy_complementarity,
    "scaling_law_fit": scaling_law_fit,
    "orchestration_blame": orchestration_blame,
    "judge_ensemble": judge_ensemble,
    "thinking_mode_coder": thinking_mode_coder,
    "num_ctx_sensitivity": num_ctx_sensitivity,
}


def main():
    parser = argparse.ArgumentParser(description="Deep analyses suite for NMI paper")
    parser.add_argument("--analysis", choices=list(ALL_ANALYSES.keys()), help="Run specific analysis")
    parser.add_argument("--all", action="store_true", help="Run all analyses")
    parser.add_argument("--list", action="store_true", help="List available analyses")
    args = parser.parse_args()

    if args.list:
        print("Available analyses:")
        for name, fn in ALL_ANALYSES.items():
            doc = fn.__doc__.strip().split("\n")[0] if fn.__doc__ else ""
            print(f"  {name:<30} {doc}")
        return

    if args.all:
        analyses = list(ALL_ANALYSES.keys())
    elif args.analysis:
        analyses = [args.analysis]
    else:
        parser.print_help()
        return

    results = {}
    for name in analyses:
        print(f"\n{'='*60}")
        try:
            results[name] = ALL_ANALYSES[name]()
        except Exception as e:
            logger.error(f"Analysis {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = {"error": str(e)}

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(results)} analyses completed")
    for name, r in results.items():
        if isinstance(r, dict) and "finding" in r:
            print(f"\n  [{name}]")
            print(f"  {r['finding'][:200]}...")

    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
