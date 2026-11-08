"""Figure 5 assembled (scratch, 28 Oct; not the repository plate): the seven panels chosen or advised on the options
page, redrawn into one 183 mm plate so every text is 8 pt and the colours and the strategy order are the same in
every panel.

  a  fig5a-a1    three signals per strategy (D163)                          reads ../fig5_a/a_data.json
  b  fig5b2-6    judge against papers, answers split four ways (D164)       reads ../fig5_b/b_points.json + the raw pull
  c  fig5b3-8b   answers with every key concept, judge verdict (Q16 open)   reads ../fig5_bc3/b8/points.json, recount.json
  d  fig5c2-5    head-to-head counts against single pass (D164)             reads ../fig5_bc2/c5/c5_counts.json
  e  fig5c2-8    margins per draw, grey lines between strategies (D164,     reads the pull through S473, as
                 version A; Q17 open)                                       ../fig5_bc3/c8sep/build_c3_8.py does
  f  fig5d-d3    faithfulness of passed and failed answers (advice)         reads ../fig5_d/d_data.json
  g  fig5e-e4    MiniCheck precision at faithfulness 5 and below (advice)   reads ../fig5_e/e_data.json

Every panel's data step is its scratch build's, unchanged; only the drawing is new. Before drawing, each panel's
numbers are compared with its scratch build's numbers file and the run stops on any difference.

Colours, one per signal everywhere: judge #0072B2 (blue, circle), concepts #E69F00 (orange, square), papers #000000
(black, diamond); panel e's marks and its key use them (28 Oct review: a and d name the signals in plain text, and a
draws no means).
Category colours are kept off the three signal colours: b and c keep their scratch colours (sky blue, vermillion,
greys); d's outcome colours change from orange and blue (the concept and judge colours) to reddish purple (single pass
higher) and bluish green (strategy higher). f keeps cividis. Strategy order everywhere: single pass, multi-hop,
verified pass, RLM-5, RLM-10, RLM-20. Panels in one band share the row labels.

Layout A (chosen): band 1 a | b | c on the six strategy rows; band 2 d | e on the five strategies against single pass;
band 3 f | g on the six strategies, two sub-rows each. Layout B ([a | b] / [c | d | e] / [f | g]) is planned by
plan_layouts() and does not fit 170 mm at 8 pt (see layout_plan in numbers.json and layout_sketch.png).

  uv run --frozen python <this folder>/build_fig5.py        (from the repository root)

28 Oct evening review (Valerio): a, Tukey whiskers on every box, no means or intervals, plain column names, the
draws in the legend; b, a 2 x 2 key; c, the n header names what it counts; d, plain column names; e, its own strategy
names and its key at the top left, x label 'Strategy minus single pass'; g, one 'Faithfulness' heading over sub-rows
'5' and '0-4'. Also fig5_a_alt.png: panel a with the Judge column as a pass-rate bar under the dots, to compare.

Writes into this folder: Figure 5 (provisional, assembled 28 Oct).{pdf,svg,png}, Source Data Fig. 5.xlsx, Source Data
Fig. 5 caption.md, figure5_numbers.json and figure5_provenance.json (S448's files), legend.md, legend_draft.md
(legend.md with the data stamp, for S448 R9), methods_notes.md, numbers.json (every drawn number with its source)
and layout_sketch.png.
"""
import csv  # noqa: F401
import glob
import hashlib
import importlib.util
import itertools
import json
import logging
import re
import statistics
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
FIGOPTS = HERE.parent
PULL = FIGOPTS.parent / "fig5_pull_1028"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
S473 = importlib.util.module_from_spec(spec)
sys.modules["S473"] = S473
spec.loader.exec_module(S473)
S463, S457 = S473.S463, S473.S457

logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.textpath import TextToPath  # noqa: E402

S457.figure_lock_agreed()
plt.rcParams.update(S457.plate_rc("fig5_assembled"))
plt.rcParams["axes.unicode_minus"] = False
PT, MM_PT = S457.PT, S457.MM_PT
W = S457.FIG_W_MM
H_MAX = S457.FIG_H_MAX_MM
assert W == 183.0 and H_MAX == 170.0

CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
assert CONFIGS == list(S473.CONFIGS)
LABEL = {c: S473.LABEL[c] for c in CONFIGS}
OTHERS = CONFIGS[1:]
SIGS = ("judge", "concept", "papers")
OK = S457.OKABE
SIG_COL = {"judge": OK["blue"], "concept": OK["orange"], "papers": OK["black"]}
SIG_MK = {"judge": "o", "concept": "s", "papers": "D"}
SIG_MS = {"o": 1.0, "s": 0.9, "D": 0.85}            # c8's equal visual weight (square and diamond look larger)
GREY = S457.DOT_GREY
WHITE, BLACK = "#FFFFFF", "#000000"
assert (SIG_COL["judge"], SIG_COL["concept"]) == ("#0072B2", "#E69F00")
B_COLS = [OK["sky blue"], "#BBBBBB", "#888888", OK["reddish purple"]]  # b6's four segments; vermillion (too close
#                                         to the concepts orange, story critic F8) changed to reddish purple, 28 Oct fix
C_PASS, C_FAIL = "#BBBBBB", OK["sky blue"]                              # b3-8b
D_COLS = {"sp": OK["reddish purple"], "tie": "#BBBBBB", "ot": OK["bluish green"]}
SEP_GREY = "#949494"                                                    # c3-8 A's separator lines

STAMP_FILE = "Figure 5 (provisional, assembled 28 Oct)"
T2P, FP = TextToPath(), FontProperties(family=S457.FONT, size=PT)


def tw(s):
    return T2P.get_text_width_height_descent(s, FP, ismath=False)[0] * MM_PT


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


SOURCES = {}


def src(key, path):
    SOURCES[key] = {"path": str(path), "sha256": sha(path)}
    return path


DIFFS = {}           # panel -> differences from its scratch build's numbers file (want none)


def same(a, b, tol=1e-9):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


# =====================================================================================================================
# data, panel by panel, each as its scratch build computes it
# =====================================================================================================================
# ---- a: fig5_a/draw_a.py a1 (a_data.json from prep.py, S473's functions on fig5_pull_1028)
A_DATA = src("a: a_data.json (fig5_a/prep.py)", FIGOPTS / "fig5_a/a_data.json")
DA = json.loads(A_DATA.read_text())
assert DA["configs"] == CONFIGS
QA, QW = DA["questions"], DA["W_questions"]
A_SPECS = [("pass", "pass4", QA, (0, 100), [0, 50, 100], "Judge pass rate (%)", "Judge", "3 draws", "judge"),
           ("concept", "concept", QA, (0, 1), [0, 0.5, 1], "Concept recall", "Concepts", "3 draws", "concept"),
           ("papers", "papers", QW, (0, 1), [0, 0.5, 1], "Papers precision", "Papers", "draw 1", "papers")]
A = {}
for col, sig, qs, lim, ticks, xl, ref, dr, s_ in A_SPECS:
    rows = {c: [(q, DA["per_q"][c][q][sig]) for q in qs if DA["per_q"][c][q][sig] is not None] for c in CONFIGS}
    A[col] = {"rows": rows, "summary": {c: S457.summary([v for _, v in rows[c]]) for c in CONFIGS},
              "n": len({q for c in CONFIGS for q, _ in rows[c]})}
a1 = json.loads(src("a: scratch a1_three_signals.numbers.json", FIGOPTS / "fig5_a/a1_three_signals.numbers.json")
                .read_text())
DIFFS["a"] = []
for col in A:
    if a1["columns"][col]["n_questions"] != A[col]["n"]:
        DIFFS["a"].append((col, "n", A[col]["n"], a1["columns"][col]["n_questions"]))
    for c in CONFIGS:
        mine, theirs = A[col]["summary"][c], a1["columns"][col]["per_strategy"][c]["summary"]
        for k in theirs:
            if not same(mine[k], theirs[k], 1e-12):
                DIFFS["a"].append((col, c, k, mine[k], theirs[k]))
        if [list(x) for x in A[col]["rows"][c]] != a1["columns"][col]["per_strategy"][c]["per_question"]:
            DIFFS["a"].append((col, c, "per_question"))

# ---- b: fig5_bc2/b6/draw_b6.py (b_points.json, re-read against the raw pull; the 28 October counts asserted)
BPTS = src("b: b_points.json (fig5_b/prep.py)", FIGOPTS / "fig5_b/b_points.json")
DB = json.loads(BPTS.read_text())
assert DB["configs"] == CONFIGS
PTS_B = DB["b"]
assert len(PTS_B) == 495 and len(DB["W_questions"]) == 83 and DB["pass_t"] == 4
assert all(p["draw"] == 1 for p in PTS_B)
assert all(p["judge_pass"] == int(p["judge_correctness"] >= 4) for p in PTS_B)
cp = src("b: pull s3/g1_collect.jsonl", PULL / "s3/g1_collect.jsonl")
judge_raw = {}
for r in jl(cp):
    a_ = r.get("a") or {}
    if a_.get("status") == "ok":
        judge_raw[(r["config"], r["question_id"], r["draw"])] = (a_.get("scores") or {}).get("correctness")
    elif a_.get("status") == "no_answer":
        judge_raw[(r["config"], r["question_id"], r["draw"])] = 0
papers_raw = {}
for f_ in sorted(glob.glob(str(PULL / "l1/papers/*.jsonl"))):
    src(f"b: pull {Path(f_).relative_to(PULL)}", f_)
    for r in jl(f_):
        papers_raw[(r["config"], r["question_id"], r["draw"])] = (r.get("signals") or {}).get("precision")
mism = [(p["strategy"], p["question_id"]) for p in PTS_B
        if judge_raw.get((p["strategy"], p["question_id"], 1)) != p["judge_correctness"]
        or papers_raw.get((p["strategy"], p["question_id"], 1)) is None
        or abs(papers_raw[(p["strategy"], p["question_id"], 1)] - p["papers_precision"]) > 1e-9]
