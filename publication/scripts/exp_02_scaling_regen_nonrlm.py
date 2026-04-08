#!/usr/bin/env python3
"""
V4-5 Non-RLM error recovery: regenerate entries where Gemini 429 errors
leaked into the answer text. Generation only — judging done separately.

Usage:
    uv run python publication/scripts/exp_02_scaling_regen_nonrlm.py
    uv run python publication/scripts/exp_02_scaling_regen_nonrlm.py --dry-run
    uv run python publication/scripts/exp_02_scaling_regen_nonrlm.py --judge  # judge after gen
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Force CPU embeddings to prevent MPS/GPU wired memory leak
import os
os.environ["MENTORI_EMBED_DEVICE"] = "cpu"

from backend.agents.model_router import ModelRouter
from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, configure_gemini_from_admin,
    setup_retriever, judge_answer,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("v4_5_regen_nonrlm")
logger.setLevel(logging.INFO)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
SCALING_FILE = RESULTS_DIR / "v4_5_scaling_latest.json"
GT_PATH = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"

ERROR_MARKERS = ["429", "RESOURCE_EXHAUSTED", "quota", "{'error':", "error_code"]


def is_bad_result(r: Dict) -> bool:
    gen = r.get("generation", {})
    ans = gen.get("answer", "") if isinstance(gen, dict) else str(gen)
    if not ans.strip() or len(ans.strip()) < 20:
        return True
    return any(m in ans for m in ERROR_MARKERS)


async def run_regen(dry_run: bool = False):
    data = json.load(open(SCALING_FILE))
    key = "per_question_results" if "per_question_results" in data else "results"
    results = data[key]
    gt = {q["id"]: q for q in json.load(open(GT_PATH))["questions"]}

    non_rlm = {"single_pass", "multi_hop", "verified_pass"}
    bad_indices = [i for i, r in enumerate(results) if r.get("config") in non_rlm and is_bad_result(r)]
    logger.info(f"Found {len(bad_indices)} bad non-RLM entries")

    if dry_run:
        from collections import Counter
        by_idx_cfg = Counter((results[i]["index_name"], results[i]["config"]) for i in bad_indices)
        for (idx, cfg), n in sorted(by_idx_cfg.items()):
            print(f"  {idx.replace('exp_v4_', '')}/{cfg}: {n}")
        return

    user_id = find_admin_user_id()
    configure_gemini_from_admin()
    router = ModelRouter()
    retrievers = {}

    n_fixed = 0
    n_errors = 0
    t_start = time.time()

    for pi, idx in enumerate(bad_indices):
        r = results[idx]
        index_name, config, qid = r["index_name"], r["config"], r["question_id"]
        q = gt.get(qid, {})
        question = r["question"]

        logger.info(f"[{pi+1}/{len(bad_indices)}] {index_name} | {config} | {qid}")

        if index_name not in retrievers:
            try:
                ret, coll, _ = setup_retriever(user_id, index_name)
                retrievers[index_name] = (ret, coll)
            except Exception as e:
                logger.error(f"  Retriever failed: {e}")
                n_errors += 1
                continue
        retriever, collection_name = retrievers[index_name]

        try:
            if config == "single_pass":
                gen_result = await _single_pass_rag(question, retriever, collection_name, router, GEN_MODEL)
            elif config == "multi_hop":
                gen_result = await _multi_hop_rag(question, retriever, collection_name, router, GEN_MODEL)
            elif config == "verified_pass":
                gen_result = await _verified_pass_rag(question, retriever, collection_name, router, GEN_MODEL)
            else:
                continue
        except Exception as e:
            logger.error(f"  Gen failed: {e}")
            n_errors += 1
            continue

        ans_text = gen_result.answer or ""
        if any(m in ans_text for m in ERROR_MARKERS):
            logger.warning(f"  Still has error markers, skipping")
            n_errors += 1
            continue

        expected_sources = q.get("source_files", [])
        cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

        # Update in-place (generation only, no judge yet)
        results[idx]["generation"] = asdict(gen_result)
        results[idx]["judge_scores"] = {}  # Clear old bad scores, judge later
        results[idx]["citation_metrics"] = asdict(cit_metrics)
        results[idx]["regen_timestamp"] = datetime.now().isoformat()
        n_fixed += 1

        if (pi + 1) % 50 == 0:
            data[key] = results
            with open(SCALING_FILE, "w") as f:
                json.dump(data, f, indent=2, default=str)
            elapsed = time.time() - t_start
            rate = (pi + 1) / elapsed * 60
            logger.info(f"  Saved. Fixed={n_fixed}, Errors={n_errors}, Rate={rate:.1f}/min")

        await asyncio.sleep(0.5)

    data[key] = results
    with open(SCALING_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"\nGen done! Fixed={n_fixed}, Errors={n_errors}, {(time.time()-t_start)/60:.1f}min")


async def run_judge():
    """Judge all entries that have answers but empty judge_scores."""
    data = json.load(open(SCALING_FILE))
    key = "per_question_results" if "per_question_results" in data else "results"
    results = data[key]
    gt = {q["id"]: q for q in json.load(open(GT_PATH))["questions"]}

    router = ModelRouter()
    to_judge = [(i, r) for i, r in enumerate(results)
                if r.get("generation", {}).get("answer", "").strip()
                and not r.get("judge_scores", {})]

    logger.info(f"Judging {len(to_judge)} unjudged entries")
    n_done = 0

    for pi, (idx, r) in enumerate(to_judge):
        q = gt.get(r["question_id"], {})
        logger.info(f"[{pi+1}/{len(to_judge)}] {r['index_name']} | {r['config']} | {r['question_id']}")

        try:
            scores = await judge_answer(
                question=r["question"],
                expected=q.get("expected_answer", ""),
                concepts=q.get("expected_concepts", []),
                generated=r["generation"]["answer"],
                router=router,
                answerable=r.get("answerable", True),
            )
            results[idx]["judge_scores"] = scores
            n_done += 1
        except Exception as e:
            logger.error(f"  Judge failed: {e}")

        if (pi + 1) % 50 == 0:
            data[key] = results
            with open(SCALING_FILE, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"  Saved. Judged={n_done}/{pi+1}")

    data[key] = results
    with open(SCALING_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Judge done! {n_done}/{len(to_judge)} judged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--judge", action="store_true", help="Judge unjudged entries only")
    args = parser.parse_args()

    if args.judge:
        asyncio.run(run_judge())
    else:
        asyncio.run(run_regen(dry_run=args.dry_run))
