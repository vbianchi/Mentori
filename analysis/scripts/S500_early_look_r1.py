#!/usr/bin/env python3
"""S500 - the early look at rater packet r1 (protocol amendment 8, D168), with amendment 7's analysis.

Why. Amendment 8 of findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md (D168, D170, 29 October 2026) lets Valerio's completed
packet r1 be analysed before the raters' deadline, after amendments 7 and 8 were committed (89db1b16). S08 --v22,
the protocol's engine, refuses before the deadline and with fewer than two packets, as it should; this script does
not change it. It imports S08's join, judge and MiniCheck readers and its statistics unchanged, and reads the one
packet itself. Every result is descriptive (amendment 8): with one rater, item 1 and the gate cannot be computed and
no decision is taken.

What it computes, on the analysis items (the 49 less any item an invalid cell removes, amendments 2, 4, 5):
  A. Protocol items 2, 3, 5 and D with r1 as the "mean human" (S08.v22_correlations; item 5's loop as S08's).
  B. Is the judge trusted (amendment 7, D169), one rater: quadratic-weighted kappa on 0 to 5 (judge 0 to 5, rater 1
     to 5), Cohen's kappa on pass or fail at bars 4 and 3 (the same bar for judge and rater), Spearman's rho; for
     correctness and faithfulness; 95% intervals over S08's 2,000 draws, seed 42. Delta needs two raters: not
     computed. Exploratory, not in amendment 7: Spearman of judge and of rater correctness with answer length.
  C. Amendment 7's three signals against the human verdict. J = judge correctness >= 4 (3); C = concept recall on
     S471's score() (D12 loose matcher, the one in force), >= 0.5 (0.33, 0.67, 1); M = MiniCheck precision against
     the whole source papers (--papers, S498's output), >= 0.5 (0.67, 0.8, 1); rules at least 1, 2, 3 of 3; human
     verdict r1 correctness >= 4 (3), and faithfulness as a second, descriptive verdict. Accuracy, exact two-sided
     McNemar of 2-of-3 against J, C and M (alpha 0.05, intersection-union), Cohen's kappa with its interval,
     balanced accuracy, sensitivity, specificity, pass rates, kappa between signal pairs, ROC AUC of the vote
     count. Items with no M value leave every comparison (listed). Without --papers, C runs on J and C only and says
     the rules are pending.

Refusals (exit 1, nothing written): S08 --v22 is on key v2.5 (D190, 31 October 2026; below); r1's sha256 differs from amendment 8's and --accept-hash is not given; the
packet's items or content (question, answer, expert answer) differ from the current master; a blank score cell
(amendment 2); invalid cells on more than 10 items (amendment 5).

    uv run python scripts/S500_early_look_r1.py [--papers findings/recompute/S498_human49_minicheck_papers.jsonl]

Writes findings/recompute/S500_early_look_r1/results.json. The packet file is never written or
committed. FD10 (D183): beside it, bootstrap/resamples.npz and bootstrap/index.json hold every resample the 95%
intervals come from: the 2,000 item draws (S08.v22_draws, seed 42) for parts A and B and for part C, the eval_ids in
the order the draws index, and each statistic's 2,000 resampled values (NaN where a resample gives no finite value,
which the interval leaves out). Nothing else changes: results.json is written as before, and every interval recomputed
from the saved values is checked equal to the one in results.json before either file is written. The whole folder is
git-ignored (D168). Per D168's line kept by Valerio, no number from here goes to the second rater before his packet
is back.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import S08_human_eval_analysis as S08  # noqa: E402
from machine import RECOMPUTE, ROOT, rel  # noqa: E402

PACKET = ROOT / "response/human_eval_v22/superseded/human_eval_v22_r1.xlsx"   # moved from packets/ on 31 October (amendment 9)
PACKET_SHA256 = "e9a177e1e16ab0d3938d81220ab706e09e41607daf134078d06db7ed2237c9e8"   # amendment 8
OUT = RECOMPUTE / "S500_early_look_r1"
COLS = {"Item": "eval_id", "Question": "question", "Answer to rate": "generated_answer",
        "Expert answer": "expected_answer", "Correctness (1-5)": "correctness",
        "Completeness (1-5)": "completeness", "Faithfulness (1-5)": "faithfulness", "Overall (1-5)": "overall"}
SCALES = ["correctness", "completeness", "faithfulness", "overall"]
STAT_SCALES = ["correctness", "completeness", "faithfulness"]
JUDGE_BARS = [4, 3]
HUMAN_BARS = [4, 3]
C_GRID = [0.5, 0.33, 0.67, 1.0]
M_GRID = [0.5, 0.67, 0.8, 1.0]
PRIMARY = {"judge_bar": 4, "c": 0.5, "m": 0.5, "human_bar": 4, "verdict": "correctness"}
RES_OUT = OUT / "bootstrap"     # FD10 (D183): the resamples behind every interval, git-ignored with OUT
RESAMPLES: dict | None = None   # name -> (draws set, 2,000 values, the interval returned); filled only by main()


class Refused(Exception):
    pass


def cell(v):
    """(value, state): a whole number 1 to 5 is valid; None or empty text blank; anything else invalid."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None, "blank"
    try:
        f = float(str(v).strip())
    except ValueError:
        return None, "invalid"
    if f.is_integer() and 1 <= f <= 5:
        return int(f), "ok"
    return None, "invalid"


