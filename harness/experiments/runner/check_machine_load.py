"""Checks for D83 Q146, D89 A1 and D90: busy_servers_on_machine on every local model call, from a sampler beside the
calls (experiments/runner/machine_load.py and ollama_client.py), and the rebuild of past calls' load
(scripts/S452_q146_load_rebuild.py). No model call, no ssh.

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_machine_load

(the Mentori copy's environment, for the lock adapter's part; everything else is standard library.)

A. machine_load: ps's CPU time in macOS and Linux forms; which processes are runners; the count is the judge's
   (CPU time grew by >= 0.1 s in the window; a runner that appears in the window is not counted); a loopback or own
   address is this machine, a TEST-NET address is not; a server on another machine and an unreadable process list
   give None with the reason, without counting. Where ps shows no ollama serve (the Beelink, whose server is the
   Windows app outside WSL's sight), the count comes from Windows' process list read from WSL: its lines as
   PowerShell printed them on the Beelink on 17 October (llama-server.exe and `ollama.exe runner` are runners,
   `ollama.exe serve` is the server, `ollama app.exe` neither), two readings a window apart, None with the reason when
   it cannot be read, lacks a reading or shows no server, and None when there is no Windows process list either.
   A mutant of machine_load without the Windows reading gives None there, and the check fails on it.
B. ollama_client through a stub Ollama on 127.0.0.1, with D89 A1's sampler (a stand-in reading of two servers, the
   stub's and another, each with a busy runner): generate, chat and embed record busy_servers_on_machine (1: the other
   server; the called server left out), busy_how the sampled reading's, busy_offset_s and busy_overlap, the offset
   being the time from the post the stub received to the end of a reading the sampler took, and busy_overlap true
   exactly when that reading's window overlapped the call; a call held 1.2 s by the stub (readings 0.3 s long every
   0.5 s) gets an overlapping reading, through generate and through embed (D90 O2); the process's first call waits
   for the first reading outside the server gate (the reading saw the gate free); with a 2 s reading always in
   progress no call waits for it (each posted within 0.25 s) while the readings run beside calls holding the gate; a
   mutant on the old path (the window inside the gate) waits before posting, so the no-wait check fails on it. busy=
   given by the caller is recorded as given with no offset and no reading; a server on another machine, no server on
   the called port, ports unread, a failed reading and no reading yet each give None with the reason; every LOCK.toml
   [record] field is in each record, and no record carries busy_age_s (D89 A1's field).
O. D90: (O1) servers, not runners: two busy runners of one other server (a K1 server's devstral and bge-m3) count
   once, on a macOS reading and on the Beelink's; a mutant count_for counting runners gives 2, not 1. (Q1) the called
   server is left out even when only it was busy (another client's call): 0; a mutant that keeps it gives 1. (O2)
   pick(): of the readings whose window overlaps the call, the one nearest the call's middle (the earlier on a tie);
   a reading whose window holds the whole call; none overlapping: the latest that ended by the post; none at all:
   None; at_end() on canned readings: an overlapping reading is used however long after the post it came, with its
   offset; with no overlap a reading that ended over MAX_AGE_S before the post is refused with its offset; a mutant
   pick() without the overlap rule (D89 A1's latest reading before the post) gives the earlier reading, so the
   checks fail on it. A failed reading overlapping the call does not hide a successful one that also overlapped
   (review F3); a mutant letting it compete picks the failure. The sampler keeps HISTORY readings and a forked child
   starts with none of its parent's.
S. A sampler that stalls (review of 17 October, F1 F3 F4 F7): a reading that answers once and then hangs gives the
   count while the reading is fresh, then None with its offset once it ended more than MAX_AGE_S before the post (a
   mutant without the age limit keeps the stale count, and the check fails on it); a reading that never comes costs
   the process's calls the
   first wait once, not per call (the old ready(), a mutant, waits on every call); a timed-out reading's process group
   is killed whole, its child too (subprocess.run's timeout, a mutant, leaves the child running); the Beelink's
   PowerShell reads the listeners before the window, so the call returns as the window ends, and limits each CIM
   query on the Windows side.
W. The sampler's reading on the Beelink (the listeners of MSFT_NetTCPConnection, then Win32_Process with ParentProcessId,
   as PowerShell printed them there on 17 October, plus A2's second server on 11435): each runner with its server, a call to either
   port counting the other's runner; a mutant count_for that keeps the called server's runner gives 2, not 1.
C. The lock adapter (Mentori's every call, G3, G4, G5, T3): an Ollama generate and chat write records carrying the
   sampler's count, how it was taken, its offset and whether it overlapped the call.
D. Every caller takes the sampler's path (D89 A1): the only busy= passed to the client is verifier_ports' branch for a
   client without MEASURE; no module calls the window count outside machine_load, the passage judge's own definition
   and that branch; the passage judge passes no busy=. Its busy_runners (kept, no call path uses it) is still
   machine_load.busy_here's count: on a Beelink-like machine (WSL's ps without the server, Windows' list with a busy
   runner) it gives 1, and None, not 0, when neither list shows a server; its code before the Q146 fix (ps only)
   gives 0 there, and the check fails on it. In experiments/runner only ollama_client posts a model request, apart from
   job.py's model load (fresh_load: the load and unload requests, which produce no answer and no call record).
E. S452's pure functions on canned input: Go durations as GIN prints them, a [GIN] line (a duration over a minute
   is truncated to the second by Gin and taken + 0.5 s), interval merging and the
   load over a span (mean, most at once, share), matching records to log lines (duration and end, one line per
   record, the record without waited_for_server_s, an unmatched record), G1 spans from start and end records (a
   restart after an earlier end is still running), the port of a server URL, and which calls can miss a request still
   running at the reading (they end after the reading minus the longest model request logged on any port).
F. This machine's real count once (reads ps; no model call): an integer; and its real sampler (ps and lsof): a
   first reading in about 1 s, a newer one after, the runners matched to their servers, each window's start read
   about BUSY_WINDOW_S before its end.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "mentori"))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import machine_load as ml  # noqa: E402
from experiments.runner import ollama_client as oc  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import load  # noqa: E402

import S452_q146_load_rebuild as S  # noqa: E402

lock = load()
GEN = "qwen3-coder:30b"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail else ""))


# ---------------------------------------------------------------- A
check("A ps CPU time: macOS MMM:SS.ss, Linux HH:MM:SS and DD-HH:MM:SS",
      ml.parse_cpu_seconds("8352:36.03") == 8352 * 60 + 36.03 and ml.parse_cpu_seconds("0:01.50") == 1.5
      and ml.parse_cpu_seconds("02:03:04") == 7384 and ml.parse_cpu_seconds("1-02:03:04") == 86400 + 7384)
PS = """17140   8352:36.03 /opt/homebrew/Cellar/ollama/0.40.2/libexec/lib/ollama/llama-server --model /x --port 502
 5266     2:35.74 /opt/homebrew/opt/ollama/bin/ollama serve
  901     0:10.00 /usr/local/bin/ollama runner --model /y --port 6001
  902     0:00.10 python3 exp_01_generation.py --ollama-url http://127.0.0.1:11453
