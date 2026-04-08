#!/usr/bin/env python3
"""
V4-8: Coder Benchmark Rerun with Corrected Context Window

Reruns the V2-8 coder benchmark (objective pass/fail verification against
ground truth) with the corrected Ollama context window.

V2-8 ran ALL Ollama models with the default num_ctx=2048, which truncated
prompts and caused catastrophic failures — especially for thinking modes
that consume context with reasoning traces. The _ensure_num_ctx() fix
(2026-03-05) now injects num_ctx=24576 (24K) for all Ollama calls.

This script:
  1. Copies Gemini results from V2-8 (unaffected by Ollama context bug)
  2. Reruns all Ollama model variants with the corrected context window
  3. Outputs results to publication/results/v4_8_*

Design: 10 Ollama model variants × 11 configs × 20 ops = 2,200 evals
        + 2 Gemini models (copied) × 11 configs × 20 ops = 440 evals
        = 2,640 total

Usage:
    # Copy Gemini results from V2-8 (run first)
    uv run python publication/scripts/exp_05_coder_benchmark.py --copy-gemini

    # Run a single Ollama model
    uv run python publication/scripts/exp_05_coder_benchmark.py --model ollama::qwen3-coder:latest

    # Run with thinking mode
    uv run python publication/scripts/exp_05_coder_benchmark.py --model ollama::gpt-oss:20b --think high

    # Smoke test (3 ops only)
    uv run python publication/scripts/exp_05_coder_benchmark.py --model ollama::qwen3-coder:latest --max-ops 3

    # Resume interrupted run
    uv run python publication/scripts/exp_05_coder_benchmark.py --model ollama::qwen3-coder:latest --resume

    # Run all Ollama models sequentially
    uv run python publication/scripts/exp_05_coder_benchmark.py --run-all
"""

import argparse
import asyncio
import json
import logging
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default TOOL_SERVER_URL to localhost when running outside Docker
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

# Import V2-8 core functions
from tests.experiments_v2.exp_v2_8_coder_benchmark import (
    CONFIG_NAMES,
    ALL_DATASETS,
    ALL_COMPLEXITIES,
    _model_slug,
    _dispatch,
    load_ground_truth_ops,
    _generate_report,
)

from tests.experiments.exp_common import (
    find_admin_user_id,
    configure_gemini_from_admin,
    load_intermediate,
    save_intermediate,
)

from backend.agents.model_router import ModelRouter

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_05_coder_benchmark")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

V4_RESULTS_DIR = Path(__file__).parent / "results_v4"
V2_RESULTS_DIR = Path(__file__).parent.parent / "experiments_v2" / "results_v2"

# Ollama models to rerun (all that were in V2-8)
OLLAMA_MODELS = [
    ("ollama::qwen3-coder:latest", None),        # think=off
    ("ollama::qwen3-coder-next:q4_K_M", None),   # think=off
    ("ollama::gpt-oss:20b", None),                # think=off
    ("ollama::gpt-oss:20b", "low"),               # think=low
    ("ollama::gpt-oss:20b", "medium"),            # think=medium
    ("ollama::gpt-oss:20b", "high"),              # think=high
    ("ollama::glm-4.7-flash:bf16", None),         # think=off
    ("ollama::glm-4.7-flash:bf16", True),         # think=on
    ("ollama::nemotron-3-nano:30b", None),        # think=off
    ("ollama::nemotron-3-nano:30b", True),        # think=on
    # New models from V4-0 triage
    ("ollama::gemma3:27b", None),                 # think=off
    ("ollama::devstral-small-2:24b", None),       # think=off
    ("ollama::deepseek-r1:70b", None),            # think=off (native CoT)
]

# V2-8 Gemini result files to copy (first timestamped = full data)
GEMINI_V2_FILES = {
    "gemini-2.5-pro_think-True": "v2_8_coder_benchmark_gemini-2.5-pro_think-True_20260223_213453.json",
    "gemini-3-flash-preview_think-True": "v2_8_coder_benchmark_gemini-3-flash-preview_think-True_20260223_163219.json",
}


# ─────────────────────────────────────────────────────────────
# Copy Gemini results from V2-8
# ─────────────────────────────────────────────────────────────

