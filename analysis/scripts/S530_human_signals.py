#!/usr/bin/env python3
"""S530 - the numbers behind Figure 2 and Supplementary Figure 3: three automated signals set against the raters.

WHY. Amendment 7 of findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md (the signals, the rules at least 1, 2 and 3 of 3, the grid
of cut-offs, the comparison of judge-rater with rater-rater agreement) and amendment 8 (one rater, on Valerio's word).
S08 computes items 1 to 5, D and the decision; it does not write resamples or any of amendment 7. This script does, and
S531 draws what this script writes. build_order.md section 2 gives the number; fig2.md section 6 gives the functions.

WHAT IT READS. Rating rows through S08.v22_read_rating_rows and S08.v22_parse_ratings. Judge scores by
S08.v22_judge_values (S508, key v2.5), MiniCheck against the key by S08.v22_minicheck_values (S384), Concepts by
S510.concept_recall_v25, the old matcher by S500.concept_recall, Papers from S498's filtered output, Papers with no
source-list filter from S498's first output, the simple evaluators from S509's rows and its split rows. It imports
S500's kappa, qwk06, mcnemar and describe and S510's per_draw, summary_of, spearman_masked, rband and jband. S510's
read_inputs and compute stay out: compute casts ratings to int (S510:300-303, :330-331), so a mean of 2.5 would become 2.
It opens no output folder of S500, S501, S510 or S517.

WHAT IT COMPUTES, all on S08's draws (2,000 resamples of the items, seed 42):
  rater_scores           the included packets, each rater's scores, the raters' mean per item. Refuses more than two
                         included packets (S08b:317 defines Delta for rater 1 and rater 2 only; Valerio rules how more
                         raters enter), and any count other than --raters.
  bands                  raters' mean in bands <3, 3 to <4, >=4 through S510.rband, so 3.5 falls in the middle band.
  lanes (2e)             per rater, for quadratic-weighted kappa, Spearman's rho and Cohen's kappa at pass marks 4 and 3:
                         judge with raters, the mean over raters per draw; raters with each other; Delta, their difference
                         per draw (S08b:317). One rater: the judge's lane only.
  signals (2f)           Judge, Concepts and Papers and the rules against the raters' mean correctness at the same pass
                         mark, the mean itself, so 3.5 fails pass at 4 (S08b:291). Items with no Papers value leave
                         (S08b:303). An item with no Concepts value casts no vote and leaves the Concepts row and its
                         McNemar test, as S510.compute does (S510:327-351).
  grid                   the 64 cells on correctness and the 64 on faithfulness, as S500.part_c (S08b:293, :300-302).
  reliability_resamples  S08's item 1 statistics per draw, plus exact and adjacent agreement as shares. Two raters only.
  per_rater (S3b)        each signal with each rater, with the number of answers that have a value. The second judge's
                         rows (D273, SUPP3-B O1, D274) read S508 --judge second's folder through
                         S08.v22_judge_values(which="second"), with every check the main judge's rows pass; while that
                         folder holds no summary.json the rows stay empty.
  bias (S3g, sheet 2e)   mean of judge minus raters per answer, per draw, correctness and faithfulness.
  delta_count            how many of the eight Deltas fall in each of S08b:318-321's three wordings.
  verified_pass_answers  how many analysed answers come from verified pass, from the join's config.

GATE BEFORE WRITING (README.md:75-79). gate() compares this script's rho, D and intervals, and item 5's and item 1's, with
S08's results file to 1e-9, and the item set and the packets exactly. A statistic undefined on both sides (NaN here, null
in S08's file, which S08._json_safe writes) counts as equal. A difference refuses and nothing is written.

REFUSALS, each before any rating cell is read: --raters 2 before the protocol's deadline (S08.v22_deadline_check);
--raters 1 with no decision line (S08.v22_on_word); a missing S08 results file; a missing S498 filtered file, which S498 --filtered
writes through minicheck_filter.HEADING_RULE (no_heading since D245).

PAPERS WAITS (D206, Valerio, 2 November): with --papers-waits a missing S498 filtered file no longer refuses. Papers is
then absent, so f and the grid (which need Papers for their item set and for the rules) are null with the reason in
"papers_waits", and S3b's Papers row has no summary, as the second judge's has none. Every other value is the one the
file would give (S530_human_signals_test.py, test_papers_waits). With the file present the flag changes nothing.

    uv run --frozen python scripts/S530_human_signals.py --raters 2
    uv run --frozen python scripts/S530_human_signals.py --raters 1 --on-word D<nnn> [--papers-waits]

THE "generated" TIME (D315 Q4 O2). With the environment variable MENTORI_GENERATED_AT set, results.json's
_provenance.generated is exactly its value, which must read YYYY-MM-DDTHH:MM:SSZ (a real UTC time) or the run refuses
before anything is read; unset, it is the current UTC time, as before. The release's reproduce.py sets it from
ratings.tar's findings/recompute/S530_human_signals/generated_at.txt, the time of the run the committed figures record,
so a rebuild writes the same bytes. Nothing else in the output depends on it.

Writes findings/recompute/S530_human_signals/ (git-ignored): results.json, resamples.npz, grid.csv. Only the integrator
runs it on real packets, and only on Valerio's dated word. scripts/S530_human_signals_test.py runs it on made-up packets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S08_human_eval_analysis as S08  # noqa: E402
import S500_early_look_r1 as S500  # noqa: E402
import S510_fig2_panel_drafts as S510  # noqa: E402
from machine import RECOMPUTE, rel  # noqa: E402

SCRIPT = "scripts/S530_human_signals.py"
OUT = RECOMPUTE / "S530_human_signals"
S498_PLAIN = RECOMPUTE / "S498_human49_minicheck_papers.jsonl"
S498_FILTERED = RECOMPUTE / "S498_human49_minicheck_papers_filtered.jsonl"
S509_ROWS = RECOMPUTE / "S509_simple_evaluators_49" / "rows.jsonl"
S509_SPLIT = RECOMPUTE / "S509_simple_evaluators_49_split" / "rows.jsonl"
DIMS = ("correctness", "faithfulness")
PASS_MARKS = (4, 3)
RULE_COUNTS = (1, 2, 3)
PAPERS_WAITS = "Papers waits for S498's filtered file (scripts/S498_human49_minicheck_papers.py --filtered; D202, D245): f and the grid wait with it"
GATE_TOL = 1e-9
RELIABILITY = ("Krippendorff's alpha", "ICC(2,1)", "Gwet's AC2", "Mean weighted kappa", "Exact agreement",
               "Adjacent agreement")
S3B_SIGNALS = ("Judge", "Second judge", "Concepts", "Concepts, old matcher", "MiniCheck against the key", "Papers",
               "Papers, no source-list filter")
EVALUATORS = tuple(lab for _, lab in S510.S_METRICS) + ("Judge",)
DELTA_WORDS = {"above": "better", "includes zero": "about as well", "below": "less well"}   # S08b:318-321


class Refused(Exception):
    """Refused: nothing is written."""


GENERATED_AT_ENV = "MENTORI_GENERATED_AT"
GENERATED_AT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def generated_at() -> str | None:
    """D315 Q4 O2: MENTORI_GENERATED_AT, exactly, when set (a real UTC time written YYYY-MM-DDTHH:MM:SSZ, else
    Refused); None when unset, and main then stamps the current UTC time (S08._utc_now) where it always did."""
    v = os.environ.get(GENERATED_AT_ENV)
    if v is None:
        return None
    from datetime import datetime
    try:
        ok = bool(GENERATED_AT_RE.fullmatch(v)) and datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ") is not None
    except ValueError:
        ok = False
    if not ok:
        raise Refused(f"{GENERATED_AT_ENV} is {v!r}, not a UTC time written YYYY-MM-DDTHH:MM:SSZ")
    return v


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _pass_kappa(mark: int):
    return lambda a, b: S500.kappa(a >= mark, b >= mark)


STATS = (("Weighted kappa", S500.qwk06), ("Spearman's rho", lambda a, b: S08.v22_spearman(b, a)),
         ("Kappa, pass at 4", _pass_kappa(4)), ("Kappa, pass at 3", _pass_kappa(3)))


def public(s):
    """A summary with its resamples taken out, for results.json."""
    return None if s is None else {k: v for k, v in s.items() if k != "resamples"}


# ---------------------------------------------------------------- the raters

def rater_scores(rows: list, ids: list, raters: int) -> dict:
    """S08's parse, then one or two included packets as --raters says."""
    included, status, mats, items = S08.v22_parse_ratings(rows, ids, min_included=raters)
    if len(included) > 2:
        raise Refused(f"{len(included)} included packets: S08b:317 defines Delta for rater 1 and rater 2 only, and "
                      f"Valerio rules how more raters enter")
    if len(included) != raters:
        raise Refused(f"--raters {raters} on {len(included)} included packets ({', '.join(included)})")
    if raters == 1 and included != ["r1"]:
        raise Refused(f"the one-rater mode needs r1; included: {', '.join(included)}")
    per = {s: {d: mats[s][d].astype(int) for d in mats[s]} for s in included}
    mean = {d: np.mean([per[s][d] for s in included], axis=0) for d in S08.V22_STAT_SCALES}
    return {"included": included, "status": status, "items": items, "kept": items["analysed"], "per": per, "mean": mean}


