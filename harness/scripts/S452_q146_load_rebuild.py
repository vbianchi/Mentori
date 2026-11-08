#!/usr/bin/env python3
"""S452, D83 Q146: the machine load of G1's and S2's past local model calls on the Studio, rebuilt from the Studio's
Ollama server logs and G1's start and end records. No model call; the Studio is only read (ssh: date, ls, ps, lsof,
grep, cat, jq; nothing is written there).

    uv run python scripts/S452_q146_load_rebuild.py [--host 10.15.212.253]

Why: every Ollama record before Q146 has busy_servers_on_machine null (COUNTERCHECKS.md:455-461; G1's 405 verifier
calls among them), so a time in Figure 2 (G1) or Figure 6 (S2) cannot be told apart from what else ran at that hour.

What is read:
- ~/ollama_logs/serve_<port>.log, every [GIN] line. A line is `[GIN] 2026/10/16 - 00:05:50 | 200 | 11.422281458s |
  127.0.0.1 | POST "/api/chat"`: the end of the request to the second (local time, truncated) and its duration. A model
  request is a POST to /api/chat, /api/generate, /api/embed or /api/embeddings; it occupies the port from end - duration
  to end. The end is taken as the logged second + 0.5 s, so every interval is known to +-0.5 s; a duration of a
  minute or more, which Gin truncates to the second, is taken as the logged value + 0.5 s (start +-1 s).
- The Ollama records (provider "ollama") of G1, ~/projects/mentori-runs/findings/runs/exp_01__<six
  configs>__exp_v4_s20_n0/calls.jsonl, and of S2 on the Studio, findings/runs/exp_05__*/calls.jsonl in the two S2
  clones ~/projects/mentori-runs-s2 and ~/projects/mentori-runs-s2-d75 (projected by jq on the Studio; a line still
  being written is skipped).
- G1's start and end records, ~/projects/mentori-runs/findings/recompute/G1_runs/g1_<config>.{start,end}.json and the
  copies archived before the Q141 restart (q141_before_restart_*/): which of the six strategies ran when. Their Gemini
  calls and in-process searches are in no server log; the number of G1 strategies running is their only trace.
- Every `ollama serve` running now: its port (lsof) and its log file; a server whose log is not
  ~/ollama_logs/serve_<port>.log has its model requests in the window counted, to state whether it carried load.

Each record is matched to its own [GIN] line on its port: duration within 1.0 s of the record's wall_s and end within
2.5 s of at + 0.5 + waited_for_server_s + wall_s (at is the record's start to the second); one line per record, best
first. For each call (its [GIN] interval, or the record's own estimate when unmatched) the script gives, over the
call's span: the time-averaged number of OTHER logged ports serving a model request (other_ports_mean), the most at
once (other_ports_max), the share of the span with at least one (other_any_share), the seconds another request on the
same port overlapped it (same_port_overlap_s; one request at a time, so 0 up to the 1 s resolution), the G1 strategies
whose span holds its start (g1_jobs_running; a G1 call's own strategy among them), the ports whose log begins after
the call started (load there unknown), and whether it can miss a request still running at the reading
(may_miss_running: it ends after the reading minus the longest model request logged).

Limits, stated in every output: Studio only (no laptop or Beelink load, so nothing for the S2 variants that ran on the
laptop); from 15 Oct 08:23 (the first logged line; the five logs begin at different times); no Gemini or Anthropic
load; no load outside an Ollama server (in-process encoders and rerankers, other programs); a server not running now
is not seen; intervals +-0.5 s; the count is of ports, not of models (two models on one port count once); a request
still running when the logs are read has no [GIN] line yet and is missing from the load of the calls it overlapped
(may_miss_running marks the calls that can be affected).

Gate (reproduce before writing): the first [GIN] line of serve_11441.log is in the minute 2026/10/15 - 08:23
(COUNTERCHECKS.md:459, Q146 card), G1 verified_pass holds 405 Ollama records (Q146 card, evidence), and every one of them has
busy_servers_on_machine null. Otherwise nothing is written.

Writes findings/recompute/Q146_load_rebuild/S452_calls_load.csv, S452_summary.json and S452_summary.md.
G1 and S2 are still running: run it again when they end; the outputs are replaced whole.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import re
import shlex
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "findings/recompute/Q146_load_rebuild"
G1_REPO = "~/projects/mentori-runs"
G1_CONFIGS = ["single_pass", "verified_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20"]
S2_CLONES = ["~/projects/mentori-runs-s2", "~/projects/mentori-runs-s2-d75"]
LOG_GLOB = "~/ollama_logs/serve_*.log"
MODEL_PATHS = {"/api/chat", "/api/generate", "/api/embed", "/api/embeddings"}
TOL_DUR_S, TOL_END_S = 1.0, 2.5
RESOLUTION_S = 1.0           # two intervals each known to +-0.5 s: an overlap up to 1 s can be two requests in one second
GATE_FIRST_11441 = "2026/10/15 - 08:23"       # to the minute, as COUNTERCHECKS.md:459 gives it
GATE_VERIFIED_PASS = 405
FIELDS = ["at", "wall_s", "waited_for_server_s", "first_token_s", "server", "model", "status", "seq", "pid",
          "run_id", "item_id", "draw", "busy_servers_on_machine"]

GIN = re.compile(r'^\[GIN\] (\d{4}/\d\d/\d\d - \d\d:\d\d:\d\d) \| *(\d{3}) \| *(\S+) \| *(\S+) \| *(\w+) +"([^"]*)"')
DUR = re.compile(r"([0-9.]+)(h|ms|µs|us|ns|m|s)")
UNIT = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 1e-3, "µs": 1e-6, "us": 1e-6, "ns": 1e-9}


# ---------------------------------------------------------------- pure functions (checked by experiments/runner/check_machine_load.py E)

def parse_duration(d: str) -> float:
    """A Go time.Duration as GIN prints it ("1h33m12s", "2m3.5s", "11.42s", "44.4ms", "186.667µs") in seconds."""
    parts = DUR.findall(d)
    if not parts or "".join(n + u for n, u in parts) != d:
        raise ValueError(f"not a duration: {d!r}")
    return sum(float(n) * UNIT[u] for n, u in parts)


def parse_gin(line: str, offset: timezone) -> dict | None:
    """One [GIN] line: end (epoch, the logged second + 0.5), duration, status, method, path. None if not a GIN line."""
    m = GIN.match(line)
    if not m:
        return None
    ts, status, dur, client, method, path = m.groups()
    end = datetime.strptime(ts, "%Y/%m/%d - %H:%M:%S").replace(tzinfo=offset).timestamp() + 0.5
    d = parse_duration(dur)
    if d >= 60:                  # Gin truncates a latency over a minute to the second ("18m40s" for 1121.0 s)
        d += 0.5
    return {"end": end, "start": end - d, "dur": d, "status": int(status), "method": method, "path": path,
            "client": client, "logged": ts}


def is_model_request(g: dict) -> bool:
    return g["method"] == "POST" and g["path"] in MODEL_PATHS


def local_epoch(at: str, offset: timezone) -> float:
    return datetime.strptime(at, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=offset).timestamp()


def merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def overlap(merged: list[tuple[float, float]], starts: list[float], s: float, e: float) -> float:
    """Seconds of [s, e] covered by merged (sorted, disjoint; starts = their start times)."""
    i = max(0, bisect.bisect_right(starts, s) - 1)
    tot = 0.0
    while i < len(merged) and merged[i][0] < e:
        tot += max(0.0, min(e, merged[i][1]) - max(s, merged[i][0]))
        i += 1
    return tot


def busy_at(merged: list[tuple[float, float]], starts: list[float], t: float) -> bool:
    """t inside one of merged's intervals (start inclusive, end exclusive)."""
    i = bisect.bisect_right(starts, t) - 1
    return i >= 0 and merged[i][1] > t