def read_packet(path: Path) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb["Rating"]
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h).strip() if h is not None else "" for h in rows[0]]
    miss = [c for c in COLS if c not in head]
    if miss:
        raise Refused(f"the packet's Rating sheet lacks columns {miss}")
    idx = {COLS[c]: head.index(c) for c in COLS}
    return [{k: r[i] for k, i in idx.items()} for r in rows[1:] if r[idx["eval_id"]]]


def parse(rows: list[dict], eval_ids: list[str]) -> tuple[dict, dict]:
    """Amendments 2, 4, 5 for one packet: ratings by eval_id and the analysis item set."""
    if sorted(r["eval_id"] for r in rows) != sorted(eval_ids):
        raise Refused("the packet's items are not the protocol's 49")
    vals, blanks, invalid = {}, [], {}
    for r in rows:
        vals[r["eval_id"]] = {}
        for s in SCALES:
            v, st = cell(r[s])
            if st == "blank":
                blanks.append((r["eval_id"], s))
            elif st == "invalid":
                invalid.setdefault(r["eval_id"], []).append(s)
            vals[r["eval_id"]][s] = v
    if blanks:
        raise Refused(f"{len(blanks)} blank score cells: the packet is not complete (amendment 2)")
    bad_items = sorted(e for e, ss in invalid.items() if set(ss) & set(STAT_SCALES))
    if len(bad_items) > 10:
        raise Refused(f"invalid cells on {len(bad_items)} items, more than 10 (amendment 5)")
    kept = [e for e in eval_ids if e not in bad_items]
    return vals, {"analysed": kept, "removed": [{"eval_id": e, "scales": invalid[e]} for e in bad_items],
                  "invalid_overall_only": sorted(e for e, ss in invalid.items() if not set(ss) & set(STAT_SCALES))}


def _no_ctl(s: str) -> str:
    """The text less C0 control characters other than tab, newline and carriage return: an .xlsx cell cannot hold
    them (XML 1.0), so the packet lost them on writing (PDF-extraction residue such as \x08 in four answers)."""
    return "".join(ch for ch in s if ch in "\t\n\r" or ord(ch) >= 32)


def check_content(rows: list[dict]) -> dict:
    _, master = S08.v22_read_content(S08.V22_MASTER)
    m = {x["eval_id"]: x for x in master}
    diff, ctl = [], []
    for r in rows:
        for k in ("question", "generated_answer", "expected_answer"):
            a, b = str(r[k] or "").strip(), str(m[r["eval_id"]][k] or "").strip()
            if a != b:
                (ctl if _no_ctl(a) == _no_ctl(b) else diff).append((r["eval_id"], k))
    if diff:
        raise Refused(f"the packet differs from the current master on {len(diff)} cells (first {diff[0]})")
    return {"checked": ["question", "generated_answer", "expected_answer"], "items": len(rows), "differences": 0,
            "equal_only_after_removing_control_characters": ctl}


