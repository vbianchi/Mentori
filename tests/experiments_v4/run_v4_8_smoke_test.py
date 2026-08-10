#!/usr/bin/env python3
"""
V4-8 Smoke Test — 1 op × all configs × all model variants.

Runs airway_1_dimensions (simplest op) across every config and model+think combo
to verify no systematic failures before the full benchmark run.

Results saved to results_v4/v4_8_smoke_test.json (does NOT touch real intermediates).

Usage:
    uv run python tests/experiments_v4/run_v4_8_smoke_test.py
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure tool server URL
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from tests.experiments_v2.exp_v2_8_coder_benchmark import (
    CONFIG_NAMES,
    _dispatch,
    load_ground_truth_ops,
)
from tests.experiments.exp_common import find_admin_user_id, configure_gemini_from_admin
from backend.agents.model_router import ModelRouter

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("smoke_test")
logger.setLevel(logging.INFO)

V4_RESULTS_DIR = Path(__file__).parent / "results_v4"

# All model variants to test
SMOKE_MODELS = [
    ("ollama::qwen3-coder:latest", None),
    ("ollama::qwen3-coder-next:q4_K_M", None),
    ("ollama::gpt-oss:20b", None),
    ("ollama::gpt-oss:20b", "low"),
    ("ollama::gpt-oss:20b", "medium"),
    ("ollama::gpt-oss:20b", "high"),
    ("ollama::glm-4.7-flash:bf16", None),
    ("ollama::glm-4.7-flash:bf16", True),
    ("ollama::nemotron-3-nano:30b", None),
    ("ollama::nemotron-3-nano:30b", True),
    ("ollama::gemma3:27b", None),
    ("ollama::devstral-small-2:24b", None),
    ("ollama::deepseek-r1:70b", None),
]


async def run_smoke_test():
    configure_gemini_from_admin()
    user_id = find_admin_user_id()
    router = ModelRouter()

    # Load just 1 op (simplest)
    ops = load_ground_truth_ops(["airway"], ["simple"], max_ops=1)
    if not ops:
        logger.error("No operations found!")
        return
    op = ops[0]
    logger.info(f"Smoke test op: {op['op_id']} ({op['complexity']}, {op['dataset']})")

    base_workspace = PROJECT_ROOT / "data" / "workspace" / "v4_8_smoke_test"
    if base_workspace.exists():
        shutil.rmtree(base_workspace)
    base_workspace.mkdir(parents=True, exist_ok=True)

    datasets_dir = Path(__file__).parent.parent / "experiments_v2" / "datasets"

    results = []
    total = len(SMOKE_MODELS) * len(CONFIG_NAMES)
    done = 0
    t_start = time.time()

    for model, think in SMOKE_MODELS:
        think_label = f"think={think}" if think else "off"
        model_short = model.split("::", 1)[-1]
        logger.info(f"\n{'='*60}")
        logger.info(f"Model: {model_short} | {think_label}")
        logger.info(f"{'='*60}")

        for config in CONFIG_NAMES:
            done += 1
            elapsed = time.time() - t_start
            rate = done / max(elapsed, 1) * 3600
            eta_m = (total - done) / max(rate / 60, 0.01)

            logger.info(f"  [{done}/{total}] {config} | ETA: {eta_m:.0f}m")

            workspace = base_workspace / f"{model_short}_{config}_{uuid.uuid4().hex[:4]}"
            workspace.mkdir(parents=True, exist_ok=True)
            files_dir = workspace / "files"
            files_dir.mkdir(parents=True, exist_ok=True)
            for _key, filename in op["files"].items():
                src = datasets_dir / filename
                if src.exists():
                    shutil.copy2(src, files_dir / filename)

            try:
                result = await _dispatch(
                    config, op, router, user_id, workspace,
                    gen_model=model, think=think,
                )
                passed = result.get("passed", False)
                error = result.get("exec_error", "")
            except Exception as e:
                passed = False
                error = str(e)
                result = {}

            status = "PASS" if passed else "FAIL"
            err_short = f" | {error[:80]}" if error else ""
            logger.info(f"    -> {status}{err_short}")

            results.append({
                "model": model,
                "think": str(think) if think else "off",
                "config": config,
                "op_id": op["op_id"],
                "passed": passed,
                "error": error[:200] if error else "",
                "latency_s": result.get("latency_s", 0),
            })

    # Save results
    smoke_file = V4_RESULTS_DIR / "v4_8_smoke_test.json"
    with open(smoke_file, "w") as f:
        json.dump({"results": results, "total": total}, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*80}")
    print("V4-8 SMOKE TEST SUMMARY")
    print(f"{'='*80}")

    by_model = {}
    for r in results:
        key = f"{r['model'].split('::',1)[-1]} [{r['think']}]"
        if key not in by_model:
            by_model[key] = {"passed": 0, "failed": 0, "errors": []}
        if r["passed"]:
            by_model[key]["passed"] += 1
        else:
            by_model[key]["failed"] += 1
            by_model[key]["errors"].append(f"{r['config']}: {r['error'][:60]}")

    all_pass = True
    for model, stats in sorted(by_model.items()):
        p, f_count = stats["passed"], stats["failed"]
        mark = "PASS" if f_count == 0 else "FAIL"
        if f_count > 0:
            all_pass = False
        print(f"  {mark}  {model:<45} {p}/{p+f_count}")
        for err in stats["errors"][:3]:
            print(f"         -> {err}")

    by_config = {}
    for r in results:
        if r["config"] not in by_config:
            by_config[r["config"]] = {"passed": 0, "failed": 0}
        if r["passed"]:
            by_config[r["config"]]["passed"] += 1
        else:
            by_config[r["config"]]["failed"] += 1

    print(f"\nBy config:")
    for config in CONFIG_NAMES:
        stats = by_config.get(config, {"passed": 0, "failed": 0})
        p, f_count = stats["passed"], stats["failed"]
        mark = "PASS" if f_count == 0 else "FAIL"
        print(f"  {mark}  {config:<35} {p}/{p+f_count}")

    total_pass = sum(1 for r in results if r["passed"])
    print(f"\nTotal: {total_pass}/{total} passed")
    print(f"{'ALL CLEAR - ready for full run!' if all_pass else 'FAILURES DETECTED - fix before full run!'}")
    print(f"\nResults: {smoke_file}")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
