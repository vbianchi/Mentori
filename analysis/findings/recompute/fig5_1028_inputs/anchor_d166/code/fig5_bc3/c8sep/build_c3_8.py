"""Figure 5 panel c, design c3-8 (scratch, exploratory): c8 with the strategies divided (Valerio, 28 Oct).

Run with A or B: A draws a grey separator line between strategies, B alternating light grey bands behind them;
both add vertical space between strategies (PITCH 9.4 -> 10.6 mm). Every number is c8's.
Copied from ../../fig5_bc2/c8/build_c8.py; the rest of this docstring is c8's.


Reads, never writes, the repository. Loads the 28 October pull through S473's own readers (pull_sources, reproduce,
S463.read_collect, read_l3, read_l1, check_same_answers, compute), exactly as ../../fig5_c/prep.py does, and builds the
signals with compute's own rules: the judge's plain call (a 'failed' answer scores 0, an unscored call is left out),
concept recall = L3's concept_recall_loose (provisional loose matcher), MiniCheck precision against the papers (draw 1).
The question set is compute's W set (answerable questions whose six draw-1 answers all have an L1 papers row).

For strategy c against strategy r, signal s, draw d: on the W questions where both draw-d values exist,
  margin = (questions where c's value > r's - questions where c's value < r's) / questions with both x 100.
Drawn: the five strategies against single pass. Source Data also carries the 10 pairs not against single pass.
Writes here: fig5c3-8<V>.pdf, .svg, .png (600 dpi), _numbers.json, _source_data.csv, _legend.md.
"""
import hashlib
import itertools
import json
import sys
import tempfile
import csv
from pathlib import Path

import numpy as np

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
PULL = HERE.parents[2] / "fig5_pull_1028"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
S473 = importlib.util.module_from_spec(spec)
sys.modules["S473"] = S473
spec.loader.exec_module(S473)
S463 = S473.S463
S457 = S473.S457
CONFIGS = S473.CONFIGS
SIGS = ("judge", "concept", "papers")
VAR = sys.argv[1]
assert VAR in ("A", "B"), VAR
STEM = f"fig5c3-8{VAR}"
SIG_DRAWS = {"judge": (1, 2, 3), "concept": (1, 2, 3), "papers": (1,)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------
# data, through S473
# ---------------------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory(prefix="fig5c8_") as tmpd:
    tmp = Path(tmpd)
    srcs = S473.pull_sources(PULL.resolve(), tmp)
    rep = S473.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups)
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    txt = S473.answer_text_sha(srcs["ans_dirs"])
    diff = [k for (c, q, d), r in l3["rows"].items()
            for k in [f"{S473.INDEX}|{c}|{q}|d{d}"] if txt.get(k) != r.get("answer_sha256")]
    assert not diff, diff[:3]
    faith_rows = {}
    for x in S473.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    cc = fn["c"]
    # the signals as compute builds them (S473.compute, "judge = {}" to "papers = {}")
    cells = read["cells"]
    sig = {"judge": {}, "concept": {}, "papers": {}}
    for (c, q, d), cell in cells.items():
        if groups[q] == "answerable":
            sig["judge"][(c, q, d)] = (cell["score"] if cell["kind"] == "scored"
                                       else 0 if cell["kind"] == "failed" else None)
    for (c, q, d), r in l3["rows"].items():
        if groups[q] == "answerable":
            sig["concept"][(c, q, d)] = (r["concept_recall_loose"] if r["status"] in ("ok", "no_answer", "error")
                                         else None)
    for (c, q, d), r in l1["stages"]["papers"].items():
        if groups[q] == "answerable":
            sig["papers"][(c, q, d)] = (r.get("signals") or {}).get("precision")
    judge_kinds = {}
    for (c, q, d), cell in cells.items():
        if groups[q] == "answerable":
            judge_kinds[cell["kind"]] = judge_kinds.get(cell["kind"], 0) + 1

QW = cc["questions"]
assert len(QW) == 83, len(QW)


def margin(s, c, r, d):
    w = t = lo = 0
    for q in QW:
        a, b = sig[s].get((c, q, d)), sig[s].get((r, q, d))
        if a is None or b is None:
            continue
        if a > b:
            w += 1
        elif a < b:
            lo += 1
        else:
            t += 1
    n = w + t + lo
    return {"wins": w, "ties": t, "losses": lo, "n": n, "margin_pct": 100.0 * (w - lo) / n}