"""
check("A runners: llama-server and 'ollama runner' are runners, 'ollama serve' and a client are not",
      ml.runners_from_ps(PS) == {17140: 8352 * 60 + 36.03, 901: 10.0}, ml.runners_from_ps(PS))

seq = iter([{1: 10.0, 2: 5.0, 3: 7.0}, {1: 10.5, 2: 5.05, 3: 7.0, 4: 3.0}])
_real_cpu, _real_time = ml._runner_cpu, ml.time
ml._runner_cpu = lambda: next(seq)
ml.time = type("T", (), {"sleep": staticmethod(lambda s: None)})
n = ml.busy_runners()
ml.time = _real_time


def _raise():
    raise OSError("ps not found")


ml._runner_cpu = _raise
none = ml.busy_runners()
ml._runner_cpu = _real_cpu
check("A count: one runner grew 0.5 s (counted), one 0.05 s and one 0 s (not), one new in the window (not)", n == 1, n)
check("A count: an unreadable process list gives None", none is None)
check("A this machine: 127.0.0.1, localhost, [::1] and this host's name are; TEST-NET 192.0.2.1 is not",
      all(ml.is_this_machine(u) for u in ("http://127.0.0.1:11453", "http://localhost:11453", "http://[::1]:11453",
                                          f"http://{__import__('socket').gethostname()}:1"))
      and not ml.is_this_machine("http://192.0.2.1:11453"))
WSL_PS = """41271 00:00:01 /init /mnt/c/Users/Valerio/AppData/Local/Programs/Ollama/ollama.exe pull qwen3.8:27b
  302 00:00:04 python3 -m experiments.scorers.ragchecker_run --base-url http://127.0.0.1:11434
