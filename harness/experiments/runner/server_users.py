"""K1 review F1 (17 October): does anyone but this launcher use an Ollama server? A fresh load (job.py fresh-load)
unloads every model the server holds, so a launcher runs this before each fresh load and refuses on any user it
cannot prove to be its own. On the Beelink one server (11434) serves every job, so a K1 start would otherwise
unload T3's olmo-3.1:32b-think, and a T3 load would unload K1's devstral.

    uv run --no-sync python -m experiments.runner.server_users survey --base http://127.0.0.1:<port> \\
        --own-models devstral-small-2:24b bge-m3:latest --ledger <dir>/own_<port>.json --begin-log <server log> \\
        [--job-pattern REGEX] [--windows-netstat]
    uv run --no-sync python -m experiments.runner.server_users loaded --base http://127.0.0.1:<port> \\
        --ledger <dir>/own_<port>.json --record <fresh-load record> --calls <the scorer's calls log>

survey: a user is any of
  loaded      a model in /api/ps that is not one of --own-models; or one of --own-models, unless the ledger proves
              that every model request the server has served since this launcher's last fresh load on it was this
              launcher's own (below). Without that proof (no ledger, a load that did not complete, a ledger for
              another server, a count that differs, anything unreadable) every loaded model is a user.
  connection  an established TCP connection with the port at either end: lsof on macOS, ss on Linux, and with
              --windows-netstat (the Beelink: Ollama runs on Windows and WSL uses mirrored networking) Windows'
              netstat.exe, which also sees clients on the Windows side.
  process     a process whose command line holds the port as a word (127.0.0.1:<port>, --base-url ...:<port>, a
              queue script's "<port>" argument), or matches --job-pattern (the Beelink's job scripts, which use the
              default port without naming it). An Ollama server or runner (ollama serve, llama-server) is not a user.
This process and its ancestors (the launcher that runs it) are never users. Whatever cannot be read (the server, lsof,
ss, netstat.exe, ps) makes the server busy: the guard fails closed. Prints one JSON object, then a FREE or BUSY line;
exit 0 free, 1 busy. With --begin-log, a free survey starts a new ledger (state "loading") whose log offset is the
log's size read before anything else, so a request that ends after that read is counted in the next proof.

The proof (K1 review F1, exact). Ollama's server log writes one [GIN] line per request when it ends: status, time,
client address, method, path (read on 17 October in the Beelink's server.log and the Studio's serve_11453.log; the
client address is 127.0.0.1 for every client, so the line cannot say whose a request was). A model request is a POST
to any path but NOT_A_MODEL (/api/show, /api/me, pulls, pushes, creates, copies, blobs, sign-in): /api/chat,
/api/generate, /api/embed, /api/embeddings, the /v1 endpoints and any path not listed. The proof holds when the
number of model requests in the log since the ledger's offset equals this launcher's own requests since then:
    the fresh load's      one unload per model it found loaded (its record's "unloaded") plus the load itself
                          (job.py fresh_load: these are its only POSTs; check_k1 runs fresh_load against a stub server)
    the scorer's          the lines its calls log gained since the load whose "server" is this server (one per request
                          ollama_client.chat or .embed sent; RAGChecker writes them directly, RAGAS through the lock
                          proxy; a record the proxy wrote without sending, client_gone or a refusal, has no "server")
A request by anyone else adds a line and no record, so the counts differ. A difference the other way (a record whose
request never reached the server, a connection refused) also fails the proof: the guard fails closed. A request still
running when the survey reads the log has no line yet: the log is read last, after the connections, so such a request
was already open when they were listed (or began after the listing, the race every check-then-act has; the fresh load
follows the survey at once).

loaded: after a fresh load that passed, the launcher records it in the ledger (the load record, its unloads, the
scorer's calls log and its line count now, before the scorer starts); state "scoring". The ledger file is keyed by the
server's port (K1 review F2), and holds the server's base, which the proof checks.

What the guard cannot see: a job between two calls whose model is not loaded and whose command line names neither the
port nor --job-pattern. Every call under the lock asks Ollama to keep its model loaded for 24 hours, so this needs a
model the server evicted. A model request by another client since this launcher's load, with no model of its own still
loaded and no process or connection seen, is recorded in the survey ("own_use") but does not by itself make the server
busy (the proof decides only whose the loaded devstral and bge-m3 are).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

NETSTAT = "/mnt/c/Windows/System32/netstat.exe"
SERVER_PROCESS = re.compile(r"(^|[/\\\s])(ollama(\.exe)?\s+(serve|runner)\b|llama-server(\.exe)?\s)")
# one request in Ollama's server log: [GIN] 2026/10/17 - 11:57:54 | 200 |    2.1628725s |       127.0.0.1 | POST     "/api/chat"
GIN = re.compile(r'\[GIN\][^|\n]*\|[^|\n]*\|[^|\n]*\|[^|\n]*\|\s*([A-Z]+)\s+"([^"?\n]*)(\?[^"\n]*)?"')
NOT_A_MODEL = {"/api/show", "/api/me", "/api/pull", "/api/push", "/api/create", "/api/copy", "/api/delete",
               "/api/signin", "/api/signout"}


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def norm(base: str | None) -> str:
    return (base or "").rstrip("/")


def own_pids(ps_rows: list[tuple[int, int, str]], me: int) -> set[int]:
    """This process and its ancestors."""
    parent = {pid: ppid for pid, ppid, _ in ps_rows}
    out, p = set(), me
    while p and p not in out:
        out.add(p)
        p = parent.get(p, 0)
    return out


def processes(port: int, pattern: str | None, ps_text: str, me: int) -> tuple[list[dict], set[int]]:
    rows = []
    for ln in ps_text.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)$", ln)
        if m:
            rows.append((int(m[1]), int(m[2]), m[3]))
    own = own_pids(rows, me)
    word = re.compile(rf"(?<![\w.]){port}(?!\w)")
    job = re.compile(pattern) if pattern else None
    users = []
    for pid, _, args in rows:
        if pid in own or SERVER_PROCESS.search(args):
            continue
        why = "names the port" if word.search(args) else "matches the job pattern" if job and job.search(args) else None
        if why:
            users.append({"pid": pid, "why": why, "args": args[:200]})
    return users, own


def connections_lsof(port: int, text: str, own: set[int]) -> list[dict]:
    out = []
    for ln in text.splitlines()[1:]:
        f = ln.split()
        if len(f) >= 9 and "(ESTABLISHED)" in ln and re.search(rf":{port}\b", f[8]) and int(f[1]) not in own:
            out.append({"tool": "lsof", "pid": int(f[1]), "command": f[0], "name": f[8]})
    return out


def connections_ss(port: int, text: str, own: set[int]) -> list[dict]:
    out = []
    for ln in text.splitlines():
        f = ln.split()
        ends = [x for x in f if re.search(r":\d+$", x)]
        if len(ends) < 2 or not any(x.endswith(f":{port}") for x in ends[:2]):
            continue
        pids = [int(x) for x in re.findall(r"pid=(\d+)", ln)]
        if pids and all(p in own for p in pids):
            continue
        out.append({"tool": "ss", "pids": pids, "local": ends[0], "peer": ends[1]})
    return out


def connections_netstat(port: int, text: str) -> list[dict]:
    out = []
    for ln in text.splitlines():
        f = ln.split()
        if len(f) >= 5 and f[0] == "TCP" and f[3] == "ESTABLISHED" and (
                f[1].endswith(f":{port}") or f[2].endswith(f":{port}")):
            out.append({"tool": "netstat.exe", "local": f[1], "peer": f[2], "windows_pid": f[4]})
    return out


def model_requests(log: Path, offset: int) -> int:
    """Model requests (module docstring) in the server log after byte offset. A last line still being written that
    holds [GIN] counts as one unless it reads whole as a request that is not a model's (fail closed)."""
    size = log.stat().st_size
    if size < offset:
        raise ValueError(f"{log} is {size} bytes, shorter than the ledger's offset {offset} (rotated or rewritten)")
    n = 0
    with log.open("rb") as fh:
        fh.seek(offset)
        for raw in fh:
            line = raw.decode("utf-8", "replace")
            m = GIN.search(line)
            if m:
                n += m[1] == "POST" and m[2] not in NOT_A_MODEL and not m[2].startswith("/api/blobs/")
            elif not raw.endswith(b"\n") and "[GIN]" in line:
                n += 1
    return n