rows = []
for c, r in itertools.combinations(CONFIGS, 2):
    # against single pass the strategy is the row (c) and single pass the reference; otherwise the later strategy in
    # CONFIGS order is the row and the earlier the reference
    row, ref = (r, c)
    for s in SIGS:
        for d in SIG_DRAWS[s]:
            m = margin(s, row, ref, d)
            rows.append({"strategy": row, "reference": ref, "signal": s, "draw": d, **m})

DRAWN = [x for x in rows if x["reference"] == "single_pass"]
ROWS_ORDER = ["multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]

# checked values from the spec (rounded half up to integers)
CHECK = {"multi_hop": ([-7, -13, -16], [-46, -55, -54], [-52]),
         "verified_pass": ([5, 5, -2], [5, -5, -4], [16]),
         "rlm_5": ([-29, -33, -18], [17, 20, 24], [-80]),
         "rlm_10": ([-25, -23, -18], [29, 22, 30], [-85]),
         "rlm_20": ([-31, -27, -30], [23, 19, 20], [-86])}
mism = []
for c in ROWS_ORDER:
    for s, want in zip(SIGS, CHECK[c]):
        got = [int(S457.half_up(x["margin_pct"], 0)) for x in DRAWN if x["strategy"] == c and x["signal"] == s]
        if got != want:
            mism.append((c, s, got, want))
print("check against the spec's values:", "all equal" if not mism else mism)

# ---------------------------------------------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------------------------------------------
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

plt.rcParams.update(S457.plate_rc("fig5c8"))
W_MM, H_MM = 78.0, 74.0              # c3-8: 6 mm taller for the space between strategies
LAB_RIGHT = 18.0                     # labels right-aligned in an 18 mm column
PLOT_X, PLOT_W = 19.5, 56.0
PLOT_Y, PLOT_H = 12.0, 53.0          # from the top; c3-8: 5 x PITCH
PITCH, SUB = 10.6, 2.5               # critic: SUB 2.2 -> 2.5 to leave room for a dodged mark
MSZ_MM = 1.4                         # critic: 1.6 -> 1.4 mm, so near-equal draws separate with a small dodge
MSZ = MSZ_MM / S457.MM_PT            # marker size in points
COL = {"judge": "#0072B2", "concept": "#E69F00", "papers": "#000000"}
MK = {"judge": "o", "concept": "s", "papers": "D"}
SUBOFF = {"judge": -SUB, "concept": 0.0, "papers": SUB}
KEYTXT = {"judge": "Judge (3 draws)", "concept": "Concepts (3 draws)", "papers": "Papers (draw 1)"}
MSZ_S = {"o": MSZ, "s": MSZ * 0.9, "D": MSZ * 0.85}   # equal visual weight: a square and a diamond look larger


def text_mm(fig, x, y, s, **kw):
    return fig.text(x / W_MM, 1 - y / H_MM, s, **kw)


fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4), facecolor="#FFFFFF")
ax = fig.add_axes([PLOT_X / W_MM, 1 - (PLOT_Y + PLOT_H) / H_MM, PLOT_W / W_MM, PLOT_H / H_MM])
ax.set_xlim(-100, 100)
ax.set_ylim(PLOT_H, 0)              # y in mm from the plot's top
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.set_yticks([])
ax.set_xticks([-100, -50, 0, 50, 100])
ax.set_xticklabels(["−100", "−50", "0", "50", "100"])
ax.set_xlabel("Margin over single pass (% of questions)", labelpad=2)
ax.axvline(0, color="#000000", lw=0.5, zorder=1)
ax.patch.set_visible(False)          # c3-8: the bands and lines below sit under the axes, so its white patch goes
from matplotlib.patches import Rectangle  # noqa: E402
SEP_GREY, SEP_LW = "#949494", 0.5    # A: WCAG contrast with white 3.0:1 (computed below)
BAND_GREY = "#EFEFEF"                # B: a grey (R5), behind black text (R11)
DIV_X0 = 0.5                         # from the plate's left edge, so each label sits inside its strategy's band
DIV_X1 = PLOT_X + PLOT_W
TOP0 = -(PITCH * 5 - PLOT_H) / 2     # 0: the rows fill the plot exactly
divs = []
for i in range(5):
    y0, y1 = PLOT_Y + TOP0 + i * PITCH, PLOT_Y + TOP0 + (i + 1) * PITCH
    if VAR == "A" and i > 0:
        fig.add_artist(Line2D([DIV_X0 / W_MM, DIV_X1 / W_MM], [1 - y0 / H_MM] * 2, transform=fig.transFigure,
                              color=SEP_GREY, lw=SEP_LW, solid_capstyle="butt", zorder=-1))
        divs.append({"kind": "line", "y_mm_from_plate_top": y0, "x_mm": [DIV_X0, DIV_X1], "colour": SEP_GREY,
                     "width_pt": SEP_LW})
    if VAR == "B" and i % 2 == 0:
        fig.add_artist(Rectangle((DIV_X0 / W_MM, 1 - y1 / H_MM), (DIV_X1 - DIV_X0) / W_MM, PITCH / H_MM,
                                 transform=fig.transFigure, facecolor=BAND_GREY, edgecolor="none", lw=0, zorder=-1))
        divs.append({"kind": "band", "y_mm_from_plate_top": [y0, y1], "x_mm": [DIV_X0, DIV_X1], "colour": BAND_GREY})


