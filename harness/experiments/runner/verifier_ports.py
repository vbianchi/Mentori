"""Q152 (D83): the timing test for Figure 3's verifier ports. Figure 3's checks (the verified-pass verifier,
gpt-oss:20b) stay on the Studio; before G4's verified pass starts, one verifier port is timed against two there,
while the Figure 6 reruns (S2) run, with the same 20 checks each way. The second port opens only if the two together
check more answers per hour. Every check records its port and the busy servers on the machine (Q146's field,
busy_servers_on_machine): where the client measures it itself (the Q146 build, ollama_client.MEASURE, inside the
server gate) it is left to the client; on a client without that build it is taken just before the call with the
passage judge's count (experiments/scorers/judge_passages.py busy_runners, the same measure). busy_source says which.

    uv run python -m experiments.runner.verifier_ports select --sink <G1 verified_pass sink> [--out <dir>] \\
        [--copy-of <the Studio path, when --sink is a copy>]
    uv run python -m experiments.runner.verifier_ports run --sink <same sink> [--out <dir>] \\
        [--first-port 11453] [--second-port 11456]
    uv run python -m experiments.runner.verifier_ports analyse [--out <dir>]

The checks. A check is one verifier call. The 20 are G1's own draw-1 verifier calls
(findings/runs/exp_01__verified_pass__exp_v4_s20_n0 on the Studio, 405 answers, done 17 Oct 05:54), chosen by a rule
that reads no timing: each draw-1 answer's last line whose verification status is ok, its verifier call found by
(ctx_uid, verification.call_seq), sorted by question id, positions floor(i * n / 20) for i = 0 to 19. select writes
the choice to <out>/checks.json (keys, request hashes and G1's own timings, no prompt). With --copy-of, select read a
copy of the sink: checks.json's "sink" is the --copy-of path (the one run and analyse are given on the Studio),
"read_from" the copy select read, and the hashes are the copy's; run refuses unless the sink it is given has the same
calls.jsonl. run reads each prompt from the
sink's calls.jsonl (prompt_sent), rebuilds the request with the lock (gpt-oss:20b, role generator, the call's draw and
thinking) and refuses unless the request's sha256 equals the one G1 recorded, so both arms send G1's exact bytes.

run, in order:
  1. Refuses if no S2 (exp_05) process runs, if the first port has another user (the guard below), if anything listens
     on the second port, or if <out>/results.jsonl exists (move it away to run again).
  2. Arm "one": fresh load of gpt-oss:20b on the first port (experiments/runner/job.py; the server check included),
     then the 20 checks in checks.json order through one worker on that port. After the first call returns, job.py's
     after-first-call check; a failure stops the arm.
  3. Starts a server on the second port with the lock's [server] settings (OLLAMA_NUM_PARALLEL, FLASH_ATTENTION,
     KV_CACHE_TYPE, KEEP_ALIVE, the binary the lock pins for macos, the same model store as 11453), log
     ~/ollama_logs/serve_<port>.log, and waits for it to answer.
  4. Arm "two": fresh load on both ports, then the same 20 checks from one shared queue in the same order, one worker
     per port (each takes the next check when its call ends), after-first-call checked per port.
  5. Stops the server it started (SIGTERM to its process group, which start_new_session made its own, so its runner
     goes too; SIGKILL to the group after 60 s), unless --keep-second. SIGTERM and SIGINT (a kill, Ctrl-C) are
     caught: run.json records the signal and the arm in progress, and the server is stopped the same way. SIGHUP (a
     dropped ssh session) is caught the same way only when it was not ignored at start; started under nohup it is
     ignored, and stays ignored, so a dropped session does not end the run. SIGKILL cannot be caught; a server left
     on the second port then makes the next run refuse.
  Each worker sends one call at a time to its own port, so no call waits on the client's per-server gate, and a busy
  count taken just before the call (a 1 s window) describes the machine at that call's start either way.

The guard (review F1). A fresh load unloads every model of its server, so another job on 11453 (K1's scorers are
proposed there once G1 ends, findings/recompute/K1/run_k1_studio.sh) would lose its models, and would share the GPU
with the arm it overlaps. Before the start, before every fresh load and before every call, each port of the arm is
surveyed with experiments/runner/server_users.py survey (fail closed: whatever cannot be read is a user): a model in
the port's /api/ps other than the verifier (the lock's gpt-oss:20b-date20261010, which G1 leaves loaded for 24 h), an
established connection to the port that is not this process's own (the server's end of this process's own call is
told apart by its peer address), a process naming the port as a word, or a process matching JOB_PATTERN (exp_01,
exp_02, K1 and the scorers, wherever they point). A busy survey is repeated after CONFIRM_S, and only a second busy
one counts (a call of this process opening between lsof's reads of the two ends can look like a stranger's once). A
busy guard refuses the start, or stops the arm before the call it guards. Every survey is a line of <out>/guard.jsonl.
What it cannot see: a job between two calls with no model of its own loaded, no open connection and a command line
that names neither the port nor JOB_PATTERN; and a request that begins and ends between two surveys.

Each check is one line of <out>/results.jsonl: the client's whole record (ollama_client.generate: options, status,
tokens, wall_s, load_s, prompt_eval_s, eval_s, busy_servers_on_machine, text) plus arm, port, the check's position,
item_id, draw, the replayed request's sha256 match, t_start and t_end (epoch seconds) and the reply's sha256.
<out>/run.json keeps the commit, the lock's sha256, the ports, the start and end of each arm, the S2 variants running
at each arm's start and end, and any refusal.

analyse (no model call) reads results.jsonl and writes <out>/report.json and <out>/REPORT.md. Before any new number it
reproduces a known one: the sum of G1's wall_s and output tokens over the 20 checks, recomputed from the sink, must equal
what select stored. Per arm: checks ending ok, the arm's span (first call's start to last call's end), checks per hour
= ok checks / span * 3,600, per-check wall_s and eval tokens per second, output tokens, seconds per 1,000 output tokens,
busy_servers_on_machine (median and range) per port. The decision is the card's rule as written: open the second port
only if arm two's checks per hour exceed arm one's. Beside it, stated and not used by the rule: how far the arms' loads
and output tokens differ, and how many replies are byte-identical between the arms (the same seed on the same weights).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.runner import server_users  # noqa: E402
from experiments.runner.lock import load  # noqa: E402

N_CHECKS = 20
VERIFIER = "gpt-oss:20b"              # exp_01 VERIFY_MODEL without the provider; the lock maps it to the date copy
VERIFIER_SITE = "backend/retrieval/chunk_verifier.py"
OUT = ROOT / "findings/recompute/Q152_verifier_ports"
BINARY = Path("/opt/homebrew/opt/ollama/bin/ollama")     # the Studio's keg binary, as launch_g1.sh and 11453 run
LOG_DIR = Path.home() / "ollama_logs"
MODELS_DIR = Path.home() / ".ollama/models"               # 11453's OLLAMA_MODELS
S2_PATTERN = "exp_05_coder_benchmark.py"                 # the Figure 6 reruns the card says the test runs beside
# jobs that may use 11453 without naming it: G1 and G2 (exp_01), Figure 3 (exp_02), K1 (its launchers and every
# scorer it starts read K1/assignment.json; RAGAS takes its port from MENTORI_OLLAMA_BASE), and the scorers anywhere
JOB_PATTERN = (r"exp_01_generation\.py|exp_02_scaling_factorial\.py|exp_02_scaling_generate_rlm\.py|"
               r"K1/assignment\.json|run_k1_|k1_lib\.sh|ragchecker_run\.py|S357_ragas\.py|judge_passages")
CONFIRM_S = 2.0                                          # a busy survey is repeated once after this
STOP_WAIT_S = 60                                         # SIGTERM to the second server's group, then SIGKILL
ABORT = threading.Event()                                # set by a caught signal: the workers send no new call


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode() if isinstance(b, str) else b).hexdigest()


def jsonl(path: Path):
    with path.open() as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


# ── select ───────────────────────────────────────────────────────────────────────────────────────────────────────

def choose(answers: list[dict], calls: list[dict], n: int = N_CHECKS) -> list[dict]:
    """The rule: draw-1 answers (a key's last line), verification status ok, their verifier call by (ctx_uid,
    call_seq), sorted by question id, positions floor(i * len / n). Reads no timing."""
    last: dict[str, dict] = {}
    for a in answers:
        last[a["answer_key"]] = a
    by_ctx = {(c.get("ctx_uid"), c.get("seq")): c for c in calls
              if str(c.get("call_site", "")).startswith(VERIFIER_SITE)}
    pool = []
    for a in last.values():
        ver = (a.get("generation") or {}).get("verification") or {}
        if a.get("draw") != 1 or ver.get("status") != "ok":
            continue
        c = by_ctx.get((a.get("ctx_uid"), ver.get("call_seq")))
        if c is None or c.get("status") != "ok":
            continue
        pool.append((a["question_id"], a, c))
    pool.sort(key=lambda t: t[0])
    if len(pool) < n:
        raise SystemExit(f"only {len(pool)} draw-1 verifier calls with status ok; the test needs {n}")
    picked = [pool[(i * len(pool)) // n] for i in range(n)]
    return [{"position": i, "question_id": q, "answer_key": a["answer_key"], "ctx_uid": c["ctx_uid"],
             "seq": c["seq"], "draw": c["draw"], "thinking": c.get("thinking"), "candidate": c.get("candidate"),
             "request_sha256": c["request_sha256"], "prompt_chars": len(c["prompt_sent"]),
             "g1": {k: c.get(k) for k in ("server", "prompt_tokens", "output_tokens", "wall_s", "prompt_eval_s",
                                          "eval_s", "waited_for_server_s", "at")},
             "g1_reply_sha256": sha(c.get("text") or "")}
            for i, (q, a, c) in enumerate(picked)]


def cmd_select(a) -> int:
    sink = Path(a.sink)
    answers, calls = list(jsonl(sink / "answers.jsonl")), list(jsonl(sink / "calls.jsonl"))
    checks = choose(answers, calls)
    copy_of = getattr(a, "copy_of", None)
    out = {"what": "Q152 (D83): the 20 verifier checks both arms send",
           "rule": "draw-1 answers (a key's last line) with verification status ok; their verifier call by "
                   "(ctx_uid, verification.call_seq); sorted by question id; positions floor(i * n / 20)",
           "sink": copy_of or str(sink), "read_from": str(sink.resolve())}
    if copy_of:
        out["copy_note"] = (f"select read a copy of {copy_of} at read_from; the hashes below are the copy's, and run "
                            "refuses unless the sink it is given has a calls.jsonl with calls_sha256")
    out |= {"run_id": calls[0].get("run_id") if calls else None,
           "calls_sha256": sha((sink / "calls.jsonl").read_bytes()),
           "answers_sha256": sha((sink / "answers.jsonl").read_bytes()),
           "made_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script": "experiments/runner/verifier_ports.py select",
           "g1_wall_s_sum": round(sum(c["g1"]["wall_s"] for c in checks), 3),
           "g1_output_tokens_sum": sum(c["g1"]["output_tokens"] for c in checks),
           "checks": checks}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "checks.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(checks)} checks written to {Path(a.out) / 'checks.json'}; G1 wall_s sum {out['g1_wall_s_sum']}, "
          f"output tokens {out['g1_output_tokens_sum']}")
    return 0


# ── run ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def replay_calls(manifest: dict, sink: Path, lock) -> list[tuple[dict, object, str]]:
    """(check, OllamaCall, prompt) for each check, refusing unless the rebuilt request is G1's exact bytes."""
    want = {(c["ctx_uid"], c["seq"]): c for c in manifest["checks"]}
    prompts = {}
    for r in jsonl(sink / "calls.jsonl"):
        k = (r.get("ctx_uid"), r.get("seq"))
        if k in want:
            prompts[k] = r["prompt_sent"]
    out = []
    for c in manifest["checks"]:
        k = (c["ctx_uid"], c["seq"])
        if k not in prompts:
            raise SystemExit(f"refused: check {c['position']} ({c['answer_key']}) is not in {sink}/calls.jsonl")
        call = lock.ollama(VERIFIER, role="generator", draw=int(c["draw"]), thinking=c["thinking"],
                           candidate=c["candidate"])
        got = sha(json.dumps(call.payload(prompts[k])).encode())
        if got != c["request_sha256"]:
            raise SystemExit(f"refused: check {c['position']} ({c['answer_key']}) rebuilds to request {got[:12]}, "
                             f"G1 sent {c['request_sha256'][:12]}")
        out.append((c, call, prompts[k]))
    return out


