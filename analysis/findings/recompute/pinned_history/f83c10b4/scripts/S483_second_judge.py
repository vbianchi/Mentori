#!/usr/bin/env python3
"""S483: the second judge, qwen3.8:27b GGUF (LOCK.toml [judge] second_model, digest aaee06c3, machines ["beelink"]
under lock d66daa28): D85's repeat check, D92 Q198's composite, and the check of its G1 run.

D85 (README.md, Valerio 17 October): the GGUF build is "checked for repeating its scores on the 107 calibration
answers before it judges". D92 Q198: "the paper names 0.628 as the MLX build's score and, after the D85 repeat check,
gives the GGUF build's composite on the 107 calibration answers beside the MLX build's 0.530 on the same answers".

  d85        D85's repeat check, as S440 checked devstral (scripts/S440_judge_lock_check.py: the 107 calibration
             answers of S376.answers_and_key, the archived judge prompt, whole answers, one server, one call at a
             time), here with the lock's [judge] settings for the second judge: judge_passages.py check --judge second
             judges the 107 twice, each pass after its own fresh load, and passes only if every answer gives every score
             equal in both passes, every call is ok and every call record sent temperature 0 and think false. Live, it
             runs findings/recompute/S3_runs/run_s3.sh with S3_JUDGE=second S3_CHECK_ONLY=1 on the Beelink's Windows
             Ollama (the launcher's guard, its release ledger and its check dir out/check_second_<port>, so the G1 run
             that follows finds the check passed and starts on it). It refuses anywhere but a machine the lock's
             [models] machines names for the second judge. --dry-run: offline, no server contact at all: the lock,
             the 107 prompts and the exact request body each would send, the check dir, the composite's reproduction
             gate, a time estimate, and the live command.
  composite  D92 Q198, offline. First reproduces S376b's Table A for all 22 judges (composite, its three Pearson r,
             95% interval from 2,000 resamples of the 107 answers with seed 20261009, difference from qwen3-coder)
             from the S376 ledger and the reference measures stored in S376_calibration_analysis.json, and refuses
             unless every value equals the stored one (the MLX build: 0.530, 0.451 to 0.608). Then the same numbers for
             the GGUF build from the passed check's rows (repro_check_rows.jsonl; both passes equal), on the same
             resamples. Writes findings/recompute/S483_d85_composite.{json,md}. --dry-run: the gate only.
  g1-status  The check of the second judge's G1 run (run_s3.sh S3_JUDGE=second on G1R15 and G1, phases 1 and 2),
             offline, read only: the check passed for this judge and lock; every row in its outs names the second
             judge with the lock's digest, under one run_sha256 and the current lock; every header names it; every
             recheck passed; what is left (s3_guard.py plan --judge second); the pace measured on its own rows and
             the hours left at that pace. Exit 1 on any problem.
  selftest   Offline, with mutants: the composite path fed the MLX build's own ledger rows gives 0.530 and its
             interval; a check not passed, of another judge, or with the passes differing is refused; g1-status flags a
             row without the second judge's name, a second run_sha256 and a failed recheck.

    uv run --frozen python scripts/S483_second_judge.py d85 --dry-run
    uv run --frozen python scripts/S483_second_judge.py d85                     (the Beelink, once no K1 worker runs)
    uv run --frozen python scripts/S483_second_judge.py composite [--check-dir DIR] [--dry-run]
    uv run --frozen python scripts/S483_second_judge.py g1-status [--port 11434]
    uv run --frozen python scripts/S483_second_judge.py selftest
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import socket
import sys
import time
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from experiments.runner.lock import load  # noqa: E402

D = ROOT / "findings/recompute/S3_runs"
S376_LEDGER = ROOT / "findings/recompute/S376_judge_calibration.jsonl"
S376_ANALYSIS = ROOT / "findings/recompute/S376_calibration_analysis.json"
S440_BEELINK = ROOT / "findings/recompute/S440_judge_lock_check_beelink.jsonl"
OUT_JSON = ROOT / "findings/recompute/S483_d85_composite.json"
OUT_MD = ROOT / "findings/recompute/S483_d85_composite.md"
MLX = "qwen3.8:27b-mlx"
GGUF = "qwen3.8:27b (GGUF, D85 check)"
TOL = 1e-12
# The Beelink's Windows Ollama (findings/recompute/K1/run_k1_beelink.sh: the app's server on the default port)
WIN = "/mnt/c/Users/Valerio/AppData/Local"
BEELINK = {"S3_SERVER_LOG": f"{WIN}/Ollama/server.log", "S3_OLLAMA_BIN": f"{WIN}/Programs/Ollama/ollama.exe",
           "S3_CHECK_MACHINE": "beelink"}
DEFAULT_PORT = 11434
# K1's launcher and its watcher on the Beelink: users of this machine's servers that the guard's 11434 pattern does not
# name (its scorer children are named there already); S3_JOB_PATTERN adds them (run_s3.sh "Settings")
K1_PATTERN = r"run_k1_beelink\.sh( beelink)?\s*$|k1_autorestart\.sh main"
# D143 (Valerio, 26 October, Q11 O-c): the second judge runs on the Windows app's server while a K1 helper scores on its
# own server: only the main K1 worker's launcher counts (above), and a helper's processes, which name their own folder
# findings/recompute/K1/beelink_<port>/ (run_k1_beelink.sh JOB_PATTERN), are not strangers (run_s3.sh S3_NOT_STRANGER)
K1_HELPER = r"findings/recompute/K1/beelink_[0-9]+/"
# D204 (Valerio, 2 November): the laptop and the Studio may run the second judge too (LOCK.toml [models] machines). Each
# machine's server log, binary and check_server machine name; the Studio's per-port log as run_s3.sh's default. The K1
# patterns name only the Beelink's processes.
MACHINE_ENV = {
    "beelink": {**BEELINK, "S3_JOB_PATTERN": K1_PATTERN, "S3_NOT_STRANGER": K1_HELPER},
    "laptop": {"S3_SERVER_LOG": "/opt/homebrew/var/log/ollama.log", "S3_OLLAMA_BIN": "/opt/homebrew/opt/ollama/bin/ollama",
               "S3_CHECK_MACHINE": "macos"},
    "studio": {"S3_OLLAMA_BIN": "/opt/homebrew/opt/ollama/bin/ollama", "S3_CHECK_MACHINE": "macos"},
}


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def this_machine() -> str:
    """The lock's [models] machines name of this machine: beelink (WSL with the Windows disk), studio, laptop."""
    if Path("/mnt/c/Windows").exists():
        return "beelink"
    return "studio" if "studio" in socket.gethostname().lower() else "laptop"


