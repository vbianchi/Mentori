"""Checks for experiments/runner/anthropic_client.py and its route through lock_adapter (B11; T2's Haiku generator).

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_anthropic [--live]

Offline (a fake HTTP layer in place of urllib, a stubbed key; no network, no key read). The fake logs every request
of the run: the client's headers and the headers urllib would send, URL and method, the timeout the HTTP layer was
opened with, the body, and for every stream the (timeout, stream lines yielded by then) of each time its socket timeout
was set, the HTTP error each request ended with, and the client's waits between attempts (its sleep replaced, so
nothing waits). Every fake() script expects one request (none where nothing may be posted; the number the Q170 rule
makes in the resend cases of 5); a script that ends in an error holds one response more than it expects, so an extra
request is counted, never refused by the fake.
1. Settings: settings() equals the lock's [anthropic] model_id and max_tokens and the claude-haiku-4-5 row's temperature,
   for thinking None, "default", "off" and False; thinking True and a level are refused; another model's row
   (gemma3:27b), a row that names top_p (a scratch lock), a missing draw and a draw of 0 are refused, nothing posted.
2. The request: the body posted has exactly model, max_tokens, temperature, stream and messages (and system when one
   is given), each value the lock's; no top_p, top_k, thinking, seed, stop_sequences, tools or metadata; the client's
   headers are exactly Content-type application/json, X-api-key (the stubbed key) and Anthropic-version 2023-06-01,
   and the headers urllib would send are those plus urllib's own (measured on a bare request: Content-length, Host,
   User-agent); the HTTP layer is opened with timeout None, passed explicitly (LOCK [generation] timeout = "none");
   the request is a POST to https://api.anthropic.com/v1/messages (written out in this script, no query);
   request_sha256 is the sha256 of the bytes posted; a generate with a system posts those keys plus the system.
3. The record: every [record] field that applies to a cloud call is present and filled (options_sent, stop_reason,
   prompt_tokens, output_tokens, wall_s, passages, lock_sha256), the local-only ones are absent as in a Gemini record,
   and the stream lands in text, model_version, message_id, request_id, tokens and first_chunk_s; the key never
   reaches the record.
4. Stops: max_tokens and model_context_window_exceeded -> status length; refusal -> status refusal with stop_details
   kept; a stream with no stop_reason -> error. Each record is complete (gaps(): every key of the ok record, the
   fields every call fills, the usage message_start and message_delta gave, first_chunk_s after a token, one attempt
   per request logged, numbered, with its time, its wait (0, then 2, 4, 8, 16 s) and the HTTP code that request ended
   with, every attempt before the last an error with that HTTP error's text and whole body, the last one's status,
   error and error_body equal to the record's).
5. Resends (Q170, D83). Sent again: HTTP 529, 429 and 500 before any token, then an answer (2 requests, a 2 s wait,
   status ok, both attempts recorded); HTTP 529 on a multi-megabyte generate (8's prompt and system: the same bytes
   posted twice, the answer whole); a chat after HTTP 500; 529, 429, 500, 529 then an answer on the fifth attempt
   (waits 2, 4, 8, 16 s); five 529s (5 requests, no sixth, status error with the last reply, all five recorded); a 529
   after message_start but before any token, then a refused connection (the record holds the second attempt's
   outcome, no request id, model, message id or usage kept from the first). Not sent again (one request, no wait,
   status error, the reply body and the part read kept, the record complete): HTTP 400 and 503 (not on the list),
   HTTP 529 after the first token, a refused connection, an error event inside the stream before and after the first
   token (not an HTTP code, as gemini_client), a reset after the first token, a stream cut mid-event (IncompleteRead).
6. Stall: a silent socket after the first token, and pings for stall_s after the first token, end as stalled, the
   record complete; pings for longer than stall_s before the first token do not (no limit before the first token).
7. chat: system messages joined into the top-level system, user and assistant turns as given, Mentori's placeholders
   for empty turns; images, tool calls, a tool message and tools are refused before anything is posted;
   messages_posted is a copy; body_checks(): generate and chat, each with and without a system, post exactly the
   lock's keys and values, and a chat without a system message posts no system.
8. Whole at any size (LOCK [text], truncate = false): the asserts enforce a prompt of at least 3,000,000 characters
   (3,300,000 used), a system of at least 2,000,000 (2,150,002 used), a chat of more than 20 turns (41 used), a
   streamed answer of more than 100,000 characters (160,800 used) and 500 passages; big_case() posts a generate with
   a system, a chat with system messages and a chat of the 41 turns alone, each compared whole with what was posted
   and recorded (text and content_blocks), each body with exactly the lock's keys and values. Then, over EVERY request
   of 1 to 8 (the log above), seven invariants: each fake() script ended with exactly the requests it expects; a
   request is sent again only after an HTTP 429, 500 or 529 that came before any content_block_delta, with the same
   bytes as the first, after waits of 2, 4, 8, 16 s, 5 requests at most per script (the resend invariant); the
   client's headers exactly the three of 2, the wire headers those plus urllib's own; a POST to the
   endpoint; timeout None; the body exactly the lock's keys and values (plus system when one is posted); and every
   stream that yielded a content_block_delta had its socket timeout set exactly once, to stall_s, when the first
   content_block_delta had just been read (none before), and a stream that yielded none never had it set.
9. Mutants, each run through sweep(): every case of 4, 5, 6, 7's body_checks and 8's big_case, posted under a fresh
   log, and the seven invariants of 8 over every request the sweep posts (a crash counts as a failure). The sweep
   passes on the client as it is, its allowed resends included (the
   control); each mutant must make something fail. Body: top_p sent, top_k sent, a thinking setting sent, max_tokens
   8192, temperature 0.7, temperature left out; max_tokens 8192, temperature 0 and metadata each only for a long
   input, top_k only with a system; temperature 0 in a chat only when no system is posted. Whole: prompt[:200000],
   system[:50000], msgs[-20:], msgs[-20:] only when no system is posted, text[:100000], content_blocks cut with text
   left whole, passages[:20]. Request (the client's own source altered): timeout=stall_s; an anthropic-beta header
   always, only when the bytes posted exceed 1,000,000, only when a system is posted, only on chat; the endpoint with
   ?beta=true; the stall timeout armed at open instead of at the first token; a 3600 s timeout armed at open only
   when the bytes posted exceed 1,000,000. Resend, forbidden ones: an unrecorded resend at once inside one attempt
   after any HTTP error, and after an HTTP 529 only when the bytes posted exceed 1,000,000; a resend after any HTTP
   error (400 and 503 too); 503 resent too; a resend after the first token; a resend after any error before the first
   token (a refused connection, an error event); a resend after an overloaded_error event before the first token only;
   6 attempts; a resend posting a seed. Resend, allowed ones broken: 500 not resent; 4 attempts; no wait (the wait
   still recorded); waits halved; the wait recorded as 0; only the last attempt recorded; the first attempt's request
   id, model and message id, or usage kept into the record. Record: output_tokens None on error, the attempt's error
   and error_body None.
10. The adapter: inside a run context built by experiment.context with {"generator": "anthropic::claude-haiku-4-5"},
   lock_adapter.generate and chat return the text, done_reason stop or length and the counts, and write one record
   each (provider anthropic, role generator, caller_asked with the caller's options never sent, prompt_sent or
   messages_sent), the request's headers and timeout as in 2; an error (HTTP 400) raises LockCallError with the
   record written and transient None; HTTP 529 then an answer is resent inside the client and returns the answer with
   one record holding both attempts; five 529s raise LockCallError after 5 requests with one record of 5 attempts;
   the judge scope, a retry scope (the step-level retry with a new seed), tools, images and claude:: are refused with
   nothing posted and no record; the inputs and answer of 8 are recorded whole in calls.jsonl (content_blocks
   included); the large generate posts the whole prompt, its request_sha256 is the sha256 of the bytes posted, and a
   mutant cutting the prompt to 200,000 characters in lock_adapter's Anthropic generate branch is caught;
   experiment.context refuses anthropic::gemma3:27b; the seven invariants of 8 hold over every request of 10.
Live (only with --live; one short call, a few hundred tokens, needs ANTHROPIC_API_KEY):
11. One generate at the lock's settings: status ok, model_version names the dated snapshot, tokens recorded.

Coverage, stated exactly. The request shapes posted are generate and chat, each with and without a system, each
small (a few words) and multi-megabyte (5.2 to 7.9 million bytes posted), answered ok, length (max_tokens and
model_context_window_exceeded), refusal, error (HTTP 400 and 503, HTTP 529 after the first token, five 529s in a row,
a refused connection, an error event in the stream before and after the first token, a reset, a cut stream, a stream
with no stop_reason), resent then answered (HTTP 529, 429 and 500 on small generates, 500 on a chat, 529 on a
multi-megabyte generate, four errors before the fifth attempt) and stalled (a silent socket, pings with no token).
The invariants of 8 hold over every request posted, so a defect keyed on size, on a system being present, on
generate against chat, or on the outcome is caught where the shapes above reach it.
Not every shape meets every outcome (the stops, stalls and most errors are small generates). Behaviour keyed on any
other input feature (a particular draw or candidate, a word in the prompt, the passages, a date, the number of calls
made, a caller's stall_s or test_override_cfg) is not covered by these checks; the client is also read in review.
"""

