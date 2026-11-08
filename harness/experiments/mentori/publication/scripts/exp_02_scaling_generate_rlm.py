#!/usr/bin/env python3
"""
V4-5 Step 1: Regenerate RLM answers using Gemini API ONLY (no Ollama).

Generates the RLM answers (rlm_5, rlm_10, rlm_20) of the corpus-scaling factorial via Gemini. Saves results
WITHOUT judge scores (A7): the lock's judge scores them in a separate step.

Runs under the lock (step 3, A9): the questions are the 135 of answer key v2.4 (D48, experiments/runner/
experiment.py questions()), each asked on an index where it is in scope (Q55, scripts/key_scope.py in_scope: not
answerable at every core size, answerable where min_core <= the core size); one draw (D49, Figure 3); generator
gemini::gemini-3-flash-preview (D27). Every (index, config) is one run, findings/runs/<run_id>/ with run_id
exp_02_scaling_generate_rlm__<config>__<index>, and every (question, draw) of it runs in its own run context. An
answer is keyed by index|config|question_id|d<draw> (experiment.answer_key). --base-url is the run contexts' Ollama
server; this script calls Gemini only, so nothing contacts it.

Usage:
    # Dry run (the work list; no database, no model call, nothing written)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_generate_rlm.py \\
        --dry-run

    # Full run (all RLM configs, all indexes)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_generate_rlm.py \\
        --base-url http://127.0.0.1:21441

    # Specific indexes and configs
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_generate_rlm.py \\
        --base-url http://127.0.0.1:21441 --indexes exp_v4_s20_n0 exp_v4_s50_n0 --configs rlm_10

    # Resume interrupted run
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_generate_rlm.py \\
        --base-url http://127.0.0.1:21441 --resume
"""

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
import time

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from exp_common import (
    GEN_MODEL,
    setup_retriever,
    find_admin_user_id,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    GenerationResult, _run_rlm,
)
from backend.retrieval.rlm.context import RLMContext
from backend.retrieval.rlm.executor import SETUP_ERRORS
from backend.retrieval.rlm.orchestrator import RLMOrchestrator
# exp_common imports backend.agents.lock_adapter, which puts the reanalysis repository on sys.path
from experiments.runner import experiment as ex
from experiments.runner import run_context as rc

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("v4_5_generate_rlm")
logger.setLevel(logging.INFO)

# ── Paths ──
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
ARCHIVE_DIR = RESULTS_DIR / "v4_5_archive_contaminated"

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
EXPERIMENT = "exp_02_scaling_generate_rlm"   # the first part of every run_id of this script
FIGURE = 3
DRAWS = ex.draws(FIGURE)                       # (1,): one draw for Figure 3 (D49)
MODELS = {"generator": GEN_MODEL}              # the run contexts' agent_roles: the RLM's one model

# Q29 (D68; limits #40, #41, #143): one attempt per answer. The whole-answer retry (MAX_RETRIES_PER_QUESTION = 3,
# 30 s apart), the answer-text error check (ERROR_PATTERNS matched case-insensitively against the answer, so
# "internal standard" or "data unavailable" counted as an API error) and the blanking of answers under 20
# characters are deleted. A call error is read from the call's status (the adapter raises LockCallError, the RLM
# ends with stop_reason call_error) and retried only at the call level (the Gemini client's rule, every attempt in
# the call record); an answer is never regenerated and its text never judged as an error.

# The RLM run's record (RLMOrchestrator._metadata) reaches this script through GenerationResult.rlm, which
# exp1_rlm_vs_singlepass._run_rlm fills (the RETRIEVAL track's file); a run refuses to start without that field.
RLM_RECORD_FIELD = "rlm"


def filter_questions(questions: List[Dict], core_size: int) -> List[Dict]:
    """The questions asked at a core size: of the 135 (D48), those in scope (Q55, scripts/key_scope.py in_scope): not
    answerable, or answerable with min_core <= core size. Replaces the filter on category out_of_domain and
    min_core of ground_truth_v4.json (A9)."""
    return [q for q in questions if not q["answerable"] or q["min_core"] <= core_size]


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


