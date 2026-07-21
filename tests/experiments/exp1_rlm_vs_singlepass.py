"""
Experiment 1: RLM vs Single-Pass RAG for Scientific Document QA

Core novelty experiment: tests whether code-mediated iterative retrieval (RLM)
outperforms standard single-pass RAG for scientific document QA.

Holds retrieval constant (BGE-M3 + RRF, the best from Exp 2+3) and compares
answer generation strategies.

Design:
  1 generation model (qwen3-coder)
  × 5 answer configs (single_pass, multi_hop, rlm@5, rlm@10, rlm@20)
  × 37 ground truth questions (20 answerable + 10 unanswerable + 7 OOD)
  = 185 generation runs + judge calls

Usage:
    # Full experiment
    uv run python tests/experiments/exp1_rlm_vs_singlepass.py --index exp_s20

    # Quick smoke test
    uv run python tests/experiments/exp1_rlm_vs_singlepass.py \\
        --configs single_pass --max-questions 3

    # Specific configs
    uv run python tests/experiments/exp1_rlm_vs_singlepass.py --configs single_pass rlm_20

    # Resume from saved intermediate results
    uv run python tests/experiments/exp1_rlm_vs_singlepass.py --resume
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter
from backend.retrieval.retriever import SimpleRetriever
from backend.retrieval.rlm.orchestrator import RLMOrchestrator
from backend.retrieval.rlm.context import RLMContext
from backend.retrieval.pipeline import ScientificRAGPipeline, PipelineConfig

from tests.experiments.exp_common import (
    JUDGE_MODEL, GEN_MODEL, JUDGE_OPTIONS, RESULTS_DIR as COMMON_RESULTS_DIR,
    find_admin_user_id, check_index_exists, configure_gemini_from_admin,
    setup_retriever, load_ground_truth, load_intermediate, save_intermediate,
    result_key, judge_answer as common_judge_answer, save_final_results,
)

# Import V4 context/output constants (used by V4 experiment callers)
try:
    from tests.experiments_v4.exp_common import NUM_CTX, NUM_PREDICT
except ImportError:
    NUM_CTX = 24576
    NUM_PREDICT = 8192

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp1_rlm_vs_singlepass")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────

EXPERIMENTS_DIR = PROJECT_ROOT / "tests" / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
GT_FILE = EXPERIMENTS_DIR / "ground_truth_exp1.json"
INTERMEDIATE_FILE = RESULTS_DIR / "exp1_intermediate.json"

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

DEFAULT_INDEX = "exp_s20"

GEN_MODELS = [
    GEN_MODEL,
]

JUDGE_MODELS = [
    JUDGE_MODEL,
]

CONFIG_NAMES = [
    "single_pass",
    "multi_hop",
    "rlm_5",
    "rlm_10",
    "rlm_20",
    "verified_pass",
]


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class GenerationResult:
    """Result from a single answer generation run."""
    answer: str
    latency_s: float
    llm_calls: int
    tokens_used: int
    retrieved_passages: int
    config: str
    gen_model: str
    error: Optional[str] = None


@dataclass
class JudgeScores:
    """Scores from a single judge evaluation."""
    correctness: int  # 0-5
    completeness: int  # 0-5
    faithfulness: int  # 0-5
    citation_quality: int  # 0-5
    justification: str = ""
    judge_model: str = ""


@dataclass
class CitationMetrics:
    """Citation extraction metrics."""
    total_citations: int = 0
    unique_sources: int = 0
    citation_density: float = 0.0  # citations per 100 words
    source_coverage: float = 0.0  # fraction of expected sources cited


@dataclass
class QuestionResult:
    """Full result for one question under one config."""
    question_id: str
    question: str
    config: str
    gen_model: str
    generation: Optional[GenerationResult] = None
    judge_scores: Dict[str, JudgeScores] = field(default_factory=dict)
    citation_metrics: Optional[CitationMetrics] = None



# Helper functions now imported from exp_common:
# find_admin_user_id, check_index_exists, configure_gemini_from_admin,
# setup_retriever, load_ground_truth, judge_answer, etc.


# ─────────────────────────────────────────────────────────────
# A. Single-Pass RAG Generator
# ─────────────────────────────────────────────────────────────

SINGLE_PASS_PROMPT = """You are a scientific research assistant. Based ONLY on the following retrieved passages, answer the question. If the passages don't contain enough information, say so clearly.

