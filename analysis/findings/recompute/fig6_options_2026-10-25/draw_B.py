"""Figure 6 alternatives, design B: paired contrasts for best of 3, combined and x3 (REVIEWERS_fig6.md section 3,
points 1 and 4: R4-16, ED-3, R1-5, R4-5, R1-10, R1-11, ED-5).

Each contrast pairs the same variant and operation (11 variants x 20 operations = 220 pairs): free-form best of 3 and
free-form combined against free-form; structured best of 3, structured combined and structured x3 against structured.
Per contrast: rescued (base failed, arm passed), lost (base passed, arm failed), net points = 100 (rescued - lost) / 220,
a 95% percentile interval resampling the 20 operations (10,000 resamples, seed 20261013, coverage_check.py's boot()),
and cost multiples = summed arm / summed base over the 220 pairs, for generator_calls (model calls of the generator
role; n_calls also counts the judge), latency_s and output_tokens.

REPRODUCE FIRST: stops before drawing unless attempts.csv gives 2,420 attempts and 1,692 passes (after S4), and the five contrasts
give exactly the counts, net, interval and cost multiples in coverage_check.json gap_best_of_3.

Reads only the frozen inputs/attempts.csv, inputs/summary.json and inputs/coverage_check.json (D155, INVENTORY A1f:
copied byte for byte from the drafts' scratch folder fig6_alt, where this script read them as ../), each checked
against its sha256 in findings/recompute/frozen_inputs/SHA256SUMS before it is read, and experiments/FIGURE_LOCK.toml.
Writes B_numbers.json (the anchor S481's family B reproduces) and the option images into this folder, or into --out.
No file carries a time: the PDFs are saved with no date, creator or producer, and B_numbers.json names the script and
its inputs by repository path and sha256. The script runs under PYTHONHASHSEED=0, re-executing itself with it set
when needed: without it the PDFs' embedded font subsets change with Python's per-process string-hash seed.

The one command that rebuilds the anchor, from the repository root (into a folder outside the repository, so this
folder's draft images, some drawn by the draw_B1b_* wrappers, are not overwritten); the B_numbers.json it writes there
equals this folder's byte for byte:
  uv run --frozen python findings/recompute/fig6_options_2026-10-25/draw_B.py --out <folder>
Without --out it writes into this folder, as the drafts did.
"""
import csv
import json
import math
import random
import statistics as st
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE / "inputs"                  # D155: the frozen copies (they were ../ in the scratch folder fig6_alt)
_ap = __import__("argparse").ArgumentParser(description="Figure 6 option B and B_numbers.json")
_ap.add_argument("--out", help="write into this folder instead of the script's own (a rebuild to compare)")
_args = _ap.parse_args()
OUT = Path(_args.out).resolve() if _args.out else HERE
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro  # noqa: E402
# The PDFs' embedded font subsets follow Python's per-process string-hash seed (26 October: seeds 1 and 3 gave one
# sha256 for B_alt1_forest.pdf, seed 2 another): run under PYTHONHASHSEED=0, re-executing this command line if needed.
if __import__("os").environ.get("PYTHONHASHSEED") != "0":
    sys.stdout.flush()
    __import__("os").execve(sys.executable, [sys.executable, *sys.orig_argv[1:]],
                            {**__import__("os").environ, "PYTHONHASHSEED": "0"})

_SUMS = fig_repro._read_sums(ROOT / "findings/recompute/frozen_inputs/SHA256SUMS")
INPUTS = {}
for _f in ("attempts.csv", "summary.json", "coverage_check.json"):
    _rel = (DATA / _f).relative_to(ROOT).as_posix()
    _got = fig_repro.sha256_file(DATA / _f)
    if _SUMS.get(_rel) != _got:
        sys.exit(f"NOT REPRODUCED: {_rel} sha256 {_got[:12]} is not the frozen copy's {str(_SUMS.get(_rel))[:12]}")
    INPUTS[_rel] = _got
FLOCK = tomllib.loads((ROOT / "experiments/FIGURE_LOCK.toml").read_text())
assert FLOCK["status"] == "agreed"

import logging
logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

# ---- house style, from the lock and S447 (as draw_G.py)
FONT = FLOCK["type"]["font_families"][0]
PT = float(FLOCK["type"]["font_min_pt"])
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LINE_MIN = float(FLOCK["lines"]["line_min_pt"])
CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
OK = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"], CAT))
OKABE_GREY = "#999999"
GREY_NOTE = "#5A5A5A"          # S447 GREY_NOTE (7:1 on white)
PALE = "#D9D9D9"               # both pass tile (alt4)
MM = 1 / 25.4
MM_PER_PT = 25.4 / 72
LW_AX = max(0.5, LINE_MIN)
plt.rcParams.update({"font.family": FONT, "font.size": PT, "pdf.fonttype": 42, "svg.fonttype": "none",
                     "axes.linewidth": LW_AX, "xtick.major.width": LW_AX, "ytick.major.width": LW_AX,
                     "xtick.minor.width": LW_AX, "xtick.major.size": 2, "ytick.major.size": 2, "xtick.labelsize": PT,
                     "ytick.labelsize": PT, "axes.labelsize": PT, "legend.fontsize": PT, "axes.edgecolor": "#000000",
                     "text.color": "#000000", "axes.labelcolor": "#000000", "axes.grid": False})
BOOT_SEED, N_BOOT = 20261013, 10000
MINUS = "−"
HF = 0.6                       # a group header line, as a share of a row
TIMES = "×"


SHOW_COUNTS = True
CENTRE = "mean"          # "median" (Valerio, 25 Oct: "Show me b1b with median first"): the median of the 11 variant gains, no interval


def ms(mm):
    return mm / MM_PER_PT


