#!/usr/bin/env python3
"""Offline checks of K1's split of Figure 5's scoring (D83, Q142): the assignment (scripts/S451_k1_assign.py,
experiments/scorers/assignment.py), RAGChecker's --run with --assignment/--machine/--stop-on-failed/--dry-run
(experiments/scorers/ragchecker_run.py) and RAGAS's K1 run mode (scripts/S357_ragas.py --run). No model call, no
server contact: RAGChecker and RAGAS are replaced by stubs, every fixture is a temporary directory.

D86 (two stages, three machines): the staged assignment recomputed from the rule's words (stage draw, balance, sizes,
seed, tampering), S451 gate (G1's draw 1 final: the Q151 rerun ended after it started), select() by stage, both
scorers' k1_stage in rows, call records and headers, and the three launchers end to end against stubs (stage 1 then
stage 2 without stopping, both stages' dry runs, the G1 gate, the machine refusals, Studio port 11441).

Since the K1 review of 17 October:
  F2  an embedding call that fails goes through the real path (S357 lock_client's transport, experiments/runner/
      proxy.py, ollama_client.embed) to a stub Ollama on 127.0.0.1 (a free port): an HTTP 5xx, a dropped connection
      or a server-check refusal stops RAGAS --run with exit 3 and writes no row; an HTTP 4xx (the server refused the
      request) is the metric's error on a written row, recorded as before. A mutant with the old status (always 400)
      writes the row, so the case guards the fix.
  F1  experiments/runner/server_users.py, the K1 launchers' busy guard, on canned /api/ps, connection, process and
      server-log listings: what makes the server busy, and the exact proof that a loaded devstral or bge-m3 is the
      launcher's own (every model request in the server's log since its last fresh load is one of its own); the
      fresh load's request count, from the real job.py fresh_load against a stub Ollama on a free port.
  F2  the ledger is per server: one for 11434 proves nothing on 11499.
  F3  both committed launchers (run_k1_studio.sh, run_k1_beelink.sh, k1_lib.sh) run end to end with every external
      command a stub: the busy check before each fresh load, the ledger, RAGAS's after-first-call only after a chat
      and an embedding call, with --also the encoder.
  F4  a failed after-first-call stops this launcher's scorer by PID only.
  D1  (D86 review, second round) stage 1 is the first D86 file's (pinned, STAGE_1_D86); stage 2 is the greedy deal
      recomputed here from the rule's words, its ends within the greedy's guarantee (the largest stage 2 question on
      its machine), S451's reported ends equal to these; the first form's split ends further apart (mutant).

Helpers (Valerio, 17 October; findings/recompute/K1/README.md "Helping K1"): workers, the amendment chain, fences,
moves, abandons, releases and suggest, numbered as the design's tests 1 to 15: the committed assignment read exactly as
the K1 commit's code (c7ad841) reads it, for every machine and stage, with an empty chain; signatures; random moves;
what counts as begun; the fence's, the target's and the stage 1 rule's refusals; the lock; an end-to-end move with both
scorers' real run mode against stubs and collect(); the pin; machine and worker in every record; the launchers with a
worker (port, clone, tracked files, fence, JOB_PATTERN); suggest; the prefix hash. The two reviews' fixes, 16 and 17:
amendments.json put back after a release (fence, launcher lookup, scorers refuse "rolled-back"); a fence on a clone
with a modified tracked file; a scorer selecting by machine for a machine a move names; k1_procs.py's match on the
Beelink's real process lines and its stop of real processes; a later LOCK.toml (S451 check passes, S451 worker refuses).

    PYTHONHASHSEED=0 uv run python experiments/scorers/check_k1.py
"""

from __future__ import annotations

import asyncio
import contextlib
import copy
import importlib
import io
import json
import shutil
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import index_identity as ii  # noqa: E402
from experiments.scorers import assignment as A  # noqa: E402
from experiments.scorers import records as R  # noqa: E402
from experiments.scorers.check_records import CHUNKS, INDEX, exp01_line, make_store, qids, write_jsonl  # noqa: E402

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def raises(fn, exc=Exception):
    try:
        fn()
    except exc as e:                                        # noqa: BLE001
        return e
    return None


def signed(asg: dict) -> dict:
    asg = {k: asg[k] for k in A.SIGNED + A.STAGED if k in asg}
    asg["assignment_sha256"] = A.sha256(A.canonical(asg))
    return asg


def write_asg(path: Path, asg: dict) -> Path:
    path.write_text(json.dumps(asg))
    return path


def check_assignment(tmp: Path) -> None:
    """D86: the staged file of S451 (stage draw, machines, sizes, seed), recomputed here from the key and the rule's
    words, not only through S451's own functions."""
    import hashlib
    import S451_k1_assign as S451
    committed = A.load(S451.OUT)
    sizes = committed["stage_sizes"]
    inputs = committed["stage_2_inputs"]
    asg = S451.compute(sizes, inputs)
    check("S451 reproduces the committed assignment (assignment_sha256 and every signed field, seed and stage sizes)",
          committed["assignment_sha256"] == asg["assignment_sha256"]
          and all(committed[k] == asg[k] for k in A.SIGNED + A.STAGED), asg["assignment_sha256"][:12])
    check("the stage draw is reproducible: computed twice, the same bytes",
          A.canonical(S451.compute(sizes, inputs)) == A.canonical(asg))
    qs = [q for q in S451.ex.questions() if R.applies("ragchecker", q["id"])]
    ids = [q["id"] for q in asg["questions"]]
    check("96 questions, exactly the ones Rule 8 makes applicable, in the key's order; the 39 not scored with a reason",
          ids == [q["id"] for q in qs] and len(ids) == len(set(ids)) == 96 and len(asg["not_scored"]) == 39
          and all(q["reason"] for q in asg["not_scored"]) and not set(ids) & {q["id"] for q in asg["not_scored"]})
    cell = {}
    for q in asg["questions"]:
        cell[(q["stage"], q["machine"])] = cell.get((q["stage"], q["machine"]), 0) + 1
    check("every question in exactly one stage (1 or 2) and one machine of the three; the counts per (stage, machine) "
          "are the signed stage sizes", all(q["stage"] in (1, 2) and q["machine"] in ("studio", "beelink", "laptop")
                                            for q in asg["questions"])
          and asg["machines"] == ["studio", "beelink", "laptop"]
          and all(cell.get((int(k), m), 0) == n for k, v in sizes.items() for m, n in v.items())
          and sum(cell.values()) == 96, str(sizes))
    # the stage draw by the rule's words: per category, the quota (largest remainder) of lowest sha256(seed|id)
    n1 = sum(sizes["1"].values())
    cats = list(dict.fromkeys(q["category"] for q in qs))
    size = {c: sum(q["category"] == c for q in qs) for c in cats}
    exact = {c: n1 * size[c] / 96 for c in cats}
    quota = {c: int(exact[c]) for c in cats}
    for c in sorted(cats, key=lambda c: (-(exact[c] - quota[c]), cats.index(c)))[: n1 - sum(quota.values())]:
        quota[c] += 1
    want1 = set()
    for c in cats:
        r = sorted((q["id"] for q in qs if q["category"] == c),
                   key=lambda i: hashlib.sha256(f"{asg['seed']}|{i}".encode()).hexdigest())
        want1 |= set(r[: quota[c]])
    check("stage 1 is, in every category, its proportional quota of the lowest sha256(seed|id) ranks (recomputed "
          "here from the rule's words)", {q["id"] for q in asg["questions"] if q["stage"] == 1} == want1,
          str(quota))
    worst = 0.0
    for c in cats:
        in_c = [q for q in asg["questions"] if q["category"] == c and q["stage"] == 1]
        for m in asg["machines"]:
            worst = max(worst, abs(sum(q["machine"] == m for q in in_c) - len(in_c) * sizes["1"][m] / n1))
    check("balance: every (stage 1, category, machine) count within one question of its proportion of the stage's "
          "category", worst <= 1, f"largest gap {worst:.2f}")
    check_deal(tmp, committed, asg, qs)
    other = S451.compute(sizes, inputs, seed="another seed")
    split = {"1": {"studio": sizes["1"]["studio"] + sizes["1"]["laptop"], "beelink": sizes["1"]["beelink"],
                   "laptop": 0}}
    resplit = S451.compute(split, inputs)
    st = lambda a: {q["id"] for q in a["questions"] if q["stage"] == 1}                    # noqa: E731
    check("the seed decides the draw (another seed, another stage 1 of the same size and quotas); the machines' "
          "split does not (the same stage 1 when the stage 1 counts move between machines)",
          st(other) != st(asg) and len(st(other)) == n1 and st(resplit) == st(asg))
    e = raises(lambda: S451.compute({"1": {**sizes["1"], "studio": 97}}, inputs), SystemExit)
    check("compute() refuses stage 1 sizes that are not a part of the 96", e is not None and "not a part" in str(e))
    short = copy.deepcopy(inputs)
    del short["question_cost_h"]["laptop"][next(q["id"] for q in asg["questions"] if q["stage"] == 2)]
    e = raises(lambda: S451.compute(sizes, short), SystemExit)
    check("compute() refuses deal inputs without a (machine, question) cost", e is not None and "lack 1" in str(e))
    t = json.loads(S451.OUT.read_text())
    t["questions"][0]["machine"] = "laptop" if t["questions"][0]["machine"] != "laptop" else "studio"
    e = raises(lambda: A.load(write_asg(tmp / "tampered.json", t)), A.AssignmentError)
    check("load() refuses a file with one machine changed by hand", e is not None and "recompute" in str(e))
    t = json.loads(S451.OUT.read_text())
    t["questions"][0]["stage"] = 3 - t["questions"][0]["stage"]
    e = raises(lambda: A.load(write_asg(tmp / "tampered_stage.json", t)), A.AssignmentError)
    check("load() refuses a file with one stage changed by hand", e is not None and "recompute" in str(e))
    t = json.loads(S451.OUT.read_text())
    t["questions"][0]["stage"] = 3 - t["questions"][0]["stage"]
    e = raises(lambda: A.load(write_asg(tmp / "resigned_stage.json", signed(t))), A.AssignmentError)
    check("load() refuses a re-signed file whose questions per (stage, machine) differ from stage_sizes",
          e is not None and "do not match stage_sizes" in str(e), str(e))
    t = json.loads(S451.OUT.read_text())
    del t["questions"][0]["stage"]
    e = raises(lambda: A.load(write_asg(tmp / "nostage.json", signed(t))), A.AssignmentError)
    check("load() refuses a staged file with a question without a stage", e is not None and "no stage" in str(e))
    t = json.loads(S451.OUT.read_text())
    t["rule"] += " "
    e = raises(lambda: A.load(write_asg(tmp / "tampered_rule.json", t)), A.AssignmentError)
    check("load() refuses a file whose rule text changed", e is not None and "rule_sha256" in str(e))
    real = S451.OUT.read_bytes()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = S451.cmd_write(types.SimpleNamespace(sizing=str(S451.SIZING)))
    check("S451 write (from the committed sizing.json) leaves an equal file unchanged",
          rc == 0 and S451.OUT.read_bytes() == real and "unchanged" in buf.getvalue(),
          buf.getvalue()[-200:].replace("\n", " | "))
    sz = json.loads(S451.SIZING.read_text())
    check("sizing.json and the assignment agree: its stage sizes and deal inputs are the signed ones, stage 1 its "
          "stage_1_size", sz["stage_sizes"] == sizes and sz["stage_1_size"] == n1 and sz["stage_2_inputs"] == inputs)
    old = tmp / "sizing_before_deal.json"
    old.write_text(json.dumps({k: v for k, v in sz.items() if k != "stage_2_inputs"}))
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = S451.cmd_write(types.SimpleNamespace(sizing=str(old)))
    check("S451 write refuses a sizing without the deal's inputs (D86's first form)",
          rc == 1 and "no stage_2_inputs" in buf.getvalue() and S451.OUT.read_bytes() == real)
    check_gate(tmp)


# D86 review D1 (17 October): the stage 1 of D86's first file (assignment d2d2c2e637d1, written 17 October 15:30), kept
# when stage 2 was dealt again: sha256 of its 25 "<question id>|<machine>" lines, sorted, joined by newlines.
STAGE_1_D86 = (25, "a86c7f874afa4ae53f2c8b6b1a29d6d23bf942d9c344adddf2e9bd579ccd8432")


def check_deal(tmp: Path, committed: dict, asg: dict, qs: list) -> None:
    """D86 review D1: stage 1 unchanged; stage 2 dealt by the greedy (recomputed here from the rule's words, not
    through S451's deal_stage_2), and its ends within the spread the greedy guarantees."""
    import datetime as dt
    import hashlib
    import S451_k1_assign as S451
    one = sorted(f"{q['id']}|{q['machine']}" for q in committed["questions"] if q["stage"] == 1)
    check("D1: stage 1 is D86's first file's, unchanged (the same 25 questions on the same machines)",
          (len(one), hashlib.sha256("\n".join(one).encode()).hexdigest()) == STAGE_1_D86,
          f"{len(one)} questions, {hashlib.sha256(chr(10).join(one).encode()).hexdigest()[:12]}")
    inp = committed["stage_2_inputs"]
    cost, ms = inp["question_cost_h"], committed["machines"]
    t = {m: dt.datetime.fromisoformat(inp["starts"][m]) for m in ms}
    end = {m: (t[m] - min(t.values())).total_seconds() / 3600 for m in ms}
    for q in committed["questions"]:
        if q["stage"] == 1:
            end[q["machine"]] += cost[q["machine"]][q["id"]]
    key = [q["id"] for q in qs]
    two = [q["id"] for q in committed["questions"] if q["stage"] == 2]
    want = {}
    for i in sorted(two, key=lambda i: (-max(cost[m][i] for m in ms), key.index(i))):
        m = min(ms, key=lambda m: (end[m], ms.index(m)))
        want[i] = m
        end[m] += cost[m][i]
    got = {q["id"]: q["machine"] for q in committed["questions"] if q["stage"] == 2}
    check("D1: stage 2 is the greedy's deal, recomputed here (largest question first, to the machine whose projected "
          "end, start plus its hours so far, is then the earliest), one machine per question",
          got == want and len(two) == len(set(two)) == 71, f"{sum(got[i] != want[i] for i in two)} differ")
    spread = max(end.values()) - min(end.values())
    bound = max(cost[got[i]][i] for i in two)
    largest = max(cost[m][i] for m in ms for i in two)
    check("D1: the stage 2 ends are within the spread the greedy guarantees (at most the largest stage 2 question on "
          "the machine it went to, itself at most the largest single question cost)",
          spread <= bound + 1e-9 and bound <= largest, f"{spread:.1f} h apart, bound {bound:.1f} h, largest {largest:.1f} h")
    e = S451.ends(committed)
    check("D1: S451's reported ends (S451 check, write, size) are the ends computed here",
          all(abs((e[m][2]["end"] - min(t.values())).total_seconds() / 3600 - end[m]) < 1e-6 for m in ms),
          ", ".join(f"{m} {S451.local(e[m][2]['end'])}" for m in ms))
    # the first form (D86's first file): stage 2 split by questions per hour, then dealt by category share
    cats = list(dict.fromkeys(q["category"] for q in qs))
    rate = {m: len(cost[m]) / sum(cost[m].values()) for m in ms}
    first = S451.deal(sorted((q for q in qs if q["id"] in got), key=lambda q: cats.index(q["category"])),
                      S451.apportion(len(two), rate, ms))
    end0 = {m: (t[m] - min(t.values())).total_seconds() / 3600 for m in ms}
    for q in committed["questions"]:
        end0[q["machine"] if q["stage"] == 1 else first[q["id"]]] += cost[q["machine"] if q["stage"] == 1
                                                                             else first[q["id"]]][q["id"]]
    spread0 = max(end0.values()) - min(end0.values())
    check("D1 mutant: the first form's split (questions per hour) on the same inputs ends further apart than the deal",
          spread < spread0, f"first form {spread0:.1f} h apart, the deal {spread:.1f} h")
    t2 = json.loads(S451.OUT.read_text())
    m0 = next(m for m in ms)
    q0 = next(iter(t2["stage_2_inputs"]["question_cost_h"][m0]))
    t2["stage_2_inputs"]["question_cost_h"][m0][q0] += 1.0
    e2 = raises(lambda: A.load(write_asg(tmp / "tampered_costs.json", t2)), A.AssignmentError)
    check("D1: load() refuses a file whose deal inputs (one question's hours) changed by hand",
          e2 is not None and "recompute" in str(e2))


def check_gate(tmp: Path) -> None:
    """S451 gate (D86): G1's draw 1 is final only when the Q151 rerun's multi-hop run ended after it started."""
    import S451_k1_assign as S451
    t0 = "2026-10-17T12:48:20Z"

    def records(name, mh_end="2026-10-17T15:40:00Z", mh_rc=0, mh_start=t0, layout="copy", other_rc=0):
        d = tmp / f"gate_{name}"
        d.mkdir()
        rr = {"q151_rerun": t0, "to_run": {"d1": 6}}
        if layout == "copy":
            (d / "q151_rerun.json").write_text(json.dumps(rr))
        elif layout == "live":
            (d / "q151_before_rerun_20261017T124813Z").mkdir()
            (d / "q151_before_rerun_20261017T124813Z" / "rerun.json").write_text(json.dumps(rr))
        for c in S451.CONFIGS:
            s, e, rc = ("2026-10-17T01:31:00Z", "2026-10-17T14:44:00Z", other_rc)
            if c == "multi_hop":
                s, e, rc = mh_start, mh_end, mh_rc
            (d / f"g1_{c}.start.json").write_text(json.dumps({"job": f"g1_{c}", "start": s}))
            (d / f"g1_{c}.end.json").write_text(json.dumps({"job": f"g1_{c}", "end": e, "rc": rc}))
        return d
    ok, live = S451.gate(records("ok")), S451.gate(records("live", layout="live"))
    check("gate: every config ended rc 0 after its start, the multi-hop rerun started and ended after the Q151 "
          "record (the copy's q151_rerun.json, and the Studio's q151_before_rerun_*/rerun.json): passed",
          ok == [] and live == [], str(ok + live))
    running = S451.gate(records("running", mh_end="2026-10-17T02:23:57Z"))      # the Studio at 15:08 on 17 October
    check("gate: the multi-hop end record older than the rerun's start (the rerun still running, the end record of "
          "02:23 its first run's): refused", len(running) == 2 and "running" in running[0], str(running))
    check("gate: the rerun ended with rc 1: refused", S451.gate(records("rc1", mh_rc=1)) != [])
    check("gate: an end record before the rerun's own start record (a start record not rewritten): refused",
          S451.gate(records("oldstart", mh_start="2026-10-17T01:31:00Z", mh_end="2026-10-17T02:23:57Z")) != [])
    check("gate: no Q151 rerun record: refused", "no Q151 rerun record" in " ".join(S451.gate(records("none", layout="none"))))
    check("gate: another config's end rc 1 (a strategy not ended cleanly): refused",
          S451.gate(records("other", other_rc=1)) != [])
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = S451.cmd_gate(types.SimpleNamespace(records=str(tmp / "gate_running")))
    check("gate command: exit 1 and 'G1 GATE REFUSED' when refused (what k1_lib.sh and copy_k1_inputs.sh read)",
          rc == 1 and buf.getvalue().startswith("G1 GATE REFUSED"))


def fixture(tmp: Path, Q: dict) -> tuple:
    """Two runs (single_pass, multi_hop), draws 1 and 2, the four questions; an assignment over them."""
    store = tmp / "chroma"
    make_store(store, {"coll_s20": CHUNKS})
    sinks = []
    qa, qf, qn = Q["answerable"], Q["false_premise"], Q["not_answerable"]
    from experiments.runner import experiment as ex
    qb = next(q["id"] for q in ex.questions() if R.group_of(q["id"]) == "answerable" and q["id"] != qa)
    for cfg in ("single_pass", "multi_hop"):
        sink = tmp / "runs" / f"exp_01__{cfg}__{INDEX}"
        ii.record(sink, INDEX, "coll_s20", store=store, script="check")
        lines = []
        for d in (1, 2):
            for q in (qa, qb, qf, qn):
                lines.append(exp01_line(q, d, f"answer {cfg} {q} {d}", None, ["id-b", "id-a"], config=cfg))
        write_jsonl(sink / "answers.jsonl", lines)
        sinks.append(sink)
    asg = signed({"rule": "fixture", "rule_sha256": A.sha256("fixture"), "draws": [1],
                  "configs": ["single_pass", "multi_hop"], "machines": ["studio", "beelink"],
                  "questions": [{"id": qa, "machine": "studio"}, {"id": qb, "machine": "beelink"},
                                {"id": qf, "machine": "studio"}],
                  "not_scored": [{"id": qn, "reason": "not applicable (Rule 8)"}]})
    return sinks, write_asg(tmp / "asg.json", asg), (qa, qb, qf, qn)


def check_select(tmp: Path, sinks: list, asg_path: Path, qs: tuple) -> None:
    qa, qb, qf, qn = qs
    asg = A.load(asg_path)
    items = [x for s in sinks for x in R.read_run(s)]
    sel = A.select(items, asg, "studio")
    check("select(): the machine's questions, draw 1 only, question by question, configs in the file's order",
          [(x["question_id"], x["config"], x["draw"]) for x in sel]
          == [(qa, "single_pass", 1), (qa, "multi_hop", 1), (qf, "single_pass", 1), (qf, "multi_hop", 1)])
    check("select(): the other machine gets the rest; a not_scored question goes to neither",
          [(x["question_id"], x["config"]) for x in A.select(items, asg, "beelink")]
          == [(qb, "single_pass"), (qb, "multi_hop")])
    e = raises(lambda: A.select(items, asg, "laptop"), A.AssignmentError)
    check("select(): a machine the file does not name is refused", e is not None)
    e = raises(lambda: A.select([x for x in items if x["config"] == "single_pass"], asg, "studio"), A.AssignmentError)
    check("select(): a missing config (one run not passed) is refused", e is not None and "without an answer" in str(e))
    extra = copy.deepcopy(items[0])
    extra["config"] = "rlm_5"
    e = raises(lambda: A.select(items + [extra], asg, "studio"), A.AssignmentError)
    check("select(): an answer of a config the file does not name is refused", e is not None and "rlm_5" in str(e))
    stray = copy.deepcopy(items[0])
    stray["question_id"] = "SOMETHING_ELSE"
    e = raises(lambda: A.select(items + [stray], asg, "studio"), A.AssignmentError)
    check("select(): a question the file names nowhere is refused", e is not None and "not in the assignment" in str(e))
    e = raises(lambda: A.select(items + [copy.deepcopy(items[0])], asg, "studio"), A.AssignmentError)
    check("select(): a doubled answer is refused", e is not None and "with two" in str(e))


def fake_ragchecker(fail_on: str | None, evaluated: list):
    class Res:
        def __init__(self, d):
            self.results = [types.SimpleNamespace(**d["results"][0])]

        @classmethod
        def from_dict(cls, d):
            return cls(d)

    class Evaluator:
        def evaluate(self, res, metrics):
            y = res.results[0]
            evaluated.append(y.query_id)
            if fail_on and fail_on in y.query_id:
                raise RuntimeError("model call stalled: no token for 600 s")
            y.response_claims, y.gt_answer_claims = [["s", "p", "o"]], [["s", "p", "o"]]
            y.answer2response = y.response2answer = y.retrieved2response = y.retrieved2answer = []
            y.metrics = {"overall_metrics": {"precision": 100.0}}

    fake = types.ModuleType("ragchecker")
    fake.RAGResults = Res
    fake.metrics = types.ModuleType("ragchecker.metrics")
    fake.metrics.all_metrics = ["all"]
    return fake, Evaluator


@contextlib.contextmanager
def modules(mods: dict):
    saved = {m: sys.modules.get(m) for m in mods}
    sys.modules.update(mods)
    try:
        yield
    finally:
        for m, v in saved.items():
            if v is None:
                sys.modules.pop(m, None)
            else:
                sys.modules[m] = v


