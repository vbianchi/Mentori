#!/usr/bin/env python3
"""
Per-Turn RLM Compute Saturation Analysis for V4 Experiments.

Analyzes how information accumulates across RLM recursion depths to validate
Basu's compute saturation theory: H = ln(s) / ln(p), where H is the effective
reasoning horizon, s is problem complexity, and p is per-turn success probability.

Since per-turn intermediate data is not stored in V4-4 results, this script
uses AGGREGATE evidence across rlm_5, rlm_10, rlm_20 configs:

1. Concept recall (deterministic) per question per config
2. Semantic similarity (BGE-M3) per question per config
3. Marginal gain analysis: (rlm_10 - rlm_5) vs (rlm_20 - rlm_10)
4. Answer length growth as proxy for information accumulation
5. Category-level breakdown (FR, CO, TE, CD, SY)
6. Basu's H estimation from observed diminishing returns
7. LLM-call efficiency (quality per LLM call)

Usage:
  uv run python publication/scripts/analysis_perturn.py
  uv run python publication/scripts/analysis_perturn.py --skip-embeddings
  uv run python publication/scripts/analysis_perturn.py --include-v45
"""

import argparse
import json
import logging
import math
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# ── Project path setup ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from exp_common import (
    V4_GROUND_TRUTH,
    V4_RESULTS_DIR,
    save_v4_results,
    save_v4_markdown,
)

logger = logging.getLogger("perturn_analysis")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ── Constants ──
RLM_CONFIGS = ["rlm_5", "rlm_10", "rlm_20"]
ALL_CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
RLM_DEPTH_MAP = {"rlm_5": 5, "rlm_10": 10, "rlm_20": 20}
CATEGORY_MAP = {
    "factual_recall": "FR",
    "conceptual": "CO",
    "technical": "TE",
    "cross_document": "CD",
    "synthesis": "SY",
    "out_of_domain": "OOD",
}
ANSWERABLE_CATEGORIES = ["factual_recall", "conceptual", "technical", "cross_document", "synthesis"]


# ═══════════════════════════════════════════════════════════════
# 1. METRIC FUNCTIONS (reused from deterministic scorer)
# ═══════════════════════════════════════════════════════════════

def compute_concept_recall(answer: str, expected_concepts: List[str]) -> float:
    """Fraction of expected concepts found in the answer."""
    if not expected_concepts:
        return 1.0
    answer_lower = answer.lower()
    found = 0
    for concept in expected_concepts:
        concept_lower = concept.lower()
        if concept_lower in answer_lower:
            found += 1
            continue
        words = concept_lower.split()
        if len(words) > 1:
            sig_words = [w for w in words if len(w) > 3]
            if sig_words and all(w in answer_lower for w in sig_words):
                found += 1
                continue
        if '-' in concept_lower:
            if concept_lower.replace('-', ' ') in answer_lower:
                found += 1
                continue
        if ' ' in concept_lower:
            if concept_lower.replace(' ', '-') in answer_lower:
                found += 1
                continue
    return found / len(expected_concepts)


def extract_numbers(text: str) -> Set[str]:
    """Extract numeric values from text."""
    numbers = set()
    for m in re.finditer(r'(\d+\.?\d*)\s*(%|[A-Za-z]{1,5}(?:/[A-Za-z]{1,5})?)?', text):
        num_str = m.group(1)
        unit = (m.group(2) or "").lower().strip()
        try:
            num_val = float(num_str)
            numbers.add(num_str)
            if unit:
                numbers.add(f"{num_str}{unit}")
            if num_val == int(num_val) and '.' in num_str:
                numbers.add(str(int(num_val)))
        except ValueError:
            continue
    return numbers


def compute_number_overlap(expected_answer: str, generated_answer: str) -> float:
    """Fraction of numbers from expected answer found in generated answer."""
    expected_nums = extract_numbers(expected_answer)
    if not expected_nums:
        return 1.0
    generated_nums = extract_numbers(generated_answer)
    gen_lower = generated_answer.lower()
    found = 0
    for num in expected_nums:
        if num in generated_nums or num in gen_lower:
            found += 1
    return min(found / len(expected_nums), 1.0)


def count_citations(answer: str) -> int:
    """Count citation markers in answer."""
    inline = re.findall(r'\[([^\]]+\.pdf):?\d*\]', answer, re.IGNORECASE)
    numbered = re.findall(r'\[(\d+)\]', answer)
    return len(inline) + len(numbered)