def sgn(x, fmt="{:+.1f}"):
    return fmt.format(x).replace("-", MINUS)


# ---- data
S = json.loads((DATA / "summary.json").read_text())
COV = json.loads((DATA / "coverage_check.json").read_text())
rows = list(csv.DictReader(open(DATA / "attempts.csv")))
for r in rows:
    r["passed"] = int(r["passed"])
if (len(rows), sum(r["passed"] for r in rows)) != (2420, 1692):
    sys.exit("NOT REPRODUCED: attempts.csv is not 2,420 / 1,692")
VARS = S["variants_in_order"]
STRATS = S["strategies_in_order"]
SLAB = S["strategy_labels"]
LABEL = {v: S["per_variant"][v]["label"] for v in VARS}
MODEL = {v: S["per_variant"][v]["model"] for v in VARS}
GEMINI = {v: MODEL[v].startswith("gemini") for v in VARS}
OPS = sorted({r["op_id"] for r in rows})
assert len(VARS) == 11 and len(OPS) == 20 and len(STRATS) == 11
IDX = {(r["variant_id"], r["strategy"], r["op_id"]): r for r in rows}
assert len(IDX) == 2420
COSTS = ["generator_calls", "latency_s", "output_tokens"]
COST_HEAD = {"generator_calls": "model\ncalls", "latency_s": "wall\ntime", "output_tokens": "output\ntokens"}


def boot(diffs_by_op, n=N_BOOT, seed=BOOT_SEED):
    """coverage_check.py's boot(), unchanged: 95% percentile interval of the mean over operations."""
    rng = random.Random(seed)
    ops = list(diffs_by_op)
    msx = []
    for _ in range(n):
        s = [diffs_by_op[rng.choice(ops)] for _ in ops]
        msx.append(sum(s) / len(s))
    msx.sort()
    return round(msx[int(0.025 * n)], 1), round(msx[int(0.975 * n) - 1], 1)


def contrast(arm, base):
    c = {"arm": arm, "base": base, "rescued": 0, "lost": 0, "both_pass": 0, "both_fail": 0, "tiles": {},
         "per_variant": {}}
    per_op = defaultdict(list)
    sums = {k: [0.0, 0.0] for k in COSTS}
    for v in VARS:
        rv = lv = 0
        for o in OPS:
            a, b = IDX[(v, base, o)], IDX[(v, arm, o)]
            pa, pb = a["passed"], b["passed"]
            kind = ("rescued" if pb else "both_fail") if not pa else ("both_pass" if pb else "lost")
            c[kind] += 1
            c["tiles"][(v, o)] = kind
            rv += kind == "rescued"
            lv += kind == "lost"
            per_op[o].append(pb - pa)
            for k in COSTS:
                x, y = a[k], b[k]
                assert x != "" and y != "", (v, o, k)   # every row has a value (coverage_check.json coverage)
                sums[k][0] += float(x)
                sums[k][1] += float(y)
        c["per_variant"][v] = {"rescued": rv, "lost": lv, "gain_points": 100 * (rv - lv) / len(OPS)}
    n = len(VARS) * len(OPS)
    c["n_pairs"] = n
    c["net_points"] = 100 * (c["rescued"] - c["lost"]) / n
    c["interval_95_ops"] = boot({o: 100 * sum(x) / len(x) for o, x in per_op.items()})
    c["cost_multiple_of_sums"] = {k: sums[k][1] / sums[k][0] for k in COSTS}
    c["cost_sums"] = {k: {"base": sums[k][0], "arm": sums[k][1]} for k in COSTS}
    c["median_variant_gain"] = st.median(c["per_variant"][v]["gain_points"] for v in VARS)
    c["variants_up"] = sum(c["per_variant"][v]["gain_points"] > 0 for v in VARS)
    c["variants_down"] = sum(c["per_variant"][v]["gain_points"] < 0 for v in VARS)
    return c


# the five contrasts of the task, in the shared strategy order
MAIN = [("free_form_n3_best", "free_form"), ("free_form_n3_combined", "free_form"),
        ("coder_v2_n1_cell3_best", "coder_v2_n1"), ("coder_v2_n1_cell3_combined", "coder_v2_n1"),
        ("coder_v2_n3", "coder_v2_n1")]
ALL_FF = [(s, "free_form") for s in STRATS if s != "free_form"]
C = {}
for arm, base in MAIN + ALL_FF:
    C[(arm, base)] = contrast(arm, base)

# ---- reproduce coverage_check.json gap_best_of_3 exactly
for arm, base in MAIN:
    c, ref = C[(arm, base)], COV["gap_best_of_3"][f"{arm} vs {base}"]
    mine = {"n_pairs": c["n_pairs"], "rescued": c["rescued"], "lost": c["lost"], "both_pass": c["both_pass"],
            "both_fail": c["both_fail"], "net_points": round(c["net_points"], 1),
            "interval_95_ops": list(c["interval_95_ops"]),
            "cost_multiple_of_sums": {k: round(c["cost_multiple_of_sums"][k], 2) for k in COSTS},
            "per_variant": {v: {"rescued": c["per_variant"][v]["rescued"], "lost": c["per_variant"][v]["lost"]}
                            for v in VARS}}
    theirs = {k: ref[k] for k in mine}
    theirs["cost_multiple_of_sums"] = {k: ref["cost_multiple_of_sums"][k] for k in COSTS}
    if mine != theirs:
        sys.exit(f"NOT REPRODUCED: {arm} vs {base}\n mine   {mine}\n theirs {theirs}")
# the all-against-free-form rows check against the strategy pass counts in summary.json
for arm, base in ALL_FF:
    c = C[(arm, base)]
    pa = sum(S["per_variant"][v]["by_strategy"][arm][0] for v in VARS)
    pb = sum(S["per_variant"][v]["by_strategy"][base][0] for v in VARS)
    assert c["rescued"] - c["lost"] == pa - pb, arm
