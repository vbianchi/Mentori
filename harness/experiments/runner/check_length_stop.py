"""Checks for D114 Q29 O2 (S2 length stops): exp_05 --length-stop and exp_v2_8 LENGTH_STOP, in every config.

Run from the repository root inside the Mentori copy's environment (offline: no model, no server; the Ollama
transport under the adapter is replaced by a fake, as check_codegen.py does; kernels are real local Jupyter kernels,
sinks and workspaces go to a temporary directory, and findings/runs is compared before and after):

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_length_stop

What it pins:
1. Under "retry" (the default) _run_coder_v2 gives coder_loop_v2 the router itself, every call is made as submitted
   and length_stop is None: the code path every variant before D114 ran.
2. Under "stop" (fake loops driving the real _run_coder_v2, their calls through the real ModelRouter and
   lock_adapter): the attempt ends at the first event coder_loop_v2 yields after its first length stop, wherever that
   stop is (planning, a step that then fails, a step that would be retried, a step that completes), and when the loop
   ends with no event after it (loop_end) or by an exception (exception); exec_outcome "length", passed False, no later
   call, the loop closed, a retry it ends not counted, exec_error keeps what coder_v2 reported and names the stop, the
   soft-pass judge reads the step's text as before; the length stops are read from the attempt's own records (its
   ctx_uid, whole lines, from the file's size at its start, generator calls only, status or stop_reason "length"), so
   the router is passed as is and every record keeps its call_site; every generator call asked for after the stop is
   refused before anything is sent (_LengthGate through run_context's call gate: no request, no record, counted in
   length_stop calls_refused) and the fake loop, as Mentori, goes on after a failed call; an unknown rule is a setup
   error.
3. exp_05 end to end with the fake transport. coder_v2_n1, the nemotron off pattern of 20-21 October (audit A21-10):
   under "retry" both steps run, under "stop" only step 1, exec_outcome "length", the entry storing the rule and the
   stop. The attempt ends at step_execution_start: coder_v2 queues that event from execute_step's callback and yields
   it only when execute_step has returned (coder_v2.py:488-510), so the step's own call after the introspection is
   asked for first, and refused by the gate before it is sent (on the Studio, under "retry", the server refused it as
   longer than the context), and the step_failed event that would follow is never read. coder_v2_n3 with the real
   coder_loop_v2 whose plan candidate 1 ends on "length" (review of 22 October, F1): candidates 2 and 3, asked for
   by the planning task the loop started and which closing the loop does not stop, are refused, and that task ends
   inside the attempt, so no generator call of an attempt is made after its first length stop and no record of one
   attempt lands among the next one's. free_form_n3_best whose first candidate ends on "length": under "retry"
   candidates 2 and 3 and the pick are still made; under "stop" none is, the attempt is "length" with the
   candidate's seq. introspect_then_code whose analysis (a reply that is read, not run) ends on "length", and
   thinker_coder_split whose API summary (inside the config's try) does: under "retry" the code call is still made;
   under "stop" it is not. Under "stop" every sink the run uses gets LENGTH_STOP_MARKER. A resume under "retry" is
   refused when a sink of the variant holds "stop" attempts or the marker, of any config, also one --configs leaves
   out; "stop" over attempts stored before the flag is not.
4. exp_05's command line: --length-stop is retry or stop, default retry; stop needs --model and --thinking.
5. findings/recompute/S2_launch/run_s2_variant_d112.sh (audit N30): passes --length-stop stop, runs from its own code
   clone and never the D75 clone, keeps the variant's logs in the D75 clone, and runs its preflight before any model
   is loaded. Run on a copy (stubbed uv, curl and sleep; the script and module names a laptop guard watches for are
   renamed in the copy, so no process here names them, and its PATH line rewritten so the stubs come first): it
   refuses a variant other than nemotron-3-nano:30b off, a code clone that is the D75 clone, a code clone whose
   exp_05 does not take the flag, a sink of the variant not linked from the code clone, and a real folder in the code
   clone's findings/runs for the variant, each before any fresh load; with everything in place it runs the preflight,
   the fresh load and exp_05 with --length-stop stop --resume, in that order. run_s2_variant_d101.sh (the D75 clone's
   launcher) refuses a variant whose sinks hold LENGTH_STOP_MARKER before anything runs, and runs one without it
   (main's copy; a tree without it, a clone at 6457ae6, skips these three checks and says so).
6. Mutants: each check above that holds the rule is run again on the code with one part broken, and must fail: the
   coder_v2 watch sees no length stop; _is_length never true (no config ends); the resume refusal removed; the gate
   refuses nothing (the F1 check fails); the marker ignored (the marker refusal fails).
"""

import asyncio
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from experiments.runner import runs_snapshot

ROOT = Path(__file__).resolve().parents[2]
RUNS_BEFORE = runs_snapshot.take(ROOT / "findings" / "runs")
M = ROOT / "experiments" / "mentori"
sys.path.insert(0, str(M))

import tests.experiments_v2.exp_v2_8_coder_benchmark as v28  # noqa: E402
from backend.agents import lock_adapter as la  # noqa: E402
from backend.agents.model_router import ModelRouter  # noqa: E402
from backend.agents.notebook import coder_v2 as coder_v2_mod  # noqa: E402

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="check_length_stop_"))
results = []
D = "D114 Q29 O2"


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))


# ── the fake transport and exp_05 with its sinks in TMP (as check_codegen.py) ──

