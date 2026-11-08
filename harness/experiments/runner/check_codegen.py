"""Checks for the code-generation track (Figure 6, plan row B6): exp_05, exp_v2_8 and backend/agents/notebook.

Run from the repository root inside the Mentori copy's environment (offline: no model, no server, no key; the
Ollama transport under the adapter is replaced by a fake that answers from the prompt, as check_adapter.py stubs it;
kernels are real local Jupyter kernels, sinks and workspaces go to a temporary directory):

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_codegen

What it pins:
1. D69 Q35, decided by the reply's first ```: when it opens ```python (D75 Q56: also py, python3, any case) the
   first block runs; otherwise the reply up to it runs, and a later example block is cut; an opening fence never
   closed is "unclosed_block" and runs to the end; with no fence the whole reply runs; an empty reply or empty code
   runs nothing; it stores the raw reply, the code whole, the block count and the first fence's tag.
2. Class X "pick best": only a stated pick counts (parse_stated_pick); "1. Candidate 2 is best" is unparsed.
3. Q34: EXEC_TIMEOUT is 120 s, the kernel's default; a firing is the outcome "exec_timeout" (a real kernel, 1 s).
4. cuts.md step_executor.py:1020 and :820: _summarize_outputs gives every output whole for objects and dicts; the
   tool message states the cell's status. M3: prompt-tools mode writes the model's own tool call back whole; the
   native assistant turn carries the call in {"function": ...} shape.
5. Class X cell_evaluator: a failed call is status "error", a reply with no numeric score "unparsed", both with no
   score; a stated score, integer, float or numeric text, is used as given (20.0 retries, as submitted); whole
   traceback, output and source; a LockError passes through.
6. cuts.md prompts_v2 M18, :433: every variable, every cell, whole code.
7. Q32: extra cell candidates and coder_v2_n3 plan candidates send seeds draw*1000+k; a single plan does not.
8. D69 Q38: a LockError raised inside analyser, introspector, algorithm, step or evaluator reaches the caller.
9. exp_05 end to end (free_form, free_form_n3_best, coder_v2_n1) with the fake transport: no options asked, the code
   and generations stored whole, exec_outcome, pick, cell evaluations with status, the attempt's call records with
   options_sent, the report's options_sent from the records and no num_ctx constant, no database read; Q34: each
   extraction and introspection outcome is stored (a timeout there included); coder_v2 counts its "step_retry"
   events and stores n_llm_calls None (it emits no per-call event).
10. D72: scan finds import and from-import at any depth, import_module (an alias, name=) and __import__ (bare or an
   attribute) with a literal name, imports inside a literal passed to exec or compile, and falls back to a regex on
   a syntax error (lines split on ";", "try:" and "if c:" headers stripped); install lines are recorded; ALLOW_LIST
   pins are uv.lock's versions; check classifies stdlib, present, not_allowed (no install command run) and installs
   a missing allow-listed module with exactly one install command, the pinned requirement into the probed
   interpreter, every frozen distribution held (subprocess stubbed); in a real kernel the probe that answers is the
   kernel's own (the stand-alone probe made to raise), only generated code is scanned, a ModuleNotFoundError for a
   not_allowed module is recorded as the model's failure, a rebound print does not stop the probe, a failed probe is
   recorded and the code still runs, and with no recorder nothing is probed; the flag is judged on the final kernel
   run of a failed attempt (an error fixed by a later run does not count); the attempt's records carry imports,
   missing_installed, missing_not_allowed, install_lines, missing_library_not_allowed and import_scans.
11. D75 (round 3). Q56: a fence tagged python, py or python3 in any case opens the block, a bare ``` only at the top
   of the reply (after text it still closes continued code, D69). Q57: a reply run as code that ended on "length"
   runs nothing, exec_outcome "length" (exp_05 end to end, free_form and best-of-3). Q58: a first line naming exactly
   one number in range is the pick (exp_05 runs candidate 2 for "The best candidate is 2."). Q59: no score, no
   retry. Q60: an introspection entry for a script variable is labelled by its type, a bare error entry is readable;
   both recovery configs reach their retry on kmf.median_ and pass (exp_05 end to end). Q61: the retry prompt holds
   ename: evalue, no traceback, no earlier code. Q62: the kernel prints pandas at its defaults, pd still bound.
   Q63: the benchmark's kernels start offline (UV_OFFLINE, an empty uv cache removed at stop, PIP_NO_INDEX, no
   VIRTUAL_ENV) and an install of a missing package fails there; other kernels start as before; a package
   fingerprint is taken before and after every attempt and a change stops the run with no attempt stored. Q64: a
   NameError for a name the failed not_allowed import binds counts toward the flag, after it only, also recomputed
   from code_cells for records stored before. Q101: a step_failed with no error text is written with the step's
   last evaluation. The report counts exec_outcome, fence tags and cases, picks and evaluation statuses per config.
12. D78 Q112: a kernel started offline as an attempt's reports the harness's interpreter, which the fingerprint then
   reads; a kernel reporting another one (or none) at the variant's start stops it before any attempt or fingerprint,
   and a scan of an attempt's kernel on another interpreter stops the run with no attempt stored. Q108: findings/runs
   is compared, every path with its sha256, between the check's start and its end.
13. D80 V1 (audit F34, F35) and D81 (Q136-Q138), through the real ModelRouter and lock_adapter over a fake transport.
   read_text_tool_call reads the stored shapes gpt-oss:20b wrote at high: JSON (bare, with the functions. prefix, in
   ```json fences, followed by an execute_cell), the Python-call form (keywords, or one dict literal, bare or in a
   ```python fence, assigned or not, comments passing) and the harmony header form ("assistant to=" or "commentary
   to=functions.add_cell", an optional ":", then a JSON object). It refuses every other stored shape ({"functions":
   [...]} and {"commentary": [...]} wrappers, prose before or after, a "**Step**" line,
   assistant.functions.add_cell(...), a header with the arguments in parentheses) and
   every off-schema call, a name with a prefix other than functions., a call nested in the arguments, an f-string or
   a name as add_cell's argument, and **kwargs among them. In execute_step an Ollama tool-call parse error, a stall, an
   HTTP 500 and a dropped connection are retried, each retry's record naming the failed call's seq and the reason,
   its retry number and the seed it sent (draw 1: 1000001, 2000001, 3000001, on a scratch lock with [generation]
   retry_seed); a Gemini stall and a Gemini URLError "timed out" before the first chunk (through gemini_client over a
   fake transport) are not retried: one call, no transient_retry, the step fails on it, as the submitted Gemini
   client never raised. After MAX_TRANSIENT_RETRIES (3) the step fails on the error, with 4 calls made; an add_cell
   written as text (JSON or Python) adds that cell, the next turn carries it as a native call, its record says it was
   read from text; a shape not read ends the step as before; a cell candidate written as text joins the candidates.
14. D83 Q154-Q156. Q154: a Python-call add_cell assigned to a name and followed by lines that only keep its result
   (the name, or one subscript of it by a constant: cell_id = result["cell_id"]) is read, the four stored shapes
   included, the keeping line recorded in not_read with name None in the reply's order; a keeping line before the
   call, from another name (bare or subscripted), from the result's name after a later statement rebound it (to
   another call's result, or by r = r["cell_id"]), with a call, an attribute, a subscript by a name or of a
   subscript, a constant, a tuple target, an augmented assignment, an assignment expression (:=) anywhere in the
   reply (one rebinding the result's name inside execute_cell's arguments included; review of wave B, S2) or prose
   around is refused; through execute_step
   the cell is added. Q155: a crash
   after the answer began (an error with first_token_s) and a stream with no final chunk are retried with the retry
   seed and their reasons; a crash on every try fails after 3 retries. Q156: when the pick call of a best-of-3 round
   crashes, the redone round sends the turn d + 1,000,000 r, candidates d * 1000 + k + 1,000,000 r and the pick
   d + 1,000,000 r, each recorded with retry 1, seed_sent and the pick's crash as the failed call; a round in a
   later turn sends first-try seeds after an earlier turn was retried (the retry does not carry over), on the native
   and the prompt-tools path; the combined
   strategy (outside Q156) keeps its first-try seeds for candidates and the combine call.
15. Q4 (Valerio, 24 Oct): an operation with a boolean field. The extraction code compiles and reads a numpy boolean
   (lung_9_schoenfeld's ground truth: before, `false` in the code was a NameError and nothing was read); the
   notebook-output fallback reads "any_violation: False" as False (before, int(float("False")) raised) and leaves a
   value that is not True or False unread; verify_results passes the operation on those values.
"""

import asyncio
import inspect
import json
import re
import sys
import tempfile
from pathlib import Path

from experiments.runner import runs_snapshot

ROOT = Path(__file__).resolve().parents[2]
# Q108 (D78): findings/runs as it is at the check's start, every path with its sha256; compared at the end
RUNS_BEFORE = runs_snapshot.take(ROOT / "findings" / "runs")
M = ROOT / "experiments" / "mentori"
sys.path.insert(0, str(M))

import tests.experiments_v2.exp_v2_8_coder_benchmark as v28  # noqa: E402
from backend.agents import lock_adapter as la  # noqa: E402
from backend.agents.model_router import ModelRouter  # noqa: E402
from backend.agents.notebook import algorithm, analyzer, api_introspector, cell_evaluator, prompts_v2  # noqa: E402
from backend.agents.notebook import step_executor as se  # noqa: E402
from backend.agents.notebook import import_scan as isc  # noqa: E402
from backend.agents.notebook.kernel import EXEC_TIMEOUT, NotebookKernel, is_exec_timeout  # noqa: E402
from backend.agents.notebook import kernel as kernel_mod  # noqa: E402
from backend.agents.notebook.schema import AlgorithmStep, CellOutput  # noqa: E402

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="check_codegen_"))
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))


def raises(exc, coro_or_fn):
    try:
        r = coro_or_fn()
        if inspect.iscoroutine(r):
            asyncio.run(r)
    except exc as e:
        return e
    return None


# ── 1. D69 Q35 ────────────────────────────────────────────────────────────────
x = v28.extract_code("```python\nhelper = 1\n```\ntext\n```python\nmain = 2\n```")
check("Q35 first block of two", x["code"] == "helper = 1" and x["n_blocks"] == 2 and x["fence_case"] == "first_block")
x = v28.extract_code("import pandas as pd\nn = 1\n```\n\nThis script loads the data.")
check("Q35 no opening fence: cut at the closing fence", x["code"] == "import pandas as pd\nn = 1"
      and x["fence_case"] == "no_opening_fence" and x["n_blocks"] == 0 and x["code_status"] == "ok", x)
x = v28.extract_code("Here is the script:\n```python\nimport pandas as pd\nresult = 1\n")
check("Q35 unclosed opening fence runs to the end", x["code"] == "import pandas as pd\nresult = 1"
      and x["fence_case"] == "unclosed_block" and x["n_blocks"] == 0 and x["first_fence_tag"] == "python", x)
x = v28.extract_code("```python\nresult = 1\n")
check("Q35 unclosed fence at the start is not empty", x["code"] == "result = 1" and x["code_status"] == "ok"
      and x["fence_case"] == "unclosed_block", x)
x = v28.extract_code("import x\nresult = 1\n```\n\nUsage example:\n```python\nprint(result)\n```")
check("Q35 continued code, later example block cut", x["code"] == "import x\nresult = 1"
      and x["fence_case"] == "no_opening_fence" and x["n_blocks"] == 1 and x["first_fence_tag"] == "", x)
x = v28.extract_code("```py\nn = 1\n```")
check("Q56 ```py opens the block (D75), tag kept", x["fence_case"] == "first_block" and x["code"] == "n = 1"
      and x["code_status"] == "ok" and x["first_fence_tag"] == "py" and x["n_blocks"] == 1, x)
x = v28.extract_code("n = 1\nprint(n)")
check("Q35 no fence: whole reply", x["code"] == "n = 1\nprint(n)" and x["fence_case"] == "no_fence"
      and x["first_fence_tag"] is None)
x = v28.extract_code("")
check("Q35 empty reply runs nothing", x["code"] == "" and x["code_status"] == "empty_reply")
x = v28.extract_code("```python\n\n```\nprose only")
check("Q35 empty code runs nothing", x["code"] == "" and x["code_status"] == "empty_code", x)
long = "x = 1\n" * 2000
x = v28.extract_code(f"```python\n{long}```")
check("code whole (no [:4000])", x["code"] == long.strip() and x["raw_reply"].startswith("```python"))

# ── 2. stated pick ────────────────────────────────────────────────────────────
# D75 Q58: a first line naming exactly one number in range is the pick ("I pick 2" now 2; "Candidate 1 is weak" now
# 1, by the same rule); a line naming two numbers stays unparsed
picks = {"2": 2, "**3**": 3, "Candidate 2.": 2, " 1 ": 1, "1. Candidate 2 is best": None, "4": None, "": None,
         "I pick 2": 2, "2\n\nCandidate 2 is the best because": 2, "\n3\nreason": 3,
         "Candidate 1 is weak\n2": 1, "The best candidate is 2.": 2, "Candidate 2 is best": 2,
         "Candidate2 is best": 2, "**Candidate 3** is the best.": 3, "Candidate 2 of 3": None,
         "Candidate 4 is best": None, "2.5": None, "uses python3, so 2": 2, "the 2nd one": None,
         "None of them; I choose candidate 0": None}
check("stated pick only (D75 Q58)", all(se.parse_stated_pick(k, 3) == v for k, v in picks.items()),
      {k: se.parse_stated_pick(k, 3) for k in picks if se.parse_stated_pick(k, 3) != picks[k]})

# ── 3. Q34 ────────────────────────────────────────────────────────────────────
check("EXEC_TIMEOUT 120", EXEC_TIMEOUT == 120 and v28.EXEC_TIMEOUT == 120)
check("kernel default is EXEC_TIMEOUT",
      inspect.signature(NotebookKernel.execute).parameters["timeout"].default == EXEC_TIMEOUT)
check("benchmark default is EXEC_TIMEOUT",
      inspect.signature(v28._execute_and_collect).parameters["timeout"].default == EXEC_TIMEOUT)
src = (M / "tests/experiments_v2/exp_v2_8_coder_benchmark.py").read_text()
check("no other limit at any benchmark site", not re.search(r"_execute_and_collect\([^)]*timeout=", src))
user_err = {"output_type": "error", "ename": "TimeoutError", "evalue": "socket timed out",
            "traceback": ["TimeoutError: socket timed out"]}
check("a TimeoutError the code raises is not exec_timeout", not is_exec_timeout(user_err))


async def _timeout_run():
    k = NotebookKernel(str(TMP / "t.ipynb"), str(TMP))
    await k.start()
    try:
        runs = []
        token = v28._SUPPORT_RUNS.set(runs)
        try:
            out = await v28._execute_and_collect(k, "import time\ntime.sleep(5)", timeout=1, stage="extraction")
            ok = await v28._execute_and_collect(k, "print('after')", stage="introspection")
            await v28._execute_and_collect(k, "print('main')")
        finally:
            v28._SUPPORT_RUNS.reset(token)
    finally:
        await k.stop()
    return out, ok, runs


out, after, support_runs = asyncio.run(_timeout_run())
check("Q34 extraction timeout recorded by stage", support_runs == [
      {"stage": "extraction", "outcome": "exec_timeout"}, {"stage": "introspection", "outcome": "ok"}], support_runs)
check("every extraction and introspection site tagged",
      not re.search(r"_execute_and_collect\(\w+, (extraction|introspect_code)\)", src)
      and src.count('stage="extraction"') == 7 and src.count('stage="introspection"') == 5)
check("exec_timeout is its own outcome", out["outcome"] == "exec_timeout" and out["timed_out"], out)
check("timeout dict form recognised", is_exec_timeout(CellOutput(output_type="error", ename="TimeoutError",
      evalue="Execution timed out after 120s", traceback=["TimeoutError: Cell execution exceeded 120s limit"])
      .to_dict()))
check("kernel usable after a timeout", after["outcome"] == "ok", after)

