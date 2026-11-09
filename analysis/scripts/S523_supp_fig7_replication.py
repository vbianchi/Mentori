#!/usr/bin/env python3
"""S523 - Supplementary Figure 6, replication in full: a and b from the T2 judge rows (D256), c from S518's verdicts.

    uv run --frozen python scripts/S523_supp_fig7_replication.py [--out <folder>]
    uv run --frozen python scripts/S523_supp_fig7_replication_test.py

WHAT IT DOES. Draws the plate, 183 x 150 mm, and writes it (PDF, SVG, PNG), a data workbook, the numbers and provenance
files and the legend into findings/figures_provisional/supp_fig6_replication/ (or --out). No model call.

  a  Valerio's tab comment of 6 November (replacing fig3.md S7 a's double difference): ten rows on one axis, two per
     generator (gemini-3-flash, gemma3:27b, qwen3-coder:30b, claude-haiku-4-5, gemini-2.5-pro: Figure 3e's order,
     D289), verified pass above
     RLM-10. A question's value is the generator's pass share (judge score 4 or more, over the draws it holds) with the
     strategy minus with single pass, in percentage points, on the answerable questions where the generator holds both
     strategies. O1 of Valerio's tab thread of 6 Nov 21:27 (the box and dot rows collapsed onto 0 and needed floating
     counts): a diverging bar per row, the share of questions where the strategy passed fewer draws than single pass
     to the left (vermillion) and more to the right (blue), ties not drawn (counted in sheet a); a black diamond for the
     mean difference with its two-sided 95% percentile interval over 10,000 question resamples (S463's seed). No
     number in the panel but the axis ticks and n per row in the right column.
  b  fig3.md S7 b, D256 Q2: the six strategies ranked by pass rate at score 4 within each generator (gemini-3-flash
     and the four T2 generators), on the answerable questions every one of that generator's strategies answered; rank 1
     yellow, ranks only, a tie sharing the higher rank.
  c  RLM-10 minus single pass at judge score 4 or more on the one-paper and many-paper questions, per generator, with
     the 95% interval S518 stored (fig3.md section 6, S7 c). Read only from S518's committed verdict files
     (findings/recompute/S518_split_confirmation/<source>.json), through S463.read_s518 and S463.s518_rows, the reader
     Figure 3e uses. D289 (Valerio, 7 Nov): c is the complement of Figure 3e, which draws I alone: the same six rows,
     order, labels and gap (S463.E3_ROW_ORDER, S463.E3_LABEL, S463.e3_layout), gemini-3-flash with the main judge,
     gemini-3-flash with the second judge, gemma3:27b, qwen3-coder:30b, then after the gap claude-haiku-4-5 and
     gemini-2.5-pro; no group heads. This replaces fig3.md:130's "the second judge is not drawn".

THE ROWS OF a AND b (D256, Valerio, 5 November 18:46, "Q1: ok, Q2: ok"). judge_rows_v25.t2_source reads each generator's
committed collects, all six strategies and draws 1 to 3, the key v2.5 row where one exists, else the key v2.4 row:
gemini-3-flash-preview from fig2_inputs and fig3_s6_inputs, claude-haiku-4-5 and gemini-2.5-pro from S518_inputs, the two
local generators from t2_local_v25_inputs (S585, after D209's draws 2 and 3). Every file is held to its SHA256SUMS
line. The judge-code rule, S463.panel_f_judge_codes, is applied to every T2 file beside G1's: key v2.4, 11e51fde beside
38ae79ab with S495's passed proof; key v2.5, 211568db itself or (D256 Q1) a run whose headers name G1 v2.5's
judge_passages code identity (gemma3 26705cce, qwen3-coder ca540672). The first judge only, devstral-small-2:24b: no
second-judge row (fig3.md:130).

REPRODUCE FIRST (README.md:75-79). Before anything is written: from these cells, S518's D_one and D_many with their
intervals for gemini-3-flash-preview, claude-haiku-4-5 and gemini-2.5-pro (RLM-10 against single pass), and
gemini-3-flash's six pass rates at score 4 on the 86 equal to Figure 3a's committed rates (figure3_numbers.json, sheet
Fig. 3a, row kind strategy, group all); the two local sets reproduce S518's earlier copies cell by cell
(judge_rows_v25.t2_source). Any difference refuses the build.

The count in the name is the T2 answers the plate reads for the four T2 generators (cells of t2_source), of D178's
7,020 (experiments/README.md:1344).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import S457_fig2_panels as S457  # noqa: E402
import S463_fig2_ranking as S463  # noqa: E402
import fig_repro as FR  # noqa: E402
import figure_names as fn  # noqa: E402
import house_style as hs  # noqa: E402
import judge_rows_v25 as JR  # noqa: E402

SCRIPT = "scripts/S523_supp_fig7_replication.py"
N = 6                                              # D302 (5 before; 7 before D257)
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig6_replication"
T2_PLANNED = 7020                                # D178 (experiments/README.md:1344): T2's planned size
GENERATORS = ("claude-haiku-4-5", "gemini-2.5-pro", "gemma3:27b", "qwen3-coder:30b")    # D160 (2)
C_SOURCES = S463.E3_ROW_ORDER                    # D289: Figure 3e's six rows, its order (S518's five and the reference)
C_MEASURES = ("one_paper", "many_paper")         # fig3.md S7 c: D_one and D_many
T2_GENS = ("claude-haiku-4-5", "gemini-2.5-pro", "gemma3", "qwen3-coder")     # t2_source names, the T2 generators
B_GENS = (JR.FLASH, "gemma3", "qwen3-coder", "claude-haiku-4-5", "gemini-2.5-pro")   # panel b's rows, 3e's order (D289)
GEN_LABEL = {JR.FLASH: "gemini-3-flash", "claude-haiku-4-5": "claude-haiku-4-5", "gemini-2.5-pro": "gemini-2.5-pro",
             "gemma3": "gemma3:27b", "qwen3-coder": "qwen3-coder:30b"}
A_GENS = B_GENS                                  # panel a's generators, gemini-3-flash first (Valerio's tab comment, 6 Nov)
A_ARMS = ("verified_pass", "rlm_10")             # panel a: two rows per generator, this order (tab comment, 6 Nov)
SP = "single_pass"
STRATS = JR.T2_CONFIGS                           # single pass, multi-hop, verified pass, RLM-5, RLM-10, RLM-20
STRAT_LABEL = dict(zip(STRATS, (fn.SINGLE_PASS, fn.MULTI_HOP, fn.VERIFIED_PASS, fn.RLM_5, fn.RLM_10, fn.RLM_20)))
THRESHOLD = 4
B_QUESTIONS = {JR.FLASH: 86, "claude-haiku-4-5": 86, "gemini-2.5-pro": 86, "gemma3": 29, "qwen3-coder": 29}
#   D256 Q2: the answerable questions every strategy of the generator answered; the build refuses other counts.
#   gemini-2.5-pro answered all six at draw 1 on the 135 (draws 2 and 3 on D98's 45), so its count is 86.
REPRO_TOL = 1e-9
W, H = S457.FIG_W_MM, 150.0
SHEETS = {k: f"Supplementary Fig. {N}{k}" for k in "abc"}
SLOTS = {"a": (0.0, 0.0, 183.0, 96.0), "b": (0.0, 98.0, 77.0, 52.0), "c": (80.0, 98.0, 103.0, 52.0)}
OWNED = (f"Supplementary Figure {N}*", f"supplementary_figure{N}_numbers.json", f"supplementary_figure{N}_provenance.json",
         "legend_draft.md")
# panel a, in mm: one axis; per generator two rows (verified pass, RLM-10)
A_GLAB, A_SLAB = 35.0, 55.0                      # right edges: the generators' names, the strategies' names
A_X0, A_X1, A_XN = 57.0, 163.0, 182.5            # axes left, axes right, the n column's right edge
A_TOP, A_RP, A_GGAP = 8.0, 7.0, 2.0              # first row's top, a row's height, the gap between two generators
A_XLIM, A_TICKS = (-55.0, 55.0), (-50, -25, 0, 25, 50)   # O1 bars: every share and interval within 45
A_BAR_MM = 4.0                                   # a row's bar thickness
A_FEWER, A_MORE = hs.OKABE["vermillion"], hs.OKABE["blue"]
# panel b, in mm
B_LAB, B_X0, B_TW, B_TH, B_GAP = 27.0, 28.5, 7.9, 5.2, 0.3   # label right edge, first tile, tile width, height, gap
B_HEAD_DY = 20.0                                 # the strategy heads' baseline below the slot's top (turned 90
#                                                  degrees, reading upwards); 23 before Valerio's tab comment of 6 Nov
B_YELLOW = hs.OKABE["yellow"]
# panel c, in mm from the slot's left edge and from the axes' top
C_LAB, C_AX, C_AXW = 37.0, 38.5, 63.0            # label column's right edge, axes left, axes width (D289: 3e's labels)
C_DY = 1.0                                       # the two marks' offsets; row pitch and gap S463.e3_layout's (D289)
C_DYS = {"one_paper": -C_DY, "many_paper": C_DY}
C_POS_TOL = 1e-9                                 # check_drawn: a mark's data value equals its workbook cell


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_c() -> dict:
    """S518's verdicts through Figure 3e's reader (it refuses a file that is not S518's), the drawn sources' rows only."""
    t2 = S463.read_s518(S463.S518_DIR)
    rows = [r for r in S463.s518_rows(t2) if r["source"] in C_SOURCES and r["measure"] in C_MEASURES]
    rows.sort(key=lambda r: (C_SOURCES.index(r["source"]), C_MEASURES.index(r["measure"])))   # D289: 3e's order
    got = [s for s in dict.fromkeys(r["source"] for r in rows)]
    if got != list(C_SOURCES):
        raise SystemExit(f"Supplementary Figure {N}: S518's verdicts give sources {got}, not {list(C_SOURCES)}")
    for r in rows:
        r["drawn"] = "panel c"
    used = {s: t2["sources"][s]["rows"]["rows_used"] for s in C_SOURCES}
    return {"rows": rows, "used": used, "k": sum(used.values()), "t2": t2}


def share(cells: dict, c: str, q: str):
    """A question's pass share at score 4 over the draws held (S511.shares' reading, Rule 10: a failed answer is a fail;
    a judge failure counts in neither direction), as a Fraction, or None when no draw holds an answer."""
    k = n = 0
    for d in (1, 2, 3):
        x = cells.get((c, q, d))
        if x is None:
            continue
        if x["kind"] == "scored":
            k, n = k + int(x["score"] >= THRESHOLD), n + 1
        elif x["kind"] == "failed":
            n += 1
    return Fraction(k, n) if n else None


def draws_held(cells: dict, c: str, q: str) -> str:
    return ",".join(str(d) for d in (1, 2, 3) if (cells.get((c, q, d)) or {}).get("kind") in ("scored", "failed"))


def judge_codes(src: dict) -> dict:
    """S463.panel_f_judge_codes on every T2 file beside G1's (D160 (5); D256 Q1 for key v2.5)."""
    g1 = src[JR.FLASH]
    out = {}
    for g in T2_GENS:
        r, rec = src[g], {}
        if r["run_sha256"]["v2.4"]:
            rec["v2.4"] = S463.panel_f_judge_codes(g1["run_sha256"]["v2.4"], r["run_sha256"]["v2.4"])
        rec["v2.5"] = S463.panel_f_judge_codes(g1["run_sha256"]["v2.5"], r["run_sha256"]["v2.5"],
                                               g1_headers=g1["headers_v25"], t2_headers=r["headers_v25"])
        out[g] = rec
    return out


