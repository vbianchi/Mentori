#!/usr/bin/env python3
"""
V4-7: Full System Evaluation

Does multi-agent orchestration improve quality beyond the RAG pipeline alone?
And does structured code generation (coder_v2) beat free-form?

This wraps the orchestration and coder experiments with V4-style pass-rate metrics.

Part A — Orchestration:
  4 additive configs: zero_shot → llm_with_rag → orchestrator_no_supervisor → orchestrator_full
  Questions: V4 ground truth (paper-level for min_core <= 20)

Part B — Coder:
  2 configs: free_form vs coder_v2
  Bioinformatics tasks from V4 coder ground truth

Usage:
    # Full run
    uv run python publication/scripts/exp_04_system.py

    # Part A only
    uv run python publication/scripts/exp_04_system.py --part orchestration

    # Part B only
    uv run python publication/scripts/exp_04_system.py --part coder

    # Smoke test
    uv run python publication/scripts/exp_04_system.py --part orchestration --max-questions 3
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default TOOL_SERVER_URL to localhost when running outside Docker
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from exp_common import (
    save_v4_results, save_v4_markdown,
    compute_pass_rate, compute_median_latency, compute_mean_score,
    detect_judge_key,
    format_v4_table, format_pct, format_latency, format_score,
    V4_RESULTS_DIR, V4_GROUND_TRUTH,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_04_system")
logger.setLevel(logging.INFO)


def _run_exp5(extra_args: List[str] = None):
    """Run orchestration experiment via subprocess."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "tests" / "experiments" / "exp5_orchestration.py"),
    ]
    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def _run_exp6(extra_args: List[str] = None):
    """Run coder experiment via subprocess."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "tests" / "experiments" / "exp6_coder_agent.py"),
    ]
    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def _reformat_exp5_results() -> Optional[str]:
    """Load exp5 results and reformat with V4 pass-rate metrics."""
    # TODO: Update to load V4 orchestration results once available
    from tests.experiments_v2.exp_v2_common import find_v1_latest

    path = find_v1_latest("exp5")
    if not path:
        logger.warning("No exp5 results found.")
        return None

    with open(path) as f:
        data = json.load(f)

    results = data.get("per_question_results", [])
    configs = data.get("configs", [])
    judge_key = detect_judge_key(results)

    headers = ["Config", "% Pass", "Mean Corr.", "Med. Latency", "N"]
    rows = []

    for config in configs:
        cr = [r for r in results if r["config"] == config]
        if not cr:
            continue
        pr = compute_pass_rate(cr, judge_key=judge_key)
        ms = compute_mean_score(cr, judge_key=judge_key)
        ml = compute_median_latency(cr)
        rows.append([
            config,
            format_pct(pr),
            format_score(ms),
            format_latency(ml),
            str(len(cr)),
        ])

    table = format_v4_table(headers, rows, ["l", "r", "r", "r", "r"])

    md_lines = [
        "## Part A: Multi-Agent Orchestration",
        "",
        f"**Data source**: `{path.name}`",
        "",
        table,
        "",
    ]

    return "\n".join(md_lines)


def _reformat_exp6_results() -> Optional[str]:
    """Load exp6 results and reformat with V4 success-rate metrics."""
    # TODO: Update to load V4 coder results once available
    from tests.experiments_v2.exp_v2_common import find_v1_latest

    path = find_v1_latest("exp6")
    if not path:
        logger.warning("No exp6 results found.")
        return None

    with open(path) as f:
        data = json.load(f)

    results = data.get("per_task_results", [])
    configs = data.get("configs", [])
    summary = data.get("aggregate_summary", {})

    headers = ["Config", "Success Rate", "Code Quality", "Sci. Correctness", "Completeness", "Med. Latency"]
    rows = []

    for config in configs:
        s = summary.get(config, {})
        cr = [r for r in results if r["config"] == config]
        latencies = [
            r.get("generation", {}).get("latency_s", 0)
            for r in cr if r.get("generation", {}).get("latency_s", 0) > 0
        ]

        import statistics
        med_lat = statistics.median(latencies) if latencies else 0

        rows.append([
            config,
            f"{s.get('success_rate', 0):.0f}%",
            f"{s.get('code_quality_mean', 0):.1f}",
            f"{s.get('scientific_correctness_mean', 0):.1f}",
            f"{s.get('completeness_mean', 0):.1f}",
            format_latency(med_lat),
        ])

    table = format_v4_table(headers, rows, ["l", "r", "r", "r", "r", "r"])

    md_lines = [
        "## Part B: Coder Agent",
        "",
        f"**Data source**: `{path.name}`",
        "",
        table,
        "",
    ]

    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="V4-7: Full System Evaluation"
    )
    parser.add_argument(
        "--part",
        choices=["orchestration", "coder", "both"],
        default="both",
        help="Which part to run (default: both)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
        help="Limit questions for orchestration part",
    )
    parser.add_argument(
        "--max-tasks", type=int, default=None,
        help="Limit tasks for coder part",
    )
    parser.add_argument(
        "--resume", action="store_true",
    )
    parser.add_argument(
        "--reformat-only", action="store_true",
        help="Only reformat existing results (no new runs)",
    )

    args = parser.parse_args()

    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.reformat_only:
        extra = []
        if args.resume:
            extra.append("--resume")

        if args.part in ("orchestration", "both"):
            exp5_args = list(extra)
            if args.max_questions:
                exp5_args.extend(["--max-questions", str(args.max_questions)])
            logger.info("Running Part A: Orchestration (exp5)")
            _run_exp5(exp5_args)

        if args.part in ("coder", "both"):
            exp6_args = list(extra)
            if args.max_tasks:
                exp6_args.extend(["--max-tasks", str(args.max_tasks)])
            logger.info("Running Part B: Coder (exp6)")
            _run_exp6(exp6_args)

    # Reformat
    md_sections = [
        "# V4-7: Full System Evaluation",
        "",
    ]

    if args.part in ("orchestration", "both"):
        part_a = _reformat_exp5_results()
        if part_a:
            md_sections.append(part_a)

    if args.part in ("coder", "both"):
        part_b = _reformat_exp6_results()
        if part_b:
            md_sections.append(part_b)

    md_content = "\n".join(md_sections)

    if md_content.strip() == "# V4-7: Full System Evaluation":
        print("No results available to reformat.")
        return

    md_path = save_v4_markdown(md_content, "v4_7_system")

    print(f"\n{'='*70}")
    print("V4-7 COMPLETE: Full System Evaluation")
    print(f"{'='*70}")
    print(f"Report: {md_path}")
    print()
    print(md_content[:2000])


if __name__ == "__main__":
    main()