if mism:
    raise SystemExit(f"b: {len(mism)} answers differ from the raw pull: {mism[:3]}")
B_MEDIAN = statistics.median(p["papers_precision"] for p in PTS_B)
B_ON_MEDIAN = sum(p["papers_precision"] == B_MEDIAN for p in PTS_B)


def b_split(rows, m):
    hi = [p["papers_precision"] >= m for p in rows]
    ps = [bool(p["judge_pass"]) for p in rows]
    return [sum((not j) and h for j, h in zip(ps, hi)), sum(j and h for j, h in zip(ps, hi)),
            sum((not j) and (not h) for j, h in zip(ps, hi)), sum(j and (not h) for j, h in zip(ps, hi)), len(rows)]


B = {c: b_split([p for p in PTS_B if p["strategy"] == c], B_MEDIAN) for c in CONFIGS}
B_EXPECTED = {"single_pass": [7, 63, 6, 7, 83], "multi_hop": [1, 38, 15, 28, 82], "verified_pass": [6, 65, 5, 7, 83],
              "rlm_5": [4, 20, 21, 37, 82], "rlm_10": [6, 17, 13, 46, 82], "rlm_20": [4, 17, 22, 40, 83]}
if B != B_EXPECTED or round(B_MEDIAN, 4) != 0.6562 or B_ON_MEDIAN != 3:
    raise SystemExit(f"b: counts {B} median {B_MEDIAN} differ from the 28 October check")
B_KEYS = ["judge_fails_papers_high", "both_high", "both_low", "judge_passes_papers_low", "n"]
b6 = json.loads(src("b: scratch b6_bars_numbers.json", FIGOPTS / "fig5_bc2/b6/b6_bars_numbers.json").read_text())
DIFFS["b"] = [(c, B[c], b6["counts"][LABEL[c]]) for c in CONFIGS
              if dict(zip(B_KEYS, B[c])) != b6["counts"][LABEL[c]]]
if not same(B_MEDIAN, b6["median_papers_precision_pooled"]):
    DIFFS["b"].append(("median", B_MEDIAN, b6["median_papers_precision_pooled"]))

# ---- c: fig5_bc3/b8/draw_b3_8.py design b (points.json and recount.json, recount.py from raw files)
PTS_C = json.loads(src("c: points.json (fig5_bc3/b8/recount.py)", FIGOPTS / "fig5_bc3/b8/points.json").read_text())
REC_C = json.loads(src("c: recount.json (fig5_bc3/b8/recount.py)", FIGOPTS / "fig5_bc3/b8/recount.json").read_text())
assert len(PTS_C) == 495 and REC_C["changed_vs_old_b8_numbers"] == [] and REC_C["judge_raw_vs_g1_collect_mismatches"] == []
C = {c: {"pass": sum(1 for p in PTS_C if p["strategy"] == c and p["concept_recall"] == 1 and p["pass"]),
         "fail": sum(1 for p in PTS_C if p["strategy"] == c and p["concept_recall"] == 1 and not p["pass"])}
     for c in CONFIGS}
assert C == {"single_pass": {"pass": 27, "fail": 0}, "multi_hop": {"pass": 12, "fail": 0},
             "verified_pass": {"pass": 29, "fail": 0}, "rlm_5": {"pass": 21, "fail": 9},
             "rlm_10": {"pass": 29, "fail": 5}, "rlm_20": {"pass": 26, "fail": 5}}, C
C_TOT = {c: {"n": sum(1 for p in PTS_C if p["strategy"] == c),
             "fail": sum(1 for p in PTS_C if p["strategy"] == c and not p["pass"])} for c in CONFIGS}
b8 = json.loads(src("c: scratch b8 numbers.json", FIGOPTS / "fig5_bc3/b8/numbers.json").read_text())
DIFFS["c"] = [(c, C[c], b8["b"]["every_concept_by_strategy"][c]) for c in CONFIGS
              if C[c] != b8["b"]["every_concept_by_strategy"][c]]
DIFFS["c"] += [(c, "totals", C_TOT[c], b8["b"]["strategy_totals"][c]) for c in CONFIGS
               if C_TOT[c] != b8["b"]["strategy_totals"][c]]

# ---- d: fig5_bc2/c5/draw_c5.py (c5_counts.json from prep_c5.py, S473's functions)
C5 = src("d: c5_counts.json (fig5_bc2/c5/prep_c5.py)", FIGOPTS / "fig5_bc2/c5/c5_counts.json")
DD = json.loads(C5.read_text())
assert DD["strategies"] == CONFIGS
D = {}
for o in OTHERS:
    for s in SIGS:
        r = DD["pairs"][f"single_pass|{o}"][s]
        assert r["first_higher"] + r["tie"] + r["second_higher"] == r["n"]
        D[(o, s)] = {"sp": r["first_higher"], "tie": r["tie"], "ot": r["second_higher"], "n": r["n"]}
D_CHECK = {"multi_hop": [(31, 40, 12), (66, 11, 6), (52, 21, 9)],
           "verified_pass": [(15, 50, 18), (25, 35, 23), (23, 24, 36)],
           "rlm_5": [(53, 14, 16), (23, 17, 43), (74, 0, 8)],
           "rlm_10": [(49, 14, 20), (25, 13, 45), (75, 2, 5)],
           "rlm_20": [(54, 14, 15), (29, 18, 36), (77, 0, 6)]}
for o, trip in D_CHECK.items():
    for s, t in zip(SIGS, trip):
        assert (D[(o, s)]["sp"], D[(o, s)]["tie"], D[(o, s)]["ot"]) == t, (o, s)
c5n = json.loads(src("d: scratch c5_numbers.json", FIGOPTS / "fig5_bc2/c5/c5_numbers.json").read_text())
SIGNAME = {"judge": "Judge", "concept": "Concepts", "papers": "Papers"}
DIFFS["d"] = []
for o in OTHERS:
    for s in SIGS:
        t = c5n["drawn"][SIGNAME[s]][LABEL[o]]
        m = D[(o, s)]
        if (m["sp"], m["tie"], m["ot"], m["n"]) != (t["single_pass_higher"], t["tie"], t["other_higher"], t["n"]):
            DIFFS["d"].append((o, s, m, t))

# ---- e: fig5_bc3/c8sep/build_c3_8.py (the pull through S473's readers; compute's signals; margins per draw)
SIG_DRAWS = {"judge": (1, 2, 3), "concept": (1, 2, 3), "papers": (1,)}
with tempfile.TemporaryDirectory(prefix="fig5asm_") as tmpd:
    srcs = S473.pull_sources(PULL.resolve(), Path(tmpd))
    E_REP = S473.reproduce()
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
        b_ = x.get("b") or {}
        v = (b_.get("scores") or {}).get("faithfulness") if b_.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b_.get("status"), v, b_.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    cc = fn["c"]
    sig = {"judge": {}, "concept": {}, "papers": {}}
    for (c, q, d), cell in read["cells"].items():
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
    for k, v in srcs["sha"].items():
        SOURCES[f"e: {k}"] = {"sha256": v}
SOURCES["e: findings/recompute/L3/concept_recall.jsonl"] = {
    "path": str(ROOT / "findings/recompute/L3/concept_recall.jsonl"),
    "sha256": sha(ROOT / "findings/recompute/L3/concept_recall.jsonl")}
QW_E = cc["questions"]
assert len(QW_E) == 83 and QW_E == QW, (len(QW_E), QW_E == QW)


def margin(s, c, r, d):
    w = t = lo = 0
    for q in QW_E:
        a_, b_ = sig[s].get((c, q, d)), sig[s].get((r, q, d))
        if a_ is None or b_ is None:
            continue
        if a_ > b_:
            w += 1
        elif a_ < b_:
            lo += 1
        else:
            t += 1
    n = w + t + lo
    return {"wins": w, "ties": t, "losses": lo, "n": n, "margin_pct": 100.0 * (w - lo) / n}


E_ROWS = []
for c, r in itertools.combinations(CONFIGS, 2):
    row, ref = (r, c)
    for s in SIGS:
        for d in SIG_DRAWS[s]:
            E_ROWS.append({"strategy": row, "reference": ref, "signal": s, "draw": d, **margin(s, row, ref, d)})
E_DRAWN = [x for x in E_ROWS if x["reference"] == "single_pass"]
E_CHECK = {"multi_hop": ([-7, -13, -16], [-46, -55, -54], [-52]),
           "verified_pass": ([5, 5, -2], [5, -5, -4], [16]),
           "rlm_5": ([-29, -33, -18], [17, 20, 24], [-80]),
           "rlm_10": ([-25, -23, -18], [29, 22, 30], [-85]),
           "rlm_20": ([-31, -27, -30], [23, 19, 20], [-86])}
for c in OTHERS:
    for s, want in zip(SIGS, E_CHECK[c]):
        got = [int(S457.half_up(x["margin_pct"], 0)) for x in E_DRAWN if x["strategy"] == c and x["signal"] == s]
        assert got == want, (c, s, got, want)
c8 = json.loads(src("e: scratch fig5c3-8A_numbers.json", FIGOPTS / "fig5_bc3/c8sep/fig5c3-8A_numbers.json")
                .read_text())
DIFFS["e"] = []
c8d = {(x["row"], x["signal"], x["draw"]): x for x in c8["drawn"]}
for x in E_DRAWN:
    t = c8d.get((LABEL[x["strategy"]], x["signal"], x["draw"]))
    if t is None or any(not same(x[k], t[k], 1e-12) for k in ("margin_pct", "wins", "ties", "losses", "n")):
        DIFFS["e"].append((x, t))
if len(c8d) != len(E_DRAWN):
    DIFFS["e"].append(("count", len(c8d), len(E_DRAWN)))
if not (same(cc["W"], c8["kendall_W"], 1e-12) and same(cc["P"], c8["kendall_W_exact_P"], 1e-12)):
    DIFFS["e"].append(("W", cc["W"], cc["P"]))

