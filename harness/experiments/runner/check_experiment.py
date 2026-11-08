"""Checks for experiments/runner/experiment.py. Offline except one live start and stop of the tool server on
127.0.0.1 with a dummy run (no model call; the context's base_url is never contacted).

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_experiment

1. questions(): 135, in the v2.4 key's order, ids distinct, the fields FIELDS; CD_015, SY_010 and OOD_011 absent;
   the set is the submission's question set on 20 core papers (the harness filter, exp_01_generation.py:229-233,
   applied to the v1 key data/replication_inputs/ground_truth.json: 138) less D48's three; answerable is the D5
   key's; per category 20, 20, 20, 17, 9 and 49; a caller's change to a returned question does not reach the next.
2. draws(): (1, 2, 3) for Figures 2, 3 (D78 Q116) and 4, (1,) for 6; Figures 1 and 5, "2", 2.0 and True refused.
3. Keys: answer_key's two forms, distinct across draw and index; a part with '|' or a space, and draws 0, True and
   "1", refused. run_id's form; a part with '/', '__', a leading '.', or empty, refused.
4. context(): allowed is the models as generators and the lock's judge as judge (both where a generator is the
   judge's model; no judge with judge=False); agent_roles is exactly the dict given (no 'default'); inside the run,
   check_model allows the judge only as judge. Refused: a model the lock cannot run, claude::, no provider, a
   [think:x] suffix, no models, a thinking level the lock does not name (Ollama and Gemini), and a run-level
   context with draw None that allows a generator; a run of another arm or experiment, a run_id of another form,
   and a sink of another run.
5. sink(): created under the root; the same run finds its own sink again; a ctx/run.json of another run, or one
   that is not JSON, is refused. The run's identity: the first context writes <sink>/run_identity.json; another
   item, draw or base_url of the same run is accepted; other models, judge, thinking or tools are refused and leave
   the file as it was; a run_identity.json that is not JSON is refused.
6. Live: tool_server() on a dummy run (tools: validate_python_syntax). It writes ctx/run.json, serves on a free
   port other than 8777, sets TOOL_SERVER_URL in the environment and in backend.config.settings (imported before),
   and Mentori's engine path (sse_client(f"{settings.TOOL_SERVER_URL}/sse"), ClientSession) lists exactly the run's
   tools and runs one; a second tool_server() in the same process is refused; on exit the port is closed and the
   environment and setting are as before; no model call was recorded. The parent's working directory is the
   scratch directory, not the repository, for all of 6. While the server serves, its port cannot be bound by
   another socket, and the server's start line names that port (the launcher refuses a socket bound elsewhere).
   Mentori's app.log is written in <sink>/backend/logs/, and
   the repository's backend/logs/app.log does not grow. An item context is refused before anything starts; a
   run-level context of the same run under other models is refused before ctx/run.json is overwritten. A server
   with an SSE connection still open at exit is stopped (port closed, within SIGTERM plus the SIGKILL wait). A run
   whose run.json enables a tool the server lacks: the server exits before it serves, the refusal shows the
   server's own error, and the setting is unchanged.
7. G4's two named sets (Q105, D75), offline, run before 6. scaling_questions(n) at 5, 10, 20 and 50 core papers:
   "common" is questions() at every size; "per_size" is exactly the D5 key's questions that scripts/key_scope.py
   Scope.in_scope keeps at n, in the v2.4 key's order, 66, 90, 135 and 244, D48's three absent, every question of
   FIELDS; at 20 per_size is the common set, at 5 and 10 inside it, at 50 it holds it and 109 more (all answerable,
   min_core 50); core sizes 15, 0, "5", 5.0, True and None refused; a caller's change does not reach the next call.
   exp_02_scaling_factorial.py: index_questions() on one index of each size asks the union of the two sets once, in
   the key's order (135, 135, 135, 244), each question carrying the names of the sets it is in (69 common only at
   5, 45 at 10, none at 20, 109 per_size only at 50); --max-questions keeps the first n; the work list asks it on
   every (index, config, draw); a stored answer carries question_sets; a resume of answers without question_sets is
   refused; the report's JSON names both sets of every index and its markdown counts the answers in each (the
   report's save functions replaced, so nothing is written).
   B9 F1 (16 Oct), exp_01_generation.py's smoke test: a run with --max-questions is its own run,
   exp_01__<config>__<index>.smoke, for all 7 configs (named as exp_02 names one), with the paper run's answer keys;
   run_experiment and main() run with the strategies, database, index and router stubbed and RUNS_ROOT on a scratch
   folder: a smoke beside a paper run with a stored answer starts, writes only in <paper run>.smoke and leaves the
   paper run's bytes unchanged; a second smoke without --resume is refused on its own answers; the paper run is
   refused on the paper run's; with --sink-root every sink and index identity is under it and nothing under
   RUNS_ROOT; the matched-budget arm's smoke runs in its .smoke run without checking or writing the paper arm, whose
   own run is refused on another plan; the dry run (CLI) lists the .smoke run under --sink-root, and the paper run
   under RUNS_ROOT without it.
   Q141 restart (D83), exp_01's --skip-failed, on a smoke sink holding a key stored without an error, a key whose two
   lines are both errors, a key stored with an error and a key not stored: work_list marks each present, failed,
   skip and retry; --resume runs the two failed keys and the unstored one; --resume --skip-failed runs the unstored
   one only and leaves the failed keys' error lines their answers, the earlier lines byte for byte; each start logs
   its resume mode and counts; a second start runs nothing; skip_failed without resume, and the CLI's --skip-failed
   without --resume, are refused before anything starts; a sink holding only a failed key is refused without
   --resume; the dry run counts the failed keys as stored with --skip-failed and as to run again without it.
   F48 (audit of 16 Oct), the index check before a run: expected_chunks() is S66's 12 indexes, exactly ALL_INDEXES,
   30,337 chunks; chroma_counts() counts each collection's METADATA-segment rows in a scratch Chroma 1.4 sqlite
   (an empty collection 0) from a read-only file whose bytes and mtime it leaves unchanged, and refuses a folder
   with no store; index_problems() gives none when every count matches and one line per bad index, naming it
   (count off by one, not READY, not looked up, collection absent, not in S66); on the scratch database
   mentori_collections() and check_indexes() pass a READY index with its 196 chunks and stop on two bad ones out of
   three, naming only those; run_experiment() with a missing index exits non-zero before writing a sink or a report;
   --dry-run still prints without reading the database.
8. Q108 (D78), last: runs_snapshot names each path added, removed or rewritten and ignores what was already there;
   findings/runs, every path with its sha256, is the same at the check's end as at its start.
"""

import asyncio
import json
import os
import socket
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from experiments.runner import runs_snapshot

ROOT = Path(__file__).resolve().parents[2]
# Q108 (D78): findings/runs as it is at the check's start, every path with its sha256; compared at the end
RUNS_BEFORE = runs_snapshot.take(ROOT / "findings" / "runs")
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_experiment_")).resolve()
# Mentori's settings read these at import, here and in the tool server: a scratch database, workspace and vector
# store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
os.environ["TOOL_SERVER_URL"] = "http://127.0.0.1:9"      # what the engine would reach without tool_server()
sys.path.insert(0, str(MENTORI))

from backend.config import settings  # noqa: E402

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

lock = load()
JUDGE = lock.d["judge"]["model"]
BASE = "http://127.0.0.1:21441"     # never contacted: nothing here makes a model call
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(fn, kind=Exception):
    try:
        fn()
    except kind as e:
        return e
    except Exception as e:   # the wrong kind
        return AssertionError(f"{type(e).__name__}: {e}")
    return None


# 1. questions
qs = ex.questions()
ids = [q["id"] for q in qs]
v24 = [r["id"] for r in json.loads(ex.KEY_V24.read_text())["records"]]
check("1 questions(): 135, distinct, in the v2.4 key's order", len(qs) == 135 and len(set(ids)) == 135
      and ids == [i for i in v24 if i in set(ids)], f"{len(qs)}, first {ids[0]}, last {ids[-1]}")
