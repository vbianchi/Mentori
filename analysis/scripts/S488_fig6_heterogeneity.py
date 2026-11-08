#!/usr/bin/env python3
"""S488 - D155 A12 (findings/audits/scratch_repro_2026-10-26/INVENTORY.md F11): whether a prompting family's effect
on Figure 6's pass rate depends on the model, one stated test on the committed Figure 6 cells.

WHY. The audit of 25 October gave four heterogeneity numbers from two scratch scripts and two methods: introspection
against free-form Q 6.3 (P 0.79) and Q 6.0 (P 0.82), structured against free-form Q 136.5 (P 2e-24) and Q 55.9
(P 2.2e-08). Q 6.3 and Q 136.5 came from SCR/audit_1025/synthesis/het.py (risk differences, an ad hoc variance, on
figure6_numbers.json); Q 6.0 and Q 55.9 from SCR/audit_1025/story_skeptic/fig6_check.py (log odds ratios, on the 24 Oct
fig6_cells.csv). D155: no number without a committed script. This is that script, with one method.

THE METHOD (one, for every contrast). Cochran's Q on log odds ratios (Woolf's inverse-variance test):
  - per variant v, the 2x2 table of passes and failures, family B (structured or introspection) against family A
    (free-form), pooled over the family's strategies and the 20 operations (B: 4 strategies, 80 attempts; A: 3
    strategies, 60 attempts);
  - 0.5 added to all four cells of every variant's table (Haldane-Anscombe), so a cell at 0% or 100% (gemma3:27b
    passes 0 of 80 structured attempts) keeps a finite log odds ratio and variance;
  - log OR_v = ln((a d) / (b c)), var_v = 1/a + 1/b + 1/c + 1/d, w_v = 1 / var_v;
  - pooled log OR = sum(w_v log OR_v) / sum(w_v) (fixed effect); Q = sum(w_v (log OR_v - pooled)^2), referred to
    chi-square with k - 1 degrees of freedom (k variants); I^2 = max(0, (Q - df) / Q).
  Woolf's variance treats each variant's 80 and 60 attempts as independent, though they are 20 operations repeated
  over the strategies, the same operations in both families; with each variant's variance from a bootstrap over the
  20 operations instead (paired across families, 4,000 resamples; computed by the audit's verifier, scratch code, as
  findings/audits/audit_2026-10-27_scripts/fig4_6_verified.md F4 records it, not by this script), no conclusion
  changes: introspection Q 5.98, P 0.817 becomes 5.90, P 0.824; structured 55.86, P 2.2e-08 becomes 146.6, P 1.8e-26
  (gemma3:27b's 0 of 80 gives a near-zero bootstrap variance); structured without gemma3:27b 45.31, P 8.1e-07
  becomes 42.72, P 2.4e-06.
  Why not risk differences (het.py): the variance of a difference of two proportions is near zero when both sit at 0%
  or 100%, so such a variant gets a near-infinite weight and dominates Q. het.py patched that with + 0.5 / n inside the
  variance, a choice no reference states. Why not the committed interaction_chi2 (S447, fig6_numbers.json): a Pearson
  chi-square on the 11 x 11 table of pass counts alone (chi2 88.38, df 100, P 0.79), which asks whether the variants'
  passes spread alike over all 11 strategies, not whether one family's effect depends on the model; its P 0.79 matching
  the introspection P is a coincidence.

STATED CONTRASTS. (1) introspection against free-form, 11 variants; (2) structured against free-form, 11 variants;
(3) structured against free-form without gemma3:27b, 10 variants (its 80 structured failures are 78 'tools refused by
Ollama' and 2 'no code', S478_fig6_thinking_gap.json, so this asks whether the dependence on the model is that one
variant). Each is one Q on one fixed set of variants. Exploratory: no threshold is set and no correction applied.

THE RECORDS (D253, 5 November). The test is run on the S2 records after S4's reruns (s2_after_s4_20261105.tar,
commits a5ae6757 and d3acc869: 1,692 of 2,420 passes, structured 515 of 880). The inventory's values were computed on
the records of 21 October (s2_length_retries_20261021.tar, 1,660 of 2,420, fig6_cells.csv of 24 October); they are
kept as a reproduce step on those records, so a change to the method still fails the run.

WHAT IS READ (committed files and the frozen tar of 21 October; no run record, no model call):
  findings/figures_provisional/fig6/figure6_numbers.json   the current plate's numbers (S481, after S4): sheet
                                                           "Fig. 6a", its 121 "strategy" rows and 33 "family pooled"
                                                           rows (the cells tested)
  findings/figures_provisional/fig6/fig6_cells.csv         S447's cells after S4: the same 121 (variant, strategy)
                                                           cells, a second source
  findings/figures_provisional/fig6/fig6_numbers.json      S447's pooled_structured_vs_free_form (the anchor)
  findings/recompute/S479_fig6_by_tier.json                S479's by_group passes (a second anchor)
  fig6_cells.csv at commit S525.OLD_AT (94262a0e)          S447's cells of 24 Oct, the records of 21 Oct (git show)
  frozen s2_length_retries_20261021.tar                    read through S525.load_copy when it is in the tar folder
  findings/recompute/S580_codegen_passages/S580_codegen_passages.json   S580's Q, P and I2 (D253's check)

REPRODUCE FIRST (README.md:75-79). Before anything is written, exit 2 unless:
  (1) the records of 21 October: the frozen tar before S4 gives 1,660 of 2,420 (S525.OLD_WANT) and its 121 cells equal
      fig6_cells.csv of 24 Oct cell by cell (when the tar is not in the tar folder, the csv alone is read and the
      record says so); on those cells every contrast whose inventory value was computed with this script's method
      (log odds ratios, 0.5 added to every cell) equals it at the inventory's precision (Q to 0.1, P to two
      significant figures): introspection Q 6.0 P 0.82, structured Q 55.9 P 2.2e-08. The inventory's risk-difference
      values use another method and are meant to differ, so they are reported beside the new value and not gated;
  (2) the records after S4: the 33 family pooled rows sum to 1,692 of 2,420 (WANT_AFTER_S4), free-form 510 of 660,
      introspection 667 of 880, structured 515 of 880, equal to fig6_numbers.json pooled_structured_vs_free_form and
      to S479 by_group "all"; each family pooled row equals the sum of its variant's strategy rows; and every one of
      the 121 strategy cells equals fig6_cells.csv's cell (passes and attempts).
  After the contrasts on the records after S4, D253's check: each contrast's printed Q, df, P and I2 equals S580's
  committed heterogeneity_S488_method, or exit 2.

REFUSES TO WRITE (D160 (6), Q18; audit findings/audits/audit_2026-10-27_scripts/fig4_6_verified.md F3). Exit 2 and
nothing written when: the selftest below fails (it runs first, quietly); a reproduce gate above fails; or S580's
values differ from this script's.

COMMANDS (repository root):
  uv run python scripts/S488_fig6_heterogeneity.py            selftest, reproduce, then write
                                                              findings/recompute/S488_fig6_heterogeneity/
                                                              S488_fig6_heterogeneity.json (no write time in it)
  uv run python scripts/S488_fig6_heterogeneity.py selftest   the method on synthetic tables, the reproduce gate
                                                              refusing a cell changed in memory, the inventory gate
                                                              (on the cells of 24 Oct) refusing a same-method Q or P
                                                              moved, and the S580 gate refusing a Q, P or I2 moved
                                                              (nothing written)
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

from scipy.stats import chi2

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/S488_fig6_heterogeneity.py"
FIG6 = ROOT / "findings/figures_provisional/fig6"
NUMBERS = FIG6 / "figure7_numbers.json"
CELLS = FIG6 / "fig6_cells.csv"
S447_NUMBERS = FIG6 / "fig6_numbers.json"
J479 = ROOT / "findings/recompute/S479_fig6_by_tier.json"
J580 = ROOT / "findings/recompute/S580_codegen_passages/S580_codegen_passages.json"
CELLS_REL = "findings/figures_provisional/fig6/fig6_cells.csv"
OUT = ROOT / "findings/recompute/S488_fig6_heterogeneity/S488_fig6_heterogeneity.json"
WANT_AFTER_S4 = {"all": [1692, 2420], "free-form": [510, 660], "introspection": [667, 880],
                 "structured": [515, 880]}   # D253: S478.WANT after S4 and the families S580 holds
sys.path.insert(0, str(ROOT / "scripts"))

FAMS = ["free-form", "introspection", "structured"]
# The plate's variant labels (S481.vlabel: Gemini's lowest setting "low", a model with one setting unlabelled) and
# S447's variant ids, both ways checked below.
LABEL_OF_ID = {
    "qwen3-coder-30b+default": "qwen3-coder:30b",
    "qwen3-coder-next-q4_K_M+default": "qwen3-coder-next",
    "gpt-oss-20b+low": "gpt-oss:20b (low)",
    "gpt-oss-20b+medium": "gpt-oss:20b (medium)",
    "gpt-oss-20b+high": "gpt-oss:20b (high)",
    "gemma3-27b+default": "gemma3:27b",
    "devstral-small-2-24b+default": "devstral-small-2:24b",
    "gemini-2.5-pro+default": "gemini-2.5-pro (default)",
    "gemini-2.5-pro+off": "gemini-2.5-pro (low)",
    "gemini-3-flash-preview+default": "gemini-3-flash (default)",
    "gemini-3-flash-preview+off": "gemini-3-flash (low)",
}
CONTRASTS = [
    ("introspection vs free-form", "introspection", "free-form", ()),
    ("structured vs free-form", "structured", "free-form", ()),
    ("structured vs free-form, without gemma3:27b", "structured", "free-form", ("gemma3:27b",)),
]
INVENTORY_F11 = {   # INVENTORY.md:76, from AUDIT_2026-10-25.md:234-235,567,599
    "introspection vs free-form": [
        {"Q": 6.3, "df": 10, "P": 0.79, "method": "risk differences, variance (p(1-p) + 0.5/n)/n",
         "script": "SCR/audit_1025/synthesis/het.py", "data": "figure7_numbers.json family pooled rows"},
        {"Q": 6.0, "df": 10, "P": 0.82, "method": "log odds ratios, 0.5 added to every cell",
         "script": "SCR/audit_1025/story_skeptic/fig6_check.py", "data": "fig6_cells.csv (24 Oct)"}],
    "structured vs free-form": [
        {"Q": 136.5, "df": 10, "P": 2e-24, "method": "risk differences, variance (p(1-p) + 0.5/n)/n",
         "script": "SCR/audit_1025/synthesis/het.py", "data": "figure7_numbers.json family pooled rows"},
        {"Q": 55.9, "df": 10, "P": 2.2e-08, "method": "log odds ratios, 0.5 added to every cell",
         "script": "SCR/audit_1025/story_skeptic/fig6_check.py", "data": "fig6_cells.csv (24 Oct)"}],
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stop(msg: str):
    print(f"NOT REPRODUCED: {msg}; nothing written", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------------------------------------- method
def log_or(b_pass: int, b_n: int, a_pass: int, a_n: int):
    """Log odds ratio of family B against family A and its variance, 0.5 added to every cell."""
    a, b = b_pass + 0.5, b_n - b_pass + 0.5
    c, d = a_pass + 0.5, a_n - a_pass + 0.5
    return math.log((a * d) / (b * c)), 1 / a + 1 / b + 1 / c + 1 / d


def cochran_q(tables):
    """tables: [(b_pass, b_n, a_pass, a_n)] one per variant. Woolf's inverse-variance Cochran Q on log odds ratios."""
    lv = [log_or(*t) for t in tables]
    w = [1 / v for _, v in lv]
    pooled = sum(wi * l for wi, (l, _) in zip(w, lv)) / sum(w)
    q = sum(wi * (l - pooled) ** 2 for wi, (l, _) in zip(w, lv))
    df = len(tables) - 1
    return {"Q": q, "df": df, "P": float(chi2.sf(q, df)), "I2": max(0.0, (q - df) / q) if q > 0 else 0.0,
            "pooled_log_odds_ratio": pooled, "pooled_odds_ratio": math.exp(pooled),
            "pooled_se": math.sqrt(1 / sum(w))}


