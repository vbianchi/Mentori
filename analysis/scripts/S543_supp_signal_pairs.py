#!/usr/bin/env python3
"""S543 - Supplementary Figure 12: answers stating every concept, each strategy against single pass (FF18 a), old Figure 5b (D295) and old Figure 6e (D298).

WHY. FF18 a moved old 5c and old 5d off Figure 5. Build spec fig5.md section 6. Valerio's note of 2 November brought old
5d back to Figure 5, so old 5e, the margin per draw, takes panel b here in its place and no panel is lost.

WHAT THE CODE DOES. It imports S497 and reads panel_data's output through S497.d200_data, so the numbers have one source.
  a  old 5c: dat["C"], the answers of 5b that state every key concept (found equal to the concepts counted, D181's
     reading), by the judge's verdict. A count too narrow for its segment prints just right of the bar. The n column
     counts only these answers.
  b  old 5e: dat["E_DRAWN"], per draw (wins - losses) / (wins + ties + losses) x 100 of each strategy against the same
     draw of single pass on the W questions where both values exist, one mark per draw, Judge and Concepts three draws,
     Papers draw 1. The judge compares 0 to 5 scores. Marks closer than one marker width move up or down, never sideways.
     Marks are 1.25 mm; if two would still overlap they are drawn at 1.1 mm (fig5.md 5d), and past that the build refuses.
  c  old Figure 5b, moved here by D295 (Valerio's "go", 7 November, thread 206c8013): dat["B"], the draw-1 answers by the
     judge's verdict and Papers high (at or above their pooled median) or low, drawn by S497.draw_verdict_papers in a
     second band. Its sheet holds the rows of HEAD's sheet Fig. 6b, its legend clause old b's, relettered.
  d  old Figure 6e, moved here by D298 (Valerio's "O1", 7 November, thread ded27888: "move e to Supplementary Fig. 12 as
     panel d, and keep one sentence here citing it. Figure 6 becomes a to e, with the evaluators as e."): dat["G"], Papers
     of the draw-1 answers at faithfulness 5 and below, drawn by S497.draw_papers_by_faithfulness right of c in the
     second band. Its sheet holds the rows of HEAD's sheet Fig. 6e, its legend clause old e's, relettered, with the
     faithfulness definition and the box spelled out (Figure 6's "box as in a" does not reach this plate).

    uv run --frozen python scripts/S543_supp_signal_pairs.py figure [--out <folder>]

With minicheck_filter's heading rule unset it exits 2, as that module does, and writes nothing.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
SCRIPT = "scripts/S543_supp_signal_pairs.py"
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig12_signal_pairs"
N = 12                                             # D302 (19 before; 16 before D257)
W = 183.0
H1 = 59.0                               # band 1 (a, b): 57 in fig5.md; old 5e's rows need 7.6 mm, so its marks stay inside them
R1 = 12.0                               # band 1's rows start under its key lines (S497's d200_layout R1 until D295)
C_Y0 = H1 + 3.6                         # band 2 (c, old Figure 5b): its letter line 2.9 mm below
C_P1, C_W = 6.0, 70.0                   # c's row pitch (old 5b's) and its bar width
C_R1 = C_Y0 + 12.0                      # c's rows under its three key lines, as old 5b's
H = round(C_R1 + 6 * C_P1 + 8.4, 1)     # c's axis text ends inside the last 8.4 mm (finish_plate); d's must too (draw)
D_LET = 97.0                            # d (old Figure 6e, D298): its letter, right of c's n column
KINDS = ("signal", "verdict")
MARKS_MM = (1.25, 1.1)                  # fig5.md 5d: hs.MARK_MM, and the size to fall back on
IMPORTS = ("S497_fig5_d166.py", "S540_fig5_evaluators.py", "house_style.py", "figure_names.py", "minicheck_filter.py",
           "S473_fig5_panels.py", "S457_fig2_panels.py", "S463_fig2_ranking.py", "fig_repro.py", "judge_rows_v25.py",
           "S564_claimify_selection.py")


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S497 = _load("S497", ROOT / "scripts" / "S497_fig5_d166.py")
hs, S540, S473, FN = S497.hs, S497.S540, S497.S473, S497.FN
CONFIGS, OTHERS, LABEL, SIGS = S497.CONFIGS, S497.OTHERS, S497.LABEL, S497.SIGS
P2 = 7.6                                # panel b's row pitch, as old 5e
PASS_T = S473.PASS_T


def sheets(dat: dict) -> dict:
    a = {"columns": ["strategy", "every_concept_judge_pass", "every_concept_judge_fail", "every_concept_n"], "rows": []}
    for c in CONFIGS:
        p, f = dat["C"][c]["pass"], dat["C"][c]["fail"]
        a["rows"].append([LABEL[c], p, f, p + f])
    b = {"columns": ["strategy", "reference", "signal", "draw", "wins", "ties", "losses", "questions_with_both",
                     "margin_pct"],
         "rows": [[LABEL[x["strategy"]], LABEL[x["reference"]], x["signal"], x["draw"], x["wins"], x["ties"], x["losses"],
                   x["n"], x["margin_pct"]] for x in dat["E_DRAWN"]]}
    c = {"columns": S497.VERDICT_COLS,
         "rows": [[LABEL[x]] + list(dat["B"][x]) + [dat["b_median"]] for x in CONFIGS]}
    return {f"Supplementary Fig. {N}a": a, f"Supplementary Fig. {N}b": b, f"Supplementary Fig. {N}c": c,
            f"Supplementary Fig. {N}d": {"columns": S497.PAPERS_FAITH_COLS, "rows": []}}   # filled as d is drawn


def place_marks(drawn: list, x_mm: float, msz: float) -> tuple:
    """Each strategy's marks on its row, as old 5e placed them: each signal at its own height, a mark closer than one
    marker width to one already placed tried up and down. Returns (marks, closest gap); a mark is (strategy index, signal,
    margin_pct, offset from the row's centre in mm). Any mark too close to its row's edge stops the build."""
    sub_off, dodge = {"judge": -1.7, "concept": 0.0, "papers": 1.7}, 1.25
    marks, gaps = [], []
    for i, c in enumerate(OTHERS):
        placed = []
        for s in SIGS:
            pts = sorted([x for x in drawn if x["strategy"] == c and x["signal"] == s], key=lambda z: z["draw"])
            tries = (0.0, -dodge, dodge) if s != "papers" else (0.0, dodge, -dodge)
            for x in pts:
                xm = (x["margin_pct"] + 100) * x_mm
                best = None
                for off in tries:
                    y = sub_off[s] + off
                    gap = min([((xm - px) ** 2 + (y - py) ** 2) ** 0.5 for px, py in placed] + [9e9])
                    if gap >= msz * 0.98:
                        best = (y, gap)
                        break
                    if best is None or gap > best[1]:
                        best = (y, gap)
                half = msz * (2 ** 0.5 if s == "papers" else 1) / 2
                if abs(best[0]) + half >= P2 / 2 - 0.2 + 1e-9:
                    raise S540.Refused(f"S16 b: {c} {s}: a mark at {best[0]:.2f} mm leaves its row")
                gaps.append(best[1])
                placed.append((xm, best[0]))
                marks.append((i, s, x["margin_pct"], best[0]))
    return marks, min(gaps)


def fit_marks(drawn: list, x_mm: float) -> tuple:
    """place_marks at the marks' size, then at the fallback. Past that the build refuses."""
    for msz in MARKS_MM:
        marks, gap = place_marks(drawn, x_mm, msz)
        if gap >= msz * 0.98:
            return marks, gap, msz
    raise S540.Refused(f"S16 b: two marks are {gap:.2f} mm apart at {msz} mm")


def draw(dat: dict, sh: dict):
    hs.apply_rc("S543")
    hs.check_plate_kinds(KINDS)
    pl = S497.Page(W, H)
    tw = hs._text_width_mm
    g = S497.d200_layout()
    LABW, P1 = g["LABW"], 5 * P2 / 6                   # a's six rows end level with b's five
    # a
    pl.letter(0, 2.9, "a")
    x0, w, nr = LABW + 1.8, 27.5, 58.0
    fail, pas = hs.colour("verdict", "judge fails"), hs.colour("verdict", "judge passes")
    hs.key(pl.fig, [("swatch", fail, "judge fails"), ("swatch", pas, "judge passes")], centre_x=x0 + w / 2, y=2.9)
    pl.t(nr, 2.9 + 2 * g["LINE"], "n, all concepts", ha="right")
    totals = [dat["C"][c]["pass"] + dat["C"][c]["fail"] for c in CONFIGS]
    xmax = max(totals) * 1.25 + 1
    ax = pl.ax(x0, R1, w, 6 * P1, (0, xmax), (6, 0))
    step = 10 if xmax <= 60 else 20
    ax.set_xticks(list(range(0, int(xmax) + 1, step)))
    ax.set_xlabel("Answers with every concept (n)", labelpad=1.5)
    mm = w / xmax
    name = f"Supplementary Fig. {N}a"
    for i, c in enumerate(CONFIGS):
        yc = R1 + (i + 0.5) * P1
        pl.t(LABW, yc, LABEL[c], ha="right", va="center_baseline", why="strategy name")
        p, f = dat["C"][c]["pass"], dat["C"][c]["fail"]
        hs.bar(ax, i + 0.5, [p, f], [pas, fail], slot=4.0 / P1 / hs.BAR_FRAC)
        if p:
            pl.t(x0 + p / 2 * mm, yc, str(p), ha="center", va="center_baseline", color=hs.ink_on(pas),
                 printed={"sheet": name, "row": i, "format": "{every_concept_judge_pass}"})
        pr = {"sheet": name, "row": i, "format": "{every_concept_judge_fail}"}
        if f and f * mm >= tw(str(f)) + 0.6:
            pl.t(x0 + (p + f / 2) * mm, yc, str(f), ha="center", va="center_baseline", color=hs.ink_on(fail), printed=pr)
        else:
            pl.t(x0 + (p + f) * mm + 0.6, yc, str(f), va="center_baseline", printed=pr)
        pl.t(nr, yc, str(p + f), ha="right", va="center_baseline",
             printed={"sheet": name, "row": i, "format": "{every_concept_n}"})
    # b
    let, labr, xb, xe, top = 62.0, 84.0, 86.0, 180.6, R1
    pl.letter(let, 2.9, "b")
    names = {"judge": FN.JUDGE, "concept": FN.CONCEPTS, "papers": FN.PAPERS}
    hs.key(pl.fig, [("mark", (hs.colour("signal", n), hs.marker("signal", n)), n) for n in names.values()],
           centre_x=(xb + xe) / 2, y=2.9, gap=3.0)
    pl.t(xb, 2.9 + g["LINE"], "single pass better")
    pl.t(xe, 2.9 + g["LINE"], "strategy better", ha="right")
    fw = xe - xb
    ax = pl.ax(xb, top, fw, 5 * P2, (-100, 100), (5 * P2, 0))
    ax.set_xticks([-100, -50, 0, 50, 100], [hs.fmt_num(v) for v in (-100, -50, 0, 50, 100)])
    ax.set_xlabel("Strategy minus single pass (% of questions)", labelpad=1.5)
    hs.reference_line(ax, 0)
    for i in range(1, 5):
        ax.plot([-100, 100], [i * P2] * 2, color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0, clip_on=False)
    for i, o in enumerate(OTHERS):
        pl.t(labr, top + (i + 0.5) * P2, LABEL[o], ha="right", va="center_baseline", why="strategy name")
    marks, gap, msz = fit_marks(dat["E_DRAWN"], fw / 200.0)
    for i, s, v, off in marks:
        mk = hs.marker("signal", names[s])
        ax.plot([v], [(i + 0.5) * P2 + off], ls="none", marker=mk, ms=msz * hs.MARKER_SCALE[mk] / hs.MM_PT,
                mfc=hs.colour("signal", names[s]), mec=hs.WHITE, mew=0.3, zorder=3, clip_on=False)
    pl.mark_mm, pl.mark_gap = msz, gap
    # c: old Figure 5b, the strategies' names on its rows
    for i, c in enumerate(CONFIGS):
        pl.t(LABW, C_R1 + (i + 0.5) * C_P1, LABEL[c], ha="right", va="center_baseline", why="strategy name")
    drawn, unprinted = {"rows": []}, []
    S497.draw_verdict_papers(pl, dat, drawn, unprinted, let=0.0, x0=LABW + 1.8, w=C_W, y0=C_Y0, r1=C_R1, p1=C_P1,
                             line=g["LINE"], letter="c", sheet_name=f"Supplementary Fig. {N}c")
    if drawn["rows"] != sh[f"Supplementary Fig. {N}c"]["rows"]:
        raise S540.Refused(f"Supplementary Figure {N}c: the drawn rows differ from sheet c")
    pl.c_unprinted = unprinted
    # d: old Figure 6e (D298), right of c, its rows from c's letter line down, its n column at the page's right edge
    d_sheet = sh[f"Supplementary Fig. {N}d"]
    d_sheet["rows"] = []
    if D_LET < LABW + 1.8 + C_W + 1.2 + max(tw("(n)"), tw("888")) + 2.0:
        raise S540.Refused(f"Supplementary Figure {N}d's letter at {D_LET} mm is inside c's n column")
    if C_Y0 + 4.4 + 12 * g["SP"] + 5 * g["GG"] + g["PAD"] > H + 1e-9:
        raise S540.Refused(f"Supplementary Figure {N}d's axis passes the plate's bottom ({H} mm)")
    S497.draw_papers_by_faithfulness(pl, dat, g, d_sheet, let=D_LET, y0=C_Y0,
                                     nx=W - 0.2 - max(tw("(n)"), tw("88")), letter="d",
                                     sheet_name=f"Supplementary Fig. {N}d")
    if not pl.printed:
        raise S540.Refused("the printed map is empty (build order F7)")
    bad = hs.check_figure_colours(pl.fig)
    if bad:
        raise S540.Refused(f"Supplementary Figure {N}: colours outside the house palette: {bad}")
    return pl


def b_papers_n(dat: dict) -> str:
    """The Papers n of panel b, from the marks: one number, or each strategy's where they differ."""
    return S497.papers_n({x["strategy"]: x["n"] for x in dat["E_DRAWN"] if x["signal"] == "papers"})


def legend(dat: dict, R: dict) -> str:
    C = dat["C"]
    n = sum(C[c]["pass"] + C[c]["fail"] for c in CONFIGS)
    if dat["b_median"] is None:         # Papers waits (S497.blank_papers)
        c_na, c_med = S497.PENDING, S497.PENDING
    else:
        c_na, c_med = len(dat["pts_b"]), S497.S457.half_up(dat["b_median"], 3)
    d_n, d_nq = (S497.PENDING, S497.PENDING) if dat["G_N"] is None else (dat["G_N"], dat["G_NQ"])
    # D295: c is old Figure 5b, its clause moved from Figure 6's legend; a's answers are c's, and b's counterpart is
    # Figure 6c (old 5d). D298: d is old Figure 6e, its clause moved from Figure 6's legend with the faithfulness
    # definition it shared there with Figure 6d, and the box spelled out
    f_ctx = S497.faith_left_out(dat, R)["ctx"]
    return (f"**Supplementary Figure {N} | Answers stating every concept; each strategy against single pass; Papers "
            "by the judge's verdict and by faithfulness.** Answers "
            "of gemini-3-flash to the answerable questions. **a**, Of the draw-1 answers of c, those that "
            f"state every key concept, by the judge's verdict (n = {n}); n at right counts only these answers. "
            # S3 (7 Nov): the count of RLM fails at score 3 is a result, left to the text and sheet a
            f"**b**, Questions won minus lost against "
            f"single pass, as a percentage of n = {len(dat['qw'])} questions (Papers, {b_papers_n(dat)}), one mark per draw "
            f"(Papers, draw 1). The judge compares 0 to 5 scores, and the marks show how far each draw moves. Figure "
            f"{S497.FIG_N}c gives the same comparison as counts on three-draw means. "
            f"**c**, Draw-1 answers to {len(dat['qw'])} questions (n = {c_na} answers) by the judge's verdict and "
            f"Papers: high, at or above their median ({c_med}). "
            f"**d**, Papers of draw-1 answers with faithfulness 5 and below 5 (n = {d_n} answers, {d_nq} questions; n at "
            "right). Faithfulness score, from the judge with the retrieved passages; calls longer than the judge's "
            f"context are refused ({f_ctx}). Dots, answers; box, quartiles; black line, median; whiskers, range.")


def figure(out, set_dir=None) -> None:
    with tempfile.TemporaryDirectory(prefix="S543_") as t:
        R, dat, srcs, d200 = S497.d200_data(Path(t), set_dir)
        fn = R["fn"]
        n4, m = fn["all4"], S473.PLANNED["papers"]
        tag = f"provisional, {n4} of {m}"
        stamp = (f"PROVISIONAL: {n4} of {m} draw-1 answerable answers have a final row from all four scorers; numbers "
                 "from S497's panel_data on the claim-filtered rows")
        sh = sheets(dat)
        cap = (f"# Supplementary Figure {N} data, caption\n\n**Supplementary Figure {N} data.** Provisional. Data stamp: "
               f"{stamp}. Sheet a: per strategy the draw-1 answers that state every key concept, by the judge's verdict. "
               "Sheet b: per strategy, signal and draw against single pass, the wins, ties, losses, questions and the "
               "margin. Sheet c: per strategy the draw-1 answers in the four groups of the judge's verdict and Papers "
               "against the pooled median. Sheet d: per strategy and faithfulness group (5, 0 to 4) a summary row (n, "
               "quartiles, median, whisker ends at the range) and one row per plotted draw-1 answer with its Papers "
               f"value. Generated by `uv run --frozen python {SCRIPT} figure`.\n")
        pl = draw(dat, sh)
        notes = ("- b: margin = (wins minus losses) / (wins + ties + losses) x 100, draw against the same draw of single "
                 "pass, on the W questions where both values exist. Judge compares 0 to 5 scores; Figure "
                 f"{S497.FIG_N}a's Judge is at score {PASS_T}. Marks {pl.mark_mm} mm; marks closer than one marker width are moved up or down, closest "
                 f"centres {pl.mark_gap:.2f} mm apart.\n"
                 + ("- c: Papers waits; the panel is empty." if dat["b_median"] is None else
                    f"- c: Papers high: at or above {dat['b_median']:.4f}, the median of all {len(dat['pts_b'])} draw-1 "
                    f"answers pooled; the {dat['b_on']} answers on it count as high. Counts too narrow for their segment "
                    "are not printed and stay in the sheet: "
                    + (", ".join(f"{a_} {k_.replace('_', ' ')} {v_}" for a_, k_, v_ in pl.c_unprinted) or "none")
                    + ".")
                 + "\n- d: answers with a scored faithfulness call and a Papers value (draw 1); the answers Figure "
                 f"{S497.FIG_N}d leaves out (no text, or a call longer than the judge's context) are left out here too. "
                 "A group under 5 answers shows dots and its median tick.")
        S540.write_supp(out, N, tag, stamp, pl, sh, legend(dat, R), cap, script=SCRIPT, imports=IMPORTS,
                        inputs={**srcs["sha"], **d200["sha"]}, notes=notes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    S473.FR.pin_hash_seed()
    figure(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