check("1 each question has exactly the fields " + ", ".join(ex.FIELDS), all(tuple(q) == ex.FIELDS for q in qs))
check("1 CD_015, SY_010 and OOD_011 are absent", not set(ex.DROPPED_D48) & set(ids))
v1 = json.loads((ROOT / "data" / "replication_inputs" / "ground_truth.json").read_text())["questions"]
harness = {q["id"] for q in v1 if q.get("category") == "out_of_domain"
           or (q.get("min_core") is not None and q["min_core"] <= 20)}
check("1 the set is the harness's 138 on 20 core papers (v1 key) less D48's three",
      len(harness) == 138 and set(ids) == harness - set(ex.DROPPED_D48), f"harness {len(harness)}")
d5 = {q["id"]: q for q in json.loads(ex.KEY_D5.read_text())["questions"]}
check("1 answerable is the D5 key's on every question (the ten false-premise questions answerable)",
      all(q["answerable"] == d5[q["id"]]["answerable"] for q in qs)
      and sorted(q["id"] for q in qs if q["answer_type"] == "refutation" and q["answerable"])
      == [f"OOD_0{n}" for n in range(41, 51)])
cats = Counter(q["category"] for q in qs)
check("1 per category: 20 factual, 20 conceptual, 20 technical, 17 cross-document, 9 synthesis, 49 out of domain",
      cats == {"factual_recall": 20, "conceptual": 20, "technical": 20, "cross_document": 17, "synthesis": 9,
               "out_of_domain": 49}, json.dumps(cats))
qs[0]["question"] = "changed"
qs[0]["key_concepts"].append("changed")
again = ex.questions()[0]
check("1 a change to a returned question does not reach the next call",
      again["question"] != "changed" and "changed" not in again["key_concepts"])

# 2. draws
check("2 draws: (1, 2, 3) for Figures 2, 4 and 3 (D78 Q116), (1,) for 6",
      [ex.draws(f) for f in (2, 4, 3, 6)] == [(1, 2, 3), (1, 2, 3), (1, 2, 3), (1,)])
bad = [(f, raises(lambda f=f: ex.draws(f), ex.ExperimentError)) for f in (1, 5, "2", 2.0, True)]
check("2 draws refuses Figures 1 and 5, '2', 2.0 and True", all(isinstance(e, ex.ExperimentError) for _, e in bad),
      "; ".join(f"{f!r}: {type(e).__name__}" for f, e in bad))

# 3. keys
k1 = ex.answer_key("rlm_10", "01_sarek_FR1", 1)
k2 = ex.answer_key("rlm_10", "01_sarek_FR1", 2)
k3 = ex.answer_key("qwen3-coder:30b", "01_sarek_FR1", 1, index="exp_v4_s20_n0")
k4 = ex.answer_key("qwen3-coder:30b", "01_sarek_FR1", 1, index="exp_v4_s50_n0")
check("3 answer_key: config|question_id|d<draw>, and index|config|question_id|d<draw>",
      k1 == "rlm_10|01_sarek_FR1|d1" and k3 == "exp_v4_s20_n0|qwen3-coder:30b|01_sarek_FR1|d1", f"{k1}  {k3}")
check("3 answer keys differ across draw and index", len({k1, k2, k3, k4}) == 4)
bad = [raises(fn, ex.ExperimentError) for fn in (
    lambda: ex.answer_key("a|b", "Q", 1), lambda: ex.answer_key("rlm 10", "Q", 1),
    lambda: ex.answer_key("c", "Q|1", 1), lambda: ex.answer_key("c", "Q", 1, index="i|j"),
    lambda: ex.answer_key("c", "Q", 0), lambda: ex.answer_key("c", "Q", True), lambda: ex.answer_key("c", "Q", "1"))]
check("3 answer_key refuses '|' and a space in a part, and draws 0, True and '1'",
      all(isinstance(e, ex.ExperimentError) for e in bad), "; ".join(type(e).__name__ for e in bad))
check("3 run_id: experiment__arm and experiment__arm__extra",
      ex.run_id("exp_03", "full_pipeline") == "exp_03__full_pipeline"
      and ex.run_id("exp_01", "rlm_10", "s20") == "exp_01__rlm_10__s20")
bad = [raises(fn, ex.ExperimentError) for fn in (
    lambda: ex.run_id("exp/01", "a"), lambda: ex.run_id("exp_01", "a__b"), lambda: ex.run_id(".x", "a"),
    lambda: ex.run_id("", "a"), lambda: ex.run_id("exp_01", "a", ""))]
check("3 run_id refuses '/', '__', a leading '.', and an empty part", all(isinstance(e, ex.ExperimentError)
      for e in bad), "; ".join(type(e).__name__ for e in bad))

# 4. contexts
runs = tmp / "runs"


def mk(experiment, arm, item, draw, models, thinking=None, extra=None, **kw):
    """context() of run experiment__arm[__extra] in its own sink under the scratch runs/."""
    rid = ex.run_id(experiment, arm, extra)
    return ex.context(experiment, arm, item, draw, models, thinking, base_url=kw.pop("base_url", BASE), run=rid,
                      sink=ex.sink(rid, root=runs), **kw)


MODELS = {"handyman": "gemini::gemini-3-flash-preview", "coder": "ollama::qwen3-coder:30b"}
c = mk("exp_03", "full_pipeline", "01_sarek_FR1", 2, MODELS)
sk = (runs / "exp_03__full_pipeline").resolve()
check("4 allowed: the models as generators, the lock's judge as judge",
      c.allowed == {"gemini-3-flash-preview": "generator", "qwen3-coder:30b": "generator", JUDGE: "judge"},
      json.dumps(c.allowed))
check("4 agent_roles is exactly the dict given (no 'default'); run_id, arm, item, draw and sink as given",
      c.agent_roles == MODELS and "default" not in c.agent_roles and c.run_id == "exp_03__full_pipeline"
      and (c.arm, c.item_id, c.draw, c.sink) == ("full_pipeline", "01_sarek_FR1", 2, sk))
with rc.run(c):
    e_gen = raises(lambda: rc.check_model(JUDGE, "generator"), LockError)
    e_judge = raises(lambda: rc.check_model(JUDGE, "judge"))
check("4 inside the run the judge is allowed as judge only", isinstance(e_gen, LockError) and e_judge is None,
      str(e_gen)[:90])
c = mk("exp_03", "full_pipeline", "Q", 1, MODELS, extra="nojudge", judge=False)
check("4 judge=False: no judge allowed", JUDGE not in c.allowed, json.dumps(c.allowed))
c = mk("exp_05", "devstral", "Q", 1, {"coder": f"ollama::{JUDGE}"})
check("4 the judge's model as a Mentori component: allowed as generator and judge",
      c.allowed == {JUDGE: ["generator", "judge"]}, json.dumps(c.allowed))
s10 = ex.sink(ex.run_id("exp_01", "rlm_10", "s20"), root=runs)
s20 = ex.sink(ex.run_id("exp_01", "rlm_20", "s20"), root=runs)
cases = {
    "a model the lock cannot run": (lambda: mk("e", "a", "Q", 1, {"coder": "ollama::mistral:7b"}), LockError),
    "claude::": (lambda: mk("e", "a", "Q", 1, {"coder": "claude::claude-haiku-4-5"}), ex.ExperimentError),
    "no provider": (lambda: mk("e", "a", "Q", 1, {"coder": "qwen3-coder:30b"}), ex.ExperimentError),
    "a [think:x] suffix": (lambda: mk("e", "a", "Q", 1, {"coder": "ollama::gpt-oss:20b[think:high]"}),
                           ex.ExperimentError),
    "no models": (lambda: mk("e", "a", "Q", 1, {}), ex.ExperimentError),
    "a thinking level the lock does not name (Ollama)": (lambda: mk(
        "e", "a", "Q", 1, {"coder": "ollama::qwen3-coder:30b"}, "high"), LockError),
    "a thinking level the lock does not name (Gemini)": (lambda: mk(
        "e", "a", "Q", 1, {"handyman": "gemini::gemini-3-flash-preview"}, "high"), LockError),
    "a run-level context with draw None that allows a generator": (lambda: mk(
        "e", "a", None, None, MODELS), rc.RunContextError),
    "a run of another arm": (lambda: ex.context("exp_01", "rlm_20", "Q", 1, MODELS, base_url=BASE,
                                                run="exp_01__rlm_10__s20", sink=s10), ex.ExperimentError),
    "a run of another experiment": (lambda: ex.context("exp_02", "rlm_10", "Q", 1, MODELS, base_url=BASE,
                                                       run="exp_01__rlm_10__s20", sink=s10), ex.ExperimentError),
    "a run_id of another form (an arm that only starts with the arm)": (lambda: ex.context(
        "exp_01", "rlm_1", "Q", 1, MODELS, base_url=BASE, run="exp_01__rlm_10__s20", sink=s10), ex.ExperimentError),
    "a run_id of another form (four parts)": (lambda: ex.context(
        "exp_01", "rlm_10", "Q", 1, MODELS, base_url=BASE, run="exp_01__rlm_10__s20__x"), ex.ExperimentError),
    "a sink of another run": (lambda: ex.context("exp_01", "rlm_10", "Q", 1, MODELS, base_url=BASE,
                                                 run="exp_01__rlm_10__s20", sink=s20), ex.ExperimentError),
}
for label, (fn, kind) in cases.items():
    e = raises(fn, kind)
    check(f"4 refused: {label}", isinstance(e, kind), f"{type(e).__name__}: {str(e)[:90]}")