def bands(values) -> np.ndarray:
    return np.array([S510.rband(float(v)) for v in values], int)


def judge_bands(values) -> np.ndarray:
    return np.array([S510.jband(int(v)) for v in values], int)


def cell_counts(rows_band, cols_band) -> list:
    g = np.zeros((3, 3), int)
    for a, b in zip(rows_band, cols_band):
        g[a, b] += 1
    return g.tolist()


# ---------------------------------------------------------------- panel e, per rater, bias

def lanes(scores: dict, judge: dict, draws) -> dict:
    """Judge with raters, raters with each other and Delta for each statistic and dimension (mock:266-286). Delta is
    the difference per draw, S08b:317."""
    out = {}
    slots = scores["included"]
    for dim in DIMS:
        j = judge[dim]
        out[dim] = {}
        for name, f in STATS:
            arrs = [scores["per"][s][dim] for s in slots]
            per_j = [S510.per_draw(f, [j, h], draws) for h in arrs]
            pts_j = [f(j, h) for h in arrs]
            lane = S510.summary_of(float(np.mean(pts_j)), np.mean(per_j, axis=0))
            other, delta = None, None
            if len(arrs) == 2:
                other = S510.summary_of(f(arrs[0], arrs[1]), S510.per_draw(f, arrs, draws))
                delta = S510.summary_of(lane["point"] - other["point"], lane["resamples"] - other["resamples"])
            out[dim][name] = {"judge": lane, "raters": other, "delta": delta}
    return out