def copy_gemini_results():
    """Copy V2-8 Gemini results to V4-8 output directory."""
    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0

    for model_key, v2_filename in GEMINI_V2_FILES.items():
        src = V2_RESULTS_DIR / v2_filename
        if not src.exists():
            logger.warning(f"V2-8 Gemini result not found: {src}")
            continue

        # Load, update experiment name, save to V4
        data = json.load(open(src))
        data["experiment"] = "v4_8_coder_benchmark"
        data["v2_8_source"] = v2_filename
        data["num_ctx_note"] = "Gemini API - no Ollama context window limitation"

        # Save as both timestamped and _latest for comparison tool
        v4_filename = f"v4_8_coder_benchmark_{model_key}.json"
        v4_latest = f"v4_8_coder_benchmark_{model_key}_latest.json"
        for fname in (v4_filename, v4_latest):
            dst = V4_RESULTS_DIR / fname
            with open(dst, "w") as f:
                json.dump(data, f, indent=2, default=str)
        logger.info(f"Copied: {v2_filename} -> {v4_filename} (+latest)")
        copied += 1

    logger.info(f"Copied {copied} Gemini result files to {V4_RESULTS_DIR}")
    return copied


# ─────────────────────────────────────────────────────────────
# Run experiment for a single Ollama model
# ─────────────────────────────────────────────────────────────

async def run_single_model(
    gen_model: str,
    think: Union[bool, str, None] = None,
    configs: List[str] = None,
    datasets: List[str] = None,
    complexities: List[str] = None,
    max_ops: Optional[int] = None,
    resume: bool = False,
):
    """Run coder benchmark for a single model with corrected context window."""
    configs = configs or CONFIG_NAMES
    datasets = datasets or ALL_DATASETS
    complexities = complexities or ALL_COMPLEXITIES

    # Configure Gemini API key (needed for Gemini models and Gemini-as-judge)
    configure_gemini_from_admin()

    ops = load_ground_truth_ops(datasets, complexities, max_ops)
    if not ops:
        logger.error("No operations match filters.")
        return

    model_slug = _model_slug(gen_model)
    think_suffix = f"_think-{think}" if think else ""

    logger.info(f"{'='*60}")
    logger.info(f"V4-8: Coder Benchmark (corrected num_ctx=24576)")
    logger.info(f"{'='*60}")
    logger.info(f"Model: {gen_model} | Think: {think if think else 'off'}")
    logger.info(f"Operations: {len(ops)} | Configs: {len(configs)}")
    logger.info(f"Total evals: {len(ops) * len(configs)}")
    logger.info(f"{'='*60}")

    user_id = find_admin_user_id()
    router = ModelRouter()

    base_workspace = PROJECT_ROOT / "data" / "workspace" / "v4_8_benchmark"
    base_workspace.mkdir(parents=True, exist_ok=True)

    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    intermediate_file = V4_RESULTS_DIR / f"v4_8_intermediate_{model_slug}{think_suffix}.json"

    intermediate = load_intermediate(intermediate_file) if resume else {
        "results": [], "completed_keys": []
    }
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total = len(configs) * len(ops)
    done = 0
    t_start = time.time()

    for config in configs:
        for op in ops:
            op_id = op["op_id"]
            key = f"{config}::{op_id}"

            if key in completed:
                done += 1
                continue

            done += 1
            elapsed = time.time() - t_start
            rate = done / max(elapsed, 1) * 3600
            eta_h = (total - done) / max(rate, 0.01)

            logger.info(
                f"[{done}/{total}] {config} | {op_id} "
                f"({op['complexity']}) | ETA: {eta_h:.1f}h"
            )

            # Create workspace with dataset files
            import uuid
            workspace = base_workspace / f"{config}_{op_id}_{uuid.uuid4().hex[:6]}"
            workspace.mkdir(parents=True, exist_ok=True)

            files_dir = workspace / "files"
            files_dir.mkdir(parents=True, exist_ok=True)

            datasets_dir = Path(__file__).parent.parent / "experiments_v2" / "datasets"
            for _key, filename in op["files"].items():
                src = datasets_dir / filename
                if src.exists():
                    shutil.copy2(src, files_dir / filename)

            # Run
            try:
                result = await _dispatch(
                    config, op, router, user_id, workspace,
                    gen_model=gen_model, think=think,
                )
            except Exception as e:
                import traceback
                logger.error(f"Dispatch failed: {e}\n{traceback.format_exc()}")
                result = {
                    "config": config,
                    "passed": False,
                    "field_results": {},
                    "actual_results": {},
                    "exec_error": str(e),
                    "latency_s": 0,
                    "n_cells": 0,
                    "n_llm_calls": 0,
                    "n_retries": 0,
                    "n_idle_recovered": 0,
                }

            entry = {
                "op_id": op_id,
                "dataset": op["dataset"],
                "complexity": op["complexity"],
                "category": op["category"],
                "config": config,
                "gen_model": gen_model,
                "passed": result["passed"],
                "judge_score": result.get("judge_score"),
                "judge_comment": result.get("judge_comment"),
                "field_results": result.get("field_results", {}),
                "actual_results": result.get("actual_results", {}),
                "exec_error": result.get("exec_error", ""),
                "latency_s": result.get("latency_s", 0),
                "n_cells": result.get("n_cells", 0),
                "n_llm_calls": result.get("n_llm_calls", 0),
                "n_retries": result.get("n_retries", 0),
                "n_idle_recovered": result.get("n_idle_recovered", 0),
            }

            all_results.append(entry)
            completed.add(key)

            save_intermediate(
                {"results": all_results, "completed_keys": list(completed)},
                intermediate_file,
            )

            status = "PASS" if result["passed"] else "FAIL"
            logger.info(
                f"  -> {status} ({result.get('latency_s', 0):.0f}s)"
                + (f" | {result.get('exec_error', '')[:80]}" if not result["passed"] else "")
            )

        logger.info(f"Completed config: {config}")

    # Generate V4-8 report
    _generate_v4_8_report(
        all_results, configs, datasets, complexities, ops,
        gen_model=gen_model, think=think,
    )

    # Clean up intermediate
    if intermediate_file.exists():
        intermediate_file.unlink()


