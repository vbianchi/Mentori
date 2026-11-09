#!/usr/bin/env python3
"""
V4-4: Generation Strategy Comparison (Fixed Scale)

With retrieval held constant at s20_n0, which generation strategy produces the
best answers?

Design:
  Index: exp_v4_s20_n0 (20 core papers, 0 noise)
  Questions: the 135 of answer key v2.4 (D48), from experiments/runner/experiment.py questions()
  6 configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass
  Draws: 1, 2, 3 (D49, Figure 2)
  Models: gemini::gemini-3-flash-preview generates every config (D27); the verified-pass verifier is
  ollama::gpt-oss:20b, a generator component at its maker's default, through the date-fixed copy the lock maps (Q18)
  matched_budget (D36, D51; run only when named): single pass with each question's top_k from the plan
  experiments/runner/matched_budget.py writes from the RLM-10 call records (--matched-budget-plan)

Each answer line stores the strategy's record (GenerationResult, D37): the passage ids of the generation prompt, every
call's tokens and stop reason (from calls.jsonl), the retrieval records (widths used, query_type, whether reranking
ran), multi-hop's hops, the verified pass's verdicts and fallback, the RLM's metadata, the matched-budget plan entry.
Every retrieval is also a line of <sink>/retrievals.jsonl. Each start appends the index's identity (collection and
content hashes, experiments/runner/index_identity.py) to <sink>/index_identity.jsonl of every run with an answer to
make, so the stored passage ids resolve to their text (F5).

Every answer runs inside its own run context, experiment.context() for its (question, draw), so every model call
goes through the lock (D67). One run per (config, index): run_id exp_01__<config>__<index>, sink
findings/runs/<run_id>/, which holds calls.jsonl (one record per model call) and answers.jsonl (one line per answer,
appended and fsynced, never rewritten). A smoke test (--max-questions) is its own run,
exp_01__<config>__<index>.smoke, as exp_02's (B9 F1), so its answers never sit in a paper run, and --sink-root puts
every sink under another directory, as exp_03's. An answer's key is <index>|<config>|<question_id>|d<draw>
(experiment.answer_key). The last line of a key is its answer; earlier lines are attempts that stored an error and
stay as the record of them (records.md F11). Generation stores answers only; they are judged later by the lock's
judge (A7, D67).

Scheduling (D80 V16, B9 O2): within each (draw, config) the pending answers run as a rolling pool
(experiments/runner/pool.py) of 6 (single_pass, multi_hop, verified_pass, matched_budget) or 2 (the RLM configs), the
old batch sizes: they start in work-list order, at most that many at once, and an answer that ends frees its slot for
the next, so one slow answer holds one slot instead of its batch. Each answer is stored as it ends, with "pool": the
pool's size and the answers in flight when it started, itself included.

Latency (Q150, D83): generation.latency_s stays the answer's clock time, from its start to its end while the others
of its pool ran (Q31, Q117: reported as measured, with the pool size). The latency compared between strategies is the
answer's own time: its model calls' time (generation.calls[].wall_s, every call) plus its search time. Every search
is timed where it runs (backend/retrieval/retriever.py, rlm/context.py): each retriever record (generation.retrievals
and <sink>/retrievals.jsonl) holds search_s and, of it, load_s (an encoder, the reranker or the keyword index loaded
during the call); the RLM's own log (generation.rlm.metadata.retrievals) holds search_s for every search and
navigation read, its search_semantic entries covering the retriever's call. An RLM answer's search time is the sum of
its log's search_s; its retrievals.jsonl lines are the search_semantic calls already in that log, so they are not
added again. Every search runs synchronously on the event loop (the strategies call retrieve() without awaiting it;
the RLM's code blocks run on the loop's thread), so no other answer's code or search runs in this process during it;
other answers' model calls go on in worker threads, and other processes share the machine's CPU.

Another generator (D83 Q173, D142; T2, Figure 2 panel f). --generator names the model of the role "generator" in
every config: the strategy's model (single pass, multi-hop, verified pass's answer, the RLM's root turns and its
sub-calls, all of which call the gen_model this script passes). The verified-pass verifier stays VERIFY_MODEL.
Without --generator the generator is GEN_MODEL (gemini::gemini-3-flash-preview) and nothing of G1 or G2 changes: run
ids, sinks, answer keys, records and printed lines are as before. Another generator is a cloud generator the lock
runs, anthropic::<model> (B11; claude-haiku-4-5) or gemini::<model> (a second Google model), or (D158 (2)) a local
ollama::<tag> the lock runs as a generator. It is checked against the lock at every draw of the run before anything
is read (an Anthropic call sends no seed: the draw is checked and recorded, LOCK [generation] seed, anthropic_client;
an Ollama generator through Lock.ollama, as every call of the run will build it). Its runs are named "+<model>" after the index (':' and '/' written '-'):
exp_01__<config>__<index>+claude-haiku-4-5, its smoke exp_01__<config>__<index>+claude-haiku-4-5.smoke, as exp_06
names T1's local generators (D97), so no generator resumes into another's run and a sink holds one configuration
(experiment.py IDENTITY). The answer key inside each run keeps its form, <index>|<config>|<question_id>|d<draw>; two
generators' answers are told apart by their run (run_id, sink) and gen_model, as exp_06's are. matched_budget is
refused with another generator: its plan comes from the reference generator's RLM-10 records (D51), and T2 runs the
six configs (D83 Q177).

A local generator (D158 (2)). --generator ollama::<tag> answers on --generator-url, its own Ollama server, and the
verified-pass verifier stays on --ollama-url (the run context's servers map, experiments/runner/run_context.py: the
generator's tag goes to --generator-url, every other Ollama call to --ollama-url); the two may name one server.
Everything sent is the lock's, built per call by Lock.ollama through the lock adapter, as for every Ollama call of the
experiments: the sampling row of [sampling.models] with the maker's default thinking ([thinking] generator "default",
[sampling.thinking_on]), seed the draw ([generation] seed; candidate and retry seeds where a caller names them, which
no exp_01 strategy does), num_ctx and num_predict from [generation] or the model's [exceptions] row, the date-fixed
copy [date] maps, truncate and shift false; before each call ollama_client checks the server's Ollama version and the
model's digest against [models] (a mismatch is a lock refusal and stops the run, Q38) and every call writes the
[record] fields. Refused before anything is read: a tag the lock does not run as a generator (no digest in [models],
no [sampling.models] row), glm-4.7-flash and the qwen3.5 models (NO_GENERAL_TASK_ROW: their [sampling.thinking_on]
rows are the makers' coding values, and a general-task row is needed before they answer questions, D83 Q181; a lock
edit, Valerio's), --generator-url missing or not an http(s) URL, --generator-url with a cloud generator, and in
verified_pass a generator whose tag is the verifier's on another server (one tag goes to one server). An Ollama
generator call that fails is not retried by any exp_01 strategy (as G1's Gemini calls were not; D81's retry seed is
for Mentori's step loop): it is recorded and the answer stored with its error, or for the RLM ends that answer
(call_error).

A local server's failure on resume (D160 (3), Valerio 27 October: Q19 O2, Q-L1). --rerun-server-failures, with
--resume --skip-failed and a local ollama:: generator only, narrows --skip-failed: a key whose last line is a failure
of our own Ollama server (server_failure: the call that ended the answer failed with a stall, an HTTP 5xx, a refused
or dropped connection, a stream cut short, a runner that stopped, or a server that could not be read before the
request) runs again; its error line stays as the record of that attempt and the new line is appended, the last line
of a key being its answer. A rerun is a first try under a new run context with the same draw, so it sends the same
seed, the draw. Every other failed key keeps its error line as its answer (D143 O4): the model's own failures (a
prompt over the context, HTTP 400; a turn cap, the RLM's max_turns_empty), any error not named above, and every
cloud generator's (the option is refused with one). Without the option nothing changes.

A question filter for a paper run (D159 (2), D98; the same option, file and rule as exp_02's and exp_06's, D112 Q11).
--question-ids-file runs only the questions a JSON file names (D98's subset, findings/recompute/D98_subset/
d98_subset.json, written by scripts/S464_d98_subset.py: 45 of the 135), in the key's order. It is not a smoke: run
ids, sinks and answer keys are the ones without the filter, so T2's gemini-2.5-pro draws 2 and 3 resume into the runs
of its draw 1, their keys (...|d2, ...|d3) distinct from draw 1's, and each answer is the one an unfiltered start would
store for its key. Each answer line the start stores holds the filter's record under "question_filter" (the file, its
sha256, the counts, the draws); a start without the filter stores no such key, so its lines are as before.
read_ids_file and run_questions say what is refused (a file that is not such a JSON, an unknown or repeated id, the
option with --max-questions), before anything is read or written.

The gate-off arm (D238, G14). --configs rlm_10_nogate runs rlm_10's call (_run_rlm, max_turns 10, the same generator,
index, lock and seed rule) with RLMOrchestrator(quality_gate=False): no final answer is refused for too few sub-calls
or no substance (rlm/orchestrator.py GATE_OFF_RECORD). It is run only when named, and only with --question-ids-file or
as a smoke (check_nogate). Its run is exp_01__rlm_10_nogate__<index>, its keys <index>|rlm_10_nogate|<question>|d<draw>,
its run_identity.json arm rlm_10_nogate, and every answer's generation.rlm.metadata.quality_gate is GATE_OFF_RECORD, so
none of its answers can be read as a gated one. Without it nothing changes.

The search-off arm (D239, arm B, G16). --configs rlm_10_nosearch runs rlm_10's call (_run_rlm, max_turns 10, the same
generator, index, lock, seed rule and quality gate) with RLMOrchestrator(search_tools=False): the RLM's REPL has no
search_keyword, search_regex or search_semantic (a call fails in the block's output and is logged), its navigation
reads stay, and its prompt names no search function (rlm/orchestrator.py SEARCH_OFF_RECORD). It is run only when named,
and only with --question-ids-file or as a smoke (check_nogate). Its run is exp_01__rlm_10_nosearch__<index>[+<model>],
its keys <index>|rlm_10_nosearch|<question>|d<draw>, its run_identity.json arm rlm_10_nosearch, and every answer's
generation.rlm.metadata.search_tools is SEARCH_OFF_RECORD with the run's refused attempts, so none of its answers can be
read as one with search. Without it nothing changes.

The control arm (D240, G17). --configs rlm_10_ctrl runs rlm_10's call exactly (_run_rlm, max_turns 10, the same
generator, index, lock, seed rule, quality gate and search functions) under its own name: the control R' of D240, on
today's code beside the two switches, without touching G1's runs. It is run only when named, and only with
--question-ids-file or as a smoke (check_nogate). Its run is exp_01__rlm_10_ctrl__<index>[+<model>], its keys
<index>|rlm_10_ctrl|<question>|d<draw>, its run_identity.json arm rlm_10_ctrl; its RLM record has neither a
quality_gate nor a search_tools key, as rlm_10's. Without it nothing changes.

Primary metric: % pass rate (correctness >= 3)
Secondary: % correct refusal (unanswerable), median latency

Usage:
    # The work list, without a model call or a file written
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py --dry-run

    # Full run
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --ollama-url http://127.0.0.1:21441

    # Smoke test: runs exp_01__single_pass__<index>.smoke, never the paper run; --sink-root keeps it out of findings/runs
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --ollama-url http://127.0.0.1:21441 --configs single_pass --max-questions 3 --draws 1 \\
        --sink-root findings/recompute/B9_smoke/exp01_sinks

    # Resume (skips the keys whose answer is stored without an error; a key stored with an error runs again)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --ollama-url http://127.0.0.1:21441 --resume

    # Resume that skips every stored key, failed or not (Q141 restart, D83): a key whose last line stores an error
    # keeps that line as its answer and is not run again (D80 V1: a Gemini call is never retried)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --ollama-url http://127.0.0.1:21441 --resume --skip-failed

    # Resume of a local generator (D160 (3)): as --skip-failed, except that a key whose last line is a failure of our
    # own Ollama server (server_failure) runs again with the same seed
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --generator ollama::gemma3:27b --generator-url http://127.0.0.1:<port> --ollama-url http://127.0.0.1:<port> \\
        --resume --skip-failed --rerun-server-failures

    # T2 (D142): claude-haiku-4-5 as the generator; its own runs (exp_01__<config>__<index>+claude-haiku-4-5)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --generator anthropic::claude-haiku-4-5 --dry-run

    # T2 (D158 (2)): a local generator on its own server, the verifier on --ollama-url
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --generator ollama::gemma3:27b --generator-url http://127.0.0.1:<port> --ollama-url http://127.0.0.1:<port>

    # T2 (D159 (2), D98): gemini-2.5-pro's draws 2 and 3 on D98's 45 questions, into the runs of its draw 1
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py \\
        --generator gemini::gemini-2.5-pro --ollama-url http://127.0.0.1:11499 --configs rlm_10 --draws 2 3 \\
        --question-ids-file findings/recompute/D98_subset/d98_subset.json
"""

