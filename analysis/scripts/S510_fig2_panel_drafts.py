#!/usr/bin/env python3
"""S510 - Figure 2's panels drawn as drafts, two or three layouts each, for Valerio's panel-by-panel review (D183).

WHY. D183 (Valerio, 30 October, figures dashboard FD6 to FD14): FD8 a, a neutral title while one rater's packet is
read, and the panels drawn now for a review panel by panel, kept out of git as early-look material (D168); FD9 a, the
correctness panel is one 3 x 3 grid of counts, placed first; FD10 a, S500's bootstrap resamples drawn from its file;
FD11 c, the judge scores set against the rater are the lock's call on key v2.5 only (S508; S373's rows dropped);
FD12 a, ROUGE-L, METEOR, number overlap and bge-m3 similarity on the 49 rated answers, exploratory, for the
Supplementary human-evaluation figure (S509); FD13 c, panel f shows accuracy (with the protocol's McNemar tests) and
Cohen's kappa side by side. D171 (1): on an ordinal scale yellow is bigger and blue smaller (cividis); D171 (2): the
rater's scores split in bands 1-2, 3 and 4-5; D171 (4): the picked designs (a3 100% bars, b5 in bands, c4 bootstrap
cloud, e4 horizontal box plots of the resamples).

THE PANELS (the order of the dashboard's Figure 2; FD9 a puts correctness first):
  a  correctness: rater bands 1-2, 3, 4-5 against judge bands 0-2, 3, 4-5, one 3 x 3 grid of counts
  b  faithfulness: the judge's score (0 to 5) for each rater level, 100% bars
  c  MiniCheck precision against the key, per item, by rater faithfulness band, with each band's median
  d  each bootstrap resample's rho(rater, judge) against rho(rater, MiniCheck), faithfulness (protocol items 2 to 4)
  e  judge-rater agreement as box plots of the resamples: weighted kappa, Spearman's rho, Cohen's kappa at pass bars
     4 and 3, correctness and faithfulness; kappa 0.6 a reference line only (D169 (2))
  f  the three signals J, C, M and the rules at least 1, 2, 3 of 3 against the rater's verdict: accuracy with the
     exact McNemar tests of 2 of 3 against each signal (amendment 7's primary) beside Cohen's kappa, at bar 4
     (judge 4, rater 4, the primary cell) and bar 3 (judge 3, rater 3), C and M at 0.5
  s  Supplementary (FD12 a): the four simple evaluators against the rater, exploratory
Each panel is drawn in two or three layouts (a1, a2, a3 and so on), each its own PDF, SVG and PNG, plus a contact
sheet of all of them.

WHAT IT COMPUTES. S501 computed none; this script must, because S500's statistics hold S373's judge (FD11 c drops it).
With S508's scores in the judge's place it recomputes, with S500's own functions (kappa, qwk06, mcnemar) and S08's
Spearman, on S500's saved draws (FD10: the same 2,000 resamples of the items, seed 42), every statistic a panel draws
that involves the judge; the rater-only and signal-only values (C, M, MiniCheck against the key) are S500's per-item
values. Accuracy's interval (f) uses the same draws; amendment 7 names none, so it is descriptive. One rater: every
panel is descriptive (amendment 8).
  C ("concept recall, key v2.5, D181 rule") is computed here, not taken from S500: D181 (experiments/README.md),
    S505.recall_q(answer, concepts, question, "loose", "need", empty="b") on key v2.5 (its sha256 pinned as S508's),
    the answer texts S500's concept_recall() reads, key v2.5's question text. It passes at C >= 0.5, S500's rule (its
    PRIMARY c). Under reading (b) a question whose every concept is made only of question words has no C: that item
    casts no C vote (no pass vote in the rules), and the C row's accuracy and kappa and the McNemar test of 2 of 3
    against C use the items with a C value (provenance.json lists the items without one). S500's old C (D12's loose
    matcher on key v2.4) is kept only for the reproduce gate.
  M ("MiniCheck, without the source-list filter") is S498's value as S500 holds it.

REPRODUCE BEFORE WRITING (README.md:75-79). Before anything new is computed or written, compute() runs on S500's own
inputs (its per-item judge, S373's, and its old C) and its saved draws, and must give S500's results.json values
(reproduce_s500: part A rho with the judge and with MiniCheck and D, part B weighted kappa, rho and kappa at bars 4 and
3 with their intervals, part C at bars 4 and 3 with J, C, M and the rules, McNemar and the 2-of-3 claim) within
GATE_TOL. It prints "S500 reproduced N of N" and no value; any difference refuses.

REFUSALS (exit 1, nothing drawn): S508's results are missing, incomplete, on another key, or their recheck did not
pass after all 49 items were judged; S500's results or its FD10 resamples are missing, or their draws are not
S08.v22_draws; S500 ran without --papers (no M); S500's results are not reproduced from its own inputs; an analysed
item has no S508 row; key v2.5's sha256 is not amendment 9's, or an item's question or answer text is missing;
S509's rows are missing or not the 49.

    uv run --frozen python scripts/S510_fig2_panel_drafts.py [--out DIR]

Writes findings/recompute/S510_fig2_drafts/ (git-ignored, D168: the drafts and their numbers compare a human rating
with the judge): one <id>.pdf, .svg and .png per layout, contact_sheet.png and .pdf, numbers.json (every number a
draft draws), legend_draft.md (the neutral title and the panel definitions, no number) and provenance.json (the
inputs' sha256, any text-crowding a draft has). No number goes to the second rater before his packet is back (D170).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S457_fig2_panels as S457  # noqa: E402
import S500_early_look_r1 as S500  # noqa: E402
import S508_judge_49_v25 as S508  # noqa: E402
from machine import RECOMPUTE, rel  # noqa: E402

S08 = S500.S08
OUT = RECOMPUTE / "S510_fig2_drafts"
S500_RESULTS = S500.OUT / "results.json"
S500_BOOT = S500.RES_OUT
S508_DIR = S508.OUT
S509_DIR = RECOMPUTE / "S509_simple_evaluators_49"
TITLE = "Agreement of three automated signals with expert raters"       # FD8 a, the option's own example
SCRIPT = "scripts/S510_fig2_panel_drafts.py"
R_BANDS, J_BANDS = ("1-2", "3", "4-5"), ("0-2", "3", "4-5")
SETTINGS = (("bar 4", 4, 4), ("bar 3", 3, 3))                         # (label, judge bar, rater bar); C, M at 0.5
C_LABEL = "concept recall, key v2.5, D181 rule"                      # D181: S505 loose Q-need, reading (b), key v2.5
M_LABEL = "MiniCheck, without the source-list filter"   # S498's M, no D172 filter
C_PASS = 0.5                                                          # S500 PRIMARY["c"]: C passes at C >= 0.5
M_PASS = 0.5                                                          # S500 PRIMARY["m"]
F_ROWS = (("J", "signals", "Judge (J)"), ("C", "signals", "Concept recall (C)\nkey v2.5, D181 rule"),
          ("M", "signals", "MiniCheck (M), without the\nsource-list filter"),
          ("1of3", "rules", "At least 1 of 3"), ("2of3", "rules", "At least 2 of 3"), ("3of3", "rules", "All 3 of 3"))
GATE_TOL = 1e-9                                                       # float tolerance of the reproduce gate
S_METRICS = (("rouge_l_f1", "ROUGE-L"), ("meteor", "METEOR"), ("number_overlap", "Number overlap"),
             ("semantic_similarity", "bge-m3 similarity"))
BLUE, ORANGE, BLACK, GREY = S457.OKABE["blue"], S457.OKABE["orange"], "#000000", S457.DOT_GREY
PT = S457.PT


class Refused(Exception):
    pass


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rband(v: float) -> int:
    return 0 if v < 3 else 1 if v < 4 else 2


def jband(v: int) -> int:
    return 0 if v <= 2 else 1 if v == 3 else 2


# ---------------------------------------------------------------- inputs

def read_inputs(s500=S500_RESULTS, boot=S500_BOOT, s508=S508_DIR, s509=S509_DIR) -> dict:
    s508, s509, boot = Path(s508), Path(s509), Path(boot)
    summ_f = s508 / "summary.json"
    if not summ_f.exists():
        raise Refused(f"S508's results are not there ({rel(summ_f)}): run S508 first (the 49 items judged on key v2.5, "
                      f"FD11 c). Nothing drawn")
    summ = json.loads(summ_f.read_text())
    if not summ.get("complete") or summ.get("key", {}).get("sha256") != S508.KEY25_SHA256:
        raise Refused(f"S508's results are not complete on key v2.5 ({summ.get('ok')} of {summ.get('items')} ok, key "
                      f"{str(summ.get('key', {}).get('sha256'))[:12]}). Nothing drawn")
    rc_ = summ.get("recheck") or {}
    if rc_.get("passed") is not True or rc_.get("after_complete") is not True:
        raise Refused(f"S508's recheck has not passed after all 49 items were judged ({summ.get('recheck')}): run "
                      f"S508 again (it rechecks; or --recheck-only). Nothing drawn")
    rows = {}
    for d in map(json.loads, filter(str.strip, (s508 / "rows.jsonl").read_text().splitlines())):
        if d.get("run_sha256") == summ["judge"]["run_sha256"]:
            rows[d["eval_id"]] = d                                  # the latest row of each item wins
    judge = {e: d["scores"] for e, d in rows.items() if d["status"] == "ok"
             and all(isinstance((d["scores"] or {}).get(k), int) for k in ("correctness", "faithfulness"))}
    if not Path(s500).exists():
        raise Refused(f"S500's results are not there ({rel(Path(s500))}): run S500 with --papers. Nothing drawn")
    res = json.loads(Path(s500).read_text())
    if not res["C_three_signals"].get("m_available"):
        raise Refused("S500 ran without --papers: no M for panel f (run S500 with --papers). Nothing drawn")
    per = res["per_item"]
    miss = [p["eval_id"] for p in per if p["eval_id"] not in judge]
    if miss:
        raise Refused(f"{len(miss)} analysed items have no ok S508 row (first {miss[0]}). Nothing drawn")
    if not (boot / "index.json").exists() or not (boot / "resamples.npz").exists():
        raise Refused(f"S500's resamples are not there ({rel(boot)}): run S500 at the FD10 version. Nothing drawn")
    idx = json.loads((boot / "index.json").read_text())
    z = np.load(boot / "resamples.npz")
    ids_ab, ids_c = idx["eval_ids_AB"], idx["eval_ids_C"]
    if ids_ab != [p["eval_id"] for p in per]:
        raise Refused("S500's resample order is not its per-item order. Nothing drawn")
    if ids_c != [p["eval_id"] for p in per if S08._finite(p.get("minicheck_papers_precision"))]:
        raise Refused("S500's part C order is not the items with an M value. Nothing drawn")
    for name, ids in (("draws_AB", ids_ab), ("draws_C", ids_c)):
        if not np.array_equal(z[name], np.array(S08.v22_draws(len(ids)))):
            raise Refused(f"S500's {name} are not S08.v22_draws({len(ids)}). Nothing drawn")
    if not (s509 / "rows.jsonl").exists():
        raise Refused(f"S509's rows are not there ({rel(s509)}): run S509 first. Nothing drawn")
    simple = {d["eval_id"]: d["signals"] for d in map(json.loads, filter(str.strip, (s509 / "rows.jsonl").read_text()
                                                                           .splitlines()))}
    if set(simple) != set(judge) or len(simple) != S508.N_ITEMS:
        raise Refused(f"S509's rows are not the 49 items S508 judged ({len(simple)} rows). Nothing drawn")
    files = [Path(s500), boot / "index.json", boot / "resamples.npz", summ_f, s508 / "rows.jsonl",
             s509 / "rows.jsonl", s509 / "header.json"]
    return {"per": per, "judge": judge, "draws_ab": z["draws_AB"], "draws_c": z["draws_C"], "ids_c": ids_c,
            "simple": simple, "s508_summary": summ, "s500": res,
            "inputs": {rel(f): sha(f) for f in files if f.exists()}}


def concept_recall_v25(per: list[dict]) -> tuple[dict, dict]:
    """Signal C under D181 on key v2.5: S505.recall_q(answer, concepts, question, "loose", "need", empty="b"), the
    answer text S500's concept_recall() reads (the master's generated_answer, S08.v22_read_content: no rating column),
    the concepts and question text of key v2.5 (sha256 pinned as S508's). None where every concept of the question is
    made only of question words (reading (b) leaves it out of the denominator): that item has no C."""
    import S505_question_aware_matcher as S505
    raw = S508.KEY25.read_bytes()
    if hashlib.sha256(raw).hexdigest() != S508.KEY25_SHA256:
        raise Refused(f"{S508.KEY25.name} is not amendment 9's key v2.5 (sha256). Nothing drawn")
    key = {q["id"]: q for q in json.loads(raw)["questions"]}
    _, master = S08.v22_read_content(S08.V22_MASTER)
    text = {x["eval_id"]: x["generated_answer"] for x in master}
    out = {}
    for p in per:
        e, qid = p["eval_id"], p["question_id"]
        if qid not in key or e not in text:
            raise Refused(f"{e}: {'no answer text in the master' if e not in text else qid + ' is not in key v2.5'}. "
                          f"Nothing drawn")
        q = key[qid]
        out[e] = S505.recall_q(text[e], list(q["expected_concepts"]), q["question"], "loose", "need", empty="b")
    prov = {"signal": "C", "label": C_LABEL, "decision": "D181 (experiments/README.md)",
            "matcher": 'scripts/S505_question_aware_matcher.py recall_q(answer, concepts, question, "loose", "need", '
                       'empty="b")', "key": rel(S508.KEY25), "key_sha256": S508.KEY25_SHA256,
            "answer_text": "S08.v22_read_content(S08.V22_MASTER) generated_answer, as S500.concept_recall() reads it",
            "question_text": "key v2.5's question", "pass_rule": f"C >= {C_PASS} (S500's PRIMARY c)",
            "none_rule": "a question whose concepts are all excluded under (b) gives no C: the item's C casts no vote "
                         "(it adds no pass vote to the rules at least 1, 2, 3 of 3) and leaves the C row's accuracy and "
                         "kappa and the McNemar test of 2 of 3 against C, which use the items with a C value",
            "items_without_c": sorted(e for e, v in out.items() if v is None),
            "s500_C_kept_for": "the reproduce gate only (D12's loose matcher on key v2.4, S471.score)"}
    return out, prov


def _close(a, b) -> bool:
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b)
                and all(_close(x, y) for x, y in zip(a, b)))
    if isinstance(a, (bool, np.bool_)) or isinstance(b, (bool, np.bool_)):
        return isinstance(a, (bool, np.bool_)) and isinstance(b, (bool, np.bool_)) and bool(a) == bool(b)
    if a is None or b is None:
        return a is None and b is None
    a, b = float(a), float(b)
    if np.isnan(a) or np.isnan(b):
        return bool(np.isnan(a) and np.isnan(b))
    return abs(a - b) <= GATE_TOL * (1 + abs(b))


def reproduce_s500(inp: dict) -> tuple[int, int, list[str]]:
    """README.md:75-79: before any new number, compute() on S500's own inputs (its per-item judge, S373's, and its old
    C, D12's loose matcher on key v2.4) and S500's saved draws must give S500's results.json: part A protocol items 2
    to 4 (rho with the judge, rho with MiniCheck, D, with intervals), part B weighted kappa, Spearman's rho and Cohen's
    kappa at bars 4 and 3 with intervals (correctness and faithfulness), part C at bars 4 and 3 (correctness verdict,
    C and M at 0.5): the rater's pass rate, accuracy and kappa with its interval of J, C, M and the three rules, the
    McNemar tests of 2 of 3 against J, C and M, and the 2-of-3 claim. Returns (equal, compared, names that differ)."""
    res, per = inp["s500"], inp["per"]
    R = compute({**inp, "judge": {p["eval_id"]: p["judge"] for p in per},
                 "concept": {p["eval_id"]: p["concept_recall_loose"] for p in per}})
    pairs = []
    A = res["A_protocol_items_r1"]["items2to4_r1_as_mean"]
    for ours, theirs in (("rho_rater_judge", "rho_human_judge"), ("rho_rater_minicheck", "rho_human_minicheck"),
                         ("D", "D")):
        pairs += [(f"A {theirs}", R["d"][ours]["point"], A[theirs]),
                  (f"A {theirs}_ci95", R["d"][ours]["ci95"], A[f"{theirs}_ci95"])]
    B = res["B_judge_trust_one_rater"]
    for dim in ("correctness", "faithfulness"):
        for ours, theirs in (("Weighted kappa", "qwk_0to5"), ("Spearman's rho", "spearman"),
                             ("Kappa, pass at 4", "kappa_pass_at_4"), ("Kappa, pass at 3", "kappa_pass_at_3")):
            ci = "qwk_ci95" if theirs == "qwk_0to5" else f"{theirs}_ci95"
            pairs += [(f"B {dim} {theirs}", R["e"][dim][ours]["point"], B[dim][theirs]),
                      (f"B {dim} {ci}", R["e"][dim][ours]["ci95"], B[dim][ci])]
    cells = res["C_three_signals"]["cells"]
    for label, jb, hb in SETTINGS:
        hit = [c for c in cells if c["verdict"] == "correctness" and c["human_bar"] == hb and c["judge_bar"] == jb
               and _close(c["c"], C_PASS) and _close(c["m"], M_PASS)]
        if len(hit) != 1:
            pairs.append((f"C {label}: S500 cell", None, len(hit)))
            continue
        c, f = hit[0], R["f"][label]
        pairs.append((f"C {label} rater pass rate", f["rater_pass_rate"], c["human_pass_rate"]))
        for k, grp in (("J", "signals"), ("C", "signals"), ("M", "signals"), ("1of3", "rules"), ("2of3", "rules"),
                       ("3of3", "rules")):
            pairs += [(f"C {label} {k} accuracy", f[k]["accuracy"]["point"], c[grp][k]["accuracy"]),
                      (f"C {label} {k} kappa", f[k]["kappa"]["point"], c[grp][k]["kappa"]),
                      (f"C {label} {k} kappa_ci95", f[k]["kappa"]["ci95"], c[grp][k]["kappa_ci95"])]
        for k in ("J", "C", "M"):
            for fld in ("rule_right_single_wrong", "rule_wrong_single_right", "p_two_sided", "favours_rule"):
                pairs.append((f"C {label} McNemar 2of3 vs {k} {fld}", f["mcnemar_2of3_vs"][k][fld],
                              c["mcnemar_2of3_vs"][k][fld]))
        pairs.append((f"C {label} claim_2of3_better_than_every_single", f["claim_2of3_better_than_every_single"],
                      c["claim_2of3_better_than_every_single"]))
    bad = [name for name, ours, theirs in pairs if not _close(ours, theirs)]
    return len(pairs) - len(bad), len(pairs), bad


# ---------------------------------------------------------------- statistics (S500's functions, S508's judge)

def per_draw(f, arrays, draws) -> np.ndarray:
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for idx in draws:
            v = f(*[x[idx] for x in arrays])
            out.append(float(v) if S08._finite(v) else np.nan)
    return np.array(out)


def summary_of(point, vals) -> dict:
    fin = vals[np.isfinite(vals)]
    q = (lambda p: float(np.percentile(fin, p))) if fin.size else (lambda p: float("nan"))
    return {"point": float(point), "ci95": S08._ci95(list(fin)), "q25": q(25), "median": q(50), "q75": q(75),
            "finite_resamples": int(fin.size), "resamples": vals}


def spearman_masked(a, b) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    return S08.v22_spearman(a[m], b[m])


def compute(inp: dict) -> dict:
    per, J, dab, dc = inp["per"], inp["judge"], inp["draws_ab"], inp["draws_c"]
    ids = [p["eval_id"] for p in per]
    hC = np.array([p["r1"]["correctness"] for p in per], int)
    hF = np.array([p["r1"]["faithfulness"] for p in per], int)
    jC = np.array([J[e]["correctness"] for e in ids], int)
    jF = np.array([J[e]["faithfulness"] for e in ids], int)
    mck = np.array([p["minicheck_key_precision"] for p in per], float)
    n = {"items": len(ids), "items_with_m": len(inp["ids_c"]), "resamples": int(len(dab))}
    grid = np.zeros((3, 3), int)                                     # [judge band][rater band]
    for h, j in zip(hC, jC):
        grid[jband(j), rband(h)] += 1
    bars = np.zeros((5, 6), int)                                     # [rater level 1..5][judge 0..5]
    for h, j in zip(hF, jF):
        bars[h - 1, j] += 1
    bands_c = {R_BANDS[b]: sorted(float(v) for v, h in zip(mck, hF) if rband(h) == b) for b in range(3)}
    d = {"rho_rater_judge": summary_of(S08.v22_spearman(hF, jF), per_draw(S08.v22_spearman, [hF, jF], dab)),
         "rho_rater_minicheck": summary_of(S08.v22_spearman(hF, mck), per_draw(S08.v22_spearman, [hF, mck], dab))}
    d["D"] = summary_of(d["rho_rater_judge"]["point"] - d["rho_rater_minicheck"]["point"],
                        d["rho_rater_judge"]["resamples"] - d["rho_rater_minicheck"]["resamples"])
    e = {}
    for dim, h, j in (("correctness", hC, jC), ("faithfulness", hF, jF)):
        e[dim] = {"Weighted kappa": summary_of(S500.qwk06(j, h), per_draw(S500.qwk06, [j, h], dab)),
                  "Spearman's rho": summary_of(S08.v22_spearman(h, j), per_draw(S08.v22_spearman, [h, j], dab))}
        for b in (4, 3):
            e[dim][f"Kappa, pass at {b}"] = summary_of(S500.kappa(j >= b, h >= b),
                                                       per_draw(S500.kappa, [j >= b, h >= b], dab))
    pc = {p["eval_id"]: p for p in per}
    cid = inp["ids_c"]
    cv = [inp["concept"][e] for e in cid]
    has = np.array([v is not None for v in cv], bool)               # D181 (b): an item with no C casts no C vote
    cr = np.array([np.nan if v is None else v for v in cv], float)
    mp = np.array([pc[e]["minicheck_papers_precision"] for e in cid], float)
    jc = np.array([J[e]["correctness"] for e in cid], int)
    hc = np.array([pc[e]["r1"]["correctness"] for e in cid], int)
    acc = lambda p_, t_: float(np.mean(p_ == t_)) if p_.size else float("nan")   # noqa: E731
    on_c = lambda fn: (lambda p_, t_, m_: fn(p_[m_], t_[m_]))             # noqa: E731  the items with a C value
    f = {}
    for label, jb, hb in SETTINGS:
        truth = hc >= hb
        sig = {"J": jc >= jb, "C": has & (np.nan_to_num(cr, nan=-1.0) >= C_PASS), "M": mp >= M_PASS}
        votes = sum(v.astype(int) for v in sig.values())
        pred = {**sig, **{f"{k}of3": votes >= k for k in (1, 2, 3)}}
        cell = {"judge_bar": jb, "rater_bar": hb, "c": C_PASS, "m": M_PASS, "rater_pass_rate": float(truth.mean()),
                "C_items": int(has.sum())}
        for k, pv in pred.items():
            if k == "C":
                cell[k] = {"accuracy": summary_of(on_c(acc)(pv, truth, has), per_draw(on_c(acc), [pv, truth, has], dc)),
                           "kappa": summary_of(on_c(S500.kappa)(pv, truth, has),
                                               per_draw(on_c(S500.kappa), [pv, truth, has], dc))}
            else:
                cell[k] = {"accuracy": summary_of(acc(pv, truth), per_draw(acc, [pv, truth], dc)),
                           "kappa": summary_of(S500.kappa(pv, truth), per_draw(S500.kappa, [pv, truth], dc))}
        ok2 = pred["2of3"] == truth
        cell["mcnemar_2of3_vs"] = {s: (S500.mcnemar(ok2[has], (sig[s] == truth)[has]) if s == "C"
                                       else S500.mcnemar(ok2, sig[s] == truth)) for s in sig}
        cell["claim_2of3_better_than_every_single"] = all(v["favours_rule"] for v in cell["mcnemar_2of3_vs"].values())
        f[label] = cell
    s = {"by_band": {}, "rho": {}}
    for key, lab in S_METRICS:
        v = np.array([np.nan if inp["simple"][e][key] is None else inp["simple"][e][key] for e in ids], float)
        s["by_band"][lab] = {R_BANDS[b]: sorted(float(x) for x, h in zip(v, hC) if rband(h) == b and np.isfinite(x))
                             for b in range(3)}
        s["rho"][lab] = {dim: summary_of(spearman_masked(h.astype(float), v),
                                         per_draw(spearman_masked, [h.astype(float), v], dab))
                         for dim, h in (("correctness", hC), ("faithfulness", hF))}
        s["rho"][lab]["null_items"] = int(np.sum(~np.isfinite(v)))
    s["rho"]["Judge (J)"] = {dim: e[dim]["Spearman's rho"] for dim in ("correctness", "faithfulness")}
    n["items_with_m_and_c"] = int(has.sum())
    return {"n": n, "a": {"grid_judge_by_rater": grid, "rater_bands": R_BANDS, "judge_bands": J_BANDS},
            "b": {"counts_rater_level_by_judge_score": bars}, "c": bands_c, "d": d, "e": e, "f": f, "s": s}


# ---------------------------------------------------------------- drawing helpers

def cividis(i: int) -> str:
    """Entry i (0 to 255) of [colour] continuous, as matplotlib's table holds it (S448 R5)."""
    from matplotlib import colormaps
    r, g, b = colormaps[S457.FLOCK["colour"]["continuous"]](int(i))[:3]
    return "#%02X%02X%02X" % (round(255 * r), round(255 * g), round(255 * b))


def lum(hexc: str) -> float:
    c = [int(hexc[k:k + 2], 16) / 255 for k in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def text_on(hexc: str) -> str:
    """Black or white, whichever stands out more from hexc (WCAG 2.1 ratio; S448 R11 asks 4.5)."""
    L = lum(hexc)
    return BLACK if (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) else "#FFFFFF"


class Panel:
    """One draft: a figure of W x H mm, axes placed in mm from the top left, the panel letter at the corner."""

    def __init__(self, pid: str, letter: str, W: float, H: float, note: str):
        import matplotlib.pyplot as plt
        self.pid, self.W, self.H, self.note = pid, W, H, note
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        self.fig.text(1.0 / W, 1 - 1.0 / H, letter, fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT,
                      va="top", ha="left")

    def ax(self, x, y, w, h):
        a = self.fig.add_axes([x / self.W, 1 - (y + h) / self.H, w / self.W, h / self.H])
        for s_ in ("top", "right"):
            a.spines[s_].set_visible(False)
        return a


def crowding(fig, W, H) -> list[str]:
    """S457.finish_plate's two text checks, reported instead of refused: a draft is for reading, not a plate."""
    from matplotlib.text import Text
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes, out = [], []
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text().strip():
            bb = t.get_window_extent(rend)
            x0, x1 = bb.x0 / fig.dpi * 25.4, bb.x1 / fig.dpi * 25.4
            y0, y1 = H - bb.y1 / fig.dpi * 25.4, H - bb.y0 / fig.dpi * 25.4
            if x0 < -0.01 or y0 < -0.01 or x1 > W + 0.01 or y1 > H + 0.01:
                out.append(f"past the page: {t.get_text()!r}")
            boxes.append((t.get_text(), x0, y0, x1, y1))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05 and a[2] < b[4] - 0.05 and b[2] < a[4] - 0.05:
                out.append(f"on each other: {a[0]!r} / {b[0]!r}")
    return out


def save(p: Panel, out: Path, log: dict) -> None:
    """As S457.finish_plate (no ligatures, no date or creator, the PNG the PDF rasterised by MuPDF), but a crowded
    text is listed in provenance.json, not a refusal."""
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    import fitz
    for t in p.fig.findobj(Text):
        t.set_fontfeatures(["-liga"])
    problems = crowding(p.fig, p.W, p.H)
    title = f"{TITLE}: draft {p.pid}"
    p.fig.savefig(out / f"{p.pid}.pdf", facecolor="#FFFFFF", metadata={"Title": title, "Author": None, "Subject": None,
                  "Keywords": None, "Creator": None, "Producer": None, "CreationDate": None, "ModDate": None})
    p.fig.savefig(out / f"{p.pid}.svg", facecolor="#FFFFFF", metadata={"Title": title, "Date": None, "Creator": None})
    plt.close(p.fig)
    pix = fitz.open(out / f"{p.pid}.pdf")[0].get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    pix.save(out / f"{p.pid}.png")
    log[p.pid] = {"note": p.note, "size_mm": [p.W, p.H], "text_problems": problems}


def box_row(ax, y, s, colour, h=0.28, horizontal=True):
    """A box of the resamples: quartiles, median line, whiskers to the 95% interval, the point estimate a diamond."""
    lo, hi = s["ci95"]
    if not np.isfinite(lo):
        return
    ax.plot([lo, s["q25"]], [y, y], color=colour, lw=0.6, solid_capstyle="butt")
    ax.plot([s["q75"], hi], [y, y], color=colour, lw=0.6, solid_capstyle="butt")
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((s["q25"], y - h / 2), s["q75"] - s["q25"], h, facecolor="#FFFFFF", edgecolor=colour,
                           lw=0.6))
    ax.plot([s["median"]] * 2, [y - h / 2, y + h / 2], color=colour, lw=1.0, solid_capstyle="butt")
    ax.plot([s["point"]], [y], marker="D", ms=2.4, color=BLACK, mew=0, ls="none", zorder=5)


def ticks_in(lo, hi, step):
    """Explicit ticks inside the view, so no tick label of a tick outside it is laid out (a text past the page)."""
    first = np.ceil(lo / step - 1e-9) * step
    return [round(float(v), 6) for v in np.arange(first, hi + 1e-9, step)]


def interval_row(ax, y, s, colour):
    lo, hi = s["ci95"]
    if np.isfinite(lo):
        ax.plot([lo, hi], [y, y], color=colour, lw=1.0, solid_capstyle="butt")
    ax.plot([s["point"]], [y], "o", ms=3.0, color=colour, mew=0)


def strip(ax, x0, vals, horizontal=False, width=0.6):
    """Dots of one group placed apart across the group (never along the value axis) and its median line."""
    k = len(vals)
    if not k:
        return
    offs = [(i - (k - 1) / 2) * min(0.08, width / max(k, 1)) for i in range(k)]
    med = float(np.median(vals))
    if horizontal:
        ax.plot(vals, [x0 + o for o in offs], "o", ms=2.2, color=GREY, mew=0, zorder=2)
        ax.plot([med, med], [x0 - 0.3, x0 + 0.3], color=BLACK, lw=1.0, zorder=3)
    else:
        ax.plot([x0 + o for o in offs], vals, "o", ms=2.2, color=GREY, mew=0, zorder=2)
        ax.plot([x0 - 0.3, x0 + 0.3], [med, med], color=BLACK, lw=1.0, zorder=3)


# ---------------------------------------------------------------- the drafts

def draw_a(R, out, log):
    from matplotlib.patches import Rectangle as Rect
    g = R["a"]["grid_judge_by_rater"]
    mx = max(int(g.max()), 1)
    # a1: heat grid, cividis (yellow = more answers), counts in each cell, agreeing cells outlined
    p = Panel("a1", "a", 60, 52, "3 x 3 grid of counts, cell colour by count (yellow more), agreeing bands outlined")
    ax = p.ax(16, 5, 38, 36)
    for jb in range(3):
        for rb in range(3):
            col = cividis(round(255 * g[jb, rb] / mx))
            ax.add_patch(Rect((rb, jb), 1, 1, facecolor=col, edgecolor="#FFFFFF", lw=1.0))
            ax.text(rb + 0.5, jb + 0.5, str(g[jb, rb]), ha="center", va="center", color=text_on(col), fontsize=PT)
    for k in range(3):
        ax.add_patch(Rect((k, k), 1, 1, fill=False, edgecolor=BLACK, lw=1.0))
    ax.set_xlim(0, 3), ax.set_ylim(0, 3)
    ax.set_xticks([0.5, 1.5, 2.5], R_BANDS), ax.set_yticks([0.5, 1.5, 2.5], J_BANDS)
    ax.set_xlabel("Rater correctness"), ax.set_ylabel("Judge correctness")
    save(p, out, log)
    # a2: plain counts with row and column totals, agreeing cells shaded grey
    p = Panel("a2", "a", 60, 54, "3 x 3 counts with row and column totals, agreeing cells shaded, no colour scale")
    ax = p.ax(16, 8, 36, 34)
    for jb in range(3):
        for rb in range(3):
            ax.add_patch(Rect((rb, jb), 1, 1, facecolor="#E6E6E6" if jb == rb else "#FFFFFF", edgecolor=GREY, lw=0.5))
            ax.text(rb + 0.5, jb + 0.5, str(g[jb, rb]), ha="center", va="center", fontsize=PT)
        ax.text(3.25, jb + 0.5, str(g[jb].sum()), ha="left", va="center", fontsize=PT, color="#595959")
    for rb in range(3):
        ax.text(rb + 0.5, 3.2, str(g[:, rb].sum()), ha="center", va="bottom", fontsize=PT, color="#595959")
    ax.set_xlim(0, 3), ax.set_ylim(0, 3)
    ax.set_xticks([0.5, 1.5, 2.5], R_BANDS), ax.set_yticks([0.5, 1.5, 2.5], J_BANDS)
    ax.set_xlabel("Rater correctness"), ax.set_ylabel("Judge correctness")
    save(p, out, log)
    # a3: circles, area by count (S501's form), in bands
    p = Panel("a3", "a", 60, 52, "3 x 3 circles, area by count, count printed; the diagonal a grey guide")
    ax = p.ax(16, 5, 38, 36)
    ax.plot([-0.5, 2.5], [-0.5, 2.5], color=GREY, lw=0.5, zorder=1)
    for jb in range(3):
        for rb in range(3):
            if g[jb, rb]:
                ax.scatter([rb], [jb], s=40 + 420 * g[jb, rb] / mx, color="#BFDCEF", edgecolors=BLUE, linewidths=0.6,
                           zorder=2)
                ax.text(rb, jb, str(g[jb, rb]), ha="center", va="center", fontsize=PT, zorder=3)
    ax.set_xlim(-0.6, 2.6), ax.set_ylim(-0.6, 2.6)
    ax.set_xticks([0, 1, 2], R_BANDS), ax.set_yticks([0, 1, 2], J_BANDS)
    ax.set_xlabel("Rater correctness"), ax.set_ylabel("Judge correctness")
    save(p, out, log)


def draw_b(R, out, log):
    c = R["b"]["counts_rater_level_by_judge_score"]
    from matplotlib.patches import Rectangle as Rect
    cols = [cividis(round(255 * k / 5)) for k in range(6)]          # judge 0 dark blue ... 5 yellow (D171 (1))

    def key(ax, x, y, labels, colours, title):
        ax.text(x, y, title, transform=ax.transAxes, fontsize=PT, va="bottom")
        for k, (lab, colr) in enumerate(zip(labels, colours)):
            yy = y - 0.11 * (k + 1)
            ax.add_patch(Rect((x, yy), 0.06, 0.08, transform=ax.transAxes, facecolor=colr, edgecolor="none",
                              clip_on=False))
            ax.text(x + 0.09, yy + 0.04, lab, transform=ax.transAxes, fontsize=PT, va="center")

    for pid, horizontal in (("b1", False), ("b2", True)):
        p = Panel(pid, "b", 76 if horizontal else 66, 52, ("100% bars, one per rater level, judge score 0 to 5 stacked (yellow higher), n "
                                     "above" if not horizontal else "the same as horizontal bars, rater 5 on top"))
        ax = p.ax(14, 5, 36, 36)
        for lv in range(5):
            tot = c[lv].sum()
            start = 0.0
            for j in range(6):
                share = 100 * c[lv, j] / tot if tot else 0
                if share:
                    if horizontal:
                        ax.barh(lv + 1, share, left=start, height=0.7, color=cols[j], edgecolor="#FFFFFF", lw=0.3)
                    else:
                        ax.bar(lv + 1, share, bottom=start, width=0.7, color=cols[j], edgecolor="#FFFFFF", lw=0.3)
                start += share
            if horizontal:
                ax.text(102, lv + 1, f"n = {tot}", va="center", fontsize=PT)
            else:
                ax.text(lv + 1, 102, str(tot), ha="center", va="bottom", fontsize=PT)
        if horizontal:
            ax.set_xlim(0, 100), ax.set_ylim(0.4, 5.6), ax.set_yticks(range(1, 6))
            ax.set_ylabel("Raters"), ax.set_xlabel("Share of answers (%)")
        else:
            ax.set_ylim(0, 100), ax.set_xlim(0.4, 5.6), ax.set_xticks(range(1, 6))
            ax.set_xlabel("Raters"), ax.set_ylabel("Share of answers (%)")
        key(ax, 1.34 if horizontal else 1.04, 0.95, [str(k) for k in range(6)], cols, "Judge")
        if horizontal:
            ax.set_xticks([0, 25, 50, 75, 100])
        else:
            ax.set_yticks([0, 20, 40, 60, 80, 100])
        save(p, out, log)
    # b3: bands on both sides (D171 (2)), the share printed in each segment
    p = Panel("b3", "b", 62, 52, "bands both sides: rater 1-2, 3, 4-5; judge 0-2, 3, 4-5 (3 colours), % in segments")
    ax = p.ax(14, 5, 34, 36)
    bc = [cividis(0), cividis(128), cividis(255)]
    rows = [c[0] + c[1], c[2], c[3] + c[4]]
    for b, r in enumerate(rows):
        jb = [r[0] + r[1] + r[2], r[3], r[4] + r[5]]
        tot, start = sum(jb), 0.0
        for k in range(3):
            share = 100 * jb[k] / tot if tot else 0
            if share:
                ax.bar(b, share, bottom=start, width=0.7, color=bc[k], edgecolor="#FFFFFF", lw=0.3)
                if share >= 9:
                    ax.text(b, start + share / 2, f"{share:.0f}", ha="center", va="center", fontsize=PT,
                            color=text_on(bc[k]))
            start += share
        ax.text(b, 102, str(tot), ha="center", va="bottom", fontsize=PT)
    ax.set_ylim(0, 100), ax.set_xlim(-0.6, 2.6), ax.set_xticks(range(3), R_BANDS)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("Raters"), ax.set_ylabel("Share of answers (%)")
    key(ax, 1.05, 0.95, list(J_BANDS), bc, "Judge")
    save(p, out, log)


def draw_c(R, out, log):
    bands = R["c"]
    p = Panel("c1", "c", 56, 52, "dots per item by rater faithfulness band, the band's median a black line")
    ax = p.ax(14, 5, 38, 36)
    for b, lab in enumerate(R_BANDS):
        strip(ax, b, bands[lab])
    ax.set_xlim(-0.6, 2.6), ax.set_ylim(-0.04, 1.04), ax.set_xticks(range(3), R_BANDS)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("Rater faithfulness"), ax.set_ylabel("MiniCheck precision (key)")
    save(p, out, log)
    p = Panel("c2", "c", 56, 52, "box plots (Tukey whiskers) with every item's dot")
    ax = p.ax(14, 5, 38, 36)
    for b, lab in enumerate(R_BANDS):
        v = bands[lab]
        if v:
            ax.boxplot([v], positions=[b], widths=0.5, whis=1.5, showfliers=False, medianprops={"color": BLACK,
                       "lw": 1.0}, boxprops={"lw": 0.6}, whiskerprops={"lw": 0.6}, capprops={"lw": 0.6})
            strip(ax, b, v, width=0.4)
    ax.set_xlim(-0.6, 2.6), ax.set_ylim(-0.04, 1.04), ax.set_xticks(range(3), R_BANDS)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("Rater faithfulness"), ax.set_ylabel("MiniCheck precision (key)")
    save(p, out, log)
    p = Panel("c3", "c", 70, 40, "horizontal: one row per band, dots and the median, n beside")
    ax = p.ax(18, 4, 40, 24)
    for b, lab in enumerate(R_BANDS):
        strip(ax, b, bands[lab], horizontal=True)
        ax.text(1.06, b, f"n = {len(bands[lab])}", va="center", fontsize=PT)
    ax.set_ylim(-0.6, 2.6), ax.set_xlim(-0.04, 1.04), ax.set_yticks(range(3), R_BANDS)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Rater faithfulness"), ax.set_xlabel("MiniCheck precision (key)")
    save(p, out, log)


def draw_d(R, out, log):
    d = R["d"]
    x, y = d["rho_rater_minicheck"]["resamples"], d["rho_rater_judge"]["resamples"]
    m = np.isfinite(x) & np.isfinite(y)
    lo = float(min(np.nanmin(x), np.nanmin(y), 0.0)) - 0.05
    hi = float(max(np.nanmax(x), np.nanmax(y))) + 0.05
    p = Panel("d1", "d", 58, 56, "the 2,000 resamples as dots, the diagonal, the estimate in blue")
    ax = p.ax(15, 5, 38, 38)
    ax.plot(x[m], y[m], "o", ms=0.9, color=GREY, mew=0, zorder=1)
    ax.plot([lo, hi], [lo, hi], color=BLACK, lw=0.5, zorder=2)
    ax.plot([d["rho_rater_minicheck"]["point"]], [d["rho_rater_judge"]["point"]], "o", ms=3.5, color=BLUE, mew=0,
            zorder=3)
    ax.set_xlim(lo, hi), ax.set_ylim(lo, hi), ax.set_aspect("equal")
    ax.set_xticks(ticks_in(lo, hi, 0.5)), ax.set_yticks(ticks_in(lo, hi, 0.5))
    ax.set_xlabel("Rater with MiniCheck (rho)"), ax.set_ylabel("Rater with judge (rho)")
    save(p, out, log)
    p = Panel("d2", "d", 70, 56, "the same cloud as a density (hexagons, yellow more resamples), diagonal, estimate")
    ax = p.ax(15, 5, 38, 38)
    from matplotlib.colors import ListedColormap
    from matplotlib.ticker import MaxNLocator
    hb = ax.hexbin(x[m], y[m], gridsize=18, cmap=ListedColormap([cividis(i) for i in range(256)]), mincnt=1,
                   linewidths=0.0, extent=(lo, hi, lo, hi))
    ax.plot([lo, hi], [lo, hi], color=BLACK, lw=0.5)
    ax.plot([d["rho_rater_minicheck"]["point"]], [d["rho_rater_judge"]["point"]], "o", ms=3.5, color=S457.OKABE[
        "vermillion"], mew=0)
    ax.set_xlim(lo, hi), ax.set_ylim(lo, hi), ax.set_aspect("equal")
    ax.set_xticks(ticks_in(lo, hi, 0.5)), ax.set_yticks(ticks_in(lo, hi, 0.5))
    ax.set_xlabel("Rater with MiniCheck (rho)"), ax.set_ylabel("Rater with judge (rho)")
    cax = p.ax(56, 8, 2, 30)
    cb = p.fig.colorbar(hb, cax=cax)
    cb.outline.set_linewidth(0.5)
    cb.set_label("Resamples")
    cb.locator = MaxNLocator(4, integer=True)
    cb.update_ticks()
    save(p, out, log)
    p = Panel("d3", "d", 60, 46, "the difference D per resample (protocol item 4), zero line, estimate and 95% interval")
    ax = p.ax(14, 5, 42, 28)
    D = d["D"]["resamples"][np.isfinite(d["D"]["resamples"])]
    ax.hist(D, bins=30, color="#BFDCEF", edgecolor=BLUE, lw=0.4)
    ax.axvline(0, color=BLACK, lw=0.5)
    for v in d["D"]["ci95"]:
        ax.axvline(v, color=GREY, lw=0.6, ls=(0, (3, 2)))
    ax.axvline(d["D"]["point"], color=BLUE, lw=1.0)
    lo_d, hi_d = float(D.min()), float(D.max())
    ax.set_xlim(lo_d - 0.05, hi_d + 0.05), ax.set_xticks(ticks_in(lo_d - 0.05, hi_d + 0.05, 0.5))
    ax.set_xlabel("D, judge minus MiniCheck (rho)"), ax.set_ylabel("Resamples")
    ax.set_yticks(ticks_in(0, ax.get_ylim()[1], 100 if ax.get_ylim()[1] > 150 else 50))
    save(p, out, log)


E_STATS = ("Weighted kappa", "Spearman's rho", "Kappa, pass at 4", "Kappa, pass at 3")


def draw_e(R, out, log):
    e = R["e"]
    p = Panel("e1", "e", 96, 56, "one axis: each statistic a pair of boxes (correctness blue, faithfulness orange)")
    ax = p.ax(30, 5, 60, 38)
    for i, st in enumerate(E_STATS):
        y = len(E_STATS) - 1 - i
        box_row(ax, y + 0.17, e["correctness"][st], BLUE)
        box_row(ax, y - 0.17, e["faithfulness"][st], ORANGE)
    ax.axvline(0, color=BLACK, lw=0.5), ax.axvline(0.6, color=GREY, lw=0.6, ls=(0, (3, 2)))
    ax.set_yticks(range(len(E_STATS)), list(E_STATS)[::-1]), ax.set_ylim(-0.6, len(E_STATS) - 0.4)
    ax.set_xlim(-0.4, 1.0), ax.set_xticks([-0.4, 0, 0.4, 0.8]), ax.set_xlabel("Agreement, judge with rater")
    ax.plot([], [], "s", ms=3, mfc="#FFFFFF", mec=BLUE, label="Correctness")
    ax.plot([], [], "s", ms=3, mfc="#FFFFFF", mec=ORANGE, label="Faithfulness")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, borderaxespad=0.2)
    save(p, out, log)
    p = Panel("e2", "e", 120, 50, "two columns side by side, correctness and faithfulness, one box per statistic")
    for k, (dim, col) in enumerate((("correctness", BLUE), ("faithfulness", ORANGE))):
        ax = p.ax(30 + 48 * k, 8, 40, 30)
        for i, st in enumerate(E_STATS):
            box_row(ax, len(E_STATS) - 1 - i, e[dim][st], col, h=0.4)
        ax.axvline(0, color=BLACK, lw=0.5), ax.axvline(0.6, color=GREY, lw=0.6, ls=(0, (3, 2)))
        ax.set_yticks(range(len(E_STATS)), list(E_STATS)[::-1] if k == 0 else [""] * len(E_STATS))
        ax.set_ylim(-0.6, len(E_STATS) - 0.4), ax.set_xlim(-0.4, 1.0), ax.set_xticks([-0.4, 0, 0.4, 0.8])
        ax.set_xlabel("Agreement, judge with rater")
        ax.text(0.0, 1.03, dim.capitalize(), transform=ax.transAxes, fontsize=PT, va="bottom")
    save(p, out, log)
    p = Panel("e3", "e", 96, 56, "the estimate and its 95% interval only (no box), for comparison with e1")
    ax = p.ax(30, 5, 60, 38)
    for i, st in enumerate(E_STATS):
        y = len(E_STATS) - 1 - i
        interval_row(ax, y + 0.15, e["correctness"][st], BLUE)
        interval_row(ax, y - 0.15, e["faithfulness"][st], ORANGE)
    ax.axvline(0, color=BLACK, lw=0.5), ax.axvline(0.6, color=GREY, lw=0.6, ls=(0, (3, 2)))
    ax.set_yticks(range(len(E_STATS)), list(E_STATS)[::-1]), ax.set_ylim(-0.6, len(E_STATS) - 0.4)
    ax.set_xlim(-0.4, 1.0), ax.set_xticks([-0.4, 0, 0.4, 0.8]), ax.set_xlabel("Agreement, judge with rater")
    ax.plot([], [], "o", ms=3, color=BLUE, label="Correctness")
    ax.plot([], [], "o", ms=3, color=ORANGE, label="Faithfulness")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, borderaxespad=0.2)
    save(p, out, log)