# ---- f: fig5_d/d_draw.py d3 (d_data.json from d_data.py, S473's functions)
DF = json.loads(src("f: d_data.json (fig5_d/d_data.py)", FIGOPTS / "fig5_d/d_data.json").read_text())
assert DF["configs"] == CONFIGS
F_OK = [r for r in DF["rows"] if r["faith_status"] == "ok"]


def counts_of(rows):
    from collections import Counter
    cn = Counter(r["faithfulness"] for r in rows)
    return [cn.get(k, 0) for k in range(6)]


F = {}
for c in CONFIGS:
    for word, test in (("pass", lambda v: v >= 4), ("fail", lambda v: v < 4)):
        rs = [r for r in F_OK if r["strategy"] == c and test(r["correctness"])]
        F[(c, word)] = {"counts": counts_of(rs), "n": len(rs)}
    if F[(c, "pass")]["n"] + F[(c, "fail")]["n"] != DF["d"][c]["n"]:
        raise SystemExit(f"f {c}: pass and fail do not add to panel d's n")
d3 = json.loads(src("f: scratch d3_pass_fail_numbers.json", FIGOPTS / "fig5_d/d3_pass_fail_numbers.json").read_text())
DIFFS["f"] = []
for c in CONFIGS:
    for word in ("pass", "fail"):
        t = d3["numbers"]["per_strategy"][LABEL[c]][word]
        if (F[(c, word)]["n"], F[(c, word)]["counts"]) != (t["n"], t["counts_faith_0_to_5"]):
            DIFFS["f"].append((c, word, F[(c, word)], t))