# ---- statistics --------------------------------------------------------------------------------------------
def kappa(a, b) -> float:
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n = a.size
    if n == 0:
        return float("nan")
    po = np.mean(a == b)
    pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if np.isclose(pe, 1.0) else float((po - pe) / (1 - pe))


def qwk06(a, b) -> float:
    """Quadratic-weighted kappa over 0..5 (S08.v22_qwk's formula on six categories)."""
    a, b = np.asarray(a, int), np.asarray(b, int)
    O = np.zeros((6, 6))
    np.add.at(O, (a, b), 1)
    E = np.outer(O.sum(axis=1), O.sum(axis=0)) / O.sum()
    k = np.arange(6)
    w = (k[:, None] - k[None, :]) ** 2
    den = (w * E).sum()
    return float("nan") if np.isclose(den, 0.0) else float(1 - (w * O).sum() / den)


def boot(f, arrays, draws, name=None, which="AB") -> list[float]:
    out, every = [], []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for idx in draws:
            v = f(*[x[idx] for x in arrays])
            every.append(float(v) if S08._finite(v) else float("nan"))
            if S08._finite(v):
                out.append(v)
    ci = S08._ci95(out)
    if name is not None and RESAMPLES is not None:          # FD10: kept, never used for a number here
        RESAMPLES[name] = (which, every, ci)
    return ci


def record_corr(h, j, m, draws, corr, prefix) -> None:
    """FD10: protocol items 2 to 4's resampled values, S08.v22_correlations' own loop on the same draws (rho(h, j),
    rho(h, m) and their difference D), recorded with the intervals that function returned."""
    if RESAMPLES is None:
        return
    h, j, m = (np.asarray(x, dtype=float) for x in (h, j, m))
    rj, rm, rd = [], [], []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for idx in draws:
            a, b = S08.v22_spearman(h[idx], j[idx]), S08.v22_spearman(h[idx], m[idx])
            rj.append(float(a) if S08._finite(a) else float("nan"))
            rm.append(float(b) if S08._finite(b) else float("nan"))
            rd.append(float(a - b) if S08._finite(a) and S08._finite(b) else float("nan"))
    for k, v in (("rho_human_judge", rj), ("rho_human_minicheck", rm), ("D", rd)):
        RESAMPLES[f"{prefix}.{k}"] = ("AB", v, corr[f"{k}_ci95"])


def mcnemar(rule_ok, single_ok) -> dict:
    """Exact two-sided McNemar on the discordant pairs: b = rule right and single wrong, c = the reverse."""
    from scipy.stats import binomtest
    b = int(np.sum(rule_ok & ~single_ok))
    c = int(np.sum(~rule_ok & single_ok))
    p = 1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5, alternative="two-sided").pvalue)
    return {"rule_right_single_wrong": b, "rule_wrong_single_right": c, "p_two_sided": p,
            "favours_rule": bool(b > c and p < 0.05)}


def describe(pred, truth, draws, name=None) -> dict:
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    tp, tn = np.sum(pred & truth), np.sum(~pred & ~truth)
    sens = float(tp / truth.sum()) if truth.sum() else float("nan")
    spec = float(tn / (~truth).sum()) if (~truth).sum() else float("nan")
    return {"accuracy": float(np.mean(pred == truth)), "kappa": kappa(pred, truth),
            "kappa_ci95": boot(kappa, [pred, truth], draws, name and f"{name}.kappa", "C"), "sensitivity": sens,
            "specificity": spec,
            "balanced_accuracy": float(np.nanmean([sens, spec])), "pass_rate": float(pred.mean())}


def auc(score, truth) -> float:
    from scipy.stats import mannwhitneyu
    s, t = np.asarray(score, float), np.asarray(truth, bool)
    if t.all() or (~t).all():
        return float("nan")
    return float(mannwhitneyu(s[t], s[~t]).statistic / (t.sum() * (~t).sum()))


