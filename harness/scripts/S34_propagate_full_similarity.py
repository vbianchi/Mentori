#!/usr/bin/env python3
"""S34 - every derived number that moves when the deterministic signal reads complete answers.

Two input corrections now apply to the exp04 evaluation, and they hit different signals:

    judge          published prompt cut the answer at 3,000 characters; S21 arm F re-ran it on
                   complete answers (39 of the 528 answerable scores change).
    deterministic  the bge-m3 similarity component was computed on the first 2,000 characters
                   (analysis_deterministic_scorer.py:277-278); S30/S33 recomputed it on complete
                   answers (29 correctness and 22 faithfulness scores change).

This script recomputes every quantity the response and the manuscript build on those two
signals, in three states, so the effect of each correction is separable:

    P  published      deposited judge, deposited deterministic
    C  current        re-judged, deposited deterministic   (what the response says today)
    N  new            re-judged, full-answer deterministic (what it should say)

Quantities: mean pairwise Spearman rho between the three signals, PC1 share, participation
ratio, Kendall's W with its exact permutation p, the seven-row metric-subset ranking table,
the unique-failure cells, and the four Fig. 5c judge-versus-deterministic correlations.

Gates. State P must reproduce the published values (mean rho 0.867, PC1 91.2%, PR 1.19,
W 0.9111, cells 156/15/1/154, Fig 5c 0.502/0.608/0.167/0.257) and state C must reproduce the
values currently written in the response (0.904, 93.6%, 1.14, 0.9270, 155/15/1/153,
0.504/0.621/0.131/0.205). If either fails, the third state means nothing and the script says so
rather than writing its output.

Outputs: findings/recompute/S34_propagation.json + .md
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, RESULTS  # noqa: E402

OUT = RECOMPUTE
SRC = "exp04_generation_latest.json"
CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
SEED, N_BOOT = 42, 2000
T_FAITH, T_PREC = 4.0, 0.5

GATE_P = {"rho": 0.867, "pc1": 0.912, "pr": 1.19, "W": 0.9111,
          "cells": (156, 15, 1, 154), "fig5c": (0.502, 0.608, 0.167, 0.257)}
GATE_C = {"rho": 0.904, "pc1": 0.936, "pr": 1.14, "W": 0.9270,
          "cells": (155, 15, 1, 153), "fig5c": (0.504, 0.621, 0.131, 0.205)}


def utcnow() -> str:
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def judged_rows(o):
    if isinstance(o, dict):
        if "judge_scores" in o:
            yield o
        for v in o.values():
            yield from judged_rows(v)
    elif isinstance(o, list):
        for v in o:
            yield from judged_rows(v)


def load() -> pd.DataFrame:
    ans = pd.read_csv(OUT / "master_join.csv").query("answerable == True").copy()  # noqa: E712
    s30 = pd.read_csv(OUT / "S30_baseline_scores_full.csv")[
        ["question_id", "config", "det_score_correctness_fullsim",
         "det_score_faithfulness_fullsim", "bge_sim_full"]]
    ans = ans.merge(s30, on=["question_id", "config"], how="left", validate="one_to_one")
    assert ans["det_score_correctness_fullsim"].notna().all(), "S30 join incomplete"

    idx = {(r.get("question_id"), r.get("config")): i
           for i, r in enumerate(judged_rows(json.load(open(RESULTS / SRC))))}
    new = {}
    for line in open(OUT / "S21_rejudge_raw.jsonl"):
        d = json.loads(line)
        if d["file"] == SRC and d["arm"] == "F" and d.get("parsed"):
            new[d["row_idx"]] = d["parsed"]

    for dim in DIMS:
        col = f"judge_{dim}"
        vals = []
        for _, r in ans.iterrows():
            i = idx.get((r["question_id"], r["config"]))
            vals.append(float(new[i][dim]) if (i is not None and i in new and dim in new[i])
                        else float(r[col]))
        ans[f"{col}_full"] = vals
    return ans


def kendalls_w(rank_matrix: np.ndarray) -> float:
    k, n = rank_matrix.shape
    rank_sums = rank_matrix.sum(axis=0)
    s = float(np.sum((rank_sums - rank_sums.mean()) ** 2))
    return 12.0 * s / (k ** 2 * (n ** 3 - n))


def exact_w_p(rank_matrix: np.ndarray) -> float:
    """Exact permutation p: enumerate all rank permutations of two raters against a fixed third
    (W is invariant to a common relabeling of the items), as in S06_metric_ablation.py."""
    observed = kendalls_w(rank_matrix)
    base = rank_matrix[0]
    perms = list(itertools.permutations(range(1, rank_matrix.shape[1] + 1)))
    hits = total = 0
    for p1 in perms:
        a = np.array(p1, dtype=float)
        for p2 in perms:
            m = np.vstack([base, a, np.array(p2, dtype=float)])
            total += 1
            if kendalls_w(m) >= observed - 1e-12:
                hits += 1
    return hits / total


def signal_vectors(df: pd.DataFrame, judge_col: str, det_col: str) -> dict:
    g = df.groupby("config")
    return {"det": np.array([g[det_col].mean()[c] for c in CONFIGS], dtype=float),
            "judge": np.array([g[judge_col].mean()[c] for c in CONFIGS], dtype=float),
            "mc": np.array([g["mc_f1"].mean()[c] * 5.0 for c in CONFIGS], dtype=float)}


def triple_stats(vecs: dict) -> tuple:
    ps = np.vstack([vecs["det"], vecs["judge"], vecs["mc"]])
    corr = np.ones((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                corr[i, j] = stats.spearmanr(ps[i], ps[j]).statistic
    eig = np.sort(np.linalg.eigvalsh(corr))
    return (float(np.mean([corr[0, 1], corr[0, 2], corr[1, 2]])),
            float(eig[-1] / eig.sum()),
            float(eig.sum() ** 2 / np.sum(eig ** 2)))


def subset_table(vecs: dict) -> dict:
    ranks = {k: stats.rankdata(v) for k, v in vecs.items()}
    agg = lambda s: stats.rankdata(np.mean([ranks[p] for p in s], axis=0))  # noqa: E731
    triple = agg(("det", "judge", "mc"))
    out = {}
    for s in [("det",), ("judge",), ("mc",), ("det", "judge"), ("det", "mc"), ("judge", "mc")]:
        r = agg(s)
        out["+".join(s)] = {"rho": round(float(stats.spearmanr(r, triple).statistic), 4),
                            "tau": round(float(stats.kendalltau(r, triple).statistic), 4)}
    out["triple_order_best_to_worst"] = [CONFIGS[i] for i in np.argsort(-triple)]
    return out


def cells(df: pd.DataFrame, judge_faith: str, det_faith: str, judge_pass_col: str) -> dict:
    jf = df[judge_faith] < T_FAITH
    dt = df[det_faith] < T_FAITH
    mc = df["mc_precision"] < T_PREC
    return {"only_mc": int((mc & ~jf & ~dt).sum()),
            "only_det": int((dt & ~jf & ~mc).sum()),
            "only_judge": int((jf & ~dt & ~mc).sum()),
            "only_mc_judge_pass": int(((df[judge_faith] >= T_FAITH) & (df[det_faith] >= T_FAITH)
                                       & mc & (df[judge_pass_col] == True)).sum())}  # noqa: E712


def fig5c(df: pd.DataFrame, judge_suffix: str, det_map: dict) -> dict:
    out = {}
    for dim in DIMS:
        j = df[f"judge_{dim}{judge_suffix}"]
        d = df[det_map[dim]]
        out[dim] = round(float(stats.spearmanr(d, j).statistic), 4)
    return out


def state(df: pd.DataFrame, judge_suffix: str, det_corr: str, det_faith: str,
          judge_pass_col: str, det_map: dict, with_boot: bool = False) -> dict:
    vecs = signal_vectors(df, f"judge_correctness{judge_suffix}", det_corr)
    rho, pc1, pr = triple_stats(vecs)
    ranks = np.vstack([stats.rankdata(vecs[k]) for k in ("det", "judge", "mc")])
    W = kendalls_w(ranks)
    # a tied ranking (average ranks, no tie correction) against an untied null: W and its exact P
    # with the tie broken each way, so the reported P can be bounded (Methods, Statistics)
    tie_bounds = []
    for r_i in range(ranks.shape[0]):
        vals, cnt = np.unique(ranks[r_i], return_counts=True)
        for v in vals[cnt == 2]:
            idx = np.where(ranks[r_i] == v)[0]
            for lo, hi in ((0, 1), (1, 0)):
                m = ranks.copy()
                m[r_i][idx[0]], m[r_i][idx[1]] = v - 0.5 + lo, v - 0.5 + hi
                tie_bounds.append({"rater": ("det", "judge", "mc")[r_i], "items": [CONFIGS[i] for i in idx],
                                   "kendalls_w": round(kendalls_w(m), 4), "exact_p": round(exact_w_p(m), 6)})
    res = {"kendalls_w_tie_broken": tie_bounds,
           "mean_pairwise_rho": round(rho, 4), "pc1": round(pc1, 4),
           "participation_ratio": round(pr, 4), "kendalls_w": round(W, 4),
           "kendalls_w_exact_p": round(exact_w_p(ranks), 6),
           "subsets": subset_table(vecs),
           "cells": cells(df, f"judge_faithfulness{judge_suffix}", det_faith, judge_pass_col),
           "fig5c": fig5c(df, judge_suffix, det_map),
           "config_mean_det_correctness": {c: round(float(df.groupby("config")[det_corr].mean()[c]), 4)
                                           for c in CONFIGS}}
    if with_boot:
        piv = {"det": df.pivot_table(index="question_id", columns="config", values=det_corr)[CONFIGS],
               "judge": df.pivot_table(index="question_id", columns="config",
                                       values=f"judge_correctness{judge_suffix}")[CONFIGS],
               "mc": df.pivot_table(index="question_id", columns="config", values="mc_f1")[CONFIGS]}
        scale = {"det": 1.0, "judge": 1.0, "mc": 5.0}
        qids = df["question_id"].unique()
        rng = np.random.default_rng(SEED)
        B = []
        for _ in range(N_BOOT):
            bq = rng.choice(qids, size=len(qids), replace=True)
            B.append(triple_stats({k: piv[k].loc[bq].mean(axis=0).to_numpy(float) * scale[k]
                                   for k in piv}))
        B = np.array(B)
        res["bootstrap"] = {
            "n_resamples": N_BOOT, "seed": SEED,
            "rho_ci": [round(float(x), 4) for x in np.percentile(B[:, 0], [2.5, 97.5])],
            "pc1_ci": [round(float(x), 4) for x in np.percentile(B[:, 1], [2.5, 97.5])],
            "pr_ci": [round(float(x), 4) for x in np.percentile(B[:, 2], [2.5, 97.5])],
            "pc1_below_090_share": round(float(np.mean(B[:, 1] < 0.90)), 4)}
    return res


def check(label: str, got: dict, want: dict, tol: float = 0.0015) -> list:
    bad = []
    for key, w in (("rho", "mean_pairwise_rho"), ("pc1", "pc1"),
                   ("pr", "participation_ratio"), ("W", "kendalls_w")):
        if abs(got[w] - want[key]) > (tol if key != "pr" else 0.006):
            bad.append(f"{label}: {w} = {got[w]}, expected {want[key]}")
    c = got["cells"]
    if (c["only_mc"], c["only_det"], c["only_judge"], c["only_mc_judge_pass"]) != want["cells"]:
        bad.append(f"{label}: cells = {c}, expected {want['cells']}")
    for dim, w in zip(DIMS, want["fig5c"]):
        if abs(got["fig5c"][dim] - w) > 0.0015:
            bad.append(f"{label}: fig5c {dim} = {got['fig5c'][dim]}, expected {w}")
    return bad


def main() -> None:
    t0 = time.time()
    ts = utcnow()
    print(f"[S34] start {ts}")
    df = load()
    print(f"[S34] {len(df)} answerable rows; judge correctness changed on "
          f"{int((df['judge_correctness_full'] != df['judge_correctness']).sum())}, "
          f"deterministic correctness on "
          f"{int((df['det_score_correctness_fullsim'] != df['det_score_correctness']).sum())}")

    det_dep = {"correctness": "det_score_correctness", "completeness": "det_score_completeness",
               "faithfulness": "det_score_faithfulness",
               "citation_quality": "det_score_citation_quality"}
    det_new = dict(det_dep, correctness="det_score_correctness_fullsim",
                   faithfulness="det_score_faithfulness_fullsim")

    P = state(df, "", "det_score_correctness", "det_score_faithfulness", "judge_pass", det_dep)
    C = state(df, "_full", "det_score_correctness", "det_score_faithfulness", "judge_pass", det_dep)
    N = state(df, "_full", "det_score_correctness_fullsim", "det_score_faithfulness_fullsim",
              "judge_pass", det_new, with_boot=True)

    problems = check("published", P, GATE_P) + check("current", C, GATE_C)
    if problems:
        print("[S34] GATE FAILURE, nothing written:")
        for p in problems:
            print(f"   {p}")
        sys.exit(1)
    print("[S34] gates pass: published and current states both reproduce")

    result = {"_provenance": {"script": "scripts/S34_propagate_full_similarity.py",
                              "generated": ts,
                              "wall_clock_runtime_seconds": round(time.time() - t0, 1),
                              "states": {"P": "deposited judge + deposited deterministic",
                                         "C": "re-judged + deposited deterministic",
                                         "N": "re-judged + full-answer deterministic"},
                              "depends_on": ["S21_rejudge_raw.jsonl",
                                             "S30_baseline_scores_full.csv"]},
              "published": P, "current": C, "new": N}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "S34_propagation.json").write_text(json.dumps(result, indent=2))

    def row(name, a, b, c, fmt="{:.4f}"):
        return (f"| {name} | {fmt.format(a)} | {fmt.format(b)} | {fmt.format(c)} | "
                f"{'yes' if abs(c - b) > 1e-9 else 'no'} |")

    L = ["# S34 - propagation of the complete-answer corrections", "",
         f"Generated: {ts} | n = {len(df)} answerable answers", "",
         "P = as published. C = judge re-run on complete answers (what the response says today). "
         "N = judge re-run and deterministic similarity on complete answers.", "",
         "| quantity | P published | C current | N new | moves |", "|---|---|---|---|---|",
         row("mean pairwise rho", P["mean_pairwise_rho"], C["mean_pairwise_rho"],
             N["mean_pairwise_rho"]),
         row("PC1 share", P["pc1"], C["pc1"], N["pc1"]),
         row("participation ratio", P["participation_ratio"], C["participation_ratio"],
             N["participation_ratio"]),
         row("Kendall W", P["kendalls_w"], C["kendalls_w"], N["kendalls_w"]),
         row("Kendall W exact p", P["kendalls_w_exact_p"], C["kendalls_w_exact_p"],
             N["kendalls_w_exact_p"], "{:.6f}"),
         row("deterministic alone, rho vs triple", P["subsets"]["det"]["rho"],
             C["subsets"]["det"]["rho"], N["subsets"]["det"]["rho"]),
         row("judge alone, rho vs triple", P["subsets"]["judge"]["rho"],
             C["subsets"]["judge"]["rho"], N["subsets"]["judge"]["rho"]),
         row("deterministic+judge, rho vs triple", P["subsets"]["det+judge"]["rho"],
             C["subsets"]["det+judge"]["rho"], N["subsets"]["det+judge"]["rho"]),
         ]
    for k, label in (("only_mc", "caught only by MiniCheck"),
                     ("only_det", "caught only by the deterministic signal"),
                     ("only_judge", "caught only by the judge"),
                     ("only_mc_judge_pass", "of those, judge passes")):
        L.append(row(label, P["cells"][k], C["cells"][k], N["cells"][k], "{:.0f}"))
    for dim in DIMS:
        L.append(row(f"Fig 5c {dim}", P["fig5c"][dim], C["fig5c"][dim], N["fig5c"][dim]))
    b = N["bootstrap"]
    L += ["", "## Intervals for the new state (cluster bootstrap, "
          f"{b['n_resamples']} resamples, seed {b['seed']})", "",
          f"- mean pairwise rho 95% CI {b['rho_ci'][0]} to {b['rho_ci'][1]}",
          f"- PC1 95% CI {b['pc1_ci'][0]} to {b['pc1_ci'][1]}, below 0.90 in "
          f"{b['pc1_below_090_share'] * 100:.1f}% of draws",
          f"- participation ratio 95% CI {b['pr_ci'][0]} to {b['pr_ci'][1]}", "",
          "## Three-signal configuration order", "",
          f"- published: {' > '.join(P['subsets']['triple_order_best_to_worst'])}",
          f"- new: {' > '.join(N['subsets']['triple_order_best_to_worst'])}", ""]
    (OUT / "S34_propagation.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[4:]))
    print(f"[S34] wrote {OUT / 'S34_propagation.json'} and .md in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()
