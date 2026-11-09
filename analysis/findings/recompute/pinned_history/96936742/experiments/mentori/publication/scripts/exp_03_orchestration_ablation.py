#!/usr/bin/env python3
"""
V4-6: Orchestration Ablation

Measures the value of multi-agent orchestration itself. Compares 4 additive
configs from raw LLM to full orchestrator:

  1. raw_gemini      — Gemini direct (no retrieval, no orchestration)
  2. naive_rag       — retrieve(k=10) → Gemini (no orchestration)
  3. rlm_10          — RLM with 10 turns (no orchestrator wrapper)
  4. full_orchestrator — Full pipeline: plan → execute → supervise → synthesize

Each config answers the 135 questions of answer key v2.4 (D48; experiments.runner.experiment.questions()) on
exp_v4_s20_n0, in draws 1, 2 and 3 (D49, Figure 4), every Mentori agent role on gemini-3-flash-preview (D27, D34).

Reanalysis (step 3, A7, A9; D48, D49, D67):
  - One run per (config, index): run_id exp_03__<config>__<index>, sink findings/runs/<run_id>/ (calls.jsonl, ctx/,
    run_identity.json, answers.json). Each (question, draw) runs inside its own run context
    (experiment.context(...); every model call of the answer belongs to it). Answers are keyed by
    experiment.answer_key(config, question_id, draw, index=index) and kept in <sink>/answers.json; a key already
    there is skipped, so a run always resumes.
  - full_orchestrator: the run's tool server is started once per run (experiment.tool_server) and each answer's
    context is written as the sidecar <sink>/ctx/<task_id>.json, task_id v4_6_orch_<question_id>_d<draw>, which the
    tool server's tools read. The tool registry is discovered in this process too, so the executor injects task_id
    into the tool calls (executor.py inject_session_secrets reads the local registry).
  - No judging here (A7): answers are stored, and the lock's judge scores them in a separate step.
  - F5 (audit of 16 October): each run start appends the index's identity (collection and content hashes,
    experiments/runner/index_identity.py) to <sink>/index_identity.jsonl, so stored passage ids resolve to text.

Reanalysis (B5, D52; Q22 to Q26, Q38, Q39; records.md F12 to F16, limits.md Class X):
  - Figure 4's set-ups that D52 defines are configs here: orch_no_distiller (no step output is distilled) and
    orch_distiller_f1 (the distiller with exp_04b's prompt F1), each a full_orchestrator run with one switch
    (SessionContext.orchestrator_switches). D75 defines the rest, each a config with one switch of
    orchestrator/schemas.ORCHESTRATOR_SWITCHES: orch_no_analyser, orch_no_planner, orch_no_supervisor and
    orch_no_synthesiser switch that phase off (Q83 to Q86), and orch_factual_to_documents sends every factual
    question to the documents (analyser "factual_to_documents", Q87). Q82's stress conditions (distiller_trigger
    "every_step": every non-empty step output distilled) are not Mentori's default and are not in the default run
    list (STRESS_CONFIG_NAMES; run them by name with --configs).
  - Each full_orchestrator answer runs in its own new workspace, <sink>/workspaces/<task_id> (Q22, D68), and records
    the memory context the analyser and planner were given (memory_context_injected).
  - An error is never stored as the answer (A5, F12): the answer is the synthesis text only, "" when there is none,
    with error and error_kind beside it. A lock refusal, here or inside a tool, fails the question as a setup error
    (Q38, D69): it is recorded in <sink>/answers.json setup_errors and the key stays to do, so the answer runs again
    once the setup is fixed. Any other failure is stored with an empty answer and marked done (Q30, D68: counted as a
    failure, never redrawn).
  - The full_orchestrator answer stores plan_status, the analysis, the plan, every step attempt (tool, arguments,
    routing, raw and distilled output, passages, the model calls inside the tool), each supervisor evaluation and
    micro-adjustment, the synthesis's answer_source and errors (records.md F14 to F16).
  - Every config stores the answer's model calls read from <sink>/calls.jsonl (llm_calls counts them; A6, D37), the
    passages naive_rag sent (set_passages before its call), and answer_wall_s.

Latency (Q150, D83; exp_01's docstring states the rule): answer_wall_s stays the answer's clock time. An answer's
own time is its model calls' wall_s plus its search time, and here the search time is read from the run's records as
follows, since answers.json does not hold it for every config:
  - naive_rag and full_orchestrator: the sum of search_s over the lines of <sink>/retrievals.jsonl that the stored
    answer's own attempt wrote: the lines between the two byte offsets in generation.retrievals_bytes (the file's size
    before and after that answer's dispatch) whose run_id is the run's, item_id the question's id and run_draw the
    draw (answer_search_s below). An earlier attempt at the same key in the same sink (a setup error run again, a
    resume) wrote its lines before the stored attempt began, so they are not counted. Matching by item_id and
    run_draw alone would count them, and no other field both records carry names the attempt: a full_orchestrator
    retrieval's ctx_uid is the tool server's, new on every tool call (run_context.load), and need not appear in the
    answer's call records. Answers run one at a time in a run, so no other answer's line falls between the offsets;
    the item filter drops a late line of another item. naive_rag calls retrieve() with no trace,
    and a full_orchestrator step keeps only query, query_type, collection, top_k, reranked, n_returned and passages
    of each retrieval (executor.py _tool_record), so neither answer record holds search_s, load_s or loads. The tool
    server's query_documents builds a new SimpleRetriever on every call, so each of its lines carries
    loads.bm25_index (the keyword index built over the whole collection), not only the first in the process.
  - rlm_10: the sum of search_s over the stored answer's generation.rlm.metadata.retrievals, as in exp_01; its
    retrievals.jsonl lines are search_semantic calls already in that log.
  - Not recorded: the RLM context's own log inside the tool server's tools (deep_research_rlm,
    cross_document_analysis, paper_triage, analyze_corpus, summarize_document_pages) is timed but written to no
    record, so their keyword and regex searches and navigation reads are missing from a full_orchestrator answer's
    search time; only their search_semantic calls reach retrievals.jsonl.

Usage (from experiments/mentori):
    # Work list only: no model call, no file written
    uv run python publication/scripts/exp_03_orchestration_ablation.py --dry-run

    # Generate (every config, draws 1 to 3); base URL of the Ollama server the run contexts name
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --base-url http://127.0.0.1:21441

    # Smoke test (3 questions, draw 1, one config)
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --base-url ... \\
        --max-questions 3 --draws 1 --configs raw_gemini

    # Figure 4's smoke (Q147, D83): named questions, 3 answerable and 2 not answerable, under a smoke sink root
    uv run python publication/scripts/exp_03_orchestration_ablation.py --generate --base-url ... --draws 1 \\
        --question-ids 01_sarek_CO2 01_sarek_FR1 01_sarek_TE3 OOD_001 OOD_002 --configs ... --sink-root ...
    (G3's smoke and launch: findings/recompute/G3_runs/README.md)
"""

