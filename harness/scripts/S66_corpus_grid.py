#!/usr/bin/env python3
"""S66 - the corpus-scaling factorial reported as the whole 4 x 3 grid, paired within cell.

Reviewer 2, Question 1 asks whether all corpus sizes were evaluated on a fixed common subset of
questions, so that question difficulty and category composition can be separated from corpus size.
The answer as first drafted rested on the 22 answerable questions present at every core-paper
subset, read along the no-noise row, which is the steepest of the three noise rows and the one
slice where the RLM retrieval configuration changes with the treatment (see the reranker
inventory below). This script reports the design as it was run: 12 index configurations, four
core-paper subsets crossed with three noise ratios.

Everything here is paired within a cell: each cell keeps only the questions scored for BOTH
compared strategies in that cell, so the two arms face an identical question set and the gap
inside a cell carries no question-composition difference. Comparing gaps ACROSS cells is a
separate assumption, tested in scripts/S67 by the within/between decomposition, not assumed here.

Scores are the complete-answer re-judge throughout. Deposited scores appear only as reproduction
gates and as one labelled contingency, never as a published cell.

Gates, all evaluated before anything is written; a failure exits, it never warns.

  Structural
   S1  9,894 tidy rows, 6,305 re-judged rows
   S2  the join key (question_id, strategy, index_name) is unique in both files
   S3  every re-judged row finds its partner, and the join changes exactly 258 scores outside
       verified_pass (262 in all, 4 on verified_pass), whose rows all carry the rerun's correctness (scripts/exp05_final.py)
   S4  the 3,589 unmatched rows are exactly the unanswerable, unjudged ones
   S5  empty and gen_error are identically zero over all 9,894 rows
   S6  answerable question sets are 22 / 44 / 88 / 200 and strictly nested
   S7  the 50 unanswerable control questions are the same set at every core-paper subset
   S8  total documents equals core papers x (1 + noise ratio) in all twelve configurations
   S9  crash inventory: exactly 23 missing single-pass-or-RLM-10 answerable cells, all on
       RLM-10, distributed 7 / 6 / 3 / 7 across 5 / 10 / 20 / 50 core papers

  Reproduction, published values that must come back before corrected ones are written
   R1  manuscript L199-201, deposited, 50 core papers, no noise: single-pass 83.0, RLM-5 63.1,
       RLM-10 61.2, RLM-20 62.1
   R2  all 24 cells of findings/recompute/S11_fig3d_subset_panel.csv, deposited
   R3  manuscript L204-205, deposited: RLM-5 at 20 core papers, 0x to 3x, 86.9 to 72.4 = 14.5 pp
   R4  the published crossover, deposited, unpaired, pooled over noise ratios: -25.7 pp
       (publication/scripts/analysis_statistical_tests.py, test_3)

Writes findings/recompute/S66_corpus_grid.json + .md
"""
from __future__ import annotations

import collections
import csv
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, RESULTS  # noqa: E402
from exp05_final import rerun_rows  # noqa: E402

OUT = RECOMPUTE
TIDY = OUT / "S11_exp05_tidy.csv"
REJUDGED = OUT / "S11_exp05_tidy_rejudged.csv"
PANEL = OUT / "S11_fig3d_subset_panel.csv"
INDEXES = sorted(RESULTS.glob("create_indexes_*.json"))

CORES = ["5", "10", "20", "50"]
NOISE = ["0", "1", "3"]
STRATEGIES = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
BASE, PRIMARY = "single_pass", "rlm_10"
PASS_AT = 3
RERANKER_CHUNKS = 800          # backend/retrieval/rlm/context.py:200


def utcnow() -> str:
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def read_csv(path: Path) -> list:
    with open(path) as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


def die(msg: str) -> None:
    sys.exit(f"FATAL: {msg}")