def reproduce(src: dict, qs: dict) -> list[str]:
    """README.md:75-79: S518's D_one and D_many (with intervals and question counts) for Flash, Haiku and gemini-2.5-pro
    from these cells, and Flash's six pass rates at score 4 equal to Figure 3a's committed rates."""
    S518 = S463.s518_module()
    said = []
    for g in (JR.FLASH, "claude-haiku-4-5", "gemini-2.5-pro"):
        cells = {k: v for k, v in src[g]["cells"].items() if k[0] in (S518.A, S518.B)}
        got = S518.analyse(cells, qs)
        want = json.loads((S463.S518_DIR / f"{g}.json").read_text())["result"]
        for m in C_MEASURES:
            a, b = got[m], want[m]
            if a["questions"] != b["questions"] or any(abs(a[x] - b[x]) > REPRO_TOL for x in ("d", "lo", "hi")):
                raise SystemExit(f"Supplementary Figure {N}: reproduce refused: {g} {m} {a} is not S518's {b}")
        said.append(f"{g}: S518's D_one and D_many with intervals")
    f3 = json.loads((ROOT / "findings/figures_provisional/fig3_strategies/figure3_numbers.json").read_text())
    sh = f3["sheets"]["Fig. 3a"]
    rows = [dict(zip(sh["columns"], r)) for r in sh["rows"]]
    want = {r["strategy"]: r["pass_rate_pct"] for r in rows if r["row_kind"] == "strategy" and r["threshold"] == THRESHOLD
            and r["question_group"] == "all" and r["strategy"] in STRATS}
    ans = [q for q, v in qs.items() if v["kind"] in ("one", "many")]
    cells = src[JR.FLASH]["cells"]
    for c in STRATS:
        v = [share(cells, c, q) for q in ans]
        v = [x for x in v if x is not None]
        got = 100 * float(sum(v, Fraction(0)) / len(v))
        if c not in want or abs(got - want[c]) > 1e-6:
            raise SystemExit(f"Supplementary Figure {N}: reproduce refused: gemini-3-flash {c} {got} is not Figure 3a's "
                             f"{want.get(c)}")
    said.append("gemini-3-flash: Figure 3a's six pass rates at score 4 (figure3_numbers.json)")
    return said + [src[g]["reproduced"] for g in T2_GENS if src[g]["reproduced"]]


