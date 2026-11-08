"""Figure 5 panel e: the current panel on today's data and three alternatives (scratch, 28 Oct; not a plate).

Reads e_data.json (prep.py: S473's own read and compute() on fig5_pull_1028). Every drawn number is computed here from
its points and, where S473 computed the same statistic (rho_all, rho_3to5, e9), the script stops unless they agree.
Each option is drawn at the size it would have on the plate, through S457.finish_plate (no text off the page or on
another text, else nothing is written; PDF, SVG, and a 600 dpi PNG rasterised from the PDF).

Options
  e1_current     S473's panel e as drawn (dot swarm per faithfulness score, median line, rho, n); only its two header
                 texts moved so they fit the page.
  e2_box_rho     a box per faithfulness score over its answers' dots, n per score under the axis, and both of S473's
                 answer-level rho with their question-resample intervals (all scores; scores 3 to 5, the paper's E10).
  e3_stacked     the 503 answers by MiniCheck precision (bins of 0.1), each bar split by faithfulness score in panel
                 d's cividis colours.
  e4_by_strategy per strategy, MiniCheck precision of the answers rated 5 and of those rated 0 to 4: dots, quartile box,
                 median.
"""
import json
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


S457 = mod("S457", ROOT / "scripts/S457_fig2_panels.py")
S463 = sys.modules.get("S463") or mod("S463", ROOT / "scripts/S463_fig2_ranking.py")

import logging
logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

S457.figure_lock_agreed()
plt.rcParams.update(S457.plate_rc("fig5e_opts"))
plt.rcParams["axes.unicode_minus"] = False
PT, MM_PT = S457.PT, S457.MM_PT
GREY, BLACK = S457.DOT_GREY, "#000000"
DOT = S457.DOT_MM / MM_PT


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


DATA = HERE / "e_data.json"
D = json.loads(DATA.read_text())
P = D["points"]
CONFIGS, LABEL = D["configs"], D["labels"]
SOURCES = {"e_data.json": {"path": str(DATA), "sha256": sha(DATA),
                           "made_by": "prep.py (S473 compute on fig5_pull_1028)"},
           "s3_collect": D["inputs"]["s3_collect"], "l3": D["inputs"]["l3"],
           "pull_and_frozen_inputs_sha256": D["inputs"]["inputs_sha256"], "code_sha256": D["code"],
           "draw_e.py": sha(__file__)}


# ---- recount and check against S473's own statistics
def spearman(x, y):
    from scipy import stats
    return float(stats.spearmanr(x, y).statistic)


rho_all = spearman([p["faithfulness"] for p in P], [p["papers_precision"] for p in P])
sub = [p for p in P if p["faithfulness"] >= 3]
rho_35 = spearman([p["faithfulness"] for p in sub], [p["papers_precision"] for p in sub])
five = [p["papers_precision"] for p in P if p["faithfulness"] == 5]
assert abs(rho_all - D["rho_all"]["rho"]) < 1e-12 and D["rho_all"]["answers"] == len(P), "rho_all"
assert abs(rho_35 - D["rho_3to5"]["rho"]) < 1e-12 and D["rho_3to5"]["answers"] == len(sub), "rho_3to5"
assert D["e9"]["rated_5"] == len(five) and D["e9"]["below_half"] == sum(v < 0.5 for v in five), "e9"
assert abs(D["e9"]["median"] - float(np.median(five))) < 1e-12, "e9 median"
NQ = len({p["question_id"] for p in P})
assert NQ == D["rho_all"]["questions"]

CIV6 = None