def delta_count(e: dict) -> dict:
    """How many of the eight Deltas fall in each wording of S08b:318-321: interval above 0, including 0, below 0."""
    c = {w: 0 for w in DELTA_WORDS.values()}
    undefined = 0
    for dim in e.values():
        for lane in dim.values():
            if lane["delta"] is None:
                continue
            lo, hi = lane["delta"]["ci95"]
            if not (np.isfinite(lo) and np.isfinite(hi)):
                undefined += 1
            else:
                c[DELTA_WORDS["above" if lo > 0 else "below" if hi < 0 else "includes zero"]] += 1
    return {**c, "undefined": undefined}


def bias(mean: dict, judge: dict, draws) -> dict:
    f = lambda j, h: float(np.mean(j - h))                               # noqa: E731
    return {d: S510.summary_of(f(judge[d], mean[d]), S510.per_draw(f, [judge[d].astype(float), mean[d]], draws))
            for d in DIMS}


# ---------------------------------------------------------------- panel f and the grid

def signals(hc, jc, cv: list, mp, draws) -> dict:
    """The six rows of 2f at both pass marks: S510.compute's panel f (S510:325-354) on the raters' mean, not on an
    integer. hc, jc, mp over the items with a Papers value, cv a list with None where the item has no Concepts value."""
    has = np.array([v is not None for v in cv], bool)
    cr = np.array([np.nan if v is None else v for v in cv], float)
    acc = lambda p_, t_: float(np.mean(p_ == t_)) if p_.size else float("nan")      # noqa: E731
    on_c = lambda fn: (lambda p_, t_, m_: fn(p_[m_], t_[m_]))                       # noqa: E731
    out = {}
    for b in PASS_MARKS:
        truth = hc >= b
        sig = {"J": jc >= b, "C": has & (np.nan_to_num(cr, nan=-1.0) >= S510.C_PASS), "M": mp >= S510.M_PASS}
        votes = sum(v.astype(int) for v in sig.values())
        pred = {**sig, **{f"{k}of3": votes >= k for k in RULE_COUNTS}}
        cell = {"rater_pass_rate": float(truth.mean())}
        for k, pv in pred.items():
            if k == "C":
                cell[k] = {"accuracy": S510.summary_of(on_c(acc)(pv, truth, has),
                                                       S510.per_draw(on_c(acc), [pv, truth, has], draws)),
                           "kappa": S510.summary_of(on_c(S500.kappa)(pv, truth, has),
                                                    S510.per_draw(on_c(S500.kappa), [pv, truth, has], draws)),
                           "n": int(has.sum())}
            else:
                cell[k] = {"accuracy": S510.summary_of(acc(pv, truth), S510.per_draw(acc, [pv, truth], draws)),
                           "kappa": S510.summary_of(S500.kappa(pv, truth), S510.per_draw(S500.kappa, [pv, truth], draws)),
                           "n": int(truth.size)}
        ok2 = pred["2of3"] == truth
        cell["mcnemar_2of3_vs"] = {s: (S500.mcnemar(ok2[has], (sig[s] == truth)[has]) if s == "C"
                                       else S500.mcnemar(ok2, sig[s] == truth)) for s in sig}
        cell["claim_2of3_better_than_every_single"] = all(v["favours_rule"] for v in cell["mcnemar_2of3_vs"].values())
        out[str(b)] = cell
    return out