Cite sources using the format [source_file:page_number] for every factual claim.

## Retrieved Passages

{passages}

## Question

{question}

## Answer
"""


async def _single_pass_rag(
    question: str,
    retriever: SimpleRetriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
) -> GenerationResult:
    """
    Single-pass RAG: retrieve top-10 → LLM generates answer.

    This is the baseline — one retrieval step, one generation step.
    """
    t0 = time.time()

    # Retrieve top-10 chunks
    results = retriever.retrieve(
        query=question,
        top_k=10,
        collection_name=collection_name,
    )

    # Format passages
    passages = []
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("file_name", "unknown")
        page = r["metadata"].get("page", "?")
        text = r["text"][:800]  # Truncate very long chunks
        passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")

    passages_text = "\n\n".join(passages)
    prompt = SINGLE_PASS_PROMPT.replace("{passages}", passages_text).replace("{question}", question)

    # Generate answer
    response = await router.generate(
        model_identifier=gen_model,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
    )

    answer = response.get("response", response.get("message", {}).get("content", ""))
    if not answer:
        answer = str(response)

    latency = time.time() - t0

    return GenerationResult(
        answer=answer,
        latency_s=latency,
        llm_calls=1,
        tokens_used=len(prompt.split()) + len(answer.split()),  # rough estimate
        retrieved_passages=len(results),
        config="single_pass",
        gen_model=gen_model,
    )


# ─────────────────────────────────────────────────────────────
# B. Multi-Hop RAG Generator (RLM without code)
# ─────────────────────────────────────────────────────────────

MULTI_HOP_SYSTEM = """You are a scientific research assistant performing iterative document analysis.

You will be shown retrieved passages. After reviewing them, you must either:
1. Output FINAL ANSWER: <your complete answer> if you have enough information
2. Output SEARCH: <refined query> to search for more specific information

Always cite sources as [source_file:page_number].
Be thorough — gather enough evidence before answering."""

MULTI_HOP_USER = """## Question
{question}

## Retrieved Passages (Search #{search_num})
{passages}

## Previous findings
{history}

