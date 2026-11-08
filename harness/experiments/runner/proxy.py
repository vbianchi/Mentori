"""An OpenAI-compatible endpoint that sends every call under the lock, for libraries that speak only the
OpenAI API (RAGAS, RAGChecker). Ollama's own /v1 endpoint cannot carry num_ctx, truncate or shift.

    uv run python -m experiments.runner.proxy --upstream http://127.0.0.1:11434 \
        --model devstral-small-2:24b --role scorer --port 18080 --log <file.jsonl>

POST /v1/chat/completions
    The request's model must be the proxy's model. Whatever temperature, max_tokens, seed or top_p the library
    sends is recorded and not used: the lock's values go upstream. n > 1, tools and logprobs are refused (400).
    response_format json_object -> format "json"; json_schema -> its schema.
POST /v1/embeddings
    Inputs go to /api/embed with truncate false. The model must be in the lock's [models]. Token-id inputs are
    refused (the library must send text).
GET /v1/models
GET /api/version, /api/tags; POST /api/show
    Read-only Ollama endpoints, passed through unchanged (RAGAS records the served model's /api/show).

One upstream request at a time (the lock's num_parallel 1). Every call appends one record to --log: the D37
fields, the library's own parameters, the reply. A call that fails upstream (a prompt longer than the context,
a stall) returns an HTTP error with the reason, so the library sees a failure and never a cut answer. An answer
that fills the context comes back with finish_reason "length".

The status of a failure says whose it is (K1 review F2, 17 October). 400: the request is refused, by this proxy (the
checks above) or by the server (chat: any failed call whose error text contains "context", as a prompt longer than
the context gives; embeddings: an HTTP 4xx from /api/embed). 502: any other failed call (chat: a stall, an HTTP
error, a connection refused or reset; embeddings: an HTTP 5xx, a connection refused or reset, a reply that is not
JSON). 503 (embeddings): the server check refused the server itself (its Ollama version or the encoder's digest
differs from the lock). A caller that stops on a transport failure
(S357_ragas.py transport_failure(), any 5xx) therefore stops on 502 and 503, and records a 400 as the metric's error.
"""

from __future__ import annotations

import argparse
import base64
import struct
import select
import socket
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from experiments.runner.lock import LockError, load
from experiments.runner.ollama_client import chat, embed

REFUSED = ("tools", "functions", "logprobs", "top_logprobs")
PASSTHROUGH = ("/api/version", "/api/tags", "/api/show")


def embed_failure_status(error: str | None) -> int:
    """The proxy's status for a failed /api/embed call (ollama_client.embed's record error). 400 only when the server
    answered with an HTTP 4xx (it refused the request, e.g. an input longer than the encoder's context under truncate
    false); anything else is a transport failure, 502: HTTP 5xx, connection refused or reset, a reply that is not JSON
    (K1 review F2, 17 October: every embedding failure used to be 400, so RAGAS --run wrote the row with a null
    answer_relevancy instead of stopping)."""
    return 400 if (error or "").startswith("HTTP 4") else 502


