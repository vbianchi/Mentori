#!/usr/bin/env python3
"""
V2-7 Part A (Orchestration) Status Dashboard.

Reads completed and intermediate results from exp5 to show a live
breakdown of the runs.

Usage:
    uv run python tests/experiments_v2/v2_7_status.py
"""

import json
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).parent.parent / "experiments" / "results"

def load_all_results():
    """Load all exp5 results."""
    results = []
    sources = {}

    intermediate_path = RESULTS_DIR / "exp5_intermediate.json"
    intermediate_mtime = intermediate_path.stat().st_mtime if intermediate_path.exists() else 0

    completed_files = sorted(RESULTS_DIR.glob("exp5_results_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    latest_completed = None
    for f in completed_files:
        if "latest" not in f.name:
            latest_completed = f
            break
            
    completed_mtime = latest_completed.stat().st_mtime if latest_completed else 0

    # If an intermediate file is actively being written to (newer than the last completed run), ONLY load it.
    if intermediate_mtime > completed_mtime:
        try:
            data = json.loads(intermediate_path.read_text())
            for r in data.get("results", []):
                key = (r["config"], r["question_id"])
                sources[key] = ("running", "intermediate")
                results.append(r)
        except Exception:
            pass
    else:
        # Load the latest completed run
        if latest_completed:
            try:
                data = json.loads(latest_completed.read_text())
                for r in data.get("per_question_results", []):
                    key = (r["config"], r["question_id"])
                    sources[key] = ("done", latest_completed.name)
                    results.append(r)
            except Exception:
                pass

    return results, sources

ALL_CONFIGS = [
    "zero_shot", 
    "llm_with_rag", 
    "orchestrator_no_supervisor", 
    "orchestrator_full"
]
TOTAL_QUESTIONS = 20
EXPECTED_TOTAL = TOTAL_QUESTIONS * len(ALL_CONFIGS)

def aggregate(results):
    by_config = defaultdict(list)
    for r in results:
        by_config[r["config"]].append(r)
        
    rows = []
    for cfg in ALL_CONFIGS:
        recs = by_config[cfg]
        n = len(recs)
        
        # Determine pass/fail based on a correctness >= 4 threshold 
        passed = sum(1 for r in recs if r.get("judge_scores", {}).get("correctness", 0) >= 4)
        
        pass_rate = (passed / n * 100) if n else 0
        progress = (n / TOTAL_QUESTIONS * 100)
        
        latencies = [r.get("generation", {}).get("latency_s", 0) for r in recs if r.get("generation", {}).get("latency_s", 0) > 0]
        med_lat = sorted(latencies)[len(latencies)//2] if latencies else 0
        
        llms = [r.get("generation", {}).get("llm_calls", 0) for r in recs if r.get("generation", {}).get("llm_calls", 0) > 0]
        avg_llm = sum(llms) / len(llms) if llms else 0
        
        tokens = [r.get("generation", {}).get("tokens_used", 0) for r in recs if r.get("generation", {}).get("tokens_used", 0) > 0]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0
        
        rows.append({
            "config": cfg,
            "n": n,
            "progress": f"{n}/{TOTAL_QUESTIONS} ({progress:.0f}%)",
            "pass_rate": f"{pass_rate:.0f}%",
            "passed": passed,
            "med_lat": f"{med_lat:.0f}s",
            "avg_llm": f"{avg_llm:.1f}",
            "avg_tokens": f"{avg_tokens:.0f}",
        })
        
    return rows

def print_summary(rows, results, sources):
    print("=" * 100)
    print("V2-7 PART A (ORCHESTRATION) — STATUS DASHBOARD")
    print("=" * 100)
    
    done_count = sum(1 for s, _ in sources.values() if s == "done")
    running_count = sum(1 for s, _ in sources.values() if s == "running")
    print(f"Loaded {len(results)} total evaluations ({done_count} completed, {running_count} in-progress)")
    print(f"Benchmark scale: {TOTAL_QUESTIONS} questions × {len(ALL_CONFIGS)} configs = {EXPECTED_TOTAL} total evaluations")
    print()
    
    hdr = f"{'Config':<30} {'Progress':<16} {'Pass Rate':>10} {'Pass':>5} {'Med.Lat':>8} {'LLMs':>6} {'Tokens':>8}"
    print(hdr)
    print("-" * len(hdr))
    
    for r in rows:
        status = "✓" if r["n"] == TOTAL_QUESTIONS else "…"
        print(
            f"{status} {r['config']:<28} {r['progress']:<16} {r['pass_rate']:>10}"
            f" {r['passed']:>5} {r['med_lat']:>8} {r['avg_llm']:>6} {r['avg_tokens']:>8}"
        )
    print()

def main():
    results, sources = load_all_results()
    if not results:
        print("No V2-7 (exp5) results found.")
        return
        
    rows = aggregate(results)
    print_summary(rows, results, sources)

if __name__ == "__main__":
    main()
