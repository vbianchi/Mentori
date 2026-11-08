"""Checks for experiments/runner/run_context.py; offline, no model call.

    uv run --no-sync python -m experiments.runner.check_run_context

1. The context is visible inside asyncio.to_thread and asyncio.create_task, and not after the with-block;
   current() raises outside a run.
2. check_model refuses a model the run does not list and a listed model in another role.
3. Passages set in a run are read back, are None in a new run, and do not leak out of a create_task.
4. append under contention: 4 processes write 200 lines each into one file (each started from a sidecar the
   parent dumped), and 4 threads in this process write 200 each through one shared context. Every line is
   valid JSON, and seq runs 1..200 in each process, 1..800 across the threads. append waits while another
   holder has the file's flock (the line count alone passes without the lock on this Mac).
5. The sidecar round-trips every field, and a task_id with a path in it is refused.
6. The review fixes (15 October): a judge record's own draw=None stands beside run_draw; two loads of one sidecar
   in one process get different ctx_uids; a relative sink is resolved, an empty one refused; a refused or non-JSON
   record takes no seq; NaN is refused; a lone surrogate is written; bad draws and roles are refused at
   construction; concurrent dumps of one task_id all succeed; a set_passages inside to_thread stays there.
7. Mentori's fields (step 2 review, 15 October): agent_roles and tools round-trip through the sidecar; agent_roles
   is validated (strings), and a model it names must be allowed as a generator; agent_model(role) returns the
   role's entry and refuses a missing role (no 'default' fallback) and a call outside a run; the run-level context
   (item_id None) dumps only as run.json and an item context never does; a record appended in it carries
   item_id None; a sidecar without agent_roles or tools is refused.
"""

import asyncio
import contextvars
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import threading
from collections import defaultdict
from pathlib import Path

from experiments.runner import run_context as rc
from experiments.runner.lock import LockError

N_PROC, N_LINES = 4, 200


def worker(path: str, n: int) -> None:
    with rc.run(rc.load(Path(path))):
        for i in range(n):
            # longer than PIPE_BUF, so POSIX does not promise the write is atomic (on this Mac it stayed whole
            # without the lock; see the held-lock check)
            rc.append({"i": i, "text": "x" * 4000})


if len(sys.argv) == 4 and sys.argv[1] == "--worker":
    worker(sys.argv[2], int(sys.argv[3]))
    sys.exit(0)

ROOT = Path(__file__).resolve().parents[2]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return str(e) or type(e).__name__
    return None


tmp = Path(tempfile.mkdtemp(prefix="check_run_context_")).resolve()   # /var is /private/var on a Mac; sinks are resolved


def make(item="Q001", sink=None, **kw):
    return rc.RunContext(run_id="check-run", arm="single_pass", item_id=item, draw=2, thinking="off",
                         base_url="http://10.15.212.253:11441", sink=sink or tmp / "sink",
                         allowed={"gpt-oss:20b": "generator", "devstral-small-2:24b": ["judge", "scorer"]}, **kw)


# 1. visibility
check("current() raises outside a run", raises(rc.RunContextError, rc.current))
ctx = make()


async def inside():
    in_thread = await asyncio.to_thread(lambda: rc.current().item_id)

    async def task_body():
        await asyncio.sleep(0)
        return rc.current().item_id

    return in_thread, await asyncio.create_task(task_body())


with rc.run(ctx):
    seen = asyncio.run(inside())
check("visible inside asyncio.to_thread", seen[0] == "Q001", seen[0])
check("visible inside asyncio.create_task", seen[1] == "Q001", seen[1])
check("not visible after the with-block", raises(rc.RunContextError, rc.current))


async def two_items():
    async def one(item):
        with rc.run(make(item)):
            await asyncio.sleep(0.01)
            return await asyncio.to_thread(lambda: rc.current().item_id)
    return await asyncio.gather(one("Q1"), one("Q2"))


check("two concurrent tasks each see their own run", asyncio.run(two_items()) == ["Q1", "Q2"])
check("a thread started outside a run sees none",
      raises(rc.RunContextError, lambda: asyncio.run(asyncio.to_thread(rc.current))))
check("run() refuses something that is not a RunContext", raises(rc.RunContextError, lambda: rc.run({}).__enter__()))
check("a context with no allowed models is refused", raises(rc.RunContextError, lambda: rc.RunContext(
      "r", "a", "i", 1, None, "http://x", tmp, {})))
