#!/usr/bin/env python3
"""
V4-0 Phase 3b: Objective Quality Metrics for Judge Calibration

Computes deterministic, ground-truth-based quality metrics for each
Phase 2 generated answer. These metrics serve as the objective baseline
against which all judge models are calibrated.

Metrics computed per answer:
  1. Concept recall: fraction of expected_concepts found in the answer
  2. Semantic similarity: cosine similarity between expected_answer and generated_answer
  3. Citation coverage: whether cited papers match source_files in ground truth

Usage:
  # Compute objective metrics for all Phase 2 answers
  python exp_00_objective_metrics.py

  # Then run the full judge calibration analysis
  python exp_00_objective_metrics.py --analyze-judges
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

logger = logging.getLogger("exp_00_objective_metrics")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

# ── Constants ──

PHASE2_FILE = V4_RESULTS_DIR / "v4_0_phase2_latest.json"
SCORE_DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]


# ── Objective Metric Computation ──

def compute_concept_recall(answer: str, expected_concepts: List[str]) -> float:
    """Compute fraction of expected concepts found in the answer.

    Uses case-insensitive matching with word boundary awareness.
    Returns 0.0-1.0.
    """
    if not expected_concepts:
        return 1.0  # no concepts to check

    answer_lower = answer.lower()
    found = 0
    for concept in expected_concepts:
        # Try exact match first (case-insensitive)
        concept_lower = concept.lower()
        if concept_lower in answer_lower:
            found += 1
            continue
        # Try individual words for multi-word concepts
        words = concept_lower.split()
        if len(words) > 1:
            # Check if all significant words appear (skip short words)
            sig_words = [w for w in words if len(w) > 3]
            if sig_words and all(w in answer_lower for w in sig_words):
                found += 1
                continue
        # Try common abbreviation/variant patterns
        # e.g., "GATK best-practice" -> "GATK" or "best practice"
        if '-' in concept_lower:
            no_hyphen = concept_lower.replace('-', ' ')
            if no_hyphen in answer_lower:
                found += 1
                continue

    return found / len(expected_concepts)


def compute_semantic_similarity(
    expected_answer: str,
    generated_answer: str,
    embedder,
) -> float:
    """Compute cosine similarity between expected and generated answers.

    Uses BGE-M3 embeddings (same model used in our RAG pipeline).
    Returns -1.0 to 1.0 (typically 0.3-0.95 for related texts).
    """
    if not expected_answer or not generated_answer:
        return 0.0

    # Truncate to reasonable length for embedding
    exp_trunc = expected_answer[:2000]
    gen_trunc = generated_answer[:2000]

    embeddings = embedder.embed_documents([exp_trunc, gen_trunc])
    # Cosine similarity (embeddings are already normalized by BGE-M3)
    sim = np.dot(embeddings[0], embeddings[1])
    return float(sim)


def compute_citation_coverage(
    answer: str,
    source_files: List[str],
    final_citations: int,
) -> Dict[str, float]:
    """Compute citation quality metrics.

    Returns dict with:
      - has_citations: 1.0 if any citations, 0.0 otherwise
      - source_mentioned: fraction of source_files mentioned in answer
      - citation_density: citations per 1000 chars (capped at 1.0)
    """
    metrics = {}

    # Basic citation presence
    metrics["has_citations"] = 1.0 if final_citations > 0 else 0.0

    # Source file mention check
    if source_files:
        answer_lower = answer.lower()
        found = 0
        for sf in source_files:
            # Extract paper name from filename (e.g., "01_sarek.pdf" -> "sarek")
            name = sf.replace('.pdf', '').lower()
            # Remove leading number prefix
            name_parts = name.split('_', 1)
            if len(name_parts) > 1:
                name_clean = name_parts[1]
            else:
                name_clean = name
            if name_clean in answer_lower or name in answer_lower:
                found += 1
        metrics["source_mentioned"] = found / len(source_files)
    else:
        metrics["source_mentioned"] = 0.0

    # Citation density (normalized)
    answer_len = max(len(answer), 1)
    raw_density = (final_citations / answer_len) * 1000
    metrics["citation_density"] = min(raw_density, 1.0)  # cap at 1.0

    return metrics


def compute_all_objective_metrics(
    phase2_file: Path,
    gt_path: Path,
) -> List[Dict[str, Any]]:
    """Compute objective metrics for all Phase 2 answers."""
    from backend.retrieval.embeddings import EmbeddingEngine

    # Load data
    phase2 = json.load(open(phase2_file))
    answers = phase2["per_question_results"]
    gt_questions = load_ground_truth(gt_path, answerable_only=False)
    gt_lookup = {q["id"]: q for q in gt_questions}

    # Initialize embedding engine
    logger.info("Loading BGE-M3 embedding model...")
    embedder = EmbeddingEngine(model_name="BAAI/bge-m3")
    logger.info("Embedding model loaded.")

    results = []
    for i, answer in enumerate(answers):
        qid = answer["question_id"]
        model = answer["model"]
        gt = gt_lookup.get(qid)

        if not gt:
            logger.warning(f"No GT for {qid}, skipping")
            continue

        if not answer.get("completed") or not answer.get("final_answer"):
            # Still record with zero metrics
            results.append({
                "model": model,
                "question_id": qid,
                "category": answer.get("category", ""),
                "completed": False,
                "concept_recall": 0.0,
                "semantic_similarity": 0.0,
                "has_citations": 0.0,
                "source_mentioned": 0.0,
                "citation_density": 0.0,
            })
            continue

        final_answer = answer["final_answer"]
        expected_answer = gt.get("expected_answer", "")
        expected_concepts = gt.get("expected_concepts", [])
        source_files = gt.get("source_files", [])

        # Compute metrics
        concept_recall = compute_concept_recall(final_answer, expected_concepts)
        semantic_sim = compute_semantic_similarity(expected_answer, final_answer, embedder)
        citation_metrics = compute_citation_coverage(
            final_answer, source_files, answer.get("final_citations", 0)
        )

        result = {
            "model": model,
            "question_id": qid,
            "category": answer.get("category", ""),
            "difficulty": answer.get("difficulty", ""),
            "completed": True,
            "concept_recall": round(concept_recall, 4),
            "semantic_similarity": round(semantic_sim, 4),
            **{k: round(v, 4) for k, v in citation_metrics.items()},
            "answer_length": len(final_answer),
            "final_citations": answer.get("final_citations", 0),
        }
        results.append(result)

        if (i + 1) % 10 == 0:
            logger.info(f"  [{i+1}/{len(answers)}] {model} | {qid}: "
                        f"concept={concept_recall:.2f}, sim={semantic_sim:.3f}, "
                        f"cites={answer.get('final_citations', 0)}")

    return results


# ── Judge Calibration Analysis ──

def load_all_judge_scores(
    results_dir: Path,
    include_legacy: bool = False,
) -> Dict[str, Dict[str, Dict]]:
    """Load all judge scores from completed Phase 3 runs.

    Supports two formats:
    1. Judge scoring format (post-fix): all_scores.{model_id} from exp_00_judge_scoring.py
    2. Legacy judge comparison format (pre-fix): all_scores.reference + all_scores.candidates

    IMPORTANT: Legacy files (v4_0_judge_20260304_*.json) contain Gemini reference
    scores for answers generated BEFORE the num_ctx fix (2048 default). These must
    NOT be mixed with post-fix objective metrics for calibration. Set include_legacy=True
    only for Gemini self-consistency analysis on pre-fix data.

    Returns: {judge_model_id: {gen_model|qid: scores_dict}}
    """
    import glob

    all_judges = {}

    for fpath in sorted(glob.glob(str(results_dir / "v4_0_judge_*.json"))):
        fname = Path(fpath).name
        if "intermediate" in fname or "latest" in fname:
            continue

        try:
            data = json.load(open(fpath))
        except Exception:
            continue

        experiment_type = data.get("experiment", "")

        if experiment_type == "v4_0_judge_scoring":
            # Post-fix format: all_scores keyed by judge model ID
            for judge_model, scores in data.get("all_scores", {}).items():
                if not isinstance(scores, dict):
                    continue
                nonzero = sum(1 for s in scores.values() if isinstance(s, dict) and s.get("correctness", 0) > 0)
                if nonzero > 0:
                    all_judges[judge_model] = scores
        elif include_legacy:
            # Legacy format (pre-fix): reference + candidates
            # Only loaded when explicitly requested
            ref_model = data.get("reference_model", "")
            ref_scores = data.get("all_scores", {}).get("reference", {})
            if ref_scores and ref_model:
                ts = fname.replace("v4_0_judge_", "").replace(".json", "")
                key = f"{ref_model}__run_{ts}"
                if key not in all_judges:
                    all_judges[key] = ref_scores

            for cand_model, scores in data.get("all_scores", {}).get("candidates", {}).items():
                if cand_model == "NONE_PLACEHOLDER" or cand_model == "SKIP_NONE":
                    continue
                nonzero = sum(1 for s in scores.values() if s.get("correctness", 0) > 0)
                if nonzero > 0:
                    all_judges[cand_model] = scores
        else:
            logger.debug(f"  Skipping legacy pre-fix file: {fname}")

    return all_judges


def calibrate_judges_against_gt(
    objective_metrics: List[Dict],
    judge_scores: Dict[str, Dict[str, Dict]],
) -> Dict[str, Dict[str, Any]]:
    """Compute calibration metrics for each judge against objective ground truth.

    For each judge, measures how well its scores predict objective metrics:
    - correctness ↔ semantic_similarity
    - completeness ↔ concept_recall
    - citation_quality ↔ citation_density + source_mentioned
    - faithfulness ↔ concept_recall (proxy: answers with high concept recall are more faithful)
    """
    from scipy.stats import spearmanr, pearsonr

    # Build lookup: "model|qid" -> objective metrics
    obj_lookup = {}
    for m in objective_metrics:
        key = f"{m['model']}|{m['question_id']}"
        obj_lookup[key] = m

    calibration = {}

    for judge_id, scores in judge_scores.items():
        # Align judge scores with objective metrics
        aligned_keys = [k for k in scores if k in obj_lookup and obj_lookup[k]["completed"]]

        if len(aligned_keys) < 10:
            logger.warning(f"  {judge_id}: only {len(aligned_keys)} aligned answers, skipping")
            continue

        # Extract arrays
        j_correctness = np.array([scores[k].get("correctness", 0) for k in aligned_keys], dtype=float)
        j_completeness = np.array([scores[k].get("completeness", 0) for k in aligned_keys], dtype=float)
        j_faithfulness = np.array([scores[k].get("faithfulness", 0) for k in aligned_keys], dtype=float)
        j_citation_q = np.array([scores[k].get("citation_quality", 0) for k in aligned_keys], dtype=float)

        o_concept_recall = np.array([obj_lookup[k]["concept_recall"] for k in aligned_keys], dtype=float)
        o_semantic_sim = np.array([obj_lookup[k]["semantic_similarity"] for k in aligned_keys], dtype=float)
        o_citation_dens = np.array([obj_lookup[k]["citation_density"] for k in aligned_keys], dtype=float)
        o_source_ment = np.array([obj_lookup[k]["source_mentioned"] for k in aligned_keys], dtype=float)
        o_has_cites = np.array([obj_lookup[k]["has_citations"] for k in aligned_keys], dtype=float)

        # Composite citation metric
        o_cite_composite = (o_citation_dens + o_source_ment + o_has_cites) / 3.0

        def safe_corr(x, y, method="pearson"):
            if np.std(x) == 0 or np.std(y) == 0:
                return 0.0, 1.0
            if method == "pearson":
                return pearsonr(x, y)
            else:
                return spearmanr(x, y)

        # Calibration pairs
        cal = {}

        # correctness ↔ semantic_similarity
        r, p = safe_corr(j_correctness, o_semantic_sim)
        cal["correctness_vs_semantic_sim"] = {"pearson": round(r, 4), "p_value": round(p, 6)}
        rs, ps = safe_corr(j_correctness, o_semantic_sim, "spearman")
        cal["correctness_vs_semantic_sim_spearman"] = round(rs, 4)

        # completeness ↔ concept_recall
        r, p = safe_corr(j_completeness, o_concept_recall)
        cal["completeness_vs_concept_recall"] = {"pearson": round(r, 4), "p_value": round(p, 6)}
        rs, ps = safe_corr(j_completeness, o_concept_recall, "spearman")
        cal["completeness_vs_concept_recall_spearman"] = round(rs, 4)

        # faithfulness ↔ concept_recall (proxy)
        r, p = safe_corr(j_faithfulness, o_concept_recall)
        cal["faithfulness_vs_concept_recall"] = {"pearson": round(r, 4), "p_value": round(p, 6)}

        # citation_quality ↔ composite citation metric
        r, p = safe_corr(j_citation_q, o_cite_composite)
        cal["citation_quality_vs_cite_composite"] = {"pearson": round(r, 4), "p_value": round(p, 6)}
        rs, ps = safe_corr(j_citation_q, o_cite_composite, "spearman")
        cal["citation_quality_vs_cite_composite_spearman"] = round(rs, 4)

        # Composite calibration score (average Pearson across key pairs)
        key_pearsons = [
            cal["correctness_vs_semantic_sim"]["pearson"],
            cal["completeness_vs_concept_recall"]["pearson"],
            cal["citation_quality_vs_cite_composite"]["pearson"],
        ]
        cal["composite_calibration"] = round(float(np.mean(key_pearsons)), 4)
        cal["n_aligned"] = len(aligned_keys)

        # Judge score statistics
        cal["judge_stats"] = {
            "correctness_mean": round(float(np.mean(j_correctness)), 2),
            "completeness_mean": round(float(np.mean(j_completeness)), 2),
            "faithfulness_mean": round(float(np.mean(j_faithfulness)), 2),
            "citation_quality_mean": round(float(np.mean(j_citation_q)), 2),
        }

        calibration[judge_id] = cal

    return calibration


def compute_gemini_consistency(
    judge_scores: Dict[str, Dict[str, Dict]],
) -> Dict[str, Any]:
    """Compute self-consistency across multiple gemini runs."""
    gemini_runs = {k: v for k, v in judge_scores.items() if k.startswith("gemini::")}

    if len(gemini_runs) < 2:
        return {"n_runs": len(gemini_runs), "note": "Need >=2 runs for consistency"}

    run_keys = sorted(gemini_runs.keys())
    logger.info(f"Computing Gemini consistency across {len(run_keys)} runs")

    # Find common scored answers
    common_keys = set(gemini_runs[run_keys[0]].keys())
    for rk in run_keys[1:]:
        common_keys &= set(gemini_runs[rk].keys())
    common_keys = sorted(common_keys)

    if not common_keys:
        return {"n_runs": len(run_keys), "error": "No common keys across runs"}

    # Per-dimension consistency
    consistency = {"n_runs": len(run_keys), "n_common": len(common_keys)}

    for dim in SCORE_DIMS:
        scores_per_run = []
        for rk in run_keys:
            vals = [gemini_runs[rk][k].get(dim, 0) for k in common_keys]
            scores_per_run.append(np.array(vals, dtype=float))

        # Pairwise correlations
        pairwise_corrs = []
        pairwise_maes = []
        for i in range(len(scores_per_run)):
            for j in range(i + 1, len(scores_per_run)):
                if np.std(scores_per_run[i]) > 0 and np.std(scores_per_run[j]) > 0:
                    corr = np.corrcoef(scores_per_run[i], scores_per_run[j])[0, 1]
                    pairwise_corrs.append(float(corr))
                mae = float(np.mean(np.abs(scores_per_run[i] - scores_per_run[j])))
                pairwise_maes.append(mae)

        # Per-answer std across runs
        stacked = np.stack(scores_per_run)
        per_answer_std = np.std(stacked, axis=0)

        consistency[f"{dim}_mean_pairwise_corr"] = round(float(np.mean(pairwise_corrs)), 4) if pairwise_corrs else 0.0
        consistency[f"{dim}_mean_pairwise_mae"] = round(float(np.mean(pairwise_maes)), 4)
        consistency[f"{dim}_mean_answer_std"] = round(float(np.mean(per_answer_std)), 4)
        consistency[f"{dim}_max_answer_std"] = round(float(np.max(per_answer_std)), 4)

    return consistency


# ── Report Generation ──

def generate_objective_report(
    obj_metrics: List[Dict],
    calibration: Dict[str, Dict],
    gemini_consistency: Dict,
) -> str:
    """Generate comprehensive markdown report."""
    lines = [
        "# V4-0 Phase 3: Judge Calibration Against Ground Truth",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Methodology**: Objective metrics (concept recall, semantic similarity, citation coverage)",
        f"**Reference**: Human-curated ground truth (`expected_answer` + `expected_concepts`)",
        f"**Answers evaluated**: {len(obj_metrics)}",
        "",
    ]

    # Objective metrics summary by model
    lines.extend(["## 1. Objective Quality Metrics (per generation model)", ""])

    models = sorted(set(m["model"] for m in obj_metrics))
    lines.append("| Generation Model | Concept Recall | Semantic Sim | Has Citations | Source Mentioned | Citation Density |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")

    for model in models:
        runs = [m for m in obj_metrics if m["model"] == model and m["completed"]]
        if not runs:
            continue
        avg_cr = np.mean([r["concept_recall"] for r in runs])
        avg_ss = np.mean([r["semantic_similarity"] for r in runs])
        avg_hc = np.mean([r["has_citations"] for r in runs])
        avg_sm = np.mean([r["source_mentioned"] for r in runs])
        avg_cd = np.mean([r["citation_density"] for r in runs])
        lines.append(f"| `{model}` | {avg_cr:.3f} | {avg_ss:.3f} | {avg_hc:.1%} | {avg_sm:.3f} | {avg_cd:.3f} |")

    # Gemini consistency
    lines.extend(["", "## 2. Reference Judge Self-Consistency (Gemini)", ""])
    n_runs = gemini_consistency.get("n_runs", 0)
    if n_runs >= 2:
        lines.append(f"**Runs**: {n_runs} independent scoring passes on {gemini_consistency.get('n_common', 0)} answers")
        lines.append("")
        lines.append("| Dimension | Mean Pairwise Corr | Mean Pairwise MAE | Mean Answer Std | Max Answer Std |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for dim in SCORE_DIMS:
            corr = gemini_consistency.get(f"{dim}_mean_pairwise_corr", 0)
            mae = gemini_consistency.get(f"{dim}_mean_pairwise_mae", 0)
            mean_std = gemini_consistency.get(f"{dim}_mean_answer_std", 0)
            max_std = gemini_consistency.get(f"{dim}_max_answer_std", 0)
            lines.append(f"| {dim} | {corr:.4f} | {mae:.3f} | {mean_std:.3f} | {max_std:.3f} |")
    else:
        lines.append(f"*Insufficient runs ({n_runs}). Need >=2 for consistency analysis.*")

    # Judge calibration
    lines.extend(["", "## 3. Judge Calibration Against Ground Truth", ""])
    lines.append("Lower MAE and higher Pearson = better calibrated judge.")
    lines.append("")
    lines.append("| Judge Model | Composite | Corr↔Sem.Sim | Compl↔Concept | Cite↔Composite | N |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")

    # Sort by composite calibration (higher is better)
    ranked = sorted(calibration.items(), key=lambda x: x[1].get("composite_calibration", 0), reverse=True)

    for judge_id, cal in ranked:
        comp = cal.get("composite_calibration", 0)
        corr_sim = cal.get("correctness_vs_semantic_sim", {}).get("pearson", 0)
        compl_cr = cal.get("completeness_vs_concept_recall", {}).get("pearson", 0)
        cite_comp = cal.get("citation_quality_vs_cite_composite", {}).get("pearson", 0)
        n = cal.get("n_aligned", 0)
        lines.append(f"| `{judge_id}` | {comp:.4f} | {corr_sim:.4f} | {compl_cr:.4f} | {cite_comp:.4f} | {n} |")

    # Detailed per-judge
    lines.extend(["", "## 4. Per-Judge Detail", ""])

    for judge_id, cal in ranked[:5]:  # Top 5
        lines.append(f"### `{judge_id}`")
        lines.append("")
        lines.append(f"- **Composite calibration**: {cal.get('composite_calibration', 0):.4f}")
        lines.append(f"- **Correctness ↔ Semantic similarity**: Pearson={cal.get('correctness_vs_semantic_sim', {}).get('pearson', 0):.4f} (p={cal.get('correctness_vs_semantic_sim', {}).get('p_value', 1):.4f})")
        lines.append(f"- **Completeness ↔ Concept recall**: Pearson={cal.get('completeness_vs_concept_recall', {}).get('pearson', 0):.4f} (p={cal.get('completeness_vs_concept_recall', {}).get('p_value', 1):.4f})")
        lines.append(f"- **Citation quality ↔ Citation composite**: Pearson={cal.get('citation_quality_vs_cite_composite', {}).get('pearson', 0):.4f}")
        stats = cal.get("judge_stats", {})
        lines.append(f"- **Score means**: correctness={stats.get('correctness_mean', 0)}, completeness={stats.get('completeness_mean', 0)}, faithfulness={stats.get('faithfulness_mean', 0)}, citation_quality={stats.get('citation_quality_mean', 0)}")
        lines.append("")

    # Recommendation
    if ranked:
        winner_id = ranked[0][0]
        winner_cal = ranked[0][1].get("composite_calibration", 0)
        lines.extend([
            "## 5. Recommendation",
            "",
            f"**Best calibrated judge**: `{winner_id}` (composite calibration: {winner_cal:.4f})",
            "",
            "This judge's scores best predict objective answer quality as measured by",
            "concept recall, semantic similarity, and citation coverage against",
            "human-curated ground truth.",
        ])

    return "\n".join(lines)


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="V4-0: Objective Quality Metrics & Judge Calibration",
    )
    parser.add_argument(
        "--phase2-file", type=Path, default=PHASE2_FILE,
        help=f"Phase 2 merged results (default: {PHASE2_FILE.name})",
    )
    parser.add_argument(
        "--analyze-judges", action="store_true",
        help="Also run judge calibration analysis against objective metrics",
    )
    parser.add_argument(
        "--skip-embeddings", action="store_true",
        help="Skip semantic similarity (faster, for testing)",
    )
    parser.add_argument(
        "--include-legacy", action="store_true",
        help="Include pre-fix legacy judge files (v4_0_judge_20260304_*). "
             "WARNING: these scored answers generated with num_ctx=2048, "
             "not the current post-fix Phase 2 answers.",
    )

    args = parser.parse_args()

    # Step 1: Compute objective metrics
    logger.info("Computing objective quality metrics for Phase 2 answers...")
    obj_metrics = compute_all_objective_metrics(args.phase2_file, V4_GROUND_TRUTH)
    logger.info(f"Computed metrics for {len(obj_metrics)} answers")

    # Summary by model
    models = sorted(set(m["model"] for m in obj_metrics))
    for model in models:
        runs = [m for m in obj_metrics if m["model"] == model and m["completed"]]
        if runs:
            avg_cr = np.mean([r["concept_recall"] for r in runs])
            avg_ss = np.mean([r["semantic_similarity"] for r in runs])
            logger.info(f"  {model}: concept_recall={avg_cr:.3f}, sem_sim={avg_ss:.3f}")

    # Save objective metrics
    obj_data = {
        "experiment": "v4_0_objective_metrics",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "n_answers": len(obj_metrics),
        "metrics": obj_metrics,
    }
    obj_path, _ = save_v4_results(obj_data, "v4_0_objective")
    logger.info(f"Saved objective metrics: {obj_path}")

    if not args.analyze_judges:
        logger.info("Run with --analyze-judges to calibrate judges against these metrics")
        return

    # Step 2: Load all judge scores
    logger.info("Loading all judge scores (post-fix only)...")
    if args.include_legacy:
        logger.warning("Including legacy pre-fix judge files — calibration may be invalid!")
    judge_scores = load_all_judge_scores(V4_RESULTS_DIR, include_legacy=args.include_legacy)
    logger.info(f"Loaded {len(judge_scores)} judge variants")
    for jid, scores in judge_scores.items():
        nonzero = sum(1 for s in scores.values() if s.get("correctness", 0) > 0)
        logger.info(f"  {jid}: {len(scores)} scores ({nonzero} non-zero)")

    # Step 3: Calibrate judges against ground truth
    logger.info("Calibrating judges against objective metrics...")
    calibration = calibrate_judges_against_gt(obj_metrics, judge_scores)

    # Step 4: Gemini self-consistency
    logger.info("Computing Gemini self-consistency...")
    gemini_consistency = compute_gemini_consistency(judge_scores)

    # Step 5: Generate report
    report = generate_objective_report(obj_metrics, calibration, gemini_consistency)

    # Save
    full_data = {
        "experiment": "v4_0_judge_calibration",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "objective_metrics": obj_metrics,
        "calibration": calibration,
        "gemini_consistency": gemini_consistency,
    }
    json_path, _ = save_v4_results(full_data, "v4_0_calibration")
    md_path = save_v4_markdown(report, "v4_0_calibration")

    print(f"\n{'='*70}")
    print("V4-0 COMPLETE: Judge Calibration Against Ground Truth")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(report[:5000])


if __name__ == "__main__":
    main()
