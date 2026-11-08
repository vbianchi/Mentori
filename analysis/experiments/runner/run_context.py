"""The run context: who a model call belongs to, read by the adapter without being passed through every call.

    from experiments.runner import run_context as rc
    ctx = rc.RunContext(run_id="exp03-r1", arm="orchestrator", item_id="Q017", draw=1, thinking=None,
                        base_url="http://10.15.212.253:11441", sink=Path("runs/exp03-r1"),
                        allowed={"gpt-oss:20b": "generator", "devstral-small-2:24b": "judge"})
    with rc.run(ctx):
        rc.current()                          # the context; raises RunContextError outside a run
        rc.check_model("gpt-oss:20b", "generator")   # LockError unless allowed names that tag with that role
        rc.set_passages(["uid1", "uid2"])     # the passage ids the strategy is about to send
        rc.passages()                         # read back by the adapter for the record's passages field
        rc.append({"status": "ok", ...})      # one JSON line in <sink>/calls.jsonl, with run_id, item_id, arm,
                                              # run_draw, ctx_uid, seq and pid added, under an exclusive file lock
        rc.agent_model("vision")              # agent_roles["vision"]; LockError when the run names none
        p = rc.dump("task-123")               # <sink>/ctx/task-123.json, for the tool-server process
    # in the tool server: with rc.run(rc.load(p)): ...

The context lives in a contextvars.ContextVar, so asyncio.to_thread and asyncio.create_task see the context of
the code that started them. There is no default context: current() outside a run raises. seq counts the appends
made through one context object, starting at 1. Every RunContext, including each one load() builds, gets its own
ctx_uid, so (ctx_uid, seq) names one record even when the tool server loads the same sidecar once per tool call.
The run's draw is written as run_draw; a record's own draw (the call's seed, None for a judge) is left as it is.
allowed maps a tag to one role, or to a list of roles where one model serves two (devstral as judge and scorer).
The sink is stored resolved, so a tool server with another working directory writes to the same files.

Mentori's fields: agent_roles maps a Mentori agent role (vision, transcriber, handyman, coder, editor, ...) to the
Mentori model identifier that role runs ('ollama::qwen3-coder:30b', 'gemini::gemini-3-flash-preview'); every model it
names must be allowed as a generator (Mentori's components run as generators, D66). agent_model(role) is the one
lookup every tool uses: the role's entry, with no 'default' fallback and no database read, so the experiment writes
every role it uses explicitly. tools is the list of tool names the run enables in the tool server; None means every
tool the server discovers (see backend/tool_server.py).

servers (D158 (2), exp_01's local generator) maps a model tag to the Ollama server its calls go to; a tag it does
not name goes to base_url. None (the default, every run before D158) sends every Ollama call to base_url, and leaves
to_dict() as it was (the key is written only when servers is given), so no sidecar written before changes. Each tag
must be in allowed and each server an http(s) URL. server_for(tag) is the one lookup the adapter uses.

A run-level context has item_id None: the tool server runs the tools that take no task_id under it, and the
experiment dumps it as the sidecar <sink>/ctx/run.json (dump(RUN_TASK_ID)). dump refuses to write an item context
there and a run-level context anywhere else.

Passages follow contextvars: a set_passages() inside asyncio.to_thread, asyncio.gather or create_task is seen
there and in what it starts, never by the caller. Call set_passages() in the code that makes the model call.

A call gate (D114 Q29 O2) is an object with before(tag, role) and after(line, file), set for a block with gate(g) and
seen, as the context is, in asyncio.to_thread and in a task created inside the block, also once the block has ended.
check_model() calls g.before(tag, role) after its own checks: the adapter calls check_model() before anything is sent,
so an exception there refuses the call with nothing sent and no record written. append() calls g.after(line, file)
once the line is written, with the line as a dict. With no gate set (every run but exp_05 --length-stop stop's
coder_v2 attempts) neither is called and nothing changes. gate_in(context) is the gate a task's context holds.
"""

from __future__ import annotations

import contextvars
import fcntl
import json
import os
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from experiments.runner.lock import LockError

ROLES = ("generator", "judge", "scorer")       # the roles lock.ollama accepts
RUN_TASK_ID = "run"                            # <sink>/ctx/run.json holds the run-level context (item_id None)
ADDED = ("run_id", "item_id", "arm", "run_draw", "ctx_uid", "seq", "pid")
SIDECAR_IDENTITY = ("run_id", "item_id", "arm", "draw", "sink")   # dump() refuses to overwrite a sidecar differing in one


