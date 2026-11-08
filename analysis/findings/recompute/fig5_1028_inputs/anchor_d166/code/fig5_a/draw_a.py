"""Figure 5 panel a options (scratch, not a plate), drawn from a_data.json (prep.py, S473's own functions on the
28 October pull). Each option is one PNG and PDF at the size it would have on the plate (left half of 183 mm), and
one numbers JSON with every drawn number and the input files' sha256. Style: S457.plate_rc (FIGURE_LOCK [type],
[lines]); S473's strategy colours (Okabe-Ito) and markers; S457's dot rows (grey question dots, quartile box, median,
blue mean with Rule 2's 95% percentile interval over 10,000 question resamples). Score 4 only (D160 (8))."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S457", ROOT / "scripts/S457_fig2_panels.py")
S457 = importlib.util.module_from_spec(spec); sys.modules["S457"] = S457; spec.loader.exec_module(S457)
plt.rcParams.update(S457.plate_rc("fig5alt_a"))
MM_PT = S457.MM_PT
DATA_P = HERE / "a_data.json"
D = json.loads(DATA_P.read_text())
C = D["configs"]
LAB = D["labels"]
QA = D["questions"]
QW = D["W_questions"]
OK = S457.OKABE
COL = {"single_pass": OK["black"], "multi_hop": OK["orange"], "verified_pass": OK["vermillion"],
       "rlm_5": OK["sky blue"], "rlm_10": OK["blue"], "rlm_20": OK["bluish green"]}      # S473 LINE_COL
MARK = {"single_pass": "o", "multi_hop": "s", "verified_pass": "D", "rlm_5": "^", "rlm_10": "v", "rlm_20": "P"}
GREY, BLUE = S457.DOT_GREY, OK["blue"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SOURCES = {"a_data.json (prep.py output)": {"path": str(DATA_P), "sha256": sha(DATA_P)},
           "inputs of a_data.json (pull and repository files, as recorded by S473.pull_sources)": D["inputs_sha256"],
           "prep.py": {"path": str(HERE / "prep.py"), "sha256": sha(HERE / "prep.py")},
           "draw_a.py": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())}}


def per_q(c, sig, qs):
    return [(q, D["per_q"][c][q][sig]) for q in qs if D["per_q"][c][q][sig] is not None]


def check_text(fig, W, H, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    boxes = []
    for t_ in fig.findobj(Text):
        if t_.get_visible() and t_.get_text().strip():
            b = t_.get_window_extent(r)
            x0, x1 = b.x0 / fig.dpi * 25.4, b.x1 / fig.dpi * 25.4
            y0, y1 = H - b.y1 / fig.dpi * 25.4, H - b.y0 / fig.dpi * 25.4
            if x0 < -0.01 or y0 < -0.01 or x1 > W + 0.01 or y1 > H + 0.01:
                raise SystemExit(f"{name}: {t_.get_text()!r} off the page")
            boxes.append((t_.get_text(), x0, y0, x1, y1))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05 and a[2] < b[4] - 0.05 and b[2] < a[4] - 0.05:
                raise SystemExit(f"{name}: {a[0]!r} on {b[0]!r}")


def save(fig, W, H, name, numbers):
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    check_text(fig, W, H, name)
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=600, metadata={"CreationDate": None} if ext == "pdf" else None)
    plt.close(fig)
    numbers["sources"] = SOURCES
    numbers["size_mm"] = [W, H]
    (HERE / f"{name}.numbers.json").write_text(json.dumps(numbers, indent=1) + "\n")


def axes_mm(fig, W, H, x, y, w, h):
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def text_mm(fig, W, H, x, y, s, **kw):
    return fig.text(x / W, 1 - y / H, s, **kw)


def letter(fig, W, H, x=0.5, y=6.8):
    text_mm(fig, W, H, x, y, "a", fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT, va="baseline", ha="left")


def dot_row_capped(ax, vals_mm, vals, s, y, pitch, overlaps, key, mean_mm, cap_mm):
    """S457.dot_row's marks with a smaller mean marker and end caps on its interval (critic: in a3 the 1.5 mm mean dot
    was wider than every concept and papers interval, about 0.6 to 1.1 mm, so no interval could be seen)."""
    off, over = S457.swarm(vals_mm)
    overlaps[key] = over
    ax.plot(vals, [y - o / pitch for o in off], ls="none", marker="o", ms=S457.DOT_MM / MM_PT, mfc=GREY, mew=0,
            zorder=2)
    hb = S457.BOX_HALF_MM / pitch
    ax.plot([s["quartile_25"], s["quartile_75"], s["quartile_75"], s["quartile_25"], s["quartile_25"]],
            [y - hb, y - hb, y + hb, y + hb, y - hb], color="#000000", lw=0.5, solid_joinstyle="miter", zorder=5)
    ax.plot([s["median"], s["median"]], [y - hb, y + hb], color="#000000", lw=1.0, solid_capstyle="butt", zorder=5)
    yb = y + S457.MEAN_OFF_MM / pitch
    hc = cap_mm / 2 / pitch
    ax.plot([s["mean_lo"], s["mean_hi"]], [yb, yb], color=BLUE, lw=0.9, solid_capstyle="butt", zorder=3)
    for xv in (s["mean_lo"], s["mean_hi"]):
        ax.plot([xv, xv], [yb - hc, yb + hc], color=BLUE, lw=0.6, solid_capstyle="butt", zorder=3)
    ax.plot([s["mean"]], [yb], ls="none", marker="o", ms=mean_mm / MM_PT, mfc=BLUE, mew=0, zorder=4)


def forest(fig, W, H, x0, top, w, h, rows, column, lim, ticks, xlabel, ylabels, zero=False, tick_fmt=None,
           mean_mm=None, cap_mm=1.4):
    """One forest column: per row its per-question values as grey dots, quartile box, median, blue mean with its
    interval (S457.dot_row). rows: [(row key, [(q, v)])]. Returns the summaries."""
    ax = axes_mm(fig, W, H, x0, top, w, h)
    span = lim[1] - lim[0]
    ax.set_xlim(lim[0] - 0.04 * span, lim[1] + 0.04 * span)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xticks(ticks)
    ax.set_xticklabels([tick_fmt(v) if tick_fmt else f"{v:g}" for v in ticks])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(ylabels if ylabels else [])
    ax.tick_params(axis="y", length=0, pad=2)
    clean(ax)
    ax.set_xlabel(xlabel, labelpad=2)
    if zero:
        ax.axvline(0, color="#000000", lw=0.5, ls=(0, (2, 1.5)), zorder=1)
    pitch = h / len(rows)
    mm_per = w / (span * 1.08)
    out, overlaps = {}, {}
    for i, (key, pq) in enumerate(rows):
        vals = [v for _, v in pq]
        s = S457.summary(vals)
        if mean_mm is None:
            S457.dot_row(ax, [(v - lim[0]) * mm_per for v in vals], vals, s, i - 0.12, pitch, overlaps,
                         f"{column} {key}")
        else:
            dot_row_capped(ax, [(v - lim[0]) * mm_per for v in vals], vals, s, i - 0.12, pitch, overlaps,
                           f"{column} {key}", mean_mm, cap_mm)
        out[key] = {"summary": s, "per_question": [[q, v] for q, v in pq]}
    return ax, out, overlaps


W_PANEL = 100.0


# ------------------------------------------------------------------ a0: the current panel, today's data
def a0():
    W, H = W_PANEL, 70.0
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    LABX, TOP, AW, AH, GAP = 20.0, 13.0, 34.0, 47.0, 5.0      # critic: S473 draw()'s panel a (LAB, A_TOP, A_W, A_H, A_GAP)
    nums = {"option": "a0_current", "threshold": "judge correctness score 4 or more (D154, D160 (8))", "columns": {}}
    specs = [("pass", "pass4", QA, (0, 100), [0, 25, 50, 75, 100], "Pass rate 4+ (%)", "Against the answer key",
              "n = {n} questions, three draws"),
             ("papers", "papers", QW, (0, 1), [0, 0.25, 0.5, 0.75, 1], "MiniCheck precision",
              "Against the papers", "n = {n} questions, draw 1")]
    for j, (col, sig, qs, lim, ticks, xl, ref, nfmt) in enumerate(specs):
        x0 = LABX + j * (AW + GAP)
        rows = [(c, per_q(c, sig, qs)) for c in C]
        _, out, ov = forest(fig, W, H, x0, TOP, AW, AH, rows, col, lim, ticks, xl,
                            [LAB[c] for c in C] if j == 0 else None)
        n = len({q for _, pq in rows for q, _ in pq})
        text_mm(fig, W, H, x0, TOP - 6.2, ref, ha="left", va="baseline")
        text_mm(fig, W, H, x0, TOP - 2.4, nfmt.format(n=n), ha="left", va="baseline")
        nums["columns"][col] = {"n_questions": n, "per_strategy": out, "dot_overlaps": ov,
                                "n_per_strategy": {c: len(out[c]["per_question"]) for c in C}}
    letter(fig, W, H, y=TOP - 6.2)
    save(fig, W, H, "a0_current", nums)


# ------------------------------------------------------------------ a1: three signals, one forest each
def a1():
    W, H = W_PANEL, 68.0
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    LABX, TOP, AW, AH, GAP = 20.0, 11.0, 23.4, 45.0, 4.0      # critic: AW 24 put the "1" at 99.9 of 100 mm
    nums = {"option": "a1_three_signals", "threshold": "judge correctness score 4 or more (D154, D160 (8))",
            "concept_recall": "L3 loose matcher (D12), provisional until P2's hand labels; per question the mean of "
                              "its three draws (Rule 7), an empty answer 0 (Rule 10)", "columns": {}}
    specs = [("pass", "pass4", QA, (0, 100), [0, 50, 100], "Pass rate\n4+ (%)", "Judge (key)",
              "n = {n}, 3 draws"),
             ("concept", "concept", QA, (0, 1), [0, 0.5, 1], "Concept\nrecall", "Concepts (key)", "n = {n}, 3 draws"),
             ("papers", "papers", QW, (0, 1), [0, 0.5, 1], "MiniCheck\nprecision", "Papers", "n = {n}, draw 1")]
    for j, (col, sig, qs, lim, ticks, xl, ref, nfmt) in enumerate(specs):
        x0 = LABX + j * (AW + GAP)
        rows = [(c, per_q(c, sig, qs)) for c in C]
        _, out, ov = forest(fig, W, H, x0, TOP, AW, AH, rows, col, lim, ticks, xl,
                            [LAB[c] for c in C] if j == 0 else None)
        n = len({q for _, pq in rows for q, _ in pq})
        text_mm(fig, W, H, x0, TOP - 6.2, ref, ha="left", va="baseline")
        text_mm(fig, W, H, x0, TOP - 2.4, nfmt.format(n=n), ha="left", va="baseline")
        nums["columns"][col] = {"n_questions": n, "per_strategy": out, "dot_overlaps": ov}
    letter(fig, W, H, y=TOP - 6.2)
    save(fig, W, H, "a1_three_signals", nums)


# ------------------------------------------------------------------ a2: trade-off map (brief O2) with a pass strip
def a2():
    W, H = W_PANEL, 68.0
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    LABX, TOP, SW, SH = 22.0, 11.0, 24.0, 45.0
    nums = {"option": "a2_tradeoff_map", "threshold": "judge correctness score 4 or more (D154, D160 (8))",
            "concept_recall": "L3 loose matcher (D12), provisional; per question the mean of its three draws",
            "map_questions": "the W questions (each strategy's draw-1 answer has a MiniCheck papers row)",
            "strip": {}, "map": {}}
    # strip: pass rate at 4, the 86 questions; row labels carry the strategy's marker in its colour
    rows = [(c, per_q(c, "pass4", QA)) for c in C]
    ax, out, ov = forest(fig, W, H, LABX, TOP, SW, SH, rows, "pass", (0, 100), [0, 50, 100], "Pass rate 4+ (%)",
                         [LAB[c] for c in C])
    nums["strip"] = {"n_questions": len(QA), "per_strategy": out, "dot_overlaps": ov}
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    by_text = {lab.get_text(): lab for lab in ax.get_yticklabels()}
    pitch = SH / len(C)
    for i, c in enumerate(C):
        bb = by_text[LAB[c]].get_window_extent(rend)
        x_mm = bb.x0 / fig.dpi * 25.4 - 1.8
        y_mm = TOP + (i + 0.5) * pitch
        fig.add_artist(matplotlib.lines.Line2D([x_mm / W], [1 - y_mm / H], ls="none", marker=MARK[c],
                                               ms=1.9 / MM_PT, mfc=COL[c], mec=COL[c], mew=0.5))
    text_mm(fig, W, H, LABX, TOP - 6.2, "Judge (key)", ha="left", va="baseline")
    text_mm(fig, W, H, LABX, TOP - 2.4, f"n = {len(QA)}, 3 draws", ha="left", va="baseline")
    # map: x concept recall, y MiniCheck precision; grey dots, one per strategy and question (all six pooled);
    # each strategy's mean in its colour and marker with its two 95% intervals (question resamples)
    MX, MW, MH = 58.0, 40.0, 45.0
    axm = axes_mm(fig, W, H, MX, TOP, MW, MH)
    clean(axm)
    axm.set_xlim(-0.04, 1.04); axm.set_ylim(-0.04, 1.04)
    axm.set_xticks([0, 0.5, 1]); axm.set_xticklabels(["0", "0.5", "1"])
    axm.set_yticks([0, 0.5, 1]); axm.set_yticklabels(["0", "0.5", "1"])
    axm.set_xlabel("Concept recall (key)", labelpad=2)
    axm.set_ylabel("MiniCheck precision (papers)", labelpad=1)
    text_mm(fig, W, H, MX, TOP - 6.2, "Key against papers", ha="left", va="baseline")
    text_mm(fig, W, H, MX, TOP - 2.4, f"n = {len(QW)} questions", ha="left", va="baseline")
    for c in C:
        pts = [(q, D["per_q"][c][q]["concept"], D["per_q"][c][q]["papers"]) for q in QW
               if D["per_q"][c][q]["concept"] is not None and D["per_q"][c][q]["papers"] is not None]
        axm.plot([x for _, x, _ in pts], [y for _, _, y in pts], ls="none", marker="o", ms=S457.DOT_MM / MM_PT,
                 mfc=GREY, mew=0, zorder=2)
        sx = S457.summary([x for _, x, _ in pts]); sy = S457.summary([y for _, _, y in pts])
        axm.plot([sx["mean_lo"], sx["mean_hi"]], [sy["mean"]] * 2, color=COL[c], lw=0.9, solid_capstyle="butt", zorder=4)
        axm.plot([sx["mean"]] * 2, [sy["mean_lo"], sy["mean_hi"]], color=COL[c], lw=0.9, solid_capstyle="butt", zorder=4)
        axm.plot([sx["mean"]], [sy["mean"]], ls="none", marker=MARK[c], ms=1.9 / MM_PT, mfc=COL[c],
                 mec="#FFFFFF", mew=0.3, zorder=5)
        nums["map"][c] = {"n_questions": len(pts), "concept_recall": sx, "papers_precision": sy,
                          "per_question": [[q, x, y] for q, x, y in pts]}
    letter(fig, W, H, y=TOP - 6.2)
    save(fig, W, H, "a2_tradeoff_map", nums)


# ------------------------------------------------------------------ a3: paired differences from single pass
def a3():
    W, H = W_PANEL, 68.0
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    LABX, TOP, AW, AH, GAP = 20.0, 11.0, 22.5, 39.0, 5.0
    others = [c for c in C if c != "single_pass"]
    nums = {"option": "a3_paired_vs_single_pass",
            "what": "per question, strategy minus single pass on the same question, in percentage points (pass "
                    "share x 100, concept recall x 100, MiniCheck precision x 100); a question enters a column only "
                    "when both strategies have a value there",
            "threshold": "judge correctness score 4 or more (D154, D160 (8))",
            "concept_recall": "L3 loose matcher (D12), provisional", "columns": {}}
    scale = {"pass4": 1.0, "concept": 100.0, "papers": 100.0}
    specs = [("pass", "pass4", QA, "Judge (key)", "pass rate 4+", "3 draws", "Pass rate\n4+"),
             ("concept", "concept", QA, "Concepts (key)", "concept recall", "3 draws", "Concept\nrecall"),
             ("papers", "papers", QW, "Papers", "MiniCheck precision", "draw 1", "MiniCheck\nprecision")]
    for j, (col, sig, qs, ref, what, dr, xl) in enumerate(specs):
        x0 = LABX + j * (AW + GAP)
        rows = []
        for c in others:
            pq = []
            for q in qs:
                a, b = D["per_q"][c][q][sig], D["per_q"]["single_pass"][q][sig]
                if a is not None and b is not None:
                    pq.append((q, scale[sig] * (a - b)))
            rows.append((c, pq))
        _, out, ov = forest(fig, W, H, x0, TOP, AW, AH, rows, col, (-100, 100), [-50, 0, 50],
                            xl, [LAB[c] for c in others] if j == 0 else None, zero=True,
                            tick_fmt=lambda v: ("\u2212" if v < 0 else "+" if v > 0 else "") + f"{abs(v):g}",
                            mean_mm=0.8, cap_mm=1.4)
        n = len({q for _, pq in rows for q, _ in pq})
        text_mm(fig, W, H, x0, TOP - 6.2, ref, ha="left", va="baseline")
        text_mm(fig, W, H, x0, TOP - 2.4, f"n = {n}, {dr}", ha="left", va="baseline")
        nums["columns"][col] = {"signal": what, "n_questions": n, "per_strategy": out, "dot_overlaps": ov}
    text_mm(fig, W, H, LABX + (3 * AW + 2 * GAP) / 2, TOP + AH + 15.5,
            "Difference from single pass (percentage points)", ha="center", va="baseline")
    letter(fig, W, H, y=TOP - 6.2)
    save(fig, W, H, "a3_paired_vs_single_pass", nums)


if __name__ == "__main__":
    for f in (a0, a1, a2, a3):
        f()
        print("drew", f.__name__)
