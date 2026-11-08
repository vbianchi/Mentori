"""One Anthropic call under the lock, streamed, with the record D37 asks for (B11; T2's claude-haiku-4-5, D77).

    rec = generate(load(), "claude-haiku-4-5", draw=1, prompt=prompt)
    rec = chat(load(), "claude-haiku-4-5", draw=1, messages=msgs)

Built as experiments/runner/gemini_client.py is built: the standard library's HTTP layer (urllib), the exact bytes
posted hashed into the record, one record per call. The request carries what the lock gives and nothing else:

    model        [anthropic] model_id (claude-haiku-4-5-20251001, the dated snapshot the alias resolves to)
    max_tokens   [anthropic] max_tokens (64000, D57)
    temperature  [sampling.models] "claude-haiku-4-5" temperature (1.0, D43)

top_p and top_k are not sent (the row names none; Anthropic's defaults apply). No thinking setting is sent: the row's
think is "omit", so the generator rule's "default" and "off" both send nothing, which on claude-haiku-4-5 is thinking
off (the maker's default; extended thinking runs only when a request asks for it). thinking True (on as the row's
factor) or a level is refused, as Lock.ollama refuses them for an "omit" row. No seed is sent: the Messages API takes
none. The draw (and a candidate) is still required and checked by the lock's seed rule, and recorded, so a record
says which draw it belongs to. No stop sequence, no tool, no cache_control, no metadata are sent. A model whose name
is not the alias [anthropic] model_id resolves (model_id == model or model_id starts with model + "-") is refused, so
another model's sampling row can never be sent under Haiku's id; so is a sampling row that names any value other than
temperature (this reader would not send it).

The call streams (Server-Sent Events). There is no total timeout and no limit before the first token. The first token
is the first content_block_delta: Anthropic sends message_start and ping events before it, and pings keep coming while
the model works, so the socket alone cannot tell a stalled answer from a slow one. From the first token on, a gap of
[generation] stall_s seconds with no new delta ends the call as "stalled", whether the socket went silent (the read
timeout armed on the first token, as gemini_client arms it) or kept receiving pings. A caller's stall_s replaces the
lock's; the record then has test_override true and stall_s as used.

Status: "ok" when stop_reason is end_turn; "length" when it is max_tokens (the answer filled max_tokens) or
model_context_window_exceeded (the answer filled the context window: the lock's shift = false rule, a full context
stops the answer as "length"); otherwise the stop_reason itself (refusal, and stop_sequence, tool_use or pause_turn,
which a request with no stop sequence and no tool should never get), or "error" with the HTTP reason, the error event
in the stream, or the transport's exception, or "stalled". stop_details (sent with a refusal) is recorded whole.

Resends (Q170, D83; gemini_client's Q29 rule): HTTP 429, 500 and 529 (overloaded) only, only when no token has arrived
(first_chunk_s None), 5 attempts at most, waiting 2, 4, 8, 16 s before attempts 2 to 5. The same bytes are posted
again: nothing reached the model, so no seed or setting changes. Every attempt is in rec["attempts"] (attempt,
waited_before_s, http_code, status, error, error_body, wall_s, as gemini_client's). Any other HTTP error, a refused
connection, an error event inside the stream (before or after the first token, as gemini_client), an error after the
first token and a stall end the call on that attempt, Anthropic's whole error reply kept in error_body. Each attempt
starts from a clean record (the stream's ids, stop and usage, and the request id, are the last attempt's); wall_s
covers every attempt and wait, first_chunk_s is counted from the start of the attempt that streamed. The adapter's
step-level retry with a new seed is still refused for Anthropic (a retry scope refuses it), as for Gemini.

chat takes Ollama/OpenAI-shaped messages with text content: every system message goes into the top-level system
(joined by a blank line, in order), user -> role "user", assistant -> role "assistant"; Mentori's placeholders for an
empty turn as gemini_client sends them ("[Empty]" for an assistant turn, a space for a user turn; Anthropic may refuse
the space with a 400, which is then recorded as an error, never repaired). Tool calls, tool messages, images and tools
are not mapped (T2 sends none) and are refused before anything is sent.

The record: text (the text blocks' text), thinking_text (thinking blocks' text; none expected, as no thinking is
asked for), content_blocks (each block's type and, for text and thinking, its text, in order), tool_calls (always []),
model_version (message_start's model), message_id, request_id (the request-id header), prompt_tokens (usage
input_tokens), cache_creation_input_tokens and cache_read_input_tokens (as returned; nothing asks for caching),
output_tokens (the last usage output_tokens, the whole answer's), thinking_tokens None (the API reports none apart),
total_tokens (prompt + output when both are given), request_sha256 (the sha256 of the exact bytes posted), wall_s,
first_chunk_s (seconds to the first token), plus the fields gemini_client records. The local-only fields of [record]
(model_digest, server, ollama_version, load_s, prompt_eval_s, eval_s, busy_servers_on_machine) are absent, as for
Gemini.

The key is read from ANTHROPIC_API_KEY, else from ~/.config/mentori-runs/keys.env (gemini_client.key); it is sent in
the x-api-key header and never written to a record.
"""