@contextlib.contextmanager
def _setup_failures():
    """Collects, for one answer, every setup failure of the RLM: an exception from RLMContext.from_index (the index
    or the reranker did not load, D40) and a LockError or RunContextError from RLMOrchestrator.run (Q38). The caller
    stops the script on any, so a setup failure is never stored, and so never counted as done on resume (review D3,
    written when exp1's _run_rlm stored every exception as the answer's error). Since Q73 (D75) _run_rlm stores only
    an RLMRunError: a failed load raises RLMStop and a lock refusal raises as it is, so the exception reaches the
    caller directly; the list is kept as a second guard. The two methods are restored on exit."""
    caught: List[BaseException] = []
    from_index, run = RLMContext.__dict__["from_index"], RLMOrchestrator.__dict__["run"]

    async def watched_from_index(cls, *args, **kwargs):
        try:
            return await from_index.__get__(None, cls)(*args, **kwargs)
        except Exception as e:
            caught.append(e)
            raise

    async def watched_run(self, *args, **kwargs):
        try:
            return await run(self, *args, **kwargs)
        except SETUP_ERRORS as e:
            caught.append(e)
            raise

    RLMContext.from_index = classmethod(watched_from_index)
    RLMOrchestrator.run = watched_run
    try:
        yield caught
    finally:
        RLMContext.from_index = from_index
        RLMOrchestrator.run = run