# ── 4. step_executor texts ────────────────────────────────────────────────────
long_out = "value " * 200
outs = [CellOutput(output_type="stream", stream_name="stdout", text=long_out),
        {"output_type": "stream", "name": "stdout", "text": "second"},
        {"output_type": "execute_result", "data": {"text/plain": "third result"}},
        CellOutput(output_type="display_data", data={"image/png": "AAA"}),
        {"output_type": "error", "ename": "KeyError", "evalue": "'x'",
         "traceback": ["\x1b[0;31mTraceback line 1\x1b[0m", "KeyError: 'x'"]}]
s = se._summarize_outputs(outs)
check("_summarize_outputs whole, objects and dicts",
      long_out in s and "second" in s and "third result" in s and "[image output]" in s
      and "KeyError: 'x'\nTraceback line 1\nKeyError: 'x'" in s and "\x1b" not in s, s[-200:])
pm = se._prompt_tools_messages([
    {"role": "user", "content": "do it"},
    {"role": "assistant", "content": "Called add_cell",
     "tool_calls": [{"function": {"name": "add_cell", "arguments": {"source": "df = load()\nprint(df)"}}}]},
    {"role": "tool", "name": "add_cell", "content": "Cell abc added successfully"}])
check("M3 prompt-tools keeps the model's own call", '"source": "df = load()\\nprint(df)"' in pm[1]["content"]
      and pm[2]["role"] == "user" and "Called add_cell" not in pm[1]["content"], pm[1])


class FakeNotebook:
    def __init__(self):
        self.cells = []

    def add_cell(self, source, cell_type="code", position=None):
        c = {"id": f"cell{len(self.cells):04d}abcdef", "source": source, "cell_type": cell_type,
             "status": "idle", "outputs": []}
        self.cells.append(c)
        return c


class FakeManager:
    def save_notebook(self, nb):
        pass


class FakeState:
    variables = {}

    def to_dict(self):
        return {"variables": []}


class FakeKernel:
    def __init__(self, outputs):
        self.outputs = outputs
        self.timeouts = []

    async def get_kernel_variables(self):
        return FakeState()

    async def execute(self, code, timeout=None):
        self.timeouts.append(timeout)
        for o in self.outputs:
            yield o


class ScriptedRouter:
    """A router whose chat answers from a script and records the messages and the candidate scope of each call."""

    def __init__(self, replies, fail=None):
        self.replies, self.fail, self.calls = list(replies), fail, []

    async def chat(self, model_identifier, messages, tools=None, options=None, think=None):
        self.calls.append({"messages": [dict(m) for m in messages], "candidate": la._candidate.get(),
                           "options": options, "tools": bool(tools)})
        if self.fail is not None:
            raise self.fail
        return self.replies.pop(0)


def tool_reply(name, args):
    return {"message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name,
                                                                                         "arguments": args}}]}}


def text_reply(text):
    return {"message": {"role": "assistant", "content": text, "tool_calls": []}}


async def run_step(router, kernel, strategy="single"):
    step = AlgorithmStep.from_dict({"step_number": 1, "description": "count", "expected_output": "print n"})
    events = []
    async for ev in se.execute_step(step=step, notebook=FakeNotebook(), notebook_manager=FakeManager(),
                                    kernel=kernel, model_router=router, model_identifier="ollama::qwen3-coder:30b",
                                    previous_results=[], cell_strategy=strategy):
        events.append(ev)
    return events


err_out = {"output_type": "error", "ename": "ValueError", "evalue": "bad", "traceback": ["ValueError: bad"]}
r = ScriptedRouter([text_reply("- pandas.read_csv()"), tool_reply("add_cell", {"source": "x = 1"}),
                    tool_reply("execute_cell", {"cell_id": "cell0000"}), text_reply("done")])
k = FakeKernel([err_out])
asyncio.run(run_step(r, k))
step_calls = [c for c in r.calls if c["tools"]]
asst = [m for m in step_calls[-1]["messages"] if m["role"] == "assistant"]
check("native assistant turn carries {'function': ...}",
      asst and asst[0]["tool_calls"][0] == {"function": {"name": "add_cell", "arguments": {"source": "x = 1"}}},
      asst[:1])
tool_msgs = [m for m in step_calls[-1]["messages"] if m["role"] == "tool"]
check("tool message states the status and the whole error", tool_msgs[-1]["content"].startswith(
      "Executed with status error. Output: ValueError: bad\nValueError: bad"), tool_msgs[-1]["content"])
check("cell executed at EXEC_TIMEOUT", k.timeouts == [EXEC_TIMEOUT], k.timeouts)
check("no options asked by the coder's calls", all(c["options"] is None for c in r.calls))

# best_of_3 cell candidates: seeds 2 and 3, pick unparsed recorded
r = ScriptedRouter([text_reply("- plan"), tool_reply("add_cell", {"source": "a = 1"}),
                    tool_reply("add_cell", {"source": "a = 2"}), tool_reply("add_cell", {"source": "a = 3"}),
                    text_reply("1. Candidate 3 is best"),
                    tool_reply("execute_cell", {"cell_id": "cell0000"}), text_reply("done")])
ev = asyncio.run(run_step(r, FakeKernel([{"output_type": "stream", "name": "stdout", "text": "1"}]), "best_of_3"))
cands = [e for e in ev if e.get("type") == "cell_candidates"]
check("Q32 cell candidates 2 and 3", [c["candidate"] for c in r.calls] == [None, None, 2, 3, None, None, None],
      [c["candidate"] for c in r.calls])
check("cell pick unparsed recorded, fallback 1", cands and cands[0]["pick"] == "unparsed"
      and cands[0]["picked_fallback"] == 1 and cands[0]["candidates"] == ["a = 1", "a = 2", "a = 3"]
      and cands[0]["judge_reply"] == "1. Candidate 3 is best", cands)
r = ScriptedRouter([text_reply("- plan"), tool_reply("add_cell", {"source": "a = 1"}),
                    tool_reply("add_cell", {"source": "a = 2"}), tool_reply("add_cell", {"source": "a = 3"}),
                    text_reply("3"), tool_reply("execute_cell", {"cell_id": "cell0000"}), text_reply("done")])
ev = asyncio.run(run_step(r, FakeKernel([]), "best_of_3"))
cands = [e for e in ev if e.get("type") == "cell_candidates"]
check("cell stated pick 3", cands and cands[0]["pick"] == 3, cands)

# ── 5. cell_evaluator ─────────────────────────────────────────────────────────
pe = cell_evaluator._parse_evaluation_response
e1 = pe("This looks good and correct", [])
e2 = pe('{"feedback": "fine", "should_retry": true}', [])
e3 = pe('{"score": "80", "feedback": "fine"}', [])
check("no JSON is unparsed, no keyword score", e1.status == "unparsed" and e1.score is None
      and e1.feedback == "This looks good and correct", e1)
check("no numeric score is unparsed", e2.status == "unparsed" and e2.score is None, e2)
check("a stated score is ok", e3.status == "ok" and e3.score == 80 and e3.meets_expectations)
e4 = pe('{"score": 20.0, "feedback": "wrong"}', [])
e5 = pe('{"score": 72.5, "feedback": "near"}', [])
e6 = pe('{"score": "72.5"}', [])
e7 = pe('{"score": true}', [])
e8 = pe('{"score": NaN}', [])
e9 = pe('{"score": "high"}', [])
check("a float score is a score: 20.0 retries, as submitted", e4.status == "ok" and e4.score == 20
      and isinstance(e4.score, int) and e4.should_retry and not e4.is_acceptable, e4)
check("72.5 and \"72.5\" used as given", e5.status == e6.status == "ok" and e5.score == e6.score == 72.5, (e5, e6))
check("true, NaN, non-numeric text are unparsed", all(e.status == "unparsed" and e.score is None
      for e in (e7, e8, e9)), (e7, e8, e9))
check("no score is accepted without retry, as before", e1.is_acceptable and not e1.should_retry)
step = AlgorithmStep.from_dict({"step_number": 1, "description": "d", "expected_output": "print"})
cell = {"id": "c1", "source": "s" * 3000, "status": "success",
        "outputs": [{"output_type": "stream", "name": "stdout", "text": "o" * 5000}]}


class FailRouter:
    def __init__(self, exc):
        self.exc, self.messages = exc, None

    async def chat(self, model_identifier, messages, **kw):
        self.messages = messages
        raise self.exc


rec = {"model": "qwen3-coder:30b", "status": "error", "error": "boom"}
fr = FailRouter(la.LockCallError(rec))
ev_err = asyncio.run(cell_evaluator._evaluate_with_llm(cell, step, fr, "ollama::qwen3-coder:30b"))
check("failed evaluation call is status error, no score", ev_err.status == "error" and ev_err.score is None
      and ev_err.is_acceptable, ev_err)
check("evaluator prompt has the whole source and output", "s" * 3000 in fr.messages[0]["content"]
      and "o" * 5000 in fr.messages[0]["content"])
check("evaluator passes a LockError through", raises(LockError, lambda: cell_evaluator._evaluate_with_llm(
      cell, step, FailRouter(LockError("x")), "ollama::m")) is not None)
tb = ["Traceback (most recent call last):", "  File x, line 1", "\x1b[31mKeyError\x1b[0m: " + "k" * 400]
errs = cell_evaluator._extract_cell_errors({"outputs": [{"output_type": "error", "ename": "KeyError",
                                                         "evalue": "k", "traceback": tb}]})
q = cell_evaluator._quick_evaluation({"outputs": [{"output_type": "error", "ename": "KeyError", "evalue": "v" * 300,
                                                   "traceback": tb}]}, step)
check("whole ANSI-stripped traceback", errs[1] == "Traceback (most recent call last):\n  File x, line 1\nKeyError: "
      + "k" * 400, errs)
check("retry feedback whole", q.feedback == "Cell execution failed with error: KeyError: " + "v" * 300)

# ── 6. prompts_v2 ─────────────────────────────────────────────────────────────
ks = prompts_v2.build_kernel_state_summary({"variables": [{"name": f"df{i}", "type": "DataFrame"} for i in range(7)]})
check("every variable listed", all(f"df{i}" in ks for i in range(7)), ks)


class R:
    success, variables_created, files_created = True, [], []
    cells_created = [{"source": "y = 2\n" * 300, "cell_type": "code"}]


ps = prompts_v2.build_previous_steps_with_code([R()])
check("previous code whole", ("y = 2\n" * 300).strip() in ps and "truncated" not in ps)
nb = prompts_v2.build_notebook_summary({"cells_summary": [{"id": f"id{i:06d}", "source": "z" * 100} for i in range(12)]})
check("every cell, whole source", nb.count("z" * 100) == 12, nb[-150:])

# ── 7/8. plan candidates and setup errors ─────────────────────────────────────
seen = []


class StreamRouter:
    def __init__(self, fail=None):
        self.fail = fail

    async def chat_stream(self, model_identifier, messages, tools=None, think=None, options=None):
        seen.append(la._candidate.get())
        if self.fail:
            raise self.fail
        plan = {"task_summary": "t", "steps": [{"step_number": 1, "description": "d", "expected_output": "e"}]}
        yield json.dumps({"message": {"content": json.dumps(plan)}})


class NBState:
    def to_context_string(self):
        return "empty"


saved = algorithm.N_CANDIDATES
algorithm.N_CANDIDATES = 3
asyncio.run(algorithm.generate_algorithm(StreamRouter(), "ollama::m", "req", NBState()))
three = list(seen)
seen.clear()
algorithm.N_CANDIDATES = 1
asyncio.run(algorithm.generate_algorithm(StreamRouter(), "ollama::m", "req", NBState()))
check("Q32 plan candidates 1-3 (judge seed draw)", three == [1, 2, 3, None] and seen == [None], (three, seen))
check("algorithm passes a LockError through", raises(LockError, lambda: algorithm.generate_algorithm(
      StreamRouter(LockError("x")), "ollama::m", "req", NBState())) is not None)
algorithm.N_CANDIDATES = saved
check("analyser passes a LockError through", raises(LockError, lambda: analyzer.analyze_request(
      "make a plot of the data please now", None, "", None, FailRouter(LockError("x")), "ollama::m")) is not None)
ar = asyncio.run(analyzer.analyze_request("q " * 80, None, "", None, FailRouter(RuntimeError("x")), "ollama::m"))
check("analyser fallback keeps the whole request", ar.detected_intent == "q " * 80)
check("introspector passes a LockError through", raises(LockError, lambda: api_introspector.introspect_step(
      FailRouter(LockError("x")), "ollama::m", "d", "e", "")) is not None)
check("step passes a LockError through", raises(LockError, lambda: run_step(
      ScriptedRouter([], fail=LockError("x")), FakeKernel([]))) is not None)
check("API reference whole", "m25" in v28._build_api_reference([{"module": "a", "object": "B",
      "methods": [f"m{i}" for i in range(30)], "attributes": [], "docstring": "d" * 900}])
      and "d" * 900 in v28._build_api_reference([{"module": "a", "object": "B", "docstring": "d" * 900}]))

