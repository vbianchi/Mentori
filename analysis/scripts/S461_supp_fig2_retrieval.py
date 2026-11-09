#!/usr/bin/env python3
"""S461 - Supplementary Figure 2 (retrieval pipeline selection) redrawn under experiments/FIGURE_LOCK.toml.

WHY. experiments/LIST.md (Indexing, Supplementary Figure 2) keeps this figure as it is, with no run: 28 retrieval
queries of their own, no language model, the deposit's four sweeps of February 2026. Only the plate must change:
scripts/S295_supp_ED1.R draws 6.5 to 7.5 pt type and major gridlines (S295:98-104), against FIGURE_LOCK [type]
font_min_pt and [lines] gridlines. This script draws the same four panels from the same four records, with every
figure rule from the lock, and writes the plate (PDF, SVG, PNG rasterised from the PDF) that S448 checks, a data
workbook and its caption (the numbers drawn, one sheet per panel), supplementary_figure2_numbers.json (every number
drawn, and every number printed tied to its workbook cell), supplementary_figure2_provenance.json (input and output
sha256, the figure lock's sha256) and legend_draft.md (a draft).

ONE COMMAND (D155), from the repository root, rebuilds the committed plate from the frozen deposit records:

    uv run --frozen python scripts/S461_supp_fig2_retrieval.py [--out <dir>]

    uv run --frozen python scripts/S448_figure_rules_check.py --figure 2 --supplementary \
        --dir findings/figures_provisional/supp_fig2

It writes every file of findings/figures_provisional/supp_fig2/ (or of --out) byte-equal to the committed one
(26 October: PDF, SVG, PNG, workbook, caption, legend, numbers and provenance; run twice, the same bytes).

NAMING (D92 Q194). The plate is named by FIGURE_LOCK [files] supplementary_name, "Supplementary Figure 2
(provisional, ...)" (scripts/si_names.tsv, row ED1), so no file here shares a name with main Figure 2's; the data
workbook is "Supplementary Figure 2 data (...)", since Source Data is a main-figure rule (editor row 20); S448
--supplementary holds a Supplementary figure to the drawing rules and to R8's consistency parts (2) to (6) on that
workbook, not to the Source Data paperwork of R8's part (1) (D94 O-b).

REPRODUCE BEFORE WRITING (README.md:75-79). Nothing is written unless (1) every result row's overall MRR equals the
mean of its per-query MRRs and its per-query count equals its n_queries, (2) the rows are exactly the grid each
record's config declares, once each, and (3) the values S295 printed on the committed plate are regenerated: the
chunking means and the scalability values, read from manuscript/submission/supplementary/Supplementary_Figure_2.pdf
(sha256 922dd598, commit b143bf2) on 17 October 2026 and held here as REF_C and REF_D. D2 (8 Nov): the build does not
open that PDF; scripts/S616_figure_editorial.py check stops when it changes and asks for a re-read.

No model call. Reads the deposit's five records from their frozen copy (D155), findings/recompute/upstream_inputs/
publication/results/ (fig_repro.frozen; each file checked against frozen_inputs/SHA256SUMS, whose lines equal
data/upstream/MANIFEST.sha256's), never from the sibling checkout scripts/machine.py finds; before anything is written,
each must have the sha256 the committed provenance records for it. The command re-executes itself under
PYTHONHASHSEED=0 (fig_repro.pin_hash_seed): on 26 October this plate's PDF came out in two versions, by the seed
Python drew, in one embedded font subset's AAT 'prop' table (fontTools' subsetter orders it by string hashes); seed 0
gives the committed one.
"""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import house_style as hs  # noqa: E402  one drawing style for every plate
from S457_fig2_panels import finish_plate  # noqa: E402  the last step of a plate, shared (S457, S463, S472)
import machine  # noqa: E402  the deposit's location, as every script finds it (rel() only, since D155)
import fig_repro as FR  # noqa: E402  (D155: frozen inputs, deterministic files)

OUT = ROOT / "findings" / "figures_provisional" / "supp_fig2"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
LOCK = ROOT / "experiments" / "LOCK.toml"
N = 2                                              # the number S448's --figure and the lock's names carry
REF_PDF = ROOT / "manuscript" / "submission" / "supplementary" / "Supplementary_Figure_2.pdf"
REF_PDF_SHA = "922dd598ad200705de8bda465db1a0794cde9644132e56adfc850ed27f2e4140"
# What S295 printed on that plate (its PDF text, read 17 October 2026): panel c's mean per chunking configuration and
# panel d's value per corpus size, two decimals, rounded half up
REF_C = {"Semantic 2000 char": "0.80", "Semantic 4000 char": "0.80", "Semantic 500 char": "0.81",
         "Semantic 1000 char": "0.83", "Simple 128 tok": "0.92", "Simple 256 tok": "0.96", "Simple 1024 tok": "0.97",
         "Simple 512 tok (baseline)": "0.99"}
REF_D = {5: "1.00", 10: "1.00", 20: "1.00", 50: "0.94", 100: "0.88"}
FILES = {"a": "exp01_embedding_latest.json", "b": "exp02_search_latest.json", "c": "exp03a_chunking_latest.json",
         "d": "exp03b_scalability_latest.json"}
# The deposit's question-answering record: its question ids are read only to check that the retrieval queries are not
# among them (experiments/LIST.md, Indexing: "not the ... benchmark", stated in the legend)
QA_FILE = "exp04_generation_latest.json"
ANSWER_KEYS = ("answer", "generation", "response", "judge_scores")   # a per-query field of a generated, judged answer

FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
SI_LABEL = FLOCK["files"]["supplementary_name"].format(n=N)    # "Supplementary Figure 2" (D92 Q194); the plate's name
SIDE = f"supplementary_figure{N}"                  # the numbers and provenance files S448 --supplementary reads
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
assert len(_CAT) == 8, "[colour] categorical: S461 names Okabe and Ito's eight"
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
GREY = "#999999"                                   # Okabe-Ito's grey, a grey under [colour] grey_tol (leaders only)
PT = float(FLOCK["type"]["font_min_pt"])            # every text at the floor: one size ([type] size_variance)
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper
FONT = FLOCK["type"]["font_families"][0]
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])
W_MM = float(FLOCK["page"]["width_double_mm"])
H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
MM_PER_PT = 25.4 / 72


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fix_workbook(p: Path) -> None:
    """The same cells give the same bytes: openpyxl writes the save time into docProps/core.xml (dcterms:created,
    dcterms:modified; openpyxl/writer/excel.py sets modified on every save) and into every zip member's date. Both
    are removed or fixed here, so the sha256 the provenance records holds for any later run on the same records."""
    import re
    import zipfile
    members = []
    with zipfile.ZipFile(p) as z:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = re.sub(rb"<dcterms:(created|modified)\b[^>]*>[^<]*</dcterms:\1>", b"", data)
            members.append((info, data))
    with zipfile.ZipFile(p, "w") as z:
        for info, data in members:
            zi = zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = info.external_attr
            z.writestr(zi, data)


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def half_up(x, nd=2) -> str:
    """A printed number, rounded once: to 1e-9, then half away from zero (S447's and S448's rule)."""
    q = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f"{abs(q) if q == 0 else q:.{nd}f}"


