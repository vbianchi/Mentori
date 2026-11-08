"""Checks for experiments/mentori/backend/tool_server.py and for the one agent-role lookup the tools use (step 2
review, D1 and D2, 15 October). Offline: a stub Ollama server on 127.0.0.1, a fake Tavily, no model and no key.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_tool_server

Every tool call below goes through the FastMCP server that tool_server.build() returns (FastMCP.call_tool), so it
runs inside the wrapper that restores the run context, and every model call goes through the real lock adapter to
the stub, which writes the real record in the sink.
1. The server: it refuses to start without <sink>/ctx/run.json, with a run.json that has an item_id, with a
   tools field naming a tool it does not have, or when a tool module failed to import; tools None registers every
   discovered tool, a list exactly those. dump refuses to overwrite a sidecar holding another item's context.
2. A tool with no task_id runs under the run-level context (item_id None), where a model call is refused; a real
   one (validate_python_syntax) runs.
3. A tool with task_id restores that task's item context per call: read_image on task A and describe_figure and
   compare_images on task B write records carrying items QA and QB, the vision role's model and the call site.
4. Refusals before the tool runs: a task_id with no sidecar, no task_id for a tool that takes one, the reserved
   task_id "run", a sidecar of another run, a sidecar whose tools differ from the run's.
5. The role lookup: the vision tools, the transcriber (directly and through read_document's vision path),
   web_search (filtered) and deep_research resolve agent_roles[role] (the record's model is that role's model),
   and every model-calling tool in the four modules refuses a missing role with LockError naming the role even
   though agent_roles has 'default' (smart_query included, through the tool it dispatches to); the refusal raises
   out of the tool, never returned as its result text. The four modules hold no other lookup (no
   resolve_model_for_chat, agent_roles.get, user.settings).
   Not covered: over SSE, the MCP low-level server turns that exception into a result with isError=True, which
   Mentori's executor reads as text (tool_server docstring); FastMCP.call_tool in-process raises ToolError instead.
6. Every tool whose source reaches a model call, directly or through another tool, takes task_id.
"""

import asyncio
import inspect
import json
import os
import re
import sys
import tempfile
import threading
import tokenize
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
tmp = Path(tempfile.mkdtemp(prefix="check_tool_server_")).resolve()
# Mentori's settings read these at import: a scratch database, workspace and vector store, never the copy's own
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
os.environ["BACKEND_INTERNAL_URL"] = "http://127.0.0.1:9"
sys.path.insert(0, str(MENTORI))

from PIL import Image  # noqa: E402

from backend import tool_server as ts  # noqa: E402
from backend.agents import lock_adapter as la  # noqa: E402
from backend.mcp.decorator import ToolMetadata  # noqa: E402
from backend.mcp.registry import registry  # noqa: E402
from backend.retrieval.agents.transcriber import AgentFactory  # noqa: E402

from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

lock = load()
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def cause(fn):
    """The exception fn raises, unwrapped from FastMCP's ToolError; None when it returns."""
    try:
        fn()
    except Exception as e:
        while e.__cause__ is not None:
            e = e.__cause__
        return e
    return None


class Stub(BaseHTTPRequestHandler):
    """Answers like Ollama 0.40.2 holding every model in the lock; keeps each request body."""
    bodies = []

    def do_GET(self):
        body = ({"version": lock.d["server"]["ollama_version"]} if self.path == "/api/version"
                else {"models": [{"name": t, "digest": r["digest"]} for t, r in lock.d["models"].items()]})
        self._lines([body])

    def do_POST(self):
        Stub.bodies.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        done = {"done": True, "done_reason": "stop", "prompt_eval_count": 11, "eval_count": 7}
        if self.path == "/api/chat":
            self._lines([{"message": {"role": "assistant", "content": "A stub answer."}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, **done}])
        else:
            self._lines([{"response": "A stub answer.", "done": False}, {"response": "", **done}])

    def _lines(self, objs):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for o in objs:
            self.wfile.write((json.dumps(o) + "\n").encode())

    def log_message(self, *args):
        pass


stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{stub.server_address[1]}"

