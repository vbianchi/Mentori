#!/usr/bin/env python3
"""coverage_check.py - checks that the data each proposed Figure 6 gap panel needs exists, and prints the numbers.

Scratch work, outside the repository. Reads attempts.csv (prep.py) and, for the failure split, the same records
through S447.load_mirror / keep_design / fail_kind as prep.py does. Reproduces 2,420 attempts and 1,692 passes (after S4; 1,660 before) first.
Writes coverage_check.json next to this script. One draw, descriptive, no test.

    cd /Users/valeriobianchi/projects/Mentori-reanalysis && PYTHONDONTWRITEBYTECODE=1 uv run --frozen python <this file>
"""
import csv
import json
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))

rows = list(csv.DictReader(open(HERE / "attempts.csv")))
for r in rows:
    r["passed"] = int(r["passed"])
if (len(rows), sum(r["passed"] for r in rows)) != (2420, 1692):
    sys.exit("NOT REPRODUCED: attempts.csv is not 2,420 / 1,692")
S = json.load(open(HERE / "summary.json"))
VARS = S["variants_in_order"]
OPS = sorted({r["op_id"] for r in rows})
out = {"reproduced": {"attempts": 2420, "passes": 1692}}

# ---- field coverage ------------------------------------------------------------------------------------------------
cov = {}
for c in ["latency_s", "n_calls", "generator_calls", "llm_calls_d115", "prompt_tokens", "output_tokens",
          "thinking_tokens"]:
    by_v = Counter(r["variant_id"] for r in rows if r[c] != "")
    cov[c] = {"rows": sum(by_v.values()), "by_variant": {v: by_v.get(v, 0) for v in VARS}}
nonzero_think = Counter(r["variant_id"] for r in rows if r["thinking_tokens"] not in ("", "0", "0.0"))
cov["thinking_tokens_nonzero_by_variant"] = {v: nonzero_think.get(v, 0) for v in VARS}
out["coverage"] = cov
print("coverage:", {c: cov[c]["rows"] for c in cov if isinstance(cov[c], dict) and "rows" in cov[c]})
print("thinking_tokens rows by variant:", cov["thinking_tokens"]["by_variant"])
print("thinking_tokens nonzero by variant:", cov["thinking_tokens_nonzero_by_variant"])

idx = {(r["variant_id"], r["strategy"], r["op_id"]): r for r in rows}
f = lambda x: float(x) if x not in ("", None) else None


def boot(diffs_by_op, n=10000, seed=20261013):
    """95% percentile interval of the mean over operations, resampling the 20 operations."""
    rng = random.Random(seed)
    ops = list(diffs_by_op)
    ms = []
    for _ in range(n):
        s = [diffs_by_op[rng.choice(ops)] for _ in ops]
        ms.append(sum(s) / len(s))
    ms.sort()
    return round(ms[int(0.025 * n)], 1), round(ms[int(0.975 * n) - 1], 1)


# ---- gap 1: best of 3 and combined against single free-form, paired --------------------------------------------
pairs = {}
for base, arms in (("free_form", ["free_form_n3_best", "free_form_n3_combined"]),
                   ("coder_v2_n1", ["coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined", "coder_v2_n3"])):
    for arm in arms:
        rescued = lost = both = neither = 0
        per_op = defaultdict(list)
        ratio = {"latency_s": [], "generator_calls": [], "output_tokens": []}
        sums = {k: [0.0, 0.0] for k in ratio}
        per_var = {}
        for v in VARS:
            rv = lv = 0
            for o in OPS:
                a, b = idx[(v, base, o)], idx[(v, arm, o)]
                rescued += (not a["passed"]) and b["passed"]
                lost += a["passed"] and not b["passed"]
                both += a["passed"] and b["passed"]
                neither += (not a["passed"]) and not b["passed"]
                rv += (not a["passed"]) and b["passed"]
                lv += a["passed"] and not b["passed"]
                per_op[o].append(b["passed"] - a["passed"])
                for k in ratio:
                    x, y = f(a[k]), f(b[k])
                    if x is not None and y is not None:
                        sums[k][0] += x
                        sums[k][1] += y
                        if x > 0:
                            ratio[k].append(y / x)
            per_var[v] = {"rescued": rv, "lost": lv}
        d_op = {o: 100 * sum(x) / len(x) for o, x in per_op.items()}
        net = 100 * (rescued - lost) / (len(VARS) * len(OPS))
        pairs[f"{arm} vs {base}"] = {
            "n_pairs": len(VARS) * len(OPS), "rescued": rescued, "lost": lost, "both_pass": both,
            "both_fail": neither, "net_points": round(net, 1), "interval_95_ops": boot(d_op),
            "cost_multiple_of_sums": {k: round(sums[k][1] / sums[k][0], 2) for k in sums if sums[k][0]},
            "cost_multiple_median_paired": {k: round(st.median(ratio[k]), 2) for k in ratio if ratio[k]},
            "per_variant": per_var}
out["gap_best_of_3"] = pairs
for k, p in pairs.items():
    print(f"{k}: rescued {p['rescued']}, lost {p['lost']}, net {p['net_points']:+.1f} {p['interval_95_ops']}, "
          f"cost x (sums) {p['cost_multiple_of_sums']}")

# ---- gap 2: pass against cost, per strategy and per thinking setting ---------------------------------------------
def med(xs):
    xs = [f(x) for x in xs if f(x) is not None]
    return round(st.median(xs), 1) if xs else None


