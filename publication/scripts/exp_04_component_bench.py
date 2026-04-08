#!/usr/bin/env python3
"""
V4-7: Component-Level Orchestrator Benchmarks

Isolates each of the 5 LLM-powered orchestrator components and benchmarks
them independently across 13 base models (8B–235B + Gemini API) with all
applicable thinking variants (~24 model entries total).

Components:
  1. Analyzer  — binary query classification (direct_answer vs needs_plan)
  2. Planner   — execution plan generation with tool calls
  3. Supervisor — step result quality evaluation (0-100)
  4. Distiller  — observation compression (≤600 words)
  5. Synthesizer — final answer generation from step results

Usage:
    # Build datasets (no model calls)
    uv run python publication/scripts/exp_04_component_bench.py --build-dataset

    # Smoke test
    uv run python publication/scripts/exp_04_component_bench.py --benchmark analyzer --models qwen3-coder --max-items 10

    # Run one benchmark, one model
    uv run python publication/scripts/exp_04_component_bench.py --benchmark supervisor --models qwen3-coder

    # Run all benchmarks for all models
    uv run python publication/scripts/exp_04_component_bench.py --benchmark all

    # Resume interrupted run
    uv run python publication/scripts/exp_04_component_bench.py --benchmark distiller --resume

    # Use specific Ollama port
    uv run python publication/scripts/exp_04_component_bench.py --benchmark analyzer --port 11435
"""

import argparse
import asyncio
import json
import logging
import os
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default TOOL_SERVER_URL to localhost when running outside Docker
if "TOOL_SERVER_URL" not in os.environ:
    os.environ["TOOL_SERVER_URL"] = "http://localhost:8777"

from exp_common import (
    JUDGE_MODEL,
    JUDGE_OPTIONS,
    RESULTS_DIR,
    judge_answer,
    load_ground_truth,
    load_intermediate,
    save_intermediate,
    result_key,
    save_final_results,
    configure_gemini_from_admin,
)

from backend.agents.model_router import ModelRouter

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_04_component_bench")
logger.setLevel(logging.INFO)

GROUND_TRUTH_PATH = PROJECT_ROOT / "datasets" / "ground_truth_v4.json"
V4_4_RESULTS_PATH = RESULTS_DIR / "v4_4_generation_latest.json"

# ─────────────────────────────────────────────────────────────
# Model Matrix
# ─────────────────────────────────────────────────────────────

MODEL_MATRIX: List[Tuple[str, str, List]] = [
    ("ollama::llama3:8b", "8B", [False]),
    ("ollama::gpt-oss:20b", "20B", [False, "low", "medium", "high"]),
    ("ollama::devstral-small-2:24b", "24B", [False]),
    ("ollama::gemma3:27b", "27B", [False]),
    ("ollama::qwen3-coder:latest", "30B", [False]),
    ("ollama::nemotron-3-nano:30b", "30B", [False]),
    ("ollama::olmo-3:32b", "32B", [False]),
    ("ollama::qwen3.5:35b", "35B", [False, True]),
    ("ollama::deepseek-r1:70b", "70B", [True]),
    ("ollama::gpt-oss:120b", "120B", [False, "low", "high"]),
    ("ollama::qwen3.5:122b", "122B", [False, True]),
    ("ollama::qwen3:235b", "235B", [False, True]),
    ("gemini::gemini-3-flash-preview", "API", [False, True]),
]

# num_ctx per benchmark
BENCH_NUM_CTX = {
    "analyzer": 16384,
    "planner": 24576,
    "supervisor": 24576,
    "distiller": 24576,
    "synthesizer": 24576,
}

BENCH_NUM_PREDICT = {
    "analyzer": 512,
    "planner": 4096,
    "supervisor": 1024,
    "distiller": 1200,
    "synthesizer": 8192,
}

BENCHMARK_NAMES = ["analyzer", "planner", "supervisor", "distiller", "synthesizer"]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def model_key(model_id: str, think) -> str:
    """Create a deterministic key from model ID and think parameter."""
    # Extract short name from model_id
    if "::" in model_id:
        name = model_id.split("::")[1]
    else:
        name = model_id
    # Clean up name for filesystem
    name = name.replace(":", "-").replace("/", "_")
    if think is False or think is None:
        return name
    elif think is True:
        return f"{name}_think-on"
    else:
        return f"{name}_think-{think}"


def parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from LLM response, handling markdown fences and thinking tags."""
    if not text:
        return None
    # Strip <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def extract_numbers(text: str) -> set:
    """Extract all numbers/percentages from text for retention checking."""
    if not text:
        return set()
    # Match integers, decimals, percentages, p-values
    return set(re.findall(r"\d+(?:\.\d+)?(?:%|‰)?", text))


def extract_sources(text: str) -> set:
    """Extract document/paper names mentioned in text."""
    if not text:
        return set()
    # Match common paper filename patterns
    patterns = [
        r"\b\d{2}_\w+\.pdf\b",               # 01_sarek.pdf
        r"\b[\w-]+\.pdf\b",                    # any .pdf reference
        r"\b[A-Z][a-z]+ et al\.?,? \d{4}\b",  # Author et al., 2024
    ]
    sources = set()
    for pattern in patterns:
        sources.update(re.findall(pattern, text))
    return sources


def extract_tokens(response: Dict) -> Tuple[int, int]:
    """Extract input/output token counts from model response."""
    tokens_in = response.get("prompt_eval_count", 0)
    tokens_out = response.get("eval_count", 0)
    # Gemini / chat endpoint fallback
    if not tokens_in and not tokens_out:
        usage = response.get("usage", {})
        tokens_in = usage.get("input_tokens", usage.get("prompt_tokens", 0))
        tokens_out = usage.get("output_tokens", usage.get("completion_tokens", 0))
    # chat endpoint: message content
    if not tokens_in and not tokens_out:
        msg = response.get("message", {})
        if msg:
            tokens_in = response.get("prompt_eval_count", 0)
            tokens_out = response.get("eval_count", 0)
    return tokens_in, tokens_out


def get_response_text(response: Dict) -> str:
    """Extract text from either generate() or chat() response."""
    # generate() format
    text = response.get("response", "")
    if text:
        return text
    # chat() format
    msg = response.get("message", {})
    if isinstance(msg, dict):
        return msg.get("content", "")
    return ""


def filter_model_matrix(model_filter: Optional[str]) -> List[Tuple[str, str, List]]:
    """Filter MODEL_MATRIX by substring match on model name."""
    if not model_filter:
        return MODEL_MATRIX
    filters = [f.strip().lower() for f in model_filter.split(",")]
    result = []
    for model_id, size, thinks in MODEL_MATRIX:
        name_lower = model_id.lower()
        if any(f in name_lower for f in filters):
            result.append((model_id, size, thinks))
    if not result:
        logger.error(f"No models matched filter: {model_filter}")
        logger.info("Available models: " + ", ".join(m[0] for m in MODEL_MATRIX))
        sys.exit(1)
    return result


# ─────────────────────────────────────────────────────────────
# Prompt Templates (imported from orchestrator)
# ─────────────────────────────────────────────────────────────

# Import the actual prompts used by the orchestrator
from backend.agents.orchestrator.prompts import (
    ORCHESTRATOR_ANALYZER_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    ORCHESTRATOR_PLANNER_PROMPT,
    SUPERVISOR_EVALUATION_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    ORCHESTRATOR_SYNTHESIZER_PROMPT,
)
from backend.agents.orchestrator.observation_distiller import _DISTILL_PROMPT

# Static tools description for planner benchmark (simplified)
TOOLS_DESCRIPTION = """**smart_query**: Search and analyze documents in a knowledge base using intelligent routing. Handles simple lookups, deep research, cross-document analysis, and corpus analysis automatically.
  Parameters:
    - query: string (required) — The research question or search query
    - index_name: string (required) — Name of the document index to search
    - strategy: string — Override routing: "simple", "deep", "cross_doc", "corpus"