from __future__ import annotations

import copy
import hashlib
import http.client
import json
import socket
import time
import urllib.error
import urllib.request

from experiments.runner.gemini_client import key
from experiments.runner.lock import SAMPLING_KEYS, LockError, _lookup
from experiments.runner.ollama_client import _arm

API = "https://api.anthropic.com/v1/messages"
VERSION = "2023-06-01"                     # the anthropic-version header
LENGTH = ("max_tokens", "model_context_window_exceeded")
RETRY_CODES = (429, 500, 529)              # Q170 (D83): rate limit, server error, overloaded
BACKOFF_S = (2, 4, 8, 16)                  # waits before attempts 2, 3, 4, 5 (gemini_client's)
_open = urllib.request.urlopen             # the HTTP layer; check_anthropic replaces it with a fake
_clock = time.monotonic                    # the stall clock; check_anthropic replaces it to stall without waiting
_sleep = time.sleep                        # the wait between attempts; check_anthropic replaces it to log the waits


class StalledError(Exception):
    """Pings kept coming but no new token for stall_s seconds."""


def _key() -> str:
    return key("ANTHROPIC_API_KEY")


def settings(lock, model: str, thinking: bool | str | None = None) -> dict:
    """{"model", "temperature", "max_tokens"}: Lock.anthropic's values, after the checks this reader needs (see the
    module docstring). thinking: None = the generator rule ([thinking] generator); "default" and "off" (or False)
    send nothing; True and a level are refused."""
    model_id = lock.d["anthropic"]["model_id"]
    if not (model_id == model or model_id.startswith(model + "-")):
        raise LockError(f"{model}: the lock's [anthropic] model_id is {model_id!r}, not this model; nothing was sent")
    _, row = _lookup(lock.d["sampling"]["models"], model)
    if row is None:
        raise LockError(f"{model}: no row in [sampling.models]")
    extra = [k for k in SAMPLING_KEYS if k in row and k != "temperature"]
    if extra:
        raise LockError(f"{model}: [sampling.models] names {extra}; this reader sends only temperature")
    mode = lock.d["thinking"]["generator"] if thinking is None else (
        "default" if thinking == "default" else "off" if thinking in (False, "off") else thinking)
    if mode not in ("default", "off"):
        raise LockError(f"{model}: thinking {thinking!r} is not sent (the row's think is {row.get('think')!r}: no "
                        "thinking mode in the lock); only the default or off, which send nothing")
    if row.get("think") != "omit":
        raise LockError(f"{model}: [sampling.models] think is {row.get('think')!r}; this reader knows only 'omit'")
    return lock.anthropic(model)