def _describe(pred, truth, draws, mask=None) -> dict:
    """S500.describe; with mask, on the items the mask holds, each resample keeping its masked items (S510:333)."""
    if mask is None or mask.all():
        return S500.describe(pred, truth, draws)
    d = S500.describe(pred[mask], truth[mask], [])
    f = lambda p_, t_, m_: S500.kappa(p_[m_], t_[m_])                    # noqa: E731
    v = S510.per_draw(f, [pred, truth, mask], draws)
    d["kappa_ci95"] = S08._ci95(list(v[np.isfinite(v)]))
    return d


def grid(hc, hf, jc, cv: list, mp, draws) -> list:
    """Every cell of amendment 7: verdict x rater bar x judge bar x Concepts cut x Papers cut, as S500.part_c's loops
    (S08b:293, :300-302), with an item with no Concepts value casting no vote."""
    has = np.array([v is not None for v in cv], bool)
    cr = np.array([-1.0 if v is None else v for v in cv], float)
    cells = []
    for verdict, hv in (("correctness", hc), ("faithfulness", hf)):
        for hb in S500.HUMAN_BARS:
            truth = hv >= hb
            for jb in S500.JUDGE_BARS:
                for ct in S500.C_GRID:
                    for mt in S500.M_GRID:
                        sig = {"J": jc >= jb, "C": has & (cr >= ct), "M": mp >= mt}
                        votes = sum(v.astype(int) for v in sig.values())
                        rules = {f"{k}of3": votes >= k for k in RULE_COUNTS}
                        ok2 = rules["2of3"] == truth
                        cells.append({
                            "verdict": verdict, "rater_bar": hb, "judge_bar": jb, "concepts_cut": ct, "papers_cut": mt,
                            "n": int(truth.size), "rater_pass_rate": float(truth.mean()),
                            "signals": {k: _describe(v, truth, draws, has if k == "C" else None) for k, v in sig.items()},
                            "rules": {k: S500.describe(v, truth, draws) for k, v in rules.items()},
                            "pairwise_signal_kappa": {f"{a}-{b}": S500.kappa(sig[a], sig[b])
                                                      for i, a in enumerate(sig) for b in list(sig)[i + 1:]},
                            "mcnemar_2of3_vs": {s: (S500.mcnemar(ok2[has], (sig[s] == truth)[has]) if s == "C"
                                                    else S500.mcnemar(ok2, sig[s] == truth)) for s in sig},
                            "auc_vote_count": S500.auc(votes, truth),
                            "primary": (verdict == S500.PRIMARY["verdict"] and hb == S500.PRIMARY["human_bar"]
                                        and jb == S500.PRIMARY["judge_bar"] and ct == S500.PRIMARY["c"]
                                        and mt == S500.PRIMARY["m"])})
    return cells


# ---------------------------------------------------------------- Supplementary Figure 3

def reliability_resamples(F, draws) -> dict:
    """Item 1 per draw on S08's own functions (S08.v22_irr), with exact and adjacent agreement as shares, mean over
    rater pairs, so all six fit one axis. F: raters x items."""
    funcs = {"Krippendorff's alpha": S08.v22_alpha_ordinal, "ICC(2,1)": S08.v22_icc_2_1,
             "Gwet's AC2": lambda Z: S08.v22_gwet_ac2(Z)[0], "Mean weighted kappa": lambda Z: S08.v22_mean_pairwise_qwk(Z)[0],
             "Exact agreement": lambda Z: S08.v22_agreement(Z)["exact_pct_mean_pairwise"] / 100,
             "Adjacent agreement": lambda Z: S08.v22_agreement(Z)["adjacent_pct_mean_pairwise"] / 100}
    import warnings
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name in RELIABILITY:
            f = funcs[name]
            vals = [f(F[:, idx]) for idx in draws]
            out[name] = S510.summary_of(f(F), np.array([float(v) if S08._finite(v) else np.nan for v in vals]))
    return out