# ── data ────────────────────────────────────────────────────────────────────────────────────
def load() -> tuple:
    rows = read_csv(TIDY)
    rj_rows = read_csv(REJUDGED)
    if len(rows) != 9894:
        die(f"expected 9,894 tidy rows, got {len(rows)}")
    if len(rj_rows) != 6305:
        die(f"expected 6,305 re-judged rows, got {len(rj_rows)}")

    key = lambda r: (r["question_id"], r["strategy"], r["index_name"])  # noqa: E731
    if len({key(r) for r in rows}) != len(rows):
        die("the join key is not unique in the tidy file")
    if len({key(r) for r in rj_rows}) != len(rj_rows):
        die("the join key is not unique in the re-judged file")

    rj = {key(r): r["correctness"] for r in rj_rows}
    changed = matched = 0
    for r in rows:
        r["correctness_deposited"] = r["correctness"]
        new = rj.get(key(r))
        if new in (None, ""):
            r["correctness_rejudged"] = r["correctness"]
        else:
            matched += 1
            r["correctness_rejudged"] = str(int(float(new)))
            if r["strategy"] != "verified_pass":
                changed += r["correctness_rejudged"] != r["correctness_deposited"]
    if matched != 6305:
        die(f"{matched} re-judged rows found a partner, expected 6,305")
    if changed != 258:          # S49's 262 re-judge changes, 4 of which fall on verified_pass rows
        die(f"the join changes {changed} correctness values outside verified_pass; the re-judge changes 258 there")
    # verified_pass is the rerun with the verifier working (scripts/exp05_final.py), not a re-judge
    final_vp = rerun_rows()
    vp_off = [r for r in rows if r["strategy"] == "verified_pass" and r["answerable"] == "1"
              and int(r["correctness_rejudged"]) != final_vp[(r["index_name"], r["question_id"])]["judge_scores"]["correctness"]]
    if vp_off:
        die(f"{len(vp_off)} verified_pass rows do not carry the rerun's correctness")

    unmatched = [r for r in rows if key(r) not in rj]
    if len(unmatched) != 3589 or any(r["answerable"] != "0" or r["unjudged"] != "1"
                                     for r in unmatched):
        die("the unmatched rows are not exactly the unanswerable, unjudged ones")
    if any(r["empty"] != "0" or r["gen_error"] != "0" for r in rows):
        die("empty or gen_error is non-zero somewhere; the pass rule would change")

    answerable = {c: {r["question_id"] for r in rows
                      if r["size"] == c and r["answerable"] == "1"} for c in CORES}
    if [len(answerable[c]) for c in CORES] != [22, 44, 88, 200]:
        die(f"answerable counts {[len(answerable[c]) for c in CORES]}, expected 22/44/88/200")
    for a, b in zip(CORES, CORES[1:]):
        if not answerable[a] <= answerable[b]:
            die(f"the answerable set at {a} core papers is not nested in {b}")
    unans = {c: {r["question_id"] for r in rows
                 if r["size"] == c and r["answerable"] == "0"} for c in CORES}
    if len({frozenset(v) for v in unans.values()}) != 1 or len(unans["5"]) != 50:
        die("the 50 unanswerable control questions are not one identical set at every size")
    return rows, answerable


def index_inventory() -> dict:
    """Chunk counts per configuration, and the reranker state they imply for the RLM path."""
    inv = {}
    for f in INDEXES:
        for it in json.load(open(f)).get("results", []):
            inv[it["index"]] = {"core_papers": it["core_papers"], "noise_papers": it["noise_papers"],
                                "total_documents": it["total_files"], "chunks": it["total_chunks"],
                                "rlm_reranker_on": it["total_chunks"] > RERANKER_CHUNKS}
    for core in CORES:
        for noise in NOISE:
            name = f"exp_v4_s{core}_n{noise}"
            if name not in inv:
                die(f"no index-creation record for {name}")
            if inv[name]["total_documents"] != int(core) * (1 + int(noise)):
                die(f"{name} has {inv[name]['total_documents']} documents, expected "
                    f"{int(core) * (1 + int(noise))}")
    return inv


# ── measurement ─────────────────────────────────────────────────────────────────────────────
def scoreable(r: dict) -> bool:
    return r["answerable"] == "1" and r["empty"] == "0" and r["unjudged"] == "0"


def cell_map(rows: list, core: str, noise: str, strategy: str, col: str, thresh: int,
             subset=None) -> dict:
    """question_id -> pass indicator, for one strategy in one cell."""
    return {r["question_id"]: int(int(r[col]) >= thresh)
            for r in rows
            if r["size"] == core and r["noise"] == noise and r["strategy"] == strategy
            and scoreable(r) and (subset is None or r["question_id"] in subset)}