async def run_generation(
    indexes: List[str],
    configs: List[str],
    base_url: Optional[str],
    resume: bool = False,
    dry_run: bool = False,
    output_file: Path = None,
):
    """Generate RLM answers for specified indexes and configs."""
    global OUTPUT_FILE
    if output_file:
        OUTPUT_FILE = output_file

    # The 135 questions of answer key v2.4 (D48)
    all_questions = ex.questions()
    logger.info(f"Loaded {len(all_questions)} questions of answer key v2.4")

    # Load existing results for resume; an answer without an answer_key (made before the lock, keyed without its
    # draw) refuses the resume, so no such answer is counted as done
    existing_keys = set()
    existing_results = []
    if resume and OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            data = json.load(f)
            existing_results = data.get("results", [])
            old = [r.get("question_id") for r in existing_results if "answer_key" not in r]
            if old:
                raise SystemExit(f"{OUTPUT_FILE} holds {len(old)} answers without an answer_key (made before the "
                                 f"lock, first {old[:3]}); it is not resumed")
            # Every stored answer is done, a failed one included (Q29, limits #127: it is never regenerated; Q30:
            # it counts as a failure)
            for r in existing_results:
                existing_keys.add(r["answer_key"])
        logger.info(f"Resuming: {len(existing_keys)} existing results loaded")

    # Build work list: one entry per (index, config, draw, question)
    work = []
    for index_name in indexes:
        core_size, noise_ratio = parse_index(index_name)
        questions = filter_questions(all_questions, core_size)

        for config in configs:
            max_turns = RLM_CONFIGS[config]
            for draw in DRAWS:
                for q in questions:
                    key = ex.answer_key(config, q["id"], draw, index=index_name)
                    if key in existing_keys:
                        continue
                    work.append({
                        "index_name": index_name,
                        "config": config,
                        "max_turns": max_turns,
                        "draw": draw,
                        "answer_key": key,
                        "run_id": ex.run_id(EXPERIMENT, config, index_name),
                        "question": q,
                    })

    logger.info(f"Total work: {len(work)} evaluations across {len(indexes)} indexes × {len(configs)} configs")

    if dry_run:
        # Show breakdown
        from collections import Counter
        by_idx = Counter(w["index_name"] for w in work)
        by_cfg = Counter(w["config"] for w in work)
        by_run = Counter((w["run_id"], w["draw"]) for w in work)
        first = {}
        for w in work:
            first.setdefault((w["run_id"], w["draw"]), w["answer_key"])
        print(f"\nDry run (no database read, no model call, nothing written): {len(work)} evals to generate")
        print(f"draws {DRAWS} (D49, Figure {FIGURE}); generator {GEN_MODEL}")
        print(f"\nBy index:")
        for k, v in sorted(by_idx.items()):
            print(f"  {k}: {v}")
        print(f"\nBy config:")
        for k, v in sorted(by_cfg.items()):
            print(f"  {k}: {v}")
        print("\nBy run and draw (first pending answer key):")
        for (run, draw), v in by_run.items():
            print(f"  {run} d{draw}: {v}  {first[(run, draw)]}")
        return

    # The RLM's record must reach every stored answer (A6/D37)
    if RLM_RECORD_FIELD not in GenerationResult.__dataclass_fields__:
        raise SystemExit(f"GenerationResult has no {RLM_RECORD_FIELD!r} field: exp1_rlm_vs_singlepass._run_rlm does "
                         "not yet pass the RLM's record (RLMResult.metadata / RLMRunError.metadata); not run")

    # Resolve admin user
    user_id = find_admin_user_id()
    logger.info(f"Admin user ID: {user_id}")

    # Create model router (Gemini only: no Ollama call)
    router = ModelRouter()

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
        draw = w["draw"]
        is_answerable = q["answerable"]

        progress = f"[{n_done + i + 1}/{n_done + len(work)}]"
        logger.info(f"{progress} {index_name} | {config} | {qid} | d{draw}: {q['question'][:60]}...")

        # The run context of this (question, draw): every model call of the answer is recorded in the run's sink.
        # Built before the RLM starts, so a context the lock or the sink refuses stops the run.
        ctx = ex.context(EXPERIMENT, config, qid, draw, MODELS, base_url=base_url, run=w["run_id"], judge=False)

        # One attempt (Q29). A setup failure (_setup_failures, Q38, D40) stops the script with this answer not stored;
        # the answers made before it are saved first.
        try:
            with rc.run(ctx), _setup_failures() as setup:
                gen_result = await generate_one_rlm(
                    question=q["question"],
                    router=router,
                    model=GEN_MODEL,
                    user_id=user_id,
                    max_turns=max_turns,
                    index_name=index_name,
                    config_name=config,
                )
            if setup:
                raise setup[0]
        except BaseException:
            _save(results)
            raise

        if gen_result.error:
            n_errors += 1
            logger.warning(f"  FAILED: {gen_result.error[:80]}")

        # Unjudged (A7). No citation coverage: the v2.4 key's questions carry no source_files, so the scoring step
        # computes it from the stored answer. generation holds the RLM's record under generation.rlm (A6/D37) and
        # stop_reason repeats its stop reason.
        rlm = getattr(gen_result, RLM_RECORD_FIELD, None)
        result = {
            "stop_reason": rlm.get("stop_reason") if isinstance(rlm, dict) else None,
            "answer_key": w["answer_key"],
            "run_id": w["run_id"],
            "index_name": index_name,
            "question_id": qid,
            "question": q["question"],
            "category": q["category"],
            "answerable": is_answerable,
            "config": config,
            "draw": draw,
            "gen_model": GEN_MODEL,
            "generation": asdict(gen_result),
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
        "draws": list(DRAWS),
        "timestamp": datetime.now().isoformat(),
        "n_results": len(results),
        "results": results,
    }
    # publication/results is not in the copy: without its folder the first save (after 10 answers) would raise
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--base-url", type=str, default=None,
                        help="The Ollama server every run context names (its base_url), e.g. "
                             "http://127.0.0.1:21441; required except with --dry-run. This script calls Gemini only, "
                             "so nothing contacts it")
    args = parser.parse_args()
    if not args.dry_run and not (args.base_url or "").startswith(("http://", "https://")):
        parser.error("--base-url http(s)://host:port is required (the Ollama server of the run contexts)")

    output_file = None
    if args.group:
        output_file = RESULTS_DIR / f"v4_5_rlm_generated_{args.group}.json"

    asyncio.run(run_generation(
        indexes=args.indexes,
        configs=args.configs,
        base_url=args.base_url,
        resume=args.resume,
        dry_run=args.dry_run,
        output_file=output_file,
    ))
