#!/usr/bin/env python3
"""S518 - D195: the confirmatory test of the question-type split, fixed before its rows were read.

WHY. On Gemini 3 Flash, judged by devstral, RLM-10 loses to single pass on the one-paper questions and beats it on the
many-paper ones (S511, exploratory, split after looking; Rule 8 does not name it). D195 (Valerio, 1 November) states that
split as a hypothesis before anyone reads the second judge's rows on those answers or the local generators' rows, so the
prediction can fail. Valerio has seen none of the rows this script reads in `run`. Every value below was fixed by D195;
a change is a departure and carries a new decision.

THE HYPOTHESIS. Pass = judge correctness 4 or more, on the 86 answerable questions (Rule 8) as far as a source covers them.
For one source, per question, p(arm) is the arm's share over its draws (S511.shares; Rule 10, a failed answer is a fail;
a judge failure counts in neither direction) and d = p(rlm_10) - p(single_pass). D_one and D_many are the means of d over
the one-paper and many-paper questions (S511.questions), and I = D_many - D_one.
  Predicted: D_one < 0, D_many > 0, I > 0.
  Primary reading for a source, on I only: its 95% interval excludes 0 above zero: "agrees"; excludes 0 below zero:
  "opposite"; contains 0: "not shown". "Not shown" is never read as "does not hold".
  The interval: Rule 2's percentiles, 10,000 resamples, the questions of each type resampled apart (S518.interaction).
  D_one and D_many carry Rule 2's interval and the exact sign-flip P, descriptive.
  Rows on the final key: a key v2.5 row where one exists, else the source's v2.4 row, for a key that did not change.
  Every source is reported, whatever it shows. No pooled verdict across sources, no multiplicity correction: three test
  sources, read one by one, as stated here.

THE SOURCES (SOURCES below). "test": second_judge (qwen3.8:27b on Flash's answers), gemma3, qwen3-coder: rows nobody had
read on the day of D195. The local generators' RLM runs hold D98's 45 questions, so they carry 20 one-paper and 9 many-paper
questions, and a wide interval is expected. "beside": claude-haiku-4-5 and gemini-2.5-pro: Valerio has not seen them, but
an agent read gemini-2.5-pro's draw 1 and another noted Haiku as partly read on 1 November (RUNNING.md, D195), so they are
reported beside the test, labelled, and they count for nothing in it. The questions are the same in every source: this
tests generators and judges, not new questions. No human rating is read; S08b is untouched.

REPRODUCE FIRST (README.md:75-79). `gate` recomputes Flash under devstral on key v2.4 from the frozen rows and refuses unless
D_one and D_many, with their intervals, equal S511's committed pairs. `run` runs the gate first and refuses unless this
file is committed and unchanged and D195 stands in experiments/README.md.

    uv run --frozen python scripts/S518_split_confirmation.py gate
    uv run --frozen python scripts/S518_split_confirmation.py run --source gemma3 --collect <v2.5 collect.jsonl> [--base <v2.4 collect.jsonl>]

writes findings/recompute/S518_split_confirmation/<source>.json. The rows are read only here. `run` is not to be used
before Valerio says so.

Note of 2 November 2026 (D201 Q8, Valerio: yes; dated note under D195 in experiments/README.md). The result now stores,
under "inputs", each file `run` reads: the --collect and --base files, and what the gate and the questions read (the G1
collect, S511's results.json, the D5 key, S511's source). Each entry holds its role, its path (relative to the
repository when inside it, else as given) and its sha256, taken before the read, and `run` refuses if the file changed
by the end. `run` also refuses unless S511's source, which this script imports, is committed and unchanged, as this
file is. Nothing is copied yet. No hypothesis, source, threshold, interval or reading changed. Every line above stands.

Note of 4 November 2026 (D235 Q4, Valerio: "Q4: yes"). Figure 3e gets a reference row: Gemini 3 Flash judged by devstral
on key v2.5, the generator whose split S511 found and D195 set out to confirm. It is not a source of the test: SOURCES,
the hypothesis, the readings and `gate` are unchanged, and the row counts for nothing in the test. `reference` reads
fixed files only: the base is the G1 collect `gate` reads (key v2.4, held to S511.G1_COLLECT_SHA) and the collect is
fig3_s6_inputs/s6_g1_collect.jsonl (key v2.5 on the changed questions, S512 out_s6_g1 with out_s6_g1r15 replacing, held
to that folder's SHA256SUMS), merged as `run` merges a source (the v2.5 row where one exists). Questions, draws, arms,
threshold and statistic are `run`'s. Reproduce first: D_one and D_many with their intervals, question counts and sign-flip
P must equal S511's committed key v2.5 pairs (results.json "v25" "pairs", RLM-10 against single pass, both halves),
or it refuses and writes nothing. I and its reading are then the new numbers. `reference --dry` prints the result and
writes nothing; without --dry it refuses unless this file and S511 are committed and unchanged, D195 and D235 stand in
experiments/README.md, and it writes findings/recompute/S518_split_confirmation/gemini-3-flash-preview.json.

    uv run --frozen python scripts/S518_split_confirmation.py reference [--dry]

Note of 4 November 2026 (D241 (1), Valerio: "Ok, do it"). The local generators' RLM-10 answered D98's 45 only, so their
many-paper half held 9 questions. T2X (findings/recompute/T2X_runs/) answers the other 17 many-paper questions with
gemma3:27b and qwen3-coder:30b, rlm_10 at draw 1 (seed 1), judged by devstral on key v2.5 (scripts/S574_t2x_judge_v25.py,
sets t2xgemma and t2xqcoder). `run --t2x <collect>` adds those rows to a local source: only for gemma3 and qwen3-coder;
the file's rows must be key v2.5, under one lock that scripts/lock_equiv.py proves equal to D88's, one run_sha256, run
ids of the source's generator, draw 1, and questions among t2x_questions.json's 17 (sha256 pinned); its rlm_10 rows
are read, and a key already held by --collect or --base is refused, never replaced. Its single_pass rows are not read
and are counted ("t2x_single_pass_not_read"): T2's single_pass already holds draws 1 to 3 of these 17 questions for both
generators on key v2.5 (S518_inputs/<source>/collect.jsonl), and a T2X single_pass row is a second answer to a key T2
answered under the same seed. The many-paper half then has 26 questions (9 with RLM-10 at draws 1 to 3, 17 at draw 1;
single pass at draws 1 to 3 for all 26), the one-paper half its 20, unchanged. p(arm) stays the share over the draws a
source holds (`shares`, unchanged). The hypothesis, the threshold, the statistics, the readings and `gate` are unchanged;
`gate` still runs first and refuses as before. Without --t2x nothing changes.

    uv run --frozen python scripts/S518_split_confirmation.py run --source gemma3 --collect <v2.5 collect.jsonl> --t2x <T2X collect.jsonl>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("S511", ROOT / "scripts" / "S511_g2_matched_budget.py")
S511 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S511)

SCRIPT = "scripts/S518_split_confirmation.py"
S511_SCRIPT = "scripts/S511_g2_matched_budget.py"
OUT = ROOT / "findings" / "recompute" / "S518_split_confirmation"
DECISION = "**D195**"
A, B = "rlm_10", "single_pass"
THRESHOLD = 4
SOURCES = {"second_judge": "test", "gemma3": "test", "qwen3-coder": "test",
           "claude-haiku-4-5": "beside", "gemini-2.5-pro": "beside"}
N_BOOT, SEED, PCT, TOL = S511.N_BOOT, S511.SEED, S511.PCT, S511.TOL
# D235 Q4: the reference row (not a source of the test). Flash, devstral, key v2.5 where a row exists, else v2.4.
REFERENCE, REF_ROLE, REF_KEY, REF_DECISION = "gemini-3-flash-preview", "reference", "v2.5", "**D235**"
REF_BASE = S511.RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl"        # held to S511.G1_COLLECT_SHA, as `gate` holds it
REF_COLLECT = S511.RECOMPUTE / "fig3_s6_inputs" / "s6_g1_collect.jsonl"  # held to that folder's SHA256SUMS (S528)
REF_COLLECT_SHA = "2a79dc76e87e362513b414776c39873c068466195c23ce979a439afad46462d3"  # and to its committed sha256 (SHA256SUMS:575 at ad7c5f69)
# D241: T2X's rows for the two local sources (--t2x). The source -> exp_01's generator tag of its run ids.
T2X_SOURCES = {"gemma3": "gemma3-27b", "qwen3-coder": "qwen3-coder-30b"}
T2X_DECISION = "**D241**"
T2X_QUESTIONS = S511.RECOMPUTE / "T2X_runs" / "t2x_questions.json"
T2X_QUESTIONS_SHA = "1943af5bc2ef4fca5c116b00050580fe7031c9d0c35d23546144d4422c18822c"  # t2x_check.py questions --write
T2X_DRAW = 1


class Refused(RuntimeError):
    pass


def counts(n: int, seed: int):
    """Resample counts for n questions, one stream per type (S511.resample_counts holds a single seed)."""
    import numpy as np
    idx = np.random.default_rng(seed).integers(0, n, size=(N_BOOT, n))
    flat = np.bincount((idx + n * np.arange(N_BOOT)[:, None]).ravel(), minlength=N_BOOT * n)
    return flat.reshape(N_BOOT, n).astype(float)


def interaction(d_one: list, d_many: list) -> tuple[float, float, float]:
    """I = mean(d_many) - mean(d_one) and its 2.5 and 97.5 percentiles, each type's questions resampled apart."""
    import numpy as np
    x, y = np.array([float(v) for v in d_one]), np.array([float(v) for v in d_many])
    a = counts(len(x), SEED) @ x / len(x)
    b = counts(len(y), SEED + 1) @ y / len(y)
    lo, hi = np.percentile(b - a, PCT)
    return float(y.mean() - x.mean()), float(lo), float(hi)


