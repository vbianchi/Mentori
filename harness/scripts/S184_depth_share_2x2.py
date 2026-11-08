#!/usr/bin/env python3
"""S184 - the seven-turn share, on all four bases, so the abstract and the figure can agree.

The abstract says seven turns capture "80-86%" of the improvement. Letter paragraph [226] says
the figure reports the crashes-excluded choice, "75% to 82%". Both are true statements about
different things and neither is the number the revision should print, because:

  80-86%  is the BALANCED question set with the 53 depth-1 turn-cap crashes scored as zeros
          (S45, pct_of_plateau_at_depth_7 0.7950 and 0.8589)
  75-82%  is ALL questions with those crashes EXCLUDED
          (S10, fits.crashes_out, 0.7528 and 0.8229)

So the two numbers differ on two axes at once, and the balanced-and-crashes-excluded cell,
which is the one the revision's own choices imply, had never been computed. Letter [224] makes
the balanced set primary for the fitted seven-turn share; letter [226] says the figure excludes
crashes. Their intersection is this script.

CONVENTION. The balanced question set is fixed FIRST, on the full record set, as the questions
answered at all ten depths. Crashes are dropped afterwards. Defining balance after dropping
crashes would re-select the questions on an outcome and is not done.

GATE. Refuses to write unless it reproduces S10 on both all-question anchors and S45 on the
balanced crashes-in anchor, to four decimal places.

Writes findings/recompute/S184_depth_share_2x2.json + .md
"""
from __future__ import annotations
import json, subprocess, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RESULTS, shown  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = RESULTS
OUT = ROOT / "findings/recompute"
PRIMARY = RES / "exp09_depth_sweep_gemini-3-flash-preview_merged.json"

# What must reproduce before anything here is believed.
GATE = {
    ("all", "crashes_in", "logistic"): 0.8426,
    ("all", "crashes_in", "satexp"): 0.7811,
    ("all", "crashes_out", "logistic"): 0.7528,
    ("all", "crashes_out", "satexp"): 0.8229,
    ("balanced", "crashes_in", "logistic"): 0.8589,
    ("balanced", "crashes_in", "satexp"): 0.7950,
}
TOL = 5e-4


def utcnow() -> str:
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def is_crash(r) -> bool:
    e = r.get("error")
    return bool(e) and "Maximum turns" in e


def f_logistic(d, L, k, d0):
    return L / (1.0 + np.exp(-k * (np.asarray(d, float) - d0)))


def f_satexp(d, L, k):
    return L * (1.0 - np.exp(-k * np.asarray(d, float)))


def r2(y, yhat) -> float:
    y = np.asarray(y, float)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot else float("nan")


def fit(x, y, kind):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if kind == "logistic":
        popt, _ = curve_fit(f_logistic, x, y, p0=[0.5, 0.5, 3.0],
                            bounds=([0, 0, -10], [2, 10, 60]), maxfev=200000)
        yhat = f_logistic(x, *popt)
    else:
        popt, _ = curve_fit(f_satexp, x, y, p0=[0.5, 0.3],
                            bounds=([0, 0], [2, 10]), maxfev=200000)
        yhat = f_satexp(x, *popt)
    return [float(v) for v in popt], r2(y, yhat)


def share_at_7(kind, popt) -> float:
    """(fit(7) - fit(1)) / (L - fit(1)), S10's definition."""
    f = f_logistic if kind == "logistic" else f_satexp
    L, base = popt[0], float(f(1, *popt))
    return (float(f(7, *popt)) - base) / (L - base) if L != base else float("nan")


