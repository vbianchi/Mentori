"""Figure 5 panel c, design c5 (scratch, exploratory): head-to-head against single pass, question by question.
Reads c5_counts.json (prep_c5.py, through S473's own functions). Three facets (Judge | Concepts | Papers), one row per
other strategy; each row one stacked bar in numbers of questions, from 0: orange, single pass higher; grey, ties;
blue, the other strategy higher; the bar ends at the row's n (83, or 82 where a draw-1 MiniCheck precision is null).
Critic, 28 Oct: was a diverging bar with the ties centred on zero, so the orange bar's left end sat at (single pass
higher + ties / 2) on an axis labelled 80 0 80 and the axis could not be read as a count; now every segment's start
or end reads on a 0 to 83 axis. The x label no longer says n = 83 (three Papers bars are 82); the legend gives n. 78 x 68 mm. Saved by S457.finish_plate
(refuses texts past the page or on each other), PDF + SVG + 600 dpi PNG. Writes c5_numbers.json."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import S457_fig2_panels as S457  # noqa: E402

HERE = Path(__file__).resolve().parent
CJ = HERE / "c5_counts.json"
D = json.loads(CJ.read_text())
CONF = D["strategies"]
LAB = D["label"]
SIGS = ("judge", "concept", "papers")
SIGNAME = {"judge": "Judge", "concept": "Concepts", "papers": "Papers"}
ROWS = ["multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
ORANGE, GREY, BLUE = "#E69F00", "#BBBBBB", "#0072B2"
assert ORANGE == S457.OKABE["orange"] and BLUE == S457.OKABE["blue"]
NQ = D["n_questions"]
plt.rcParams.update(S457.plate_rc("fig5c5"))

W, H = 78.0, 68.0
LAB_W, FAC_W, GAP = 17.3, 16.5, 4.5   # spec 17, 18.5, 2.5: its last "80" fell past the page and adjacent facets' "80"s sat 0.1 mm apart; now 2 mm
PITCH, BAR_H = 8.0, 4.5
TOP = 16.0                       # top of the facets' plot area (mm from the page top)
PLOT_H = PITCH * len(ROWS)       # 40 mm
XL = 83
XTICKS = [0, 40, 80]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ax_mm(fig, x, y, w, h):
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def text_mm(fig, x, y, s, **kw):
    return fig.text(x / W, 1 - y / H, s, **kw)


fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
text_mm(fig, 0.5, 3.6, "c", fontsize=S457.PT_LETTER, fontweight="bold", va="baseline", ha="left")

# key: one row, centred on the plate, 3 x 2 mm swatches with 8 pt text beside them
KEY_Y = 8.2                     # centre line of the key row (mm)
items = [(ORANGE, "single pass higher"), (GREY, "tie"), (BLUE, "other strategy higher")]
fig.canvas.draw()
rend = fig.canvas.get_renderer()
widths = []
for _, s in items:
    t = text_mm(fig, 0, 0, s, fontsize=S457.PT)
    bb = t.get_window_extent(rend)
    widths.append(bb.width / fig.dpi * 25.4)
    t.remove()
SW, SH, SG, IG = 3.0, 2.0, 0.9, 2.6   # swatch w, h; swatch-to-text gap; gap between items
total = sum(SW + SG + w for w in widths) + IG * (len(items) - 1)
x = (W - total) / 2
kax = fig.add_axes([0, 0, 1, 1], facecolor="none")
kax.set_xlim(0, W)
kax.set_ylim(H, 0)
kax.axis("off")
for (col, s), w in zip(items, widths):
    kax.add_patch(plt.Rectangle((x, KEY_Y - SH / 2), SW, SH, facecolor=col, edgecolor="none"))
    text_mm(fig, x + SW + SG, KEY_Y, s, fontsize=S457.PT, va="center_baseline", ha="left")
    x += SW + SG + w + IG

drawn = {}
for j, s in enumerate(SIGS):
    x0 = LAB_W + j * (FAC_W + GAP)
    ax = ax_mm(fig, x0, TOP, FAC_W, PLOT_H)
    ax.set_xlim(0, XL)
    ax.set_ylim(len(ROWS) - 0.5, -0.5)
    for k in ("top", "right", "left"):
        ax.spines[k].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(XTICKS)
    ax.set_xticklabels([str(t) for t in XTICKS])
    ax.tick_params(axis="x", pad=1.5)
    bh = BAR_H / PITCH
    drawn[s] = {}
    for i, o in enumerate(ROWS):
        r = D["pairs"][f"single_pass|{o}"][s]
        sp, tie, ot = r["first_higher"], r["tie"], r["second_higher"]
        assert sp + tie + ot == r["n"]
        ax.barh(i, sp, left=0, height=bh, color=ORANGE, lw=0, zorder=2)
        ax.barh(i, tie, left=sp, height=bh, color=GREY, lw=0, zorder=2)
        ax.barh(i, ot, left=sp + tie, height=bh, color=BLUE, lw=0, zorder=2)
        drawn[s][LAB[o]] = {"single_pass_higher": sp, "tie": tie, "other_higher": ot, "n": r["n"],
                            "bar_from": 0, "bar_to": sp + tie + ot}
    text_mm(fig, x0 + FAC_W / 2, TOP - 1.6, SIGNAME[s], fontsize=S457.PT, ha="center", va="baseline")
    if j == 1:
        ax.set_xlabel("Number of questions", labelpad=2)
for i, o in enumerate(ROWS):
    text_mm(fig, LAB_W - 0.4, TOP + PITCH * (i + 0.5), LAB[o], fontsize=S457.PT, ha="right", va="center_baseline")

paths = {k: HERE / f"c5.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(fig, W, H, paths, title="Figure 5c c5")
from PIL import Image  # noqa: E402

im = np.asarray(Image.open(paths["png"]).convert("L"))
m = int(round(0.6 / 25.4 * 600))
inked = [k for k, v in {"left": im[:, :m], "right": im[:, -m:], "top": im[:m, :], "bottom": im[-m:, :]}.items()
         if (v < 250).any()]
if inked:
    raise SystemExit(f"c5: ink within 0.6 mm of the page edge ({inked})")

not_drawn = {}
for key, row in D["pairs"].items():
    a, b = key.split("|")
    if a == "single_pass":
        continue
    not_drawn[f"{LAB[a]} against {LAB[b]}"] = {
        SIGNAME[s]: {f"{LAB[a]} higher": row[s]["first_higher"], "tie": row[s]["tie"],
                     f"{LAB[b]} higher": row[s]["second_higher"], "n": row[s]["n"]} for s in SIGS}
assert len(not_drawn) == 10

numbers = {
    "option": "c5", "title": "Head-to-head against single pass, question by question",
    "size_mm": [W, H],
    "rule": D["rule"], "provisional": D["provisional"],
    "n_questions_W_set": NQ,
    "papers_cells_without_precision": {
        "multi-hop, 01_sarek_TE3, draw 1": "status ok, precision null: no claim sentence",
        "RLM-5, 02_snakemake_CO2, draw 1": "status error, precision null: no answer",
        "RLM-10, 02_snakemake_CO2, draw 1": "status error, precision null: no answer",
        "effect": "the Papers rows for multi-hop, RLM-5 and RLM-10 compare 82 questions, the others 83"},
    "drawn": {SIGNAME[s]: drawn[s] for s in SIGS},
    "pairs_not_drawn": not_drawn,
    "legend_only": {"kendall_W": D["W"], "exact_P": D["P"], "n_questions": NQ},
    "axes": {"x": [0, XL], "ticks": XTICKS, "tick_labels": [str(t) for t in XTICKS],
             "x_label": "Number of questions", "n_in_legend": "n = 83 questions per bar; 82 for the Papers bars of "
             "multi-hop, RLM-5 and RLM-10 (a null draw-1 MiniCheck precision)"},
    "colours": {"single pass higher": ORANGE, "tie": GREY, "other strategy higher": BLUE},
    "sources": {"c5_counts.json": {"path": str(CJ), "sha256": sha(CJ)},
                "computed_by": {"path": str(HERE / "prep_c5.py"), "sha256": sha(HERE / "prep_c5.py")},
                "drawn_by": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
                "prep_inputs": D["inputs"]},
    "outputs": {k: {"path": str(p), "sha256": sha(p)} for k, p in paths.items()},
}
(HERE / "c5_numbers.json").write_text(json.dumps(numbers, indent=1, ensure_ascii=False) + "\n")
print("c5", f"{W} x {H} mm")
