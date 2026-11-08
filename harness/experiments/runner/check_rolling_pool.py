"""Checks for D80 V16 (B9 F2, F5, O2, O3): experiments/runner/pool.py, and exp_01_generation.py and
exp_02_scaling_factorial.py scheduling answers through it, with exp_02's files per process. Offline: the strategies,
database, index and router are stubbed (no model call, no Ollama or Gemini contact, no Chroma store read); every file
is written in a scratch directory. The lock file is read, never written.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_rolling_pool

1. pool.rolling on fake items, one slow: items start in the order given; never more than the size run at once, and
   the pool fills to it; while the slow item runs, the other slot runs every other item; each item is passed to done
   once, with the number in flight at its start (1 to the size). A mutant with fixed batches (the old gather) fails
   the slow-item test. A stop result starts nothing more, lets the items in flight end and be stored, then is raised;
   an error in done cancels the items still running; a size that is not an integer from 1 is refused.
2. exp_01 run_experiment, smoke runs under a scratch --sink-root, a fake strategy whose first question is slow, for a
   fast config (pool 6) and an RLM config (pool 2): every key stored once; the strategy started in work-list order,
   each answer inside its own run context (run_id, item_id, draw) with the question's text; at most the pool size in
   flight and the pool full; every other answer stored before the slow one ended; each line's "pool" names the size
   and its in-flight count. The same run with the fixed-batch mutant: the same records apart from scheduling (pool,
   pid, ctx_uid, seq), and the slow-answer test fails. A stop: nothing started after it, the answers in flight stored,
   the stop raised, its key unstored.
3. exp_02 run_experiment, the same on one index (pool 4, the RLM config), plus: each answer one line of its run's
   answers.jsonl, the report named by the index, no intermediate file; the report's rows are the sink's lines without
   what run_context adds, in order and key order; a second start into the same sinks without --resume is refused on
   the stored answers, writing nothing; a --resume start of the finished run starts nothing, adds no line and writes a
   report with the same rows.
4. Two exp_02 processes (this module run with --child) on different indexes at the same time, both mid-run at once:
   their reports (_latest.json included) and sinks are different files, each holding only its own index's answers and
   each sink line its own process's pid; a third process on one of the two indexes, started while that one runs, is
   refused and writes nothing. With the old names (one v4_5_smoke_intermediate.json and one v4_5_scaling_smoke prefix
   for every process) the two would write the same files.
5. A crash (review of 16 October, F1): an exp_02 process (this module run with --crash) ends by os._exit right after
   its 7th answers.jsonl line, before any later step (its log line, the answers in flight, the next draws, the
   report). Without --resume the next start is refused, writing nothing; with --resume it runs only the keys the sink
   lacks and ends with every key of the work list stored once, the 7 lines before the crash unchanged, and the report
   from the sink. Two mutants fail the same resume: the old resume logic (done = the intermediate file's keys, which
   the crash left one short of the sink, and a key to run that the sink stores refused) is refused on the crashed key
   for ever; a resume that ignores the sink stores the keys before the crash a second time.
"""

import asyncio
import contextlib
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
SCRIPTS = MENTORI / "publication" / "scripts"
tmp = Path(tempfile.mkdtemp(prefix="check_rolling_pool_")).resolve()
# Mentori's settings read these at import: a scratch database, workspace and vector store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
sys.path.insert(0, str(MENTORI))
sys.path.insert(0, str(SCRIPTS))
os.chdir(tmp)       # Mentori's app.log is written under the working directory: the scratch one, not the repository

import exp_01_generation as e01  # noqa: E402
import exp_02_scaling_factorial as e02  # noqa: E402
import exp_common  # noqa: E402  (the module whose save_v4_results exp_02 calls)

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import pool  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402

for name in ("exp_01_generation", "exp_02_scaling_factorial"):
    logging.getLogger(name).setLevel(logging.WARNING)

BASE = "http://127.0.0.1:9"
SLOW, FAST = 0.8, 0.03
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


async def fixed_batches(items, size, run, done, stops=()):
    """The mutant: the old scheduling, fixed batches of size, each an asyncio.gather, the next after the slowest."""
    items, stop = list(items), None
    for b in range(0, len(items), size):
        batch = items[b:b + size]
        res = await asyncio.gather(*(run(i) for i in batch), return_exceptions=True)
        for k, (i, r) in enumerate(zip(batch, res)):
            if stops and isinstance(r, stops) and stop is None:
                stop = r
            done(i, r, k + 1)
        if stop is not None:
            raise stop


