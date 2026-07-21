#!/usr/bin/env python3
"""
V4-8 Status Dashboard — Aggregates all completed and in-progress results.

Reads all v4_8_coder_benchmark_*.json (completed) and v4_8_intermediate_*.json
(in-progress) files, deduplicates by model+think+config+op, and prints a
summary table showing where we stand.

Usage:
    uv run python tests/experiments_v4/v4_8_status.py
    uv run python tests/experiments_v4/v4_8_status.py --detail
    uv run python tests/experiments_v4/v4_8_status.py --detail --model qwen3-coder
    uv run python tests/experiments_v4/v4_8_status.py --csv
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results_v4"

ALL_CONFIGS = [
    "free_form", "free_form_n3_best", "free_form_n3_combined",
    "coder_v2_n1", "coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined",
    "coder_v2_n3",
    "introspect_then_code", "error_recovery_introspect", "thinker_coder_split",
    "introspect_with_recovery",
]

ALL_OPS = 20
TOTAL_PER_MODEL = ALL_OPS * len(ALL_CONFIGS)  # 220


# ─────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────

def _parse_think_from_filename(filename: str) -> str:
    m = re.search(r"_think-(\w+)", filename)
    return m.group(1) if m else ""


def load_all_results():
    """Load all completed and intermediate V4-8 results, deduplicating."""
    results = []
    sources = {}

    # 1. Completed results (authoritative) — only _latest.json to avoid double-counting reruns
    for f in sorted(RESULTS_DIR.glob("v4_8_coder_benchmark_*_latest.json")):
        try:
            data = json.loads(f.read_text())
            think = data.get("think", "") or ""
            if think in ("off", "None", "NOT_SET"):
                think = ""
            if not think:
                think = _parse_think_from_filename(f.name)
            for r in data.get("per_operation_results", data.get("results", [])):
                r["think"] = think
                key = (r["gen_model"], think, r["config"], r["op_id"])
                sources[key] = ("done", f.name)
                results.append(r)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {f.name}: {e}", file=sys.stderr)

    # 2. Intermediate results (only if not already covered)
    for f in sorted(RESULTS_DIR.glob("v4_8_intermediate_*.json")):
        try:
            data = json.loads(f.read_text())
            think = _parse_think_from_filename(f.name)
            for r in data.get("results", []):
                r["think"] = think
                key = (r["gen_model"], think, r["config"], r["op_id"])
                if key not in sources:
                    sources[key] = ("running", f.name)
                    results.append(r)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {f.name}: {e}", file=sys.stderr)

    return results, sources


def model_label(r):
    model = r.get("gen_model", "unknown")
    name = model.split("::", 1)[-1] if "::" in model else model
    if name.endswith(":latest"):
        name = name[:-7]
    name = name.replace(":", "-")
    think = r.get("think", "")
    if think:
        name += f" [think:{think}]"
    return name


# ─────────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────────

def aggregate(results):
    by_model = defaultdict(list)
    for r in results:
        by_model[model_label(r)].append(r)

    rows = []
    for label in sorted(by_model.keys()):
        recs = by_model[label]
        n = len(recs)
        passed = sum(1 for r in recs if r.get("passed"))
        failed = n - passed
        pass_rate = passed / n * 100 if n else 0
        latencies = [r["latency_s"] for r in recs if r.get("latency_s", 0) > 0]
        med_lat = sorted(latencies)[len(latencies) // 2] if latencies else 0
        progress = n / TOTAL_PER_MODEL * 100

        cells = [r.get("n_cells", 0) for r in recs if r.get("n_cells", 0) > 0]
        avg_cells = sum(cells) / len(cells) if cells else 0
        llm_calls = [r.get("n_llm_calls", 0) for r in recs if r.get("n_llm_calls", 0) > 0]
        avg_llm = sum(llm_calls) / len(llm_calls) if llm_calls else 0
        total_retries = sum(r.get("n_retries", 0) for r in recs)
        total_idle_recovered = sum(r.get("n_idle_recovered", 0) for r in recs)

        by_config = {}
        for cfg in ALL_CONFIGS:
            cfg_recs = [r for r in recs if r["config"] == cfg]
            if cfg_recs:
                cfg_pass = sum(1 for r in cfg_recs if r.get("passed"))
                by_config[cfg] = f"{cfg_pass}/{len(cfg_recs)}"
            else:
                by_config[cfg] = "-"

        by_complexity = {}
        for cx in ["simple", "medium", "complex"]:
            cx_recs = [r for r in recs if r.get("complexity") == cx]
            if cx_recs:
                cx_pass = sum(1 for r in cx_recs if r.get("passed"))
                by_complexity[cx] = f"{cx_pass}/{len(cx_recs)}"
            else:
                by_complexity[cx] = "-"

        by_dataset = {}
        for ds in ["airway", "lung_cancer"]:
            ds_recs = [r for r in recs if r.get("dataset") == ds]
            if ds_recs:
                ds_pass = sum(1 for r in ds_recs if r.get("passed"))
                by_dataset[ds] = f"{ds_pass}/{len(ds_recs)}"
            else:
                by_dataset[ds] = "-"

        rows.append({
            "model": label,
            "progress": f"{n}/{TOTAL_PER_MODEL} ({progress:.0f}%)",
            "pass_rate": f"{pass_rate:.0f}%",
            "passed": passed,
            "failed": failed,
            "n": n,
            "med_latency": f"{med_lat:.0f}s",
            "avg_cells": f"{avg_cells:.1f}",
            "avg_llm_calls": f"{avg_llm:.1f}",
            "total_retries": total_retries,
            "total_idle_recovered": total_idle_recovered,
            "by_config": by_config,
            "by_complexity": by_complexity,
            "by_dataset": by_dataset,
        })

    rows.sort(key=lambda r: (-r["n"], -r["passed"]))
    return rows


def aggregate_detail(results, model_filter=None):
    by_model = defaultdict(list)
    for r in results:
        label = model_label(r)
        if model_filter and model_filter.lower() not in label.lower():
            continue
        by_model[label].append(r)

    detail = {}
    for label in sorted(by_model.keys()):
        recs = by_model[label]
        by_op = defaultdict(dict)
        for r in recs:
            by_op[r["op_id"]][r["config"]] = r
        detail[label] = by_op
    return detail


# ─────────────────────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────────────────────

def print_summary(rows, results=None):
    print("=" * 110)
    print("V4-8 CODER BENCHMARK — STATUS DASHBOARD  (num_ctx=24576, rerun of V2-8)")
    print("=" * 110)

    op_complexity = {}
    op_dataset = {}
    if results:
        for r in results:
            op_complexity[r["op_id"]] = r.get("complexity", "?")
            op_dataset[r["op_id"]] = r.get("dataset", "?")
    cx_counts = Counter(op_complexity.values())
    ds_counts = Counter(op_dataset.values())
    n_configs = len(ALL_CONFIGS)
    complexity_max = {cx: cnt * n_configs for cx, cnt in cx_counts.items()}
    dataset_max = {ds: cnt * n_configs for ds, cnt in ds_counts.items()}

    print(f"  Benchmark: {ALL_OPS} ops x {n_configs} configs = {TOTAL_PER_MODEL} evals/model")
    if complexity_max:
        cx_str = "  |  ".join(
            f"{cx}: {complexity_max.get(cx, '?')}"
            for cx in ["simple", "medium", "complex"] if cx in complexity_max
        )
        print(f"  By complexity (max/model): {cx_str}")
    if dataset_max:
        ds_str = "  |  ".join(
            f"{ds}: {dataset_max.get(ds, '?')}"
            for ds in ["airway", "lung_cancer"] if ds in dataset_max
        )
        print(f"  By dataset    (max/model): {ds_str}")
    print()

    # Main table
    hdr = f"{'Model':<35} {'Progress':<16} {'Pass%':>6} {'Pass':>5} {'Fail':>5} {'Med.Lat':>8} {'Cells':>6} {'LLM':>5} {'Retry':>6} {'IdleRec':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        status = "+" if r["n"] == TOTAL_PER_MODEL else "~"
        print(
            f"{status} {r['model']:<33} {r['progress']:<16} {r['pass_rate']:>6}"
            f" {r['passed']:>5} {r['failed']:>5} {r['med_latency']:>8}"
            f" {r['avg_cells']:>6} {r['avg_llm_calls']:>5} {r['total_retries']:>6}"
            f" {r['total_idle_recovered']:>8}"
        )
    print()

    # By-config breakdown
    cfg_short = {
        "free_form": "ff",
        "free_form_n3_best": "ff_n3b",
        "free_form_n3_combined": "ff_n3c",
        "coder_v2_n1": "cv2_n1",
        "coder_v2_n1_cell3_best": "cv2_c3b",
        "coder_v2_n1_cell3_combined": "cv2_c3c",
        "coder_v2_n3": "cv2_n3",
        "introspect_then_code": "intro",
        "error_recovery_introspect": "err_rec",
        "thinker_coder_split": "think",
        "introspect_with_recovery": "i+rec",
    }
    print(f"PASS RATE BY CONFIG  (pass/done  |  max {ALL_OPS} ops per config)")
    print("-" * 130)
    hdr2 = f"{'Model':<35}" + "".join(f" {cfg_short.get(c, c):>8}" for c in ALL_CONFIGS)
    print(hdr2)
    print("-" * len(hdr2))
    for r in rows:
        line = f"{r['model']:<35}"
        for c in ALL_CONFIGS:
            line += f" {r['by_config'].get(c, '-'):>8}"
        print(line)
    print()

    # By-complexity breakdown
    print("PASS RATE BY COMPLEXITY")
    print("-" * 80)
    hdr3 = f"{'Model':<35} {'simple':>18} {'medium':>18} {'complex':>18}"
    print(hdr3)
    print("-" * len(hdr3))
    for r in rows:
        print(
            f"{r['model']:<35}"
            f" {r['by_complexity'].get('simple', '-'):>18}"
            f" {r['by_complexity'].get('medium', '-'):>18}"
            f" {r['by_complexity'].get('complex', '-'):>18}"
        )
    print()

    # By-dataset breakdown
    print("PASS RATE BY DATASET")
    print("-" * 75)
    hdr4 = f"{'Model':<35} {'airway':>16} {'lung_cancer':>16}"
    print(hdr4)
    print("-" * len(hdr4))
    for r in rows:
        print(
            f"{r['model']:<35}"
            f" {r['by_dataset'].get('airway', '-'):>16}"
            f" {r['by_dataset'].get('lung_cancer', '-'):>16}"
        )


def print_detail(detail):
    for label, by_op in detail.items():
        print()
        print(f"{'=' * 80}")
        print(f"  {label}")
        print(f"{'=' * 80}")
        cfg_short = ["ff", "n3b", "n3c", "n1", "c3b", "c3c", "n3", "intr", "err", "thnk", "i+r"]
        print(f"  {'op_id':<35} {'[cx]':<9} {'[ds]':<14} {' '.join(f'{c:>4}' for c in cfg_short)}")
        print(f"  {'-'*35} {'-'*9} {'-'*14} {'-' * (5 * len(cfg_short))}")
        for op_id in sorted(by_op.keys()):
            configs = by_op[op_id]
            first = next(iter(configs.values()))
            cx = first.get("complexity", "?")
            ds = first.get("dataset", "?")
            marks = []
            for cfg in ALL_CONFIGS:
                if cfg in configs:
                    marks.append("  P " if configs[cfg].get("passed") else "  F ")
                else:
                    marks.append("  . ")
            passed = sum(1 for c in configs.values() if c.get("passed"))
            total = len(configs)
            print(f"  {op_id:<35} [{cx:<7}] [{ds:<12}] {''.join(marks)}  ({passed}/{total})")


def print_csv(rows):
    import csv, io
    out = io.StringIO()
    w = csv.writer(out)
    headers = ["model", "progress", "pass_rate", "passed", "failed", "med_latency"]
    headers += [f"cfg_{c}" for c in ALL_CONFIGS]
    headers += ["simple", "medium", "complex", "airway", "lung_cancer"]
    w.writerow(headers)
    for r in rows:
        row = [r["model"], r["progress"], r["pass_rate"], r["passed"], r["failed"], r["med_latency"]]
        row += [r["by_config"].get(c, "-") for c in ALL_CONFIGS]
        row += [r["by_complexity"].get(c, "-") for c in ["simple", "medium", "complex"]]
        row += [r["by_dataset"].get(d, "-") for d in ["airway", "lung_cancer"]]
        w.writerow(row)
    print(out.getvalue())


def main():
    parser = argparse.ArgumentParser(description="V4-8 Coder Benchmark Status Dashboard")
    parser.add_argument("--detail", action="store_true", help="Per-operation breakdown")
    parser.add_argument("--model", type=str, default=None, help="Filter by model name")
    parser.add_argument("--csv", action="store_true", help="CSV output")
    args = parser.parse_args()

    results, sources = load_all_results()
    if not results:
        print("No V4-8 results found.")
        return

    done_count = sum(1 for s, _ in sources.values() if s == "done")
    running_count = sum(1 for s, _ in sources.values() if s == "running")
    print(f"Loaded {len(results)} evaluations ({done_count} completed, {running_count} in-progress)")
    print()

    rows = aggregate(results)

    if args.csv:
        print_csv(rows)
    else:
        print_summary(rows, results=results)

    if args.detail:
        detail = aggregate_detail(results, model_filter=args.model)
        print_detail(detail)


if __name__ == "__main__":
    main()
