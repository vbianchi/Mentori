"""Checks for experiments/runner/verifier_ports.py (Q152, D83), offline: no model call, no real Ollama server.

    uv run python -m experiments.runner.check_verifier_ports

1. choose: draw-1 answers only, a key's last line, verification status ok, its verifier call by (ctx_uid, call_seq),
   sorted by question id, positions floor(i * n / 20); fewer than 20 refused. select: no prompt stored, G1's sums,
   and with --copy-of the Studio path as sink and the copy as read_from (review F4).
2. replay_calls: a stored prompt rebuilds to the stored request_sha256 under the lock; an edited prompt or a missing
   call is refused.
3. run_arm against two stub Ollama servers on free ports, through the real ollama_client.generate: arm one sends all
   20 to one port in order, arm two shares them over both ports, every position once per arm, the stub receives the
   exact bytes G1 sent, port and busy_servers_on_machine recorded on every line, the fresh-load records written, the
   after-first-call check run on each port of arm two, the guard called before each fresh load and each call. How busy
   is passed: with busy None generate gets no busy argument, with a busy function its value; busy_measure picks None
   for a client with MEASURE and judge_passages.busy_runners for one without (a stand-in module each way).
4. A failed after-first-call check stops the arm and records it as refused; a failed fresh load refuses before any
   call; a guard that turns busy before a call stops the arm before that call, and before a fresh load stops it
   before the load.
5. summarise and decide: checks per hour from ok checks over the span; the second port opens only when arm two is
   faster; equal is no; an arm with a check not ok, or a request not matching G1, gives no decision.
6. analyse end to end: reproduces G1's sums from the sink before writing, refuses when they differ, writes REPORT.md
   and report.json with the decision.
7. The guard on canned listings (review F1): free with only the verifier loaded and S2 running; the server's end of
   this process's own connection not counted; refuses on a stranger's connection, another model loaded (K1's
   devstral), a K1 process that names no port, a process naming the port, an unreadable /api/ps or lsof, anything
   listening on the second port, no S2, an existing results.jsonl; a busy survey followed by a free one is free.
8. cmd_run end to end (review F2, F3): a stand-in server binary (a stub that starts a child "runner") on a real
   second port, both arms, the second server and its runner stopped, run.json complete; a calls.jsonl that is not
   the one select read refused; a SIGHUP during arm two (SIGHUP not ignored at start) recorded in run.json, the
   server and runner stopped; started with SIGHUP ignored (nohup), SIGHUP stays ignored through and after the run
   (SIGTERM and SIGINT caught), so a SIGHUP during arm two ends nothing; the SIGHUP, SIGTERM and SIGINT handlers,
   recorded before the first cmd_run, are the same after each run. stop_server: SIGTERM reaches the runner through
   the process group; a server and a runner that both ignore SIGTERM (the runner shown alive after a SIGTERM of its
   own) are killed by the group SIGKILL after the wait, nothing left for the per-pid sweep; a runner that left the
   group is killed by pid.
9. server_env carries the lock's [server] values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import types
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.runner import verifier_ports as V  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from experiments.runner.ollama_client import generate  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS" if ok else "FAIL"), name, detail if not ok else "")


lock = load()
CALL = lock.ollama(V.VERIFIER, role="generator", draw=1, thinking="default")


def sha(b):
    return hashlib.sha256(b.encode() if isinstance(b, str) else b).hexdigest()


def synthetic_sink(d: Path, n_q: int = 30) -> None:
    """answers.jsonl and calls.jsonl as exp_01 writes them, for n_q questions in draws 1 and 2, with traps."""
    answers, calls = [], []
    for i in range(n_q):
        q = f"Q{i:03d}"
        for draw in (1, 2):
            ctx = f"ctx{i}_{draw}"
            prompt = f"You are a scientific relevance judge. question {q} draw {draw}"
            call = lock.ollama(V.VERIFIER, role="generator", draw=draw, thinking="default")
            req = sha(json.dumps(call.payload(prompt)).encode())
            calls.append({"ctx_uid": ctx, "seq": 2, "call_site": "backend/retrieval/chunk_verifier.py:200 verify",
                          "status": "ok", "draw": str(draw), "thinking": "default", "candidate": None,
                          "prompt_sent": prompt, "request_sha256": req, "text": f"[reply {q}]",
                          "server": "http://127.0.0.1:11453", "prompt_tokens": 100 + i, "output_tokens": 10 + i,
                          "wall_s": 1.5 + i, "prompt_eval_s": 0.1, "eval_s": 1.0, "waited_for_server_s": 0.0,
                          "at": "2026-10-17T01:31:45", "run_id": "exp_01__verified_pass__exp_v4_s20_n0"})
            status = "error" if i == 3 else "ok"                      # a verifier that failed: excluded
            answers.append({"answer_key": f"k|{q}|d{draw}", "question_id": q, "draw": draw, "ctx_uid": ctx,
                            "generation": {"verification": {"status": status, "call_seq": 2}}})
    # a failed first attempt of Q000 draw 1, then its answer (the last line) as above: the earlier line is not used
    answers.insert(0, {"answer_key": "k|Q000|d1", "question_id": "Q000", "draw": 1, "ctx_uid": "old",
                       "generation": {"verification": {"status": "unparsed", "call_seq": 2}}})
    d.mkdir(parents=True, exist_ok=True)
    (d / "answers.jsonl").write_text("".join(json.dumps(a) + "\n" for a in answers))
    (d / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))


# 1. choose
tmp = Path(tempfile.mkdtemp(prefix="check_verifier_ports_"))
sink = tmp / "sink"
synthetic_sink(sink)
answers = [json.loads(x) for x in (sink / "answers.jsonl").read_text().splitlines()]
calls = [json.loads(x) for x in (sink / "calls.jsonl").read_text().splitlines()]
picked = V.choose(answers, calls)
pool = sorted(f"Q{i:03d}" for i in range(30) if i != 3)
check("choose takes 20", len(picked) == 20)
check("choose: draw 1 only", all(int(c["draw"]) == 1 for c in picked))
check("choose: positions floor(i * n / 20) of the sorted pool",
      [c["question_id"] for c in picked] == [pool[(i * len(pool)) // 20] for i in range(20)])
check("choose: a failed verifier is not chosen", "Q003" not in [c["question_id"] for c in picked])
check("choose: a key's last line is its answer (Q000 kept, from ctx0_1)",
      any(c["question_id"] == "Q000" and c["ctx_uid"] == "ctx0_1" for c in picked))
try:
    V.choose(answers[:10], calls)
    check("choose refuses fewer than 20", False)
except SystemExit:
    check("choose refuses fewer than 20", True)

out = tmp / "out"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(out)))
manifest = json.loads((out / "checks.json").read_text())
check("select stores no prompt", "prompt_sent" not in (out / "checks.json").read_text()
      and "relevance judge" not in (out / "checks.json").read_text())
check("select stores G1's sums", manifest["g1_wall_s_sum"] == round(sum(c["g1"]["wall_s"] for c in picked), 3))
check("select without --copy-of: sink is the path read, no copy note",
      manifest["sink"] == str(sink) and manifest["read_from"] == str(sink.resolve()) and "copy_note" not in manifest)
out_copy = tmp / "out_copy"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(out_copy), copy_of="/Users/studio/runs/sink"))
mc = json.loads((out_copy / "checks.json").read_text())
check("select --copy-of: sink names the Studio path, read_from the copy, a copy note, the copy's hashes",
      mc["sink"] == "/Users/studio/runs/sink" and mc["read_from"] == str(sink.resolve()) and "copy_note" in mc
      and mc["calls_sha256"] == sha((sink / "calls.jsonl").read_bytes()) and mc["checks"] == manifest["checks"])

# 2. replay_calls
work = V.replay_calls(manifest, sink, lock)
check("replay rebuilds every request to G1's bytes", len(work) == 20)
bad = sink.parent / "sink_bad"
bad.mkdir()
(bad / "calls.jsonl").write_text((sink / "calls.jsonl").read_text().replace("question Q000 draw 1", "question Q000 draw 1 "))
try:
    V.replay_calls(manifest, bad, lock)
    check("replay refuses an edited prompt", False)
except SystemExit as e:
    check("replay refuses an edited prompt", "rebuilds to request" in str(e))
(bad / "calls.jsonl").write_text("")
try:
    V.replay_calls(manifest, bad, lock)
    check("replay refuses a missing call", False)
except SystemExit as e:
    check("replay refuses a missing call", "is not in" in str(e))


# 3. run_arm against stub servers
class Stub(BaseHTTPRequestHandler):
    received: list = []
    delay = 0.05

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
            self._json({"version": lock.d["server"]["ollama_version"]})
        elif self.path == "/api/tags":
            self._json({"models": [{"name": CALL.model, "digest": CALL.digest}]})
        else:
            self.send_error(404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        Stub.received.append((self.server.server_address[1], sha(data), time.time()))
        time.sleep(Stub.delay)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        self.wfile.write(json.dumps({"response": "[ok]", "done": False}).encode() + b"\n")
        self.wfile.write(json.dumps({"response": "", "done": True, "done_reason": "stop", "prompt_eval_count": 5,
                                     "eval_count": 7, "eval_duration": 5 * 10**7, "total_duration": 6 * 10**7,
                                     "load_duration": 10**6, "prompt_eval_duration": 10**6}).encode() + b"\n")


servers = [ThreadingHTTPServer(("127.0.0.1", 0), Stub) for _ in range(2)]
for s in servers:
    threading.Thread(target=s.serve_forever, daemon=True).start()
P1, P2 = (s.server_address[1] for s in servers)
loads_seen = []
guard_seen = []


def fake_fresh_load(base, model, log, binary, machine):
    loads_seen.append(base)
    return {"base": base, "model": model, "ok": True}


def fake_after(rec, log, binary, machine, first=None):
    rec["after_first_call"] = {"first_call": first and first.get("request_sha256")}
    return rec


def free_guard(p):
    guard_seen.append(p)
    return {"port": p, "busy": False, "processes": [], "connections": [], "loaded": [], "unreadable": []}


def busy_guard_after(n):
    """A guard that turns busy on its n-th survey (K1's devstral appears on the port)."""
    seen = []

    def g(p):
        seen.append(p)
        if len(seen) >= n:
            return {"port": p, "busy": True, "processes": [], "connections": [], "unreadable": [],
                    "loaded": [{"model": "devstral-small-2:24b", "why": "not one of this launcher's models"}]}
        return {"port": p, "busy": False, "processes": [], "connections": [], "loaded": [], "unreadable": []}
    return g


busy_n = iter(range(1000))
arm_out = tmp / "arm"
arm_out.mkdir()
one = V.run_arm("one", [P1], work, arm_out, lambda: next(busy_n), generate, fake_fresh_load, fake_after,
                lambda p: Path("/dev/null"), free_guard)
rows = [json.loads(x) for x in (arm_out / "results.jsonl").read_text().splitlines()]
check("arm one: 20 checks on one port, in order",
      len(rows) == 20 and {r["port"] for r in rows} == {P1} and [r["position"] for r in rows] == list(range(20)))
check("arm one: every request is G1's bytes, as the stub received them",
      all(r["request_matches_g1"] for r in rows)
      and [h for p, h, _ in Stub.received] == [c["request_sha256"] for c in manifest["checks"]])
check("arm one: busy and port recorded on every check",
      all(isinstance(r["busy_servers_on_machine"], int) and r["server"].endswith(str(r["port"])) for r in rows))
check("arm one: status ok, tokens and timings kept", all(r["status"] == "ok" and r["output_tokens"] == 7
                                                         and r["t_end"] >= r["t_start"] for r in rows))
check("arm one: the fresh-load record holds the after-first-call result",
      "after_first_call" in json.loads((arm_out / f"fresh_load_one_{P1}.json").read_text()))
check("arm one: the guard surveys before the fresh load and before each of the 20 calls, each a guard.jsonl line",
      guard_seen == [P1] * 21 and len((arm_out / "guard.jsonl").read_text().splitlines()) == 21
      and all(isinstance(r["guard_s"], float) for r in rows))
Stub.received.clear()
guard_seen.clear()
two = V.run_arm("two", [P1, P2], work, arm_out, lambda: next(busy_n), generate, fake_fresh_load, fake_after,
                lambda p: Path("/dev/null"), free_guard)
rows2 = [json.loads(x) for x in (arm_out / "results.jsonl").read_text().splitlines()][20:]
check("arm two: every position once", sorted(r["position"] for r in rows2) == list(range(20)))
check("arm two: both ports used", {r["port"] for r in rows2} == {P1, P2})
starts = sorted((t, p) for p, _, t in Stub.received)
overlap = any(a[1] != b[1] and b[0] - a[0] < Stub.delay for a, b in zip(starts, starts[1:]))
check("arm two: the two ports work at the same time", overlap)
check("arm two: fresh load on both ports", loads_seen[-2:] == [f"http://127.0.0.1:{P1}", f"http://127.0.0.1:{P2}"])
check("arm two: the after-first-call check ran on each port (both fresh-load records hold it)",
      all("after_first_call" in json.loads((arm_out / f"fresh_load_two_{p}.json").read_text()) for p in (P1, P2)))
check("arm two: the guard surveys each port before its load and both ports before each call",
      guard_seen[:2] == [P1, P2] and len(guard_seen) == 2 + 2 * 20)

from experiments.runner import ollama_client as OC  # noqa: E402
if hasattr(OC, "MEASURE"):
    arm_out4 = tmp / "arm4"
    arm_out4.mkdir()
    V.run_arm("one", [P1], work[:2], arm_out4, None, generate, fake_fresh_load, fake_after,
              lambda p: Path("/dev/null"), free_guard)
    rows4 = [json.loads(x) for x in (arm_out4 / "results.jsonl").read_text().splitlines()]
    check("busy None with this client (Q146 build): the client measures it, with busy_how",
          all(r["busy_source"] == "ollama_client (Q146)" and r.get("busy_how") for r in rows4))
check("busy given by the test: source named", all(r["busy_source"].startswith("judge_passages") for r in rows))
sent_kw = []


def recording_generate(base, call, prompt, **kw):
    sent_kw.append(kw)
    return {"status": "ok", "request_sha256": None, "text": ""}


arm_out6 = tmp / "arm6"
arm_out6.mkdir()
V.run_arm("one", [P1], work[:2], arm_out6, None, recording_generate, fake_fresh_load, fake_after,
          lambda p: Path("/dev/null"), free_guard)
V.run_arm("one", [P1], work[:2], arm_out6, lambda: 5, recording_generate, fake_fresh_load, fake_after,
          lambda p: Path("/dev/null"), free_guard)
check("busy None: generate gets no busy argument (the client's own MEASURE default); a busy function: its value",
      sent_kw == [{}, {}, {"busy": 5}, {"busy": 5}], sent_kw)
check("busy_measure: None for a client with MEASURE, judge_passages.busy_runners for one without",
      V.busy_measure(types.SimpleNamespace(MEASURE=object())) is None
      and V.busy_measure(types.SimpleNamespace()).__name__ == "busy_runners"
      and V.busy_measure(types.SimpleNamespace()).__module__ == "experiments.scorers.judge_passages")


# 4. refusals inside an arm
def failing_after(rec, log, binary, machine, first=None):
    raise RuntimeError("the runner that answered is not the one loaded")


arm_out2 = tmp / "arm2"
arm_out2.mkdir()
r = V.run_arm("one", [P1], work, arm_out2, lambda: 0, generate, fake_fresh_load, failing_after,
              lambda p: Path("/dev/null"), free_guard)
n_lines = len((arm_out2 / "results.jsonl").read_text().splitlines())
check("a failed after-first-call stops the arm", "refused" in r and n_lines == 1, f"{r} {n_lines}")
arm_out5 = tmp / "arm5"
arm_out5.mkdir()


def raising_generate(*a, **k):
    raise RuntimeError("the server holds another digest")


r = V.run_arm("one", [P1], work, arm_out5, lambda: 0, raising_generate, fake_fresh_load, fake_after,
              lambda p: Path("/dev/null"), free_guard)
check("a call that raises stops the arm and is recorded", "refused" in r and "another digest" in r["refused"]
      and not (arm_out5 / "results.jsonl").exists())
arm_out3 = tmp / "arm3"
arm_out3.mkdir()
r = V.run_arm("one", [P1], work, arm_out3, lambda: 0, generate, lambda *a: {"ok": False}, fake_after,
              lambda p: Path("/dev/null"), free_guard)
check("a failed fresh load refuses before any call", "refused" in r and not (arm_out3 / "results.jsonl").exists())
arm_out7 = tmp / "arm7"
arm_out7.mkdir()
Stub.received.clear()
r = V.run_arm("one", [P1], work, arm_out7, lambda: 0, generate, fake_fresh_load, fake_after,
              lambda p: Path("/dev/null"), busy_guard_after(6))
n7 = len((arm_out7 / "results.jsonl").read_text().splitlines())
check("a guard busy before a call stops the arm before that call (4 calls sent, the 5th not)",
      "refused" in r and "another user" in r["refused"] and "devstral" in r["refused"] and n7 == 4
      and len(Stub.received) == 4, f"{r} {n7}")
loads_before = len(loads_seen)
arm_out8 = tmp / "arm8"
arm_out8.mkdir()
r = V.run_arm("one", [P1], work, arm_out8, lambda: 0, generate, fake_fresh_load, fake_after,
              lambda p: Path("/dev/null"), busy_guard_after(1))
check("a guard busy before the fresh load refuses with no load and no call",
      "refused" in r and len(loads_seen) == loads_before and not (arm_out8 / "results.jsonl").exists())


# 5. summarise and decide
def row(arm, pos, port, t0, t1, status="ok", busy=1, match=True):
    return {"arm": arm, "position": pos, "port": port, "t_start": t0, "t_end": t1, "status": status,
            "wall_s": t1 - t0, "eval_s": (t1 - t0) * 0.8, "output_tokens": 1000, "busy_servers_on_machine": busy,
            "request_matches_g1": match, "reply_sha256": str(pos)}


a1 = V.summarise([row("one", i, 1, i * 60.0, (i + 1) * 60.0) for i in range(20)])
check("checks per hour = ok checks / span * 3600", a1["checks_per_hour"] == 60.0 and a1["span_s"] == 1200.0)
fast = V.summarise([row("two", i, 1 + i % 2, (i // 2) * 90.0, (i // 2 + 1) * 90.0) for i in range(20)])
same = V.summarise([row("two", i, 1 + i % 2, (i // 2) * 120.0, (i // 2 + 1) * 120.0) for i in range(20)])
check("two ports faster: the second opens", V.decide(a1, fast)["open_second_port"] is True)
check("two ports equal: it does not open", V.decide(a1, same)["open_second_port"] is False)
part = V.summarise([row("two", i, 1, i * 30.0, (i + 1) * 30.0, status="error" if i == 5 else "ok")
                    for i in range(20)])
check("a check not ok: no decision", V.decide(a1, part)["open_second_port"] is None)
nomatch = V.summarise([row("two", i, 1 + i % 2, (i // 2) * 90.0, (i // 2 + 1) * 90.0, match=i != 7)
                       for i in range(20)])
check("a request not matching G1 (all ok, faster): no decision",
      nomatch["ok"] == 20 and V.decide(a1, nomatch)["open_second_port"] is None)
check("busy per port", fast["per_port"]["1"]["busy_median"] == 1 and fast["per_port"]["2"]["checks"] == 10)

# 6. analyse end to end
res = out / "results.jsonl"
res.write_text("".join(json.dumps(r) + "\n" for r in
                       [row("one", i, 11453, i * 60.0, (i + 1) * 60.0) for i in range(20)]
                       + [row("two", i, 11453 + 3 * (i % 2), (i // 2) * 90.0, (i // 2 + 1) * 90.0)
                          for i in range(20)]))
V.cmd_analyse(argparse.Namespace(out=str(out), sink=str(sink)))
rep = json.loads((out / "report.json").read_text())
check("analyse: reproduces G1's sums first", rep["reproduced"].startswith("G1 sums reproduced"))
check("analyse: decision yes on the faster arm two", rep["decision"]["open_second_port"] is True)
check("analyse: REPORT.md written with the decision", "the second port opens" in (out / "REPORT.md").read_text())
m2 = dict(manifest, g1_wall_s_sum=manifest["g1_wall_s_sum"] + 1)
(out / "checks.json").write_text(json.dumps(m2))
try:
    V.cmd_analyse(argparse.Namespace(out=str(out), sink=str(sink)))
    check("analyse refuses when G1's sums differ", False)
except SystemExit as e:
    check("analyse refuses when G1's sums differ", "are not the ones select stored" in str(e))

# 7. the guard and the preconditions, on canned listings
VER = CALL.model                                         # gpt-oss:20b-date20261010
ME = 999
S2_LINE = ("17129 17128 /x/.venv/bin/python3 experiments/mentori/publication/scripts/exp_05_coder_benchmark.py "
           "--model ollama::gpt-oss:20b --thinking high --base-url http://127.0.0.1:11452\n")
PS_FREE = S2_LINE + f"{ME} 1 python -m experiments.runner.verifier_ports run --sink /s\n"
LSOF_HEAD = "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\n"


def lsof_line(cmd, pid, name):
    return f"{cmd} {pid} bio 12u IPv4 0xabc 0t0 TCP {name} (ESTABLISHED)\n"


def canned(ps=PS_FREE, est="", listen="", fail=(), flip=None):
    """A runner for ps and lsof; flip: listings that replace est after the first lsof read (a transient)."""
    state = {"lsof_est": 0}

    def runner(cmd):
        if cmd[0] in fail:
            raise OSError(f"{cmd[0]} cannot run")
        if cmd[0] == "ps":
            return 0, ps, ""
        if cmd[0] == "lsof":
            if "-sTCP:LISTEN" in cmd:
                return (0 if listen else 1), listen, ""
            state["lsof_est"] += 1
            text = flip if flip is not None and state["lsof_est"] > 1 else est
            return (0 if text else 1), (LSOF_HEAD + text) if text else "", ""
        return 1, "", "unknown"
    return runner


def ps_get(*models):
    return lambda url: {"models": [{"name": m} for m in models]}


def bad_get(url):
    raise OSError("connection refused")


def pre(runner=None, get=ps_get(VER), outdir=None):
    w, g = V.preconditions(11453, 11456, outdir or (tmp / "pre_empty"), VER, 0, runner=runner or canned(), get=get,
                           me=ME, platform="darwin")
    return w, g


(tmp / "pre_empty").mkdir()
w, g = pre()
check("guard: free with only the verifier loaded and S2 running", w == [] and g["verifier_loaded"] == [VER], w)
own = (lsof_line("python", ME, "127.0.0.1:50001->127.0.0.1:11453")
       + lsof_line("ollama", 500, "127.0.0.1:11453->127.0.0.1:50001"))
w, g = pre(canned(est=own))
check("guard: the server's end of this process's own call is not a user", w == []
      and g["own_connections_not_counted"] == 1, w)
stranger = own + (lsof_line("python", 777, "127.0.0.1:50002->127.0.0.1:11453")
                  + lsof_line("ollama", 500, "127.0.0.1:11453->127.0.0.1:50002"))
w, g = pre(canned(est=stranger))
check("guard: a stranger's established connection refuses", any("another user" in x for x in w)
      and len(g["connections"]) == 2, w)
w, _ = pre(get=ps_get(VER, "devstral-small-2:24b"))
check("guard: another model loaded on the port (K1's devstral) refuses",
      any("devstral-small-2:24b loaded" in x for x in w), w)
w, _ = pre(canned(ps=PS_FREE + "4242 4200 bash findings/recompute/K1/run_k1_studio.sh\n"
                  "4243 4242 python scripts/S357_ragas.py --assignment findings/recompute/K1/assignment.json\n"))
check("guard: a K1 process that names no port refuses", any("matches the job pattern" in x for x in w), w)
w, _ = pre(canned(ps=PS_FREE + "5151 1 python monitor.py --base http://127.0.0.1:11453\n"))
check("guard: a process naming the port refuses", any("names the port" in x for x in w), w)
G1_PS = PS_FREE + "55401 1 python experiments/mentori/publication/scripts/exp_01_generation.py --configs rlm_5\n"
w, _ = pre(canned(ps=G1_PS))
check("guard: an exp_01 process refuses (G1's rule for 11453)", any("exp_01_generation" in x for x in w), w)
w, _ = pre(get=bad_get)
check("guard: an unreadable /api/ps refuses (fail closed)", any("cannot read /api/ps" in x for x in w), w)
w, _ = pre(canned(fail=("lsof",)))
check("guard: an unreadable lsof refuses (fail closed)", any("cannot read lsof" in x for x in w)
      and any("listens on port 11456" in x for x in w), w)
w, _ = pre(canned(listen="ollama 600 bio 3u IPv4 0xdef 0t0 TCP 127.0.0.1:11456 (LISTEN)\n"))
check("preconditions refuse when something listens on the second port", any("listens on port 11456" in x for x in w)
      and not any("another user" in x for x in w), w)
w, _ = pre(canned(ps=f"{ME} 1 python verifier_ports run\n"))
check("preconditions refuse when no S2 runs", any("no Figure 6 rerun" in x for x in w), w)
w, _ = pre(outdir=out)
check("preconditions refuse an existing results.jsonl", any("results.jsonl exists" in x for x in w), w)
g = V.guard_port(11453, VER, 0, runner=canned(est=stranger, flip=own), get=ps_get(VER), me=ME, platform="darwin")
check("guard: a busy survey followed by a free one is free (the first kept)",
      g["busy"] is False and g.get("first_survey", {}).get("busy") is True)
g = V.guard_port(11453, VER, 0, runner=canned(est=stranger), get=ps_get(VER), me=ME, platform="darwin")
check("guard: busy twice is busy", g["busy"] is True and g.get("first_survey", {}).get("busy") is True)
PS = ("17129 /x/.venv/bin/python3 experiments/mentori/publication/scripts/exp_05_coder_benchmark.py --model "
      "ollama::gpt-oss:20b --thinking high --base-url http://127.0.0.1:11452\n"
      "17128 uv run --project experiments/mentori --frozen python experiments/mentori/publication/scripts/"
      "exp_05_coder_benchmark.py --model ollama::gpt-oss:20b --thinking high --base-url http://127.0.0.1:11452\n")
check("s2_running names each variant once", V.s2_running(PS) == ["ollama::gpt-oss:20b high http://127.0.0.1:11452"])
check("arm records the S2 variants at start and end", "s2_at_start" in one and "s2_at_end" in two)

# 8. cmd_run end to end, with a stand-in server binary on a real second port
STUB_SERVER = r'''
import json, os, signal, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
MODE, PIDFILE, VERSION, MODEL, DIGEST = {cfg}
if MODE == "ignore_term":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
RUNNER = ("import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(600)"
          if MODE == "ignore_term" else "import time; time.sleep(600)")   # ignore_term: the runner ignores it too
runner = subprocess.Popen([sys.executable, "-c", RUNNER], start_new_session=(MODE == "runner_leaves"))
open(PIDFILE, "w").write(json.dumps({{"server": os.getpid(), "runner": runner.pid}}))
host, port = os.environ["OLLAMA_HOST"].rsplit(":", 1)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/version": self._json({{"version": VERSION}})
        elif self.path == "/api/tags": self._json({{"models": [{{"name": MODEL, "digest": DIGEST}}]}})
        else: self.send_error(404)
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"])); time.sleep(0.05)
        self.send_response(200); self.send_header("Content-Type", "application/x-ndjson"); self.end_headers()
        self.wfile.write(json.dumps({{"response": "[ok]", "done": False}}).encode() + b"\n")
        self.wfile.write(json.dumps({{"response": "", "done": True, "done_reason": "stop", "prompt_eval_count": 5,
            "eval_count": 7, "eval_duration": 5 * 10**7, "total_duration": 6 * 10**7, "load_duration": 10**6,
            "prompt_eval_duration": 10**6}}).encode() + b"\n")
ThreadingHTTPServer((host, int(port)), H).serve_forever()
'''


def stub_binary(name, mode):
    pidfile = tmp / f"{name}.pids"
    cfg = repr((mode, str(pidfile), lock.d["server"]["ollama_version"], CALL.model, CALL.digest))
    p = tmp / f"{name}.py"
    p.write_text(f"#!{sys.executable}\n" + STUB_SERVER.format(cfg=cfg))
    p.chmod(0o755)
    return p, pidfile


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def gone(pid, wait=5.0):
    t = time.time() + wait
    while time.time() < t:
        if not V.alive(pid):
            return True
        try:
            os.waitpid(pid, os.WNOHANG)                  # reap it if it is this process's own child
        except ChildProcessError:
            pass
        time.sleep(0.1)
    return not V.alive(pid)


V.LOG_DIR = tmp / "logs"
SURVEY = {"runner": canned(), "get": ps_get(VER), "me": ME, "platform": "darwin", "confirm_s": 0}
DEPS = {"generate": generate, "fresh_load": fake_fresh_load, "after_first_call": fake_after, "busy": lambda: 0,
        "survey": SURVEY}
SIGS = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
handlers = lambda: {s: signal.getsignal(s) for s in SIGS}   # noqa: E731
H0 = handlers()                                   # N2: recorded before the first cmd_run
run_out = tmp / "run_out"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(run_out), copy_of=None))
V.BINARY, pids_file = stub_binary("stub_ok", "ok")
P3 = free_port()
rc = V.cmd_run(argparse.Namespace(sink=str(sink), out=str(run_out), first_port=P1, second_port=P3,
                                  keep_second=False), DEPS)
rr = [json.loads(x) for x in (run_out / "results.jsonl").read_text().splitlines()]
H1 = handlers()                                   # after the first cmd_run
runj = json.loads((run_out / "run.json").read_text())
srvj = json.loads((run_out / "second_server.json").read_text())
pids = json.loads(pids_file.read_text())
check("cmd_run: both arms, 20 checks each, arm two on both ports, the second through the started server",
      rc == 0 and len(rr) == 40 and {r["port"] for r in rr if r["arm"] == "two"} == {P1, P3}
      and all(r["status"] == "ok" for r in rr), f"rc {rc}")
check("cmd_run: the second server and its runner are stopped, the stop recorded",
      gone(pids["server"]) and gone(pids["runner"]) and srvj["pid"] == pids["server"] and "stopped_at" in srvj
      and pids["runner"] in srvj["descendants"] and srvj["left_after_stop"] == [], srvj)
check("cmd_run: run.json holds both arms, the start survey and an end, and no arm in progress",
      [x["arm"] for x in runj["arms"]] == ["one", "two"] and "ended_at" in runj and "in_progress" not in runj
      and runj["start_survey"]["busy"] is False and "interrupted" not in runj)

bad_sink = tmp / "sink_extra"
bad_sink.mkdir()
(bad_sink / "calls.jsonl").write_text((sink / "calls.jsonl").read_text() + "\n")
run_out2 = tmp / "run_out2"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(run_out2), copy_of=None))
try:
    V.cmd_run(argparse.Namespace(sink=str(bad_sink), out=str(run_out2), first_port=P1, second_port=free_port(),
                                 keep_second=False), DEPS)
    check("cmd_run refuses a calls.jsonl that is not the one select read", False)
except SystemExit as e:
    check("cmd_run refuses a calls.jsonl that is not the one select read", "calls_sha256 differs" in str(e)
          and not (run_out2 / "run.json").exists())

run_out3 = tmp / "run_out3"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(run_out3), copy_of=None))
V.BINARY, pids_file3 = stub_binary("stub_hup", "ok")
n_two = []


def hup_generate(base, call, prompt, **kw):
    if not base.endswith(f":{P1}") or n_two:
        n_two.append(base)
        if len(n_two) == 3:
            os.kill(os.getpid(), signal.SIGHUP)          # the ssh session drops during arm two
    return generate(base, call, prompt, **kw)


if H0[signal.SIGHUP] == signal.SIG_IGN:           # this check itself run under nohup: SIGHUP must reach cmd_run
    signal.signal(signal.SIGHUP, signal.SIG_DFL)
H2 = handlers()
P4 = free_port()
rc3 = V.cmd_run(argparse.Namespace(sink=str(sink), out=str(run_out3), first_port=P1, second_port=P4,
                                   keep_second=False), dict(DEPS, generate=hup_generate))
H3 = handlers()
signal.signal(signal.SIGHUP, H0[signal.SIGHUP])
runj3 = json.loads((run_out3 / "run.json").read_text())
pids3 = json.loads(pids_file3.read_text())
check("cmd_run: a SIGHUP during arm two is recorded with the arm, and the run exits 1",
      rc3 == 1 and runj3.get("interrupted", {}).get("signal") == "SIGHUP"
      and runj3["interrupted"]["during"] == "arm two" and "ended_at" in runj3, runj3.get("interrupted"))
check("cmd_run: after the SIGHUP the second server and its runner are stopped",
      gone(pids3["server"]) and gone(pids3["runner"])
      and "stopped_at" in json.loads((run_out3 / "second_server.json").read_text()))
V.ABORT.clear()

# Q152 review: started under nohup, SIGHUP is ignored, and cmd_run must leave it so (a dropped ssh session)
run_out4 = tmp / "run_out4"
V.cmd_select(argparse.Namespace(sink=str(sink), out=str(run_out4), copy_of=None))
V.BINARY, pids_file4 = stub_binary("stub_hup_ignored", "ok")
seen4, n_two4 = [], []


def hup_ignored_generate(base, call, prompt, **kw):
    seen4.append((signal.getsignal(signal.SIGHUP), signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)))
    if not base.endswith(f":{P1}") or n_two4:
        n_two4.append(base)
        if len(n_two4) == 3:
            os.kill(os.getpid(), signal.SIGHUP)          # the ssh session drops during arm two
    return generate(base, call, prompt, **kw)


signal.signal(signal.SIGHUP, signal.SIG_IGN)      # as nohup leaves it
try:
    rc4 = V.cmd_run(argparse.Namespace(sink=str(sink), out=str(run_out4), first_port=P1, second_port=free_port(),
                                       keep_second=False), dict(DEPS, generate=hup_ignored_generate))
finally:
    hup_after4 = signal.getsignal(signal.SIGHUP)
    signal.signal(signal.SIGHUP, H0[signal.SIGHUP])
runj4 = json.loads((run_out4 / "run.json").read_text())
pids4 = json.loads(pids_file4.read_text())
V.ABORT.clear()
check("cmd_run started with SIGHUP ignored (nohup): SIGHUP stays ignored at every call and after the run, SIGTERM "
      "and SIGINT are caught, and a SIGHUP during arm two ends nothing (both arms complete, nothing interrupted)",
      rc4 == 0 and len(seen4) == 40 and len(n_two4) >= 3
      and all(h == signal.SIG_IGN and t is V._interrupt and i is V._interrupt for h, t, i in seen4)
      and hup_after4 == signal.SIG_IGN and "interrupted" not in runj4
      and [x["arm"] for x in runj4["arms"]] == ["one", "two"] and gone(pids4["server"]) and gone(pids4["runner"]),
      (rc4, runj4.get("interrupted"), sorted({str(h) for h, _, _ in seen4}), hup_after4))
check("cmd_run: the SIGHUP, SIGTERM and SIGINT handlers, recorded before the first cmd_run, are the same after each "
      "run (the ok run, the SIGHUP run, the run started with SIGHUP ignored once its ignore is undone)",
      H1 == H0 and H3 == H2 and handlers() == H0, {"before": H0, "after_first": H1, "after_hup": H3})


def started_stub(name, mode):
    binary, pf = stub_binary(name, mode)
    V.BINARY = binary
    port = free_port()
    st = {}
    out_s = tmp / f"srv_{name}"
    out_s.mkdir()
    rec, proc = V.start_server(port, lock, out_s, st)
    for _ in range(50):
        if pf.exists() and pf.read_text():
            break
        time.sleep(0.1)
    return rec, proc, json.loads(pf.read_text())


rec, proc, pp = started_stub("stub_term", "ignore_term")
time.sleep(0.5)                                   # the runner has set its SIG_IGN
os.kill(pp["runner"], signal.SIGTERM)             # N3: the runner itself ignores SIGTERM
time.sleep(0.5)
runner_ignores = V.alive(pp["runner"])
t0 = time.time()
V.stop_server(rec, proc, wait_s=1)
check("stop_server: a server and a runner that both ignore SIGTERM (the runner alive after a SIGTERM of its own) are "
      "killed by the group SIGKILL after the wait, nothing left for the per-pid sweep",
      runner_ignores and rec.get("sigkill_group") is True and pp["runner"] in rec["descendants"]
      and rec["left_after_stop"] == [] and gone(pp["server"]) and gone(pp["runner"]) and time.time() - t0 < 20, rec)
rec, proc, pp = started_stub("stub_leaves", "runner_leaves")
V.stop_server(rec, proc, wait_s=1)
check("stop_server: a runner that left the group is killed by pid, and recorded",
      gone(pp["server"]) and gone(pp["runner"]) and rec["left_after_stop"] == [pp["runner"]], rec)

# 9. server env
env = V.server_env(11456, lock)
s = lock.d["server"]
check("server_env carries the lock's [server] values",
      env["OLLAMA_HOST"] == "127.0.0.1:11456" and env["OLLAMA_NUM_PARALLEL"] == str(s["num_parallel"])
      and env["OLLAMA_KV_CACHE_TYPE"] == s["kv_cache_type"] and env["OLLAMA_KEEP_ALIVE"] == s["keep_alive"]
      and env["OLLAMA_FLASH_ATTENTION"] == ("1" if s["flash_attention"] else "0"))

for srv in servers:
    srv.shutdown()
print(f"{sum(RESULTS)}/{len(RESULTS)} checks passed")
sys.exit(0 if all(RESULTS) else 1)