def check_ragchecker(tmp: Path, sinks: list, asg_path: Path, qs: tuple) -> None:
    qa, qb, qf, qn = qs
    evaluated: list = []
    fake, Evaluator = fake_ragchecker(None, evaluated)
    with modules({"ragchecker": fake, "ragchecker.metrics": fake.metrics}):
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        gt = tmp / "gt.json"
        gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": "the reference"} for q in qs]}))
        refs = {q: "the reference" for q in qs}
        lock = types.SimpleNamespace(sha256="LOCKSHA")
        call = types.SimpleNamespace(digest="d", options={}, fields=[])

        def ns(out, **kw):
            base = dict(run=list(sinks), store=None, rows=None, limit=None, gt=gt, out=out, base="none", order="claims",
                        assignment=asg_path, machine="studio", stop_on_failed=True, dry_run=False)
            return types.SimpleNamespace(**{**base, **kw})

        out = tmp / "rc_studio"
        out.mkdir()
        cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0}
        with contextlib.redirect_stdout(io.StringIO()):
            rc = rr.score_run(ns(out), Evaluator(), cur, lock, "m", call, False, out / "ragchecker.jsonl", refs)
        rows = [json.loads(ln) for ln in (out / "ragchecker.jsonl").read_text().splitlines()]
        head = json.loads((out / "ragchecker_headers.jsonl").read_text().splitlines()[-1])
        check("ragchecker K1: two runs in one process, the studio's answers question by question, configs in order",
              rc == 0 and [(r["question_id"], r["config"]) for r in rows]
              == [(qa, "single_pass"), (qa, "multi_hop"), (qf, "single_pass"), (qf, "multi_hop")])
        check("ragchecker K1: every row carries the machine; the header the assignment, its sha256 fields and machine",
              all(r.get("machine") == "studio" for r in rows) and head["machine"] == "studio"
              and head["assignment_sha256"] == A.load(asg_path)["assignment_sha256"]
              and head["assignment_file_sha256"] == A.sha256(asg_path.read_bytes())
              and head["_provenance"]["inputs"][:2] == [str(s) for s in sinks])
        n = len(evaluated)
        with contextlib.redirect_stdout(io.StringIO()):
            rr.score_run(ns(out), Evaluator(), cur, lock, "m", call, False, out / "ragchecker.jsonl", refs)
        check("ragchecker K1: a resume over the same assignment makes no call", len(evaluated) == n)
        calls_log = tmp / "calls.jsonl"
        llm = rr.make_llm("none", call, "claims", calls_log, {"key": "k", "n": 0, "checks": 0, "ambiguous": 0,
                                                             "batch": 0, "machine": "beelink"})
        saved = rr.chat
        rr.chat = lambda base, c, msgs: {"status": "ok", "text": "Entailment", "error": None, "stop_reason": "stop"}
        try:
            llm(["### Claim: x " + rr.CHECK_SIGNATURE])
        finally:
            rr.chat = saved
        check("ragchecker K1: a call record carries the machine when the process has one",
              json.loads(calls_log.read_text())["machine"] == "beelink")

        ev2: list = []
        fake2, Evaluator2 = fake_ragchecker(f"|{qa}|", ev2)
        sys.modules["ragchecker"], sys.modules["ragchecker.metrics"] = fake2, fake2.metrics
        out2 = tmp / "rc_stop"
        out2.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = rr.score_run(ns(out2), Evaluator2(), dict(cur), lock, "m", call, False, out2 / "ragchecker.jsonl", refs)
        rows = [json.loads(ln) for ln in (out2 / "ragchecker.jsonl").read_text().splitlines()]
        check("ragchecker --stop-on-failed: exit 4 after the first failed answer, nothing scored after it",
              rc == 4 and len(rows) == 1 and rows[0]["status"] == "failed" and len(ev2) == 1)
        length_row = {**rows[0], "error": "RuntimeError: model call length: length"}
        key = f"{length_row['run_id']}|{length_row['answer_key']}"
        retried = {}
        for name, prior in (("twice", [length_row, length_row]), ("once", [length_row]),
                            ("stall_twice", [rows[0], rows[0]]), ("length_then_stall", [length_row, rows[0]])):
            o = tmp / f"rc_d110_{name}"
            o.mkdir()
            (o / "ragchecker.jsonl").write_text("".join(json.dumps(r) + "\n" for r in prior))
            ev: list = []
            fk, Ev = fake_ragchecker(None, ev)
            sys.modules["ragchecker"], sys.modules["ragchecker.metrics"] = fk, fk.metrics
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rr.score_run(ns(o), Ev(), dict(cur), lock, "m", call, False, o / "ragchecker.jsonl", refs)
            last = {}
            for r in map(json.loads, (o / "ragchecker.jsonl").read_text().splitlines()):
                last[(r["run_id"], r["answer_key"])] = r["status"]
            retried[name] = (key in ev, last[(length_row["run_id"], length_row["answer_key"])], len(ev))
        check("D110: an answer failed twice by a length stop is not retried and its failed row stays latest; once, or "
              "twice by another failure, or a length stop then another failure, it is retried; the rest are scored",
              retried["twice"] == (False, "failed", 3) and retried["once"] == (True, "ok", 4)
              and retried["stall_twice"] == (True, "ok", 4) and retried["length_then_stall"] == (True, "ok", 4),
              str(retried))
        out3 = tmp / "rc_plain"
        out3.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            rr.score_run(types.SimpleNamespace(run=sinks[0], store=None, rows=None, limit=None, gt=gt, out=out3,
                                               base="none", order="claims"),
                         Evaluator(), dict(cur), lock, "m", call, False, out3 / "ragchecker.jsonl", refs)
        rows = [json.loads(ln) for ln in (out3 / "ragchecker.jsonl").read_text().splitlines()]
        head = json.loads((out3 / "ragchecker_headers.jsonl").read_text())
        check("ragchecker without the K1 options: one run, every answer, no machine field, header without assignment",
              len(rows) == 8 and not any("machine" in r for r in rows) and "assignment" not in head
              and head["_provenance"]["inputs"][0] == str(sinks[0]))
        bad = [dict(assignment=asg_path, machine=None), dict(rows="0:2"), dict(run=None)]
        refused = []
        for kw in bad:
            a = ns(out, **kw)
            if kw.get("run", 1) is None:
                a.arm, a.dry_run = Path("x"), True
            refused.append(raises(lambda: rr.k1_args(a), SystemExit) is not None)
        check("ragchecker K1 options: --assignment without --machine, --rows with several runs, --dry-run without "
              "--run are refused", all(refused), str(refused))


def check_ragas(tmp: Path, sinks: list, asg_path: Path, qs: tuple) -> None:
    qa, qb, qf, qn = qs
    S = importlib.import_module("S357_ragas")
    from experiments.runner.lock import load
    lock = load()
    gt = tmp / "gt.json"
    seen: list = []

    async def score_row(row, ref, metrics, sem, transport=None):
        seen.append((row["question_id"], row["config"]))
        names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "factual_correctness")
        lost = ["faithfulness"] if row["question_id"] == qf and row["config"] == "multi_hop" and STOP["on"] else []
        sc = {m: 0.5 for m in names}
        if row["question_id"] == qf and row["config"] == "single_pass":
            sc["context_recall"] = None
        return {"question_id": row["question_id"], "config": row["config"], "scores": sc,
                "errors": {} if sc["context_recall"] is not None else {"context_recall": "ValueError: x"},
                "wall_s": {m: 1.0 for m in names}, "n_contexts": len(row["contexts"]),
                "context_chars": 0, "at": "T", "transport_failures": lost}

    STOP = {"on": False}
    stub = types.SimpleNamespace(call=types.SimpleNamespace(options={"temperature": 0, "num_predict": 16384},
                                                            lock_sha256=lock.sha256, digest="d", fields=[]))
    ragas = types.ModuleType("ragas")
    ragas.__version__ = "stub"
    llms, embs, mets = (types.ModuleType(n) for n in ("ragas.llms", "ragas.embeddings", "ragas.metrics"))
    llms.llm_factory = lambda *a, **k: "llm"
    embs.OpenAIEmbeddings = lambda **k: "emb"
    coll = types.SimpleNamespace(**{n: (lambda **k: n) for n in ("Faithfulness", "AnswerRelevancy",
                                    "ContextPrecisionWithReference", "ContextRecall", "FactualCorrectness")})
    mets.collections = coll
    saved = {k: getattr(S, k) for k in ("score_row", "lock_client", "ollama_show", "ollama_version")}
    S.score_row, S.lock_client = score_row, (lambda m, e, p: (None, stub))
    S.ollama_show, S.ollama_version = (lambda m: {"model": m}), (lambda: "stub")

    def ns(out, **kw):
        base = dict(run=[str(s) for s in sinks], gt=str(gt), store=None, out=str(out), key=None, concurrency=1,
                    assignment=str(asg_path), machine="beelink", limit=None, dry_run=False, llm=None, embedding=None)
        return types.SimpleNamespace(**{**base, **kw})

    try:
        with modules({"ragas": ragas, "ragas.llms": llms, "ragas.embeddings": embs, "ragas.metrics": mets}):
            out = tmp / "ragas_b" / "ragas.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                rc = asyncio.run(S.main_run_async(ns(out)))
            rows = [json.loads(ln) for ln in out.read_text().splitlines()]
            head = json.loads((out.parent / "ragas_headers.jsonl").read_text())
            check("ragas --run K1: the beelink's answers in order, status ok, machine in every row and the header",
                  rc == 0 and [(r["question_id"], r["config"], r["status"], r["machine"]) for r in rows]
                  == [(qb, "single_pass", "ok", "beelink"), (qb, "multi_hop", "ok", "beelink")]
                  and head["machine"] == "beelink" and head["assignment_sha256"] == A.load(asg_path)["assignment_sha256"])
            check("ragas --run rows carry run_id, answer_key, draw, item_sha256 and the lock; Rule 8's check passes",
                  all(r["run_id"] and r["answer_key"] and r["draw"] == 1 and r["item_sha256"]
                      and r["lock_sha256"] == lock.sha256 for r in rows) and R.rule8_violations(rows) == [])
            n = len(seen)
            with contextlib.redirect_stdout(io.StringIO()):
                asyncio.run(S.main_run_async(ns(out)))
            check("ragas --run: a resume makes no call", len(seen) == n)
            STOP["on"] = True
            out2 = tmp / "ragas_s" / "ragas.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                rc = asyncio.run(S.main_run_async(ns(out2, machine="studio")))
            rows = [json.loads(ln) for ln in out2.read_text().splitlines()]
            check("ragas --run: a null metric is ok_with_nulls; a transport failure writes no row and stops (exit 3)",
                  rc == 3 and [(r["question_id"], r["config"], r["status"]) for r in rows]
                  == [(qa, "single_pass", "ok"), (qa, "multi_hop", "ok"), (qf, "single_pass", "ok_with_nulls")])
            STOP["on"] = False
            with contextlib.redirect_stdout(io.StringIO()):
                rc = asyncio.run(S.main_run_async(ns(out2, machine="studio")))
            rows = [json.loads(ln) for ln in out2.read_text().splitlines()]
            check("ragas --run: the next session scores only the answer the failure left", rc == 0 and len(rows) == 4
                  and rows[-1]["question_id"] == qf and rows[-1]["config"] == "multi_hop")
            out3 = tmp / "ragas_d" / "ragas.jsonl"
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                rc = asyncio.run(S.main_run_async(ns(out3, dry_run=True)))
            check("ragas --run --dry-run: the work list, no row, no header, no directory",
                  rc == 0 and not out3.parent.exists() and "DRY RUN" in buf.getvalue())
            refusals = []
            for kw in (dict(concurrency=2), dict(machine=None), dict(key="2.4"), dict(gt=None)):
                with contextlib.redirect_stdout(io.StringIO()):
                    refusals.append(asyncio.run(S.main_run_async(ns(tmp / "ragas_r" / "x.jsonl", **kw))) == 1)
            check("ragas --run refuses --concurrency 2, --assignment without --machine, --key, and no --gt",
                  all(refusals) and not (tmp / "ragas_r").exists(), str(refusals))
            lock_rows = tmp / "ragas_l" / "ragas.jsonl"
            write_jsonl(lock_rows, [{**rows[0], "lock_sha256": "OTHER"}])
            with contextlib.redirect_stdout(io.StringIO()):
                rc = asyncio.run(S.main_run_async(ns(lock_rows, machine="studio")))
            check("ragas --run: an output scored under another lock is refused", rc == 1)
            got: list = []
            px = S.TaggedProxy.__new__(S.TaggedProxy)
            orig = S.Proxy.write
            S.Proxy.write = lambda self, rec: got.append(dict(rec))
            try:
                S.RUN_MACHINE = "studio"
                px.write({"endpoint": "chat"})
                S.RUN_MACHINE = None
                px.write({"endpoint": "chat"})
            finally:
                S.Proxy.write = orig
            check("ragas --run: a call record carries the machine in K1, and no machine field otherwise",
                  got[0].get("machine") == "studio" and "machine" not in got[1])
    finally:
        S.RUN_MACHINE = S.RUN_STAGE = None
        for k, v in saved.items():
            setattr(S, k, v)


def check_staged(tmp: Path, sinks: list, qs: tuple) -> None:
    """D86: select() by stage and both scorers' k1_stage (rows, call records, headers), on a staged fixture over three
    machines: qf stage 1 studio, qb stage 1 laptop, qa stage 2 studio."""
    qa, qb, qf, qn = qs
    asg_path = write_asg(tmp / "asg_staged.json", signed({
        "rule": "fixture", "rule_sha256": A.sha256("fixture"), "draws": [1], "configs": ["single_pass", "multi_hop"],
        "machines": ["studio", "beelink", "laptop"], "seed": "fixture seed",
        "stage_sizes": {"1": {"studio": 1, "beelink": 0, "laptop": 1}, "2": {"studio": 1, "beelink": 0, "laptop": 0}},
        "questions": [{"id": qa, "machine": "studio", "stage": 2}, {"id": qb, "machine": "laptop", "stage": 1},
                      {"id": qf, "machine": "studio", "stage": 1}],
        "not_scored": [{"id": qn, "reason": "not applicable (Rule 8)"}]}))
    asg = A.load(asg_path)
    items = [x for s in sinks for x in R.read_run(s)]
    sel = lambda m, k=None: [(x["question_id"], x["config"], x.get("k1_stage")) for x in A.select(items, asg, m, stage=k)]  # noqa: E731
    check("select() staged: the studio's stage 1 questions first, then stage 2's, each answer carrying k1_stage",
          sel("studio") == [(qf, "single_pass", 1), (qf, "multi_hop", 1), (qa, "single_pass", 2), (qa, "multi_hop", 2)])
    check("select() stage=1 and stage=2 split the machine's answers; a stage where the machine has none gives none "
          "(a question of the other stage is known, not refused)",
          sel("studio", 1) == [(qf, "single_pass", 1), (qf, "multi_hop", 1)]
          and sel("studio", 2) == [(qa, "single_pass", 2), (qa, "multi_hop", 2)]
          and sel("laptop", 1) == [(qb, "single_pass", 1), (qb, "multi_hop", 1)] and sel("laptop", 2) == []
          and sel("beelink", 1) == [])
    d83 = A.load(tmp / "asg.json")
    e1 = raises(lambda: A.select(items, d83, "studio", stage=1), A.AssignmentError)
    e2 = raises(lambda: A.select(items, asg, "studio", stage=3), A.AssignmentError)
    check("select() refuses a stage of a D83 file (no stages) and a stage the file does not have",
          e1 is not None and "no stages" in str(e1) and e2 is not None)
    check("select() of a D83 file is unchanged: no k1_stage on its answers",
          all("k1_stage" not in x for x in A.select(items, d83, "studio")))
    stamp = A.stamp(asg, "studio", asg_path, 1)
    check("stamp(): a staged header records the seed, the stage and the machine's questions in it",
          stamp["k1_stage"] == 1 and stamp["questions_in_stage"] == 1 and stamp["seed"] == "fixture seed"
          and "k1_stage" not in A.stamp(d83, "studio", tmp / "asg.json"))

    evaluated: list = []
    fake, Evaluator = fake_ragchecker(None, evaluated)
    with modules({"ragchecker": fake, "ragchecker.metrics": fake.metrics}):
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        gt = tmp / "gt_staged.json"
        gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": "the reference"} for q in qs]}))
        refs = {q: "the reference" for q in qs}
        lock = types.SimpleNamespace(sha256="LOCKSHA")
        call = types.SimpleNamespace(digest="d", options={}, fields=[])
        out = tmp / "rc_staged"
        out.mkdir()

        def ns(k):
            return types.SimpleNamespace(run=list(sinks), store=None, rows=None, limit=None, gt=gt, out=out,
                                         base="none", order="claims", assignment=asg_path, machine="studio",
                                         stage=k, stop_on_failed=True, dry_run=False)
        cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0}
        calls_log = out / "ragchecker_calls.jsonl"
        llm = rr.make_llm("none", call, "claims", calls_log, cur)
        saved = rr.chat
        rr.chat = lambda base, c, msgs: {"status": "ok", "text": "Entailment", "error": None, "stop_reason": "stop"}

        class CallingEvaluator(Evaluator):
            def evaluate(self, res, metrics):
                llm(["### Claim: x " + rr.CHECK_SIGNATURE])
                super().evaluate(res, metrics)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc1 = rr.score_run(ns(1), CallingEvaluator(), cur, lock, "m", call, False, out / "ragchecker.jsonl", refs)
                rc2 = rr.score_run(ns(2), CallingEvaluator(), cur, lock, "m", call, False, out / "ragchecker.jsonl", refs)
        finally:
            rr.chat = saved
        rows = [json.loads(ln) for ln in (out / "ragchecker.jsonl").read_text().splitlines()]
        heads = [json.loads(ln) for ln in (out / "ragchecker_headers.jsonl").read_text().splitlines()]
        recs = [json.loads(ln) for ln in calls_log.read_text().splitlines()]
        check("ragchecker --stage 1 then --stage 2 into one --out: stage 1's answers then stage 2's, k1_stage on every "
              "row and every call record, the header names its stage; stage 2 resumes over stage 1's rows",
              rc1 == rc2 == 0 and [(r["question_id"], r["k1_stage"], r["machine"]) for r in rows]
              == [(qf, 1, "studio"), (qf, 1, "studio"), (qa, 2, "studio"), (qa, 2, "studio")]
              and [h["k1_stage"] for h in heads] == [1, 2] and [h["to_do"] for h in heads] == [2, 2]
              and [c.get("k1_stage") for c in recs] == [1, 1, 2, 2] and all(c["stage"] == "check" for c in recs),
              f"{[(r['question_id'], r.get('k1_stage')) for r in rows]} {[c.get('k1_stage') for c in recs]}")
        a = ns(1)
        a.assignment = a.machine = None
        check("ragchecker: --stage without --assignment is refused", raises(lambda: rr.k1_args(a), SystemExit) is not None)

    S = importlib.import_module("S357_ragas")
    from experiments.runner.lock import load
    lk = load()

    async def score_row(row, ref, metrics, sem, transport=None):
        names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "factual_correctness")
        S.TaggedProxy.write(px, {"endpoint": "chat"})
        return {"question_id": row["question_id"], "config": row["config"], "scores": {m: 0.5 for m in names},
                "errors": {}, "wall_s": {m: 1.0 for m in names}, "n_contexts": len(row["contexts"]),
                "context_chars": 0, "at": "T", "transport_failures": []}
    got: list = []
    px = S.TaggedProxy.__new__(S.TaggedProxy)
    stub = types.SimpleNamespace(call=types.SimpleNamespace(options={"temperature": 0, "num_predict": 16384},
                                                            lock_sha256=lk.sha256, digest="d", fields=[]))
    ragas = types.ModuleType("ragas")
    ragas.__version__ = "stub"
    llms, embs, mets = (types.ModuleType(n) for n in ("ragas.llms", "ragas.embeddings", "ragas.metrics"))
    llms.llm_factory = lambda *a, **k: "llm"
    embs.OpenAIEmbeddings = lambda **k: "emb"
    mets.collections = types.SimpleNamespace(**{n: (lambda **k: n) for n in (
        "Faithfulness", "AnswerRelevancy", "ContextPrecisionWithReference", "ContextRecall", "FactualCorrectness")})
    saved = {k: getattr(S, k) for k in ("score_row", "lock_client", "ollama_show", "ollama_version")}
    orig_write = S.Proxy.write
    S.score_row, S.lock_client = score_row, (lambda m, e, p: (None, stub))
    S.ollama_show, S.ollama_version = (lambda m: {"model": m}), (lambda: "stub")
    S.Proxy.write = lambda self, rec: got.append(dict(rec))

    def rns(out, **kw):
        base = dict(run=[str(x) for x in sinks], gt=str(gt), store=None, out=str(out), key=None, concurrency=1,
                    assignment=str(asg_path), machine="laptop", stage=1, limit=None, dry_run=False, llm=None,
                    embedding=None)
        return types.SimpleNamespace(**{**base, **kw})
    try:
        with modules({"ragas": ragas, "ragas.llms": llms, "ragas.embeddings": embs, "ragas.metrics": mets}):
            out = tmp / "ragas_staged" / "ragas.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                rc = asyncio.run(S.main_run_async(rns(out)))
                rc_none = asyncio.run(S.main_run_async(rns(out, stage=2)))
                refused = asyncio.run(S.main_run_async(rns(tmp / "ragas_r2" / "x.jsonl", assignment=None, machine=None)))
            rows = [json.loads(ln) for ln in out.read_text().splitlines()]
            head = [json.loads(ln) for ln in (out.parent / "ragas_headers.jsonl").read_text().splitlines()]
            check("ragas --run --stage 1 on the laptop: its stage 1 answers, k1_stage and machine on every row and "
                  "every call record, the header names the stage; --stage 2 (none there) scores nothing",
                  rc == rc_none == 0 and [(r["question_id"], r["k1_stage"], r["machine"]) for r in rows]
                  == [(qb, 1, "laptop"), (qb, 1, "laptop")] and [h["k1_stage"] for h in head] == [1, 2]
                  and len(got) == 2 and all(g.get("k1_stage") == 1 and g.get("machine") == "laptop" for g in got),
                  f"{rows} {got}")
            check("ragas --run: --stage without --assignment is refused, nothing written",
                  refused == 1 and not (tmp / "ragas_r2").exists())
    finally:
        S.RUN_MACHINE = S.RUN_STAGE = None
        S.Proxy.write = orig_write
        for k, v in saved.items():
            setattr(S, k, v)


class StubOllama:
    """A stub Ollama 0.40.2 on 127.0.0.1 (a free port) for the embedding path: /api/version, /api/tags (the lock's
    digests) and /api/embed answering as self.embed says: "ok", "http500", "http400", "drop" (the connection closed
    with no answer). self.version changes what /api/version says (a server-check refusal)."""

    def __init__(self, lock):
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        self.embed, self.version, self.posts = "ok", lock.d["server"]["ollama_version"], []
        tags = [{"name": t, "digest": r["digest"]} for t, r in lock.d["models"].items()]
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, obj):
                data = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if self.path == "/api/version":
                    return self._send(200, {"version": srv.version})
                if self.path == "/api/tags":
                    return self._send(200, {"models": tags})
                return self._send(404, {"error": "not found"})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                srv.posts.append((self.path, body))
                if self.path != "/api/embed":
                    return self._send(404, {"error": "not found"})
                if srv.embed == "drop":
                    self.close_connection = True
                    self.connection.shutdown(2)
                    return None
                if srv.embed == "http500":
                    return self._send(500, {"error": "llama runner process has terminated: exit status 2"})
                if srv.embed == "http400":
                    return self._send(400, {"error": "the input length exceeds the context length"})
                return self._send(200, {"embeddings": [[0.1] * 4 for _ in body["input"]], "prompt_eval_count": 3})

        self.http = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.http.server_address[1]}"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def close(self):
        self.http.shutdown()


def check_ragas_embed_failures(tmp: Path, sinks: list, asg_path: Path, qs: tuple) -> None:
    """F2 (K1 review, 17 October): the embedding path end to end, the scorer's own code from the OpenAI client down.
    Only RAGAS is a stub: AnswerRelevancy's ascore embeds the question through an OpenAIEmbeddings that calls
    client.embeddings.create as ragas 0.4.3's does (ragas/embeddings/openai_provider.py aembed_text); the other four
    metrics return 0.5 with no call."""
    import openai
    from experiments.runner import proxy as P
    from experiments.runner.lock import load
    qa, qb, qf, qn = qs
    S = importlib.import_module("S357_ragas")
    lock = load()
    stub = StubOllama(lock)
    gt = tmp / "gt_embed.json"
    gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": "the reference"} for q in qs]}))

    class Emb:
        def __init__(self, client=None, model=None, **k):
            self.client, self.model = client, model

        async def aembed_text(self, text, **k):
            r = await self.client.embeddings.create(input=text, model=self.model)
            return r.data[0].embedding

    class Metric:
        def __init__(self, name, **k):
            self.name, self.emb = name, k.get("embeddings")

        async def ascore(self, **k):
            if self.name == "AnswerRelevancy":
                await self.emb.aembed_text(k["user_input"])
            return 0.5

    ragas = types.ModuleType("ragas")
    ragas.__version__ = "stub"
    llms, embs, mets = (types.ModuleType(n) for n in ("ragas.llms", "ragas.embeddings", "ragas.metrics"))
    llms.llm_factory = lambda *a, **k: "llm"
    embs.OpenAIEmbeddings = Emb
    mets.collections = types.SimpleNamespace(**{n: (lambda n=n, **k: Metric(n, **k)) for n in (
        "Faithfulness", "AnswerRelevancy", "ContextPrecisionWithReference", "ContextRecall", "FactualCorrectness")})
    saved = {k: getattr(S, k) for k in ("BASE", "ollama_show", "ollama_version")}
    S.BASE = stub.base
    S.ollama_show, S.ollama_version = (lambda m: {"model": m}), (lambda: "stub")

    def ns(out):
        return types.SimpleNamespace(run=[str(x) for x in sinks], gt=str(gt), store=None, out=str(out), key=None,
                                     concurrency=1, assignment=str(asg_path), machine="studio", limit=None,
                                     dry_run=False, llm=None, embedding=None)

    def session(name, mode, version=None):
        stub.embed = mode
        out = tmp / f"embed_{name}" / "ragas.jsonl"
        if version:                                   # the server changes after lock_client checked it
            real = S.lock_client

            def later(*a):
                got = real(*a)
                stub.version = version
                return got
            S.lock_client = later
        try:
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                rc = asyncio.run(S.main_run_async(ns(out)))
        finally:
            if version:
                S.lock_client = real
                stub.version = lock.d["server"]["ollama_version"]
        rows = [json.loads(ln) for ln in out.read_text().splitlines()] if out.exists() else []
        calls = [json.loads(ln) for ln in S.calls_path(out).read_text().splitlines()] if S.calls_path(out).exists() else []
        return rc, rows, calls, buf.getvalue()

    try:
        with modules({"ragas": ragas, "ragas.llms": llms, "ragas.embeddings": embs, "ragas.metrics": mets}):
            rc, rows, calls, _ = session("ok", "ok")
            check("F2 embeddings answered: every row ok, one embeddings record per answer, status ok",
                  rc == 0 and [r["status"] for r in rows] == ["ok"] * 4
                  and [c["status"] for c in calls if c.get("endpoint") == "embeddings"] == ["ok"] * 4,
                  f"rc {rc}, {len(rows)} rows")
            for name, mode, why in (("http500", "http500", "an HTTP 500 from /api/embed"),
                                    ("drop", "drop", "a connection closed with no answer")):
                rc, rows, calls, log = session(name, mode)
                rec = [c for c in calls if c.get("endpoint") == "embeddings"]
                check(f"F2 {why}: a transport failure: no row, exit 3; the call recorded once",
                      rc == 3 and rows == [] and len(rec) == 1 and rec[0]["status"] == "error"
                      and "transport failure on ['answer_relevancy']" in log, f"rc {rc}, rows {len(rows)}, "
                      f"{rec[0]['error'][:80] if rec else 'no record'}")
            n_posts = len(stub.posts)
            rc, rows, calls, log = session("lock", "ok", version="0.12.0")
            rec = [c for c in calls if c.get("endpoint") == "embeddings"]
            check("F2 a server-check refusal on the embedding call (Ollama 0.12.0): no row, exit 3, the LockError "
                  "recorded once, nothing sent to /api/embed",
                  rc == 3 and rows == [] and len(rec) == 1 and rec[0]["error"].startswith("LockError: ")
                  and all(p != "/api/embed" for p, _ in stub.posts[n_posts:]), f"rc {rc}, rows {len(rows)}")
            codes = {}
            px = P.Proxy(stub.base, lock.d["scorers"]["model"], "scorer", tmp / "embed_codes.jsonl")
            for mode in ("ok", "http500", "drop", "http400", "lock"):
                stub.embed, stub.version = ("ok", "0.12.0") if mode == "lock" else (mode, lock.d["server"]["ollama_version"])
                codes[mode] = px.embeddings({"model": "bge-m3", "input": ["x"]})[0]
            stub.version = lock.d["server"]["ollama_version"]
            check("F2 the proxy's status per case: answered 200, HTTP 500 502, dropped 502, HTTP 400 400, server "
                  "check refused 503", codes == {"ok": 200, "http500": 502, "drop": 502, "http400": 400, "lock": 503},
                  str(codes))
            n_posts = len(stub.posts)
            rc, rows, calls, log = session("http400", "http400")
            rec = [c for c in calls if c.get("endpoint") == "embeddings"]
            check("F2 an HTTP 400 from /api/embed (the server refused the request): recorded as before, a row "
                  "ok_with_nulls, answer_relevancy null with the 400 as its error, the call record status error 'HTTP 400: ...'",
                  rc == 0 and [r["status"] for r in rows] == ["ok_with_nulls"] * 4
                  and all(r["scores"]["answer_relevancy"] is None and r["errors"]["answer_relevancy"].startswith(
                      "BadRequestError: Error code: 400") and "exceeds the context length" in r["errors"]["answer_relevancy"]
                          and r["scores"]["faithfulness"] == 0.5 for r in rows)
                  and len(rec) == 4 and all(c["status"] == "error" and c["error"].startswith("HTTP 400: ") for c in rec),
                  f"rc {rc}, {[r['status'] for r in rows]}")
            check("F2 the 400s reached /api/embed (the server answered each)",
                  sum(p == "/api/embed" for p, _ in stub.posts[n_posts:]) == 4)
            st = P.embed_failure_status
            check("F2 embed_failure_status: HTTP 4xx 400; HTTP 5xx, refused, reset, bad JSON, none 502",
                  [st(e) for e in ("HTTP 400: x", "HTTP 404: x", "HTTP 500: x", "HTTP 503: x",
                                   "URLError: <urlopen error [Errno 61] Connection refused>",
                                   "RemoteDisconnected: Remote end closed connection without response",
                                   "JSONDecodeError: Expecting value", None)] == [400, 400, 502, 502, 502, 502, 502, 502])
            check("F2 transport_failure: openai 502 and 503 count, 400 does not",
                  [S.transport_failure(openai.APIStatusError("m", response=__import__("httpx").Response(
                      c, request=__import__("httpx").Request("POST", "http://x")), body=None)) for c in (502, 503, 400)]
                  == [True, True, False])
            P.embed_failure_status = lambda error: 400            # mutant: the old status, every failure 400
            try:
                rc, rows, calls, log = session("mutant500", "http500")
            finally:
                P.embed_failure_status = st
            check("F2 mutant (proxy.py before F2, every embedding failure 400): the HTTP 500 is written as ok_with_nulls "
                  "and the run goes on, so the 500 case guards the fix",
                  rc == 0 and [r["status"] for r in rows] == ["ok_with_nulls"] * 4, f"rc {rc}")
    finally:
        for k, v in saved.items():
            setattr(S, k, v)
        stub.close()