**web_search**: Search the web for current information.
  Parameters:
    - query: string (required) — Search query
    - max_results: integer — Maximum results to return (default: 5)

**execute_python**: Execute Python code in a Jupyter notebook.
  Parameters:
    - code: string (required) — Python code to execute
    - timeout: integer — Execution timeout in seconds (default: 30)

**read_file**: Read a file from the workspace.
  Parameters:
    - file_path: string (required) — Path to file

**write_file**: Write content to a file in the workspace.
  Parameters:
    - file_path: string (required) — Path to file
    - content: string (required) — Content to write

**list_files**: List files in a workspace directory.
  Parameters:
    - directory: string — Directory path (default: workspace root)

**read_image**: Read and analyze an image file.
  Parameters:
    - image_path: string (required) — Path to image file

**ask_user**: Ask the user a clarifying question.
  Parameters:
    - question: string (required) — Question to ask
    - options: array — Optional list of choices

**inspect_document_index**: Get metadata and statistics about a document index.
  Parameters:
    - index_name: string (required) — Index to inspect

**read_document**: Read a specific document's content.
  Parameters:
    - file_path: string (required) — Document path
    - pages: string — Page range (e.g. "1-5")

**list_document_indexes**: List all available document indexes.
  Parameters: (none)
"""


# ─────────────────────────────────────────────────────────────
# Dataset Builders
# ─────────────────────────────────────────────────────────────

def build_analyzer_dataset(gt_questions: List[Dict]) -> List[Dict]:
    """Build analyzer benchmark dataset (~350 items).

    Source A: 200 answerable GT questions (needs_plan)
    Source B: 100 programmatic direct_answer queries
    Source C: 50 edge cases (manually labeled)
    """
    dataset = []

    # Source A: answerable GT questions → needs_plan
    answerable = [q for q in gt_questions if q.get("answerable", True)]
    for q in answerable:
        dataset.append({
            "query": q["question"],
            "expected_decision": "needs_plan",
            "expected_complexity": _complexity_from_category(q["category"]),
            "source": "ground_truth",
            "category": q["category"],
            "question_id": q["id"],
        })

    # Source B: direct_answer queries (programmatic)
    greetings = [
        "Hello!", "Hi there", "Good morning", "Hey, how are you?",
        "Hi!", "Hello, nice to meet you", "Good afternoon",
        "Hey!", "Greetings!", "Hi, I'm new here",
        "Hello there!", "Good evening", "Howdy!",
        "Hi, how's it going?", "What's up?",
        "Yo!", "Hey there!", "Hiya!", "Sup?",
        "Good day!", "Hello hello!", "Hi again",
        "Hey hey!", "Hola!", "Bonjour!",
        "Aloha!", "What's happening?", "How are things?",
        "Nice day, isn't it?", "Morning!",
    ]
    for q in greetings:
        dataset.append({
            "query": q,
            "expected_decision": "direct_answer",
            "expected_complexity": "trivial",
            "source": "greeting",
            "category": "greeting",
        })

    meta_questions = [
        "What can you do?", "How do you work?", "Who made you?",
        "What are your capabilities?", "Help", "What is Mentori?",
        "Tell me about yourself", "What tools do you have?",
        "How can you help me?", "What kind of questions can I ask?",
        "Are you an AI?", "What models do you use?",
        "Can you search the web?", "Do you remember our conversations?",
        "What file formats do you support?", "How do I upload documents?",
        "Can you write code?", "What programming languages do you support?",
        "How accurate are your answers?", "What's your knowledge cutoff?",
        "Can you analyze images?", "Do you support multiple languages?",
        "How do I create an index?", "What is RAG?",
        "Can you help with data analysis?", "What is deep research?",
        "How do you cite sources?", "What's the difference between simple and deep search?",
        "Can you generate plots?", "How do I export results?",
    ]
    for q in meta_questions:
        dataset.append({
            "query": q,
            "expected_decision": "direct_answer",
            "expected_complexity": "trivial",
            "source": "meta",
            "category": "meta",
        })

    clarifications = [
        "Can you explain that?", "What do you mean by that?",
        "Tell me more", "Could you elaborate?",
        "I don't understand", "Can you rephrase that?",
        "What does that mean?", "Could you simplify that?",
        "Can you give an example?", "That's confusing, explain again",
        "What exactly do you mean?", "Break it down for me",
        "Can you put that in simpler terms?", "I'm not following",
        "Say that again?", "Huh?", "Could you be more specific?",
        "Can you clarify the last point?", "What was that about?",
        "Go on", "Continue", "And then what?",
    ]
    for q in clarifications[:20]:
        dataset.append({
            "query": q,
            "expected_decision": "direct_answer",
            "expected_complexity": "trivial",
            "source": "clarification",
            "category": "clarification",
        })

    general_knowledge = [
        "What is PCR?", "Define epidemiology",
        "Who discovered penicillin?", "What is a p-value?",
        "Explain the central dogma of molecular biology",
        "What is CRISPR?", "Define bioinformatics",
        "What is a genome?", "Explain natural selection",
        "What is a confidence interval?",
        "What is RNA?", "Define phylogenetics",
        "What is next-generation sequencing?", "Explain Hardy-Weinberg equilibrium",
        "What is a meta-analysis?", "Define variant calling",
        "What is machine learning?", "Explain Bayesian statistics",
        "What is a transcriptome?", "Define proteomics",
    ]
    for q in general_knowledge:
        dataset.append({
            "query": q,
            "expected_decision": "direct_answer",
            "expected_complexity": "simple",
            "source": "general_knowledge",
            "category": "general_knowledge",
        })

    # Source C: edge cases (ambiguous queries with manual labels)
    edge_cases = [
        # General knowledge → direct_answer
        ("Tell me about CRISPR", "direct_answer", "simple"),
        ("What is whole genome sequencing?", "direct_answer", "simple"),
        ("Explain variant calling pipelines", "direct_answer", "simple"),
        ("What are the types of genomic variants?", "direct_answer", "simple"),
        ("How does Illumina sequencing work?", "direct_answer", "simple"),
        ("What is a BAM file?", "direct_answer", "simple"),
        ("Explain the difference between WGS and WES", "direct_answer", "simple"),
        ("What is copy number variation?", "direct_answer", "simple"),
        ("How does read alignment work?", "direct_answer", "simple"),
        ("What is a VCF file format?", "direct_answer", "simple"),
        # Needs documents → needs_plan
        ("What does my CRISPR paper say?", "needs_plan", "simple"),
        ("Summarize the papers I uploaded", "needs_plan", "moderate"),
        ("What methodology was used in the Sarek paper?", "needs_plan", "simple"),
        ("Compare the approaches across my papers", "needs_plan", "complex"),
        ("Find the sample sizes mentioned in my documents", "needs_plan", "moderate"),
        ("What are the main findings in my uploaded research?", "needs_plan", "moderate"),
        ("Search my documents for mentions of machine learning", "needs_plan", "simple"),
        ("Which papers discuss variant calling?", "needs_plan", "simple"),
        ("Extract the key statistics from my papers", "needs_plan", "moderate"),
        ("What tools are mentioned across my documents?", "needs_plan", "moderate"),
        ("Analyze the citations in my papers", "needs_plan", "moderate"),
        ("List the datasets used in my uploaded papers", "needs_plan", "moderate"),
        ("How do the results compare between paper A and paper B?", "needs_plan", "complex"),
        ("What is the sample size in the HPAI study?", "needs_plan", "simple"),
        ("Show me all papers about AMR", "needs_plan", "simple"),
        # Action requests → needs_plan
        ("Search the web for the latest COVID-19 variants", "needs_plan", "simple"),
        ("Run this Python code: print('hello')", "needs_plan", "simple"),
        ("Create a plot of the data in results.csv", "needs_plan", "moderate"),
        ("Write a summary report to output.md", "needs_plan", "moderate"),
        ("List all files in my workspace", "needs_plan", "simple"),
        # Ambiguous but context-dependent
        ("Tell me about the methodology", "needs_plan", "moderate"),
        ("What were the results?", "needs_plan", "simple"),
        ("Any interesting findings?", "needs_plan", "moderate"),
        ("What's the conclusion?", "needs_plan", "simple"),
        ("Can you summarize everything?", "needs_plan", "complex"),
        # Tricky direct answers
        ("Thanks!", "direct_answer", "trivial"),
        ("That's helpful, thank you", "direct_answer", "trivial"),
        ("Perfect, that answers my question", "direct_answer", "trivial"),
        ("OK", "direct_answer", "trivial"),
        ("Got it", "direct_answer", "trivial"),
        ("Never mind", "direct_answer", "trivial"),
        ("Forget it", "direct_answer", "trivial"),
        ("Let me think about that", "direct_answer", "trivial"),
        ("I'll come back to this later", "direct_answer", "trivial"),
        ("Sounds good", "direct_answer", "trivial"),
    ]
    for query, decision, complexity in edge_cases:
        dataset.append({
            "query": query,
            "expected_decision": decision,
            "expected_complexity": complexity,
            "source": "edge_case",
            "category": "edge_case",
        })

    logger.info(f"Analyzer dataset: {len(dataset)} items "
                f"(needs_plan={sum(1 for d in dataset if d['expected_decision']=='needs_plan')}, "
                f"direct_answer={sum(1 for d in dataset if d['expected_decision']=='direct_answer')})")
    return dataset


def _complexity_from_category(category: str) -> str:
    """Map question category to expected complexity level."""
    return {
        "factual_recall": "simple",
        "conceptual": "moderate",
        "technical": "moderate",
        "cross_document": "complex",
        "synthesis": "complex",
        "out_of_domain": "simple",
    }.get(category, "moderate")


def build_planner_dataset(gt_questions: List[Dict]) -> List[Dict]:
    """Build planner benchmark dataset (~100 items).

    Source A: 60 GT questions (10 per category) → should use smart_query
    Source B: 20 non-research tasks → specific tools
    Source C: 20 multi-step tasks
    """
    dataset = []

    # Source A: research questions (10 per category)
    by_cat = {}
    for q in gt_questions:
        if not q.get("answerable", True):
            continue
        cat = q["category"]
        by_cat.setdefault(cat, []).append(q)

    for cat, questions in by_cat.items():
        for q in questions[:10]:
            dataset.append({
                "query": q["question"],
                "expected_tools": ["smart_query"],
                "expected_agent": "editor",
                "expected_steps": 1,
                "source": "ground_truth",
                "category": cat,
                "question_id": q["id"],
            })

    # Source B: non-research tasks (20)
    non_research = [
        ("List all files in my workspace", ["list_files"], "handyman", 1),
        ("Show me what's in the data directory", ["list_files"], "handyman", 1),
        ("Search the web for latest COVID-19 variants", ["web_search"], "handyman", 1),
        ("Find recent news about antimicrobial resistance", ["web_search"], "handyman", 1),
        ("Look up the latest SARS-CoV-2 lineages online", ["web_search"], "handyman", 1),
        ("Run this Python code: print('hello world')", ["execute_python"], "coder", 1),
        ("Calculate the mean of [1, 2, 3, 4, 5] using Python", ["execute_python"], "coder", 1),
        ("Create a bar chart of these values: A=10, B=20, C=15", ["execute_python"], "coder", 1),
        ("Write a Python script to parse a FASTA file", ["execute_python"], "coder", 1),
        ("Generate a heatmap from my results", ["execute_python"], "coder", 1),
        ("Analyze the image at workspace/figure1.png", ["read_image"], "vision", 1),
        ("Describe what's shown in workspace/plot.png", ["read_image"], "vision", 1),
        ("Read the file at workspace/results.txt", ["read_file"], "handyman", 1),
        ("Show me the contents of config.json", ["read_file"], "handyman", 1),
        ("Write 'Hello World' to workspace/output.txt", ["write_file"], "handyman", 1),
        ("Save these notes to workspace/notes.md", ["write_file"], "handyman", 1),
        ("What document indexes do I have?", ["list_document_indexes"], "editor", 1),
        ("Show me the details of my research index", ["inspect_document_index"], "editor", 1),
        ("Read pages 1-5 of document 01_sarek.pdf", ["read_document"], "editor", 1),
        ("What's in the first page of my HPAI paper?", ["read_document"], "editor", 1),
    ]
    for query, tools, agent, steps in non_research:
        dataset.append({
            "query": query,
            "expected_tools": tools,
            "expected_agent": agent,
            "expected_steps": steps,
            "source": "non_research",
            "category": "non_research",
        })

    # Source C: multi-step tasks (20)
    multi_step = [
        ("Find papers about CRISPR, then summarize the top 3 findings",
         ["smart_query"], "editor", 1),  # smart_query handles internally
        ("Search my documents for machine learning methods and create a comparison table in Python",
         ["smart_query", "execute_python"], None, 2),
        ("Look up recent COVID variants online, then search my papers for related content",
         ["web_search", "smart_query"], None, 2),
        ("Read the methodology section of my Sarek paper and write a summary to a file",
         ["smart_query", "write_file"], None, 2),
        ("Find all papers mentioning sample sizes, then calculate the average using Python",
         ["smart_query", "execute_python"], None, 2),
        ("Search for variant calling tools in my papers, then look up their latest versions online",
         ["smart_query", "web_search"], None, 2),
        ("Analyze figure1.png and compare it with the results described in my papers",
         ["read_image", "smart_query"], None, 2),
        ("List my workspace files and read the most recent results file",
         ["list_files", "read_file"], "handyman", 2),
        ("Search my papers for statistical methods, then write a Python script to replicate one",
         ["smart_query", "execute_python"], None, 2),
        ("Find cross-document themes and save the analysis to a report",
         ["smart_query", "write_file"], None, 2),
        ("Read my AMR paper and extract key statistics into a CSV",
         ["smart_query", "execute_python"], None, 2),
        ("Search the web for bioinformatics best practices and compare with my papers",
         ["web_search", "smart_query"], None, 2),
        ("Analyze the image in workspace/gel.png and write a description to results.md",
         ["read_image", "write_file"], None, 2),
        ("Find papers about epidemiology methods, summarize them, and create a comparison plot",
         ["smart_query", "execute_python"], None, 2),
        ("List all document indexes, inspect the largest one, then run a deep search",
         ["list_document_indexes", "inspect_document_index", "smart_query"], None, 3),
        ("Extract data from my papers, write it to a CSV, then generate a summary plot",
         ["smart_query", "execute_python", "execute_python"], None, 3),
        ("Search the web for three topics, then synthesize what I found",
         ["web_search", "web_search", "web_search"], "handyman", 3),
        ("Read three different documents and compare their methodologies",
         ["smart_query"], "editor", 1),  # smart_query handles multi-doc
        ("Analyze two images and write a comparative report",
         ["read_image", "read_image", "write_file"], None, 3),
        ("Search papers, run analysis code, and save results to workspace",
         ["smart_query", "execute_python", "write_file"], None, 3),
    ]
    for query, tools, agent, steps in multi_step:
        dataset.append({
            "query": query,
            "expected_tools": tools,
            "expected_agent": agent,
            "expected_steps": steps,
            "source": "multi_step",
            "category": "multi_step",
        })

    logger.info(f"Planner dataset: {len(dataset)} items")
    return dataset


def build_supervisor_dataset(v4_4_results: List[Dict]) -> List[Dict]:
    """Build supervisor benchmark dataset (~200 items) from V4-4 results.

    Source A: 80 good results (correctness >= 4)
    Source B: 80 bad results (correctness <= 2 or failed OOD)
    Source C: 40 borderline results (correctness == 3)
    """
    dataset = []

    good, bad, borderline = [], [], []
    for r in v4_4_results:
        scores = r.get("judge_scores", {})
        answer = r.get("generation", {}).get("answer", "")
        if not answer:
            continue

        correctness = scores.get("correctness")
        if correctness is None:
            # Unanswerable: use refusal_accuracy
            refusal = scores.get("refusal_accuracy", 0)
            if refusal >= 4:
                good.append(r)
            elif refusal <= 2:
                bad.append(r)
            else:
                borderline.append(r)
            continue

        if correctness >= 4:
            good.append(r)
        elif correctness <= 2:
            bad.append(r)
        elif correctness == 3:
            borderline.append(r)

    # Sample to target counts
    import random
    random.seed(42)
    good_sample = random.sample(good, min(80, len(good)))
    bad_sample = random.sample(bad, min(80, len(bad)))
    border_sample = random.sample(borderline, min(40, len(borderline)))

    def _make_supervisor_item(r, expected_quality: str):
        scores = r.get("judge_scores", {})
        correctness = scores.get("correctness", scores.get("refusal_accuracy", 0))
        answer = r.get("generation", {}).get("answer", "")
        question = r["question"]

        return {
            "question_id": r["question_id"],
            "question": question,
            "category": r["category"],
            "config": r["config"],
            "answer": answer,
            "judge_correctness": correctness,
            "expected_quality": expected_quality,  # "good", "bad", "borderline"
            "goal": question,
            "step_description": f"Answer: {question}",
            "tool_name": "smart_query",
            "tool_args": json.dumps({"query": question, "index_name": "exp_v4_s20_n0"}),
            "expected_output": "Detailed answer with citations",
        }

    for r in good_sample:
        dataset.append(_make_supervisor_item(r, "good"))
    for r in bad_sample:
        dataset.append(_make_supervisor_item(r, "bad"))
    for r in border_sample:
        dataset.append(_make_supervisor_item(r, "borderline"))

    random.shuffle(dataset)
    logger.info(f"Supervisor dataset: {len(dataset)} items "
                f"(good={len(good_sample)}, bad={len(bad_sample)}, "
                f"borderline={len(border_sample)})")
    return dataset


def build_distiller_dataset(v4_4_results: List[Dict]) -> List[Dict]:
    """Build distiller benchmark dataset (~100 items) from V4-4 results.

    Uses RLM-generated answers (which are 2K-10K chars) as proxy for tool output.
    """
    dataset = []

    # Filter to RLM configs with substantial answers
    rlm_results = [
        r for r in v4_4_results
        if r.get("config", "").startswith("rlm_")
        and len(r.get("generation", {}).get("answer", "")) > 2000
    ]

    import random
    random.seed(42)

    # Source A: real long outputs (60)
    real_sample = random.sample(rlm_results, min(60, len(rlm_results)))
    for r in real_sample:
        answer = r["generation"]["answer"]
        dataset.append({
            "question_id": r["question_id"],
            "raw_content": answer,
            "raw_length": len(answer),
            "tool_name": "smart_query",
            "source": "real_rlm",
            "numbers": list(extract_numbers(answer)),
            "sources": list(extract_sources(answer)),
        })

    # Source B: synthetic long outputs (20) — concatenate multiple answers
    if len(rlm_results) >= 4:
        for i in range(20):
            # Pick 2-5 random answers and concatenate
            n_concat = random.randint(2, min(5, len(rlm_results)))
            parts = random.sample(rlm_results, n_concat)
            combined = "\n\n---\n\n".join(
                p["generation"]["answer"] for p in parts
            )
            dataset.append({
                "question_id": f"synthetic_{i:03d}",
                "raw_content": combined,
                "raw_length": len(combined),
                "tool_name": "deep_research_rlm",
                "source": "synthetic_concat",
                "numbers": list(extract_numbers(combined)),
                "sources": list(extract_sources(combined)),
            })

    # Source C: edge cases (20) — very long or number-dense
    number_dense = sorted(
        rlm_results,
        key=lambda r: len(extract_numbers(r.get("generation", {}).get("answer", ""))),
        reverse=True,
    )
    for r in number_dense[:20]:
        answer = r["generation"]["answer"]
        if any(d["question_id"] == r["question_id"] and d["source"] == "real_rlm" for d in dataset):
            continue  # skip duplicates
        dataset.append({
            "question_id": r["question_id"],
            "raw_content": answer,
            "raw_length": len(answer),
            "tool_name": "smart_query",
            "source": "number_dense",
            "numbers": list(extract_numbers(answer)),
            "sources": list(extract_sources(answer)),
        })

    logger.info(f"Distiller dataset: {len(dataset)} items")
    return dataset


def build_synthesizer_dataset(
    v4_4_results: List[Dict],
    gt_questions: List[Dict],
) -> List[Dict]:
    """Build synthesizer benchmark dataset (~100 items) from V4-4 RLM-10 results.

    Uses RLM-10 answers as synthetic "step results" for the synthesizer.
    """
    dataset = []
    gt_by_id = {q["id"]: q for q in gt_questions}

    # Filter to rlm_10 config with valid answers
    rlm10 = [
        r for r in v4_4_results
        if r.get("config") == "rlm_10"
        and r.get("generation", {}).get("answer", "")
    ]

    # Take up to 80 answerable + 20 OOD
    answerable = [r for r in rlm10 if r.get("answerable", True)]
    ood = [r for r in rlm10 if not r.get("answerable", True)]

    import random
    random.seed(42)
    ans_sample = random.sample(answerable, min(80, len(answerable)))
    ood_sample = random.sample(ood, min(20, len(ood)))

    for r in ans_sample + ood_sample:
        gt = gt_by_id.get(r["question_id"], {})
        answer = r["generation"]["answer"]

        # Build synthetic step result
        step_content = answer
        dataset.append({
            "question_id": r["question_id"],
            "question": r["question"],
            "category": r["category"],
            "answerable": r.get("answerable", True),
            "step_result_content": step_content,
            "expected_answer": gt.get("expected_answer", ""),
            "expected_concepts": gt.get("expected_concepts", []),
            "source": "rlm_10",
        })

    logger.info(f"Synthesizer dataset: {len(dataset)} items "
                f"(answerable={len(ans_sample)}, ood={len(ood_sample)})")
    return dataset


# ─────────────────────────────────────────────────────────────
# Benchmark Runners
# ─────────────────────────────────────────────────────────────

async def run_analyzer_bench(
    item: Dict, router: ModelRouter, model_id: str, think, num_ctx: int
) -> Dict:
    """Run analyzer benchmark on a single item."""
    prompt = ORCHESTRATOR_ANALYZER_PROMPT.format(
        user_context="(No user context available)",
        memory_context="(No previous work in this task)",
        conversation_context="(No previous conversation)",
        user_query=item["query"],
    )

    t0 = time.time()
    try:
        # Use chat() for universal thinking-mode support
        response = await router.chat(
            model_identifier=model_id,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0,
                "num_predict": BENCH_NUM_PREDICT["analyzer"],
                "num_ctx": num_ctx,
            },
            think=think,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        parsed = parse_json_response(text)
        if parsed:
            decision = parsed.get("decision", "")
            complexity = parsed.get("complexity", "")
            json_valid = True
        else:
            decision = ""
            complexity = ""
            json_valid = False

        return {
            "decision": decision,
            "complexity": complexity,
            "json_valid": json_valid,
            "decision_correct": decision == item["expected_decision"],
            "complexity_correct": complexity == item["expected_complexity"],
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "raw_response": text[:500],
            "error": None,
        }
    except Exception as e:
        return {
            "decision": "",
            "complexity": "",
            "json_valid": False,
            "decision_correct": False,
            "complexity_correct": False,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "raw_response": "",
            "error": str(e),
        }


async def run_planner_bench(
    item: Dict, router: ModelRouter, model_id: str, think, num_ctx: int
) -> Dict:
    """Run planner benchmark on a single item."""
    prompt = ORCHESTRATOR_PLANNER_PROMPT.format(
        user_query=item["query"],
        available_indexes="exp_v4_s20_n0 (50 core papers, 0 noise papers)",
        workspace_path="/workspace_data/task_bench/",
        memory_context="(No session memory)",
        workspace_files="(No files in workspace yet)",
        user_context="(No user profile information available)",
        conversation_context="(No previous conversation)",
        tools_description=TOOLS_DESCRIPTION,
    )

    t0 = time.time()
    try:
        # Use chat() with system prompt like the real planner
        response = await router.chat(
            model_identifier=model_id,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0,
                "num_predict": BENCH_NUM_PREDICT["planner"],
                "num_ctx": num_ctx,
            },
            think=think,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        parsed = parse_json_response(text)
        if not parsed:
            return {
                "json_valid": False,
                "tool_correct": False,
                "agent_correct": False,
                "step_count": 0,
                "has_placeholders": False,
                "uses_smart_query_routing": True,
                "latency_s": round(latency, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "raw_response": text[:500],
                "error": None,
            }

        steps = parsed.get("steps", [])
        step_count = len(steps)

        # Check tool selection accuracy
        actual_tools = [s.get("tool_name", "") for s in steps]
        expected_tools = item["expected_tools"]
        tool_correct = any(t in actual_tools for t in expected_tools)

        # Check agent role
        actual_agents = [s.get("agent_role", "") for s in steps]
        agent_correct = (
            item["expected_agent"] is None
            or item["expected_agent"] in actual_agents
        )

        # Check for placeholders (bad: {{placeholder}} except {{step_N.result}})
        all_args_str = json.dumps([s.get("tool_args", {}) for s in steps])
        placeholder_pattern = r"\{\{(?!step_\d+\.result)"
        has_placeholders = bool(re.search(placeholder_pattern, all_args_str))

        # Check constraint: should NOT use query_documents directly
        banned_tools = {"query_documents", "deep_research_rlm", "cross_document_analysis", "analyze_corpus"}
        uses_smart_query_routing = not any(t in banned_tools for t in actual_tools)

        # Check step efficiency
        step_efficiency = step_count / max(item["expected_steps"], 1)

        return {
            "json_valid": True,
            "tool_correct": tool_correct,
            "agent_correct": agent_correct,
            "step_count": step_count,
            "expected_steps": item["expected_steps"],
            "step_efficiency": round(step_efficiency, 2),
            "has_placeholders": has_placeholders,
            "uses_smart_query_routing": uses_smart_query_routing,
            "actual_tools": actual_tools,
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "raw_response": text[:500],
            "error": None,
        }
    except Exception as e:
        return {
            "json_valid": False,
            "tool_correct": False,
            "agent_correct": False,
            "step_count": 0,
            "has_placeholders": False,
            "uses_smart_query_routing": True,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "raw_response": "",
            "error": str(e),
        }


async def run_supervisor_bench(
    item: Dict, router: ModelRouter, model_id: str, think, num_ctx: int
) -> Dict:
    """Run supervisor benchmark on a single item."""
    prompt = SUPERVISOR_EVALUATION_PROMPT.format(
        goal=item["goal"],
        step_id="step_1",
        step_description=item["step_description"],
        tool_name=item["tool_name"],
        tool_args=item["tool_args"],
        expected_output=item["expected_output"],
        index_context="",
        result_content=item["answer"][:8000],
        previous_steps_summary="(This is the first step)",
    )

    t0 = time.time()
    try:
        # Use chat() for universal thinking-mode support
        response = await router.chat(
            model_identifier=model_id,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0,
                "num_predict": BENCH_NUM_PREDICT["supervisor"],
                "num_ctx": num_ctx,
            },
            think=think,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        parsed = parse_json_response(text)
        if not parsed:
            return {
                "json_valid": False,
                "quality_score": None,
                "should_retry": None,
                "should_escalate": None,
                "latency_s": round(latency, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "raw_response": text[:500],
                "error": None,
            }

        quality_score = parsed.get("quality_score")
        should_retry = parsed.get("should_retry")
        should_escalate = parsed.get("should_escalate")

        # Validate score is numeric 0-100
        if isinstance(quality_score, (int, float)) and 0 <= quality_score <= 100:
            score_valid = True
        else:
            score_valid = False
            quality_score = None

        return {
            "json_valid": True,
            "score_valid": score_valid,
            "quality_score": quality_score,
            "should_retry": should_retry,
            "should_escalate": should_escalate,
            "issues": parsed.get("issues", []),
            "reasoning": parsed.get("reasoning", ""),
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "raw_response": text[:500],
            "error": None,
        }
    except Exception as e:
        return {
            "json_valid": False,
            "quality_score": None,
            "should_retry": None,
            "should_escalate": None,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "raw_response": "",
            "error": str(e),
        }


async def run_distiller_bench(
    item: Dict, router: ModelRouter, model_id: str, think, num_ctx: int
) -> Dict:
    """Run distiller benchmark on a single item."""
    prompt = _DISTILL_PROMPT.format(
        tool_name=item["tool_name"],
        raw_content=item["raw_content"][:12000],
    )

    t0 = time.time()
    try:
        response = await router.chat(
            model_identifier=model_id,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0,
                "num_predict": BENCH_NUM_PREDICT["distiller"],
                "num_ctx": num_ctx,
            },
            think=think,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        if not text.strip():
            return {
                "distilled": "",
                "distilled_length": 0,
                "word_count": 0,
                "word_count_compliant": False,
                "compression_ratio": 0,
                "number_retention": 0,
                "source_retention": 0,
                "has_key_findings": False,
                "has_sources_cited": False,
                "latency_s": round(latency, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "error": "Empty response",
            }

        # Compute retention metrics
        raw_numbers = set(item.get("numbers", []))
        raw_sources = set(item.get("sources", []))
        dist_numbers = extract_numbers(text)
        dist_sources = extract_sources(text)

        number_retention = (
            len(raw_numbers & dist_numbers) / len(raw_numbers)
            if raw_numbers else 1.0
        )
        source_retention = (
            len(raw_sources & dist_sources) / len(raw_sources)
            if raw_sources else 1.0
        )

        word_count = len(text.split())
        compression_ratio = len(text) / item["raw_length"] if item["raw_length"] > 0 else 0

        # Structure compliance
        text_upper = text.upper()
        has_key_findings = "KEY FINDINGS" in text_upper or "KEY FINDING" in text_upper
        has_sources_cited = "SOURCES CITED" in text_upper or "SOURCES" in text_upper

        return {
            "distilled": text[:1000],
            "distilled_length": len(text),
            "word_count": word_count,
            "word_count_compliant": word_count <= 700,  # 600 target + 100 margin
            "compression_ratio": round(compression_ratio, 3),
            "number_retention": round(number_retention, 3),
            "source_retention": round(source_retention, 3),
            "has_key_findings": has_key_findings,
            "has_sources_cited": has_sources_cited,
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "error": None,
        }
    except Exception as e:
        return {
            "distilled": "",
            "distilled_length": 0,
            "word_count": 0,
            "word_count_compliant": False,
            "compression_ratio": 0,
            "number_retention": 0,
            "source_retention": 0,
            "has_key_findings": False,
            "has_sources_cited": False,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "error": str(e),
        }


async def run_synthesizer_bench(
    item: Dict, router: ModelRouter, model_id: str, think, num_ctx: int
) -> Dict:
    """Run synthesizer benchmark on a single item."""
    # Build synthetic steps_with_results
    steps_with_results = f"""### step_1: Search documents for answer
