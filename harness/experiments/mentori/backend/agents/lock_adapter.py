# backend/agents/lock_adapter.py
"""
Lock adapter: every model call ModelRouter makes goes through experiments/runner under experiments/LOCK.toml
(A1 and A2 of experiments/fix_design/decisions.html, D67; design in experiments/fix_design/calls.md O1).

    from backend.agents import lock_adapter as la
    out = la.generate("ollama::qwen3-coder:30b", prompt)                 # inside experiments.runner.run_context.run()
    out = la.chat("gemini::gemini-3-flash-preview", messages, tools=tools)
    out = la.generate("anthropic::claude-haiku-4-5", prompt)            # B11: T2's Haiku generator, text only
    out = await la.agenerate(...)  /  await la.achat(...)                # asyncio.to_thread; the run context carries over
    with la.judge():                                                     # role "judge": the lock's judge only
        out = la.generate("ollama::devstral-small-2:24b", prompt)
    with la.candidate(2):                                                # candidate 2 of a best-of-n step (seed d*1000+2)
        out = la.chat(...)

Every Ollama call goes to the run context's server for its model, ctx.server_for(tag): the context's servers map
where it names the tag (D158 (2), exp_01's local generator beside the verifier), else its base_url.

What is sent comes only from the lock: the model is the identifier's name (provider prefix and [think:x] suffix
removed), the role comes from the role scope (default "generator"), the draw and the thinking factor from the run
context, the candidate from the candidate scope. The caller's options, think argument and [think:x] suffix are written
into the record as caller_asked and never sent. A call outside a run context, a model the run does not allow in that
role, a claude:: model (the Anthropic route is anthropic::), Gemini or Anthropic in a role other than generator, tools
or images for Anthropic (B11: not mapped, T2 sends none), a caller system prompt for generate (no caller passes one;
calls.md F4 G2) and a call in the run-level context (item_id None, the context of the tool server's tools that take no
task_id) are refused before any request. Anthropic calls go through experiments/runner/anthropic_client (B11).

Return shapes are the ones Mentori's callers read (calls.md "What the adapter translates", cuts.md A0 (c)):
    generate -> {"response", "thinking", "done_reason", "prompt_eval_count", "eval_count", "lock_record"}
    chat     -> {"message": {"role": "assistant", "content", "thinking", "tool_calls"[, "_gemini_parts"]},
                 "response", "done_reason", "prompt_eval_count", "eval_count", "lock_record"}
chat's "response" is the message content again (cuts.md A0 (c)), for the callers that fall back to it. lock_record is
the record as written; its repr is "<lock_record seq N>", so a caller that stores str(result) never stores the
prompt or the messages the record holds.
tool_calls are in Ollama's shape, {"function": {"name", "arguments"}} (plus "id" when the provider gives one), which
step_executor._extract_tool_calls reads; Gemini's functionCall parts are mapped into it and the raw parts are returned
as _gemini_parts for the caller to echo back. done_reason is "stop" or "length". The two counts are the record's
prompt_tokens and output_tokens, 0 where the provider gave none (as Mentori's Gemini client returned them); the record
keeps None. For Gemini, eval_count is the answer tokens only, as before; thinking tokens are in the record.

A status other than "ok" or "length" (error, stalled, and Gemini's finish reasons not named below:
finish_reason_unspecified, image_other, no_image, image_recitation, missing_thought_signature, pup_limited_disabled,
continuation) raises LockCallError(record) after the record is written; "length" returns the text with done_reason "length". A
Gemini "empty" or "blocked" reply (gemini_client.EMPTY_TEXT_STATUSES; D83 Q145, D89 Q145 O3) returns with done_reason
"stop", no tool call and empty text (a blocked reply "" and no parts to echo; an empty reply its blank text and parts,
as before D89), as Mentori's submitted Gemini client returned a reply with no text (models/gemini.py:166-176,
:348-365, passed on unchanged by model_router.py at 96e2193:216-222, :309-318). A Gemini "recitation",
"malformed_function_call" or "malformed_response" reply (D90 Q1, Q2), or one ended for "language", "other",
"unexpected_tool_call" or "too_many_tool_calls" (D92 Q188; all gemini_client.PASSED_ON_STATUSES) returns with
done_reason "stop" and what the stream held, as an "ok" reply does: its text, thinking, function calls and parts
("" and none when it held none), as the submitted chat_completion passed on every text part and function call of a
reply without reading its finishReason (models/gemini.py:327-347). The record keeps the status and Google's reason
(_finish, _returned). An Ollama
server that cannot be reached before the request is posted (its version or tag list unreadable) is recorded as
status error with nothing sent, and raises LockCallError the same way. The adapter does not retry (the Gemini
client's own Q29 resend rule applies, and the Anthropic client's Q170 rule, the same one). An Anthropic status
other than ok or length (error, stalled, refusal and the like) raises LockCallError as Gemini's does.

D80 V1 (audit F34, F35), D81 (Q136, Q138) and D83 (Q155), for a caller whose recovery reads them:
    except la.LockCallError as e: e.transient            # Ollama: "stalled", "tool-call parse error", "HTTP 500",
                                                         # "dropped connection", "error inside the stream", "no final
                                                         # chunk"; else None, and always None for Gemini
    with la.retry({"attempt": r, ...}):                  # retry r (1 to 3) of an Ollama generator call: seed + 1,000,000
                                                         # * r (D81), and the record carries "transient_retry": that
                                                         # dict, "retry": r and "seed_sent"
    with la.text_tool_calls(reader):                     # an Ollama chat with tools and no native tool call: the
                                                         # reader's calls become message["tool_calls"]
transient(record) names, for Ollama calls only, the failures Mentori's submitted step loop retried (step_executor's
string rule) and whose text under the lock no longer matches that rule. The submitted Ollama client asked with
stream false (96e2193 models/ollama.py:235) and raised every non-200 reply as "Ollama error (<status>)", so a server
failure reached its retry as "Ollama error (500)" whenever the server answered it with a 500. Under the lock every call
is streamed, and the same failure now arrives in one of three forms, none of which is that text: an HTTP 500 before
the stream begins, an error sent inside a stream that began with 200 OK, and a stream that ends without its final
chunk. ("HTTP 500" alone is not the submitted "Ollama error (500)": that equation, written here before D83 Q155,
overstated the match.) transient() names: Ollama's "error parsing tool call", which now arrives inside a 200 stream
(status error, the text as the server wrote it); a stall (status stalled), which that client raised as an httpx
timeout ("timed out"); an HTTP 500 before the stream (D81 Q138, "HTTP 500: ..." as ollama_client records it); a
dropped connection (Q138: the error names RemoteDisconnected, ConnectionResetError, "Connection reset by peer" or
"Server disconnected", httpx's text in the submitted client); and (D83 Q155) any other error sent inside the stream, a
mid-answer crash such as "model runner has unexpectedly stopped" ("error inside the stream": status error, the record
holds first_token_s, so a line was read, and the error is the server's text, not ollama_client's own "<exception
class>: <message>"), and a stream that ended without its final chunk ("no final chunk": ollama_client's "the stream
ended without a final chunk" when the stream closed between chunks, its "IncompleteRead: ..." when it closed partway
through one, review of 17 Oct F1). Which of these errors the submitted server answered with a 500 rather than another
status is UNVERIFIED (D83 Q155); an error that recurs on every try still fails after the 3 retries and is recorded.
A Gemini call is never transient: the submitted Gemini chat returned its error as a dict and never raised (96e2193
models/gemini.py:305-317), so no Gemini failure reached that retry; a Gemini call inside a retry scope is refused
before any request (LockError). The caller keeps its own retry count and backoff. Inside a retry scope the lock
builds the call with retry r = the scope's "attempt", so the call sends the lock's retry seed ([generation]
retry_seed; a lock without it refuses the call, it never resends the first try's seed); the record carries "retry":
r and "seed_sent": the seed in options_sent (None when nothing was sent).
Only chat() records "tool_calls_from_text" (achat and ModelRouter.chat_stream run chat(); generate() never records
it). Every chat() inside text_tool_calls carries the key. Only a chat on Ollama with tools given whose reply ended
"ok" with no native tool call passes its text to reader(text), which returns None or {"calls": [Ollama-shaped
calls], ...}; the key then holds the reader's dict whole ({"calls": [], "reader_error"} when the reader raised), and
the returned message carries the calls read when there are any. Any other chat in the scope (Gemini, no tools, a
status other than ok, a native tool call) records None, its native tool_calls returned as before. Outside the two
scopes no record carries any of these keys.

Every call appends one record to <sink>/calls.jsonl through run_context.append: the runner's record (with
session_id, code_commit and code_dirty, D92 Q199; an Anthropic record gets them here, an unreached Ollama
server's record in _unreached) plus provider,
role, caller_asked, call_site (the first stack frame outside this module and model_router.py; None when that frame
is asyncio's own, the router coroutine having been run as the task itself), and the request whole, copied before the
call: prompt_sent (generate) or messages_sent (chat; for Ollama the list as posted, the lock's date-fixed system prompt
included, checked against the runner's messages_sha256; for Gemini the messages as given, contents_sent being the
posted form; for Anthropic the messages as given, system_sent and messages_posted being the posted form), with images
replaced by their sha256s; tools_given (names and one sha256 of the caller's tools list). passages come from
run_context.passages().
"""
from __future__ import annotations

