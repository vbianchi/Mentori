"""G19 (D249 O2, D239 amended revived): the gemma3:27b ablation's checks. README.md beside this file.

Arms (all on ollama::gemma3:27b under experiments/LOCK.toml, draw 1 = seed 1, turn cap 10, index exp_v4_s20_n0, the
46 questions of g19_questions.json):
  A  the package RLM (rlms 0.1.3 as G6, experiments/rlm_ref, adapter.LockedOllama), run b4_rlm_ref_gemma3__cap10__d239a46,
     keys cap10|<q>|d1
  B  exp_01 rlm_10_nosearch (RLMOrchestrator(search_tools=False)), run exp_01__rlm_10_nosearch__exp_v4_s20_n0+gemma3-27b
  C  exp_01 rlm_10_nogate (RLMOrchestrator(quality_gate=False)), run exp_01__rlm_10_nogate__exp_v4_s20_n0+gemma3-27b
  R  stored, not run: T2's gemma3:27b rlm_10 draw 1 on D98's 29 and T2X's on the 17 (manifest below).

    uv run --frozen python findings/recompute/G19_runs/g19_check.py questions [--write]
    uv run --frozen python findings/recompute/G19_runs/g19_check.py match
    uv run --frozen python findings/recompute/G19_runs/g19_check.py seeds <calls.jsonl> [<calls.jsonl> ...]
    uv run --frozen python findings/recompute/G19_runs/g19_check.py smoke <arm> --root <smoke sinks> --server <URL> [--commit C] [--write F]
    uv run --frozen python findings/recompute/G19_runs/g19_check.py verify <arm> --root <sinks> [--server <URL>]
    uv run --frozen python findings/recompute/G19_runs/g19_check.py progress --root <sinks>
    uv run --frozen python findings/recompute/G19_runs/g19_check.py stored <arm> --root <sinks>   (exit 0 when a key is stored)
    uv run --frozen python findings/recompute/G19_runs/g19_check.py stores --stores <dir> --g1-sinks <dir> --t2x-store <dir> --arms B C
    uv run --frozen python findings/recompute/G19_runs/g19_check.py manifest --t2-run <sink> --t2x-run <sink> --t2-collect <f> --t2x-collect <f> [--write]
    uv run --frozen python findings/recompute/G19_runs/g19_check.py estimate [--t2-run <sink> --write] [--t2x-records <f>]

questions  The rule (D239 amended): D98's 45 (findings/recompute/D98_subset/d98_subset.json, sha256 pinned) kept where
           S511.questions() calls the question answerable and one-paper (20), plus every answerable many-paper question
           of Figure 3a's 86 (S511 kind "many", 26), in answer key v2.4's order. Refused unless 20 + 26 = 46, the many-
           paper half is D98's 9 plus T2X's 17 (T2X_runs/t2x_questions.json, sha256 pinned), and the 46 are G15's 29
           (D98's answerable questions in the five categories) plus T2X's 17. --write writes g19_questions.json; without
           it the file must equal the rule's output byte for byte. exp_01 and run_rlm_ref read its "ids" (and "name").
match      exp_01's rlm_10 (R's config) against rlm_10_nosearch (B) and rlm_10_nogate (C) for ollama::gemma3:27b at draw
           1, offline (stand-ins, no model or index): the arguments to _run_rlm and RLMOrchestrator, the pool, models,
           run identity and the lock's call. Passes when each arm differs only in its names and its one switch.
seeds      R's call records (T2's and T2X's calls.jsonl on the Studio): every gemma3:27b call of the 46 at draw 1 sent
           the options, fields and digest the lock gives now (Lock.ollama, seed 1), so the new arms send what R sent.
smoke      One arm's smoke verdict: B and C exp_01 --max-questions 1 (its .smoke run), A run_rlm_ref --smoke --limit 1;
           one answer with no error, every call gemma3:27b at the lock (options, fields, digest, Ollama, lock sha256),
           on --server, no other model.
verify     After a run: every key of the 46 at draw 1 has a line and no other key does; B and C: the arm's config and run,
           the question filter's sha256, the switch recorded in every answer (B search_tools SEARCH_OFF_RECORD with
           consistent attempts and no search retrieval, gate on; C quality_gate GATE_OFF_RECORD, rejections 0, search
           on); A: the package records (one answer per key, every call an Ollama gemma3:27b call at the lock, a retry at
           its retry seed, every [record] field on a call that was sent, the request verified). Every call at --server
           when given. Prints
           COUNTS by stop reason. No score is read.
manifest   The stored arm R the reader uses: for each of the 46, the source (T2 for D98's 29, T2X for the 17), its run
           and answer key exp_v4_s20_n0|rlm_10|<q>|d1, the sha256 of its last answer line, whether its judged row (key
           v2.5, devstral) is in the named collect file (counted, never scored), and each file's sha256. Refused when a
           key is missing from its sink, a line is not gemma3:27b rlm_10 at draw 1, or a collect lacks a row.
estimate   Hours per arm on one, two and three ports, from R's own answer lines (T2's gemma3 rlm_10, draws 1 to 3, the
           20 one-paper and 9 many-paper questions of the 46; T2X's README method: server s = the sum of an answer's
           calls' wall_s, other s = latency minus every call's wait and wall). --t2x-records adds T2X's measured wall
           time of its gemma3 run, rlm_10 plus single_pass on one port (t2x_records.jsonl on the Studio).
Exit codes: 0 passed; 1 refused or a check failed; 2 usage.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import statistics
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MENTORI = ROOT / "experiments" / "mentori"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DECISION = "D249 O2"
NAME = "d239a46"                                      # run_rlm_ref's run id part (A)
QUESTIONS = HERE / "g19_questions.json"
ESTIMATE = HERE / "g19_estimate.json"
MANIFEST = HERE / "g19_stored_R.json"
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"
D98_SHA256 = "957c79b6b0f3afb12b70be51d0802e7853b4d4ff12e2bdb519d44a10111046bc"   # S464, as T2X and S512
T2X_QUESTIONS = ROOT / "findings" / "recompute" / "T2X_runs" / "t2x_questions.json"
T2X_SHA256 = "1943af5bc2ef4fca5c116b00050580fe7031c9d0c35d23546144d4422c18822c"   # T2X README (D241)
LOCK_WANT = "8730d401a5d7b6baa1780e656f844261eaead60e45b5199afa29d57f989ad495"   # D212's lock, as G12 to G17 and T2X
OLLAMA_VERSION = "0.40.2"
INDEX = "exp_v4_s20_n0"
MODEL = "gemma3:27b"
GEN_MODEL = f"ollama::{MODEL}"
TAG = "+gemma3-27b"
DRAW, CAP = 1, 10
CAP_A = CAP                                           # check_rlm_ref_ollama sets 2 for its cap-2 sink
ONE_PAPER = ("factual_recall", "conceptual", "technical")
MANY_PAPER = ("cross_document", "synthesis")
CATEGORIES = ONE_PAPER + MANY_PAPER                   # run_rlm_ref.CATEGORIES (the test holds them equal)
COUNTS = {"n": 46, "one_paper": 20, "many_paper": 26, "many_in_d98": 9, "many_t2x": 17}
REF_CONFIG = "rlm_10"                                 # R: T2's and T2X's gemma3 rlm_10
CONFIG = {"B": "rlm_10_nosearch", "C": "rlm_10_nogate"}
ARMS = ("A", "B", "C")
ARM_LABEL = {"A": "package RLM", "B": "search off", "C": "gate off", "R": "Mentori RLM-10 (stored)"}
SWITCH = {"B": "search_tools", "C": "quality_gate"}
NAME_FIELDS = {"run_id", "arm", "config_name"}
A_EXPERIMENT = "b4_rlm_ref_gemma3"
# rlm/orchestrator.py's records (the test holds these equal to the module's)
GATE_OFF_RECORD = {"on": False, "decision": "D238", "min_llm_calls": 3, "max_early_rejections": 3}
SEARCH_FUNCTIONS = ["search_keyword", "search_regex", "search_semantic"]
NAVIGATION_FUNCTIONS = ["list_documents", "get_document_structure", "get_chunk", "get_chunks_range",
                        "get_chunks_by_page"]
SEARCH_OFF_RECORD = {"on": False, "decision": "D239", "removed": SEARCH_FUNCTIONS, "kept": NAVIGATION_FUNCTIONS}
MIN_LLM_CALLS = 3
POOL = {"A": 1, "B": 2, "C": 2, "R": 2}               # run_rlm_ref one question at a time; exp_01 BATCH_SIZE_RLM 2


class Refused(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p) -> str:
    return sha256_bytes(Path(p).read_bytes())


def read_jsonl(path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def run_id(arm: str, smoke: bool = False) -> str:
    if arm == "A":
        return f"{A_EXPERIMENT}__cap{CAP_A}__{'smoke' if smoke else NAME}"
    cfg = REF_CONFIG if arm == "R" else CONFIG[arm]
    return f"exp_01__{cfg}__{INDEX}{TAG}" + (".smoke" if smoke else "")


def answer_key(arm: str, q: str, draw: int = DRAW) -> str:
    if arm == "A":
        return f"cap{CAP_A}|{q}|d{draw}"
    cfg = REF_CONFIG if arm == "R" else CONFIG[arm]
    return f"{INDEX}|{cfg}|{q}|d{draw}"


# ----------------------------------------------------------------------------------------------------- the questions

def _s511():
    spec = importlib.util.spec_from_file_location("S511_g19", ROOT / "scripts" / "S511_g2_matched_budget.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def compute_questions(qs: dict | None = None, order: list | None = None, d98: Path = D98_SUBSET,
                      t2x: Path = T2X_QUESTIONS, categories: dict | None = None) -> dict:
    """The 46 (module docstring). qs: S511.questions(); order: the key's ids in order; categories: {id: category}
    (the tests pass made-up ones)."""
    raw = Path(d98).read_bytes()
    if sha256_bytes(raw) != D98_SHA256:
        raise Refused(f"{Path(d98).name} sha256 {sha256_bytes(raw)[:12]} is not D98's {D98_SHA256[:12]}")
    sub = set(json.loads(raw)["ids"])
    if len(sub) != 45:
        raise Refused(f"D98's subset holds {len(sub)} questions, not 45")
    traw = Path(t2x).read_bytes()
    if sha256_bytes(traw) != T2X_SHA256:
        raise Refused(f"{Path(t2x).name} sha256 {sha256_bytes(traw)[:12]} is not T2X's {T2X_SHA256[:12]}")
    t2x_ids = json.loads(traw)["ids"]
    if qs is None or order is None or categories is None:
        from experiments.runner import experiment as ex
        if qs is None:
            qs = _s511().questions()
        key = ex.questions()
        order = order if order is not None else [q["id"] for q in key]
        categories = categories if categories is not None else {
            q["id"]: (q.get("category") if q["answerable"] else None) for q in key}
    one = [q for q in order if q in sub and qs[q]["kind"] == "one"]
    many = [q for q in order if qs[q]["kind"] == "many"]
    many_in = [q for q in many if q in sub]
    many_out = [q for q in many if q not in sub]
    got = {"n": len(one) + len(many), "one_paper": len(one), "many_paper": len(many), "many_in_d98": len(many_in),
           "many_t2x": len(many_out)}
    if got != COUNTS:
        raise Refused(f"the rule gives {got}, D239 amended names {COUNTS}")
    if many_out != [q for q in order if q in set(t2x_ids)] or len(t2x_ids) != 17:
        raise Refused("the many-paper questions outside D98's subset are not T2X's 17")
    g15 = [q for q in order if q in sub and categories.get(q) in CATEGORIES]   # G15's (D239's) 29, R's T2 half
    if set(g15) != set(one) | set(many_in) or len(g15) != 29:
        raise Refused(f"D98's answerable questions in the five categories ({len(g15)}) are not the 20 + 9")
    ids = [q for q in order if q in set(one) | set(many)]
    from experiments.runner import experiment as ex
    return {"decision": DECISION, "name": NAME,
            "rule": ("D239 amended: D98's 45-question subset (findings/recompute/D98_subset/d98_subset.json) kept where "
                     "S511.questions() calls the question answerable and one-paper (20), plus every answerable many-"
                     "paper question of Figure 3a's 86 (S511 kind many: D98's 9 and T2X's 17), in answer key v2.4's "
                     "order"),
            "counts": got, "d98_subset_sha256": D98_SHA256, "t2x_questions_sha256": T2X_SHA256,
            "key_d5": str(Path(ex.KEY_D5).relative_to(ROOT)), "key_d5_sha256": ex.KEY_D5_SHA256,
            "stored_R": {"t2_d98": one + many_in, "t2x": many_out},
            "one_paper": one, "many_paper": many, "ids": ids}


def questions_text(d: dict) -> str:
    return json.dumps(d, indent=1) + "\n"


def check_questions(path: Path = QUESTIONS, **kw) -> dict:
    want = questions_text(compute_questions(**kw))
    if not Path(path).exists():
        raise Refused(f"no {Path(path).name}: g19_check.py questions --write")
    if Path(path).read_text(encoding="utf-8") != want:
        raise Refused(f"{Path(path).name} differs from the rule's output (g19_check.py questions --write rewrites it)")
    return json.loads(want)


def read_ids(path: Path = QUESTIONS) -> dict:
    """{ids, one_paper, many_paper, t2_d98, t2x} of a questions file, read without the rule, shape-checked."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    ids, one, many = d.get("ids") or [], d.get("one_paper") or [], d.get("many_paper") or []
    if (len(ids), len(one), len(many)) != (46, 20, 26) or len(set(ids)) != 46 or set(one) | set(many) != set(ids):
        raise Refused(f"{Path(path).name}: {len(ids)} ids ({len(one)} one-paper, {len(many)} many-paper), not 46 = 20 + 26")
    sr = d.get("stored_R") or {}
    return {"ids": ids, "one_paper": one, "many_paper": many, "t2_d98": sr.get("t2_d98") or [],
            "t2x": sr.get("t2x") or [], "sha256": sha256_file(path)}