import argparse
import asyncio
import functools
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# The tool server URL is set by experiment.tool_server() for the run it serves (settings.TOOL_SERVER_URL); no
# default here, so the orchestrator never reaches a server that is not the run's.

from backend.agents.model_router import ModelRouter
from backend.agents import lock_adapter  # noqa: F401  (puts the repository on sys.path for experiments.runner)
from backend.agents.orchestrator import run_records as rr
from experiments.runner import experiment as ex
from experiments.runner import index_identity
from experiments.runner import run_context as rc

from exp_common import (
    GEN_MODEL,
    find_admin_user_id, check_index_exists,
    setup_retriever,
    load_intermediate, save_intermediate,
)
from tests.experiments.exp1_rlm_vs_singlepass import _run_rlm, RLMStop

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_03_orchestration_ablation")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

EXPERIMENT = "exp_03"
FIGURE = 4                             # draws (1, 2, 3) (D49)
DEFAULT_INDEX = "exp_v4_s20_n0"
ANSWERS_FILE = "answers.json"          # <sink>/answers.json: {"results": [...], "completed_keys": [...]}

CONFIG_NAMES = ["raw_gemini", "naive_rag", "rlm_10", "full_orchestrator", "orch_no_distiller", "orch_distiller_f1",
                "orch_no_analyser", "orch_no_planner", "orch_no_supervisor", "orch_no_synthesiser",
                "orch_factual_to_documents"]
# Q82 (D75): stress conditions, not Mentori's default; left out of the default run list, run only by name, and only
# if F1's effect on whole answers is still wanted once the full pipeline's step records are counted
# (experiments/mentori/orchestrator/distiller_firing.py)
STRESS_CONFIG_NAMES = ["orch_distil_every_step", "orch_distil_every_step_f1"]
# D52 (Figure 4): each orchestrator set-up is the full pipeline with the switches named here
# (SessionContext.orchestrator_switches; their meanings: orchestrator/schemas.ORCHESTRATOR_SWITCHES)
ORCHESTRATOR_CONFIGS = {
    "full_orchestrator": {},                      # Mentori as built
    "orch_no_distiller": {"distiller": "off"},    # the distiller switched off: no step output is distilled
    "orch_distiller_f1": {"distiller": "F1"},     # the distiller with exp_04b's prompt F1
    "orch_no_analyser": {"analyser": "off"},      # Q83 (D75): no analyser call, every question to the plan
    "orch_no_planner": {"planner": "off"},        # Q84 (D75): one fixed step, smart_query at its default mode
    "orch_no_supervisor": {"supervisor": "off"},  # Q85 (D75): each step once, no evaluation, adjustment or retry
    "orch_no_synthesiser": {"synthesiser": "off"},   # Q86 (D75): the steps' text as synthesis would have read it
    "orch_factual_to_documents": {"analyser": "factual_to_documents"},   # Q87 (D75): factual questions to documents
    "orch_distil_every_step": {"distiller_trigger": "every_step"},       # Q82 stress: Mentori's prompt, every step
    "orch_distil_every_step_f1": {"distiller": "F1", "distiller_trigger": "every_step"},   # Q82 stress: F1, every step
}
TOOL_CONFIGS = tuple(ORCHESTRATOR_CONFIGS)  # the configs whose run starts a tool server

