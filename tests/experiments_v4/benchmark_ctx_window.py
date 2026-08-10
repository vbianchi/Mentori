#!/usr/bin/env python3
"""
Quick benchmark: Run 2 questions through RLM with the new num_ctx/num_predict
settings and monitor memory bandwidth + answer quality.

Compares old settings (num_ctx=2048, num_predict=2000) vs new (98304 / 8192).

Usage:
    uv run python tests/experiments_v4/benchmark_ctx_window.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter
from tests.experiments_v4.exp_common import (
    GEN_MODEL, JUDGE_MODEL, NUM_CTX, NUM_PREDICT,
    JUDGE_OPTIONS, GEN_OPTIONS,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever, judge_answer,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _run_rlm, GenerationResult,
)

# Pick 2 questions from GT that exercise different categories
GT_FILE = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"
INDEX = "exp_v4_s20_n0"


async def run_benchmark():
    with open(GT_FILE) as f:
        gt = json.load(f)

    # Pick 1 factual + 1 conceptual from answerable questions
    questions = []
    for q in gt["questions"]:
        if not q.get("answerable", True):
            continue
        cat = q.get("category", "")
        if cat == "factual_recall" and not any(x["category"] == "factual_recall" for x in questions):
            questions.append(q)
        elif cat == "conceptual" and not any(x["category"] == "conceptual" for x in questions):
            questions.append(q)
        if len(questions) == 2:
            break

    print(f"Selected questions:")
    for q in questions:
        print(f"  [{q['category']}] {q['id']}: {q['question'][:80]}...")

    user_id = find_admin_user_id()
    configure_gemini_from_admin()

    if not check_index_exists(user_id, INDEX):
        print(f"ERROR: Index {INDEX} not found")
        sys.exit(1)

    router = ModelRouter()
    retriever, collection_name, _ = setup_retriever(user_id, INDEX)

    print(f"\n{'='*70}")
    print(f"Settings: NUM_CTX={NUM_CTX}, NUM_PREDICT={NUM_PREDICT}")
    print(f"GEN_MODEL: {GEN_MODEL}")
    print(f"JUDGE_MODEL: {JUDGE_MODEL}")
    print(f"JUDGE_OPTIONS: {JUDGE_OPTIONS}")
    print(f"GEN_OPTIONS: {GEN_OPTIONS}")
    print(f"{'='*70}\n")

    results = []

    for q in questions:
        print(f"\n{'─'*60}")
        print(f"Q: {q['question']}")
        print(f"Category: {q['category']} | ID: {q['id']}")
        print(f"Expected: {q.get('expected_answer', '')[:200]}...")
        print(f"{'─'*60}")

        # --- single_pass ---
        print("\n[single_pass] Running...")
        t0 = time.time()
        sp_result = await _single_pass_rag(
            q["question"], retriever, collection_name, router, GEN_MODEL,
        )
        sp_time = time.time() - t0
        print(f"[single_pass] {len(sp_result.answer)} chars, {sp_time:.1f}s")
        print(f"[single_pass] Answer preview: {sp_result.answer[:300]}...")

        # --- rlm_10 ---
        print("\n[rlm_10] Running...")
        t0 = time.time()
        rlm_result = await _run_rlm(
            q["question"], router, GEN_MODEL, user_id,
            max_turns=10, config_name="rlm_10", index_name=INDEX,
        )
        rlm_time = time.time() - t0
        print(f"[rlm_10] {len(rlm_result.answer)} chars, {rlm_time:.1f}s")
        print(f"[rlm_10] Answer preview: {rlm_result.answer[:300]}...")

        # --- Judge both ---
        for label, gen_result in [("single_pass", sp_result), ("rlm_10", rlm_result)]:
            if gen_result.answer and not gen_result.error:
                scores = await judge_answer(
                    question=q["question"],
                    expected=q.get("expected_answer", ""),
                    concepts=q.get("expected_concepts", []),
                    generated=gen_result.answer,
                    router=router,
                    answerable=True,
                )
                print(f"\n[{label}] Judge scores: {scores}")

                results.append({
                    "question_id": q["id"],
                    "category": q["category"],
                    "config": label,
                    "answer_len": len(gen_result.answer),
                    "latency_s": round(gen_result.latency_s, 1),
                    "llm_calls": gen_result.llm_calls,
                    "retrieved_passages": gen_result.retrieved_passages,
                    "judge_scores": scores,
                })

    # Summary
    print(f"\n\n{'='*70}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"{'Config':<15} {'QID':<25} {'Len':>6} {'Time':>6} {'Corr':>5} {'Compl':>5} {'Faith':>5}")
    print(f"{'─'*15} {'─'*25} {'─'*6} {'─'*6} {'─'*5} {'─'*5} {'─'*5}")
    for r in results:
        s = r.get("judge_scores", {})
        print(
            f"{r['config']:<15} {r['question_id']:<25} "
            f"{r['answer_len']:>6} {r['latency_s']:>5.0f}s "
            f"{s.get('correctness', '?'):>5} {s.get('completeness', '?'):>5} {s.get('faithfulness', '?'):>5}"
        )

    # Save
    out_path = PROJECT_ROOT / "tests" / "experiments_v4" / "results_v4" / "benchmark_ctx_window.json"
    with open(out_path, "w") as f:
        json.dump({
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "gen_model": GEN_MODEL,
            "judge_model": JUDGE_MODEL,
            "results": results,
        }, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
