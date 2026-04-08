#!/usr/bin/env python3
"""
V4-6: Citation Accuracy

Beyond correctness — do answers cite their sources properly?

Design:
  Index: exp_v4_s20_n0 (20 core papers, no noise)
  Questions: V4 ground truth paper-level questions (min_core <= 20)
  4 configs: single_pass, rlm_20, rlm_20_verify, verified_pass
  Dual judge: standard answer judge + citation-specific judge

Metrics: source coverage (auto), citation precision/recall/grounding (judge),
         correctness, latency

Usage:
    uv run python publication/scripts/exp_03_citations.py
    uv run python publication/scripts/exp_03_citations.py --configs single_pass verified_pass
    uv run python publication/scripts/exp_03_citations.py --resume
"""

import argparse
import asyncio
import json
import logging
import re
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
    GEN_MODEL, JUDGE_MODEL, JUDGE_OPTIONS, JUDGE_THINK,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever,
    load_ground_truth, load_intermediate, save_intermediate, result_key,
    judge_answer,
    save_v4_results, save_v4_markdown,
    compute_pass_rate, compute_median_latency, compute_mean_score,
    compute_mean_source_coverage, detect_judge_key,
    format_v4_table, format_pct, format_latency, format_score,
    V4_DIR, V4_RESULTS_DIR, V4_GROUND_TRUTH,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _evaluate_citations,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_03_citations")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GT_FILE = V4_GROUND_TRUTH
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_6_intermediate.json"
DEFAULT_INDEX = "exp_v4_s20_n0"

CONFIG_NAMES = ["single_pass", "rlm_20", "rlm_20_verify", "verified_pass"]


# ─────────────────────────────────────────────────────────────
# Citation-specific judge (same as exp4, inline for clarity)
# ─────────────────────────────────────────────────────────────

CITATION_JUDGE_PROMPT = """You are an expert scientific evaluator focusing on citation quality.

## Question
{question}

## Expected Source Files
{expected_sources}

## Generated Answer
{generated_answer}

## Task
Evaluate the citations in the generated answer:

1. **Citation Precision** (0-5): What fraction of cited sources actually appear in the expected sources?
   0=all citations wrong, 3=half correct, 5=all citations correct

2. **Citation Recall** (0-5): What fraction of expected sources are cited?
   0=no expected sources cited, 3=some cited, 5=all expected sources cited

3. **Citation Specificity** (0-5): Do citations point to specific pages/sections (not vague)?
   0=no page/section info, 3=some specific, 5=all precise with page numbers

4. **Grounding** (0-5): Is every factual claim backed by a citation?
   0=mostly uncited claims, 3=partially cited, 5=every claim has a citation

Respond in EXACTLY this JSON format:
```json
{{
  "citation_precision": <0-5>,
  "citation_recall": <0-5>,
  "citation_specificity": <0-5>,
  "grounding": <0-5>,
  "justification": "<brief explanation>"
}}
```"""