# ═══════════════════════════════════════════════════════════════
# 2. DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_v44_results() -> List[Dict]:
    """Load V4-4 generation strategy results."""
    path = V4_RESULTS_DIR / "v4_4_generation_latest.json"
    if not path.exists():
        raise FileNotFoundError(f"V4-4 results not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return data["per_question_results"]


def load_v45_intermediate() -> List[Dict]:
    """Load V4-5 intermediate results if available."""
    results = []
    for fname in ["v4_5_intermediate.json", "v4_5_intermediate_s20.json", "v4_5_intermediate_s50.json"]:
        path = V4_RESULTS_DIR / fname
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            results.extend(data.get("results", []))
    return results


def load_ground_truth() -> Dict[str, Dict]:
    """Load ground truth indexed by question_id."""
    with open(V4_GROUND_TRUTH) as f:
        data = json.load(f)
    return {q["id"]: q for q in data["questions"]}


# ═══════════════════════════════════════════════════════════════
# 3. PER-QUESTION ANALYSIS
# ═══════════════════════════════════════════════════════════════

@dataclass
class QuestionMetrics:
    """Metrics for one question across one config."""
    question_id: str
    category: str
    config: str
    max_depth: int  # allowed RLM depth (5, 10, 20, or 0 for non-RLM)
    actual_llm_calls: int
    answer_length: int  # character count
    answer_words: int
    concept_recall: float
    number_overlap: float
    citation_count: int
    latency_s: float
    semantic_similarity: Optional[float] = None
    # Derived
    quality_per_call: Optional[float] = None  # concept_recall / llm_calls


def analyze_question(
    result: Dict,
    gt: Dict,
    embedder=None,
) -> Optional[QuestionMetrics]:
    """Compute metrics for a single question result."""
    if not result.get("answerable", True):
        return None

    answer = result.get("generation", {}).get("answer", "")
    if not answer or len(answer.strip()) < 10:
        return None

    config = result["config"]
    expected_concepts = gt.get("expected_concepts", [])
    expected_answer = gt.get("expected_answer", "")

    cr = compute_concept_recall(answer, expected_concepts)
    no = compute_number_overlap(expected_answer, answer)
    llm_calls = result.get("generation", {}).get("llm_calls", 1) or 1
    depth = RLM_DEPTH_MAP.get(config, 0)

    m = QuestionMetrics(
        question_id=result["question_id"],
        category=result.get("category", "unknown"),
        config=config,
        max_depth=depth,
        actual_llm_calls=llm_calls,
        answer_length=len(answer),
        answer_words=len(answer.split()),
        concept_recall=cr,
        number_overlap=no,
        citation_count=count_citations(answer),
        latency_s=result.get("generation", {}).get("latency_s", 0),
    )

    # Semantic similarity if embedder available
    if embedder is not None and expected_answer:
        try:
            embs = embedder.encode([expected_answer[:2000], answer[:2000]], normalize_embeddings=True)
            m.semantic_similarity = float(np.dot(embs[0], embs[1]))
        except Exception as e:
            logger.warning(f"Embedding failed for {result['question_id']}: {e}")

    # Quality per call
    if llm_calls > 0:
        m.quality_per_call = cr / llm_calls

    return m


# ═══════════════════════════════════════════════════════════════
# 4. MARGINAL GAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════

@dataclass
class MarginalGain:
    """Marginal gain from depth_low to depth_high for one question."""
    question_id: str
    category: str
    depth_low: int
    depth_high: int
    delta_concept_recall: float
    delta_number_overlap: float
    delta_answer_length: int
    delta_citations: int
    delta_latency: float
    delta_semantic_sim: Optional[float] = None


def compute_marginal_gains(
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]],
) -> List[MarginalGain]:
    """Compute marginal gains between adjacent RLM depths."""
    gains = []
    depth_pairs = [(5, 10), (10, 20)]

    for qid, config_metrics in metrics_by_qid.items():
        for d_low, d_high in depth_pairs:
            cfg_low = f"rlm_{d_low}"
            cfg_high = f"rlm_{d_high}"
            m_low = config_metrics.get(cfg_low)
            m_high = config_metrics.get(cfg_high)
            if not m_low or not m_high:
                continue

            delta_ss = None
            if m_low.semantic_similarity is not None and m_high.semantic_similarity is not None:
                delta_ss = m_high.semantic_similarity - m_low.semantic_similarity

            gains.append(MarginalGain(
                question_id=qid,
                category=m_low.category,
                depth_low=d_low,
                depth_high=d_high,
                delta_concept_recall=m_high.concept_recall - m_low.concept_recall,
                delta_number_overlap=m_high.number_overlap - m_low.number_overlap,
                delta_answer_length=m_high.answer_length - m_low.answer_length,
                delta_citations=m_high.citation_count - m_low.citation_count,
                delta_latency=m_high.latency_s - m_low.latency_s,
                delta_semantic_sim=delta_ss,
            ))

    return gains


# ═══════════════════════════════════════════════════════════════
# 5. BASU'S H ESTIMATION
# ═══════════════════════════════════════════════════════════════

