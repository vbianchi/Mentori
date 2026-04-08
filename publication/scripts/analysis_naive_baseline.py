#!/usr/bin/env python3
"""
V4 Naive Baseline: Direct Gemini generation without any orchestration.

This is the simplest possible RAG pipeline:
  retrieve(k=10) → format context → Gemini prompt → answer

No orchestration, no RLM, no planning, no supervisor, no verification.
Serves as the "what if you just asked the LLM?" external baseline.

Two modes:
  --generate : Generate answers only (Gemini API, can run on laptop)
  --judge    : Score existing answers with Ollama judge (needs Mac Studio)

Usage:
    # Generate on MacBook Pro (Gemini API only, no Ollama needed)
    uv run python publication/scripts/analysis_naive_baseline.py --generate

    # Smoke test (3 questions)
    uv run python publication/scripts/analysis_naive_baseline.py --generate --max-questions 3

    # Judge on Mac Studio (needs Ollama)
    uv run python publication/scripts/analysis_naive_baseline.py --judge

    # Resume interrupted run
    uv run python publication/scripts/analysis_naive_baseline.py --generate --resume
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

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
    compute_pass_rate, compute_refusal_rate, compute_median_latency,
    compute_mean_source_coverage, compute_mean_score,
    aggregate_v4_metrics,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import _evaluate_citations

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("analysis_naive_baseline")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = V4_GROUND_TRUTH
DEFAULT_INDEX = "exp_v4_s20_n0"
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_naive_baseline_intermediate.json"

# The naive prompt — minimal, no special instructions
NAIVE_PROMPT = """Answer the following question using ONLY the provided source passages.
If the information is not in the passages, say so clearly.
Cite sources using [N] notation.

## Source Passages
{passages}

## Question
{question}

## Answer"""


# ─────────────────────────────────────────────────────────────
# Core generation (retrieve + prompt, nothing else)
# ─────────────────────────────────────────────────────────────

