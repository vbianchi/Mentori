#!/usr/bin/env python3
"""S531 - Figure 2 and Supplementary Figure 3, in one of three modes (fig2.md sections 1 to 5).

MODES.
  --raters 0  frames. Axes, ticks, labels, keys, reference lines and cell grids, and no box, dot, bar, hexagon, count or
              printed value. The workbooks hold every row key and no value. This mode imports neither S500 nor S510 and
              opens nothing under the rating folders or findings/recompute/ (the test proves it under an audit hook). Its
              output is committed, and rebuilds byte for byte.
  --raters 1  one rater, on Valerio's word: reads S530's output for one rater. 2e keeps one lane per dimension and loses
              its Delta axis; S3's reliability panel goes and the letters shift up one; S3b's second rater goes. Labels
              read Rater. Output stays in the git-ignored folder.
  --raters 2  two raters, after the deadline: reads S530's output. Alpha below the gate keeps the plate; the protocol's
              sentence (S08b:73-76) goes in Results, not in either legend (rulings page 6 Nov, FIG2-KRIPP: O1). Output
              stays in the git-ignored folder until --released.

Modes 1 and 2 draw only what S530 wrote: this script computes no statistic beyond hexagon counts for 2d, shares in 2b
and a band's median in 2c. S3b draws every row S530's s3b holds a summary for, the second judge's included (rulings page
6 Nov, SUPP3-B: O1): that summary is Spearman's rho of the second judge's score with each rater, so S530 computes it from
the ratings and this script reads no second-judge score of its own. While S530 writes the row empty, the row stays a
frame and the legend's closing line names it. The claim-level panel (one author's marks against the source papers) is
gone (D274): the rating window closed with no claim mark returned (D273), so the bias panel, once g, is now f.

RELEASE. Every mode 2 build prints its release tag, S531-release-<12 hex>: a hash of the two numbers files, so a tag names
exactly the cells that build holds. --released copies the two folders to findings/figures_provisional/ only in mode 2,
and only when the decision --on-word D<nnn> names holds that tag. Rater 2's per-answer columns need Dirkjan's yes after his
packet is back (fig2.md section 2), so --released also needs one of two things:
  --rater2-yes D<nnn>  a decision line that holds the same tag and the word Dirkjan;
  --without-rater2     the workbooks leave out rater 2's per-answer columns, and the two kinds of cell that would give them
                       back: the raters' per-answer means (rater 2 = 2 x mean - rater 1), and rater 1's per-answer
                       faithfulness, which with the band in sheet 2c bounds rater 2's. The plates do not change, and the
                       tag does, since the cells differ.

Modes 1 and 2 never write into the repository outside the git-ignored folder without --released: any other --out inside
the repository refuses (fig2.md section 2). Mode 1 reads only results that record Valerio's word (S530 --on-word).

    uv run --frozen python scripts/S531_fig2_s3_plates.py --raters 0
    uv run --frozen python scripts/S531_fig2_s3_plates.py --raters 1
    uv run --frozen python scripts/S531_fig2_s3_plates.py --raters 2 [--without-rater2]
    uv run --frozen python scripts/S531_fig2_s3_plates.py --raters 2 --released --on-word D<nnn> --rater2-yes D<nnn>
    uv run --frozen python scripts/S531_fig2_s3_plates.py --raters 2 --released --on-word D<nnn> --without-rater2

Writes, per plate: the PDF, SVG and PNG; the workbook and its caption; the numbers and provenance files; legend_draft.md.
Then check each folder with S448, as scripts/S531_fig2_s3_plates_test.py does.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import figure_names as fn  # noqa: E402
import house_style as hs  # noqa: E402
import pdf_font_determinism  # noqa: E402,F401  (D301: the plate prints a Greek rho; the same font subset every run)
import S08_human_eval_analysis as S08  # noqa: E402  (constants only: its import opens no rating)
import S457_fig2_panels as S457  # noqa: E402  (finish_plate, write_source_data)
from machine import RECOMPUTE  # noqa: E402

SCRIPT = "scripts/S531_fig2_s3_plates.py"
FIGURES = ROOT / "findings" / "figures_provisional"
RESULTS = RECOMPUTE / "S530_human_signals"
DRAFT = RECOMPUTE / "S531_plates"
FOLDERS = ("fig2_human", "supp_fig3")
N_ITEMS, N_BOOT, SEED = S08.V22_N_ITEMS, S08.V22_N_BOOT, S08.SEED
EVAL_IDS = [f"E{i:03d}" for i in range(1, N_ITEMS + len(S08.V22_WITHDRAWN) + 1) if f"E{i:03d}" not in S08.V22_WITHDRAWN]
WORD = {0: fn.RATERS, 1: fn.RATER_ONE_RATER_MODE, 2: fn.RATERS}
BAND_TICKS = ("<3", "3 to <4", "≥4")             # mock:170; fixed in every mode (FP r1 2.11)
BAND_TICKS_ONE = ("1-2", "3", "4-5")             # D206: one rater scores whole numbers, so the same bands read 1-2, 3, 4-5
WAITS_TEXT = "Waits for the heading rule"        # D206: f and S3d need Papers, which waits for the heading rule


def band_ticks(mode: int) -> tuple:
    return BAND_TICKS_ONE if mode == 1 else BAND_TICKS


def waits(res) -> bool:
    """D206: S530 ran with --papers-waits, so f, the grid and S3b's Papers row hold nothing yet."""
    return res is not None and res.get("f") is None
JUDGE_TICKS = ("0-2", "3", "4-5")                # mock:171
STATS = ("Weighted kappa", "Spearman's rho", "Kappa, pass at 4", "Kappa, pass at 3")
DIMS = ("correctness", "faithfulness")
BLUE, ORANGE = hs.OKABE["blue"], hs.OKABE["orange"]
FILL = hs.GREY["fill"]
TICKS = [-1, -0.5, 0, 0.5, 1]                    # mock:174-175
TICK_LABELS = [hs.fmt_num(v, 1 if v % 1 else 0) for v in TICKS]
HEX_GRID = 18
F_ROWS = (("J", fn.JUDGE), ("C", fn.CONCEPTS), ("M", fn.PAPERS), ("1of3", "At least 1 of 3"),
          ("2of3", "At least 2 of 3"), ("3of3", "All 3 of 3"))
F_YS = [5.5, 4.5, 3.5, 2.0, 1.0, 0.0]
PASS_MARKS = (4, 3)
RELIABILITY = ("Krippendorff's alpha", "ICC(2,1)", "Gwet's AC2", "Mean weighted kappa", "Exact agreement",
               "Adjacent agreement")
S3B_SIGNALS = (fn.JUDGE, "Second judge", fn.CONCEPTS, f"{fn.CONCEPTS}, old matcher", fn.MINICHECK_AGAINST_KEY, fn.PAPERS,
               f"{fn.PAPERS}, no source-list filter")
EVALUATORS = ("ROUGE-L", "METEOR", "Number overlap", "bge-m3 similarity", fn.JUDGE)
CUTS_C, CUTS_M = (0.33, 0.5, 0.67, 1.0), (0.5, 0.67, 0.8, 1.0)
S3D_BLOCKS = ((4, 4), (4, 3), (3, 4), (3, 3))     # judge bar, rater bar
PRIMARY_CELL = (4, 4, 0.5, 0.5)                   # S08b:294; a frame reads no result, a filled plate reads S530's flag
SUMMARY = ("point", "ci95_low", "q25", "median", "q75", "ci95_high")
WITHHELD = {"Fig. 2c": ("r2_correctness", "r2_faithfulness", "raters_correctness", "raters_faithfulness",
                        "r1_faithfulness"),   # a mean gives rater 2 back; r1 with the faithfulness band bounds it
            "s3c": ("r2_completeness",)}      # --without-rater2 (S3c holds no mean and no band)
FIG2_W, FIG2_H, S3_W, S3_H = 183.0, 166.0, 183.0, 138.0


class Refused(Exception):
    """Refused: nothing is written."""


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- drawing helpers

def letter(fig, x, y, ch):
    hs.panel_letter(fig, x + 0.5, y, ch)


def box(ax, y, s, fill, h, point=False, diamond=2.0):
    """f-mock:201-212: quartiles, median, whiskers to the 95% interval, on request a diamond for the estimate on all
    answers. hs.boxplot has no fill. A statistic with no finite resample draws nothing."""
    from matplotlib.patches import Rectangle
    lo, hi = s["ci95"]
    if lo is None or hi is None or lo != lo or hi != hi:
        return
    line = {"color": hs.BLACK, "solid_capstyle": "butt", "zorder": 4}
    ax.plot([lo, s["q25"]], [y, y], lw=hs.LW["whisker"], **line)
    ax.plot([s["q75"], hi], [y, y], lw=hs.LW["whisker"], **line)
    ax.add_patch(Rectangle((s["q25"], y - h / 2), s["q75"] - s["q25"], h, facecolor=fill, edgecolor=hs.BLACK,
                           lw=hs.LW["box"], zorder=3))
    ax.plot([s["median"]] * 2, [y - h / 2, y + h / 2], lw=hs.LW["median"], **line)
    if point and s.get("point") is not None:
        ax.plot([s["point"]], [y], "D", ms=diamond, mfc=hs.BLACK, mec="none", mew=0, zorder=5)


