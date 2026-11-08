#!/usr/bin/env python3
"""S565 - the strategy-by-corpus-size interaction test of D213 (2), on the G4 re-run, its method fixed before the run.

DECISION. D213 (Valerio, 3 November early afternoon, experiments/README.md "D213"), part (2), Q6.4 go:
  "the strategy-by-corpus-size interaction test on the re-run, its method fixed here before any run: G4 draw 1 (one run
  per index; 12 indexes, 5, 10, 20, 50 core papers by 0, 1, 3 distractors per core paper), answerable questions whose
  papers are all in the index, final-key judge rows; pass = judge correctness 4 or more (primary), 3 or more
  (secondary); model as the submitted S11 (scripts/S11_corpus_mixed_model.R): logistic, random intercept per question,
  pass ~ strategy x log2(core papers) + distractor level; primary contrast RLM-10 against single pass, the other four
  strategies against single pass secondary and exploratory, unadjusted; question sets (a) the 22 asked at every size
  (primary) and (b) all in-scope questions; interval: two-sided 95% percentile, 10,000 cluster-bootstrap resamples of
  questions, seed fixed; companion: RLM-10's gap to single pass at 50 minus at 20 core papers on the same 86 questions,
  same bootstrap. Reported whatever it shows; with one draw per index the intervals will be wide."

THE COMMANDS, from the repository root:

    uv run --frozen python <this file> run [--out <folder>] [--cores N] [--n-boot 10000]
    uv run --frozen python <this file> selftest

READS (no second reader). The G4 draw-1 reading Supplementary Figure 17 and Figure 3f draw, through S484's own loader:
S484.load() (S476.reproduce_g4 on findings/recompute/G4_fig3c, the key v2.4 anchor, gated by S476 itself) then
S484.load_d185() (S476.reproduce_g4_d185 on findings/recompute/G4_fig3c_d185: S514 g4c's per-answer choice by
scripts/judge_rows_v25.py, the key v2.5 judge row for the 132 questions v2.5 changed, else the v2.4 row, which v2.5
left unchanged; 0 covered answers await S6, so this is the final key). Pass values are S484.table's (pass3, pass4)
over the covered questions (D126: answerable, every source paper among the index's core papers). A failed answer is a
fail (S476.g4_cells); a judge call without a score is missing and left out. The 22: q66_tables.json ids.answerable
(the questions in scope at every size, the "The same 22" block of Figure 3f). Also read for the reproduction: the
committed Supplementary Figure 17 numbers (supp_fig17_corpus/, dropped by D302, read from git at FIG9_COMMIT), Figure 3's numbers (sheet
Fig. 3f) and q66_tables.json's pooled_over_ratios rates.

REPRODUCE FIRST (README.md:75-79); exit 2 and no result written on any difference:
  (1) per size, single pass's and RLM-10's pass rate at score 4 and 3 on all in-scope questions, computed here from
      the model's input rows, equal the committed sheets Supplementary Fig. 17b (score 4) and 17c (score 3), cell for
      cell (n pairs, n questions, pass rate), to 1e-9;
  (2) the same on the 22: Supplementary Figure 17's Source Data holds no 22-question rows, so the rates are held to
      Figure 3f's Source Data block "The same 22" (score 4) and to q66_tables.json answerable pooled_over_ratios
      (score 4 and 3);
  (3) RLM-10 minus single pass at 20 and 50 core papers, score 4, all in scope, equals Figure 3f's cells and
      Supplementary Fig. 17a's. The letter's -6.2 and -13.6 are computed on the final key and on the key v2.4
      anchor (G4_fig3c) and the match is reported, not gated.

THE MODEL (R, lme4; S565_corpus_interaction.R beside this file): S11's fit_interaction, two strategies at a time,
pass ~ strategy * log2(core papers, centred) + factor(distractor ratio) + (1 | question), binomial, bobyqa. One row
per (index, question, strategy). Bootstrap: the 10,000 x n counts of S463.resample_counts (default_rng(20261013),
Rule 2's resamples), written to counts_<set>.csv so R refits on exactly these; percentiles 2.5 and 97.5.

THE COMPANION (here, numpy): on the 86 questions in scope at both 20 and 50 core papers, d(c) = RLM-10 minus single
pass over every (index, question) pair at size c where both have a value (S484.pooled's ratio of sums), gap = d(50) -
d(20) in points; each resample takes the same counts row, sums each question's numerators and pair counts at each size
as often as drawn, and recomputes the gap.

WRITES into --out (default out/ beside this file; never the repository): tidy.csv, counts_<set>.csv, model.json (R),
results.json, results.md, header.json (inputs' sha256, command, versions; no write time in results). No model call,
no network, no server.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCRIPT = "S565_corpus_interaction.py"
RSCRIPT = HERE / "S565_corpus_interaction.R"
OUT = ROOT / "findings" / "recompute" / "S565_corpus_interaction"
G4D185 = ROOT / "findings" / "recompute" / "G4_fig3c_d185"
G4V24 = ROOT / "findings" / "recompute" / "G4_fig3c"
# D302 dropped the corpus plate (D257's Supplementary Figure 17) from the paper and the working tree; its committed
# numbers and provenance are read from the last commit that held them (D303), so the reproduction still checks against
# a frozen artifact and nothing needs the folder on disk.
FIG9_COMMIT = "c07192ba901c9c9af20fd3e08764712ade78bfa8"
FIG9 = "findings/figures_provisional/supp_fig17_corpus/supplementary_figure17_numbers.json"
FIG9_PROV = "findings/figures_provisional/supp_fig17_corpus/supplementary_figure17_provenance.json"
FIG3 = ROOT / "findings" / "figures_provisional" / "fig3_strategies" / "figure3_numbers.json"
Q66 = G4D185 / "q66_tables.json"
SIZES, RATIOS = (5, 10, 20, 50), (0, 1, 3)
STRATS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
SETS = ("same22", "all_in_scope")              # (a) primary, (b)
THRESHOLDS = (4, 3)                            # primary, secondary
K = {3: 0, 4: 1}                               # index into S484.table's (pass3, pass4)
LETTER = {20: -6.2, 50: -13.6}                 # the letter's RLM-10 minus single pass at score 4, points
N_BOOT_DEFAULT = 10000
TOL = 1e-9


class Refused(Exception):
    pass


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def idx(c, r):
    return f"exp_v4_s{c}_n{r}"


# ---------------------------------------------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------------------------------------------
def tidy_rows(by, sets: dict) -> list:
    """One row per (question set, threshold, index, question, strategy), pass None where the cell has no value."""
    out = []
    for name, qsets in sets.items():
        for thr in THRESHOLDS:
            for c in SIZES:
                for r in RATIOS:
                    i = idx(c, r)
                    for s in STRATS:
                        for q in sorted(qsets[c]):
                            v = by[(i, s)].get(q, (None, None))[K[thr]]
                            out.append({"question_set": name, "threshold": thr, "index": i, "core_papers": c,
                                        "distractor_ratio": r, "question_id": q, "strategy": s,
                                        "pass": "" if v is None else int(v)})
    return out


def common_rates(by, c, qids, k, strats=STRATS):
    """Supplementary Fig. 17b/17c's rate: over the (index, question) pairs where every strategy has a value at score 3
    (S484.common_pairs), each strategy's pass share at threshold k. Recomputed here from by, not by S484.compute."""
    pairs = [(idx(c, r), q) for r in RATIOS for q in sorted(qids)
             if all(by[(idx(c, r), s)].get(q, (None, None))[0] is not None for s in strats)]
    return {s: {"n_pairs": len(pairs), "n_questions": len({q for _, q in pairs}),
                "pass_pct": 100 * sum(by[(i, s)][q][k] for i, q in pairs) / len(pairs)} for s in strats}, pairs