check("4 a refused context writes no run identity", not (runs / "e__a" / ex.IDENTITY_FILE).exists()
      and not (s10 / ex.IDENTITY_FILE).exists() and not (s20 / ex.IDENTITY_FILE).exists())
c = mk("exp_06", "rlm", "Q", 1, {"coder": "ollama::gpt-oss:20b"}, "high")
check("4 a thinking level the lock names (gpt-oss:20b high) is accepted", c.thinking == "high")

# 5. sinks
rid = ex.run_id("exp_01", "rlm_10", "s20")
s1 = ex.sink(rid, root=runs)
check("5 sink: <root>/<run_id>/, created", s1 == (runs / rid).resolve() and s1.is_dir(), str(s1))
with rc.run(ex.context("exp_01", "rlm_10", None, 1, MODELS, base_url=BASE, run=rid, sink=s1)):
    rc.dump(rc.RUN_TASK_ID)
check("5 the same run finds its own sink again (resume)", raises(lambda: ex.sink(rid, root=runs)) is None)
other = ex.sink(ex.run_id("exp_01", "rlm_20", "s20"), root=runs)
(other / "ctx").mkdir()
(other / "ctx" / "run.json").write_text((s1 / "ctx" / "run.json").read_text())
e = raises(lambda: ex.sink(ex.run_id("exp_01", "rlm_20", "s20"), root=runs), ex.ExperimentError)
check("5 a sink holding another run's run.json is refused", isinstance(e, ex.ExperimentError), str(e)[:110])
(other / "ctx" / "run.json").write_text("{not json")
e = raises(lambda: ex.sink(ex.run_id("exp_01", "rlm_20", "s20"), root=runs), ex.ExperimentError)
check("5 a run.json that is not JSON is refused", isinstance(e, ex.ExperimentError), str(e)[:110])
ident_path = s1 / ex.IDENTITY_FILE
ident = json.loads(ident_path.read_text())
check("5 the run's first context wrote <sink>/run_identity.json with its configuration",
      ident == {"run_id": rid, "arm": "rlm_10", "allowed": {"gemini-3-flash-preview": "generator",
                "qwen3-coder:30b": "generator", JUDGE: "judge"}, "agent_roles": MODELS, "thinking": None,
                "tools": None}, json.dumps(ident)[:110])
same = [raises(fn) for fn in (
    lambda: ex.context("exp_01", "rlm_10", "01_sarek_FR1", 3, MODELS, base_url=BASE, run=rid, sink=s1),
    lambda: ex.context("exp_01", "rlm_10", "OOD_041", 2, MODELS, base_url="http://127.0.0.1:21442", run=rid, sink=s1),
    lambda: ex.context("exp_01", "rlm_10", None, 2, MODELS, base_url=BASE, run=rid, sink=s1))]
check("5 the same run with another item, draw or base_url is accepted (resume)", same == [None, None, None],
      "; ".join(str(e)[:60] for e in same if e))
before = ident_path.read_bytes()
others = {
    "other models": lambda: ex.context("exp_01", "rlm_10", "Q", 1, {"coder": "ollama::gpt-oss:20b"}, base_url=BASE,
                                       run=rid, sink=s1),
    "the same models under other roles": lambda: ex.context(
        "exp_01", "rlm_10", "Q", 1, {"handyman": "ollama::qwen3-coder:30b", "coder": "gemini::gemini-3-flash-preview"},
        base_url=BASE, run=rid, sink=s1),
    "no judge": lambda: ex.context("exp_01", "rlm_10", "Q", 1, MODELS, base_url=BASE, run=rid, sink=s1, judge=False),
    "other thinking": lambda: ex.context("exp_01", "rlm_10", "Q", 1, MODELS, False, base_url=BASE, run=rid, sink=s1),
    "other tools": lambda: ex.context("exp_01", "rlm_10", "Q", 1, MODELS, base_url=BASE, run=rid, sink=s1,
                                      tools=["validate_python_syntax"]),
}
for label, fn in others.items():
    e = raises(fn, ex.ExperimentError)
    check(f"5 the same run under {label} is refused", isinstance(e, ex.ExperimentError), str(e)[:110])
check("5 a refused configuration leaves run_identity.json as it was", ident_path.read_bytes() == before)
bad_ident = ex.sink(ex.run_id("exp_01", "rlm_50"), root=runs)
(bad_ident / ex.IDENTITY_FILE).write_text("{not json")
e = raises(lambda: ex.context("exp_01", "rlm_50", "Q", 1, MODELS, base_url=BASE, run="exp_01__rlm_50",
                              sink=bad_ident), ex.ExperimentError)
check("5 a run_identity.json that is not JSON is refused", isinstance(e, ex.ExperimentError), str(e)[:110])

# 7. G4's two named sets (Q105, D75); offline, before the live part
sys.path.append(str(ROOT / "scripts"))
sys.path.insert(0, str(MENTORI / "publication" / "scripts"))
from key_scope import Scope  # noqa: E402

sc = Scope()
key_order = [i for i in v24 if i in sc.records]
common_ids = [q["id"] for q in ex.questions()]
sets = {n: ex.scaling_questions(n) for n in ex.SCALING_CORE_SIZES}
per = {n: [q["id"] for q in sets[n]["per_size"]] for n in sets}
check("7 scaling_questions: the two named sets, common and per_size, at 5, 10, 20 and 50 core papers",
      ex.SCALING_CORE_SIZES == (5, 10, 20, 50) and ex.SCALING_SETS == ("common", "per_size")
      and all(tuple(sets[n]) == ex.SCALING_SETS for n in sets))
check("7 common is questions() (the 135) at every size",
      all([q["id"] for q in sets[n]["common"]] == common_ids and sets[n]["common"] == ex.questions() for n in sets))
check("7 per_size is the D5 key's questions key_scope.in_scope keeps, in the v2.4 key's order: 66, 90, 135, 244",
      all(per[n] == [i for i in key_order if sc.in_scope(i, n)] for n in sets)
      and [len(per[n]) for n in sets] == [66, 90, 135, 244], "/".join(str(len(per[n])) for n in sets))
check("7 per_size: D48's three absent, every question of FIELDS, answerable the D5 key's",
      all(not set(ex.DROPPED_D48) & set(per[n]) and all(tuple(q) == ex.FIELDS
          and q["answerable"] == sc.records[q["id"]]["answerable"] for q in sets[n]["per_size"]) for n in sets))
only50 = [i for i in per[50] if i not in set(common_ids)]
check("7 per_size is common at 20, inside it at 5 and 10, and at 50 holds it and 109 more (answerable, min_core 50)",
      per[20] == common_ids and set(per[5]) < set(common_ids) and set(per[10]) < set(common_ids)
      and set(common_ids) < set(per[50]) and len(only50) == 109
      and all(sc.records[i]["answerable"] and sc.records[i]["min_core"] == 50 for i in only50), f"{len(only50)} more")