def reading(lo: float, hi: float) -> str:
    return "agrees" if lo > 0 else "opposite" if hi < 0 else "not shown"


def read_rows(path: Path, qs: dict) -> dict:
    """{(config, question, draw): (cell, key_version)} from an s3_guard collect file, for the two arms, as
    S511.read_collect makes a cell. Refuses a doubled row, a wrong prompt and a second lock."""
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    if len({r.get("lock_sha256") for r in rows}) != 1:
        raise Refused(f"{path}: rows under more than one lock")
    out = {}
    for r in rows:
        c, q, d = r["config"].split("+")[0], r["question_id"], int(r["draw"])
        if c not in (A, B) or q not in qs or qs[q]["kind"] not in ("one", "many"):
            continue
        k = (c, q, d)
        if k in out:
            raise Refused(f"{path}: {k} doubled")
        if not r.get("answerable_prompt"):
            raise Refused(f"{path}: {k} judged with the not-answerable prompt")
        st = (r.get("a") or {}).get("status")
        if st == "ok":
            v = (r["a"].get("scores") or {}).get("correctness")
            cell = {"kind": "scored", "score": v} if isinstance(v, (int, float)) and not isinstance(v, bool) \
                else {"kind": "unscored", "why": "ok, no score"}
        elif st == "no_answer":
            cell = {"kind": "failed"}
        elif st in S511.JUDGE_FAILED:
            cell = {"kind": "unscored", "why": st}
        else:
            raise Refused(f"{path}: {k} (a) status {st!r}")
        out[k] = (cell, r.get("key_version"))
    return out