# --------------------------------------------------------------------------------------------------------- the lock

def lock_call(retry: int | None = None):
    from experiments.runner.lock import load
    return load().ollama(MODEL, role="generator", draw=DRAW, retry=retry)


def lock_now():
    from experiments.runner.lock import load
    return load()


def not_sent(c: dict) -> bool:
    """A call record of arm A for which no request reached the server: nothing sent (options_sent None) and either the
    prompt was not sendable (b4.not_sent) or the server could not be read first (adapter._ollama_unreached, error
    'before the request was posted'). Such a record has no server timings and no busy_servers_on_machine, so the
    LOCK [record] fields are not asked of it."""
    return c.get("options_sent") is None and (
        (c.get("b4") or {}).get("not_sent") is True
        or str(c.get("error") or "").startswith("before the request was posted"))


def retried_refs(calls: list) -> set:
    """(ctx_uid, seq) of every call a later record retried: its transient_retry names the failed call (Mentori's step
    loop, step_executor.py, and adapter.LockedOllama both write failed_seq and failed_ctx_uid)."""
    out = set()
    for c in calls:
        t = c.get("transient_retry") or {}
        if t.get("failed_seq") is not None:
            out.add((t.get("failed_ctx_uid") or c.get("ctx_uid"), t["failed_seq"]))
    return out