import argparse
import asyncio
import collections
import functools
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
from backend.agents import lock_adapter  # noqa: F401  (puts the reanalysis root on sys.path for experiments.runner)
from backend.retrieval.pipeline import PipelineConfig

from experiments.runner import anthropic_client
from experiments.runner import experiment as ex
from experiments.runner import index_identity
from experiments.runner import pool
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError, load as load_lock

from exp_common import (
    GEN_MODEL, JUDGE_MODEL,
    find_admin_user_id, check_index_exists,
    setup_retriever,
    save_v4_results, save_v4_markdown,
    compute_pass_rate, compute_refusal_rate, compute_median_latency,
    compute_mean_source_coverage, compute_mean_score,
    aggregate_v4_metrics, detect_judge_key,
    format_v4_table, format_pct, format_latency, format_score,
    V4_DIR, V4_RESULTS_DIR,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _AnswerCalls, failed_answer, REFUSALS, STOPS,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_01_generation")
logger.setLevel(logging.INFO)


def _index_core_size(index_name: str) -> int:
    """Extract core paper count from index name like 'exp_v4_s20_n0'."""
    import re
    m = re.search(r"_s(\d+)_", index_name)
    return int(m.group(1)) if m else 50

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

EXPERIMENT = "exp_01"
FIGURE = 2                      # D49: draws 1, 2, 3
ANSWERS = "answers.jsonl"       # <sink>/answers.jsonl, one line per answer, appended through run_context.append
RUNS_ROOT = ex.RUNS             # findings/runs/: each run's sink is RUNS_ROOT/<run_id>
DEFAULT_INDEX = "exp_v4_s20_n0"

# The models of each config, as Mentori agent role -> model identifier (the run context's agent_roles and
# allow-list). The verifier is the model PipelineConfig.verified() calls (pipeline.py verify_model); it runs as a
# generator component (D66), and the lock sends it to the date-fixed copy gpt-oss:20b-date20261010 ([date]).
VERIFY_MODEL = "ollama::gpt-oss:20b"     # Q18
CLOUD_GENERATORS = ("anthropic", "gemini")   # D83 Q173: the providers --generator takes besides the default
LOCAL_GENERATOR = "ollama"                  # D158 (2): a local generator, on --generator-url
# D83 Q181: [sampling.thinking_on] holds these rows' coding values (LOCK.toml: "to be settled before any of them
# generates answers to questions"); a general-task row is a lock edit, Valerio's. Matched on the [sampling.models] row
# the tag reads (lock._lookup); lifted here once the lock holds their general-task rows.
NO_GENERAL_TASK_ROW = ("glm-4.7-flash", "qwen3.5:35b", "qwen3.5:122b")


def generator_tag(generator: str) -> str:
    """"" for the default generator (GEN_MODEL: every G1 and G2 name as before), else "+<model>" with ':' and '/'
    written '-' (anthropic::claude-haiku-4-5 -> "+claude-haiku-4-5"), which follows the index in the run_id (D83 Q173,
    as exp_06's generator_tag, D97)."""
    if generator == GEN_MODEL:
        return ""
    return "+" + re.sub(r"[:/]", "-", generator.split("::", 1)[1])


def is_local(generator: str) -> bool:
    """True for an ollama::<tag> generator (D158 (2))."""
    return generator.partition("::")[0] == LOCAL_GENERATOR


def check_generator(generator: str, draws: tuple = (1,)) -> str:
    """--generator: GEN_MODEL (the default), or anthropic::<model> or gemini::<model> that the lock runs as a
    generator at every draw of the run (anthropic_client.settings after the draw's seed check; Lock.gemini), or
    (D158 (2)) ollama::<tag> that the lock runs as a generator at every draw (Lock.ollama, role generator, the maker's
    default thinking, as every call of the run builds it) and that is not one of NO_GENERAL_TASK_ROW (D83 Q181).
    Anything else is refused here, before an index, a database or a sink is read (D83 Q173). Returns the generator."""
    if generator == GEN_MODEL:
        return generator
    provider, _, name = generator.partition("::")
    if (provider not in CLOUD_GENERATORS + (LOCAL_GENERATOR,) or not name or name != name.strip() or "[" in name
            or "]" in name):
        raise SystemExit(f"--generator {generator!r}: {GEN_MODEL} (the default), anthropic::<model> or "
                         f"gemini::<model> (a cloud generator the lock runs), or ollama::<tag> (a local generator the "
                         f"lock runs, on --generator-url); nothing run")
    lock = load_lock()
    if provider == LOCAL_GENERATOR:
        from experiments.runner.lock import _lookup
        row, _ = _lookup(lock.d["sampling"]["models"], name)
        if row in NO_GENERAL_TASK_ROW:
            raise SystemExit(f"--generator {generator!r}: its [sampling.thinking_on] row {row!r} holds the maker's "
                             f"coding values, and a general-task row is needed before it answers questions (D83 Q181; "
                             f"a lock edit, Valerio's); nothing run")
    try:
        for d in draws:
            if provider == "anthropic":
                lock._seed(d, None)                      # the draw is checked and recorded; no seed is sent (B11)
                anthropic_client.settings(lock, name)
            elif provider == "gemini":
                lock.gemini(name, d)
            else:
                lock.ollama(name, role="generator", draw=d)   # D158 (2): digest in [models], sampling row, seed
    except LockError as e:
        raise SystemExit(f"--generator {generator!r}: the lock does not run it as a generator ({e}); nothing run")
    return generator


def generator_servers(configs: List[str], generator: str, generator_url: Optional[str],
                      base_url: Optional[str] = None) -> Optional[Dict[str, str]]:
    """The run contexts' servers map (D158 (2)): {the generator's tag: generator_url} for a local generator, None for
    any other (every Ollama call then goes to --ollama-url, as before). Refuses a local generator without an http(s)
    --generator-url, a --generator-url with any other generator, and, when base_url is given and verified_pass runs, a
    generator whose tag is the verifier's on a server other than base_url (a tag goes to one server)."""
    if not is_local(generator):
        if generator_url is not None:
            raise SystemExit(f"--generator-url is for a local ollama:: generator; --generator {generator!r} makes no "
                             f"call there; nothing run")
        return None
    if not isinstance(generator_url, str) or not generator_url.startswith(("http://", "https://")):
        raise SystemExit(f"--generator {generator!r} answers on --generator-url, an http(s) URL of its Ollama server "
                         f"(got {generator_url!r}); nothing run")
    tag = generator.split("::", 1)[1]
    if (base_url is not None and "verified_pass" in configs and tag == VERIFY_MODEL.split("::", 1)[1]
            and generator_url.rstrip("/") != base_url.rstrip("/")):
        raise SystemExit(f"--generator {generator!r} is the verifier's model: in verified_pass both go to one server, "
                         f"and --generator-url {generator_url} is not --ollama-url {base_url}; nothing run")
    return {tag: generator_url}

CONFIG_NAMES = [
    "single_pass",
    "multi_hop",
    "rlm_5",
    "rlm_10",
    "rlm_20",
    "verified_pass",
]

MATCHED_BUDGET = "matched_budget"           # D51: run only when named, and only with --matched-budget-plan
CUT_ARM = "single_pass_cut800"               # D196: single pass with April's 800-character cut, run only when named;
PASSAGE_CUT = 800                            # the one exception to LOCK.toml [text] component_cuts, by Valerio's word
NOGATE_ARM = "rlm_10_nogate"                 # D238 (G14): rlm_10 with the RLM's quality gate off (RLMOrchestrator
                                             # quality_gate=False), run only when named and only on named questions
NOSEARCH_ARM = "rlm_10_nosearch"             # D239 (arm B): rlm_10 with the RLM's search functions removed
                                             # (RLMOrchestrator search_tools=False), run only when named and on named
                                             # questions
CTRL_ARM = "rlm_10_ctrl"                     # D240 (G17, R'): rlm_10's call under its own name, run only when named
                                             # and on named questions
NAMED_QUESTIONS_ARMS = ((NOGATE_ARM, "D238"), (NOSEARCH_ARM, "D239"), (CTRL_ARM, "D240"))
ALL_CONFIGS = CONFIG_NAMES + [MATCHED_BUDGET]

CATEGORIES = [
    "factual_recall", "conceptual", "technical",
    "synthesis", "cross_document", "out_of_domain",
]


def load_budget_plan(path: Optional[Path], configs: List[str], questions: List[Dict]) -> Optional[Dict]:
    """The matched-budget plan (experiments/runner/matched_budget.py plan) when the matched_budget config runs: it
    must name a top_k for every question of the run. Returns {"sha256", "path", "questions"}; None otherwise."""
    if MATCHED_BUDGET not in configs:
        if path is not None:
            raise SystemExit("--matched-budget-plan is given, and the matched_budget config is not in --configs")
        return None
    if path is None:
        raise SystemExit("the matched_budget config needs --matched-budget-plan (D51)")
    import hashlib
    raw = Path(path).read_bytes()
    plan = json.loads(raw)
    if plan.get("kind") != "matched_budget_plan":
        raise SystemExit(f"{path} is not a matched-budget plan")
    entries = plan.get("questions") or {}
    missing = [q["id"] for q in questions
               if not isinstance((entries.get(q["id"]) or {}).get("top_k"), int) or entries[q["id"]]["top_k"] < 1]
    if missing:
        raise SystemExit(f"{path} names no top_k for {len(missing)} questions of the run, first {missing[:3]}")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "path": str(path), "questions": entries}


