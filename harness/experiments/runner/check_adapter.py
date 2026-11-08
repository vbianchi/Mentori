"""Checks for experiments/mentori/backend/agents/lock_adapter.py and ModelRouter's three call methods (A1, D67).

Run from the repository root inside the Mentori copy's environment:

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_adapter [--offline]
        [--base-url http://127.0.0.1:21441]

Offline (a stub Ollama server on 127.0.0.1 and a fake Gemini HTTP layer; no model, no key):
1. ModelRouter.generate and chat with options {temperature 9, num_ctx 5}, think "high" and a [think:high] suffix send
   exactly the lock's request (the bytes the stub receives decode to what Lock.ollama builds), and the record keeps
   all three in caller_asked, with the call site in this file.
2. Outside a run context the call is refused; a model the run does not allow, a model in a role the run does not
   allow, Gemini as judge, claude::, and a caller system prompt for generate are refused. Nothing reaches the server
   and no record is written for any of them.
3. chat_stream yields two Ollama-format lines (message, then done with the counts); the planner's parsing loop
   (planner.py:151-171, copied) rebuilds the content, the thinking and the token usage.
4. An error status raises LockCallError with the record written (status error); a length stop returns the text
   with done_reason "length". A server that cannot be reached raises LockCallError with a record (status error)
   for generate and chat. str() of a result never carries the prompt or the messages (lock_record's repr is
   "<lock_record seq N>"). The messages are recorded as they were when the call began, even when the caller's list
   grows during the call, and caller_asked counts the images inside chat messages.
5. Gemini: the request carries the lock's generationConfig and the system message as systemInstruction (Q28); the
   functionCall comes back in Ollama's tool_calls shape, step_executor._extract_tool_calls reads it, and
   _gemini_parts echoed in the next turn go out unchanged.
6. The judge scope sends the lock's judge settings; a candidate scope sends seed draw * 1000 + k.
8. D80 V1 (audit F34, F35): Ollama's "error parsing tool call" inside a 200 stream raises LockCallError with transient
   "tool-call parse error" and a text holding neither "(500)" nor "timed out"; transient() names an Ollama stall and
   nothing else (an unreached server, a Gemini stall, a Gemini status, a Gemini error with the same text; for an HTTP
   500 and another error inside the stream see 9 and D83 Q155 below), and a Gemini stall through gemini_client raises LockCallError with transient None and a text
   without "timed out". A retry scope writes transient_retry into the record of each call inside it and of no other.
   Inside text_tool_calls, an Ollama chat with tools whose reply is an add_cell written as text returns it as message
   tool_calls (the native tool_calls recorded empty, tool_calls_from_text holding what was read); outside the scope,
   without tools, on a length stop, beside a native call in the same reply (the native call kept) and in a Gemini
   reply holding the same text nothing is read (tool_calls_from_text null); a reader that raises still leaves the
   call's record.
9. D81 (Q136-Q138) and the last D80 V1 finding. Through the stub and the real ollama_client: an HTTP 500, a
   connection closed with no response (RemoteDisconnected) and a connection reset (ConnectionResetError) each raise
   LockCallError with its record, transient "HTTP 500" or "dropped connection"; transient() also names the
   URLError-wrapped reset and httpx's "Server disconnected", and nothing for Gemini. On a scratch lock with
   [generation] retry_seed, a call in retry scope r sends seed + 1,000,000 * r (draw 1: 1000001, 3000001; candidate
   3: 2001003), passes ollama_client's own lock check, and its record carries retry and seed_sent; on a lock without
   the key (LOCK.toml until the coordinator adds it) a retry is refused before any request with no record. A
   Gemini call, a judge call and a scope with no attempt are refused inside a retry scope, nothing posted. A
   Python-call and a header-form reply are read through the adapter; generate() inside text_tool_calls records no
   tool_calls_from_text (only chat() does).
D83 Q155. Through the stub and the real ollama_client: any error sent inside a stream that began with 200 OK (the
   stub's "model failed", Ollama's "model runner has unexpectedly stopped" after a first chunk) is transient "error
   inside the stream", and a stream with no final chunk is "no final chunk", whether it closes between chunks or
   partway through a chunk of a chunked reply (http.client.IncompleteRead, recorded by ollama_client as
   "IncompleteRead: ...", not raised: review of 17 Oct F1); a line that is not JSON (recorded as
   ollama_client's own "JSONDecodeError: ...") is not transient. transient() on records: an in-stream error needs a
   line read (first_token_s) and a text that is not ollama_client's "<exception class>: <message>"; nothing for Gemini.
D89 (Q145 O3). Through gemini_client over a fake HTTP layer: an empty reply (STOP, and a stream with no finishReason
   and nothing in it), a blocked prompt and an answer blocked after text was streamed each return from chat and
   generate with done_reason stop, empty text, no tool call and no parts to echo, while the record (written once)
   keeps the status, Google's reason and the streamed text; the next turn sends the empty model turn as "[Empty]" and
   goes on.
D90 (Q1, Q2). A recitation stop after streamed text, a malformed_function_call with no part, and a malformed_response
   after a text part and a function call part each return from chat and generate with done_reason stop and what the
   stream held (text, the function call in Ollama's shape, the parts to echo), the record written once with the
   status and Google's reason; the next turn after a malformed reply with no part sends "[Empty]" and goes on; a
   finishReason OTHER still raises LockCallError (transient None); for Ollama the five returned statuses still raise.
10. D92 Q188: a Gemini reply ended for language, other, unexpected_tool_call or too_many_tool_calls returns the
   streamed text with done_reason stop and its status kept; a reason Q188 does not name (no_image) still raises.
   D92 Q199: an Anthropic record gets session_id, code_commit and code_dirty in _append, a record with its own
   keeps them, an unreached-server record carries them before _append, and every call record the check wrote, in
   every sink, carries this process's values.
Live (skipped with --offline):
7. One ModelRouter.generate and one chat_stream on qwen3-coder:30b at --base-url (an ssh tunnel to the Studio's
   paper server), and one ModelRouter.chat with a tool on gemini-3-flash-preview; each writes one record to a
   temporary sink.
"""

import argparse
import asyncio
import io
import json
import re
import socket
import struct
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "mentori"))

from backend.agents import lock_adapter as la  # noqa: E402
from backend.agents.model_router import ModelRouter  # noqa: E402
from backend.agents.notebook.step_executor import STEP_TOOLS_SCHEMA, _extract_tool_calls  # noqa: E402
from backend.agents.notebook import step_executor as se  # noqa: E402

from experiments.runner import gemini_client as gc  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner import ollama_client as oc  # noqa: E402
from experiments.runner.lock import LOCK, Lock, LockError, load  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--base-url", default="http://127.0.0.1:21441")
ap.add_argument("--offline", action="store_true")
a = ap.parse_args()
if ":11434" in a.base_url:
    sys.exit("refused: port 11434 is never a paper server")

GEN, JUDGE, GEM = "qwen3-coder:30b", "devstral-small-2:24b", "gemini-3-flash-preview"
lock = load()
router = ModelRouter()
results = []
tmp = Path(tempfile.mkdtemp(prefix="check_adapter_"))


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    return None


def lines(sink: Path) -> list:
    f = sink / "calls.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def read_of(r, key=None):
    """D80 V1: the record's tool_calls_from_text (or one key of it); "absent" when the record has no such key."""
    v = r.get("tool_calls_from_text", "absent")
    return v if key is None else (v.get(key) if isinstance(v, dict) else "absent")


def ctx_for(base, sink, allowed, draw=1, thinking=None, item="Q001"):
    return rc.RunContext(run_id="check-adapter", arm="check", item_id=item, draw=draw, thinking=thinking,
                         base_url=base, sink=sink, allowed=allowed)


