#!/usr/bin/env python3
"""S532: Supplementary Figure 5, answers to the false-premise questions, by strategy and corpus size (supp.md section 11).

One command, from the repository root:
    uv run --frozen python scripts/S532_supp4_false_premise.py plate [--out <folder>]
    uv run --frozen python scripts/S448_figure_rules_check.py --figure 4 --supplementary \
        --dir findings/figures_provisional/supp_fig5_false_premise
    uv run --frozen python scripts/S532_supp4_false_premise.py selftest
    uv run --frozen python scripts/S532_supp4_false_premise.py mutants

WHAT IT READS.
  a and b (G1, every draw): S463.read_collect on findings/recompute/fig2_inputs/g1_collect.jsonl, then S463.judge_rows
    with s6_root findings/recompute/fig3_s6_inputs, which reads every answer through scripts/judge_rows_v25.py
    (JR.choose(..., all_draws=True)): an answer's key v2.5 judge row where one exists, else its key v2.4 row. No second
    reader of judge rows. Judge devstral-small-2:24b, plain call (a), the answerable prompt (Rule 8): correctness against
    the key's refutation.
  c (G4, draw 1): findings/recompute/G4_fig3c_d185/q66_tables.json `false_premise`, written by S514 g4c: k of n per
    strategy and size, per index, and the answers awaiting S6G4. This script reads the table and draws it.

REPRODUCE FIRST (README.md:75-79; any difference exits 2 and nothing is written).
  (1) On key v2.4, every pass and fail answer key of the ten questions at scores 4 and 3 equals the false_premise lists
      of Figure 3's ranking.json as committed at RANKING_AT (its copy pinned in the tree, O3, so a later rebuild of that plate on key
      v2.5 does not move this anchor).
  (2) On key v2.5: 180 answers, 108 on changed questions, 163 pass at 4, per strategy 30, 28, 28, 26, 25, 26
      (facts_behind_notes.txt:485, :489).
  (3) q66: exactly the five ids OOD_041, 042, 044, 045, 049, and n = 15 at every cell.

Rule 9 (experiments/LIST.md:353-370): counts k of n, no interval, no test, no ranking. Rule 10: a failed answer counts as
a fail. S4c is the one home of the five false-premise questions (supp.md C5).

WRITES findings/figures_provisional/supp_fig5_false_premise/: "Supplementary Figure 5".{pdf,svg,png},
"Supplementary Figure 5 data".xlsx (sheets 4a, 4b, 4c), its caption, supplementary_figure5_numbers.json,
supplementary_figure5_provenance.json, legend_draft.md. k of N counts a and b's 180 answers, all on their final key, and
c's 360 answers less those awaiting S6G4. No model call.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import logging
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import pinned_history as PH  # noqa: E402


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S463 = _load("S463", ROOT / "scripts" / "S463_fig2_ranking.py")       # read_collect, judge_rows, key_groups, rerun_keys
S457 = S463.S457                                                       # finish_plate, plate_rc, G1, wcag, FLOCK
import fig_repro as FR  # noqa: E402
import house_style as hs  # noqa: E402

SCRIPT = "scripts/S532_supp4_false_premise.py"
SUPP_N = 5                                         # D302 (6 before; 4 before D257)
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig5_false_premise"
PLATE = S457.FLOCK["files"]["supplementary_name"].format(n=SUPP_N)
SIDE = f"supplementary_figure{SUPP_N}"
SHEET = f"Supplementary Fig. {SUPP_N}"
INPUTS = ROOT / "findings" / "recompute" / "fig2_inputs"
COLLECT = INPUTS / "g1_collect.jsonl"
S6_ROOT = ROOT / "findings" / "recompute" / "fig3_s6_inputs"
Q66 = ROOT / "findings" / "recompute" / "G4_fig3c_d185" / "q66_tables.json"
RANKING_PATH = "findings/figures_provisional/fig3_strategies/ranking.json"
RANKING_AT = "94262a0e"                        # Stage 0's last commit: the plate on key v2.4, the anchor of (1)
INDEX = "exp_v4_s20_n0"
STRATS = S457.G1                               # the six strategies, Figure 3's order (no ranking, Rule 9)
DRAWS = (1, 2, 3)
T_MAIN, T_RELAX = 4, 3                         # Rule 9 (D160 (11)): pass at correctness 4, 3 the relaxed threshold
SIZES = (5, 10, 20, 50)
Q5_WANT = ("OOD_041", "OOD_042", "OOD_044", "OOD_045", "OOD_049")
V25_WANT = {"answers": 180, "changed": 108, "passed_4": 163,
            "per_strategy": {"single_pass": 30, "multi_hop": 28, "verified_pass": 28, "rlm_5": 26, "rlm_10": 25,
                             "rlm_20": 26}}
# Our short wording of each false premise, for the row labels; the question's own words are in the key, not here
SHORT = {"OOD_041": "Sarek: Illumina short reads only", "OOD_042": "fastp: separate tools, several passes",
         "OOD_043": "DESeq2: raw counts, no normalization", "OOD_044": "Snakemake: first-come job queue",
         "OOD_045": "nf-core: CRAM raised storage by 65%", "OOD_046": "Salmon: full alignment to the genome",
         "OOD_047": "LSD Nepal: pregnant cows at lower risk", "OOD_048": "HPAI: same signs in every species",
         "OOD_049": "MultiQC: one tool at a time", "OOD_050": "Rabies: uniform vaccination coverage"}
C_HEADS = {"single_pass": ("single", "pass"), "multi_hop": ("multi-", "hop"), "verified_pass": ("verified", "pass"),
           "rlm_5": ("RLM-", "5"), "rlm_10": ("RLM-", "10"), "rlm_20": ("RLM-", "20")}
A_COLS = ["row", "threshold", "strategy", "strategy_label", "question_id", "short_claim", "draws_passed", "of_draws",
          "passed", "of_answers", "pass_keys", "fail_keys", "key_versions"]
B_COLS = ["row", "strategy", "strategy_label", "draw", "questions_passed", "of_questions", "mean_of_draws"]
C_COLS = ["row", "core_papers", "index", "strategy", "strategy_label", "passed_4", "passed_3", "n", "answers_by_status",
          "awaiting_s6_n"]


class Refused(Exception):
    """Refused before anything is written (exit 2)."""


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def passed(c: dict, t: int) -> int:
    """Rule 10: a failed or unscored answer counts as a fail."""
    return int(c["kind"] == "scored" and c["score"] >= t)


def tally(cells: dict, qf: list) -> dict:
    """Per threshold and strategy: draws passed per question, questions passed per draw, pass and fail keys."""
    res = {}
    for t in (T_MAIN, T_RELAX):
        per = {}
        for s, _ in STRATS:
            per_q = {q: [passed(cells[(s, q, d)], t) for d in DRAWS] for q in qf}
            per_d = {d: sum(per_q[q][i] for q in qf) for i, d in enumerate(DRAWS)}
            per[s] = {"passed_of_30": sum(per_d.values()), "per_draw_of_10": per_d,
                      "per_question_draws_passed": {q: sum(v) for q, v in per_q.items()},
                      "pass_keys": sorted(cells[(s, q, d)]["key"] for q in qf for d in DRAWS
                                          if passed(cells[(s, q, d)], t)),
                      "fail_keys": sorted(cells[(s, q, d)]["key"] for q in qf for d in DRAWS
                                          if not passed(cells[(s, q, d)], t))}
        res[t] = per
    return res


def read_ranking() -> dict:
    """The false_premise lists of Figure 3's ranking.json at RANKING_AT."""
    try:   # O3: as committed at RANKING_AT, pinned in the tree, held to its git blob id (scripts/pinned_history.py)
        got = PH.text(PH.show(RANKING_AT, RANKING_PATH))
    except PH.PinError as e:
        raise Refused(f"git show {RANKING_AT}:{RANKING_PATH}: {str(e)[:200]}") from None
    return json.loads(got)["keys"]


