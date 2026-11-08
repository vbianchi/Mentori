"""How busy the machine was when a local model call ran: LOCK.toml [record] busy_servers_on_machine (D83 Q146).

    ready(base_url)                          # before the server gate: the sampler's first reading, waited for once
    fields = at_end(base_url, t_post, t_end) # after the call: the reading that overlapped it, no wait (D90 O2)

D90 (Valerio, 17 October, night) changes three things in what D89 A1 built; the D89 text below is kept as the history.
O1: the count is of busy SERVERS, not runners. A server is busy when at least one of its runners' CPU time grew by
>= BUSY_CPU_S in the window; a K1 server that holds devstral and bge-m3 runs them as two runners and counts once.
count_for() groups the busy runners by the server that started them (their parent process; a runner whose parent is
not a listed server still counts once per parent). Q1: busy_servers_on_machine is how many OTHER servers were busy:
the called server is left out even when another client keeps it busy, since its runners cannot be told apart by
client. O2: the sampler still reads in the background every SAMPLE_EVERY_S seconds, now keeping its readings
(HISTORY of them), and each call is given, at its end, the reading whose window overlapped the call (from the post to
the last byte read); when several did (a call longer than the period), the one whose window's middle is nearest the
call's middle; when none did (a call shorter than the gap between two windows, or a reading still running at the
call's end, which is not waited for), the latest reading that ended before the post. The record carries
busy_offset_s, the seconds from the post to the end of that reading's window (negative: it ended before the post;
positive: during or after the call), and busy_overlap (true when the window overlapped the call). busy_age_s, which
records written before D90 carry, was the seconds from the latest reading's end to the post, that is
-busy_offset_s with busy_overlap false; it is no longer written, so a record's field names say which rule made it.
A stale reading is refused as before: with no overlap, a reading that ended more than MAX_AGE_S before the post
gives None, with its offset and the reason (an overlapping reading is fresh by definition). A reading's window runs
from Reading.t0 to Reading.t: on macOS and Linux t0 is read as the first ps returns; on the Beelink the window runs
inside one PowerShell call whose start WSL does not see, so t0 is taken as t - BUSY_WINDOW_S.

D89 A1 (Valerio, 17 October): the reading is taken by a sampler running beside the calls, not by a 1 s window inside
the server gate before each call (that wait cost K1 1.55 s of about 3.5 s per call on the Beelink, 1.2 s on the
Studio). SAMPLER is one daemon thread per client process (started by the first call, started again in a forked child),
which every SAMPLE_EVERY_S seconds takes one reading of the machine (reading() below, the same quantity as before: model
runners whose CPU time grew by >= BUSY_CPU_S in a BUSY_WINDOW_S window), each runner with the Ollama server that started
it (its parent process) and each server with the ports it listens on. A call takes the latest reading as it is posted
and records the count, how it was taken (busy_how) and the reading's age (busy_age_s: seconds from the moment the
reading returned, just after its window ended, to the moment the request is posted). A reading older than MAX_AGE_S
(the sampler stalled: a hung PowerShell, a dead thread) is not used: the count is None with its age as the reason. Q146's meaning is kept: the window used to run inside the gate,
so the called server's runner was idle in it and the count was the other runners' work; a reading taken beside the
calls can hold the called server's own call, so count_for() leaves out every runner of the server that listens on the
called port. The count is None, with the reason, when the reading failed, when no Ollama server of the reading listens
on the called port (its runners could not be told apart), or when the server is on another machine. The only wait is
ready()'s, before the gate: the calls wait for the first reading until FIRST_WAIT_S after the sampler started in this
process, and never again after that (a reading that never comes costs the process FIRST_WAIT_S once, not per call).

The runner-to-server match: ps's parent pid of each runner (llama-server, or "ollama runner") is its `ollama serve`
(read 17 October on the Studio, 11 servers, and the laptop) and lsof -c ollama lists each server's listening ports
(the Studio: 11 servers in 0.01 s). On the Beelink, Win32_Process's ParentProcessId (llama-server.exe 888 under
ollama.exe serve 32480, read 17 October) and the listeners of MSFT_NetTCPConnection, the class Get-NetTCPConnection
reads (32480 on 11434, the same two listeners by either, read 17 October), in the same PowerShell call as the two CPU
readings: the listeners first, then the window, so the call returns as the window ends. Each CIM query has a Windows-
side limit (-OperationTimeoutSec), and the PowerShell runs in its own process group, killed whole at the WSL-side limit.

busy_here(), busy_runners() and measure() below are the window count as it was (the passage judge's busy_runners() is
busy_here()'s count): no call path uses them since D89 A1; experiments/runner/verifier_ports.py keeps busy_runners
for a client without MEASURE, which no client in this repository is.

Before D89 A1:

    n, how = measure(base_url)        # inside ollama_client's server gate, just before the request is posted

The measure is the passage judge's (judge_passages.busy_runners as of 6f0a67a, lines 179-209), moved here
unchanged and now called by the judge too: the number of model runner processes on this machine (llama-server, or
"ollama runner") whose CPU time grew by at least BUSY_CPU_S in a window of BUSY_WINDOW_S. A difference of CPU time,
not ps %cpu, because macOS reports %cpu as a decaying average over up to a minute (man ps) and counted the runner
of the call that had just ended (113 of 113 judge calls on 16 October recorded 1).

ollama_client takes it inside the server gate (one call at a time per server across this machine's processes,
LOCK.toml [server] num_parallel 1), so the runner of the server being called is idle in the window and the count is
the other runners' work: other servers, and other models on the same server. The judge takes it before its call,
outside the gate, which is the same count when one process calls the server (the judge's case); where several
processes share a server through the gate (exp_01's verifier, exp_05's queues), only inside the gate does the window
exclude a sibling's call on the same server.

The count is of this machine. A server on another machine (the base URL's host is not an address of this machine)
is not measured: n is None and how says so. A failure to read the process list gives None too, with the reason.

Where ps shows no `ollama serve`, the runners are out of ps's sight and a ps count would be 0 whatever ran. The
Beelink is such a machine: its Ollama is the Windows app (ollama.exe under
/mnt/c/Users/Valerio/AppData/Local/Programs/Ollama), whose processes WSL's ps does not list (read 17 October). There
the same count is taken from Windows' own process list, read from WSL with POWERSHELL (Win32_Process: each process's
command line and its kernel plus user CPU time, in 100 ns ticks), two readings BUSY_WINDOW_S apart in one PowerShell
call. The runners are llama-server.exe and `ollama.exe runner`; the server is `ollama.exe serve`. Read 17 October on
the Beelink: llama-server.exe 19024 at 15,189.4 CPU s, ollama.exe serve 32480, and `ollama app.exe` (the tray app,
neither). A machine with neither a visible server nor that process list gives None with the reason.

busy_here() is the count for this machine with how it was taken; measure(base_url) adds the check that the server is
on this machine. The passage judge's busy_runners() (judge_passages.py) is busy_here()'s count.
"""