def p_text(v: float) -> str:
    return "P < 0.001" if v < 0.001 else f"P = {v:.2f}" if v >= 0.01 else f"P = {v:.3f}"


def draw_f(R, out, log):
    f = R["f"]
    ys = [5.5, 4.5, 3.5, 2.0, 1.0, 0.0]
    labels = [r[2] for r in F_ROWS]
    cols = {"bar 4": BLUE, "bar 3": ORANGE}

    def column(ax, stat, settings, xlim, xlab, show_labels, dy=0.17):
        for j, s_ in enumerate(settings):
            off = dy * (len(settings) - 1) / 2 - dy * j
            for y, (k, _, _) in zip(ys, F_ROWS):
                interval_row(ax, y + off, f[s_][k][stat], cols[s_])
        ax.axvline(0 if stat == "kappa" else 0.5, color=BLACK if stat == "kappa" else GREY, lw=0.5,
                   ls="-" if stat == "kappa" else (0, (3, 2)))
        ax.set_yticks(ys, labels if show_labels else [""] * len(ys))
        ax.set_ylim(-0.6, 6.1), ax.set_xlim(*xlim), ax.set_xlabel(xlab)
        ax.set_xticks([0.4, 0.6, 0.8, 1.0] if stat == "accuracy" else [0, 0.5, 1.0])

    def legend(ax):
        for s_ in ("bar 4", "bar 3"):
            ax.plot([], [], "o", ms=3, color=cols[s_], label=f"Pass at {s_[-1]}")
        ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, borderaxespad=0.2)

    # f1: accuracy | kappa, both bars in each, McNemar P beside J, C and M in the accuracy column
    p = Panel("f1", "f", 176, 58, "accuracy and kappa columns, bars 4 and 3 paired; McNemar P of 2 of 3 against J, C, M")
    a1, a2 = p.ax(54, 8, 38, 40), p.ax(126, 8, 42, 40)          # left margin for the C and M labels (D181)
    column(a1, "accuracy", ("bar 4", "bar 3"), (0.2, 1.0), "Accuracy, signal or rule with rater", True)
    column(a2, "kappa", ("bar 4", "bar 3"), (-0.3, 1.0), "Cohen's kappa, signal or rule with rater", False)
    for y, (k, _, _) in zip(ys[:3], F_ROWS[:3]):
        a1.text(1.04, y, " / ".join(p_text(f[s_]["mcnemar_2of3_vs"][k]["p_two_sided"]) for s_ in ("bar 4", "bar 3")),
                transform=a1.get_yaxis_transform(), fontsize=PT, va="center")
    a1.text(1.04, 6.1, "2 of 3 against it", transform=a1.get_yaxis_transform(), fontsize=PT, va="bottom")
    legend(a2)
    save(p, out, log)
    # f2: one block per bar, accuracy and kappa in each block
    p = Panel("f2", "f", 176, 62, "one block per pass bar (4 left, 3 right), accuracy and kappa side by side in each")
    for b, s_ in enumerate(("bar 4", "bar 3")):
        ax1, ax2 = p.ax(54 + 62 * b, 10, 26, 42), p.ax(84 + 62 * b, 10, 26, 42)
        column(ax1, "accuracy", (s_,), (0.2, 1.0), "Accuracy", b == 0)
        column(ax2, "kappa", (s_,), (-0.3, 1.0), "Cohen's kappa", False)
        ax1.text(0.0, 1.03, f"Pass at {s_[-1]}", transform=ax1.transAxes, fontsize=PT, va="bottom")
    save(p, out, log)
    # f3: accuracy | McNemar table | kappa
    p = Panel("f3", "f", 176, 70, "accuracy, then the McNemar table (2 of 3 right and the signal wrong, the reverse, P), "
                                  "then kappa")
    a1, a3 = p.ax(54, 8, 36, 52), p.ax(134, 8, 38, 52)
    column(a1, "accuracy", ("bar 4", "bar 3"), (0.2, 1.0), "Accuracy", True)
    column(a3, "kappa", ("bar 4", "bar 3"), (-0.3, 1.0), "Cohen's kappa", False)
    legend(a1)
    t = p.ax(98, 8, 34, 52)
    t.axis("off")
    t.set_xlim(0, 1), t.set_ylim(-0.6, 6.1)
    t.text(0.5, 6.3, "2 of 3 against", ha="center", va="bottom", fontsize=PT)
    for j, s_ in enumerate(("bar 4", "bar 3")):
        for y, (k, _, _) in zip(ys[:3], F_ROWS[:3]):
            mc = f[s_]["mcnemar_2of3_vs"][k]
            t.text(0.5, y + (0.22 if j == 0 else -0.22),
                   f"{s_}: {mc['rule_right_single_wrong']} vs {mc['rule_wrong_single_right']}, "
                   f"{p_text(mc['p_two_sided'])}",
                   ha="center", va="center", fontsize=PT)
    save(p, out, log)