def vbox(ax, x, s, fill, w):
    """box() turned upright: the statistic on y, one box at x (Supplementary Fig. 3f, Valerio's comment of 6 Nov)."""
    from matplotlib.patches import Rectangle
    lo, hi = s["ci95"]
    if lo is None or hi is None or lo != lo or hi != hi:
        return
    line = {"color": hs.BLACK, "solid_capstyle": "butt", "zorder": 4}
    ax.plot([x, x], [lo, s["q25"]], lw=hs.LW["whisker"], **line)
    ax.plot([x, x], [s["q75"], hi], lw=hs.LW["whisker"], **line)
    ax.add_patch(Rectangle((x - w / 2, s["q25"]), w, s["q75"] - s["q25"], facecolor=fill, edgecolor=hs.BLACK,
                           lw=hs.LW["box"], zorder=3))
    ax.plot([x - w / 2, x + w / 2], [s["median"]] * 2, lw=hs.LW["median"], **line)


def grid_cells(ax, g, gid: str, sheet: str, printed: dict, ticks=BAND_TICKS):
    """3 x 3 cells: white with a grey edge and no number in a frame (g None); else cividis, yellow more, a white edge,
    the count in hs.ink_on. The agreeing cells carry a black outline in every mode."""
    from matplotlib.patches import Rectangle
    top = 1 if g is None else max(max(max(r) for r in g), 1)
    for jb in range(3):
        for rb in range(3):
            v = None if g is None else g[jb][rb]
            col = hs.WHITE if g is None else hs.cividis_value(v, 0, top)
            cell = Rectangle((rb, jb), 1, 1, facecolor=col, edgecolor=hs.GREY["line"] if g is None else hs.WHITE,
                             lw=hs.LW["box"] if g is None else 1.0)
            cell.set_gid(f"{gid}_cell_{jb}_{rb}")
            ax.add_patch(cell)
            if g is not None:
                t = ax.text(rb + 0.5, jb + 0.5, str(v), ha="center", va="center", color=hs.ink_on(col))
                t.set_gid(f"{gid}_n_{jb}_{rb}")
                printed[t.get_gid()] = {"sheet": sheet, "row": 3 * jb + rb, "format": "{answers}",
                                        "inside": {"gid": cell.get_gid(), "path": 0}}
    for k in range(3):
        ax.add_patch(Rectangle((k, k), 1, 1, fill=False, edgecolor=hs.BLACK, lw=1.0))
    ax.set_xlim(0, 3), ax.set_ylim(0, 3)
    ax.set_xticks([0.5, 1.5, 2.5], ticks), ax.set_yticks([0.5, 1.5, 2.5], JUDGE_TICKS)


def hex_counts(x, y) -> dict:
    """Hexagons of the resamples (fig2:56): matplotlib's hexbin for the counts, in a figure of its own. The panel draws
    one Polygon per hexagon, since a hexbin collection failed S448 R10 on the prototype."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    hb = ax.hexbin(x, y, gridsize=HEX_GRID, mincnt=1, extent=(-1, 1, -1, 1))
    out = {"offsets": hb.get_offsets().tolist(), "counts": [int(c) for c in hb.get_array()],
           "verts": hb.get_paths()[0].vertices.tolist()}
    plt.close(fig)
    return out


def hex_panel(ax, hx) -> None:
    from matplotlib.patches import Polygon
    mx = max(hx["counts"])
    for (ox, oy), c in zip(hx["offsets"], hx["counts"]):
        ax.add_patch(Polygon([(vx + ox, vy + oy) for vx, vy in hx["verts"]], closed=True,
                             facecolor=hs.cividis_value(c, 1, mx), edgecolor="none", lw=0, zorder=1))


def colour_key(fig, y0, hex_max, printed):
    """2d's key above the axes: its word, the vector bar, and in a filled plate 1 and the largest count below the bar."""
    hs.text_mm(fig, 5, y0 + 2.8, "Resamples")
    hs.vector_colourbar(fig, y0 + 0.9, 14, 1, 2 if hex_max is None else max(hex_max, 2), [], [], x_left=20)
    if hex_max is not None:
        lo = hs.text_mm(fig, 20, y0 + 6.6, "1", ha="left")
        lo.set_gid("d_key_lo")
        printed["d_key_lo"] = {"fixed": "1", "why": "the colour key's lower end"}
        hi = hs.text_mm(fig, 34, y0 + 6.6, str(hex_max), ha="right")
        hi.set_gid("d_key_hi")
        printed["d_key_hi"] = {"sheet": "Fig. 2d", "row": 0, "format": "{hex_max}"}


def fixed_ids(fig, prefix: str, printed: dict) -> None:
    """Every fig-level text with a digit and no gid yet gets one and a fixed entry (fig2:80)."""
    k = 0
    for t in fig.texts:
        s = t.get_text()
        if s and re.search(r"\d", s) and not t.get_gid():
            k += 1
            t.set_gid(f"{prefix}{k}")
            printed[t.get_gid()] = {"fixed": s, "why": "a label of the design, no data"}


# ---------------------------------------------------------------- Figure 2

def panel_a(fig, x0, y0, mode, res, printed):
    letter(fig, x0, y0 + 2.8, "a")
    ax = hs.axes_mm(fig, x0 + 15, y0 + 8, 40, 35)
    grid_cells(ax, None if res is None else res["a"]["grid"], "a", "Fig. 2a", printed, band_ticks(mode))
    ax.set_xlabel(f"{WORD[mode]}, correctness"), ax.set_ylabel("Judge, correctness")


def panel_b(fig, x0, y0, mode, res, printed):
    letter(fig, x0, y0 + 2.8, "b")
    bc = hs.cividis_levels(3)
    ax = hs.axes_mm(fig, x0 + 15, y0 + 8, 40, 35)
    ax.set_ylim(0, 100), ax.set_xlim(-0.6, 2.6)
    if res is not None:
        for b, row in enumerate(res["b"]["grid"]):
            tot = sum(row)
            shares = [100 * v / tot if tot else 0 for v in row]
            labels = [hs.fmt_num(s) if s >= 9 else None for s in shares]
            art = hs.bar(ax, b, shares, bc, orient="v", labels=labels)
            at = iter(art["texts"])
            for k, lab in enumerate(labels):
                if lab is not None and shares[k] > 0:
                    t = next(at)
                    t.set_gid(f"b_pct_{b}_{k}")
                    printed[t.get_gid()] = {"sheet": "Fig. 2b", "row": 3 * b + k, "format": "{share_pct:.0f}"}
            t = ax.text(b, 101.5, str(tot), ha="center", va="bottom", clip_on=False)
            t.set_gid(f"b_n_{b}")
            printed[t.get_gid()] = {"sheet": "Fig. 2b", "row": 3 * b, "format": "{band_n}"}
    ax.set_xticks(range(3), band_ticks(mode)), ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel(f"{WORD[mode]}, faithfulness"), ax.set_ylabel("Share of answers (%)")
    hs.key(fig, [("swatch", c, lab) for c, lab in zip(bc, JUDGE_TICKS)], centre_x=x0 + 37, y=y0 + 2.8, title=fn.JUDGE)


def panel_c(fig, x0, y0, mode, res, printed):
    letter(fig, x0, y0 + 2.8, "c")
    ax = hs.axes_mm(fig, x0 + 15, y0 + 8, 40, 35)
    ax.set_xlim(-0.6, 2.6), ax.set_ylim(0, 1)
    small = False
    if res is not None:
        for b in range(3):
            v = [p["minicheck_key_precision"] for p in res["per_answer"] if p["band_faithfulness"] == b]
            if len(v) >= hs.SMALL_N:
                hs.boxplot(ax, b, values=v, orient="v", whis="range", dot_mm=hs.DOT_SPARSE_MM)   # Q3, 2 Nov: range
            elif v:
                import numpy as np
                small = True
                hs.strip(ax, b, v, orient="v", size_mm=hs.DOT_SPARSE_MM)
                hs.summary_tick(ax, b, float(np.median(v)), orient="v")
    ax.set_xticks(range(3), band_ticks(mode)), ax.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0", "0.25", "0.5", "0.75", "1"])
    ax.set_xlabel(f"{WORD[mode]}, faithfulness"), ax.set_ylabel(fn.MINICHECK_AGAINST_KEY)
    return small


def _ptext(fig, x, y, s, gid, entry, printed):
    t = hs.text_mm(fig, x, y, s, ha="left")
    t.set_gid(gid)
    printed[gid] = entry