def s2_running(ps_text: str | None = None) -> list[str]:
    """The S2 (Figure 6) model processes running now: their --model and --base-url, one per variant."""
    if ps_text is None:
        ps_text = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, timeout=30).stdout
    out = []
    for line in ps_text.splitlines():
        if S2_PATTERN in line and "uv run" not in line:
            words = line.split()
            pick = lambda f: words[words.index(f) + 1] if f in words[:-1] else "?"      # noqa: E731
            out.append(f"{pick('--model')} {pick('--thinking')} {pick('--base-url')}")
    return sorted(out)


def others(port: int, verifier_model: str, runner=None, get=None, me: int | None = None,
           platform: str | None = None) -> dict:
    """One survey of the port by server_users.survey (fail closed), with JOB_PATTERN, where the verifier's model in
    /api/ps and the server's end of this process's own connections are not users (module docstring, the guard).
    runner, get, me and platform are canned by the checks, as server_users.survey's."""
    texts: dict[str, str] = {}
    run = runner or server_users.run

    def capture(cmd):
        rc, text, err = run(cmd)
        texts[cmd[0]] = text
        return rc, text, err

    me = os.getpid() if me is None else me
    kw = {"me": me, "runner": capture}
    if get is not None:
        kw["get"] = get
    if platform is not None:
        kw["platform"] = platform
    s = server_users.survey(f"http://127.0.0.1:{port}", [], None, JOB_PATTERN, False, **kw)
    rows = [(int(m[1]), int(m[2]), m[3]) for m in
            (re.match(r"\s*(\d+)\s+(\d+)\s+(.*)$", ln) for ln in texts.get("ps", "").splitlines()) if m]
    own = server_users.own_pids(rows, me)
    own_ends = set()                                 # this process's own client ends: "127.0.0.1:50001"
    for ln in texts.get("lsof", "").splitlines()[1:]:
        f = ln.split()
        if len(f) >= 9 and "(ESTABLISHED)" in ln and f[1].isdigit() and int(f[1]) in own and "->" in f[8]:
            own_ends.add(f[8].split("->")[0])
    conns = [c for c in s["connections"]
             if not ("->" in c.get("name", "") and c["name"].split("->")[1] in own_ends)]
    loaded = [u for u in s["loaded"] if u["model"] != verifier_model]
    users = {"processes": s["processes"], "connections": conns, "loaded": loaded, "unreadable": s["unreadable"]}
    return {"port": port, "at": s["at"], "busy": any(users.values()), **users,
            "verifier_loaded": [u["model"] for u in s["loaded"] if u["model"] == verifier_model],
            "own_connections_not_counted": len(s["connections"]) - len(conns)}