def wcag(hexc):
    v = int(hexc[1:3], 16) / 255
    lin = v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return round(1.05 / (lin + 0.05), 2)

drawn_numbers = []
# critic (28 Oct): marks closer than one marker width are dodged vertically, so every draw is countable (verified
# pass's judge draws 1 and 2 are both +4.8 and coincided; RLM-20's judge -31.3/-30.1 and others overlapped).
# x is never moved; a dodged mark sits DODGE mm above or below its signal's line.
DODGE = 1.0
X_MM = PLOT_W / 200.0
dodged = []
for i, c in enumerate(ROWS_ORDER):
    yc = PITCH / 2 + i * PITCH - (PITCH * 5 - PLOT_H) / 2
    text_mm(fig, LAB_RIGHT, PLOT_Y + yc, S473.LABEL[c], ha="right", va="center")
    placed = []                                    # (x_mm, y_mm) of marks already in this row
    for s in SIGS:
        pts = sorted([x for x in DRAWN if x["strategy"] == c and x["signal"] == s], key=lambda z: z["draw"])
        tries = (0.0, -DODGE, DODGE) if s != "papers" else (0.0, DODGE, -DODGE)
        for x in pts:
            xm = (x["margin_pct"] + 100) * X_MM
            best = None
            for off in tries:
                y = yc + SUBOFF[s] + off
                gap = min([((xm - px) ** 2 + (y - py) ** 2) ** 0.5 for px, py in placed] + [9e9])
                if gap >= MSZ_MM * 0.98:
                    best = (off, y)
                    break
                if best is None or gap > best[2]:
                    best = (off, y, gap)
            off, y = best[0], best[1]
            if off:
                dodged.append((S473.LABEL[c], s, x["draw"], off))
            placed.append((xm, y))
            ax.plot([x["margin_pct"]], [y], ls="none", marker=MK[s], ms=MSZ_S[MK[s]], mfc=COL[s],
                    mec="#FFFFFF", mew=0.3, zorder=3, clip_on=False)
            drawn_numbers.append({"row": S473.LABEL[c], "signal": s, "draw": x["draw"],
                                  "margin_pct": x["margin_pct"], "y_mm_from_plot_top": y, "dodge_mm": off,
                                  "wins": x["wins"], "ties": x["ties"], "losses": x["losses"], "n": x["n"]})
min_gap = {}
for r_ in {d["row"] for d in drawn_numbers}:
    pp = [((d["margin_pct"] + 100) * X_MM, d["y_mm_from_plot_top"]) for d in drawn_numbers if d["row"] == r_]
    min_gap[r_] = round(min(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
                            for a, b in itertools.combinations(pp, 2)), 2)
print("dodged", dodged)
print("closest two marks per row (mm; marker", MSZ_MM, "mm):", min_gap)