GIN_LINE = '[GIN] 2026/10/17 - 12:00:00 | 200 |    1.0s |       127.0.0.1 | {m}     "{p}"\n'


def check_busy_guard(tmp: Path) -> None:
    """F1 (K1 review, 17 October): experiments/runner/server_users.py on canned listings and a canned server log, no
    command run, no server. F2: the ledger is per server."""
    from experiments.runner import server_users as U
    base = "http://127.0.0.1:11434"
    PS = ("    1     0 /sbin/launchd\n"
          "  400     1 bash findings/recompute/K1/run_k1_beelink.sh\n"
          "  450   400 uv run --no-sync python -m experiments.runner.server_users survey --base http://127.0.0.1:11434\n"
          "  500   450 /x/bin/python -m experiments.runner.server_users survey --base http://127.0.0.1:11434\n"
          "  600     1 /opt/homebrew/opt/ollama/bin/ollama serve\n"
          "  601   600 /opt/ollama/llama-server --model /m/blobs/sha256-ab11434cd --port 11434 -c 131072\n"
          "  700     1 /usr/bin/python3 /usr/share/tool.py --sha sha256-ab11434cd --size 211434\n")
    log, ledger = tmp / "server.log", tmp / "own_11434.json"
    calls, record = tmp / "ragchecker_calls.jsonl", tmp / "fresh_load.json"
    OWN = ["devstral-small-2:24b", "bge-m3:latest"]

    def gin(*reqs):
        with log.open("a") as fh:
            for m, p in reqs:
                fh.write(GIN_LINE.format(m=m, p=p))

    def call(server=base, line=True, path="/api/chat"):
        with calls.open("a") as fh:
            fh.write(json.dumps({"server": server, "status": "ok"}) + "\n")
        if line:
            gin(("POST", path))

    def survey(ps=PS, models=(), lsof=(1, "", ""), ss=(0, "", ""), netstat=None, pattern=None, platform="darwin",
               get_error=None, begin=False, at=base, led=ledger):
        def runner(cmd):
            if cmd[0] == "ps":
                return ps if isinstance(ps, tuple) else (0, ps, "")
            if cmd[0] == "lsof":
                return lsof
            if cmd[0] == "ss":
                return ss
            return netstat

        def get(url):
            if get_error:
                raise get_error
            return {"models": [{"name": n, "expires_at": "2026-10-18T12:00:00.1234567+02:00"} for n in models]}
        return U.survey(at, OWN, led, pattern, netstat is not None, begin_log=log if begin else None,
                        runner=runner, get=get, me=500, platform=platform)

    def fresh_load(unloaded=()):
        """What job.py fresh_load does to the log: one unload per held model, the offset, the load; then its record."""
        gin(*[("POST", "/api/generate")] * len(unloaded))
        off = log.stat().st_size
        gin(("POST", "/api/generate"), ("GET", "/api/version"), ("GET", "/api/ps"))
        record.write_text(json.dumps({"base": base, "unloaded": list(unloaded), "log_offset": off, "ok": True}))
        return U.loaded(base, ledger, record, calls)

    log.write_text(GIN_LINE.format(m="POST", p="/api/chat") * 3)    # R0's requests, before this launcher
    calls.write_text("{}\n{}\n")                                     # an earlier run's two records
    o = survey()
    check("F1 guard: nothing loaded, no connection, only the launcher's own process tree and Ollama naming the port: free",
          o["busy"] is False and o["processes"] == [] and U.summary(o) == "free", U.summary(o))
    o = survey(models=["olmo-3.1:32b-think"])
    check("F1 guard: another job's model loaded (T3's olmo-3.1:32b-think), idle, no connection: busy, with the unload "
          "command for whoever decides", o["busy"] and o["loaded"][0]["model"] == "olmo-3.1:32b-think"
          and "keep_alive\": 0" in o["loaded"][0]["unload"] and base in o["loaded"][0]["unload"], U.summary(o))
    o = survey(models=["devstral-small-2:24b"], begin=True)
    check("F1 guard: devstral loaded and no ledger (a first start after R0's filler): busy, and a busy survey begins "
          "no ledger", o["busy"] and "no ledger" in o["loaded"][0]["why"] and not ledger.exists(), U.summary(o))
    size0 = log.stat().st_size
    o = survey(begin=True)
    led = json.loads(ledger.read_text()) if ledger.exists() else {}
    check("F1 ledger: a free survey with --begin-log begins the ledger at the log's size, state loading, this server's "
          "base", o["busy"] is False and led.get("state") == "loading" and led.get("log_offset") == size0
          and led.get("base") == base, str(led))
    o = survey(models=["devstral-small-2:24b"])
    check("F1 guard: devstral loaded while the ledger says the load never completed (state loading): busy",
          o["busy"] and "did not complete" in o["loaded"][0]["why"], U.summary(o))
    led = fresh_load()
    call(), call(), call(path="/api/embed")
    with calls.open("a") as fh:                                       # a proxy record with no request: no server
        fh.write(json.dumps({"endpoint": "chat", "status": "client_gone"}) + "\n")
    gin(("POST", "/api/show"), ("POST", "/api/me"), ("GET", "/api/tags"), ("HEAD", "/api/blobs/sha256:ab"))
    o = survey(models=OWN)
    check("F1 proof: devstral and bge-m3 loaded, the log since the ledger's offset holds exactly the load and the "
          "scorer's 3 recorded calls (/api/show, /api/me, GETs and a proxy record with no request are not model "
          "requests): free", o["busy"] is False and o["own_use"]["proved"] and o["own_use"]["own_load_requests"] == 1
          and o["own_use"]["own_scorer_requests"] == 3 and o["own_use"]["server_log_model_requests"] == 4
          and led["calls_lines"] == 2, json.dumps(o["own_use"]))
    gin(("POST", "/api/chat"))
    o = survey(models=OWN)
    check("F1 proof: one request by another client a second after this launcher's scorer ended (the old rule took any "
          "use within its stamp plus 120 s as its own): devstral and bge-m3 are users, the counts named",
          o["busy"] and len(o["loaded"]) == 2 and "5 model requests" in o["loaded"][0]["why"]
          and "sent 4" in o["loaded"][0]["why"], U.summary(o))
    o = survey(models=[])
    check("F1 proof: the same foreign request with nothing loaded is recorded in own_use and does not by itself make "
          "the server busy (the docstring's stated limit)", o["busy"] is False and o["own_use"]["proved"] is False)
    for path in ("/v1/chat/completions", "/api/embed", "/api/generate", "/api/some-new-endpoint"):
        ledger.unlink()
        survey(begin=True)
        fresh_load(unloaded=["devstral-small-2:24b"])
        call()
        gin(("POST", path))
        o = survey(models=["devstral-small-2:24b"])
        if not o["busy"]:
            break
    check("F1 proof: another client's POST to /v1/chat/completions, /api/embed, /api/generate or a path not listed is "
          "a model request; the load's unload of a held model is the launcher's own", o["busy"]
          and o["own_use"]["own_load_requests"] == 2, json.dumps(o["own_use"]))
    ledger.unlink()
    survey(begin=True)
    fresh_load()
    call(line=False)                                                   # a record whose request never reached it
    o = survey(models=["devstral-small-2:24b"])
    check("F1 proof fails closed the other way: a record with no request in the log (a connection refused) leaves "
          "devstral a user", o["busy"] and "sent 2" in o["loaded"][0]["why"], U.summary(o))
    ledger.unlink()
    survey(begin=True)
    fresh_load()
    with log.open("a") as fh:
        fh.write('[GIN] 2026/10/17 - 12:00:01 | 200 |    1.0s |       127.0.0.1 | PO')
    o = survey(models=["devstral-small-2:24b"])
    check("F1 proof: a last log line still being written counts as a request (fail closed)", o["busy"], U.summary(o))
    log.write_text("")
    o = survey(models=["devstral-small-2:24b"])
    check("F1 proof: a log shorter than the ledger's offset (rotated, a restarted server) proves nothing: busy",
          o["busy"] and "cannot be read" in o["loaded"][0]["why"], U.summary(o))
    ledger.unlink()
    survey(begin=True)
    fresh_load()
    other = U.survey("http://127.0.0.1:11499", OWN, ledger, None, False, runner=lambda c: (0, "", "") if c[0] == "ps"
                     else (1, "", ""), get=lambda u: {"models": [{"name": "devstral-small-2:24b"}]}, me=500)
    check("F2: a ledger proves nothing for another server (11434's ledger read for 11499): busy",
          other["busy"] and "is for http://127.0.0.1:11434" in other["loaded"][0]["why"], U.summary(other))
    rec_bad = tmp / "bad_record.json"
    rec_bad.write_text(json.dumps({"base": base, "unloaded": [], "log_offset": 0, "ok": True}))
    ledger.unlink()
    survey(begin=True)
    r1 = raises(lambda: U.loaded(base, ledger, rec_bad, calls), ValueError)
    rec_bad.write_text(json.dumps({"base": base, "unloaded": [], "log_offset": log.stat().st_size, "ok": False}))
    r2 = raises(lambda: U.loaded(base, ledger, rec_bad, calls), ValueError)
    r3 = raises(lambda: U.loaded("http://127.0.0.1:11499", ledger, record, calls), ValueError)
    check("F1 ledger: `loaded` refuses a record whose log offset precedes the ledger's, a load that did not pass, and "
          "another server", all((r1, r2, r3)), str([r1, r2, r3]))
    o = survey(ps=PS + " 800 1 python3 exp_05_coder_benchmark.py --base-url http://127.0.0.1:11434\n"
                        " 801 1 /bin/bash ./queue_s2.sh 17108 11434 ollama::x default\n")
    check("F1 guard: a process naming the port (a job's --base-url, a queue script's port argument): busy; a blob or "
          "a number that merely contains the digits is not", o["busy"] and [u["pid"] for u in o["processes"]] == [800, 801],
          str([u["pid"] for u in o["processes"]]))
    rc_line = " 900 1 /home/v/.cache/uv/bin/python3 experiments/scorers/ragchecker_run.py --arm a.json --gt g.json\n"
    pat = job_pattern("beelink")
    o1, o2 = survey(ps=PS + rc_line), survey(ps=PS + rc_line, pattern=pat)
    o3 = survey(ps=PS + " 901 1 /usr/bin/python3 experiments/mentori/publication/scripts/exp_03_rlm.py --x 1\n", pattern=pat)
    check("F1 guard: a scorer on the default port (its command line does not name it) is busy through the Beelink's "
          "JOB_PATTERN, and so is any exp_ script; without the pattern it is not seen",
          not o1["busy"] and o2["busy"] and o2["processes"][0]["why"] == "matches the job pattern" and o3["busy"])
    jl_main = " 902 1 /home/v/.venv/bin/python3 experiments/scorers/judge_passages.py --base http://127.0.0.1:11434 --judge second\n"
    jl_bare = " 903 1 /home/v/.venv/bin/python3 experiments/scorers/judge_passages.py --judge second\n"
    jl_both = " 904 1 /home/v/.venv/bin/python3 experiments/scorers/judge_passages.py --base http://127.0.0.1:11434 --x 11435\n"
    hp, mp = job_pattern("beelink", "beelink_11435"), job_pattern("beelink")
    hb = "http://127.0.0.1:11435"
    h_main, h_bare = survey(ps=PS + jl_main, pattern=hp, at=hb), survey(ps=PS + jl_bare, pattern=hp, at=hb)
    m_main = survey(ps=PS + jl_main, pattern=mp)
    h_both = survey(ps=PS + jl_both, pattern=hp, at=hb)
    check("D143 (Q11 O-c): a helper does not count a job script naming the main server's port 11434; it still counts one "
          "naming no port, the main worker still counts it, and one naming the helper's own port is busy for the helper",
          not h_main["busy"] and h_bare["busy"] and m_main["busy"] and h_both["busy"]
          and h_both["processes"][0]["why"] == "names the port",
          str([h_main["busy"], h_bare["busy"], m_main["busy"], h_both["busy"]]))
    lsof = (0, "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\n"
               "ollama 600 v 9u IPv4 0x1 0t0 TCP 127.0.0.1:11434->127.0.0.1:61694 (ESTABLISHED)\n"
               "python3.1 17188 v 4u IPv4 0x2 0t0 TCP 127.0.0.1:61694->127.0.0.1:11434 (ESTABLISHED)\n", "")
    o = survey(lsof=lsof)
    lsof_own = (0, "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\n"
                   "python 500 v 4u IPv4 0x2 0t0 TCP 127.0.0.1:61700->127.0.0.1:11434 (ESTABLISHED)\n"
                   "python 999 v 4u IPv4 0x2 0t0 TCP 127.0.0.1:61701->127.0.0.1:114340 (ESTABLISHED)\n", "")
    o_own = survey(lsof=lsof_own)
    check("F1 guard (macOS lsof): an open connection to the port, either end, is busy; the guard's own and another "
          "port's are not", o["busy"] and len(o["connections"]) == 2 and not o_own["busy"], U.summary(o_own))
    ss = (0, "0      0      127.0.0.1:53553      127.0.0.1:11434 users:((\"python3\",pid=38516,fd=4))\n"
             "0      0      127.0.0.1:53560      127.0.0.1:11434\n", "")
    o = survey(ss=ss, platform="linux")
    check("F1 guard (Linux ss): a client with a pid and one whose pid is hidden (another user's) are both busy",
          o["busy"] and [c["pids"] for c in o["connections"]] == [[38516], []])
    ns = ("  TCP    0.0.0.0:11434          0.0.0.0:0              LISTENING       32480\n"
          "  TCP    127.0.0.1:11434        127.0.0.1:51451        TIME_WAIT       0\n")
    o_quiet = survey(platform="linux", netstat=(0, ns, ""))
    o_win = survey(platform="linux", netstat=(0, ns + "  TCP    127.0.0.1:11434        127.0.0.1:54553        "
                                                      "ESTABLISHED     32480\n", ""))
    check("F1 guard (Beelink netstat.exe, 17 October's lines): LISTENING and TIME_WAIT are free, an ESTABLISHED "
          "connection on the port is busy (a Windows-side client is seen too)",
          not o_quiet["busy"] and o_win["busy"] and o_win["connections"][0]["tool"] == "netstat.exe")
    o = survey(get_error=OSError("connection refused"))
    o2 = survey(lsof=(1, "", "lsof: WARNING: can't stat()"))
    o3 = survey(ps=(1, "", "ps: no"))
    o4 = survey(platform="linux", netstat=(1, "", "netstat failed"))
    check("F1 guard fails closed: /api/ps unreadable, lsof or ps or netstat.exe failing each make the server busy",
          all(x["busy"] and x["unreadable"] for x in (o, o2, o3, o4)),
          str([x["unreadable"] for x in (o, o2, o3, o4)]))


def job_pattern(machine: str, worker: str | None = None) -> str:
    """The JOB_PATTERN run_k1_<machine>.sh exports for a worker: its STRANGER and JOB_PATTERN lines run by bash."""
    import subprocess
    src = (ROOT / f"findings/recompute/K1/run_k1_{machine}.sh").read_text()
    lines = [ln for ln in src.splitlines() if ln.startswith(("STRANGER=", "MAIN_PORT=", "NOT_MAIN=", "JOB_PATTERN="))]
    return subprocess.run(["bash", "-c", 'WORKER=$1\n' + "\n".join(lines) + '\nprintf %s "$JOB_PATTERN"', "k1",
                           worker or machine], capture_output=True, text=True, check=True).stdout


def check_fresh_load_requests(tmp: Path) -> None:
    """F1: the proof counts a fresh load's model requests as one unload per held model plus the load. Run the real
    experiments/runner/job.py fresh_load against a stub Ollama (a free port on 127.0.0.1) and count its POSTs."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    from experiments.runner import job as J
    from experiments.runner import server_users as U
    seen = []

    class H(BaseHTTPRequestHandler):
        def _reply(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            seen.append(("GET", self.path))
            self._reply({"models": [{"name": "olmo-3.1:32b-think"}, {"name": "bge-m3:latest"}]}
                        if self.path == "/api/ps" else {})

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            seen.append(("POST", self.path))
            self._reply({"done": True})

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log = tmp / "fl_server.log"
    log.write_text("")
    real = J.check
    J.check = lambda *a, **k: {"ok": True, "pending": False, "checks": {}}
    try:
        rec = J.fresh_load(f"http://127.0.0.1:{srv.server_address[1]}", "devstral-small-2:24b", log, None, None)
    finally:
        J.check = real
        srv.shutdown()
    model_posts = [p for m, p in seen if m == "POST" and p not in U.NOT_A_MODEL and not p.startswith("/api/blobs/")]
    check("F1 proof's accounting: job.py fresh_load sends exactly one model request per model it unloads plus the load "
          "(2 held, 3 POSTs), as server_users.own_requests counts", rec["unloaded"] == ["olmo-3.1:32b-think",
          "bge-m3:latest"] and len(model_posts) == len(rec["unloaded"]) + 1, str(seen))


STUB = r"""
import json, os, shutil, subprocess, sys, time, tomllib
from pathlib import Path
ROOT, D, SC = Path(os.environ["K1STUB_ROOT"]), Path(os.environ["K1STUB_DIR"]), os.environ["K1STUB_SCENARIO"]
sys.path.insert(0, str(ROOT))
LOG, STATE, TRACE = D / "server.log", D / "state.json", D / "trace.jsonl"
LOCK = tomllib.load(open(ROOT / "experiments/LOCK.toml", "rb"))
SCORER, EMB = LOCK["scorers"]["model"], LOCK["scorers"]["embedding"]
GIN = '[GIN] 2026/10/17 - 12:00:00 | 200 |    1.0s |       127.0.0.1 | POST     "{}"\n'

def trace(**k):
    with TRACE.open("a") as fh:
        fh.write(json.dumps({"t": time.time(), "pid": os.getpid(), **k}) + "\n")

def gin(path):
    with LOG.open("a") as fh:
        fh.write(GIN.format(path))

def state():
    return json.loads(STATE.read_text())

def save(s):
    STATE.write_text(json.dumps(s))

def opt(a, name):
    return a[a.index(name) + 1] if name in a else None

def count(f, s):
    return sum(s in ln for ln in open(f)) if Path(f).exists() else 0

def call(calls, rec, path, model):
    calls.parent.mkdir(parents=True, exist_ok=True)
    with calls.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    gin(path)
    s = state()
    s["loaded"] = s["loaded"] + [model] if model not in s["loaded"] else s["loaded"]
    save(s)

tool, a = sys.argv[1], sys.argv[2:]
if tool == "curl":
    trace(tool="curl", msg=opt(a, "-d"))
    sys.exit(0)
if tool == "pgrep":
    trace(tool="pgrep", args=a)
    if SC in ("refuse_running", "refuse_dry"):
        print("424242")
        sys.exit(0)
    sys.exit(1)
if tool == "pkill":
    trace(tool="pkill", args=a)
    if len(a) == 3 and a[:2] == ["-TERM", "-P"] and a[2].isdigit():      # real, and only the children of that pid
        sys.exit(subprocess.call([shutil.which("pkill"), *a]))
    sys.exit(1)
if "-c" in a:
    print(SCORER, EMB)
    sys.exit(0)
if "scripts/S451_k1_assign.py" in a and "gate" in a:
    trace(tool="gate", records=opt(a, "--records"))
    if SC == "gate_closed":
        print("G1 GATE REFUSED: " + opt(a, "--records") + "\n  g1_multi_hop: ended before its last start (running)")
        sys.exit(1)
    print("G1 GATE PASSED: " + opt(a, "--records"))
    sys.exit(0)
if "scripts/S451_k1_assign.py" in a and "worker" in a:      # the real lookup, on this repo's chain
    trace(tool="worker", args=a)
    sys.exit(subprocess.call([sys.executable, str(ROOT / "scripts/S451_k1_assign.py"),
                              *a[a.index("scripts/S451_k1_assign.py") + 1:]]))
if "scripts/S451_k1_assign.py" in a:
    print("CHECK PASSED")
    sys.exit(0)
if "experiments.runner.server_users" in a:
    sub = a[a.index("experiments.runner.server_users") + 1:]
    trace(tool="server_users", cmd=sub[0], args=sub)
    if "--begin-log" in sub:
        sub[sub.index("--begin-log") + 1] = str(LOG)
    from experiments.runner import server_users as U
    s = state()
    PSX = "    1     0 /sbin/launchd\n" + os.environ.get("K1STUB_PS_EXTRA", "")      # D89 A2: other processes
    rc = U.main(sub, runner=lambda c: (0, PSX, "") if c[0] == "ps" else (
        (1, "", "") if c[0] == "lsof" else (0, "", "")),
        get=lambda u: {"models": [{"name": m} for m in s["loaded"]]}, me=os.getpid(), platform="darwin")
    trace(tool="server_users_rc", cmd=sub[0], rc=rc)
    sys.exit(rc)
if "experiments.runner.job" in a:
    sub = a[a.index("experiments.runner.job") + 1:]
    rec_path = Path(opt(sub, "--record"))
    out = rec_path.parent
    rg = out / "ragas" / "ragas_calls.jsonl"
    trace(tool="job", cmd=sub[0], args=sub, ragchecker_calls=count(out / "ragchecker" / "ragchecker_calls.jsonl", "{"),
          ragas_chat=count(rg, '"endpoint": "chat"'), ragas_embeddings=count(rg, '"endpoint": "embeddings"'))
    if sub[0] == "fresh-load":
        s = state()
        held = list(s["loaded"])
        for _ in held:
            gin("/api/generate")
        off = LOG.stat().st_size
        gin("/api/generate")
        s["loaded"] = [opt(sub, "--model")]
        save(s)
        rec_path.write_text(json.dumps({"base": opt(sub, "--base").rstrip("/"), "model": opt(sub, "--model"),
                                        "unloaded": held, "log_offset": off, "ok": True}))
        print("ok")
        sys.exit(0)
    sys.exit(1 if SC == "afc_fail" else 0)
if any(x.endswith("ragchecker_run.py") for x in a):
    if "--dry-run" in a:
        trace(tool="dry_run", name="ragchecker", stage=opt(a, "--stage"))
        print('{"answers": 4, "to_do": 3}\nDRY RUN: no model call, nothing written')
        sys.exit(0)
    out, base = Path(opt(a, "--out")), opt(a, "--base")
    trace(tool="scorer", name="ragchecker", stage=opt(a, "--stage"), args=a)
    call(out / "ragchecker_calls.jsonl", {"server": base, "status": "ok"}, "/api/chat", SCORER)
    if SC == "graceful":                       # the coordinator touches the stop file during the first answer, which
        Path(opt(a, "--stop-file")).touch()    # ends and is written; the scorer stops before the next (exit 5)
        with (out / "ragchecker.jsonl").open("a") as fh:
            fh.write(json.dumps({"status": "ok"}) + "\n")
        print("RAGCHECKER STOPPED BETWEEN ANSWERS")
        sys.exit(5)
    time.sleep(30 if SC == "afc_fail" else 0.5)
    call(out / "ragchecker_calls.jsonl", {"server": base, "status": "ok"}, "/api/chat", SCORER)
    if SC == "foreign":
        gin("/api/chat")                       # another client's devstral request, a moment before the scorer ends
    with (out / "ragchecker.jsonl").open("a") as fh:
        fh.write(json.dumps({"status": "ok"}) + "\n")
    print("RAGCHECKER DONE")
    sys.exit(0)
if any(x.endswith("S357_ragas.py") for x in a):
    if "--dry-run" in a:
        trace(tool="dry_run", name="ragas", stage=opt(a, "--stage"))
        print('{"answers": 4, "to_do": 3}\nDRY RUN: no model call, nothing written')
        sys.exit(0)
    out, base = Path(opt(a, "--out")), os.environ["MENTORI_OLLAMA_BASE"]
    calls = out.parent / (out.stem + "_calls.jsonl")
    trace(tool="scorer", name="ragas", base=base, stage=opt(a, "--stage"), args=a)
    call(calls, {"endpoint": "chat", "server": base, "status": "ok"}, "/api/chat", SCORER)
    with calls.open("a") as fh:                # the proxy's record of a call it never sent: no server, no request
        fh.write(json.dumps({"endpoint": "chat", "status": "client_gone"}) + "\n")
    time.sleep(1.0)                            # a watcher that fired on the chat call alone would check now
    call(calls, {"endpoint": "embeddings", "server": base, "status": "ok"}, "/api/embed", EMB)
    time.sleep(1.0)
    with out.open("a") as fh:
        fh.write(json.dumps({"status": "ok"}) + "\n")
    print("RAGAS --run DONE")
    sys.exit(0)
