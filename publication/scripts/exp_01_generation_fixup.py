#!/usr/bin/env python3
"""
V4-4 Fixup: Re-judge connection-error results and regenerate empty answers.

Parallelizes judge calls across 6 Ollama instances (ports 11434-11439).

Usage:
    uv run python publication/scripts/exp_01_generation_fixup.py
    uv run python publication/scripts/exp_01_generation_fixup.py --dry-run   # just report what needs fixing
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
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter
from backend.agents.models.ollama import OllamaClient

from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever,
    judge_answer,
    V4_RESULTS_DIR, V4_GROUND_TRUTH,
    aggregate_v4_metrics, detect_judge_key,
    format_pct, format_score,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_01_generation_fixup")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

OLLAMA_PORTS = [11434, 11435, 11436, 11437, 11438, 11439]
BATCH_SIZE = 6  # one per Ollama instance
INDEX_NAME = "exp_v4_s20_n0"

LATEST_RESULTS = V4_RESULTS_DIR / "v4_4_generation_latest.json"


def _is_conn_error(r: Dict) -> bool:
    """Check if result has a connection-error judge score."""
    js = r.get("judge_scores", {})
    if not isinstance(js, dict):
        return False
    just = js.get("justification", "")
    return "connection" in just.lower() or "All connection attempts failed" in just


def _is_empty_answer(r: Dict) -> bool:
    """Check if result has an empty/missing answer."""
    gen = r.get("generation", {})
    answer = gen.get("answer", "") if isinstance(gen, dict) else ""
    return not answer


def _create_router(port: int) -> ModelRouter:
    """Create a ModelRouter pointing to a specific Ollama port."""
    router = ModelRouter()
    router.ollama = OllamaClient(base_url=f"http://localhost:{port}")
    return router


# ─────────────────────────────────────────────────────────────
# Judge-only fixup (has answer, bad judge score)
# ─────────────────────────────────────────────────────────────

async def _rejudge_one(
    r: Dict, gt_by_id: Dict, router: ModelRouter, port: int,
) -> Dict:
    """Re-judge a single result using the given router."""
    qid = r["question_id"]
    config = r["config"]
    is_answerable = r.get("answerable", True)
    gen = r.get("generation", {})
    answer = gen.get("answer", "")

    gt_q = gt_by_id.get(qid, {})

    try:
        new_scores = await judge_answer(
            question=r["question"],
            expected=gt_q.get("expected_answer", ""),
            concepts=gt_q.get("expected_concepts", []),
            generated=answer,
            router=router,
            answerable=is_answerable,
        )
        logger.info(f"  Re-judged {config}|{qid} on :{port} -> {_score_summary(new_scores, is_answerable)}")
        return new_scores
    except Exception as e:
        logger.error(f"  Re-judge FAILED {config}|{qid} on :{port}: {e}")
        return None  # keep original on failure


def _score_summary(scores: Dict, answerable: bool) -> str:
    if answerable:
        return f"corr={scores.get('correctness')}"
    else:
        return f"ref={scores.get('refusal_accuracy')}"


# ─────────────────────────────────────────────────────────────
# Regeneration fixup (empty answer)
# ─────────────────────────────────────────────────────────────

async def _regen_one(
    r: Dict, gt_by_id: Dict,
    retriever, collection_name: str,
    gen_router: ModelRouter,
    judge_router: ModelRouter,
    user_id: str,
    judge_port: int,
) -> Dict:
    """Regenerate answer and re-judge for an empty-answer result."""
    qid = r["question_id"]
    config = r["config"]
    is_answerable = r.get("answerable", True)
    gt_q = gt_by_id.get(qid, {})

    # Regenerate
    try:
        if config == "single_pass":
            gen_result = await _single_pass_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        elif config == "multi_hop":
            gen_result = await _multi_hop_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        elif config.startswith("rlm_"):
            max_turns = int(config.split("_")[1])
            gen_result = await _run_rlm(r["question"], gen_router, GEN_MODEL, user_id, max_turns=max_turns, config_name=config, index_name=INDEX_NAME)
        elif config == "verified_pass":
            gen_result = await _verified_pass_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        else:
            raise ValueError(f"Unknown config: {config}")

        logger.info(f"  Regenerated {config}|{qid}: {len(gen_result.answer)} chars")
    except Exception as e:
        logger.error(f"  Regen FAILED {config}|{qid}: {e}")
        return None

    if not gen_result.answer:
        logger.warning(f"  Regen produced empty answer for {config}|{qid}")
        return None

    # Judge the regenerated answer
    try:
        judge_scores = await judge_answer(
            question=r["question"],
            expected=gt_q.get("expected_answer", ""),
            concepts=gt_q.get("expected_concepts", []),
            generated=gen_result.answer,
            router=judge_router,
            answerable=is_answerable,
        )
    except Exception as e:
        logger.error(f"  Judge after regen FAILED {config}|{qid}: {e}")
        judge_scores = {}

    # Citations
    expected_sources = gt_q.get("source_files", [])
    if isinstance(gt_q.get("source_file"), str) and not expected_sources:
        expected_sources = [gt_q["source_file"]]
    cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

    return {
        "generation": asdict(gen_result),
        "judge_scores": judge_scores,
        "citation_metrics": asdict(cit_metrics),
    }


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main(dry_run: bool = False):
    if not LATEST_RESULTS.exists():
        logger.error(f"Results file not found: {LATEST_RESULTS}")
        sys.exit(1)

    with open(LATEST_RESULTS) as f:
        data = json.load(f)

    results = data["per_question_results"]
    logger.info(f"Loaded {len(results)} results from {LATEST_RESULTS.name}")

    # Build ground truth lookup
    with open(V4_GROUND_TRUTH) as f:
        gt_data = json.load(f)
    gt_by_id = {q["id"]: q for q in gt_data["questions"]}

    # Classify what needs fixing
    needs_rejudge = [(i, r) for i, r in enumerate(results) if _is_conn_error(r) and not _is_empty_answer(r)]
    needs_regen = [(i, r) for i, r in enumerate(results) if _is_empty_answer(r)]

    logger.info(f"Connection-error results (re-judge only): {len(needs_rejudge)}")
    logger.info(f"Empty answers (regenerate + judge): {len(needs_regen)}")

    if dry_run:
        logger.info("\n--- Re-judge needed ---")
        for i, r in needs_rejudge:
            logger.info(f"  [{i}] {r['config']} | {r['question_id']}")
        logger.info("\n--- Regen needed ---")
        for i, r in needs_regen:
            logger.info(f"  [{i}] {r['config']} | {r['question_id']}")
        return

    # ── Phase 1: Re-judge (parallel across 6 Ollama instances) ──

    if needs_rejudge:
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase 1: Re-judging {len(needs_rejudge)} results across {len(OLLAMA_PORTS)} Ollama instances")
        logger.info(f"{'='*60}")

        routers = [_create_router(port) for port in OLLAMA_PORTS]
        fixed = 0
        failed = 0

        for batch_start in range(0, len(needs_rejudge), BATCH_SIZE):
            batch = needs_rejudge[batch_start:batch_start + BATCH_SIZE]

            tasks = []
            for j, (idx, r) in enumerate(batch):
                port_idx = j % len(OLLAMA_PORTS)
                tasks.append(_rejudge_one(r, gt_by_id, routers[port_idx], OLLAMA_PORTS[port_idx]))

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for (idx, r), new_scores in zip(batch, batch_results):
                if isinstance(new_scores, Exception):
                    logger.error(f"  Exception for {r['config']}|{r['question_id']}: {new_scores}")
                    failed += 1
                elif new_scores is not None:
                    results[idx]["judge_scores"] = new_scores
                    fixed += 1
                else:
                    failed += 1

            logger.info(f"  Batch {batch_start//BATCH_SIZE + 1}/{(len(needs_rejudge) + BATCH_SIZE - 1)//BATCH_SIZE}: "
                       f"fixed={fixed}, failed={failed}")

        logger.info(f"Phase 1 complete: {fixed} fixed, {failed} failed")

    # ── Phase 2: Regenerate empty answers ──

    if needs_regen:
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase 2: Regenerating {len(needs_regen)} empty answers")
        logger.info(f"{'='*60}")

        configure_gemini_from_admin()
        user_id = find_admin_user_id()
        gen_router = ModelRouter()  # uses default Ollama for any Ollama gen calls
        retriever, collection_name, _ = setup_retriever(user_id, INDEX_NAME)

        # Create judge routers for parallel judging
        judge_routers = [_create_router(port) for port in OLLAMA_PORTS]

        fixed = 0
        failed = 0

        # Regenerate sequentially (RLM configs are heavy on Gemini)
        for j, (idx, r) in enumerate(needs_regen):
            judge_port_idx = j % len(OLLAMA_PORTS)
            result = await _regen_one(
                r, gt_by_id,
                retriever, collection_name,
                gen_router,
                judge_routers[judge_port_idx],
                user_id,
                OLLAMA_PORTS[judge_port_idx],
            )

            if result is not None:
                results[idx]["generation"] = result["generation"]
                results[idx]["judge_scores"] = result["judge_scores"]
                results[idx]["citation_metrics"] = result["citation_metrics"]
                fixed += 1
            else:
                failed += 1

            logger.info(f"  Regen [{j+1}/{len(needs_regen)}]: {r['config']}|{r['question_id']} -> {'OK' if result else 'FAILED'}")

        logger.info(f"Phase 2 complete: {fixed} fixed, {failed} failed")

    # ── Save updated results ──

    logger.info(f"\n{'='*60}")
    logger.info("Saving updated results")
    logger.info(f"{'='*60}")

    # Recompute config metrics
    from collections import defaultdict
    config_results_map = defaultdict(list)
    for r in results:
        config_results_map[r["config"]].append(r)

    judge_key = detect_judge_key(results)
    config_metrics = {}
    for config_name, config_results in config_results_map.items():
        config_metrics[config_name] = aggregate_v4_metrics(config_results, judge_key=judge_key)

    data["per_question_results"] = results
    data["config_metrics"] = config_metrics
    data["timestamp_fixup"] = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save with new timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = V4_RESULTS_DIR / f"v4_4_generation_{ts}.json"
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Update latest symlink
    latest = V4_RESULTS_DIR / "v4_4_generation_latest.json"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    import shutil
    shutil.copy2(out_json, latest)

    logger.info(f"Saved: {out_json.name}")
    logger.info(f"Updated: {latest.name}")

    # Print summary table
    logger.info(f"\n{'='*60}")
    logger.info("Updated Config Metrics")
    logger.info(f"{'='*60}")

    header = f"{'Config':<16} {'Pass%':>6} {'Refusal%':>8} {'MeanCorr':>9}"
    logger.info(header)
    logger.info("-" * len(header))
    for c in ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]:
        m = config_metrics.get(c, {})
        pr = format_pct(m.get("pass_rate", 0))
        rr = format_pct(m.get("refusal_rate", 0)) if m.get("n_unanswerable", 0) > 0 else "-"
        mc = format_score(m.get("mean_correctness", 0))
        logger.info(f"{c:<16} {pr:>6} {rr:>8} {mc:>9}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V4-4 fixup: re-judge and regenerate")
    parser.add_argument("--dry-run", action="store_true", help="Just report what needs fixing")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