"""
check("A ollama serve seen in macOS and Linux ps output; not in WSL's, where the server is the Windows app",
      ml.server_visible(PS) and ml.server_visible("  10 00:01:00 /usr/local/bin/ollama serve\n")
      and not ml.server_visible(WSL_PS))

# Windows' process list as PowerShell printed it on the Beelink, 17 October (pid, CPU ticks of 100 ns, command line;
# the llama-server command line shortened), then the same a window later: llama-server.exe grew 0.5 s, serve 0.05 s.
WIN1 = ('10396\t60781250\t"C:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\ollama app.exe" \r\n'
        '32480\t51997812500\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve\r\n'
        '19024\t153666093750\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe '
        '--model C:\\Users\\Valerio\\.ollama\\models\\blobs\\sha256-0dff --port 55768\r\n')
WIN2 = WIN1.replace("153666093750", "153671093750").replace("51997812500", "51998312500")
QUOTED = '501\t20000000\t"C:\\Program Files\\Ollama\\ollama.exe" runner --ollama-engine --model x --port 6001\r\n'
serve1, cpu1 = ml.windows_reading(WIN1)
serve_q, cpu_q = ml.windows_reading(QUOTED)
check("A Windows' list: llama-server.exe is a runner (CPU s from ticks), ollama.exe serve the server, ollama app.exe "
      "neither; a quoted ollama.exe runner is a runner",
      serve1 and cpu1 == {19024: 15366.609375} and cpu_q == {501: 2.0} and not serve_q, (serve1, cpu1, cpu_q))

_real_wr, _real_ps_exe, _real_ps = ml._windows_read, ml.POWERSHELL, ml._ps
win_out = {"text": WIN1 + "---\r\n" + WIN2}
ml._windows_read = lambda: win_out["text"]
ml.POWERSHELL = sys.executable                            # a file that exists: WSL's powershell.exe stands here
ml._ps = lambda: WSL_PS
calls = []
_real_busy = ml.busy_runners
ml.busy_runners = lambda: calls.append(1) or 2
wsl_win = ml.measure("http://127.0.0.1:11434")
win_out["text"] = WIN1.replace("ollama.exe serve", "ollama.exe pull x") + "---\n" + WIN2.replace("ollama.exe serve", "x")
no_serve = ml.busy_here()
win_out["text"] = WIN1
one_reading = ml.busy_here()


def _boom():
    raise OSError("no powershell")


ml._windows_read = _boom
unreadable_win = ml.busy_here()
ml.POWERSHELL = "/nonexistent/powershell.exe"
ml._windows_read = lambda: calls.append("win") or WIN1 + "---\n" + WIN2
no_list = ml.measure("http://127.0.0.1:11434")
check("A ps without the server (WSL): the count from Windows' list, two readings a window apart (llama-server.exe "
      "grew 0.5 s: 1; the server 0.05 s and is not a runner), how says so, ps's count not taken",
      wsl_win == (1, ml.HOW_WINDOWS) and calls == [], wsl_win)
check("A Windows' list without ollama.exe serve, with one reading, or unreadable: None and the reason",
      no_serve[0] is None and "no ollama serve" in no_serve[1] and one_reading[0] is None
      and "two readings" in one_reading[1] and unreadable_win[0] is None and "could not be read" in unreadable_win[1],
      (no_serve, one_reading, unreadable_win))
check("A ps without the server and no Windows list to read: None and the reason, nothing counted (the count would "
      "be 0 whatever ran)", no_list[0] is None and "no ollama serve" in no_list[1] and calls == [], no_list)


def mutant(path: Path, name: str, old: str, new: str):
    """A copy of the module at path with old replaced by new (old must occur once)."""
    src = path.read_text()
    assert src.count(old) == 1, (path, old)
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    sys.modules[name] = mod                      # a dataclass in the module looks its module up while it is defined
    exec(compile(src.replace(old, new), str(path), "exec"), mod.__dict__)
    return mod


m_ml = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_mutant",
              "    if os.path.exists(POWERSHELL):\n        return busy_windows()\n", "")
m_ml._ps, m_ml.POWERSHELL, m_ml._windows_read = (lambda: WSL_PS), sys.executable, (lambda: WIN1 + "---\n" + WIN2)
m_wsl = m_ml.measure("http://127.0.0.1:11434")
check("A mutant (machine_load without the Windows reading): the Beelink case gives None, not 1, so the check above "
      "fails on it", m_wsl[0] is None and m_wsl != (1, ml.HOW_WINDOWS), m_wsl)

ml._ps = lambda: PS
ml.busy_runners = lambda: calls.append(1) or 2
remote = ml.measure("http://192.0.2.1:11453")
ml.busy_runners = lambda: None
unread = ml.measure("http://127.0.0.1:11453")
ml.busy_runners, ml._ps, ml._windows_read, ml.POWERSHELL = _real_busy, _real_ps, _real_wr, _real_ps_exe
check("A a server on another machine: None and the reason, nothing counted",
      remote == (None, "not measured: 192.0.2.1 is not this machine") and calls == [], remote)
check("A an unreadable process list: None and the reason",
      unread == (None, "not measured: the process list could not be read"), unread)


# ---------------------------------------------------------------- B
class Stub(BaseHTTPRequestHandler):
    posted = []
    delay = 0.0                                  # seconds before answering a POST (a call that holds the gate)

    def do_GET(self):
        body = ({"version": lock.d["server"]["ollama_version"]} if self.path == "/api/version"
                else {"models": [{"name": t, "digest": r["digest"]} for t, r in lock.d["models"].items()]})
        self._send(json.dumps(body).encode())

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        Stub.posted.append(time.time())
        time.sleep(Stub.delay)
        done = {"done": True, "done_reason": "stop", "prompt_eval_count": 3, "eval_count": 2}
        if self.path == "/api/embed":
            self._send(json.dumps({"embeddings": [[0.1]], "prompt_eval_count": 1}).encode())
        elif self.path == "/api/chat":
            self._send(b"".join((json.dumps(o) + "\n").encode() for o in (
                {"message": {"role": "assistant", "content": "hi"}, "done": False},
                {"message": {"role": "assistant", "content": ""}, **done})))
        else:
            self._send(b"".join((json.dumps(o) + "\n").encode() for o in (
                {"response": "hi", "done": False}, {"response": "", **done})))

    def _send(self, b):
        self.send_response(200)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{stub.server_address[1]}"
gate = f"/tmp/mentori-ollama-{hashlib.sha1(base.encode()).hexdigest()[:12]}.lock"
STUB_PORT = stub.server_address[1]


def gate_held() -> bool:
    """Another open of the gate file cannot lock it: a call holds the server gate."""
    with open(gate, "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fh, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


class FakeRead:
    """A reading of a machine with two servers: the called one (pid 100, the stub's port; its runner 1 busy) and
    another (pid 200, port 11999; its runner 2 busy). Each read takes `slow` seconds (the window) and notes, halfway,
    whether a call held the gate, and when it ended."""

    def __init__(self, slow: float):
        self.slow, self.log = slow, []

    def __call__(self):
        t0 = time.time()
        time.sleep(self.slow / 2)
        held = gate_held()
        time.sleep(self.slow / 2)
        t = time.time()
        self.log.append({"t0": t0, "t": t, "held": held})
        return ml.Reading(t, ml.HOW_SAMPLED, busy=[(1, 100), (2, 200)], ports={100: {STUB_PORT}, 200: {11999}},
                          servers={100, 200}, t0=t0)


_real_sampler = ml.SAMPLER
fake = FakeRead(0.3)
ml.SAMPLER = ml.Sampler(read=fake, every=0.5)
call = lock.ollama(GEN, draw=1)
Stub.posted.clear()
first_t0 = time.time()
recs = {"generate": oc.generate(base, call, "x")}
first_post = Stub.posted[0]
recs["chat"] = oc.chat(base, call, [{"role": "user", "content": "x"}])
recs["embed"] = oc.embed(base, "bge-m3:latest", ["x"])
fields = set(lock.d["record"]["fields"])
for k, r in recs.items():
    check(f"B {k}: busy_servers_on_machine 1 (the other server; the called server left out), busy_how the sampled "
          f"reading's, busy_offset_s a number, busy_overlap a bool, no busy_age_s, every [record] field",
          r["status"] == "ok" and r["busy_servers_on_machine"] == 1 and r["busy_how"] == ml.HOW_SAMPLED
          and isinstance(r["busy_offset_s"], float) and isinstance(r["busy_overlap"], bool)
          and "busy_age_s" not in r and fields <= set(r),
          f"{r['busy_servers_on_machine']}, {r['busy_how']}, {r.get('busy_offset_s')}, {r.get('busy_overlap')}, "
          f"missing {sorted(fields - set(r))}")
check("B the process's first call waited for the sampler's first reading outside the server gate (the reading saw the "
      "gate free), then posted", fake.log and fake.log[0]["held"] is False and first_post >= fake.log[0]["t"]
      and recs["generate"]["waited_for_server_s"] < 0.1, (fake.log[:1], round(first_post - first_t0, 3)))


def offset_ok(r, post, log) -> tuple:
    """(the reading the record's offset points to, within 0.05 s of a reading's end taken; its overlap as the record
    says it; its overlap as the log's window and the call's span [post, post + wall_s] say it, or the record's own
    answer when an edge of the window falls within 0.05 s of an edge of the call, where the client's clock and the
    stub's differ by the time the post takes to arrive)."""
    hit = [x for x in log if abs((post + r["busy_offset_s"]) - x["t"]) < 0.05]
    if not hit:
        return None, r["busy_overlap"], None
    x = hit[0]
    end = post + r["wall_s"]
    if abs(x["t"] - post) < 0.05 or abs(x["t0"] - end) < 0.05:
        return x, r["busy_overlap"], r["busy_overlap"]
    return x, r["busy_overlap"], x["t0"] < end and x["t"] > post


offs = [offset_ok(r, Stub.posted[i], fake.log) for i, r in enumerate(recs.values())]
check("B busy_offset_s is the time from the post to the end of a reading the sampler took (within 0.05 s, the post "
      "read by the stub), and busy_overlap says whether that reading's window overlapped the call",
      all(x is not None and said == seen for x, said, seen in offs),
      [(r["busy_offset_s"], r["busy_overlap"]) for r in recs.values()])

Stub.delay = 1.2                                         # each call holds the gate 1.2 s: a 0.3 s reading lands inside
long_calls = [oc.generate(base, call, "x"), oc.embed(base, "bge-m3:latest", ["x"])]
Stub.delay = 0.0
long_posts = Stub.posted[-2:]
long_offs = [offset_ok(r, p, fake.log) for r, p in zip(long_calls, long_posts)]
check("B D90 O2: a call held 1.2 s (readings 0.3 s long every 0.5 s) records a reading whose window overlapped it, "
      "with its offset from the post inside the call, through generate and through embed",
      all(r["busy_overlap"] is True and 0 < r["busy_offset_s"] <= r["wall_s"] + 0.35 and r["busy_servers_on_machine"] == 1
          and x is not None and seen for r, (x, _, seen) in zip(long_calls, long_offs)),
      [(r["busy_offset_s"], r["busy_overlap"], r["wall_s"]) for r in long_calls])
check("B the window is not in wall_s (each reading takes 0.3 s; the stub answers at once)",
      all(r["wall_s"] < 0.3 for r in recs.values()), [r["wall_s"] for r in recs.values()])

# no call waits for the reading: readings back to back, each 2 s long, so one is always running
slow = FakeRead(2.0)
ml.SAMPLER = ml.Sampler(read=slow, every=0.0)
ml.SAMPLER.latest(10.0)                                  # the first reading exists; the next is running from now on
Stub.delay = 1.5                                         # each call holds the gate 1.5 s
lat = []
for i in range(5):
    t0 = time.time()
    n0 = len(Stub.posted)
    r = oc.generate(base, call, "x")
    lat.append(round(Stub.posted[n0] - t0, 3))
    time.sleep(0.3)
check("B no call waits for the reading: with a 2 s reading always in progress, 5 calls each posted within 0.25 s of "
      "being made (each call then holds the gate 1.5 s), each with the latest finished reading and its age",
      max(lat) < 0.25 and r["busy_servers_on_machine"] == 1
      and r["busy_offset_s"] is not None and r["busy_offset_s"] > -4.5, lat)
Stub.delay = 0.0
time.sleep(2.2)
check("B the readings run beside the calls: a reading found the gate held by a call while it ran",
      any(x["held"] for x in slow.log), [x["held"] for x in slow.log])

# mutant: the old path (a 1 s window inside the gate before each call) waits there, and the check above fails on it
m_oc = mutant(ROOT / "experiments/runner/ollama_client.py", "ollama_client_old_path",
              '        t_post = time.time()\n        _read(',
              '        rec["busy_servers_on_machine"], rec["busy_how"] = machine_load.measure(base)\n'
              '        t_post = time.time()\n        _read(')
_real_busy2, _real_ps2 = ml.busy_runners, ml._ps
ml.busy_runners = lambda: time.sleep(0.3) or 4
ml._ps = lambda: PS
lat_m = []
for i in range(3):
    t0 = time.time()
    n0 = len(Stub.posted)
    m_oc.generate(base, call, "x")
    lat_m.append(round(Stub.posted[n0] - t0, 3))
ml.busy_runners, ml._ps = _real_busy2, _real_ps2
check("B mutant (the old path: the window inside the gate before posting): each call waits the window before it "
      "posts, so the no-wait check above fails on it", min(lat_m) >= 0.3, lat_m)

ml.SAMPLER = ml.Sampler(read=FakeRead(0.0), every=0.5)
seen_given = len(Stub.posted)
given = oc.generate(base, call, "x", busy=5)
check("B busy= given by the caller: recorded as given, busy_offset_s and busy_overlap None, the sampler not started",
      given["busy_servers_on_machine"] == 5 and given["busy_how"] == "given by the caller"
      and given["busy_offset_s"] is None and given["busy_overlap"] is None and ml.SAMPLER._thread is None)
remote_smp = ml.Sampler(read=FakeRead(0.0))
remote = ml.at_end("http://192.0.2.1:11453", time.time(), time.time(), remote_smp)
check("B a server on another machine: None, the reason, no offset, no reading taken",
      remote == {"busy_servers_on_machine": None, "busy_how": "not measured: 192.0.2.1 is not this machine",
                 "busy_offset_s": None, "busy_overlap": None} and remote_smp._thread is None, remote)
r0 = ml.Reading(1.0, ml.HOW_SAMPLED, busy=[(1, 100), (2, 200), (3, 300)], ports={100: {11441}, 200: {11451}},
                servers={100, 200, 300})
check("B count_for: the runners of the server on the called port are left out (11441: 2; 11451: 2, a runner whose "
      "server lists no port counted as another's); no server on the port, ports unread, a failed reading: None with "
      "the reason",
      ml.count_for(r0, 11441) == (2, ml.HOW_SAMPLED) and ml.count_for(r0, 11451) == (2, ml.HOW_SAMPLED)
      and ml.count_for(r0, 11499)[0] is None and "listens on port 11499" in ml.count_for(r0, 11499)[1]
      and ml.count_for(ml.Reading(1.0, ml.HOW_SAMPLED, busy=[], ports=None, why_ports="lsof failed"), 11441)
      == (None, "not measured: lsof failed")
      and ml.count_for(ml.Reading(1.0, "not measured: the process list could not be read"), 11441)
      == (None, "not measured: the process list could not be read"))
t_ny = time.time()
none_yet = ml.at_end(base, t_ny, t_ny, ml.Sampler(read=lambda: time.sleep(5) or r0, every=10))
check("B no reading yet (at_end never waits): None and the reason, in well under the reading's 5 s",
      none_yet["busy_servers_on_machine"] is None and "no reading yet" in none_yet["busy_how"]
      and time.time() - t_ny < 0.5, none_yet)

# ---------------------------------------------------------------- O: D90


def R(t0, t, busy=((1, 100), (2, 200))):
    return ml.Reading(t, ml.HOW_SAMPLED, busy=list(busy), ports={100: {STUB_PORT}, 200: {11999}}, servers={100, 200},
                      t0=t0)


two_runners = R(0.0, 1.0, busy=[(1, 100), (2, 200), (3, 200)])         # server 200: devstral and bge-m3 both busy
m_runners = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_runners",
                   "    return len({server for _, server in r.busy if server not in own}), r.how\n",
                   "    return sum(1 for _, server in r.busy if server not in own), r.how\n")
check("O O1 servers, not runners: a call to the stub's server, with the other server running two busy runners (a K1 "
      "server's devstral and bge-m3), counts 1", ml.count_for(two_runners, STUB_PORT) == (1, ml.HOW_SAMPLED),
      ml.count_for(two_runners, STUB_PORT))
check("O mutant (count_for counting runners, D89 A1's count): 2, so the check above fails on it",
      m_runners.count_for(two_runners, STUB_PORT)[0] == 2, m_runners.count_for(two_runners, STUB_PORT))
only_called = R(0.0, 1.0, busy=[(1, 100), (4, 100)])                   # only the called server busy (another client)
m_keep = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_keep_called",
                "    return len({server for _, server in r.busy if server not in own}), r.how\n",
                "    return len({server for _, server in r.busy}), r.how\n")