def cividis6():
    from matplotlib import colormaps
    cm = colormaps[S457.FLOCK["colour"]["continuous"]]
    return ["#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(round(255 * i / 5)))[:3]) for i in range(6)]


CIV6 = cividis6()          # S473.cividis6(): panel d's six colours, score 0 dark to score 5 light


def r(x, nd=4):
    return None if x is None else round(float(x), nd)


def quart(v):
    return {"n": len(v), "q25": r(np.percentile(v, 25)), "median": r(np.median(v)), "q75": r(np.percentile(v, 75)),
            "min": r(min(v)), "max": r(max(v))}


class Canvas:
    def __init__(self, w, h, salt):
        self.W, self.H = w, h
        self.fig = plt.figure(figsize=(w / 25.4, h / 25.4), facecolor="#FFFFFF")

    def axes(self, x, y, w, h):
        return self.fig.add_axes([x / self.W, 1 - (y + h) / self.H, w / self.W, h / self.H])

    def text(self, x, y, s, **kw):
        kw.setdefault("ha", "left"); kw.setdefault("va", "baseline")
        return self.fig.text(x / self.W, 1 - y / self.H, s, **kw)

    def letter(self, x, y):
        self.text(x, y, S457.LETTER_CASE("e"), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT)

    def finish(self, stem, title):
        paths = {k: HERE / f"{stem}.{k}" for k in ("pdf", "svg", "png")}
        S457.finish_plate(self.fig, self.W, self.H, paths, title=title)
        return paths


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def write_numbers(stem, what, numbers, extra=None):
    out = {"option": stem, "what": what, "sources": SOURCES, "numbers": numbers,
           "provisional": "MiniCheck against the papers: 509 of 516 draw-1 answerable rows pulled 28 Oct (L1 not "
                          "ended); faithfulness with passages: S3 collect of 28 Oct"}
    if extra:
        out.update(extra)
    (HERE / f"{stem}.numbers.json").write_text(json.dumps(out, indent=1) + "\n")


def per_score():
    return {k: sorted(p["papers_precision"] for p in P if p["faithfulness"] == k) for k in range(6)}


BY = per_score()
OVERLAPS = {}


def swarm_column(ax, k, vals, ax_w_mm, ax_h_mm, xlim, ylim, half=2.0, key=""):
    mm_x = ax_w_mm / (xlim[1] - xlim[0])
    ys_mm = [v * (ax_h_mm / (ylim[1] - ylim[0])) for v in vals]
    off, over = S457.swarm(ys_mm, half=half, pitch=0.5, dot=S457.DOT_MM)
    OVERLAPS[key] = over
    # critic 28 Oct: dots over the median line and the box (S473:1401-1403 draws them at zorder 5 over the median's 4,
    # "so a score with one answer still shows its dot"); at zorder 3 the median hid the dots that sit on it
    ax.plot([k + o / mm_x for o in off], vals, ls="none", marker="o", ms=DOT, mfc=GREY, mew=0, zorder=7)
    return over


# =====================================================================================================================
# e1: the current panel (S473 draw(), panel e), on today's data
# =====================================================================================================================
def e1():
    # plate: E_X 151, C_TOP 84, E_W 28, C_H 50, letter at E_X - 11 (140); canvas = plate x 140 to 183
    X0, TOP = 140.0, 84.0 - 12.0
    W, H = 183.0 - X0, 50.0 + 12.0 + 12.0
    cv = Canvas(W, H, "e1")
    ax_x, ax_y, ax_w, ax_h = 151.0 - X0, 84.0 - TOP, 28.0, 50.0
    ax = cv.axes(ax_x, ax_y, ax_w, ax_h)
    xlim, ylim = (-0.6, 5.6), (-0.04, 1.04)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xticks(range(6)); ax.set_xticklabels([str(k) for k in range(6)])
    ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(["0", "0.5", "1"])
    clean(ax)
    ax.set_xlabel("Faithfulness score", labelpad=2)
    ax.set_ylabel("MiniCheck precision (papers)", labelpad=2)
    nums = {"per_score": {}}
    for k in range(6):
        v = BY[k]
        if not v:
            continue
        over = swarm_column(ax, k, v, ax_w, ax_h, xlim, ylim, half=2.0, key=f"e1 {k}")
        med = float(np.median(v))
        ax.plot([k - 0.32, k + 0.32], [med, med], color=BLACK, lw=1.0, solid_capstyle="butt", zorder=4)
        nums["per_score"][k] = {"n": len(v), "median": r(med), "dots_overlapping": over, "values": v}
    # the two header texts: S473 put "rho = ..." at C_TOP - 6.2 and "n = ... answers, draw 1" at C_TOP - 2.4, both at
    # E_X; the only change is that they now start at the letter's column so neither runs past the page
    cv.text(ax_x - 7.0, ax_y - 6.2, f"rho = {rho_all:.2f}")
    cv.text(ax_x - 7.0, ax_y - 2.4, f"n = {len(P)} answers, draw 1")
    cv.letter(0.0, ax_y - 6.2)
    nums.update(rho_all=r(rho_all), n_answers=len(P), n_questions=NQ)
    cv.finish("e1_current", "Figure 5e option 1")
    write_numbers("e1_current", "S473 panel e redrawn on today's data; header texts moved left to fit the page", nums)


# =====================================================================================================================
# e2: box per score over its dots, n per score, both rho with intervals
# =====================================================================================================================
def e2():
    X0 = 140.0
    W, H = 183.0 - X0, 74.0
    cv = Canvas(W, H, "e2")
    ax_x, ax_y, ax_w, ax_h = 10.0, 14.0, 31.0, 46.0
    ax = cv.axes(ax_x, ax_y, ax_w, ax_h)
    xlim, ylim = (-0.6, 5.6), (-0.04, 1.04)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xticks(range(6)); ax.set_xticklabels([str(k) for k in range(6)])
    ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(["0", "0.5", "1"])
    clean(ax)
    ax.set_ylabel("MiniCheck precision (papers)", labelpad=2)
    mm_x = ax_w / (xlim[1] - xlim[0])
    nums = {"per_score": {}}
    hb = 1.6 / mm_x
    for k in range(6):
        v = BY[k]
        if not v:
            continue
        over = swarm_column(ax, k, v, ax_w, ax_h, xlim, ylim, half=2.0, key=f"e2 {k}")
        q = quart(v)
        ax.add_patch(Rectangle((k - hb, q["q25"]), 2 * hb, q["q75"] - q["q25"], fill=False, ec=BLACK, lw=0.5,
                               joinstyle="miter", zorder=5))
        ax.plot([k - hb, k + hb], [q["median"]] * 2, color=BLACK, lw=1.0, solid_capstyle="butt", zorder=6)
        nums["per_score"][k] = dict(q, dots_overlapping=over, values=v)
    # n per score, one line under the tick labels, and the axis title under that
    yn = ax_y + ax_h + 7.0
    cv.text(ax_x - 7.0, yn, "n")
    for k in range(6):
        xk = ax_x + (k - xlim[0]) * mm_x
        cv.text(xk, yn, str(len(BY[k])), ha="center")
    cv.text(ax_x + ax_w / 2, yn + 4.4, "Faithfulness score", ha="center")
    ra, rb = D["rho_all"], D["rho_3to5"]
    cv.text(ax_x - 7.0, ax_y - 6.6, f"rho {ra['rho']:.2f} ({ra['lo']:.2f} to {ra['hi']:.2f}), all")
    cv.text(ax_x - 7.0, ax_y - 2.8, f"rho {rb['rho']:.2f} ({rb['lo']:.2f} to {rb['hi']:.2f}), 3 to 5")
    cv.letter(0.0, ax_y - 6.6)
    nums.update(rho_all={k: r(ra[k]) for k in ("rho", "lo", "hi")}, rho_3to5={k: r(rb[k]) for k in ("rho", "lo", "hi")},
                n_answers=len(P), n_answers_3to5=rb["answers"], n_questions=NQ,
                interval="S473 answer_rho: 95% percentile interval over 10,000 question resamples (S463 seed), every "
                         "answer of a question drawn together")
    cv.finish("e2_box_rho", "Figure 5e option 2")
    write_numbers("e2_box_rho", "box per faithfulness score over its answers' dots; n per score; both rho with "
                  "their intervals", nums)


# =====================================================================================================================
# e3: answers by MiniCheck precision, stacked by faithfulness score (panel d's colours)
# =====================================================================================================================
def e3():
    X0 = 140.0
    W, H = 183.0 - X0, 74.0
    cv = Canvas(W, H, "e3")
    # critic 28 Oct: 2 mm further right for the 3-digit top tick "100" (the y label then stays on the page), 4 mm
    # narrower so the centred x label keeps its place
    ax_x, ax_y, ax_w, ax_h = 11.0, 16.0, 27.0, 44.0
    ax = cv.axes(ax_x, ax_y, ax_w, ax_h)
    edges = [i / 10 for i in range(11)]
    # bin i holds edges[i] <= v < edges[i+1]; the last bin also holds v = 1
    def bin_of(v):
        return min(int(np.floor(v * 10 + 1e-9)), 9)
    counts = [[0] * 6 for _ in range(10)]
    for p in P:
        counts[bin_of(p["papers_precision"])][p["faithfulness"]] += 1
    assert sum(map(sum, counts)) == len(P)
    for i in range(10):
        base = 0
        for k in range(6):
            n = counts[i][k]
            if n:
                ax.add_patch(Rectangle((edges[i] + 0.004, base), 0.092, n, fc=CIV6[k], ec="none", lw=0, zorder=3))
            base += n
    top = max(sum(c) for c in counts)
    ymax = int(np.ceil(top / 20.0) * 20)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(0, ymax)
    ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["0", "0.5", "1"])
    # critic 28 Oct: the axis ran to 100 with its last tick at 80, so its top was unlabelled; tick the top too
    yt = [0, ymax // 2, ymax] if ymax % 2 == 0 else list(range(0, ymax + 1, 20))
    ax.set_yticks(yt); ax.set_yticklabels([str(t) for t in yt])
    clean(ax)
    ax.set_xlabel("MiniCheck precision (papers)", labelpad=2)
    ax.set_ylabel("Answers (n)", labelpad=2)
    # key on top, as panel d's
    cv.text(ax_x - 5.0, ax_y - 10.6, "Faithfulness score")
    kx = ax_x - 5.0
    for k in range(6):
        kk = cv.axes(kx, ax_y - 8.8, 2.6, 2.4)
        kk.add_patch(Rectangle((0, 0), 1, 1, fc=CIV6[k], ec="none"))
        kk.set_axis_off(); kk.set_xlim(0, 1); kk.set_ylim(0, 1)
        cv.text(kx + 3.0, ax_y - 6.8, str(k))
        kx += 6.0
    cv.text(ax_x - 5.0, ax_y - 2.4, f"n = {len(P)} answers, draw 1")
    cv.letter(0.0, ax_y - 10.6)
    nums = {"bins": [{"from": edges[i], "to": edges[i + 1], "closed_right": i == 9,
                      "by_faithfulness": {k: counts[i][k] for k in range(6)}, "total": sum(counts[i])}
                     for i in range(10)],
            "n_answers": len(P), "n_questions": NQ, "y_max": ymax}
    cv.finish("e3_stacked", "Figure 5e option 3")
    write_numbers("e3_stacked", "answers by MiniCheck precision in bins of 0.1, each bar split by faithfulness score",
                  nums)


# =====================================================================================================================
# e4: per strategy, answers rated 5 against answers rated 0 to 4
# =====================================================================================================================
def e4():
    W, H = 72.0, 74.0
    cv = Canvas(W, H, "e4")
    ax_x, ax_y, ax_w, ax_h = 31.0, 12.0, 34.0, 50.0
    ax = cv.axes(ax_x, ax_y, ax_w, ax_h)
    rows = []
    for c in CONFIGS:
        for grp in (5, "0 to 4"):
            v = sorted(p["papers_precision"] for p in P if p["strategy"] == c
                       and ((p["faithfulness"] == 5) if grp == 5 else (p["faithfulness"] < 5)))
            rows.append((c, grp, v))
    nrow = len(rows)
    # rows: two per strategy, a gap between strategies
    ys, y = [], 0.0
    for i in range(nrow):
        ys.append(y)
        y += 1.0 if i % 2 == 0 else 1.6
    ax.set_ylim(ys[-1] + 0.8, -0.8)
    ax.set_xlim(-0.04, 1.04)
    ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["0", "0.5", "1"])
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    clean(ax)
    ax.set_xlabel("MiniCheck precision (papers)", labelpad=2)
    span = ys[-1] + 1.6
    mm_y = ax_h / span
    mm_x = ax_w / 1.08
    nums = {"rows": []}
    hb = 0.9 / mm_y
    for (c, grp, v), yy in zip(rows, ys):
        if v:
            off, over = S457.swarm([x * mm_x for x in v], half=1.1, pitch=0.5, dot=S457.DOT_MM)
            OVERLAPS[f"e4 {c} {grp}"] = over
            ax.plot(v, [yy + o / mm_y for o in off], ls="none", marker="o", ms=DOT, mfc=GREY, mew=0, zorder=7)
            q = quart(v)
            ax.add_patch(Rectangle((q["q25"], yy - hb), q["q75"] - q["q25"], 2 * hb, fill=False, ec=BLACK, lw=0.5,
                                   joinstyle="miter", zorder=5))
            ax.plot([q["median"]] * 2, [yy - hb, yy + hb], color=BLACK, lw=1.0, solid_capstyle="butt", zorder=6)
        else:
            q, over = {"n": 0}, 0
        nums["rows"].append({"strategy": LABEL[c], "faithfulness": "5" if grp == 5 else "0 to 4", **q,
                             "dots_overlapping": over, "values": v})
        ymm = ax_y + (yy + 0.8) * (ax_h / (ys[-1] + 1.6)) + 1.1
        cv.text(ax_x - 1.5, ymm, "5" if grp == 5 else "0 to 4", ha="right")
        cv.text(ax_x + ax_w + 1.0, ymm, f"{len(v)}", ha="left")
        if grp == 5:
            cv.text(0.0 + 5.0, ymm + (1.3 * ax_h / (ys[-1] + 1.6)) / 2, LABEL[c], ha="left")
    cv.text(ax_x - 1.5, ax_y - 2.4, "Faithfulness", ha="right")
    cv.text(ax_x + ax_w + 1.0, ax_y - 2.4, "n", ha="left")
    cv.letter(0.0, ax_y - 6.2)
    cv.text(5.0, ax_y - 6.2, f"n = {len(P)} answers, draw 1")
    nums.update(n_answers=len(P), n_questions=NQ)
    cv.finish("e4_by_strategy", "Figure 5e option 4")
    write_numbers("e4_by_strategy", "per strategy, MiniCheck precision of the answers rated 5 and of those rated 0 "
                  "to 4: dots, quartile box, median", nums)


if __name__ == "__main__":
    e1(); e2(); e3(); e4()
    (HERE / "overlaps.json").write_text(json.dumps(OVERLAPS, indent=1) + "\n")
    print("rho_all", rho_all, "rho_3to5", rho_35, "n", len(P), "q", NQ)
    print("dots overlapping:", OVERLAPS)