Review these passages and either provide your FINAL ANSWER or request another SEARCH."""


async def _multi_hop_rag(
    question: str,
    retriever: SimpleRetriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
    max_turns: int = 5,
) -> GenerationResult:
    """
    Multi-hop RAG: iterative retrieve-refine loop with natural language queries only.

    This is the "RLM without code" ablation — same iterative retrieval,
    but the LLM can only request searches in natural language (no programmatic
    filtering, slicing, regex).
    """
    t0 = time.time()
    current_query = question
    history_parts = []
    total_llm_calls = 0
    total_passages = 0
    all_passages_seen = []

    for turn in range(max_turns):
        # Retrieve
        results = retriever.retrieve(
            query=current_query,
            top_k=10,
            collection_name=collection_name,
        )
        total_passages += len(results)

        # Format passages
        passages = []
        for i, r in enumerate(results, 1):
            source = r["metadata"].get("file_name", "unknown")
            page = r["metadata"].get("page", "?")
            text = r["text"][:800]
            passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")
            all_passages_seen.append(f"{source}:p{page}")

        passages_text = "\n\n".join(passages)
        history_text = "\n".join(history_parts) if history_parts else "None yet."

        prompt = MULTI_HOP_USER.replace("{question}", question)
        prompt = prompt.replace("{search_num}", str(turn + 1))
        prompt = prompt.replace("{passages}", passages_text)
        prompt = prompt.replace("{history}", history_text)

        # Call LLM
        response = await router.chat(
            model_identifier=gen_model,
            messages=[
                {"role": "system", "content": MULTI_HOP_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
            think=False,
        )
        total_llm_calls += 1

        answer_text = response.get("message", {}).get("content", "")
        if not answer_text:
            answer_text = response.get("response", str(response))

        # Check for FINAL ANSWER
        final_match = re.search(r"FINAL\s*ANSWER:\s*(.*)", answer_text, re.DOTALL | re.IGNORECASE)
        if final_match:
            answer = final_match.group(1).strip()
            latency = time.time() - t0
            return GenerationResult(
                answer=answer,
                latency_s=latency,
                llm_calls=total_llm_calls,
                tokens_used=total_llm_calls * 1500,  # rough estimate
                retrieved_passages=total_passages,
                config="multi_hop",
                gen_model=gen_model,
            )

        # Check for SEARCH: <query>
        search_match = re.search(r"SEARCH:\s*(.+?)(?:\n|$)", answer_text, re.IGNORECASE)
        if search_match:
            current_query = search_match.group(1).strip()
            history_parts.append(
                f"Turn {turn + 1}: Searched '{current_query}' — "
                f"found {len(results)} passages"
            )
        else:
            # LLM didn't follow protocol — treat entire response as answer
            latency = time.time() - t0
            return GenerationResult(
                answer=answer_text,
                latency_s=latency,
                llm_calls=total_llm_calls,
                tokens_used=total_llm_calls * 1500,
                retrieved_passages=total_passages,
                config="multi_hop",
                gen_model=gen_model,
            )

    # Max turns reached — force answer from last response
    latency = time.time() - t0
    return GenerationResult(
        answer=f"[Max turns reached] {answer_text}",
        latency_s=latency,
        llm_calls=total_llm_calls,
        tokens_used=total_llm_calls * 1500,
        retrieved_passages=total_passages,
        config="multi_hop",
        gen_model=gen_model,
    )


# ─────────────────────────────────────────────────────────────
# C. RLM Runner
# ─────────────────────────────────────────────────────────────

async def _run_rlm(
    question: str,
    router: ModelRouter,
    gen_model: str,
    user_id: str,
    max_turns: int = 20,
    verify: bool = False,
    think=False,
    config_name: str = "rlm_20",
    index_name: str = DEFAULT_INDEX,
) -> GenerationResult:
    """
    Wrap existing RLM infrastructure for programmatic use.
    """
    t0 = time.time()

    try:
        context = await RLMContext.from_index(
            index_name=index_name,
            user_id=user_id,
        )

        orchestrator = RLMOrchestrator(
            model_router=router,
            model_identifier=gen_model,
            max_turns=max_turns,
            verify=verify,
            think=think,
        )

        result = await orchestrator.run(task=question, context=context)

        latency = time.time() - t0

        return GenerationResult(
            answer=result,
            latency_s=latency,
            llm_calls=context.llm_calls_made,
            tokens_used=context.total_tokens_used,
            retrieved_passages=len(context.citations),
            config=config_name,
            gen_model=gen_model,
        )

    except Exception as e:
        latency = time.time() - t0
        logger.error(f"RLM error ({config_name}): {e}")
        return GenerationResult(
            answer="",
            latency_s=latency,
            llm_calls=0,
            tokens_used=0,
            retrieved_passages=0,
            config=config_name,
            gen_model=gen_model,
            error=str(e),
        )


# ─────────────────────────────────────────────────────────────
# D. Verified-Pass RAG Generator
# ─────────────────────────────────────────────────────────────

async def _verified_pass_rag(
    question: str,
    retriever: SimpleRetriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
) -> GenerationResult:
    """
    Verified-pass RAG: wide retrieval → rerank → LLM verification → generate.

    Uses ScientificRAGPipeline with the verified() config:
    dense(100) → RRF hybrid(50) → cross-encoder rerank(15) → LLM verify → generate.
    """
    t0 = time.time()

    config = PipelineConfig.verified()
    config.gen_model = gen_model

    pipeline = ScientificRAGPipeline(
        retriever=retriever,
        collection_name=collection_name,
        model_router=router,
        config=config,
    )

    result = await pipeline.answer(question)
    latency = time.time() - t0

    # Count LLM calls: 1 for verification + 1 for generation
    llm_calls = 2 if config.use_verification else 1

    return GenerationResult(
        answer=result.answer,
        latency_s=latency,
        llm_calls=llm_calls,
        tokens_used=0,  # Not tracked at this level
        retrieved_passages=result.chunks_used,
        config="verified_pass",
        gen_model=gen_model,
        error=result.error,
    )


# ─────────────────────────────────────────────────────────────
# E. LLM-as-Judge Evaluator
# ─────────────────────────────────────────────────────────────

JUDGE_PROMPT = """You are an expert scientific evaluator. Score the following generated answer against the expected answer.

