"""One Ollama call under the lock, streamed, with the record D37 asks for.

    rec = generate(base_url, lock.ollama(model, draw=1), prompt, passages=None)

Before the call: the server must run the lock's Ollama version and hold the model with the lock's digest.
The call streams, so there is no total timeout and no limit before the first token; after it, a gap of
[generation] stall_s seconds with no new token ends it as "stalled" (Q2). One request at a time per server,
across processes on this machine: every call holds an exclusive file lock for its server for its whole length
(waited_for_server_s records the wait). Nothing is cut: a prompt longer than the context comes
back from Ollama as an error (truncate false) and is recorded as status "error" with Ollama's message; an
answer that fills the context stops with done_reason "length" and is recorded as status "length".

    rec = chat(base_url, call, messages, tools=None)        # tools: Ollama's list, sent whole when given
    rec = generate(base_url, call, prompt, images=None)     # images: base64 strings, sent whole when given

The settings sent are recorded whole (options_sent, fields_sent, system_sent, format_sent); the prompt,
messages, tools and images are recorded by hash, never whole. request_sha256 is the sha256 of the exact bytes
posted; chat adds messages_sha256 (the messages after the lock's date-fixed system prompt is inserted) and
tools_sent (the tool names and one sha256 of the tools list), both over canonical JSON (sorted keys, no spaces,
UTF-8, a lone surrogate kept as its code unit); images_sha256 holds one sha256 per image, of its decoded bytes
(generate: the images argument; chat: each message's images, in message order). chat records tool_calls exactly
as the stream returns them (they can arrive in any chunk). The record keeps draw and candidate. Tools and images
are content: _checked compares only the model and the settings (options, fields, system) with the lock's.

busy_servers_on_machine (LOCK.toml [record], D83 Q146; D89 A1; D90): every call records a reading of the
machine-load sampler that runs beside the calls in this process (experiments/runner/machine_load.py: the OTHER Ollama
servers on this machine with a runner whose CPU time grew in a 1 s window, the called server left out (D90 O1, Q1);
read from Windows' process list where ps cannot see the server, as on the Beelink). At the call's end, with no wait,
the record is given the reading whose window overlapped the call (from the post to the last byte read; the one nearest
the call's middle when several did), else the latest one that ended before the post (D90 O2): busy_offset_s is the
seconds from the post to the end of that reading's window (negative: before the post), busy_overlap whether its
window overlapped the call, busy_how how it was taken or why the count is None (a server on another machine, a reading
that failed or shows no server on the called port, no overlapping reading and the latest one ended more than
machine_load.MAX_AGE_S before the post). The only wait is for the sampler's first reading, before the gate, and only
until machine_load.FIRST_WAIT_S after the sampler started in this process (machine_load.ready). A caller that passes
busy= gives the value itself, busy_how records that and busy_offset_s and busy_overlap are None. Records written
between D89 A1 and D90 carry busy_age_s instead (the latest reading's age at the post, -busy_offset_s with no
overlap) and count busy runners, not servers. Before D89 A1 the count was taken by a 1 s window inside the gate
before each call (1.5 s on the Beelink), which held the server for that long.
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import http.client
import json
import os
import socket
import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path
import time
import urllib.error
import urllib.request

from experiments.runner import machine_load
from experiments.runner.lock import LockError, OllamaCall, load

MEASURE = object()          # busy not given: the sampler's reading that overlapped the call (Q146, D89 A1, D90 O2)

# D92 Q199 (audit F17, F35): every call record names the session that wrote it and the code it ran on.
# session_id: one label per process, "<host>:<pid>:<UTC start>:<8 hex>", set when this module is imported and set
# again in a child forked after that (os.register_at_fork; multiprocessing's fork start method forks), so two
# processes (a restart, a second worker, a forked worker) never share one, and records of one process always do.
# code_commit: the commit checked out in the repository that holds this file (git rev-parse HEAD, read once, when this
# module is imported, so it names the code the process loaded, not a checkout made later; about 0.02 s; a forked child
# keeps its parent's, the code it inherited); code_dirty: True when tracked files under experiments/ or scripts/ differ
# from that commit (git status, untracked files not read), so the commit alone does not name the code; both None, with
# code_error, when git cannot say. git runs with the repository as its working directory, never on its command line
# (the Beelink helper's clone path names its port, which K1's busy guard reads from ps), and --no-optional-locks, so
# git status never takes index.lock from a commit running at the same moment.
_REPO = Path(__file__).resolve().parents[2]


def _new_session_id() -> str:
    return (f"{socket.gethostname()}:{os.getpid()}:{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}:"
            f"{uuid.uuid4().hex[:8]}")


SESSION_ID = _new_session_id()


def _after_fork_in_child() -> None:
    global SESSION_ID
    SESSION_ID = _new_session_id()


os.register_at_fork(after_in_child=_after_fork_in_child)
_code: dict | None = None


def code_version() -> dict:
    """{"code_commit", "code_dirty"} (plus "code_error" when git failed), read once per process."""
    global _code
    if _code is None:
        try:
            run = lambda *a: subprocess.run(["git", "--no-optional-locks", *a], cwd=_REPO,  # noqa: E731
                                            capture_output=True, text=True, timeout=60, check=True).stdout
            _code = {"code_commit": run("rev-parse", "HEAD").strip(),
                     "code_dirty": bool(run("status", "--porcelain", "--untracked-files=no", "--",
                                            "experiments", "scripts").strip())}
        except (OSError, subprocess.SubprocessError) as e:
            _code = {"code_commit": None, "code_dirty": None, "code_error": f"{type(e).__name__}: {e}"}
    return dict(_code)


def provenance() -> dict:
    """The fields D92 Q199 adds to every call record: session_id, code_commit, code_dirty (and code_error)."""
    return {"session_id": SESSION_ID, **code_version()}


code_version()                                             # at import: the code this process loaded



@contextmanager
def server_gate(base: str, rec: dict | None = None):
    """An exclusive lock on this server for one call, shared by every process on this machine (LOCK.toml [server]
    num_parallel = 1)."""
    path = f"/tmp/mentori-ollama-{hashlib.sha1(base.rstrip('/').encode()).hexdigest()[:12]}.lock"
    t0 = time.time()
    with open(path, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        if rec is not None:
            rec["waited_for_server_s"] = round(time.time() - t0, 3)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _arm(r, stall_s: float) -> None:
    """From the first token on, a read that waits stall_s seconds raises socket.timeout."""
    try:
        r.fp.raw._sock.settimeout(stall_s)
    except AttributeError as e:                                   # never run without the stall rule
        raise RuntimeError("cannot set the stall timeout on this response") from e


def _get(url: str) -> dict:
    """A small metadata request (version, tags, ps). 600 s, the lock's stall_s: a server busy with a long prompt can
    take more than 30 s to answer one, which failed a whole RAGChecker answer on the Beelink (15 October)."""
    with urllib.request.urlopen(url, timeout=600) as r:
        return json.loads(r.read())


def server_state(base: str, model: str) -> tuple[str, str | None]:
    version = _get(f"{base}/api/version")["version"]
    digest = next((m["digest"] for m in _get(f"{base}/api/tags")["models"] if m["name"] == model), None)
    return version, digest


def _s(ns):
    return None if ns is None else round(ns / 1e9, 3)


def canonical_sha256(obj) -> str:
    """sha256 of obj as canonical JSON: sorted keys, no spaces, UTF-8 (the same list in any key order, one hash).
    A lone surrogate, which the posted JSON sends as a \\u escape, is encoded as its code unit (surrogatepass)."""
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                          .encode("utf-8", "surrogatepass")).hexdigest()


def image_sha256(im) -> str:
    """sha256 of one image's decoded bytes. The image must be a base64 str; \\r and \\n (line-wrapped base64) are
    skipped for the hash and the string is sent as given. Anything else raises ValueError before the call."""
    if not isinstance(im, str):
        raise ValueError(f"an image must be a base64 str, not {type(im).__name__}")
    return hashlib.sha256(base64.b64decode(im.replace("\r", "").replace("\n", ""), validate=True)).hexdigest()


def tools_sent(tools: list | None) -> dict | None:
    """The record of a tools list: each tool's function name in order, and one sha256 of the whole list."""
    if tools is None:
        return None
    return {"names": [(t.get("function") or {}).get("name") for t in tools], "sha256": canonical_sha256(tools)}