# ---- the three parts ----------------------------------------------------------------------------------------
def part_a(kept, r1, judge, mc) -> dict:
    draws = S08.v22_draws(len(kept))
    h = np.array([r1[e]["faithfulness"] for e in kept], float)
    corr = S08.v22_correlations(h, np.array([judge[e]["faithfulness"] for e in kept], float),
                                np.array([mc[e] for e in kept], float), draws)
    record_corr(h, [judge[e]["faithfulness"] for e in kept], [mc[e] for e in kept], draws, corr, "A.items2to4")
    item5 = {}
    for d in ("correctness", "completeness"):
        hd = np.array([r1[e][d] for e in kept], float)
        jd = np.array([judge[e][d] for e in kept], float)
        item5[d] = {"rho": S08.v22_spearman(hd, jd), "ci95": boot(S08.v22_spearman, [hd, jd], draws,
                                                                 f"A.item5.{d}.rho")}
    return {"items2to4_r1_as_mean": corr, "item5": item5,
            "item1": "not computed: one rater (needs the second packet)", "decision": "none taken (amendment 8)"}


def part_b(kept, r1, judge, chars) -> dict:
    draws = S08.v22_draws(len(kept))
    out = {}
    for d in ("correctness", "faithfulness"):
        h = np.array([r1[e][d] for e in kept], int)
        j = np.array([judge[e][d] for e in kept], int)
        row = {"qwk_0to5": qwk06(j, h), "qwk_ci95": boot(qwk06, [j, h], draws, f"B.{d}.qwk_0to5"),
               "spearman": S08.v22_spearman(h, j),
               "spearman_ci95": boot(S08.v22_spearman, [h, j], draws, f"B.{d}.spearman")}
        for b in JUDGE_BARS:
            row[f"kappa_pass_at_{b}"] = kappa(j >= b, h >= b)
            row[f"kappa_pass_at_{b}_ci95"] = boot(kappa, [j >= b, h >= b], draws, f"B.{d}.kappa_pass_at_{b}")
            row[f"agreement_pass_at_{b}"] = float(np.mean((j >= b) == (h >= b)))
        out[d] = row
    L = np.array([chars[e] for e in kept], float)
    out["exploratory_length"] = {
        "spearman_judge_correctness_vs_chars": S08.v22_spearman(np.array([judge[e]["correctness"] for e in kept], float), L),
        "spearman_r1_correctness_vs_chars": S08.v22_spearman(np.array([r1[e]["correctness"] for e in kept], float), L),
        "note": "not in amendment 7; whether the judge rewards length more than the rater does"}
    out["delta"] = "not computed: needs two raters (amendment 7)"
    out["reference_line_kappa"] = 0.6
    return out


def part_c(kept, r1, judge, crec, mpap) -> dict:
    have_m = mpap is not None
    items = [e for e in kept if (not have_m) or S08._finite(mpap.get(e))]
    left = [e for e in kept if e not in items]
    draws = S08.v22_draws(len(items))
    jc = np.array([judge[e]["correctness"] for e in items], float)
    cr = np.array([crec[e] for e in items], float)
    mp = np.array([mpap[e] for e in items], float) if have_m else None
    cells = []
    for verdict in ("correctness", "faithfulness"):
        hv = np.array([r1[e][verdict] for e in items], float)
        for hb in HUMAN_BARS:
            truth = hv >= hb
            for jb in JUDGE_BARS:
                for ct in C_GRID:
                    for mt in (M_GRID if have_m else [None]):
                        sig = {"J": jc >= jb, "C": cr >= ct}
                        if have_m:
                            sig["M"] = mp >= mt
                        nm = f"C.{verdict}.h{hb}.j{jb}.c{ct}.m{mt}"
                        cell_ = {"verdict": verdict, "human_bar": hb, "judge_bar": jb, "c": ct, "m": mt,
                                 "n": len(items), "human_pass_rate": float(truth.mean()),
                                 "signals": {k: describe(v, truth, draws, f"{nm}.signals.{k}") for k, v in sig.items()},
                                 "pairwise_signal_kappa": {f"{a}-{b}": kappa(sig[a], sig[b])
                                                           for i, a in enumerate(sig) for b in list(sig)[i + 1:]}}
                        if have_m:
                            votes = sig["J"].astype(int) + sig["C"].astype(int) + sig["M"].astype(int)
                            rules = {f"{k}of3": votes >= k for k in (1, 2, 3)}
                            cell_["rules"] = {k: describe(v, truth, draws, f"{nm}.rules.{k}")
                                              for k, v in rules.items()}
                            ok2 = rules["2of3"] == truth
                            mc_ = {s: mcnemar(ok2, sig[s] == truth) for s in sig}
                            cell_["mcnemar_2of3_vs"] = mc_
                            cell_["claim_2of3_better_than_every_single"] = all(v["favours_rule"] for v in mc_.values())
                            cell_["auc_vote_count"] = auc(votes, truth)
                        cell_["primary"] = (verdict == PRIMARY["verdict"] and hb == PRIMARY["human_bar"]
                                            and jb == PRIMARY["judge_bar"] and ct == PRIMARY["c"]
                                            and (mt == PRIMARY["m"] if have_m else True))
                        cells.append(cell_)
    if RESAMPLES is not None:
        RESAMPLES["_C_items"] = list(items)
    return {"m_available": have_m, "items": len(items), "left_no_m": left, "cells": cells,
            "note": None if have_m else "M (MiniCheck against the whole papers) pending: rules not computed"}