import asyncio
import copy
import json
import re
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[4]            # the reanalysis repository, whose experiments/runner this module calls
if str(_REPO) not in sys.path:
    sys.path.append(str(_REPO))     # appended, so the Mentori copy's own packages keep precedence

from experiments.runner import anthropic_client, gemini_client, ollama_client  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

from backend.agents.models.utils import parse_model_identifier  # noqa: E402

_SKIP = {_HERE, _HERE.parent / "model_router.py"}   # frames that are never the call site
_MENTORI = _HERE.parents[2]
_ASYNCIO = Path(asyncio.__file__).resolve().parent

_UNSET = object()                                   # _site not given: the call site is read from the stack here
_role: ContextVar[str] = ContextVar("lock_adapter_role", default="generator")
_candidate: ContextVar[Optional[int]] = ContextVar("lock_adapter_candidate", default=None)
_retry: ContextVar[Optional[dict]] = ContextVar("lock_adapter_retry", default=None)                 # D80 V1
_text_reader: ContextVar[Optional[Callable]] = ContextVar("lock_adapter_text_reader", default=None)  # D80 V1


class LockRecord(dict):
    """A call's record as written. Its repr names only the seq, so str() of a result that holds it never carries
    the prompt, the messages or the passages into a caller's stored answer."""

    def __repr__(self):
        return f"<lock_record seq {self.get('seq')}>"

    __str__ = __repr__