def call_problems(c: dict, server: str | None, want_lock: str = LOCK_WANT) -> list:
    """What is wrong with one Ollama call record of a G19 answer (A, B, C, or R's reference)."""
    if c.get("provider") != "ollama" or c.get("model") != MODEL:
        return [f"provider {c.get('provider')!r} model {c.get('model')!r}, not ollama {MODEL}"]
    bad = []
    if c.get("role") != "generator":
        bad.append(f"role {c.get('role')!r}")
    if c.get("options_sent") is None:                      # A: nothing sent (an unreached server, a prompt not sendable)
        return bad + ([] if c.get("status") == "error" else [f"nothing sent but status {c.get('status')!r}"])
    r = c.get("retry")
    call = lock_call(r if r else None)
    if c.get("options_sent") != call.options:
        bad.append(f"options_sent {c.get('options_sent')!r}, not the lock's {call.options!r} (retry {r})")
    if c.get("fields_sent") != call.fields:
        bad.append(f"fields_sent {c.get('fields_sent')!r}, not the lock's {call.fields!r}")
    if c.get("model_digest") != call.digest:
        bad.append(f"digest {str(c.get('model_digest'))[:12]}, not the lock's {call.digest[:12]}")
    if c.get("ollama_version") != OLLAMA_VERSION:
        bad.append(f"Ollama {c.get('ollama_version')!r}")
    if c.get("lock_sha256") != want_lock:
        bad.append(f"lock {str(c.get('lock_sha256'))[:12]}, not {want_lock[:12]}")
    if c.get("draw") != DRAW:
        bad.append(f"draw {c.get('draw')!r}")
    if r and ((c.get("transient_retry") or {}).get("attempt") != r or c.get("seed_sent") != call.options["seed"]):
        bad.append(f"retry {r} without its transient_retry or seed_sent")
    if server is not None and str(c.get("server") or "").rstrip("/") != server.rstrip("/"):
        bad.append(f"server {c.get('server')!r}, not {server}")
    if not c.get("request_sha256"):
        bad.append("no request_sha256")
    return bad


# ------------------------------------------------------------------------------------------------------------ match