def draw_s(R, out, log):
    s = R["s"]
    p = Panel("s1", "s", 170, 46, "each simple evaluator per item by rater correctness band, the band's median")
    for k, (_, lab) in enumerate(S_METRICS):
        ax = p.ax(14 + 40 * k, 8, 30, 28)
        for b, band in enumerate(R_BANDS):
            strip(ax, b, s["by_band"][lab][band])
        ax.set_xlim(-0.6, 2.6), ax.set_ylim(-0.04, 1.04), ax.set_xticks(range(3), R_BANDS)
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_xlabel("Rater correctness")
        ax.text(0.0, 1.04, lab, transform=ax.transAxes, fontsize=PT, va="bottom")
        if k == 0:
            ax.set_ylabel("Score")
    save(p, out, log)
    rows = [lab for _, lab in S_METRICS] + ["Judge (J)"]
    p = Panel("s2", "s", 96, 56, "Spearman's rho of each evaluator with the rater, boxes of the resamples; the judge "
                                 "for reference")
    ax = p.ax(30, 6, 60, 40)
    for i, lab in enumerate(rows):
        y = len(rows) - 1 - i
        box_row(ax, y + 0.17, s["rho"][lab]["correctness"], BLUE)
        box_row(ax, y - 0.17, s["rho"][lab]["faithfulness"], ORANGE)
    ax.axvline(0, color=BLACK, lw=0.5)
    ax.set_yticks(range(len(rows)), rows[::-1]), ax.set_ylim(-0.6, len(rows) - 0.4), ax.set_xlim(-0.6, 1.0)
    ax.set_xticks([-0.5, 0, 0.5, 1.0])
    ax.set_xlabel("Spearman's rho with the rater")
    ax.plot([], [], "s", ms=3, mfc="#FFFFFF", mec=BLUE, label="Correctness")
    ax.plot([], [], "s", ms=3, mfc="#FFFFFF", mec=ORANGE, label="Faithfulness")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, borderaxespad=0.2)
    save(p, out, log)


