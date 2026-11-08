"""Checks for experiments/runner/ollama_client.py against a live server, which must be named and idle.

    uv run python -m experiments.runner.check_client --stub-only
    uv run python -m experiments.runner.check_client --base http://127.0.0.1:<port> [--n 3]

The server (D92 Q199, audit of 17 October F16 and F51). There is no default server: --base (or its old name
--base-url) must name one on this machine (127.0.0.1 or localhost), unless --stub-only runs the offline part 4 alone
(and part 0b) and contacts no Ollama. Before any live call the check runs experiments/runner/server_users.py survey on
the server with no model of its own and no ledger, and refuses (exit 1, nothing sent) when it finds any user: a model
loaded in /api/ps (this check has loaded none), a process naming the port, an open connection to the port, or
anything it cannot read. Until 18 October it called 127.0.0.1:11434 by default, the laptop's S2 server.
0b. Offline: the guard refuses a stub server holding a loaded model (named as 127.0.0.1 and as localhost) and a base
   on another host, and lets an idle stub pass, sending nothing but GET /api/ps. Then the live path itself, run as a
   child process of this check (environment CHECK_GUARD_CHILD=1, under which the child skips this step): with --base
   naming the busy stub it must exit 1 with a REFUSED line, the stub having received nothing but GET /api/ps; with no
   --base, exit 1 and REFUSED.

1. Reproduce: re-judge the first n calibration answers of S440's laptop lock pass with the new client
   (same prompt; the lock supplies the date-fixed system prompt) and compare the judge text with the stored raw_text.
2. A prompt longer than the context must come back as status "error", never cut.
3. An answer that fills a small output must come back as status "length". The lock gives no small
   output, so this one call alone sets num_predict 16; it checks the recording, not a setting.
4. Offline, before any live call: tools_sent hashes a tools list the same way in any key order and matches a
   hand-written canonical string; a call whose settings differ from the lock's is refused with tools or images.
   A stub server on 127.0.0.1 (a free port) streams tool calls in two chunks and receives the request bytes:
   request_sha256 is the hash of those bytes, messages_sha256 covers the inserted system prompt, tool_calls
   holds both calls in order, and an image is sent whole while the record keeps only its sha256 (generate, and
   chat with images inside messages, in message order). Line-wrapped base64 hashes as the same image; bytes or
   a string that is not base64 raise ValueError before the call; a lone surrogate is sent and hashed, not a
   crash; a best-of-n candidate passes the lock check and its draw, candidate and seed are recorded.
   An embed call sends truncate false and its record holds every LOCK.toml [record] field (F23). Every chat,
   generate and embed record carries session_id, code_commit and code_dirty (D92 Q199, audit F17, F35); a child
   forked after import gets its own session_id; git runs with the repository as cwd and --no-optional-locks.
5. Live: a chat on qwen3-coder:30b (the lock's generator settings, draw 1) with one tool, get_weather(city),
   must come back with status ok and the tool call recorded.
"""

import argparse
import base64
import hashlib
import json
import sys
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from S141_runner.judge import build_prompt  # noqa: E402
from S141_runner.providers import pinned_system  # noqa: E402
from S376_judge_calibration import answers_and_key  # noqa: E402

from experiments.runner.lock import LockError, load  # noqa: E402
from experiments.runner.ollama_client import canonical_sha256, chat, embed, generate, image_sha256, tools_sent  # noqa: E402

REFS = {"laptop": ROOT / "findings/recompute/S440_judge_lock_check_laptop.jsonl",
        "beelink": ROOT / "findings/recompute/S440_judge_lock_check_beelink.jsonl"}
JUDGE = "devstral-small-2:24b"
ENC = "bge-m3:latest"

ap = argparse.ArgumentParser()
ap.add_argument("--base", "--base-url", dest="base_url", default=None,
                help="the live server on this machine (required unless --stub-only; no default, D92 Q199)")
ap.add_argument("--stub-only", action="store_true", help="the offline parts (4 and 0b) only; no Ollama is contacted")
ap.add_argument("--n", type=int, default=3)
ap.add_argument("--reference", choices=sorted(REFS), default="laptop", help="whose S440 lock pass to reproduce")
a = ap.parse_args()