## Question
{question}

## Expected Answer
{expected_answer}

## Expected Concepts
{expected_concepts}

## Generated Answer
{generated_answer}

## Scoring (0-5 each)

Score each dimension and provide brief justification:

1. **Correctness** (0-5): Does the answer match the expected answer factually?
   0=completely wrong, 3=partially correct, 5=fully correct

2. **Completeness** (0-5): Does it cover all expected concepts?
   0=none covered, 3=most covered, 5=all covered with depth

3. **Faithfulness** (0-5): Are all claims grounded in source material (no hallucinations)?
   0=mostly hallucinated, 3=some unsupported claims, 5=all claims supported

4. **Citation Quality** (0-5): Are citations present, accurate, and properly formatted?
   0=no citations, 3=some citations, 5=comprehensive accurate citations

Respond in EXACTLY this JSON format:
```json
{{
  "correctness": <0-5>,
  "completeness": <0-5>,
  "faithfulness": <0-5>,
  "citation_quality": <0-5>,
  "justification": "<brief explanation>"
}}
```"""


async def _judge_answer(
    question: str,
    expected_answer: str,
    expected_concepts: List[str],
    generated_answer: str,
    router: ModelRouter,
    judge_model: str,
) -> JudgeScores:
    """
    LLM-as-judge evaluation with structured scoring.
    """
    concepts_text = ", ".join(expected_concepts) if expected_concepts else "N/A"

    prompt = JUDGE_PROMPT.replace("{question}", question)
    prompt = prompt.replace("{expected_answer}", expected_answer)
    prompt = prompt.replace("{expected_concepts}", concepts_text)
    prompt = prompt.replace("{generated_answer}", generated_answer[:3000])  # Truncate long answers

    try:
        response = await router.generate(
            model_identifier=judge_model,
            prompt=prompt,
            options={"temperature": 0, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
        )

        response_text = response.get("response", response.get("message", {}).get("content", ""))
        # Some models (e.g. gpt-oss:20b) use built-in thinking — check thinking field too
        if not response_text:
            thinking_text = response.get("thinking", "")
            if thinking_text:
                response_text = thinking_text
            else:
                response_text = str(response)

        # Parse JSON from response
        scores = _parse_judge_scores(response_text)
        scores.judge_model = judge_model
        return scores

    except Exception as e:
        logger.error(f"Judge error ({judge_model}): {e}")
        return JudgeScores(
            correctness=0, completeness=0, faithfulness=0, citation_quality=0,
            justification=f"Judge error: {e}",
            judge_model=judge_model,
        )


def _parse_judge_scores(text: str) -> JudgeScores:
    """Parse judge scores from LLM response, handling various formats."""
    # Strip markdown code fences if present
    cleaned = re.sub(r'```(?:json)?\s*', '', text)
    cleaned = cleaned.replace('```', '')

    # Try JSON extraction
    json_match = re.search(r'\{[^{}]*"correctness"[^{}]*\}', cleaned, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return JudgeScores(
                correctness=int(data.get("correctness", 0)),
                completeness=int(data.get("completeness", 0)),
                faithfulness=int(data.get("faithfulness", 0)),
                citation_quality=int(data.get("citation_quality", 0)),
                justification=data.get("justification", ""),
            )
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: regex extraction
    scores = {}
    for dim in ["correctness", "completeness", "faithfulness", "citation_quality"]:
        match = re.search(rf'"{dim}":\s*(\d)', cleaned)
        if not match:
            match = re.search(rf'\*?\*?{dim}\*?\*?[:\s]+(\d)', cleaned, re.IGNORECASE)
        scores[dim] = int(match.group(1)) if match else 0

    justification_match = re.search(r'"justification":\s*"([^"]*)"', cleaned)
    justification = justification_match.group(1) if justification_match else ""

    return JudgeScores(
        correctness=scores.get("correctness", 0),
        completeness=scores.get("completeness", 0),
        faithfulness=scores.get("faithfulness", 0),
        citation_quality=scores.get("citation_quality", 0),
        justification=justification,
    )


# ─────────────────────────────────────────────────────────────
# E. Citation Evaluator
# ─────────────────────────────────────────────────────────────

def _evaluate_citations(
    answer: str,
    expected_sources: List[str],
) -> CitationMetrics:
    """
    Extract and evaluate citations from generated answers.

    Handles both [source:page] and RLM-style [N] references.
    """
    # Pattern 1: [source_file:page] or [source_file:pN]
    inline_citations = re.findall(
        r'\[([^\]]+\.pdf):(?:p(?:age)?)?(\d+)\]', answer, re.IGNORECASE
    )

    # Pattern 2: Numbered [N] references (RLM format)
    numbered_refs = re.findall(r'\[(\d+)\]', answer)

    # Pattern 3: Source lines in reference section
    source_lines = re.findall(
        r'(\S+\.pdf),?\s*page\s*(\d+)', answer, re.IGNORECASE
    )

    # Collect unique sources
    sources_found = set()
    total_citations = 0

    for source, page in inline_citations:
        sources_found.add(source)
        total_citations += 1

    for source, page in source_lines:
        sources_found.add(source)

    total_citations += len(numbered_refs)

    # Word count for density
    word_count = len(answer.split())
    density = (total_citations / max(word_count, 1)) * 100

    # Source coverage: fraction of expected sources that were cited
    if expected_sources:
        covered = sum(
            1 for s in expected_sources
            if any(s.lower() in found.lower() for found in sources_found)
        )
        coverage = covered / len(expected_sources)
    else:
        coverage = 0.0

    return CitationMetrics(
        total_citations=total_citations,
        unique_sources=len(sources_found),
        citation_density=round(density, 2),
        source_coverage=round(coverage, 2),
    )


# ─────────────────────────────────────────────────────────────
# Config dispatch
# ─────────────────────────────────────────────────────────────

async def _run_config(
    config_name: str,
    question: str,
    retriever: SimpleRetriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
    user_id: str,
    index_name: str = DEFAULT_INDEX,
) -> GenerationResult:
    """Dispatch to the right generator based on config name."""
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
    elif config_name == "rlm_20_verify":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=20, verify=True, config_name="rlm_20_verify", index_name=index_name)
    elif config_name == "verified_pass":
        return await _verified_pass_rag(question, retriever, collection_name, router, gen_model)
    else:
        raise ValueError(f"Unknown config: {config_name}")


# ─────────────────────────────────────────────────────────────
# Intermediate results / resume
# ─────────────────────────────────────────────────────────────

def _load_intermediate() -> Dict[str, Any]:
    """Load intermediate results if available."""
    if INTERMEDIATE_FILE.exists():
        with open(INTERMEDIATE_FILE) as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data.get('results', []))} intermediate results")
        return data
    return {"results": [], "completed_keys": []}


def _save_intermediate(data: Dict[str, Any]):
    """Save intermediate results."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INTERMEDIATE_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _result_key(gen_model: str, config: str, question_id: str) -> str:
    """Create a unique key for deduplication."""
    return f"{gen_model}|{config}|{question_id}"


