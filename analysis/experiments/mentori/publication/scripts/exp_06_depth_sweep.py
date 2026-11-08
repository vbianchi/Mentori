#!/usr/bin/env python3
"""
V4-9: RLM Depth Sweep — Fine-grained saturation curve
======================================================

Generates RLM answers at 10+ depths (turn caps) on a stratified question subset, for the saturation curve of
Figure 3. Supports resume. One attempt per answer (Q29): a failed answer is stored with its error and the RLM's
record (stop_reason, rlm) and counts as done; it is never regenerated.

Runs under the lock (step 3, A9). Generator gemini::gemini-3-flash-preview (D27; the --model flag is gone). Three
draws, 1, 2, 3 (D78 Q116, which replaced D49's one draw for Figure 3; experiment.draws(3)), in the order draw, then
question, then depth, so draw 1 is done at every depth before draw 2 starts. Questions (--question-set): depth_sweep86 (the default, G5; D75 Q50) is the submitted sweep's 88
questions less CD_015 and SY_010, the same named set as the authors' RLM depth sweep
(experiments/rlm_ref/run_rlm_ref.py depth_sweep86_questions); per_category (T1, which keeps the submitted 15) is
this script's own rule on the 135 of answer key v2.4 (D48, experiments/runner/experiment.py questions()):
answerable questions only, grouped by category (factual_recall, conceptual, technical, cross_document, synthesis),
the first --n-questions / 5 of each in the key's order (those with min_core <= 20 first, which on the 135 is every
answerable one). Each depth is one run, findings/runs/<run_id>/ with run_id
exp_06_depth_sweep__rlm_<depth>__<set> (depthsweep86, or percategory<n>), and every (question, draw) of it runs in
its own run context. Each set has its own runs and results files, so neither resumes into the other. An answer is
keyed by rlm_<depth>|question_id|d<draw> (experiment.answer_key; the old key question_id|d<depth> wrote the depth
where the draw now goes). --base-url is the run contexts' Ollama server (the old
--port set OLLAMA_BASE_URL after backend.config had read it, so it changed nothing: calls.md B7); a Gemini run never
contacts it. Answers are stored unscored: the judge (A7), concept recall and citation coverage run in a separate
step on the stored answers (the v2.4 key carries key_concepts phrases and no source_files, not the v4 key's
expected_concepts and source_files). Each start appends the index's identity (collection and content hashes,
experiments/runner/index_identity.py) to <sink>/index_identity.jsonl of every depth with an answer to make, so the
passages_seen ids resolve to their text (F5).

A question filter (D112 Q11, G7). --question-ids-file runs only the set's questions a JSON file names (D98's subset,
findings/recompute/D98_subset/d98_subset.json: 45 of the 135, of which depth_sweep86 holds 29), --question-ids the ones
named; filter_questions says what is refused. The filter changes no run name, answer key or results-file name, so draws
2 and 3 of the subset resume into the runs and files of draw 1; it is applied before --part cuts the shares, and the
results files record it ("question_filter"). With --part, a share's files hold its kept questions' rows only.

Several processes (D95 Q213). --part k/n runs share k of n of the questions (experiment.share: dealt round robin in the
set's order, so the n shares are disjoint and together hold every question once), each answer exactly as one process
would run it (same run context, settings and seed: the seed is the draw). --draws runs only the draws named, so a
queue can finish a draw on every share before the next starts (D78 Q116's order across processes;
findings/recompute/G5_runs/g5_queue.sh). A share's results files carry "_part<k>of<n>" before the time, so no two
processes write one file, and hold the rows of that share's questions only (every draw; the union over the files is
the answer set, as before). Every results file is written whole under a temporary name and moved into place, so a
reader (another share's resume, check_g5.py) never reads half of one and a stop never leaves one cut. --stop-file
names a file whose presence stops the run before its next answer (the answers stored so far kept, exit code 3).

A local generator (D97, T1: the depth sweep of the local models behind Figure 3b and 3c). --generator ollama::<tag>
runs the RLM with that model, every call under the lock as a generator (the tag that runs, the date-fixed copy where
[date] names one, must have a digest in [models]; its thinking is the maker's default, D66) and sent to --base-url,
which is then the server that answers. Without --generator the generator is gemini::gemini-3-flash-preview and
nothing of G5 changes: its runs, files and answer keys keep their names. With it, "+<tag>" (':' and '/' written '-',
as S2 names its variants) follows the set's name in every run_id and results-file prefix, and the smoke's
(exp_06_depth_sweep__rlm_<depth>__percategory15+gemma3-27b, ...__smoke+gemma3-27b), so each generator has its own
runs and files and no generator resumes into another's. A model the lock does not run as a generator is refused
before anything is read or written.

Usage:
    # Work list only (no database, no model call, nothing written)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py --dry-run

    # Smoke test (2 questions × 2 depths, depths 1 and 5, × the 3 draws)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --smoke

    # Smoke test at the depths named (--depths with --smoke): the same 2 questions and own runs and files, at every
    # depth the run reaches (G5's smoke, findings/recompute/G5_runs)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --smoke --depths 1 2 3 5 7 10 15 20 30 50

    # Full run
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441

    # Custom depths
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --depths 1 3 5 10 20 40

    # D98's subset only, draws 2 and 3, share 1 of 4 (G7, D112 Q11)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --resume --draws 2 3 --part 1/4 \\
        --question-ids-file findings/recompute/D98_subset/d98_subset.json

    # Resume interrupted run
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --resume

    # Share 2 of 4 of the questions, draw 1 only, stopping before the next answer when STOP exists (G5's queue)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:21441 --resume --part 2/4 --draws 1 --stop-file findings/recompute/G5_runs/STOP

    # T1 (D97): a local generator on the 15 per-category questions, draw 1, on the server that answers
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py \\
        --base-url http://127.0.0.1:11434 --generator ollama::gemma3:27b --question-set per_category --draws 1 --resume
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlsplit

# Project path setup
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.agents.model_router import ModelRouter
from backend.retrieval.rlm.orchestrator import RLMOrchestrator, RLMRunError
from backend.retrieval.rlm.context import RLMContext
from backend.retrieval.rlm.executor import SETUP_ERRORS

from exp_common import (
    find_admin_user_id,
    GEN_MODEL,
)
# exp_common imports backend.agents.lock_adapter, which puts the reanalysis repository on sys.path
from experiments.runner import experiment as ex
from experiments.runner import index_identity
from experiments.runner import run_context as rc
from experiments.rlm_ref.run_rlm_ref import depth_sweep86_questions, DEPTH_SWEEP_SIZE   # D75 Q50

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_06_depth_sweep")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

RESULTS_DIR = Path(__file__).resolve().parent / "results_v4"
INDEX_NAME = "exp_v4_s20_n0"
EXPERIMENT = "exp_06_depth_sweep"     # the first part of every run_id of this script
FIGURE = 3
DRAWS = ex.draws(FIGURE)              # (1, 2, 3): three draws for Figure 3 (D78 Q116; D49 had one)
MODEL = GEN_MODEL                     # gemini::gemini-3-flash-preview (D27)
MODELS = {"generator": MODEL}         # the run contexts' agent_roles: the RLM's one model
LOCAL = "ollama::"                    # D97 (T1): --generator ollama::<tag>, a local model under the lock

DEFAULT_DEPTHS = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50]
SMOKE_DEPTHS = [1, 5]
STOPPED_EXIT = 3                      # the exit code of a run stopped by --stop-file before its next answer

# D75 Q50: the question sets. depth_sweep86 is the named set (experiments/rlm_ref/run_rlm_ref.py, with the deposit's
# path and sha256), shared with the authors' RLM; per_category is this script's rule, kept for T1 (15 questions)
QUESTION_SETS = ("depth_sweep86", "per_category")
PER_CATEGORY_DEFAULT_N = 15

# Stratified question selection (per_category): 3 per category from answerable questions
CATEGORIES_TO_SAMPLE = {
    "factual_recall": 3,
    "conceptual": 3,
    "technical": 3,
    "cross_document": 3,
    "synthesis": 3,
}

# Q29 (D68, limits #144): one attempt per answer. MAX_RETRIES = 3 reran the whole RLM run on any exception, the run
# that ends at the turn cap with nothing included, so failed runs were re-sampled; retries happen only at the call
# level (the Gemini client's rule, every attempt in the call record).


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class DepthResult:
    """Result from a single (question, depth) evaluation."""
    question_id: str
    question: str
    category: str
    depth: int
    model: str
    answer: str
    latency_s: float
    llm_calls: int
    tokens_used: int
    retrieved_passages: int
    error: Optional[str] = None
    # Filled after judging
    judge_scores: Optional[Dict[str, Any]] = None
    # Filled after citation evaluation
    citation_metrics: Optional[Dict[str, Any]] = None
    # Filled after concept recall computation
    concept_recall: Optional[float] = None


# ─────────────────────────────────────────────────────────────
# Question selection
# ─────────────────────────────────────────────────────────────

def select_questions(n_per_category: Dict[str, int], smoke: bool = False) -> List[Dict]:
    """Select stratified questions from the 135 of answer key v2.4 (D48): the answerable ones, in the key's order.
    The key has no difficulty field, so the smoke test takes the first 2."""
    questions = [q for q in ex.questions() if q["answerable"]]

    if smoke:
        # Just pick 2 easy questions for smoke test
        easy = [q for q in questions if q.get("difficulty") == "easy"]
        if len(easy) < 2:
            easy = questions[:2]
        return easy[:2]

    selected = []
    by_category = {}
    for q in questions:
        cat = q.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)

    for cat, n in n_per_category.items():
        pool = by_category.get(cat, [])
        if not pool:
            logger.warning(f"No questions for category '{cat}'")
            continue
        # Prefer questions with min_core <= 20 (available in our index)
        eligible = [q for q in pool if q.get("min_core", 999) <= 20]
        if not eligible:
            eligible = pool
        # Take first n (deterministic for reproducibility)
        selected.extend(eligible[:n])

    logger.info(f"Selected {len(selected)} questions across {len(n_per_category)} categories")
    return selected


# ─────────────────────────────────────────────────────────────
# Citation evaluation (from deleted exp1, reconstructed)
# ─────────────────────────────────────────────────────────────

def evaluate_citations(answer: str, expected_sources: List[str]) -> Dict[str, Any]:
    """Extract and evaluate citations from generated answers."""
    # Pattern 1: [source_file:page]
    inline = re.findall(r'\[([^\]]+\.pdf):(?:p(?:age)?)?(\d+)\]', answer, re.IGNORECASE)
    # Pattern 2: Numbered [N]
    numbered = re.findall(r'\[(\d+)\]', answer)
    # Pattern 3: Source lines
    source_lines = re.findall(r'(\S+\.pdf),?\s*page\s*(\d+)', answer, re.IGNORECASE)

    sources_found = set()
    total_citations = 0
    for source, _ in inline:
        sources_found.add(source)
        total_citations += 1
    for source, _ in source_lines:
        sources_found.add(source)
    total_citations += len(numbered)

    word_count = len(answer.split())
    density = (total_citations / max(word_count, 1)) * 100

    if expected_sources:
        covered = sum(
            1 for s in expected_sources
            if any(s.lower() in found.lower() for found in sources_found)
        )
        coverage = covered / len(expected_sources)
    else:
        coverage = 0.0

    return {
        "total_citations": total_citations,
        "unique_sources": len(sources_found),
        "citation_density": round(density, 2),
        "source_coverage": round(coverage, 2),
    }


# ─────────────────────────────────────────────────────────────
# Concept recall computation
# ─────────────────────────────────────────────────────────────

def compute_concept_recall(answer: str, expected_concepts: List[str]) -> float:
    """Compute fraction of expected concepts found in the answer."""
    if not expected_concepts:
        return 0.0
    answer_lower = answer.lower()
    found = 0
    for concept in expected_concepts:
        # Exact match or fuzzy (concept as substring)
        if concept.lower() in answer_lower:
            found += 1
    return round(found / len(expected_concepts), 4)


# ─────────────────────────────────────────────────────────────
# RLM execution, one attempt
# ─────────────────────────────────────────────────────────────

async def run_rlm(
    question: str,
    router: ModelRouter,
    model: str,
    user_id: str,
    depth: int,
    index_name: str,
) -> Dict[str, Any]:
    """Run the RLM once at a given depth (Q29, D68: no whole-answer retry).

    Returns the answer and the run's record: rlm is RLMResult.metadata (or RLMRunError.metadata for a run that ended
    with no answer: stop_reason max_turns_empty or call_error, stored with answer "" and the error, A5). setup_s is
    loading the index (and, on the first answer, the reranker), latency_s the RLM run alone (rlm F22). Setup is not
    caught: a failed index load or reranker load (D40) and a LockError or RunContextError (Q38) mean the run's own
    setup is wrong, so the script stops and nothing is stored for the answer (a stored error would count as done on
    resume). Q73 (D75): any other exception of the RLM run also stops the script with nothing stored: every outcome
    the RLM is built to produce is an answer or an RLMRunError, so anything else is our code doing something
    unplanned, to be looked at before it counts (resume runs the answer again)."""
    t0 = time.time()
    context = await RLMContext.from_index(
        index_name=index_name,
        user_id=user_id,
    )
    setup_s = time.time() - t0
    orchestrator = RLMOrchestrator(
        model_router=router,
        model_identifier=model,
        max_turns=depth,
        verify=False,
        think=False,
    )
    t1 = time.time()
    answer, rlm, error = "", None, None
    try:
        result = await orchestrator.run(task=question, context=context)
        answer, rlm = str(result), result.metadata
    except RLMRunError as e:
        rlm = e.metadata
        error = f"{rlm['stop_reason']}: {e}"
    # Q73 (D75): nothing else is caught (SETUP_ERRORS included): the script stops, the answer is not stored
    latency = time.time() - t1

    return {
        "answer": answer,
        "setup_s": setup_s,
        "latency_s": latency,
        "llm_calls": context.llm_calls_made,
        "tokens_used": context.total_tokens_used,
        # D37 (records: it stored the citation count): the chunks returned to the code
        "retrieved_passages": len(rlm["passages_seen"]) if rlm else len(context.passages_seen),
        "stop_reason": rlm["stop_reason"] if rlm else None,
        "rlm": rlm,
        "error": error,
    }


# ─────────────────────────────────────────────────────────────
# Resume support
# ─────────────────────────────────────────────────────────────

def arm(depth: int) -> str:
    """The config (and run arm) of one depth: rlm_<depth>, as exp_02 names RLM-5, 10 and 20 by their turn cap."""
    return f"rlm_{depth}"


def set_tag(question_set: str, n_questions: Optional[int] = None) -> str:
    """The name a question set gives its runs and files: depthsweep86, or percategory<n> (D75 Q50)."""
    if question_set == "depth_sweep86":
        return "depthsweep86"
    if question_set == "per_category":
        return f"percategory{n_questions or PER_CATEGORY_DEFAULT_N}"
    raise SystemExit(f"--question-set {question_set!r}: one of {QUESTION_SETS}")


def generator_tag(model: str) -> str:
    """D97 (T1): "" for the default generator (G5: every name as before), else "+<tag>" with ':' and '/' written '-'
    (gemma3:27b -> "+gemma3-27b"), which follows the set's name and the smoke's in run_ids and results files."""
    if model == MODEL:
        return ""
    return "+" + re.sub(r"[:/]", "-", model[len(LOCAL):])


def check_generator(model: str) -> str:
    """--generator: the default (MODEL, G5) or ollama::<tag> that the lock runs as a generator: the tag that runs (the
    date-fixed copy where [date] names one) has a digest in [models] and the model a row in [sampling.models]
    (Lock.ollama, draw 1, the maker's default thinking, as every call of the run will ask). Anything else is refused
    here, before a database, a store or a results file is opened (D97)."""
    if model == MODEL:
        return model
    if not model.startswith(LOCAL) or not model[len(LOCAL):] or "[" in model or model != model.strip():
        raise SystemExit(f"--generator {model!r}: {MODEL} (the default) or ollama::<tag> (D97, T1); nothing run")
    from experiments.runner.lock import LockError, load
    try:
        load().ollama(model[len(LOCAL):], role="generator", draw=1)
    except LockError as e:
        raise SystemExit(f"--generator {model!r}: the lock does not run it as a generator ({e}); nothing run")
    return model


def run_name(depth: int, smoke: bool = False, tag: Optional[str] = None, gen: str = "") -> str:
    """The run_id of one depth: exp_06_depth_sweep__rlm_<depth>__<tag>, the tag naming the question set (and a local
    generator, D97). A smoke test is its own run (__smoke, __smoke<gen> for a local generator), so its answers never
    sit in a paper run under the paper's answer keys."""
    return ex.run_id(EXPERIMENT, arm(depth), f"smoke{gen}" if smoke else tag)


def file_prefix(smoke: bool = False, tag: Optional[str] = None, gen: str = "") -> str:
    """The results files' prefix, v4_9_depth_sweep_<tag> for a question set. A smoke test's (v4_9_depth_sweep_smoke_,
    v4_9_depth_sweep_smoke<gen>_ for a local generator, D97) is not matched by a paper run's resume and merge pattern,
    <prefix>_<model>*, nor is one set's by another's."""
    if smoke:
        return f"v4_9_depth_sweep_smoke{gen}"
    return f"v4_9_depth_sweep_{tag}" if tag else "v4_9_depth_sweep"


def result_key(question_id: str, depth: int, draw: int) -> str:
    """rlm_<depth>|question_id|d<draw> (experiment.answer_key)."""
    return ex.answer_key(arm(depth), question_id, draw)


def _rows(path: Path) -> List[Dict]:
    """The results of one results file. A row without an answer_key (made before the lock, keyed without its draw)
    refuses the file, so no such answer is resumed or merged."""
    with open(path) as f:
        rows = json.load(f).get("results", [])
    old = [r.get("question_id") for r in rows if "answer_key" not in r]
    if old:
        raise SystemExit(f"{path} holds {len(old)} answers without an answer_key (made before the lock, first "
                         f"{old[:3]}); it is not read")
    return rows


def load_existing_results(output_path: Path) -> Dict[str, DepthResult]:
    """Load existing results for resume."""
    if not output_path.exists():
        return {}
    return {r["answer_key"]: r for r in _rows(output_path)}


def server_suffix(base_url: Optional[str]) -> str:
    """The output-file suffix that keeps parallel runs apart: the server's host and port (the old port suffix)."""
    if not base_url:
        return ""
    return "_" + re.sub(r"[^A-Za-z0-9.]+", "-", urlsplit(base_url).netloc)


def select_draws(draws=None) -> tuple:
    """The draws a start runs: Figure 3's (DRAWS, D78 Q116), or those of them --draws names, in DRAWS order (as
    exp_02's select_draws). A draw that is not one of Figure 3's is refused."""
    if not draws:
        return tuple(DRAWS)
    unknown = sorted(set(draws) - set(DRAWS))
    if unknown:
        raise SystemExit(f"--draws {unknown}: Figure {FIGURE}'s draws are {DRAWS} (D78 Q116), nothing run")
    return tuple(d for d in DRAWS if d in set(draws))


def part_tag(part: Optional[str]) -> str:
    """The results files' share part, "_part<k>of<n>" (D95 Q213), or "" for one process over every question."""
    if not part:
        return ""
    k, n = ex.share_spec(part)
    return f"_part{k}of{n}"


def filter_questions(questions: List[Dict], ids=None, ids_file=None, known=None) -> tuple:
    """D112 Q11 (D98, G7): (the questions of the set that --question-ids or --question-ids-file names, in the set's
    order, not the order of the names; a record of the filter for the results files, or None without a filter).

    --question-ids: each id must be one of the set's questions (as exp_03's --question-ids), named once.
    --question-ids-file: a JSON file holding a list of ids, or an object whose "ids" is one
    (findings/recompute/D98_subset/d98_subset.json, written by scripts/S464_d98_subset.py). Each id must be one of the
    135 questions of answer key v2.4 (known; D48), named once; the set's questions among them are kept and the others
    are listed as outside the set, since D98's subset is drawn from the 135 (depth_sweep86 holds 29 of its 45).
    Refused before anything is read or written: both options, an unknown or repeated id, a file that is not such a
    JSON, a filter that keeps no question. Run names, answer keys and results-file names are the ones without the
    filter, so a later draw of the kept questions resumes into the runs and files of draw 1."""
    if ids and ids_file:
        raise SystemExit("--question-ids and --question-ids-file: name the questions one way; nothing run")
    if not ids and not ids_file:
        return questions, None
    in_set = [q["id"] for q in questions]
    record = {"option": "--question-ids" if ids else "--question-ids-file"}
    if ids_file:
        path = Path(ids_file)
        try:
            raw = path.read_bytes()
            data = json.loads(raw)
        except (OSError, ValueError) as e:
            raise SystemExit(f"--question-ids-file {path}: not a JSON file ({e}); nothing run")
        ids = data.get("ids") if isinstance(data, dict) else data
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
            raise SystemExit(f"--question-ids-file {path}: holds no list of question ids (a list, or an object "
                             f"with \"ids\"); nothing run")
        known = set(known if known is not None else (q["id"] for q in ex.questions()))
        unknown = [i for i in ids if i not in known]
        what = f"not among the {len(known)} questions (D48)"
        record.update(file=str(path), file_sha256=hashlib.sha256(raw).hexdigest())
    else:
        unknown = [i for i in ids if i not in set(in_set)]
        what = f"not among the set's {len(in_set)} questions"
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    if unknown or repeated:
        raise SystemExit(f"{record['option']}: {unknown[:5]} {what}; {repeated[:5]} named twice; nothing run")
    named = set(ids)
    kept = [q for q in questions if q["id"] in named]
    if not kept:
        raise SystemExit(f"{record['option']}: none of the {len(ids)} ids is one of the set's {len(in_set)} "
                         f"questions; nothing run")
    record.update(n_named=len(ids), n_kept=len(kept), n_set=len(in_set),
                  outside_set=sorted(named - set(in_set)))
    return kept, record


def work_list(questions: List[Dict], depths: List[int], completed: set, smoke: bool = False,
              tag: Optional[str] = None, draws=None, gen: str = "") -> List[Dict]:
    """One entry per (draw, question, depth), in run order, with done True where its key is completed. draws: the
    draws this start runs (select_draws; every draw of DRAWS when None). gen: generator_tag (D97)."""
    return [{"draw": draw, "question": q, "depth": depth, "key": result_key(q["id"], depth, draw),
             "run_id": run_name(depth, smoke, tag, gen),
             "done": result_key(q["id"], depth, draw) in completed}
            for draw in (draws or DRAWS) for q in questions for depth in depths]


def print_work_list(work: List[Dict], questions: List[Dict], depths: List[int], draws=None,
                    part: Optional[str] = None, model: str = MODEL) -> None:
    """The dry run: what a run would generate. No database, no model call, nothing written."""
    draws = draws or DRAWS
    print(f"{EXPERIMENT}: dry run (no database read, no model call, nothing written)")
    print(f"draws {DRAWS} (D78 Q116, Figure {FIGURE}); generator {model}; index {INDEX_NAME}; depths {depths}")
    if tuple(draws) != tuple(DRAWS):
        print(f"this start runs draws {tuple(draws)} only (--draws)")
    if part:
        print(f"share {part} of the questions (--part, D95 Q213): {len(questions)} questions")
    print(f"{len(questions)} questions:")
    for q in questions:
        print(f"  {q['id']:<28} {q['category']:<15} min_core {q['min_core']}")
    print(f"{'run_id':<45} {'draw':>4} {'pending':>7}  first pending answer key")
    for depth in depths:
        for draw in draws:
            run = next(w["run_id"] for w in work if w["depth"] == depth)
            pending = [w for w in work if w["depth"] == depth and w["draw"] == draw and not w["done"]]
            print(f"{run:<45} {draw:>4} {len(pending):>7}  "
                  f"{pending[0]['key'] if pending else '-'}")
    print(f"total: {sum(1 for w in work if not w['done'])} answers pending of {len(work)}")


# ─────────────────────────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────────────────────────

async def run_experiment(args):
    """Run the depth sweep experiment."""
    model = check_generator(getattr(args, "generator", None) or MODEL)   # D97: refused before anything is read
    gen = generator_tag(model)
    # D97: the run contexts' agent_roles for this run's generator (local, so the module's MODELS stays G5's default and
    # the context line below reads as it did)
    MODELS = {"generator": model}
    smoke = args.smoke
    # --depths when given; otherwise the smoke's 1 and 5, or the run's ten. A smoke given --depths runs those depths
    # (G5's smoke runs all ten, so the deep caps are reached before the run)
    depths = args.depths or (SMOKE_DEPTHS if smoke else DEFAULT_DEPTHS)

    if smoke:
        logger.info(f"SMOKE TEST MODE: 2 questions × {len(depths)} depths {depths}")

    # Select questions (D75 Q50: depth_sweep86 for G5, the named set both RLMs run; per_category for T1)
    tag = set_tag(args.question_set, args.n_questions) + gen
    if smoke:
        questions = select_questions(CATEGORIES_TO_SAMPLE, smoke=True)
    elif args.question_set == "depth_sweep86":
        if args.n_questions is not None and args.n_questions != DEPTH_SWEEP_SIZE:
            raise SystemExit(f"--n-questions {args.n_questions}: depth_sweep86 is the named set of "
                             f"{DEPTH_SWEEP_SIZE} questions (D75 Q50); per_category takes a count")
        questions = depth_sweep86_questions()
    else:
        n = args.n_questions or PER_CATEGORY_DEFAULT_N
        questions = select_questions({cat: n // 5 or 3 for cat in CATEGORIES_TO_SAMPLE})

    # D112 Q11 (D98, G7): the named questions of the set only, before the share is cut; names and keys unchanged
    n_set = len(questions)
    questions, question_filter = filter_questions(questions, getattr(args, "question_ids", None),
                                                  getattr(args, "question_ids_file", None))
    if question_filter:
        line = (f"question filter ({question_filter['option']}"
                + (f" {question_filter['file']}, sha256 {question_filter['file_sha256'][:12]}"
                   if "file" in question_filter else "")
                + f"): {len(questions)} of the set's {n_set} questions kept; "
                f"{len(question_filter['outside_set'])} named ids outside the set")
        logger.info(line)
        if args.dry_run:
            print(line)

    # D95 Q213: share k of n of the questions (--part), the draws named (--draws); each answer as one process runs it
    part = getattr(args, "part", None)
    if part:
        questions = ex.share(questions, part)
        if not questions:
            raise SystemExit(f"--part {part}: the share holds no question ({len(questions)}); nothing run")
    draws = select_draws(getattr(args, "draws", None))
    stop_file = Path(args.stop_file) if getattr(args, "stop_file", None) else None

    total_evals = len(questions) * len(depths) * len(draws)
    logger.info(f"Depth sweep: {len(questions)} questions × {len(depths)} depths × {len(draws)} draws = "
                f"{total_evals} evaluations" + (f" (share {part})" if part else ""))
    logger.info(f"Model: {model}")
    logger.info(f"Depths: {depths}")
    logger.info(f"Draws: {draws} of {DRAWS}")
    logger.info(f"Index: {INDEX_NAME}")

    # Output path: the server in the name avoids write conflicts when running in parallel; a share's part (D95 Q213)
    # keeps the processes of one server apart
    model_short = model.split("::")[-1].replace(":", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = server_suffix(args.base_url) + part_tag(part)
    prefix = file_prefix(smoke, tag, gen)
    output_path = RESULTS_DIR / f"{prefix}_{model_short}{suffix}_{timestamp}.json"
    latest_path = RESULTS_DIR / f"{prefix}_{model_short}{suffix}_latest.json"
    if output_path.exists() and not args.dry_run:
        raise SystemExit(f"{output_path} exists (another start of this share in the same second); nothing run")

    # Resume support: scan ALL files for this model (any server) to find completed keys
    existing = {}
    if args.resume:
        pattern = f"{prefix}_{model_short}*.json"
        for f in sorted(RESULTS_DIR.glob(pattern)):
            if f.name.endswith("_merged.json"):
                continue
            file_results = load_existing_results(f)
            existing.update(file_results)
        if existing:
            logger.info(f"Resuming: found {len(existing)} existing results across all files")
        else:
            logger.info("No existing results found, starting fresh")

    work = work_list(questions, depths, set(existing.keys()), smoke, tag, draws, gen)
    if args.dry_run:
        print_work_list(work, questions, depths, draws, part, model)
        return

    # Setup
    user_id = find_admin_user_id()
    # F5 (audit of 16 October): each depth's sink records the index's content (<sink>/index_identity.jsonl), so the
    # passages_seen ids its answers store resolve to text exactly (experiments/scorers/records.py)
    for rid in sorted({w["run_id"] for w in work if not w["done"]}):
        index_identity.record_index(ex.sink(rid), INDEX_NAME, user_id, script="exp_06_depth_sweep.py")

    router = ModelRouter()

    # A share's files hold its own questions' rows (every draw); one process's hold every row it resumed from
    mine = {q["id"] for q in questions}
    all_results = [r for r in existing.values() if not part or r.get("question_id") in mine]
    completed = set(existing.keys())
    n_skipped = 0
    n_errors = 0
    stopped = False

    for wi, w in enumerate(work):
        q, depth, draw, key = w["question"], w["depth"], w["draw"], w["key"]
        qid = q["id"]
        if key in completed:
            n_skipped += 1
            continue
        if stop_file is not None and stop_file.exists():
            logger.info(f"Stop file {stop_file} present: stopping before {key} (answers stored so far kept)")
            stopped = True
            break

        progress = f"[{wi + 1}/{total_evals}]"
        logger.info(f"{progress} {qid} @ depth={depth}, draw={draw} ...")

        # The run context of this (question, depth, draw): every model call of the answer is recorded in the
        # depth's run sink. Built before the RLM starts, so a context the lock or the sink refuses stops the run.
        ctx = ex.context(EXPERIMENT, arm(depth), qid, draw, MODELS, base_url=args.base_url, run=w["run_id"],
                         judge=False)

        # Run RLM, one attempt (Q29)
        with rc.run(ctx):
            rlm_result = await run_rlm(
                question=q["question"],
                router=router,
                model=model,
                user_id=user_id,
                depth=depth,
                index_name=INDEX_NAME,
            )

        if rlm_result["error"]:
            n_errors += 1
            logger.error(f"  FAILED: {rlm_result['error'][:100]}")

        # Unscored here: the judge (A7), concept recall and citation coverage run on the stored answers
        result = {
            "answer_key": key,
            "run_id": w["run_id"],
            "question_id": qid,
            "question": q["question"],
            "category": q["category"],
            "depth": depth,
            "draw": draw,
            "model": model,
            "answer": rlm_result["answer"],
            "setup_s": round(rlm_result["setup_s"], 2),
            "latency_s": round(rlm_result["latency_s"], 2),
            "llm_calls": rlm_result["llm_calls"],
            "tokens_used": rlm_result["tokens_used"],
            "retrieved_passages": rlm_result["retrieved_passages"],
            "stop_reason": rlm_result["stop_reason"],
            "error": rlm_result["error"],
            "rlm": rlm_result["rlm"],   # the run's record (A6/D37), RLMOrchestrator._metadata
        }

        all_results.append(result)
        completed.add(key)

        # Save intermediate results after each evaluation
        _save_results(all_results, output_path, latest_path, model, depths, questions, tag, part, draws,
                      question_filter)

        logger.info(f"  latency={rlm_result['latency_s']:.1f}s, stop_reason={rlm_result['stop_reason']}, "
                    f"answer {len(rlm_result['answer'] or '')} characters")

    # Final save
    _save_results(all_results, output_path, latest_path, model, depths, questions, tag, part, draws,
                  question_filter)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"DEPTH SWEEP COMPLETE")
    logger.info(f"  Total: {len(all_results)} results")
    logger.info(f"  Skipped (resumed): {n_skipped}")
    logger.info(f"  Errors: {n_errors}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"{'='*60}")

    # Print the depth summary (answers are unscored here)
    print("\n--- Depth Summary ---")
    _print_depth_summary(all_results)
    if stopped:
        raise SystemExit(STOPPED_EXIT)


def _print_depth_summary(results: List[Dict]) -> None:
    """Answers, errors and mean latency of the answers without an error, per depth. No concept recall: it is
    computed from the stored answers in the scoring step."""
    import statistics
    print(f"{'Depth':>6} | {'n':>4} | {'errors':>6} | {'Mean Lat':>8}")
    print("-" * 36)
    by_depth = {}
    for r in results:
        by_depth.setdefault(r["depth"], []).append(r)
    for d in sorted(by_depth.keys()):
        rows = by_depth[d]
        ok = [r["latency_s"] for r in rows if not r.get("error")]
        mean_lat = f"{statistics.mean(ok):>7.1f}s" if ok else f"{'-':>8}"
        print(f"{d:>6} | {len(rows):>4} | {len(rows) - len(ok):>6} | {mean_lat}")


def _write_whole(path: Path, text: str) -> None:
    """Writes text to path under a temporary name in the same folder and moves it into place (os.replace), so a
    reader sees the old file or the new one, never half of one, and a stop never leaves path cut. The temporary name
    starts with '.', so the results globs (<prefix>_<model>*.json) never read it."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _save_results(results, output_path, latest_path, model, depths, questions, tag=None, part=None, draws=None,
                  question_filter=None):
    """Save results to JSON: the start's file and its _latest, each written whole and moved into place."""
    data = {
        "experiment": "v4_9_depth_sweep",
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "depths": depths,
        "draws": list(DRAWS),
        "draws_run": list(draws or DRAWS),
        "part": part,
        "question_filter": question_filter,   # D112 Q11: filter_questions' record, None without one
        "question_set": tag,
        "n_questions": len(questions),
        "question_ids": [q["id"] for q in questions],
        "index": INDEX_NAME,
        "n_results": len(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, default=str)
    _write_whole(output_path, text)
    _write_whole(latest_path, text)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def merge_results(model: str, tag: Optional[str] = None):
    """Merge all parallel depth sweep results for a model and one question set (tag) into one file."""
    model_short = model.split("::")[-1].replace(":", "_").replace("/", "_")
    pattern = f"{file_prefix(tag=tag)}_{model_short}*.json"   # this set's paper files; smoke files have their own prefix
    all_results = {}
    seen_in = {}

    # limits #147 (Q29: an answer is never replaced by a later attempt): an answer key in more than one row refuses
    # the merge and lists the duplicates. A run's file repeats the rows it resumed from, and its _latest file repeats
    # the run's file, so rows equal to the one already read are the same answer, not a duplicate.
    duplicates = []
    for f in sorted(RESULTS_DIR.glob(pattern)):
        if f.name.endswith("_merged.json"):
            continue
        for r in _rows(f):
            key = r["answer_key"]
            if key in all_results and all_results[key] != r:
                duplicates.append(f"{key}: {seen_in[key]} and {f.name}")
                continue
            all_results.setdefault(key, r)
            seen_in.setdefault(key, f.name)
    if duplicates:
        raise SystemExit(f"merge refused: {len(duplicates)} answer keys have two different rows:\n  "
                         + "\n  ".join(duplicates))

    merged = list(all_results.values())
    merged.sort(key=lambda r: (r["question_id"], r["depth"], r["draw"]))

    output = {
        "experiment": "v4_9_depth_sweep",
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "n_results": len(merged),
        "results": merged,
    }

    merged_path = RESULTS_DIR / f"v4_9_depth_sweep_{model_short}_merged.json"
    with open(merged_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"Merged {len(merged)} results → {merged_path.name}")

    # Print summary
    print("\n--- Merged Depth Summary ---")
    _print_depth_summary(merged)


def main():
    parser = argparse.ArgumentParser(
        description="V4-9: RLM Depth Sweep — fine-grained saturation curve"
    )
    parser.add_argument(
        "--depths", type=int, nargs="+", default=None,
        help=f"Depths to test (default: {DEFAULT_DEPTHS}; with --smoke, {SMOKE_DEPTHS})"
    )
    parser.add_argument(
        "--question-set", choices=QUESTION_SETS, default="depth_sweep86",
        help="depth_sweep86 (default; G5, D75 Q50): the submitted sweep's 88 questions less CD_015 and SY_010, as the "
             "authors' RLM runs; per_category (T1): --n-questions stratified across the 5 categories"
    )
    parser.add_argument(
        "--n-questions", type=int, default=None,
        help=f"per_category: total questions (default {PER_CATEGORY_DEFAULT_N}); depth_sweep86: only 86 is accepted"
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke test: 2 questions × 2 depths (or the --depths given), in its own runs (exp_06_depth_sweep__rlm_<depth>__smoke) and "
             "files (v4_9_depth_sweep_smoke_*), which resume and merge of the paper run never read"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from latest results file"
    )
    parser.add_argument(
        "--base-url", type=str, default=None,
        help="The Ollama server every run context names (its base_url), e.g. http://127.0.0.1:21441; required "
             "except with --dry-run and --merge. Replaces --port, which never changed where calls went (calls.md "
             "B7). With the default generator (Gemini) nothing contacts it; with --generator ollama::<tag> it is the "
             "server every call goes to"
    )
    parser.add_argument(
        "--generator", type=str, default=MODEL,
        help=f"The RLM's model: {MODEL} (the default, G5) or ollama::<tag>, a local model the lock runs as a "
             "generator (D97, T1), whose runs and files carry +<tag> after the set's name"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the work list (questions, runs, draws, pending answer keys) and stop: no database, no model call"
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="Merge all parallel results for this model and print summary"
    )
    parser.add_argument(
        "--part", type=str, default=None,
        help="k/n: run share k of n of the questions, dealt round robin in the set's order (experiment.share; D95 "
             "Q213), into results files of its own (_part<k>of<n>); each answer as one process would run it"
    )
    parser.add_argument(
        "--draws", type=int, nargs="+", default=None,
        help=f"Run only these of Figure {FIGURE}'s draws {DRAWS} (D78 Q116: a queue finishes a draw on every share "
             "before the next starts)"
    )
    parser.add_argument(
        "--stop-file", type=str, default=None,
        help=f"Stop before the next answer when this file exists (answers stored so far kept; exit {STOPPED_EXIT})"
    )
    parser.add_argument(
        "--question-ids", nargs="+", default=None,
        help="Only these of the set's questions, in the set's order (D112 Q11; as exp_03's --question-ids); runs, "
             "answer keys and results files keep their names"
    )
    parser.add_argument(
        "--question-ids-file", type=str, default=None,
        help="Only the set's questions this JSON file names (a list, or an object with \"ids\": D98's subset, "
             "findings/recompute/D98_subset/d98_subset.json), in the set's order; ids of the 135 outside the set are "
             "listed, not run (D112 Q11, G7)"
    )

    args = parser.parse_args()
    if args.part:
        try:
            ex.share_spec(args.part)
        except ex.ExperimentError as e:
            parser.error(f"--part: {e}")
    if not (args.dry_run or args.merge) and not (args.base_url or "").startswith(("http://", "https://")):
        parser.error("--base-url http(s)://host:port is required (the Ollama server of the run contexts)")

    if args.merge:
        model = check_generator(args.generator)
        merge_results(model, set_tag(args.question_set, args.n_questions) + generator_tag(model))
    else:
        asyncio.run(run_experiment(args))


if __name__ == "__main__":
    main()