# D81 Q138: the texts of a dropped connection in an Ollama record (ollama_client writes "<exception class>: <message>";
# a reset while posting arrives wrapped in URLError, "<urlopen error [Errno 54] Connection reset by peer>")
_DROPPED = ("RemoteDisconnected", "ConnectionResetError", "Connection reset by peer", "Server disconnected")
# D83 Q155: ollama_client's own texts for a failure it saw (not an error the server sent): "<exception class>:
# <message>" (a Python class name, which starts with a capital; socket's gaierror and herror do not) and the stream
# that ended without its final chunk. The server's error texts (Go errors) start in lower case.
_CLIENT_TEXT = re.compile(r"^(?:[A-Z]\w*|gaierror|herror): ")
_NO_FINAL_CHUNK = "the stream ended without a final chunk"
# a chunked stream closed partway through a chunk: ollama_client records http.client.IncompleteRead (review F1)
_CUT_CHUNK = "IncompleteRead: "


def transient(record: dict) -> Optional[str]:
    """D80 V1 (audit F34), D81 Q138 and D83 Q155: for an Ollama record, "stalled" for a stall, "tool-call parse
    error" for Ollama's "error parsing tool call", "HTTP 500" for an HTTP 500 before the stream, "dropped connection"
    for an error naming a dropped connection (_DROPPED), "no final chunk" for a stream that ended without its final
    chunk (between chunks, or partway through one: IncompleteRead), and "error inside the stream" for any other
    error the server sent inside a stream that began with 200 OK (a line was read, first_token_s, and the text is not
    ollama_client's own, _CLIENT_TEXT); else None, and always None for another provider. These are the Ollama failures Mentori's submitted step loop retried (raised by its
    non-streaming Ollama client as "timed out", "Ollama error (500)" and httpx's "Server disconnected") whose text
    under the lock no longer names them; its Gemini client never raised, so it never retried a Gemini call."""
    if record.get("provider") != "ollama":
        return None
    if record.get("status") == "stalled":
        return "stalled"
    if record.get("status") != "error":
        return None
    err = str(record.get("error") or "")
    if err.startswith("error parsing tool call"):
        return "tool-call parse error"
    if err.startswith("HTTP 500"):
        return "HTTP 500"
    if any(d in err for d in _DROPPED):
        return "dropped connection"
    if err == _NO_FINAL_CHUNK or err.startswith(_CUT_CHUNK):
        return "no final chunk"
    if record.get("first_token_s") is not None and err and not _CLIENT_TEXT.match(err):
        return "error inside the stream"
    return None