check("a context with an unknown role is refused", raises(LockError, lambda: rc.RunContext(
      "r", "a", "i", 1, None, "http://x", tmp, {"gemma3:27b": "reader"})))

# 2. check_model
with rc.run(ctx):
    check("check_model accepts a listed model in its role", raises(LockError, lambda: rc.check_model("gpt-oss:20b", "generator")) is None)
    check("check_model accepts a model listed with two roles, in each",
          raises(LockError, lambda: rc.check_model("devstral-small-2:24b", "judge")) is None
          and raises(LockError, lambda: rc.check_model("devstral-small-2:24b", "scorer")) is None)
    e = raises(LockError, lambda: rc.check_model("qwen3-coder:latest", "generator"))
    check("check_model refuses an unlisted model with LockError", e, e)
    e = raises(LockError, lambda: rc.check_model("gpt-oss:20b", "judge"))
    check("check_model refuses a listed model in the wrong role", e, e)
check("check_model outside a run raises", raises(rc.RunContextError, lambda: rc.check_model("gpt-oss:20b", "generator")))

# 3. passages
with rc.run(ctx):
    check("passages() is None before set_passages", rc.passages() is None)
    rc.set_passages(["c1", "c2"])
    check("passages() returns what set_passages gave", rc.passages() == ["c1", "c2"])

    async def child():
        rc.set_passages(["other"])
        return await asyncio.to_thread(rc.passages)

    async def parent():
        got = await asyncio.create_task(child())
        return got, rc.passages()

    got, after = asyncio.run(parent())
    check("a task's set_passages is seen in its own to_thread", got == ["other"], got)
    check("a task's set_passages does not change the parent's", after == ["c1", "c2"], after)
with rc.run(make("Q002")):
    check("a new run starts with no passages", rc.passages() is None)
check("passages() outside a run raises", raises(rc.RunContextError, rc.passages))

# 4. append
sink = tmp / "append"
base = make(sink=sink)
with rc.run(base):
    side = rc.dump("append-task")
    first = rc.append({"note": "parent"}, file="parent.jsonl")
    check("append adds run_id, item_id, arm, run_draw, ctx_uid, seq and pid", all(k in first for k in rc.ADDED)
          and first["seq"] == 1 and first["run_draw"] == 2 and first["ctx_uid"] == base.ctx_uid,
          json.dumps({k: first[k] for k in rc.ADDED}))
    check("append refuses a record whose run_id differs",
          raises(rc.RunContextError, lambda: rc.append({"run_id": "another"}, file="parent.jsonl")))
    check("append refuses a file name with a path", raises(rc.RunContextError, lambda: rc.append({}, file="../x.jsonl")))
check("append outside a run raises", raises(rc.RunContextError, lambda: rc.append({})))

procs = [subprocess.Popen([sys.executable, "-m", "experiments.runner.check_run_context", "--worker", str(side),
                           str(N_LINES)], cwd=ROOT) for _ in range(N_PROC)]
codes = [p.wait() for p in procs]
check(f"{N_PROC} worker processes exit 0", codes == [0] * N_PROC, codes)
lines = (sink / "calls.jsonl").read_text(encoding="utf-8").splitlines()
bad, by_pid = 0, defaultdict(list)
for ln in lines:
    try:
        r = json.loads(ln)
        by_pid[r["pid"]].append(r["seq"])
    except (json.JSONDecodeError, KeyError):
        bad += 1
check(f"{N_PROC * N_LINES} lines, every one valid JSON", len(lines) == N_PROC * N_LINES and bad == 0,
      f"{len(lines)} lines, {bad} invalid")
check(f"seq runs 1..{N_LINES} in each of the {N_PROC} processes", len(by_pid) == N_PROC and all(
      sorted(s) == list(range(1, N_LINES + 1)) for s in by_pid.values()), {p: len(s) for p, s in by_pid.items()})
check("every worker line carries the dumped run_id, item_id, arm and run_draw", all(
      (r["run_id"], r["item_id"], r["arm"], r["run_draw"]) == ("check-run", "Q001", "single_pass", 2)
      for r in map(json.loads, lines)))
keys = [(r["ctx_uid"], r["seq"]) for r in map(json.loads, lines)]
check(f"(ctx_uid, seq) is unique over the {len(keys)} worker lines, {N_PROC} ctx_uids",
      len(set(keys)) == len(keys) and len({k[0] for k in keys}) == N_PROC)

