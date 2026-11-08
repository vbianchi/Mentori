"""Checks for T3's harness (audit F4, plan row B13): publication/scripts/exp_04_component_bench.py and
exp_04b_distiller_ablation.py under the lock. Offline: a fake model router (the lock adapter is not called), runs
written to a scratch directory; no model, no Ollama, no key. The lock file is read, never written.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_component_bench

1. Cuts: neither script slices a text it sends or stores; each runner sends a 30,000-character input whole and stores
   a 2,000-character reply whole (LOCK [text]).
2. Options: every runner calls the router with no options and no think (the lock decides; D66).
3. Refusals: a LockError from the router leaves each runner (Q38); any other error is stored as the item's error.
4. Matrix (T3-8, plan row B18): exp_04 and exp_04b each run the six models of T3's core, gpt-oss:20b, devstral, gemma3,
   qwen3-coder:30b, llama3:8b and gemini-3-flash-preview, all at the lock's generator rule (thinking None), none refused.
   Each decision is held on its own: qwen3.5:35b dropped and olmo-3:32b replaced (D77), qwen3-coder:latest as :30b (D83
   Q166), nemotron out (D116), deepseek-r1:70b and gpt-oss:120b out (D83 Q165), olmo-3.1 and qwen3.5:122b out (D197), and
   the lock still refuses the old tags, so a row added back cannot run. exp_04b's Gemini line (D198 O7b).
5. exp_04 end to end: one run context per (item, draw), seen by the router; one answers.jsonl line per key with the
   run's identity; a second pass stores nothing new; a refusal mid-run stops it with the key unstored; with a dataset
   fixture under which main creates a sink for a model the lock runs (the control), main given that model and one
   the lock does not run (a row added to a copy of the matrix) refuses before any call or sink (none for the runnable
   model either), and refuses a run without --ollama-url.
6. exp_04b end to end: the same for one variant and one model, the distillation stored whole. With no dataset,
   --dry-run writes nothing and a run is refused; only --build-dataset writes the dataset.
7. Frozen inputs and counts only (T3-9, D195): load_frozen refuses a changed file, a changed count and a benchmark the
   manifest does not name; main with --datasets runs on the frozen items without reading the ground truth or the V4-4
   file; --counts-only writes the same answers, and its log and its printed output name no metric. Gemini runs through
   exp_04b's run_experiment under the lock's Gemini rows, one sink, no server named but the context's. On the frozen
   inputs of findings/recompute/T3_runs/inputs: each runner takes the first real item of its benchmark with no error, and
   the dry runs give 832 items a model and 1,164 answers for Supplementary Figure 13. The lane's plan (t3_guard.py) names
   the matrix's six models. ModelRouter builds with no key and no server.
"""

import asyncio
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
SCRIPTS = MENTORI / "publication" / "scripts"
tmp = Path(tempfile.mkdtemp(prefix="check_component_bench_")).resolve()
# Mentori's settings read these at import: a scratch database, workspace and vector store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(SCRIPTS))

import exp_04_component_bench as e4  # noqa: E402
import exp_04b_distiller_ablation as e4b  # noqa: E402

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

lock = load()
results = []
BASE = "http://127.0.0.1:9"
GEMMA = "ollama::gemma3:27b"
GEMINI = "gemini::gemini-3-flash-preview"
T3_SIX = {"ollama::gpt-oss:20b", "ollama::devstral-small-2:24b", GEMMA, "ollama::qwen3-coder:30b", "ollama::llama3:8b", GEMINI}


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