def per_rater(scores: dict, signal_values: dict, draws) -> list:
    """Each signal with each rater, both dimensions: 7 x 2 x 2 rows. A signal with no reader (the second judge) and a
    rater who is not there give a row with no summary and no n. n counts the answers with a value for that signal."""
    rows = []
    for sig in S3B_SIGNALS:
        for dim in DIMS:
            for k in (0, 1):
                slot = scores["included"][k] if k < len(scores["included"]) else None
                v = signal_values.get(sig)
                row = {"signal": sig, "dimension": dim, "rater": k + 1, "n": None, "summary": None}
                if slot is not None and v is not None:
                    a = v[dim] if isinstance(v, dict) else v
                    h = scores["per"][slot][dim].astype(float)
                    row["n"] = int(np.sum(np.isfinite(a)))
                    row["summary"] = S510.summary_of(S510.spearman_masked(h, a),
                                                     S510.per_draw(S510.spearman_masked, [h, a], draws))
                rows.append(row)
    return rows


def simple_rows(mean: dict, judge: dict, simple: dict, kept: list, draws) -> list:
    """Spearman's rho of each simple evaluator and the judge with the raters' mean (S510.compute part s)."""
    rows = []
    for key, lab in tuple(S510.S_METRICS) + ((None, "Judge"),):
        for dim in DIMS:
            h = mean[dim].astype(float)
            v = judge[dim].astype(float) if key is None else np.array(
                [np.nan if simple[e].get(key) is None else simple[e][key] for e in kept], float)
            rows.append({"evaluator": lab, "dimension": dim, "n": int(np.sum(np.isfinite(v))),
                         "summary": S510.summary_of(S510.spearman_masked(h, v),
                                                    S510.per_draw(S510.spearman_masked, [h, v], draws))})
    return rows


# ---------------------------------------------------------------- everything

def compute(inp: dict, n_boot: int = S08.V22_N_BOOT) -> tuple:
    """inp: ids, configs, rows (rating rows), raters, judge, mc, concepts, concepts_old, papers, papers_plain, simple.
    Returns (results, resamples)."""
    sc = rater_scores(inp["rows"], inp["ids"], inp["raters"])
    kept = sc["kept"]
    if not kept:
        raise Refused("no item is left in the analysis set")
    draws = S08.v22_draws(len(kept), n_boot)
    judge = {d: np.array([inp["judge"][e][d] for e in kept], int) for d in S08.V22_STAT_SCALES}
    mck = np.array([inp["mc"][e] for e in kept], float)
    hc, hf, hk = (sc["mean"][d] for d in ("correctness", "faithfulness", "completeness"))
    res: dict = {"raters": inp["raters"], "included": sc["included"], "status": sc["status"], "seed": S08.SEED,
                 "n_boot": n_boot, "n_items": len(inp["ids"]), "n_analysed": len(kept), "analysis_items": sc["items"],
                 "verified_pass_answers": sum(1 for e in kept if inp["configs"][e] == "verified_pass")}
    res["a"] = {"grid": cell_counts(judge_bands(judge["correctness"]), bands(hc))}
    res["b"] = {"grid": cell_counts(bands(hf), judge_bands(judge["faithfulness"]))}
    corr = {"rho_judge": S510.summary_of(S08.v22_spearman(hf, judge["faithfulness"]),
                                         S510.per_draw(S08.v22_spearman, [hf, judge["faithfulness"]], draws)),
            "rho_minicheck": S510.summary_of(S08.v22_spearman(hf, mck), S510.per_draw(S08.v22_spearman, [hf, mck], draws))}
    corr["D"] = S510.summary_of(corr["rho_judge"]["point"] - corr["rho_minicheck"]["point"],
                                corr["rho_judge"]["resamples"] - corr["rho_minicheck"]["resamples"])
    res["d"] = {k: public(v) for k, v in corr.items()}
    e = lanes(sc, judge, draws)
    res["e"] = {d: {st: {k: public(v) for k, v in row.items()} for st, row in e[d].items()} for d in DIMS}
    res["delta_count"] = delta_count(e)
    bi = bias(sc["mean"], judge, draws)
    res["bias"] = {d: public(bi[d]) for d in DIMS}

    if inp["papers"] is None:                    # D206: f and the grid wait for the heading rule
        res["f"], res["grid"], res["papers_waits"] = None, None, PAPERS_WAITS
    else:
        _f_and_grid(res, inp, kept, judge, hc, hf, n_boot)

    F = np.array([sc["per"][s]["faithfulness"] for s in sc["included"]])
    rel_ = reliability_resamples(F, draws) if inp["raters"] == 2 else None
    res["s3a"] = None if rel_ is None else {k: public(v) for k, v in rel_.items()}
    res["alpha"] = None if rel_ is None else rel_["Krippendorff's alpha"]["point"]
    finite = lambda d: np.array([np.nan if d.get(x) is None else d[x] for x in kept], float)   # noqa: E731
    sig_vals = {"Judge": {d: judge[d].astype(float) for d in DIMS}, "Concepts": finite(inp["concepts"]),
                "Concepts, old matcher": finite(inp["concepts_old"]), "MiniCheck against the key": mck,
                "Papers": None if inp["papers"] is None else finite(inp["papers"]),
                "Papers, no source-list filter": finite(inp["papers_plain"])}
    if inp.get("second_judge") is not None:                 # D274: the second judge's rows, as the judge's
        sig_vals["Second judge"] = {d: np.array([np.nan if inp["second_judge"][e].get(d) is None
                                                 else inp["second_judge"][e][d] for e in kept], float) for d in DIMS}
    res["s3b"] = [{**{k: v for k, v in r.items() if k != "summary"}, "summary": public(r["summary"])}
                  for r in per_rater(sc, sig_vals, draws)]
    res["s3c"] = {"grid": cell_counts(judge_bands(judge["completeness"]), bands(hk)),
                  "rho": public(S510.summary_of(S08.v22_spearman(hk, judge["completeness"]),
                                                S510.per_draw(S08.v22_spearman, [hk, judge["completeness"]], draws)))}
    res["correctness_rho"] = public(S510.summary_of(S08.v22_spearman(hc, judge["correctness"]),
                                                    S510.per_draw(S08.v22_spearman, [hc, judge["correctness"]], draws)))
    res["s3e"] = [{**{k: v for k, v in r.items() if k != "summary"}, "summary": public(r["summary"])}
                  for r in simple_rows(sc["mean"], judge, inp["simple"], kept, draws)]
    slots = (sc["included"] + [None])[:2]
    hf_band = bands(hf)
    res["per_answer"] = [dict(
        eval_id=x, **{f"r{k + 1}_{d}": None if s_ is None else int(sc["per"][s_][d][i])
                      for k, s_ in enumerate(slots) for d in S08.V22_STAT_SCALES},
        raters_correctness=float(hc[i]), raters_faithfulness=float(hf[i]), raters_completeness=float(hk[i]),
        band_faithfulness=int(hf_band[i]),
        judge_correctness=int(judge["correctness"][i]), judge_faithfulness=int(judge["faithfulness"][i]),
        judge_completeness=int(judge["completeness"][i]), minicheck_key_precision=float(mck[i]))
        for i, x in enumerate(kept)]
    samples = {f"d.{k}": v["resamples"] for k, v in corr.items()}
    return res, samples