def per_question(by, a, b, c, qids, k):
    """{question: (summed a minus b, pair count)} over the size's three indexes, pairs where both have a value."""
    num, den = collections.defaultdict(float), collections.defaultdict(float)
    for r in RATIOS:
        A, B = by[(idx(c, r), a)], by[(idx(c, r), b)]
        for q in qids:
            x, y = A.get(q, (None, None))[k], B.get(q, (None, None))[k]
            if x is None or y is None:
                continue
            num[q] += x - y
            den[q] += 1
    return num, den


def gap_point(by, qids, k, a="rlm_10", b="single_pass"):
    out = {}
    for c in (20, 50):
        num, den = per_question(by, a, b, c, qids, k)
        out[c] = 100 * sum(num.values()) / sum(den.values())
    return out


def companion(by, qids_sorted, counts, k):
    """RLM-10's gap to single pass at 50 minus at 20 core papers; the counts matrix (n_boot x n) gives the resamples."""
    arrs = {}
    for c in (20, 50):
        num, den = per_question(by, "rlm_10", "single_pass", c, qids_sorted, k)
        arrs[c] = (np.array([num.get(q, 0.0) for q in qids_sorted]), np.array([den.get(q, 0.0) for q in qids_sorted]))
    pt = {c: 100 * arrs[c][0].sum() / arrs[c][1].sum() for c in (20, 50)}
    bd = {}
    for c in (20, 50):
        top, bot = counts @ arrs[c][0], counts @ arrs[c][1]
        bd[c] = (top, bot)
    ok = (bd[20][1] > 0) & (bd[50][1] > 0)
    g = 100 * (bd[50][0][ok] / bd[50][1][ok] - bd[20][0][ok] / bd[20][1][ok])
    lo, hi = np.percentile(g, (2.5, 97.5))
    d20b, d50b = (100 * bd[c][0][ok] / bd[c][1][ok] for c in (20, 50))
    return {"d20_pp": pt[20], "d50_pp": pt[50], "gap_pp": pt[50] - pt[20], "ci95_pp": [float(lo), float(hi)],
            "d20_ci95_pp": [float(x) for x in np.percentile(d20b, (2.5, 97.5))],
            "d50_ci95_pp": [float(x) for x in np.percentile(d50b, (2.5, 97.5))],
            "n_questions": len(qids_sorted), "n_pairs": {c: int(arrs[c][1].sum()) for c in (20, 50)},
            "resamples": int(counts.shape[0]), "resamples_used": int(ok.sum())}