def concept_recall(kept) -> dict:
    import S471_l3_concept_recall as S471
    import S470_l1_signals as S470
    key = S470.the_key()
    join = {it["eval_id"]: it for it in S08.v22_join()["items"]}
    _, master = S08.v22_read_content(S08.V22_MASTER)
    text = {x["eval_id"]: x["generated_answer"] for x in master}
    out = {}
    for e in kept:
        q = key["questions"][join[e]["question_id"]]
        out[e] = S471.score(text[e], q["expected_concepts"], False)["concept_recall_loose"]
    return out


def read_papers(path: Path, join_items) -> dict:
    by = {}
    for line in path.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            if "eval_id" in d:
                by[d["eval_id"]] = d.get("precision")
    return by


def write_resamples(kept: list, prov: dict) -> Path:
    """FD10 (D183): the draws and every statistic's resampled values, beside results.json in the git-ignored folder.
    Each interval is recomputed from the saved values (S08._ci95 of the finite ones) and must equal the interval the
    statistic returned, or nothing is written."""
    c_items = RESAMPLES.pop("_C_items")
    names = sorted(RESAMPLES)

    def same(a, b) -> bool:                                   # NaN equals NaN: no finite resample either way
        return all(x == y or (np.isnan(x) and np.isnan(y)) for x, y in zip(a, b))

    bad = [n for n in names if not same(S08._ci95([v for v in RESAMPLES[n][1] if np.isfinite(v)]), RESAMPLES[n][2])]
    if bad:
        raise Refused(f"FD10: {len(bad)} saved resample sets do not give their interval (first {bad[0]})")
    draws_ab, draws_c = np.array(S08.v22_draws(len(kept))), np.array(S08.v22_draws(len(c_items)))
    RES_OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(RES_OUT / "resamples.npz", draws_AB=draws_ab, draws_C=draws_c,
                        values=np.array([RESAMPLES[n][1] for n in names], dtype=float))
    index = {"_provenance": {**prov, "fd10": "D183 FD10 a: S500 writes its bootstrap resamples (git-ignored)"},
             "n_boot": S08.V22_N_BOOT, "seed": S08.SEED, "draws": "S08.v22_draws(n): rng = numpy default_rng(seed); "
             "each draw is rng.integers(0, n, n), indices into the eval_id order below",
             "eval_ids_AB": list(kept), "eval_ids_C": c_items,
             "statistics": [{"row": i, "name": n, "draws": RESAMPLES[n][0], "ci95": RESAMPLES[n][2]}
                            for i, n in enumerate(names)],
             "npz": {"draws_AB": list(draws_ab.shape), "draws_C": list(draws_c.shape),
                     "values": [len(names), S08.V22_N_BOOT]},
             "resamples_npz_sha256": S08._sha256(RES_OUT / "resamples.npz")}
    (RES_OUT / "index.json").write_text(json.dumps(index, indent=1, allow_nan=True) + "\n")
    return RES_OUT