# One model per role, so a record's model names the role that chose it
VISION, TRANSCRIBER, HANDYMAN, EDITOR, CODER, DEFAULT = (
    "gemma3:27b", "llama3:8b", "qwen3-coder:30b", "qwen3-coder-next:q4_K_M", "deepseek-r1:70b", "qwen3.5:122b")
ROLES = {"vision": f"ollama::{VISION}", "transcriber": f"ollama::{TRANSCRIBER}", "handyman": f"ollama::{HANDYMAN}",
         "editor": f"ollama::{EDITOR}", "coder": f"ollama::{CODER}", "default": f"ollama::{DEFAULT}"}
ALLOWED = {m: "generator" for m in (VISION, TRANSCRIBER, HANDYMAN, EDITOR, CODER, DEFAULT)}


def ctx(sink, item, run_id="check-tool-server", agent_roles=None, tools=None):
    return rc.RunContext(run_id=run_id, arm="full_pipeline", item_id=item, draw=1, thinking=None, base_url=BASE,
                         sink=sink, allowed=ALLOWED, agent_roles=dict(ROLES if agent_roles is None else agent_roles),
                         tools=tools)


def dump(c, task_id):
    with rc.run(c):
        return rc.dump(task_id)


def records(sink):
    f = sink / "calls.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def call(server, name, args):
    return asyncio.run(server.call_tool(name, args))


def text(result) -> str:
    blocks = result[0] if isinstance(result, tuple) else result
    return "".join(getattr(b, "text", "") for b in blocks)


# Probe tools: what run context a call sees, and whether a model call is allowed there
def probe(note: str = "") -> str:
    """Probe without task_id."""
    c = rc.current()
    return json.dumps({"item_id": c.item_id, "run_id": c.run_id})


def probe_model(note: str = "") -> str:
    """Probe without task_id that tries a model call."""
    return la.generate(ROLES["handyman"], "hello")["response"]


def probe_item(note: str = "", task_id: str = None) -> str:
    """Probe with task_id."""
    c = rc.current()
    return json.dumps({"item_id": c.item_id, "run_id": c.run_id})


registry.discover_tools()
REAL = set(registry.tools)
for f in (probe, probe_model, probe_item):
    registry.tools[f.__name__] = ToolMetadata(name=f.__name__, description=f.__doc__, func=f)

# 1. the server
sink = tmp / "sink"
e = cause(lambda: ts.build(sink))
check("1 no run.json: the server refuses to start", isinstance(e, rc.RunContextError), str(e)[:100])
dump(ctx(sink, "Q-X"), "item-as-run")
(sink / "ctx" / "run.json").write_text((sink / "ctx" / "item-as-run.json").read_text())
e = cause(lambda: ts.build(sink))
check("1 a run.json with an item_id: refused", isinstance(e, rc.RunContextError) and "item_id" in str(e), str(e)[:100])
e = cause(lambda: dump(ctx(sink, None), rc.RUN_TASK_ID))
check("1 dump refuses to overwrite a sidecar holding another item's context", isinstance(e, rc.RunContextError)
      and "item_id" in str(e), str(e)[:100])
(sink / "ctx" / "run.json").unlink()
dump(ctx(sink, None, tools=["read_image", "no_such_tool"]), rc.RUN_TASK_ID)
e = cause(lambda: ts.build(sink))
check("1 a tools field naming a tool the server lacks: refused", isinstance(e, rc.RunContextError)
      and "no_such_tool" in str(e), str(e)[:100])
dump(ctx(sink, None), rc.RUN_TASK_ID)
registry.failed["broken_tools"] = "ImportError: no module named nowhere"
e = cause(lambda: ts.build(sink))
check("1 a tool module that failed to import: the server refuses to start, naming it",
      isinstance(e, rc.RunContextError) and "broken_tools" in str(e), str(e)[:100])
del registry.failed["broken_tools"]
all_server = ts.build(sink)
names = {t.name for t in asyncio.run(all_server.list_tools())}
check(f"1 tools None registers every discovered tool ({len(REAL)} and the 3 probes)", names == set(registry.tools),
      f"{len(names)} registered")