Tool: smart_query
Status: Success
Result: {item['step_result_content'][:6000]}
"""

    prompt = ORCHESTRATOR_SYNTHESIZER_PROMPT.format(
        user_query=item["question"],
        plan_goal=f"Answer the research question: {item['question']}",
        user_context="(No user profile information available)",
        steps_with_results=steps_with_results,
    )

    t0 = time.time()
    try:
        response = await router.chat(
            model_identifier=model_id,
            messages=[
                {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0,
                "num_predict": BENCH_NUM_PREDICT["synthesizer"],
                "num_ctx": num_ctx,
            },
            think=think,
        )
        latency = time.time() - t0
        text = get_response_text(response)
        tokens_in, tokens_out = extract_tokens(response)

        if not text.strip():
            return {
                "answer": "",
                "answer_length": 0,
                "latency_s": round(latency, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "judge_scores": None,
                "error": "Empty response",
            }

        return {
            "answer": text,
            "answer_length": len(text),
            "latency_s": round(latency, 2),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "judge_scores": None,  # Filled in by judge pass
            "error": None,
        }
    except Exception as e:
        return {
            "answer": "",
            "answer_length": 0,
            "latency_s": round(time.time() - t0, 2),
            "tokens_in": 0,
            "tokens_out": 0,
            "judge_scores": None,
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────────
# Metric Computers
# ─────────────────────────────────────────────────────────────

def compute_analyzer_metrics(results: List[Dict]) -> Dict:
    """Compute aggregate metrics for analyzer benchmark."""
    valid = [r for r in results if not r.get("error")]
    if not valid:
        return {"n": 0, "error": "No valid results"}

    n = len(valid)
    decision_correct = sum(1 for r in valid if r["decision_correct"])
    json_valid = sum(1 for r in valid if r["json_valid"])

    # Edge case accuracy
    edge_results = [r for r in valid if r.get("_source") == "edge_case"]
    edge_correct = sum(1 for r in edge_results if r["decision_correct"]) if edge_results else 0

    latencies = [r["latency_s"] for r in valid]
    tokens_in = sum(r["tokens_in"] for r in valid)
    tokens_out = sum(r["tokens_out"] for r in valid)

    return {
        "n": n,
        "decision_accuracy": round(decision_correct / n, 4),
        "json_validity": round(json_valid / n, 4),
        "edge_case_n": len(edge_results),
        "edge_case_accuracy": round(edge_correct / len(edge_results), 4) if edge_results else None,
        "mean_latency_s": round(statistics.mean(latencies), 2),
        "median_latency_s": round(statistics.median(latencies), 2),
        "total_tokens_in": tokens_in,
        "total_tokens_out": tokens_out,
        "mean_tokens_out": round(tokens_out / n, 1),
    }


def compute_planner_metrics(results: List[Dict]) -> Dict:
    """Compute aggregate metrics for planner benchmark."""
    valid = [r for r in results if not r.get("error")]
    if not valid:
        return {"n": 0, "error": "No valid results"}

    n = len(valid)
    json_valid = sum(1 for r in valid if r["json_valid"])
    tool_correct = sum(1 for r in valid if r["tool_correct"])
    agent_correct = sum(1 for r in valid if r["agent_correct"])
    no_placeholders = sum(1 for r in valid if not r["has_placeholders"])
    smart_routing = sum(1 for r in valid if r["uses_smart_query_routing"])

    step_counts = [r["step_count"] for r in valid if r["json_valid"]]
    efficiencies = [r.get("step_efficiency", 1.0) for r in valid if r["json_valid"] and r.get("step_efficiency")]

    latencies = [r["latency_s"] for r in valid]
    tokens_in = sum(r["tokens_in"] for r in valid)
    tokens_out = sum(r["tokens_out"] for r in valid)

    return {
        "n": n,
        "json_validity": round(json_valid / n, 4),
        "tool_accuracy": round(tool_correct / n, 4),
        "agent_accuracy": round(agent_correct / n, 4),
        "arg_completeness": round(no_placeholders / n, 4),
        "constraint_compliance": round(smart_routing / n, 4),
        "mean_steps": round(statistics.mean(step_counts), 2) if step_counts else 0,
        "mean_step_efficiency": round(statistics.mean(efficiencies), 2) if efficiencies else 0,
        "mean_latency_s": round(statistics.mean(latencies), 2),
        "median_latency_s": round(statistics.median(latencies), 2),
        "total_tokens_in": tokens_in,
        "total_tokens_out": tokens_out,
    }


def compute_supervisor_metrics(results: List[Dict]) -> Dict:
    """Compute aggregate metrics for supervisor benchmark."""
    valid = [r for r in results if not r.get("error")]
    if not valid:
        return {"n": 0, "error": "No valid results"}

    n = len(valid)
    json_valid = sum(1 for r in valid if r["json_valid"])
    score_valid = sum(1 for r in valid if r.get("score_valid"))

    # Correlation between supervisor score and judge correctness
    scored = [
        r for r in valid
        if r.get("quality_score") is not None and r.get("_judge_correctness") is not None
    ]

    spearman_rho = None
    if len(scored) >= 10:
        try:
            from scipy.stats import spearmanr
            scores = [r["quality_score"] for r in scored]
            judges = [r["_judge_correctness"] for r in scored]
            rho, p_val = spearmanr(scores, judges)
            spearman_rho = round(rho, 4)
        except ImportError:
            pass

    # Retry precision/recall
    retry_decisions = [r for r in valid if r.get("should_retry") is not None]
    retried_bad = sum(
        1 for r in retry_decisions
        if r["should_retry"] and r.get("_expected_quality") == "bad"
    )
    retried_total = sum(1 for r in retry_decisions if r["should_retry"])
    bad_total = sum(1 for r in retry_decisions if r.get("_expected_quality") == "bad")
    bad_retried = sum(
        1 for r in retry_decisions
        if r.get("_expected_quality") == "bad" and r["should_retry"]
    )

    retry_precision = round(retried_bad / retried_total, 4) if retried_total > 0 else None
    retry_recall = round(bad_retried / bad_total, 4) if bad_total > 0 else None

    latencies = [r["latency_s"] for r in valid]
    tokens_in = sum(r["tokens_in"] for r in valid)
    tokens_out = sum(r["tokens_out"] for r in valid)

    return {
        "n": n,
        "json_validity": round(json_valid / n, 4),
        "score_validity": round(score_valid / n, 4) if score_valid else 0,
        "score_judge_spearman": spearman_rho,
        "retry_precision": retry_precision,
        "retry_recall": retry_recall,
        "mean_latency_s": round(statistics.mean(latencies), 2),
        "median_latency_s": round(statistics.median(latencies), 2),
        "total_tokens_in": tokens_in,
        "total_tokens_out": tokens_out,
    }


def compute_distiller_metrics(results: List[Dict]) -> Dict:
    """Compute aggregate metrics for distiller benchmark."""
    valid = [r for r in results if not r.get("error")]
    if not valid:
        return {"n": 0, "error": "No valid results"}

    n = len(valid)
    number_retentions = [r["number_retention"] for r in valid]
    source_retentions = [r["source_retention"] for r in valid]
    compressions = [r["compression_ratio"] for r in valid if r["compression_ratio"] > 0]
    word_compliant = sum(1 for r in valid if r["word_count_compliant"])
    has_kf = sum(1 for r in valid if r["has_key_findings"])
    has_sc = sum(1 for r in valid if r["has_sources_cited"])

    latencies = [r["latency_s"] for r in valid]
    tokens_in = sum(r["tokens_in"] for r in valid)
    tokens_out = sum(r["tokens_out"] for r in valid)

    return {
        "n": n,
        "mean_number_retention": round(statistics.mean(number_retentions), 4),
        "mean_source_retention": round(statistics.mean(source_retentions), 4),
        "mean_compression_ratio": round(statistics.mean(compressions), 4) if compressions else 0,
        "word_count_compliance": round(word_compliant / n, 4),
        "structure_key_findings": round(has_kf / n, 4),
        "structure_sources_cited": round(has_sc / n, 4),
        "mean_latency_s": round(statistics.mean(latencies), 2),
        "median_latency_s": round(statistics.median(latencies), 2),
        "total_tokens_in": tokens_in,
        "total_tokens_out": tokens_out,
    }


def compute_synthesizer_metrics(results: List[Dict]) -> Dict:
    """Compute aggregate metrics for synthesizer benchmark."""
    valid = [r for r in results if not r.get("error")]
    if not valid:
        return {"n": 0, "error": "No valid results"}

    n = len(valid)

    # Judge scores (if available)
    judged = [r for r in valid if r.get("judge_scores")]
    answerable_judged = [r for r in judged if r.get("_answerable", True)]
    ood_judged = [r for r in judged if not r.get("_answerable", True)]

    correctness_scores = [
        r["judge_scores"]["correctness"] for r in answerable_judged
        if "correctness" in r.get("judge_scores", {})
    ]
    pass_rate = (
        round(sum(1 for s in correctness_scores if s >= 3) / len(correctness_scores), 4)
        if correctness_scores else None
    )
    mean_correctness = (
        round(statistics.mean(correctness_scores), 3)
        if correctness_scores else None
    )

    # OOD refusal
    ood_refusals = [
        r["judge_scores"].get("refusal_accuracy", 0) for r in ood_judged
        if r.get("judge_scores")
    ]
    ood_refusal_rate = (
        round(sum(1 for s in ood_refusals if s >= 3) / len(ood_refusals), 4)
        if ood_refusals else None
    )

    latencies = [r["latency_s"] for r in valid]
    tokens_in = sum(r["tokens_in"] for r in valid)
    tokens_out = sum(r["tokens_out"] for r in valid)

    return {
        "n": n,
        "n_judged": len(judged),
        "pass_rate": pass_rate,
        "mean_correctness": mean_correctness,
        "ood_refusal_rate": ood_refusal_rate,
        "mean_latency_s": round(statistics.mean(latencies), 2),
        "median_latency_s": round(statistics.median(latencies), 2),
        "total_tokens_in": tokens_in,
        "total_tokens_out": tokens_out,
    }


# ─────────────────────────────────────────────────────────────
# Main Benchmark Runner
# ─────────────────────────────────────────────────────────────

BENCH_RUNNERS = {
    "analyzer": run_analyzer_bench,
    "planner": run_planner_bench,
    "supervisor": run_supervisor_bench,
    "distiller": run_distiller_bench,
    "synthesizer": run_synthesizer_bench,
}

BENCH_METRICS = {
    "analyzer": compute_analyzer_metrics,
    "planner": compute_planner_metrics,
    "supervisor": compute_supervisor_metrics,
    "distiller": compute_distiller_metrics,
    "synthesizer": compute_synthesizer_metrics,
}


async def run_benchmark(
    benchmark_name: str,
    dataset: List[Dict],
    model_entries: List[Tuple[str, str, List]],
    router: ModelRouter,
    args,
) -> Dict:
    """Run a complete benchmark across all model variants."""
    runner = BENCH_RUNNERS[benchmark_name]
    metrics_fn = BENCH_METRICS[benchmark_name]
    num_ctx = BENCH_NUM_CTX[benchmark_name]

    max_items = args.max_items or len(dataset)
    dataset = dataset[:max_items]

    all_results = {}
    summary = {}

    for model_id, size_label, think_variants in model_entries:
        for think in think_variants:
            mk = model_key(model_id, think)
            inter_path = RESULTS_DIR / f"v4_7_bench_{benchmark_name}_{mk}.json"

            # Resume support
            if args.resume and inter_path.exists():
                inter_data = load_intermediate(inter_path)
                results = inter_data.get("results", [])
                completed = set(inter_data.get("completed_keys", []))
                logger.info(f"Resuming {mk}: {len(completed)} already done")
            else:
                results = []
                completed = set()

            think_label = f"think={think}" if think is not False else "think=off"
            logger.info(
                f"\n{'='*60}\n"
                f"Benchmark: {benchmark_name} | Model: {model_id} ({size_label}) | {think_label}\n"
                f"Dataset: {len(dataset)} items | Completed: {len(completed)}\n"
                f"{'='*60}"
            )

            for i, item in enumerate(dataset):
                # Use index-qualified key to handle duplicate question_ids
                # (supervisor: same Q with different configs; distiller: same Q with different RLM outputs)
                base_key = item.get("question_id", item.get("query", f"item_{i}"))
                item_key = f"{base_key}_{i}"
                rk = result_key(mk, str(item_key))
                if rk in completed:
                    continue

                try:
                    result = await runner(item, router, model_id, think, num_ctx)
                except Exception as e:
                    logger.error(f"Runner error on {item_key}: {e}")
                    result = {"error": str(e)}

                # Attach metadata
                result["model_key"] = mk
                result["model_id"] = model_id
                result["size_label"] = size_label
                result["think"] = str(think)
                result["item_key"] = str(item_key)
                result["benchmark"] = benchmark_name

                # Attach source info for metrics
                if benchmark_name == "analyzer":
                    result["_source"] = item.get("source", "")
                elif benchmark_name == "supervisor":
                    result["_judge_correctness"] = item.get("judge_correctness")
                    result["_expected_quality"] = item.get("expected_quality")
                elif benchmark_name == "synthesizer":
                    result["_answerable"] = item.get("answerable", True)

                results.append(result)
                completed.add(rk)

                # Progress logging
                done = len(completed)
                total = len(dataset)
                if done % 10 == 0 or done == total:
                    logger.info(f"  [{mk}] {done}/{total} complete")

                # Save intermediate every 25 items
                if done % 25 == 0:
                    save_intermediate(
                        {"results": results, "completed_keys": list(completed)},
                        inter_path,
                    )

            # Save final per-model results
            save_intermediate(
                {"results": results, "completed_keys": list(completed)},
                inter_path,
            )

            # Compute metrics for this model variant
            model_metrics = metrics_fn(results)
            model_metrics["model_key"] = mk
            model_metrics["model_id"] = model_id
            model_metrics["size_label"] = size_label
            model_metrics["think"] = str(think)
            summary[mk] = model_metrics
            all_results[mk] = results

            logger.info(f"  Metrics for {mk}: {json.dumps(model_metrics, indent=2)}")

    return {
        "benchmark": benchmark_name,
        "timestamp": datetime.now().isoformat(),
        "n_models": len(summary),
        "n_items": len(dataset),
        "summary": summary,
    }


async def judge_synthesizer_results(
    benchmark_results: Dict,
    dataset: List[Dict],
    router: ModelRouter,
) -> Dict:
    """Run judge scoring on synthesizer benchmark results."""
    gt_by_id = {d["question_id"]: d for d in dataset}
    summary = benchmark_results.get("summary", {})

    for mk, metrics in summary.items():
        inter_path = RESULTS_DIR / f"v4_7_bench_synthesizer_{mk}.json"
        if not inter_path.exists():
            continue

        inter_data = load_intermediate(inter_path)
        results = inter_data.get("results", [])
        judged_count = 0

        for r in results:
            if r.get("judge_scores") is not None:
                continue
            if r.get("error") or not r.get("answer"):
                continue

            item_key = r.get("item_key", "")
            gt = gt_by_id.get(item_key, {})
            answerable = gt.get("answerable", True)

            try:
                scores = await judge_answer(
                    question=gt.get("question", r.get("_question", "")),
                    expected=gt.get("expected_answer", ""),
                    concepts=gt.get("expected_concepts", []),
                    generated=r["answer"],
                    router=router,
                    answerable=answerable,
                )
                r["judge_scores"] = scores
                judged_count += 1
            except Exception as e:
                logger.error(f"Judge error for {item_key}: {e}")
                r["judge_scores"] = {"error": str(e)}

            if judged_count % 10 == 0:
                save_intermediate(
                    {"results": results, "completed_keys": inter_data.get("completed_keys", [])},
                    inter_path,
                )

        # Final save
        save_intermediate(
            {"results": results, "completed_keys": inter_data.get("completed_keys", [])},
            inter_path,
        )

        # Recompute metrics with judge scores
        metrics_fn = BENCH_METRICS["synthesizer"]
        # Attach _answerable from dataset
        for r in results:
            item_key = r.get("item_key", "")
            gt = gt_by_id.get(item_key, {})
            r["_answerable"] = gt.get("answerable", True)

        new_metrics = metrics_fn(results)
        new_metrics["model_key"] = mk
        new_metrics["model_id"] = metrics.get("model_id")
        new_metrics["size_label"] = metrics.get("size_label")
        new_metrics["think"] = metrics.get("think")
        summary[mk] = new_metrics

        logger.info(f"  Judged {judged_count} results for {mk}")

    return benchmark_results


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="V4-7: Component-Level Orchestrator Benchmarks"
    )
    parser.add_argument(
        "--benchmark", "-b",
        choices=BENCHMARK_NAMES + ["all"],
        default="all",
        help="Which benchmark to run (default: all)",
    )
    parser.add_argument(
        "--models", "-m",
        type=str,
        default=None,
        help="Comma-separated model name filters (e.g. 'qwen3-coder,gemma3')",
    )
    parser.add_argument(
        "--max-items", "-n",
        type=int,
        default=None,
        help="Max dataset items per benchmark (for smoke testing)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Ollama port (overrides OLLAMA_BASE_URL)",
    )
    parser.add_argument(
        "--build-dataset",
        action="store_true",
        help="Generate datasets only (no model calls)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from intermediate results",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip judge scoring for synthesizer benchmark",
    )
    args = parser.parse_args()

    # Set Ollama port
    if args.port:
        os.environ["OLLAMA_BASE_URL"] = f"http://localhost:{args.port}"
        logger.info(f"Using Ollama port: {args.port}")

    # Load data
    logger.info("Loading ground truth and V4-4 results...")
    gt_questions = load_ground_truth(GROUND_TRUTH_PATH)
    logger.info(f"Ground truth: {len(gt_questions)} questions")

    v4_4_results = []
    if V4_4_RESULTS_PATH.exists():
        with open(V4_4_RESULTS_PATH) as f:
            v4_4_data = json.load(f)
        v4_4_results = v4_4_data.get("per_question_results", [])
        logger.info(f"V4-4 results: {len(v4_4_results)} items")
    else:
        logger.warning(f"V4-4 results not found at {V4_4_RESULTS_PATH}")

    # Determine which benchmarks to run
    if args.benchmark == "all":
        benchmarks = BENCHMARK_NAMES
    else:
        benchmarks = [args.benchmark]

    # Build datasets
    datasets = {}
    for bench in benchmarks:
        if bench == "analyzer":
            datasets[bench] = build_analyzer_dataset(gt_questions)
        elif bench == "planner":
            datasets[bench] = build_planner_dataset(gt_questions)
        elif bench == "supervisor":
            if not v4_4_results:
                logger.error("Supervisor benchmark requires V4-4 results")
                continue
            datasets[bench] = build_supervisor_dataset(v4_4_results)
        elif bench == "distiller":
            if not v4_4_results:
                logger.error("Distiller benchmark requires V4-4 results")
                continue
            datasets[bench] = build_distiller_dataset(v4_4_results)
        elif bench == "synthesizer":
            if not v4_4_results:
                logger.error("Synthesizer benchmark requires V4-4 results")
                continue
            datasets[bench] = build_synthesizer_dataset(v4_4_results, gt_questions)

    if args.build_dataset:
        # Save datasets and exit
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        for bench, ds in datasets.items():
            path = RESULTS_DIR / f"v4_7_bench_{bench}_dataset.json"
            with open(path, "w") as f:
                json.dump(ds, f, indent=2, default=str)
            logger.info(f"Saved {bench} dataset: {len(ds)} items -> {path}")
        logger.info("Dataset generation complete. Use without --build-dataset to run benchmarks.")
        return

    # Configure Gemini if needed
    model_entries = filter_model_matrix(args.models)
    has_gemini = any("gemini" in m[0] for m in model_entries)
    if has_gemini:
        if not configure_gemini_from_admin():
            logger.warning("Gemini not configured — Gemini model variants will fail")

    # Initialize router
    router = ModelRouter()

    # Run benchmarks
    all_summaries = {}
    for bench in benchmarks:
        if bench not in datasets:
            continue

        logger.info(f"\n{'#'*60}\n# BENCHMARK: {bench.upper()}\n{'#'*60}")
        result = await run_benchmark(bench, datasets[bench], model_entries, router, args)

        # Judge synthesizer results
        if bench == "synthesizer" and not args.skip_judge:
            logger.info("Running judge scoring on synthesizer results...")
            result = await judge_synthesizer_results(result, datasets[bench], router)

        all_summaries[bench] = result

        # Save per-benchmark summary
        save_final_results(result, f"v4_7_bench_{bench}")
        logger.info(f"Benchmark {bench} complete: {result.get('n_models', 0)} model variants")

    # Save cross-benchmark summary
    if len(all_summaries) > 1:
        cross_summary = {
            "experiment": "v4_7_component_bench",
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {
                bench: {
                    "n_models": data.get("n_models", 0),
                    "n_items": data.get("n_items", 0),
                    "summary": data.get("summary", {}),
                }
                for bench, data in all_summaries.items()
            },
        }
        save_final_results(cross_summary, "v4_7_bench_summary")

    # Print final summary table
    print("\n" + "=" * 80)
    print("V4-7 COMPONENT BENCHMARK RESULTS")
    print("=" * 80)
    for bench, data in all_summaries.items():
        print(f"\n--- {bench.upper()} ---")
        for mk, metrics in data.get("summary", {}).items():
            key_metric = _key_metric_for_bench(bench, metrics)
            print(f"  {mk:45s}  {key_metric}")

    print("\nDone.")


def _key_metric_for_bench(bench: str, metrics: Dict) -> str:
    """Format the key metric for summary display."""
    if bench == "analyzer":
        acc = metrics.get("decision_accuracy", 0)
        lat = metrics.get("mean_latency_s", 0)
        return f"accuracy={acc:.1%}  latency={lat:.1f}s"
    elif bench == "planner":
        tool = metrics.get("tool_accuracy", 0)
        jv = metrics.get("json_validity", 0)
        lat = metrics.get("mean_latency_s", 0)
        return f"tool_acc={tool:.1%}  json={jv:.1%}  latency={lat:.1f}s"
    elif bench == "supervisor":
        rho = metrics.get("score_judge_spearman", "N/A")
        jv = metrics.get("json_validity", 0)
        lat = metrics.get("mean_latency_s", 0)
        return f"rho={rho}  json={jv:.1%}  latency={lat:.1f}s"
    elif bench == "distiller":
        nr = metrics.get("mean_number_retention", 0)
        wc = metrics.get("word_count_compliance", 0)
        lat = metrics.get("mean_latency_s", 0)
        return f"num_ret={nr:.1%}  word_ok={wc:.1%}  latency={lat:.1f}s"
    elif bench == "synthesizer":
        pr = metrics.get("pass_rate")
        lat = metrics.get("mean_latency_s", 0)
        pr_str = f"{pr:.1%}" if pr is not None else "N/A"
        return f"pass_rate={pr_str}  latency={lat:.1f}s"
    return str(metrics)


if __name__ == "__main__":
    asyncio.run(main())