class LockCallError(Exception):
    """A call that ended with a status other than ok or length. .record is the record written for it; .transient is
    transient(record) (D80 V1)."""

    def __init__(self, record: dict):
        self.record = record
        self.transient = transient(record)
        super().__init__(f"{record.get('model')}: status {record.get('status')}: {record.get('error')}")


@contextmanager
def role(name: str):
    """The role of every call made inside the block (and in what it starts): generator, judge or scorer."""
    if name not in rc.ROLES:
        raise LockError(f"unknown role {name!r}; the roles are {', '.join(rc.ROLES)}")
    token = _role.set(name)
    try:
        yield
    finally:
        _role.reset(token)


def judge():
    """The judge's scope: wrap the judge's model call in `with judge():`."""
    return role("judge")


@contextmanager
def candidate(k: int):
    """Candidate k (1 to 999) of an n-candidate step inside the draw; the lock sends seed draw * 1000 + k."""
    token = _candidate.set(k)
    try:
        yield
    finally:
        _candidate.reset(token)


@contextmanager
def retry(info: Optional[dict]):
    """D80 V1: the calls made inside the block are a retry after a transient failure; each one's record carries
    "transient_retry": info, "retry" and "seed_sent". D81: info["attempt"] is the retry number r (1 to 3) the lock's
    retry seed takes. info None is no scope (the caller's first try)."""
    token = _retry.set(None if info is None else dict(info))
    try:
        yield
    finally:
        _retry.reset(token)


@contextmanager
def text_tool_calls(reader: Callable[[str], Optional[dict]]):
    """D80 V1 (audit F35): an Ollama chat with tools inside the block that ended "ok" with no native tool call has
    its text read by reader; every chat inside the block records tool_calls_from_text (None when nothing was read);
    see the module's docstring."""
    token = _text_reader.set(reader)
    try:
        yield
    finally:
        _text_reader.reset(token)


