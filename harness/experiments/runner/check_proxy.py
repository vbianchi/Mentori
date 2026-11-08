"""Checks for experiments/runner/proxy.py against a live Ollama, which must be named and idle.

    uv run python -m experiments.runner.check_proxy --stub-only
    uv run python -m experiments.runner.check_proxy --base http://127.0.0.1:<port> [--n 2]

The server (D92 Q199, audit of 17 October F16 and F51). The live part has no default server: --base (or its old name
--upstream) must name one, on this machine (127.0.0.1 or localhost). Before any request reaches it, the live part
runs experiments/runner/server_users.py survey on it with no model of its own and no ledger, and refuses (exit 1,
nothing sent) when the survey finds any user: a model loaded in /api/ps (this check has loaded none, so any loaded
model is another job's or left by one), a process naming the port, an open connection to the port, or anything it
cannot read. Until 18 October the live part went to 127.0.0.1:11434 by default, the laptop's S2 server, and twice on
17 October its prompts made S2's calls wait up to 21 s (RUNNING.md, S2). Part 0b checks the refusal on stub servers.

0. Offline, first, against a stub server on 127.0.0.1 (a free port) that answers as another Ollama version: an
   embeddings request refused by ollama_client.embed's server check (LockError) comes back as HTTP 503 (400 before
   the K1 review's F2 of 17 October: the server is refused, not the request, so a caller stops on it) and leaves
   exactly one record (status error, the LockError's reason, endpoint embeddings); nothing reaches /api/embed.
   experiments/scorers/check_k1.py checks the other embedding failures (HTTP 5xx and a dropped connection 502, an
   HTTP 4xx 400) end to end through RAGAS --run.
   --stub-only runs this part (and 0b) alone and contacts no Ollama.
0b. Offline: the server guard refuses a stub server holding a loaded model, and a base on another host, before any
   request but /api/ps; it lets an idle stub pass. Then the live path itself, run as a child process of this check
   (environment CHECK_GUARD_CHILD=1, under which the child skips this step): with --base naming the busy stub it must
   exit 1 with a REFUSED line, the stub having received nothing but GET /api/ps; with no --base, exit 1 and REFUSED.
1. Reproduce: the judge prompts of S440's laptop lock pass, sent as an OpenAI chat request with the library's
   own temperature 0.9, max_tokens 5 and seed 7, come back with S440's judge text byte for byte: the library's
   values are recorded and not used.
2. A prompt longer than the context returns an HTTP error, never a cut answer.
3. n = 2 is refused.
4. Embeddings through bge-m3 return 1,024 numbers per input.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from S141_runner.judge import build_prompt  # noqa: E402
from S376_judge_calibration import answers_and_key  # noqa: E402

from experiments.runner.proxy import Proxy, serve  # noqa: E402

REFS = {"laptop": ROOT / "findings/recompute/S440_judge_lock_check_laptop.jsonl",
        "beelink": ROOT / "findings/recompute/S440_judge_lock_check_beelink.jsonl"}
JUDGE = "devstral-small-2:24b"
PORT = 18089

ap = argparse.ArgumentParser()
ap.add_argument("--base", "--upstream", dest="upstream", default=None,
                help="the live part's Ollama server on this machine (required unless --stub-only; no default, D92 Q199)")
ap.add_argument("--n", type=int, default=2)
ap.add_argument("--reference", choices=sorted(REFS), default="laptop", help="whose S440 lock pass to reproduce")
ap.add_argument("--stub-only", action="store_true", help="run part 0 (the stub server) only; no Ollama is contacted")
a = ap.parse_args()
results = []


def post(path, body, port=PORT):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def stub_part():
    """Part 0: a LockError on embeddings is answered 503 and recorded once (offline)."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    posted = []

    class Stub(BaseHTTPRequestHandler):
        def do_GET(self):
            body = {"version": "0.12.0"} if self.path == "/api/version" else {"models": []}
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            posted.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *x):
            pass

    stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    slog = Path(tempfile.mkdtemp()) / "proxy_stub.jsonl"
    shttpd = serve(Proxy(f"http://127.0.0.1:{stub.server_address[1]}", JUDGE, "scorer", slog), 0)
    code, obj = post("/v1/embeddings", {"model": "bge-m3", "input": ["STAR aligner", "DESeq2"]},
                     port=shttpd.server_address[1])
    recs = [json.loads(x) for x in slog.read_text().splitlines()] if slog.exists() else []
    rec = recs[0] if recs else {}
    check("0 a LockError on embeddings returns 503 with the reason", code == 503 and "0.12.0" in obj["error"]["message"],
          f"HTTP {code}: {obj['error']['message'][:120]}")
    check("0 ... and leaves exactly one record: status error, the LockError's reason, endpoint embeddings",
          len(recs) == 1 and rec.get("status") == "error" and rec.get("endpoint") == "embeddings"
          and str(rec.get("error")).startswith("LockError: ") and "0.12.0" in rec["error"]
          and rec.get("model") == "bge-m3:latest" and rec.get("n_inputs") == 2, json.dumps(rec)[:240])
    check("0 nothing reached /api/embed", posted == [], str(posted))
    shttpd.shutdown()
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