import argparse
import copy
import hashlib
import http.client
import inspect
import io
import json
import re
import socket
import sys
import tempfile
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "mentori"))

from backend.agents import lock_adapter as la  # noqa: E402

from experiments.runner import anthropic_client as ac  # noqa: E402
from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LOCK, Lock, LockError, load  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--live", action="store_true")
args = ap.parse_args()

MODEL = "claude-haiku-4-5"
lock = load()
A, ROW = lock.d["anthropic"], lock.d["sampling"]["models"][MODEL]
WANT = {"model": A["model_id"], "temperature": ROW["temperature"], "max_tokens": A["max_tokens"]}
STALL = lock.d["generation"]["stall_s"]   # every call of this script runs at the lock's stall_s
LONG = 1_000_000                          # bytes posted: the conditional mutants' "long"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    return None


# The conformance rules, written once so the mutants of 9 run the very checks 2 to 8 run
ALLOWED_KEYS = {"model", "max_tokens", "temperature", "stream", "messages"}


def body_conforms(body: dict, system: bool = False) -> bool:
    """The posted body has exactly the lock's keys and values (and system when one was given)."""
    keys = ALLOWED_KEYS | ({"system"} if system else set())
    return (set(body) == keys and body["model"] == WANT["model"] and body["max_tokens"] == WANT["max_tokens"]
            and body["temperature"] == WANT["temperature"] and body["stream"] is True
            and (not system or isinstance(body["system"], str)))


RESEND = (429, 500, 529)   # Q170 (D83): the HTTP codes resent before any token, written out, not read from the client
WAITS = (2, 4, 8, 16)      # the waits before attempts 2 to 5 (gemini_client's Q29 rule); 5 attempts at most


def wire_headers(req) -> dict:
    """The headers urllib would send for req: the request's own plus what urllib's HTTPS handler adds before the
    socket (do_request_: Content-length, Host, and the opener's User-agent). Below that, http.client adds
    Accept-Encoding: identity and do_open Connection: close to every request, whoever builds it."""
    r = urllib.request.Request(req.full_url, data=req.data, headers=dict(req.header_items()), method=req.get_method())
    h = urllib.request.HTTPSHandler()
    h.add_parent(urllib.request.build_opener())
    h.do_request_(r)
    return dict(r.header_items())


CLIENT_HEADERS = {"Content-type", "X-api-key", "Anthropic-version"}
URLLIB_OWN = set(wire_headers(urllib.request.Request(ac.API, data=b"{}")))   # what urllib adds to a bare request


def headers_conform(own: dict, sent: dict) -> bool:
    """own: the client's request headers, exactly the three, each value the lock's; sent: those plus urllib's own."""
    return (set(own) == CLIENT_HEADERS and own["Content-type"] == "application/json"
            and own["X-api-key"] == "offline-key" and own["Anthropic-version"] == "2023-06-01"
            and set(sent) == CLIENT_HEADERS | URLLIB_OWN)


SNAPSHOT = "claude-haiku-4-5-20251001"
STARTED = {"model_version": SNAPSHOT, "message_id": "msg_fake1", "request_id": "req_fake1", "prompt_tokens": 21,
           "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}          # what message_start gave
FILLED = ("options_sent", "lock_sha256", "stall_s", "request_sha256", "wall_s", "at", "status", "model_id", "draw",
          "passages", "attempts")                                                  # filled on every path
KEYS = set()                                                                       # the ok record's keys (check 3)
PS = ["p1", "p2"]


def gaps(r: dict, first_token: bool = False, **want) -> list:
    """What a record lacks: a key of the ok record, a field every call fills left None, a value other than want (the
    usage and ids the stream gave, kept on every path), first_chunk_s after a token, an error text for status error
    or stalled; and its attempts against the requests the current fake() script logged: one attempt per request,
    numbered 1 on, each with its time, the wait before it (0, then 2, 4, 8, 16 s) and the HTTP code that request
    ended with; every attempt before the last an error with that HTTP error's text and whole body; the last one's
    status, error and error_body equal to the record's."""
    bad = sorted(KEYS - set(r))
    bad += [k for k in FILLED if r.get(k) is None]
    bad += [f"{k}={r.get(k)!r}" for k, v in want.items() if r.get(k) != v]
    if first_token and r.get("first_chunk_s") is None:
        bad.append("first_chunk_s")
    if r.get("status") in ("error", "stalled") and not r.get("error"):
        bad.append("error")
    reqs = LOG["scripts"][-1]["requests"] if LOG["scripts"] else []
    a = r.get("attempts") or []
    if not a or len(a) != len(reqs) or len(a) > 5:
        return bad + [f"attempts: {len(a)} for {len(reqs)} requests"]
    for i, (x, q) in enumerate(zip(a, reqs)):
        if ((x.get("attempt"), x.get("waited_before_s"), x.get("http_code")) != (i + 1, WAITS[i - 1] if i else 0,
                                                                                 ended_code(q))
                or x.get("wall_s") is None):
            bad.append(f"attempts[{i}] {x.get('attempt')} {x.get('waited_before_s')} {x.get('http_code')}")
        e = ended_error(q)
        if i < len(a) - 1 and (x.get("status") != "error" or e is None or x.get("error") != e.fake_error
                               or x.get("error_body") != e.fake_body):
            bad.append(f"attempts[{i}] error/error_body")
    last = a[-1]
    if (last.get("status"), last.get("error"), last.get("error_body")) != (r.get("status"), r.get("error"),
                                                                          r.get("error_body")):
        bad.append("attempts[-1] status/error/error_body")
    return bad


# A fake HTTP layer
DELTA_LINE = b'"type": "content_block_delta"'


class FakeSock:
    """settimeout records (timeout, how many stream lines the response had yielded by then)."""
    def __init__(self, response):
        self.response, self.timeouts = response, []

    def settimeout(self, t):
        self.timeouts.append((t, self.response.yielded))


class FakeResponse:
    """first_delta: how many lines had been yielded when the first content_block_delta data line was."""
    def __init__(self, lines, fail_after=None, exc=None, headers=None):
        self.lines, self.fail_after = lines, fail_after
        self.exc = exc if exc is not None else ConnectionResetError("reset by peer")
        self.headers = headers if headers is not None else {"request-id": "req_fake1"}
        self.yielded, self.first_delta, self.raised = 0, None, None
        self.sock = FakeSock(self)

        class _Raw:
            _sock = self.sock

        class _Fp:
            raw = _Raw

        self.fp = _Fp

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        for i, line in enumerate(self.lines):
            if self.fail_after is not None and i == self.fail_after:
                self.raised = self.exc
                raise self.exc
            self.yielded += 1
            if self.first_delta is None and line.startswith(b"data:") and DELTA_LINE in line:
                self.first_delta = self.yielded
            yield line


def sse(*events):
    out = []
    for e in events:
        out += [f"event: {e['type']}\n".encode(), f"data: {json.dumps(e)}\n".encode(), b"\n"]
    return out


START = {"type": "message_start", "message": {"id": "msg_fake1", "type": "message", "role": "assistant",
         "model": "claude-haiku-4-5-20251001", "content": [], "stop_reason": None,
         "usage": {"input_tokens": 21, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                   "output_tokens": 1}}}
PING = {"type": "ping"}
BLOCK = {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
D1 = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "STAR aligns "}}
D2 = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "reads."}}
BSTOP = {"type": "content_block_stop", "index": 0}
STOP = {"type": "message_stop"}


def delta(stop, out=12, **extra):
    return {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None, **extra},
            "usage": {"output_tokens": out}}


def stream(stop="end_turn", **extra):
    return sse(START, PING, BLOCK, D1, D2, BSTOP, delta(stop, **extra), STOP)


def error_json(code, typ):
    return json.dumps({"type": "error", "error": {"type": typ, "message": f"fake {code}"}, "request_id": "req_err"})


def http_error(code, typ):
    """A fresh HTTP error (its body can be read once), carrying the error text and body the record must keep."""
    body = error_json(code, typ)
    e = urllib.error.HTTPError(ac.API, code, "err", {"request-id": "req_err"}, io.BytesIO(body.encode()))
    e.fake_error, e.fake_body = f"HTTP {code}: {typ}: fake {code}", body
    return e