def floor_to(v, step) -> float:
    """The largest multiple of step at or below v (decimal, so 0.4 stays 0.4)."""
    s = Decimal(str(step))
    return float((Decimal(repr(round(float(v), 9))) / s).to_integral_value(rounding="ROUND_FLOOR") * s)


def ticks(lo, hi, step):
    s = Decimal(str(step))
    n = int(((Decimal(str(hi)) - Decimal(str(lo))) / s).to_integral_value(rounding=ROUND_HALF_UP))
    return [float(Decimal(str(lo)) + k * s) for k in range(n + 1)]


def letter(x):
    return LETTER_CASE(x)


def sheet(x):
    return f"Supplementary Fig. {N}{letter(x)}"


# ---------------------------------------------------------------------------------------------------------------
def load():
    res = FR.check_committed(FR.frozen("upstream", "publication/results"))     # D155: the frozen deposit records
    paths = {k: res / v for k, v in FILES.items()}
    missing = [str(p) for p in paths.values() if not p.exists()]
    paths["qa"] = res / QA_FILE
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise SystemExit(f"deposit records missing: {missing}")
    recs = {k: json.loads(p.read_text()) for k, p in paths.items() if k != "qa"}
    qa_ids = {r["question_id"] for r in json.loads(paths["qa"].read_text())["per_question_results"]}
    return paths, recs, qa_ids


