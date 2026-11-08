"""Figure 5 panel b, design b6 (scratch, not a plate): per strategy, the answers where the judge and the papers point
opposite ways.

One stacked bar per strategy (draw 1, the 83 W questions; 82 where an answer has no papers score). Each answer is put in
one of four groups by two splits:
  judge   pass = correctness 4 or more (S473.PASS_T, field judge_pass of b_points.json)
  papers  high = MiniCheck precision at or above the median of all 495 answers (the data's own median, 0.6562; the
          answers exactly on it count as high); low = below it
Segments left to right: judge fails & papers high | both high | both low | judge passes & papers low.

Reads ../../fig5_b/b_points.json (prep.py: S473.compute() on fig5_pull_1028, panel b's rows). Before drawing, it
re-reads the judge score and the papers precision of each of the 495 answers from the raw pull (s3/g1_collect.jsonl,
l1/papers/*.jsonl) and requires them equal to b_points.json, and requires the counts to equal the ones checked on
28 October (the brief). Writes b6_bars.{pdf,svg,png} (S457.finish_plate) and b6_bars_numbers.json.
"""
import glob
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
FIGOPTS = HERE.parent.parent
PULL = FIGOPTS.parent / "fig5_pull_1028"
BPTS = FIGOPTS / "fig5_b" / "b_points.json"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
S473 = importlib.util.module_from_spec(spec); sys.modules["S473"] = S473; spec.loader.exec_module(S473)
S457 = S473.S457

import logging
logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties

S457.figure_lock_agreed()
plt.rcParams.update(S457.plate_rc("fig5alt_b6"))
plt.rcParams["axes.unicode_minus"] = False
PT, MM_PT = S457.PT, S457.MM_PT
LW = max(0.5, S457.LINE_MIN_PT)
C_FAIL_HIGH = S457.OKABE["sky blue"]      # #56B4E9
C_PASS_LOW = S457.OKABE["vermillion"]     # #D55E00
C_BOTH_HIGH, C_BOTH_LOW = "#BBBBBB", "#888888"
assert (C_FAIL_HIGH, C_PASS_LOW) == ("#56B4E9", "#D55E00")
SEG_COL = [C_FAIL_HIGH, C_BOTH_HIGH, C_BOTH_LOW, C_PASS_LOW]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


# ---------------------------------------------------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------------------------------------------------
D = json.loads(BPTS.read_text())
CONFIGS, LABEL, PTS = D["configs"], D["labels"], D["b"]
assert CONFIGS == ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"], CONFIGS
assert len(PTS) == 495 and len(D["W_questions"]) == 83 and D["pass_t"] == 4
assert all(p["draw"] == 1 for p in PTS)
assert all(p["judge_pass"] == int(p["judge_correctness"] >= 4) for p in PTS)

# reproduce: every answer's judge score and papers precision equal to the raw pull's rows
raw_files = {}
cp = PULL / "s3/g1_collect.jsonl"
raw_files[str(cp)] = sha(cp)
judge_raw = {}
for r in jl(cp):
    a = r.get("a") or {}
    if a.get("status") == "ok":
        judge_raw[(r["config"], r["question_id"], r["draw"])] = (a.get("scores") or {}).get("correctness")
    elif a.get("status") == "no_answer":
        judge_raw[(r["config"], r["question_id"], r["draw"])] = 0
papers_raw = {}
for f in sorted(glob.glob(str(PULL / "l1/papers/*.jsonl"))):
    raw_files[f] = sha(f)
    for r in jl(f):
        papers_raw[(r["config"], r["question_id"], r["draw"])] = (r.get("signals") or {}).get("precision")
mism = [(p["strategy"], p["question_id"]) for p in PTS
        if judge_raw.get((p["strategy"], p["question_id"], 1)) != p["judge_correctness"]
        or papers_raw.get((p["strategy"], p["question_id"], 1)) is None
        or abs(papers_raw[(p["strategy"], p["question_id"], 1)] - p["papers_precision"]) > 1e-9]
if mism:
    raise SystemExit(f"{len(mism)} answers differ from the raw pull: {mism[:3]}")

MEDIAN = statistics.median(p["papers_precision"] for p in PTS)
ON_MEDIAN = sum(p["papers_precision"] == MEDIAN for p in PTS)


