#!/usr/bin/env python3
"""
V4-6: Orchestration Ablation

Measures the value of multi-agent orchestration itself. Compares 4 additive
configs from raw LLM to full orchestrator:

  1. raw_gemini      — Gemini direct (no retrieval, no orchestration)
  2. naive_rag       — retrieve(k=10) → Gemini (no orchestration)
  3. rlm_10          — RLM with 10 turns (no orchestrator wrapper)
  4. full_orchestrator — Full pipeline: plan → execute → supervise → synthesize

Each config answers the same 138 questions on exp_v4_s20_n0.

Two modes:
  --generate : Generate answers (Gemini API, can run on laptop)
  --judge    : Score existing answers with Ollama judge (needs Mac Studio)

Usage:
    # Generate on MacBook Pro
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate

    # Smoke test (3 questions)
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --max-questions 3

    # Specific configs only
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --configs raw_gemini naive_rag

    # Judge on Mac Studio
    uv run python publication/scripts/exp_03_orchestration_ablation.py --judge

    # Resume
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --resume
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure tool server URL points to local instance (not Docker default)
# Must be set BEFORE importing backend modules (pydantic Settings reads env at import time)
import os
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from backend.agents.model_router import ModelRouter

from exp_common import (
    GEN_MODEL, JUDGE_MODEL, NUM_CTX, NUM_PREDICT,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever, setup_pipeline,
    load_ground_truth, load_intermediate, save_intermediate, result_key,
    judge_answer,
    save_v4_results,
    aggregate_v4_metrics,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _run_rlm,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_03_orchestration_ablation")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = V4_GROUND_TRUTH
DEFAULT_INDEX = "exp_v4_s20_n0"
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_6_intermediate.json"

CONFIG_NAMES = ["raw_gemini", "naive_rag", "rlm_10", "full_orchestrator"]

# Raw prompt (no retrieval context)
RAW_PROMPT = """You are a scientific research assistant. Answer the following question based on your training knowledge.
If you are not confident, say so.

## Question
{question}

## Answer"""

# Naive RAG prompt (same as naive baseline)
NAIVE_RAG_PROMPT = """Answer the following question using ONLY the provided source passages.
If the information is not in the passages, say so clearly.
Cite sources using [N] notation.

## Source Passages
{passages}

## Question
{question}

## Answer"""

# Full orchestrator system prompt
ORCHESTRATOR_SYSTEM = """You are Mentori, a scientific research assistant. Answer the user's question thoroughly using the tools available to you. Search the document index, analyze relevant passages, and provide a well-cited answer."""


# ─────────────────────────────────────────────────────────────
# Config dispatchers
# ─────────────────────────────────────────────────────────────

async def _raw_gemini(question: str, router: ModelRouter) -> Dict[str, Any]:
    """Raw Gemini: no retrieval, no orchestration. Just the LLM."""
    t0 = time.time()
    response = await router.generate(
        model_identifier=GEN_MODEL,
        prompt=RAW_PROMPT.replace("{question}", question),
        options={"temperature": 0.1, "num_predict": NUM_PREDICT},
    )
    answer = response.get("response", response.get("message", {}).get("content", ""))
    return {
        "answer": answer or "",
        "latency_s": round(time.time() - t0, 1),
        "llm_calls": 1,
        "sources_retrieved": [],
        "word_count": len((answer or "").split()),
        "prompt_tokens": response.get("prompt_eval_count", 0),
        "completion_tokens": response.get("eval_count", 0),
    }


async def _naive_rag(question: str, retriever, collection_name: str, router: ModelRouter) -> Dict[str, Any]:
    """Naive RAG: retrieve(k=10) → format → single Gemini call."""
    t0 = time.time()
    results = retriever.retrieve(query=question, top_k=10, collection_name=collection_name)

    passages = []
    sources_used = set()
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("file_name", "unknown")
        page = r["metadata"].get("page", "?")
        text = r["text"][:800]
        passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")
        sources_used.add(source)

    prompt = NAIVE_RAG_PROMPT.replace("{passages}", "\n\n".join(passages)).replace("{question}", question)
    response = await router.generate(
        model_identifier=GEN_MODEL,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": NUM_PREDICT},
    )
    answer = response.get("response", response.get("message", {}).get("content", ""))
    return {
        "answer": answer or "",
        "latency_s": round(time.time() - t0, 1),
        "llm_calls": 1,
        "sources_retrieved": list(sources_used),
        "word_count": len((answer or "").split()),
        "prompt_tokens": response.get("prompt_eval_count", 0),
        "completion_tokens": response.get("eval_count", 0),
    }