def read_ab() -> dict:
    """The five generators' cells (judge_rows_v25.t2_source), the judge-code rule, the reproduce step, then panel a's
    and panel b's rows."""
    qs = S463.s518_module().S511.questions()
    ans = [q for q, v in qs.items() if v["kind"] in ("one", "many")]
    src = {g: JR.t2_source(g) for g in B_GENS}
    codes = judge_codes(src)
    reproduced = reproduce(src, qs)
    a_rows, a_rowsum = [], []
    for g in A_GENS:
        for arm in A_ARMS:
            C, vals = src[g]["cells"], []
            for q in ans:
                p = (share(C, arm, q), share(C, SP, q))
                if None in p:
                    continue
                v = 100 * float(p[0] - p[1])
                vals.append(v)
                a_rows.append({"row_kind": "question (grey dot)", "strategy": arm, "strategy_label": STRAT_LABEL[arm],
                               "generator": GEN_LABEL[g], "question_id": q, "question_type": qs[q]["kind"],
                               "value_pp": round(v, 9), "generator_strategy_share": float(p[0]),
                               "generator_single_pass_share": float(p[1]),
                               "generator_draws_strategy": draws_held(C, arm, q),
                               "generator_draws_single_pass": draws_held(C, SP, q), "threshold": THRESHOLD})
            import numpy as np
            n = len(vals)
            fewer, more = sum(v < 0 for v in vals), sum(v > 0 for v in vals)
            boot = S463.resample_counts(n) @ np.asarray(vals) / n
            lo, hi = (float(x) for x in np.percentile(boot, S463.PCT))
            a_rowsum.append({"row_kind": "bar (questions fewer, tied, more; mean difference)", "strategy": arm,
                             "strategy_label": STRAT_LABEL[arm], "generator": GEN_LABEL[g], "n_questions": n,
                             "fewer": fewer, "tied": n - fewer - more, "more": more,
                             "fewer_pct": round(100 * fewer / n, 9), "more_pct": round(100 * more / n, 9),
                             "mean_pp": round(sum(vals) / n, 9), "ci95_lo_pp": round(lo, 9), "ci95_hi_pp": round(hi, 9),
                             "resamples": S463.N_BOOT, "resample_seed": S463.SEED,
                             "threshold": THRESHOLD, "_values": vals, "_gen": g})
    b_rows = []
    for g in B_GENS:
        C = src[g]["cells"]
        common = [q for q in ans if all(share(C, c, q) is not None for c in STRATS)]
        if len(common) != B_QUESTIONS[g]:
            raise SystemExit(f"Supplementary Figure {N} b: {g} answered all six strategies on {len(common)} answerable "
                             f"questions, not {B_QUESTIONS[g]} (D256 Q2)")
        rate = {c: sum((share(C, c, q) for q in common), Fraction(0)) / len(common) for c in STRATS}
        for c in STRATS:
            b_rows.append({"row_kind": "tile (generator by strategy)", "generator": GEN_LABEL[g], "strategy": c,
                           "strategy_label": STRAT_LABEL[c], "questions": len(common),
                           "pass_rate_pct": round(100 * float(rate[c]), 9),
                           "rank": 1 + sum(rate[x] > rate[c] for x in STRATS), "threshold": THRESHOLD, "_gen": g})
    k = {g: len(src[g]["cells"]) for g in T2_GENS}
    files = {}
    for g in B_GENS:
        files.update(src[g]["files"])
    return {"a_rows": a_rows, "a_box": a_rowsum, "b_rows": b_rows, "k": k, "files": files, "codes": codes,
            "reproduced": reproduced, "counts": {g: src[g]["counts"] for g in B_GENS},
            "run_sha256": {g: src[g]["run_sha256"] for g in B_GENS}}