check("O Q1 the called server is left out even when only it was busy (another client's call on it): 0",
      ml.count_for(only_called, STUB_PORT) == (0, ml.HOW_SAMPLED), ml.count_for(only_called, STUB_PORT))
check("O mutant (count_for keeping the called server): 1, so the check above fails on it",
      m_keep.count_for(only_called, STUB_PORT)[0] == 1, m_keep.count_for(only_called, STUB_PORT))

A, B, C, D = R(0, 1), R(5, 6), R(10, 11), R(15, 16)
hist = [A, B, C, D]
p_many = ml.pick(hist, 4.5, 12.0)            # B and C overlap; the call's middle 8.25: C's 10.5 nearer than B's 5.5
p_tie = ml.pick(hist, 3.0, 13.0)             # middle 8: B and C each 2.5 away, the earlier taken
p_inside = ml.pick(hist, 5.5, 5.8)           # the call lies inside B's window
p_none = ml.pick(hist, 6.5, 9.0)             # no window overlaps: the latest that ended by the post, B
p_edge = ml.pick(hist, 6.0, 9.0)             # B ends at the post: not an overlap, the latest before
p_empty = ml.pick(hist, -3.0, -2.0)
check("O O2 pick(): of the overlapping readings the one nearest the call's middle (C for a call 4.5 to 12), the "
      "earlier on a tie, a window holding the whole call, else the latest that ended by the post (also one ending at "
      "the post), else None",
      p_many == (C, True) and p_tie == (B, True) and p_inside == (B, True) and p_none == (B, False)
      and p_edge == (B, False) and p_empty == (None, False),
      [(x[0].t if x[0] else None, x[1]) for x in (p_many, p_tie, p_inside, p_none, p_edge, p_empty)])