class RunContextError(Exception):
    pass


@dataclass
class RunContext:
    run_id: str
    arm: str
    item_id: str | None              # None only in the run-level context
    draw: int | None                 # 1, 2, 3 (D49); None only when no allowed model is a generator
    thinking: bool | str | None      # the row's thinking factor; None = the role's rule in the lock
    base_url: str                    # the Ollama server
    sink: Path                       # the directory every record of this run goes to
    allowed: dict                    # model tag -> role, or tag -> list of roles
    agent_roles: dict = field(default_factory=dict)   # Mentori agent role -> Mentori model identifier
    tools: list | None = None        # the tool names the run enables; None = every tool the tool server has
    servers: dict | None = None      # D158 (2): model tag -> its Ollama server; a tag not named goes to base_url
    seq: int = 0                     # the last seq issued by append(); 0 = none yet
    ctx_uid: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)   # new on every construction
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def __post_init__(self):
        for name in ("run_id", "arm", "base_url"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise RunContextError(f"{name} must be a non-empty string, got {getattr(self, name)!r}")
        if self.item_id is not None and (not isinstance(self.item_id, str) or not self.item_id):
            raise RunContextError(f"item_id must be a non-empty string, or None for the run-level context, "
                                  f"got {self.item_id!r}")
        if self.draw is not None and (isinstance(self.draw, bool) or not isinstance(self.draw, int) or self.draw < 1):
            raise RunContextError(f"draw must be an int from 1 or None, got {self.draw!r}")
        if self.sink is None or str(self.sink) == "" or Path(self.sink) == Path("."):
            raise RunContextError(f"sink must name a directory, got {self.sink!r}")
        self.sink = Path(self.sink).resolve()
        if not isinstance(self.allowed, dict) or not self.allowed:
            raise RunContextError("allowed must name at least one model")
        for tag, roles in self.allowed.items():
            for role in _roles(roles, tag):
                if role not in ROLES:
                    raise LockError(f"{tag}: unknown role {role!r} in allowed")
        if self.draw is None and any("generator" in _roles(r) for r in self.allowed.values()):
            raise RunContextError("draw is None, but allowed names a generator, whose seed is its draw")
        if not isinstance(self.agent_roles, dict):
            raise RunContextError(f"agent_roles must be a dict of role -> model identifier, got {self.agent_roles!r}")
        for role, ident in self.agent_roles.items():
            if not isinstance(role, str) or not role or not isinstance(ident, str) or not ident:
                raise RunContextError(f"agent_roles: {role!r} -> {ident!r}; a role and its model identifier are "
                                      f"non-empty strings")
            tag = model_name(ident)
            if tag not in self.allowed:
                raise LockError(f"agent_roles: {role!r} runs {ident!r}, and {tag} is not in this run's allowed "
                                f"models ({', '.join(sorted(self.allowed))})")
            if "generator" not in _roles(self.allowed[tag], tag):
                raise LockError(f"agent_roles: {role!r} runs {ident!r}, and {tag} is allowed as "
                                f"{self.allowed[tag]!r}, not as a generator (Mentori's components are generators)")
        if self.tools is not None:
            if (not isinstance(self.tools, list) or not all(isinstance(t, str) and t for t in self.tools)
                    or len(set(self.tools)) != len(self.tools)):
                raise RunContextError(f"tools must be None or a list of distinct tool names, got {self.tools!r}")
        if self.servers is not None:
            if not isinstance(self.servers, dict) or not self.servers:
                raise RunContextError(f"servers must be None or a dict of model tag -> server, got {self.servers!r}")
            for tag, url in self.servers.items():
                if tag not in self.allowed:
                    raise RunContextError(f"servers names {tag!r}, which is not in this run's allowed models "
                                          f"({', '.join(sorted(self.allowed))})")
                if not isinstance(url, str) or not url.startswith(("http://", "https://")) or url != url.strip():
                    raise RunContextError(f"servers: {tag!r} -> {url!r}; a server is an http(s) URL")
            self.servers = dict(self.servers)

    def server_for(self, tag: str) -> str:
        """The Ollama server a call to tag goes to: servers[tag] where servers names it, else base_url."""
        return (self.servers or {}).get(tag, self.base_url)

    def next_seq(self) -> int:
        with self._lock:
            self.seq += 1
            return self.seq

    def to_dict(self) -> dict:
        d = {"run_id": self.run_id, "arm": self.arm, "item_id": self.item_id, "draw": self.draw,
             "thinking": self.thinking, "base_url": self.base_url, "sink": str(self.sink),
             "allowed": self.allowed, "agent_roles": self.agent_roles, "tools": self.tools, "seq": self.seq}
        if self.servers is not None:
            d["servers"] = dict(self.servers)       # D158 (2): written only when given, so older sidecars are unchanged
        return d


def model_name(identifier: str) -> str:
    """The model tag in a Mentori model identifier: the provider prefix ('ollama::', 'gemini::'; none means
    ollama) and a [think:x] suffix removed, as backend.agents.models.utils.parse_model_identifier does."""
    name = identifier.split("::", 1)[1] if "::" in identifier else identifier
    if "[" in name and "]" in name:
        name = name[:name.index("[")]
    return name.strip()


def _roles(value, tag: str = "") -> tuple:
    """One role or a list of roles as a tuple; anything else, or an empty list, raises LockError."""
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)) and value and all(isinstance(r, str) for r in value):
        return tuple(value)
    raise LockError(f"{tag}: allowed gives {value!r}; a role is a string or a non-empty list of strings")