def _f_and_grid(res: dict, inp: dict, kept: list, judge: dict, hc, hf, n_boot: int) -> None:
    """Panel f and the grid, on the items with a Papers value."""
    with_m = [i for i, x in enumerate(kept) if S08._finite(inp["papers"].get(x))]
    ids_m = [kept[i] for i in with_m]
    draws_m = S08.v22_draws(len(ids_m), n_boot)
    jc_m, hc_m, hf_m = judge["correctness"][with_m], hc[with_m], hf[with_m]
    cv = [inp["concepts"].get(x) for x in ids_m]
    mp = np.array([inp["papers"][x] for x in ids_m], float)
    f = signals(hc_m, jc_m, cv, mp, draws_m)
    res["f"] = {"n": len(ids_m), "items_left_no_papers": [x for x in kept if x not in ids_m],
                "items_no_concepts": [x for x, v in zip(ids_m, cv) if v is None],
                **{b: {k: ({"n": v["n"], "accuracy": public(v["accuracy"]), "kappa": public(v["kappa"])}
                           if isinstance(v, dict) and "accuracy" in v else v) for k, v in cell.items()}
                   for b, cell in f.items()}}
    res["grid"] = grid(hc_m, hf_m, jc_m, cv, mp, draws_m)


def gate(res: dict, s08: dict) -> int:
    """S530 against S08's results file: the known numbers first. Returns how many were compared, or refuses."""
    def undefined(v) -> bool:
        return v is None or np.isnan(float(v))

    def same(a, b) -> bool:
        if undefined(a) or undefined(b):
            return undefined(a) and undefined(b)
        return abs(float(a) - float(b)) <= GATE_TOL
    pairs = []
    it = s08["items2to4"]
    for ours, theirs in (("rho_judge", "rho_human_judge"), ("rho_minicheck", "rho_human_minicheck"), ("D", "D")):
        o = res["d"][ours]
        pairs += [(theirs, o["point"], it[theirs]), (f"{theirs} low", o["ci95"][0], it[f"{theirs}_ci95"][0]),
                  (f"{theirs} high", o["ci95"][1], it[f"{theirs}_ci95"][1])]
    for dim, o in (("correctness", res["correctness_rho"]), ("completeness", res["s3c"]["rho"])):
        d = s08["item5_descriptive"][dim]
        pairs += [(f"item 5 {dim}", o["point"], d["rho_human_judge"]), (f"item 5 {dim} low", o["ci95"][0], d["ci95"][0]),
                  (f"item 5 {dim} high", o["ci95"][1], d["ci95"][1])]
    irr = s08.get("item1_reliability_faithfulness")
    if res["s3a"] is not None:
        for ours, theirs in (("Krippendorff's alpha", "krippendorff_alpha_ordinal"), ("ICC(2,1)", "icc_2_1"),
                             ("Gwet's AC2", "gwet_ac2_quadratic"), ("Mean weighted kappa", "mean_pairwise_qwk")):
            o = res["s3a"][ours]
            pairs += [(theirs, o["point"], irr[theirs]), (f"{theirs} low", o["ci95"][0], irr["ci95"][theirs][0]),
                      (f"{theirs} high", o["ci95"][1], irr["ci95"][theirs][1])]
    elif irr is not None:
        raise Refused("S08's results hold item 1 and this run has one rater: not the same run")
    bad = [name for name, a, b in pairs if not same(a, b)]
    if res["analysis_items"]["analysed"] != s08["analysis_items"]["analysed"]:
        bad.append("the item set")
    if res["included"] != s08["included"]:
        bad.append("the packets")
    if bad:
        raise Refused(f"S530 does not reproduce S08's results file: {', '.join(bad[:6])}. Nothing written")
    return len(pairs) + 2