def split(rows, m):
    hi = [p["papers_precision"] >= m for p in rows]
    ps = [bool(p["judge_pass"]) for p in rows]
    return [sum((not j) and h for j, h in zip(ps, hi)), sum(j and h for j, h in zip(ps, hi)),
            sum((not j) and (not h) for j, h in zip(ps, hi)), sum(j and (not h) for j, h in zip(ps, hi)), len(rows)]


COUNTS = {c: split([p for p in PTS if p["strategy"] == c], MEDIAN) for c in CONFIGS}
EXPECTED = {"single_pass": [7, 63, 6, 7, 83], "multi_hop": [1, 38, 15, 28, 82], "verified_pass": [6, 65, 5, 7, 83],
            "rlm_5": [4, 20, 21, 37, 82], "rlm_10": [6, 17, 13, 46, 82], "rlm_20": [4, 17, 22, 40, 83]}
if COUNTS != EXPECTED or round(MEDIAN, 4) != 0.6562 or ON_MEDIAN != 3:
    raise SystemExit(f"counts {COUNTS} median {MEDIAN} on it {ON_MEDIAN} differ from the 28 October check")
OWN = {}
for c in CONFIGS:
    rows = [p for p in PTS if p["strategy"] == c]
    m = statistics.median(p["papers_precision"] for p in rows)
    OWN[c] = {"median": round(m, 4), "counts": split(rows, m)}
PASS_ANY = {c: sum(p["judge_pass"] for p in PTS if p["strategy"] == c) for c in CONFIGS}

# ---------------------------------------------------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------------------------------------------------
W, H = 78.0, 68.0
T2P, FP = TextToPath(), FontProperties(family=S457.FONT, size=PT)


def tw(s):
    return T2P.get_text_width_height_descent(s, FP, ismath=False)[0] * MM_PT


def text_mm(fig, x, y, s, **kw):
    return fig.text(x / W, 1 - y / H, s, **kw)


def rect_mm(fig, x, y, w, h, col):
    fig.add_artist(matplotlib.patches.Rectangle((x / W, 1 - (y + h) / H), w / W, h / H, transform=fig.transFigure,
                                                facecolor=col, edgecolor="none", linewidth=0))


NAME_W = max(tw(LABEL[c]) for c in CONFIGS)
NLAB = {c: f"n = {COUNTS[c][4]}" for c in CONFIGS}
NLAB_W = max(tw(s) for s in NLAB.values())
LEFT_OUT_GAP = 6.0                          # names end this far left of the bars: room for an outside count, which
                                            # sits 0.4 mm from its bar and about 4 mm from the name (critic, 28 Oct)
X_NAME = 0.3 + NAME_W                       # names right-aligned here
AX_X0 = X_NAME + LEFT_OUT_GAP
AX_X1 = W - 0.3 - NLAB_W - 1.2
XMAX = 83.0
MM_PER = (AX_X1 - AX_X0) / XMAX
BAR_H, BAR_GAP = 5.0, 3.0
KEY_Y1, KEY_Y2, KEY_Y3 = 3.0, 6.7, 10.4     # key baselines (three lines: the spec's two do not fit 78 mm at 8 pt)
BAR_TOP0 = 12.6
PAD = 0.8                                   # axes box beyond the first and last bar
AX_TOP = BAR_TOP0 - PAD
AX_H = 6 * BAR_H + 5 * BAR_GAP + 2 * PAD
SW = 3.0                                    # swatch side
DIGIT_PAD = 0.3                             # a count goes inside when it fits with this margin each side

fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
ax = fig.add_axes([AX_X0 / W, 1 - (AX_TOP + AX_H) / H, (AX_X1 - AX_X0) / W, AX_H / H])
ax.set_xlim(0, XMAX)
ax.set_ylim(AX_H, 0)                         # y in mm from the axes top, downwards
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.set_yticks([])
ax.set_xticks([0, 20, 40, 60, 80])
ax.set_xticklabels(["0", "20", "40", "60", "80"])
ax.set_xlabel("Answers (n)", labelpad=2)

text_mm(fig, 0.3, KEY_Y1, "b", fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT, va="baseline", ha="left")