trace(tool="unknown", args=a)
sys.exit(9)
"""

WRAP = ('uv() { "$K1STUB_PY" "$K1STUB" uv "$@"; }; curl() { "$K1STUB_PY" "$K1STUB" curl "$@"; }; '
        'pkill() { "$K1STUB_PY" "$K1STUB" pkill "$@"; }; pgrep() { "$K1STUB_PY" "$K1STUB" pgrep "$@"; }; '
        'sleep() { command sleep 0.05; }; export -f uv curl pkill pgrep sleep; exec bash "$@"')


CLONES = {"studio": "projects/mentori-runs-k1", "beelink": "projects/mentori-runs", "laptop": "projects/mentori-runs-k1"}


def test_repo(repo: Path, amendments: bytes | None = None, claims: str = "ok") -> None:
    """A git repo standing for a clone at the K1 commit: the committed assignment.json and amendments.json (or the
    given chain), the sealed reference claims folder (D92 Q190; claims "ok", "missing" or "bad_manifest") and one
    other tracked file, all committed."""
    import hashlib
    import subprocess
    k1 = repo / "findings/recompute/K1"
    k1.mkdir(parents=True, exist_ok=True)
    (k1 / "assignment.json").write_bytes((ROOT / "findings/recompute/K1/assignment.json").read_bytes())
    (k1 / "amendments.json").write_bytes(amendments or (ROOT / "findings/recompute/K1/amendments.json").read_bytes())
    if claims != "missing":
        cd = k1 / "reference_claims"
        cd.mkdir()
        body = b'{"question_id": "fixture"}\n'
        (cd / "reference_claims.jsonl").write_bytes(body)
        h = hashlib.sha256(body if claims == "ok" else b"other").hexdigest()
        (cd / "MANIFEST.sha256").write_text(f"{h}  reference_claims.jsonl\n")
    (repo / "tracked.txt").write_text("tracked\n")
    git = ["git", "-C", str(repo), "-c", "user.name=check", "-c", "user.email=check@invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(git[:3] + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "clone"], check=True)


def run_launcher(tmp: Path, name: str, machine: str, scenario: str, loaded=(), ledgers=None, port=None,
                 dry=False, extra_env=None, worker=None, amendments=None, prepare=None, args=None, claims="ok") -> dict:
    """One launcher (the committed run_k1_<machine>.sh and k1_lib.sh) end to end, every external command a stub:
    uv (the lock read, S451 check, both scorers, the real server_users on canned listings, job fresh-load and
    after-first-call; S451 worker is the real one on this repo's chain), curl (ntfy), pkill (recorded; run for real
    only as -P <pid>) and sleep (0.05 s). The repo is a git repo at the worker's registry clone under a HOME of its own
    (helpers: the launcher checks the clone, the port and the tracked files). prepare(repo) runs before the launch."""
    import os
    import subprocess
    import time
    d = tmp / f"launch_{name}"
    worker = worker or machine
    home, inputs = d / "home", d / "inputs"
    clone = CLONES[machine] if worker == machine else f"projects/mentori-runs-k1-{worker.rsplit('_', 1)[1]}"
    repo = home / clone
    for x in (repo, home, inputs):
        x.mkdir(parents=True, exist_ok=True)
    test_repo(repo, amendments, claims)
    (inputs / "x").write_text("x\n")
    subprocess.run("shasum -a 256 x > MANIFEST.sha256", shell=True, cwd=inputs, check=True)
    (d / "server.log").write_text("")
    (d / "state.json").write_text(json.dumps({"loaded": list(loaded)}))
    out = repo / "findings/recompute/K1" / worker
    out.mkdir(parents=True, exist_ok=True)
    for fname, obj in (ledgers or {}).items():
        (out / fname).write_text(json.dumps(obj))
    if prepare:
        prepare(repo)
    stub = d / "k1stub.py"
    stub.write_text(STUB)
    env = {**os.environ, "HOME": str(home), "K1_INPUTS": str(inputs),
           "K1STUB": str(stub), "K1STUB_PY": sys.executable, "K1STUB_ROOT": str(ROOT), "K1STUB_DIR": str(d),
           "K1STUB_SCENARIO": scenario, **({"K1_PORT": port} if port else {}), **(extra_env or {})}
    for k in ("K1_DRY_RUN", "K1_REPO", "K1_PORT_11453_OK") + (() if port else ("K1_PORT",)):
        if k not in (extra_env or {}):
            env.pop(k, None)
    if dry:
        env["K1_DRY_RUN"] = "1"
    t0 = time.time()
    argv = list(args) if args is not None else ([worker] if worker != machine else [])
    p = subprocess.run(["/bin/bash", "-c", WRAP, "k1", str(ROOT / f"findings/recompute/K1/run_k1_{machine}.sh"), *argv],
                       env=env, capture_output=True, text=True, timeout=180)
    tr = [json.loads(x) for x in (d / "trace.jsonl").read_text().splitlines()] if (d / "trace.jsonl").exists() else []
    busy = [json.loads(x) for x in (out / "busy_checks.jsonl").read_text().splitlines()] \
        if (out / "busy_checks.jsonl").exists() else []
    return {"rc": p.returncode, "stdout": p.stdout + p.stderr, "trace": tr, "busy": busy, "out": out, "repo": repo,
            "home": home, "wall_s": time.time() - t0, "log": d / "server.log"}


def steps(r: dict) -> list[str]:
    return [f"{e['tool']}:{e.get('cmd') or e.get('name') or ''}" + (f":{e['stage']}" if e.get("stage") else "")
            for e in r["trace"] if e["tool"] in ("server_users", "job", "scorer")]


def check_launchers(tmp: Path) -> None:
    """F3 (K1 review, 17 October): the launchers' wiring, run against stubs (run_launcher), not read as strings. F1 and
    F2 through the launcher: the ledger per port, the proof between scorers. F4: a failed after-first-call stops only
    this launcher's scorer, by PID."""
    import os
    import time
    from experiments.runner.lock import load
    scorer, emb = load().d["scorers"]["model"], load().d["scorers"]["embedding"]
    want = [x for k in ("1", "2") for x in (
        "server_users:survey", "job:fresh-load", "server_users:loaded", f"scorer:ragchecker:{k}", "job:after-first-call",
        "server_users:survey", "job:fresh-load", "server_users:loaded", f"scorer:ragas:{k}", "job:after-first-call")]
    for machine, port, log in (("studio", "11441", None),
                               ("beelink", "11434", "/mnt/c/Users/Valerio/AppData/Local/Ollama/server.log"),
                               ("laptop", "11434", "/opt/homebrew/var/log/ollama.log")):
        r = run_launcher(tmp, f"clean_{machine}", machine, "clean")
        tr, st = r["trace"], steps(r)
        surveys = [e for e in tr if e["tool"] == "server_users" and e["cmd"] == "survey"]
        rcs = [e for e in tr if e["tool"] == "server_users_rc"]
        log = log or str(r["home"] / f"ollama_logs/serve_{port}.log")
        check(f"F3/D86 launcher {machine}: runs to the end against the stubs, in the order busy check, fresh load, "
              f"ledger, scorer, after-first-call, for RAGChecker then RAGAS, stage 1 then stage 2 without stopping "
              f"(each scorer called with its --stage)", r["rc"] == 0 and st == want
              and f"K1 {machine} done" in r["stdout"], f"rc {r['rc']} {st} {r['stdout'][-300:]}".replace("\n", " | "))
        fl_idx = [i for i, s in enumerate(st) if s == "job:fresh-load"]
        check(f"F3 launcher {machine}: a busy check that returned free immediately before each of the four fresh loads",
              len(fl_idx) == 4 and all(st[i - 1] == "server_users:survey" for i in fl_idx)
              and [e["rc"] for e in rcs if e["cmd"] == "survey"] == [0, 0, 0, 0], str(st))
        dry = [(e["name"], e["stage"]) for e in tr if e["tool"] == "dry_run"]
        gates = [e["records"] for e in tr if e["tool"] == "gate"]
        live = [str(r["home"] / "projects/mentori-runs/findings/recompute/G1_runs")] if machine == "studio" else []
        pg = [e["args"] for e in tr if e["tool"] == "pgrep"]
        posts = [e.get("msg") or "" for e in tr if e["tool"] == "curl"]
        check(f"D86 launcher {machine}: both scorers' dry runs for both stages, the G1 gate on the inputs' g1_records "
              f"{'and the live G1 records ' if live else ''}before them, the refusal check {'(' + machine + ') ' if pg else ''}"
              f"and an ntfy post at each stage's end",
              dry == [("ragchecker", "1"), ("ragas", "1"), ("ragchecker", "2"), ("ragas", "2")]
              and gates == [str(r["home"].parent / "inputs" / "g1_records")] + live
              and len(pg) == (0 if machine == "studio" else 1)
              and [p for p in posts if p.startswith(f"K1 {machine} stage ") and p.endswith(" done")]
              == [f"K1 {machine} stage 1 done", f"K1 {machine} stage 2 done"],
              f"dry {dry} gates {gates} pgrep {pg} posts {posts}")
        led_path = os.path.normpath(r["out"] / f"own_{port}.json")
        check(f"F2 launcher {machine}: the busy check names the ledger of this server's port (own_{port}.json), the "
              f"lock's scorer and encoder, and the server's own log to begin it at",
              all(all(f in s["args"] for f in ("--ledger", "--own-models", "--base", "--begin-log"))
                  and os.path.normpath(r["repo"] / s["args"][s["args"].index("--ledger") + 1]) == led_path
                  and s["args"][s["args"].index("--own-models") + 1:][:2] == [scorer, emb]
                  and s["args"][s["args"].index("--base") + 1] == f"http://127.0.0.1:{port}"
                  and os.path.normpath(s["args"][s["args"].index("--begin-log") + 1]) == os.path.normpath(log)
                  for s in surveys) and Path(led_path).exists() and not (r["out"] / "own_until").exists(),
              str([s["args"] for s in surveys]))
        second = r["busy"][1] if len(r["busy"]) > 1 else {}
        check(f"F1 launcher {machine}: between the scorers, devstral loaded is the launcher's own by the proof (the log "
              f"holds the load and RAGChecker's 2 calls, nothing else)", second.get("busy") is False
              and (second.get("own_use") or {}).get("proved") is True
              and (second.get("own_use") or {}).get("own_scorer_requests") == 2, json.dumps(second.get("own_use")))
        afc = [e for e in tr if e["tool"] == "job" and e["cmd"] == "after-first-call"]
        ok_afc = len(afc) == 4
        if ok_afc:
            rc_a, rg_a = afc[:2]
            ok_afc = ("--also" not in rc_a["args"] and rc_a["ragchecker_calls"] >= 1
                      and "--also" in rg_a["args"] and rg_a["args"][rg_a["args"].index("--also") + 1:] == [emb]
                      and rg_a["ragas_chat"] >= 1 and rg_a["ragas_embeddings"] >= 1)
        check(f"F3 launcher {machine}: RAGChecker's after-first-call after its first call, without --also; RAGAS's only "
              f"once a chat and an embedding call are recorded (the stub waits a second between them), with --also "
              f"{emb}", ok_afc, json.dumps([{k: e.get(k) for k in ("args", "ragchecker_calls", "ragas_chat",
                                                                   "ragas_embeddings")} for e in afc]))
        if machine == "studio":
            from experiments.runner import server_users as U
            third = U.survey(f"http://127.0.0.1:{port}", [scorer, emb], Path(led_path), None, False,
                             runner=lambda c: (0, "", "") if c[0] == "ps" else (1, "", ""),
                             get=lambda u: {"models": [{"name": scorer}, {"name": emb}]}, me=os.getpid())
            check("F1 launcher studio: after RAGAS, devstral and bge-m3 loaded are its own by the proof (the load's "
                  "unload of devstral and the load, a chat and an embedding call; the proxy's client_gone record "
                  "not counted)", third["busy"] is False and third["own_use"]["own_load_requests"] == 2
                  and third["own_use"]["own_scorer_requests"] == 2, json.dumps(third["own_use"]))

    r = run_launcher(tmp, "foreign", "studio", "foreign")
    st = steps(r)
    last = r["busy"][-1] if r["busy"] else {}
    check("F1 launcher: another client's devstral request while RAGChecker ran makes the check before RAGAS busy; the "
          "launcher stops with no second fresh load", r["rc"] == 1 and st.count("job:fresh-load") == 1
          and st[-1] == "server_users:survey" and last.get("busy") is True
          and "another job uses the server" in " ".join(e.get("msg") or "" for e in r["trace"] if e["tool"] == "curl"),
          f"{st} {json.dumps(last.get('own_use'))}")
    stale = {"state": "scoring", "base": "http://127.0.0.1:11453", "port": 11453, "log": str(tmp / "none.log"),
             "log_offset": 0, "load_record": str(tmp / "none.json"), "calls": str(tmp / "none.jsonl"), "calls_lines": 0}
    r = run_launcher(tmp, "other_port", "studio", "clean", loaded=[scorer], ledgers={"own_11453.json": stale})
    st = steps(r)
    first = r["busy"][0] if r["busy"] else {}
    check("F2 launcher: on 11441, devstral loaded and only a ledger of 11453 present: busy (the old per-machine stamp "
          "would have taken it as its own); no fresh load", r["rc"] == 1 and st == ["server_users:survey"]
          and first.get("busy") is True and "no ledger" in first["loaded"][0]["why"], f"{st} {first.get('loaded')}")

    check_launcher_refusals(tmp)
    r = run_launcher(tmp, "afc_fail", "studio", "afc_fail")
    st, tr = steps(r), r["trace"]
    pk = [e["args"] for e in tr if e["tool"] == "pkill"]
    spid = next((e["pid"] for e in tr if e["tool"] == "scorer"), None)
    gone = False
    for _ in range(40):
        try:
            os.kill(spid, 0)
        except (ProcessLookupError, TypeError):
            gone = True
            break
        except PermissionError:
            break
        time.sleep(0.05)
    check("F4 launcher: a failed after-first-call stops this launcher's scorer by PID (pkill -TERM -P <its pid>, then "
          "kill), never by a pattern another job's command line could match; the scorer (sleeping 30 s) is gone and "
          "the launcher stops at once, with no second fresh load", r["rc"] == 1 and r["wall_s"] < 25 and gone
          and len(pk) == 1 and pk[0][:2] == ["-TERM", "-P"] and pk[0][2].isdigit()
          and st.count("job:fresh-load") == 1 and "after-first-call check FAILED" in r["stdout"],
          f"rc {r['rc']} wall {r['wall_s']:.1f} pkill {pk} gone {gone} {st}")


def check_launcher_refusals(tmp: Path) -> None:
    """D86: the launchers' refusals, run against the stubs (run_launcher), and the refusal patterns against the command
    lines read on the machines on 17 October."""
    import re
    import subprocess
    for machine in ("studio", "beelink", "laptop"):
        r = run_launcher(tmp, f"gate_{machine}", machine, "gate_closed")
        posts = [e.get("msg") or "" for e in r["trace"] if e["tool"] == "curl"]
        check(f"D86 launcher {machine}: G1's draw 1 not final (the gate refuses): stops before any dry run, busy "
              f"check or load, with an ntfy post", r["rc"] == 1 and steps(r) == []
              and not any(e["tool"] == "dry_run" for e in r["trace"]) and "G1's draw 1 is not final" in r["stdout"]
              and posts == [f"K1 {machine} stopped: G1 not final"], f"rc {r['rc']} {steps(r)} {posts}")
    for machine, why in (("beelink", "R0's deferred rows"), ("laptop", "an S2 variant on the laptop")):
        r = run_launcher(tmp, f"refuse_{machine}", machine, "refuse_running")
        check(f"D86 launcher {machine}: the scoring run refuses while {why} run (pgrep finds one): no dry run, no busy "
              f"check, no load", r["rc"] == 1 and steps(r) == [] and f"{why}" in r["stdout"]
              and "it must end first" in r["stdout"] and not any(e["tool"] == "dry_run" for e in r["trace"]),
              f"rc {r['rc']} {steps(r)} {r['stdout'][-300:]}".replace("\n", " | "))
        r = run_launcher(tmp, f"refuse_dry_{machine}", machine, "refuse_dry", dry=True)
        check(f"D86 launcher {machine}: a dry run while {why} run completes (dry runs of both stages), says the scoring "
              f"run would refuse, and loads nothing", r["rc"] == 0 and steps(r) == []
              and "would refuse now" in r["stdout"] and "dry run complete" in r["stdout"]
              and len([e for e in r["trace"] if e["tool"] == "dry_run"]) == 4
              and not any(e["tool"] == "curl" for e in r["trace"]), f"rc {r['rc']} {r['stdout'][-300:]}".replace("\n", " | "))
    for port, why, word in (("11453", "Figure 3's verifier", "verifier"), ("11434", "the Mentori app's port", "Mentori")):
        p = subprocess.run(["bash", str(ROOT / "findings/recompute/K1/run_k1_studio.sh")], capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "HOME": str(tmp), "K1_PORT": port}, timeout=30)
        check(f"D86 launcher studio: K1_PORT {port} is refused ({why}) before anything runs",
              p.returncode == 1 and "REFUSED" in p.stdout and word in p.stdout, p.stdout.strip())
    studio = (ROOT / "findings/recompute/K1/run_k1_studio.sh").read_text()
    check("D86 launcher studio: port 11441 by default, its server log serve_11441.log",
          "PORT=${K1_PORT:-11441}" in studio and "SERVER_LOG=$HOME/ollama_logs/serve_$PORT.log" in studio)
    pat = {m: (ROOT / f"findings/recompute/K1/run_k1_{m}.sh").read_text().split("REFUSE_PATTERN='", 1)[1].split("'", 1)[0]
           for m in ("beelink", "laptop")}
    seen = {"beelink": ["bash run_rc_deferred.sh",
                        "/home/valeriob/.cache/uv/environments-v2/ragchecker-run-64f684a08008db75/bin/python3 "
                        "experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11434 --arm findings/recompute/"
                        "S357/arm_gemini/results.json --gt findings/recompute/S357/subset_ground_truth.json --out "
                        "findings/recompute/R0_pilot_beelink/rc_rows90_180/ragchecker --rows 90:180"],
            "laptop": ["/Users/valeriobianchi/projects/mentori-runs-s2-laptop-d75/experiments/mentori/.venv/bin/python3 "
                       "experiments/mentori/publication/scripts/exp_05_coder_benchmark.py --model "
                       "ollama::devstral-small-2:24b --thinking default --base-url http://127.0.0.1:11434",
                       "bash findings/recompute/S2_launch_laptop/run_s2_laptop.sh ollama::devstral-small-2:24b default"]}
    k1 = ["bash findings/recompute/K1/run_k1_beelink.sh", "bash findings/recompute/K1/run_k1_laptop.sh",
          "python3 experiments/scorers/ragchecker_run.py --run k1_inputs/runs/x --assignment "
          "findings/recompute/K1/assignment.json --machine beelink --stage 1"]
    check("D86 refusal patterns: the Beelink's matches R0's deferred filler and its scorer, the laptop's the S2 "
          "launcher and exp_05 (command lines read 17 October); neither matches a K1 launcher or scorer",
          all(re.search(pat[m], c) for m in seen for c in seen[m]) and not any(re.search(pat[m], c) for m in pat for c in k1),
          str(pat))


# ---------------------------------------------------------------- helpers (Valerio, 17 October): workers, the chain,
# fences, moves, releases, suggest. The numbers in the check names are the design's tests (1 to 15).

PS_IDLE = "    1     0 /sbin/launchd\n"
NOW = "2026-10-17T18:30:00+02:00"


class HFix:
    """A K1 world in a temporary directory: two runs (single_pass, multi_hop) of draw 1 over five applicable questions
    h1..h5 (the key's order) and one not applicable; a staged base (studio: h1 h2 stage 1, h3 h4 stage 2; beelink: h5
    stage 2; laptop: none) with its deal inputs and per-answer estimates; a coordinator K1 directory and one clone per
    worker under home/c/<worker>, each with its own copy of the files (a checkout)."""

    def __init__(self, tmp: Path, name: str, rc_s: float = 36000.0, rg_s: float = 3600.0,
                 laptop_start: str = "2026-10-17T17:30:00+02:00"):
        import S451_k1_assign as S451
        from experiments.runner import experiment as ex
        self.S = S451
        self.home = tmp / f"h_{name}"
        self.home.mkdir()
        qs = ex.questions()
        app = [q["id"] for q in qs if R.applies("ragchecker", q["id"])][:5]
        qn = next(q["id"] for q in qs if not R.applies("ragchecker", q["id"]))
        self.h = app
        self.qn = qn
        store = self.home / "chroma"
        make_store(store, {"coll_s20": CHUNKS})
        self.sinks = []
        for cfg in ("single_pass", "multi_hop"):
            sink = self.home / "runs" / f"exp_01__{cfg}__{INDEX}"
            ii.record(sink, INDEX, "coll_s20", store=store, script="check")
            write_jsonl(sink / "answers.jsonl", [exp01_line(q, 1, f"answer {cfg} {q}", None, ["id-b", "id-a"], config=cfg)
                                                 for q in app + [qn]])
            self.sinks.append(sink)
        self.gt = self.home / "gt.json"
        self.gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": "the reference"} for q in app + [qn]]}))
        self.per = {q: {c: [rc_s, rg_s] for c in ("single_pass", "multi_hop")} for q in app}
        fac = {"rc_factor": {"studio": 1.0, "beelink": 1.0, "laptop": 1.0},
               "ragas_factor": {"studio": 1.0, "beelink": 3.0, "laptop": 3.0}}
        cost = {m: {q: round(sum(v[0] * fac["rc_factor"][m] + v[1] * fac["ragas_factor"][m] for v in self.per[q].values())
                             / 3600, 3) for q in app} for m in ("studio", "beelink", "laptop")}
        sha = {"single_pass": "a" * 64, "multi_hop": "b" * 64}
        start = "2026-10-17T17:30:00+02:00"
        st = {app[0]: 1, app[1]: 1, app[2]: 2, app[3]: 2, app[4]: 2}
        mach = {app[0]: "studio", app[1]: "studio", app[2]: "studio", app[3]: "studio", app[4]: "beelink"}
        self.base = signed({"rule": "fixture", "rule_sha256": A.sha256("fixture"), "draws": [1],
                            "configs": ["single_pass", "multi_hop"], "machines": ["studio", "beelink", "laptop"],
                            "seed": "fixture seed",
                            "stage_sizes": {"1": {"studio": 2, "beelink": 0, "laptop": 0},
                                            "2": {"studio": 2, "beelink": 1, "laptop": 0}},
                            "questions": [{"id": q, "category": "c", "group": "answerable", "stage": st[q],
                                           "machine": mach[q]} for q in app],
                            "not_scored": [{"id": qn, "reason": "not applicable (Rule 8)"}],
                            "stage_2_inputs": {"starts": {"studio": start, "beelink": start, "laptop": laptop_start},
                                               "question_cost_h": cost, **fac, "answers_sha256": sha}})
        self.k1 = self.home / "coord" / "findings/recompute/K1"
        self.k1.mkdir(parents=True)
        (self.k1 / "assignment.json").write_text(json.dumps(self.base))
        base = A.load(self.k1 / "assignment.json")
        reg = {w: {"machine": w, "port": p, "clone": f"~/c/{w}"} for w, p in (("studio", 11441), ("beelink", 11434),
                                                                               ("laptop", 11434))}
        g = {"base_assignment_sha256": base["assignment_sha256"], "base_file_sha256": base["file_sha256"],
             "lock_sha256": A.sha256((ROOT / "experiments/LOCK.toml").read_bytes()), "workers": reg,
             "move_rule": S451.MOVE_RULE, "move_rule_sha256": A.sha256(S451.MOVE_RULE)}
        g["genesis_sha256"] = A.genesis_sha256(g)
        (self.k1 / "amendments.json").write_text(json.dumps({"genesis": g, "records": []}, indent=1))
        (self.k1 / "estimates.json").write_text(json.dumps({"answers_sha256": sha, "per_answer": self.per}))

    def clone(self, worker: str, clone: str | None = None) -> Path:
        """A worker's clone (made on first use) with the coordinator's assignment and amendments checked out; its K1."""
        import subprocess
        root = self.home / (clone or f"c/{worker}")
        k1 = root / "findings/recompute/K1"
        k1.mkdir(parents=True, exist_ok=True)
        for f in ("assignment.json", "amendments.json"):
            (k1 / f).write_bytes((self.k1 / f).read_bytes())
        if not (root / ".git").exists():              # a git clone at a commit (the fence checks its tracked files)
            git = ["git", "-C", str(root), "-c", "user.name=check", "-c", "user.email=check@invalid", "-c",
                   "commit.gpgsign=false"]
            subprocess.run(git[:3] + ["init", "-q"], check=True)
            subprocess.run(git + ["add", "findings/recompute/K1/assignment.json", "findings/recompute/K1/amendments.json"],
                           check=True)
            subprocess.run(git + ["commit", "-qm", "clone"], check=True)
        return k1

    def root(self, worker: str, clone: str | None = None) -> Path:
        return self.home / (clone or f"c/{worker}")

    def chain(self, k1: Path | None = None) -> tuple[dict, dict, dict]:
        return self.S.load_all(k1 or self.k1)

    def fence(self, worker: str, ps: str = PS_IDLE, clone: str | None = None, **kw):
        return self.S.fence(worker, k1=self.root(worker, clone) / "findings/recompute/K1", root=self.root(worker, clone),
                            home=self.home, ps_text=ps, me=999999, now=dt_(NOW), **kw)

    def copy_fence(self, worker: str, name: str, clone: str | None = None) -> Path:
        """What the coordinator copies back: fence.json and the two row files."""
        src = self.root(worker, clone) / "findings/recompute/K1" / worker
        d = self.home / "copies" / name
        d.mkdir(parents=True)
        for f in ("fence.json", "ragchecker/ragchecker.jsonl", "ragas/ragas.jsonl"):
            if (src / f).exists():
                shutil.copy(src / f, d / Path(f).name)
        return d

    def move(self, src, dst, n, fence_from, **kw):
        return self.S.move(src, dst, n, fence_from=fence_from, reason=kw.pop("reason", "check"), k1=self.k1,
                           now=dt_(kw.pop("now", NOW)), **kw)

    def write_rows(self, worker: str, scorer: str, rows: list, calls: list | None = None, clone: str | None = None):
        out = self.root(worker, clone) / "findings/recompute/K1" / worker
        write_jsonl(out / A.ROWS[scorer], rows)
        if calls is not None:
            write_jsonl(out / A.CALLS[scorer], calls)


def dt_(s: str):
    import datetime as dt
    return dt.datetime.fromisoformat(s)


def hrow(q: str, cfg: str, worker: str | None = "studio", status: str = "ok", wall=10.0, machine: str | None = None) -> dict:
    r = {"run_id": f"exp_01__{cfg}__{INDEX}", "answer_key": f"{INDEX}|{cfg}|{q}|d1", "question_id": q, "config": cfg,
         "draw": 1, "status": status, "wall_s": wall, "machine": machine or (worker or "").split("_")[0] or "studio",
         "lock_sha256": "L"}
    if worker:
        r["worker"] = worker
    return r