def reproduce_v24(res: dict, rk: dict) -> int:
    """(1): the recount on key v2.4 against the committed lists; the keys compared."""
    n = 0
    for t in (T_MAIN, T_RELAX):
        for s, _ in STRATS:
            theirs = rk[f"false_premise|correctness {t} or more|{s}"]
            if sorted(theirs.get("pass", [])) != res[t][s]["pass_keys"] or \
                    sorted(theirs.get("fail", [])) != res[t][s]["fail_keys"]:
                raise Refused(f"score {t}, {s}: the recount on key v2.4 differs from ranking.json at {RANKING_AT}")
            n += len(res[t][s]["pass_keys"]) + len(res[t][s]["fail_keys"])
    return n


def gate_v25(res: dict, n_answers: int, n_changed: int) -> dict:
    """(2): the counts on key v2.5."""
    got = {"answers": n_answers, "changed": n_changed, "passed_4": sum(res[T_MAIN][s]["passed_of_30"] for s, _ in STRATS),
           "per_strategy": {s: res[T_MAIN][s]["passed_of_30"] for s, _ in STRATS}}
    if got != V25_WANT:
        raise Refused(f"the counts on key v2.5 are {got}, the gate holds {V25_WANT}")
    return got


def read_q66(path: Path = Q66) -> dict:
    """(3): the five ids, 15 answers at every cell, 24 cells."""
    q = json.loads(path.read_text())
    fp = q["false_premise"]
    ids = q["ids"]["false_premise"]
    if tuple(sorted(ids)) != Q5_WANT:
        raise Refused(f"q66 false-premise ids are {ids}, not {Q5_WANT}")
    main = fp["main"]
    keys = {(e["core_papers"], e["strategy"]) for e in main}
    want = {(c, s) for c in SIZES for s, _ in STRATS}
    if len(main) != 24 or keys != want:
        raise Refused(f"q66: {len(main)} cells, want the 24 of six strategies at four sizes")
    bad = [e for e in main if e["answers"] != 15 or e["score4"]["n"] != 15 or e["score3"]["n"] != 15]
    if bad:
        raise Refused(f"q66: n is not 15 at {[(e['core_papers'], e['strategy']) for e in bad][:3]}")
    return {"main": main, "awaiting": fp["awaiting_s6"], "rule": fp["rule"], "ids": list(ids), "provisional": q.get("provisional")}


