"""The few functions every entry point of experiments/mentori uses to run under the lock (step 3, A9; D48, D49, D67).

    from experiments.runner import experiment as ex
    qs = ex.questions()                                   # the 135 questions of answer key v2.4 (D48), key order
    sets = ex.scaling_questions(5)                        # G4 only (Q105): {"common": the 135, "per_size": 66 at 5}
    rid = ex.run_id("exp_01", "single_pass", "s20")       # "exp_01__single_pass__s20"
    sink = ex.sink(rid)                                   # findings/runs/exp_01__single_pass__s20/ (created)
    models = {"handyman": "gemini::gemini-3-flash-preview"}
    for d in ex.draws(2):                                 # (1, 2, 3) for Figures 2, 3 and 4, (1,) for 6 (D49, D78)
        for q in qs:
            key = ex.answer_key("single_pass", q["id"], d)          # resume and dedupe; index= where it varies
            ctx = ex.context("exp_01", "single_pass", q["id"], d, models, base_url=BASE, run=rid)
            with rc.run(ctx):
                ...                                       # every model call of this (item, draw)
    run_ctx = ex.context("exp_03", "full_pipeline", None, 1, models, base_url=BASE, run=rid3)
    with ex.tool_server(run_ctx) as sse_url:              # Mentori's engine connects to it (settings.TOOL_SERVER_URL)
        ...

QUESTIONS. The 135 are the questions of the D5 key (data/ground_truth_v2/ground_truth_v2_4_as_v1.json, S381; the
six D7 drops already absent) in scope on the 20-paper index of Figures 2 to 4: every question the key marks not
answerable, and every answerable one with min_core 20 or less (the Q55 rule, scripts/key_scope.py in_scope at core
size 20). That is the submission's 138 (the harness filter at 20 core papers, key_scope K5) less CD_015, SY_010 and
OOD_011 (D7, D48). Their text comes from the v2.4 records (data/ground_truth_v2/all_v2_4.json), in that file's order;
answerable is v2.4's question_answerable (D5: the ten false-premise questions are answerable). Both files are read
only when their sha256 is the one pinned here. A count other than 135, or one of D48's three ids present, is refused.

G4'S TWO SETS (Q105, D75). Corpus scaling (exp_02_scaling_factorial.py) asks, on an index of N core papers (N in
SCALING_CORE_SIZES), two named sets, and scaling_questions(N) returns both: "common", the 135 of questions() at every
size (the primary set, the fixed common set Reviewer 4 asked for), and "per_size", every question of the D5 key in
scope at N (the same Q55 rule, scripts/key_scope.py in_scope at N: not answerable, or answerable with min_core <= N),
for the deposit's comparison with the published figure. The D5 key holds 244 questions (v2.4's 250 less D7's six,
D48's three among them), so per_size counts 66, 90, 135 and 244 at 5, 10, 20 and 50 core papers (N_PER_SIZE; another
count is refused), and at 20 it is the common set itself. Every other run asks questions() only.

RUNS AND SINKS. A run is one (experiment, arm, extra) and writes to one sink, findings/runs/<run_id>/, which holds
calls.jsonl, the sidecars in ctx/ and run_identity.json. sink() refuses a directory whose ctx/run.json names another
run or sink; the same run_id finds its own sink again, which is how a run resumes. A sink holds one configuration:
the first context() of a run writes <sink>/run_identity.json (IDENTITY: run_id, arm, allowed, agent_roles, thinking,
tools), and every later context() of that run, and tool_server(), is refused when one of them differs, so a resume
under other models, thinking or tools cannot add its answers to the same sink under the same answer keys. Items,
draws and the Ollama server (base_url) may differ: the first two are what a run iterates over, and every record
writes its server and model digest (LOCK.toml [record]). A run's items and draws are told apart by their contexts
(item_id, draw) and by answer_key(); a run spanning several draws gives its run-level context one of them, because
RunContext requires a draw wherever a generator is allowed (the run-level context makes no model call, and the tool
server does not compare draws).

CONTEXTS. context() builds the RunContext of one (item, draw), or the run-level one (item_id None). Its run_id
starts with experiment__arm, and a sink it is given is the directory named by that run_id, so one arm's records
cannot land in another arm's run or sink. models maps
each Mentori agent role the run uses to its model identifier ('ollama::<tag>', 'gemini::<model>' or
'anthropic::<model>', B11), and becomes agent_roles exactly: no 'default' is added. allowed comes from the lock: every
model in models is allowed as a generator (Mentori's components are generators, D66) and is checked against the lock
now (Lock.ollama, Lock.gemini or anthropic_client.settings with the context's draw and thinking), so a model the
lock cannot run is refused before the run starts;
the lock's judge ([judge] model) is allowed as judge, which the adapter reaches only inside lock_adapter.judge().

THE TOOL SERVER. tool_server(run_ctx) serves one run: it dumps the run-level context as <sink>/ctx/run.json, starts
backend/tool_server.py in the Mentori environment (uv run --project experiments/mentori --frozen python -P) with
MENTORI_RUN_SINK=<sink> and the sink as working directory, on a port of 127.0.0.1, waits until GET /sse answers with
the endpoint event, and yields the SSE URL. The port is bound and listened on here, before the server starts, and
handed to it as an inherited file descriptor (uvicorn serves on that socket), so no other process can take the port
between its choice and the server's start and answer in the server's place. The working directory is the sink
because Mentori's logging writes backend/logs/app.log relative to it (backend/logging_config.py:67-70), and its
settings read .env from it; -P keeps that directory off sys.path. backend/tool_server.py's own __main__ binds
0.0.0.0:8777, so the process runs a launcher that calls that module's build(), sets the host, port and transport
security, and runs uvicorn on the inherited socket; the module itself is unchanged. Mentori's
engine connects to f"{settings.TOOL_SERVER_URL}/sse" (backend/agents/orchestrator/engine.py:173-176), and settings is
read once, at the import of backend.config: tool_server() sets the environment variable TOOL_SERVER_URL (read by an
import after this point) and, when backend.config is already imported, the attribute settings.TOOL_SERVER_URL; both
are put back on exit. No settings file is edited. The server's stdout and stderr go to <sink>/tool_server.log; a
server that exits before it serves is refused with the end of that log. On exit the server's process group gets
SIGTERM, then SIGKILL after 15 s. tool_server() is a plain context manager (it blocks while the server starts), and
one runs at a time in a process.
"""