# ---------------------------------------------------------------- composite (S376b's Table A, reproduced)

def s376b():
    import S376b_calibration_analysis as B
    return B


def current_ledger() -> tuple[dict, list[str]]:
    """S376b's inputs: the ledger rows scored against the current key, by judge, and the 107 answer keys."""
    import S376_judge_calibration as S376
    cur = {x["answer_key"]: x["key_hash"] for x in S376.answers_and_key()}
    by = defaultdict(list)
    for r in map(json.loads, filter(str.strip, S376_LEDGER.read_text().splitlines())):
        if r["key_hash"] == cur.get(r["answer_key"]):
            by[r["judge"]].append(r)
    return by, sorted(cur)


def table_a(by: dict, obj: dict, extra: dict | None = None, seed: int | None = None) -> dict:
    """S376b.main's table(False), whose code it follows line by line: per judge its scored rows, the composite and the
    three r, then 2,000 resamples of the answers (seed 20261009), each judge's composite on its scored answers among
    the resample, the 95% interval and the difference from qwen3-coder on the same resample. extra: judges added
    (name -> rows), computed on the same resamples, so they change no other judge's numbers."""
    B = s376b()
    rows_by = dict(by) | (extra or {})
    keys = sorted(obj)
    rng = np.random.default_rng(B.SEED if seed is None else seed)
    boots = [rng.choice(len(keys), len(keys), replace=True) for _ in range(B.N_BOOT)]
    res, scored_by = {}, {}
    for j, rows in rows_by.items():
        ok = [r for r in rows if r["scores"] is not None and r["answer_key"] in obj]
        scored_by[j] = {r["answer_key"]: r for r in ok}
        comp, parts = B.composite(ok, obj)
        res[j] = {"n_scored": len(ok), "n_calls": len(rows), "composite": comp, **parts}
    boot = defaultdict(list)
    for idx in boots:
        sample = [keys[i] for i in idx]
        for j in res:
            boot[j].append(B.composite([scored_by[j][k] for k in sample if k in scored_by[j]], obj)[0])
    inc = np.array(boot.get(B.INCUMBENT, [np.nan] * B.N_BOOT))
    for j in res:
        b = np.array(boot[j])
        res[j]["ci95"] = [float(np.nanpercentile(b, 2.5)), float(np.nanpercentile(b, 97.5))]
        d = b - inc
        res[j]["diff_vs_incumbent_ci95"] = [float(np.nanpercentile(d, 2.5)), float(np.nanpercentile(d, 97.5))]
    return res