def cividis6():
    cm = matplotlib.colormaps[S457.FLOCK["colour"]["continuous"]]
    return ["#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(round(255 * i / 5)))[:3]) for i in range(6)]


COLS6 = cividis6()

# ---- g: fig5_e/draw_e.py e4 (e_data.json from prep.py, S473's compute)
DG = json.loads(src("g: e_data.json (fig5_e/prep.py)", FIGOPTS / "fig5_e/e_data.json").read_text())
PTS_G = DG["points"]
assert DG["configs"] == CONFIGS


def quart(v):
    r_ = lambda x: round(float(x), 4)  # noqa: E731
    return {"n": len(v), "q25": r_(np.percentile(v, 25)), "median": r_(np.median(v)), "q75": r_(np.percentile(v, 75)),
            "min": r_(min(v)), "max": r_(max(v))}


G = []
for c in CONFIGS:
    for grp in ("5", "0 to 4"):
        pts = sorted([p for p in PTS_G if p["strategy"] == c
                      and ((p["faithfulness"] == 5) if grp == "5" else (p["faithfulness"] < 5))],
                     key=lambda p: (p["papers_precision"], p["question_id"]))
        v = [p["papers_precision"] for p in pts]
        G.append({"strategy": c, "grp": grp, "values": v, "qids": [p["question_id"] for p in pts], "q": quart(v),
                  "q_exact": {"q25": float(np.percentile(v, 25)), "median": float(np.median(v)),
                              "q75": float(np.percentile(v, 75))}})
e4 = json.loads(src("g: scratch e4_by_strategy.numbers.json", FIGOPTS / "fig5_e/e4_by_strategy.numbers.json")
                .read_text())
DIFFS["g"] = []
for mine, t in zip(G, e4["numbers"]["rows"]):
    if (LABEL[mine["strategy"]], mine["grp"]) != (t["strategy"], t["faithfulness"]):
        DIFFS["g"].append(("order", mine["strategy"], mine["grp"], t["strategy"], t["faithfulness"]))
    for k in ("n", "q25", "median", "q75", "min", "max"):
        if mine["q"][k] != t[k]:
            DIFFS["g"].append((mine["strategy"], mine["grp"], k, mine["q"][k], t[k]))
    if mine["values"] != t["values"]:
        DIFFS["g"].append((mine["strategy"], mine["grp"], "values"))
G_N = len(PTS_G)
G_NQ = len({p["question_id"] for p in PTS_G})
assert G_N == 503 and G_NQ == DG["rho_all"]["questions"]

if any(DIFFS.values()):
    raise SystemExit(f"drawn numbers differ from the scratch builds: { {k: v[:3] for k, v in DIFFS.items() if v} }")

# =====================================================================================================================
# layout (mm, from the plate's top left). Band 1: a | b | c; band 2: d | e; band 3: f | g.
# =====================================================================================================================
LINE = 3.7                                  # baseline to baseline of two 8 pt header lines
LABR = max(tw(LABEL[c]) for c in CONFIGS) + 0.4      # the shared strategy names, right-aligned here
# band 1
Y1 = 0.0
B1L = [Y1 + 2.9, Y1 + 2.9 + LINE, Y1 + 2.9 + 2 * LINE]
R1, P1 = Y1 + 12.0, 6.0
R1B = R1 + 6 * P1
A_X0, A_W, A_G = LABR + 1.8, 20.5, 4.0
A_XS = [A_X0 + j * (A_W + A_G) for j in range(3)]
A_END = A_XS[-1] + A_W
B_LET = A_END + 1.2
B_X0, B_W, B_XMAX = A_END + 4.6, 48.0, 83.0
B_X1 = B_X0 + B_W
B_NX = B_X1 + 1.2
C_LET = B_NX + tw("(n)") + 1.6
C_X0, C_W, C_XMAX = C_LET + 2.0, 27.5, 35.0
C_X1 = C_X0 + C_W
C_NX = C_X1 + 1.2
C_NR = C_NX + tw("34")                      # c's counts and their header end here (right-aligned)
C_NHEAD = "n, all concepts"                 # 28 Oct review: the n counts only answers stating every concept
assert C_NR <= W - 0.3 and C_NR - tw(C_NHEAD) > C_X0 + 3.0, (C_NR, tw(C_NHEAD))
BOTTOM_PAD = 8.4                            # axis line to the bottom of its x label
# band 2
Y2 = R1B + BOTTOM_PAD + 0.6
B2L = [Y2 + 2.9, Y2 + 2.9 + LINE]
R2, P2 = Y2 + 8.4, 7.6
R2B = R2 + 5 * P2
D_X0, D_W, D_G = LABR + 1.8, 17.0, 4.5     # gap widened so '80' and the next facet's '0' do not touch (F13)
D_XS = [D_X0 + j * (D_W + D_G) for j in range(3)]
D_END = D_XS[-1] + D_W
E_LET = D_END + 2.5
E_LABR = E_LET + 2.4 + LABR                 # 28 Oct review: e carries its own strategy names
E_X0, E_X1 = E_LABR + 1.8, W - 2.6
# band 3
Y3 = R2B + BOTTOM_PAD + 0.6
B3L = Y3 + 2.9
R3, SP, GG = Y3 + 4.4, 3.2, 1.0
R3B = R3 + 12 * SP + 5 * GG
F_SUBR = LABR + 3.2 + tw("judge pass")
F_X0, F_W = F_SUBR + 1.4, 34.0
F_X1 = F_X0 + F_W
F_NX = F_X1 + 1.2
G_LET = F_NX + tw("215") + 2.0
G_LABR = G_LET + 2.4 + LABR                 # g repeats the strategy names (critics D6, F11)
G_SUBR = G_LABR + 1.6 + tw("0\u20134")       # 28 Oct review: sub-rows '5' and '0-4' (en dash) under 'Faithfulness'
G_X0 = G_SUBR + 1.4
G_NX = W - 0.4 - tw("(n)")
G_X1 = G_NX - 1.2
H = round(R3B + BOTTOM_PAD + 0.6, 1)
if H > H_MAX:
    raise SystemExit(f"layout A is {H} mm high, over {H_MAX}")


def row_c1(i):
    return R1 + (i + 0.5) * P1


def row_c2(i):
    return R2 + (i + 0.5) * P2


def grp_top3(i):
    return R3 + i * (2 * SP + GG)


def sub_c3(i, j):
    return grp_top3(i) + (j + 0.5) * SP


def plan_layouts():
    """Layout A (built) and layout B ([a | b] / [c | d | e] / [f | g]) at the same 8 pt geometry: each band's header,
    rows and axis room in mm, and the panel boxes. B puts c beside d and e, so band 2 takes six rows at e's pitch."""
    hdr1, hdr2, hdr3 = R1 - Y1, R2 - Y2, R3 - Y3
    band1 = hdr1 + 6 * P1 + BOTTOM_PAD
    band2_a = hdr2 + 5 * P2 + BOTTOM_PAD
    band3 = hdr3 + 12 * SP + 5 * GG + BOTTOM_PAD
    band2_b = hdr2 + 6 * P2 + BOTTOM_PAD
    gaps = 2 * 0.6 + 0.6
    A_ = {"bands": ["a | b | c (six rows)", "d | e (five rows)", "f | g (six groups of two)"],
          "band_heights_mm": [round(band1, 1), round(band2_a, 1), round(band3, 1)],
          "height_mm": round(band1 + band2_a + band3 + gaps, 1),
          "panels_mm": {"a": [round(A_END - 0.0, 1), round(band1, 1)],
                        "b": [round(C_LET - B_LET, 1), round(band1, 1)],
                        "c": [round(W - C_LET, 1), round(band1, 1)],
                        "d": [round(E_LET, 1), round(band2_a, 1)],
                        "e": [round(W - E_LET, 1), round(band2_a, 1)],
                        "f": [round(G_LET, 1), round(band3, 1)],
                        "g": [round(W - G_LET, 1), round(band3, 1)]},
          "note": "a, d and f boxes include the shared strategy-name column (%.1f mm)" % (LABR + 1.8)}
    c_w = 2.0 + C_W + 1.2 + tw("34") + 2.0 + 2.0
    d_w = 3 * D_W + 2 * D_G
    e_min = 70.0
    B_ = {"bands": ["a | b (six rows)", "c | d | e (six rows; d and e leave single pass empty)", "f | g"],
          "band_heights_mm": [round(band1, 1), round(band2_b, 1), round(band3, 1)],
          "height_mm": round(band1 + band2_b + band3 + gaps, 1),
          "band2_width_mm": round(LABR + 1.8 + c_w + d_w + 4.0 + e_min, 1),
          "why_not": "band 2 must hold six rows at e's 7.6 mm pitch (three marks per row, dodged), so B is "
                     "%.1f mm high at 8 pt, over the 170 mm page; fitting it would need type under 8 pt or "
                     "panel e's rows under 6.3 mm, where its dodged draws overlap" % (band1 + band2_b + band3 + gaps)}
    return {"A": A_, "B": B_}


LAYOUTS = plan_layouts()
assert LAYOUTS["A"]["height_mm"] <= H_MAX + 0.01 and LAYOUTS["B"]["height_mm"] > H_MAX


# =====================================================================================================================
# drawing
# =====================================================================================================================
class Plate:
    def __init__(self, w=None, h=None):
        self.w, self.h = (w or W), (h or H)
        self.fig = plt.figure(figsize=(self.w / 25.4, self.h / 25.4), facecolor=WHITE)
        self.pg = self.fig.add_axes([0, 0, 1, 1])
        self.pg.set_axis_off()
        self.pg.set_xlim(0, self.w)
        self.pg.set_ylim(self.h, 0)
        self.pg.set_zorder(10)               # texts and swatches over every data axes (the page has no patch)
        self.printed = {}
        self.k = 0

    def axes(self, x, y, w, h, xlim):
        a_ = self.fig.add_axes([x / self.w, 1 - (y + h) / self.h, w / self.w, h / self.h])
        a_.patch.set_visible(False)
        a_.set_xlim(*xlim)
        a_.set_ylim(y + h, y)                # y in plate mm, downwards
        a_.set_yticks([])
        for s_ in ("top", "right", "left"):
            a_.spines[s_].set_visible(False)
        return a_

    def t(self, x, y, s, printed=None, why="a label", **kw):
        kw.setdefault("ha", "left")
        kw.setdefault("va", "baseline")
        txt = self.pg.text(x, y, s, **kw)
        if re.search(r"\d", s):
            gid = f"s448num_{self.k}"
            self.k += 1
            txt.set_gid(gid)
            self.printed[gid] = printed if printed else {"fixed": s, "why": why}
        return txt

    def letter(self, x, y, s):
        self.t(x, y, S457.LETTER_CASE(s), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT)

    def rect(self, x, y, w, h, col):
        self.pg.add_patch(Rectangle((x, y), w, h, facecolor=col, edgecolor="none", linewidth=0))

    def mark(self, x, y, s, size=1.4):
        mk = SIG_MK[s]
        self.pg.plot([x], [y], ls="none", marker=mk, ms=size * SIG_MS[mk] / MM_PT, mfc=SIG_COL[s], mec=WHITE,
                     mew=0.3, zorder=5)

    def sig_title(self, x, y, s, words, size=1.4):
        """A signal's name with its mark in front (x is the mark's left edge); used by e's key only (28 Oct review)."""
        w_ = size + 0.8 + tw(words)
        self.mark(x + size / 2, y - 1.0, s, size)
        self.t(x + size + 0.8, y, words)
        return x + w_


PL = Plate()
P = PL.t
DRAWN = {}           # every number drawn, per panel

# ---- shared strategy names
for i, c in enumerate(CONFIGS):
    P(LABR, row_c1(i), LABEL[c], ha="right", va="center_baseline", why="strategy name")
for i, c in enumerate(OTHERS):
    P(LABR, row_c2(i), LABEL[c], ha="right", va="center_baseline", why="strategy name")
    P(E_LABR, row_c2(i), LABEL[c], ha="right", va="center_baseline", why="strategy name")
for i, c in enumerate(CONFIGS):
    P(LABR, grp_top3(i) + SP, LABEL[c], ha="right", va="center_baseline", why="strategy name")
    P(G_LABR, grp_top3(i) + SP, LABEL[c], ha="right", va="center_baseline", why="strategy name")


# ---- a (28 Oct review: Tukey whiskers on every box, no means or intervals, plain column names, draws in the legend)
def tukey(vals, q25, q75):
    """Tukey's whisker ends: the most extreme values within 1.5 x IQR of the box."""
    iqr = q75 - q25
    lo = min(v for v in vals if v >= q25 - 1.5 * iqr - 1e-9)
    hi = max(v for v in vals if v <= q75 + 1.5 * iqr + 1e-9)
    return lo, hi


A_CAP_MM = 1.0                          # whisker cap height (mm)
A_COLLAPSED = []                        # (column, strategy, value, questions at that value, questions)


def draw_a(pl, judge_bar=False, sheet=None, drawn=None):
    """Panel a on Plate pl. judge_bar: the Judge column as a pass-rate bar under the dots (fig5_a_alt.png only)."""
    pl.letter(0.0, B1L[0], "a")
    for j, (col, sigk, qs, lim, ticks, xl, ref, dr, s_) in enumerate(A_SPECS):
        x0 = A_XS[j]
        span = lim[1] - lim[0]
        ax = pl.axes(x0, R1, A_W, 6 * P1, (lim[0] - 0.04 * span, lim[1] + 0.04 * span))
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{v:g}" for v in ticks])
        ax.set_xlabel(xl, labelpad=2)
        if re.search(r"\d", xl):                # S448 R8: a text with a digit is declared
            gid = f"s448num_{pl.k}"
            pl.k += 1
            ax.xaxis.label.set_gid(gid)
            pl.printed[gid] = {"fixed": xl, "why": "the judge score a pass needs (Rule 5, D154)"}
        mm_per = A_W / (span * 1.08)
        over = {}
        bar = judge_bar and col == "pass"
        for i, c in enumerate(CONFIGS):
            vals = [v for _, v in A[col]["rows"][c]]
            sm = A[col]["summary"][c]
            y = row_c1(i)
            off, ov = S457.swarm([(v - lim[0]) * mm_per for v in vals])
            over[c] = ov
            hb = S457.BOX_HALF_MM
            if bar:
                ax.barh(y, sm["mean"], left=0, height=2 * S457.DOT_HALF_MM + 0.6, color="#DDDDDD", lw=0, zorder=1)
                ax.plot([sm["mean"]] * 2, [y - S457.DOT_HALF_MM - 0.3, y + S457.DOT_HALF_MM + 0.3], color=BLACK,
                        lw=1.0, solid_capstyle="butt", zorder=5)
            ax.plot(vals, [y - o for o in off], ls="none", marker="o", ms=S457.DOT_MM / MM_PT, mfc=GREY, mew=0,
                    zorder=2)
            wlo, whi = tukey(vals, sm["quartile_25"], sm["quartile_75"])
            if not bar:
                for a_, b_ in ((wlo, sm["quartile_25"]), (sm["quartile_75"], whi)):
                    if b_ > a_:
                        ax.plot([a_, b_], [y, y], color=BLACK, lw=0.5, solid_capstyle="butt", zorder=5)
                for xe in (wlo, whi):
                    ax.plot([xe, xe], [y - A_CAP_MM / 2, y + A_CAP_MM / 2], color=BLACK, lw=0.5,
                            solid_capstyle="butt", zorder=5)
                ax.plot([sm["quartile_25"], sm["quartile_75"], sm["quartile_75"], sm["quartile_25"],
                         sm["quartile_25"]], [y - hb, y - hb, y + hb, y + hb, y - hb], color=BLACK, lw=0.5,
                        solid_joinstyle="miter", zorder=5)
                # a box of zero width (quartiles equal) is drawn as its median line, taller than the dots so it is
                # not read as one more column of dots (28 Oct review)
                hm = S457.DOT_HALF_MM + 0.5 if sm["quartile_75"] - sm["quartile_25"] < 1e-12 else hb
                ax.plot([sm["median"]] * 2, [y - hm, y + hm], color=BLACK, lw=1.0, solid_capstyle="butt", zorder=6)
                if sheet is not None and sm["quartile_75"] - sm["quartile_25"] < 1e-12:
                    A_COLLAPSED.append((col, c, sm["median"], sum(1 for v in vals if abs(v - sm["median"]) < 1e-9),
                                        len(vals)))
            if sheet is not None:
                sheet["rows"].append([LABEL[c], col, "key" if col != "papers" else "papers", "summary", None, None,
                                      sm["median"], sm["quartile_25"], sm["quartile_75"], wlo, whi, len(vals),
                                      A[col]["n"], dr])
                for q, v in A[col]["rows"][c]:
                    sheet["rows"].append([LABEL[c], col, "key" if col != "papers" else "papers", "question", q, v,
                                          None, None, None, None, None, None, None, dr])
            if drawn is not None:
                drawn.setdefault(col, {"n_questions": A[col]["n"], "draws": dr, "per_strategy": {},
                                       "dots_overlapping": over})
                drawn[col]["per_strategy"][LABEL[c]] = {
                    "summary": {"questions_n": len(vals), "median": sm["median"], "quartile_25": sm["quartile_25"],
                                "quartile_75": sm["quartile_75"], "whisker_low": wlo, "whisker_high": whi},
                    "per_question": A[col]["rows"][c]}
        pl.t(x0 + A_W / 2, B1L[2], ref, ha="center")        # plain column name (28 Oct review)


SHEET = {k: {"columns": None, "rows": []} for k in "abcdefg"}
SHEET["a"]["columns"] = ["strategy", "signal", "reference", "row", "question_id", "value", "median", "quartile_25",
                         "quartile_75", "whisker_low", "whisker_high", "n_questions", "n_questions_column", "draws"]
DRAWN["a"] = {"source": str(A_DATA), "columns": {}}
draw_a(PL, sheet=SHEET["a"], drawn=DRAWN["a"]["columns"])
assert [(k, LABEL[c]) for k, c, *_ in A_COLLAPSED] == [("pass", "single pass")], A_COLLAPSED
A_COLL_AT, A_COLL_N = A_COLLAPSED[0][3], A_COLLAPSED[0][4]

# ---- b
SHEET["b"]["columns"] = ["strategy"] + B_KEYS + ["papers_median_pooled"]
PL.letter(B_LET, B1L[0], "b")
SW = 3.0
# 28 Oct review: the key is a 2 x 2 grid, columns papers high / low, rows judge pass / fail ("papers high" defined in
# the legend: at or above the median of all 495 answers)
B_RH = B_LET + 3.0 + max(tw("judge pass"), tw("judge fail"))      # row headings end here (right-aligned)
B_CW = max(tw("papers high"), tw("papers low")) + 1.0              # cell width
B_CX = [B_RH + 1.0, B_RH + 1.0 + B_CW + 0.6]
B_KEY_END = B_CX[1] + B_CW
assert B_KEY_END < B_NX - 1.0, (B_KEY_END, B_NX)
B_GRID = {("pass", "high"): B_COLS[1], ("pass", "low"): B_COLS[3], ("fail", "high"): B_COLS[0],
          ("fail", "low"): B_COLS[2]}
for cx, hl in zip(B_CX, ("high", "low")):
    P(cx + B_CW / 2, B1L[0], f"papers {hl}", ha="center")
for yb, pf in zip(B1L[1:], ("pass", "fail")):
    P(B_RH, yb, f"judge {pf}", ha="right")
    for cx, hl in zip(B_CX, ("high", "low")):
        PL.rect(cx, yb - SW + 0.3, B_CW, SW, B_GRID[(pf, hl)])
axb = PL.axes(B_X0, R1, B_W, 6 * P1, (0, B_XMAX))
axb.set_xticks([0, 20, 40, 60, 80])
axb.set_xticklabels(["0", "20", "40", "60", "80"])
axb.set_xlabel("Answers (n)", labelpad=2)
MMB = B_W / B_XMAX
BAR1 = 4.0
B_UNPRINTED = []
P(B_NX, B1L[2], "(n)")
DRAWN["b"] = {"source": str(BPTS), "papers_median_pooled": B_MEDIAN, "answers_on_median": B_ON_MEDIAN,
              "counts": {}, "count_labels": []}
for i, c in enumerate(CONFIGS):
    yc = row_c1(i)
    SHEET["b"]["rows"].append([LABEL[c]] + B[c] + [B_MEDIAN])
    x0 = 0
    for k_, (v, col_) in enumerate(zip(B[c][:4], B_COLS)):
        axb.barh(yc, v, left=x0, height=BAR1, color=col_, lw=0, zorder=2)
        s = str(v)
        seg = v * MMB
        pr = {"sheet": "Fig. 5b", "row": i, "format": "{" + B_KEYS[k_] + "}"}
        if seg >= tw(s) + 0.6:
            P(B_X0 + (x0 + v / 2) * MMB, yc, s, printed=pr, ha="center", va="center_baseline")
            place = "inside"
        elif k_ == 0:
            # a count too narrow for its segment is not printed (story critic F9: left of zero it read as a tick
            # label); the legend says so and the Source Data holds it
            place = "not printed (segment too narrow)"
            B_UNPRINTED.append((LABEL[c], v))
        elif k_ == 3:
            P(B_X0 + (x0 + v) * MMB + 0.5, yc, s, printed=pr, ha="left", va="center_baseline")
            place = "outside right"
        else:
            raise SystemExit(f"b {c} segment {k_ + 1} ({v}) too narrow for its count")
        DRAWN["b"]["count_labels"].append([LABEL[c], B_KEYS[k_], v, place])
        x0 += v
    assert x0 == B[c][4]
    P(B_NX, yc, str(B[c][4]), printed={"sheet": "Fig. 5b", "row": i, "format": "{n}"}, va="center_baseline")
    DRAWN["b"]["counts"][LABEL[c]] = dict(zip(B_KEYS, B[c]))

# ---- c
SHEET["c"]["columns"] = ["strategy", "every_concept_judge_pass", "every_concept_judge_fail", "every_concept_n"]
PL.letter(C_LET, B1L[0], "c")
for (col_, words), yb in zip([(C_FAIL, "judge fails"), (C_PASS, "judge passes")], B1L[:2]):
    PL.rect(C_LET + 3.0, yb - SW + 0.3, SW, SW, col_)
    P(C_LET + 3.0 + SW + 0.8, yb, words)
P(C_NR, B1L[2], C_NHEAD, ha="right")
axc = PL.axes(C_X0, R1, C_W, 6 * P1, (0, C_XMAX))
axc.set_xticks([0, 10, 20, 30])
axc.set_xticklabels(["0", "10", "20", "30"])
C_XL = "Answers with every concept (n)"         # numbers critic D6: it counts answers, not concepts
assert C_X0 + C_W / 2 + tw(C_XL) / 2 < W - 0.3 and C_X0 + C_W / 2 - tw(C_XL) / 2 > B_X1 - 4.0, tw(C_XL)
axc.set_xlabel(C_XL, labelpad=2)
MMC = C_W / C_XMAX
DRAWN["c"] = {"source": str(FIGOPTS / "fig5_bc3/b8/points.json"), "every_concept": {}, "strategy_totals": {}}
for i, c in enumerate(CONFIGS):
    yc = row_c1(i)
    p_, f_ = C[c]["pass"], C[c]["fail"]
    SHEET["c"]["rows"].append([LABEL[c], p_, f_, p_ + f_])
    axc.barh(yc, p_, height=BAR1, color=C_PASS, lw=0, zorder=2)
    axc.barh(yc, f_, left=p_, height=BAR1, color=C_FAIL, lw=0, zorder=2)
    P(C_X0 + p_ / 2 * MMC, yc, str(p_), printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_pass}"},
      ha="center", va="center_baseline")
    if f_:
        assert f_ * MMC >= tw(str(f_)) + 0.6
        P(C_X0 + (p_ + f_ / 2) * MMC, yc, str(f_),
          printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_fail}"}, ha="center",
          va="center_baseline")
    else:
        P(C_X0 + p_ * MMC + 0.6, yc, "0", printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_fail}"},
          ha="left", va="center_baseline")
    P(C_NR, yc, str(p_ + f_), printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_n}"},
      ha="right", va="center_baseline")
    DRAWN["c"]["every_concept"][LABEL[c]] = C[c]
    DRAWN["c"]["strategy_totals"][LABEL[c]] = C_TOT[c]