from __future__ import annotations

import base64
import collections
import functools
import ipaddress
import os
import re
import signal
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

BUSY_WINDOW_S = 1.0          # judge_passages.py:179
BUSY_CPU_S = 0.1             # judge_passages.py:180
HOW = f"runners whose CPU time grew by >= {BUSY_CPU_S} s in {BUSY_WINDOW_S} s, inside the server gate"


def parse_cpu_seconds(t: str) -> float:
    """ps's cumulative CPU time: [[DD-]HH:]MM:SS[.ss] (macOS prints MMM:SS.ss, Linux [DD-]HH:MM:SS)."""
    days, _, hms = t.rpartition("-")
    s = 0.0
    for part in hms.split(":"):
        s = s * 60 + float(part)
    return s + 86400 * int(days or 0)


def runners_from_ps(text: str) -> dict[int, float]:
    """CPU seconds of each model runner in the output of `ps -axo pid=,time=,command=` (judge_passages._runner_cpu)."""
    cpu = {}
    for line in text.splitlines():
        pid, t, cmd = (line.strip().split(None, 2) + ["", ""])[:3]
        if "llama-server" in cmd or "ollama runner" in cmd:
            cpu[int(pid)] = parse_cpu_seconds(t)
    return cpu


def _ps() -> str:
    return subprocess.run(["ps", "-axo", "pid=,time=,command="], capture_output=True, text=True, timeout=10).stdout