def ended_error(q):
    """The HTTP error a logged request ended with (raised at open or inside its stream), else None."""
    for e in (q["raised"], q["response"].raised if q["response"] is not None else None):
        if isinstance(e, urllib.error.HTTPError):
            return e
    return None


def ended_code(q):
    e = ended_error(q)
    return e.code if e is not None else None


posted, headers, wire, timeouts, endpoints = [], [], [], [], []   # the current fake() script's requests
LOG = {"scripts": []}   # every fake() script of the current scope: {"expect": n, "requests": [entry, ...]}
ENDPOINT = ("https://api.anthropic.com/v1/messages", "POST")   # written out, not read from the client
MISSING = object()   # the opener's default: a client that passes no timeout would get urllib's global default


def fake(script, clock=None, expect=None):
    """Replaces the HTTP layer: each request takes the next item (an exception to raise or a FakeResponse). The script
    expects expect requests (default one, or none when it is empty); a script that ends in an error holds one item
    more than it expects, so an extra request is counted by the invariants, not refused by the fake (a request past
    the script's end raises, and the sweep of 9 counts that as a failure). Every request is logged in
    LOG for the invariants of 8, with the error it ended with and the client's waits between attempts (the client's
    sleep is replaced: nothing waits)."""
    sent = []
    for x in (posted, headers, wire, timeouts, endpoints):
        x.clear()
    seg = {"expect": (1 if script else 0) if expect is None else expect, "requests": [], "slept": []}
    LOG["scripts"].append(seg)

    def opener(req, timeout=MISSING):
        entry = {"url": req.full_url, "method": req.get_method(), "own": dict(req.header_items()),
                 "wire": wire_headers(req), "timeout": timeout, "bytes": len(req.data or b""), "data": req.data,
                 "body": json.loads(req.data), "response": None, "raised": None}
        seg["requests"].append(entry)
        endpoints.append((entry["url"], entry["method"]))
        posted.append(req.data)
        headers.append(entry["own"])
        wire.append(entry["wire"])
        timeouts.append(timeout)
        sent.append(entry["body"])
        if not script:
            raise AssertionError("a request the script did not expect (a retry?)")
        item = script.pop(0)
        if isinstance(item, BaseException):
            entry["raised"] = item
            raise item
        entry["response"] = item
        return item
    ac._open, ac._key, ac._sleep = opener, lambda: "offline-key", seg["slept"].append
    ac._clock = clock if clock is not None else SAVED[2]
    return sent


def scoped(fn):
    """(fn(), the fake() scripts it ran): fn runs under a fresh request log; the caller's log is left as it was."""
    saved = LOG["scripts"]
    LOG["scripts"] = []
    try:
        return fn(), LOG["scripts"]
    finally:
        LOG["scripts"] = saved


INVARIANTS = {
    "count": "each fake() script ended with exactly the requests it expects (one, or the resends of 5 it holds "
             "for; none where nothing may be posted)",
    "resend": "a request is sent again only after an HTTP 429, 500 or 529 that came before any content_block_delta, "
              "with the same bytes, after waits of 2, 4, 8, 16 s (the client's sleep, logged), 5 requests at most",
    "headers": "the client's headers exactly Anthropic-version, Content-type, X-api-key (the lock's values), the "
               "wire headers those plus urllib's own",
    "endpoint": "a POST to https://api.anthropic.com/v1/messages, no query",
    "timeout": "opened with timeout None, passed explicitly",
    "body": "the body exactly the lock's keys and values (plus system when one is posted)",
    "arming": "a stream that yielded a content_block_delta had its socket timeout set once, to stall_s, when the "
              "first one had just been read; a stream that yielded none never had it set",
}


def armed_right(resp) -> bool:
    return resp.sock.timeouts == ([(STALL, resp.first_delta)] if resp.first_delta is not None else [])


def resend_faults(s: dict) -> list:
    """Where one fake() script breaks the Q170 rule: a request after one that did not end with an HTTP 429, 500 or 529
    before any content_block_delta, a request posting other bytes than the first, waits other than 2, 4, 8, 16 s
    before requests 2 on, more than 5 requests."""
    reqs, bad = s["requests"], []
    if len(reqs) > 5:
        bad.append(f"{len(reqs)} requests")
    for j in range(1, len(reqs)):
        p = reqs[j - 1]
        if ended_code(p) not in RESEND or (p["response"] is not None and p["response"].first_delta is not None):
            bad.append(f"request {j + 1} after {ended_code(p)}" + (" past a token" if ended_code(p) in RESEND else ""))
        if reqs[j]["data"] != reqs[0]["data"]:
            bad.append(f"request {j + 1} posts other bytes")
    if s["slept"] != list(WAITS[:max(len(reqs) - 1, 0)]):
        bad.append(f"waits {s['slept']} for {len(reqs)} requests")
    return bad


def log_faults(scripts: list) -> dict:
    """{invariant: [where it fails]} over every request of scripts."""
    reqs = [q for s in scripts for q in s["requests"]]
    return {
        "count": [f"script {i}: {len(s['requests'])} of {s['expect']}" for i, s in enumerate(scripts)
                  if len(s["requests"]) != s["expect"]],
        "resend": [f"script {i}: {b}" for i, s in enumerate(scripts) for b in resend_faults(s)],
        "headers": [i for i, q in enumerate(reqs) if not headers_conform(q["own"], q["wire"])],
        "endpoint": [i for i, q in enumerate(reqs) if (q["url"], q["method"]) != ENDPOINT],
        "timeout": [i for i, q in enumerate(reqs) if q["timeout"] is not None],
        "body": [i for i, q in enumerate(reqs) if not body_conforms(q["body"], system="system" in q["body"])],
        "arming": [f"{i}: {q['response'].sock.timeouts}" for i, q in enumerate(reqs)
                   if q["response"] is not None and not armed_right(q["response"])],
    }


def report_log(prefix: str, scripts: list) -> None:
    """One check per invariant over every request of scripts, with what they covered."""
    reqs = [q for s in scripts for q in s["requests"]]
    streams = [q["response"] for q in reqs if q["response"] is not None]
    cover = (f"{len(reqs)} requests in {len(scripts)} scripts ({sum('system' in q['body'] for q in reqs)} with a "
             f"system, {sum(q['bytes'] > LONG for q in reqs)} over {LONG:,} bytes), {len(streams)} streams "
             f"({sum(r.first_delta is not None for r in streams)} with a content_block_delta)")
    for k, v in log_faults(scripts).items():
        check(f"{prefix}: {INVARIANTS[k]}", reqs and not v, f"fails at {v[:4]}" if v else cover)


SAVED = (ac._open, ac._key, ac._clock, ac._payload, ac._attempt)
ORIG = {n: getattr(ac, n) for n in ("_open", "_key", "_clock", "_sleep", "_payload", "_attempt", "_call", "_record",
                                    "to_messages", "generate", "chat")}


def restore():
    for n, fn in ORIG.items():
        setattr(ac, n, fn)


def source_mutant(name: str, *pairs: tuple[str, str], module=ac, fn=None):
    """A function's own source with each (old, new) of pairs replaced, compiled against its module (so it calls the
    fake HTTP layer, and the adapter its clients, as the original does). fn defaults to the client's original of
    name. Each old must occur exactly once."""
    src = inspect.getsource(fn if fn is not None else ORIG[name])
    for old, new in pairs:
        if src.count(old) != 1:
            raise AssertionError(f"mutant of {name}: {old!r} occurs {src.count(old)} times, not once")
        src = src.replace(old, new)
    ns = {}
    exec(compile(src, module.__file__, "exec"), vars(module), ns)
    return ns[name]


# 8's inputs: each far above any limit a cut might use (a cut at 20 turns, 50,000 or 200,000 characters, 20 passages)
SYS_A = "".join(f"<s{i:06d}> Answer from the passages only, é 漢. " for i in range(25000))
SYS_B = "".join(f"<r{i:06d}> Cite each passage you use, 🌱. " for i in range(25000))
BIG_SYSTEM = SYS_A + "\n\n" + SYS_B
BIG_PROMPT = "".join(f"[q{i:06d}] Which aligner, é 漢 🌱, handles spliced reads? " for i in range(60000))
BIG_TURNS = [{"role": "user", "content": BIG_PROMPT}] + [
    {"role": "assistant" if i % 2 else "user", "content": "".join(f"t{i}.{j} " for j in range(2000))}
    for i in range(1, 41)]
BIG_CHAT = [{"role": "system", "content": SYS_A}, {"role": "system", "content": SYS_B}] + copy.deepcopy(BIG_TURNS)
BIG_PASSAGES = [f"doc{i:04d}:chunk{i % 13}" for i in range(500)]
ANSWER_PARTS = [f"<a{i:04d}> " + "STAR maps spliced reads. " * 40 for i in range(100)] + ["L" * 60000]
ANSWER = "".join(ANSWER_PARTS)
ANSWER_BLOCKS = [{"type": "text", "text": ANSWER}]   # the one text block the big stream sends, whole
assert len(BIG_PROMPT) >= 3_000_000 and len(BIG_SYSTEM) >= 2_000_000 and len(BIG_TURNS) > 20
assert len(ANSWER) > 100_000 and len(BIG_PASSAGES) == 500