# D80 V1: the error text as the laptop low run recorded it (COUNTERCHECKS A5 F34), and a text-form call in the shape
# gpt-oss:20b wrote at high (exp_05__coder_v2_n1__gpt-oss-20b+high seq 4, airway_1_dimensions, trimmed)
# D83 Q155: the text the submitted run's result files hold 30 times as "Ollama error (500): model runner has ..."
RUNNER_STOPPED = ("model runner has unexpectedly stopped, this may be due to resource limitations or an internal "
                  "error, check ollama server logs for details")
PARSE_ERROR = ("error parsing tool call: raw='{\"cell_type\":\"code\",\"source\":\"# Step 6: ...', "
               "err=invalid character 'p' looking for beginning of value")
# D81 Q137: the Python-call and header forms (exp_05__coder_v2_n1__gpt-oss-20b+high seq 11 airway_5 and seq 6 airway_8,
# trimmed)
PY_CALL = ('```python\ncell_id = functions.add_cell(\n    cell_type="code",\n    source="""import pandas as pd"""\n)\n'
           'functions.execute_cell(cell_id=cell_id)\n```')
HEADER_CALL = ('commentary to=functions.add_cell:\n{\n  "cell_type": "code",\n  "source": "import pandas as pd"\n}\n'
               'commentary to=functions.execute_cell:\n{\n  "cell_id": "0"\n}')
# D81 Q136: a scratch lock with [generation] retry_seed (LOCK.toml's bytes, the line added when it is not there yet)
RETRY_LINE = b'retry_seed = "seed + 1000000 * retry"   # D81 (Q136)\n'
_raw = LOCK.read_bytes()
RETRY_LOCK = Lock(_raw if re.search(rb"(?m)^retry_seed = ", _raw) else
                  re.sub(rb'(?m)^think = "off"', lambda m: RETRY_LINE + m.group(0), _raw, count=1), LOCK)
NO_RETRY_LOCK = Lock(re.sub(rb"(?m)^retry_seed = .*\n", b"", _raw), LOCK)
TEXT_CALL = ('{\n  "name": "functions.add_cell",\n  "arguments": {\n    "cell_type": "code",\n    "source": '
             '"import pandas as pd"\n  }\n}\n{\n  "name": "functions.execute_cell",\n  "arguments": {\n    '
             '"cell_id": "${cell_id}"\n  }\n}')


class Stub(BaseHTTPRequestHandler):
    """Answers like Ollama 0.40.2 holding every model in the lock; keeps each request body; mode picks the reply."""
    bodies, mode, shared = [], "ok", None

    def do_GET(self):
        body = ({"version": lock.d["server"]["ollama_version"]} if self.path == "/api/version"
                else {"models": [{"name": t, "digest": r["digest"]} for t, r in lock.d["models"].items()]})
        self._lines([body])

    def do_POST(self):
        Stub.bodies.append(self.rfile.read(int(self.headers["Content-Length"])))
        if Stub.mode == "grow":                                   # another task appends to the caller's list
            Stub.shared.append({"role": "user", "content": "appended during the call"})
        done = {"done": True, "done_reason": "length" if Stub.mode == "length" else "stop",
                "prompt_eval_count": 11, "eval_count": 7}
        if Stub.mode == "error":
            self._lines([{"error": "stub: model failed"}])
        elif Stub.mode == "http500":                              # D81 Q138: Ollama's HTTP 500 before any stream
            body = json.dumps({"error": "llama runner process has terminated: exit status 2"}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif Stub.mode == "disconnect":                           # D81 Q138: closed with no response at all
            self.close_connection = True
        elif Stub.mode == "reset":                                # D81 Q138: the connection reset (RST)
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            self.connection.close()
            self.close_connection = True
        elif Stub.mode in ("py_call", "header_call"):            # D81 Q137: the other two text forms
            self._lines([{"message": {"role": "assistant",
                                      "content": PY_CALL if Stub.mode == "py_call" else HEADER_CALL}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, **done}])
        elif Stub.mode == "crash":                                # D83 Q155: a crash mid-answer, inside a 200
            self._lines([{"message": {"role": "assistant", "content": "Let me "}, "done": False},
                         {"error": RUNNER_STOPPED}])
        elif Stub.mode == "no_final":                             # D83 Q155: the stream ends with no final chunk
            self._lines([{"message": {"role": "assistant", "content": "Let me "}, "done": False}])
        elif Stub.mode == "cut_chunk":                            # review F1: a chunked reply closed partway
            line = (json.dumps({"message": {"role": "assistant", "content": "Let me "}, "done": False}) + "\n").encode()
            self.send_response(200)                               # through its second chunk
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b"%x\r\n" % len(line) + line + b"\r\n" + b"40\r\n{\"message\": {\"ro")
            self.wfile.flush()
            self.close_connection = True
        elif Stub.mode == "bad_line":                             # a line that is not JSON, mid-answer
            self._lines([{"message": {"role": "assistant", "content": "Let me "}, "done": False}], tail=b"{not json\n")
        elif Stub.mode == "parse_error":                          # as Ollama 0.40.2 streams it: inside a 200
            self._lines([{"message": {"role": "assistant", "content": ""}, "done": False},
                         {"error": PARSE_ERROR}])
        elif Stub.mode in ("text_call", "text_call_length"):     # gpt-oss at high: the call written as text
            self._lines([{"message": {"role": "assistant", "content": TEXT_CALL}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, **done,
                          "done_reason": "length" if Stub.mode == "text_call_length" else "stop"}])
        elif Stub.mode == "text_and_native":                      # the text-form call and a native call, one reply
            self._lines([{"message": {"role": "assistant", "content": TEXT_CALL, "tool_calls": [
                             {"function": {"name": "get_weather", "arguments": {"city": "Paris"}}}]}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, **done}])
        elif self.path == "/api/chat":
            self._lines([{"message": {"role": "assistant", "content": "", "thinking": "Let me see. "}, "done": False},
                         {"message": {"role": "assistant", "content": "Hello ", "thinking": "Done."}, "done": False},
                         {"message": {"role": "assistant", "content": "there.", "tool_calls": [
                             {"function": {"name": "get_weather", "arguments": {"city": "Paris"}}}]}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, **done}])
        else:
            self._lines([{"response": "Hello ", "done": False}, {"response": "there.", "done": False},
                         {"response": "", **done}])

    def _lines(self, objs, tail=b""):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for o in objs:
            self.wfile.write((json.dumps(o) + "\n").encode())
        self.wfile.write(tail)

    def log_message(self, *args):
        pass