def _runner_cpu() -> dict[int, float]:
    return runners_from_ps(_ps())


def server_visible(text: str) -> bool:
    """An `ollama serve` process in ps's output (macOS and Linux; not the Windows app seen from WSL)."""
    return any(ln.rstrip().endswith("ollama serve") or " ollama serve " in ln for ln in text.splitlines())


def busy_runners() -> int | None:
    """The judge's count (judge_passages.busy_runners): runners that used CPU in the window just before the call."""
    try:
        t0 = _runner_cpu()
        time.sleep(BUSY_WINDOW_S)
        t1 = _runner_cpu()
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return grown(t0, t1)


def grown(t0: dict[int, float], t1: dict[int, float]) -> int:
    """Runners whose CPU time grew by at least BUSY_CPU_S from t0 to t1 (one new in the window is not counted)."""
    return sum(1 for pid, s in t1.items() if s - t0.get(pid, s) >= BUSY_CPU_S)


# ---------------------------------------------------------------- Windows' process list, read from WSL (the Beelink)

POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
PS_TIMEOUT_S = 60.0          # the WSL-side limit on one PowerShell call (its process group is killed)
CIM_TIMEOUT_S = 15           # the Windows-side limit on each CIM query (-OperationTimeoutSec; PowerShell 5.1 there)
HOW_WINDOWS = (f"Windows runners (llama-server.exe, ollama.exe runner) read from WSL with PowerShell Win32_Process, "
               f"CPU time grew by >= {BUSY_CPU_S} s in {BUSY_WINDOW_S} s, inside the server gate")
# Two readings, BUSY_WINDOW_S apart, separated by a line "---". Each line: pid, CPU ticks (100 ns, an integer, so no
# locale's decimal comma), command line, tab-separated.
_WIN_READ = ("$q = \"Name LIKE 'llama-server%' OR Name LIKE 'ollama%'\"; "
             "function Read-Ollama { Get-CimInstance Win32_Process -Filter $q | ForEach-Object { "
             "[string]$_.ProcessId + \"`t\" + [string]($_.KernelModeTime + $_.UserModeTime) + \"`t\" + $_.CommandLine } }; "
             f"Read-Ollama; '---'; Start-Sleep -Milliseconds {int(BUSY_WINDOW_S * 1000)}; Read-Ollama")
_WIN_RUNNER = re.compile(r"llama-server(\.exe)?\b|ollama(\.exe)?\"?\s+runner\b", re.I)
_WIN_SERVE = re.compile(r"ollama(\.exe)?\"?\s+serve\b", re.I)


def windows_reading(text: str) -> tuple[bool, dict[int, float]]:
    """One reading of Windows' process list (lines pid TAB ticks TAB command line): (an ollama.exe serve is
    running, CPU seconds of each runner)."""
    serve, cpu = False, {}
    for line in text.splitlines():
        parts = line.rstrip("\r").split("\t", 2)
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        pid, ticks, cmd = parts
        if _WIN_SERVE.search(cmd):
            serve = True
        if _WIN_RUNNER.search(cmd):
            cpu[int(pid)] = int(ticks) / 1e7
    return serve, cpu


def _run_bounded(argv: list[str], timeout: float) -> str:
    """stdout of argv, run in its own process group; at the timeout the whole group is killed (subprocess.run kills
    only the direct child, which leaves its children running: review of 17 October, F4) and TimeoutExpired raised."""
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        return p.communicate(timeout=timeout)[0]
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.communicate()
        raise