def check_plan_matches(answers: Path, sha256: str) -> None:
    """Refuses a matched-budget run whose answers.jsonl already holds an answer made under another plan, so one run
    never mixes two plans (D51). Each line's generation.matched_budget.plan_sha256 is compared with the plan given."""
    if not answers.exists():
        return
    with open(answers, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            rec = json.loads(line)
            other = ((rec.get("generation") or {}).get("matched_budget") or {}).get("plan_sha256")
            if other != sha256:
                raise SystemExit(f"{answers}:{n} was made under plan sha256 {other!r}, and this run's plan is "
                                 f"{sha256}; one matched-budget run holds one plan (D51). Name another index or "
                                 f"move the run aside.")


def read_ids_file(path, known: Optional[List[str]] = None) -> tuple:
    """D159 (2) (D98, as exp_02's and exp_06's, D112 Q11): (the question ids a --question-ids-file names, in the file's
    order; the filter's record). The file holds a JSON list of ids, or an object whose "ids" is one
    (findings/recompute/D98_subset/d98_subset.json, written by scripts/S464_d98_subset.py). Each id must be one of the
    135 questions of answer key v2.4 (known; D48), named once. Refused before anything is read or written: a file that
    is not such a JSON, an unknown or repeated id."""
    import hashlib
    path = Path(path)
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, ValueError) as e:
        raise SystemExit(f"--question-ids-file {path}: not a JSON file ({e}); nothing run")
    ids = data.get("ids") if isinstance(data, dict) else data
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
        raise SystemExit(f"--question-ids-file {path}: holds no list of question ids (a list, or an object with "
                         f"\"ids\"); nothing run")
    known = set(known if known is not None else (q["id"] for q in ex.questions()))
    unknown = [i for i in ids if i not in known]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    if unknown or repeated:
        raise SystemExit(f"--question-ids-file {path}: {unknown[:5]} not among the {len(known)} questions (D48); "
                         f"{repeated[:5]} named twice; nothing run")
    return list(ids), {"option": "--question-ids-file", "file": str(path),
                       "file_sha256": hashlib.sha256(raw).hexdigest(), "n_named": len(ids)}