# ---- d
SHEET["d"]["columns"] = ["strategy", "reference", "signal", "single_pass_higher", "tie", "strategy_higher",
                         "n_questions"]
PL.letter(0.0, B2L[0], "d")
kx = 3.5
for col_, words in ((D_COLS["sp"], "single pass higher"), (D_COLS["tie"], "tie"), (D_COLS["ot"], "strategy higher")):
    PL.rect(kx, B2L[0] - SW + 0.3, SW, SW, col_)
    P(kx + SW + 0.8, B2L[0], words)
    kx += SW + 0.8 + tw(words) + 2.6
D_KEY_END = kx - 2.6
DRAWN["d"] = {"source": str(C5), "drawn": {}}
BAR2 = 4.4
for j, s in enumerate(SIGS):
    x0 = D_XS[j]
    ax = PL.axes(x0, R2, D_W, 5 * P2, (0, 83))
    ax.set_xticks([0, 40, 80])
    ax.set_xticklabels(["0", "40", "80"])
    ax.tick_params(axis="x", pad=1.5)
    if j == 1:
        ax.set_xlabel("Questions (n)", labelpad=2)
    P(x0 + D_W / 2, B2L[1], SIGNAME[s], ha="center")      # plain column name (28 Oct review)
    DRAWN["d"]["drawn"][SIGNAME[s]] = {}
    for i, o in enumerate(OTHERS):
        m = D[(o, s)]
        yc = row_c2(i)
        ax.barh(yc, m["sp"], left=0, height=BAR2, color=D_COLS["sp"], lw=0, zorder=2)
        ax.barh(yc, m["tie"], left=m["sp"], height=BAR2, color=D_COLS["tie"], lw=0, zorder=2)
        ax.barh(yc, m["ot"], left=m["sp"] + m["tie"], height=BAR2, color=D_COLS["ot"], lw=0, zorder=2)
        DRAWN["d"]["drawn"][SIGNAME[s]][LABEL[o]] = {"single_pass_higher": m["sp"], "tie": m["tie"],
                                                      "other_higher": m["ot"], "n": m["n"]}
for o in OTHERS:
    for s in SIGS:
        m = D[(o, s)]
        SHEET["d"]["rows"].append([LABEL[o], "single pass", s, m["sp"], m["tie"], m["ot"], m["n"]])

# ---- e
SHEET["e"]["columns"] = ["strategy", "reference", "signal", "draw", "wins", "ties", "losses", "questions_with_both",
                         "margin_pct"]
PL.letter(E_LET, B2L[0], "e")
E_W = E_X1 - E_X0
axe = PL.axes(E_X0, R2, E_W, 5 * P2, (-100, 100))
axe.set_xticks([-100, -50, 0, 50, 100])
axe.set_xticklabels(["−100", "−50", "0", "50", "100"])
axe.set_xlabel("Strategy minus single pass (% of questions)", labelpad=2)     # 28 Oct review
axe.axvline(0, color=BLACK, lw=0.5, zorder=1)
for i in range(1, 5):
    yb = R2 + i * P2
    axe.plot([-100, 100], [yb, yb], color=SEP_GREY, lw=0.5, solid_capstyle="butt", zorder=0, clip_on=False)
P(E_X0, B2L[1], "single pass better")
P(E_X1, B2L[1], "strategy better", ha="right")
KEYTXT = {"judge": "Judge", "concept": "Concepts", "papers": "Papers"}     # one name per signal (F10, D6)
E_KEY_MS = 1.8                          # 28 Oct review: e's key at the top left, marks larger than the plotted ones
kx = E_LET + 3.0
for s in SIGS:
    kx = PL.sig_title(kx, B2L[0], s, KEYTXT[s], size=E_KEY_MS) + 3.0