def rc_call(q: str, cfg: str = "single_pass") -> dict:
    return {"answer": f"exp_01__{cfg}__{INDEX}|{INDEX}|{cfg}|{q}|d1", "status": "ok", "stage": "check"}


def check_helpers_chain(tmp: Path) -> None:
    """Tests 1, 7, 8: the empty chain reads the base exactly (also as the K1 commit's code read it), signatures, random
    moves."""
    import random
    import subprocess
    import S451_k1_assign as S451
    from experiments.runner import experiment as ex
    real = S451.OUT.read_bytes()
    head_blob = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:findings/recompute/K1/assignment.json"],
                               capture_output=True).stdout
    base = A.load(S451.OUT)
    chain = A.load_chain(S451.AMEND, base)
    gen = chain["genesis"]["genesis_sha256"]
    eff = A.effective(base, chain, upto=gen)            # the chain cut at its genesis: no move applied
    heads = [gen] + [r["amendment_sha256"] for r in chain["records"]]
    check("helpers 1: assignment.json is the committed file, byte for byte (e2c3ab33ccdb, never edited); the committed "
          "chain verifies over that base and the lock d66daa28 (its genesis, then each committed move: move 1 of 17 "
          "October, c58c9331, the first), and its head is its last record",
          real == head_blob and base["assignment_sha256"].startswith("e2c3ab33ccdb")
          and chain["head"] == heads[-1]
          and chain["genesis"]["lock_sha256"] == A.sha256((ROOT / "experiments/LOCK.toml").read_bytes())
          and chain["genesis"]["workers"] == S451.REGISTRY, f"{A.sha256(real)[:12]}, {len(chain['records'])} move(s)")
    eff_now = A.effective(base, chain)
    check("helpers 1: the committed moves keep stage 1 membership and each question on one worker",
          sorted(q["id"] for q in eff_now["questions"] if q["stage"] == 1)
          == sorted(q["id"] for q in base["questions"] if q["stage"] == 1)
          and len({q["id"] for q in eff_now["questions"]}) == len(eff_now["questions"]) == len(base["questions"]))
    # every answer of the 96 and of the 39 not scored, six configs, draws 1 and 2: what select() reads of an answer
    items = [{"question_id": q["id"], "config": c, "draw": d, "answer_key": f"{c}|{q['id']}|d{d}"}
             for q in ex.questions() for c in base["configs"] for d in (1, 2)]
    old_src = subprocess.run(["git", "-C", str(ROOT), "show", "c7ad841:experiments/scorers/assignment.py"],
                             capture_output=True, text=True).stdout
    old = types.ModuleType("assignment_c7ad841")
    exec(compile(old_src, "assignment_c7ad841.py", "exec"), old.__dict__)
    ob = old.load(S451.OUT)
    same_load = {k: v for k, v in ob.items()} == {k: base[k] for k in ob}
    rows, diff = 0, []
    for m in base["machines"]:
        for k in (None, 1, 2):
            want = [(x["question_id"], x["config"], x["draw"], x.get("k1_stage")) for x in old.select(items, ob, m, stage=k)]
            for got_asg in (base, eff):
                got = [(x["question_id"], x["config"], x["draw"], x.get("k1_stage"))   # a planning read: base_ok
                       for x in A.select(items, got_asg, m, stage=k, base_ok=True)]
                if got != want:
                    diff.append((m, k))
            rows += len(want)
            if old.stamp(ob, m, S451.OUT, k) != A.stamp(base, m, S451.OUT, k):
                diff.append(("stamp", m, k))
    check("helpers 1: the K1 commit's assignment.py (c7ad841, what the running launchers use) and this one load "
          "e2c3ab33ccdb alike; for every machine and stage (none, 1, 2) select() gives the same answers in the same "
          "order from the base and from the genesis chain by worker (576 answers of draw 1 split three ways), and "
          "the same header stamp", same_load and not diff and rows == 2 * 576, f"{rows} rows compared, {diff}")
    check("helpers 1: with the chain cut at its genesis each worker's questions are its machine's, in stage then key order",
          all(A.worker_questions(eff, m) == [{"id": q["id"], "stage": q["stage"]} for q in sorted(
              (q for q in base["questions"] if q["machine"] == m), key=lambda q: (q["stage"], base["questions"].index(q)))]
              for m in base["machines"]))
    check("helpers 1: the per-answer estimates (estimates.json, committed) give every signed question_cost_h again",
          S451.estimates_reproduce(json.loads(S451.ESTIMATES.read_text())["per_answer"], base["stage_2_inputs"]) == [])
    check("helpers: A.DONE_RC and A.DONE_RAGAS are the scorers' own done sets (ragchecker_run DONE with not_applicable, "
          "S357 RUN_DONE)", A.DONE_RC == frozenset(importlib.import_module("experiments.scorers.ragchecker_run").DONE
                                                   | {"not_applicable"})
          and A.DONE_RAGAS == frozenset(importlib.import_module("S357_ragas").RUN_DONE))

    # 7: signatures, on a fixture chain with two moves made through fences
    f = HFix(tmp, "sig")
    f.clone("studio")
    f.fence("studio")
    r1 = f.move("studio", "studio_11499", 1, f.copy_fence("studio", "s1"), new=True)
    k1s = f.clone("studio")
    S451.release("studio", k1=k1s)
    f.fence("studio")
    f.clone("studio_11499", clone="projects/mentori-runs-k1-11499")
    f.fence("studio_11499", clone="projects/mentori-runs-k1-11499")
    f.move("studio", "studio_11499", 1, f.copy_fence("studio", "s2"),
           fence_to=f.copy_fence("studio_11499", "t2", clone="projects/mentori-runs-k1-11499"))
    base_f, chain_f, _ = f.chain()
    doc = json.loads((f.k1 / "amendments.json").read_text())

    def refused(mut, name):
        d = copy.deepcopy(doc)
        mut(d)
        p = f.home / f"chain_{name}.json"
        p.write_text(json.dumps(d))
        return raises(lambda: A.load_chain(p, base_f), A.AssignmentError)
    e = {
        "questions": refused(lambda d: d["records"][0]["questions"][0].update(id=f.h[2]), "q"),
        "from": refused(lambda d: d["records"][0].update({"from": "beelink"}), "from"),
        "to": refused(lambda d: d["records"][1].update(to="laptop"), "to"),
        "reason": refused(lambda d: d["records"][1].update(reason="other"), "reason"),
        "order": refused(lambda d: d.update(records=d["records"][::-1]), "order"),
        "genesis": refused(lambda d: d["genesis"]["workers"]["studio"].update(port=11442), "genesis"),
    }

    def broken_prev(d):
        r = d["records"][1]
        r["prev"] = "0" * 64
        r["amendment_sha256"] = A.record_sha256(r)
    e["prev"] = refused(broken_prev, "prev")

    def resigned_wrong_source(d):
        r = d["records"][1]
        r["questions"] = [{"id": f.h[4], "stage": 2}]
        r["amendment_sha256"] = A.record_sha256(r)
        d["records"] = d["records"][:2]
    e["held"] = refused(resigned_wrong_source, "held")
    other = dict(base_f, assignment_sha256="f" * 64)
    e["base"] = raises(lambda: A.load_chain(f.k1 / "amendments.json", other), A.AssignmentError)
    e["head"] = raises(lambda: A.effective(base_f, chain_f, upto="0" * 64), A.AssignmentError)
    e["head_scorer"] = raises(lambda: A.for_worker(f.k1 / "assignment.json", f.k1 / "amendments.json", "beelink",
                                                   "beelink", "0" * 64), A.AssignmentError)
    words = {"questions": "does not recompute", "from": "does not recompute", "to": "does not recompute",
             "reason": "does not recompute", "order": "seq", "genesis": "genesis_sha256", "prev": "broken",
             "held": "does not hold", "base": "another base", "head": "not in the chain", "head_scorer": "not in the chain"}
    check("helpers 7: the chain refuses a hand edit of a move's questions, from, to or reason, records reordered, a "
          "genesis edited, a broken prev (re-signed), a re-signed move of a question its source does not hold, a chain "
          "for another base, and a pinned head that is not in the file (in effective() and in a scorer's for_worker())",
          all(e[k] is not None and words[k] in str(e[k]) for k in words) and r1["seq"] == 1 and len(chain_f["records"]) == 2,
          "; ".join(f"{k}: {str(v)[:60]}" for k, v in e.items() if v is None or words[k] not in str(v)))

    # 8: seeded random moves on the real base, signed directly (each with a fence id of its own)
    rng = random.Random(86)
    g = chain["genesis"]
    recs, prev, cur = [], g["genesis_sha256"], A.effective(base, chain)
    ok = True
    for i in range(1, 61):
        lists = {w: A.worker_questions(cur, w) for w in cur["workers"]}
        src = rng.choice(sorted(w for w in lists if lists[w]))
        new = rng.random() < 0.3
        dst = f"studio_{11500 + i}" if new else rng.choice(sorted(w for w in lists if w != src))
        k = rng.randint(1, min(5, len(lists[src])))
        qs = rng.sample(lists[src], k)
        r = {"kind": "move", "seq": i, "at": "2026-10-18T00:00+02:00", "from": src, "to": dst,
             **({"to_defined": {"machine": "studio", "port": 11500 + i, "clone": f"~/x{i}"}} if new else {}),
             "stage_filter": None, "questions": qs, "reason": "random", "fence_from": {"fence_id": A.sha256(f"f{i}")},
             "fence_to": None, "prev": prev}
        r["amendment_sha256"] = A.record_sha256(r)
        prev = r["amendment_sha256"]
        recs.append(r)
        p = tmp / "random_chain.json"
        p.write_text(json.dumps({"genesis": g, "records": recs}))
        ch = A.load_chain(p, base)
        cur = A.effective(base, ch)
        owner = A.worker_of(cur)
        st = A.stage_of(cur)
        order_ok = all([q["stage"] for q in A.worker_questions(cur, w)] == sorted(q["stage"] for q in A.worker_questions(cur, w))
                       for w in cur["workers"])
        ok = ok and (len(owner) == 96 and all(owner[q] in cur["workers"] for q in owner)
                     and sum(len(A.worker_questions(cur, w)) for w in cur["workers"]) == 96
                     and st == A.stage_of(base) and cur["not_scored"] == base["not_scored"] and order_ok
                     and {q for q, s in st.items() if s == 1} == {q["id"] for q in base["questions"] if q["stage"] == 1})
    keyed = all(A.worker_questions(cur, w) == sorted(A.worker_questions(cur, w), key=lambda q: (
        q["stage"], [x["id"] for x in base["questions"]].index(q["id"]))) for w in cur["workers"])
    items1 = [x for x in items if x["draw"] == 1]
    union = sorted((x["question_id"], x["config"]) for w in cur["workers"] for x in A.select(items1, cur, w))
    check("helpers 8: 60 seeded random moves (a third to new workers): after each, every one of the 96 questions has "
          "exactly one worker, every stage and the stage 1 set (the base's 25) are unchanged, not_scored is unchanged; "
          "each worker's order is stage 1 then stage 2 in the key's order; select() over all workers covers each "
          "answer once", ok and keyed and union == sorted((q["id"], c) for q in base["questions"] for c in base["configs"]),
          f"{len(cur['workers'])} workers")


def check_helpers_moves(tmp: Path) -> None:
    """Tests 2 to 6, 11 (fence and release), 15."""
    import S451_k1_assign as S451
    base = A.load(S451.OUT)
    # the base's studio list (9 stage 1, 27 stage 2), as the check names it: the live chain moved 5 of studio's stage 2
    # questions to studio_11456 on 20 Oct (amendment 8f7f0b10), so the live list no longer fits this check's fixture
    studio = A.worker_questions(A.effective(base, None), "studio")
    p5, p27, p30, p28 = (S451.pick_last(studio, set(), n, k) for n, k in ((5, None), (27, 2), (30, None), (28, 2)))
    begun = {studio[-1]["id"]}
    check("helpers 2: on the real studio list (9 stage 1, 27 stage 2) a move takes the last N not begun in its order: "
          "5 gives the last 5 of stage 2; --stage 2 and the default both take stage 2 first; 30 takes all 27 of stage 2 "
          "and the last 3 of stage 1; 28 of stage 2 is none (never part); a question begun is skipped",
          p5 == studio[-5:] and all(q["stage"] == 2 for q in p5) and p27 == studio[9:] and p30 == studio[6:]
          and [q["stage"] for q in p30].count(1) == 3 and p28 == []
          and S451.pick_last(studio, begun, 1, None) == [studio[-2]] and S451.pick_last(studio, begun, 1, 2) == [studio[-2]])

    # 3: what counts as begun, through a fence and a move (studio: h1 h2 stage 1, h3 h4 stage 2)
    def case(name, rows_rc=(), rows_rg=(), calls_rc=(), calls_rg=()):
        f = HFix(tmp, f"t3_{name}")
        f.clone("studio")
        f.write_rows("studio", "ragchecker", list(rows_rc), list(calls_rc))
        f.write_rows("studio", "ragas", list(rows_rg), list(calls_rg))
        fz = f.fence("studio")
        d = f.copy_fence("studio", name)
        two = raises(lambda: f.move("studio", "studio_11499", 2, d, new=True, stage=2), S451.Refused)
        try:
            one = [q["id"] for q in f.move("studio", "studio_11499", 1, d, new=True, stage=2, write=False)["questions"]]
        except S451.Refused:
            one = []
        return fz, two, one
    h = HFix(tmp, "t3_ids").h
    h1, h2, h3, h4 = h[:4]
    res = {
        "a RAGChecker row": case("rcrow", rows_rc=[hrow(h4, "single_pass")]),
        "a RAGAS row": case("rgrow", rows_rg=[hrow(h4, "single_pass")]),
        "only RAGChecker call records (an answer in flight)": case("rccall", calls_rc=[rc_call(h4), rc_call(h4)]),
        "only a RAGAS call record (a transport failure, no row)": case("rgcall", calls_rg=[
            {"answer": f"single_pass|{h4}", "metric": "faithfulness", "status": "error"}]),
    }
    ok3 = all(two is not None and "1 questions it has not begun" in str(two) and one == [h3] and h4 in
              fz["touched_rows"] + fz["touched_calls"] for fz, two, one in res.values())
    # an untagged call record after the last row: RAGChecker rows for h1 h2 h3 (both configs), a record naming none
    fz, two, one = case("untagged", rows_rc=[hrow(q, c) for q in (h1, h2, h3) for c in ("single_pass", "multi_hop")],
                        calls_rc=[rc_call(h3), {"status": "ok", "stage": "check"}])
    check("helpers 3: a question is begun, and never moves, with a RAGChecker row, a RAGAS row, only RAGChecker call "
          "records, or only a RAGAS call record: two cannot move (refused, never part), one moves the other",
          ok3, "; ".join(f"{k}: {v[1]} {v[2]}" for k, v in res.items()))
    check("helpers 3: an untagged call record after the last row makes the next question in the worker's order begun "
          "(h4 after h3's rows): nothing of stage 2 can move", fz["touched_calls"] == [h3, h4]
          and two is not None and "0 questions" in str(two) and one == [], f"{fz['touched_calls']} {two}")

    # 4: the fence's own refusals
    f = HFix(tmp, "t4")
    f.clone("studio")
    f.clone("beelink")
    f.write_rows("studio", "ragchecker", [hrow(h1, "single_pass")], [rc_call(h1)])
    nofence = f.home / "copies" / "empty"
    nofence.mkdir(parents=True)
    e_none = raises(lambda: f.move("studio", "studio_11499", 1, nofence, new=True), S451.Refused)
    f.fence("studio")
    d = f.copy_fence("studio", "ok")
    bad = f.copy_fence("studio", "bad")
    with (bad / "ragchecker.jsonl").open("a") as fh:
        fh.write(json.dumps(hrow(h2, "single_pass")) + "\n")
    e_hash = raises(lambda: f.move("studio", "studio_11499", 1, bad, new=True), S451.Refused)
    f.fence("beelink")
    db = f.copy_fence("beelink", "b")
    e_other = raises(lambda: f.move("studio", "studio_11499", 1, db, new=True), S451.Refused)
    f.move("studio", "studio_11499", 1, d, new=True)
    e_twice = raises(lambda: f.move("studio", "studio_11500", 1, d, new=True), S451.Refused)
    # a stale list: the coordinator's chain moved a studio question since this fence was taken (a copy of the
    # chain before the move is what the clone fenced under)
    g = HFix(tmp, "t4s")
    g.clone("studio")
    g.fence("studio")
    first = g.copy_fence("studio", "first")
    g.move("studio", "studio_11499", 1, first, new=True)
    k1s = g.clone("studio")
    S451.release("studio", k1=k1s)
    (k1s / "amendments.json").write_bytes(json.dumps({"genesis": json.loads((g.k1 / "amendments.json").read_text())[
        "genesis"], "records": []}).encode())            # the clone back on the genesis: it missed the move
    e_rolled = raises(lambda: g.fence("studio"), S451.Refused)   # review F1: its fence was released against the move
    (k1s / "studio" / "fence.json").unlink()                     # and with the fence gone too, the move still refuses
    g.fence("studio")
    e_stale = raises(lambda: g.move("studio", "studio_11500", 1, g.copy_fence("studio", "stale"), new=True), S451.Refused)
    check("helpers 16: a fence is refused in a clone whose amendments.json was put back to an older chain after a "
          "release (the head its fence was released against is not in it)",
          e_rolled is not None and "rolled-back" in str(e_rolled), str(e_rolled))
    check("helpers 4: a move refuses no fence, a copied row file whose hash differs from the fence's, another worker's "
          "fence, a fence already used (no replay), and a fence whose question list is not the worker's under the "
          "chain now (its clone missed an amendment)",
          all(x is not None for x in (e_none, e_hash, e_other, e_twice, e_stale)) and "no fence" in str(e_none)
          and "copy the worker's" in str(e_hash) and "beelink's, not studio's" in str(e_other)
          and "already used" in str(e_twice) and "missed an amendment" in str(e_stale),
          f"{e_none} | {e_hash} | {e_other} | {e_twice} | {e_stale}")

    # 5: the target's refusals
    f = HFix(tmp, "t5")
    f.clone("studio")
    f.fence("studio")
    d = f.copy_fence("studio", "s")
    e = {
        "running target without a fence": raises(lambda: f.move("studio", "beelink", 1, d), S451.Refused),
        "a new worker named as an existing one": raises(lambda: f.move("studio", "beelink", 1, d, new=True), S451.Refused),
        "11434 on the Studio": raises(lambda: f.move("studio", "studio_11434", 1, d, new=True), S451.Refused),
        "11453 on the Studio": raises(lambda: f.move("studio", "studio_11453", 1, d, new=True), S451.Refused),
        "11453 with the removed override": raises(lambda: f.move("studio", "studio_11453", 1, d, new=True,
                                                                 port_11453_ok=True), TypeError),
        "the port of another worker": raises(lambda: f.move("studio", "studio_11441", 1, d, new=True), S451.Refused),
        "the clone of another worker": raises(lambda: f.move("studio", "studio_11499", 1, d, new=True,
                                                             to_clone="~/c/studio"), S451.Refused),
        "a machine with one server": raises(lambda: f.move("studio", "laptop_11500", 1, d, new=True), S451.Refused),
        "the Beelink app's 11434 (the beelink worker's)": raises(lambda: f.move("studio", "beelink_11434", 1, d,
                                                                                new=True), S451.Refused),
        "a name not <machine>_<port>": raises(lambda: f.move("studio", "helper", 1, d, new=True), S451.Refused),
        "more questions than can move": raises(lambda: f.move("studio", "studio_11499", 5, d, new=True), S451.Refused),
    }
    import inspect
    ok53 = "port_11453_ok" not in inspect.signature(S451.move).parameters and "never a K1 port" in str(
        e["11453 on the Studio"])
    f.move("studio", "studio_11499", 1, d, new=True)
    k1s = f.clone("studio")
    S451.release("studio", k1=k1s)
    f.fence("studio")
    e["a new worker that a move already defined"] = raises(
        lambda: f.move("studio", "studio_11499", 1, f.copy_fence("studio", "s2"), new=True), S451.Refused)
    check("helpers 5: a move refuses a running target without its fence, a duplicate new worker (an existing name, or "
          "one an earlier move defined), Studio 11434 and 11453 (11453 never, no override), a port or "
          "clone another worker on the machine uses (the Beelink's 11434 among them), a new worker on a machine with "
          "one server (the laptop), a bad name, and N larger than the questions that can move",
          all(v is not None for v in e.values()) and ok53, "; ".join(f"{k}: {str(v)[:50]}" for k, v in e.items()))

    # D89 A2: the Beelink runs a second server, so a move can define beelink_11435 (its clone by default
    # ~/projects/mentori-runs-k1-11435), and the launcher's lookup gives that machine, port and clone
    f = HFix(tmp, "t5b")
    f.clone("beelink")
    f.fence("beelink")
    rec_b = f.move("beelink", "beelink_11435", 1, f.copy_fence("beelink", "b"), new=True, stage=2)
    with contextlib.redirect_stdout(io.StringIO()) as wbuf:
        rc_w = S451.cmd_worker(types.SimpleNamespace(worker="beelink_11435", amendments=str(f.k1 / "amendments.json"),
                                                     assignment=str(f.k1 / "assignment.json"), fields=True))
    check("helpers 5 (D89 A2): a move defines the Beelink helper beelink_11435 (machine beelink, port 11435, clone "
          "~/projects/mentori-runs-k1-11435); S451 worker gives the launcher those fields",
          rec_b["to_defined"] == {"machine": "beelink", "port": 11435, "clone": "~/projects/mentori-runs-k1-11435"}
          and rc_w == 0 and wbuf.getvalue().split()[:3] == ["beelink", "11435", "~/projects/mentori-runs-k1-11435"],
          f"{rec_b.get('to_defined')} | {wbuf.getvalue().strip()[:200]}")

    # 6: stage 1 moves end stage 1 sooner, or are refused (studio not started; beelink slow on its finished h5)
    f = HFix(tmp, "t6")
    f.clone("studio")
    f.clone("beelink")
    f.write_rows("beelink", "ragchecker", [hrow(f.h[4], c, worker="beelink", wall=3 * 36000.0)
                                           for c in ("single_pass", "multi_hop")])
    f.fence("studio")
    f.fence("beelink")
    ds, dbl = f.copy_fence("studio", "s"), f.copy_fence("beelink", "b")
    now6 = "2026-10-17T18:30:00+02:00"
    e_slow = raises(lambda: f.move("studio", "beelink", 1, ds, fence_to=dbl, stage=1, now=now6, write=False),
                    S451.Refused)
    ok_new = f.move("studio", "studio_11499", 1, ds, new=True, stage=1, now=now6, write=False)
    pj = ok_new["projection"]
    check("helpers 6: a stage 1 question moves to a new Studio worker when its projected stage 1 end (22 h from now) "
          "is before the source's (44 h), and is refused to the Beelink, whose measured rate (3.0, from its rows) "
          "ends it later", e_slow is not None and "stage 1 moves only to end sooner" in str(e_slow)
          and [q["stage"] for q in ok_new["questions"]] == [1]
          and pj["after"]["studio_11499"]["stage_1_end"] < pj["before"]["studio"]["stage_1_end"],
          f"{e_slow} | {pj['after']['studio_11499']['stage_1_end']} < {pj['before']['studio']['stage_1_end']}")

    # 11: the lock and release
    f = HFix(tmp, "t11")
    f.clone("studio")
    out = f.root("studio") / "findings/recompute/K1/studio"
    (out / ".launcher").mkdir(parents=True)
    (out / ".launcher" / "owner.json").write_text(json.dumps({"role": "launcher", "pid": 4242}))
    live = raises(lambda: f.fence("studio", ps=PS_IDLE + " 4242     1 bash findings/recompute/K1/run_k1_studio.sh\n"),
                  S451.Refused)
    orphan = raises(lambda: f.fence("studio", ps=PS_IDLE + " 5000     1 python3 experiments/scorers/ragchecker_run.py "
                                    "--out findings/recompute/K1/studio/ragchecker\n"), S451.Refused)
    (out / ".launcher" / "owner.json").unlink()
    old = raises(lambda: f.fence("studio", ps=PS_IDLE + " 4243     1 bash findings/recompute/K1/run_k1_studio.sh\n"),
                 S451.Refused)
    helper_launcher = PS_IDLE + " 4244     1 bash findings/recompute/K1/run_k1_studio.sh studio_11451\n"
    fz = f.fence("studio", ps=helper_launcher)
    check("helpers 11: the fence refuses while a live launcher holds the lock (owner.json's pid runs run_k1), and while "
          "any process is the worker's (an orphaned scorer naming its directory; a c7ad841 launcher between two "
          "commands, which names none); it takes a stale lock over when no process is the worker's (a helper's "
          "launcher on the machine is not)", all(x is not None for x in (live, orphan, old))
          and "live launcher" in str(live) and "orphaned" in str(orphan) and "run_k1_studio.sh" in str(old)
          and fz["lock_taken"] == "stale" and json.loads((out / ".launcher" / "owner.json").read_text())["role"] == "fence",
          f"{live} | {orphan} | {old}")
    again = raises(lambda: f.fence("studio"), S451.Refused)
    k1s = f.root("studio") / "findings/recompute/K1"
    no_rec = raises(lambda: S451.release("studio", k1=k1s), S451.Refused)
    no_ab = raises(lambda: S451.release("studio", k1=k1s, abandon_=True), S451.Refused)
    d = f.copy_fence("studio", "s")
    rec = S451.abandon("studio", d, "nothing to move", k1=f.k1, now=dt_(NOW))
    used = raises(lambda: f.move("studio", "studio_11499", 1, d, new=True), S451.Refused)
    f.clone("studio")
    as_move = raises(lambda: S451.release("studio", k1=k1s), S451.Refused)
    (out / "ragchecker").mkdir(exist_ok=True)
    (out / "ragchecker" / "ragchecker_calls.jsonl").write_text(json.dumps(rc_call(h1)) + "\n")
    ran = raises(lambda: S451.release("studio", k1=k1s, abandon_=True), S451.Refused)
    (out / "ragchecker" / "ragchecker_calls.jsonl").unlink()
    try:
        rel = S451.release("studio", k1=k1s, abandon_=True)
    except S451.Refused as e:                                 # recorded as this check's failure, not a crash
        rel = {"released_by": f"refused: {e}"}
    check("helpers 11: release refuses with no record naming the fence (move or abandon); a second fence is refused "
          "while one is unreleased; an abandon record makes the fence unusable for a move and needs release --abandon; "
          "release refuses when a file changed after the fence; then it releases and frees the lock",
          all(x is not None for x in (again, no_rec, no_ab, used, as_move, ran)) and rec["kind"] == "abandon"
          and "already used" in str(used) and "release --abandon" in str(as_move) and "changed since the fence" in str(ran)
          and rel["released_by"] == "abandon" and not (out / ".launcher").exists(),
          f"{again} | {no_rec} | {no_ab} | {used} | {as_move} | {ran}")
    f2 = HFix(tmp, "t11b")
    f2.clone("studio")
    f2.fence("studio")
    d2 = f2.copy_fence("studio", "s")
    f2.move("studio", "studio_11499", 1, d2, new=True)
    f2.clone("studio")
    k1b = f2.root("studio") / "findings/recompute/K1"
    ab_after_move = raises(lambda: S451.abandon("studio", d2, "x", k1=f2.k1), S451.Refused)
    no_abandon = raises(lambda: S451.release("studio", k1=k1b, abandon_=True), S451.Refused)
    ok = S451.release("studio", k1=k1b)
    check("helpers 11: a fence a move used cannot be abandoned (the coordinator refuses the record) nor released with "
          "--abandon; release against the move's record succeeds", ab_after_move is not None and no_abandon is not None
          and "a move used it" in str(no_abandon) and ok["released_by"] == "move", f"{ab_after_move} | {no_abandon}")

    # review F2: the fence runs only on HEAD's code (S451 and assignment.py checked out over an older HEAD refused)
    import subprocess
    f3 = HFix(tmp, "t16d")
    f3.clone("studio")
    r3 = f3.root("studio")
    git = ["git", "-C", str(r3), "-c", "user.name=check", "-c", "user.email=check@invalid", "-c", "commit.gpgsign=false"]
    (r3 / "code.py").write_text("v1\n")
    subprocess.run(git + ["add", "code.py"], check=True)
    subprocess.run(git + ["commit", "-qm", "code"], check=True)
    (r3 / "code.py").write_text("v2, checked out from a later commit\n")
    e_dirty = raises(lambda: f3.fence("studio"), S451.Refused)
    (r3 / "code.py").write_text("v1\n")
    (r3 / "findings/recompute/K1/amendments.json").write_text((f3.k1 / "amendments.json").read_text() + "\n")
    try:
        ok_amd = f3.fence("studio")["worker"] == "studio"
    except S451.Refused as e_:
        ok_amd = f"refused: {e_}"
    check("helpers 16: a fence refuses a clone with a tracked file that differs from HEAD (code checked out over an "
          "older commit, review F2) and accepts one where only amendments.json differs",
          e_dirty is not None and "tracked files differ from HEAD" in str(e_dirty) and ok_amd is True,
          f"{e_dirty} | {ok_amd}")

    # 15: a fence's prefix hash of a call log that has grown since
    f = HFix(tmp, "t15")
    f.clone("studio")
    f.write_rows("studio", "ragchecker", [hrow(h1, "single_pass")], [rc_call(h1)])
    fz = f.fence("studio")
    calls = f.root("studio") / "findings/recompute/K1/studio" / A.CALLS["ragchecker"]
    with calls.open("a") as fh:
        fh.write(json.dumps(rc_call(h2)) + "\n" + json.dumps(rc_call(h2)) + "\n")
    st = fz["files"]["ragchecker_calls"]
    check("helpers 15: hashing the fenced length of a call log that has grown since gives the fence's sha256 again; "
          "the whole file does not", S451.prefix_sha256(calls, st["bytes"]) == st["sha256"]
          and S451.file_state(calls)["sha256"] != st["sha256"] and st["lines"] == 1)