from __future__ import annotations

import copy
import hashlib
import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from experiments.runner import anthropic_client
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError, load

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
RUNS = ROOT / "findings" / "runs"

KEY_V24 = ROOT / "data" / "ground_truth_v2" / "all_v2_4.json"
KEY_V24_SHA256 = "5d8362ae931dc0fe0cc132be6b5e57187e3ae7d3131d86f63cdf1a44633fadd5"
KEY_D5 = ROOT / "data" / "ground_truth_v2" / "ground_truth_v2_4_as_v1.json"     # S381; scripts/key_scope.py KEY
KEY_D5_SHA256 = "e971de522df6fab54a070e44736b6cb28a5ebd26bab07ca9e1513230bb86f4ef"
CORE_SIZE = 20                     # the 20-paper index of Figures 2 to 4
N_QUESTIONS = 135                  # D48
DROPPED_D48 = ("CD_015", "SY_010", "OOD_011")
SCALING_CORE_SIZES = (5, 10, 20, 50)                     # G4's indexes (exp_02_scaling_factorial.py CORE_SIZES)
SCALING_SETS = ("common", "per_size")                    # Q105 (D75): G4's two named question sets, primary first
N_PER_SIZE = {5: 66, 10: 90, 20: 135, 50: 244}           # per_size at each core size (scripts/key_scope.py in_scope)
FIELDS = ("id", "question", "category", "answerable", "answer_type", "short_answer", "key_concepts", "min_core")

