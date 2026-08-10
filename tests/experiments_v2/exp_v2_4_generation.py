#!/usr/bin/env python3
"""
V2-4: Generation Strategy Comparison (Fixed Scale)

With retrieval held constant at s20, which generation strategy produces the
best answers?

Design:
  Index: exp_s20 (20 papers)
  Questions: 20 answerable + 17 unanswerable/OOD = 37 total
  6 configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass

Primary metric: % pass rate (correctness >= 3)
Secondary: % correct refusal (unanswerable), median latency, source coverage

Usage:
    # Full run
    uv run python tests/experiments_v2/exp_v2_4_generation.py

    # Smoke test
    uv run python tests/experiments_v2/exp_v2_4_generation.py \\
        --configs single_pass --max-questions 3

    # Resume
    uv run python tests/experiments_v2/exp_v2_4_generation.py --resume

    # Specific configs
    uv run python tests/experiments_v2/exp_v2_4_generation.py \\
        --configs single_pass rlm_10 verified_pass
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from tests.experiments_v2.exp_v2_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever,
    load_ground_truth, load_intermediate, save_intermediate, result_key,
    judge_answer,
    save_v2_results, save_v2_markdown,
    compute_pass_rate, compute_refusal_rate, compute_median_latency,
    compute_mean_source_coverage, compute_mean_score,
    aggregate_v2_metrics, detect_judge_key,
    format_v2_table, format_pct, format_latency, format_score,
    V2_DIR, V2_RESULTS_DIR,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_v2_4")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = Path(__file__).parent.parent / "experiments" / "ground_truth_exp1.json"
INTERMEDIATE_FILE = V2_RESULTS_DIR / "v2_4_intermediate.json"
DEFAULT_INDEX = "exp_s20"

CONFIG_NAMES = [
    "single_pass",
    "multi_hop",
    "rlm_5",
    "rlm_10",
    "rlm_20",
    "verified_pass",
]

CATEGORIES = [
    "factual_recall", "conceptual", "technical",
    "synthesis", "cross_document", "out_of_domain",
]


# ─────────────────────────────────────────────────────────────
# Config dispatch (reuses exp1 generators)
# ─────────────────────────────────────────────────────────────

async def _run_config(
    config_name: str,
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
    user_id: str,
    index_name: str,
) -> GenerationResult:
    """Dispatch to the right generator based on config name."""
    if config_name == "single_pass":
        return await _single_pass_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == "multi_hop":
        return await _multi_hop_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == "rlm_5":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=5, config_name="rlm_5", index_name=index_name)
    elif config_name == "rlm_10":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name="rlm_10", index_name=index_name)
    elif config_name == "rlm_20":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=20, config_name="rlm_20", index_name=index_name)
    elif config_name == "verified_pass":
        return await _verified_pass_rag(question, retriever, collection_name, router, gen_model)
    else:
        raise ValueError(f"Unknown config: {config_name}")


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

async def run_experiment(
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    index_name: str = DEFAULT_INDEX,
):
    """Run V2-4 generation comparison."""
    if not GT_FILE.exists():
        logger.error(f"Ground truth not found: {GT_FILE}")
        sys.exit(1)

    with open(GT_FILE) as f:
        gt_data = json.load(f)

    questions = gt_data["questions"]
    if max_questions:
        questions = questions[:max_questions]

    n_answerable = sum(1 for q in questions if q.get("answerable", True))
    n_unanswerable = len(questions) - n_answerable

    logger.info(f"V2-4: Generation Strategy Comparison")
    logger.info(f"Questions: {len(questions)} ({n_answerable} answerable, {n_unanswerable} unanswerable)")
    logger.info(f"Configs: {configs}")
    logger.info(f"Index: {index_name}")

    user_id = find_admin_user_id()
    if not check_index_exists(user_id, index_name):
        logger.error("Index check failed. Aborting.")
        sys.exit(1)

    # Configure Gemini if needed
    configure_gemini_from_admin()

    router = ModelRouter()
    retriever, collection_name, embedding_model = setup_retriever(user_id, index_name)

    # Resume support
    intermediate = load_intermediate(INTERMEDIATE_FILE) if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total = len(configs) * len(questions)
    done = 0

    for config in configs:
        for q in questions:
            qid = q["id"]
            key = result_key(config, qid)

            if key in completed:
                done += 1
                continue

            done += 1
            is_answerable = q.get("answerable", True)
            logger.info(
                f"[{done}/{total}] {config} | {qid} ({'A' if is_answerable else 'U'}): "
                f"{q['question'][:60]}..."
            )

            # Generate
            try:
                gen_result = await _run_config(
                    config_name=config,
                    question=q["question"],
                    retriever=retriever,
                    collection_name=collection_name,
                    router=router,
                    gen_model=GEN_MODEL,
                    user_id=user_id,
                    index_name=index_name,
                )
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                gen_result = GenerationResult(
                    answer="", latency_s=0, llm_calls=0, tokens_used=0,
                    retrieved_passages=0, config=config, gen_model=GEN_MODEL,
                    error=str(e),
                )

            # Judge
            judge_scores = {}
            if gen_result.answer and not gen_result.error:
                try:
                    judge_scores = await judge_answer(
                        question=q["question"],
                        expected=q.get("expected_answer", ""),
                        concepts=q.get("expected_concepts", []),
                        generated=gen_result.answer,
                        router=router,
                        answerable=is_answerable,
                    )
                except Exception as e:
                    logger.error(f"Judge error: {e}")

            # Citations
            expected_sources = q.get("source_files", [])
            if isinstance(q.get("source_file"), str) and not expected_sources:
                expected_sources = [q["source_file"]]
            cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

            result_entry = {
                "question_id": qid,
                "question": q["question"],
                "category": q.get("category", "unknown"),
                "difficulty": q.get("difficulty", "unknown"),
                "answerable": is_answerable,
                "config": config,
                "gen_model": GEN_MODEL,
                "generation": asdict(gen_result),
                "judge_scores": judge_scores,
                "citation_metrics": asdict(cit_metrics),
            }

            all_results.append(result_entry)
            completed.add(key)

            save_intermediate(
                {"results": all_results, "completed_keys": list(completed)},
                INTERMEDIATE_FILE,
            )

        logger.info(f"Completed config: {config}")

    # ── V2 Metrics & Report ──
    _generate_report(all_results, configs, index_name, n_answerable, n_unanswerable)

    # Cleanup intermediate
    if INTERMEDIATE_FILE.exists():
        INTERMEDIATE_FILE.unlink()
        logger.info("Cleaned up intermediate file")


def _generate_report(
    all_results: List[Dict],
    configs: List[str],
    index_name: str,
    n_answerable: int,
    n_unanswerable: int,
):
    """Generate V2-4 report with pass rate tables."""
    judge_key = detect_judge_key(all_results)

    # ── Main comparison table ──
    headers = ["Config", "% Pass", "% Refuse", "Med. Latency", "Source Cov.", "Mean Corr."]
    rows = []

    config_metrics = {}
    for config in configs:
        config_results = [r for r in all_results if r["config"] == config]
        if not config_results:
            continue
        metrics = aggregate_v2_metrics(config_results, judge_key=judge_key)
        config_metrics[config] = metrics

        rows.append([
            config,
            format_pct(metrics["pass_rate"]),
            format_pct(metrics["refusal_rate"]) if metrics["n_unanswerable"] > 0 else "-",
            format_latency(metrics["median_latency"]),
            format_score(metrics["source_coverage"]),
            format_score(metrics["mean_correctness"]),
        ])

    main_table = format_v2_table(
        headers, rows,
        ["l", "r", "r", "r", "r", "r"],
    )

    # ── Per-category breakdown ──
    cat_tables = []
    all_categories = sorted(set(r.get("category", "unknown") for r in all_results))

    for cat in all_categories:
        cat_results = [r for r in all_results if r.get("category") == cat]
        if not cat_results:
            continue

        cat_rows = []
        for config in configs:
            cr = [r for r in cat_results if r["config"] == config]
            if not cr:
                continue
            answerable_cr = [r for r in cr if r.get("answerable", True)]
            if answerable_cr:
                pr = compute_pass_rate(answerable_cr, judge_key=judge_key)
                ms = compute_mean_score(answerable_cr, judge_key=judge_key)
                cat_rows.append([config, format_pct(pr), format_score(ms), str(len(answerable_cr))])

        if cat_rows:
            cat_table = format_v2_table(
                ["Config", "% Pass", "Mean Corr.", "N"],
                cat_rows,
                ["l", "r", "r", "r"],
            )
            cat_tables.append((cat, cat_table))

    # ── Build markdown report ──
    md_lines = [
        "# V2-4: Generation Strategy Comparison (Fixed Scale)",
        "",
        f"**Index**: `{index_name}` | **Model**: `{GEN_MODEL}`",
        f"**Questions**: {n_answerable} answerable + {n_unanswerable} unanswerable = {n_answerable + n_unanswerable} total",
        f"**Pass threshold**: correctness >= 3",
        "",
        "## Main Results",
        "",
        main_table,
        "",
    ]

    if cat_tables:
        md_lines.append("## Per-Category Breakdown")
        md_lines.append("")
        for cat, table in cat_tables:
            md_lines.append(f"### {cat}")
            md_lines.append("")
            md_lines.append(table)
            md_lines.append("")

    md_content = "\n".join(md_lines)

    # ── Save ──
    output = {
        "experiment": "v2_4_generation",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "index_name": index_name,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "configs": configs,
        "n_answerable": n_answerable,
        "n_unanswerable": n_unanswerable,
        "pass_threshold": 3,
        "config_metrics": config_metrics,
        "per_question_results": all_results,
    }

    json_path, _ = save_v2_results(output, "v2_4_generation")
    md_path = save_v2_markdown(md_content, "v2_4_generation")

    print(f"\n{'='*70}")
    print("V2-4 COMPLETE: Generation Strategy Comparison")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:3000])


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V2-4: Generation Strategy Comparison"
    )
    parser.add_argument(
        "--index", default=DEFAULT_INDEX,
        help=f"Index name (default: {DEFAULT_INDEX})",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help="Configs to test (default: all 6)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
        help="Limit number of questions (for smoke testing)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate results",
    )

    args = parser.parse_args()

    asyncio.run(run_experiment(
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
        index_name=args.index,
    ))


if __name__ == "__main__":
    main()