def reproduce(recs, qa_ids):
    """The gate (module docstring). Returns its report; stops (exit 2) on any failure, before anything is written.
    Also checks the two facts the legend states about the queries: no retrieval query id is a question id of the
    deposit's question-answering record, and no per-query row carries a generated or judged answer."""
    probs, rows = [], 0
    ret_ids = set()
    for k, d in recs.items():
        for r in d["results"]:
            rows += 1
            ret_ids |= {q["id"] for q in r["per_query"]}
            answered = sorted({x for q in r["per_query"] for x in ANSWER_KEYS if x in q})
            if answered:
                probs.append(f"{FILES[k]}: a per-query row carries {answered}; the legend says no answer is generated")
            pq = [q["MRR"] for q in r["per_query"]]
            if len(pq) != r["n_queries"]:
                probs.append(f"{FILES[k]}: {len(pq)} per-query rows, n_queries {r['n_queries']}")
            if abs(statistics.fmean(pq) - r["overall"]["MRR"]) > 1e-12:
                probs.append(f"{FILES[k]}: overall MRR {r['overall']['MRR']} is not the per-query mean")
    shared = sorted(ret_ids & qa_ids)
    if shared:
        probs.append(f"{len(shared)} retrieval query ids are question ids of {QA_FILE} ({shared[:5]}); the legend "
                     f"says the queries are not the benchmark's")
    a, b, c, d = (recs[x] for x in "abcd")
    grids = {"a": ({(m, s) for m in a["config"]["models"] for s in a["config"]["corpus_sizes"]},
                   [(r["model"], r["corpus_size"]) for r in a["results"]]),
             "b": ({(m, s) for m in b["config"]["configs_tested"] for s in b["config"]["corpus_sizes"]},
                   [(r["config"], r["corpus_size"]) for r in b["results"]]),
             "c": ({(u, m) for u in c["config"]["runs"] for m in c["config"]["configs_tested"]},
                   [(r["run"], r["config"]) for r in c["results"]]),
             "d": ({s for s in d["config"]["corpus_sizes"]}, [r["corpus_size"] for r in d["results"]])}
    planned = 0
    for k, (want, got) in grids.items():
        planned += len(want)
        if sorted(map(str, got)) != sorted(map(str, want)):
            probs.append(f"{FILES[k]}: rows are not the config's grid once each")
    # D2 (Valerio, 8 Nov): the submitted PDF is a document, not data: the build compares with REF_C and REF_D, the
    # values read from it, and S616 check (an editorial step, not shipped) holds the PDF to REF_PDF_SHA
    means = {}
    for r in c["results"]:
        means.setdefault(r["config_label"], []).append(r["overall"]["MRR"])
    got_c = {k: half_up(statistics.fmean(v)) for k, v in means.items()}
    got_d = {r["corpus_size"]: half_up(r["overall"]["MRR"]) for r in d["results"]}
    if got_c != REF_C:
        probs.append(f"panel c means {got_c} differ from S295's plate {REF_C}")
    if got_d != REF_D:
        probs.append(f"panel d values {got_d} differ from S295's plate {REF_D}")
    if probs:
        print("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs), file=sys.stderr)
        sys.exit(2)
    return {"rows": rows, "planned": planned,
            "checks": [f"{rows} result rows: overall MRR equals the mean of the per-query MRRs, per-query count "
                       f"equals n_queries", f"rows equal each record's config grid once each ({planned} planned)",
                       f"{len(ret_ids)} retrieval query ids, none among the {len(qa_ids)} question ids of {QA_FILE}; "
                       f"no per-query row carries {', '.join(ANSWER_KEYS)}",
                       f"S295's printed values regenerated: {len(REF_C)} chunking means and {len(REF_D)} "
                       f"scalability values, against the values read from {REF_PDF.relative_to(ROOT)} sha256 "
                       f"{REF_PDF_SHA[:16]} (REF_C, REF_D; S616 check holds the PDF to that sha256)"]}


def run_numbers(results) -> dict:
    """The repeated runs of the chunking sweep, numbered 1, 2, 3 in the record's order (Valerio, 2 November: Run 1, Run 2,
    Run 3 on the plate and in the legend). The record's letters A, B, C stay in the sheet's `run` column."""
    return {u: i for i, u in enumerate(dict.fromkeys(r["run"] for r in results), 1)}


def tables(recs):
    """The data workbook's sheets, one per panel, as (columns, rows): exactly what is drawn."""
    a, b, c, d = (recs[x]["results"] for x in "abcd")
    A = [{"model": r["model"], "corpus_size_papers": r["corpus_size"], "n_queries": r["n_queries"],
          "mrr": r["overall"]["MRR"]} for r in a]
    B = [{"config": r["config"], "strategy": r["config_label"], "corpus_size_papers": r["corpus_size"],
          "n_queries": r["n_queries"], "mrr": r["overall"]["MRR"]} for r in b]
    by_cfg = {}
    for r in c:
        by_cfg.setdefault(r["config"], []).append(r["overall"]["MRR"])
    run_no = run_numbers(c)
    C = [{"config": r["config"], "configuration": r["config_label"], "run": r["run"], "n_queries": r["n_queries"],
          "mrr": r["overall"]["MRR"], "mean_mrr_over_runs": statistics.fmean(by_cfg[r["config"]]),
          "n_runs": len(by_cfg[r["config"]]), "run_number": run_no[r["run"]]} for r in c]
    D = [{"corpus_size_papers": r["corpus_size"], "index_name": r["index_name"], "n_queries": r["n_queries"],
          "mrr": r["overall"]["MRR"]} for r in d]
    out = {}
    for k, rows in zip("abcd", (A, B, C, D)):
        cols = list(rows[0])
        out[k] = (cols, [[r[x] for x in cols] for r in rows])
    return out


# ---------------------------------------------------------------------------------------------------------------
def draw(tab, paths):
    """The plate: [page] width_double_mm wide, under height_max_mm; every text [type] font_min_pt in FONT, panel letters
    panel_letter_pt bold; no gridlines, no titles, nothing but the figure. Panels a, b in the first row, c, d in the
    second. Every text holding a number or a name from a record carries an id (s448num_<k>) in printed: its workbook
    sheet, row and format (S448 R8 (6))."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    from matplotlib.lines import Line2D
    from matplotlib.text import Text
    from matplotlib.textpath import TextToPath
    from matplotlib.transforms import ScaledTranslation, blended_transform_factory

    lw_axis = max(0.5, LINE_MIN_PT)
    lw_data = hs.LW["series"]                      # style_1028: a data line that is the result, 1.0 pt
    lw_lead = hs.LW["connector"]                   # leaders 0.5 pt grey
    plt.rcParams.update(hs.rc("S461"))             # style_1028: the house settings, then S461's pads
    plt.rcParams.update({"font.family": FONT, "font.size": PT, "svg.fonttype": "none", "pdf.fonttype": 42,
                         "axes.linewidth": lw_axis, "xtick.major.width": lw_axis, "ytick.major.width": lw_axis,
                         "xtick.major.size": 2, "ytick.major.size": 2, "xtick.major.pad": 2, "ytick.major.pad": 2,
                         "xtick.labelsize": PT, "ytick.labelsize": PT, "axes.labelsize": PT, "axes.labelpad": 2,
                         "axes.edgecolor": "#000000", "xtick.color": "#000000", "ytick.color": "#000000",
                         "text.color": "#000000", "axes.labelcolor": "#000000", "axes.grid": False,
                         "lines.markeredgewidth": max(0.5, LINE_MIN_PT), "svg.hashsalt": "S461"})
    t2p = TextToPath()

    def tw(s, bold=False):
        fp = FontProperties(family=FONT, size=PT, weight="bold" if bold else "normal")
        return max(t2p.get_text_width_height_descent(x, fp, ismath=False)[0] for x in s.split("\n")) * MM_PER_PT

    LINE = PT * MM_PER_PT * 1.2                    # one text line (mm)
    TICKLAB = 2 * MM_PER_PT + 2 * MM_PER_PT + LINE  # tick, pad, label
    XAX = TICKLAB + 2 * MM_PER_PT + LINE + 0.6     # an x axis with its title
    HEAD = PT_LETTER * MM_PER_PT * 1.6             # room for a panel letter above an axes
    printed = {}

    def tie(artist, sheet_letter, row, fmt):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = {"sheet": sheet(sheet_letter), "row": row, "format": fmt}

    cols = {k: v[0] for k, v in tab.items()}
    rows = {k: [dict(zip(v[0], r)) for r in v[1]] for k, v in tab.items()}

    # ---- measures (mm, from the page's top left)
    COLW = W_MM / 2
    yt_ab = max(tw("0.40"), tw("1.00"))
    left_ab = LINE + 2 * MM_PER_PT + yt_ab + 4 * MM_PER_PT + 0.8   # y title, pad, tick labels, tick + pad
    lab_a = max(tw(r["model"]) for r in rows["a"]) + 3.2
    hyb = sorted({r["strategy"] for r in rows["b"]})
    lab_b = max([tw(s) for s in hyb] + [tw(s + " and") for s in hyb]) + 3.2
    ax_a = (left_ab, COLW - lab_a - left_ab)
    ax_b = (COLW + left_ab, W_MM - lab_b - (COLW + left_ab) - 0.3)
    yt_c = max(tw(r["configuration"]) for r in rows["c"]) + 4 * MM_PER_PT + 0.8
    MEAN_GAP = 3.0                                 # c: a run marker at 1.00 keeps clear of the printed mean
    mean_w = tw("0.00") + MEAN_GAP + 0.3
    ax_c = (yt_c + 0.3, COLW - mean_w - yt_c - 0.3 - 2.0)
    yt_d = LINE + 2 * MM_PER_PT + tw("1.00") + 4 * MM_PER_PT + 0.8
    ax_d = (COLW + yt_d, W_MM - (COLW + yt_d) - 3.0)
    ROW1, ROW2 = 54.0, 50.0
    top1 = HEAD
    y_key = top1 + ROW1 + XAX + 3.0 + PT_LETTER * MM_PER_PT + 0.8   # row 2: panel letters and keys on this line
    top2 = y_key + 7.5                             # then the row of printed values, then the axes
    runs_c = list(dict.fromkeys(r["run"] for r in rows["c"]))
    MS_HOUSE = hs.MARK_MM / MM_PER_PT              # a categorical mark, 1.25 mm
    H = top2 + ROW2 + XAX + 0.8
    if H > H_MAX_MM:
        raise SystemExit(f"the plate would be {H:.1f} mm high; FIGURE_LOCK [page] height_max_mm is {H_MAX_MM}")

    fig = plt.figure(figsize=(W_MM / 25.4, H / 25.4))
    fig.patch.set_facecolor("#FFFFFF")
    fig._hs_mm = (W_MM, H)

    def axes(x0, w, top, h, spines=True):
        ax = fig.add_axes([x0 / W_MM, 1 - (top + h) / H, w / W_MM, h / H])
        ax.spines[["top", "right"]].set_visible(False)
        if not spines:
            ax.spines[["left", "bottom"]].set_visible(False)
        ax.tick_params(direction="out")
        ax.grid(False)
        return ax

    def panel_letter(ax, x):
        bb = ax.get_position()
        fig.text(0.6 / W_MM if bb.x0 < 0.5 else (COLW + 0.6) / W_MM, bb.y1 + (HEAD - PT_LETTER * MM_PER_PT) / H,
                 letter(x), fontsize=PT_LETTER, fontweight=LETTER_WEIGHT, va="bottom", ha="left")

    def spread(vals, heights, lo, hi, gap):
        """Label centres near their values, in value order, never closer than their half heights plus gap, inside
        lo..hi (data units)."""
        order = sorted(range(len(vals)), key=lambda i: -vals[i])
        y = {}
        prev = None
        for i in order:
            y[i] = min(vals[i], hi - heights[i] / 2) if prev is None else \
                min(vals[i], y[prev] - (heights[prev] + heights[i]) / 2 - gap)
            prev = i
        nxt = None
        for i in reversed(order):
            if nxt is None:
                y[i] = max(y[i], lo + heights[i] / 2)
            else:
                y[i] = max(y[i], y[nxt] + (heights[nxt] + heights[i]) / 2 + gap)
            nxt = i
        return [y[i] for i in range(len(vals))]

    def direct_labels(ax, ends, h_mm, lead_x_end):
        """ends: [(series key, last x, last y, [(text, sheet, row, format)], colour)] at the right of the axes, a
        leader from each line's last point to its label."""
        lo, hi = ax.get_ylim()
        unit = (hi - lo) / h_mm
        heights = [len(e[3]) * LINE * unit for e in ends]
        ys = spread([e[2] for e in ends], heights, lo, hi + 0.3 * LINE * unit, 0.15 * LINE * unit)
        tr = blended_transform_factory(ax.transAxes, ax.transData)
        x_lab = 1.0 + 2.6 / ax_w_mm[id(ax)]
        for (key, x_last, y_last, lines, col), yc, hh in zip(ends, ys, heights):
            ax.add_line(Line2D([x_last, lead_x_end], [y_last, y_last], lw=lw_lead, color=GREY, clip_on=False,
                               transform=ax.transData, zorder=1))
            ax.add_line(Line2D([1.0 + 0.4 / ax_w_mm[id(ax)], x_lab - 0.3 / ax_w_mm[id(ax)]], [y_last, yc],
                               lw=lw_lead, color=GREY, clip_on=False, transform=tr, zorder=1))
            for j, (txt, sl, rw, fmt) in enumerate(lines):
                yy = yc + hh / 2 - (j + 0.5) * LINE * unit
                t = ax.text(x_lab, yy, txt, transform=tr, ha="left", va="center", fontsize=PT, clip_on=False)
                tie(t, sl, rw, fmt)

    ax_w_mm = {}
    sizes_ab = sorted({r["corpus_size_papers"] for r in rows["a"]})
    xi = {s: i for i, s in enumerate(sizes_ab)}
    SHAPES_A = [m for _, m in hs.SERIES_ORDER]    # style_1028: SERIES_ORDER's shapes, with its colours
    data_marks = []                                # (axes, Line2D): every data point, checked against the axes below

    from matplotlib.markers import MarkerStyle

    def half_extent(marker):
        """How far a marker of size 1 reaches from its centre ('D' reaches 0.71, 'o' 0.5)."""
        ms_ = MarkerStyle(marker)
        return float(np.abs(ms_.get_transform().transform(ms_.get_path().vertices)).max())

    def diam_mm(ms, markers=("o",)):
        return (2 * max(half_extent(m) * hs.MARKER_SCALE.get(m, 1.0) for m in markers) * ms +
                plt.rcParams["lines.markeredgewidth"]) * MM_PER_PT   # style_1028: each mark at its drawn size

    # a, b: the corpus-size axis runs from -X_MARGIN to the last size + X_MARGIN, wide enough that the outermost
    # point of a group (series set apart by one marker plus 0.3 mm) clears the y axis line by 0.5 mm: with A the
    # group's half width plus a marker's half and 0.5 mm, X_MARGIN * unit >= A, unit = w / (sizes - 1 + 2 X_MARGIN)
    def need_mm(ms, k, markers):
        return (k - 1) / 2 * (diam_mm(ms, markers) + 0.3) + diam_mm(ms, markers) / 2 + 0.5

    n_series_b = len({tuple(f"{r['mrr']:.12f}" for r in sorted((r for r in rows["b"] if r["config"] == s),
                                                                key=lambda r: r["corpus_size_papers"]))
                      for s in dict.fromkeys(r["config"] for r in rows["b"])})
    n_models_a = len({r["model"] for r in rows["a"]})
    X_MARGIN = 0.35
    for ms_, k_, mk_, w_ in ((MS_HOUSE, n_models_a, tuple(SHAPES_A[:n_models_a]), ax_a[1]),
                             (hs.DOT_SPARSE_MM / MM_PER_PT, n_series_b, tuple(SHAPES_A[:n_series_b]), ax_b[1])):
        A_ = need_mm(ms_, k_, mk_)
        X_MARGIN = max(X_MARGIN, A_ * (len(sizes_ab) - 1) / (w_ - 2 * A_))

    def x_step(ms, w_mm, markers=("o",)):
        """a, b: the offset between neighbouring series at one corpus size, in axis units: one marker plus 0.3 mm,
        so points with the same value sit side by side, never on one another."""
        return (diam_mm(ms, markers) + 0.3) / (w_mm / (len(sizes_ab) - 1 + 2 * X_MARGIN))

    def value_floor(vmin, step, ms, axis_mm, cap, markers=("o",)):
        """The value axis's lower end: a multiple of step, at most cap, under the lowest value by at least half a
        marker, the axis line's half width and 0.3 mm, so no point sits on the axis line."""
        span = 1.0 - floor_to(vmin, step) + step
        pad = (diam_mm(ms, markers) / 2 + lw_axis / 2 * MM_PER_PT + 0.3) / axis_mm * span
        return min(cap, floor_to(vmin - pad, step))

    # ---- a: embedding models, one neutral ink, a point shape per model, labelled at the largest corpus
    ax = axes(ax_a[0], ax_a[1], top1, ROW1)
    ax_w_mm[id(ax)] = ax_a[1]
    models = list(dict.fromkeys(r["model"] for r in rows["a"]))
    last = {m: max((r for r in rows["a"] if r["model"] == m), key=lambda r: r["corpus_size_papers"]) for m in models}
    models.sort(key=lambda m: -last[m]["mrr"])
    shapes = dict(zip(models, SHAPES_A))
    MS_A = MS_HOUSE
    col_a = {m: hs.SERIES_ORDER[i][0] for i, m in enumerate(models)}
    step_a = x_step(MS_A, ax_a[1], tuple(shapes.values()))
    off_a = {m: (i - (len(models) - 1) / 2) * step_a for i, m in enumerate(models)}
    lo_a = value_floor(min(r["mrr"] for r in rows["a"]), 0.1, MS_A, ROW1, 0.4, tuple(shapes.values()))
    ax.set_ylim(lo_a, 1.0)
    ax.set_yticks(ticks(lo_a, 1.0, 0.1))
    ax.set_yticklabels([f"{v:.1f}" for v in ticks(lo_a, 1.0, 0.1)])
    ends = []
    for m in models:
        rr = sorted((r for r in rows["a"] if r["model"] == m), key=lambda r: r["corpus_size_papers"])
        xs = [xi[r["corpus_size_papers"]] + off_a[m] for r in rr]
        ln = ax.plot(xs, [r["mrr"] for r in rr], color=col_a[m], lw=lw_data, marker=shapes[m],
                     ms=MS_A * hs.MARKER_SCALE.get(shapes[m], 1.0), mfc=col_a[m], mec="#FFFFFF", mew=0.3, zorder=3,
                     clip_on=False)[0]
        data_marks.append((ax, ln))
        ri = rows["a"].index(last[m])
        ends.append((m, xs[-1], last[m]["mrr"], [(m, "a", ri, "{model}")], "#000000"))
    ax.set_xlim(-X_MARGIN, len(sizes_ab) - 1 + X_MARGIN)
    ax.set_xticks(range(len(sizes_ab)))
    ax.set_xticklabels([str(s) for s in sizes_ab])
    ax.set_xlabel("Corpus size (papers)")
    ax.set_ylabel("Mean reciprocal rank")
    direct_labels(ax, ends, ROW1, len(sizes_ab) - 1 + X_MARGIN)
    panel_letter(ax, "a")

    # ---- b: search strategies; strategies with the same value at every size are one series under one label
    ax = axes(ax_b[0], ax_b[1], top1, ROW1)
    ax_w_mm[id(ax)] = ax_b[1]
    strategies = list(dict.fromkeys(r["config"] for r in rows["b"]))
    sig = {s: tuple(f"{r['mrr']:.12f}" for r in sorted((r for r in rows["b"] if r["config"] == s),
                                                        key=lambda r: r["corpus_size_papers"])) for s in strategies}
    series = {}
    for s in strategies:
        series.setdefault(sig[s], []).append(s)
    ser = list(series.values())
    lastb = lambda grp: max((r for r in rows["b"] if r["config"] == grp[0]), key=lambda r: r["corpus_size_papers"])
    ser.sort(key=lambda g: -lastb(g)["mrr"])
    colours = [c for c, _ in hs.SERIES_ORDER]     # style_1028: SERIES_ORDER, colour and shape together
    shapes_b = [m for _, m in hs.SERIES_ORDER]
    if len(ser) > len(colours):
        raise SystemExit(f"panel b has {len(ser)} series and {len(colours)} colours")
    MS_B = hs.DOT_SPARSE_MM / MM_PER_PT            # style_1028: 1.0 mm, six series must sit side by side in one slot
    step_b = x_step(MS_B, ax_b[1], tuple(shapes_b[:len(ser)]))
    # style_1028: neighbours set apart by their own two half widths plus 0.3 mm (house marks differ in size)
    r_b = [(half_extent(shapes_b[i]) * hs.MARKER_SCALE.get(shapes_b[i], 1.0) * MS_B + 0.15) * MM_PER_PT
           for i in range(len(ser))]
    unit_b = ax_b[1] / (len(sizes_ab) - 1 + 2 * X_MARGIN)
    cum = [0.0]
    for i in range(1, len(ser)):
        cum.append(cum[-1] + r_b[i - 1] + r_b[i] + 0.3)
    off_b = {i: (cum[i] - cum[-1] / 2) / unit_b for i in range(len(ser))}
    lo_b = value_floor(min(r["mrr"] for r in rows["b"]), 0.02, MS_B, ROW1, 0.90, tuple(shapes_b[:len(ser)]))
    ax.set_ylim(lo_b, 1.003)
    ax.set_yticks(ticks(lo_b, 1.0, 0.02))
    ax.set_yticklabels([f"{v:.2f}" for v in ticks(lo_b, 1.0, 0.02)])
    ends = []
    for i, grp in enumerate(ser):
        rr = sorted((r for r in rows["b"] if r["config"] == grp[0]), key=lambda r: r["corpus_size_papers"])
        xs = [xi[r["corpus_size_papers"]] + off_b[i] for r in rr]
        ln = ax.plot(xs, [r["mrr"] for r in rr], color=colours[i], lw=lw_data, marker=shapes_b[i],
                     ms=MS_B * hs.MARKER_SCALE.get(shapes_b[i], 1.0), mfc=colours[i], mec="#FFFFFF", mew=0.3,
                     zorder=3, clip_on=False)[0]
        data_marks.append((ax, ln))
        labs = sorted(grp, key=lambda s: next(r["strategy"] for r in rows["b"] if r["config"] == s))
        lines = []
        for j, s in enumerate(labs):
            ri = next(k for k, r in enumerate(rows["b"]) if r["config"] == s)
            lines.append((rows["b"][ri]["strategy"] + (" and" if j < len(labs) - 1 else ""), "b", ri,
                          "{strategy}" + (" and" if j < len(labs) - 1 else "")))
        ends.append((tuple(grp), xs[-1], lastb(grp)["mrr"], lines, colours[i]))
    ax.set_xlim(-X_MARGIN, len(sizes_ab) - 1 + X_MARGIN)
    ax.set_xticks(range(len(sizes_ab)))
    ax.set_xticklabels([str(s) for s in sizes_ab])
    ax.set_xlabel("Corpus size (papers)")
    ax.set_ylabel("Mean reciprocal rank")
    direct_labels(ax, ends, ROW1, len(sizes_ab) - 1 + X_MARGIN)
    panel_letter(ax, "b")

    # ---- c and d: Valerio's pick of 28 October (supp2 alt_A): c as tiles, d with sizes evenly spaced
    BLUE, MK = hs.SERIES_ORDER[0]                  # RRF and bge-m3: the series a and b draw first (blue circle)
    run_shape = dict(zip(runs_c, ["o", "^", "s"]))
    cfgs = list(dict.fromkeys(r["config"] for r in rows["c"]))
    mean_of = {c: next(r["mean_mrr_over_runs"] for r in rows["c"] if r["config"] == c) for c in cfgs}
    first_of = {c: next(k for k, r in enumerate(rows["c"]) if r["config"] == c) for c in cfgs}
    label_of = {c: rows["c"][first_of[c]]["configuration"] for c in cfgs}
    xlo_c = value_floor(min(r["mrr"] for r in rows["c"]), 0.05, MS_HOUSE, ROW2, 0.75, tuple(run_shape.values()))
    hs.panel_letter(fig, 0.6, y_key, "c")
    hs.panel_letter(fig, COLW + 0.6, y_key, "d")

    def value_row(ax_, x, txt, sl, row, fmt):
        """A printed value in the row just above the plotting area, centred on its x (data units)."""
        t = ax_.text(x, 1.0, txt, transform=blended_transform_factory(ax_.transData, ax_.transAxes) +
                     ScaledTranslation(0, 1.4 / 25.4, fig.dpi_scale_trans), ha="center", va="bottom",
                     fontsize=PT, clip_on=False)
        tie(t, sl, row, fmt)
        return t

    # c: a table of tiles, one row per configuration (highest mean on top), one column per run and the mean;
    # each tile coloured on cividis by its MRR and its value printed
    cfgs.sort(key=lambda c: -mean_of[c])
    ax = axes(ax_c[0], ax_c[1], top2, ROW2, spines=False)
    ax_w_mm[id(ax)] = ax_c[1]
    colsx = list(runs_c) + ["mean"]
    xs_ = {u: i + (0.25 if u == "mean" else 0) for i, u in enumerate(colsx)}
    ax.set_xlim(-0.5, len(colsx) - 0.25)
    ax.set_ylim(len(cfgs) - 0.5, -0.5)
    from matplotlib.patches import Rectangle
    for y, c in enumerate(cfgs):
        for u in colsx:
            if u == "mean":
                v, ri, fmt = mean_of[c], first_of[c], "{mean_mrr_over_runs:.2f}"
            else:
                ri = next(k for k, r in enumerate(rows["c"]) if r["config"] == c and r["run"] == u)
                v, fmt = rows["c"][ri]["mrr"], "{mrr:.2f}"
            fc = hs.cividis_value(v, xlo_c, 1.0)
            ax.add_patch(Rectangle((xs_[u] - 0.46, y - 0.44), 0.92, 0.88, facecolor=fc, edgecolor="none",
                                   zorder=1))
            t = ax.text(xs_[u], y, half_up(v), ha="center", va="center", fontsize=PT, color=hs.ink_on(fc),
                        zorder=2)
            tie(t, "c", ri, fmt)
    ax.set_yticks(range(len(cfgs)))
    ax.set_yticklabels([label_of[c] for c in cfgs])
    ax.tick_params(axis="y", length=0, pad=2)
    ax.xaxis.set_ticks_position("top")
    ax.set_xticks([xs_[u] for u in colsx])
    run_no = {r["run"]: r["run_number"] for r in rows["c"]}
    ax.set_xticklabels([f"Run {run_no[u]}" for u in runs_c] + ["Mean"])
    ax.tick_params(axis="x", length=0, pad=1.5, top=True, labeltop=True, bottom=False, labelbottom=False)
    cb_w = 34.0
    cb_x = ax_c[0] + ax_c[1] / 2 - (cb_w + 2.0 + tw("Mean reciprocal rank")) / 2
    cb_t = [v for v in ticks(xlo_c, 1.0, 0.05) if round(v * 100) % 10 == 0]
    hs.vector_colourbar(fig, y_key - 2.4, cb_w, xlo_c, 1.0, cb_t, [f"{v:.2f}" for v in cb_t],
                        "Mean reciprocal rank", x_left=cb_x)

    # ---- d: RRF over the pre-built BGE-M3 indexes against corpus size (horizontal), a line in RRF's series colour
    # and shape (panel b), each value printed above its size
    ax = axes(ax_d[0], ax_d[1], top2, ROW2)
    ax_w_mm[id(ax)] = ax_d[1]
    dd = sorted(rows["d"], key=lambda r: r["corpus_size_papers"])
    xd = [r["corpus_size_papers"] for r in dd].index
    ln = ax.plot([xd(r["corpus_size_papers"]) for r in dd], [r["mrr"] for r in dd], color=BLUE, lw=hs.LW["series"],
                 marker=MK, ms=MS_HOUSE, mfc=BLUE, mec=BLUE, mew=0.3, zorder=3, clip_on=False)[0]
    data_marks.append((ax, ln))
    for r in dd:
        value_row(ax, xd(r["corpus_size_papers"]), half_up(r["mrr"]), "d", rows["d"].index(r), "{mrr:.2f}")
    lo_d = value_floor(min(r["mrr"] for r in dd), 0.04, MS_HOUSE, ROW2, 0.84)
    ax.set_ylim(lo_d, 1.0)
    ax.set_yticks(ticks(lo_d, 1.0, 0.04))
    ax.set_yticklabels([f"{v:.2f}" for v in ticks(lo_d, 1.0, 0.04)])
    ax.set_xlim(-0.4, len(dd) - 0.6)
    ax.set_xticks(range(len(dd)))
    ax.set_xticklabels([str(r["corpus_size_papers"]) for r in dd])
    ax.set_xlabel("Corpus size (papers, evenly spaced)")
    ax.set_ylabel("Mean reciprocal rank")

    # ---- no ligature (S448 R10 pairs the SVG and the PDF character by character); every text on the page; no two
    # texts overlapping; c's key over no data point
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    px_mm = 25.4 / fig.dpi
    texts = [t_ for t_ in fig.findobj(Text) if t_.get_visible() and t_.get_text().strip()]
    boxes = [(t_.get_text(), t_.get_window_extent(rend)) for t_ in texts]
    probs = []
    for s, bb in boxes:
        if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > fig.bbox.width + 0.5 or bb.y1 > fig.bbox.height + 0.5:
            probs.append(f"{s!r} reaches past the page")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a_, b_ = boxes[i][1], boxes[j][1]
            if min(a_.x1, b_.x1) - max(a_.x0, b_.x0) > 0.5 and min(a_.y1, b_.y1) - max(a_.y0, b_.y0) > 0.5:
                probs.append(f"{boxes[i][0]!r} overlaps {boxes[j][0]!r}")
    # every data point: its centre inside its axes, its marker clear of the two drawn axis lines (left, bottom) by
    # more than the line's half width, and two points of a and b at one corpus size never on one another; d's
    # printed values right of the y axis line
    clear_px = lw_axis / 2 * fig.dpi / 72 + 0.5
    pts = {}
    for ax_, ln in data_marks:
        r_px = (half_extent(ln.get_marker()) * ln.get_markersize() + ln.get_markeredgewidth() / 2) * fig.dpi / 72
        xy = ax_.transData.transform(np.column_stack(ln.get_data()))
        bb = ax_.bbox
        for x_, y_ in xy:
            pts.setdefault(id(ax_), []).append((x_, y_, r_px))
            if not (bb.x0 - 0.5 <= x_ <= bb.x1 + 0.5 and bb.y0 - 0.5 <= y_ <= bb.y1 + 0.5):
                probs.append(f"a data point at {x_ * px_mm:.1f}, {y_ * px_mm:.1f} mm lies outside its axes")
            elif x_ - r_px < bb.x0 + clear_px or y_ - r_px < bb.y0 + clear_px:
                probs.append(f"a data point at {x_ * px_mm:.1f}, {y_ * px_mm:.1f} mm touches an axis line")
    for ax_ in fig.axes[:2]:
        p_ = pts[id(ax_)]
        for i in range(len(p_)):
            for j in range(i + 1, len(p_)):
                (x1, y1, r1), (x2, y2, r2) = p_[i], p_[j]
                if abs(x1 - x2) < r1 + r2 and abs(y1 - y2) < r1 + r2:
                    probs.append(f"two points overlap at {x1 * px_mm:.1f}, {y1 * px_mm:.1f} mm (dx {abs(x1 - x2) * px_mm:.2f} dy {abs(y1 - y2) * px_mm:.2f} r {r1 * px_mm:.2f} {r2 * px_mm:.2f})")
    probs += [f"colour {c} is outside the house palette" for c in hs.check_figure_colours(fig)]
    if probs:
        plt.close(fig)
        raise SystemExit("the plate is not drawn: " + "; ".join(probs[:6]))
    finish_plate(fig, W_MM, H, paths, title=SI_LABEL)
    return H, printed, {"series_b": [[next(r["strategy"] for r in rows["b"] if r["config"] == s) for s in g]
                                     for g in ser], "colours_b": colours[:len(ser)], "shapes_b": shapes_b[:len(ser)],
                        "shapes_a": shapes, "colours_a": col_a,
                        "shapes_c": run_shape}


# ---------------------------------------------------------------------------------------------------------------
def words(k):
    return ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][k] if k <= 10 \
        else f"{k:,}"