# Mentori's count of plan steps the engine runs (orchestrated_chat max_steps; limits.md #27/#133), kept and stated;
# record_plan records when it cuts a plan
MAX_STEPS = 10
# A5: the phases whose model call writes the answer (synthesizer.py); an error event of one of them makes the answer an
# error, whatever text was streamed before it
ANSWER_PHASES = ("synthesis", "direct_answer")
NAIVE_TOP_K = 10                       # naive RAG's passages (Mentori's value, stated); each passage is sent whole

# Every Mentori agent role the code reads, each on the one generator (LIST.md Figure 4; D27). The orchestrator's
# analyser, planner, supervisor and synthesiser run on the model_identifier passed to orchestrated_chat (GEN_MODEL);
# the observation distiller and memory consolidation read "librarian" (executor.py, engine.py); "distiller" is named
# as well, though no code reads it. vision and transcriber are Gemini here: the lock adapter refuses an image sent
# to them (visible as a failed call, accepted for now).
AGENT_ROLES = ("default", "lead_researcher", "supervisor", "librarian", "distiller", "coder", "editor",
               "handyman", "vision", "transcriber")
MODELS = {role: GEN_MODEL for role in AGENT_ROLES}


def run_id_for(config: str, index_name: str) -> str:
    """exp_03__<config>__<index>: one run, and one sink, per config and index (records.md F25)."""
    return ex.run_id(EXPERIMENT, config, index_name)


def task_id_for(question_id: str, draw: int) -> str:
    """The Mentori task id of one full_orchestrator answer, unique per (question, draw) within the run's sink."""
    return f"v4_6_orch_{question_id}_d{draw}"


def work_list(configs: List[str], questions: List[Dict[str, Any]], draws, index_name: str):
    """(config, draw, question, answer_key) in the order the run makes them: config, then draw, then question."""
    for config in configs:
        for d in draws:
            for q in questions:
                yield config, d, q, ex.answer_key(config, q["id"], d, index=index_name)

# Raw prompt (no retrieval context)
RAW_PROMPT = """You are a scientific research assistant. Answer the following question based on your training knowledge.
If you are not confident, say so.

## Question
{question}

## Answer"""

# Naive RAG prompt (same as naive baseline)
NAIVE_RAG_PROMPT = """Answer the following question using ONLY the provided source passages.
If the information is not in the passages, say so clearly.
Cite sources using [N] notation.

## Source Passages
{passages}

## Question
{question}

## Answer"""

# Full orchestrator system prompt
ORCHESTRATOR_SYSTEM = """You are Mentori, a scientific research assistant. Answer the user's question thoroughly using the tools available to you. Search the document index, analyze relevant passages, and provide a well-cited answer."""


# ─────────────────────────────────────────────────────────────
# Config dispatchers
# ─────────────────────────────────────────────────────────────

async def _raw_gemini(question: str, router: ModelRouter) -> Dict[str, Any]:
    """Raw Gemini: no retrieval, no orchestration. Just the LLM. A failed call raises (lock_adapter.LockCallError) and
    _run_config stores it as the answer's error. A blocked or empty reply returns "" (D89, Q145 O3) and is stored as
    an empty answer; a recitation, malformed_function_call or malformed_response reply returns the text it held (D90
    Q1, Q2; "" when none) and is stored as the answer. Each such call is counted in failed_calls."""
    t0 = time.time()
    rc.set_passages([])   # A6, D37: no passage
    response = await router.generate(
        model_identifier=GEN_MODEL,
        prompt=RAW_PROMPT.replace("{question}", question),
    )   # cuts.md exp_03:123: no caller options; the lock sets every value
    answer = response.get("response", response.get("message", {}).get("content", ""))
    return {
        "answer": answer or "",
        "latency_s": round(time.time() - t0, 1),
        "llm_calls": 1,
        "sources_retrieved": [],
        "word_count": len((answer or "").split()),
        "prompt_tokens": response.get("prompt_eval_count", 0),
        "completion_tokens": response.get("eval_count", 0),
    }


async def _naive_rag(question: str, retriever, collection_name: str, router: ModelRouter) -> Dict[str, Any]:
    """Naive RAG: retrieve(k=10) → format → single Gemini call."""
    t0 = time.time()
    results = retriever.retrieve(query=question, top_k=NAIVE_TOP_K, collection_name=collection_name)

    passages = []
    sources_used = set()
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("file_name", "unknown")
        page = r["metadata"].get("page", "?")
        text = r["text"]   # D25 (cuts.md exp_03:147): whole; 671 of 778 s20 chunks are longer than 800 characters
        passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")
        sources_used.add(source)

    prompt = NAIVE_RAG_PROMPT.replace("{passages}", "\n\n".join(passages)).replace("{question}", question)
    passage_ids = [r.get("id") or "" for r in results]
    rc.set_passages(passage_ids)   # A6, D37: the passages this call sends
    response = await router.generate(
        model_identifier=GEN_MODEL,
        prompt=prompt,
    )   # cuts.md exp_03:155: no caller options
    answer = response.get("response", response.get("message", {}).get("content", ""))
    return {
        "answer": answer or "",
        "latency_s": round(time.time() - t0, 1),
        "llm_calls": 1,
        "passages": passage_ids,
        "sources_retrieved": list(sources_used),
        "word_count": len((answer or "").split()),
        "prompt_tokens": response.get("prompt_eval_count", 0),
        "completion_tokens": response.get("eval_count", 0),
    }