def main(argv=None) -> int:
    global RESAMPLES
    RESAMPLES = {}
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", default=None, help="S498's per-item MiniCheck against the whole papers (jsonl)")
    ap.add_argument("--accept-hash", default=None, help="the packet's new sha256, if it changed after amendment 8")
    a = ap.parse_args(argv)
    # D190 (31 October 2026) moved S08's join and judge values to key v2.5 (S508's rows). The early look was computed
    # on key v2.4 (amendment 8), and amendment 9 records that it computed one completeness statistic before rater 1
    # re-rated completeness. Run now, it would correlate his v2.4 completeness (this packet) with the judge's v2.5
    # completeness, a second completeness statistic on two keys, which neither amendment allows (D190 review, F4 of
    # the second review). The results of 29 to 30 October stand as computed; to reproduce them, run this script with
    # S08 as it stood before D190 (git: scripts/S08_human_eval_analysis.py at 932a6ae8).
    if getattr(S08, "V22_KEY_VERSION", "2.4") != "2.4":
        print(f"REFUSED, nothing written: S08 --v22 is on key v{S08.V22_KEY_VERSION} since D190; the early look of "
              f"amendment 8 was computed on key v2.4 and is not re-run (amendment 9: one completeness statistic was "
              f"computed before the re-rating). To reproduce it, use S08 at 932a6ae8")
        return 1
    try:
        sha = S08._sha256(PACKET)
        if sha != PACKET_SHA256 and sha != a.accept_hash:
            raise Refused(f"the packet's sha256 {sha[:12]} is not amendment 8's {PACKET_SHA256[:12]}")
        join = S08.v22_join()
        ids = [it["eval_id"] for it in join["items"]]
        chars = {it["eval_id"]: it["answer_chars"] for it in json.loads(S08.V22_JOIN_OUT.read_text())["per_item"]}
        judge, _, jprov = S08.v22_judge_values(join)
        mc, _, mprov = S08.v22_minicheck_values(join)
        S08.v22_require_inputs(ids, judge, mc)
        rows = read_packet(PACKET)
        content = check_content(rows)
        r1, items = parse(rows, ids)
        kept = items["analysed"]
        crec = concept_recall(kept)
        mpap = read_papers(Path(a.papers), join["items"]) if a.papers else None
        res = {"packet_sha256": sha, "packet_hash_matches_amendment_8": sha == PACKET_SHA256,
               "content_check": content, "analysis_items": items, "n_analysed": len(kept),
               "A_protocol_items_r1": part_a(kept, r1, judge, mc),
               "B_judge_trust_one_rater": part_b(kept, r1, judge, chars),
               "C_three_signals": part_c(kept, r1, judge, crec, mpap),
               "per_item": [{"eval_id": e, "question_id": it["question_id"], "config": it["config"],
                             "answer_chars": chars[e], "r1": {k: r1[e][k] for k in SCALES},
                             "judge": {k: judge[e][k] for k in S08.V22_JUDGE_DIMS},
                             "minicheck_key_precision": mc[e], "concept_recall_loose": crec[e],
                             "minicheck_papers_precision": (mpap or {}).get(e)}
                            for it in join["items"] for e in [it["eval_id"]] if e in kept],
               "descriptive_only": True}
    except (Refused, S08.V22Refused) as e:
        print(f"REFUSED, nothing written: {e}")
        return 1
    prov = {"script": "scripts/S500_early_look_r1.py", "script_sha256": S08._sha256(Path(__file__)),
            "command": "uv run python " + " ".join(sys.argv), "generated": S08._utc_now(),
            "protocol": "findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md, amendments 7 and 8 (89db1b16)",
            "packet": rel(PACKET), "judge_files": jprov["files"], "minicheck_key_files": mprov["files"],
            "papers": a.papers, "papers_sha256": S08._sha256(a.papers) if a.papers else None}
    try:
        res_dir = write_resamples(kept, prov)
    except Refused as e:
        print(f"REFUSED, nothing written: {e}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(json.dumps({"_provenance": prov, **res}, default=float))
    (OUT / "results.json").write_text(json.dumps(doc, indent=1, allow_nan=True) + "\n")
    print(f"Wrote {rel(OUT / 'results.json')}: {len(kept)} items analysed, M "
          f"{'present' if mpap is not None else 'pending'}")
    print(f"Wrote {rel(res_dir / 'resamples.npz')} and {rel(res_dir / 'index.json')} (FD10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