MODEL_TOOLS = ["read_image", "describe_figure", "compare_images", "read_document", "deep_research",
               "deep_research_rlm", "cross_document_analysis", "paper_triage", "analyze_corpus",
               "summarize_document_pages", "web_search", "smart_query"]   # every tool that reaches a model call
SOME = MODEL_TOOLS + ["validate_python_syntax", "probe", "probe_model", "probe_item"]
run_ctx = ctx(sink, None, tools=SOME)
dump(run_ctx, rc.RUN_TASK_ID)
server = ts.build(sink)
names = {t.name for t in asyncio.run(server.list_tools())}
check("1 a tools list registers exactly those tools", names == set(SOME), f"{len(names)} registered")

# 2. tools with no task_id: the run-level context
seen = json.loads(text(call(server, "probe", {"note": "x"})))
check("2 a tool with no task_id runs under the run-level context (item_id None)",
      seen == {"item_id": None, "run_id": "check-tool-server"}, json.dumps(seen))
n = len(Stub.bodies)
e = cause(lambda: call(server, "probe_model", {}))
check("2 a model call in the run-level context is refused before any request", isinstance(e, LockError)
      and "run-level" in str(e) and len(Stub.bodies) == n, str(e)[:110])
out = text(call(server, "validate_python_syntax", {"code": "x = 1"}))
check("2 a real tool with no task_id (validate_python_syntax) runs", "valid" in out.lower(), out[:60])

# 3. tools with task_id: each call restores its own item
dump(ctx(sink, "QA", tools=SOME), "task-A")
dump(ctx(sink, "QB", tools=SOME), "task-B")
img = tmp / "ws" / "fig.png"
img.parent.mkdir(parents=True, exist_ok=True)
Image.new("RGB", (8, 8), (200, 30, 30)).save(img)
seen = json.loads(text(call(server, "probe_item", {"task_id": "task-A"})))
check("3 a tool with task_id runs in that task's item context", seen["item_id"] == "QA", json.dumps(seen))
outA = text(call(server, "read_image", {"path": str(img), "task_id": "task-A"}))
recA = records(sink)[-1]
check("3 read_image on task-A: the record carries item QA, the vision role's model, the image's sha256 only",
      recA["item_id"] == "QA" and recA["model"] == VISION and recA["role"] == "generator"
      and len(recA["messages_sent"][0]["images_sha256"]) == 1 and Stub.bodies[-1]["model"] == VISION
      and outA.startswith(f"[Analysis by {VISION}]"),
      f"item {recA['item_id']}, model {recA['model']}, site {recA['call_site']}")
call(server, "describe_figure", {"path": str(img), "task_id": "task-B"})
call(server, "compare_images", {"path1": str(img), "path2": str(img), "task_id": "task-B"})
rB = records(sink)[-3:]
check("3 describe_figure and compare_images on task-B: three records, item QB, the vision model, call site in "
      "vision_tools.py", [r["item_id"] for r in rB] == ["QB"] * 3 and {r["model"] for r in rB} == {VISION}
      and all(r["call_site"].startswith("backend/mcp/custom/vision_tools.py:") for r in rB),
      rB[0]["call_site"])
check("3 each tool call loaded its sidecar afresh (one ctx_uid per call)",
      len({recA["ctx_uid"], *(r["ctx_uid"] for r in rB)}) == 3)

# 4. refusals before the tool runs
n_bodies, n_recs = len(Stub.bodies), len(records(sink))
refusals = {
    "a task_id with no sidecar": {"path": str(img), "task_id": "task-missing"},
    "no task_id for a tool that takes one": {"path": str(img)},
    "the reserved task_id 'run'": {"path": str(img), "task_id": "run"},
}
dump(ctx(sink, "QZ", run_id="another-run", tools=SOME), "task-other-run")
refusals["a sidecar of another run"] = {"path": str(img), "task_id": "task-other-run"}
dump(ctx(sink, "QT", tools=SOME[:3]), "task-other-tools")
refusals["a sidecar whose tools differ from the run's"] = {"path": str(img), "task_id": "task-other-tools"}
for label, args in refusals.items():
    e = cause(lambda: call(server, "read_image", args))
    check(f"4 refused: {label}", isinstance(e, rc.RunContextError), str(e)[:110])