def _workspace(task_id: str) -> Path:
    """Q22 (D68; records.md F13, cuts.md O2): a new, empty workspace for one answer, <sink>/workspaces/<task_id>, so no
    memory or file of another answer reaches it. A workspace an earlier attempt of the same answer left behind is kept
    and the answer gets the next free <task_id>__r<n>."""
    root = rc.current().sink / "workspaces"
    path, n = root / task_id, 1
    while path.exists():
        n += 1
        path = root / f"{task_id}__r{n}"
    path.mkdir(parents=True)
    return path


@functools.lru_cache(maxsize=None)
def _index_file_count(collection_name: str) -> int:
    """limits.md #132: the documents of the index, counted as RLMContext._load_documents counts them (one per
    file_name, else per basename of file_path or source). The planner's prompt states this count (planner.py)."""
    from backend.retrieval.vector_store import VectorStore
    metas = VectorStore(collection_name=collection_name).get_collection(collection_name).get(
        include=["metadatas"]).get("metadatas") or []
    names = {m.get("file_name") or os.path.basename(m.get("file_path") or m.get("source") or "unknown")
             for m in metas}
    if not names:   # get_collection creates a collection it does not find, so an empty one means the wrong name
        raise rr.SetupError(f"collection {collection_name!r} holds no document")
    return len(names)


