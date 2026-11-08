"""Figure 5 panel d: the current panel and three alternatives, each its own PDF, SVG and PNG at plate size (scratch,
not a plate). Reads d_data.json and d_inputs.json (d_data.py, S473's functions on the 28 October pull). Every option
writes a numbers file with every number it draws and the files (path, sha256) they come from.

  d0_current      the plate's panel d as S473 draws it (share of answers at each faithfulness score, per strategy)
  d1_question_grid  Figure 2a's form (D127): per strategy and question, draws rated 5 of 3; margin, share rated 5
                  (mean over questions with Rule 2's 95% percentile interval, 10,000 question resamples)
  d2_by_correctness  the faithfulness distribution at each judge correctness score (plain call), six strategies pooled
  d3_pass_fail    the current panel split by the judge's correctness verdict (pass = score 4 or more, Rule 5)

  uv run --frozen python <this folder>/d_draw.py      (from the repository root)
"""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S457 = mod("S457", ROOT / "scripts/S457_fig2_panels.py")
S463 = mod("S463", ROOT / "scripts/S463_fig2_ranking.py")

import logging
logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextToPath

S457.figure_lock_agreed()
plt.rcParams.update(S457.plate_rc("fig5d_opts"))
PT = S457.PT
MM = 25.4 / 72                      # mm per point
BLACK = "#000000"
t2p, fp = TextToPath(), FontProperties(family=S457.FONT, size=PT)


def width(s):
    return t2p.get_text_width_height_descent(s, fp, ismath=False)[0] * MM


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


D = json.loads((HERE / "d_data.json").read_text())
INPUTS = json.loads((HERE / "d_inputs.json").read_text())
INPUTS[str(HERE / "d_data.json")] = sha(HERE / "d_data.json")
CONFIGS, LABEL, QA = D["configs"], D["labels"], D["questions"]
ROWS = D["rows"]
OK = [r for r in ROWS if r["faith_status"] == "ok"]