def guard_part():
    """Part 0b: the guard refuses a stub holding a model and a base on another host; an idle stub passes."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    seen = []

    class Ps(BaseHTTPRequestHandler):
        models: list = []

        def do_GET(self):
            seen.append(("GET", self.path))
            data = json.dumps({"models": Ps.models}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            seen.append(("POST", self.path))
            self.send_response(404)
            self.end_headers()

        def log_message(self, *x):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Ps)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    Ps.models = [{"name": "qwen3-coder:30b", "model": "qwen3-coder:30b", "expires_at": "x"}]
    why = server_guard(base)
    check("0b a server holding a model this check did not load is refused", why is not None and "qwen3-coder:30b" in why,
          str(why)[:160])
    why_lh = server_guard(base.replace("127.0.0.1", "localhost"))
    check("0b ... named as localhost too (the same server)", why_lh is not None and "qwen3-coder:30b" in why_lh)
    Ps.models = []
    why = server_guard(base)
    check("0b an idle server on this machine passes", why is None, str(why)[:160])
    check("0b a server on another host is refused", server_guard("http://10.15.212.253:11451") is not None)
    check("0b the guard sent nothing but GET /api/ps", seen and all(s == ("GET", "/api/ps") for s in seen), str(seen))
    if not os.environ.get("CHECK_GUARD_CHILD"):      # the live path itself, run as a child (which skips this part)
        Ps.models = [{"name": "qwen3-coder:30b", "model": "qwen3-coder:30b", "expires_at": "x"}]
        for args, want, name in ((["--base", base], "qwen3-coder:30b",
                                  "0b the live path refuses a busy server named with --base: exit 1, REFUSED, nothing "
                                  "sent but GET /api/ps"),
                                 ([], "REFUSED: name the server",
                                  "0b the live path with no server named: exit 1, REFUSED, nothing sent")):
            seen.clear()
            try:
                r = subprocess.run([sys.executable, "-m", "experiments.runner.check_proxy", *args], cwd=ROOT,
                                   env={**os.environ, "CHECK_GUARD_CHILD": "1"}, capture_output=True, text=True,
                                   timeout=120)
                last = (r.stdout.strip().splitlines() or [""])[-1]
                ok = r.returncode == 1 and last.startswith("REFUSED:") and want in last
            except subprocess.TimeoutExpired as e:
                ok, last = False, f"timeout: {e}"
            check(name, ok and all(s == ("GET", "/api/ps") for s in seen), f"{last[:160]} {seen}")
    srv.shutdown()


stub_part()
guard_part()
if a.stub_only:
    print(f"{sum(results)} of {len(results)} checks pass (stub only)")
    sys.exit(0 if all(results) else 1)
if not a.upstream:
    print("REFUSED: name the server: --base http://127.0.0.1:<port> (no default since D92 Q199; --stub-only contacts none)")
    sys.exit(1)
refused = server_guard(a.upstream)
if refused:
    print(f"REFUSED: {refused}; nothing sent (D92 Q199)")
    sys.exit(1)
log = Path(tempfile.mkdtemp()) / "proxy_check.jsonl"
proxy = Proxy(a.upstream, JUDGE, "scorer", log)
httpd = serve(proxy, PORT)


stored = {r["answer_key"]: r for r in map(json.loads, REFS[a.reference].read_text().splitlines()) if r["pass"] == "lock"}
items = [x for x in answers_and_key() if x["answer_key"] in stored][: a.n]
for x in items:
    prompt = build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
    code, obj = post("/v1/chat/completions", {"model": JUDGE, "messages": [{"role": "user", "content": prompt}],
                                              "temperature": 0.9, "max_tokens": 5, "seed": 7})
    text = obj["choices"][0]["message"]["content"] if code == 200 else None
    check(f"reproduce {x['answer_key']}", text == stored[x["answer_key"]]["raw_text"], f"HTTP {code}")
rec = json.loads(log.read_text().splitlines()[-1])
check("the library's temperature, max_tokens and seed were recorded, not sent",
      rec["library_asked"]["temperature"] == 0.9 and rec["options_sent"].get("temperature") == 0
      and rec["options_sent"]["num_predict"] == 16384 and "seed" not in rec["options_sent"], json.dumps(rec["options_sent"]))
check("the date-fixed system prompt was added", rec["system_sent"] is not None)

code, obj = post("/v1/chat/completions", {"model": JUDGE, "messages": [{"role": "user", "content": "word " * 132000}]})
check("an over-long prompt returns an error", code >= 400 and "context" in obj["error"]["message"], f"HTTP {code}")
code, obj = post("/v1/chat/completions", {"model": JUDGE, "n": 2, "messages": [{"role": "user", "content": "hi"}]})
check("n = 2 is refused", code == 400)
code, obj = post("/v1/embeddings", {"model": "bge-m3", "input": ["RNA-seq alignment with STAR", "survival analysis"]})
check("embeddings: two vectors of 1,024", code == 200 and [len(d["embedding"]) for d in obj["data"]] == [1024, 1024], f"HTTP {code}")
code, obj = post("/v1/embeddings", {"model": "bge-m3", "input": [[101, 102]]})
check("token-id inputs refused", code == 400)

with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/version", timeout=30) as r:
    check("/api/version passes through", json.loads(r.read()).get("version") == "0.40.2")
code, obj = post("/api/show", {"model": JUDGE})
check("/api/show passes through", code == 200 and "details" in obj)

code, obj = post("/v1/chat/completions", {"model": JUDGE, "messages": [{"role": "user", "content": [
    {"type": "text", "text": "a"}, {"type": "image_url", "image_url": {"url": "x"}}]}]})
check("content parts other than one text part are refused", code == 400)
code, obj = post("/v1/chat/completions", {"model": JUDGE, "messages": [{"role": "tool", "content": "x"}]})
check("a tool message is refused", code == 400)
code, obj = post("/v1/chat/completions", {"model": JUDGE, "response_format": {"type": "json_schema", "json_schema": {}},
                                          "messages": [{"role": "user", "content": "x"}]})
check("json_schema without a schema is refused", code == 400)
code, obj = post("/v1/chat/completions", {"model": JUDGE})
check("a request without messages is refused, not dropped", code == 400)
import base64, struct  # noqa: E402
code, obj = post("/v1/embeddings", {"model": "bge-m3", "input": ["STAR aligner"], "encoding_format": "base64"})
vec = struct.unpack("<1024f", base64.b64decode(obj["data"][0]["embedding"])) if code == 200 else ()
check("base64 embeddings decode to 1,024 floats", len(vec) == 1024)
code, obj = post("/v1/embeddings", {"model": "nomic-embed-text", "input": ["x"]})
check("an encoder other than the lock's is refused", code == 400)

# O4: a caller that hangs up mid-answer: the proxy closes the call and records it as cancelled
import socket as _s  # noqa: E402
import time as _t  # noqa: E402
body = json.dumps({"model": JUDGE, "messages": [{"role": "user", "content": "Write the numbers from one to three thousand in English words, one per line, with no gaps, no summary and no code."}]}).encode()
c = _s.create_connection(("127.0.0.1", PORT))
c.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: "
          + str(len(body)).encode() + b"\r\n\r\n" + body)
_t.sleep(3)
c.close()
_t.sleep(5)
last = json.loads(log.read_text().splitlines()[-1])
check("a call whose caller hung up is closed and recorded as cancelled", last.get("status") == "cancelled",
      f"{last.get('status')} after {last.get('output_tokens') or len(last.get('text', ''))}")

httpd.shutdown()
print(f"{sum(results)} of {len(results)} checks pass; log {log}")
sys.exit(0 if all(results) else 1)