lock = load()
call = lock.ollama(JUDGE, role="judge")
stored = {r["answer_key"]: r for r in map(json.loads, REFS[a.reference].read_text().splitlines()) if r["pass"] == "lock"}
items = [x for x in answers_and_key() if x["answer_key"] in stored][: a.n]
results = [call.system == pinned_system(JUDGE)]
print(('PASS' if results[0] else 'FAIL'), 'the lock sends the system prompt S440 sent')


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


# 4. offline: tools hashing, refusal with content, and what a stub server receives
TOOL = {"type": "function", "function": {"name": "get_weather", "description": "Get the current weather for a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "The city name"}},
                       "required": ["city"]}}}
CANON = ('[{"function":{"description":"Get the current weather for a city.","name":"get_weather","parameters":'
         '{"properties":{"city":{"description":"The city name","type":"string"}},"required":["city"],"type":"object"}},'
         '"type":"function"}]')                                  # written by hand: sorted keys, no spaces
reordered = [{"function": {"parameters": TOOL["function"]["parameters"], "name": "get_weather",
                           "description": TOOL["function"]["description"]}, "type": "function"}]
changed = [{**TOOL, "function": {**TOOL["function"], "description": "Get the weather."}}]
ts = tools_sent([TOOL])
check("tools_sent: names and the sha256 of the hand-written canonical JSON",
      ts == {"names": ["get_weather"], "sha256": hashlib.sha256(CANON.encode()).hexdigest()}, ts["sha256"][:16])
check("tools_sent: the same list in another key order hashes the same, a changed tool does not",
      tools_sent(reordered)["sha256"] == ts["sha256"] and tools_sent(changed)["sha256"] != ts["sha256"])
check("tools_sent(None) is None", tools_sent(None) is None)

GEN = "qwen3-coder:30b"
gcall = lock.ollama(GEN, draw=1)
bent = replace(gcall, options={**gcall.options, "temperature": 0.1})
IMG = base64.b64encode(b"\x89PNG\r\n\x1a\n not a real image").decode()
for name, fn in (("chat with tools", lambda: chat("http://127.0.0.1:9", bent, [{"role": "user", "content": "x"}],
                                                   tools=[TOOL])),
                 ("generate with images", lambda: generate("http://127.0.0.1:9", bent, "x", images=[IMG]))):
    try:
        fn()
        refused = False
    except LockError:
        refused = True
    check(f"a call whose options differ from the lock's is refused ({name})", refused)


class Stub(BaseHTTPRequestHandler):
    """Answers like Ollama 0.40.2 holding the judge, keeps the last request body, streams two tool calls."""
    last = b""

    def do_GET(self):
        body = ({"version": lock.d["server"]["ollama_version"]} if self.path == "/api/version"
                else {"models": [{"name": c.model, "digest": c.digest} for c in (call, gcall)]
                      + [{"name": ENC, "digest": lock.d["models"][ENC]["digest"]}]})
        self._lines([body])

    def do_POST(self):
        Stub.last = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path == "/api/chat":
            self._lines([{"message": {"role": "assistant", "content": "", "tool_calls": [
                             {"function": {"name": "get_weather", "arguments": {"city": "Paris"}}}]}, "done": False},
                         {"message": {"role": "assistant", "content": "a", "tool_calls": [
                             {"function": {"name": "get_weather", "arguments": {"city": "Rome"}}}]}, "done": False},
                         {"message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop",
                          "prompt_eval_count": 1, "eval_count": 2}])
        elif self.path == "/api/embed":
            self._lines([{"model": ENC, "embeddings": [[1.0, 0.0], [0.0, 1.0]], "total_duration": 2_000_000_000,
                          "load_duration": 500_000_000, "prompt_eval_count": 3}])
        else:
            self._lines([{"response": "a", "done": False},
                         {"response": "", "done": True, "done_reason": "stop", "prompt_eval_count": 1, "eval_count": 1}])

    def _lines(self, objs):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for o in objs:
            self.wfile.write((json.dumps(o) + "\n").encode())

    def log_message(self, *a):
        pass


stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
sbase = f"http://127.0.0.1:{stub.server_address[1]}"
user = [{"role": "user", "content": "weather?"}]
rec = chat(sbase, call, user, tools=[TOOL])
sent = json.loads(Stub.last)
check("stub chat: request_sha256 is the sha256 of the bytes the server received",
      rec["request_sha256"] == hashlib.sha256(Stub.last).hexdigest())
check("stub chat: messages_sha256 covers the inserted system prompt (F30)",
      sent["messages"][0] == {"role": "system", "content": call.system}
      and rec["messages_sha256"] == canonical_sha256(sent["messages"]) != canonical_sha256(user))