async def _full_orchestrator(question: str, user_id: str, index_name: str, task_id: str,
                             switches: Dict[str, str], collection_name: str = None) -> Dict[str, Any]:
    """Full orchestrator pipeline: plan → execute → supervise → synthesize.

    Calls the orchestrated_chat async generator from the engine, consuming all
    events and extracting the final synthesised answer. Requires:
      - the run's tool server (experiment.tool_server sets settings.TOOL_SERVER_URL)
      - the answer's run context, with its sidecar <sink>/ctx/<task_id>.json written
      - Gemini API key set

    The answer is the synthesis's text only (chunk events); an error event or exception never becomes answer text
    (A5, F12), and an error event of the synthesis or direct answer (ANSWER_PHASES) leaves the answer empty with its
    streamed text in partial_answer. A lock refusal (LockError, RunContextError, run_records.ToolRefusal, any
    run_records.SetupError) is not caught here: _run_config records it as a setup error (Q38). An unreachable tool
    server raises RunStop (Q93), which stops the run. switches: the set-up's orchestrator switches
    (ORCHESTRATOR_CONFIGS; D52).
    collection_name: the index's collection, whose documents the planner is told the count of (limits.md #132).
    """
    from backend.agents.orchestrator.engine import orchestrated_chat, MEMORY_TASKS
    from backend.agents.session_context import SessionContext, set_session_context

    t0 = time.time()

    # Q22 (D68): a fresh workspace for this (question, draw)
    workspace = _workspace(task_id)

    # Set up session context with Gemini for ALL orchestrator roles.
    # This ensures a fair comparison: all 4 V4-6 conditions use the same
    # model (Gemini), isolating the effect of orchestration layers.
    # The roles are the run context's (MODELS): the executor and engine look a role up there
    # (run_context.agent_model), and the session's copy is what inject_session_secrets reads.
    gemini_roles = dict(rc.current().agent_roles)
    ctx = SessionContext(
        user_id=user_id,
        user_email="admin@mentori",
        user_role="admin",
        task_id=task_id,
        workspace_path=str(workspace),
        model_identifier=GEN_MODEL,
        mode="agentic",
        agent_roles=gemini_roles,
        rag_preferences={"default_index": index_name},
        available_indexes=[{
            "name": index_name,
            "description": "V4 experiment index",
            "status": "ready",
            "file_count": _index_file_count(collection_name),   # limits.md #132: counted, not the constant 20
        }],
        orchestrator_switches=dict(switches),
    )
    set_session_context(ctx)

    # Build model router
    router = ModelRouter()

    # Build messages in chat format
    messages = [{"role": "user", "content": question}]

    out: Dict[str, Any] = {
        "answer": "", "error": None, "error_kind": None, "errors": [], "plan_status": None, "answer_source": None,
        "switches": dict(switches), "workspace": str(workspace), "memory_context_injected": None, "memory": None,
        "analysis": None, "plan": None, "steps": [], "supervisor": [], "micro_adjustments": [],
        "memory_consolidation": None, "completed": False,
    }
    answer_chunks = []
    try:
        async for event in orchestrated_chat(
            model_router=router,
            model_identifier=GEN_MODEL,
            messages=messages,
            session_context=ctx,
            max_steps=MAX_STEPS,
            think=False,
        ):
            etype = event.get("type", "")
            # Collect answer text from synthesis chunks
            if etype == "chunk":
                answer_chunks.append(event.get("content", ""))
            elif etype == "error":
                # F12 (limits.md Class X): recorded, never answer text
                logger.error(f"Orchestrator event error: {event.get('message', '')}")
                out["errors"].append({k: v for k, v in event.items() if k != "type"})
                if event.get("plan_status") is not None:   # the empty plan's error carries plan_status "failed"
                    out["plan_status"] = event["plan_status"]
            elif etype == "record_memory":
                out["memory_context_injected"] = event["memory_context_injected"]
                out["memory"] = {k: event[k] for k in ("workspace", "sessions", "error")}
            elif etype == "record_analysis":
                out["analysis"] = {k: v for k, v in event.items() if k != "type"}
            elif etype == "record_plan":
                out["plan"] = {k: v for k, v in event.items() if k != "type"}
                out["plan_status"] = event["plan"]["status"]
            elif etype == "record_step":
                out["steps"].append(event["step"])
            elif etype == "supervisor_evaluation":
                out["supervisor"].append({k: v for k, v in event.items() if k != "type"})
            elif etype == "micro_adjustment":
                out["micro_adjustments"].append({k: v for k, v in event.items() if k != "type"})
            elif etype == "complete":
                out["completed"] = True
                out["answer_source"] = event.get("answer_source")
                if event.get("plan_status") is not None:
                    out["plan_status"] = event["plan_status"]
    finally:
        out["answer_wall_s"] = round(time.time() - t0, 3)
        out["latency_s"] = round(time.time() - t0, 1)
        # Mentori's background memory consolidation of this answer: waited for here so its calls are this
        # answer's and its outcome is recorded (its memory reaches no other answer, Q22)
        task = MEMORY_TASKS.pop(task_id, None)
        if task is not None:
            out["memory_consolidation"] = await task

    if out["memory_consolidation"] and out["memory_consolidation"].get("status") == "refused":
        raise rr.ToolRefusal(f"memory consolidation: {out['memory_consolidation'].get('error')}")
    setup = [e for e in out["errors"] if e.get("phase") == "tool_server"]
    if setup:
        # Q93 (D75): the tool server could not be reached, so the run stops; the engine raises RunStop itself, and
        # this is the fallback should its error event arrive without it
        raise rr.RunStop(f"tool server: {setup[0].get('message')}")
    out["answer"] = "".join(answer_chunks)
    failed = [e for e in out["errors"] if e.get("phase") in ANSWER_PHASES]
    if failed:
        # A5: the call that writes the answer failed, so whatever it streamed before failing is not the answer; the
        # text is kept beside it
        out["partial_answer"], out["answer"] = out["answer"], ""
        out["error"] = "; ".join(str(e.get("message")) for e in failed)
        out["error_kind"] = "orchestrator_error"
    elif out["errors"] and not out["answer"].strip():
        out["error"] = "; ".join(str(e.get("message")) for e in out["errors"])
        out["error_kind"] = "orchestrator_error"
    elif not out["completed"]:
        out["error"], out["error_kind"] = "orchestrated_chat ended without completing", "orchestrator_error"
    out["word_count"] = len(out["answer"].split())
    out["sources_retrieved"] = []
    return out


async def dispatch_config(
    config: str,
    question: str,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
    task_id: str = None,
) -> Dict[str, Any]:
    """Route to the right generation function. Runs inside the answer's run context."""
    if config == "raw_gemini":
        return await _raw_gemini(question, router)
    elif config == "naive_rag":
        return await _naive_rag(question, retriever, collection_name, router)
    elif config == "rlm_10":
        gen_result = await _run_rlm(question, router, GEN_MODEL, user_id, max_turns=10, config_name="rlm_10", index_name=index_name)
        from dataclasses import asdict
        d = asdict(gen_result)
        # A6, D37: the whole GenerationResult (stop_reason, passages, retrievals, the RLM's metadata in rlm), as
        # exp_01 and exp_02 store it; limits.md Class X: the RLM's error is kept (it was dropped)
        return {
            **d,
            "error_kind": "strategy_error" if d.get("error") else None,
            "sources_retrieved": [],   # GenerationResult carries no source list (the old d.get("sources") was
                                       # always empty); the passage ids are in passages
            "word_count": len((d.get("answer") or "").split()),
        }
    elif config in ORCHESTRATOR_CONFIGS:
        return await _full_orchestrator(question, user_id, index_name, task_id, ORCHESTRATOR_CONFIGS[config],
                                        collection_name=collection_name)
    else:
        raise ValueError(f"Unknown config: {config}")




# ─────────────────────────────────────────────────────────────
# Work list
# ─────────────────────────────────────────────────────────────