# ---------------------------------------------------------------------------------------------------------- data
def read_sheet():
    d = json.loads(NUMBERS.read_text())
    s = d["sheets"]["Fig. 7a"]
    rows = [dict(zip(s["columns"], r)) for r in s["rows"]]
    return d["stamp"], [r for r in rows if r["part"] == "strategy"], [r for r in rows if r["part"] == "family pooled"]


def read_cells_csv(text: str | None = None):
    lines = [ln for ln in (CELLS.read_text() if text is None else text).splitlines() if not ln.startswith("#")]
    return list(csv.DictReader(lines))


def load_s525():
    import S525_fig6_s4_check as S525
    return S525


def old_cells():
    """fig6_cells.csv of 24 Oct (the records of 21 Oct) from git at S525.OLD_AT, and its sha256."""
    S525 = load_s525()
    b = S525.git_show(S525.OLD_AT, CELLS_REL)
    return read_cells_csv(b.decode()), hashlib.sha256(b).hexdigest(), S525.OLD_AT


def pool_families(csv_rows, strat_rows):
    """Family pooled rows (the sheet's format) from fig6_cells.csv rows; a strategy's family from the plate's sheet."""
    fam_of = {r["strategy"]: r["family"] for r in strat_rows}
    pool = {}
    for r in csv_rows:
        if r["variant"] not in LABEL_OF_ID:
            continue
        k = (LABEL_OF_ID[r["variant"]], fam_of[r["label"]])
        t = pool.setdefault(k, [0, 0])
        t[0] += int(r["pass"])
        t[1] += int(r["attempts"])
    return [{"variant": v, "family": f, "passes": p, "attempts": n} for (v, f), (p, n) in pool.items()]