def score_helper(f: "HFix", worker: str, clone: str | None, k: int, head: str | None, limit=None, ragas=True,
                 machine: str | None = None) -> dict:
    """Both scorers' real K1 run mode for one worker and stage, RAGChecker and RAGAS replaced by stubs that write call
    records naming their answer; head None scores in the old way (no --worker). Returns what each evaluated."""
    import S451_k1_assign as S451  # noqa: F401
    k1 = f.root(worker, clone) / "findings/recompute/K1"
    out = k1 / worker
    machine = machine or worker.split("_")[0]
    from experiments.runner.lock import load
    lsha = load().sha256
    ev: list = []
    fake, Evaluator = fake_ragchecker(None, ev)
    lock = types.SimpleNamespace(sha256=lsha)
    call = types.SimpleNamespace(digest="d", options={}, fields=[])
    kw = dict(worker=worker, amendments=k1 / "amendments.json", amendments_head=head) if head else {}
    with modules({"ragchecker": fake, "ragchecker.metrics": fake.metrics}):
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        (out / "ragchecker").mkdir(parents=True, exist_ok=True)
        cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0}
        llm = rr.make_llm("none", call, "claims", out / A.CALLS["ragchecker"], cur)
        saved = rr.chat
        rr.chat = lambda base, c, msgs: {"status": "ok", "text": "Entailment", "error": None, "stop_reason": "stop"}

        class Calling(Evaluator):
            def evaluate(self, res, metrics):
                llm(["### Claim: x " + rr.CHECK_SIGNATURE])
                super().evaluate(res, metrics)
        a = types.SimpleNamespace(run=list(f.sinks), store=None, rows=None, limit=limit, gt=f.gt, out=out / "ragchecker",
                                  base="none", order="claims", assignment=k1 / "assignment.json", machine=machine,
                                  stage=k, stop_on_failed=True, dry_run=False, **kw)
        try:
            rr.k1_args(a)
            with contextlib.redirect_stdout(io.StringIO()) as dry:
                rr.dry_run(a)
            with contextlib.redirect_stdout(io.StringIO()):
                rr.score_run(a, Calling(), cur, lock, "m", call, False, out / A.ROWS["ragchecker"],
                             {q["id"]: q["expected_answer"] for q in json.loads(f.gt.read_text())["questions"]})
        finally:
            rr.chat = saved
    seen: list = []
    if ragas:
        S = importlib.import_module("S357_ragas")
        cur_calls = {}
        names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "factual_correctness")
        px = S.TaggedProxy.__new__(S.TaggedProxy)

        async def score_row(row, ref, metrics, sem, transport=None):
            seen.append(row["question_id"])
            S.CALL_TAG.set({"answer": f"{row['config']}|{row['question_id']}", "metric": "faithfulness"})
            S.TaggedProxy.write(px, {"endpoint": "chat", "status": "ok"})
            return {"question_id": row["question_id"], "config": row["config"], "scores": {m: 0.5 for m in names},
                    "errors": {}, "wall_s": {m: 1.0 for m in names}, "n_contexts": 2, "context_chars": 0, "at": "T",
                    "transport_failures": []}
        stub = types.SimpleNamespace(call=types.SimpleNamespace(options={"temperature": 0, "num_predict": 16384},
                                                                lock_sha256=lsha, digest="d", fields=[]))
        ragas = types.ModuleType("ragas")
        ragas.__version__ = "stub"
        llms, embs, mets = (types.ModuleType(n) for n in ("ragas.llms", "ragas.embeddings", "ragas.metrics"))
        llms.llm_factory = lambda *a, **k: "llm"
        embs.OpenAIEmbeddings = lambda **k: "emb"
        mets.collections = types.SimpleNamespace(**{n: (lambda **k: n) for n in (
            "Faithfulness", "AnswerRelevancy", "ContextPrecisionWithReference", "ContextRecall", "FactualCorrectness")})
        saved = {x: getattr(S, x) for x in ("score_row", "lock_client", "ollama_show", "ollama_version")}
        orig = S.Proxy.write
        S.score_row = score_row
        S.lock_client = lambda m, e, p: (cur_calls.update(path=p), (None, stub))[1]
        S.ollama_show, S.ollama_version = (lambda m: {"model": m}), (lambda: "stub")

        def write(self, rec):
            with Path(cur_calls["path"]).open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
        S.Proxy.write = write
        rns = types.SimpleNamespace(run=[str(x) for x in f.sinks], gt=str(f.gt), store=None,
                                    out=str(out / A.ROWS["ragas"]), key=None, concurrency=1,
                                    assignment=str(k1 / "assignment.json"), machine=machine, stage=k, limit=limit,
                                    dry_run=False, llm=None, embedding=None,
                                    **{x: (str(v) if isinstance(v, Path) else v) for x, v in kw.items()})
        try:
            with modules({"ragas": ragas, "ragas.llms": llms, "ragas.embeddings": embs, "ragas.metrics": mets}):
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = asyncio.run(S.main_run_async(rns))
            if rc != 0:
                raise RuntimeError(f"ragas exit {rc}")
        finally:
            S.RUN_MACHINE = S.RUN_STAGE = S.RUN_WORKER = None
            S.Proxy.write = orig
            for x, v in saved.items():
                setattr(S, x, v)
    return {"ragchecker": [e.split("|")[-2] for e in ev], "ragas": seen, "dry": dry.getvalue()}


def check_helpers_end_to_end(tmp: Path) -> None:
    """Tests 9, 10, 12: score, stop, fence, move, release, restart; the pin; machine and worker in every record."""
    import S451_k1_assign as S451
    f = HFix(tmp, "e2e")
    h1, h2, h3, h4, h5 = f.h
    f.clone("studio")
    _, chain0, _ = f.chain()
    H0 = chain0["head"]
    s1 = score_helper(f, "studio", None, 1, H0, limit=2, ragas=False)           # RAGChecker stage 1: h1, then stopped
    f.fence("studio")
    d = f.copy_fence("studio", "e2e")
    rec = f.move("studio", "studio_11499", 1, d, new=True)
    k1s = f.clone("studio")
    S451.release("studio", k1=k1s)
    tclone = "projects/mentori-runs-k1-11499"
    f.clone("studio_11499", clone=tclone)
    _, chain1, _ = f.chain()
    H1 = chain1["head"]
    src = {k: score_helper(f, "studio", None, k, H1) for k in (1, 2)}
    tgt = {k: score_helper(f, "studio_11499", tclone, k, H1) for k in (1, 2)}
    t = src[2]["dry"]
    dry2 = json.loads(t[: t.index("\n}\n") + 2]) if t.startswith("{") else {}
    rc_src = [q for k in (1, 2) for q in src[k]["ragchecker"]]
    calls_src = [A.question_of_call(json.loads(ln), "ragchecker") for ln in
                 (k1s / "studio" / A.CALLS["ragchecker"]).read_text().splitlines()]
    check("helpers 9: after score (h1 on RAGChecker), stop, fence, move (the last question not begun, h4, to a new "
          "worker studio_11499), release and restart, the source's dry run and every call it makes leave h4 out; the "
          "target scores exactly h4 with both scorers",
          [q["id"] for q in rec["questions"]] == [h4] and s1["ragchecker"] == [h1, h1]
          and dry2.get("answers") == 2 and dry2.get("worker") == "studio" and h4 not in rc_src and h4 not in calls_src
          and set(src[1]["ragas"] + src[2]["ragas"]) == {h1, h2, h3}
          and [q for k in (1, 2) for q in tgt[k]["ragchecker"]] == [h4, h4]
          and [q for k in (1, 2) for q in tgt[k]["ragas"]] == [h4, h4],
          f"{rec['questions']} dry {dry2.get('answers')} rc {rc_src} target {tgt[2]}")
    # the Beelink's h5 scored the old way (no --worker): rows with machine only, as before the helpers
    f.clone("beelink")
    for k in (1, 2):
        score_helper(f, "beelink", None, k, None)
    coll = f.home / "collect"
    for w, clone in (("studio", None), ("studio_11499", tclone), ("beelink", None)):
        shutil.copytree(f.root(w, clone) / "findings/recompute/K1" / w, coll / w)
    base_f, chain_f, eff_f = f.chain()
    got = A.collect(coll, base_f, chain_f)
    want = sorted((q, c) for q in f.h for c in ("single_pass", "multi_hop"))
    check("helpers 9: collect() over every worker's two row files: each answer once per scorer, nothing missing",
          all(sorted((r["question_id"], r["config"]) for r in got["rows"][s]) == want for s in A.SCORERS)
          and got["missing"] == {"ragchecker": [], "ragas": []}, json.dumps(got["missing"]))
    rows_t = [json.loads(ln) for s in A.SCORERS for ln in (coll / "studio_11499" / A.ROWS[s]).read_text().splitlines()]
    calls_t = [json.loads(ln) for s in A.SCORERS for ln in (coll / "studio_11499" / A.CALLS[s]).read_text().splitlines()]
    rows_b = [json.loads(ln) for s in A.SCORERS for ln in (coll / "beelink" / A.ROWS[s]).read_text().splitlines()]
    head = json.loads((coll / "studio_11499" / "ragchecker/ragchecker_headers.jsonl").read_text().splitlines()[-1])
    check("helpers 12: a helper's rows and call records carry machine (studio, the hardware) and worker "
          "(studio_11499); its header the worker, the pinned head and the moves; rows written without --worker carry "
          "the machine only and read as worker = machine",
          all(x.get("machine") == "studio" and x.get("worker") == "studio_11499" for x in rows_t + calls_t)
          and head["worker"] == "studio_11499" and head["amendments_head"] == H1 and head["moves"] == 1
          and all("worker" not in r and r["machine"] == "beelink" for r in rows_b)
          and {A.row_worker(r) for r in rows_b} == {"beelink"}, f"{head.get('worker')} {head.get('amendments_head')}")
    again = score_helper(f, "beelink", None, 2, chain_f["head"])
    check("helpers 12: the Beelink restarted with --worker over its rows written without it resumes: no call",
          again["ragchecker"] == [] and again["ragas"] == [])
    # collect's refusals: a row in a worker's file for a question it does not own; a question in two files
    bad = f.home / "collect_bad"
    shutil.copytree(coll, bad)
    with (bad / "beelink" / A.ROWS["ragas"]).open("a") as fh:
        fh.write(json.dumps(hrow(h4, "single_pass", worker="beelink", machine="beelink")) + "\n")
    e1 = raises(lambda: A.collect(bad, base_f, chain_f), A.AssignmentError)
    bad2 = f.home / "collect_bad2"
    shutil.copytree(coll, bad2)
    with (bad2 / "studio" / A.ROWS["ragchecker"]).open("a") as fh:
        fh.write(json.dumps(hrow(h4, "single_pass", worker="studio_11499", machine="studio")) + "\n")
    e2 = raises(lambda: A.collect(bad2, base_f, chain_f), A.AssignmentError)
    check("helpers 9: collect() refuses a question with rows in two workers' files and a row written by another worker",
          e1 is not None and "rows in the files of" in str(e1) and e2 is not None and "written by" in str(e2), f"{e1} | {e2}")

    # 10: the pin. A move touching studio (made with fences) after the head a beelink and a studio process pinned
    g = HFix(tmp, "pin")
    g.clone("studio")
    _, c0, _ = g.chain()
    g.fence("studio")
    g.move("studio", "studio_11499", 1, g.copy_fence("studio", "p"), new=True)
    k1g = g.clone("studio")
    e_fenced = raises(lambda: A.for_worker(k1g / "assignment.json", k1g / "amendments.json", "studio", "studio",
                                           g.chain()[1]["head"]), A.AssignmentError)
    S451.release("studio", k1=k1g)
    k1b = g.clone("beelink")
    e_own = raises(lambda: A.for_worker(k1g / "assignment.json", k1g / "amendments.json", "studio", "studio", c0["head"]),
                   A.AssignmentError)
    ok_other = A.for_worker(k1b / "assignment.json", k1b / "amendments.json", "beelink", "beelink", c0["head"])
    e_machine = raises(lambda: A.for_worker(k1b / "assignment.json", k1b / "amendments.json", "beelink", "studio",
                                            c0["head"]), A.AssignmentError)
    check("helpers 10: a scorer pinned before a move refuses once the move changes its own worker's questions, accepts "
          "an amendment that touches only other workers, and refuses a worker on another machine",
          e_own is not None and "moved its questions" in str(e_own) and ok_other["moves_applied"] == 1
          and e_machine is not None, f"{e_own} | {e_machine}")
    # review F1: amendments.json put back to the genesis after the release (git checkout of the file, a stash, a reset)
    good = (k1g / "amendments.json").read_bytes()
    (k1g / "amendments.json").write_bytes(json.dumps({"genesis": json.loads(good)["genesis"], "records": []}).encode())
    e_rb = raises(lambda: A.for_worker(k1g / "assignment.json", k1g / "amendments.json", "studio", "studio",
                                       c0["head"]), A.AssignmentError)
    import subprocess as sp
    wk = sp.run([sys.executable, str(ROOT / "scripts/S451_k1_assign.py"), "worker", "--worker", "studio",
                 "--amendments", str(k1g / "amendments.json"), "--assignment", str(k1g / "assignment.json"), "--fields"],
                capture_output=True, text=True, cwd=ROOT, timeout=120)
    (k1g / "amendments.json").write_bytes(good)
    ok_back = A.for_worker(k1g / "assignment.json", k1g / "amendments.json", "studio", "studio", g.chain()[1]["head"])
    old_ok = A.load(k1g / "assignment.json")
    try:
        sel_items = [{"question_id": q["id"], "config": c, "draw": 1, "answer_key": f"{c}|{q['id']}|d1"}
                     for q in g.base["questions"] for c in g.base["configs"]]
        e_base = raises(lambda: A.select(sel_items, old_ok, "studio", stage=2), A.AssignmentError)
        ok_bee = A.select(sel_items, old_ok, "beelink", stage=2)
        ok_plan = A.select(sel_items, old_ok, "studio", stage=2, base_ok=True)
    except Exception as ex_:                                   # recorded as this check's failure, not a crash
        e_base, ok_bee, ok_plan = None, [], [f"{ex_}"]
    check("helpers 16: after a release, amendments.json put back to the genesis: the scorers' for_worker refuses "
          "(rolled back) and S451 worker reports the fence as rolled-back (the launcher stops); the right chain again "
          "is accepted; a scorer fenced and not released is refused",
          e_rb is not None and "rolled-back" in str(e_rb) and wk.returncode == 0 and " rolled-back:" in wk.stdout
          and ok_back["moves_applied"] == 1 and e_fenced is not None and "unreleased" in str(e_fenced),
          f"{e_rb} | {wk.stdout.strip()[-120:]} {wk.stderr.strip()[-200:]} | {e_fenced}")
    check("helpers 16: a scorer selecting by machine from the base (no --worker) is refused for a machine a move of "
          "the chain beside it names (studio, the source: it would score its moved question again), accepted for one "
          "no move names (beelink), and a planning read (base_ok) is accepted (review F2)",
          e_base is not None and "--worker" in str(e_base) and len(ok_bee) == 2 and len(ok_plan) == 4,
          f"{e_base} | {len(ok_bee)} {ok_plan[:1]}")


def chain_with_helper(worker: str = "studio_11499", port: int = 11499, machine: str = "studio") -> bytes:
    """The committed genesis plus one move of the machine's worker's last question to a new worker on that machine (a
    launcher fixture; signed directly, the fences are not the launcher's concern)."""
    import S451_k1_assign as S451
    doc = json.loads(S451.AMEND.read_text())
    base = A.load(S451.OUT)
    eff = A.effective(base, A.load_chain(S451.AMEND, base))
    q = A.worker_questions(eff, machine)[-1]
    r = {"kind": "move", "seq": 1, "at": "2026-10-18T00:00+02:00", "from": machine, "to": worker,
         "to_defined": {"machine": machine, "port": port, "clone": f"~/projects/mentori-runs-k1-{port}"},
         "stage_filter": None, "questions": [q], "reason": "launcher check", "fence_from": {"fence_id": "f" * 64},
         "fence_to": None, "prev": doc["genesis"]["genesis_sha256"]}
    r["amendment_sha256"] = A.record_sha256(r)
    doc["records"] = [r]
    return (json.dumps(doc, indent=1) + "\n").encode()


def check_helpers_launchers(tmp: Path) -> None:
    """Tests 11 (launcher side) and 13: the committed launchers against the stubs, with a worker."""
    from experiments.runner import server_users as U
    amd = chain_with_helper()
    r = run_launcher(tmp, "helper", "studio", "clean", worker="studio_11499", amendments=amd)
    surveys = [e["args"] for e in r["trace"] if e["tool"] == "server_users" and e["cmd"] == "survey"]
    scorers = [e for e in r["trace"] if e["tool"] == "scorer"]
    posts = [e.get("msg") or "" for e in r["trace"] if e["tool"] == "curl"]
    head = json.loads(amd)["records"][0]["amendment_sha256"]
    out = r["repo"] / "findings/recompute/K1/studio_11499"
    check("helpers 13: run_k1_studio.sh studio_11499 runs to the end on the worker the chain defines: port 11499, "
          "clone ~/projects/mentori-runs-k1-11499, OUT, ledger own_11499.json and rows under K1/studio_11499, "
          "JOB_PATTERN the worker's own K1/studio_11499/ (D89 A2, Q1), both scorers given --worker, --amendments and "
          "the pinned head, ntfy posts naming the worker",
          r["rc"] == 0 and len(surveys) == 4 and all(
              s[s.index("--base") + 1] == "http://127.0.0.1:11499" and s[s.index("--ledger") + 1].endswith(
                  "K1/studio_11499/own_11499.json") and s[s.index("--job-pattern") + 1] == "K1/studio_11499/" for s in surveys)
          and len(scorers) == 4 and all(e["args"][e["args"].index("--worker") + 1] == "studio_11499"
                                        and e["args"][e["args"].index("--amendments-head") + 1] == head
                                        and e["args"][e["args"].index("--machine") + 1] == "studio" for e in scorers)
          and (out / "ragchecker/ragchecker.jsonl").exists() and (out / "own_11499.json").exists()
          and "K1 studio_11499 stage 2 done" in posts and not (out / ".launcher").exists(),
          f"rc {r['rc']} {r['stdout'][-300:]}".replace("\n", " | "))

    def refusal(name, why, **kw):
        rr = run_launcher(tmp, name, kw.pop("machine", "studio"), "clean", **kw)
        return rr["rc"] == 1 and steps(rr) == [] and why in rr["stdout"] and not any(
            e["tool"] == "dry_run" for e in rr["trace"]), f"{name}: rc {rr['rc']} {rr['stdout'][-240:]}".replace("\n", " | ")

    def other_clone(repo):
        test_repo(repo.parent / "elsewhere")
    cases = {
        "clone": refusal("h_clone", "worker studio's clone is ~/projects/mentori-runs-k1", prepare=other_clone,
                         extra_env={"K1_REPO": str(tmp / "launch_h_clone" / "home/projects/elsewhere")}),
        "port": refusal("h_port", "worker studio's port is 11441", port="11442"),
        "unknown": refusal("h_unknown", "is not in the registry", worker="studio_11500"),
        "tracked": refusal("h_tracked", "tracked files differ from HEAD",
                           prepare=lambda repo: (repo / "tracked.txt").write_text("changed\n")),
        "fenced": refusal("h_fenced", "is fenced (unreleased:", prepare=lambda repo: (
            repo / "findings/recompute/K1/studio/fence.json").write_text(json.dumps({"fence_id": "c" * 64}))),
    }
    bee = run_launcher(tmp, "h_bee", "beelink", "clean", args=["laptop_11500"])
    cases["beelink worker"] = (bee["rc"] == 1 and "is not beelink or beelink_<port>" in bee["stdout"],
                               bee["stdout"][-200:].replace("\n", " | "))
    bee2 = run_launcher(tmp, "h_bee2", "beelink", "clean", args=["beelink_11434"])
    cases["beelink helper on 11434"] = (bee2["rc"] == 1 and "11434 is the beelink worker's server" in bee2["stdout"],
                                        bee2["stdout"][-200:].replace("\n", " | "))
    check("helpers 13: a launcher refuses, before any dry run or load, a clone that is not the worker's, a port that is "
          "not its, a worker the chain does not define, a modified tracked file, an unreleased fence, and on the "
          "Beelink a worker that is not beelink or beelink_<port>, or a helper on the app's 11434",
          all(v[0] for v in cases.values()),
          "; ".join(f"{k}: {v[1]}" for k, v in cases.items() if not v[0]))
    ok_amd = run_launcher(tmp, "h_amd", "studio", "clean", prepare=lambda repo: (
        repo / "findings/recompute/K1/amendments.json").write_bytes(amd))
    check("helpers 13: amendments.json checked out from a later commit (the only tracked file allowed to differ) runs; "
          "the studio worker then pins the new head", ok_amd["rc"] == 0 and all(
              e["args"][e["args"].index("--amendments-head") + 1] == head for e in ok_amd["trace"] if e["tool"] == "scorer"),
          ok_amd["stdout"][-200:].replace("\n", " | "))
    held = run_launcher(tmp, "h_held", "studio", "clean", prepare=lambda repo: (
        repo / "findings/recompute/K1/studio/.launcher").mkdir())
    check("helpers 11: a launcher refuses to score while a lock is held (a fence's or another launcher's): dry runs, "
          "then a stop before any busy check or load", held["rc"] == 1 and steps(held) == []
          and "another K1 launcher or a fence holds" in held["stdout"]
          and len([e for e in held["trace"] if e["tool"] == "dry_run"]) == 4, held["stdout"][-200:].replace("\n", " | "))
    lines = ("    1     0 /sbin/launchd\n"
             " 7001     1 /x/python3 experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11451 --run r "
             "--out findings/recompute/K1/studio_11451/ragchecker --assignment findings/recompute/K1/assignment.json "
             "--machine studio --worker studio_11451\n")
    naming = " 7002     1 /x/python3 exp_01.py --ollama-url http://127.0.0.1:11441\n"
    orphan = " 7003     1 /x/python3 experiments/scorers/ragchecker_run.py --out findings/recompute/K1/studio/ragchecker\n"
    pat = job_pattern("studio")
    u1 = U.processes(11441, pat, lines, 999999)[0]
    u2 = U.processes(11441, pat, lines + naming, 999999)[0]
    u3 = U.processes(11441, pat, lines + orphan, 999999)[0]
    u_old = U.processes(11441, r"K1/assignment\.json", lines, 999999)[0]
    check("helpers 13 (D89 A2, Q1): the Studio launcher's JOB_PATTERN is the worker's own K1/studio/, under which "
          "another worker's scorer is not a user of 11441 (the pattern before D89, K1/assignment\\.json, made it one: "
          "two Studio workers blocked each other), a process naming 11441 is, and so is an orphaned scorer of the "
          "studio worker", pat == "K1/studio/" and u1 == [] and [u["pid"] for u in u2] == [7002]
          and [u["pid"] for u in u3] == [7003] and [u["pid"] for u in u_old] == [7001], pat)