def load_over(s: float, e: float, other: dict[int, tuple[list, list]]) -> dict:
    """Over [s, e]: mean and max number of other ports busy, share of time with at least one. other: port ->
    (merged intervals, their starts). A span of zero length is read at the instant s."""
    if e <= s:
        n = sum(1 for merged, starts in other.values() if busy_at(merged, starts, s))
        return {"other_ports_mean": float(n), "other_ports_max": n, "other_any_share": float(n > 0)}
    span = e - s
    cuts, mean = {s, e}, 0.0
    for merged, starts in other.values():
        mean += overlap(merged, starts, s, e) / span
        i = max(0, bisect.bisect_right(starts, s) - 1)
        while i < len(merged) and merged[i][0] < e:
            cuts.update(x for x in merged[i] if s < x < e)
            i += 1
    pts = sorted(cuts)
    mx, any_t = 0, 0.0
    for a, b in zip(pts, pts[1:]):
        mid = (a + b) / 2
        n = sum(1 for merged, starts in other.values() if busy_at(merged, starts, mid))
        mx = max(mx, n)
        any_t += (b - a) if n else 0.0
    return {"other_ports_mean": round(mean, 3), "other_ports_max": mx, "other_any_share": round(any_t / span, 3)}


def match(records: list[dict], gins: list[dict]) -> dict[int, int]:
    """Record index -> GIN index on the same port: |dur - wall_s| <= TOL_DUR_S and the end within TOL_END_S of
    at + 0.5 + waited + wall_s (or, with no waited_for_server_s, no earlier than at + wall_s - TOL_END_S). Best pairs
    first, each line and record used once."""
    ends = [g["end"] for g in gins]
    pairs = []
    for ri, r in enumerate(records):
        if r.get("wall_s") is None:
            continue
        waited = r.get("waited_for_server_s")
        est = r["_t"] + 0.5 + (waited or 0.0) + r["wall_s"]
        lo, hi = (est - TOL_END_S, est + TOL_END_S) if waited is not None else (est - TOL_END_S, est + 86400)
        for gi in range(bisect.bisect_left(ends, lo), bisect.bisect_right(ends, hi)):
            dd = abs(gins[gi]["dur"] - r["wall_s"])
            if dd <= TOL_DUR_S:
                pairs.append((dd + abs(ends[gi] - est) / 10, ri, gi))
    used_r, used_g, out = set(), set(), {}
    for _, ri, gi in sorted(pairs):
        if ri not in used_r and gi not in used_g:
            out[ri] = gi
            used_r.add(ri)
            used_g.add(gi)
    return out