class Proxy:
    def __init__(self, upstream: str, model: str, role: str, log: Path):
        self.upstream, self.model, self.role, self.log = upstream.rstrip("/"), model, role, log
        lock = load()
        if role == "judge" and model != lock.d["judge"]["model"]:
            # D85 review F1: RAGAS and RAGChecker reach the lock through this proxy; only the main judge, which is
            # also the scorer, is served here, so a second judge cannot stand in for the scorer under role "judge"
            raise LockError(f"{model}: this proxy serves only the main judge ({lock.d['judge']['model']}) as judge")
        self.call = lock.ollama(model, role=role)
        self.gate = threading.Lock()
        self.n = 0

    def write(self, rec: dict) -> None:
        with self.log.open("a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def chat(self, body: dict, abort=None) -> tuple[int, dict]:
        asked = {k: v for k, v in body.items() if k not in ("messages",)}
        if body.get("model") not in (self.model, self.call.model):
            return 400, {"error": {"message": f"this proxy serves {self.model} only, not {body.get('model')!r}"}}
        if (body.get("n") or 1) != 1 or any(body.get(k) for k in REFUSED):
            return 400, {"error": {"message": "n > 1, tools and logprobs are not supported under the lock"}}
        fmt = None
        rf = body.get("response_format") or {}
        if rf.get("type") == "json_object":
            fmt = "json"
        elif rf.get("type") == "json_schema":
            fmt = (rf.get("json_schema") or {}).get("schema")
            if not fmt:
                return 400, {"error": {"message": "response_format json_schema without a schema"}}
        msgs = []
        for m in body.get("messages") or []:
            role, content = {"developer": "system"}.get(m.get("role"), m.get("role")), m.get("content")
            if role not in ("system", "user", "assistant"):
                return 400, {"error": {"message": f"message role {m.get('role')!r} is not supported under the lock"}}
            if isinstance(content, list):          # content parts: only a single text part maps without a choice
                if len(content) != 1 or not isinstance(content[0], dict) or content[0].get("type") != "text":
                    return 400, {"error": {"message": "content parts other than one text part are refused"}}
                content = content[0].get("text")
            if not isinstance(content, str):
                return 400, {"error": {"message": f"message content of type {type(content).__name__} is refused"}}
            msgs.append({"role": role, "content": content})
        if not msgs:
            return 400, {"error": {"message": "no messages"}}
        with self.gate:
            self.n += 1
            n = self.n
            if abort is not None and abort():            # the caller left while this call waited its turn (O4)
                self.write({"endpoint": "chat", "seq": n, "status": "client_gone", "library_asked": asked,
                            "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                return 499, {"error": {"message": "the caller went away before the call started"}}
            rec = chat(self.upstream, self.call, msgs, fmt=fmt, abort=abort)
            # messages_sha256 and request_sha256 come from chat(): what was sent, the system prompt included
            rec.update(endpoint="chat", seq=n, library_asked=asked,
                       messages_chars=sum(len(m["content"]) for m in msgs))
            self.write(rec)
        if rec["status"] == "cancelled":
            return 499, {"error": {"message": "the caller went away; the call was closed"}}
        if rec["status"] not in ("ok", "length"):
            return (400 if "context" in (rec["error"] or "") else 502), {"error": {"message": f"{rec['status']}: {rec['error']}"}}
        usage = {"prompt_tokens": rec["prompt_tokens"] or 0, "completion_tokens": rec["output_tokens"] or 0}
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        return 200, {"id": f"chatcmpl-{n}", "object": "chat.completion", "created": int(time.time()),
                     "model": body["model"],
                     "choices": [{"index": 0, "message": {"role": "assistant", "content": rec["text"]},
                                  "finish_reason": "stop" if rec["status"] == "ok" else "length"}],
                     "usage": usage}

    def embeddings(self, body: dict) -> tuple[int, dict]:
        model = body.get("model", "")
        model = model if ":" in model else model + ":latest"
        if model != load().d["scorers"]["embedding"]:
            return 400, {"error": {"message": f"the lock's encoder is {load().d['scorers']['embedding']}, not {model}"}}
        inputs = body.get("input")
        inputs = [inputs] if isinstance(inputs, str) else inputs
        if not inputs or not all(isinstance(x, str) for x in inputs):
            return 400, {"error": {"message": "send text inputs; token ids are refused"}}
        with self.gate:
            try:
                rec = embed(self.upstream, model, inputs)
            except LockError as e:                      # refused by the server check: recorded, never silent
                self.write({"endpoint": "embeddings", "status": "error", "error": f"LockError: {e}", "model": model,
                            "n_inputs": len(inputs), "input_chars": [len(x) for x in inputs],
                            "encoding_format": body.get("encoding_format", "float"),
                            "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                # the server, not the request, is refused: 503, a transport failure for the caller (F2, 17 October;
                # was 400, which RAGAS recorded as a null answer_relevancy on a scored row)
                return 503, {"error": {"message": str(e)}}
            vecs = rec.pop("embeddings")
            rec.update(endpoint="embeddings", input_chars=[len(x) for x in inputs],
                       encoding_format=body.get("encoding_format", "float"))
            self.write(rec)
        if rec["status"] != "ok":
            return embed_failure_status(rec["error"]), {"error": {"message": rec["error"]}}
        tok = rec["prompt_tokens"] or 0
        if body.get("encoding_format") == "base64":       # the OpenAI SDK's default: float32, little-endian
            vecs = [base64.b64encode(struct.pack(f"<{len(v)}f", *v)).decode() for v in vecs]
        return 200, {"object": "list", "model": body.get("model"),
                     "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vecs)],
                     "usage": {"prompt_tokens": tok, "total_tokens": tok}}


def _gone(conn) -> bool:
    """True when the caller has closed its side of the connection (O4: a call nobody waits for is closed)."""
    try:
        readable, _, _ = select.select([conn], [], [], 0)
        return bool(readable) and conn.recv(1, socket.MSG_PEEK) == b""
    except OSError:
        return True


def serve(proxy: Proxy, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _pass(self, data: bytes | None):
            req = urllib.request.Request(proxy.upstream + self.path, data=data,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    code, body = r.status, r.read()
            except urllib.error.HTTPError as e:
                code, body = e.code, e.read()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send(self, code: int, obj: dict, sse: bool = False):
            if sse and code == 200:
                c = obj["choices"][0]
                chunk = {"id": obj["id"], "object": "chat.completion.chunk", "created": obj["created"],
                         "model": obj["model"], "choices": [{"index": 0, "delta": {"role": "assistant",
                         "content": c["message"]["content"]}, "finish_reason": c["finish_reason"]}],
                         "usage": obj["usage"]}
                data = f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode()
                ctype = "text/event-stream"
            else:
                data, ctype = json.dumps(obj).encode(), "application/json"
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.rstrip("/") in PASSTHROUGH:
                return self._pass(None)
            if self.path.rstrip("/") == "/v1/models":
                return self._send(200, {"object": "list", "data": [{"id": proxy.model, "object": "model"}]})
            self._send(404, {"error": {"message": "not found"}})

        def do_POST(self):
            try:
                return self._post()
            except Exception as e:                           # noqa: BLE001 - answered and logged, never dropped
                proxy.write({"endpoint": self.path, "status": "proxy_error", "error": f"{type(e).__name__}: {e}",
                             "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                try:
                    self._send(500, {"error": {"message": f"proxy error: {type(e).__name__}: {e}"}})
                except OSError:                              # the caller is gone too; the error is in the log
                    pass

        def _post(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            path = self.path.rstrip("/")
            if path in PASSTHROUGH:
                return self._pass(raw)
            body = json.loads(raw or b"{}")
            if path == "/v1/chat/completions":
                code, obj = proxy.chat(body, abort=lambda: _gone(self.connection))
                if code == 499:                          # the caller left (O4): its record is written; no one to answer
                    return
                return self._send(code, obj, sse=bool(body.get("stream")))
            if path == "/v1/embeddings":
                return self._send(*proxy.embeddings(body))
            self._send(404, {"error": {"message": "not found"}})

        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="http://127.0.0.1:11434")
    ap.add_argument("--model", default="devstral-small-2:24b")
    ap.add_argument("--role", default="scorer", choices=["scorer", "judge"])
    ap.add_argument("--port", type=int, default=18080)
    ap.add_argument("--log", required=True, type=Path)
    a = ap.parse_args()
    p = Proxy(a.upstream, a.model, a.role, a.log)
    serve(p, a.port)
    print(f"lock proxy: {a.model} as {a.role} -> {a.upstream}, http://127.0.0.1:{a.port}/v1, log {a.log}", flush=True)
    threading.Event().wait()


if __name__ == "__main__":
    main()