def _questions(args) -> List[Dict[str, Any]]:
    """The 135 questions of answer key v2.4 (D48); the ones --question-ids names, in the key's order (Q147, D83: the
    smoke's 3 answerable and 2 not-answerable questions); or the first --max-questions of them (smoke test). An id
    that is not one of the 135, an id named twice, or both options together is refused before anything runs."""
    questions = ex.questions()
    ids = getattr(args, "question_ids", None)
    if ids and args.max_questions:
        raise SystemExit("--question-ids and --max-questions: name the questions one way")
    if ids:
        known = {q["id"] for q in questions}
        unknown = [i for i in ids if i not in known]
        repeated = sorted({i for i in ids if ids.count(i) > 1})
        if unknown or repeated:
            raise SystemExit(f"--question-ids: {unknown} not among the {len(questions)} questions (D48); "
                             f"{repeated} named twice")
        questions = [q for q in questions if q["id"] in set(ids)]
    if args.max_questions:
        questions = questions[:args.max_questions]
    return questions


def _draws(args) -> tuple:
    """Figure 4's draws (D49), or the ones of them --draws names."""
    draws = ex.draws(FIGURE)
    if args.draws:
        unknown = sorted(set(args.draws) - set(draws))
        if unknown:
            raise SystemExit(f"--draws {unknown}: Figure {FIGURE}'s draws are {draws} (D49)")
        draws = tuple(d for d in draws if d in args.draws)
    return draws


def _check_index(index_name: str) -> None:
    """The 135 questions are the ones in scope on 20 core papers (D48), so the index is a 20-paper one."""
    m = re.search(r"_s(\d+)_", index_name)
    if not m or int(m.group(1)) != ex.CORE_SIZE:
        raise SystemExit(f"index {index_name!r}: the 135 questions are those in scope on {ex.CORE_SIZE} core papers "
                         f"(D48); name an _s{ex.CORE_SIZE}_ index")


def run_dry(args):
    """Prints the work list: each run with its sink and whether it starts a tool server, then every answer key with
    done or todo (read from <sink>/answers.json when it exists). No model call, no database read, nothing written.
    An index --generate would refuse is refused here too, so the list is never one of a run that cannot start."""
    _check_index(args.index)
    questions, draws = _questions(args), _draws(args)
    configs = args.configs or CONFIG_NAMES
    print(f"{EXPERIMENT} (Figure {FIGURE}): {len(configs)} configs x {len(draws)} draws {draws} x {len(questions)} "
          f"questions; index {args.index}; every role {GEN_MODEL} ({', '.join(AGENT_ROLES)})")
    for config in configs:
        rid = run_id_for(config, args.index)
        path = (Path(args.sink_root or ex.RUNS) / rid).resolve()
        answers = path / ANSWERS_FILE
        done = set(json.loads(answers.read_text()).get("completed_keys", [])) if answers.is_file() else set()
        items = [(d, q, key) for _, d, q, key in work_list([config], questions, draws, args.index)]
        n_done = sum(key in done for _, _, key in items)
        print(f"run {rid}  sink {path}  tool server {'yes' if config in TOOL_CONFIGS else 'no'}  "
              f"{len(items)} answers: {n_done} done, {len(items) - n_done} to do")
        for d, q, key in items:
            task = f"  task_id {task_id_for(q['id'], d)}" if config in TOOL_CONFIGS else ""
            print(f"  {'done' if key in done else 'todo'}  {key}{task}")


# ─────────────────────────────────────────────────────────────
# Generate phase
# ─────────────────────────────────────────────────────────────

def _discover_tools() -> None:
    """The executor injects task_id (and the other session values) only into a call to a tool in this process's
    registry (executor.py registry.get_tool, then session_context.inject_session_secrets). Nothing on the
    orchestrator path discovers that registry, so without this every tool that takes task_id would reach the tool
    server with none, and the server refuses it. A module that fails to import is refused, as the server refuses it."""
    from backend.mcp.registry import registry
    registry.discover_tools()
    if registry.failed:
        raise SystemExit(f"tool modules failed to import in the experiment process: {registry.failed}")


def _calls_of_answer(start: int) -> Dict[str, Any]:
    """The answer's model calls, read from <sink>/calls.jsonl after byte `start` (both processes: this one and the
    tool server). llm_calls counts them (A6, D37: from the call records, not from events)."""
    calls = [rr.call_summary(c) for c in rr.since(rr.CALLS, start)]
    tokens = lambda k: sum(c.get(k) or 0 for c in calls)
    return {
        "llm_calls": len(calls),
        # D89 (Q145 O2), D90, LIST.md Rule 10: in Figure 4 an empty or blocked Gemini reply counts as a failed call,
        # though it returns to Mentori as empty text, and so do a recitation stop and a malformed_function_call or
        # malformed_response reply, though each returns the text it held (lock_adapter._finish, _returned); every
        # status but ok and length is a failed call, and the calls list keeps each one's status for the grouping
        "failed_calls": sum(1 for c in calls if c.get("status") not in ("ok", "length")),
        "prompt_tokens": tokens("prompt_tokens"),
        "output_tokens": tokens("output_tokens"),
        "sum_call_wall_s": round(sum(c.get("wall_s") or 0 for c in calls), 3),
        "calls": calls,
    }