def _checked(base: str, model: str, call: OllamaCall | None = None, test_override: bool = False):
    """Refuses a call whose request differs from what the lock builds for the same model, role, draw and thinking,
    unless test_override (a check script's deliberate change, written into the record)."""
    lock = load()
    if call is not None and lock.sha256 != call.lock_sha256:
        raise LockError("the lock changed after this call was built; rebuild it")
    if call is not None and not test_override:
        want = lock.ollama(call.requested or call.model, role=call.role, draw=call.draw, thinking=call.thinking,
                           candidate=call.candidate, retry=call.retry)      # D81: a retry's seed is the lock's too
        if (want.model, want.options, want.fields, want.system) != (call.model, call.options, call.fields, call.system):
            raise LockError(f"{call.model}: the request differs from the lock's; build calls with Lock.ollama only")
    version, digest = server_state(base, model)
    if version != lock.d["server"]["ollama_version"]:
        raise LockError(f"{base} runs Ollama {version}, the lock names {lock.d['server']['ollama_version']}")
    lock.check_digest(model, digest or "")
    return lock, version, digest


def _record(call: OllamaCall, payload: dict, base: str, version: str, digest: str, lock, passages, busy) -> dict:
    given = busy is not MEASURE
    return {"model": call.model, "role": call.role, "draw": call.draw, "candidate": call.candidate,
            "thinking": call.thinking,
            "options_sent": payload["options"],
            "fields_sent": {k: v for k, v in payload.items()      # tools and images: recorded by hash
                            if k not in ("model", "prompt", "messages", "options", "system", "stream", "tools", "images")},
            "system_sent": call.system if ("system" in payload or any(
                m.get("role") == "system" and m.get("content") == call.system for m in payload.get("messages", []))) else None,
            "model_digest": digest, "server": base, "ollama_version": version,
            "lock_sha256": lock.sha256, "busy_servers_on_machine": busy if given else None,
            "busy_how": "given by the caller" if given else None, "busy_offset_s": None, "busy_overlap": None,
            "passages": passages,
            "status": None, "stop_reason": None, "error": None, "text": "", "thinking_text": "",
            "prompt_tokens": None, "output_tokens": None,
            "wall_s": None, "load_s": None, "prompt_eval_s": None, "eval_s": None, "total_s": None,
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **provenance()}