assert kx - 3.0 < E_X1
SUB, DODGE, MSZ_MM = 1.7, 1.25, 1.25    # numbers critic D4: marks smaller and moved further apart, so no two overlap
SUBOFF = {"judge": -SUB, "concept": 0.0, "papers": SUB}
X_MM = E_W / 200.0
E_GAPS = []
DRAWN["e"] = {"source": "fig5_pull_1028 through S473 (as fig5_bc3/c8sep/build_c3_8.py)", "marks": [],
              "kendall_W": cc["W"], "kendall_W_exact_P": cc["P"]}
for i, c in enumerate(OTHERS):
    yc = row_c2(i)
    placed = []
    for s in SIGS:
        pts = sorted([x for x in E_DRAWN if x["strategy"] == c and x["signal"] == s], key=lambda z: z["draw"])
        tries = (0.0, -DODGE, DODGE) if s != "papers" else (0.0, DODGE, -DODGE)
        for x in pts:
            xm = (x["margin_pct"] + 100) * X_MM
            best = None
            for off in tries:
                y = yc + SUBOFF[s] + off
                gap = min([((xm - px) ** 2 + (y - py) ** 2) ** 0.5 for px, py in placed] + [9e9])
                if gap >= MSZ_MM * 0.98:
                    best = (off, y, gap)
                    break
                if best is None or gap > best[2]:
                    best = (off, y, gap)
            off, y = best[0], best[1]
            E_GAPS.append(best[2])
            assert abs(y - yc) + MSZ_MM * SIG_MS[SIG_MK[s]] * (2 ** 0.5 if s == "papers" else 1) / 2 < P2 / 2 - 0.2, (c, s)
            placed.append((xm, y))
            mk = SIG_MK[s]
            axe.plot([x["margin_pct"]], [y], ls="none", marker=mk, ms=MSZ_MM * SIG_MS[mk] / MM_PT, mfc=SIG_COL[s],
                     mec=WHITE, mew=0.3, zorder=3, clip_on=False)
            DRAWN["e"]["marks"].append({"row": LABEL[c], "signal": s, "draw": x["draw"], "margin_pct": x["margin_pct"],
                                        "wins": x["wins"], "ties": x["ties"], "losses": x["losses"], "n": x["n"],
                                        "dodge_mm": off, "y_mm": round(y, 3)})
for x in E_DRAWN:            # only the drawn pairs, against single pass (numbers critic D3)
    SHEET["e"]["rows"].append([LABEL[x["strategy"]], LABEL[x["reference"]], x["signal"], x["draw"], x["wins"],
                               x["ties"], x["losses"], x["n"], x["margin_pct"]])
E_MIN_GAP = min(E_GAPS)
assert E_MIN_GAP >= MSZ_MM * 0.98, E_MIN_GAP

# ---- f
SHEET["f"]["columns"] = (["strategy", "judge"] + [f"faithfulness_{k}" for k in range(6)] + ["n"]
                         + [f"share_pct_{k}" for k in range(6)])
PL.letter(0.0, B3L, "f")
kx = 3.5
P(kx, B3L, "Faithfulness score")
kx += tw("Faithfulness score") + 1.6
for k_ in range(6):
    PL.rect(kx, B3L - 2.4 + 0.3, 2.6, 2.4, COLS6[k_])
    P(kx + 3.0, B3L, str(k_), why="faithfulness score of the swatch")
    kx += 3.0 + tw(str(k_)) + 1.8
F_KEY_END = kx - 1.8
P(F_NX, B3L, "(n)")
axf = PL.axes(F_X0, R3, F_W, R3B - R3, (0, 100))
axf.set_xticks([0, 50, 100])
axf.set_xticklabels(["0", "50", "100"])
axf.set_xlabel("Answers (%)", labelpad=2)
DRAWN["f"] = {"source": str(FIGOPTS / "fig5_d/d_data.json"), "per_strategy": {}}
BAR3 = 0.78 * SP
for i, c in enumerate(CONFIGS):
    DRAWN["f"]["per_strategy"][LABEL[c]] = {}
    for j, word in enumerate(("pass", "fail")):
        yc = sub_c3(i, j)
        cnt, n = F[(c, word)]["counts"], F[(c, word)]["n"]
        left = 0.0
        for k_ in range(6):
            w_ = 100 * cnt[k_] / n if n else 0
            if w_ > 0:
                axf.barh([yc], [w_], left=[left], height=BAR3, color=COLS6[k_], lw=0, zorder=2)
            left += w_
        row_i = len(SHEET["f"]["rows"])
        SHEET["f"]["rows"].append([LABEL[c], word] + cnt + [n] + [100 * x / n for x in cnt])
        P(F_SUBR, yc, f"judge {word}", ha="right", va="center_baseline")
        P(F_NX, yc, str(n), printed={"sheet": "Fig. 5f", "row": row_i, "format": "{n}"}, va="center_baseline")
        DRAWN["f"]["per_strategy"][LABEL[c]][word] = {"n": n, "counts_faith_0_to_5": cnt,
                                                      "share_pct_0_to_5": [100 * x / n for x in cnt]}

# ---- g
SHEET["g"]["columns"] = ["strategy", "faithfulness", "row", "question_id", "papers_precision", "n", "quartile_25",
                         "median", "quartile_75"]
PL.letter(G_LET, B3L, "g")
P(G_NX, B3L, "(n)")
P(G_SUBR, B3L, "Faithfulness", ha="right")     # 28 Oct review: one heading over the sub-rows
G_W = G_X1 - G_X0
axg = PL.axes(G_X0, R3, G_W, R3B - R3, (-0.04, 1.04))
axg.set_xticks([0, 0.5, 1])
axg.set_xticklabels(["0", "0.5", "1"])
axg.set_xlabel("Papers precision", labelpad=2)
mm_x = G_W / 1.08
DRAWN["g"] = {"source": str(FIGOPTS / "fig5_e/e_data.json"), "n_answers": G_N, "n_questions": G_NQ, "rows": []}
for idx, g in enumerate(G):
    i, j = CONFIGS.index(g["strategy"]), (0 if g["grp"] == "5" else 1)
    yc = sub_c3(i, j)
    v = g["values"]
    off, over = S457.swarm([x * mm_x for x in v], half=1.1, pitch=0.5, dot=S457.DOT_MM)
    axg.plot(v, [yc + o for o in off], ls="none", marker="o", ms=S457.DOT_MM / MM_PT, mfc=GREY, mew=0, zorder=7)
    qe = g["q_exact"]
    hb = 0.9
    axg.add_patch(Rectangle((qe["q25"], yc - hb), qe["q75"] - qe["q25"], 2 * hb, fill=False, ec=BLACK, lw=0.5,
                            joinstyle="miter", zorder=5))
    axg.plot([qe["median"]] * 2, [yc - hb, yc + hb], color=BLACK, lw=1.0, solid_capstyle="butt", zorder=6)
    row_i = len(SHEET["g"]["rows"])
    SHEET["g"]["rows"].append([LABEL[g["strategy"]], g["grp"], "summary", None, None, len(v), qe["q25"],
                               qe["median"], qe["q75"]])
    for q, x in zip(g["qids"], v):
        SHEET["g"]["rows"].append([LABEL[g["strategy"]], g["grp"], "answer", q, x, None, None, None, None])
    P(G_SUBR, yc, "5" if g["grp"] == "5" else "0\u20134", ha="right", va="center_baseline",
      why="faithfulness score group")
    P(G_NX, yc, str(len(v)), printed={"sheet": "Fig. 5g", "row": row_i, "format": "{n}"}, va="center_baseline")
    DRAWN["g"]["rows"].append({"strategy": LABEL[g["strategy"]], "faithfulness": g["grp"], **g["q"],
                               "dots_overlapping": over, "values": v})

# header pieces must not run into each other (finish_plate checks text; these check swatches and keys)
assert D_KEY_END < E_LET - 1.0, (D_KEY_END, E_LET)
assert F_KEY_END < F_NX - 1.0, (F_KEY_END, F_NX)
assert B_KEY_END < C_LET - 1.0

# =====================================================================================================================
# files
# =====================================================================================================================
PULLJ = json.loads((PULL / "PULL.json").read_text())
STAMP = (f"28 Oct 2026 pull fig5_pull_1028 (ended {PULLJ.get('ended_utc')}), S3 collect run_sha256 "
         f"{str(read['run_sha256'])[:12]}; MiniCheck papers draw 1 on {len(QW)} complete question blocks; concept "
         f"recall on the loose matcher; assembled 28 Oct from seven scratch builds")
assert not STAMP.upper().startswith("PROVISIONAL")
paths = {k: HERE / f"{STAMP_FILE}.{k}" for k in ("pdf", "svg", "png")}
S457.finish_plate(PL.fig, W, H, paths, title="Figure 5")

SHEETS = {f"Fig. 5{k}": SHEET[k] for k in "abcdefg"}
from openpyxl import Workbook  # noqa: E402

wb = Workbook()
wb.remove(wb.active)
for name, sh in SHEETS.items():
    ws = wb.create_sheet(name)
    ws.append(sh["columns"])
    for r in sh["rows"]:
        assert len(r) == len(sh["columns"]), (name, r)
        ws.append(r)
