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
  Questions (Q105, D75): two named sets at every index (experiments/runner/experiment.py scaling_questions()):
    "common", the 135 of answer key v2.4 (D48) at every core size, the primary set; and "per_size", the questions
    of the D5 key in scope at the index's core size (Q55, scripts/key_scope.py in_scope: not answerable at every
    size, answerable where min_core <= the core size), the deposit's comparison: 66, 90, 135, 244 at 5, 10, 20, 50.
    An index asks their union once, in the key's order (135 at 5, 10 and 20 core papers, 244 at 50), and every
    answer records the sets its question belongs to there ("question_sets"); the report counts answers per set.
  6 gen configs: single_pass, multi_hop, rlm_5, rlm_10, rlm_20, verified_pass
  Generator gemini::gemini-3-flash-preview (D27); verified_pass's verifier ollama::gpt-oss:20b (pipeline.py:50,
    kept: Q18, D68). Three draws, seeds 1, 2, 3 (D78 Q116; experiment.DRAWS[3] is (1, 2, 3)); when Figure 3's
    analysis starts on the draws complete everywhere is not fixed in advance (D79).

Runs under the lock (step 3, A9): every (index, config) is one run, findings/runs/<run_id>/ with run_id
exp_02_scaling_factorial__<config>__<index>, and every (question, draw) of it runs in its own run context, so every
model call is recorded there. An answer is keyed by index|config|question_id|d<draw> (experiment.answer_key). The
Ollama server is --base-url, the run context's base_url (the old --ollama-port set OLLAMA_BASE_URL after
backend.config had read it, so it changed nothing: calls.md B7). Answers are stored unjudged (A7): the lock's judge
scores them in a separate step, and the report counts answers, errors and latency only. Before anything runs, every
requested index must be READY in Mentori's database and hold S66's chunk count in the Chroma store (read with sqlite
mode=ro), or the run stops naming each index that is not (check_indexes, F48); --dry-run reads neither (it reads
only the sinks' answers.jsonl, to count what is stored).

Output: answers per (index, config, question, draw); a count and latency report. Each answer's "generation" is the
strategy's whole record (exp1 GenerationResult, D37): passage ids of the generation prompt, every call's tokens and
stop reason read from the run's calls.jsonl, the retrieval records (widths used, query_type, whether reranking ran),
multi-hop's hops, the verified pass's verdicts and fallback (Q17), the RLM's metadata. Every retrieval is also a line
of the run's retrievals.jsonl.

Where the answers are (B9 F5, D80 V16): each answer is one line of its run's <sink>/answers.jsonl, appended and fsynced
as it ends, which is the record (experiments/scorers/records.py reads it as exp_01's) and the only one. Every start
reads the answers.jsonl of each run it targets: a key stored there (with or without an error) is done and never runs
again. Without --resume a start whose work list holds a stored key is refused, naming the runs (a run done before, or
another run's sinks), as exp_01 refuses; with --resume the stored keys are skipped and the rest run. A sink line that
is not an answer record, or a key stored twice, is refused. There is no intermediate file (before the review of 16
October a whole-file rewrite after every answer; a stop between the sink line and that rewrite left a key the next
--resume refused for ever): the report, results_v4/v4_5_scaling[_smoke]__<indexes>_<timestamp>.{json,md} with its
_latest.json, is written once at the end from the sinks, every answer key of the work list once, its row the sink
line without what run_context adds (item_id, arm, run_draw, ctx_uid, seq, pid). Its name is this process's own, by
the indexes it runs (process_tag: their names sorted and joined by '+'; before, every process wrote
v4_5_scaling_latest.json). A process holds a lock per index (results_v4/.v4_5_<index>[.smoke].lock) while it runs, so
a second process on the same index is refused.

Scheduling (D80 V16, B9 O2): within each (index, config, draw) the pending answers run as a rolling pool
(experiments/runner/pool.py) of 6 (single_pass, multi_hop, verified_pass) or 4 (the RLM configs), the old batch sizes:
they start in work-list order, at most that many at once, and an answer that ends frees its slot for the next, so one
slow answer holds one slot instead of its batch. Each answer stores "pool": the pool's size and the answers in flight
when it started, itself included.

A question filter for a paper run (D112 Q11, D98, G7). --question-ids-file runs, on every index, only the questions a
JSON file names (D98's subset, findings/recompute/D98_subset/d98_subset.json: 45 of the 135, all in the common set, so
every index asks all 45). Unlike --question-ids it is not a smoke: run names, answer keys, sinks and the report's name
are the ones without the filter, so draws 2 and 3 of the subset resume into the runs of draw 1 and their answers are
the answers an unfiltered start would store for those keys. read_ids_file says what is refused. The report at the end
is written from every question's stored answers, as without the filter, and holds the filter of the start that wrote
it under "question_filter" (no such key without a filter, so an unfiltered start's report is as before).

Usage:
    # Work list only (no database, no model call, nothing written)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --dry-run

    # Full run
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441

    # Smoke test: its own runs (<index>.smoke); --sink-root keeps its sinks out of findings/runs (a second smoke into
    # the same sinks is refused on the answers the first stored)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441 --indexes exp_v4_s5_n0 --configs single_pass --max-questions 3 \\
        --sink-root findings/recompute/B9_smoke/exp02_sinks

    # Resume after interruption: skips every answer key its runs' answers.jsonl store (the same --sink-root, if any)
    uv run --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441 --resume

    # G4 as one process per index (D80 V16, B9 O3): each process names one index, checks it (F48: READY in Mentori's
    # database, S66's chunk count in the store) before anything else, and stops alone if it fails; its report is its
    # own (v4_5_scaling__<index>_*), and its sinks are its index's runs. A second
    # process on the same index is refused. Every process sends its own pool of answers to Gemini (6 or 4 at once)
    # and to the verifier on --base-url, so n processes send up to n times the pool; start as many as the machine has
    # room for (B9: three), then the next as one ends.
    for idx in exp_v4_s5_n0 exp_v4_s5_n1 exp_v4_s5_n3; do
        nohup uv run --project experiments/mentori --frozen python \\
            experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
            --base-url http://127.0.0.1:21441 --indexes "$idx" > "g4_$idx.log" 2>&1 &
    done
    # resume one of them: the same command with --resume

    # One draw, or two (--draws; D78 Q116: draw 1 on every index first, then draws 2 and 3, the 50-core indexes
    # first). The start runs those draws only; the report at its end covers every draw its sinks store. The G4
    # launcher, findings/recompute/G4_runs/launch_g4.sh, starts each index with --draws 1, then --draws 2, then
    # --draws 3, each draw complete on every index before the next starts.
    uv run --project experiments/mentori --frozen python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441 --indexes exp_v4_s50_n3 --draws 1

    # A smoke on named questions (--question-ids, as exp_03's): a smoke like --max-questions (its own runs,
    # <index>.smoke, and report), on the index's questions these ids name, in the key's order. An id the index does not
    # ask is refused. G4's smoke takes its ids from a written rule (findings/recompute/G4_runs/check_g4.py smoke-ids).
    uv run --project experiments/mentori --frozen python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441 --indexes exp_v4_s50_n3 --draws 1 --sink-root findings/recompute/G4_runs/smoke_sinks \\
        --question-ids 01_sarek_CO2 OOD_001 21_livestock_gut_microbiome_review_CO2

    # D98's subset only, draws 2 and 3, into the paper runs of draw 1 (G7, D112 Q11)
    uv run --project experiments/mentori --frozen python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py \\
        --base-url http://127.0.0.1:21441 --indexes exp_v4_s50_n3 --draws 2 3 --resume \\
        --question-ids-file findings/recompute/D98_subset/d98_subset.json
"""

import argparse
import asyncio
import copy
import fcntl
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.model_router import ModelRouter

from exp_common import (
    GEN_MODEL,
    find_admin_user_id,
    setup_retriever,
    save_v4_results, save_v4_markdown,
    compute_median_latency,
    format_v4_table, format_latency,
    V4_RESULTS_DIR,
)
from tests.experiments.exp1_rlm_vs_singlepass import (
    _single_pass_rag, _multi_hop_rag, _run_rlm, _verified_pass_rag,
    GenerationResult, _AnswerCalls, failed_answer, REFUSALS, STOPS,
)
# exp_common imports backend.agents.lock_adapter, which puts the reanalysis repository on sys.path
from experiments.runner import experiment as ex
from experiments.runner import index_identity
from experiments.runner import pool
from experiments.runner import run_context as rc

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("exp_02_scaling_factorial")
logger.setLevel(logging.INFO)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

EXPERIMENT = "exp_02_scaling_factorial"   # the first part of every run_id of this script
FIGURE = 3
DRAWS = ex.draws(FIGURE)                    # (1, 2, 3): three draws for Figure 3 (D78 Q116, D79)
VERIFIER_MODEL = "ollama::gpt-oss:20b"      # verified_pass's verifier, PipelineConfig.verify_model (Q18, D68)
ANSWERS = "answers.jsonl"                    # <sink>/answers.jsonl: every stored answer, the record (B9 F5)
RUNS_ROOT = ex.RUNS                         # findings/runs/: each run's sink is RUNS_ROOT/<run_id> (--sink-root: another)
# what run_context.append adds to a stored line besides run_id, which the row carries itself (_row): the report's row
# is the line without these (stored_rows)
SINK_ADDED = tuple(k for k in rc.ADDED if k != "run_id")

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


def config_models(config: str) -> Dict[str, str]:
    """The models one config's run calls, as the run context's agent_roles (each allowed as a generator, D66).
    Only verified_pass calls a second model, the verifier."""
    models = {"generator": GEN_MODEL}
    if config == "verified_pass":
        models["verifier"] = VERIFIER_MODEL
    return models


def run_name(config: str, index_name: str, smoke: bool = False) -> str:
    """The run_id of one (config, index): exp_02_scaling_factorial__<config>__<index>. A smoke test (--max-questions)
    is its own run, <index>.smoke, so its answers never sit in a paper run under the paper's answer keys."""
    return ex.run_id(EXPERIMENT, config, f"{index_name}.smoke" if smoke else index_name)


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
# Since D80 V16 each is the size of a rolling pool (experiments/runner/pool.py), the most answers in flight at once,
# no longer a fixed batch that waits for its slowest answer.
BATCH_SIZE_FAST = 6   # single_pass, multi_hop, verified_pass
BATCH_SIZE_RLM = 4    # rlm_5, rlm_10, rlm_20 (bumped from 2; embedding leak fixed)
RLM_CONFIGS = {"rlm_5", "rlm_10", "rlm_20"}


def _row(index_name: str, config: str, q: Dict, draw: int, gen_result: GenerationResult, run_id: str,
         pool: Optional[Dict] = None) -> Dict:
    """One stored answer, unjudged (A7): the lock's judge scores it in a separate step. No citation coverage either:
    the v2.4 key's questions carry no source_files, so the scoring step computes it from the stored answer.
    question_sets: the named sets (Q105) the question belongs to on this index, as index_questions() gave them. pool:
    the rolling pool's size and the answers in flight when this one started, itself included (D80 V16)."""
    return {
        "answer_key": ex.answer_key(config, q["id"], draw, index=index_name),
        "run_id": run_id,
        "index_name": index_name,
        "question_id": q["id"],
        "question": q["question"],
        "category": q["category"],
        "answerable": q["answerable"],
        "question_sets": q.get("question_sets"),
        "config": config,
        "draw": draw,
        "gen_model": GEN_MODEL,
        "generation": asdict(gen_result),
        "pool": pool,
    }


async def _process_one(
    config: str,
    q: Dict,
    draw: int,
    ctx: rc.RunContext,
    retriever,
    collection_name: str,
    router: ModelRouter,
    user_id: str,
    index_name: str,
) -> Dict:
    """Generate one (index, config, question, draw) answer inside its run context ctx. A strategy that raises gives
    failed_answer: the error, unknown counts None and the calls made before it (A5, D37). A lock refusal (REFUSALS)
    is not caught: run_experiment starts no other answer, saves the ones in flight and ends the run, the key not
    completed (Q38)."""
    t0 = time.time()
    with rc.run(ctx):
        log = _AnswerCalls()
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
        except STOPS:
            raise   # a lock refusal (Q38) or an RLMStop (Q73, D75): nothing stored for the key
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            gen_result = failed_answer(config, GEN_MODEL, e, log, time.time() - t0)

    return _row(index_name, config, q, draw, gen_result, ctx.run_id)


# ─────────────────────────────────────────────────────────────
# Main experiment loop
# ─────────────────────────────────────────────────────────────

def _index_core_size(index_name: str) -> int:
    """Core paper count from an index name like 'exp_v4_s20_n0'. A name without _s<digits>_ is refused: it decides
    which questions are asked, and the harness's default of 50 would ask every one (scripts/key_scope.py reads the
    size the same strict way)."""
    m = re.search(r"_s(\d+)_", index_name)
    if not m:
        raise ValueError(f"index {index_name!r} names no core size (_s<digits>_)")
    return int(m.group(1))


def index_sets(index_name: str) -> Dict[str, List[Dict]]:
    """G4's two named question sets on one index (Q105, D75): experiment.scaling_questions() at its core size."""
    return ex.scaling_questions(_index_core_size(index_name))


def index_questions(index_name: str, max_questions: Optional[int] = None,
                    question_ids: Optional[List[str]] = None, keep_ids: Optional[List[str]] = None) -> List[Dict]:
    """The questions asked on one index (Q105, D75): the union of its two named sets (index_sets), each question once,
    in the key's order, each carrying question_sets, the names (ex.SCALING_SETS order) of the sets it belongs to. The
    script's old filters (category out_of_domain or min_core <= core size, on ground_truth_v4.json, A9; then the 135
    in scope at the core size, Q55) are gone."""
    sets = index_sets(index_name)
    member = {name: {q["id"] for q in sets[name]} for name in ex.SCALING_SETS}
    union = set().union(*member.values())
    out = []
    for q in ex._key():                     # the D5 key in the v2.4 key's order, which both sets keep
        if q["id"] in union:
            q = copy.deepcopy(q)                # _key() is cached: never hand it out
            q["question_sets"] = [name for name in ex.SCALING_SETS if q["id"] in member[name]]
            out.append(q)
    if question_ids:                        # a smoke on named questions: the index's own, in the key's order
        unknown = sorted(set(question_ids) - {q["id"] for q in out})
        if unknown:
            raise SystemExit(f"--question-ids {unknown}: not asked on {index_name} (Q105: the union of its two "
                             f"named sets); nothing run")
        out = [q for q in out if q["id"] in set(question_ids)]
    if keep_ids is not None:                # a paper run's filter (--question-ids-file, D98): the index's own, in order
        unknown = sorted(set(keep_ids) - {q["id"] for q in out})
        if unknown:
            raise SystemExit(f"--question-ids-file: {unknown[:5]} not asked on {index_name} (Q105: the union of its "
                             f"two named sets); nothing run")
        out = [q for q in out if q["id"] in set(keep_ids)]
    return out[:max_questions] if max_questions else out


def read_ids_file(path, known: Optional[List[str]] = None) -> tuple:
    """D112 Q11 (D98, G7): (the question ids a --question-ids-file names, in the file's order; the filter's record).
    The file holds a JSON list of ids, or an object whose "ids" is one (findings/recompute/D98_subset/d98_subset.json,
    written by scripts/S464_d98_subset.py). Each id must be one of the 135 questions of answer key v2.4 (known; D48),
    named once. Refused before anything is read or written: a file that is not such a JSON, an unknown or repeated id.
    index_questions then refuses an id an index does not ask."""
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


def is_smoke(max_questions: Optional[int], question_ids: Optional[List[str]]) -> bool:
    """A smoke test (--max-questions or --question-ids): its own runs (<index>.smoke) and report, never the paper's."""
    return max_questions is not None or bool(question_ids)


# ─────────────────────────────────────────────────────────────
# Index identity (F48, audit of 16 Oct): every requested index present, with the submitted build's chunk count
# ─────────────────────────────────────────────────────────────

# S66's index_inventory: each Figure 3 index's chunk count in the deposit's build (scripts/S66_corpus_grid.py, from
# the deposit's create_indexes_*.json); I1 (plan.csv) and A13 (COUNTERCHECKS.md) found the Studio store equal to it
INVENTORY = ex.ROOT / "findings" / "recompute" / "S66_corpus_grid.json"


def expected_chunks() -> Dict[str, int]:
    """Each index's expected chunk count, S66's index_inventory: the 12 indexes, 196 (exp_v4_s5_n0) to 10,526
    (exp_v4_s50_n3)."""
    inventory = json.loads(INVENTORY.read_text())["index_inventory"]
    return {name: int(row["chunks"]) for name, row in inventory.items()}


def chroma_counts(chroma_dir) -> Dict[str, int]:
    """The rows of every Chroma collection, read from <chroma_dir>/chroma.sqlite3 opened read-only (sqlite mode=ro):
    the embeddings of each collection's METADATA segment, the count A13 matched to S66 on the Studio store. Not
    chromadb.PersistentClient, which opens the store for writing, and whose VectorStore.get_collection creates a
    collection it does not find (backend/retrieval/vector_store.py), so a missing index would be served empty."""
    path = Path(chroma_dir) / "chroma.sqlite3"
    if not path.is_file():
        raise SystemExit(f"Index check (F48): no Chroma store at {path}, nothing run")
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT c.name, count(e.id) FROM collections c "
            "JOIN segments s ON s.collection = c.id AND s.scope = 'METADATA' "
            "LEFT JOIN embeddings e ON e.segment_id = s.id GROUP BY c.name").fetchall()
    finally:
        con.close()
    return dict(rows)


def mentori_collections(user_id: str, indexes: List[str]) -> Dict[str, tuple]:
    """Each index's Chroma collection as setup_retriever() would serve it (the first user_collections row of the
    user with that name), or None with the reason: no row, a status other than READY, or no collection name."""
    from backend.retrieval.models import UserCollection, IndexStatus
    from backend.database import engine
    from sqlmodel import Session, select

    out = {}
    with Session(engine) as session:
        for idx_name in indexes:
            idx = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id)
                .where(UserCollection.name == idx_name)
            ).first()
            if not idx:
                out[idx_name] = (None, f"not in Mentori's database for user {user_id}")
            elif idx.status != IndexStatus.READY:
                out[idx_name] = (None, f"status {idx.status}, not READY")
            elif not idx.vector_db_collection_name:
                out[idx_name] = (None, "no Chroma collection named in Mentori's database")
            else:
                out[idx_name] = (idx.vector_db_collection_name, "")
    return out


def index_problems(indexes: List[str], collections: Dict[str, tuple], counts: Dict[str, int],
                   expected: Dict[str, int]) -> List[str]:
    """One line per requested index that stops the run (F48), naming it: not in S66's inventory (no expected count),
    no usable row in Mentori's database (collections[idx] = (None, reason)), its Chroma collection absent from the
    store, or a chunk count other than S66's. Empty when every index is present with its submitted count."""
    problems = []
    for idx_name in indexes:
        if idx_name not in expected:
            problems.append(f"{idx_name}: not in S66's index inventory, so no expected chunk count")
            continue
        collection, why = collections.get(idx_name, (None, "not looked up in Mentori's database"))
        if collection is None:
            problems.append(f"{idx_name}: {why}")
        elif collection not in counts:
            problems.append(f"{idx_name}: its Chroma collection {collection} is not in the store")
        elif counts[collection] != expected[idx_name]:
            problems.append(f"{idx_name}: {counts[collection]} chunks in {collection}, "
                            f"{expected[idx_name]} expected (S66)")
    return problems


def check_indexes(user_id: str, indexes: List[str], chroma_dir=None) -> None:
    """Refuse to start (SystemExit) unless every requested index exists, is READY and holds S66's chunk count; each
    missing or mismatched index is logged and named. F48: the old loop skipped a missing index, ran the rest and
    exited 0. chroma_dir: Mentori's store (settings.CHROMA_PERSIST_DIRECTORY) unless given."""
    if chroma_dir is None:
        from backend.config import settings
        chroma_dir = settings.CHROMA_PERSIST_DIRECTORY
    problems = index_problems(indexes, mentori_collections(user_id, indexes), chroma_counts(chroma_dir),
                              expected_chunks())
    for p in problems:
        logger.error(f"Index check (F48): {p}")
    if problems:
        raise SystemExit(f"Index check (F48): {len(problems)} of {len(indexes)} requested indexes missing or not "
                         f"as built, nothing run: " + "; ".join(problems))
    logger.info(f"Index check (F48): all {len(indexes)} requested indexes present with S66's chunk counts")


# ─────────────────────────────────────────────────────────────
# One process's files (B9 F5, D80 V16): named by the indexes it runs
# ─────────────────────────────────────────────────────────────

def process_tag(indexes: List[str]) -> str:
    """The indexes a process runs as one file-name part: their names, sorted, each once, joined by '+'
    (exp_v4_s50_n3; exp_v4_s5_n0+exp_v4_s5_n1). The same indexes give the same tag, so a resume finds its files."""
    names = sorted(set(indexes))
    bad = [n for n in names if not re.fullmatch(r"[A-Za-z0-9_.-]+", n)]
    if not names or bad:
        raise SystemExit(f"indexes {indexes!r}: each a plain name ([A-Za-z0-9_.-]), at least one")
    return "+".join(names)


def report_prefix(indexes: List[str], smoke: bool = False) -> str:
    """The prefix of this process's report files, v4_5_scaling[_smoke]__<tag>: save_v4_results writes
    <prefix>_<timestamp>.json and <prefix>_latest.json, save_v4_markdown <prefix>_<timestamp>.md, all in results_v4/.
    Before B9 F5 every process wrote v4_5_scaling[_smoke]_latest.json, the last to end replacing the others'."""
    return f"v4_5_scaling{'_smoke' if smoke else ''}__{process_tag(indexes)}"


def hold_indexes(indexes: List[str], smoke: bool = False) -> List:
    """One exclusive lock per index (fcntl.flock on results_v4/.v4_5_<index>[.smoke].lock, which names the holder's
    pid), held until the returned files are closed or the process ends. A second process on an index another holds is
    refused before it writes anything: two processes on one index would write one run's sink and answer keys."""
    V4_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    held = []
    for idx in sorted(set(indexes)):
        f = open(V4_RESULTS_DIR / f".v4_5_{idx}{'.smoke' if smoke else ''}.lock", "a+", encoding="utf-8")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.seek(0)
            who = f.read().strip() or "a process"
            f.close()
            for h in held:
                h.close()
            raise SystemExit(f"{idx}: {who} runs it already ({V4_RESULTS_DIR / f.name}); one process per index, "
                             f"nothing run") from None
        f.seek(0)
        f.truncate()
        f.write(f"pid {os.getpid()}, started {datetime.now().isoformat(timespec='seconds')}\n")
        f.flush()
        held.append(f)
    return held


def stored_rows(path: Path) -> Dict[str, Dict]:
    """Each answer key a sink's answers.jsonl stores -> its row as the report holds it (the line without SINK_ADDED,
    what run_context.append adds), in line order; empty when there is no file. A stored answer with an error counts:
    exp_02 stores one answer per key, its error included (the report counts them). A line that is not an answer
    record, one without question_sets (made before Q105, so the report could not count it per set), or a key stored a
    second time (two answers under one key) is refused, never skipped or merged."""
    rows: Dict[str, Dict] = {}
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
                key = rec["answer_key"]
            except (ValueError, KeyError, TypeError) as e:
                raise SystemExit(f"{path}:{n} is not an answer record ({e!r}); nothing run")
            if not rec.get("question_sets"):
                raise SystemExit(f"{path}:{n} stores {key} without question_sets (made before Q105); nothing run")
            if key in rows:
                raise SystemExit(f"{path}:{n} stores {key} a second time; one key has one answer, nothing run")
            rows[key] = {k: v for k, v in rec.items() if k not in SINK_ADDED}
    return rows


def work_list(indexes: List[str], configs: List[str], max_questions: Optional[int],
              root: Path, question_ids: Optional[List[str]] = None,
              keep_ids: Optional[List[str]] = None) -> List[Dict]:
    """One entry per (index, config, draw), in run order, with its run_id, its questions (index_questions; keep_ids, a
    paper run's --question-ids-file, narrows them and leaves run_id and keys as they are), the rows
    its run's answers.jsonl under root already stores for them ("stored", answer key -> row, in the sink's line order)
    and the questions with no stored answer ("pending"). The sinks are the record (B9 F5): a stored key is done.
    Reads each answers.jsonl once; writes nothing. A name given twice in indexes or configs counts once (review of
    16 Oct: a repeated name would run and store every key twice)."""
    indexes, configs = list(dict.fromkeys(indexes)), list(dict.fromkeys(configs))
    smoke = is_smoke(max_questions, question_ids)
    sinks: Dict[str, Dict[str, Dict]] = {}
    work = []
    for idx_name in indexes:
        qs = index_questions(idx_name, max_questions, question_ids, keep_ids)
        for config in configs:
            rid = run_name(config, idx_name, smoke=smoke)
            if rid not in sinks:
                sinks[rid] = stored_rows(Path(root) / rid / ANSWERS)
            for draw in DRAWS:
                keys = {ex.answer_key(config, q["id"], draw, index=idx_name): q for q in qs}
                work.append({"index_name": idx_name, "config": config, "draw": draw, "run_id": rid,
                             "questions": qs,
                             "stored": {k: r for k, r in sinks[rid].items() if k in keys},
                             "pending": [q for k, q in keys.items() if k not in sinks[rid]]})
    return work


def _work_list(indexes: List[str], configs: List[str], max_questions: Optional[int], root: Path,
               question_ids: Optional[List[str]] = None, keep_ids: Optional[List[str]] = None) -> List[Dict]:
    """work_list, given question_ids only when a smoke names them and keep_ids only when --question-ids-file names
    them: without them the call is work_list's four arguments, as before --question-ids."""
    extra = {**({"question_ids": question_ids} if question_ids else {}),
             **({"keep_ids": keep_ids} if keep_ids is not None else {})}
    return work_list(indexes, configs, max_questions, root, **extra)


def report_rows(work: List[Dict]) -> List[Dict]:
    """The report's rows: every stored row of the work list, entry by entry in run order, each in its sink's line
    order (the order the answers ended in), so every answer key once."""
    return [r for w in work for r in w["stored"].values()]


def select_draws(draws=None) -> tuple:
    """The draws a start runs: Figure 3's (DRAWS, D78 Q116), or the ones of them --draws names, in DRAWS order. A draw
    that is not one of Figure 3's is refused. G4 runs draw 1 on every index first, then draws 2 and 3 (D78 Q116), so its
    launcher starts each index's process with --draws 1, then --draws 2, then --draws 3 (findings/recompute/G4_runs)."""
    if not draws:
        return DRAWS
    unknown = sorted(set(draws) - set(DRAWS))
    if unknown:
        raise SystemExit(f"--draws {unknown}: Figure {FIGURE}'s draws are {DRAWS} (D78 Q116), nothing run")
    return tuple(d for d in DRAWS if d in set(draws))


def only_draws(work: List[Dict], draws: tuple) -> List[Dict]:
    """The work list's entries of these draws only, in run order. The sinks are read whole either way (work_list), so a
    start of draws 2 and 3 into sinks that hold draw 1 lists draw 1's keys nowhere: they are neither run nor refused."""
    return [w for w in work if w["draw"] in draws]


def print_work_list(work: List[Dict], draws: tuple = DRAWS) -> None:
    """The dry run: what a run would generate. No database, no model call, nothing written; the sinks' answers.jsonl
    are read for what they store."""
    print(f"{EXPERIMENT}: dry run (no database read, no model call, nothing written)")
    print(f"draws {DRAWS} (D78 Q116, Figure {FIGURE}); generator {GEN_MODEL}; verified_pass verifier {VERIFIER_MODEL}")
    if tuple(draws) != tuple(DRAWS):
        print(f"this start runs draws {tuple(draws)} only (--draws); the other draws are not listed")
    by_core = {}
    for w in work:
        qs = w["questions"]
        by_core.setdefault(_index_core_size(w["index_name"]), (len(qs), *(
            sum(1 for q in qs if name in q["question_sets"]) for name in ex.SCALING_SETS)))
    print("questions per core size, asked (" + ", ".join(ex.SCALING_SETS) + "; Q105): "
          + ", ".join(f"{c}: {n[0]} (" + ", ".join(map(str, n[1:])) + ")" for c, n in sorted(by_core.items())))
    print(f"{'run_id':<58} {'draw':>4} {'asked':>5} {'stored':>6} {'pending':>7}  first pending answer key")
    for w in work:
        first = (ex.answer_key(w["config"], w["pending"][0]["id"], w["draw"], index=w["index_name"])
                 if w["pending"] else "-")
        print(f"{w['run_id']:<58} {w['draw']:>4} {len(w['questions']):>5} {len(w['stored']):>6} "
              f"{len(w['pending']):>7}  {first}")
    print(f"total: {sum(len(w['stored']) for w in work)} answers stored, {sum(len(w['pending']) for w in work)} "
          f"pending in {len(work)} (run, draw) pairs")


async def run_experiment(
    indexes: List[str],
    configs: List[str],
    base_url: Optional[str],
    max_questions: Optional[int] = None,
    resume: bool = False,
    dry_run: bool = False,
    sink_root: Optional[Path] = None,
    draws: Optional[List[int]] = None,
    question_ids: Optional[List[str]] = None,
    question_ids_file: Optional[Path] = None,
):
    """Run V4-5 scaling experiment (a rolling pool within each index, config and draw). The sinks of its runs under
    sink_root (RUNS_ROOT, findings/runs, when None) are the record, each answer one line of <sink>/answers.jsonl, and
    what a start skips: every key they store (resume, or refused without it). The report, named by the indexes
    (report_prefix, B9 F5), is written from them at the end, over every draw the sinks store. draws: the draws this
    start runs (select_draws; all of Figure 3's when None). question_ids: a smoke on these questions (index_questions).
    question_ids_file: a paper run on the questions the file names only (read_ids_file; D112 Q11, D98), same runs and
    keys."""
    smoke = is_smoke(max_questions, question_ids)
    root = Path(sink_root) if sink_root is not None else RUNS_ROOT
    draws = select_draws(draws)
    keep_ids, question_filter = None, None
    if question_ids_file is not None:
        if smoke:
            raise SystemExit("--question-ids-file with --question-ids or --max-questions: name the questions one way; "
                             "nothing run")
        keep_ids, question_filter = read_ids_file(question_ids_file)
        question_filter["draws"] = list(draws)
        line = (f"question filter (--question-ids-file {question_filter['file']}, sha256 "
                f"{question_filter['file_sha256'][:12]}): {len(keep_ids)} questions named; runs and keys unchanged")
        logger.info(line)
        if dry_run:
            print(line)
    if dry_run:
        print_work_list(only_draws(_work_list(indexes, configs, max_questions, root, question_ids, keep_ids), draws),
                        draws)
        return

    logger.info(f"V4-5: Factorial Scaling (rolling pool)")
    logger.info(f"Indexes: {indexes}")
    logger.info(f"Configs: {configs}")
    logger.info(f"Draws: {draws} of {DRAWS}; Ollama server: {base_url}")

    user_id = find_admin_user_id()

    # Verify indexes (F48): every requested one present with S66's chunk count, or nothing runs (a missing index was
    # skipped here and the run exited 0)
    check_indexes(user_id, indexes)

    # One process per index (B9 F5, D80 V16): another process on one of these indexes stops this one here
    held = hold_indexes(indexes, smoke)
    try:
        await _run_held(indexes, configs, base_url, max_questions, resume, root, user_id, smoke, draws, question_ids,
                        keep_ids, question_filter)
    finally:
        for f in held:
            f.close()


async def _run_held(indexes, configs, base_url, max_questions, resume, root, user_id, smoke, draws=DRAWS,
                    question_ids=None, keep_ids=None, question_filter=None):
    """run_experiment once the indexes are checked and held. Runs the work list's entries of draws only (only_draws),
    of the questions keep_ids names when given; the report at the end covers every draw and every question the sinks
    store (the filter narrows what runs, never the report)."""
    logger.info(f"Files of this process: {V4_RESULTS_DIR / report_prefix(indexes, smoke)}_*, sinks under {root}")
    router = ModelRouter()

    # The sinks are the record (B9 F5, review of 16 October): every key a target sink stores is done, its row read
    # from the sink, and never runs or is stored again. Without --resume a stored key means a run done before (or
    # another run's sinks), so the start is refused, naming the runs, before anything is written (as exp_01)
    work = only_draws(_work_list(indexes, configs, max_questions, root, question_ids, keep_ids), draws)
    stored: Dict[str, List[str]] = {}
    for w in work:
        if w["stored"]:
            stored.setdefault(w["run_id"], []).extend(w["stored"])
    n_stored = sum(map(len, stored.values()))
    if stored and not resume:
        raise SystemExit(f"{n_stored} answers of this work list are already stored in their run's {ANSWERS} ("
                         + "; ".join(f"{r}: {len(k)}, first {k[0]}" for r, k in stored.items())
                         + f"); nothing run. Pass --resume to skip them and run the rest, or name another --sink-root")
    if stored:
        logger.info(f"Resume: {n_stored} answers stored in the sinks are done; "
                    f"{sum(len(w['pending']) for w in work)} to run")
    n_saved = 0

    retrievers = {}
    identified = set()                       # the runs whose index identity this start has recorded (F5)
    for w in work:
        idx_name, config, draw = w["index_name"], w["config"], w["draw"]
        questions, pending = w["questions"], w["pending"]
        if idx_name not in retrievers:
            n_answerable = sum(1 for q in questions if q["answerable"])
            logger.info(f"\n{'='*60}")
            logger.info(f"INDEX: {idx_name}")
            logger.info(f"{'='*60}")
            logger.info(f"Questions: {len(questions)} ({n_answerable} answerable, "
                        f"{len(questions) - n_answerable} not answerable)")
            retrievers[idx_name] = setup_retriever(user_id, idx_name)
        retriever, collection_name, _ = retrievers[idx_name]

        if not pending:
            logger.info(f"Config {config}, draw {draw}: all done, skipping")
            continue
        sink = ex.sink(w["run_id"], root)
        if w["run_id"] not in identified:
            # F5 (audit of 16 October): the run's sink records the index's content (<sink>/index_identity.jsonl), so
            # the passage ids its answers store resolve to text exactly (experiments/scorers/records.py)
            index_identity.record(sink, idx_name, collection_name, script="exp_02_scaling_factorial.py")
            identified.add(w["run_id"])

        models = config_models(config)
        pool_size = BATCH_SIZE_RLM if config in RLM_CONFIGS else BATCH_SIZE_FAST
        total_for_config = len(questions)
        done_for_config = total_for_config - len(pending)
        logger.info(f"Config {config}, draw {draw}: {len(pending)} pending, rolling pool of {pool_size}")

        # one run context per (question, draw), all of them built before any answer starts, so a context the lock or
        # the run's sink refuses stops the run here instead of becoming an answer's error
        contexts = {
            q["id"]: ex.context(EXPERIMENT, config, q["id"], draw, models, base_url=base_url, run=w["run_id"],
                                sink=sink, judge=False)
            for q in pending
        }

        async def answer(q, config=config, draw=draw, idx_name=idx_name, retriever=retriever,
                         collection_name=collection_name):
            nonlocal done_for_config
            done_for_config += 1
            logger.info(
                f"  [{done_for_config}/{total_for_config}] {idx_name} | {config} | {q['id']} | d{draw} "
                f"({'A' if q['answerable'] else 'U'}): "
                f"{q['question'][:50]}..."
            )
            return await _process_one(
                config=config, q=q, draw=draw, ctx=contexts[q["id"]],
                retriever=retriever, collection_name=collection_name,
                router=router, user_id=user_id, index_name=idx_name,
            )

        def store(q, result, in_flight, config=config, draw=draw, idx_name=idx_name, run_id=w["run_id"],
                  pool_size=pool_size):
            # As each answer ends: one line of its run's answers.jsonl, the record and the only file written per
            # answer, so a process stopped at any point leaves every ended answer stored once and the next --resume
            # skips it. A lock refusal or an RLMStop saves nothing for its key, so it stays to do; the pool starts
            # nothing after it, and the run ends once the answers in flight are saved (Q38, D69)
            nonlocal n_saved
            if isinstance(result, STOPS):
                logger.error(f"Setup error for {q['id']} (Q38): {result}")
                return
            if isinstance(result, BaseException):
                # _process_one returns failed_answer for a strategy error, so this is an error outside it
                logger.error(f"Task failed for {q['id']}: {result}")
                result = _row(idx_name, config, q, draw, failed_answer(config, GEN_MODEL, result, None, None), run_id)
            result["pool"] = {"size": pool_size, "in_flight_at_start": in_flight}
            with rc.run(contexts[q["id"]]):
                rc.append(result, ANSWERS)
            n_saved += 1
            logger.info(f"  saved {result['answer_key']} ({in_flight} of {pool_size} in flight at its start; "
                        f"{n_saved} this start, {n_stored} before)")

        # A rolling pool (D80 V16, B9 O2): the pending questions start in work-list order, at most pool_size at once,
        # each freed slot starting the next, so one slow answer holds one slot only (experiments/runner/pool.py)
        await pool.rolling(pending, pool_size, answer, store, stops=STOPS)

        logger.info(f"Completed {idx_name} / {config} / draw {draw}")

    # ── Report ── written once, from the sinks (the record): every key of the work list once, whether stored by this
    # start or an earlier one
    _generate_report(report_rows(_work_list(indexes, configs, max_questions, root, question_ids)), indexes, configs,
                     smoke=smoke, question_filter=question_filter)


def _generate_report(
    all_results: List[Dict],
    indexes: List[str],
    configs: List[str],
    smoke: bool = False,
    prefix: Optional[str] = None,
    question_filter: Optional[Dict] = None,
):
    """Answer count and latency tables, saved under prefix (default report_prefix(indexes, smoke):
    v4_5_scaling[_smoke]__<the indexes>, so neither a smoke test nor a process on other indexes replaces this one's
    _latest.json, B9 F5). No pass rate or correctness: the answers are unjudged here (A7), and a pass
    rate over no scores would read as 0%. No Gemini block counts either: Gemini calls go through experiments/runner
    now, so GeminiClient's counters stay at 0; each call's status is in its run's calls.jsonl."""
    n_questions = len({r["question_id"] for r in all_results})
    # Q105 (D75): the two named sets of every index, and the answers stored in each
    question_sets = {idx: {name: [q["id"] for q in qs] for name, qs in index_sets(idx).items()} for idx in indexes}
    set_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    set_rows = []

    # ── Answer count table: answers stored (of which with an error) ──
    count_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    count_rows = []

    latency_headers = ["Config"] + [idx.replace("exp_", "") for idx in indexes]
    latency_rows = []

    for config in configs:
        count_row = [config]
        lat_row = [config]

        for idx_name in indexes:
            idx_results = [
                r for r in all_results
                if r["config"] == config and r["index_name"] == idx_name
            ]
            if not idx_results:
                count_row.append("-")
                lat_row.append("-")
                continue

            n_err = sum(1 for r in idx_results if r["generation"].get("error"))
            count_row.append(f"{len(idx_results)} ({n_err})")

            ml = compute_median_latency(idx_results)
            lat_row.append(format_latency(ml))

        count_rows.append(count_row)
        latency_rows.append(lat_row)
        set_rows.append([config] + [
            " / ".join(str(sum(1 for r in all_results if r["config"] == config and r["index_name"] == idx
                               and name in (r.get("question_sets") or ()))) for name in ex.SCALING_SETS)
            for idx in indexes])

    count_table = format_v4_table(
        count_headers, count_rows,
        ["l"] + ["r"] * len(indexes),
    )

    latency_table = format_v4_table(
        latency_headers, latency_rows,
        ["l"] + ["r"] * len(indexes),
    )

    set_table = format_v4_table(
        set_headers, set_rows,
        ["l"] + ["r"] * len(indexes),
    )

    # ── Markdown ──
    md_lines = [
        "# V4-5: Factorial Scaling",
        "",
        f"**Model**: `{GEN_MODEL}` | **Questions**: {n_questions} (answerable + not answerable) | "
        f"**Draws**: {list(DRAWS)}",
        "Answers are unjudged; the lock's judge scores them in a separate step (A7).",
        "",
        "## Answers stored (with an error)",
        "",
        count_table,
        "",
        f"## Answers per question set ({' / '.join(ex.SCALING_SETS)}; Q105: common primary)",
        "",
        set_table,
        "",
        "## Median Latency (seconds)",
        "",
        latency_table,
        "",
    ]

    md_content = "\n".join(md_lines)

    # ── Save ──
    output = {
        "experiment": "v4_5_scaling",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "indexes": indexes,
        "configs": configs,
        "draws": list(DRAWS),
        "gen_model": GEN_MODEL,
        "n_questions": n_questions,
        "question_sets": question_sets,
        "per_question_results": all_results,
    }
    if question_filter is not None:          # D112 Q11: the filter of the start that wrote this report (the rows: all)
        output["question_filter"] = question_filter

    prefix = prefix or report_prefix(indexes, smoke)
    json_path, _ = save_v4_results(output, prefix)
    md_path = save_v4_markdown(md_content, prefix)

    print(f"\n{'='*70}")
    print("V4-5 COMPLETE: Factorial Scaling")
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
        help="Limit questions (smoke testing): its own runs (<index>.smoke) and report "
             "(v4_5_scaling_smoke__<indexes>), never the paper run's",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip every answer key its runs' answers.jsonl already store and run the rest (without it, a start "
             "whose answers are already stored is refused)",
    )
    parser.add_argument(
        "--sink-root", type=Path, default=None,
        help="Write each run's sink under this directory instead of findings/runs (smoke tests, as exp_01's)",
    )
    parser.add_argument(
        "--base-url", type=str, default=None,
        help="The Ollama server every run context names (its base_url), e.g. http://127.0.0.1:21441. Required "
             "except with --dry-run. Replaces --ollama-port, which never changed where calls went (calls.md B7)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the work list (runs, draws, questions, pending answer keys) and stop: no database, no model call",
    )
    parser.add_argument(
        "--draws", nargs="+", type=int, default=None, choices=list(DRAWS),
        help=f"Draws to run (default: all of Figure {FIGURE}'s, {' '.join(map(str, DRAWS))}; D78 Q116). G4 starts "
             f"--draws 1 on every index first, then --draws 2, then --draws 3",
    )
    parser.add_argument(
        "--question-ids", nargs="+", default=None,
        help="Smoke test on these questions (as --max-questions: its own runs <index>.smoke and report): the index's "
             "questions they name, in the key's order; an id the index does not ask is refused",
    )
    parser.add_argument(
        "--question-ids-file", type=Path, default=None,
        help="A paper run on the questions this JSON file names only (a list, or an object with \"ids\"; D112 Q11, "
             "D98's subset): same runs, keys and report name as without it, so draws 2 and 3 resume into draw 1's runs",
    )

    args = parser.parse_args()
    if not args.dry_run and not (args.base_url or "").startswith(("http://", "https://")):
        parser.error("--base-url http(s)://host:port is required (the Ollama server of the run contexts)")

    asyncio.run(run_experiment(
        indexes=args.indexes,
        configs=args.configs,
        base_url=args.base_url,
        max_questions=args.max_questions,
        resume=args.resume,
        dry_run=args.dry_run,
        sink_root=args.sink_root,
        draws=args.draws,
        question_ids=args.question_ids,
        **({"question_ids_file": args.question_ids_file} if args.question_ids_file is not None else {}),
    ))

if __name__ == "__main__":
    main()