def _stream(url: str, payload: dict, rec: dict, stall_s: float | None, pick, abort=None, measure: bool = False) -> dict:
    """Post, read the stream, fill rec. pick(chunk) -> (text, thinking, tool_calls) for one chunk; tool calls from
    every chunk are kept in order in rec["tool_calls"] when rec has that key. abort() true between chunks closes
    the call (Ollama then stops generating) and records it as "cancelled". measure: record busy_servers_on_machine
    from the sampler's reading that overlapped the call, attached after the call without waiting (Q146, D89 A1, D90
    O2); the first reading is waited for before the gate."""
    stall_s = stall_s if stall_s is not None else load().d["generation"]["stall_s"]
    data = json.dumps(payload).encode()
    rec["request_sha256"] = hashlib.sha256(data).hexdigest()       # the exact bytes posted
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    text, thought = [], []
    base = url.split("/api/")[0]
    if measure:
        machine_load.ready(base)                                   # the first reading, outside the gate (D89 A1)
    with server_gate(base, rec):
        t_post = time.time()
        _read(req, rec, stall_s, pick, abort, text, thought)
        t_end = time.time()
    if measure:
        rec.update(machine_load.at_end(base, t_post, t_end))      # D90 O2: the reading that overlapped the call
    return rec


def _read(req, rec, stall_s, pick, abort, text, thought) -> dict:
    last = None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=None) as r:          # no limit before the first token (Q2)
            for line in r:
                if rec.get("first_token_s") is None:
                    rec["first_token_s"] = round(time.time() - t0, 3)
                    _arm(r, stall_s)
                if abort is not None and abort():
                    rec.update(status="cancelled", error="the caller went away; the call was closed")
                    break
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if "error" in chunk:
                    rec.update(status="error", error=chunk["error"])
                    break
                t, th, calls = pick(chunk)
                text.append(t or "")
                thought.append(th or "")
                if calls and "tool_calls" in rec:
                    rec["tool_calls"].extend(calls)
                if chunk.get("done"):
                    last = chunk
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(body).get("error", body)
        except ValueError:
            pass
        rec.update(status="error", error=f"HTTP {e.code}: {body}")
    except (socket.timeout, TimeoutError):
        rec.update(status="stalled", error=f"no new token for {stall_s:.0f} s")
    except (urllib.error.URLError, ConnectionError, OSError, ValueError,          # refused, reset, bad JSON line,
            http.client.IncompleteRead) as e:      # a stream closed mid-chunk (D83 Q155, review F1): recorded, not raised
        rec.update(status="error", error=f"{type(e).__name__}: {e}")
    rec["wall_s"] = round(time.time() - t0, 3)
    rec["text"], rec["thinking_text"] = "".join(text), "".join(thought)
    if last is not None:
        rec["stop_reason"] = last.get("done_reason")
        rec["status"] = "ok" if rec["stop_reason"] == "stop" else rec["stop_reason"] or "unknown"
        rec["prompt_tokens"], rec["output_tokens"] = last.get("prompt_eval_count"), last.get("eval_count")
        for k in ("load", "prompt_eval", "eval", "total"):
            rec[f"{k}_s"] = _s(last.get(f"{k}_duration"))
    elif rec["status"] is None:
        rec.update(status="error", error="the stream ended without a final chunk")
    return rec