def signed(v, nd=2):
    """F6's two columns: the sign as text, the size as a number, so R8 ties the digits to a cell."""
    txt = hs.fmt_num(v, nd, sign=True)
    return ("", abs(float(v))) if txt[0] not in "+" + hs.MINUS else (txt[0], abs(float(v)))


def panel_d(fig, x0, y0, mode, res, printed, hx):
    letter(fig, x0, y0 + 2.8, "d")
    ax = hs.axes_mm(fig, x0 + 15, y0 + 8, 36, 36)
    colour_key(fig, y0, None if hx is None else max(hx["counts"]), printed)
    ax.plot([-1, 1], [-1, 1], color=hs.BLACK, lw=hs.LW["reference"], zorder=2)
    if res is not None:
        hex_panel(ax, hx)
        d = res["d"]
        ax.plot([d["rho_minicheck"]["point"]], [d["rho_judge"]["point"]], "D", ms=2.4, mfc=hs.BLACK, mec=hs.WHITE, mew=0.3,
                zorder=5)
        # D (rho_judge minus rho_minicheck) and its interval stay in sheet Fig. 2d, not on the plate (Valerio, tab, 7 Nov)
    ax.set_xlim(-1, 1), ax.set_ylim(-1, 1)
    ax.set_xticks(TICKS, TICK_LABELS), ax.set_yticks(TICKS, TICK_LABELS)
    ax.tick_params(pad=3.0)
    ax.set_xlabel(f"ρ with {fn.MINICHECK_AGAINST_KEY}"), ax.set_ylabel("ρ with the judge")


def panel_e(fig, x0, y0, mode, res, printed):
    """fig2.md section 3: one axis for agreement, a narrow Delta axis in modes 0 and 2. Rows top to bottom as STATS."""
    letter(fig, x0, y0 + 2.8, "e")
    two = mode != 1
    top, h = 6.5, 36.0
    ax = hs.axes_mm(fig, 85, y0 + top, 60 if two else 92, h)   # 11 Nov (F3): 60 and the Delta axis at 154 (was 62 and
                                                              # 152), so the 1 and the minus 2 stand clearly apart
    ax.set_ylim(-0.5, 3.5), ax.set_xlim(-1, 1)
    hs.reference_line(ax, 0)
    for i, st in enumerate(STATS):
        y = 3 - i
        if st != "Spearman's rho":                  # FP r2 2.2 a: the 0.6 line on the three kappa rows only
            ax.plot([0.6, 0.6], [y - 0.46, y + 0.46], color=hs.GREY["text"], lw=hs.LW["reference"], dashes=hs.DASH,
                    zorder=1)
        if res is None:
            continue
        c, f = res["e"]["correctness"][st], res["e"]["faithfulness"][st]
        if two:
            box(ax, y + 0.33, c["judge"], BLUE, 0.17, True)
            box(ax, y + 0.11, c["raters"], hs.WHITE, 0.17, True)
            box(ax, y - 0.11, f["judge"], ORANGE, 0.17, True)
            box(ax, y - 0.33, f["raters"], hs.WHITE, 0.17, True)
        else:
            box(ax, y + 0.17, c["judge"], BLUE, 0.28, True)
            box(ax, y - 0.17, f["judge"], ORANGE, 0.28, True)
    ax.set_yticks([3, 2, 1, 0], [x.replace("rho", "ρ") for x in STATS])   # 7 Nov: one form, Spearman's ρ
    ax.set_xticks(TICKS, TICK_LABELS)   # 11 Nov (F3): this call had slipped into the comment above, so matplotlib's own
                                        # labels (hyphen-minus, "-1.0") stood in for the U+2212 ones every other panel prints
    ax.tick_params(axis="y", length=2)
    ax.set_xlabel("Value of ρ or kappa")
    items = [("swatch", BLUE, "Correctness"), ("swatch", ORANGE, "Faithfulness")]
    if two:
        items += [("swatch", FILL, "Judge with raters"), ("swatch", hs.WHITE, "Raters with each other")]
    hs.key(fig, items, centre_x=126, y=y0 + 2.8)
    if two:
        ad = hs.axes_mm(fig, 154, y0 + top, 24, h)
        ad.set_ylim(-0.5, 3.5), ad.set_xlim(-2, 2)
        hs.reference_line(ad, 0)
        if res is not None:
            for i, st in enumerate(STATS):
                box(ad, 3 - i + 0.17, res["e"]["correctness"][st]["delta"], BLUE, 0.28)
                box(ad, 3 - i - 0.17, res["e"]["faithfulness"][st]["delta"], ORANGE, 0.28)
        ad.set_yticks([3, 2, 1, 0], [""] * 4), ad.tick_params(axis="y", length=2)
        ad.set_xticks([-2, 0, 2], [hs.fmt_num(v) for v in (-2, 0, 2)])
        ad.set_xlabel("Delta")


def panel_f(fig, x0, y0, mode, res, printed):
    """f-mock:166-177 with H = 50, and f-mock:215-223's boxes."""
    letter(fig, x0, y0 + 2.8, "f")
    H, top, bottom, w = 50.0, 6.0, 9.6, 67.0
    h = H - top - bottom
    who = "the rater" if mode == 1 else "the raters"
    a1, a2 = hs.axes_mm(fig, x0 + 29, y0 + top, w, h), hs.axes_mm(fig, x0 + 107, y0 + top, w, h)
    for ax, stat, lim, ticks, tl, label in (
            (a1, "accuracy", (0, 1), [0, 0.25, 0.5, 0.75, 1], ["0", "0.25", "0.5", "0.75", "1"],
             f"Accuracy, against {who}"),
            (a2, "kappa", (-1, 1), TICKS, TICK_LABELS, f"Cohen's kappa, against {who}")):
        ax.set_ylim(-0.6, 6.1), ax.set_xlim(*lim)
        ax.set_xticks(ticks, tl), ax.set_xlabel(label)
        ax.tick_params(axis="y", length=2)
        if res is not None and not waits(res):
            for j, (b, col) in enumerate(((4, BLUE), (3, ORANGE))):
                for y, (k, _) in zip(F_YS, F_ROWS):
                    box(ax, y + 0.18 - 0.36 * j, res["f"][str(b)][k][stat], col, 0.31)
        elif waits(res):
            ax.text(sum(lim) / 2, 2.75, WAITS_TEXT, ha="center", va="center", color=hs.GREY["text"])
    a1.set_yticks(F_YS, [r[1] for r in F_ROWS]), a2.set_yticks(F_YS, [""] * 6)
    hs.reference_line(a1, 0.5, dashed=True, color=hs.GREY["text"]), hs.reference_line(a2, 0)
    hs.text_mm(fig, x0 + 3.2, y0 + top + h / 2, "Signal or rule", rotation=90, ha="center", va="center")
    hs.key(fig, [("swatch", BLUE, "Pass at 4"), ("swatch", ORANGE, "Pass at 3")], centre_x=x0 + 88, y=y0 + 2.8)


def build_fig2(mode, res, hx):
    fig = hs.figure(FIG2_W, FIG2_H)
    printed: dict = {}
    panel_a(fig, 0, 0, mode, res, printed)
    panel_b(fig, 62, 0, mode, res, printed)
    small = panel_c(fig, 126, 0, mode, res, printed)
    panel_d(fig, 0, 56, mode, res, printed, hx)
    panel_e(fig, 60, 56, mode, res, printed)
    panel_f(fig, 0, 116, mode, res, printed)
    fixed_ids(fig, "fx", printed)
    return fig, printed, small


# ---------------------------------------------------------------- Supplementary Figure 3

def s3_a(fig, res, printed, L):
    L(0, 2.8)
    ax = hs.axes_mm(fig, 33, 7.0, 49, 27.0)
    ax.set_xlim(-1, 1), ax.set_ylim(5.5, -0.5)
    ax.set_yticks(range(6), RELIABILITY), ax.tick_params(axis="y", length=2)
    ax.set_xticks(TICKS, TICK_LABELS), ax.set_xlabel("Value, faithfulness")
    gate = S08.V22_ALPHA_GATE
    ax.plot([gate] * 2, [-0.46, 0.46], color=hs.BLACK, lw=hs.LW["reference"], dashes=hs.DASH, zorder=1)
    hs.key(fig, [("dash", (hs.BLACK, hs.LW["reference"]), f"Alpha gate, {gate}")], centre_x=57, y=2.8)
    hs.reference_line(ax, 0)
    if res is not None:
        for i, name in enumerate(RELIABILITY):
            box(ax, i, res["s3a"][name], FILL, 0.5)