def g1_spans(starts: list[dict], ends: list[dict], now: float) -> list[tuple[str, float, float, bool]]:
    """(job, start, end, ended) per start record: its end is the first end record of the same job after it; none
    means still running at the time of reading (end = now)."""
    def t(x):
        return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()
    out = []
    for s in starts:
        t0 = t(s["start"])
        later = sorted(t(e["end"]) for e in ends if e["job"] == s["job"] and t(e["end"]) >= t0)
        out.append((s["job"], t0, later[0] if later else now, bool(later)))
    return sorted(set(out), key=lambda x: (x[1], x[0]))


def unseen_from(read_at: float, gins: dict[int, list[dict]]) -> tuple[float, float, int | None]:
    """A request still running when the logs are read has no [GIN] line yet, so it is missing from the load of every
    call it overlapped. Taking the longest model request logged on any port (seconds, port) as the longest one that
    can be running, such a request began after read_at - longest: (that time, longest, its port). A call that ends
    after it may miss one (may_miss_running)."""
    longest, port = 0.0, None
    for p, gl in gins.items():
        for g in gl:
            if g["dur"] > longest:
                longest, port = g["dur"], p
    return read_at - longest, longest, port


def port_of(server: str | None) -> int | None:
    m = re.search(r":(\d+)/?$", server or "")
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- reading the Studio (read-only)

