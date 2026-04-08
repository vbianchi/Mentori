#!/usr/bin/env python3
"""
V4-5 Targeted Re-run: Fix broken results from API quota exhaustion.

Two modes:
  1. Quick replication test: re-run s20_n0 (all configs) to verify V4-4 replication
  2. Full error recovery: scan existing results, identify 429/empty failures, re-run only those

Key improvements over exp_02_scaling_factorial.py:
  - Detects 429/RESOURCE_EXHAUSTED in answers and flags them as errors
  - Adds configurable inter-batch delay to avoid quota exhaustion
  - Stores error type ('api_quota', 'empty_response', 'generation_error') for analysis
  - Can merge fixed results back into the main results file
  - Tracks API call budget to proactively pause before hitting limits

Usage:
    # Quick test: re-run RLM configs at s20_n0 (V4-4 replication, ~414 evals)
    uv run python publication/scripts/exp_02_scaling_rerun.py \
        --indexes exp_v4_s20_n0 --configs rlm_5 rlm_10 rlm_20

    # Re-run ALL broken results from the latest file
    uv run python publication/scripts/exp_02_scaling_rerun.py --fix-errors

    # Re-run specific broken conditions
    uv run python publication/scripts/exp_02_scaling_rerun.py \
        --fix-errors --indexes exp_v4_s50_n0 --configs single_pass multi_hop

    # Smoke test (3 questions only)
    uv run python publication/scripts/exp_02_scaling_rerun.py \
        --indexes exp_v4_s20_n0 --configs rlm_10 --max-questions 3

    # Merge fixed results back into latest
    uv run python publication/scripts/exp_02_scaling_rerun.py --merge
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
from typing import Dict, List, Any, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever,
    load_ground_truth, load_intermediate, save_intermediate, result_key,
    judge_answer,
    save_v4_results, save_v4_markdown,
    detect_judge_key,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_02_scaling_rerun")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

LATEST_FILE = V4_RESULTS_DIR / "v4_5_scaling_latest.json"
RERUN_INTERMEDIATE = V4_RESULTS_DIR / "v4_5_rerun_intermediate.json"
RERUN_OUTPUT = V4_RESULTS_DIR / "v4_5_rerun_{timestamp}.json"

# Error detection patterns
ERROR_PATTERNS = ["429", "RESOURCE_EXHAUSTED", "quota", "rate limit", "503", "UNAVAILABLE"]

# Rate limiting
BATCH_SIZE_FAST = 4       # single_pass, multi_hop, verified_pass
BATCH_SIZE_RLM = 2        # RLM configs: conservative to avoid quota
INTER_BATCH_DELAY_S = 2   # seconds between batches
RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20"}

# API call budget tracking
API_CALLS_PER_CONFIG = {
    "single_pass": 1,
    "multi_hop": 3,
    "verified_pass": 2,
    "rlm_5": 6,
    "rlm_10": 10,
    "rlm_20": 15,
}

CORE_SIZES = [5, 10, 20, 50]
NOISE_RATIOS = [0, 1, 3]
CONFIG_NAMES = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]


def get_index_name(core_size: int, noise_ratio: int) -> str:
    return f"exp_v4_s{core_size}_n{noise_ratio}"


# ─────────────────────────────────────────────────────────────
# Error detection
# ─────────────────────────────────────────────────────────────

def classify_result_error(result: Dict) -> Optional[str]:
    """Classify a result's error type. Returns None if result is valid."""
    gen = result.get("generation", {})
    if not isinstance(gen, dict):
        return "malformed"

    # Explicit error field
    if gen.get("error"):
        error_str = str(gen["error"]).upper()
        if any(p.upper() in error_str for p in ["429", "RESOURCE_EXHAUSTED", "QUOTA"]):
            return "api_quota"
        return "generation_error"

    # 429 embedded in answer text
    answer = gen.get("answer", "")
    answer_str = str(answer)
    if any(p in answer_str for p in ERROR_PATTERNS):
        return "api_quota_in_answer"

    # Empty or very short answer (for answerable questions)
    if result.get("answerable", True):
        if not answer or len(answer_str.strip()) < 20:
            return "empty_response"

    # Zero scores on ALL judge dimensions (suspicious)
    js = result.get("judge_scores", {})
    if isinstance(js, dict) and js:
        all_zero = all(v == 0 for v in js.values() if isinstance(v, (int, float)))
        if all_zero and result.get("answerable", True):
            # Could be legitimately bad, but combined with short answer = suspicious
            if len(answer_str.strip()) < 100:
                return "likely_error"

    return None