class Stop(Exception):
    pass


class Probe:
    """Records starts, ends and the most running at once, in a run's own clock."""

    def __init__(self):
        self.t0 = time.monotonic()
        self.running = 0
        self.most = 0
        self.starts, self.ends = [], {}

    def start(self, name):
        self.starts.append(name)
        self.running += 1
        self.most = max(self.most, self.running)

    def end(self, name):
        self.running -= 1
        self.ends[name] = time.monotonic() - self.t0


def slow_held_one_slot(order: list, slow) -> bool:
    """The slow item was stored last, after every other item: the other slots ran the rest while it ran."""
    return bool(order) and order[-1] == slow and len(order) > 2


def lines(path: Path) -> list:
    return [json.loads(ln) for ln in path.read_text().splitlines()] if path.exists() else []


SCHED = {"pool", "pid", "ctx_uid", "seq"}     # what the scheduling may change in a stored line


def fake_strategy(probe: Probe, gen_cls, seen: list, slow_id: str, stop_id=None):
    async def _run_config(config_name, question, retriever, collection_name, router, gen_model, user_id, index_name,
                          budget=None):
        ctx = rc.current()
        seen.append({"q": ctx.item_id, "run_id": ctx.run_id, "draw": ctx.draw, "question": question,
                     "config": config_name, "gen_model": gen_model, "index": index_name})
        probe.start(ctx.item_id)
        try:
            await asyncio.sleep(SLOW if ctx.item_id == slow_id else FAST)
            if ctx.item_id == stop_id:
                raise e01.STOPS[-1]("stopped by the check (RLMStop)")
            return gen_cls(answer=f"answer to {ctx.item_id}", latency_s=0.0, llm_calls=1, tokens_used=1,
                           retrieved_passages=0, config=config_name, gen_model=gen_model)
        finally:
            probe.end(ctx.item_id)
    return _run_config


IDX = "exp_v4_s5_n0"
saved_e02 = {n: getattr(e02, n) for n in ("_run_config", "find_admin_user_id", "check_indexes", "setup_retriever",
                                          "ModelRouter", "index_identity", "V4_RESULTS_DIR", "pool", "RUNS_ROOT",
                                          "work_list")}
CRASH_RC = 17       # the exit code of a --crash child that reached its os._exit
saved_results_dir = exp_common.V4_RESULTS_DIR


def e02_stubs(probe, seen, slow_id, results_dir, scheduler=None, wait=None, stop_id=None):
    fake = fake_strategy(probe, e02.GenerationResult, seen, slow_id, stop_id)

    async def strategy(*a, **k):
        if wait is not None:
            await wait(rc.current().item_id)
        return await fake(*a, **k)
    e02._run_config = strategy
    e02.find_admin_user_id = lambda: "u"
    e02.check_indexes = lambda user_id, indexes: None
    e02.setup_retriever = lambda u, i: (None, f"coll_{i}", "emb")
    e02.ModelRouter = lambda: None
    e02.index_identity = SimpleNamespace(record=lambda *a, **k: None)
    e02.V4_RESULTS_DIR = exp_common.V4_RESULTS_DIR = results_dir
    e02.RUNS_ROOT = tmp / "e02_runs_root_unused"
    e02.pool = SimpleNamespace(rolling=scheduler) if scheduler else pool


def e02_restore():
    for k, v in saved_e02.items():
        setattr(e02, k, v)
    exp_common.V4_RESULTS_DIR = saved_results_dir


def e02_run(indexes, n, sink_root, results_dir, scheduler=None, config="rlm_10", wait=None, resume=False,
            work_list=None):
    """One exp_02 start under the stubs; work_list replaces exp_02's (a mutant) for this start only."""
    probe, seen = Probe(), []
    qs = e02.index_questions(indexes[0], n)
    e02_stubs(probe, seen, qs[0]["id"], results_dir, scheduler, wait)
    if work_list is not None:
        e02.work_list = work_list
    err = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(e02.run_experiment(indexes, [config], BASE, max_questions=n, sink_root=sink_root,
                                           resume=resume))
    except BaseException as e:      # noqa: BLE001
        err = e
    finally:
        e02_restore()
    return probe, seen, qs, err


def listing(folder: Path) -> dict:
    return {str(f.relative_to(folder)): f.read_bytes() for f in sorted(folder.rglob("*")) if f.is_file()} \
        if folder.exists() else {}