def contact_sheet(out: Path, log: dict) -> None:
    """Every draft on one page, at reduced size, each with its id and what it shows (a review aid, not a plate)."""
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    ids = list(log)
    cols = 3
    rows = -(-len(ids) // cols)
    fig = plt.figure(figsize=(16.5, 4.0 * rows + 0.8))
    fig.text(0.01, 1 - 0.25 / (4.0 * rows + 0.8), f"{TITLE}: panel drafts (early look, one rater; D168, D183)",
             fontsize=11, va="top")
    for k, pid in enumerate(ids):
        r_, c_ = divmod(k, cols)
        ax = fig.add_axes([0.01 + c_ / cols, 1 - (0.8 + 4.0 * (r_ + 1)) / (4.0 * rows + 0.8) + 0.02,
                           1 / cols - 0.02, 3.3 / (4.0 * rows + 0.8)])
        ax.imshow(mpimg.imread(out / f"{pid}.png"))
        ax.axis("off")
        warn = " (text crowded: see provenance.json)" if log[pid]["text_problems"] else ""
        ax.set_title(f"{pid}: {log[pid]['note']}{warn}", fontsize=7, loc="left", wrap=True)
    fig.savefig(out / "contact_sheet.png", dpi=110, facecolor="#FFFFFF")
    fig.savefig(out / "contact_sheet.pdf", facecolor="#FFFFFF", metadata={"Creator": None, "Producer": None,
                                                                          "CreationDate": None})
    plt.close(fig)


LEGEND = f"""# {TITLE}

Draft legend (D183 FD8 a: a neutral title until the second rater's packet is back). No number is written here.

**a**, Correctness: the rater's score in bands 1-2, 3 and 4-5 against the judge's score in bands 0-2, 3 and 4-5, one
cell per pair of bands, the number of answers in each. **b**, Faithfulness: the judge's score (0 to 5) for the answers
at each rater score, as shares of those answers. **c**, MiniCheck precision against the expert answer for each answer,
by the rater's faithfulness band, with each band's median. **d**, Each bootstrap resample of the answers (2,000, seed
42): Spearman's rho of the rater's faithfulness with the judge's against that with MiniCheck's. **e**, Agreement of
the judge with the rater (weighted kappa on 0 to 5, Spearman's rho, Cohen's kappa on pass at 4 and at 3) over the
resamples: box, the middle half; line, the median; whiskers, the 95% percentile interval; diamond, the estimate on all
answers; dashed line, kappa 0.6 (a reference only). **f**, The judge (J, correctness at the bar), concept recall (C,
key v2.5, D181 rule: the loose matcher less the question's own words, a concept made only of question words left out;
at 0.5; an answer whose every concept is left out has no C and casts no C vote), MiniCheck against the source papers
without the source-list filter (M, at 0.5) and the rules at least 1, 2 and 3 of 3, against the rater's
correctness at the same bar: accuracy, and Cohen's kappa, with 95% percentile intervals over the resamples; exact
two-sided McNemar tests of 2 of 3 against each signal. One rater; every panel is descriptive (protocol amendment 8).
The judge is the lock's call on key v2.5 (FD11 c). n = (filled from numbers.json when the plate is built).

**Supplementary (FD12 a, exploratory, added after the early look)**: ROUGE-L, METEOR, number overlap and bge-m3
similarity of each answer against the expert answer, by the rater's band, and their Spearman's rho with the rater.
"""


def jsonable(o):
    if isinstance(o, np.ndarray):
        return [None if (isinstance(v, float) and not np.isfinite(v)) else v for v in o.tolist()]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    raise TypeError(type(o))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--s500", type=Path, default=S500_RESULTS)
    ap.add_argument("--s500-boot", type=Path, default=S500_BOOT)
    ap.add_argument("--s508", type=Path, default=S508_DIR)
    ap.add_argument("--s509", type=Path, default=S509_DIR)
    a = ap.parse_args(argv)
    try:
        inp = read_inputs(a.s500, a.s500_boot, a.s508, a.s509)
        eq, n_cmp, bad = reproduce_s500(inp)                   # README.md:75-79, before any new number
        print(f"S510: S500 reproduced {eq} of {n_cmp}", flush=True)
        if bad:
            raise Refused(f"S500's results.json is not reproduced from its own inputs and draws ({len(bad)} differ, "
                          f"first: {', '.join(bad[:5])}). Nothing drawn, nothing written")
        inp["concept"], c_prov = concept_recall_v25(inp["per"])
    except Refused as e:
        print(f"S510 REFUSED: {e}")
        return 1
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(S457.plate_rc("S510"))
    R = compute(inp)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    log: dict = {}
    for fn in (draw_a, draw_b, draw_c, draw_d, draw_e, draw_f, draw_s):
        fn(R, out, log)
    contact_sheet(out, log)
    (out / "numbers.json").write_text(json.dumps({"labels": {"C": C_LABEL, "M": M_LABEL}, "n": R["n"],
                                                  **{k: R[k] for k in "abcdefs"},
                                                  "C_per_item": {e: inp["concept"][e] for e in inp["ids_c"]}},
                                                 default=jsonable, indent=1) + "\n")
    (out / "legend_draft.md").write_text(LEGEND)
    (out / "provenance.json").write_text(json.dumps({
        "script": SCRIPT, "script_sha256": sha(ROOT / SCRIPT), "command": "uv run --frozen python " + " ".join(
            [SCRIPT] + list(sys.argv[1:] if argv is None else argv)), "inputs": inp["inputs"],
        "figure_lock_sha256": sha(S457.FIGURE_LOCK), "title": TITLE, "drafts": log,
        "judge": "S508: the lock's plain call on key v2.5 (FD11 c)", "s508_run_sha256":
        inp["s508_summary"]["judge"]["run_sha256"], "C": c_prov,
        "M": {"label": M_LABEL, "source": "S500 per_item minicheck_papers_precision (S498, without the D172 "
              "source-list filter)", "pass_rule": f"M >= {M_PASS} (S500's PRIMARY m)"},
        "reproduce_gate": {"rule": "README.md:75-79", "compared": n_cmp, "equal": eq, "tolerance": GATE_TOL,
                           "what": "compute() on S500's per-item judge (S373) and old C with S500's saved draws "
                                   "against S500's results.json (reproduce_s500)"}}, indent=1) + "\n")
    crowded = [k for k, v in log.items() if v["text_problems"]]
    print(f"S510: {len(log)} drafts ({', '.join(log)}) and a contact sheet in {rel(out)}"
          + (f"; text crowded on {', '.join(crowded)} (listed in provenance.json)" if crowded else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