def estimate_basu_parameters(
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]],
) -> Dict[str, Any]:
    """
    Estimate Basu's compute saturation parameters from observed data.

    Basu's model: H = ln(s) / ln(p)
    - H: effective reasoning horizon (optimal number of turns)
    - s: problem complexity (inversely related to single-pass success rate)
    - p: per-turn information gain probability

    We estimate:
    - p from the ratio of concept_recall improvement per additional depth
    - s from the gap between single_pass and optimal RLM performance
    - H_observed from where marginal gains plateau
    """
    # Collect per-depth mean concept_recall
    depth_recalls = defaultdict(list)  # depth -> [concept_recall values]
    single_pass_recalls = []

    for qid, config_metrics in metrics_by_qid.items():
        sp = config_metrics.get("single_pass")
        if sp:
            single_pass_recalls.append(sp.concept_recall)

        for cfg in RLM_CONFIGS:
            m = config_metrics.get(cfg)
            if m:
                depth_recalls[RLM_DEPTH_MAP[cfg]].append(m.concept_recall)

    if not single_pass_recalls:
        return {"error": "No single_pass data found"}

    mean_sp = statistics.mean(single_pass_recalls)
    depth_means = {}
    for d, vals in sorted(depth_recalls.items()):
        depth_means[d] = statistics.mean(vals)

    # Estimate p: per-turn success probability
    # From single_pass (depth=1) to rlm_5 (depth=5), the improvement ratio
    # gives us the information accumulation rate
    cr_1 = mean_sp  # depth 1 (single pass)
    cr_5 = depth_means.get(5, cr_1)
    cr_10 = depth_means.get(10, cr_5)
    cr_20 = depth_means.get(20, cr_10)

    # p estimated as the average per-turn improvement fraction
    # Using a simple exponential decay model: CR(d) = CR_max * (1 - (1-p)^d)
    # where CR_max is the theoretical maximum recall
    # Rearranging: (1-p)^d = 1 - CR(d)/CR_max
    # For CR_max, use 1.0 (perfect recall)
    cr_max = 1.0

    # Estimate p from multiple depth points
    p_estimates = []
    for d, cr in depth_means.items():
        if cr < cr_max and cr > 0:
            # (1-p)^d = 1 - cr/cr_max
            ratio = 1.0 - cr / cr_max
            if ratio > 0 and ratio < 1:
                p_est = 1.0 - ratio ** (1.0 / d)
                if 0 < p_est < 1:
                    p_estimates.append(p_est)

    # Also estimate from single_pass as depth=1
    if cr_1 < cr_max and cr_1 > 0:
        ratio_sp = 1.0 - cr_1 / cr_max
        if 0 < ratio_sp < 1:
            p_estimates.append(1.0 - ratio_sp)

    p_mean = statistics.mean(p_estimates) if p_estimates else 0.5

    # Estimate s: problem complexity
    # s represents the "search space size" — inversely related to single-pass success
    # s = 1 / (1 - mean_sp) when mean_sp < 1
    if mean_sp < 1.0:
        s_estimate = 1.0 / (1.0 - mean_sp)
    else:
        s_estimate = float("inf")

    # Compute theoretical H
    if p_mean > 0 and p_mean < 1 and s_estimate > 1:
        H_theoretical = math.log(s_estimate) / math.log(1.0 / p_mean)
    else:
        H_theoretical = float("nan")

    # Observed optimal depth: where concept_recall peaks
    best_depth = max(depth_means, key=depth_means.get) if depth_means else 10
    H_observed = best_depth

    # Marginal gain ratios
    gain_5_10 = cr_10 - cr_5  # marginal gain from 5->10
    gain_10_20 = cr_20 - cr_10  # marginal gain from 10->20
    gain_1_5 = cr_5 - cr_1  # marginal gain from 1->5
    diminishing_ratio = gain_10_20 / gain_5_10 if gain_5_10 > 0 else float("nan")

    return {
        "single_pass_mean_cr": round(cr_1, 4),
        "depth_mean_concept_recall": {str(d): round(v, 4) for d, v in sorted(depth_means.items())},
        "p_estimates": [round(p, 4) for p in p_estimates],
        "p_mean": round(p_mean, 4),
        "s_estimate": round(s_estimate, 4),
        "H_theoretical": round(H_theoretical, 2) if not math.isnan(H_theoretical) else "NaN",
        "H_observed_optimal_depth": H_observed,
        "marginal_gains": {
            "depth_1_to_5": round(gain_1_5, 4),
            "depth_5_to_10": round(gain_5_10, 4),
            "depth_10_to_20": round(gain_10_20, 4),
            "diminishing_ratio_10_20_vs_5_10": round(diminishing_ratio, 4) if not math.isnan(diminishing_ratio) else "NaN",
        },
        "interpretation": (
            f"Per-turn success probability p={p_mean:.3f}. "
            f"Problem complexity s={s_estimate:.2f}. "
            f"Theoretical horizon H={H_theoretical:.1f} turns. "
            f"Observed optimum at depth={H_observed}. "
            f"Marginal gain ratio (10-20)/(5-10)={diminishing_ratio:.3f} "
            f"({'diminishing' if diminishing_ratio < 1.0 else 'still increasing'})."
        ) if not math.isnan(H_theoretical) and not math.isnan(diminishing_ratio) else "Insufficient data for Basu estimation."
    }


# ═══════════════════════════════════════════════════════════════
# 6. CATEGORY BREAKDOWN
# ═══════════════════════════════════════════════════════════════