def check_nogate(configs: List[str], max_questions: Optional[int], question_ids_file: Optional[Path]) -> None:
    """D238: NOGATE_ARM runs only on named questions (--question-ids-file, the G14 list) or as a smoke
    (--max-questions); a start of it over the 135 is refused before anything is read. D239: NOSEARCH_ARM the same
    (arm B's list, G16). D240: CTRL_ARM the same (G17's 86)."""
    for arm, decision in NAMED_QUESTIONS_ARMS:
        if arm in configs and question_ids_file is None and max_questions is None:
            raise SystemExit(f"{arm} ({decision}) runs on the questions a --question-ids-file names, or as a smoke "
                             f"(--max-questions); nothing run")


def run_questions(max_questions: Optional[int], question_ids_file: Optional[Path], draws: tuple) -> tuple:
    """(the questions a start runs, in the key's order; the question filter's record, or None without one).
    --max-questions: the first n (a smoke). --question-ids-file (D159 (2)): only the questions the file names, a paper
    run, not a smoke: run ids, sinks and answer keys are the ones without the filter, so draws 2 and 3 of D98's subset
    resume into the runs of draw 1 (as exp_02's and exp_06's filter, D112 Q11), each answer the one an unfiltered start
    would store for its key. The two options together are refused (one way of naming the questions, as exp_02)."""
    questions = ex.questions()
    if question_ids_file is None:
        return (questions[:max_questions] if max_questions else questions), None
    if max_questions is not None:
        raise SystemExit("--question-ids-file with --max-questions: name the questions one way; nothing run")
    keep, record = read_ids_file(question_ids_file, [q["id"] for q in questions])
    named = set(keep)
    kept = [q for q in questions if q["id"] in named]
    record.update(n_kept=len(kept), n_set=len(questions), draws=list(draws))
    return kept, record


def filter_line(record: Dict) -> str:
    """The printed and logged line of a start with a question filter (D159 (2))."""
    return (f"question filter (--question-ids-file {record['file']}, sha256 {record['file_sha256'][:12]}): "
            f"{record['n_kept']} of the {record['n_set']} questions, draws {record['draws']}; run ids and answer keys "
            f"unchanged")


# ─────────────────────────────────────────────────────────────
# Config dispatch (reuses exp1 generators)
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
    budget: Optional[Dict] = None,
) -> GenerationResult:
    """Dispatch to the right generator based on config name. budget: the question's matched-budget plan entry."""
    if config_name == "single_pass":
        return await _single_pass_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == MATCHED_BUDGET:
        return await _single_pass_rag(question, retriever, collection_name, router, gen_model,
                                      top_k=budget["top_k"], config_name=MATCHED_BUDGET, matched_budget=budget)
    elif config_name == CUT_ARM:
        return await _single_pass_rag(question, retriever, collection_name, router, gen_model,
                                      config_name=CUT_ARM, passage_cut=PASSAGE_CUT)
    elif config_name == "multi_hop":
        return await _multi_hop_rag(question, retriever, collection_name, router, gen_model)
    elif config_name == "rlm_5":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=5, config_name="rlm_5", index_name=index_name)
    elif config_name == "rlm_10":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name="rlm_10", index_name=index_name)
    elif config_name == NOGATE_ARM:
        # D238: rlm_10's call, the one change the gate off; the arm's name is its run_id, run identity and answer config
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name=NOGATE_ARM,
                              index_name=index_name, quality_gate=False)
    elif config_name == CTRL_ARM:
        # D240: rlm_10's call, nothing changed; the arm's name is its run_id, run identity and answer config
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name=CTRL_ARM,
                              index_name=index_name)
    elif config_name == NOSEARCH_ARM:
        # D239: rlm_10's call, the one change the search functions removed; the arm's name is its run_id, run identity
        # and answer config
        return await _run_rlm(question, router, gen_model, user_id, max_turns=10, config_name=NOSEARCH_ARM,
                              index_name=index_name, search_tools=False)
    elif config_name == "rlm_20":
        return await _run_rlm(question, router, gen_model, user_id, max_turns=20, config_name="rlm_20", index_name=index_name)
    elif config_name == "verified_pass":
        return await _verified_pass_rag(question, retriever, collection_name, router, gen_model)
    else:
        raise ValueError(f"Unknown config: {config_name}")


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

def config_models(config: str, generator: str = GEN_MODEL) -> Dict[str, str]:
    """The Mentori agent roles a config runs and their models: the generator (--generator, D83 Q173) for every
    config, and the verifier for verified_pass only, so no other config's run allows gpt-oss:20b. The verifier is
    VERIFY_MODEL whatever the generator."""
    models = {"generator": generator}
    if config == "verified_pass":
        models["verifier"] = VERIFY_MODEL
    return models


def config_run_id(config: str, index_name: str, smoke: bool = False, generator: str = GEN_MODEL) -> str:
    """exp_01__<config>__<index>: one run, and one sink, per (config, index). A smoke test (--max-questions) is its own
    run, exp_01__<config>__<index>.smoke (as exp_02's run_name), so its answers never sit in a paper run (B9 F1).
    Another generator's runs carry generator_tag after the index (D83 Q173): exp_01__<config>__<index>+<model>[.smoke]."""
    extra = index_name + generator_tag(generator)
    return ex.run_id(EXPERIMENT, config, f"{extra}.smoke" if smoke else extra)


def runs_root(sink_root: Optional[Path]) -> Path:
    """Where each run's sink is: --sink-root when given (smoke tests, as exp_03's), else RUNS_ROOT (findings/runs)."""
    return Path(sink_root) if sink_root is not None else RUNS_ROOT


def _answer_record(key: str, config: str, q: Dict, draw: int, index_name: str,
                   gen_result: GenerationResult, pool: Optional[Dict] = None, generator: str = GEN_MODEL,
                   question_filter: Optional[Dict] = None) -> Dict:
    """One line of answers.jsonl. run_context.append adds run_id, item_id, arm, run_draw, ctx_uid, seq and pid. pool:
    the rolling pool's size and the answers in flight when this one started, itself included (D80 V16). generator:
    the run's generator (D83 Q173), its gen_model and models. question_filter: the start's --question-ids-file record
    (D159 (2)), stored under "question_filter" only when the start had one, so an unfiltered line is as before."""
    return {
        "answer_key": key,
        "experiment": EXPERIMENT,
        "config": config,
        "question_id": q["id"],
        "draw": draw,
        "index_name": index_name,
        "question": q["question"],
        "category": q.get("category", "unknown"),
        "answerable": q["answerable"],
        "gen_model": generator,
        "models": config_models(config, generator),
        "generation": asdict(gen_result),
        "pool": pool,
        **({"question_filter": question_filter} if question_filter is not None else {}),
    }


async def _process_one(
    config: str,
    q: Dict,
    ctx: rc.RunContext,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
    budget: Optional[Dict] = None,
    generator: str = GEN_MODEL,
) -> GenerationResult:
    """Generate one (config, question, draw) answer inside its run context. Judging is a later step (A7, D67). A
    strategy that raises gives failed_answer: the error, unknown counts None and the calls made before it (A5, D37).
    A lock refusal (REFUSALS) is not caught: run_experiment starts no other answer, stores the ones in flight and ends
    the run (Q38). generator: the strategy's gen_model (D83 Q173)."""
    t0 = time.time()
    with rc.run(ctx):
        log = _AnswerCalls()
        try:
            return await _run_config(
                config_name=config,
                question=q["question"],
                retriever=retriever,
                collection_name=collection_name,
                router=router,
                gen_model=generator,
                user_id=user_id,
                index_name=index_name,
                budget=budget,
            )
        except STOPS:
            raise   # a lock refusal (Q38) or an RLMStop (Q73, D75): nothing stored for the key
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            gen = failed_answer(config, generator, e, log, time.time() - t0)
            if budget is not None:
                gen.top_k, gen.matched_budget = budget["top_k"], budget   # the plan it ran under (D51)
            return gen


def stored_answers(path: Path) -> Dict[str, tuple]:
    """Each answer key stored in an answers.jsonl -> (line number, error) of its last line (empty when the file does
    not exist). The last line of a key is its answer; earlier lines are attempts that stored an error (F11, F25). A
    line that is not a JSON answer record, or a key stored again after a line without an error (two answers under one
    key, as two runs of the same config and index would write), is refused, never skipped or merged."""
    last: Dict[str, tuple] = {}
    if not path.exists():
        return last
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
                key, error = rec["answer_key"], rec["generation"].get("error")
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                raise SystemExit(f"{path}:{n} is not an answer record ({e!r}); the run does not resume over it")
            if key in last and not last[key][1]:
                raise SystemExit(f"{path}:{n} stores {key} again after its answer at line {last[key][0]}; one key "
                                 f"has one answer, and the run does not resume over it")
            last[key] = (n, error)
    return last


