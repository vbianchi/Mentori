"""Checks for D239 arm A: the authors' RLM (rlms 0.1.3) with gemma3:27b through Ollama (adapter.LockedOllama and
run_rlm_ref.py --generator gemma3:27b). No model call: ollama_client's HTTP layer is a fake Ollama that answers from a
marker in the prompt, and its server reading (version, tags) is the lock's own values; the server named is a TEST-NET
address (192.0.2.1, RFC 5737) that nothing answers.

    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.check_rlm_ref_ollama

 1 settings sent: the posted /api/chat body is lock.ollama(gemma3:27b, draw 1)'s model, options and fields (num_ctx
   131072, num_predict -1, num_batch 1024, the [sampling.models] row, seed 1, truncate and shift false, keep_alive; no
   think, no system), streamed; a string prompt is one user message, a message list goes as given (the package's
   OpenAI client's mapping); a content that is not a string, or a prompt of another type, is a not-sent record.
 2 record fields: every LOCK [record] field, provider ollama, role generator, caller_asked, call_site, prompt_sent,
   messages_sent verified against the runner's messages_sha256, request_sha256 of the bytes posted, b4 (call, turn,
   block, cap, draw, question, retried); a root turn's passages [], a sub-call's None.
 3 retry seed (LOCK retry_seed, D81): an HTTP 500, a stall and a dropped connection are sent again with seed
   1 + 1,000,000 * r, after r s, each retry's record carrying transient_retry, retry and seed_sent, the failed attempt
   b4.retried; after 3 retries the failure stands (a sub-call raises into the code, a root call ends the question);
   an HTTP 400 (a prompt over the context: truncate false) is not retried. transient() equals lock_adapter's on every
   shape it names (the function is read from lock_adapter.py, which this project cannot import).
 4 length stop (D73 Q47, D75 Q48, D78 Q114): a sub-call that stops on length raises SubCallError; a root and a closing
   reply that stop on length go back as their text and are recorded with status length.
 5 an unreadable server (version or tags) is recorded with nothing sent and stops the run (OllamaUnreached, FATAL).
 6 patch 1 routes backend "vllm" with gemma3:27b to LockedOllama only in an Ollama question, and Gemini only in a
   Gemini one.
 7 run script: --generator gemma3:27b needs the ids file and runs cap 10 and draw 1 only (not with --smoke); the ids
   file is refused for Gemini and when it names a question that is unknown, repeated, a refutation or not answerable;
   the dry run is b4_rlm_ref_gemma3__cap10__d239a46, 46 answers (G19, D249 O2); a run without RLM_REF_OLLAMA_URL is
   refused.
 8 with Docker: a question at cap 2 through the package in the sandbox on the fake Ollama: the code's sub-call, an
   HTTP 500 retried, a length-stopped sub-call raised into the code and caught, the answer from the code; the answer
   record's model, generator, counts (retried left out of the calls, kept in the tokens) and backend.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAKE_KEY = "AIzaFAKE-b4-ollama-check-0123456789abcdef"
os.environ["GEMINI_API_KEY"] = FAKE_KEY
os.environ.pop("ANTHROPIC_API_KEY", None)

from experiments.rlm_ref import adapter as ad  # noqa: E402
from experiments.rlm_ref import run_rlm_ref as runner  # noqa: E402
from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import ollama_client as oc  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError, load  # noqa: E402

BASE = "http://192.0.2.1:9"
QUESTIONS_FILE = ROOT / "findings" / "recompute" / "G19_runs" / "g19_questions.json"   # G19 (D249 O2); G15 archived
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:                          # noqa: BLE001
        return f"wrong exception {type(e).__name__}: {e}"
    return None


def lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


# ---------------------------------------------------------------- the fake Ollama

class FakeStream:
    def __init__(self, chunks, stall_after=None):
        self.chunks, self.stall_after = chunks, stall_after

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        for i, c in enumerate(self.chunks):
            if self.stall_after is not None and i == self.stall_after:
                raise socket.timeout("timed out")
            yield (json.dumps(c) + "\n").encode()


def reply(text, done_reason="stop", prompt_tokens=50, output_tokens=7):
    return [{"message": {"role": "assistant", "content": text}, "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True, "done_reason": done_reason,
             "prompt_eval_count": prompt_tokens, "eval_count": output_tokens, "load_duration": 1_000_000,
             "prompt_eval_duration": 2_000_000, "eval_duration": 3_000_000, "total_duration": 6_000_000}]


def http_error(code, msg):
    return urllib.error.HTTPError(BASE + "/api/chat", code, "err", {}, io.BytesIO(json.dumps({"error": msg}).encode()))


class FakeOllama:
    """root(turn, cap, forced) -> text, or (text, done_reason); a sub-call answers by the marker in its last message:
    SUB-OK x, SUB-LENGTH, SUB-500-ONCE, SUB-500-ALWAYS, SUB-STALL-ONCE, SUB-RESET-ONCE, SUB-400."""

    def __init__(self, root=None):
        self.root, self.posted, self.seen, self.lock = root, [], {}, threading.Lock()

    def __call__(self, req, timeout=None):
        body = json.loads(req.data)
        with self.lock:
            self.posted.append({"url": req.full_url, "raw": req.data, "body": body})
        msgs = body["messages"]
        if msgs and msgs[0].get("role") == "system" and len(msgs) > 1 and self.root is not None:
            forced = msgs[-1]["role"] == "assistant"
            turn = cap = None
            for m in reversed(msgs):
                t = m.get("content", "") if m["role"] == "user" else ""
                hit = re.search(r"Turn (\d+)/(\d+)", t)
                if hit:
                    turn, cap = int(hit[1]), int(hit[2])
                    break
            r = self.root(turn, cap, forced)
            text, why = r if isinstance(r, tuple) else (r, "stop")
            return FakeStream(reply(text, why))
        text = msgs[-1]["content"]
        with self.lock:
            n = self.seen[text] = self.seen.get(text, 0) + 1
        if "SUB-500-ALWAYS" in text or ("SUB-500-ONCE" in text and n == 1):
            raise http_error(500, "llama runner process has terminated")
        if "SUB-STALL-ONCE" in text and n == 1:
            return FakeStream(reply("partial"), stall_after=1)
        if "SUB-RESET-ONCE" in text and n == 1:
            raise urllib.error.URLError(ConnectionResetError(54, "Connection reset by peer"))
        if "SUB-400" in text:
            raise http_error(400, "the input length exceeds the context length")
        if "SUB-LENGTH" in text:
            return FakeStream(reply("a cut answer", "length", 131000, 72))
        return FakeStream(reply("ok:" + text.split("SUB-OK", 1)[-1].strip()))


@contextlib.contextmanager
def fake_ollama(root=None, unreachable=False):
    lock = load()
    fake = FakeOllama(root)
    sleeps = []

    def state(base, model):
        if unreachable:
            raise urllib.error.URLError(OSError(65, "No route to host"))
        return lock.d["server"]["ollama_version"], lock._run_tag(model)[1]
    saved = (oc.server_state, oc._arm, urllib.request.urlopen, ad._sleep)
    oc.server_state, oc._arm, urllib.request.urlopen, ad._sleep = state, (lambda r, s: None), fake, sleeps.append
    try:
        yield fake, sleeps
    finally:
        oc.server_state, oc._arm, urllib.request.urlopen, ad._sleep = saved


def context(tmp: Path, name: str, cap: int = 3, qid: str = "01_sarek_FR1", draw: int = 1,
            generator: str = ad.OLLAMA_IDENT):
    rid = ex.run_id("b4check_ollama", f"cap{cap}", name)
    sink = ex.sink(rid, root=tmp)
    ctx = ex.context("b4check_ollama", f"cap{cap}", qid, draw, {"rlm_ref": generator}, base_url=BASE, run=rid,
                     sink=sink, judge=False)
    return ctx, sink


def one_call(s: ad.Session, prompt, root: bool = False):
    """One LockedOllama call as the package makes it (a root turn through LMHandler.completion's flag)."""
    client = ad.LockedOllama(s)
    token = ad._root.set(root)
    try:
        return client.completion(prompt)
    except Exception as e:                          # noqa: BLE001
        return e
    finally:
        ad._root.reset(token)


# ---------------------------------------------------------------- sections 1 to 6 (no Docker)

def unit(tmp: Path) -> None:
    lock = load()
    want = lock.ollama(ad.OLLAMA_MODEL, draw=1)
    fields = lock.d["record"]["fields"]

    # 1, 2: a sub-call with a string prompt, a root turn with messages
    ctx, sink = context(tmp, "u1")
    with rc.run(ctx), fake_ollama() as (fake, sleeps):
        s = ad.Session(ctx, 3, "01_sarek_FR1", sink, ad.OLLAMA_IDENT)
        s.turn, s.block = 1, 1
        out = one_call(s, "SUB-OK hello")
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "q"},
                {"role": "assistant", "content": "a"}, {"role": "user", "content": "Turn 2/3:"}]
        fake.root = lambda t, c, f: "a root reply"
        out_root = one_call(s, msgs, root=True)
    cl = lines(sink / "calls.jsonl")
    p_sub, p_root = fake.posted[0], fake.posted[1]
    b = p_sub["body"]
    check("1 a sub-call returns the reply's text", out == "ok:hello", repr(out))
    check("1 settings sent: the lock's model, options and fields for gemma3:27b draw 1 (seed 1), streamed, no think "
          "or system field", p_sub["url"] == BASE + "/api/chat" and b["model"] == want.model == "gemma3:27b"
          and b["options"] == want.options and b["options"]["seed"] == 1 and b["options"]["num_ctx"] == 131072
          and b["options"]["num_predict"] == -1 and b["stream"] is True and "think" not in b and "system" not in b
          and {k: b[k] for k in ("truncate", "shift", "keep_alive")} == want.fields, json.dumps(b["options"]))
    check("1 the [sampling.models] row of gemma3:27b is what is sent", all(
        b["options"][k] == v for k, v in lock.d["sampling"]["models"]["gemma3:27b"].items() if k != "think"))
    check("1 a string prompt is one user message; a message list goes as given (rlms OpenAI client's mapping)",
          b["messages"] == [{"role": "user", "content": "SUB-OK hello"}] and p_root["body"]["messages"] == msgs)
    sub, root = cl[0], cl[1]
    check("2 every LOCK [record] field is in the record", all(f in sub for f in fields) and all(f in root for f in fields),
          str([f for f in fields if f not in sub]))
    check("2 provider, role, caller_asked, call site, prompt_sent and the verified request",
          sub["provider"] == "ollama" and sub["role"] == "generator" and sub["caller_asked"]["given"] == "string"
          and sub["caller_asked"]["method"] == "chat" and sub["caller_asked"]["model_identifier"] == ad.OLLAMA_IDENT
          and sub["prompt_sent"] == "SUB-OK hello" and sub["messages_sent"] == b["messages"]
          and sub["messages_sent_verified"] is True and root["messages_sent_verified"] is True
          and "prompt_sent" not in root and root["caller_asked"]["given"] == "messages"
          and sub["request_sha256"] == ad.sha256_bytes(p_sub["raw"]) and sub["options_sent"] == want.options
          and sub["model_digest"] == want.digest and sub["lock_sha256"] == lock.sha256 and sub["status"] == "ok"
          and sub["prompt_tokens"] == 50 and sub["output_tokens"] == 7 and sub["eval_s"] == 0.003)
    check("2 b4 and passages: a sub-call's turn and block, passages None; a root turn's passages []",
          sub["b4"] == {"call": "sub", "turn": 1, "block": 1, "batch_id": None, "batch_index": None, "cap": 3,
                        "draw": 1, "question_id": "01_sarek_FR1", "not_sent": False, "retried": False}
          and sub["passages"] is None and root["passages"] == [] and root["b4"]["call"] == "root"
          and root["b4"]["turn"] == 2 and out_root == "a root reply", json.dumps(sub["b4"]))
    check("2 a server on another machine: busy_servers_on_machine None with its reason",
          sub["busy_servers_on_machine"] is None and "not this machine" in (sub["busy_how"] or ""), sub["busy_how"])

    # 1: not sent
    ctx, sink = context(tmp, "u2")
    with rc.run(ctx), fake_ollama() as (fake, _):
        s = ad.Session(ctx, 3, "01_sarek_FR1", sink, ad.OLLAMA_IDENT)
        e1 = one_call(s, [{"role": "user", "content": ["a", "list"]}])
        e2 = one_call(s, 42)
    cl = lines(sink / "calls.jsonl")
    check("1 a content that is not a string, or a prompt that is not a string or message list: a not-sent record "
          "(status error, no request) raised into the code", isinstance(e1, ad.SubCallError)
          and isinstance(e2, ad.SubCallError) and not fake.posted and len(cl) == 2
          and all(c["status"] == "error" and c["b4"]["not_sent"] and c["options_sent"] is None for c in cl)
          and cl[1]["prompt_given"] == 42, repr(e1)[:80])

    # 3: retries
    def retry_case(name, prompt, root=False):
        ctx, sink = context(tmp, name)
        with rc.run(ctx), fake_ollama(root=(lambda t, c, f: "x")) as (fake, sleeps):
            s = ad.Session(ctx, 3, "01_sarek_FR1", sink, ad.OLLAMA_IDENT)
            if root:
                fake.root = None                   # the root request is answered as a sub-call by its marker
                out = one_call(s, [{"role": "system", "content": "s"}, {"role": "user", "content": prompt}], root=True)
            else:
                out = one_call(s, prompt)
        return out, lines(sink / "calls.jsonl"), [p["body"]["options"]["seed"] for p in fake.posted], sleeps

    out, cl, seeds, sleeps = retry_case("r500", "SUB-500-ONCE x")
    check("3 an HTTP 500 is sent again with the retry seed 1000001 after 1 s, and its reply returns",
          isinstance(out, str) and out.startswith("ok:") and seeds == [1, 1000001]
          and sleeps == [1.0] and [c["status"] for c in cl] == ["error", "ok"]
          and [c["b4"]["retried"] for c in cl] == [True, False], f"{out!r} {seeds} {sleeps}")
    check("3 the retry's record: transient_retry (attempt 1 of 3, reason, failed seq), retry 1, seed_sent",
          cl[1]["transient_retry"] == {"attempt": 1, "of": 3, "reason": "HTTP 500", "failed_seq": cl[0]["seq"],
                                       "failed_ctx_uid": cl[0]["ctx_uid"],
                                       "failed_call_site": "rlms lm_handler single (llm_query / rlm_query)"}
          and cl[1]["retry"] == 1 and cl[1]["seed_sent"] == 1000001 and cl[1]["options_sent"]["seed"] == 1000001
          and "transient_retry" not in cl[0], json.dumps(cl[1].get("transient_retry")))
    out, cl, seeds, _ = retry_case("rstall", "SUB-STALL-ONCE x")
    check("3 a stall is retried", isinstance(out, str) and seeds == [1, 1000001] and cl[0]["status"] == "stalled"
          and cl[1]["transient_retry"]["reason"] == "stalled", f"{seeds} {[c['status'] for c in cl]}")
    out, cl, seeds, _ = retry_case("rreset", "SUB-RESET-ONCE x")
    check("3 a dropped connection is retried", isinstance(out, str) and seeds == [1, 1000001]
          and cl[1]["transient_retry"]["reason"] == "dropped connection", f"{seeds} {cl[0].get('error')}")
    out, cl, seeds, sleeps = retry_case("ralways", "SUB-500-ALWAYS x")
    check("3 after 3 retries (seeds 1, 1000001, 2000001, 3000001; waits 1, 2, 3 s) the failure raises into the code",
          isinstance(out, ad.SubCallError) and seeds == [1, 1000001, 2000001, 3000001] and sleeps == [1.0, 2.0, 3.0]
          and [c["b4"]["retried"] for c in cl] == [True, True, True, False] and [c.get("retry") for c in cl] ==
          [None, 1, 2, 3], f"{seeds} {sleeps} {out!r}"[:200])
    out, cl, seeds, _ = retry_case("rroot", "SUB-500-ALWAYS root", root=True)
    check("3 a root call that still fails after 3 retries ends the question (RootCallError, its last record)",
          isinstance(out, ad.RootCallError) and out.record["seq"] == cl[-1]["seq"] and len(cl) == 4, repr(out)[:120])
    out, cl, seeds, sleeps = retry_case("r400", "SUB-400 x")
    check("3 an HTTP 400 (a prompt over the context, truncate false) is not retried and raises into the code",
          isinstance(out, ad.SubCallError) and seeds == [1] and sleeps == [] and len(cl) == 1
          and cl[0]["error"].startswith("HTTP 400"), cl[0].get("error"))

    # 3: transient() equals lock_adapter's
    src = (ROOT / "experiments" / "mentori" / "backend" / "agents" / "lock_adapter.py").read_text()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == "transient") or (
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("_DROPPED", "_CLIENT_TEXT",
                                                                                 "_NO_FINAL_CHUNK", "_CUT_CHUNK")
                                          for t in n.targets))]
    ns = {"re": re, "Optional": __import__("typing").Optional}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "lock_adapter.py", "exec"), ns)
    shapes = [{"provider": "ollama", "status": s, "error": e, "first_token_s": f}
              for s in ("ok", "length", "stalled", "error", "cancelled")
              for e in (None, "", "error parsing tool call: x", "HTTP 500: boom", "HTTP 400: too long",
                        "URLError: <urlopen error [Errno 54] Connection reset by peer>", "RemoteDisconnected: x",
                        "the stream ended without a final chunk", "IncompleteRead: 3 bytes",
                        "model runner has unexpectedly stopped", "TimeoutError: x", "gaierror: y")
              for f in (None, 0.5)] + [{"provider": "gemini", "status": "stalled"}, {"status": "error", "error": "x"}]
    diff = [x for x in shapes if ns["transient"](x) != ad.transient(x)]
    check(f"3 transient() equals lock_adapter.py's on {len(shapes)} record shapes", len(keep) == 5 and not diff,
          f"{len(keep)} definitions read; differ on {diff[:2]}")

    # 4: length
    ctx, sink = context(tmp, "len")
    with rc.run(ctx), fake_ollama() as (fake, _):
        s = ad.Session(ctx, 3, "01_sarek_FR1", sink, ad.OLLAMA_IDENT)
        e = one_call(s, "SUB-LENGTH x")
        fake.root = lambda t, c, f: ("half a root reply", "length")
        r1 = one_call(s, [{"role": "system", "content": "s"}, {"role": "user", "content": "Turn 1/3:"}], root=True)
        s.forced = True
        r2 = one_call(s, [{"role": "system", "content": "s"}, {"role": "user", "content": "Turn 3/3:"},
                          {"role": "assistant", "content": "Please provide a final answer"}], root=True)
    cl = lines(sink / "calls.jsonl")
    check("4 a sub-call stopped on length raises SubCallError into the code (Q47), recorded status length",
          isinstance(e, ad.SubCallError) and "context limit" in str(e) and cl[0]["status"] == "length"
          and cl[0]["stop_reason"] == "length" and len(fake.posted) == 3, str(e)[:120])
    check("4 a root and a closing reply stopped on length go back as their text, status length (Q48, Q114)",
          r1 == "half a root reply" and r2 == "half a root reply" and [c["status"] for c in cl[1:]] == ["length"] * 2
          and [c["b4"]["call"] for c in cl[1:]] == ["root", "forced_final"] and cl[2]["b4"]["turn"] == 4)

    # 5: unreachable
    ctx, sink = context(tmp, "unr")
    with rc.run(ctx), fake_ollama(unreachable=True) as (fake, _):
        s = ad.Session(ctx, 3, "01_sarek_FR1", sink, ad.OLLAMA_IDENT)
        e = one_call(s, "SUB-OK x")
    cl = lines(sink / "calls.jsonl")
    check("5 an unreadable server: recorded with nothing sent, OllamaUnreached kept as the session's fatal error",
          isinstance(e, ad.OllamaUnreached) and s.fatal is e and not fake.posted and len(cl) == 1
          and cl[0]["status"] == "error" and cl[0]["options_sent"] is None
          and cl[0]["error"].startswith("before the request was posted"), repr(e)[:120])

    # 6: patch 1's routing
    from rlm.core import rlm as rlm_core
    for gen, ok_backend, bad_backend in ((ad.OLLAMA_IDENT, ("vllm", {"model_name": "gemma3:27b"}),
                                          ("gemini", {"model_name": ad.MODEL})),
                                         (ad.IDENT, ("gemini", {"model_name": ad.MODEL}),
                                          ("vllm", {"model_name": "gemma3:27b"}))):
        ctx, sink = context(tmp, f"route{len(results)}", generator=gen)
        with rc.run(ctx):
            ad._session = ad.Session(ctx, 3, "01_sarek_FR1", sink, gen)
            try:
                got = rlm_core.get_client(*ok_backend)
                e = raises(LockError, lambda: rlm_core.get_client(*bad_backend))
                e2 = raises(LockError, lambda: rlm_core.get_client(ok_backend[0], {**ok_backend[1], "base_url": "x"}))
            finally:
                ad._session = None
        want_cls = ad.LockedOllama if gen == ad.OLLAMA_IDENT else ad.LockedGemini
        check(f"6 patch 1 in a {gen} question: {ok_backend[0]} gives {want_cls.__name__}, the other backend and any "
              f"other kwargs are refused", type(got) is want_cls and isinstance(e, LockError)
              and isinstance(e2, LockError))