def read_g1(s6_root: Path = S6_ROOT) -> dict:
    """The ten questions' cells on key v2.4 and on the final key, through S463's own reader."""
    collect = FR.check_committed(COLLECT)
    side = json.loads(collect.with_name(collect.name + ".json").read_text())
    outs = (side.get("_provenance") or {}).get("inputs") or []
    relocate = {str(Path(outs[0]).parent): str(INPUTS)}
    groups = S463.key_groups()
    reruns = S463.rerun_keys()
    qf = sorted(q for q, g in groups.items() if g == "false_premise")
    if len(qf) != 10 or set(qf) != set(SHORT):
        raise Refused(f"want the ten false-premise questions of the key, got {qf}")
    read = S463.read_collect(collect, list(DRAWS), groups, reruns, None, None, relocate)
    v24 = copy.deepcopy({k: v for k, v in read["cells"].items() if k[1] in qf})
    jr = S463.judge_rows(read, collect, groups, reruns, list(DRAWS), s6_root, None)
    v25 = {k: v for k, v in read["cells"].items() if k[1] in qf}
    want = {(s, q, d) for s, _ in STRATS for q in qf for d in DRAWS}
    if set(v25) != want:
        raise Refused(f"cells: missing {sorted(want - set(v25))[:3]}, extra {sorted(set(v25) - want)[:3]}")
    return {"qf": qf, "v24": v24, "v25": v25, "judge_rows": S463.judge_rows_record(jr), "groups": groups}


def tile_colours() -> dict:
    """Four steps of cividis, 3 of 3 yellow (D171)."""
    from matplotlib import colormaps
    from matplotlib.colors import to_hex
    cm = colormaps[S457.FLOCK["colour"]["continuous"]]
    return {k: to_hex(cm(i)).upper() for k, i in zip(range(4), (0, 110, 190, 255))}


def text_on(bg: str) -> str:
    return max(("#000000", "#FFFFFF"), key=lambda c: S457.wcag(c, bg))


def sheets_of(res: dict, cells: dict, qf: list, q66: dict) -> dict:
    a, b, c = [], [], []
    for t in (T_MAIN, T_RELAX):
        for s, lab in STRATS:
            for q in qf:
                a.append({"row": "cell", "threshold": t, "strategy": s, "strategy_label": lab, "question_id": q,
                          "short_claim": SHORT[q], "draws_passed": res[t][s]["per_question_draws_passed"][q],
                          "of_draws": len(DRAWS)})
    for t in (T_MAIN, T_RELAX):
        for s, lab in STRATS:
            a.append({"row": "total", "threshold": t, "strategy": s, "strategy_label": lab, "passed": res[t][s]["passed_of_30"],
                      "of_answers": 30, "pass_keys": " ".join(res[t][s]["pass_keys"]),
                      "fail_keys": " ".join(res[t][s]["fail_keys"]),
                      "key_versions": json.dumps(dict(sorted(Counter(cells[(s, q, d)].get("key_version", "v2.4")
                                                                     for q in qf for d in DRAWS).items())))})
    for s, lab in STRATS:
        v = res[T_MAIN][s]["per_draw_of_10"]
        for d in DRAWS:
            b.append({"row": "draw", "strategy": s, "strategy_label": lab, "draw": d, "questions_passed": v[d],
                      "of_questions": len(qf)})
        b.append({"row": "mean", "strategy": s, "strategy_label": lab, "of_questions": len(qf),
                  "mean_of_draws": sum(v.values()) / len(DRAWS)})
    lab = dict(STRATS)
    by_unit = q66["awaiting"].get("by_unit", {})
    for e in q66["main"]:
        idxs = [x["index"] for x in e["per_index"]]
        c.append({"row": "size", "core_papers": e["core_papers"], "strategy": e["strategy"], "strategy_label": lab[e["strategy"]],
                  "passed_4": e["score4"]["k"], "passed_3": e["score3"]["k"], "n": e["answers"],
                  "answers_by_status": json.dumps(e["answers_by_status"], sort_keys=True),
                  "awaiting_s6_n": sum(by_unit.get(f"{e['strategy']} {i}", 0) for i in idxs)})
    for e in q66["main"]:
        for x in e["per_index"]:
            c.append({"row": "per_index", "core_papers": e["core_papers"], "index": x["index"], "strategy": e["strategy"],
                      "strategy_label": lab[e["strategy"]], "passed_4": x["score4"]["k"], "passed_3": x["score3"]["k"],
                      "n": x["score4"]["n"], "awaiting_s6_n": by_unit.get(f"{e['strategy']} {x['index']}", 0)})
    if sum(r["awaiting_s6_n"] for r in c if r["row"] == "size") != q66["awaiting"]["answers"]:
        raise Refused(f"sheet c: the answers awaiting S6G4 do not add to q66's {q66['awaiting']['answers']}")
    return {"a": [{k: r.get(k) for k in A_COLS} for r in a], "b": [{k: r.get(k) for k in B_COLS} for r in b],
            "c": [{k: r.get(k) for k in C_COLS} for r in c]}