def load_readings():
    S484 = _load("S484", ROOT / "scripts" / "S484_supp_fig4_corpus.py")
    D24 = S484.load()                       # S476.reproduce_g4, gated by S476
    D = S484.load_d185(D24)                 # the drawn reading, final key
    return S484, D24, D


def question_sets(by, q66):
    cov = {c: {q for q in by[(idx(c, 0), "single_pass")]} for c in SIZES}
    for c in SIZES:
        for r in RATIOS:
            if {q for q in by[(idx(c, r), "single_pass")]} != cov[c]:
                raise Refused(f"covered questions differ across ratios at {c} core papers")
    ids22 = set(q66["ids"]["answerable"])
    if len(ids22) != 22 or any(not ids22 <= cov[c] for c in SIZES) or ids22 != cov[5]:
        raise Refused("q66_tables.json's 22 are not the 22 in scope at every size")
    if cov[20] != cov[50] or len(cov[50]) != 86:
        raise Refused("the in-scope questions at 20 and 50 core papers are not the same 86")
    return {"same22": {c: ids22 for c in SIZES}, "all_in_scope": cov}


# ---------------------------------------------------------------------------------------------------------------
# REPRODUCTION
# ---------------------------------------------------------------------------------------------------------------
def frozen_blob(path: str) -> bytes:
    """A file of the dropped corpus plate as committed at FIG9_COMMIT (D303)."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{FIG9_COMMIT}:{path}"], capture_output=True)
    if r.returncode != 0:
        raise Refused(f"git show {FIG9_COMMIT[:8]}:{path} failed: {r.stderr.decode()[-300:]}")
    return r.stdout


def sheet(numbers, name):
    s = numbers["sheets"][name]
    return [dict(zip(s["columns"], r)) for r in s["rows"]]


def reproduce(by, sets, by24, sets24) -> tuple[list, dict]:
    lines, rec = [], {}
    fig9 = json.loads(frozen_blob(FIG9))
    prov = json.loads(frozen_blob(FIG9_PROV))
    rec_sha = (prov.get("inputs_sha256") or {}).get("findings/recompute/G4_fig3c_d185/grid_pairs.jsonl")
    now_sha = sha(G4D185 / "grid_pairs.jsonl")
    if rec_sha != now_sha:
        raise Refused(f"Supplementary Figure 17's provenance records grid_pairs.jsonl {rec_sha}, not {now_sha}")
    lines.append(f"Supplementary Figure 17 was drawn from the grid_pairs.jsonl read here (sha256 {now_sha[:12]})")
    # (1)
    n = 0
    table1 = []
    for thr, sh in ((4, "Supplementary Fig. 17b"), (3, "Supplementary Fig. 17c")):
        got = {(e["core_papers"], e["strategy"]): e for e in sheet(fig9, sh)}
        for c in SIZES:
            mine, _ = common_rates(by, c, sets["all_in_scope"][c], K[thr])
            for s in ("single_pass", "rlm_10"):
                g = got[(c, s)]
                for a in ("n_pairs", "n_questions", "pass_pct"):
                    b = {"n_pairs": "n_pairs_common", "n_questions": "n_questions_common", "pass_pct": "pass_pct"}[a]
                    n += 1
                    if abs(float(mine[s][a]) - float(g[b])) > TOL:
                        raise Refused(f"(1) {sh} {c} {s} {a}: mine {mine[s][a]}, sheet {g[b]}")
                table1.append({"set": "all_in_scope", "threshold": thr, "core_papers": c, "strategy": s,
                               **mine[s], "source": sh})
    lines.append(f"(1) all in scope: {n} values (n pairs, n questions, pass rate; single pass and RLM-10; 4 sizes; "
                 f"score 4 and 3) equal Supplementary Fig. 17b and 17c")
    # (2)
    fig3 = sheet(json.loads(FIG3.read_text()), "Fig. 3f")
    e22 = {e["core_papers"]: e for e in fig3 if e["block"] == "The same 22" and e["row_kind"] == "cell"
           and e["strategy"] == "rlm_10"}
    q66 = json.loads(Q66.read_text())
    qt = {(e["core_papers"], e["strategy"]): e["pooled_over_ratios"] for e in q66["answerable"]["main"]}
    n2a = n2b = 0
    for c in SIZES:
        for thr in THRESHOLDS:
            mine, pairs = common_rates(by, c, sets["same22"][c], K[thr])
            if len(pairs) != 66:
                raise Refused(f"(2) the 22 at {c}: {len(pairs)} pairs with every strategy, not 66")
            for s in ("single_pass", "rlm_10"):
                t = qt[(c, s)][f"score{thr}"]["failures_in"]
                if t.get("questions_without_value"):
                    raise Refused(f"(2) q66 {c} {s} score {thr}: questions without value")
                n2b += 1
                if abs(t["rate_pct"] - mine[s]["pass_pct"]) > TOL:
                    raise Refused(f"(2) q66 {c} {s} score {thr}: {t['rate_pct']}, mine {mine[s]['pass_pct']}")
                if thr == 4:
                    col = "pass_strategy_pct" if s == "rlm_10" else "pass_single_pass_pct"
                    n2a += 1
                    if abs(e22[c][col] - mine[s]["pass_pct"]) > TOL or e22[c]["n_pairs"] != 66:
                        raise Refused(f"(2) Fig. 3f same 22 {c} {s}: {e22[c][col]}, mine {mine[s]['pass_pct']}")
                table1.append({"set": "same22", "threshold": thr, "core_papers": c, "strategy": s, **mine[s],
                               "source": "Fig. 3f The same 22 and q66_tables" if thr == 4 else "q66_tables"})
    lines.append(f"(2) the 22: {n2a} rates equal Figure 3f's Source Data block 'The same 22' (score 4) and {n2b} "
                 f"equal q66_tables.json pooled_over_ratios (score 4 and 3); Supplementary Figure 17's Source Data "
                 f"holds no 22-question rows")
    # (3)
    gp = gap_point(by, sorted(sets["all_in_scope"][50]), 1)
    eall = {e["core_papers"]: e for e in fig3 if e["block"] == "All in scope" and e["row_kind"] == "cell"
            and e["strategy"] == "rlm_10" and e["question_group"] == "all"}
    f9a = {(e["core_papers"], e["row_strategy"], e["column_strategy"]): e for e in sheet(fig9, "Supplementary Fig. 17a")}
    for c in (20, 50):
        if abs(gp[c] - eall[c]["d_pp"]) > TOL or abs(gp[c] - f9a[(c, "rlm_10", "single_pass")]["d_pp"]) > TOL:
            raise Refused(f"(3) RLM-10 minus single pass at {c}: mine {gp[c]}, Fig. 3f {eall[c]['d_pp']}")
    g24 = gap_point(by24, sorted(sets24["all_in_scope"][50]), 1)
    rec["letter"] = {str(c): {"letter_pp": LETTER[c], "final_key_pp": gp[c], "key_v2.4_anchor_pp": g24[c],
                              "letter_equals_final_key": round(gp[c], 1) == LETTER[c],
                              "letter_equals_v2.4_anchor": round(g24[c], 1) == LETTER[c]} for c in (20, 50)}
    lines.append(f"(3) RLM-10 minus single pass, score 4, all in scope: 20 core papers {gp[20]:.4f}, 50 core papers "
                 f"{gp[50]:.4f} points, equal to Figure 3f and Supplementary Fig. 17a")
    lines.append("(3) the letter's values: " + "; ".join(
        f"{c} core papers letter {LETTER[c]}, final key {gp[c]:.1f}, key v2.4 anchor {g24[c]:.1f}" for c in (20, 50)))
    rec["rates"] = table1
    return lines, rec


# ---------------------------------------------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------------------------------------------
def write_csv(path, rows, cols, header_lines):
    with open(path, "w", newline="") as f:
        for h in header_lines:
            f.write(f"# {h}\n")
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def counts_for(n, n_boot):
    S463 = sys.modules["S484"].S463
    cnt = S463.resample_counts(n)
    if cnt.shape != (S463.N_BOOT, n) or S463.SEED != 20261013:
        raise Refused("S463.resample_counts is not 10,000 x n on seed 20261013")
    return cnt[:n_boot]


def run_r(tidy, counts_dir, out_json, cores, n_boot, only=""):
    cmd = ["Rscript", str(RSCRIPT), str(tidy), str(counts_dir), str(out_json), str(cores), str(n_boot), only]
    env = dict(os.environ, VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    log = Path(out_json).with_suffix(".log")
    with open(log, "w") as fh:                  # progress line per cell, readable while R runs
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True, env=env)
    text = log.read_text()
    if r.returncode != 0:
        raise Refused(f"Rscript failed: {text[-2000:]}")
    return text


def run(out: Path, cores: int, n_boot: int) -> int:
    t0 = time.time()
    try:
        S484, D24, D = load_readings()
        if not all(bool(v["complete"]) for v in D["units"].values()):
            raise Refused("not every index x strategy unit is complete")
        q66 = json.loads(Q66.read_text())
        sets = question_sets(D["by"], q66)
        sets24 = question_sets(D24["by"], q66)
        lines, rec = reproduce(D["by"], sets, D24["by"], sets24)
        for x in lines:
            print(x)
        out.mkdir(parents=True, exist_ok=True)
        hdr_lines = [f"{SCRIPT}: D213 (2) model input, G4 draw 1, final key (S484.load_d185 on {rel(G4D185)})",
                     "one row per question set x threshold x index x question x strategy; pass empty = no value"]
        rows = tidy_rows(D["by"], sets)
        cols = ["question_set", "threshold", "index", "core_papers", "distractor_ratio", "question_id", "strategy",
                "pass"]
        write_csv(out / "tidy.csv", rows, cols, hdr_lines)
        missing = collections.Counter((r["question_set"], r["threshold"], r["strategy"]) for r in rows
                                      if r["pass"] == "")
        cnts = {}
        for name in SETS:
            qs = sorted(set().union(*sets[name].values()))
            cnt = counts_for(len(qs), n_boot)
            cnts[name] = (qs, cnt)
            np.savetxt(out / f"counts_{name}.csv", cnt.astype(int), fmt="%d", delimiter=",",
                       header=",".join(qs), comments="")
        comp = {}
        for thr in THRESHOLDS:
            qs, cnt = cnts["all_in_scope"]
            if qs != sorted(sets["all_in_scope"][50]):
                raise Refused("the all-in-scope set is not the 86 of 20 and 50 core papers")
            comp[thr] = companion(D["by"], qs, cnt, K[thr])
        t_r = time.time()
        log = run_r(out / "tidy.csv", out, out / "model.json", cores, n_boot)
        r_secs = time.time() - t_r
        model = json.loads((out / "model.json").read_text())
        res = {"decision": "D213 (2)", "reproduced": lines, "letter_check": rec["letter"],
               "rates_reproduced": rec["rates"], "missing_cells": {f"{a} score {b} {c}": n for (a, b, c), n in
                                                                   sorted(missing.items())},
               "model": model, "companion": {f"score {t}": comp[t] for t in THRESHOLDS},
               "runtime_s": {"total": time.time() - t0, "r": r_secs}}
        (out / "results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        (out / "results.md").write_text(results_md(res))
        files = [G4D185 / n for n in ("grid_pairs.jsonl", "header.json", "q66_tables.json")] + \
                [G4V24 / n for n in ("grid_pairs.jsonl", "header.json")] + [FIG3,
                                                                            ROOT / "scripts/S484_supp_fig4_corpus.py",
                                                                            ROOT / "scripts/S476_fig3_d123.py",
                                                                            ROOT / "scripts/judge_rows_v25.py",
                                                                            ROOT / "scripts/S11_corpus_mixed_model.R"]
        hdr = {"script": SCRIPT, "script_sha256": sha(Path(__file__)), "r_script_sha256": sha(RSCRIPT),
               "command": f"uv run --frozen python {SCRIPT} run --cores {cores} --n-boot {n_boot}",
               "python": platform.python_version(), "r": model["r_version"], "lme4": model["lme4"],
               "inputs_sha256": {**{rel(p): sha(p) for p in files},
                                 **{f"{FIG9_COMMIT}:{q}": hashlib.sha256(frozen_blob(q)).hexdigest()
                                    for q in (FIG9, FIG9_PROV)}}, "git_head": subprocess.run(
                   ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
               "outputs_sha256": {p.name: sha(p) for p in sorted(out.iterdir()) if p.name != "header.json"}}
        (out / "header.json").write_text(json.dumps(hdr, indent=1) + "\n")
        print(log)
        print(f"wrote {out}; {time.time() - t0:.0f} s")
    except Refused as e:
        print(f"REFUSED, nothing further written: {e}", file=sys.stderr)
        return 2
    return 0


def f(x, d=3):
    return f"{x:+.{d}f}" if isinstance(x, (int, float)) else str(x)


def results_md(res) -> str:
    L = ["# S565, D213 (2): strategy by corpus size", "",
         "G4 draw 1, final key; pass at score 4 primary, 3 secondary. Interaction = change in log odds of passing "
         "against single pass per doubling of core papers (two strategies per model, S11's form, plus distractor "
         "level). Interval: two-sided 95% percentile, cluster bootstrap of questions.", "",
         "## Reproduced first", ""] + [f"- {x}" for x in res["reproduced"]] + ["", "## Interaction (primary first)", "",
         "| set | score | strategy | n rows | n questions | estimate | OR per doubling | bootstrap 95% (D213) | Wald 95% (not D213's method) | "
         "Wald P (not D213's method) | refits ok | singular |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"same22": 0, "all_in_scope": 1}
    fits = sorted(res["model"]["fits"], key=lambda r: (r["threshold"] != 4, order[r["question_set"]],
                                                        r["strategy"] != "rlm_10", r["strategy"]))
    for r in fits:
        b, w = r["boot_ci95_percentile"], r["wald_ci95"]
        L.append(f"| {r['question_set']} | {r['threshold']} | {r['strategy']} | {r['n_rows']} | {r['n_questions']} | "
                 f"{r['estimate_log_odds_per_doubling']:+.3f} | {r['odds_ratio_per_doubling']:.3f} | "
                 f"[{b[0]:+.3f}, {b[1]:+.3f}] | [{w[0]:+.3f}, {w[1]:+.3f}] | {r['wald_p_two_sided']:.4f} | "
                 f"{r['boot_ok']} of {r['boot_resamples']} | {r['boot_singular']} |")
    L += ["", "## Companion: RLM-10 minus single pass, 50 minus 20 core papers, the 86 questions", "",
          "| score | d at 20 (95%) | d at 50 (95%) | gap 50 minus 20 | 95% |", "|---|---|---|---|---|"]
    for k, c in res["companion"].items():
        L.append(f"| {k} | {c['d20_pp']:+.1f} [{c['d20_ci95_pp'][0]:+.1f}, {c['d20_ci95_pp'][1]:+.1f}] | "
                 f"{c['d50_pp']:+.1f} [{c['d50_ci95_pp'][0]:+.1f}, {c['d50_ci95_pp'][1]:+.1f}] | {c['gap_pp']:+.1f} | "
                 f"[{c['ci95_pp'][0]:+.1f}, {c['ci95_pp'][1]:+.1f}] |")
    L += ["", f"Runtime: {res['runtime_s']['total']:.0f} s in all, {res['runtime_s']['r']:.0f} s in R.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------
# SELFTEST (a fixture; nothing in the repository read for data or written)
# ---------------------------------------------------------------------------------------------------------------
def fixture(effect: bool, seed=3):
    """by in S484.table's shape: 30 questions, 10 at every size, 30 from 20 core papers. Without effect, RLM-10's
    cells are single pass's (the interaction must be exactly 0); with it, RLM-10 fails most answers at 50."""
    rng = np.random.default_rng(seed)
    qs = [f"q{i:02d}" for i in range(30)]
    inscope = {5: qs[:10], 10: qs[:20], 20: qs, 50: qs}
    by = collections.defaultdict(dict)
    for c in SIZES:
        for r in RATIOS:
            for q in inscope[c]:
                base = rng.random() < 0.8
                for s in STRATS:
                    p = base
                    if s == "rlm_10" and effect:
                        p = rng.random() < {5: 0.85, 10: 0.7, 20: 0.5, 50: 0.25}[c]
                    elif s not in ("single_pass", "rlm_10"):
                        p = rng.random() < 0.7
                    by[(idx(c, r), s)][q] = (int(p), int(p))
    return by, {"same22": {c: set(qs[:10]) for c in SIZES}, "all_in_scope": {c: set(inscope[c]) for c in SIZES}}