# The 800-line check alone cannot fail on this Mac: with flock a no-op, 4 processes x 200 lines of 200,000
# characters still gave 800 valid lines (O_APPEND writes did not interleave). So check that append waits.
held = sink / "held.jsonl"
held.touch()
with rc.run(base), open(held, "a") as h:
    fcntl.flock(h, fcntl.LOCK_EX)
    t = threading.Thread(target=contextvars.copy_context().run, args=(rc.append, {"waited": True}, "held.jsonl"))
    t.start()
    t.join(0.5)
    blocked = t.is_alive() and held.read_text() == ""
    fcntl.flock(h, fcntl.LOCK_UN)
    t.join(5)
check("append waits while another holder has the file's lock, then writes",
      blocked and not t.is_alive() and json.loads(held.read_text())["waited"] is True)

tctx = make(sink=tmp / "threads")


def thread_writer():
    for i in range(N_LINES):
        rc.append({"i": i, "text": "y" * 4000})


with rc.run(tctx):
    threads = [threading.Thread(target=contextvars.copy_context().run, args=(thread_writer,)) for _ in range(N_PROC)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
tl = [json.loads(x) for x in (tmp / "threads" / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
check(f"{N_PROC} threads sharing one context: {N_PROC * N_LINES} valid lines, seq unique 1..{N_PROC * N_LINES}",
      sorted(r["seq"] for r in tl) == list(range(1, N_PROC * N_LINES + 1)), f"{len(tl)} lines")

# 5. sidecar
with rc.run(base):
    back = rc.load(side)
check("sidecar at <sink>/ctx/<task_id>.json", side == sink / "ctx" / "append-task.json", str(side.relative_to(tmp)))
check("sidecar round-trips every field", back.to_dict() == {**base.to_dict(), "seq": 0}, json.dumps(back.to_dict()))
check("a loaded context starts its own seq at 0", back.seq == 0 and back is not base)
check("dump refuses a task_id with a path in it", raises(rc.RunContextError, lambda: rc.sidecar("../evil", sink)))
check("dump outside a run raises", raises(rc.RunContextError, lambda: rc.dump("t")))
(sink / "ctx" / "broken.json").write_text('{"run_id": "r"}')
check("load refuses a sidecar missing fields", raises(rc.RunContextError, lambda: rc.load(sink / "ctx" / "broken.json")))

# 6. review fixes
fx = make(sink=tmp / "fixes")
with rc.run(fx):
    j = rc.append({"model": "devstral-small-2:24b", "role": "judge", "draw": None})
    check("a judge record's draw=None is kept, with the run's draw as run_draw", j["draw"] is None
          and j["run_draw"] == 2, json.dumps({k: j[k] for k in ("draw", "run_draw")}))
    check("a record carrying its own seq is refused", raises(rc.RunContextError, lambda: rc.append({"seq": 9})))
    check("a record carrying another ctx_uid is refused", raises(rc.RunContextError, lambda: rc.append({"ctx_uid": "x"})))
    e = raises(rc.RunContextError, lambda: rc.append({"score": float("nan")}))
    check("a NaN is refused, never written as a value", e, e)
    check("an infinity is refused", raises(rc.RunContextError, lambda: rc.append({"score": float("inf")})))
    check("an object that is not JSON is refused", raises(rc.RunContextError, lambda: rc.append({"o": object()})))
    check("a clashing record is refused", raises(rc.RunContextError, lambda: rc.append({"arm": "other"})))
    s2 = rc.append({"text": "a\ud800b"})
    check("refused records take no seq: the next append has seq 2", s2["seq"] == 2, s2["seq"])
    fl = [json.loads(x) for x in (tmp / "fixes" / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    check("a lone surrogate is written and read back whole; 2 lines, seqs 1, 2",
          [r["seq"] for r in fl] == [1, 2] and fl[1]["text"] == "a\ud800b", [r["seq"] for r in fl])
    two = rc.dump("twice")
    with rc.run(rc.load(two)):
        a1 = rc.append({"n": 1}, file="twice.jsonl")
    with rc.run(rc.load(two)):
        a2 = rc.append({"n": 2}, file="twice.jsonl")
    check("two loads of one sidecar in one process: same pid and seq, different ctx_uid",
          (a1["pid"], a1["seq"]) == (a2["pid"], a2["seq"]) and a1["ctx_uid"] != a2["ctx_uid"],
          [(a1["pid"], a1["seq"], a1["ctx_uid"][:8]), (a2["pid"], a2["seq"], a2["ctx_uid"][:8])])
    errs = []

    def dumper():
        try:
            rc.dump("same-task")
        except Exception as ex:
            errs.append(repr(ex))

    ts = [threading.Thread(target=contextvars.copy_context().run, args=(dumper,)) for _ in range(16)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    left = [x.name for x in (tmp / "fixes" / "ctx").iterdir() if x.name.endswith(".tmp")]
    check("16 threads dumping one task_id: no error, a whole sidecar, no temp file left",
          not errs and not left and rc.load(tmp / "fixes" / "ctx" / "same-task.json").run_id == "check-run",
          f"errors {errs}, temp files {left}")

    async def hop():
        await asyncio.to_thread(rc.set_passages, ["hop2"])
        return rc.passages()

    rc.set_passages(["hop1"])
    got = asyncio.run(hop())
    check("a set_passages inside to_thread is not seen by the caller (documented)", got == ["hop1"], got)

here = os.getcwd()
os.chdir(tmp)
try:
    rel = make(sink=Path("rel/sink"))
    with rc.run(rel):
        rd = json.loads(rc.dump("rel").read_text(encoding="utf-8"))
finally:
    os.chdir(here)
check("a relative sink is resolved, in the context and in the sidecar", rel.sink.is_absolute()
      and rel.sink == (tmp / "rel" / "sink").resolve() and rd["sink"] == str(rel.sink), rd["sink"])
for bad_sink in ("", "."):
    check(f"sink {bad_sink!r} is refused", raises(rc.RunContextError, lambda: make(sink=bad_sink) if bad_sink else
          rc.RunContext("r", "a", "i", 1, None, "http://x", "", {"m": "judge"})))
for d in (0, -3):
    check(f"draw {d} is refused", raises(rc.RunContextError, lambda: rc.RunContext(
          "r", "a", "i", d, None, "http://x", tmp, {"m": "judge"})))
check("draw None with a generator allowed is refused", raises(rc.RunContextError, lambda: rc.RunContext(
      "r", "a", "i", None, None, "http://x", tmp, {"g": "generator", "j": "judge"})))
check("draw None with instruments only is accepted", raises(Exception, lambda: rc.RunContext(
      "r", "a", "i", None, None, "http://x", tmp, {"devstral-small-2:24b": ["judge", "scorer"]})) is None)
for bad in (None, [], [1]):
    check(f"allowed role {bad!r} is refused with LockError", raises(LockError, lambda: rc.RunContext(
          "r", "a", "i", 1, None, "http://x", tmp, {"m": bad})))

# 7. Mentori's fields
ROLES_OK = {"vision": "ollama::gpt-oss:20b[think:high]", "handyman": "gpt-oss:20b", "default": "ollama::gpt-oss:20b"}
TOOLS = ["read_image", "list_files"]
mx = make(sink=tmp / "mentori", agent_roles=dict(ROLES_OK), tools=list(TOOLS))
with rc.run(mx):
    mside = rc.dump("item-task")
    mback = rc.load(mside)
    check("agent_roles and tools round-trip through the sidecar", mback.agent_roles == ROLES_OK
          and mback.tools == TOOLS and mback.to_dict() == {**mx.to_dict(), "seq": 0}, json.dumps(mback.to_dict())[:120])
    check("agent_model returns the role's entry as written (suffix kept for the adapter's record)",
          rc.agent_model("vision") == ROLES_OK["vision"] and rc.agent_model("handyman") == "gpt-oss:20b")
    e = raises(LockError, lambda: rc.agent_model("editor"))
    check("agent_model refuses a role the run does not name, with LockError naming it, despite a 'default'",
          e and "'editor'" in e, e)
    check("dump refuses an item context as run.json", raises(rc.RunContextError, lambda: rc.dump(rc.RUN_TASK_ID)))
    check("dump may rewrite a sidecar with the same context", raises(Exception, lambda: rc.dump("item-task")) is None)
before = mside.read_text(encoding="utf-8")
for label, other in (("another item", make(item="Q002", sink=tmp / "mentori", agent_roles=dict(ROLES_OK))),
                     ("another draw", rc.RunContext("check-run", "single_pass", "Q001", 3, "off", "http://x",
                                                    tmp / "mentori", {"gpt-oss:20b": "generator"})),
                     ("another run", rc.RunContext("other-run", "single_pass", "Q001", 2, "off", "http://x",
                                                   tmp / "mentori", {"gpt-oss:20b": "generator"}))):
    with rc.run(other):
        e = raises(rc.RunContextError, lambda: rc.dump("item-task"))
    check(f"dump refuses to overwrite an item's sidecar with {label}'s context, leaving it as it was",
          e and "item-task" in e and mside.read_text(encoding="utf-8") == before, e)
check("agent_model outside a run raises RunContextError", raises(rc.RunContextError, lambda: rc.agent_model("vision")))
with rc.run(make(sink=tmp / "mentori")):
    check("a context with no agent_roles names no role", raises(LockError, lambda: rc.agent_model("vision")))
check("model_name strips the provider and the [think:x] suffix", [rc.model_name(x) for x in (
      "ollama::gpt-oss:20b[think:high]", "gemini::gemini-3-flash-preview", "qwen3-coder:30b")]
      == ["gpt-oss:20b", "gemini-3-flash-preview", "qwen3-coder:30b"])
e = raises(LockError, lambda: make(agent_roles={"coder": "ollama::qwen3-coder:30b"}))
check("agent_roles naming a model not in allowed is refused with LockError", e and "qwen3-coder:30b" in e, e)
e = raises(LockError, lambda: make(agent_roles={"editor": "ollama::devstral-small-2:24b"}))
check("agent_roles naming a model allowed only as judge/scorer is refused", e and "generator" in e, e)
for bad in ({"vision": 3}, {"": "gpt-oss:20b"}, {"vision": ""}, ["gpt-oss:20b"]):
    check(f"agent_roles {bad!r} is refused", raises(rc.RunContextError, lambda: make(agent_roles=bad)))
for bad in ("read_image", ["a", "a"], ["a", ""], [1]):
    check(f"tools {bad!r} is refused", raises(rc.RunContextError, lambda: make(tools=bad)))
for bad in ("", 7):
    check(f"item_id {bad!r} is refused", raises(rc.RunContextError, lambda: make(item=bad)))
runlvl = make(item=None, sink=tmp / "mentori", agent_roles=dict(ROLES_OK), tools=list(TOOLS))
with rc.run(runlvl):
    rpath = rc.dump(rc.RUN_TASK_ID)
    check("the run-level context dumps as <sink>/ctx/run.json", rpath == tmp / "mentori" / "ctx" / "run.json")
    check("the run-level context refuses any other sidecar name", raises(rc.RunContextError, lambda: rc.dump("t1")))
    rl = rc.append({"note": "run-level"}, file="runlevel.jsonl")
    check("a record in the run-level context carries item_id None", rl["item_id"] is None and rl["seq"] == 1)
check("the run-level sidecar loads back with item_id None", rc.load(rpath).item_id is None
      and rc.load(rpath).to_dict() == {**runlvl.to_dict(), "seq": 0})
d = json.loads(mside.read_text(encoding="utf-8"))
for k in ("agent_roles", "tools"):
    (tmp / "mentori" / "ctx" / f"no-{k}.json").write_text(json.dumps({x: v for x, v in d.items() if x != k}))
    check(f"load refuses a sidecar with no {k}", raises(rc.RunContextError, lambda: rc.load(
          tmp / "mentori" / "ctx" / f"no-{k}.json")))

# D158 (2): servers, a model tag -> its own Ollama server
plain = make(sink=tmp / "srv")
check("servers None: to_dict has no servers key (sidecars as before) and every tag goes to base_url",
      "servers" not in plain.to_dict() and plain.server_for("gpt-oss:20b") == plain.base_url
      and plain.server_for("devstral-small-2:24b") == plain.base_url)
srv = make(sink=tmp / "srv", servers={"gpt-oss:20b": "http://127.0.0.1:11460"})
check("servers names a tag's server; any other tag goes to base_url",
      srv.server_for("gpt-oss:20b") == "http://127.0.0.1:11460"
      and srv.server_for("devstral-small-2:24b") == srv.base_url and srv.to_dict()["servers"] == srv.servers)
with rc.run(srv):
    spath = rc.dump("srv-task")
check("a sidecar with servers loads back with them", rc.load(spath).to_dict() == {**srv.to_dict(), "seq": 0}
      and rc.load(spath).server_for("gpt-oss:20b") == "http://127.0.0.1:11460")
for bad in ({}, {"qwen3-coder:30b": "http://h:1"}, {"gpt-oss:20b": "h:1"}, {"gpt-oss:20b": ""}, {"gpt-oss:20b": 1},
            ["gpt-oss:20b"]):
    check(f"servers {bad!r} is refused", raises(rc.RunContextError, lambda: make(servers=bad)))

print(f"{sum(results)} of {len(results)} checks pass; scratch {tmp}")
sys.exit(0 if all(results) else 1)