def s3_b(fig, mode, res, printed, L):
    L(86, 2.8)
    xa, cw, gap = 127.0, 25.0, 3.0
    if mode != 1:
        hs.key(fig, [("swatch", FILL, "Rater 1"), ("swatch", hs.WHITE, "Rater 2")], centre_x=xa + cw + gap / 2, y=2.8)
    rows = {} if res is None else {(r["signal"], r["dimension"], r["rater"]): r["summary"] for r in res["s3b"]}
    for k, (dim, head) in enumerate(zip(DIMS, ("Correctness", "Faithfulness"))):
        x = xa + k * (cw + gap)
        hs.text_mm(fig, x + cw / 2, 6.6, head, ha="center")
        ax = hs.axes_mm(fig, x, 7.8, cw, 26.2)
        ax.set_xlim(-1, 1), ax.set_ylim(6.5, -0.5)
        ax.set_yticks(range(7), S3B_SIGNALS if k == 0 else [""] * 7), ax.tick_params(axis="y", length=2)
        ax.set_xticks([-1, 0, 1], [hs.fmt_num(v) for v in (-1, 0, 1)])
        hs.reference_line(ax, 0)
        for i, sig in enumerate(S3B_SIGNALS):
            s1, s2 = rows.get((sig, dim, 1)), rows.get((sig, dim, 2))
            if mode == 1 and s1:
                box(ax, i, s1, FILL, 0.5)
            elif mode == 2:
                if s1:
                    box(ax, i - 0.2, s1, FILL, 0.34)
                if s2:
                    box(ax, i + 0.2, s2, hs.WHITE, 0.34)
    hs.text_mm(fig, xa + cw + gap / 2, 41.8, "Spearman's ρ with the rater" if mode == 1
               else "Spearman's ρ with each rater", ha="center")


def s3_c(fig, mode, res, printed, L):
    y1 = 46.0
    L(0, y1 + 2.8)
    ax = hs.axes_mm(fig, 13, y1 + 5.0, 30, 17)
    grid_cells(ax, None if res is None else res["s3c"]["grid"], "c", sheet_name(mode, "c"), printed, band_ticks(mode))
    ax.set_xlabel(f"{WORD[mode]}, completeness"), ax.set_ylabel(fn.JUDGE)


def s3_d(fig, mode, res, printed, L):
    from matplotlib.patches import Rectangle
    y1 = 46.0
    L(54, y1 + 2.8)
    cw2, ch, gap = 6.0, 4.2, 5.0
    x0d = 67.0
    cells = {} if res is None or waits(res) else {(c["judge_bar"], c["rater_bar"], c["concepts_cut"], c["papers_cut"]): c
                                                  for c in res["grid"] if c["verdict"] == "correctness"}
    row_of = {key: i for i, key in enumerate(s3d_keys())}
    primary = primary_cell(res)
    who = "rater" if mode == 1 else "raters"
    for b, (jb, hb) in enumerate(S3D_BLOCKS):
        x = x0d + b * (4 * cw2 + gap)
        hs.text_mm(fig, x + 2 * cw2, y1 + 2.8, f"Judge {jb}, {who} {hb}", ha="center")
        ax = hs.axes_mm(fig, x, y1 + 5.0, 4 * cw2, 4 * ch, spines_on=())
        ax.set_xlim(0, 4), ax.set_ylim(4, 0)
        for i, ct in enumerate(CUTS_C):
            for j, mt in enumerate(CUTS_M):
                c = cells.get((jb, hb, ct, mt))
                acc = None if c is None else 100 * c["rules"]["2of3"]["accuracy"]
                col = hs.WHITE if acc is None else hs.cividis_value(acc, 0, 100)
                r = Rectangle((j, i), 1, 1, facecolor=col, edgecolor=hs.GREY["line"] if acc is None else hs.WHITE,
                              lw=hs.LW["box"])
                r.set_gid(f"d_cell_{b}_{i}_{j}")
                ax.add_patch(r)
                if acc is not None:
                    t = ax.text(j + 0.5, i + 0.5, hs.fmt_num(acc), ha="center", va="center", color=hs.ink_on(col))
                    t.set_gid(f"d_acc_{b}_{i}_{j}")
                    printed[t.get_gid()] = {"sheet": sheet_name(mode, "d"), "row": row_of[(jb, hb, ct, mt)],
                                            "format": "{accuracy:.0f}", "inside": {"gid": r.get_gid(), "path": 0}}
        ax.tick_params(axis="x", bottom=True, labelbottom=True, length=0)
        ax.set_xticks([0.5, 1.5, 2.5, 3.5], [f"{v:g}" for v in CUTS_M])
        if b == 0:
            ax.tick_params(axis="y", left=True, labelleft=True, length=0)
            ax.set_yticks([0.5, 1.5, 2.5, 3.5], [f"{v:g}" for v in CUTS_C])
        if primary[:2] == (jb, hb):
            ax.add_patch(Rectangle((CUTS_M.index(primary[3]), CUTS_C.index(primary[2])), 1, 1, fill=False,
                                   edgecolor=hs.BLACK, lw=1.0))
    if waits(res):
        hs.text_mm(fig, x0d + 2 * (4 * cw2) + 1.5 * gap, y1 + 5.0 + 2 * ch, WAITS_TEXT, ha="center",
                   color=hs.GREY["text"])
    hs.text_mm(fig, x0d + 2 * (4 * cw2) + 1.5 * gap, 74.5,
               "Papers cut-off (columns), Concepts cut-off (rows); 2 of 3 rule, accuracy (%)", ha="center")


def s3_e(fig, mode, res, printed, L):
    y2 = 80.0
    L(0, y2 + 2.8)
    ax = hs.axes_mm(fig, 30, y2 + 6.0, 85, 36.0)
    ax.set_xlim(-1, 1), ax.set_ylim(4.5, -0.5)
    ax.set_yticks(range(5), EVALUATORS), ax.tick_params(axis="y", length=2)
    who = "the rater" if mode == 1 else "the raters"
    ax.set_xticks(TICKS, TICK_LABELS), ax.set_xlabel(f"Spearman's ρ with {who}")
    hs.reference_line(ax, 0)
    hs.key(fig, [("swatch", BLUE, "Correctness"), ("swatch", ORANGE, "Faithfulness")], centre_x=72.5, y=y2 + 2.8)
    if res is not None:
        rows = {(r["evaluator"], r["dimension"]): r["summary"] for r in res["s3e"]}
        for i, ev in enumerate(EVALUATORS):
            box(ax, i - 0.17, rows[(ev, "correctness")], BLUE, 0.28, True)
            box(ax, i + 0.17, rows[(ev, "faithfulness")], ORANGE, 0.28, True)


def s3_f(fig, mode, res, printed, L):
    """The bias panel, g until D274 removed the claim-level panel; it takes f's place beside e."""
    y3 = 80.0
    L(124, y3 + 2.8)
    ax = hs.axes_mm(fig, 139, y3 + 6.0, 42, 36.0)
    ax.set_ylim(-1, 1), ax.set_xlim(-0.5, 1.5)
    ax.set_xticks([0, 1], ["Correctness", "Faithfulness"]), ax.tick_params(axis="x", length=2)
    who = "rater" if mode == 1 else "raters"
    ax.set_yticks(TICKS, TICK_LABELS)
    ax.set_ylabel(f"Judge minus {who}\n(score points)")
    hs.reference_line(ax, 0, orient="h")
    if res is not None:
        vbox(ax, 0, res["bias"]["correctness"], FILL, 0.5)
        vbox(ax, 1, res["bias"]["faithfulness"], FILL, 0.5)


def s3_letters(mode) -> dict:
    """Mode 1 draws no panel a, so each later letter shifts up one (fig2:27)."""
    names = "abcdef"
    return {k: (chr(ord(k) - 1) if mode == 1 else k) for k in names}


def sheet_name(mode, panel: str) -> str:
    return f"Supplementary Fig. 3{s3_letters(mode)[panel]}"


def build_s3(mode, res):
    fig = hs.figure(S3_W, S3_H)
    printed: dict = {}
    let = s3_letters(mode)

    def L_(panel):
        return lambda x, y: letter(fig, x, y, let[panel])
    if mode != 1:
        s3_a(fig, res, printed, L_("a"))
    s3_b(fig, mode, res, printed, L_("b"))
    s3_c(fig, mode, res, printed, L_("c"))
    s3_d(fig, mode, res, printed, L_("d"))
    s3_e(fig, mode, res, printed, L_("e"))
    s3_f(fig, mode, res, printed, L_("f"))
    fixed_ids(fig, "fx", printed)
    return fig, printed


# ---------------------------------------------------------------- sheets

def s(row, *keys):
    return [None if row is None else row.get(k) for k in keys]


def sumcols(x) -> list:
    if x is None:
        return [None] * len(SUMMARY)
    lo, hi = x["ci95"]
    return [x["point"], lo, x["q25"], x["median"], x["q75"], hi]


def s3d_keys() -> list:
    return [(jb, hb, c, m) for jb, hb in S3D_BLOCKS for c in CUTS_C for m in CUTS_M]


def primary_cell(res) -> tuple:
    """S3d's primary cell: the protocol's in a frame, S530's flag on a filled plate."""
    if res is None or waits(res):
        return PRIMARY_CELL
    hit = [(c["judge_bar"], c["rater_bar"], c["concepts_cut"], c["papers_cut"]) for c in res["grid"] if c["primary"]]
    if len(hit) != 1:
        raise Refused(f"S530's grid flags {len(hit)} primary cells, not one")
    return hit[0]


