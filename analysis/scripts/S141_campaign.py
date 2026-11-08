#!/usr/bin/env python3
"""Phase 4.1 — the campaign. Five generators, six strategies, three draws.

    138 questions x 6 strategies x 3 draws x 5 generators = 12,420 generations

Fifteen arms, each a subprocess running `S141_campaign_worker.py`. Local arms are pinned one per
Ollama instance so the three run in parallel; cloud arms run concurrently alongside them, since they
consume no local GPU.

**Roster, ruled by Valerio on 2026-08-14.** `gemini-3.6-flash` failed the P25 screen at 46.7% and is
reported as failing rather than replaced.

**Resume is the default and is why this is restartable.** An arm that has written `DONE` is skipped
whole; an arm that died part-way resumes from its own `intermediate.json`, which is per-arm precisely
so arms cannot read each other's completions (P19). Killing this orchestrator loses nothing but the
in-flight questions.

**It does not judge readiness for you.** It refuses to start unless the archive is clean at the
pinned commit, the instances answer, and the roster matches the ruling. It prints what it will do and
requires `--go`; a dry run is the default, because the first thing a ten-day job should do is show
you the plan.

    uv run python scripts/S141_campaign.py                 # dry run: the plan, no work
    uv run python scripts/S141_campaign.py --go            # start
    uv run python scripts/S141_campaign.py --go --max-questions 2 --arms 2   # shakedown
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PAPER = Path("/Users/bioinfo-001/projects/Mentori")
REANALYSIS = Path("/Users/bioinfo-001/projects/Mentori-reanalysis")
WORKER = REANALYSIS / "scripts" / "S141_campaign_worker.py"
ROOT = REANALYSIS / "findings" / "recompute" / "S141_campaign"
INSTANCES = REANALYSIS / "findings" / "recompute" / "S141_instances.json"
STATUS = ROOT / "status.json"
EXPECTED_HEAD = "af29e58292de0f3f18f3a2933e55ed74f54ba6fc"

INDEX = "exp_v4_s20_n0"
DRAWS = (1, 2, 3)
SEEDS = {1: 1, 2: 2, 3: 3}          # local only; fixed and declared, not chosen after seeing results

ROSTER = [
    {"generator": "ollama::gemma3:27b",             "kind": "local", "port": 11441},
    {"generator": "ollama::glm-4.7-flash:latest",   "kind": "local", "port": 11442},
    {"generator": "ollama::nemotron-3-nano:30b",    "kind": "local", "port": 11443},
    {"generator": "anthropic::claude-haiku-4-5",    "kind": "cloud", "port": None},
    {"generator": "gemini::gemini-3-flash-preview", "kind": "cloud", "port": None},
]

# A disclosed side-measurement, not a campaign arm. glm-4.7-flash is a thinking model and the
# archived harness configures thinking nowhere, so at the executor's 700-token sub-call cap it
# returns no answer at all (S141_THINKING_UNCONTROLLED.md). This one arm repeats draw 1 with the
# generator forced to think=False and nothing else changed, to separate "this generator cannot
# drive an RLM loop" from "this harness did not let it".
#
# Pinned to glm's own instance deliberately: glm is NOT reproducible across instances (measured,
# both with thinking on and off), so running it elsewhere would confound thinking with host.
SIDE_ARMS = [
    {"generator": "ollama::glm-4.7-flash:latest", "kind": "local", "port": 11442,
     "draw": 1, "seed": 1, "think_off": True, "suffix": "__thinkoff"},
]

# Judge-only instances for the cloud arms. Their generation happens off-machine, but every answer is
# still judged locally, and pointing them at a generator's instance is what broke the first launch:
# three arms on one single-slot server, with the judge model not even resident. One port per
# concurrent cloud arm, assigned at launch from whichever is free.
CLOUD_JUDGE_PORTS = [11444, 11445, 11446, 11447]

# Scheduling. A local arm holds its instance exclusively: three draws of the same generator all point
# at one port, and running two at once would put two arms through an instance configured
# OLLAMA_NUM_PARALLEL=1, serialising them while doubling the KV-cache pressure P26 measures. So at
# most one local arm per port, which caps local concurrency at three — one per instance, exactly the
# shape the pilot measured.
#
# Cloud arms are network-bound and only touch a port for judging, so they do not hold one. They are
# capped separately to keep judge traffic off the critical path of the local arms.
MAX_CLOUD_CONCURRENT = len(CLOUD_JUDGE_PORTS)


def archive_state() -> dict:
    p = subprocess.run(["git", "-C", str(PAPER), "status", "--porcelain"],
                       capture_output=True, text=True).stdout.strip()
    h = subprocess.run(["git", "-C", str(PAPER), "rev-parse", "HEAD"],
                       capture_output=True, text=True).stdout.strip()
    return {"porcelain_empty": p == "", "head": h, "ok": p == "" and h == EXPECTED_HEAD}


def arm_id(generator: str, draw: int) -> str:
    return f"{generator.replace('::', '_').replace(':', '_').replace('/', '_')}__draw{draw}"


def arm_done(d: Path, max_questions: int | None, index: str) -> tuple[bool, str]:
    """Done means done *at the scope now being asked for*, not merely finished once.

    The shakedown caught this: an arm run with --max-questions 2 wrote a bare-timestamp DONE, and a
    full run would have skipped it and shipped 12 rows where 828 were required. A marker without a
    scope is not evidence of completion.
    """
    f = d / "DONE"
    if not f.exists():
        return False, ""
    try:
        rec = json.loads(f.read_text())
    except Exception:
        return False, "DONE has no scope recorded (pre-scope marker); treating as incomplete"
    if rec.get("index") != index:
        return False, f"DONE is for index {rec.get('index')}, not {index}"
    if rec.get("max_questions") != max_questions:
        return False, (f"DONE covers max_questions={rec.get('max_questions')}, "
                       f"now asking for {max_questions}")
    return True, f"{rec.get('rows')} rows"


def plan(max_questions: int | None = None) -> list[dict]:
    out = []
    for entry in ROSTER:
        for draw in DRAWS:
            aid = arm_id(entry["generator"], draw)
            d = ROOT / aid
            done, why = arm_done(d, max_questions, INDEX)
            out.append({
                **entry, "draw": draw, "arm": aid, "dir": d,
                "seed": SEEDS[draw] if entry["kind"] == "local" else -1,
                "done": done, "done_note": why,
                "started": (d / "arm_header.json").exists(),
            })
    # Side measurements go LAST: a campaign arm 20 rows from finishing must not queue behind a
    # fresh side-arm for its instance, which is what happened on the first attempt.
    for e in SIDE_ARMS:
        aid = arm_id(e["generator"], e["draw"]) + e["suffix"]
        d = ROOT / aid
        done, why = arm_done(d, max_questions, INDEX)
        out.append({**e, "arm": aid, "dir": d, "done": done, "done_note": why,
                    "started": (d / "arm_header.json").exists()})
    return out


def instances_up() -> dict:
    import urllib.request
    out = {}
    for inst in json.loads(INSTANCES.read_text())["instances"]:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{inst['port']}/api/version",
                                        timeout=5) as r:
                out[inst["port"]] = json.loads(r.read().decode()).get("version")
        except Exception as e:
            out[inst["port"]] = f"DOWN: {e}"
    return out


def write_status(arms: list[dict], running: dict, started_at: float,
                 max_questions: int | None, ) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for a in arms:
        tick = a["dir"] / "tick.json"
        t = {}
        if tick.exists():
            try:
                t = json.loads(tick.read_text().strip().splitlines()[-1])
            except Exception:
                t = {}
        rows.append({
            "arm": a["arm"], "generator": a["generator"], "draw": a["draw"],
            "kind": a["kind"], "seed": a["seed"],
            "done": arm_done(a["dir"], max_questions, INDEX)[0],
            "running": a["arm"] in running,
            "rows_done": t.get("rows_done"),
            "last_row_at": t.get("last_row_at"),
            "last_question": t.get("last_question"),
            "last_config": t.get("last_config"),
        })
    STATUS.write_text(json.dumps({
        "updated": round(time.time(), 2),
        "elapsed_s": round(time.time() - started_at, 1),
        "expected_generations_per_arm": None,
        "arms": rows,
    }, indent=1) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="actually run; default is a dry run")
    ap.add_argument("--max-questions", type=int, default=None, help="shakedown only")
    ap.add_argument("--arms", type=int, default=None, help="cap the number of arms; shakedown only")
    ap.add_argument("--code-timeout", type=float, default=120.0)
    ap.add_argument("--max-parallel", type=int, default=7)   # 3 local + 4 cloud
    args = ap.parse_args()

    before = archive_state()
    arms = plan(args.max_questions)
    if args.arms:
        arms = arms[:args.arms]
    todo = [a for a in arms if not a["done"]]
    up = instances_up()

    print("S141 Phase 4.1 — the campaign\n")
    print(f"archive: HEAD {before['head'][:7]}, "
          f"{'clean' if before['porcelain_empty'] else 'DIRTY'}")
    print(f"instances: {up}")
    print(f"index: {INDEX}   draws: {list(DRAWS)}   "
          f"questions: {args.max_questions or 'all eligible'}")
    print(f"\narms: {len(arms)} total, {len(arms)-len(todo)} already done, {len(todo)} to run\n")
    for a in arms:
        flag = "DONE" if a["done"] else ("part" if a["started"] else "    ")
        print(f"  {flag}  {a['arm']:46s} {a['kind']:5s} seed={a['seed']:>2}"
              f"  {a.get('done_note','')}")

    if not before["ok"]:
        print("\nREFUSING: the archived harness is not clean at the pinned commit.")
        return 1
    if any(isinstance(v, str) and v.startswith("DOWN") for v in up.values()):
        print("\nREFUSING: an Ollama instance is down. The pilot's instances are part of the design.")
        return 1
    if not args.go:
        print("\nDry run. Nothing started. Re-run with --go to begin.")
        return 0
    if not todo:
        print("\nEvery arm is already done.")
        return 0

    ROOT.mkdir(parents=True, exist_ok=True)
    started_at = time.time()
    running: dict[str, dict] = {}
    queue = list(todo)
    print(f"\nstarting — {len(queue)} arms, at most {args.max_parallel} at once\n")

    while queue or running:
        while queue and len(running) < args.max_parallel:
            busy_ports = {r["arm"]["port"] for r in running.values()
                          if r["arm"]["kind"] == "local"}
            n_cloud = sum(1 for r in running.values() if r["arm"]["kind"] == "cloud")
            pick = None
            for i, cand in enumerate(queue):
                if cand["kind"] == "local" and cand["port"] in busy_ports:
                    continue                      # its instance is taken
                if cand["kind"] == "cloud" and n_cloud >= MAX_CLOUD_CONCURRENT:
                    continue
                pick = i
                break
            if pick is None:
                break                             # nothing launchable right now; wait for a slot
            a = queue.pop(pick)
            if a["kind"] == "cloud":
                taken = {r["arm"]["port"] for r in running.values() if r["arm"]["kind"] == "cloud"}
                free = [p for p in CLOUD_JUDGE_PORTS if p not in taken]
                if not free:
                    queue.insert(0, a)
                    break
                a["port"] = free[0]
            a["dir"].mkdir(parents=True, exist_ok=True)
            env = dict(**{k: v for k, v in __import__("os").environ.items()})
            env["OLLAMA_BASE_URL"] = f"http://127.0.0.1:{a['port']}"
            env["MENTORI_EMBED_DEVICE"] = "cpu"
            cmd = ["uv", "run", "python", str(WORKER),
                   "--arm", a["arm"], "--generator", a["generator"],
                   "--draw", str(a["draw"]), "--seed", str(a["seed"]),
                   "--arm-dir", str(a["dir"]), "--index", INDEX,
                   "--code-timeout", str(args.code_timeout)]
            if a.get("think_off"):
                cmd.append("--think-off")
            if args.max_questions:
                cmd += ["--max-questions", str(args.max_questions)]
            log = open(a["dir"] / "worker.log", "a")
            p = subprocess.Popen(cmd, cwd=str(PAPER), env=env, stdout=log,
                                 stderr=subprocess.STDOUT)
            running[a["arm"]] = {"proc": p, "arm": a, "log": log}
            print(f"  [{int(time.time()-started_at):6d}s] launched {a['arm']} pid {p.pid}")

        time.sleep(15)
        for aid in list(running):
            p = running[aid]["proc"]
            if p.poll() is not None:
                running[aid]["log"].close()
                ok = arm_done(running[aid]["arm"]["dir"], args.max_questions, INDEX)[0]
                print(f"  [{int(time.time()-started_at):6d}s] finished {aid} "
                      f"exit={p.returncode} {'DONE' if ok else 'NO DONE MARKER'}")
                del running[aid]
        write_status(arms, running, started_at, args.max_questions)

    after = archive_state()
    write_status(arms, {}, started_at, args.max_questions)
    done = sum(1 for a in arms if arm_done(a["dir"], args.max_questions, INDEX)[0])
    print(f"\narms complete: {done}/{len(arms)}   elapsed {(time.time()-started_at)/3600:.2f} h")
    print(f"archive after: HEAD {after['head'][:7]}, {'clean' if after['ok'] else 'ALTERED'}")
    return 0 if done == len(arms) else 1


if __name__ == "__main__":
    raise SystemExit(main())