def draw(fn: dict, qf: list, paths: dict, mut=None) -> tuple:
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator
    hs.apply_rc("S532")
    MM = S457.MM_PT
    W = S457.FIG_W_MM
    TILE = tile_colours()
    # D224 Q3 (Valerio, 3 Nov, the preview of 3 Nov): the strategy names at 45 degrees, a lifted, the questions
    # right-aligned against the tiles, b and c raised, c's header detached from its column heads
    X_LAB, X0, CW, GAP, TH, Y0 = 2.0, 62.0, 9.0, 4.0, 4.6, 25.0
    XB = {T_MAIN: X0, T_RELAX: X0 + 6 * CW + GAP}
    Y_B, BH = 87.0, 26.0
    # b and c across the page width (Valerio, 2 Nov: "b) why it is not stretched all the way to the left? adjust both
    # b) and c)"): b from the left margin, after its axis label and ticks; c to the right margin, its tag inside W
    # 2 Nov evening (Valerio: "make panel c smaller ... so that also b) and c) are aligned top"): c's columns as narrow
    # as its widest head ("verified", about 8.8 mm at 8 pt, the journal's floor, so the text cannot shrink); b takes the
    # width c gives up; b's letter and key sit on c's header line
    XBB, CWB = 15.0, 15.5                        # b's axes start and column width
    CWC = 10.0                                   # c's column width
    XC = W - 5.5 - 6 * CWC                       # c's left edge: its tag at XC + 6 * CWC + 2.0 stays within W
    CH, C_GAP = 4.2, 3.0                         # c's cell height and the gap between its two blocks
    H = Y_B + 2 * 4 * CH + C_GAP + 4.0
    fig = hs.figure(W, H)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    printed, readback = {}, []

    def num(t, entry):
        gid = f"s448num_{len(printed)}"
        t.set_gid(gid)
        printed[gid] = entry
        return t

    def fixed(t, why):
        return num(t, {"fixed": t.get_text(), "why": why})

    def letter(ch, x, y):
        ax.text(x, y, ch, fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT, va="baseline", ha="left")

    a_idx = {(r["row"], r["threshold"], r["strategy"], r["question_id"]): i for i, r in enumerate(fn["a"])}
    letter("a", 0.0, 3.6)
    ax.text(X0 - 1.5, Y0 - 1.6, "False premise (question)", ha="right", va="baseline")
    for t, head in ((T_MAIN, "Judge score 4 or more"), (T_RELAX, "Judge score 3 or more")):
        xb = XB[t]
        fixed(ax.text(xb + 3 * CW, 8.0, head, ha="center", va="baseline"), "the threshold of the block (Rule 9)")
        for j, (s, lab) in enumerate(STRATS):
            # at 45 degrees (D224 Q3); mutant rotated_overlap sets them at a third of the pitch, so neighbours collide
            xl = xb + ((j / 3 if mut == "rotated_overlap" else j) + 0.5) * CW - 1.0
            lb = ax.text(xl, Y0 - 1.2, lab, ha="left", va="baseline", rotation=45, rotation_mode="anchor")
            if any(ch.isdigit() for ch in lab):
                fixed(lb, "a strategy's name")
            for i, q in enumerate(qf):
                ri = a_idx[("cell", t, s, q)]
                k = fn["a"][ri]["draws_passed"]
                y = Y0 + i * TH
                ax.add_patch(plt.Rectangle((xb + j * CW, y), CW, TH, facecolor=TILE[k], edgecolor="#FFFFFF", lw=0.5))
                num(ax.text(xb + (j + 0.5) * CW, y + TH / 2, str(k), ha="center", va="center", color=text_on(TILE[k])),
                    {"sheet": f"{SHEET}a", "row": ri, "format": "{draws_passed}"})
    for i, q in enumerate(qf):
        fixed(ax.text(X0 - 1.5, Y0 + i * TH + TH / 2, f"{SHORT[q]} ({q[-3:]})", ha="right", va="center"),
              "our short wording of the false claim, with the question's number")
    # Valerio 11 Nov (figure files hold only the figure): the key's steps carry no "of 3"; the legend's a says "Draws
    # passed, of three". The title "Draws passed:" stays, since draws passed is the quantity each cell measures
    hs.key(fig, [("swatch", TILE[k], str(k)) for k in (3, 2, 1, 0)],
            centre_x=(X0 + XB[T_RELAX] + 6 * CW) / 2, y=3.6, title="Draws passed:")
    for tx in fig.texts:
        if any(ch.isdigit() for ch in tx.get_text()):
            fixed(tx, "a step of the key")

    # ---- b: each draw's questions passed (of 10) at score 4, from the left margin
    letter("b", 0.0, Y_B - 10.0)
    bx = fig.add_axes([XBB / W, 1 - (Y_B + BH) / H, 6 * CWB / W, BH / H])
    bx.set_xlim(0, 6 * CWB)
    bx.set_ylim(0, 10.3)
    for sp in ("top", "right"):
        bx.spines[sp].set_visible(False)
    bx.spines["bottom"].set_bounds(0, 6 * CWB)
    bx.xaxis.set_major_locator(FixedLocator([(j + 0.5) * CWB for j in range(6)]))
    bx.xaxis.set_major_formatter(NullFormatter())
    bx.yaxis.set_major_locator(FixedLocator(list(range(0, 11, 2))))
    bx.yaxis.set_major_formatter(FixedFormatter([str(v) for v in range(0, 11, 2)]))
    bx.yaxis.set_minor_locator(NullLocator())
    # Valerio 11 Nov: the axis names its quantity only; "in a draw, of the 10 false-premise questions" is in the legend's b
    ax.text(XBB - 8.6, Y_B + BH / 2, "Questions passed", ha="center", va="center", rotation=90)
    b_idx = {(r["row"], r["strategy"], r["draw"]): i for i, r in enumerate(fn["b"])}
    DOT = hs.DOT_SPARSE_MM
    mm_y = BH / 10.3
    for j, (s, _) in enumerate(STRATS):
        cx = (j + 0.5) * CWB
        vals = [fn["b"][b_idx[("draw", s, d)]]["questions_passed"] for d in DRAWS]
        off, _ = hs.swarm([v * mm_y for v in vals], half=hs.BAND_FRAC * CWB / 2 - DOT / 2, pitch=DOT + 0.05, dot=DOT)
        shown = [v + (0.5 if mut == "draw_b_dot" else 0.0) for v in vals]
        ln, = bx.plot([cx + o for o in off], shown, ls="none", marker="o", color=hs.GREY["dot"], ms=DOT / MM,
                      mfc=hs.GREY["dot"], mec="none", mew=0, zorder=3, clip_on=False)
        readback.append((f"b {s} dots", list(ln.get_ydata()), vals))
        m = fn["b"][b_idx[("mean", s, None)]]["mean_of_draws"]
        half = hs.BOX_FRAC * CWB / 2
        ln, = bx.plot([cx - half, cx + half], [m, m], color="#000000", lw=hs.LW["median"], solid_capstyle="butt", zorder=4)
        readback.append((f"b {s} mean", list(ln.get_ydata()), [m, m]))
    for j, (s, _) in enumerate(STRATS):              # each column named under its tick, in two lines as c's heads
        for k, (word, dy) in enumerate(zip(C_HEADS[s], (4.6, 7.9))):
            lb = ax.text(XBB + (j + 0.5) * CWB, Y_B + BH + dy, word, ha="center", va="baseline")
            if any(ch.isdigit() for ch in word):
                fixed(lb, "a strategy's name, on two lines")
    hs.key(fig, [("mark", (hs.GREY["dot"], "o"), "Draw"), ("line", ("#000000", hs.LW["median"]), "Mean")],
           centre_x=XBB + 3 * CWB, y=Y_B - 10.0)

    # ---- c: the five questions asked at every corpus size, printed counts to the right margin
    # rulings page 6 Nov, SUPP6-TITLE: O1: no in-plate header (FIGURE_LOCK titles_in_figure none, editor row 32); its
    # words "passed of 15, by core papers (rows)" are in the legend's c. The letter stays on b's line, so b and c align top
    letter("c", XC - 3.6, Y_B - 10.0)
    for j, (s, _) in enumerate(STRATS):
        one, two = C_HEADS[s]
        ax.text(XC + (j + 0.5) * CWC, Y_B - 4.6, one, ha="center", va="baseline")
        t2 = ax.text(XC + (j + 0.5) * CWC, Y_B - 1.3, two, ha="center", va="baseline")
        if any(ch.isdigit() for ch in two):
            fixed(t2, "a strategy's name, on two lines")
    c_idx = {(r["core_papers"], r["strategy"]): i for i, r in enumerate(fn["c"]) if r["row"] == "size"}
    for b_, (col, tag) in enumerate((("passed_4", "Score 4+"), ("passed_3", "Score 3+"))):
        top = Y_B + b_ * (4 * CH + C_GAP)
        for i, c in enumerate(SIZES):
            y = top + i * CH
            fixed(ax.text(XC - 1.0, y + CH / 2, str(c), ha="right", va="center"), "core papers in the index")
            for j, (s, _) in enumerate(STRATS):
                ri = c_idx[(c, s)]
                ax.add_patch(plt.Rectangle((XC + j * CWC, y), CWC, CH, facecolor="none", edgecolor=hs.GREY["line"],
                                           lw=max(0.3, S457.LINE_MIN_PT)))
                v = fn["c"][ri][col] + (1 if mut == "c_count" else 0)
                num(ax.text(XC + (j + 0.5) * CWC, y + CH / 2, str(v), ha="center", va="center"),
                    {"sheet": f"{SHEET}c", "row": ri, "format": "{" + col + "}"})
                readback.append((f"c {c} {s} {col}", [v], [fn["c"][ri][col]]))
        fixed(ax.text(XC + 6 * CWC + 2.0, top + 2 * CH, tag, ha="center", va="center", rotation=90), "the threshold (Rule 9)")
    bad_c = hs.check_figure_colours(fig)
    if bad_c:
        plt.close(fig)
        raise Refused(f"colours outside the house palette: {bad_c}")
    S457.finish_plate(fig, W, H, paths, title=PLATE)
    return W, H, printed, readback


