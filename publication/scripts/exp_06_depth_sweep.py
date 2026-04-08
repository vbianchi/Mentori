#!/usr/bin/env python3
"""
V4-9: RLM Depth Sweep — Fine-grained saturation curve
======================================================

Tests concept recall across 10+ RLM depths on a stratified question subset
to validate the logarithmic saturation model with more data points.

Supports both Ollama and Gemini models, resume, and retry on failures.

Usage:
    # Smoke test (2 questions × 2 depths)
    uv run python publication/scripts/exp_06_depth_sweep.py --smoke

    # Full run with qwen3-coder (local, no API cost)
    uv run python publication/scripts/exp_06_depth_sweep.py

    # Full run with Gemini
    uv run python publication/scripts/exp_06_depth_sweep.py --model "gemini::gemini-3-flash-preview"

    # Custom depths
    uv run python publication/scripts/exp_06_depth_sweep.py --depths 1 3 5 10 20 40

    # Resume interrupted run
    uv run python publication/scripts/exp_06_depth_sweep.py --resume

    # Custom number of questions
    uv run python publication/scripts/exp_06_depth_sweep.py --n-questions 20

    # Use a different Ollama port
    uv run python publication/scripts/exp_06_depth_sweep.py --port 11435
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Project path setup
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.agents.model_router import ModelRouter
from backend.retrieval.rlm.orchestrator import RLMOrchestrator
from backend.retrieval.rlm.context import RLMContext

from exp_common import (
    find_admin_user_id,
    load_ground_truth,
    judge_answer,
    JUDGE_MODEL,
    GEN_MODEL,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_06_depth_sweep")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

RESULTS_DIR = Path(__file__).resolve().parent / "results_v4"
GT_PATH = Path(__file__).resolve().parents[2] / "datasets" / "ground_truth_v4.json"
INDEX_NAME = "exp_v4_s20_n0"

DEFAULT_DEPTHS = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50]
SMOKE_DEPTHS = [1, 5]

# Stratified question selection: 3 per category from answerable questions
CATEGORIES_TO_SAMPLE = {
    "factual_recall": 3,
    "conceptual": 3,
    "technical": 3,
    "cross_document": 3,
    "synthesis": 3,
}

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class DepthResult:
    """Result from a single (question, depth) evaluation."""
    question_id: str
    question: str
    category: str
    depth: int
    model: str
    answer: str
    latency_s: float
    llm_calls: int
    tokens_used: int
    retrieved_passages: int
    error: Optional[str] = None
    # Filled after judging
    judge_scores: Optional[Dict[str, Any]] = None
    # Filled after citation evaluation
    citation_metrics: Optional[Dict[str, Any]] = None
    # Filled after concept recall computation
    concept_recall: Optional[float] = None


# ─────────────────────────────────────────────────────────────
# Question selection
# ─────────────────────────────────────────────────────────────

def select_questions(n_per_category: Dict[str, int], smoke: bool = False) -> List[Dict]:
    """Select stratified questions from ground truth."""
    questions = load_ground_truth(GT_PATH, answerable_only=True)

    if smoke:
        # Just pick 2 easy questions for smoke test
        easy = [q for q in questions if q.get("difficulty") == "easy"]
        if len(easy) < 2:
            easy = questions[:2]
        return easy[:2]

    selected = []
    by_category = {}
    for q in questions:
        cat = q.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)

    for cat, n in n_per_category.items():
        pool = by_category.get(cat, [])
        if not pool:
            logger.warning(f"No questions for category '{cat}'")
            continue
        # Prefer questions with min_core <= 20 (available in our index)
        eligible = [q for q in pool if q.get("min_core", 999) <= 20]
        if not eligible:
            eligible = pool
        # Take first n (deterministic for reproducibility)
        selected.extend(eligible[:n])

    logger.info(f"Selected {len(selected)} questions across {len(n_per_category)} categories")
    return selected


# ─────────────────────────────────────────────────────────────
# Citation evaluation (from deleted exp1, reconstructed)
# ─────────────────────────────────────────────────────────────

def evaluate_citations(answer: str, expected_sources: List[str]) -> Dict[str, Any]:
    """Extract and evaluate citations from generated answers."""
    # Pattern 1: [source_file:page]
    inline = re.findall(r'\[([^\]]+\.pdf):(?:p(?:age)?)?(\d+)\]', answer, re.IGNORECASE)
    # Pattern 2: Numbered [N]
    numbered = re.findall(r'\[(\d+)\]', answer)
    # Pattern 3: Source lines
    source_lines = re.findall(r'(\S+\.pdf),?\s*page\s*(\d+)', answer, re.IGNORECASE)

    sources_found = set()
    total_citations = 0
    for source, _ in inline:
        sources_found.add(source)
        total_citations += 1
    for source, _ in source_lines:
        sources_found.add(source)
    total_citations += len(numbered)

    word_count = len(answer.split())
    density = (total_citations / max(word_count, 1)) * 100

    if expected_sources:
        covered = sum(
            1 for s in expected_sources
            if any(s.lower() in found.lower() for found in sources_found)
        )
        coverage = covered / len(expected_sources)
    else:
        coverage = 0.0

    return {
        "total_citations": total_citations,
        "unique_sources": len(sources_found),
        "citation_density": round(density, 2),
        "source_coverage": round(coverage, 2),
    }


# ─────────────────────────────────────────────────────────────
# Concept recall computation
# ─────────────────────────────────────────────────────────────

def compute_concept_recall(answer: str, expected_concepts: List[str]) -> float:
    """Compute fraction of expected concepts found in the answer."""
    if not expected_concepts:
        return 0.0
    answer_lower = answer.lower()
    found = 0
    for concept in expected_concepts:
        # Exact match or fuzzy (concept as substring)
        if concept.lower() in answer_lower:
            found += 1
    return round(found / len(expected_concepts), 4)


# ─────────────────────────────────────────────────────────────
# RLM execution with retry
# ─────────────────────────────────────────────────────────────

async def run_rlm_with_retry(
    question: str,
    router: ModelRouter,
    model: str,
    user_id: str,
    depth: int,
    index_name: str,
    max_retries: int = MAX_RETRIES,
) -> Dict[str, Any]:
    """Run RLM at a given depth with retry on failure."""
    for attempt in range(max_retries):
        t0 = time.time()
        try:
            context = await RLMContext.from_index(
                index_name=index_name,
                user_id=user_id,
            )
            orchestrator = RLMOrchestrator(
                model_router=router,
                model_identifier=model,
                max_turns=depth,
                verify=False,
                think=False,
            )
            result = await orchestrator.run(task=question, context=context)
            latency = time.time() - t0

            return {
                "answer": result,
                "latency_s": latency,
                "llm_calls": context.llm_calls_made,
                "tokens_used": context.total_tokens_used,
                "retrieved_passages": len(context.citations),
                "error": None,
            }
        except Exception as e:
            latency = time.time() - t0
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return {
                    "answer": "",
                    "latency_s": latency,
                    "llm_calls": 0,
                    "tokens_used": 0,
                    "retrieved_passages": 0,
                    "error": str(e),
                }


# ─────────────────────────────────────────────────────────────
# Resume support
# ─────────────────────────────────────────────────────────────

def result_key(question_id: str, depth: int) -> str:
    return f"{question_id}|d{depth}"


def load_existing_results(output_path: Path) -> Dict[str, DepthResult]:
    """Load existing results for resume."""
    if not output_path.exists():
        return {}
    with open(output_path) as f:
        data = json.load(f)
    existing = {}
    for r in data.get("results", []):
        key = result_key(r["question_id"], r["depth"])
        existing[key] = r
    return existing


# ─────────────────────────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────────────────────────

async def run_experiment(args):
    """Run the depth sweep experiment."""
    depths = args.depths
    model = args.model
    smoke = args.smoke

    if smoke:
        depths = SMOKE_DEPTHS
        logger.info("SMOKE TEST MODE: 2 questions × 2 depths")

    # Select questions
    questions = select_questions(
        {cat: args.n_questions // 5 or 3 for cat in CATEGORIES_TO_SAMPLE}
        if not smoke else CATEGORIES_TO_SAMPLE,
        smoke=smoke,
    )

    total_evals = len(questions) * len(depths)
    logger.info(f"Depth sweep: {len(questions)} questions × {len(depths)} depths = {total_evals} evaluations")
    logger.info(f"Model: {model}")
    logger.info(f"Depths: {depths}")
    logger.info(f"Index: {INDEX_NAME}")

    # Output path — include port to avoid write conflicts when running in parallel
    model_short = model.split("::")[-1].replace(":", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    port_suffix = f"_p{args.port}" if args.port != 11434 else ""
    output_path = RESULTS_DIR / f"v4_9_depth_sweep_{model_short}{port_suffix}_{timestamp}.json"
    latest_path = RESULTS_DIR / f"v4_9_depth_sweep_{model_short}{port_suffix}_latest.json"

    # Resume support — scan ALL files for this model (any port) to find completed keys
    existing = {}
    if args.resume:
        pattern = f"v4_9_depth_sweep_{model_short}*.json"
        for f in sorted(RESULTS_DIR.glob(pattern)):
            if f.name.endswith("_merged.json"):
                continue
            file_results = load_existing_results(f)
            existing.update(file_results)
        if existing:
            logger.info(f"Resuming: found {len(existing)} existing results across all files")
        else:
            logger.info("No existing results found, starting fresh")

    # Setup
    user_id = find_admin_user_id()

    # Configure model router
    if args.port and args.port != 11434:
        import os
        os.environ["OLLAMA_BASE_URL"] = f"http://localhost:{args.port}"

    # If Gemini model, configure API key BEFORE creating ModelRouter
    # (ModelRouter.__init__ creates GeminiClient which needs the key)
    if model.startswith("gemini::"):
        from exp_common import configure_gemini_from_admin
        configure_gemini_from_admin()

    router = ModelRouter()

    all_results = list(existing.values())
    completed = set(existing.keys())
    n_skipped = 0
    n_errors = 0

    for qi, q in enumerate(questions):
        qid = q["id"]
        expected_concepts = q.get("expected_concepts", [])
        expected_sources = q.get("source_files", [])

        for di, depth in enumerate(depths):
            key = result_key(qid, depth)
            if key in completed:
                n_skipped += 1
                continue

            progress = f"[{qi * len(depths) + di + 1}/{total_evals}]"
            logger.info(f"{progress} {qid} @ depth={depth} ...")

            # Run RLM
            rlm_result = await run_rlm_with_retry(
                question=q["question"],
                router=router,
                model=model,
                user_id=user_id,
                depth=depth,
                index_name=INDEX_NAME,
            )

            if rlm_result["error"]:
                n_errors += 1
                logger.error(f"  FAILED: {rlm_result['error'][:100]}")

            # Compute concept recall
            cr = compute_concept_recall(rlm_result["answer"], expected_concepts)

            # Evaluate citations
            cit = evaluate_citations(rlm_result["answer"], expected_sources)

            # Judge (skip if answer is empty)
            judge_scores = {}
            if rlm_result["answer"] and not rlm_result["error"]:
                try:
                    judge_scores = await judge_answer(
                        question=q["question"],
                        expected=q.get("expected_answer", ""),
                        concepts=expected_concepts,
                        generated=rlm_result["answer"],
                        router=router,
                        judge_model=JUDGE_MODEL,
                        answerable=True,
                    )
                except Exception as e:
                    logger.warning(f"  Judge failed: {e}")
                    judge_scores = {"error": str(e)}

            result = {
                "question_id": qid,
                "question": q["question"],
                "category": q.get("category", "unknown"),
                "depth": depth,
                "model": model,
                "answer": rlm_result["answer"],
                "latency_s": round(rlm_result["latency_s"], 2),
                "llm_calls": rlm_result["llm_calls"],
                "tokens_used": rlm_result["tokens_used"],
                "retrieved_passages": rlm_result["retrieved_passages"],
                "error": rlm_result["error"],
                "judge_scores": judge_scores,
                "citation_metrics": cit,
                "concept_recall": cr,
            }

            all_results.append(result)
            completed.add(key)

            # Save intermediate results after each evaluation
            _save_results(all_results, output_path, latest_path, model, depths, questions)

            logger.info(f"  CR={cr:.3f}, latency={rlm_result['latency_s']:.1f}s, "
                        f"citations={cit['total_citations']}, "
                        f"coverage={cit['source_coverage']:.2f}")

    # Final save
    _save_results(all_results, output_path, latest_path, model, depths, questions)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"DEPTH SWEEP COMPLETE")
    logger.info(f"  Total: {len(all_results)} results")
    logger.info(f"  Skipped (resumed): {n_skipped}")
    logger.info(f"  Errors: {n_errors}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"{'='*60}")

    # Print saturation summary
    print("\n--- Saturation Summary ---")
    print(f"{'Depth':>6} | {'Mean CR':>8} | {'Std CR':>8} | {'n':>4} | {'Mean Lat':>8}")
    print("-" * 50)
    by_depth = {}
    for r in all_results:
        d = r["depth"]
        if d not in by_depth:
            by_depth[d] = []
        if r.get("concept_recall") is not None and not r.get("error"):
            by_depth[d].append(r)

    for d in sorted(by_depth.keys()):
        results = by_depth[d]
        crs = [r["concept_recall"] for r in results]
        lats = [r["latency_s"] for r in results]
        if crs:
            import statistics
            mean_cr = statistics.mean(crs)
            std_cr = statistics.stdev(crs) if len(crs) > 1 else 0
            mean_lat = statistics.mean(lats)
            print(f"{d:>6} | {mean_cr:>8.4f} | {std_cr:>8.4f} | {len(crs):>4} | {mean_lat:>7.1f}s")


def _save_results(results, output_path, latest_path, model, depths, questions):
    """Save results to JSON."""
    data = {
        "experiment": "v4_9_depth_sweep",
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "depths": depths,
        "n_questions": len(questions),
        "question_ids": [q["id"] for q in questions],
        "index": INDEX_NAME,
        "n_results": len(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    with open(latest_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def merge_results(model: str):
    """Merge all parallel depth sweep results for a model into one file."""
    model_short = model.split("::")[-1].replace(":", "_").replace("/", "_")
    pattern = f"v4_9_depth_sweep_{model_short}*.json"
    all_results = {}

    for f in sorted(RESULTS_DIR.glob(pattern)):
        if f.name.endswith("_merged.json"):
            continue
        with open(f) as fh:
            data = json.load(fh)
        for r in data.get("results", []):
            key = result_key(r["question_id"], r["depth"])
            # Keep the latest (or non-error) version
            if key not in all_results or (all_results[key].get("error") and not r.get("error")):
                all_results[key] = r

    merged = list(all_results.values())
    merged.sort(key=lambda r: (r["question_id"], r["depth"]))

    output = {
        "experiment": "v4_9_depth_sweep",
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "n_results": len(merged),
        "results": merged,
    }

    merged_path = RESULTS_DIR / f"v4_9_depth_sweep_{model_short}_merged.json"
    with open(merged_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"Merged {len(merged)} results → {merged_path.name}")

    # Print summary
    import statistics
    by_depth = {}
    for r in merged:
        d = r["depth"]
        if d not in by_depth:
            by_depth[d] = []
        if r.get("concept_recall") is not None and not r.get("error"):
            by_depth[d].append(r)

    print("\n--- Merged Saturation Summary ---")
    print(f"{'Depth':>6} | {'Mean CR':>8} | {'Std CR':>8} | {'n':>4} | {'Mean Lat':>8}")
    print("-" * 50)
    for d in sorted(by_depth.keys()):
        results = by_depth[d]
        crs = [r["concept_recall"] for r in results]
        lats = [r["latency_s"] for r in results]
        if crs:
            mean_cr = statistics.mean(crs)
            std_cr = statistics.stdev(crs) if len(crs) > 1 else 0
            mean_lat = statistics.mean(lats)
            print(f"{d:>6} | {mean_cr:>8.4f} | {std_cr:>8.4f} | {len(crs):>4} | {mean_lat:>7.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="V4-9: RLM Depth Sweep — fine-grained saturation curve"
    )
    parser.add_argument(
        "--model", type=str, default="ollama::qwen3-coder:latest",
        help="Model identifier (default: ollama::qwen3-coder:latest)"
    )
    parser.add_argument(
        "--depths", type=int, nargs="+", default=DEFAULT_DEPTHS,
        help=f"Depths to test (default: {DEFAULT_DEPTHS})"
    )
    parser.add_argument(
        "--n-questions", type=int, default=15,
        help="Total questions (stratified across 5 categories, default: 15)"
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke test: 2 questions × 2 depths"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from latest results file"
    )
    parser.add_argument(
        "--port", type=int, default=11434,
        help="Ollama port (default: 11434)"
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="Merge all parallel results for this model and print summary"
    )

    args = parser.parse_args()

    if args.merge:
        merge_results(args.model)
    else:
        asyncio.run(run_experiment(args))


if __name__ == "__main__":
    main()