def present_keys(path: Path) -> set:
    """The answer keys whose last line stores an answer without an error: the keys a resume skips."""
    return {k for k, (_, error) in stored_answers(path).items() if not error}


# D160 (3) (Q19 O2, Q-L1): the failures of our own Ollama server, read from the (status, error) that ollama_client._read
# and lock_adapter._unreached store on a call record and call_summary copies into the answer line (generation.calls):
#   stalled             status "stalled", "no new token for <stall_s> s" (LOCK [generation] stall_s, after the first token)
#   HTTP 5xx            status "error", "HTTP 5nn: <the server's text>" (a 500 before the stream began: a runner that
#                       crashed or could not load; a 503: the server's queue full)
#   connection refused  status "error", "URLError: <urlopen error [Errno 61] Connection refused>" (nothing listening)
#   dropped connection  status "error", a text naming lock_adapter._DROPPED (RemoteDisconnected, ConnectionResetError,
#                       "Connection reset by peer", "Server disconnected")
#   dropped stream      status "error", "the stream ended without a final chunk" or "IncompleteRead: ..." (lock_adapter
#                       _NO_FINAL_CHUNK, _CUT_CHUNK)
#   runner stopped      status "error", the server's own text inside a stream that began 200 OK, naming a runner that
#                       stopped or terminated ("model runner has unexpectedly stopped", lock_adapter's D83 Q155 example)
#   server not reached  status "error", "before the request was posted: <OSError>" (lock_adapter._unreached: the
#                       server's version or tag list could not be read)
# A text naming the context's size (a prompt over num_ctx: "HTTP 400: ... exceed_context_size_error ...",
# findings/recompute/S3_runs/README.md; "the input length exceeds the context length"; "prompt is too long"; the lock
# cuts nothing, so it fails the same way every time) is never one of them, whatever its status; Go's "context deadline
# exceeded" (a server timeout) does not name the size and stays a server failure when its class matches. Not a server
# failure either: Ollama's "error parsing tool call" (the model's reply), "cancelled" (our own process went away), and
# any other error, which keeps D143 O4.
SERVER_FAILURE_NOT_CONTEXT = re.compile(r"context (?:length|size|window)|exceed_context|exceeds? (?:the )?(?:maximum )?"
                                        r"context|too long|num_ctx", re.IGNORECASE)
SERVER_FAILURE_RUNNER = re.compile(r"runner (?:process )?has (?:unexpectedly )?(?:stopped|terminated)", re.IGNORECASE)


def server_error(status: Optional[str], error: Optional[str]) -> Optional[str]:
    """The class of a failed Ollama call's (status, error) when the failure is our server's (the table above), else
    None."""
    err = str(error or "")
    if SERVER_FAILURE_NOT_CONTEXT.search(err):
        return None
    if status == "stalled":
        return "stalled"
    if status != "error":
        return None
    if err.startswith("before the request was posted: "):
        return "server not reached"
    if re.match(r"HTTP 5\d\d\b", err):
        return "HTTP 5xx"
    if "Connection refused" in err:
        return "connection refused"
    if any(d in err for d in lock_adapter._DROPPED):
        return "dropped connection"
    if err == lock_adapter._NO_FINAL_CHUNK or err.startswith(lock_adapter._CUT_CHUNK):
        return "dropped stream"
    if SERVER_FAILURE_RUNNER.search(err):
        return "runner stopped"
    return None


def ending_call(gen: Dict) -> Optional[Dict]:
    """The call record (call_summary) that ended a failed answer: for an RLM answer the root call its call_error names
    (stop_reason call_error; a run that ended max_turns_empty has none, whatever its sub-calls did); for single pass,
    multi-hop and verified pass the answer's last call, when it failed (status neither ok nor length) and the answer's
    error is that call's (str(LockCallError) names the call's error text; a verifier call that failed fail-open and an
    exception raised after it is not). None otherwise."""
    calls = gen.get("calls") or []
    if gen.get("rlm") is not None:
        ce = ((gen.get("rlm") or {}).get("metadata") or {}).get("call_error")
        if gen.get("stop_reason") != "call_error" or not ce:
            return None
        return next((c for c in calls if c.get("seq") == ce.get("seq")), None)
    last = calls[-1] if calls else None
    if last is None or last.get("status") in ("ok", "length"):
        return None
    return last if str(last.get("error") or "") in str(gen.get("error") or "") else None


def server_failure(rec: Dict) -> Optional[str]:
    """D160 (3): the server_error class of an answer line that a resume with --rerun-server-failures runs again: a line
    stored with an error, by a local ollama:: generator's run, whose ending call (ending_call) is an Ollama call that
    failed on our own server. None for every other line (a cloud generator's included)."""
    gen = rec.get("generation") or {}
    if not gen.get("error") or not is_local(str(rec.get("gen_model") or "")):
        return None
    call = ending_call(gen)
    if call is None or call.get("provider") != "ollama":
        return None
    return server_error(call.get("status"), call.get("error"))


def server_failures(path: Path) -> Dict[str, str]:
    """Each answer key whose last line in an answers.jsonl is a server failure -> its class (server_failure). The
    last line of a key is its answer (stored_answers, which work_list has already read and checked)."""
    last: Dict[str, Dict] = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                last[rec["answer_key"]] = rec
    return {k: c for k, rec in last.items() if (c := server_failure(rec))}


def check_rerun_server_failures(skip_failed: bool, generator: str) -> None:
    """--rerun-server-failures narrows --skip-failed for a local generator only (D160 (3)); refused otherwise, before
    anything is read."""
    if not skip_failed:
        raise SystemExit("--rerun-server-failures narrows --skip-failed: pass --resume --skip-failed with it. "
                         "Nothing was started.")
    if not is_local(generator):
        raise SystemExit(f"--rerun-server-failures is for a local ollama:: generator (D160 (3)); {generator} keeps "
                         f"D143 O4 (--skip-failed). Nothing was started.")


def rerun_server_failures_in(items: List[Dict], root: Optional[Path] = None) -> List[Dict]:
    """D160 (3): work_list's items (skip_failed) with each failed key whose last line is a server failure set to run
    again (skip False, retry True); every item gains "server_failure", its class or None. Reads the answers files under
    root (RUNS_ROOT when None); writes nothing."""
    root = runs_root(root)
    found: Dict[str, Dict[str, str]] = {}
    out = []
    for i in items:
        if i["run_id"] not in found:
            found[i["run_id"]] = server_failures(root / i["run_id"] / ANSWERS)
        cls = found[i["run_id"]].get(i["key"]) if i["failed"] else None
        out.append({**i, "server_failure": cls, **({"skip": False, "retry": True} if cls else {})})
    return out


def rerun_line(items: List[Dict]) -> str:
    """The printed and logged line of a start with --rerun-server-failures (D160 (3))."""
    classes = collections.Counter(i["server_failure"] for i in items if i.get("server_failure"))
    kept = sum(i["failed"] and i["skip"] for i in items)
    return (f"--rerun-server-failures (D160 (3)): {sum(classes.values())} keys whose last line is a failure of our own "
            f"Ollama server run again with the same seed ({', '.join(f'{c} {n}' for c, n in sorted(classes.items())) or 'none'}); "
            f"{kept} keys whose last line stores another error count as stored and are not run again (D143 O4)")


def work_list(configs: List[str], questions: List[Dict], draws: tuple, index_name: str, smoke: bool = False,
              root: Optional[Path] = None, skip_failed: bool = False, generator: str = GEN_MODEL) -> List[Dict]:
    """Every (draw, config, question) of the run, in run order (draw, then config, then question), with its run_id
    (the .smoke run's when smoke), answer key, whether its answer is stored without an error (present), whether its
    last line stores an error (failed), and whether a resume skips it (skip) or runs it again (retry). A failed key
    runs again (retry) unless skip_failed (--skip-failed, Q141 restart of D83), when it is skipped as a stored answer
    is: skip = present, or failed and skip_failed; retry = failed and not skip_failed. Reads the answers files under
    root (RUNS_ROOT when None); writes nothing. generator: whose runs (config_run_id, D83 Q173)."""
    root = runs_root(root)
    items = []
    stored = {}
    for draw in draws:
        for config in configs:
            rid = config_run_id(config, index_name, smoke, generator)
            if rid not in stored:
                stored[rid] = stored_answers(root / rid / ANSWERS)
            for q in questions:
                key = ex.answer_key(config, q["id"], draw, index=index_name)
                last = stored[rid].get(key)
                present, failed = last is not None and not last[1], last is not None and bool(last[1])
                items.append({"draw": draw, "config": config, "q": q, "run_id": rid, "key": key,
                              "present": present, "failed": failed,
                              "skip": present or (failed and skip_failed),
                              "retry": failed and not skip_failed})
    return items