def _windows_read() -> str:
    """Both readings, from one PowerShell call (its progress records go to stderr and are dropped)."""
    enc = base64.b64encode(_WIN_READ.encode("utf-16-le")).decode()
    return _run_bounded([POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", enc], PS_TIMEOUT_S)


def busy_windows() -> tuple[int | None, str]:
    """The count from Windows' process list. None, with the reason, when it cannot be read, does not hold two
    readings or shows no ollama.exe serve."""
    try:
        out = _windows_read()
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"not measured: Windows' process list could not be read from WSL ({type(e).__name__})"
    lines = out.splitlines()
    if sum(ln.strip() == "---" for ln in lines) != 1:
        return None, "not measured: Windows' process list read from WSL did not hold two readings"
    cut = [ln.strip() for ln in lines].index("---")
    first, second = "\n".join(lines[:cut]), "\n".join(lines[cut + 1:])
    try:
        (serve0, t0), (serve1, t1) = windows_reading(first), windows_reading(second)
    except ValueError:
        return None, "not measured: Windows' process list read from WSL could not be parsed"
    if not (serve0 or serve1):
        return None, "not measured: no ollama serve in ps or in Windows' process list"
    return grown(t0, t1), HOW_WINDOWS


def busy_here() -> tuple[int | None, str]:
    """(count, how) for this machine: ps where ps shows an ollama serve; else Windows' process list where WSL can read
    it (the Beelink); else None with the reason."""
    try:
        visible = server_visible(_ps())
    except (OSError, subprocess.SubprocessError):
        return None, "not measured: the process list could not be read"
    if visible:
        n = busy_runners()
        return (n, HOW) if n is not None else (None, "not measured: the process list could not be read")
    if os.path.exists(POWERSHELL):
        return busy_windows()
    return None, "not measured: ps shows no ollama serve here, and there is no Windows process list to read"


def is_this_machine(base_url: str) -> bool:
    """True when the base URL's host is a loopback address or an address of this machine (a socket can bind to it)."""
    host = urlsplit(base_url if "//" in base_url else f"//{base_url}").hostname or ""
    if host in ("localhost", "") or host == socket.gethostname():
        return True
    try:
        addrs = {ai[4][0] for ai in socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)}
    except OSError:
        return False
    for a in addrs:
        ip = ipaddress.ip_address(a.split("%")[0])
        if ip.is_loopback or ip.is_unspecified:
            return True
        fam = socket.AF_INET6 if ip.version == 6 else socket.AF_INET
        try:
            with socket.socket(fam, socket.SOCK_STREAM) as s:
                s.bind((a, 0))            # only an address of this machine can be bound
            return True
        except OSError:
            continue
    return False


def measure(base_url: str) -> tuple[int | None, str]:
    """(busy_servers_on_machine, how it was taken). None when the server is on another machine or the load could
    not be read (busy_here)."""
    if not is_this_machine(base_url):
        return None, f"not measured: {urlsplit(base_url).hostname} is not this machine"
    return busy_here()


# ---------------------------------------------------------------- D89 A1: the sampler beside the calls

SAMPLE_EVERY_S = 5.0         # D89 A1 "every few seconds": one reading every 5 s per client process
FIRST_WAIT_S = 30.0          # ready(): the calls wait for the first reading until this long after the sampler started
MAX_AGE_S = 2 * SAMPLE_EVERY_S   # at_end(): with no overlapping reading, one that ended longer than this before the
                                 # post is not used (one period late is tolerated; a Beelink reading takes about 2.3 s,
                                 # so a sampler on time has ended at most about 5 s before any post)
HISTORY = 4096               # readings each process keeps (D90 O2): about 5.7 h at SAMPLE_EVERY_S; a longer call is
                             # matched against the readings still held
_WHERE = (f"servers, the called one not counted (D90 O1, Q1); sampled beside the calls every {SAMPLE_EVERY_S:g} s "
          f"(D89 A1); the reading whose window overlapped the call (nearest its middle when several did), else the "
          f"latest before the post, attached at the call's end (D90 O2): its window's end in busy_offset_s from the "
          f"post, busy_overlap whether it overlapped")
HOW_SAMPLED = (f"Ollama servers with a runner whose CPU time grew by >= {BUSY_CPU_S} s in {BUSY_WINDOW_S} s (ps, lsof); "
               + _WHERE)
HOW_SAMPLED_WINDOWS = (f"Ollama servers with a runner (llama-server.exe, ollama.exe runner) whose CPU time grew by >= "
                       f"{BUSY_CPU_S} s in {BUSY_WINDOW_S} s, read from WSL with PowerShell Win32_Process and "
                       f"MSFT_NetTCPConnection; " + _WHERE)


@dataclass
class Reading:
    """One reading of the machine. busy: (runner pid, the pid of the server that started it) for each runner whose CPU
    time grew by >= BUSY_CPU_S in the window; None when the reading failed (how says why). ports: server pid -> the
    ports it listens on; None when they could not be read (why_ports says why). t: when the window ended, as this
    process saw it (the clock read just after the second process list: on macOS before lsof, on the Beelink as the
    PowerShell call returns, its listeners having been read before the window). t0: when the window started (on macOS
    as the first process list returned; on the Beelink not seen from WSL, so t - BUSY_WINDOW_S); None for a reading
    that failed, whose start is then taken as t - BUSY_WINDOW_S too (start)."""
    t: float
    how: str
    busy: list[tuple[int, int]] | None = None
    ports: dict[int, set[int]] | None = None
    why_ports: str | None = None
    servers: set[int] = field(default_factory=set)
    t0: float | None = None

    @property
    def start(self) -> float:
        return self.t0 if self.t0 is not None else self.t - BUSY_WINDOW_S


def ps_tree(text: str) -> tuple[dict[int, tuple[int, float]], set[int]]:
    """`ps -axo pid=,ppid=,time=,command=`: each runner's (ppid, CPU seconds), and the pids of the `ollama serve`
    processes."""
    runners, servers = {}, set()
    for line in text.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) < 4 or not (parts[0].isdigit() and parts[1].isdigit()):
            continue
        pid, ppid, t, cmd = int(parts[0]), int(parts[1]), parts[2], parts[3]
        if "llama-server" in cmd or "ollama runner" in cmd:
            runners[pid] = (ppid, parse_cpu_seconds(t))
        elif cmd.rstrip().endswith("ollama serve") or " ollama serve " in cmd:
            servers.add(pid)
    return runners, servers


