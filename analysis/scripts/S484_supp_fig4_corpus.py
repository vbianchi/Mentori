#!/usr/bin/env python3
"""S484 - Supplementary Figure 17: every G4 strategy against every other, pooled by corpus
size, design S-2 as Valerio approved it (D151) and placed in the Supplementary stack by D152.

WHERE IT GOES. D151 (Valerio, 26 October about 19:10, experiments/README.md "D151"): "I agree with S-2 [...] it
should be written on the axis "pass rate 3+ (%)" and "pass rate 4+" [...] the dots should be also crossed by line
plot, so it is easy to follow them". D152 (26 October about 19:40): Figure 3 is locked at 1719dbad (S476) and S-2
joins the Supplementary stack as the planned corpus-scaling figure (experiments/figures.csv, "plan's Supp Fig 4"), so
it took number 4, and FF3 a's one list makes it 9. Named by FIGURE_LOCK [files] supplementary_name (D92 Q194), checked with S448 --supplementary.
The approved draft was the scratch fig3c_alt/S_2_pooled.py (with prep_c.py); this script replaces both and reads no
scratch file except, when asked, the scratch's numbers for the reproduction below.

D201 Q11 (Valerio, 2 November 2026, yes). The plate draws panel a, one matrix per corpus size at score 4 only, lower
triangle only, each pair once, frames kept, and two panels of pass rates: b at score 4 and c at score 3 (until this date
c and d). The matrices at score 3 leave the plate. Their pairs stay in the data workbook with their intervals, in sheet
"Supplementary Fig. 17 score 3", so both thresholds stay reported. In this script "a", "b", "c" and "d" still name
the four computed blocks (K, cells, ranks and the gates, unchanged); DRAWN_LETTER and SHEET give what the plate and the
workbook call them. check_drawn holds the plate to the lower triangle, and a matrix at score 3 or an upper-triangle
cell fails it.

THE ONE COMMAND (D155; S494 calls it, after S476 rebuild), from the repository root:

    uv run --frozen python scripts/S484_supp_fig4_corpus.py plate --frozen [--out <an empty folder>]

--frozen ties the plate to the frozen pull and runs gate (2) on the frozen scratch numbers, both read through
scripts/fig_repro.frozen() and nothing else: --copy is S476's frozen copy (S476.frozen_copy(): findings/recompute/
fig3_inputs, G4's final judging refrozen 27 October, and fig3_g4_inputs.tar), --scratch is findings/recompute/
supp_fig4_inputs/s2_samepull.json (INVENTORY.md A1g), and --scratch-copy is the pull those numbers were computed on,
the 26 October one (S476.frozen_copy("fig3_1026"): findings/recompute/fig3_1026_inputs, D156). Every frozen file must have its frozen_inputs/SHA256SUMS line, and the frozen
inputs' sha256 must equal what the committed supplementary_figure17_provenance.json recorded (frozen_inputs_sha256;
before that record existed, the tie's rows and units and gate (2)'s counts), else exit 2 with nothing written. Every
output is deterministic: the stamp names the G4 reading by its input's sha256, not a write time; the provenance holds
no write time or git state; the workbook goes through fig_repro.deterministic_xlsx. --out writes the plate into that
folder (the committed one untouched), for comparison.

Other commands, under `uv run --frozen`:

    python scripts/S484_supp_fig4_corpus.py plate [--copy <S476 pull folder>] [--scratch <S-2 numbers json>]
                                                    [--scratch-copy <the pull the S-2 numbers read>]
    python scripts/S484_supp_fig4_corpus.py selftest      (offline, a fixture; no file written in the repository)
    python scripts/S484_supp_fig4_corpus.py mutants       (offline, the fixture; every mutant must fail the selftest)

READS. S476's own reading of the G4 judging, not a second one: findings/recompute/G4_fig3c/ (written by `S476 g4c`
from the S3 judge rows of the pull it names) through S476.reproduce_g4, which rebuilds S476's point and grid tables
from the rows before anything here uses them and gates them with S476.grid_gate: since D156 the drawn rows (the judged
G4R38 reruns in) pass grid_gate's checks (1) and (2) with no anchor, and D149's anchor is checked on the reading with
those reruns held out (hold_rows), as header.json records (audit 27 Oct F7). grid_pairs.jsonl holds, per index and
question, all six strategies' cells (pass at score 3, pass at score 4, or missing), and header.json's grid inputs
hold each index x strategy unit's completeness (g4_cells' rule). With --copy, S476.g4_cells is run again on that pull
(all six strategies, G4R38_WANT_ALL) and its rows and units must equal G4_fig3c's, so the figure is tied to the judge
rows themselves. D188 (Valerio, 31 October: "every figure using v2.4 needs to move to v2.5"): the plate draws
findings/recompute/G4_fig3c_d185/ (scripts/S514_fig3_d185.py g4c: per draw-1 answer the key v2.5 judge row where S6
has judged one of the 132 questions v2.5 changed, else the v2.4 row; provisional while S6 runs), read through
S476.reproduce_g4_d185 (load_d185), which holds it to G4_fig3c's rows (every row of a question v2.5 left unchanged
equal) and recomputes its grid_tables.json from its rows and its header's draw-1 units; G4_fig3c stays the v2.4
anchor. Also read: findings/figures_provisional/supp_fig7_depth/supplementary_figure7_numbers.json (the committed
sheet Supplementary Fig. 7c of the locked plate) and experiments/FIGURE_LOCK.toml.

REPRODUCE FIRST (README.md:75-79). Exit 2 and nothing written on any difference:
  (0) D188, the v2.4 anchor: every strategy against single pass at every index, at score 3 and 4, by this script's
      own pairing (pooled() over one index) on G4_fig3c's rows and units, equals G4_fig3c's grid_tables.json (S476's
      own reading, recomputed by S476.reproduce_g4 from the same rows): completeness, n, both pass rates, d and the
      interval, to 1e-9. Then load_d185 holds the drawn reading to G4_fig3c (above), and (1) and (2) follow;
  (1) on the drawn reading (G4_fig3c_d185), every strategy against single pass at every index, at score 3 and 4,
      computed by this script's own pairing (pooled() over one index), equals the committed sheet Supplementary Fig. 7c cell
      (Supplementary Figure 7c draws the same reading): completeness, n, both pass rates, d
      and the two ends of the interval, to 1e-9 (120 cells, 108 complete on 26 October, 120 on 27 October);
  (2) with --scratch, every pooled cell of a and b and every pass rate of c and d equals the scratch S-2's numbers
      for the same pull (the scratch's compute() dumped as {"cells", "ranks"}), the same cells and no other, each
      panel against the scratch's panel at the same threshold (SCRATCH_PANEL: the scratch draws score 3 in a and c,
      score 4 in b and d, as before D154). D156: the scratch read the pull of 26 October; the plate is drawn from G4's
      final judging of 27 October. So (2) is computed on the 26 October pull (scratch_reading(): S476.g4_cells on
      --scratch-copy, with --frozen fig3_1026_inputs), with this script's own compute(), and the plate is drawn from
      G4_fig3c; without --scratch-copy, (2) runs on the drawn reading, as before.

THE PANELS (G4 draw 1, judge S3 and, for the 132 questions v2.5 changed, S6 where it has judged: devstral-small-2:24b,
plain call (a), G4_fig3c_d185; the covered questions of D126). D154
(Valerio, 26 October): score 4 or more is the pass rate, so a and c show it; b and d show the relaxed threshold, score
3 or more (until D154 a and c were score 3, b and d score 4):
  a  per core-paper size (5, 10, 20, 50) one 6 x 6 matrix, pooled over the three distractor ratios (0, 1, 3): each
     cell the row strategy's pass rate minus the column strategy's at score 4 or more, in percentage points, over the
     (index, question) pairs where both have a pass or a fail; a black frame where the two-sided 95% interval
     excludes 0. Interval: S463.interval (Rule 2, 10,000 resamples, seed 20261013) resampling questions, each
     question carrying its summed difference and its pair count from all pooled indexes (ratio of sums).
  b  the same at score 3 or more; side labels "score 4+" and "score 3+ (relaxed)" on the two blocks (D151, D154).
  c  per size, each strategy's pass rate at score 4 or more on the (index, question) pairs every strategy drawn at
     that size has (y axis "pass rate 4+ (%)", D151's wording); a line in the strategy's colour joins its dots at
     adjacent sizes where it is drawn at both (D151), never across a size where it is not drawn.
  d  the same at score 3 or more (y axis "pass rate 3+ (%)").
  A strategy is drawn at a size only when its units are complete at all three ratios of that size; single pass is
  complete everywhere. On 26 October verified pass was complete at 10 and 20 core papers only; on G4's final judging
  (27 October) every unit is complete.
  Colours: single pass orange, multi-hop bluish green, verified pass reddish purple, RLM-5 sky blue, RLM-10 blue,
  RLM-20 black (Okabe-Ito, FIGURE_LOCK [colour] categorical), the scratch's proposal: no main figure defines strategy
  colours (Figure 3's tiles and Supplementary Figure 7c's grid are cividis), so they are this plate's own. Differences on cividis
  ([colour] continuous) from -20 to +20 points (V; -18 to +18 until G4's final judging, D156). The key shows only what each colour stands for (D147).

WRITES findings/figures_provisional/supp_fig17_corpus/ (earlier "Supplementary Figure 17*" and
supplementary_figure17_* files deleted first): the plate as PDF, SVG and PNG (the PDF rasterised at 600 dpi), the data
workbook "Supplementary Figure 17 data.xlsx" (its panel sheets and "Supplementary Fig. 17 units"),
its caption, supplementary_figure17_numbers.json (sheets and the printed map S448 R8 reads),
supplementary_figure17_provenance.json and legend_draft.md. k is the index x strategy units judged complete.

No model call, no network, no Studio access: the pull is S476's (`S476 pull`).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import math
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S476 = _load("S476", ROOT / "scripts" / "S476_fig3_d123.py")      # reproduce_g4, g4_cells, grid_tables, grid_sheet
S463, S457 = S476.S463, S476.S457                                  # interval; plate_rc, finish_plate, OKABE, G1
import house_style as hs  # noqa: E402                              # one drawing style for every plate
S448 = _load("S448", ROOT / "scripts" / "S448_figure_rules_check.py")   # HALF_UP, half_up: as R8 (6) reads a number
Refused = S476.Refused
fig_repro = S476.fig_repro                                         # D155: frozen inputs, deterministic outputs

SCRIPT = "scripts/S484_supp_fig4_corpus.py"
SUPP_N = 17                                        # D257 (9 before; not cited in the manuscript, held)
OUT = ROOT / "findings" / "figures_provisional" / f"supp_fig{SUPP_N}_corpus"
G4DIR = S476.G4_FIG3C
G4D185 = S476.G4_FIG3C_D185                                        # D188: the draw-1 reading drawn (S514 g4c)
FIG3_NUMBERS = S476.OUT / f"{S476.SIDE}_numbers.json"
FIG3_SHEET = S476.SHEET   # D283: panel c is Supplementary Figure 7's one sheet ("Supplementary Fig. 7"; "...7c" before)
PLATE = S457.FLOCK["files"]["supplementary_name"].format(n=SUPP_N)      # "Supplementary Figure 17"
SIDE = f"supplementary_figure{SUPP_N}"
DRAWN_LETTER = {"a": "a", "c": "b", "d": "c"}                      # D201 Q11: computed block to the plate's panel letter
SHEET = {k: f"Supplementary Fig. {SUPP_N}{DRAWN_LETTER[k]}" for k in "acd"}
SHEET["b"] = f"Supplementary Fig. {SUPP_N} score 3"                # D201 Q11: not drawn, kept with its intervals
SHEET_UNITS = f"Supplementary Fig. {SUPP_N} units"
STRATS = S476.G4_ALL                                               # S457.G1's order, single pass first
LABEL = dict(S457.G1)
SIZES = (5, 10, 20, 50)
RATIOS = (0, 1, 3)
UNITS_TOTAL = len(STRATS) * len(SIZES) * len(RATIOS)               # 72
OK = S457.OKABE
COLOUR = {"single_pass": OK["orange"], "multi_hop": OK["bluish green"], "verified_pass": OK["reddish purple"],
          "rlm_5": OK["sky blue"], "rlm_10": OK["blue"], "rlm_20": OK["black"]}
LINE_PT = 0.75                                                     # c and d's lines (>= [lines] line_min_pt)
FRAME_PT = 1.1
V = 20.0                                                           # the colour scale runs -V to +V points (largest |d|
                                                                   # on 26 October 16.7, scale 18; on G4's final judging,
                                                                   # 27 October, 19.7, so 20, the next multiple of 5 as
                                                                   # S476's c scale; check_drawn refuses one past V)
TOL = 1e-9
K = {"a": 1, "b": 0, "c": 1, "d": 0}                               # D154: the cell index a panel reads, 1 pass4, 0 pass3
SCRATCH_PANEL = {"a": "b", "b": "a", "c": "d", "d": "c"}         # gate (2): the scratch S-2's panel at that threshold
SIDE_LABEL = {"a": "Score 4+"}                                     # D151's label, D154's order, sentence case
Y_LABEL = {"c": "Pass rate 4+ (%)", "d": "Pass rate 3+ (%)"}       # D151's wording
FMT_D_SIGNED = "{d_sign}{d_size_pp:.0f}"   # U+2212 or + from the d_sign column, so S448 R8 still ties the number (F6)
FMT_D_ZERO = "{d_size_pp:.0f}"           # a d that rounds to 0 prints no sign
PT = S457.PT


def idx_name(core, ratio):
    return f"exp_v4_s{core}_n{ratio}"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    p = Path(p)
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def git(*args) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip()


# ---------------------------------------------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------------------------------------------
def table(rows6):
    """(index, strategy) -> {question: (pass3, pass4)} over the covered questions (D126); None = missing."""
    by = collections.defaultdict(dict)
    for r in rows6:
        if not r["covered"]:
            continue
        for s in STRATS:
            c = r["cells"][s]
            by[(r["index"], s)][r["question_id"]] = (c["pass3"], c["pass4"])
    return by


def load(copy: Path | None = None):
    """S476's G4 reading (key v2.4), reproduced by S476 itself; with copy, derived again from the pull's judge rows.
    The v2.4 anchor of D188: load_d185 holds the drawn reading to it."""
    rows2, tab2, header, rows6, grid = S476.reproduce_g4(G4DIR)
    units = header["grid"]["inputs"]["units"]
    tied = None
    if copy is not None:
        cells6, info6 = S476.g4_cells(copy, S476.G4R38_KEYS, S476.G4R38_WANT_ALL, configs=S476.G4_ALL)
        if not S476.same_json(cells6, rows6) or not S476.same_json(info6["units"], units):
            raise Refused(f"S476.g4_cells on {copy} does not give {rel(G4DIR)}'s rows and units")
        tied = {"copy": str(copy), "rows": len(cells6), "units": len(info6["units"])}
    if len(units) != UNITS_TOTAL:
        raise Refused(f"{len(units)} units in {rel(G4DIR)}/header.json, not {UNITS_TOTAL}")
    return {"by": table(rows6), "units": units, "header": header, "rows6": rows6, "grid": grid, "tied": tied}


def load_d185(D24: dict, d185dir: Path = G4D185) -> dict:
    """D188: S514 g4c's draw-1 reading (key v2.5 judge rows where S6 has judged one of the 132 questions v2.5 changed,
    else the v2.4 row), held to the v2.4 reading D24 by S476.reproduce_g4_d185 (the same rows but for the 132's, its
    grid_tables.json recomputed from its rows and draw-1 units), in load()'s shape: what the plate draws."""
    rows6, grid, rec = S476.reproduce_g4_d185(d185dir, D24["rows6"], D24["header"]["grid"]["inputs"]["indexes"])
    units = rec["units"]
    if len(units) != UNITS_TOTAL:
        raise Refused(f"{len(units)} units in {rel(d185dir)}/header.json, not {UNITS_TOTAL}")
    header = json.loads((Path(d185dir) / "header.json").read_text())
    return {"by": table(rows6), "units": units, "header": header, "rows6": rows6, "grid": grid, "tied": D24["tied"],
            "d185": {k: v for k, v in rec.items() if k != "units"}}