# ─────────────────────────────────────────────────────────────
# Aggregation & reporting
# ─────────────────────────────────────────────────────────────

def _aggregate_results(results: List[Dict]) -> Dict[str, Any]:
    """Compute aggregate metrics per config per model."""
    from collections import defaultdict
    import statistics

    aggregates = defaultdict(lambda: defaultdict(list))

    for r in results:
        key = (r["gen_model"], r["config"])

        if r.get("generation", {}).get("error"):
            continue

        # Collect scores per judge
        for judge_name, scores in r.get("judge_scores", {}).items():
            for dim in ["correctness", "completeness", "faithfulness", "citation_quality"]:
                aggregates[key][f"{dim}_{judge_name}"].append(scores.get(dim, 0))

        # Latency & cost
        gen = r.get("generation", {})
        if gen.get("latency_s"):
            aggregates[key]["latency_s"].append(gen["latency_s"])
        if gen.get("llm_calls"):
            aggregates[key]["llm_calls"].append(gen["llm_calls"])
        if gen.get("tokens_used"):
            aggregates[key]["tokens_used"].append(gen["tokens_used"])

        # Citations
        cit = r.get("citation_metrics", {})
        if cit:
            aggregates[key]["citation_count"].append(cit.get("total_citations", 0))
            aggregates[key]["source_coverage"].append(cit.get("source_coverage", 0))

    # Compute mean ± std
    summary = {}
    for (gen_model, config), metrics in aggregates.items():
        entry = {"gen_model": gen_model, "config": config, "n_questions": 0}
        for metric_name, values in metrics.items():
            if values:
                entry[f"{metric_name}_mean"] = round(statistics.mean(values), 2)
                entry[f"{metric_name}_std"] = round(
                    statistics.stdev(values) if len(values) > 1 else 0, 2
                )
                entry["n_questions"] = max(entry["n_questions"], len(values))
        summary[f"{gen_model}|{config}"] = entry

    return summary