# ---------------------------------------------------------------- reading and writing

def read_jsonl(path: Path) -> list:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def read_simple(rows_f: Path = S509_ROWS, split_f: Path = S509_SPLIT) -> dict:
    """S509's rows; a value its split rows hold fills the null of the same answer. A row in both refuses."""
    out = {r["eval_id"]: dict(r["signals"]) for r in read_jsonl(rows_f)}
    if split_f.exists():
        for r in read_jsonl(split_f):
            e = r["eval_id"]
            if out[e].get("semantic_similarity") is not None:
                raise Refused(f"{e} has a bge-m3 value and a split value")
            out[e]["semantic_similarity"] = r["semantic_similarity"]
    return out


def read_inputs(raters: int, ratings=None, papers_waits: bool = False) -> dict:
    """Every input by its owner's reader. The rating cells are read last, after the machine inputs have been checked."""
    waits = papers_waits and not S498_FILTERED.exists()
    if not S498_FILTERED.exists() and not waits:
        raise Refused(f"{rel(S498_FILTERED)} is not there: run S498 --filtered once Valerio has ruled what a heading "
                      f"is (Q1). No filtered Papers value exists before the rule does")
    join = S08.v22_join()
    ids = [it["eval_id"] for it in join["items"]]
    judge, _, jprov = S08.v22_judge_values(join)
    second, sprov = None, None
    if (S08.V22_SECOND_JUDGE_DIR / "summary.json").is_file():     # D274: S508 --judge second has written its summary
        second, _, sprov = S08.v22_judge_values(join, which="second")
        gap = [e for e in ids if e not in second or not all(S08._finite(second[e].get(d)) for d in DIMS)]
        if gap:
            raise Refused(f"the second judge has no score on {len(gap)} of {len(ids)} items: {gap[:5]}")
    mc, _, mprov = S08.v22_minicheck_values(join)
    S08.v22_require_inputs(ids, judge, mc)
    path = Path(ratings) if ratings else S08.V22_MASTER
    S08.v22_require_same_content(path)
    per = [{"eval_id": it["eval_id"], "question_id": it["question_id"]} for it in join["items"]]
    concepts, cprov = S510.concept_recall_v25(per)
    return {"ids": ids, "configs": {it["eval_id"]: it["config"] for it in join["items"]}, "raters": raters,
            "judge": judge, "second_judge": second, "mc": mc, "concepts": concepts, "concepts_old": S500.concept_recall(ids),
            "papers": None if waits else {r["eval_id"]: r.get("precision") for r in read_jsonl(S498_FILTERED)},
            "papers_plain": {r["eval_id"]: r.get("precision") for r in read_jsonl(S498_PLAIN)},
            "simple": read_simple(), "rows": S08.v22_read_rating_rows(path),
            "provenance": {"ratings": {rel(path): sha(path)}, "judge_files": jprov["files"],
                           "second_judge_files": None if sprov is None else sprov["files"],
                           "minicheck_files": mprov["files"], "concepts": cprov,
                           "papers": {rel(S498_PLAIN): sha(S498_PLAIN),
                                      **({} if waits else {rel(S498_FILTERED): sha(S498_FILTERED)})},
                           "simple": {rel(p_): sha(p_) for p_ in (S509_ROWS, S509_SPLIT) if p_.exists()}}}