def planner_parse(chunks: list) -> tuple:
    """planner.py:151-171 (analyze_query), copied: content, thinking and the token_usage events."""
    full_thinking, full_content, usage = "", "", []
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if "message" in data:
                delta = data["message"]
                if "thinking" in delta:
                    full_thinking += delta["thinking"]
                if "content" in delta:
                    full_content += delta["content"]
            if data.get("done") is True and "eval_count" in data:
                usage.append({"input": data.get("prompt_eval_count", 0), "output": data.get("eval_count", 0),
                              "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)})
            if "usage" in data:
                usage.append({"gemini_usage": data["usage"]})
        except json.JSONDecodeError:
            continue
    return full_content, full_thinking, usage


async def collect(gen) -> list:
    return [c async for c in gen]


TOOL = {"type": "function", "function": {"name": "get_weather", "description": "Get the current weather for a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
ASK = {"temperature": 9, "num_ctx": 5}

# 1 to 6, offline, against the stub
stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
sbase = f"http://127.0.0.1:{stub.server_address[1]}"
sink = tmp / "offline"
ctx = ctx_for(sbase, sink, {GEN: "generator", JUDGE: "judge", GEM: "generator"})
want = lock.ollama(GEN, draw=1)

with rc.run(ctx):
    Stub.bodies.clear()

    async def mentori_caller():
        """A caller as in the copy: a coroutine that awaits the router."""
        return await router.generate(f"ollama::{GEN}[think:high]", "Say hello.", options=dict(ASK), think="high")
    out = asyncio.run(mentori_caller())
    sent = json.loads(Stub.bodies[-1])
    rec = lines(sink)[-1]
    check("1 generate sends exactly the lock's payload (options 9/5, think high and the suffix not sent)",
          sent == want.payload("Say hello.") and sent["options"]["num_ctx"] == lock.d["generation"]["num_ctx"],
          f"temperature {sent['options']['temperature']}, num_ctx {sent['options']['num_ctx']}, "
          f"think {sent.get('think', 'not sent')}")
    check("1 generate records caller_asked (options, think, suffix) and the call site in this file",
          rec["caller_asked"]["options"] == ASK and rec["caller_asked"]["think"] == "high"
          and rec["caller_asked"]["think_suffix"] == "[think:high]" and rec["caller_asked"]["method"] == "generate"
          and rec["call_site"].startswith("experiments/runner/check_adapter.py:")
          and rec["call_site"].endswith(" mentori_caller") and rec["prompt_sent"] == "Say hello."
          and rec["role"] == "generator" and rec["provider"] == "ollama" and rec["seq"] == 1, rec["call_site"])
    check("1 generate returns Mentori's shape",
          set(out) == {"response", "thinking", "done_reason", "prompt_eval_count", "eval_count", "lock_record"}
          and out["response"] == "Hello there." and out["done_reason"] == "stop"
          and (out["prompt_eval_count"], out["eval_count"]) == (11, 7) and out["lock_record"]["seq"] == 1)
    check("1 str() of the generate result carries no prompt (lock_record's repr names the seq only)",
          "Say hello" not in str(out) and repr(out["lock_record"]) == "<lock_record seq 1>"
          and out["lock_record"]["prompt_sent"] == "Say hello.", repr(out["lock_record"]))

    asyncio.run(router.generate(f"ollama::{GEN}", "Say hello."))
    check("1 a router coroutine run as the task itself (no awaiting caller) records call_site None, not asyncio",
          lines(sink)[-1]["call_site"] is None and lines(sink)[-1]["seq"] == 2)

    msgs = [{"role": "user", "content": "Weather in Paris?"}]
    out = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=[TOOL], options=dict(ASK), think="high"))
    sent = json.loads(Stub.bodies[-1])
    rec = lines(sink)[-1]
    check("1 chat sends exactly the lock's options and fields, the messages and tools whole",
          sent["options"] == want.options and {k: sent[k] for k in want.fields} == want.fields
          and "think" not in sent and sent["messages"] == msgs and sent["tools"] == [TOOL] and sent["model"] == GEN,
          json.dumps(sent["options"]))
    check("1 chat records caller_asked, messages_sent (verified against the runner's hash) and tools_given",
          rec["caller_asked"]["options"] == ASK and rec["caller_asked"]["tools"] is True
          and rec["messages_sent"] == msgs and rec["messages_sent_verified"] is True
          and rec["tools_given"]["names"] == ["get_weather"])
    check("1 chat returns Mentori's shape with Ollama tool calls",
          out["message"] == {"role": "assistant", "content": "Hello there.", "thinking": "Let me see. Done.",
                             "tool_calls": [{"function": {"name": "get_weather", "arguments": {"city": "Paris"}}}]}
          and _extract_tool_calls(out) == [{"name": "get_weather", "arguments": {"city": "Paris"}}]
          and out["response"] == "Hello there." and "Weather in Paris" not in str(out))

    # 2. refusals: nothing sent, nothing recorded
    n_bodies, n_lines = len(Stub.bodies), len(lines(sink))
    refusals = {
        "a model the run does not allow": (LockError, lambda: la.generate("ollama::gemma3:27b", "x")),
        "the judge model as a generator": (LockError, lambda: la.generate(f"ollama::{JUDGE}", "x")),
        "a generator model in the judge scope": (LockError, lambda: _in_judge(lambda: la.generate(GEN, "x"))),
        "Gemini in the judge scope": (LockError, lambda: _in_judge(lambda: la.generate(f"gemini::{GEM}", "x"))),
        "claude:: (no Anthropic route yet)": (LockError, lambda: la.chat("claude::claude-haiku-4-5", msgs)),
        "a caller system prompt for generate": (LockError, lambda: asyncio.run(
            router.generate(f"ollama::{GEN}", "x", system="You are terse."))),
    }

    def _in_judge(fn):
        with la.judge():
            return fn()
    for name, (exc, fn) in refusals.items():
        e = raises(exc, fn)
        check(f"2 refused: {name}", e is not None, str(e)[:110])
    check("2 the refusals sent nothing and wrote no record",
          len(Stub.bodies) == n_bodies and len(lines(sink)) == n_lines)

    # 3. chat_stream
    chunks = asyncio.run(collect(router.chat_stream(f"ollama::{GEN}", msgs, options=dict(ASK))))
    content, thinking, usage = planner_parse(chunks)
    check("3 chat_stream yields two Ollama-format lines, message then done",
          len(chunks) == 2 and set(json.loads(chunks[0])) == {"message"}
          and json.loads(chunks[1]) == {"done": True, "done_reason": "stop", "prompt_eval_count": 11, "eval_count": 7},
          chunks[1])
    check("3 the planner's parsing rebuilds content, thinking and one token_usage",
          (content, thinking, usage) == ("Hello there.", "Let me see. Done.", [{"input": 11, "output": 7,
                                                                                  "total": 18}]))
    check("3 chat_stream's record names its method and its caller",
          lines(sink)[-1]["caller_asked"]["method"] == "chat_stream"
          and lines(sink)[-1]["call_site"].startswith("experiments/runner/check_adapter.py:"),
          lines(sink)[-1]["call_site"])

    # 4. error and length
    Stub.mode = "error"
    e = raises(la.LockCallError, lambda: asyncio.run(router.generate(f"ollama::{GEN}", "x")))
    check("4 an error status raises LockCallError and the record is written",
          e is not None and e.record["status"] == "error" and lines(sink)[-1]["status"] == "error"
          and lines(sink)[-1]["seq"] == e.record["seq"], e.record["error"] if e else "no exception")
    e = raises(la.LockCallError, lambda: list(asyncio.run(collect(router.chat_stream(f"ollama::{GEN}", msgs)))))
    check("4 chat_stream raises too, never yields 'Error:' text", e is not None and e.record["status"] == "error")
    Stub.mode = "length"
    out = asyncio.run(router.chat(f"ollama::{GEN}", msgs))
    check("4 a length stop returns the text with done_reason length",
          out["done_reason"] == "length" and out["message"]["content"] == "Hello there."
          and lines(sink)[-1]["status"] == "length")
    Stub.mode = "ok"

    shared = [{"role": "user", "content": "Weather in Paris?"}]
    Stub.mode, Stub.shared = "grow", shared
    out = asyncio.run(router.chat(f"ollama::{GEN}", shared))
    Stub.mode, Stub.shared = "ok", None
    rec = lines(sink)[-1]
    check("4 messages_sent is the list as it was when the call began, verified, though the caller's list grew",
          len(shared) == 2 and rec["messages_sent"] == shared[:1] and rec["messages_sent_verified"] is True,
          f"caller's list now {len(shared)} messages, recorded {len(rec['messages_sent'])}")

    img = "aW1hZ2U="                                              # base64 of b"image"
    asyncio.run(router.chat(f"ollama::{GEN}", [{"role": "user", "content": "What is this?", "images": [img]}]))
    rec = lines(sink)[-1]
    check("4 caller_asked counts the images inside chat messages; messages_sent keeps their sha256s only",
          rec["caller_asked"]["images"] == 1 and "images" not in rec["messages_sent"][0]
          and len(rec["messages_sent"][0]["images_sha256"]) == 1, str(rec["caller_asked"]))

    # 6. judge scope and candidate scope
    with la.judge():
        out = asyncio.run(router.generate(f"ollama::{JUDGE}", "Score this.", options={"temperature": 0.5}))
    sent, jwant = json.loads(Stub.bodies[-1]), lock.ollama(JUDGE, role="judge")
    check("6 the judge scope sends the lock's judge request (temperature 0, think off, date-fixed system)",
          sent == jwant.payload("Score this.") and lines(sink)[-1]["role"] == "judge"
          and lines(sink)[-1]["draw"] is None, f"temperature {sent['options']['temperature']}")
    with la.candidate(3):
        asyncio.run(router.chat(f"ollama::{GEN}", msgs))
    check("6 a candidate scope sends seed draw * 1000 + k",
          json.loads(Stub.bodies[-1])["options"]["seed"] == 1003 and lines(sink)[-1]["candidate"] == 3)

    # 8. D80 V1: transient failures, the retry record, a call written as text
    Stub.mode = "parse_error"
    e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA)))
    check("8 a tool-call parse error inside a 200 stream: LockCallError, transient 'tool-call parse error', and a "
          "text the submitted rule ('(500)', 'timed out') cannot match",
          e is not None and e.transient == "tool-call parse error" and e.record["error"] == PARSE_ERROR
          and lines(sink)[-1]["seq"] == e.record["seq"] and "(500)" not in str(e) and "timed out" not in str(e),
          str(e)[:100] if e else "no exception")
    Stub.mode = "error"
    e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA)))
    check("8, D83 Q155 another error inside the stream is transient 'error inside the stream' (it was not before Q155)",
          e is not None and e.transient == "error inside the stream" and e.record.get("first_token_s") is not None,
          (e.record["error"], e.transient) if e else "no exception")
    # D83 Q155 through the stub and the real client: a crash after the answer began, a stream with no final chunk, and
    # (not transient) a line that is not JSON, which ollama_client records as its own "JSONDecodeError: ..."
    for mode, want_tr, want_err in (("crash", "error inside the stream", RUNNER_STOPPED),
                                    ("no_final", "no final chunk", "the stream ended without a final chunk"),
                                    ("cut_chunk", "no final chunk", "IncompleteRead: "),
                                    ("bad_line", None, "JSONDecodeError: ")):
        Stub.mode = mode
        n_lines = len(lines(sink))
        e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA)))
        Stub.mode = "ok"
        check(f"D83 Q155 {mode}: LockCallError with its record (status error, the answer begun), transient {want_tr!r}",
              e is not None and e.transient == want_tr and e.record["status"] == "error"
              and e.record["error"].startswith(want_err) and e.record.get("first_token_s") is not None
              and len(lines(sink)) == n_lines + 1 and lines(sink)[-1]["seq"] == e.record["seq"],
              (e.record["error"][:90], e.transient) if e else "no exception")
    Stub.mode = "ok"
    tr = {"stalled": {"provider": "ollama", "status": "stalled", "error": "no new token for 600 s"},
          "other error": {"provider": "ollama", "status": "error", "error": "stub: model failed"},
          "unreached": {"provider": "ollama", "status": "error",
                        "error": "before the request was posted: URLError: refused"},
          "HTTP 500": {"provider": "ollama", "status": "error", "error": "HTTP 500: server busy"},
          "HTTP 502": {"provider": "ollama", "status": "error", "error": "HTTP 502: bad gateway"},
          "RemoteDisconnected": {"provider": "ollama", "status": "error",
                                 "error": "RemoteDisconnected: Remote end closed connection without response"},
          "ConnectionResetError": {"provider": "ollama", "status": "error",
                                   "error": "ConnectionResetError: [Errno 54] Connection reset by peer"},
          "reset while posting": {"provider": "ollama", "status": "error",
                                  "error": "URLError: <urlopen error [Errno 54] Connection reset by peer>"},
          "Server disconnected": {"provider": "ollama", "status": "error",
                                  "error": "Server disconnected without sending a response."},
          "a text naming 500 elsewhere": {"provider": "ollama", "status": "error", "error": "stub: HTTP 500 later"},
          # D83 Q155: first_token_s present = a line of the stream was read before the error
          "crash inside the stream": {"provider": "ollama", "status": "error", "error": RUNNER_STOPPED,
                                      "first_token_s": 3.2},
          "run error inside the stream": {"provider": "ollama", "status": "error", "first_token_s": 0.4,
                                          "error": "an error was encountered while running the model: unexpected EOF"},
          "no final chunk": {"provider": "ollama", "status": "error", "first_token_s": 1.0,
                             "error": "the stream ended without a final chunk"},
          "cut mid-chunk": {"provider": "ollama", "status": "error", "first_token_s": 1.0,
                            "error": "IncompleteRead: IncompleteRead(0 bytes read)"},
          "no final chunk, no line read": {"provider": "ollama", "status": "error",
                                           "error": "the stream ended without a final chunk"},
          "client's own text mid-stream": {"provider": "ollama", "status": "error", "first_token_s": 1.0,
                                           "error": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)"},
          "client's gaierror mid-stream": {"provider": "ollama", "status": "error", "first_token_s": 1.0,
                                           "error": "gaierror: [Errno 8] nodename nor servname provided"},
          "error inside the stream, empty text": {"provider": "ollama", "status": "error", "first_token_s": 1.0,
                                                  "error": ""},
          "Gemini error inside the stream": {"provider": "gemini", "status": "error", "error": RUNNER_STOPPED,
                                             "first_token_s": 3.2},
          "Gemini no final chunk": {"provider": "gemini", "status": "error",
                                    "error": "the stream ended without a final chunk"},
          "a stall with a line read": {"provider": "ollama", "status": "stalled", "first_token_s": 1.0,
                                       "error": "no new token for 600 s"},
          "cancelled with a line read": {"provider": "ollama", "status": "cancelled", "first_token_s": 1.0,
                                         "error": "the caller went away; the call was closed"},
          "Gemini stalled": {"provider": "gemini", "status": "stalled", "error": "no new chunk for 600 s"},
          "Gemini malformed call": {"provider": "gemini", "status": "malformed_function_call", "error": None},
          "Gemini error, same text": {"provider": "gemini", "status": "error", "error": PARSE_ERROR},
          "Gemini HTTP 500": {"provider": "gemini", "status": "error", "error": "HTTP 500: internal"},
          "Gemini dropped": {"provider": "gemini", "status": "error",
                             "error": "RemoteDisconnected: Remote end closed connection without response"},
          "ok": {"provider": "ollama", "status": "ok", "error": None}}
    got = {k: la.transient(v) for k, v in tr.items()}
    check("8, 9, D83 Q155 transient() names an Ollama stall, an HTTP 500 and a dropped connection (Q138), an error "
          "sent inside a begun stream and a stream with no final chunk (Q155), and nothing else here (no Gemini "
          "failure is transient; ollama_client's own exception text is not an error inside the stream)",
          got == {"stalled": "stalled", "other error": None, "unreached": None, "HTTP 500": "HTTP 500",
                  "HTTP 502": None, "RemoteDisconnected": "dropped connection",
                  "ConnectionResetError": "dropped connection", "reset while posting": "dropped connection",
                  "Server disconnected": "dropped connection", "a text naming 500 elsewhere": None,
                  "crash inside the stream": "error inside the stream",
                  "run error inside the stream": "error inside the stream", "no final chunk": "no final chunk",
                  "no final chunk, no line read": "no final chunk", "cut mid-chunk": "no final chunk",
                  "client's own text mid-stream": None,
                  "client's gaierror mid-stream": None, "error inside the stream, empty text": None,
                  "Gemini error inside the stream": None, "Gemini no final chunk": None,
                  "a stall with a line read": "stalled", "cancelled with a line read": None,
                  "Gemini stalled": None, "Gemini malformed call": None, "Gemini error, same text": None,
                  "Gemini HTTP 500": None, "Gemini dropped": None, "ok": None}, got)

    # 9. Q138 through the real client: each failure leaves a record and is transient
    for mode, want_tr, want_err in (("http500", "HTTP 500", "HTTP 500: llama runner process has terminated"),
                                    ("disconnect", "dropped connection", "RemoteDisconnected: "),
                                    ("reset", "dropped connection", "ConnectionResetError: ")):
        Stub.mode = mode
        n_lines = len(lines(sink))
        e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs,
                                                                      tools=STEP_TOOLS_SCHEMA)))
        Stub.mode = "ok"
        check(f"9 Q138 {mode}: LockCallError with its record (status error), transient {want_tr!r}",
              e is not None and e.transient == want_tr and e.record["status"] == "error"
              and e.record["error"].startswith(want_err) and len(lines(sink)) == n_lines + 1
              and lines(sink)[-1]["seq"] == e.record["seq"], (e.record["error"][:90], e.transient) if e else "none")

    # 9. Q136: the retry seed, on a scratch lock with retry_seed (la.load and ollama_client.load both read it)
    saved_loads = (la.load, oc.load)
    la.load = oc.load = lambda: RETRY_LOCK
    try:
        info = {"attempt": 1, "of": 3, "reason": "tool-call parse error", "failed_seq": 7}
        with la.retry(info):
            asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
        in_scope, sent1 = lines(sink)[-1], json.loads(Stub.bodies[-1])
        with la.retry({**info, "attempt": 3}):
            asyncio.run(router.generate(f"ollama::{GEN}", "x"))
        in_scope3, sent3 = lines(sink)[-1], json.loads(Stub.bodies[-1])
        with la.retry({**info, "attempt": 2}), la.candidate(3):
            asyncio.run(router.chat(f"ollama::{GEN}", msgs))
        in_cand, sentc = lines(sink)[-1], json.loads(Stub.bodies[-1])
        with la.retry(None):
            asyncio.run(router.chat(f"ollama::{GEN}", msgs))
        after, sent0 = lines(sink)[-1], json.loads(Stub.bodies[-1])
    finally:
        la.load, oc.load = saved_loads
    check("8 a retry scope writes transient_retry into that call's record; retry(None) and every earlier record "
          "carry no such key", in_scope.get("transient_retry") == info
          and all("transient_retry" not in r for r in lines(sink)
                  if r["seq"] not in (in_scope["seq"], in_scope3["seq"], in_cand["seq"])),
          json.dumps(in_scope.get("transient_retry")))
    check("9 Q136 retry r sends seed + 1,000,000 * r (1000001, 3000001; candidate 3 retry 2: 2001003), the first try "
          "after it 1, through ollama_client's own lock check",
          [b["options"]["seed"] for b in (sent1, sent3, sentc, sent0)] == [1000001, 3000001, 2001003, 1]
          and {**sent1["options"], "seed": 1} == sent0["options"],
          [b["options"]["seed"] for b in (sent1, sent3, sentc, sent0)])
    check("9 Q136 the retried call's record carries retry and seed_sent; the first try's carries neither",
          [(r.get("retry"), r.get("seed_sent"), r["options_sent"]["seed"]) for r in (in_scope, in_scope3, in_cand)]
          == [(1, 1000001, 1000001), (3, 3000001, 3000001), (2, 2001003, 2001003)]
          and "retry" not in after and "seed_sent" not in after and in_scope3["prompt_sent"] == "x",
          [(r.get("retry"), r.get("seed_sent")) for r in (in_scope, in_scope3, in_cand, after)])

    # 9. refusals inside a retry scope: nothing posted, no record
    n_bodies, n_lines = len(Stub.bodies), len(lines(sink))
    la.load = oc.load = lambda: NO_RETRY_LOCK
    try:
        with la.retry(info):
            e_nokey = raises(LockError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs)))
    finally:
        la.load, oc.load = saved_loads
    la.load = oc.load = lambda: RETRY_LOCK
    try:
        with la.retry(info):
            e_judge = raises(LockError, lambda: _in_judge(lambda: la.generate(f"ollama::{JUDGE}", "x")))
        with la.retry({"of": 3}):
            e_noatt = raises(LockError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs)))
        with la.retry(info):
            e_gem = raises(LockError, lambda: asyncio.run(router.chat(f"gemini::{GEM}", msgs)))
    finally:
        la.load, oc.load = saved_loads
    check("9 Q136 on a lock without retry_seed a retry is refused, naming D81, before any request",
          e_nokey is not None and "D81" in str(e_nokey) and "retry_seed" in str(e_nokey), str(e_nokey)[:100])
    check("9 a judge call, a scope with no attempt and a Gemini call are refused inside a retry scope",
          e_judge is not None and e_noatt is not None and e_gem is not None and "never retried" in str(e_gem),
          [str(x)[:60] for x in (e_judge, e_noatt, e_gem)])
    check("9 the refusals inside a retry scope sent nothing and wrote no record",
          len(Stub.bodies) == n_bodies and len(lines(sink)) == n_lines)

    Stub.mode = "text_call"
    with la.text_tool_calls(se.read_text_tool_call):
        out = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
    rec = lines(sink)[-1]
    want_call = [{"function": {"name": "add_cell",
                               "arguments": {"cell_type": "code", "source": "import pandas as pd"}}}]
    check("8 inside text_tool_calls an add_cell written as text is returned as the call, and step_executor reads it",
          out["message"]["tool_calls"] == want_call and out["message"]["content"] == TEXT_CALL
          and _extract_tool_calls(out) == [{"name": "add_cell", "arguments": want_call[0]["function"]["arguments"]}],
          json.dumps(out["message"]["tool_calls"]))
    check("8 the record keeps the native tool_calls empty and says the call was read from text",
          rec["tool_calls"] == [] and read_of(rec, "calls") == want_call
          and read_of(rec, "names_written") == ["functions.add_cell", "functions.execute_cell"]
          and read_of(rec, "not_read") == [{"name": "functions.execute_cell",
                                                           "arguments": {"cell_id": "${cell_id}"}}]
          and out["lock_record"]["seq"] == rec["seq"], json.dumps(rec.get("tool_calls_from_text"))[:160])
    out = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
    check("8 outside the scope the same reply has no tool call and its record no tool_calls_from_text",
          out["message"]["tool_calls"] == [] and "tool_calls_from_text" not in lines(sink)[-1])
    with la.text_tool_calls(se.read_text_tool_call):
        no_tools = asyncio.run(router.chat(f"ollama::{GEN}", msgs))
        r_no_tools = lines(sink)[-1]
        Stub.mode = "text_call_length"
        cut = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
        r_cut = lines(sink)[-1]
        Stub.mode = "text_and_native"
        native = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
        r_native = lines(sink)[-1]
        Stub.mode = "ok"
    check("8 inside the scope nothing is read without tools or on a length stop (each reply the text-form call)",
          no_tools["message"]["tool_calls"] == [] and read_of(r_no_tools) is None
          and no_tools["message"]["content"] == TEXT_CALL
          and cut["done_reason"] == "length" and cut["message"]["tool_calls"] == []
          and cut["message"]["content"] == TEXT_CALL and read_of(r_cut) is None)
    check("8 a reply holding the text-form call beside a native call: the native call kept, nothing read",
          native["message"]["content"] == TEXT_CALL
          and native["message"]["tool_calls"] == [{"function": {"name": "get_weather",
                                                                "arguments": {"city": "Paris"}}}]
          and r_native["tool_calls"] == native["message"]["tool_calls"] and read_of(r_native) is None,
          json.dumps(r_native.get("tool_calls_from_text")))

    # 9. Q137 through the adapter: the Python-call and header forms are read; generate records no tool_calls_from_text
    got_forms = {}
    for mode in ("py_call", "header_call"):
        Stub.mode = mode
        with la.text_tool_calls(se.read_text_tool_call):
            out = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
        got_forms[mode] = (out["message"]["tool_calls"], read_of(lines(sink)[-1], "form"), lines(sink)[-1]["tool_calls"])
    Stub.mode = "text_call"
    with la.text_tool_calls(se.read_text_tool_call):
        gen_out = asyncio.run(router.generate(f"ollama::{GEN}", "x"))
    r_gen = lines(sink)[-1]
    Stub.mode = "ok"
    check("9 Q137 a Python-call and a header-form reply are returned as the add_cell call, recorded with their form",
          got_forms == {"py_call": (want_call, "python", []), "header_call": (want_call, "header", [])},
          json.dumps(got_forms)[:200])
    check("9 generate() inside text_tool_calls records no tool_calls_from_text (only chat() does)",
          "tool_calls_from_text" not in r_gen and r_gen["caller_asked"]["method"] == "generate"
          and "lock_record" in gen_out)

    def broken(text):
        raise KeyError("reader fault")
    Stub.mode = "text_call"
    n_lines = len(lines(sink))
    with la.text_tool_calls(broken):
        out = asyncio.run(router.chat(f"ollama::{GEN}", msgs, tools=STEP_TOOLS_SCHEMA))
    Stub.mode = "ok"
    check("8 a reader that raises leaves the call's record, with the fault, and no call read",
          len(lines(sink)) == n_lines + 1 and out["message"]["tool_calls"] == []
          and read_of(lines(sink)[-1]) == {"calls": [], "reader_error": "KeyError: 'reader fault'"},
          json.dumps(lines(sink)[-1].get("tool_calls_from_text")))