def _check_generator_configs(configs: List[str], generator: str) -> None:
    """matched_budget runs with the default generator only (its plan is the reference generator's RLM-10 budget, D51;
    T2 runs the six configs, D83 Q177)."""
    if generator != GEN_MODEL and MATCHED_BUDGET in configs:
        raise SystemExit(f"--generator {generator!r} with matched_budget: the plan is {GEN_MODEL}'s RLM-10 budget (D51) "
                         f"and T2 runs the six configs (D83 Q177); nothing run")


def _check_models(configs: List[str], draws: tuple, generator: str = GEN_MODEL) -> None:
    """Refuses, before anything starts, a config whose verifier is not the one the pipeline calls, or a model the
    lock does not run at one of the draws (a check of the lock file only; no server is contacted)."""
    if PipelineConfig.verified().verify_model != VERIFY_MODEL:
        raise SystemExit(f"PipelineConfig.verified() calls {PipelineConfig.verified().verify_model!r} as its "
                         f"verifier, and this run allows {VERIFY_MODEL!r}")
    lock = load_lock()
    for config in configs:
        for role, ident in config_models(config, generator).items():
            provider, name = ident.split("::", 1)
            for d in draws:
                if provider == "gemini":
                    lock.gemini(name, d)
                elif provider == "anthropic":                  # B11: T2's claude-haiku-4-5
                    lock._seed(d, None)
                    anthropic_client.settings(lock, name)
                else:
                    lock.ollama(name, role="generator", draw=d)


def dry_run(configs: List[str], max_questions: Optional[int], index_name: str, draws: tuple,
            matched_budget_plan: Optional[Path] = None, sink_root: Optional[Path] = None,
            skip_failed: bool = False, generator: str = GEN_MODEL, generator_url: Optional[str] = None,
            question_ids_file: Optional[Path] = None, rerun_server_failures: bool = False) -> None:
    """Prints the work list and its counts, as a run with the same skip_failed would work it (stored: the keys it
    skips). No model call, no index or database read, no file written. generator: --generator (D83 Q173); with the
    default every printed line is as before. generator_url (D158 (2)): a local generator's server, printed when given;
    the dry run does not need it. question_ids_file (D159 (2)): run_questions; one more line names the filter.
    rerun_server_failures (D160 (3)): as run_experiment's; its line replaces --skip-failed's."""
    if rerun_server_failures:
        check_rerun_server_failures(skip_failed, generator)
    check_nogate(configs, max_questions, question_ids_file)
    check_generator(generator, draws)
    _check_generator_configs(configs, generator)
    if generator_url is not None or not is_local(generator):
        generator_servers(configs, generator, generator_url)
    questions, question_filter = run_questions(max_questions, question_ids_file, draws)
    smoke = max_questions is not None
    load_budget_plan(matched_budget_plan, configs, questions)
    _check_models(configs, draws, generator)
    items = work_list(configs, questions, draws, index_name, smoke, sink_root, skip_failed, generator)
    if rerun_server_failures:
        items = rerun_server_failures_in(items, sink_root)
    n_answerable = sum(1 for q in questions if q["answerable"])
    print(f"exp_01 dry run: index {index_name}, {len(questions)} questions ({n_answerable} answerable, "
          f"{len(questions) - n_answerable} not answerable), {len(configs)} configs, draws {list(draws)}")
    if question_filter is not None:
        print(filter_line(question_filter))
    if generator != GEN_MODEL:
        print(f"generator {generator} (--generator, D83 Q173; runs named +{generator_tag(generator)[1:]}); verified "
              f"pass's verifier {VERIFY_MODEL}")
    if is_local(generator):
        print(f"generator server {generator_url or 'not given (--generator-url, required for a run)'}; the verifier "
              f"on --ollama-url (D158 (2))")
    print(f"sinks under {runs_root(sink_root).resolve()}" + (" (smoke test: its own .smoke runs)" if smoke else ""))
    width = 45 if generator == GEN_MODEL else 45 + len(generator_tag(generator))
    print(f"{'run_id':<{width}} {'draw':>4} {'items':>6} {'stored':>7} {'pending':>8}  models")
    for draw in draws:
        for config in configs:
            sel = [i for i in items if i["draw"] == draw and i["config"] == config]
            stored = sum(i["skip"] for i in sel)
            print(f"{config_run_id(config, index_name, smoke, generator):<{width}} {draw:>4} {len(sel):>6} {stored:>7} "
                  f"{len(sel) - stored:>8}  {config_models(config, generator)}")
    keys = [i["key"] for i in items]
    if len(set(keys)) != len(keys):
        raise SystemExit(f"{len(keys) - len(set(keys))} answer keys repeat in the work list")
    print(f"first key {keys[0]}; last key {keys[-1]}")
    if rerun_server_failures:
        print(rerun_line(items))
    elif skip_failed:
        print(f"--skip-failed: {sum(i['failed'] for i in items)} keys whose last line stores an error count as stored "
              f"and are not run again")
    print(f"total: {len(questions)} questions x {len(configs)} configs x {len(draws)} draws = {len(items)} answers, "
          f"{sum(i['skip'] for i in items)} stored, {sum(not i['skip'] for i in items)} pending "
          f"({sum(i['retry'] for i in items)} of them stored with an error, to run again)")


# Concurrency: RLM configs are heavy (many sequential Gemini calls per question),
# so we use lower batch sizes to avoid Gemini rate limits.
# Fast configs (single_pass, multi_hop, verified_pass) can run higher concurrency.
# Since D80 V16 each is the size of a rolling pool (experiments/runner/pool.py), the most answers in flight at once,
# no longer a fixed batch that waits for its slowest answer.
BATCH_SIZE_FAST = 6   # single_pass, multi_hop, verified_pass
BATCH_SIZE_RLM = 2    # rlm_5, rlm_10, rlm_20

RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20", NOGATE_ARM, NOSEARCH_ARM, CTRL_ARM}   # NOGATE_ARM (D238), NOSEARCH_ARM
                                                                                 # (D239), CTRL_ARM (D240) in rlm_10's
                                                                                 # rolling pool of 2


