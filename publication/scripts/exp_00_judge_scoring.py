#!/usr/bin/env python3
"""
V4-0 Phase 3: Score Phase 2 answers with candidate judge models.

Standalone scoring script — no reference judge needed.
Designed to run in parallel across multiple Ollama instances via OLLAMA_BASE_URL.

Usage:
    # Score with specific judges on a specific Ollama instance
    OLLAMA_BASE_URL=http://localhost:11434 \
      uv run python publication/scripts/exp_00_judge_scoring.py \
        --judges "ollama::gemma3:27b" "ollama::qwen3-coder:latest" \
        --run-id g1

    # Resume after interruption
    OLLAMA_BASE_URL=http://localhost:11434 \
      uv run python publication/scripts/exp_00_judge_scoring.py \
        --judges "ollama::gemma3:27b" --run-id g1 --resume
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.experiments_v4 import exp_common
from exp_common import (
    JUDGE_OPTIONS,
    judge_answer,
    load_ground_truth,
    load_intermediate,
    save_intermediate,
    find_admin_user_id,
    V4_GROUND_TRUTH,
    V4_RESULTS_DIR,
    save_v4_results,
)

# Override: judging needs ~4K context, not 98K. Reduces KV cache from ~8GB to ~200MB
# per model, allowing many more concurrent Ollama instances.
JUDGE_NUM_CTX = 16384  # generous for judge prompt (~4K tokens)
exp_common.JUDGE_OPTIONS = {**JUDGE_OPTIONS, "num_ctx": JUDGE_NUM_CTX}

logger = logging.getLogger("exp_00_judge_scoring")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

PHASE2_FILE = V4_RESULTS_DIR / "v4_0_phase2_latest.json"
SCORE_DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]


def load_phase2_answers(path: Path) -> List[Dict[str, Any]]:
    data = json.load(open(path))
    results = data["per_question_results"]
    valid = [r for r in results if r.get("completed") and r.get("final_answer")]
    logger.info(f"Loaded {len(valid)} valid answers from {len(results)} total")
    return valid


async def run_scoring(
    judge_models: List[str],
    phase2_file: Path = PHASE2_FILE,
    run_id: str = "default",
    resume: bool = False,
):
    from backend.agents.model_router import ModelRouter

    intermediate_file = V4_RESULTS_DIR / f"v4_0_judge_scoring_intermediate_{run_id}.json"

    answers = load_phase2_answers(phase2_file)
    gt_questions = load_ground_truth(V4_GROUND_TRUTH, answerable_only=False)
    gt_lookup = {q["id"]: q for q in gt_questions}

    # Filter to answers with GT
    answers = [a for a in answers if a["question_id"] in gt_lookup]
    logger.info(f"Scoring {len(answers)} answers with {len(judge_models)} judge models")

    router = ModelRouter()

    # Resume support
    if resume and intermediate_file.exists():
        intermediate = load_intermediate(intermediate_file)
    else:
        intermediate = {"scores": {}, "completed_keys": []}

    completed = set(intermediate.get("completed_keys", []))
    all_scores = intermediate.get("scores", {})

    total = len(judge_models) * len(answers)
    done = 0
    errors = 0

    for judge_model in judge_models:
        if judge_model not in all_scores:
            all_scores[judge_model] = {}

        logger.info(f"\n{'='*60}")
        logger.info(f"JUDGE: {judge_model}")
        logger.info(f"{'='*60}")

        t_model_start = time.time()

        for a in answers:
            qid = a["question_id"]
            gen_model = a["model"]
            key = f"{judge_model}|{gen_model}|{qid}"
            result_key = f"{gen_model}|{qid}"

            if key in completed:
                done += 1
                continue

            done += 1
            gt = gt_lookup[qid]

            try:
                t0 = time.time()
                scores = await judge_answer(
                    question=a["question"],
                    expected=gt.get("expected_answer", ""),
                    concepts=gt.get("expected_concepts", []),
                    generated=a["final_answer"],
                    router=router,
                    answerable=a.get("answerable", True),
                    judge_model=judge_model,
                    think=False,
                )
                elapsed = time.time() - t0
                corr = scores.get("correctness", "?")
                logger.info(
                    f"  [{done}/{total}] {gen_model[:25]} | {qid}: "
                    f"correctness={corr} ({elapsed:.1f}s)"
                )
            except Exception as e:
                logger.error(f"  [{done}/{total}] ERROR: {e}")
                scores = {dim: 0 for dim in SCORE_DIMS}
                scores["justification"] = f"Error: {e}"
                errors += 1

            all_scores[judge_model][result_key] = scores
            completed.add(key)
            intermediate["scores"] = all_scores
            intermediate["completed_keys"] = list(completed)
            save_intermediate(intermediate, intermediate_file)

        t_model_elapsed = time.time() - t_model_start
        n_scored = len(all_scores[judge_model])
        nonzero = sum(1 for s in all_scores[judge_model].values() if s.get("correctness", 0) > 0)
        logger.info(
            f"  {judge_model} done: {n_scored} scored, {nonzero} non-zero, "
            f"{t_model_elapsed:.0f}s total"
        )

    # Save final results
    output_data = {
        "experiment": "v4_0_judge_scoring",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "run_id": run_id,
        "judge_models": judge_models,
        "n_answers": len(answers),
        "n_errors": errors,
        "all_scores": all_scores,
    }

    json_path, _ = save_v4_results(output_data, f"v4_0_judge_scoring_{run_id}")
    logger.info(f"\nSaved: {json_path}")

    # Cleanup intermediate
    if intermediate_file.exists():
        intermediate_file.unlink()
        logger.info("Cleaned up intermediate file")

    return json_path


def main():
    parser = argparse.ArgumentParser(description="V4-0: Judge Model Scoring")
    parser.add_argument("--judges", nargs="+", required=True, help="Judge model IDs")
    parser.add_argument("--phase2-file", type=Path, default=PHASE2_FILE)
    parser.add_argument("--run-id", default="default", help="Run ID for parallel execution")
    parser.add_argument("--resume", action="store_true", help="Resume from intermediate")

    args = parser.parse_args()
    asyncio.run(run_scoring(
        judge_models=args.judges,
        phase2_file=args.phase2_file,
        run_id=args.run_id,
        resume=args.resume,
    ))


if __name__ == "__main__":
    main()