print("reproduced: 2,420 / 1,692 and coverage_check.json gap_best_of_3 (5 contrasts), equal")

GROUPS_MAIN = [("against free-form", MAIN[:2]), ("against structured", MAIN[2:])]
GROUPS_ALL = [("against free-form", ALL_FF), ("against structured", MAIN[2:])]


def xm(m):
    return (f"{m:.1f}" if m >= 10 else f"{m:.2f}") + TIMES


# ---- helpers (as draw_G.py)
class Fig:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.f = plt.figure(figsize=(w * MM, h * MM))

    def ax(self, x, top, w, h):
        return self.f.add_axes([x / self.w, 1 - (top + h) / self.h, w / self.w, h / self.h])

    def text(self, x, top, s, **kw):
        return self.f.text(x / self.w, 1 - top / self.h, s, **kw)


def letter(F):
    F.text(0.6, 0.6, "b", fontsize=PT_LETTER, fontweight=FLOCK["type"]["panel_letter_weight"], va="top", ha="left")


def finish(fig):
    """draw_G.py's finish(): no ligatures, and every text whole on the page, else no file is written."""
    from matplotlib.text import Text
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    px = fig.dpi * MM
    W, H = fig.get_figwidth() / MM, fig.get_figheight() / MM
    off = []
    for t_ in fig.findobj(Text):
        if t_.get_visible() and t_.get_text().strip():
            b = t_.get_window_extent(rend)
            if b.x0 / px < -0.01 or b.y0 / px < -0.01 or b.x1 / px > W + 0.01 or b.y1 / px > H + 0.01:
                off.append(t_.get_text())
    if off:
        raise SystemExit(f"text past the page edge: {off}")


SIZES = {}


def save(F, name):
    finish(F.f)
    F.f.savefig(OUT / f"{name}.pdf", metadata=fig_repro.pdf_metadata(name))
    F.f.savefig(OUT / f"{name}.png", dpi=600)
    fig_repro.check_pdf_deterministic(OUT / f"{name}.pdf")
    plt.close(F.f)
    SIZES[name] = (F.w, F.h)
    print(f"wrote {name} ({F.w:.0f} x {F.h:.1f} mm)")


def spine_off(ax, *names):
    for s in names:
        ax.spines[s].set_visible(False)


def variant_marker(ax, x, y, v, d_mm, colour=OK["blue"], z=5):
    if GEMINI[v]:
        ax.plot(x, y, "o", ms=ms(d_mm), mfc=colour, mec=colour, mew=0.4, ls="", zorder=z)
    else:
        ax.plot(x, y, "o", ms=ms(d_mm - 0.15), mfc="#FFFFFF", mec=colour, mew=0.5, ls="", zorder=z)


def key_handles(d_mm, net=True, net_label="net of 220 pairs, 95% interval"):
    h = [Line2D([], [], ls="", marker="o", ms=ms(d_mm), mfc=OK["blue"], mec=OK["blue"], mew=0.4,
                label="Gemini, cloud (4)"),
         Line2D([], [], ls="", marker="o", ms=ms(d_mm - 0.15), mfc="#FFFFFF", mec=OK["blue"], mew=0.5,
                label="open-weight (7)")]
    if net:
        h.append(Line2D([], [], color="#000000", lw=1.0, marker="D", ms=ms(1.5), mfc="#000000", mec="#000000",
                        label=net_label))
    return h