NUM_KEYS = ("composite", "correctness~similarity", "completeness~concept_recall", "citation~citation_composite")


def gate(res: dict, stored: dict) -> list[str]:
    """Every judge of the stored Table A reproduced: n, the four numbers, both intervals (TOL)."""
    bad = []
    for j, s in stored.items():
        r = res.get(j)
        if r is None:
            bad.append(f"{j}: not reproduced")
            continue
        if (r["n_scored"], r["n_calls"]) != (s["n_scored"], s["n_calls"]):
            bad.append(f"{j}: n {r['n_scored']}/{r['n_calls']} against {s['n_scored']}/{s['n_calls']}")
        for k in NUM_KEYS:
            if abs(r[k] - s[k]) > TOL:
                bad.append(f"{j}: {k} {r[k]!r} against {s[k]!r}")
        for k in ("ci95", "diff_vs_incumbent_ci95"):
            if any(abs(x - y) > TOL for x, y in zip(r[k], s[k])):
                bad.append(f"{j}: {k} {r[k]} against {s[k]}")
    return bad


def check_rows(check_dir: Path, lock) -> list[dict]:
    """The GGUF build's scores from D85's passed check, as ledger-shaped rows (answer_key, scores). Refuses a check
    that did not pass, is not the second judge's under this lock, or whose two passes differ on any answer."""
    f = check_dir / "repro_check.json"
    if not f.exists():
        raise SystemExit(f"REFUSED: no D85 check in {check_dir} (S483 d85 first)")
    c = json.loads(f.read_text())
    second = lock.d["judge"]["second_model"]
    want = {"passed": True, "full_sample": True, "judge": "second", "model": second, "n": 107, "equal_scores": 107,
            "lock_sha256": lock.sha256}
    bad = {k: (c.get(k), v) for k, v in want.items() if c.get(k) != v}
    if bad:
        raise SystemExit(f"REFUSED: {f} is not a passed D85 check of {second} under this lock (found, wanted): {bad}")
    rows = [json.loads(x) for x in (check_dir / "repro_check_rows.jsonl").read_text().splitlines() if x.strip()]
    if len(rows) != 107 or len({r["answer_key"] for r in rows}) != 107:
        raise SystemExit(f"REFUSED: {check_dir}/repro_check_rows.jsonl holds {len(rows)} rows, not the 107 answers")
    differ = [r["answer_key"] for r in rows if not r["equal"] or r["scores"] != r["first_scores"] or r["scores"] is None]
    if differ:
        raise SystemExit(f"REFUSED: the two passes differ on {len(differ)} answers (first {differ[0]})")
    return [{"answer_key": r["answer_key"], "scores": r["scores"]} for r in rows]


def reproduce() -> tuple[dict, dict, dict, dict]:
    stored = json.loads(S376_ANALYSIS.read_text())
    obj = stored["reference_measures"]
    by, keys = current_ledger()
    if sorted(obj) != keys:
        raise SystemExit("REFUSED: the stored reference measures are not the 107 answers of S376.answers_and_key")
    res = table_a(by, obj)
    bad = gate(res, stored["all_answers"])
    if bad:
        raise SystemExit(f"REFUSED: S376b's Table A not reproduced ({len(bad)} values differ; first: {bad[0]})")
    return res, stored, obj, by