def big_stream():
    ds = [{"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": t}}
          for t in ANSWER_PARTS]
    return FakeResponse(sse(START, PING, BLOCK, *ds, BSTOP, delta("end_turn", out=40000), STOP))


def big_case() -> tuple[dict, str]:
    """({part: compared whole}, sizes): a generate with a system, a chat with system messages and a chat of the 41
    turns alone, with 8's inputs, each input compared with the body posted and the record, the answer and the
    passages with the record."""
    parts = {}
    sent = fake([big_stream()])
    r = ac.generate(lock, MODEL, 1, BIG_PROMPT, system=BIG_SYSTEM, passages=BIG_PASSAGES)
    b, n_gen = sent[0], len(posted[0])
    parts["generate: the prompt posted whole"] = b["messages"] == [{"role": "user", "content": BIG_PROMPT}]
    parts["generate: the system posted whole"] = b.get("system") == BIG_SYSTEM
    parts["generate: the body posted has exactly the lock's keys and values"] = body_conforms(b, system=True)
    parts["generate: system_sent recorded whole"] = r["system_sent"] == BIG_SYSTEM
    parts["generate: the answer recorded whole"] = r["text"] == ANSWER and r["status"] == "ok"
    parts["generate: content_blocks recorded whole"] = r["content_blocks"] == ANSWER_BLOCKS
    parts["generate: the 500 passages recorded whole"] = r["passages"] == BIG_PASSAGES
    sent = fake([big_stream()])
    r = ac.chat(lock, MODEL, 1, BIG_CHAT, passages=BIG_PASSAGES)
    b, n_chat = sent[0], len(posted[0])
    parts["chat: the system posted whole"] = b.get("system") == BIG_SYSTEM
    parts["chat: the 41 turns posted whole"] = b["messages"] == BIG_TURNS
    parts["chat: the body posted has exactly the lock's keys and values"] = body_conforms(b, system=True)
    parts["chat: system_sent and messages_posted recorded whole"] = (r["system_sent"] == BIG_SYSTEM
                                                                    and r["messages_posted"] == BIG_TURNS)
    parts["chat: the answer recorded whole"] = r["text"] == ANSWER and r["status"] == "ok"
    parts["chat: content_blocks recorded whole"] = r["content_blocks"] == ANSWER_BLOCKS
    parts["chat: the 500 passages recorded whole"] = r["passages"] == BIG_PASSAGES
    sent = fake([big_stream()])
    r = ac.chat(lock, MODEL, 1, copy.deepcopy(BIG_TURNS), passages=BIG_PASSAGES)
    b, n_bare = sent[0], len(posted[0])
    parts["chat without a system: no system posted or recorded"] = "system" not in b and r["system_sent"] is None
    parts["chat without a system: the 41 turns posted whole"] = b["messages"] == BIG_TURNS
    parts["chat without a system: the body posted has exactly the lock's keys and values"] = body_conforms(b)
    parts["chat without a system: messages_posted recorded whole"] = r["messages_posted"] == BIG_TURNS
    parts["chat without a system: the answer recorded whole"] = r["text"] == ANSWER and r["status"] == "ok"
    parts["chat without a system: content_blocks recorded whole"] = r["content_blocks"] == ANSWER_BLOCKS
    parts["chat without a system: the 500 passages recorded whole"] = r["passages"] == BIG_PASSAGES
    sizes = (f"prompt {len(BIG_PROMPT):,} chars, system {len(BIG_SYSTEM):,} chars, {len(BIG_TURNS)} turns, answer "
             f"{len(ANSWER):,} chars, {len(BIG_PASSAGES)} passages; {n_gen:,}, {n_chat:,} and {n_bare:,} bytes posted")
    return parts, sizes


def system_case() -> bool:
    """A generate with a system: the body posted has the lock's keys and values plus the system, as given."""
    sent = fake([FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "What does STAR do?", system="Be brief.")
    return (body_conforms(sent[0], system=True) and sent[0]["system"] == "Be brief." and r["system_sent"] == "Be brief."
            and sent[0]["messages"] == [{"role": "user", "content": "What does STAR do?"}])


MSGS = [{"role": "system", "content": "Be brief."}, {"role": "system", "content": "Cite the paper."},
        {"role": "user", "content": "What does STAR do?"}, {"role": "assistant", "content": ""},
        {"role": "user", "content": ""}]


def body_checks() -> dict:
    """{check: passes}: the small bodies posted, generate and chat, each with and without a system."""
    sent = fake([FakeResponse(stream())])
    ac.generate(lock, MODEL, 1, "x")
    out = {"a generate without a system posts exactly the lock's keys and values": body_conforms(sent[0]),
           "a generate with a system posts those plus the system, as given": system_case()}
    sent = fake([FakeResponse(stream())])
    r = ac.chat(lock, MODEL, 1, copy.deepcopy(MSGS[:3]))
    out["a chat with system messages posts the lock's keys and values plus the joined system"] = (
        body_conforms(sent[0], system=True) and sent[0]["system"] == "Be brief.\n\nCite the paper."
        and r["system_sent"] == sent[0]["system"])
    sent = fake([FakeResponse(stream())])
    r = ac.chat(lock, MODEL, 1, copy.deepcopy(MSGS[2:]))
    out["a chat without a system message posts exactly the lock's keys and values, no system"] = (
        body_conforms(sent[0]) and r["system_sent"] is None and sent[0]["messages"] == [
            {"role": "user", "content": "What does STAR do?"}, {"role": "assistant", "content": "[Empty]"},
            {"role": "user", "content": " "}])
    return out


def stop_cases() -> dict:
    """{case: (passes, detail)}: 4's stops."""
    out = {}
    for stop in ("max_tokens", "model_context_window_exceeded"):
        fake([FakeResponse(stream(stop))])
        r = ac.generate(lock, MODEL, 1, "x", passages=PS)
        g = gaps(r, True, **STARTED, output_tokens=12, total_tokens=33, passages=PS)
        out[f"stop_reason {stop} -> status length, text kept, record complete"] = (
            r["status"] == "length" and r["text"] == "STAR aligns reads." and r["stop_reason"] == stop and not g,
            f"{r['status']} {g}")
    fake([FakeResponse(stream("refusal", stop_details={"type": "refusal", "category": None, "explanation": "fake"}))])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, True, **STARTED, output_tokens=12, total_tokens=33, passages=PS, stop_reason="refusal",
             text="STAR aligns reads.")
    out["refusal -> status refusal, stop_details kept, record complete (usage from message_start kept)"] = (
        r["status"] == "refusal" and (r["stop_details"] or {}).get("explanation") == "fake" and not g,
        f"{r['status']} {g}")
    fake([FakeResponse(sse(START, BLOCK, D1, BSTOP))])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, True, **STARTED, output_tokens=1, total_tokens=22, passages=PS)
    out["a stream with no stop_reason -> error, record complete"] = (
        r["status"] == "error" and "stop_reason" in (r["error"] or "") and not g, f"{r['error']} {g}")
    return out


CODES = ((529, "overloaded_error"), (429, "rate_limit_error"), (500, "api_error"))   # the resent codes and their types
NONE = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None, "passages": PS}   # nothing came
OK = {**STARTED, "output_tokens": 12, "total_tokens": 33, "passages": PS, "error": None, "error_body": None,
      "text": "STAR aligns reads."}   # the answer of stream(), the record clean of the attempts before it


def slept() -> list:
    return LOG["scripts"][-1]["slept"]