def stamp(c: dict, ab: dict) -> str:
    parts = ", ".join(f"{GEN_LABEL[g]} {hs.fmt_num(v)}" for g, v in ab["k"].items())
    return (f"PROVISIONAL: panels a and b from the T2 judge rows on the final key (D256), {hs.fmt_num(sum(ab['k'].values()))} "
            f"of {hs.fmt_num(T2_PLANNED)} T2 answers read ({parts}); panel c from S518's committed verdicts (D195)")


def a_counts(ab: dict) -> dict:
    """Panel a's n per row, and the legend's claim about them: 86, except RLM-10 of the two local generators."""
    n = {(b["strategy"], b["_gen"]): b["n_questions"] for b in ab["a_box"]}
    loc = {n[("rlm_10", g)] for g in ("gemma3", "qwen3-coder")}
    rest = {v for (arm, g), v in n.items() if not (arm == "rlm_10" and g in ("gemma3", "qwen3-coder"))}
    if len(loc) != 1 or len(rest) != 1:
        raise SystemExit(f"Supplementary Figure {N} a: the legend's question counts are not shared as written: {n}")
    return {"all": rest.pop(), "local_rlm10": loc.pop()}


def legend(c: dict, ab: dict) -> str:
    q = {s: next(r for r in c["rows"] if r["source"] == s) for s in C_SOURCES}
    n_loc = (q["gemma3"]["questions_one_paper"], q["gemma3"]["questions_many_paper"])
    n_cld = (q["claude-haiku-4-5"]["questions_one_paper"], q["claude-haiku-4-5"]["questions_many_paper"])
    ys_c, _ = S463.e3_layout([(s, c["t2"]["sources"][s]["role"]) for s in C_SOURCES])
    roles_c = [c["t2"]["sources"][s]["role"] for s in sorted(ys_c, key=ys_c.get)]
    if roles_c != ["reference", "test", "test", "test", "beside", "beside"]:
        raise SystemExit(f"Supplementary Figure {N} c: the legend names the rows by place, the plate's roles are {roles_c}")
    nqs = {s: (q[s]["questions_one_paper"], q[s]["questions_many_paper"]) for s in C_SOURCES}
    if nqs["qwen3-coder"] != n_loc or any(nqs[s] != n_cld for s in ("gemini-2.5-pro", "gemini-3-flash-preview",
                                                                    "second_judge")):
        raise SystemExit(f"Supplementary Figure {N}: the legend's question counts are not shared as written")
    # T2X (D241, D243): many-paper questions outside D98's 45 answered under RLM-10 in draw 1 only (S518 rows t2x_rows)
    x = {s: json.loads((S463.S518_DIR / f"{s}.json").read_text())["rows"].get("t2x_rows", 0) for s in ("gemma3", "qwen3-coder")}
    if x["gemma3"] != x["qwen3-coder"]:
        raise SystemExit(f"Supplementary Figure {N}: the T2X counts differ between gemma3 and qwen3-coder: {x}")
    draws_loc = ("three draws" if not x["gemma3"] else
                 f"three draws (RLM-10: one draw on {x['gemma3']} of the many-paper questions)")
    na = a_counts(ab)
    nb = {g: next(r["questions"] for r in ab["b_rows"] if r["_gen"] == g) for g in B_GENS}
    big = [GEN_LABEL[g] for g in B_GENS if nb[g] == nb[JR.FLASH]]
    small = [GEN_LABEL[g] for g in B_GENS if nb[g] != nb[JR.FLASH]]
    if len({nb[g] for g in B_GENS if GEN_LABEL[g] in small}) != 1:
        raise SystemExit(f"Supplementary Figure {N} b: the legend's question counts are not shared as written: {nb}")
    nsmall = nb[next(g for g in B_GENS if GEN_LABEL[g] in small)]
    return (f"# Supplementary Figure {N}, title and legend (draft)\n\n"
            f"Written by `{SCRIPT}`. Data stamp: {stamp(c, ab)}.\n\n"
            f"**Supplementary Figure {N} | Replication on other generators in full.** Judged by devstral-small-2:24b on "
            f"the final answer key; a pass is judge score 4 or more. **a**, For each generator, two rows: verified pass and "
            f"RLM-10, each the generator's pass share with that strategy minus its pass share with single pass, per "
            f"answerable question, over its draws (three, except "
            f"gemini-2.5-pro, one draw outside the fixed 45-question subset, and the RLM runs of gemma3:27b and "
            f"qwen3-coder:30b, that subset only). Bars, the share of questions (%) where the strategy passed fewer draws "
            f"than single pass (vermilion, left of 0) and more (blue, right of 0); ties are not drawn. Diamond, the mean "
            f"of the questions' differences; line, its two-sided 95% percentile interval over "
            f"10,000 question resamples; dashed line, 0. A question counts in a row when the generator holds both "
            f"strategies on it: n = {na['all']} questions per row, except n = {na['local_rlm10']} questions for RLM-10 "
            f"of gemma3:27b and qwen3-coder:30b. **b**, Rank of six strategies (columns) by pass rate within each "
            f"generator (rows), on the answerable questions every strategy of that generator answered; 1 is the highest "
            f"and yellow, and a tie shares the higher rank. **c**, RLM-10 minus single pass, on "
            f"one-paper (blue square) and many-paper (orange diamond) questions, per generator, exploratory. Mark, the "
            f"mean of the questions' differences; bar, its two-sided 95% percentile interval over 10,000 question "
            f"resamples; dashed line, 0. Top row, gemini-3-flash, the reference; rows 2 to 4, the prespecified test; "
            f"below the gap, generators outside it. Main judge except the row naming the second judge "
            f"({S463.judge2()}). gemma3:27b and qwen3-coder:30b use {draws_loc}, n = {n_loc[0]} one-paper and n = "
            f"{n_loc[1]} many-paper questions; the other rows, n = {n_cld[0]} and n = {n_cld[1]} questions.\n")