def wilson(p: int, n: int) -> list:
    if n == 0:
        return [None, None]
    z, phat = 1.959963984540054, p / n
    d = 1 + z * z / n
    c = (phat + z * z / (2 * n)) / d
    h = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def paired_cell(a: dict, b: dict) -> dict:
    """Paired comparison of two strategies on the questions both scored.

    The interval on the difference is the standard paired-proportions (McNemar) one, so a
    non-detection can be read for what it excludes rather than only for its P value."""
    q = sorted(set(a) & set(b))
    pa, pb = sum(a[k] for k in q), sum(b[k] for k in q)
    disc_b = sum(1 for k in q if a[k] == 1 and b[k] == 0)   # base passes, other fails
    disc_c = sum(1 for k in q if a[k] == 0 and b[k] == 1)
    p = (stats.binomtest(disc_b, disc_b + disc_c, 0.5).pvalue if disc_b + disc_c else 1.0)
    n = len(q)
    half = None
    if n:
        var = (disc_b + disc_c - (disc_b - disc_c) ** 2 / n) / (n * n)
        half = round(1.959963984540054 * 100 * math.sqrt(max(var, 0.0)), 1)
    return {"n_paired": n, "base_pass": pa, "other_pass": pb,
            "gap_ci95_halfwidth_pp": half,
            "base_pct": round(100 * pa / len(q), 1) if q else None,
            "other_pct": round(100 * pb / len(q), 1) if q else None,
            "base_wilson95": wilson(pa, len(q)), "other_wilson95": wilson(pb, len(q)),
            "gap_pp": round(100 * (pb - pa) / len(q), 1) if q else None,
            "discordant_base_only": disc_b, "discordant_other_only": disc_c,
            "mcnemar_exact_p": round(p, 6),
            "dropped_by_pairing": {"base": len(set(a) - set(b)), "other": len(set(b) - set(a))}}


def paired_grid(rows: list, col: str, other: str = PRIMARY, thresh: int = PASS_AT,
                subset=None, inv: dict | None = None) -> dict:
    out = {}
    for core in CORES:
        for noise in NOISE:
            a = cell_map(rows, core, noise, BASE, col, thresh, subset)
            b = cell_map(rows, core, noise, other, col, thresh, subset)
            cell = {"core_papers": int(core), "noise_ratio": int(noise),
                    "total_documents": int(core) * (1 + int(noise))}
            if inv:
                cell["chunks"] = inv[f"exp_v4_s{core}_n{noise}"]["chunks"]
                cell["rlm_reranker_on"] = inv[f"exp_v4_s{core}_n{noise}"]["rlm_reranker_on"]
            cell.update(paired_cell(a, b))
            out[f"core{core}_noise{noise}"] = cell
    ps = [c["mcnemar_exact_p"] for c in out.values()]
    for c in out.values():
        c["mcnemar_bonferroni_p"] = round(min(1.0, c["mcnemar_exact_p"] * len(ps)), 6)
    return out


def unpaired_grid(rows: list, col: str, thresh: int = PASS_AT) -> dict:
    out = {}
    for core in CORES:
        for noise in NOISE:
            cell = {"core_papers": int(core), "noise_ratio": int(noise),
                    "total_documents": int(core) * (1 + int(noise))}
            for s in STRATEGIES:
                m = cell_map(rows, core, noise, s, col, thresh)
                if not m:
                    continue
                p, n = sum(m.values()), len(m)
                cell[s] = {"pass_pct": round(100 * p / n, 1), "n_pass": p, "n": n,
                           "wilson95": wilson(p, n)}
            for s in STRATEGIES:
                if s != BASE and s in cell and BASE in cell:
                    cell[f"gap_{s}"] = round(cell[s]["pass_pct"] - cell[BASE]["pass_pct"], 1)
            out[f"core{core}_noise{noise}"] = cell
    return out