# ── 9. exp_05 end to end, fake transport ──────────────────────────────────────

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("exp05", M / "publication/scripts/exp_05_coder_benchmark.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PROJECT_ROOT = TMP
mod.V4_RESULTS_DIR = TMP / "results_v4"
check("exp_05 reads no database", not hasattr(mod, "find_admin_user_id"))
_sink = ex.sink
ex.sink = lambda run, root=TMP / "runs": _sink(run, root)
ex._run_sink = ex.sink               # context() without sink= resolves through _run_sink: never findings/runs

PASS_CODE = "genes = 38694\nsamples = 8\nmetadata_rows = 8\n"
script = {"free_form": PASS_CODE + "```\nThis sets the three values.", "pick": "1. Candidate 2 is best"}


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


def fake_generate(base_url, call, prompt, passages=None, images=None):
    if "SCORE:" in prompt:
        text = "The script ran but the numbers differ."          # no SCORE line: "unparsed"
    elif "Respond with ONLY the number" in prompt:
        text = script["pick"]
    else:
        text = script["free_form"] if call.candidate in (None, 1) else "genes = 1\n"
    return base(call, base_url, passages, text)


def fake_chat(base_url, call, messages, passages=None, tools=None, fmt=None):
    first = messages[0].get("content", "") if messages else ""
    last = messages[-1]
    if first.startswith("Analyze this user request"):
        return base(call, base_url, passages, '{"classification": "complex", "detected_intent": "dims"}', [])
    if any(m.get("role") == "system" and "algorithm designer" in (m.get("content") or "") for m in messages):
        plan = {"task_summary": "dims", "steps": [{"step_number": 1, "description": "set the values",
                                                   "expected_output": "print the values"}]}
        return base(call, base_url, passages, json.dumps(plan), [])
    if first.startswith("You are planning Python code"):
        return base(call, base_url, passages, "- pandas.read_csv(path) -> DataFrame", [])
    if first.startswith("Evaluate if this cell output"):
        return base(call, base_url, passages, "Looks right to me.", [])     # unparsed
    if first.startswith("Implement this step"):
        if last["role"] == "user":
            return base(call, base_url, passages, "", [{"function": {"name": "add_cell", "arguments": {
                "source": PASS_CODE + "print(genes, samples, metadata_rows)"}}}])
        if last["role"] == "tool" and "added" in last["content"]:
            cid = last["content"].split()[1]
            return base(call, base_url, passages, "", [{"function": {"name": "execute_cell",
                                                                     "arguments": {"cell_id": cid}}}])
        return base(call, base_url, passages, "Done.", [])
    return base(call, base_url, passages, "?", [])


la.ollama_client.generate = fake_generate
la.ollama_client.chat = fake_chat
v = mod.select(mod.variants(), "ollama::qwen3-coder:30b", "default")[0]
ops = mod.load_ops(1)
asyncio.run(mod.run_variant(v, ["free_form", "free_form_n3_best", "coder_v2_n1"], ops, "http://127.0.0.1:9"))


def answers(config):
    sink = TMP / "runs" / f"exp_05__{config}__qwen3-coder-30b+default"
    return (json.loads((sink / "answers.json").read_text())["results"][0],
            [json.loads(line) for line in (sink / "calls.jsonl").read_text().splitlines()])


ff, ff_calls = answers("free_form")
check("free_form passes after the Q35 cut", ff["passed"] and ff["exec_outcome"] == "ok", ff.get("exec_error"))
g = ff["generations"][0]
check("free_form stores raw reply, code, blocks, case", g["raw_reply"] == script["free_form"]
      and ff["code"] == PASS_CODE.strip() and g["n_blocks"] == 0 and g["fence_case"] == "no_opening_fence"
      and g["call_seq"] == 1, g)
check("attempt calls from the records", ff["n_calls"] == len(ff_calls) == 1 and ff["calls"][0]["options_sent"]
      == ff_calls[0]["options_sent"] and ff["calls"][0]["options_sent"]["num_ctx"] == 131072, ff["calls"])
check("no options asked", all(c["caller_asked"]["options"] is None for c in ff_calls))

n3, n3_calls = answers("free_form_n3_best")
check("n3 pick unparsed, candidate 1 ran", n3["pick"] == "unparsed" and n3["picked_fallback"] == 1
      and n3["code"] == PASS_CODE.strip() and n3["passed"], {k: n3[k] for k in ("pick", "picked_fallback")})
check("n3 stores every candidate and the pick reply", [x["stage"] for x in n3["generations"]]
      == ["candidate_1", "candidate_2", "candidate_3", "pick"] and n3["generations"][3]["raw_reply"]
      == script["pick"])
check("n3 candidate seeds", [c["options_sent"]["seed"] for c in n3_calls] == [1001, 1002, 1003, 1], n3_calls)

cv, cv_calls = answers("coder_v2_n1")
check("coder_v2 runs without a database", cv["exec_outcome"] == "ok" and cv["passed"], cv.get("exec_error"))
check("coder_v2 evaluation unparsed, no score", cv["cell_evaluations"]
      and all(e["status"] == "unparsed" and e["score"] is None for e in cv["cell_evaluations"]),
      cv["cell_evaluations"])
check("coder_v2 stores the notebook's code whole", cv["code_cells"]
      and cv["code_cells"][0] == PASS_CODE + "print(genes, samples, metadata_rows)", cv.get("code_cells"))
check("free_form stores its extraction outcome", ff["extract_outcomes"] == ["ok"]
      and ff["introspect_outcomes"] == [], (ff.get("extract_outcomes"), ff.get("introspect_outcomes")))
cv2_src = inspect.getsource(v28._run_coder_v2)
check("coder_v2 counts step_retry, n_llm_calls None", cv["n_llm_calls"] is None and cv["n_retries"] == 0
      and '"step_retry"' in cv2_src and "cell_retry" not in cv2_src.replace('"cell_retry", which', "")
      and "token_usage" not in cv2_src.replace('"token_usage", which', ""), (cv["n_llm_calls"], cv["n_retries"]))
check("coder_v2 stores its history (plan, steps, summary)", [h["metadata_blob"]["phase"]
      for h in cv.get("history_log") or []][:1] == ["planning"]
      and cv["history_log"][-1]["metadata_blob"]["phase"] == "summary", cv.get("history_log"))
check("coder_v2 call records", cv["n_calls"] == len(cv_calls) >= 5
      and all(c["caller_asked"]["options"] is None for c in cv_calls), cv["n_calls"])

script["free_form"] = ""
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+empty"), ["free_form"], ops, "http://127.0.0.1:9"))
em = json.loads((TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+empty" / "answers.json").read_text())["results"][0]
check("empty reply runs nothing", em["exec_outcome"] == "not_run" and em["code"] == ""
      and em["generations"][0]["code_status"] == "empty_reply" and not em["passed"], em["exec_error"])
check("soft-pass judge unparsed (was FAIL)", em["judge_score"] == "unparsed", em["judge_score"])

reports = sorted((TMP / "results_v4").glob("*_latest.json"))
rep = json.loads(reports[-1].read_text()) if reports else {}
check("report options_sent from records, no num_ctx constant", "num_ctx" not in rep and rep.get("options_sent")
      and all(o["options_sent"].get("num_ctx") == 131072 for o in rep["options_sent"]), rep.get("options_sent"))

# soft-pass judge call error
fr = FailRouter(la.LockCallError(rec))


class GenFail:
    async def generate(self, **kw):
        raise la.LockCallError(rec)


ctx = ex.context("exp_05", "free_form", ops[0]["op_id"], 1, {"coder": "ollama::qwen3-coder:30b"}, "default",
                 base_url="http://127.0.0.1:9", run="exp_05__free_form__qwen3-coder-30b+judgefail")
with rc.run(ctx):
    js = asyncio.run(v28._evaluate_failed_result(ops[0], {}, "err", GenFail()))
check("soft-pass judge error (was FAIL)", js[0] == "error", js)

# D72 records through exp_05: a script importing a module not on the allow-list fails as the model's error
script["free_form"] = "import json\nimport surely_missing_d72\ngenes = 38694\n"
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+d72"), ["free_form"], ops, "http://127.0.0.1:9"))
na = json.loads((TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+d72" / "answers.json").read_text())["results"][0]
check("D72 not_allowed: the model's error, flagged", na["exec_outcome"] == "error" and not na["passed"]
      and na["missing_library_not_allowed"] is True and na["missing_not_allowed"] == ["surely_missing_d72"]
      and na["imports"] == ["json", "surely_missing_d72"] and na["missing_installed"] == []
      and na["import_scans"][0]["classification"] == {"json": {"status": "stdlib"},
                                                      "surely_missing_d72": {"status": "not_allowed"}}
      and na["import_scans"][0]["error_not_allowed_module"] == "surely_missing_d72",
      {k: na.get(k) for k in ("exec_outcome", "imports", "missing_not_allowed", "missing_library_not_allowed")})
check("D72 fields on every attempt", all(e.get(f) is not None for e in (ff, n3, cv, na) for f in (
      "imports", "missing_installed", "missing_not_allowed", "install_lines", "missing_library_not_allowed",
      "import_scans"))
      and ff["missing_library_not_allowed"] is False and len(ff["import_scans"]) == 1
      and len(n3["import_scans"]) == 1 and len(cv["import_scans"]) >= 2,
      {k: (len(e["import_scans"]) if e.get("import_scans") is not None else None)
       for k, e in (("ff", ff), ("n3", n3), ("cv", cv))})

# ── 10. D72 import scan ───────────────────────────────────────────────────────
check("D72 scan import and from-import", isc.scan("import pandas as pd, numpy\nfrom scipy.stats import ttest_ind\n"
      "import os.path\n") == ["numpy", "os", "pandas", "scipy"])
check("D72 scan nested imports", isc.scan("def f():\n    import lifelines\n    class C:\n        from statsmodels."
      "api import OLS\ntry:\n    import pydeseq2.dds\nexcept ImportError:\n    pass\n")
      == ["lifelines", "pydeseq2", "statsmodels"])
check("D72 scan relative imports left out", isc.scan("from . import x\nfrom .y import z\nimport w\n") == ["w"])
mods, how = isc.scan_with_method("%matplotlib inline\n!pip install gseapy\nimport pandas as pd\n"
                                 "  from pingouin import anova\nimport a.b as c, d\nx = (\n")
check("D72 syntax error falls back to the regex", how == "regex" and mods == ["a", "d", "pandas", "pingouin"],
      (how, mods))
check("D72 importlib and __import__ with a literal", isc.scan("import importlib\nm = importlib.import_module("
      "'seaborn.objects')\nn = __import__(\"gseapy\")\nfrom importlib import import_module\nk = import_module('"
      "sklearn')\nq = importlib.import_module(name)\nr = importlib.import_module('.rel', 'pkg')\n")
      == ["gseapy", "importlib", "seaborn", "sklearn"])
check("D72 regex fallback catches importlib literals", isc.scan("!ls\nimportlib.import_module('pingouin')\n")
      == ["pingouin"])
f4 = {'exec("import pingouin")': ["pingouin"],
      "import importlib\nimportlib.import_module(name='pingouin')": ["importlib", "pingouin"],
      "from importlib import import_module as im; im('pingouin')": ["importlib", "pingouin"],
      "import importlib\nimportlib.__import__('pingouin')": ["importlib", "pingouin"],
      "compile(source='import lifelines', filename='x', mode='exec')": ["lifelines"],
      "!ls\nimport os; import pingouin": ["os", "pingouin"], "!ls\ntry: import pingouin": ["pingouin"],
      "!ls\nif 1: from pingouin import anova": ["pingouin"], "!ls\nexec('import seaborn')": ["seaborn"],
      "!ls\nx = import_module(name='lifelines')": ["lifelines"]}
f4_got = {c: isc.scan(c) for c in f4}
check("D72 scan exec literals, import_module alias and name=, attribute __import__, compound lines",
      f4_got == f4, {c: g for c, g in f4_got.items() if g != f4[c]})
il = isc.install_lines("!pip install gseapy\nimport pandas\n%pip install -q x\nsubprocess.run(['uv', 'pip', "
                       "'install', 'y'])\nsubprocess.run([sys.executable, '-m', 'pip', 'install', 'z'])\n"
                       "install_package('w')\nx = 'pipeline install'\n")
check("D72 install lines recorded", il == ["!pip install gseapy", "%pip install -q x",
      "subprocess.run(['uv', 'pip', 'install', 'y'])", "subprocess.run([sys.executable, '-m', 'pip', 'install', 'z'])",
      "install_package('w')"], il)
import tomllib  # noqa: E402
lock_versions = {p["name"]: p["version"] for p in tomllib.loads((M / "uv.lock").read_text())["package"]}
check("D72 ALLOW_LIST pins are uv.lock's", set(isc.ALLOW_LIST) == {"pandas", "numpy", "scipy", "sklearn",
      "lifelines", "statsmodels", "pydeseq2", "pingouin", "matplotlib", "seaborn"}
      and all(lock_versions.get(r.split("==")[0]) == r.split("==")[1] for r in isc.ALLOW_LIST.values())
      and isc.ALLOW_LIST["statsmodels"] == "statsmodels==0.14.6" and isc.ALLOW_LIST["pydeseq2"] == "pydeseq2==0.5.4"
      and isc.ALLOW_LIST["pingouin"] == "pingouin==0.7.0",
      {m: (r, lock_versions.get(r.split("==")[0])) for m, r in isc.ALLOW_LIST.items()})


class Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


commands = []


def fake_run(cmd, **kw):
    commands.append(list(cmd))
    if cmd[1:3] == ["pip", "freeze"]:
        return Proc(0, "numpy==2.4.1\nscipy==1.17.0\nlocalpkg @ file:///opt/localpkg\n-e file:///opt/editable\n")
    if cmd[1:3] == ["pip", "install"]:
        return Proc(fake_run.install_rc, "", "resolved")
    raise AssertionError(f"unexpected command {cmd}")


fake_run.install_rc = 0
states = {"json": "stdlib", "pandas": "present", "gseapy": "missing", "pydeseq2": "missing"}
cl = isc.check(["json", "pandas", "gseapy"], "/opt/kpy/bin/python", probe=lambda ms: states, run=fake_run)
check("D72 classification stdlib, present, not_allowed", cl == {"json": {"status": "stdlib"},
      "pandas": {"status": "present"}, "gseapy": {"status": "not_allowed"}}, cl)
check("D72 nothing run for not_allowed", commands == [], commands)
cl = isc.check(["pandas", "pydeseq2"], "/opt/kpy/bin/python", probe=lambda ms: states, run=fake_run)
installs = [c for c in commands if c[1:3] == ["pip", "install"]]
inst = cl["pydeseq2"]
check("D72 one install command, the pin, the probed interpreter", len(installs) == 1
      and installs[0][-1] == "pydeseq2==0.5.4" and installs[0][3:5] == ["--python", "/opt/kpy/bin/python"]
      and "--constraint" in installs[0] and inst["status"] == "installed" and inst["install"]["exit_status"] == 0
      and inst["install"]["requirement"] == "pydeseq2==0.5.4" and inst["install"]["held"] == 3, (installs, inst))
commands.clear()
fake_run.install_rc = 2
cl = isc.check(["pydeseq2"], "/opt/kpy/bin/python", probe=lambda ms: states, run=fake_run)
check("D72 a failed install is recorded", cl["pydeseq2"]["status"] == "installed"
      and cl["pydeseq2"]["install"]["exit_status"] == 2 and cl["pydeseq2"]["install"]["stderr"] == "resolved", cl)
real = isc.probe_subprocess(["json", "pandas", "surely_missing_d72"], sys.executable)
check("D72 probe in a real interpreter", real == {"json": "stdlib", "pandas": "present",
      "surely_missing_d72": "missing"}, real)
check("D72 ModuleNotFoundError parsed", isc.missing_module("ModuleNotFoundError", "No module named 'a.b'") == "a"
      and isc.missing_module("ImportError", "No module named 'a'") is None)
na_rec = {"modules": ["x"], "classification": {"x": {"status": "not_allowed"}}, "error": {"ename": "M"},
          "error_not_allowed_module": "x"}
other_err = {"modules": [], "classification": {}, "error": {"ename": "NameError"}, "error_not_allowed_module": None}
clean = {"modules": ["pandas"], "classification": {"pandas": {"status": "present"}}, "error": None,
         "error_not_allowed_module": None}


def run_of(rec, n):
    return dict(rec, kernel_run=n)


def flag(records, passed=False, outcome="error"):
    return isc.attempt_fields(records, passed=passed, exec_outcome=outcome)["missing_library_not_allowed"]


check("D72 flag only when every error is a not_allowed module", flag([na_rec, other_err]) is False
      and flag([na_rec]) is True and flag([]) is False and isc.attempt_fields([na_rec])[
          "missing_library_not_allowed"] is False)
check("D72 flag judged on the final kernel run of a failed attempt",
      # coder_v2: a cell failed on a not_allowed import, was fixed, and the re-run in a fresh kernel passed
      flag([run_of(na_rec, 1), run_of(clean, 2)], passed=True, outcome="ok") is False
      # the same run in one kernel (the fixed cell after the failed one): passed, so no failure to flag
      and flag([run_of(na_rec, 1), run_of(clean, 1)], passed=True, outcome="ok") is False
      # recovery: an AttributeError first, then a retry (kernel restarted) failing only on a not_allowed module
      and flag([run_of(other_err, 1), run_of(na_rec, 2)]) is True
      # the reverse: the final run's error is not the missing module
      and flag([run_of(na_rec, 1), run_of(other_err, 2)]) is False
      # a retry with no code (not_run) is not flagged on the earlier run's error
      and flag([run_of(na_rec, 1)], outcome="not_run") is False
      and flag([run_of(na_rec, 3)], outcome="step_failed") is True)


async def _kernel_scan():
    k = NotebookKernel(str(TMP / "d72.ipynb"), str(TMP))
    await k.start()
    calls, recs = [], []
    real_install, real_probe, real_sub = isc.install, k._probe_imports, isc.probe_subprocess
    token = isc.SCANS.set(recs)

    def no_subprocess(*a, **kw):
        raise AssertionError("the stand-alone probe ran: the kernel's probe was not the one used")
    isc.probe_subprocess = no_subprocess
    try:
        isc.install = lambda m, py, run=None: calls.append((m, py)) or {"module": m, "requirement": isc.ALLOW_LIST[m],
                                                                        "exit_status": 0}
        a = await v28._execute_and_collect(k, "import json\nimport pandas\nimport surely_missing_d72\n")
        b = await v28._execute_and_collect(k, "import surely_missing_d72\n", stage="extraction")
        no_install = list(calls)

        async def missing_once(modules):
            data = await real_probe(modules)
            if "pingouin" in modules and not calls:
                data["modules"]["pingouin"] = "missing"
            return data
        k._probe_imports = missing_once
        c = await v28._execute_and_collect(k, "import pingouin\nn = 1\n")
        exe = "".join(o.text or "" for o in [x async for x in k.execute("import sys; print(sys.executable)",
                                                                        silent=True)])
    finally:
        isc.SCANS.reset(token)
        isc.install = real_install
        isc.probe_subprocess = real_sub
        await k.stop()
    return a, b, c, recs, calls, no_install, exe.strip()


a, b, c, recs, calls, no_install, exe = asyncio.run(_kernel_scan())
check("D72 kernel: interpreter is the kernel's own", recs and recs[0]["python"] == exe
      and recs[0]["probe"] == "kernel" and recs[0]["probe_error"] is None and recs[0]["kernel_run"] is not None,
      (recs[:1], exe))
check("D72 kernel: classification and not_allowed error", a["outcome"] == "error"
      and recs[0]["classification"] == {"json": {"status": "stdlib"}, "pandas": {"status": "present"},
                                        "surely_missing_d72": {"status": "not_allowed"}}
      and recs[0]["error_not_allowed_module"] == "surely_missing_d72" and no_install == [], recs[:1])
check("D72 kernel: harness code (extraction) not scanned", b["outcome"] == "error" and len(recs) == 2, len(recs))
check("D72 kernel: missing allow-listed module installed once at its pin, then found", calls == [("pingouin", exe)]
      and recs[1]["classification"]["pingouin"]["status"] == "installed"
      and recs[1]["classification"]["pingouin"]["present_after"] is True and c["outcome"] == "ok", (calls, recs[1:]))


async def _kernel_probe_failures():
    k = NotebookKernel(str(TMP / "d72b.ipynb"), str(TMP))
    await k.start()
    recs, out = [], {}
    token = isc.SCANS.set(recs)
    real_probe = k._probe_imports
    try:
        await v28._execute_and_collect(k, "print = lambda *a, **kw: None\n")
        out["rebound"] = await v28._execute_and_collect(k, "import pandas\n__builtins__.print('ran')\n")

        async def broken(modules):
            raise RuntimeError("D72 import probe failed in the kernel: ''")
        k._probe_imports = broken
        out["fallback"] = await v28._execute_and_collect(k, "import json, pandas\n__builtins__.print('ran')\n")
        k._probe_python = None
        out["unscanned"] = await v28._execute_and_collect(k, "import pandas\n__builtins__.print('ran')\n")
    finally:
        isc.SCANS.reset(token)
        k._probe_imports = real_probe
    probed = []

    async def counting(modules):
        probed.append(modules)
        return await real_probe(modules)
    k._probe_imports = counting
    try:
        out["no_recorder"] = await v28._execute_and_collect(k, "import pandas\n__builtins__.print('ran')\n")
    finally:
        await k.stop()
    return recs, out, probed


recs2, out2, probed2 = asyncio.run(_kernel_probe_failures())
check("D72 kernel: a rebound print does not stop the probe", out2["rebound"]["outcome"] == "ok"
      and recs2[1]["probe"] == "kernel" and recs2[1]["classification"] == {"pandas": {"status": "present"}}
      and "ran" in out2["rebound"]["stdout"], (out2["rebound"], recs2[1:2]))
check("D72 kernel: a failed probe is recorded, the stand-alone probe stands in, the code runs",
      out2["fallback"]["outcome"] == "ok" and "ran" in out2["fallback"]["stdout"]
      and recs2[2]["probe"] == "subprocess" and recs2[2]["probe_error"].startswith("RuntimeError")
      and recs2[2]["classification"] == {"json": {"status": "stdlib"}, "pandas": {"status": "present"}},
      recs2[2:3])
check("D72 kernel: with no probe at all the code still runs, unclassified", out2["unscanned"]["outcome"] == "ok"
      and "ran" in out2["unscanned"]["stdout"] and recs2[3]["probe"] is None and recs2[3]["probe_error"]
      and recs2[3]["classification"] == {}, recs2[3:4])
check("D72 no scan without a recorder", isc.SCANS.get() is None and probed2 == [] and len(recs2) == 4
      and out2["no_recorder"]["outcome"] == "ok" and out2["no_recorder"]["stdout"].strip() == "ran",
      (probed2, out2["no_recorder"]))

# ── 11. D75 (round 3: Q56-Q64, Q101) ─────────────────────────────────────────
# Q56: a fence tagged python, py or python3 in any case opens the block; a bare ``` opens it only at the top
q56 = {"```Python\nn = 1\n```": ("first_block", "n = 1"), "```python3\nn = 1\n```": ("first_block", "n = 1"),
       "```PY\nn = 1\n```\nmore": ("first_block", "n = 1"), "\n  ```\nn = 1\n```\ntext": ("first_block", "n = 1"),
       "Here is the code:\n```py\nn = 1\n```": ("first_block", "n = 1"),
       "Here is the code:\n```\nn = 1\n```": ("no_opening_fence", "Here is the code:"),
       "n = 1\n```\n\n```\nprint(n)\n```": ("no_opening_fence", "n = 1"),
       "```bash\npip list\n```": ("no_opening_fence", ""), "```py\nn = 1\n": ("unclosed_block", "n = 1"),
       "```\nn = 1\n": ("unclosed_block", "n = 1"),
       "```python n = 1```": ("first_block", "n = 1"), "```python title=a.py\nn = 1\n```": ("first_block", "n = 1"),
       "```Py  {.numberLines}\nn = 1\n```": ("first_block", "n = 1"),
       "```pyspark\nn = 1\n```": ("no_opening_fence", ""),
       "```python\r\nn = 1\r\n```": ("first_block", "n = 1")}
q56_got = {r: (v28.extract_code(r)["fence_case"], v28.extract_code(r)["code"]) for r in q56}
check("Q56 opening fence: python, py, python3 any case; bare only at the top", q56_got == q56,
      {r: g for r, g in q56_got.items() if g != q56[r]})
check("Q56 python block unchanged", v28.extract_code("```python\nhelper = 1\n```")["code"] == "helper = 1"
      and v28.extract_code("text\n```python\na = 1\n```\n```py\nb = 2\n```")["n_blocks"] == 2)
q56n = {r: v28.extract_code(r)["n_blocks"] for r in ("```python x = 1```", "```python\r\nx = 1\r\n```",
        "```python title=a.py\nx = 1\n```", "```pyspark\nx = 1\n```", "```python3\nx = 1\n```")}
check("Q56 block count: one-line, CRLF and attribute blocks count, pyspark does not", q56n == {
      "```python x = 1```": 1, "```python\r\nx = 1\r\n```": 1, "```python title=a.py\nx = 1\n```": 1,
      "```pyspark\nx = 1\n```": 0, "```python3\nx = 1\n```": 1}, q56n)

# Q57: a reply run as code that ended on "length" runs nothing, whatever its fences, outcome "length"
for reply in ("```python\nx = 1\n", "```python\nx = 1\n```", "x = 1"):
    gl = v28._generation("code", {"response": reply, "done_reason": "length"})
    gs = v28._generation("code", {"response": reply, "done_reason": "stop"})
    check(f"Q57 length runs nothing ({gl['fence_case']})", gl["code_status"] == "length" and gl["code"] == "x = 1"
          and gs["code_status"] == "ok", (gl, gs))
check("Q57 not-run outcomes", v28._not_run("length")[0] == "length" and v28._not_run("empty_code")[0] == "not_run"
      and "length" in v28.EXEC_OUTCOMES and v28._generation("pick", {"response": "2", "done_reason": "length"},
                                                             code=False) == {"stage": "pick", "stop_reason": "length",
                                                                             "call_seq": None, "raw_reply": "2"})
q57_src = inspect.getsource(v28)
check("Q57 no site sets not_run by hand", q57_src.count('exec_outcome = "not_run"') == 0
      and q57_src.count("_not_run(") >= 6, q57_src.count("_not_run("))


def length_generate(base_url, call, prompt, passages=None, images=None):
    r = fake_generate(base_url, call, prompt, passages, images)
    if "## Python Code" in prompt or "Write the corrected Python code" in prompt:
        r["status"], r["stop_reason"] = "length", "length"
    return r


la.ollama_client.generate = length_generate
script["free_form"] = "```python\n" + PASS_CODE
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+len"), ["free_form", "free_form_n3_best"], ops,
                            "http://127.0.0.1:9"))
le = json.loads((TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+len" / "answers.json").read_text())["results"][0]
ln3 = json.loads((TMP / "runs" / "exp_05__free_form_n3_best__qwen3-coder-30b+len" / "answers.json")
                 .read_text())["results"][0]
check("Q57 exp_05: a length reply is outcome length, nothing ran", le["exec_outcome"] == "length"
      and not le["passed"] and le["generations"][0]["code_status"] == "length" and le["import_scans"] == []
      and le["extract_outcomes"] == [] and ln3["exec_outcome"] == "length", (le["exec_outcome"], le["exec_error"]))
la.ollama_client.generate = fake_generate


def thinker_length_generate(base_url, call, prompt, passages=None, images=None):
    if prompt.startswith("You are a research assistant"):
        r = base(call, base_url, passages, "```python\nimport lifelines\nprint(dir(lifelines")
        r["status"], r["stop_reason"] = "length", "length"
        return r
    return fake_generate(base_url, call, prompt, passages, images)


la.ollama_client.generate = thinker_length_generate
script["free_form"] = PASS_CODE + "```\n"
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+thlen"), ["thinker_coder_split"], ops,
                            "http://127.0.0.1:9"))
la.ollama_client.generate = fake_generate
th = json.loads((TMP / "runs" / "exp_05__thinker_coder_split__qwen3-coder-30b+thlen" / "answers.json")
                .read_text())["results"][0]
check("Q57 thinker_coder_split: an introspection reply cut by length fails the attempt as length, nothing runs",
      th["exec_outcome"] == "length" and th["introspect_outcome"] == "length" and not th["passed"]
      and [g["stage"] for g in th["generations"]] == ["introspection_code"] and th["import_scans"] == []
      and th["introspect_outcomes"] == [] and th["extract_outcomes"] == [], (th["exec_outcome"], th["exec_error"],
                                                                             [g["stage"] for g in th["generations"]]))

# Q58 through exp_05: "The best candidate is 2." runs candidate 2
script["free_form"] = PASS_CODE + "```\n"
script["pick"] = "The best candidate is 2."
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+q58"), ["free_form_n3_best"], ops, "http://127.0.0.1:9"))
p58 = json.loads((TMP / "runs" / "exp_05__free_form_n3_best__qwen3-coder-30b+q58" / "answers.json")
                 .read_text())["results"][0]
check("Q58 a stated single number is the pick", p58["pick"] == 2 and p58["picked_fallback"] is None
      and p58["code"] == "genes = 1", {k: p58[k] for k in ("pick", "picked_fallback", "code")})

# Q59: kept as built (no score, no retry), counted
check("Q59 no score is accepted without retry", cell_evaluator.CellEvaluation(
      None, False, False, "", [], [], [], status="unparsed").is_acceptable)

# Q60: an instance entry and a bare error entry are labelled, not a KeyError
ref = v28._build_api_reference([
    {"module": "lifelines", "object": "KaplanMeierFitter", "methods": ["fit"], "attributes": ["median_survival_time_"]},
    {"object": "kmf", "type": "KaplanMeierFitter", "methods": ["fit"], "attributes": ["median_survival_time_"]},
    {"error": "boom"}, {"module": "x", "object": "Y", "error": "No module named 'x'"}])
check("Q60 labels by module, else by type; error entries readable", ref.splitlines() == [
      "- lifelines.KaplanMeierFitter methods: fit", "- lifelines.KaplanMeierFitter attributes: median_survival_time_",
      "- kmf (a KaplanMeierFitter) methods: fit", "- kmf (a KaplanMeierFitter) attributes: median_survival_time_",
      "- [introspection error: boom]", "- x.Y: [error: No module named 'x']"], ref)

FAIL_KMF = ("from lifelines import KaplanMeierFitter\nkmf = KaplanMeierFitter()\nm = kmf.median_\n")


def recovery_generate(base_url, call, prompt, passages=None, images=None):
    if prompt.startswith("The code execution failed with this error"):
        return base(call, base_url, passages, "```python\n" + PASS_CODE + "```")
    if prompt.startswith("Analyze this scientific computing task"):
        return base(call, base_url, passages, '[{"module": "lifelines", "object": "KaplanMeierFitter"}]')
    if "## Python Code" in prompt:
        return base(call, base_url, passages, "```python\n" + FAIL_KMF + "```")
    return fake_generate(base_url, call, prompt, passages, images)


la.ollama_client.generate = recovery_generate
asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+q60"), ["error_recovery_introspect",
                                                                   "introspect_with_recovery"], ops,
                            "http://127.0.0.1:9"))