async def _judge_citations(
    question: str,
    expected_sources: List[str],
    generated_answer: str,
    router: ModelRouter,
) -> Dict[str, Any]:
    """Citation-specific judge."""
    prompt = CITATION_JUDGE_PROMPT.replace("{question}", question)
    prompt = prompt.replace("{expected_sources}", ", ".join(expected_sources) if expected_sources else "N/A")
    prompt = prompt.replace("{generated_answer}", generated_answer[:3000])

    try:
        response = await router.generate(
            model_identifier=JUDGE_MODEL,
            prompt=prompt,
            options=JUDGE_OPTIONS,
            think=JUDGE_THINK,
        )

        response_text = response.get("response", response.get("message", {}).get("content", ""))
        if not response_text:
            response_text = response.get("thinking", str(response))

        cleaned = re.sub(r'```(?:json)?\s*', '', response_text).replace('```', '')
        dims = ["citation_precision", "citation_recall", "citation_specificity", "grounding"]

        json_match = re.search(r'\{[^{}]*"citation_precision"[^{}]*\}', cleaned, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                result = {dim: int(data.get(dim, 0)) for dim in dims}
                result["justification"] = data.get("justification", "")
                return result
            except (json.JSONDecodeError, ValueError):
                pass

        scores = {}
        for dim in dims:
            match = re.search(rf'"{dim}":\s*(\d)', cleaned)
            scores[dim] = int(match.group(1)) if match else 0
        scores["justification"] = ""
        return scores

    except Exception as e:
        logger.error(f"Citation judge error: {e}")
        return {
            "citation_precision": 0, "citation_recall": 0,
            "citation_specificity": 0, "grounding": 0,
            "justification": f"Error: {e}",
        }


# ─────────────────────────────────────────────────────────────
# Config dispatch
# ─────────────────────────────────────────────────────────────

async def _run_config(
    config_name: str,
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> GenerationResult:
    """Dispatch to generator."""
    if config_name == "single_pass":
        return await _single_pass_rag(question, retriever, collection_name, router, GEN_MODEL)
    elif config_name == "rlm_20":
        return await _run_rlm(
            question, router, GEN_MODEL, user_id,
            max_turns=20, verify=False, config_name="rlm_20", index_name=index_name,
        )
    elif config_name == "rlm_20_verify":
        return await _run_rlm(
            question, router, GEN_MODEL, user_id,
            max_turns=20, verify=True, config_name="rlm_20_verify", index_name=index_name,
        )
    elif config_name == "verified_pass":
        return await _verified_pass_rag(question, retriever, collection_name, router, GEN_MODEL)
    else:
        raise ValueError(f"Unknown config: {config_name}")


# ─────────────────────────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────────────────────────

async def run_experiment(
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    index_name: str = DEFAULT_INDEX,
):
    """Run V4-6 citation accuracy experiment."""
    questions = load_ground_truth(GT_FILE, answerable_only=True)
    if max_questions:
        questions = questions[:max_questions]

    logger.info(f"V4-6: Citation Accuracy")
    logger.info(f"Questions: {len(questions)} (answerable only)")
    logger.info(f"Configs: {configs}")
    logger.info(f"Index: {index_name}")

    user_id = find_admin_user_id()
    if not check_index_exists(user_id, index_name):
        logger.error("Index check failed. Aborting.")
        sys.exit(1)

    configure_gemini_from_admin()
    router = ModelRouter()
    retriever, collection_name, _ = setup_retriever(user_id, index_name)

    intermediate = load_intermediate(INTERMEDIATE_FILE) if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total = len(configs) * len(questions)
    done = 0

    for config in configs:
        for q in questions:
            qid = q["id"]
            key = result_key(config, qid)

            if key in completed:
                done += 1
                continue

            done += 1
            logger.info(f"[{done}/{total}] {config} | {qid}: {q['question'][:50]}...")

            # Generate
            try:
                gen_result = await _run_config(
                    config_name=config,
                    question=q["question"],
                    retriever=retriever,
                    collection_name=collection_name,
                    router=router,
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

            # Standard answer judge
            answer_scores = {}
            if gen_result.answer and not gen_result.error:
                answer_scores = await judge_answer(
                    question=q["question"],
                    expected=q.get("expected_answer", ""),
                    concepts=q.get("expected_concepts", []),
                    generated=gen_result.answer,
                    router=router,
                    answerable=True,
                )

            # Citation-specific judge
            citation_judge = {}
            if gen_result.answer and not gen_result.error:
                citation_judge = await _judge_citations(
                    question=q["question"],
                    expected_sources=q.get("source_files", []),
                    generated_answer=gen_result.answer,
                    router=router,
                )

            # Automatic citation extraction
            cit_metrics = _evaluate_citations(
                gen_result.answer, q.get("source_files", [])
            )

            result_entry = {
                "question_id": qid,
                "question": q["question"],
                "category": q.get("category", "unknown"),
                "answerable": True,
                "config": config,
                "gen_model": GEN_MODEL,
                "generation": asdict(gen_result),
                "answer_scores": answer_scores,
                "citation_judge": citation_judge,
                "citation_metrics": asdict(cit_metrics),
                # Also store as judge_scores for V2 common compatibility
                "judge_scores": answer_scores,
            }

            all_results.append(result_entry)
            completed.add(key)

            save_intermediate(
                {"results": all_results, "completed_keys": list(completed)},
                INTERMEDIATE_FILE,
            )

        logger.info(f"Completed config: {config}")

    _generate_report(all_results, configs, index_name, len(questions))

    if INTERMEDIATE_FILE.exists():
        INTERMEDIATE_FILE.unlink()


def _generate_report(
    all_results: List[Dict],
    configs: List[str],
    index_name: str,
    n_questions: int,
):
    """Generate V4-6 citation report."""
    import statistics
    from collections import defaultdict

    # Aggregate per config
    agg = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        cfg = r["config"]
        # Citation judge
        for dim in ["citation_precision", "citation_recall", "citation_specificity", "grounding"]:
            val = r.get("citation_judge", {}).get(dim)
            if val is not None:
                agg[cfg][dim].append(val)
        # Answer scores
        for dim in ["correctness", "completeness", "faithfulness"]:
            val = r.get("answer_scores", {}).get(dim)
            if val is None:
                val = r.get("judge_scores", {}).get(dim)
            if val is not None:
                agg[cfg][dim].append(val)
        # Auto metrics
        cit = r.get("citation_metrics", {})
        if cit.get("source_coverage") is not None:
            agg[cfg]["source_coverage"].append(cit["source_coverage"])
        # Latency
        gen = r.get("generation", {})
        if gen.get("latency_s") and gen["latency_s"] > 0:
            agg[cfg]["latency_s"].append(gen["latency_s"])

    # Build summary
    summary = {}
    for cfg, metrics in agg.items():
        entry = {"config": cfg, "n": 0}
        for metric, values in metrics.items():
            if values:
                entry[f"{metric}_mean"] = round(statistics.mean(values), 2)
                entry[f"{metric}_std"] = round(
                    statistics.stdev(values) if len(values) > 1 else 0, 2
                )
                entry["n"] = max(entry["n"], len(values))
        summary[cfg] = entry

    # ── Table ──
    headers = [
        "Config", "Source Cov.", "Cit. Recall", "Grounding",
        "Correctness", "Med. Latency",
    ]
    rows = []
    for cfg in configs:
        if cfg not in summary:
            continue
        s = summary[cfg]

        def _fmt(dim):
            m = s.get(f"{dim}_mean", 0)
            return f"{m:.1f}"

        rows.append([
            cfg,
            f"{s.get('source_coverage_mean', 0):.0%}",
            _fmt("citation_recall"),
            _fmt("grounding"),
            _fmt("correctness"),
            f"{s.get('latency_s_mean', 0):.0f}s",
        ])

    table = format_v4_table(
        headers, rows,
        ["l", "r", "r", "r", "r", "r"],
    )

    # Full detail table
    detail_headers = [
        "Config", "N", "Cit Precision", "Cit Recall", "Specificity",
        "Grounding", "Source Cov.", "Correctness", "Latency (s)",
    ]
    detail_rows = []
    for cfg in configs:
        if cfg not in summary:
            continue
        s = summary[cfg]

        def _fmtsd(dim):
            m = s.get(f"{dim}_mean", 0)
            sd = s.get(f"{dim}_std", 0)
            return f"{m:.1f}+/-{sd:.1f}"

        detail_rows.append([
            cfg,
            str(s["n"]),
            _fmtsd("citation_precision"),
            _fmtsd("citation_recall"),
            _fmtsd("citation_specificity"),
            _fmtsd("grounding"),
            _fmtsd("source_coverage"),
            _fmtsd("correctness"),
            f"{s.get('latency_s_mean', 0):.0f}",
        ])

    detail_table = format_v4_table(
        detail_headers, detail_rows,
        ["l", "r"] + ["r"] * 7,
    )

    md_lines = [
        "# V4-6: Citation Accuracy",
        "",
        f"**Index**: `{index_name}` | **Model**: `{GEN_MODEL}`",
        f"**Questions**: {n_questions} (answerable only)",
        "",
        "## Summary",
        "",
        table,
        "",
        "## Detailed Metrics",
        "",
        detail_table,
        "",
    ]

    md_content = "\n".join(md_lines)

    # Save
    output = {
        "experiment": "v4_6_citations",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "index_name": index_name,
        "gen_model": GEN_MODEL,
        "configs": configs,
        "n_questions": n_questions,
        "summary": summary,
        "per_question_results": all_results,
    }

    json_path, _ = save_v4_results(output, "v4_6_citations")
    md_path = save_v4_markdown(md_content, "v4_6_citations")

    print(f"\n{'='*70}")
    print("V4-6 COMPLETE: Citation Accuracy")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:2000])


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4-6: Citation Accuracy"
    )
    parser.add_argument(
        "--index", default=DEFAULT_INDEX,
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=CONFIG_NAMES,
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
    )
    parser.add_argument(
        "--resume", action="store_true",
    )

    args = parser.parse_args()

    asyncio.run(run_experiment(
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
        index_name=args.index,
    ))


if __name__ == "__main__":
    main()