def category_analysis(
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]],
) -> Dict[str, Any]:
    """Per-category, per-depth analysis."""
    # category -> config -> [concept_recall]
    cat_config_cr = defaultdict(lambda: defaultdict(list))
    cat_config_ss = defaultdict(lambda: defaultdict(list))
    cat_config_len = defaultdict(lambda: defaultdict(list))
    cat_config_calls = defaultdict(lambda: defaultdict(list))

    for qid, config_metrics in metrics_by_qid.items():
        for cfg, m in config_metrics.items():
            cat = CATEGORY_MAP.get(m.category, m.category)
            cat_config_cr[cat][cfg].append(m.concept_recall)
            if m.semantic_similarity is not None:
                cat_config_ss[cat][cfg].append(m.semantic_similarity)
            cat_config_len[cat][cfg].append(m.answer_words)
            cat_config_calls[cat][cfg].append(m.actual_llm_calls)

    result = {}
    for cat in sorted(cat_config_cr.keys()):
        cat_data = {"concept_recall": {}, "semantic_similarity": {}, "answer_words": {}, "llm_calls": {}}
        for cfg in ALL_CONFIGS:
            cr_vals = cat_config_cr[cat].get(cfg, [])
            ss_vals = cat_config_ss[cat].get(cfg, [])
            len_vals = cat_config_len[cat].get(cfg, [])
            call_vals = cat_config_calls[cat].get(cfg, [])

            if cr_vals:
                cat_data["concept_recall"][cfg] = {
                    "mean": round(statistics.mean(cr_vals), 4),
                    "std": round(statistics.stdev(cr_vals), 4) if len(cr_vals) > 1 else 0.0,
                    "n": len(cr_vals),
                }
            if ss_vals:
                cat_data["semantic_similarity"][cfg] = {
                    "mean": round(statistics.mean(ss_vals), 4),
                    "std": round(statistics.stdev(ss_vals), 4) if len(ss_vals) > 1 else 0.0,
                    "n": len(ss_vals),
                }
            if len_vals:
                cat_data["answer_words"][cfg] = {
                    "mean": round(statistics.mean(len_vals), 1),
                    "median": round(statistics.median(len_vals), 1),
                }
            if call_vals:
                cat_data["llm_calls"][cfg] = {
                    "mean": round(statistics.mean(call_vals), 1),
                    "median": statistics.median(call_vals),
                }

        # RLM marginal gains for this category
        rlm_gains = {}
        for d_low, d_high in [(5, 10), (10, 20)]:
            cfg_low = f"rlm_{d_low}"
            cfg_high = f"rlm_{d_high}"
            cr_low = cat_config_cr[cat].get(cfg_low, [])
            cr_high = cat_config_cr[cat].get(cfg_high, [])
            if cr_low and cr_high:
                rlm_gains[f"{d_low}_to_{d_high}"] = round(
                    statistics.mean(cr_high) - statistics.mean(cr_low), 4
                )
        cat_data["rlm_marginal_gain_cr"] = rlm_gains
        result[cat] = cat_data

    return result


# ═══════════════════════════════════════════════════════════════
# 7. EFFICIENCY ANALYSIS
# ═══════════════════════════════════════════════════════════════

def efficiency_analysis(
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]],
) -> Dict[str, Any]:
    """Compute quality-per-compute metrics."""
    config_efficiency = defaultdict(lambda: {
        "cr_per_call": [],
        "cr_per_second": [],
        "words_per_call": [],
    })

    for qid, config_metrics in metrics_by_qid.items():
        for cfg, m in config_metrics.items():
            calls = max(m.actual_llm_calls, 1)
            latency = max(m.latency_s, 0.1)
            config_efficiency[cfg]["cr_per_call"].append(m.concept_recall / calls)
            config_efficiency[cfg]["cr_per_second"].append(m.concept_recall / latency)
            config_efficiency[cfg]["words_per_call"].append(m.answer_words / calls)

    result = {}
    for cfg in ALL_CONFIGS:
        eff = config_efficiency.get(cfg)
        if not eff or not eff["cr_per_call"]:
            continue
        result[cfg] = {
            "cr_per_call": {
                "mean": round(statistics.mean(eff["cr_per_call"]), 4),
                "std": round(statistics.stdev(eff["cr_per_call"]), 4) if len(eff["cr_per_call"]) > 1 else 0.0,
            },
            "cr_per_second": {
                "mean": round(statistics.mean(eff["cr_per_second"]), 6),
            },
            "words_per_call": {
                "mean": round(statistics.mean(eff["words_per_call"]), 1),
            },
        }
    return result


# ═══════════════════════════════════════════════════════════════
# 8. SATURATION CURVE FITTING
# ═══════════════════════════════════════════════════════════════