def check_helpers_suggest(tmp: Path) -> None:
    """Test 14: suggest on canned progress."""
    import S451_k1_assign as S451
    f = HFix(tmp, "sug", laptop_start="2026-10-25T12:00:00+02:00")      # the laptop starts late: a free port is first
    h1, h2, h3, h4, h5 = f.h
    prog = f.home / "progress"
    prog.mkdir()
    rows = {"ragchecker": [hrow(h1, c, wall=36000.0) for c in ("single_pass", "multi_hop")], "ragas": []}
    (prog / "studio.json").write_text(json.dumps(S451.progress_doc("studio", "studio", rows, {h1, h2}, None, NOW)))
    (prog / "beelink.json").write_text(json.dumps(S451.progress_doc("beelink", "beelink", {"ragchecker": [], "ragas": []},
                                                                    set(), None, NOW)))
    before = (f.k1 / "amendments.json").read_bytes()
    a = S451.suggest(prog, ["studio:11499"], 12.0, k1=f.k1, now=dt_(NOW))
    b = S451.suggest(prog, ["studio:11499"], 12.0, k1=f.k1, now=dt_(NOW))
    none = S451.suggest(prog, ["studio:11499"], 1000.0, k1=f.k1, now=dt_(NOW))
    moved = [q for p in a["proposals"] for q in p["questions"]]
    gains = [(max(dt_(v) for v in p["ends_before"].values()) - max(dt_(v) for v in p["ends_after"].values()))
             .total_seconds() / 3600 for p in a["proposals"]]
    check("helpers 14: suggest on canned progress gives the same output twice, writes nothing (amendments.json's bytes "
          "unchanged), proposes moves (to the free Studio port as a new worker, to an existing worker with its fence) "
          "that each lower the later of their two workers' ends by at least the minimum gain, each worker in one pair "
          "of the round at most (a fence serves one move), never a question begun (h1, h2), and none under a gain it "
          "cannot reach",
          json.dumps(a, default=str) == json.dumps(b, default=str) and (f.k1 / "amendments.json").read_bytes() == before
          and a["proposals"] and all(g >= 12.0 for g in gains) and not set(moved) & {h1, h2}
          and none["proposals"] == [] and any(p["to"] == "studio_11499" and "--new" in p["command"] for p in a["proposals"])
          and all(("--new" in p["command"]) != ("--fence-to" in p["command"]) for p in a["proposals"])
          and len({w for p in a["proposals"] for w in (p["from"], p["to"])}) == 2 * len(a["proposals"]),
          json.dumps({"proposals": [(p["from"], p["to"], p["questions"], p["gain_h"]) for p in a["proposals"]],
                      "notes": a["notes"][:3]}))


def check_helpers_procs_and_lock(tmp: Path) -> None:
    """Review fixes: the stop shares the fence's matcher (k1_procs.py), never matches its own shell, stops a launcher
    and its scorer for real and lists the clone's other processes; S451 check does not fail on a later LOCK.toml, the
    launcher's lookup refuses it with that reason."""
    import os
    import signal
    import subprocess
    import time
    import S451_k1_assign as S451
    P = S451.P
    # the Beelink's processes as read on 17 October at about 18:40 (ps -eo pid,ppid,args), and the stop's own shell
    seen = [(44215, 1, "bash -c export PATH=$HOME/.local/bin:$PATH; cd ~/projects/mentori-runs && nohup bash "
                       "findings/recompute/K1/run_k1_beelink.sh > findings/recompute/K1/run_k1_beelink.out 2>&1 < "
                       "/dev/null & sleep 90; tail -5 ~/projects/mentori-runs/findings/recompute/K1/run_k1_beelink.out"),
            (44217, 44215, "bash findings/recompute/K1/run_k1_beelink.sh"),
            (44328, 44217, "uv run --script experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11434 --out "
                           "findings/recompute/K1/beelink/ragchecker --assignment findings/recompute/K1/assignment.json"),
            (44339, 44328, "/home/valeriob/.cache/uv/environments-v2/x/bin/python3 experiments/scorers/ragchecker_run.py "
                           "--out findings/recompute/K1/beelink/ragchecker"),
            (50000, 1, "bash run_rc_deferred.sh"),
            (60001, 1, "sshd: valeriob@notty"),
            (60002, 60001, "bash -c cd ~/projects/mentori-runs && uv run --no-project python - --worker beelink "
                           "--machine beelink --stop # pkill -f findings/recompute/K1/beelink/ run_k1_beelink.sh"),
            (60003, 60002, "uv run --no-project python - --worker beelink --machine beelink --stop"),
            (60004, 60003, "python - --worker beelink --machine beelink --stop")]
    own = P.own_tree(seen, 60004)
    got = P.naming(seen, own, "beelink", "beelink")
    helper = P.naming(seen + [(7, 1, "bash findings/recompute/K1/run_k1_studio.sh studio_11451")], set(), "studio",
                      "studio")
    check("helpers 17: the stop and the fence share one matcher (S451 imports k1_procs.py); on the Beelink's processes "
          "it finds the ssh start's wrapper, the launcher and the scorer with its uv parent, never its own shell (whose "
          "command line names both patterns: what pkill -f matched on Linux), and not R0's filler; a helper's launcher "
          "is not the studio worker's",
          S451.naming is P.naming and S451.launcher_worker is P.launcher_worker
          and [u["pid"] for u in got] == [44215, 44217, 44328, 44339]
          and [u["launcher"] for u in got] == [True, True, False, False] and helper == [], json.dumps(got)[:300])
    # for real: a launcher and a scorer of a worker no real process can be, and another process run from the clone
    d = tmp / "procs"
    clone = d / "clone"
    (clone / "findings/recompute/K1").mkdir(parents=True)
    W = "chk_k1_procs_w"
    launcher = clone / "findings/recompute/K1/run_k1_laptop.sh"
    launcher.write_text("while true; do sleep 1; done\n")
    py = sys.executable
    procs = [subprocess.Popen(["bash", str(launcher), W], cwd=d, start_new_session=True),
             subprocess.Popen([py, "-c", "import time; time.sleep(300)", f"--out=findings/recompute/K1/{W}/ragchecker"],
                              cwd=d, start_new_session=True),
             subprocess.Popen([py, "-c", "import time; time.sleep(300)", "other-job-of-the-clone"], cwd=clone,
                              start_new_session=True)]
    try:
        time.sleep(1.0)
        src = (ROOT / "findings/recompute/K1/k1_procs.py").read_bytes()
        run = lambda *x: subprocess.run([py, "-", "--worker", W, "--machine", "laptop", "--clone", str(clone), *x],  # noqa: E731
                                        input=src, capture_output=True, cwd=clone, timeout=120)
        listed = run()
        stopped = run("--stop", "--wait", "10")
        time.sleep(0.5)
        alive = [p.poll() is None for p in procs]
        os.kill(procs[2].pid, signal.SIGTERM)
        procs[2].wait(timeout=10)
        free = run()
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
    out = [x.stdout.decode() for x in (listed, stopped, free)]
    check("helpers 17: k1_procs.py from stdin (as on a clone still on c7ad841) lists a worker's launcher and scorer "
          "(exit 1); --stop ends both with SIGTERM, launcher first, and leaves the clone's other process, which it "
          "lists (exit 2: no checkout); once that has ended it reports the clone free (exit 0); it never matched its "
          "own process, whose working directory is the clone",
          listed.returncode == 1 and "WORKER RUNNING: 2" in out[0] and stopped.returncode == 2
          and "SIGTERM to launchers" in out[1] and "CLONE BUSY: 1" in out[1] and alive == [False, False, True]
          and free.returncode == 0 and "FREE" in out[2],
          f"rc {listed.returncode} {stopped.returncode} {free.returncode} alive {alive} | "
          f"{out[1][-300:]} {stopped.stderr.decode()[-200:]}".replace("\n", " | "))
    # review defect 5: a later LOCK.toml does not fail S451 check; the launcher's lookup refuses with that reason
    other = tmp / "LOCK_later.toml"
    other.write_bytes(S451.LOCK_FILE.read_bytes() + b"\n# a later row\n")
    saved = S451.LOCK_FILE
    try:
        S451.LOCK_FILE = other
        base = A.load(S451.OUT)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            why = S451.check_chain(base)
        with contextlib.redirect_stdout(io.StringIO()) as wbuf:
            rc_w = S451.cmd_worker(types.SimpleNamespace(worker="studio", amendments=str(S451.AMEND),
                                                         assignment=str(S451.OUT), fields=True))
    finally:
        S451.LOCK_FILE = saved
    check("helpers 17: with a later LOCK.toml, S451 check's chain part does not fail (it prints the genesis lock and "
          "the file's) and S451 worker, the launcher's lookup, refuses naming the lock (review defect 5)",
          why == [] and "a K1 worker refuses to start in this tree" in buf.getvalue() and rc_w == 1
          and "K1 runs under" in wbuf.getvalue(), f"{why} | {wbuf.getvalue().strip()[:200]}")


# ---------------------------------------------------------------- D89 (Valerio, 17 October evening): K1 O2, a stop
# between answers; A2 / Q1, the busy guard per worker on every machine (two K1 workers on one machine).

def check_d89_graceful(tmp: Path, sinks: list, asg_path: Path, qs: tuple) -> None:
    """K1 O2: both scorers finish the answer in flight, exit 5 before the next and resume there; the launcher treats it
    as a clean stop; k1_procs.py --graceful touches the file and waits, and refuses a clone without the stop."""
    import os
    import subprocess
    import time
    qa, qb, qf, qn = qs
    want = [(qa, "single_pass"), (qa, "multi_hop"), (qf, "single_pass"), (qf, "multi_hop")]
    # RAGChecker
    ev: list = []
    fake, Evaluator = fake_ragchecker(None, ev)
    out = tmp / "rc_grace"
    out.mkdir()
    stopf = out / ".stop_after_answer"

    class Touching(Evaluator):
        def evaluate(self, res, metrics):
            super().evaluate(res, metrics)
            if len(ev) == 1:
                stopf.touch()                    # the coordinator, while the first answer is in flight

    with modules({"ragchecker": fake, "ragchecker.metrics": fake.metrics}):
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        gt = tmp / "gt.json"
        refs = {q: "the reference" for q in qs}
        lock = types.SimpleNamespace(sha256="LOCKSHA")
        call = types.SimpleNamespace(digest="d", options={}, fields=[])

        def ns(o, **kw):
            base = dict(run=list(sinks), store=None, rows=None, limit=None, gt=gt, out=o, base="none", order="claims",
                        assignment=asg_path, machine="studio", stop_on_failed=True, dry_run=False, stop_file=stopf)
            return types.SimpleNamespace(**{**base, **kw})

        cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0}
        with contextlib.redirect_stdout(io.StringIO()) as b1:
            rc1 = rr.score_run(ns(out), Touching(), dict(cur), lock, "m", call, False, out / "ragchecker.jsonl", refs)
        rows1 = [json.loads(ln) for ln in (out / "ragchecker.jsonl").read_text().splitlines()]
        n1 = len(ev)
        stopf.unlink()                           # the launcher removes it when it stops (k1_lib.sh paused)
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = rr.score_run(ns(out), Evaluator(), dict(cur), lock, "m", call, False, out / "ragchecker.jsonl", refs)
        rows2 = [json.loads(ln) for ln in (out / "ragchecker.jsonl").read_text().splitlines()]
        out2 = tmp / "rc_grace_nofile"
        out2.mkdir()
        stopf.touch()
        with contextlib.redirect_stdout(io.StringIO()):
            rc3 = rr.score_run(ns(out2, stop_file=None), Evaluator(), dict(cur), lock, "m", call, False,
                               out2 / "ragchecker.jsonl", refs)
        stopf.unlink()
        rows3 = (out2 / "ragchecker.jsonl").read_text().splitlines()
        refused = raises(lambda: rr.k1_args(types.SimpleNamespace(**{**vars(ns(out)), "run": None, "arm": Path("x"),
                                                                       "assignment": None, "machine": None})), SystemExit)
    check("D89 K1 O2 ragchecker --stop-file: the file touched during the first answer: that answer is finished and "
          "written (status ok), then exit 5 before the next with 'STOPPED BETWEEN ANSWERS'; the next session resumes "
          "at the second answer and ends with the four answers once each; without --stop-file the file is not looked "
          "for; --stop-file without --run is refused",
          rc1 == rr.STOP_EXIT == 5 and n1 == 1 and [r["status"] for r in rows1] == ["ok"]
          and "RAGCHECKER STOPPED BETWEEN ANSWERS" in b1.getvalue() and rc2 == 0
          and [(r["question_id"], r["config"]) for r in rows2] == want and len(ev) == 8
          and rc3 == 0 and len(rows3) == 4 and refused is not None,
          f"rc {rc1} {rc2} {rc3}, rows {len(rows1)} {len(rows2)} {len(rows3)}, evaluated {n1} then {len(ev)}")
    # RAGAS
    S = importlib.import_module("S357_ragas")
    from experiments.runner.lock import load
    lk = load()
    rstop = tmp / "ragas_grace" / ".stop_after_answer"
    seen: list = []

    async def score_row(row, ref, metrics, sem, transport=None):
        seen.append((row["question_id"], row["config"]))
        if len(seen) == 1:
            rstop.parent.mkdir(parents=True, exist_ok=True)
            rstop.touch()
        names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "factual_correctness")
        return {"question_id": row["question_id"], "config": row["config"], "scores": {m: 0.5 for m in names},
                "errors": {}, "wall_s": {m: 1.0 for m in names}, "n_contexts": len(row["contexts"]), "context_chars": 0,
                "at": "T", "transport_failures": []}

    stub = types.SimpleNamespace(call=types.SimpleNamespace(options={"temperature": 0, "num_predict": 16384},
                                                            lock_sha256=lk.sha256, digest="d", fields=[]))
    ragas = types.ModuleType("ragas")
    ragas.__version__ = "stub"
    llms, embs, mets = (types.ModuleType(n) for n in ("ragas.llms", "ragas.embeddings", "ragas.metrics"))
    llms.llm_factory = lambda *a, **k: "llm"
    embs.OpenAIEmbeddings = lambda **k: "emb"
    mets.collections = types.SimpleNamespace(**{n: (lambda **k: n) for n in (
        "Faithfulness", "AnswerRelevancy", "ContextPrecisionWithReference", "ContextRecall", "FactualCorrectness")})
    saved = {k: getattr(S, k) for k in ("score_row", "lock_client", "ollama_show", "ollama_version")}
    S.score_row, S.lock_client = score_row, (lambda m, e, p: (None, stub))
    S.ollama_show, S.ollama_version = (lambda m: {"model": m}), (lambda: "stub")
    rout = tmp / "ragas_grace" / "ragas.jsonl"
    a = types.SimpleNamespace(run=[str(x) for x in sinks], gt=str(tmp / "gt.json"), store=None, out=str(rout), key=None,
                              concurrency=1, assignment=str(asg_path), machine="studio", limit=None, dry_run=False,
                              llm=None, embedding=None, stop_file=str(rstop))
    try:
        with modules({"ragas": ragas, "ragas.llms": llms, "ragas.embeddings": embs, "ragas.metrics": mets}):
            with contextlib.redirect_stdout(io.StringIO()) as b1:
                g1 = asyncio.run(S.main_run_async(a))
            r1 = [json.loads(ln) for ln in rout.read_text().splitlines()]
            m1 = len(seen)
            rstop.unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                g2 = asyncio.run(S.main_run_async(a))
            r2 = [json.loads(ln) for ln in rout.read_text().splitlines()]
    finally:
        S.RUN_MACHINE = S.RUN_STAGE = None
        for k, v in saved.items():
            setattr(S, k, v)
    check("D89 K1 O2 ragas --run --stop-file: the first answer finished and written, exit 5 before the next ('RAGAS "
          "--run STOPPED BETWEEN ANSWERS'); the next session resumes and ends with the four answers once each",
          g1 == S.RUN_STOP_EXIT == 5 and m1 == 1 and len(r1) == 1 and r1[0]["status"] == "ok"
          and "STOPPED BETWEEN ANSWERS" in b1.getvalue() and g2 == 0
          and [(r["question_id"], r["config"]) for r in r2] == want and len(seen) == 4,
          f"rc {g1} {g2}, rows {len(r1)} {len(r2)}, scored {m1} then {len(seen)}")
    # the launcher
    r = run_launcher(tmp, "grace", "studio", "graceful")
    st, posts = steps(r), [e.get("msg") or "" for e in r["trace"] if e["tool"] == "curl"]
    scorer_args = [e["args"] for e in r["trace"] if e["tool"] == "scorer"]
    check("D89 K1 O2 launcher: RAGChecker exits 5 between answers: the launcher prints PAUSED, removes the stop file and "
          "its lock, exits 0, starts no further pass (one fresh load, no RAGAS) and posts no failure (only the pass's "
          "start); the scorer was given --stop-file $OUT/.stop_after_answer",
          r["rc"] == 0 and "PAUSED: stopped between answers" in r["stdout"] and st.count("job:fresh-load") == 1
          and not any(x.startswith("scorer:ragas") for x in st) and not (r["out"] / ".stop_after_answer").exists()
          and not (r["out"] / ".launcher").exists() and len(posts) == 1 and "started" in posts[0]
          and scorer_args and scorer_args[0][scorer_args[0].index("--stop-file") + 1]
          == "findings/recompute/K1/studio/.stop_after_answer",
          f"rc {r['rc']} {st} posts {posts} {r['stdout'][-200:]}".replace("\n", " | "))
    pre = lambda repo: (repo / "findings/recompute/K1/studio/.stop_after_answer").touch()  # noqa: E731
    r = run_launcher(tmp, "grace_pre", "studio", "clean", prepare=pre)
    posts = [e.get("msg") or "" for e in r["trace"] if e["tool"] == "curl"]
    rd = run_launcher(tmp, "grace_pre_dry", "studio", "clean", prepare=pre, dry=True)
    check("D89 K1 O2 launcher: a stop file present at the start (a request no running worker consumed, review F1): the "
          "scoring run refuses before any check, load or pass, posts it (never a silent pause), exits 1 and keeps the "
          "file; a dry run says the scoring run would refuse and still exits 0",
          r["rc"] == 1 and steps(r) == [] and "exists at the start" in r["stdout"] and "PAUSED" not in r["stdout"]
          and (r["out"] / ".stop_after_answer").exists() and len(posts) == 1 and "stop file present at start" in posts[0]
          and rd["rc"] == 0 and "the scoring run would refuse to start" in rd["stdout"],
          f"rc {r['rc']} {rd['rc']} posts {posts} {r['stdout'][-300:]}".replace("\n", " | "))
    # k1_procs.py --graceful, for real
    d = tmp / "grace_procs"
    clone = d / "clone"
    k1 = clone / "findings/recompute/K1"
    k1.mkdir(parents=True)
    (k1 / "k1_lib.sh").write_text("STOPFILE=$OUT/.stop_after_answer\n")
    W = "chk_k1_grace_w"
    sf = f"findings/recompute/K1/{W}/.stop_after_answer"
    launcher = k1 / "run_k1_laptop.sh"
    launcher.write_text(f"while [ ! -e {sf} ]; do sleep 0.2; done; sleep 1; exit 0\n")
    py = sys.executable
    wait_code = f"import os, time\nwhile not os.path.exists('{sf}'): time.sleep(0.2)\ntime.sleep(1.5)"
    procs = [subprocess.Popen(["bash", str(launcher), W], cwd=clone, start_new_session=True),
             subprocess.Popen([py, "-c", wait_code, "experiments/scorers/ragchecker_run.py",
                               f"--out=findings/recompute/K1/{W}/ragchecker"], cwd=clone, start_new_session=True)]
    src = (ROOT / "findings/recompute/K1/k1_procs.py").read_bytes()
    run = lambda c, *x: subprocess.run([py, "-", "--worker", W, "--machine", "laptop", "--clone", str(c), *x],  # noqa: E731
                                       input=src, capture_output=True, cwd=c, timeout=120)
    try:
        time.sleep(1.0)
        g = run(clone, "--graceful", "--poll", "0.3", "--graceful-wait", "30")
        codes = [p.wait(timeout=10) for p in procs]
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
    old = d / "old"
    (old / "findings/recompute/K1").mkdir(parents=True)
    (old / "findings/recompute/K1/k1_lib.sh").write_text("# c7ad841's launcher: no stop file\n")
    stubborn = subprocess.Popen([py, "-c", "import time; time.sleep(60)", "scripts/S357_ragas.py",
                                 f"--out=findings/recompute/K1/{W}/ragas"], cwd=old, start_new_session=True)
    try:
        time.sleep(0.5)
        g_old = run(old, "--graceful")
        touched_old = (old / sf).exists()
        (old / "findings/recompute/K1/k1_lib.sh").write_text("STOPFILE=$OUT/.stop_after_answer\n")
        g_to = run(old, "--graceful", "--poll", "0.3", "--graceful-wait", "2")
        alive = stubborn.poll() is None
        kept = (old / sf).exists()
        g_hard = run(old, "--stop", "--wait", "5")          # review F1: after the timeout, --stop removes the file
        hard_gone = stubborn.wait(timeout=10) is not None and not (old / sf).exists()
    finally:
        if stubborn.poll() is None:
            stubborn.kill()
    # review F2: a process that only names the worker's folder (a tail -f of its log) is not waited for
    tl = d / "tail"
    (tl / "findings/recompute/K1").mkdir(parents=True)
    (tl / "findings/recompute/K1/k1_lib.sh").write_text("STOPFILE=$OUT/.stop_after_answer\n")
    (tl / "findings/recompute/K1/run_k1_laptop.sh").write_text(launcher.read_text())
    tail = subprocess.Popen([py, "-c", "import time; time.sleep(60)", f"findings/recompute/K1/{W}/ragchecker.log"],
                            cwd=tl, start_new_session=True)
    lt = subprocess.Popen(["bash", str(tl / "findings/recompute/K1/run_k1_laptop.sh"), W], cwd=tl,
                          start_new_session=True)
    try:
        time.sleep(0.5)
        t0 = time.time()
        g_tail = run(tl, "--graceful", "--poll", "0.3", "--graceful-wait", "20")
        tail_s, tail_alive = time.time() - t0, tail.poll() is None
    finally:
        for x in (tail, lt):
            if x.poll() is None:
                x.kill()
    out_g = g.stdout.decode()
    check("D89 K1 O2 k1_procs.py --graceful (real processes): touches the worker's stop file, waits while the answer in "
          "flight ends (the launcher and the scorer exit by themselves, code 0, no signal), removes the file, reports "
          "FREE (exit 0); on a clone whose k1_lib.sh has no stop file (c7ad841) it refuses (exit 4) and touches "
          "nothing; on a timeout it exits 1, the file stays and nothing is signalled",
          g.returncode == 0 and "STOPPED BETWEEN ANSWERS" in out_g and "FREE" in out_g and codes == [0, 0]
          and not (clone / sf).exists() and g_old.returncode == 4 and "REFUSED" in g_old.stdout.decode()
          and not touched_old and g_to.returncode == 1 and "TIMEOUT" in g_to.stdout.decode() and kept
          and alive, f"rc {g.returncode} codes {codes} | old {g_old.returncode} | timeout {g_to.returncode} alive {alive} | "
          f"{out_g[-200:]}".replace("\n", " | "))
    out_t = g_tail.stdout.decode()
    check("D89 K1 O2 k1_procs.py (review F1, F2): after a --graceful timeout, --stop stops the worker and removes the "
          "stop file it left, so the next start does not meet it (exit 0, FREE); a process that only names the worker's "
          "folder (a tail -f of its log) is not waited for: --graceful reports the stop once the launcher has ended "
          "(well inside its 20 s), removes the file, leaves that process alone and lists it (exit 1, WORKER RUNNING)",
          g_hard.returncode == 0 and "removed" in g_hard.stdout.decode() and hard_gone
          and "STOPPED BETWEEN ANSWERS" in out_t and g_tail.returncode == 1 and "WORKER RUNNING" in out_t
          and tail_s < 10 and tail_alive and not (tl / sf).exists(),
          f"hard {g_hard.returncode} gone {hard_gone} | tail rc {g_tail.returncode} {tail_s:.1f} s alive {tail_alive} | "
          f"{out_t[-200:]}".replace("\n", " | "))


