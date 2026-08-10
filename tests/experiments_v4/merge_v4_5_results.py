#!/usr/bin/env python3
"""
Merge V4-5 result files into a single unified v4_5_scaling_latest.json.

Combines:
  - s5/s10/s50 data from the most recent fixup file (7,488 results)
  - s20 data from the latest s20-specific file (2,484 results)

Deduplication: keeps the BEST result per (index_name, config, question_id),
preferring results with non-empty answers and valid judge scores.

Usage:
    uv run python tests/experiments_v4/merge_v4_5_results.py --dry-run
    uv run python tests/experiments_v4/merge_v4_5_results.py
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

V4_RESULTS_DIR = Path(__file__).parent / "results_v4"


def _result_quality(r: dict) -> tuple:
    """Score a result for dedup ordering. Higher = better."""
    gen = r.get("generation", {})
    answer = (gen.get("answer", "") if isinstance(gen, dict) else "").strip()
    has_answer = 1 if answer else 0

    js = r.get("judge_scores", {})
    corr = js.get("correctness")
    ref = js.get("refusal_accuracy")
    has_judge = 1 if (corr is not None or ref is not None) else 0

    # Penalize judge errors
    just = str(js.get("justification", "")).lower()
    judge_clean = 0 if ("connection" in just or "error" in just or "failed" in just) else 1

    return (has_answer, has_judge, judge_clean)


def merge(dry_run: bool = False):
    """Load ALL V4-5 result files, deduplicate per (index, config, qid), keep best."""

    all_files = sorted(V4_RESULTS_DIR.glob("v4_5_scaling_20260*.json"))
    all_files = [f for f in all_files if "corrupted" not in f.name and "pre_merge" not in f.name]

    latest = V4_RESULTS_DIR / "v4_5_scaling_latest.json"
    if latest.exists():
        all_files.append(latest)

    # Also check intermediate files
    for pattern in ["v4_5_intermediate*.json"]:
        all_files.extend(V4_RESULTS_DIR.glob(pattern))

    print(f"=== V4-5 Merge: scanning {len(all_files)} files ===")

    all_loaded = []
    source_names = []
    for f in all_files:
        try:
            data = json.load(open(f))
            results = data.get("per_question_results", data.get("results", []))
            if results:
                all_loaded.extend(results)
                source_names.append(f.name)
                print(f"  {f.name}: {len(results)} results")
        except Exception as e:
            print(f"  {f.name}: SKIP ({e})")

    # Deduplicate: best result per (index, config, qid)
    best = {}
    for r in all_loaded:
        key = (r.get("index_name", ""), r.get("config", ""), r.get("question_id", ""))
        quality = _result_quality(r)
        if key not in best or quality > _result_quality(best[key]):
            best[key] = r

    merged = list(best.values())

    # Sort by index, config, question_id for readability
    merged.sort(key=lambda r: (r.get("index_name", ""), r.get("config", ""), r.get("question_id", "")))

    # Stats
    from collections import Counter
    idx_counts = Counter(r["index_name"] for r in merged)
    empty = sum(1 for r in merged if not (r.get("generation", {}).get("answer", "") or "").strip())
    has_answer_no_judge = sum(
        1 for r in merged
        if (r.get("generation", {}).get("answer", "") or "").strip()
        and r.get("judge_scores", {}).get("correctness") is None
        and r.get("judge_scores", {}).get("refusal_accuracy") is None
    )

    print(f"\n=== Merged Results ===")
    print(f"  Total: {len(merged)}")
    print(f"  Empty answers: {empty}")
    print(f"  Has answer, no judge: {has_answer_no_judge}")
    print(f"  By index:")
    for k, v in sorted(idx_counts.items()):
        print(f"    {k}: {v}")

    if dry_run:
        print("\n[DRY RUN] No files written.")
        return

    # Backup current latest
    latest = V4_RESULTS_DIR / "v4_5_scaling_latest.json"
    if latest.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = V4_RESULTS_DIR / f"v4_5_scaling_pre_merge_{ts}.json"
        shutil.copy2(latest, backup)
        print(f"\n  Backed up latest -> {backup.name}")

    # Build merged output
    output = {
        "experiment": "v4_5_scaling",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "merged_from": sorted(set(source_names)),
        "indexes": sorted(idx_counts.keys()),
        "configs": sorted(set(r["config"] for r in merged)),
        "gen_model": merged[0].get("gen_model", "") if merged else "",
        "judge_model": "ollama::qwen3-coder:latest",
        "n_questions": len(merged),
        "per_question_results": merged,
    }

    # Save timestamped + latest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_path = V4_RESULTS_DIR / f"v4_5_scaling_{ts}.json"
    with open(ts_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    with open(latest, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n  Saved: {ts_path.name}")
    print(f"  Updated: v4_5_scaling_latest.json")
    print(f"\n=== Merge complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge V4-5 result files")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()
    merge(dry_run=args.dry_run)