# ---- alt1: contrast forest; alt1b adds every strategy against free-form
def forest(groups, name, row_mm, dot_mm=1.0, pitch_mm=1.1):
    lab_w, plot_w = 35.0, 54.0
    col_x = {"rl": lab_w + plot_w + 9.0}
    for i, k in enumerate(COSTS):
        col_x[k] = col_x["rl"] + 13.5 + 12.0 * i
    W = col_x[COSTS[-1]] + 6.0
    head_h = 13.0
    n_rows = sum(len(g) + HF for _, g in groups)           # a header line per group, HF of a row
    plot_h = n_rows * row_mm
    H = head_h + plot_h + 10.0
    F = Fig(W, H)
    letter(F)
    ax = F.ax(lab_w, head_h, plot_w, plot_h)
    y = 0
    ys, vals = [], []
    for gname, items in groups:
        ax.text(-lab_w / plot_w, y + HF * 0.6, gname, transform=ax.get_yaxis_transform(), ha="left", va="center",
                color=GREY_NOTE, fontstyle="italic")
        y += HF
        for arm, base in items:
            c = C[(arm, base)]
            yc = y + 0.72                                    # interval line, dots stacked upward from it
            lo, hi = c["interval_95_ops"]
            if CENTRE == "median_split":   # Valerio, 25 Oct: "two b1b median, only gemini vs open"
                gm = st.median(c["per_variant"][v]["gain_points"] for v in VARS if GEMINI[v])
                om = st.median(c["per_variant"][v]["gain_points"] for v in VARS if not GEMINI[v])
                c["median_gemini"], c["median_open"] = gm, om
                ax.plot(gm, yc - 0.05, "D", ms=ms(1.5), mfc="#000000", mec="#000000", zorder=7)
                ax.plot(om, yc + 0.17, "D", ms=ms(1.5), mfc="#FFFFFF", mec="#000000", mew=0.7, zorder=7)
            elif CENTRE == "median":
                ax.plot(c["median_variant_gain"], yc, "D", ms=ms(1.5), mfc="#000000", mec="#000000", zorder=7)
            else:
                ax.plot([lo, hi], [yc, yc], color="#000000", lw=1.0, solid_capstyle="butt", zorder=6)
                ax.plot(c["net_points"], yc, "D", ms=ms(1.5), mfc="#000000", mec="#000000", zorder=7)
            g = defaultdict(list)
            for v in VARS:
                g[c["per_variant"][v]["gain_points"]].append(v)
            band = row_mm * 0.72 - 1.0 - dot_mm / 2           # room above the line, in mm
            for x, vv in g.items():
                vv.sort(key=lambda v: (not GEMINI[v], VARS.index(v)))
                k = len(vv)
                step = pitch_mm if (k - 1) * pitch_mm <= band else band / max(k - 1, 1)
                for j, v in enumerate(vv):
                    variant_marker(ax, x, yc - (1.0 + dot_mm / 2 + j * step) / row_mm, v, dot_mm)
                if (k - 1) * pitch_mm > band:          # a stack that does not fit: squeezed, with its count (S447)
                    print(f"  {name}: {k} ties at {x} in {SLAB[arm]} squeezed to {step:.2f} mm, count printed")
                    ym = yc - (1.0 + dot_mm / 2 + (k - 1) * step / 2) / row_mm
                    right = min([d - x for d in g if d > x] + [99])
                    left = min([x - d for d in g if d < x] + [99])
                    side = 1 if right >= left else -1
                    if SHOW_COUNTS:                    # Valerio, 25 Oct: B-1b "without the black numbers on the dots"
                        ax.text(x + side * 1.6, ym, str(k), ha="left" if side > 0 else "right", va="center", zorder=8)
                vals.append(x)
            vals += [lo, hi]
            ax.text(-0.02, yc - 0.15, SLAB[arm], transform=ax.get_yaxis_transform(), ha="right", va="center")
            for key, s in [("rl", f"{c['rescued']} / {c['lost']}")] + \
                          [(k, xm(c["cost_multiple_of_sums"][k])) for k in COSTS]:
                F.f.text(col_x[key] / W, 0, s, ha="center", va="center",
                         transform=matplotlib.transforms.blended_transform_factory(F.f.transFigure, ax.transData)
                         ).set_y(yc - 0.15)
            ys.append(yc)
            y += 1
    ax.set_ylim(n_rows, 0)
    ax.set_yticks([])
    lo = 10 * math.floor(min(vals) / 10)
    hi = 10 * math.ceil(max(vals) / 10)
    lo, hi = min(lo, -10), max(hi, 10)
    ax.set_xlim(lo - 2, hi + 2)
    step = 10 if hi - lo <= 50 else 20
    ax.set_xticks(range(int(math.ceil(lo / step) * step), int(hi) + 1, step))
    ax.set_xticklabels([sgn(t, "{:+d}") if t else "0" for t in ax.get_xticks().astype(int)])
    ax.axvline(0, color=OKABE_GREY, lw=max(0.6, LINE_MIN), zorder=1)
    ax.set_xlabel("change in pass rate, same variant and operation (percentage points)", labelpad=2)
    spine_off(ax, "top", "right", "left")
    # column heads
    F.text(col_x["rl"], head_h - 0.6, "rescued\n/ lost", ha="center", va="bottom", linespacing=1.0)
    for k in COSTS:
        F.text(col_x[k], head_h - 0.6, COST_HEAD[k], ha="center", va="bottom", linespacing=1.0)
    F.text((col_x[COSTS[0]] + col_x[COSTS[-1]]) / 2, head_h - 7.6, "cost, as a multiple",
           ha="center", va="bottom", color=GREY_NOTE)
    hs = key_handles(dot_mm, net=CENTRE != "median_split",
                     net_label="median of the 11 variant gains" if CENTRE == "median" else "net of 220 pairs, 95% interval")
    if CENTRE == "median_split":
        hs += [Line2D([], [], ls="", marker="D", ms=ms(1.5), mfc="#000000", mec="#000000", label="median, Gemini"),
               Line2D([], [], ls="", marker="D", ms=ms(1.5), mfc="#FFFFFF", mec="#000000", mew=0.7,
                      label="median, open-weight")]
    F.f.legend(handles=hs, loc="upper left", bbox_to_anchor=(4.0 / W, 1 - 1.0 / H),
               ncol=2 if CENTRE == "median_split" else 3,
               frameon=False, handlelength=1.4, handletextpad=0.4, columnspacing=1.0, borderaxespad=0, borderpad=0)
    save(F, name)


