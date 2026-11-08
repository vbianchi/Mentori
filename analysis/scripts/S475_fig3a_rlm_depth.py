#!/usr/bin/env python3
"""S475 - a provisional Figure 3 panel draft: concept recall of the two RLMs by turn cap, side by side.

WHY. Valerio, 22 October: "Make a plot with the two RLMs depth in comparison". Plan row L2 (S474, committed
e4823e1) scored the depth answers of both RLMs for concept recall on D12's loose matcher, provisional (D17), no
judge: G5, Mentori's RLM (exp_06), gemini-3-flash-preview, draw 1 (D98), 86 questions x 10 caps = 860 answers; G6,
the authors' package (rlms 0.1.3), gemini-3-flash-preview, three draws, 86 x 10 x 3 = 2,580 answers. This plate draws
S474's numbers as they are; it computes nothing in another way (D84: exploratory phase, no analysis rule here).

ONE COMMAND, from the repository root:

    uv run --frozen python scripts/S475_fig3a_rlm_depth.py

READS (run-derived outputs of S474, the trust boundary README.md:13-27):
  findings/recompute/L2/concept_recall.jsonl   one row per answer (3,440): system, cap, question, draw, the loose
                                               concept recall, failed, cap_reached, stopped_by_cap, d92_action
  findings/recompute/L2/cap_tables.json        S474's per-cap means, 95% percentile intervals (10,000 question
                                               resamples, seed 20261013, LIST.md Rules 1 and 2), shares, D92 counts
  findings/recompute/L2/header.json            S474's provenance (provisional, matcher, counts)
  experiments/rlm_ref/run_rlm_ref.py, G4_runs/README.md, G5_runs/README.md, D98_subset/d98_subset.json
                                               through S459.planned_total(): Figure 3's planned answers (the "of N")
  experiments/FIGURE_LOCK.toml                 every size, font, colour and width (D84, D87)

REPRODUCE FIRST (README.md:75-79). Before anything is drawn, every number of cap_tables.json the plate uses is
recomputed from concept_recall.jsonl by S474's stated method (each question's mean over its draws at a cap, the mean
over the 86 questions, the 2.5th and 97.5th percentiles, numpy linear, of the means over 10,000 resamples
numpy.random.default_rng(20261013).integers(0, 86, size=(10000, 86)) of the questions sorted; failed answers in and
left out; four decimals) and must equal it: per system and cap the answers, questions, mean, interval, per-draw
means, failed answers, cap_reached and stopped_by_cap shares and the D92 action counts. The anchors S474 printed
(G5 cap 20 = 76.8%, G6 cap 50 = 65.9%) must come out. Any difference stops the run (exit 2), nothing written.
D186 (4): reproduce() and compute() take the value field; with field "concept_recall" (S474 --d181's L2_d181, D181's
reading on key v2.5) the anchors are ANCHORS_D181, the means S474 --d181 printed in L2_d181/cap_tables.md (G5 cap 20 =
71.9%, G6 cap 50 = 63.1%). S476 runs the v2.4 loose anchors on L2/ first, then these on L2_d181/. This script's own
plate (the command above) still draws L2/'s loose reading.

RETIRED (23 October; experiments/RUNNING.md:964, :972): do not run this script. S476 imports its functions and writes
the plate. Since FF3 a's one list that plate is Supplementary Figure 8, in findings/figures_provisional/supp_fig8_depth/,
and OUT below still names the folder of main Figure 3 as it was, which no longer exists. If run, this script would write:

WRITES findings/figures_provisional/fig3a_rlm_depth/ (earlier "Figure 3*" and "Source Data Fig. 3*" files there are
deleted first; findings/figures_provisional/fig3/, S459's plate, is not touched):
  Figure 3 (provisional, <n> of <N>).{pdf,svg,png}   [page] width_double_mm wide; [type] font_min_pt text in the first
        of [type] font_families; panel letters [type] panel_letter_pt bold lowercase; Okabe-Ito colours (blue for
        Mentori's RLM, vermillion for the authors' package) and black; no gridlines; the PNG is the PDF rasterised by
        MuPDF at 600 dpi (S457.finish_plate). The name is the "(provisional, n of m)" form: S448 R1 also accepts
        "(provisional, panel a draft, n of m)", but R8 part (5) reads the tag as "(provisional, <n> of <m>)" only.
  Source Data Fig. 3 (provisional, ...).xlsx, its caption .md, figure3_numbers.json, figure3_provenance.json,
        legend_draft.md. n = the answers drawn (860 + 2,580); N = Figure 3's written plan under D98, as S459 counts it.

THE PANELS
  a  concept recall (%) by turn cap (log axis, every cap labelled), both RLMs: small dots, each question's value
     (G5 its one answer, G6 the mean of its three), spread across the cap at right angles to the value axis
     (S457.swarm), G5 left of the cap and G6 right of it; line and large dot, their mean over the 86 questions
     (cap_tables.json "all": failed answers score 0, Rule 10); band, its 95% interval (Rule 2).
  b  the share of answers whose turns used reached the cap (S474's cap_reached: turns_used >= cap), by cap, both RLMs.
No hypothesis test. No model call; no Ollama port contacted; no ssh.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import math
import platform
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
L2 = ROOT / "findings" / "recompute" / "L2"
ROWS_F, TABLES_F, HEADER_F = L2 / "concept_recall.jsonl", L2 / "cap_tables.json", L2 / "header.json"
OUT = ROOT / "findings" / "figures_provisional" / "fig3a_rlm_depth"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
S474_F = ROOT / "scripts" / "S474_l2_concept_recall.py"
FIG_N = 3
SEED, N_BOOT, PCT = 20261013, 10000, (2.5, 97.5)      # S474 (LIST.md Rule 2, S407's convention)
ANCHORS = {("G5", 20): "76.8", ("G6", 50): "65.9"}   # cap_tables.md as S474 printed it, mean %
ANCHORS_D181 = {("G5", 20): "71.9", ("G6", 50): "63.1"}   # D186 (4): L2_d181/cap_tables.md as S474 --d181 printed it
LOOSE, D181_FIELD = "concept_recall_loose", "concept_recall"   # the value field of L2/ and of L2_d181/ (S474 tables)
D92_ACTIONS = ("rebuild", "rerun", "stays_failed")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S457 = _load("S457", ROOT / "scripts" / "S457_fig2_panels.py")      # plate_rc, finish_plate, swarm, half_up
S459 = _load("S459", ROOT / "scripts" / "S459_fig3_rlm_ref_caps.py")  # design_constants, planned_total
# D155: planned_total() reads the plan tables of G4's and G5's run READMEs, which are working documents that keep
# changing. S475, S476 and S485 (which take S459 from here) read them from their frozen copy instead, each as committed
# at f30c75e5 (findings/recompute/fig3_readmes_inputs/<G4_runs|G5_runs>/README.md), checked against
# frozen_inputs/SHA256SUMS; the provenance then names and hashes that copy.
S459.G4_README = S459.FR.check_committed(S459.FR.frozen("fig3_readmes", "G4_runs/README.md"))
S459.G5_README = S459.FR.check_committed(S459.FR.frozen("fig3_readmes", "G5_runs/README.md"))

FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
PT = float(FLOCK["type"]["font_min_pt"])
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper
FONT = FLOCK["type"]["font_families"][0]
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])
FIG_W_MM = float(FLOCK["page"]["width_double_mm"])
FIG_H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
MM_PT = 25.4 / 72
SYSTEMS = {"G5": {"name": "RLM", "colour": OKABE["blue"], "side": -1,
                  "sheet_name": "G5, RLM (exp_06), gemini-3-flash-preview, draw 1"},
           "G6": {"name": "Zhang RLM", "colour": OKABE["vermillion"], "side": +1,
                  "sheet_name": "G6, Zhang RLM (rlms 0.1.3), gemini-3-flash-preview, draws 1, 2, 3"}}
LW_MEAN = max(1.0, LINE_MIN_PT)
MS_MEAN_MM, DOT_MM, DOT_PITCH_MM, DOT_HALF_MM, STRIP_OFF_MM = 1.5, 0.40, 0.45, 2.3, 2.8
DOT_ALPHA, BAND_ALPHA = 0.5, 0.18


def sha256_file(p: Path) -> str:
    return S457.sha256_file(Path(p))


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT))


def git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


# ---------------------------------------------------------------------------------------------------------------
# Reproduce first: cap_tables.json from concept_recall.jsonl, by S474's stated method
# ---------------------------------------------------------------------------------------------------------------
def per_question(R, cap, qorder, drop_failed, field=LOOSE):
    vals = defaultdict(list)
    for r in R:
        if r["cap"] == cap and not (drop_failed and r["failed"]):
            vals[r["question_id"]].append(r[field])
    return np.array([np.mean(vals[q]) if vals[q] else np.nan for q in qorder]), vals


def interval(vec, res):
    """The mean over the questions with a value, and the percentile interval of that mean over the resamples (a
    resample holding no question with a value is left out, as S474 states)."""
    have = ~np.isnan(vec)
    m = []
    for row in res:
        v = vec[row]
        v = v[~np.isnan(v)]
        if v.size:
            m.append(v.mean())
    lo, hi = np.percentile(np.array(m), PCT)
    return int(have.sum()), round(float(np.nanmean(vec)), 4), [round(float(lo), 4), round(float(hi), 4)]


def reproduce(rows, tables, caps, field=LOOSE, anchors=None):
    """field: the value read (LOOSE for L2/, D181_FIELD for L2_d181/); anchors: default ANCHORS for LOOSE,
    ANCHORS_D181 for D181_FIELD."""
    if field not in (LOOSE, D181_FIELD):
        raise SystemExit(f"reproduce: field {field!r} is neither {LOOSE} nor {D181_FIELD}")
    anchors = anchors if anchors is not None else (ANCHORS if field == LOOSE else ANCHORS_D181)
    probs, compared = [], 0
    qorder = sorted({r["question_id"] for r in rows})
    if len(qorder) != 86:
        probs.append(f"{len(qorder)} questions in {rel(ROWS_F)}, not 86")
    res = np.random.default_rng(SEED).integers(0, len(qorder), size=(N_BOOT, len(qorder)))
    mine = {}
    for s in SYSTEMS:
        R = [r for r in rows if r["system"] == s]
        draws = sorted({r["draw"] for r in R})
        for mode, drop in (("all", False), ("failed_left_out", True)):
            for c in caps:
                C = [r for r in R if r["cap"] == c]
                kept = [r for r in C if not (drop and r["failed"])]
                vec, _ = per_question(R, c, qorder, drop, field)
                nq, mean, ci = interval(vec, res)
                got = {"answers": len(kept), "questions": nq, "mean": mean, "ci95": ci,
                       "per_draw_mean": {str(d): round(float(np.mean([r[field] for r in kept
                                                                      if r["draw"] == d])), 4)
                                         for d in draws if any(r["draw"] == d for r in kept)},
                       "failed": sum(r["failed"] for r in C),
                       "cap_reached_share": round(sum(r["cap_reached"] for r in C) / len(C), 4),
                       "stopped_by_cap_share": round(sum(r["stopped_by_cap"] for r in C) / len(C), 4),
                       "d92": {x: {"failed": sum(r.get("d92_action") == x and r["failed"] for r in C),
                                   "not_failed": sum(r.get("d92_action") == x and not r["failed"] for r in C)}
                               for x in D92_ACTIONS}}
                want = tables[s][mode]["per_cap"][str(c)]
                for k, v in got.items():
                    compared += 1
                    if want.get(k) != v:
                        probs.append(f"{s} {mode} cap {c} {k}: cap_tables.json {want.get(k)!r}, recomputed {v!r}")
                mine[(s, mode, c)] = got
    for (s, c), txt in anchors.items():
        v = S457.half_up(100 * mine[(s, "all", c)]["mean"], 1)
        compared += 1
        if v != txt:
            probs.append(f"anchor {s} cap {c}: S474 printed {txt}%, recomputed {v}%")
    if probs:
        print("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs[:10]), file=sys.stderr)
        sys.exit(2)
    return {"compared": compared, "questions": len(qorder), "seed": SEED, "n_boot": N_BOOT,
            "what": "per system, mode (failed in, failed left out) and cap: answers, questions, mean, 95% interval, "
                    "per-draw means, failed, cap_reached and stopped_by_cap shares, D92 action counts; and the "
                    "anchors " + ", ".join(f"{s} cap {c} = {v}%" for (s, c), v in anchors.items())}, qorder


# ---------------------------------------------------------------------------------------------------------------
# The numbers the plate draws
# ---------------------------------------------------------------------------------------------------------------
A_COLS = ["row", "system", "system_name", "cap", "question_id", "value_pct", "draws", "questions", "answers",
          "mean_pct", "ci95_lo_pct", "ci95_hi_pct", "failed", "failed_d92_rebuild", "failed_d92_rerun",
          "failed_d92_stays_failed", "failed_no_d92_action", "not_failed_d92_rerun"]
B_COLS = ["system", "system_name", "cap", "answers", "cap_reached_n", "cap_reached_pct", "stopped_by_cap_n",
          "stopped_by_cap_pct"]


def compute(rows, tables, caps, qorder, field=LOOSE):
    a_sum, a_q, b = [], [], []
    for s, info in SYSTEMS.items():
        R = [r for r in rows if r["system"] == s]
        for c in caps:
            t = tables[s]["all"]["per_cap"][str(c)]
            C = [r for r in R if r["cap"] == c]
            a_sum.append({"row": "cap", "system": s, "system_name": info["sheet_name"], "cap": c, "question_id": None,
                          "value_pct": None, "draws": len({r["draw"] for r in C}), "questions": t["questions"],
                          "answers": t["answers"], "mean_pct": 100 * t["mean"], "ci95_lo_pct": 100 * t["ci95"][0],
                          "ci95_hi_pct": 100 * t["ci95"][1], "failed": t["failed"],
                          "failed_d92_rebuild": t["d92"]["rebuild"]["failed"],
                          "failed_d92_rerun": t["d92"]["rerun"]["failed"],
                          "failed_d92_stays_failed": t["d92"]["stays_failed"]["failed"],
                          "failed_no_d92_action": t["failed"] - sum(t["d92"][x]["failed"] for x in D92_ACTIONS),
                          "not_failed_d92_rerun": t["d92"]["rerun"]["not_failed"]})
            _, vals = per_question(R, c, qorder, False, field)
            for q in qorder:
                a_q.append({"row": "question", "system": s, "system_name": info["sheet_name"], "cap": c,
                            "question_id": q, "value_pct": 100 * float(np.mean(vals[q])), "draws": len(vals[q]),
                            **{k: None for k in A_COLS[7:]}})
            b.append({"system": s, "system_name": info["sheet_name"], "cap": c, "answers": len(C),
                      "cap_reached_n": sum(r["cap_reached"] for r in C),
                      "cap_reached_pct": 100 * t["cap_reached_share"],
                      "stopped_by_cap_n": sum(r["stopped_by_cap"] for r in C),
                      "stopped_by_cap_pct": 100 * t["stopped_by_cap_share"]})
            if round(b[-1]["cap_reached_n"] / len(C), 4) != t["cap_reached_share"]:
                raise SystemExit(f"{s} cap {c}: cap_reached count and share disagree")
    a = [{k: r[k] for k in A_COLS} for r in a_sum + a_q]
    return {"a": a, "b": [{k: r[k] for k in B_COLS} for r in b]}


def sheets_of(fn):
    out = []
    for letter, cols in (("a", A_COLS), ("b", B_COLS)):
        out.append((f"Fig. {FIG_N}{LETTER_CASE(letter)}", cols, [[r[c] for c in cols] for r in fn[letter]]))
    return out


def write_source_data(sheets, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols, rows in sheets:
        ws = wb.create_sheet(name)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rows:
            ws.append([("" if x is None else x) for x in r])
    wb.save(path)


# ---------------------------------------------------------------------------------------------------------------
# The plate
# ---------------------------------------------------------------------------------------------------------------
def draw_figure(fn, caps, paths):
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

    plt.rcParams.update(S457.plate_rc("S475"))
    plt.rcParams["axes.unicode_minus"] = False
    t2p = TextToPath()

    def tw(s):
        fp = FontProperties(family=FONT, size=PT)
        return t2p.get_text_width_height_descent(s, fp, ismath=False)[0] * MM_PT

    W = FIG_W_MM
    LEFT, RIGHT = 15.0, 3.0
    AX_W = W - LEFT - RIGHT
    LINE = PT * MM_PT * 1.25
    KEY1, KEY2 = 3.4, 3.4 + LINE + 0.6                  # key rows (centres, mm from the top)
    A_TOP, A_H = KEY2 + LINE + 1.4, 66.0
    XAX = 2 * MM_PT + 2 * MM_PT + LINE + 2 * MM_PT + LINE
    B_HEAD = A_TOP + A_H + XAX + 5.0                    # b's letter and n line (centre)
    B_TOP, B_H = B_HEAD + 3.0, 30.0
    H = B_TOP + B_H + XAX + 1.5
    if H > FIG_H_MAX_MM - 0.05:
        raise SystemExit(f"the page would be {H:.1f} mm high, over [page] height_max_mm {FIG_H_MAX_MM}")
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    printed, readback, overlaps = {}, [], {}

    def num(artist, entry):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])

    def text_mm(x, y, s, **kw):
        return fig.text(x / W, 1 - y / H, s, **kw)

    def letter(x, y, s):
        text_mm(x, y, LETTER_CASE(s), fontsize=PT_LETTER, fontweight=LETTER_WEIGHT, va="center", ha="left")

    XLO, XHI = 0.85, 58.0
    dec_per_mm = (math.log10(XHI) - math.log10(XLO)) / AX_W
    # the strips must stay apart between the two closest caps
    gap_mm = min(math.log10(b / a) for a, b in zip(caps, caps[1:])) / dec_per_mm
    if 2 * (STRIP_OFF_MM + DOT_HALF_MM + DOT_MM / 2) >= gap_mm:
        raise SystemExit(f"the dot strips of two neighbouring caps would touch ({gap_mm:.1f} mm apart)")

    def cap_axis(ax, ylabel, ylim):
        ax.set_xscale("log")
        ax.set_xlim(XLO, XHI)
        ax.xaxis.set_major_locator(FixedLocator(list(caps)))
        ax.xaxis.set_major_formatter(FixedFormatter([str(c) for c in caps]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_ylim(*ylim)
        ax.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
        ax.yaxis.set_major_formatter(FixedFormatter(["0", "25", "50", "75", "100"]))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_xlabel("turn cap", labelpad=2)
        ax.set_ylabel(ylabel, labelpad=2)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    a_rows = fn["a"]
    a_idx = {(r["system"], r["cap"]): i for i, r in enumerate(a_rows) if r["row"] == "cap"}
    b_idx = {(r["system"], r["cap"]): i for i, r in enumerate(fn["b"])}

    # ---- a
    ax = axes_mm(LEFT, A_TOP, AX_W, A_H)
    cap_axis(ax, "concept recall (%)", (-2, 102))
    for s, info in SYSTEMS.items():
        col = info["colour"]
        summ = [a_rows[a_idx[(s, c)]] for c in caps]
        ax.fill_between(list(caps), [r["ci95_lo_pct"] for r in summ], [r["ci95_hi_pct"] for r in summ],
                        facecolor=col, alpha=BAND_ALPHA, edgecolor="none", linewidth=0, zorder=1)
        for c in caps:
            vals = [r["value_pct"] for r in a_rows if r["row"] == "question" and r["system"] == s and r["cap"] == c]
            off, over = S457.swarm([v / 100 * A_H for v in vals], half=DOT_HALF_MM, pitch=DOT_PITCH_MM, dot=DOT_MM)
            overlaps[f"{s} cap {c}"] = over
            xs = [c * 10 ** ((info["side"] * STRIP_OFF_MM + o) * dec_per_mm) for o in off]
            ln, = ax.plot(xs, vals, ls="none", marker="o", ms=DOT_MM / MM_PT, mfc=col, mew=0, alpha=DOT_ALPHA,
                          zorder=2, clip_on=False)
            readback.append((f"a {s} cap {c} dots", list(ln.get_ydata()), vals))
        ln, = ax.plot(list(caps), [r["mean_pct"] for r in summ], color=col, lw=LW_MEAN, marker="o",
                      ms=MS_MEAN_MM / MM_PT, mew=0, zorder=4, clip_on=False)
        readback.append((f"a {s} means", list(ln.get_ydata()), [r["mean_pct"] for r in summ]))
    letter(1.5, KEY1, "a")

    # the key, above a: one swatch per system (line, large dot, band), then what the marks are
    x = LEFT
    for s, info in SYSTEMS.items():
        col = info["colour"]
        fig.add_artist(Rectangle(((x) / W, 1 - (KEY1 + 1.1) / H), 6.0 / W, 2.2 / H, transform=fig.transFigure,
                                 facecolor=col, alpha=BAND_ALPHA, edgecolor="none"))
        fig.add_artist(Line2D([x / W, (x + 6.0) / W], [1 - KEY1 / H] * 2, transform=fig.transFigure, color=col,
                              lw=LW_MEAN))
        fig.add_artist(Line2D([(x + 3.0) / W], [1 - KEY1 / H], transform=fig.transFigure, ls="none", marker="o",
                              ms=MS_MEAN_MM / MM_PT, mfc=col, mew=0))
        fmt = info["name"] + (", one draw" if s == "G5" else ", mean of three draws") + ", n = {questions} questions"
        t = text_mm(x + 7.2, KEY1, fmt.format(questions=a_rows[a_idx[(s, caps[0])]]["questions"]),
                    va="center", ha="left")
        num(t, {"sheet": f"Fig. {FIG_N}a", "row": a_idx[(s, caps[0])], "format": fmt})
        x += 7.2 + tw(t.get_text()) + 6.0
    marks = "line and large dot: mean over the questions; band: 95% interval; small dot: one question"
    t = text_mm(LEFT, KEY2, marks, va="center", ha="left")
    num(t, {"fixed": marks, "why": "the key's words; 95% is the interval's level (LIST.md Rule 2)"})

    # ---- b
    bx = axes_mm(LEFT, B_TOP, AX_W, B_H)
    cap_axis(bx, "reached the cap (%)", (-4, 104))
    for s, info in SYSTEMS.items():
        rows_b = [fn["b"][b_idx[(s, c)]] for c in caps]
        ln, = bx.plot(list(caps), [r["cap_reached_pct"] for r in rows_b], color=info["colour"], lw=LW_MEAN,
                      marker="o", ms=MS_MEAN_MM / MM_PT, mew=0, zorder=3, clip_on=False)
        readback.append((f"b {s}", list(ln.get_ydata()), [r["cap_reached_pct"] for r in rows_b]))
    letter(1.5, B_HEAD, "b")
    x = LEFT
    for s, info in SYSTEMS.items():
        fmt = info["name"] + ": n = {answers} answers per cap"
        t = text_mm(x, B_HEAD, fmt.format(answers=fn["b"][b_idx[(s, caps[0])]]["answers"]), va="center", ha="left")
        num(t, {"sheet": f"Fig. {FIG_N}b", "row": b_idx[(s, caps[0])], "format": fmt})
        x += tw(t.get_text()) + 6.0
    if any(len({r["answers"] for r in fn["b"] if r["system"] == s}) != 1 for s in SYSTEMS):
        raise SystemExit("b: the answers per cap differ between caps; one n per system cannot be printed")
    if any(len({r["questions"] for r in a_rows if r["row"] == "cap" and r["system"] == s}) != 1 for s in SYSTEMS):
        raise SystemExit("a: the questions per cap differ between caps; one n per system cannot be printed")
    S457.finish_plate(fig, W, H, paths, title="Figure 3")
    return W, H, printed, readback, overlaps


def check_drawn(readback):
    bad, n = [], 0
    for what, got, want in readback:
        for g, w in zip(got, want, strict=True):
            n += 1
            if abs(float(g) - float(w)) > 1e-9:
                bad.append(f"{what}: drawn {g}, Source Data {w}")
    return bad, n


# ---------------------------------------------------------------------------------------------------------------
# Legend and caption
# ---------------------------------------------------------------------------------------------------------------
def legend_and_caption(fn, tables, header, caps, stamp, n, N):
    A, B = (f"**{LETTER_CASE(x)}**" for x in "ab")
    summ = {(r["system"], r["cap"]): r for r in fn["a"] if r["row"] == "cap"}
    fail = {s: sum(summ[(s, c)]["failed"] for c in caps) for s in SYSTEMS}
    ans = {s: sum(summ[(s, c)]["answers"] for c in caps) for s in SYSTEMS}
    g6 = {c: summ[("G6", c)] for c in caps}
    act = {k: sum(g6[c][f"failed_d92_{k}"] for c in caps) for k in D92_ACTIONS}
    none = {c: g6[c]["failed_no_d92_action"] for c in caps if g6[c]["failed_no_d92_action"]}
    if sum(act.values()) + sum(none.values()) != fail["G6"] or any(v < 0 for v in none.values()):
        raise SystemExit(f"G6: the D92 actions {act} and the unlisted {none} do not add to its {fail['G6']} failed")
    none_txt = "".join(f", {k} (cap {c}) on no rerun list" for c, k in none.items())
    if any(summ[("G5", c)][f"failed_d92_{k}"] for c in caps for k in D92_ACTIONS):
        raise SystemExit("a G5 answer carries a D92 action; the legend says D92 concerns the package only")
    nf_rerun = sum(g6[c]["not_failed_d92_rerun"] for c in caps)
    note = header["counts"]["G5"]["note_removed"]
    c30, c50 = g6[30], g6[50]
    caps_txt = ", ".join(str(c) for c in caps[:-1]) + f" and {caps[-1]}"
    title = "Concept recall of two recursive language models across turn caps"
    # Valerio, 23 October: the caption describes the image only, under 350 words, in the style of the resubmission's
    # captions (resubmission/05_figures/Figure_<n>_caption.md); no data-state words. The failure counts, the D92
    # actions, the matcher's status and the turn-limit note move to the header below (detail_txt), not lost.
    legend = (
        f"RLM (blue; one draw, n = {ans['G5']:,} answers) and the authors' RLM package (rlms 0.1.3, "
        f"vermilion; three draws, n = {ans['G6']:,} answers) answer the same 86 depth-sweep questions with "
        f"gemini-3-flash-preview at ten turn caps ({caps_txt}, on a logarithmic axis). Concept recall is the share of a "
        f"question's expected concepts that a concept matcher finds in the answer; a failed answer scores 0. "
        f"{A}, Concept recall (%) against turn cap. Small dots: each question's recall (for the package, the mean of "
        f"its three draws; n = 86 questions per system and cap), RLM left of the cap and the package right "
        f"of it. Line and large dot: the mean over the questions. Band: the two-sided 95% percentile interval of "
        f"that mean over 10,000 bootstrap resamples of the questions. "
        f"{B}, Share (%) of answers whose turns used reached the cap (for the package, the closing call is not "
        f"counted); n = {fn['b'][0]['answers']} answers per cap for RLM and "
        f"n = {fn['b'][len(caps)]['answers']} for the package.")
    detail_txt = (
        f"**Detail moved from the caption (23 October).** Scored with D12's loose concept matcher, provisional "
        f"until human labels choose the matcher (D17); no answer is judged. Answer key v2.4. Mentor::i's fixed "
        f"turn-limit note is removed before matching ({note} answers). Failed answers, scored 0: {fail['G5']} of "
        f"Mentor::i's {ans['G5']:,} and {fail['G6']} of the package's {ans['G6']:,}. Of the package's, "
        f"{act['rebuild']} (all {g6[1]['failed']} at cap 1 among them) will take the stored reply of their failed "
        f"closing call as the answer, {act['rerun']} will be run again, {act['stays_failed']} stay failed{none_txt}; "
        f"at cap 30, {c30['failed']} failed ({c30['failed_d92_rerun']} rerun, {c30['failed_d92_stays_failed']} stay "
        f"failed), at cap 50, {c50['failed']} ({c50['failed_d92_rerun']} rerun, {c50['failed_d92_stays_failed']} "
        f"stay failed). {nf_rerun} answers that did not fail will also be rerun. Equal values beyond a strip's width "
        f"overlap in a (Source Data give every value). The interval is not adjusted across caps; no hypothesis test. "
        f"Turns used: RLM, the turns its record counts; the package, its root calls.")
    lines = ["# Figure 3 panel draft (the two RLMs by turn cap), title and legend (draft)", "",
             "Written by `uv run --frozen python scripts/S475_fig3a_rlm_depth.py` from S474's L2 outputs "
             "(findings/recompute/L2/, committed e4823e1). A panel draft beside S459's provisional Figure 3 "
             "(findings/figures_provisional/fig3/), not a replacement of it.", "",
             f"Data stamp: {stamp}.", "",
             detail_txt, "",
             f"**Figure 3 | {title}.** {legend}", ""]
    cap = ["# Source Data Fig. 3, caption", "",
           (f"**Source Data Fig. 3 | Numerical values plotted in Figure 3 (panel draft, the two RLMs by turn cap).** "
            f"Provisional. Data stamp: {stamp}. One sheet per panel. Sheet Fig. 3a: one 'cap' row per system and "
            f"turn cap with the questions, answers, the mean concept recall (%), its 95% interval (%), the failed "
            f"answers (scored 0) and the failed answers by the action D92 gives them (rebuild, rerun, stays_failed) "
            f"or none, "
            f"and the answers that did not fail but are rerun; then one 'question' row per system, cap and question "
            f"with its value (%), the mean of its draws, and the draws. Sheet Fig. 3b: per system and cap, the "
            f"answers, the answers whose turns used reached the cap (count and %), and the answers whose stop "
            f"reason the cap caused (count and %). Generated by `uv run --frozen python "
            f"scripts/S475_fig3a_rlm_depth.py` from findings/recompute/L2/ (S474)."), "",
           f"Proposed Data Availability sentence: \"The source data for Figure {FIG_N} is in Supplementary Data {FIG_N + 1}.\"",   # D303 follow-up (D302)
           ""]
    return "\n".join(lines), "\n".join(cap)


# ---------------------------------------------------------------------------------------------------------------
def main(argv=None):
    # Retired by D123 (23 Oct): S476 draws Figure 3 into this script's folder, so a run here would delete S476's plate.
    # S476 imports reproduce, compute, per_question and the drawing constants from here; they stay as they are.
    raise SystemExit("S475 is retired (D123): scripts/S476_fig3_d123.py draws Figure 3; this module only lends it functions")
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        raise SystemExit("S475 takes no arguments")
    if FLOCK.get("status") != "agreed":
        raise SystemExit(f"{rel(FIGURE_LOCK)} has status {FLOCK.get('status')!r}, not 'agreed' (D87): no plate")
    for s in SYSTEMS.values():
        if s["colour"] not in _CAT:
            raise SystemExit(f"{s['colour']} is not in [colour] categorical")
    header = json.loads(HEADER_F.read_text())
    tables = json.loads(TABLES_F.read_text())
    rows = [json.loads(x) for x in ROWS_F.read_text().splitlines() if x.strip()]
    if header.get("script") != "scripts/S474_l2_concept_recall.py" or header.get("provisional") is not True:
        raise SystemExit(f"{rel(HEADER_F)} is not S474's provisional L2 header")
    caps = tuple(header["caps"])
    want_n = {s: header["counts"][s]["rows"] for s in SYSTEMS}
    got_n = Counter(r["system"] for r in rows)
    if dict(got_n) != want_n:
        raise SystemExit(f"{rel(ROWS_F)} holds {dict(got_n)} rows, header.json {want_n}")
    ids, design_caps, _, _ = S459.design_constants()
    if tuple(design_caps) != caps or set(ids) != {r["question_id"] for r in rows}:
        raise SystemExit("S474's caps or questions are not run_rlm_ref.py's DEPTH_SWEEP86 and caps")
    reproduced, qorder = reproduce(rows, tables, caps)
    plan = S459.planned_total(ids, caps)
    n = len(rows)
    N = plan["G4"] + plan["G5"] + want_n["G6"]
    stamp = (f"PROVISIONAL: {n:,} of {N:,} answers, RLM (G5, draw 1, {want_n['G5']:,}) and the RLM authors' "
             f"package (G6, three draws, {want_n['G6']:,}) at {len(caps)} turn caps, concept recall on D12's loose "
             f"matcher (S474, L2 of {header.get('written_utc', 'frozen inputs (D155)')}), no judge; G6 before the D92 reruns")
    tag = f" (provisional, {n} of {N})"
    fn = compute(rows, tables, caps, qorder)
    legend, cap = legend_and_caption(fn, tables, header, caps, stamp, n, N)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in list(OUT.glob("Figure 3*")) + list(OUT.glob("Source Data Fig. 3*")):
        old.unlink()
    paths = {x: OUT / f"Figure 3{tag}.{x}" for x in ("pdf", "svg", "png")}
    W, H, printed, readback, overlaps = draw_figure(fn, caps, paths)
    bad, n_checked = check_drawn(readback)
    sheets = sheets_of(fn)
    sd = OUT / f"Source Data Fig. 3{tag}.xlsx"
    write_source_data(sheets, sd)
    numbers = OUT / "figure3_numbers.json"
    numbers.write_text(json.dumps({"stamp": stamp, "what": "every number the plate draws, sheet by sheet as Source "
                                   "Data Fig. 3 holds them (S448 R8 compares the workbook with this file)",
                                   "sheets": {nm: {"columns": cols, "rows": rws} for nm, cols, rws in sheets},
                                   "printed": printed,
                                   "printed_what": "every number printed on the plate: the SVG group id of its text, "
                                                   "and the Source Data sheet, row and format it is written from"},
                                  indent=1, default=str) + "\n")
    (OUT / "legend_draft.md").write_text(legend)
    capf = OUT / f"Source Data Fig. 3 caption{tag}.md"
    capf.write_text(cap)
    inputs = {rel(p): sha256_file(p) for p in (ROWS_F, TABLES_F, HEADER_F, S474_F, FIGURE_LOCK,
                                               ROOT / "experiments" / "rlm_ref" / "run_rlm_ref.py",
                                               S459.G4_README, S459.G5_README, S459.D98_SUBSET)}
    prov = {"script": rel(Path(__file__)), "script_sha256": sha256_file(Path(__file__)),
            "command": "uv run --frozen python scripts/S475_fig3a_rlm_depth.py",
            "python": platform.python_version(),
            "written_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "repo_head": git("rev-parse", "--short", "HEAD"),
            "script_dirty_vs_head": git("status", "--short", "--", rel(Path(__file__))),
            "inputs_sha256": inputs, "model_calls": 0, "stamp": stamp, "page_mm": [W, H],
            "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK), "status": FLOCK["status"]},
            "s474_header": {"written_utc": header.get("written_utc"), "script_sha256": header["script_sha256"],
                            "matcher": header["matcher"], "gate": header["gate"]["reproduced"]},
            "reproduced": reproduced, "planned_answers": {**plan, "G6 depth caps": want_n["G6"], "N": N},
            "drawn_check": f"check_drawn(): {n_checked} drawn values equal their Source Data"
                           + ("" if not bad else " | FAILED: " + "; ".join(bad[:5])),
            "dot_overlaps": {"what": "dots per strip that found no free slot within the strip (S457.swarm) and "
                                     "overlap another", "total": sum(overlaps.values()), "by_strip": overlaps},
            "panels": {"a": "concept recall (%) by cap: mean over 86 questions (line, large dot), 95% percentile "
                            "interval (band), one small dot per question; G5 left of the cap, G6 right",
                       "b": "share (%) of answers whose turns used reached the cap (S474 cap_reached)"},
            "colours": {s: v["colour"] for s, v in SYSTEMS.items()}, "font": FONT,
            "type_pt": {"panel letters": PT_LETTER, "all other text": PT},
            "files": {p.name: sha256_file(p) for p in [*paths.values(), sd, capf, numbers, OUT / "legend_draft.md"]}}
    (OUT / "figure3_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    if bad:
        for p in [*paths.values(), sd, capf, numbers, OUT / "legend_draft.md", OUT / "figure3_provenance.json"]:
            p.unlink(missing_ok=True)
        print("check_drawn FAILED, nothing kept: " + "; ".join(bad[:5]), file=sys.stderr)
        sys.exit(1)
    print(stamp)
    print(f"reproduced: {reproduced['compared']} values of cap_tables.json recomputed from concept_recall.jsonl, "
          f"all equal (anchors G5 cap 20 = 76.8%, G6 cap 50 = 65.9%)")
    print(f"check_drawn: {n_checked} drawn values equal their Source Data; dots overlapping: "
          f"{sum(overlaps.values())} of {sum(1 for r in fn['a'] if r['row'] == 'question')}")
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W:.0f} x {H:.1f} mm), {sd.name}, {capf.name}, "
          f"figure3_numbers.json, legend_draft.md, figure3_provenance.json into {rel(OUT)}")


if __name__ == "__main__":
    main()