# end labels, 8 pt black, at the two ends of the axis, just above the plot
text_mm(fig, PLOT_X, PLOT_Y - 1.2, "single pass better", ha="left", va="baseline")
text_mm(fig, PLOT_X + PLOT_W, PLOT_Y - 1.2, "strategy better", ha="right", va="baseline")   # critic: the row's strategy

# key, one row above the end labels, with the marks' shapes
fig.canvas.draw()
rend = fig.canvas.get_renderer()
KEY_Y = PLOT_Y - 5.6
GAP_MARK, GAP_ITEM = 0.6, 1.8
widths = {}
for s in SIGS:
    t = text_mm(fig, 0, KEY_Y, KEYTXT[s], ha="left", va="baseline")
    bb = t.get_window_extent(rend)
    widths[s] = (bb.x1 - bb.x0) / fig.dpi * 25.4
    t.remove()
total = sum(MSZ_MM + GAP_MARK + widths[s] for s in SIGS) + GAP_ITEM * 2
x0 = (W_MM - total) / 2
assert x0 > 0.3, f"key too wide: starts at {x0:.1f} mm"
x = x0
for s in SIGS:
    fig.add_artist(Line2D([(x + MSZ_MM / 2) / W_MM], [1 - (KEY_Y - 1.0) / H_MM], transform=fig.transFigure, ls="none",
                          marker=MK[s], ms=MSZ_S[MK[s]], mfc=COL[s], mec="#FFFFFF", mew=0.3))
    text_mm(fig, x + MSZ_MM + GAP_MARK, KEY_Y, KEYTXT[s], ha="left", va="baseline")
    x += MSZ_MM + GAP_MARK + widths[s] + GAP_ITEM
text_mm(fig, 0.5, 2.7, "c", fontsize=S457.PT_LETTER, fontweight="bold", ha="left", va="baseline")

paths = {k: HERE / f"{STEM}.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(fig, W_MM, H_MM, paths, title=f"Figure 5c c3-8{VAR}")

# ---------------------------------------------------------------------------------------------------------------
# Source Data, legend, numbers
# ---------------------------------------------------------------------------------------------------------------
with open(HERE / f"{STEM}_source_data.csv", "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["strategy", "reference", "signal", "draw", "wins", "ties", "losses", "questions_with_both",
                 "margin_pct", "drawn"])
    for x in rows:
        wr.writerow([S473.LABEL[x["strategy"]], S473.LABEL[x["reference"]], x["signal"], x["draw"], x["wins"],
                     x["ties"], x["losses"], x["n"], S457.half_up(x["margin_pct"], 2),
                     int(x["reference"] == "single_pass")])

tie_pct = {s: [100.0 * x["ties"] / x["n"] for x in DRAWN if x["signal"] == s] for s in SIGS}
tie_rng = {s: (int(S457.half_up(min(v), 0)), int(S457.half_up(max(v), 0))) for s, v in tie_pct.items()}
n_pap = {x["strategy"]: x["n"] for x in DRAWN if x["signal"] == "papers"}
assert len(set(n_pap.values())) == 2 and min(n_pap.values()) == max(n_pap.values()) - 1, n_pap
n_papers = sorted({x["n"] for x in DRAWN if x["signal"] == "papers"})
n_other = sorted({x["n"] for x in DRAWN if x["signal"] != "papers"})
legend = (
    "**c**, Each signal's verdict on each strategy against single pass, question by question. For one draw, the margin "
    "is the number of questions on which the strategy's answer scores higher than single pass's answer to the same "
    "question, minus the number on which it scores lower, as a percentage of the questions with both answers scored "
    "(0 = as many wins as losses; ties count in the denominator only). "
    "Blue circles, the judge's correctness score (from 0 to 5, with 0 for an answer with no text), one per draw; orange "
    "squares, concept recall against the answer key (L3's provisional loose matcher), one per draw; black diamonds, "
    "MiniCheck precision against the source papers, draw 1 only. "
    + ("Grey lines separate the strategies. " if VAR == "A" else "Shaded bands mark alternate strategies. ") +
    f"n = {n_other[0]} questions for the judge and concept recall, and for the papers on "
    + " and ".join(S473.LABEL[c] for c in ROWS_ORDER if n_pap[c] == max(n_papers))
    + f"; n = {min(n_papers)} questions for the papers on "
    + (lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1])([S473.LABEL[c] for c in ROWS_ORDER if n_pap[c] == min(n_papers)])
    + " (each lacks a papers value on one question). "
    "Each mark is one draw's margin; no mean or interval is drawn; marks closer than one marker width are moved up or "
    "down, never sideways. Draw d of a strategy is compared with draw d of single pass; the draws are independent, so "
    "this pairing is one of several possible. "
    f"The judge's marks compare the 0 to 5 scores themselves, while panel a draws the judge's pass rate (score {S473.PASS_T} "
    "or more), so a score that rises from 4 to 5, which leaves panel a unchanged, counts here as a win. "
    f"A signal that ties often shows shorter margins: the judge's score ties on {tie_rng['judge'][0]} to "
    f"{tie_rng['judge'][1]}% of the questions, concept recall on {tie_rng['concept'][0]} to {tie_rng['concept'][1]}% and "
    f"the papers' precision on {tie_rng['papers'][0]} to {tie_rng['papers'][1]}%, so only the signs of the three "
    "signals' margins compare, not their lengths. "
    f"Ranking the six strategies by their mean on each signal (same {len(QW)} questions), the three rankings' "
    f"agreement is Kendall's W = {S457.half_up(cc['W'], 2)} (exact one-sided P = {S457.half_up(cc['P'], 3)}, "
    "permutation null over untied rankings)."
)
(HERE / f"{STEM}_legend.md").write_text(legend + "\n")