def merge(base: dict, over: dict) -> tuple[dict, dict]:
    """The final key: the v2.5 row where one exists, else the base row. Refuses a v2.4 row in `over`."""
    if any(v[1] != "v2.5" for v in over.values()):
        raise Refused("--collect holds a row that is not key v2.5")
    cells = {k: v[0] for k, v in base.items()}
    cells.update({k: v[0] for k, v in over.items()})
    return cells, {"base_rows": len(base), "v25_rows": len(over), "rows_used": len(cells)}


def shares(cells: dict, qids: list) -> dict:
    """{arm: {q: Fraction or None}}: S511.shares' reading over the draws a source holds (a local RLM run has every draw
    of D98's 45, a generator's other draws may be absent)."""
    out = {}
    for c in (A, B):
        out[c] = {}
        for q in qids:
            k = n = 0
            for (cc, qq, _d), cell in cells.items():
                if cc != c or qq != q:
                    continue
                if cell["kind"] == "scored":
                    k, n = k + int(cell["score"] >= THRESHOLD), n + 1
                elif cell["kind"] == "failed":
                    n += 1
            out[c][q] = Fraction(k, n) if n else None
    return out


def diffs(sh: dict, qids: list) -> dict:
    return {q: sh[A][q] - sh[B][q] for q in qids if sh[A][q] is not None and sh[B][q] is not None}