def sheets_fig2(mode, res, samples, hx, withhold=False) -> list:
    """fig2.md section 5, with 2d's printed text as F6's sign and size columns (build_order sections 1 and 4). withhold:
    WITHHELD's columns stay blank."""
    bt = band_ticks(mode)
    a = [[JUDGE_TICKS[j], bt[r], None if res is None else res["a"]["grid"][j][r]]
         for j in range(3) for r in range(3)]
    b = []
    for r in range(3):
        row = None if res is None else res["b"]["grid"][r]
        tot = None if row is None else sum(row)
        for j in range(3):
            n = None if row is None else row[j]
            b.append([bt[r], JUDGE_TICKS[j], n, None if n is None else (100 * n / tot if tot else 0.0), tot])
    c_cols = ["eval_id", "r1_correctness", "r2_correctness", "r1_faithfulness", "r2_faithfulness", "raters_correctness",
              "raters_faithfulness", "band_faithfulness", "judge_correctness", "judge_faithfulness",
              "minicheck_key_precision"]
    if res is None:
        c = [[e] + [None] * (len(c_cols) - 1) for e in EVAL_IDS]
    else:
        gone = WITHHELD["Fig. 2c"] if withhold else ()
        c = [[None if k in gone else p.get(k) if k != "band_faithfulness" else bt[p[k]] for k in c_cols]
             for p in res["per_answer"]]
    d_cols = ["resample", "rho_judge", "rho_minicheck", "D", "D_ci95_low", "D_ci95_high", "d_sign", "d_size",
              "ci_low_sign", "ci_low_size", "ci_high_sign", "ci_high_size", "hex_max"]
    if res is None:
        d = [["all answers"] + [None] * (len(d_cols) - 1)] + [[i] + [None] * (len(d_cols) - 1)
                                                              for i in range(1, N_BOOT + 1)]
    else:
        D = res["d"]["D"]
        lo, hi = D["ci95"]
        d = [["all answers", res["d"]["rho_judge"]["point"], res["d"]["rho_minicheck"]["point"], D["point"], lo, hi,
              *signed(D["point"]), *signed(lo), *signed(hi), max(hx["counts"])]]
        rj, rm, rd = (samples[f"d.{k}"] for k in ("rho_judge", "rho_minicheck", "D"))
        tidy = lambda v: None if v != v else float(v)                     # noqa: E731
        d += [[i + 1, tidy(rj[i]), tidy(rm[i]), tidy(rd[i])] + [None] * (len(d_cols) - 4) for i in range(len(rj))]
    e_cols = ["dimension", "statistic", "pair", "point", "ci95_low", "q25", "median", "q75", "ci95_high",
              "finite_resamples"]
    e = []
    for dim in DIMS:
        for st in STATS:
            for pair, key in (("judge with raters", "judge"), ("raters with each other", "raters"), ("Delta", "delta")):
                x = None if res is None else res["e"][dim][st][key]
                e.append([dim, st, pair, *sumcols(x), *s(x, "finite_resamples")])
    for dim in DIMS:
        x = None if res is None else res["bias"][dim]
        e.append([dim, "bias", "judge minus raters", *sumcols(x), *s(x, "finite_resamples")])
    f_cols = ["pass_mark", "row", "statistic", "n", "point", "ci95_low", "q25", "median", "q75", "ci95_high",
              "finite_resamples", "rule_right_single_wrong", "rule_wrong_single_right", "p_two_sided", "favours_rule"]
    f = []
    for mark in PASS_MARKS:
        for k, lab in F_ROWS:
            for stat in ("accuracy", "kappa"):
                cell = None if res is None or waits(res) else res["f"][str(mark)][k]
                x = None if cell is None else cell[stat]
                m = None if cell is None or stat != "accuracy" or k not in "JCM" else \
                    res["f"][str(mark)]["mcnemar_2of3_vs"][k]
                f.append([mark, lab, stat, None if cell is None else cell["n"], *sumcols(x), *s(x, "finite_resamples"),
                          *s(m, "rule_right_single_wrong", "rule_wrong_single_right", "p_two_sided", "favours_rule")])
    return [("Fig. 2a", ["judge_band", "rater_band", "answers"], a),
            ("Fig. 2b", ["rater_band", "judge_band", "answers", "share_pct", "band_n"], b),
            ("Fig. 2c", c_cols, c), ("Fig. 2d", d_cols, d), ("Fig. 2e", e_cols, e), ("Fig. 2f", f_cols, f)]


def sheets_s3(mode, res, withhold=False) -> list:
    """fig2.md section 5, with an n column on b and d, so each n the legend states stands in a cell. S3b's second judge
    holds what S530 wrote for it (SUPP3-B O1). S3f is the bias panel (D274). withhold: WITHHELD's columns stay blank."""
    out = []
    if mode != 1:
        out.append((sheet_name(mode, "a"), ["statistic", *SUMMARY],
                    [[k, *sumcols(None if res is None else res["s3a"][k])] for k in RELIABILITY]))
    rows = {} if res is None else {(r["signal"], r["dimension"], r["rater"]): r for r in res["s3b"]}
    b = []
    for sig in S3B_SIGNALS:
        for dim in DIMS:
            for r in (1, 2):
                row = rows.get((sig, dim, r))
                b.append([sig, dim, r, None if row is None else row["n"],
                          *sumcols(None if row is None else row["summary"])])
    out.append((sheet_name(mode, "b"), ["signal", "dimension", "rater", "n", *SUMMARY], b))
    c_cols = ["row_kind", "judge_band", "rater_band", "answers", "rho", "ci95_low", "ci95_high", "eval_id",
              "r1_completeness", "r2_completeness", "judge_completeness"]
    blank = [None] * len(c_cols)
    c = []
    for j in range(3):
        for r in range(3):
            row = list(blank)
            row[:4] = ["cell", JUDGE_TICKS[j], band_ticks(mode)[r], None if res is None else res["s3c"]["grid"][j][r]]
            c.append(row)
    rho = list(blank)
    rho[0] = "rho"
    if res is not None:
        x = res["s3c"]["rho"]
        rho[4:7] = [x["point"], *x["ci95"]]
    c.append(rho)
    for k, e in enumerate(EVAL_IDS if res is None else [p["eval_id"] for p in res["per_answer"]]):
        row = list(blank)
        row[0], row[7] = "answer", e
        if res is not None:
            p = res["per_answer"][k]
            row[8:11] = [p["r1_completeness"], None if withhold else p["r2_completeness"], p["judge_completeness"]]
        c.append(row)
    out.append((sheet_name(mode, "c"), c_cols, c))
    cells = {} if res is None or waits(res) else {(c_["judge_bar"], c_["rater_bar"], c_["concepts_cut"], c_["papers_cut"]): c_
                                                  for c_ in res["grid"] if c_["verdict"] == "correctness"}
    d = []
    primary = primary_cell(res)
    for key in s3d_keys():
        c_ = cells.get(key)
        d.append([*key, None if c_ is None else 100 * c_["rules"]["2of3"]["accuracy"],
                  "primary" if key == primary else None, None if c_ is None else c_["n"]])
    out.append((sheet_name(mode, "d"), ["judge_bar", "rater_bar", "concepts_cut", "papers_cut", "accuracy", "primary", "n"],
                d))
    rows = {} if res is None else {(r["evaluator"], r["dimension"]): r for r in res["s3e"]}
    e = []
    for ev in EVALUATORS:
        for dim in DIMS:
            r = rows.get((ev, dim))
            e.append([ev, dim, None if r is None else r["n"], *sumcols(None if r is None else r["summary"])])
    out.append((sheet_name(mode, "e"), ["evaluator", "dimension", "n", *SUMMARY], e))
    out.append((sheet_name(mode, "f"), ["dimension", "n", *SUMMARY],
                [[dim, None if res is None else res["n_analysed"], *sumcols(None if res is None else res["bias"][dim])]
                 for dim in DIMS]))
    return out


# ---------------------------------------------------------------- legends