def join(xs):
    xs = [str(x) for x in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def legend_text(recs, tab, drawn, stamp, tag):
    a, b, c, d = (recs[x] for x in "abcd")
    rows = {k: [dict(zip(v[0], r)) for r in v[1]] for k, v in tab.items()}
    nq = {r["n_queries"] for k in "abd" for r in rows[k]}
    assert len(nq) == 1, "a, b and d no longer share one query count"
    nq = nq.pop()
    ids = {k: {q["id"] for r in recs[k]["results"] for q in r["per_query"]} for k in "abd"}
    assert ids["a"] == ids["b"] == ids["d"], "a, b and d no longer share one query set"
    run_ids = {}
    for r in c["results"]:
        run_ids.setdefault(r["run"], set()).update(q["id"] for q in r["per_query"])
    runs = list(run_ids)
    same_as_abd = [u for u in runs if run_ids[u] == ids["a"]]
    others = [u for u in runs if u not in same_as_abd]
    disjoint = all(not (run_ids[u] & run_ids[v]) for i, u in enumerate(runs) for v in runs[i + 1:])
    other_n = sorted({len(run_ids[u]) for u in others})
    merged = [g for g in drawn["series_b"] if len(g) > 1]
    n_runs = {r["n_runs"] for r in rows["c"]}
    assert len(n_runs) == 1
    n_runs = n_runs.pop()
    sizes_ab = sorted({r["corpus_size_papers"] for r in rows["a"]})
    sizes_d = sorted({r["corpus_size_papers"] for r in rows["d"]})
    cfg_a = a["config"]
    # where two drawn series have the same value at two neighbouring corpus sizes, their lines lie on one another
    # between those sizes (the points are set apart, the lines are not)
    val_a = {m: [next(r["mrr"] for r in rows["a"] if r["model"] == m and r["corpus_size_papers"] == s)
                 for s in sizes_ab] for m in dict.fromkeys(r["model"] for r in rows["a"])}
    val_b = {g[0]: [next(r["mrr"] for r in rows["b"] if r["strategy"] == g[0] and r["corpus_size_papers"] == s)
                    for s in sizes_ab] for g in drawn["series_b"]}

    def coincide(vals):
        ks = list(vals)
        return any(vals[u][i] == vals[v][i] and vals[u][i + 1] == vals[v][i + 1]
                   for x, u in enumerate(ks) for v in ks[x + 1:] for i in range(len(sizes_ab) - 1))
    hidden = [p for p, v in (("a", val_a), ("b", val_b)) if coincide(v)]
    def hidden_sentence(k, many):
        return (f" Where two {many} tie at neighbouring sizes, only the line drawn last shows between them."
                if k in hidden else "")
    # audit 27 Oct F6 (fig1_2_5): `disjoint` compares raw query ids, and the second and third runs carry the prefixes B_ and C_, so
    # it holds by construction; whether the queries' texts differ cannot be read from these records (per_query holds
    # ids and scores, no query text). The sentence therefore speaks of query ids, which is what is compared.
    run_no = run_numbers(c["results"])
    run_sentence = (f"run {join([str(run_no[u]) for u in same_as_abd])} on the {nq} queries, "
                    f"run{'s' if len(others) > 1 else ''} {join([str(run_no[u]) for u in others])} each on "
                    f"{join(other_n)} other query ids"
                    + (", no query id shared between runs" if disjoint else ""))
    merged_sentence = "".join(f" {join(g)} are equal at every corpus size and are drawn as one line." for g in merged)
    # Valerio, 23 Oct: the legend describes the image only, in the style of resubmission/05_figures/*_caption.md;
    # no method narrative, no run dates, no statement on tests, no provisional note (the data stamp stays in the
    # header above the title, where S448 R9 finds it).
    # Valerio, 8 Nov (editor row 45, extended to the Supplementary legends): an "n = X" only in a panel that draws
    # derived statistics (this plate draws none: c's mean tile has no spread), and every panel described in full,
    # never "as in a" or "in a and b".
    shown = "a, b and d" + (f" and run {join([str(run_no[u]) for u in same_as_abd])} of c" if same_as_abd else "")
    spread = "points at one size set apart along the axis, so ties stay visible."
    body = (
        f"Each value is a mean reciprocal rank (MRR) over retrieval queries of their own, not questions of the "
        f"question-answering benchmark; no answer is generated and no judge is involved. Panels {shown} use one set "
        f"of {nq} queries. "
        f"**a**, MRR on the {nq} queries against corpus size ({join(sizes_ab)} papers, evenly spaced) for "
        f"{words(len(cfg_a['models']))} embedding models with "
        f"{cfg_a['search_mode'].replace('_only', '').replace('_', ' ')} search only ({cfg_a['chunk_size']}-token "
        f"chunks, overlap {cfg_a['chunk_overlap']}); one colour and shape per model, labelled at the largest corpus; "
        f"{spread}{hidden_sentence('a', 'models')} "
        f"**b**, MRR on the {nq} queries against corpus size ({join(sizes_ab)} papers, evenly spaced) for "
        f"{words(len(b['config']['configs_tested']))} search strategies with {b['config']['embedding_model']} "
        f"embeddings; one colour and shape per strategy, labelled at the largest corpus; {spread}{merged_sentence}"
        f"{hidden_sentence('b', 'strategies')} "
        f"**c**, MRR of {words(len(c['config']['configs_tested']))} chunking configurations "
        f"({c['config']['model']} embeddings, {c['config']['search']} search, {c['config']['corpus_size']} papers), "
        f"each run {words(n_runs)} times: {run_sentence}. One row per configuration, highest mean at the top; each "
        f"tile gives one run's MRR and the last column the mean of the {words(n_runs)} runs, coloured on the scale "
        f"above the tiles. "
        f"**d**, MRR on the {nq} queries against corpus size ({join(sizes_d)} papers, evenly spaced) for "
        f"{d['config']['search'].replace('BGE-M3', 'bge-m3')} search, one run per size; each value is printed above "
        f"its size.\n")
    title = f"**{SI_LABEL} | Retrieval pipeline selection.**"
    head = (f"Legend DRAFT for {SI_LABEL} (provisional; written by scripts/S461_supp_fig2_retrieval.py). Data stamp: "
            f"{stamp}.\n\n")
    return head + title + "\n\n" + body


# ---------------------------------------------------------------------------------------------------------------
def recorded_as_frozen(key: str) -> str:
    """A deposit record the provenance of 23 October names by "<upstream>/publication/results/<file>": its frozen
    label (findings/recompute/upstream_inputs/)."""
    return "frozen:upstream/" + key[len("<upstream>/"):] if key.startswith("<upstream>/publication/results/") else key


def main(argv=None):
    global OUT
    FR.pin_hash_seed()                              # D155: the PDF's font subsets depend on the string-hash seed
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="default findings/figures_provisional/supp_fig2; the committed record is read there")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    prov_p = OUT / f"{SIDE}_provenance.json"
    if not prov_p.exists():
        raise SystemExit(f"{prov_p.relative_to(ROOT)} is missing: there is no committed plate to rebuild")
    recorded = json.loads(prov_p.read_text())["provenance"]["inputs_sha256"]
    if a.out:
        OUT = Path(a.out).resolve()
    if FLOCK.get("status") != "agreed":
        raise SystemExit(f"{FIGURE_LOCK.relative_to(ROOT)} status {FLOCK.get('status')!r}, not 'agreed' (D87)")
    inputs, recs, qa_ids = load()
    try:
        seen = FR.check_recorded({FR.frozen_label(p): sha256_file(p) for p in inputs.values()}, recorded,
                                 recorded_as_frozen)
    except FR.FrozenInputError as e:
        raise SystemExit(f"REFUSED: {e}") from None
    print(f"frozen inputs: {seen['compared']} recorded by the committed plate, each equal; "
          f"{len(seen['not_recorded_before'])} read and not recorded before")
    rep = reproduce(recs, qa_ids)                       # exit 2 before anything is written
    tab = tables(recs)
    n_in, n_plan = rep["rows"], rep["planned"]
    tag = f" (provisional, {n_in} of {n_plan})"
    months = sorted({datetime.strptime(r["timestamp"], "%Y%m%d_%H%M%S").strftime("%B %Y") for r in recs.values()})
    stamp = (f"PROVISIONAL: {n_in} of {n_plan} result rows, the deposit's four retrieval sweeps of "
             f"{join(months)} as they are (no run planned, experiments/LIST.md); legend a draft")
    OUT.mkdir(parents=True, exist_ok=True)
    before_q194 = list(OUT.glob(f"Figure {N}*")) + list(OUT.glob(f"Source Data Fig. {N}*")) + \
        [p for p in (OUT / f"figure{N}_numbers.json", OUT / f"figure{N}_provenance.json") if p.exists()]
    for old in list(OUT.glob(f"{SI_LABEL}*")) + before_q194:
        old.unlink()                              # a plate of another state, or of the names before D92 Q194, is never
        #                                           left beside this one
    paths = {x: OUT / f"{SI_LABEL}{tag}.{x}" for x in ("pdf", "svg", "png")}
    H, printed, drawn = draw(tab, paths)
    FR.check_pdf_deterministic(paths["pdf"])        # D155: saved with no date; refuse one
    FR.check_svg_deterministic(paths["svg"])
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for k in "abcd":
        cols, rws = tab[k]
        ws = wb.create_sheet(sheet(k))
        ws.append(cols)
        for c_ in ws[1]:
            c_.font = Font(bold=True)
        for r in rws:
            ws.append(r)
    sd = OUT / f"{SI_LABEL} data{tag}.xlsx"
    wb.save(sd)
    fix_workbook(sd)
    FR.check_xlsx_deterministic(sd)                 # fix_workbook is fig_repro.deterministic_xlsx's model
    numbers = OUT / f"{SIDE}_numbers.json"
    numbers.write_text(json.dumps({
        "stamp": stamp, "what": f"every number {SI_LABEL} draws, sheet by sheet as the data workbook holds them "
                                "(S448 --supplementary holds it to the workbook and the plate, R8 (2) to (6), D94 O-b)",
        "sheets": {sheet(k): {"columns": tab[k][0], "rows": tab[k][1]} for k in "abcd"},
        "printed": printed,
        "printed_what": "every text on the plate written from a record (labels and printed values): the SVG group "
                        "id of its text, the data workbook's sheet, 0-based data row and format it is written from"},
        indent=1) + "\n")
    legend = legend_text(recs, tab, drawn, stamp, tag)
    (OUT / "legend_draft.md").write_text(legend)
    capf = OUT / f"{SI_LABEL} data caption{tag}.md"
    capf.write_text(
        f"**{SI_LABEL} data{tag} |** The numbers drawn in {SI_LABEL} (retrieval pipeline selection), one "
        f"sheet per panel: {sheet('a')} embedding model by corpus size, {sheet('b')} search strategy by corpus "
        f"size, {sheet('c')} chunking configuration by run with the mean over runs (`run` holds the record's letter, "
        f"`run_number` the number the plate and the legend print), {sheet('d')} RRF search "
        f"over the pre-built BGE-M3 indexes (the record's words) by corpus size. Each row is one result row of the "
        f"deposit's records (exp01_embedding_latest.json, exp02_search_latest.json, exp03a_chunking_latest.json, exp03b_scalability_latest.json) with its mean "
        f"reciprocal rank unrounded.\n\nProvisional: {stamp}.\n")
    prov_cmd = "uv run --frozen python scripts/S461_supp_fig2_retrieval.py"
    out = {
        "provenance": {"script": "scripts/S461_supp_fig2_retrieval.py",
                       "script_sha256": sha256_file(Path(__file__)), "command": prov_cmd,
                       "python": platform.python_version(),
                       "deterministic": "D155: no build time and no repository HEAD are recorded; the script's and "
                                        "every input's sha256 identify the build",
                       "inputs_sha256": {FR.frozen_label(p): sha256_file(p) for p in inputs.values()},
                       "lock_toml_sha256": sha256_file(LOCK), "model_calls": 0},
        "reproduced": rep["checks"], "stamp": stamp, "figure": SI_LABEL,
        "named": f"{SI_LABEL}: FIGURE_LOCK [files] supplementary_name (D92 Q194)",
        "page_mm": [W_MM, round(H, 3)],
        "figure_lock": {"path": str(FIGURE_LOCK.relative_to(ROOT)), "sha256": sha256_file(FIGURE_LOCK),
                        "status": FLOCK.get("status")},
        "type_pt": {"panel letters (bold)": PT_LETTER, "all other text": PT}, "font": FONT,
        "drawn": drawn,
        "panels": {"a": "MRR by corpus size per embedding model (exp01), a house colour and shape per model, "
                        "direct labels",
                   "b": "MRR by corpus size per search strategy (exp02), Okabe-Ito colours; strategies with equal "
                        "values at every size merged into one series",
                   "c": "MRR per chunking configuration (exp03a): tiles by run and mean, each value printed, cividis "
                        "scale above",
                   "d": "MRR of RRF over the pre-built BGE-M3 indexes (the record's words) per corpus size (exp03b), each value printed"},
        "files": {p.name: sha256_file(p) for p in list(paths.values()) + [sd, capf, numbers,
                                                                         OUT / "legend_draft.md"]}}
    (OUT / f"{SIDE}_provenance.json").write_text(json.dumps(out, indent=1) + "\n")
    print("reproduced: " + "; ".join(rep["checks"]))
    print(stamp)
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W_MM:g} x {H:.1f} mm), {sd.name}, {capf.name}, "
          f"{numbers.name}, legend_draft.md, {SIDE}_provenance.json into "
          f"{OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT}")


if __name__ == "__main__":
    main()