def old_tar_check(csv_rows):
    """REPRODUCE (1), the tar part: the copy before S4 gives S525.OLD_WANT and its 121 cells equal fig6_cells.csv of
    24 Oct. When the tar is not in the tar folder, the record says the tar was not read (as S481.s4_gate)."""
    import fig_repro
    S525 = load_s525()
    try:
        fig_repro.frozen(S525.OLD_SET, S525.OLD_SET)
    except fig_repro.FrozenInputError as e:
        print(f"records of 21 Oct: the tar {S525.OLD_SET} is not readable ({e}); fig6_cells.csv of 24 Oct read alone")
        return {"tar": S525.OLD_SET, "tar_read": False, "why": str(e)}
    S447 = S525.load_S447()
    rows, prov = S525.load_copy(S447, S525.OLD_SET, S525.git_show(S525.OLD_AT, S525.MANIFEST_REL),
                                S525.git_show(S525.OLD_AT, S525.Q4_REL))
    got = (len(rows), sum(r["passed"] for r in rows.values()))
    if got != tuple(S525.OLD_WANT):
        stop(f"the tar {S525.OLD_SET} gives {got}, not S525.OLD_WANT {S525.OLD_WANT}")
    tar = {}
    for (rid, _), r in rows.items():
        _, strategy, variant = rid.split("__", 2)
        t = tar.setdefault((variant, strategy), [0, 0])
        t[0] += r["passed"]
        t[1] += 1
    by_csv = {(r["variant"], r["strategy"]): [int(r["pass"]), int(r["attempts"])] for r in csv_rows
              if r["variant"] in LABEL_OF_ID}
    if tar != by_csv:
        diff = sorted(k for k in set(tar) | set(by_csv) if tar.get(k) != by_csv.get(k))
        stop(f"{len(diff)} cells differ between the tar {S525.OLD_SET} and fig6_cells.csv of 24 Oct, e.g. {diff[:3]}")
    return {"tar": S525.OLD_SET, "tar_read": True, "tar_sha256": prov["tar_sha256"], "totals": list(got),
            "cells_equal_to_fig6_cells_csv_24_oct": len(tar)}