def guard_port(port: int, verifier_model: str, confirm_s: float = CONFIRM_S, **kw) -> dict:
    """The guard on one port: a busy survey is repeated after confirm_s, and the second one decides."""
    first = others(port, verifier_model, **kw)
    if not first["busy"]:
        return first
    time.sleep(confirm_s)
    second = others(port, verifier_model, **kw)
    second["first_survey"] = first
    return second


def preconditions(first: int, second: int, out: Path, verifier_model: str, confirm_s: float = CONFIRM_S,
                  **kw) -> tuple[list[str], dict]:
    """The reasons not to start (an empty list: start), and the first port's survey. kw: others()'s canned
    runner, get, me and platform (the checks)."""
    why = []
    if (out / "results.jsonl").exists():
        why.append(f"{out}/results.jsonl exists; move it away to run again")
    run = kw.get("runner") or server_users.run
    try:
        rc, ps, err = run(["ps", "-eo", "pid=,ppid=,args="])
        if rc != 0:
            raise OSError(err.strip() or f"exit {rc}")
    except (OSError, subprocess.SubprocessError) as e:
        why.append(f"cannot read ps: {e}")
        ps = ""
    if not s2_running(ps):
        why.append("no Figure 6 rerun (S2, exp_05) runs: the card times the ports while they run")
    g = guard_port(first, verifier_model, confirm_s, **kw)
    if g["busy"]:
        why.append(f"port {first} has another user: {server_users.summary(g)}")
    try:
        rc, lis, err = run(["lsof", "-nP", f"-iTCP:{second}", "-sTCP:LISTEN"])
        if rc not in (0, 1) or (rc == 1 and err.strip()):              # lsof: exit 1 and no output = none
            raise OSError(f"lsof exit {rc} {err.strip()[:200]}")
    except (OSError, subprocess.SubprocessError) as e:
        why.append(f"cannot read whether anything listens on port {second}: {e}")
        lis = ""
    if lis.strip():
        why.append(f"something listens on port {second}; this test starts its own server there (a server a killed "
                   f"run left: {out}/second_server.json names its pid)")
    return why, g