# ---- alt2: diverging flip bars, stacked by variant, cost in a margin
def flips():
    lab_w, plot_w = 35.0, 62.0
    cols = ["net"] + COSTS
    col_x = {}
    for i, k in enumerate(cols):
        col_x[k] = lab_w + plot_w + 8.0 + 12.0 * i
    W = col_x[cols[-1]] + 6.0
    head_h, row_mm, bar_mm = 13.0, 6.5, 3.6
    groups = GROUPS_MAIN
    n_rows = sum(len(g) + HF for _, g in groups)
    plot_h = n_rows * row_mm
    H = head_h + plot_h + 10.0
    F = Fig(W, H)
    letter(F)
    ax = F.ax(lab_w, head_h, plot_w, plot_h)
    bh = bar_mm / row_mm
    order = [v for v in VARS if GEMINI[v]] + [v for v in VARS if not GEMINI[v]]    # Gemini next to 0
    vmax = max(max(C[k]["rescued"], C[k]["lost"]) for k in MAIN)
    lim = 5 * math.ceil((vmax + 6) / 5)
    blend = matplotlib.transforms.blended_transform_factory(F.f.transFigure, ax.transData)
    y = 0
    for gname, items in groups:
        ax.text(-lab_w / plot_w, y + HF * 0.6, gname, transform=ax.get_yaxis_transform(), ha="left", va="center",
                color=GREY_NOTE, fontstyle="italic")
        y += HF
        for arm, base in items:
            c = C[(arm, base)]
            yc = y + 0.5
            for side, kind, colour in ((1, "rescued", OK["blue"]), (-1, "lost", OK["vermillion"])):
                x0 = 0
                for v in order:
                    k = c["per_variant"][v][kind]
                    if not k:
                        continue
                    ax.add_patch(Rectangle((x0 if side > 0 else -x0 - k, yc - bh / 2), k, bh,
                                           fc=colour if GEMINI[v] else "#FFFFFF", ec="#FFFFFF" if GEMINI[v] else colour,
                                           lw=0.6 if GEMINI[v] else 0.5, zorder=4 if GEMINI[v] else 3))
                    x0 += k
                tot = c[kind]
                ax.text(side * (tot + 0.8), yc, str(tot), ha="left" if side > 0 else "right", va="center")
            ax.text(-0.02, yc, SLAB[arm], transform=ax.get_yaxis_transform(), ha="right", va="center")
            vals = [("net", sgn(c["net_points"]))] + [(k, xm(c["cost_multiple_of_sums"][k])) for k in COSTS]
            for key, s in vals:
                t = F.f.text(col_x[key] / W, 0, s, ha="center", va="center", transform=blend)
                t.set_y(yc)
            y += 1
    ax.set_ylim(n_rows, 0)
    ax.set_yticks([])
    ax.set_xlim(-lim, lim)
    ax.set_xticks(range(-lim + lim % 10, lim + 1, 10))
    ax.set_xticklabels([str(abs(int(t))) for t in ax.get_xticks()])
    ax.axvline(0, color="#000000", lw=LW_AX, zorder=6)
    ax.set_xlabel("pairs lost (left) and rescued (right), of 220", labelpad=2)
    spine_off(ax, "top", "right", "left")
    F.text(col_x["net"], head_h - 0.6, "net\n(points)", ha="center", va="bottom", linespacing=1.0)
    for k in COSTS:
        F.text(col_x[k], head_h - 0.6, COST_HEAD[k], ha="center", va="bottom", linespacing=1.0)
    F.text((col_x[COSTS[0]] + col_x[COSTS[-1]]) / 2, head_h - 7.6, "cost, as a multiple", ha="center",
           va="bottom", color=GREY_NOTE)
    hs = [Rectangle((0, 0), 1, 1, fc=OK["blue"], ec=OK["blue"], lw=0.5, label="rescued"),
          Rectangle((0, 0), 1, 1, fc=OK["vermillion"], ec=OK["vermillion"], lw=0.5, label="lost"),
          Rectangle((0, 0), 1, 1, fc=GREY_NOTE, ec=GREY_NOTE, lw=0.5, label="Gemini, cloud: filled"),
          Rectangle((0, 0), 1, 1, fc="#FFFFFF", ec=GREY_NOTE, lw=0.5, label="open-weight: open")]
    F.f.legend(handles=hs, loc="upper left", bbox_to_anchor=(4.0 / W, 1 - 1.0 / H), ncol=4, frameon=False,
               handlelength=1.0, handleheight=0.8, handletextpad=0.4, columnspacing=1.0, borderaxespad=0,
               borderpad=0)
    save(F, "B_alt2_flip_bars")


# ---- alt3: net gain against the model-call multiple, log x with evenly spaced ticks; two small multiples, names on
# top. Point values only (no error bars), so E2 is met without the per-variant points; the intervals are in alt1.
FAM_COLOUR = {"free-form": OK["black"], "introspection": OK["orange"], "structured": OK["blue"]}
FAM_MARK = {"free-form": "o", "introspection": "s", "structured": "D"}