def gate_v24(D24) -> dict:
    """D188, the v2.4 anchor: this script's per-index pooling (per_index) on G4_fig3c's rows and units equals
    G4_fig3c's own grid_tables.json, which S476.reproduce_g4 recomputed from the same rows (completeness, n, both pass
    rates, d and the interval, to 1e-9)."""
    sh = S476.grid_sheet(D24["grid"])
    num = {"sheets": {FIG3_SHEET: {"columns": S476.GRID_COLS, "rows": [[x[k] for k in S476.GRID_COLS] for x in sh]}}}
    try:
        return gate_fig3c(per_index(D24["by"], D24["units"]), num)
    except Refused as e:
        raise Refused(f"gate (0), G4_fig3c's grid (key v2.4) not reproduced: {e}") from None


def scratch_reading(copy) -> dict:
    """D156: the reading gate (2) is run on: S476.g4_cells on the pull the scratch S-2 read (all six strategies, the
    G4R38 keys held as that pull's judging left them), not the reading drawn."""
    cells6, info6 = S476.g4_cells(copy, S476.G4R38_KEYS, S476.G4R38_WANT_ALL, configs=S476.G4_ALL)
    if len(info6["units"]) != UNITS_TOTAL:
        raise Refused(f"{len(info6['units'])} units in the scratch's pull, not {UNITS_TOTAL}")
    return {"by": table(cells6), "units": info6["units"], "copy": str(copy), "rows": len(cells6),
            "units_complete": sum(bool(v["complete"]) for v in info6["units"].values()),
            "g4r38_judged": info6["g4r38_judged"]}


def gate2(cells, ranks, scratch, scratch_R=None):
    """Gate (2) on the reading of the pull the scratch read: scratch_R when given (D156: the scratch's own pull, the
    plate drawn from a later one), else the drawn reading's cells and ranks. None when there are no scratch numbers."""
    if scratch is None:
        return None
    if scratch_R is None:
        return gate_scratch(cells, ranks, scratch)
    _, cells2, ranks2 = compute(scratch_R["by"], scratch_R["units"])
    g = gate_scratch(cells2, ranks2, scratch)
    g["reading"] = (f"the scratch's own pull, not the drawn one (D156): {scratch_R['rows']} rows, "
                    f"{scratch_R['units_complete']} of {UNITS_TOTAL} units complete, "
                    f"{scratch_R['g4r38_judged']} G4R38 reruns judged")
    return g


def g4_reading_id(header) -> str:
    """The G4 reading named by its input, not by a write time (D155): g4_collect.jsonl's sha256 when S476 recorded
    the frozen inputs, else the S3 judging run's run_sha256."""
    g = (header.get("frozen_inputs_sha256") or {}).get("findings/recompute/fig3_inputs/g4_collect.jsonl")
    if g:
        return f"g4_collect.jsonl {g[:8]}"
    return f"S3 run {str((header.get('inputs') or {}).get('run_sha256'))[:8]}"


def frozen_inputs(committed_prov: Path) -> tuple:
    """(the frozen copy, the frozen scratch numbers, {name: sha256}, the frozen pull the scratch read); refused when a
    frozen file is not its SHA256SUMS line or the sha256 differ from what the committed provenance recorded. The
    scratch S-2 read the pull of 26 October 18:30 (fig3_1026_inputs, D156); the plate is drawn from fig3_inputs."""
    copy = S476.frozen_copy()
    copy26 = S476.frozen_copy("fig3_1026")
    scratch = S476.S474.frozen_checked("supp_fig4", "s2_samepull.json")
    shas = S476.frozen_shas(copy, tars=("g4_inputs",))
    shas.update(S476.frozen_shas(copy26, tars=()))
    shas[rel(scratch)] = sha(scratch)
    if committed_prov.exists():
        rec = json.loads(committed_prov.read_text()).get("frozen_inputs_sha256")
        if rec is not None and rec != shas:
            diff = sorted(k for k in set(rec) | set(shas) if rec.get(k) != shas.get(k))
            raise Refused(f"frozen inputs differ from those {rel(committed_prov)} recorded ({len(diff)}): {diff[:3]}")
    return copy, scratch, shas, copy26


def legacy_check(committed_prov: Path, res, D) -> str:
    """Before frozen_inputs_sha256 existed: the committed provenance's tie (rows, units) and gate (2) counts."""
    if not committed_prov.exists():
        raise Refused(f"{rel(committed_prov)} is missing: nothing to reproduce against")
    pv = json.loads(committed_prov.read_text())
    if pv.get("frozen_inputs_sha256") is not None:
        return f"{len(pv['frozen_inputs_sha256'])} sha256 equal to {rel(committed_prov)}"
    g_r = pv.get("g4_reading") or {}
    anchor = g_r.get("v2.4_anchor") if isinstance(g_r.get("v2.4_anchor"), dict) else g_r   # D188: the tie sits there
    t_old = anchor.get("tied_to_pull_by_g4_cells") or {}
    g_old = (pv.get("reproduced") or {}).get("gate2_scratch_s2")
    if (t_old.get("rows"), t_old.get("units")) != (D["tied"]["rows"], D["tied"]["units"]) or g_old != res["gate2"]:
        raise Refused(f"the frozen inputs do not give {rel(committed_prov)}'s tie {t_old} and gate (2) {g_old}")
    return f"{rel(committed_prov)} holds no frozen_inputs_sha256 yet; its tie and gate (2) counts equal"


def unit_complete(units, s, idx):
    return bool(units[f"{s} {idx}"]["complete"])


def drawn_by_size(units):
    return {c: [s for s in STRATS if all(unit_complete(units, s, idx_name(c, r)) for r in RATIOS)] for c in SIZES}