def verified_pass_budget() -> dict:
    """The retrieval-budget change that disqualifies verified_pass from corpus-scaling claims.

    The budget is not binary: it takes fifteen distinct values. What matters is that every
    verified_pass answer at 50 core papers used the raised budget and none at 5 did, so for that
    arm the budget cannot be separated from corpus size. The only configuration holding both
    budgets at usable n is 20 core papers with 3x noise, which is reported two ways."""
    src = RESULTS / "exp05_scaling_latest.json"
    # the arm as the paper reports it: the rerun with the verifier working (scripts/exp05_final.py),
    # laid over the deposited rows so the keys and the index names stay the deposit's
    final_vp = rerun_rows()
    rows = [dict(r, generation=dict(r.get("generation") or {},
                                    retrieved_passages=final_vp[(r["index_name"], r["question_id"])]["retrieved_passages"]),
                 judge_scores=final_vp[(r["index_name"], r["question_id"])]["judge_scores"])
            for r in json.load(open(src))["per_question_results"] if r["config"] == "verified_pass"]
    vp = [r for r in rows if r["config"] == "verified_pass" and r.get("answerable")
          and "correctness" in (r.get("judge_scores") or {})]
    dist = collections.Counter((r.get("generation") or {}).get("retrieved_passages") for r in vp)
    by_cell = {}
    for r in vp:
        core = r["index_name"].split("_s")[1].split("_")[0]
        by_cell.setdefault(core, collections.Counter())[
            (r.get("generation") or {}).get("retrieved_passages")] += 1
    cell = [r for r in vp if r["index_name"] == "exp_v4_s20_n3"]
    grp = {"raised": [r for r in cell
                      if (r.get("generation") or {}).get("retrieved_passages") == 15],
           "original": [r for r in cell
                        if (r.get("generation") or {}).get("retrieved_passages") != 15]}
    rate = lambda g: (round(100 * sum(r["judge_scores"]["correctness"] >= PASS_AT  # noqa: E731
                                      for r in g) / len(g), 1), len(g)) if g else None
    # question-paired within that configuration is impossible (one answer per question), so the
    # pairing the reviewers asked for is across configurations at the same budget split
    pairs = {}
    for r in vp:
        rp = (r.get("generation") or {}).get("retrieved_passages")
        pairs.setdefault(r["question_id"], {})[
            "raised" if rp == 15 else "original"] = r["judge_scores"]["correctness"] >= PASS_AT
    both = {q: v for q, v in pairs.items() if len(v) == 2}
    paired_diff = (round(100 * (sum(v["raised"] for v in both.values())
                                - sum(v["original"] for v in both.values())) / len(both), 1)
                   if both else None)
    return {"source": src.name,
            "retrieved_passages_distribution": {str(k): v for k, v in sorted(
                dist.items(), key=lambda t: (t[0] is None, t[0]))},
            "by_core_papers": {k: {str(kk): vv for kk, vv in sorted(
                v.items(), key=lambda t: (t[0] is None, t[0]))} for k, v in by_cell.items()},
            "within_20core_3x_noise": {
                "raised_budget_15": rate(grp["raised"]), "original_budget": rate(grp["original"]),
                "difference_pp": round(rate(grp["raised"])[0] - rate(grp["original"])[0], 1)},
            "paired_across_configurations": {"n_questions": len(both),
                                             "difference_pp": paired_diff},
            "note": ("all verified_pass answers at 50 core papers used the raised budget and none "
                     "at 5 core papers did, so for that arm the budget is confounded with corpus "
                     "size")}


def crossover(rows: list, col: str, paired: bool, thresh: int = PASS_AT) -> float:
    """(RLM-10 minus single-pass) at 50 core papers, minus the same at 5, pooled over noise
    ratios. This is the published test_3 contrast; paired=False reproduces it exactly."""
    def gap(core):
        a = {}
        b = {}
        for noise in NOISE:
            for k, v in cell_map(rows, core, noise, BASE, col, thresh).items():
                a[(k, noise)] = v
            for k, v in cell_map(rows, core, noise, PRIMARY, col, thresh).items():
                b[(k, noise)] = v
        if paired:
            q = set(a) & set(b)
            a = {k: a[k] for k in q}
            b = {k: b[k] for k in q}
        return sum(b.values()) / len(b) - sum(a.values()) / len(a)
    return round(100 * (gap("50") - gap("5")), 2)