def own_requests(ledger: dict, base: str) -> tuple[int, int]:
    """(the fresh load's model requests, the scorer's) since the ledger's offset (module docstring)."""
    rec = json.loads(Path(ledger["load_record"]).read_text())
    if norm(rec.get("base")) != norm(base):
        raise ValueError(f"the load record {ledger['load_record']} is for {rec.get('base')}, not {base}")
    if not isinstance(rec.get("unloaded"), list):
        raise ValueError(f"the load record {ledger['load_record']} lists no unloads")
    if rec.get("log_offset") is None or rec["log_offset"] < ledger["log_offset"]:
        raise ValueError("the load record's log offset precedes the ledger's: the load is not the one the ledger began")
    scorer = 0
    calls = Path(ledger["calls"])
    if calls.exists():
        with calls.open() as fh:
            for i, ln in enumerate(fh):
                if i >= ledger["calls_lines"] and ln.strip():
                    scorer += norm(json.loads(ln).get("server")) == norm(base)
    return len(rec["unloaded"]) + 1, scorer


def own_use(ledger_file: Path | None, base: str) -> dict:
    """The proof that every model request since this launcher's last fresh load on this server was its own."""
    if ledger_file is None or not ledger_file.exists():
        return {"proved": False, "why": "no ledger of this launcher's own use of this server (a first start)"}
    try:
        led = json.loads(ledger_file.read_text())
        if norm(led.get("base")) != norm(base):
            return {"proved": False, "why": f"the ledger {ledger_file} is for {led.get('base')}, not {base}"}
        if led.get("state") != "scoring":
            return {"proved": False, "why": f"this launcher's last fresh load on {base} did not complete "
                                            f"(ledger state {led.get('state')!r}, {led.get('at')})"}
        server = model_requests(Path(led["log"]), led["log_offset"])
        load_n, scorer_n = own_requests(led, base)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return {"proved": False, "why": f"the proof cannot be read: {type(e).__name__}: {e}"}
    out = {"since": led.get("at"), "server_log_model_requests": server, "own_load_requests": load_n,
           "own_scorer_requests": scorer_n, "proved": server == load_n + scorer_n}
    if not out["proved"]:
        out["why"] = (f"the server log holds {server} model requests since this launcher's fresh load of "
                      f"{led.get('at')}, this launcher sent {load_n + scorer_n} ({load_n} load, {scorer_n} scorer)")
    return out