spec = importlib.util.spec_from_file_location("exp05", M / "publication/scripts/exp_05_coder_benchmark.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PROJECT_ROOT = TMP
mod.V4_RESULTS_DIR = TMP / "results_v4"
_sink = ex.sink
ex.sink = lambda run, root=TMP / "runs": _sink(run, root)
ex._run_sink = ex.sink


def base(call, base_url, passages, text, tool_calls=None):
    r = {"model": call.model, "role": call.role, "draw": call.draw, "candidate": call.candidate,
         "thinking": call.thinking, "options_sent": call.options, "fields_sent": call.fields,
         "model_digest": call.digest, "server": base_url, "lock_sha256": call.lock_sha256, "passages": passages,
         "status": "ok", "stop_reason": "stop", "error": None, "text": text, "thinking_text": "",
         "prompt_tokens": 10, "output_tokens": 5, "wall_s": 0.1}
    if tool_calls is not None:
        r["tool_calls"] = tool_calls
        r["messages_sha256"] = None
    return r


RUNAWAY = "- pandas.read_csv(path) -> DataFrame\n" + "- pandas.DataFrame.head() -> DataFrame\n" * 50


def length(r):
    r["status"], r["stop_reason"] = "length", "length"
    return r


def fake_generate(base_url, call, prompt, passages=None, images=None):
    if "SCORE:" in prompt:                                            # the soft-pass judge
        return base(call, base_url, passages, "The step failed on the context limit.")
    if prompt.startswith("You are a scientific Python programmer") and call.candidate == 1:
        return length(base(call, base_url, passages, "```python\n" + RUNAWAY))   # candidate 1 fills the context
    if prompt.startswith("You are a research assistant"):                # thinker_coder_split's introspection
        return base(call, base_url, passages, "```python\nprint('pandas.read_csv(path) -> DataFrame')\n```")
    if prompt.startswith("Based on the introspection output"):            # its API summary fills the context
        return length(base(call, base_url, passages, RUNAWAY))
    if prompt.startswith("Analyze this scientific computing task"):
        return length(base(call, base_url, passages, '[{"module": "pandas", "object": "DataFrame"}' + RUNAWAY))
    return base(call, base_url, passages, "?")


def fake_chat(base_url, call, messages, passages=None, tools=None, fmt=None):
    first = messages[0].get("content", "") if messages else ""
    if first.startswith("FAKE "):                                     # the fake loops' calls: "FAKE <reason> <n>"
        r = base(call, base_url, passages, "x", [])
        return length(r) if first.split()[1] == "length" else r
    if first.startswith("Analyze this user request"):
        return base(call, base_url, passages, '{"classification": "complex", "detected_intent": "dims"}', [])
    if any(m.get("role") == "system" and "algorithm designer" in (m.get("content") or "") for m in messages):
        plan = {"task_summary": "dims", "steps": [
            {"step_number": 1, "description": "load the counts", "expected_output": "a table"},
            {"step_number": 2, "description": "set the values", "expected_output": "print the values"}]}
        return base(call, base_url, passages, json.dumps(plan), [])
    if first.startswith("You are planning Python code"):
        return length(base(call, base_url, passages, RUNAWAY, []))   # the reply filled the context
    if first.startswith("Implement this step") and RUNAWAY in first:
        return {**base(call, base_url, passages, "", []), "status": "error", "stop_reason": None,
                "prompt_tokens": None, "output_tokens": None,
                "error": 'HTTP 400: {"error":{"code":400,"message":"request (132201 tokens) exceeds the available '
                         'context size (131072 tokens), try increasing it","type":"exceed_context_size_error"}}'}
    return base(call, base_url, passages, "?", [])


la.ollama_client.generate = fake_generate
la.ollama_client.chat = fake_chat
GEN = "ollama::nemotron-3-nano:30b"
v = mod.select(mod.variants(), GEN, "off")[0]
ops = mod.load_ops(1)

# ── 1 and 2. the real _run_coder_v2 with fake loops calling through the real router ──

RUN = {}


def make_loop(script):
    """A coder_loop_v2 stand-in: ("call", reason) makes one chat call through the router it is given (ModelRouter,
    lock_adapter, the fake transport: the record is written as in a run), ("event", dict) yields the event, ("raise",
    text) raises. It records the calls made, the router it got and whether it was closed."""
    async def loop(model_router=None, **kw):
        RUN.update(router=model_router, calls=[], closed=False)
        try:
            for kind, x in script:
                if kind == "call":
                    try:
                        await model_router.chat(model_identifier=GEN, messages=[
                            {"role": "user", "content": f"FAKE {x} {len(RUN['calls'])}"}])
                        RUN["calls"].append(x)
                    except v28.LengthStopRefused:          # Mentori goes on after a failed call
                        RUN["calls"].append(x + ":refused")
                elif kind == "raise":
                    raise RuntimeError(x)
                else:
                    yield x
        finally:
            RUN["closed"] = True
    return loop


JUDGED = []


async def no_judge(op, actual, error, router):
    JUDGED.append(error)
    return "FAIL", ""


OP = {"op_id": ops[0]["op_id"], "ground_truth": {}, "tolerance": {}, "prompt": "p"}
N_FAKE = [0]


def run_fake(script, rule):
    real_loop, real_eval = coder_v2_mod.coder_loop_v2, v28._evaluate_failed_result
    coder_v2_mod.coder_loop_v2, v28._evaluate_failed_result = make_loop(script), no_judge
    RUN.clear()
    JUDGED.clear()
    N_FAKE[0] += 1
    rid = f"exp_05__coder_v2_n1__fake-{N_FAKE[0]}"
    ctx = ex.context("exp_05", "coder_v2_n1", OP["op_id"], 1, {v28.CODER_ROLE: GEN}, "off",
                     base_url="http://127.0.0.1:9", run=rid, sink=TMP / "runs" / rid)
    ws = TMP / f"fake_{N_FAKE[0]}"
    ws.mkdir()
    router = ModelRouter()
    token = v28.LENGTH_STOP.set(rule)
    try:
        with rc.run(ctx):
            r = asyncio.run(v28._run_coder_v2(OP, router, rid, ws, n_candidates=1, gen_model=GEN))
    finally:
        v28.LENGTH_STOP.reset(token)
        coder_v2_mod.coder_loop_v2, v28._evaluate_failed_result = real_loop, real_eval
    RUN["records"] = [json.loads(x) for x in (TMP / "runs" / rid / "calls.jsonl").read_text().splitlines()]
    RUN["router_given"] = router
    return r


def ev(kind, step, **kw):
    return ("event", {"type": kind, "step_number": step, **kw})


def stop_record(r, ended_at, step, idx, refused=0):
    """r's length_stop is D114's, ending at ended_at (step), its first stop the records' idx-th, refused calls
    refused."""
    first = RUN["records"][idx]
    want = {"rule": "stop", "decision": D, "ended_at": ended_at, "step_number": step,
            "first": {"seq": first["seq"], "call_site": first["call_site"]}, "n": r["length_stop"]["n"]
            if r.get("length_stop") else None, "calls_refused": refused}
    return (r["exec_outcome"] == "length" and r["passed"] is False and r["length_stop"] == want
            and first["status"] == "length" and RUN["closed"] is True)


ERR400 = 'nemotron-3-nano:30b: status error: HTTP 400: {"error":{"code":400}}'
# the nemotron off attempt of 20 October: each step's introspection ends on length, its next call is refused
NEMOTRON = [("call", "stop"), ("call", "stop"),                                       # analysis, plan
            ev("step_started", 1), ("call", "length"), ("call", "stop"), ev("step_failed", 1, error=ERR400),
            ev("step_started", 2), ("call", "length"), ("call", "stop"), ev("step_failed", 2, error=ERR400),
            ev("step_started", 3), ("call", "stop"), ev("step_complete", 3)]

r = run_fake(NEMOTRON, "retry")
check("1 retry: the loop gets the router itself", RUN["router"] is RUN["router_given"])
check("1 retry: every step runs, as submitted", RUN["calls"] == ["stop", "stop", "length", "stop", "length", "stop",
                                                                   "stop"], RUN["calls"])
check("1 retry: outcome and record as before", r["exec_outcome"] == "step_failed" and r["length_stop"] is None
      and r["length_stop_rule"] == "retry" and r["n_retries"] == 0
      and r["exec_error"] == f"Step failed: {ERR400} | Step failed: {ERR400}", (r["exec_outcome"], r["exec_error"]))


def nemotron_stop():
    r = run_fake(NEMOTRON, "stop")
    return r, (RUN["calls"] == ["stop", "stop", "length", "stop:refused"] and len(RUN["records"]) == 3
               and stop_record(r, "step_failed", 1, 2, refused=1))


r, ok = nemotron_stop()
third = RUN["records"][2]
check("2 stop: the loop gets the router itself too (records unchanged)", RUN["router"] is RUN["router_given"]
      and third["call_site"].endswith(" loop") and "check_length_stop.py" in third["call_site"], third["call_site"])
check("2 stop: the attempt ends at step 1's failure, the call before it refused unsent, outcome length, closed", ok,
      (RUN["calls"], r["length_stop"]))
check("2 stop: exec_error keeps the step's text and names the stop", r["exec_error"] == (
      f"Step failed: {ERR400} | the attempt ended at its first length stop (seq {third['seq']}, "
      f"{third['call_site']}), at step_failed of step 1 ({D})"), r["exec_error"])
check("2 stop: the soft-pass judge reads the step's text as before", JUDGED == [f"Step failed: {ERR400}"], JUDGED)

RETRY = [("call", "stop"), ev("step_started", 1),
         ("call", "stop"), ev("cell_evaluation", 1, score=20, status="ok", should_retry=True), ev("step_retry", 1),
         ("call", "length"), ev("cell_evaluation", 1, score=20, status="ok", should_retry=True), ev("step_retry", 1),
         ("call", "stop"), ev("step_complete", 1)]
r = run_fake(RETRY, "stop")
check("2 stop: a retry before the length stop is made and counted; the attempt ends at the next event",
      RUN["calls"] == ["stop", "stop", "length"] and r["n_retries"] == 1 and stop_record(r, "cell_evaluation", 1, 2)
      and JUDGED == [r["exec_error"]] and r["exec_error"].endswith(f"({D})"), (RUN["calls"], r["length_stop"]))
r = run_fake(RETRY, "retry")
check("1 retry: both retries made and counted", r["n_retries"] == 2 and RUN["calls"] == ["stop", "stop", "length",
                                                                                         "stop"], RUN["calls"])

PLANNING = [("call", "length"),                                                        # planning: before any step
            ev("step_started", 1), ("call", "stop"), ev("step_complete", 1),
            ev("step_started", 2), ("call", "stop"), ev("step_failed", 2, error="KeyError: 'x'")]


def planning_stop():
    r = run_fake(PLANNING, "stop")
    return r, RUN["calls"] == ["length"] and stop_record(r, "step_started", 1, 0)


r, ok = planning_stop()
check("2 stop: a length stop in planning ends the attempt at the next event", ok, (RUN["calls"], r["length_stop"]))
r = run_fake(PLANNING, "retry")
check("1 retry: a length stop in planning ends nothing", RUN["calls"] == ["length", "stop", "stop"]
      and r["length_stop"] is None and r["exec_outcome"] == "step_failed", (RUN["calls"], r["exec_outcome"]))

GOES_ON = [("call", "stop"), ev("step_started", 1), ("call", "length"), ev("step_complete", 1),
           ev("step_started", 2), ("call", "stop"), ev("step_complete", 2)]
r = run_fake(GOES_ON, "stop")
check("2 stop: a length stop in a step that completes ends the attempt there (no pass after it)",
      RUN["calls"] == ["stop", "length"] and stop_record(r, "step_complete", 1, 1), (RUN["calls"], r["length_stop"]))

LAST = [ev("step_started", 1), ("call", "stop"), ("call", "length")]
r = run_fake(LAST, "stop")
check("2 stop: a length stop with no event after it ends the attempt at loop_end",
      RUN["calls"] == ["stop", "length"] and stop_record(r, "loop_end", None, 1), r["length_stop"])
RAISE = [ev("step_started", 1), ("call", "length"), ("raise", "boom")]
r = run_fake(RAISE, "stop")
check("2 stop: an exception after a length stop: the outcome is length", stop_record(r, "exception", None, 0)
      and "boom" in r["exec_error"], (r["exec_outcome"], r["length_stop"]))
r = run_fake(RAISE, "retry")
check("1 retry: the same exception stays the attempt's exception", r["exec_outcome"] == "exception"
      and r["length_stop"] is None, r["exec_outcome"])

# _LengthRecords reads only this attempt's whole generator lines, from the file's size at its start
lr_sink = TMP / "runs" / "exp_05__coder_v2_n1__lr"
lr_sink.mkdir(parents=True)
lr_file = lr_sink / "calls.jsonl"
G = {"role": "generator"}
lr_file.write_text(json.dumps({**G, "ctx_uid": "u1", "seq": 1, "status": "length"}) + "\n")   # before the attempt


class _Ctx:
    sink, ctx_uid = lr_sink, "u1"


_real_current = rc.current
rc.current = lambda: _Ctx
try:
    lr = v28._LengthRecords()
finally:
    rc.current = _real_current
with open(lr_file, "a") as f:
    f.write(json.dumps({**G, "ctx_uid": "u2", "seq": 1, "status": "length"}) + "\n")      # another attempt
    f.write(json.dumps({**G, "ctx_uid": "u1", "seq": 2, "status": "ok"}) + "\n")
    f.write(json.dumps({"role": "judge", "ctx_uid": "u1", "seq": 3, "status": "length"}) + "\n")   # an instrument
    f.write(json.dumps({**G, "ctx_uid": "u1", "seq": 4, "status": "ok", "stop_reason": "length",
                        "call_site": "a.py:1 f"}) + "\n")
    f.write('{"role": "generator", "ctx_uid": "u1", "seq": 5, "sta')                     # a line not yet whole
n1 = lr.count()
with open(lr_file, "a") as f:
    f.write('tus": "length", "call_site": "b.py:2 g"}\n')
n2 = lr.count()
check("2 _LengthRecords: this attempt's whole generator lines only, from its start", (n1, n2) == (1, 2)
      and lr.stops == [{"seq": 4, "call_site": "a.py:1 f"}, {"seq": 5, "call_site": "b.py:2 g"}], (n1, n2, lr.stops))

tok = v28.LENGTH_STOP.set("never")
try:
    asyncio.run(v28._run_coder_v2(OP, ModelRouter(), "u", TMP, n_candidates=1, gen_model=GEN))
    bad = None
except LockError as e:
    bad = e
finally:
    v28.LENGTH_STOP.reset(tok)
check("2 an unknown rule is a setup error", bad is not None)

# ── 3. exp_05 end to end, fake transport ──────────────────────────────────────


def stored(config, extra):
    sink = TMP / "runs" / f"exp_05__{config}__{extra}"
    return (json.loads((sink / "answers.json").read_text())["results"],
            [json.loads(x) for x in (sink / "calls.jsonl").read_text().splitlines()])


def sites(calls):
    return [c["call_site"].rsplit(" ", 1)[-1] + (":" + c["status"] if c["status"] != "ok" else "")
            + (f"#{c['candidate']}" if c.get("candidate") else "") for c in calls]


def e2e(config, extra, rule, **kw):
    asyncio.run(mod.run_variant(dict(v, extra=extra), [config], ops, "http://127.0.0.1:9", length_stop=rule, **kw))
    (e,), cs = stored(config, extra)
    return e, cs


er, cr = e2e("coder_v2_n1", "nemotron+retry", "retry")
check("3 coder_v2 retry: both steps run, each a length stop and a refused call (as on the Studio)", sites(cr) == [
      "analyze_request", "_stream_llm_response", "introspect_step:length", "execute_step:error",
      "introspect_step:length", "execute_step:error", "_evaluate_failed_result"], sites(cr))
check("3 coder_v2 retry: step_failed, rule stored, no length_stop", er["exec_outcome"] == "step_failed"
      and er["length_stop_rule"] == "retry" and er["length_stop"] is None and not er["passed"], er["exec_outcome"])


def coder_v2_e2e_stop(extra):
    es, cs = e2e("coder_v2_n1", extra, "stop")
    intro = next((c for c in cs if c["call_site"].endswith("introspect_step")), None)
    ok = (sites(cs) == ["analyze_request", "_stream_llm_response", "introspect_step:length", "_evaluate_failed_result"]
          and (es["length_stop"] or {}).get("calls_refused") == 1
          and intro is not None and es["exec_outcome"] == "length" and not es["passed"]
          and es["length_stop_rule"] == "stop"
          and (es["length_stop"] or {}).get("ended_at") == "step_execution_start"
          and es["length_stop"]["first"] == {"seq": intro["seq"], "call_site": intro["call_site"]})
    return es, cs, intro, ok


es, cs, intro, ok = coder_v2_e2e_stop("nemotron+stop")
check("3 coder_v2 stop: step 1's call after the stop refused unsent, then the soft-pass judge; length, the entry "
      "names the rule and the stop", ok,
      (sites(cs), es.get("length_stop")))
check("3 coder_v2 stop: the records keep Mentori's call sites", intro["call_site"].startswith(
      "backend/agents/notebook/api_introspector.py:") and [c["call_site"] for c in cs[:3]] == [
      c["call_site"] for c in cr[:3]], [c["call_site"] for c in cs])
check("3 coder_v2 stop: exec_error is the stop's note; the stored calls are the four made",
      es["exec_error"] == (f"the attempt ended at its first length stop (seq {intro['seq']}, {intro['call_site']}), "
                           f"at step_execution_start of step 1 ({D})")
      and es["n_calls"] == len(cs) == 4, es["exec_error"])
SINK_STOP = TMP / "runs" / "exp_05__coder_v2_n1__nemotron+stop"
check("3 stop: the sink gets the marker, retry does not", (SINK_STOP / mod.LENGTH_STOP_MARKER).is_file()
      and not (TMP / "runs" / "exp_05__coder_v2_n1__nemotron+retry" / mod.LENGTH_STOP_MARKER).exists())


# coder_v2_n3 with the real coder_loop_v2: plan candidate 1 ends on "length" (review of 22 October, F1)
PLAN1 = {"task_summary": "dims", "steps": [
    {"step_number": 1, "description": "load the counts", "expected_output": "a table"}]}


def chat_n3(base_url, call, messages, passages=None, tools=None, fmt=None):
    first = messages[0].get("content", "") if messages else ""
    if first.startswith("Analyze this user request"):
        return base(call, base_url, passages, '{"classification": "complex", "detected_intent": "dims"}', [])
    if any(m.get("role") == "system" and "algorithm designer" in (m.get("content") or "") for m in messages):
        if call.candidate == 1:
            return length(base(call, base_url, passages, "{" + "x" * 50, []))
        time.sleep(1.0)                            # a real plan call takes a while: the orphan race of F1
        return base(call, base_url, passages, json.dumps(PLAN1), [])
    time.sleep(1.0)
    return base(call, base_url, passages, json.dumps(PLAN1), [])


def n3_planning(extra, rule):
    """Two attempts of coder_v2_n3 with the real coder_loop_v2; returns (entries, records in file order, problems)."""
    la.ollama_client.chat = chat_n3
    try:
        asyncio.run(mod.run_variant(dict(v, extra=extra), ["coder_v2_n3"], mod.load_ops(2), "http://127.0.0.1:9",
                                    length_stop=rule))
    finally:
        la.ollama_client.chat = fake_chat
    sink = TMP / "runs" / f"exp_05__coder_v2_n3__{extra}"
    res = json.loads((sink / "answers.json").read_text())["results"]
    cs = [json.loads(x) for x in (sink / "calls.jsonl").read_text().splitlines()]
    bad = []
    order = [c["ctx_uid"] for c in cs]
    for e in res:
        u = e["ctx_uid"]
        idx = [i for i, x in enumerate(order) if x == u]
        if idx != list(range(idx[0], idx[-1] + 1)):
            bad.append(f"{e['answer_key']}: its records are not together in the file ({idx})")
        mine = [c for c in cs if c["ctx_uid"] == u]
        if e["n_calls"] != len(mine):
            bad.append(f"{e['answer_key']}: {e['n_calls']} calls stored, {len(mine)} in the file at the end")
        gens = [c for c in mine if c["role"] == "generator"]
        first = next((c["seq"] for c in gens if c["status"] == "length"), None)
        if rule == "stop" and (first is None or any(c["seq"] > first for c in gens)):
            bad.append(f"{e['answer_key']}: a generator call after its first length stop "
                       f"({[(c['seq'], c['status'], c.get('candidate')) for c in gens]})")
        if rule == "stop" and ((e["length_stop"] or {}).get("calls_refused") != 2 or e["exec_outcome"] != "length"):
            bad.append(f"{e['answer_key']}: {e['exec_outcome']}, length_stop {e['length_stop']}")
    return res, cs, bad


res3, cs3, bad3 = n3_planning("n3plan+stop", "stop")
check("3 coder_v2_n3 stop (real coder_loop_v2): plan candidates 2 and 3 refused unsent, the planning task ends inside "
      "its attempt, no record lands in the next attempt", not bad3 and len(res3) == 2, bad3)
res3r, cs3r, bad3r = n3_planning("n3plan+retry", "retry")
check("1 coder_v2_n3 retry (real coder_loop_v2): candidates 2 and 3 and the plan judge are made, as submitted",
      not bad3r and all(sum(1 for c in cs3r if c["ctx_uid"] == e["ctx_uid"] and c["role"] == "generator"
                            and c["call_site"].endswith("_stream_llm_response")) == 4 for e in res3r),
      (bad3r, sites(cs3r)))

e, c = e2e("free_form_n3_best", "n3+retry", "retry")
check("3 free_form_n3_best retry: candidates 2, 3 and the pick still made after candidate 1's length stop",
      sites(c) == ["_run_free_form_n3:length#1", "_run_free_form_n3#2", "_run_free_form_n3#3", "_run_free_form_n3",
                   "_evaluate_failed_result"]
      and e["exec_outcome"] == "length" and e["length_stop"] is None, (sites(c), e["exec_outcome"]))


def n3_stop(extra):
    e, c = e2e("free_form_n3_best", extra, "stop")
    ok = (sites(c) == ["_run_free_form_n3:length#1", "_evaluate_failed_result"] and e["exec_outcome"] == "length"
          and not e["passed"] and e["length_stop_rule"] == "stop"
          and (e["length_stop"] or {}).get("first") == {"seq": c[0]["seq"], "call_site": c[0]["call_site"]}
          and e["length_stop"]["ended_at"] == "candidate_1" and e["generations"][0]["stage"] == "candidate_1"
          and e["exec_error"].endswith(f"({D})"))
    return e, c, ok


e, c, ok = n3_stop("n3+stop")
check("3 free_form_n3_best stop: the attempt ends at candidate 1's length stop, nothing called after but the judge",
      ok, (sites(c), e.get("exec_outcome"), e.get("length_stop")))

e, c = e2e("introspect_then_code", "itc+retry", "retry")
check("3 introspect_then_code retry: the code call is still made after the analysis' length stop",
      sites(c)[:2] == ["_run_introspect_then_code:length", "_run_introspect_then_code"]
      and e["length_stop"] is None and e["exec_outcome"] != "length", (sites(c), e["exec_outcome"]))
e, c = e2e("introspect_then_code", "itc+stop", "stop")
check("3 introspect_then_code stop: no call after the analysis' length stop (a reply read, not run, ends it too)",
      sites(c) == ["_run_introspect_then_code:length", "_evaluate_failed_result"] and e["exec_outcome"] == "length"
      and e["length_stop"]["ended_at"] == "analysis", (sites(c), e["exec_outcome"]))


e, c = e2e("thinker_coder_split", "tcs+retry", "retry")
check("3 thinker_coder_split retry: the coder call is still made after the API summary's length stop",
      sites(c)[:3] == ["_run_thinker_coder_split", "_run_thinker_coder_split:length", "_run_thinker_coder_split"]
      and e["length_stop"] is None, (sites(c), e["exec_outcome"]))
e, c = e2e("thinker_coder_split", "tcs+stop", "stop")
check("3 thinker_coder_split stop: the API summary's length stop (inside the config's try) ends the attempt",
      sites(c) == ["_run_thinker_coder_split", "_run_thinker_coder_split:length", "_evaluate_failed_result"]
      and e["exec_outcome"] == "length" and e["length_stop"]["ended_at"] == "api_summary", (sites(c), e["exec_outcome"]))


def resume_refused(extra, configs=("coder_v2_n1",)):
    try:
        asyncio.run(mod.run_variant(dict(v, extra=extra), list(configs), ops, "http://127.0.0.1:9", resume=True))
        return None
    except ex.ExperimentError as err:
        return err


refused = resume_refused("nemotron+stop")
check("3 a resume under retry of a run holding stop attempts is refused", refused is not None
      and "--length-stop stop" in str(refused), refused)
refused = resume_refused("nemotron+stop", ("free_form",))
check("3 ... also when --configs names only another config (review 3)", refused is not None, refused)


def marker_refused(extra):
    """A variant whose only sign of "stop" is the marker in a sink --configs leaves out (no attempt stored yet)."""
    (TMP / "runs" / f"exp_05__coder_v2_n3__{extra}").mkdir(parents=True)
    (TMP / "runs" / f"exp_05__coder_v2_n3__{extra}" / mod.LENGTH_STOP_MARKER).write_text("stop\n")
    return resume_refused(extra, ("free_form",))


refused = marker_refused("marked")
check("3 a resume under retry of a variant marked for stop, with no stop attempt stored yet, is refused (review 1)",
      refused is not None and mod.LENGTH_STOP_MARKER in str(refused), refused)
check("3 stop over attempts stored before the flag (no rule) or under retry is allowed",
      mod.check_length_rule([{"answer_key": "a"}, {"length_stop_rule": "retry"}], "stop", "r") is None
      and mod.check_length_rule([], "retry", "r") is None and mod.check_length_rule([], "stop", "r", True) is None)
try:
    mod.check_length_rule([], "never", "r")
    unknown = None
except ex.ExperimentError as err:
    unknown = err
check("3 an unknown rule is refused", unknown is not None)

# ── 4. command line ───────────────────────────────────────────────────────────


def exits(argv):
    saved = sys.argv
    sys.argv = ["exp_05"] + argv
    try:
        mod.main()
        return None
    except SystemExit as err:
        return err.code
    finally:
        sys.argv = saved


check("4 stop with --run-all is refused", exits(["--run-all", "--length-stop", "stop"]) == 2)
check("4 stop without --thinking is refused", exits(["--model", "ollama::nemotron-3-nano:30b", "--length-stop",
                                                     "stop"]) == 2)
check("4 an unknown value is refused", exits(["--model", "ollama::nemotron-3-nano:30b", "--thinking", "off",
                                              "--length-stop", "never"]) == 2)
from contextlib import redirect_stdout  # noqa: E402
import io  # noqa: E402


def dry(extra_args):
    saved = sys.argv
    sys.argv = ["exp_05", "--model", "ollama::nemotron-3-nano:30b", "--thinking", "off", "--dry-run"] + extra_args
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            mod.main()
    finally:
        sys.argv = saved
    return buf.getvalue()


check("4 the default is retry, printed with the work list", "length stops (D112 Q8): retry" in dry([]))
check("4 stop is printed as the launcher's preflight reads it", "length stops (D112 Q8): stop"
      in dry(["--length-stop", "stop"]))

# ── 5. the launcher ───────────────────────────────────────────────────────────

LDIR = ROOT / "findings" / "recompute" / "S2_launch"
LAUNCHER = LDIR / "run_s2_variant_d112.sh"
text = LAUNCHER.read_text()
lines = text.splitlines()
E05 = "exp_05" + "_coder_benchmark.py"              # spelled apart: this file's text is not a command line, but kept so
JOB = "experiments.runner." + "job"
check("5 the D114 launcher passes --length-stop stop to exp_05",
      any("--base-url $B --length-stop stop $RESUME > $D/exp05.log" in x for x in lines))
check("5 it runs from its own code clone, never the D75 clone, and keeps the logs there",
      'CODE=${S2_CODE_CLONE:-$HOME/projects/mentori-runs-s2-d114}' in text and 'cd "$CODE" || exit 1' in text
      and "RUNS=$HOME/projects/mentori-runs-s2-d75" in text and "D=$RUNS/findings/recompute/S2_launch/$TAG" in text
      and "cd ~/projects/mentori-runs-s2-d75" not in text)
pre = next(i for i, x in enumerate(lines) if "--length-stop stop --dry-run" in x)
load = next(i for i, x in enumerate(lines) if "fresh-load" in x)
check("5 the preflight comes before the fresh load", pre < load, (pre, load))
check("5 bash reads it", subprocess.run(["bash", "-n", str(LAUNCHER)]).returncode == 0)

# the launcher run on a copy, in a fake home, with stubs
FH = TMP / "home"
STUBS = FH / ".local" / "bin"
STUBS.mkdir(parents=True)
LOG = TMP / "stub.log"
for name, body in {
    "uv": 'echo "uv $*" >> "$STUB_LOG"\n'
          'case "$*" in *--dry-run*) [ "$STUB_PREFLIGHT" = old ] && { echo "unrecognized arguments" >&2; exit 2; }\n'
          '  echo "length stops (D112 Q8): stop";;\n'
          '  *E05.py*) echo "[64/220] x"; echo "[65/220] y";; esac\nexit 0\n',
    "curl": 'echo "curl $*" >> "$STUB_LOG"\nexit 0\n',
    "sleep": "exit 0\n",
}.items():
    p = STUBS / name
    p.write_text("#!/bin/bash\n" + body)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
COPY = TMP / "launch" / "run_s2_variant_d112.sh"
COPY.parent.mkdir()
PATH_LINE = "export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1"
check("5 the launcher's PATH line is the one the copy rewrites", PATH_LINE in text)
COPY.write_text(text.replace(E05, "E05.py").replace(JOB, "RUNNER_JOB").replace(
    PATH_LINE, "export PATH=$HOME/.local/bin:/opt/homebrew/bin:$PATH PYTHONDONTWRITEBYTECODE=1"))   # stubs first
CODE, RUNS = FH / "projects" / "mentori-runs-s2-d114", FH / "projects" / "mentori-runs-s2-d75"
SINK = "exp_05__free_form__nemotron-3-nano-30b+off"
(RUNS / "findings" / "runs" / SINK).mkdir(parents=True)
(CODE / "findings" / "runs").mkdir(parents=True)


def launch(env_extra=None, variant=("ollama::nemotron-3-nano:30b", "off"), script=None):
    LOG.write_text("")
    env = {**os.environ, "HOME": str(FH), "STUB_LOG": str(LOG), **(env_extra or {})}
    env.pop("S2_CODE_CLONE", None)
    env.update(env_extra or {})
    p = subprocess.run(["bash", str(script or COPY), *variant, "19999", "--resume"], env=env,
                       capture_output=True, text=True, timeout=120)
    return p.returncode, LOG.read_text()


rc_, log = launch(variant=("ollama::nemotron-3-nano:30b", "default"))
check("5 run: a variant other than nemotron-3-nano:30b off is refused before anything runs", rc_ == 1
      and "uv " not in log and "D114 names nemotron-3-nano:30b off only" in log, log)
rc_, log = launch({"S2_CODE_CLONE": str(RUNS)})
check("5 run: a code clone that is the D75 clone is refused before anything runs", rc_ == 1 and "uv " not in log
      and "the code clone is the D75 clone" in log, log)
rc_, log = launch()
check("5 run: a sink of the variant not linked from the code clone is refused before any fresh load",
      rc_ == 1 and "fresh-load" not in log and "is not a link to the D75 clone" in log, log)
(CODE / "findings" / "runs" / SINK).symlink_to(RUNS / "findings" / "runs" / SINK)
REAL = CODE / "findings" / "runs" / "exp_05__coder_v2_n3__nemotron-3-nano-30b+off"
REAL.mkdir()
rc_, log = launch()
check("5 run: a real folder of the variant in the code clone's findings/runs is refused before any fresh load",
      rc_ == 1 and "fresh-load" not in log and "is a folder in the code clone" in log, log)
REAL.rmdir()
rc_, log = launch({"STUB_PREFLIGHT": "old"})
check("5 run: a code clone whose exp_05 does not take the flag is refused before any fresh load",
      rc_ == 1 and "fresh-load" not in log and "does not take --length-stop stop" in log, log)
rc_, log = launch()
for _ in range(100):                                         # the after-first-call subshell runs on after the launcher
    if "after-first-call" in LOG.read_text():
        break
    time.sleep(0.1)
log = LOG.read_text()
order = [x.split()[0] + (" dry-run" if "--dry-run" in x else " fresh-load" if "fresh-load" in x
         else " exp_05" if "E05.py" in x and "--base-url" in x else " after" if "after-first-call" in x else "")
         for x in log.splitlines() if x.startswith("uv ") and "after-first-call" not in x]
run_line = next((x for x in log.splitlines() if "E05.py" in x and "--base-url" in x), "")
check("5 run: preflight, fresh load, then exp_05 with --length-stop stop --resume, logs in the D75 clone",
      rc_ == 0 and order[:3] == ["uv dry-run", "uv fresh-load", "uv exp_05"]
      and run_line.endswith("--base-url http://127.0.0.1:19999 --length-stop stop --resume")
      and (RUNS / "findings/recompute/S2_launch/ollama--nemotron-3-nano-30b+off/exp05.log").read_text().startswith(
          "[64/220]"), (rc_, order, run_line))

# the D75 clone's launcher refuses a variant marked for "stop" (review 1); main's copy only (a clone at 6457ae6 has
# none: the D75 clone's untracked copy is replaced by main's, deploy step 3)
if not (LDIR / "run_s2_variant_d101.sh").is_file():
    print("SKIP 5 run_s2_variant_d101.sh: not in this tree (3 checks)")
else:
    D101 = (LDIR / "run_s2_variant_d101.sh").read_text()
    COPY101 = TMP / "launch" / "run_s2_variant_d101.sh"
    COPY101.write_text(D101.replace(E05, "E05.py").replace(JOB, "RUNNER_JOB").replace(
        PATH_LINE, "export PATH=$HOME/.local/bin:/opt/homebrew/bin:$PATH PYTHONDONTWRITEBYTECODE=1"))
    check("5 run_s2_variant_d101.sh: bash reads it, and its guard comes before any uv or curl",
          subprocess.run(["bash", "-n", str(LDIR / "run_s2_variant_d101.sh")]).returncode == 0
          and D101.index(mod.LENGTH_STOP_MARKER) < min(D101.index("uv run"), D101.index("curl -s -d \"S2 started")))
    (RUNS / "findings" / "runs" / SINK / mod.LENGTH_STOP_MARKER).write_text("stop\n")
    rc_, log = launch(script=COPY101)
    check("5 run_s2_variant_d101.sh refuses a variant whose sink holds the marker, before anything runs",
          rc_ == 1 and "uv " not in log and "runs under --length-stop stop" in log, log)
    rc_, log = launch(script=COPY101, variant=("ollama::nemotron-3-nano:30b", "default"))
    for _ in range(100):                                         # its after-first-call subshell runs on after it
        if "after-first-call" in LOG.read_text():
            break
        time.sleep(0.1)
    log = LOG.read_text()
    check("5 run_s2_variant_d101.sh runs a variant without the marker", "fresh-load" in log and "E05.py" in log, log)
    (RUNS / "findings" / "runs" / SINK / mod.LENGTH_STOP_MARKER).unlink()

# ── 6. mutants: each must make its check fail ─────────────────────────────────

real_count, real_is_length, real_rule = v28._LengthRecords.count, v28._is_length, mod.check_length_rule
try:
    v28._LengthRecords.count = lambda self: 0
    check("6 mutant (coder_v2 watch sees nothing): the planning check fails", not planning_stop()[1])
    check("6 mutant (coder_v2 watch sees nothing): the nemotron check fails", not nemotron_stop()[1])
finally:
    v28._LengthRecords.count = real_count
try:
    v28._is_length = lambda rec: False
    check("6 mutant (_is_length never true): the free_form_n3_best stop check fails", not n3_stop("n3+mutant")[2])
    check("6 mutant (_is_length never true): the coder_v2 end-to-end stop check fails",
          not coder_v2_e2e_stop("nemotron+mutant")[3])
finally:
    v28._is_length = real_is_length
try:
    mod.check_length_rule = lambda results, rule, rid, marked=False: None
    check("6 mutant (resume refusal removed): the refusal check fails", resume_refused("nemotron+stop") is None)
finally:
    mod.check_length_rule = real_rule
real_marker = mod.LENGTH_STOP_MARKER
try:
    mod.LENGTH_STOP_MARKER = "NO_SUCH_MARKER"                 # the marker is never found
    shutil.rmtree(TMP / "runs" / "exp_05__coder_v2_n3__marked2", ignore_errors=True)
    (TMP / "runs" / "exp_05__coder_v2_n3__marked2").mkdir(parents=True)
    (TMP / "runs" / "exp_05__coder_v2_n3__marked2" / real_marker).write_text("stop\n")
    check("6 mutant (marker ignored): the marker refusal check fails",
          resume_refused("marked2", ("free_form",)) is None)
finally:
    mod.LENGTH_STOP_MARKER = real_marker
real_before = v28._LengthGate.before
try:
    v28._LengthGate.before = lambda self, tag, role: None     # the gate refuses nothing
    check("6 mutant (gate refuses nothing): the coder_v2_n3 planning check fails", n3_planning("n3plan+mutant",
                                                                                                "stop")[2])
    check("6 mutant (gate refuses nothing): the nemotron fake-loop check fails", not nemotron_stop()[1])
finally:
    v28._LengthGate.before = real_before

# ── the end ───────────────────────────────────────────────────────────────────

d_runs = runs_snapshot.diff(RUNS_BEFORE, runs_snapshot.take(ROOT / "findings" / "runs"))
check("findings/runs unchanged by the check", d_runs == [], d_runs[:5])
shutil.rmtree(FH, ignore_errors=True)
print(f"check_length_stop: {sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