def _generate_markdown_report(
    results: List[Dict],
    summary: Dict[str, Any],
) -> str:
    """Generate a markdown summary table."""
    lines = [
        "# Experiment 1: RLM vs Single-Pass RAG — Results",
        "",
        f"Generated: {datetime.now().isoformat()}",
        f"Total evaluations: {len(results)}",
        "",
    ]

    # Group by gen_model
    gen_models = sorted(set(r["gen_model"] for r in results))

    for gen_model in gen_models:
        lines.append(f"## Generation Model: `{gen_model}`")
        lines.append("")
        lines.append(
            "| Config | N | Correctness | Completeness | Faithfulness | Citation Q. | Latency (s) | LLM Calls |"
        )
        lines.append(
            "|--------|---|-------------|--------------|--------------|-------------|-------------|-----------|"
        )

        for config in CONFIG_NAMES:
            key = f"{gen_model}|{config}"
            if key not in summary:
                continue
            s = summary[key]

            # Use first available judge for the main table
            judge_key = None
            for jm in JUDGE_MODELS:
                short = jm.split("::")[-1].replace(":", "_").replace(".", "_")
                if f"correctness_{short}_mean" in s:
                    judge_key = short
                    break
            if not judge_key:
                # Fallback: find any judge key
                for k in s:
                    m = re.match(r"correctness_(.+)_mean", k)
                    if m:
                        judge_key = m.group(1)
                        break
            if not judge_key:
                continue

            def _fmt(dim):
                mean = s.get(f"{dim}_{judge_key}_mean", 0)
                std = s.get(f"{dim}_{judge_key}_std", 0)
                return f"{mean:.1f}±{std:.1f}"

            latency = f"{s.get('latency_s_mean', 0):.0f}±{s.get('latency_s_std', 0):.0f}"
            llm_calls = f"{s.get('llm_calls_mean', 0):.0f}"

            lines.append(
                f"| {config:16s} | {s['n_questions']:2d} | "
                f"{_fmt('correctness'):11s} | {_fmt('completeness'):12s} | "
                f"{_fmt('faithfulness'):12s} | {_fmt('citation_quality'):11s} | "
                f"{latency:11s} | {llm_calls:9s} |"
            )

        lines.append("")

    # Per-category breakdown
    lines.append("## Per-Category Breakdown")
    lines.append("")
    categories = sorted(set(r.get("category", "unknown") for r in results))
    for cat in categories:
        cat_results = [r for r in results if r.get("category") == cat]
        if not cat_results:
            continue

        lines.append(f"### {cat}")
        lines.append(f"Questions: {len(set(r['question_id'] for r in cat_results))}")
        lines.append("")

        cat_summary = _aggregate_results(cat_results)
        for key, s in sorted(cat_summary.items()):
            judge_key = None
            for k in s:
                m = re.match(r"correctness_(.+)_mean", k)
                if m:
                    judge_key = m.group(1)
                    break
            if not judge_key:
                continue
            corr = s.get(f"correctness_{judge_key}_mean", 0)
            lines.append(f"- `{s['config']}` ({s['gen_model']}): correctness={corr:.1f}")

        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

