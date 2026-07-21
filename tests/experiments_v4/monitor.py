#!/usr/bin/env python3
"""
Monitor experiment progress, memory usage, and estimate completion time.
Runs in a loop, printing a dashboard every N seconds.
"""

import json
import subprocess
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

V4_RESULTS = Path(__file__).parent / "results_v4"
S20_INTERMEDIATE = V4_RESULTS / "v4_5_intermediate_s20.json"
SCALING_LATEST = V4_RESULTS / "v4_5_scaling_latest.json"
V46_LATEST = V4_RESULTS / "v4_6_orchestration_ablation_latest.json"
NAIVE_LATEST = V4_RESULTS / "v4_naive_baseline_latest.json"

INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 30  # seconds


def get_memory_gb():
    r = subprocess.run(["vm_stat"], capture_output=True, text=True)
    d = {}
    for line in r.stdout.split("\n"):
        m = re.match(r"(.+?):\s+(\d+)", line)
        if m:
            d[m.group(1)] = int(m.group(2))
    ps = 16384
    active = d.get("Pages active", 0) * ps / 1e9
    wired = d.get("Pages wired down", 0) * ps / 1e9
    compressed = d.get("Pages occupied by compressor", 0) * ps / 1e9
    return active + wired + compressed, active, wired, compressed


def get_tmux_sessions():
    r = subprocess.run(["tmux", "list-sessions"], capture_output=True, text=True)
    if r.returncode != 0:
        return []
    sessions = []
    for line in r.stdout.strip().split("\n"):
        name = line.split(":")[0]
        if name not in ("claude",):
            sessions.append(name)
    return sessions


def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def count_results(data):
    results = data.get("per_question_results", data.get("results", []))
    total = len(results)
    has_answer = sum(
        1 for r in results
        if r.get("generation", {}).get("answer", "").strip()
    )
    has_judge = sum(
        1 for r in results
        if isinstance(r.get("judge_scores", {}), dict)
        and (
            r["judge_scores"].get("correctness") is not None
            or r["judge_scores"].get("refusal_accuracy") is not None
        )
    )
    empty = total - has_answer
    return total, has_answer, has_judge, empty


def s20_detail(data):
    results = data.get("per_question_results", data.get("results", []))
    by_cell = Counter()
    ans_cell = Counter()
    for r in results:
        key = (r.get("index_name", "?"), r.get("config", "?"))
        by_cell[key] += 1
        if r.get("generation", {}).get("answer", "").strip():
            ans_cell[key] += 1

    # Target: 3 indexes × 6 configs × 138
    target = 3 * 6 * 138
    done = sum(ans_cell.values())
    return done, target, by_cell, ans_cell


# Track history for rate estimation
history = []  # (timestamp, s20_count)


def print_dashboard():
    now = datetime.now()
    mem_total, mem_active, mem_wired, mem_compressed = get_memory_gb()
    sessions = get_tmux_sessions()

    print(f"\033[2J\033[H", end="")  # clear screen
    print(f"{'='*70}")
    print(f"  MENTORI EXPERIMENT MONITOR — {now.strftime('%H:%M:%S')}")
    print(f"{'='*70}")

    # Memory
    print(f"\n  Memory: {mem_total:.0f} GB / 512 GB "
          f"(active={mem_active:.0f}, wired={mem_wired:.0f}, "
          f"compressed={mem_compressed:.0f})")
    if mem_total > 200:
        print(f"  ⚠️  HIGH MEMORY — watch for pressure")
    elif mem_total > 300:
        print(f"  🚨 CRITICAL MEMORY — kernel panic risk")
    else:
        print(f"  ✓ Memory OK")

    # Tmux sessions
    print(f"\n  Active sessions: {', '.join(sessions) if sessions else 'none'}")

    # V4-5 scaling_latest
    print(f"\n  {'─'*66}")
    print(f"  V4-5 SCALING (scaling_latest.json)")
    data = load_json_safe(SCALING_LATEST)
    if data:
        total, has_ans, has_judge, empty = count_results(data)
        print(f"    Total: {total} | Answered: {has_ans} | Judged: {has_judge} | Empty: {empty}")
    else:
        print(f"    (file not readable)")

    # V4-5 s20 intermediate
    print(f"\n  {'─'*66}")
    print(f"  V4-5 S20 GENERATION (intermediate_s20.json)")
    s20_data = load_json_safe(S20_INTERMEDIATE)
    if s20_data:
        done, target, by_cell, ans_cell = s20_detail(s20_data)
        print(f"    Progress: {done}/{target} answers ({done/target*100:.1f}%)")

        history.append((time.time(), done))

        # Rate estimation
        if len(history) >= 2:
            # Use last 5 min window for rate
            window = 300
            recent = [(t, c) for t, c in history if t > time.time() - window]
            if len(recent) >= 2 and recent[-1][1] > recent[0][1]:
                dt = recent[-1][0] - recent[0][0]
                dc = recent[-1][1] - recent[0][1]
                rate = dc / dt * 3600  # per hour
                remaining = target - done
                if rate > 0:
                    eta_hours = remaining / rate
                    eta_time = now + timedelta(hours=eta_hours)
                    print(f"    Rate: {rate:.1f} results/hour | "
                          f"ETA: {eta_time.strftime('%H:%M')} ({eta_hours:.1f}h)")
                else:
                    print(f"    Rate: stalled (0 results in last {window}s)")
            elif len(recent) >= 2 and recent[-1][1] == recent[0][1]:
                print(f"    Rate: stalled (no new results in {window}s) — Gemini RPD?")
            else:
                print(f"    Rate: collecting data... (need {INTERVAL}s+)")

        # Per-index breakdown
        for idx in ["exp_v4_s20_n0", "exp_v4_s20_n1", "exp_v4_s20_n3"]:
            configs = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
            parts = []
            for c in configs:
                key = (idx, c)
                t = by_cell.get(key, 0)
                a = ans_cell.get(key, 0)
                if t > 0:
                    mark = "✓" if a >= 138 else f"{a}/138"
                    parts.append(f"{c[:6]}={mark}")
                else:
                    parts.append(f"{c[:6]}=—")
            short_idx = idx.replace("exp_v4_", "")
            print(f"    {short_idx}: {' | '.join(parts)}")

    else:
        print(f"    (file not readable)")

    # V4-6
    print(f"\n  {'─'*66}")
    print(f"  V4-6 ORCHESTRATION")
    v46_data = load_json_safe(V46_LATEST)
    if v46_data:
        total, has_ans, has_judge, empty = count_results(v46_data)
        print(f"    Total: {total}/552 | Answered: {has_ans} | Judged: {has_judge}")
    else:
        print(f"    (file not readable)")

    # Naive
    naive_data = load_json_safe(NAIVE_LATEST)
    if naive_data:
        total, has_ans, has_judge, empty = count_results(naive_data)
        print(f"  NAIVE BASELINE: {total} | Answered: {has_ans} | Judged: {has_judge} ✓")

    # Overall remaining work
    print(f"\n  {'─'*66}")
    print(f"  REMAINING WORK (Gemini RPD-gated)")
    print(f"    s20 generation:   ~522 questions (~5,800 API calls)")
    print(f"    s50 RLM regen:    2,250 questions (~30,000 API calls)")
    print(f"    V4-6 rlm_10:     138 questions (~1,840 API calls)")
    print(f"    Total: ~37,600 API calls → ~3.8 days at 10K RPD")

    print(f"\n{'='*70}")
    print(f"  Next refresh in {INTERVAL}s (Ctrl+C to stop)")


if __name__ == "__main__":
    try:
        while True:
            print_dashboard()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