def place_labels(F, ax, pts, names, pad_mm=0.6):
    """After draw_G.py's place_labels(): each name beside its point where it fits, else the nearest free place with a
    leader line. A name never covers a point, another name, a leader or the zero line, and a leader never crosses a
    name, a point or another leader. Orders are tried (seeded) and the layout with the shortest total offset is kept."""
    fig = F.f
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    tr = ax.transData
    px = fig.dpi * MM

    def to_mm(x, y):
        X, Y = tr.transform((x, y))
        return X / px, Y / px

    bb = ax.get_window_extent(rend)
    box = (bb.x0 / px, bb.y0 / px, bb.x1 / px, bb.y1 / px)
    dots = [to_mm(*p) for p in pts]
    zero = to_mm(1, 0)[1]
    r_dot = 1.2
    sizes = []
    for nm in names:
        t = ax.text(0, 0, nm)
        b0 = t.get_window_extent(rend)
        sizes.append((b0.width / px, b0.height / px))
        t.remove()

    def seg_hits_box(p, q, b, grow):
        for k in range(41):
            x = p[0] + (q[0] - p[0]) * k / 40
            y = p[1] + (q[1] - p[1]) * k / 40
            if b[0] - grow < x < b[2] + grow and b[1] - grow < y < b[3] + grow:
                return True
        return False

    def segs_cross(a, b, c, d):
        def o(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0

    def layout(order):
        placed, leaders, out, cost = {}, {}, {}, 0.0
        for i in order:
            cx, cy = dots[i]
            w, hh = sizes[i]
            cands = []
            for d in (1.4, 2.5, 4.0, 5.5, 7.0, 9.0, 11.0, 14.0, 17.0, 20.0):
                cands += [(cx + d, cy - hh / 2), (cx - d - w, cy - hh / 2), (cx - w / 2, cy + d * 0.8),
                          (cx - w / 2, cy - d * 0.8 - hh), (cx + d * 0.6, cy + d * 0.6),
                          (cx + d * 0.6, cy - d * 0.6 - hh), (cx - w - d * 0.6, cy + d * 0.6),
                          (cx - w - d * 0.6, cy - d * 0.6 - hh), (cx - w + 1.0, cy - d - hh), (cx - w + 1.0, cy + d),
                          (cx - 1.0, cy - d - hh), (cx - 1.0, cy + d)]
            for (bx, by) in cands:
                b = (bx, by, bx + w, by + hh)
                if b[0] < box[0] + 0.8 or b[2] > min(box[2] + 6, F.w - 0.5) or b[1] < box[1] + 0.8 or b[3] > box[3]:
                    continue
                if b[1] - 0.3 < zero < b[3] + 0.3:
                    continue
                if any(not (b[2] + pad_mm < q[0] or q[2] + pad_mm < b[0] or b[3] + 0.3 < q[1] or q[3] + 0.3 < b[1])
                       for q in placed.values()):
                    continue
                if any(b[0] - r_dot < dx < b[2] + r_dot and b[1] - r_dot < dy < b[3] + r_dot for dx, dy in dots):
                    continue
                if any(seg_hits_box(s[0], s[1], b, 0.3) for s in leaders.values()):
                    continue
                far = max(abs((b[0] + b[2]) / 2 - cx) - w / 2, abs((b[1] + b[3]) / 2 - cy) - hh / 2) > 1.6
                seg = None

                def gap(dx, dy):
                    return math.hypot(max(b[0] - dx, 0, dx - b[2]), max(b[1] - dy, 0, dy - b[3]))
                own = gap(cx, cy)
                if not far and any(j != i and gap(dx, dy) < own + 1.5 for j, (dx, dy) in enumerate(dots)):
                    continue                          # a name must sit nearer its own point than any other
                if far:
                    e = (min(max(cx, b[0]), b[2]), min(max(cy, b[1]), b[3]))
                    start = (cx + (e[0] - cx) * 0.9 / max(math.dist((cx, cy), e), 1e-9),
                             cy + (e[1] - cy) * 0.9 / max(math.dist((cx, cy), e), 1e-9))
                    seg = (start, e)
                    if any(seg_hits_box(start, e, q, 0.3) for q in placed.values()):
                        continue
                    if any(j != i and seg_hits_box(start, e, (dx, dy, dx, dy), r_dot)
                           for j, (dx, dy) in enumerate(dots)):
                        continue
                    if any(segs_cross(start, e, s[0], s[1]) for s in leaders.values()):
                        continue
                placed[i] = b
                if seg:
                    leaders[i] = seg
                cost += math.dist((cx, cy), ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
                break
            else:
                return None, math.inf
        return (placed, leaders), cost

    rng = random.Random(BOOT_SEED)
    best, best_cost = None, math.inf
    base = sorted(range(len(pts)), key=lambda i: -pts[i][1])
    for t_ in range(400):
        order = base if t_ == 0 else rng.sample(base, len(base))
        res, cost = layout(order)
        if cost < best_cost:
            best, best_cost = res, cost
    if best is None:
        raise SystemExit(f"no layout for the labels {names}")
    placed, leaders = best
    inv = tr.inverted()
    for i, b in placed.items():
        tx, ty = inv.transform(((b[0] + b[2]) / 2 * px, (b[1] + b[3]) / 2 * px))
        ax.text(tx, ty, names[i], ha="center", va="center", zorder=8)
        if i in leaders:
            (sx, sy), (ex, ey) = leaders[i]
            a0, a1 = inv.transform((sx * px, sy * px)), inv.transform((ex * px, ey * px))
            ax.plot([a0[0], a1[0]], [a0[1], a1[1]], color=GREY_NOTE, lw=max(0.4, LINE_MIN), zorder=4)


def cost_scatter():
    W, H = 136.0, 66.0
    F = Fig(W, H)
    letter(F)
    top, h = 12.0, 40.0
    fam = S["family_of_strategy"]
    panels = [("against free-form", ALL_FF, 13.0, 78.0, [1, 2, 4, 8, 16, 32], SLAB),
              ("against structured", MAIN[2:], 104.0, 30.0, [1, 1.41, 2],
               {k: SLAB[k].replace("structured ", "") for k in SLAB})]
    allv = [C[k]["net_points"] for k in ALL_FF + MAIN[2:]]
    ylo, yhi = 10 * math.floor(min(allv) / 10) - 3, 10 * math.ceil(max(allv) / 10) + 3
    drawn = {}
    axs = []
    for title, items, x0, w, ticks, names in panels:
        ax = F.ax(x0, top, w, h)
        axs.append(ax)
        F.text(x0 + w / 2, top - 1.0, title, ha="center", va="bottom")
        ax.set_xscale("log", base=2)
        xs = [C[k]["cost_multiple_of_sums"]["generator_calls"] for k in items]
        ax.set_xlim(min(ticks[0], min(xs)) / 2 ** 0.3, max(ticks[-1], max(xs)) * 2 ** 0.3)
        ax.set_xticks(ticks, [f"{t:g}" if t != 1.41 else "1.4" for t in ticks])
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.axhline(0, color=OKABE_GREY, lw=max(0.6, LINE_MIN), zorder=1)
        ax.set_ylim(ylo, yhi)
        ax.set_yticks(range(int(math.ceil(ylo / 10) * 10), int(yhi) + 1, 10))
        ax.set_yticklabels([sgn(t, "{:+d}") if t else "0" for t in ax.get_yticks().astype(int)])
        pts = []
        for k in items:
            c = C[k]
            x, yv = c["cost_multiple_of_sums"]["generator_calls"], c["net_points"]
            f_ = fam[k[0]]
            ax.plot(x, yv, FAM_MARK[f_], ms=ms(1.7 if f_ != "structured" else 1.6), mfc=FAM_COLOUR[f_],
                    mec="#FFFFFF", mew=0.3, zorder=6)
            pts.append((x, yv))
            drawn[f"{k[0]} vs {k[1]}"] = {"calls_multiple": round(x, 3), "net_points": round(yv, 2)}
        ax.set_xlabel("model calls, as a multiple (log scale)" if w > 50 else "model calls,\nas a multiple (log)",
                      labelpad=2)
        spine_off(ax, "top", "right")
        ax._pts, ax._names = pts, [names[k[0]] for k in items]
    axs[0].set_ylabel("change in pass rate\n(percentage points)", labelpad=2)
    axs[1].set_yticklabels([])
    for ax in axs:
        place_labels(F, ax, ax._pts, ax._names)
    hs = [Line2D([], [], ls="", marker=FAM_MARK[f_], ms=ms(1.7), mfc=FAM_COLOUR[f_], mec="#FFFFFF", mew=0.3,
                 label=f_ + (" family" if f_ != "structured" else " family")) for f_ in FAM_COLOUR]
    hs.append(Line2D([], [], ls="", label="one point = net of 220 pairs"))
    F.f.legend(handles=hs, loc="upper left", bbox_to_anchor=(4.0 / W, 1 - 1.0 / H), ncol=4, frameon=False,
               handlelength=0.8, handletextpad=0.4, columnspacing=1.2, borderaxespad=0, borderpad=0)
    save(F, "B_alt3_cost_scatter")
    return drawn


# ---- alt4: Supplementary paired tiles, 11 variants x 20 operations per contrast
def tiles():
    W = 183.0
    lab_w, gap = 33.0, 6.0
    grid_w = (W - lab_w - gap - 2.0) / 2
    tile_w = grid_w / len(OPS)
    tile_h = 3.1
    grid_h = tile_h * len(VARS)
    title_h, foot_h, vgap = 8.6, 8.0, 2.0
    block_h = title_h + grid_h + foot_h + vgap
    key_h = 9.0                            # two key lines (critic B: plain names do not fit on one)
    H = key_h + 3 * block_h
    F = Fig(W, H)                          # a Supplementary figure of one panel: no panel letter
    TILE = {"rescued": (OK["blue"], OK["blue"]), "lost": (OK["vermillion"], OK["vermillion"]),
            "both_pass": (PALE, PALE), "both_fail": ("#FFFFFF", OKABE_GREY)}
    # operations: dataset, then the operation number in its id
    ds = {r["op_id"]: r["dataset"] for r in rows}
    num = {o: int(o.split("_")[1]) for o in OPS}
    ops = sorted(OPS, key=lambda o: (ds[o] != "RNA-seq", num[o]))
    slots = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]
    for (arm, base), (r_, c_) in zip(MAIN, slots):
        cc = C[(arm, base)]
        x0 = lab_w + c_ * (grid_w + gap)
        top = key_h + r_ * block_h + title_h
        ax = F.ax(x0, top, grid_w, grid_h)
        for i, v in enumerate(VARS):
            for j, o in enumerate(ops):
                fc, ec = TILE[cc["tiles"][(v, o)]]
                ax.add_patch(Rectangle((j + 0.06, i + 0.08), 0.88, 0.84, fc=fc, ec=ec, lw=0.4))
        ax.set_xlim(0, len(ops))
        ax.set_ylim(len(VARS), 0)
        ax.set_yticks(np.arange(len(VARS)) + 0.5, [LABEL[v] for v in VARS] if c_ == 0 else [])
        ax.set_xticks(np.arange(len(ops)) + 0.5, [str(num[o]) for o in ops])
        ax.tick_params(length=0, pad=1.5)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.axvline(10, color="#000000", lw=0.6)
        F.text(x0, top - 4.3, f"{SLAB[arm]} against {SLAB[base]}", ha="left", va="bottom")
        F.text(x0, top - 0.8, f"rescued {cc['rescued']}, lost {cc['lost']} of {cc['n_pairs']} pairs", ha="left", va="bottom",
               color=GREY_NOTE)
        F.text(x0 + grid_w / 4, top + grid_h + 4.0, "RNA-seq operations", ha="center", va="top", color=GREY_NOTE)
        F.text(x0 + 3 * grid_w / 4, top + grid_h + 4.0, "survival operations", ha="center", va="top",
               color=GREY_NOTE)
    # Gemini rows marked: a filled or open marker before each name, left grids only
    for r_ in range(3):
        top = key_h + r_ * block_h + title_h
        for i, v in enumerate(VARS):
            yy = top + (i + 0.5) * tile_h
            F.f.lines.append(Line2D([1.6 / W], [1 - yy / H], transform=F.f.transFigure, ls="", marker="o",
                                    ms=ms(1.2 if GEMINI[v] else 1.05), mfc=OK["black"] if GEMINI[v] else "#FFFFFF",
                                    mec="#000000", mew=0.5))
    hs = [Rectangle((0, 0), 1, 1, fc=TILE[k][0], ec=TILE[k][1], lw=0.4, label=lab) for k, lab in
          [("rescued", "rescued (only the first named passed)"), ("lost", "lost (only the second named passed)"),
           ("both_pass", "both passed"), ("both_fail", "both failed")]]
    hs += [Line2D([], [], ls="", marker="o", ms=ms(1.2), mfc="#000000", mec="#000000", label="Gemini, cloud"),
           Line2D([], [], ls="", marker="o", ms=ms(1.05), mfc="#FFFFFF", mec="#000000", mew=0.5, label="open-weight")]
    F.f.legend(handles=hs, loc="upper left", bbox_to_anchor=(4.0 / W, 1 - 1.0 / H), ncol=3, frameon=False,
               handlelength=1.0, handleheight=0.8, handletextpad=0.4, columnspacing=2.0, borderaxespad=0,
               borderpad=0)
    save(F, "B_alt4_tiles_supplementary")


def combined():
    from matplotlib.image import imread
    items = [("alt1: contrast forest (five contrasts)", "B_alt1_forest"),
             ("alt1b: forest, every strategy against free-form", "B_alt1b_forest_all"),
             ("alt2: diverging flip bars", "B_alt2_flip_bars"),
             ("alt3: net against model-call multiple (matched budget)", "B_alt3_cost_scatter"),
             ("alt4: Supplementary, paired tiles", "B_alt4_tiles_supplementary")]
    hs = [SIZES[n][1] for _, n in items]
    fig = plt.figure(figsize=(2 * 190 * MM, (max(hs[0] + hs[2] + hs[3], hs[1] + hs[4]) + 30) * MM))
    from matplotlib.gridspec import GridSpec
    left = [items[0], items[2], items[3]]
    right = [items[1], items[4]]
    gl = GridSpec(3, 1, left=0.01, right=0.49, top=0.975, bottom=0.01,
                  height_ratios=[SIZES[n][1] + 8 for _, n in left], hspace=0.08)
    gr = GridSpec(2, 1, left=0.51, right=0.99, top=0.975, bottom=0.01,
                  height_ratios=[SIZES[n][1] + 8 for _, n in right], hspace=0.08)
    for g, its in ((gl, left), (gr, right)):
        for k, (title, name) in enumerate(its):
            a = fig.add_subplot(g[k])
            a.imshow(imread(OUT / f"{name}.png"))
            a.set_axis_off()
            a.set_title(f"{title} ({SIZES[name][0]:.0f} x {SIZES[name][1]:.0f} mm)", fontsize=PT + 2, loc="left")
    fig.savefig(OUT / "B_options.png", dpi=300)
    plt.close(fig)
    print("wrote B_options")


if __name__ == "__main__":
    forest(GROUPS_MAIN, "B_alt1_forest", row_mm=8.6)
    forest(GROUPS_ALL, "B_alt1b_forest_all", row_mm=6.2, dot_mm=0.95, pitch_mm=1.0)
    flips()
    drawn = cost_scatter()
    tiles()
    combined()
    numbers = {"provenance": {"script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
                              "script_sha256": fig_repro.sha256_file(Path(__file__)), "inputs_sha256": INPUTS,
                              "bootstrap": f"{N_BOOT} resamples of the 20 operations, seed {BOOT_SEED}",
                              "sizes_mm": SIZES},
               "contrasts": {}}
    for k, c in C.items():
        numbers["contrasts"][f"{k[0]} vs {k[1]}"] = {
            "arm_label": SLAB[k[0]], "base_label": SLAB[k[1]], "n_pairs": c["n_pairs"], "rescued": c["rescued"],
            "lost": c["lost"], "both_pass": c["both_pass"], "both_fail": c["both_fail"],
            "net_points": round(c["net_points"], 2), "interval_95_ops": c["interval_95_ops"],
            "base_passes": c["both_pass"] + c["lost"], "base_fails": c["both_fail"] + c["rescued"],
            "lost_pct_of_base_passes": round(100 * c["lost"] / (c["both_pass"] + c["lost"]), 1),
            "rescued_pct_of_base_fails": round(100 * c["rescued"] / (c["both_fail"] + c["rescued"]), 1),
            "median_variant_gain_points": c["median_variant_gain"], "variants_up": c["variants_up"],
            "variants_down": c["variants_down"],
            "cost_multiple_of_sums": {kk: round(x, 3) for kk, x in c["cost_multiple_of_sums"].items()},
            "cost_sums": c["cost_sums"],
            "per_variant": {LABEL[v]: c["per_variant"][v] for v in VARS}}
    numbers["alt3_drawn"] = drawn
    (OUT / "B_numbers.json").write_text(json.dumps(numbers, indent=1) + "\n")
    print(f"{'contrast':52s} resc lost  net    95% ops        med.var up/down  calls  wall  tokens")
    for k in MAIN + ALL_FF:
        c = C[k]
        cm = c["cost_multiple_of_sums"]
        print(f"{SLAB[k[0]] + ' vs ' + SLAB[k[1]]:52s} {c['rescued']:4d} {c['lost']:4d} {c['net_points']:+5.1f} "
              f"[{c['interval_95_ops'][0]:+5.1f}, {c['interval_95_ops'][1]:+5.1f}]  {c['median_variant_gain']:+6.1f}"
              f"  {c['variants_up']:2d}/{c['variants_down']:2d}  {cm['generator_calls']:5.2f} {cm['latency_s']:5.2f} "
              f"{cm['output_tokens']:5.2f}")
    for k in MAIN:
        r_ = numbers["contrasts"][f"{k[0]} vs {k[1]}"]
        print(f"{SLAB[k[0]]}: lost {r_['lost']} of {r_['base_passes']} base passes ({r_['lost_pct_of_base_passes']}%), "
              f"rescued {r_['rescued']} of {r_['base_fails']} base failures ({r_['rescued_pct_of_base_fails']}%)")
    st_ff = [C[(a, "free_form")]["cost_multiple_of_sums"]["generator_calls"] for a in
             ("coder_v2_n1", "coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined", "coder_v2_n3")]
    b3 = C[("free_form_n3_best", "free_form")]["cost_multiple_of_sums"]["generator_calls"]
    print(f"structured arms against free-form: {min(st_ff):.2f}x to {max(st_ff):.2f}x the calls, that is "
          f"{min(st_ff) / b3:.1f} to {max(st_ff) / b3:.1f} times free-form best of 3's {b3:.2f}x")
    for k in MAIN:
        print(SLAB[k[0]], "per variant (rescued, lost):",
              {LABEL[v]: (C[k]["per_variant"][v]["rescued"], C[k]["per_variant"][v]["lost"]) for v in VARS})