def pooled(by, a, b, idxs, k):
    """a minus b over every (index, question) pair where both have a pass or a fail, k 0 (score 3) or 1 (score 4);
    the interval resamples questions, each carrying its summed difference and pair count over idxs."""
    num, den = collections.defaultdict(float), collections.defaultdict(float)
    xs = ys = n = 0
    for i in idxs:
        A, B = by[(i, a)], by[(i, b)]
        for q in A:
            x, y = A[q][k], B.get(q, (None, None))[k]
            if x is None or y is None:
                continue
            num[q] += x - y
            den[q] += 1
            xs, ys, n = xs + x, ys + y, n + 1
    if not n:
        return {"n_pairs": 0}
    qs = sorted(num)
    ci = S463.interval([num[q] for q in qs], [den[q] for q in qs])
    return {"n_pairs": n, "n_questions": len(qs), "pass_a_pct": 100 * xs / n, "pass_b_pct": 100 * ys / n,
            "d_pp": 100 * (xs - ys) / n, "ci95_pp": [100 * ci[0], 100 * ci[1]]}


def common_pairs(by, c, drawn_c):
    idxs = [idx_name(c, r) for r in RATIOS]
    return [(i, q) for i in idxs for q in sorted(by[(i, "single_pass")])
            if all(by[(i, s)].get(q, (None, None))[0] is not None for s in drawn_c)]


def compute(by, units):
    drawn = drawn_by_size(units)
    cells = {"a": [], "b": []}
    for c in SIZES:
        idxs = [idx_name(c, r) for r in RATIOS]
        for a, b in itertools.permutations(drawn[c], 2):
            for panel, k in (("a", K["a"]), ("b", K["b"])):
                m = pooled(by, a, b, idxs, k)
                if not m["n_pairs"]:
                    raise Refused(f"{panel} {c} {a} {b}: no pair")
                lo, hi = m["ci95_pp"]
                cells[panel].append({"core_papers": c, "row_strategy": a, "column_strategy": b,
                                     "n_pairs": m["n_pairs"], "n_questions": m["n_questions"],
                                     "pass_row_pct": m["pass_a_pct"], "pass_column_pct": m["pass_b_pct"],
                                     "d_pp": m["d_pp"], "ci95_lo_pp": lo, "ci95_hi_pp": hi,
                                     "interval_excludes_0": "yes" if (lo > 0 or hi < 0) else "no",
                                     "indexes_pooled": " ".join(idxs),
                                     # the printed sign and size (U+2212), from d_pp, rounded as printed
                                     "d_sign": ("" if S448.half_up(abs(m["d_pp"]), 0) == "0" else
                                                "\u2212" if m["d_pp"] < 0 else "+"),
                                     "d_size_pp": abs(m["d_pp"])})
    ranks = {"c": [], "d": []}
    for c in SIZES:
        common = common_pairs(by, c, drawn[c])
        for panel, k in (("c", K["c"]), ("d", K["d"])):
            rate = {s: 100 * sum(by[(i, s)][q][k] for i, q in common) / len(common) for s in drawn[c]}
            for s in drawn[c]:
                # S4-O2: the pass rate's 95% interval by Rule 2 as the matrix frames (S463.interval, questions
                # resampled, each carrying its passes and its pairs from the three indexes)
                num, den = collections.defaultdict(float), collections.defaultdict(float)
                for i, q in common:
                    num[q] += by[(i, s)][q][k]
                    den[q] += 1
                qs = sorted(num)
                lo, hi = S463.interval([num[q] for q in qs], [den[q] for q in qs])
                ranks[panel].append({"core_papers": c, "strategy": s, "strategy_label": LABEL[s],
                                     "n_pairs_common": len(common), "n_questions_common": len({q for _, q in common}),
                                     "pass_pct": rate[s], "rank": 1 + sum(v > rate[s] + TOL for v in rate.values()),
                                     "ci95_lo_pct": 100 * lo, "ci95_hi_pct": 100 * hi})
    return drawn, cells, ranks


def per_index(by, units):
    """Every strategy against single pass on one index, by pooled() over that index alone (gate (1))."""
    out = []
    for score, k in ((3, 0), (4, 1)):
        for s in STRATS[1:]:
            for c in SIZES:
                for r in RATIOS:
                    i = idx_name(c, r)
                    e = {"score": score, "index": i, "strategy": s,
                         "complete": unit_complete(units, s, i) and unit_complete(units, "single_pass", i)}
                    if e["complete"]:
                        e.update(pooled(by, s, "single_pass", [i], k))
                    out.append(e)
    return out


def gate_fig3c(mine, numbers, tol=TOL):
    """(1): this script's per-index readings equal the committed sheet Supplementary Fig. 7c, cell by cell."""
    sh = numbers["sheets"][FIG3_SHEET]
    ref = {(x["score"], x["index"], x["strategy"]): x for x in (dict(zip(sh["columns"], r)) for r in sh["rows"])}
    bad, n = [], 0
    if len(ref) != len(mine):
        bad.append(f"sheet Supplementary Fig. 7c has {len(ref)} cells, this script {len(mine)}")
    for e in mine:
        x = ref.get((e["score"], e["index"], e["strategy"]))
        if x is None:
            bad.append(f"{e['score']} {e['index']} {e['strategy']}: not in sheet Supplementary Fig. 7c")
            continue
        if bool(x["complete"]) != e["complete"]:
            bad.append(f"{e['score']} {e['index']} {e['strategy']}: complete {e['complete']}, Supplementary Fig. 7c {x['complete']}")
            continue
        if not e["complete"]:
            continue
        for mk, rk in (("n_pairs", "n_paired"), ("pass_a_pct", "pass_strategy_pct"),
                       ("pass_b_pct", "pass_single_pass_pct"), ("d_pp", "d_pp")):
            n += 1
            if abs(float(e[mk]) - float(x[rk])) > tol:
                bad.append(f"{e['score']} {e['index']} {e['strategy']} {rk}: {e[mk]} against {x[rk]}")
        for j, rk in ((0, "ci95_lo_pp"), (1, "ci95_hi_pp")):
            n += 1
            if abs(e["ci95_pp"][j] - float(x[rk])) > tol:
                bad.append(f"{e['score']} {e['index']} {e['strategy']} {rk}: {e['ci95_pp'][j]} against {x[rk]}")
    if bad:
        raise Refused(f"gate (1), sheet Supplementary Fig. 7c not reproduced ({len(bad)}): " + "; ".join(bad[:4]))
    return {"cells": len(mine), "complete": sum(e["complete"] for e in mine), "values": n}


def gate_scratch(cells, ranks, scratch, tol=TOL):
    """(2): the pooled cells and pass rates equal the scratch S-2's for the same pull, the same cells and no other."""
    bad, n = [], 0
    for panel in "ab":
        ref = {(e["core_papers"], e["row_strategy"], e["column_strategy"]): e
               for e in scratch["cells"][SCRATCH_PANEL[panel]]}
        got = {(e["core_papers"], e["row_strategy"], e["column_strategy"]): e for e in cells[panel]}
        if set(ref) != set(got):
            bad.append(f"{panel}: cells {sorted(set(got) ^ set(ref))[:3]} in one and not the other")
        for key in set(ref) & set(got):
            for f in ("n_pairs", "n_questions", "pass_row_pct", "pass_column_pct", "d_pp", "ci95_lo_pp", "ci95_hi_pp"):
                n += 1
                if abs(float(got[key][f]) - float(ref[key][f])) > tol:
                    bad.append(f"{panel} {key} {f}: {got[key][f]} against the scratch's {ref[key][f]}")
            if got[key]["interval_excludes_0"] != ref[key]["interval_excludes_0"]:
                bad.append(f"{panel} {key}: frame differs")
    for panel in "cd":
        ref = {(e["core_papers"], e["strategy"]): e for e in scratch["ranks"][SCRATCH_PANEL[panel]]}
        got = {(e["core_papers"], e["strategy"]): e for e in ranks[panel]}
        if set(ref) != set(got):
            bad.append(f"{panel}: dots {sorted(set(got) ^ set(ref))[:3]} in one and not the other")
        for key in set(ref) & set(got):
            for f in ("n_pairs_common", "pass_pct", "rank"):
                n += 1
                if abs(float(got[key][f]) - float(ref[key][f])) > tol:
                    bad.append(f"{panel} {key} {f}: {got[key][f]} against the scratch's {ref[key][f]}")
    if bad:
        raise Refused(f"gate (2), the scratch S-2 not reproduced ({len(bad)}): " + "; ".join(bad[:4]))
    return {"values": n, "cells": sum(len(cells[p]) for p in "ab"), "dots": sum(len(ranks[p]) for p in "cd")}


# ---------------------------------------------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------------------------------------------
def cividis_hex(v, vmax):
    """The colour a difference v takes (independent of draw()'s own lookup; check_drawn uses this one)."""
    import matplotlib
    cm = matplotlib.colormaps["cividis"]
    i = int(np.rint((float(np.clip(v, -vmax, vmax)) + vmax) / (2 * vmax) * 255))
    return "#%02X%02X%02X" % tuple(int(round(255 * x)) for x in cm(i)[:3])


def cd_style(s):
    """c and d's mark: black circles, each strategy having its own labelled panel (a labelled strategy takes no colour)."""
    return "#000000", "o"


def tri(rows):
    """D201 Q11: each pair once, the rows below the diagonal: row strategy later in STRATS than column strategy."""
    return [e for e in rows if STRATS.index(e["row_strategy"]) > STRATS.index(e["column_strategy"])]