def reproduce_21_october(strat_rows, tar=True):
    """REPRODUCE (1): the inventory's same-method values on the records of 21 October. Exit 2 on a miss."""
    rows, csv_sha, at = old_cells()
    tar_rec = old_tar_check(rows) if tar else {"tar_read": False, "why": "selftest: the csv alone"}
    res = contrasts(pool_families(rows, strat_rows))
    cmp_ = compare(res)
    n_gated = gate_inventory(cmp_)
    return {"records": "s2_length_retries_20261021 (1,660 of 2,420)", "fig6_cells_csv": f"{at}:{CELLS_REL}",
            "fig6_cells_csv_sha256": csv_sha, "tar_check": tar_rec, "contrasts": res,
            "against_inventory_F11": cmp_, "same_method_rows_equal": n_gated}


def gate_s580(results, j580=None):
    """D253: each contrast's printed Q, df, P and I2 equals S580's committed heterogeneity_S488_method; exit 2 if not."""
    want = (json.loads(J580.read_text()) if j580 is None else j580)["P2"]["heterogeneity_S488_method"]
    keys = ("Q", "df", "P", "I2_pct")
    got = {r["contrast"]: {k: r["printed"][k] for k in keys} for r in results}
    if set(got) != set(want) or any(got[c] != {k: want[c][k] for k in keys} for c in got):
        stop(f"S488 {got} is not S580's committed {want}")
    return [{"contrast": c, "S488": got[c], "S580": {k: want[c][k] for k in keys}, "equal": True} for c in got]


