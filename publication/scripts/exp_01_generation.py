#!/usr/bin/env python3
"""
V4-4: Generation Strategy Comparison (Fixed Scale)

With retrieval held constant at s20_n0, which generation strategy produces the
best answers?

Design:
  Index: exp_v4_s20_n0 (20 core papers, 0 noise)
  Questions: From V4 ground truth (paper-level questions for min_core <= 20)
  6 configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass

Primary metric: % pass rate (correctness >= 3)
Secondary: % correct refusal (unanswerable), median latency, source coverage

Usage:
    # Full run
    uv run python publication/scripts/exp_01_generation.py

    # Smoke test
    uv run python publication/scripts/exp_01_generation.py \\
        --configs single_pass --max-questions 3

    # Resume
    uv run python publication/scripts/exp_01_generation.py --resume

    # Specific configs
    uv run python publication/scripts/exp_01_generation.py \\
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

from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever,
    load_ground_truth, load_intermediate, save_intermediate, result_key,
    judge_answer,
    save_v4_results, save_v4_markdown,
    compute_pass_rate, compute_refusal_rate, compute_median_latency,
    compute_mean_source_coverage, compute_mean_score,
    aggregate_v4_metrics, detect_judge_key,
    format_v4_table, format_pct, format_latency, format_score,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_01_generation")
logger.setLevel(logging.INFO)


def _index_core_size(index_name: str) -> int:
    """Extract core paper count from index name like 'exp_v4_s20_n0'."""
    import re
    m = re.search(r"_s(\d+)_", index_name)
    return int(m.group(1)) if m else 50

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = V4_GROUND_TRUTH
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_4_intermediate.json"
DEFAULT_INDEX = "exp_v4_s20_n0"

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

async def _process_one(
    config: str,
    q: Dict,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> Dict:
    """Generate + judge + cite one (config, question) pair."""
    qid = q["id"]
    is_answerable = q.get("answerable", True)

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

    return {
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


# Concurrency: RLM configs are heavy (many sequential Gemini calls per question),
# so we use lower batch sizes to avoid Gemini rate limits.
# Fast configs (single_pass, multi_hop, verified_pass) can run higher concurrency.
BATCH_SIZE_FAST = 6   # single_pass, multi_hop, verified_pass
BATCH_SIZE_RLM = 2    # rlm_5, rlm_10, rlm_20

RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20"}


async def run_experiment(
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    index_name: str = DEFAULT_INDEX,
):
    """Run V4-4 generation comparison (batched parallel within each config)."""
    if not GT_FILE.exists():
        logger.error(f"Ground truth not found: {GT_FILE}")
        sys.exit(1)

    with open(GT_FILE) as f:
        gt_data = json.load(f)

    questions = gt_data["questions"]

    # Filter to questions valid for this index (min_core <= core_size, or OOD)
    core_size = _index_core_size(index_name)
    questions = [
        q for q in questions
        if q.get("category") == "out_of_domain"
        or (q.get("min_core") is not None and q["min_core"] <= core_size)
    ]

    if max_questions:
        questions = questions[:max_questions]

    n_answerable = sum(1 for q in questions if q.get("answerable", True))
    n_unanswerable = len(questions) - n_answerable

    logger.info(f"V4-4: Generation Strategy Comparison (batched parallel)")
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
    skipped = sum(1 for c in configs for q in questions if result_key(c, q["id"]) in completed)
    logger.info(f"Skipping {skipped} already-completed, {total - skipped} remaining")

    done = skipped

    for config in configs:
        pending = [q for q in questions if result_key(config, q["id"]) not in completed]
        if not pending:
            logger.info(f"Config {config}: all done, skipping")
            continue

        batch_size = BATCH_SIZE_RLM if config in RLM_CONFIGS else BATCH_SIZE_FAST
        logger.info(f"Config {config}: {len(pending)} questions, batch_size={batch_size}")

        # Process in batches
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            batch_start = done + 1

            for q in batch:
                done += 1
                logger.info(
                    f"[{done}/{total}] {config} | {q['id']} "
                    f"({'A' if q.get('answerable', True) else 'U'}): "
                    f"{q['question'][:60]}..."
                )

            # Run batch concurrently
            tasks = [
                _process_one(
                    config=config, q=q,
                    retriever=retriever, collection_name=collection_name,
                    router=router, user_id=user_id, index_name=index_name,
                )
                for q in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Save completed results from this batch
            for q, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Task failed for {q['id']}: {result}")
                    result = {
                        "question_id": q["id"],
                        "question": q["question"],
                        "category": q.get("category", "unknown"),
                        "difficulty": q.get("difficulty", "unknown"),
                        "answerable": q.get("answerable", True),
                        "config": config,
                        "gen_model": GEN_MODEL,
                        "generation": asdict(GenerationResult(
                            answer="", latency_s=0, llm_calls=0, tokens_used=0,
                            retrieved_passages=0, config=config, gen_model=GEN_MODEL,
                            error=str(result),
                        )),
                        "judge_scores": {},
                        "citation_metrics": asdict(_evaluate_citations("", [])),
                    }
                all_results.append(result)
                completed.add(result_key(config, q["id"]))

            save_intermediate(
                {"results": all_results, "completed_keys": list(completed)},
                INTERMEDIATE_FILE,
            )
            logger.info(f"  Batch saved ({len(batch)} results, total {len(all_results)})")

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
    """Generate V4-4 report with pass rate tables."""
    judge_key = detect_judge_key(all_results)

    # ── Main comparison table ──
    headers = ["Config", "% Pass", "% Refuse", "Med. Latency", "Source Cov.", "Mean Corr."]
    rows = []

    config_metrics = {}
    for config in configs:
        config_results = [r for r in all_results if r["config"] == config]
        if not config_results:
            continue
        metrics = aggregate_v4_metrics(config_results, judge_key=judge_key)
        config_metrics[config] = metrics

        rows.append([
            config,
            format_pct(metrics["pass_rate"]),
            format_pct(metrics["refusal_rate"]) if metrics["n_unanswerable"] > 0 else "-",
            format_latency(metrics["median_latency"]),
            format_score(metrics["source_coverage"]),
            format_score(metrics["mean_correctness"]),
        ])

    main_table = format_v4_table(
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
            cat_table = format_v4_table(
                ["Config", "% Pass", "Mean Corr.", "N"],
                cat_rows,
                ["l", "r", "r", "r"],
            )
            cat_tables.append((cat, cat_table))

    # ── Build markdown report ──
    md_lines = [
        "# V4-4: Generation Strategy Comparison (Fixed Scale)",
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
        "experiment": "v4_4_generation",
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

    json_path, _ = save_v4_results(output, "v4_4_generation")
    md_path = save_v4_markdown(md_content, "v4_4_generation")

    print(f"\n{'='*70}")
    print("V4-4 COMPLETE: Generation Strategy Comparison")
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
        description="V4-4: Generation Strategy Comparison"
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