def check_drawn(readback) -> list:
    bad = []
    for what, got, want in readback:
        if len(got) != len(want) or any(abs(float(a) - float(b)) > 1e-9 for a, b in zip(got, want)):
            bad.append(f"{what}: drawn {got}, workbook {want}")
    return bad


def legend(q66: dict, res: dict, qf: list) -> tuple:
    # Editor row 45 round (Valerio, 8 Nov): every panel described in full, with no reference to another panel. D310
    # (9 Nov): b's black line is a mean over draws, a derived statistic, so b states "n = X draws" (S448 R9). c names the
    # five questions by where they sit, not by internal id (audit 9 Nov, A77).
    ids = ", ".join(q[-3:] if i else q for i, q in enumerate(q66["ids"]))
    labs = [lab for _, lab in STRATS]
    strats = ", ".join(labs[:-1]) + " and " + labs[-1]
    nq, nd, n5 = len(qf), len(DRAWS), len(q66["ids"])
    word = {3: "three", 5: "five"}
    sizes = sorted({e["core_papers"] for e in q66["main"]})
    sizes_t = ", ".join(str(x) for x in sizes[:-1]) + f" and {sizes[-1]}"
    title = "Answers to the false-premise questions, by strategy and corpus size"
    body = (
        f"Each question states a false claim about one paper and asks whether it is true. Answers are by gemini-3-flash "
        f"with six strategies ({strats}). A judge (devstral-small-2:24b) scores each answer from 0 to 5 for correctness "
        f"against the key's refutation; an answer passes at a score of {T_MAIN} or more, or at {T_RELAX} or more, the "
        f"relaxed threshold. **a**, Draws passed, of {word.get(nd, nd)}, for each of the {nq} false-premise questions "
        f"(rows, by short claim and question number) and each strategy (columns), on the 20-paper index. Left grid, a "
        f"score of {T_MAIN} or more; right grid, {T_RELAX} or more. The number and the colour of each cell give the draws "
        f"passed: yellow {nd}, olive 2, grey 1, dark blue 0. **b**, Questions passed in a draw, of the {nq} false-premise "
        f"questions on the 20-paper index at a score of {T_MAIN} or more (y axis), for each strategy (x axis). Grey dots, "
        f"the {word.get(nd, nd)} draws; black line, the mean of the n = {nd} draws. **c**, Answers passed of 15, by "
        f"number of core papers (rows) and strategy (columns), for the {word.get(n5, n5)} false-premise questions in scope "
        f"at every corpus size (Supplementary Data 1), one draw. Rows are {sizes_t} core papers. Each cell counts 15 answers: "
        f"{word.get(n5, n5)} questions, each on three indexes with 0, 1 and 3 distractor papers per core paper. Upper "
        f"block, a score of {T_MAIN} or more; lower block, {T_RELAX} or more. Counts are shown as they are, with no test "
        f"and no ranking. " + class_sentence())
    return title, body