_ctx: contextvars.ContextVar[RunContext] = contextvars.ContextVar("experiments_run_context")
# (the context object the passages belong to, the passage ids); a separate variable, so a strategy's
# set_passages in one task does not change what a sibling task of the same run reads
_passages: contextvars.ContextVar[tuple] = contextvars.ContextVar("experiments_run_passages")
_gate: contextvars.ContextVar = contextvars.ContextVar("experiments_run_gate", default=None)   # D114 Q29 O2


@contextmanager
def run(ctx: RunContext):
    """Sets ctx as the run context for the block and resets it (and the passages) on the way out."""
    if not isinstance(ctx, RunContext):
        raise RunContextError(f"run() takes a RunContext, got {type(ctx).__name__}")
    t1, t2 = _ctx.set(ctx), _passages.set((ctx, None))
    try:
        yield ctx
    finally:
        _passages.reset(t2)
        _ctx.reset(t1)


@contextmanager
def gate(g):
    """Sets g as the call gate for the block (D114 Q29 O2; see the module docstring) and resets it on the way out."""
    if not (callable(getattr(g, "before", None)) and callable(getattr(g, "after", None))):
        raise RunContextError(f"a call gate has before(tag, role) and after(line, file), got {type(g).__name__}")
    token = _gate.set(g)
    try:
        yield g
    finally:
        _gate.reset(token)


def gate_in(context: contextvars.Context):
    """The call gate a context holds (a task's get_context()), or None."""
    return context.get(_gate)


def current() -> RunContext:
    try:
        return _ctx.get()
    except LookupError:
        raise RunContextError("no run context is set: a model call outside experiments.runner.run_context.run() "
                              "has no run, item or draw to belong to") from None


def check_model(tag: str, role: str) -> None:
    """Raises LockError unless the run's allowed list names tag with role."""
    ctx = current()
    if tag not in ctx.allowed:
        raise LockError(f"{tag}: not in this run's allowed models ({', '.join(sorted(ctx.allowed))})")
    if role not in _roles(ctx.allowed[tag]):
        raise LockError(f"{tag}: allowed in this run as {ctx.allowed[tag]!r}, not as {role!r}")
    g = _gate.get()
    if g is not None:
        g.before(tag, role)   # D114 Q29 O2: may refuse the call, before anything is sent


def agent_model(role: str) -> str:
    """The model identifier the run context names for Mentori's agent role `role` (agent_roles[role]). Raises
    RunContextError outside a run and LockError when the run names no model for the role: there is no 'default'
    role, session, database or built-in fallback."""
    ctx = current()
    ident = ctx.agent_roles.get(role)
    if not ident:
        raise LockError(f"the run context names no model for the agent role {role!r} (agent_roles has "
                        f"{sorted(ctx.agent_roles) or 'no role'}; no 'default' fallback); nothing was sent")
    return ident


def set_passages(ids: list) -> None:
    ctx = current()
    _passages.set((ctx, list(ids)))


def passages() -> list | None:
    """The ids the last set_passages() in this run and task gave, else None (never set)."""
    ctx = current()
    owner, ids = _passages.get((None, None))
    return list(ids) if owner is ctx and ids is not None else None