def answer_search_s(sink: Path, result: Dict[str, Any]) -> float:
    """Q150 (D83): the search time of a stored naive_rag or full_orchestrator answer (`result`, one entry of
    <sink>/answers.json results): the sum of search_s over the whole lines of <sink>/retrievals.jsonl between the
    answer's generation.retrievals_bytes offsets whose run_id, item_id and run_draw are the answer's run_id,
    question_id and draw. Lines an earlier attempt at the same key wrote (a setup error run again, a resume) lie
    before the first offset and are not counted. A line without search_s raises (KeyError). rlm_10's search time is
    its RLM log's (module docstring), so it is refused here."""
    if result["config"] == "rlm_10":
        raise ValueError("rlm_10: the search time is the sum over generation.rlm.metadata.retrievals")
    a, b = result["generation"]["retrievals_bytes"]
    p = Path(sink) / rr.RETRIEVALS
    if b <= a or not p.is_file():
        return 0.0
    with open(p, "rb") as f:
        # as rr.since: one byte before `a`; when it is not a newline, `a` fell inside a line another writer had begun
        f.seek(max(a - 1, 0))
        data = f.read(b - max(a - 1, 0))
    if a > 0:
        data = data[1:] if data[:1] == b"\n" else data[data.find(b"\n") + 1:] if b"\n" in data else b""
    key = (result["run_id"], result["question_id"], result["draw"])
    total = 0.0
    for line in data.decode("utf-8").split("\n")[:-1]:   # whole lines only
        if line.strip():
            rec = json.loads(line)
            if (rec.get("run_id"), rec.get("item_id"), rec.get("run_draw")) == key:
                total += rec["search_s"]
    return round(total, 6)


# Q38 (D69): the run is set up wrong; the question fails and stays to do. rr.SetupError covers a refusal inside a tool
# (ToolRefusal) and an empty collection; rr.RunStop (a SetupError) also stops the run (A4), an unreachable tool
# server among them (Q93, D75)
SETUP_ERRORS = (rr.SetupError, *rr.REFUSALS)