async def run_experiment(
    configs: List[str],
    base_url: str,
    max_questions: Optional[int] = None,
    resume: bool = False,
    index_name: str = DEFAULT_INDEX,
    draws: tuple = ex.draws(FIGURE),
    matched_budget_plan: Optional[Path] = None,
    sink_root: Optional[Path] = None,
    skip_failed: bool = False,
    generator: str = GEN_MODEL,
    generator_url: Optional[str] = None,
    question_ids_file: Optional[Path] = None,
    rerun_server_failures: bool = False,
):
    """Run V4-4 generation comparison (a rolling pool within each config and draw), one run context per answer. A smoke
    test (max_questions given) runs and resumes only its own .smoke runs; sink_root puts every sink under it.
    skip_failed (with resume only): a key whose last line stores an error is skipped as a stored answer is, its error
    line kept as its answer (Q141 restart, D83). generator: --generator (D83 Q173), checked before anything is read;
    its runs are config_run_id's with generator_tag. generator_url (D158 (2)): a local generator's Ollama server, the
    run contexts' servers map (generator_servers); base_url stays the verifier's. question_ids_file (D159 (2)):
    run_questions, read before anything else is; each answer line of the start stores the filter's record.
    rerun_server_failures (D160 (3), --rerun-server-failures; with skip_failed and a local generator only): a key whose
    last line is a failure of our own Ollama server (server_failure) runs again, under a new run context with the same
    draw and so the same seed, its error line kept and the new line appended; every other failed key is kept, as
    skip_failed keeps it."""
    if skip_failed and not resume:
        raise SystemExit("skip_failed (--skip-failed) is a way to resume: pass --resume with it. Nothing was started.")
    if rerun_server_failures:
        check_rerun_server_failures(skip_failed, generator)
    check_nogate(configs, max_questions, question_ids_file)
    check_generator(generator, draws)
    _check_generator_configs(configs, generator)
    servers = generator_servers(configs, generator, generator_url, base_url)
    questions, question_filter = run_questions(max_questions, question_ids_file, draws)
    smoke = max_questions is not None
    root = runs_root(sink_root)

    n_answerable = sum(1 for q in questions if q["answerable"])
    n_unanswerable = len(questions) - n_answerable

    plan = load_budget_plan(matched_budget_plan, configs, questions)
    if plan is not None:
        check_plan_matches(root / config_run_id(MATCHED_BUDGET, index_name, smoke, generator) / ANSWERS, plan["sha256"])
    _check_models(configs, draws, generator)
    items = work_list(configs, questions, draws, index_name, smoke, root, skip_failed, generator)
    if rerun_server_failures:
        items = rerun_server_failures_in(items, root)
    stored = [i for i in items if i["present"] or i["failed"]]
    if stored and not resume:
        runs = sorted({i["run_id"] for i in stored})
        logger.error(f"{len(stored)} of these answers are already stored ({', '.join(runs)}); pass --resume to "
                     f"skip them, or name another index. Nothing was started.")
        sys.exit(1)

    logger.info(f"V4-4: Generation Strategy Comparison (rolling pool)")
    logger.info(f"Questions: {len(questions)} ({n_answerable} answerable, {n_unanswerable} unanswerable)")
    if question_filter is not None:
        logger.info(filter_line(question_filter))
    logger.info(f"Configs: {configs}")
    logger.info(f"Draws: {list(draws)}")
    logger.info(f"Index: {index_name}")
    if generator != GEN_MODEL:
        logger.info(f"Generator: {generator} (--generator, D83 Q173); verifier {VERIFY_MODEL}"
                    + (f"; generator server {generator_url}, verifier server {base_url} (D158 (2))" if servers else ""))
    if rerun_server_failures:
        logger.info("Resume: on, --skip-failed --rerun-server-failures (a key stored with an error is kept, not run "
                    "again, unless its last line is a failure of our own Ollama server: D160 (3))")
    else:
        logger.info("Resume: " + ("on, --skip-failed (a key stored with an error is kept, not run again)" if skip_failed
                                  else "on (a key stored with an error runs again)" if resume else "off"))

    user_id = find_admin_user_id()
    if not check_index_exists(user_id, index_name):
        logger.error("Index check failed. Aborting.")
        sys.exit(1)

    router = ModelRouter()
    retriever, collection_name, embedding_model = setup_retriever(user_id, index_name)
    # F5 (audit of 16 October): each run's sink records the index's content (<sink>/index_identity.jsonl), so the
    # passage ids its answers store resolve to text exactly (experiments/scorers/records.py)
    for rid in sorted({i["run_id"] for i in items if not i["skip"]}):
        index_identity.record(ex.sink(rid, root), index_name, collection_name, script="exp_01_generation.py")

    total = len(items)
    skipped = sum(i["skip"] for i in items)
    logger.info(f"Skipping {skipped} already-stored, {total - skipped} remaining "
                f"({sum(i['retry'] for i in items)} stored with an error, run again"
                + (f"; {sum(i['failed'] and i['skip'] for i in items)} stored with an error, kept: --skip-failed)"
                   if skip_failed else ")"))
    if rerun_server_failures:
        logger.info(rerun_line(items))
        for i in items:
            if i.get("server_failure"):
                logger.info(f"  runs again: {i['key']} ({i['server_failure']}, {i['run_id']})")

    done = skipped

    for draw in draws:
        for config in configs:
            pending = [i for i in items if i["draw"] == draw and i["config"] == config and not i["skip"]]
            if not pending:
                logger.info(f"Config {config}, draw {draw}: all done, skipping")
                continue

            pool_size = BATCH_SIZE_RLM if config in RLM_CONFIGS else BATCH_SIZE_FAST
            logger.info(f"Config {config}, draw {draw}: {len(pending)} questions, rolling pool of {pool_size}")

            # One run context per (question, draw), every one of the config's draw built before any answer starts, so
            # a context the lock or the run's sink refuses stops the run before a call is made
            contexts = {
                i["key"]: ex.context(EXPERIMENT, config, i["q"]["id"], draw, config_models(config, generator),
                                     base_url=base_url, run=i["run_id"], sink=ex.sink(i["run_id"], root),
                                     judge=False, servers=servers)
                for i in pending
            }
            budgets = {i["key"]: ({**plan["questions"][i["q"]["id"]], "plan_sha256": plan["sha256"]}
                                  if config == MATCHED_BUDGET else None) for i in pending}
            started = 0

            async def answer(i, config=config, draw=draw):
                nonlocal started
                started += 1
                q = i["q"]
                logger.info(f"[{done + started}/{total}] {config} d{draw} | {q['id']} "
                            f"({'A' if q['answerable'] else 'U'}): {q['question'][:60]}...")
                return await _process_one(
                    config=config, q=q, ctx=contexts[i["key"]],
                    retriever=retriever, collection_name=collection_name,
                    router=router, user_id=user_id, index_name=index_name,
                    budget=budgets[i["key"]], generator=generator,
                )

            def store(i, result, in_flight, config=config, draw=draw, pool_size=pool_size):
                # Each answer is one line of its run's answers.jsonl, under its own context, stored as it ends. A lock
                # refusal or an RLMStop stores nothing for its key (it stays to do); the pool starts nothing after it,
                # and the run ends once the answers in flight are stored (Q38, Q73, D69).
                if isinstance(result, STOPS):
                    logger.error(f"Stopped on {i['q']['id']} (Q38, Q73): {type(result).__name__}: {result}")
                    return
                if isinstance(result, BaseException):
                    # _process_one returns failed_answer for a strategy error, so this is an error outside it
                    logger.error(f"Task failed for {i['q']['id']}: {result}")
                    result = failed_answer(config, generator, result, None, None)
                    budget = budgets[i["key"]]
                    if budget is not None:
                        result.top_k, result.matched_budget = budget["top_k"], budget   # D51
                with rc.run(contexts[i["key"]]):
                    rc.append(_answer_record(i["key"], config, i["q"], draw, index_name, result,
                                             pool={"size": pool_size, "in_flight_at_start": in_flight},
                                             generator=generator, question_filter=question_filter), ANSWERS)
                logger.info(f"  stored {i['key']} ({in_flight} of {pool_size} in flight at its start)")

            # A rolling pool (D80 V16, B9 O2): the pending answers start in work-list order, at most pool_size at once,
            # each freed slot starting the next, so one slow answer holds one slot only (experiments/runner/pool.py)
            await pool.rolling(pending, pool_size, answer, store, stops=STOPS)
            done += len(pending)

            logger.info(f"Completed config: {config}, draw {draw}")

    # Judging and the report (_generate_report) are a later step, by the lock's judge (A7, D67)
    print(f"\n{'='*70}")
    print("V4-4 GENERATION COMPLETE: answers stored, not judged")
    print(f"{'='*70}")
    for config in configs:
        rid = config_run_id(config, index_name, smoke, generator)
        last = stored_answers(root / rid / ANSWERS)
        n_err = sum(1 for _, error in last.values() if error)
        print(f"{rid}: {len(last) - n_err} answer keys stored, {n_err} with an error, in {root / rid / ANSWERS}")