# ---------------------------------------------------------------- section 7: the run script

def script(tmp: Path) -> None:
    q = ["--question-ids-file", str(QUESTIONS_FILE)]
    g = ["--generator", "gemma3:27b"]
    e = raises(SystemExit, lambda: runner.main([*g, "--cap", "10", "--draw", "1", "--dry-run"]))
    check("7 gemma3:27b needs --question-ids-file", isinstance(e, SystemExit) and "ids-file" in str(e), str(e)[:80])
    for cap, draw in (("5", "1"), ("20", "1"), ("10", "2"), ("10", "3")):
        e = raises(SystemExit, lambda: runner.main([*g, *q, "--cap", cap, "--draw", draw, "--dry-run"]))
        check(f"7 D239 arm A refuses cap {cap} draw {draw}", isinstance(e, SystemExit) and "D239" in str(e))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e = raises(SystemExit, lambda: runner.main([*g, *q, "--smoke", "--cap", "1", "--draw", "1", "--limit", "1",
                                                    "--dry-run", "--runs-root", str(tmp)]))
    check("7 a smoke runs any cap, its own run", e is None and buf.getvalue().startswith(
        "b4_rlm_ref_gemma3__cap1__smoke: 1 answers"), buf.getvalue()[:80])
    e = raises(SystemExit, lambda: runner.main([*q, "--cap", "10", "--draw", "1", "--dry-run"]))
    check("7 the ids file is refused for the Gemini runs", isinstance(e, SystemExit) and "D239" in str(e))
    e = raises(SystemExit, lambda: runner.main([*g, *q, "--question-set", "depth_sweep86", "--cap", "10", "--draw", "1",
                                                "--dry-run"]))
    check("7 the ids file and a named set are refused together", isinstance(e, SystemExit))
    good = json.loads(QUESTIONS_FILE.read_text())
    for what, ids in (("an unknown id", ["NOPE_1"]), ("a repeated id", ["01_sarek_CO2", "01_sarek_CO2"]),
                      ("a refutation question", [next(x["id"] for x in ex.questions() if x["answer_type"] == "refutation")]),
                      ("a not-answerable question", [next(x["id"] for x in ex.questions() if not x["answerable"])]),
                      ("no name", None)):
        p = tmp / f"ids_{len(results)}.json"
        p.write_text(json.dumps({"name": "x1", "ids": ids} if ids else {"ids": good["ids"]}))
        e = raises(SystemExit, lambda p=p: runner.main([*g, "--question-ids-file", str(p), "--cap", "10", "--draw",
                                                        "1", "--dry-run"]))
        check(f"7 an ids file with {what} is refused", isinstance(e, SystemExit), str(e)[:90])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runner.main([*g, *q, "--cap", "10", "--draw", "1", "--dry-run", "--runs-root", str(tmp)])
    out = buf.getvalue().splitlines()
    keys = [x.split()[-1] for x in out if x.startswith("  todo")]
    check("7 the dry run: b4_rlm_ref_gemma3__cap10__d239a46, the file's 46 keys cap10|<id>|d1, the lock's options",
          out[0].startswith("b4_rlm_ref_gemma3__cap10__d239a46: 46 answers at cap 10, draw 1, generator "
                            "ollama::gemma3:27b") and keys == [f"cap10|{i}|d1" for i in good["ids"]]
          and "'seed': 1}" in out[-1] and "1000001, 2000001, 3000001" in out[-1], out[0])
    saved = os.environ.pop(runner.OLLAMA_URL_ENV, None)
    try:
        e = raises(SystemExit, lambda: runner.main([*g, *q, "--cap", "10", "--draw", "1", "--runs-root", str(tmp)]))
    finally:
        if saved is not None:
            os.environ[runner.OLLAMA_URL_ENV] = saved
    check("7 a run with no RLM_REF_OLLAMA_URL is refused before anything starts", isinstance(e, SystemExit)
          and runner.OLLAMA_URL_ENV in str(e) and not (tmp / "b4_rlm_ref_gemma3__cap10__d239a46").exists(), str(e)[:80])
    import importlib.util
    spec = importlib.util.spec_from_file_location("g19_check", ROOT / "findings/recompute/G19_runs/g19_check.py")
    g19 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g19)
    check("7 g19_check's categories are run_rlm_ref's", tuple(g19.CATEGORIES) == tuple(runner.CATEGORIES))
    check("7 g19_check's arm A run id and keys are run_rlm_ref's",
          g19.run_id("A") == ex.run_id(runner.OLLAMA_EXPERIMENT, "cap10", "d239a46")
          and g19.answer_key("A", "01_sarek_CO2") == ex.answer_key("cap10", "01_sarek_CO2", 1))