def analyse(cells: dict, qs: dict) -> dict:
    ones = [q for q, v in qs.items() if v["kind"] == "one"]
    manys = [q for q, v in qs.items() if v["kind"] == "many"]
    sh = shares(cells, ones + manys)
    d1, d2 = diffs(sh, ones), diffs(sh, manys)
    if not d1 or not d2:
        raise Refused(f"no question of a type is covered: one-paper {len(d1)}, many-paper {len(d2)}")
    res = {}
    for name, d in (("one_paper", d1), ("many_paper", d2)):
        v = list(d.values())
        lo, hi = S511.interval([float(x) for x in v], [1.0] * len(v))
        res[name] = {"questions": len(v), "d": float(sum(v, Fraction(0)) / len(v)), "lo": lo, "hi": hi,
                     "p_signflip_exact_two_sided": S511.signflip_p(v)}
    i, lo, hi = interaction(list(d1.values()), list(d2.values()))
    res["interaction"] = {"I": i, "lo": lo, "hi": hi, "reading": reading(lo, hi)}
    return res


def gate() -> dict:
    """Flash, devstral, key v2.4, three draws: D_one and D_many with their intervals against S511's committed pairs."""
    qs = S511.questions()
    p = S511.RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl"
    if S511.sha256_file(p) != S511.G1_COLLECT_SHA:
        raise Refused("g1_collect.jsonl is not the frozen file")
    got = analyse({k: v[0] for k, v in read_rows(p, qs).items()}, qs)
    want = json.loads((S511.OUT / "results.json").read_text())["pairs"][str(THRESHOLD)]
    for name, key in (("one_paper", "one-paper"), ("many_paper", "many-paper")):
        w = [x for x in want[key] if {x["a"], x["b"]} == {A, B}]
        if len(w) != 1:
            raise Refused(f"S511 results hold no single {A} against {B} pair for {key}")
        w = w[0]
        sign = 1 if w["a"] == A else -1
        wd, (wl, wh) = sign * w["d"], sorted((sign * w["lo"], sign * w["hi"]))
        g = got[name]
        if g["questions"] != w["questions"] or any(abs(a - b) > TOL for a, b in ((g["d"], wd), (g["lo"], wl), (g["hi"], wh))):
            raise Refused(f"gate: {name} {g} is not S511's {wd}, {wl}, {wh}")
    return got


def summed_sha(path: Path) -> str | None:
    """The sha256 the folder's SHA256SUMS records for this file, or None."""
    sums = Path(path).parent / "SHA256SUMS"
    if not sums.is_file():
        return None
    for line in sums.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == Path(path).name:
            return parts[0]
    return None


def reference_cells(qs: dict, base: Path = None, collect: Path = None) -> tuple[dict, dict]:
    """D235 Q4: Flash's cells on the final key, merged as `run` merges a source. Refuses a base that is not the frozen G1
    collect or a collect whose sha256 is not the one its folder's SHA256SUMS records."""
    base, collect = base or REF_BASE, collect or REF_COLLECT
    if S511.sha256_file(base) != S511.G1_COLLECT_SHA:
        raise Refused(f"{Path(base).name} is not the frozen G1 collect")
    want = summed_sha(collect)
    if want is None or S511.sha256_file(collect) != want:
        raise Refused(f"{Path(collect).name} is not the file its folder's SHA256SUMS records")
    if want != REF_COLLECT_SHA:
        raise Refused(f"{Path(collect).name} is not the pinned v2.5 collect ({REF_COLLECT_SHA[:8]})")
    return merge(read_rows(base, qs), read_rows(collect, qs))


def reference_gate(got: dict, results: Path = None) -> str:
    """D235 Q4, reproduce first: D_one and D_many on key v2.5, with interval, question count and sign-flip P, equal
    S511's committed key v2.5 pairs (results.json "v25", RLM-10 against single pass). Returns what was reproduced."""
    want = json.loads(Path(results or S511.OUT / "results.json").read_text()).get("v25", {}).get("pairs", {}).get(str(THRESHOLD))
    if not want:
        raise Refused("S511 results hold no key v2.5 pairs")
    said = []
    for name, key in (("one_paper", "one-paper"), ("many_paper", "many-paper")):
        w = [x for x in want.get(key, []) if {x["a"], x["b"]} == {A, B}]
        if len(w) != 1:
            raise Refused(f"S511's key v2.5 results hold no single {A} against {B} pair for {key}")
        w = w[0]
        sign = 1 if w["a"] == A else -1
        wd, (wl, wh), wp = sign * w["d"], sorted((sign * w["lo"], sign * w["hi"])), w["p_signflip_exact_two_sided"]
        g = got[name]
        if g["questions"] != w["questions"] or any(abs(a - b) > TOL for a, b in
                                                    ((g["d"], wd), (g["lo"], wl), (g["hi"], wh),
                                                     (g["p_signflip_exact_two_sided"], wp))):
            raise Refused(f"reference: {name} {g} is not S511's key v2.5 {wd}, {wl}, {wh}, P {wp}")
        said.append(f"{key} {wd:+.6f} [{wl:+.6f}, {wh:+.6f}], n {w['questions']}, P {wp:.3g}")
    return "S511 results.json v25.pairs['4'] rlm_10 against single_pass: " + "; ".join(said)