async def run_experiment(
    gen_models: List[str],
    configs: List[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    index_name: str = DEFAULT_INDEX,
):
    """Run the full experiment."""

    # Load ground truth
    if not GT_FILE.exists():
        logger.error(f"Ground truth file not found: {GT_FILE}")
        sys.exit(1)

    with open(GT_FILE) as f:
        gt_data = json.load(f)

    questions = gt_data["questions"]
    if max_questions:
        questions = questions[:max_questions]

    n_answerable = sum(1 for q in questions if q.get("answerable", True))
    n_unanswerable = len(questions) - n_answerable
    logger.info(f"Loaded {len(questions)} questions ({n_answerable} answerable, {n_unanswerable} unanswerable/OOD)")
    logger.info(f"Gen models: {gen_models}")
    logger.info(f"Configs: {configs}")
    logger.info(f"Index: {index_name}")

    # Setup
    user_id = find_admin_user_id()
    if not check_index_exists(user_id, index_name):
        logger.error("Index check failed. Aborting.")
        sys.exit(1)

    # Configure Gemini API key from admin user settings
    uses_gemini = any("gemini" in m for m in gen_models + JUDGE_MODELS)
    if uses_gemini:
        if not configure_gemini_from_admin():
            logger.warning(
                "Gemini models requested but no API key found. "
                "Gemini calls will fail. Set key in admin Settings > API Keys."
            )

    router = ModelRouter()

    # Initialize retriever
    retriever, collection_name, embedding_model = setup_retriever(user_id, index_name)

    # Load intermediate results if resuming
    intermediate = _load_intermediate() if resume else {"results": [], "completed_keys": []}
    all_results = intermediate["results"]
    completed = set(intermediate["completed_keys"])

    # Experiment loop
    total = len(gen_models) * len(configs) * len(questions)
    done = 0

    for gen_model in gen_models:
        for config in configs:
            for q in questions:
                qid = q["id"]
                key = _result_key(gen_model, config, qid)

                if key in completed:
                    done += 1
                    continue

                done += 1
                logger.info(
                    f"[{done}/{total}] {gen_model} | {config} | {qid}: "
                    f"{q['question'][:60]}..."
                )

                # ── Generate answer ──
                is_answerable = q.get("answerable", True)
                try:
                    gen_result = await _run_config(
                        config_name=config,
                        question=q["question"],
                        retriever=retriever,
                        collection_name=collection_name,
                        router=router,
                        gen_model=gen_model,
                        user_id=user_id,
                        index_name=index_name,
                    )
                except Exception as e:
                    logger.error(f"Generation failed: {e}")
                    gen_result = GenerationResult(
                        answer="", latency_s=0, llm_calls=0, tokens_used=0,
                        retrieved_passages=0, config=config, gen_model=gen_model,
                        error=str(e),
                    )

                # ── Judge with each judge model ──
                judge_scores = {}
                if gen_result.answer and not gen_result.error:
                    for judge_model in JUDGE_MODELS:
                        judge_short = judge_model.split("::")[-1].replace(":", "_").replace(".", "_")
                        try:
                            scores = await common_judge_answer(
                                question=q["question"],
                                expected=q.get("expected_answer", ""),
                                concepts=q.get("expected_concepts", []),
                                generated=gen_result.answer,
                                router=router,
                                answerable=is_answerable,
                                judge_model=judge_model,
                            )
                            scores["judge_model"] = judge_model
                            judge_scores[judge_short] = scores
                        except Exception as e:
                            logger.error(f"Judge error ({judge_model}): {e}")
                            if is_answerable:
                                judge_scores[judge_short] = {
                                    "correctness": 0, "completeness": 0,
                                    "faithfulness": 0, "citation_quality": 0,
                                    "justification": f"Error: {e}",
                                    "judge_model": judge_model,
                                }
                            else:
                                judge_scores[judge_short] = {
                                    "refusal_accuracy": 0, "hallucination_avoidance": 0,
                                    "explanation_quality": 0,
                                    "justification": f"Error: {e}",
                                    "judge_model": judge_model,
                                }

                # ── Citation evaluation ──
                expected_sources = q.get("source_files", [])
                if isinstance(q.get("source_file"), str):
                    expected_sources = [q["source_file"]] if not expected_sources else expected_sources
                cit_metrics = _evaluate_citations(gen_result.answer, expected_sources)

                # ── Store result ──
                result_entry = {
                    "question_id": qid,
                    "question": q["question"],
                    "category": q.get("category", "unknown"),
                    "difficulty": q.get("difficulty", "unknown"),
                    "answerable": is_answerable,
                    "config": config,
                    "gen_model": gen_model,
                    "generation": asdict(gen_result),
                    "judge_scores": judge_scores,
                    "citation_metrics": asdict(cit_metrics),
                }

                all_results.append(result_entry)
                completed.add(key)

                # Save intermediate results after each question
                _save_intermediate({
                    "results": all_results,
                    "completed_keys": list(completed),
                })

            logger.info(
                f"Completed config '{config}' with model '{gen_model}' "
                f"({len(questions)} questions)"
            )

    # ── Final output ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save full results JSON
    results_file = RESULTS_DIR / f"exp1_results_{timestamp}.json"
    summary = _aggregate_results(all_results)

    output = {
        "experiment": "exp1_rlm_vs_singlepass",
        "timestamp": timestamp,
        "index_name": index_name,
        "gen_models": gen_models,
        "configs": configs,
        "n_questions": len(questions),
        "n_answerable": n_answerable,
        "n_unanswerable": n_unanswerable,
        "total_evaluations": len(all_results),
        "per_question_results": all_results,
        "aggregate_summary": summary,
    }

    with open(results_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Results saved to {results_file}")

    # Also save as latest
    latest_file = RESULTS_DIR / "exp1_results_latest.json"
    with open(latest_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Generate markdown report
    md_report = _generate_markdown_report(all_results, summary)
    md_file = RESULTS_DIR / f"exp1_results_{timestamp}.md"
    with open(md_file, "w") as f:
        f.write(md_report)
    logger.info(f"Markdown report saved to {md_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("EXPERIMENT 1 COMPLETE")
    print("=" * 70)
    print(f"Total evaluations: {len(all_results)}")
    print(f"Results: {results_file}")
    print(f"Report:  {md_file}")
    print()

    # Print compact summary table
    print(md_report[:2000])

    # Clean up intermediate file on success
    if INTERMEDIATE_FILE.exists():
        INTERMEDIATE_FILE.unlink()
        logger.info("Cleaned up intermediate results file")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Experiment 1: RLM vs Single-Pass RAG"
    )
    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX,
        help=f"Index name to use (default: {DEFAULT_INDEX})",
    )
    parser.add_argument(
        "--gen-models",
        nargs="+",
        default=GEN_MODELS,
        help="Generation models to test (default: all)",
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=CONFIG_NAMES,
        choices=CONFIG_NAMES + ["rlm_20_verify"],
        help="Configurations to test (default: all)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Limit number of questions (for quick testing)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from saved intermediate results",
    )

    args = parser.parse_args()

    asyncio.run(run_experiment(
        gen_models=args.gen_models,
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
        index_name=args.index,
    ))


if __name__ == "__main__":
    main()
