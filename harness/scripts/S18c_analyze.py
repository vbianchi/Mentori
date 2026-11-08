"""S18c - pre-registered analysis of the six-arm grounded re-judge.

Reads findings/recompute/S18_rejudge_raw.jsonl only. Every number the write-up may quote is
emitted to S18_results.json; nothing is computed in prose.

Contrasts, each isolating one variable:
  A  vs published   replication GATE          (does the re-run reproduce the deposited scores)
  B  vs B2          noise floor               (the judge's own run-to-run variability)
  A  vs A2          context inertness         (does num_ctx alone move anything)
  A2 vs B           truncation effect         (the 3000-char cut)
  C  vs B           evidence effect, total
  D  vs B           irrelevant-text effect    (same bulk, wrong paper)
  C  vs D           evidence CONTENT effect   <- PRIMARY
"""
from __future__ import annotations
import json, math, argparse, sys
from pathlib import Path
from collections import defaultdict
from statistics import mean

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, rel  # noqa: E402

OUT = RECOMPUTE
RAW = OUT / "S18_rejudge_raw.jsonl"
DIMS = ["faithfulness", "correctness", "completeness", "citation_quality"]
PRIMARY = "faithfulness"
GATE_EXACT = 0.95
GATE_MAD = 0.05
SEED = 42


def load(path):
    rows = [json.loads(l) for l in open(path)]
    by = {}
    for r in rows:
        if r.get("parsed"):
            by[(r["arm"], r["question_id"], r["config"])] = r
    return rows, by


def paired(by, arm_x, arm_y, dim, keys):
    x, y, qids = [], [], []
    for (q, c) in keys:
        a, b = by.get((arm_x, q, c)), by.get((arm_y, q, c))
        if a and b:
            x.append(a["parsed"][dim]); y.append(b["parsed"][dim]); qids.append(q)
    return np.array(x, float), np.array(y, float), qids