def reproduce(strat_rows, fam_rows, csv_rows):
    """The anchors; exit 2 on any difference. Returns what was compared."""
    ids = set(LABEL_OF_ID)
    labels = set(LABEL_OF_ID.values())
    if {r["variant"] for r in strat_rows} != labels or {r["variant"] for r in fam_rows} != labels:
        stop("the sheet's variant labels are not the 11 of LABEL_OF_ID")
    if len(fam_rows) != 33 or len(strat_rows) != 121:
        stop(f"{len(fam_rows)} family pooled and {len(strat_rows)} strategy rows, not 33 and 121")
    # (1) family pooled totals against S447 and S479
    tot = {f: [0, 0] for f in FAMS}
    for r in fam_rows:
        tot[r["family"]][0] += r["passes"]
        tot[r["family"]][1] += r["attempts"]
    allp = [sum(t[0] for t in tot.values()), sum(t[1] for t in tot.values())]
    if {"all": allp, **tot} != WANT_AFTER_S4:
        stop(f"the plate's family totals {({'all': allp, **tot})} are not the records after S4 {WANT_AFTER_S4}")
    p447 =json.loads(S447_NUMBERS.read_text())["pooled_structured_vs_free_form"]
    want447 = {"free-form": p447["free_form_family"], "introspection": p447["introspection_family"],
               "structured": p447["structured_family"]}
    for f in FAMS:
        if tot[f] != [want447[f]["pass"], want447[f]["attempts"]]:
            stop(f"{f} pooled {tot[f]} is not fig6_numbers.json's {want447[f]}")
    if allp != [p447["all"]["pass"], p447["all"]["attempts"]]:
        stop(f"all {allp} is not fig6_numbers.json's {p447['all']}")
    j479 = json.loads(J479.read_text())["by_group"]
    for g, got in [("all", allp)] + [(f, tot[f]) for f in FAMS]:
        if j479[g]["all"]["passes"] != got:
            stop(f"{g} {got} is not S479 by_group's {j479[g]['all']['passes']}")
    # (2) each family pooled row is the sum of its strategy rows
    for r in fam_rows:
        ss = [x for x in strat_rows if x["variant"] == r["variant"] and x["family"] == r["family"]]
        if [sum(x["passes"] for x in ss), sum(x["attempts"] for x in ss)] != [r["passes"], r["attempts"]]:
            stop(f"{r['variant']} {r['family']}: pooled row is not the sum of its strategy rows")
    # (3) the 121 cells against fig6_cells.csv (S447, 24 Oct)
    by_csv = {}
    for r in csv_rows:
        if r["variant"] in ids:
            by_csv[(LABEL_OF_ID[r["variant"]], r["label"])] = [int(r["pass"]), int(r["attempts"])]
    by_sheet = {(r["variant"], r["strategy"]): [r["passes"], r["attempts"]] for r in strat_rows}
    if by_csv != by_sheet:
        diff = sorted(k for k in set(by_csv) | set(by_sheet) if by_csv.get(k) != by_sheet.get(k))
        stop(f"{len(diff)} cells differ between figure7_numbers.json and fig6_cells.csv, e.g. {diff[:3]}")
    known = {"all": allp, **tot}
    print("reproduced: " + ", ".join(f"{k} {v[0]:,} of {v[1]:,}" for k, v in known.items())
          + " (fig6_numbers.json and S479 equal); 121 cells equal to fig6_cells.csv")
    return {"passes_of_attempts": known, "equal_to": ["fig6_numbers.json pooled_structured_vs_free_form",
                                                       "S479_fig6_by_tier.json by_group all"],
            "cells_equal_to_fig6_cells_csv": len(by_sheet), "family_rows_equal_sum_of_strategy_rows": len(fam_rows)}