WB = HERE / "Source Data Fig. 5.xlsx"
wb.save(WB)
CAP = HERE / "Source Data Fig. 5 caption.md"
CAP.write_text(
    "# Source Data Fig. 5, caption\n\n"
    "**Source Data Fig. 5 | Numerical values plotted in Figure 5.** Provisional (the plate is the provisional "
    f"assembly of 28 October). Data stamp: {STAMP}. One sheet per panel. "
    "Fig. 5a: per strategy and signal a summary row (median, quartiles, Tukey whisker ends, questions) and one row "
    "per plotted question. Fig. 5b: per strategy the draw-1 "
    "answers in the four groups of the judge's verdict and the papers' precision against the pooled median. Fig. 5c: "
    "per strategy the draw-1 answers that state every key concept, by the judge's verdict, and their total. "
    "Fig. 5d: per strategy and signal the questions where single pass scores higher, ties and where the strategy "
    "scores higher. Fig. 5e: per strategy against single pass, signal and draw, the wins, ties, losses, questions "
    "and the margin. Fig. 5f: per strategy and judge verdict the answers at each "
    "faithfulness score and their share. Fig. 5g: per strategy and faithfulness group a summary row (n, quartiles, "
    "median) and one row per plotted answer. Generated by build_fig5.py in figopts_1028/fig5_assembled.\n\n"
    "Proposed Data Availability sentence: \"The source data for Figure 5 is in Supplementary Data [Y].\"\n")
NUMF = HERE / "figure5_numbers.json"
NUMF.write_text(json.dumps({"stamp": STAMP, "what": "Figure 5 assembled, Source Data values and printed numbers",
                            "sheets": SHEETS, "printed": PL.printed}, indent=1, default=float) + "\n")

# ---- legend
N_C = sum(C[c]["pass"] + C[c]["fail"] for c in CONFIGS)
pap82 = [LABEL[o] for o in OTHERS if D[(o, "papers")]["n"] == 82]
assert pap82 == ["multi-hop", "RLM-5", "RLM-10"]
assert all(D[(o, s)]["n"] == 83 for o in OTHERS for s in ("judge", "concept"))
assert all(D[(o, "papers")]["n"] == 83 for o in OTHERS if LABEL[o] not in pap82)
assert A["pass"]["n"] == 86 and A["concept"]["n"] == 86 and A["papers"]["n"] == 83
# ---- checks behind the legend's sentences (fixes of 28 Oct)
RLM = ("rlm_5", "rlm_10", "rlm_20")
c_rlm_fail = [p["judge"] for p in PTS_C if p["strategy"] in RLM and p["concept_recall"] == 1 and not p["pass"]]
assert len(c_rlm_fail) == sum(C[c]["fail"] for c in RLM) == 19, len(c_rlm_fail)
C_RLM_AT3 = sum(1 for v in c_rlm_fail if v == 3)
assert C_RLM_AT3 == 18 and sorted(set(c_rlm_fail)) == [0, 3], sorted(c_rlm_fail)
# "single draws tie more often than three-draw means, so e's margins are shorter than d's" (judge and concepts)
E_VS_D = []
for o in OTHERS:
    for s in ("judge", "concept"):
        m = D[(o, s)]
        d_net = 100.0 * (m["ot"] - m["sp"]) / m["n"]
        for x in E_DRAWN:
            if x["strategy"] == o and x["signal"] == s:
                E_VS_D.append((LABEL[o], s, x["draw"], m["tie"], x["ties"], round(d_net, 1), round(x["margin_pct"], 1)))
E_SHORTER = sum(1 for r in E_VS_D if abs(r[6]) < abs(r[5]))
E_MORE_TIES = sum(1 for r in E_VS_D if r[4] > r[3])
assert all(D[(o, "papers")]["n"] == 83 or LABEL[o] in ("multi-hop", "RLM-5", "RLM-10") for o in OTHERS)
pap82_a = [c for c in CONFIGS if A["papers"]["summary"][c]["n"] == 82] if "n" in A["papers"]["summary"]["single_pass"] \
    else [c for c in CONFIGS if len(A["papers"]["rows"][c]) == 82]
assert [LABEL[c] for c in pap82_a] == ["multi-hop", "RLM-5", "RLM-10"], pap82_a
assert all(len(A[k]["rows"][c]) == 86 for k in ("pass", "concept") for c in CONFIGS)
F_NQ = len({r["question_id"] for r in F_OK})
from collections import Counter  # noqa: E402
F_OUT = {c: Counter(r["faith_status"] for r in DF["rows"] if r["strategy"] == c and r["faith_status"] != "ok")
         for c in CONFIGS}
F_OUT = {c: {"no_answer": F_OUT[c].get("no_answer", 0), "error": F_OUT[c].get("error", 0)} for c in CONFIGS}
assert all(sum(F_OUT[c].values()) == len([r for r in DF["rows"] if r["strategy"] == c and r["faith_status"] != "ok"])
           for c in CONFIGS)
assert all(F[(c, "pass")]["n"] + F[(c, "fail")]["n"] + sum(F_OUT[c].values()) == F_NQ * 3 for c in CONFIGS)
assert not B_UNPRINTED or B_UNPRINTED == [("multi-hop", 1)], B_UNPRINTED
LEGEND = (
    "**Figure 5 | Three evaluation signals and the judge's faithfulness score on the answers of six generation "
    "strategies.** "
    "Answers of gemini-3-flash-preview to the answerable questions. Judge, the judge's correctness score against the "
    "answer key (pass at 4 or more of 5); Concepts, concept recall, the share of the key's concepts an answer states; "
    "Papers, MiniCheck precision, the share of an answer's claims the source papers support. "
    "**a**, Each signal per strategy: grey dots, questions; box, quartiles; black line, median; whiskers, the most "
    "extreme questions within 1.5 box widths of the box. Judge (pass rate) and Concepts, three draws, "
    f"n = {A['pass']['n']} questions; Papers, draw 1, n = {A['papers']['n']} questions (82 for multi-hop, RLM-5 and "
    f"RLM-10). Single pass's Judge box is a line at 100, where {A_COLL_AT} of {A_COLL_N} questions sit. "
    f"**b**, Draw-1 answers to {len(QW)} questions (n = {len(PTS_B)} answers), by the judge's verdict and by Papers "
    f"precision: high, at or above the median of all {len(PTS_B)} answers ({S457.half_up(B_MEDIAN, 3)}); low, "
    "below it. Multi-hop's 1 fail-high answer is unlabelled. "
    f"**c**, Of the same answers, those that state every key concept, by the judge's verdict (n = {N_C}); n at right "
    "counts only these answers, so it differs by strategy. Of the 19 RLM answers the judge fails, "
    f"{C_RLM_AT3} score 3. "
    "**d**, Questions where single pass or the strategy scores higher, and ties, per signal (Judge and Concepts, "
    f"per-question means of three draws; Papers, draw 1); n = {len(QW)} questions (Papers, as in a). "
    "**e**, Questions won minus lost against single pass, as a percentage, one mark per draw (Papers, draw 1); n as "
    "in d. In d and e the judge compares 0 to 5 scores, not a's pass rate. "
    "**f**, **g**, The judge's faithfulness score, given after reading the retrieved passages. **f**, Answers the "
    f"judge passes and fails on correctness, {F_NQ} questions, three draws; n at right, excluding answers with no text "
    f"or a failed faithfulness call. **g**, Papers precision of draw-1 answers with faithfulness 5 and below 5 "
    f"(n = {G_N} answers, {G_NQ} questions; n at right); dots (answers), boxes and median lines as in a, no "
    "whiskers."
)
n_words = len(LEGEND.split())
assert E_MORE_TIES == len(E_VS_D) == 30      # the legend's "single draws tie more often" holds for every mark
assert [LABEL[c] for c in pap82_a] == pap82   # d's papers n equal a's ("as in a")
assert n_words < 350, (n_words, LEGEND)
(HERE / "legend.md").write_text(LEGEND + "\n")
(HERE / "legend_draft.md").write_text(
    "# Figure 5, title and legend (draft)\n\n"
    f"Written by build_fig5.py (figopts_1028/fig5_assembled). Data stamp: {STAMP}.\n\n" + LEGEND + "\n")

