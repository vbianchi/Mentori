#!/usr/bin/env python3
"""
V4-5: Factorial Scaling Experiment (Core Size × Noise Ratio)

Does pass rate degrade due to corpus size, noise injection, or both?
This factorial design separates the two effects.

Design:
  Indexes: 12 factorial configs (4 core sizes × 3 noise ratios)
    - Core sizes: 5, 10, 20, 50
    - Noise ratios: 0x, 1x, 3x
    - Example: exp_v4_s20_n1 = 20 core + 20 noise papers
  Questions: V4 ground truth (paper-level questions filtered by min_core)
  6 gen configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass

Primary metric: % pass rate per (core_size, noise_ratio, gen_config)
Secondary: median latency, 2D heatmaps showing degradation patterns

Output: Factorial heatmaps isolating noise vs scale effects.

Usage:
    # Full run
    uv run python publication/scripts/exp_02_scaling_factorial.py

    # Smoke test
    uv run python publication/scripts/exp_02_scaling_factorial.py \\
        --indexes exp_v4_s5_n0 --configs single_pass --max-questions 3

    # Specific core sizes and noise ratios
    uv run python publication/scripts/exp_02_scaling_factorial.py \\
        --core-sizes 5 10 --noise-ratios 0 1 --configs single_pass rlm_10

    # Resume after interruption
    uv run python publication/scripts/exp_02_scaling_factorial.py --resume
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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
    compute_pass_rate, compute_median_latency, compute_mean_score,
    detect_judge_key,
    format_v4_table, format_pct, format_latency,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_02_scaling_factorial")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = V4_GROUND_TRUTH
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_5_intermediate.json"

# Factorial design: 4 core sizes × 3 noise ratios = 12 index configs
CORE_SIZES = [5, 10, 20, 50]
NOISE_RATIOS = [0, 1, 3]  # 0x, 1x, 3x noise multiplier

def get_index_name(core_size: int, noise_ratio: int) -> str:
    """Generate index name from factorial parameters."""
    return f"exp_v4_s{core_size}_n{noise_ratio}"

ALL_INDEXES = [get_index_name(c, n) for c in CORE_SIZES for n in NOISE_RATIOS]

CONFIG_NAMES = [
    "single_pass",
    "multi_hop",
    "rlm_5",
    "rlm_10",
    "rlm_20",
    "verified_pass",
]


# ─────────────────────────────────────────────────────────────
# Config dispatch
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


# ─────────────────────────────────────────────────────────────
# Batched parallel processing
# ─────────────────────────────────────────────────────────────

# Concurrency: RLM configs are heavy (many sequential Gemini calls per question),
# so we use lower batch sizes to avoid Gemini rate limits.
BATCH_SIZE_FAST = 6   # single_pass, multi_hop, verified_pass
BATCH_SIZE_RLM = 4    # rlm_5, rlm_10, rlm_20 (bumped from 2; embedding leak fixed)
RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20"}

# Memory safety: restart interval and pressure threshold
# Root cause (embedding singleton leak) fixed — periodic restarts no longer needed.
# Keep memory-pressure restart as safety net only.
RESTART_EVERY_N_BATCHES = 0  # disabled — embedding leak fixed, no longer needed
MEMORY_PRESSURE_THRESHOLD_GB = 100  # restart Ollama if active+wired+comp exceeds this (512GB system)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def _get_memory_used_gb() -> float:
    """Get current physical memory used (GB) on macOS via vm_stat."""
    try:
        out = subprocess.check_output(["vm_stat"], text=True)
        page_size = 16384  # Apple Silicon default
        pages_used = 0
        for line in out.splitlines():
            # Count active + wired + compressed (= memory actually consumed)
            for key in ["Pages active", "Pages wired down", "Pages occupied by compressor"]:
                if line.startswith(key):
                    val = int(line.split(":")[1].strip().rstrip("."))
                    pages_used += val
        return (pages_used * page_size) / (1024 ** 3)
    except Exception:
        return 0.0


def _get_ollama_port() -> int:
    """Extract port from OLLAMA_BASE_URL."""
    import re
    m = re.search(r":(\d+)", OLLAMA_BASE_URL)
    return int(m.group(1)) if m else 11434


def _restart_ollama() -> None:
    """Port-aware restart of the Ollama instance on the configured port only.

    Only kills the specific Ollama process bound to our port, so parallel
    instances on other ports are unaffected.

    Retries up to 3 times if Ollama fails to come back."""
    import urllib.request

    port = _get_ollama_port()
    host = f"0.0.0.0:{port}"
    log_file = f"/tmp/ollama_{port}.log"
    max_retries = 3

    for retry in range(max_retries):
        if retry > 0:
            logger.warning(f"  [memory] Restart attempt {retry + 1}/{max_retries}...")

        logger.info(f"  [memory] Hard restart: killing Ollama on port {port}...")

        # Kill ONLY the Ollama process bound to our specific port
        try:
            pid_out = subprocess.check_output(
                f"lsof -ti tcp:{port}", shell=True, text=True
            ).strip()
            if pid_out:
                for pid in pid_out.splitlines():
                    pid = pid.strip()
                    if pid:
                        subprocess.run(["kill", "-9", pid], check=False)
                        logger.info(f"  [memory] Killed PID {pid} on port {port}")
        except subprocess.CalledProcessError:
            logger.info(f"  [memory] No process found on port {port}")

        time.sleep(3)

        # Restart using nohup + shell redirect
        subprocess.Popen(
            ["bash", "-c", f"nohup env OLLAMA_HOST={host} ollama serve >> {log_file} 2>&1 &"],
        )
        logger.info(f"  [memory] Restarted Ollama on port {port}")

        # Wait for Ollama to be ready (up to 90s)
        for attempt in range(45):
            time.sleep(2)
            try:
                req = urllib.request.Request(f"http://localhost:{port}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read()
                after_gb = _get_memory_used_gb()
                logger.info(f"  [memory] Ollama ready after {(attempt+1)*2}s. Memory: {after_gb:.0f}GB")
                return
            except Exception:
                pass

        logger.error(f"  [memory] Ollama failed to start on port {port} after 90s (attempt {retry + 1})")

    logger.error(f"  [memory] Ollama failed after {max_retries} restart attempts on port {port}!")


def _check_memory_and_restart() -> None:
    """If memory usage exceeds threshold, hard-restart Ollama."""
    used_gb = _get_memory_used_gb()
    if used_gb > MEMORY_PRESSURE_THRESHOLD_GB:
        logger.warning(
            f"  [memory] PRESSURE: {used_gb:.0f}GB used (threshold {MEMORY_PRESSURE_THRESHOLD_GB}GB). "
            f"Hard-restarting Ollama..."
        )
        _restart_ollama()


async def _process_one(
    config: str,
    q: Dict,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> Dict:
    """Generate + judge + cite one (index, config, question) tuple."""
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

    # Judge
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
    }


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

def _index_core_size(index_name: str) -> int:
    """Extract core paper count from index name like 'exp_v4_s20_n0'."""
    import re
    m = re.search(r"_s(\d+)_", index_name)
    return int(m.group(1)) if m else 50


async def run_experiment(
    indexes: List[str],
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
):
    """Run V4-5 scaling experiment (batched parallel within each config)."""
    with open(GT_FILE) as f:
        gt_data = json.load(f)
    all_questions = gt_data["questions"]

    logger.info(f"V4-5: Factorial Scaling (batched parallel)")
    logger.info(f"Indexes: {indexes}")
    logger.info(f"Configs: {configs}")

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

    # Resume — safety check: refuse to overwrite non-empty intermediate without --resume
    if not resume and INTERMEDIATE_FILE.exists():
        try:
            existing = json.loads(INTERMEDIATE_FILE.read_text())
            n_existing = len(existing.get("results", []) or existing.get("per_question_results", []))
            if n_existing > 0:
                logger.error(
                    f"Intermediate file {INTERMEDIATE_FILE.name} already has {n_existing} results. "
                    f"Use --resume to continue, or delete the file to start fresh. Aborting."
                )
                sys.exit(1)
        except (json.JSONDecodeError, OSError):
            pass  # corrupt or unreadable file, safe to overwrite

    intermediate = load_intermediate(INTERMEDIATE_FILE) if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    for idx_name in valid_indexes:
        logger.info(f"\n{'='*60}")
        logger.info(f"INDEX: {idx_name}")
        logger.info(f"{'='*60}")

        # Filter questions valid for this index
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
            pending = [q for q in questions if result_key(idx_name, config, q["id"]) not in completed]
            if not pending:
                logger.info(f"Config {config}: all done, skipping")
                continue

            batch_size = BATCH_SIZE_RLM if config in RLM_CONFIGS else BATCH_SIZE_FAST
            total_for_config = len(questions)
            done_for_config = total_for_config - len(pending)
            logger.info(f"Config {config}: {len(pending)} pending, batch_size={batch_size}")

            batch_count = 0
            for i in range(0, len(pending), batch_size):
                batch = pending[i:i + batch_size]
                batch_count += 1

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

                for q, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.error(f"Task failed for {q['id']}: {result}")
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
                        }
                    all_results.append(result)
                    completed.add(result_key(idx_name, config, q["id"]))

                save_intermediate(
                    {"results": all_results, "completed_keys": list(completed)},
                    INTERMEDIATE_FILE,
                )
                logger.info(f"  Batch saved ({len(batch)} results, total {len(all_results)})")

                # Memory safety: hard-restart Ollama periodically (disabled — embedding leak fixed)
                if RESTART_EVERY_N_BATCHES > 0 and batch_count % RESTART_EVERY_N_BATCHES == 0:
                    _restart_ollama()
                _check_memory_and_restart()

            # Hard-restart after each config only if periodic restarts are enabled
            if RESTART_EVERY_N_BATCHES > 0:
                _restart_ollama()
            logger.info(f"Completed {idx_name} / {config}")

    # ── Report ──
    _generate_report(all_results, indexes, configs, len(questions))

    if INTERMEDIATE_FILE.exists():
        INTERMEDIATE_FILE.unlink()


def _generate_report(
    all_results: List[Dict],
    indexes: List[str],
    configs: List[str],
    n_questions: int,
):
    """Generate V4-5 killer table and latency table."""
    judge_key = detect_judge_key(all_results)

    # ── Pass rate table ──
    pass_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes] + ["Trend"]
    pass_rows = []

    latency_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    latency_rows = []

    for config in configs:
        pass_row = [config]
        lat_row = [config]
        rates = []

        for idx_name in indexes:
            idx_results = [
                r for r in all_results
                if r["config"] == config and r["index_name"] == idx_name
            ]
            if not idx_results:
                pass_row.append("-")
                lat_row.append("-")
                continue

            pr = compute_pass_rate(idx_results, judge_key=judge_key)
            rates.append(pr)
            pass_row.append(format_pct(pr))

            ml = compute_median_latency(idx_results)
            lat_row.append(format_latency(ml))

        # Compute trend
        trend = _compute_trend(rates)
        pass_row.append(trend)
        pass_rows.append(pass_row)
        latency_rows.append(lat_row)

    pass_table = format_v4_table(
        pass_headers, pass_rows,
        ["l"] + ["r"] * len(indexes) + ["c"],
    )

    latency_table = format_v4_table(
        latency_headers, latency_rows,
        ["l"] + ["r"] * len(indexes),
    )

    # ── Mean correctness table ──
    corr_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    corr_rows = []

    for config in configs:
        corr_row = [config]
        for idx_name in indexes:
            idx_results = [
                r for r in all_results
                if r["config"] == config and r["index_name"] == idx_name
            ]
            if not idx_results:
                corr_row.append("-")
                continue
            ms = compute_mean_score(idx_results, judge_key=judge_key)
            corr_row.append(f"{ms:.2f}")
        corr_rows.append(corr_row)

    corr_table = format_v4_table(
        corr_headers, corr_rows,
        ["l"] + ["r"] * len(indexes),
    )

    # ── Markdown ──
    md_lines = [
        "# V4-5: Factorial Scaling",
        "",
        f"**Model**: `{GEN_MODEL}` | **Questions**: {n_questions} (answerable + unanswerable)",
        f"**Pass threshold**: correctness >= 3 (answerable), refusal_accuracy >= 3 (unanswerable)",
        "",
        "## % Pass Rate (correctness >= 3)",
        "",
        pass_table,
        "",
        "## Median Latency (seconds)",
        "",
        latency_table,
        "",
        "## Mean Correctness (0-5)",
        "",
        corr_table,
        "",
    ]

    md_content = "\n".join(md_lines)

    # ── Save ──
    output = {
        "experiment": "v4_5_scaling",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "indexes": indexes,
        "configs": configs,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "n_questions": n_questions,
        "pass_threshold": 3,
        "per_question_results": all_results,
    }

    json_path, _ = save_v4_results(output, "v4_5_scaling")
    md_path = save_v4_markdown(md_content, "v4_5_scaling")

    # Log Gemini empty response statistics
    try:
        from backend.agents.models.gemini import GeminiClient
        gemini_stats = GeminiClient.get_empty_response_stats()
        output["gemini_empty_response_stats"] = gemini_stats
        # Re-save with stats included
        save_v4_results(output, "v4_5_scaling")
        logger.info(f"Gemini empty response stats: {gemini_stats}")
    except Exception as e:
        logger.warning(f"Could not get Gemini stats: {e}")

    print(f"\n{'='*70}")
    print("V4-5 COMPLETE: Factorial Scaling")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:3000])

    # Print Gemini safety/empty response summary
    try:
        from backend.agents.models.gemini import GeminiClient
        stats = GeminiClient.get_empty_response_stats()
        print(f"\n{'='*70}")
        print("GEMINI EMPTY RESPONSE STATS")
        print(f"{'='*70}")
        print(f"  Total API calls:    {stats['total_calls']}")
        print(f"  Total blocked:      {stats['total_blocked']} ({stats['block_rate']})")
        print(f"    SAFETY:           {stats['SAFETY']}")
        print(f"    RECITATION:       {stats['RECITATION']}")
        print(f"    NO_CANDIDATES:    {stats['NO_CANDIDATES']}")
        print(f"    EMPTY_CONTENT:    {stats['EMPTY_CONTENT']}")
        print(f"    OTHER:            {stats['OTHER']}")
    except Exception:
        pass


def _compute_trend(rates: List[float]) -> str:
    """Compute a trend indicator from a sequence of pass rates."""
    if len(rates) < 2:
        return "?"

    first_half = rates[:len(rates) // 2 + 1]
    second_half = rates[len(rates) // 2:]

    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0

    diff = avg_second - avg_first

    if diff > 10:
        return "^ RISE"
    elif diff > -5:
        return "-> FLAT"
    elif diff > -20:
        return "v DECLINE"
    else:
        return "vv COLLAPSE"


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4-5: Factorial Scaling"
    )
    parser.add_argument(
        "--indexes", nargs="+", default=ALL_INDEXES,
        help=f"Indexes to test (default: {ALL_INDEXES})",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
        help="Configs to test (default: all 6)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
        help="Limit questions (smoke testing)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate results",
    )
    parser.add_argument(
        "--intermediate-file", type=str, default=None,
        help="Custom intermediate file path (for parallel runs on different indexes)",
    )
    parser.add_argument(
        "--ollama-port", type=int, default=None,
        help="Ollama port override (for parallel runs, e.g. 11435, 11436)",
    )

    args = parser.parse_args()

    # Override intermediate file if specified
    if args.intermediate_file:
        global INTERMEDIATE_FILE
        INTERMEDIATE_FILE = Path(args.intermediate_file)

    # Override Ollama URL if port specified
    if args.ollama_port:
        global OLLAMA_BASE_URL
        OLLAMA_BASE_URL = f"http://localhost:{args.ollama_port}"
        os.environ["OLLAMA_BASE_URL"] = OLLAMA_BASE_URL
        logger.info(f"Using Ollama at {OLLAMA_BASE_URL}")

    asyncio.run(run_experiment(
        indexes=args.indexes,
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
    ))


if __name__ == "__main__":
    main()