# the key: swatch bottom 0.3 mm under the baseline, top 2.7 mm over it. The spec's words, "judge fails, papers support
# more of its claims than the median answer", run 86.7 mm at 8 pt on a 78 mm plate; shortened to fit one line.
KX = 2.8
key_words = ["judge fails, papers above the median answer",      # critic, 28 Oct: parallel wording, each line says
             "judge passes, papers below the median answer",     # what it is compared with ("fewer" alone did not)
             "judge and papers agree (both above / both below)"]
key_w = [tw(s) for s in key_words]


def swatch_item(x, y, cols, words):
    for i, col in enumerate(cols):
        rect_mm(fig, x + i * (SW + 0.3), y - SW + 0.3, SW, SW, col)
    tx = x + len(cols) * SW + (len(cols) - 1) * 0.3 + 0.8
    text_mm(fig, tx, y, words, ha="left", va="baseline")
    return tx + tw(words)


end1 = swatch_item(KX, KEY_Y1, [C_FAIL_HIGH], key_words[0])
end2 = swatch_item(KX, KEY_Y2, [C_PASS_LOW], key_words[1])
end3 = swatch_item(KX, KEY_Y3, [C_BOTH_HIGH, C_BOTH_LOW], key_words[2])
KEY_RIGHT = max(end1, end2, end3)
if KEY_RIGHT > W - 0.5:
    raise SystemExit(f"key runs to {KEY_RIGHT:.1f} mm, past the {W} mm plate")

drawn_labels = []
for i, c in enumerate(CONFIGS):
    yb = PAD + i * (BAR_H + BAR_GAP)        # bar top, axes mm
    yc = yb + BAR_H / 2
    y_fig = AX_TOP + yc                      # centre, plate mm
    text_mm(fig, X_NAME, y_fig, LABEL[c], ha="right", va="center_baseline")
    n = COUNTS[c][4]
    text_mm(fig, AX_X1 + 1.2, y_fig, NLAB[c], ha="left", va="center_baseline")
    x0 = 0
    for k, (v, col) in enumerate(zip(COUNTS[c][:4], SEG_COL)):
        ax.add_patch(matplotlib.patches.Rectangle((x0, yb), v, BAR_H, facecolor=col, edgecolor="none", linewidth=0))
        seg_mm = v * MM_PER
        s = str(v)
        inside = seg_mm >= tw(s) + 2 * DIGIT_PAD
        if inside:
            xt, ha = AX_X0 + (x0 + v / 2) * MM_PER, "center"
        elif k == 0:                         # the left end: just left of the bar
            xt, ha = AX_X0 - 0.4, "right"
        elif k == 3:                         # the right end: just right of the bar (the n label is further right)
            xt, ha = AX_X0 + (x0 + v) * MM_PER + 0.5, "left"
        else:
            raise SystemExit(f"{c} segment {k + 1} ({v}) too narrow for its count and not at an end")
        text_mm(fig, xt, y_fig, s, ha=ha, va="center_baseline", color="#000000")
        drawn_labels.append({"strategy": LABEL[c], "segment": k + 1, "count": v, "width_mm": round(seg_mm, 2),
                             "placed": "inside" if inside else "outside"})
        x0 += v
    assert x0 == n

