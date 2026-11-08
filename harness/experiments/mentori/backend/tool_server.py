"""
Mentori's tool server (copied from Mentori-paper 83a4091, B8), serving one run of an experiment.

    MENTORI_RUN_SINK=<sink> python3 -m backend.tool_server

MENTORI_RUN_SINK names the run's sink, the directory every record of the run goes to. The experiment writes two
kinds of sidecar there with experiments.runner.run_context.dump before the server starts and before each item:

    <sink>/ctx/run.json         the run-level context (item_id None); required, read once at start
    <sink>/ctx/<task_id>.json   one item's context, under the Mentori task id the item runs as

Each tool call runs inside a run context (run_context.run):
    - a tool with a task_id parameter runs in the item context of the task_id it is given, loaded from
      <sink>/ctx/<task_id>.json for that call. A call with no task_id, the reserved task_id "run", a missing sidecar,
      or a sidecar of another run or sink, or one whose tools differ from the run's, is refused before the tool runs;
    - a tool with no task_id parameter runs in the run-level context. Such a tool makes no model call (every tool
      that calls a model takes task_id: read_image, describe_figure, compare_images, read_document, deep_research,
      deep_research_rlm, cross_document_analysis, paper_triage, analyze_corpus, summarize_document_pages,
      web_search, and smart_query through the rag tools it dispatches to), and the lock adapter refuses a model call
      in a context with item_id None.

A refusal (RunContextError here, or a LockError or RunContextError a tool raises) is re-raised by the wrapper as
LockRefusal, whose text starts with TOOL_REFUSAL_MARKER (backend/agents/session_context.py) and whose cause is the
refusal. It reaches the MCP client as a call result with isError=True and the text "Error executing tool <name>:
[LOCK REFUSAL] <type>: <refusal>" (mcp/server/fastmcp/tools/base.py, mcp/server/lowlevel/server.py
_make_error_result). The orchestrator's executor and coder read isError and the marker and fail the question as a
setup error (Q38, D69; agents/orchestrator/run_records.py ToolRefusal). Any other exception a tool raises keeps
FastMCP's text without the marker, and the planner sees it as Mentori's recovery expects (Q39, D69).

The server refuses to start when a tool module fails to import (registry.failed): the submitted server printed the
error and served without that module's tools.

Which tools the server registers comes from the run-level context's tools field. As submitted, the server
registered every discovered tool except those in the admin database's disabled list (Mentori-paper
backend/tool_server.py:15-32). That list as of the submitted runs is not available, so tools None means every
discovered tool, and a list registers exactly those tools (a name the server does not have refuses the start).
The admin database is not read.
"""
import functools
import inspect
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from backend.mcp.registry import registry

_REPO = Path(__file__).resolve().parents[3]   # the reanalysis repository, whose experiments/runner this module calls
if str(_REPO) not in sys.path:
    sys.path.append(str(_REPO))               # appended, so the Mentori copy's own packages keep precedence

from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError  # noqa: E402

from backend.agents.session_context import TOOL_REFUSAL_MARKER  # noqa: E402
from backend.logging_config import setup_logging  # noqa: E402
logger = setup_logging()

SINK_VAR = "MENTORI_RUN_SINK"


class LockRefusal(RuntimeError):
    """A lock refusal inside a tool call (LockError or RunContextError, the cause), marked for the client (Q38)."""


def _refusal(e: Exception) -> LockRefusal:
    return LockRefusal(f"{TOOL_REFUSAL_MARKER} {type(e).__name__}: {e}")


def load_run(sink: Path, known: set) -> rc.RunContext:
    """The run-level context <sink>/ctx/run.json. Raises RunContextError when it is missing, names another sink,
    has an item_id, or enables a tool that is not in `known`."""
    sink = Path(sink).resolve()
    path = rc.sidecar(rc.RUN_TASK_ID, sink)
    if not path.is_file():
        raise rc.RunContextError(f"{path} does not exist: the experiment writes the run-level context there "
                                 f"(run_context.dump({rc.RUN_TASK_ID!r})) before the tool server starts")
    run = rc.load(path)
    if run.sink != sink:
        raise rc.RunContextError(f"{path} names the sink {run.sink}, not {sink}")
    if run.item_id is not None:
        raise rc.RunContextError(f"{path} has item_id {run.item_id!r}; the run-level context has none")
    unknown = sorted(set(run.tools or ()) - set(known))
    if unknown:
        raise rc.RunContextError(f"{path} enables tools this server does not have: {unknown}")
    return run