def _generate_v4_8_report(
    all_results: List[Dict],
    configs: List[str],
    datasets: List[str],
    complexities: List[str],
    ops: List[Dict],
    gen_model: str = "",
    think: Union[bool, str, None] = None,
):
    """Generate V4-8 JSON + markdown reports (adapted from V2-8)."""
    import statistics

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _pass_rate(results):
        if not results:
            return 0.0
        return round(sum(1 for r in results if r["passed"]) / len(results) * 100, 1)

    def _median_lat(results):
        lats = [r["latency_s"] for r in results if r.get("latency_s", 0) > 0]
        return round(statistics.median(lats), 1) if lats else 0.0

    by_config = defaultdict(list)
    for r in all_results:
        by_config[r["config"]].append(r)

    by_config_complexity = defaultdict(list)
    for r in all_results:
        by_config_complexity[(r["config"], r["complexity"])].append(r)

    by_config_dataset = defaultdict(list)
    for r in all_results:
        by_config_dataset[(r["config"], r["dataset"])].append(r)

    summary = {}
    for config in configs:
        cr = by_config.get(config, [])
        summary[config] = {
            "pass_rate": _pass_rate(cr),
            "median_latency": _median_lat(cr),
            "n": len(cr),
            "by_complexity": {
                cx: {"pass_rate": _pass_rate(by_config_complexity.get((config, cx), [])),
                     "n": len(by_config_complexity.get((config, cx), []))}
                for cx in ALL_COMPLEXITIES
            },
            "by_dataset": {
                ds: {"pass_rate": _pass_rate(by_config_dataset.get((config, ds), [])),
                     "n": len(by_config_dataset.get((config, ds), []))}
                for ds in ALL_DATASETS
            },
        }

    model_slug = _model_slug(gen_model)
    think_suffix = f"_think-{think}" if think else ""

    output = {
        "experiment": "v4_8_coder_benchmark",
        "timestamp": timestamp,
        "gen_model": gen_model,
        "think": str(think) if think else "off",
        "num_ctx": 24576,
        "num_ctx_note": "Corrected from V2-8 default of 2048 (Ollama default)",
        "configs": configs,
        "datasets": datasets,
        "complexities": complexities,
        "n_operations": len(ops),
        "total_evaluations": len(all_results),
        "summary": summary,
        "per_operation_results": all_results,
    }

    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = V4_RESULTS_DIR / f"v4_8_coder_benchmark_{model_slug}{think_suffix}_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Also save as _latest
    latest_path = V4_RESULTS_DIR / f"v4_8_coder_benchmark_{model_slug}{think_suffix}_latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"\nV4-8 COMPLETE: {gen_model} think={think}")
    logger.info(f"Results: {json_path}")

    # Print summary table
    print(f"\n{'='*60}")
    print(f"V4-8 Results: {gen_model} think={think if think else 'off'}")
    print(f"num_ctx=24576 (corrected from V2-8 default of 2048)")
    print(f"{'='*60}")
    print(f"{'Config':30s} | {'Pass%':>6s} | {'Med.Lat':>8s} | {'N':>4s}")
    print(f"{'-'*30}-+-{'-'*6}-+-{'-'*8}-+-{'-'*4}")
    for config in configs:
        s = summary.get(config, {})
        print(f"{config:30s} | {s.get('pass_rate',0):5.1f}% | {s.get('median_latency',0):7.1f}s | {s.get('n',0):4d}")
    print()

    return json_path