def to_messages(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Ollama/OpenAI messages as (system, messages). Raises ValueError on what it does not map (an unknown role,
    images, tool calls, a tool message), never drops it."""
    system, out = [], []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if m.get("images"):
            raise ValueError("images in a message are not mapped for Anthropic")
        if content is not None and not isinstance(content, str):
            raise ValueError(f"content of a {role!r} message is not text: {type(content).__name__}")
        if role == "system":
            system.append(content or "")
        elif role == "user":
            out.append({"role": "user", "content": content or " "})              # Mentori's placeholder
        elif role == "assistant":
            if m.get("tool_calls"):
                raise ValueError("tool calls are not mapped for Anthropic (T2 sends none)")
            out.append({"role": "assistant", "content": content or "[Empty]"})    # Mentori's placeholder
        else:
            raise ValueError(f"no Anthropic mapping for role {role!r}")
    return ("\n\n".join(system) if system else None), out


def _http_error(e: urllib.error.HTTPError) -> tuple[str, str]:
    """(error, error_body): "HTTP code: type: message", and the whole reply body as received."""
    body = e.read().decode("utf-8", "replace")
    msg = body
    try:
        err = json.loads(body).get("error", {})
        msg = f"{err.get('type')}: {err.get('message', body)}"
    except (ValueError, AttributeError):
        pass
    return f"HTTP {e.code}: {msg}", body


def _event(data: dict, rec: dict, out: dict) -> None:
    """One SSE data object into out (blocks) and rec (ids, usage, stop_reason)."""
    t = data.get("type")
    if t == "message_start":
        msg = data.get("message") or {}
        rec["model_version"] = msg.get("model", rec["model_version"])
        rec["message_id"] = msg.get("id", rec["message_id"])
        out["usage"].update({k: v for k, v in (msg.get("usage") or {}).items() if v is not None})
    elif t == "content_block_start":
        b = data.get("content_block") or {}
        out["blocks"].append({"type": b.get("type"), "text": b.get("text") or b.get("thinking") or ""})
    elif t == "content_block_delta":
        d = data.get("delta") or {}
        block = out["blocks"][data.get("index", len(out["blocks"]) - 1)]
        if d.get("type") == "text_delta":
            block["text"] += d.get("text", "")
        elif d.get("type") == "thinking_delta":
            block["text"] += d.get("thinking", "")
        else:                                                   # signature_delta and the like: kept, not read
            block.setdefault("other_deltas", []).append(d)
    elif t == "message_delta":
        d = data.get("delta") or {}
        if d.get("stop_reason"):
            rec["stop_reason"] = d["stop_reason"]
        if d.get("stop_details") is not None:
            rec["stop_details"] = d["stop_details"]
        out["usage"].update({k: v for k, v in (data.get("usage") or {}).items() if v is not None})


def _attempt(req, rec: dict, stall_s: float, out: dict) -> int | None:
    """One streamed request. Fills out and rec; returns the HTTP code of an HTTP error, else None."""
    t0 = time.time()
    last_token = None
    try:
        with _open(req, timeout=None) as r:                       # no limit before the first token (Q2)
            rec["request_id"] = (getattr(r, "headers", None) or {}).get("request-id")
            for raw in r:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue                                       # event: lines, blank lines
                data = json.loads(line[5:])
                if data.get("type") == "error":                    # an error sent inside the stream
                    err = data.get("error") or {}
                    rec.update(status="error", error=f"in stream: {err.get('type')} {err.get('message', err)}",
                               error_body=line[5:].strip())
                    break
                _event(data, rec, out)
                now = _clock()
                if data.get("type") == "content_block_delta":
                    if rec["first_chunk_s"] is None:
                        rec["first_chunk_s"] = round(time.time() - t0, 3)
                        _arm(r, stall_s)                           # from the first token on, a silent socket stalls
                    last_token = now
                elif last_token is not None and now - last_token >= stall_s:
                    raise StalledError                             # pings, but no new token for stall_s
    except urllib.error.HTTPError as e:
        rec["request_id"] = rec.get("request_id") or (e.headers.get("request-id") if e.headers else None)
        err, body = _http_error(e)
        rec.update(status="error", error=err, error_body=body)
        return e.code
    except (socket.timeout, TimeoutError, StalledError):
        rec.update(status="stalled", error=f"no new token for {stall_s:.0f} s")
    except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError, AttributeError, TypeError,
            IndexError) as e:
        # refused, reset, a stream cut mid-event (IncompleteRead), a bad JSON line, an event of the wrong shape
        rec.update(status="error", error=f"{type(e).__name__}: {e}")
    finally:
        out["attempt_s"] = round(time.time() - t0, 3)
    return None


def _call(payload: dict, rec: dict, stall_s: float) -> dict:
    """Sends payload with the Q170 resend rule and completes rec."""
    data = json.dumps(payload).encode()
    rec["request_sha256"] = hashlib.sha256(data).hexdigest()       # the exact bytes posted, the same on every attempt
    req = urllib.request.Request(API, data=data, headers={
        "Content-Type": "application/json", "x-api-key": _key(), "anthropic-version": VERSION})
    t0 = time.time()
    out = {}
    for n in range(1, len(BACKOFF_S) + 2):
        wait = BACKOFF_S[n - 2] if n > 1 else 0
        if wait:
            _sleep(wait)
        out = {"blocks": [], "usage": {}, "attempt_s": None}
        rec.update(status=None, error=None, error_body=None, request_id=None, model_version=None, message_id=None,
                   stop_reason=None, stop_details=None)
        code = _attempt(req, rec, stall_s, out)
        rec["attempts"].append({"attempt": n, "waited_before_s": wait, "http_code": code, "status": rec["status"]
                                or "streamed", "error": rec["error"], "error_body": rec["error_body"],
                                "wall_s": out["attempt_s"]})
        if code not in RETRY_CODES or rec["first_chunk_s"] is not None:
            break
    rec["wall_s"] = round(time.time() - t0, 3)
    rec.update(text="".join(b["text"] for b in out["blocks"] if b["type"] == "text"),
               thinking_text="".join(b["text"] for b in out["blocks"] if b["type"] == "thinking"),
               content_blocks=out["blocks"])
    u = out["usage"]
    rec.update(prompt_tokens=u.get("input_tokens"), output_tokens=u.get("output_tokens"),
               cache_creation_input_tokens=u.get("cache_creation_input_tokens"),
               cache_read_input_tokens=u.get("cache_read_input_tokens"))
    if rec["prompt_tokens"] is not None and rec["output_tokens"] is not None:
        rec["total_tokens"] = rec["prompt_tokens"] + rec["output_tokens"]
    if rec["status"] is None:
        sr = rec["stop_reason"]
        rec["status"] = "ok" if sr == "end_turn" else "length" if sr in LENGTH else sr if sr else "error"
        if sr is None:
            rec["error"] = "the stream ended without a stop_reason"
    rec["attempts"][-1].update(status=rec["status"], error=rec["error"])
    return rec


def _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg) -> tuple[dict, float, bool]:
    """(cfg, stall_s, test_override): cfg from settings() unless test_override_cfg (a check script's deliberate
    change); stall_s from [generation] unless the caller passes another value. Either override is recorded. The draw
    and candidate are checked by the lock's seed rule (nothing is sent: the API takes no seed)."""
    lock._seed(draw, candidate)
    cfg = test_override_cfg if test_override_cfg is not None else settings(lock, model, thinking)
    locked = lock.d["generation"]["stall_s"]
    stall = stall_s if stall_s is not None else locked
    return cfg, stall, test_override_cfg is not None or stall != locked


def _record(model, draw, candidate, thinking, cfg, override, stall_s, lock, passages) -> dict:
    return {"model": model, "provider": "anthropic", "model_id": cfg.get("model"), "draw": draw,
            "candidate": candidate, "thinking": thinking,
            "options_sent": {k: v for k, v in cfg.items() if k != "model"}, "test_override": override,
            "stall_s": stall_s, "system_sent": None, "request_sha256": None, "lock_sha256": lock.sha256,
            "passages": passages, "status": None, "stop_reason": None, "stop_details": None, "error": None,
            "error_body": None, "text": "", "thinking_text": "", "content_blocks": [], "tool_calls": [],
            "model_version": None, "message_id": None, "request_id": None, "prompt_tokens": None,
            "output_tokens": None, "thinking_tokens": None, "total_tokens": None,
            "cache_creation_input_tokens": None, "cache_read_input_tokens": None, "wall_s": None,
            "first_chunk_s": None, "attempts": [], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def _payload(cfg: dict, messages: list[dict], system: str | None) -> dict:
    p = {**cfg, "stream": True, "messages": messages}
    if system is not None:
        p["system"] = system
    return p


def generate(lock, model: str, draw: int, prompt: str, thinking: bool | str | None = None, system: str | None = None,
             passages: list | None = None, stall_s: float | None = None, test_override_cfg: dict | None = None,
             candidate: int | None = None) -> dict:
    """One user turn. The settings come from settings(lock, model, thinking); test_override_cfg (a check script's
    deliberate change) replaces them and is written into the record."""
    cfg, stall_s, override = _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg)
    rec = _record(model, draw, candidate, thinking, cfg, override, stall_s, lock, passages)
    rec["system_sent"] = system
    return _call(_payload(cfg, [{"role": "user", "content": prompt}], system), rec, stall_s)


def chat(lock, model: str, draw: int, messages: list[dict], tools: list[dict] | None = None,
         thinking: bool | str | None = None, passages: list | None = None, stall_s: float | None = None,
         test_override_cfg: dict | None = None, candidate: int | None = None) -> dict:
    """Multi-turn Messages call, text only. Settings as generate. tools are refused (not mapped; T2 sends none). The
    record adds messages_posted (the request's messages, whole, as a copy, so a caller that later changes its
    messages does not change the record)."""
    if tools:
        raise LockError(f"{model}: tools are not mapped for Anthropic (T2 sends none); nothing was sent")
    cfg, stall_s, override = _settings(lock, model, draw, thinking, candidate, stall_s, test_override_cfg)
    system, msgs = to_messages(messages)
    rec = _record(model, draw, candidate, thinking, cfg, override, stall_s, lock, passages)
    rec.update(system_sent=system, messages_posted=copy.deepcopy(msgs))
    return _call(_payload(cfg, msgs, system), rec, stall_s)