bad = [(n, raises(lambda n=n: ex.scaling_questions(n), ex.ExperimentError)) for n in (15, 0, "5", 5.0, True, None)]
check("7 scaling_questions refuses core sizes 15, 0, '5', 5.0, True and None",
      all(isinstance(e, ex.ExperimentError) for _, e in bad), "; ".join(f"{n!r}: {type(e).__name__}" for n, e in bad))
got = ex.scaling_questions(50)
got["per_size"][0]["question"] = "changed"
got["per_size"][0]["key_concepts"].append("changed")
again = ex.scaling_questions(50)["per_size"][0]
check("7 a change to a returned per_size question does not reach the next call",
      again["question"] != "changed" and "changed" not in again["key_concepts"])

import exp_02_scaling_factorial as e02  # noqa: E402

GEN = e02.GenerationResult(answer="a", latency_s=1.0, llm_calls=1, tokens_used=1, retrieved_passages=1,
                          config="single_pass", gen_model=e02.GEN_MODEL)
IDX = {5: "exp_v4_s5_n0", 10: "exp_v4_s10_n1", 20: "exp_v4_s20_n3", 50: "exp_v4_s50_n0"}
asked = {n: e02.index_questions(IDX[n]) for n in IDX}
check("7 exp_02 asks, on each index, the union of the two sets once, in the key's order: 135, 135, 135, 244",
      all([q["id"] for q in asked[n]] == [i for i in key_order if i in set(common_ids) | set(per[n])] for n in IDX)
      and [len(asked[n]) for n in IDX] == [135, 135, 135, 244], "/".join(str(len(asked[n])) for n in IDX))
check("7 exp_02: every asked question carries the names of the sets it is in",
      all(q["question_sets"] == [s for s, ids in (("common", common_ids), ("per_size", per[n])) if q["id"] in ids]
          for n in IDX for q in asked[n]))
only = {n: (sum(q["question_sets"] == ["common"] for q in asked[n]),
            sum(q["question_sets"] == ["per_size"] for q in asked[n])) for n in IDX}
check("7 exp_02: common only 69, 45, 0, 0 and per_size only 0, 0, 0, 109 at 5, 10, 20, 50",
      [only[n] for n in IDX] == [(69, 0), (45, 0), (0, 0), (0, 109)], json.dumps(only))
check("7 exp_02: --max-questions keeps the first n asked", [q["id"] for q in e02.index_questions(IDX[50], 3)]
      == [q["id"] for q in asked[50][:3]])
wl = e02.work_list(list(IDX.values()), ["single_pass", "rlm_10"], None, tmp / "e02_no_sinks")
check("7 exp_02: the work list asks index_questions on every (index, config, draw)",
      len(wl) == 4 * 2 * 3 and all(w["questions"] == e02.index_questions(w["index_name"]) == w["pending"] for w in wl))
row = e02._row(IDX[5], "single_pass", asked[5][-1], 1, GEN, "r")
check("7 exp_02: a stored answer carries question_sets", row["question_sets"] == asked[5][-1]["question_sets"]
      and row["question_sets"], json.dumps(row["question_sets"]))
old_sink = tmp / "e02_old_sink" / e02.ANSWERS     # the sink is the resume source since the review of 16 October
old_sink.parent.mkdir(parents=True, exist_ok=True)
old_sink.write_text(json.dumps({"answer_key": "exp_v4_s5_n0|single_pass|Q|d1", "question_id": "Q"}) + "\n")
e = raises(lambda: e02.stored_rows(old_sink), SystemExit)
check("7 exp_02: a resume over stored answers without question_sets is refused",
      e is not None and "question_sets" in str(e), str(e)[:90])
saved_fns = e02.save_v4_results, e02.save_v4_markdown
out = {}
e02.save_v4_results = lambda data, prefix: (out.update(json=data, prefix=prefix) or (tmp / "r.json", None))
e02.save_v4_markdown = lambda content, prefix: (out.update(md=content) or tmp / "r.md")
rows = [dict(e02._row(IDX[n], "single_pass", q, 1, GEN, "r")) for n in (5, 50)
        for q in asked[n]]
import contextlib, io, logging, shutil  # noqa: E401,E402
with contextlib.redirect_stdout(io.StringIO()):
    e02._generate_report(rows, [IDX[5], IDX[50]], ["single_pass"])
e02.save_v4_results, e02.save_v4_markdown = saved_fns
qs_out = out.get("json", {}).get("question_sets", {})
check("7 exp_02 report: its JSON names both sets of every index",
      qs_out.get(IDX[5]) == {"common": common_ids, "per_size": per[5]}
      and qs_out.get(IDX[50]) == {"common": common_ids, "per_size": per[50]})
check("7 exp_02 report: its markdown counts the answers in each set (135 / 66 at 5, 135 / 244 at 50)",
      "| single_pass | 135 / 66 | 135 / 244 |" in out.get("md", "").replace("  ", " "),
      next((ln for ln in out.get("md", "").splitlines() if " / " in ln and "single_pass" in ln), ""))

# B9 F1 (16 Oct): exp_01's smoke test (--max-questions) is its own run, exp_01__<config>__<index>.smoke, as exp_02's,
# and --sink-root puts every sink under another directory, as exp_03's. The runs below go through run_experiment and
# main() with the strategies, database, index and router stubbed (no model call, no server contacted), RUNS_ROOT
# pointed at a scratch folder standing in for findings/runs, and every sink in the scratch directory.
import exp_01_generation as e01  # noqa: E402
from types import SimpleNamespace  # noqa: E402

I20 = e01.DEFAULT_INDEX
paper = {c: f"exp_01__{c}__{I20}" for c in e01.ALL_CONFIGS}
check("B9 F1 exp_01: a smoke's run_id is <index>.smoke for all 7 configs, the paper run's is <index>",
      len(paper) == 7 and all(e01.config_run_id(c, I20) == paper[c]
                              and e01.config_run_id(c, I20, smoke=True) == paper[c] + ".smoke" for c in paper))
check("B9 F1 exp_01 names a smoke run as exp_02 does (<index>.smoke)",
      e01.config_run_id("rlm_10", I20, True).split("__")[2] == e02.run_name("rlm_10", I20, True).split("__")[2]
      == f"{I20}.smoke")
q_all = ex.questions()
wl_smoke = e01.work_list(e01.ALL_CONFIGS, q_all[:3], (1, 2), I20, smoke=True, root=tmp / "e01_none")
wl_paper = e01.work_list(e01.ALL_CONFIGS, q_all[:3], (1, 2), I20, root=tmp / "e01_none")
check("B9 F1 exp_01: every item of a smoke's work list is in a .smoke run (42 items), every paper item in the paper run",
      len(wl_smoke) == 42 and all(i["run_id"] == paper[i["config"]] + ".smoke" for i in wl_smoke)
      and all(i["run_id"] == paper[i["config"]] for i in wl_paper))
check("B9 F1 exp_01: a smoke keeps the paper run's answer keys (it is told apart by its run, as exp_02's)",
      [i["key"] for i in wl_smoke] == [i["key"] for i in wl_paper])

fake_runs = tmp / "e01_runs"          # stands in for findings/runs (RUNS_ROOT)
smoke_root = tmp / "e01_smoke"        # --sink-root
identities, strategy_calls = [], []


async def _fake_config(config_name, question, retriever, collection_name, router, gen_model, user_id, index_name,
                       budget=None):
    strategy_calls.append(config_name)
    gen = e01.GenerationResult(answer="a", latency_s=0.0, llm_calls=0, tokens_used=0, retrieved_passages=0,
                               config=config_name, gen_model=gen_model)
    if budget is not None:
        gen.top_k, gen.matched_budget = budget["top_k"], budget
    return gen


stubs = {"_run_config": _fake_config, "find_admin_user_id": lambda: "u", "check_index_exists": lambda u, i: True,
         "setup_retriever": lambda u, i: (None, "coll", "emb"), "ModelRouter": lambda: None,
         "index_identity": SimpleNamespace(record=lambda sink, *a, **k: identities.append(Path(sink).resolve())),
         "RUNS_ROOT": fake_runs}