def contrasts(fam_rows):
    pool = {(r["variant"], r["family"]): (r["passes"], r["attempts"]) for r in fam_rows}
    order = [LABEL_OF_ID[v] for v in LABEL_OF_ID]
    out = []
    for name, fb, fa, without in CONTRASTS:
        vs = [v for v in order if v not in without]
        tables = [(*pool[(v, fb)], *pool[(v, fa)]) for v in vs]
        res = cochran_q(tables)
        per = []
        for v, t in zip(vs, tables):
            lo, var = log_or(*t)
            per.append({"variant": v, f"{fb}_passes": t[0], f"{fb}_attempts": t[1], f"{fa}_passes": t[2],
                        f"{fa}_attempts": t[3], "log_odds_ratio": lo, "variance": var,
                        "rate_difference_points": 100 * (t[0] / t[1] - t[2] / t[3])})
        out.append({"contrast": name, "family_b": fb, "family_a": fa, "variants": len(vs),
                    "left_out": list(without), **res,
                    "printed": {"Q": round(res["Q"], 1), "df": res["df"], "P": float(f"{res['P']:.2g}"),
                                "I2_pct": round(100 * res["I2"]), "pooled_odds_ratio": round(res["pooled_odds_ratio"], 2)},
                    "per_variant": per})
    return out


def compare(results, inventory=None):
    """Each new Q beside the inventory's values for the same contrast: equal (at the inventory's precision) or not,
    and why. inventory defaults to INVENTORY_F11 (the selftest passes a changed copy)."""
    out = []
    for r in results:
        for old in (INVENTORY_F11 if inventory is None else inventory).get(r["contrast"], []):
            q_eq = round(r["Q"], 1) == old["Q"]
            p_eq = float(f"{r['P']:.2g}") == old["P"]
            same_method = old["method"].startswith("log odds")
            if not same_method:
                why = ("different method: risk differences with het.py's variance (p(1-p) + 0.5/n)/n, which gives "
                       "a variant near 0% or 100% in both families a near-infinite weight")
            elif q_eq and p_eq:
                why = "same method on the same 121 cells (fig6_cells.csv of 24 Oct, the records of 21 Oct)"
            else:
                why = "NOT EXPLAINED: same method and cells, different value"
            out.append({"contrast": r["contrast"], "inventory": old, "S488": r["printed"],
                        "Q_equal": q_eq, "P_equal": p_eq, "why": why})
    return out


def gate_inventory(cmp_):
    """Exit 2 when a same-method inventory row is not reproduced (Q to 0.1, P to two significant figures). The
    risk-difference rows are another method and are not gated."""
    bad = [c for c in cmp_ if c["inventory"]["method"].startswith("log odds") and not (c["Q_equal"] and c["P_equal"])]
    if bad:
        stop("same method, different value: " + "; ".join(
            f"{c['contrast']} Q {c['S488']['Q']} P {c['S488']['P']} against the inventory's Q {c['inventory']['Q']} "
            f"P {c['inventory']['P']}" for c in bad))
    return sum(c["inventory"]["method"].startswith("log odds") for c in cmp_)