def _dumps(obj, **kw) -> str:
    # ensure_ascii keeps a lone surrogate as an escape (utf-8 cannot encode it); allow_nan=False refuses NaN and
    # infinity, which are not JSON: a failed score is a status in the record, never a value
    try:
        return json.dumps(obj, ensure_ascii=True, allow_nan=False, **kw)
    except (TypeError, ValueError) as e:
        raise RunContextError(f"the record is not JSON: {e}") from None


def append(record: dict, file: str = "calls.jsonl") -> dict:
    """Appends record as one JSON line to <sink>/<file>, with run_id, item_id, arm, run_draw, ctx_uid, seq and
    pid added. The write holds an exclusive fcntl.flock on the file, so threads and processes (the tool server
    writes to the same sink) never interleave lines. A record that already carries one of those keys with another
    value, or that is not JSON (NaN included), is refused before a seq is taken, so seqs have no gaps. Returns
    the line written, as a dict."""
    ctx = current()
    if Path(file).name != file:
        raise RunContextError(f"file must be a plain file name inside the sink, got {file!r}")
    added = {"run_id": ctx.run_id, "item_id": ctx.item_id, "arm": ctx.arm, "run_draw": ctx.draw,
             "ctx_uid": ctx.ctx_uid, "seq": None, "pid": os.getpid()}
    clash = {k: record[k] for k in ADDED if k in record and k != "seq" and record[k] != added[k]}
    if "seq" in record:
        clash["seq"] = record["seq"]
    if clash:
        raise RunContextError(f"the record already carries {clash}, which differs from the run context")
    _dumps(record)
    added["seq"] = ctx.next_seq()
    line = _dumps({**record, **added}) + "\n"
    ctx.sink.mkdir(parents=True, exist_ok=True)
    with open(ctx.sink / file, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    g = _gate.get()
    if g is not None:
        g.after({**record, **added}, file)   # D114 Q29 O2: the line as written
    return {**record, **added}


def sidecar(task_id: str, sink: Path | None = None) -> Path:
    """<sink>/ctx/<task_id>.json; sink defaults to the current run's."""
    if not task_id or Path(task_id).name != task_id or task_id in (".", ".."):
        raise RunContextError(f"task_id must be a plain file name, got {task_id!r}")
    return Path(sink if sink is not None else current().sink) / "ctx" / f"{task_id}.json"


def dump(task_id: str) -> Path:
    """Writes the current context as JSON at <sink>/ctx/<task_id>.json (whole file or nothing) and returns
    the path. task_id RUN_TASK_ID takes the run-level context (item_id None) and only it. An existing sidecar is
    overwritten only by a context with the same run_id, item_id, arm, draw and sink (SIDECAR_IDENTITY)."""
    path = sidecar(task_id)
    run_level = current().item_id is None
    if run_level != (task_id == RUN_TASK_ID):
        raise RunContextError(f"dump({task_id!r}): {RUN_TASK_ID}.json holds the run-level context (item_id None) "
                              f"and every other sidecar an item's; this context has item_id {current().item_id!r}")
    if path.is_file():   # a task id reused across items would give a late tool call of one item another's context
        old = json.loads(path.read_text(encoding="utf-8"))
        new = current().to_dict()
        differ = [k for k in SIDECAR_IDENTITY if old.get(k) != new[k]]
        if differ:
            raise RunContextError(f"dump({task_id!r}): {path} holds another context (differs in "
                                  f"{', '.join(differ)}); a Mentori task id names one item of one run")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(_dumps(current().to_dict(), indent=1) + "\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


def load(path: Path) -> RunContext:
    """The context a dump() wrote, as a new RunContext with its own ctx_uid and seq starting at 0."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("run_id", "arm", "item_id", "draw", "thinking", "base_url", "sink", "allowed",
                           "agent_roles", "tools") if k not in d]
    if missing:
        raise RunContextError(f"{path}: the sidecar has no {', '.join(missing)}")
    return RunContext(run_id=d["run_id"], arm=d["arm"], item_id=d["item_id"], draw=d["draw"],
                      thinking=d["thinking"], base_url=d["base_url"], sink=Path(d["sink"]), allowed=d["allowed"],
                      agent_roles=d["agent_roles"], tools=d["tools"], servers=d.get("servers"))