la.ollama_client.generate = fake_generate
for cfg in ("error_recovery_introspect", "introspect_with_recovery"):
    sink60 = TMP / "runs" / f"exp_05__{cfg}__qwen3-coder-30b+q60"
    r60 = json.loads((sink60 / "answers.json").read_text())["results"][0]
    c60 = [json.loads(line) for line in (sink60 / "calls.jsonl").read_text().splitlines()]
    retry = [c["prompt_sent"] for c in c60 if (c.get("prompt_sent") or "").startswith("The code execution failed")]
    check(f"Q60 {cfg}: the AttributeError on a script variable reaches its retry and passes",
          r60["passed"] and r60["exec_outcome"] == "ok" and r60["n_retries"] == 1 and len(retry) == 1
          and "kmf (a KaplanMeierFitter)" in retry[0] and "lifelines.KaplanMeierFitter" in retry[0]
          and "AttributeError: 'KaplanMeierFitter' object has no attribute 'median_'" in retry[0],
          (r60["exec_outcome"], r60["exec_error"]))
    # Q61: the retry gets ename: evalue and the introspection, no traceback and no earlier code
    check(f"Q61 {cfg}: retry prompt holds no traceback and no earlier code", retry
          and "Traceback" not in retry[0] and "kmf.median_" not in retry[0], retry[:1])


# Q62: pandas prints at its defaults in Mentori's kernel; pd is still bound
async def _pandas_kernel():
    k = NotebookKernel(str(TMP / "q62.ipynb"), str(TMP))
    await k.start()
    try:
        opts = await v28._execute_and_collect(k, "print(pd.get_option('display.max_rows'), "
                                                 "pd.get_option('display.width'))", stage="extraction")
        frame = await v28._execute_and_collect(k, "import pandas\nprint(pandas.DataFrame({'a': range(40)}))",
                                               stage="extraction")
        return opts["stdout"].split(), frame["stdout"]
    finally:
        await k.stop()


opts62, frame62 = asyncio.run(_pandas_kernel())
check("Q62 pandas defaults in the kernel (max_rows 60, width 80), pd bound", opts62 == ["60", "80"], opts62)
check("Q62 a 40-row table prints whole", "..." not in frame62 and len(frame62.strip().splitlines()) == 41,
      frame62[:200])
check("Q62 no display settings left in kernel.py", "display.max_rows" not in (
      M / "backend/agents/notebook/kernel.py").read_text())

# Q63: offline kernel environment, empty uv cache, no VIRTUAL_ENV; package fingerprint before and after
oe = kernel_mod.offline_env({"VIRTUAL_ENV": "/v", "PATH": "/bin", "UV_OFFLINE": "0"}, "/empty")
check("Q63 offline_env", oe == {"PATH": "/bin", "UV_OFFLINE": "1", "UV_CACHE_DIR": "/empty", "PIP_NO_INDEX": "1"}, oe)
UVB = isc.uv_binary()
ENV_PROBE = ("import os, json\nprint(json.dumps({k: os.environ.get(k) for k in ('UV_OFFLINE', 'UV_CACHE_DIR', "
             "'PIP_NO_INDEX', 'VIRTUAL_ENV')}))\nprint(os.listdir(os.environ['UV_CACHE_DIR']) "
             "if os.environ.get('UV_CACHE_DIR') else None)")
INSTALL_TRY = ("import subprocess, sys\np = subprocess.run([%r, 'pip', 'install', '--dry-run', '--python', "
               "sys.executable, 'gseapy'], capture_output=True, text=True)\nprint(p.returncode)\n"
               "print('not found in the cache' in (p.stderr + p.stdout))" % UVB)