saved_e01 = {n: getattr(e01, n) for n in stubs}
for n, v in stubs.items():
    setattr(e01, n, v)


def e01_run(**kw):
    """run_experiment on the stubs; returns the SystemExit it raised, or None."""
    with contextlib.redirect_stdout(io.StringIO()):
        return raises(lambda: asyncio.run(e01.run_experiment(base_url=BASE, index_name=I20, **kw)), SystemExit)


def listing(folder: Path) -> dict:
    return {str(f.relative_to(folder)): f.read_bytes() for f in sorted(folder.rglob("*")) if f.is_file()}


def answers_of(folder: Path) -> list:
    path = folder / e01.ANSWERS
    return [json.loads(ln) for ln in path.read_text().splitlines()] if path.exists() else []


try:
    # a paper run with one stored answer, in the folder that stands in for findings/runs
    paper_sp = fake_runs / paper["single_pass"]
    paper_sp.mkdir(parents=True)
    (paper_sp / e01.ANSWERS).write_text(json.dumps({
        "answer_key": ex.answer_key("single_pass", q_all[0]["id"], 1, index=I20), "generation": {"error": None}}) + "\n")
    before = listing(fake_runs)
    e = e01_run(configs=["single_pass"], max_questions=3, draws=(1,))
    got = answers_of(fake_runs / (paper["single_pass"] + ".smoke"))
    check("B9 F1 exp_01: a smoke beside a paper run with a stored answer starts (it does not read the paper run)",
          e is None and len(got) == 3, repr(e))
    check("B9 F1 exp_01: without --sink-root the smoke writes its 3 answers in RUNS_ROOT/<paper run>.smoke, each line "
          "naming the .smoke run",
          [r["run_id"] for r in got] == [paper["single_pass"] + ".smoke"] * 3
          and [r["question_id"] for r in got] == [q["id"] for q in q_all[:3]])
    after = listing(fake_runs)
    check("B9 F1 exp_01: the paper run's folder is byte for byte as before the smoke (nothing added, nothing changed)",
          {k: v for k, v in after.items() if k.startswith(paper["single_pass"] + "/")} == before
          and all(k.startswith(paper["single_pass"] + ".smoke/") for k in after if k not in before))
    e = e01_run(configs=["single_pass"], max_questions=3, draws=(1,))
    check("B9 F1 exp_01: a second smoke without --resume is refused on its own .smoke answers",
          e is not None and len(answers_of(fake_runs / (paper["single_pass"] + ".smoke"))) == 3, repr(e))
    e = e01_run(configs=["single_pass"], max_questions=None, draws=(1,))
    check("B9 F1 exp_01: the paper run (no --max-questions) reads the paper run, and is refused on its stored answer",
          e is not None and listing(fake_runs) == after, repr(e))

    # --sink-root: every sink of the smoke under it, nothing under RUNS_ROOT
    identities.clear()
    strategy_calls.clear()
    e = e01_run(configs=["single_pass", "rlm_10"], max_questions=2, draws=(1, 2), sink_root=smoke_root)
    sr = {c: answers_of(smoke_root / (paper[c] + ".smoke")) for c in ("single_pass", "rlm_10")}
    check("B9 F1 exp_01: --sink-root writes the smoke's 8 answers in <sink-root>/<paper run>.smoke of each config",
          e is None and [len(v) for v in sr.values()] == [4, 4] and len(strategy_calls) == 8
          and all(r["run_id"] == paper[c] + ".smoke" for c, v in sr.items() for r in v), repr(e))
    check("B9 F1 exp_01: with --sink-root nothing is written under RUNS_ROOT, and every sink is a .smoke run under it",
          listing(fake_runs) == after
          and sorted(p.name for p in smoke_root.iterdir()) == sorted(paper[c] + ".smoke" for c in sr)
          and sorted(identities) == sorted((smoke_root / (paper[c] + ".smoke")).resolve() for c in sr))

    # the matched-budget arm (G2) through exp_01: a paper arm under another plan, then a smoke under a new plan
    plan_file = tmp / "e01_plan.json"
    plan_file.write_text(json.dumps({"kind": "matched_budget_plan",
                                     "questions": {q["id"]: {"top_k": 12} for q in q_all}}))
    paper_mb = fake_runs / paper["matched_budget"]
    paper_mb.mkdir(parents=True)
    (paper_mb / e01.ANSWERS).write_text(json.dumps({
        "answer_key": ex.answer_key("matched_budget", q_all[0]["id"], 1, index=I20),
        "generation": {"error": None, "matched_budget": {"plan_sha256": "a" * 64}}}) + "\n")
    before_mb = listing(fake_runs)
    e = e01_run(configs=["matched_budget"], max_questions=2, draws=(1,), matched_budget_plan=plan_file,
                sink_root=smoke_root)
    mb = answers_of(smoke_root / (paper["matched_budget"] + ".smoke"))
    check("B9 F1 matched budget: a smoke of the arm runs in <sink-root>/exp_01__matched_budget__<index>.smoke, not "
          "checked against or written into the paper arm",
          e is None and len(mb) == 2 and all(r["run_id"] == paper["matched_budget"] + ".smoke"
                                             and r["generation"]["top_k"] == 12 for r in mb)
          and listing(fake_runs) == before_mb, repr(e))
    e = e01_run(configs=["matched_budget"], max_questions=None, draws=(1,), matched_budget_plan=plan_file)
    check("B9 F1 matched budget: the paper arm checks its plan against the paper run (refused: another plan stored)",
          e is not None and "one plan" in str(e) and listing(fake_runs) == before_mb, str(e)[:90])

    # the CLI: --max-questions and --sink-root reach the dry run
    def e01_main(argv):
        saved_argv, sys.argv = sys.argv, ["exp_01_generation.py", *argv]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                e01.main()
        finally:
            sys.argv = saved_argv
        return out.getvalue()
    dry = e01_main(["--dry-run", "--configs", "single_pass", "--max-questions", "2", "--draws", "1", "2",
                    "--sink-root", str(smoke_root)])
    row = next((ln for ln in dry.splitlines() if ln.startswith(paper["single_pass"])), "")
    check("B9 F1 exp_01 CLI: a dry run with --max-questions and --sink-root lists the .smoke run under the sink root, "
          "its 2 answers of draw 1 stored there",
          f"sinks under {smoke_root.resolve()} (smoke test" in dry and row.split()[:4] == [
              paper["single_pass"] + ".smoke", "1", "2", "2"], row)
    dry = e01_main(["--dry-run", "--configs", "single_pass", "--draws", "1"])
    row = next((ln for ln in dry.splitlines() if ln.startswith(paper["single_pass"])), "")
    check("B9 F1 exp_01 CLI: a dry run without --max-questions lists the paper run under RUNS_ROOT, its 1 answer stored",
          f"sinks under {fake_runs.resolve()}" in dry and "smoke" not in dry
          and row.split()[:4] == [paper["single_pass"], "1", "135", "1"], row)

    # Q141 restart (D83): a resume with and without --skip-failed, on a sink whose 4 questions are stored without an
    # error (q0), stored with an error after an earlier error attempt (q1: two lines, both errors), stored with an
    # error (q2), and not stored (q3). --resume runs q1, q2 and q3; --resume --skip-failed runs q3 only and keeps the
    # error lines of q1 and q2 as their answers; --skip-failed without --resume is refused before anything starts
    q_ids = {q["question"]: q["id"] for q in q_all}
    sf_root = tmp / "e01_skip_failed"
    sf_run = sf_root / (paper["rlm_5"] + ".smoke")

    def k(i):
        return ex.answer_key("rlm_5", q_all[i]["id"], 1, index=I20)

    def seed_sink():
        """The sink as described above; returns its bytes."""
        if sf_root.exists():
            shutil.rmtree(sf_root)
        sf_run.mkdir(parents=True)
        lines_ = [{"answer_key": k(0), "generation": {"error": None}},
                  {"answer_key": k(1), "generation": {"error": "RLMRunError: LLM error: a first attempt"}},
                  {"answer_key": k(1), "generation": {"error": "RLMRunError: LLM error: status malformed"}},
                  {"answer_key": k(2), "generation": {"error": "RLMRunError: Maximum turns (5) reached"}}]
        (sf_run / e01.ANSWERS).write_text("".join(json.dumps(r) + "\n" for r in lines_))
        return (sf_run / e01.ANSWERS).read_bytes()

    def q_run(**kw):
        """One start of the 4-question rlm_5 smoke under sf_root: (SystemExit or None, question ids the strategy
        ran, the sink's bytes, the log lines exp_01 wrote)."""
        strategy_calls.clear()
        ran.clear()
        log = io.StringIO()
        h = logging.StreamHandler(log)
        e01.logger.addHandler(h)
        try:
            e = e01_run(configs=["rlm_5"], max_questions=4, draws=(1,), sink_root=sf_root, **kw)
        finally:
            e01.logger.removeHandler(h)
        return e, list(ran), (sf_run / e01.ANSWERS).read_bytes(), log.getvalue()

    def rlog(log):
        return " | ".join(ln for ln in log.splitlines() if ln.startswith(("Resume", "Skipping")))

    ran = []
    _saved_fake = e01._run_config

    async def _fake_tracking(config_name, question, *a, **kw):
        ran.append(q_ids[question])
        return await _saved_fake(config_name, question, *a, **kw)

    e01._run_config = _fake_tracking
    seed_sink()
    wl = {i["key"]: i for i in e01.work_list(["rlm_5"], q_all[:4], (1,), I20, smoke=True, root=sf_root)}
    wl_sf = {i["key"]: i for i in e01.work_list(["rlm_5"], q_all[:4], (1,), I20, smoke=True, root=sf_root,
                                                skip_failed=True)}
    fields = lambda w: [(w[k(i)]["present"], w[k(i)]["failed"], w[k(i)]["skip"], w[k(i)]["retry"])   # noqa: E731
                        for i in range(4)]
    check("Q141 exp_01 work_list: present/failed/skip/retry per key; without skip_failed a failed key is retried, "
          "with it skipped, an unstored key pending either way",
          fields(wl) == [(True, False, True, False), (False, True, False, True), (False, True, False, True),
                         (False, False, False, False)]
          and fields(wl_sf) == [(True, False, True, False), (False, True, True, False), (False, True, True, False),
                                (False, False, False, False)], f"{fields(wl)} | {fields(wl_sf)}")

    before = seed_sink()
    e, got_ran, after_b, log = q_run(resume=True)
    new = [json.loads(ln) for ln in after_b[len(before):].decode().splitlines()]
    check("Q141 exp_01 --resume (no --skip-failed): runs the two failed keys and the unstored one (q1, q2, q3), not "
          "q0; the earlier lines kept byte for byte, one new line per key run",
          e is None and sorted(got_ran) == sorted(q_all[i]["id"] for i in (1, 2, 3)) and after_b.startswith(before)
          and sorted(r["answer_key"] for r in new) == sorted(k(i) for i in (1, 2, 3)), f"{e!r} {got_ran}")
    check("Q141 exp_01 --resume logs that a key stored with an error runs again (2 of them)",
          "Resume: on (a key stored with an error runs again)" in log
          and "Skipping 1 already-stored, 3 remaining (2 stored with an error, run again)" in log, rlog(log))

    before = seed_sink()
    e, got_ran, after_b, log = q_run(resume=True, skip_failed=True)
    new = [json.loads(ln) for ln in after_b[len(before):].decode().splitlines()]
    last = e01.stored_answers(sf_run / e01.ANSWERS)
    check("Q141 exp_01 --resume --skip-failed: runs only the unstored key (q3); the failed keys q1 and q2 are not run "
          "and their error lines stay their answers; the earlier lines kept byte for byte, one new line (q3)",
          e is None and got_ran == [q_all[3]["id"]] and after_b.startswith(before)
          and [r["answer_key"] for r in new] == [k(3)]
          and last[k(1)] == (3, "RLMRunError: LLM error: status malformed")
          and last[k(2)] == (4, "RLMRunError: Maximum turns (5) reached") and last[k(3)][1] is None,
          f"{e!r} {got_ran} {last}")
    check("Q141 exp_01 --resume --skip-failed is recorded in the run log, with the count of failed keys kept",
          "Resume: on, --skip-failed (a key stored with an error is kept, not run again)" in log
          and "Skipping 3 already-stored, 1 remaining (0 stored with an error, run again; 2 stored with an error, "
              "kept: --skip-failed)" in log, rlog(log))
    finished = after_b
    e, got_ran, after_b, log = q_run(resume=True, skip_failed=True)
    check("Q141 exp_01 a second --resume --skip-failed start of the finished sink runs nothing and adds no line",
          e is None and got_ran == [] and after_b == finished and len(after_b.decode().splitlines()) == 5,
          f"{e!r} {got_ran}")

    before = seed_sink()
    e, got_ran, after_b, _ = q_run(skip_failed=True)
    check("Q141 exp_01 skip_failed without resume is refused before anything starts, nothing written",
          e is not None and "pass --resume" in str(e) and got_ran == [] and after_b == before, repr(e))
    (sf_run / e01.ANSWERS).write_text(json.dumps({"answer_key": k(1), "generation": {"error": "x"}}) + "\n")
    before = (sf_run / e01.ANSWERS).read_bytes()
    e, got_ran, after_b, _ = q_run()
    check("Q141 exp_01 without --resume a sink holding only a failed key is still refused (a failed key is stored)",
          e is not None and got_ran == [] and after_b == before, repr(e))

    # the CLI: --skip-failed reaches the dry run (the failed keys counted as stored, none to run again), and a run
    # with --skip-failed but no --resume is refused by the parser
    seed_sink()
    base_argv = ["--dry-run", "--configs", "rlm_5", "--max-questions", "4", "--draws", "1", "--sink-root", str(sf_root)]
    dry_r = e01_main(base_argv)
    dry_s = e01_main(base_argv + ["--resume", "--skip-failed"])
    row_r = next((ln for ln in dry_r.splitlines() if ln.startswith(paper["rlm_5"])), "").split()[:5]
    row_s = next((ln for ln in dry_s.splitlines() if ln.startswith(paper["rlm_5"])), "").split()[:5]
    check("Q141 exp_01 CLI dry run: without --skip-failed 1 stored, 3 pending (2 to run again); with it 3 stored, "
          "1 pending (0 to run again), the 2 kept failed keys named",
          row_r[2:] == ["4", "1", "3"] and "3 pending (2 of them stored with an error, to run again)" in dry_r
          and "--skip-failed" not in dry_r
          and row_s[2:] == ["4", "3", "1"] and "1 pending (0 of them stored with an error, to run again)" in dry_s
          and "--skip-failed: 2 keys whose last line stores an error count as stored and are not run again" in dry_s,
          f"{row_r} {row_s}")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        e = raises(lambda: e01_main(["--configs", "rlm_5", "--draws", "1", "--ollama-url", BASE, "--skip-failed"]),
                   SystemExit)
    check("Q141 exp_01 CLI: --skip-failed without --resume is refused by the parser (exit 2), nothing started",
          e is not None and e.code == 2 and "--skip-failed is a way to resume: pass --resume with it" in err.getvalue()
          and ran == [], err.getvalue()[-120:])
