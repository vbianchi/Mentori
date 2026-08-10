"""
Merge parallel judge fixup results back into v4_5_scaling_latest.json.

Each parallel fixup instance saves a timestamped file containing ALL results,
but only the indexes it was assigned to have updated judge scores. This script
loads the pre-parallel baseline, then picks up updated scores from each
parallel output file and merges them together.

Usage:
    python merge_judge_results.py --baseline path/to/baseline.json
    python merge_judge_results.py --baseline path/to/baseline.json --files f1.json f2.json f3.json
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

V4_RESULTS_DIR = Path(__file__).parent / "results_v4"
LATEST = V4_RESULTS_DIR / "v4_5_scaling_latest.json"


def find_recent_fixup_files(n=3):
    """Find the N most recent fixup output files."""
    pattern = "v4_5_scaling_2*.json"
    files = sorted(V4_RESULTS_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    files = [f for f in files if "_in_progress" not in f.name
             and "baseline" not in f.name
             and "merged" not in f.name
             and f.name != "v4_5_scaling_latest.json"]

    print(f"Found {len(files)} fixup output files (most recent first):")
    for f in files[:10]:
        print(f"  {f.name} ({datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M:%S')})")

    return files[:n]


def merge(baseline_path: Path, fixup_files: list):
    # Load the clean baseline (saved BEFORE parallel runs started)
    with open(baseline_path) as f:
        base = json.load(f)

    base_results = base["per_question_results"]
    print(f"\nBaseline: {baseline_path.name} ({len(base_results)} results)")

    # Index results by (index_name, config, question_id) for fast lookup
    base_index = {}
    for i, r in enumerate(base_results):
        key = (r.get("index_name", ""), r.get("config", ""), r.get("question_id", ""))
        base_index[key] = i

    updated = 0
    seen_indexes = set()

    for fpath in fixup_files:
        fpath = Path(fpath)
        with open(fpath) as f:
            data = json.load(f)

        results = data["per_question_results"]
        file_updated = 0

        for r in results:
            idx_name = r.get("index_name", "")
            key = (idx_name, r.get("config", ""), r.get("question_id", ""))

            if key not in base_index:
                continue

            base_r = base_results[base_index[key]]

            # Check if this result has a better judge score than base
            new_js = r.get("judge_scores", {})
            old_js = base_r.get("judge_scores", {})

            if not isinstance(new_js, dict):
                continue

            new_corr = new_js.get("correctness")
            old_corr = old_js.get("correctness") if isinstance(old_js, dict) else None

            # Update if: new has a valid score AND old was error/missing
            old_is_error = (
                old_corr is None or
                old_corr == "n/a" or
                (isinstance(old_js, dict) and "connection" in str(old_js.get("justification", "")).lower())
            )
            new_is_valid = new_corr is not None and new_corr != "n/a"

            if new_is_valid and old_is_error:
                base_results[base_index[key]]["judge_scores"] = new_js
                seen_indexes.add(idx_name)
                file_updated += 1
                updated += 1

        print(f"  {fpath.name}: {file_updated} scores updated")

    print(f"\nTotal updated: {updated} scores across indexes: {sorted(seen_indexes)}")

    if updated == 0:
        print("No updates to apply. Exiting.")
        return

    # Recompute config metrics
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root
    from tests.experiments_v4.exp_v4_common import aggregate_v4_metrics, detect_judge_key

    config_results_map = defaultdict(list)
    for r in base_results:
        config_results_map[r["config"]].append(r)

    judge_key = detect_judge_key(base_results)
    config_metrics = {}
    for config_name, config_results in config_results_map.items():
        config_metrics[config_name] = aggregate_v4_metrics(config_results, judge_key=judge_key)

    base["per_question_results"] = base_results
    base["config_metrics"] = config_metrics
    base["timestamp_merge"] = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save timestamped copy + update latest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = V4_RESULTS_DIR / f"v4_5_scaling_merged_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(base, f, indent=2, default=str)

    shutil.copy2(out_path, LATEST)
    print(f"\nSaved: {out_path.name}")
    print(f"Updated: v4_5_scaling_latest.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="Path to the clean baseline JSON (saved before parallel runs)")
    parser.add_argument("--files", nargs="*", help="Specific fixup output files to merge (default: 3 most recent)")
    args = parser.parse_args()

    baseline = Path(args.baseline)
    if not baseline.exists():
        print(f"ERROR: Baseline not found: {baseline}")
        sys.exit(1)

    if args.files:
        fixup_files = [Path(f) for f in args.files]
    else:
        fixup_files = find_recent_fixup_files(n=3)

    if not fixup_files:
        print("ERROR: No fixup files found to merge")
        sys.exit(1)

    merge(baseline, fixup_files)