async def _offline_kernel():
    token = kernel_mod.OFFLINE.set(True)
    try:
        k = NotebookKernel(str(TMP / "q63.ipynb"), str(TMP))
        await k.start()
    finally:
        kernel_mod.OFFLINE.reset(token)
    try:
        env = await v28._execute_and_collect(k, ENV_PROBE, stage="extraction")
        inst = await v28._execute_and_collect(k, INSTALL_TRY, stage="extraction")
        cache = k._empty_cache
    finally:
        await k.stop()
    k2 = NotebookKernel(str(TMP / "q63b.ipynb"), str(TMP))
    await k2.start()
    try:
        env2 = await v28._execute_and_collect(k2, ENV_PROBE.split("\nprint(os.listdir")[0], stage="extraction")
    finally:
        await k2.stop()
    return env["stdout"].splitlines(), inst["stdout"].split(), cache, env2["stdout"], k.offline, k2.offline


env63, inst63, cache63, env63b, off1, off2 = asyncio.run(_offline_kernel())
e63 = json.loads(env63[0]) if env63 else {}
check("Q63 offline kernel: UV_OFFLINE, empty uv cache, PIP_NO_INDEX, no VIRTUAL_ENV",
      e63.get("UV_OFFLINE") == "1" and e63.get("PIP_NO_INDEX") == "1" and e63.get("VIRTUAL_ENV") is None
      and e63.get("UV_CACHE_DIR") == cache63 and env63[1] == "[]" and off1, env63)
check("Q63 offline kernel: an install of a package not present fails offline", inst63[:1] != ["0"]
      and inst63[1:] == ["True"] and isc.probe_subprocess(["gseapy"], sys.executable) == {"gseapy": "missing"},
      inst63)
check("Q63 the empty cache is removed at stop", cache63 and not Path(cache63).exists(), cache63)
check("Q63 outside the benchmark a kernel starts as before", not off2 and '"UV_OFFLINE": null' in env63b, env63b)
fp = isc.fingerprint(sys.executable)
check("Q63 fingerprint of the real environment", "pandas==2.3.3" in fp and fp == sorted(fp), fp[:3])
check("Q63 an unchanged fingerprint passes", isc.check_unchanged(fp, list(fp)) is None)
e = raises(isc.EnvironmentChanged, lambda: isc.check_unchanged(["a==1"], ["a==1", "gseapy==1.1"], "x"))
check("Q63 a changed fingerprint is EnvironmentChanged, naming the change", e and "gseapy==1.1" in str(e), e)
e = raises(isc.EnvironmentCheckError, lambda: isc.fingerprint("/py", run=lambda cmd, **kw: Proc(2, "", "no")))
check("Q63 a failed freeze is a setup error", e is not None, e)
_real_fp, _fp_calls = isc.fingerprint, []


def _drifting_fp(python, run=None):
    _fp_calls.append(python)
    return ["a==1"] + (["gseapy==1.1"] if len(_fp_calls) % 2 == 0 else [])


isc.fingerprint = _drifting_fp
script["free_form"] = PASS_CODE + "```\n"
e = raises(isc.EnvironmentChanged, lambda: mod.run_variant(dict(v, extra="qwen3-coder-30b+q63"), ["free_form"], ops,
                                                           "http://127.0.0.1:9"))
isc.fingerprint = _real_fp
ans63 = TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+q63" / "answers.json"
check("Q63 exp_05: a changed environment stops the run, no attempt stored", e is not None
      and _fp_calls == [sys.executable, sys.executable]
      and (not ans63.exists() or json.loads(ans63.read_text())["results"] == []), (e, _fp_calls))
check("Q63 the attempt's kernels start offline", "OFFLINE.set(True)" in inspect.getsource(v28._dispatch)
      and isc.EnvironmentCheckError in v28.SETUP_ERRORS)
fp_sha = isc.fingerprint_sha256(isc.fingerprint(sys.executable))
check("Q63 fingerprint_sha256 is the sha256 of the sorted lines", isc.fingerprint_sha256(["b==2", "a==1"])
      == __import__("hashlib").sha256(b"a==1\nb==2").hexdigest() and len(fp_sha) == 64)

# Q63 through coder_v2's own path: every Jupyter kernel started during an exp_05 attempt (KernelRegistry.get_kernel
# inside coder_loop_v2, and the re-run) gets the offline environment; the attempt records its fingerprint
_real_start_kernel = kernel_mod.KernelManager.start_kernel
_real_get_kernel_attr = kernel_mod.KernelRegistry.__dict__["get_kernel"]   # the classmethod itself, restored below
_real_get_kernel = kernel_mod.KernelRegistry.get_kernel
started63, registry63 = [], []


def _recording_start_kernel(self, *a, **kw):
    started63.append(kw.get("env"))
    return _real_start_kernel(self, *a, **kw)


async def _recording_get_kernel(notebook_path, working_dir, kernel_name="python3"):
    k = await _real_get_kernel(notebook_path, working_dir, kernel_name)
    registry63.append((k.offline, k._empty_cache))
    return k


kernel_mod.KernelManager.start_kernel = _recording_start_kernel
kernel_mod.KernelRegistry.get_kernel = staticmethod(_recording_get_kernel)
try:
    asyncio.run(mod.run_variant(dict(v, extra="qwen3-coder-30b+q63reg"), ["coder_v2_n1"], ops, "http://127.0.0.1:9"))
finally:
    kernel_mod.KernelManager.start_kernel = _real_start_kernel
    kernel_mod.KernelRegistry.get_kernel = _real_get_kernel_attr
r63 = json.loads((TMP / "runs" / "exp_05__coder_v2_n1__qwen3-coder-30b+q63reg" / "answers.json")
                 .read_text())["results"][0]
check("Q63 coder_v2 through _dispatch: its registry kernels and every kernel of the attempt start offline",
      r63["passed"] and registry63 and all(off and cache for off, cache in registry63) and started63
      and all(e is not None and e.get("UV_OFFLINE") == "1" and e.get("PIP_NO_INDEX") == "1"
              and "VIRTUAL_ENV" not in e for e in started63),
      (r63.get("exec_outcome"), registry63, [None if e is None else e.get("UV_OFFLINE") for e in started63]))
check("Q63 the attempt records its fingerprint before and after", r63["packages_sha256_before"] == fp_sha
      and r63["packages_sha256_after"] == fp_sha, (r63.get("packages_sha256_before"), fp_sha))

# D78 Q112: the fingerprint reads the interpreter the kernel reports about itself; another one stops the run
check("Q112 the kernel reporting the harness's interpreter passes", isc.check_kernel_python("/py", "/py") is None)
e = raises(isc.KernelInterpreterMismatch, lambda: isc.check_kernel_python("/other/python3", "/py", "x"))
check("Q112 another interpreter is KernelInterpreterMismatch (a setup error), naming both",
      e and "/other/python3" in str(e) and "/py" in str(e) and isc.EnvironmentCheckError in type(e).__mro__, e)
check("Q112 a kernel that reported nothing is refused", raises(isc.KernelInterpreterMismatch,
      lambda: isc.check_kernel_python(None, "/py")) is not None)
check("Q112 scans with the interpreter or with no probe answer pass",
      isc.check_scans_python([{"python": "/py"}, {"python": None}, {}], "/py") is None)
e = raises(isc.KernelInterpreterMismatch, lambda: isc.check_scans_python(
    [{"python": "/py"}, {"python": "/b"}, {"python": "/a"}, {"python": "/b"}], "/py"))
check("Q112 a scan on another interpreter is refused, naming each", e and "['/a', '/b']" in str(e), e)
started112 = []


def _recording_start_kernel112(self, *a, **kw):
    started112.append(kw.get("env"))
    return _real_start_kernel(self, *a, **kw)


kernel_mod.KernelManager.start_kernel = _recording_start_kernel112
v28._KERNEL_PYTHON = None
try:
    kp112 = asyncio.run(v28.check_kernel_python())
finally:
    kernel_mod.KernelManager.start_kernel = _real_start_kernel
check("Q112 a real kernel, started offline as an attempt's, reports the harness's interpreter, which is kept",
      kp112 == sys.executable and v28._KERNEL_PYTHON == sys.executable and len(started112) == 1
      and started112[0] is not None and started112[0].get("UV_OFFLINE") == "1", (kp112, started112))
check("Q112 the fingerprint reads the kernel's interpreter", "import_scan.fingerprint(python)" in
      inspect.getsource(v28._dispatch) and "fingerprint(sys.executable)" not in inspect.getsource(v28._dispatch))
_real_probe = kernel_mod.NotebookKernel._probe_imports


async def _other_probe(self, modules):
    return {"executable": "/other/python3", "modules": {m: "stdlib" for m in modules}}


_fp_calls.clear()
isc.fingerprint = _drifting_fp
kernel_mod.NotebookKernel._probe_imports = _other_probe
try:
    e = raises(isc.KernelInterpreterMismatch, lambda: mod.run_variant(dict(v, extra="qwen3-coder-30b+q112"),
                                                                      ["free_form"], ops, "http://127.0.0.1:9"))
finally:
    kernel_mod.NotebookKernel._probe_imports = _real_probe
    isc.fingerprint = _real_fp
ans112 = TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+q112" / "answers.json"
check("Q112 exp_05: a kernel on another interpreter stops the variant at its start, no attempt, no fingerprint",
      e is not None and "/other/python3" in str(e) and _fp_calls == [] and v28._KERNEL_PYTHON is None
      and not ans112.exists(), (e, _fp_calls))
_real_check_kp = v28.check_kernel_python


async def _harness_kp():
    v28._KERNEL_PYTHON = sys.executable
    return sys.executable


v28.check_kernel_python = _harness_kp
kernel_mod.NotebookKernel._probe_imports = _other_probe
script["free_form"] = "import os\n" + PASS_CODE + "```\n"
try:
    e = raises(isc.KernelInterpreterMismatch, lambda: mod.run_variant(dict(v, extra="qwen3-coder-30b+q112scan"),
                                                                      ["free_form"], ops, "http://127.0.0.1:9"))
finally:
    kernel_mod.NotebookKernel._probe_imports = _real_probe
    v28.check_kernel_python = _real_check_kp
    script["free_form"] = PASS_CODE + "```\n"
ans112s = TMP / "runs" / "exp_05__free_form__qwen3-coder-30b+q112scan" / "answers.json"
check("Q112 exp_05: an attempt whose kernel reports another interpreter stops the run, no attempt stored",
      e is not None and "/other/python3" in str(e)
      and (not ans112s.exists() or json.loads(ans112s.read_text())["results"] == []), e)

# Q64: a NameError for a name the failed not_allowed import would have bound counts toward the flag
IB = ("import gseapy as gp\nimport a.b\nfrom pingouin import anova, ttest as tt\nfrom x import *\n"
      "try:\n    import y\nexcept ImportError:\n    pass\n")
check("Q64 import bindings (a star import binds nothing known)", isc.import_bindings(IB)
      == {"a": ["a"], "gseapy": ["gp"], "pingouin": ["anova", "tt"], "y": ["y"]}, isc.import_bindings(IB))
check("Q64 import bindings, regex fallback", isc.import_bindings("!pip list\nimport gseapy as gp\n"
      "from pingouin import (anova, ttest as tt)\n") == {"gseapy": ["gp"], "pingouin": ["anova", "tt"]},
      isc.import_bindings("!pip list\nimport gseapy as gp\nfrom pingouin import (anova, ttest as tt)\n"))
gp_fail = {"kernel_run": 7, "modules": ["gseapy"], "classification": {"gseapy": {"status": "not_allowed"}},
           "error": {"ename": "ModuleNotFoundError", "evalue": "No module named 'gseapy'"},
           "error_not_allowed_module": "gseapy", "import_bindings": {"gseapy": ["gp"]}}


def err(ename, evalue, run=7):
    return {"kernel_run": run, "modules": [], "classification": {}, "error": {"ename": ename, "evalue": evalue},
            "error_not_allowed_module": None, "import_bindings": {}}


ok_cell = dict(clean, kernel_run=7)
check("Q64 NameError for the failed import's name counts", flag([gp_fail, ok_cell,
      err("NameError", "name 'gp' is not defined")], outcome="error") is True)
check("Q64 NameError for another name does not", flag([gp_fail, err("NameError", "name 'df2' is not defined")])
      is False)
check("Q64 any other error does not", flag([gp_fail, err("NameError", "name 'gp' is not defined"),
      err("KeyError", "'log2FC'")]) is False)
check("Q64 a NameError before the failed import does not", flag([err("NameError", "name 'gp' is not defined"),
      gp_fail]) is False)
check("Q64 a NameError alone is not flagged", flag([err("NameError", "name 'gp' is not defined")]) is False)
old_rec = {k: v for k, v in gp_fail.items() if k != "import_bindings"}   # stored before D75
check("Q64 recomputed from stored code_cells for records without import_bindings",
      isc.attempt_fields([old_rec, err("NameError", "name 'gp' is not defined")], passed=False,
                         exec_outcome="step_failed", codes=["import gseapy as gp\n", "gp.enrichr()\n"])[
          "missing_library_not_allowed"] is True
      and isc.attempt_fields([old_rec, err("NameError", "name 'gp' is not defined")], passed=False,
                             exec_outcome="step_failed")["missing_library_not_allowed"] is False)
check("Q64 the kernel records import_bindings", '"import_bindings": import_scan.import_bindings(code)' in (
      M / "backend/agents/notebook/kernel.py").read_text())


# Q101: a step_failed with no error text is written with the step's last evaluation
async def _fake_loop(**kw):
    yield {"type": "cell_evaluation", "step_number": 1, "cell_id": "c1", "score": 30, "status": "ok",
           "meets_expectations": False, "should_retry": True, "feedback": "the table has no log2FC column",
           "issues": []}
    yield {"type": "step_retry", "step_number": 1}
    yield {"type": "step_failed", "step_number": 1, "error": None}
    yield {"type": "step_failed", "step_number": 2, "error": None}
    yield {"type": "step_failed", "step_number": 3, "error": "KeyError: 'x'"}


from backend.agents.notebook import coder_v2 as coder_v2_mod  # noqa: E402

_real_loop, _real_eval = coder_v2_mod.coder_loop_v2, v28._evaluate_failed_result
coder_v2_mod.coder_loop_v2 = _fake_loop


judged101 = []


async def _no_judge(op, actual, error, router):
    judged101.append(error)
    return "FAIL", ""


v28._evaluate_failed_result = _no_judge
ws101 = TMP / "q101"
ws101.mkdir()
r101 = asyncio.run(v28._run_coder_v2(ops[0], None, "u", ws101, n_candidates=1, gen_model="ollama::m"))
coder_v2_mod.coder_loop_v2, v28._evaluate_failed_result = _real_loop, _real_eval
check("Q101 the reason replaces None, the outcome unchanged", "None" not in r101["exec_error"]
      and r101["exec_outcome"] == "step_failed" and r101["exec_error"] == (
          "Step failed: step 1: no cell created after its last evaluation (status ok, feedback: the table "
          "has no log2FC column) | Step failed: step 2: no cell created, no error text, no evaluation of this step"
          " | Step failed: KeyError: 'x'"), r101["exec_error"])
check("Q101 the soft-pass judge reads the text it read before (only the record changes)", judged101 == [
      "Step failed: None | Step failed: None | Step failed: KeyError: 'x'"], judged101)

# D75 counts beside the pass rates (Q56-Q59)
oc = mod.outcome_counts([
    {"exec_outcome": "ok", "generations": [{"fence_case": "first_block", "first_fence_tag": "py"},
                                           {"stage": "pick", "raw_reply": "2"}], "pick": "unparsed"},
    {"exec_outcome": "length", "generations": [{"fence_case": "unclosed_block", "first_fence_tag": "python"}],
     "pick": 2},
    {"exec_outcome": "step_failed", "cell_candidates": [{"strategy": "best_of_3", "pick": "unparsed"},
                                                        {"strategy": "combined", "pick": None}],
     "cell_evaluations": [{"status": "unparsed"}, {"status": "ok"}, {"status": "error"}]}])