check("stub chat: the tools list is sent whole and kept out of fields_sent",
      sent["tools"] == [TOOL] and "tools" not in rec["fields_sent"] and rec["tools_sent"] == ts)
check("stub chat: tool calls from two chunks recorded in order, status ok",
      [c["function"]["arguments"]["city"] for c in rec["tool_calls"]] == ["Paris", "Rome"] and rec["status"] == "ok",
      json.dumps(rec["tool_calls"]))
rec = generate(sbase, call, "describe", images=[IMG])
sent = json.loads(Stub.last)
check("stub generate: the image is sent whole, the record keeps only its sha256",
      sent["images"] == [IMG] and rec["images_sha256"] == [hashlib.sha256(base64.b64decode(IMG)).hexdigest()]
      and IMG not in json.dumps(rec) and rec["request_sha256"] == hashlib.sha256(Stub.last).hexdigest())
rec = chat(sbase, call, [{"role": "user", "content": "a", "images": [IMG]}, {"role": "user", "content": "b"},
                         {"role": "user", "content": "c", "images": [IMG]}])
sent = json.loads(Stub.last)
check("stub chat: images inside messages are sent whole, the record keeps their sha256s in message order",
      [m.get("images") for m in sent["messages"][1:]] == [[IMG], None, [IMG]]
      and rec["images_sha256"] == [hashlib.sha256(base64.b64decode(IMG)).hexdigest()] * 2 and IMG not in json.dumps(rec)
      and chat(sbase, call, user)["images_sha256"] is None)
wrapped = "\n".join(IMG[i:i + 8] for i in range(0, len(IMG), 8))
rec = generate(sbase, call, "describe", images=[wrapped])
check("stub generate: line-wrapped base64 is sent as given and hashes as the same image",
      json.loads(Stub.last)["images"] == [wrapped] and rec["images_sha256"] == [image_sha256(IMG)])
for name, bad in (("bytes", IMG.encode()), ("not base64", "not base64!")):
    try:
        generate(sbase, call, "describe", images=[bad])
        refused = False
    except ValueError:
        refused = True
    check(f"an image that is not a base64 str ({name}) raises ValueError before the call", refused)
rec = chat(sbase, call, [{"role": "user", "content": "a\ud800b"}])
check("stub chat: a lone surrogate is sent and hashed, not a crash",
      rec["status"] == "ok" and rec["messages_sha256"] == canonical_sha256(json.loads(Stub.last)["messages"]))
rec = chat(sbase, lock.ollama(GEN, draw=2, candidate=3), user)
check("stub chat: a best-of-n candidate passes the lock check and its number is recorded",
      rec["status"] == "ok" and (rec["draw"], rec["candidate"], rec["options_sent"].get("seed")) == (2, 3, 2003),
      f"draw {rec['draw']}, candidate {rec['candidate']}, seed {rec['options_sent'].get('seed')}")
rec = embed(sbase, ENC, ["STAR aligner", "DESeq2"])
sent = json.loads(Stub.last)
check("stub embed: truncate false sent, and the record holds every LOCK.toml [record] field (F23)",
      sent["truncate"] is False and rec["status"] == "ok" and set(lock.d["record"]["fields"]) <= set(rec)
      and rec["fields_sent"] == {"truncate": False, "keep_alive": lock.d["server"]["keep_alive"]}
      and (rec["load_s"], rec["total_s"], rec["prompt_tokens"]) == (0.5, 2.0, 3) and rec["wall_s"] is not None,
      f"missing {sorted(set(lock.d['record']['fields']) - set(rec))}")
# D92 Q199 (audit F17, F35): every record names its session and its code (ollama_client.provenance, read at import)
import os as _os  # noqa: E402
import re as _re  # noqa: E402
import subprocess as _sp  # noqa: E402
from experiments.runner.ollama_client import provenance as _provenance  # noqa: E402
_p = _provenance()
_recs = [chat(sbase, call, user), generate(sbase, call, "x"), embed(sbase, ENC, ["x"])]
_head = _sp.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check("stub chat, generate and embed: each record carries session_id (host:pid:UTC start:8 hex, this process), "
      "code_commit (the checkout's commit) and code_dirty (a bool), one value per process (D92 Q199)",
      all({k: r.get(k) for k in _p} == _p for r in _recs)
      and _re.fullmatch(r".+:\d+:\d{8}T\d{6}Z:[0-9a-f]{8}", _p["session_id"]) is not None
      and f":{_os.getpid()}:" in _p["session_id"] and _re.fullmatch(r"[0-9a-f]{40}", _p["code_commit"] or "")
      and isinstance(_p["code_dirty"], bool),
      f"{_p} (HEAD now {_head[:12]}; a commit made after this process imported the client differs)")