FIG2_LEGEND = """Two authors rated {n} answers; the raters' score is their mean. Verified pass holds {vp} of the answers. **a**, Correctness: answers per pair of bands of the judge's score (rows) and the raters' score (columns), printed in each cell; outlined cells, agreeing bands. **b**, Faithfulness: share of each judge band within each band of the raters' score; the number of answers in each band is printed above its bar. **c**, MiniCheck against the key by the raters' faithfulness band; dots, every answer; box, quartiles; line, median; whiskers, range; n = {n} rated answers. **d**, Spearman's ρ of the raters' faithfulness with the judge's against that with MiniCheck, over {boot} resamples of the answers; colour, resamples per hexagon; diamond, the estimate on all answers; diagonal line, equal ρ. Source Data gives the difference of the two ρ with its two-sided 95% percentile interval. n = {n} rated answers. **e**, Agreement, judge with raters and raters with each other: quadratic-weighted kappa, Spearman's ρ and Cohen's kappa at pass marks 4 and 3, over {boot} resamples of the answers. Delta, the first minus the second. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval; diamond, the estimate on all answers; dashed line, kappa 0.6, reference only. n = {n} rated answers. **f**, Accuracy and Cohen's kappa of Judge; Concepts (concept recall) and Papers passing at 0.5; and the rules at least 1, 2 and 3 of 3, against the raters' correctness at the same pass mark, over {boot} resamples of the answers. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval; dashed line, accuracy 0.5, reference only. Source Data gives two-sided McNemar tests. {f_n}"""
# 8 Nov, 20:45Z (Valerio, editor row 45): an n only on a panel with derived statistics (c to f), "n = X rated answers",
# inside that panel; no n on a and b; every panel described in full, no "as in" or cross-panel letters.
# Shortened 8 Nov (Valerio: the legends "are too long"), 308 to 214 words. Gone from here, still in Methods: the run
# the 49 answers come from and that they were rated blind to the strategy ('Expert raters'), the resampling seed (42)
# and alpha 0.05 (statistics paragraph), "The raters judged support against the expert answer" ('Expert raters'), what
# MiniCheck against the key measures ('Claim checking'), refusal scoring ('LLM judge scoring'). In Source Data: d's
# interval, f's McNemar tests. Concepts and Papers (MiniCheck against the source papers) are defined in Figure 1's legend.

S3_LEGEND = """Two authors rated the {n} answers of Figure 2; the raters' score is their mean. **a**, Agreement of the two raters on faithfulness, six statistics (rows), over {boot} answer resamples. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval; dashed line, the gate on Krippendorff's alpha, {gate}. {n_a} **b**, Spearman's ρ of seven signals (rows) with each rater's correctness (left) and faithfulness (right), over {boot} answer resamples; grey, rater 1; white, rater 2; the second judge's row is exploratory, added after rating began. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval. {n_b} **c**, Completeness: answers per pair of bands of the judge's score (rows) and the raters' score (columns); colour, count, yellow for more; outlined cells, agreeing bands. **d**, Accuracy (%) of the 2 of 3 rule (pass when at least two of judge, Concepts and Papers pass) against the raters' correctness{d_on}, by Concepts cut-off (rows) and Papers cut-off (columns); blocks, the judge's and the raters' pass marks, 4 or 3; colour, accuracy, yellow for higher; outlined cell, the primary cell. **e**, Spearman's ρ of ROUGE-L, METEOR, number overlap, bge-m3 similarity and, for reference, the judge with the raters' correctness (blue) and faithfulness (orange), over {boot} answer resamples; exploratory, added after rating began. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval; diamond, the estimate on all answers. {n_e} **f**, Mean of the judge's score minus the raters' score (score points) for correctness and faithfulness, over {boot} answer resamples; exploratory. Box, quartiles; line, median; whiskers, two-sided 95% percentile interval; solid line, no difference. {n_f}"""
# 8 Nov (Valerio, editor row 45, extended to the Supplementary legends): an n only on a panel that draws derived
# statistics (a, b, e, f: boxes over resamples), "n = X rated answers" inside that panel; none on c and d (cells);
# every panel described in full, no shared resampling sentence, no cross-panel letter. The seed (42) is in Methods.

FIG2_SHEET_TEXT = {   # D309 A69: Source Data Fig. 2 caption, one entry per sheet of sheets_fig2
    "Fig. 2a": ("One row per pair of bands, the judge's correctness score (judge_band: 0-2, 3, 4-5) and the raters' "
                "correctness score (rater_band: <3, 3 to <4, ≥4); answers, the number of answers in that pair."),
    "Fig. 2b": ("One row per band of the raters' faithfulness score (rater_band) and band of the judge's faithfulness "
                "score (judge_band); answers, the number in that pair; share_pct, their share of the rater band (%); "
                "band_n, the answers in the rater band."),
    "Fig. 2c": ("One row per rated answer (eval_id): each rater's correctness and faithfulness (r1_, r2_), the raters' "
                "mean (raters_), the raters' faithfulness band (band_faithfulness), the judge's correctness and "
                "faithfulness scores (judge_) and MiniCheck against the key (minicheck_key_precision, 0 to 1)."),
    "Fig. 2d": ("First row 'all answers': Spearman's rho of the raters' faithfulness with the judge (rho_judge) and with "
                "MiniCheck (rho_minicheck), their difference D = rho_judge minus rho_minicheck with its two-sided 95% "
                "percentile interval (D_ci95_low, D_ci95_high), each also as sign and size (d_, ci_low_, ci_high_), and "
                "the most resamples in one hexagon (hex_max). Then one row per answer resample (resample 1 to "
                f"{N_BOOT:,}) with rho_judge, rho_minicheck and D."),
    "Fig. 2e": ("One row per dimension (correctness, faithfulness), statistic and pair (judge with raters, raters with "
                "each other, Delta = the first minus the second), and one 'bias' row per dimension (the judge's score "
                "minus the raters'): point, the estimate on all answers; ci95_low and ci95_high, the two-sided 95% "
                "percentile interval; q25, median, q75, the box; finite_resamples, resamples with a value."),
    "Fig. 2f": ("One row per pass mark (4, 3), signal or rule (row: Judge, Concepts, Papers, at least 1, 2 and 3 of 3) "
                "and statistic (accuracy, kappa) against the raters' correctness: n, answers; point, ci95_low, q25, "
                "median, q75, ci95_high and finite_resamples as in Fig. 2e. On the accuracy rows of Judge, Concepts and "
                "Papers, a two-sided exact McNemar test of the 2 of 3 rule against that signal: rule_right_single_wrong "
                "and rule_wrong_single_right, the discordant answers; p_two_sided; favours_rule, true when the rule is "
                "right on more of them and p_two_sided is below 0.05."),
}
VERIFIED_PASS_ITEMS = 5      # frames only, which read no file; the test checks it on S08's join. Filled: S530's count
FRAMES_LINE = "This version draws frames only: no rating is shown."
WAITS_LINE = ("{where} for the rule that takes headings out of Papers (D202); the frame stays empty until then "
              "(D206).")
HELD_LINE = "This version leaves the second judge's row empty."   # D274: no line once S530 writes the row
# FIG2-KRIPP O1 (rulings page 6 Nov): the protocol's sentence on alpha below the gate (S08b:73-76) is no longer written
# into either legend; the Results human-evaluation paragraph carries it.
ONE_LINE = "All panels are descriptive; no decision was taken."
WITHHELD_LINE = ("Left blank in this release: rater 2's per-answer scores, the raters' per-answer means and rater 1's "
                 "per-answer faithfulness, which would give rater 2's scores back. The plate is drawn from all of them.")
TITLE = {1: "Agreement of three automated signals with an expert rater",
         0: "Agreement of three automated signals with expert raters",
         2: "Agreement of three automated signals with expert raters"}


def _sub(text: str, old: str, new: str) -> str:
    if old not in text:
        raise Refused(f"the legend no longer holds {old!r}: the one-rater wording cannot be made")
    return text.replace(old, new)


def one_rater_fig2(t: str) -> str:
    """fig2.md section 5: one author, no mean, Rater, no Delta, no raters with each other, descriptive."""
    for old, new in (("Two authors rated", "One author rated"),
                     ("; the raters' score is their mean.", "."),
                     ("and the raters' score (columns)", "and the rater's score (columns)"),
                     ("each band of the raters' score", "each band of the rater's score"),
                     ("by the raters' faithfulness band", "by the rater's faithfulness band"),
                     ("Spearman's ρ of the raters' faithfulness", "Spearman's ρ of the rater's faithfulness"),
                     ("Agreement, judge with raters and raters with each other:", "Agreement, judge with rater:"),
                     (" Delta, the first minus the second.", ""),
                     ("against the raters' correctness", "against the rater's correctness")):
        t = _sub(t, old, new)
    return t


def one_rater_s3(t: str) -> str:
    """Panel a (two raters with each other) goes and each later letter shifts up one."""
    if " **a**, " not in t or " **b**, " not in t:
        raise Refused("the legend no longer holds panels a and b: the one-rater wording cannot be made")
    t = t[:t.index(" **a**, ")] + t[t.index(" **b**, "):]
    for old, new in (("Two authors rated", "One author rated"),
                     ("; the raters' score is their mean.", "."),
                     ("with each rater's correctness (left) and faithfulness (right)",
                      "with the rater's correctness (left) and faithfulness (right)"),
                     ("; grey, rater 1; white, rater 2;", ";"),
                     ("the raters' ", "the rater's ")):
        t = _sub(t, old, new)
    for a, b in zip("bcdef", "abcde"):
        t = _sub(t, f"**{a}**,", f"**{b}**,")
    return t