def call_site() -> Optional[str]:
    """The first stack frame outside this module and model_router.py, as 'path:line function' (path relative to
    the Mentori copy, else to the repository). None when that frame is asyncio's own: the router's coroutine was
    run as a task with no awaiting caller (every call site in the copy awaits the router directly)."""
    f = sys._getframe(1)
    while f is not None:
        p = Path(f.f_code.co_filename)
        try:
            p = p.resolve()
        except OSError:
            pass
        if p.is_relative_to(_ASYNCIO):
            return None
        if p not in _SKIP:
            for base in (_MENTORI, _REPO):
                if p.is_relative_to(base):
                    p = p.relative_to(base)
                    break
            return f"{p}:{f.f_lineno} {f.f_code.co_name}"
        f = f.f_back
    return None


def _jsonable(value):
    """value as JSON data for the record; anything JSON cannot hold is kept as its repr."""
    return None if value is None else json.loads(json.dumps(value, default=repr))


def _route(model_identifier: str):
    """(run context, provider, model name, [think:x] suffix or None, role). Refuses before any request."""
    ctx = rc.current()
    if ctx.item_id is None:
        raise LockError(f"{model_identifier}: the run-level context (item_id None) makes no model call; every call "
                        "belongs to an item (a tool that calls a model takes task_id); nothing was sent")
    parsed = parse_model_identifier(model_identifier)
    name = parsed.model_name
    suffix = None
    if "[" in model_identifier and "]" in model_identifier:
        suffix = model_identifier[model_identifier.index("["):model_identifier.index("]") + 1]
    who = _role.get()
    if parsed.provider == "claude":
        raise LockError(f"{model_identifier}: the Anthropic route is 'anthropic::<model>' (B11); nothing was sent")
    if parsed.provider not in ("ollama", "gemini", "anthropic"):
        raise LockError(f"{model_identifier}: unknown provider {parsed.provider!r}; nothing was sent")
    cloud = {"gemini": "Gemini", "anthropic": "Anthropic"}.get(parsed.provider)
    if cloud and who != "generator":
        raise LockError(f"{name}: {cloud} runs only as a generator, not as {who!r}; the lock's instruments are Ollama")
    if parsed.provider == "gemini" and _retry.get() is not None:
        raise LockError(f"{name}: a Gemini call is never retried (D80 V1, D81: the submitted Gemini chat never raised); "
                        "nothing was sent")
    if parsed.provider == "anthropic" and _retry.get() is not None:
        raise LockError(f"{name}: an Anthropic call is never retried (B11, as Gemini); nothing was sent")
    rc.check_model(name, who)
    return ctx, parsed.provider, name, suffix, who


def _retry_number() -> Optional[int]:
    """D81: the retry scope's "attempt" (the lock checks it is 1 to 3), or None outside a retry scope."""
    again = _retry.get()
    if again is None:
        return None
    if "attempt" not in again:
        raise LockError(f"a retry scope names no attempt ({again!r}); the retry seed needs it (D81); nothing was sent")
    return again["attempt"]


def _ollama_call(lock, ctx, name: str, who: str):
    """The OllamaCall the lock builds: a generator takes the run's draw and thinking factor, an instrument neither;
    inside a retry scope the retry number (D81), which an instrument refuses."""
    gen = who == "generator"
    return lock.ollama(name, role=who, draw=ctx.draw if gen else None, thinking=ctx.thinking if gen else None,
                       candidate=_candidate.get(), retry=_retry_number())


def _asked(method, model_identifier, suffix, options, think, tools, system, images) -> dict:
    return {"method": method, "model_identifier": model_identifier, "think_suffix": suffix,
            "options": _jsonable(options), "think": _jsonable(think), "tools": bool(tools),
            "system": system is not None, "images": len(images) if images else 0}


def _without_images(messages: list) -> list:
    """The messages for the record: each message's images replaced by their sha256s (images_sha256)."""
    out = []
    for m in messages:
        m = dict(m)
        if "images" in m:
            m["images_sha256"] = [ollama_client.image_sha256(im) for im in (m.pop("images") or [])]
        out.append(m)
    return out