cost_strat = {}
for s in S["strategies_in_order"]:
    rr = [r for r in rows if r["strategy"] == s]
    cost_strat[s] = {"pass": [sum(r["passed"] for r in rr), len(rr)],
                     "median_latency_s": med([r["latency_s"] for r in rr]),
                     "median_generator_calls": med([r["generator_calls"] for r in rr]),
                     "median_output_tokens": med([r["output_tokens"] for r in rr])}
cost_set = {}
for v in VARS:
    rr = [r for r in rows if r["variant_id"] == v]
    cost_set[v] = {"pass": [sum(r["passed"] for r in rr), len(rr)],
                   "median_latency_s": med([r["latency_s"] for r in rr]),
                   "median_output_tokens": med([r["output_tokens"] for r in rr]),
                   "median_thinking_tokens": med([r["thinking_tokens"] for r in rr]),
                   "thinking_rows": sum(1 for r in rr if r["thinking_tokens"] != "")}
out["cost_by_strategy"], out["cost_by_variant"] = cost_strat, cost_set
print("cost by strategy:")
for s, c in cost_strat.items():
    print(f"  {s:28s} {c}")
print("cost by variant:")
for v, c in cost_set.items():
    print(f"  {v:34s} {c}")

# ---- gap 3a: per dataset ------------------------------------------------------------------------------------------
ds = defaultdict(lambda: [0, 0])
for r in rows:
    for key in [(r["dataset"], r["family"]), (r["dataset"], "all")]:
        ds[key][0] += r["passed"]
        ds[key][1] += 1
out["by_dataset_family"] = {f"{a} | {b}": v for (a, b), v in sorted(ds.items())}
gapd = {}
for d in ("RNA-seq", "survival"):
    for v in VARS:
        p = lambda fam: [sum(r["passed"] for r in rows if r["variant_id"] == v and r["dataset"] == d
                             and r["family"] == fam),
                         sum(1 for r in rows if r["variant_id"] == v and r["dataset"] == d and r["family"] == fam)]
        s_, f_ = p("structured"), p("free-form")
        gapd.setdefault(d, {})[v] = round(100 * s_[0] / s_[1] - 100 * f_[0] / f_[1], 1)
out["structured_minus_free_form_by_dataset_variant"] = gapd
pool_gap = {d: round(100 * ds[(d, "structured")][0] / ds[(d, "structured")][1]
                     - 100 * ds[(d, "free-form")][0] / ds[(d, "free-form")][1], 1) for d in ("RNA-seq", "survival")}
out["structured_minus_free_form_by_dataset_pooled"] = pool_gap
tdf = defaultdict(lambda: [0, 0])
for r in rows:
    tdf[(r["dataset"], r["tier"], r["family"])][0] += r["passed"]
    tdf[(r["dataset"], r["tier"], r["family"])][1] += 1
out["by_dataset_tier_family"] = {" | ".join(k): v for k, v in sorted(tdf.items())}
ops_dt = Counter((r["dataset"], r["tier"]) for r in rows if r["variant_id"] == VARS[0] and r["strategy"] == "free_form")
out["operations_by_dataset_tier"] = {" | ".join(k): n for k, n in sorted(ops_dt.items())}
print("pooled gap by dataset:", pool_gap)
print("operations by dataset and tier:", out["operations_by_dataset_tier"])
print("by dataset, tier and family:", out["by_dataset_tier_family"])
print("by dataset and family:", out["by_dataset_family"])
print("gap by dataset:", gapd)

# ---- gap 3b: failure split, from the records -----------------------------------------------------------------------
import S478_fig6_thinking_gap as S478  # noqa: E402
S447 = S478.S447
atts, flags, inputs, notes = S447.load_mirror()
kept, vs, total, left = S447.keep_design(atts)
if (len(kept), sum(bool(a["passed"]) for a in kept)) != (2420, 1692):
    sys.exit("NOT REPRODUCED: records are not 2,420 / 1,692")
fam = S["family_of_strategy"]
split = defaultdict(Counter)
eo_of_wrong = Counter()
for a in kept:
    if a["passed"]:
        continue
    k = S447.fail_kind(a, flags.get(a.get("ctx_uid"), set()))
    s = S447.config_of(a["run_id"])
    eo = a.get("exec_outcome")
    ar = a.get("actual_results")
    if k == "result wrong or missing":
        eo_of_wrong[(eo, bool(ar))] += 1
        k2 = "ran, values returned but wrong" if ar else "ran, no result returned"
    elif k == "code raised or timed out":
        k2 = "code raised or timed out (no result)"
    else:
        k2 = "machinery or other: " + k
    split[s][k2] += 1
    split[fam[s]][k2] += 1
out["failure_split"] = {s: dict(c.most_common()) for s, c in split.items()}
out["result_wrong_or_missing_by_exec_outcome_and_has_results"] = {f"{eo} | has_results={h}": n
                                                                  for (eo, h), n in eo_of_wrong.items()}
print("'result wrong or missing' by exec_outcome and whether actual_results is non-empty:",
      out["result_wrong_or_missing_by_exec_outcome_and_has_results"])
for s in list(S["strategies_in_order"]) + ["free-form", "introspection", "structured"]:
    print(f"  {s:28s} {dict(split[s].most_common())}")

(HERE / "coverage_check.json").write_text(json.dumps(out, indent=1) + "\n")
print("wrote", HERE / "coverage_check.json")