def resend_cases() -> dict:
    """{case: (passes, detail)}: 5's resends (Q170). Each script holds exactly the items the rule takes plus one, and
    expects the requests the rule makes, so one request more or fewer fails (the case here, the count invariant in the
    sweep). gaps() checks every attempt against the request it logged."""
    out = {}
    for code, typ in CODES:
        s = fake([http_error(code, typ), FakeResponse(stream()), FakeResponse(stream())], expect=2)
        r = ac.generate(lock, MODEL, 1, "x", passages=PS)
        g = gaps(r, True, **OK)
        out[f"HTTP {code} before any token, then an answer: sent again after 2 s, status ok, both attempts "
            "recorded"] = (r["status"] == "ok" and len(s) == 2 and slept() == [2] and not g,
                           f"{len(s)} requests, waits {slept()}, {g}")
    s = fake([http_error(529, "overloaded_error"), big_stream(), big_stream()], expect=2)
    r = ac.generate(lock, MODEL, 1, BIG_PROMPT, system=BIG_SYSTEM, passages=PS)
    g = gaps(r, True, **{**OK, "text": ANSWER, "output_tokens": 40000, "total_tokens": 40021})
    out["HTTP 529 on a multi-megabyte generate (8's prompt and system): the same bytes sent again, answer whole"] = (
        r["status"] == "ok" and len(s) == 2 and posted[0] == posted[1] and len(posted[1]) > LONG
        and r["content_blocks"] == ANSWER_BLOCKS and not g, f"{len(s)} requests, {g}")
    s = fake([http_error(500, "api_error"), FakeResponse(stream()), FakeResponse(stream())], expect=2)
    r = ac.chat(lock, MODEL, 1, copy.deepcopy(MSGS[:3]), passages=PS)
    g = gaps(r, True, **OK)
    out["chat: HTTP 500 before any token, then an answer: sent again, the same bytes"] = (
        r["status"] == "ok" and len(s) == 2 and posted[0] == posted[1] and slept() == [2] and not g, f"{len(s)} {g}")
    errs = [http_error(529, "overloaded_error"), http_error(429, "rate_limit_error"), http_error(500, "api_error"),
            http_error(529, "overloaded_error")]
    s = fake(errs + [FakeResponse(stream()), FakeResponse(stream())], expect=5)
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, True, **OK)
    out["four errors (529, 429, 500, 529), then an answer on the fifth attempt: waits 2, 4, 8, 16 s, status ok"] = (
        r["status"] == "ok" and len(s) == 5 and slept() == [2, 4, 8, 16] and not g, f"{len(s)} {slept()} {g}")
    s = fake([http_error(529, "overloaded_error") for _ in range(5)] + [FakeResponse(stream())], expect=5)
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, request_id="req_err", **NONE)
    out["five HTTP 529s: 5 attempts, no sixth, status error with the last one's reply, all five recorded"] = (
        r["status"] == "error" and len(s) == 5 and slept() == [2, 4, 8, 16] and r["error"] == "HTTP 529: "
        "overloaded_error: fake 529" and r["error_body"] == error_json(529, "overloaded_error") and not g,
        f"{len(s)} {slept()} {r['error']} {g}")
    s = fake([FakeResponse(sse(START, PING, BLOCK), fail_after=6, exc=http_error(529, "overloaded_error")),
              urllib.error.URLError("refused"), FakeResponse(stream())], expect=2)
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, request_id=None, model_version=None, message_id=None, **NONE)
    out["HTTP 529 after message_start but before any token, then a refused connection: sent again once, the record "
        "the second attempt's (no id, model or usage kept from the first)"] = (
        r["status"] == "error" and len(s) == 2 and (r["error"] or "").startswith("URLError") and not g,
        f"{len(s)} {r['error']} {g}")
    return out