def rows_named(names: set, plate_rows: tuple) -> str:
    """The rows in names, in plate order. Two rows of one family (a name and its "name, variant") read "name rows"."""
    out = []
    for row in plate_rows:
        if row not in names:
            continue
        head = row.split(",")[0]
        family = [x for x in plate_rows if x.split(",")[0] == head]
        if len(family) > 1 and all(x in names for x in family):
            out += [] if f"{head} rows" in out else [f"{head} rows"]
        else:
            out.append(f"{row} row")
    return " and ".join(out)


def n_line(res, kind: str = "fig2", mode: int = 2) -> str:
    """Figure 2's real n: the analysed answers, then f when it holds fewer, read from S530's counts. Supplementary
    Figure 3 states its n panel by panel (s3_n)."""
    if kind != "fig2":
        raise ValueError("n_line is Figure 2's; Supplementary Figure 3 takes s3_n")
    n = N_ITEMS if res is None else res["n_analysed"]
    fewer = []
    if res is not None and not waits(res):
        nf, nc = res["f"]["n"], res["f"]["4"]["C"]["n"]
        fewer += [f"{nf} in f"] if nf != n else []
        fewer += [f"{nc} in f's {fn.CONCEPTS} row"] if nc != nf else []
    return "; ".join([f"n = {n} answers", *fewer]) + "."


def s3_n(res) -> dict:
    """Supplementary Figure 3's n, editor row 45's form, inside each panel that draws boxes over resamples (a, b, e, f),
    with any row that holds fewer answers named, read from S530's counts. c and d draw cells and carry no n; d says in
    words when it is computed on the answers with a Papers score only (d_on)."""
    n = N_ITEMS if res is None else res["n_analysed"]

    def per_row(rows, key, plate_rows):
        by_n: dict = {}
        for r in ([] if res is None else rows):
            if r["n"] is not None and r["n"] != n:
                by_n.setdefault(r["n"], set()).add(r[key])
        fewer = [f"{m} in the {rows_named(by_n[m], plate_rows)}" for m in sorted(by_n, reverse=True)]
        return f"n = {n} rated answers" + (f" ({'; '.join(fewer)})." if fewer else ".")
    nd = set() if res is None or waits(res) else {c["n"] for c in res["grid"]}
    if res is not None and (len(nd) > 1 or (len(nd) == 0 and not waits(res))):
        raise Refused(f"S530's grid holds {sorted(nd)} as n, not one value")
    return {"n_a": f"n = {n} rated answers.",
            "n_b": per_row(None if res is None else res["s3b"], "signal", S3B_SIGNALS),
            "d_on": ", on answers with a Papers score" if any(m != n for m in nd) else "",
            "n_e": per_row(None if res is None else res["s3e"], "evaluator", EVALUATORS),
            "n_f": f"n = {n} rated answers."}


def second_judge_drawn(res) -> bool:
    """SUPP3-B O1: True when S530's s3b holds a summary on a second-judge row, which s3_b then draws as any other row."""
    return res is not None and any(r["signal"] == "Second judge" and r["summary"] is not None for r in res["s3b"])


def f_n(res) -> str:
    """Figure 2f's n, editor row 45's form: the answers with a Papers score, read from S530 (E029 has none)."""
    n = N_ITEMS if res is None else res["n_analysed"]
    if res is None or waits(res):
        return f"n = {n} rated answers."
    nf, nc = res["f"]["n"], res["f"]["4"]["C"]["n"]
    out = f"n = {nf} rated answers" + (" that have a Papers score" if nf != n else "")
    return out + (f" ({nc} in the Concepts row)." if nc != nf else ".")


def legend(kind: str, mode: int, res, stamp: str, small=False) -> str:
    """The spec's legends, the numbers from S08's constants. Filled plates carry each panel's real n."""
    vals = dict(n=N_ITEMS if res is None else res["n_analysed"], boot=f"{N_BOOT:,}", seed=SEED,
                gate=S08.V22_ALPHA_GATE, vp=VERIFIED_PASS_ITEMS if res is None else res["verified_pass_answers"],
                f_n=f_n(res), **s3_n(res))
    if kind == "fig2":
        body = FIG2_LEGEND.format(**vals)
        if small:
            body = _sub(body, "dots, every answer;", f"dots, every answer; under {hs.SMALL_N} answers, dots and a median line;")
        if mode == 1:
            body = one_rater_fig2(body)
        head = f"**Figure 2 | {TITLE[mode]}.**"   # D303: the title ends with a full stop, as in the tab
    else:
        body = S3_LEGEND.format(**vals)
        if mode == 1:
            body = one_rater_s3(body)
        head = "**Supplementary Figure 3 | Human evaluation in full.**"   # D303
    tail = []
    if mode == 0:
        tail.append(FRAMES_LINE)
    if mode == 1:
        tail.append(ONE_LINE)
    if mode != 0 and kind == "s3":
        tail += [] if second_judge_drawn(res) else [HELD_LINE]
    if waits(res):
        tail.append(WAITS_LINE.format(where="Panel f waits" if kind == "fig2"
                                      else f"Panel {s3_letters(mode)['d']} and b's Papers row wait"))
    return "\n\n".join([head, body, *tail]) + "\n"     # Q9 (11 Nov): no data stamp line in the legend draft


# ---------------------------------------------------------------- files

def fixed_workbook(path: Path) -> None:
    """Rewrites a workbook with fixed dates inside and on each zip entry, so one input gives one file (build_order
    section 8: `S531 --raters 0` rebuilds byte for byte). Cells are not touched."""
    src = path.read_bytes()
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(src)) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in sorted(zin.infolist(), key=lambda i: i.filename):
            raw = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                raw = re.sub(rb"(<dcterms:(created|modified)[^>]*>)[^<]*", rb"\g<1>2026-11-01T00:00:00Z", raw)
            zi = zipfile.ZipInfo(info.filename, date_time=(2026, 11, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zout.writestr(zi, raw)
    path.write_bytes(out.getvalue())


def plate_files(kind: str, mode: int, fig, printed, sheets_, res, out: Path, inputs: dict, small: bool, withhold: bool) -> str:
    """S457.finish_plate (F4), then the workbook, caption, numbers, legend and provenance, into out. Returns the stamp."""
    n = 2 if kind == "fig2" else 3
    k = 0 if res is None else res["n_analysed"]
    sfx = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    state = {0: "frames", 1: "one rater", 2: "two raters"}[mode]
    stamp = f"{state}, {k} of {N_ITEMS} answers drawn"
    plate = plate_name(kind)
    stem = f"{plate}{sfx}"
    book_stem = f"Source Data Fig. {n}" if kind == "fig2" else f"{plate} data"
    side = "figure2" if kind == "fig2" else "supplementary_figure3"
    W, H = fig._hs_mm
    S457.finish_plate(fig, W, H, {e: out / f"{stem}.{e}" for e in ("pdf", "svg", "png")}, title=plate)
    book = out / f"{book_stem}{sfx}.xlsx"
    S457.write_source_data(sheets_, book)
    fixed_workbook(book)
    numbers = out / f"{side}_numbers.json"
    body = {"stamp": stamp, "sheets": {nm: {"columns": c, "rows": r} for nm, c, r in sheets_}, "printed": printed}
    if kind == "fig2" and res is not None:
        # D309 N1 O1: the legend's "Verified pass holds 5 of the answers" gets a committed source. A count of answers
        # per strategy, read from S530's join configs; no rating value.
        body["counts"] = {"rated_answers": res["n_analysed"], "verified_pass_answers": res["verified_pass_answers"]}
    numbers.write_text(json.dumps(body, indent=0, ensure_ascii=False, allow_nan=False) + "\n")
    cap = out / f"{book_stem} caption{sfx}.md"
    if kind == "fig2":   # D309 A69: each sheet's rows and columns, as the Fig. 3 to 7 captions describe theirs
        sheet_lines = "\n".join(f"- {nm}: {len(r)} rows. {FIG2_SHEET_TEXT[nm]}" for nm, _, r in sheets_)
        sheet_lines += f"\n\nWritten by {SCRIPT} from S530's results (scripts/S530_human_signals.py)."
    else:
        sheet_lines = "\n".join(f"- {nm}: {len(r)} rows" for nm, _, r in sheets_)
    sd_no = f" The source data for Figure {n} is in Supplementary Data {n + 1}." if kind == "fig2" else ""   # D303 (D302)
    cap.write_text(f"{book_stem}. The numbers behind {plate}, one sheet per panel.{sd_no} Data stamp: {stamp}.\n\n"
                   f"{sheet_lines}\n" + (f"\n{WITHHELD_LINE}\n" if withhold else ""))
    (out / "legend_draft.md").write_text(legend(kind, mode, res, stamp, small))
    files = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    prov = out / f"{side}_provenance.json"
    flags = " --without-rater2" if withhold else ""
    prov.write_text(json.dumps({"stamp": stamp, "script": SCRIPT, "script_sha256": sha(ROOT / SCRIPT),
                                "command": f"uv run --frozen python {SCRIPT} --raters {mode}{flags}", "raters": mode,
                                "inputs": inputs, "files": files}, indent=1) + "\n")
    return stamp


def plate_name(kind: str) -> str:
    return "Figure 2" if kind == "fig2" else "Supplementary Figure 3"


def write_plate(kind: str, mode: int, fig, printed, sheets_, res, out: Path, inputs: dict, small=False,
                withhold=False) -> dict:
    """The colour and printed checks, then every file in a folder beside out. Only a whole plate replaces out, so a check
    that fails, here or in S457.finish_plate, leaves out as it was."""
    plate = plate_name(kind)
    bad = hs.check_figure_colours(fig)
    if bad:
        raise SystemExit(f"S531: colours outside the house palette on {plate}: {bad}")
    if not printed:                          # F7: `printed` is never empty
        raise SystemExit(f"S531: {plate} has an empty printed map")
    building = out.with_name(f".{out.name}.building")
    if building.exists():
        shutil.rmtree(building)
    building.mkdir(parents=True)
    try:
        stamp = plate_files(kind, mode, fig, printed, sheets_, res, building, inputs, small, withhold)
    except BaseException:
        shutil.rmtree(building, ignore_errors=True)
        raise
    if out.exists():
        shutil.rmtree(out)
    building.rename(out)
    return {"plate": plate, "folder": out, "stamp": stamp}


def load_results(folder: Path, mode: int) -> tuple:
    import numpy as np
    f = Path(folder) / "results.json"
    if not f.exists():
        raise Refused(f"{f} is not there: run S530 --raters {mode} first")
    res = json.loads(f.read_text())
    if res["raters"] != mode:
        raise Refused(f"{f} holds {res['raters']} rater(s), this run asks for {mode}")
    if mode == 1 and not res.get("_provenance", {}).get("on_word"):
        raise Refused(f"{f} records no word of Valerio's: the one-rater plates need S530 --raters 1 --on-word D<nnn>")
    z = np.load(Path(folder) / "resamples.npz")
    return res, {k: z[k] for k in z.files}, {f.name: sha(f), "resamples.npz": sha(Path(folder) / "resamples.npz")}


def build(mode: int, results: Path, out: Path, withhold: bool = False) -> list:
    """Both plates of one mode into out/fig2_human and out/supp_fig3. withhold: WITHHELD's columns stay blank."""
    res, samples, inputs = (None, None, {}) if mode == 0 else load_results(results, mode)
    hs.apply_rc("S531")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"xtick.major.pad": 1.5, "ytick.major.pad": 1.5, "axes.labelpad": 1.5})   # mock:485
    hs.check_plate_kinds(())                                      # Figure 2 draws no COLOURS kind
    hx = None
    if res is not None:
        import numpy as np
        x, y = samples["d.rho_minicheck"], samples["d.rho_judge"]
        m = np.isfinite(x) & np.isfinite(y)
        hx = hex_counts(x[m], y[m])
    fig, printed, small = build_fig2(mode, res, hx)
    done = [write_plate("fig2", mode, fig, printed, sheets_fig2(mode, res, samples, hx, withhold), res, out / FOLDERS[0],
                        inputs, small, withhold)]
    hs.check_plate_kinds(())                                      # S3 draws no COLOURS kind since D274
    fig, printed = build_s3(mode, res)
    done.append(write_plate("s3", mode, fig, printed, sheets_s3(mode, res, withhold), res, out / FOLDERS[1], inputs,
                            False, withhold))
    return done


