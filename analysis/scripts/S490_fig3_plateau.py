"""S490: Supplementary Figure 8's plateau numbers, recomputed from its committed rows (inventory A14, F13; D155).

One command, from the repository root:
    uv run python scripts/S490_fig3_plateau.py            reproduce, then write
    uv run python scripts/S490_fig3_plateau.py --check    reproduce, then compare with the committed output only

Promoted from the 25 October scratch drafts fig3_alt/prep.py (its Source Data gate and its plateau rules) and
audit_1025/fig3/recompute.py (the same text at caps 20 and 50). Reads only committed files:
    findings/recompute/L2/concept_recall.jsonl       panel a (S474's L2 rows: Mentori's RLM G5, the authors' package G6);
                                                     L2_d135/concept_recall.jsonl in its place once it exists (D160
                                                     Q23: G6 after the D135 reruns, the rows Supplementary Figure 8a then draws)
                                                     D186 (4): the D181 reading the plate's supplementary_figure8_provenance.json
                                                     (read from the working tree when this module is imported)
                                                     names under "l2_d181" "drawn" (L2_d135_d181/, its value
                                                     concept_recall) in their place once the plate draws it
    findings/recompute/T1_L2/concept_recall.jsonl    panel b (T1's four local models), the v2.4 loose reading
    findings/recompute/T1_L2/cap_tables.json         panel b's caps, models and complete questions
                                                     D188: when the plate's supplementary_figure8_provenance.json names "t1_d181"
                                                     (T1_L2_d181/, D181's reading on key v2.5, its value
                                                     concept_recall), b is reproduced from that folder's rows and
                                                     tables, the rows the plate then draws
    findings/recompute/G4_fig3c/pairs.jsonl          panel c (G4 draw 1, RLM-10 and single pass per index and question)
                                                     D188: when the provenance names "g4_d185" (G4_fig3c_d185/, key
                                                     v2.5 judge rows where S6 has judged), c is reproduced from its
                                                     grid_pairs.jsonl, the rows the plate then draws
    findings/recompute/G4_fig3c/grid_tables.json     the v2.4 anchor of c (below)
    findings/figures_provisional/supp_fig8_depth/Supplementary Figure 8 data (provisional, ...).xlsx   the plate's numbers

REPRODUCE FIRST. D188: the v2.4 readings first, whatever the plate draws: T1_L2's cap_tables.json (each model and
cap's mean of concept_recall_loose over the complete questions, questions, failed, cap-reached and stopped-by-cap
counts) recomputed from T1_L2's rows, and RLM-10's cells of G4_fig3c's grid_tables.json (n paired, both pass rates,
the difference, at score 3 and 4) recomputed from G4_fig3c's pairs.jsonl. Then, from the rows the plate draws, by the
method S474, S475 and S476 state, this script recomputes every cell of the
committed data workbook that the rows determine without a bootstrap: sheet Supplementary Fig. 8a (every question value and draw count;
every cap row's mean, questions, answers, failed, median, quartiles, range, cap-reached and stopped-by-cap counts and
shares), sheet Supplementary Fig. 8b (every answer's recall; every model cap row's mean, median, questions, answers, failed,
cap-reached and stopped-by-cap counts) and sheet Supplementary Fig. 8c (RLM-10's cells at score 3 and 4: n paired, both
strategies' shares passing, the difference). Each must equal its cell within 1e-9 (a float-summing tolerance). Any
difference: the script prints it and exits 2 with nothing written.

Then it writes findings/recompute/S490_fig3_plateau/numbers.json (no time in it, so a rerun is byte-equal):
  plateau     per system of panel a, the cap where the mean stops rising, under two rules:
              interval rule: the smallest cap whose mean is at or above the lower end of the 95% interval of the
                highest-mean cap (that interval is S474's bootstrap, read from the workbook cell it reproduced);
              two-point rule: the smallest cap whose mean is within 2 points of the highest mean.
  common86    panel c's indexes with 5 and 10 core papers, on all common answerable questions (pairs.jsonl "common",
              both cells judged): each strategy's share of answers at score 4 or more (D154: the pass rate) and at
              score 3 or more (the relaxed threshold, the 25 October rule), and the range over the six indexes and
              both strategies.
  same_text   panel b: answers whose text (answer_sha256) is the same at caps 20 and 50, same model and question,
              over T1_L2's complete questions.
Beside each number: the value the inventory (findings/audits/scratch_repro_2026-10-26/INVENTORY.md, F13) states and
whether they are equal. A difference is reported, never adjusted.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import openpyxl

REPO = Path(__file__).resolve().parents[1]
# D160 (7) Q23: Supplementary Figure 8a draws L2_d135 (G6 after the D135 reruns, written by S476 rebuild once
# findings/recompute/g6_d135_inputs is frozen); until then it draws L2 (G6 before them). This script reproduces the
# rows the plate draws, so it reads the same file.
L2_GATED_ROWS = REPO / "findings/recompute/L2/concept_recall.jsonl"
L2_D135_ROWS = REPO / "findings/recompute/L2_d135/concept_recall.jsonl"
L2_ROWS = L2_D135_ROWS if L2_D135_ROWS.exists() else L2_GATED_ROWS
A_FIELD = "concept_recall_loose"
# D186 (4): when the plate's supplementary_figure8_provenance.json in the working tree (read here, at import) names D181's reading
# ("l2_d181"), a is reproduced from that folder's rows and their D181 value, so this script reads the rows the plate draws
_PROV = REPO / "findings/figures_provisional/supp_fig8_depth/supplementary_figure8_provenance.json"
_D181 = (json.loads(_PROV.read_text()).get("l2_d181") or {}) if _PROV.exists() else {}
if _D181.get("drawn"):
    L2_ROWS, A_FIELD = REPO / _D181["drawn"] / "concept_recall.jsonl", "concept_recall"
T1_ROWS_V24 = REPO / "findings/recompute/T1_L2/concept_recall.jsonl"
T1_TABLES_V24 = REPO / "findings/recompute/T1_L2/cap_tables.json"
G4_ROWS_V24 = REPO / "findings/recompute/G4_fig3c/pairs.jsonl"
G4_GRID_V24 = REPO / "findings/recompute/G4_fig3c/grid_tables.json"
T1_ROWS, T1_TABLES, B_FIELD, G4_ROWS = T1_ROWS_V24, T1_TABLES_V24, "concept_recall_loose", G4_ROWS_V24
# D188: when the plate's provenance names T1_L2_d181 ("t1_d181") and G4_fig3c_d185 ("g4_d185"), b and c are reproduced
# from those folders, the rows the plate draws; the v2.4 folders above stay the anchors reproduced first
_T1D = ((json.loads(_PROV.read_text()).get("t1_d181") or {}) if _PROV.exists() else {}).get("dir")
_G4D = ((json.loads(_PROV.read_text()).get("g4_d185") or {}) if _PROV.exists() else {}).get("dir")
if _T1D:
    T1_ROWS, T1_TABLES, B_FIELD = REPO / _T1D / "concept_recall.jsonl", REPO / _T1D / "cap_tables.json", "concept_recall"
if _G4D:
    G4_ROWS = REPO / _G4D / "grid_pairs.jsonl"
PLATE = REPO / "findings/figures_provisional/supp_fig8_depth"
SD_GLOB = "Supplementary Figure 8 data (provisional*.xlsx"
SHEET = "Supplementary Fig. 8"
# D283: a and b moved to main Figure 4 (sheets "Fig. 4a", "Fig. 4b"), c alone stays Supplementary Figure 8 (one sheet,
# "Supplementary Fig. 8"); the sheets are read under the names a, b and c this script has always used
PLATE_AB = REPO / "findings/figures_provisional/fig4_depth"
SD_GLOB_AB = "Source Data Fig. 4 (provisional*.xlsx"
# D284: RLM's draws 2 and 3 on all 86 (S514 l2g7 --all86), joined to the drawn D181 rows as S476 joins them
L2_D284_ROWS = REPO / "findings/recompute/L2_d135_d181_d284/concept_recall_g7.jsonl"
OUT = REPO / "findings/recompute/S490_fig3_plateau"
TOL = 1e-9
SYSTEMS = ("G5", "G6")
SYSTEM_NAME = {"G5": "Mentori's RLM", "G6": "authors' RLM package"}
SMALL_CORE = (5, 10)            # F13: "at 5 and 10 papers"
CAP_A, CAP_B = 20, 50           # F13: "identical at caps 20 and 50"

# The inventory's F13 values, for the comparison only (nothing here is an anchor or a target).
INVENTORY_F13 = {
    "plateau_interval_rule_cap": {"G5": 3, "G6": 5},
    "plateau_two_point_rule_cap": {"G5": 7, "G6": 10},
    "common86_small_index_range_pct_score3": [24.10, 55.95],
    "same_text_cap20_cap50": {"same": 51, "of": 52},
}
INVENTORY_NOTE = ("INVENTORY.md F13: plateau at cap 3 (interval rule) and cap 7 (2-point rule), package at cap 5 or 10; "
                  "24.10% to 55.95% on all 86 questions at 5 and 10 papers; 51 of 52 answers identical at caps 20 and "
                  "50. The package's 'cap 5 or 10' is read as cap 5 by the interval rule and cap 10 by the 2-point "
                  "rule (fig3_alt/STORY.md:164: 'By the same two rules: cap 5 and cap 10').")


class Refused(Exception):
    pass


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(REPO))


def jl(p: Path) -> list:
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def source_data_path(plate: Path = PLATE, pattern: str = SD_GLOB) -> Path:
    wbs = sorted(glob.glob(str(plate / pattern)))
    if len(wbs) != 1:
        raise Refused(f"expected one data workbook in {rel(plate)}, found {len(wbs)}")
    return Path(wbs[0])


def l2_rows() -> list:
    """The rows a draws: L2_ROWS, and with D284's folder present RLM's draws 2 and 3 joined to them."""
    rows = jl(L2_ROWS)
    if A_FIELD == "concept_recall" and L2_D284_ROWS.exists():
        rows = rows + jl(L2_D284_ROWS)
    return rows


def read_source_data(p: Path) -> dict:
    wb = openpyxl.load_workbook(p, read_only=True)
    sd = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        sd[ws.title] = [{k: (None if v == "" else v) for k, v in zip(rows[0], r)} for r in rows[1:]]
    return sd


def load_inputs() -> dict:
    sdp = source_data_path()
    sd7 = read_source_data(sdp)
    sdab = read_source_data(source_data_path(PLATE_AB, SD_GLOB_AB))
    sd = {f"{SHEET}a": sdab["Fig. 4a"], f"{SHEET}b": sdab["Fig. 4b"], f"{SHEET}c": sd7[SHEET]}
    return {"l2": l2_rows(), "t1": jl(T1_ROWS), "t1tab": json.loads(T1_TABLES.read_text()), "g4": jl(G4_ROWS),
            "sd": sd, "sd_path": sdp, "sd_path_ab": source_data_path(PLATE_AB, SD_GLOB_AB),
            "t1_v24": jl(T1_ROWS_V24), "t1tab_v24": json.loads(T1_TABLES_V24.read_text()), "g4_v24": jl(G4_ROWS_V24),
            "grid_v24": json.loads(G4_GRID_V24.read_text())}


# ------------------------------------------------------------------------------------------------ recomputation
def a_tables(l2: list) -> dict:
    """Panel a per system and cap: the per-question means (over draws) and the cap summaries, as S474/S475 compute
    them (the cap mean is round(mean, 4) x 100, S474 cap_tables then S475)."""
    caps = sorted({r["cap"] for r in l2})
    qorder = sorted({r["question_id"] for r in l2})
    out = {}
    for s in SYSTEMS:
        for c in caps:
            C = [r for r in l2 if r["system"] == s and r["cap"] == c]
            vals = defaultdict(list)
            for r in C:
                vals[r["question_id"]].append(r[A_FIELD])
            qv = {q: 100 * float(np.mean(vals[q])) for q in qorder if vals[q]}
            vec = np.array([float(np.mean(vals[q])) for q in qorder if vals[q]])
            pct = 100 * vec
            q1, q3 = np.percentile(pct, [25, 75])
            out[(s, c)] = {"question_value_pct": qv, "question_draws": {q: len(vals[q]) for q in qorder if vals[q]},
                           "mean_pct": 100 * round(float(np.mean(vec)), 4), "questions": len(vec),
                           "answers": len(C), "failed": sum(bool(r["failed"]) for r in C),
                           "median_pct": float(np.median(pct)), "q1_pct": float(q1), "q3_pct": float(q3),
                           "min_pct": float(pct.min()), "max_pct": float(pct.max()),
                           "cap_reached_n": sum(bool(r["cap_reached"]) for r in C),
                           "stopped_by_cap_n": sum(bool(r["stopped_by_cap"]) for r in C)}
            t = out[(s, c)]
            t["cap_reached_pct"] = 100 * round(t["cap_reached_n"] / len(C), 4)
            t["stopped_by_cap_pct"] = 100 * round(t["stopped_by_cap_n"] / len(C), 4)
    return {"caps": caps, "qorder": qorder, "cells": out}


def b_tables(t1: list, t1tab: dict, field: str | None = None) -> dict:
    """Panel b per model and cap over the complete questions, on field (default B_FIELD, the value the plate draws)."""
    field = B_FIELD if field is None else field
    complete = list(t1tab["complete_questions"])
    out = {}
    for m in t1tab["models"]:
        for c in t1tab["caps"]:
            R = [r for r in t1 if r["model"] == m and r["cap"] == c]
            K = [r for r in R if r["in_complete_question"]]
            v = [100 * r[field] for r in K]
            out[(m, c)] = {"questions_complete": len(K), "answers": len(R),
                           "mean_pct": float(np.mean(v)) if v else None,
                           "median_pct": float(np.median(v)) if v else None,
                           "failed": sum(bool(r["failed"]) for r in K),
                           "cap_reached_n": sum(bool(r["cap_reached"]) for r in K),
                           "stopped_by_cap_n": sum(bool(r["stopped_by_cap"]) for r in K)}
    return {"complete": complete, "cells": out}


def pair_reading(rows: list, set_name: str, which: str) -> dict:
    """RLM-10 against single pass over one index's questions in set_name with both cells judged (S476 grid_point's
    pairing: question order, None left out)."""
    pairs = []
    for r in sorted(rows, key=lambda x: x["question_id"]):
        if not r[set_name]:
            continue
        a, b = r["cells"]["rlm_10"][which], r["cells"]["single_pass"][which]
        if a is None or b is None:
            continue
        pairs.append((a, b))
    n = len(pairs)
    if not n:
        return {"n_paired": 0}
    return {"n_paired": n, "pass_rlm10_pct": 100 * sum(a for a, _ in pairs) / n,
            "pass_single_pass_pct": 100 * sum(b for _, b in pairs) / n,
            "d_pp": 100 * float(np.mean([a - b for a, b in pairs]))}


# ------------------------------------------------------------------------------------------------ the gate
def gate(inp: dict) -> tuple[list, Counter, dict]:
    sd = inp["sd"]
    bad, compared = [], Counter()

    def same(what, got, want, panel):
        compared[panel] += 1
        if isinstance(want, bool) or isinstance(got, bool) or want is None or got is None:
            if want != got:
                bad.append(f"{what}: workbook {want!r}, recomputed {got!r}")
            return
        if isinstance(want, (int, float)) and isinstance(got, (int, float)):
            if not math.isclose(float(got), float(want), abs_tol=TOL, rel_tol=0):
                bad.append(f"{what}: workbook {want!r}, recomputed {got!r}")
        elif got != want:
            bad.append(f"{what}: workbook {want!r}, recomputed {got!r}")

    # D188: the v2.4 anchors first. T1_L2's cap_tables.json from its rows (the loose value), and RLM-10's cells of
    # G4_fig3c's grid_tables.json from its pairs.jsonl
    Bv = b_tables(inp["t1_v24"], inp["t1tab_v24"], "concept_recall_loose")
    tv = {(c["model"], c["cap"]): c for c in inp["t1tab_v24"]["cells"]}
    if set(tv) != set(Bv["cells"]):
        bad.append(f"v2.4 b: T1_L2 cap_tables cells {sorted(tv)} are not the rows' {sorted(Bv['cells'])}")
    for key, t in Bv["cells"].items():
        w = tv.get(key)
        if w is None:
            continue
        same(f"v2.4 b {key[0]} cap {key[1]} mean", None if t["mean_pct"] is None else t["mean_pct"] / 100, w["mean"],
             "v2.4 b")
        for col in ("questions_complete", "failed", "cap_reached_n", "stopped_by_cap_n"):
            same(f"v2.4 b {key[0]} cap {key[1]} {col}", t[col], w[col], "v2.4 b")
    v_idx = defaultdict(list)
    for r in inp["g4_v24"]:
        v_idx[r["index"]].append(r)
    gv = [e for e in inp["grid_v24"]["cells"] if e["strategy"] == "rlm_10" and e["complete"]]
    if not gv:
        bad.append("v2.4 c: G4_fig3c's grid_tables.json holds no complete rlm_10 cell")
    for e in gv:
        got = pair_reading(v_idx[e["index"]], "covered", {3: "pass3", 4: "pass4"}[e["score"]])
        for mine, ref in (("n_paired", "n_paired"), ("pass_rlm10_pct", "pass_strategy_pct"),
                          ("pass_single_pass_pct", "pass_single_pass_pct"), ("d_pp", "d_pp")):
            same(f"v2.4 c score {e['score']} {e['index']} {ref}", got.get(mine), e[ref], "v2.4 c")

    A = a_tables(inp["l2"])
    sd_cap = {(r["system"], r["cap"]): r for r in sd[f"{SHEET}a"] if r["row"] == "cap"}
    sd_q = {(r["system"], r["cap"], r["question_id"]): r for r in sd[f"{SHEET}a"] if r["row"] == "question"}
    sd_strip = {(r["system"], r["cap"]): r for r in sd[f"{SHEET}a"] if r["row"] == "strip"}
    if set(sd_cap) != set(A["cells"]):
        bad.append(f"a: workbook cap rows {sorted(sd_cap)} are not the rows' {sorted(A['cells'])}")
    n_q = 0
    for (s, c), t in A["cells"].items():
        w = sd_cap.get((s, c))
        if w is None:
            continue
        for col in ("mean_pct", "questions", "answers", "failed", "median_pct", "q1_pct", "q3_pct", "min_pct",
                    "max_pct"):
            same(f"a {s} cap {c} {col}", t[col], w[col], "a")
        ws = sd_strip.get((s, c))
        if ws is None:
            bad.append(f"a {s} cap {c}: no strip row")
        else:
            for col in ("answers", "cap_reached_n", "cap_reached_pct", "stopped_by_cap_n", "stopped_by_cap_pct"):
                same(f"a strip {s} cap {c} {col}", t[col], ws[col], "a")
        for q, v in t["question_value_pct"].items():
            wq = sd_q.get((s, c, q))
            if wq is None:
                bad.append(f"a {s} cap {c} {q}: no question row")
                continue
            n_q += 1
            same(f"a {s} cap {c} {q} value_pct", v, wq["value_pct"], "a")
            same(f"a {s} cap {c} {q} draws", t["question_draws"][q], wq["draws"], "a")
    if n_q != len(sd_q):
        bad.append(f"a: {n_q} question values recomputed, the workbook has {len(sd_q)} question rows")

    B = b_tables(inp["t1"], inp["t1tab"])
    sd_bc = {(r["model"], r["cap"]): r for r in sd[f"{SHEET}b"] if r["row"] == "cap"}
    sd_ba = {(r["answer_key"], r["model"]): r for r in sd[f"{SHEET}b"] if r["row"] == "answer"}
    if set(sd_bc) != set(B["cells"]):
        bad.append(f"b: workbook cap rows {sorted(sd_bc)} are not the rows' {sorted(B['cells'])}")
    for (m, c), t in B["cells"].items():
        w = sd_bc.get((m, c))
        if w is None:
            continue
        for col in ("questions_complete", "answers", "mean_pct", "median_pct", "failed", "cap_reached_n",
                    "stopped_by_cap_n"):
            same(f"b {m} cap {c} {col}", t[col], w[col], "b")
    b_col = "recall_pct" if any("recall_pct" in r for r in sd[f"{SHEET}b"]) else "recall_loose_pct"
    if len(sd_ba) != len(inp["t1"]):
        bad.append(f"b: {len(inp['t1'])} T1 rows, workbook {len(sd_ba)} answer rows")
    for r in inp["t1"]:
        w = sd_ba.get((r["answer_key"], r["model"]))
        if w is None:
            bad.append(f"b {r['model']} {r['answer_key']}: no answer row")
            continue
        same(f"b {r['model']} {r['answer_key']} {b_col}", 100 * r[B_FIELD], w[b_col], "b")

    g4 = inp["g4"]
    by_idx = defaultdict(list)
    for r in g4:
        by_idx[r["index"]].append(r)
    sd_c = [r for r in sd[f"{SHEET}c"] if r["row"] == "cell" and r["strategy"] == "rlm_10"]
    if not sd_c:
        bad.append("c: the workbook holds no rlm_10 cell")
    for w in sd_c:
        if not w["complete"]:
            continue
        which = {3: "pass3", 4: "pass4"}[w["score"]]
        got = pair_reading(by_idx[w["index"]], "covered", which)
        same(f"c score {w['score']} {w['index']} n_paired", got["n_paired"], w["n_paired"], "c")
        same(f"c score {w['score']} {w['index']} pass_strategy_pct", got.get("pass_rlm10_pct"),
             w["pass_strategy_pct"], "c")
        same(f"c score {w['score']} {w['index']} pass_single_pass_pct", got.get("pass_single_pass_pct"),
             w["pass_single_pass_pct"], "c")
        same(f"c score {w['score']} {w['index']} d_pp", got.get("d_pp"), w["d_pp"], "c")
    return bad, compared, {"A": A, "B": B, "by_idx": by_idx, "sd_cap": sd_cap}


# ------------------------------------------------------------------------------------------------ the numbers
def numbers(inp: dict, parts: dict) -> dict:
    A, B, by_idx, sd_cap = parts["A"], parts["B"], parts["by_idx"], parts["sd_cap"]
    plateau = {}
    for s in SYSTEMS:
        R = {c: A["cells"][(s, c)]["mean_pct"] for c in A["caps"]}
        best = max(A["caps"], key=lambda c: (R[c], -c))
        lo = sd_cap[(s, best)]["ci95_lo_pct"]
        hi = sd_cap[(s, best)]["ci95_hi_pct"]
        plateau[s] = {"name": SYSTEM_NAME[s], "mean_pct_per_cap": {str(c): R[c] for c in A["caps"]},
                      "highest_mean": {"cap": best, "mean_pct": R[best], "ci95_pct": [lo, hi]},
                      "interval_rule_cap": min(c for c in A["caps"] if R[c] >= lo),
                      "two_point_rule_cap": min(c for c in A["caps"] if R[c] >= R[best] - 2.0)}
    common = {}
    vals = {3: [], 4: []}
    for idx in sorted(by_idx, key=lambda i: (by_idx[i][0]["core_papers"], by_idx[i][0]["distractor_ratio"])):
        R = by_idx[idx]
        if R[0]["core_papers"] not in SMALL_CORE:
            continue
        e = {"core_papers": R[0]["core_papers"], "distractor_ratio": R[0]["distractor_ratio"],
             "common_questions": sum(bool(r["common"]) for r in R)}
        for score, which in ((3, "pass3"), (4, "pass4")):
            p = pair_reading(R, "common", which)
            e[f"score{score}"] = p
            vals[score] += [p["pass_rlm10_pct"], p["pass_single_pass_pct"]]
        common[idx] = e
    same_text = {}
    for m in inp["t1tab"]["models"]:
        ta = {r["question_id"]: r["answer_sha256"] for r in inp["t1"]
              if r["model"] == m and r["cap"] == CAP_A and r["in_complete_question"]}
        tb = {r["question_id"]: r["answer_sha256"] for r in inp["t1"]
              if r["model"] == m and r["cap"] == CAP_B and r["in_complete_question"]}
        both = sorted(set(ta) & set(tb))
        same_text[m] = {"questions_at_both": len(both), "same_text": sum(ta[q] == tb[q] for q in both)}
    tot_same = sum(v["same_text"] for v in same_text.values())
    tot_n = sum(v["questions_at_both"] for v in same_text.values())

    r3 = [round(min(vals[3]), 2), round(max(vals[3]), 2)]
    inv = INVENTORY_F13
    compare = {
        "plateau_interval_rule_cap": {s: {"computed": plateau[s]["interval_rule_cap"],
                                          "inventory": inv["plateau_interval_rule_cap"][s],
                                          "equal": plateau[s]["interval_rule_cap"] ==
                                          inv["plateau_interval_rule_cap"][s]} for s in SYSTEMS},
        "plateau_two_point_rule_cap": {s: {"computed": plateau[s]["two_point_rule_cap"],
                                           "inventory": inv["plateau_two_point_rule_cap"][s],
                                           "equal": plateau[s]["two_point_rule_cap"] ==
                                           inv["plateau_two_point_rule_cap"][s]} for s in SYSTEMS},
        "common86_small_index_range_pct_score3": {"computed_2dp": r3,
                                                  "inventory": inv["common86_small_index_range_pct_score3"],
                                                  "equal": r3 == inv["common86_small_index_range_pct_score3"]},
        "same_text_cap20_cap50": {"computed": {"same": tot_same, "of": tot_n},
                                  "inventory": inv["same_text_cap20_cap50"],
                                  "equal": {"same": tot_same, "of": tot_n} == inv["same_text_cap20_cap50"]},
    }
    return {
        "plateau": plateau,
        "plateau_rules": {"interval_rule": "smallest cap whose mean is at or above the lower end of the 95% interval "
                                           "of the highest-mean cap (the interval is the workbook cell)",
                          "two_point_rule": "smallest cap whose mean is within 2 points of the highest mean"},
        "common86": {"what": "panel c indexes with 5 and 10 core papers, all common answerable questions with both "
                             "cells judged; pass rate of RLM-10 and of single pass at judge score 3 or more and 4 or "
                             "more (D154: 4 is the pass rate, 3 the relaxed threshold)",
                     "indexes": common,
                     "range_pct_score3": [min(vals[3]), max(vals[3])],
                     "range_pct_score4": [min(vals[4]), max(vals[4])]},
        "same_text_cap20_cap50": {"what": f"T1 answers whose answer_sha256 is the same at caps {CAP_A} and {CAP_B}, "
                                          "same model and question, over T1_L2's complete questions",
                                  "complete_questions": len(inp["t1tab"]["complete_questions"]),
                                  "per_model": same_text, "same": tot_same, "of": tot_n},
        "inventory_compare": compare,
        "inventory_note": INVENTORY_NOTE,
    }


def build() -> tuple[dict, list, Counter]:
    inp = load_inputs()
    bad, compared, parts = gate(inp)
    if bad:
        return {}, bad, compared
    num = numbers(inp, parts)
    head = {"script": rel(Path(__file__)), "script_sha256": sha256_file(Path(__file__)),
            "command": "uv run python scripts/S490_fig3_plateau.py",
            "inputs": {rel(p): sha256_file(p) for p in dict.fromkeys((L2_ROWS, T1_ROWS, T1_TABLES, G4_ROWS, T1_ROWS_V24,
                                                                     T1_TABLES_V24, G4_ROWS_V24, G4_GRID_V24,
                                                                     inp["sd_path"], inp["sd_path_ab"])
                                                    + ((L2_D284_ROWS,) if A_FIELD == "concept_recall"
                                                       and L2_D284_ROWS.exists() else ()))},
            "readings": {"a": f"{rel(L2_ROWS)} ({A_FIELD})"
                              + (f" + {rel(L2_D284_ROWS)}" if A_FIELD == "concept_recall" and L2_D284_ROWS.exists() else ""), "b": f"{rel(T1_ROWS)} ({B_FIELD})", "c": rel(G4_ROWS),
                         "v2.4 anchors": [rel(T1_TABLES_V24), rel(G4_GRID_V24)]},
            "reproduced": {"values_equal_to_source_data": sum(v for k, v in compared.items() if len(k) == 1),
                           "per_sheet": {f"{SHEET}{k}": compared[k] for k in sorted(compared) if len(k) == 1},
                           "v2.4_anchors": {k: compared[k] for k in sorted(compared) if len(k) > 1},
                           "tolerance": TOL, "mismatches": 0}}
    return {"header": head, **num}, [], compared


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="compare with the committed output, write nothing")
    a = ap.parse_args(argv)
    try:
        doc, bad, compared = build()
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if bad:
        print(f"REPRODUCTION FAILED ({len(bad)} of {sum(compared.values())} values differ), nothing written:",
              file=sys.stderr)
        for b in bad[:20]:
            print("  " + b, file=sys.stderr)
        return 2
    print(f"reproduced: {sum(compared.values())} workbook values equal "
          f"({', '.join((f'{SHEET}{k}' if len(k) == 1 else k) + f' {v}' for k, v in sorted(compared.items()))}); "
          f"0 mismatches")
    text = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    target = OUT / "numbers.json"
    if a.check:
        ok = target.exists() and target.read_text() == text
        print(f"{rel(target)} {'byte-equal' if ok else 'DIFFERS'}")
        return 0 if ok else 1
    OUT.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    for k, v in doc["inventory_compare"].items():
        print(f"{k}: {json.dumps(v)}")
    print(f"wrote {rel(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