async def _full_orchestrator(question: str, user_id: str, index_name: str) -> Dict[str, Any]:
    """Full orchestrator pipeline: plan → execute → supervise → synthesize.

    Calls the orchestrated_chat async generator from the engine, consuming all
    events and extracting the final synthesised answer. Requires:
      - Tool server running on TOOL_SERVER_URL (default http://localhost:8777)
      - Ollama running (for any local model calls during orchestration)
      - Gemini API key set
    """
    from backend.agents.orchestrator.engine import orchestrated_chat
    from backend.agents.session_context import SessionContext, set_session_context

    t0 = time.time()

    # Create workspace directory
    workspace = PROJECT_ROOT / "data" / "workspace" / "v4_6_temp"
    workspace.mkdir(parents=True, exist_ok=True)

    # Set up session context with Gemini for ALL orchestrator roles.
    # This ensures a fair comparison: all 4 V4-6 conditions use the same
    # model (Gemini), isolating the effect of orchestration layers.
    # Previous run had empty agent_roles → distiller fell back to truncation.
    gemini_roles = {
        "lead_researcher": GEN_MODEL,
        "supervisor": GEN_MODEL,
        "librarian": GEN_MODEL,
        "coder": GEN_MODEL,
        "default": GEN_MODEL,
    }
    ctx = SessionContext(
        user_id=user_id,
        user_email="admin@mentori",
        user_role="admin",
        task_id=f"v4_6_orch_{int(time.time())}",
        workspace_path=str(workspace),
        model_identifier=GEN_MODEL,
        mode="agentic",
        agent_roles=gemini_roles,
        rag_preferences={"default_index": index_name},
        available_indexes=[{
            "name": index_name,
            "description": "V4 experiment index",
            "status": "ready",
            "file_count": 20,
        }],
    )
    set_session_context(ctx)

    # Build model router
    router = ModelRouter()

    # Build messages in chat format
    messages = [{"role": "user", "content": question}]

    try:
        answer_chunks = []
        llm_calls = 0

        async for event in orchestrated_chat(
            model_router=router,
            model_identifier=GEN_MODEL,
            messages=messages,
            session_context=ctx,
            max_steps=10,
            think=False,
        ):
            etype = event.get("type", "")
            # Collect answer text from synthesis chunks
            if etype == "chunk":
                answer_chunks.append(event.get("content", ""))
            elif etype == "token_usage":
                llm_calls += 1
            elif etype == "error":
                logger.error(f"Orchestrator event error: {event.get('message', '')}")

        answer = "".join(answer_chunks)
        return {
            "answer": answer or "",
            "latency_s": round(time.time() - t0, 1),
            "llm_calls": llm_calls,
            "sources_retrieved": [],
            "word_count": len((answer or "").split()),
        }
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        return {
            "answer": f"Error: {e}",
            "latency_s": round(time.time() - t0, 1),
            "llm_calls": 0,
            "sources_retrieved": [],
            "word_count": 0,
        }