def ssh(host: str, cmd: str) -> bytes:
    """One read-only command on the host, under /bin/sh (the login shell may be zsh, whose unmatched glob aborts)."""
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, "/bin/sh -c " + shlex.quote(cmd)],
                       capture_output=True, timeout=1800)
    if r.returncode not in (0, 1):            # grep exits 1 on no match
        raise SystemExit(f"ssh {host} {cmd[:80]!r} failed ({r.returncode}): {r.stderr.decode()[:300]}")
    return r.stdout


def jq_records(host: str, files: list[str]) -> list[dict]:
    keep = "{" + ", ".join(FIELDS) + ", provider, file: input_filename}"
    prog = f'fromjson? | select(.provider == "ollama") | {keep}'
    cmd = "jq -c -R " + shlex.quote(prog) + " " + " ".join(files)
    return [json.loads(x) for x in ssh(host, cmd).decode().splitlines() if x.strip()]


def remote_glob(host: str, pattern: str) -> list[str]:
    return [x for x in ssh(host, f"ls -1 {pattern} 2>/dev/null").decode().split() if x]


def servers_now(host: str) -> list[dict]:
    """Every `ollama serve` running on the host: pid, listening port, stdout file (lsof)."""
    out = []
    for line in ssh(host, "ps -axo pid=,command=").decode().splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if not cmd.strip().endswith("ollama serve"):
            continue
        lst = ssh(host, f"lsof -nP -a -p {pid} -iTCP -sTCP:LISTEN 2>/dev/null; echo ---; "
                        f"lsof -nP -a -p {pid} -d 1 2>/dev/null").decode()
        listen, _, fd1 = lst.partition("---")
        ports = [int(m) for m in re.findall(r":(\d+) \(LISTEN\)", listen)]
        logs = [ln.split()[-1] for ln in fd1.splitlines() if ln.split() and not ln.startswith("COMMAND")]
        out.append({"pid": int(pid), "port": ports[0] if ports else None, "log": logs[0] if logs else None})
    return out


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="10.15.212.253")
    a = ap.parse_args()
    read_at = time.time()
    z = ssh(a.host, "date +%z").decode().strip()                     # e.g. +0200
    offset = timezone(timedelta(hours=int(z[:3]), minutes=int(z[0] + z[3:])))
    home = ssh(a.host, "echo $HOME").decode().strip()

    # call records (read before the logs, so every record read has ended before its log line was read)
    g1_files = remote_glob(a.host, " ".join(f"{G1_REPO}/findings/runs/exp_01__{c}__exp_v4_s20_n0/calls.jsonl"
                                            for c in G1_CONFIGS))
    s2_files = remote_glob(a.host, " ".join(f"{c}/findings/runs/exp_05__*/calls.jsonl" for c in S2_CLONES))
    recs = []
    for exp, files in (("G1", g1_files), ("S2", s2_files)):
        for i in range(0, len(files), 40):
            for r in jq_records(a.host, files[i:i + 40]):
                r["exp"] = exp
                recs.append(r)
    vp = [r for r in recs if "/exp_01__verified_pass__" in r["file"]]
    if len(vp) != GATE_VERIFIED_PASS or any(r["busy_servers_on_machine"] is not None for r in vp):
        raise SystemExit(f"GATE FAILED: G1 verified_pass has {len(vp)} Ollama records "
                         f"({sum(r['busy_servers_on_machine'] is not None for r in vp)} with a load), not "
                         f"{GATE_VERIFIED_PASS} all null; nothing written")
    # server logs
    logs, gins, inputs = {}, {}, {}
    for f in remote_glob(a.host, LOG_GLOB):
        port = int(re.search(r"serve_(\d+)\.log$", f).group(1))
        raw = ssh(a.host, f"grep -a '^\\[GIN\\]' {shlex.quote(f)}")
        inputs[f] = {"gin_lines": raw.count(b"\n"), "sha256_of_gin_lines": hashlib.sha256(raw).hexdigest()}
        parsed = [g for g in (parse_gin(x, offset) for x in raw.decode("utf-8", "replace").splitlines()) if g]
        logs[port] = {"first": parsed[0]["logged"] if parsed else None, "first_t": parsed[0]["end"] - 0.5 if parsed
                      else None, "last": parsed[-1]["logged"] if parsed else None,
                      "model_requests": sum(map(is_model_request, parsed))}
        gins[port] = sorted((g for g in parsed if is_model_request(g)), key=lambda g: g["end"])
    window_start = min(v["first_t"] for v in logs.values() if v["first_t"] is not None)
    unseen_t, longest, longest_port = unseen_from(read_at, gins)

    # gate 1
    if not (logs.get(11441, {}).get("first") or "").startswith(GATE_FIRST_11441):
        raise SystemExit(f"GATE FAILED: serve_11441.log begins {logs.get(11441, {}).get('first')}, "
                         f"not {GATE_FIRST_11441}; nothing written")

    # servers whose log is elsewhere: model requests inside the window
    others = []
    for s in servers_now(a.host):
        if s["log"] and s["port"] and s["log"] != f"{home}/ollama_logs/serve_{s['port']}.log":
            raw = ssh(a.host, f"grep -a '^\\[GIN\\]' {shlex.quote(s['log'])}").decode("utf-8", "replace")
            ps = [g for g in (parse_gin(x, offset) for x in raw.splitlines()) if g and is_model_request(g)]
            inside = [g for g in ps if g["end"] >= window_start]
            others.append({**s, "model_requests_in_window": len(inside),
                           "last_model_request": ps[-1]["logged"] if ps else None})
        elif s["port"] not in logs:
            others.append({**s, "model_requests_in_window": None, "last_model_request": None,
                           "note": "no log file found"})

    for r in recs:
        r["_t"] = local_epoch(r["at"], offset)
        r["port"] = port_of(r["server"])

    # G1 start and end records
    def jsons(pattern):
        out = []
        for f in remote_glob(a.host, pattern):
            try:
                out.append(json.loads(ssh(a.host, f"cat {shlex.quote(f)}")))
            except ValueError:
                pass
        return out
    gdir = f"{G1_REPO}/findings/recompute/G1_runs"
    starts = jsons(f"{gdir}/g1_*.start.json {gdir}/q141_before_restart_*/g1_*.start.json")
    ends = jsons(f"{gdir}/g1_*.end.json {gdir}/q141_before_restart_*/g1_*.end.json")
    spans = g1_spans(starts, ends, read_at)

    # match, then load
    by_port = defaultdict(list)
    for i, r in enumerate(recs):
        by_port[r["port"]].append(i)
    merged = {p: merge([(g["start"], g["end"]) for g in gl]) for p, gl in gins.items()}
    idx = {p: (m, [x[0] for x in m]) for p, m in merged.items()}
    rows, unmatched_ports = [], defaultdict(int)
    for port, ris in by_port.items():
        sub = [recs[i] for i in ris]
        gl = gins.get(port, [])
        mm = match(sub, gl)
        for k, r in enumerate(sub):
            gi = mm.get(k)
            if gi is not None:
                s, e = gl[gi]["start"], gl[gi]["end"]
            elif r.get("wall_s") is not None:
                s = r["_t"] + 0.5 + (r.get("waited_for_server_s") or 0.0)
                e = s + r["wall_s"]
                unmatched_ports[port] += 1
            else:
                s = e = r["_t"]
            other = {p: v for p, v in idx.items() if p != port}
            ld = load_over(s, e, other)
            same = 0.0
            if gi is not None and port in gins:
                own = [(g["start"], g["end"]) for j, g in enumerate(gl) if j != gi and g["start"] < e and g["end"] > s]
                same = sum(min(e, b) - max(s, a2) for a2, b in own)
            rows.append({
                "exp": r["exp"], "run_id": r.get("run_id"), "file": r["file"].replace(home, "~"), "seq": r.get("seq"),
                "pid": r.get("pid"), "item_id": r.get("item_id"), "draw": r.get("draw"), "model": r.get("model"),
                "port": port, "status": r.get("status"), "at": r["at"], "wall_s": r.get("wall_s"),
                "span_s": round(e - s, 3),
                "matched": gi is not None,
                "start": datetime.fromtimestamp(s, offset).isoformat(timespec="seconds"),
                "end": datetime.fromtimestamp(e, offset).isoformat(timespec="seconds"),
                "gin_minus_wall_s": round(gl[gi]["dur"] - r["wall_s"], 3) if gi is not None else None,
                **ld, "same_port_overlap_s": round(same, 3),
                "g1_jobs_running": sum(1 for _, t0, t1, _e in spans if t0 <= s < t1),
                "ports_unknown": " ".join(str(p) for p, v in sorted(logs.items())
                                          if v["first_t"] is None or v["first_t"] > s) or "",
                "before_window": s < window_start,
                "may_miss_running": e > unseen_t,
                "busy_recorded": r.get("busy_servers_on_machine")})
    rows.sort(key=lambda x: (x["exp"], x["file"], x["seq"] or 0))

    # summary
    def summ(rs):
        if not rs:
            return {"calls": 0}
        mm = [x for x in rs if x["matched"]]
        means = [x["other_ports_mean"] for x in rs]
        return {"calls": len(rs), "matched": len(mm), "unmatched": len(rs) - len(mm),
                "before_window": sum(x["before_window"] for x in rs),
                "with_unknown_ports": sum(bool(x["ports_unknown"]) for x in rs),
                "other_ports_mean_median": round(statistics.median(means), 3),
                "other_ports_mean_min": min(means),
                "other_ports_mean_max": max(means),
                "other_ports_max_counts": dict(sorted(
                    {k: sum(1 for x in rs if x["other_ports_max"] == k) for k in {x["other_ports_max"] for x in rs}}
                    .items())),
                "share_with_any_other_busy_over_half": sum(x["other_any_share"] > 0.5 for x in rs),
                "same_port_overlap_calls": sum(x["same_port_overlap_s"] > RESOLUTION_S for x in rs),
                "may_miss_running": sum(x["may_miss_running"] for x in rs),
                "gin_minus_wall_s_median": (round(statistics.median(x["gin_minus_wall_s"] for x in mm), 3)
                                            if mm else None),
                "g1_jobs_running_counts": dict(sorted(
                    {k: sum(1 for x in rs if x["g1_jobs_running"] == k) for k in {x["g1_jobs_running"] for x in rs}}
                    .items()))}
    per_run = {}
    for x in rows:
        per_run.setdefault(x["run_id"] or x["file"], []).append(x)
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    prov = {"script": "scripts/S452_q146_load_rebuild.py", "command": "uv run python scripts/S452_q146_load_rebuild.py",
            "repo_head": git, "host": a.host, "read_at": datetime.fromtimestamp(read_at, offset).isoformat(
                timespec="seconds"), "studio_utc_offset": z, "inputs": inputs,
            "record_files": {"G1": [f.replace(home, "~") for f in g1_files], "S2": len(s2_files)}}
    limits = ["Studio only: no laptop or Beelink load, and nothing for the S2 variants that ran on the laptop",
              f"from {datetime.fromtimestamp(window_start, offset).isoformat(timespec='seconds')} (the first logged "
              "line); each log begins at its own time (log_coverage), and a call is marked with the ports whose log "
              "begins after it started (ports_unknown)",
              "no Gemini or Anthropic load: G1's Gemini calls and in-process searches show only as the number of G1 "
              "strategies running (g1_jobs_running: every G1 strategy whose span holds the call's start, so for a "
              "G1 call its own strategy is one of them)",
              "no load outside an Ollama server (in-process encoders and rerankers, other programs), and a server "
              "not running at the time of reading is not seen",
              "intervals +-0.5 s (the log gives the end to the second; a duration over a minute only to the second, "
              "so its start +-1 s), so the load of a call shorter than a few "
              "seconds is uncertain (span_s gives each call's length) and a same-port overlap up to "
              f"{RESOLUTION_S} s is two requests logged in one second; a call is matched to its log line by time and "
              f"duration only (duration within {TOL_DUR_S} s, end within {TOL_END_S} s)",
              "a count of ports, not of models: two models busy on one port count once",
              "a request still running when the logs were read has no [GIN] line yet, so it is missing from the load "
              "of every call it overlapped; the longest model request logged is "
              f"{longest:.0f} s (port {longest_port}), and if none still running is longer, the calls that end after "
              f"{datetime.fromtimestamp(unseen_t, offset).isoformat(timespec='seconds')} can be undercounted "
              "(may_miss_running); G1 and S2 were still running at the time of reading: run again when no request "
              "is running on any logged port"]
    summary = {"provenance": prov, "decision": "D83 Q146", "limits": limits,
               "gate": {"serve_11441_first_line": logs[11441]["first"], "g1_verified_pass_ollama_records": len(vp),
                        "all_null": True},
               "log_coverage": {str(p): {k: v[k] for k in ("first", "last", "model_requests")}
                                for p, v in sorted(logs.items())},
               "servers_logging_elsewhere": others,
               "g1_spans": [{"job": j, "start": datetime.fromtimestamp(t0, offset).isoformat(timespec="seconds"),
                             "end": datetime.fromtimestamp(t1, offset).isoformat(timespec="seconds"), "ended": ed}
                            for j, t0, t1, ed in spans],
               "records_by_port": {str(p): len(v) for p, v in sorted(by_port.items(), key=lambda kv: str(kv[0]))},
               "unmatched_by_port": {str(p): n for p, n in sorted(unmatched_ports.items(), key=lambda kv: str(kv[0]))},
               "G1": summ([x for x in rows if x["exp"] == "G1"]), "S2": summ([x for x in rows if x["exp"] == "S2"]),
               "per_run": {k: summ(v) for k, v in sorted(per_run.items())}}

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "S452_calls_load.csv").open("w", newline="") as fh:
        fh.write(f"# generated by scripts/S452_q146_load_rebuild.py; command {prov['command']}; read from {a.host} at "
                 f"{prov['read_at']}; inputs and limits in S452_summary.json\n")
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (OUT / "S452_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    md = [f"# Q146: machine load of G1's and S2's past local calls, rebuilt from the Studio's logs",
          "", f"Provenance: `{prov['command']}` at repo HEAD {git[:7]}, read from the Studio ({a.host}) at "
          f"{prov['read_at']}. Inputs (sha256 of the [GIN] lines read per log) in S452_summary.json. No model call.",
          "", "## Limits", ""] + [f"- {x}" for x in limits] + [
          "", "## Log coverage (first and last [GIN] line, model requests)", "",
          "| port | first | last | model requests |", "|---|---|---|---|"] + [
          f"| {p} | {v['first']} | {v['last']} | {v['model_requests']} |" for p, v in sorted(logs.items())] + [
          "", "Servers running now whose log is elsewhere, model requests inside the window: " + (", ".join(
              f"{o['port']}: {o['model_requests_in_window']}" for o in others) or "none") + ".",
          "", "## Calls", "", "| | calls | matched | other ports busy, mean over the call: median, least | "
          "most at once (calls) | G1 strategies running at the call's start, the call's own included (calls) | "
          "may miss a request still running (calls) |", "|---|---|---|---|---|---|---|"] + [
          f"| {k} | {v['calls']} | {v.get('matched')} | {v.get('other_ports_mean_median')}, "
          f"{v.get('other_ports_mean_min')} | {v.get('other_ports_max_counts')} | {v.get('g1_jobs_running_counts')} | "
          f"{v.get('may_miss_running')} |"
          for k, v in (("G1", summary["G1"]), ("S2", summary["S2"]))] + [
          "", "Per run: S452_summary.json `per_run`; per call: S452_calls_load.csv."]
    (OUT / "S452_summary.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"G1": summary["G1"], "S2": summary["S2"], "log_coverage": summary["log_coverage"],
                      "servers_logging_elsewhere": others}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