def listeners_lsof(text: str) -> dict[int, set[int]]:
    """`lsof -nP -iTCP -sTCP:LISTEN -a -c ollama -Fpn`: pid -> listening ports (lines p<pid>, f<fd>, n<addr>:<port>)."""
    out: dict[int, set[int]] = {}
    pid = None
    for line in text.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = int(line[1:])
            out.setdefault(pid, set())
        elif line.startswith("n") and pid is not None:
            m = re.search(r":(\d+)$", line.strip())
            if m:
                out[pid].add(int(m[1]))
    return out


def busy_pairs(t0: dict[int, tuple[int, float]], t1: dict[int, tuple[int, float]]) -> list[tuple[int, int]]:
    """(runner, its server) for the runners whose CPU time grew by >= BUSY_CPU_S from t0 to t1 (as grown())."""
    return sorted((pid, ppid) for pid, (ppid, s) in t1.items() if s - t0.get(pid, (ppid, s))[1] >= BUSY_CPU_S)


def _ps_tree_text() -> str:
    return subprocess.run(["ps", "-axo", "pid=,ppid=,time=,command="], capture_output=True, text=True,
                          timeout=10).stdout


def _lsof_listen() -> str:
    p = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-a", "-c", "ollama", "-Fpn"], capture_output=True,
                       text=True, timeout=30)
    if p.returncode not in (0, 1) or (p.returncode == 1 and p.stderr.strip()):
        raise OSError(f"lsof exit {p.returncode}: {p.stderr.strip()[:120]}")
    return p.stdout