def _generate_report(
    all_results: List[Dict],
    configs: List[str],
    index_name: str,
    n_answerable: int,
    n_unanswerable: int,
):
    """Generate V4-4 report with pass rate tables. Not called by generation: the report needs judge scores, which
    the judging step adds (A7, D67). Generation stores no citation_metrics, so the Source Cov. column reads 0.00
    (compute_mean_source_coverage) until the analysis step adds them or the column is dropped."""
    judge_key = detect_judge_key(all_results)

    # ── Main comparison table ──
    headers = ["Config", "% Pass", "% Refuse", "Med. Latency", "Source Cov.", "Mean Corr."]
    rows = []

    config_metrics = {}
    for config in configs:
        config_results = [r for r in all_results if r["config"] == config]
        if not config_results:
            continue
        metrics = aggregate_v4_metrics(config_results, judge_key=judge_key)
        config_metrics[config] = metrics

        rows.append([
            config,
            format_pct(metrics["pass_rate"]),
            format_pct(metrics["refusal_rate"]) if metrics["n_unanswerable"] > 0 else "-",
            format_latency(metrics["median_latency"]),
            format_score(metrics["source_coverage"]),
            format_score(metrics["mean_correctness"]),
        ])

    main_table = format_v4_table(
        headers, rows,
        ["l", "r", "r", "r", "r", "r"],
    )

    # ── Per-category breakdown ──
    cat_tables = []
    all_categories = sorted(set(r.get("category", "unknown") for r in all_results))

    for cat in all_categories:
        cat_results = [r for r in all_results if r.get("category") == cat]
        if not cat_results:
            continue

        cat_rows = []
        for config in configs:
            cr = [r for r in cat_results if r["config"] == config]
            if not cr:
                continue
            answerable_cr = [r for r in cr if r.get("answerable", True)]
            if answerable_cr:
                pr = compute_pass_rate(answerable_cr, judge_key=judge_key)
                ms = compute_mean_score(answerable_cr, judge_key=judge_key)
                cat_rows.append([config, format_pct(pr), format_score(ms), str(len(answerable_cr))])

        if cat_rows:
            cat_table = format_v4_table(
                ["Config", "% Pass", "Mean Corr.", "N"],
                cat_rows,
                ["l", "r", "r", "r"],
            )
            cat_tables.append((cat, cat_table))

    # ── Build markdown report ──
    md_lines = [
        "# V4-4: Generation Strategy Comparison (Fixed Scale)",
        "",
        f"**Index**: `{index_name}` | **Model**: `{GEN_MODEL}`",
        f"**Questions**: {n_answerable} answerable + {n_unanswerable} unanswerable = {n_answerable + n_unanswerable} total",
        f"**Pass threshold**: correctness >= 3",
        "",
        "## Main Results",
        "",
        main_table,
        "",
    ]

    if cat_tables:
        md_lines.append("## Per-Category Breakdown")
        md_lines.append("")
        for cat, table in cat_tables:
            md_lines.append(f"### {cat}")
            md_lines.append("")
            md_lines.append(table)
            md_lines.append("")

    md_content = "\n".join(md_lines)

    # ── Save ──
    output = {
        "experiment": "v4_4_generation",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "index_name": index_name,
        "gen_model": GEN_MODEL,
        "judge_model": JUDGE_MODEL,
        "configs": configs,
        "n_answerable": n_answerable,
        "n_unanswerable": n_unanswerable,
        "pass_threshold": 3,
        "config_metrics": config_metrics,
        "per_question_results": all_results,
    }

    json_path, _ = save_v4_results(output, "v4_4_generation")
    md_path = save_v4_markdown(md_content, "v4_4_generation")

    print(f"\n{'='*70}")
    print("V4-4 COMPLETE: Generation Strategy Comparison")
    print(f"{'='*70}")
    print(f"Results: {json_path}")
    print(f"Report:  {md_path}")
    print()
    print(md_content[:3000])


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V4-4: Generation Strategy Comparison"
    )
    parser.add_argument(
        "--index", default=DEFAULT_INDEX,
        help=f"Index name (default: {DEFAULT_INDEX})",
    )
    parser.add_argument(
        "--configs", nargs="+", default=CONFIG_NAMES,
        choices=ALL_CONFIGS + [CUT_ARM, NOGATE_ARM, NOSEARCH_ARM, CTRL_ARM],
        help="Configs to test (default: the 6 of CONFIG_NAMES; matched_budget, D51, single_pass_cut800, D196, "
             "rlm_10_nogate, D238, rlm_10_nosearch, D239, and rlm_10_ctrl, D240, run only when named)",
    )
    parser.add_argument(
        "--matched-budget-plan", type=Path, default=None,
        help="The plan experiments/runner/matched_budget.py wrote (required with the matched_budget config)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=None,
        help="Limit number of questions (smoke testing): its own runs, exp_01__<config>__<index>.smoke, never the "
             "paper run's",
    )
    parser.add_argument(
        "--sink-root", type=Path, default=None,
        help="Write each run's sink under this directory instead of findings/runs (smoke tests)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip the answer keys already stored in each run's answers.jsonl (a key stored with an error runs again)",
    )
    parser.add_argument(
        "--skip-failed", action="store_true",
        help="With --resume (or --dry-run): skip every stored key, a key whose last line stores an error included; "
             "that line stays its answer and is not run again (Q141 restart, D83; D80 V1: Gemini is never retried)",
    )
    parser.add_argument(
        "--rerun-server-failures", action="store_true",
        help="With --resume --skip-failed, a local ollama:: generator only (D160 (3)): a key whose last line is a "
             "failure of our own Ollama server (a stall, an HTTP 5xx, a refused or dropped connection, a stream cut "
             "short, a runner that stopped, a server not reached) runs again with the same seed, its error line kept; "
             "every other failed key is kept (D143 O4)",
    )
    parser.add_argument(
        "--draws", nargs="+", type=int, default=list(ex.draws(FIGURE)),
        choices=list(ex.draws(FIGURE)),
        help=f"Draws to run (default: {' '.join(map(str, ex.draws(FIGURE)))}, D49)",
    )
    parser.add_argument(
        "--ollama-url", default=None,
        help="The Ollama server the verifier runs on (required for a run; e.g. http://127.0.0.1:21441)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the work list (questions x configs x draws) and exit: no model call, no file written",
    )
    parser.add_argument(
        "--generator", default=GEN_MODEL,
        help=f"The model of the role generator in every config (D83 Q173): {GEN_MODEL} (the default, G1) or "
             "anthropic::<model> or gemini::<model> the lock runs (T2); its runs are named +<model> after the index. "
             f"The verified-pass verifier stays {VERIFY_MODEL}; an ollama::<tag> the lock runs (D158 (2)) answers on "
             "--generator-url",
    )
    parser.add_argument(
        "--generator-url", default=None,
        help="A local ollama:: generator's Ollama server (D158 (2), required with one, refused with any other); the "
             "verifier stays on --ollama-url, which may be the same server",
    )
    parser.add_argument(
        "--question-ids-file", type=Path, default=None,
        help="Only the questions this JSON file names (a list, or an object with \"ids\": D98's subset, "
             "findings/recompute/D98_subset/d98_subset.json), in the key's order; a paper run, not a smoke: run ids "
             "and answer keys unchanged, so draws 2 and 3 resume into the runs of draw 1 (D159 (2), as exp_02's and "
             "exp_06's, D112 Q11). Refused with --max-questions",
    )

    args = parser.parse_args()
    draws = tuple(sorted(set(args.draws)))
    # D196: the flat wide call alone may run at 50 core papers, where the 135 questions are all in scope (D48)
    if _index_core_size(args.index) != ex.CORE_SIZE and not (_index_core_size(args.index) == 50
                                                            and list(args.configs) == [MATCHED_BUDGET]):
        parser.error(f"--index {args.index}: the 135 questions are those in scope on {ex.CORE_SIZE} core papers "
                     f"(D48); this index has {_index_core_size(args.index)}")

    if args.skip_failed and not (args.resume or args.dry_run):
        parser.error("--skip-failed is a way to resume: pass --resume with it")
    if args.rerun_server_failures and not args.skip_failed:
        parser.error("--rerun-server-failures narrows --skip-failed: pass --resume --skip-failed with it")
    if args.dry_run:
        # D160 (3): the option is passed only when given, so the call without it is the one it was
        run_dry = functools.partial(dry_run, rerun_server_failures=True) if args.rerun_server_failures else dry_run
        run_dry(args.configs, args.max_questions, args.index, draws, args.matched_budget_plan, args.sink_root,
                args.skip_failed, args.generator, generator_url=args.generator_url,
                question_ids_file=args.question_ids_file)
        return
    if not args.ollama_url:
        parser.error("--ollama-url is required for a run (the run context names the Ollama server)")

    asyncio.run(run_experiment(
        configs=args.configs,
        base_url=args.ollama_url,
        max_questions=args.max_questions,
        resume=args.resume,
        index_name=args.index,
        draws=draws,
        matched_budget_plan=args.matched_budget_plan,
        sink_root=args.sink_root,
        skip_failed=args.skip_failed,
        rerun_server_failures=args.rerun_server_failures,
        generator=args.generator,
        generator_url=args.generator_url,
        question_ids_file=args.question_ids_file,
    ))


if __name__ == "__main__":
    main()
