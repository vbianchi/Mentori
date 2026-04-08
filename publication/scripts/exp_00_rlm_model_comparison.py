#!/usr/bin/env python3
"""
V4-0: RLM Model Comparison Experiment

Tests which model + thinking configuration performs best at following the RLM
protocol: generating Python code in REPL blocks, iterating over retrieval,
and building grounded reports with citations.

Design:
  Index:     exp_v4_s20_n0 (20 core papers, no noise)
  Questions: Stratified subset from V4 ground truth (answerable only, min_core <= 20)
  Models:    All available Ollama + Gemini API models (configurable)
  max_turns: 5 (fast diagnostic) or 10 (thorough)

Per-run instrumentation:
  - Turns used, code blocks per turn, execution success/failure
  - FINAL_VAR detection (did RLM complete properly?)
  - Report quality: sections count, total chars, citations, llm_calls
  - Wall-clock latency
  - Judge scoring: correctness, completeness, faithfulness, citation_quality

Parallelism:
  - Models run sequentially (Ollama can only serve one at a time efficiently)
  - Questions within a model run sequentially (RLM is stateful)
  - Gemini API models can run concurrently with Ollama models via --parallel-api

Output:
  - Console summary table (model × metric)
  - JSON results with per-question detail
  - Markdown report with rankings

Usage:
    # Full run with all default models
    uv run python publication/scripts/exp_00_rlm_model_comparison.py

    # Quick smoke test (2 questions, 2 models)
    uv run python publication/scripts/exp_00_rlm_model_comparison.py \
        --models "ollama::qwen3-coder:latest" "ollama::qwen3.5:9b" \
        --max-questions 2

    # Test specific model families
    uv run python publication/scripts/exp_00_rlm_model_comparison.py \
        --models "ollama::qwen3-coder:latest" "ollama::devstral-small-2:24b" \
        --max-turns 10

    # Include Gemini
    uv run python publication/scripts/exp_00_rlm_model_comparison.py \
        --models "ollama::qwen3-coder:latest" "gemini::gemini-3-flash-preview"

    # Resume after interruption
    uv run python publication/scripts/exp_00_rlm_model_comparison.py --resume

    # List available models
    uv run python publication/scripts/exp_00_rlm_model_comparison.py --list-models
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_00_rlm_model_comparison")
logger.setLevel(logging.INFO)

from exp_common import (
    JUDGE_MODEL,
    find_admin_user_id,
    check_index_exists,
    configure_gemini_from_admin,
    judge_answer,
    save_v4_results,
    save_v4_markdown,
    load_ground_truth,
    load_intermediate,
    save_intermediate,
    result_key,
    compute_pass_rate,
    compute_mean_score,
    aggregate_v4_metrics,
    detect_judge_key,
    format_v4_table,
    format_pct,
    format_score,
    V4_GROUND_TRUTH,
    V4_RESULTS_DIR,
)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

DEFAULT_INDEX = "exp_v4_s20_n0"
DEFAULT_MAX_TURNS = 5
INTERMEDIATE_FILE = V4_RESULTS_DIR / "v4_0_intermediate.json"  # default; overridden by --run-id

# Stratified question selection: pick questions covering all categories
# and difficulties for a representative sample
QUESTION_BUDGET = 15  # default number of questions per model

# ─────────────────────────────────────────────────────────────
# Model catalog — organized by family, size, and type
# ─────────────────────────────────────────────────────────────

MODEL_CATALOG = [
    # ── Qwen Code Family (code-trained) ──
    {"model": "ollama::qwen3-coder:latest", "family": "qwen-code", "size_gb": 18, "params": "~30B", "type": "code", "think": False},
    {"model": "ollama::qwen3-coder-next:q4_K_M", "family": "qwen-code", "size_gb": 51, "params": "~80B-Q4", "type": "code", "think": False},

    # ── Qwen General Family (different sizes) ──
    {"model": "ollama::qwen3.5:9b", "family": "qwen-general", "size_gb": 6.6, "params": "9B", "type": "general", "think": False},
    {"model": "ollama::qwen3.5:35b", "family": "qwen-general", "size_gb": 23, "params": "35B", "type": "general", "think": False},
    {"model": "ollama::qwen3.5:122b", "family": "qwen-general", "size_gb": 81, "params": "122B", "type": "general", "think": False},

    # ── Devstral (Mistral code family) ──
    {"model": "ollama::devstral-small-2:24b", "family": "mistral-code", "size_gb": 15, "params": "24B", "type": "code", "think": False},

    # ── GLM (Zhipu) ──
    {"model": "ollama::glm-4.7-flash:latest", "family": "glm", "size_gb": 19, "params": "~30B", "type": "general", "think": False},

    # ── Nemotron (NVIDIA) ──
    {"model": "ollama::nemotron-3-nano:30b", "family": "nemotron", "size_gb": 24, "params": "30B", "type": "general", "think": False},

    # ── DeepSeek R1 (reasoning) ──
    {"model": "ollama::deepseek-r1:70b", "family": "deepseek", "size_gb": 42, "params": "70B", "type": "reasoning", "think": False},

    # ── Gemma (Google local) ──
    {"model": "ollama::gemma3:27b", "family": "gemma", "size_gb": 17, "params": "27B", "type": "general", "think": False},

    # ── GPT-OSS (current judge baseline) ──
    {"model": "ollama::gpt-oss:20b", "family": "gpt-oss", "size_gb": 13, "params": "20B", "type": "general", "think": False},
    {"model": "ollama::gpt-oss:120b", "family": "gpt-oss", "size_gb": 65, "params": "120B", "type": "general", "think": False},

    # ── OLMo (AI2) ──
    {"model": "ollama::olmo-3:32b", "family": "olmo", "size_gb": 19, "params": "32B", "type": "general", "think": False},

    # ── Small models (baseline/negative controls) ──
    {"model": "ollama::ministral-3:14b", "family": "ministral", "size_gb": 9.1, "params": "14B", "type": "general", "think": False},
    {"model": "ollama::ministral-3:8b", "family": "ministral", "size_gb": 6.0, "params": "8B", "type": "general", "think": False},

    # ── Gemini API ──
    {"model": "gemini::gemini-3-flash-preview", "family": "gemini", "size_gb": 0, "params": "API", "type": "api", "think": False},
]

# Default subset for quick testing — one per family, varied sizes
DEFAULT_MODELS = [
    "ollama::qwen3-coder:latest",       # code-trained baseline (30B)
    "ollama::qwen3.5:9b",               # small general
    "ollama::qwen3.5:35b",              # medium general
    "ollama::qwen3.5:122b",             # large general
    "ollama::devstral-small-2:24b",     # code-trained alternative
    "ollama::glm-4.7-flash:latest",     # Chinese family
    "ollama::deepseek-r1:70b",          # reasoning model
    "ollama::gemma3:27b",               # Google local
    "ollama::gpt-oss:20b",              # judge-class model
    "ollama::gpt-oss:120b",             # large judge-class
    "gemini::gemini-3-flash-preview",   # API baseline
]


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class TurnDiagnostic:
    """Per-turn RLM diagnostic data."""
    turn: int
    code_blocks_found: int
    code_previews: List[str]
    execution_outputs: List[str]
    execution_errors: List[str]
    final_var_detected: bool
    report_sections: int
    report_chars: int
    citations: int
    llm_calls: int


@dataclass
class RLMRunResult:
    """Complete result for one model × one question."""
    model: str
    model_meta: Dict[str, Any]
    question_id: str
    question: str
    category: str
    difficulty: str
    answerable: bool
    turns_used: int
    total_time_s: float
    final_answer: str
    final_answer_length: int
    final_report_sections: int
    final_citations: int
    final_llm_calls: int
    completed: bool  # True if FINAL_VAR was reached
    code_blocks_total: int
    execution_errors_total: int
    error: Optional[str] = None
    judge_scores: Optional[Dict[str, Any]] = None
    per_turn: List[TurnDiagnostic] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Question selection — stratified sampling
# ─────────────────────────────────────────────────────────────

def select_questions(
    all_questions: List[Dict],
    max_questions: int,
    min_core: int = 20,
) -> List[Dict]:
    """Select a stratified subset of answerable questions.

    Ensures coverage across categories and difficulties.
    Filters to answerable questions with min_core <= threshold.
    """
    # Filter: answerable only, within core threshold
    eligible = [
        q for q in all_questions
        if q.get("answerable", True) and q.get("min_core", 5) <= min_core
    ]

    if len(eligible) <= max_questions:
        return eligible

    # Stratify by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for q in eligible:
        by_category[q.get("category", "unknown")].append(q)

    selected = []
    categories = sorted(by_category.keys())
    per_cat = max(1, max_questions // len(categories))
    remainder = max_questions - per_cat * len(categories)

    for cat in categories:
        pool = by_category[cat]
        # Within category, prefer diverse difficulties
        easy = [q for q in pool if q.get("difficulty") == "easy"]
        medium = [q for q in pool if q.get("difficulty") == "medium"]
        hard = [q for q in pool if q.get("difficulty") == "hard"]

        # Take balanced from each difficulty
        cat_selected = []
        for diff_pool in [easy, medium, hard]:
            take = min(len(diff_pool), max(1, per_cat // 3))
            cat_selected.extend(diff_pool[:take])

        # Fill remaining from the full category pool
        seen_ids = {q["id"] for q in cat_selected}
        for q in pool:
            if len(cat_selected) >= per_cat:
                break
            if q["id"] not in seen_ids:
                cat_selected.append(q)
                seen_ids.add(q["id"])

        selected.extend(cat_selected)

    # Fill remainder with whatever is left
    seen_ids = {q["id"] for q in selected}
    for q in eligible:
        if len(selected) >= max_questions:
            break
        if q["id"] not in seen_ids:
            selected.append(q)
            seen_ids.add(q["id"])

    return selected[:max_questions]


# ─────────────────────────────────────────────────────────────
# Instrumented RLM run
# ─────────────────────────────────────────────────────────────

async def run_rlm_instrumented(
    question: Dict,
    model_id: str,
    model_meta: Dict[str, Any],
    user_id: str,
    index_name: str,
    max_turns: int,
    think: Union[bool, str] = False,
    num_ctx: int = 16384,
) -> RLMRunResult:
    """Run RLM with per-turn instrumentation and return structured result."""
    from backend.agents.model_router import ModelRouter
    from backend.retrieval.rlm.orchestrator import RLMOrchestrator
    from backend.retrieval.rlm.context import RLMContext

    q_text = question["question"]
    q_id = question["id"]
    t0 = time.time()

    try:
        context = await RLMContext.from_index(
            index_name=index_name,
            user_id=user_id,
        )

        router = ModelRouter()
        orchestrator = RLMOrchestrator(
            model_router=router,
            model_identifier=model_id,
            max_turns=max_turns,
            verify=False,
            think=think,
            verbose=False,
            num_ctx=num_ctx,
        )

        per_turn: List[TurnDiagnostic] = []
        final_answer = ""
        completed = False

        async for event in orchestrator.run_stream(task=q_text, context=context):
            if event.type == "progress" and event.metadata and "turn" in event.metadata:
                turn_num = event.metadata["turn"]
                if turn_num > 0:
                    td = TurnDiagnostic(
                        turn=turn_num,
                        code_blocks_found=0,
                        code_previews=[],
                        execution_outputs=[],
                        execution_errors=[],
                        final_var_detected=False,
                        report_sections=len(context.report_sections),
                        report_chars=sum(len(s.content) for s in context.report_sections),
                        citations=len(context.citations),
                        llm_calls=context.llm_calls_made,
                    )
                    per_turn.append(td)

            elif event.type == "code" and per_turn:
                per_turn[-1].code_blocks_found += 1
                per_turn[-1].code_previews.append(event.content[:150])

            elif event.type == "output" and per_turn:
                output = event.content[:200]
                if "Error" in output or "Traceback" in output:
                    per_turn[-1].execution_errors.append(output)
                else:
                    per_turn[-1].execution_outputs.append(output)

            elif event.type == "final":
                final_answer = event.content
                completed = True
                if per_turn:
                    per_turn[-1].final_var_detected = True

            elif event.type == "error":
                elapsed = round(time.time() - t0, 1)
                return RLMRunResult(
                    model=model_id, model_meta=model_meta,
                    question_id=q_id, question=q_text,
                    category=question.get("category", "unknown"),
                    difficulty=question.get("difficulty", "unknown"),
                    answerable=question.get("answerable", True),
                    turns_used=len(per_turn),
                    total_time_s=elapsed,
                    final_answer="",
                    final_answer_length=0,
                    final_report_sections=len(context.report_sections),
                    final_citations=len(context.citations),
                    final_llm_calls=context.llm_calls_made,
                    completed=False,
                    code_blocks_total=sum(t.code_blocks_found for t in per_turn),
                    execution_errors_total=sum(len(t.execution_errors) for t in per_turn),
                    error=event.content,
                    per_turn=per_turn,
                )

        elapsed = round(time.time() - t0, 1)
        return RLMRunResult(
            model=model_id, model_meta=model_meta,
            question_id=q_id, question=q_text,
            category=question.get("category", "unknown"),
            difficulty=question.get("difficulty", "unknown"),
            answerable=question.get("answerable", True),
            turns_used=len(per_turn),
            total_time_s=elapsed,
            final_answer=final_answer,
            final_answer_length=len(final_answer),
            final_report_sections=len(context.report_sections),
            final_citations=len(context.citations),
            final_llm_calls=context.llm_calls_made,
            completed=completed,
            code_blocks_total=sum(t.code_blocks_found for t in per_turn),
            execution_errors_total=sum(len(t.execution_errors) for t in per_turn),
            per_turn=per_turn,
        )

    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        logger.error(f"RLM run failed ({model_id}): {e}")
        return RLMRunResult(
            model=model_id, model_meta=model_meta,
            question_id=q_id, question=q_text,
            category=question.get("category", "unknown"),
            difficulty=question.get("difficulty", "unknown"),
            answerable=question.get("answerable", True),
            turns_used=0, total_time_s=elapsed,
            final_answer="", final_answer_length=0,
            final_report_sections=0, final_citations=0,
            final_llm_calls=0, completed=False,
            code_blocks_total=0, execution_errors_total=0,
            error=str(e),
        )


# ─────────────────────────────────────────────────────────────
# Judge scoring for RLM results
# ─────────────────────────────────────────────────────────────

async def judge_rlm_result(
    result: RLMRunResult,
    question: Dict,
    router,
    judge_model: str = JUDGE_MODEL,
) -> Dict[str, Any]:
    """Judge an RLM result using the standard judge infrastructure."""
    if not result.final_answer or result.error:
        return {
            "correctness": 0, "completeness": 0,
            "faithfulness": 0, "citation_quality": 0,
            "justification": f"No answer generated. Error: {result.error or 'RLM did not complete'}",
        }

    return await judge_answer(
        question=question["question"],
        expected=question.get("expected_answer", ""),
        concepts=question.get("expected_concepts", []),
        generated=result.final_answer,
        router=router,
        answerable=question.get("answerable", True),
        judge_model=judge_model,
    )


# ─────────────────────────────────────────────────────────────
# Output formatting
# ─────────────────────────────────────────────────────────────

def print_summary_table(results: List[RLMRunResult]):
    """Print compact summary table grouped by model."""
    from collections import defaultdict

    by_model = defaultdict(list)
    for r in results:
        by_model[r.model].append(r)

    print(f"\n{'='*120}")
    print("V4-0: RLM MODEL COMPARISON RESULTS")
    print(f"{'='*120}")

    header = (
        f"{'Model':<40} | {'Params':>8} | {'Type':>7} | "
        f"{'Done':>4} | {'Turns':>5} | {'Codes':>5} | {'Errs':>4} | "
        f"{'Cites':>5} | {'Sects':>5} | {'Time':>6} | "
        f"{'Corr':>4} | {'Comp':>4} | {'Faith':>5} | {'Cite':>4} | {'Pass%':>5}"
    )
    print(header)
    print("-" * len(header))

    model_summaries = []

    for model_id in sorted(by_model.keys()):
        runs = by_model[model_id]
        meta = runs[0].model_meta

        n_completed = sum(1 for r in runs if r.completed)
        avg_turns = sum(r.turns_used for r in runs) / len(runs) if runs else 0
        avg_codes = sum(r.code_blocks_total for r in runs) / len(runs) if runs else 0
        avg_errs = sum(r.execution_errors_total for r in runs) / len(runs) if runs else 0
        avg_cites = sum(r.final_citations for r in runs) / len(runs) if runs else 0
        avg_sects = sum(r.final_report_sections for r in runs) / len(runs) if runs else 0
        avg_time = sum(r.total_time_s for r in runs) / len(runs) if runs else 0

        # Judge scores
        scored = [r for r in runs if r.judge_scores]
        avg_corr = sum(r.judge_scores.get("correctness", 0) for r in scored) / len(scored) if scored else 0
        avg_comp = sum(r.judge_scores.get("completeness", 0) for r in scored) / len(scored) if scored else 0
        avg_faith = sum(r.judge_scores.get("faithfulness", 0) for r in scored) / len(scored) if scored else 0
        avg_cite_q = sum(r.judge_scores.get("citation_quality", 0) for r in scored) / len(scored) if scored else 0
        pass_rate = sum(1 for r in scored if r.judge_scores.get("correctness", 0) >= 3) / len(scored) * 100 if scored else 0

        print(
            f"{model_id:<40} | {meta.get('params', '?'):>8} | {meta.get('type', '?'):>7} | "
            f"{n_completed:>2}/{len(runs):<1} | {avg_turns:>5.1f} | {avg_codes:>5.1f} | {avg_errs:>4.1f} | "
            f"{avg_cites:>5.1f} | {avg_sects:>5.1f} | {avg_time:>5.0f}s | "
            f"{avg_corr:>4.1f} | {avg_comp:>4.1f} | {avg_faith:>5.1f} | {avg_cite_q:>4.1f} | {pass_rate:>4.0f}%"
        )

        model_summaries.append({
            "model": model_id,
            "params": meta.get("params", "?"),
            "type": meta.get("type", "?"),
            "family": meta.get("family", "?"),
            "n_questions": len(runs),
            "n_completed": n_completed,
            "completion_rate": round(n_completed / len(runs) * 100, 1) if runs else 0,
            "avg_turns": round(avg_turns, 1),
            "avg_code_blocks": round(avg_codes, 1),
            "avg_exec_errors": round(avg_errs, 1),
            "avg_citations": round(avg_cites, 1),
            "avg_report_sections": round(avg_sects, 1),
            "avg_time_s": round(avg_time, 1),
            "avg_correctness": round(avg_corr, 2),
            "avg_completeness": round(avg_comp, 2),
            "avg_faithfulness": round(avg_faith, 2),
            "avg_citation_quality": round(avg_cite_q, 2),
            "pass_rate": round(pass_rate, 1),
        })

    print()
    return model_summaries


def generate_markdown_report(
    model_summaries: List[Dict],
    all_results: List[RLMRunResult],
    index_name: str,
    max_turns: int,
    n_questions: int,
) -> str:
    """Generate markdown report with model comparison tables."""
    lines = [
        "# V4-0: RLM Model Comparison",
        "",
        f"**Index**: `{index_name}` | **max_turns**: {max_turns} | **Questions**: {n_questions}",
        f"**Judge**: `{JUDGE_MODEL}` | **Pass threshold**: correctness >= 3",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Overall Rankings (by Pass Rate)",
        "",
    ]

    # Sort by pass rate descending
    ranked = sorted(model_summaries, key=lambda x: (-x["pass_rate"], -x["avg_correctness"]))

    headers = ["Rank", "Model", "Params", "Type", "Pass%", "Corr", "Comp", "Faith", "Cite-Q", "Done%", "Avg Time"]
    rows = []
    for i, m in enumerate(ranked, 1):
        rows.append([
            str(i),
            m["model"],
            m["params"],
            m["type"],
            f"{m['pass_rate']:.0f}%",
            f"{m['avg_correctness']:.2f}",
            f"{m['avg_completeness']:.2f}",
            f"{m['avg_faithfulness']:.2f}",
            f"{m['avg_citation_quality']:.2f}",
            f"{m['completion_rate']:.0f}%",
            f"{m['avg_time_s']:.0f}s",
        ])

    lines.append(format_v4_table(headers, rows, ["r", "l", "r", "l", "r", "r", "r", "r", "r", "r", "r"]))
    lines.append("")

    # RLM Protocol Adherence table
    lines.append("## RLM Protocol Adherence")
    lines.append("")

    headers2 = ["Model", "Params", "Completion%", "Avg Turns", "Avg Code Blocks", "Avg Exec Errors", "Avg Citations", "Avg Sections"]
    rows2 = []
    for m in ranked:
        rows2.append([
            m["model"],
            m["params"],
            f"{m['completion_rate']:.0f}%",
            f"{m['avg_turns']:.1f}",
            f"{m['avg_code_blocks']:.1f}",
            f"{m['avg_exec_errors']:.1f}",
            f"{m['avg_citations']:.1f}",
            f"{m['avg_report_sections']:.1f}",
        ])

    lines.append(format_v4_table(headers2, rows2, ["l", "r", "r", "r", "r", "r", "r", "r"]))
    lines.append("")

    # Code-trained vs General comparison
    code_models = [m for m in ranked if m["type"] == "code"]
    general_models = [m for m in ranked if m["type"] == "general"]
    api_models = [m for m in ranked if m["type"] == "api"]

    if code_models and general_models:
        lines.append("## Code-trained vs General-purpose")
        lines.append("")
        avg_code_pass = sum(m["pass_rate"] for m in code_models) / len(code_models)
        avg_general_pass = sum(m["pass_rate"] for m in general_models) / len(general_models)
        avg_code_complete = sum(m["completion_rate"] for m in code_models) / len(code_models)
        avg_general_complete = sum(m["completion_rate"] for m in general_models) / len(general_models)

        lines.append(f"| Metric | Code-trained (n={len(code_models)}) | General (n={len(general_models)}) |")
        lines.append("|---|---:|---:|")
        lines.append(f"| Avg Pass Rate | {avg_code_pass:.1f}% | {avg_general_pass:.1f}% |")
        lines.append(f"| Avg Completion | {avg_code_complete:.1f}% | {avg_general_complete:.1f}% |")
        lines.append("")

    # Per-question breakdown for top 3 models
    lines.append("## Per-Question Detail (Top 3 Models)")
    lines.append("")

    top3_models = [m["model"] for m in ranked[:3]]
    for model_id in top3_models:
        model_runs = [r for r in all_results if r.model == model_id]
        lines.append(f"### {model_id}")
        lines.append("")
        q_headers = ["Q-ID", "Category", "Done", "Turns", "Codes", "Errs", "Corr", "Time"]
        q_rows = []
        for r in model_runs:
            corr = r.judge_scores.get("correctness", "-") if r.judge_scores else "-"
            q_rows.append([
                r.question_id,
                r.category,
                "Y" if r.completed else "N",
                str(r.turns_used),
                str(r.code_blocks_total),
                str(r.execution_errors_total),
                str(corr),
                f"{r.total_time_s:.0f}s",
            ])
        lines.append(format_v4_table(q_headers, q_rows, ["l", "l", "c", "r", "r", "r", "r", "r"]))
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Model availability check
# ─────────────────────────────────────────────────────────────

async def check_model_available(model_id: str) -> bool:
    """Check if a model is available (Ollama: check list, Gemini: check API key)."""
    if model_id.startswith("gemini::"):
        return configure_gemini_from_admin()

    if model_id.startswith("ollama::"):
        try:
            import httpx
            model_name = model_id.replace("ollama::", "")
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:11434/api/tags", timeout=5)
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    names = [m.get("name", "") for m in models]
                    # Match with or without tag
                    return any(model_name in n or n.startswith(model_name.split(":")[0]) for n in names)
        except Exception:
            pass
    return False


async def list_available_models():
    """Print all models from catalog with availability status."""
    print(f"\n{'='*90}")
    print("MODEL CATALOG")
    print(f"{'='*90}")
    print(f"{'Model':<45} | {'Family':>12} | {'Params':>8} | {'Type':>7} | {'Size':>6} | {'Avail':>5}")
    print("-" * 90)

    for mc in MODEL_CATALOG:
        avail = await check_model_available(mc["model"])
        print(
            f"{mc['model']:<45} | {mc['family']:>12} | {mc['params']:>8} | "
            f"{mc['type']:>7} | {mc['size_gb']:>5.1f}G | {'YES' if avail else 'NO':>5}"
        )


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

async def run_experiment(
    model_ids: List[str],
    max_questions: int = QUESTION_BUDGET,
    max_turns: int = DEFAULT_MAX_TURNS,
    index_name: str = DEFAULT_INDEX,
    resume: bool = False,
    skip_judge: bool = False,
    judge_model: str = JUDGE_MODEL,
    run_id: Optional[str] = None,
    num_ctx: int = 16384,
):
    """Run the full model comparison experiment."""
    from backend.agents.model_router import ModelRouter

    # Determine intermediate file path (namespaced by run_id for parallel runs)
    if run_id:
        intermediate_file = V4_RESULTS_DIR / f"v4_0_intermediate_{run_id}.json"
    else:
        intermediate_file = INTERMEDIATE_FILE

    # Load ground truth
    if not V4_GROUND_TRUTH.exists():
        logger.error(f"Ground truth not found: {V4_GROUND_TRUTH}")
        sys.exit(1)

    all_questions = load_ground_truth(V4_GROUND_TRUTH, answerable_only=True)
    questions = select_questions(all_questions, max_questions)

    logger.info(f"V4-0: RLM Model Comparison")
    logger.info(f"Models: {len(model_ids)}")
    logger.info(f"Questions: {len(questions)} (stratified from {len(all_questions)} eligible)")
    logger.info(f"Index: {index_name}, max_turns: {max_turns}")
    if run_id:
        logger.info(f"Run ID: {run_id} (intermediate: {intermediate_file.name})")

    user_id = find_admin_user_id()
    if not check_index_exists(user_id, index_name):
        logger.error("Index check failed. Aborting.")
        sys.exit(1)

    configure_gemini_from_admin()

    # Build model metadata lookup
    catalog_lookup = {mc["model"]: mc for mc in MODEL_CATALOG}

    # Resume support
    intermediate = load_intermediate(intermediate_file) if resume else {"results": [], "completed_keys": []}
    all_results_raw = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    total_runs = len(model_ids) * len(questions)
    done = 0

    for model_id in model_ids:
        meta = catalog_lookup.get(model_id, {
            "model": model_id, "family": "unknown", "size_gb": 0,
            "params": "?", "type": "unknown", "think": False,
        })
        think = meta.get("think", False)

        # Check availability
        avail = await check_model_available(model_id)
        if not avail:
            logger.warning(f"Model not available, skipping: {model_id}")
            done += len(questions)
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"MODEL: {model_id} ({meta.get('params', '?')})")
        logger.info(f"{'='*60}")

        for q in questions:
            q_id = q["id"]
            key = result_key(model_id, q_id)

            if key in completed:
                done += 1
                continue

            done += 1
            logger.info(
                f"[{done}/{total_runs}] {model_id} | {q_id} ({q.get('category', '?')}): "
                f"{q['question'][:55]}..."
            )

            # Run RLM
            result = await run_rlm_instrumented(
                question=q,
                model_id=model_id,
                model_meta=meta,
                user_id=user_id,
                index_name=index_name,
                max_turns=max_turns,
                think=think,
                num_ctx=num_ctx,
            )

            status = "DONE" if result.completed else ("ERR" if result.error else "MAX")
            logger.info(
                f"  -> {status} | {result.turns_used} turns, "
                f"{result.code_blocks_total} codes, {result.final_citations} cites, "
                f"{result.total_time_s:.0f}s"
            )

            # Judge
            if not skip_judge:
                router = ModelRouter()
                result.judge_scores = await judge_rlm_result(
                    result, q, router, judge_model=judge_model,
                )
                corr = result.judge_scores.get("correctness", "?")
                logger.info(f"  -> Judge: correctness={corr}")

            # Save intermediate
            all_results_raw.append(asdict(result))
            completed.add(key)
            save_intermediate(
                {"results": all_results_raw, "completed_keys": list(completed)},
                intermediate_file,
            )

    # Reconstruct typed results for reporting
    all_results = []
    for raw in all_results_raw:
        r = RLMRunResult(
            model=raw["model"],
            model_meta=raw["model_meta"],
            question_id=raw["question_id"],
            question=raw["question"],
            category=raw["category"],
            difficulty=raw["difficulty"],
            answerable=raw["answerable"],
            turns_used=raw["turns_used"],
            total_time_s=raw["total_time_s"],
            final_answer=raw.get("final_answer", ""),
            final_answer_length=raw["final_answer_length"],
            final_report_sections=raw["final_report_sections"],
            final_citations=raw["final_citations"],
            final_llm_calls=raw["final_llm_calls"],
            completed=raw["completed"],
            code_blocks_total=raw["code_blocks_total"],
            execution_errors_total=raw["execution_errors_total"],
            error=raw.get("error"),
            judge_scores=raw.get("judge_scores"),
        )
        all_results.append(r)

    # Generate reports
    model_summaries = print_summary_table(all_results)

    md_report = generate_markdown_report(
        model_summaries, all_results,
        index_name, max_turns, len(questions),
    )

    # Save
    output_data = {
        "experiment": "v4_0_rlm_model_comparison",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "index_name": index_name,
        "max_turns": max_turns,
        "judge_model": judge_model,
        "n_questions": len(questions),
        "n_models": len(model_ids),
        "model_ids": model_ids,
        "question_ids": [q["id"] for q in questions],
        "model_summaries": model_summaries,
        "per_question_results": all_results_raw,
    }

    json_path, _ = save_v4_results(output_data, "v4_0_rlm_models")
    md_path = save_v4_markdown(md_report, "v4_0_rlm_models")

    print(f"\n{'='*70}")
    print("V4-0 COMPLETE: RLM Model Comparison")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_report[:4000])

    # Cleanup intermediate
    if intermediate_file.exists():
        intermediate_file.unlink()
        logger.info("Cleaned up intermediate file")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4-0: RLM Model Comparison Experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full run with default models
  %(prog)s

  # Quick smoke test
  %(prog)s --models "ollama::qwen3-coder:latest" "ollama::qwen3.5:9b" --max-questions 2

  # All models, thorough
  %(prog)s --all-models --max-turns 10

  # List available models
  %(prog)s --list-models
        """,
    )
    parser.add_argument(
        "--models", nargs="+", default=None,
        help="Model identifiers to test (default: DEFAULT_MODELS subset)",
    )
    parser.add_argument(
        "--all-models", action="store_true",
        help="Test all models in the catalog",
    )
    parser.add_argument(
        "--index", default=DEFAULT_INDEX,
        help=f"Index name (default: {DEFAULT_INDEX})",
    )
    parser.add_argument(
        "--max-questions", type=int, default=QUESTION_BUDGET,
        help=f"Max questions per model (default: {QUESTION_BUDGET})",
    )
    parser.add_argument(
        "--max-turns", type=int, default=DEFAULT_MAX_TURNS,
        help=f"Max RLM turns (default: {DEFAULT_MAX_TURNS})",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from intermediate results",
    )
    parser.add_argument(
        "--skip-judge", action="store_true",
        help="Skip judge scoring (faster, diagnostic only)",
    )
    parser.add_argument(
        "--judge-model", default=JUDGE_MODEL,
        help=f"Judge model (default: {JUDGE_MODEL})",
    )
    parser.add_argument(
        "--run-id", default=None,
        help="Run ID for parallel execution (namespaces intermediate file)",
    )
    parser.add_argument(
        "--num-ctx", type=int, default=16384,
        help="Context window size for Ollama models (default: 16384)",
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List all models in catalog with availability status",
    )

    args = parser.parse_args()

    if args.list_models:
        asyncio.run(list_available_models())
        return

    if args.all_models:
        model_ids = [mc["model"] for mc in MODEL_CATALOG]
    elif args.models:
        model_ids = args.models
    else:
        model_ids = DEFAULT_MODELS

    asyncio.run(run_experiment(
        model_ids=model_ids,
        max_questions=args.max_questions,
        max_turns=args.max_turns,
        index_name=args.index,
        resume=args.resume,
        skip_judge=args.skip_judge,
        judge_model=args.judge_model,
        run_id=args.run_id,
        num_ctx=args.num_ctx,
    ))


if __name__ == "__main__":
    main()