inputs = {"pull:" + k.split(":", 1)[1] if k.startswith("pull:") else k: v for k, v in srcs["sha"].items()}
used = {k: v for k, v in inputs.items()
        if k.startswith("pull:s3/g1_collect") or k.startswith("pull:l1/papers") or k.startswith("pull:l1/header")
        or "concept_recall" in k or k.startswith("findings/recompute/L3")}
out = {
    "what": f"Figure 5 panel c design c3-8{VAR}: c8 with the strategies divided (scratch, exploratory)",
    "dividers": divs, "divider_contrast_with_white": {SEP_GREY: wcag(SEP_GREY), BAND_GREY: wcag(BAND_GREY)},
    "tie_pct_range": tie_rng,
    "plate_mm": [W_MM, H_MM], "plot_area_mm": [PLOT_W, PLOT_H],
    "question_set": {"name": "S473 compute's W set", "n": len(QW), "questions": QW,
                     "left_out_partial_blocks": cc["partial_blocks_left_out"]},
    "rule": "margin = (wins - losses) / (wins + ties + losses) x 100 over W questions where both draw-d values exist",
    "check_against_spec": "all equal" if not mism else mism,
    "drawn": drawn_numbers,
    "source_data_rows": rows,
    "kendall_W": cc["W"], "kendall_W_exact_P": cc["P"],
    "judge_cell_kinds_answerable": judge_kinds,
    "n_questions_per_mark": {"judge_and_concept": n_other, "papers": n_papers},
    "provisional": ["concept recall: L3 loose matcher (D12), provisional until P2's hand labels choose the matcher"],
    "reproduced": rep,
    "files": {
        "used_by_this_panel": {k: {"sha256": v} for k, v in used.items()},
        "all_pull_and_repo_inputs_read": inputs,
        "pull_dir": str(PULL),
        "l3": {"path": str(ROOT / "findings/recompute/L3/concept_recall.jsonl"),
               "sha256": sha(ROOT / "findings/recompute/L3/concept_recall.jsonl")},
        "scripts": {p: sha(ROOT / p) for p in ("scripts/S473_fig5_panels.py", "scripts/S463_fig2_ranking.py",
                                               "scripts/S457_fig2_panels.py")},
        "builder": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "outputs": {p.name: sha(p) for p in [*paths.values(), HERE / f"{STEM}_source_data.csv", HERE / f"{STEM}_legend.md"]},
    },
}
(HERE / f"{STEM}_numbers.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
for c in ROWS_ORDER:
    print(S473.LABEL[c], {s: [(S457.half_up(x["margin_pct"], 1), x["wins"], x["ties"], x["losses"], x["n"])
                              for x in DRAWN if x["strategy"] == c and x["signal"] == s] for s in SIGS})
print("W", cc["W"], "P", cc["P"], "key starts at", round(x0, 2), "mm")