def crossover_intervals(rows: list, reps: int = 10000, seed: int = 20260722,
                        batches: int = 10) -> dict:
    """Question-clustered percentile bootstrap around the crossover, all four conventions, so no
    convention travels with an interval computed for a different one."""
    import random
    qs = sorted({r["question_id"] for r in rows if r["answerable"] == "1"})
    by_q = collections.defaultdict(list)
    for r in rows:
        by_q[r["question_id"]].append(r)
    out = {}
    for col, paired in (("correctness_deposited", False), ("correctness_deposited", True),
                        ("correctness_rejudged", False), ("correctness_rejudged", True)):
        rng = random.Random(seed)
        draws = []
        for _ in range(reps):
            samp = [rng.choice(qs) for _ in qs]
            frame = []
            for i, q in enumerate(samp):
                for r in by_q[q]:
                    frame.append({**r, "question_id": f"{q}_{i}"})
            try:
                draws.append(crossover(frame, col, paired))
            except ZeroDivisionError:
                pass
        draws.sort()
        lo, hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
        chunk = max(1, len(draws) // batches)
        bnds = [sorted(draws[i:i + chunk]) for i in range(0, len(draws), chunk)][:batches]
        mcse = lambda p: round(statistics.pstdev(  # noqa: E731
            [b[int(p * len(b))] for b in bnds if b]) / math.sqrt(len(bnds)), 2)
        key = ("deposited" if "deposited" in col else "rejudged") + ("_paired" if paired
                                                                    else "_unpaired")
        out[key] = {"ci95": [round(lo, 2), round(hi, 2)], "n_reps": len(draws),
                    "mcse_lo": mcse(0.025), "mcse_hi": mcse(0.975)}
    return out


def main() -> None:
    rows, answerable = load()
    inv = index_inventory()
    common22 = answerable["5"]

    # ── S9 crash inventory ──────────────────────────────────────────────────────────────
    missing = collections.Counter()
    missing_rows = []
    for core in CORES:
        for noise in NOISE:
            for s in (BASE, PRIMARY):
                have = {r["question_id"] for r in rows
                        if r["size"] == core and r["noise"] == noise and r["strategy"] == s}
                # sorted: a set difference iterates in hash order, which Python randomises
                # per process, so this inventory's row order varied between runs and showed
                # up as a spurious difference in scripts/doctor_rerun.py
                for q in sorted(answerable[core] - have):
                    missing[(core, s)] += 1
                    missing_rows.append({"question_id": q, "strategy": s, "core_papers": int(core),
                                         "noise_ratio": int(noise)})
    if len(missing_rows) != 23 or any(m["strategy"] != PRIMARY for m in missing_rows):
        die(f"crash inventory is {len(missing_rows)} rows, expected 23 all on {PRIMARY}")
    by_core = [missing[(c, PRIMARY)] for c in CORES]
    if by_core != [7, 6, 3, 7]:
        die(f"crashes by core papers {by_core}, expected [7, 6, 3, 7]")

    # ── R1 manuscript cells ─────────────────────────────────────────────────────────────
    for s, v in {"single_pass": 83.0, "rlm_5": 63.1, "rlm_10": 61.2, "rlm_20": 62.1}.items():
        m = cell_map(rows, "50", "0", s, "correctness_deposited", PASS_AT)
        got = round(100 * sum(m.values()) / len(m), 1)
        if abs(got - v) != 0:
            die(f"deposited {s} at 50 core papers, no noise = {got}, manuscript reports {v}")

    # ── R2 the deposited fixed-subset panel ─────────────────────────────────────────────
    for r in read_csv(PANEL):
        s, size = r["strategy"], r["size"]
        m = cell_map(rows, size, "0", s, "correctness_deposited", PASS_AT, common22)
        got = (round(100 * sum(m.values()) / len(m), 1), len(m))
        if abs(got[0] - float(r["pass_pct_n0"])) > 0.05 or got[1] != int(r["n_n0"]):
            die(f"panel cell {s} at {size} core papers, no noise: {got} against "
                f"{r['pass_pct_n0']} (n={r['n_n0']})")
        pooled = {}
        for noise in NOISE:
            pooled.update({(k, noise): v for k, v in
                           cell_map(rows, size, noise, s, "correctness_deposited",
                                    PASS_AT, common22).items()})
        gp = (round(100 * sum(pooled.values()) / len(pooled), 1), len(pooled))
        if abs(gp[0] - float(r["pass_pct_pooled"])) > 0.05 or gp[1] != int(r["n_pooled"]):
            die(f"panel cell {s} at {size} core papers, pooled: {gp} against "
                f"{r['pass_pct_pooled']} (n={r['n_pooled']})")

    # ── R3 the manuscript's noise sensitivity ───────────────────────────────────────────
    def pct(core, noise, s, col, thresh=PASS_AT):
        m = cell_map(rows, core, noise, s, col, thresh)
        return round(100 * sum(m.values()) / len(m), 1)
    dep_sens = round(pct("20", "0", "rlm_5", "correctness_deposited")
                     - pct("20", "3", "rlm_5", "correctness_deposited"), 1)
    if dep_sens != 14.5:
        die(f"deposited RLM-5 noise sensitivity at 20 core papers is {dep_sens}, "
            "the manuscript reports 14.5")

    # ── R4 the published crossover ──────────────────────────────────────────────────────
    cross_dep_unpaired = crossover(rows, "correctness_deposited", paired=False)
    if abs(cross_dep_unpaired - (-25.7)) > 0.05:
        die(f"deposited unpaired crossover is {cross_dep_unpaired}, the letter reports -25.7")
    print("every gate passed: structure, crash inventory 7/6/3/7, the manuscript's four cells "
          "at 50 core papers, all 24 panel cells, the 14.5 pp noise sensitivity, and the "
          "published -25.7 pp crossover")

    # ── measurement ─────────────────────────────────────────────────────────────────────
    RJ, DEP = "correctness_rejudged", "correctness_deposited"
    grids = {
        "paired_rejudged": paired_grid(rows, RJ, inv=inv),
        "paired_rejudged_threshold4": paired_grid(rows, RJ, thresh=4, inv=inv),
        "paired_deposited_contingency": paired_grid(rows, DEP, inv=inv),
        "paired_rejudged_common22": paired_grid(rows, RJ, subset=common22, inv=inv),
        "unpaired_rejudged_all_strategies": unpaired_grid(rows, RJ),
        "unpaired_rejudged_all_strategies_threshold4": unpaired_grid(rows, RJ, thresh=4),
    }
    for s in ("multi_hop", "verified_pass", "rlm_5", "rlm_20"):
        grids[f"paired_rejudged_{s}"] = paired_grid(rows, RJ, other=s, inv=inv)

    # crashes scored as failures: add the missing answerable cells as failures, then pair
    crash_rows = list(rows)
    for m in missing_rows:
        crash_rows.append({"question_id": m["question_id"], "strategy": m["strategy"],
                           "size": str(m["core_papers"]), "noise": str(m["noise_ratio"]),
                           "answerable": "1", "empty": "0", "unjudged": "0", "gen_error": "0",
                           "category": next(r["category"] for r in rows
                                            if r["question_id"] == m["question_id"]),
                           "index_name": f"exp_v4_s{m['core_papers']}_n{m['noise_ratio']}",
                           "correctness": "0", DEP: "0", RJ: "0"})
    grids["paired_rejudged_crash_as_failure"] = paired_grid(crash_rows, RJ, inv=inv)

    # composition: the common 22 against the questions that exist only at larger subsets
    composition = {}
    for core in CORES[1:]:
        for noise in NOISE:
            entry = {}
            for s in STRATEGIES:
                m = cell_map(rows, core, noise, s, RJ, PASS_AT)
                a = {k: v for k, v in m.items() if k in common22}
                b = {k: v for k, v in m.items() if k not in common22}
                if a and b:
                    entry[s] = {"common22_pct": round(100 * sum(a.values()) / len(a), 1),
                                "common22_n_pass": sum(a.values()), "common22_n": len(a),
                                "others_pct": round(100 * sum(b.values()) / len(b), 1),
                                "others_n_pass": sum(b.values()), "others_n": len(b),
                                "difference_pp": round(100 * (sum(a.values()) / len(a)
                                                              - sum(b.values()) / len(b)), 1)}
            composition[f"core{core}_noise{noise}"] = entry

    # entry cohorts: the smallest core-paper subset at which a question is answerable
    s_min = {}
    for core in CORES:
        for q in answerable[core]:
            s_min.setdefault(q, int(core))
    cohorts = {}
    for core in CORES:
        for noise in NOISE:
            a = cell_map(rows, core, noise, BASE, RJ, PASS_AT)
            b = cell_map(rows, core, noise, PRIMARY, RJ, PASS_AT)
            q = set(a) & set(b)
            entry = {}
            for c in CORES:
                qq = {x for x in q if s_min[x] == int(c)}
                if qq:
                    entry[f"entered_at_{c}"] = {
                        "n": len(qq),
                        "gap_pp": round(100 * (sum(b[x] for x in qq) - sum(a[x] for x in qq))
                                        / len(qq), 1)}
            cohorts[f"core{core}_noise{noise}"] = entry

    cat = {r["question_id"]: r["category"] for r in rows}
    def share(qs):
        c = collections.Counter(cat[q] for q in qs)
        return {k: {"n": v, "pct": round(100 * v / len(qs), 1)} for k, v in sorted(c.items())}

    payload = {
        "_provenance": {"script": "scripts/S66_corpus_grid.py", "generated": utcnow(),
                        "inputs": [TIDY.name, REJUDGED.name, PANEL.name] +
                                  [f.name for f in INDEXES],
                        "pass_rule": f"judge correctness >= {PASS_AT}, answerable only, empty "
                                     "and unjudged excluded (analysis_deep.py:766-797)",
                        "pairing": "each cell keeps only questions scored for both compared "
                                   "strategies in that cell",
                        "gates": ["9,894 + 6,305 rows, unique join keys, 262 changes",
                                  "3,589 unmatched rows are the unanswerable set",
                                  "empty and gen_error identically zero",
                                  "answerable sets 22/44/88/200 and nested",
                                  "50 unanswerable controls identical at every size",
                                  "documents = core x (1 + noise ratio) in all 12",
                                  "23 crashes, all RLM-10, 7/6/3/7 by core papers",
                                  "manuscript cells 83.0/63.1/61.2/62.1",
                                  "all 24 deposited panel cells",
                                  "14.5 pp deposited noise sensitivity",
                                  "-25.7 pp deposited unpaired crossover"]},
        "index_inventory": inv,
        "crash_inventory": {"total": len(missing_rows), "by_core_papers": dict(zip(CORES, by_core)),
                            "rows": missing_rows},
        "grids": grids,
        "composition_common22_vs_others": composition,
        "entry_cohorts": cohorts,
        "category_composition": {"common22": share(common22),
                                 "all_answerable_200": share(answerable["50"])},
        "crossover_pp": {
            "deposited_unpaired_published": cross_dep_unpaired,
            "deposited_paired": crossover(rows, DEP, paired=True),
            "rejudged_unpaired": crossover(rows, RJ, paired=False),
            "rejudged_paired": crossover(rows, RJ, paired=True),
            "intervals": crossover_intervals(rows)},
        "verified_pass_retrieval_budget": verified_pass_budget(),
        "noise_sensitivity_rlm5_at_20_core": {
            "deposited_pp": dep_sens,
            "rejudged_pp": round(pct("20", "0", "rlm_5", RJ) - pct("20", "3", "rlm_5", RJ), 1)},
        "manuscript_cells_50_core_no_noise": {
            s: {"deposited": pct("50", "0", s, DEP), "rejudged": pct("50", "0", s, RJ)}
            for s in STRATEGIES},
    }
    (OUT / "S66_corpus_grid.json").write_text(json.dumps(payload, indent=1))

    # ── markdown ────────────────────────────────────────────────────────────────────────
    g = grids["paired_rejudged"]
    md = ["# S66 - the corpus-scaling factorial, all twelve index configurations", "",
          f"Generated {payload['_provenance']['generated']}. Every gate passed.", "",
          "Scores are the complete-answer re-judge. Pass is judge correctness at or above "
          f"{PASS_AT}. Each cell keeps only the questions scored for both strategies in that "
          "cell, so the two arms face an identical question set.", "",
          "## Single-pass against RLM-10, paired within cell", "",
          "| core papers | noise ratio | documents | chunks | RLM reranker | single-pass | "
          "RLM-10 | gap | n | McNemar P | Bonferroni P |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for core in CORES:
        for noise in NOISE:
            c = g[f"core{core}_noise{noise}"]
            md.append(
                f"| {core} | {noise}x | {c['total_documents']} | {c['chunks']} | "
                f"{'on' if c['rlm_reranker_on'] else 'off'} | "
                f"{c['base_pct']}% ({c['base_pass']}/{c['n_paired']}) | "
                f"{c['other_pct']}% ({c['other_pass']}/{c['n_paired']}) | "
                f"{c['gap_pp']:+.1f} | {c['n_paired']} | {c['mcnemar_exact_p']:.4g} | "
                f"{c['mcnemar_bonferroni_p']:.4g} |")
    md += ["", "## The same cells at the stricter threshold of 4", "",
           "| core papers | noise ratio | single-pass | RLM-10 | gap |", "|---|---|---|---|---|"]
    for core in CORES:
        for noise in NOISE:
            c = grids["paired_rejudged_threshold4"][f"core{core}_noise{noise}"]
            md.append(f"| {core} | {noise}x | {c['base_pct']}% | {c['other_pct']}% | "
                      f"{c['gap_pp']:+.1f} |")
    md += ["", "## Every strategy against single-pass, paired, gap in percentage points", "",
           "| core papers | noise ratio | " + " | ".join(
               s for s in STRATEGIES if s != BASE) + " |",
           "|---|---|" + "---|" * (len(STRATEGIES) - 1)]
    for core in CORES:
        for noise in NOISE:
            cells = []
            for s in STRATEGIES:
                if s == BASE:
                    continue
                gk = "paired_rejudged" if s == PRIMARY else f"paired_rejudged_{s}"
                c = grids[gk][f"core{core}_noise{noise}"]
                cells.append(f"{c['gap_pp']:+.1f}")
            md.append(f"| {core} | {noise}x | " + " | ".join(cells) + " |")
    md += ["", "## Crashes scored as failures rather than dropped", "",
           f"All {len(missing_rows)} missing answerable cells are RLM-10 generations, "
           f"{by_core[0]} / {by_core[1]} / {by_core[2]} / {by_core[3]} across 5 / 10 / 20 / 50 "
           "core papers, so they concentrate where the corpus is small and dropping them is the "
           "anti-conservative convention.", "",
           "| core papers | noise ratio | single-pass | RLM-10 | gap |", "|---|---|---|---|---|"]
    for core in CORES:
        for noise in NOISE:
            c = grids["paired_rejudged_crash_as_failure"][f"core{core}_noise{noise}"]
            md.append(f"| {core} | {noise}x | {c['base_pct']}% | {c['other_pct']}% | "
                      f"{c['gap_pp']:+.1f} |")
    comp = composition["core50_noise0"]
    md += ["", "## Composition, inside the 50-core index with no noise", "",
           "| strategy | common 22 | the others | difference |", "|---|---|---|---|"]
    for s in STRATEGIES:
        e = comp[s]
        md.append(f"| {s} | {e['common22_pct']}% ({e['common22_n_pass']}/{e['common22_n']}) | "
                  f"{e['others_pct']}% ({e['others_n_pass']}/{e['others_n']}) | "
                  f"{e['difference_pp']:+.1f} pp |")
    md += ["", "## Category composition", "", "| category | common 22 | all 200 answerable |",
           "|---|---|---|"]
    for k in sorted(payload["category_composition"]["all_answerable_200"]):
        a = payload["category_composition"]["common22"].get(k, {"n": 0, "pct": 0.0})
        b = payload["category_composition"]["all_answerable_200"][k]
        md.append(f"| {k} | {a['n']} ({a['pct']}%) | {b['n']} ({b['pct']}%) |")
    c = payload["crossover_pp"]
    md += ["", "## The crossover contrast, four conventions", "",
           "| convention | deposited | re-judged |", "|---|---|---|",
           f"| unpaired, pooled over noise ratios (the published test) | "
           f"{c['deposited_unpaired_published']} | {c['rejudged_unpaired']} |",
           f"| paired within cell | {c['deposited_paired']} | {c['rejudged_paired']} |", "",
           "## Retrieval configuration, from the deposited index-creation records", "",
           "| configuration | documents | chunks | RLM reranker |", "|---|---|---|---|"]
    for core in CORES:
        for noise in NOISE:
            i = inv[f"exp_v4_s{core}_n{noise}"]
            md.append(f"| {core} core, {noise}x noise | {i['total_documents']} | {i['chunks']} | "
                      f"{'on' if i['rlm_reranker_on'] else 'off'} |")
    md += ["", f"The RLM retrieval path enables a cross-encoder reranker above "
           f"{RERANKER_CHUNKS} chunks (backend/retrieval/rlm/context.py:200). The non-RLM "
           "strategies use the harness retriever, which sets it unconditionally "
           "(tests/experiments_v4/exp_common.py:196). In the no-noise row the threshold falls "
           "exactly between 20 and 50 core papers; across the twelve configurations it does not "
           "track core papers, which is why the twelve-cell model can carry it as a covariate."]
    (OUT / "S66_corpus_grid.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[6:]))
    print(f"\nwrote {OUT / 'S66_corpus_grid.json'} and .md")


if __name__ == "__main__":
    main()