# a child forked after import gets its own session_id (its pid), keeps the parent's code fields, and the parent's
# session_id is unchanged
from experiments.runner import ollama_client as _oc  # noqa: E402
import warnings as _warnings  # noqa: E402
_r, _w = _os.pipe()
with _warnings.catch_warnings():               # the stub server's thread: the child only writes a pipe and exits
    _warnings.simplefilter("ignore", DeprecationWarning)
    _pid = _os.fork()
if _pid == 0:
    _os.close(_r)
    _os.write(_w, json.dumps(_oc.provenance()).encode())
    _os._exit(0)
_os.close(_w)
with _os.fdopen(_r) as _f:
    _child = json.loads(_f.read())
_os.waitpid(_pid, 0)
check("D92 Q199 a child forked after import records its own session_id (its pid), the parent's code_commit and "
      "code_dirty; the parent's session_id is unchanged",
      _child["session_id"] != _p["session_id"] and f":{_pid}:" in _child["session_id"]
      and {k: _child.get(k) for k in _p if k != "session_id"} == {k: v for k, v in _p.items() if k != "session_id"}
      and _oc.provenance()["session_id"] == _p["session_id"], f"parent {_p['session_id']}, child {_child}")
# git runs with the repository as cwd (no path on its command line: the Beelink clone's path names a port K1's busy
# guard reads from ps) and --no-optional-locks (git status takes no index.lock)
_seen, _saved_run, _saved_code = [], _oc.subprocess.run, _oc._code
try:
    _oc._code = None
    _oc.subprocess.run = lambda args, **kw: (_seen.append((list(args), kw.get("cwd"))),
                                             _saved_run(args, **kw))[1]
    _again = _oc.code_version()
finally:
    _oc.subprocess.run, _oc._code = _saved_run, _saved_code
check("D92 Q199 code_version runs git --no-optional-locks with the repository as cwd, no path on the command line, "
      "and reads the same commit",
      len(_seen) == 2 and all(a[:2] == ["git", "--no-optional-locks"] and "-C" not in a
                              and not any(str(ROOT) in x for x in a) and cwd == _oc._REPO for a, cwd in _seen)
      and _again["code_commit"] == _p["code_commit"], repr(_seen))
stub.shutdown()


def server_guard(base: str) -> str | None:
    """D92 Q199 (audit F16, F51): None if the server at base is idle and on this machine, else why it is refused.
    server_users.survey with no own model and no ledger: any loaded model, process naming the port, open connection
    to the port or unreadable listing is a user. Reads ps, lsof (or ss, and netstat.exe where it exists) and /api/ps."""
    from urllib.parse import urlsplit
    from experiments.runner import server_users as U
    u = urlsplit(base)
    if u.scheme != "http" or u.hostname not in ("127.0.0.1", "localhost") or u.port is None:
        return f"{base} is not http://127.0.0.1:<port> or http://localhost:<port>: the guard sees this machine only"
    out = U.survey(f"http://127.0.0.1:{u.port}", [], None, None, Path(U.NETSTAT).exists())
    return f"{base} has another user: {U.summary(out)}" if out["busy"] else None