check("4 the refusals sent nothing and wrote no record", len(Stub.bodies) == n_bodies
      and len(records(sink)) == n_recs)

# 5. one role lookup
asked = []
_agent_model = rc.agent_model


def spy(role):
    asked.append(role)
    return _agent_model(role)


rc.agent_model = spy
try:
    # transcriber, directly in an item context
    with rc.run(ctx(sink, "QT1", tools=SOME)):
        agent = asyncio.run(AgentFactory.get_transcriber({"transcriber": "ollama::should-not-be-read"}))
        page = asyncio.run(agent.transcribe_page(str(img)))
    r = records(sink)[-1]
    check("5 transcriber: get_transcriber takes agent_roles['transcriber'] from the run context, not its argument",
          agent.model_identifier == ROLES["transcriber"] and r["model"] == TRANSCRIBER and r["item_id"] == "QT1"
          and r["caller_asked"]["images"] == 1 and page == "A stub answer.", f"{r['model']}, item {r['item_id']}")

    # read_document's vision path through the server: a one-page PDF, transcribed through the stub
    uroot = tmp / "ws" / "u1"
    uroot.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (60, 80), (255, 255, 255)).save(uroot / "doc.pdf")
    dump(ctx(sink, "QD", tools=SOME), "task-D")
    out = text(call(server, "read_document", {"file_path": "doc.pdf", "mode": "vision", "user_id": "u1",
                                              "task_id": "task-D"}))
    r = records(sink)[-1]
    check("5 read_document (vision): the run's transcriber, no database read, record item QD",
          r["model"] == TRANSCRIBER and r["item_id"] == "QD" and "--- Page 1 (Vision) ---" in out,
          f"{r['model']}, item {r['item_id']}, {out[:40]!r}")

    # web_search (filtered) through the server, Tavily faked
    ws_globals = registry.tools["web_search"].func.__wrapped__.__globals__
    ws_globals["_fetch_tavily"] = lambda payload: {"answer": "", "results": [
        {"title": "A result", "url": "https://example.org/a", "content": "Text.", "score": 0.9}]}
    dump(ctx(sink, "QW", tools=SOME), "task-W")
    n = len(records(sink))
    call(server, "web_search", {"query": "RNA-seq aligners", "llm_filter": True, "TAVILY_API_KEY": "offline",
                                "workspace_path": str(tmp / "ws"), "task_id": "task-W"})
    rw = records(sink)[n:]
    check("5 web_search (filtered): every call on the handyman's model, item QW",
          rw and {r["model"] for r in rw} == {HANDYMAN} and {r["item_id"] for r in rw} == {"QW"},
          f"{len(rw)} records")

    # deep_research through the server (max_depth 0: the planning call only)
    dump(ctx(sink, "QR", tools=SOME), "task-R")
    call(server, "deep_research", {"topic": "aligners", "user_id": "u1", "task_id": "task-R", "max_depth": 0})
    r = records(sink)[-1]
    check("5 deep_research: the handyman's model, item QR", r["model"] == HANDYMAN and r["item_id"] == "QR",
          f"{r['model']}, item {r['item_id']}")

    # a missing role, with 'default' set: every model-calling tool fails with LockError naming the role
    no = {}
    for role in ("vision", "transcriber", "handyman", "editor", "coder"):
        dump(ctx(sink, f"QN-{role}", agent_roles={k: v for k, v in ROLES.items() if k != role}, tools=SOME),
             f"task-no-{role}")
        no[role] = f"task-no-{role}"
    cases = [
        ("read_image", "vision", {"path": str(img)}),
        ("describe_figure", "vision", {"path": str(img)}),
        ("compare_images", "vision", {"path1": str(img), "path2": str(img)}),
        ("read_document", "transcriber", {"file_path": "doc.pdf", "mode": "vision", "user_id": "u1"}),
        ("web_search", "handyman", {"query": "q", "llm_filter": True, "TAVILY_API_KEY": "offline",
                                    "workspace_path": str(tmp / "ws")}),
        ("web_search", "handyman", {"query": "q", "llm_deep": True, "TAVILY_API_KEY": "offline",
                                    "workspace_path": str(tmp / "ws")}),
        ("deep_research", "handyman", {"topic": "t", "user_id": "u1"}),
        ("deep_research_rlm", "coder", {"task": "t", "index_name": "papers", "user_id": "u1"}),
        ("cross_document_analysis", "editor", {"task": "t", "index_name": "papers", "user_id": "u1"}),
        ("paper_triage", "editor", {"query": "t", "index_name": "papers", "user_id": "u1"}),
        ("analyze_corpus", "editor", {"task": "t", "index_name": "papers", "user_id": "u1",
                                      "workspace_path": str(tmp / "ws")}),
        ("summarize_document_pages", "editor", {"index_name": "papers", "user_id": "u1"}),
        ("smart_query", "coder", {"query": "compare all papers", "index_name": "papers", "mode": "deep",
                                  "user_id": "u1"}),   # dispatches to deep_research_rlm
    ]
    import backend.retrieval.models  # noqa: F401  (registers the collection tables smart_query reads first)
    from backend.database import engine as db_engine
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(db_engine)   # the scratch database, empty: smart_query routes on size 0
    n_bodies, n_recs = len(Stub.bodies), len(records(sink))
    for tool, role, args in cases:
        params = inspect.signature(registry.tools[tool].func).parameters
        args = {k: v for k, v in args.items() if k in params}
        missing = [p for p, v in params.items() if v.default is inspect.Parameter.empty and p not in args
                   and p != "task_id"]
        for p in missing:                       # required arguments this list does not name
            args[p] = "t"
        del asked[:]
        e = cause(lambda: call(server, tool, {**args, "task_id": no[role]}))
        check(f"5 {tool}: no {role!r} role (default set) fails the tool with LockError naming it",
              isinstance(e, LockError) and f"'{role}'" in str(e) and asked[-1:] == [role],
              f"asked {asked}, {type(e).__name__}: {str(e)[:70]}")
    check("5 the missing-role refusals sent nothing and wrote no record",
          len(Stub.bodies) == n_bodies and len(records(sink)) == n_recs)