METHODS = [
    ("all panels", "Concept recall is L3's loose matcher (D12), provisional until P2's labels choose the matcher. "
                   "MiniCheck precision is against the whole source papers, draw 1 only; the papers question set is "
                   f"S473's W set, the {len(QW)} answerable questions whose six draw-1 answers all have an L1 papers "
                   "row. A judge answer with no text scores 0 (Rule 10)."),
    ("a", "Per question, the judge's pass share over its three draws (score 4 or more) and concept recall as the mean "
          "of its three draws (Rule 7); MiniCheck precision from draw 1. Quartiles and median by numpy percentile "
          "(linear), as S457.summary. Whiskers (Tukey): from the box to the most extreme question value within 1.5 x "
          "the interquartile range of the box, black, 0.5 pt, with caps, drawn over the grey dots; a whisker of zero "
          "length shows its cap only. No means or intervals (28 Oct review: the boxes already show the spread). "
          f"Single pass's Judge box has zero width: its quartiles and median are 100, where {A_COLL_AT} of "
          f"{A_COLL_N} questions sit, so it is drawn as the median line. Column names are plain text; the draws and "
          "the n per strategy are in the legend (82 papers questions for multi-hop, RLM-5 and RLM-10, each missing "
          "one W question: multi-hop no claim sentence, RLM-5 and RLM-10 no answer, 02_snakemake_CO2). "
          "fig5_a_alt.png (not in the plate) draws the Judge column as a bar of the pass rate (the mean of the "
          "question shares, Rule 2) under the dots, since a question's judge value takes only 0, 33, 67 or 100."),
    ("b", f"Papers above the median: MiniCheck precision at or above {B_MEDIAN:.4f}, the median of all {len(PTS_B)} "
          f"draw-1 answers of the six strategies pooled; the {B_ON_MEDIAN} answers exactly on it count as above. "
          "In the key, papers high = at or above this median, papers low = below it. "
          "Judge pass = correctness 4 or more. n per strategy: " + ", ".join(f"{LABEL[c]} {B[c][4]}" for c in CONFIGS)
          + " (one answer each of multi-hop, RLM-5 and RLM-10 has no papers score). Light grey: judge passes and "
          "papers at or above the median; dark grey: judge fails and papers below. Reddish purple (judge passes, "
          "papers below) replaces the scratch build's vermillion, which read as the concepts orange. Counts too "
          "narrow for their segment are not printed: " + ", ".join(f"{a_} {v_}" for a_, v_ in B_UNPRINTED) + "."),
    ("c", "Every key concept: concept recall 1 (loose matcher). The n at right counts the strategy's answers that state "
          "every concept, not all its answers, so it differs by strategy (header 'n, all concepts'). Judge fails = correctness 3 or less. Three answers of the 498 are left "
          f"out (no MiniCheck score), so the set equals b's. Of the 19 RLM answers the judge fails, {C_RLM_AT3} score "
          "3 and one scores 0 (17_brucellosis_ethiopia_FR1, RLM-5); at a pass mark of 3 the 19 would be 1 "
          "(fig5_bc3/b8/critic/critic_robust.txt)."),
    ("d", "Per question: judge correctness (0 to 5) and concept recall averaged over draws 1 to 3; MiniCheck precision "
          "from draw 1; higher = strictly higher, tie = equal to 1e-9 (prep_c5.py). Colours: reddish purple, single "
          "pass higher; grey, tie; bluish green, strategy higher (changed from c5's orange and blue, which are the "
          "concept and judge colours). Column names are plain text (28 Oct review)."),
    ("e", "Margin = (wins minus losses) / (wins + ties + losses) x 100 for draw d of the strategy against draw d of "
          "single pass, on the W questions where both values exist; ties count in the denominator only. The judge "
          "compares the 0 to 5 scores, not the pass rate of a. Within a row Judge marks sit highest and Papers lowest "
          "(left the legend on 28 Oct for length). Single draws tie more often than d's three-draw means, so e's "
          "margins differ from d's bars. Marks closer than one marker width are moved up or "
          f"down (never sideways): marks {MSZ_MM} mm, offsets {DODGE} mm, closest centres {E_MIN_GAP:.2f} mm apart, "
          "so no two marks overlap. Against d: in " + f"{E_SHORTER} of {len(E_VS_D)}" + " judge and concept marks "
          "e's margin is shorter than d's net share, and in " + f"{E_MORE_TIES} of {len(E_VS_D)}" + " the draw has "
          "more ties than d's three-draw means. Grey lines separate the strategies (version A; Q17 open). e repeats "
          "the strategy names and its key sits at the top left; the x axis reads 'Strategy minus single pass "
          "(% of questions)'. Kendall's W over the "
          f"three rankings of the six strategy means: W = {S457.half_up(cc['W'], 2)}, exact one-sided P = "
          f"{S457.half_up(cc['P'], 3)} (in the legend of the repository plate; not drawn here)."),
    ("f", "Faithfulness from the judge's call with passages (S3 'b'); pass = correctness of the plain call 4 or more "
          "(Rule 5). Answers with no text and unscored faithfulness calls are left out, as in S473's panel d: "
          + "; ".join(f"{LABEL[c]} {F_OUT[c]['no_answer']} with no text, {F_OUT[c]['error']} ended in an error"
                      for c in CONFIGS if sum(F_OUT[c].values())) + f" (each strategy has {F_NQ} x 3 = "
          + f"{F_NQ * 3} answers)."),
    ("g", "Answers with a scored faithfulness call and a MiniCheck precision (draw 1, every L1 papers row, so 86 "
          "questions here against b's 83). Swarm half width 1.1 mm; quartiles by numpy percentile (linear). g repeats "
          "the strategy names; one heading 'Faithfulness' over sub-rows '5' and '0\u20134' (28 Oct review)."),
]
(HERE / "methods_notes.md").write_text(
    "# Figure 5 (assembled), notes for the Methods\n\nDetail that left the legend to keep it under 350 words.\n\n"
    + "\n".join(f"- **{k}**: {v}" for k, v in METHODS) + "\n")

PROV = HERE / "figure5_provenance.json"
listed = [paths["pdf"], paths["svg"], paths["png"], WB, CAP, NUMF, HERE / "legend_draft.md"]
PROV.write_text(json.dumps({
    "provenance": {"script": str(Path(__file__).resolve()), "script_sha256": sha(Path(__file__).resolve())},
    "stamp": STAMP, "page_mm": [W, H], "inputs": SOURCES,
    "files": {p.name: sha(p) for p in listed}}, indent=1) + "\n")

# ---- numbers.json: every drawn number with its source, the scratch comparison and the layout plan
(HERE / "numbers.json").write_text(json.dumps({
    "what": "Figure 5 assembled (scratch, 28 Oct): every drawn number per panel, with the file it comes from",
    "stamp": STAMP, "plate_mm": [W, H],
    "panels": DRAWN,
    "scratch_comparison": {"compared_with": {
        "a": "fig5_a/a1_three_signals.numbers.json (summaries and per-question values)",
        "b": "fig5_bc2/b6/b6_bars_numbers.json (counts, pooled median)",
        "c": "fig5_bc3/b8/numbers.json (b.every_concept_by_strategy, b.strategy_totals)",
        "d": "fig5_bc2/c5/c5_numbers.json (drawn)",
        "e": "fig5_bc3/c8sep/fig5c3-8A_numbers.json (drawn: margin, wins, ties, losses, n; W and P)",
        "f": "fig5_d/d3_pass_fail_numbers.json (per_strategy n and counts)",
        "g": "fig5_e/e4_by_strategy.numbers.json (rows: n, quartiles, median, min, max, values)"},
        "differences": DIFFS},
    "reproduced": E_REP,
    "layout_chosen": "A",
    "layout_plan": LAYOUTS,
    "geometry_mm": {"label_column_right": round(LABR, 2), "band1": [Y1, R1, R1B], "band2": [Y2, R2, R2B],
                    "band3": [Y3, R3, R3B], "a_columns_x": [round(x, 2) for x in A_XS], "a_column_w": A_W,
                    "b_bars_x": [round(B_X0, 2), round(B_X1, 2)], "c_bars_x": [round(C_X0, 2), round(C_X1, 2)],
                    "d_facets_x": [round(x, 2) for x in D_XS], "d_facet_w": D_W,
                    "e_names_right": round(E_LABR, 2), "e_plot_x": [round(E_X0, 2), round(E_X1, 2)], "f_bars_x": [round(F_X0, 2), round(F_X1, 2)],
                    "g_plot_x": [round(G_X0, 2), round(G_X1, 2)],
                    "row_pitch": {"band1": P1, "band2": P2, "band3_sub": SP, "band3_group_gap": GG}},
    "legend_words": n_words,
    "a_collapsed_boxes": A_COLLAPSED,
    "f_left_out": F_OUT,
    "sources": SOURCES,
}, indent=1, default=float) + "\n")


# ---- layout sketch: A and B as boxes with their sizes (a plan, not a plate)
def sketch():
    fig, axs = plt.subplots(1, 2, figsize=(10, 5.2))
    for ax_, key in zip(axs, ("A", "B")):
        L_ = LAYOUTS[key]
        hs = L_["band_heights_mm"]
        ax_.set_xlim(-5, 190)
        ax_.set_ylim(max(180, L_["height_mm"] + 8), -14)
        ax_.set_aspect("equal")
        ax_.axis("off")
        ax_.add_patch(Rectangle((0, 0), 183, 170, fill=False, ec="#000000", lw=0.8, ls=(0, (3, 2))))
        y = 0
        if key == "A":
            boxes = [[("a", A_END), ("b", C_LET - A_END), ("c", W - C_LET)],
                     [("d", E_LET), ("e", W - E_LET)], [("f", G_LET), ("g", W - G_LET)]]
        else:
            boxes = [[("a", A_END), ("b", W - A_END)],
                     [("c", 40.2 + LABR), ("d", 3 * D_W + 2 * D_G + 4), ("e", W - 40.2 - LABR - 3 * D_W - 2 * D_G - 4)],
                     [("f", G_LET), ("g", W - G_LET)]]
        for band, hb_ in zip(boxes, hs):
            x = 0
            for name, wd in band:
                ax_.add_patch(Rectangle((x, y), wd, hb_, fill=True, fc="#EEEEEE", ec="#000000", lw=0.6))
                ax_.text(x + wd / 2, y + hb_ / 2, f"{name}\n{wd:.0f} x {hb_:.0f}", ha="center", va="center", fontsize=8)
                x += wd
            y += hb_ + 0.6
        ok = "fits" if L_["height_mm"] <= H_MAX else "over 170 mm"
        ax_.set_title(f"Layout {key}: {L_['height_mm']:.1f} mm high ({ok})", fontsize=9)
    fig.savefig(HERE / "layout_sketch.png", dpi=150)
    plt.close(fig)


sketch()


# ---- fig5_a_alt.png: panel a with the Judge column as a pass-rate bar (28 Oct review; to compare, not in the plate)
def alt_a():
    pl = Plate(A_END + 0.4, round(R1B + BOTTOM_PAD + 0.6, 1))
    for i, c in enumerate(CONFIGS):
        pl.t(LABR, row_c1(i), LABEL[c], ha="right", va="center_baseline")
    draw_a(pl, judge_bar=True)
    with tempfile.TemporaryDirectory(prefix="fig5alt_") as td:
        S457.finish_plate(pl.fig, pl.w, pl.h, {"pdf": Path(td) / "a.pdf", "svg": Path(td) / "a.svg",
                                                "png": HERE / "fig5_a_alt.png"}, title="Figure 5a alternative")
    return [pl.w, pl.h]


ALT_MM = alt_a()
print(json.dumps({"plate_mm": [W, H], "alt_a_mm": ALT_MM, "legend_words": n_words, "printed": len(PL.printed),
                  "e_vs_d": {"shorter": E_SHORTER, "more_ties": E_MORE_TIES, "of": len(E_VS_D), "rows": E_VS_D},
                  "e_min_gap_mm": E_MIN_GAP, "a_collapsed": A_COLLAPSED, "b_unprinted": B_UNPRINTED,
                  "layout": {k: v["height_mm"] for k, v in LAYOUTS.items()},
                  "differences": {k: len(v) for k, v in DIFFS.items()}}, indent=1))