# ---------------------------------------------------------------------------------------------------------- test
def selftest() -> bool:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok &= bool(cond)
    # identical tables: Q = 0, P = 1
    r = cochran_q([(10, 20, 15, 20)] * 5)
    check("identical tables give Q 0 and P 1", abs(r["Q"]) < 1e-12 and abs(r["P"] - 1) < 1e-12)
    # hand-computed two-table case: log ORs l1, l2, weights w1, w2
    l1, v1 = math.log((10.5 * 10.5) / (10.5 * 10.5)), 4 / 10.5
    a, b, c, d = 18.5, 2.5, 10.5, 10.5
    l2, v2 = math.log(a * d / (b * c)), 1 / a + 1 / b + 1 / c + 1 / d
    w1, w2 = 1 / v1, 1 / v2
    m = (w1 * l1 + w2 * l2) / (w1 + w2)
    qh = w1 * (l1 - m) ** 2 + w2 * (l2 - m) ** 2
    r = cochran_q([(10, 20, 10, 20), (18, 20, 10, 20)])
    check(f"two tables equal the hand computation (Q {qh:.6f})", abs(r["Q"] - qh) < 1e-12 and r["df"] == 1)
    # a 0-of-n cell stays finite (gemma3's structured 0 of 80)
    lo, var = log_or(0, 80, 38, 60)
    check("0 of 80 gives a finite log odds ratio", math.isfinite(lo) and math.isfinite(var))
    # direction: more passes in B gives a positive log OR
    check("B better than A gives log OR > 0", log_or(15, 20, 5, 20)[0] > 0)
    # mutant: without the 0.5 correction a 0 cell breaks the test
    try:
        math.log((0 * 22) / (80 * 38))
        broken = False
    except ValueError:
        broken = True
    check("without the correction 0 of 80 has no log odds ratio (why 0.5 is added)", broken)
    # the reproduce gate refuses a changed cell (one pass moved in the committed rows, in memory only)
    _, sr, fr = read_sheet()
    cr = read_cells_csv()
    for what, mut in (("a family pooled row", lambda s, f, c: f[0].update(passes=f[0]["passes"] + 1)),
                      ("a strategy cell", lambda s, f, c: s[0].update(passes=s[0]["passes"] - 1)),
                      ("a fig6_cells.csv cell", lambda s, f, c: c[0].update({"pass": str(int(c[0]["pass"]) - 1)}))):
        s2, f2, c2 = [dict(x) for x in sr], [dict(x) for x in fr], [dict(x) for x in cr]
        mut(s2, f2, c2)
        try:
            reproduce(s2, f2, c2)
            refused = False
        except SystemExit as e:
            refused = e.code == 2
        check(f"reproduce() refuses {what} changed by one pass", refused)
    # the inventory gate, on the cells of 24 Oct (the records of 21 Oct, D253): they pass it; a same-method Q or P
    # moved is refused; a risk-difference row that differs is not
    fr_old = pool_families(old_cells()[0], sr)
    check("the cells of 24 Oct pool to 1,660 of 2,420 (structured 483 of 880)",
          [sum(r["passes"] for r in fr_old), sum(r["attempts"] for r in fr_old)] == [1660, 2420]
          and [sum(r["passes"] for r in fr_old if r["family"] == "structured"),
               sum(r["attempts"] for r in fr_old if r["family"] == "structured")] == [483, 880])
    oc = [dict(x) for x in old_cells()[0]]
    oc[0]["pass"] = str(int(oc[0]["pass"]) + 1)
    try:
        rec = old_tar_check(oc)
        refused = None if not rec["tar_read"] else False
    except SystemExit as e:
        refused = e.code == 2
    if refused is None:   # the tar is not in the tar folder: main() records that it was not read
        print("  SKIP  old_tar_check() mutant: the tar of 21 Oct is not readable here")
    else:
        check("old_tar_check() refuses a fig6_cells.csv of 24 Oct cell changed by one pass (against the tar)", refused)
    cmp_ = compare(contrasts(fr_old))
    try:
        n_gated = gate_inventory(cmp_)
        passed = n_gated == 2
    except SystemExit:
        passed = False
    check("gate_inventory() passes the cells of 24 Oct on its 2 same-method rows", passed)
    try:
        gate_inventory(compare(contrasts(fr)))
        refused = False
    except SystemExit as e:
        refused = e.code == 2
    check("gate_inventory() refuses the cells after S4 (structured Q 40.4 is not the inventory's 55.9)", refused)
    # mutants: the inventory's first same-method row moved (Q by 0.1, P by one step at two significant figures), in
    # a copy, then compare() and gate_inventory() run on the committed cells as main() runs them
    for what, field, move in (("a same-method Q moved by 0.1", "Q", lambda q: round(q + 0.1, 1)),
                              ("a same-method P moved", "P", lambda p: float(f"{p * 1.1:.2g}"))):
        inv2 = {k: [dict(o) for o in v] for k, v in INVENTORY_F11.items()}
        row = next(o for v in inv2.values() for o in v if o["method"].startswith("log odds"))
        row[field] = move(row[field])
        try:
            gate_inventory(compare(contrasts(fr_old), inv2))
            refused = False
        except SystemExit as e:
            refused = e.code == 2
        check(f"gate_inventory() refuses {what}", refused)
    c2 = [dict(c) for c in cmp_]
    for c in c2:
        if not c["inventory"]["method"].startswith("log odds"):
            c["Q_equal"] = c["P_equal"] = False
    try:
        gate_inventory(c2)
        passed = True
    except SystemExit:
        passed = False
    check("gate_inventory() does not gate the risk-difference rows (another method)", passed)
    # D253: S580's committed Q, P and I2 equal this script's on the cells after S4; one moved is refused
    res = contrasts(fr)
    try:
        passed = len(gate_s580(res)) == 3
    except SystemExit:
        passed = False
    check("gate_s580() passes: S580's committed Q, df, P and I2 equal S488's on the records after S4", passed)
    for what, field, move in (("Q moved by 0.1", "Q", lambda x: round(x + 0.1, 1)),
                              ("P moved", "P", lambda x: float(f"{x * 1.1:.2g}")),
                              ("I2 moved by 1", "I2_pct", lambda x: x + 1)):
        j2 = json.loads(J580.read_text())
        h = j2["P2"]["heterogeneity_S488_method"]["structured vs free-form"]
        h[field] = move(h[field])
        try:
            gate_s580(res, j2)
            refused = False
        except SystemExit as e:
            refused = e.code == 2
        check(f"gate_s580() refuses S580's structured {what}", refused)
    print(f"selftest {'PASS' if ok else 'FAIL'}")
    return ok


