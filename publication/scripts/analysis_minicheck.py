#!/usr/bin/env python3
"""
MiniCheck Faithfulness Scoring for V4 Experiments

Computes NLI-based faithfulness scores using MiniCheck (Tang et al., EMNLP 2024).
Unlike our proxy metric (concept_recall × semantic_similarity), MiniCheck
performs actual textual entailment checking at the sentence level.

Two-directional evaluation:
  1. PRECISION (forward): What fraction of generated answer sentences are
     entailed by the expected answer? High precision = no hallucination.
  2. RECALL (backward): What fraction of expected answer sentences are
     covered by the generated answer? High recall = complete answer.

Input: V4-4 or V4-5 results JSON + ground truth
Output: Augmented results with MiniCheck faithfulness scores + comparison report

Usage:
  # Score V4-4 results
  uv run python publication/scripts/analysis_minicheck.py \\
      --input publication/results/v4_4_generation_latest.json

  # Score only first N results (testing)
  uv run python publication/scripts/analysis_minicheck.py \\
      --input results.json --max-results 10
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

logger = logging.getLogger("minicheck")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# ═══════════════════════════════════════════════════════════════
# 1. SENTENCE DECOMPOSITION
# ═══════════════════════════════════════════════════════════════

def decompose_to_sentences(text: str) -> List[str]:
    """Split text into individual sentences for claim-level checking.

    Handles markdown formatting, bullet points, and scientific text.
    Filters out very short fragments and formatting artifacts.
    """
    # Remove markdown formatting
    clean = re.sub(r'\[([^\]]+\.pdf):?\d*\]', '', text)  # Remove citations
    clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)  # Bold
    clean = re.sub(r'\*([^*]+)\*', r'\1', clean)  # Italic
    clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)  # Headers
    clean = re.sub(r'^\s*[-*]\s+', '', clean, flags=re.MULTILINE)  # Bullets
    clean = re.sub(r'^\s*\d+\.\s+', '', clean, flags=re.MULTILINE)  # Numbered lists

    # Split on sentence boundaries
    # Handle abbreviations and decimal numbers carefully
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean)

    # Also split on newlines that separate distinct statements
    expanded = []
    for s in sentences:
        parts = s.split('\n')
        expanded.extend(parts)

    # Filter
    result = []
    for s in expanded:
        s = s.strip()
        if len(s) < 20:  # Too short to be a meaningful claim
            continue
        if s.startswith('|') or s.startswith('---'):  # Table formatting
            continue
        result.append(s)

    return result


# ═══════════════════════════════════════════════════════════════
# 2. MINICHECK SCORING
# ═══════════════════════════════════════════════════════════════

def score_faithfulness(
    generated_answer: str,
    expected_answer: str,
    scorer,
) -> Dict[str, Any]:
    """Score faithfulness bidirectionally using MiniCheck.

    Returns:
        precision: fraction of generated sentences entailed by expected
        recall: fraction of expected sentences covered by generated
        f1: harmonic mean
        per_sentence: detailed per-sentence results
    """
    gen_sentences = decompose_to_sentences(generated_answer)
    exp_sentences = decompose_to_sentences(expected_answer)

    if not gen_sentences or not exp_sentences:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "n_gen_sentences": len(gen_sentences),
            "n_exp_sentences": len(exp_sentences),
            "precision_details": [],
            "recall_details": [],
        }

    # --- PRECISION (forward): generated claims vs expected answer ---
    # "Is each generated sentence entailed by the expected answer?"
    precision_docs = [expected_answer] * len(gen_sentences)
    precision_claims = gen_sentences

    pred_labels, raw_probs, _, _ = scorer.score(
        docs=precision_docs,
        claims=precision_claims,
    )

    precision_details = []
    for sent, label, prob in zip(gen_sentences, pred_labels, raw_probs):
        precision_details.append({
            "sentence": sent[:200],
            "supported": bool(label),
            "probability": round(float(prob), 4),
        })

    precision = sum(pred_labels) / len(pred_labels) if pred_labels else 0.0

    # --- RECALL (backward): expected claims vs generated answer ---
    # "Is each expected sentence covered by the generated answer?"
    recall_docs = [generated_answer] * len(exp_sentences)
    recall_claims = exp_sentences

    pred_labels_r, raw_probs_r, _, _ = scorer.score(
        docs=recall_docs,
        claims=recall_claims,
    )

    recall_details = []
    for sent, label, prob in zip(exp_sentences, pred_labels_r, raw_probs_r):
        recall_details.append({
            "sentence": sent[:200],
            "covered": bool(label),
            "probability": round(float(prob), 4),
        })

    recall = sum(pred_labels_r) / len(pred_labels_r) if pred_labels_r else 0.0

    # F1
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_gen_sentences": len(gen_sentences),
        "n_exp_sentences": len(exp_sentences),
        "mean_precision_prob": round(float(np.mean(raw_probs)), 4),
        "mean_recall_prob": round(float(np.mean(raw_probs_r)), 4),
        "precision_details": precision_details,
        "recall_details": recall_details,
    }


# ═══════════════════════════════════════════════════════════════
# 3. MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def load_results(path: Path) -> Tuple[List[Dict], Dict]:
    """Load V4-4 or V4-5 results."""
    data = json.load(open(path))
    if "per_question_results" in data:
        results = data["per_question_results"]
        meta = {k: v for k, v in data.items() if k != "per_question_results"}
    elif "results" in data:
        results = data["results"]
        meta = {k: v for k, v in data.items() if k != "results"}
    else:
        raise ValueError(f"Unknown result format in {path}")
    return results, meta


def run_minicheck_scoring(
    results: List[Dict],
    gt_path: Path,
    scorer,
    max_results: Optional[int] = None,
) -> List[Dict]:
    """Run MiniCheck on all answerable results."""
    gt_all = load_ground_truth(gt_path, answerable_only=False)
    gt_lookup = {q["id"]: q for q in gt_all}

    scored = []
    answerable_count = 0

    for i, r in enumerate(results):
        if max_results and len(scored) >= max_results:
            break

        qid = r["question_id"]
        gt = gt_lookup.get(qid)
        if not gt:
            continue

        is_answerable = r.get("answerable", gt.get("answerable", True))
        if not is_answerable:
            continue  # MiniCheck only applies to answerable questions

        # Extract answer
        answer = ""
        if isinstance(r.get("generation"), dict):
            answer = r["generation"].get("answer", "")
        if not answer:
            continue

        expected = gt.get("expected_answer", "")
        if not expected:
            continue

        answerable_count += 1

        # Score
        mc_result = score_faithfulness(answer, expected, scorer)

        scored.append({
            "question_id": qid,
            "config": r.get("config", "unknown"),
            "index_name": r.get("index_name", ""),
            "category": r.get("category", gt.get("category", "")),
            "difficulty": r.get("difficulty", ""),
            "minicheck": {
                "precision": mc_result["precision"],
                "recall": mc_result["recall"],
                "f1": mc_result["f1"],
                "n_gen_sentences": mc_result["n_gen_sentences"],
                "n_exp_sentences": mc_result["n_exp_sentences"],
                "mean_precision_prob": mc_result["mean_precision_prob"],
                "mean_recall_prob": mc_result["mean_recall_prob"],
            },
            "minicheck_details": {
                "precision_details": mc_result["precision_details"],
                "recall_details": mc_result["recall_details"],
            },
            # Preserve existing scores for comparison
            "judge_scores": r.get("judge_scores", {}),
            "citation_metrics": r.get("citation_metrics", {}),
        })

        if (len(scored)) % 20 == 0:
            logger.info(
                f"  [{len(scored)}/{answerable_count}] {qid} ({r.get('config', '')}): "
                f"P={mc_result['precision']:.2f} R={mc_result['recall']:.2f} "
                f"F1={mc_result['f1']:.2f}"
            )

    logger.info(f"Scored {len(scored)} answerable results with MiniCheck")
    return scored


# ═══════════════════════════════════════════════════════════════
# 4. REPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_report(
    scored: List[Dict],
    meta: Dict,
    input_file: str,
) -> str:
    """Generate comparison report."""
    lines = [
        "# MiniCheck Faithfulness Analysis",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Input**: `{input_file}`",
        f"**Model**: MiniCheck-FT5 (Flan-T5-Large, 770M params)",
        f"**Method**: Bidirectional NLI — precision (generated→expected) + recall (expected→generated)",
        f"**Reference**: Tang et al. (2024). *MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents.* EMNLP.",
        f"**Results scored**: {len(scored)} answerable questions",
        "",
    ]

    # --- By config ---
    configs = sorted(set(r["config"] for r in scored))
    lines.extend(["## By Configuration", ""])
    lines.append("| Config | N | Precision | Recall | F1 | Mean Gen Sents | Mean Exp Sents |")
    lines.append("|--------|--:|:---------:|:------:|:--:|:--------------:|:--------------:|")

    for cfg in configs:
        cfg_results = [r for r in scored if r["config"] == cfg]
        n = len(cfg_results)
        p = np.mean([r["minicheck"]["precision"] for r in cfg_results])
        rec = np.mean([r["minicheck"]["recall"] for r in cfg_results])
        f1 = np.mean([r["minicheck"]["f1"] for r in cfg_results])
        gs = np.mean([r["minicheck"]["n_gen_sentences"] for r in cfg_results])
        es = np.mean([r["minicheck"]["n_exp_sentences"] for r in cfg_results])
        lines.append(f"| {cfg} | {n} | {p:.3f} | {rec:.3f} | {f1:.3f} | {gs:.1f} | {es:.1f} |")
    lines.append("")

    # --- By category ---
    categories = sorted(set(r["category"] for r in scored))
    lines.extend(["## By Category", ""])
    lines.append("| Category | N | Precision | Recall | F1 |")
    lines.append("|----------|--:|:---------:|:------:|:--:|")

    for cat in categories:
        cat_results = [r for r in scored if r["category"] == cat]
        n = len(cat_results)
        p = np.mean([r["minicheck"]["precision"] for r in cat_results])
        rec = np.mean([r["minicheck"]["recall"] for r in cat_results])
        f1 = np.mean([r["minicheck"]["f1"] for r in cat_results])
        lines.append(f"| {cat} | {n} | {p:.3f} | {rec:.3f} | {f1:.3f} |")
    lines.append("")

    # --- Comparison with judge faithfulness ---
    lines.extend(["## Comparison: MiniCheck vs LLM Judge Faithfulness", ""])

    judge_faith = []
    mc_f1 = []
    mc_prec = []
    for r in scored:
        jf = r.get("judge_scores", {}).get("faithfulness")
        if jf is not None:
            judge_faith.append(jf)
            mc_f1.append(r["minicheck"]["f1"])
            mc_prec.append(r["minicheck"]["precision"])

    if len(judge_faith) > 10:
        from scipy.stats import spearmanr
        jf_arr = np.array(judge_faith, dtype=float)
        mc_arr = np.array(mc_f1, dtype=float)
        mp_arr = np.array(mc_prec, dtype=float)

        rho_f1, p_f1 = spearmanr(jf_arr, mc_arr)
        rho_p, p_p = spearmanr(jf_arr, mp_arr)

        lines.append(f"- **Judge faithfulness mean**: {np.mean(jf_arr):.2f} / 5.0")
        lines.append(f"- **MiniCheck F1 mean**: {np.mean(mc_arr):.3f}")
        lines.append(f"- **MiniCheck precision mean**: {np.mean(mp_arr):.3f}")
        lines.append(f"- **Spearman ρ (judge vs MiniCheck F1)**: {rho_f1:.3f} (p={p_f1:.4f})")
        lines.append(f"- **Spearman ρ (judge vs MiniCheck precision)**: {rho_p:.3f} (p={p_p:.4f})")
        lines.append("")

        # Per-config comparison
        lines.append("| Config | Judge Faith. | MC Precision | MC Recall | MC F1 | Δ (normalized) |")
        lines.append("|--------|:-----------:|:-----------:|:--------:|:----:|:--------------:|")
        for cfg in configs:
            cfg_results = [r for r in scored if r["config"] == cfg]
            jf_cfg = [r["judge_scores"].get("faithfulness", 0) for r in cfg_results
                       if r.get("judge_scores", {}).get("faithfulness") is not None]
            mc_cfg = [r["minicheck"]["f1"] for r in cfg_results]
            mc_p_cfg = [r["minicheck"]["precision"] for r in cfg_results]
            mc_r_cfg = [r["minicheck"]["recall"] for r in cfg_results]
            if jf_cfg:
                jf_norm = np.mean(jf_cfg) / 5.0  # Normalize to 0-1
                delta = jf_norm - np.mean(mc_cfg)
                lines.append(
                    f"| {cfg} | {np.mean(jf_cfg):.2f} | "
                    f"{np.mean(mc_p_cfg):.3f} | {np.mean(mc_r_cfg):.3f} | "
                    f"{np.mean(mc_cfg):.3f} | {delta:+.3f} |"
                )
        lines.append("")
        lines.append("*Δ (normalized) = Judge/5 - MC F1. Positive = judge overrates relative to MiniCheck.*")

    lines.append("")

    # --- Methodology ---
    lines.extend([
        "## Methodology",
        "",
        "MiniCheck (Tang et al., EMNLP 2024) is a 770M-parameter fact-checker trained on",
        "synthetic data with structured factual error injection. It performs sentence-level",
        "textual entailment, checking whether a claim is supported by a grounding document.",
        "",
        "We repurpose it bidirectionally:",
        "- **Precision**: Each generated answer sentence is checked against the expected answer.",
        "  High precision means the generated content is entailed by ground truth (no hallucination).",
        "- **Recall**: Each expected answer sentence is checked against the generated answer.",
        "  High recall means the generated answer covers all expected content (completeness).",
        "- **F1**: Harmonic mean of precision and recall.",
        "",
        "This provides an independent, model-based faithfulness metric that does not rely on",
        "the same LLM judge used for primary scoring, avoiding self-evaluation bias.",
        "",
        "**Limitation**: MiniCheck is strict on numerical reasoning — it does not perform unit",
        "conversions (e.g., '1.4 TB' vs '1378 GB' is marked unsupported). This may slightly",
        "underestimate precision for answers with paraphrased numerical values.",
    ])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 5. MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MiniCheck faithfulness scoring for V4 experiments",
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
        "--max-results", type=int, default=None,
        help="Limit number of results to score (for testing)",
    )
    parser.add_argument(
        "--output-prefix", type=str, default="v4_minicheck",
        help="Output file prefix",
    )
    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Load results
    results, meta = load_results(args.input)
    logger.info(f"Loaded {len(results)} results from {args.input.name}")

    # Initialize MiniCheck
    logger.info("Loading MiniCheck (Flan-T5-Large, 770M params)...")
    from minicheck.minicheck import MiniCheck
    scorer = MiniCheck(model_name='flan-t5-large', cache_dir='./ckpts')
    logger.info("MiniCheck loaded.")

    # Score
    scored = run_minicheck_scoring(results, args.gt, scorer, args.max_results)

    # Report
    report = generate_report(scored, meta, str(args.input))

    # Save
    output_data = {
        "experiment": "minicheck_faithfulness",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "input_file": str(args.input),
        "model": "MiniCheck-FT5 (flan-t5-large, 770M)",
        "n_scored": len(scored),
        "per_result": scored,
    }
    json_path, _ = save_v4_results(output_data, args.output_prefix)
    md_path = save_v4_markdown(report, args.output_prefix)

    print(f"\n{'='*70}")
    print("MINICHECK SCORING COMPLETE")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print(f"\n{report[:5000]}")


if __name__ == "__main__":
    main()