finally:
    for n, v in saved_e01.items():
        setattr(e01, n, v)
check("B9 F1 exp_01: the stubs are restored (RUNS_ROOT is findings/runs again)",
      e01.RUNS_ROOT == ex.RUNS and e01._run_config is saved_e01["_run_config"])

# F48 (audit of 16 Oct): exp_02 refuses to start unless every requested index is present with S66's chunk count
import hashlib, sqlite3  # noqa: E401,E402
exp = e02.expected_chunks()
check("7 F48 expected_chunks(): S66's 12 indexes, exactly exp_02's ALL_INDEXES, 196 to 10,526, 30,337 in all",
      set(exp) == set(e02.ALL_INDEXES) and len(exp) == 12 and exp["exp_v4_s5_n0"] == 196
      and exp["exp_v4_s50_n3"] == 10526 and sum(exp.values()) == 30337, f"{len(exp)}, {sum(exp.values())}")


def fake_chroma(folder: Path, rows: dict) -> Path:
    """A Chroma 1.4 sqlite with the three tables the count reads: per collection a METADATA and a VECTOR segment,
    and rows[name] embeddings in the METADATA one."""
    folder.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(folder / "chroma.sqlite3")
    con.executescript("CREATE TABLE collections (id TEXT, name TEXT); CREATE TABLE segments (id TEXT, type TEXT, "
                      "scope TEXT, collection TEXT); CREATE TABLE embeddings (id INTEGER PRIMARY KEY, segment_id TEXT, "
                      "embedding_id TEXT, seq_id INTEGER, created_at TEXT);")
    for k, (name, n) in enumerate(rows.items()):
        con.execute("INSERT INTO collections VALUES (?, ?)", (f"c{k}", name))
        con.execute("INSERT INTO segments VALUES (?, 'urn:chroma:segment/metadata/sqlite', 'METADATA', ?)",
                    (f"m{k}", f"c{k}"))
        con.execute("INSERT INTO segments VALUES (?, 'urn:chroma:segment/vector/hnsw-local-persisted', 'VECTOR', ?)",
                    (f"v{k}", f"c{k}"))
        con.executemany("INSERT INTO embeddings (segment_id, embedding_id, seq_id) VALUES (?, ?, ?)",
                        [(f"m{k}", f"e{k}_{i}", i) for i in range(n)])
    con.commit()
    con.close()
    return folder / "chroma.sqlite3"