m_pick = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_latest_before",
                "    over = [r for r in readings if r.start < t_end and r.t > t_post]\n", "    over = []\n")
check("O mutant (pick without the overlap rule: the latest reading before the post, D89 A1's): A, not C, for the "
      "call 4.5 to 12 and A, not B, for the call inside B's window, so the check above fails on it",
      m_pick.pick(hist, 4.5, 12.0) == (A, False) and m_pick.pick(hist, 5.5, 5.8) == (A, False))


class Held:
    """A sampler stand-in with canned finished readings (at_end only asks for readings())."""

    def __init__(self, readings):
        self._r = readings

    def readings(self):
        return list(self._r)


late = Held([R(0, 1), R(500, 501, busy=[(1, 100), (2, 200), (3, 300)])])   # a long call; a reading 400 s in
e_long = ml.at_end(base, 100.0, 1000.0, late)
e_stale = ml.at_end(base, 100.0, 101.0, Held([R(0, 1)]))
e_fresh = ml.at_end(base, 5.0, 6.0, Held([R(0, 1)]))
check("O O2 at_end(): an overlapping reading is used however long after the post it came (offset 401, overlap true, "
      "count 2: servers 200 and 300); no overlap and the latest ended 99 s before the post: None with offset -99 and "
      "the reason; no overlap and 4 s before: used, offset -4, overlap false",
      e_long == {"busy_servers_on_machine": 2, "busy_how": ml.HOW_SAMPLED, "busy_offset_s": 401.0, "busy_overlap": True}
      and e_stale["busy_servers_on_machine"] is None and e_stale["busy_offset_s"] == -99.0
      and e_stale["busy_overlap"] is False and "99.0 s before the post, over 10 s" in e_stale["busy_how"]
      and e_fresh == {"busy_servers_on_machine": 1, "busy_how": ml.HOW_SAMPLED, "busy_offset_s": -4.0,
                      "busy_overlap": False}, (e_long, e_stale, e_fresh))
check("O mutant (pick without the overlap rule) at_end on the long call: the reading before it, 99 s before the post, "
      "refused as stale, so the check above fails on it",
      m_pick.at_end(base, 100.0, 1000.0, late)["busy_servers_on_machine"] is None)
valid = R(100.5, 101.5)                                                # a successful reading inside the call
failed = ml.Reading(103.6, "not measured: the sampler's reading failed (TimeoutExpired: stub)")   # start 102.6 by convention
p_fail = ml.pick([valid, failed], 100.0, 106.0)                        # F3: the failure's middle 103.1 is nearer 103
p_fail_only = ml.pick([A, failed], 102.0, 104.0)                       # only the failure overlaps: it is used (None)
f_end = ml.at_end(base, 100.0, 106.0, sampler=Held([valid, failed]))
check("O O2 pick() (review F3): a failed reading overlapping the call does not hide a successful one that also "
      "overlapped (the call 100 to 106, a valid window 100.5 to 101.5, a failure at 103.6); a failure is chosen only "
      "when no successful reading overlapped",
      p_fail == (valid, True) and p_fail_only == (failed, True) and f_end["busy_servers_on_machine"] == 1
      and f_end["busy_overlap"] is True and f_end["busy_offset_s"] == 1.5,
      [(x[0].t, x[1]) for x in (p_fail, p_fail_only)] + [f_end])
m_fail = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_failed_wins",
                "    over = [r for r in over if r.busy is not None] or over\n", "")
check("O mutant (pick() letting a failed reading compete): the failure at 103.6 wins, so the check above fails on it",
      m_fail.pick([valid, failed], 100.0, 106.0) == (failed, True))


class Slow2:
    """A reading that answers at once the first time and takes 0.5 s after that."""

    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        if self.n > 1:
            time.sleep(0.5)
        return R(time.time() - 1, time.time())


fork_smp = ml.Sampler(read=Slow2(), every=100.0)
fork_smp.latest(2.0)
had = len(fork_smp.readings())
fork_smp._pid = -1                                        # as a forked child sees it: another process's sampler
fork_smp.start()
after_fork = len(fork_smp._history)
check("O the sampler keeps HISTORY readings; a forked child starts with none of its parent's",
      fork_smp._history.maxlen == ml.HISTORY == 4096 and had == 1 and after_fork == 0, (had, after_fork))

# ---------------------------------------------------------------- S: a sampler that stalls
release = threading.Event()                              # set at the end: the hung readings' threads return


class Hang:
    """A reading that answers `answers` times, then hangs (a PowerShell that stopped answering)."""

    def __init__(self, answers: int):
        self.answers, self.n = answers, 0

    def __call__(self):
        self.n += 1
        if self.n > self.answers:
            release.wait()
        return ml.Reading(time.time(), ml.HOW_SAMPLED, busy=[(1, 100), (2, 200)], ports={100: {STUB_PORT}, 200: {11999}},
                          servers={100, 200})


_real_max = ml.MAX_AGE_S
ml.MAX_AGE_S = 0.6
h = Hang(1)
smp_h = ml.Sampler(read=h, every=0.2)
smp_h.latest(5.0)
t_f = time.time()
fresh = ml.at_end(base, t_f, t_f + 0.01, smp_h)
time.sleep(0.9)
t_s = time.time()
stale = ml.at_end(base, t_s, t_s + 0.01, smp_h)
m_age = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_no_age_limit",
               "    if not overlap and t_post - r.t > MAX_AGE_S:\n", "    if False:\n")
m_age.MAX_AGE_S = 0.6
m_stale = m_age.at_end(base, t_s, t_s + 0.01, smp_h)
ml.MAX_AGE_S = _real_max
check("S a reading that answers once and then hangs: the count while it is fresh (1), then None with its offset once "
      "it ended more than MAX_AGE_S (0.6 s here) before the post, the reason naming the stalled sampler",
      fresh["busy_servers_on_machine"] == 1 and -0.6 < fresh["busy_offset_s"] <= 0
      and stale["busy_servers_on_machine"] is None and "s before the post, over 0.6 s" in stale["busy_how"]
      and "stalled" in stale["busy_how"] and stale["busy_offset_s"] < -0.6 and stale["busy_overlap"] is False,
      (fresh, stale))
check("S mutant (at_end without the age limit): the stale reading's count 1 is stored as if fresh, so the check above "
      "fails on it", m_stale["busy_servers_on_machine"] == 1 and m_stale["busy_offset_s"] < -0.6, m_stale)