def cividis6():                      # S473.cividis6, the plate's six score colours
    cm = matplotlib.colormaps[S457.FLOCK["colour"]["continuous"]]
    return ["#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(round(255 * i / 5)))[:3]) for i in range(6)]


COLS6 = cividis6()


class Page:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
        self.page = self.fig.add_axes([0, 0, 1, 1])
        self.page.set_axis_off()
        self.page.set_xlim(0, W)
        self.page.set_ylim(H, 0)

    def axes(self, x, y, w, h):
        return self.fig.add_axes([x / self.W, 1 - (y + h) / self.H, w / self.W, h / self.H])

    def text(self, x, y, s, **kw):
        return self.page.text(x, y, s, **kw)

    def letter(self, x, y):
        self.text(x, y, S457.LETTER_CASE("d"), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT,
                  va="baseline", ha="left")

    def score_key(self, x, y, title="Faithfulness score"):
        """S473's key: the title, then a swatch and the score for 0 to 5 on the line below."""
        self.text(x, y, title, ha="left", va="baseline")
        kx = x
        for k in range(6):
            self.page.add_patch(Rectangle((kx, y + 1.6), 2.6, 2.4, fc=COLS6[k], ec="none", lw=0))
            self.text(kx + 3.0, y + 3.6, str(k), ha="left", va="baseline")
            kx += 3.0 + width(str(k)) + 2.2

    def hidden_check(self, stem):
        """Critic, 28 Oct: finish_plate tests text against the page and against other text, not against an axes drawn
        after it. Every text and patch on the page layer must lie clear of each later axes' background."""
        from matplotlib.text import Text
        self.fig.canvas.draw()
        rend = self.fig.canvas.get_renderer()
        later = [a.patch.get_window_extent(rend) for a in self.fig.axes if a is not self.page and a.patch.get_visible()
                 and a.patch.get_facecolor()[3] > 0]
        marks = [(t.get_text(), t.get_window_extent(rend)) for t in self.page.texts if t.get_text().strip()]
        marks += [("patch", p.get_window_extent(rend)) for p in self.page.patches]
        marks += [("line", ln.get_window_extent(rend)) for ln in self.page.lines]
        hid = [s for s, bb in marks for ab in later
               if bb.x0 < ab.x1 - 0.5 and ab.x0 < bb.x1 - 0.5 and bb.y0 < ab.y1 - 0.5 and ab.y0 < bb.y1 - 0.5]
        if hid:
            raise SystemExit(f"{stem}: page marks under a later axes {hid[:3]}")

    def save(self, stem):
        paths = {k: HERE / f"{stem}.{k}" for k in ("pdf", "svg", "png")}
        self.hidden_check(stem)
        S457.finish_plate(self.fig, self.W, self.H, paths, title=f"Figure 5d option {stem}")
        return paths


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def stacked(ax, i, counts, n, h=0.62):
    left = 0.0
    for k in range(6):
        w_ = 100 * counts[k] / n if n else 0
        if w_ > 0:
            ax.barh([i], [w_], left=[left], height=h, color=COLS6[k], lw=0)
        left += w_


def write_numbers(stem, what, numbers):
    (HERE / f"{stem}_numbers.json").write_text(json.dumps({
        "option": stem, "what": what,
        "data": "28 October pull (fig5_pull_1028), S3 G1 collect run_sha256 " + D["collect_run_sha256"][:12]
                + "; faithfulness = the judge's call with passages (S3 'b'), correctness = its plain call (S3 'a')",
        "provisional": "the S3 judge rows for G1 are complete (1,539 scored faithfulness calls, 6 unscored, 3 no "
                       "text, the same as the 23 October plate); nothing in this panel is provisional",
        "numbers": numbers, "inputs_sha256": INPUTS,
        "script": {str(HERE / "d_draw.py"): sha(HERE / "d_draw.py"), str(HERE / "d_data.py"): sha(HERE / "d_data.py")},
    }, indent=1) + "\n")


def counts_of(rows):
    c = Counter(r["faithfulness"] for r in rows)
    return [c.get(k, 0) for k in range(6)]


W, H = 66.0, 68.0
TOP, AX_H = 9.5, 50.0                # the plate's C_TOP - 9.5 is this page's 0

# ------------------------------------------------------------------ d0: the current panel
pg = Page(W, H)
X0, AW = 18.5, 34.0
ax = pg.axes(X0, TOP, AW, AX_H)
ax.set_xlim(0, 100); ax.set_ylim(len(CONFIGS) - 0.5, -0.5)
ax.set_xticks([0, 50, 100]); ax.set_xticklabels(["0", "50", "100"])
ax.set_yticks(range(len(CONFIGS))); ax.set_yticklabels([LABEL[c] for c in CONFIGS])
ax.tick_params(axis="y", length=0, pad=2); clean(ax)
ax.set_xlabel("Answers (%)", labelpad=2)
num0 = {}
for i, c in enumerate(CONFIGS):
    cnt = [D["d"][c]["counts"][str(k)] for k in range(6)]
    n = D["d"][c]["n"]
    if cnt != counts_of([r for r in OK if r["strategy"] == c]):
        raise SystemExit(f"d0 {c}: counts differ from the per-answer rows")
    stacked(ax, i, cnt, n)
    pg.text(X0 + AW + 1.0, TOP + AX_H * (i + 0.5) / len(CONFIGS) + 1.0, f"n = {n}", ha="left", va="baseline")
    num0[LABEL[c]] = {"n": n, "counts_0_to_5": cnt, "share_pct_0_to_5": [round(100 * x / n, 4) for x in cnt],
                      "faith_status_counts": D["d"][c]["status"],
                      "left_out": {k: v for k, v in D["d"][c]["status"].items() if k != "ok"}}
pg.score_key(X0, TOP - 6.2)
pg.letter(0.0, TOP - 6.2)
pg.save("d0_current")
write_numbers("d0_current", "the plate's panel d on today's data: per strategy the share of its scored answers at "
              "each faithfulness score (judge with passages, three draws); n at right", {
                  "per_strategy": num0, "all": D["d_all"]})

# ------------------------------------------------------------------ d1: question grid with margin (Figure 2a's form)
LEV = S463.tile_colours(3)
NO3 = S463.NO_SCORE
per = {}
for c in CONFIGS:
    for q in QA:
        sc = [r["faithfulness"] for r in OK if r["strategy"] == c and r["question_id"] == q]
        per[(c, q)] = (sum(1 for v in sc if v == 5), len(sc))
order = sorted(QA, key=lambda q: (-sum(per[(c, q)][0] for c in CONFIGS), q))
marg = {}
for c in CONFIGS:
    sh = [per[(c, q)][0] / per[(c, q)][1] for q in QA if per[(c, q)][1] > 0]
    lo, hi = S463.interval(sh, [1] * len(sh))
    marg[c] = {"mean_pct": 100 * sum(sh) / len(sh), "lo_pct": 100 * lo, "hi_pct": 100 * hi, "questions": len(sh),
               "answers_at_5": sum(per[(c, q)][0] for q in QA), "answers": sum(per[(c, q)][1] for q in QA)}
    if marg[c]["answers_at_5"] != D["d"][c]["counts"]["5"] or marg[c]["answers"] != D["d"][c]["n"]:
        raise SystemExit(f"d1 {c}: answers at 5 differ from d0")
pg = Page(W, H)
LABW, HW, GAP, MW = 18.5, 25.5, 4.5, 15.5
pitch = 7.4
GT = 10.5
axh = pg.axes(LABW, GT, HW, 6 * pitch)
axh.set_xlim(0, len(order)); axh.set_ylim(6, 0)
for s_ in ("top", "right", "left"):
    axh.spines[s_].set_visible(False)
for i, c in enumerate(CONFIGS):
    for j, q in enumerate(order):
        k, n = per[(c, q)]
        col = LEV[k] if n == 3 else NO3
        axh.add_patch(Rectangle((j, i + 0.08), 1, 0.84, fc=col, ec=col, lw=0.35))
axh.set_yticks([i + 0.5 for i in range(6)]); axh.set_yticklabels([LABEL[c] for c in CONFIGS])
axh.tick_params(axis="y", length=0, pad=2)
axh.set_xticks([0.5, len(order) - 0.5]); axh.set_xticklabels(["1", str(len(order))])
axh.set_xlabel("Question", labelpad=1.5)
lo_ax, step, lim = S463.margin_axis([v for m in marg.values() for v in (m["mean_pct"], m["lo_pct"])])
am = pg.axes(LABW + HW + GAP, GT, MW, 6 * pitch)
am.set_xlim(*lim); am.set_ylim(6, 0)
for s_ in ("top", "right", "left"):
    am.spines[s_].set_visible(False)
am.set_yticks([])
am.set_xticks([lo_ax + step * k for k in range(int((100 - lo_ax) / step) + 1)])
am.set_xticklabels([f"{lo_ax + step * k:g}" for k in range(int((100 - lo_ax) / step) + 1)])
am.set_xlabel("Rated 5 (%)", labelpad=1.5)
for i, c in enumerate(CONFIGS):
    m = marg[c]
    am.plot([m["lo_pct"], m["hi_pct"]], [i + 0.5] * 2, color=BLACK, lw=0.9, solid_capstyle="butt")
    am.plot([m["mean_pct"]], [i + 0.5], ls="none", marker="o", ms=1.5 / MM, mfc=BLACK, mew=0, zorder=4)
# key: two lines, as Figure 2a
kx, ky = 4.0, 2.6
pg.text(kx, ky + 0.9, "Draws rated 5:", ha="left", va="baseline")
kx += width("Draws rated 5:") + 1.2
for k in (3, 2, 1, 0):
    pg.page.add_patch(Rectangle((kx, ky - 1.0), 2.0, 2.0, fc=LEV[k], ec="none", lw=0))
    s = f"{k}" + (" of 3" if k == 0 else "")
    pg.text(kx + 2.6, ky + 0.9, s, ha="left", va="baseline")
    kx += 2.6 + width(s) + 1.6
ky2 = ky + 3.9
kx = 4.0
pg.page.add_patch(Rectangle((kx, ky2 - 1.0), 2.0, 2.0, fc=NO3, ec="none", lw=0))
pg.text(kx + 2.6, ky2 + 0.9, "under 3 scored", ha="left", va="baseline")
kx += 2.6 + width("under 3 scored") + 2.4
pg.page.plot([kx, kx + 3.2], [ky2, ky2], color=BLACK, lw=0.9, solid_capstyle="butt")
pg.page.plot([kx + 1.6], [ky2], ls="none", marker="o", ms=1.5 / MM, mfc=BLACK, mew=0)
pg.text(kx + 3.8, ky2 + 0.9, "mean, 95% interval", ha="left", va="baseline")
pg.letter(0.0, ky + 0.9)
pg.save("d1_question_grid")
write_numbers("d1_question_grid", "per strategy and answerable question, the draws the judge with passages rated 5 "
              "(of its scored draws; a tile with fewer than 3 scored draws is drawn light grey); margin, the share "
              "rated 5 as the mean over questions of each question's share over its scored draws, with the 95% "
              "percentile interval of 10,000 question resamples (S463.interval, seed 20261013)", {
                  "question_order": order,
                  "order_key": "draws rated 5 summed over the six strategies, high to low, then question id",
                  "tiles": {LABEL[c]: {q: {"rated_5": per[(c, q)][0], "scored": per[(c, q)][1]} for q in order}
                            for c in CONFIGS},
                  "tiles_under_3_scored": [[LABEL[c], q, per[(c, q)][1]] for c in CONFIGS for q in order
                                           if per[(c, q)][1] < 3],
                  "margin": {LABEL[c]: marg[c] for c in CONFIGS},
                  "margin_axis": {"low": lo_ax, "step": step, "limits": lim}})

# ------------------------------------------------------------------ d2: faithfulness by judge correctness score
pg = Page(W, H)
X0, AW = 18.5, 34.0
ax = pg.axes(X0, TOP, AW, AX_H)
SC = [5, 4, 3, 2, 1, 0]
ax.set_xlim(0, 100); ax.set_ylim(len(SC) - 0.5, -0.5)
ax.set_xticks([0, 50, 100]); ax.set_xticklabels(["0", "50", "100"])
ax.set_yticks(range(len(SC))); ax.set_yticklabels([str(s) for s in SC])
ax.tick_params(axis="y", length=0, pad=2); clean(ax)
ax.set_xlabel("Answers (%)", labelpad=2)
ax.set_ylabel("Correctness score (judge)", labelpad=3)
num2 = {}
none_c = [r for r in OK if r["correctness"] is None]
if none_c:
    raise SystemExit(f"d2: {len(none_c)} scored faithfulness calls without a correctness score")
for i, s in enumerate(SC):
    rs = [r for r in OK if r["correctness"] == s]
    cnt = counts_of(rs)
    stacked(ax, i, cnt, len(rs))
    pg.text(X0 + AW + 1.0, TOP + AX_H * (i + 0.5) / len(SC) + 1.0, f"n = {len(rs):,}", ha="left", va="baseline")
    num2[str(s)] = {"n": len(rs), "counts_faith_0_to_5": cnt,
                    "share_pct_0_to_5": [round(100 * x / len(rs), 4) if rs else None for x in cnt],
                    "per_strategy_n": dict(Counter(LABEL[r["strategy"]] for r in rs))}
if sum(v["n"] for v in num2.values()) != D["d_all"]["n"]:
    raise SystemExit("d2: rows do not add up to panel d's answers")
pg.score_key(X0, TOP - 6.2)
pg.letter(0.0, TOP - 6.2)
pg.save("d2_by_correctness")
write_numbers("d2_by_correctness", "per judge correctness score of the plain call (0 to 5), the share of answers at "
              "each faithfulness score of the call with passages; six strategies and three draws pooled; n at right",
              {"per_correctness_score": num2, "all_n": D["d_all"]["n"]})

# ------------------------------------------------------------------ d3: the current panel split by the judge's verdict
pg = Page(W, H)
X0, AW = 26.0, 27.0
ax = pg.axes(X0, TOP, AW, AX_H)
NR = 2 * len(CONFIGS)
ax.set_xlim(0, 100); ax.set_ylim(NR - 0.5 + 0.6, -0.5)
ax.set_xticks([0, 50, 100]); ax.set_xticklabels(["0", "50", "100"])
ax.set_yticks([]); clean(ax); ax.spines["left"].set_visible(False)
ax.set_xlabel("Answers (%)", labelpad=2)
num3 = {}
ypos = []
for i, c in enumerate(CONFIGS):
    num3[LABEL[c]] = {}
    for j, (word, test) in enumerate((("pass", lambda v: v >= 4), ("fail", lambda v: v < 4))):
        y = 2 * i + j + 0.12 * i
        rs = [r for r in OK if r["strategy"] == c and test(r["correctness"])]
        cnt = counts_of(rs)
        stacked(ax, y, cnt, len(rs), h=0.78)
        ymm = TOP + AX_H * (y + 0.5) / (NR + 0.6)
        pg.text(X0 - 1.2, ymm + 1.0, word, ha="right", va="baseline")
        pg.text(X0 + AW + 1.0, ymm + 1.0, f"n = {len(rs)}", ha="left", va="baseline")
        num3[LABEL[c]][word] = {"n": len(rs), "counts_faith_0_to_5": cnt,
                                "share_pct_0_to_5": [round(100 * x / len(rs), 4) if rs else None for x in cnt]}
    ymid = TOP + AX_H * (2 * i + 0.12 * i + 1.0) / (NR + 0.6)
    pg.text(X0 - 1.2 - width("pass") - 1.6, ymid + 1.0, LABEL[c], ha="right", va="baseline")
    if num3[LABEL[c]]["pass"]["n"] + num3[LABEL[c]]["fail"]["n"] != D["d"][c]["n"]:
        raise SystemExit(f"d3 {c}: pass and fail do not add to panel d's n")
# critic, 28 Oct: the pass/fail rows name their variable (the plate's panel b says "judge passes", "judge fails");
# the key moves right to X0 so the heading sits clear of its swatches
pg.text(X0 - 1.2, TOP - 0.9, "Judge", ha="right", va="baseline")
pg.score_key(X0, TOP - 6.2)
pg.letter(0.0, TOP - 6.2)
pg.save("d3_pass_fail")
write_numbers("d3_pass_fail", "per strategy, the faithfulness distribution (judge with passages) of the answers the "
              "judge's plain call passes (correctness 4 or more, Rule 5) and of those it fails (below 4); n at right",
              {"per_strategy": num3})
print("written:", sorted(p.name for p in HERE.glob("d?_*.png")))
