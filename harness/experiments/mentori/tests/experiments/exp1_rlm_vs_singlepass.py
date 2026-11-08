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
from backend.agents.lock_adapter import LockCallError
from backend.retrieval.retriever import SimpleRetriever
from backend.retrieval.rlm.orchestrator import RLMOrchestrator, RLMRunError
from backend.retrieval.rlm.context import RLMContext
from backend.retrieval.pipeline import ScientificRAGPipeline, PipelineConfig, call_summary
from backend.agents.orchestrator.run_records import REFUSALS   # LockError, RunContextError: setup errors (Q38)

from experiments.runner import run_context as rc

from tests.experiments.exp_common import (
    JUDGE_MODEL, GEN_MODEL, JUDGE_OPTIONS, RESULTS_DIR as COMMON_RESULTS_DIR,
    find_admin_user_id, check_index_exists,
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
    """Result from a single answer generation run.

    The fields after error are the answer's record (D37, A6), stored by exp_01 and exp_02 through asdict(). Token
    counts come from the answer's call records in <sink>/calls.jsonl (the old word counts and calls x 1,500 are gone);
    llm_calls is the number of those records. A failed call leaves answer "" and its error in error (A5)."""
    answer: str
    latency_s: Optional[float]           # None only when nobody timed the answer (failed_answer)
    llm_calls: Optional[int]           # None only when no call records could be read (failed_answer)
    tokens_used: Optional[int]           # prompt + output + thinking tokens over the answer's call records
    retrieved_passages: Optional[int]    # passages in the generation prompt; multi-hop: summed over hops; RLM:
                                         # len(passages_seen), every passage its code was handed (Q74, D75)
    config: str
    gen_model: str
    error: Optional[str] = None
    stop_reason: Optional[str] = None    # how the answer ended: single pass and verified pass, the generation call's
                                         # lock status (ok, length, or the failed call's); multi-hop and RLM, the
                                         # strategy's own; the provider's stop reason is in calls[].stop_reason
    passages: Optional[List[str]] = None # passage ids in the final generation prompt (D37); RLM: passages_seen,
                                         # every passage its code was handed (Q74, D75)
    calls: List[Dict[str, Any]] = field(default_factory=list)       # call_summary() of every call record
    prompt_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    thinking_tokens: Optional[int] = None
    calls_without_tokens: int = 0        # call records whose provider gave no prompt or output count
    retrievals: List[Dict[str, Any]] = field(default_factory=list)  # retriever records (widths, query_type, reranked)
    hops: Optional[List[Dict[str, Any]]] = None   # multi-hop: one entry per hop
    length_turns: Optional[int] = None            # multi-hop: hops whose reply stopped at the output limit (Q151, D83)
    verification: Optional[Dict[str, Any]] = None # verified pass: Verification.to_record()
    verify_fallback: Optional[bool] = None        # verified pass: Q17 fallback to the first 5 passages
    top_k: Optional[int] = None                   # single pass and matched budget: passages asked of the retriever
    matched_budget: Optional[Dict[str, Any]] = None   # D51: the plan entry the answer ran under
    rlm: Optional[Dict[str, Any]] = None          # RLM: the run's metadata (RLM_FIELDS)


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
# find_admin_user_id, check_index_exists,
# setup_retriever, load_ground_truth, judge_answer, etc.


# Counts the decisions keep, stated (limits.md, records.md)
SINGLE_PASS_TOP_K = 10      # single pass retrieves 10 passages (exp1:196 as submitted); D51's arm passes its own
MULTI_HOP_TOP_K = 10        # each hop retrieves 10 passages and sees only its own, as submitted (limits.md #2, Q2)
MULTI_HOP_MAX_TURNS = 5     # searches before the closing turn (Q21 alternative, D68)
MULTI_HOP_CLOSING_SEARCH = False   # the closing turn runs no sixth search: it re-shows the fifth hop's passages, so
                                   # multi-hop keeps the submitted 5 retrievals (Q76, D75)
SEARCH_MARKER = re.compile(r"^[ \t]*SEARCH:\s*(.+?)[ \t]*$", re.IGNORECASE | re.MULTILINE)
# Q77 (D75): the reply's own marker at the start of a line, so "research:" is not a search; the query may sit on the
# next line
# Q151 (D83), as the RLM's D80 V4 (orchestrator.CUT_REPLY_NOTE): a hop's reply that stopped at the output limit
# (done_reason "length": Gemini's MAX_TOKENS, Ollama's length) is not acted on. No search runs from it and it is
# neither the answer nor a final answer; the next hop shows the same passages again with this line in its search log,
# and the turn is counted in length_turns.
MULTI_HOP_CUT_NOTE = "Your reply was cut off by the output limit, so none of it was used and no search was run from it."
RLM_FIELDS = ("stop_reason", "turns", "rejections", "sub_calls_ok", "sub_calls_failed", "sub_calls_empty",
              "n_code_blocks_run", "nudges", "passages_seen", "timer_firings")   # the RLM metadata an answer stores
                                                                              # (RLM track; Q65, D75: sub_calls_empty)
CALLS = "calls.jsonl"


class _AnswerCalls:
    """The call records of the answer running in the current run context: the lines of <sink>/calls.jsonl written
    after this object was made that carry this context's ctx_uid (every call of one (question, draw) runs under one
    context object, the RLM's sub-calls included). The size is read and the tail read under a shared flock, the lock
    run_context.append writes under, so no line is read half written."""

    def __init__(self):
        ctx = rc.current()
        self.ctx_uid = ctx.ctx_uid
        self.path = ctx.sink / CALLS
        self.offset = self._read(None)

    def _read(self, offset: Optional[int]):
        """Under a shared flock: the file's size (offset None), else its bytes from offset on."""
        import fcntl
        if not self.path.exists():
            return 0 if offset is None else b""
        with open(self.path, "rb") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                if offset is None:
                    return f.seek(0, 2)
                f.seek(offset)
                return f.read()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def records(self) -> List[Dict[str, Any]]:
        data = self._read(self.offset)
        out = []
        for line in data.decode("utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("ctx_uid") == self.ctx_uid:
                out.append(rec)
        return out


def _with_calls(gen: GenerationResult, log: _AnswerCalls) -> GenerationResult:
    """Fills the answer's call fields from its call records (D37, A6): llm_calls, calls, and the token sums. A
    record with no prompt or output count (a failed call, or a provider that gave none) is counted in
    calls_without_tokens; the sums are over the counts given, None when no record gives one."""
    recs = log.records()
    gen.calls = [call_summary(r) for r in recs]
    gen.llm_calls = len(recs)

    def total(key):
        vals = [r.get(key) for r in recs if isinstance(r.get(key), int)]
        return sum(vals) if vals else None

    gen.prompt_tokens, gen.output_tokens, gen.thinking_tokens = (total("prompt_tokens"), total("output_tokens"),
                                                                 total("thinking_tokens"))
    gen.calls_without_tokens = sum(1 for r in recs if not isinstance(r.get("prompt_tokens"), int)
                                   or not isinstance(r.get("output_tokens"), int))
    parts = [v for v in (gen.prompt_tokens, gen.output_tokens, gen.thinking_tokens) if v is not None]
    gen.tokens_used = sum(parts) if parts else None
    return gen


def failed_answer(config: str, gen_model: str, error: BaseException, log: Optional[_AnswerCalls],
                  latency_s: Optional[float]) -> GenerationResult:
    """The record of an answer whose strategy raised (exp_01, exp_02): answer "", the exception as its error, the
    counts nobody measured None (never 0, A5), and the calls the answer made before it raised, from its call
    records (D37). log is the _AnswerCalls opened before the strategy ran; None when there was none, and then
    llm_calls is None too."""
    gen = GenerationResult(answer="", latency_s=latency_s, llm_calls=None, tokens_used=None, retrieved_passages=None,
                           config=config, gen_model=gen_model, error=f"{type(error).__name__}: {error}")
    return _with_calls(gen, log) if log is not None else gen


def _format_passages(results: List[Dict[str, Any]], cut: Optional[int] = None) -> str:
    """The passages block of the single-pass, multi-hop and matched-budget prompts: each passage whole (D25; the
    800-character cut is gone, cuts.md exp1:205, :296). cut: D196's one exception, the named arm single_pass_cut800,
    which puts the April cut back to measure what it did; no other caller passes it."""
    passages = []
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("file_name", "unknown")
        page = r["metadata"].get("page", "?")
        text = r["text"] if cut is None else r["text"][:cut]
        passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")
    return "\n\n".join(passages)


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
    top_k: int = SINGLE_PASS_TOP_K,
    config_name: str = "single_pass",
    matched_budget: Optional[Dict[str, Any]] = None,
    passage_cut: Optional[int] = None,
) -> GenerationResult:
    """
    Single-pass RAG: retrieve top_k (10) → LLM generates answer.

    This is the baseline: one retrieval step, one generation step. The D51 matched-budget arm is this function
    with the top_k of its plan (experiments/runner/matched_budget.py) and config_name "matched_budget".
    """
    t0 = time.time()
    log = _AnswerCalls()
    trace: List[Dict[str, Any]] = []

    # Retrieve top_k chunks
    results = retriever.retrieve(
        query=question,
        top_k=top_k,
        collection_name=collection_name,
        trace=trace,
    )

    prompt = single_pass_prompt(question, results, passage_cut)
    gen = GenerationResult(
        answer="", latency_s=0.0, llm_calls=0, tokens_used=None, retrieved_passages=len(results),
        config=config_name, gen_model=gen_model, passages=[r["id"] for r in results], retrievals=trace,
        top_k=top_k, matched_budget=matched_budget,
    )

    # Generate answer. No options: the lock's settings (D53). The record carries the passage ids (D37).
    rc.set_passages(gen.passages)
    try:
        response = await router.generate(model_identifier=gen_model, prompt=prompt)
        gen.answer = response.get("response") or ""     # never str(response) (A5, limits #65)
        gen.stop_reason = (response.get("lock_record") or {}).get("status")   # ok or length
    except LockCallError as e:
        gen.error = str(e)                              # A5: the failure is recorded, the answer stays empty
        gen.stop_reason = e.record.get("status")

    gen.latency_s = time.time() - t0
    return _with_calls(gen, log)


def single_pass_prompt(question: str, results: List[Dict[str, Any]], cut: Optional[int] = None) -> str:
    """The single-pass prompt for a question and its passages (also what matched_budget.py counts, D51)."""
    return SINGLE_PASS_PROMPT.replace("{passages}", _format_passages(results, cut)).replace("{question}", question)


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

# Q21 (alternative, D68): when the model asks for a sixth search, it gets one closing turn that must answer. The turn
# shows MULTI_HOP_USER's sections (with MULTI_HOP_CLOSING_SEARCH False, the fifth hop's passages again, and the
# history includes the search it asked for); only the last line differs from MULTI_HOP_USER.
MULTI_HOP_CLOSING_USER = """## Question
{question}

## Retrieved Passages (Search #{search_num})
{passages}

## Previous findings
{history}

This is your last turn: no more searches are available. Review these passages and provide your FINAL ANSWER."""


def _search_log(turn: int, query: str, n: int) -> str:
    """One line of multi-hop's search log: the hop's search and its own passage count (limits #2/#116), the submitted
    wording (its dash written as an escape)."""
    return f"Turn {turn + 1}: Searched '{query}' \u2014 found {n} passages"


async def _multi_hop_rag(
    question: str,
    retriever: SimpleRetriever,
    collection_name: str,
    router: ModelRouter,
    gen_model: str,
    max_turns: int = MULTI_HOP_MAX_TURNS,
) -> GenerationResult:
    """
    Multi-hop RAG: iterative retrieve-refine loop with natural language queries only.

    This is the "RLM without code" ablation — same iterative retrieval,
    but the LLM can only request searches in natural language (no programmatic
    filtering, slicing, regex).

    Each hop sees its own MULTI_HOP_TOP_K passages, whole, and the log of earlier searches (limits.md #2, as
    submitted). After max_turns hops that each asked for another search, one closing turn must answer (Q21): with
    MULTI_HOP_CLOSING_SEARCH False it runs no new search and shows the last hop's passages again. stop_reason:
    final_answer, no_protocol (the reply is the answer, as Mentori did), closing_final_answer, closing_no_protocol
    (a closing reply with neither FINAL ANSWER nor SEARCH is the answer, as no_protocol), closing_search_request (the
    closing reply still asks for a search: no answer is stored, the defect Q21 names; Q77, D75), closing_length (the
    closing reply stopped at the output limit: no answer is stored, Q151, D83), or the failed call's status (A5: the
    answer stays empty). Each hop is in hops with its query, passage ids, call and length_cut.

    Q151 (D83), as the RLM's D80 V4: a reply that stopped at the output limit (done_reason "length") is not acted on.
    No search runs from it, and neither a FINAL ANSWER in it nor the reply itself (no_protocol) is taken as the
    answer. The next hop runs no search and shows the same passages again; its search log carries MULTI_HOP_CUT_NOTE
    for the cut hop, which is how the model is told. The cut hop counts as one of the max_turns hops, as a cut root
    turn counts as an RLM turn, and length_turns counts the cut hops.
    """
    t0 = time.time()
    log = _AnswerCalls()
    current_query = question   # the query the next hop searches; None after a cut reply (Q151)
    history_parts = []
    retrievals: List[Dict[str, Any]] = []
    hops: List[Dict[str, Any]] = []
    total_passages = 0
    gen = GenerationResult(answer="", latency_s=0.0, llm_calls=0, tokens_used=None, retrieved_passages=0,
                           config="multi_hop", gen_model=gen_model, retrievals=retrievals, hops=hops,
                           length_turns=0)

    search_num = 0
    for turn in range(max_turns + 1):
        closing = turn == max_turns
        # Q151: no search after a cut reply (current_query None); the hop shows the last search's passages again
        searched = current_query is not None and (not closing or MULTI_HOP_CLOSING_SEARCH)
        if searched:
            # Retrieve
            trace: List[Dict[str, Any]] = []
            results = retriever.retrieve(
                query=current_query,
                top_k=MULTI_HOP_TOP_K,
                collection_name=collection_name,
                trace=trace,
            )
            retrievals.extend(trace)
            total_passages += len(results)
            search_num += 1
        # else: the closing turn (Q21, MULTI_HOP_CLOSING_SEARCH) or the hop after a cut reply (Q151) shows the last
        # search's results again
        ids = [r["id"] for r in results]

        passages_text = _format_passages(results)
        history_text = "\n".join(history_parts) if history_parts else "None yet."

        prompt = (MULTI_HOP_CLOSING_USER if closing else MULTI_HOP_USER).replace("{question}", question)
        prompt = prompt.replace("{search_num}", str(search_num))
        prompt = prompt.replace("{passages}", passages_text)
        prompt = prompt.replace("{history}", history_text)

        hop = {"turn": turn + 1, "closing": closing, "query": current_query if searched else None,
               "requested_query": None if searched else current_query, "passages": ids, "call": None,
               "reply": None, "length_cut": False}
        hops.append(hop)

        # Call LLM: no options and no think argument (the lock's settings, D53, D66); the record carries the ids
        rc.set_passages(ids)
        try:
            response = await router.chat(
                model_identifier=gen_model,
                messages=[
                    {"role": "system", "content": MULTI_HOP_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
        except LockCallError as e:
            hop["call"] = call_summary(e.record)
            gen.error, gen.stop_reason = str(e), e.record.get("status")   # A5: recorded, answer stays empty
            break
        hop["call"] = call_summary(response.get("lock_record"))

        # The reply as the lock returned it; never str(response) (records.md multi-hop, A5)
        answer_text = response.get("message", {}).get("content") or ""
        hop["reply"] = answer_text

        if response.get("done_reason") == "length":
            # Q151 (D83), as the RLM (D80 V4): the reply stopped at the output limit, so nothing in it is acted on.
            # It stays whole in hop["reply"] and its call record keeps status length; the search log tells the model
            # in the next hop (its search, if this hop ran one, is logged first, as a search request logs it)
            hop["length_cut"] = True
            gen.length_turns += 1
            history_parts.append((_search_log(turn, current_query, len(results)) + ". " if searched else
                                  f"Turn {turn + 1}: ") + MULTI_HOP_CUT_NOTE)
            current_query = None
            if closing:
                gen.answer, gen.stop_reason, gen.passages = "", "closing_length", ids   # no answer is stored
                break
            continue

        # Check for FINAL ANSWER
        final_match = re.search(r"FINAL\s*ANSWER:\s*(.*)", answer_text, re.DOTALL | re.IGNORECASE)
        if final_match:
            gen.answer = final_match.group(1).strip()
            gen.stop_reason = "closing_final_answer" if closing else "final_answer"
            gen.passages = ids
            break

        # Check for SEARCH: <query>
        search_match = SEARCH_MARKER.search(answer_text)

        if closing:
            # The closing turn must answer (Q21). A reply that still asks for a search is not an answer: none is
            # stored (A5; storing it is the defect Q21 names). A reply with neither marker is the answer, as Mentori's
            # no_protocol branch takes it. Q77 (D75).
            gen.answer = "" if search_match else answer_text
            gen.stop_reason = "closing_search_request" if search_match else "closing_no_protocol"
            gen.passages = ids
            break

        if search_match:
            # limits #2/#116: the log pairs each search with its own passage count (the old code logged the next
            # query with the count of the one just run). Q151: a hop that ran no search (after a cut reply) logs none
            if searched:
                history_parts.append(_search_log(turn, current_query, len(results)))
            current_query = search_match.group(1).strip()
        else:
            # LLM didn't follow protocol — treat entire response as answer
            gen.answer = answer_text
            gen.stop_reason = "no_protocol"
            gen.passages = ids
            break

    gen.retrieved_passages = total_passages
    gen.latency_s = time.time() - t0
    return _with_calls(gen, log)


# ─────────────────────────────────────────────────────────────
# C. RLM Runner
# ─────────────────────────────────────────────────────────────

class RLMStop(RuntimeError):
    """Q73 (D75): an RLM outcome that is neither an answer nor an RLMRunError (a failed index or reranker load, or an
    unplanned exception of our RLM code). It stops the run with nothing stored for the answer, as a lock refusal
    does, so resume runs the answer again; the original exception is its __cause__."""


STOPS = (*REFUSALS, RLMStop)   # what exp_01 and exp_02 let stop the run instead of storing a failed answer


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
    quality_gate: bool = True,
    search_tools: bool = True,
) -> GenerationResult:
    """
    Wrap existing RLM infrastructure for programmatic use.

    quality_gate (D238): passed to RLMOrchestrator; True, the default, is the gate every run had. exp_01's
    rlm_10_nogate (G14) passes False, and its record then carries rlm.metadata.quality_gate. search_tools (D239):
    passed to RLMOrchestrator; True, the default, is the REPL every run had. exp_01's rlm_10_nosearch (arm B) passes
    False, and its record then carries rlm.metadata.search_tools.

    RLMOrchestrator.run() returns the answer (an RLMResult, a str) with .metadata, the run's record, or raises
    RLMRunError carrying the same .metadata when the run ends with no answer. rlm holds the RLM_FIELDS of that
    metadata (None where it gives none), the citation count and the whole metadata. Tokens and llm_calls come from
    the answer's call records (D37), not from the RLM's own counters. A run with no answer (RLMRunError) is the
    answer's error, never its text (A5). A lock refusal (REFUSALS) is not caught: it ends the answer as a setup error
    (Q38, D69). Q73 (D75): any other exception, a failed index or reranker load included, raises RLMStop: nothing is
    stored for the answer. Q74 (D75): retrieved_passages and passages are the RLM's passages_seen, every passage a
    search or navigation function returned to its code; the citation count stays in rlm["citations"].
    """
    t0 = time.time()
    log = _AnswerCalls()
    gen = GenerationResult(answer="", latency_s=0.0, llm_calls=0, tokens_used=None, retrieved_passages=None,
                           config=config_name, gen_model=gen_model)
    # Q73 (D75): the index and the reranker load outside the answer's try: a failed load stops the run (D40)
    try:
        context = await RLMContext.from_index(
            index_name=index_name,
            user_id=user_id,
        )
    except REFUSALS:
        raise
    except Exception as e:
        raise RLMStop(f"index or reranker load ({config_name}): {type(e).__name__}: {e}") from e

    # Q73 (D75): from building the orchestrator to the returned record, the only exception kept as the answer's
    # error is RLMRunError; a lock refusal raises as it is, and anything else (a slip in our own code, in the run or
    # while building the record) raises RLMStop, so _process_one cannot store it as a failed answer
    try:
        orchestrator = RLMOrchestrator(
            model_router=router,
            model_identifier=gen_model,
            max_turns=max_turns,
            verify=verify,
            think=think,
            quality_gate=quality_gate,
            search_tools=search_tools,
        )
        try:
            result = await orchestrator.run(task=question, context=context)
            gen.answer = str(result)
            meta = dict(getattr(result, "metadata", None) or {})
        except RLMRunError as e:
            # no answer (max_turns_empty, call_error): the answer's error, with the run's record (A5)
            logger.error(f"RLM error ({config_name}): {e}")
            gen.error = f"{type(e).__name__}: {e}"
            meta = dict(e.metadata or {})

        gen.rlm = {**{k: meta.get(k) for k in RLM_FIELDS}, "citations": len(context.citations), "metadata": meta}
        gen.stop_reason = meta.get("stop_reason")
        # Q74 (D75): the RLM's retrieved set is passages_seen, as exp_06 stores it (it stored the citation count,
        # as submitted at exp1:416 of 982e869; that count stays in rlm["citations"])
        seen = meta.get("passages_seen")
        if seen is None:
            seen = list(context.passages_seen)
        gen.retrieved_passages = len(seen)
        gen.passages = list(seen)

        gen.latency_s = time.time() - t0
        return _with_calls(gen, log)
    except REFUSALS:
        raise       # a lock refusal is a setup error: it fails the question, never stored as an answer (Q38, D69)
    except Exception as e:
        raise RLMStop(f"RLM run or record ({config_name}): {type(e).__name__}: {e}") from e


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
    dense(100) → RRF hybrid(50) → cross-encoder rerank(15) → LLM verify → generate. The widths reach the retriever
    (Q16, D68) and the retrieval record keeps the widths used; the verifier is gpt-oss:20b (Q18).
    """
    t0 = time.time()
    log = _AnswerCalls()

    config = PipelineConfig.verified()
    config.gen_model = gen_model

    pipeline = ScientificRAGPipeline(
        retriever=retriever,
        collection_name=collection_name,
        model_router=router,
        config=config,
    )

    result = await pipeline.answer(question)
    # result.calls is [verifier call, generator call], ending at the call that failed when one did
    last = result.calls[-1] if result.calls else {}

    gen = GenerationResult(
        answer=result.answer,
        latency_s=time.time() - t0,
        llm_calls=0,
        tokens_used=None,
        retrieved_passages=len(result.passages) if result.passages is not None else None,
        config="verified_pass",
        gen_model=gen_model,
        error=result.error,
        stop_reason=last.get("status"),     # the generator call's status (ok or length), or the failed call's
        passages=result.passages,
        retrievals=[result.retrieval] if result.retrieval else [],
        verification=result.verification,
        verify_fallback=result.verify_fallback,
    )
    return _with_calls(gen, log)


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

    Not reachable (A7, D67): generation never judges, and this judge cuts the answer to 3,000 characters and turns
    an error into scores of 0. Answers are judged later by the lock's judge.
    """
    raise RuntimeError("exp1's inline judge is retired (A7, D67): answers are judged by the lock's judge in a "
                       "separate step")
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
    """Run the full experiment.

    Refused (A7, A9, D67): run as a script, exp1 judges inline with tests/experiments/exp_common.judge_answer (a
    3,000-character cut, 0 on a judge error), outside any run context, on its own question file. The entry points are
    publication/scripts/exp_01_generation.py and exp_02_scaling_factorial.py, which import this module's strategies.
    """
    raise SystemExit("exp1_rlm_vs_singlepass.py does not run as a script (A7, A9, D67): use "
                     "publication/scripts/exp_01_generation.py, which runs these strategies under the lock")

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