async def dispatch_config(
    config: str,
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> Dict[str, Any]:
    """Route to the right generation function."""
    if config == "raw_gemini":
        return await _raw_gemini(question, router)
    elif config == "naive_rag":
        return await _naive_rag(question, retriever, collection_name, router)
    elif config == "rlm_10":
        gen_result = await _run_rlm(question, router, GEN_MODEL, user_id, max_turns=10, config_name="rlm_10", index_name=index_name)
        from dataclasses import asdict
        d = asdict(gen_result)
        return {
            "answer": d.get("answer", ""),
            "latency_s": d.get("latency_s", 0),
            "llm_calls": d.get("llm_calls", 0),
            "sources_retrieved": d.get("sources", []),
            "word_count": len(d.get("answer", "").split()),
        }
    elif config == "full_orchestrator":
        return await _full_orchestrator(question, user_id, index_name)
    else:
        raise ValueError(f"Unknown config: {config}")


# ─────────────────────────────────────────────────────────────
# Generate phase
# ─────────────────────────────────────────────────────────────

async def run_generate(args):
    """Generate answers for all configs × questions."""
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
    m = re.search(r"_s(\d+)_", index_name)
    core_size = int(m.group(1)) if m else 50
    questions = [q for q in questions if (q.get("min_core") or 5) <= core_size or not q.get("answerable", True)]

    if args.max_questions:
        questions = questions[:args.max_questions]

    configs = args.configs or CONFIG_NAMES
    total = len(configs) * len(questions)
    logger.info(f"V4-6 Orchestration ablation: {len(configs)} configs × {len(questions)} questions = {total} evals")

    # Load intermediate
    intermediate = load_intermediate(INTERMEDIATE_FILE) if args.resume else {"results": [], "completed_keys": []}
    completed = set(intermediate.get("completed_keys", []))

    count = 0
    for config in configs:
        for i, q in enumerate(questions):
            qid = q["id"]
            key = result_key(config, qid)
            count += 1

            if key in completed:
                logger.info(f"[{count}/{total}] Skip {config}/{qid}")
                continue

            logger.info(f"[{count}/{total}] {config}/{qid}")

            try:
                gen_result = await dispatch_config(
                    config=config,
                    question=q["question"],
                    retriever=retriever,
                    collection_name=collection_name,
                    router=router,
                    user_id=user_id,
                    index_name=index_name,
                )

                expected_sources = q.get("source_files", [])
                if isinstance(expected_sources, str):
                    expected_sources = [expected_sources]
                cite_metrics = _evaluate_citations(gen_result["answer"], expected_sources)

                result = {
                    "question_id": qid,
                    "config": config,
                    "question": q["question"],
                    "category": q.get("category", "unknown"),
                    "answerable": q.get("answerable", True),
                    "expected_answer": q.get("expected_answer", ""),
                    "expected_concepts": q.get("expected_concepts", []),
                    "generation": gen_result,
                    "generated_answer": gen_result["answer"],
                    "citation_metrics": cite_metrics,
                    "index_name": index_name,
                    "gen_model": GEN_MODEL,
                    "judge_scores": {},
                }

                intermediate["results"].append(result)
                intermediate["completed_keys"] = list(completed | {key})
                completed.add(key)
                save_intermediate(intermediate, INTERMEDIATE_FILE)

            except Exception as e:
                logger.error(f"Error on {config}/{qid}: {e}")
                continue

    logger.info(f"Generation complete: {len(intermediate['results'])} results")


# ─────────────────────────────────────────────────────────────
# Judge phase
# ─────────────────────────────────────────────────────────────

async def run_judge(args):
    """Score existing answers with the Ollama judge."""
    intermediate = load_intermediate(INTERMEDIATE_FILE)
    if not intermediate["results"]:
        logger.error("No results to judge. Run --generate first.")
        return

    router = ModelRouter()
    n_judged = 0

    for i, r in enumerate(intermediate["results"]):
        if r.get("judge_scores") and (
            r["judge_scores"].get("correctness") is not None or
            r["judge_scores"].get("refusal_accuracy") is not None
        ):
            continue

        qid = r["question_id"]
        config = r["config"]
        logger.info(f"[{i+1}/{len(intermediate['results'])}] Judging: {config}/{qid}")

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
            save_intermediate(intermediate, INTERMEDIATE_FILE)

        except Exception as e:
            logger.error(f"Judge error on {config}/{qid}: {e}")
            continue

    logger.info(f"Judging complete: {n_judged} newly scored")

    # Save final results with per-config summary
    config_groups = {}
    for r in intermediate["results"]:
        cfg = r["config"]
        if cfg not in config_groups:
            config_groups[cfg] = []
        config_groups[cfg].append(r)

    config_summaries = {}
    for cfg, results in config_groups.items():
        config_summaries[cfg] = aggregate_v4_metrics(results)

    summary = {
        "experiment": "v4_6_orchestration_ablation",
        "timestamp": datetime.now().isoformat(),
        "index": args.index if hasattr(args, 'index') else DEFAULT_INDEX,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "configs": CONFIG_NAMES,
        "config_summaries": config_summaries,
        "n_total": len(intermediate["results"]),
        "per_question_results": intermediate["results"],
    }

    save_v4_results(summary, "v4_6_orchestration_ablation")
    logger.info("Final results saved.")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4-6: Orchestration Ablation")
    parser.add_argument("--generate", action="store_true", help="Generate answers (Gemini only)")
    parser.add_argument("--judge", action="store_true", help="Judge existing answers (Ollama)")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="Index name")
    parser.add_argument("--configs", nargs="+", choices=CONFIG_NAMES, help="Specific configs to run")
    parser.add_argument("--max-questions", type=int, default=None, help="Limit questions")
    parser.add_argument("--resume", action="store_true", help="Resume from intermediate")
    args = parser.parse_args()

    if not args.generate and not args.judge:
        parser.error("Specify --generate or --judge (or both)")

    if args.generate:
        asyncio.run(run_generate(args))

    if args.judge:
        asyncio.run(run_judge(args))


if __name__ == "__main__":
    main()