# 4. a server that cannot be reached: a port nothing listens on, closed before the call
import socket  # noqa: E402
with socket.socket() as _s:
    _s.bind(("127.0.0.1", 0))
    dead = f"http://127.0.0.1:{_s.getsockname()[1]}"
dsink = tmp / "unreachable"
with rc.run(ctx_for(dead, dsink, {GEN: "generator"})):
    e1 = raises(la.LockCallError, lambda: asyncio.run(router.generate(f"ollama::{GEN}", "x")))
    e2 = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"ollama::{GEN}", msgs)))
recs = lines(dsink)
check("4 an unreachable server raises LockCallError for generate and chat, each with a record (status error)",
      e1 is not None and e2 is not None and [r["status"] for r in recs] == ["error", "error"]
      and all(r["error"].startswith("before the request was posted: URLError") for r in recs)
      and recs[1]["messages_sent_verified"] is None and recs[1]["caller_asked"]["method"] == "chat",
      recs[0]["error"][:90] if recs else "no record")

# 2. no run context
n_bodies = len(Stub.bodies)
e = raises(rc.RunContextError, lambda: asyncio.run(router.generate(f"ollama::{GEN}", "x")))
check("2 refused: a call outside a run context", e is not None and len(Stub.bodies) == n_bodies, str(e)[:90])
stub.shutdown()