def fmt(r: dict) -> str:
    return (f"{r['composite']:.3f} ({r['ci95'][0]:.3f} to {r['ci95'][1]:.3f}) | {r['correctness~similarity']:.3f} | "
            f"{r['completeness~concept_recall']:.3f} | {r['citation~citation_composite']:.3f} | "
            f"{r['diff_vs_incumbent_ci95'][0]:+.3f} to {r['diff_vs_incumbent_ci95'][1]:+.3f}")


def cmd_composite(a) -> int:
    lock = load()
    res, stored, obj, by = reproduce()
    print(f"GATE PASSED: S376b's Table A reproduced for all {len(stored['all_answers'])} judges (every value within "
          f"{TOL}); {MLX}: {fmt(res[MLX])}", flush=True)
    if a.dry_run:
        print(f"dry run: would read {a.check_dir / 'repro_check.json'} and repro_check_rows.jsonl, and write "
              f"{OUT_JSON.relative_to(ROOT)} and .md")
        return 0
    rows = check_rows(a.check_dir, lock)
    out = table_a(by, obj, {GGUF: rows})
    if gate(out, stored["all_answers"]):
        raise SystemExit("REFUSED: adding the GGUF build changed another judge's numbers")
    c = json.loads((a.check_dir / "repro_check.json").read_text())
    prov = {"script": "scripts/S483_second_judge.py composite", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "lock_sha256": lock.sha256,
            "inputs": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha_file(p)
                       for p in (S376_LEDGER, S376_ANALYSIS, a.check_dir / "repro_check.json",
                                 a.check_dir / "repro_check_rows.jsonl")},
            "check": {k: c.get(k) for k in ("model", "model_digest", "server", "ollama_version", "options_sent",
                                             "fields_sent", "machine_identity")},
            "method": "S376b Table A (all 107 answers): composite = mean of three Pearson r; 2,000 resamples, seed "
                      "20261009; the GGUF build's rows from the D85 check (both passes equal)"}
    doc = {"_provenance": prov, "gguf": out[GGUF], "mlx": out[MLX], "devstral": out["devstral-small-2:24b"],
           "incumbent": out[s376b().INCUMBENT]}
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    hdr = "| Judge | Scored | Composite (95% CI) | Corr~sim | Compl~recall | Cite~cite | Diff vs qwen3-coder (95% CI) |"
    md = ["# S483: the second judge's composite on the 107 calibration answers (D85, D92 Q198)", "",
          f"Provenance: `{json.dumps(prov['inputs'])}`; lock {lock.sha256}; check {c.get('model')} digest "
          f"{c.get('model_digest')} on {c.get('server')}, Ollama {c.get('ollama_version')}, machine "
          f"{(c.get('machine_identity') or {}).get('machine')}.", "",
          "S376b's Table A was reproduced for all 22 judges before this was written. The GGUF build's scores are the "
          "D85 check's (both passes equal), at the lock's [judge] settings; the MLX build's are S376's (num_ctx 32,768, "
          "num_predict 8,192, temperature 0, think false; the Studio, Ollama 0.40.1 and 0.40.2).", "",
          hdr, "|---|---:|---|---:|---:|---:|---|"]
    for name, r in ((GGUF, out[GGUF]), (MLX, out[MLX]), ("devstral-small-2:24b", out["devstral-small-2:24b"])):
        md.append(f"| {name} | {r['n_scored']}/{r['n_calls']} | " + fmt(r) + " |")
    OUT_MD.write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


# ---------------------------------------------------------------- d85

def second_call(lock):
    second = lock.d["judge"].get("second_model")
    if not second:
        raise SystemExit("REFUSED: LOCK.toml [judge] names no second_model")
    return second, lock.ollama(second, role="judge")