# ---------------------------------------------------------------- section 8: through the package, with Docker

def end_to_end(tmp: Path) -> None:
    image = ad.ensure_image()
    image["network"] = ad.ensure_network(image["image_id"])
    bundle = ad.load_context()
    ad.add_sandbox_forms(bundle, image)

    def root(turn, cap, forced):
        if turn == 1:
            return ("Looking.\n```repl\nr = llm_query('SUB-500-ONCE hi')\nprint('GOT', r)\ntry:\n"
                    "    llm_query('SUB-LENGTH long')\nexcept Exception as e:\n    print('CAUGHT', type(e).__name__)\n```")
        return "Done.\n```repl\nanswer['content'] = 'gemma answer'\nanswer['ready'] = True\n```"
    ctx, sink = context(tmp, "e2e", cap=2)
    with fake_ollama(root) as (fake, sleeps), rc.run(ctx):
        try:
            rec = ad.run_question(ctx, {"id": "01_sarek_FR1", "question": "Which workflow manager does Sarek use?"},
                                  2, bundle, image, "check", "cap2", ex.answer_key("cap2", "01_sarek_FR1", 1),
                                  generator=ad.OLLAMA_IDENT)
        except Exception as e:                      # noqa: BLE001
            rec = e
    ok = isinstance(rec, dict)
    cl = lines(sink / "calls.jsonl")
    trace = json.loads((sink / rec["trace"]["path"]).read_text()) if ok else {}
    out1 = trace["iterations"][0]["code_blocks"][0]["stdout"] if ok else ""
    check("8 through the package in the sandbox: the code's answer", ok and rec["stop_reason"] == "answer_ready"
          and rec["answer"] == "gemma answer" and rec["status"] == "ok", repr(rec)[:300])
    check("8 the code saw the retried sub-call's reply and caught the length stop as LLMQueryError",
          "GOT ok:SUB-500-ONCE hi" in str(out1) and "CAUGHT LLMQueryError" in str(out1), str(out1)[:200])
    check("8 every call went to /api/chat with the lock's options (seed 1, the retry 1000001)",
          sorted(p["body"]["options"]["seed"] for p in fake.posted) == [1, 1, 1, 1, 1000001]
          and all(p["url"] == BASE + "/api/chat" for p in fake.posted)
          and all(c["options_sent"]["num_ctx"] == 131072 for c in cl), str([p["body"]["options"]["seed"]
                                                                            for p in fake.posted]))
    check("8 the answer record: model, generator, server, backend; retried attempts out of the calls, in the tokens",
          ok and rec["model"] == "gemma3:27b" and rec["generator"] == ad.OLLAMA_IDENT and rec["server"] == BASE
          and rec["package"]["rlm_kwargs"]["backend"] == "vllm (LockedOllama)" and rec["calls"]["root"] == 2
          and rec["calls"]["sub"] == 2 and rec["calls"]["retried"] == 1 and rec["calls"]["sub_failed"] == 1
          and rec["calls"]["sub_length"] == 1 and rec["turns_used"] == 2 and rec["tokens"]["total"]["calls"] == 5
          and rec["calls"]["seqs"] == sorted(c["seq"] for c in cl), json.dumps(rec.get("calls") if ok else None))
    check("8 the root turns' messages are the package's (system first, Turn 1/2 and 2/2), sent as given",
          [c["b4"]["call"] for c in cl if c["b4"]["call"] == "root"] == ["root", "root"]
          and all(c["messages_sent"][0]["role"] == "system" for c in cl if c["b4"]["call"] == "root")
          and sleeps == [1.0])
    # g19_check verify of arm A on this sink (its cap 2 for G19's 10), then on a copy with one record's seed changed
    import importlib.util
    spec = importlib.util.spec_from_file_location("g19_check", ROOT / "findings/recompute/G19_runs/g19_check.py")
    g19 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g19)
    g19.CAP_A = 2
    g19.read_ids = lambda p: {"ids": json.loads(Path(p).read_text())["ids"], "one_paper": [], "many_paper": [],
                              "t2_d98": [], "t2x": [], "sha256": g19.sha256_file(p)}
    qf = tmp / "g19_q.json"
    qf.write_text(json.dumps({"ids": ["01_sarek_FR1"]}))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        v_ok = g19.verify_a(qf, sink)
    bad = tmp / "bad_sink"
    shutil.copytree(sink, bad)
    rows = lines(bad / "calls.jsonl")
    rows[0]["options_sent"] = {**rows[0]["options_sent"], "seed": 7}
    (bad / "calls.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        v_bad = g19.verify_a(qf, bad)
        v_missing = g19.verify_a(QUESTIONS_FILE, sink)
    check("8 g19_check verify (arm A) passes this sink, and fails a changed seed and the 45 answers it does not hold",
          v_ok == 0 and v_bad == 1 and v_missing == 1 and "not the lock's" in buf2.getvalue(),
          buf.getvalue().strip().splitlines()[-1] if buf.getvalue() else "")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_rlm_ref_ollama_", dir=ROOT / "experiments" / "rlm_ref")).resolve()
    try:
        unit(tmp)
        script(tmp)
        if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
            check("8 Docker is running (colima start); section 8 not run", False)
        else:
            end_to_end(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = sum(results)
    print(f"\n{n_ok}/{len(results)} checks passed")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