# 5. Gemini through a fake HTTP layer
def sse(*chunks):
    return [f"data: {json.dumps(c)}\n".encode() for c in chunks] + [b"\n"]


class FakeResponse(io.BytesIO):
    def __init__(self, ls):
        super().__init__(b"".join(ls))


GTOOL = {"type": "function", "function": {"name": "gene_length", "description": "Length of a human gene in bp.",
         "parameters": {"type": "object", "properties": {"gene": {"type": "string"}}, "required": ["gene"]}}}
PARTS = [{"text": "Checking.", "thoughtSignature": "c2lnLWE="},
         {"functionCall": {"name": "gene_length", "args": {"gene": "TP53"}}, "thoughtSignature": "c2lnLWI="}]
STREAM = sse({"candidates": [{"content": {"role": "model", "parts": PARTS}, "finishReason": "STOP"}],
              "modelVersion": "fake-1",
              "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "thoughtsTokenCount": 7}})
posted = []


def opener(req, timeout=None):
    posted.append(json.loads(req.data))
    return FakeResponse(STREAM)


saved = (gc._open, gc._sleep, gc._arm, gc._key)
gc._open, gc._sleep, gc._arm, gc._key = opener, lambda s: None, lambda r, s: None, lambda: "offline"
gsink = tmp / "gemini-offline"
try:
    with rc.run(ctx_for(sbase, gsink, {GEM: "generator"})):
        gmsgs = [{"role": "system", "content": "Use the tool."}, {"role": "user", "content": "How long is TP53?"}]
        out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL], options=dict(ASK), think="high"))
        rec = lines(gsink)[-1]
        check("5 Gemini request: the lock's generationConfig, the system message as systemInstruction (Q28)",
              posted[-1]["generationConfig"] == gc.generation_config(lock.gemini(GEM, 1))
              and posted[-1]["systemInstruction"] == {"parts": [{"text": "Use the tool."}]}
              and [c["role"] for c in posted[-1]["contents"]] == ["user"],
              json.dumps(posted[-1]["generationConfig"]))
        calls = _extract_tool_calls(out)
        check("5 Gemini functionCall comes back in Ollama's shape and step_executor reads it",
              out["message"]["tool_calls"] == [{"function": {"name": "gene_length", "arguments": {"gene": "TP53"}}}]
              and calls == [{"name": "gene_length", "arguments": {"gene": "TP53"}}]
              and out["message"]["_gemini_parts"] == PARTS and out["message"]["content"] == "Checking.",
              json.dumps(out["message"]["tool_calls"]))
        check("5 Gemini record: caller_asked kept, provider and role, raw parts, counts",
              rec["caller_asked"]["options"] == ASK and rec["provider"] == "gemini" and rec["role"] == "generator"
              and rec["raw_parts"] == PARTS and (out["prompt_eval_count"], out["eval_count"]) == (10, 5)
              and rec["thinking_tokens"] == 7 and rec["messages_sent"] == gmsgs)
        # the next turn as step_executor.py:432-446 builds it
        turn2 = gmsgs + [{"role": "assistant", "content": "Called gene_length", "tool_calls": [calls[0]],
                          "_gemini_parts": out["message"]["_gemini_parts"]},
                         {"role": "tool", "name": "gene_length", "content": "19149"}]
        asyncio.run(router.chat(f"gemini::{GEM}", turn2, tools=[GTOOL]))
        check("5 the echoed _gemini_parts go out unchanged, the tool result as functionResponse",
              posted[-1]["contents"][1] == {"role": "model", "parts": PARTS}
              and posted[-1]["contents"][2]["parts"][0]["functionResponse"]["name"] == "gene_length")

        # 8. D80 V1 on Gemini: the text-form call is not read; a stall is not transient
        tool_stream = STREAM
        STREAM = sse({"candidates": [{"content": {"role": "model", "parts": [{"text": TEXT_CALL}]},
                                      "finishReason": "STOP"}], "modelVersion": "fake-1",
                      "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}})
        with la.text_tool_calls(se.read_text_tool_call):
            out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=STEP_TOOLS_SCHEMA))
        rec = lines(gsink)[-1]
        check("8 a Gemini reply holding the text-form call, inside text_tool_calls: nothing read",
              rec["provider"] == "gemini" and rec["status"] == "ok" and rec["text"] == TEXT_CALL
              and rec["tool_calls"] == [] and out["message"]["tool_calls"] == [] and read_of(rec) is None,
              json.dumps(rec.get("tool_calls_from_text"))[:120])
        STREAM = tool_stream

        class StallingResponse(io.BytesIO):
            """One chunk, then the socket times out as gemini_client's armed stall timer makes it."""
            def __iter__(self):
                yield sse({"candidates": [{"content": {"role": "model", "parts": [{"text": "Checking"}]}}]})[0]
                raise TimeoutError("timed out")
        gc._open = lambda req, timeout=None: (posted.append(json.loads(req.data)), StallingResponse())[1]
        n_gem = len(lines(gsink))
        e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL])))
        check("8 a Gemini stall raises LockCallError with transient None and a text without 'timed out'",
              e is not None and e.record["provider"] == "gemini" and e.record["status"] == "stalled"
              and e.transient is None and "timed out" not in str(e) and len(lines(gsink)) == n_gem + 1,
              str(e)[:100] if e else "no exception")

        # D83 Q145 and D89 (Q145 O3): an empty, blocked or recitation Gemini reply returns to the caller as empty text
        # (done_reason stop, no tool call, no parts to echo); the record keeps the status and Google's reason
        def serve(*chunks):
            gc._open = lambda req, timeout=None: (posted.append(json.loads(req.data)), FakeResponse(sse(*chunks)))[1]
        USAGE = {"promptTokenCount": 10, "totalTokenCount": 10}
        PART = {"content": {"role": "model", "parts": [{"text": "half an answer"}]}}
        cases = [   # D89: returned as empty text
            ("empty reply (STOP)", [{"candidates": [{"content": {"role": "model"}, "finishReason": "STOP"}],
                                     "usageMetadata": USAGE}],
             lambda r: r["status"] == "empty" and r["stop_reason"] == "STOP"),
            ("empty reply (no finishReason, the 19_hpai shape)",
             [{"candidates": [{"content": {"role": "model", "parts": []}}], "usageMetadata": USAGE}],
             lambda r: r["status"] == "empty" and r["stop_reason"] is None and r["error"] is None),
            ("blocked prompt", [{"promptFeedback": {"blockReason": "OTHER"}, "usageMetadata": USAGE}],
             lambda r: r["status"] == "blocked" and r["block_reason"] == "OTHER" and r["block_source"] == "prompt"
             and r["prompt_feedback"] == {"blockReason": "OTHER"}),
            ("blocked answer after streamed text", [{"candidates": [PART]},
                                                    {"candidates": [{"content": {"role": "model", "parts": []},
                                                                     "finishReason": "SAFETY",
                                                                     "finishMessage": "fake stop"}]}],
             lambda r: r["status"] == "blocked" and r["block_reason"] == "SAFETY" and r["block_source"] == "answer"
             and r["finish_message"] == "fake stop" and r["text"] == "half an answer"),
        ]
        for name, chunks, kept in cases:
            serve(*chunks)
            n0 = len(lines(gsink))
            out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL]))
            rec = lines(gsink)[-1]
            check(f"D89 chat, {name}: returned as empty text (done_reason stop, no tool call, no parts), the record "
                  f"written once with status {rec['status']} and Google's reason",
                  out["done_reason"] == "stop" and out["message"]["content"] == "" and out["response"] == ""
                  and out["message"]["tool_calls"] == [] and out["message"]["_gemini_parts"] == []
                  and out["message"]["thinking"] == "" and len(lines(gsink)) == n0 + 1 and kept(rec)
                  and out["lock_record"]["seq"] == rec["seq"], f"{rec['status']} {rec.get('error')}")
            serve(*chunks)
            g = asyncio.run(router.generate(f"gemini::{GEM}", "x"))
            check(f"D89 generate, {name}: response '' with done_reason stop, status kept",
                  g["response"] == "" and g["done_reason"] == "stop" and g["thinking"] == ""
                  and kept(lines(gsink)[-1]), lines(gsink)[-1]["status"])
        # the answer goes on: the next turn sends the blocked turn as Mentori's placeholder for an empty model turn
        serve({"promptFeedback": {"blockReason": "OTHER"}})
        out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL]))
        gc._open = opener                                       # the tool-calling reply of section 5
        nxt = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs + [{**out["message"]},
                                                                   {"role": "user", "content": "Go on."}],
                                      tools=[GTOOL]))
        check("D89 after a blocked reply the conversation goes on: the empty model turn is sent as '[Empty]' "
              "(models/gemini.py:256-257) and the next reply returns",
              posted[-1]["contents"][-2] == {"role": "model", "parts": [{"text": "[Empty]"}]}
              and nxt["done_reason"] == "stop" and nxt["message"]["tool_calls"] != [],
              json.dumps(posted[-1]["contents"][-2]))
        # D90 (Q1, Q2): a recitation stop and a malformed reply return with what the stream held, as an ok reply does
        FCALL = {"functionCall": {"name": GTOOL["function"]["name"], "args": {"q": "x"}}}
        passed = [
            ("recitation after streamed text", [{"candidates": [PART]},
                                                {"candidates": [{"content": {"role": "model", "parts": []},
                                                                 "finishReason": "RECITATION",
                                                                 "finishMessage": "fake recitation"}]}],
             "half an answer", 0, 1,
             lambda r: r["status"] == "recitation" and r["stop_reason"] == "RECITATION"
             and r["finish_message"] == "fake recitation" and r["text"] == "half an answer"),
            ("malformed_function_call with no part", [{"candidates": [{"content": {"role": "model"},
                                                                       "finishReason": "MALFORMED_FUNCTION_CALL",
                                                                       "finishMessage": "fake malformed"}],
                                                       "usageMetadata": USAGE}],
             "", 0, 0,
             lambda r: r["status"] == "malformed_function_call" and r["stop_reason"] == "MALFORMED_FUNCTION_CALL"
             and r["finish_message"] == "fake malformed" and r["text"] == ""),
            ("malformed_response after a text part and a function call", [
                {"candidates": [PART]}, {"candidates": [{"content": {"role": "model", "parts": [FCALL]}}]},
                {"candidates": [{"content": {"role": "model", "parts": []}, "finishReason": "MALFORMED_RESPONSE"}]}],
             "half an answer", 1, 2,
             lambda r: r["status"] == "malformed_response" and r["stop_reason"] == "MALFORMED_RESPONSE"
             and r["text"] == "half an answer" and len(r["tool_calls"]) == 1),
        ]
        for name, chunks, text, n_calls, n_parts, kept in passed:
            serve(*chunks)
            n0 = len(lines(gsink))
            out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL]))
            rec = lines(gsink)[-1]
            tc = out["message"]["tool_calls"]
            check(f"D90 chat, {name}: returned with what the stream held (done_reason stop, text {text!r}, "
                  f"{n_calls} tool call(s), {n_parts} part(s) to echo), the record written once with status "
                  f"{rec['status']} and Google's reason",
                  out["done_reason"] == "stop" and out["message"]["content"] == text and out["response"] == text
                  and len(tc) == n_calls and all(c["function"]["name"] == GTOOL["function"]["name"] for c in tc)
                  and len(out["message"]["_gemini_parts"]) == n_parts and len(lines(gsink)) == n0 + 1 and kept(rec)
                  and out["lock_record"]["seq"] == rec["seq"],
                  f"{rec['status']} {out['message']['content']!r} {len(tc)} {len(out['message']['_gemini_parts'])}")
            serve(*chunks)
            g = asyncio.run(router.generate(f"gemini::{GEM}", "x"))
            check(f"D90 generate, {name}: response {text!r} with done_reason stop, status kept",
                  g["response"] == text and g["done_reason"] == "stop" and kept(lines(gsink)[-1]),
                  f"{lines(gsink)[-1]['status']} {g['response']!r}")
        # the answer goes on after a malformed reply with no part: the empty model turn is sent as "[Empty]"
        serve({"candidates": [{"content": {"role": "model"}, "finishReason": "MALFORMED_FUNCTION_CALL"}]})
        out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL]))
        gc._open = opener
        nxt = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs + [{**out["message"]},
                                                                   {"role": "user", "content": "Go on."}],
                                      tools=[GTOOL]))
        check("D90 after a malformed reply with no part the conversation goes on: the empty model turn is sent as "
              "'[Empty]' (models/gemini.py:256-257) and the next reply returns",
              posted[-1]["contents"][-2] == {"role": "model", "parts": [{"text": "[Empty]"}]}
              and nxt["done_reason"] == "stop" and nxt["message"]["tool_calls"] != [],
              json.dumps(posted[-1]["contents"][-2]))
        # D92 Q188: a reply Google ended for language, other, unexpected_tool_call or too_many_tool_calls returns with
        # what the stream held, as D90's statuses; a reason Q188 does not name (no_image) still raises
        for fr in ("LANGUAGE", "OTHER", "UNEXPECTED_TOOL_CALL", "TOO_MANY_TOOL_CALLS"):
            serve({"candidates": [PART]}, {"candidates": [{"content": {"role": "model", "parts": []},
                                                           "finishReason": fr}]})
            n0 = len(lines(gsink))
            out = asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL]))
            rec = lines(gsink)[-1]
            check(f"D92 Q188 chat, finishReason {fr}: returned with the streamed text (done_reason stop), the record "
                  f"written once with status {fr.lower()}",
                  out["done_reason"] == "stop" and out["message"]["content"] == "half an answer"
                  and rec["status"] == fr.lower() and rec["stop_reason"] == fr and len(lines(gsink)) == n0 + 1,
                  f"{rec['status']} {out['message']['content']!r}")
        serve({"candidates": [{"content": {"role": "model"}, "finishReason": "NO_IMAGE"}]})
        n0 = len(lines(gsink))
        e = raises(la.LockCallError, lambda: asyncio.run(router.chat(f"gemini::{GEM}", gmsgs, tools=[GTOOL])))
        check("D92 a Gemini finishReason Q188 does not name (NO_IMAGE, status no_image) still raises LockCallError, its "
              "record written once", e is not None and e.record["status"] == "no_image" and e.transient is None
              and len(lines(gsink)) == n0 + 1, str(e)[:100] if e else "no exception")
        # D92 Q199: an Anthropic record (anthropic_client writes no session or code fields) gets them in _append; a
        # record that already carries them (Ollama, Gemini) keeps its own
        from experiments.runner import ollama_client as _oc
        prov = _oc.provenance()
        la._append({"model": "claude-haiku-4-5", "status": "ok", "text": "x"}, "anthropic", "generator", {}, None)
        ra = lines(gsink)[-1]
        la._append({"model": GEM, "status": "ok", "session_id": "kept:1:x:y", "code_commit": "c" * 40,
                    "code_dirty": False}, "gemini", "generator", {}, None)
        rk = lines(gsink)[-1]
        check("D92 Q199 an Anthropic record gets session_id, code_commit and code_dirty in _append; a record that "
              "carries its own keeps them",
              all(ra.get(k) == v for k, v in prov.items()) and rk["session_id"] == "kept:1:x:y"
              and rk["code_commit"] == "c" * 40 and rk["code_dirty"] is False, json.dumps(prov))
        # the unreached-server record carries them itself, as an ollama_client record does (not only through _append)
        ru = la._unreached(lock.ollama(GEN, draw=1), "http://127.0.0.1:9/", OSError("refused"))
        check("D92 Q199 an unreached-server record (lock_adapter._unreached) carries session_id, code_commit and "
              "code_dirty before _append, as an ollama_client record does",
              {k: ru.get(k) for k in prov} == prov and ru["status"] == "error", json.dumps({k: ru.get(k) for k in prov}))
        n_ol = len(lines(gsink))
        for st in ("empty", "blocked", "recitation", "malformed_function_call", "malformed_response"):
            e = raises(la.LockCallError, lambda: la._finish({"provider": "ollama", "status": st}))
            check(f"D89, D90 '{st}' returns only for Gemini: an Ollama record with that status still raises",
                  e is not None and len(lines(gsink)) == n_ol)