def draw(paths, drawn, cells, ranks, vmax=V, mut=None):
    """The house style. a's matrices with the colour key above them, centred, ticks at -20, -10, 0, +10, +20 (S4-O1),
    minus signs U+2212, sentence-case labels; D201 Q11: score 4 only, the lower triangle only, so a matrix has
    len(STRATS) - 1 rows (no single pass row) and columns (no RLM-20 column), with the column names under it, where
    every column has a cell. b and c (Valerio: "C and d need to be redrawn in a different style") as small multiples
    with each pass rate's 95% interval (S4-O2): one small panel per strategy (columns) and threshold (rows), black dot
    and interval, a thin line joining the dots across sizes (D151)."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_hex
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
    plt.rcParams.update(hs.rc("S484"))
    cmap = matplotlib.colormaps["cividis"].resampled(256)

    def colour(v):
        return to_hex(cmap(int(round((min(max(v, -vmax), vmax) + vmax) / (2 * vmax) * 255))))

    def ink(h):
        return "#FFFFFF" if S457.wcag(h, "#FFFFFF") >= S457.wcag(h, "#000000") else "#000000"

    CELL, GUT, GAP, X0 = 7.5, 0.6, 2.6, 22.4
    SIDE_X = 1.9
    MW = (len(STRATS) - 1) * CELL
    KEY_Y = 3.9                                   # the colour key's label baseline (and panel a's letter)
    FACET_Y = 10.6
    TOP_A = FACET_Y + 1.8
    NAME_MM = 1.0 + max(hs._text_width_mm(LABEL[s]) for s in STRATS)   # the column names, turned, under a matrix
    H_ROW, ROW_GAP = 19.0, 3.6                    # b's and c's small panels
    y_a_end = TOP_A + MW + NAME_MM
    head_y = y_a_end + 6.2
    W, H = hs.PAGE_W_MM, round(head_y + 2.4 + 2 * H_ROW + ROW_GAP + 7.4 + 1.6, 1)
    fig = hs.figure(W, H)
    ov = fig.add_axes([0, 0, 1, 1])
    ov.set_xlim(0, W)
    ov.set_ylim(H, 0)
    ov.axis("off")
    printed, reg = {}, {"cells": {}, "dots": {}, "ivals": {}, "lines": collections.defaultdict(list), "geom": {}}
    reg["geom"] = {"cell": CELL, "gut": GUT, "gap": GAP, "x0": X0, "top": {"a": TOP_A}}

    def mx(ci):
        return X0 + ci * (MW + GAP)

    def label(x, y, s, gid, why, **kw):
        ov.text(x, y, s, fontsize=PT, gid=gid, **kw)
        if re.search(r"\d", s):
            printed[gid] = {"fixed": s, "why": why}

    # ---- the colour key, above the matrices, centred over the four (STYLE.md: a continuous key above, centred)
    KW, KH = 40.0, 2.4
    k_lab = "Difference in pass rate, row minus column (percentage points)"
    lab_w = hs._text_width_mm(k_lab)
    centre = (X0 + mx(3) + MW) / 2
    kx = centre - (KW + 2.0 + lab_w) / 2
    tv = [-vmax, -vmax / 2, 0, vmax / 2, vmax]
    hs.vector_colourbar(fig, KEY_Y - 1.9, KW, -vmax, vmax, tv, [hs.fmt_num(v, sign=True) for v in tv], None, x_left=kx,
                        h=KH)
    ov.text(kx + KW + 2.0, KEY_Y, k_lab, ha="left", va="baseline", fontsize=PT)
    ov.text(1.0, KEY_Y, "a", ha="left", va="baseline", fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT)

    # ---- a: the matrices, score 4, lower triangle (D201 Q11). A mutant may draw what the plate must not
    for ci, c in enumerate(SIZES):
        label(mx(ci) + MW / 2, FACET_Y, f"{c} core papers", f"facet_{c}",
              "the matrix's core-paper size (sheet a, column core_papers)", ha="center", va="baseline")
        for j, s in enumerate(STRATS[:-1]):
            label(mx(ci) + (j + 0.5) * CELL, TOP_A + MW + 1.0, LABEL[s], f"col_{c}_{s}",
                  "a strategy's name (column label)", rotation=90, ha="center", va="top")
    for i, s in enumerate(STRATS[1:]):
        label(X0 - 1.2, TOP_A + (i + 0.5) * CELL, LABEL[s], f"row_a_{s}", "a strategy's name (row label)",
              ha="right", va="center")
    for panel, top, side in (("a", TOP_A, SIDE_LABEL["a"]),):
        label(SIDE_X, top + MW / 2, side, f"side_{panel}", "the threshold the block shows (D151; D154: 4 the pass rate)",
              rotation=90, ha="center", va="center")
        shown = cells["b" if mut == "matrix_at_score_3" else panel]
        for r_i, e in enumerate(tri(shown)):
            ci = SIZES.index(e["core_papers"])
            i, j = STRATS.index(e["row_strategy"]) - 1, STRATS.index(e["column_strategy"])
            if mut == "upper_triangle":
                i, j = j, i                       # mirrored across the diagonal, inside the 5 x 5 grid
            x, y = mx(ci) + j * CELL + GUT / 2, top + i * CELL + GUT / 2
            fill = colour(e["d_pp"])
            gid = f"{panel}_{e['core_papers']}_{e['row_strategy']}_{e['column_strategy']}"
            rect = Rectangle((x, y), CELL - GUT, CELL - GUT, facecolor=fill, edgecolor="none", lw=0, zorder=1)
            rect.set_gid(f"{gid}_box")
            ov.add_patch(rect)
            framed = e["interval_excludes_0"] == "yes"
            if mut == "frame_inverted":
                framed = not framed
            frame = None
            if framed:
                frame = Rectangle((x, y), CELL - GUT, CELL - GUT, facecolor="none", edgecolor="#000000",
                                  lw=FRAME_PT, zorder=3, joinstyle="miter")
                ov.add_patch(frame)
            fmt = FMT_D_SIGNED if e["d_sign"] else FMT_D_ZERO
            ov.text(x + (CELL - GUT) / 2, y + (CELL - GUT) / 2, S448.HALF_UP.format(fmt, **e),
                    ha="center", va="center_baseline", fontsize=PT, color=ink(fill), zorder=4, gid=gid)
            printed[gid] = {"sheet": SHEET[panel], "row": r_i, "format": fmt, "inside": {"gid": f"{gid}_box",
                                                                                         "path": 0}}
            reg["cells"][(panel, e["core_papers"], e["row_strategy"], e["column_strategy"])] = (rect, frame)

    # ---- b and c (computed c and d): each strategy's pass rate by size, with its 95% interval
    LIM = {"c": (50, 100), "d": (70, 100)}
    for panel in LIM:                             # the fixed floor holds unless an interval reaches under it
        low = min(e["ci95_lo_pct"] for e in ranks[panel])
        if low < LIM[panel][0]:
            LIM[panel] = (10 * math.floor(low / 10), 100)
    YT = {k: [v[0], (v[0] + v[1]) // 2, v[1]] for k, v in LIM.items()}

    def mark(ax, x, y, s, key, xerr=None, yerr=None):
        col, mk = cd_style(s)
        ln = None
        if yerr is not None:
            ln, = ax.plot([x, x], yerr, color=col, lw=hs.LW["interval"], solid_capstyle="butt", zorder=3,
                          clip_on=False)
        if xerr is not None:
            ln, = ax.plot(xerr, [y, y], color=col, lw=hs.LW["interval"], solid_capstyle="butt", zorder=3,
                          clip_on=False)
        dt, = ax.plot([x], [y], ls="none", marker=mk, ms=hs.ESTIMATE_MM * hs.MARKER_SCALE.get(mk, 1.0) / hs.MM_PT, mfc=col,
                      mec="none", mew=0, zorder=4, clip_on=False)
        reg["dots"][key] = dt
        reg["ivals"][key] = ln

    def join(ax, run, s, key):
        col, _ = cd_style(s)
        if len(run) >= 2:
            ln, = ax.plot(*zip(*run), ls="-", lw=hs.LW["connector"], color=col, marker="none",
                          solid_capstyle="butt", zorder=2)
            reg["lines"][key].append(ln)

    def letter(x, y, ch):
        ov.text(x, y, ch, ha="left", va="baseline", fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT)

    def runs_of(panel, s, xpos):
        """(x, y) runs of adjacent sizes where the strategy is drawn (a line never crosses a size not drawn)."""
        src = ranks["c"] if mut == "d_from_c" and panel == "d" else ranks[panel]
        val = {(e["core_papers"], e["strategy"]): e["pass_pct"] for e in src}
        out, run = [], []
        for c in SIZES + (None,):
            if (c, s) in val:
                run.append((xpos(c), val[(c, s)]))
                continue
            if mut == "line_across_gap" and c is not None:
                continue
            if len(run) >= 2:
                out.append(run)
            run = []
        return out

    XL, GX = 20.0, 2.6
    w = (W - 1.5 - XL - 5 * GX) / 6
    rows = (("c", head_y + 2.4, H_ROW), ("d", head_y + 2.4 + H_ROW + ROW_GAP, H_ROW))
    letter(1.0, head_y, DRAWN_LETTER["c"])
    for j, s in enumerate(STRATS):
        x0 = XL + j * (w + GX)
        ov.text(x0 + w / 2, head_y, LABEL[s], ha="center", va="baseline", fontsize=PT, gid=f"cd_head_{s}")
        if re.search(r"\d", LABEL[s]):
            printed[f"cd_head_{s}"] = {"fixed": LABEL[s], "why": "a strategy's name (column head)"}
        for panel, top, h in rows:
            ax = fig.add_axes([x0 / W, 1 - (top + h) / H, w / W, h / H])
            ax.set_xlim(-0.4, 3.4)
            ax.set_ylim(*LIM[panel])
            for run in runs_of(panel, s, lambda c: SIZES.index(c)):
                join(ax, run, s, (panel, s))
            for e in ranks[panel]:
                if e["strategy"] == s:
                    mark(ax, SIZES.index(e["core_papers"]), e["pass_pct"], s, (panel, e["core_papers"], s),
                         yerr=[e["ci95_lo_pct"], e["ci95_hi_pct"]])
            ax.xaxis.set_major_locator(FixedLocator(range(4)))
            ax.xaxis.set_major_formatter(FixedFormatter([str(c) for c in SIZES] if panel == "d" else [""] * 4))
            ax.yaxis.set_major_locator(FixedLocator(YT[panel]))
            ax.yaxis.set_major_formatter(FixedFormatter([str(v) for v in YT[panel]] if j == 0 else [""] * 3))
            ax.xaxis.set_minor_locator(NullLocator())
            ax.yaxis.set_minor_locator(NullLocator())
            if j == 0:
                ax.set_ylabel(Y_LABEL[panel])
                ax.yaxis.label.set_gid(f"ylabel_{panel}")
                printed[f"ylabel_{panel}"] = {"fixed": ax.yaxis.label.get_text(),
                                              "why": "the axis label naming the threshold (D151)"}
    letter(1.0, rows[1][1] + 1.6, DRAWN_LETTER["d"])
    x_lab_y = rows[1][1] + rows[1][2] + 7.4
    ov.text(XL + (6 * w + 5 * GX) / 2, x_lab_y, "Core papers (sizes evenly spaced)", ha="center",
            va="baseline", fontsize=PT)
    readback = read_back(reg)
    bad_col = hs.check_figure_colours(fig)
    if bad_col:
        raise SystemExit(f"{PLATE}: colours outside the house palette {bad_col}")
    S457.finish_plate(fig, W, H, paths, title=PLATE)
    return printed, readback, (W, H)


def read_back(reg):
    """What was drawn, read from the artists themselves: each matrix cell's fill, position and frame; each c and d
    dot's position and colour and its interval's ends; each line's points and colour."""
    from matplotlib.colors import to_hex
    out = {"cells": {}, "dots": {}, "lines": {}, "geom": reg["geom"]}
    for key, (rect, frame) in reg["cells"].items():
        out["cells"][key] = {"fill": to_hex(rect.get_facecolor()).upper(), "xy": tuple(rect.get_xy()),
                             "framed": frame is not None and frame.get_linewidth() >= S457.LINE_MIN_PT}
    for key, ln in reg["dots"].items():
        xy = ln.get_xydata()
        iv = reg["ivals"].get(key)
        out["dots"][key] = {"xy": (float(xy[0][0]), float(xy[0][1])), "n": len(xy),
                            "colour": to_hex(ln.get_markerfacecolor()).upper(),
                            "interval": None if iv is None else [tuple(map(float, p)) for p in iv.get_xydata()]}
    for key, lns in reg["lines"].items():
        out["lines"][key] = [{"xy": [tuple(map(float, p)) for p in ln.get_xydata()],
                              "colour": to_hex(ln.get_color()).upper()} for ln in lns]
    return out