DRAWS = {2: (1, 2, 3), 4: (1, 2, 3), 3: (1, 2, 3), 6: (1,)}   # by figure: D49; Figure 3 three draws by D78 Q116
IDENTITY_FILE = "run_identity.json"                      # <sink>/run_identity.json: the run's configuration
IDENTITY = ("run_id", "arm", "allowed", "agent_roles", "thinking", "tools")
PROVIDERS = ("ollama", "gemini", "anthropic")   # the providers the lock adapter routes (B11: anthropic::, not claude::)
SEP = "__"                         # between the parts of a run_id
KEY_SEP = "|"                      # between the parts of an answer key
_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_KEY_PART = re.compile(r"^[^\s|]+$")

SERVER_LOG = "tool_server.log"
URL_VAR = "TOOL_SERVER_URL"
START_TIMEOUT_S = 300.0            # importing every tool module takes a while on a cold start
STOP_TIMEOUT_S = 15.0
_LAUNCHER = """
import os, socket, sys
from pathlib import Path
sys.path.insert(0, {mentori!r})
import uvicorn
from backend import tool_server as ts
from mcp.server.transport_security import TransportSecuritySettings
port, fd = int(sys.argv[1]), int(sys.argv[2])
sock = socket.socket(fileno=fd)              # bound to 127.0.0.1:port and listening, by experiment.tool_server()
if sock.getsockname() != ("127.0.0.1", port):
    raise SystemExit(f"inherited socket {{fd}} is bound to {{sock.getsockname()}}, not 127.0.0.1:{{port}}")
server = ts.build(Path(os.environ[ts.SINK_VAR]))
# what FastMCP sets itself for a server built on 127.0.0.1 (mcp/server/fastmcp/server.py, FastMCP.__init__)
server.settings.host = "127.0.0.1"
server.settings.port = port
server.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True, allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"])
ts.logger.info(f"Starting Mentori MCP Server on 127.0.0.1:{{port}} for sink {{os.environ[ts.SINK_VAR]}}")
# FastMCP.run_sse_async (mcp/server/fastmcp/server.py:756-769), with uvicorn serving the inherited socket
config = uvicorn.Config(server.sse_app(), host="127.0.0.1", port=port, log_level=server.settings.log_level.lower())
uvicorn.Server(config).run(sockets=[sock])
"""

_serving = False                   # one tool server at a time in this process (settings is one object)


class ExperimentError(Exception):
    pass


def _sha256(path: Path) -> tuple[bytes, str]:
    raw = Path(path).read_bytes()
    return raw, hashlib.sha256(raw).hexdigest()


def _in_scope(q: dict, core_size: int) -> bool:
    """The Q55 rule (scripts/key_scope.py in_scope): not answerable, or answerable with min_core <= core_size."""
    return not q["answerable"] or q["min_core"] <= core_size


@lru_cache(maxsize=1)
def _key() -> tuple:
    """Every question of the D5 key (244), in the v2.4 key's order, each a dict of FIELDS; both files sha256-pinned."""
    v24_raw, v24_sha = _sha256(KEY_V24)
    if v24_sha != KEY_V24_SHA256:
        raise ExperimentError(f"{KEY_V24} has sha256 {v24_sha}, not the v2.4 key's {KEY_V24_SHA256}")
    d5_raw, d5_sha = _sha256(KEY_D5)
    if d5_sha != KEY_D5_SHA256:
        raise ExperimentError(f"{KEY_D5} has sha256 {d5_sha}, not the D5 key's {KEY_D5_SHA256}")
    d5 = json.loads(d5_raw)
    if d5.get("source_v24_sha256") != KEY_V24_SHA256:
        raise ExperimentError(f"{KEY_D5} was made from v2.4 sha256 {d5.get('source_v24_sha256')}, not {KEY_V24_SHA256}")
    scope = {}
    for q in d5["questions"]:
        if not isinstance(q.get("answerable"), bool):
            raise ExperimentError(f"{q.get('id')}: the D5 key's answerable is {q.get('answerable')!r}")
        if q["answerable"] and not (isinstance(q.get("min_core"), int) and not isinstance(q["min_core"], bool)):
            raise ExperimentError(f"{q['id']}: answerable in the D5 key without an integer min_core")
        scope[q["id"]] = q
    out, seen = [], set()
    for r in json.loads(v24_raw)["records"]:
        if r["id"] in seen:
            raise ExperimentError(f"{r['id']} is in the v2.4 key twice")
        seen.add(r["id"])
        if r["id"] not in scope:          # D7's six: not in the D5 key
            continue
        if r["question_answerable"] != scope[r["id"]]["answerable"]:
            raise ExperimentError(f"{r['id']}: v2.4 question_answerable {r['question_answerable']!r}, the D5 key "
                                  f"{scope[r['id']]['answerable']!r}")
        out.append({"id": r["id"], "question": r["question"], "category": r["category"],
                    "answerable": r["question_answerable"], "answer_type": r["answer_type"],
                    "short_answer": r["short_answer"], "key_concepts": r["key_concepts"],
                    "min_core": scope[r["id"]].get("min_core")})
    missing = sorted(set(scope) - seen)
    if missing:
        raise ExperimentError(f"{len(missing)} questions of the D5 key are not in the v2.4 records: {missing[:5]}")
    present = [i for i in DROPPED_D48 if i in {q["id"] for q in out}]
    if present:
        raise ExperimentError(f"{present} are in the D5 key; D48 drops them")
    return tuple(out)