async def _run_config(config, rid, sink, questions, draws, args, retriever, collection_name, router, user_id):
    """Every (draw, question) of one config's run, each in its own run context."""
    index_name = args.index
    answers_path = sink / ANSWERS_FILE
    intermediate = load_intermediate(answers_path)
    intermediate.setdefault("setup_errors", [])
    completed = set(intermediate.get("completed_keys", []))
    items = list(work_list([config], questions, draws, index_name))

    for count, (_, d, q, key) in enumerate(items, 1):
        qid = q["id"]
        if key in completed:
            logger.info(f"[{count}/{len(items)}] Skip {key}")
            continue
        logger.info(f"[{count}/{len(items)}] {key}")

        ctx = ex.context(EXPERIMENT, config, qid, d, MODELS, base_url=args.base_url, run=rid, sink=sink)
        task_id = task_id_for(qid, d) if config in TOOL_CONFIGS else None
        t0 = time.time()
        error = error_kind = None
        gen_result: Dict[str, Any] = {}
        try:
            with rc.run(ctx):
                if task_id:
                    rc.dump(task_id)      # <sink>/ctx/<task_id>.json, read by the tool server's tools
                start = rr.offset(rr.CALLS)
                rstart = rr.offset(rr.RETRIEVALS)   # Q150 (D83): this attempt's retrievals begin here
                try:
                    gen_result = await dispatch_config(
                        config=config,
                        question=q["question"],
                        retriever=retriever,
                        collection_name=collection_name,
                        router=router,
                        user_id=user_id,
                        index_name=index_name,
                        task_id=task_id,
                    )
                except SETUP_ERRORS as e:
                    # Q38 (D69): a setup error; recorded, the key stays to do, so it runs again once the setup is fixed
                    logger.error(f"Setup error on {key}: {type(e).__name__}: {e}")
                    intermediate["setup_errors"].append({
                        "answer_key": key, "question_id": qid, "draw": d, "task_id": task_id,
                        "error": f"{type(e).__name__}: {e}", "error_kind": "setup_error",
                        "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **_calls_of_answer(start)})
                    save_intermediate(intermediate, answers_path)
                    if isinstance(e, rr.RunStop):
                        # A4 (D67): the reranker failed to load; the run stops instead of going on without it
                        raise SystemExit(f"run {rid} stopped at {key}: {e}") from e
                    continue
                except RLMStop:
                    raise   # Q73 (D75): an RLM outcome that is neither an answer nor an RLMRunError; nothing stored
                except Exception as e:
                    # A5, Q30 (D68): stored with an empty answer and marked done, counted as a failure, never redrawn
                    logger.error(f"Error on {key}: {type(e).__name__}: {e}")
                    error, error_kind = f"{type(e).__name__}: {e}", "exception"
                    gen_result = {"answer": "", "error": error, "error_kind": error_kind}
                # answer_wall_s: the orchestrator's own (to its complete event), else the dispatch's (records.md F24)
                gen_result = {**gen_result,
                              "answer_wall_s": gen_result.get("answer_wall_s") or round(time.time() - t0, 3),
                              "llm_calls_reported": gen_result.get("llm_calls"), **_calls_of_answer(start),
                              "retrievals_bytes": [rstart, rr.offset(rr.RETRIEVALS)]}   # Q150: answer_search_s

            result = {
                "answer_key": key,
                "run_id": rid,
                "question_id": qid,
                "config": config,
                "draw": d,
                "task_id": task_id,
                "question": q["question"],
                "category": q["category"],
                "answerable": q["answerable"],
                "answer_type": q["answer_type"],
                "short_answer": q["short_answer"],
                "key_concepts": q["key_concepts"],
                "generation": gen_result,
                "generated_answer": gen_result.get("answer", ""),
                "error": gen_result.get("error"),
                "error_kind": gen_result.get("error_kind"),
                "plan_status": gen_result.get("plan_status"),
                "index_name": index_name,
                "gen_model": GEN_MODEL,
                "agent_roles": MODELS,
            }

            intermediate["results"].append(result)
            intermediate["completed_keys"].append(key)
            completed.add(key)
            save_intermediate(intermediate, answers_path)

        except Exception as e:
            # a failure outside the answer (the run context, the sidecar, the record) stops the run: nothing about
            # this answer could be stored (A5)
            logger.error(f"Error on {key} outside the answer: {type(e).__name__}: {e}")
            raise

    logger.info(f"Run {rid}: {len(intermediate['results'])} answers in {answers_path}")


async def run_generate(args):
    """Generate answers for every config x draw x question, one run per config."""
    if not args.base_url:
        raise SystemExit("--generate needs --base-url, the Ollama server the run contexts name")
    _check_index(args.index)
    questions, draws = _questions(args), _draws(args)
    configs = args.configs or CONFIG_NAMES

    user_id = find_admin_user_id()
    index_name = args.index

    if not check_index_exists(user_id, index_name):
        raise SystemExit(f"Index {index_name} not found or not ready")

    retriever, collection_name, _ = setup_retriever(user_id, index_name)
    router = ModelRouter()
    if any(c in TOOL_CONFIGS for c in configs):
        _discover_tools()

    total = len(configs) * len(draws) * len(questions)
    logger.info(f"V4-6 Orchestration ablation: {len(configs)} configs x {len(draws)} draws x {len(questions)} "
                f"questions = {total} answers")

    for config in configs:
        rid = run_id_for(config, index_name)
        sink = ex.sink(rid, root=args.sink_root) if args.sink_root else ex.sink(rid)
        # F5 (audit of 16 October): the index's content, so the passage ids the answers store resolve to text exactly
        index_identity.record(sink, index_name, collection_name, script="exp_03_orchestration_ablation.py")
        # the run-level context: checks every model against the lock and holds the run's identity before any answer
        run_ctx = ex.context(EXPERIMENT, config, None, draws[0], MODELS, base_url=args.base_url, run=rid, sink=sink)
        if config in TOOL_CONFIGS:
            with ex.tool_server(run_ctx) as sse_url:
                logger.info(f"Run {rid}: tool server at {sse_url}")
                await _run_config(config, rid, sink, questions, draws, args, retriever, collection_name, router,
                                  user_id)
        else:
            await _run_config(config, rid, sink, questions, draws, args, retriever, collection_name, router, user_id)

    logger.info("Generation complete")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V4-6: Orchestration Ablation (Figure 4; answers only, no judging)")
    parser.add_argument("--generate", action="store_true", help="Generate answers (Gemini only)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the work list (runs, sinks, answer keys, done or todo); no model call, no write")
    parser.add_argument("--base-url", default=None,
                        help="The Ollama server the run contexts name (required with --generate)")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="Index name (a 20-paper index, D48)")
    parser.add_argument("--configs", nargs="+", choices=CONFIG_NAMES + STRESS_CONFIG_NAMES,
                        help="Specific configs to run (default: CONFIG_NAMES; the Q82 stress conditions only by name)")
    parser.add_argument("--draws", nargs="+", type=int, default=None,
                        help="Draws to run, of Figure 4's 1 2 3 (D49; default all three)")
    parser.add_argument("--max-questions", type=int, default=None, help="Limit questions (smoke test)")
    parser.add_argument("--question-ids", nargs="+", default=None,
                        help="Only these of the 135 questions, in the key's order (Q147, D83: the smoke's list; "
                             "findings/recompute/G3_runs/smoke_ids.py)")
    parser.add_argument("--sink-root", type=Path, default=None,
                        help="Write each run's sink under this directory instead of findings/runs (smoke tests)")
    args = parser.parse_args()

    if args.generate == args.dry_run:
        parser.error("Specify --generate or --dry-run")

    if args.dry_run:
        run_dry(args)
    else:
        asyncio.run(run_generate(args))


if __name__ == "__main__":
    main()