def reading_ps(sleep=time.sleep) -> Reading:
    """A reading where ps shows the servers (macOS, Linux): two ps readings BUSY_WINDOW_S apart, then the listeners."""
    try:
        r0, servers = ps_tree(_ps_tree_text())
        t0 = time.time()
        sleep(BUSY_WINDOW_S)
        r1, servers1 = ps_tree(_ps_tree_text())
    except (OSError, subprocess.SubprocessError, ValueError):
        return Reading(time.time(), "not measured: the process list could not be read")
    t = time.time()
    servers |= servers1
    try:
        ports, why = listeners_lsof(_lsof_listen()), None
    except (OSError, subprocess.SubprocessError) as e:
        ports, why = None, f"the servers' ports could not be read ({type(e).__name__}: {e})"
    return Reading(t, HOW_SAMPLED, busy_pairs(r0, r1), ports, why, servers, t0=t0)


# Windows (the Beelink, read from WSL): the listening ports of every ollama process ("L", pid, port; MSFT_NetTCPConnection
# State 2 is Listen), then two readings of Win32_Process (pid, parent pid, CPU ticks of 100 ns, command line,
# tab-separated) BUSY_WINDOW_S apart, the three parts separated by lines "---". The listeners come first so that the
# call returns as the window ends (review of 17 October, F2: read after the window they made the age 0.8 s too young).
_WIN_SAMPLE = (f"$t = {CIM_TIMEOUT_S}; "
               "$o = @(Get-CimInstance Win32_Process -Filter \"Name LIKE 'ollama%'\" -OperationTimeoutSec $t | "
               "ForEach-Object { $_.ProcessId }); "
               "Get-CimInstance -Namespace ROOT/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'State = 2' "
               "-OperationTimeoutSec $t | Where-Object { $o -contains $_.OwningProcess } | ForEach-Object { "
               "'L' + \"`t\" + [string]$_.OwningProcess + \"`t\" + [string]$_.LocalPort }; '---'; "
               "$q = \"Name LIKE 'llama-server%' OR Name LIKE 'ollama%'\"; "
               "function Read-Ollama { Get-CimInstance Win32_Process -Filter $q -OperationTimeoutSec $t | ForEach-Object { "
               "[string]$_.ProcessId + \"`t\" + [string]$_.ParentProcessId + \"`t\" + "
               "[string]($_.KernelModeTime + $_.UserModeTime) + \"`t\" + $_.CommandLine } }; "
               f"Read-Ollama; '---'; Start-Sleep -Milliseconds {int(BUSY_WINDOW_S * 1000)}; Read-Ollama")


def windows_tree(text: str) -> tuple[dict[int, tuple[int, float]], set[int]]:
    """One Win32_Process reading (pid TAB ppid TAB ticks TAB command line): each runner's (ppid, CPU seconds), and the
    pids of the ollama.exe serve processes."""
    runners, servers = {}, set()
    for line in text.splitlines():
        parts = line.rstrip("\r").split("\t", 3)
        if len(parts) < 4 or not (parts[0].strip().isdigit() and parts[1].strip().isdigit()):
            continue
        pid, ppid, ticks, cmd = int(parts[0]), int(parts[1]), parts[2], parts[3]
        if _WIN_SERVE.search(cmd):
            servers.add(pid)
        if _WIN_RUNNER.search(cmd):
            runners[pid] = (ppid, int(ticks) / 1e7)
    return runners, servers


def windows_listeners(text: str) -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    for line in text.splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 3 and parts[0] == "L" and parts[1].isdigit() and parts[2].isdigit():
            out.setdefault(int(parts[1]), set()).add(int(parts[2]))
    return out