def generate(base_url: str, call: OllamaCall, prompt: str, passages: list | None = None,
             busy=MEASURE, stall_s: float | None = None, test_override: bool = False,
             images: list[str] | None = None) -> dict:
    """/api/generate under the lock. images: base64 strings, sent whole as the payload's images; the record keeps
    one sha256 per image (of its decoded bytes), never the data. An image that is not a base64 str raises
    ValueError before the call."""
    base = base_url.rstrip("/")
    lock, version, digest = _checked(base, call.model, call, test_override)
    images_sha256 = None if images is None else [image_sha256(im) for im in images]
    payload = call.payload(prompt)
    if images is not None:
        payload["images"] = list(images)
    rec = _record(call, payload, base, version, digest, lock, passages, busy)
    rec.update(test_override=test_override, images_sha256=images_sha256)
    return _stream(f"{base}/api/generate", payload, rec, stall_s,
                   lambda c: (c.get("response"), c.get("thinking"), None), measure=busy is MEASURE)


def chat(base_url: str, call: OllamaCall, messages: list[dict], fmt=None, passages: list | None = None,
         busy=MEASURE, stall_s: float | None = None, test_override: bool = False,
         abort=None, tools: list[dict] | None = None) -> dict:
    """/api/chat under the lock. The model's date-fixed system prompt is added only when the caller sends
    no system message of its own (a caller's system message replaces the template's, date included).
    tools: Ollama's tools list, sent whole when given; message.tool_calls from every chunk go to rec["tool_calls"].
    Images inside messages are sent whole; images_sha256 lists their hashes in message order (None when no
    message has images), and an image that is not a base64 str raises ValueError before the call."""
    base = base_url.rstrip("/")
    lock, version, digest = _checked(base, call.model, call, test_override)
    msgs = [dict(m) for m in messages]                            # images inside a message pass whole
    if call.system is not None and not any(m.get("role") == "system" for m in msgs):
        msgs.insert(0, {"role": "system", "content": call.system})
    images_sha256 = ([image_sha256(im) for m in msgs for im in (m.get("images") or [])]
                     if any("images" in m for m in msgs) else None)
    payload = {"model": call.model, "messages": msgs, "stream": True, "options": dict(call.options), **call.fields}
    if fmt is not None:
        payload["format"] = fmt
    if tools is not None:
        payload["tools"] = tools
    rec = _record(call, payload, base, version, digest, lock, passages, busy)
    rec.update(test_override=test_override, format_sent=fmt, messages_sha256=canonical_sha256(msgs),
               tools_sent=tools_sent(tools), tool_calls=[], images_sha256=images_sha256)

    def pick(c):
        m = c.get("message") or {}
        return m.get("content"), m.get("thinking"), m.get("tool_calls")
    return _stream(f"{base}/api/chat", payload, rec, stall_s, abort=abort, pick=pick, measure=busy is MEASURE)


def embed(base_url: str, model: str, inputs: list[str]) -> dict:
    """/api/embed with truncate false: an input longer than the encoder's limit is an error, never cut."""
    base = base_url.rstrip("/")
    lock, version, digest = _checked(base, model)
    payload = {"model": model, "input": inputs, "truncate": lock.d["server"]["truncate"],
               "keep_alive": lock.d["server"]["keep_alive"]}
    req = urllib.request.Request(f"{base}/api/embed", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    # F23 (audit of 16 October): every key of LOCK.toml [record], as chat and generate write them. /api/embed sends no
    # options, has no stop reason or output, and reports only load and total durations, so those keys are None.
    # busy_servers_on_machine is recorded as for chat and generate (Q146, D89 A1, D90): the reading that overlapped the call
    rec = {"model": model, "model_digest": digest, "ollama_version": version, "server": base,
           "lock_sha256": lock.sha256, "n_inputs": len(inputs), "status": "ok", "error": None,
           "options_sent": None, "fields_sent": {k: v for k, v in payload.items() if k not in ("model", "input")},
           "stop_reason": None, "output_tokens": None, "busy_servers_on_machine": None, "busy_how": None,
           "busy_offset_s": None, "busy_overlap": None, "passages": None,
           "wall_s": None, "load_s": None, "prompt_eval_s": None, "eval_s": None, "total_s": None,
           "embeddings": None, "prompt_tokens": None, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **provenance()}
    t0 = None
    try:
        machine_load.ready(base)                                   # the first reading, outside the gate (D89 A1)
        with server_gate(base, rec):
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=None) as r:
                body = json.loads(r.read())
        rec["embeddings"], rec["prompt_tokens"] = body.get("embeddings"), body.get("prompt_eval_count")
        rec["load_s"], rec["total_s"] = _s(body.get("load_duration")), _s(body.get("total_duration"))
    except urllib.error.HTTPError as e:
        rec.update(status="error", error=f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    except (urllib.error.URLError, ConnectionError, OSError, ValueError) as e:
        rec.update(status="error", error=f"{type(e).__name__}: {e}")
    if t0 is not None:
        t_end = time.time()
        rec["wall_s"] = round(t_end - t0, 3)
        rec.update(machine_load.at_end(base, t0, t_end))           # D90 O2: the reading that overlapped the call
    return rec