@lru_cache(maxsize=1)
def _questions() -> tuple:
    out = [q for q in _key() if _in_scope(q, CORE_SIZE)]
    present = [i for i in DROPPED_D48 if i in {q["id"] for q in out}]
    if present:
        raise ExperimentError(f"{present} are among the questions; D48 drops them")
    if len(out) != N_QUESTIONS:
        raise ExperimentError(f"{len(out)} questions in scope at {CORE_SIZE} core papers, not {N_QUESTIONS} (D48)")
    return tuple(out)


def questions() -> list[dict]:
    """The 135 questions of answer key v2.4 (D48) in the key's order, each a dict of FIELDS (a fresh copy)."""
    return copy.deepcopy(list(_questions()))


def scaling_questions(core_size: int) -> dict[str, list[dict]]:
    """G4's two named question sets on an index of core_size core papers (Q105, D75; the module docstring, G4'S TWO
    SETS): {"common": the 135 of questions(), "per_size": the D5 key's questions in scope at core_size}, each in the
    key's order, each question a dict of FIELDS (fresh copies). A core size not in SCALING_CORE_SIZES is refused."""
    if type(core_size) is not int or core_size not in SCALING_CORE_SIZES:   # not a bool, a float or a string
        raise ExperimentError(f"core size {core_size!r}: G4's indexes have {', '.join(map(str, SCALING_CORE_SIZES))}")
    per_size = [q for q in _key() if _in_scope(q, core_size)]
    if len(per_size) != N_PER_SIZE[core_size]:
        raise ExperimentError(f"{len(per_size)} questions in scope at {core_size} core papers, not "
                              f"{N_PER_SIZE[core_size]} (N_PER_SIZE)")
    return {"common": questions(), "per_size": copy.deepcopy(per_size)}


def draws(figure: int) -> tuple:
    """The draws of a figure's runs: (1, 2, 3) for Figures 2 and 4 (D49) and Figure 3 (D78 Q116), (1,) for Figure 6
    (D49)."""
    if type(figure) is not int or figure not in DRAWS:     # not a bool, a float or a string
        raise ExperimentError(f"figure {figure!r}: D49 names draws for Figures {', '.join(map(str, sorted(DRAWS)))}")
    return DRAWS[figure]


def share_spec(part: str) -> tuple:
    """(k, n) of a share written "k/n": share k of n, 1 <= k <= n. Refuses anything else (D95 Q213)."""
    m = re.fullmatch(r"([1-9][0-9]*)/([1-9][0-9]*)", part) if isinstance(part, str) else None
    if not m or int(m.group(1)) > int(m.group(2)):
        raise ExperimentError(f"share {part!r}: write k/n with 1 <= k <= n (for example 2/4)")
    return int(m.group(1)), int(m.group(2))


def share(items, part: str) -> list:
    """Share k of n of items (part "k/n"), dealt round robin in the items' order: the items at positions k-1, k-1+n,
    k-1+2n, ... (D95 Q213: G5's questions split over n processes). The n shares are disjoint, together hold every item
    once, and keep the items' order inside each share; n = 1 gives every item."""
    k, n = share_spec(part)
    return list(items)[k - 1::n]