def main(argv):
    if argv[1:] == ["selftest"]:
        sys.exit(0 if selftest() else 1)
    if argv[1:]:
        sys.exit(f"usage: uv run python {SCRIPT} [selftest]")
    quiet = io.StringIO()
    try:
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            st_ok = selftest()
    except SystemExit:   # the selftest itself could not run (an input missing or refused): show why
        st_ok = False
        print(quiet.getvalue().rstrip(), file=sys.stderr)
    if not st_ok:
        print("REFUSED: the selftest fails, nothing written (run `selftest` to see which check)", file=sys.stderr)
        sys.exit(2)
    print("selftest PASS (run first, quietly)")
    stamp, strat_rows, fam_rows = read_sheet()
    # (1) the records of 21 October: the inventory's same-method values
    old = reproduce_21_october(strat_rows)
    for c in old["against_inventory_F11"]:
        o = c["inventory"]
        print(f"  records of 21 Oct, inventory {c['contrast']}: Q {o['Q']} P {o['P']} ({o['method']}): S488 Q "
              f"{c['S488']['Q']} P {c['S488']['P']}, Q equal {c['Q_equal']}, P equal {c['P_equal']}")
    t = old["tar_check"]
    print(f"reproduced records of 21 Oct: {old['same_method_rows_equal']} same-method inventory rows equal"
          + (f"; the tar gives {t['totals'][1]:,} of {t['totals'][0]:,} passes and its "
             f"{t['cells_equal_to_fig6_cells_csv_24_oct']} cells equal fig6_cells.csv of 24 Oct" if t["tar_read"]
             else "; the tar was not read"))
    # (2) the records after S4
    known = reproduce(strat_rows, fam_rows, read_cells_csv())
    res = contrasts(fam_rows)
    for r in res:
        p = r["printed"]
        print(f"{r['contrast']}: Q {p['Q']}, df {p['df']}, P {p['P']}, I2 {p['I2_pct']}%, pooled OR "
              f"{p['pooled_odds_ratio']} ({r['variants']} variants)")
    against_580 = gate_s580(res)
    print(f"S580 gate (D253): {len(against_580)} contrasts, Q, df, P and I2 equal to S580's committed values")
    inputs = [(NUMBERS, "Figure 7 plate numbers (S481, after S4), sheet Fig. 7a: the cells tested"),
              (CELLS, "anchor: S447's cells after S4, compared cell by cell"),
              (S447_NUMBERS, "anchor: S447 pooled_structured_vs_free_form"),
              (J479, "anchor: S479 by_group"),
              ]
    # S580's file records this script's output's sha256, so hashing the whole file would make the two outputs record
    # each other; the part read is hashed instead (canonical JSON of P2.heterogeneity_S488_method)
    h580 = json.dumps(json.loads(J580.read_text())["P2"]["heterogeneity_S488_method"], sort_keys=True,
                      separators=(",", ":"))
    out = {
        "provenance": {
            "script": SCRIPT, "script_sha256": sha(Path(__file__)),
            "command": f"uv run python {SCRIPT}",
            "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "role": role} for p, role in inputs]
            + [{"path": str(J580.relative_to(ROOT)), "part": "P2.heterogeneity_S488_method",
                "sha256_of_part": hashlib.sha256(h580.encode()).hexdigest(),
                "role": "D253 check: S580's Q, df, P and I2 (the part read; canonical JSON, sorted keys)"}],
            "data_stamp": stamp, "model_calls": 0,
            "method": " ".join(__doc__.split("THE METHOD")[1].split("STATED CONTRASTS")[0].split()),
            "ported_from": ["SCR/audit_1025/synthesis/het.py", "SCR/audit_1025/story_skeptic/fig6_check.py"]},
        "reproduced": known,
        "contrasts": res,
        "against_S580": against_580,
        "reproduced_21_october": old,
        "committed_interaction_chi2_is_another_test": json.loads(S447_NUMBERS.read_text())["interaction_chi2"]
        | {"what": "S447's Pearson chi-square on pass counts, variants x strategies; not a test of one family's "
                   "effect across variants"},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv)