async def _naive_generate(
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
) -> Dict[str, Any]:
    """Simplest possible RAG: retrieve(k=10) → format → generate."""
    t0 = time.time()

    # Retrieve top-10 chunks
    results = retriever.retrieve(
        query=question,
        top_k=10,
        collection_name=collection_name,
    )

    # Format passages
    passages = []
    sources_used = set()
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("file_name", "unknown")
        page = r["metadata"].get("page", "?")
        text = r["text"][:800]
        passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")
        sources_used.add(source)

    passages_text = "\n\n".join(passages)
    prompt = NAIVE_PROMPT.replace("{passages}", passages_text).replace("{question}", question)

    # Single LLM call — no orchestration, no retry, no verification
    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 8192},
    )

    answer = response.get("response", response.get("message", {}).get("content", ""))
    latency = time.time() - t0

    # Token tracking
    prompt_tokens = response.get("prompt_eval_count", 0)
    completion_tokens = response.get("eval_count", 0)

    return {
        "answer": answer or "",
        "latency_s": round(latency, 1),
        "llm_calls": 1,
        "sources_retrieved": list(sources_used),
        "n_passages": len(passages),
        "word_count": len((answer or "").split()),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


# ─────────────────────────────────────────────────────────────
# Generate phase (Gemini only — can run on laptop)
# ─────────────────────────────────────────────────────────────

async def run_generate(args):
    """Generate answers for all questions using naive baseline."""
    configure_gemini_from_admin()
    user_id = find_admin_user_id()
    index_name = args.index

    if not check_index_exists(user_id, index_name):
        logger.error(f"Index {index_name} not found")
        return

    retriever, collection_name, _ = setup_retriever(user_id, index_name)
    router = ModelRouter()

    # Load questions
    questions = load_ground_truth(GT_FILE)
    # Filter by index core size
    import re
    m = re.search(r"_s(\d+)_", index_name)
    core_size = int(m.group(1)) if m else 50
    questions = [q for q in questions if (q.get("min_core") or 5) <= core_size or not q.get("answerable", True)]

    if args.max_questions:
        questions = questions[:args.max_questions]

    logger.info(f"Naive baseline: {len(questions)} questions on {index_name} with {GEN_MODEL}")

    # Load intermediate results for resume
    intermediate = load_intermediate(INTERMEDIATE_FILE) if args.resume else {"results": [], "completed_keys": []}
    completed = set(intermediate.get("completed_keys", []))

    for i, q in enumerate(questions):
        qid = q["id"]
        key = result_key("naive_baseline", qid)

        if key in completed:
            logger.info(f"[{i+1}/{len(questions)}] Skip {qid} (already done)")
            continue

        logger.info(f"[{i+1}/{len(questions)}] Generating: {qid}")

        try:
            gen_result = await _naive_generate(
                question=q["question"],
                retriever=retriever,
                collection_name=collection_name,
                router=router,
                gen_model=GEN_MODEL,
            )

            # Citation metrics
            expected_sources = q.get("source_files", [])
            if isinstance(expected_sources, str):
                expected_sources = [expected_sources]
            cite_metrics = _evaluate_citations(gen_result["answer"], expected_sources)
            from dataclasses import asdict
            cite_metrics_dict = asdict(cite_metrics) if hasattr(cite_metrics, '__dataclass_fields__') else cite_metrics

            result = {
                "question_id": qid,
                "config": "naive_baseline",
                "question": q["question"],
                "category": q.get("category", "unknown"),
                "answerable": q.get("answerable", True),
                "expected_answer": q.get("expected_answer", ""),
                "expected_concepts": q.get("expected_concepts", []),
                "generation": gen_result,
                "generated_answer": gen_result["answer"],
                "citation_metrics": cite_metrics_dict,
                "index_name": index_name,
                "gen_model": GEN_MODEL,
                "judge_scores": {},  # Filled in judge phase
            }

            intermediate["results"].append(result)
            intermediate["completed_keys"] = list(completed | {key})
            completed.add(key)
            save_intermediate(intermediate, INTERMEDIATE_FILE)

        except Exception as e:
            logger.error(f"Error on {qid}: {e}")
            continue

    logger.info(f"Generation complete: {len(intermediate['results'])} results saved")
    return intermediate


# ─────────────────────────────────────────────────────────────
# Judge phase (needs Ollama — run on Mac Studio)
# ─────────────────────────────────────────────────────────────

async def run_judge(args):
    """Score existing naive baseline answers with the Ollama judge."""
    intermediate = load_intermediate(INTERMEDIATE_FILE)
    if not intermediate["results"]:
        logger.error("No results to judge. Run --generate first.")
        return

    router = ModelRouter()
    n_judged = 0
    n_total = len(intermediate["results"])

    for i, r in enumerate(intermediate["results"]):
        # Skip already judged
        if r.get("judge_scores") and r["judge_scores"].get("correctness") is not None:
            continue
        if not r.get("answerable", True) and r.get("judge_scores", {}).get("refusal_accuracy") is not None:
            continue

        qid = r["question_id"]
        logger.info(f"[{i+1}/{n_total}] Judging: {qid}")

        try:
            scores = await judge_answer(
                question=r["question"],
                expected=r.get("expected_answer", ""),
                concepts=r.get("expected_concepts", []),
                generated=r.get("generated_answer", ""),
                router=router,
                answerable=r.get("answerable", True),
            )
            r["judge_scores"] = scores
            n_judged += 1

            # Save after each judge call
            save_intermediate(intermediate, INTERMEDIATE_FILE)

        except Exception as e:
            logger.error(f"Judge error on {qid}: {e}")
            continue

    logger.info(f"Judging complete: {n_judged} newly scored")

    # Save final results
    answerable = [r for r in intermediate["results"] if r.get("answerable", True)]
    unanswerable = [r for r in intermediate["results"] if not r.get("answerable", True)]

    summary = {
        "experiment": "v4_naive_baseline",
        "timestamp": datetime.now().isoformat(),
        "index": args.index if hasattr(args, 'index') else DEFAULT_INDEX,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "n_total": n_total,
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
        "metrics": aggregate_v4_metrics(intermediate["results"]),
        "per_question_results": intermediate["results"],
    }

    save_v4_results(summary, "v4_naive_baseline")
    logger.info("Final results saved.")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4 Naive Baseline")
    parser.add_argument("--generate", action="store_true", help="Generate answers (Gemini only)")
    parser.add_argument("--judge", action="store_true", help="Judge existing answers (Ollama)")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="Index name")
    parser.add_argument("--max-questions", type=int, default=None, help="Limit questions (smoke test)")
    parser.add_argument("--resume", action="store_true", help="Resume from intermediate file")
    args = parser.parse_args()

    if not args.generate and not args.judge:
        parser.error("Specify --generate or --judge (or both)")

    if args.generate:
        asyncio.run(run_generate(args))

    if args.judge:
        asyncio.run(run_judge(args))


if __name__ == "__main__":
    main()