# 0b. offline: the guard on stub servers
class Ps(BaseHTTPRequestHandler):
    models: list = []
    seen: list = []

    def do_GET(self):
        Ps.seen.append(("GET", self.path))
        data = json.dumps({"models": Ps.models}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        Ps.seen.append(("POST", self.path))
        self.send_response(404)
        self.end_headers()

    def log_message(self, *a):
        pass


ps_srv = ThreadingHTTPServer(("127.0.0.1", 0), Ps)
threading.Thread(target=ps_srv.serve_forever, daemon=True).start()
pbase = f"http://127.0.0.1:{ps_srv.server_address[1]}"
Ps.models = [{"name": JUDGE, "model": JUDGE, "expires_at": "x"}]
why = server_guard(pbase)
check("0b a server holding a model this check did not load is refused", why is not None and JUDGE in why, str(why)[:160])
why = server_guard(pbase.replace("127.0.0.1", "localhost"))
check("0b ... named as localhost too (the same server)", why is not None and JUDGE in why)
Ps.models = []
why = server_guard(pbase)
check("0b an idle server on this machine passes", why is None, str(why)[:160])
check("0b a server on another host is refused", server_guard("http://10.15.212.253:11451") is not None)
check("0b the guard sent nothing but GET /api/ps", Ps.seen and all(s == ("GET", "/api/ps") for s in Ps.seen), str(Ps.seen))
import os as _gos  # noqa: E402
import subprocess as _gsp  # noqa: E402
if not _gos.environ.get("CHECK_GUARD_CHILD"):          # the live path itself, run as a child (which skips this part)
    Ps.models = [{"name": JUDGE, "model": JUDGE, "expires_at": "x"}]
    for _args, _want, _name in ((["--base", pbase], JUDGE,
                                 "0b the live path refuses a busy server named with --base: exit 1, REFUSED, nothing "
                                 "sent but GET /api/ps"),
                                ([], "REFUSED: name the server",
                                 "0b the live path with no server named: exit 1, REFUSED, nothing sent")):
        Ps.seen.clear()
        try:
            _r = _gsp.run([sys.executable, "-m", "experiments.runner.check_client", *_args], cwd=ROOT,
                          env={**_gos.environ, "CHECK_GUARD_CHILD": "1"}, capture_output=True, text=True, timeout=180)
            _last = (_r.stdout.strip().splitlines() or [""])[-1]
            _ok = _r.returncode == 1 and _last.startswith("REFUSED:") and _want in _last
        except _gsp.TimeoutExpired as e:
            _ok, _last = False, f"timeout: {e}"
        check(_name, _ok and all(s == ("GET", "/api/ps") for s in Ps.seen), f"{_last[:160]} {Ps.seen}")
ps_srv.shutdown()
if a.stub_only:
    print(f"{sum(results)} of {len(results)} checks pass (stub only: parts 4 and 0b)")
    sys.exit(0 if all(results) else 1)
if not a.base_url:
    print("REFUSED: name the server: --base http://127.0.0.1:<port> (no default since D92 Q199; --stub-only contacts none)")
    sys.exit(1)
refused = server_guard(a.base_url)
if refused:
    print(f"REFUSED: {refused}; no live call sent (D92 Q199)")
    sys.exit(1)
for x in items:
    prompt = build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
    rec = generate(a.base_url, call, prompt)
    same = rec["text"] == stored[x["answer_key"]]["raw_text"]
    results.append(same)
    print(("PASS" if same else "FAIL"), "reproduce", x["answer_key"], rec["status"], rec["wall_s"], "s",
          rec["prompt_tokens"], "prompt tokens")

long_prompt = "word " * (call.options["num_ctx"] + 1000)
rec = generate(a.base_url, call, long_prompt)
ok = rec["status"] == "error" and rec["output_tokens"] is None
results.append(ok)
print(("PASS" if ok else "FAIL"), "over-long prompt refused:", rec["status"], (rec["error"] or "")[:160])

short = replace(call, options={**call.options, "num_predict": 16})
rec = generate(a.base_url, short, "Count from 1 to 200, one number per line.", test_override=True)
ok = rec["status"] == "length" and rec["stop_reason"] == "length"
results.append(ok)
print(("PASS" if ok else "FAIL"), "output limit recorded:", rec["status"], rec["output_tokens"], "tokens")

try:
    generate(a.base_url, short, "hi")
    refused = False
except LockError:
    refused = True
results.append(refused)
print(("PASS" if refused else "FAIL"), "a call changed after Lock.ollama is refused without test_override")

# 5. live: one tool call on the lock's generator settings
rec = chat(a.base_url, gcall, [{"role": "user", "content": "What is the weather in Paris right now? Use the tool."}],
           tools=[TOOL])
names = [(c.get("function") or {}).get("name") for c in rec["tool_calls"]]
check(f"live chat with one tool on {GEN}: status ok and the tool call recorded",
      rec["status"] == "ok" and "get_weather" in names and rec["tools_sent"] == ts,
      f"{rec['status']}, think sent {rec['fields_sent'].get('think', 'omitted')}, {json.dumps(rec['tool_calls'])}, "
      f"{rec['wall_s']} s")
print(f"{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