def write_grid_csv(cells: list, path: Path) -> None:
    head = ["verdict", "rater_bar", "judge_bar", "concepts_cut", "papers_cut", "n", "rater_pass_rate", "primary",
            "signal_or_rule", "accuracy", "kappa", "kappa_ci95_low", "kappa_ci95_high", "sensitivity", "specificity",
            "balanced_accuracy", "pass_rate", "mcnemar_rule_right_single_wrong", "mcnemar_rule_wrong_single_right",
            "mcnemar_p_two_sided", "mcnemar_favours_rule", "auc_vote_count", "kappa_J_C", "kappa_J_M", "kappa_C_M"]
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        for c in cells:
            base = [c[k] for k in ("verdict", "rater_bar", "judge_bar", "concepts_cut", "papers_cut", "n",
                                   "rater_pass_rate", "primary")]
            tail = [c["auc_vote_count"], *(c["pairwise_signal_kappa"][k] for k in ("J-C", "J-M", "C-M"))]
            for k, v in {**c["signals"], **c["rules"]}.items():
                m = c["mcnemar_2of3_vs"].get(k, {})
                w.writerow(base + [k, v["accuracy"], v["kappa"], *v["kappa_ci95"], v["sensitivity"], v["specificity"],
                                   v["balanced_accuracy"], v["pass_rate"], m.get("rule_right_single_wrong"),
                                   m.get("rule_wrong_single_right"), m.get("p_two_sided"), m.get("favours_rule")] + tail)


def write(res: dict, samples: dict, out: Path, prov: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    def plain(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    body = S08._json_safe(json.loads(json.dumps({"_provenance": prov, **res}, default=plain)))
    (out / "results.json").write_text(json.dumps(body, indent=1, allow_nan=False) + "\n")
    np.savez_compressed(out / "resamples.npz", **samples)
    if res["grid"] is not None:
        write_grid_csv(res["grid"], out / "grid.csv")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raters", type=int, choices=(1, 2), required=True)
    ap.add_argument("--on-word", help="--raters 1: the decision line that records Valerio's word (S08.v22_on_word)")
    ap.add_argument("--ratings", type=Path, help="the ratings sheet, default S08's master")
    ap.add_argument("--s08-results", type=Path, help="default S08's results file for this mode")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--papers-waits", action="store_true",
                    help="D206: run without S498's filtered file; f, the grid and S3b's Papers row wait for the heading rule")
    a = ap.parse_args(argv)
    try:
        generated = generated_at()                   # refuses a malformed MENTORI_GENERATED_AT before anything is read
        if a.raters == 1:
            word = S08.v22_on_word(a.on_word)
        else:
            word = None
            S08.v22_deadline_check()                 # before any rating cell is opened
        s08_f = a.s08_results or (S08.V22_ONE_RATER_OUT if a.raters == 1 else S08.V22_RESULTS_OUT)
        if not Path(s08_f).exists():
            raise Refused(f"{rel(Path(s08_f))} is not there: run S08 first; S530 reproduces it before it writes")
        inp = read_inputs(a.raters, a.ratings, **({"papers_waits": True} if a.papers_waits else {}))
        res, samples = compute(inp)
        compared = gate(res, json.loads(Path(s08_f).read_text()))
    except (Refused, S08.V22Refused, S510.Refused) as e:
        print(f"S530 REFUSED, nothing written: {e}")
        return 1
    print(f"S530: S08's results reproduced, {compared} values to {GATE_TOL}")
    prov = {"script": SCRIPT, "script_sha256": sha(ROOT / SCRIPT), "command": "uv run --frozen python " + " ".join(
            [SCRIPT] + list(sys.argv[1:] if argv is None else argv)), "generated": generated or S08._utc_now(),
            "on_word": word, "s08_results": {rel(Path(s08_f)): sha(s08_f)}, "reproduced": compared,
            "inputs": inp["provenance"]}
    write(res, samples, a.out, prov)
    print(f"S530: wrote results.json, resamples.npz and grid.csv in {rel(a.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