finally:
    gc._open, gc._sleep, gc._arm, gc._key = saved

# 7. live
if not a.offline:
    lsink = tmp / "live"
    with rc.run(ctx_for(a.base_url, lsink, {GEN: "generator", GEM: "generator"})):
        out = asyncio.run(router.generate(f"ollama::{GEN}", "Reply with one word: ready.",
                                          options={"temperature": 0.1, "num_predict": 100}))
        r = lines(lsink)[-1]
        check(f"7 live ModelRouter.generate on {GEN}", r["status"] == "ok" and out["response"].strip() != ""
              and r["options_sent"] == lock.ollama(GEN, draw=1).options and r["caller_asked"]["options"]["num_predict"]
              == 100, f"{out['response'].strip()[:40]!r}, {r['wall_s']} s, seq {r['seq']}")
        chunks = asyncio.run(collect(router.chat_stream(f"ollama::{GEN}", [
            {"role": "user", "content": "Name one RNA-seq aligner, one word."}], think=False)))
        content, thinking, usage = planner_parse(chunks)
        r = lines(lsink)[-1]
        check(f"7 live ModelRouter.chat_stream on {GEN}", r["status"] == "ok" and content.strip() != ""
              and content == r["text"] and len(usage) == 1 and usage[0]["output"] == r["output_tokens"],
              f"{content.strip()[:40]!r}, {r['wall_s']} s, seq {r['seq']}")
        out = asyncio.run(router.chat(f"gemini::{GEM}", [
            {"role": "system", "content": "Answer gene questions with the gene_length tool; never guess."},
            {"role": "user", "content": "How long is the human TP53 gene? Call the tool."}], tools=[GTOOL],
            options={"temperature": 0.0}))
        r = lines(lsink)[-1]
        calls = _extract_tool_calls(out)
        check(f"7 live ModelRouter.chat with a tool on {GEM}", r["status"] == "ok" and r["provider"] == "gemini"
              and calls and calls[0]["name"] == "gene_length" and out["message"]["_gemini_parts"] == r["raw_parts"],
              f"{json.dumps(calls)}, {r['wall_s']} s, seq {r['seq']}")
    check("7 one record per live call in the sink", [x["seq"] for x in lines(lsink)] == [1, 2, 3], str(lsink))

# D92 Q199: every record this check wrote (Ollama stub, Gemini fake, unreached server, live), in every sink, carries
# this process's session_id and code fields, except the two written above with their own
from experiments.runner import ollama_client as _oc  # noqa: E402
_prov = _oc.provenance()
_all = [r for f in sorted(tmp.rglob("calls.jsonl")) for r in lines(f.parent)]
_bad = [(r.get("provider"), r.get("seq")) for r in _all
        if r.get("session_id") != "kept:1:x:y" and any(r.get(k) != v for k, v in _prov.items())]
check(f"D92 Q199 all {len(_all)} call records written here carry session_id, code_commit and code_dirty",
      len(_all) > 0 and not _bad, repr(_bad[:5]))
print(f"records in {tmp}")
print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
