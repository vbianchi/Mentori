"""
What the orchestrator records about a run, and which failures stop an answer (A5, A6, D37, D69).

    from backend.agents.orchestrator import run_records as rr
    try: ...
    except rr.REFUSALS: raise                  # a lock refusal is a setup error: it fails the question (Q38, D69)
    except Exception as e: status = rr.failure(e)   # any other failure keeps Mentori's recovery and is recorded
    off = rr.offset(rr.CALLS)                  # before a tool call
    calls = rr.since(rr.CALLS, off)            # after it: the call records the tool wrote for this item (Q39)

A refusal comes in two forms. In this process the lock adapter raises LockError or RunContextError before any
request. Inside the tool server the wrapper turns the same exceptions into a tool result with isError=True whose text
carries TOOL_REFUSAL_MARKER (backend/tool_server.py); the executor and the coder raise ToolRefusal on it. Neither form
is caught by the orchestrator's recovery paths, so it leaves orchestrated_chat and the entry point records the item
as a setup error. A tool error whose text carries RUN_STOP_MARKER (the reranker failed to load, A4) raises RunStop
the same way, and the entry point records it and stops the run. ToolRefusal and RunStop are both SetupError.

The record readers take the lines appended to a file of the run's sink after a byte offset and keep those of the
current item (run_id, item_id and run_draw of the run context). Within one item the engine waits for each tool call,
so the lines a tool call appends between the two reads belong to that call; a late line of another item (a memory
consolidation still running) is dropped by the item filter.
"""
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from backend.agents import lock_adapter
from backend.agents.session_context import RUN_STOP_MARKER, TOOL_REFUSAL_MARKER
from experiments.runner import run_context as rc
from experiments.runner.lock import LockError

CALLS = "calls.jsonl"                # lock_adapter's call records (run_context.append's default file)
RETRIEVALS = "retrievals.jsonl"      # backend/retrieval/retriever.py RETRIEVALS: one record per retrieve() (D37, D70)
TOOL_RECORDS = "tool_records.jsonl"  # what a tool reports about itself: smart_query's routing, the passages
                                     # query_documents returned verbatim (rag_tools.py)

REFUSALS = (LockError, rc.RunContextError)


class SetupError(RuntimeError):
    """The run is set up wrong, so the question fails as a setup error and stays to do (Q38, D69). The orchestrator's
    recovery paths re-raise it; the entry point records it."""


class ToolRefusal(SetupError):
    """A lock refusal inside a tool, read from the tool server's result (isError and TOOL_REFUSAL_MARKER). A setup
    error: it fails the question (Q38, D69)."""


class RunStop(SetupError):
    """A4 (D67): an error inside a tool after which the run cannot go on (the reranker failed to load), read from the
    tool server's result (isError and RUN_STOP_MARKER). Recorded as a setup error; the entry point then stops the run."""


def _result_has(mcp_result, marker: str) -> bool:
    if not getattr(mcp_result, "isError", False):
        return False
    return any(marker in getattr(c, "text", "") for c in (mcp_result.content or []))


def is_refusal_result(mcp_result) -> bool:
    """True when an MCP tool result is the tool server's refusal (isError and the marker in its text)."""
    return _result_has(mcp_result, TOOL_REFUSAL_MARKER)


def is_run_stop_result(mcp_result) -> bool:
    """True when an MCP tool result is an error after which the run stops (isError and RUN_STOP_MARKER; A4)."""
    return _result_has(mcp_result, RUN_STOP_MARKER)


def failure(e: BaseException) -> Dict[str, Any]:
    """A failure as a record: status "error", the exception's type and text, and for a model call that ended with a
    status other than ok or length (lock_adapter.LockCallError) the call's own status and seq."""
    out = {"status": "error", "error": f"{type(e).__name__}: {e}", "call_status": None, "call_seq": None}
    if isinstance(e, lock_adapter.LockCallError):
        out["call_status"] = e.record.get("status")
        out["call_seq"] = e.record.get("seq")
    return out


def _path(file: str) -> Path:
    return rc.current().sink / file


def offset(file: str) -> int:
    """The current size in bytes of <sink>/<file> (0 when it does not exist yet)."""
    p = _path(file)
    return p.stat().st_size if p.is_file() else 0


def since(file: str, start: int) -> List[Dict[str, Any]]:
    """The records of the current item appended to <sink>/<file> after byte `start`, in file order."""
    ctx = rc.current()
    p = _path(file)
    if not p.is_file():
        return []
    with open(p, "rb") as f:
        # one byte before `start`: when it is not a newline, `start` fell inside a line another writer had begun,
        # and that line's tail is dropped rather than parsed as a record
        f.seek(max(start - 1, 0))
        data = f.read()
    if start > 0:
        data = data[1:] if data[:1] == b"\n" else data[data.find(b"\n") + 1:] if b"\n" in data else b""
    # only whole lines: a line another task of this process is still writing (it ends without a newline) is not read
    out = []
    for line in data.decode("utf-8").split("\n")[:-1]:
        if not line.strip():
            continue
        rec = json.loads(line)
        if (rec.get("run_id"), rec.get("item_id"), rec.get("run_draw")) == (ctx.run_id, ctx.item_id, ctx.draw):
            out.append(rec)
    return out


def call_summary(rec: Dict[str, Any]) -> Dict[str, Any]:
    """The fields of a call record that an answer's record repeats; the whole record stays in calls.jsonl (by seq
    and ctx_uid)."""
    keys = ("seq", "ctx_uid", "pid", "provider", "model", "role", "status", "stop_reason", "error", "call_site",
            "prompt_tokens", "output_tokens", "thinking_tokens", "wall_s", "passages")
    return {k: rec.get(k) for k in keys}


def passages_carried(results: Iterable[Dict[str, Any]]) -> List[str]:
    """The passage ids that the given step results put whole into a prompt: the ids a tool returned verbatim
    (passage_ids), for each result whose content is that tool output undistilled. In first-seen order."""
    ids: List[str] = []
    for r in results:
        if r.get("distilled"):
            continue
        for i in r.get("passage_ids") or []:
            if i and i not in ids:
                ids.append(i)
    return ids


def set_passages(ids: Optional[List[str]]) -> None:
    """run_context.set_passages: the ids the next model call in this task carries (A6, D37); [] for none."""
    rc.set_passages(list(ids or []))