def selftest() -> int:
    fails = []
    tmp = Path(tempfile.mkdtemp(prefix="s565_"))
    try:
        # companion by hand on a 2-question toy
        by = collections.defaultdict(dict)
        for r in RATIOS:
            by[(idx(20, r), "single_pass")] = {"a": (1, 1), "b": (1, 0)}
            by[(idx(20, r), "rlm_10")] = {"a": (1, 1), "b": (0, 0)}
            by[(idx(50, r), "single_pass")] = {"a": (1, 1), "b": (1, 1)}
            by[(idx(50, r), "rlm_10")] = {"a": (0, 0), "b": (None, None)}
        cnt = np.array([[1, 1], [2, 0], [0, 2]], dtype=float)
        c = companion(by, ["a", "b"], cnt, 0)
        # score 3: d20 = (0 + -3)/6 = -50; d50 = (-3)/3 = -100 (b has no value); gap -50
        if abs(c["d20_pp"] + 50) > TOL or abs(c["d50_pp"] + 100) > TOL or abs(c["gap_pp"] + 50) > TOL:
            fails.append(f"companion point {c}")
        # resample [2,0]: d20 0, d50 -100 -> -100; [0,2]: d50 has no pair -> left out; [1,1]: -50
        if c["resamples_used"] != 2:
            fails.append(f"companion: a resample with no pair at 50 was kept ({c['resamples_used']})")
        # common_rates: a strategy missing a cell drops the pair for all
        cr, pairs = common_rates(by, 50, {"a", "b"}, 0, ("single_pass", "rlm_10"))
        if len(pairs) != 3 or cr["single_pass"]["pass_pct"] != 100.0 or cr["rlm_10"]["pass_pct"] != 0.0:
            fails.append(f"common_rates {cr}")
        # counts: the repository's resamples
        _load("S484", ROOT / "scripts" / "S484_supp_fig4_corpus.py")
        k = counts_for(7, 10000)
        if k.shape != (10000, 7) or not np.all(k.sum(axis=1) == 7):
            fails.append("counts rows do not each draw n questions")
        # R: no effect -> interaction exactly 0 everywhere; effect -> negative, interval below 0
        for effect in (False, True):
            byf, sets = fixture(effect)
            rows = tidy_rows(byf, sets)
            d = tmp / f"e{int(effect)}"
            d.mkdir()
            write_csv(d / "tidy.csv", rows, list(rows[0]), ["selftest fixture"])
            for name in SETS:
                qs = sorted(set().union(*sets[name].values()))
                np.savetxt(d / f"counts_{name}.csv", counts_for(len(qs), 200).astype(int), fmt="%d", delimiter=",",
                           header=",".join(qs), comments="")
            run_r(d / "tidy.csv", d, d / "model.json", 4, 200, "rlm_10")
            m = json.loads((d / "model.json").read_text())
            for r in m["fits"]:
                e, (lo, hi) = r["estimate_log_odds_per_doubling"], r["boot_ci95_percentile"]
                if not effect and (abs(e) > 1e-4 or abs(lo) > 1e-4 or abs(hi) > 1e-4):
                    fails.append(f"no-effect fixture {r['question_set']} {r['threshold']}: {e} [{lo}, {hi}]")
                if effect and r["question_set"] == "all_in_scope" and not (e < 0 and hi < 0):
                    fails.append(f"effect fixture {r['threshold']}: {e} [{lo}, {hi}] not below 0")
                if r["boot_ok"] + r["boot_errors"] != 200:
                    fails.append("bootstrap refits not all accounted for")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for x in fails:
        print("FAIL", x)
    print("selftest", "FAILED" if fails else "passed", f"({len(fails)} failures)")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, default=OUT)
    r.add_argument("--cores", type=int, default=8)
    r.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT)
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    if (a.out / "results.json").exists():                      # a finished run is never written over
        print(f"REFUSED: {a.out} holds results.json already", file=sys.stderr)
        return 2
    return run(a.out.resolve(), a.cores, a.n_boot)


if __name__ == "__main__":
    sys.exit(main())