def _windows_sample() -> str:
    enc = base64.b64encode(_WIN_SAMPLE.encode("utf-16-le")).decode()
    return _run_bounded([POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", enc], PS_TIMEOUT_S)


def reading_windows() -> Reading:
    """A reading from Windows' process list and listeners, read from WSL (the Beelink)."""
    try:
        out = _windows_sample()
    except (OSError, subprocess.SubprocessError) as e:
        return Reading(time.time(), f"not measured: Windows' process list could not be read from WSL ({type(e).__name__})")
    t = time.time()
    parts = re.split(r"^---\r?$", out, flags=re.M)
    if len(parts) != 3:
        return Reading(t, "not measured: Windows' process list read from WSL did not hold the listeners and two readings")
    try:
        (r0, s0), (r1, s1) = windows_tree(parts[1]), windows_tree(parts[2])
    except ValueError:
        return Reading(t, "not measured: Windows' process list read from WSL could not be parsed")
    if not (s0 or s1):
        return Reading(t, "not measured: no ollama serve in ps or in Windows' process list")
    ports = windows_listeners(parts[0])
    return Reading(t, HOW_SAMPLED_WINDOWS, busy_pairs(r0, r1), ports,
                   None if ports else "MSFT_NetTCPConnection listed no port of an ollama process", s0 | s1,
                   t0=t - BUSY_WINDOW_S)     # the window's start, inside the PowerShell call, is not seen from WSL


def reading() -> Reading:
    """One reading of this machine, as busy_here() chooses its list: ps where ps shows an ollama serve; else Windows'
    list where WSL can read it; else a reading that says why there is none."""
    try:
        visible = server_visible(_ps())
    except (OSError, subprocess.SubprocessError):
        return Reading(time.time(), "not measured: the process list could not be read")
    if visible:
        return reading_ps()
    if os.path.exists(POWERSHELL):
        return reading_windows()
    return Reading(time.time(), "not measured: ps shows no ollama serve here, and there is no Windows process list to read")


def count_for(r: Reading, port: int) -> tuple[int | None, str]:
    """The reading's count for a call to the server on this port (Q146's meaning, the module docstring): the servers
    with at least one busy runner (D90 O1: two busy runners of one server count once), leaving out the server that
    listens on the port, however busy it was and whoever kept it busy (D90 Q1)."""
    if r.busy is None:
        return None, r.how
    if r.ports is None:
        return None, f"not measured: {r.why_ports}"
    own = {pid for pid, ports in r.ports.items() if port in ports and (not r.servers or pid in r.servers)}
    if not own:
        return None, (f"not measured: no Ollama server of the reading listens on port {port}, so its runners cannot be "
                      f"told apart from the others")
    return len({server for _, server in r.busy if server not in own}), r.how


def pick(readings: list[Reading], t_post: float, t_end: float) -> tuple[Reading | None, bool]:
    """(the reading for a call posted at t_post that ended at t_end, whether its window overlapped the call) (D90 O2):
    of the readings whose window [start, t] overlaps [t_post, t_end], the one whose window's middle is nearest the
    call's middle (the earlier on a tie); when none overlaps, the latest that ended by the post; else (None, False).
    A failed reading (busy None) has no window of its own (start is t - BUSY_WINDOW_S by convention), so it is chosen
    among the overlapping readings only when no successful one overlapped (review of 17 October, F3: a failure at
    103.6 hid a valid reading over [100.5, 101.5] of a call from 100 to 106)."""
    over = [r for r in readings if r.start < t_end and r.t > t_post]
    over = [r for r in over if r.busy is not None] or over
    if over:
        mid = (t_post + t_end) / 2
        return min(over, key=lambda r: abs((r.start + r.t) / 2 - mid)), True
    before = [r for r in readings if r.t <= t_post]
    return (max(before, key=lambda r: r.t), False) if before else (None, False)


class Sampler:
    """One per client process (SAMPLER): a daemon thread taking a reading every `every` seconds and keeping the last
    HISTORY of them (D90 O2)."""

    def __init__(self, read=None, every: float = SAMPLE_EVERY_S, first_wait_s: float = FIRST_WAIT_S):
        self.read = read or reading
        self.every = every
        self.first_wait_s = first_wait_s
        self._latest: Reading | None = None
        self._history: collections.deque[Reading] = collections.deque(maxlen=HISTORY)
        self._cond = threading.Condition()
        self._thread: threading.Thread | None = None
        self._pid = None
        self._first_by: float | None = None      # monotonic deadline for the first reading in this process

    def start(self) -> None:
        with self._cond:
            if self._thread is not None and self._thread.is_alive() and self._pid == os.getpid():
                return
            if self._pid != os.getpid():
                self._latest = None              # a forked child: the parent's readings are not this process's
                self._history.clear()
                self._first_by = time.monotonic() + self.first_wait_s
            self._pid = os.getpid()
            self._thread = threading.Thread(target=self._loop, name="machine-load-sampler", daemon=True)
            self._thread.start()

    def _loop(self) -> None:
        while True:
            t0 = time.monotonic()
            try:
                r = self.read()
            except Exception as e:                # noqa: BLE001 - a failed reading is recorded, never raised in a call
                r = Reading(time.time(), f"not measured: the sampler's reading failed ({type(e).__name__}: {e})")
            with self._cond:
                self._latest = r
                self._history.append(r)
                self._cond.notify_all()
            time.sleep(max(0.0, self.every - (time.monotonic() - t0)))

    def readings(self) -> list[Reading]:
        """The readings this process's sampler has finished, oldest first (at most HISTORY), without waiting."""
        self.start()
        with self._cond:
            return list(self._history)

    def latest(self, wait_s: float = 0.0) -> Reading | None:
        """The latest reading; with wait_s, waits at most that long for the first one."""
        self.start()
        with self._cond:
            if self._latest is None and wait_s > 0:
                self._cond.wait_for(lambda: self._latest is not None, timeout=wait_s)
            return self._latest

    def first(self) -> Reading | None:
        """ready()'s wait: the latest reading, waiting for the first only until first_wait_s after the sampler started
        in this process (review of 17 October, F3: a reading that never comes cost every call the full wait)."""
        self.start()
        with self._cond:
            left = self._first_by - time.monotonic()
            if self._latest is None and left > 0:
                self._cond.wait_for(lambda: self._latest is not None, timeout=left)
            return self._latest


SAMPLER = Sampler()


@functools.lru_cache(maxsize=64)
def _here(base_url: str) -> bool:
    return is_this_machine(base_url)


def port_of(base_url: str) -> int:
    u = urlsplit(base_url if "//" in base_url else f"//{base_url}")
    return u.port or 11434


def ready(base_url: str) -> None:
    """Before the server gate: starts the sampler and waits for its first reading, until FIRST_WAIT_S after it started
    in this process; after that, never. A server on another machine needs no reading."""
    if _here(base_url):
        SAMPLER.first()


FIELDS = ("busy_servers_on_machine", "busy_how", "busy_offset_s", "busy_overlap")   # what at_end() gives a record


def at_end(base_url: str, t_post: float, t_end: float, sampler: Sampler | None = None) -> dict:
    """The record's FIELDS for a call to base_url posted at t_post that ended at t_end (time.time()), from the
    readings the sampler has finished, without waiting (D90 O2; after the call, so outside the server gate)."""
    def out(n, how, offset=None, overlap=None):
        return dict(zip(FIELDS, (n, how, offset, overlap)))
    if not _here(base_url):
        return out(None, f"not measured: {urlsplit(base_url).hostname} is not this machine")
    r, overlap = pick((sampler or SAMPLER).readings(), t_post, t_end)
    if r is None:
        return out(None, f"not measured: the sampler had no reading yet at the call's end (ready() waits "
                         f"{FIRST_WAIT_S:g} s for the first)")
    offset = round(r.t - t_post, 3)
    if not overlap and t_post - r.t > MAX_AGE_S:
        return out(None, (f"not measured: no reading overlapped the call, and the latest before it ended "
                          f"{t_post - r.t:.1f} s before the post, over {MAX_AGE_S:g} s (the sampler is stalled); that "
                          f"reading's how: {r.how}"), offset, False)
    n, how = count_for(r, port_of(base_url))
    return out(n, how, offset, overlap)