def _count(v) -> int:
    return v if isinstance(v, int) else 0


def _empty_text(record: dict) -> bool:
    """D89 (Q145 O3): a Gemini reply that returns to the caller as empty text (gemini_client.EMPTY_TEXT_STATUSES)."""
    return record.get("provider") == "gemini" and record["status"] in gemini_client.EMPTY_TEXT_STATUSES


def _gemini_returns(record: dict) -> bool:
    """D89, D90: a Gemini reply that returns to the caller although its status is not ok or length
    (gemini_client.RETURNED_STATUSES: empty, blocked, recitation, malformed_function_call, malformed_response, and
    since D92 Q188 language, other, unexpected_tool_call, too_many_tool_calls)."""
    return record.get("provider") == "gemini" and record["status"] in gemini_client.RETURNED_STATUSES


def _finish(record: dict) -> str:
    """done_reason for a call that returns: "stop" (status ok, or a Gemini status in RETURNED_STATUSES) or "length".
    Any other status raises. D83 Q145 and D89 (Q145 O3): gemini_client labels a reply with no text and no function
    call "empty" (STOP: "ok" before Q145; no finishReason: "error" before D89) and a reply Google blocked "blocked";
    each returns to the caller as empty text (_returned), as Mentori's submitted Gemini client returned every reply
    with no text, "" with an empty_reason and never an error (models/gemini.py:166-176 generate_completion, :348-365
    chat_completion; PROMPT_BLOCKED, SAFETY, NO_CANDIDATES and EMPTY_CONTENT alike, :46-110). D90: a recitation stop
    (Q1) and a malformed_function_call or malformed_response reply (Q2) return with what the stream held (_returned),
    as the submitted client took any reply's parts without reading its finishReason (:327-347). The status and
    Google's reason are the record's."""
    if record["status"] == "ok" or _gemini_returns(record):
        return "stop"
    if record["status"] == "length":
        return "length"
    raise LockCallError(record)


def _returned(record: dict) -> tuple:
    """(text, thinking, raw parts) the caller receives. A blocked reply returns none of what the stream held before
    Google stopped it (D89: empty text). A recitation stop returns the text the stream held before Google stopped it
    (D90 Q1), and a malformed_function_call or malformed_response reply what it held (D90 Q2), as an ok reply does.
    The submitted client called generate_content without streaming (models/gemini.py:147, :299) and returned whatever
    text parts the final reply held; whether Google's non-streamed reply to a blocked, recited or malformed answer
    holds the text made before the stop is UNVERIFIED (D90 Q1 passes the streamed text on). An empty reply returns
    its blank text as before. The record keeps everything the stream held."""
    if _empty_text(record) and record["status"] != "empty":
        return "", "", []
    return record["text"], record["thinking_text"], record.get("raw_parts") or []


def _append(rec: dict, provider: str, who: str, asked: dict, site: Optional[str], **extra) -> LockRecord:
    again = _retry.get()
    if again is not None:
        extra["transient_retry"] = again                # D80 V1: this call retries a transient failure
        extra["retry"] = again.get("attempt")           # D81: the retry number its seed took
        extra["seed_sent"] = (rec.get("options_sent") or {}).get("seed")   # None when nothing was sent
    # D92 Q199: every record carries session_id, code_commit and code_dirty; the Ollama and Gemini records have them
    # from their client, an Anthropic record gets them here (anthropic_client does not write them)
    prov = {k: v for k, v in ollama_client.provenance().items() if k not in rec}
    return LockRecord(rc.append({**rec, **prov, "provider": provider, "role": who, "caller_asked": asked,
                                 "call_site": site, **extra}))