def check_out(mode: int, out: Path) -> None:
    """Rated plates stay out of the repository until --released: inside it, only the git-ignored folder (fig2:29)."""
    p, draft = Path(out).resolve(), DRAFT.resolve()
    if mode != 0 and p.is_relative_to(ROOT.resolve()) and not p.is_relative_to(draft):
        raise Refused(f"--raters {mode} writes rated plates: inside the repository only {draft} holds them until "
                      f"--released; {p} refused")


def numbers_of(draft: Path, name: str) -> dict:
    return json.loads(next((Path(draft) / name).glob("*_numbers.json")).read_text())


def release_tag(draft: Path) -> str:
    """The tag a decision line quotes: a hash of the two numbers files, so it names exactly the cells of this build."""
    h = hashlib.sha256()
    for name in FOLDERS:
        h.update(next((Path(draft) / name).glob("*_numbers.json")).read_bytes())
    return f"S531-release-{h.hexdigest()[:12]}"


def holds_rater2(draft: Path) -> bool:
    """True when a cell WITHHELD names is filled, read from the two numbers files and not from a flag."""
    for name, sheet, cols in ((FOLDERS[0], "Fig. 2c", WITHHELD["Fig. 2c"]), (FOLDERS[1], sheet_name(2, "c"), WITHHELD["s3c"])):
        t = numbers_of(draft, name)["sheets"][sheet]
        at = [t["columns"].index(c) for c in cols]
        if any(row[i] is not None for row in t["rows"] for i in at):
            return True
    return False


def decision_line(decision, readme=None) -> str:
    """S08.v22_on_word's check, in this script's words: its own message speaks of a one-rater run."""
    try:
        return S08.v22_on_word(decision, readme)
    except S08.V22Refused:
        raise Refused(f"{decision!r} is not one dated decision line of the form D<nnn>: --released needs one, holding "
                      f"the release tag") from None


def release(draft: Path, target: Path, on_word: str, rater2_yes: str = None, readme=None) -> list:
    """Copies the two mode 2 folders to target, replacing the frames (fig2:31). Refuses anything but a complete two-rater
    draft; a decision that does not hold this draft's tag; and rater 2's cells without a line that holds the tag and the
    word Dirkjan."""
    for name in FOLDERS:
        src = Path(draft) / name
        prov = next(iter(src.glob("*_provenance.json")), None) if src.is_dir() else None
        if prov is None or json.loads(prov.read_text()).get("raters") != 2:
            raise Refused(f"{src} is not a two-rater draft: nothing moved")
    tag = release_tag(draft)
    if tag not in decision_line(on_word, readme):
        raise Refused(f"{on_word} does not name this release: its line must hold {tag}. Nothing moved")
    if holds_rater2(draft):
        if rater2_yes is None:
            raise Refused(f"this draft holds rater 2's per-answer columns: record Dirkjan's yes in a decision line that "
                          f"holds {tag} and pass --rater2-yes D<nnn>, or rebuild with --without-rater2. Nothing moved")
        yes = decision_line(rater2_yes, readme)
        if tag not in yes or "Dirkjan" not in yes:
            raise Refused(f"{rater2_yes} is not Dirkjan's yes to this release: its line must hold {tag} and the word "
                          f"Dirkjan. Nothing moved")
    moved = []
    for name in FOLDERS:
        dst = Path(target) / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(Path(draft) / name, dst)
        moved.append(dst)
    return moved


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raters", type=int, choices=(0, 1, 2), required=True)
    ap.add_argument("--results", type=Path, default=RESULTS, help="S530's folder (modes 1 and 2)")
    ap.add_argument("--out", type=Path, help="default: figures_provisional in mode 0, the git-ignored folder otherwise; "
                                             "modes 1 and 2 refuse any other folder inside the repository")
    ap.add_argument("--released", action="store_true", help="mode 2: copy the draft to figures_provisional")
    ap.add_argument("--on-word", help="--released: the decision that records Valerio's word and holds the release tag")
    ap.add_argument("--rater2-yes", help="--released: the decision that records Dirkjan's yes and holds the release tag")
    ap.add_argument("--without-rater2", action="store_true", help="mode 2: leave rater 2's per-answer columns out")
    a = ap.parse_args(argv)
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    try:
        if a.without_rater2 and a.raters != 2:
            raise Refused("--without-rater2 is for mode 2: no other mode holds rater 2's columns")
        if a.rater2_yes and (a.without_rater2 or not a.released):
            raise Refused("--rater2-yes goes with --released, and not with --without-rater2")
        if a.released:
            if a.raters != 2:
                raise Refused("--released is for mode 2 only: mode 1 stays in the git-ignored folder (fig2:29)")
            decision_line(a.on_word)
            if a.rater2_yes is None and not a.without_rater2:
                raise Refused("--released needs --rater2-yes D<nnn>, Dirkjan's yes, or --without-rater2")
            if a.rater2_yes:
                decision_line(a.rater2_yes)
        out = a.out or (FIGURES if a.raters == 0 else DRAFT)
        check_out(a.raters, out)
        done = build(a.raters, a.results, out, a.without_rater2)
        for d in done:
            print(f"S531: {d['plate']}, {d['stamp']}, in {d['folder']}")
        if a.raters == 2:
            print(f"S531: release tag {release_tag(out)}")
        if a.released:
            moved = release(out, FIGURES, a.on_word, a.rater2_yes)
            print("S531: released to", ", ".join(str(p) for p in moved))
    except (Refused, S08.V22Refused) as e:
        print(f"S531 REFUSED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