def capture(config: str, question: str = "Q?") -> dict:
    """What one answer of this exp_01 config would run, every model, index and store call replaced by a stand-in
    (G16's and G17's capture, for gemma3:27b)."""
    for p in (str(MENTORI), str(MENTORI / "publication" / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import exp_01_generation as e1
    import tests.experiments.exp1_rlm_vs_singlepass as x1
    seen = {}
    real_run_rlm = e1._run_rlm

    async def run_rlm(question, router, gen_model, user_id, **kw):
        seen["run_rlm"] = {"question": question, "gen_model": gen_model, "user_id": user_id, **kw}
        return await real_run_rlm(question, router, gen_model, user_id, **kw)

    class Ctx:
        citations, passages_seen = [], []

    class Orch:
        def __init__(self, **kw):
            seen["orchestrator"] = {k: v for k, v in kw.items() if k != "model_router"}

        async def run(self, task, context):
            seen["task"] = task
            return x1.RLMResult("stand-in answer") if hasattr(x1, "RLMResult") else "stand-in answer"

    async def from_index(index_name, user_id, **kw):
        seen["index"] = {"index_name": index_name, "user_id": user_id, **kw}
        return Ctx()

    class Calls:
        pass

    saved = (e1._run_rlm, x1.RLMOrchestrator, x1.RLMContext.__dict__["from_index"], x1._AnswerCalls, x1._with_calls)
    e1._run_rlm, x1.RLMOrchestrator, x1._AnswerCalls = run_rlm, Orch, Calls
    x1._with_calls = lambda gen, log: gen
    x1.RLMContext.from_index = staticmethod(from_index)
    try:
        asyncio.run(e1._run_config(config, question, None, "collection", None, GEN_MODEL, "user", INDEX))
    finally:
        e1._run_rlm, x1.RLMOrchestrator, x1._AnswerCalls, x1._with_calls = saved[0], saved[1], saved[3], saved[4]
        x1.RLMContext.from_index = saved[2]
    seen["pool"] = e1.BATCH_SIZE_RLM if config in e1.RLM_CONFIGS else e1.BATCH_SIZE_FAST
    seen["models"] = e1.config_models(config, GEN_MODEL)
    seen["run_id"] = e1.config_run_id(config, INDEX, generator=GEN_MODEL)
    return seen


def identity(config: str, run: str, sink_root: Path) -> dict:
    import exp_01_generation as e1
    from experiments.runner import experiment as ex
    ctx = ex.context(e1.EXPERIMENT, config, "01_sarek_CO2", DRAW, e1.config_models(config, GEN_MODEL),
                     base_url="http://127.0.0.1:1", run=run, sink=sink_root / run, judge=False,
                     servers={MODEL: "http://127.0.0.1:2"})
    return {k: getattr(ctx, k) for k in ("run_id", "arm", "allowed", "agent_roles", "thinking", "tools", "draw")}


def flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def match() -> dict:
    caps = {c: capture(c) for c in (REF_CONFIG, CONFIG["B"], CONFIG["C"])}
    with tempfile.TemporaryDirectory() as t:
        for c, v in caps.items():
            v["identity"] = identity(c, v["run_id"], Path(t))
    call = lock_call()
    for v in caps.values():
        v["lock"] = {"options": call.options, "fields": call.fields, "digest": call.digest}
    fl = {c: flat(v) for c, v in caps.items()}
    out = {}
    for arm in ("B", "C"):
        a, b = fl[REF_CONFIG], fl[CONFIG[arm]]
        allowed = NAME_FIELDS | {SWITCH[arm]}
        diffs = [(k, a.get(k, "<absent>"), b.get(k, "<absent>")) for k in sorted(set(a) | set(b))
                 if a.get(k, "<absent>") != b.get(k, "<absent>")]
        bad = [d for d in diffs if d[0].split(".")[-1] not in allowed]
        if b.get(f"orchestrator.{SWITCH[arm]}") is not False or b.get(f"run_rlm.{SWITCH[arm]}") is not False:
            bad.append((f"{SWITCH[arm]} not passed False", a.get(f"orchestrator.{SWITCH[arm]}"),
                        b.get(f"orchestrator.{SWITCH[arm]}")))
        for other in ("quality_gate", "search_tools"):
            if other != SWITCH[arm] and b.get(f"orchestrator.{other}") is not True:
                bad.append((f"orchestrator.{other} not True", True, b.get(f"orchestrator.{other}")))
        out[arm] = (diffs, bad)
    same = sorted(k for k in fl[REF_CONFIG] if all(fl[CONFIG[a]].get(k, "<absent>") == fl[REF_CONFIG][k]
                                                    for a in ("B", "C")))
    return {"arms": out, "same": same, "flat": fl}


def cmd_match() -> int:
    m = match()
    fails = 0
    for arm, (diffs, bad) in m["arms"].items():
        for k, x, y in diffs:
            print(f"{'FAIL' if (k, x, y) in bad else 'diff'} {arm} {k}: {REF_CONFIG} {x!r} | {CONFIG[arm]} {y!r}")
        for d in bad:
            if d not in diffs:
                print(f"FAIL {arm} {d[0]}: {REF_CONFIG} {d[1]!r} | {CONFIG[arm]} {d[2]!r}")
        fails += bool(bad)
    if fails:
        return 1
    print(f"match passed: {len(m['same'])} fields equal in rlm_10, rlm_10_nosearch and rlm_10_nogate for {GEN_MODEL}; "
          f"B differs only in its names and search_tools False, C only in its names and quality_gate False")
    return 0


# ------------------------------------------------------------------------------------------------------------ seeds

def cmd_seeds(qpath: Path, calls_files: list) -> int:
    ids = set(read_ids(qpath)["ids"])
    call = lock_call()
    seen, bad, n_retried = Counter(), [], 0
    for f in calls_files:
        for r in read_jsonl(f):
            q = r.get("item_id")
            if q not in ids or r.get("run_draw") != DRAW or r.get("model") != MODEL:
                continue
            seen[q] += 1
            # a call retried after a transient failure sent the lock's retry seed (LOCK retry_seed: seed + 1,000,000
            # * r), as call_problems: the lock's call at that retry, and its transient_retry names the same attempt
            rt = r.get("retry")
            try:
                want = lock_call(rt) if rt else call
            except Exception as e:                       # a retry number the lock refuses (not 1 to 3)
                bad.append((q, r.get("seq"), f"retry {rt!r}: {e}", call))
                continue
            sent = (r.get("options_sent"), {k: v for k, v in (r.get("fields_sent") or {}).items() if k in want.fields},
                    r.get("model_digest"))
            if sent != (want.options, want.fields, want.digest):
                bad.append((q, r.get("seq"), sent, want))
            elif rt and (r.get("transient_retry") or {}).get("attempt") != rt:
                bad.append((q, r.get("seq"), f"retry {rt} with transient_retry {r.get('transient_retry')!r}", want))
            n_retried += bool(rt)
    missing = sorted(q for q in ids if not seen[q])
    for b in bad[:20]:
        print(f"FAIL seeds: reference call {b[1]} of {b[0]} sent {b[2]}, the lock gives "
              f"{(b[3].options, b[3].fields, b[3].digest[:12])} now")
    for q in missing[:20]:
        print(f"FAIL seeds: no reference gemma3:27b call of {q} at draw 1 in {', '.join(map(str, calls_files))}")
    if bad or missing:
        return 1
    print(f"seeds passed: {sum(seen.values())} reference gemma3:27b calls of the {len(ids)} questions at draw 1, each "
          f"sent {call.options} (a retry r its retry seed, {n_retried} retried) and digest {call.digest[:12]}, as G19's "
          f"calls will")
    return 0


# ------------------------------------------------------------------------------------------------- smoke and verify

def _answer_error(arm: str, a: dict):
    return (a.get("error") or (a.get("status") != "ok" and a.get("stop_reason"))) if arm == "A" \
        else (a.get("generation") or {}).get("error")


def _stop(arm: str, a: dict):
    return a.get("stop_reason") if arm == "A" else (a.get("generation") or {}).get("stop_reason")


def smoke_verdict(arm: str, root: Path, server: str, want_lock: str = LOCK_WANT) -> tuple:
    if arm not in ARMS:
        return False, [f"arm {arm!r} is not one of {ARMS}"], {}
    sink = Path(root) / run_id(arm, smoke=True)
    answers, calls = read_jsonl(sink / "answers.jsonl"), read_jsonl(sink / "calls.jsonl")
    problems, facts = [], {"arm": arm, "sink": str(sink)}
    if len(answers) != 1:
        problems.append(f"{len(answers)} answer lines, not 1")
    for a in answers:
        if _answer_error(arm, a):
            problems.append(f"stored with an error: {str(_answer_error(arm, a))[:200]}")
        if arm == "A":
            if a.get("generator") != GEN_MODEL or a.get("model") != MODEL:
                problems.append(f"generator {a.get('generator')!r} model {a.get('model')!r}")
        else:
            if a.get("gen_model") != GEN_MODEL or a.get("config") != CONFIG[arm]:
                problems.append(f"gen_model {a.get('gen_model')!r} config {a.get('config')!r}")
            md = ((a.get("generation") or {}).get("rlm") or {}).get("metadata") or {}
            problems += [f"switch: {p}" for p in switch_problems(arm, md)]
        facts.update(stop_reason=_stop(arm, a))
    if not calls:
        problems.append("no call records")
    retried = retried_refs(calls)
    for c in calls:
        bad = call_problems(c, server, want_lock)
        # a failed call that was retried is not a smoke failure: A marks it b4.retried; for B and C (exp_01, no b4)
        # a later record's transient_retry names it (Mentori's step loop)
        if c.get("status") not in ("ok", "length") and not (c.get("b4") or {}).get("retried") \
                and (c.get("ctx_uid"), c.get("seq")) not in retried:
            bad.append(f"status {c.get('status')!r}: {str(c.get('error'))[:160]}")
        if bad:
            problems.append(f"call seq {c.get('seq')}: " + "; ".join(bad))
    facts.update(calls=len(calls), call_wall_s=round(sum(c.get("wall_s") or 0 for c in calls), 1),
                 statuses=dict(Counter(str(c.get("status")) for c in calls)))
    return not problems, problems, facts


def switch_problems(arm: str, md: dict) -> list:
    """The arm's switch as every answer of it must record it (rlm.metadata)."""
    out = []
    qg, st = md.get("quality_gate"), md.get("search_tools")
    if arm == "C":
        if qg != GATE_OFF_RECORD:
            out.append(f"quality_gate {qg!r}, not {GATE_OFF_RECORD}")
        if md.get("rejections") != 0 or md.get("stop_reason") == "final_after_max_rejections":
            out.append(f"rejections {md.get('rejections')}, stop reason {md.get('stop_reason')}")
    elif qg is not None:
        out.append(f"quality_gate {qg!r}: the gate is on in {arm}")
    if arm == "B":
        if not isinstance(st, dict) or {k: st.get(k) for k in SEARCH_OFF_RECORD} != SEARCH_OFF_RECORD:
            out.append(f"search_tools {st!r}, not {SEARCH_OFF_RECORD} with attempts")
        elif not isinstance(st.get("attempts"), list) or st.get("n_attempts") != len(st["attempts"]):
            out.append(f"search_tools attempts {st.get('attempts')!r}, n_attempts {st.get('n_attempts')}")
        searched = [x.get("fn") for x in (md.get("retrievals") or []) if x.get("fn") in SEARCH_FUNCTIONS]
        if searched:
            out.append(f"{len(searched)} search retrievals in the record ({sorted(set(searched))})")
    elif st is not None:
        out.append(f"search_tools {st!r}: search is off in {arm}")
    return out


def last_lines(sink: Path) -> tuple:
    last, n = {}, Counter()
    for a in read_jsonl(Path(sink) / "answers.jsonl"):
        last[a.get("answer_key")] = a
        n[a.get("answer_key")] += 1
    return last, n


def verify(arm: str, root: Path | None, server: str | None, qpath: Path = QUESTIONS, want_lock: str = LOCK_WANT,
           sink: Path | None = None) -> tuple:
    """(problems, counts) of one arm's sink: <root>/<the arm's run id>, or sink when given."""
    if arm not in ARMS:
        return [f"arm {arm!r} is not one of {ARMS}"], {}
    q = read_ids(qpath)
    rid = run_id(arm)
    sink = Path(sink) if sink is not None else Path(root) / rid
    last, n_lines = last_lines(sink)
    want = {answer_key(arm, i) for i in q["ids"]}
    problems = []
    missing, extra = sorted(want - set(last)), sorted(set(last) - want)
    if missing:
        problems.append(f"{rid}: {len(missing)} of {len(want)} keys have no line (first {missing[0]})")
    if extra:
        problems.append(f"{rid}: {len(extra)} keys outside G19's (first {extra[0]})")
    if arm == "A":
        problems += [f"{rid}: answer {k} stored {c} times (one attempt per answer, Q29)" for k, c in n_lines.items() if c > 1]
    for k in sorted(want & set(last)):
        a = last[k]
        if arm == "A":
            if a.get("generator") != GEN_MODEL or a.get("model") != MODEL or a.get("lock_sha256") != want_lock \
                    or a.get("draw") != DRAW or a.get("cap") != CAP_A:
                problems.append(f"{k}: generator {a.get('generator')!r}, model {a.get('model')!r}, lock "
                                f"{str(a.get('lock_sha256'))[:8]}, draw {a.get('draw')}, cap {a.get('cap')}")
            if server is not None and str(a.get("server") or "").rstrip("/") != server.rstrip("/"):
                problems.append(f"{k}: server {a.get('server')!r}, not {server}")
            continue
        g = a.get("generation") or {}
        if a.get("run_id") != rid or a.get("gen_model") != GEN_MODEL or a.get("draw") != DRAW \
                or a.get("config") != CONFIG[arm] or g.get("config") != CONFIG[arm]:
            problems.append(f"{k}: run_id {a.get('run_id')!r}, gen_model {a.get('gen_model')!r}, draw {a.get('draw')!r}, "
                            f"config {a.get('config')!r}")
        f = a.get("question_filter") or {}
        if f.get("file_sha256") != q["sha256"]:
            problems.append(f"{k}: question filter {str(f.get('file_sha256'))[:12]}, not g19_questions.json "
                            f"{q['sha256'][:12]}")
        md = (g.get("rlm") or {}).get("metadata") or {}
        if md:
            problems += [f"{k}: {p}" for p in switch_problems(arm, md)]
        elif not g.get("error"):
            problems.append(f"{k}: an answer with no RLM record")
    calls = read_jsonl(sink / "calls.jsonl")
    fields = lock_now().d["record"]["fields"]
    by_uid = {}
    for c in calls:
        by_uid.setdefault(c.get("ctx_uid"), set()).add(c.get("seq"))
        bad = call_problems(c, server, want_lock)
        if arm == "A":
            if c.get("options_sent") is not None and c.get("messages_sent_verified") is not True:
                bad.append("messages_sent not verified against the posted request")
            miss = [x for x in fields if x not in c]
            if miss and not not_sent(c):
                bad.append(f"no {miss}")
        elif c.get("run_id") not in (None, rid):
            bad.append(f"run {c.get('run_id')!r}")
        if bad:
            problems.append(f"{rid} call seq {c.get('seq')}: " + "; ".join(bad))
    if arm == "A":
        for k, a in last.items():
            if not set((a.get("calls") or {}).get("seqs") or []) <= by_uid.get(a.get("ctx_uid"), set()):
                problems.append(f"{k}: seqs not among its calls")
    mine = {k: a for k, a in last.items() if k in want}
    answered = {k: a for k, a in mine.items() if not _answer_error(arm, a)}
    failed = {k: a for k, a in mine.items() if _answer_error(arm, a)}
    by = lambda rs: dict(sorted(Counter(str(_stop(arm, a)) for a in rs.values()).items()))  # noqa: E731
    counts = {"arm": arm, "run_id": rid, "keys": len(want), "stored": len(mine), "answered": len(answered),
              "answered_by_stop": by(answered), "failed": len(failed), "failed_by_stop": by(failed),
              "missing": len(missing), "calls": len(calls),
              "retried_attempts": sum(bool((c.get("b4") or {}).get("retried")) for c in calls)}
    if arm == "B":
        n_att = [(((((a.get("generation") or {}).get("rlm") or {}).get("metadata") or {}).get("search_tools") or {})
                  .get("n_attempts", 0)) for a in mine.values()]
        counts.update(search_attempts=sum(n_att), answers_with_search_attempt=sum(1 for x in n_att if x))
    if arm == "C":
        counts["answered_under_3_sub_calls"] = sum(
            1 for a in answered.values()
            if ((((a.get("generation") or {}).get("rlm") or {}).get("metadata") or {}).get("sub_calls_ok", 0)
                < MIN_LLM_CALLS))
    return problems, counts


def verify_a(qpath: Path, sink: Path) -> int:
    """check_rlm_ref_ollama's entry: verify arm A on one sink, wherever it is."""
    problems, counts = verify("A", None, None, qpath, sink=sink)
    print("COUNTS: " + json.dumps(counts))
    for p in problems[:40]:
        print("FAIL " + p)
    print("verify: " + ("PASS" if not problems else f"{len(problems)} problems"))
    return 0 if not problems else 1


def progress(root: Path, qpath: Path = QUESTIONS) -> dict:
    ids = read_ids(qpath)["ids"]
    out = {}
    for arm in ARMS:
        last, _ = last_lines(Path(root) / run_id(arm))
        mine = {k: a for k, a in last.items() if k in {answer_key(arm, i) for i in ids}}
        out[arm] = {"run_id": run_id(arm), "stored": len(mine), "of": len(ids),
                    "with_error": sum(1 for a in mine.values() if _answer_error(arm, a))}
    return out


def stores(stores_root: Path, g1_sinks: Path, t2x_store: Path, arms=("B", "C"), machine: str = "studio") -> list:
    """T2's store check on each arm's store (<stores>/<config>), and each store's clone.sha256 equal to the store T2X's
    gemma3:27b run used (<t2x store>/clone.sha256): the same files, byte for byte."""
    sys.path.insert(0, str(ROOT / "findings" / "recompute" / "T2_runs"))
    import check_t2
    names = [CONFIG[a] for a in arms]
    problems = check_t2.stores(stores_root, g1_sinks, names, machine)
    ref = Path(t2x_store) / "clone.sha256"
    if not ref.exists():
        return problems + [f"no {ref}: the store T2X's gemma3:27b run used (G19_T2X_STORE)"]
    for nm in names:
        mine = Path(stores_root) / nm / "clone.sha256"
        if mine.exists() and mine.read_bytes() != ref.read_bytes():
            problems.append(f"{nm}: {mine} differs from {ref} (not the store T2X used)")
    return problems


# --------------------------------------------------------------------------------------------- the stored arm R

def manifest(t2_run: Path, t2x_run: Path, t2_collect: Path, t2x_collect: Path, qpath: Path = QUESTIONS) -> dict:
    q = read_ids(qpath)
    if set(q["t2_d98"]) | set(q["t2x"]) != set(q["ids"]) or len(q["t2_d98"]) != 29 or len(q["t2x"]) != 17:
        raise Refused("the questions file does not split the 46 into T2's 29 and T2X's 17")
    rid = run_id("R")
    rows, problems = [], []
    files = {}
    for src, run, coll, qids in (("T2", t2_run, t2_collect, q["t2_d98"]), ("T2X", t2x_run, t2x_collect, q["t2x"])):
        run, coll = Path(run), Path(coll)
        if run.name != rid:
            problems.append(f"{src}: {run} is not a sink of {rid}")
        af = run / "answers.jsonl"
        if not af.exists() or not coll.exists():
            problems.append(f"{src}: missing {af if not af.exists() else coll}")
            continue
        files[src] = {"answers": str(af), "answers_sha256": sha256_file(af), "collect": str(coll),
                      "collect_sha256": sha256_file(coll)}
        last, _ = last_lines(run)
        judged = Counter(r.get("answer_key") for r in read_jsonl(coll)
                         if r.get("run_id") == rid and r.get("draw") == DRAW and r.get("key_version") == "v2.5")
        for i in qids:
            k = answer_key("R", i)
            a = last.get(k)
            if a is None:
                problems.append(f"{src}: {k} has no line in {af}")
                continue
            if a.get("gen_model") != GEN_MODEL or a.get("config") != REF_CONFIG or a.get("draw") != DRAW \
                    or a.get("run_id") != rid:
                problems.append(f"{src}: {k} is gen_model {a.get('gen_model')!r} config {a.get('config')!r} draw "
                                f"{a.get('draw')!r}")
            if not judged[k]:
                problems.append(f"{src}: {k} has no key v2.5 row in {coll}")
            rows.append({"question_id": i, "kind": "one" if i in q["one_paper"] else "many", "source": src,
                         "answer_key": k, "line_sha256": sha256_bytes(json.dumps(a, sort_keys=True).encode()),
                         "error": bool((a.get("generation") or {}).get("error")), "judged_rows": judged[k]})
    if problems:
        raise Refused("; ".join(problems[:10]) + (f" (and {len(problems) - 10} more)" if len(problems) > 10 else ""))
    order = {i: n for n, i in enumerate(q["ids"])}
    rows.sort(key=lambda r: order[r["question_id"]])
    return {"decision": DECISION, "arm": "R", "label": ARM_LABEL["R"], "run_id": rid, "draw": DRAW,
            "questions_sha256": q["sha256"], "n": len(rows),
            "sources": {"T2": "T2's gemma3:27b rlm_10 draw 1 on D98's 29 (the T2 gemma3 clone's sink; judged in set "
                              "S6WT2LGEMMA, collect findings/recompute/S518_inputs/gemma3/collect.jsonl)",
                        "T2X": "T2X's gemma3:27b rlm_10 draw 1 on the 17 (D241, D243; the T2X clone's sink; judged by "
                               "judge_t2x.sh, collect T2X_runs/collect/t2xgemma_collect.jsonl)"},
            "files": files, "rows": rows}


# ------------------------------------------------------------------------------------------------------- estimate

def answer_times(a: dict) -> tuple:
    g = a["generation"]
    srv = sum(x.get("wall_s") or 0 for x in g["calls"])
    oth = max(g["latency_s"] - sum((x.get("waited_for_server_s") or 0) + (x.get("wall_s") or 0) for x in g["calls"]), 0)
    return srv, oth


def estimate_from(t2_run: Path, qpath: Path = QUESTIONS, t2x_records: Path | None = None) -> dict:
    """Per kind (one, many): mean server s and other s of T2's gemma3 rlm_10 answers (draws 1 to 3) on the 46's
    questions it holds; hours per arm = sum over the 46 of its kind's time (low: server only; high: server + other)."""
    q = read_ids(qpath)
    af = Path(t2_run) / "answers.jsonl"
    rows = [a for a in read_jsonl(af) if a.get("question_id") in set(q["ids"]) and a.get("config") == REF_CONFIG
            and not (a.get("generation") or {}).get("error")]
    kinds = {}
    for kind, qs in (("one", set(q["one_paper"])), ("many", set(q["many_paper"]))):
        t = [answer_times(a) for a in rows if a["question_id"] in qs]
        if not t:
            raise Refused(f"{af}: no {kind}-paper answer of the 46")
        kinds[kind] = {"answers_read": len(t), "server_s_mean": round(statistics.mean(x[0] for x in t), 1),
                       "server_s_median": round(statistics.median(x[0] for x in t), 1),
                       "other_s_mean": round(statistics.mean(x[1] for x in t), 1)}
    n = {"one": len(q["one_paper"]), "many": len(q["many_paper"])}
    lo = sum(n[k] * kinds[k]["server_s_mean"] for k in n) / 3600
    hi = sum(n[k] * (kinds[k]["server_s_mean"] + kinds[k]["other_s_mean"]) for k in n) / 3600
    arm = [round(lo, 2), round(hi, 2)]
    out = {"decision": DECISION, "how": "T2X README's method on T2's gemma3:27b rlm_10 answers (draws 1 to 3) of the 46: "
           "server s = the sum of an answer's calls' wall_s (one request at a time per server), other s = latency minus "
           "every call's wait and wall (retrieval, the RLM's code, the pool). An arm = 20 one-paper + 26 many-paper "
           "answers; low = the server never idle, high = nothing overlaps. B and C are taken as R's time; A (the "
           "package) has no gemma3 timing and is taken as R's, UNVERIFIED until its smoke.",
           "input": {"path": str(af), "sha256": sha256_file(af)}, "kinds": kinds, "per_arm_hours": arm,
           "ports": {"1": [round(3 * lo, 2), round(3 * hi, 2)],      # the three arms one after the other
                     "2": [round(2 * lo, 2), round(2 * hi, 2)],      # two arms on one port, one on the other
                     "3": arm}}                                        # one arm per port
    if t2x_records is not None:
        out["t2x_measured"] = t2x_measured(t2x_records)
    return out


def t2x_measured(path: Path) -> dict:
    """T2X's gemma3:27b run's start and end (t2x_records.jsonl, written by run_t2x.sh on the Studio). The run holds
    single_pass and rlm_10 (T2X_CONFIGS' default), so its span bounds rlm_10's time from above, on one port."""
    from datetime import datetime
    recs = [r for r in read_jsonl(path) if r.get("generator") == GEN_MODEL and r.get("mode") in ("run", "resume")]
    starts = {r["start"]: r for r in recs if "end" not in r}
    ends = {r["start"]: r for r in recs if "end" in r}
    spans = []
    for s, r in starts.items():
        if s in ends:
            t0 = datetime.fromisoformat(s.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(ends[s]["end"].replace("Z", "+00:00"))
            spans.append({"start": s, "end": ends[s]["end"], "rc": ends[s].get("rc"),
                          "hours": round((t1 - t0).total_seconds() / 3600, 2)})
    hours = round(sum(x["hours"] for x in spans), 2)
    return {"records": str(path), "sha256": sha256_file(path), "spans": spans, "hours_17_many": hours,
            "per_answer_s": round(hours * 3600 / 17, 1) if spans else None}


def estimate_lines(e: dict) -> list:
    k = e["kinds"]
    lines = [f"time estimate ({DECISION}; {e['input']['path']}):",
             f"  R's gemma3 rlm_10: one-paper {k['one']['server_s_mean']} s server + {k['one']['other_s_mean']} s other "
             f"an answer ({k['one']['answers_read']} answers), many-paper {k['many']['server_s_mean']} s + "
             f"{k['many']['other_s_mean']} s ({k['many']['answers_read']} answers)",
             f"  one arm (46 answers): {e['per_arm_hours'][0]:.1f} to {e['per_arm_hours'][1]:.1f} h",
             f"  138 answers: one port {e['ports']['1'][0]:.1f} to {e['ports']['1'][1]:.1f} h; two ports "
             f"{e['ports']['2'][0]:.1f} to {e['ports']['2'][1]:.1f} h (two arms on one); three ports "
             f"{e['ports']['3'][0]:.1f} to {e['ports']['3'][1]:.1f} h; plus a load per port"]
    m = e.get("t2x_measured")
    if m:
        lines.append(f"  T2X measured, one port: gemma3 rlm_10 plus single_pass on the 17 many-paper took "
                     f"{m['hours_17_many']} h (at most {m['per_answer_s']} s an rlm_10 answer)")
    return lines


# ------------------------------------------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("questions")
    p.add_argument("--write", action="store_true")
    sub.add_parser("match")
    p = sub.add_parser("seeds")
    p.add_argument("calls", nargs="+", type=Path)
    p = sub.add_parser("smoke")
    p.add_argument("arm", choices=ARMS)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--server", required=True)
    p.add_argument("--commit", default="")
    p.add_argument("--write", type=Path)
    p = sub.add_parser("verify")
    p.add_argument("arm", choices=ARMS)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--server")
    p = sub.add_parser("progress")
    p.add_argument("--root", type=Path, required=True)
    p = sub.add_parser("stored")
    p.add_argument("arm", choices=ARMS)
    p.add_argument("--root", type=Path, required=True)
    p = sub.add_parser("stores")
    p.add_argument("--stores", type=Path, required=True)
    p.add_argument("--g1-sinks", type=Path, required=True)
    p.add_argument("--t2x-store", type=Path, required=True)
    p.add_argument("--arms", nargs="+", choices=("B", "C"), default=["B", "C"])
    p = sub.add_parser("manifest")
    for x in ("--t2-run", "--t2x-run", "--t2-collect", "--t2x-collect"):
        p.add_argument(x, type=Path, required=True)
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("estimate")
    p.add_argument("--t2-run", type=Path)
    p.add_argument("--t2x-records", type=Path)
    p.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "questions":
            d = compute_questions()
            if a.write:
                QUESTIONS.write_text(questions_text(d), encoding="utf-8")
                print(f"written {QUESTIONS.name}: {d['counts']}")
            else:
                check_questions()
                print(f"QUESTIONS OK: {QUESTIONS.name} equals the rule {d['counts']}, sha256 "
                      f"{sha256_file(QUESTIONS)[:12]}")
            return 0
        if a.cmd == "match":
            return cmd_match()
        if a.cmd == "seeds":
            return cmd_seeds(QUESTIONS, a.calls)
        if a.cmd == "smoke":
            ok, problems, facts = smoke_verdict(a.arm, a.root, a.server)
            v = {"pass": ok, "arm": a.arm, "run_id": run_id(a.arm, smoke=True), "commit": a.commit,
                 "server": a.server, "problems": problems, "facts": facts}
            if a.write:
                a.write.write_text(json.dumps(v, indent=1) + "\n")
            print(json.dumps(facts))
            print("SMOKE PASS" if ok else "SMOKE FAIL: " + "; ".join(problems[:5]))
            return 0 if ok else 1
        if a.cmd == "verify":
            problems, counts = verify(a.arm, a.root, a.server)
            for x in problems[:40]:
                print("PROBLEM", x)
            print("COUNTS: " + json.dumps(counts))
            print("VERIFY PASS" if not problems else f"VERIFY FAIL: {len(problems)} problems")
            return 0 if not problems else 1
        if a.cmd == "progress":
            print(json.dumps(progress(a.root), indent=1))
            return 0
        if a.cmd == "stored":
            n = progress(a.root)[a.arm]["stored"]
            print(n)
            return 0 if n else 1
        if a.cmd == "stores":
            problems = stores(a.stores, a.g1_sinks, a.t2x_store, a.arms)
            print("stores: every store holds G1's index and equals T2X's" if not problems
                  else "stores: " + "; ".join(problems))
            return 0 if not problems else 1
        if a.cmd == "manifest":
            m = manifest(a.t2_run, a.t2x_run, a.t2_collect, a.t2x_collect)
            if a.write:
                MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
                print(f"written {MANIFEST.name}")
            print(f"MANIFEST OK: R holds {m['n']} answers ({Counter(r['source'] for r in m['rows'])}), every one "
                  f"judged on key v2.5; failed {sum(r['error'] for r in m['rows'])}")
            return 0
        if a.cmd == "estimate":
            if a.t2_run:
                e = estimate_from(a.t2_run, t2x_records=a.t2x_records)
                if a.write:
                    ESTIMATE.write_text(json.dumps(e, indent=1) + "\n")
                    print(f"written {ESTIMATE.name}")
            else:
                e = json.loads(ESTIMATE.read_text())
                if a.t2x_records:
                    e["t2x_measured"] = t2x_measured(a.t2x_records)
            print("\n".join(estimate_lines(e)))
            return 0
    except Refused as e:
        print("REFUSED:", e)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
