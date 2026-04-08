#!/usr/bin/env python3
"""
V4-5 Step 1: Regenerate RLM answers using Gemini API ONLY (no Ollama).

Reads the archived V4-5 data, identifies contaminated RLM results (rlm_5,
rlm_10, rlm_20), and regenerates them via Gemini. Saves results WITHOUT
judge scores — those are added by exp_02_scaling_judge_rlm.py in a separate step.

Usage:
    # Full run (all RLM configs, all indexes)
    uv run python publication/scripts/exp_02_scaling_generate_rlm.py

    # Specific indexes
    uv run python publication/scripts/exp_02_scaling_generate_rlm.py --indexes exp_v4_s20_n0 exp_v4_s50_n0

    # Specific configs
    uv run python publication/scripts/exp_02_scaling_generate_rlm.py --configs rlm_10

    # Dry run (show what would be regenerated)
    uv run python publication/scripts/exp_02_scaling_generate_rlm.py --dry-run

    # Resume interrupted run
    uv run python publication/scripts/exp_02_scaling_generate_rlm.py --resume
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from exp_common import (
    GEN_MODEL,
    setup_retriever,
    find_admin_user_id,
    configure_gemini_from_admin,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    GenerationResult, _evaluate_citations, _run_rlm,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("v4_5_generate_rlm")
logger.setLevel(logging.INFO)

# ── Paths ──
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
ARCHIVE_DIR = RESULTS_DIR / "v4_5_archive_contaminated"
GT_PATH = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"

# The latest archived file with 9,003 valid results
ARCHIVE_FILE = ARCHIVE_DIR / "v4_5_scaling_in_progress_20260322_120045.json"

# Output (default — overridden by --output or --group)
OUTPUT_FILE = RESULTS_DIR / "v4_5_rlm_generated.json"

# ── Constants ──
RLM_CONFIGS = {
    "rlm_5": 5,
    "rlm_10": 10,
    "rlm_20": 20,
}
CORE_SIZES = [5, 10, 20, 50]
NOISE_RATIOS = [0, 1, 3]
ALL_INDEXES = [f"exp_v4_s{s}_n{n}" for s in CORE_SIZES for n in NOISE_RATIOS]
INTER_REQUEST_DELAY = 1.0  # seconds between Gemini calls

# Patterns that indicate a Gemini API error leaked into the answer text.
# These must be specific enough to avoid false positives (e.g., "500 GB" in a real answer).
ERROR_PATTERNS = [
    "RESOURCE_EXHAUSTED", "rate limit", "rate_limit",
    "UNAVAILABLE", "INTERNAL",
    "GoogleGenerativeAI Error", "API key not valid",
    "Permission denied", "PERMISSION_DENIED",
    "FinishReason.SAFETY", "FinishReason.RECITATION",
    "candidates[0].content", "response.text",
    "error code: 429", "error code: 503", "error code: 500",
    "google.api_core.exceptions",
]

MAX_RETRIES_PER_QUESTION = 3
RETRY_DELAY = 30  # seconds between retries on transient errors


def _detect_answer_error(gen_result: GenerationResult) -> str | None:
    """Check if a GenerationResult contains a disguised API error."""
    answer = str(gen_result.answer or "")

    # Check for error patterns in answer text
    for pattern in ERROR_PATTERNS:
        if pattern.lower() in answer.lower():
            return f"api_error_in_answer: '{pattern}' found"

    # Empty or very short answer (< 20 chars) for what should be substantive
    if len(answer.strip()) < 20 and not gen_result.error:
        return "empty_or_trivial_response"

    return None


def load_ground_truth() -> List[Dict]:
    """Load and return all questions from ground truth."""
    with open(GT_PATH) as f:
        return json.load(f)["questions"]


def filter_questions(questions: List[Dict], core_size: int) -> List[Dict]:
    """Filter questions valid for a given core size."""
    return [
        q for q in questions
        if q.get("category") == "out_of_domain"
        or (q.get("min_core") is not None and q["min_core"] <= core_size)
    ]


def parse_index(index_name: str) -> tuple:
    """Parse index name into (core_size, noise_ratio)."""
    parts = index_name.replace("exp_v4_s", "").split("_n")
    return int(parts[0]), int(parts[1])


async def generate_one_rlm(
    question: str,
    router: ModelRouter,
    model: str,
    user_id: str,
    max_turns: int,
    index_name: str,
    config_name: str,
) -> GenerationResult:
    """Generate a single RLM answer via Gemini.

    Delegates to the same _run_rlm used by V4-4 and the original V4-5,
    ensuring identical behavior (verify=False, think=False).
    """
    return await _run_rlm(
        question=question,
        router=router,
        gen_model=model,
        user_id=user_id,
        max_turns=max_turns,
        verify=False,
        think=False,
        config_name=config_name,
        index_name=index_name,
    )


async def run_generation(
    indexes: List[str],
    configs: List[str],
    resume: bool = False,
    dry_run: bool = False,
    output_file: Path = None,
):
    """Generate RLM answers for specified indexes and configs."""
    global OUTPUT_FILE
    if output_file:
        OUTPUT_FILE = output_file

    # Load ground truth
    all_questions = load_ground_truth()
    logger.info(f"Loaded {len(all_questions)} questions from ground truth")

    # Load existing results for resume
    existing_keys = set()
    existing_results = []
    if resume and OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            data = json.load(f)
            existing_results = data.get("results", [])
            for r in existing_results:
                key = (r["index_name"], r["config"], r["question_id"])
                if r.get("generation", {}).get("answer", "").strip():
                    existing_keys.add(key)
        logger.info(f"Resuming: {len(existing_keys)} existing results loaded")

    # Resolve admin user and configure Gemini API key
    user_id = find_admin_user_id()
    configure_gemini_from_admin()
    logger.info(f"Admin user ID: {user_id}")

    # Create model router (Gemini only — no Ollama needed)
    router = ModelRouter()

    # Build work list
    work = []
    for index_name in indexes:
        core_size, noise_ratio = parse_index(index_name)
        questions = filter_questions(all_questions, core_size)

        for config in configs:
            max_turns = RLM_CONFIGS[config]
            for q in questions:
                key = (index_name, config, q["id"])
                if key in existing_keys:
                    continue
                work.append({
                    "index_name": index_name,
                    "config": config,
                    "max_turns": max_turns,
                    "question": q,
                })

    logger.info(f"Total work: {len(work)} evaluations across {len(indexes)} indexes × {len(configs)} configs")

    if dry_run:
        # Show breakdown
        from collections import Counter
        by_idx = Counter(w["index_name"] for w in work)
        by_cfg = Counter(w["config"] for w in work)
        print(f"\nDry run — {len(work)} evals to generate:")
        print(f"\nBy index:")
        for k, v in sorted(by_idx.items()):
            print(f"  {k}: {v}")
        print(f"\nBy config:")
        for k, v in sorted(by_cfg.items()):
            print(f"  {k}: {v}")
        return

    # Run generation sequentially (no concurrent Gemini calls to avoid issues)
    results = list(existing_results)
    n_done = len(existing_keys)
    n_errors = 0
    t_start = time.time()

    for i, w in enumerate(work):
        index_name = w["index_name"]
        config = w["config"]
        max_turns = w["max_turns"]
        q = w["question"]
        qid = q["id"]
        is_answerable = q.get("answerable", True)

        progress = f"[{n_done + i + 1}/{n_done + len(work)}]"
        logger.info(f"{progress} {index_name} | {config} | {qid}: {q['question'][:60]}...")

        # Generate with retry on transient errors
        gen_result = None
        for attempt in range(MAX_RETRIES_PER_QUESTION):
            gen_result = await generate_one_rlm(
                question=q["question"],
                router=router,
                model=GEN_MODEL,
                user_id=user_id,
                max_turns=max_turns,
                index_name=index_name,
                config_name=config,
            )

            # Check for errors in the result
            if gen_result.error:
                logger.warning(f"  Attempt {attempt+1}/{MAX_RETRIES_PER_QUESTION} error: {gen_result.error[:80]}")
                if attempt < MAX_RETRIES_PER_QUESTION - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                break

            # Check for API errors disguised as answers
            answer_error = _detect_answer_error(gen_result)
            if answer_error:
                logger.warning(f"  Attempt {attempt+1}/{MAX_RETRIES_PER_QUESTION} {answer_error}")
                gen_result = GenerationResult(
                    answer="",
                    latency_s=gen_result.latency_s,
                    llm_calls=gen_result.llm_calls,
                    tokens_used=gen_result.tokens_used,
                    retrieved_passages=gen_result.retrieved_passages,
                    config=config,
                    gen_model=GEN_MODEL,
                    error=answer_error,
                )
                if attempt < MAX_RETRIES_PER_QUESTION - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                break

            # Success
            break

        if gen_result.error:
            n_errors += 1
            logger.warning(f"  FAILED after {MAX_RETRIES_PER_QUESTION} attempts: {gen_result.error[:80]}")

        # Citation metrics (deterministic, no LLM needed)
        expected_sources = q.get("source_files", [])
        if isinstance(q.get("source_file"), str) and not expected_sources:
            expected_sources = [q["source_file"]]
        cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

        result = {
            "index_name": index_name,
            "question_id": qid,
            "question": q["question"],
            "category": q.get("category", "unknown"),
            "answerable": is_answerable,
            "config": config,
            "gen_model": GEN_MODEL,
            "generation": asdict(gen_result),
            "judge_scores": {},  # Empty — filled by judge script
            "citation_metrics": asdict(cit_metrics),
            "generated_timestamp": datetime.now().isoformat(),
        }
        results.append(result)

        # Save intermediate every 10 results
        if (i + 1) % 10 == 0:
            _save(results)
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed * 60
            remaining = len(work) - (i + 1)
            eta_h = (remaining / rate) / 60 if rate > 0 else 0
            logger.info(f"  Saved {len(results)} results. Rate: {rate:.1f}/min, ETA: {eta_h:.1f}h")

        # Rate limiting
        await asyncio.sleep(INTER_REQUEST_DELAY)

    # Final save
    _save(results)

    # Summary
    n_generated = sum(1 for r in results if r.get("generation", {}).get("answer", "").strip())
    elapsed = time.time() - t_start
    logger.info(f"\nDone! {n_generated} answers generated, {n_errors} errors, {elapsed/60:.1f} min")


def _save(results: List[Dict]):
    """Save results to output file."""
    data = {
        "experiment": "v4_5_rlm_regeneration",
        "gen_model": GEN_MODEL,
        "timestamp": datetime.now().isoformat(),
        "n_results": len(results),
        "results": results,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V4-5 RLM generation (Gemini only, no Ollama)")
    parser.add_argument("--indexes", nargs="+", default=ALL_INDEXES,
                        help="Index names to process (default: all 12)")
    parser.add_argument("--configs", nargs="+", default=list(RLM_CONFIGS.keys()),
                        choices=list(RLM_CONFIGS.keys()),
                        help="RLM configs to regenerate (default: all 3)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing output file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without running")
    parser.add_argument("--group", type=str, default=None,
                        help="Group name for parallel runs (creates v4_5_rlm_generated_GROUP.json)")
    args = parser.parse_args()

    output_file = None
    if args.group:
        output_file = RESULTS_DIR / f"v4_5_rlm_generated_{args.group}.json"

    asyncio.run(run_generation(
        indexes=args.indexes,
        configs=args.configs,
        resume=args.resume,
        dry_run=args.dry_run,
        output_file=output_file,
    ))