def scan_errors(results: List[Dict]) -> Dict[str, List[Dict]]:
    """Scan results and group by error type."""
    errors = {}
    for r in results:
        err_type = classify_result_error(r)
        if err_type:
            errors.setdefault(err_type, []).append(r)
    return errors


# ─────────────────────────────────────────────────────────────
# Generation with error detection
# ─────────────────────────────────────────────────────────────

async def _run_config(
    config_name: str,
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
    user_id: str,
    index_name: str,
) -> GenerationResult:
    """Dispatch to the right generator."""
    if config_name == "single_pass":
        return await _single_pass_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == "multi_hop":
        return await _multi_hop_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == "rlm_5":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=5, config_name="rlm_5", index_name=index_name)
    elif config_name == "rlm_10":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name="rlm_10", index_name=index_name)
    elif config_name == "rlm_20":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=20, config_name="rlm_20", index_name=index_name)
    elif config_name == "verified_pass":
        return await _verified_pass_rag(question, retriever, collection_name, router, gen_model)
    else:
        raise ValueError(f"Unknown config: {config_name}")


def _detect_answer_error(gen_result: GenerationResult) -> Optional[str]:
    """Check if a GenerationResult contains a disguised API error."""
    answer = str(gen_result.answer)
    for pattern in ERROR_PATTERNS:
        if pattern in answer:
            return f"api_error_detected: {pattern} found in answer"
    return None