def t2x_ids(path: Path = None) -> set:
    """D241: the 17 questions of T2X, under the pin."""
    path = Path(path or T2X_QUESTIONS)
    if S511.sha256_file(path) != T2X_QUESTIONS_SHA:
        raise Refused(f"{path.name} is not the pinned T2X questions file ({T2X_QUESTIONS_SHA[:8]})")
    ids = json.loads(path.read_text())["ids"]
    if len(ids) != 17 or len(set(ids)) != 17:
        raise Refused(f"{path.name} names {len(set(ids))} questions, not D241's 17")
    return set(ids)


def t2x_cells(path: Path, qs: dict, source: str, held: set, qfile: Path = None) -> tuple[dict, dict]:
    """D241: T2X's rlm_10 cells for a local source (module docstring, note of 4 November), and what was read.
    held: the keys --collect and --base give; a T2X key among them is refused."""
    import lock_equiv
    if source not in T2X_SOURCES:
        raise Refused(f"--t2x is for {', '.join(T2X_SOURCES)} only, not {source}")
    ids = t2x_ids(qfile)
    raw = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    if not raw:
        raise Refused(f"{path}: no rows")
    locks, shas = {r.get("lock_sha256") for r in raw}, {r.get("run_sha256") for r in raw}
    if len(locks) != 1 or not locks <= lock_equiv.EQUIVALENT:
        raise Refused(f"{path}: rows under {sorted(str(x)[:8] for x in locks)}, not one lock lock_equiv accepts")
    if len(shas) != 1:
        raise Refused(f"{path}: rows under {len(shas)} run_sha256, not one")
    import tomllib
    lock = tomllib.loads((ROOT / "experiments" / "LOCK.toml").read_text())
    judge_digest = lock["models"][lock["judge"]["model"]]["digest"]
    for r in raw:
        c = r["config"].split("+")[0]
        if (r.get("a") or {}).get("model_digest") != judge_digest:
            raise Refused(f"{path}: a row not scored by the main judge {lock['judge']['model']} ({judge_digest[:8]}): "
                          "the second judge's collect is not read here")
        if not str(r.get("questions", "")).startswith("whole:t2x"):
            raise Refused(f"{path}: a row of set {r.get('questions')}, not a T2X set")
        if not str(r.get("run_id", "")).endswith("+" + T2X_SOURCES[source]):
            raise Refused(f"{path}: run {r.get('run_id')} is not {source}'s")
        if c not in (A, B) or r["question_id"] not in ids or int(r["draw"]) != T2X_DRAW:
            raise Refused(f"{path}: {(c, r['question_id'], r['draw'])} is not T2X's (rlm_10 or single_pass, the 17, draw 1)")
    rows = read_rows(Path(path), qs)
    if any(v[1] != "v2.5" for v in rows.values()):
        raise Refused(f"{path}: a row that is not key v2.5")
    mine = {k: v[0] for k, v in rows.items() if k[0] == A}
    twice = sorted(set(mine) & held)
    if twice:
        raise Refused(f"{path}: {len(twice)} keys already held by --collect or --base (first {twice[0]}): never replaced")
    return mine, {"t2x_rows": len(mine), "t2x_single_pass_not_read": sum(1 for k in rows if k[0] == B)}


def refuse_unless_fixed() -> str:
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()
    for path in (SCRIPT, S511_SCRIPT):
        if git("status", "--porcelain", "--", path):
            raise Refused(f"{path} differs from its commit")
        if not git("log", "-1", "--format=%h", "--", path):
            raise Refused(f"{path} is not committed")
    head = git("log", "-1", "--format=%h", "--", SCRIPT)
    if DECISION not in (ROOT / "experiments" / "README.md").read_text():
        raise Refused(f"{DECISION} is not in experiments/README.md")
    return head


def input_record(role: str, path: Path) -> dict:
    """D201 Q8: what ties a result to one file it read: its role, its path, its sha256."""
    p = Path(path).resolve()
    shown = str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(path)
    return {"role": role, "path": shown, "sha256": S511.sha256_file(p), "_read": p}