def cmd_d85(a) -> int:
    lock = load()
    second, call = second_call(lock)
    row = lock.d["models"].get(second) or {}
    machines = row.get("machines", [])
    here = this_machine()
    ck = D / "out" / f"check_second_{a.port}"
    env = {"S3_REPO": str(ROOT), "S3_PORT": str(a.port), "S3_JUDGE": "second", "S3_CHECK_ONLY": "1",
           "S3_SET": "G1", **MACHINE_ENV.get(here, {})}
    import lock_equiv                                       # D204: the lock as D88's but for the second judge's machines
    if not lock_equiv.accepts(lock.path):
        raise SystemExit(f"REFUSED: experiments/LOCK.toml: {lock_equiv.why_not(lock.path.read_text())}")
    env["S3_LOCK_WANT"] = lock.sha256
    live = " ".join(f"{k}='{v}'" if any(ch in v for ch in "|\\ ") else f"{k}={v}" for k, v in env.items()) \
        + " bash findings/recompute/S3_runs/run_s3.sh"
    if not a.dry_run:
        if here not in machines:
            raise SystemExit(f"REFUSED: {second} runs on {machines} under lock {lock.sha256[:8]}; this machine is {here}")
        print(f"D85 live: {live}", flush=True)
        os.chdir(ROOT)
        os.execvpe("bash", ["bash", "findings/recompute/S3_runs/run_s3.sh"], {**os.environ, **env})
    import S376_judge_calibration as S376
    import S141_runner.judge as J
    raw = tomllib.loads(lock.path.read_text())
    items = S376.answers_and_key()
    prompts = [J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"], x["answerable"], None)
               for x in items]
    bodies = [call.payload(p) for p in prompts]
    sent = {k: v for k, v in bodies[0].items() if k != "prompt"}
    want_opts = {"num_ctx": raw["generation"]["num_ctx"], "num_predict": raw["judge"]["num_predict"],
                 "num_batch": raw["generation"]["num_batch"], "temperature": raw["judge"]["temperature"]}
    same = all({k: v for k, v in b.items() if k != "prompt"} == sent for b in bodies) and sent["options"] == want_opts \
        and sent.get("think") is False and "system" not in sent and "seed" not in sent["options"]
    print(f"lock {lock.sha256} (status {lock.d['status']}); [judge] second_model {second}; [models] digest {row.get('digest')}, "
          f"machines {machines}; this machine: {here}" + ("" if here in machines else " (a live run is refused here)"))
    print(f"[judge] settings sent by each of the 214 requests (2 passes x {len(items)}): {json.dumps(sent)}; equal to "
          f"LOCK.toml read directly, no seed, no system prompt, think false: {same}")
    print(f"the 107 calibration answers: {len(items)} (answerable {sum(x['answerable'] for x in items)}), prompts "
          f"{min(map(len, prompts)):,} to {max(map(len, prompts)):,} characters, sha256 of all {hashlib.sha256(''.join(prompts).encode()).hexdigest()[:16]}")
    st = "absent" if not (ck / "repro_check.json").exists() else json.loads((ck / "repro_check.json").read_text()).get("passed")
    print(f"check dir {ck.relative_to(ROOT)}: {st}")
    res, stored, _, _ = reproduce()
    print(f"composite gate: S376b's Table A reproduced for all {len(stored['all_answers'])} judges; {MLX} {fmt(res[MLX])}")
    s = [json.loads(x) for x in S440_BEELINK.read_text().splitlines() if x.strip()]
    s = [r for r in s if r["pass"] == "lock"]
    dev = sum(r["wall_s"] for r in s) / len(s)
    by, _ = current_ledger()
    q = {r["answer_key"]: r["wall_s"] for r in by[MLX]}
    d = {r["answer_key"]: r["wall_s"] for r in by["devstral-small-2:24b"]}
    ratio = sum(q[k] for k in q if k in d) / sum(d[k] for k in q if k in d)
    print(f"estimate (UNVERIFIED): devstral on the Beelink at the lock {dev:.1f} s a call (S440, {len(s)} calls) x "
          f"{ratio:.2f} (the MLX build's time over devstral's on the same 107, S376, the Studio) = {dev * ratio:.1f} s; "
          f"214 calls about {214 * dev * ratio / 3600:.1f} h, plus two fresh loads")
    print(f"live (the Beelink, once no K1 worker runs there; from this clone): uv run --frozen python scripts/S483_second_judge.py d85")
    print(f"  which runs: {live}")
    print("D85 DRY RUN: no server contact, nothing written" + ("" if same else "; SETTINGS DIFFER"))
    return 0 if same else 1


