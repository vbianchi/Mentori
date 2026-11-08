"""Figure 5, option b3-8 (scratch, not a plate): what the key's concepts say about the answers the judge fails, by
strategy family. Two designs, each one panel of a main figure, 89 mm wide (FIGURE_LOCK [page] width_single_mm).

  fig5b3-8a  b2-8's mirrored histogram of concept recall only (the papers half is left out: b2-6 already carries
             the judge against the papers). Passed answers above the zero line, failed below, each as a percent of
             its own group; each bar split into RLM (RLM-5, RLM-10, RLM-20) and the other three strategies. A line at
             0.5 splits the failed side, and the counts on each side of it carry the message.
  fig5b3-8b  per strategy, the answers that state every key concept (concept recall 1), split into passed and
             failed by the judge. Rows in b2-6's order.

Reads points.json and recount.json, written by recount.py from raw files only (judge_passages.jsonl, L1 papers rows,
L3 concept_recall.jsonl). Asserts the counts checked on 28 October before drawing. Writes fig5b3-8a.{pdf,svg,png},
fig5b3-8b.{pdf,svg,png} (S457.finish_plate: PNG = the PDF rasterised at 600 dpi), source_data_b3-8a.csv,
source_data_b3-8b.csv and numbers.json.
"""
import csv
import hashlib
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S457", ROOT / "scripts/S457_fig2_panels.py")
S457 = importlib.util.module_from_spec(spec); sys.modules["S457"] = S457; spec.loader.exec_module(S457)

logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

S457.figure_lock_agreed()
plt.rcParams.update(S457.plate_rc("fig5b3_8"))
plt.rcParams["axes.unicode_minus"] = False
LW = max(0.5, S457.LINE_MIN_PT)
BLACK, WHITE = "#000000", "#FFFFFF"
C_RLM, C_OTH = S457.OKABE["reddish purple"], S457.OKABE["blue"]          # design a: strategy family
C_PASS, C_FAIL = "#BBBBBB", S457.OKABE["sky blue"]                         # design b: b2-6's grey (agree) and sky blue
assert (C_RLM, C_OTH, C_FAIL) == ("#CC79A7", "#0072B2", "#56B4E9")
W = S457.FLOCK["page"]["width_single_mm"]
assert W == 89.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


PTS = json.loads((HERE / "points.json").read_text())
REC = json.loads((HERE / "recount.json").read_text())
assert len(PTS) == 495 and REC["changed_vs_old_b8_numbers"] == [] and REC["judge_raw_vs_g1_collect_mismatches"] == []
CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
LABEL = {"single_pass": "single pass", "multi_hop": "multi-hop", "verified_pass": "verified pass",
         "rlm_5": "RLM-5", "rlm_10": "RLM-10", "rlm_20": "RLM-20"}
fam = lambda p: "rlm" if p["strategy"].startswith("rlm") else "other"
N = {1: sum(p["pass"] for p in PTS), 0: sum(1 - p["pass"] for p in PTS)}
assert N == {1: 385, 0: 110}

# ---- design a: counts per bin, side and family ----------------------------------------------------------------------
EDGES = [round(i / 10, 1) for i in range(11)]
bin_of = lambda v: min(int(v * 10 + 1e-9), 9)
CNT = {(jp, f): [0] * 10 for jp in (1, 0) for f in ("rlm", "other")}
for p in PTS:
    CNT[(p["pass"], fam(p))][bin_of(p["concept_recall"])] += 1
EXPECT = {(1, "rlm"): [0, 0, 3, 2, 0, 10, 18, 30, 38, 76], (1, "other"): [2, 2, 6, 13, 7, 26, 23, 19, 42, 68],
          (0, "rlm"): [4, 4, 9, 3, 1, 10, 6, 4, 10, 19], (0, "other"): [5, 9, 13, 7, 0, 4, 1, 1, 0, 0]}
assert CNT == EXPECT, CNT                                    # reproduce before drawing (recount of 28 October)
assert all(p["concept_recall"] == 1 for p in PTS if p["concept_recall"] >= 0.9)   # the last bin holds only 1.0
PCT = {k: [100 * x / N[k[0]] for x in v] for k, v in CNT.items()}
FAM_N = {f: sum(1 for p in PTS if fam(p) == f) for f in ("rlm", "other")}
FAIL_F = {f: sum(1 for p in PTS if fam(p) == f and not p["pass"]) for f in ("rlm", "other")}
UNDER = {f: sum(1 for p in PTS if fam(p) == f and not p["pass"] and p["concept_recall"] < 0.5) for f in ("rlm", "other")}
HALF = {f: FAIL_F[f] - UNDER[f] for f in ("rlm", "other")}
ALL_F = {f: sum(1 for p in PTS if fam(p) == f and not p["pass"] and p["concept_recall"] == 1) for f in ("rlm", "other")}
assert FAM_N == {"rlm": 247, "other": 248} and FAIL_F == {"rlm": 70, "other": 40}
assert UNDER == {"rlm": 21, "other": 34} and HALF == {"rlm": 49, "other": 6} and ALL_F == {"rlm": 19, "other": 0}