class FakeRouter:
    """router.chat answered by `reply(text)`; each call keeps its kwargs and the run context it ran in. A reply that
    is an exception is raised."""

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    async def chat(self, model_identifier, messages, tools=None, options=None, think=None):
        ctx = rc.current()
        text = "\n".join(m.get("content", "") for m in messages)
        self.calls.append({"model": model_identifier, "text": text, "options": options, "think": think,
                           "item_id": ctx.item_id, "draw": ctx.draw, "run_id": ctx.run_id})
        out = self.reply(text)
        if isinstance(out, BaseException):
            raise out
        return {"message": {"role": "assistant", "content": out, "thinking": "", "tool_calls": []},
                "response": out, "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1}


def ctx_for(item="0000_Q1", draw=1, run="exp_04__analyzer__gemma3-27b"):
    return rc.RunContext(run_id=run, arm="analyzer", item_id=item, draw=draw, thinking=None, base_url=BASE,
                         sink=tmp / "direct" / run, allowed={"gemma3:27b": "generator"},
                         agent_roles={"analyzer": GEMMA})


def run(coro):
    return asyncio.run(coro)


BIG = "Result 42.0% (n=7) in 01_x.pdf. " * 940          # 30,080 characters
REPLY = '{"decision": "needs_plan", "complexity": "simple", "quality_score": 70, "steps": []}' + " " * 1950
ITEMS = {
    "analyzer": {"query": "What is X?", "expected_decision": "needs_plan", "expected_complexity": "simple",
                 "source": "ground_truth", "question_id": "FR_001"},
    "planner": {"query": "What is X?", "expected_tools": ["smart_query"], "expected_agent": "editor",
                "expected_steps": 1, "question_id": "FR_001"},
    "supervisor": {"question_id": "FR_001", "goal": "g", "step_description": "s", "tool_name": "smart_query",
                   "tool_args": "{}", "expected_output": "e", "answer": BIG},
    "distiller": {"question_id": "FR_001", "raw_content": BIG, "raw_length": len(BIG), "tool_name": "smart_query",
                  "numbers": ["42.0%"], "sources": ["01_x.pdf"]},
    "synthesizer": {"question_id": "FR_001", "question": "What is X?", "step_result_content": BIG},
}
STORED = {"analyzer": "raw_response", "planner": "raw_response", "supervisor": "raw_response",
          "distiller": "distilled", "synthesizer": "answer"}

# ── 1. Cuts ──────────────────────────────────────────────────────────────────
for path in (SCRIPTS / "exp_04_component_bench.py", SCRIPTS / "exp_04b_distiller_ablation.py"):
    src = path.read_text(encoding="utf-8")
    cuts = re.findall(r"\b(?:text|content|raw_content|answer)\[:\d+\]|\]\[:\d+\]", src)
    check(f"1 {path.name}: no text slice left (audit F4)", not cuts, cuts)

# ── 1, 2, 3. Each runner ─────────────────────────────────────────────────────
for bench, runner in e4.BENCH_RUNNERS.items():
    fr = FakeRouter(lambda t: REPLY)
    with rc.run(ctx_for()):
        out = run(runner(ITEMS[bench], fr, GEMMA))
    c = fr.calls[0] if fr.calls else {}
    check(f"2 {bench}: no options and no think sent to the router", c.get("options") is None
          and c.get("think") is None, {k: c.get(k) for k in ("options", "think")})
    if bench in ("supervisor", "distiller", "synthesizer"):
        check(f"1 {bench}: the 30,080-character input is in the prompt whole", BIG in c.get("text", ""))
    check(f"1 {bench}: the {len(REPLY)}-character reply stored whole in {STORED[bench]}",
          out.get(STORED[bench]) == REPLY, len(out.get(STORED[bench]) or ""))
    try:
        with rc.run(ctx_for()):
            run(runner(ITEMS[bench], FakeRouter(lambda t: LockError("refused")), GEMMA))
        check(f"3 {bench}: a lock refusal leaves the runner (Q38)", False)
    except LockError:
        check(f"3 {bench}: a lock refusal leaves the runner (Q38)", True)
    with rc.run(ctx_for()):
        out = run(runner(ITEMS[bench], FakeRouter(lambda t: RuntimeError("status error")), GEMMA))
    check(f"3 {bench}: a failed call is stored as the item's error", out.get("error") == "status error", out.get("error"))

fr = FakeRouter(lambda t: "KEY FINDINGS 42.0% 01_x.pdf")
with rc.run(ctx_for(run="exp_04b__F2__gemma3-27b")):
    out = run(e4b.run_single(ITEMS["distiller"], "F2", fr, GEMMA))
check("2 exp_04b: no options and no think sent to the router",
      fr.calls[0]["options"] is None and fr.calls[0]["think"] is None)
check("1 exp_04b F2: the observation whole, the word budget in the prompt",
      BIG in fr.calls[0]["text"] and "≤ 400 words" in fr.calls[0]["text"])   # 3 distinct numbers: the floor, 400
for v in e4b.ALL_VARIANTS:
    p = e4b.build_prompt(v, "smart_query", BIG)
    if not (isinstance(p, str) and BIG in p):
        check(f"1 exp_04b {v}: build_prompt returns the prompt with the observation whole", False)
        break
else:
    check("1 exp_04b: every variant's build_prompt returns the prompt with the observation whole", True)
try:
    with rc.run(ctx_for()):
        run(e4b.run_single(ITEMS["distiller"], "F1", FakeRouter(lambda t: LockError("refused")), GEMMA))
    check("3 exp_04b: a lock refusal leaves run_single (Q38)", False)
except LockError:
    check("3 exp_04b: a lock refusal leaves run_single (Q38)", True)

# ── 4. Matrix ────────────────────────────────────────────────────────────────
entries, refused = e4.model_matrix(lock)
ids = [m for m, _, _ in entries]
check("4 exp_04's matrix is T3's six models and refuses none", set(ids) == T3_SIX and len(ids) == 6 and not refused,
      (ids, refused))
check("4 every model at the lock's generator rule (thinking None, D66)", all(t == (None,) for _, _, t in entries), entries)
check("4 D77: qwen3.5:35b dropped, olmo-3:32b replaced", e4.t3_model("ollama::qwen3.5:35b") is None
      and e4.D77_REPLACED["ollama::olmo-3:32b"] == "ollama::olmo-3.1:32b-think")
check("4 D83 Q166: qwen3-coder:latest runs as qwen3-coder:30b",
      e4.t3_model("ollama::qwen3-coder:latest") == "ollama::qwen3-coder:30b")
out_of_t3 = {"ollama::nemotron-3-nano:30b": "D116", "ollama::deepseek-r1:70b": "D83 Q165", "ollama::gpt-oss:120b": "D83 Q165",
             "ollama::olmo-3:32b": "D197", "ollama::olmo-3.1:32b-think": "D197", "ollama::qwen3.5:122b": "D197"}
check("4 each left-out model stays out, by its decision", all(e4.t3_model(m) is None for m in out_of_t3)
      and all(why in e4.LEFT_OUT.get(e4.D77_REPLACED.get(m, m), "") for m, why in out_of_t3.items()),
      {m: e4.t3_model(m) for m in out_of_t3})
for old in ("ollama::qwen3-coder:latest", "ollama::qwen3:235b"):
    try:
        e4.lock_check(lock, old, None)
        check(f"4 the lock refuses {old}", False)
    except LockError as e:
        check(f"4 the lock refuses {old}", "no digest" in str(e), str(e)[:80])
b_entries, b_refused = e4b.model_list(lock)
b_ids = [m for m, _ in b_entries]
check("4 exp_04b's list is the same six models, Gemini's line included, and refuses none (D198 O7b)",
      set(b_ids) == T3_SIX and len(b_ids) == 6 and not b_refused, (b_ids, b_refused))

# ── 5. exp_04 end to end ─────────────────────────────────────────────────────
root = tmp / "runs"
ds = [dict(ITEMS["analyzer"], question_id=f"FR_00{i}") for i in range(3)] + [
    {"query": "Hello!", "expected_decision": "direct_answer", "expected_complexity": "trivial", "source": "greeting"}]
args = SimpleNamespace(max_items=None, draws=[2, 1], runs_root=root, ollama_url=BASE)
fr = FakeRouter(lambda t: '{"decision": "needs_plan", "complexity": "simple"}')
out = run(e4.run_benchmark("analyzer", ds, [(GEMMA, "27B", (None,))], fr, args))
rid = "exp_04__analyzer__gemma3-27b"
sink = root / rid
lines = [json.loads(x) for x in (sink / e4.ANSWERS).read_text().splitlines()]
check("5 one call and one stored line per (item, draw): 4 items x 2 draws",
      len(fr.calls) == 8 and len(lines) == 8, (len(fr.calls), len(lines)))
check("5 every call ran in its own item's context (item_id, draw, run_id)",
      [(c["item_id"], c["draw"]) for c in fr.calls] == [(r["item_id"], r["run_draw"]) for r in lines]
      and {c["run_id"] for c in fr.calls} == {rid}
      and [c["item_id"] for c in fr.calls[:4]] == ["0000_FR_000", "0001_FR_001", "0002_FR_002", "0003"],
      [(c["item_id"], c["draw"]) for c in fr.calls])
check("5 answer keys <model key>|<item_id>|d<draw>, draws in order 1 then 2",
      [r["answer_key"] for r in lines][:2] == ["gemma3-27b|0000_FR_000|d1", "gemma3-27b|0001_FR_001|d1"]
      and [r["draw"] for r in lines] == [1] * 4 + [2] * 4, [r["answer_key"] for r in lines][:2])
ident = json.loads((sink / ex.IDENTITY_FILE).read_text())
check("5 run identity: thinking None, the model alone as a generator, no judge (A7)",
      ident["thinking"] is None and ident["allowed"] == {"gemma3:27b": "generator"}
      and ident["agent_roles"] == {"analyzer": GEMMA}, ident)
check("5 the summary comes from the stored answers", out["summary"]["gemma3-27b"]["n"] == 8
      and out["summary"]["gemma3-27b"]["decision_accuracy"] == 0.75, out["summary"])
fr2 = FakeRouter(lambda t: "{}")
run(e4.run_benchmark("analyzer", ds, [(GEMMA, "27B", (None,))], fr2, args))
check("5 a second pass makes no call and stores nothing new (a run always resumes)",
      not fr2.calls and len((sink / e4.ANSWERS).read_text().splitlines()) == 8)
n = {"k": 0}


def refuse_second(t):
    n["k"] += 1
    return LockError("not allowed") if n["k"] == 2 else '{"decision": "needs_plan"}'


ds2 = [dict(ITEMS["analyzer"], question_id=f"FR_10{i}") for i in range(3)]
args2 = SimpleNamespace(max_items=None, draws=[1], runs_root=root / "r2", ollama_url=BASE)
try:
    run(e4.run_benchmark("analyzer", ds2, [(GEMMA, "27B", (None,))], FakeRouter(refuse_second), args2))
    check("5 a refusal mid-run stops it", False)
except SystemExit as e:
    kept = [json.loads(x)["answer_key"] for x in (root / "r2" / rid / e4.ANSWERS).read_text().splitlines()]
    check("5 a refusal mid-run stops it; the earlier key kept, the refused key unstored (Q38)",
          kept == ["gemma3-27b|0000_FR_100|d1"] and "0001_FR_101" in str(e), (kept, str(e)))
saved = sys.argv
# A dataset fixture for main: a ground-truth file that exists, read as two questions, built into the analyzer items
# above, and a fake router. Without it main builds no analyzer dataset where the ground truth is absent, and the
# refusal check below would pass with no sink whether or not the refusal came first.
gt_fixture = tmp / "ground_truth_fixture.json"
gt_fixture.write_text("[]", encoding="utf-8")
patched = {"GROUND_TRUTH_PATH": gt_fixture, "load_ground_truth": lambda p: [{"id": "FR_200"}, {"id": "FR_201"}],
           "build_analyzer_dataset": lambda gt: [dict(ITEMS["analyzer"], question_id=q["id"]) for q in gt]}
fr_main = FakeRouter(lambda t: '{"decision": "needs_plan", "complexity": "simple"}')
patched["ModelRouter"] = lambda: fr_main
# A row the lock does not run, kept by t3_model: no row of the real matrix is refused any more (section 4)
patched["SUBMITTED_MATRIX"] = e4.SUBMITTED_MATRIX + [("ollama::not-in-the-lock:1b", "1B", [False])]
originals = {k: getattr(e4, k) for k in patched}
for k, v in patched.items():
    setattr(e4, k, v)
try:
    sys.argv = ["exp_04", "--benchmark", "analyzer", "--models", "gemma3:27b", "--draws", "1", "--ollama-url", BASE,
                "--runs-root", str(root / "r3_control")]
    run(e4.main())
    control = root / "r3_control" / rid / e4.ANSWERS
    check("5 control: with the fixture and a model the lock runs, main creates the sink and stores 2 answers",
          control.exists() and len(control.read_text().splitlines()) == 2 and len(fr_main.calls) == 2,
          (control.exists(), len(fr_main.calls)))
    fr_main.calls.clear()
    # The control's runnable model plus one the lock refuses: without the up-front refusal, main would run gemma3:27b
    # and create its sink under r3, so an empty r3 and no call show the refusal came first
    both = "gemma3:27b,not-in-the-lock:1b"
    sel_run, sel_ref = e4.select_models(both)
    check("5 the refusal run's selection: gemma3:27b runnable, the added row refused",
          [m for m, _, _ in sel_run] == [GEMMA] and [m for m, _ in sel_ref] == ["ollama::not-in-the-lock:1b"],
          ([m for m, _, _ in sel_run], [m for m, _ in sel_ref]))
    try:
        sys.argv = ["exp_04", "--benchmark", "analyzer", "--models", both, "--draws", "1", "--ollama-url", BASE,
                    "--runs-root", str(root / "r3")]
        run(e4.main())
        check("5 main refuses a model the lock does not run", False)
    except SystemExit as e:
        check("5 main refuses a model the lock does not run alongside one it runs, with the same fixture, before any "
              "call or sink (none for gemma3:27b either)",
              "the lock does not run ollama::not-in-the-lock:1b" in str(e) and not (root / "r3").exists()
              and not (root / "r3" / rid).exists() and not fr_main.calls, str(e)[:160])
finally:
    for k, v in originals.items():
        setattr(e4, k, v)
try:
    sys.argv = ["exp_04", "--benchmark", "analyzer"]
    run(e4.main())
    check("5 main refuses a run without --ollama-url", False)
except SystemExit as e:
    check("5 main refuses a run without --ollama-url", e.code == 2, e.code)
finally:
    sys.argv = saved

# ── 6. exp_04b end to end ────────────────────────────────────────────────────
dist = [dict(ITEMS["distiller"], question_id=f"synthetic_00{i}") for i in range(2)]
fr = FakeRouter(lambda t: "KEY FINDINGS 42.0% 01_x.pdf " + "x" * 2000)
run(e4b.run_experiment(dist, ["F1"], [(GEMMA, "27B")], BASE, draws=(1,), runs_root=root, router=fr))
rid_b = "exp_04b__F1__gemma3-27b"
lines = [json.loads(x) for x in (root / rid_b / e4b.ANSWERS).read_text().splitlines()]
check("6 exp_04b: one context per item, one stored line each, the distillation whole",
      len(lines) == 2 and [c["item_id"] for c in fr.calls] == ["0000_synthetic_000", "0001_synthetic_001"]
      and all(r["run_id"] == rid_b and len(r["distilled"]) == 2028 for r in lines)
      and all(BIG in c["text"] and c["options"] is None and c["think"] is None for c in fr.calls),
      [(r.get("item_id"), len(r.get("distilled", ""))) for r in lines])
ident = json.loads((root / rid_b / ex.IDENTITY_FILE).read_text())
check("6 exp_04b run identity: thinking None, the distiller role on the model alone",
      ident["thinking"] is None and ident["agent_roles"] == {"distiller": GEMMA}
      and ident["allowed"] == {"gemma3:27b": "generator"}, ident)

# exp_04b's main and the dataset: the V4-4 results present (so the submitted code would have built and written the
# dataset), the dataset absent; only --build-dataset writes it
v44 = tmp / "v4_4_fixture.json"
v44.write_text(json.dumps({"per_question_results": []}), encoding="utf-8")
ds_path = tmp / "results_v4" / "v4_7_bench_distiller_dataset.json"
saved_paths = (e4b.DATASET_PATH, e4b.V4_4_RESULTS_PATH, e4b.RESULTS_DIR)
e4b.DATASET_PATH, e4b.V4_4_RESULTS_PATH, e4b.RESULTS_DIR = ds_path, v44, ds_path.parent
saved = sys.argv
try:
    sys.argv = ["exp_04b", "--dry-run", "--models", "gemma3:27b", "--runs-root", str(root / "b_dry")]
    e4b.main()
    check("6 exp_04b --dry-run with no dataset writes nothing (no dataset file, no run)",
          not ds_path.exists() and not ds_path.parent.exists() and not (root / "b_dry").exists())
    try:
        sys.argv = ["exp_04b", "--models", "gemma3:27b", "--ollama-url", BASE, "--runs-root", str(root / "b_run")]
        e4b.main()
        check("6 exp_04b refuses a run with no dataset", False)
    except SystemExit as e:
        check("6 exp_04b refuses a run with no dataset, writing nothing",
              "--build-dataset" in str(e) and not ds_path.exists() and not (root / "b_run").exists(), str(e)[:160])
    sys.argv = ["exp_04b", "--build-dataset"]
    e4b.main()
    check("6 exp_04b --build-dataset writes the dataset", ds_path.exists()
          and isinstance(json.loads(ds_path.read_text()), list))
finally:
    sys.argv = saved
    e4b.DATASET_PATH, e4b.V4_4_RESULTS_PATH, e4b.RESULTS_DIR = saved_paths

# ── 7. Frozen inputs and counts only ─────────────────────────────────────────
frozen = tmp / "frozen"
frozen.mkdir()


def write_frozen(folder, rows_by_bench):
    files = {}
    for bench, rows in rows_by_bench.items():
        raw = json.dumps(rows).encode()
        (folder / f"{bench}.json").write_bytes(raw)
        files[bench] = {"file": f"{bench}.json", "sha256": hashlib.sha256(raw).hexdigest(), "items": len(rows)}
    (folder / "MANIFEST.json").write_text(json.dumps({"files": files}))


frozen_rows = {"analyzer": [dict(ITEMS["analyzer"], question_id=f"FR_30{i}") for i in range(2)],
               "distiller": [dict(ITEMS["distiller"], question_id=f"synthetic_30{i}") for i in range(2)]}
write_frozen(frozen, frozen_rows)
loaded = e4.load_frozen(frozen, ["analyzer", "distiller"])
check("7 load_frozen returns the items of both files", loaded == frozen_rows)


def refused_with(folder, benches, word):
    try:
        e4.load_frozen(folder, benches)
        return False
    except SystemExit as e:
        return word in str(e)


check("7 load_frozen refuses a benchmark the manifest does not name", refused_with(frozen, ["planner"], "names no planner"))
bad = tmp / "frozen_bad"
bad.mkdir()
write_frozen(bad, frozen_rows)
(bad / "analyzer.json").write_text(json.dumps(frozen_rows["analyzer"]) + " ")
check("7 load_frozen refuses a file whose bytes changed", refused_with(bad, ["analyzer"], "sha256"))
short = tmp / "frozen_short"
short.mkdir()
write_frozen(short, frozen_rows)
m = json.loads((short / "MANIFEST.json").read_text())
m["files"]["analyzer"]["items"] = 3
(short / "MANIFEST.json").write_text(json.dumps(m))
check("7 load_frozen refuses a count that differs", refused_with(short, ["analyzer"], "the manifest says 3"))
check("7 load_frozen refuses a folder with no manifest", refused_with(tmp, ["analyzer"], "MANIFEST.json"))


class Grab(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


METRIC_WORDS = re.compile(r"accuracy|num_ret|src_ret|Metrics|retention|rho|pass_rate|json=|NumRet|SrcRet")
grab = Grab()
e4.logger.addHandler(grab)
e4b.logger.addHandler(grab)
fr_frozen = FakeRouter(lambda t: '{"decision": "needs_plan", "complexity": "simple"}')
out = io.StringIO()
missing = {"GROUND_TRUTH_PATH": tmp / "not_there_gt.json", "V4_4_RESULTS_PATH": tmp / "not_there_v44.json",
           "ModelRouter": lambda: fr_frozen}
originals = {k: getattr(e4, k) for k in missing}
for k, v in missing.items():
    setattr(e4, k, v)
saved = sys.argv
try:
    sys.argv = ["exp_04", "--benchmark", "analyzer", "--models", "gemma3:27b", "--draws", "1", "--ollama-url", BASE,
                "--runs-root", str(root / "r7"), "--datasets", str(frozen), "--counts-only"]
    with contextlib.redirect_stdout(out):
        run(e4.main())
finally:
    sys.argv = saved
    for k, v in originals.items():
        setattr(e4, k, v)
    e4.logger.removeHandler(grab)
stored = [json.loads(x) for x in (root / "r7" / rid / e4.ANSWERS).read_text().splitlines()]
check("7 exp_04 main with --datasets runs on the frozen items, the other two files absent",
      [r["answer_key"] for r in stored] == ["gemma3-27b|0000_FR_300|d1", "gemma3-27b|0001_FR_301|d1"], len(stored))
check("7 exp_04 --counts-only: answers carry their scores in the file, as without it", "decision_correct" in stored[0])
check("7 exp_04 --counts-only: no metric in its log or its printed output",
      not METRIC_WORDS.search(out.getvalue()) and not any(METRIC_WORDS.search(x) for x in grab.lines),
      [x for x in grab.lines if METRIC_WORDS.search(x)][:3])
check("7 control: the same log check finds a metric line when --counts-only is off",
      METRIC_WORDS.search(e4._key_metric_for_bench("analyzer", {"decision_accuracy": 0.5})) is not None)

grab2 = Grab()
e4b.logger.removeHandler(grab)
e4b.logger.addHandler(grab2)
fr_g = FakeRouter(lambda t: "KEY FINDINGS 42.0% 01_x.pdf")
outb = io.StringIO()
with contextlib.redirect_stdout(outb):
    run(e4b.run_experiment(frozen_rows["distiller"], ["baseline", "F1"], [(GEMINI, "API")], BASE, draws=(1,),
                           runs_root=root / "r7b", router=fr_g, counts_only=True))
e4b.logger.removeHandler(grab2)
rid_g = "exp_04b__baseline__gemini-3-flash-preview"
g_lines = (root / "r7b" / rid_g / e4b.ANSWERS).read_text().splitlines()
ident = json.loads((root / "r7b" / rid_g / ex.IDENTITY_FILE).read_text())
check("7 exp_04b runs Gemini on baseline and F1 at draw 1, one sink each",
      len(g_lines) == 2 and (root / "r7b" / "exp_04b__F1__gemini-3-flash-preview" / e4b.ANSWERS).exists()
      and ident["agent_roles"] == {"distiller": GEMINI} and len(fr_g.calls) == 4, ident.get("agent_roles"))
check("7 exp_04b --counts-only: no metric in its log or its printed output",
      not METRIC_WORDS.search(outb.getvalue()) and not any(METRIC_WORDS.search(x) for x in grab2.lines),
      outb.getvalue()[:200])
saved = sys.argv
fr_b = FakeRouter(lambda t: "KEY FINDINGS")
saved_router = e4b.ModelRouter
e4b.ModelRouter = lambda: fr_b
try:
    sys.argv = ["exp_04b", "--variants", "F1", "--models", "gemma3:27b", "--draws", "1", "--ollama-url", BASE,
                "--runs-root", str(root / "r7c"), "--datasets", str(frozen), "--counts-only"]
    with contextlib.redirect_stdout(io.StringIO()):
        e4b.main()
finally:
    sys.argv = saved
    e4b.ModelRouter = saved_router
check("7 exp_04b main with --datasets runs on the frozen distiller items, DATASET_PATH not read",
      len((root / "r7c" / "exp_04b__F1__gemma3-27b" / e4b.ANSWERS).read_text().splitlines()) == 2 and len(fr_b.calls) == 2)

# The repository's frozen inputs: the items' fields reach each runner; the replies are the fake router's, nothing is printed
inputs = ROOT / "findings" / "recompute" / "T3_runs" / "inputs"
real = e4.load_frozen(inputs, e4.BENCHMARK_NAMES)
check("7 the frozen inputs load: 832 items", sum(len(v) for v in real.values()) == 832, {k: len(v) for k, v in real.items()})
for bench, runner in e4.BENCH_RUNNERS.items():
    with rc.run(ctx_for()):
        out = run(runner(real[bench][0], FakeRouter(lambda t: REPLY), GEMMA))
    check(f"7 {bench}: the first frozen item goes through its runner", out.get("error") is None, out.get("error"))
with rc.run(ctx_for(run="exp_04b__F1__gemma3-27b")):
    out = run(e4b.run_single(real["distiller"][0], "F1", FakeRouter(lambda t: "KEY FINDINGS"), GEMMA))
check("7 exp_04b: the first frozen distiller item goes through run_single", out.get("error") is None, out.get("error"))
saved = sys.argv
try:
    sys.argv = ["exp_04", "--dry-run", "--datasets", str(inputs), "--draws", "1", "--runs-root", str(root / "r7d")]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(e4.main())
    check("7 exp_04 --dry-run on the frozen inputs: 6 models, 4,992 answers at draw 1",
          "6 models the lock runs" in buf.getvalue() and "0 models the lock refuses" in buf.getvalue()
          and sum(int(x) for x in re.findall(r"= (\d+) answers", buf.getvalue())) == 4992, buf.getvalue()[-400:])
    sys.argv = ["exp_04b", "--dry-run", "--datasets", str(inputs), "--variants", "baseline", "F1", "--draws", "1",
                "--runs-root", str(root / "r7e")]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e4b.main()
    check("7 exp_04b --dry-run on the frozen inputs: 1,164 answers, Supplementary Figure 13's count",
          "97 items x 2 variants x 6 models x 1 draws = 1164 answers, 0 stored" in buf.getvalue(), buf.getvalue()[-300:])
finally:
    sys.argv = saved
spec = importlib.util.spec_from_file_location("t3_guard_check", ROOT / "findings" / "recompute" / "T3_runs" / "t3_guard.py")
guard = importlib.util.module_from_spec(spec)
sys.modules["t3_guard_check"] = guard
spec.loader.exec_module(guard)
check("7 the lane's plan names the matrix's six models",
      {f"ollama::{t}" for t in guard.LOCAL_ORDER} | {f"gemini::{guard.GEMINI}"} == T3_SIX)
# Every step of the lane, core and smoke, through each script's own parser, as run_t3.sh sends it (--dry-run added)
bad_steps = []
for job in guard.jobs():
    for stage in ("core", "smoke"):
        for step, key, options, _ in guard.steps(job, stage):
            line = [*options, "--ollama-url", BASE, "--datasets", str(inputs), "--counts-only", "--dry-run",
                    "--runs-root", str(root / "r7f")]
            buf = io.StringIO()
            saved = sys.argv
            try:
                sys.argv = ["script", *line]
                with contextlib.redirect_stdout(buf):
                    if key == "a":
                        run(e4.main())
                    else:
                        e4b.main()
            except SystemExit as e:
                bad_steps.append((job, stage, step, e.code))
            finally:
                sys.argv = saved
            if "1 models the lock runs" not in buf.getvalue():
                bad_steps.append((job, stage, step, buf.getvalue()[:120]))
check("7 every step of the lane parses in its script and selects its one model", not bad_steps, bad_steps[:3])
# A start past exp_04 makes its first call through exp_04b (t3_guard.py first_call): its options through exp_04b's parser
late = root / "r7g"
late_job = guard.jobs("local")[0]
for rid, want in guard.sinks(late_job, "core").items():
    if rid.startswith("exp_04__"):
        (late / rid).mkdir(parents=True)
        (late / rid / "answers.jsonl").write_text("".join(json.dumps({"answer_key": f"made-up-{i}"}) + "\n" for i in range(want)))
late_key, *late_options = guard.first_call(late, late_job, "core")
buf = io.StringIO()
saved = sys.argv
try:
    sys.argv = ["script", *late_options, "--ollama-url", BASE, "--datasets", str(inputs), "--counts-only", "--dry-run",
                "--runs-root", str(late)]
    with contextlib.redirect_stdout(buf):
        e4b.main()
finally:
    sys.argv = saved
check("7 first_call past exp_04 parses in exp_04b and selects its one model",
      late_key == "b" and "1 models the lock runs" in buf.getvalue(), buf.getvalue()[:200])
from backend.agents.model_router import ModelRouter  # noqa: E402
check("7 ModelRouter builds with no key and no server", ModelRouter() is not None)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