# Q20 (Valerio, 10 Nov: "For the 27 cards, go with suggestions"): S586's classes of a and b's 180 answers enter the
# legend, read from S586's own summary. The labels are Claude's (labels_status in its header); D259 confirmed the one
# "affirmed" label, so the sentence says who classed them.
S586_SUMMARY = ROOT / "findings/recompute/S586_false_premise_classes/summary.json"


def class_sentence() -> str:
    d = json.loads(S586_SUMMARY.read_text())
    tot = next(r for r in d["summary"] if r["strategy"] == "all")      # S586's row over the six strategies
    cj = d["class_by_judge"]
    other_pass = sum(cj[f"{c}|pass"] for c in ("hedged", "refused", "affirmed"))
    other = tot["hedged"] + tot["refused"] + tot["affirmed"]
    assert sum(tot[c] for c in ("contradicted", "hedged", "refused", "affirmed")) == tot["answers"]
    return (f"Claude (Anthropic), the writing aid, also classed each of the {tot['answers']} answers on the 20-paper "
            f"index by reading it against its question and the key: {tot['contradicted']} contradict the false claim "
            f"with evidence, {tot['hedged']} hedge, {tot['refused']} say the papers do not hold the answer and "
            f"{tot['affirmed']} affirms the claim (confirmed by the first author). The judge passed "
            f"{cj['contradicted|pass']} of the {tot['contradicted']} and {other_pass} of the other {other}.")


