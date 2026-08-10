#!/usr/bin/env python3
"""
V2-8 Status Dashboard — Aggregates all completed and in-progress results.

Reads all v2_8_coder_benchmark_*.json (completed) and v2_8_intermediate_*.json
(in-progress) files, deduplicates by model+think+config+op, and prints a
summary table showing where we stand.

Usage:
    uv run python tests/experiments_v2/v2_8_status.py
    uv run python tests/experiments_v2/v2_8_status.py --detail        # per-operation breakdown
    uv run python tests/experiments_v2/v2_8_status.py --detail --model qwen3-coder
    uv run python tests/experiments_v2/v2_8_status.py --csv           # CSV output
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results_v2"

# ─────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────

def _parse_think_from_filename(filename: str) -> str:
    """Extract think mode from filename.

    Examples:
        v2_8_coder_benchmark_qwen3-coder_think-True_20260220.json -> True
        v2_8_intermediate_gpt-oss-20b_think-low.json -> low
        v2_8_coder_benchmark_20260219_125620.json -> ''
    """
    import re
    m = re.search(r"_think-(\w+)", filename)
    return m.group(1) if m else ""


def load_all_results():
    """Load all completed and intermediate V2-8 results, deduplicating."""
    results = []
    sources = {}  # track where each result came from

    # 1. Load completed results (authoritative — these override intermediates)
    for f in sorted(RESULTS_DIR.glob("v2_8_coder_benchmark_*.json")):
        if "_latest" in f.name:
            continue  # skip symlink/copies
        try:
            data = json.loads(f.read_text())
            # Resolve think: top-level field > filename > empty
            think = data.get("think", "") or ""
            if think in ("off", "None", "NOT_SET"):
                think = ""
            if not think:
                think = _parse_think_from_filename(f.name)
            for r in data.get("per_operation_results", []):
                r["think"] = think  # inject into each result
                key = (r["gen_model"], think, r["config"], r["op_id"])
                sources[key] = ("done", f.name)
                results.append(r)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {f.name}: {e}", file=sys.stderr)

    # 2. Load intermediate results (only if not already covered by completed)
    for f in sorted(RESULTS_DIR.glob("v2_8_intermediate*.json")):
        try:
            data = json.loads(f.read_text())
            think = _parse_think_from_filename(f.name)
            for r in data.get("results", []):
                r["think"] = think  # inject into each result
                key = (r["gen_model"], think, r["config"], r["op_id"])
                if key not in sources:
                    sources[key] = ("running", f.name)
                    results.append(r)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {f.name}: {e}", file=sys.stderr)

    return results, sources


def model_label(r):
    """Create a short label like 'qwen3-coder' or 'gpt-oss-20b [think:low]'."""
    model = r.get("gen_model", "unknown")
    # Strip provider prefix
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

ALL_CONFIGS = [
    "free_form", "free_form_n3_best", "free_form_n3_combined",
    "coder_v2_n1", "coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined",
    "coder_v2_n3",
    # New introspection-based algorithms
    "introspect_then_code", "error_recovery_introspect", "thinker_coder_split",
    # Combined best approach
    "introspect_with_recovery",
]

ALL_OPS = 20  # total operations in the benchmark (v4.0: 10 airway + 10 lung)
TOTAL_PER_MODEL = ALL_OPS * len(ALL_CONFIGS)  # 140


def aggregate(results):
    """Group results by model_label and compute stats."""
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

        # Cell/LLM/retry stats
        cells = [r.get("n_cells", 0) for r in recs if r.get("n_cells", 0) > 0]
        avg_cells = sum(cells) / len(cells) if cells else 0
        llm_calls = [r.get("n_llm_calls", 0) for r in recs if r.get("n_llm_calls", 0) > 0]
        avg_llm = sum(llm_calls) / len(llm_calls) if llm_calls else 0
        total_retries = sum(r.get("n_retries", 0) for r in recs)
        total_idle_recovered = sum(r.get("n_idle_recovered", 0) for r in recs)

        # By config
        by_config = {}
        for cfg in ALL_CONFIGS:
            cfg_recs = [r for r in recs if r["config"] == cfg]
            if cfg_recs:
                cfg_pass = sum(1 for r in cfg_recs if r.get("passed"))
                by_config[cfg] = f"{cfg_pass}/{len(cfg_recs)}"
            else:
                by_config[cfg] = "-"

        # By complexity
        by_complexity = {}
        for cx in ["simple", "medium", "complex"]:
            cx_recs = [r for r in recs if r["complexity"] == cx]
            if cx_recs:
                cx_pass = sum(1 for r in cx_recs if r.get("passed"))
                by_complexity[cx] = f"{cx_pass}/{len(cx_recs)}"
            else:
                by_complexity[cx] = "-"

        # By dataset
        by_dataset = {}
        for ds in ["airway", "lung_cancer"]:
            ds_recs = [r for r in recs if r["dataset"] == ds]
            if ds_recs:
                ds_pass = sum(1 for r in ds_recs if r.get("passed"))
                by_dataset[ds] = f"{ds_pass}/{len(ds_recs)}"
            else:
                by_dataset[ds] = "-"

        # Per-config cell/llm stats
        by_config_cells = {}
        for cfg in ALL_CONFIGS:
            cfg_recs = [r for r in recs if r["config"] == cfg]
            if cfg_recs:
                c = [r.get("n_cells", 0) for r in cfg_recs if r.get("n_cells", 0) > 0]
                l = [r.get("n_llm_calls", 0) for r in cfg_recs if r.get("n_llm_calls", 0) > 0]
                rt = sum(r.get("n_retries", 0) for r in cfg_recs)
                by_config_cells[cfg] = {
                    "avg_cells": sum(c) / len(c) if c else 0,
                    "avg_llm": sum(l) / len(l) if l else 0,
                    "retries": rt,
                }

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
            "by_config_cells": by_config_cells,
            "by_complexity": by_complexity,
            "by_dataset": by_dataset,
        })

    # Sort: completed first (desc by n), then by pass rate
    rows.sort(key=lambda r: (-r["n"], -r["passed"]))
    return rows


def aggregate_detail(results, model_filter=None):
    """Per-operation breakdown grouped by model."""
    by_model = defaultdict(list)
    for r in results:
        label = model_label(r)
        if model_filter and model_filter.lower() not in label.lower():
            continue
        by_model[label].append(r)

    detail = {}
    for label in sorted(by_model.keys()):
        recs = by_model[label]
        # Group by op_id
        by_op = defaultdict(dict)
        for r in recs:
            by_op[r["op_id"]][r["config"]] = r
        detail[label] = by_op

    return detail


# ─────────────────────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────────────────────

def print_summary(rows, results=None):
    print("=" * 100)
    print("V2-8 CODER BENCHMARK — STATUS DASHBOARD")
    print("=" * 100)

    # Compute expected totals from the loaded results
    op_complexity: dict = {}
    op_dataset: dict = {}
    if results:
        for r in results:
            op_complexity[r["op_id"]] = r.get("complexity", "?")
            op_dataset[r["op_id"]] = r.get("dataset", "?")
    from collections import Counter as _Counter
    cx_counts = _Counter(op_complexity.values())
    ds_counts = _Counter(op_dataset.values())
    n_configs = len(ALL_CONFIGS)
    complexity_max = {cx: cnt * n_configs for cx, cnt in cx_counts.items()}
    dataset_max = {ds: cnt * n_configs for ds, cnt in ds_counts.items()}

    print(f"  Benchmark scale: {ALL_OPS} ops × {n_configs} configs = {TOTAL_PER_MODEL} evaluations per model")
    if complexity_max:
        cx_str = "  |  ".join(
            f"{cx}: {complexity_max.get(cx, '?')}"
            for cx in ["simple", "medium", "complex"] if cx in complexity_max
        )
        print(f"  By complexity (max per model): {cx_str}")
    if dataset_max:
        ds_str = "  |  ".join(
            f"{ds}: {dataset_max.get(ds, '?')}"
            for ds in ["airway", "lung_cancer"] if ds in dataset_max
        )
        print(f"  By dataset    (max per model): {ds_str}")
    print()

    # Main table
    hdr = f"{'Model':<35} {'Progress':<16} {'Pass Rate':>10} {'Pass':>5} {'Fail':>5} {'Med.Lat':>8} {'Cells':>6} {'LLM':>5} {'Retry':>6} {'IdleRec':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        status = "✓" if r["n"] == TOTAL_PER_MODEL else "…"
        cells_str = r.get("avg_cells", "0.0")
        llm_str = r.get("avg_llm_calls", "0.0")
        retries_str = str(r.get("total_retries", 0))
        idle_rec_str = str(r.get("total_idle_recovered", 0))
        print(
            f"{status} {r['model']:<33} {r['progress']:<16} {r['pass_rate']:>10}"
            f" {r['passed']:>5} {r['failed']:>5} {r['med_latency']:>8}"
            f" {cells_str:>6} {llm_str:>5} {retries_str:>6} {idle_rec_str:>8}"
        )

    print()

    # By-config breakdown
    print(f"PASS RATE BY CONFIG  (pass/done  |  max {ALL_OPS} ops per config × {n_configs} configs = {TOTAL_PER_MODEL} per model)")
    print("-" * 120)
    cfg_short = {
        "free_form": "ff",
        "free_form_n3_best": "ff_n3b",
        "free_form_n3_combined": "ff_n3c",
        "coder_v2_n1": "cv2_n1",
        "coder_v2_n1_cell3_best": "cv2_c3b",
        "coder_v2_n1_cell3_combined": "cv2_c3c",
        "coder_v2_n3": "cv2_n3",
        # New introspection-based algorithms
        "introspect_then_code": "intro",
        "error_recovery_introspect": "err_rec",
        "thinker_coder_split": "think",
        "introspect_with_recovery": "i+rec",
    }
    hdr2 = f"{'Model':<35}" + "".join(f" {cfg_short.get(c, c):>8}" for c in ALL_CONFIGS)
    print(hdr2)
    print("-" * len(hdr2))
    for r in rows:
        line = f"{r['model']:<35}"
        for c in ALL_CONFIGS:
            line += f" {r['by_config'].get(c, '-'):>8}"
        print(line)
    # Footer: expected totals row
    max_line = f"  {'(max per col)':>33}"
    for _ in ALL_CONFIGS:
        max_line += f" {'/' + str(ALL_OPS):>8}"
    print(max_line)

    print()

    # By-complexity breakdown
    cx_max_labels = {
        cx: f"{cx}\n(of {complexity_max[cx]})" if cx in complexity_max else cx
        for cx in ["simple", "medium", "complex"]
    }
    cx_headers = [
        f"{'simple':>10}{'(of ' + str(complexity_max.get('simple', '?')) + ')':>10}"
        if "simple" in complexity_max else f"{'simple':>20}",
    ]
    def _cx_hdr(cx):
        max_n = complexity_max.get(cx)
        return f"{cx}{'(of ' + str(max_n) + ')' if max_n else '':>6}"

    cx_col_w = 18
    print(f"PASS RATE BY COMPLEXITY")
    if complexity_max:
        print(f"  Expected totals per model: " + "  |  ".join(
            f"{cx}={complexity_max[cx]}" for cx in ["simple", "medium", "complex"] if cx in complexity_max
        ))
    print("-" * 80)
    hdr3 = (
        f"{'Model':<35}"
        f" {'simple':>{cx_col_w}}"
        f" {'medium':>{cx_col_w}}"
        f" {'complex':>{cx_col_w}}"
    )
    print(hdr3)
    print("-" * len(hdr3))
    for r in rows:
        def _cx_cell(cx):
            val = r['by_complexity'].get(cx, '-')
            if val == '-' or cx not in complexity_max:
                return val
            # val is "pass/done"; annotate with max
            return f"{val}/{complexity_max[cx]}"
        print(
            f"{r['model']:<35}"
            f" {_cx_cell('simple'):>{cx_col_w}}"
            f" {_cx_cell('medium'):>{cx_col_w}}"
            f" {_cx_cell('complex'):>{cx_col_w}}"
        )

    print()

    # By-dataset breakdown
    ds_col_w = 16
    print("PASS RATE BY DATASET")
    if dataset_max:
        print(f"  Expected totals per model: " + "  |  ".join(
            f"{ds}={dataset_max[ds]}" for ds in ["airway", "lung_cancer"] if ds in dataset_max
        ))
    print("-" * 75)
    hdr4 = (
        f"{'Model':<35}"
        f" {'airway':>{ds_col_w}}"
        f" {'lung_cancer':>{ds_col_w}}"
    )
    print(hdr4)
    print("-" * len(hdr4))
    for r in rows:
        def _ds_cell(ds):
            val = r['by_dataset'].get(ds, '-')
            if val == '-' or ds not in dataset_max:
                return val
            return f"{val}/{dataset_max[ds]}"
        print(
            f"{r['model']:<35}"
            f" {_ds_cell('airway'):>{ds_col_w}}"
            f" {_ds_cell('lung_cancer'):>{ds_col_w}}"
        )


def print_detail(detail):
    for label, by_op in detail.items():
        print()
        print(f"{'=' * 80}")
        print(f"  {label}")
        print(f"{'=' * 80}")
        for op_id in sorted(by_op.keys()):
            configs = by_op[op_id]
            first = next(iter(configs.values()))
            cx = first.get("complexity", "?")
            ds = first.get("dataset", "?")
            results_str = []
            for cfg in ALL_CONFIGS:
                if cfg in configs:
                    r = configs[cfg]
                    mark = "✓" if r.get("passed") else "✗"
                    results_str.append(f"{mark}")
                else:
                    results_str.append("·")
            line = " ".join(results_str)
            passed = sum(1 for c in configs.values() if c.get("passed"))
            total = len(configs)
            print(f"  {op_id:<35} [{cx:<7}] [{ds:<12}] {line}  ({passed}/{total})")
        # Legend
        print(f"  {'':35} Config order: ff  n3b n3c n1  c3b c3c n3")


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


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V2-8 Coder Benchmark Status Dashboard")
    parser.add_argument("--detail", action="store_true", help="Show per-operation breakdown")
    parser.add_argument("--model", type=str, default=None, help="Filter by model name (substring match)")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    args = parser.parse_args()

    results, sources = load_all_results()

    if not results:
        print("No V2-8 results found.")
        return

    # Count sources
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