def check_drawn(rb, drawn, cells, ranks, vmax=V):
    """Every drawn mark against the workbook rows: a matrix cell at its row, column and size, in the colour of its d,
    framed exactly where the interval excludes 0; a c or d dot at its pass rate in its strategy's mark colour, its
    interval from the row's ci95_lo_pct to ci95_hi_pct; a line for each run of adjacent sizes where the strategy is
    drawn, through its dots, none across a gap."""
    bad = []
    g = rb["geom"]
    want = set()
    for panel in "a":                             # D201 Q11: the score 4 block, the lower triangle
        for e in tri(cells[panel]):
            key = (panel, e["core_papers"], e["row_strategy"], e["column_strategy"])
            want.add(key)
            got = rb["cells"].get(key)
            if got is None:
                bad.append(f"{key}: not drawn")
                continue
            if abs(e["d_pp"]) > vmax:
                bad.append(f"{key}: d {e['d_pp']:.1f} beyond the colour scale's {vmax}")
            if got["fill"] != cividis_hex(e["d_pp"], vmax):
                bad.append(f"{key}: fill {got['fill']}, want {cividis_hex(e['d_pp'], vmax)}")
            ci, i, j = SIZES.index(e["core_papers"]), STRATS.index(e["row_strategy"]) - 1, STRATS.index(
                e["column_strategy"])
            x = g["x0"] + ci * ((len(STRATS) - 1) * g["cell"] + g["gap"]) + j * g["cell"] + g["gut"] / 2
            y = g["top"][panel] + i * g["cell"] + g["gut"] / 2
            if abs(got["xy"][0] - x) > 1e-9 or abs(got["xy"][1] - y) > 1e-9:
                bad.append(f"{key}: at {got['xy']}, want {(x, y)}")
            if got["framed"] != (e["interval_excludes_0"] == "yes" and (e["ci95_lo_pp"] > 0 or e["ci95_hi_pp"] < 0)):
                bad.append(f"{key}: framed {got['framed']}, interval [{e['ci95_lo_pp']:.2f}, {e['ci95_hi_pp']:.2f}]")
    extra = set(rb["cells"]) - want
    if extra:
        bad.append(f"cells drawn with no workbook row: {sorted(extra)[:3]}")
    horiz = False
    for panel in "cd":
        rows = {(e["core_papers"], e["strategy"]): e for e in ranks[panel]}
        got_keys = {k[1:] for k in rb["dots"] if k[0] == panel}
        if got_keys != set(rows):
            bad.append(f"{panel}: dots drawn {sorted(got_keys ^ set(rows))[:3]} not the rows'")
        for (c, s), e in rows.items():
            d = rb["dots"].get((panel, c, s))
            if d is None:
                continue
            v = d["xy"][0] if horiz else d["xy"][1]
            pos = d["xy"][1] if horiz else d["xy"][0]
            want_pos = SIZES.index(c)
            if d["n"] != 1 or abs(v - e["pass_pct"]) > 1e-9 or abs(pos - want_pos) > 1e-9:
                bad.append(f"{panel} {c} {s}: dot at {d['xy']}, want {e['pass_pct']} at {want_pos}")
            if d["colour"] != cd_style(s)[0].upper():
                bad.append(f"{panel} {c} {s}: dot colour {d['colour']}")
            iv = d["interval"]
            ends = None if iv is None else sorted(p[0 if horiz else 1] for p in iv)
            if ends is None or abs(ends[0] - e["ci95_lo_pct"]) > 1e-9 or abs(ends[1] - e["ci95_hi_pct"]) > 1e-9:
                bad.append(f"{panel} {c} {s}: interval {ends}, want [{e['ci95_lo_pct']}, {e['ci95_hi_pct']}]")
            if not e["ci95_lo_pct"] - 1e-9 <= e["pass_pct"] <= e["ci95_hi_pct"] + 1e-9:
                bad.append(f"{panel} {c} {s}: pass rate outside its interval")
        for s in STRATS:
            runs, run = [], []
            for c in SIZES + (None,):
                if (c, s) in rows:
                    run.append((SIZES.index(c), rows[(c, s)]["pass_pct"]))
                    continue
                if len(run) >= 2:
                    runs.append(run)
                run = []
            got = rb["lines"].get((panel, s), [])
            if len(got) != len(runs):
                bad.append(f"{panel} {s}: {len(got)} lines, want {len(runs)}")
                continue
            for ln, r in zip(got, runs):
                if ln["colour"] != cd_style(s)[0].upper() or len(ln["xy"]) != len(r) or any(
                        abs(p[0] - q[0]) > 1e-9 or abs(p[1] - q[1]) > 1e-9 for p, q in zip(ln["xy"], r)):
                    bad.append(f"{panel} {s}: a line through {ln['xy']}, want {r}")
    for c in SIZES:
        for panel in "cd":
            if sorted(e["strategy"] for e in ranks[panel] if e["core_papers"] == c) != sorted(drawn[c]):
                bad.append(f"{panel} {c}: strategies not the drawn ones")
    return bad