# ─────────────────────────────────────────────────────────────
# Run all Ollama models
# ─────────────────────────────────────────────────────────────

async def run_all_models(
    configs: List[str] = None,
    max_ops: Optional[int] = None,
):
    """Run all Ollama models sequentially."""
    for model, think in OLLAMA_MODELS:
        think_str = f"think={think}" if think else "think=off"
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting: {model} {think_str}")
        logger.info(f"{'#'*60}\n")

        await run_single_model(
            gen_model=model,
            think=think,
            configs=configs,
            max_ops=max_ops,
            resume=True,  # Always resume for --run-all to handle interruptions
        )


# ─────────────────────────────────────────────────────────────
# Comparison report: V2-8 vs V4-8
# ─────────────────────────────────────────────────────────────

def generate_comparison_report():
    """Generate a comparison report between V2-8 (num_ctx=2048) and V4-8 (num_ctx=24576)."""
    print(f"\n{'='*70}")
    print("V2-8 vs V4-8: Impact of Context Window Correction")
    print(f"{'='*70}\n")

    # Load V2-8 results (first timestamped files)
    v2_data = {}
    for f in sorted(V2_RESULTS_DIR.glob("v2_8_coder_benchmark_*_20260*.json")):
        if "_latest" in f.name or "_intermediate" in f.name:
            continue
        m = re.match(r"v2_8_coder_benchmark_(.+?)_(\d{8}_\d{6})\.json", f.name)
        if m:
            model_key = m.group(1)
            if model_key not in v2_data:  # first = oldest = original run
                data = json.load(open(f))
                per_op = data.get("per_operation_results", [])
                if per_op:
                    v2_data[model_key] = per_op

    # Load V4-8 results
    v4_data = {}
    for f in sorted(V4_RESULTS_DIR.glob("v4_8_coder_benchmark_*_latest.json")):
        m = re.match(r"v4_8_coder_benchmark_(.+?)_latest\.json", f.name)
        if m:
            model_key = m.group(1)
            data = json.load(open(f))
            per_op = data.get("per_operation_results", [])
            if per_op:
                v4_data[model_key] = per_op

    if not v4_data:
        print("No V4-8 results found yet. Run experiments first.")
        return

    print(f"{'Model':40s} | {'V2-8':>8s} | {'V4-8':>8s} | {'Delta':>8s} | {'Note':s}")
    print(f"{'-'*40}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*20}")

    for model_key in sorted(set(list(v2_data.keys()) + list(v4_data.keys()))):
        v2_ops = v2_data.get(model_key, [])
        v4_ops = v4_data.get(model_key, [])

        v2_pass = sum(1 for r in v2_ops if r.get("passed")) / max(len(v2_ops), 1) * 100
        v4_pass = sum(1 for r in v4_ops if r.get("passed")) / max(len(v4_ops), 1) * 100

        is_gemini = "gemini" in model_key
        note = "copied" if is_gemini else ""

        if v2_ops and v4_ops:
            delta = v4_pass - v2_pass
            delta_str = f"{delta:+.1f}pp"
            print(f"{model_key:40s} | {v2_pass:7.1f}% | {v4_pass:7.1f}% | {delta_str:>8s} | {note}")
        elif v2_ops:
            print(f"{model_key:40s} | {v2_pass:7.1f}% | {'--':>8s} | {'--':>8s} | pending")
        elif v4_ops:
            print(f"{model_key:40s} | {'--':>8s} | {v4_pass:7.1f}% | {'--':>8s} | new")

    print()

    # Save comparison as JSON
    comparison = {
        "experiment": "v4_8_vs_v2_8_comparison",
        "timestamp": datetime.now().isoformat(),
        "description": "Impact of correcting Ollama context window from 2048 to 24576 tokens",
        "models": {},
    }
    for model_key in sorted(set(list(v2_data.keys()) + list(v4_data.keys()))):
        v2_ops = v2_data.get(model_key, [])
        v4_ops = v4_data.get(model_key, [])
        v2_pass = sum(1 for r in v2_ops if r.get("passed")) / max(len(v2_ops), 1) * 100
        v4_pass = sum(1 for r in v4_ops if r.get("passed")) / max(len(v4_ops), 1) * 100
        comparison["models"][model_key] = {
            "v2_8_pass_rate": round(v2_pass, 1) if v2_ops else None,
            "v4_8_pass_rate": round(v4_pass, 1) if v4_ops else None,
            "delta_pp": round(v4_pass - v2_pass, 1) if v2_ops and v4_ops else None,
            "v2_8_num_ctx": 2048 if "gemini" not in model_key else "API",
            "v4_8_num_ctx": 24576 if "gemini" not in model_key else "API",
            "is_gemini": "gemini" in model_key,
            "v2_8_n": len(v2_ops),
            "v4_8_n": len(v4_ops),
        }

    comp_path = V4_RESULTS_DIR / "v4_8_comparison_v2_vs_v4.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"Comparison saved: {comp_path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4-8: Coder Benchmark with Corrected Context Window (num_ctx=24576)"
    )
    parser.add_argument(
        "--copy-gemini", action="store_true",
        help="Copy Gemini results from V2-8 (these are unaffected by the bug)",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Ollama model to run (e.g., ollama::qwen3-coder:latest)",
    )
    parser.add_argument(
        "--think", type=str, nargs="?", const="True", default=None,
        help="Enable thinking/reasoning. --think for True, --think low/medium/high for levels.",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help=f"Configs to test (default: all {len(CONFIG_NAMES)})",
    )
    parser.add_argument(
        "--max-ops", type=int, default=None,
        help="Max operations (for smoke tests)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate checkpoint",
    )
    parser.add_argument(
        "--run-all", action="store_true",
        help="Run all 10 Ollama model variants sequentially",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Generate V2-8 vs V4-8 comparison report",
    )

    args = parser.parse_args()

    # Parse think argument
    think_val = None
    if args.think is not None:
        if args.think.lower() in ("true", "1", "yes", "on"):
            think_val = True
        elif args.think.lower() in ("false", "0", "no", "off"):
            think_val = False
        else:
            think_val = args.think.lower()

    if args.copy_gemini:
        copy_gemini_results()
    elif args.compare:
        generate_comparison_report()
    elif args.run_all:
        asyncio.run(run_all_models(configs=args.configs, max_ops=args.max_ops))
    elif args.model:
        asyncio.run(run_single_model(
            gen_model=args.model,
            think=think_val,
            configs=args.configs,
            max_ops=args.max_ops,
            resume=args.resume,
        ))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  --copy-gemini                          # Copy V2-8 Gemini results first")
        print("  --model ollama::qwen3-coder:latest     # Run single model")
        print("  --model ollama::gpt-oss:20b --think high  # The think:high retest")
        print("  --run-all                              # All 10 Ollama variants")
        print("  --compare                              # V2-8 vs V4-8 comparison")


if __name__ == "__main__":
    main()