# ---- design b: per strategy, the answers that state every key concept ------------------------------------------------
ALLC = {c: {"pass": sum(1 for p in PTS if p["strategy"] == c and p["concept_recall"] == 1 and p["pass"]),
            "fail": sum(1 for p in PTS if p["strategy"] == c and p["concept_recall"] == 1 and not p["pass"])}
        for c in CONFIGS}
assert ALLC == {"single_pass": {"pass": 27, "fail": 0}, "multi_hop": {"pass": 12, "fail": 0},
                "verified_pass": {"pass": 29, "fail": 0}, "rlm_5": {"pass": 21, "fail": 9},
                "rlm_10": {"pass": 29, "fail": 5}, "rlm_20": {"pass": 26, "fail": 5}}, ALLC
PER_S = {c: {"n": sum(1 for p in PTS if p["strategy"] == c),
             "fail": sum(1 for p in PTS if p["strategy"] == c and not p["pass"])} for c in CONFIGS}


def text_mm(fig, H, x, y, s, **kw):
    return fig.text(x / W, 1 - y / H, s, **kw)


def letter(fig, H):
    text_mm(fig, H, 0.3, 2.9, S457.LETTER_CASE("b"), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT,
            va="baseline", ha="left")


def key_row(fig, H, x, y, colour, s):
    fig.add_artist(Rectangle((x / W, 1 - (y + 2.6) / H), 3.0 / W, 2.6 / H, transform=fig.transFigure,
                             facecolor=colour, edgecolor="none"))
    text_mm(fig, H, x + 4.0, y + 2.6, s, va="baseline", ha="left")