def _unreached(call, base_url: str, e: OSError) -> dict:
    """The record of an Ollama call that failed before its request was posted: the runner reads the server's
    version and tag list first, outside its own error handling, so an OSError (URLError included) that leaves
    ollama_client.generate or chat comes from there. Status error, nothing sent."""
    return {"model": call.model, "role": call.role, "draw": call.draw, "candidate": call.candidate,
            "thinking": call.thinking, "options_sent": None, "model_digest": None, "server": base_url.rstrip("/"),
            "ollama_version": None, "lock_sha256": call.lock_sha256, "passages": rc.passages(),
            "status": "error", "stop_reason": None,
            "error": f"before the request was posted: {type(e).__name__}: {e}", "text": "", "thinking_text": "",
            "prompt_tokens": None, "output_tokens": None, "wall_s": None, "load_s": None, "prompt_eval_s": None,
            "eval_s": None, "total_s": None, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **ollama_client.provenance()}                         # D92 Q199


def generate(model_identifier: str, prompt: str, system: Optional[str] = None, images: Optional[List[str]] = None,
             options: Optional[Dict[str, Any]] = None, think: Union[bool, str, None] = None,
             _site: Any = _UNSET, _method: str = "generate") -> Dict[str, Any]:
    """One completion under the lock. images: base64 strings (Ollama only)."""
    site = call_site() if _site is _UNSET else _site
    ctx, provider, name, suffix, who = _route(model_identifier)
    asked = _asked(_method, model_identifier, suffix, options, think, None, system, images)
    if system is not None:
        raise LockError("generate takes no caller system prompt (no caller passes one, calls.md F4 G2); "
                        "nothing was sent")
    lock = load()
    if provider == "ollama":
        call = _ollama_call(lock, ctx, name, who)
        try:
            rec = ollama_client.generate(ctx.server_for(name), call, prompt, passages=rc.passages(), images=images)
        except OSError as e:
            rec = _unreached(call, ctx.server_for(name), e)
    elif provider == "anthropic":
        if images:
            raise LockError(f"{name}: images are not mapped for Anthropic generate; nothing was sent")
        rec = anthropic_client.generate(lock, name, ctx.draw, prompt, thinking=ctx.thinking, passages=rc.passages(),
                                        candidate=_candidate.get())
    else:
        if images:
            raise LockError(f"{name}: images are not mapped for Gemini generate; nothing was sent")
        rec = gemini_client.generate(lock, name, ctx.draw, prompt, thinking=ctx.thinking, passages=rc.passages(),
                                     candidate=_candidate.get())
    record = _append(rec, provider, who, asked, site, prompt_sent=prompt)
    done = _finish(record)
    text, thinking, _ = _returned(record)
    return {"response": text, "thinking": thinking, "done_reason": done,
            "prompt_eval_count": _count(record["prompt_tokens"]), "eval_count": _count(record["output_tokens"]),
            "lock_record": record}


def _ollama_tool_calls(provider: str, record: dict) -> list:
    """The record's tool calls in Ollama's shape: Ollama's as returned, Gemini's {"id", "name", "arguments"} as
    {"function": {"name", "arguments"}} with "id" when Gemini gave one. Anthropic's record has none (no tools sent)."""
    if provider == "ollama":
        return copy.deepcopy(record.get("tool_calls") or [])
    out = []
    for tc in record.get("tool_calls") or []:
        c = {"function": {"name": tc["name"], "arguments": copy.deepcopy(tc["arguments"])}}
        if tc.get("id"):
            c["id"] = tc["id"]
        out.append(c)
    return out