def _part(name: str, value, sep: str) -> str:
    """A run_id part (a directory name: letters, digits, '.', '_', '+', '-') or an answer-key part (no space, no
    '|'); sep is the separator it may not hold."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ExperimentError(f"{name} {value!r}: a string (or an integer)")
    value = str(value)
    if sep == SEP and (not _PART.match(value) or SEP in value):
        raise ExperimentError(f"{name} {value!r}: letters, digits, '.', '_', '+' and '-', starting with a letter or "
                              f"digit, without {SEP!r}")
    if sep == KEY_SEP and not _KEY_PART.match(value):
        raise ExperimentError(f"{name} {value!r}: no space and no {KEY_SEP!r}")
    return value


def run_id(experiment: str, arm: str, extra=None) -> str:
    """experiment__arm, or experiment__arm__extra (extra: what else names the run, such as an index)."""
    parts = [_part("experiment", experiment, SEP), _part("arm", arm, SEP)]
    if extra is not None:
        parts.append(_part("extra", extra, SEP))
    return SEP.join(parts)


def sink(run: str, root: Path = RUNS) -> Path:
    """<root>/<run>/ (root findings/runs), created. Refused when its ctx/run.json names another run or sink."""
    if not isinstance(run, str) or not all(_PART.match(p) for p in run.split(SEP)):
        raise ExperimentError(f"run_id {run!r}: not one run_id() makes")
    path = (Path(root) / run).resolve()
    held = rc.sidecar(rc.RUN_TASK_ID, path)
    if held.exists():
        try:
            old = json.loads(held.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise ExperimentError(f"{held} is not a run context ({e}); the sink is not reused") from None
        if not isinstance(old, dict) or old.get("run_id") != run or old.get("sink") != str(path):
            who = (old.get("run_id"), old.get("sink")) if isinstance(old, dict) else old
            raise ExperimentError(f"{path} holds the run context of {who!r}, not run {run!r}; a sink holds one run")
    path.mkdir(parents=True, exist_ok=True)
    return path


_run_sink = sink                   # context() takes a parameter named sink


def answer_key(config: str, question_id: str, draw: int, index=None) -> str:
    """config|question_id|d<draw>, or index|config|question_id|d<draw> where the script varies the index. The one
    key a script resumes and dedupes on (records.md F7, F25)."""
    if isinstance(draw, bool) or not isinstance(draw, int) or draw < 1:
        raise ExperimentError(f"draw {draw!r}: an integer from 1")
    parts = [_part("config", config, KEY_SEP), _part("question_id", question_id, KEY_SEP), f"d{draw}"]
    if index is not None:
        parts.insert(0, _part("index", index, KEY_SEP))
    return KEY_SEP.join(parts)


def _mentori_model(role: str, ident: str) -> tuple[str, str]:
    """(provider, model tag) of a Mentori model identifier; refuses one the adapter would not route as named."""
    if not isinstance(ident, str) or "::" not in ident:
        raise ExperimentError(f"{role!r}: {ident!r} names no provider; write 'ollama::<tag>', 'gemini::<model>' or "
                              "'anthropic::<model>'")
    provider, name = ident.split("::", 1)
    if provider not in PROVIDERS:
        raise ExperimentError(f"{role!r}: {ident!r}: provider {provider!r}, the adapter routes {PROVIDERS}")
    if "[" in name or "]" in name or name != name.strip() or not name:
        raise ExperimentError(f"{role!r}: {ident!r}: a [think:x] suffix is never sent (thinking comes from the run "
                              f"context); name the model alone")
    return provider, name


def _identity(ctx: rc.RunContext) -> dict:
    """The fields of a context that one run keeps the same in every context (IDENTITY), as JSON reads them back."""
    return json.loads(json.dumps({k: getattr(ctx, k) for k in IDENTITY}))


def _hold(ctx: rc.RunContext) -> None:
    """Writes <sink>/run_identity.json for the run's first context; refuses a context whose IDENTITY differs from the
    one written. The file is written whole under a temporary name and linked into place, so two processes starting
    the same run cannot both write it, and neither reads half of it."""
    ident = _identity(ctx)
    path = ctx.sink / IDENTITY_FILE
    ctx.sink.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        tmp = ctx.sink / f".{IDENTITY_FILE}.{os.getpid()}.{time.monotonic_ns()}"
        tmp.write_text(json.dumps(ident, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        try:
            os.link(tmp, path)
        except FileExistsError:
            pass
        finally:
            tmp.unlink()
    try:
        held = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ExperimentError(f"{path} is not a run identity ({e}); the sink is not reused") from None
    if not isinstance(held, dict):
        raise ExperimentError(f"{path} holds {held!r}, not a run identity; the sink is not reused")
    diff = sorted(k for k in set(IDENTITY) | set(held) if held.get(k) != ident.get(k))
    if diff:
        what = "; ".join(f"{k}: sink {held.get(k)!r}, here {ident.get(k)!r}" for k in diff)
        raise ExperimentError(f"{ctx.sink} holds run {held.get('run_id')!r} under another configuration ({what}; "
                              f"{path}); a sink holds one configuration: name the run apart (run_id extra)")


def context(experiment: str, arm: str, item_id: str | None, draw: int | None, models: dict,
            thinking: bool | str | None = None, *, base_url: str, run: str | None = None, sink: Path | None = None,
            tools: list | None = None, judge: bool = True, servers: dict | None = None) -> rc.RunContext:
    """The RunContext of one (item, draw) of a run, or the run-level one (item_id None). models: Mentori agent role ->
    model identifier; becomes agent_roles as given. run: the run_id (default run_id(experiment, arm)), which starts
    with experiment__arm; sink: the run's sink (default sink(run)), a directory named run. tools: the tool names the
    run enables (None: every tool the server has). judge: allow the lock's judge in the judge role (calls inside
    lock_adapter.judge()). servers: model tag -> the Ollama server its calls go to (D158 (2); RunContext.servers), not
    part of the run's identity, as base_url is not. Every model is checked against the lock with this draw and thinking, and the context
    against the run's identity in its sink (_hold), before the context is returned."""
    if not isinstance(models, dict) or not models:
        raise ExperimentError("models names no Mentori agent role; a run names every role it uses")
    head = run_id(experiment, arm)
    if run is None:
        run = head
    elif not isinstance(run, str) or run.split(SEP)[:2] != head.split(SEP) or run_id(*run.split(SEP, 2)) != run:
        raise ExperimentError(f"run {run!r} is not a run of experiment {experiment!r}, arm {arm!r}: a run_id starts "
                              f"with {head + SEP!r} or is {head!r}")
    if sink is not None and Path(sink).resolve().name != run:
        raise ExperimentError(f"sink {sink} is not run {run!r}'s: a run's sink is the directory named by its run_id")
    lock = load()
    allowed: dict = {}
    gemini, anthropic = [], []
    for role, ident in models.items():
        provider, name = _mentori_model(role, ident)
        allowed[name] = "generator"
        if provider == "gemini":
            gemini.append(name)
        elif provider == "anthropic":
            anthropic.append(name)
    if judge:
        jm = lock.d["judge"]["model"]
        allowed[jm] = ["generator", "judge"] if jm in allowed else "judge"
    ctx = rc.RunContext(run_id=run, arm=arm, item_id=item_id, draw=draw, thinking=thinking, base_url=base_url,
                        sink=Path(sink) if sink is not None else _run_sink(run), allowed=allowed,
                        agent_roles=dict(models), tools=tools, servers=servers)
    for name, roles in allowed.items():
        for r in ([roles] if isinstance(roles, str) else roles):
            try:
                if name in gemini:
                    lock.gemini(name, draw, thinking=thinking)
                elif name in anthropic:
                    lock._seed(draw, None)                 # the draw is checked (and recorded); no seed is sent
                    anthropic_client.settings(lock, name, thinking)
                elif r == "generator":
                    lock.ollama(name, role=r, draw=draw, thinking=thinking)
                else:
                    lock.ollama(name, role=r)
            except LockError as e:
                raise LockError(f"{name} as {r}: the lock does not run it ({e}); nothing was started") from None
    _hold(ctx)
    return ctx