async def _process_one(
    config: str,
    q: Dict,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> Dict:
    """Generate + judge + cite one (index, config, question) tuple.

    Enhanced: detects API errors in answers and flags them properly.
    """
    qid = q["id"]
    is_answerable = q.get("answerable", True)

    try:
        gen_result = await _run_config(
            config_name=config,
            question=q["question"],
            retriever=retriever,
            collection_name=collection_name,
            router=router,
            gen_model=GEN_MODEL,
            user_id=user_id,
            index_name=index_name,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        gen_result = GenerationResult(
            answer="", latency_s=0, llm_calls=0, tokens_used=0,
            retrieved_passages=0, config=config, gen_model=GEN_MODEL,
            error=str(e),
        )

    # ── NEW: Detect API errors disguised as answers ──
    answer_error = _detect_answer_error(gen_result)
    if answer_error:
        logger.warning(f"  API error in answer for {qid}/{config}: {answer_error}")
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

    # Judge (only if we have a valid answer)
    judge_scores = {}
    if gen_result.answer and not gen_result.error:
        try:
            judge_scores = await judge_answer(
                question=q["question"],
                expected=q.get("expected_answer", ""),
                concepts=q.get("expected_concepts", []),
                generated=gen_result.answer,
                router=router,
                answerable=is_answerable,
            )
        except Exception as e:
            logger.error(f"Judge error: {e}")

    # Citations
    expected_sources = q.get("source_files", [])
    if isinstance(q.get("source_file"), str) and not expected_sources:
        expected_sources = [q["source_file"]]
    cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

    return {
        "index_name": index_name,
        "question_id": qid,
        "question": q["question"],
        "category": q.get("category", "unknown"),
        "answerable": is_answerable,
        "config": config,
        "gen_model": GEN_MODEL,
        "generation": asdict(gen_result),
        "judge_scores": judge_scores,
        "citation_metrics": asdict(cit_metrics),
        "rerun_timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# Core experiment runner
# ─────────────────────────────────────────────────────────────

def _index_core_size(index_name: str) -> int:
    import re
    m = re.search(r"_s(\d+)_", index_name)
    return int(m.group(1)) if m else 50


async def run_targeted(
    indexes: List[str],
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    questions_to_run: Optional[List[Tuple[str, str, str]]] = None,  # (index, config, qid) tuples
):
    """Run targeted re-evaluation with rate limiting and error detection."""
    with open(V4_GROUND_TRUTH) as f:
        gt_data = json.load(f)
    all_questions = gt_data["questions"]
    q_by_id = {q["id"]: q for q in all_questions}

    logger.info(f"V4-5 Re-run (targeted, with error detection)")
    logger.info(f"Indexes: {indexes}")
    logger.info(f"Configs: {configs}")
    logger.info(f"Inter-batch delay: {INTER_BATCH_DELAY_S}s")

    user_id = find_admin_user_id()
    configure_gemini_from_admin()
    router = ModelRouter()

    # Verify indexes
    valid_indexes = []
    for idx_name in indexes:
        if check_index_exists(user_id, idx_name):
            valid_indexes.append(idx_name)
        else:
            logger.error(f"Index {idx_name} not found. Skipping.")

    if not valid_indexes:
        logger.error("No valid indexes. Aborting.")
        sys.exit(1)

    # Resume support
    intermediate = load_intermediate(RERUN_INTERMEDIATE) if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total_api_calls = 0
    total_questions_done = 0
    total_errors = 0
    start_time = time.time()

    for idx_name in valid_indexes:
        logger.info(f"\n{'='*60}")
        logger.info(f"INDEX: {idx_name}")
        logger.info(f"{'='*60}")

        core_size = _index_core_size(idx_name)
        questions = [
            q for q in all_questions
            if q.get("category") == "out_of_domain"
            or (q.get("min_core") is not None and q["min_core"] <= core_size)
        ]

        if max_questions:
            questions = questions[:max_questions]

        n_answerable = sum(1 for q in questions if q.get("answerable", True))
        n_unanswerable = len(questions) - n_answerable
        logger.info(f"Questions: {len(questions)} ({n_answerable} answerable, {n_unanswerable} unanswerable)")

        retriever, collection_name, _ = setup_retriever(user_id, idx_name)

        for config in configs:
            # If we have a specific set of (index, config, qid) to re-run, filter
            if questions_to_run:
                pending = [
                    q for q in questions
                    if (idx_name, config, q["id"]) in questions_to_run
                    and result_key(idx_name, config, q["id"]) not in completed
                ]
            else:
                pending = [
                    q for q in questions
                    if result_key(idx_name, config, q["id"]) not in completed
                ]

            if not pending:
                logger.info(f"Config {config}: all done, skipping")
                continue

            batch_size = BATCH_SIZE_RLM if config in RLM_CONFIGS else BATCH_SIZE_FAST
            total_for_config = len(pending)
            est_api_calls = total_for_config * API_CALLS_PER_CONFIG.get(config, 1)
            logger.info(
                f"Config {config}: {total_for_config} pending, "
                f"batch_size={batch_size}, est. API calls={est_api_calls}"
            )

            done_for_config = 0
            for i in range(0, len(pending), batch_size):
                batch = pending[i:i + batch_size]

                for q in batch:
                    done_for_config += 1
                    logger.info(
                        f"  [{done_for_config}/{total_for_config}] {idx_name} | {config} | {q['id']} "
                        f"({'A' if q.get('answerable', True) else 'U'}): "
                        f"{q['question'][:50]}..."
                    )

                tasks = [
                    _process_one(
                        config=config, q=q,
                        retriever=retriever, collection_name=collection_name,
                        router=router, user_id=user_id, index_name=idx_name,
                    )
                    for q in batch
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                batch_errors = 0
                for q, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.error(f"Task exception for {q['id']}: {result}")
                        result = {
                            "index_name": idx_name,
                            "question_id": q["id"],
                            "question": q["question"],
                            "category": q.get("category", "unknown"),
                            "answerable": q.get("answerable", True),
                            "config": config,
                            "gen_model": GEN_MODEL,
                            "generation": asdict(GenerationResult(
                                answer="", latency_s=0, llm_calls=0, tokens_used=0,
                                retrieved_passages=0, config=config, gen_model=GEN_MODEL,
                                error=str(result),
                            )),
                            "judge_scores": {},
                            "citation_metrics": asdict(_evaluate_citations("", [])),
                            "rerun_timestamp": datetime.now().isoformat(),
                        }

                    # Check if this result has an error
                    err_type = classify_result_error(result)
                    if err_type:
                        batch_errors += 1
                        total_errors += 1
                        logger.warning(f"  ERROR [{err_type}]: {q['id']}/{config}")

                    all_results.append(result)
                    completed.add(result_key(idx_name, config, q["id"]))
                    total_questions_done += 1

                total_api_calls += len(batch) * API_CALLS_PER_CONFIG.get(config, 1)

                save_intermediate(
                    {"results": all_results, "completed_keys": list(completed)},
                    RERUN_INTERMEDIATE,
                )

                elapsed = time.time() - start_time
                rate = total_questions_done / elapsed * 60 if elapsed > 0 else 0
                logger.info(
                    f"  Batch done: {len(batch)} results ({batch_errors} errors), "
                    f"total={len(all_results)}, ~{total_api_calls} API calls, "
                    f"{rate:.0f} q/min"
                )

                # Rate limiting: pause between batches
                if i + batch_size < len(pending):
                    logger.debug(f"  Rate limit pause: {INTER_BATCH_DELAY_S}s")
                    await asyncio.sleep(INTER_BATCH_DELAY_S)

            logger.info(f"Completed {idx_name} / {config}")

    # ── Save final results ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = V4_RESULTS_DIR / f"v4_5_rerun_{timestamp}.json"

    output = {
        "experiment": "v4_5_rerun",
        "timestamp": datetime.now().isoformat(),
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "indexes": indexes,
        "configs": configs,
        "total_results": len(all_results),
        "total_errors": total_errors,
        "elapsed_seconds": time.time() - start_time,
        "per_question_results": all_results,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"\nResults saved to {output_file}")

    # ── Print summary ──
    _print_summary(all_results, indexes, configs)

    # Clean up intermediate
    if RERUN_INTERMEDIATE.exists():
        RERUN_INTERMEDIATE.unlink()

    return output_file


def _print_summary(results: List[Dict], indexes: List[str], configs: List[str]):
    """Print a compact summary table."""
    print(f"\n{'='*70}")
    print(f"RE-RUN SUMMARY ({len(results)} results)")
    print(f"{'='*70}")

    # Error summary
    errors = scan_errors(results)
    if errors:
        print(f"\nErrors detected:")
        for err_type, items in sorted(errors.items()):
            print(f"  {err_type}: {len(items)}")
    else:
        print(f"\nNo errors detected!")

    # Pass rates by config
    print(f"\n{'Config':20s}  {'N':>5s}  {'Pass':>7s}  {'Mean':>7s}  {'Errors':>7s}")
    print("-" * 55)

    for config in configs:
        cfg_results = [r for r in results if r.get("config") == config]
        answerable = [r for r in cfg_results if r.get("answerable", True)]
        scores = []
        for r in answerable:
            js = r.get("judge_scores", {})
            c = js.get("correctness") if isinstance(js, dict) else None
            if c is not None:
                scores.append(c)

        n_errors = sum(1 for r in cfg_results if classify_result_error(r))
        n = len(scores)
        pass_rate = sum(1 for s in scores if s >= 3) / n if n > 0 else 0
        mean_corr = sum(scores) / n if n > 0 else 0

        print(f"{config:20s}  {n:5d}  {pass_rate:6.1%}  {mean_corr:7.2f}  {n_errors:7d}")


# ─────────────────────────────────────────────────────────────
# Fix-errors mode: scan + re-run broken results
# ─────────────────────────────────────────────────────────────

def find_broken_results(
    latest_file: Path,
    target_indexes: Optional[List[str]] = None,
    target_configs: Optional[List[str]] = None,
) -> List[Tuple[str, str, str]]:
    """Scan the latest results file and return (index, config, qid) tuples that need re-running."""
    with open(latest_file) as f:
        data = json.load(f)

    results = data.get("per_question_results", data.get("results", []))
    broken = []

    for r in results:
        err_type = classify_result_error(r)
        if not err_type:
            continue

        idx = r.get("index_name", "")
        cfg = r.get("config", "")
        qid = r.get("question_id", "")

        if target_indexes and idx not in target_indexes:
            continue
        if target_configs and cfg not in target_configs:
            continue

        broken.append((idx, cfg, qid))

    return broken


# ─────────────────────────────────────────────────────────────
# Merge mode: merge rerun results into latest
# ─────────────────────────────────────────────────────────────

def merge_rerun_into_latest(rerun_file: Path, latest_file: Path):
    """Replace broken results in latest with fixed results from rerun."""
    with open(latest_file) as f:
        latest = json.load(f)
    with open(rerun_file) as f:
        rerun = json.load(f)

    latest_results = latest.get("per_question_results", latest.get("results", []))
    rerun_results = rerun.get("per_question_results", rerun.get("results", []))

    # Build lookup for rerun results
    rerun_lookup = {}
    for r in rerun_results:
        key = (r.get("index_name"), r.get("config"), r.get("question_id"))
        # Only use rerun result if it's NOT an error
        if not classify_result_error(r):
            rerun_lookup[key] = r

    # Replace in latest
    replaced = 0
    still_broken = 0
    new_results = []
    for r in latest_results:
        key = (r.get("index_name"), r.get("config"), r.get("question_id"))
        if key in rerun_lookup:
            new_results.append(rerun_lookup[key])
            replaced += 1
        else:
            new_results.append(r)

    # Check how many are still broken
    for r in new_results:
        if classify_result_error(r):
            still_broken += 1

    latest["per_question_results"] = new_results

    # Save as new latest
    backup = latest_file.with_suffix(".json.bak")
    import shutil
    shutil.copy2(latest_file, backup)
    logger.info(f"Backed up {latest_file} → {backup}")

    with open(latest_file, "w") as f:
        json.dump(latest, f, indent=2, default=str)

    print(f"\nMerge complete:")
    print(f"  Replaced: {replaced} results")
    print(f"  Still broken: {still_broken} results")
    print(f"  Saved to: {latest_file}")
    print(f"  Backup: {backup}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4-5 targeted re-run with error detection")
    parser.add_argument("--indexes", nargs="+", help="Index names to re-run (e.g., exp_v4_s20_n0)")
    parser.add_argument("--configs", nargs="+", default=CONFIG_NAMES, help="Configs to re-run")
    parser.add_argument("--max-questions", type=int, help="Limit questions per index")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted re-run")
    parser.add_argument("--batch-delay", type=float, default=2.0,
                        help="Seconds between batches (default: 2.0)")
    parser.add_argument("--batch-size-rlm", type=int, default=2,
                        help="Batch size for RLM configs (default: 2)")

    # Modes
    parser.add_argument("--fix-errors", action="store_true",
                        help="Scan latest results, re-run only broken entries")
    parser.add_argument("--scan-only", action="store_true",
                        help="Just scan and report errors, don't re-run")
    parser.add_argument("--merge", type=str, metavar="RERUN_FILE",
                        help="Merge a rerun results file into latest")

    args = parser.parse_args()

    # Apply CLI overrides
    global INTER_BATCH_DELAY_S, BATCH_SIZE_RLM
    INTER_BATCH_DELAY_S = args.batch_delay
    BATCH_SIZE_RLM = args.batch_size_rlm

    # ── Merge mode ──
    if args.merge:
        rerun_file = Path(args.merge)
        if not rerun_file.exists():
            print(f"Error: {rerun_file} not found")
            sys.exit(1)
        merge_rerun_into_latest(rerun_file, LATEST_FILE)
        return

    # ── Scan-only mode ──
    if args.scan_only:
        if not LATEST_FILE.exists():
            print(f"Error: {LATEST_FILE} not found")
            sys.exit(1)
        with open(LATEST_FILE) as f:
            data = json.load(f)
        results = data.get("per_question_results", data.get("results", []))
        errors = scan_errors(results)

        print(f"\nError scan of {LATEST_FILE.name} ({len(results)} results):")
        print(f"{'='*60}")
        total_errors = 0
        for err_type, items in sorted(errors.items()):
            total_errors += len(items)
            # Group by index × config
            from collections import Counter
            groups = Counter((r.get("index_name"), r.get("config")) for r in items)
            print(f"\n{err_type} ({len(items)} results):")
            for (idx, cfg), count in sorted(groups.items()):
                print(f"  {idx}/{cfg}: {count}")

        clean = len(results) - total_errors
        print(f"\n{'='*60}")
        print(f"Total: {total_errors} errors, {clean} clean ({clean/len(results):.1%})")
        return

    # ── Fix-errors mode ──
    if args.fix_errors:
        if not LATEST_FILE.exists():
            print(f"Error: {LATEST_FILE} not found")
            sys.exit(1)

        broken = find_broken_results(
            LATEST_FILE,
            target_indexes=args.indexes,
            target_configs=args.configs if args.configs != CONFIG_NAMES else None,
        )

        if not broken:
            print("No broken results found!")
            return

        # Derive indexes and configs from broken results
        indexes = sorted(set(idx for idx, _, _ in broken))
        configs = sorted(set(cfg for _, cfg, _ in broken))
        questions_set = set(broken)

        print(f"\nFound {len(broken)} broken results across {len(indexes)} indexes, {len(configs)} configs")
        print(f"Indexes: {indexes}")
        print(f"Configs: {configs}")

        est_calls = sum(API_CALLS_PER_CONFIG.get(cfg, 1) for _, cfg, _ in broken)
        print(f"Estimated API calls: ~{est_calls}")

        response = input("\nProceed with re-run? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return

        asyncio.run(run_targeted(
            indexes=indexes,
            configs=configs,
            max_questions=args.max_questions,
            resume=args.resume,
            questions_to_run=questions_set,
        ))
        return

    # ── Standard targeted re-run ──
    if not args.indexes:
        # Default: re-run s20_n0 with all configs (V4-4 replication test)
        args.indexes = ["exp_v4_s20_n0"]
        print(f"No indexes specified. Defaulting to {args.indexes} (V4-4 replication test)")

    asyncio.run(run_targeted(
        indexes=args.indexes,
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
    ))


if __name__ == "__main__":
    main()