check("D75 report counts", oc == {"exec_outcome": {"length": 1, "ok": 1, "step_failed": 1},
      "first_fence_tag": {"py": 1, "python": 1}, "fence_case": {"first_block": 1, "unclosed_block": 1},
      "pick": {"2": 1, "unparsed": 1}, "cell_pick": {"unparsed": 1},
      "cell_evaluation_status": {"error": 1, "ok": 1, "unparsed": 1}}, oc)
rep2 = json.loads(sorted((TMP / "results_v4").glob("*_latest.json"))[-1].read_text())
check("D75 the report carries the counts per config", all("counts" in s for s in rep2["summary"].values()),
      list(rep2["summary"]))

# ── 13. D80 V1: transient retries and calls written as text ───────────────────
# The stored shapes, trimmed, from exp_05__coder_v2_n1__gpt-oss-20b+high (S4 copy; COUNTERCHECKS A5 F35)
SRC = "import pandas as pd"
ADD = ('{\n  "name": "functions.add_cell",\n  "arguments": {\n    "cell_type": "code",\n    "source": "' + SRC
       + '"\n  }\n}')
EXE = '{\n  "name": "functions.execute_cell",\n  "arguments": {\n    "cell_id": "${cell_id}"\n  }\n}'
read_ok = {
    "bare, functions. prefix (seq 15 lung_2)": ADD,
    "bare, add_cell then execute_cell (seq 4 airway_1)": ADD + "\n" + EXE,
    "one line each, no prefix (seq 6 lung_5)": '{"name":"add_cell","arguments":{"cell_type":"code","source":"' + SRC
                                              + '"}}\n{"name":"execute_cell","arguments":{"cell_id":"$cell_id"}}',
    "```json fence (seq 18 airway_4)": "```json\n" + ADD + "\n```",
    "two ```json fences (seq 4 lung_4)": "```json\n" + ADD + "\n```\n```json\n" + EXE + "\n```",
    "two objects in one fence (seq 4 lung_5)": "```json\n" + ADD + "\n" + EXE + "\n```\n",
    "source holding ``` and braces": '{"name": "add_cell", "arguments": {"source": "s = \\"```{x}```\\""}}',
    # D81 Q137: the Python-call form
    "Python keywords, assigned, then execute_cell (seq 11 airway_5)":
        '```python\ncell_id = functions.add_cell(\n    cell_type="code",\n    source="""' + SRC
        + '"""\n)\nfunctions.execute_cell(cell_id=cell_id)\n```',
    "Python keywords, a comment, execute_cell on a subscript (seq 4 airway_10)":
        "```python\n# Add a new cell that loads the data, then execute it\nadded_cell = functions.add_cell(\n    "
        "cell_type='code',\n    source=\"\"\"" + SRC + "\"\"\"\n)\nfunctions.execute_cell(cell_id=added_cell['cell_id'])\n```\n",
    "Python one dict literal (seq 6 lung_6)": '```python\nnew_cell_id = functions.add_cell({\n    "cell_type": "code",\n'
        '    "source": \'\'\'' + SRC + '\'\'\'\n})\nfunctions.execute_cell({"cell_id": new_cell_id})\n```\n',
    "Python bare, no prefix, implicit concatenation": 'add_cell(source="import pandas "\n         "as pd")',
    # D81 Q137: the header form
    "assistant to= header (seq 4 airway_8)": 'assistant to=functions.add_cell\n{\n  "cell_type": "code",\n  "source": "'
        + SRC + '"\n}\nassistant to=functions.execute_cell\n{\n  "cell_id": "0"\n}',
    "commentary to= header with ':' (seq 6 airway_8)": 'commentary to=functions.add_cell:\n{\n  "cell_type": "code",\n  '
        '"source": "' + SRC + '"\n}\ncommentary to=functions.execute_cell:\n{\n  "cell_id": "0"\n}',
    "commentary to= header, object on the same line (seq 13 airway_9)": 'commentary to=functions.add_cell {\n  '
        '"cell_type": "code",\n  "source": "' + SRC + '"\n}\ncommentary to=functions.execute_cell {\n  "cell_id": '
        '"$cell_id"\n}',
}
PY_GLUE = ('```python\nresult = functions.add_cell({\n    "cell_type": "code",\n    "source": "' + SRC + '"\n})\n'
           'cell_id = result["cell_id"]\nfunctions.execute_cell({"cell_id": cell_id})\n```')
# D83 Q154: the four stored gpt-oss high replies D81 refused for their keeping line (replies 10, 19, 26, 32 of the 32
# stored text-call replies, 1-based; the build report's #9, #18, #25, #31), trimmed: the call assigned to a name, then
# one line keeping cell_id from it, then execute_cell
read_ok["Python with a keeping line, dict literal (seq 4 lung_1)"] = PY_GLUE
read_ok["Python with a keeping line, triple quotes, a blank line (reply 32)"] = (
    '```python\ncell_result = functions.add_cell({\n    "cell_type": "code",\n    "source": """' + SRC + '"""\n})\n\n'
    'cell_id = cell_result["cell_id"]\nfunctions.execute_cell({"cell_id": cell_id})\n```\n')
read_ok["Python with a keeping line in single quotes (reply 26)"] = (
    "```python\nresult = functions.add_cell({\n    'cell_type': 'code',\n    'source': '''" + SRC + "'''\n})\n"
    "cell_id = result['cell_id']\nfunctions.execute_cell({\"cell_id\": cell_id})\n```")
read_ok["Python with a keeping line, no execute_cell"] = ('cell_obj = functions.add_cell(cell_type="code", source="'
                                                         + SRC + '")\ncell_id = cell_obj["cell_id"]')
read_ok["Python with a line keeping the whole result"] = ('r = functions.add_cell(cell_type="code", source="' + SRC
                                                          + '")\nkept = r\nfunctions.execute_cell(cell_id=kept)')
not_read = {
    # D83 Q154: a line that does more than keep add_cell's result, or keeps something else, is still refused
    "Python: a keeping line before add_cell": ('cell_id = result["cell_id"]\nresult = functions.add_cell(source="'
                                               + SRC + '")'),
    "Python: a keeping line from another name": ('result = functions.add_cell(source="' + SRC + '")\n'
                                                 'cell_id = other["cell_id"]'),
    "Python: a keeping line of another bare name": ('result = functions.add_cell(source="' + SRC + '")\n'
                                                    'kept = other'),
    # review of 17 Oct F2: the result's name, once rebound, no longer holds add_cell's result
    "Python: the result's name rebound to execute_cell's": ('r = functions.add_cell(source="' + SRC + '")\n'
                                                            'r = functions.execute_cell(cell_id="0")\nx = r["out"]'),
    "Python: the result's name rebound by a keeping line": ('r = functions.add_cell(source="' + SRC + '")\n'
                                                            'r = r["cell_id"]\nx = r["y"]'),
    "Python: a keeping line from execute_cell's result": ('r = functions.add_cell(source="' + SRC + '")\n'
                                                          'out = functions.execute_cell(cell_id="0")\nx = out["x"]'),
    "Python: an attribute of the result": 'result = functions.add_cell(source="' + SRC + '")\ncell_id = result.cell_id',
    "Python: a call in the keeping line": ('result = functions.add_cell(source="' + SRC + '")\n'
                                           'cell_id = str(result["cell_id"])'),
    "Python: a subscript by a name": 'result = functions.add_cell(source="' + SRC + '")\ncell_id = result[key]',
    "Python: a subscript of a subscript": ('result = functions.add_cell(source="' + SRC + '")\n'
                                           'cell_id = result["cell"]["id"]'),
    "Python: a keeping line with add_cell not assigned": ('functions.add_cell(source="' + SRC + '")\n'
                                                          'cell_id = result["cell_id"]'),
    "Python: a constant assigned": 'result = functions.add_cell(source="' + SRC + '")\ncell_id = "0"',
    "Python: a keeping line, prose after": (PY_GLUE + "\n\nThis adds the cell and runs it."),
    "Python: a tuple target keeping the result": ('result = functions.add_cell(source="' + SRC + '")\n'
                                                  'a, b = result["cell_id"], 1'),
    "Python: an augmented assignment": 'result = functions.add_cell(source="' + SRC + '")\nresult += "x"',
    # review of D83 wave B (S2): a walrus rebinds a name inside another call's arguments, unseen statement by statement
    "Python: a walrus rebinding the result's name in execute_cell's arguments":
        'r = functions.add_cell(source="' + SRC + '")\nfunctions.execute_cell(cell_id=(r := "0"))\nx = r["cell_id"]',
    "Python: a walrus binding another name": ('r = functions.add_cell(source="' + SRC + '")\n'
                                             'functions.execute_cell(cell_id=(c := "0"))'),
    "a **Step** line before a Python call (seq 11 airway_3)": '**Step 2 – Filter expressed genes**  \n\n```python\n'
        'cell = functions.add_cell(\n    cell_type="code",\n    source="' + SRC + '"\n)\n```',
    "prose before and after a Python call (seq 4 airway_6)": "Here is the code:\n\n```python\nfunctions.add_cell("
        "source='" + SRC + "')\n```\n\nAfter running this code, the variables are defined.",
    "assistant.functions.add_cell (seq 9 lung_3)": 'assistant.functions.add_cell({"cell_type":"code","source":"' + SRC
        + '"})\nassistant.functions.execute_cell({"cell_id":"<cell_id>"})',
    "header with the arguments in parentheses (seq 8 lung_1)": 'commentary to=functions.add_cell({"cell_type":"code",'
        '"source":"' + SRC + '"})\ncommentary to=functions.execute_cell({"cell_id":"1"})',
    "a header inside bare fences, prose around (seq 4 lung_8)": '**Add a new code cell**\n\n```\ncommentary '
        'to=functions.add_cell\n{"cell_type": "code", "source": "' + SRC + '"}\n```\n',
    # D81 Q137: the other refusals of the two new forms
    "Python: another function name": 'functions.run_code(source="x = 1")',
    "Python: print beside the call": 'functions.add_cell(source="x = 1")\nprint("done")',
    "Python: a call nested in add_cell's arguments": 'functions.add_cell(source=open("a.py").read())',
    "Python: a call nested in execute_cell's arguments": ('functions.add_cell(source="x = 1")\n'
                                                           'functions.execute_cell(cell_id=os.system("ls"))'),
    "Python: an f-string source": 'functions.add_cell(source=f"x = {y}")',
    "Python: a name as the source": 'functions.add_cell(source=code)',
    "Python: **kwargs": 'functions.add_cell(**{"source": "x = 1"})',
    "Python: a positional string": 'functions.add_cell("x = 1")',
    "Python: a dict and a keyword": 'functions.add_cell({"source": "x = 1"}, cell_type="code")',
    "Python: a dict with a duplicate key": 'functions.add_cell({"source": "x = 1", "source": "y = 2"})',
    "Python: a dict with ** unpacking": 'functions.add_cell({**base, "source": "x = 1"})',
    "Python: two add_cell": 'functions.add_cell(source="a = 1")\nfunctions.add_cell(source="b = 2")',
    "Python: off the schema": 'functions.add_cell(source="x = 1", position=0)',
    "Python: a tuple target": 'a, b = functions.add_cell(source="x = 1")',
    "Python: a ```py fence holding the call": '```py\nfunctions.add_cell(source="x = 1")\n```',
    "Python: two fences": '```python\nfunctions.add_cell(source="x = 1")\n```\n```python\nfunctions.execute_cell('
        'cell_id="0")\n```',
    "header: another tool's name": 'commentary to=functions.run_code\n{"source": "x = 1"}',
    "header: no functions. prefix": 'commentary to=add_cell\n{"source": "x = 1"}',
    "header: analysis channel": 'analysis to=functions.add_cell\n{"source": "x = 1"}',
    "header: prose after the object": 'commentary to=functions.add_cell\n{"source": "x = 1"}\nThen run it.',
    "header: arguments not an object": 'commentary to=functions.add_cell\n["x = 1"]',
    "header and JSON mixed": 'commentary to=functions.add_cell\n{"source": "x = 1"}\n' + EXE,
    "{\"functions\": [...]} wrapper (seq 4 airway_4)": '{"functions": [' + ADD + ", " + EXE + "]}",
    "{\"commentary\": [...]} wrapper (seq 4 airway_7)": '{"commentary": [' + ADD + "]}",
    "prose after a fenced call (seq 8 airway_6)": "```json\n" + ADD + "\n```\n\nAfter the kernel responds, execute it.",
    "prose before the call (seq 25 airway_10)": "We need to invoke `add_cell` with the code.\n" + ADD,
    "```python fence holding the JSON": "```python\n" + ADD + "\n```",
    "fence never closed": "```json\n" + ADD,
    "two add_cell": ADD + "\n" + ADD,
    "execute_cell only": EXE,
    "argument not in the schema": '{"name": "add_cell", "arguments": {"source": "x = 1", "position": "0"}}',
    "no source": '{"name": "add_cell", "arguments": {"cell_type": "code"}}',
    "source not a string": '{"name": "add_cell", "arguments": {"source": ["x = 1"]}}',
    "cell_type off the enum": '{"name": "add_cell", "arguments": {"source": "x = 1", "cell_type": "raw"}}',
    "a key beside name and arguments": '{"name": "add_cell", "arguments": {"source": "x = 1"}, "id": "c1"}',
    "duplicate key": '{"name": "add_cell", "name": "add_cell", "arguments": {"source": "x = 1"}}',
    "another tool's name": '{"name": "functions.run_code", "arguments": {"source": "x = 1"}}',
    "a prefix other than functions.": '{"name": "foo.add_cell", "arguments": {"source": "x = 1"}}',
    "arguments as a JSON string": '{"name": "add_cell", "arguments": "{\\"source\\": \\"x = 1\\"}"}',
    "a JSON list": "[" + ADD + "]",
    "empty": "",
}
got_ok = {k: se.read_text_tool_call(t) for k, t in read_ok.items()}
check("D80 V1 the stored text-call shapes are read, as add_cell with their arguments",
      all(g is not None and len(g["calls"]) == 1 and g["calls"][0]["function"]["name"] == "add_cell"
          and set(g["calls"][0]["function"]["arguments"]) <= {"source", "cell_type"} for g in got_ok.values())
      and got_ok["bare, functions. prefix (seq 15 lung_2)"]["calls"][0]["function"]["arguments"]
      == {"cell_type": "code", "source": SRC}
      and got_ok["two ```json fences (seq 4 lung_4)"]["fenced"] is True
      and got_ok["bare, add_cell then execute_cell (seq 4 airway_1)"]["not_read"]
      == [{"name": "functions.execute_cell", "arguments": {"cell_id": "${cell_id}"}}],
      [k for k, g in got_ok.items() if g is None])
_py = {k: g for k, g in got_ok.items() if k.startswith("Python")}
_hd = {k: g for k, g in got_ok.items() if "header" in k}
check("D81 Q137 the Python-call form: the arguments read by literal_eval, the form, fence, names and comments "
      "recorded, the other call's source not evaluated",
      len(_py) == 9 and all(g and g["form"] == "python" for g in _py.values())
      and all(g["calls"][0]["function"]["arguments"] == {"cell_type": "code", "source": SRC}
              for k, g in _py.items() if "bare" not in k)
      and _py["Python bare, no prefix, implicit concatenation"]["calls"][0]["function"]["arguments"]
      == {"source": SRC} and _py["Python bare, no prefix, implicit concatenation"]["fenced"] is False
      and _py["Python keywords, assigned, then execute_cell (seq 11 airway_5)"]["fenced"] is True
      and _py["Python keywords, assigned, then execute_cell (seq 11 airway_5)"]["not_read"]
      == [{"name": "functions.execute_cell", "source": "functions.execute_cell(cell_id=cell_id)"}]
      and _py["Python keywords, a comment, execute_cell on a subscript (seq 4 airway_10)"]["comments"] == 1
      and _py["Python one dict literal (seq 6 lung_6)"]["names_written"]
      == ["functions.add_cell", "functions.execute_cell"],
      {k: (g or {}).get("form") for k, g in _py.items()})
