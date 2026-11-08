#!/usr/bin/env python3
"""S580 - every number of the manuscript's code-generation passages (Results 'Code generation performance', the
abstract's and the Discussion's code-generation sentences, the Figure 6 legend's gemma3:27b sentence), on the S2
records after S4's reruns (s2_after_s4_20261105.tar, commits a5ae6757, d3acc869).

WHY. The passages' pooled counts, ranges, failure counts and gpt-oss:20b thinking numbers were summed from the plate
sheets by hand (findings/audits/story_panels_2026-11-03/statements.json: "summed in this check"), and S488's
heterogeneity test refuses to run on the new records (its reproduce gate holds the 1,660-pass records of 21 October and
fig6_cells.csv of 24 October). This script writes each number in one file, from the committed plate numbers S481 and
S447 wrote on the new tar. It computes nothing the plates do not hold except sums, differences and S488's Cochran Q.

WHAT IS READ (committed files only; no run record, no model call):
  findings/figures_provisional/fig6/figure6_numbers.json        S481: sheets Fig. 6a (family pooled, structured minus
                                                                free-form), 6b (box rows)
  findings/figures_provisional/supp_fig15_fig6_pairs/supplementary_figure15_numbers.json   sheet 15f (contrasts; sheet
                                                                6d until D299)
  findings/figures_provisional/fig6/fig6_numbers.json           S447: pooled_structured_vs_free_form, panel_b_cells
                                                                (fail kinds per cell)
  findings/figures_provisional/supp_fig16_fig6_models/supplementary_figure16_numbers.json   sheet 16b
  findings/figures_provisional/supp_fig14_fig6_failures/supplementary_figure14_numbers.json sheet 14
  findings/recompute/S488_fig6_heterogeneity/S488_fig6_heterogeneity.json   S488's committed tables (the known number)
  scripts/S488_fig6_heterogeneity.py                            its cochran_q and LABEL_OF_ID, imported, not changed

REPRODUCE FIRST (README.md:75-79). Exit 2, nothing written, unless:
  (1) S488.cochran_q on S488's committed per-variant tables of 21 October (its reproduced_21_october, D253) gives
      their printed values: structured vs
      free-form Q 55.9 (df 10, P 2.2e-08, I2 82%), introspection vs free-form Q 6.0 (P 0.82, I2 0%);
  (2) the plate holds S478.WANT after S4, 2,420 attempts and 1,692 passes, and the task's known totals: structured
      515 of 880, free-form 510 of 660, introspection 667 of 880 (S447 pooled_structured_vs_free_form equal to the
      sum of sheet 6a's family pooled rows), gpt-oss:20b (high) 133 of 220 (sheet 19b);
  (3) for every variant and family, Supplementary Figure 14's failed attempts sum to attempts minus passes of sheet
      6a's family pooled row, and S447's panel_b_cells (11 design variants) give the same passes per variant and family.

ROUNDING. Rates and differences are exact fractions, printed to one decimal half away from zero; a value exactly on
a half (for example 18.75) is listed under "ties" so the reader sees the choice.

COMMAND (repository root):
  uv run python scripts/S580_codegen_passages.py     writes findings/recompute/S580_codegen_passages/S580_codegen_passages.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/S580_codegen_passages.py"
FIG6 = ROOT / "findings/figures_provisional/fig6/figure7_numbers.json"
SUPP23 = ROOT / "findings/figures_provisional/supp_fig15_fig6_pairs/supplementary_figure15_numbers.json"   # D299: Fig. 7d is Supplementary Fig. 15f
S447 = ROOT / "findings/figures_provisional/fig6/fig6_numbers.json"
SUPP19 = ROOT / "findings/figures_provisional/supp_fig16_fig6_models/supplementary_figure16_numbers.json"
SUPP20 = ROOT / "findings/figures_provisional/supp_fig14_fig6_failures/supplementary_figure14_numbers.json"
S488_JSON = ROOT / "findings/recompute/S488_fig6_heterogeneity/S488_fig6_heterogeneity.json"
S488_PY = ROOT / "scripts/S488_fig6_heterogeneity.py"
OUT = ROOT / "findings/recompute/S580_codegen_passages/S580_codegen_passages.json"

WANT = (2420, 1692)
KNOWN_FAMILY = {"structured": (515, 880), "free-form": (510, 660), "introspection": (667, 880)}
KNOWN_HIGH = (133, 220)
KNOWN_S488 = {"structured vs free-form": {"Q": 55.9, "df": 10, "P": 2.2e-08, "I2_pct": 82},
              "introspection vs free-form": {"Q": 6.0, "df": 10, "P": 0.82, "I2_pct": 0}}
TOOL_KINDS = ["tools refused by Ollama", "tool-call parse error", "tool call written as text", "stall",
              "other call error", "step produced no cell and no error"]
TIES = []


def stop(msg):
    print(f"NOT REPRODUCED: {msg}; nothing written", file=sys.stderr)
    sys.exit(2)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def r1(x: Fraction, what: str):
    """One decimal, half away from zero, from the exact fraction; ties recorded."""
    d = Decimal(x.numerator) / Decimal(x.denominator)
    if (x * 100).denominator == 1 and (x * 100).numerator % 10 == 5:
        TIES.append({"what": what, "exact": str(d)})
    return float(d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def pct(p, n):
    return Fraction(100 * p, n)


def sheet(path, name):
    s = json.loads(path.read_text())["sheets"][name]
    return [dict(zip(s["columns"], r)) for r in s["rows"]]


def load_s488():
    spec = importlib.util.spec_from_file_location("S488", S488_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def q_printed(res):
    return {"Q": round(res["Q"], 1), "df": res["df"], "P": float(f"{res['P']:.2g}"), "I2_pct": round(100 * res["I2"])}


def main():
    S488 = load_s488()
    # (1) S488's known numbers by its own method on its committed tables
    old = json.loads(S488_JSON.read_text())["reproduced_21_october"]["contrasts"]   # D253: S488's tables of 21 Oct
    for c in old:
        if c["contrast"] not in KNOWN_S488:
            continue
        fb, fa = c["family_b"], c["family_a"]
        tables = [(v[f"{fb}_passes"], v[f"{fb}_attempts"], v[f"{fa}_passes"], v[f"{fa}_attempts"])
                  for v in c["per_variant"]]
        got = q_printed(S488.cochran_q(tables))
        if got != KNOWN_S488[c["contrast"]]:
            stop(f"S488's method on its committed tables gives {got} for {c['contrast']}, not {KNOWN_S488[c['contrast']]}")
    print("reproduced S488 (records of 21 Oct): structured Q 55.9 P 2.2e-08 I2 82%; introspection Q 6.0 P 0.82 I2 0%")

    # (2) totals
    a = sheet(FIG6, "Fig. 7a")
    fam = {(r["variant"], r["family"]): r for r in a if r["part"] == "family pooled"}
    gaps = [r for r in a if r["part"] == "structured minus free-form"]
    tot = {f: [0, 0] for f in KNOWN_FAMILY}
    for (v, f), r in fam.items():
        tot[f][0] += r["passes"]
        tot[f][1] += r["attempts"]
    p447 = json.loads(S447.read_text())["pooled_structured_vs_free_form"]
    k447 = {"structured": p447["structured_family"], "free-form": p447["free_form_family"],
            "introspection": p447["introspection_family"]}
    for f, (p, n) in KNOWN_FAMILY.items():
        if tuple(tot[f]) != (p, n) or (k447[f]["pass"], k447[f]["attempts"]) != (p, n):
            stop(f"{f}: sheet 6a {tot[f]}, S447 {k447[f]}, known {(p, n)}")
    allpn = (sum(t[1] for t in tot.values()), sum(t[0] for t in tot.values()))
    if allpn != WANT or (p447["all"]["attempts"], p447["all"]["pass"]) != WANT:
        stop(f"totals {allpn} / S447 {p447['all']} are not WANT {WANT}")
    b19 = sheet(SUPP19, "Supplementary Fig. 16b")
    bars = {(r["variant"], r["outcome"]): r["attempts"] for r in b19 if r["part"] == "bar"}
    meds = {r["variant"]: r for r in b19 if r["part"] == "medians"}
    if (meds["gpt-oss:20b (high)"]["passes"], meds["gpt-oss:20b (high)"]["attempts_n"]) != KNOWN_HIGH:
        stop("gpt-oss:20b (high) is not 133 of 220 in sheet 19b")
    # (3) Supplementary Figure 14 and S447 cells against sheet 6a
    s20 = sheet(SUPP20, "Supplementary Fig. 14")
    fail20 = {}
    for r in s20:
        k = (r["variant"], r["family"])
        fail20.setdefault(k, {})[r["failure_group"]] = r["attempts_failed"]
        if r["attempts"] != fam[k]["attempts"]:
            stop(f"{k}: Supp 12 has {r['attempts']} attempts, sheet 6a {fam[k]['attempts']}")
    for k, g in fail20.items():
        if sum(g.values()) != fam[k]["attempts"] - fam[k]["passes"]:
            stop(f"{k}: Supp 12 failures {sum(g.values())} are not attempts minus passes of sheet 6a")
    label_of = S488.LABEL_OF_ID
    strat_family = {r["strategy"]: r["family"] for r in a if r["part"] == "strategy"}
    cells = [c for c in json.loads(S447.read_text())["panel_b_cells"] if c["variant"] in label_of]
    if len(cells) != 121:
        stop(f"{len(cells)} S447 design cells, not 121")
    p_cells = {}
    for c in cells:
        k = (label_of[c["variant"]], strat_family[c["label"]])
        p_cells[k] = p_cells.get(k, 0) + c["pass"]
    if any(p_cells[k] != fam[k]["passes"] for k in fam):
        stop("S447 panel_b_cells passes differ from sheet 6a's family pooled rows")
    print(f"reproduced after S4: {WANT[0]:,} attempts, {WANT[1]:,} passes; structured 515 of 880, free-form 510 of "
          "660, introspection 667 of 880; gpt-oss:20b (high) 133 of 220; Supp 12 and S447 cells equal to sheet 6a")

    out = {}
    # ---- P1
    rate = {f: r1(pct(*KNOWN_FAMILY[f]), f"{f} rate") for f in KNOWN_FAMILY}
    gap = pct(515, 880) - pct(510, 660)
    out["P1"] = {"free_form": {"passes": 510, "attempts": 660, "pct": rate["free-form"]},
                 "introspection": {"passes": 667, "attempts": 880, "pct": rate["introspection"]},
                 "structured": {"passes": 515, "attempts": 880, "pct": rate["structured"]},
                 "structured_minus_free_form_points": r1(gap, "structured minus free-form"),
                 "structured_minus_free_form_exact": str(Decimal(gap.numerator) / Decimal(gap.denominator))}
    d = sheet(SUPP23, "Supplementary Fig. 15f")
    con = {(r["strategy"], r["against"]): r for r in d if r["part"] in ("contrast", "contrast (not drawn)")}

    def cview(k):
        r = con[k]
        return {"change_points": round(r["net_change_pct_points"], 1), "low": r["interval_95_low_pct_points"],
                "high": r["interval_95_high_pct_points"], "rescued": r["rescued"], "lost": r["lost"],
                "pairs": r["n_pairs"]}
    for name, k in [("best_of_3_vs_free_form", ("free-form best of 3", "free-form")),
                    ("combined_vs_free_form", ("free-form combined", "free-form")),
                    ("structured_best_of_3_vs_structured", ("structured best of 3", "structured")),
                    ("structured_x3_vs_structured", ("structured x3", "structured")),
                    ("structured_combined_vs_structured", ("structured combined", "structured")),
                    ("structured_best_of_3_vs_free_form", ("structured best of 3", "free-form")),
                    ("structured_x3_vs_free_form", ("structured x3", "free-form")),
                    ("structured_vs_free_form_single", ("structured", "free-form"))]:
        out["P1"][name] = cview(k)
    # ---- P2
    blocks = {}
    for g in gaps:
        blocks.setdefault(g["block"], []).append(g)
    rng = {}
    for b, gs in blocks.items():
        exact = [(pct(g["structured_passes"], g["structured_attempts"]) - pct(g["free_form_passes"], g["free_form_attempts"]), g["variant"]) for g in gs]
        lo, hi = min(exact), max(exact)
        sp = sum(g["structured_passes"] for g in gs); sn = sum(g["structured_attempts"] for g in gs)
        fp = sum(g["free_form_passes"] for g in gs); fn = sum(g["free_form_attempts"] for g in gs)
        rng[b] = {"variants": len(gs),
                  "most_negative": {"variant": lo[1], "points": r1(lo[0], f"{b} min gap")},
                  "least_negative_or_most_positive": {"variant": hi[1], "points": r1(hi[0], f"{b} max gap")},
                  "pooled": {"structured": [sp, sn], "free_form": [fp, fn],
                             "gap_points": r1(pct(sp, sn) - pct(fp, fn), f"{b} pooled gap")},
                  "per_variant_points": {v: r1(x, f"{v} gap") for x, v in sorted(exact)}}
    het = {}
    order = list(label_of.values())
    for name, fb in [("structured vs free-form", "structured"), ("introspection vs free-form", "introspection")]:
        t = [(fam[(v, fb)]["passes"], fam[(v, fb)]["attempts"], fam[(v, "free-form")]["passes"],
              fam[(v, "free-form")]["attempts"]) for v in order]
        het[name] = q_printed(S488.cochran_q(t))
    t = [(fam[(v, "structured")]["passes"], fam[(v, "structured")]["attempts"], fam[(v, "free-form")]["passes"],
          fam[(v, "free-form")]["attempts"]) for v in order if v != "gemma3:27b"]
    het["structured vs free-form, without gemma3:27b"] = q_printed(S488.cochran_q(t))
    boxes = {(r["tier"], r["family"]): r for r in sheet(FIG6, "Fig. 7b") if r["part"] == "box" and r["variant"] == "all variants"}
    med = {f: {t: round(boxes[(t, f)]["median_pct"], 1) for t in ("simple", "medium", "complex")}
           for f in ("structured", "free-form", "introspection")}
    out["P2"] = {"gap_by_block": rng, "heterogeneity_S488_method": het, "median_operation_pass_pct": med,
                 "n_operations": {t: boxes[(t, "structured")]["n_operations"] for t in ("simple", "medium", "complex")}}
    # ---- P3
    gem = {r["variant"] for r in gaps if r["block"] == "Gemini"}
    ow = [v for v in order if v not in gem]
    ow_ids = {i for i, l in label_of.items() if l in ow}
    sfail = sum(fam[(v, "structured")]["attempts"] - fam[(v, "structured")]["passes"] for v in ow)
    by_group = {}
    for v in ow:
        for g, n in fail20[(v, "structured")].items():
            by_group.setdefault(g, {})[v] = n
    groups = {g: {"total": sum(x.values()), "by_variant": {v: n for v, n in x.items() if n}} for g, x in by_group.items()}
    kinds_s, kinds_f = {}, {}
    for c in cells:
        if c["variant"] not in ow_ids:
            continue
        fam_c = strat_family[c["label"]]
        tgt = kinds_s if fam_c == "structured" else kinds_f if fam_c == "free-form" else None
        if tgt is None:
            continue
        for k, v in c.items():
            if k.startswith("kind: ") and v:
                kk = k[6:]
                tgt.setdefault(kk, {"total": 0, "by_variant": {}})
                tgt[kk]["total"] += v
                lv = label_of[c["variant"]]
                tgt[kk]["by_variant"][lv] = tgt[kk]["by_variant"].get(lv, 0) + v
    tool = groups["tools refused by Ollama"]["total"] + groups["other tool or call failure"]["total"]
    out["P3"] = {"open_weight_structured_failed": sfail,
                 "tool_failures (tools refused + other tool or call failure)": tool,
                 "supp20_groups_open_weight_structured": groups,
                 "S447_fail_kinds_open_weight_structured": kinds_s,
                 "S447_fail_kinds_open_weight_free_form": kinds_f,
                 "open_weight_free_form_tool_kind_failures": sum(kinds_f.get(k, {}).get("total", 0) for k in TOOL_KINDS),
                 "open_weight_introspection_tool_group_failures": sum(
                     fail20[(v, "introspection")][g] for v in ow
                     for g in ("tools refused by Ollama", "other tool or call failure"))}
    # ---- P4
    th = {}
    for s in ("low", "medium", "high"):
        v = f"gpt-oss:20b ({s})"
        th[s] = {"passes": meds[v]["passes"], "attempts": meds[v]["attempts_n"],
                 "median_wall_time_s": meds[v]["median_wall_time_s_printed"],
                 "median_output_tokens": meds[v]["median_output_tokens_printed"],
                 "tool_or_call_failure_other_19b": bars[(v, "tool or call failure, other")],
                 "tool_or_call_failure_other_by_family_supp20": {
                     f: sum(fail20[(v, f)][g] for g in ("tools refused by Ollama", "other tool or call failure",
                                                       "other (harness, no code)"))
                     for f in ("free-form", "introspection", "structured")},
                 "passes_by_family": {f: [fam[(v, f)]["passes"], fam[(v, f)]["attempts"]] for f in KNOWN_FAMILY},
                 "passes_without_tools (free-form + introspection)": [
                     fam[(v, "free-form")]["passes"] + fam[(v, "introspection")]["passes"],
                     fam[(v, "free-form")]["attempts"] + fam[(v, "introspection")]["attempts"]]}
    th["high_minus_medium_passes"] = {f: th["high"]["passes_by_family"][f][0] - th["medium"]["passes_by_family"][f][0]
                                      for f in KNOWN_FAMILY}
    th["high_minus_medium_passes"]["all"] = th["high"]["passes"] - th["medium"]["passes"]
    th["high_minus_low_passes_all"] = th["high"]["passes"] - th["low"]["passes"]
    out["P4"] = th
    # ---- legend
    gk = fail20[("gemma3:27b", "structured")]
    out["legend_gemma3"] = {"structured_passes": fam[("gemma3:27b", "structured")]["passes"],
                            "structured_attempts": fam[("gemma3:27b", "structured")]["attempts"],
                            "tools_refused_by_Ollama": gk["tools refused by Ollama"],
                            "other_groups": {g: n for g, n in gk.items() if n and g != "tools refused by Ollama"}}
    out["ties"] = TIES
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    prov = {"script": SCRIPT, "script_sha256": sha(ROOT / SCRIPT), "command": f"uv run python {SCRIPT}",
            "repo_head": head, "inputs_sha256": {str(p.relative_to(ROOT)): sha(p)
                                                 for p in (FIG6, SUPP23, S447, SUPP19, SUPP20, S488_JSON, S488_PY)},
            "records": json.loads(FIG6.read_text())["stamp"],
            "reproduced": ["S488 committed Q 55.9 / 6.0 by its own cochran_q", "WANT 2,420 / 1,692",
                           "families 515/880, 510/660, 667/880", "gpt-oss:20b (high) 133/220",
                           "Supp 12 failures = attempts - passes per variant and family", "S447 cells = sheet 6a"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"provenance": prov, **out}, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
