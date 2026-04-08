#!/usr/bin/env python3
"""
V4-5 Fixup: Re-generate empty answers and re-judge connection errors.

Reads from v4_5_scaling_latest.json, fixes problems by index, saves updated file.

Usage:
    uv run python publication/scripts/exp_02_scaling_fixup.py --dry-run
    uv run python publication/scripts/exp_02_scaling_fixup.py --judge-only   # Ollama only, no Gemini
    uv run python publication/scripts/exp_02_scaling_fixup.py --regen-only   # empty answers only
    uv run python publication/scripts/exp_02_scaling_fixup.py                # both

    # Limit to specific indexes or configs:
    uv run python publication/scripts/exp_02_scaling_fixup.py --indexes exp_v4_s5_n0 exp_v4_s10_n0
    uv run python publication/scripts/exp_02_scaling_fixup.py --configs rlm_5 rlm_10

    # s50 RLM regen (expensive — many Gemini calls):
    uv run python publication/scripts/exp_02_scaling_fixup.py --regen-only --indexes exp_v4_s50_n0 exp_v4_s50_n1 exp_v4_s50_n3 --configs rlm_5 rlm_10 rlm_20
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter
from backend.agents.models.ollama import OllamaClient

from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, configure_gemini_from_admin,
    setup_retriever,
    judge_answer,
    V4_RESULTS_DIR, V4_GROUND_TRUTH,
    aggregate_v4_metrics, detect_judge_key,
    format_pct, format_score,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    _evaluate_citations,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("exp_02_scaling_fixup")
logger.setLevel(logging.INFO)

OLLAMA_PORTS = [11434]
BATCH_SIZE = 1  # conservative — single Ollama instance default
LATEST_RESULTS = V4_RESULTS_DIR / "v4_5_scaling_latest.json"


# ─────────────────────────────────────────────────────────────
# Classification helpers
# ─────────────────────────────────────────────────────────────

def _is_judge_error(r: Dict) -> bool:
    js = r.get("judge_scores", {})
    if not isinstance(js, dict):
        return True
    just = js.get("justification", "")
    corr = js.get("correctness")
    ref = js.get("refusal_accuracy")
    # Has no valid score at all
    if corr is None and ref is None:
        return True
    # Has score but it's 0 with a connection/error justification
    if "connection" in just.lower() or "error" in just.lower() or "failed" in just.lower():
        return True
    return False


def _is_empty_answer(r: Dict) -> bool:
    gen = r.get("generation", {})
    answer = gen.get("answer", "") if isinstance(gen, dict) else ""
    return not answer.strip()


def _create_router(port: int) -> ModelRouter:
    router = ModelRouter()
    router.ollama = OllamaClient(base_url=f"http://localhost:{port}")
    return router


# ─────────────────────────────────────────────────────────────
# Re-judge (Ollama only)
# ─────────────────────────────────────────────────────────────

async def _rejudge_one(r: Dict, gt_by_id: Dict, router: ModelRouter, port: int) -> Optional[Dict]:
    qid = r["question_id"]
    config = r["config"]
    is_answerable = r.get("answerable", True)
    gen = r.get("generation", {})
    answer = gen.get("answer", "") if isinstance(gen, dict) else ""

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
        logger.info(f"  Re-judged {config}|{qid} -> corr={new_scores.get('correctness', 'n/a')}")
        return new_scores
    except Exception as e:
        logger.error(f"  Re-judge FAILED {config}|{qid}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Regen (Gemini + Ollama judge)
# ─────────────────────────────────────────────────────────────

async def _regen_one(
    r: Dict,
    gt_by_id: Dict,
    retriever,
    collection_name: str,
    gen_router: ModelRouter,
    judge_router: ModelRouter,
    user_id: str,
) -> Optional[Dict]:
    qid = r["question_id"]
    config = r["config"]
    index_name = r["index_name"]
    is_answerable = r.get("answerable", True)
    gt_q = gt_by_id.get(qid, {})

    try:
        if config == "single_pass":
            gen_result = await _single_pass_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        elif config == "multi_hop":
            gen_result = await _multi_hop_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        elif config.startswith("rlm_"):
            max_turns = int(config.split("_")[1])
            gen_result = await _run_rlm(
                r["question"], gen_router, GEN_MODEL, user_id,
                max_turns=max_turns, config_name=config, index_name=index_name,
            )
        elif config == "verified_pass":
            gen_result = await _verified_pass_rag(r["question"], retriever, collection_name, gen_router, GEN_MODEL)
        else:
            raise ValueError(f"Unknown config: {config}")

        logger.info(f"  Regenerated {config}|{qid} ({index_name}): {len(gen_result.answer)} chars")
    except Exception as e:
        logger.error(f"  Regen FAILED {config}|{qid}: {e}")
        return None

    if not gen_result.answer.strip():
        logger.warning(f"  Regen produced empty answer for {config}|{qid}")
        return None

    # Judge
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

async def main(
    dry_run: bool = False,
    judge_only: bool = False,
    regen_only: bool = False,
    filter_indexes: Optional[List[str]] = None,
    filter_configs: Optional[List[str]] = None,
    ollama_port: int = 11434,
):
    global OLLAMA_PORTS, BATCH_SIZE
    OLLAMA_PORTS = [ollama_port]
    BATCH_SIZE = 1

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

    # Filter by index/config if requested
    def _passes_filter(r):
        if filter_indexes and r.get("index_name") not in filter_indexes:
            return False
        if filter_configs and r.get("config") not in filter_configs:
            return False
        return True

    # Classify
    needs_rejudge = [
        (i, r) for i, r in enumerate(results)
        if _passes_filter(r) and _is_judge_error(r) and not _is_empty_answer(r)
    ]
    needs_regen = [
        (i, r) for i, r in enumerate(results)
        if _passes_filter(r) and _is_empty_answer(r)
    ]

    if judge_only:
        needs_regen = []
    if regen_only:
        needs_rejudge = []

    logger.info(f"Judge-error results (re-judge only): {len(needs_rejudge)}")
    logger.info(f"Empty answers (regenerate + re-judge): {len(needs_regen)}")

    # Breakdown by index
    from collections import Counter
    rj_idx = Counter(r["index_name"] for _, r in needs_rejudge)
    rn_idx = Counter(r["index_name"] for _, r in needs_regen)
    rn_cfg = Counter(r["config"] for _, r in needs_regen)
    logger.info(f"  Re-judge by index: {dict(sorted(rj_idx.items()))}")
    logger.info(f"  Regen by index:    {dict(sorted(rn_idx.items()))}")
    logger.info(f"  Regen by config:   {dict(sorted(rn_cfg.items()))}")

    if dry_run:
        print(f"\n=== DRY RUN ===")
        print(f"Would re-judge: {len(needs_rejudge)} results")
        print(f"Would regen:    {len(needs_regen)} results")
        print(f"\nRe-judge by index: {dict(sorted(rj_idx.items()))}")
        print(f"Regen by index:    {dict(sorted(rn_idx.items()))}")
        print(f"Regen by config:   {dict(sorted(rn_cfg.items()))}")
        return

    if not needs_rejudge and not needs_regen:
        logger.info("Nothing to fix!")
        return

    judge_router = _create_router(ollama_port)

    # ── Phase 1: Re-judge (has answer, broken judge score) ──

    if needs_rejudge:
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase 1: Re-judging {len(needs_rejudge)} results")
        logger.info(f"{'='*60}")

        fixed = 0
        failed = 0
        for j, (idx, r) in enumerate(needs_rejudge):
            new_scores = await _rejudge_one(r, gt_by_id, judge_router, ollama_port)
            if new_scores is not None:
                results[idx]["judge_scores"] = new_scores
                fixed += 1
            else:
                failed += 1
            if (j + 1) % 50 == 0:
                logger.info(f"  [{j+1}/{len(needs_rejudge)}] fixed={fixed}, failed={failed}")

        logger.info(f"Phase 1 complete: {fixed} fixed, {failed} failed")

    # ── Phase 2: Regen empty answers (grouped by index) ──

    if needs_regen:
        logger.info(f"\n{'='*60}")
        logger.info(f"Phase 2: Regenerating {len(needs_regen)} empty answers")
        logger.info(f"{'='*60}")

        configure_gemini_from_admin()
        user_id = find_admin_user_id()
        gen_router = ModelRouter()

        # Group by index_name to set up retriever once per index
        by_index: Dict[str, List[Tuple[int, Dict]]] = defaultdict(list)
        for idx, r in needs_regen:
            by_index[r["index_name"]].append((idx, r))

        total_fixed = 0
        total_failed = 0

        for index_name, index_items in sorted(by_index.items()):
            logger.info(f"\n  Index: {index_name} ({len(index_items)} to regen)")
            try:
                retriever, collection_name, _ = setup_retriever(user_id, index_name)
            except Exception as e:
                logger.error(f"  Could not set up retriever for {index_name}: {e} — skipping")
                total_failed += len(index_items)
                continue

            for j, (idx, r) in enumerate(index_items):
                result = await _regen_one(
                    r, gt_by_id,
                    retriever, collection_name,
                    gen_router, judge_router,
                    user_id,
                )

                if result is not None:
                    results[idx]["generation"] = result["generation"]
                    results[idx]["judge_scores"] = result["judge_scores"]
                    results[idx]["citation_metrics"] = result["citation_metrics"]
                    total_fixed += 1
                else:
                    total_failed += 1

                if (j + 1) % 20 == 0:
                    logger.info(f"    [{j+1}/{len(index_items)}] fixed={total_fixed}, failed={total_failed}")
                    # Save intermediate progress
                    _save(data, results, suffix="_in_progress")

        logger.info(f"Phase 2 complete: {total_fixed} fixed, {total_failed} failed")

    # ── Save ──
    _save(data, results)


def _save(data: Dict, results: List[Dict], suffix: str = ""):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"v4_5_scaling{suffix}_{ts}.json"
    out_path = V4_RESULTS_DIR / out_name

    # Recompute config metrics
    config_results_map = defaultdict(list)
    for r in results:
        config_results_map[r["config"]].append(r)

    judge_key = detect_judge_key(results)
    config_metrics = {}
    for config_name, config_results in config_results_map.items():
        config_metrics[config_name] = aggregate_v4_metrics(config_results, judge_key=judge_key)

    data["per_question_results"] = results
    data["config_metrics"] = config_metrics
    data["timestamp_fixup"] = ts

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    if not suffix:  # only update latest on final save
        latest = V4_RESULTS_DIR / "v4_5_scaling_latest.json"
        shutil.copy2(out_path, latest)
        logger.info(f"Saved: {out_name} | Updated: v4_5_scaling_latest.json")
    else:
        logger.info(f"Progress saved: {out_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V4-5 Fixup: re-generate empty answers and re-judge errors")
    parser.add_argument("--dry-run", action="store_true", help="Report what needs fixing without doing it")
    parser.add_argument("--judge-only", action="store_true", help="Only re-judge (no Gemini calls)")
    parser.add_argument("--regen-only", action="store_true", help="Only regenerate empty answers")
    parser.add_argument(
        "--indexes", nargs="+",
        choices=["exp_v4_s5_n0","exp_v4_s5_n1","exp_v4_s5_n3",
                 "exp_v4_s10_n0","exp_v4_s10_n1","exp_v4_s10_n3",
                 "exp_v4_s20_n0","exp_v4_s20_n1","exp_v4_s20_n3",
                 "exp_v4_s50_n0","exp_v4_s50_n1","exp_v4_s50_n3"],
        help="Filter to specific indexes",
    )
    parser.add_argument(
        "--configs", nargs="+",
        choices=["single_pass","multi_hop","rlm_5","rlm_10","rlm_20","verified_pass"],
        help="Filter to specific configs",
    )
    parser.add_argument("--ollama-port", type=int, default=11434, help="Ollama port for judging")
    args = parser.parse_args()

    asyncio.run(main(
        dry_run=args.dry_run,
        judge_only=args.judge_only,
        regen_only=args.regen_only,
        filter_indexes=args.indexes,
        filter_configs=args.configs,
        ollama_port=args.ollama_port,
    ))