finally:
    rc.agent_model = _agent_model

SOURCES = ["backend/mcp/custom/vision_tools.py", "backend/retrieval/agents/transcriber.py",
           "backend/mcp/custom/rag_tools.py", "backend/mcp/custom/web_search.py"]


def code_only(path: Path) -> str:
    """The module's code tokens joined without spaces: strings (docstrings included) and comments dropped."""
    with open(path, "rb") as f:
        return "".join(t.string for t in tokenize.tokenize(f.readline)
                       if t.type not in (tokenize.STRING, tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                                         tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING))


other = {s: [w for w in ("resolve_model_for_chat", "agent_roles.get", "agent_roles[", "user.settings", "_run_model",
                         "_run_role_model") if w in code_only(MENTORI / s)] for s in SOURCES}
lookups = {s: code_only(MENTORI / s).count("rc.agent_model(") for s in SOURCES}
check("5 the four modules hold no other role lookup in their code; each calls rc.agent_model",
      not any(other.values()) and all(lookups.values()), json.dumps({"other": other, "agent_model calls": lookups}))

# 6. every tool that can call a model takes task_id: a tool reaches a model call when its source holds a marker, or
# calls another tool that does (smart_query dispatches to the rag tools), to a fixed point
MARKERS = ("agent_model", "ModelRouter", "lock_adapter", "la.chat", "la.generate", "_read_image_internal",
           "get_transcriber", "_filtered_web_search", "_deep_web_research")
src = {n: inspect.getsource(registry.tools[n].func.__wrapped__) for n in REAL}
calling = {n for n in REAL if any(m in src[n] for m in MARKERS)}
while True:
    more = {n for n in REAL - calling if any(re.search(rf"\b{c}\(", src[n]) for c in calling)}
    if not more:
        break
    calling |= more
calling = sorted(calling)
without = [n for n in calling if not ts.takes_task_id(registry.tools[n].func)]
check(f"6 the {len(calling)} tools whose source reaches a model call, directly or through another tool, all take "
      f"task_id", calling == sorted(MODEL_TOOLS) and not without, f"{calling}; without task_id: {without}")

stub.shutdown()
print(f"records in {sink}")
print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