def build(out: Path = OUT, fixture: dict | None = None, mut=None, quiet=False) -> dict:
    S457.figure_lock_agreed()
    if fixture is None:
        g1 = read_g1()
        qf, v24, v25 = g1["qf"], g1["v24"], g1["v25"]
        rk = read_ranking()
        q66 = read_q66()
    else:
        qf, v24, v25, rk, q66 = fixture["qf"], fixture["v24"], fixture["v25"], fixture["ranking"], fixture["q66"]
        g1 = {"judge_rows": {"fixture": True}}
    if mut == "v24_key_moved":
        k0 = next(iter(v24))
        v24 = {**v24, k0: {**v24[k0], "score": 5 - min(v24[k0]["score"], 5)}}
    compared = reproduce_v24(tally(v24, qf), rk)
    res = tally(v25, qf)
    n_changed = sum(1 for c in v25.values() if c.get("key_version") == "v2.5")
    got25 = None
    if fixture is None or fixture.get("gate"):
        got25 = gate_v25(res, len(v25), n_changed)
    fn = sheets_of(res, v25, qf, q66)
    awaiting = q66["awaiting"]["answers"]
    n, m = len(v25) + 24 * 15 - awaiting, len(v25) + 24 * 15
    stamp = (f"{n} of {m} answers on their final key: a and b, all {len(v25)} (G1, three draws, {n_changed} on "
             f"changed questions read from S6G1, the others unchanged by key v2.5); c, {24 * 15 - awaiting} of {24 * 15} "
             f"(G4 draw 1, {awaiting} awaiting S6G4, read on key v2.4 until it ends)")
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="S532_"))
    paths = {x: tmp / f"{PLATE}{tag}.{x}" for x in ("pdf", "svg", "png")}
    try:
        W, H, printed, readback = draw(fn, qf, paths, mut)
        bad = check_drawn(readback)
        if bad:
            raise Refused(f"check_drawn ({len(bad)}): " + "; ".join(bad[:3]))
        FR.check_pdf_deterministic(paths["pdf"])
        FR.check_svg_deterministic(paths["svg"])
        for p in list(out.glob(f"{PLATE}*")):
            p.unlink()
        final = {x: out / p.name for x, p in paths.items()}
        for x, p in paths.items():
            shutil.move(str(p), final[x])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sheets = {f"{SHEET}{k}": {"columns": c, "rows": [[r[x] for x in c] for r in fn[k]]}
              for k, c in (("a", A_COLS), ("b", B_COLS), ("c", C_COLS))}
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, sh in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(sh["columns"])
        for r in sh["rows"]:
            ws.append(["" if v is None else v for v in r])
    xlsx = out / f"{PLATE} data{tag}.xlsx"
    wb.save(xlsx)
    FR.deterministic_xlsx(xlsx)
    title, body = legend(q66, res, qf)
    lp = out / "legend_draft.md"
    lp.write_text(f"Legend DRAFT for {PLATE} (written by {SCRIPT}).\n\n**{PLATE} | {title}.**\n\n{body}\n")
    cap = out / f"{PLATE} data caption{tag}.md"
    cap.write_text(f"# {PLATE} data, caption\n\n**{PLATE} data | Numerical values plotted in {PLATE}.** Data "
                   f"stamp: {stamp}. Sheet {SHEET}a: one 'cell' row per threshold, strategy and question (draws passed of "
                   f"3), then one 'total' row per threshold and strategy, not drawn (answers passed of 30, the pass and fail "
                   f"answer keys, the key version of its rows). Sheet {SHEET}b: one 'draw' row per strategy and draw (questions "
                   f"passed of 10 at score 4 or more) and one 'mean' row per strategy. Sheet {SHEET}c: one 'size' row per "
                   f"core-paper size and strategy (answers passed at 4 and at 3, of n = 15, by status, and the answers "
                   f"awaiting S6G4), then one 'per_index' row per index.\n")
    numbers = out / f"{SIDE}_numbers.json"
    numbers.write_text(json.dumps({"stamp": stamp, "what": f"every number {PLATE} draws, sheet by sheet as the data workbook "
                                   "holds them (S448 --supplementary R8 (2) to (6))", "sheets": sheets, "printed": printed,
                                   "printed_what": "every text holding a digit: the SVG group id, and the sheet, row and "
                                                   "format it is written from, or the fixed text",
                                   "questions": qf}, indent=1, default=str) + "\n")
    inputs = {} if fixture else {rel(p): sha(p) for p in (COLLECT, Q66)}     # the data read; S463's code is held by (1) and (2)
    prov = {"script": SCRIPT, "script_sha256": sha(Path(__file__)), "command": f"uv run --frozen python {SCRIPT} plate",
            "python": platform.python_version(), "model_calls": 0, "inputs_sha256": inputs, "stamp": stamp, "figure": PLATE,
            "page_mm": [W, H], "judge_rows": g1["judge_rows"],
            "reproduced": {"v2.4 answer keys equal ranking.json": compared, "ranking_at": RANKING_AT, "v2.5": got25,
                           "q66_ids": q66["ids"]},
            "rule": q66["rule"], "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "status": S457.FLOCK["status"]},
            "files": {p.name: sha(p) for p in [*final.values(), xlsx, cap, numbers, lp]}}
    (out / f"{SIDE}_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    if not quiet:
        print(stamp)
        print(f"reproduced: {compared} answer keys equal ranking.json at {RANKING_AT}; key v2.5 gate {got25}")
        print(f"wrote {PLATE}{tag} ({W:.0f} x {H:.1f} mm) and the rest into {rel(out)}")
    return {"ok": True, "n": n, "m": m, "H": H, "out": out, "stamp": stamp}


# ---------------------------------------------------------------------------------------------------------------
# Selftest and mutants (made-up cells, NOT DATA)
# ---------------------------------------------------------------------------------------------------------------
def make_fixture() -> dict:
    """Ten made-up questions' cells and a q66 of the real shape. Scores come from a formula, not from any data."""
    qf = sorted(SHORT)
    v24, v25 = {}, {}
    for si, (s, _) in enumerate(STRATS):
        for qi, q in enumerate(qf):
            for d in DRAWS:
                score = 5 - ((si + qi + d) % 4 == 0) * 3
                key = f"{INDEX}|{s}|{q}|d{d}"
                v24[(s, q, d)] = {"kind": "scored", "score": score, "key": key}
                v25[(s, q, d)] = {"kind": "scored", "score": score, "key": key, "key_version": "v2.5"}
    res = tally(v24, qf)
    rk = {f"false_premise|correctness {t} or more|{s}": {"pass": res[t][s]["pass_keys"], "fail": res[t][s]["fail_keys"]}
          for t in (T_MAIN, T_RELAX) for s, _ in STRATS}
    main = []
    for c in SIZES:
        for s, _ in STRATS:
            per = [{"index": f"exp_v4_s{c}_n{r}", "score3": {"k": 5, "n": 5}, "score4": {"k": 4, "n": 5}} for r in (0, 1, 3)]
            main.append({"answers": 15, "answers_by_status": {"ok": 15}, "core_papers": c, "per_index": per, "strategy": s,
                         "score3": {"k": 15, "n": 15}, "score4": {"k": 12, "n": 15}})
    q66 = {"main": main, "awaiting": {"answers": 0, "by_unit": {}}, "rule": "fixture", "ids": list(Q5_WANT)}
    return {"qf": qf, "v24": v24, "v25": v25, "ranking": rk, "q66": q66, "gate": False}


def outline_pair(pitch: float) -> tuple:
    """Two of a's names at 45 degrees, pitch mm apart, as draw sets them: (upright boxes intersect, outlines overlap)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    hs.apply_rc("S532")
    fig = hs.figure(60.0, 30.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 60.0)
    ax.set_ylim(30.0, 0)
    ax.axis("off")
    ts = [ax.text(10.0 + j * pitch, 25.0, lab, ha="left", va="baseline", rotation=45, rotation_mode="anchor")
          for j, lab in enumerate(("verified pass", "RLM-5"))]
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    a, b = (t.get_window_extent(rend) for t in ts)
    up = a.x0 < b.x1 - 0.05 and b.x0 < a.x1 - 0.05 and a.y0 < b.y1 - 0.05 and b.y0 < a.y1 - 0.05
    turned = S457.outlines_overlap(*(S457.text_outline(t, rend, fig) for t in ts), 0.05)
    plt.close(fig)
    return up, turned


def selftest() -> int:
    res, fx = [], make_fixture()

    def ok(name, cond, why=""):
        res.append((name, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {name}{(': ' + str(why)[:200]) if why and not cond else ''}")
    c = {"kind": "scored", "score": 4, "key": "k"}
    ok("a score of 4 passes at 4 and at 3", passed(c, 4) == 1 and passed(c, 3) == 1)
    ok("a score of 3 passes only at 3", passed({**c, "score": 3}, 4) == 0 and passed({**c, "score": 3}, 3) == 1)
    ok("a failed answer counts as a fail (Rule 10)", passed({"kind": "failed", "key": "k"}, 3) == 0)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "p"
        r = build(out, fixture=fx, quiet=True)
        ok("the fixture plate is written", r["ok"], r)
        s448 = subprocess.run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", str(SUPP_N),
                               "--supplementary", "--dir", str(out)], capture_output=True, text=True)
        fails = [ln for ln in s448.stdout.splitlines() if " FAIL " in ln and not ln.startswith("FAIL:")]
        # D310 (9 Nov): b's mean over draws carries its n, so S448 --supplementary passes on every rule, R9 included
        ok("S448 --supplementary passes on the fixture plate (D310)", s448.returncode == 0, fails[:3])
        ok("b's mean states its n (D310)", "the mean of the n = 3 draws" in (out / "legend_draft.md").read_text())
        nums = json.loads((out / f"{SIDE}_numbers.json").read_text())
        ok("every number on the plate is in the printed map", len(nums["printed"]) > 200, len(nums["printed"]))
        svg = next(out.glob(f"{PLATE}*.svg")).read_text()
        ok("no in-plate header on c (rulings page 6 Nov, SUPP6-TITLE: O1)", "Passed of 15" not in svg
           and "s532_c_head" not in svg and "passed of 15, by number of core papers (rows)" in (out / "legend_draft.md").read_text().lower())
    up, turned = outline_pair(9.0)
    ok("two 45-degree names at a's pitch: upright boxes meet, outlines apart (D224 Q3)", up and not turned, (up, turned))
    up, turned = outline_pair(3.0)
    ok("two 45-degree names at a third of the pitch: outlines overlap", turned, (up, turned))
    sq = [(0, 0), (2, 0), (2, 1), (0, 1)]
    ok("upright boxes: the outline test is the old box test", S457.outlines_overlap(sq, [(1.9, 0.5), (3, 0.5), (3, 2), (1.9, 2)])
       and not S457.outlines_overlap(sq, [(1.96, 0.5), (3, 0.5), (3, 2), (1.96, 2)]))
    try:
        gate_v25(tally(fx["v25"], fx["qf"]), 180, 108)
        ok("the key v2.5 gate refuses counts that are not the gate's", False)
    except Refused:
        ok("the key v2.5 gate refuses counts that are not the gate's", True)
    bad = [n for n, c_ in res if not c_]
    print(f"selftest: {len(res) - len(bad)} of {len(res)} checks pass")
    return 0 if not bad else 1


MUTANTS = [("v24_key_moved", "one key v2.4 cell moved, so its answer key changes lists"),
           ("draw_b_dot", "b's dots drawn half a question high"),
           ("c_count", "a count of c printed one too high"),
           ("rotated_overlap", "a's 45-degree names at a third of the pitch, so neighbouring outlines overlap (D224 Q3)")]


def mutants() -> int:
    caught = 0
    fx = make_fixture()
    with tempfile.TemporaryDirectory() as td:
        build(Path(td) / "clean", fixture=fx, quiet=True)     # the clean fixture must build, or a refusal proves nothing
    for name, what in MUTANTS:
        with tempfile.TemporaryDirectory() as td:
            try:
                build(Path(td) / "m", fixture=fx, mut=name, quiet=True)
                hit = False
            except (Refused, SystemExit):           # S457.finish_plate refuses crowded texts with SystemExit
                hit = True
        caught += hit
        print(f"  {'CAUGHT' if hit else 'MISSED'}  {name}: {what}")
    extra = copy.deepcopy(fx)
    extra["q66"]["main"][0]["answers"] = 14
    try:
        with tempfile.TemporaryDirectory() as td:
            Q = Path(td) / "q.json"
            Q.write_text(json.dumps({"false_premise": {"main": extra["q66"]["main"], "awaiting_s6": extra["q66"]["awaiting"],
                                                       "rule": "x"}, "ids": {"false_premise": list(Q5_WANT)}}))
            read_q66(Q)
        hit = False
    except Refused:
        hit = True
    caught += hit
    print(f"  {'CAUGHT' if hit else 'MISSED'}  q66_n: a cell of c with n = 14")
    n = len(MUTANTS) + 1
    print(f"mutants: {caught} of {n} caught")
    return 0 if caught == n else 1


def main(argv=None) -> int:
    FR.pin_hash_seed()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plate").add_argument("--out", type=Path, default=None)
    sub.add_parser("selftest")
    sub.add_parser("mutants")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "plate":
            build(a.out.resolve() if a.out else OUT)
            return 0
        if a.cmd == "selftest":
            return selftest()
        return mutants()
    except Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    except S463.Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