def chat(model_identifier: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
         options: Optional[Dict[str, Any]] = None, think: Union[bool, str, None] = None,
         _site: Any = _UNSET, _method: str = "chat") -> Dict[str, Any]:
    """One chat turn under the lock. tools: Ollama/OpenAI function tools, sent whole when the list is not empty
    (as Mentori's clients did)."""
    site = call_site() if _site is _UNSET else _site
    ctx, provider, name, suffix, who = _route(model_identifier)
    asked = _asked(_method, model_identifier, suffix, options, think, tools, None,
                   [im for m in messages for im in (m.get("images") or [])])
    tools = tools or None
    lock = load()
    sent = [dict(m) for m in messages]                         # copied before the call, as the runner copies them
    if provider == "ollama":
        call = _ollama_call(lock, ctx, name, who)
        if call.system is not None and not any(m.get("role") == "system" for m in sent):
            sent.insert(0, {"role": "system", "content": call.system})   # the list ollama_client.chat posts
        try:
            rec = ollama_client.chat(ctx.server_for(name), call, messages, passages=rc.passages(), tools=tools)
        except OSError as e:
            rec = {**_unreached(call, ctx.server_for(name), e), "tool_calls": []}
        verified = (None if rec.get("messages_sha256") is None
                    else ollama_client.canonical_sha256(sent) == rec["messages_sha256"])
    elif provider == "anthropic":
        if tools:
            raise LockError(f"{name}: tools are not mapped for Anthropic (T2 sends none); nothing was sent")
        rec = anthropic_client.chat(lock, name, ctx.draw, messages, thinking=ctx.thinking, passages=rc.passages(),
                                    candidate=_candidate.get())
        verified = None
    else:
        rec = gemini_client.chat(lock, name, ctx.draw, messages, tools=tools, thinking=ctx.thinking,
                                 passages=rc.passages(), candidate=_candidate.get())
        verified = None
    extra = {}
    reader = _text_reader.get()
    if reader is not None:
        # D80 V1 (audit F35): a call the model wrote as text, read only from a whole Ollama reply with no native call
        read = None
        if provider == "ollama" and tools and rec.get("status") == "ok" and not rec.get("tool_calls"):
            try:
                read = reader(rec.get("text") or "")
            except Exception as e:                      # the call's record is written whatever the reader does
                read = {"calls": [], "reader_error": f"{type(e).__name__}: {e}"}
        extra["tool_calls_from_text"] = _jsonable(read)
    record = _append(rec, provider, who, asked, site, messages_sent=_without_images(sent),
                     messages_sent_verified=verified, tools_given=ollama_client.tools_sent(tools), **extra)
    if verified is False:
        raise RuntimeError(f"{name}: messages_sent differs from what the runner hashed (seq {record['seq']}); "
                           "the adapter's copy of ollama_client.chat's system rule is out of date")
    done = _finish(record)
    text, thinking, parts = _returned(record)
    read = record.get("tool_calls_from_text")
    message = {"role": "assistant", "content": text, "thinking": thinking,
               "tool_calls": (copy.deepcopy(read["calls"]) if read and read.get("calls")
                              else [] if _empty_text(record) else _ollama_tool_calls(provider, record))}
    if provider == "gemini":
        message["_gemini_parts"] = copy.deepcopy(parts)
    return {"message": message, "response": text, "done_reason": done,
            "prompt_eval_count": _count(record["prompt_tokens"]), "eval_count": _count(record["output_tokens"]),
            "lock_record": record}


async def agenerate(model_identifier: str, prompt: str, system: Optional[str] = None,
                    images: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None,
                    think: Union[bool, str, None] = None, _method: str = "generate") -> Dict[str, Any]:
    """generate in a worker thread (asyncio.to_thread copies the run context and the role and candidate scopes).
    The call site is taken here, in the caller's thread."""
    return await asyncio.to_thread(generate, model_identifier, prompt, system=system, images=images, options=options,
                                   think=think, _site=call_site(), _method=_method)


async def achat(model_identifier: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                options: Optional[Dict[str, Any]] = None, think: Union[bool, str, None] = None,
                _method: str = "chat") -> Dict[str, Any]:
    """chat in a worker thread, as agenerate."""
    return await asyncio.to_thread(chat, model_identifier, messages, tools=tools, options=options, think=think,
                                   _site=call_site(), _method=_method)