store = fake_chroma(tmp / "f48_chroma", {"coll_s5_n0": 196, "coll_s5_n1": 521, "coll_empty": 0})
store.chmod(0o444)
before = (hashlib.sha256(store.read_bytes()).hexdigest(), store.stat().st_mtime_ns)
counts = e02.chroma_counts(tmp / "f48_chroma")
check("7 F48 chroma_counts(): rows of each collection's METADATA segment, an empty collection 0, from a read-only "
      "file it leaves unchanged", counts == {"coll_s5_n0": 196, "coll_s5_n1": 521, "coll_empty": 0}
      and (hashlib.sha256(store.read_bytes()).hexdigest(), store.stat().st_mtime_ns) == before, json.dumps(counts))
e = raises(lambda: e02.chroma_counts(tmp / "f48_no_store"), SystemExit)
check("7 F48 chroma_counts(): a folder without chroma.sqlite3 is refused, naming the path",
      e is not None and "f48_no_store" in str(e), str(e)[:90])
check("7 F48 index_problems(): every index present with S66's count gives none",
      e02.index_problems(list(exp), {i: (f"coll_{i}", "") for i in exp}, {f"coll_{i}": n for i, n in exp.items()},
                         exp) == [])
probs = e02.index_problems(
    ["exp_v4_s5_n0", "exp_v4_s5_n1", "exp_v4_s10_n0", "exp_v4_s10_n1", "exp_v4_s10_n3", "exp_v4_s99_n0"],
    {"exp_v4_s5_n0": ("coll_s5_n0", ""), "exp_v4_s5_n1": ("coll_s5_n1", ""),
     "exp_v4_s10_n0": (None, "status PENDING, not READY"), "exp_v4_s10_n3": ("coll_gone", "")},
    counts, exp)
check("7 F48 index_problems(): one line per index that stops the run, in request order, each naming its index "
      "(count 521 for 522, not READY, not looked up, collection absent, not in S66)",
      len(probs) == 5 and [p.split(":")[0] for p in probs]
      == ["exp_v4_s5_n1", "exp_v4_s10_n0", "exp_v4_s10_n1", "exp_v4_s10_n3", "exp_v4_s99_n0"]
      and "521 chunks" in probs[0] and "522 expected" in probs[0] and "not READY" in probs[1]
      and "coll_gone" in probs[3] and "S66" in probs[4], " | ".join(probs))

# end to end on the scratch database (DATABASE_URL above): Mentori's user_collections, then run_experiment
from backend.database import engine  # noqa: E402
from backend.retrieval.models import IndexStatus, UserCollection  # noqa: E402
from sqlmodel import Session  # noqa: E402

UserCollection.__table__.create(engine, checkfirst=True)
with Session(engine) as s:
    s.add(UserCollection(id="f48a", user_id="u48", name="exp_v4_s5_n0", status=IndexStatus.READY,
                         vector_db_collection_name="coll_s5_n0"))
    s.add(UserCollection(id="f48b", user_id="u48", name="exp_v4_s5_n1", status=IndexStatus.PROCESSING,
                         vector_db_collection_name="coll_s5_n1"))
    s.commit()
check("7 F48 mentori_collections(): the READY row's collection; not READY and no row each with its reason",
      (lambda m: m["exp_v4_s5_n0"] == ("coll_s5_n0", "") and m["exp_v4_s5_n1"][0] is None
       and "not READY" in m["exp_v4_s5_n1"][1] and m["exp_v4_s10_n0"][0] is None
       and "not in Mentori's database" in m["exp_v4_s10_n0"][1])(
          e02.mentori_collections("u48", ["exp_v4_s5_n0", "exp_v4_s5_n1", "exp_v4_s10_n0"])))
check("7 F48 check_indexes(): an index present with its 196 chunks passes",
      raises(lambda: e02.check_indexes("u48", ["exp_v4_s5_n0"], tmp / "f48_chroma"), BaseException) is None)
e = raises(lambda: e02.check_indexes("u48", ["exp_v4_s5_n0", "exp_v4_s5_n1", "exp_v4_s10_n0"], tmp / "f48_chroma"),
           SystemExit)
check("7 F48 check_indexes(): one index fine and two not stops everything, naming the two (not the fine one)",
      e is not None and "2 of 3" in str(e) and "exp_v4_s5_n1" in str(e) and "exp_v4_s10_n0" in str(e)
      and "exp_v4_s5_n0" not in str(e), str(e)[:120])
saved_admin, saved_chroma, saved_results = e02.find_admin_user_id, settings.CHROMA_PERSIST_DIRECTORY, e02.V4_RESULTS_DIR
e02.find_admin_user_id = lambda: "u48"
settings.CHROMA_PERSIST_DIRECTORY = str(tmp / "f48_chroma")
e02.V4_RESULTS_DIR = tmp / "f48_results"     # the report and the index locks; the sinks go under f48_sinks
e = raises(lambda: asyncio.run(e02.run_experiment(["exp_v4_s5_n0", "exp_v4_s10_n0"], ["single_pass"], BASE,
                                                  sink_root=tmp / "f48_sinks")), SystemExit)
check("7 F48 run_experiment(): a missing index stops the run before anything is written (exit not 0)",
      e is not None and e.code not in (0, None) and "exp_v4_s10_n0" in str(e)
      and not (tmp / "f48_sinks").exists() and not (tmp / "f48_results").exists(), str(e)[:90])