# ---------------------------------------------------------------- g1-status

def g1_status(outs: list[Path], ck: Path, lock, plan_left=None) -> tuple[list[str], dict]:
    """Problems and facts of the second judge's G1 run in outs (each a set out: judge/<run>/...)."""
    second, call = second_call(lock)
    tag = {"which": "second", "model": second, "digest": call.digest}
    probs, facts = [], {}
    f = ck / "repro_check.json"
    c = json.loads(f.read_text()) if f.exists() else {}
    if not (c.get("passed") is True and c.get("judge") == "second" and c.get("model") == second
            and c.get("lock_sha256") == lock.sha256):
        probs.append(f"check {f}: not a passed D85 check of {second} under this lock")
    rows, runs, n_hdr, rech = [], set(), 0, []
    for o in outs:
        for jf in sorted(o.glob("judge/*/judge_passages.jsonl")):
            latest = {}
            for r in map(json.loads, filter(str.strip, jf.read_text().splitlines())):
                if r.get("judge") != tag:
                    probs.append(f"{jf}: a row not naming {second} with digest {call.digest[:12]}")
                    break
                if r.get("lock_sha256") != lock.sha256:
                    probs.append(f"{jf}: a row under lock {str(r.get('lock_sha256'))[:8]}")
                    break
                dg = (r.get("a") or {}).get("model_digest")
                if dg and not call.digest.startswith(dg[:12]):
                    probs.append(f"{jf}: a call answered by digest {dg[:12]}")
                    break
                runs.add(r.get("run_sha256"))
                latest[(r.get("run_id"), r["config"], r["question_id"], r["draw"])] = r
            rows += latest.values()
            for h in map(json.loads, filter(str.strip, (jf.parent / "judge_passages_headers.jsonl").read_text().splitlines())
                         if (jf.parent / "judge_passages_headers.jsonl").exists() else []):
                n_hdr += 1
                if h.get("model") != second:
                    probs.append(f"{jf.parent}: a header names {h.get('model')}")
            rs = jf.parent / "judge_passages_recheck_summary.json"
            if rs.exists():
                rech.append(json.loads(rs.read_text()).get("passed"))
    if len(runs) > 1:
        probs.append(f"{len(runs)} run_sha256 values across the outs (one lock, code and judge expected)")
    if any(x is False for x in rech):
        probs.append(f"{sum(x is False for x in rech)} unit recheck(s) not passed")
    ok = [r for r in rows if r["a"]["status"] == "ok"]
    walls = sorted(r["a"].get("wall_s") or 0 for r in ok)
    facts.update(rows=len(rows), status_a=dict(Counter(r["a"]["status"] for r in rows)), headers=n_hdr,
                 rechecks=dict(Counter(map(str, rech))), by_config=dict(Counter(r["config"] for r in rows)),
                 mean_a_wall_s=round(sum(walls) / len(walls), 1) if walls else None)
    if plan_left is not None:
        facts["left"] = plan_left
        if facts["mean_a_wall_s"]:
            facts["hours_left_at_this_pace"] = round(plan_left * facts["mean_a_wall_s"] / 3600, 1)
    return probs, facts