never = Hang(0)
_b_sampler = ml.SAMPLER
ml.SAMPLER = ml.Sampler(read=never, every=1.0, first_wait_s=0.6)
lat_f, recs_f = [], []
for i in range(3):
    t0 = time.time()
    n0 = len(Stub.posted)
    recs_f.append(oc.generate(base, call, "x"))
    lat_f.append(round(Stub.posted[n0] - t0, 3))
ml.SAMPLER = _b_sampler
m_rd = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_wait_each_call",
              "        SAMPLER.first()\n", "        SAMPLER.latest(SAMPLER.first_wait_s)\n")
m_rd.SAMPLER = m_rd.Sampler(read=Hang(0), every=1.0, first_wait_s=0.6)
lat_m2 = []
for i in range(2):
    t0 = time.time()
    m_rd.ready(base)
    lat_m2.append(round(time.time() - t0, 3))
check("S a reading that never comes: the process's first call waits the first wait (0.6 s here) before the gate, the "
      "next calls post at once; each records None, 'no reading yet'",
      0.5 <= lat_f[0] < 1.2 and max(lat_f[1:]) < 0.25
      and all(r["busy_servers_on_machine"] is None and "no reading yet" in r["busy_how"] for r in recs_f), lat_f)
check("S mutant (ready() waiting on every call until a reading lands, the old ready()): the second call waits too, so "
      "the check above fails on it", min(lat_m2) >= 0.5, lat_m2)

gd = Path(tempfile.mkdtemp(prefix="ml_group_"))
fake_ps = gd / "fakeps.sh"
fake_ps.write_text(f"#!/bin/bash\nsleep 60 &\necho $! > {gd}/child\nwait\n")
fake_ps.chmod(0o755)


def child_alive() -> bool:
    for _ in range(50):
        if (gd / "child").exists() and (gd / "child").read_text().strip():
            break
        time.sleep(0.05)
    pid = int((gd / "child").read_text())
    time.sleep(0.3)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    os.kill(pid, 9)                                      # the mutant's orphan: not left behind by this check
    return True


try:
    ml._run_bounded([str(fake_ps)], 0.5)
    timed = False
except subprocess.TimeoutExpired:
    timed = True
alive = child_alive()
(gd / "child").unlink()
try:
    subprocess.run([str(fake_ps)], capture_output=True, text=True, timeout=0.5)
except subprocess.TimeoutExpired:
    pass
alive_m = child_alive()
check("S a reading past its time limit: TimeoutExpired, and its whole process group is killed, its child too (on WSL "
      "the PowerShell started through the interop shim)", timed and not alive, (timed, alive))
check("S mutant (subprocess.run's timeout, the code before): the child is left running, so the check above fails on it",
      alive_m, alive_m)
lst, win = ml._WIN_SAMPLE.find("MSFT_NetTCPConnection"), ml._WIN_SAMPLE.find("Read-Ollama;")
check("S the Beelink's PowerShell reads the listeners before the window (the call returns as the window ends: 0.027 to "
      "0.030 s after it on the Beelink, 17 October, against 0.79 to 0.82 s with the listeners after), and each of its "
      "three CIM queries has a Windows-side limit (-OperationTimeoutSec)",
      0 <= lst < win and ml._WIN_SAMPLE.count("-OperationTimeoutSec $t") == 3
      and ml._WIN_SAMPLE.count("Get-CimInstance") == 3, (lst, win))

# ---------------------------------------------------------------- W: the sampler's reading on the Beelink
# Windows' lines as the sampler's PowerShell printed them on the Beelink on 17 October at about 22:30 (read-only; the
# runner's command line shortened): ollama.exe serve 32480 listening on 11434, its llama-server.exe 888; plus a second
# server 40000 on 11435 with its runner 40001, as A2's second server would show.
W1 = ('10396\t19052\t65937500\t"C:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\ollama app.exe" \r\n'
      '32480\t10396\t60560468750\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve\r\n'
      '888\t32480\t94402500000\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe '
      '--model x --port 59514 --host 127.0.0.1 -c 131072 -np 1\r\n'
      '40000\t1\t1000000\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve\r\n'
      '40001\t40000\t50000000\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe '
      '--model y --port 59600\r\n')
W2 = W1.replace("94402500000", "94407812500").replace("50000000\t", "60000000\t")      # 888 +0.53 s, 40001 +1.0 s
WL = "L\t32480\t11434\r\nL\t10396\t60477\r\nL\t40000\t11435\r\n"
_real_ws = ml._windows_sample
ml._windows_sample = lambda: WL + "---\r\n" + W1 + "---\r\n" + W2
rw = ml.reading_windows()
ml._windows_sample = lambda: W1 + "---\r\n" + W2
rw_short = ml.reading_windows()
ml._windows_sample = _real_ws
check("W the Beelink's reading (MSFT_NetTCPConnection's listeners, then Win32_Process with ParentProcessId): both runners busy, each with "
      "its server; a call to 11434 counts the other server's runner (1), a call to 11435 the first's (1); the app's "
      "listener is not a server; a reading without the listeners part: None with the reason",
      rw.busy == [(888, 32480), (40001, 40000)] and rw.ports == {32480: {11434}, 10396: {60477}, 40000: {11435}}
      and rw.servers == {32480, 40000} and ml.count_for(rw, 11434) == (1, ml.HOW_SAMPLED_WINDOWS)
      and ml.count_for(rw, 11435) == (1, ml.HOW_SAMPLED_WINDOWS) and ml.count_for(rw, 60477)[0] is None
      and rw_short.busy is None and "listeners" in rw_short.how, (rw, rw_short.how))
m_cnt = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_count_all",
               "    return len({server for _, server in r.busy if server not in own}), r.how\n",
               "    return len(r.busy), r.how\n")
check("W mutant (count_for counting the called server's own runner too): 2 on the Beelink reading, not 1, so the "
      "checks above fail on it", m_cnt.count_for(rw, 11434)[0] == 2)
# D90 O1 on the Beelink: the second server 40000 also runs bge-m3 (runner 40002), busy in the same window
BGE = ('40002\t40000\t7000000\tC:\\Users\\Valerio\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe '
       '--model z --port 59700\r\n')
ml._windows_sample = lambda: WL + "---\r\n" + W1 + BGE + "---\r\n" + W2 + BGE.replace("7000000", "9000000")
rw2 = ml.reading_windows()
ml._windows_sample = _real_ws
m_rn = mutant(ROOT / "experiments/runner/machine_load.py", "machine_load_runners_w",
              "    return len({server for _, server in r.busy if server not in own}), r.how\n",
              "    return sum(1 for _, server in r.busy if server not in own), r.how\n")