e02.find_admin_user_id = lambda: (_ for _ in ()).throw(AssertionError("the dry run read the database"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    e = raises(lambda: asyncio.run(e02.run_experiment(["exp_v4_s10_n0"], ["single_pass"], None, dry_run=True,
                                                      sink_root=tmp / "f48_sinks")), BaseException)
check("7 F48 --dry-run still prints the work list without reading the database or the store",
      e is None and "exp_v4_s10_n0" in buf.getvalue(), str(e)[:90] if e else "")
e02.find_admin_user_id, settings.CHROMA_PERSIST_DIRECTORY, e02.V4_RESULTS_DIR = saved_admin, saved_chroma, saved_results


# 6. live: the tool server, started from the scratch directory, not the repository
REPO_LOG = ROOT / "backend" / "logs" / "app.log"     # where Mentori's logging writes when the working directory is ROOT
repo_log_before = REPO_LOG.stat().st_size if REPO_LOG.exists() else None
os.chdir(tmp)


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def port_bindable(port: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


async def engine_path(name_args):
    """What Mentori's engine does (engine.py:173-186): sse_client on settings.TOOL_SERVER_URL + '/sse', a session,
    list_tools; then one tool call."""
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    async with sse_client(f"{settings.TOOL_SERVER_URL}/sse") as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            names = sorted(t.name for t in (await session.list_tools()).tools)
            out = await session.call_tool(*name_args)
            return names, out


TOOLS = ["validate_python_syntax"]
live_rid = ex.run_id("check", "tool_server")
live_sink = ex.sink(live_rid, root=runs)
run_ctx = ex.context("check", "tool_server", None, 1, {"coder": "ollama::qwen3-coder:30b"}, base_url=BASE,
                     run=live_rid, sink=live_sink, tools=TOOLS)
item_ctx = ex.context("check", "tool_server", "Q", 1, {"coder": "ollama::qwen3-coder:30b"}, base_url=BASE,
                      run=live_rid, sink=live_sink, tools=TOOLS)
e = raises(lambda: ex.tool_server(item_ctx).__enter__(), ex.ExperimentError)
check("6 an item context is refused before anything starts", isinstance(e, ex.ExperimentError)
      and not (live_sink / "ctx" / "run.json").exists(), str(e)[:90])
env_before, setting_before = os.environ["TOOL_SERVER_URL"], settings.TOOL_SERVER_URL
t0 = time.monotonic()
with ex.tool_server(run_ctx) as url:
    started = time.monotonic() - t0
    base = url.removesuffix("/sse")
    port = int(base.rsplit(":", 1)[1])
    print(f"     served at {url} after {started:.1f} s")
    rj = json.loads((live_sink / "ctx" / "run.json").read_text())
    check("6 ctx/run.json holds the run-level context", rj["run_id"] == live_rid and rj["item_id"] is None
          and rj["tools"] == TOOLS and rj["sink"] == str(live_sink))
    check("6 serves on 127.0.0.1 on a free port other than 8777", url.startswith("http://127.0.0.1:")
          and url.endswith("/sse") and port != 8777 and port_open(port), url)
    check("6 while it serves, its port cannot be bound by another socket", not port_bindable(port))
    check("6 TOOL_SERVER_URL is the server's, in the environment and in backend.config.settings",
          os.environ["TOOL_SERVER_URL"] == base and settings.TOOL_SERVER_URL == base, settings.TOOL_SERVER_URL)
    names, out = asyncio.run(engine_path(("validate_python_syntax", {"code": "x = 1"})))
    text = "".join(getattr(b, "text", "") for b in out.content)
    check("6 the engine's path lists exactly the run's tools and runs one under the run-level context",
          names == TOOLS and not out.isError and "valid" in text.lower(), f"{names}, {text[:50]!r}")
    e = raises(lambda: ex.tool_server(run_ctx).__enter__(), ex.ExperimentError)
    check("6 a second tool server in the same process is refused", isinstance(e, ex.ExperimentError), str(e)[:80])
time.sleep(0.5)
check("6 on exit the server is stopped (port closed)", not port_open(port))
check("6 on exit TOOL_SERVER_URL is as before, in the environment and the setting",
      os.environ["TOOL_SERVER_URL"] == env_before and settings.TOOL_SERVER_URL == setting_before)
check("6 no model call was recorded", not (live_sink / "calls.jsonl").exists())
log = (live_sink / ex.SERVER_LOG).read_text()
check("6 the server's output is in <sink>/tool_server.log", "Starting Mentori MCP Server on 127.0.0.1" in log)
start_line = next((ln for ln in log.splitlines() if "Starting Mentori MCP Server" in ln), "")
check("6 the server serves the socket bound here (the launcher checks it; its line names the port; no bind error)",
      f"127.0.0.1:{port} " in start_line and "address already in use" not in log, start_line[-100:])
app_log = live_sink / "backend" / "logs" / "app.log"
check("6 Mentori's app.log is in <sink>/backend/logs/, not the repository's",
      app_log.is_file() and "Starting Mentori MCP Server" in app_log.read_text()
      and (REPO_LOG.stat().st_size if REPO_LOG.exists() else None) == repo_log_before,
      f"repo app.log {repo_log_before} -> {REPO_LOG.stat().st_size if REPO_LOG.exists() else None} bytes")

run_json = (live_sink / "ctx" / "run.json").read_bytes()
swap = rc.RunContext(run_id=live_rid, arm="tool_server", item_id=None, draw=1, thinking="high", base_url=BASE,
                     sink=live_sink, allowed={"gpt-oss:20b": "generator"},
                     agent_roles={"coder": "ollama::gpt-oss:20b"}, tools=TOOLS)
e = raises(lambda: ex.tool_server(swap).__enter__(), ex.ExperimentError)
check("6 a run-level context of the same run under other models is refused before ctx/run.json is overwritten",
      isinstance(e, ex.ExperimentError) and (live_sink / "ctx" / "run.json").read_bytes() == run_json
      and not ex._serving, str(e)[:100])

with ex.tool_server(run_ctx) as url:
    port2 = int(url.rsplit(":", 1)[1].split("/")[0])
    held = socket.create_connection(("127.0.0.1", port2))
    held.sendall(f"GET /sse HTTP/1.1\r\nHost: 127.0.0.1:{port2}\r\nAccept: text/event-stream\r\n\r\n".encode())
    held.settimeout(10)
    first = b""
    while b"event: endpoint" not in first and len(first) < 65536:
        chunk = held.recv(4096)
        if not chunk:
            break
        first += chunk
    t1 = time.monotonic()
stopped = time.monotonic() - t1
held.close()
print(f"     with an SSE connection open, the server stopped in {stopped:.1f} s")
check("6 a server with an SSE connection open at exit is stopped (port closed)",
      b"event: endpoint" in first and not port_open(port2) and stopped < 2 * ex.STOP_TIMEOUT_S + 5,
      f"{stopped:.1f} s, {first[-60:]!r}")

bad_rid = ex.run_id("check", "tool_server_bad")
bad_sink = ex.sink(bad_rid, root=runs)
bad_ctx = ex.context("check", "tool_server_bad", None, 1, {"coder": "ollama::qwen3-coder:30b"}, base_url=BASE,
                     run=bad_rid, sink=bad_sink, tools=["no_such_tool"])
e = raises(lambda: ex.tool_server(bad_ctx).__enter__(), ex.ExperimentError)
check("6 a server that exits before it serves is refused with its own error",
      isinstance(e, ex.ExperimentError) and "exited with code" in str(e) and "no_such_tool" in str(e),
      str(e).splitlines()[0][:100] if e else "")
check("6 after the failed start the setting is unchanged and a new server may start",
      settings.TOOL_SERVER_URL == setting_before and not ex._serving)

# Q108 (D78): the gate's snapshot names each path added, removed or changed, and ignores what was there before
snap = tmp / "snap"
(snap / "run_a").mkdir(parents=True)
(snap / "run_a" / "answers.json").write_text("[]")
(snap / "run_a" / "calls.jsonl").write_text("{}\n")
(snap / "old.txt").write_text("x")
s0 = runs_snapshot.take(snap)
check("Q108 an unchanged folder gives no difference (what was there before is ignored)",
      runs_snapshot.diff(s0, runs_snapshot.take(snap)) == [] and s0["run_a"] == "dir"
      and len(s0["old.txt"]) == 64, s0)
(snap / "run_a" / "calls.jsonl").write_text("{}\n{}\n")
(snap / "old.txt").unlink()
(snap / "run_b").mkdir()
(snap / "run_b" / "answers.json").write_text("[]")
d108 = runs_snapshot.diff(s0, runs_snapshot.take(snap))
check("Q108 an added, a removed and a rewritten file are each named",
      d108 == ["removed old.txt", "changed run_a/calls.jsonl", "added run_b", "added run_b/answers.json"], d108)
check("Q108 a folder that does not exist is the empty snapshot", runs_snapshot.take(tmp / "no_such") == {})

d_runs = runs_snapshot.diff(RUNS_BEFORE, runs_snapshot.take(ex.RUNS))
check("nothing was written under the repository's findings/runs (sha256 of every path, before and after)",
      ex.RUNS == ROOT / "findings" / "runs" and not d_runs, "; ".join(d_runs))
print(f"scratch in {tmp}")
print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