def check_d89_guard(tmp: Path) -> None:
    """A2 / Q1: the busy guard counts only a worker's own K1 processes, on every machine; any other job still blocks."""
    from experiments.runner import server_users as U
    bee_main = (" 7101     1 /x/python3 experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11434 --out "
                "findings/recompute/K1/beelink/ragchecker --assignment findings/recompute/K1/assignment.json --machine "
                "beelink --worker beelink\n")
    bee_help = (" 7102     1 uv run --script scripts/S357_ragas.py --run r --out findings/recompute/K1/beelink_11435/ragas/"
                "ragas.jsonl --assignment findings/recompute/K1/assignment.json --machine beelink --worker beelink_11435\n")
    bee_help_rc = (" 7103     1 /x/python3 experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11435 --out "
                   "findings/recompute/K1/beelink_11435/ragchecker --assignment findings/recompute/K1/assignment.json\n")
    stranger = " 7104     1 /usr/bin/python3 experiments/mentori/publication/scripts/exp_03_rlm.py --x 1\n"
    judge = " 7105     1 /x/python3 -m experiments.scorers.judge_passages --run r\n"
    lap_s2 = " 7106     1 bash findings/recompute/S2_launch_laptop/run_s2_laptop.sh ollama::x default\n"
    lap_other = " 7107     1 /x/python3 scripts/S357_ragas.py --out findings/recompute/K1/laptop_2/ragas/ragas.jsonl\n"
    lap_own = " 7108     1 /x/python3 scripts/S357_ragas.py --out findings/recompute/K1/laptop/ragas/ragas.jsonl\n"
    root = "    1     0 /sbin/launchd\n"
    pid = lambda port, pat, lines: [u["pid"] for u in U.processes(port, pat, root + lines, 999999)[0]]  # noqa: E731
    pb, ph, pl = job_pattern("beelink"), job_pattern("beelink", "beelink_11435"), job_pattern("laptop")
    old_b = pb.split("|findings/recompute/K1/")[0].replace("^(?!.*findings/recompute/K1/).*", "")
    got = {"beelink sees the helper's two scorers": pid(11434, pb, bee_help + bee_help_rc),
           "beelink_11435 sees the beelink worker's scorer": pid(11435, ph, bee_main),
           "beelink: a stranger (exp_03, judge_passages)": pid(11434, pb, stranger + judge),
           "beelink_11435: a stranger (exp_03, judge_passages)": pid(11435, ph, stranger + judge),
           "beelink: its own orphaned scorer": pid(11434, pb, bee_main),
           "beelink_11435: its own orphaned scorers": pid(11435, ph, bee_help + bee_help_rc),
           "laptop: another K1 worker; S2; its own": (pid(11434, pl, lap_other), pid(11434, pl, lap_s2),
                                                      pid(11434, pl, lap_own)),
           "the Beelink's pattern before D89 sees the helper's scorers": pid(11434, old_b, bee_help + bee_help_rc)}
    want = {"beelink sees the helper's two scorers": [],
            "beelink_11435 sees the beelink worker's scorer": [],
            "beelink: a stranger (exp_03, judge_passages)": [7104, 7105],
            "beelink_11435: a stranger (exp_03, judge_passages)": [7104, 7105],
            "beelink: its own orphaned scorer": [7101],
            "beelink_11435: its own orphaned scorers": [7102, 7103],
            "laptop: another K1 worker; S2; its own": ([], [7106], [7108]),
            "the Beelink's pattern before D89 sees the helper's scorers": [7102, 7103]}
    bad = {k: got[k] for k in want if got[k] != want[k]}
    check("D89 A2 / Q1 busy guard (Beelink and laptop patterns as the launchers export them): another K1 worker's "
          "processes on the machine are not users, a job script that is not a K1 worker's is (for either Beelink "
          "server: it may not name its port), the worker's own orphaned scorer is; the Beelink's pattern before D89 "
          "made the other worker's scorers users", not bad, json.dumps(bad) + " " + pb)
    amd = chain_with_helper("beelink_11435", 11435, "beelink")
    r1 = run_launcher(tmp, "d89_bee_helper", "beelink", "clean", worker="beelink_11435", amendments=amd,
                      extra_env={"K1STUB_PS_EXTRA": bee_main})
    sv = [e["args"] for e in r1["trace"] if e["tool"] == "server_users" and e["cmd"] == "survey"]
    r2 = run_launcher(tmp, "d89_bee_main", "beelink", "clean", extra_env={"K1STUB_PS_EXTRA": bee_help + bee_help_rc})
    r3 = run_launcher(tmp, "d89_bee_stranger", "beelink", "clean", extra_env={"K1STUB_PS_EXTRA": stranger})
    r4 = run_launcher(tmp, "d89_studio_two", "studio", "clean", extra_env={"K1STUB_PS_EXTRA": (
        " 7201     1 /x/python3 experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11451 --out "
        "findings/recompute/K1/studio_11451/ragchecker --assignment findings/recompute/K1/assignment.json\n")})
    r5 = run_launcher(tmp, "d89_studio_port", "studio", "clean", extra_env={"K1STUB_PS_EXTRA": (
        " 7202     1 /x/python3 exp_01.py --ollama-url http://127.0.0.1:11441\n")})
    p3 = [e.get("msg") or "" for e in r3["trace"] if e["tool"] == "curl"]
    check("D89 A2 launchers end to end: run_k1_beelink.sh beelink_11435 (server 127.0.0.1:11435, its log server_11435.log, "
          "clone ~/projects/mentori-runs-k1-11435) runs to the end beside the beelink worker's scorer, and the beelink "
          "worker beside the helper's two; a stranger job (exp_03) stops the beelink worker at its first busy check, "
          "with no load; on the Studio a second worker's scorer does not stop the studio worker, a job naming 11441 "
          "does", r1["rc"] == 0 and len(sv) == 4 and all(
              x[x.index("--base") + 1] == "http://127.0.0.1:11435" and x[x.index("--begin-log") + 1]
              == "/mnt/c/Users/Valerio/AppData/Local/Ollama/server_11435.log"
              and x[x.index("--job-pattern") + 1] == ph for x in sv)
          and "K1 beelink_11435 done" in r1["stdout"] and r2["rc"] == 0 and "K1 beelink done" in r2["stdout"]
          and r3["rc"] == 1 and steps(r3) == ["server_users:survey"] and "K1 beelink stopped: another job uses the server" in p3
          and r4["rc"] == 0 and r5["rc"] == 1 and steps(r5) == ["server_users:survey"],
          f"rc {r1['rc']} {r2['rc']} {r3['rc']} {r4['rc']} {r5['rc']} | {r1['stdout'][-200:]} | {sv[:1]}".replace("\n", " | "))


# ---------------------------------------------------------------- D92 Q190: reference claims cut once per question

SIX = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")


def fixture_six(tmp: Path, Q: dict) -> tuple:
    """Six runs (K1's six strategies), draw 1, two answerable questions; an assignment over them (qa studio, qb beelink)."""
    store = tmp / "chroma6"
    make_store(store, {"coll_s20": CHUNKS})
    from experiments.runner import experiment as ex
    qa = Q["answerable"]
    qb = next(q["id"] for q in ex.questions() if R.group_of(q["id"]) == "answerable" and q["id"] != qa)
    sinks = []
    for cfg in SIX:
        sink = tmp / "runs6" / f"exp_01__{cfg}__{INDEX}"
        ii.record(sink, INDEX, "coll_s20", store=store, script="check")
        write_jsonl(sink / "answers.jsonl", [exp01_line(q, 1, f"answer {cfg} {q}", None, ["id-b", "id-a"], config=cfg)
                                             for q in (qa, qb)])
        sinks.append(sink)
    asg = signed({"rule": "fixture6", "rule_sha256": A.sha256("fixture6"), "draws": [1], "configs": list(SIX),
                  "machines": ["studio", "beelink"],
                  "questions": [{"id": qa, "machine": "studio"}, {"id": qb, "machine": "beelink"}], "not_scored": []})
    return sinks, write_asg(tmp / "asg6.json", asg), (qa, qb), store


def claims_dir(d: Path, entries: list[dict]) -> str:
    """A sealed-looking reference claims folder (the file and its MANIFEST.sha256 line); returns the file's sha256."""
    import hashlib
    d.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(e) + "\n" for e in entries).encode()
    (d / "reference_claims.jsonl").write_bytes(body)
    h = hashlib.sha256(body).hexdigest()
    (d / "MANIFEST.sha256").write_text(f"{h}  reference_claims.jsonl\n")
    return h


def claims_entry(rr, qid: str, question: str, reference: str, claims: list, lock, digest: str, **over) -> dict:
    e = {"question_id": qid, "k1_stage": None, "assigned_machine": "studio", "status": "ok",
         "question_sha256": rr.text_sha256(question), "reference_sha256": rr.text_sha256(reference),
         "messages_sha256": "m" * 64, "request_sha256": "r" * 64, "reply_sha256": "p" * 64,
         "text_to_refchecker_sha256": "t" * 64, "claims": claims, "n_claims": len(claims), "cut_machine": "studio",
         "server": "http://127.0.0.1:11441", "model": "devstral-small-2:24b", "model_digest": digest,
         "lock_sha256": lock.sha256, "prompt_tokens": 1, "output_tokens": 1, "wall_s": 1.0, "at": "T", "reproduced": None}
    e.update(over)
    e["entry_sha256"] = rr.entry_sha256(e)
    return e


def check_q190(tmp: Path, Q: dict) -> None:
    """D92 Q190: RAGChecker's --reference-claims. Claims passed for every answer (the library's skip, mimicked by the
    fake evaluator as evaluator.py:104 does it); the same claims for all six answers of a question where per-answer
    cuts differ; every hash refusal before anything is written; resume (stop file, equal claims, other claims refused,
    archive); a library that ignored the claims recorded as failed; the dry run; the launchers; and S462's selftest
    with the real RAGChecker 0.1.9."""
    import os
    import subprocess
    from experiments.runner.lock import load
    sinks, asg_path, (qa, qb), store = fixture_six(tmp, Q)
    lock = load()
    model = lock.d["scorers"]["model"]
    call = lock.ollama(model, role="scorer")
    gt = tmp / "gt6.json"
    refs = {qa: "the reference of qa", qb: "the reference of qb"}
    gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": r} for q, r in refs.items()]}))
    CLAIMS = [["s1", "p1", "o1"], ["s2", "p2", "o2"], ["it's", "a \"quoted\"", "claim"]]
    CLAIMS_B = [["qb subject", "qb predicate", "qb object"], ["s9", "p9", "o9"]]   # qb's own (review T1)

    class Res:
        def __init__(self, d):
            self.results = [types.SimpleNamespace(**{"gt_answer_claims": None, **d["results"][0]})]

        @classmethod
        def from_dict(cls, d):
            return cls(d)

    def evaluator(cur: dict, cuts: list, received: list, ignore: bool = False):
        class Ev:
            def evaluate(self, res, metrics):
                y = res.results[0]
                received.append(copy.deepcopy(y.gt_answer_claims))
                cur["extracts"] = cur.get("extracts", 0) + 1                    # the response's cut
                if y.gt_answer_claims is None or ignore:                        # evaluator.py:104
                    cur["extracts"] += 1
                    cuts.append(y.query_id)
                    y.gt_answer_claims = [["cut", str(len(cuts)), "x"]] * (len(cuts) + 1)   # a cutter that differs
                y.response_claims = [["r", "p", "o"]]
                y.answer2response = y.response2answer = y.retrieved2response = y.retrieved2answer = []
                y.metrics = {"overall_metrics": {"precision": 50.0}}
        return Ev()

    fake = types.ModuleType("ragchecker")
    fake.RAGResults = Res
    fake.metrics = types.ModuleType("ragchecker.metrics")
    fake.metrics.all_metrics = ["all"]
    with modules({"ragchecker": fake, "ragchecker.metrics": fake.metrics}):
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        own = {qa: CLAIMS, qb: CLAIMS_B}
        ent = {q: claims_entry(rr, q, "Q?", refs[q], own[q], lock, call.digest) for q in (qa, qb)}
        cdir = tmp / "claims6"
        h = claims_dir(cdir, list(ent.values()))

        def ns(o, **kw):
            base = dict(run=list(sinks), store=store, rows=None, limit=None, gt=gt, out=o, base="none", order="claims",
                        assignment=asg_path, machine="studio", stop_on_failed=True, dry_run=False, stop_file=None,
                        reference_claims=cdir / "reference_claims.jsonl", reference_claims_sha256=h)
            return types.SimpleNamespace(**{**base, **kw})

        def run(o, ignore=False, **kw):
            o.mkdir(parents=True, exist_ok=True)
            cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0, "batch": 0}
            cuts, received = [], []
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                rc = rr.score_run(ns(o, **kw), evaluator(cur, cuts, received, ignore), cur, lock, model, call, False,
                                  o / "ragchecker.jsonl", refs)
            rows = [json.loads(x) for x in (o / "ragchecker.jsonl").read_text().splitlines()] \
                if (o / "ragchecker.jsonl").exists() else []
            return rc, rows, cuts, received, buf.getvalue()

        # 1. claims passed
        rc, rows, cuts, received, _ = run(tmp / "q190_pass")
        head = json.loads((tmp / "q190_pass" / "ragchecker_headers.jsonl").read_text().splitlines()[-1])
        check("Q190 claims passed: the studio's six answers scored, each given the entry's claims (RAGChecker cut no "
              "reference), each row tagged with the file and entry sha256 and one extraction call, the header naming "
              "the file", rc == 0 and len(rows) == 6 and not cuts and received == [CLAIMS] * 6
              and all(r["status"] == "ok" and r["gt_answer_claims"] == CLAIMS and r["extract_calls"] == 1
                      and r["reference_claims"] == rr.claims_tag({"file_sha256": h}, ent[qa]) for r in rows)
              and head["reference_claims"]["file_sha256"] == h and head["reference_claims"]["entries"] == 2,
              f"rc {rc}, rows {len(rows)}, cuts {len(cuts)}")
        # 1b. each question its own entry (review T1): both questions' twelve answers in one run, no assignment
        rcw, roww, cutw, recw, _ = run(tmp / "q190_own", assignment=None, machine=None)
        byq = {q: [r for r in roww if r["question_id"] == q] for q in (qa, qb)}
        check("Q190 each question its own entry: the twelve answers of two questions with different claims, every row "
              "given its own question's claims and tagged with its own entry's sha256",
              rcw == 0 and len(roww) == 12 and not cutw and all(len(byq[q]) == 6 for q in (qa, qb))
              and all(r["status"] == "ok" and r["gt_answer_claims"] == own[q]
                      and r["reference_claims"]["entry_sha256"] == ent[q]["entry_sha256"]
                      and r["reference_claims"]["n_claims"] == len(own[q]) for q in (qa, qb) for r in byq[q])
              and sorted(map(json.dumps, recw)) == sorted([json.dumps(CLAIMS)] * 6 + [json.dumps(CLAIMS_B)] * 6),
              f"rc {rcw}, rows {len(roww)}, " + ", ".join(f"{q[:12]}: {[r['reference_claims']['entry_sha256'][:8] for r in byq[q]]}"
                                                       for q in (qa, qb)))
        # 2. the same claims for all six answers, where per-answer cuts differ
        rcn, rown, cutn, _, _ = run(tmp / "q190_percut", reference_claims=None, reference_claims_sha256=None)
        check("Q190 the same claims for all six answers: without the file the (differing) cutter gives the six "
              "answers six claim lists; with it all six have the entry's", rcn == 0 and len(cutn) == 6
              and len({json.dumps(r["gt_answer_claims"]) for r in rown}) == 6
              and len({json.dumps(r["gt_answer_claims"]) for r in rows}) == 1 and [r["config"] for r in rows] == list(SIX))
        # 3. refusals on a hash mismatch, each before anything is written
        bad = {}
        bad["pinned sha256"] = dict(reference_claims_sha256="0" * 64)
        man = tmp / "claims_badman"
        claims_dir(man, list(ent.values()))
        (man / "MANIFEST.sha256").write_text(f"{'1' * 64}  reference_claims.jsonl\n")
        bad["manifest"] = dict(reference_claims=man / "reference_claims.jsonl")
        edited = dict(ent[qa], claims=CLAIMS[:1])                       # claims edited, entry_sha256 not
        ed = tmp / "claims_edited"
        bad["entry edited"] = dict(reference_claims=ed / "reference_claims.jsonl",
                                   reference_claims_sha256=claims_dir(ed, [edited, ent[qb]]))
        for name, over in (("reference", dict(reference_sha256=rr.text_sha256("another reference"))),
                           ("question", dict(question_sha256=rr.text_sha256("another question?"))),
                           ("lock", dict(lock_sha256="f" * 64)), ("model digest", dict(model_digest="0" * 64)),
                           ("status", dict(status="no_reference"))):
            d = tmp / f"claims_{name.replace(' ', '_')}"
            e2 = claims_entry(rr, qa, "Q?", refs[qa], CLAIMS, lock, call.digest, **over)
            bad[name] = dict(reference_claims=d / "reference_claims.jsonl", reference_claims_sha256=claims_dir(d, [e2, ent[qb]]))
        d = tmp / "claims_missing_q"
        bad["question missing"] = dict(reference_claims=d / "reference_claims.jsonl",
                                       reference_claims_sha256=claims_dir(d, [ent[qb]]))
        d = tmp / "claims_twice"
        bad["entry twice"] = dict(reference_claims=d / "reference_claims.jsonl",
                                  reference_claims_sha256=claims_dir(d, [ent[qa], ent[qa], ent[qb]]))
        refused = {}
        for name, over in bad.items():
            o = tmp / f"q190_bad_{name.replace(' ', '_')}"
            e = raises(lambda: run(o, **over), SystemExit)
            refused[name] = e is not None and str(e).startswith("REFUSED: ") and not (o / "ragchecker.jsonl").exists() \
                and not (o / "ragchecker_headers.jsonl").exists()
        check("Q190 refusal on a hash mismatch, nothing written: the file's sha256 not the one given, the manifest "
              "naming another, an entry edited after it was hashed, an entry cut from another reference or question "
              "text, under another lock or model digest, not ok, the question missing, an entry twice",
              all(refused.values()), ", ".join(k for k, v in refused.items() if not v) or f"{len(refused)} refused")
        a1 = ns(tmp, reference_claims_sha256=None)
        a2 = ns(tmp, reference_claims=None)
        a3 = ns(tmp, run=None)
        a3.arm = Path("x")
        check("Q190 options: --reference-claims without its sha256, the sha256 alone, and --reference-claims without "
              "--run are refused", all(raises(lambda a=a: rr.k1_args(a), SystemExit) is not None for a in (a1, a2, a3)))
        # 4. resume
        o = tmp / "q190_resume"
        stopf = o / ".stop"
        o.mkdir()
        cur = {"key": None, "n": 0, "checks": 0, "ambiguous": 0, "batch": 0}
        cuts, received = [], []

        class Touch:
            ev = evaluator(cur, cuts, received)

            def evaluate(self, res, metrics):
                self.ev.evaluate(res, metrics)
                stopf.touch()

        with contextlib.redirect_stdout(io.StringIO()):
            rc1 = rr.score_run(ns(o, stop_file=stopf), Touch(), cur, lock, model, call, False, o / "ragchecker.jsonl", refs)
        stopf.unlink()
        rc2, rows2, cuts2, rec2, _ = run(o, stop_file=stopf)
        check("Q190 resume: stopped after the first answer (exit 5), the next session scores the other five with the "
              "same claims, each answer once, no reference cut", rc1 == 5 and rc2 == 0 and len(rows2) == 6
              and [r["config"] for r in rows2] == list(SIX) and len(rec2) == 5 and not cuts and not cuts2
              and all(r["gt_answer_claims"] == CLAIMS for r in rows2))
        rc3, rows3, cuts3, rec3, _ = run(o)
        head = json.loads((o / "ragchecker_headers.jsonl").read_text().splitlines()[-1])
        check("Q190 resume: a finished output resumes with nothing to score, rows tagged by this entry count as done",
              rc3 == 0 and len(rows3) == 6 and not rec3 and head["to_do"] == 0
              and head["reference_claims"]["accepted_by_equal_claims"] == 0)
        eq = tmp / "q190_equal"
        eq.mkdir()
        old = [dict(r) for r in rows2]
        for r in old:
            r.pop("reference_claims")
            r.pop("extract_calls")
        write_jsonl(eq / "ragchecker.jsonl", old)
        rc4, rows4, _, rec4, _ = run(eq)
        head = json.loads((eq / "ragchecker_headers.jsonl").read_text().splitlines()[-1])
        check("Q190 resume: rows written before the file (no tag) whose reference claims equal the entry's count as "
              "done, by equal claims, and the header counts them (the Studio's rows of 17 October)",
              rc4 == 0 and not rec4 and len(rows4) == 6 and head["reference_claims"]["accepted_by_equal_claims"] == 6)
        rcp = tmp / "q190_percut"
        nrows = len((rcp / "ragchecker.jsonl").read_text().splitlines())
        e = raises(lambda: run(rcp), SystemExit)
        check("Q190 resume: rows cut per answer, other than the entry's (the Beelink's), are refused with the archive "
              "pointer, nothing appended", e is not None and "S462_k1_reference_claims.py archive" in str(e)
              and len((rcp / "ragchecker.jsonl").read_text().splitlines()) == nrows)
        oth = tmp / "q190_other_entry"
        oth.mkdir()
        write_jsonl(oth / "ragchecker.jsonl", [dict(r, reference_claims=dict(r["reference_claims"], entry_sha256="9" * 64))
                                               for r in rows2])
        e = raises(lambda: run(oth), SystemExit)
        check("Q190 resume: rows tagged with another entry are refused", e is not None and "another" in str(e))
        S462 = importlib.import_module("S462_k1_reference_claims")
        k1 = tmp / "k1_arch"
        shutil.copytree(rcp, k1 / "beelink" / "ragchecker")
        dst = S462.archive(k1, "beelink", "check_k1", now="20261018T010000Z")
        rc5, rows5, cuts5, _, _ = run(k1 / "beelink" / "ragchecker")
        check("Q190 archive then rescore: S462 archive moves the worker's ragchecker output aside with its hashes, "
              "and the next run scores all six answers again with the entry's claims",
              dst.name == "ragchecker_archived_q190_20261018T010000Z" and (dst / "ARCHIVED.json").exists()
              and rc5 == 0 and len(rows5) == 6 and not cuts5 and all(r["gt_answer_claims"] == CLAIMS for r in rows5))
        # 5. a library that cut the reference anyway
        rc6, rows6, _, _, _ = run(tmp / "q190_ignored", ignore=True)
        check("Q190 guard: a RAGChecker that cut the reference despite the claims gives a failed row (claims changed, "
              "2 extraction calls), and --stop-on-failed stops (exit 4)", rc6 == 4 and len(rows6) == 1
              and rows6[0]["status"] == "failed" and "not used as passed" in rows6[0]["error"]
              and rows6[0]["extract_calls"] == 2)
    # 6. the dry run
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rcd = rr.dry_run(ns(tmp / "q190_dry"))
    dj = json.JSONDecoder().raw_decode(buf.getvalue())[0]
    e = raises(lambda: rr.dry_run(ns(tmp / "q190_dry", reference_claims_sha256="0" * 64)), SystemExit)
    check("Q190 dry run: reports the file and its entries, and refuses a hash mismatch as the run does",
          rcd == 0 and dj["reference_claims"]["file_sha256"] == h and dj["reference_claims"]["entries"] == 2
          and e is not None)
    # 7. the launchers
    r = run_launcher(tmp, "q190_studio", "studio", "clean")
    sc = [t for t in r["trace"] if t["tool"] == "scorer" and t["name"] == "ragchecker"]
    import hashlib
    want = hashlib.sha256(b'{"question_id": "fixture"}\n').hexdigest()
    check("Q190 launcher: both stages' RAGChecker get --reference-claims (the clone's reference_claims folder) with "
          "the sha256 its MANIFEST.sha256 gives",
          r["rc"] == 0 and len(sc) == 2 and all(t["args"][t["args"].index("--reference-claims-sha256") + 1] == want
                                                and t["args"][t["args"].index("--reference-claims") + 1]
                                                == "findings/recompute/K1/reference_claims/reference_claims.jsonl"
                                                for t in sc), r["stdout"][-300:])
    outs = {}
    for c in ("missing", "bad_manifest"):
        for dry in (False, True):
            rr_ = run_launcher(tmp, f"q190_{c}_{int(dry)}", "beelink", "clean", claims=c, dry=dry)
            outs[(c, dry)] = rr_["rc"] == 1 and not [t for t in rr_["trace"] if t["tool"] in ("scorer", "dry_run")] \
                and ("no sealed reference claims" if c == "missing" else "differ from their MANIFEST.sha256") \
                in rr_["stdout"]
    check("Q190 launcher: a clone without the sealed claims, or whose claims differ from their manifest, is refused "
          "in the run and in the dry run, before any scorer or dry run", all(outs.values()), str(outs))
    # 8. S462's selftest: the real RAGChecker 0.1.9 and RefChecker with a fake model
    p = subprocess.run(["uv", "run", "--script", str(ROOT / "scripts/S462_k1_reference_claims.py"), "selftest"],
                       capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": "0"}, timeout=900)
    last = [ln for ln in p.stdout.splitlines() if ln.startswith("S462 SELFTEST")]
    fails = [ln for ln in p.stdout.splitlines() if ln.startswith("FAIL")]
    check("Q190 S462 selftest (real RAGChecker 0.1.9): the cut and its reproduction gate, resume, seal, verify, and "
          "ragchecker_run --run on six strategies with and without the claims passed",
          p.returncode == 0 and last and not fails, (last[-1] if last else p.stdout[-300:] + p.stderr[-300:]))



def check_q7(tmp: Path) -> None:
    """D112 Q7 O-a (README "D112 Q7: the four rerun answers"): scripts/S495_k1_q7_inputs.py's selftest, then both
    scorers' own --dry-run, without --assignment, on a set S495 built from a fixture: exactly the four keys to do. The
    same dry run on the fixture's whole source sinks lists every answer they hold, so the set's filter is what selects."""
    import os
    import subprocess
    S495 = importlib.import_module("S495_k1_q7_inputs")
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = S495.selftest()
    last = [ln for ln in buf.getvalue().splitlines() if ln.startswith("S495 SELFTEST")]
    check("Q7 S495 selftest: build, check and each refusal", rc == 0 and bool(last), last[-1] if last else buf.getvalue()[-300:])
    g, k = S495.fixture(tmp / "q7")
    S495.build(g, k, tmp / "q7" / "set")
    gt = str(ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json")
    env = {**os.environ, "PYTHONHASHSEED": "0", "MENTORI_OLLAMA_BASE": "http://127.0.0.1:9", "RAGAS_DO_NOT_TRACK": "true"}

    def dry(scorer: str, root: Path) -> dict:
        runs = [str(root / S495.sink(c)) for c in S495.CONFIGS]
        if scorer == "ragchecker":
            cmd = ["uv", "run", "--script", str(ROOT / "experiments/scorers/ragchecker_run.py"), "--base",
                   "http://127.0.0.1:9", "--run", *runs, "--store", str(k / "store"), "--gt", gt, "--out",
                   str(tmp / "q7" / f"out_{root.name}" / "ragchecker"), "--order", "claims", "--stop-on-failed", "--dry-run"]
        else:
            cmd = ["uv", "run", "--script", str(ROOT / "scripts/S357_ragas.py"), "--run", *runs, "--store",
                   str(k / "store"), "--gt", gt, "--out", str(tmp / "q7" / f"out_{root.name}" / "ragas" / "ragas.jsonl"),
                   "--concurrency", "1", "--dry-run"]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=ROOT, timeout=900)
        text = p.stdout
        try:
            d = json.loads(text[text.index("{"):text.index("\n}") + 2])
        except ValueError:
            d = {}
        d["rc"], d["dry_line"] = p.returncode, "DRY RUN: no model call, nothing written" in text
        d["listed"] = [ln.split()[:3] for ln in text.splitlines() if ln.startswith("  ") and " d" in ln]
        return d

    want = sorted([q, c, "d1"] for q, c in (("06_star_aligner_FR1", "rlm_5"), ("06_star_aligner_FR1", "rlm_20"),
                                             ("OOD_041", "rlm_20"), ("OOD_043", "rlm_20")))
    for scorer in ("ragchecker", "ragas"):
        d = dry(scorer, tmp / "q7" / "set")
        check(f"Q7 {scorer} --dry-run on the set (no --assignment): answers 4, to_do 4, the four keys, nothing written",
              d["rc"] == 0 and d["dry_line"] and d.get("answers") == 4 and d.get("to_do") == 4
              and sorted(d["listed"]) == want and not (tmp / "q7" / "out_set").exists(),
              f"answers {d.get('answers')} to_do {d.get('to_do')}")
        w = dry(scorer, g)
        check(f"Q7 {scorer} --dry-run on the whole source sinks lists all 16 of their answers (the set's filter selects)",
              w["rc"] == 0 and w.get("answers") == 16, f"answers {w.get('answers')}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_k1_"))
    try:
        Q = qids()
        check_assignment(tmp)
        sinks, asg_path, qs = fixture(tmp, Q)
        check_select(tmp, sinks, asg_path, qs)
        check_ragchecker(tmp, sinks, asg_path, qs)
        check_ragas(tmp, sinks, asg_path, qs)
        check_ragas_embed_failures(tmp, sinks, asg_path, qs)
        check_staged(tmp, sinks, qs)
        check_busy_guard(tmp)
        check_fresh_load_requests(tmp)
        check_launchers(tmp)
        check_helpers_chain(tmp)
        check_helpers_moves(tmp)
        check_helpers_end_to_end(tmp)
        check_helpers_launchers(tmp)
        check_helpers_suggest(tmp)
        check_helpers_procs_and_lock(tmp)
        check_d89_graceful(tmp, sinks, asg_path, qs)
        check_d89_guard(tmp)
        check_q190(tmp, Q)
        check_q7(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(RESULTS), sum(RESULTS)
    print(f"check_k1: {ok}/{n} passed")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