check("W D90 O1: the Beelink's second server running devstral and bge-m3, both busy: a call to 11434 counts 1 server "
      "(a mutant counting runners gives 2, so this check fails on it); the reading's window start is its end minus "
      "BUSY_WINDOW_S",
      sorted(rw2.busy) == [(888, 32480), (40001, 40000), (40002, 40000)]
      and ml.count_for(rw2, 11434) == (1, ml.HOW_SAMPLED_WINDOWS) and m_rn.count_for(rw2, 11434)[0] == 2
      and rw2.t0 == rw2.t - ml.BUSY_WINDOW_S, (rw2.busy, ml.count_for(rw2, 11434), m_rn.count_for(rw2, 11434)))

# ---------------------------------------------------------------- C
from backend.agents import lock_adapter as la  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="check_machine_load_"))
ctx = rc.RunContext(run_id="check-machine-load", arm="check", item_id="Q001", draw=1, thinking=None, base_url=base,
                    sink=tmp, allowed={GEN: "generator"})
with rc.run(ctx):
    la.generate(f"ollama::{GEN}", "x")
    la.chat(f"ollama::{GEN}", [{"role": "user", "content": "x"}])
lines = [json.loads(x) for x in (tmp / "calls.jsonl").read_text().splitlines()]
check("C the lock adapter's Ollama generate and chat write the sampler's count, how it was taken, its offset and "
      "whether it overlapped the call",
      len(lines) == 2 and all(x["busy_servers_on_machine"] == 1 and x["busy_how"] == ml.HOW_SAMPLED
                              and isinstance(x.get("busy_offset_s"), float) and isinstance(x.get("busy_overlap"), bool)
                              and "busy_age_s" not in x and x["provider"] == "ollama" for x in lines),
      [(x.get("busy_servers_on_machine"), x.get("busy_how"), x.get("busy_offset_s"), x.get("busy_overlap"))
       for x in lines])
ml.SAMPLER = _real_sampler

# ---------------------------------------------------------------- D
py = [p for d in ("experiments", "scripts") for p in (ROOT / d).rglob("*.py")
      if ".venv" not in p.parts and "recovered_harness" not in p.parts and "__pycache__" not in p.parts]
passing = sorted({f"{p.relative_to(ROOT)}: {m.group(1)}" for p in py
                  if p.name not in ("check_machine_load.py", "ollama_client.py")
                  for m in re.finditer(r"\b(?:generate|chat)\([^)]*\bbusy=([^,)]+)", p.read_text(errors="replace"))})
check("D every caller takes the sampler's path (D89 A1): the only busy= passed to the client is verifier_ports' "
      "branch for a client without MEASURE, which no client here is; the passage judge passes none",
      passing == ["experiments/runner/verifier_ports.py: b"], passing)
old_path = sorted({f"{p.relative_to(ROOT)}" for p in py
                   if p.name not in ("check_machine_load.py", "machine_load.py", "judge_passages.py", "verifier_ports.py")
                   and not p.name.startswith("check_")
                   and re.search(r"\b(?:machine_load\.measure|busy_here|busy_runners)\(", p.read_text(errors="replace"))})
check("D no module calls the window count (measure, busy_here, busy_runners) outside machine_load, the judge's own "
      "definition and verifier_ports' fallback", old_path == [], old_path)
runner = sorted({p.name for p in (ROOT / "experiments/runner").glob("*.py")
                 if not p.name.startswith("check_") and p.name != "ollama_client.py"
                 for ln in p.read_text().splitlines()
                 if re.search(r"/api/(chat|generate|embed)", ln) and re.search(r"_post\(|urlopen\(|Request\(", ln)})
check("D in experiments/runner only ollama_client posts a model request, apart from job.py's model load",
      runner == ["job.py"], runner)
JP = ROOT / "experiments/scorers/judge_passages.py"
jp = JP.read_text()
check("D the passage judge passes no busy= (its records carry the client's sampled reading, D89 A1); its busy_runners "
      "is still machine_load.busy_here's count", "busy=" not in jp.split("def judge_call", 1)[1].split("\ndef ", 1)[0]
      and "passages=passages)      # Q146: the client's sampler (D89 A1)" in jp
      and "    return machine_load.busy_here()[0]\n" in jp)
spec = importlib.util.spec_from_file_location("judge_passages_q146", JP)
jpm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jpm)
OLD_JUDGE = """    try:
        t0 = machine_load._runner_cpu()
        machine_load.time.sleep(machine_load.BUSY_WINDOW_S)
        t1 = machine_load._runner_cpu()
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return sum(1 for pid, s in t1.items() if s - t0.get(pid, s) >= machine_load.BUSY_CPU_S)
"""                                                      # the judge's code before this fix: ps only
m_jp = mutant(JP, "judge_passages_old", "    return machine_load.busy_here()[0]\n", OLD_JUDGE)


def beelink(fn, windows: str):
    """fn() on a machine like the Beelink: WSL's ps without the server or a runner, Windows' list as given."""
    ml._ps, ml.POWERSHELL, ml._windows_read = (lambda: WSL_PS), sys.executable, (lambda: windows)
    real_sleep, ml.time = ml.time, type("T", (), {"sleep": staticmethod(lambda s: None)})
    try:
        return fn()
    finally:
        ml._ps, ml.POWERSHELL, ml._windows_read, ml.time = _real_ps, _real_ps_exe, _real_wr, real_sleep


busy_win = beelink(jpm.busy_runners, WIN1 + "---\n" + WIN2)
none_win = beelink(jpm.busy_runners, WIN1.replace("ollama.exe serve", "x") + "---\n" + WIN2.replace("ollama.exe serve", "x"))
old_win = beelink(m_jp.busy_runners, WIN1 + "---\n" + WIN2)
check("D the passage judge on a Beelink-like machine: 1 (the busy llama-server.exe in Windows' list), and None, not 0, "
      "when neither list shows a server", busy_win == 1 and none_win is None, (busy_win, none_win))
check("D mutant (the judge's code before this fix, ps only): 0 there whatever ran, so the check above fails on it",
      old_win == 0, old_win)

# ---------------------------------------------------------------- E
check("E Go durations as GIN prints them",
      S.parse_duration("1h33m12s") == 5592 and S.parse_duration("2m6s") == 126
      and abs(S.parse_duration("11.422281458s") - 11.422281458) < 1e-9
      and abs(S.parse_duration("44.42875ms") - 0.04442875) < 1e-12
      and abs(S.parse_duration("186.667µs") - 186.667e-6) < 1e-12 and S.parse_duration("1m0s") == 60)
bad = []
for d in ("abc", "5x", "", "1.2"):
    try:
        S.parse_duration(d)
        bad.append(d)
    except ValueError:
        pass
check("E a string that is not a duration raises", bad == [], bad)
tz = timezone(timedelta(hours=2))
g = S.parse_gin('[GIN] 2026/10/16 - 00:05:50 | 200 | 11.422281458s |       127.0.0.1 | POST     "/api/chat"', tz)
want_end = datetime(2026, 10, 16, 0, 5, 50, tzinfo=tz).timestamp() + 0.5
check("E a [GIN] line: end at the logged second + 0.5, start = end - duration, a model request",
      g is not None and g["end"] == want_end and abs(g["start"] - (want_end - 11.422281458)) < 1e-6
      and g["status"] == 200 and S.is_model_request(g))