out = {k: HERE / f"b6_bars.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(fig, W, H, out, title="Figure 5b option 6")

numbers = {
    "option": "b6_bars",
    "what": "Per strategy, the draw-1 answers on the 83 W questions in four groups: judge fails & papers high, both "
            "high, both low, judge passes & papers low (left to right).",
    "rules": {"judge_pass": "correctness >= 4 (S473.PASS_T)",
              "papers_high": "MiniCheck precision >= median of all 495 answers (pooled); on the median counts as high"},
    "median_papers_precision_pooled": MEDIAN,
    "answers_on_the_median": ON_MEDIAN,
    "n_answers": len(PTS),
    "n_questions": len(D["W_questions"]),
    "left_out": D["b_left_out"],
    "segments": ["judge fails, papers high", "both high", "both low", "judge passes, papers low"],
    "colours": SEG_COL,
    "counts": {LABEL[c]: dict(zip(["judge_fails_papers_high", "both_high", "both_low", "judge_passes_papers_low",
                                   "n"], COUNTS[c])) for c in CONFIGS},
    "judge_passes_total": {LABEL[c]: PASS_ANY[c] for c in CONFIGS},
    "alternative_not_drawn_own_median": {LABEL[c]: {"median": OWN[c]["median"],
                                                    "counts": dict(zip(["judge_fails_papers_high", "both_high",
                                                                        "both_low", "judge_passes_papers_low", "n"],
                                                                       OWN[c]["counts"]))} for c in CONFIGS},
    "count_labels": drawn_labels,
    "layout_mm": {"plate": [W, H], "bars_x": [round(AX_X0, 2), round(AX_X1, 2)], "mm_per_answer": round(MM_PER, 4),
                  "bar_height": BAR_H, "bar_gap": BAR_GAP, "key_right_edge": round(KEY_RIGHT, 2)},
    "reproduced": "judge correctness and papers precision of all 495 answers equal to the raw pull "
                  "(s3/g1_collect.jsonl row a, l1/papers/*.jsonl signals.precision); counts equal to the 28 October check",
    "sources": {"b_points.json": {"path": str(BPTS), "sha256": sha(BPTS)},
                "raw_pull": raw_files,
                "upstream_recorded_by_prep": {k: v for k, v in D["inputs_sha256"].items()
                                              if k.startswith(("pull:l1/papers", "pull:s3/g1_collect"))},
                "S473_sha256_at_prep": D["s473_sha256"],
                "S473_sha256_now": sha(ROOT / "scripts/S473_fig5_panels.py"),
                "draw_b6.py": sha(Path(__file__))},
    "files": {k: {"path": str(p), "sha256": sha(p)} for k, p in out.items()},
    "legend_draft": ("b, For each strategy, its draw-1 answers to the 83 answerable questions with all three signals "
                     "(n = 83 answers; n = 82 for multi-hop, RLM-5 and RLM-10, where one answer has no papers score), "
                     "split by two yes-or-no readings: the judge passes the answer (correctness 4 or more of 5) or "
                     "fails it, and the papers support a larger share of its claims (MiniCheck precision) than the "
                     "median answer or a smaller one. The median, 0.656, is the data's own: the median over all 495 "
                     "answers of the six strategies, not a chosen value; the 3 answers exactly on it count as larger. "
                     "Blue, the judge fails the answer but the papers are above the median; vermillion, the judge passes "
                     "it but the papers are below the median; light and dark grey, the two agree (both above, both "
                     "below). Numbers are answers."),
    "builder_notes": [
        "The spec's key wording, 'judge fails, papers support more of its claims than the median answer', is 86.7 mm "
        "at 8 pt on a 78 mm plate; the key is on three lines (the spec said two), so the bars start at 12.6 mm. "
        "Critic, 28 Oct: the key reworded to 'judge fails, papers above the median answer', 'judge passes, papers "
        "below the median answer', 'judge and papers agree (both above / both below)' (the earlier 'papers support "
        "fewer' did not say fewer than what), and the name-to-bar gap widened from 4 to 6 mm so multi-hop's outside "
        "'1' no longer reads as part of its name.",
        "Count labels: the spec put a count inside a segment at least 4 mm wide, else outside its end. At 0.584 mm "
        "per answer that sends interior segments of 5 and 6 (single pass and verified pass, both low) outside, where "
        "they would sit on a neighbour. Drawn instead: inside when the digits fit with 0.3 mm each side (a single "
        "digit needs 2.2 mm, so 4 answers fit); only multi-hop's 1 (0.58 mm) is outside, just left of its bar.",
        "RISK: the vermillion segment grows for the RLMs partly because their papers precision is lower overall "
        "(panel a shows it: means 0.52 to 0.55 against 0.81 to 0.84). The split the seed allows instead, each "
        "strategy's own median, removes that level but gives 23 to 31 'judge passes, papers low' answers in every "
        "strategy (about half fall below a median by construction), which reads flat and is harder to explain. "
        "Recommended: the pooled median, said so in the legend.",
    ],
}
(HERE / "b6_bars_numbers.json").write_text(json.dumps(numbers, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({"key_right": round(KEY_RIGHT, 1), "key_w": [round(x, 1) for x in key_w], "name_w": round(NAME_W, 1),
                  "bars_x": [round(AX_X0, 1), round(AX_X1, 1)], "mm_per": round(MM_PER, 3),
                  "outside": [d for d in drawn_labels if d["placed"] == "outside"]}, indent=1))