def fixed_reads() -> list:
    """D201 Q8: the files `run` reads whatever the source: what gate() and S511.questions() read, and S511's source."""
    from experiments.runner import experiment as ex
    return [("gate: G1 collect", S511.RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl"),
            ("gate: S511 results", S511.OUT / "results.json"),
            ("questions: D5 key", Path(ex.KEY_D5)),
            ("import: S511", ROOT / S511_SCRIPT)]


def seal(records: list) -> list:
    """The records for the result, after holding each file to the sha256 taken before it was read (D201 Q8)."""
    for r in records:
        if S511.sha256_file(r["_read"]) != r["sha256"]:
            raise Refused(f"{r['path']} changed while it was read")
    return [{k: r[k] for k in ("role", "path", "sha256")} for r in records]


def reference(records: list, g: dict, dry: bool) -> int:
    """D235 Q4: compute Flash's row on key v2.5, refuse unless it reproduces S511's key v2.5 pairs, then write it (or,
    with dry, print it). Raises Refused."""
    commit = None
    if not dry:
        commit = refuse_unless_fixed()
        if REF_DECISION not in (ROOT / "experiments" / "README.md").read_text():
            raise Refused(f"{REF_DECISION} is not in experiments/README.md")
    qs = S511.questions()
    records += [input_record("reference base (key v2.4)", REF_BASE), input_record("reference collect (key v2.5)", REF_COLLECT),
                input_record("reference collect: SHA256SUMS", REF_COLLECT.parent / "SHA256SUMS")]
    cells, info = reference_cells(qs)
    res = analyse(cells, qs)
    said = reference_gate(res)
    out = {"source": REFERENCE, "role": REF_ROLE, "key": REF_KEY, "judge": "devstral-small-2:24b",
           "label": "Gemini 3 Flash (reference), key v2.5", "script_commit": commit, "decision": "D235",
           "method": "D195", "threshold": THRESHOLD, "inputs": seal(records), "rows": info,
           "reproduced": said, "result": res, "reference_flash_v24": g}
    if dry:
        print(json.dumps(dict(out, dry_run=True), indent=1))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{REFERENCE}.json").write_text(json.dumps(out, indent=1) + "\n")
    print("reproduced", said)
    print("written", OUT / f"{REFERENCE}.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("gate")
    r = sub.add_parser("run")
    r.add_argument("--source", required=True, choices=sorted(SOURCES))
    r.add_argument("--collect", required=True, type=Path)
    r.add_argument("--base", type=Path)
    r.add_argument("--t2x", type=Path, help="D241: T2X's v2.5 collect (S574), rlm_10 rows of the 17 added; gemma3 and "
                                            "qwen3-coder only")
    f = sub.add_parser("reference", help="D235 Q4: Gemini 3 Flash on key v2.5, the reference row of Figure 3e")
    f.add_argument("--dry", action="store_true", help="print the result, write nothing (no commit needed)")
    a = ap.parse_args()
    try:
        records = [input_record(*x) for x in fixed_reads()]
        g = gate()
        if a.mode == "gate":
            print("gate PASSED: Flash, devstral, key v2.4 equal S511")
            return 0
        if a.mode == "reference":
            return reference(records, g, a.dry)
        commit = refuse_unless_fixed()
        qs = S511.questions()
        records += [input_record("collect", a.collect)] + ([input_record("base", a.base)] if a.base else [])
        cells, info = merge(read_rows(a.base, qs) if a.base else {}, read_rows(a.collect, qs))
        if a.t2x:
            if T2X_DECISION not in (ROOT / "experiments" / "README.md").read_text():
                raise Refused(f"{T2X_DECISION} is not in experiments/README.md")
            records += [input_record("t2x collect", a.t2x), input_record("t2x questions", T2X_QUESTIONS)]
            extra, t2x_info = t2x_cells(a.t2x, qs, a.source, set(cells))
            cells.update(extra)
            info.update(t2x_info, rows_used=len(cells))
        res = {"source": a.source, "role": SOURCES[a.source], "script_commit": commit, "decision": "D195",
               "threshold": THRESHOLD, "inputs": seal(records), "rows": info, "result": analyse(cells, qs),
               "reference_flash_v24": g}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{a.source}.json").write_text(json.dumps(res, indent=1) + "\n")
        print("written", OUT / f"{a.source}.json")
        return 0
    except Refused as e:
        print("REFUSED:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