gl = S.parse_gin('[GIN] 2026/10/16 - 09:05:23 | 200 |        18m40s |       127.0.0.1 | POST     "/api/chat"', tz)
check("E a duration over a minute (Gin truncates it to the second) is taken as the logged value + 0.5 s, so the "
      "record of 1121.007 s (gpt-oss:20b high, seq 14, 16 Oct 08:46:42) is within the 1 s tolerance",
      gl["dur"] == 1120.5 and abs(gl["dur"] - 1121.007) <= S.TOL_DUR_S)
gv = S.parse_gin('[GIN] 2026/10/15 - 23:00:48 | 200 |    44.42875ms |       127.0.0.1 | GET      "/api/tags"', tz)
gs = S.parse_gin('[GIN] 2026/10/17 - 08:53:29 | 200 |    42.54225ms |       127.0.0.1 | POST     "/api/show"', tz)
check("E GET /api/tags and POST /api/show are not model requests; a server line is not a GIN line",
      not S.is_model_request(gv) and not S.is_model_request(gs)
      and S.parse_gin('time=2026-10-16T00:05:50 level=INFO msg="llama runner started"', tz) is None)
other = {p: (m, [x[0] for x in m]) for p, m in
         {1: S.merge([(0, 10)]), 2: S.merge([(5, 12), (11, 15)]), 3: S.merge([(20, 30)])}.items()}
lo = S.load_over(0, 20, other)
check("E load over [0, 20]: mean (10 + 10 + 0) / 20 = 1.0, most at once 2 (5 to 10), share 15/20",
      lo == {"other_ports_mean": 1.0, "other_ports_max": 2, "other_any_share": 0.75}, lo)
z = S.load_over(7, 7, other)
check("E a zero-length span is read at its instant (two ports busy at 7)",
      z == {"other_ports_mean": 2.0, "other_ports_max": 2, "other_any_share": 1.0}, z)
check("E merge joins overlapping intervals; overlap counts only inside the span",
      S.merge([(5, 12), (11, 15), (20, 21)]) == [(5, 15), (20, 21)]
      and S.overlap([(5, 15), (20, 21)], [5, 20], 14, 20.5) == 1.5)
t0 = 1_000_000.0
recs_m = [{"_t": t0, "wall_s": 10.0, "waited_for_server_s": 0.0},       # posts at t0+0.5, ends t0+10.5
          {"_t": t0 + 30, "wall_s": 4.0, "waited_for_server_s": 5.0},   # waited 5 s: ends t0+39.5
          {"_t": t0 + 60, "wall_s": 3.0},                                # no waited: any end from t0+61.5 on
          {"_t": t0 + 100, "wall_s": 2.0, "waited_for_server_s": 0.0},  # no line of its duration: unmatched
          {"_t": t0 + 200, "wall_s": None}]                              # never sent
gins_m = [{"end": t0 + 10.5, "dur": 4.0}, {"end": t0 + 11.0, "dur": 10.2},   # decoy (duration), the match
          {"end": t0 + 39.5, "dur": 4.1}, {"end": t0 + 75.0, "dur": 3.1},
          {"end": t0 + 102.5, "dur": 9.0}]
mm = S.match(recs_m, gins_m)
check("E matching: duration within 1 s and end within 2.5 s; waited_for_server_s shifts the end; without it any "
      "later end; no line of its duration or never sent: unmatched",
      mm == {0: 1, 1: 2, 2: 3}, mm)
two = S.match([{"_t": t0, "wall_s": 10.0, "waited_for_server_s": 0.0},
               {"_t": t0, "wall_s": 10.4, "waited_for_server_s": 0.0}], [{"end": t0 + 10.5, "dur": 10.0}])
check("E one log line goes to one record, the closer one", two == {0: 0}, two)
sp = S.g1_spans([{"job": "g1_rlm_5", "start": "2026-10-16T23:31:00Z"},
                 {"job": "g1_rlm_5", "start": "2026-10-16T23:31:00Z"},          # the archived copy
                 {"job": "g1_rlm_5", "start": "2026-10-17T09:51:00Z"},          # the restart
                 {"job": "g1_single_pass", "start": "2026-10-16T23:31:00Z"}],
                [{"job": "g1_rlm_5", "end": "2026-10-17T05:09:00Z"},
                 {"job": "g1_single_pass", "end": "2026-10-17T00:41:00Z"}], now=2e9)
check("E G1 spans: the archived copy counted once, the restart after the old end still running, each job its own "
      "end", [(j, e) for j, _, _, e in sp] == [("g1_rlm_5", True), ("g1_single_pass", True), ("g1_rlm_5", False)]
      and sp[2][2] == 2e9, sp)
u_t, u_l, u_p = S.unseen_from(t0 + 10000, {11451: [{"dur": 9960.5}, {"dur": 30.0}], 11452: [{"dur": 120.0}]})
check("E a request still running at the reading: the longest logged (9,960.5 s on 11451) sets the time after which a "
      "call can miss one", (u_t, u_l, u_p) == (t0 + 39.5, 9960.5, 11451) and S.unseen_from(5.0, {}) == (5.0, 0.0, None),
      (u_t, u_l, u_p))
check("E the port of a server URL", S.port_of("http://127.0.0.1:11453") == 11453
      and S.port_of("http://127.0.0.1:11453/") == 11453 and S.port_of(None) is None)

# ---------------------------------------------------------------- F
t = time.time()
real = ml.busy_runners()
check("F this machine's count, read from ps once (no model call): an integer, in about 1 s",
      isinstance(real, int) and real >= 0 and 0.9 < time.time() - t < 15, f"{real} in {time.time() - t:.2f} s")
smp = ml.Sampler(every=1.0)
t = time.time()
r_first = smp.latest(30.0)
time.sleep(2.5)
r_now = smp.latest()
ports = sorted({p for v in (r_now.ports or {}).values() for p in v})
port = 11434 if 11434 in ports else (ports[0] if ports else 11434)
n, how = ml.count_for(r_now, port)
check("F this machine's sampler (real ps and lsof, no model call): a first reading in about 1 s, a newer one 2.5 s "
      "later, each runner matched to a server; the count for a port a server here listens on is an integer, how the "
      "sampled reading's; the window's start read 1 to 3 s before its end", r_first is not None
      and r_now.t > r_first.t and r_now.busy is not None and r_now.t0 is not None
      and ml.BUSY_WINDOW_S <= r_now.t - r_now.t0 < 3 and (not ports or (isinstance(n, int) and how == ml.HOW_SAMPLED)),
      f"first in {r_first.t - t:.2f} s, busy {r_now.busy}, ports {r_now.ports}, port {port}: {n}")

release.set()
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
