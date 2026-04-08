#!/usr/bin/env python3
"""
Deterministic Scoring System for V4 Experiments

Computes objective, reproducible quality scores from ground truth,
replacing subjective LLM-judge scoring with threshold-based metrics.

Architecture:
  1. Compute objective metrics per answer (concept recall, semantic similarity,
     number overlap, citation coverage)
  2. Map each metric to a 0-5 score using published thresholds
  3. Compare with existing LLM judge scores (agreement analysis)
  4. Output JSON + markdown report

Metrics → Score Dimensions:
  - Correctness  ← semantic_similarity (0.6) + number_overlap (0.4)
  - Completeness ← concept_recall (direct mapping)
  - Faithfulness ← concept_recall × semantic_similarity (proxy)
  - Citation Quality ← source_coverage (0.5) + has_citations (0.25) + density_norm (0.25)

For OOD (unanswerable) questions:
  - Refusal Accuracy ← keyword detection + answer length
  - Hallucination Avoidance ← absence of citations + specific claims
  - Explanation Quality ← presence of explanatory reasoning

Usage:
  # Score V4-4 results
  uv run python publication/scripts/analysis_deterministic_scorer.py \\
      --input publication/results/v4_4_generation_latest.json

  # Score V4-5 intermediate results
  uv run python publication/scripts/analysis_deterministic_scorer.py \\
      --input publication/results/v4_5_intermediate.json

  # Skip embeddings (faster, no semantic similarity)
  uv run python publication/scripts/analysis_deterministic_scorer.py \\
      --input results.json --skip-embeddings

  # Show threshold calibration info
  uv run python publication/scripts/analysis_deterministic_scorer.py \\
      --input results.json --show-distributions
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# ── Project path setup ──
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from exp_common import (
    load_ground_truth,
    V4_GROUND_TRUTH,
    V4_RESULTS_DIR,
    save_v4_results,
    save_v4_markdown,
)

logger = logging.getLogger("det_scorer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# ═══════════════════════════════════════════════════════════════
# 1. PUBLISHED THRESHOLDS (reproducibility-critical)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ThresholdConfig:
    """Published threshold boundaries for deterministic scoring.

    Each tuple defines (min_inclusive, max_exclusive) for scores 0-5.
    These thresholds are fixed and published in the paper for reproducibility.
    """
    # Correctness: based on semantic similarity (0.0-1.0 cosine)
    # + number overlap for factual precision
    correctness_thresholds: Tuple[float, ...] = (0.0, 0.40, 0.55, 0.65, 0.75, 0.85)
    # Score: <0.40→0, 0.40-0.55→1, 0.55-0.65→2, 0.65-0.75→3, 0.75-0.85→4, ≥0.85→5

    # Completeness: based on concept recall (0.0-1.0 fraction)
    completeness_thresholds: Tuple[float, ...] = (0.0, 0.01, 0.21, 0.41, 0.61, 0.81)
    # Score: 0%→0, 1-20%→1, 21-40%→2, 41-60%→3, 61-80%→4, 81-100%→5

    # Faithfulness: concept_recall × semantic_similarity product (0.0-1.0)
    faithfulness_thresholds: Tuple[float, ...] = (0.0, 0.10, 0.25, 0.40, 0.55, 0.70)
    # Score: <0.10→0, 0.10-0.25→1, 0.25-0.40→2, 0.40-0.55→3, 0.55-0.70→4, ≥0.70→5

    # Citation quality: composite of source_coverage, has_citations, density (0.0-1.0)
    citation_thresholds: Tuple[float, ...] = (0.0, 0.01, 0.21, 0.41, 0.61, 0.81)
    # Score: 0→0, 0.01-0.20→1, 0.21-0.40→2, 0.41-0.60→3, 0.61-0.80→4, ≥0.81→5

    # Number overlap weight in correctness (vs semantic similarity)
    number_weight: float = 0.4
    semantic_weight: float = 0.6

    # Citation composite weights
    cite_source_weight: float = 0.50
    cite_has_weight: float = 0.25
    cite_density_weight: float = 0.25
    cite_density_cap: float = 10.0  # citations per 100 words cap


DEFAULT_THRESHOLDS = ThresholdConfig()


# ═══════════════════════════════════════════════════════════════
# 2. OBJECTIVE METRIC COMPUTATION
# ═══════════════════════════════════════════════════════════════

def compute_concept_recall(answer: str, expected_concepts: List[str]) -> float:
    """Fraction of expected concepts found in the answer.

    Uses case-insensitive matching with:
    - Exact substring match
    - Multi-word concept: all significant words (>3 chars) present
    - Hyphen normalization ("best-practice" ↔ "best practice")

    Returns 0.0-1.0.
    """
    if not expected_concepts:
        return 1.0

    answer_lower = answer.lower()
    found = 0
    for concept in expected_concepts:
        concept_lower = concept.lower()
        # Exact match
        if concept_lower in answer_lower:
            found += 1
            continue
        # Multi-word: all significant words present
        words = concept_lower.split()
        if len(words) > 1:
            sig_words = [w for w in words if len(w) > 3]
            if sig_words and all(w in answer_lower for w in sig_words):
                found += 1
                continue
        # Hyphen normalization
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
    """Extract numeric values with optional units from text.

    Returns normalized number strings for comparison.
    Handles: integers, decimals, percentages, units (TB, GB, MB, etc.)
    """
    numbers = set()

    # Pattern: number with optional unit
    # Matches: 1.4, 1378, 90x, 1.4 TB, 98%, 0.694
    for m in re.finditer(
        r'(\d+\.?\d*)\s*(%|[A-Za-z]{1,5}(?:/[A-Za-z]{1,5})?)?',
        text
    ):
        num_str = m.group(1)
        unit = (m.group(2) or "").lower().strip()

        # Normalize: remove trailing zeros after decimal
        try:
            num_val = float(num_str)
            # Store both raw and normalized forms
            numbers.add(num_str)
            if unit:
                numbers.add(f"{num_str}{unit}")
            # Also store integer form if it's a whole number
            if num_val == int(num_val) and '.' in num_str:
                numbers.add(str(int(num_val)))
        except ValueError:
            continue

    return numbers


def compute_number_overlap(expected_answer: str, generated_answer: str) -> float:
    """Fraction of numbers from expected answer found in generated answer.

    Critical for factual_recall questions where specific values matter.
    Returns 0.0-1.0. Returns 1.0 if no numbers in expected (N/A).
    """
    expected_nums = extract_numbers(expected_answer)
    if not expected_nums:
        return 1.0  # No numbers to check

    generated_nums = extract_numbers(generated_answer)

    # Also check raw text containment for numbers (handles formatting differences)
    gen_lower = generated_answer.lower()
    found = 0
    for num in expected_nums:
        if num in generated_nums:
            found += 1
        elif num in gen_lower:
            found += 1

    return min(found / len(expected_nums), 1.0)


def compute_citation_metrics(
    answer: str,
    source_files: List[str],
) -> Dict[str, float]:
    """Compute deterministic citation quality metrics.

    Returns:
      - has_citations: 1.0 if any citation markers found, 0.0 otherwise
      - source_coverage: fraction of expected source_files mentioned/cited
      - citation_density: citations per 100 words (capped)
      - total_citations: raw count
    """
    # Count citations: [source:page], [N], [source.pdf], etc.
    inline_cites = re.findall(r'\[([^\]]+\.pdf):?\d*\]', answer, re.IGNORECASE)
    numbered_refs = re.findall(r'\[(\d+)\]', answer)
    total = len(inline_cites) + len(numbered_refs)

    has_citations = 1.0 if total > 0 else 0.0

    # Source coverage
    source_coverage = 0.0
    if source_files:
        answer_lower = answer.lower()
        found = 0
        for sf in source_files:
            name = sf.replace('.pdf', '').lower()
            # Remove leading number prefix (e.g., "01_sarek" -> "sarek")
            parts = name.split('_', 1)
            name_clean = parts[1] if len(parts) > 1 else name
            if name_clean in answer_lower or sf.lower() in answer_lower:
                found += 1
        source_coverage = found / len(source_files)

    # Citation density (per 100 words)
    word_count = max(len(answer.split()), 1)
    density = (total / word_count) * 100

    return {
        "has_citations": has_citations,
        "source_coverage": source_coverage,
        "citation_density": density,
        "total_citations": float(total),
    }


def compute_semantic_similarity(
    expected: str,
    generated: str,
    embedder,
) -> float:
    """Cosine similarity between expected and generated answers using BGE-M3.

    Returns 0.0-1.0 (BGE-M3 embeddings are normalized).
    """
    if not expected or not generated:
        return 0.0

    exp_trunc = expected[:2000]
    gen_trunc = generated[:2000]

    embeddings = embedder.embed_documents([exp_trunc, gen_trunc])
    sim = float(np.dot(embeddings[0], embeddings[1]))
    return max(0.0, min(sim, 1.0))  # Clamp


# ═══════════════════════════════════════════════════════════════
# 3. OOD (UNANSWERABLE) DETERMINISTIC SCORING
# ═══════════════════════════════════════════════════════════════

# Refusal indicators — phrases that indicate the system recognizes
# the question cannot be answered from available documents
REFUSAL_STRONG = [
    "cannot answer", "can't answer", "unable to answer",
    "not available in", "not found in", "not present in",
    "not covered in", "not in the available", "not in the corpus",
    "no relevant information", "no information available",
    "outside the scope", "beyond the scope",
    "does not contain", "do not contain",
    "cannot be answered", "can't be answered",
    "no documents", "no relevant documents",
]

REFUSAL_WEAK = [
    "not enough information", "insufficient information",
    "limited information", "may not", "might not",
    "i don't have", "i do not have",
    "unclear from", "not explicitly",
    "cannot determine", "cannot confirm",
    "no specific", "no direct",
]

EXPLANATION_PHRASES = [
    "because", "the available documents", "the corpus",
    "the provided", "the indexed", "none of the",
    "topic is not", "subject is not", "not covered",
    "would require", "additional sources", "other sources",
    "outside", "beyond", "different domain",
]


def score_ood_refusal(answer: str) -> Dict[str, Any]:
    """Deterministic scoring of OOD question handling.

    Returns metrics and 0-5 scores for:
      - refusal_accuracy: Did it recognize the question is unanswerable?
      - hallucination_avoidance: Did it avoid fabricating content?
      - explanation_quality: Did it explain why it can't answer?
    """
    answer_lower = answer.lower()
    word_count = len(answer.split())

    # --- Refusal detection ---
    strong_hits = sum(1 for p in REFUSAL_STRONG if p in answer_lower)
    weak_hits = sum(1 for p in REFUSAL_WEAK if p in answer_lower)
    has_strong_refusal = strong_hits > 0
    has_weak_refusal = weak_hits > 0

    # --- Hallucination indicators ---
    # Citations in OOD answers are BAD (citing sources for info that isn't there)
    cite_count = len(re.findall(r'\[\d+\]', answer)) + len(
        re.findall(r'\[[^\]]+\.pdf', answer, re.IGNORECASE)
    )
    has_citations = cite_count > 0

    # Specific numbers/data (potential fabrication if present in OOD answer)
    specific_numbers = len(re.findall(r'\b\d+\.?\d*\s*(%|GB|TB|MB|bp|kb)\b', answer, re.IGNORECASE))

    # --- Explanation detection ---
    explanation_hits = sum(1 for p in EXPLANATION_PHRASES if p in answer_lower)

    # === Score: Refusal Accuracy (0-5) ===
    if has_strong_refusal and word_count < 200:
        refusal_score = 5
    elif has_strong_refusal and word_count < 400:
        refusal_score = 4
    elif has_strong_refusal:
        # Refused but then gave a long answer anyway
        refusal_score = 3
    elif has_weak_refusal and word_count < 300:
        refusal_score = 3
    elif has_weak_refusal:
        refusal_score = 2
    elif word_count < 50:
        # Very short answer without explicit refusal — could be implicit
        refusal_score = 2
    elif word_count < 150:
        refusal_score = 1
    else:
        # Long answer with no refusal indicators
        refusal_score = 0

    # === Score: Hallucination Avoidance (0-5) ===
    if not has_citations and specific_numbers == 0 and has_strong_refusal:
        hallucination_score = 5
    elif not has_citations and specific_numbers <= 1:
        hallucination_score = 4
    elif not has_citations and specific_numbers <= 3:
        hallucination_score = 3
    elif has_citations and cite_count <= 2:
        hallucination_score = 2
    elif has_citations and cite_count <= 5:
        hallucination_score = 1
    else:
        hallucination_score = 0

    # === Score: Explanation Quality (0-5) ===
    if explanation_hits >= 3 and has_strong_refusal:
        explanation_score = 5
    elif explanation_hits >= 2 and (has_strong_refusal or has_weak_refusal):
        explanation_score = 4
    elif explanation_hits >= 1 and has_strong_refusal:
        explanation_score = 4
    elif explanation_hits >= 1:
        explanation_score = 3
    elif has_weak_refusal:
        explanation_score = 2
    elif has_strong_refusal:
        # Refused but no explanation why
        explanation_score = 2
    else:
        if word_count < 50:
            explanation_score = 1  # Implicit refusal, no explanation
        else:
            explanation_score = 0

    return {
        "metrics": {
            "strong_refusal_hits": strong_hits,
            "weak_refusal_hits": weak_hits,
            "has_strong_refusal": has_strong_refusal,
            "has_weak_refusal": has_weak_refusal,
            "citation_count": cite_count,
            "specific_numbers": specific_numbers,
            "explanation_hits": explanation_hits,
            "word_count": word_count,
        },
        "scores": {
            "refusal_accuracy": refusal_score,
            "hallucination_avoidance": hallucination_score,
            "explanation_quality": explanation_score,
        },
    }


# ═══════════════════════════════════════════════════════════════
# 4. THRESHOLD-BASED SCORE MAPPING
# ═══════════════════════════════════════════════════════════════

def metric_to_score(value: float, thresholds: Tuple[float, ...]) -> int:
    """Map a 0.0-1.0 metric to a 0-5 integer score using thresholds.

    thresholds is a tuple of 6 values (boundaries for scores 0-5).
    Score N is assigned when thresholds[N] <= value < thresholds[N+1].
    Score 5 is assigned when value >= thresholds[5].
    """
    for i in range(5, 0, -1):
        if value >= thresholds[i]:
            return i
    return 0


def score_answerable(
    concept_recall: float,
    semantic_similarity: float,
    number_overlap: float,
    citation_metrics: Dict[str, float],
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
) -> Dict[str, Any]:
    """Compute deterministic 0-5 scores for an answerable question.

    Returns dict with raw metrics, composite metrics, and integer scores.
    """
    # Correctness composite: semantic similarity + number overlap
    correctness_metric = (
        thresholds.semantic_weight * semantic_similarity
        + thresholds.number_weight * number_overlap
    )

    # Completeness: direct concept recall
    completeness_metric = concept_recall

    # Faithfulness proxy: concept_recall × semantic_similarity
    # Intuition: faithful answers cover expected concepts AND align with
    # expected text. Low on either → likely hallucinated or off-topic.
    faithfulness_metric = concept_recall * semantic_similarity

    # Citation quality composite
    density_norm = min(
        citation_metrics["citation_density"] / thresholds.cite_density_cap, 1.0
    )
    citation_metric = (
        thresholds.cite_source_weight * citation_metrics["source_coverage"]
        + thresholds.cite_has_weight * citation_metrics["has_citations"]
        + thresholds.cite_density_weight * density_norm
    )

    # Map to 0-5
    scores = {
        "correctness": metric_to_score(correctness_metric, thresholds.correctness_thresholds),
        "completeness": metric_to_score(completeness_metric, thresholds.completeness_thresholds),
        "faithfulness": metric_to_score(faithfulness_metric, thresholds.faithfulness_thresholds),
        "citation_quality": metric_to_score(citation_metric, thresholds.citation_thresholds),
    }

    metrics = {
        "concept_recall": round(concept_recall, 4),
        "semantic_similarity": round(semantic_similarity, 4),
        "number_overlap": round(number_overlap, 4),
        "correctness_composite": round(correctness_metric, 4),
        "completeness_metric": round(completeness_metric, 4),
        "faithfulness_composite": round(faithfulness_metric, 4),
        "citation_composite": round(citation_metric, 4),
        "source_coverage": round(citation_metrics["source_coverage"], 4),
        "has_citations": citation_metrics["has_citations"],
        "citation_density": round(citation_metrics["citation_density"], 4),
        "total_citations": int(citation_metrics["total_citations"]),
    }

    return {"metrics": metrics, "scores": scores}


# ═══════════════════════════════════════════════════════════════
# 5. AGREEMENT ANALYSIS (deterministic vs LLM judge)
# ═══════════════════════════════════════════════════════════════

def analyze_agreement(
    results: List[Dict],
) -> Dict[str, Any]:
    """Compute agreement statistics between deterministic and LLM judge scores.

    For answerable questions: correctness, completeness, faithfulness, citation_quality
    For OOD questions: refusal_accuracy, hallucination_avoidance, explanation_quality
    """
    from scipy.stats import spearmanr

    # Separate answerable and OOD
    answerable = [r for r in results if r.get("answerable", True)]
    ood = [r for r in results if not r.get("answerable", True)]

    analysis = {"n_total": len(results), "n_answerable": len(answerable), "n_ood": len(ood)}

    # --- Answerable agreement ---
    ans_dims = ["correctness", "completeness", "faithfulness", "citation_quality"]
    for dim in ans_dims:
        det_scores = []
        judge_scores = []
        for r in answerable:
            ds = r.get("deterministic_scores", {}).get(dim)
            js = r.get("judge_scores", {}).get(dim)
            if ds is not None and js is not None:
                det_scores.append(ds)
                judge_scores.append(js)

        if len(det_scores) < 5:
            analysis[f"answerable_{dim}"] = {"n": len(det_scores), "note": "insufficient data"}
            continue

        det_arr = np.array(det_scores, dtype=float)
        judge_arr = np.array(judge_scores, dtype=float)

        exact = int(np.sum(det_arr == judge_arr))
        within_1 = int(np.sum(np.abs(det_arr - judge_arr) <= 1))
        within_2 = int(np.sum(np.abs(det_arr - judge_arr) <= 2))
        mae = float(np.mean(np.abs(det_arr - judge_arr)))
        n = len(det_scores)

        # Spearman correlation
        if np.std(det_arr) > 0 and np.std(judge_arr) > 0:
            rho, p_val = spearmanr(det_arr, judge_arr)
        else:
            rho, p_val = 0.0, 1.0

        analysis[f"answerable_{dim}"] = {
            "n": n,
            "exact_agreement": round(exact / n, 4),
            "within_1_agreement": round(within_1 / n, 4),
            "within_2_agreement": round(within_2 / n, 4),
            "mae": round(mae, 4),
            "spearman_rho": round(float(rho), 4),
            "spearman_p": round(float(p_val), 6),
            "det_mean": round(float(np.mean(det_arr)), 2),
            "judge_mean": round(float(np.mean(judge_arr)), 2),
            "det_std": round(float(np.std(det_arr)), 2),
            "judge_std": round(float(np.std(judge_arr)), 2),
        }

    # --- OOD agreement ---
    ood_dims = ["refusal_accuracy", "hallucination_avoidance", "explanation_quality"]
    for dim in ood_dims:
        det_scores = []
        judge_scores = []
        for r in ood:
            ds = r.get("deterministic_scores", {}).get(dim)
            js = r.get("judge_scores", {}).get(dim)
            if ds is not None and js is not None:
                det_scores.append(ds)
                judge_scores.append(js)

        if len(det_scores) < 5:
            analysis[f"ood_{dim}"] = {"n": len(det_scores), "note": "insufficient data"}
            continue

        det_arr = np.array(det_scores, dtype=float)
        judge_arr = np.array(judge_scores, dtype=float)

        exact = int(np.sum(det_arr == judge_arr))
        within_1 = int(np.sum(np.abs(det_arr - judge_arr) <= 1))
        mae = float(np.mean(np.abs(det_arr - judge_arr)))
        n = len(det_scores)

        if np.std(det_arr) > 0 and np.std(judge_arr) > 0:
            rho, p_val = spearmanr(det_arr, judge_arr)
        else:
            rho, p_val = 0.0, 1.0

        analysis[f"ood_{dim}"] = {
            "n": n,
            "exact_agreement": round(exact / n, 4),
            "within_1_agreement": round(within_1 / n, 4),
            "mae": round(mae, 4),
            "spearman_rho": round(float(rho), 4),
            "spearman_p": round(float(p_val), 6),
            "det_mean": round(float(np.mean(det_arr)), 2),
            "judge_mean": round(float(np.mean(judge_arr)), 2),
        }

    return analysis


# ═══════════════════════════════════════════════════════════════
# 6. MAIN SCORING PIPELINE
# ═══════════════════════════════════════════════════════════════

def load_results(path: Path) -> Tuple[List[Dict], Dict]:
    """Load V4-4 or V4-5 results. Returns (results_list, metadata)."""
    data = json.load(open(path))

    # V4-4 format: per_question_results
    if "per_question_results" in data:
        results = data["per_question_results"]
        meta = {k: v for k, v in data.items() if k != "per_question_results"}
    # V4-5 format: results
    elif "results" in data:
        results = data["results"]
        meta = {k: v for k, v in data.items() if k != "results"}
    else:
        raise ValueError(f"Unknown result format in {path}")

    logger.info(f"Loaded {len(results)} results from {path.name}")
    return results, meta


def score_all(
    results: List[Dict],
    gt_path: Path,
    embedder=None,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    show_distributions: bool = False,
) -> List[Dict]:
    """Score all results deterministically.

    Args:
        results: List of result dicts from V4-4 or V4-5
        gt_path: Path to ground_truth_v4.json
        embedder: Optional embedding engine for semantic similarity
        thresholds: Threshold configuration
        show_distributions: If True, log metric distributions

    Returns:
        List of scored result dicts (original fields + deterministic_scores + objective_metrics)
    """
    # Load ground truth
    gt_all = load_ground_truth(gt_path, answerable_only=False)
    gt_lookup = {q["id"]: q for q in gt_all}
    logger.info(f"Loaded {len(gt_lookup)} ground truth questions")

    scored = []
    # Track metric distributions for calibration
    metric_values = defaultdict(list)

    for i, r in enumerate(results):
        qid = r["question_id"]
        gt = gt_lookup.get(qid)
        if not gt:
            logger.warning(f"No ground truth for {qid}, skipping")
            continue

        # Extract generated answer
        answer = ""
        if isinstance(r.get("generation"), dict):
            answer = r["generation"].get("answer", "")
        elif isinstance(r.get("generation"), str):
            answer = r["generation"]

        is_answerable = r.get("answerable", gt.get("answerable", True))

        # Build scored result (preserve original fields)
        scored_r = {
            "question_id": qid,
            "config": r.get("config", "unknown"),
            "index_name": r.get("index_name", ""),
            "category": r.get("category", gt.get("category", "")),
            "difficulty": r.get("difficulty", gt.get("difficulty", "")),
            "answerable": is_answerable,
            "judge_scores": r.get("judge_scores", {}),
            "existing_citation_metrics": r.get("citation_metrics", {}),
        }

        if not answer or r.get("generation", {}).get("error"):
            # No answer generated — score 0 across the board
            if is_answerable:
                scored_r["deterministic_scores"] = {
                    "correctness": 0, "completeness": 0,
                    "faithfulness": 0, "citation_quality": 0,
                }
                scored_r["objective_metrics"] = {
                    "concept_recall": 0.0, "semantic_similarity": 0.0,
                    "number_overlap": 0.0, "correctness_composite": 0.0,
                    "completeness_metric": 0.0, "faithfulness_composite": 0.0,
                    "citation_composite": 0.0, "source_coverage": 0.0,
                    "has_citations": 0.0, "citation_density": 0.0,
                    "total_citations": 0,
                }
            else:
                # No answer for OOD = implicit refusal (score varies)
                scored_r["deterministic_scores"] = {
                    "refusal_accuracy": 3, "hallucination_avoidance": 5,
                    "explanation_quality": 0,
                }
                scored_r["objective_metrics"] = {"word_count": 0, "empty_answer": True}
            scored.append(scored_r)
            continue

        if is_answerable:
            # --- Answerable question scoring ---
            expected_answer = gt.get("expected_answer", "")
            expected_concepts = gt.get("expected_concepts", [])
            source_files = gt.get("source_files", [])

            # Compute metrics
            concept_recall = compute_concept_recall(answer, expected_concepts)
            number_overlap = compute_number_overlap(expected_answer, answer)
            cite_metrics = compute_citation_metrics(answer, source_files)

            # Semantic similarity (if embedder available)
            if embedder:
                sem_sim = compute_semantic_similarity(expected_answer, answer, embedder)
            else:
                sem_sim = 0.5  # Neutral default when embeddings unavailable

            # Score
            result = score_answerable(
                concept_recall, sem_sim, number_overlap, cite_metrics, thresholds
            )
            scored_r["objective_metrics"] = result["metrics"]
            scored_r["deterministic_scores"] = result["scores"]

            # Track for distributions
            for k, v in result["metrics"].items():
                metric_values[k].append(v)

        else:
            # --- OOD question scoring ---
            ood_result = score_ood_refusal(answer)
            scored_r["objective_metrics"] = ood_result["metrics"]
            scored_r["deterministic_scores"] = ood_result["scores"]

        scored.append(scored_r)

        if (i + 1) % 50 == 0:
            logger.info(f"  Scored {i+1}/{len(results)}")

    logger.info(f"Scored {len(scored)}/{len(results)} results")

    if show_distributions and metric_values:
        logger.info("\n=== Metric Distributions (answerable only) ===")
        for metric, vals in sorted(metric_values.items()):
            arr = np.array(vals)
            logger.info(
                f"  {metric:25s}: mean={np.mean(arr):.3f}  "
                f"median={np.median(arr):.3f}  "
                f"std={np.std(arr):.3f}  "
                f"min={np.min(arr):.3f}  max={np.max(arr):.3f}"
            )

    return scored


# ═══════════════════════════════════════════════════════════════
# 7. REPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_report(
    scored: List[Dict],
    agreement: Dict,
    meta: Dict,
    thresholds: ThresholdConfig,
    input_file: str,
) -> str:
    """Generate comprehensive markdown report."""
    lines = [
        "# Deterministic Scoring Report",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Input**: `{input_file}`",
        f"**Total results scored**: {len(scored)}",
        f"**Gen model**: {meta.get('gen_model', 'N/A')}",
        f"**Methodology**: Threshold-based deterministic scoring from ground truth metrics",
        "",
    ]

    # --- Published thresholds ---
    lines.extend([
        "## 1. Published Thresholds",
        "",
        "All scores are deterministic and reproducible using these thresholds:",
        "",
        "### Answerable Questions",
        "",
        "| Score | Correctness (sem_sim×0.6 + num_overlap×0.4) | Completeness (concept_recall) | Faithfulness (recall × sim) | Citation Quality (composite) |",
        "|:-----:|:---:|:---:|:---:|:---:|",
    ])
    t = thresholds
    labels = ["0", "1", "2", "3", "4", "5"]
    for i in range(6):
        lo = [t.correctness_thresholds, t.completeness_thresholds,
              t.faithfulness_thresholds, t.citation_thresholds]
        ranges = []
        for th in lo:
            if i < 5:
                ranges.append(f"{th[i]:.2f} – {th[i+1]:.2f}")
            else:
                ranges.append(f"≥ {th[i]:.2f}")
        lines.append(f"| **{labels[i]}** | {ranges[0]} | {ranges[1]} | {ranges[2]} | {ranges[3]} |")
    lines.append("")

    # --- Score distributions ---
    answerable = [r for r in scored if r.get("answerable", True)]
    ood = [r for r in scored if not r.get("answerable", True)]

    if answerable:
        lines.extend(["## 2. Answerable Questions — Score Summary", ""])

        # By config
        configs = sorted(set(r["config"] for r in answerable))
        dims = ["correctness", "completeness", "faithfulness", "citation_quality"]

        lines.append("### By Configuration (Deterministic Scores)")
        lines.append("")
        lines.append("| Config | N | Correctness | Completeness | Faithfulness | Citation | Mean |")
        lines.append("|--------|--:|:----------:|:-----------:|:-----------:|:--------:|:----:|")

        for cfg in configs:
            cfg_results = [r for r in answerable if r["config"] == cfg]
            n = len(cfg_results)
            means = {}
            for dim in dims:
                vals = [r["deterministic_scores"].get(dim, 0) for r in cfg_results]
                means[dim] = np.mean(vals) if vals else 0
            overall = np.mean(list(means.values()))
            lines.append(
                f"| {cfg} | {n} | {means['correctness']:.2f} | "
                f"{means['completeness']:.2f} | {means['faithfulness']:.2f} | "
                f"{means['citation_quality']:.2f} | {overall:.2f} |"
            )
        lines.append("")

        # By category
        categories = sorted(set(r["category"] for r in answerable))
        lines.append("### By Category (Deterministic Scores)")
        lines.append("")
        lines.append("| Category | N | Correctness | Completeness | Faithfulness | Citation |")
        lines.append("|----------|--:|:----------:|:-----------:|:-----------:|:--------:|")

        for cat in categories:
            cat_results = [r for r in answerable if r["category"] == cat]
            n = len(cat_results)
            means = {}
            for dim in dims:
                vals = [r["deterministic_scores"].get(dim, 0) for r in cat_results]
                means[dim] = np.mean(vals)
            lines.append(
                f"| {cat} | {n} | {means['correctness']:.2f} | "
                f"{means['completeness']:.2f} | {means['faithfulness']:.2f} | "
                f"{means['citation_quality']:.2f} |"
            )
        lines.append("")

    # --- OOD Summary ---
    if ood:
        lines.extend(["## 3. OOD Questions — Score Summary", ""])
        ood_dims = ["refusal_accuracy", "hallucination_avoidance", "explanation_quality"]

        configs = sorted(set(r["config"] for r in ood))
        lines.append("| Config | N | Refusal Acc | Halluc. Avoid | Explanation |")
        lines.append("|--------|--:|:----------:|:------------:|:----------:|")

        for cfg in configs:
            cfg_results = [r for r in ood if r["config"] == cfg]
            n = len(cfg_results)
            means = {}
            for dim in ood_dims:
                vals = [r["deterministic_scores"].get(dim, 0) for r in cfg_results]
                means[dim] = np.mean(vals)
            lines.append(
                f"| {cfg} | {n} | {means['refusal_accuracy']:.2f} | "
                f"{means['hallucination_avoidance']:.2f} | "
                f"{means['explanation_quality']:.2f} |"
            )
        lines.append("")

    # --- Agreement analysis ---
    lines.extend(["## 4. Agreement: Deterministic vs LLM Judge", ""])

    if answerable:
        lines.append("### Answerable Dimensions")
        lines.append("")
        lines.append("| Dimension | N | Exact Agree | ±1 Agree | ±2 Agree | MAE | Spearman ρ | Det Mean | Judge Mean |")
        lines.append("|-----------|--:|:----------:|:-------:|:-------:|:---:|:---------:|:--------:|:----------:|")

        for dim in ["correctness", "completeness", "faithfulness", "citation_quality"]:
            ag = agreement.get(f"answerable_{dim}", {})
            if "note" in ag:
                lines.append(f"| {dim} | {ag.get('n', 0)} | — | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {dim} | {ag['n']} | {ag['exact_agreement']:.1%} | "
                f"{ag['within_1_agreement']:.1%} | {ag['within_2_agreement']:.1%} | "
                f"{ag['mae']:.2f} | {ag['spearman_rho']:.3f} | "
                f"{ag['det_mean']:.2f} | {ag['judge_mean']:.2f} |"
            )
        lines.append("")

    if ood:
        lines.append("### OOD Dimensions")
        lines.append("")
        lines.append("| Dimension | N | Exact Agree | ±1 Agree | MAE | Spearman ρ |")
        lines.append("|-----------|--:|:----------:|:-------:|:---:|:---------:|")

        for dim in ["refusal_accuracy", "hallucination_avoidance", "explanation_quality"]:
            ag = agreement.get(f"ood_{dim}", {})
            if "note" in ag:
                lines.append(f"| {dim} | {ag.get('n', 0)} | — | — | — | — |")
                continue
            lines.append(
                f"| {dim} | {ag['n']} | {ag['exact_agreement']:.1%} | "
                f"{ag['within_1_agreement']:.1%} | {ag['mae']:.2f} | "
                f"{ag['spearman_rho']:.3f} |"
            )
        lines.append("")

    # --- Methodology note ---
    lines.extend([
        "## 5. Methodology Notes",
        "",
        "### Metric Definitions",
        "",
        "**Correctness** = semantic_similarity × 0.6 + number_overlap × 0.4",
        "- Semantic similarity: cosine similarity of BGE-M3 embeddings between expected and generated answers",
        "- Number overlap: fraction of numeric values from expected answer found in generated answer",
        "",
        "**Completeness** = concept_recall",
        "- Fraction of expected_concepts (from ground truth) found in the generated answer",
        "- Uses case-insensitive matching with multi-word fuzzy matching and hyphen normalization",
        "",
        "**Faithfulness** = concept_recall × semantic_similarity (proxy)",
        "- Without access to retrieved passages, we cannot directly verify source grounding",
        "- This proxy captures: answers covering expected concepts AND aligning with expected text are likely faithful",
        "- Limitation: this is a proxy metric; true faithfulness requires passage-level verification",
        "",
        "**Citation Quality** = source_coverage × 0.5 + has_citations × 0.25 + density_norm × 0.25",
        "- Source coverage: fraction of expected source_files mentioned in the answer",
        "- Has citations: binary indicator of any citation markers present",
        "- Density: citations per 100 words, normalized to [0, 1] with cap at 10",
        "",
        "### OOD Scoring",
        "",
        "OOD questions use keyword-based detection:",
        "- **Refusal accuracy**: presence of refusal phrases + answer brevity",
        "- **Hallucination avoidance**: absence of citations and specific fabricated data in OOD answers",
        "- **Explanation quality**: presence of explanatory reasoning about why the question cannot be answered",
    ])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 8. MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic scorer for V4 experiment results",
    )
    parser.add_argument(
        "--input", "-i", type=Path, required=True,
        help="Input results JSON (V4-4 or V4-5 format)",
    )
    parser.add_argument(
        "--gt", type=Path, default=V4_GROUND_TRUTH,
        help=f"Ground truth file (default: {V4_GROUND_TRUTH})",
    )
    parser.add_argument(
        "--skip-embeddings", action="store_true",
        help="Skip semantic similarity computation (faster, uses 0.5 default)",
    )
    parser.add_argument(
        "--show-distributions", action="store_true",
        help="Log metric distributions for threshold calibration",
    )
    parser.add_argument(
        "--output-prefix", type=str, default="v4_deterministic",
        help="Output file prefix (default: v4_deterministic)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Load results
    results, meta = load_results(args.input)

    # Initialize embedder
    embedder = None
    if not args.skip_embeddings:
        logger.info("Loading BGE-M3 embedding model...")
        from backend.retrieval.embeddings import EmbeddingEngine
        embedder = EmbeddingEngine(model_name="BAAI/bge-m3")
        logger.info("Embedding model loaded.")
    else:
        logger.info("Skipping embeddings (--skip-embeddings). Semantic similarity will use default 0.5.")

    # Score all results
    thresholds = DEFAULT_THRESHOLDS
    scored = score_all(
        results, args.gt, embedder, thresholds,
        show_distributions=args.show_distributions,
    )

    # Agreement analysis
    logger.info("Computing agreement with LLM judge scores...")
    agreement = analyze_agreement(scored)

    # Generate report
    report = generate_report(scored, agreement, meta, thresholds, str(args.input))

    # Save
    output_data = {
        "experiment": "deterministic_scoring",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "input_file": str(args.input),
        "thresholds": asdict(thresholds),
        "n_results": len(scored),
        "agreement": agreement,
        "per_result": scored,
    }
    json_path, _ = save_v4_results(output_data, args.output_prefix)
    md_path = save_v4_markdown(report, args.output_prefix)

    # Print summary
    print(f"\n{'='*70}")
    print("DETERMINISTIC SCORING COMPLETE")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print(f"\n{report[:5000]}")


if __name__ == "__main__":
    main()