def fit_saturation_curve(
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]],
) -> Dict[str, Any]:
    """
    Fit a logarithmic saturation curve to concept_recall vs depth.

    Model: CR(d) = a * ln(d) + b
    This captures the diminishing returns pattern predicted by Basu's theory.

    Also fits exponential saturation: CR(d) = CR_max * (1 - exp(-k*d))
    """
    # Collect (depth, concept_recall) pairs
    depth_cr_pairs = []  # (depth, cr)
    for qid, config_metrics in metrics_by_qid.items():
        sp = config_metrics.get("single_pass")
        if sp:
            depth_cr_pairs.append((1, sp.concept_recall))
        for cfg in RLM_CONFIGS:
            m = config_metrics.get(cfg)
            if m:
                depth_cr_pairs.append((RLM_DEPTH_MAP[cfg], m.concept_recall))

    if len(depth_cr_pairs) < 4:
        return {"error": "Insufficient data points for curve fitting"}

    # Group by depth, compute means
    depth_groups = defaultdict(list)
    for d, cr in depth_cr_pairs:
        depth_groups[d].append(cr)

    depths = sorted(depth_groups.keys())
    mean_crs = [statistics.mean(depth_groups[d]) for d in depths]
    std_crs = [statistics.stdev(depth_groups[d]) if len(depth_groups[d]) > 1 else 0.0 for d in depths]

    # Logarithmic fit: CR = a * ln(d) + b
    ln_depths = [math.log(d) for d in depths]
    n = len(depths)
    sum_x = sum(ln_depths)
    sum_y = sum(mean_crs)
    sum_xy = sum(x * y for x, y in zip(ln_depths, mean_crs))
    sum_x2 = sum(x * x for x in ln_depths)

    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-10:
        a_log, b_log = 0.0, sum_y / n
    else:
        a_log = (n * sum_xy - sum_x * sum_y) / denom
        b_log = (sum_y - a_log * sum_x) / n

    # R-squared for log fit
    ss_res = sum((y - (a_log * math.log(d) + b_log)) ** 2 for d, y in zip(depths, mean_crs))
    ss_tot = sum((y - sum_y / n) ** 2 for y in mean_crs)
    r2_log = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Exponential saturation fit: CR = CR_max * (1 - exp(-k*d))
    # Simple grid search for k given CR_max = max observed + small margin
    cr_max_est = min(max(mean_crs) * 1.1, 1.0)
    best_k = 0.1
    best_sse = float("inf")
    for k_try in [i * 0.01 for i in range(1, 200)]:
        sse = sum(
            (y - cr_max_est * (1.0 - math.exp(-k_try * d))) ** 2
            for d, y in zip(depths, mean_crs)
        )
        if sse < best_sse:
            best_sse = sse
            best_k = k_try

    r2_exp = 1.0 - best_sse / ss_tot if ss_tot > 0 else 0.0

    # Predicted CR at various depths
    predictions = {}
    for d in [1, 5, 10, 15, 20, 30, 50]:
        predictions[str(d)] = {
            "log_model": round(a_log * math.log(d) + b_log, 4),
            "exp_model": round(cr_max_est * (1.0 - math.exp(-best_k * d)), 4),
        }

    return {
        "data_points": {str(d): {"mean_cr": round(cr, 4), "std_cr": round(s, 4), "n": len(depth_groups[d])}
                        for d, cr, s in zip(depths, mean_crs, std_crs)},
        "log_fit": {
            "a": round(a_log, 6),
            "b": round(b_log, 6),
            "equation": f"CR(d) = {a_log:.4f} * ln(d) + {b_log:.4f}",
            "R2": round(r2_log, 4),
        },
        "exp_fit": {
            "CR_max": round(cr_max_est, 4),
            "k": round(best_k, 4),
            "equation": f"CR(d) = {cr_max_est:.4f} * (1 - exp(-{best_k:.4f} * d))",
            "R2": round(r2_exp, 4),
        },
        "predictions": predictions,
        "saturation_depth_90pct": (
            round(-math.log(0.1) / best_k, 1) if best_k > 0 else "N/A"
        ),
        "saturation_depth_95pct": (
            round(-math.log(0.05) / best_k, 1) if best_k > 0 else "N/A"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# 9. V4-5 CROSS-INDEX ANALYSIS (optional)
# ═══════════════════════════════════════════════════════════════

def analyze_v45_saturation(v45_results: List[Dict], gt_index: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze saturation patterns across different index sizes from V4-5."""
    # index -> config -> [concept_recall]
    index_config_cr = defaultdict(lambda: defaultdict(list))

    for r in v45_results:
        if not r.get("answerable", True):
            continue
        answer = r.get("generation", {}).get("answer", "")
        if not answer or len(answer.strip()) < 10:
            continue
        qid = r["question_id"]
        gt = gt_index.get(qid)
        if not gt:
            continue
        cr = compute_concept_recall(answer, gt.get("expected_concepts", []))
        idx = r.get("index_name", "unknown")
        cfg = r["config"]
        index_config_cr[idx][cfg].append(cr)

    result = {}
    for idx in sorted(index_config_cr.keys()):
        idx_data = {}
        for cfg in ALL_CONFIGS:
            vals = index_config_cr[idx].get(cfg, [])
            if vals:
                idx_data[cfg] = {
                    "mean_cr": round(statistics.mean(vals), 4),
                    "n": len(vals),
                }
        if idx_data:
            result[idx] = idx_data

    return result


# ═══════════════════════════════════════════════════════════════
# 10. MARKDOWN REPORT
# ═══════════════════════════════════════════════════════════════

def generate_report(analysis: Dict[str, Any]) -> str:
    """Generate markdown report from analysis results."""
    lines = [
        "# RLM Compute Saturation Analysis",
        "",
        f"Generated: {analysis['timestamp']}",
        f"Data source: V4-4 ({analysis['n_questions_analyzed']} questions, {analysis['n_results_analyzed']} results)",
        "",
        "## 1. Overview",
        "",
        "This analysis examines how information accumulates across RLM recursion depths",
        "(5, 10, 20 turns) to validate Basu's compute saturation theory.",
        "",
    ]

    # Aggregate config comparison
    lines.append("## 2. Config-Level Concept Recall")
    lines.append("")
    lines.append("| Config | Mean CR | Std | Mean Words | Mean LLM Calls |")
    lines.append("|--------|--------:|----:|-----------:|---------------:|")
    agg = analysis.get("aggregate_by_config", {})
    for cfg in ALL_CONFIGS:
        d = agg.get(cfg, {})
        if d:
            lines.append(
                f"| {cfg} | {d.get('mean_cr', 0):.3f} | {d.get('std_cr', 0):.3f} "
                f"| {d.get('mean_words', 0):.0f} | {d.get('mean_llm_calls', 0):.1f} |"
            )
    lines.append("")

    # Marginal gains
    lines.append("## 3. Marginal Gains (Diminishing Returns)")
    lines.append("")
    mg = analysis.get("marginal_gains_summary", {})
    for transition, vals in mg.items():
        lines.append(f"**{transition}:**")
        lines.append(f"  - Mean delta concept_recall: {vals.get('mean_delta_cr', 0):+.4f}")
        lines.append(f"  - Mean delta answer length: {vals.get('mean_delta_words', 0):+.0f} words")
        if "mean_delta_ss" in vals and vals["mean_delta_ss"] is not None:
            lines.append(f"  - Mean delta semantic similarity: {vals['mean_delta_ss']:+.4f}")
        lines.append("")

    # Basu parameters
    lines.append("## 4. Basu's H Estimation")
    lines.append("")
    basu = analysis.get("basu_parameters", {})
    if "error" not in basu:
        lines.append(f"- Per-turn success probability p = {basu.get('p_mean', 'N/A')}")
        lines.append(f"- Problem complexity s = {basu.get('s_estimate', 'N/A')}")
        lines.append(f"- Theoretical horizon H = {basu.get('H_theoretical', 'N/A')} turns")
        lines.append(f"- Observed optimal depth = {basu.get('H_observed_optimal_depth', 'N/A')}")
        lines.append("")
        mg_vals = basu.get("marginal_gains", {})
        lines.append(f"- Gain depth 1->5: {mg_vals.get('depth_1_to_5', 'N/A')}")
        lines.append(f"- Gain depth 5->10: {mg_vals.get('depth_5_to_10', 'N/A')}")
        lines.append(f"- Gain depth 10->20: {mg_vals.get('depth_10_to_20', 'N/A')}")
        lines.append(f"- Diminishing ratio: {mg_vals.get('diminishing_ratio_10_20_vs_5_10', 'N/A')}")
        lines.append("")
        lines.append(f"**Interpretation:** {basu.get('interpretation', '')}")
    else:
        lines.append(f"Error: {basu['error']}")
    lines.append("")

    # Saturation curve
    lines.append("## 5. Saturation Curve Fit")
    lines.append("")
    curve = analysis.get("saturation_curve", {})
    if "error" not in curve:
        log_fit = curve.get("log_fit", {})
        exp_fit = curve.get("exp_fit", {})
        lines.append(f"**Logarithmic model:** {log_fit.get('equation', 'N/A')} (R2={log_fit.get('R2', 'N/A')})")
        lines.append(f"**Exponential model:** {exp_fit.get('equation', 'N/A')} (R2={exp_fit.get('R2', 'N/A')})")
        lines.append(f"**90% saturation depth:** {curve.get('saturation_depth_90pct', 'N/A')} turns")
        lines.append(f"**95% saturation depth:** {curve.get('saturation_depth_95pct', 'N/A')} turns")
        lines.append("")

        # Data points table
        lines.append("| Depth | Mean CR | Std | N |")
        lines.append("|------:|--------:|----:|--:|")
        for d_str, vals in sorted(curve.get("data_points", {}).items(), key=lambda x: int(x[0])):
            lines.append(f"| {d_str} | {vals['mean_cr']:.4f} | {vals['std_cr']:.4f} | {vals['n']} |")
        lines.append("")

        # Predictions table
        lines.append("| Depth | Log Model | Exp Model |")
        lines.append("|------:|----------:|----------:|")
        for d_str, preds in sorted(curve.get("predictions", {}).items(), key=lambda x: int(x[0])):
            lines.append(f"| {d_str} | {preds['log_model']:.4f} | {preds['exp_model']:.4f} |")
    lines.append("")

    # Category analysis
    lines.append("## 6. Category Breakdown")
    lines.append("")
    cat_data = analysis.get("category_analysis", {})
    for cat in ["FR", "CO", "TE", "CD", "SY"]:
        cd = cat_data.get(cat, {})
        if not cd:
            continue
        lines.append(f"### {cat}")
        lines.append("")

        # CR table
        cr_data = cd.get("concept_recall", {})
        if cr_data:
            lines.append("| Config | Mean CR | Std | N |")
            lines.append("|--------|--------:|----:|--:|")
            for cfg in ALL_CONFIGS:
                v = cr_data.get(cfg, {})
                if v:
                    lines.append(f"| {cfg} | {v['mean']:.4f} | {v['std']:.4f} | {v['n']} |")
            lines.append("")

        # Marginal gains
        mg_data = cd.get("rlm_marginal_gain_cr", {})
        if mg_data:
            lines.append(f"RLM marginal gains: {', '.join(f'{k}: {v:+.4f}' for k, v in mg_data.items())}")
            lines.append("")

    # Efficiency
    lines.append("## 7. Compute Efficiency")
    lines.append("")
    eff = analysis.get("efficiency", {})
    lines.append("| Config | CR/Call | CR/Second | Words/Call |")
    lines.append("|--------|-------:|----------:|----------:|")
    for cfg in ALL_CONFIGS:
        e = eff.get(cfg, {})
        if e:
            lines.append(
                f"| {cfg} | {e['cr_per_call']['mean']:.4f} "
                f"| {e['cr_per_second']['mean']:.6f} "
                f"| {e['words_per_call']['mean']:.0f} |"
            )
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="RLM Compute Saturation Analysis")
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Skip semantic similarity computation (faster)")
    parser.add_argument("--include-v45", action="store_true",
                        help="Include V4-5 intermediate results for cross-index analysis")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("RLM Per-Turn Compute Saturation Analysis")
    logger.info("=" * 60)

    # Load data
    logger.info("Loading V4-4 results...")
    v44_results = load_v44_results()
    logger.info(f"  Loaded {len(v44_results)} results")

    logger.info("Loading ground truth...")
    gt_index = load_ground_truth()
    logger.info(f"  Loaded {len(gt_index)} questions")

    # Initialize embedder if needed
    embedder = None
    if not args.skip_embeddings:
        logger.info("Loading BGE-M3 embedder...")
        try:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer("BAAI/bge-m3")
            logger.info("  BGE-M3 loaded successfully")
        except Exception as e:
            logger.warning(f"  Failed to load embedder: {e}. Continuing without semantic similarity.")

    # Compute per-question metrics
    logger.info("Computing per-question metrics...")
    all_metrics: List[QuestionMetrics] = []
    metrics_by_qid: Dict[str, Dict[str, QuestionMetrics]] = defaultdict(dict)

    for r in v44_results:
        qid = r["question_id"]
        gt = gt_index.get(qid)
        if not gt:
            continue
        m = analyze_question(r, gt, embedder)
        if m:
            all_metrics.append(m)
            metrics_by_qid[qid][r["config"]] = m

    logger.info(f"  Computed {len(all_metrics)} metrics across {len(metrics_by_qid)} questions")

    # Aggregate by config
    logger.info("Computing aggregate statistics...")
    aggregate_by_config = {}
    for cfg in ALL_CONFIGS:
        cfg_metrics = [m for m in all_metrics if m.config == cfg]
        if not cfg_metrics:
            continue
        crs = [m.concept_recall for m in cfg_metrics]
        words = [m.answer_words for m in cfg_metrics]
        calls = [m.actual_llm_calls for m in cfg_metrics]
        latencies = [m.latency_s for m in cfg_metrics]

        d = {
            "mean_cr": round(statistics.mean(crs), 4),
            "std_cr": round(statistics.stdev(crs), 4) if len(crs) > 1 else 0.0,
            "median_cr": round(statistics.median(crs), 4),
            "mean_words": round(statistics.mean(words), 1),
            "mean_llm_calls": round(statistics.mean(calls), 1),
            "mean_latency": round(statistics.mean(latencies), 1),
            "n": len(cfg_metrics),
        }

        # Add semantic similarity if available
        ss_vals = [m.semantic_similarity for m in cfg_metrics if m.semantic_similarity is not None]
        if ss_vals:
            d["mean_ss"] = round(statistics.mean(ss_vals), 4)
            d["std_ss"] = round(statistics.stdev(ss_vals), 4) if len(ss_vals) > 1 else 0.0

        # Number overlap
        no_vals = [m.number_overlap for m in cfg_metrics]
        d["mean_number_overlap"] = round(statistics.mean(no_vals), 4)

        aggregate_by_config[cfg] = d

    # Marginal gains
    logger.info("Computing marginal gains...")
    gains = compute_marginal_gains(metrics_by_qid)
    marginal_summary = {}
    for d_low, d_high in [(5, 10), (10, 20)]:
        transition_gains = [g for g in gains if g.depth_low == d_low and g.depth_high == d_high]
        if transition_gains:
            d = {
                "mean_delta_cr": round(statistics.mean([g.delta_concept_recall for g in transition_gains]), 4),
                "std_delta_cr": round(statistics.stdev([g.delta_concept_recall for g in transition_gains]), 4) if len(transition_gains) > 1 else 0.0,
                "mean_delta_words": round(statistics.mean([g.delta_answer_length for g in transition_gains]), 1),
                "mean_delta_citations": round(statistics.mean([g.delta_citations for g in transition_gains]), 2),
                "mean_delta_latency": round(statistics.mean([g.delta_latency for g in transition_gains]), 1),
                "n_questions": len(transition_gains),
                "pct_improved": round(
                    sum(1 for g in transition_gains if g.delta_concept_recall > 0) / len(transition_gains) * 100, 1
                ),
                "pct_degraded": round(
                    sum(1 for g in transition_gains if g.delta_concept_recall < 0) / len(transition_gains) * 100, 1
                ),
                "pct_unchanged": round(
                    sum(1 for g in transition_gains if g.delta_concept_recall == 0) / len(transition_gains) * 100, 1
                ),
            }
            ss_deltas = [g.delta_semantic_sim for g in transition_gains if g.delta_semantic_sim is not None]
            if ss_deltas:
                d["mean_delta_ss"] = round(statistics.mean(ss_deltas), 4)
            marginal_summary[f"depth_{d_low}_to_{d_high}"] = d

    # Basu estimation
    logger.info("Estimating Basu's parameters...")
    basu = estimate_basu_parameters(metrics_by_qid)

    # Saturation curve
    logger.info("Fitting saturation curve...")
    curve = fit_saturation_curve(metrics_by_qid)

    # Category analysis
    logger.info("Computing category breakdown...")
    cat_analysis = category_analysis(metrics_by_qid)

    # Efficiency
    logger.info("Computing efficiency metrics...")
    eff = efficiency_analysis(metrics_by_qid)

    # V4-5 cross-index (optional)
    v45_analysis = None
    if args.include_v45:
        logger.info("Loading V4-5 intermediate results...")
        v45_results = load_v45_intermediate()
        if v45_results:
            logger.info(f"  Loaded {len(v45_results)} V4-5 results")
            v45_analysis = analyze_v45_saturation(v45_results, gt_index)
        else:
            logger.warning("  No V4-5 results found")

    # Assemble output
    analysis = {
        "experiment": "v4_perturn_analysis",
        "timestamp": datetime.now().isoformat(),
        "data_source": "v4_4_generation_latest.json",
        "n_questions_analyzed": len(metrics_by_qid),
        "n_results_analyzed": len(all_metrics),
        "has_semantic_similarity": embedder is not None,
        "aggregate_by_config": aggregate_by_config,
        "marginal_gains_summary": marginal_summary,
        "basu_parameters": basu,
        "saturation_curve": curve,
        "category_analysis": cat_analysis,
        "efficiency": eff,
    }
    if v45_analysis:
        analysis["v45_cross_index"] = v45_analysis

    # Per-question detail (for downstream analysis)
    analysis["per_question_detail"] = [
        asdict(m) for m in all_metrics
    ]

    # Save
    logger.info("Saving results...")
    json_path, latest_path = save_v4_results(analysis, "v4_perturn_analysis")
    logger.info(f"  JSON: {json_path}")
    logger.info(f"  Latest: {latest_path}")

    # Generate report
    report = generate_report(analysis)
    md_path = save_v4_markdown(report, "v4_perturn_analysis")
    logger.info(f"  Report: {md_path}")

    # Print key findings
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)

    print("\n--- Aggregate Concept Recall by Config ---")
    for cfg in ALL_CONFIGS:
        d = aggregate_by_config.get(cfg, {})
        if d:
            ss_str = f", SS={d['mean_ss']:.3f}" if "mean_ss" in d else ""
            print(f"  {cfg:15s}: CR={d['mean_cr']:.3f} +/- {d['std_cr']:.3f}{ss_str}, "
                  f"words={d['mean_words']:.0f}, calls={d['mean_llm_calls']:.1f}")

    print("\n--- Marginal Gains ---")
    for transition, vals in marginal_summary.items():
        print(f"  {transition}: delta_CR={vals['mean_delta_cr']:+.4f} "
              f"({vals['pct_improved']:.0f}% improved, {vals['pct_degraded']:.0f}% degraded)")

    print("\n--- Basu's H Estimation ---")
    if "error" not in basu:
        print(f"  p (per-turn success) = {basu['p_mean']}")
        print(f"  s (complexity)       = {basu['s_estimate']}")
        print(f"  H (theoretical)      = {basu['H_theoretical']} turns")
        print(f"  H (observed optimum) = {basu['H_observed_optimal_depth']}")

    print("\n--- Saturation Curve ---")
    if "error" not in curve:
        print(f"  Log fit R2 = {curve['log_fit']['R2']}")
        print(f"  Exp fit R2 = {curve['exp_fit']['R2']}")
        print(f"  90% saturation at {curve['saturation_depth_90pct']} turns")
        print(f"  95% saturation at {curve['saturation_depth_95pct']} turns")

    print("\n--- Category Winners (RLM depth with highest mean CR) ---")
    for cat in ["FR", "CO", "TE", "CD", "SY"]:
        cd = cat_analysis.get(cat, {})
        cr_data = cd.get("concept_recall", {})
        if cr_data:
            best = max(
                ((cfg, v["mean"]) for cfg, v in cr_data.items()),
                key=lambda x: x[1],
            )
            print(f"  {cat}: best={best[0]} (CR={best[1]:.3f})")

    print(f"\nResults saved to: {latest_path}")
    print(f"Report saved to: {md_path}")


if __name__ == "__main__":
    main()