def cell(records, qset, anchor) -> dict:
    recs = [r for r in records if r["question_id"] in qset]
    if anchor == "crashes_out":
        recs = [r for r in recs if not is_crash(r)]
    by_depth = defaultdict(list)
    for r in recs:
        by_depth[r["depth"]].append(float(r["concept_recall"]))
    depths = sorted(by_depth)
    means = [float(np.mean(by_depth[d])) for d in depths]
    out = {"n_records": len(recs), "n_questions": len({r["question_id"] for r in recs}),
           "depths": depths, "per_depth_n": {d: len(by_depth[d]) for d in depths},
           "per_depth_mean": {d: round(float(np.mean(by_depth[d])), 4) for d in depths},
           "fits": {}}
    for kind in ("logistic", "satexp"):
        popt, rr = fit(depths, means, kind)
        out["fits"][kind] = {"params_means": [round(v, 4) for v in popt],
                             "r2_means": round(rr, 4),
                             "share_at_depth_7": round(share_at_7(kind, popt), 4)}
    return out


def main() -> int:
    ts = utcnow()
    raw = json.load(open(PRIMARY))["results"]
    records = [r for r in raw
               if r.get("depth") is not None and r.get("question_id") is not None
               and r.get("concept_recall") is not None]

    per_q = defaultdict(set)
    for r in records:
        per_q[r["question_id"]].add(int(r["depth"]))
    all_depths = {int(r["depth"]) for r in records}
    every = {q for q, ds in per_q.items() if ds == all_depths}
    sets = {"all": set(per_q), "balanced": every}

    grid = {}
    for qname, qset in sets.items():
        for anchor in ("crashes_in", "crashes_out"):
            grid[f"{qname}/{anchor}"] = cell(records, qset, anchor)

    bad = []
    for (qname, anchor, kind), want in GATE.items():
        got = grid[f"{qname}/{anchor}"]["fits"][kind]["share_at_depth_7"]
        if abs(got - want) > TOL:
            bad.append(f"{qname}/{anchor}/{kind}: got {got}, S10/S45 say {want}")
    if bad:
        print("FATAL: does not reproduce the published fits.")
        for b in bad:
            print("  " + b)
        return 1

    payload = {"_provenance": {"script": "scripts/S184_depth_share_2x2.py", "generated": ts,
                               "input": shown(PRIMARY),
                               "gate": "S10 both all-question anchors, S45 balanced crashes-in",
                               "convention": "balanced set fixed on the full records, crashes "
                                             "dropped afterwards"},
               "n_questions_total": len(per_q), "n_questions_balanced": len(every),
               "crash_records": sum(1 for r in records if is_crash(r)),
               "grid": grid}
    (OUT / "S184_depth_share_2x2.json").write_text(json.dumps(payload, indent=2))

    L = ["# S184 - share of the fitted improvement reached by seven turns, on all four bases", "",
         f"Generated: {ts}", "",
         f"{len(per_q)} questions in the sweep, {len(every)} answered at all {len(all_depths)} "
         f"depths. {payload['crash_records']} records are 'Maximum turns' crashes.", "",
         "| question set | crash anchor | records | logistic | saturating exponential | range |",
         "|---|---|---|---|---|---|"]
    for key in ("all/crashes_in", "all/crashes_out", "balanced/crashes_in",
                "balanced/crashes_out"):
        c = grid[key]
        lo = c["fits"]["logistic"]["share_at_depth_7"]
        se = c["fits"]["satexp"]["share_at_depth_7"]
        q, a = key.split("/")
        L.append(f"| {q} | {a.replace('_', ' ')} | {c['n_records']} | {lo:.1%} | {se:.1%} | "
                 f"{min(lo, se):.0%} to {max(lo, se):.0%} |")
    bc = grid["balanced/crashes_out"]["fits"]
    L += ["",
          "The revision makes the balanced set primary for this quantity (letter, Reviewer 3 "
          "Minor Point) and reports the figure with crashes excluded. That cell is the last row: "
          f"{min(bc['logistic']['share_at_depth_7'], bc['satexp']['share_at_depth_7']):.0%} to "
          f"{max(bc['logistic']['share_at_depth_7'], bc['satexp']['share_at_depth_7']):.0%}.",
          "",
          "Abstract, Results sentence and the Fig. 3a legend must all quote one row of this table."]
    (OUT / "S184_depth_share_2x2.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