def child(index: str, folder: Path) -> None:
    """One exp_02 process: index's first 5 questions, rlm_10, sinks and results under folder. Its first answer is
    quick; the rest wait for folder/release, so the parent can look at it mid-run."""
    async def wait(item_id):
        if item_id != first:
            t = time.monotonic()
            while not (folder / "release").exists():
                if time.monotonic() - t > 180:
                    raise TimeoutError("no release")
                await asyncio.sleep(0.05)
    first = e02.index_questions(index, 5)[0]["id"]
    global SLOW
    SLOW = FAST
    probe, seen, qs, err = e02_run([index], 5, folder / "sinks", folder / "results", wait=wait)
    if err is not None:
        print(f"CHILD ERROR {type(err).__name__}: {err}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"pid": os.getpid(), "index": index}))


def crash_child(index: str, folder: Path, after: int) -> None:
    """One exp_02 process (index's first 5 questions, rlm_10, sinks and results under folder) that ends by os._exit
    right after its after-th answers.jsonl line is written and fsynced: nothing it would do next happens (its log
    line, the answers in flight, the report), as when the machine stops there."""
    real, n = rc.append, [0]

    def append(record, file="calls.jsonl"):
        line = real(record, file)
        if file == e02.ANSWERS:
            n[0] += 1
            if n[0] == after:
                os._exit(CRASH_RC)
        return line
    rc.append = append
    global SLOW
    SLOW = FAST
    probe, seen, qs, err = e02_run([index], 5, folder / "sinks", folder / "results")
    print(f"CRASH CHILD did not crash: {n[0]} lines, {err!r}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__" and "--child" in sys.argv:
    k = sys.argv.index("--child")
    child(sys.argv[k + 1], Path(sys.argv[k + 2]))
    sys.exit(0)
if __name__ == "__main__" and "--crash" in sys.argv:
    k = sys.argv.index("--crash")
    crash_child(sys.argv[k + 1], Path(sys.argv[k + 2]), int(sys.argv[k + 3]))

# ───────────────────────── 1. pool.rolling ─────────────────────────

async def unit(scheduler, size=2, n=10, slow=0):
    probe, stored = Probe(), []

    async def run(i):
        probe.start(i)
        try:
            await asyncio.sleep(SLOW if i == slow else FAST)
            return f"r{i}"
        finally:
            probe.end(i)

    await scheduler(range(n), size, run, lambda i, r, k: stored.append((i, r, k)))
    return probe, stored


probe, stored = asyncio.run(unit(pool.rolling))
check("1 pool: the items start in the order given", probe.starts == list(range(10)), probe.starts)
check("1 pool: never more than the size (2) in flight, and the pool fills to it", probe.most == 2, probe.most)
check("1 pool: every item passed to done once, with its result",
      sorted((i, r) for i, r, _ in stored) == [(i, f"r{i}") for i in range(10)])
check("1 pool: while the slow item runs, the other slot runs the 9 others (the slow one stored last)",
      slow_held_one_slot([i for i, _, _ in stored], 0), [i for i, _, _ in stored])
check("1 pool: each item's in-flight count at its start is 1 to the size; the first 1, the second 2",
      all(1 <= k <= 2 for _, _, k in stored) and dict((i, k) for i, _, k in stored)[0] == 1
      and dict((i, k) for i, _, k in stored)[1] == 2, [k for _, _, k in stored])
probe6, stored6 = asyncio.run(unit(pool.rolling, size=6, n=20))
check("1 pool of 6 over 20: at most 6 at once and 6 reached, every item once, the slow one last",
      probe6.most == 6 and sorted(i for i, _, _ in stored6) == list(range(20))
      and slow_held_one_slot([i for i, _, _ in stored6], 0), probe6.most)
mprobe, mstored = asyncio.run(unit(fixed_batches))
check("1 mutant (fixed batches): the slow-item test fails (the slow item holds its batch)",
      not slow_held_one_slot([i for i, _, _ in mstored], 0), [i for i, _, _ in mstored])


async def stopping():
    started, stored, cancelled = [], [], []

    async def run(i):
        started.append(i)
        await asyncio.sleep({0: 0.3, 1: 0.05}.get(i, FAST))
        if i == 1:
            raise Stop("refused")
        return i

    err = None
    try:
        await pool.rolling(range(8), 2, run, lambda i, r, k: stored.append((i, type(r).__name__)), stops=(Stop,))
    except Stop as e:
        err = e

    async def run2(i):
        try:
            await asyncio.sleep(0.05 if i == 0 else 5)
        except asyncio.CancelledError:
            cancelled.append(i)
            raise
        return i

    def bad_done(i, r, k):
        raise RuntimeError("store failed")

    err2 = None
    try:
        await pool.rolling(range(4), 2, run2, bad_done)
    except RuntimeError as e:
        err2 = e
    return started, stored, err, cancelled, err2


started, stored, err, cancelled, err2 = asyncio.run(stopping())
check("1 pool stop: nothing starts after the stop; the item in flight ends and is stored; the stop is raised",
      started == [0, 1] and stored == [(1, "Stop"), (0, "int")] and isinstance(err, Stop), f"{started} {stored}")
check("1 pool: an error in done cancels the items still running and is raised",
      cancelled == [1] and isinstance(err2, RuntimeError), f"{cancelled} {err2!r}")
bad = []
for size in (0, -1, 1.5, True, "2"):
    try:
        asyncio.run(pool.rolling([1], size, None, None))
        bad.append(size)
    except ValueError:
        pass
check("1 pool: sizes 0, -1, 1.5, True and '2' refused", not bad, bad)


# ───────────────────────── 2. exp_01 ─────────────────────────

QS = ex.questions()
I20 = e01.DEFAULT_INDEX
saved_e01 = {n: getattr(e01, n) for n in ("_run_config", "find_admin_user_id", "check_index_exists",
                                          "setup_retriever", "ModelRouter", "index_identity", "RUNS_ROOT", "pool")}


def e01_run(config, n, sink_root, scheduler=None, stop_id=None):
    probe, seen = Probe(), []
    e01._run_config = fake_strategy(probe, e01.GenerationResult, seen, QS[0]["id"], stop_id)
    e01.find_admin_user_id = lambda: "u"
    e01.check_index_exists = lambda u, i: True
    e01.setup_retriever = lambda u, i: (None, "coll", "emb")
    e01.ModelRouter = lambda: None
    e01.index_identity = SimpleNamespace(record=lambda *a, **k: None)
    e01.RUNS_ROOT = tmp / "e01_runs_root_unused"
    e01.pool = SimpleNamespace(rolling=scheduler) if scheduler else pool
    err = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(e01.run_experiment([config], BASE, max_questions=n, index_name=I20, draws=(1,),
                                           sink_root=sink_root))
    except BaseException as e:      # noqa: BLE001 (the stop is a check's result)
        err = e
    finally:
        for k, v in saved_e01.items():
            setattr(e01, k, v)
    return probe, seen, lines(sink_root / (e01.config_run_id(config, I20, True)) / e01.ANSWERS), err


for config, size in (("single_pass", 6), ("rlm_10", 2)):
    n = 14
    probe, seen, got, err = e01_run(config, n, tmp / f"e01_{config}")
    wl = e01.work_list([config], QS[:n], (1,), I20, smoke=True, root=tmp / "e01_none")
    rid = e01.config_run_id(config, I20, True)
    check(f"2 exp_01 {config}: the run ends, every key of the work list stored once ({n})",
          err is None and sorted(r["answer_key"] for r in got) == sorted(i["key"] for i in wl), repr(err))
    check(f"2 exp_01 {config}: the strategy starts in work-list order, each answer in its own context "
          f"(run, question, draw 1) with the question's text, config and generator unchanged",
          [s["q"] for s in seen] == [i["q"]["id"] for i in wl]
          and all(s["run_id"] == rid and s["draw"] == 1 and s["question"] == q["question"] and s["config"] == config
                  and s["gen_model"] == e01.GEN_MODEL and s["index"] == I20 for s, q in zip(seen, QS[:n])))
    check(f"2 exp_01 {config}: at most {size} answers in flight, and {size} reached", probe.most == size, probe.most)
    check(f"2 exp_01 {config}: every other answer stored while the slow one ran (it is the last line)",
          slow_held_one_slot([r["question_id"] for r in got], QS[0]["id"]), [r["question_id"] for r in got][-3:])
    check(f"2 exp_01 {config}: each line's pool is size {size} and its in-flight count 1 to {size} (first 1)",
          all(r["pool"]["size"] == size and 1 <= r["pool"]["in_flight_at_start"] <= size for r in got)
          and next(r for r in got if r["question_id"] == QS[0]["id"])["pool"]["in_flight_at_start"] == 1)
    mprobe, mseen, mgot, merr = e01_run(config, n, tmp / f"e01_{config}_mutant", scheduler=fixed_batches)
    strip = lambda rs: sorted((json.dumps({k: v for k, v in r.items() if k not in SCHED}, sort_keys=True)
                               for r in rs))   # noqa: E731
    check(f"2 exp_01 {config}: the fixed-batch mutant stores the same records apart from scheduling "
          f"(pool, pid, ctx_uid, seq), started in the same order",
          merr is None and strip(mgot) == strip(got) and [s["q"] for s in mseen] == [s["q"] for s in seen])
    check(f"2 exp_01 {config}: the fixed-batch mutant fails the slow-answer test",
          not slow_held_one_slot([r["question_id"] for r in mgot], QS[0]["id"]), [r["question_id"] for r in mgot][:3])

# a stop on the second question of an RLM config (pool 2): the first (slow) is in flight and stored, nothing after
probe, seen, got, err = e01_run("rlm_5", 8, tmp / "e01_stop", stop_id=QS[1]["id"])
check("2 exp_01 stop: the stop is raised, nothing starts after it, the answer in flight is stored, the stopped key not",
      isinstance(err, e01.STOPS) and [s["q"] for s in seen] == [QS[0]["id"], QS[1]["id"]]
      and [r["question_id"] for r in got] == [QS[0]["id"]], f"{type(err).__name__}, {[s['q'] for s in seen]}")


# ───────────────────────── 3. exp_02 ─────────────────────────

n = 10
sinks, rdir = tmp / "e02_sinks", tmp / "e02_results"
probe, seen, qs, err = e02_run([IDX], n, sinks, rdir)
rid = e02.run_name("rlm_10", IDX, smoke=True)
got = lines(sinks / rid / e02.ANSWERS)
D = e02.DRAWS
check(f"3 exp_02: the run ends; each answer one line of its run's answers.jsonl, every key once ({n} x draws {D})",
      err is None and len(got) == n * len(D) and sorted(r["answer_key"] for r in got)
      == sorted(ex.answer_key("rlm_10", q["id"], d, index=IDX) for d in D for q in qs)
      and all(r["run_id"] == rid and r["generation"]["answer"] == f"answer to {r['question_id']}" for r in got),
      f"{len(got)} lines, {err!r}")
check("3 exp_02: the strategy starts in work-list order (draw, then question), each in its own context (run, "
      "question, draw) with the question's text",
      [(s["draw"], s["q"]) for s in seen] == [(d, q["id"]) for d in D for q in qs]
      and all(s["run_id"] == rid and s["question"] == q["question"] for s, q in zip(seen, [q for _ in D for q in qs])))
check("3 exp_02: at most 4 answers in flight (the RLM pool), and 4 reached", probe.most == 4, probe.most)
check("3 exp_02: in every draw, every other answer stored while the slow one ran (it is the draw's last line)",
      all(slow_held_one_slot([r["question_id"] for r in got if r["draw"] == d], qs[0]["id"]) for d in D),
      [[r["question_id"] for r in got if r["draw"] == d][-1] for d in D])
check("3 exp_02: each line's pool is size 4 and its in-flight count 1 to 4",
      all(r["pool"]["size"] == 4 and 1 <= r["pool"]["in_flight_at_start"] <= 4 for r in got))
files = sorted(listing(rdir))
latest = json.loads((rdir / f"v4_5_scaling_smoke__{IDX}_latest.json").read_text()) \
    if (rdir / f"v4_5_scaling_smoke__{IDX}_latest.json").exists() else {}
check("3 exp_02: no intermediate file is written; the files are the report v4_5_scaling_smoke__<index>_<ts>.json, "
      "_latest.json and _<ts>.md, and the lock .v4_5_<index>.smoke.lock",
      not any("intermediate" in f for f in files) and len(files) == 4
      and f"v4_5_scaling_smoke__{IDX}_latest.json" in files and f".v4_5_{IDX}.smoke.lock" in files
      and sum(f.startswith(f"v4_5_scaling_smoke__{IDX}_2") for f in files) == 2, files)
strip = lambda rs: sorted(json.dumps({k: v for k, v in r.items() if k not in SCHED}, sort_keys=True)  # noqa: E731
                          for r in rs)
# the row as the old code put it in the report: the dict _row made, which run_context.append returns with these added
as_row = lambda rs: [json.dumps({k: v for k, v in r.items() if k not in e02.SINK_ADDED}) for r in rs]   # noqa: E731
row_keys = list(e02._row(IDX, "rlm_10", qs[0], 1, e02.GenerationResult(
    answer="", latency_s=0.0, llm_calls=0, tokens_used=0, retrieved_passages=0, config="rlm_10",
    gen_model=e02.GEN_MODEL), rid))
check("3 exp_02: the report's rows are the sink's lines without what run_context adds (item_id, arm, run_draw, "
      "ctx_uid, seq, pid), in the sink's order, each with exactly _row's keys in _row's order (the old in-memory row)",
      e02.SINK_ADDED == ("item_id", "arm", "run_draw", "ctx_uid", "seq", "pid")
      and as_row(got) == [json.dumps(r) for r in latest.get("per_question_results", [])]
      and all(list(r) == row_keys for r in latest.get("per_question_results", [])),
      f"{len(latest.get('per_question_results', []))} rows")
no_lock = lambda d: {k: v for k, v in listing(d).items() if not k.startswith(".v4_5_")}   # noqa: E731
before = listing(sinks), no_lock(rdir)
probe2, seen2, _, err2 = e02_run([IDX], n, sinks, rdir)
check("3 exp_02: a second start into the same sinks without --resume is refused on the answers stored there, nothing "
      "started or written (its lock file aside)",
      isinstance(err2, SystemExit) and "already stored" in str(err2) and "--resume" in str(err2) and not seen2
      and (listing(sinks), no_lock(rdir)) == before, str(err2)[:120])
sinks_before = listing(sinks)
(rdir / f"v4_5_scaling_smoke__{IDX}_latest.json").unlink()
probe3, seen3, _, err3 = e02_run([IDX], n, sinks, rdir, resume=True)
latest3 = json.loads((rdir / f"v4_5_scaling_smoke__{IDX}_latest.json").read_text()) \
    if (rdir / f"v4_5_scaling_smoke__{IDX}_latest.json").exists() else {}
check("3 exp_02: a --resume start of the finished run starts nothing, adds no sink line, and writes a report with the "
      "same rows",
      err3 is None and not seen3 and listing(sinks) == sinks_before
      and latest3.get("per_question_results") == latest["per_question_results"], repr(err3))
mprobe, mseen, _, merr = e02_run([IDX], n, tmp / "e02_sinks_mutant", tmp / "e02_results_mutant",
                                 scheduler=fixed_batches)
mgot = lines(tmp / "e02_sinks_mutant" / rid / e02.ANSWERS)
check("3 exp_02: the fixed-batch mutant stores the same records apart from scheduling, and fails the slow-answer test",
      merr is None and strip(mgot) == strip(got)
      and not any(slow_held_one_slot([r["question_id"] for r in mgot if r["draw"] == d], qs[0]["id"]) for d in D),
      repr(merr))


# ───────────────────────── 4. two processes ─────────────────────────

A, B = "exp_v4_s5_n0", "exp_v4_s10_n1"
shared = tmp / "two"
shared.mkdir()


def spawn(index):
    # from the scratch directory, so nothing Mentori writes relative to the working directory lands in the repository
    return subprocess.Popen([sys.executable, "-m", "experiments.runner.check_rolling_pool", "--child", index,
                             str(shared)], cwd=tmp, env={**os.environ, "PYTHONPATH": str(ROOT)},
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


sink_of = {i: shared / "sinks" / e02.run_name("rlm_10", i, smoke=True) / e02.ANSWERS for i in (A, B)}
procs = {i: spawn(i) for i in (A, B)}
t = time.monotonic()
while not all(lines(p) for p in sink_of.values()) and time.monotonic() - t < 300 \
        and all(p.poll() is None for p in procs.values()):
    time.sleep(0.2)
both_mid = all(lines(p) for p in sink_of.values()) and all(p.poll() is None for p in procs.values())
check("4 two processes: both mid-run at once, each with its first answer in its own run's sink",
      both_mid and sink_of[A] != sink_of[B], {i: len(lines(p)) for i, p in sink_of.items()})
mid = {i: lines(p) for i, p in sink_of.items()}
check("4 two processes: each sink holds only its own index's one answer so far",
      all([r["index_name"] for r in mid[i]] == [i] for i in (A, B)), {i: len(mid[i]) for i in mid})
before_dup = listing(shared)
dup = spawn(A)
dup_out, dup_err = dup.communicate(timeout=300)
check("4 a third process on an index another runs is refused (exit 1), naming the holder, and writes nothing",
      dup.returncode == 1 and "runs it already" in dup_err and f"pid {procs[A].pid}" in dup_err
      and listing(shared) == before_dup, (dup.returncode, dup_err.strip().splitlines()[-1:] if dup_err else ""))
(shared / "release").write_text("go")
outs = {i: p.communicate(timeout=300) for i, p in procs.items()}
check("4 two processes: both end with exit 0", all(procs[i].returncode == 0 for i in procs),
      {i: (procs[i].returncode, outs[i][1].strip().splitlines()[-1:]) for i in procs})
names = sorted(listing(shared / "results"))
own = {i: [f for f in names if i in f] for i in (A, B)}
check("4 two processes: every report and lock file is named by one index, none by both, 4 each (2 reports .json "
      "with _latest, 1 .md, 1 lock); no intermediate file",
      sorted(own[A] + own[B]) == names and not set(own[A]) & set(own[B]) and all(len(own[i]) == 4 for i in own)
      and not any("intermediate" in f for f in names), names)
lat = {i: json.loads((shared / "results" / f"v4_5_scaling_smoke__{i}_latest.json").read_text()) for i in (A, B)}
N4 = 5 * len(e02.DRAWS)
check(f"4 two processes: each _latest.json holds its own index's {N4} answers (5 questions x draws {e02.DRAWS}) only",
      all(sorted({r["index_name"] for r in lat[i]["per_question_results"]}) == [i]
          and len(lat[i]["per_question_results"]) == N4 for i in lat),
      {i: len(lat[i]["per_question_results"]) for i in lat})
sink_lines = {i: lines(shared / "sinks" / e02.run_name("rlm_10", i, smoke=True) / e02.ANSWERS) for i in (A, B)}
check(f"4 two processes: each index's sink holds its {N4} answers, every line written by its own process's pid",
      all(len(sink_lines[i]) == N4 and {r["pid"] for r in sink_lines[i]} == {procs[i].pid}
          and {r["index_name"] for r in sink_lines[i]} == {i} for i in sink_lines),
      {i: sorted({r["pid"] for r in sink_lines[i]}) for i in sink_lines})
old_names = lambda i: ("v4_5_smoke_intermediate.json", "v4_5_scaling_smoke")   # noqa: E731  (before B9 F5)
new_names = lambda i: (e02.report_prefix([i], True),)   # noqa: E731
check("4 the old names would collide (one intermediate file and one report prefix for both), the new prefix does not",
      old_names(A) == old_names(B) and not set(new_names(A)) & set(new_names(B)), new_names(A))
check("4 the tag is the sorted indexes, each once, joined by '+'",
      e02.process_tag([B, A, B]) == "+".join(sorted([A, B])), e02.process_tag([B, A, B]))
try:
    e02.process_tag(["../x"])
    check("4 process_tag refuses '../x'", False)
except SystemExit:
    check("4 process_tag refuses '../x'", True)


# ───────────────────────── 5. a crash after a sink line ─────────────────────────

AFTER = 7               # draw 1's 5 answers and 2 of draw 2's: the crash falls inside a draw, a later draw untouched
N5 = 5
rid5 = e02.run_name("rlm_10", IDX, smoke=True)
keys5 = sorted(ex.answer_key("rlm_10", q["id"], d, index=IDX) for d in e02.DRAWS for q in e02.index_questions(IDX, N5))


def crash(folder: Path):
    """Runs a --crash child into folder; returns its exit code and stderr."""
    p = subprocess.run([sys.executable, "-m", "experiments.runner.check_rolling_pool", "--crash", IDX, str(folder),
                        str(AFTER)], cwd=tmp, env={**os.environ, "PYTHONPATH": str(ROOT)},
                       capture_output=True, text=True, timeout=300)
    return p.returncode, p.stderr


def resumed_once(err, got) -> bool:
    """The resume test: the start ends, and the sink holds every key of the work list once."""
    return err is None and sorted(r["answer_key"] for r in got) == keys5


cdir = tmp / "crash"
rc5, err5 = crash(cdir)
sink5 = cdir / "sinks" / rid5 / e02.ANSWERS
crashed = lines(sink5)
check(f"5 crash: the child ends by os._exit right after its {AFTER}th sink line: {AFTER} lines, each key once, no "
      f"report written (its lock file only)",
      rc5 == CRASH_RC and len(crashed) == AFTER and len({r["answer_key"] for r in crashed}) == AFTER
      and sorted(listing(cdir / "results")) == [f".v4_5_{IDX}.smoke.lock"],
      (rc5, len(crashed), err5.strip().splitlines()[-1:] if err5 else ""))
head = sink5.read_bytes() if sink5.exists() else b""
before5 = listing(cdir / "sinks"), no_lock(cdir / "results")
_, seen5a, _, err5a = e02_run([IDX], N5, cdir / "sinks", cdir / "results")
check("5 crash: a start without --resume is refused on the stored answers, nothing started or written",
      isinstance(err5a, SystemExit) and "already stored" in str(err5a) and not seen5a
      and (listing(cdir / "sinks"), no_lock(cdir / "results")) == before5, str(err5a)[:120])


def old_resume(intermediate: Path):
    """The mutant: the old resume logic. Done = the intermediate file's completed keys; a key to run that its sink
    stores is the clash, refused (SystemExit), nothing run."""
    def work_list(indexes, configs, max_questions, root):
        done = set(json.loads(intermediate.read_text())["completed_keys"])
        work, clash = saved_e02["work_list"](indexes, configs, max_questions, root), []
        for w in work:
            keys = {ex.answer_key(w["config"], q["id"], w["draw"], index=w["index_name"]): q for q in w["questions"]}
            clash += [k for k in keys if k not in done and k in w["stored"]]
            w["pending"] = [q for k, q in keys.items() if k not in done]
            w["stored"] = {k: r for k, r in w["stored"].items() if k in done}
        if clash:
            raise SystemExit(f"{len(clash)} answers to run are already stored in their run's {e02.ANSWERS} and not in "
                             f"{intermediate}; nothing run")
        return work
    return work_list


def blind_resume(indexes, configs, max_questions, root):
    """The second mutant: a resume that ignores the sink (nothing stored, every key pending)."""
    work = saved_e02["work_list"](indexes, configs, max_questions, root)
    for w in work:
        w["stored"], w["pending"] = {}, list(w["questions"])
    return work


# what the old code left at this crash: its intermediate file was rewritten after each sink line, so it holds the
# answers before the crashed one (the 7th line was written, its rewrite was not)
old_inter = tmp / "crash_old_intermediate.json"
old_inter.write_text(json.dumps({"results": crashed[:-1], "completed_keys": [r["answer_key"] for r in crashed[:-1]]}))
_, mseen5, _, merr5 = e02_run([IDX], N5, cdir / "sinks", cdir / "results", resume=True,
                              work_list=old_resume(old_inter))
mgot5 = lines(sink5)
check("5 crash, mutant with the old resume logic: refused on the crashed key, nothing started or written, so it fails "
      "the resume test (and would on every later --resume)",
      not resumed_once(merr5, mgot5) and isinstance(merr5, SystemExit) and "1 answers to run are already stored"
      in str(merr5) and not mseen5 and (listing(cdir / "sinks"), no_lock(cdir / "results")) == before5,
      str(merr5)[:120])

_, seen5, _, err5r = e02_run([IDX], N5, cdir / "sinks", cdir / "results", resume=True)
got5 = lines(sink5)
check(f"5 crash, --resume: the run ends with every key of the work list ({len(keys5)}) stored once, no refusal",
      resumed_once(err5r, got5), f"{len(got5)} lines, {len({r['answer_key'] for r in got5})} keys, {err5r!r}")
check(f"5 crash, --resume: the {AFTER} lines before the crash unchanged, and only the keys the sink lacked started",
      sink5.read_bytes().startswith(head)
      and sorted(ex.answer_key("rlm_10", s["q"], s["draw"], index=IDX) for s in seen5)
      == sorted(set(keys5) - {r["answer_key"] for r in crashed}), f"{len(seen5)} started")
lat5 = cdir / "results" / f"v4_5_scaling_smoke__{IDX}_latest.json"
rows5 = json.loads(lat5.read_text())["per_question_results"] if lat5.exists() else []
check("5 crash, --resume: the report holds every key once, its rows the sink's lines in order (without what "
      "run_context adds)",
      as_row(got5) == [json.dumps(r) for r in rows5] and sorted(r["answer_key"] for r in rows5) == keys5,
      f"{len(rows5)} rows")

bdir = tmp / "crash_blind"
brc, berr = crash(bdir)
_, bseen, _, berr5 = e02_run([IDX], N5, bdir / "sinks", bdir / "results", resume=True, work_list=blind_resume)
bgot = lines(bdir / "sinks" / rid5 / e02.ANSWERS)
check("5 crash, mutant that ignores the sink on resume: the keys before the crash are stored a second time, so it "
      "fails the resume test",
      brc == CRASH_RC and not resumed_once(berr5, bgot)
      and len(bgot) - len({r["answer_key"] for r in bgot}) == AFTER, f"{len(bgot)} lines, {berr5!r}")

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