def cluster_boot_diff(x, y, qids, stat, n=2000, seed=SEED):
    """Bootstrap the difference in `stat` resampling QUESTIONS (6 answers move together)."""
    rng = np.random.default_rng(seed)
    idx = defaultdict(list)
    for i, q in enumerate(qids):
        idx[q].append(i)
    qs = list(idx)
    out = []
    for _ in range(n):
        pick = rng.choice(len(qs), len(qs), replace=True)
        sel = [i for k in pick for i in idx[qs[k]]]
        out.append(stat(x[sel]) - stat(y[sel]))
    lo, hi = np.percentile(out, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


def tost_equivalence(x, y, qids, margin_pp=5.0, n=10000):
    """Two one-sided tests for the 'the judge ignores the evidence' branch.

    An insensitivity claim is an EQUIVALENCE claim and cannot be made by failing to reject a
    difference. We assert it only if the cluster-bootstrap 95% CI on the difference in the
    share scored 5 lies entirely inside (-margin, +margin).
    """
    lo, hi = cluster_boot_diff(x, y, qids, lambda v: float((v == 5).mean()), n=n)
    lo_pp, hi_pp = 100 * lo, 100 * hi
    return {"margin_pp": margin_pp,
            "ci95_pp": [round(lo_pp, 2), round(hi_pp, 2)],
            "equivalent": bool(lo_pp > -margin_pp and hi_pp < margin_pp),
            "n_boot": n}


def compare(by, ax, ay, keys, label):
    res = {"contrast": f"{ax} vs {ay}", "label": label, "dims": {}}
    for dim in DIMS:
        x, y, qids = paired(by, ax, ay, dim, keys)
        if len(x) == 0:
            res["dims"][dim] = {"n": 0}
            continue
        d = x - y
        exact = float((d == 0).mean())
        mad = float(np.abs(d).mean())
        # Wilcoxon on the paired ordinal scores
        try:
            w_p = float(stats.wilcoxon(x, y, zero_method="wilcox").pvalue) if np.any(d) else 1.0
        except ValueError:
            w_p = 1.0
        # McNemar on the binary "scored 5"
        b = int(((x == 5) & (y != 5)).sum())
        c = int(((x != 5) & (y == 5)).sum())
        mc_p = float(stats.binomtest(min(b, c), b + c, 0.5).pvalue) if (b + c) else 1.0
        f5x, f5y = float((x == 5).mean()), float((y == 5).mean())
        lo, hi = cluster_boot_diff(x, y, qids, lambda v: float((v == 5).mean()))
        mlo, mhi = cluster_boot_diff(x, y, qids, lambda v: float(v.mean()))
        res["dims"][dim] = {
            "n": int(len(x)),
            "mean_x": round(float(x.mean()), 4), "mean_y": round(float(y.mean()), 4),
            "mean_diff": round(float(d.mean()), 4), "mean_diff_ci95": [mlo, mhi],
            "exact_agreement": round(exact, 4), "mean_abs_diff": round(mad, 4),
            "share5_x": round(f5x, 4), "share5_y": round(f5y, 4),
            "share5_diff_pp": round(100 * (f5x - f5y), 2),
            "share5_diff_ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)],
            "wilcoxon_p": w_p,
            "mcnemar_5_b": b, "mcnemar_5_c": c, "mcnemar_5_p": mc_p,
            "mcnemar_note": "unclustered; 6 answers per question are not independent. "
                            "The cluster bootstrap CI above is the primary inference; this "
                            "p-value is descriptive only.",
            "n_discordant_bc": b + c,
            "tost": tost_equivalence(x, y, qids) if dim == PRIMARY else None,
        }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(RAW))
    ap.add_argument("--subset", default="full", choices=["full", "selected", "all"],
                    help="evidence mode restriction for the primary analysis")
    a = ap.parse_args()

    rows, by = load(a.raw)
    arms = sorted({r["arm"] for r in rows})
    print(f"rows: {len(rows)}   parsed: {len(by)}   arms: {arms}")
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        pf = sum(1 for r in rs if not r.get("parsed"))
        er = sum(1 for r in rs if r.get("error"))
        hc = sum(1 for r in rs if r.get("hit_ceiling"))
        print(f"  {arm:<3} n={len(rs):>4}  parse_fail={pf:<3} errors={er:<3} hit_ceiling={hc}")
        if hc:
            print("    *** CONTEXT CEILING HIT - results for this arm are invalid ***")

    # evidence mode per question, taken from arm C rows
    mode = {}
    for r in rows:
        if r["arm"] == "C" and r.get("evidence_mode"):
            mode[r["question_id"]] = r["evidence_mode"].split(":")[-1]
    keys_all = sorted({(q, c) for (arm, q, c) in by})
    keys = keys_all if a.subset == "all" else [k for k in keys_all if mode.get(k[0]) == a.subset]
    print(f"\nevidence-mode restriction '{a.subset}': {len(keys)} of {len(keys_all)} answers "
          f"({len({k[0] for k in keys})} questions)")

    # ---------------------------------------------------------------- gate
    A = [(k, by[("A",) + k]) for k in keys_all if ("A",) + k in by]

    def gate_for(rows):
        g = {}
        for dim in DIMS:
            xs = np.array([r["parsed"][dim] for _, r in rows], float)
            ys = np.array([(r["published"] or {}).get(dim, np.nan) for _, r in rows], float)
            ok = ~np.isnan(ys)
            if not ok.any():
                g[dim] = {"n": 0}
                continue
            d = xs[ok] - ys[ok]
            g[dim] = {"n": int(ok.sum()),
                      "exact_agreement": round(float((d == 0).mean()), 4),
                      "mean_abs_diff": round(float(np.abs(d).mean()), 4),
                      "mean_diff": round(float(d.mean()), 4)}
        return g

    # The deposited scores are a two-pass mixture: 189 of 528 answerable rows errored in the main
    # judging pass and were re-scored by exp_v4_4_fixup.py across 6 parallel Ollama instances
    # (findings/S18_TWO_PASS_JUDGING.md). A single-instance re-run is only strictly comparable to
    # the main pass, so the gate is evaluated on that stratum and the fixup rows are reported
    # alongside rather than pooled.
    strata = {"all": A,
              "main": [(k, r) for k, r in A if r.get("published_origin") == "main"],
              "fixup": [(k, r) for k, r in A if r.get("published_origin") == "fixup"]}
    gates = {name: gate_for(rows) for name, rows in strata.items() if rows}
    gate = gates.get("all", {})
    primary_stratum = "main" if "main" in gates else "all"
    gp = gates[primary_stratum][PRIMARY]
    gate_pass = (gp.get("exact_agreement", 0) >= GATE_EXACT
                 and gp.get("mean_abs_diff", 9) <= GATE_MAD)

    print(f"\n{'='*70}\nREPLICATION GATE (arm A vs deposited scores)\n{'='*70}")
    print(f"{'stratum':<10}{'dimension':<18}{'n':>5}{'exact':>9}{'mean|diff|':>12}")
    for name in ("main", "fixup", "all"):
        if name not in gates:
            continue
        for dim in DIMS:
            g = gates[name][dim]
            if not g.get("n"):
                continue
            print(f"{name:<10}{dim:<18}{g['n']:>5}{100*g['exact_agreement']:>8.1f}%"
                  f"{g['mean_abs_diff']:>12.3f}")
    print(f"\n  criterion: faithfulness exact >= {100*GATE_EXACT:.0f}% and "
          f"mean|diff| <= {GATE_MAD}, judged on the '{primary_stratum}' stratum")
    print(f"  GATE: {'PASS' if gate_pass else 'FAIL'}")

    # ---------------------------------------------------------------- contrasts
    plan = [("B", "B2", "noise floor: identical inputs, two runs"),
            ("A", "A2", "context inertness: num_ctx only"),
            ("A2", "B", "truncation effect: 3000-char cut removed"),
            ("C", "B", "evidence effect, total"),
            ("D", "B", "irrelevant-text effect: same bulk, wrong paper"),
            ("C", "D", "PRIMARY: evidence content effect")]
    contrasts = []
    print(f"\n{'='*70}\nCONTRASTS on {PRIMARY} (subset={a.subset})\n{'='*70}")
    print(f"{'contrast':<10}{'n':>5}{'mean_x':>9}{'mean_y':>9}{'diff':>8}"
          f"{'5/5 x':>8}{'5/5 y':>8}{'d pp':>8}{'CI95 pp':>18}{'wilcox p':>11}")
    for ax, ay, lab in plan:
        r = compare(by, ax, ay, keys, lab)
        contrasts.append(r)
        d = r["dims"][PRIMARY]
        if not d.get("n"):
            print(f"{ax}-{ay:<7} (no data)")
            continue
        ci = d["share5_diff_ci95_pp"]
        print(f"{ax+'-'+ay:<10}{d['n']:>5}{d['mean_x']:>9.3f}{d['mean_y']:>9.3f}"
              f"{d['mean_diff']:>8.3f}{100*d['share5_x']:>7.1f}%{100*d['share5_y']:>7.1f}%"
              f"{d['share5_diff_pp']:>8.1f}{f'[{ci[0]:.1f}, {ci[1]:.1f}]':>18}"
              f"{d['wilcoxon_p']:>11.2e}")

    res = {
        "_provenance": {"script": "scripts/S18c_analyze.py", "raw": rel(a.raw),
                        "subset": a.subset, "seed": SEED,
                        "n_rows": len(rows), "n_parsed": len(by)},
        "arms_present": arms,
        "per_arm_health": {arm: {
            "n": sum(1 for r in rows if r["arm"] == arm),
            "parse_failures": sum(1 for r in rows if r["arm"] == arm and not r.get("parsed")),
            "errors": sum(1 for r in rows if r["arm"] == arm and r.get("error")),
            "hit_ceiling": sum(1 for r in rows if r["arm"] == arm and r.get("hit_ceiling")),
        } for arm in arms},
        "evidence_mode_counts": {m: sum(1 for v in mode.values() if v == m) for m in set(mode.values())},
        "replication_gate": {"criterion_exact": GATE_EXACT, "criterion_mad": GATE_MAD,
                             "per_dimension": gate, "by_stratum": gates,
                             "primary_stratum": primary_stratum, "pass": bool(gate_pass),
                             "note": "deposited scores are a two-pass mixture; the gate is judged "
                                     "on the main-pass rows (see findings/S18_TWO_PASS_JUDGING.md)"},
        "contrasts": contrasts,
        "primary_dimension": PRIMARY,
        "n_answers_in_subset": len(keys),
    }
    json.dump(res, open(OUT / f"S18_results_{a.subset}.json", "w"), indent=1)
    print(f"\nwrote {OUT / f'S18_results_{a.subset}.json'}")
    if not gate_pass:
        print("\nNOTE: the gate did not pass. Per the pre-registration the evidence contrasts "
              "must NOT be reported as a controlled comparison against the published run.")


if __name__ == "__main__":
    main()
