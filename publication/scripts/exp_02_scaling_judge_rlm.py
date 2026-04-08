#!/usr/bin/env python3
"""
V4-5 Step 2: Judge RLM answers using Ollama ONLY (no Gemini).

Reads the generated RLM answers from exp_02_scaling_generate_rlm.py output,
runs qwen3-coder judge on each, and produces the final merged V4-5 dataset
combining valid non-RLM results from the archive with fresh RLM results.

Usage:
    # Judge all unjudged RLM results
    uv run python publication/scripts/exp_02_scaling_judge_rlm.py

    # Resume interrupted judging
    uv run python publication/scripts/exp_02_scaling_judge_rlm.py --resume

    # Dry run
    uv run python publication/scripts/exp_02_scaling_judge_rlm.py --dry-run

    # Merge with archive after judging (creates final dataset)
    uv run python publication/scripts/exp_02_scaling_judge_rlm.py --merge
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from exp_common import (
    JUDGE_MODEL,
    GEN_MODEL,
    judge_answer,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("v4_5_judge_rlm")
logger.setLevel(logging.INFO)

# ── Paths ──
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
ARCHIVE_DIR = RESULTS_DIR / "v4_5_archive_contaminated"
GT_PATH = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"

# Input: generated RLM answers (from step 1)
RLM_GENERATED_FILE = RESULTS_DIR / "v4_5_rlm_generated.json"

# Output: judged RLM answers
RLM_JUDGED_FILE = RESULTS_DIR / "v4_5_rlm_judged.json"

# Archive: valid non-RLM results
ARCHIVE_FILE = ARCHIVE_DIR / "v4_5_scaling_in_progress_20260322_120045.json"

# Final merged output
MERGED_FILE = RESULTS_DIR / "v4_5_scaling_latest.json"

# ── Constants ──
NON_RLM_CONFIGS = {"single_pass", "multi_hop", "verified_pass"}
RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20"}


def load_ground_truth() -> Dict[str, Dict]:
    """Load ground truth indexed by question ID."""
    with open(GT_PATH) as f:
        questions = json.load(f)["questions"]
    return {q["id"]: q for q in questions}


async def run_judging(resume: bool = False, dry_run: bool = False):
    """Judge all generated RLM answers."""

    # Load generated results from all group files + main file
    import glob as globmod
    gen_files = sorted(globmod.glob(str(RESULTS_DIR / "v4_5_rlm_generated*.json")))
    if not gen_files:
        logger.error(f"No generated files found matching v4_5_rlm_generated*.json")
        logger.error("Run exp_02_scaling_generate_rlm.py first")
        return

    all_results = []
    seen_keys = set()
    for gf in gen_files:
        with open(gf) as f:
            gen_data = json.load(f)
        for r in gen_data.get("results", []):
            key = (r["index_name"], r["config"], r["question_id"])
            if key not in seen_keys:
                all_results.append(r)
                seen_keys.add(key)
    logger.info(f"Loaded {len(all_results)} generated results from {len(gen_files)} files")

    # Load ground truth for expected answers/concepts
    gt = load_ground_truth()

    # Filter to results that have answers but no judge scores
    to_judge = []
    already_judged = []
    for r in all_results:
        answer = r.get("generation", {}).get("answer", "").strip()
        has_judge = bool(r.get("judge_scores", {}))
        if answer and not has_judge:
            to_judge.append(r)
        elif answer and has_judge:
            already_judged.append(r)

    # Resume: load existing judged results
    if resume and RLM_JUDGED_FILE.exists():
        with open(RLM_JUDGED_FILE) as f:
            judged_data = json.load(f)
        existing_judged = {
            (r["index_name"], r["config"], r["question_id"]): r
            for r in judged_data.get("results", [])
            if r.get("judge_scores", {})
        }
        # Remove already-judged from work list
        to_judge = [
            r for r in to_judge
            if (r["index_name"], r["config"], r["question_id"]) not in existing_judged
        ]
        already_judged.extend(existing_judged.values())
        logger.info(f"Resuming: {len(existing_judged)} already judged, {len(to_judge)} remaining")

    logger.info(f"To judge: {len(to_judge)} | Already judged: {len(already_judged)} | No answer: {len(all_results) - len(to_judge) - len(already_judged)}")

    if dry_run:
        from collections import Counter
        by_idx = Counter(r["index_name"] for r in to_judge)
        by_cfg = Counter(r["config"] for r in to_judge)
        print(f"\nDry run — {len(to_judge)} answers to judge:")
        print(f"\nBy index:")
        for k, v in sorted(by_idx.items()):
            print(f"  {k}: {v}")
        print(f"\nBy config:")
        for k, v in sorted(by_cfg.items()):
            print(f"  {k}: {v}")
        return

    # Create model router (Ollama only)
    router = ModelRouter()

    judged_results = list(already_judged)
    n_errors = 0
    t_start = time.time()

    for i, r in enumerate(to_judge):
        qid = r["question_id"]
        q = gt.get(qid, {})
        answer = r["generation"]["answer"]
        is_answerable = r.get("answerable", True)

        progress = f"[{i + 1}/{len(to_judge)}]"
        logger.info(f"{progress} {r['index_name']} | {r['config']} | {qid}")

        try:
            judge_scores = await judge_answer(
                question=r["question"],
                expected=q.get("expected_answer", ""),
                concepts=q.get("expected_concepts", []),
                generated=answer,
                router=router,
                answerable=is_answerable,
            )
        except Exception as e:
            logger.error(f"  Judge error: {e}")
            n_errors += 1
            judge_scores = {
                "correctness": 0, "completeness": 0,
                "faithfulness": 0, "citation_quality": 0,
                "justification": f"Judge error: {e}",
            } if is_answerable else {
                "refusal_accuracy": 0, "hallucination_avoidance": 0,
                "explanation_quality": 0, "justification": f"Judge error: {e}",
            }

        # Update result with judge scores
        r["judge_scores"] = judge_scores
        r["judged_timestamp"] = datetime.now().isoformat()
        judged_results.append(r)

        # Save intermediate every 20 results
        if (i + 1) % 20 == 0:
            _save_judged(judged_results)
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed * 60
            remaining = len(to_judge) - (i + 1)
            eta_h = (remaining / rate) / 60 if rate > 0 else 0
            logger.info(f"  Saved. Rate: {rate:.1f}/min, ETA: {eta_h:.1f}h, Errors: {n_errors}")

    # Final save
    _save_judged(judged_results)

    # Also save back to the generated file with judge scores included
    _save_generated_with_judges(all_results, judged_results)

    elapsed = time.time() - t_start
    n_judged = sum(1 for r in judged_results if r.get("judge_scores", {}))
    logger.info(f"\nDone! {n_judged} judged, {n_errors} errors, {elapsed/60:.1f} min")


def _save_judged(results: List[Dict]):
    """Save judged results."""
    data = {
        "experiment": "v4_5_rlm_judging",
        "judge_model": JUDGE_MODEL,
        "timestamp": datetime.now().isoformat(),
        "n_results": len(results),
        "results": results,
    }
    with open(RLM_JUDGED_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _save_generated_with_judges(all_gen: List[Dict], judged: List[Dict]):
    """Update the generated file with judge scores."""
    judged_map = {
        (r["index_name"], r["config"], r["question_id"]): r.get("judge_scores", {})
        for r in judged
    }
    for r in all_gen:
        key = (r["index_name"], r["config"], r["question_id"])
        if key in judged_map:
            r["judge_scores"] = judged_map[key]

    data = {
        "experiment": "v4_5_rlm_regeneration",
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "timestamp": datetime.now().isoformat(),
        "n_results": len(all_gen),
        "results": all_gen,
    }
    with open(RLM_GENERATED_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def merge_datasets():
    """Merge valid non-RLM results from archive with fresh RLM results."""

    logger.info("=== Merging datasets ===")

    # Load archive (non-RLM results are valid)
    with open(ARCHIVE_FILE) as f:
        archive = json.load(f)
    archive_results = archive.get("per_question_results", archive.get("results", []))
    logger.info(f"Archive: {len(archive_results)} total results")

    # Keep only non-RLM results from archive
    non_rlm = [r for r in archive_results if r.get("config") in NON_RLM_CONFIGS]
    non_rlm_with_answer = [r for r in non_rlm
                           if (r.get("generation", {}).get("answer", "")).strip()]
    logger.info(f"Valid non-RLM from archive: {len(non_rlm_with_answer)}")

    # Load fresh RLM results from all group files
    import glob as globmod
    gen_files = sorted(globmod.glob(str(RESULTS_DIR / "v4_5_rlm_generated*.json")))
    if not gen_files:
        logger.error(f"No RLM generated files found")
        return

    rlm_results = []
    seen_keys = set()
    for gf in gen_files:
        with open(gf) as f:
            data = json.load(f)
        for r in data.get("results", []):
            key = (r["index_name"], r["config"], r["question_id"])
            if key not in seen_keys:
                rlm_results.append(r)
                seen_keys.add(key)
    logger.info(f"Loaded {len(rlm_results)} RLM results from {len(gen_files)} files")
    rlm_with_answer = [r for r in rlm_results
                       if (r.get("generation", {}).get("answer", "")).strip()]
    rlm_with_judge = [r for r in rlm_with_answer if r.get("judge_scores", {})]
    logger.info(f"Fresh RLM: {len(rlm_with_answer)} with answers, {len(rlm_with_judge)} judged")

    # Merge
    merged = non_rlm_with_answer + rlm_with_answer

    # Deduplicate by (index, config, qid) — keep latest
    seen = {}
    for r in merged:
        key = (r["index_name"], r["config"], r["question_id"])
        seen[key] = r  # last wins
    merged_dedup = list(seen.values())

    # Sort for consistency
    merged_dedup.sort(key=lambda r: (r["index_name"], r["config"], r["question_id"]))

    # Stats
    from collections import Counter
    by_cfg = Counter(r["config"] for r in merged_dedup)
    by_idx = Counter(r["index_name"] for r in merged_dedup)
    has_judge = sum(1 for r in merged_dedup if r.get("judge_scores", {}))
    empty = sum(1 for r in merged_dedup
                if not (r.get("generation", {}).get("answer", "")).strip())

    logger.info(f"\n=== Merged dataset ===")
    logger.info(f"Total: {len(merged_dedup)}")
    logger.info(f"With judge: {has_judge}")
    logger.info(f"Empty: {empty}")
    logger.info(f"By config: {dict(sorted(by_cfg.items()))}")
    logger.info(f"By index: {dict(sorted(by_idx.items()))}")

    # Save
    data = {
        "experiment": "v4_5_factorial_scaling",
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "timestamp": datetime.now().isoformat(),
        "n_results": len(merged_dedup),
        "merge_sources": {
            "non_rlm_archive": str(ARCHIVE_FILE),
            "rlm_regenerated": str(RLM_GENERATED_FILE),
        },
        "per_question_results": merged_dedup,
    }
    with open(MERGED_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved merged dataset to {MERGED_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V4-5 RLM judging (Ollama only, no Gemini)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing judged file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be judged without running")
    parser.add_argument("--merge", action="store_true",
                        help="Merge archive non-RLM + fresh RLM into final dataset")
    args = parser.parse_args()

    if args.merge:
        merge_datasets()
    else:
        asyncio.run(run_judging(resume=args.resume, dry_run=args.dry_run))