check("D81 Q137 the header form: assistant and commentary headers, with or without ':', the object on the next line "
      "or the same one; the other call recorded as not read",
      len(_hd) == 3 and all(g and g["form"] == "header" and g["fenced"] is False
                            and g["calls"][0]["function"]["arguments"] == {"cell_type": "code", "source": SRC}
                            and g["names_written"] == ["functions.add_cell", "functions.execute_cell"]
                            and len(g["not_read"]) == 1 for g in _hd.values())
      and _hd["assistant to= header (seq 4 airway_8)"]["not_read"]
      == [{"name": "functions.execute_cell", "arguments": {"cell_id": "0"}}],
      {k: (g or {}).get("form") for k, g in _hd.items()})
_kp = {k: g for k, g in got_ok.items() if "keeping line" in k or "keeping the whole" in k}
check("D83 Q154 an add_cell whose result one line keeps (a name, or one subscript by a constant) is read; the keeping "
      "line is recorded as not read, name None, in the reply's order",
      len(_kp) == 5 and all(g and g["form"] == "python" and g["calls"][0]["function"]["name"] == "add_cell"
                            for g in _kp.values())
      and _kp["Python with a keeping line, dict literal (seq 4 lung_1)"]["not_read"]
      == [{"name": None, "source": 'cell_id = result["cell_id"]'},
          {"name": "functions.execute_cell", "source": 'functions.execute_cell({"cell_id": cell_id})'}]
      and _kp["Python with a keeping line, dict literal (seq 4 lung_1)"]["names_written"]
      == ["functions.add_cell", "functions.execute_cell"]
      and _kp["Python with a keeping line, no execute_cell"]["not_read"]
      == [{"name": None, "source": 'cell_id = cell_obj["cell_id"]'}]
      and _kp["Python with a line keeping the whole result"]["not_read"][0] == {"name": None, "source": "kept = r"},
      {k: (g or {}).get("not_read") for k, g in _kp.items()})
check("D81 Q137 the json form is recorded as form json", got_ok["```json fence (seq 18 airway_4)"]["form"] == "json")
got_no = {k: se.read_text_tool_call(t) for k, t in not_read.items()}
check("D80 V1 every other shape is not read", all(g is None for g in got_no.values()),
      [k for k, g in got_no.items() if g is not None])
check("S2 (review of D83 wave B): a reply holding an assignment expression is not read, one rebinding add_cell's "
      "result name inside execute_cell's arguments (then kept from) included; without the walrus the same reply is read",
      got_no["Python: a walrus rebinding the result's name in execute_cell's arguments"] is None
      and got_no["Python: a walrus binding another name"] is None
      and se.read_text_tool_call('r = functions.add_cell(source="' + SRC + '")\nfunctions.execute_cell(cell_id="0")'
                                 '\nx = r["cell_id"]') is not None)

# D81 Q136: a retried call needs [generation] retry_seed; the d80 steps run on a scratch lock that has it (LOCK.toml's
# bytes, the line added when it is not there yet), so they pass before and after the coordinator adds it
from experiments.runner.lock import LOCK, Lock  # noqa: E402

_lraw = LOCK.read_bytes()
RETRY_LOCK = Lock(_lraw if re.search(rb"(?m)^retry_seed = ", _lraw) else
                  re.sub(rb'(?m)^think = "off"', lambda m: b'retry_seed = "seed + 1000000 * retry"   # D81 (Q136)\n'
                         + m.group(0), _lraw, count=1), LOCK)
_saved_load = la.load
la.load = lambda: RETRY_LOCK

D80_MODEL = "qwen3-coder:30b"
STEP_OK = {"output_type": "stream", "name": "stdout", "text": "1"}


# D83 Q156: replies for the cell judge's pick (or combine) calls, taken in order before its default ("2", or "c = 9")
D80_PICK = []


def d80_chat(script, seen):
    """A transport for execute_step: the introspection answered, the pick "2" and the combine "c = 9" unless D80_PICK
    holds a scripted reply; each step or candidate call takes the next scripted reply ("error" text, "crash" text
    (D83 Q155: an error after the stream began, first_token_s set), "nofinal" (a stream with no final chunk),
    "stalled", "add" source, "execute", "tool" name (a call to a tool that adds no cell), "text" reply)."""
    def chat(base_url, call, messages, passages=None, tools=None, fmt=None):
        seen.append({"messages": json.loads(json.dumps(messages)), "candidate": call.candidate, "tools": bool(tools)})
        first = messages[0].get("content", "") if messages else ""
        if first.startswith("You are planning Python code"):
            return base(call, base_url, passages, "- pandas.read_csv(path) -> DataFrame", [])
        judge = "Respond with ONLY the number" in first or "Write the final synthesized code" in first
        if judge and not D80_PICK:
            return base(call, base_url, passages, "2" if "Respond with ONLY" in first else "c = 9", [])
        kind, val = D80_PICK.pop(0) if judge else script.pop(0)
        if kind == "error":
            return {**base(call, base_url, passages, "", []), "status": "error", "stop_reason": None, "error": val}
        if kind == "crash":
            return {**base(call, base_url, passages, "", []), "status": "error", "stop_reason": None, "error": val,
                    "first_token_s": 0.5}
        if kind == "nofinal":
            return {**base(call, base_url, passages, "", []), "status": "error", "stop_reason": None,
                    "error": "the stream ended without a final chunk", "first_token_s": 0.5}
        if kind == "stalled":
            return {**base(call, base_url, passages, "", []), "status": "stalled", "stop_reason": None,
                    "error": "no new token for 600 s"}
        if kind == "add":
            return base(call, base_url, passages, "", [{"function": {"name": "add_cell",
                                                                     "arguments": {"source": val}}}])
        if kind == "tool":
            return base(call, base_url, passages, "", [{"function": {"name": val, "arguments": {}}}])
        if kind == "execute":
            cid = messages[-1]["content"].split()[1]
            return base(call, base_url, passages, "", [{"function": {"name": "execute_cell",
                                                                     "arguments": {"cell_id": cid}}}])
        return base(call, base_url, passages, val, [])
    return chat


def d80_step(name, script, strategy="single"):
    """execute_step on the real router and adapter; returns (events, records, transport calls, notebook)."""
    seen, nb = [], FakeNotebook()
    la.ollama_client.chat = d80_chat(script, seen)
    sink = TMP / f"d80_{name}"
    ctx = rc.RunContext(run_id=f"check-codegen-d80-{name}", arm="check", item_id="Q1", draw=1, thinking=None,
                        base_url="http://127.0.0.1:9", sink=sink, allowed={D80_MODEL: "generator"})
    step = AlgorithmStep.from_dict({"step_number": 1, "description": "count", "expected_output": "print n"})

    async def go():
        return [ev async for ev in se.execute_step(
            step=step, notebook=nb, notebook_manager=FakeManager(), kernel=FakeKernel([STEP_OK]),
            model_router=ModelRouter(), model_identifier=f"ollama::{D80_MODEL}", previous_results=[],
            cell_strategy=strategy)]
    with rc.run(ctx):
        events = asyncio.run(go())
    recs = [json.loads(x) for x in (sink / "calls.jsonl").read_text().splitlines()]
    return events, recs, seen, nb


def result_of(events):
    return [e for e in events if e.get("type") == "_step_result"][-1]["result"]


def step_recs(recs):
    return [r for r in recs if " execute_step" in str(r.get("call_site"))]


def read_of(r, key=None):
    """The record's tool_calls_from_text (or one key of it); "absent" when the record has no such key."""
    v = r.get("tool_calls_from_text", "absent")
    return v if key is None else (v.get(key) if isinstance(v, dict) else "absent")