def table(rs: list[dict]) -> tuple[list, list]:
    cols = list(dict.fromkeys(c for r in rs for c in r))
    return cols, [[r.get(c) for c in cols] for r in rs]


def check_drawn(marks: list, rows: list) -> list[str]:
    """Every row of sheet 7c drawn once, its mark at d_pp and its bar from ci95_lo_pp to ci95_hi_pp, in its colour."""
    probs = []
    if sorted(i for i, *_ in marks) != list(range(len(rows))):
        probs.append(f"{len(marks)} marks for {len(rows)} rows")
    for i, art, col in marks:
        r = rows[i]
        x = list(art["mark"].get_xdata())
        lo, hi = sorted(art["interval"].get_xdata())
        if len(x) != 1 or abs(x[0] - r["d_pp"]) > C_POS_TOL or abs(lo - r["ci95_lo_pp"]) > C_POS_TOL \
                or abs(hi - r["ci95_hi_pp"]) > C_POS_TOL:
            probs.append(f"{r['source']} {r['measure']}: drawn {x}, {lo}, {hi}; sheet {r['d_pp']}, "
                         f"{r['ci95_lo_pp']}, {r['ci95_hi_pp']}")
        if art["mark"].get_markerfacecolor().upper() != col.upper():
            probs.append(f"{r['source']} {r['measure']}: colour {art['mark'].get_markerfacecolor()}, want {col}")
    return probs