def no_text_on_bars(fig, ax, bars_xy):
    """Every text in the axes stays off every bar: bars_xy is a list of (x0, x1, y0, y1) in data units."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    for t in ax.texts:
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
        for (bx0, bx1, by0, by1) in bars_xy:
            if bx0 < x1 and x0 < bx1 and by0 < y1 and y0 < by1 and not getattr(t, "_in_bar", False):
                raise SystemExit(f"text {t.get_text()!r} on a bar at x {bx0:.2f}-{bx1:.2f}")


# =====================================================================================================================
# design a
# =====================================================================================================================
HA = 72.0
fig = plt.figure(figsize=(W / 25.4, HA / 25.4), facecolor=WHITE)
letter(fig, HA)
key_row(fig, HA, 13.0, 0.6, C_RLM, "RLM-5, RLM-10, RLM-20")
key_row(fig, HA, 13.0, 4.6, C_OTH, "single pass, multi-hop, verified pass")
AX_X, AX_Y, AX_W, AX_H = 13.0, 10.5, 74.0, 48.0
ax = fig.add_axes([AX_X / W, 1 - (AX_Y + AX_H) / HA, AX_W / W, AX_H / HA])
YTOP, YBOT = 40, -48
ctr = [(EDGES[k] + EDGES[k + 1]) / 2 for k in range(10)]
BW = 0.09
bars = []
for jp, sgn in ((1, 1), (0, -1)):
    inner, outer = PCT[(jp, "other")], PCT[(jp, "rlm")]                  # the other three next to the zero line
    ax.bar(ctr, [sgn * v for v in inner], width=BW, color=C_OTH, linewidth=0, zorder=2)
    ax.bar(ctr, [sgn * v for v in outer], bottom=[sgn * v for v in inner], width=BW, color=C_RLM, linewidth=0, zorder=2)
    for k in range(10):
        tot = sgn * (inner[k] + outer[k])
        bars.append((ctr[k] - BW / 2, ctr[k] + BW / 2, min(0, tot), max(0, tot)))
ax.axhline(0, color=BLACK, lw=LW, zorder=3)
ax.plot([0.5, 0.5], [0, YBOT], color=BLACK, lw=LW, zorder=3, solid_capstyle="butt")
ax.set_xlim(-0.01, 1.01)
ax.set_ylim(YBOT, YTOP)
ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["0", "0.5", "1"])
ax.set_yticks([-40, -20, 0, 20, 40]); ax.set_yticklabels(["40", "20", "0", "20", "40"])
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlabel("Concept recall\n(share of the key’s concepts the answer states)", labelpad=2)
# side labels left of the axis, one per half
y0 = ax.transData.transform((0, 0))[1]
for s, ymid in ((f"Passed, % of {N[1]}", YTOP / 2), (f"Failed, % of {N[0]}", YBOT / 2)):
    ax.text(-0.135, ymid, s, rotation=90, ha="center", va="center", transform=ax.get_yaxis_transform())
# the message: failed answers each side of 0.5, by family
ax.text(0.25, -30.5, "under half", ha="center", va="baseline")
ax.text(0.25, -37.0, f"{UNDER['other']} of {FAIL_F['other']} others", ha="center", va="baseline")
ax.text(0.25, -43.5, f"{UNDER['rlm']} of {FAIL_F['rlm']} RLM", ha="center", va="baseline")
ax.text(0.73, -30.5, "half or more", ha="center", va="baseline")
ax.text(0.73, -37.0, f"{HALF['other']} of {FAIL_F['other']} others", ha="center", va="baseline")
ax.text(0.73, -43.5, f"{HALF['rlm']} of {FAIL_F['rlm']} RLM", ha="center", va="baseline")
t19 = ax.text(ctr[9], -PCT[(0, "rlm")][9] - 1.5, str(ALL_F["rlm"]), ha="center", va="top")
# the in-bar count at the passed answers' 1.0 bin: RLM and others
ti = ax.text(ctr[9], PCT[(1, "other")][9] / 2, str(CNT[(1, "other")][9]), ha="center", va="center", color=WHITE)
to = ax.text(ctr[9], PCT[(1, "other")][9] + PCT[(1, "rlm")][9] / 2, str(CNT[(1, "rlm")][9]), ha="center",
             va="center", color=BLACK)
ti._in_bar = to._in_bar = True
no_text_on_bars(fig, ax, bars)
outA = {k: HERE / f"fig5b3-8a.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(fig, W, HA, outA, title="Figure 5b option b3-8a")

# =====================================================================================================================
# design b
# =====================================================================================================================
HB = 50.0
fig = plt.figure(figsize=(W / 25.4, HB / 25.4), facecolor=WHITE)
letter(fig, HB)
key_row(fig, HB, 27.0, 0.6, C_FAIL, "judge fails (score 3 or less)")
key_row(fig, HB, 27.0, 4.6, C_PASS, "judge passes (score 4 or more)")
BX, BY, BWID, BH = 27.0, 10.5, 47.0, 30.0
ax = fig.add_axes([BX / W, 1 - (BY + BH) / HB, BWID / W, BH / HB])
XMAX = 35
rows = list(range(len(CONFIGS)))[::-1]
bars = []
for c, y in zip(CONFIGS, rows):
    p_, f_ = ALLC[c]["pass"], ALLC[c]["fail"]
    ax.barh(y, p_, height=0.62, color=C_PASS, linewidth=0, zorder=2)
    ax.barh(y, f_, left=p_, height=0.62, color=C_FAIL, linewidth=0, zorder=2)
    t = ax.text(p_ / 2, y, str(p_), ha="center", va="center"); t._in_bar = True
    if f_:
        t = ax.text(p_ + f_ / 2, y, str(f_), ha="center", va="center"); t._in_bar = True
    else:
        ax.text(p_ + 0.6, y, "0", ha="left", va="center")
    ax.text(1.03, y, f"n = {p_ + f_}", ha="left", va="center", transform=ax.get_yaxis_transform())
    bars.append((0, p_ + f_, y - 0.31, y + 0.31))
ax.set_yticks(rows); ax.set_yticklabels([LABEL[c] for c in CONFIGS])
ax.tick_params(axis="y", length=0)
ax.set_ylim(-0.6, len(CONFIGS) - 0.4)
ax.set_xlim(0, XMAX)
ax.set_xticks([0, 10, 20, 30])
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.spines["left"].set_visible(False)
ax.set_xlabel("Answers that state every key concept (n)", labelpad=2)
no_text_on_bars(fig, ax, bars)
outB = {k: HERE / f"fig5b3-8b.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(fig, W, HB, outB, title="Figure 5b option b3-8b")

# ---- Source Data and numbers -----------------------------------------------------------------------------------------
with (HERE / "source_data_b3-8a.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["judge", "family", "bin_lo", "bin_hi", "bin_rule", "answers", "group_n", "percent_of_group"])
    for jp in (1, 0):
        for fm in ("other", "rlm"):
            for k in range(10):
                w.writerow(["pass" if jp else "fail", fm, EDGES[k], EDGES[k + 1],
                            "lo <= x < hi" if k < 9 else "x = 1.0 (no value in 0.9 to 1.0 except 1.0)",
                            CNT[(jp, fm)][k], N[jp], round(PCT[(jp, fm)][k], 4)])
with (HERE / "source_data_b3-8b.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["strategy", "all_concepts_judge_pass", "all_concepts_judge_fail", "all_concepts_n",
                "strategy_answers_n", "strategy_judge_fail_n"])
    for c in CONFIGS:
        w.writerow([LABEL[c], ALLC[c]["pass"], ALLC[c]["fail"], ALLC[c]["pass"] + ALLC[c]["fail"],
                    PER_S[c]["n"], PER_S[c]["fail"]])

nums = {
    "option": "b3-8 (a and b)",
    "message": "When the judge fails an answer from single pass, multi-hop or verified pass, the answer misses most "
               "key concepts (34 of 40 state under half of them); when it fails an RLM answer, the answer often "
               "states them (49 of 70 state half or more, 19 state every one).",
    "answer_set": "draw 1; the 83 answerable questions whose six strategies all have a MiniCheck papers row (the W "
                  "set of S473); answers with a judge score, a concept recall and a papers precision: 495 (3 left "
                  "out: recount.json left_out); judge pass = correctness >= 4 (variant a, no passages); a no-answer "
                  "row scores 0",
    "plates_mm": {"fig5b3-8a": [W, HA], "fig5b3-8b": [W, HB]},
    "n": {"pass": N[1], "fail": N[0], "rlm_answers": FAM_N["rlm"], "other_answers": FAM_N["other"]},
    "a": {"counts": {f"{'pass' if k[0] else 'fail'}|{k[1]}": v for k, v in CNT.items()},
          "percent_of_judge_group": {f"{'pass' if k[0] else 'fail'}|{k[1]}": [round(x, 4) for x in v]
                                     for k, v in PCT.items()},
          "fail_by_family": FAIL_F, "fail_concept_under_half": UNDER, "fail_concept_half_or_more": HALF,
          "fail_every_concept": ALL_F, "pass_every_concept": {"rlm": CNT[(1, "rlm")][9], "other": CNT[(1, "other")][9]},
          "y_limits_percent": [YBOT, YTOP]},
    "b": {"every_concept_by_strategy": ALLC, "strategy_totals": PER_S,
          "every_concept_by_family": REC["all_concepts_by_family"]},
    "not_drawn": {
        "fail_every_concept_judge_scores": REC["fail_all_concepts"]["by_judge_score"],
        "fail_every_concept_justification_keywords": REC["fail_all_concepts"]["justification_names_a_wrong_or_conflicting_statement"],
        "pass_concept_under_half": {"n": REC["pass_concept_lt_half"]["n"], "by_strategy": REC["pass_concept_lt_half"]["by_strategy"]},
        "pass_papers_under_half_(b2-6 territory)": REC["pass_papers_lt_half"],
        "summaries": REC["summaries"]},
    "recount": {"changed_vs_old_b8_numbers": REC["changed_vs_old_b8_numbers"],
                "judge_raw_vs_g1_collect_mismatches": REC["judge_raw_vs_g1_collect_mismatches"],
                "judge_rows_replaced_by_g1r15": REC["judge_rows_replaced_by_g1r15"]},
    "files": {**{f"a.{k}": {"path": str(v), "sha256": sha(v)} for k, v in outA.items()},
              **{f"b.{k}": {"path": str(v), "sha256": sha(v)} for k, v in outB.items()},
              "source_data_b3-8a.csv": sha(HERE / "source_data_b3-8a.csv"),
              "source_data_b3-8b.csv": sha(HERE / "source_data_b3-8b.csv")},
    "sources": {"raw_inputs_sha256": REC["inputs_sha256"],
                "recount.py": {"path": str(HERE / "recount.py"), "sha256": sha(HERE / "recount.py")},
                "recount.json": sha(HERE / "recount.json"), "points.json": sha(HERE / "points.json"),
                "S457_fig2_panels.py (plate helpers)": sha(ROOT / "scripts/S457_fig2_panels.py"),
                "FIGURE_LOCK.toml": sha(ROOT / "experiments/FIGURE_LOCK.toml"),
                "script": {"path": str(Path(__file__).resolve()), "sha256": sha(__file__)}},
}
(HERE / "numbers.json").write_text(json.dumps(nums, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({"a": nums["a"]["fail_by_family"], "under": UNDER, "half": HALF, "all": ALL_F, "b": ALLC}, indent=None))