def server_env(port: int, lock) -> dict:
    """The lock's [server] settings as the server's environment, as 11453 runs (read 17 Oct: OLLAMA_HOST,
    NUM_PARALLEL, KEEP_ALIVE, KV_CACHE_TYPE, FLASH_ATTENTION, MODELS). check_server then reads them from the log."""
    s = lock.d["server"]
    return {"HOME": str(Path.home()), "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
            "OLLAMA_HOST": f"127.0.0.1:{port}", "OLLAMA_NUM_PARALLEL": str(s["num_parallel"]),
            "OLLAMA_KEEP_ALIVE": s["keep_alive"], "OLLAMA_KV_CACHE_TYPE": s["kv_cache_type"],
            "OLLAMA_FLASH_ATTENTION": "1" if s["flash_attention"] else "0", "OLLAMA_MODELS": str(MODELS_DIR)}


def start_server(port: int, lock, out: Path, started: dict) -> tuple[dict, subprocess.Popen]:
    """Starts BINARY serve on port in a session of its own; started["rec"] and started["proc"] are set as soon as
    it runs, so a signal caught while it comes up still stops it (cmd_run)."""
    LOG_DIR.mkdir(exist_ok=True)
    log = LOG_DIR / f"serve_{port}.log"
    fh = log.open("a")
    proc = subprocess.Popen([str(BINARY), "serve"], env=server_env(port, lock), stdout=fh, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    rec = {"port": port, "pid": proc.pid, "binary": str(BINARY), "log": str(log),
           "env": {k: v for k, v in server_env(port, lock).items() if k.startswith("OLLAMA_")},
           "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    started.update(rec=rec, proc=proc)
    (out / "second_server.json").write_text(json.dumps(rec, indent=1) + "\n")
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/version", timeout=5).read()
            rec["up_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            return rec, proc
        except OSError:
            if proc.poll() is not None:
                raise SystemExit(f"refused: the server on {port} exited ({proc.returncode}); see {log}")
            time.sleep(1)
    raise SystemExit(f"refused: the server on {port} did not answer within 60 s")


def descendants(pid: int, ps_text: str) -> list[int]:
    """Every process below pid in a `ps -eo pid=,ppid=` listing."""
    kids: dict[int, list[int]] = {}
    for ln in ps_text.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)", ln)
        if m:
            kids.setdefault(int(m[2]), []).append(int(m[1]))
    out, todo = [], [pid]
    while todo:
        for c in kids.get(todo.pop(), []):
            if c not in out:
                out.append(c)
                todo.append(c)
    return out


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def stop_server(rec: dict, proc: subprocess.Popen, wait_s: float = STOP_WAIT_S) -> None:
    """Stops the server this test started and everything it started (review F2): SIGTERM to its process group
    (start_new_session made the server the leader of a group of its own, so its runners are in it), never another
    group; SIGKILL to the group after wait_s; then SIGKILL to any process that was below the server before the stop
    and still runs wait_s later (a runner that left the group). Records the processes and what was left."""
    if proc.pid == os.getpgrp():
        raise RuntimeError(f"the server {proc.pid} leads this process's own group; not signalling it")

    def group(sig) -> None:
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass

    try:
        ps = subprocess.run(["ps", "-eo", "pid=,ppid="], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        ps = ""
    kids = descendants(proc.pid, ps)
    rec["descendants"] = kids
    group(signal.SIGTERM)
    try:
        proc.wait(timeout=wait_s)
    except subprocess.TimeoutExpired:
        group(signal.SIGKILL)
        rec["sigkill_group"] = True
        proc.wait(timeout=30)
    deadline = time.time() + wait_s
    while time.time() < deadline and any(alive(k) for k in kids):
        time.sleep(0.2)
    left = [k for k in kids if alive(k)]
    for k in left:
        try:
            os.kill(k, signal.SIGKILL)
        except ProcessLookupError:
            pass
    rec["left_after_stop"] = left
    rec["stopped_at"], rec["exit_code"] = time.strftime("%Y-%m-%dT%H:%M:%S"), proc.returncode


def run_arm(arm: str, ports: list[int], work: list, out: Path, busy, generate, fresh_load, after_first_call,
            log_of, guard) -> dict:
    """Fresh load on every port, then the checks in order from one queue, one worker per port. guard(port) is the
    guard's survey of a port (guard_port): before each port's fresh load that port, and before each call every port
    of the arm; a busy one stops the arm before the load or call it guards. Each survey is a line of guard.jsonl."""
    write = threading.Lock()

    def guarded(when: str, which: list[int]) -> str | None:
        for p in which:
            g = guard(p)
            with write:
                with (out / "guard.jsonl").open("a") as fh:
                    fh.write(json.dumps({"arm": arm, "when": when, **g}, ensure_ascii=False) + "\n")
            if g["busy"]:
                return f"port {p} has another user ({when}): {server_users.summary(g)}"
        return None

    loads = {}
    for p in ports:
        why = guarded(f"before the fresh load on {p}", [p])
        if why:
            return {"arm": arm, "ports": ports, "refused": why}
        base = f"http://127.0.0.1:{p}"
        rec = fresh_load(base, VERIFIER, log_of(p), BINARY, "macos")
        (out / f"fresh_load_{arm}_{p}.json").write_text(json.dumps(rec, indent=1) + "\n")
        if not rec.get("ok"):
            return {"arm": arm, "ports": ports, "refused": f"fresh load on {p} did not pass"}
        loads[p] = rec
    q: queue.Queue = queue.Queue()
    for item in work:
        q.put(item)
    stop = threading.Event()
    problems: list[str] = []

    def worker(p: int):
        try:
            work_port(p)
        except Exception as e:                               # a refusal (LockError: version, digest) or a crash
            problems.append(f"port {p}: {type(e).__name__}: {e}")
            stop.set()

    def work_port(p: int):
        base = f"http://127.0.0.1:{p}"
        first = True
        while not stop.is_set() and not ABORT.is_set():
            try:
                c, call, prompt = q.get_nowait()
            except queue.Empty:
                return
            g0 = time.time()
            why = guarded(f"before position {c['position']} on {p}", ports)
            if why:
                problems.append(why)
                stop.set()
                return
            guard_s = round(time.time() - g0, 3)
            if busy is None:                                 # the client measures it (Q146 build)
                t0 = time.time()
                rec = generate(base, call, prompt)
                src = "ollama_client (Q146)"
            else:
                b = busy()
                t0 = time.time()
                rec = generate(base, call, prompt, busy=b)
                src = "judge_passages.busy_runners before the call"
            t1 = time.time()
            rec.update(arm=arm, port=p, busy_source=src, position=c["position"], item_id=c["question_id"],
                       answer_key=c["answer_key"], draw=c["draw"], request_matches_g1=rec.get("request_sha256") ==
                       c["request_sha256"], t_start=round(t0, 3), t_end=round(t1, 3), guard_s=guard_s,
                       reply_sha256=sha(rec.get("text") or ""), reply_equals_g1=sha(rec.get("text") or "") ==
                       c["g1_reply_sha256"])
            with write:
                with (out / "results.jsonl").open("a") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if first:
                first = False
                try:
                    after_first_call(loads[p], log_of(p), BINARY, "macos", first=rec)
                except Exception as e:                       # job.SetupError: this port's runner is not certified
                    problems.append(f"after-first-call on {p}: {e}")
                    stop.set()
                finally:
                    (out / f"fresh_load_{arm}_{p}.json").write_text(json.dumps(loads[p], indent=1) + "\n")

    s2_at_start = s2_running()
    t_start = time.time()
    # daemon threads, joined in short waits: a caught signal is handled in this (the main) thread at once, and the
    # process can then end while a worker's call is still open (cmd_run stops the server under it)
    threads = [threading.Thread(target=worker, args=(p,), daemon=True) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        while t.is_alive():
            t.join(0.5)
    res = {"arm": arm, "ports": ports, "start": round(t_start, 3), "end": round(time.time(), 3),
           "s2_at_start": s2_at_start, "s2_at_end": s2_running()}
    if problems:
        res["refused"] = "; ".join(problems)
    return res


class Interrupted(Exception):
    """A caught SIGTERM, SIGINT or (when not ignored at start) SIGHUP (cmd_run)."""


def _interrupt(signum, frame):
    ABORT.set()
    raise Interrupted(signal.Signals(signum).name)


def busy_measure(oc):
    """None when the client measures busy_servers_on_machine itself (the Q146 build: oc.MEASURE exists), else the
    passage judge's busy_runners, which run_arm then calls just before each call and passes as busy=."""
    if hasattr(oc, "MEASURE"):
        return None
    from experiments.scorers.judge_passages import busy_runners
    return busy_runners


def cmd_run(a, deps: dict | None = None) -> int:
    """deps, set only by the checks: generate, fresh_load, after_first_call, busy, and survey (others()'s canned
    runner, get, me and platform, and confirm_s)."""
    if deps is None:
        from experiments.runner import ollama_client
        from experiments.runner.job import after_first_call, fresh_load
        deps = {"generate": ollama_client.generate, "fresh_load": fresh_load, "after_first_call": after_first_call,
                "busy": busy_measure(ollama_client), "survey": {}}
    out, sink = Path(a.out), Path(a.sink)
    lock = load()
    verifier_model = lock.ollama(VERIFIER, role="generator", draw=1, thinking="default").model
    manifest = json.loads((out / "checks.json").read_text())
    if sha((sink / "calls.jsonl").read_bytes()) != manifest["calls_sha256"]:
        raise SystemExit(f"refused: {sink}/calls.jsonl is not the file select read (calls_sha256 differs)")
    work = replay_calls(manifest, sink, lock)
    kw = dict(deps.get("survey") or {})
    confirm_s = kw.pop("confirm_s", CONFIRM_S)
    why, survey0 = preconditions(a.first_port, a.second_port, out, verifier_model, confirm_s, **kw)
    run = {"what": "Q152 (D83) verifier port timing test", "commit": subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "lock_sha256": lock.sha256, "first_port": a.first_port, "second_port": a.second_port, "sink": str(sink),
        "checks_sha256": sha((out / "checks.json").read_bytes()), "n_checks": len(work),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "start_survey": survey0, "arms": []}
    if why:
        run["refused"] = why
        (out / "run.json").write_text(json.dumps(run, indent=1) + "\n")
        print("refused:", *why, sep="\n  ")
        return 1
    log_of = lambda p: LOG_DIR / f"serve_{p}.log"     # noqa: E731
    save = lambda: (out / "run.json").write_text(json.dumps(run, indent=1) + "\n")   # noqa: E731
    guard = lambda p: guard_port(p, verifier_model, confirm_s, **kw)                 # noqa: E731
    arm_args = (deps["busy"], deps["generate"], deps["fresh_load"], deps["after_first_call"], log_of, guard)
    started: dict = {}
    rc = 1
    ABORT.clear()
    # SIGHUP ignored at start (nohup) stays ignored: a handler here would replace nohup's SIG_IGN, and a dropped ssh
    # session would then end the run (review of D83 wave B, Q152)
    caught = tuple(s for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
                   if not (s == signal.SIGHUP and signal.getsignal(s) == signal.SIG_IGN))
    old = {s: signal.signal(s, _interrupt) for s in caught}
    try:
        run["in_progress"] = "arm one"
        save()
        one = run_arm("one", [a.first_port], work, out, *arm_args)
        run["arms"].append(one)
        if one.get("refused"):
            print("refused:", one["refused"])
            return 1
        run["in_progress"] = "starting the second server"
        save()
        start_server(a.second_port, lock, out, started)
        run["in_progress"] = "arm two"
        save()
        two = run_arm("two", [a.first_port, a.second_port], work, out, *arm_args)
        run["arms"].append(two)
        run.pop("in_progress")
        if two.get("refused"):
            print("refused:", two["refused"])
            return 1
        rc = 0
    except Interrupted as e:
        run["interrupted"] = {"signal": str(e), "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "during": run.pop("in_progress", None)}
        print(f"interrupted by {e} during {run['interrupted']['during']}; stopping the second server; move "
              f"{out}/results.jsonl away before running again")
        return 1
    finally:
        for s in caught:                                  # no second signal cuts the stop short
            signal.signal(s, signal.SIG_IGN)
        run.pop("in_progress", None)                      # left in run.json only by a kill no handler sees
        try:
            if started.get("proc") is not None and not a.keep_second:
                stop_server(started["rec"], started["proc"])
                (out / "second_server.json").write_text(json.dumps(started["rec"], indent=1) + "\n")
            run["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            save()
        finally:
            for s, h in old.items():
                signal.signal(s, h)
    print(f"done: {sum(1 for _ in jsonl(out / 'results.jsonl'))} checks in {out / 'results.jsonl'}; "
          f"next: python -m experiments.runner.verifier_ports analyse --out {out}")
    return rc


# ── analyse ──────────────────────────────────────────────────────────────────────────────────────────────────────

def summarise(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("status") == "ok"]
    span = (max(r["t_end"] for r in rows) - min(r["t_start"] for r in rows)) if rows else 0.0
    out_tok = sum(r.get("output_tokens") or 0 for r in ok)
    rates = [r["output_tokens"] / r["eval_s"] for r in ok if r.get("eval_s") and r.get("output_tokens")]
    per_port = {}
    for p in sorted({r["port"] for r in rows}):
        pr = [r for r in rows if r["port"] == p]
        busy = [r["busy_servers_on_machine"] for r in pr if r.get("busy_servers_on_machine") is not None]
        per_port[str(p)] = {"checks": len(pr), "ok": sum(1 for r in pr if r.get("status") == "ok"),
                            "median_wall_s": round(statistics.median(r["wall_s"] for r in pr), 1),
                            "busy_median": statistics.median(busy) if busy else None,
                            "busy_range": [min(busy), max(busy)] if busy else None}
    busy_all = [r["busy_servers_on_machine"] for r in rows if r.get("busy_servers_on_machine") is not None]
    return {"checks": len(rows), "ok": len(ok),
            "status_counts": {s: sum(1 for r in rows if r.get("status") == s) for s in sorted({r.get("status")
                                                                                              for r in rows})},
            "span_s": round(span, 1),
            "checks_per_hour": round(len(ok) / span * 3600, 2) if span > 0 else None,
            "median_wall_s": round(statistics.median(r["wall_s"] for r in rows), 1) if rows else None,
            "median_eval_tokens_per_s": round(statistics.median(rates), 1) if rates else None,
            "output_tokens": out_tok,
            "s_per_1000_output_tokens": round(span / out_tok * 1000, 1) if out_tok else None,
            "busy_median": statistics.median(busy_all) if busy_all else None,
            "busy_range": [min(busy_all), max(busy_all)] if busy_all else None,
            "busy_missing": sum(1 for r in rows if r.get("busy_servers_on_machine") is None),
            "requests_match_g1": sum(1 for r in rows if r.get("request_matches_g1")),
            "per_port": per_port}


def decide(one: dict, two: dict, n: int = N_CHECKS) -> dict:
    """The card's rule: open the second port only if arm two checks more answers per hour than arm one. No decision
    when an arm did not end every check ok, since a rate over fewer checks is not the same 20 each way."""
    if one["ok"] != n or two["ok"] != n or one["requests_match_g1"] != n or two["requests_match_g1"] != n:
        return {"open_second_port": None,
                "why": f"no decision: arm one {one['ok']}/{n} ok, arm two {two['ok']}/{n} ok, requests matching G1 "
                       f"{one['requests_match_g1']} and {two['requests_match_g1']}; the rule needs the same {n} "
                       "checks ending ok each way"}
    yes = two["checks_per_hour"] > one["checks_per_hour"]
    return {"open_second_port": yes,
            "why": f"two ports {two['checks_per_hour']} checks per hour against one port {one['checks_per_hour']}: "
                   + ("more, so the second port opens" if yes else "not more, so Figure 3 keeps one port")}


def cmd_analyse(a) -> int:
    out = Path(a.out)
    manifest = json.loads((out / "checks.json").read_text())
    # reproduce before writing: G1's own sums over the 20, from the sink, must equal what select stored
    sink = Path(a.sink or manifest["sink"])
    if (sink / "calls.jsonl").exists():
        want = {(c["ctx_uid"], c["seq"]) for c in manifest["checks"]}
        g1 = [r for r in jsonl(sink / "calls.jsonl") if (r.get("ctx_uid"), r.get("seq")) in want]
        wall, toks = round(sum(r["wall_s"] for r in g1), 3), sum(r["output_tokens"] for r in g1)
        if (len(g1), wall, toks) != (len(want), manifest["g1_wall_s_sum"], manifest["g1_output_tokens_sum"]):
            raise SystemExit(f"refused: G1's sums from {sink} ({len(g1)} calls, {wall} s, {toks} tokens) are not the "
                             f"ones select stored ({manifest['g1_wall_s_sum']} s, {manifest['g1_output_tokens_sum']})")
        reproduced = f"G1 sums reproduced from {sink}: {len(g1)} calls, {wall} s, {toks} output tokens"
    else:
        raise SystemExit(f"refused: {sink}/calls.jsonl is not here; pass --sink to reproduce G1's sums first")
    if not (out / "results.jsonl").exists():
        raise SystemExit(f"refused: {out}/results.jsonl is not here; run comes first ({reproduced})")
    rows = list(jsonl(out / "results.jsonl"))
    arms = {arm: summarise([r for r in rows if r["arm"] == arm]) for arm in ("one", "two")}
    by_pos = {arm: {r["position"]: r for r in rows if r["arm"] == arm} for arm in arms}
    same = sum(1 for p, r in by_pos["one"].items() if p in by_pos["two"] and r["reply_sha256"] ==
               by_pos["two"][p]["reply_sha256"])
    d = decide(arms["one"], arms["two"])
    rep = {"what": "Q152 (D83): one verifier port against two, the same 20 checks each way",
           "made_by": "uv run python -m experiments.runner.verifier_ports analyse", "at": time.strftime(
               "%Y-%m-%dT%H:%M:%S"), "results_sha256": sha((out / "results.jsonl").read_bytes()),
           "checks_sha256": sha((out / "checks.json").read_bytes()), "reproduced": reproduced, "arms": arms,
           "replies_identical_between_arms": same, "decision": d,
           "beside_the_rule": {
               "output_tokens_two_over_one": round(arms["two"]["output_tokens"] / arms["one"]["output_tokens"], 3)
               if arms["one"]["output_tokens"] else None,
               "busy_median_one_two": [arms["one"]["busy_median"], arms["two"]["busy_median"]]}}
    (out / "report.json").write_text(json.dumps(rep, indent=1) + "\n")
    lines = [
        "# Q152: one verifier port against two",
        "",
        f"Made by `uv run python -m experiments.runner.verifier_ports analyse` at {rep['at']} from "
        f"`results.jsonl` (sha256 {rep['results_sha256'][:12]}) and `checks.json` ({rep['checks_sha256'][:12]}). "
        f"{reproduced}.",
        "",
        f"Decision (D83 Q152, the card's rule): {d['why']}.",
        "",
        "| arm | ports | checks ok | span s | checks per hour | median wall s | eval tokens/s | output tokens | "
        "s per 1,000 output tokens | busy servers, median (range) |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for arm, s in arms.items():
        lines.append(f"| {arm} | {', '.join(s['per_port'])} | {s['ok']} of {s['checks']} | {s['span_s']} | "
                     f"{s['checks_per_hour']} | {s['median_wall_s']} | {s['median_eval_tokens_per_s']} | "
                     f"{s['output_tokens']} | {s['s_per_1000_output_tokens']} | {s['busy_median']} "
                     f"({s['busy_range']}) |")
    lines += ["", "Per port:", ""]
    for arm, s in arms.items():
        for p, v in s["per_port"].items():
            lines.append(f"- arm {arm}, port {p}: {v['ok']} of {v['checks']} ok, median wall {v['median_wall_s']} s, "
                         f"busy servers median {v['busy_median']} (range {v['busy_range']})")
    lines += ["", "Beside the rule, not used by it:", "",
              f"- Output tokens, arm two over arm one: {rep['beside_the_rule']['output_tokens_two_over_one']} "
              "(the same seeded requests; a ratio far from 1 means the arms did different amounts of work).",
              f"- Busy servers, median, arm one and arm two: {rep['beside_the_rule']['busy_median_one_two']} "
              "(the arms ran at different times beside S2; the second port itself counts as busy in arm two).",
              f"- Replies byte-identical between the arms: {same} of {N_CHECKS}.",
              ""]
    (out / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--sink", required=True)
    s.add_argument("--out", default=str(OUT))
    s.add_argument("--copy-of", help="when --sink is a copy: the path of the sink it copies (the Studio's), which "
                   "checks.json then names as its sink; read_from keeps the copy's path")
    r = sub.add_parser("run")
    r.add_argument("--sink", required=True)
    r.add_argument("--out", default=str(OUT))
    r.add_argument("--first-port", type=int, default=11453)
    r.add_argument("--second-port", type=int, default=11456)
    r.add_argument("--keep-second", action="store_true", help="leave the second server running after the test")
    n = sub.add_parser("analyse")
    n.add_argument("--out", default=str(OUT))
    n.add_argument("--sink", help="the G1 sink, to reproduce G1's sums first (default: the one checks.json names)")
    a = ap.parse_args()
    return {"select": cmd_select, "run": cmd_run, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