def check_drawn_ab(a_art: list, tiles: list) -> list[str]:
    """Panel a: every bar's two segments, diamond and interval at its sheet row, fewer + tied + more = n. Panel b: every tile's printed rank its sheet row's, yellow exactly when
    the rank is 1."""
    probs = []
    for b, left, right, est in a_art:
        w_l, w_r = -left.get_width(), right.get_width()
        x = list(est["mark"].get_xdata())
        lo, hi = sorted(est["interval"].get_xdata())
        if abs(w_l - b["fewer_pct"]) > C_POS_TOL or abs(w_r - b["more_pct"]) > C_POS_TOL or len(x) != 1 \
                or abs(x[0] - b["mean_pp"]) > C_POS_TOL or abs(lo - b["ci95_lo_pp"]) > C_POS_TOL \
                or abs(hi - b["ci95_hi_pp"]) > C_POS_TOL:
            probs.append(f"a {b['generator']} {b['strategy']}: drawn {w_l}, {w_r}, {x}, {lo}, {hi}; sheet "
                         f"{b['fewer_pct']}, {b['more_pct']}, {b['mean_pp']}, {b['ci95_lo_pp']}, {b['ci95_hi_pp']}")
        if b["fewer"] + b["tied"] + b["more"] != b["n_questions"] or len(b["_values"]) != b["n_questions"]:
            probs.append(f"a {b['generator']} {b['strategy']}: counts do not add to n")
    for r, rect, t in tiles:
        if t.get_text() != hs.fmt_num(r["rank"]):
            probs.append(f"b {r['generator']} {r['strategy']}: rank printed {t.get_text()}, sheet {r['rank']}")
        yellow = rect.get_facecolor()[:3] == tuple(int(B_YELLOW[i:i + 2], 16) / 255 for i in (1, 3, 5))
        if yellow != (r["rank"] == 1):
            probs.append(f"b {r['generator']} {r['strategy']}: yellow {yellow}, rank {r['rank']}")
    return probs