def _listen() -> socket.socket:
    """A socket bound to a free port of 127.0.0.1 and listening, inheritable, for the tool server to serve on. Held
    from before the server starts until it exits, so no other process can bind the port in between."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        s.listen(128)
        s.set_inheritable(True)
    except OSError:
        s.close()
        raise
    return s


def _serves(port: int, timeout: float = 2.0) -> bool:
    """True when GET /sse on the port answers 200 with the SSE endpoint event (the first thing FastMCP sends)."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        conn.request("GET", "/sse", headers={"Accept": "text/event-stream"})
        resp = conn.getresponse()
        if resp.status != 200:
            return False
        for _ in range(5):
            if resp.readline().strip() == b"event: endpoint":
                return True
        return False
    except (OSError, http.client.HTTPException):
        return False
    finally:
        conn.close()


def _tail(path: Path, start: int, n: int = 40) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(start)
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError as e:
        return f"(no log: {e})"
    return "\n".join(lines[-n:])


def _stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    for sig, wait in ((signal.SIGTERM, STOP_TIMEOUT_S), (signal.SIGKILL, STOP_TIMEOUT_S)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


@contextmanager
def tool_server(run_ctx: rc.RunContext, start_timeout_s: float = START_TIMEOUT_S):
    """Serves run_ctx's run (see the module docstring, THE TOOL SERVER) and yields the SSE URL."""
    global _serving
    if not isinstance(run_ctx, rc.RunContext) or run_ctx.item_id is not None:
        raise ExperimentError("tool_server takes the run-level context (item_id None) of the run it serves")
    if _serving:
        raise ExperimentError("a tool server already serves a run in this process; settings.TOOL_SERVER_URL names one")
    _hold(run_ctx)
    with rc.run(run_ctx):
        rc.dump(rc.RUN_TASK_ID)
    sock = _listen()
    port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    log = run_ctx.sink / SERVER_LOG
    env = {**os.environ, "MENTORI_RUN_SINK": str(run_ctx.sink)}
    cmd = ["uv", "run", "--project", str(MENTORI), "--frozen", "python", "-P", "-c",
           _LAUNCHER.format(mentori=str(MENTORI)), str(port), str(sock.fileno())]
    try:
        with open(log, "ab") as f:
            start = f.tell()
            f.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S')} run {run_ctx.run_id} port {port} pid {os.getpid()}\n"
                    .encode())
            f.flush()
            proc = subprocess.Popen(cmd, cwd=run_ctx.sink, env=env, stdin=subprocess.DEVNULL, stdout=f,
                                    stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(sock.fileno(),))
    finally:
        sock.close()                  # the server holds its own copy; the port stays bound until it exits
    old_env = os.environ.get(URL_VAR)
    config = sys.modules.get("backend.config")
    old_setting = getattr(config.settings, URL_VAR) if config is not None else None
    _serving = True
    try:
        deadline = time.monotonic() + start_timeout_s
        while True:
            if proc.poll() is not None:
                raise ExperimentError(f"the tool server exited with code {proc.returncode} before it served "
                                      f"(log {log}):\n{_tail(log, start)}")
            if _serves(port):
                break
            if time.monotonic() > deadline:
                raise ExperimentError(f"the tool server did not serve on {base} within {start_timeout_s:.0f} s "
                                      f"(log {log}):\n{_tail(log, start)}")
            time.sleep(0.5)
        if proc.poll() is not None:
            raise ExperimentError(f"the tool server exited with code {proc.returncode} (log {log}):\n"
                                  f"{_tail(log, start)}")
        os.environ[URL_VAR] = base
        if config is not None:
            setattr(config.settings, URL_VAR, base)
        yield f"{base}/sse"
    finally:
        _stop(proc)
        if old_env is None:
            os.environ.pop(URL_VAR, None)
        else:
            os.environ[URL_VAR] = old_env
        if config is not None:
            setattr(config.settings, URL_VAR, old_setting)
        _serving = False
