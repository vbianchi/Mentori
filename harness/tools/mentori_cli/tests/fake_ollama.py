"""A fake Ollama HTTP server for the opt-in integration test: no model behind it, a canned reply to every request.

It answers /api/version, /api/tags (the models given, with their digests), and /api/generate and /api/chat with one
streamed chunk and a final chunk, as Ollama streams. Every request body is kept in .requests.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPLY = "The fake server's answer [01_paper.pdf:1]."


class FakeOllama:
    def __init__(self, version: str, tags: dict[str, str], reply: str = REPLY):
        self.version, self.tags, self.reply, self.requests = version, dict(tags), reply, []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, obj):
                body = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/api/version":
                    return self._json({"version": outer.version})
                if self.path == "/api/tags":
                    return self._json({"models": [{"name": k, "digest": v} for k, v in outer.tags.items()]})
                self.send_error(404)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append({"path": self.path, "body": body})
                chat = self.path == "/api/chat"
                part = {"message": {"role": "assistant", "content": outer.reply}} if chat else {"response": outer.reply}
                last = {**({"message": {"role": "assistant", "content": ""}} if chat else {"response": ""}),
                        "done": True, "done_reason": "stop", "prompt_eval_count": 100, "eval_count": 12,
                        "load_duration": 1, "prompt_eval_duration": 1, "eval_duration": 1, "total_duration": 3}
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                for chunk in ({**part, "done": False}, last):
                    self.wfile.write((json.dumps(chunk) + "\n").encode())
                    self.wfile.flush()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