def draw(paths: dict, c: dict, ab: dict) -> dict:
    """a the T2 boxes, b the rank tiles, c S518's D_one and D_many per generator. Returns the printed map (S448 R8 (6))."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    plt.rcParams.update(hs.rc("S523"))
    hs.check_plate_kinds([])
    fig = hs.figure(W, H)
    printed = {}

    def fixed(t, why):
        gid = f"s448num_{len(printed)}"
        t.set_gid(gid)
        printed[gid] = {"fixed": t.get_text(), "why": why}
        return t

    def text(x, y, s, why, **kw):
        t = hs.text_mm(fig, x, y, s, **{"va": "center", **kw})
        return fixed(t, why) if any(ch.isdigit() for ch in s) else t

    def num(t, entry):
        """A printed number tied to its workbook cell (S448 R8 (6))."""
        gid = f"s448num_{len(printed)}"
        t.set_gid(gid)
        printed[gid] = entry
        return t

    from matplotlib.patches import Rectangle
    for k, (x, y, w, h) in SLOTS.items():
        t = hs.panel_letter(fig, x, y + 2.4, k)
        if k == "a":                                 # build_order F7: the map is never empty
            fixed(t, "panel letter")

    # ---- a: per question, the generator's strategy minus its single pass (Valerio's tab comment, 6 Nov) ------------
    #      one axis; per generator two rows, verified pass above RLM-10
    ya = SLOTS["a"][1]
    top = ya + A_TOP
    rows_y, y = {}, 0.0
    for i, g in enumerate(A_GENS):
        if i:
            y += A_GGAP
        for arm in A_ARMS:
            rows_y[(g, arm)] = y + A_RP / 2
            y += A_RP
    ha = y
    ax = hs.axes_mm(fig, A_X0, top, A_X1 - A_X0, ha, spines_on=("bottom",))
    ax.set_xlim(*A_XLIM)
    ax.set_ylim(ha, 0)
    ax.set_yticks([])
    ax.tick_params(left=False, pad=1)
    ax.xaxis.set_major_locator(FixedLocator(list(A_TICKS)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: hs.fmt_num(v)))
    ax.xaxis.set_minor_locator(NullLocator())
    hs.reference_line(ax, 0.0, dashed=True)
    mx, _ = hs.mm_per_unit(ax)
    for g in A_GENS:
        yg = sum(rows_y[(g, arm)] for arm in A_ARMS) / len(A_ARMS)
        text(A_GLAB, top + yg, GEN_LABEL[g], "the generator's name", ha="right")
        for arm in A_ARMS:
            text(A_SLAB, top + rows_y[(g, arm)], STRAT_LABEL[arm], "the strategy's name", ha="right")
    a_art = []
    for bi, b in enumerate(ab["a_box"]):
        yc = rows_y[(b["_gen"], b["strategy"])]
        out = [v for v in (-b["fewer_pct"], b["more_pct"], b["ci95_lo_pp"], b["ci95_hi_pp"])
               if not A_XLIM[0] <= v <= A_XLIM[1]]
        if out:
            raise SystemExit(f"Supplementary Figure {N} a: a value outside the axis {A_XLIM}: {out}")
        num(hs.text_mm(fig, A_XN, top + yc, f"n = {hs.fmt_num(b['n_questions'])}", va="center", ha="right"),
            {"sheet": SHEETS["a"], "row": bi, "format": "n = {n_questions}"})
        th = A_BAR_MM / hs.mm_per_unit(ax)[1]
        left = ax.barh(yc, -b["fewer_pct"], left=0.0, height=th, color=A_FEWER, edgecolor="none", lw=0, zorder=2.0)
        right = ax.barh(yc, b["more_pct"], left=0.0, height=th, color=A_MORE, edgecolor="none", lw=0, zorder=2.0)
        est = hs.estimate(ax, yc, b["mean_pp"], b["ci95_lo_pp"], b["ci95_hi_pp"], marker_="D", zorder=6.0)
        a_art.append((b, left[0], right[0], est))
    hs.key(fig, [("swatch", A_FEWER, "Fewer draws passed than single pass"),
                 ("swatch", A_MORE, "More draws passed"),
                 ("mark", (hs.BLACK, "D"), "Mean difference and its interval")],
           centre_x=A_X0 + (A_X1 - A_X0) / 2, y=ya + 2.4, max_width=None)
    text(A_X0 + (A_X1 - A_X0) / 2, top + ha + 6.4, "Share of questions (%); mean difference (percentage points)",
         "the axis label",
         ha="center")

    # ---- b: rank of the six strategies within each generator (fig3.md S7 b, D256 Q2) --------------------------------
    xb, yb, _, _ = SLOTS["b"]
    nb = len(B_GENS)
    tw, th = B_TW + B_GAP, B_TH + B_GAP
    B_HEAD_Y = yb + B_HEAD_DY
    top_b = B_HEAD_Y + 1.2
    axb = hs.axes_mm(fig, B_X0, top_b, len(STRATS) * tw, nb * th, spines_on=())
    axb.set_xlim(0, len(STRATS) * tw)
    axb.set_ylim(nb * th, 0)
    axb.set_axis_off()
    for j, cf in enumerate(STRATS):
        text(B_X0 + j * tw + B_TW / 2, B_HEAD_Y, STRAT_LABEL[cf], "the strategy's name", rotation=90, ha="center",
             va="bottom")
    tiles = []
    for i, g in enumerate(B_GENS):
        text(B_LAB, top_b + i * th + B_TH / 2, GEN_LABEL[g], "the generator's name", ha="right")
        for j, cf in enumerate(STRATS):
            ri, r = next((n_, x) for n_, x in enumerate(ab["b_rows"]) if x["_gen"] == g and x["strategy"] == cf)
            fill = B_YELLOW if r["rank"] == 1 else hs.WHITE
            rect = Rectangle((j * tw, i * th), B_TW, B_TH, facecolor=fill, edgecolor=hs.GREY["line"],
                             lw=hs.LINE_MIN_PT, zorder=2)
            axb.add_patch(rect)
            t = axb.text(j * tw + B_TW / 2, i * th + B_TH / 2, hs.fmt_num(r["rank"]), ha="center", va="center",
                         fontsize=hs.PT, color=hs.BLACK, zorder=3)
            num(t, {"sheet": SHEETS["b"], "row": ri, "format": "{rank}"})
            tiles.append((r, rect, t))

    # ---- c: S518's D_one and D_many per generator (fig3.md S7 c) -------------------------------------------------
    X, Y, WC, _ = SLOTS["c"]
    rows = c["rows"]
    xlim, ticks = S463.E3_XLIM, S463.E3_TICKS
    out = [f"{r['source']} {r['measure']}" for r in rows for v in (r["d_pp"], r["ci95_lo_pp"], r["ci95_hi_pp"])
           if not xlim[0] <= v <= xlim[1]]
    if out:
        raise SystemExit(f"Supplementary Figure {N} c: a value outside the axis {xlim}: {out[:3]}")
    hs.key(fig, [("mark", S463.E3_MARK[m], t) for m, t in zip(C_MEASURES, S463.E3_KEY)], centre_x=X + C_AX + C_AXW / 2,
           y=Y + 2.4, max_width=None)
    # D289: Figure 3e's rows, order and gap, no group heads
    ys, hc = S463.e3_layout([(s, c["t2"]["sources"][s]["role"]) for s in C_SOURCES])
    top = Y + 8.4
    ax = hs.axes_mm(fig, X + C_AX, top, C_AXW, hc, spines_on=("bottom",))
    ax.set_xlim(*xlim)
    ax.set_ylim(hc, 0)
    ax.set_yticks([])
    ax.tick_params(left=False, pad=1)
    ax.xaxis.set_major_locator(FixedLocator(list(ticks)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: hs.fmt_num(v)))
    ax.xaxis.set_minor_locator(NullLocator())
    hs.reference_line(ax, 0.0, dashed=True)
    for s, yc in ys.items():
        text(X + C_LAB, top + yc, S463.E3_LABEL[s], "the generator's name", ha="right")
    marks = []
    for i, r in enumerate(rows):
        col, mk = S463.E3_MARK[r["measure"]]
        art = hs.estimate(ax, ys[r["source"]] + C_DYS[r["measure"]], r["d_pp"], r["ci95_lo_pp"], r["ci95_hi_pp"],
                          marker_=mk, colour=col, zorder=6.0 + C_MEASURES.index(r["measure"]))
        marks.append((i, art, col))
    text(X + C_AX + C_AXW / 2, top + hc + 6.4, f"{S463.fn.RLM_10} minus single pass (percentage points)", "the axis label",
         ha="center")
    probs = check_drawn(marks, rows) + check_drawn_ab(a_art, tiles)
    if probs:
        plt.close(fig)
        raise SystemExit(f"Supplementary Figure {N} c: drawn marks differ from the workbook: {probs[:3]}")
    bad = hs.check_figure_colours(fig)
    if bad:
        raise SystemExit(f"Supplementary Figure {N}: colours outside the house palette: {bad}")
    S457.finish_plate(fig, W, H, paths, f"Supplementary Figure {N}")
    return printed


def clean(rs: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rs]


def build(out: Path) -> dict:
    S457.figure_lock_agreed()
    c = read_c()
    ab = read_ab()
    k = sum(ab["k"].values())
    tag = f" (provisional, {k} of {T2_PLANNED})"
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for pat in OWNED:
        for old in out.glob(pat):
            old.unlink()
    paths = {x: out / f"Supplementary Figure {N}{tag}.{x}" for x in ("pdf", "svg", "png")}
    sheet_list = [(SHEETS["a"], *table(clean(ab["a_box"]) + clean(ab["a_rows"]))),
                  (SHEETS["b"], *table(clean(ab["b_rows"]))), (SHEETS["c"], *table(c["rows"]))]
    sd = out / f"Supplementary Figure {N} data{tag}.xlsx"
    S457.write_source_data(sheet_list, sd)
    FR.deterministic_xlsx(sd)
    printed = draw(paths, c, ab)
    FR.check_pdf_deterministic(paths["pdf"])
    FR.check_svg_deterministic(paths["svg"])
    st = stamp(c, ab)
    nf = out / f"supplementary_figure{N}_numbers.json"
    nf.write_text(json.dumps({"stamp": st, "what": "a: per question and its bar row (fewer, tied, more; mean and interval), the generator's pass share with "
                              "the strategy minus with single pass (percentage points); b: pass rate and rank of the "
                              "six strategies per generator; c: S518's D_one and D_many per generator, as S518 stored "
                              "them (percentage points)",
                              "sheets": {nm: {"columns": cl, "rows": r} for nm, cl, r in sheet_list}, "printed": printed},
                             indent=1) + "\n")
    lf = out / "legend_draft.md"
    lf.write_text(legend(c, ab))
    cap = out / f"Supplementary Figure {N} data caption{tag}.md"
    cap.write_text(f"# Supplementary Figure {N} data, caption\n\nProvisional. Data stamp: {st}. Sheet {SHEETS['a']}: per "
                   f"generator and strategy (verified pass, RLM-10), one bar row (n_questions; questions where the "
                   f"strategy passed fewer, the same and more draws than single pass, and the first and last as % of "
                   f"n; mean_pp with its two-sided 95% percentile interval over 10,000 question resamples, seed "
                   f"{S463.SEED}) and one row per answerable question: the generator's pass shares at "
                   f"judge score 4 or more with the strategy and with single pass, the draws held, and value_pp, the "
                   f"strategy's share minus single pass's. Sheet {SHEETS['b']}: per generator and "
                   f"strategy, the pass rate at score 4 on the questions every strategy of the generator answered, and "
                   f"its rank (1 the highest; a tie shares the higher rank). Sheet {SHEETS['c']}: per generator and "
                   f"question type, RLM-10 minus single pass at judge score 4 or more (d_pp) with the two-sided 95% "
                   f"interval (ci95_lo_pp, ci95_hi_pp) and the exact two-sided sign-flip P, in percentage points, as "
                   f"S518 stored them, with the file and its sha256. Generated by `uv run --frozen python {SCRIPT}`.\n")
    names = [p.name for p in paths.values()] + [sd.name, cap.name, nf.name, lf.name]
    lock = ROOT / "experiments" / "FIGURE_LOCK.toml"
    t2 = c["t2"]
    pf = out / f"supplementary_figure{N}_provenance.json"
    pf.write_text(json.dumps(
        {"provenance": {"script": SCRIPT, "script_sha256": sha(Path(__file__)),
                        "command": f"uv run --frozen python {SCRIPT}", "python": platform.python_version(),
                        "deterministic": "no build time and no repository HEAD are recorded",
                        "inputs_sha256": {"experiments/FIGURE_LOCK.toml": sha(lock),
                                          "scripts/house_style.py": sha(ROOT / "scripts/house_style.py"),
                                          "scripts/S457_fig2_panels.py": sha(ROOT / "scripts/S457_fig2_panels.py"),
                                          "scripts/S463_fig2_ranking.py": sha(ROOT / "scripts/S463_fig2_ranking.py"),
                                          "scripts/S518_split_confirmation.py":
                                              sha(ROOT / "scripts/S518_split_confirmation.py"),
                                          "scripts/judge_rows_v25.py": sha(ROOT / "scripts/judge_rows_v25.py"),
                                          "findings/figures_provisional/fig3_strategies/figure3_numbers.json":
                                              sha(ROOT / "findings/figures_provisional/fig3_strategies/figure3_numbers.json"),
                                          **{S463.label(p): t2["sha256"][str(p)] for p in t2["paths"]},
                                          **{S463.label(p): v for p, v in sorted(ab["files"].items())}},
                        "reproduced": {"c": t2["reproduced"], "a and b": ab["reproduced"]},
                        "judge_codes": ab["codes"], "rows": ab["counts"],
                        "decision": "D256 (Valerio, 5 Nov 18:46: 'Q1: ok, Q2: ok')",
                        "model_calls": 0},
         "stamp": st, "page_mm": [W, H], "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha(lock),
                                                         "status": S457.FLOCK.get("status")},
         "files": {n: sha(out / n) for n in names}}, indent=1) + "\n")
    return {"out": out, "names": names}


def main(argv=None) -> int:
    FR.pin_hash_seed()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    r = build(a.out)
    print(f"wrote {len(r['names']) + 1} files into {r['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