PE = "error parsing tool call: raw='{\"cell_type\":\"code\",\"source\":\"# Step 6: ...', err=invalid character"
ev, recs, seen, nb = d80_step("retry", [("error", PE), ("stalled", None), ("add", "n = 1\nprint(n)"),
                                        ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
check("D80 V1 a tool-call parse error and a stall are retried and the step passes",
      res.success and [r["status"] for r in srs] == ["error", "stalled", "ok", "ok", "ok"]
      and [c["source"] for c in nb.cells] == ["n = 1\nprint(n)"], [r["status"] for r in srs])
pad = srs + [{}] * 5
want_tr = ([None] + [{"attempt": k, "of": se.MAX_TRANSIENT_RETRIES, "reason": why, "failed_seq": pad[k - 1].get("seq"),
                      "failed_ctx_uid": pad[k - 1].get("ctx_uid"), "failed_call_site": pad[k - 1].get("call_site")}
                     for k, why in ((1, "tool-call parse error"), (2, "stalled"))] + [None, None])
check("D80 V1 each retry's record names the failed call and the reason; no other record has transient_retry",
      [r.get("transient_retry") for r in srs] == want_tr
      and sum("transient_retry" in r for r in recs) == 2, [r.get("transient_retry") for r in srs])
check("D80 V1 a retry resends the same messages (the step's turn unchanged)",
      [s["messages"] for s in seen if s["tools"]][:3] == [[s["messages"] for s in seen if s["tools"]][0]] * 3)
check("D81 Q136 each retry sends seed + 1,000,000 * r and records retry and seed_sent; the other calls send the "
      "draw, 1, and carry neither",
      [r["options_sent"]["seed"] for r in srs] == [1, 1000001, 2000001, 1, 1]
      and [(r.get("retry"), r.get("seed_sent")) for r in srs]
      == [(None, None), (1, 1000001), (2, 2000001), (None, None), (None, None)]
      and sum("retry" in r for r in recs) == 2, [(r["options_sent"]["seed"], r.get("retry")) for r in srs])

# D81 Q138: an HTTP 500 and a dropped connection are retried like a parse error
ev, recs, seen, nb = d80_step("q138", [("error", "HTTP 500: llama runner process has terminated: exit status 2"),
                                       ("error", "RemoteDisconnected: Remote end closed connection without response"),
                                       ("error", "ConnectionResetError: [Errno 54] Connection reset by peer"),
                                       ("add", "n = 3\nprint(n)"), ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
check("D81 Q138 an HTTP 500 and two dropped connections are retried, each recorded with its reason and seed, and "
      "the step passes",
      res.success and [c["source"] for c in nb.cells] == ["n = 3\nprint(n)"]
      and [(r.get("transient_retry") or {}).get("reason") for r in srs]
      == [None, "HTTP 500", "dropped connection", "dropped connection", None, None]
      and [(r.get("transient_retry") or {}).get("failed_seq") for r in srs][1:4] == [r["seq"] for r in srs[:3]]
      and [r["options_sent"]["seed"] for r in srs] == [1, 1000001, 2000001, 3000001, 1, 1],
      [(r["status"], (r.get("transient_retry") or {}).get("reason"), r["options_sent"]["seed"]) for r in srs])

# D83 Q155: a crash after the answer began and a stream with no final chunk are retried like a parse error
CRASH = ("model runner has unexpectedly stopped, this may be due to resource limitations or an internal error, check "
         "ollama server logs for details")
ev, recs, seen, nb = d80_step("q155", [("crash", CRASH), ("nofinal", None), ("add", "n = 5\nprint(n)"),
                                       ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
check("D83 Q155 a mid-answer crash and a stream with no final chunk are retried, each recorded with its reason, retry "
      "number and seed, and the step passes",
      res.success and [c["source"] for c in nb.cells] == ["n = 5\nprint(n)"]
      and [(r.get("transient_retry") or {}).get("reason") for r in srs]
      == [None, "error inside the stream", "no final chunk", None, None]
      and [(r.get("transient_retry") or {}).get("failed_seq") for r in srs][1:3] == [r["seq"] for r in srs[:2]]
      and [r["options_sent"]["seed"] for r in srs] == [1, 1000001, 2000001, 1, 1]
      and [(r.get("retry"), r.get("seed_sent")) for r in srs]
      == [(None, None), (1, 1000001), (2, 2000001), (None, None), (None, None)],
      [(r["status"], (r.get("transient_retry") or {}).get("reason"), r["options_sent"]["seed"]) for r in srs])
ev, recs, seen, nb = d80_step("q155_exhausted", [("crash", CRASH)] * 4 + [("text", "unused")])
srs = step_recs(recs)
res = result_of(ev)
check("D83 Q155 a crash on every try fails the step after 3 retries, 4 calls made, the error kept",
      not res.success and len(srs) == 4 and CRASH in (res.error_message or "")
      and [r.get("retry") for r in srs] == [None, 1, 2, 3]
      and [r["options_sent"]["seed"] for r in srs] == [1, 1000001, 2000001, 3000001], res.error_message)


def round_recs(recs):
    """Every record but the introspection's: the step's own calls, the candidates and the pick, in order."""
    return [r for r in recs if "introspect" not in str(r.get("call_site"))]


# D83 Q156: the pick call of a best-of-3 round crashes; the round is redone whole under retry 1
D80_PICK[:] = [("crash", CRASH)]
ev, recs, seen, nb = d80_step("q156", [("add", "a = 1"), ("add", "a = 2"), ("add", "a = 3"),
                                       ("add", "b = 1"), ("add", "b = 2"), ("add", "b = 3"),
                                       ("execute", None), ("text", "Done.")], "best_of_3")
rr = round_recs(recs)
res = result_of(ev)
cands = [e for e in ev if e.get("type") == "cell_candidates"]
check("D83 Q156 a redone best-of-3 round sends every call under the retry seed: the turn d + 1,000,000 r, candidate k "
      "d * 1000 + k + 1,000,000 r, the pick d + 1,000,000 r; the first round and the later turns send their own seeds",
      res.success and [c["source"] for c in nb.cells] == ["b = 2"] and not D80_PICK
      and [r["options_sent"]["seed"] for r in rr] == [1, 1002, 1003, 1, 1000001, 1001002, 1001003, 1000001, 1, 1]
      and [r.get("candidate") for r in rr] == [None, 2, 3, None, None, 2, 3, None, None, None],
      [(r["options_sent"]["seed"], r.get("candidate"), r["status"]) for r in rr])
check("D83 Q156 each call of the redone round records retry 1, the seed sent and the pick's crash as the reason",
      [(r.get("retry"), r.get("seed_sent")) for r in rr]
      == [(None, None)] * 4 + [(1, 1000001), (1, 1001002), (1, 1001003), (1, 1000001)] + [(None, None)] * 2
      and all((r.get("transient_retry") or {}).get("reason") == "error inside the stream"
              and (r.get("transient_retry") or {}).get("failed_seq") == rr[3]["seq"]
              and "_judge_cell_candidates" in str((r.get("transient_retry") or {}).get("failed_call_site"))
              for r in rr[4:8])
      and sum("transient_retry" in r for r in recs) == 4,
      [(r.get("retry"), r.get("seed_sent"), (r.get("transient_retry") or {}).get("failed_call_site")) for r in rr])
check("D83 Q156 the answer's record holds the redone round only (the crashed round yielded nothing)",
      len(cands) == 1 and cands[0]["candidates"] == ["b = 1", "b = 2", "b = 3"] and cands[0]["pick"] == 2,
      cands)

# The combined strategy is outside Q156 (it names best-of-3): its redone round's candidates and combine call keep
# their first-try seeds; only the turn's own call takes the retry seed
D80_PICK[:] = [("crash", CRASH)]
ev, recs, seen, nb = d80_step("q156_combined", [("add", "a = 1"), ("add", "a = 2"), ("add", "a = 3"),
                                                ("add", "b = 1"), ("add", "b = 2"), ("add", "b = 3"),
                                                ("execute", None), ("text", "Done.")], "combined")
rr = round_recs(recs)
res = result_of(ev)
check("D83 Q156 limit: a redone combined round retries only the turn's own call (candidates and combine resend their "
      "first-try seeds), as before Q156",
      res.success and [c["source"] for c in nb.cells] == ["c = 9"] and not D80_PICK
      and [r["options_sent"]["seed"] for r in rr] == [1, 1002, 1003, 1, 1000001, 1002, 1003, 1, 1, 1]
      and [r.get("retry") for r in rr] == [None] * 4 + [1] + [None] * 5,
      [(r["options_sent"]["seed"], r.get("candidate"), r.get("retry")) for r in rr])
D80_PICK.clear()

# Review of 17 Oct F4: turn 1 crashes and its retry calls a tool that adds no cell; the best-of-3 round of turn 2 is
# a first try, so its candidates and pick send their first-try seeds (a retry does not carry over to a later turn)
ev, recs, seen, nb = d80_step("q156_later_turn", [("crash", CRASH), ("tool", "list_cells"), ("add", "a = 1"),
                                                  ("add", "a = 2"), ("add", "a = 3"), ("execute", None),
                                                  ("text", "Done.")], "best_of_3")
rr = round_recs(recs)
res = result_of(ev)
check("D83 Q156 a best-of-3 round in a later turn sends first-try seeds after an earlier turn was retried: turn 1 "
      "d then d + 1,000,000, turn 2 d, candidates d * 1000 + k, the pick d, with no retry recorded",
      res.success and [c["source"] for c in nb.cells] == ["a = 2"]
      and [r["options_sent"]["seed"] for r in rr] == [1, 1000001, 1, 1002, 1003, 1, 1, 1]
      and [r.get("retry") for r in rr] == [None, 1] + [None] * 6
      and sum("transient_retry" in r for r in recs) == 1,
      [(r["options_sent"]["seed"], r.get("candidate"), r.get("retry")) for r in rr])


def ptool(name, args):
    """A reply in the prompt-tools format (```json {"tool_call": ...}```), read by _extract_tool_calls_from_text."""
    return "```json\n" + json.dumps({"tool_call": {"name": name, "arguments": args}}) + "\n```"


# The same on the prompt-tools path (entered after an XML syntax error): turn 2 crashes, its retry edits a cell that
# does not exist (no cell added), and the best-of-3 round of turn 3 sends first-try seeds
ev, recs, seen, nb = d80_step("q156_later_turn_prompt", [
    ("error", "XML syntax error on line 1: unexpected EOF"), ("crash", CRASH),
    ("text", ptool("edit_cell", {"cell_id": "nope", "source": "z = 0"})), ("text", ptool("add_cell", {"source": "a = 1"})),
    ("text", ptool("add_cell", {"source": "a = 2"})), ("text", ptool("add_cell", {"source": "a = 3"})),
    ("text", "Done.")], "best_of_3")
rr = round_recs(recs)
check("D83 Q156 the same on the prompt-tools path: after the XML switch and a retried turn with no cell, the next "
      "round's candidates and pick send d * 1000 + k and d, with no retry recorded",
      [c["source"] for c in nb.cells] == ["a = 2"] and not D80_PICK
      and [r["options_sent"]["seed"] for r in rr] == [1, 1, 1000001, 1, 1002, 1003, 1, 1]
      and [r.get("retry") for r in rr] == [None, None, 1] + [None] * 5
      and sum("transient_retry" in r for r in recs) == 1,
      [(r["options_sent"]["seed"], r.get("candidate"), r.get("retry"), r["status"]) for r in rr])

# A Gemini stall: gemini_client's own stream over a fake transport (one chunk, then the socket times out)
import io  # noqa: E402

D80_GEM = "gemini-3-flash-preview"
gem_posts = []


class _GemStream(io.BytesIO):
    def __init__(self, parts, finish):
        cand = {"content": {"role": "model", "parts": parts}, **({"finishReason": finish} if finish else {})}
        super().__init__(f"data: {json.dumps({'candidates': [cand]})}\n\n".encode())


class _GemStall(_GemStream):
    def __iter__(self):
        yield from self.getvalue().splitlines(keepends=True)
        raise TimeoutError("timed out")


def _gem_open(req, timeout=None):
    body = json.loads(req.data)
    gem_posts.append(body)
    if "You are planning Python code" in json.dumps(body):
        return _GemStream([{"text": "- pandas.read_csv(path) -> DataFrame"}], "STOP")
    return _GemStall([{"text": "Let me"}], None)


_gc = la.gemini_client
_saved = (_gc._open, _gc._arm, _gc._sleep, _gc._key)
_gc._open, _gc._arm, _gc._sleep, _gc._key = _gem_open, lambda r, s: None, lambda s: None, lambda: "offline"
try:
    gsink = TMP / "d80_gemini_stall"
    with rc.run(rc.RunContext(run_id="check-codegen-d80-gemini-stall", arm="check", item_id="Q1", draw=1,
                              thinking=None, base_url="http://127.0.0.1:9", sink=gsink,
                              allowed={D80_GEM: "generator"})):
        gnb = FakeNotebook()

        async def _ggo():
            return [e async for e in se.execute_step(
                step=AlgorithmStep.from_dict({"step_number": 1, "description": "count", "expected_output": "print n"}),
                notebook=gnb, notebook_manager=FakeManager(), kernel=FakeKernel([STEP_OK]), model_router=ModelRouter(),
                model_identifier=f"gemini::{D80_GEM}", previous_results=[], cell_strategy="single")]
        ev = asyncio.run(_ggo())
finally:
    _gc._open, _gc._arm, _gc._sleep, _gc._key = _saved
grecs = [json.loads(x) for x in (gsink / "calls.jsonl").read_text().splitlines()]
gsrs = step_recs(grecs)
res = result_of(ev)
check("D80 V1 a Gemini stall is not retried: one step call, status stalled, no transient_retry, the step fails on it",
      not res.success and [(r["provider"], r["status"]) for r in gsrs] == [("gemini", "stalled")]
      and not any("transient_retry" in r for r in grecs) and "status stalled" in (res.error_message or "")
      and "timed out" not in (res.error_message or "") and gnb.cells == []
      and sum("You are planning Python code" not in json.dumps(b) for b in gem_posts) == 1,
      ([(r["provider"], r["status"], r.get("call_site"), r.get("transient_retry")) for r in grecs],
       res.error_message))

# D81 (the last D80 V1 finding): a Gemini URLError "timed out" before the first chunk. gemini_client records it as
# status error, "URLError: <urlopen error timed out>"; the submitted string rule ('timed out') matches that text, and
# the step must still not retry it
import urllib.error  # noqa: E402

gem_posts.clear()


def _gem_open_timeout(req, timeout=None):
    body = json.loads(req.data)
    gem_posts.append(body)
    if "You are planning Python code" in json.dumps(body):
        return _GemStream([{"text": "- pandas.read_csv(path) -> DataFrame"}], "STOP")
    raise urllib.error.URLError(TimeoutError("timed out"))


_gc._open, _gc._arm, _gc._sleep, _gc._key = _gem_open_timeout, lambda r, s: None, lambda s: None, lambda: "offline"
try:
    tsink = TMP / "d80_gemini_urlerror"
    with rc.run(rc.RunContext(run_id="check-codegen-d81-gemini-urlerror", arm="check", item_id="Q1", draw=1,
                              thinking=None, base_url="http://127.0.0.1:9", sink=tsink,
                              allowed={D80_GEM: "generator"})):
        tnb = FakeNotebook()

        async def _tgo():
            return [e async for e in se.execute_step(
                step=AlgorithmStep.from_dict({"step_number": 1, "description": "count", "expected_output": "print n"}),
                notebook=tnb, notebook_manager=FakeManager(), kernel=FakeKernel([STEP_OK]), model_router=ModelRouter(),
                model_identifier=f"gemini::{D80_GEM}", previous_results=[], cell_strategy="single")]
        ev = asyncio.run(_tgo())
finally:
    _gc._open, _gc._arm, _gc._sleep, _gc._key = _saved
trecs = [json.loads(x) for x in (tsink / "calls.jsonl").read_text().splitlines()]
tsrs = step_recs(trecs)
res = result_of(ev)
check("D81 a Gemini URLError 'timed out' before the first chunk is not retried: one step call, status error, no "
      "transient_retry, the step fails on it (its text holds 'timed out', which the string rule matches)",
      not res.success and [(r["provider"], r["status"]) for r in tsrs] == [("gemini", "error")]
      and "timed out" in (tsrs[0]["error"] if tsrs else "") and "timed out" in (res.error_message or "")
      and not any("transient_retry" in r or "retry" in r for r in trecs) and tnb.cells == []
      and sum("You are planning Python code" not in json.dumps(b) for b in gem_posts) == 1,
      ([(r["provider"], r["status"], r.get("error")) for r in trecs], res.error_message))

ev, recs, seen, nb = d80_step("exhausted", [("error", PE)] * 4 + [("text", "unused")])
srs = step_recs(recs)
res = result_of(ev)
check("D80 V1 after MAX_TRANSIENT_RETRIES retries the step fails on the parse error, 4 calls made",
      se.MAX_TRANSIENT_RETRIES == 3 and not res.success and len(srs) == 4 and PE in (res.error_message or "")
      and [r.get("transient_retry", {}).get("attempt") for r in srs] == [None, 1, 2, 3]
      and [r["options_sent"]["seed"] for r in srs] == [1, 1000001, 2000001, 3000001], res.error_message)

TEXT = "```json\n" + ADD.replace(SRC, "n = 2\\nprint(n)") + "\n```\n```json\n" + EXE + "\n```"
ev, recs, seen, nb = d80_step("text", [("text", TEXT), ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
nxt = ([s["messages"] for s in seen if s["tools"]] + [[]] * 2)[1]
check("D80 V1 an add_cell written as text adds that cell and the step passes",
      res.success and [c["source"] for c in nb.cells] == ["n = 2\nprint(n)"] and res.tool_calls_made == 2,
      [c["source"] for c in nb.cells])
check("D80 V1 its record: native tool_calls empty, tool_calls_from_text holding the call read and the one not read",
      srs[0]["tool_calls"] == [] and read_of(srs[0], "calls")
      == [{"function": {"name": "add_cell", "arguments": {"cell_type": "code", "source": "n = 2\nprint(n)"}}}]
      and read_of(srs[0], "fenced") is True and len(read_of(srs[0], "not_read")) == 1
      and read_of((srs + [{}])[1]) is None, json.dumps(srs[0].get("tool_calls_from_text"))[:200])
check("D80 V1 the next turn carries the call read as a native call",
      nxt[1:3] == [{"role": "assistant", "content": "Called add_cell", "tool_calls": [
          {"function": {"name": "add_cell", "arguments": {"cell_type": "code", "source": "n = 2\nprint(n)"}}}]},
          {"role": "tool", "name": "add_cell", "content": "Cell cell0000 added successfully"}], nxt[1:3])

PYTEXT = read_ok["Python keywords, assigned, then execute_cell (seq 11 airway_5)"].replace(SRC, "n = 4\nprint(n)")
ev, recs, seen, nb = d80_step("python", [("text", PYTEXT), ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
check("D81 Q137 an add_cell in the Python-call form adds that cell and the step passes; its record says so",
      res.success and [c["source"] for c in nb.cells] == ["n = 4\nprint(n)"] and srs[0]["tool_calls"] == []
      and read_of(srs[0], "form") == "python"
      and read_of(srs[0], "calls") == [{"function": {"name": "add_cell",
                                                      "arguments": {"cell_type": "code", "source": "n = 4\nprint(n)"}}}],
      [c["source"] for c in nb.cells])

GLUE = PY_GLUE.replace(SRC, "n = 6")
ev, recs, seen, nb = d80_step("q154", [("text", GLUE), ("execute", None), ("text", "Done.")])
srs = step_recs(recs)
res = result_of(ev)
check("D83 Q154 an add_cell followed by a line keeping its result adds that cell and the step passes; the record "
      "holds the form and the lines not read",
      res.success and [c["source"] for c in nb.cells] == ["n = 6"] and srs[0]["tool_calls"] == []
      and read_of(srs[0], "form") == "python" and read_of(srs[0], "not_read")
      == [{"name": None, "source": 'cell_id = result["cell_id"]'},
          {"name": "functions.execute_cell", "source": 'functions.execute_cell({"cell_id": cell_id})'}],
      (res.success, read_of(srs[0])))

PY = PY_GLUE.replace('result["cell_id"]', "result.cell_id")      # D83 Q154: an attribute is still refused
ev, recs, seen, nb = d80_step("notread", [("text", PY)])
srs = step_recs(recs)
res = result_of(ev)
check("D80 V1 a shape not read ends the step as before: no cell, recorded as nothing read",
      not res.success and nb.cells == [] and len(srs) == 1 and read_of(srs[0]) is None)

ev, recs, seen, nb = d80_step("candidates", [("add", "a = 1"), ("text", ADD.replace(SRC, "a = 2")), ("add", "a = 3"),
                                             ("execute", None), ("text", "Done.")], "best_of_3")
cands = [e for e in ev if e.get("type") == "cell_candidates"]
crec = [r for r in recs if r.get("candidate") == 2]
check("D80 V1 a cell candidate written as text joins the candidates, its record saying so",
      cands and cands[0]["candidates"] == ["a = 1", "a = 2", "a = 3"] and cands[0]["pick"] == 2
      and [c["source"] for c in nb.cells] == ["a = 2"] and len(crec) == 1
      and read_of(crec[0], "calls") == [{"function": {"name": "add_cell",
                                                      "arguments": {"cell_type": "code", "source": "a = 2"}}}],
      cands[0]["candidates"] if cands else None)

la.load = _saved_load

# 15. Q4: an operation with a boolean field (lung_9_schoenfeld)
import contextlib  # noqa: E402
_gt9 = json.loads((M / "tests/experiments_v2/datasets/coder_ground_truth.json").read_text())
_op9 = _gt9["datasets"]["lung_cancer"]["operations"]["lung_9_schoenfeld"]
_ns9 = {"sex_schoenfeld_p": 0.1302, "age_schoenfeld_p": 0.7302, "ph_ecog_schoenfeld_p": 0.1458}
exec("import numpy as np\nany_violation = np.False_", _ns9)
_buf9 = io.StringIO()
try:
    with contextlib.redirect_stdout(_buf9):
        exec(compile(v28.build_extraction_code(_op9["ground_truth"]), "extraction", "exec"), _ns9)
    _got9 = v28._parse_benchmark_output(_buf9.getvalue())
except Exception as e:
    _got9 = repr(e)
check("Q4 extraction code runs for a boolean field and reads a numpy boolean as False",
      isinstance(_got9, dict) and _got9.get("any_violation") is False and _got9.get("sex_schoenfeld_p") == 0.1302
      and v28.verify_results(_got9, _op9["ground_truth"], _op9["tolerance"])["passed"], _got9)
import nbformat  # noqa: E402
_nb9 = nbformat.v4.new_notebook()
for _txt in ("sex_schoenfeld_p: 0.1302\nage_schoenfeld_p: 0.7302\nph_ecog_schoenfeld_p: 0.1458\n"
             "any_violation: False\n", "any_violation: maybe\n"):
    _c = nbformat.v4.new_code_cell("print(...)")
    _c.outputs = [nbformat.v4.new_output("stream", name="stdout", text=_txt)]
    _nb9.cells = [_c]
    nbformat.write(_nb9, str(TMP / "q4.ipynb"))
    _fb9 = v28._extract_from_notebook_cells(str(TMP / "q4.ipynb"), _op9["ground_truth"])
    if "False" in _txt:
        check("Q4 notebook-output fallback reads 'any_violation: False' as False and the operation passes",
              _fb9.get("any_violation") is False
              and v28.verify_results(_fb9, _op9["ground_truth"], _op9["tolerance"])["passed"], _fb9)
    else:
        check("Q4 notebook-output fallback leaves 'any_violation: maybe' unread", "any_violation" not in _fb9, _fb9)

d_runs = runs_snapshot.diff(RUNS_BEFORE, runs_snapshot.take(ROOT / "findings" / "runs"))
check("nothing written under the repository's findings/runs (sha256 of every path, before and after)", not d_runs,
      "; ".join(d_runs))
print(f"check_codegen: {sum(results)} of {len(results)} passed; scratch {TMP}")
sys.exit(0 if all(results) else 1)