def plan_to_do(set_name: str, out: Path, ck: Path, phases: str) -> int | None:
    """s3_guard.py plan --judge second, offline: the answers left to judge in the set's phases (None: no inputs)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("s3_guard_s483", D / "s3_guard.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    inputs = g.home(g.SETS[set_name]["inputs"])
    if not inputs.exists():
        return None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = g.plan(set_name, inputs.resolve(), out, phases, ck, None, None, "second")
    tot = next((json.loads(x)["total"] for x in buf.getvalue().splitlines() if x.startswith('{"total')), None)
    if rc != 0 or tot is None:
        raise SystemExit(f"REFUSED: s3_guard.py plan --judge second refused {set_name}: {buf.getvalue()[-300:]}")
    return tot["to_do"]


def cmd_g1_status(a) -> int:
    lock = load()
    ck = D / "out" / f"check_second_{a.port}"
    outs = [D / "out_g1r15_second", D / "out_second"]
    left = 0
    for s, o in (("G1R15", outs[0]), ("G1", outs[1])):
        n = plan_to_do(s, o, ck, a.phases)
        print(f"{s}: {'no inputs here' if n is None else f'{n} answers left to judge (phases {a.phases})'}")
        left += n or 0
    probs, facts = g1_status(outs, ck, lock, left)
    print(json.dumps(facts))
    print("G1 SECOND JUDGE: " + ("OK" if not probs else f"{len(probs)} PROBLEMS: " + "; ".join(probs[:5])))
    return 0 if not probs else 1


# ---------------------------------------------------------------- selftest

def module_with(old: str | None = None, new: str | None = None):
    """This script as a module, or a mutant with one passage changed (it must occur once)."""
    src = Path(__file__).read_text()
    if old is not None:
        assert src.count(old) == 1, f"mutant anchor not found once: {old[:60]!r}"
        src = src.replace(old, new)
    import types
    m = types.ModuleType("s483_mut")
    m.__file__ = __file__
    exec(compile(src, __file__, "exec"), m.__dict__)
    return m


def cmd_selftest(a) -> int:
    import tempfile
    results = []

    def check(name, ok):
        results.append(bool(ok))
        print(f"{'PASS' if ok else 'FAIL'}  {name}", flush=True)

    lock = load()
    second, call = second_call(lock)
    tmp = Path(tempfile.mkdtemp(prefix="s483_"))
    _, stored, obj, by = reproduce()
    check("gate: S376b's Table A reproduced for all 22 judges from the ledger and the stored reference measures", True)

    def fake_check(d: Path, rows, **over):
        d.mkdir(parents=True, exist_ok=True)
        rep = {"passed": True, "full_sample": True, "judge": "second", "model": second, "n": 107, "equal_scores": 107,
               "lock_sha256": lock.sha256} | over
        (d / "repro_check.json").write_text(json.dumps(rep))
        (d / "repro_check_rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        return d

    mlx_rows = [{"answer_key": r["answer_key"], "scores": r["scores"], "first_scores": r["scores"], "equal": True}
                for r in by[MLX]]
    ck = fake_check(tmp / "ck_mlx", mlx_rows)

    def as_gguf(m, d):
        rows = m.check_rows(d, lock)
        return m.table_a(by, obj, {GGUF: rows})[GGUF]
    g = as_gguf(sys.modules[__name__], ck)
    s = stored["all_answers"][MLX]
    check(f"the composite path fed the MLX build's own 107 rows as a check gives its stored {s['composite']:.3f} "
          f"({s['ci95'][0]:.3f} to {s['ci95'][1]:.3f}) and its difference interval",
          not gate({MLX: g}, {MLX: s}))
    m1 = module_with("    rng = np.random.default_rng(B.SEED if seed is None else seed)\n",
                     "    rng = np.random.default_rng(1)\n")
    check("mutant (another bootstrap seed): that case fails", gate({MLX: as_gguf(m1, ck)}, {MLX: s}))
    m2 = module_with('        ok = [r for r in rows if r["scores"] is not None and r["answer_key"] in obj]\n',
                     '        ok = [r for r in rows if r["scores"] is not None and r["answer_key"] in obj][:100]\n')
    check("mutant (not every scored answer used): that case fails", gate({MLX: as_gguf(m2, ck)}, {MLX: s}))
    one = [dict(r) for r in mlx_rows]
    one[0] = {**one[0], "scores": {**one[0]["scores"], "correctness": (one[0]["scores"]["correctness"] + 1) % 6},
              "first_scores": {**one[0]["scores"], "correctness": (one[0]["scores"]["correctness"] + 1) % 6}}
    check("one score changed in the check: the composite moves (it reads the check's scores)",
          abs(as_gguf(sys.modules[__name__], fake_check(tmp / "ck_one", one))["composite"] - s["composite"]) > 1e-6)

    def refused(d):
        try:
            check_rows(d, lock)
            return False
        except SystemExit as e:
            return str(e).startswith("REFUSED")
    differ = [dict(r) for r in mlx_rows]
    differ[3] = {**differ[3], "equal": False, "first_scores": {**differ[3]["scores"], "completeness": 0}}
    check("a check not passed, of the main judge, under another lock, or whose two passes differ: refused",
          refused(fake_check(tmp / "ck_np", mlx_rows, passed=False))
          and refused(fake_check(tmp / "ck_main", mlx_rows, judge=None, model=lock.d["judge"]["model"]))
          and refused(fake_check(tmp / "ck_lock", mlx_rows, lock_sha256="0" * 64))
          and refused(fake_check(tmp / "ck_diff", differ)) and refused(tmp / "ck_none"))
    m3 = module_with("    differ = [r[\"answer_key\"] for r in rows if not r[\"equal\"] or r[\"scores\"] != r[\"first_scores\"] "
                     "or r[\"scores\"] is None]\n", "    differ = []\n")
    check("mutant (passes that differ not refused): that case fails",
          _not_refused(m3, fake_check(tmp / "ck_diff3", differ), lock))

    # g1-status on a synthetic out
    tag = {"which": "second", "model": second, "digest": call.digest}
    ckd = fake_check(tmp / "ck_g1", mlx_rows)

    def out_with(name, rows, recheck=True):
        u = tmp / name / "judge" / "exp_01__single_pass__exp_v4_s20_n0"
        u.mkdir(parents=True, exist_ok=True)
        (u / "judge_passages.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (u / "judge_passages_headers.jsonl").write_text(json.dumps({"model": second}) + "\n")
        (u / "judge_passages_recheck_summary.json").write_text(json.dumps({"passed": recheck}))
        return tmp / name
    base = {"run_id": "r", "config": "single_pass", "draw": 1, "run_sha256": "x", "lock_sha256": lock.sha256,
            "judge": tag, "a": {"status": "ok", "wall_s": 20.0, "model_digest": call.digest}}
    good = [base | {"question_id": f"Q{i}"} for i in range(4)]
    p0, f0 = g1_status([out_with("o_good", good)], ckd, lock, 10)
    check("g1-status on rows that all name the second judge, one run_sha256, recheck passed: no problem; the pace "
          "20 s and 10 answers left give 0.1 h", p0 == [] and f0["rows"] == 4 and f0["hours_left_at_this_pace"] == 0.1)
    bad1 = good[:3] + [{k: v for k, v in good[3].items() if k != "judge"}]
    bad2 = good[:3] + [good[3] | {"run_sha256": "y"}]
    p1, _ = g1_status([out_with("o_b1", bad1)], ckd, lock)
    p2, _ = g1_status([out_with("o_b2", bad2)], ckd, lock)
    p3, _ = g1_status([out_with("o_b3", good, recheck=False)], ckd, lock)
    p4, _ = g1_status([out_with("o_b4", good)], tmp / "no_check", lock)
    check("g1-status flags a row without the second judge's name, a second run_sha256, a failed recheck, and a "
          "missing check", all(len(p) == 1 for p in (p1, p2, p3, p4)))
    m4 = module_with("                if r.get(\"judge\") != tag:\n", "                if False:\n")
    check("mutant (rows not checked for the judge's name): that case fails",
          m4.g1_status([out_with("o_b5", bad1)], ckd, lock)[0] == [])
    n, t = sum(results), len(results)
    print(f"S483 SELFTEST: {n}/{t}")
    return 0 if n == t else 1


def _not_refused(m, d, lock) -> bool:
    try:
        m.check_rows(d, lock)
        return True
    except SystemExit:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("d85")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    c = sub.add_parser("composite")
    c.add_argument("--check-dir", type=Path, default=D / "out" / f"check_second_{DEFAULT_PORT}")
    c.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("g1-status")
    s.add_argument("--port", type=int, default=DEFAULT_PORT)
    s.add_argument("--phases", default="1 2")
    sub.add_parser("selftest")
    a = ap.parse_args()
    return {"d85": cmd_d85, "composite": cmd_composite, "g1-status": cmd_g1_status, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