def join_words(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def missing_reason(rows6, drawn):
    """Why a covered cell of a drawn strategy has no pass or fail: the statuses g4_cells gave it, in words."""
    st = {r["cells"][s]["status"] for r in rows6 if r["covered"] for s in drawn[r["core_papers"]]
          if r["cells"][s]["pass3"] is None}
    if not st:
        return ""
    if st == {"held_g4r38"}:
        return "an answer held out as a setup error"
    if st == {"unscored"}:
        return "an answer not scored by the judge"
    if st <= {"held_g4r38", "unscored"}:
        return "an answer held out as a setup error or not scored by the judge"
    raise Refused(f"a drawn strategy has covered cells with status {sorted(st)}")


def covered_counts(by):
    """Covered questions per size, from the table (equal at the three ratios, else refused)."""
    out = {}
    for c in SIZES:
        n = {len(by[(idx_name(c, r), "single_pass")]) for r in RATIOS}
        if len(n) != 1:
            raise Refused(f"{c} core papers: covered questions differ across ratios {n}")
        out[c] = n.pop()
    return out


def counted_clause(by, covered):
    """Which questions a size counts. Every index is asked its questions; only the covered ones count (D126), and the
    counts come from `covered`. The two largest sizes are called the same questions only when their sets are equal."""
    def qs(c):
        return {q for r in RATIOS for q in by[(idx_name(c, r), "single_pass")]}
    c0, c1, c2, c3 = SIZES
    same = qs(c2) == qs(c3)
    tail = f"{c2} and {c3} count the same {covered[c2]}" if same else f"{c2} and {c3} count {covered[c2]} and {covered[c3]}"
    return (f"The questions are asked at every size, but at {c0} and {c1} core papers only the {covered[c0]} and "
            f"{covered[c1]} whose papers are in the index are counted; {tail}, so a step from {c0} to {c1} or {c1} to "
            f"{c2} also changes the questions.")


def legend_text(stamp, drawn, cells, ranks, reason, covered, by):
    full = {c: covered[c] * len(RATIOS) for c in SIZES}
    short = collections.defaultdict(set)
    for e in cells["a"]:
        if e["n_pairs"] != full[e["core_papers"]]:
            short[(e["core_papers"], e["n_pairs"])].add(frozenset((e["row_strategy"], e["column_strategy"])))
    parts = []
    for (c, n), pairs in sorted(short.items()):
        lone = [s for s in drawn[c] if pairs == {frozenset((s, t)) for t in drawn[c] if t != s}]
        if lone:                       # every pair with one strategy, and only those, is short at this size
            parts.append(f"every pair with {LABEL[lone[0]]} at {c} core papers (n = {n})")
        else:
            parts.append(join_words(sorted(" and ".join(LABEL[x] for x in sorted(p, key=STRATS.index))
                                           for p in pairs)) + f" at {c} core papers (n = {n})")
    exc = f"fewer where {reason} removes a pair: " + "; ".join(parts) if parts else ""
    vp = [c for c in SIZES if "verified_pass" in drawn[c]]
    vp_not = [c for c in SIZES if c not in vp]
    common = sorted({(e["core_papers"], e["n_pairs_common"]) for e in ranks["c"]})
    n_cmp = {c: len(drawn[c]) * (len(drawn[c]) - 1) // 2 for c in SIZES}
    cmp_words = join_words([f"{n_cmp[c]}" for c in SIZES])
    return (
        f"Legend DRAFT for {PLATE} (written by {SCRIPT}).\n\n"
        f"**{PLATE} | Every strategy against every other, by corpus size**\n\n"
        "**a**, Difference in pass rate between two strategies, row minus column, in percentage points, a "
        "pass being a judge correctness score of 4 or more (gemini-3-flash, one draw; devstral-small-2 "
        "judge). One matrix per corpus size (5, 10, 20 and 50 core papers), each pooling its three indexes (0, 1 and "
        "3 distractor papers per core paper). Each difference is over the question-index pairs where both strategies "
        "have a pass or a fail (a failed answer counts as a fail), on the questions whose source papers are all in "
        "the index: n = "
        f"{join_words([str(full[c]) for c in SIZES])} pairs ({join_words([str(covered[c]) for c in SIZES])} "
        f"questions, three indexes each)" + (f", {exc}" if exc else "") + ". Colour shows the difference "
        "(key). A black frame marks a difference whose two-sided 95% interval excludes 0 (percentile bootstrap, "
        "10,000 resamples of questions, each question carrying its pairs from all three indexes; not adjusted for "
        f"the {cmp_words} comparisons at 5, 10, 20 and 50 core papers). Each pair appears once. "
        + (f"Verified pass is drawn at {join_words([str(c) for c in vp])} core papers, where its three indexes "
           f"are judged; at {join_words([str(c) for c in vp_not])} its judging is not finished. " if vp_not else "") +
        "**b**, Pass rate of each strategy at a score "
        "of 4 or more by corpus size, one panel per strategy, sizes evenly spaced; thin lines join the dots at adjacent "
        "sizes. Dot, the pass rate on the question-index pairs where every strategy has a pass or a fail (n = "
        f"{join_words([str(n) for _, n in common])} at 5, 10, 20 and 50 core papers); bar, its two-sided 95% "
        f"interval (percentile bootstrap over questions, as in a). {counted_clause(by, covered)} "
        "**c**, As b, at the relaxed threshold, 3 or more.\n")


def caption_text(stamp, tag, k, d185: bool = False):
    return (f"# {PLATE} data, caption\n\n"
            f"**{PLATE} data | Numerical values plotted in {PLATE}.** {k} of {UNITS_TOTAL} index x "
            "strategy units of G4 draw 1 are judged complete" + (
                "; verified pass is drawn only at the sizes where its three units are complete, and every value "
                "will be redrawn by the same script when its judging ends. " if k < UNITS_TOTAL else ". ") +
            f"Data stamp: {stamp}. Sheets {SHEET['a']} and {SHEET['b']}: one row per pair of strategies and "
            "core-paper size, each pair once, row minus column, at judge score 4 or more (the pass rate, drawn in a) "
            "and 3 or more (the relaxed threshold, not drawn) (n pairs, n questions, both pass rates, the "
            "difference d in points, its two-sided 95% interval, whether it excludes 0, the indexes pooled). Sheets "
            f"{SHEET['c']} and {SHEET['d']}: each strategy's pass rate per size, at score 4 or more and at the "
            f"relaxed 3 or more, on the pairs every drawn strategy has, with its rank and its two-sided 95% interval. Sheet {SHEET_UNITS}: the {UNITS_TOTAL} index x strategy units and whether each is "
            f"judged complete. Generated by `uv run --frozen python {SCRIPT} plate` from "
            + ("findings/recompute/G4_fig3c_d185 (S514's draw-1 reading of the judge rows: key v2.5 where S6 has "
               "judged, else key v2.4), held to findings/recompute/G4_fig3c (S476's reading of the S3 judge rows).\n"
               if d185 else "findings/recompute/G4_fig3c (S476's reading of the S3 judge rows).\n"))


def word_count(legend):
    body = legend.split("\n\n", 1)[1]
    return len(re.sub(r"\*\*", "", body).split())


def legend_problems(legend):
    bad = []
    if "\u2014" in legend or "\u2013" in legend:
        bad.append("an em or en dash in the legend")
    w = word_count(legend) - len(f"{PLATE} |".split())
    if w >= int(S457.FLOCK["legend"]["words_under"]):
        bad.append(f"legend {w} words, not under {S457.FLOCK['legend']['words_under']}")
    for need in ("two-sided", "n = ", "**a**", "**b**", "**c**"):
        if need not in legend:
            bad.append(f"legend lacks {need!r}")
    return bad


# ---------------------------------------------------------------------------------------------------------------
# PLATE
# ---------------------------------------------------------------------------------------------------------------
def build(D, numbers3, scratch=None, out=OUT, write=True, quiet=False, vmax=V, mut=None, frozen_shas=None,
          scratch_R=None, D24=None):
    """scratch_R: the reading of the pull the scratch S-2 read (scratch_reading()), for gate (2); None runs gate (2)
    on the drawn reading (the scratch's pull is the drawn one). D24 (D188): the v2.4 reading (load()) when D is
    S514's (load_d185()); gate (0) runs on it first."""
    by, units = D["by"], D["units"]
    g0 = None if D24 is None else gate_v24(D24)
    g1 = gate_fig3c(per_index(by, units), numbers3)
    drawn, cells, ranks = compute(by, units)
    g2 = gate2(cells, ranks, scratch, scratch_R)
    k = sum(bool(v["complete"]) for v in units.values())
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    vp_open = [c for c in SIZES if "verified_pass" not in drawn[c]]
    stamp = (f"{k} of {UNITS_TOTAL} index x strategy units judged complete (G4 draw 1, judge S3, "
             f"devstral-small-2:24b plain call (a)); "
             + (f"verified pass not yet judged at {join_words([str(c) for c in vp_open])} core papers; " if vp_open
                else "") + (f"S476 g4c on {g4_reading_id(D['header'])}" if "d185" not in D else
                            f"S514 g4c on {g4_reading_id(D['header'])}: key v2.5 judge rows where S6 has judged one of "
                            f"the 132 questions v2.5 changed, key v2.4 for the {D['d185']['awaiting_s6_covered']} "
                            f"covered answers awaiting it"))
    cov = covered_counts(by)
    if cov != S476.COVERED_WANT:
        raise Refused(f"covered questions {cov}, not D126's {S476.COVERED_WANT}")
    legend = legend_text(stamp, drawn, cells, ranks, missing_reason(D["rows6"], drawn), cov, by)
    lp = legend_problems(legend)
    if lp:
        raise Refused("; ".join(lp))
    tmp = Path(tempfile.mkdtemp(prefix="s484_"))
    base = f"{PLATE}{tag}"
    paths = {x: tmp / f"{base}.{x}" for x in ("pdf", "svg", "png")}
    printed, rb, (W, H) = draw(paths, drawn, cells, ranks, vmax=vmax, mut=mut)
    bad = check_drawn(rb, drawn, cells, ranks, vmax=vmax)
    if bad:
        shutil.rmtree(tmp, ignore_errors=True)
        raise Refused(f"check_drawn ({len(bad)}): " + "; ".join(bad[:4]))
    res = {"drawn": drawn, "cells": cells, "ranks": ranks, "gate0": g0, "gate1": g1, "gate2": g2, "legend": legend,
           "stamp": stamp,
           "tag": tag, "k": k, "tmp": tmp, "page_mm": [W, H],
           "frames": sum(e["interval_excludes_0"] == "yes" for e in tri(cells["a"]))}
    if not write:
        return res
    cols = {p: list(cells[p][0]) for p in "ab"} | {p: list(ranks[p][0]) for p in "cd"}
    sheets = {SHEET[p]: {"columns": cols[p], "rows": [[e[c] for c in cols[p]] for e in (
        tri(cells[p]) if p in "ab" else ranks[p])]} for p in "acdb"}
    ucols = ["core_papers", "distractor_ratio", "index", "strategy", "strategy_label", "complete", "drawn_at_size"]
    sheets[SHEET_UNITS] = {"columns": ucols, "rows": [[c, r, idx_name(c, r), s, LABEL[s],
                                                       "yes" if unit_complete(units, s, idx_name(c, r)) else "no",
                                                       "yes" if s in drawn[c] else "no"]
                                                      for c in SIZES for r in RATIOS for s in STRATS]}
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, sh in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(sh["columns"])
        for r in sh["rows"]:
            ws.append(r)
    xlsx = tmp / f"{PLATE} data{tag}.xlsx"
    wb.save(xlsx)
    fig_repro.deterministic_xlsx(xlsx)                 # D155: no write time in core.xml or the zip members
    fig_repro.check_pdf_deterministic(paths["pdf"])
    fig_repro.check_svg_deterministic(paths["svg"])
    cap = tmp / f"{PLATE} data caption{tag}.md"
    cap.write_text(caption_text(stamp, tag, k, "d185" in D))
    numbers = {"stamp": stamp, "sheets": sheets, "printed": printed,
               "drawn_strategies_by_core_papers": {str(c): v for c, v in drawn.items()},
               "colour_scale_pp": [-vmax, vmax], "colour_map": "cividis", "strategy_colours": COLOUR,
               "framed_cells": res["frames"], "page_mm": [W, H]}
    nf = tmp / f"{SIDE}_numbers.json"
    nf.write_text(json.dumps(numbers, indent=1) + "\n")
    lg = tmp / "legend_draft.md"
    lg.write_text(legend)
    inputs = [G4DIR / f for f in ("header.json", "grid_pairs.jsonl", "grid_tables.json", "pairs.jsonl",
                                  "point_tables.json", "anchor_d149_rlm10.json")] + \
        ([G4D185 / f for f in S476.G4_D185_FILES] if "d185" in D else []) + \
        [FIG3_NUMBERS, ROOT / "scripts" / "S476_fig3_d123.py", S457.FIGURE_LOCK]
    files = [paths["pdf"], paths["svg"], paths["png"], xlsx, cap, nf, lg]
    me = Path(__file__).resolve()
    prov = {"stamp": stamp, "script": SCRIPT, "script_sha256": sha(me),
            "command": f"uv run --frozen python {SCRIPT} plate" + (
                " --frozen" if frozen_shas is not None else (" --copy <pull>" if D["tied"] else "") +
                (" --scratch <S-2 numbers>" if scratch is not None else "") +
                (" --scratch-copy <its pull>" if scratch_R is not None else "")),
            "python": platform.python_version(), "frozen_inputs_sha256": frozen_shas,
            "figure": PLATE, "page_mm": [W, H],
            "decisions": ["D151 (S-2 design)", "D152 (Supplementary stack)", "D126 (covered questions)",
                          "D147 (colour-only key)", "D92 Q194 (Supplementary naming)"],
            "inputs_sha256": {rel(p): sha(p) for p in inputs},
            "gate2_pull": None if scratch_R is None else scratch_R["copy"],
            "g4_reading": {"from": rel(G4D185) if "d185" in D else rel(G4DIR), "g4c_on": g4_reading_id(D["header"]),
                           "s476_pull": D["header"]["copy"],
                           **({"v2.4_anchor": {"from": rel(G4DIR), "tied_to_pull_by_g4_cells": D["tied"]},
                               "d185": D["d185"]} if "d185" in D else {"tied_to_pull_by_g4_cells": D["tied"]})},
            "reproduced": {"gate0_g4_fig3c_v24": g0, "gate1_source_data_fig3c": g1, "gate2_scratch_s2": g2,
                           "check_drawn": f"{len(tri(cells['a']))} cells, "
                                          f"{sum(len(ranks[p]) for p in 'cd')} dots and their lines read back"},
            "lock_sha256": sha(S457.FIGURE_LOCK),
            "files": {p.name: sha(p) for p in files}}
    pf = tmp / f"{SIDE}_provenance.json"
    pf.write_text(json.dumps(prov, indent=1) + "\n")
    out.mkdir(parents=True, exist_ok=True)
    for p in out.iterdir():
        if p.name.startswith((PLATE + " ", PLATE + ".", SIDE)) or p.name == "legend_draft.md":
            p.unlink()
    for p in files + [pf]:
        shutil.copyfile(p, out / p.name)
    shutil.rmtree(tmp, ignore_errors=True)
    res["out"] = out
    if not quiet:
        if g0 is not None:
            print(f"gate (0): {g0['complete']} of {g0['cells']} cells of G4_fig3c's grid (key v2.4), {g0['values']} values "
                  f"equal")
        print(f"gate (1): {g1['complete']} of {g1['cells']} sheet Supplementary Fig. 7c cells complete, {g1['values']} values "
              f"equal; gate (2): {'not run' if g2 is None else str(g2['values']) + ' values equal to the scratch S-2'}"
              f"; drawn {len(tri(cells['a']))} cells ({res['frames']} framed), "
              f"{sum(len(ranks[p]) for p in 'cd')} dots; legend {word_count(legend)} words; wrote {rel(out)}")
    return res


def plate(copy=None, scratch=None, frozen=False, out=None, scratch_copy=None) -> int:
    S457.figure_lock_agreed()
    try:
        out = OUT if out is None else Path(out).expanduser().resolve()
        if out != OUT and out.exists() and any(out.iterdir()):
            raise Refused(f"{out} exists and is not empty: write the plate into a new folder")
        shas = None
        if frozen:
            if copy is not None or scratch is not None:
                raise Refused("--frozen reads the frozen copy and scratch numbers: no --copy or --scratch")
            if scratch_copy is not None:
                raise Refused("--frozen reads the scratch's frozen pull itself: no --scratch-copy")
            copy, scratch, shas, scratch_copy = frozen_inputs(OUT / f"{SIDE}_provenance.json")
        D24 = load(copy)
        D = load_d185(D24)                              # D188: drawn; D24 is its v2.4 anchor
        numbers3 = json.loads(FIG3_NUMBERS.read_text())
        sc = json.loads(Path(scratch).read_text()) if scratch else None
        if scratch_copy is not None and sc is None:
            raise Refused("--scratch-copy is the pull of --scratch's numbers: give --scratch too")
        R = scratch_reading(scratch_copy) if scratch_copy is not None else None
        if frozen:                                     # reproduce against the committed record before writing
            res = build(D, numbers3, sc, write=False, quiet=True, scratch_R=R, D24=D24)
            shutil.rmtree(res["tmp"], ignore_errors=True)
            print("frozen inputs: " + legacy_check(OUT / f"{SIDE}_provenance.json", res, D))
        build(D, numbers3, sc, out=out, frozen_shas=shas, scratch_R=R, D24=D24)
    except Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    return 0


# ---------------------------------------------------------------------------------------------------------------
# SELFTEST AND MUTANTS (a fixture; nothing in the repository is read for data or written)
# ---------------------------------------------------------------------------------------------------------------
def fixture(seed=7):
    """Six strategies x 12 indexes in S476's grid_pairs shape: covered and uncovered questions, a few held (None)
    cells, verified pass incomplete at 10 (one ratio) and 50 (all), so it is drawn at 5 and 20 with a gap between."""
    rng = np.random.default_rng(seed)
    ncov = {5: 6, 10: 8, 20: 10, 50: 10}
    rows, units = [], {}
    for c in SIZES:
        base = {f"q{c}_{j:02d}": rng.random() for j in range(ncov[c] + 3)}
        for r in RATIOS:
            i = idx_name(c, r)
            for s in STRATS:
                inc = s == "verified_pass" and (c == 50 or (c == 10 and r == 1))
                units[f"{s} {i}"] = {"complete": not inc}
            for j, (q, p) in enumerate(sorted(base.items())):
                cells = {}
                for s in STRATS:
                    u = rng.random()
                    held = s == "rlm_20" and j == 1 and r == 3
                    if not units[f"{s} {i}"]["complete"]:
                        cell = {"status": "not_judged", "correctness": None, "pass3": None, "pass4": None,
                                "failed": False}
                    elif held:
                        cell = {"status": "held_g4r38", "correctness": None, "pass3": None, "pass4": None,
                                "failed": False}
                    else:
                        sc = int(np.clip(round(1 + 4 * (0.6 * p + 0.4 * u)), 1, 5))
                        cell = {"status": "ok", "correctness": sc, "pass3": int(sc >= 3), "pass4": int(sc >= 4),
                                "failed": False}
                    cells[s] = cell
                cov = j < ncov[c]
                rows.append({"index": i, "core_papers": c, "distractor_ratio": r, "question_id": q, "common": True,
                             "covered": cov, "per_size": True, "cells": cells,
                             "both_units_complete": True})
    return rows, units


def fig3c_numbers(rows, units):
    """The fixture's sheet Supplementary Fig. 7c as S476 writes it (grid_tables, grid_sheet): the reference of gate (1)."""
    idxs = [idx_name(c, r) for c in SIZES for r in RATIOS]
    grid = S476.grid_tables(rows, idxs, units)
    sh = S476.grid_sheet(grid)
    return {"sheets": {FIG3_SHEET: {"columns": S476.GRID_COLS, "rows": [[x[k] for k in S476.GRID_COLS] for x in sh]}}}


def ref_pooled(rows, a, b, core, k):
    """An independent pooled reading: explicit loops and the resampling drawn here from S463's seed and count."""
    pairs = []
    for r in rows:
        if r["core_papers"] != core or not r["covered"]:
            continue
        x, y = r["cells"][a][f"pass{3 + k}"], r["cells"][b][f"pass{3 + k}"]
        if x is not None and y is not None:
            pairs.append((r["question_id"], x - y))
    qs = sorted({q for q, _ in pairs})
    num = np.array([sum(d for q2, d in pairs if q2 == q) for q in qs], dtype=float)
    den = np.array([sum(1 for q2, _ in pairs if q2 == q) for q in qs], dtype=float)
    idx = np.random.default_rng(S463.SEED).integers(0, len(qs), size=(S463.N_BOOT, len(qs)))
    top, bot = num[idx].sum(axis=1), den[idx].sum(axis=1)
    ok = bot > 0
    lo, hi = np.percentile(top[ok] / bot[ok], [2.5, 97.5])
    return {"n": len(pairs), "d": 100 * sum(d for _, d in pairs) / len(pairs), "lo": 100 * lo, "hi": 100 * hi}


LAST_FAILS: list = []


def selftest(quiet=False, mut=None) -> int:
    fails = []

    def check(name, ok, detail=""):
        if not ok:
            fails.append(f"{name}: {detail}")
        elif not quiet:
            print(f"  ok  {name}")

    rows, units = fixture()
    by = table(rows)
    drawn, cells, ranks = compute(by, units)
    # T1, T2: every pooled cell against the independent reading
    worst = 0.0
    for p in "ab":
        k = K[p]
        for e in cells[p]:
            r = ref_pooled(rows, e["row_strategy"], e["column_strategy"], e["core_papers"], k)
            worst = max(worst, abs(r["n"] - e["n_pairs"]), abs(r["d"] - e["d_pp"]), abs(r["lo"] - e["ci95_lo_pp"]),
                        abs(r["hi"] - e["ci95_hi_pp"]))
    check("pooled n, d and interval equal an independent reading (loops, S463's seed)", worst < 1e-9, f"{worst}")
    # T3: antisymmetry
    aa = {(e["core_papers"], e["row_strategy"], e["column_strategy"]): e for e in cells["a"]}
    asym = [k for k, e in aa.items() if abs(e["d_pp"] + aa[(k[0], k[2], k[1])]["d_pp"]) > 1e-9
            or e["n_pairs"] != aa[(k[0], k[2], k[1])]["n_pairs"]]
    check("each comparison twice with opposite signs and one n", not asym, f"{asym[:2]}")
    # T4: drawn rule
    check("verified pass drawn only where its three units are complete",
          [c for c in SIZES if "verified_pass" in drawn[c]] == [5, 20], f"{drawn}")
    check("a size draws every other strategy", all(len(drawn[c]) >= 5 for c in SIZES), f"{drawn}")
    # T5: the common set of c and d, derived again
    for p in "cd":
        k = K[p]
        bad = []
        for c in SIZES:
            pr = [(r["index"], r["question_id"]) for r in rows if r["core_papers"] == c and r["covered"] and all(
                r["cells"][s]["pass3"] is not None for s in drawn[c])]
            for e in (x for x in ranks[p] if x["core_papers"] == c):
                rate = 100 * sum(next(r for r in rows if (r["index"], r["question_id"]) == key)["cells"][e["strategy"]]
                                 [f"pass{3 + k}"] for key in pr) / len(pr)
                if e["n_pairs_common"] != len(pr) or abs(rate - e["pass_pct"]) > 1e-9:
                    bad.append((c, e["strategy"], e["pass_pct"], rate))
        check(f"panel {p}: each pass rate on the pairs every drawn strategy has", not bad, f"{bad[:2]}")
    # T6: gate (1) against S476's own Source Data of the fixture; it refuses a changed cell or a changed flag
    num3 = fig3c_numbers(rows, units)
    try:
        g = gate_fig3c(per_index(by, units), num3)
        check("gate (1) passes on S476's own Source Data of the fixture", g["complete"] == 120 - 2 * 4, f"{g}")
    except Refused as e:
        check("gate (1) passes on S476's own Source Data of the fixture", False, str(e)[:200])
    for what, edit in (("a d changed by 1e-6", lambda r, c: r.__setitem__(c.index("d_pp"), r[c.index("d_pp")] + 1e-6)),
                       ("an interval end changed by 1e-6",
                        lambda r, c: r.__setitem__(c.index("ci95_hi_pp"), r[c.index("ci95_hi_pp")] + 1e-6)),
                       ("a completeness flag flipped",
                        lambda r, c: r.__setitem__(c.index("complete"), not r[c.index("complete")]))):
        n2 = json.loads(json.dumps(num3))
        sh = n2["sheets"][FIG3_SHEET]
        row = next(r for r in sh["rows"] if r[sh["columns"].index("complete")])
        edit(row, sh["columns"])
        try:
            gate_fig3c(per_index(by, units), n2)
            check(f"gate (1) refuses {what}", False, "passed")
        except Refused:
            check(f"gate (1) refuses {what}", True)
    # T6b (D188): gate (0), the v2.4 anchor, passes on S476's own grid of the fixture and refuses a changed cell
    idxs = [idx_name(c, r) for c in SIZES for r in RATIOS]
    D24 = {"by": by, "units": units, "grid": S476.grid_tables(rows, idxs, units)}
    try:
        g0 = gate_v24(D24)
        check("gate (0) passes on S476's own grid of the fixture (D188)", g0["complete"] == 120 - 2 * 4, f"{g0}")
    except Refused as e:
        check("gate (0) passes on S476's own grid of the fixture (D188)", False, str(e)[:200])
    D24b = json.loads(json.dumps(D24["grid"]))
    next(e for e in D24b["cells"] if e["complete"])["d_pp"] += 1e-6
    try:
        gate_v24({**D24, "grid": D24b})
        check("gate (0) refuses a grid cell's d changed by 1e-6 (D188)", False, "passed")
    except Refused:
        check("gate (0) refuses a grid cell's d changed by 1e-6 (D188)", True)
    # T7: gate (2) passes on itself and refuses a changed value
    sc = {"cells": {SCRATCH_PANEL[p]: cells[p] for p in "ab"},          # the scratch's panel letters (gate (2))
          "ranks": {SCRATCH_PANEL[p]: ranks[p] for p in "cd"}}
    try:
        gate_scratch(cells, ranks, sc)
        check("gate (2) passes on the same numbers", True)
    except Refused as e:
        check("gate (2) passes on the same numbers", False, str(e)[:200])
    sc2 = json.loads(json.dumps(sc))
    sc2["ranks"]["d"][0]["pass_pct"] += 1e-6
    try:
        gate_scratch(cells, ranks, sc2)
        check("gate (2) refuses a changed pass rate", False, "passed")
    except Refused:
        check("gate (2) refuses a changed pass rate", True)
    # T7b (D156): gate (2) runs on the scratch's own pull when the plate is drawn from a later one: numbers of
    # another reading (one pass flipped) pass on that reading and are refused on the drawn one
    rows2 = json.loads(json.dumps(rows))
    flip = next(r for r in rows2 if r["covered"] and r["core_papers"] == 10 and r["cells"]["rlm_10"]["pass3"] is not None)
    flip["cells"]["rlm_10"]["pass3"] = 1 - flip["cells"]["rlm_10"]["pass3"]
    R = {"by": table(rows2), "units": units, "rows": len(rows2), "units_complete": 0, "g4r38_judged": 0}
    _, cR, rR = compute(R["by"], R["units"])
    scR = {"cells": {SCRATCH_PANEL[p]: cR[p] for p in "ab"}, "ranks": {SCRATCH_PANEL[p]: rR[p] for p in "cd"}}
    try:
        gR = gate2(cells, ranks, scR, R)
        check("gate (2) runs on the scratch's own pull (D156)", "D156" in gR["reading"], f"{gR}")
    except Refused as e:
        check("gate (2) runs on the scratch's own pull (D156)", False, str(e)[:200])
    try:
        gate2(cells, ranks, scR, None)
        check("gate (2) on the drawn reading refuses the other pull's numbers", False, "passed")
    except Refused:
        check("gate (2) on the drawn reading refuses the other pull's numbers", True)
    # T8: draw the fixture, read it back, and the legend
    vmax = 5 * np.ceil(max(abs(e["d_pp"]) for p in "ab" for e in cells[p]) / 5) + 1
    tmp = Path(tempfile.mkdtemp(prefix="s484_selftest_"))
    try:
        paths = {x: tmp / f"plate.{x}" for x in ("pdf", "svg", "png")}
        _, rb, _ = draw(paths, drawn, cells, ranks, vmax=vmax, mut=mut)
        bad = check_drawn(rb, drawn, cells, ranks, vmax=vmax)
        check("check_drawn passes on the fixture plate", not bad, f"{bad[:3]}")
        key = next(iter(rb["dots"]))
        rb["dots"][key]["xy"] = (rb["dots"][key]["xy"][0], rb["dots"][key]["xy"][1] + 0.5)
        check("check_drawn catches a dot moved by 0.5 points", bool(check_drawn(rb, drawn, cells, ranks, vmax=vmax)))
        check("the PDF, SVG and PNG written", all(p.exists() and p.stat().st_size for p in paths.values()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    try:
        leg = legend_text("STAMP", drawn, cells, ranks, missing_reason(rows, drawn), covered_counts(by), by)
    except Refused as e:
        leg = ""
        check("the fixture legend is written", False, str(e)[:200])
    probs = legend_problems(leg) if leg else ["no legend"]
    # the fixture's short pairs and undrawn strategy add clauses the real data do not have, so it runs past the limit;
    # build() holds the real legend to legend_problems as it stands, and this proves the limit fires
    over = [x for x in probs if "words, not under" in x]
    check("the fixture legend has no dash and names n and two-sided", not [x for x in probs if x not in over], str(probs))
    check("the word limit fires on the fixture legend, which is over it", bool(over), str(probs))
    check("D201 Q11: panel letters a, b, c and no d", "**d**" not in leg and all(f"**{x}**" in leg for x in "abc"))
    check("D201 Q11: tri() holds each pair once, every row after its column",
          len(tri(cells["a"])) == len(cells["a"]) // 2
          and all(STRATS.index(e["row_strategy"]) > STRATS.index(e["column_strategy"]) for e in tri(cells["a"]))
          and len({frozenset((e["core_papers"], e["row_strategy"], e["column_strategy"])) for e in tri(cells["a"])})
          == len(tri(cells["a"])), f"{len(tri(cells['a']))} of {len(cells['a'])}")
    check("D201 Q11: score 3's pairs keep their intervals in their own sheet, not a panel letter",
          SHEET["b"].endswith("score 3") and len(SHEET["b"]) <= 31 and all("ci95_lo_pp" in e and "ci95_hi_pp" in e for e in tri(cells["b"])))
    check("the legend says the questions are counted, not asked, at the small sizes",
          "are counted" in leg and "are asked;" not in leg)
    check("the legend names where verified pass is drawn", "Verified pass is drawn at 5 and 20 core papers" in leg)
    check("the legend says a failed answer counts as a fail and names the generator",
          "a failed answer counts as a fail" in leg and "gemini-3-flash-preview" in leg and "scored answer" not in leg)
    LAST_FAILS[:] = fails
    if fails:
        if not quiet:
            print("SELFTEST FAIL:\n  " + "\n  ".join(fails))
        return 1
    if not quiet:
        print("SELFTEST PASS")
    return 0


def _mut_pooled_none_as_zero():
    orig = pooled

    def m(by, a, b, idxs, k):
        by2 = collections.defaultdict(dict)
        for key, v in by.items():
            by2[key] = {q: tuple(0 if x is None else x for x in t) for q, t in v.items()}
        return orig(by2, a, b, idxs, k)
    return {"pooled": m}


def _mut_resample_pairs():
    def m(by, a, b, idxs, k):
        d, xs, ys, qs = [], 0, 0, set()
        for i in idxs:
            for q, t in by[(i, a)].items():
                x, y = t[k], by[(i, b)].get(q, (None, None))[k]
                if x is None or y is None:
                    continue
                d.append(x - y)
                xs, ys = xs + x, ys + y
                qs.add(q)
        if not d:
            return {"n_pairs": 0}
        ci = S463.interval(d, [1.0] * len(d))
        return {"n_pairs": len(d), "n_questions": len(qs), "pass_a_pct": 100 * xs / len(d),
                "pass_b_pct": 100 * ys / len(d), "d_pp": 100 * sum(d) / len(d), "ci95_pp": [100 * ci[0], 100 * ci[1]]}
    return {"pooled": m}


def _mut_score4_from_3():
    orig = pooled
    return {"pooled": lambda by, a, b, idxs, k: orig(by, a, b, idxs, 0)}


def _mut_sign():
    orig = pooled

    def m(by, a, b, idxs, k):
        r = orig(by, b, a, idxs, k)
        if r["n_pairs"]:
            r["pass_a_pct"], r["pass_b_pct"] = r["pass_b_pct"], r["pass_a_pct"]
        return r
    return {"pooled": m}


def _mut_any_ratio():
    return {"drawn_by_size": lambda units: {c: [s for s in STRATS if any(unit_complete(units, s, idx_name(c, r))
                                                                         for r in RATIOS)] for c in SIZES}}


def _mut_two_ratios():
    orig = pooled
    return {"pooled": lambda by, a, b, idxs, k: orig(by, a, b, idxs[:2] if len(idxs) == 3 else idxs, k)}


def _mut_common_two_ratios():
    orig = common_pairs
    return {"common_pairs": lambda by, c, drawn_c: [(i, q) for i, q in orig(by, c, drawn_c)
                                                    if not i.endswith(f"_n{RATIOS[-1]}")]}


def _mut_gate_tol():
    orig = gate_fig3c
    return {"gate_fig3c": lambda mine, numbers, tol=TOL: orig(mine, numbers, tol=1e-3)}


def _mut_gate_skip_ci():
    def m(mine, numbers, tol=TOL):
        sh = numbers["sheets"][FIG3_SHEET]
        ref = {(x["score"], x["index"], x["strategy"]): x for x in (dict(zip(sh["columns"], r)) for r in sh["rows"])}
        bad = []
        for e in mine:
            x = ref[(e["score"], e["index"], e["strategy"])]
            if bool(x["complete"]) != e["complete"]:
                bad.append(1)
            elif e["complete"] and abs(e["d_pp"] - x["d_pp"]) > tol:
                bad.append(1)
        if bad:
            raise Refused("x")
        return {"cells": len(mine), "complete": sum(e["complete"] for e in mine), "values": 0}
    return {"gate_fig3c": m}


def _mut_gate2_skip_ranks():
    orig = gate_scratch
    return {"gate_scratch": lambda cells, ranks, scratch, tol=TOL: orig(
        cells, ranks, {"cells": scratch["cells"], "ranks": {SCRATCH_PANEL[p]: ranks[p] for p in "cd"}})}


def _mut_check_drawn_off():
    return {"check_drawn": lambda *a, **k: []}


MUTANTS = [
    ("a missing cell counted as a fail", _mut_pooled_none_as_zero, None),
    ("the interval resamples pairs, not questions", _mut_resample_pairs, None),
    ("score 4 read as score 3", _mut_score4_from_3, None),
    ("the difference column minus row", _mut_sign, None),
    ("a strategy drawn at a size where one ratio is complete", _mut_any_ratio, None),
    ("pooled over two ratios only", _mut_two_ratios, None),
    ("c and d's common set drops the third ratio", _mut_common_two_ratios, None),
    ("gate (1) at tolerance 1e-3", _mut_gate_tol, None),
    ("gate (1) compares d only", _mut_gate_skip_ci, None),
    ("gate (2) skips c and d", _mut_gate2_skip_ranks, None),
    ("check_drawn finds nothing", _mut_check_drawn_off, None),
    ("frames where the interval includes 0", None, "frame_inverted"),
    ("D201 Q11: the matrices drawn at score 3", None, "matrix_at_score_3"),
    ("D201 Q11: the upper triangle drawn", None, "upper_triangle"),
    ("panel d drawn at c's values", None, "d_from_c"),
    ("a line joined across a size not drawn", None, "line_across_gap"),
]


def mutants() -> int:
    g = globals()
    killed, alive = 0, []
    for name, make, draw_mut in MUTANTS:
        saved = {}
        if make is not None:
            for k, v in make().items():
                saved[k] = g[k]
                g[k] = v
        try:
            rc = selftest(quiet=True, mut=draw_mut)
        except Exception as e:          # a mutant that crashes the selftest is killed
            rc = f"crash {type(e).__name__}"
        finally:
            g.update(saved)
        if rc:
            killed += 1
            why = rc if isinstance(rc, str) else (LAST_FAILS[0] if LAST_FAILS else "?")
            print(f"  killed  {name}  <- {why[:110]}")
        else:
            alive.append(name)
            print(f"  ALIVE   {name}")
    print(f"MUTANTS {killed}/{len(MUTANTS)} killed" + (f"; alive: {alive}" if alive else ""))
    return 0 if not alive else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plate")
    p.add_argument("--copy", type=Path, default=None)
    p.add_argument("--scratch", type=Path, default=None)
    p.add_argument("--scratch-copy", type=Path, default=None,
                   help="the pull --scratch's numbers were computed on, when it is not --copy (D156)")
    p.add_argument("--frozen", action="store_true", help="the frozen copy and scratch numbers (D155): the one command")
    p.add_argument("--out", type=Path, default=None, help="write the plate here, not into the committed folder")
    sub.add_parser("selftest")
    sub.add_parser("mutants")
    a = ap.parse_args(argv)
    if a.cmd == "plate":
        return plate(a.copy.resolve() if a.copy else None, a.scratch, frozen=a.frozen, out=a.out,
                     scratch_copy=a.scratch_copy.resolve() if a.scratch_copy else None)
    if a.cmd == "selftest":
        return selftest()
    return mutants()


if __name__ == "__main__":
    raise SystemExit(main())