def no_resend_cases() -> dict:
    """{case: (passes, detail)}: 5's errors that are never sent again, each script holding a second response a
    resend would take."""
    out = {}
    after = {**STARTED, "output_tokens": 1, "total_tokens": 22, "passages": PS}   # message_start, then D1

    def one(name, s, r, extra, g):
        out[name] = (len(s) == 1 and r["status"] == "error" and slept() == [] and extra and not g,
                     f"{len(s)} request(s), {r['error']}" + (f"; gaps {g}" if g else ""))

    for code, typ in ((400, "invalid_request_error"), (503, "api_error")):
        s = fake([http_error(code, typ), FakeResponse(stream())])
        r = ac.generate(lock, MODEL, 1, "x", passages=PS)
        one(f"HTTP {code} (not on the list)", s, r, r["error"] == f"HTTP {code}: {typ}: fake {code}"
            and r["error_body"] == error_json(code, typ), gaps(r, request_id="req_err", **NONE))
    s = fake([FakeResponse(stream(), fail_after=12, exc=http_error(529, "overloaded_error")), FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)   # line 12: D2's event line, after D1
    one("HTTP 529 after the first token", s, r, r["error"] == "HTTP 529: overloaded_error: fake 529"
        and r["text"] == "STAR aligns ", gaps(r, True, **after))
    s = fake([urllib.error.URLError("refused"), FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    one("a refused connection", s, r, (r["error"] or "").startswith("URLError"), gaps(r, request_id=None, **NONE))
    err = {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
    s = fake([FakeResponse(sse(START, BLOCK, D1, err)), FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    one("an error event in the stream after the first token", s, r,
        r["error"] == "in stream: overloaded_error Overloaded" and json.loads(r["error_body"] or "null") == err
        and r["text"] == "STAR aligns ", gaps(r, True, **after))
    s = fake([FakeResponse(sse(START, PING, err)), FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    one("an error event in the stream before the first token (as gemini_client: not an HTTP code)", s, r,
        r["error"] == "in stream: overloaded_error Overloaded" and r["text"] == "" and r["first_chunk_s"] is None,
        gaps(r, **after))
    s = fake([FakeResponse(stream(), fail_after=15), FakeResponse(stream())])   # line 15: after D2
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    one("a reset after the first token", s, r, r["text"] == "STAR aligns reads." and "reset" in (r["error"] or ""),
        gaps(r, True, **after))
    s = fake([FakeResponse(stream(), fail_after=13, exc=http.client.IncompleteRead(b"da", 40)),   # D2's data
              FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    one("a stream cut mid-event", s, r, (r["error"] or "").startswith("IncompleteRead") and r["text"] == "STAR aligns ",
        gaps(r, True, **after))
    return out


def ticking(times):
    it = iter(times)
    return lambda: next(it)


def stall_cases() -> dict:
    """{case: (passes, detail)}: 6's stalls."""
    out = {}
    sent = fake([FakeResponse(stream(), fail_after=15, exc=socket.timeout("timed out"))])
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, True, **STARTED, output_tokens=1, total_tokens=22, passages=PS)
    out["a silent socket after the first token -> stalled, text kept, record complete"] = (
        r["status"] == "stalled" and r["text"] == "STAR aligns reads." and len(sent) == 1 and not g,
        f"{r['error']} {g}")
    # times: one per data line read (START, PING, BLOCK, D1, then pings)
    sent = fake([FakeResponse(sse(START, PING, BLOCK, D1, PING, PING, D2, delta("end_turn"), STOP))],
                clock=ticking([0, 1, 2, 3, 300, STALL + 3, STALL + 4, STALL + 5, STALL + 6]))
    r = ac.generate(lock, MODEL, 1, "x", passages=PS)
    g = gaps(r, True, **STARTED, output_tokens=1, total_tokens=22, passages=PS)
    out["pings for stall_s after the first token -> stalled, record complete"] = (
        r["status"] == "stalled" and r["text"] == "STAR aligns " and len(sent) == 1 and not g,
        f"{r['status']} {r['error']} {g}")
    fake([FakeResponse(sse(START, PING, PING, PING, BLOCK, D1, D2, delta("end_turn"), STOP))],
         clock=ticking([0, 10, 5000, 9000, 9001, 9002, 9003, 9004, 9005]))
    r = ac.generate(lock, MODEL, 1, "x")
    out["pings longer than stall_s before the first token -> not stalled (no limit before the first token)"] = (
        r["status"] == "ok" and r["text"] == "STAR aligns reads.", r["status"])
    return out


def sweep() -> list:
    """[what fails]: every case of 4, 5, 6, 7's body_checks and 8's big_case under a fresh request log, then the six
    invariants of 8 over every request the sweep posted."""
    def run():
        try:
            bad = [f"4 {k}" for k, (ok, _) in stop_cases().items() if not ok]
            bad += [f"5 {k}" for k, (ok, _) in resend_cases().items() if not ok]
            bad += [f"5 {k}" for k, (ok, _) in no_resend_cases().items() if not ok]
            bad += [f"6 {k}" for k, (ok, _) in stall_cases().items() if not ok]
            bad += [f"7 {k}" for k, ok in body_checks().items() if not ok]
            parts, _ = big_case()
            return bad + [f"8 {k}" for k, ok in parts.items() if not ok]
        except Exception as e:   # a request past a script's end, or a mutant's crash: a failure, never a pass
            return [f"crashed: {type(e).__name__}: {e}"[:200]]
    bad, scripts = scoped(run)
    n = sum(len(s["requests"]) for s in scripts)
    return bad + [f"invariant {k}: {len(v)} of " + (f"{len(scripts)} scripts" if k == "count" else f"{n} requests")
                  for k, v in log_faults(scripts).items() if v]


try:
    # 1. Settings
    for t in (None, "default", "off", False):
        check(f"1 settings at thinking {t!r} are the lock's", ac.settings(lock, MODEL, t) == WANT,
              json.dumps(ac.settings(lock, MODEL, t)))
    for t in (True, "high"):
        sent = fake([])
        e = raises(LockError, lambda: ac.generate(lock, MODEL, 1, "x", thinking=t))
        check(f"1 thinking {t!r} refused, nothing posted", e is not None and not sent, str(e)[:110])
    sent = fake([])
    e = raises(LockError, lambda: ac.generate(lock, "gemma3:27b", 1, "x"))
    check("1 another model's row is never sent under Haiku's id", e is not None and not sent, str(e)[:110])
    raw = LOCK.read_bytes()
    topp = Lock(re.sub(rb'("claude-haiku-4-5"\s*= \{ temperature = 1.0,)', rb"\1 top_p = 0.9,", raw), LOCK)
    e = raises(LockError, lambda: ac.settings(topp, MODEL))
    check("1 a row naming top_p is refused (never silently dropped)",
          e is not None and "top_p" in topp.d["sampling"]["models"][MODEL], str(e)[:110])
    for d in (None, 0):
        sent = fake([])
        e = raises(LockError, lambda: ac.generate(lock, MODEL, d, "x"))
        check(f"1 draw {d!r} refused, nothing posted", e is not None and not sent, str(e)[:110])

    # 2 and 3. Request and record
    sent = fake([FakeResponse(stream())])
    r = ac.generate(lock, MODEL, 2, "What does STAR do?", passages=["p1", "p2"], candidate=3)
    b = sent[0]
    check("2 body posted has exactly the lock's keys and values", body_conforms(b), json.dumps(
        {k: v for k, v in b.items() if k != "messages"}))
    check("2 nothing else: no top_p, top_k, thinking, seed, stop_sequences, tools, metadata, system",
          not {"top_p", "top_k", "thinking", "seed", "stop_sequences", "tools", "metadata", "system"} & set(b))
    check("2 the prompt is the one user message", b["messages"] == [{"role": "user", "content": "What does STAR do?"}])
    check("2 headers: exactly Content-type application/json, X-api-key from the key reader, Anthropic-version "
          "2023-06-01; urllib sends those plus its own", headers_conform(headers[0], wire[0]),
          f"client {sorted(headers[0])}; urllib's own {sorted(URLLIB_OWN - CLIENT_HEADERS)}")
    check("2 the HTTP layer is opened with timeout None, passed explicitly (LOCK [generation] timeout = \"none\")",
          timeouts == [None], repr(timeouts))
    check("2 the request is a POST to https://api.anthropic.com/v1/messages, no query", endpoints == [ENDPOINT],
          repr(endpoints))
    check("2 request_sha256 is the sha256 of the bytes posted",
          r["request_sha256"] == hashlib.sha256(posted[0]).hexdigest())
    applies = ["options_sent", "stop_reason", "prompt_tokens", "output_tokens", "wall_s", "passages", "lock_sha256"]
    local = ["model_digest", "server", "ollama_version", "load_s", "prompt_eval_s", "eval_s", "busy_servers_on_machine"]
    check("3 every [record] field that applies is present and filled", all(r.get(k) is not None for k in applies)
          and set(lock.d["record"]["fields"]) == set(applies) | set(local),
          json.dumps({k: r.get(k) for k in applies}))
    check("3 the local-only fields are absent, as in a Gemini record", not set(local) & set(r))
    check("3 options_sent is the lock's (temperature, max_tokens); model_id the dated snapshot",
          r["options_sent"] == {"temperature": WANT["temperature"], "max_tokens": WANT["max_tokens"]}
          and r["model_id"] == WANT["model"], json.dumps(r["options_sent"]))
    check("3 stream read: text, status ok, model_version, message_id, request_id, tokens, first token time",
          r["text"] == "STAR aligns reads." and r["status"] == "ok" and r["stop_reason"] == "end_turn"
          and r["model_version"] == "claude-haiku-4-5-20251001" and r["message_id"] == "msg_fake1"
          and r["request_id"] == "req_fake1" and (r["prompt_tokens"], r["output_tokens"], r["total_tokens"])
          == (21, 12, 33) and r["first_chunk_s"] is not None and r["thinking_tokens"] is None
          and r["lock_sha256"] == lock.sha256 and r["passages"] == ["p1", "p2"],
          f"{r['status']} {r['prompt_tokens']}+{r['output_tokens']} {r['model_version']}")
    check("3 draw and candidate recorded (no seed sent); the lock's stall_s, no override",
          (r["draw"], r["candidate"], r["stall_s"], r["test_override"]) == (2, 3, STALL, False))
    check("3 the key is in no record field", "offline-key" not in json.dumps(r))
    KEYS.update(r)
    check("2 a generate with a system posts the lock's keys and values plus the system", system_case())

    # 4. Stops
    for name, (ok, detail) in stop_cases().items():
        check(f"4 {name}", ok, detail)

    # 5. Resends (Q170): sent again only on HTTP 429, 500 or 529 before any token, 5 attempts at most, each recorded
    for name, (ok, detail) in resend_cases().items():
        check(f"5 resent: {name}", ok, detail)
    for name, (ok, detail) in no_resend_cases().items():
        check(f"5 not resent: {name}: status error, one request, no wait, record kept and complete", ok, detail)

    # 6. Stall (the arming of the socket timeout is an invariant of 8, over every stream)
    for name, (ok, detail) in stall_cases().items():
        check(f"6 {name}", ok, detail)

    # 7. chat
    system, msgs = ac.to_messages(MSGS)
    check("7 system messages -> top-level system, joined by a blank line",
          system == "Be brief.\n\nCite the paper.", repr(system))
    check("7 user and assistant turns as given, Mentori's placeholders for empty turns",
          msgs == [{"role": "user", "content": "What does STAR do?"}, {"role": "assistant", "content": "[Empty]"},
                   {"role": "user", "content": " "}], json.dumps(msgs))
    sent = fake([FakeResponse(stream())])
    caller = copy.deepcopy(MSGS[:3])
    r = ac.chat(lock, MODEL, 1, caller)
    caller[2]["content"] = "changed after the call"
    check("7 chat posts system and messages at the lock's settings; messages_posted is a copy",
          body_conforms(sent[0], system=True) and sent[0]["system"] == "Be brief.\n\nCite the paper."
          and r["messages_posted"] == [{"role": "user", "content": "What does STAR do?"}]
          and r["system_sent"] == sent[0]["system"] and r["status"] == "ok")
    for name, ok in body_checks().items():
        check(f"7 {name}", ok)
    refused = {
        "images": (ValueError, lambda: ac.chat(lock, MODEL, 1, [{"role": "user", "content": "x", "images": ["aGk="]}])),
        "tool calls": (ValueError, lambda: ac.chat(lock, MODEL, 1, [{"role": "user", "content": "x"}, {
            "role": "assistant", "content": "", "tool_calls": [{"function": {"name": "f", "arguments": {}}}]}])),
        "a tool message": (ValueError, lambda: ac.chat(lock, MODEL, 1, [{"role": "tool", "content": "1"}])),
        "tools": (LockError, lambda: ac.chat(lock, MODEL, 1, [{"role": "user", "content": "x"}],
                                             tools=[{"type": "function", "function": {"name": "f"}}])),
    }
    for name, (exc, fn) in refused.items():
        sent = fake([])
        check(f"7 {name} refused before anything is posted", raises(exc, fn) is not None and not sent)

    # 8. Whole at any size, then the invariants over every request of 1 to 8
    parts, sizes = big_case()
    for name, ok in parts.items():
        check(f"8 {name}", ok, sizes if name.endswith("prompt posted whole") else "")
    report_log("8 every request of 1 to 8", LOG["scripts"])

    # 9. Mutants: every case and invariant above, run against altered clients
    def mutant_payload(change):
        def p(cfg, messages, system):
            body = SAVED[3](cfg, messages, system)
            change(body)
            return body
        return p

    def long_input(b):
        return sum(len(m["content"]) for m in b["messages"]) + len(b.get("system") or "") > 1_000_000

    def retrying(when):
        def attempt(req, rec, stall_s, out):
            code = SAVED[4](req, rec, stall_s, out)
            if code is not None and when(req, code):
                rec.update(status=None, error=None, error_body=None)
                code = SAVED[4](req, rec, stall_s, out)
            return code
        return attempt

    def cut_text(payload, rec, stall_s):
        rec = ORIG["_call"](payload, rec, stall_s)
        rec["text"] = rec["text"][:100000]
        return rec

    def cut_blocks(payload, rec, stall_s):
        rec = ORIG["_call"](payload, rec, stall_s)
        for blk in rec["content_blocks"]:
            blk["text"] = blk["text"][:100000]
        return rec

    def cut_passages(model, draw, candidate, thinking, cfg, override, stall_s, lock_, passages):
        return ORIG["_record"](model, draw, candidate, thinking, cfg, override, stall_s, lock_,
                               passages[:20] if passages else passages)

    def cut_turns(only_without_system):
        def to_messages(messages):
            system, msgs = ORIG["to_messages"](messages)
            return system, (msgs[-20:] if system is None or not only_without_system else msgs)
        return to_messages

    def cut_prompt(b):
        for m in b["messages"]:
            m["content"] = m["content"][:200000]

    def attempt_error_none(payload, rec, stall_s):
        rec = ORIG["_call"](payload, rec, stall_s)
        rec["attempts"][0].update(error=None, error_body=None)
        return rec

    def drop_output_on_error(payload, rec, stall_s):
        rec = ORIG["_call"](payload, rec, stall_s)
        if rec["status"] == "error":
            rec["output_tokens"] = None
        return rec

    HDR = '"anthropic-version": VERSION}'
    BETA = '"anthropic-beta": "context-1m-2025-08-07"'
    OPEN = 'rec["request_id"] = (getattr(r, "headers", None) or {}).get("request-id")'
    ARM = "_arm(r, stall_s)                           # from the first token on"
    BRK = 'if code not in RETRY_CODES or rec["first_chunk_s"] is not None:'

    def beta_when(cond):
        return source_mutant("_call", (HDR, f'"anthropic-version": VERSION, **({{{BETA}}} if {cond} else {{}})}}'))

    mutants = {   # name: {client attribute: its replacement}
        "top_p sent": {"_payload": mutant_payload(lambda b: b.update(top_p=0.95))},
        "top_k sent": {"_payload": mutant_payload(lambda b: b.update(top_k=40))},
        "a thinking setting sent": {"_payload": mutant_payload(
            lambda b: b.update(thinking={"type": "enabled", "budget_tokens": 1024}))},
        "max_tokens 8192": {"_payload": mutant_payload(lambda b: b.update(max_tokens=8192))},
        "temperature 0.7": {"_payload": mutant_payload(lambda b: b.update(temperature=0.7))},
        "temperature left out": {"_payload": mutant_payload(lambda b: b.pop("temperature"))},
        "max_tokens 8192 only for a long input": {"_payload": mutant_payload(
            lambda b: b.update(max_tokens=8192) if long_input(b) else None)},
        "temperature 0 only for a long input": {"_payload": mutant_payload(
            lambda b: b.update(temperature=0) if long_input(b) else None)},
        "metadata only for a long input": {"_payload": mutant_payload(
            lambda b: b.update(metadata={"user_id": "x"}) if long_input(b) else None)},
        "top_k only with a system": {"_payload": mutant_payload(lambda b: b.update(top_k=40) if "system" in b else None)},
        "temperature 0 in a chat only when no system is posted": {"chat": source_mutant("chat", (
            "_call(_payload(cfg, msgs, system), rec, stall_s)",
            '_call(_payload(cfg if system is not None else {**cfg, "temperature": 0}, msgs, system), rec, stall_s)'))},
        "prompt[:200000]": {"_payload": mutant_payload(cut_prompt)},
        "system[:50000]": {"_payload": mutant_payload(
            lambda b: b.update(system=b["system"][:50000]) if "system" in b else None)},
        "msgs[-20:]": {"to_messages": cut_turns(False)},
        "msgs[-20:] only when no system is posted": {"to_messages": cut_turns(True)},
        "text[:100000]": {"_call": cut_text},
        "content_blocks text[:100000], text left whole": {"_call": cut_blocks},
        "passages[:20]": {"_record": cut_passages},
        "timeout=stall_s": {"_attempt": source_mutant(
            "_attempt", ("_open(req, timeout=None)", "_open(req, timeout=stall_s)"))},
        "an anthropic-beta header": {"_call": source_mutant("_call", (HDR, f'"anthropic-version": VERSION, {BETA}}}'))},
        f"an anthropic-beta header only when the bytes posted exceed {LONG:,}": {"_call": beta_when(f"len(data) > {LONG}")},
        "an anthropic-beta header only when a system is posted": {"_call": beta_when('"system" in payload')},
        "an anthropic-beta header only on chat": {"_call": beta_when('"messages_posted" in rec')},
        "the endpoint with ?beta=true": {"_call": source_mutant(
            "_call", ("urllib.request.Request(API,", 'urllib.request.Request(API + "?beta=true",'))},
        "the stall timeout armed at open instead of at the first token": {"_attempt": source_mutant(
            "_attempt", (OPEN, "_arm(r, stall_s); " + OPEN), (ARM, "pass" + ARM[len("_arm(r, stall_s)"):]))},
        f"a 3600 s timeout armed at open only when the bytes posted exceed {LONG:,}": {"_attempt": source_mutant(
            "_attempt", (OPEN, f"_arm(r, 3600) if len(req.data) > {LONG} else None; " + OPEN))},
        # Resends (Q170): each mutant breaks one part of the rule; the allowed resends of 5 pass on the client as it is
        "an unrecorded resend at once (inside one attempt, no wait) after any HTTP error": {
            "_attempt": retrying(lambda req, code: True)},
        f"an unrecorded resend at once after an HTTP 529 only when the bytes posted exceed {LONG:,}": {
            "_attempt": retrying(lambda req, code: code == 529 and len(req.data) > LONG)},
        "a resend after any HTTP error (400 and 503 too)": {"_call": source_mutant("_call", (BRK, (
            'if code is None or rec["first_chunk_s"] is not None:')))},
        "HTTP 503 resent too": {"_call": source_mutant("_call", (BRK, (
            'if code not in RETRY_CODES + (503,) or rec["first_chunk_s"] is not None:')))},
        "HTTP 500 not resent (429 and 529 only)": {"_call": source_mutant("_call", (BRK, (
            'if code not in (429, 529) or rec["first_chunk_s"] is not None:')))},
        "a resend after the first token": {"_call": source_mutant("_call", (BRK, "if code not in RETRY_CODES:"))},
        "a resend after any error before the first token (a refused connection, an error event)": {
            "_call": source_mutant("_call", (BRK, (
                'if (code not in RETRY_CODES and not (code is None and rec["status"] == "error")) '
                'or rec["first_chunk_s"] is not None:')))},
        "a resend after an overloaded_error event in the stream before the first token only": {
            "_call": source_mutant("_call", (BRK, (
                'if (code not in RETRY_CODES and not (rec["error"] or "").startswith("in stream: overloaded_error")) '
                'or rec["first_chunk_s"] is not None:')))},
        "6 attempts (a fifth wait of 32 s)": {"_call": source_mutant(
            "_call", ("range(1, len(BACKOFF_S) + 2)", "range(1, len(BACKOFF_S) + 3)"),
            ("wait = BACKOFF_S[n - 2]", "wait = (BACKOFF_S + (32,))[n - 2]"))},
        "4 attempts": {"_call": source_mutant(
            "_call", ("range(1, len(BACKOFF_S) + 2)", "range(1, len(BACKOFF_S) + 1)"))},
        "no wait before a resend (the wait still recorded)": {"_call": source_mutant(
            "_call", ("_sleep(wait)", "pass"))},
        "waits halved: 1, 2, 4, 8 s (2, 4, 8, 16 recorded)": {"_call": source_mutant(
            "_call", ("_sleep(wait)", "_sleep(wait // 2)"))},
        "the wait recorded as 0": {"_call": source_mutant(
            "_call", ('"waited_before_s": wait', '"waited_before_s": 0'))},
        "only the last attempt recorded": {"_call": source_mutant(
            "_call", ('rec["attempts"].append(', 'rec["attempts"].clear() or rec["attempts"].append('))},
        "a resend posts a seed": {"_call": source_mutant("_call", (
            "code = _attempt(req, rec, stall_s, out)",
            "code = _attempt(req if n == 1 else urllib.request.Request(API, data=json.dumps({**payload, "
            "\"seed\": n}).encode(), headers=dict(req.header_items())), rec, stall_s, out)"))},
        "the first attempt's request id kept": {"_call": source_mutant("_call", ("request_id=None, ", ""))},
        "the first attempt's model and message id kept": {"_call": source_mutant(
            "_call", ("model_version=None, message_id=None,", ""))},
        "the first attempt's usage kept": {"_call": source_mutant("_call", (
            'out = {"blocks": [], "usage": {}, "attempt_s": None}',
            'out = out or {"blocks": [], "usage": {}, "attempt_s": None}'))},
        "output_tokens None on error": {"_call": drop_output_on_error},
        "the attempt's error and error_body None": {"_call": attempt_error_none},
    }
    control = sweep()
    check("9 control: the sweep passes on the client as it is", not control, "; ".join(control[:4]))
    for name, attrs in mutants.items():
        for attr, fn in attrs.items():
            setattr(ac, attr, fn)
        try:
            bad = sweep()
        finally:
            restore()
        check(f"9 mutant caught: {name}", bad, f"{len(bad)} fail: " + "; ".join(bad[:4]) + ("; ..." if len(bad) > 4 else ""))
finally:
    restore()

# 10. The adapter, inside a run context experiment.context builds
tmp = Path(tempfile.mkdtemp(prefix="check_anthropic_"))
IDENT = f"anthropic::{MODEL}"
LOG["scripts"] = []   # 10's own requests, for the invariants of 8 at its end


def lines(sink):
    f = sink / "calls.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


try:
    rid = ex.run_id("exp_01", "single_pass", "check")
    ctx = ex.context("exp_01", "single_pass", "Q001", 1, {"generator": IDENT}, base_url="http://127.0.0.1:9",
                     run=rid, sink=ex.sink(rid, root=tmp))
    check("10 experiment.context allows anthropic::claude-haiku-4-5 as generator",
          ctx.allowed.get(MODEL) == "generator", json.dumps(ctx.allowed))
    e = raises(LockError, lambda: ex.context("exp_01", "single_pass", "Q001", 1, {"generator": "anthropic::gemma3:27b"},
                                             base_url="http://127.0.0.1:9", run=ex.run_id("exp_01", "single_pass", "bad"),
                                             sink=ex.sink(ex.run_id("exp_01", "single_pass", "bad"), root=tmp)))
    check("10 experiment.context refuses anthropic::gemma3:27b", e is not None, str(e)[:110])
    with rc.run(ctx):
        rc.set_passages(["p1"])
        sent = fake([FakeResponse(stream())])
        out = la.generate(IDENT, "What does STAR do?", options={"temperature": 9, "top_p": 0.1}, think="high")
        rec = lines(ctx.sink)[-1]
        check("10 lock_adapter.generate: text, done_reason stop, counts; the caller's options never sent; headers, "
              "timeout and endpoint as in 2",
              out["response"] == "STAR aligns reads." and out["done_reason"] == "stop"
              and (out["prompt_eval_count"], out["eval_count"]) == (21, 12) and body_conforms(sent[0])
              and headers_conform(headers[0], wire[0]) and timeouts == [None] and endpoints == [ENDPOINT],
              f"{sorted(headers[0])} {timeouts} {endpoints}")
        check("10 one record: provider anthropic, role generator, caller_asked, prompt_sent, passages, call site",
              len(lines(ctx.sink)) == 1 and rec["provider"] == "anthropic" and rec["role"] == "generator"
              and rec["caller_asked"]["options"] == {"temperature": 9, "top_p": 0.1}
              and rec["prompt_sent"] == "What does STAR do?" and rec["passages"] == ["p1"]
              and (rec["call_site"] or "").startswith("experiments/runner/check_anthropic.py"),
              f"{rec['provider']} {rec['role']} {rec['call_site']}")
        sent = fake([FakeResponse(stream("max_tokens"))])
        out = la.chat(IDENT, MSGS[:3])
        rec = lines(ctx.sink)[-1]
        check("10 lock_adapter.chat: length returns the text with done_reason length; messages_sent as given",
              out["done_reason"] == "length" and out["message"]["content"] == "STAR aligns reads."
              and out["message"]["tool_calls"] == [] and rec["messages_sent"] == MSGS[:3]
              and body_conforms(sent[0], system=True) and endpoints == [ENDPOINT])
        n = len(lines(ctx.sink))
        sent = fake([http_error(400, "invalid_request_error"), FakeResponse(stream())])
        e = raises(la.LockCallError, lambda: la.generate(IDENT, "x"))
        check("10 an error (HTTP 400) raises LockCallError with the record written, transient None, one request",
              e is not None and e.transient is None and len(sent) == 1 and len(lines(ctx.sink)) == n + 1
              and lines(ctx.sink)[-1]["status"] == "error", str(e)[:110])
        n = len(lines(ctx.sink))
        sent = fake([http_error(529, "overloaded_error"), FakeResponse(stream()), FakeResponse(stream())], expect=2)
        out = la.generate(IDENT, "x")
        rec = lines(ctx.sink)[-1]
        check("10 HTTP 529 then an answer: resent inside the client, the answer returned, one record holding both "
              "attempts (529 waited 0, then ok after 2 s)",
              out["response"] == "STAR aligns reads." and len(sent) == 2 and len(lines(ctx.sink)) == n + 1
              and [(a["http_code"], a["waited_before_s"], a["status"]) for a in rec["attempts"]]
              == [(529, 0, "error"), (None, 2, "ok")] and slept() == [2], json.dumps(rec["attempts"])[:200])
        n = len(lines(ctx.sink))
        sent = fake([http_error(529, "overloaded_error") for _ in range(5)] + [FakeResponse(stream())], expect=5)
        e = raises(la.LockCallError, lambda: la.generate(IDENT, "x"))
        check("10 five HTTP 529s: LockCallError after 5 requests, one record with 5 attempts, transient None",
              e is not None and e.transient is None and len(sent) == 5 and len(lines(ctx.sink)) == n + 1
              and len(lines(ctx.sink)[-1]["attempts"]) == 5 and slept() == [2, 4, 8, 16], str(e)[:110])

        def in_judge():
            with la.judge():
                return la.generate(IDENT, "x")

        def in_retry():
            with la.retry({"attempt": 1}):
                return la.generate(IDENT, "x")

        n = len(lines(ctx.sink))
        for name, fn in {
            "the judge scope": in_judge,
            "a retry scope": in_retry,
            "tools": lambda: la.chat(IDENT, MSGS[2:3], tools=[{"type": "function", "function": {"name": "f"}}]),
            "images": lambda: la.generate(IDENT, "x", images=["aGk="]),
            "claude::": lambda: la.generate(f"claude::{MODEL}", "x"),
        }.items():
            sent = fake([])
            e = raises(LockError, fn)
            check(f"10 {name} refused, nothing posted, no record", e is not None and not sent
                  and len(lines(ctx.sink)) == n, str(e)[:100])
        rc.set_passages(BIG_PASSAGES)

        def adapter_big_generate() -> dict:
            """{part: passes}: lock_adapter.generate with 8's prompt, compared with what was posted and recorded."""
            sent = fake([big_stream()])
            out = la.generate(IDENT, BIG_PROMPT)
            rec = lines(ctx.sink)[-1]
            return {
                "the prompt posted whole": sent[0]["messages"] == [{"role": "user", "content": BIG_PROMPT}],
                "request_sha256 is the sha256 of the bytes posted":
                    rec["request_sha256"] == hashlib.sha256(posted[0]).hexdigest(),
                "the body posted has the lock's keys and values": body_conforms(sent[0]),
                "prompt_sent, answer, content_blocks and 500 passages recorded whole":
                    out["response"] == ANSWER and rec["prompt_sent"] == BIG_PROMPT and rec["text"] == ANSWER
                    and rec["content_blocks"] == ANSWER_BLOCKS and rec["passages"] == BIG_PASSAGES,
                "timeout None, POST to the endpoint": timeouts == [None] and endpoints == [ENDPOINT],
            }

        parts = adapter_big_generate()
        broken = [k for k, ok in parts.items() if not ok]
        check("10 lock_adapter.generate with 8's prompt: posted whole, request_sha256 of the bytes posted, calls.jsonl "
              "keeps prompt, answer, content_blocks and 500 passages whole", not broken, "; ".join(broken))
        LA_GENERATE = la.generate
        la.generate = source_mutant(
            "generate", ("anthropic_client.generate(lock, name, ctx.draw, prompt,",
                         "anthropic_client.generate(lock, name, ctx.draw, prompt[:200000],"), module=la, fn=LA_GENERATE)
        try:
            parts, _ = scoped(adapter_big_generate)
            broken = [k for k, ok in parts.items() if not ok]
        finally:
            la.generate = LA_GENERATE
        check("10 mutant caught: prompt[:200000] in lock_adapter's Anthropic generate branch", broken,
              "; ".join(broken))
        sent = fake([big_stream()])
        out = la.chat(IDENT, BIG_CHAT)
        rec = lines(ctx.sink)[-1]
        check("10 calls.jsonl keeps 8's system, 41 turns, answer and 500 passages whole (chat)",
              out["message"]["content"] == ANSWER and rec["messages_sent"] == BIG_CHAT
              and rec["messages_posted"] == BIG_TURNS and rec["system_sent"] == BIG_SYSTEM
              and rec["text"] == ANSWER and rec["passages"] == BIG_PASSAGES and timeouts == [None]
              and body_conforms(sent[0], system=True) and endpoints == [ENDPOINT])
    report_log("10 every request of 10", LOG["scripts"])
finally:
    restore()

# 11. Live
if args.live:
    r = ac.generate(lock, MODEL, 1, "In one sentence: what does the STAR aligner do in an RNA-seq pipeline?")
    check("11 live: status ok at the lock's settings, the dated snapshot answering",
          r["status"] == "ok" and r["model_version"] == WANT["model"] and r["output_tokens"],
          f"{r['status']} {r['error']} {r['model_version']} {r['prompt_tokens']}+{r['output_tokens']} "
          f"{r['wall_s']} s request {r['request_id']}")

print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