def enabled(run: rc.RunContext, known) -> list:
    """The tools to register: the run's tools field, or every known tool when it is None."""
    return sorted(known) if run.tools is None else list(run.tools)


def takes_task_id(func) -> bool:
    return "task_id" in inspect.signature(func).parameters


def restore(name: str, has_task_id: bool, kwargs: dict, run: rc.RunContext) -> rc.RunContext:
    """The run context of one call to tool `name` (see the module docstring). Raises RunContextError, so the call
    is refused before the tool runs."""
    if not has_task_id:
        return run
    task_id = kwargs.get("task_id")
    if not task_id:
        raise rc.RunContextError(f"{name}: takes task_id, and the call has none, so it has no item; refused")
    if task_id == rc.RUN_TASK_ID:
        raise rc.RunContextError(f"{name}: task_id {task_id!r} is reserved for the run-level context; refused")
    path = rc.sidecar(task_id, run.sink)
    if not path.is_file():
        raise rc.RunContextError(f"{name}: task_id {task_id!r} has no sidecar {path}; refused")
    ctx = rc.load(path)
    if ctx.sink != run.sink or ctx.run_id != run.run_id:
        raise rc.RunContextError(f"{name}: {path} is run {ctx.run_id!r} with sink {ctx.sink}, not this server's run "
                                 f"{run.run_id!r} with sink {run.sink}; refused")
    if ctx.item_id is None:
        raise rc.RunContextError(f"{name}: {path} has no item_id; refused")
    if ctx.tools != run.tools:
        raise rc.RunContextError(f"{name}: {path} enables tools {ctx.tools!r}, the run {run.tools!r}; refused")
    logger.info(f"Tool {name}: run {ctx.run_id} item {ctx.item_id} arm {ctx.arm} draw {ctx.draw} ({path})")
    return ctx


def in_run(name: str, func, run: rc.RunContext):
    """func wrapped so that each call runs inside the run context restore() gives. The signature stays func's,
    so FastMCP builds the same tool schema. A refusal, from restore() or from the tool, is re-raised as LockRefusal
    (Q38, D69); every other exception passes unchanged."""
    has_task_id = takes_task_id(func)
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                with rc.run(restore(name, has_task_id, kwargs, run)):
                    return await func(*args, **kwargs)
            except (LockError, rc.RunContextError) as e:
                raise _refusal(e) from e
        wrapper = async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                with rc.run(restore(name, has_task_id, kwargs, run)):
                    return func(*args, **kwargs)
            except (LockError, rc.RunContextError) as e:
                raise _refusal(e) from e
        wrapper = sync_wrapper
    wrapper.__signature__ = inspect.signature(func)
    return wrapper


def build(sink: Path) -> FastMCP:
    """The FastMCP server for the run whose sink is `sink`, with the run's tools registered."""
    registry.discover_tools()
    if registry.failed:
        raise rc.RunContextError(f"tool modules failed to import, so their tools would be missing from the run: "
                                 f"{registry.failed}")
    logger.info(f"Discovered {len(registry.tools)} tools.")
    run = load_run(sink, set(registry.tools))
    names = enabled(run, registry.tools)
    logger.info(f"Run {run.run_id}, sink {run.sink}: {len(names)} tools enabled "
                f"({'every tool' if run.tools is None else 'the run context tools field'})")
    # Host/Port to ensure correct binding and allowed_hosts configuration
    mcp = FastMCP("Mentori Tool Server", host="0.0.0.0", port=8777)
    for name in names:
        meta = registry.tools[name]
        logger.info(f"Registering MCP tool: {name}")
        mcp.tool(name=name, description=meta.description)(in_run(name, meta.func, run))
    return mcp


if __name__ == "__main__":
    if not os.environ.get(SINK_VAR):
        raise SystemExit(f"{SINK_VAR} names no run sink: every tool call runs in a run context read from "
                         f"<sink>/ctx/, so the server has nothing to serve")
    server = build(Path(os.environ[SINK_VAR]))
    logger.info("Starting Mentori MCP Server on port 8777...")
    server.run(transport='sse')