def loaded_users(models: list[dict], own_models: list[str], proof: dict) -> list[dict]:
    users = []
    for m in models:
        name = m.get("name") or m.get("model")
        if name in own_models and proof["proved"]:
            continue
        why = "not one of this launcher's models" if name not in own_models else proof["why"]
        users.append({"model": name, "why": why, "expires_at": m.get("expires_at"),
                      "unload": f"curl -s {{base}}/api/generate -d '{{\"model\": \"{name}\", \"keep_alive\": 0}}'"})
    return users


def write_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1) + "\n")
    tmp.replace(path)


def survey(base: str, own_models: list[str], ledger: Path | None, pattern: str | None, windows_netstat: bool,
           begin_log: Path | None = None, runner=run, get=None, me: int | None = None,
           platform: str = sys.platform) -> dict:
    """Every user of the server at base that is not this process or its ancestors. runner, get, me and platform are
    set by the checks (experiments/scorers/check_k1.py) to canned listings."""
    base = norm(base)
    port = int(base.rsplit(":", 1)[1])
    me = os.getpid() if me is None else me
    out = {"base": base, "port": port, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "processes": [], "connections": [],
           "loaded": [], "unreadable": []}
    begin_offset = None
    if begin_log is not None:                                   # first, so a request ending after it is counted later
        try:
            begin_offset = begin_log.stat().st_size
        except OSError as e:
            out["unreadable"].append(f"{begin_log}: {e}")
    try:
        rc, text, err = runner(["ps", "-eo", "pid=,ppid=,args="])
        if rc != 0:
            raise OSError(err.strip() or f"exit {rc}")
        out["processes"], own = processes(port, pattern, text, me)
    except (OSError, subprocess.SubprocessError) as e:
        out["unreadable"].append(f"ps: {e}")
        own = {me}
    tools = [("lsof", ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:ESTABLISHED"])] if platform == "darwin" else [
        ("ss", ["ss", "-Htnp", "state", "established", f"( sport = :{port} or dport = :{port} )"])]
    if windows_netstat:
        tools.append(("netstat.exe", [NETSTAT, "-ano", "-p", "TCP"]))
    for name, cmd in tools:
        if runner is run and not (shutil.which(cmd[0]) or Path(cmd[0]).exists()):
            out["unreadable"].append(f"{name}: not found")
            continue
        try:
            rc, text, err = runner(cmd)
        except (OSError, subprocess.SubprocessError) as e:
            out["unreadable"].append(f"{name}: {e}")
            continue
        if rc != 0 and not (name == "lsof" and rc == 1 and not err.strip()):     # lsof: exit 1, no output = none
            out["unreadable"].append(f"{name}: exit {rc} {err.strip()[:200]}")
            continue
        out["connections"] += (connections_lsof(port, text, own) if name == "lsof" else
                               connections_ss(port, text, own) if name == "ss" else connections_netstat(port, text))
    out["ledger"] = None if ledger is None else str(ledger)
    try:
        ps = get(f"{base}/api/ps") if get else json.loads(urllib.request.urlopen(f"{base}/api/ps", timeout=60).read())
        # the log last: a request that was not yet a line when it was read was still open when the connections were
        out["own_use"] = own_use(ledger, base)
        out["loaded"] = loaded_users(ps.get("models") or [], own_models, out["own_use"])
        for u in out["loaded"]:
            u["unload"] = u["unload"].replace("{base}", base)
    except Exception as e:                                          # noqa: BLE001 - fail closed, reason recorded
        out["unreadable"].append(f"/api/ps: {type(e).__name__}: {e}")
        out.setdefault("own_use", None)
    out["busy"] = bool(out["processes"] or out["connections"] or out["loaded"] or out["unreadable"])
    if begin_log is not None and not out["busy"]:
        if ledger is None:
            raise ValueError("--begin-log needs --ledger")
        write_json(ledger, {"state": "loading", "base": base, "port": port, "log": str(begin_log.resolve()),
                            "log_offset": begin_offset, "at": out["at"]})
        out["ledger_begun"] = {"log_offset": begin_offset}
    return out


def loaded(base: str, ledger: Path, record: Path, calls: Path) -> dict:
    """After a fresh load that passed: the ledger names the load and the scorer's calls log at its length now."""
    base = norm(base)
    led = json.loads(ledger.read_text())
    if led.get("state") != "loading" or norm(led.get("base")) != base:
        raise ValueError(f"{ledger}: no load begun on {base} (state {led.get('state')!r}, base {led.get('base')})")
    rec = json.loads(record.read_text())
    if rec.get("ok") is not True or norm(rec.get("base")) != base:
        raise ValueError(f"{record}: not a passed fresh load on {base}")
    if rec.get("log_offset") is None or rec["log_offset"] < led["log_offset"]:
        raise ValueError(f"{record}: its log offset precedes the ledger's (not the load this ledger began)")
    lines = sum(1 for _ in calls.open()) if calls.exists() else 0
    led.update(state="scoring", load_record=str(record.resolve()), unloaded=len(rec["unloaded"]), calls=str(calls.resolve()),
               calls_lines=lines, loaded_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    write_json(ledger, led)
    return led


def summary(out: dict) -> str:
    bits = [f"{u['model']} loaded ({u['why']})" for u in out["loaded"]]
    bits += [f"pid {u['pid']} {u['why']}: {u['args'][:80]}" for u in out["processes"]]
    bits += [f"{len(out['connections'])} open connection(s) to port {out['port']}"] if out["connections"] else []
    bits += [f"cannot read {x}" for x in out["unreadable"]]
    return "; ".join(bits) if bits else "free"


def main(argv: list[str] | None = None, **canned) -> int:
    """canned: survey()'s runner, get, me and platform, set only by the checks."""
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("survey")
    s.add_argument("--base", required=True)
    s.add_argument("--own-models", nargs="*", default=[])
    s.add_argument("--ledger", type=Path)
    s.add_argument("--begin-log", type=Path, help="the server's log: a free survey begins a new ledger at its size")
    s.add_argument("--job-pattern")
    s.add_argument("--windows-netstat", action="store_true")
    g = sub.add_parser("loaded")
    g.add_argument("--base", required=True)
    g.add_argument("--ledger", required=True, type=Path)
    g.add_argument("--record", required=True, type=Path)
    g.add_argument("--calls", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "loaded":
        try:
            led = loaded(a.base, a.ledger, a.record, a.calls)
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"REFUSED: {type(e).__name__}: {e}")
            return 1
        print(json.dumps(led))
        return 0
    if a.begin_log is not None and a.ledger is None:
        ap.error("--begin-log needs --ledger")
    out = survey(a.base, a.own_models, a.ledger, a.job_pattern, a.windows_netstat, begin_log=a.begin_log, **canned)
    print(json.dumps(out))
    print(("BUSY: " if out["busy"] else "FREE: ") + summary(out))
    return 1 if out["busy"] else 0


if __name__ == "__main__":
    sys.exit(main())
