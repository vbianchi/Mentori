#!/usr/bin/env python3
"""
V2-5: Scaling Robustness (The Killer Experiment)

As corpus grows from 5 to 100 papers, which generation methods degrade and
which stay stable?

Design:
  Indexes: exp_s5, exp_s10, exp_s20, exp_s50, exp_s100
  Questions: 20 answerable only
  6 configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass
  = 600 total runs

Primary metric: % pass rate at each scale
Secondary: median latency per (config, scale)

Output: The "killer table" showing pass rate degradation patterns.

Usage:
    # Full run (~8 hours)
    uv run python tests/experiments_v2/exp_v2_5_scaling.py

    # Smoke test
    uv run python tests/experiments_v2/exp_v2_5_scaling.py \\
        --indexes exp_s5 --configs single_pass --max-questions 3

    # Add specific new configs
    uv run python tests/experiments_v2/exp_v2_5_scaling.py \\
        --configs rlm_5 rlm_10 --resume

    # Resume after interruption
    uv run python tests/experiments_v2/exp_v2_5_scaling.py --resume
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
    compute_pass_rate, compute_median_latency, compute_mean_score,
    detect_judge_key,
    format_v2_table, format_pct, format_latency,
    V2_DIR, V2_RESULTS_DIR,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_v2_5")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = Path(__file__).parent.parent / "experiments" / "ground_truth_exp1.json"
INTERMEDIATE_FILE = V2_RESULTS_DIR / "v2_5_intermediate.json"

ALL_INDEXES = ["exp_s5", "exp_s10", "exp_s20", "exp_s50", "exp_s100"]

CONFIG_NAMES = [
    "single_pass",
    "multi_hop",
    "rlm_5",
    "rlm_10",
    "rlm_20",
    "verified_pass",
]


# ─────────────────────────────────────────────────────────────
# Config dispatch
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
    """Dispatch to the right generator."""
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
    indexes: List[str],
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
):
    """Run V2-5 scaling experiment."""
    # Load answerable questions only
    questions = load_ground_truth(GT_FILE, answerable_only=True)
    if max_questions:
        questions = questions[:max_questions]

    logger.info(f"V2-5: Scaling Robustness")
    logger.info(f"Questions: {len(questions)} (answerable only)")
    logger.info(f"Indexes: {indexes}")
    logger.info(f"Configs: {configs}")

    user_id = find_admin_user_id()
    configure_gemini_from_admin()
    router = ModelRouter()

    # Verify indexes
    for idx_name in indexes:
        if not check_index_exists(user_id, idx_name):
            logger.error(f"Index {idx_name} not found. Skipping.")
            indexes = [i for i in indexes if i != idx_name]

    if not indexes:
        logger.error("No valid indexes. Aborting.")
        sys.exit(1)

    # Resume
    intermediate = load_intermediate(INTERMEDIATE_FILE) if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total = len(indexes) * len(configs) * len(questions)
    done = 0

    for idx_name in indexes:
        logger.info(f"\n{'='*60}")
        logger.info(f"INDEX: {idx_name}")
        logger.info(f"{'='*60}")

        retriever, collection_name, _ = setup_retriever(user_id, idx_name)

        for config in configs:
            for q in questions:
                qid = q["id"]
                key = result_key(idx_name, config, qid)

                if key in completed:
                    done += 1
                    continue

                done += 1
                logger.info(
                    f"[{done}/{total}] {idx_name} | {config} | {qid}: "
                    f"{q['question'][:50]}..."
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
                        index_name=idx_name,
                    )
                except Exception as e:
                    logger.error(f"Generation failed: {e}")
                    gen_result = GenerationResult(
                        answer="", latency_s=0, llm_calls=0, tokens_used=0,
                        retrieved_passages=0, config=config, gen_model=GEN_MODEL,
                        error=str(e),
                    )

                # Judge
                scores = {}
                if gen_result.answer and not gen_result.error:
                    try:
                        scores = await judge_answer(
                            question=q["question"],
                            expected=q.get("expected_answer", ""),
                            concepts=q.get("expected_concepts", []),
                            generated=gen_result.answer,
                            router=router,
                            answerable=True,
                        )
                    except Exception as e:
                        logger.error(f"Judge error: {e}")

                # Citations
                cit_metrics = _evaluate_citations(
                    gen_result.answer, q.get("source_files", [])
                )

                result_entry = {
                    "index_name": idx_name,
                    "question_id": qid,
                    "question": q["question"],
                    "category": q.get("category", "unknown"),
                    "answerable": True,
                    "config": config,
                    "gen_model": GEN_MODEL,
                    "generation": asdict(gen_result),
                    "judge_scores": scores,
                    "citation_metrics": asdict(cit_metrics),
                }

                all_results.append(result_entry)
                completed.add(key)

                save_intermediate(
                    {"results": all_results, "completed_keys": list(completed)},
                    INTERMEDIATE_FILE,
                )

            logger.info(f"Completed {idx_name} / {config}")

    # ── Report ──
    _generate_report(all_results, indexes, configs, len(questions))

    if INTERMEDIATE_FILE.exists():
        INTERMEDIATE_FILE.unlink()


def _generate_report(
    all_results: List[Dict],
    indexes: List[str],
    configs: List[str],
    n_questions: int,
):
    """Generate V2-5 killer table and latency table."""
    judge_key = detect_judge_key(all_results)

    # ── Pass rate table ──
    pass_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes] + ["Trend"]
    pass_rows = []

    latency_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    latency_rows = []

    for config in configs:
        pass_row = [config]
        lat_row = [config]
        rates = []

        for idx_name in indexes:
            idx_results = [
                r for r in all_results
                if r["config"] == config and r["index_name"] == idx_name
            ]
            if not idx_results:
                pass_row.append("-")
                lat_row.append("-")
                continue

            pr = compute_pass_rate(idx_results, judge_key=judge_key)
            rates.append(pr)
            pass_row.append(format_pct(pr))

            ml = compute_median_latency(idx_results)
            lat_row.append(format_latency(ml))

        # Compute trend
        trend = _compute_trend(rates)
        pass_row.append(trend)
        pass_rows.append(pass_row)
        latency_rows.append(lat_row)

    pass_table = format_v2_table(
        pass_headers, pass_rows,
        ["l"] + ["r"] * len(indexes) + ["c"],
    )

    latency_table = format_v2_table(
        latency_headers, latency_rows,
        ["l"] + ["r"] * len(indexes),
    )

    # ── Mean correctness table ──
    corr_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    corr_rows = []

    for config in configs:
        corr_row = [config]
        for idx_name in indexes:
            idx_results = [
                r for r in all_results
                if r["config"] == config and r["index_name"] == idx_name
            ]
            if not idx_results:
                corr_row.append("-")
                continue
            ms = compute_mean_score(idx_results, judge_key=judge_key)
            corr_row.append(f"{ms:.2f}")
        corr_rows.append(corr_row)

    corr_table = format_v2_table(
        corr_headers, corr_rows,
        ["l"] + ["r"] * len(indexes),
    )

    # ── Markdown ──
    md_lines = [
        "# V2-5: Scaling Robustness",
        "",
        f"**Model**: `{GEN_MODEL}` | **Questions**: {n_questions} (answerable only)",
        f"**Pass threshold**: correctness >= 3",
        "",
        "## % Pass Rate (correctness >= 3)",
        "",
        pass_table,
        "",
        "## Median Latency (seconds)",
        "",
        latency_table,
        "",
        "## Mean Correctness (0-5)",
        "",
        corr_table,
        "",
    ]

    md_content = "\n".join(md_lines)

    # ── Save ──
    output = {
        "experiment": "v2_5_scaling",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "indexes": indexes,
        "configs": configs,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "n_questions": n_questions,
        "pass_threshold": 3,
        "per_question_results": all_results,
    }

    json_path, _ = save_v2_results(output, "v2_5_scaling")
    md_path = save_v2_markdown(md_content, "v2_5_scaling")

    print(f"\n{'='*70}")
    print("V2-5 COMPLETE: Scaling Robustness")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:3000])


def _compute_trend(rates: List[float]) -> str:
    """Compute a trend indicator from a sequence of pass rates."""
    if len(rates) < 2:
        return "?"

    first_half = rates[:len(rates) // 2 + 1]
    second_half = rates[len(rates) // 2:]

    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0

    diff = avg_second - avg_first

    if diff > 10:
        return "^ RISE"
    elif diff > -5:
        return "-> FLAT"
    elif diff > -20:
        return "v DECLINE"
    else:
        return "vv COLLAPSE"


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V2-5: Scaling Robustness"
    )
    parser.add_argument(
        "--indexes", nargs="+", default=ALL_INDEXES,
        help=f"Indexes to test (default: {ALL_INDEXES})",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help="Configs to test (default: all 6)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
        help="Limit questions (smoke testing)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate results",
    )

    args = parser.parse_args()

    asyncio.run(run_experiment(
        indexes=args.indexes,
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
    ))


if __name__ == "__main__":
    main()
