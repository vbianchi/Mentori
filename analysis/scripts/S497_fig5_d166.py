#!/usr/bin/env python3
"""S497 - Figure 5 as D166 locks it: the assembled plate of 28 October (version 2), drawn from frozen inputs.

D166 (Valerio, 28 October, "Overall figure 5 is fine. I like it, just lock it."; experiments/README.md): Figure 5's
design is the assembled version 2, built in the session scratch by figopts_1028/fig5_assembled/build_fig5.py. Seven
panels on one 183 mm plate, every text 8 pt:
  a  three signals per strategy: per question the judge's pass share over three draws (score 4 or more), concept
     recall (L3's loose matcher, the mean of three draws) and MiniCheck precision against the papers (draw 1); grey
     dots (questions), quartile box, median line, Tukey whiskers; a box whose quartiles are equal is drawn as its
     median line, taller than the dots
  b  draw-1 answers on the W questions split four ways by the judge's verdict and by MiniCheck precision at or above
     the pooled median of those answers
  c  of the same answers, those with concept recall 1 (every key concept), by the judge's verdict
  d  per signal, the questions where single pass or the strategy scores higher, and ties (judge correctness and
     concept recall as three-draw means per question, MiniCheck precision draw 1)
  e  per draw, (wins minus losses) / questions x 100 of each strategy against single pass, per signal
  f  the judge's faithfulness score (the call with passages) of the answers it passes and fails on correctness
  g  MiniCheck precision of draw-1 answers with faithfulness 5 and below 5
Strategy order everywhere: single pass, multi-hop, verified pass, RLM-5, RLM-10, RLM-20.

WHY A SCRIPT OF ITS OWN (as S476 beside S475 for Figure 3: D123 gave it a script of its own, D152 locked the
plate). S473 holds the pull, the readers, the checks and compute() for Figure 5's signals, and its own plate of 26
October (five panels, a different design). The locked plate shares none of S473's drawing and reads another pull (28
October), so it is drawn here. S497 imports S473 and calls its readers and compute() unchanged, so every signal value is S473's; the per-panel counts that the
scratch build took from its seven panel builds (each panel's data step, frozen in
findings/recompute/fig5_1028_inputs/anchor_d166/code/) are computed here from S473's readers' rows (a's Judge column,
b and g from compute()'s output; a's Concepts and Papers, c, d, e and f from the rows with compute()'s rules, d's
means checked against compute()'s), and the drawing is build_fig5.py's, ported.

THE ONE COMMAND (D155; S494 calls it), from the repository root, with the tars below in FROZEN_TARS (default
~/Mentori_scratch_keep/frozen_2026-10-26, or the Zenodo deposit's data files):
    uv run --frozen python scripts/S497_fig5_d166.py figure [--out <folder>]
It writes into --out (default findings/figures_provisional/fig5/): "Figure 5.{pdf,svg,png}",
"Source Data Fig. 5.xlsx" and its caption, figure5_numbers.json, figure5_provenance.json,
legend_draft.md, methods_notes.md and fig5_data_state.json (claims.md only with --claims-out DIR, into DIR: D2, the
editorial step S616 claims). n of 516 is compute()'s all4: the draw-1
answerable answers with a final row from all four scorers, of the 516 planned (S473 PLANNED["papers"]). A second run
writes the same bytes, in any time zone (no time, git state or temporary path in any file but the collect's own
time, read in COLLECT_TZ by collect_utc; fig_repro's deterministic PDF, SVG and xlsx; PYTHONHASHSEED pinned to 0,
fig_repro.pin_hash_seed).
    uv run --frozen python scripts/S497_fig5_d166.py figure --from <a pull folder of S473 pull>
reads a new pull instead (S473.pull_sources); the reproduction against the locked plate (below, 4) is then made only
when the pull's L1 rows and collect are the frozen ones, and the provenance says which.
    uv run --frozen python scripts/S497_fig5_d166.py selftest      (offline, no model call, about 15 seconds)

FROZEN INPUTS (fig_repro.frozen(); nothing read from the scratch folder or another machine):
  findings/recompute/fig5_1028_inputs/   frozen by frozen_inputs/freeze_fig5_1028.py: the 28 October pull's PULL.json,
                                         l1/ (L1's header and its key, papers and overlap rows from the Studio) and
                                         s3/'s sidecar; s3/IDENTICAL_FILES.tsv names the rest of s3/ (collect, outs,
                                         G1R15 records) where the same bytes are frozen; anchor_d166/ holds the locked
                                         plate's numbers.json, figure5_numbers.json, legend.md and PNG (and the
                                         scratch code that made them, a record only)
  findings/recompute/fig2_inputs/        g1_collect.jsonl (f5ff75bc, the same bytes as the 28 October pull's) and the
                                         outs out/ and out_g1r15/ it was collected from
  k1_inputs_runs.tar, fig2_g1r15_inputs.tar   G1's generation records, as S473 reads them
  repository files                       L3's rows and header, S26's and S30's deposited inputs, G1's rerun list, each
                                         pinned to the sha256 S473's FROZEN_SHA256 holds
Each committed frozen file is checked against frozen_inputs/SHA256SUMS (fig_repro.check_committed), each tar member
against its members list, each repository input against its pin and each file IDENTICAL_FILES.tsv names against its
line; an input read and pinned nowhere stops the run. The collect's sidecar names the scratch pull's s3/out and
s3/out_g1r15; S463.read_collect finds the outs through it, so the run reads a copy of the sidecar with that folder
prefix replaced by fig2_inputs/ (as S473 frozen_sources does), in a temporary folder.

REPRODUCE BEFORE WRITING (README.md:75-79). Nothing is written (exit 1, "REFUSED") unless (in the order 1, 2, 4, 3):
  1. S473.reproduce(): W 0.927, exact P 0.000181, mean rho 0.9037, PC1 0.9361, participation ratio 1.137 from S26's
     and S30's deposited inputs; S463's and S457's resample counts equal; L3's rows equal its header's counts;
  2. S3's judged answers equal the texts L1 and L3 scored (answer sha256, S473's check), and the judge rows read
     again from the raw outs (out/, then out_g1r15/'s 15 reruns over it, the later line of an answer winning) give
     the collect's correctness for every answer (as the scratch recount.py did);
  3. S473.check_fig2: S473's own sheet a (S473.build_sheets) gives Figure 2's committed sheet 2a pass rate,
     interval and questions per strategy at score 4 and 3 (Figure 2 written from the same collect, f5ff75bc). D201 Q2 (2
     November 2026): that plate is now Figure 3, held as it stood at commit 94262a0e (S473.FIG3_V24_AT, git show), the
     last one on key v2.4, so this check keeps testing the same 48 values until Figure 5 moves to key v2.5;
  4. with the frozen inputs, every per-panel number computed here equals the locked plate's numbers.json (its
     "panels", the scratch build's every drawn number), before drawing; after drawing, before anything is moved into
     --out, every drawn number (numbers.json "panels" but its source paths), the seven Source Data sheets and the
     printed-number map (figure5_numbers.json), the legend (legend.md) and the PNG pixel by pixel equal the locked
     plate's.
The legend is the locked one; the data-dependent words in it (the counts, the strategies with 82 papers questions, the
collapsed box, the unlabelled count, the 19 RLM fails) are checked against the data and refused when they no longer
hold, so a rebuild on other data stops for the legend to be rewritten rather than printing a stale sentence.

D186 (Valerio, 31 October; experiments/README.md "D186"), the default since:
  (3) the judge rows are read through scripts/judge_rows_v25.py (S463.judge_rows, as Figure 2): an answer's key v2.5
      row (S512, out_s6_g1 with out_s6_g1r15 as --replace, under figure --s6, else beside the outs the collect read)
      where one exists, else its key v2.4 row. The checks 1, 2 and 4 above (the locked plate drawn again and held to
      anchor_d166) run on the v2.4 collect alone (read_and_compute); only then does with_judge_rows read the rows
      through the reader, on a copy, and a v2.5 row chosen replaces the v2.4 row in every panel (the cells, the call
      with passages of f, the raw rows b is held to). Check 3 (Figure 2's pass rates) runs on the rows chosen, as
      Figure 2 reads them. With no S6 outs every answer is read from key v2.4 and the provenance says "awaiting S6"
      with the count.
  (4) concept recall is D181's reading, findings/recompute/L3_d181 (S471 --d181: S505's loose matcher with the
      question rule, Q-need, reading (b), key v2.5), in place of L3's loose matcher. Reproduce first: the whole
      locked plate is built on L3's loose reading as before and held to anchor_d166 (4 above, before and after
      drawing, the PNG included) in a temporary folder; only then is L3_d181 read (read_l3_d181: its two files pinned
      by sha256, its header D181's and final, its answers L3's answer for answer, and on the questions whose concepts
      v2.5 left unchanged its loose base equal to L3's loose value) and the plate drawn from it. Its rows enter
      S473.compute under L3's column names (concept_recall_loose := concept_recall, found_loose := found, n_concepts
      := n_counted). The legend is the locked one with the count of c's RLM fails written from the data (the question
      rule is in methods_notes.md: a clause in the legend would take it over 350 words); a count of c too narrow for
      its segment is printed just right of the bar, as the locked plate prints a 0; fig5_data_state.json counts the
      Source Data cells that differ from the loose reading.

D200 (FF18 a, Am6, Am10; build spec findings/audits/figure_design_2026-11-01/spec/fig5.md section 4). The plate of
seven panels below amends D166's design: a to the judge's dot stacks and range whiskers, b as before, c the signal
ablation (old c goes to Supplementary Figure 12), d old d with its counts printed in the bars (Valerio's note of 2
November, which replaces FF18 a's choice of old e here; old e, the margin per draw, goes to Supplementary Figure 12), e
the evaluators against the judge (S540), f as before, g with range whiskers. The D166 plate stays the reproduce step:
_figure holds it to anchor_d166 first, and build_d200 is reached only afterwards.
  `figure` builds the D200 plate when d200_waits is empty: findings/recompute/fig5_d200_inputs exists and this run held
  the D166 plate to anchor_d166 (a `--from` pull with other rows does not). Otherwise it prints what it waits for and
  goes on to the plate of D166 and D186. D208 (2 Nov) replaced the heading rule with S564's Claimify-style selection, and
  D212 Q6 (3 Nov) asked for 5c and 5e on the re-run answers now, so the rule is no longer waited for (3 Nov): while
  no S564 reader exists and no test sets a rule, Papers waits inside the plate (papers_waits): S473.compute runs on L1's
  stored precision because it needs a value, blank_papers removes every Papers value before drawing, write_d200 refuses
  if one reaches a sheet (papers_left) or a printed number of b or g, and the Papers counts of the legend read
  [PENDING]. That plate is written only if its own checks pass; check 3 holds it to Figure 3 at
  commit 94262a0e (D201 Q2), so a Figure 3 rebuilt on the S6 rows does not refuse it, and adding --s6 still stops at the
  locked legend's refusal. A test sets a fixture rule in its own process and passes its own folder
  (scripts/S497_fig5_d200_test.py); the command line has no way to do either.
  The D200 data: the judge rows through judge_rows_v25 with the S6 rows of fig3_s6_inputs (F3); L3_d181; L1's final rows
  (S473.read_l1, its header's manifest equal to L3's, and the row counts of plan.csv L1); the claim filter
  (apply_claim_filter, on a copy); K1's final rows (S540.read_k1_final); S473.compute; S473.check_fig2 with at=None, the
  plate's current key v2.5 files.
  panel_data_d200 adds to panel_data: a's range whiskers and counts, ablation, S540's table of answers and 5e's rows.
  5c's rank rule is held to S06_metric_ablation.json's subset_table on S06's means (selftest).
  caption_d200 is the Source Data caption of this plate; caption_text stays with the plate of D166 until Q1 and the
  frozen set let `figure` stop writing that plate.
D295 (Valerio's "go", 7 November, manuscript thread 206c8013) reorders the D200 plate into six panels: a stays a; old c
(ranks) is b, old d (wins) is c, old f (faithfulness by verdict) is d, old g (Papers by faithfulness) is e, old e (the
evaluators) is f. Old b (draw-1 answers by the judge's verdict and Papers) moved to Supplementary Figure 12c: S543 draws
it with draw_verdict_papers and holds its sheet (VERDICT_COLS). The functions keep their old names (_draw_5c draws b,
and so on); build_d200 maps them. The D166 path above (build, texts, the locked legend) is unchanged.
D298 (Valerio's "O1", 7 November, manuscript thread ded27888: "move e to Supplementary Fig. 12 as panel d, and keep one
sentence here citing it. Figure 6 becomes a to e, with the evaluators as e."): the plate has five panels. Old e (Papers
by faithfulness) moved to Supplementary Figure 12d: S543 draws it with draw_papers_by_faithfulness and holds its sheet
(PAPERS_FAITH_COLS). Old f (the evaluators, _draw_5e) is e and takes band 3's full width.

THE STATISTICS are S473's (experiments/LIST.md Rules 2, 5, 7, 8, 10): a question's judge pass share is the share of
its three draws scoring 4 or more, a failed answer (no text) scoring 0; concept recall the mean of its draws; the W
questions are the answerable questions whose six draw-1 answers all have an L1 papers row (83 of 86 on 28 October).
Panel a's box: numpy linear percentiles (S457.summary); whiskers: the most extreme value within 1.5 x IQR of the box.
Panel b's median: statistics.median of the 495 answers' MiniCheck precision; an answer on it counts as high. Panel d:
a strictly higher three-draw mean wins, equal within 1e-9 ties. Panel e: per draw, wins, ties and losses of the
strategy's value against single pass's on the W questions where both exist. Panel f: faithfulness from S3's call
with passages (status ok only); pass is correctness 4 or more. Panel g: draw-1 answers with a scored faithfulness and a MiniCheck
precision, every L1 papers row (86 questions).
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import itertools
import json
import re
import shutil
import statistics
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S473 = _load("S473", ROOT / "scripts" / "S473_fig5_panels.py")
# D2 (Valerio, 8 Nov): figures are built from data only. The claims list (S473.claims_md) reads the main text and the
# Supplementary Information, so figure writes it only with `--claims-out DIR` (scripts/S616_figure_editorial.py claims),
# into DIR; without it no document is opened and the plate's folder and provenance hold no claims.md.
CLAIMS_OUT: "Path | None" = None


def write_claims(text: str) -> None:
    if CLAIMS_OUT is not None:
        CLAIMS_OUT.mkdir(parents=True, exist_ok=True)
        (CLAIMS_OUT / "claims.md").write_text(text)
S457, S463, FR = S473.S457, S473.S463, S473.FR
hs = _load("house_style", ROOT / "scripts" / "house_style.py")
# D301: the plates print a Greek rho; this makes the embedded font subset the same on every run (its docstring)
PFD = _load("pdf_font_determinism", ROOT / "scripts" / "pdf_font_determinism.py")
FN = _load("figure_names", ROOT / "scripts" / "figure_names.py")
MF = _load("minicheck_filter", ROOT / "scripts" / "minicheck_filter.py")
S540 = _load("S540", ROOT / "scripts" / "S540_fig5_evaluators.py")

SCRIPT = "scripts/S497_fig5_d166.py"
OUT = ROOT / "findings" / "figures_provisional" / "fig5"
FIG_N = FN.FIG_SIGNALS                          # D283 (6 November 2026): 5 until then; the folder stays fig5. The
#   D166 path and the locked plate it is held to (anchor_d166) keep the number 5 they were frozen with
SET, FIG2_SET = "fig5_1028", "fig2"
SET_DIR = f"{SET}_inputs"
K1_TAR, G1R15_TAR = S473.K1_TAR, S473.G1R15_TAR
ANCHOR = "anchor_d166"
ANCHOR_PNG = "Figure 5 (provisional, assembled 28 Oct).png"
SALT = "S497"                                   # svg.hashsalt (fig_repro: fixed SVG ids)
CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
LABEL = {c: S473.LABEL[c] for c in CONFIGS}
OTHERS = CONFIGS[1:]
SIGS = ("judge", "concept", "papers")
SIGNAME = {"judge": "Judge", "concept": "Concepts", "papers": "Papers"}
SIG_DRAWS = {"judge": (1, 2, 3), "concept": (1, 2, 3), "papers": (1,)}
PASS_T = S473.PASS_T
TIE = 1e-9
COLLECT_TZ = "Europe/Amsterdam"                 # the zone of the laptop where S473 pull runs s3_guard.py collect
# the repository inputs and tar members S473 pins (FROZEN_SHA256), all but its 23 October pull's files
PINS = {k: v for k, v in S473.FROZEN_SHA256.items() if not k.startswith("fig5_inputs/")}
L3_D181 = ROOT / "findings" / "recompute" / "L3_d181"                 # D186 (4): Figure 5's concept recall since D186
L3_D181_SHA256 = {"concept_recall.jsonl": "2ce0985ee014cf33f84417410282271b518c06a220138d2d6f67145c539e6371",
                  "header.json": "6a3fea6221df0142be83c1ec51e765bbac37dc10a63ca246385ad8994673fc9e"}   # 31 Oct (S471 --d181)
READINGS = {"loose": "L3's loose matcher (D12; findings/recompute/L3)",
            "D181": "D181's reading (S505's loose matcher with the question rule, Q-need, reading (b), key v2.5; "
                    "findings/recompute/L3_d181)"}
OWNED = ("Figure 5*", "Source Data Fig. 5*", "figure5_numbers.json", "figure5_provenance.json", "legend_draft.md",
         "claims.md", "fig5_data_state.json", "methods_notes.md")
SRC_NOTE = {"a": "S473.compute: panel a's per-question values (pass share at 4, concept recall mean, papers draw 1)",
            "b": "S473.compute: fn['b'], the draw-1 answers on the W questions",
            "c": "fn['b'] with the concept reading's found and concept counts (every concept; L3_d181's found and "
                 "n_counted since D186 (4))",
            "d": "per-question three-draw means on the W questions (judge, concept), draw 1 (papers)",
            "e": "per-draw margins against single pass on the W questions",
            "f": "S3's call with passages (faithfulness, status ok) by the plain call's correctness",
            "g": "S473.compute: fn['e']['points']"}
if CONFIGS != list(S473.CONFIGS):
    raise SystemExit("S473's strategy order is not D166's")


class Refused(SystemExit):
    pass


def sha256_file(p) -> str:
    return FR.sha256_file(p)


def jl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


# ---------------------------------------------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------------------------------------------
def check_inputs(sha: dict, tsv_sha: dict, committed: set) -> str:
    """Every input read is pinned: a committed frozen file by SHA256SUMS (names in committed, checked when read), a
    repository file or tar member by PINS, a file IDENTICAL_FILES.tsv names by its line. A pin not read, a sha256
    that differs, or an input pinned nowhere stops the run."""
    bad = [f"{k}: {sha[k][:12]}, pinned {v[:12]}" for k, v in PINS.items() if k in sha and sha[k] != v]
    bad += [f"{k}: {sha[k][:12]}, IDENTICAL_FILES.tsv {v[:12]}" for k, v in tsv_sha.items() if k in sha and sha[k] != v]
    bad += [f"{k}: pinned, not read" for k in PINS if k not in sha]
    bad += [f"{k}: read, pinned nowhere" for k in sha if k not in PINS and k not in tsv_sha and k not in committed]
    if bad:
        raise Refused(f"{len(bad)} frozen input(s) differ from their pins (D155), first: " + "; ".join(bad[:3])
                      + "; nothing written")
    n_com = sum(k in committed for k in sha)
    n_both = sum(k in sha and k in committed for k in PINS)
    n_pin = sum(k in sha and k not in committed for k in PINS)
    n_tsv = sum(k in sha and k not in PINS and k not in committed for k in tsv_sha)
    if n_com + n_pin + n_tsv != len(sha):          # each input counted once (review 28 Oct F2: 66 + 16 + 1 was 83)
        raise Refused(f"the input counts {n_com} + {n_pin} + {n_tsv} do not add to the {len(sha)} inputs read")
    return (f"{len(sha)} inputs: {n_com} committed frozen files equal to SHA256SUMS ({n_both} of them also equal "
            f"to S473's pin), {n_pin} more equal to S473's pins, {n_tsv} equal to {SET_DIR}/s3/IDENTICAL_FILES.tsv")


def collect_utc(when: str, pull_log: dict, zone: str = COLLECT_TZ) -> str:
    """The collect's time in UTC. s3_guard.py collect writes "at" in the local time of the machine that ran it, with
    no zone. S473 pull runs the collect on the laptop (COLLECT_TZ), so "at" is read in that zone, not in the zone of
    the machine running this script (review 28 Oct F1: under TZ=America/New_York the stamp printed 15:19:31Z, after
    the pull ended). The time must fall inside the pull's own window (PULL.json started_utc to ended_utc), which
    shows the zone is the right one; a pull collected in another zone stops the run."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    at = datetime.fromisoformat(when).replace(tzinfo=ZoneInfo(zone)).astimezone(timezone.utc)
    win = [datetime.fromisoformat(pull_log[k].replace("Z", "+00:00")) for k in ("started_utc", "ended_utc")]
    if not win[0] <= at <= win[1]:
        raise Refused(f"the collect's time {when} read in {zone} is {at:%Y-%m-%dT%H:%M:%SZ}, outside the pull's "
                      f"{pull_log['started_utc']} to {pull_log['ended_utc']}; nothing written")
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def frozen_sources(tmp: Path) -> dict:
    """The 28 October pull from its frozen parts (module docstring, FROZEN INPUTS); as S473.frozen_sources, with the
    set fig5_1028 for fig5 and the locked plate's anchor files."""
    sha, labels, committed = {}, [], set()

    def rec(name, p, frozen_file=False):
        if frozen_file:
            FR.check_committed(p)
            committed.add(name)
        sha[name] = FR.sha256_file(p)
        return p

    f5, f2 = FR.frozen(SET), FR.frozen(FIG2_SET)
    pull_json = rec(f"{SET_DIR}/PULL.json", FR.frozen(SET, "PULL.json"), True)
    side_f = rec(f"{SET_DIR}/s3/g1_collect.jsonl.json", FR.frozen(SET, "s3/g1_collect.jsonl.json"), True)
    tsv = rec(f"{SET_DIR}/s3/IDENTICAL_FILES.tsv", FR.frozen(SET, "s3/IDENTICAL_FILES.tsv"), True)
    l1 = FR.frozen(SET, "l1")
    for p in sorted(x for x in l1.rglob("*") if x.is_file()):
        rec(f"{SET_DIR}/{p.relative_to(f5).as_posix()}", p, True)
    anchor = {}
    for n in ("numbers.json", "figure5_numbers.json", "legend.md", ANCHOR_PNG):
        anchor[n] = rec(f"{SET_DIR}/{ANCHOR}/{n}", FR.frozen(SET, f"{ANCHOR}/{n}"), True)
    collect = rec("fig2_inputs/g1_collect.jsonl", FR.frozen(FIG2_SET, "g1_collect.jsonl"), True)
    outs = []
    for o in ("out", "out_g1r15"):
        outs.append(FR.frozen(FIG2_SET, o))
        for p in sorted(outs[-1].rglob("*")):
            if p.is_file():
                rec(f"fig2_inputs/{p.relative_to(f2).as_posix()}", p, True)
    g1r15 = FR.frozen(G1R15_TAR, G1R15_TAR)
    rec(f"{G1R15_TAR}.tar:{G1R15_TAR}/MANIFEST.sha256", g1r15 / "MANIFEST.sha256")
    for p in sorted((g1r15 / "runs").glob("*/answers.jsonl")):
        rec(f"{G1R15_TAR}.tar:{G1R15_TAR}/{p.relative_to(g1r15).as_posix()}", p)
    labels.append((g1r15 / "runs", f"{G1R15_TAR}.tar:{G1R15_TAR}/runs"))
    k1_runs = S473._k1_view(tmp, sha, labels)
    for p in S473.REPO_INPUTS:
        rec(p.relative_to(ROOT).as_posix(), p)
    tsv_sha = S473.identical_files(tsv)
    checked = check_inputs(sha, tsv_sha, committed)
    # the sidecar, its two input folders moved from the scratch pull's s3/ to fig2_inputs/ (S473 frozen_sources)
    side = json.loads(side_f.read_text())
    ins = (side.get("_provenance") or {}).get("inputs") or []
    old = str(Path(ins[0]).parent) if ins else ""
    if [Path(x).name for x in ins] != ["out", "out_g1r15"] or any(str(Path(x).parent) != old for x in ins):
        raise Refused(f"the frozen sidecar's inputs are {ins}, not one pull's s3/out and s3/out_g1r15")

    def move(p):
        if p != old and not p.startswith(old + "/"):
            raise Refused(f"the frozen sidecar names {p}, outside its pull's s3/ ({old})")
        return str(f2) + p[len(old):]
    moved = dict(side)
    moved["_provenance"] = {**side["_provenance"], "inputs": [move(x) for x in ins]}
    moved["from"] = {move(k): v for k, v in (side.get("from") or {}).items()}
    for k in moved["from"]:
        name = Path(k).relative_to(f2.parent).as_posix()
        if name not in sha or tsv_sha.get(name) != sha[name]:
            raise Refused(f"the sidecar takes rows from {name}, not a frozen file equal to the pull's")
    view = tmp / "s3"
    view.mkdir()
    (view / collect.name).symlink_to(collect)
    (view / side_f.name).write_text(json.dumps(moved, indent=1) + "\n")
    labels.append((view / collect.name, "fig2_inputs/g1_collect.jsonl"))
    return {"pull": pull_json, "collect": view / collect.name, "collect_name": "fig2_inputs/g1_collect.jsonl",
            "side": side, "l1": l1, "outs": outs, "ans_dirs": [k1_runs, g1r15 / "runs"], "sha": sha,
            "labels": labels, "checked": checked, "anchor": anchor, "anchor_applies": "frozen inputs"}


def pull_sources(src: Path, tmp: Path) -> dict:
    """A new pull's folder (S473 pull --to <dir>) through S473.pull_sources, with the locked plate's anchor from the
    frozen set; the anchor is compared only when the pull's L1 rows and collect are the frozen ones."""
    s = S473.pull_sources(src, tmp)
    s["outs"] = [src / "s3" / "out", src / "s3" / "out_g1r15"]
    s["anchor"] = {n: FR.check_committed(FR.frozen(SET, f"{ANCHOR}/{n}"))
                   for n in ("numbers.json", "figure5_numbers.json", "legend.md", ANCHOR_PNG)}
    for n, p in s["anchor"].items():
        s["sha"][f"{SET_DIR}/{ANCHOR}/{n}"] = FR.sha256_file(p)
    f5 = FR.frozen(SET, "l1")
    mine = {p.relative_to(src / "l1").as_posix(): FR.sha256_file(p) for p in sorted((src / "l1").rglob("*.jsonl"))}
    frozen = {p.relative_to(f5).as_posix(): FR.sha256_file(p) for p in sorted(f5.rglob("*.jsonl"))}
    same = mine == frozen and FR.sha256_file(s["collect"]) == PINS["fig2_inputs/g1_collect.jsonl"]
    s["anchor_applies"] = ("the pull's L1 rows and collect equal the frozen ones" if same else None)
    return s


# ---------------------------------------------------------------------------------------------------------------
# the data: S473's readers and compute(), then each panel's numbers
# ---------------------------------------------------------------------------------------------------------------
def jscore(row):
    """The judge's plain call (a) of a collect or out row, as the scratch recount.py read it: ok -> correctness, no
    answer -> 0 (Rule 10), any other status -> no value."""
    a = row.get("a") or {}
    st = a.get("status")
    if st == "ok":
        v = (a.get("scores") or {}).get("correctness")
        return v if isinstance(v, int) and not isinstance(v, bool) else None
    if st == "no_answer":
        return 0
    return None


def raw_judge(outs) -> dict:
    """The judge rows of the raw outs: each judge_passages.jsonl's latest line per answer, the second out (G1's 15
    reruns) replacing the first's rows of those answers (s3_guard.py collect)."""
    def ident(d):
        return (d["config"], d["question_id"], d["draw"])
    got = {}
    for o in outs:
        part = {}
        for f in sorted(glob.glob(str(Path(o) / "judge" / "*" / "judge_passages.jsonl"))):
            for d in jl(f):
                part[ident(d)] = d
        got.update(part)
    return got


def every_concept(r) -> bool:
    """Concept recall 1 by L3's counts (found_loose of n_concepts), as recount.py: the exact fraction where the row
    has n_concepts, else its concept_recall_loose to the nearest fraction with denominator at most 1,000."""
    if r.get("n_concepts"):
        return Fraction(r["found_loose"], r["n_concepts"]) == 1
    v = r.get("concept_recall_loose")
    return v is not None and Fraction(v).limit_denominator(1000) == 1


def tukey(vals, q25, q75):
    """Tukey's whisker ends: the most extreme values within 1.5 x IQR of the box."""
    iqr = q75 - q25
    lo = min(v for v in vals if v >= q25 - 1.5 * iqr - 1e-9)
    hi = max(v for v in vals if v <= q75 + 1.5 * iqr + 1e-9)
    return lo, hi


def read_l3_d181(groups, l3, folder: Path = L3_D181, pins: dict | None = None) -> dict:
    """D186 (4): L3_d181's rows in S473.read_l3's shape, for S473.compute. Refused unless: both files have the sha256
    pinned (L3_D181_SHA256); the header is S471's, plan row L3, reading D181, provisional false, key v2.5 (S512's
    KEY25_SHA256), the same answer copy as L3 (inputs manifest_sha256) and its counts the rows'; the rows are L3's
    answers one for one (config, question, draw, group, status, answer sha256); and on the questions whose
    expected_concepts v2.5 left unchanged (S512.keys) each row's D12 loose base (concept_recall_loose_base,
    found_loose_base, n_concepts) equals L3's loose value, so the answers scored are the ones L3 scored. Each row
    enters compute with concept_recall_loose := concept_recall, found_loose := found, n_concepts := n_counted."""
    pins = L3_D181_SHA256 if pins is None else pins
    files = {n: Path(folder) / n for n in ("concept_recall.jsonl", "header.json")}
    for n, f in files.items():
        if sha256_file(f) != pins[n]:
            raise Refused(f"{f.name} of {Path(folder).name} is {sha256_file(f)[:12]}, not the {pins[n][:12]} S497 pins "
                          f"(D186 (4)); nothing written")
    hdr = json.loads(files["header.json"].read_text())
    S512 = S463.JR.S512
    want = {"script": "scripts/S471_l3_concept_recall.py", "plan_row": "L3", "reading": "D181", "provisional": False}
    got_h = {k: hdr.get(k) for k in want}
    if got_h != want or (hdr.get("key") or {}).get("sha256") != S512.KEY25_SHA256 or \
            (hdr.get("inputs") or {}).get("manifest_sha256") != l3["header"]["inputs"]["manifest_sha256"]:
        raise Refused(f"{Path(folder).name}/header.json is not S471's final D181 reading of L3's answers on key v2.5 "
                      f"({got_h}); nothing written")
    rows = S473.read_jsonl(files["concept_recall.jsonl"])
    cnt = hdr["counts"]
    got = {"rows": len(rows), "scored": sum(1 for r in rows if r.get("group") != "not_answerable"),
           "status_scored": dict(Counter(r["status"] for r in rows if r.get("group") != "not_answerable")),
           "by_group": dict(Counter(r["group"] for r in rows))}
    if got != {k: cnt[k] for k in got}:
        raise Refused(f"{Path(folder).name}: the rows give {got}, the header {({k: cnt[k] for k in got})}")
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}
    out, held, bad = {}, 0, []
    for r in rows:
        k = (r["config"], r["question_id"], r["draw"])
        a = l3["rows"].get(k)
        if k in out or a is None or any(r.get(f) != a.get(f) for f in ("group", "status", "answer_sha256")):
            bad.append(f"{k}: not L3's answer one for one")
            continue
        if r["group"] != "not_answerable" and r["question_id"] in same_c:
            if (r.get("concept_recall_loose_base"), r.get("found_loose_base"), r.get("n_concepts")) != \
                    (a.get("concept_recall_loose"), a.get("found_loose"), a.get("n_concepts")):
                bad.append(f"{k}: the loose base on unchanged concepts is not L3's loose value")
                continue
            held += 1
        out[k] = dict(r, concept_recall_loose=r["concept_recall"], found_loose=r["found"], n_concepts=r["n_counted"])
    if bad or set(out) != set(l3["rows"]):
        raise Refused(f"{Path(folder).name}: {len(bad)} rows refused (first: {bad[:1]}), {len(set(l3['rows']) - set(out))} "
                      f"of L3's answers missing; nothing written")
    nq = len({q for (_, q, _) in out if q in same_c and groups.get(q) != "not_answerable"})
    return {"rows": out, "header": l3["header"], "header_d181": hdr,
            "reproduced": (f"L3_d181 (D186 (4)): both files at their pinned sha256, the header S471's final D181 "
                           f"reading on key v2.5 of L3's answer copy, its {len(out):,} rows L3's answers one for one, and "
                           f"on the {nq} questions whose concepts v2.5 left unchanged the loose base of {held:,} rows "
                           f"equal to L3's loose value")}


def faith_of(rows) -> dict:
    """Panel f's (status, faithfulness, error) per answer from the judge's call with passages (b), the later row of an
    answer winning."""
    out = {}
    for x in rows:
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        out[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    return out


def read_and_compute(srcs) -> dict:
    """S473's reading and compute() as S473 _figure runs them (and as build_fig5.py did), with the reproduce checks
    1 and 2 of the module docstring, on the key v2.4 collect alone: the locked plate is reproduced from this result,
    and only then does with_judge_rows put the key v2.5 rows in (D186 (3))."""
    import numpy as np
    import lock_equiv                                       # D204: d66daa28 but for the second judge's machines
    if not lock_equiv.accepts(S463.LOCK_TOML):
        raise Refused("experiments/LOCK.toml is not D88's d66daa28: the judge rows are checked against it")
    rep = S473.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups)
    rep.append(l3["reproduced"])
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    txt = S473.answer_text_sha(srcs["ans_dirs"])
    diff = sorted(k for (c, q, d), r in l3["rows"].items()
                  for k in [f"{S473.INDEX}|{c}|{q}|d{d}"] if txt.get(k) != r.get("answer_sha256"))
    if diff:
        raise Refused(f"{len(diff)} answers judged by S3 differ from the texts L3 and L1 scored, first {diff[0]}")
    rep.append(f"S3's judged answers (K1's copy with G1R15's reruns over it) equal the texts L1 and L3 scored "
               f"(answer sha256, all {len(l3['rows']):,})")
    col_rows = S473.read_jsonl(srcs["collect"])
    faith_rows = faith_of(col_rows)
    # 2: the raw outs give the collect's correctness for every answer (recount.py's cross-check)
    col = {(x["config"], x["question_id"], x["draw"]): x for x in col_rows}
    raw = raw_judge(srcs["outs"])
    mism = sorted(k for k in set(col) | set(raw) if (k in col) != (k in raw) or (k in col and jscore(col[k]) != jscore(raw[k])))
    if mism:
        raise Refused(f"{len(mism)} answers' judge correctness differs between the raw outs and the collect, first "
                      f"{mism[0]}; nothing written")
    rep.append(f"the judge's correctness read again from the raw outs (out/, out_g1r15/ over it) equals the "
               f"collect's for all {len(col):,} rows")
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    return {"rep": rep, "groups": groups, "read": read, "l3": l3, "l1": l1, "faith_rows": faith_rows, "fn": fn,
            "ans_inputs": ans_inputs, "raw": raw, "np": np, "answers": answers, "col_rows": col_rows}


def with_judge_rows(R: dict, srcs: dict, judge_rows=None) -> dict:
    """D186 (3): R's cells read through scripts/judge_rows_v25.py (S463.judge_rows, as Figure 2) on a copy of R's
    read, so R itself stays the key v2.4 result the locked plate was reproduced from. An answer's key v2.5 row (S6,
    under srcs["s6"], else beside the outs the collect read) where one exists, else its key v2.4 row. A v2.5 row chosen
    replaces the v2.4 row in the cells (S463.judge_rows), in the call with passages panel f reads, and in the raw rows
    panel b is held to. Returns a new R (fn not yet computed again: the caller computes it on the concept reading it
    draws). judge_rows: S463.judge_rows, or a stand-in for the selftest."""
    import copy
    judge_rows = judge_rows or S463.judge_rows
    read = copy.deepcopy(R["read"])
    jr = judge_rows(read, srcs["collect"], R["groups"], S463.rerun_keys(), list(S473.DRAWS), srcs.get("s6"),
                    R["answers"])
    v25 = {(k[1], k[2], k[3]): v["row"] for k, v in jr["choice"].items() if k != "_sources" and v["status"] == "v2.5"}
    faith_rows = faith_of([*R["col_rows"], *v25.values()])   # a v2.5 row chosen replaces its answer's v2.4 row
    return {**R, "read": read, "faith_rows": faith_rows, "raw": {**R["raw"], **v25},
            "rep": [*R["rep"], f"judge rows (D186 (3), judge_rows_v25): {jr['status']}"],
            "judge_rows": S463.judge_rows_record(jr), "v25_rows": len(v25)}


def panel_data(R) -> dict:
    """Each panel's numbers from compute()'s output, as the scratch builds computed them (anchor_d166/code/)."""
    import numpy as np
    fn, read, l3, l1, groups, faith_rows = R["fn"], R["read"], R["l3"], R["l1"], R["groups"], R["faith_rows"]
    cells = read["cells"]
    qa, cc = fn["qa"], fn["c"]
    qw = cc["questions"]
    # ---- a (fig5_a/prep.py): per question the pass share at PASS_T (compute's a), the concept mean, papers draw 1
    conc = {(c, q, d): (r["concept_recall_loose"] if r["status"] in ("ok", "no_answer", "error") else None)
            for (c, q, d), r in l3["rows"].items() if groups[q] == "answerable"}
    papers1 = {(c, q, d): (r.get("signals") or {}).get("precision")
               for (c, q, d), r in l1["stages"]["papers"].items() if groups[q] == "answerable"}
    per_q = {}
    for c in CONFIGS:
        pass_q = dict(fn["a"][c]["pass"]["per_q"])
        pq = {}
        for q in qa:
            cv = [conc[(c, q, d)] for d in S473.DRAWS if conc.get((c, q, d)) is not None]
            pq[q] = {"pass": pass_q.get(q), "concept": (sum(cv) / len(cv)) if cv else None,
                     "papers": papers1.get((c, q, 1))}
        per_q[c] = pq
    a_specs = [("pass", qa, (0, 100), [0, 50, 100], "Judge pass rate (%)", "Judge", "3 draws"),
               ("concept", qa, (0, 1), [0, 0.5, 1], "Concept recall", "Concepts", "3 draws"),
               ("papers", qw, (0, 1), [0, 0.5, 1], "Papers precision", "Papers", "draw 1")]
    A = {}
    for col, qs, *_ in a_specs:
        rows = {c: [(q, per_q[c][q][col]) for q in qs if per_q[c][q][col] is not None] for c in CONFIGS}
        A[col] = {"rows": rows, "summary": {c: S457.summary([v for _, v in rows[c]]) for c in CONFIGS},
                  "n": len({q for c in CONFIGS for q, _ in rows[c]})}
    # ---- b (fig5_bc2/b6): fn['b'], each answer read again from the raw collect and L1 rows
    pts_b = fn["b"]
    if any(p["draw"] != 1 or p["judge_pass"] != int(p["judge_correctness"] >= PASS_T) for p in pts_b):
        raise Refused("b: an answer of compute's panel b rows is not draw 1 or its pass is not correctness >= PASS_T")
    jraw = {k: jscore(r) for k, r in R["raw"].items()}
    praw = {}
    for f_ in sorted(Path(R["l1_dir"]).glob("papers/*.jsonl")):
        for r in jl(f_):
            praw[(r["config"], r["question_id"], r["draw"])] = (r.get("signals") or {}).get("precision")
    mism = [(p["strategy"], p["question_id"]) for p in pts_b
            if jraw.get((p["strategy"], p["question_id"], 1)) != p["judge_correctness"]
            or praw.get((p["strategy"], p["question_id"], 1)) is None
            or abs(praw[(p["strategy"], p["question_id"], 1)] - p["papers_precision"]) > 1e-9]
    if mism:
        raise Refused(f"b: {len(mism)} answers differ from the raw judge and L1 rows: {mism[:3]}")
    b_median = statistics.median(p["papers_precision"] for p in pts_b)
    b_on = sum(p["papers_precision"] == b_median for p in pts_b)

    def b_split(rows, m):
        hi = [p["papers_precision"] >= m for p in rows]
        ps = [bool(p["judge_pass"]) for p in rows]
        return [sum((not j) and h for j, h in zip(ps, hi)), sum(j and h for j, h in zip(ps, hi)),
                sum((not j) and (not h) for j, h in zip(ps, hi)), sum(j and (not h) for j, h in zip(ps, hi)),
                len(rows)]
    B = {c: b_split([p for p in pts_b if p["strategy"] == c], b_median) for c in CONFIGS}
    # ---- c (fig5_bc3/b8/recount.py): the same answers, every key concept by L3's counts, the judge's verdict;
    # the answer set derived again from the raw rows (W questions, draw 1, all three values present) must be b's
    qw_raw = [q for q in qa if all((c, q, 1) in praw for c in CONFIGS)]
    if qw_raw != qw:
        raise Refused("c: the W questions from the raw L1 rows differ from compute's")
    keys_c = []
    for q in qw:
        for c in CONFIGS:
            k = (c, q, 1)
            r3 = l3["rows"].get(k)
            cv_ok = r3 is not None and r3["status"] in ("ok", "no_answer", "error") and (
                r3.get("n_concepts") or r3.get("concept_recall_loose") is not None)
            if praw.get(k) is not None and cv_ok and jraw.get(k) is not None:
                keys_c.append((c, q))
    if sorted(keys_c) != sorted((p["strategy"], p["question_id"]) for p in pts_b):
        raise Refused("c: the answers with all three values from the raw rows are not panel b's answers")
    pts_c = [{"strategy": p["strategy"], "question_id": p["question_id"], "judge": p["judge_correctness"],
              "pass": bool(p["judge_pass"]), "all": every_concept(l3["rows"][(p["strategy"], p["question_id"], 1)])}
             for p in pts_b]
    C = {c: {"pass": sum(1 for p in pts_c if p["strategy"] == c and p["all"] and p["pass"]),
             "fail": sum(1 for p in pts_c if p["strategy"] == c and p["all"] and not p["pass"])} for c in CONFIGS}
    C_TOT = {c: {"n": sum(1 for p in pts_c if p["strategy"] == c),
                 "fail": sum(1 for p in pts_c if p["strategy"] == c and not p["pass"])} for c in CONFIGS}
    # ---- d (fig5_bc2/c5/prep_c5.py): per W question the three-draw means (judge: failed 0), papers draw 1
    judge = {(c, q, d): (cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None)
             for (c, q, d), cell in cells.items() if groups[q] == "answerable"}
    sig = {"judge": judge, "concept": conc, "papers": papers1}

    def qmean(s, c, q, draws):
        v = [sig[s][(c, q, d)] for d in draws if (c, q, d) in sig[s] and sig[s][(c, q, d)] is not None]
        return float(np.mean(v)) if v else None
    V = {s: np.array([[np.nan if qmean(s, c, q, SIG_DRAWS[s]) is None else qmean(s, c, q, SIG_DRAWS[s])
                       for c in CONFIGS] for q in qw]) for s in SIGS}
    for s in SIGS:
        for i, c in enumerate(CONFIGS):
            if abs(np.nanmean(V[s][:, i]) - cc["means"][s][c]) >= 1e-12:
                raise Refused(f"d: the per-question means of {s} for {c} do not give compute's configuration mean")
    D = {}
    for o in OTHERS:
        for s in SIGS:
            x, y = V[s][:, 0], V[s][:, CONFIGS.index(o)]
            ok = ~(np.isnan(x) | np.isnan(y))
            dd = x[ok] - y[ok]
            D[(o, s)] = {"sp": int((dd > TIE).sum()), "tie": int((np.abs(dd) <= TIE).sum()),
                         "ot": int((dd < -TIE).sum()), "n": int(ok.sum())}
    # ---- e (fig5_bc3/c8sep/build_c3_8.py): per draw, the strategy against single pass on the W questions
    def margin(s, c, r, d):
        w = t = lo = 0
        for q in qw:
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
    e_drawn = []
    for c, r in itertools.combinations(CONFIGS, 2):
        if c != "single_pass":
            continue
        for s in SIGS:
            for d in SIG_DRAWS[s]:
                e_drawn.append({"strategy": r, "reference": c, "signal": s, "draw": d, **margin(s, r, c, d)})
    # ---- f (fig5_d/d_data.py): per answer the faithfulness call's status and score and the plain call's correctness
    rows_f = []
    for c in CONFIGS:
        for q in qa:
            for d in S473.DRAWS:
                st, v, _ = faith_rows.get((c, q, d), (None, None, None))
                cell = cells[(c, q, d)]
                corr = cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None
                rows_f.append({"strategy": c, "question_id": q, "faith_status": st, "faithfulness": v,
                               "correctness": corr})
    f_ok = [r for r in rows_f if r["faith_status"] == "ok"]
    if any(r["correctness"] is None for r in f_ok):
        raise Refused("f: an answer with a faithfulness score has no correctness (an unscored plain call)")
    F = {}
    for c in CONFIGS:
        for word, test in (("pass", lambda v: v >= PASS_T), ("fail", lambda v: v < PASS_T)):
            rs = [r for r in f_ok if r["strategy"] == c and test(r["correctness"])]
            cn = Counter(r["faithfulness"] for r in rs)
            F[(c, word)] = {"counts": [cn.get(k, 0) for k in range(6)], "n": len(rs)}
        if F[(c, "pass")]["n"] + F[(c, "fail")]["n"] != fn["d"][c]["n"]:
            raise Refused(f"f {c}: pass and fail do not add to compute's faithfulness n")
    f_nq = len({r["question_id"] for r in f_ok})
    f_out = {}
    for c in CONFIGS:
        cn = Counter(r["faith_status"] for r in rows_f if r["strategy"] == c and r["faith_status"] != "ok")
        f_out[c] = {"no_answer": cn.get("no_answer", 0), "error": cn.get("error", 0)}
        if sum(f_out[c].values()) != sum(cn.values()):
            raise Refused(f"f {c}: a faithfulness status other than ok, no_answer or error: {dict(cn)}")
        if F[(c, "pass")]["n"] + F[(c, "fail")]["n"] + sum(f_out[c].values()) != f_nq * 3:
            raise Refused(f"f {c}: the answers do not add to {f_nq} questions x 3 draws")
    # ---- g (fig5_e/prep.py, draw_e.py e4): fn['e']['points'] by faithfulness 5 and below
    pts_g = fn["e"]["points"]

    def quart(v):
        r_ = lambda x: round(float(x), 4)  # noqa: E731
        return {"n": len(v), "q25": r_(np.percentile(v, 25)), "median": r_(np.median(v)),
                "q75": r_(np.percentile(v, 75)), "min": r_(min(v)), "max": r_(max(v))}
    G = []
    for c in CONFIGS:
        for grp in ("5", "0 to 4"):
            pts = sorted([p for p in pts_g if p["strategy"] == c
                          and ((p["faithfulness"] == 5) if grp == "5" else (p["faithfulness"] < 5))],
                         key=lambda p: (p["papers_precision"], p["question_id"]))
            v = [p["papers_precision"] for p in pts]
            G.append({"strategy": c, "grp": grp, "values": v, "qids": [p["question_id"] for p in pts], "q": quart(v),
                      "q_exact": {"q25": float(np.percentile(v, 25)), "median": float(np.median(v)),
                                  "q75": float(np.percentile(v, 75))}})
    return {"qa": qa, "qw": qw, "a_specs": a_specs, "A": A, "pts_b": pts_b, "B": B, "b_median": b_median,
            "b_on": b_on, "pts_c": pts_c, "C": C, "C_TOT": C_TOT, "D": D, "E_DRAWN": e_drawn, "cc": cc, "F": F,
            "f_nq": f_nq, "f_out": f_out, "rows_f": rows_f, "G": G, "G_N": len(pts_g),
            "G_NQ": fn["e"]["rho_all"]["questions"]}


# ---------------------------------------------------------------------------------------------------------------
# the locked plate's numbers (anchor_d166): reproduced before drawing and again before writing
# ---------------------------------------------------------------------------------------------------------------
B_KEYS = ["judge_fails_papers_high", "both_high", "both_low", "judge_passes_papers_low", "n"]


def strip(x, drop=("source",)):
    """A parsed json value without the keys in drop, at any depth (the anchor's source paths name scratch files)."""
    if isinstance(x, dict):
        return {k: strip(v, drop) for k, v in x.items() if k not in drop}
    if isinstance(x, list):
        return [strip(v, drop) for v in x]
    return x


def jnorm(x):
    """As json would store x (tuples as lists, numpy scalars as floats)."""
    return json.loads(json.dumps(x, default=float))


def first_diff(a, b, path="") -> str | None:
    """The first key path where two parsed json values differ (floats compared exactly), or None."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                return f"{path}/{k}: only in {'the build' if k in a else 'the locked plate'}"
            d = first_diff(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: {len(a)} items, the locked plate {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, bool) or isinstance(b, bool) or not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        return None if a == b else f"{path}: {a!r}, the locked plate {b!r}"
    return None if float(a) == float(b) else f"{path}: {a!r}, the locked plate {b!r}"


def data_view(P) -> dict:
    """The panel numbers computed before drawing, in the shape of the locked plate's numbers.json "panels" (the
    parts that do not depend on the drawing: dot overlaps, label places and mark offsets are compared after it)."""
    a = {}
    for col, *_ in P["a_specs"]:
        a[col] = {"n_questions": P["A"][col]["n"], "per_strategy": {}}
        for c in CONFIGS:
            sm = P["A"][col]["summary"][c]
            vals = [v for _, v in P["A"][col]["rows"][c]]
            wlo, whi = tukey(vals, sm["quartile_25"], sm["quartile_75"])
            a[col]["per_strategy"][LABEL[c]] = {
                "summary": {"questions_n": len(vals), "median": sm["median"], "quartile_25": sm["quartile_25"],
                            "quartile_75": sm["quartile_75"], "whisker_low": wlo, "whisker_high": whi},
                "per_question": P["A"][col]["rows"][c]}
    out = {"a": {"columns": a},
           "b": {"papers_median_pooled": P["b_median"], "answers_on_median": P["b_on"],
                 "counts": {LABEL[c]: dict(zip(B_KEYS, P["B"][c])) for c in CONFIGS}},
           "c": {"every_concept": {LABEL[c]: P["C"][c] for c in CONFIGS},
                 "strategy_totals": {LABEL[c]: P["C_TOT"][c] for c in CONFIGS}},
           "d": {"drawn": {SIGNAME[s]: {LABEL[o]: {"single_pass_higher": P["D"][(o, s)]["sp"],
                                                   "tie": P["D"][(o, s)]["tie"],
                                                   "other_higher": P["D"][(o, s)]["ot"], "n": P["D"][(o, s)]["n"]}
                                        for o in OTHERS} for s in SIGS}},
           "e": {"marks": sorted([{"row": LABEL[x["strategy"]], "signal": x["signal"], "draw": x["draw"],
                                   **{k: x[k] for k in ("margin_pct", "wins", "ties", "losses", "n")}}
                                  for x in P["E_DRAWN"]], key=lambda m: (m["row"], m["signal"], m["draw"])),
                 "kendall_W": P["cc"]["W"], "kendall_W_exact_P": P["cc"]["P"]},
           "f": {"per_strategy": {LABEL[c]: {w: {"n": P["F"][(c, w)]["n"], "counts_faith_0_to_5": P["F"][(c, w)]["counts"],
                                                 "share_pct_0_to_5": [100 * x / P["F"][(c, w)]["n"]
                                                                      for x in P["F"][(c, w)]["counts"]]}
                                             for w in ("pass", "fail")} for c in CONFIGS}},
           "g": {"n_answers": P["G_N"], "n_questions": P["G_NQ"],
                 "rows": [{"strategy": LABEL[g["strategy"]], "faithfulness": g["grp"], **g["q"], "values": g["values"]}
                          for g in P["G"]]}}
    return jnorm(out)


def anchor_view(panels) -> dict:
    """The locked plate's numbers.json "panels" in data_view's shape."""
    p = strip(panels)
    a = {col: {"n_questions": v["n_questions"],
               "per_strategy": {s: {"summary": x["summary"], "per_question": x["per_question"]}
                                for s, x in v["per_strategy"].items()}} for col, v in p["a"]["columns"].items()}
    return {"a": {"columns": a},
            "b": {k: p["b"][k] for k in ("papers_median_pooled", "answers_on_median", "counts")},
            "c": p["c"], "d": p["d"],
            "e": {"marks": sorted([{k: m[k] for k in ("row", "signal", "draw", "margin_pct", "wins", "ties", "losses", "n")}
                                   for m in p["e"]["marks"]], key=lambda m: (m["row"], m["signal"], m["draw"])),
                  "kendall_W": p["e"]["kendall_W"], "kendall_W_exact_P": p["e"]["kendall_W_exact_P"]},
            "f": p["f"],
            "g": {"n_answers": p["g"]["n_answers"], "n_questions": p["g"]["n_questions"],
                  "rows": [{k: v for k, v in r.items() if k != "dots_overlapping"} for r in p["g"]["rows"]]}}


def compare_anchor_data(P, anchor_numbers) -> str:
    mine, theirs = data_view(P), anchor_view(anchor_numbers["panels"])
    bad = [f"{L}: {d}" for L in "abcdefg" for d in [first_diff(mine[L], theirs[L], L)] if d]
    if bad:
        raise Refused(f"the numbers of {len(bad)} panel(s) differ from the locked plate's (D166, "
                      f"{SET_DIR}/{ANCHOR}/numbers.json), first: " + "; ".join(bad[:3]) + "; nothing written")
    n = sum(len(json.dumps(mine[L])) for L in mine)
    return (f"every panel's numbers (a to g: {len(mine['e']['marks'])} margins, {len(mine['g']['rows'])} g rows, "
            f"{sum(len(x['per_question']) for v in mine['a']['columns'].values() for x in v['per_strategy'].values())}"
            f" a values) equal the locked plate's numbers.json before drawing ({n:,} characters of json compared)")


def compare_anchor_drawn(drawn, sheets, printed, legend, anchor_numbers, anchor_f5) -> str:
    """After drawing: every drawn number (but the source paths), the sheets, the printed map and the legend."""
    bad = []
    d = first_diff(jnorm(strip(drawn)), strip(anchor_numbers["panels"]), "panels")
    if d:
        bad.append(d)
    d = first_diff(jnorm(sheets), anchor_f5["sheets"], "sheets")
    if d:
        bad.append(d)
    d = first_diff(jnorm(printed), anchor_f5["printed"], "printed")
    if d:
        bad.append(d)
    if legend != anchor_numbers.get("_legend"):
        bad.append("the legend differs from the locked plate's legend.md")
    if bad:
        raise Refused("the drawn plate differs from the locked plate (D166): " + "; ".join(bad[:3]) + "; nothing "
                      "written")
    return (f"every drawn number, the {len(sheets)} Source Data sheets "
            f"({sum(len(s['rows']) for s in sheets.values()):,} rows), the {len(printed)} printed numbers' map and the "
            f"legend equal the locked plate's (numbers.json, figure5_numbers.json, legend.md)")


def png_equal(a: Path, b: Path) -> str:
    """The two PNGs pixel for pixel (MuPDF's decoding): same size, every sample equal."""
    import fitz
    pa, pb = fitz.Pixmap(str(a)), fitz.Pixmap(str(b))
    if (pa.width, pa.height, pa.n) != (pb.width, pb.height, pb.n):
        raise Refused(f"the plate's PNG is {pa.width} x {pa.height} ({pa.n} channels), the locked plate's "
                      f"{pb.width} x {pb.height} ({pb.n}); nothing written")
    sa, sb = pa.samples, pb.samples
    if sa != sb:
        nd = sum(1 for i in range(0, len(sa), pa.n) if sa[i:i + pa.n] != sb[i:i + pa.n])
        raise Refused(f"the plate's PNG differs from the locked plate's in {nd:,} of {pa.width * pa.height:,} pixels; "
                      f"nothing written")
    return f"the PNG equals the locked plate's pixel for pixel ({pa.width} x {pa.height}, {pa.width * pa.height:,} pixels)"


# ---------------------------------------------------------------------------------------------------------------
# the plate: build_fig5.py's layout and drawing (anchor_d166/build_fig5.py, from its "layout" section to the end of
# panel g), unchanged but for the names its data step gave and the source notes; D166 locks this design
# ---------------------------------------------------------------------------------------------------------------
def cividis6():
    import matplotlib
    cm = matplotlib.colormaps[S457.FLOCK["colour"]["continuous"]]
    return ["#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(round(255 * i / 5)))[:3]) for i in range(6)]


def build(dat, g_whiskers: bool = False, a_range: bool = False) -> dict:
    """Draw the locked plate in memory (layout A: band 1 a | b | c, band 2 d | e, band 3 f | g) from panel_data's
    numbers; finish_plate saves it later. g_whiskers (Valerio, 2 Nov: "we always make boxplots using whiskers"): g's
    boxes get whiskers to the smallest and largest value with caps (hs.box_stats, whis range), and sheet Fig. 5g their
    ends; off for the locked plate's reproduction, which drew none. a_range (Valerio, 2 Nov evening, "Q3: yes"): a's
    whiskers run to the smallest and largest question value instead of Tukey's 1.5 x IQR; off for the reproduction,
    which drew Tukey's. Returns the drawing's names: the Plate (PL), every drawn number (DRAWN),
    the Source Data sheets (SHEET), the collapsed boxes, the unprinted counts, panel e's closest marks, the layout."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np  # noqa: F401
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath

    S457.figure_lock_agreed()
    plt.rcParams.update(S457.plate_rc(SALT))
    plt.rcParams["axes.unicode_minus"] = False
    PT, MM_PT = S457.PT, S457.MM_PT
    W = S457.FIG_W_MM
    H_MAX = S457.FIG_H_MAX_MM
    if (W, H_MAX) != (183.0, 170.0):
        raise Refused(f"FIGURE_LOCK's page is {W} x {H_MAX} mm, not the 183 x 170 mm the locked layout is built for")
    OK = S457.OKABE
    SIG_COL = {"judge": OK["blue"], "concept": OK["orange"], "papers": OK["black"]}
    SIG_MK = {"judge": "o", "concept": "s", "papers": "D"}
    SIG_MS = {"o": 1.0, "s": 0.9, "D": 0.85}            # equal visual weight (square and diamond look larger)
    GREY = S457.DOT_GREY
    WHITE, BLACK = "#FFFFFF", "#000000"
    B_COLS = [OK["sky blue"], "#BBBBBB", "#888888", OK["reddish purple"]]
    C_PASS, C_FAIL = "#BBBBBB", OK["sky blue"]
    D_COLS = {"sp": OK["reddish purple"], "tie": "#BBBBBB", "ot": OK["bluish green"]}
    SEP_GREY = "#949494"
    T2P, FP = TextToPath(), FontProperties(family=S457.FONT, size=PT)

    def tw(s):
        return T2P.get_text_width_height_descent(s, FP, ismath=False)[0] * MM_PT

    A_SPECS = [(col, None, qs, lim, ticks, xl, ref, dr, None) for col, qs, lim, ticks, xl, ref, dr in dat["a_specs"]]
    A, B, B_MEDIAN, B_ON_MEDIAN = dat["A"], dat["B"], dat["b_median"], dat["b_on"]
    C, C_TOT, D, E_DRAWN, cc = dat["C"], dat["C_TOT"], dat["D"], dat["E_DRAWN"], dat["cc"]
    F, G, G_N, G_NQ = dat["F"], dat["G"], dat["G_N"], dat["G_NQ"]
    COLS6 = cividis6()

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
        raise Refused(f"layout A is {H} mm high, over {H_MAX}")


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
                wlo, whi = ((min(vals), max(vals)) if a_range
                            else tukey(vals, sm["quartile_25"], sm["quartile_75"]))
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
    DRAWN["a"] = {"source": SRC_NOTE["a"], "columns": {}}
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
    DRAWN["b"] = {"source": SRC_NOTE["b"], "papers_median_pooled": B_MEDIAN, "answers_on_median": B_ON_MEDIAN,
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
                raise Refused(f"b {c} segment {k_ + 1} ({v}) too narrow for its count")
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
    DRAWN["c"] = {"source": SRC_NOTE["c"], "every_concept": {}, "strategy_totals": {}}
    for i, c in enumerate(CONFIGS):
        yc = row_c1(i)
        p_, f_ = C[c]["pass"], C[c]["fail"]
        SHEET["c"]["rows"].append([LABEL[c], p_, f_, p_ + f_])
        axc.barh(yc, p_, height=BAR1, color=C_PASS, lw=0, zorder=2)
        axc.barh(yc, f_, left=p_, height=BAR1, color=C_FAIL, lw=0, zorder=2)
        P(C_X0 + p_ / 2 * MMC, yc, str(p_), printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_pass}"},
          ha="center", va="center_baseline")
        if f_ and f_ * MMC >= tw(str(f_)) + 0.6:
            P(C_X0 + (p_ + f_ / 2) * MMC, yc, str(f_),
              printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_fail}"}, ha="center",
              va="center_baseline")
        else:
            # a 0, or (D186 (4)) a count too narrow for its segment: just right of the bar, as the locked plate's 0
            assert C_X0 + (p_ + f_) * MMC + 0.6 + tw(str(f_)) <= C_X0 + C_W, (c, p_, f_)
            P(C_X0 + (p_ + f_) * MMC + 0.6, yc, str(f_),
              printed={"sheet": "Fig. 5c", "row": i, "format": "{every_concept_judge_fail}"},
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
    DRAWN["d"] = {"source": SRC_NOTE["d"], "drawn": {}}
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
    DRAWN["e"] = {"source": SRC_NOTE["e"], "marks": [],
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
    DRAWN["f"] = {"source": SRC_NOTE["f"], "per_strategy": {}}
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
                             "median", "quartile_75"] + (["whisker_low", "whisker_high"] if g_whiskers else [])
    PL.letter(G_LET, B3L, "g")
    P(G_NX, B3L, "(n)")
    P(G_SUBR, B3L, "Faithfulness", ha="right")     # 28 Oct review: one heading over the sub-rows
    G_W = G_X1 - G_X0
    axg = PL.axes(G_X0, R3, G_W, R3B - R3, (-0.04, 1.04))
    axg.set_xticks([0, 0.5, 1])
    axg.set_xticklabels(["0", "0.5", "1"])
    axg.set_xlabel("Papers precision", labelpad=2)
    mm_x = G_W / 1.08
    DRAWN["g"] = {"source": SRC_NOTE["g"], "n_answers": G_N, "n_questions": G_NQ, "rows": []}
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
        wk = []
        if g_whiskers:                              # 2 Nov: whiskers to the range, caps 5/12 of the box (house_style)
            wlo, whi = min(v), max(v)
            cap = hs.CAP_FRAC * hb
            for a_, b_ in ((wlo, qe["q25"]), (qe["q75"], whi)):
                if b_ > a_:
                    axg.plot([a_, b_], [yc, yc], color=BLACK, lw=0.5, solid_capstyle="butt", zorder=5)
            for x_ in (wlo, whi):
                axg.plot([x_, x_], [yc - cap, yc + cap], color=BLACK, lw=0.5, solid_capstyle="butt", zorder=5)
            wk = [wlo, whi]
        row_i = len(SHEET["g"]["rows"])
        SHEET["g"]["rows"].append([LABEL[g["strategy"]], g["grp"], "summary", None, None, len(v), qe["q25"],
                                   qe["median"], qe["q75"]] + wk)
        for q, x in zip(g["qids"], v):
            SHEET["g"]["rows"].append([LABEL[g["strategy"]], g["grp"], "answer", q, x, None, None, None, None]
                                      + ([None, None] if g_whiskers else []))
        P(G_SUBR, yc, "5" if g["grp"] == "5" else "0\u20134", ha="right", va="center_baseline",
          why="faithfulness score group")
        P(G_NX, yc, str(len(v)), printed={"sheet": "Fig. 5g", "row": row_i, "format": "{n}"}, va="center_baseline")
        DRAWN["g"]["rows"].append({"strategy": LABEL[g["strategy"]], "faithfulness": g["grp"], **g["q"],
                                   "dots_overlapping": over, "values": v})

    # header pieces must not run into each other (finish_plate checks text; these check swatches and keys)
    assert D_KEY_END < E_LET - 1.0, (D_KEY_END, E_LET)
    assert F_KEY_END < F_NX - 1.0, (F_KEY_END, F_NX)
    assert B_KEY_END < C_LET - 1.0

    return dict(locals())


# ---------------------------------------------------------------------------------------------------------------
# texts: the locked legend (its data-dependent words checked), the Source Data caption, the Methods notes
# ---------------------------------------------------------------------------------------------------------------
RLM = ("rlm_5", "rlm_10", "rlm_20")


def texts(dat, Z, R, reading: str = "loose") -> dict:
    """The locked legend (anchor_d166/legend.md), its counts written from the data and its fixed words checked
    against them, and the Methods notes (build_fig5.py's, with the scratch file references replaced by what this
    script computes). reading "loose" (L3, the locked plate's): the legend is the locked one word for word, its 19
    RLM fails of c checked. reading "D181" (D186 (4)): the same legend with c's RLM fails counted from the data (a
    clause on the question rule would take it to 361 words, over the journal's 350); the Methods name the reading and
    its rule."""
    if reading not in READINGS:
        raise Refused(f"reading {reading!r} is not one of {sorted(READINGS)}")
    A, C, D, F_OUT = dat["A"], dat["C"], dat["D"], dat["f_out"]
    qw, pts_b, pts_c = dat["qw"], dat["pts_b"], dat["pts_c"]
    PR = S473.PASS_RELAXED
    bad = []
    pap82 = [LABEL[o] for o in OTHERS if D[(o, "papers")]["n"] != len(qw)]
    a_short = [LABEL[c] for c in CONFIGS if len(A["papers"]["rows"][c]) != len(qw)]
    if pap82 != ["multi-hop", "RLM-5", "RLM-10"] or a_short != pap82 or any(
            D[(o, "papers")]["n"] != 82 for o in OTHERS if LABEL[o] in pap82):
        bad.append(f"'(82 for multi-hop, RLM-5 and RLM-10)': d's papers n short for {pap82}, a's for {a_short}")
    if any(D[(o, s)]["n"] != len(qw) for o in OTHERS for s in ("judge", "concept")):
        bad.append("d's judge and concept n are not the W questions'")
    if any(len(A[k]["rows"][c]) != A[k]["n"] for k in ("pass", "concept") for c in CONFIGS):
        bad.append("a's Judge and Concepts columns do not have every question for every strategy")
    if [(k, LABEL[c]) for k, c, *_ in Z["A_COLLAPSED"]] != [("pass", "single pass")] or \
            Z["A_COLLAPSED"][0][2] != 100:
        bad.append(f"'Single pass's Judge box is a line at 100': the collapsed boxes are {Z['A_COLLAPSED']}")
    if reading == "loose" and Z["B_UNPRINTED"] != [("multi-hop", 1)]:
        bad.append(f"'Multi-hop's 1 fail-high answer is unlabelled': the unprinted counts are {Z['B_UNPRINTED']}")
    # D203 (2 Nov): on other data the sentence is written from the counts (the locked words where they still hold)
    if Z["B_UNPRINTED"] == [("multi-hop", 1)]:
        b_unl = "Multi-hop's 1 fail-high answer is unlabelled. "
    elif Z["B_UNPRINTED"]:
        b_unl = ("Unlabelled fail-high: "
                 + ", ".join(f"{lab} {v}" for lab, v in Z["B_UNPRINTED"]) + ". ")
    else:
        b_unl = ""
    c_rlm_fail = sorted((p["judge"], p["question_id"], p["strategy"]) for p in pts_c
                        if p["strategy"] in RLM and p["all"] and not p["pass"])
    if len(c_rlm_fail) != sum(C[c]["fail"] for c in RLM) or (reading == "loose" and len(c_rlm_fail) != 19):
        bad.append(f"'Of the 19 RLM answers the judge fails': {len(c_rlm_fail)}")
    if bad:
        raise Refused("the locked legend's words no longer hold on these data (rewrite the legend): " + "; ".join(bad)
                      + "; nothing written")
    c_at3 = sum(1 for v, _, _ in c_rlm_fail if v == PASS_T - 1)
    c_other = [x for x in c_rlm_fail if x[0] != PASS_T - 1]
    c_fail_relaxed = sum(1 for v, _, _ in c_rlm_fail if v < PR)
    coll = Z["A_COLLAPSED"][0]
    a_coll_at, a_coll_n = coll[3], coll[4]
    n_c = sum(C[c]["pass"] + C[c]["fail"] for c in CONFIGS)
    LEGEND = (
        "**Figure 5 | Three evaluation signals and the judge's faithfulness score on the answers of six generation "
        "strategies.** "
        "Answers of gemini-3-flash-preview to the answerable questions. Judge, the judge's correctness score against "
        f"the answer key (pass at {PASS_T} or more of 5); Concepts, concept recall, the share of the key's concepts an "
        "answer states; Papers, MiniCheck precision, the share of an answer's claims the source papers support. "
        "**a**, Each signal per strategy: grey dots, questions; box, quartiles; black line, median; whiskers, "
        + ("the most extreme questions within 1.5 box widths of the box. " if reading == "loose" else
           "range. ")
        + "Judge (pass rate) and Concepts, three draws, "
        f"n = {A['pass']['n']} questions; Papers, draw 1, n = {A['papers']['n']} questions (82 for multi-hop, RLM-5 "
        f"and RLM-10). Single pass's Judge box is a line at 100, where {a_coll_at} of {a_coll_n} questions sit. "
        f"**b**, Draw-1 answers to {len(qw)} questions (n = {len(pts_b)} answers), by the judge's verdict and by "
        f"Papers precision: high, at or above the median of all {len(pts_b)} answers "
        f"({S457.half_up(dat['b_median'], 3)}); low, below it. {b_unl}"
        f"**c**, Of the same answers, those that state every key concept, by the judge's verdict (n = {n_c}); n at "
        f"right counts only these answers, so it differs by strategy. Of the {len(c_rlm_fail)} RLM answers the judge "
        f"fails, {c_at3} score {PASS_T - 1}. "
        "**d**, Questions where single pass or the strategy scores higher, and ties, per signal (Judge and Concepts, "
        f"per-question means of three draws; Papers, draw 1); n = {len(qw)} questions (Papers, as in a). "
        "**e**, Questions won minus lost against single pass, as a percentage, one mark per draw (Papers, draw 1); n "
        "as in d. In d and e the judge compares 0 to 5 scores, not a's pass rate. "
        "**f**, **g**, The judge's faithfulness score, given after reading the retrieved passages. **f**, Answers the "
        f"judge passes and fails on correctness, {dat['f_nq']} questions, three draws; n at right, excluding answers "
        "with no text or a failed faithfulness call. **g**, Papers precision of draw-1 answers with faithfulness 5 "
        f"and below 5 (n = {dat['G_N']} answers, {dat['G_NQ']} questions; n at right); dots (answers), boxes and "
        + ("median lines as in a, no whiskers." if reading == "loose" else
           "median lines as in a; whiskers, range.")
    )
    n_words = len(LEGEND.split())
    if n_words >= 350:
        raise Refused(f"the legend has {n_words} words, the journal's limit is under 350; nothing written")
    # Methods notes: e against d (single draws tie more often than three-draw means)
    e_vs_d = []
    for o in OTHERS:
        for s in ("judge", "concept"):
            m = D[(o, s)]
            d_net = 100.0 * (m["ot"] - m["sp"]) / m["n"]
            for x in dat["E_DRAWN"]:
                if x["strategy"] == o and x["signal"] == s:
                    e_vs_d.append((LABEL[o], s, x["draw"], m["tie"], x["ties"], round(d_net, 1),
                                   round(x["margin_pct"], 1)))
    e_shorter = sum(1 for r in e_vs_d if abs(r[6]) < abs(r[5]))
    e_more_ties = sum(1 for r in e_vs_d if r[4] > r[3])
    if e_more_ties != len(e_vs_d):
        raise Refused(f"the Methods' 'single draws tie more often than d's three-draw means' holds for {e_more_ties} "
                      f"of {len(e_vs_d)} marks; nothing written")
    # the W questions' MiniCheck nulls, per strategy, with L1's reason
    nulls = []
    for c in CONFIGS:
        for q in qw:
            r = R["l1"]["stages"]["papers"][(c, q, 1)]
            if (r.get("signals") or {}).get("precision") is None:
                nulls.append((LABEL[c], q, (r.get("null_reasons") or {}).get("precision")))
    null_txt = ", ".join(f"{s} {q} ({why})" for s, q, why in nulls)
    cc = dat["cc"]
    lv = sorted({int(S457.half_up(v, 0)) for c in CONFIGS for _, v in A["pass"]["rows"][c]})
    judge_levels = ", ".join(str(x) for x in lv[:-1]) + f" or {lv[-1]}"
    F_OUT_TXT = "; ".join(f"{LABEL[c]} {F_OUT[c]['no_answer']} with no text, {F_OUT[c]['error']} ended in an error"
                          for c in CONFIGS if sum(F_OUT[c].values()))
    # review 28 Oct F4: f's errors, each one's message read from the collect (S3 'b', the call with passages)
    f_err = [m for (c, q, d), (st, _, m) in R["faith_rows"].items() if st == "error" and q in dat["qa"]]
    if len(f_err) != sum(F_OUT[c]["error"] for c in CONFIGS):
        raise Refused(f"f: {len(f_err)} errors in the collect, the panel counts {sum(F_OUT[c]['error'] for c in CONFIGS)}")
    f_err_ctx = sum(1 for m in f_err if "exceeds the available context" in str(m))
    F_ERR_TXT = (f"; all {len(f_err)} errors are requests (answer and passages) longer than the judge's context "
                 "(the server's exceed_context_size_error), which the lock never cuts (LOCK.toml truncate = false)"
                 if f_err and f_err_ctx == len(f_err) else
                 f"; {f_err_ctx} of the {len(f_err)} errors are requests longer than the judge's context" if f_err else "")
    # review 28 Oct F4: an answer with no text: the judge's 0 (Rule 10) and L3's concept recall of it
    order = lambda k: (CONFIGS.index(k[0]), k[1], k[2])  # noqa: E731
    no_text = sorted((k for k, cell in R["read"]["cells"].items() if cell["kind"] == "failed" and k[1] in dat["qa"]),
                     key=order)
    l3_nt = sorted((k for k, r in R["l3"]["rows"].items() if r["status"] in ("no_answer", "error")
                    and k[1] in dat["qa"] and r.get("concept_recall_loose") is not None), key=order)
    if l3_nt != no_text or any(R["l3"]["rows"][k]["concept_recall_loose"] != 0 for k in l3_nt):
        raise Refused(f"the Methods' 'no text scores 0 for concept recall': the judge's failed answers {no_text}, L3's "
                      f"no-text rows with a value {l3_nt}; nothing written")
    NO_TEXT_TXT = ", ".join(f"{LABEL[c]} {q} draw {d}" for c, q, d in no_text)
    # review 28 Oct F4: L1's papers rows missing at the pull, and the questions they leave out of the W set
    have_p, planned_p = R["fn"]["have"]["papers"], S473.PLANNED["papers"]
    l1_missing = sorted((q, c) for c in CONFIGS for q in dat["qa"] if (c, q, 1) not in R["l1"]["stages"]["papers"])
    missing_qs = sorted({q for q, _ in l1_missing})
    if len(l1_missing) != planned_p - have_p or sorted(set(dat["qa"]) - set(qw)) != missing_qs:
        raise Refused(f"the Methods' L1 sentence: {len(l1_missing)} rows missing against {planned_p} - {have_p}, "
                      f"questions {missing_qs} against those outside W; nothing written")
    L1_TXT = (f" L1's papers stage had {have_p} of the {planned_p} draw-1 answerable rows when pulled "
              f"({R['pull_ended']}); the {len(l1_missing)} missing fall on {', '.join(missing_qs)}, left out of the W "
              "set until L1 ends." if l1_missing else "")
    # review 28 Oct F10: why single pass's Judge box is a line
    sp_pass = [v for _, v in A["pass"]["rows"]["single_pass"]]
    sp_below = sum(1 for v in sp_pass if v < 100)
    sp_sum = A["pass"]["summary"]["single_pass"]
    if not (sp_sum["quartile_25"] == sp_sum["median"] == sp_sum["quartile_75"] == 100
            and 4 * sp_below < len(sp_pass)):
        raise Refused(f"the Methods' 'under a quarter below 100' for single pass's Judge box: {sp_below} of "
                      f"{len(sp_pass)} below 100, quartiles {sp_sum}; nothing written")
    METHODS = [
        ("all panels", ("Concept recall is L3's loose matcher (D12), provisional until P2's labels choose the matcher. "
                        if reading == "loose" else
                        "Concept recall is D181's reading (D186 (4)): S505's loose matcher with the question rule, "
                        "Q-need, reading (b), on key v2.5 (findings/recompute/L3_d181, S471 --d181): a concept's content "
                        "words that also occur in its question do not count, the loose need rule applies to the words "
                        "left, and a concept made only of question words leaves the denominator. ") +
                       "MiniCheck precision is against the whole source papers, draw 1 only; the papers question set "
                       f"is S473's W set, the {len(qw)} answerable questions whose six draw-1 answers all have an L1 "
                       "papers row." + L1_TXT + " An answer with no text scores 0 for the judge (Rule 10) and 0 for "
                       f"concept recall ({'L3' if reading == 'loose' else 'L3_d181'} finds none of its concepts): {NO_TEXT_TXT}. "
                       "Q15 (open, Valerio's call; experiments/NOW.md, 28 October): MiniCheck scores as claims the "
                       "numbered source list that ends every RLM answer and the citation marks left in its sentences; "
                       "a measurement in the session scratch (not yet a repository script) found that the source-list "
                       "lines lower RLM precision, so every Papers value (a, b, c's answer set, d, e, g) may change "
                       "when Q15 is decided."),
        ("a", "Per question, the judge's pass share over its three draws (score "
              f"{PASS_T} or more) and concept recall as the mean of its three draws (Rule 7); MiniCheck precision from "
              f"draw 1. A question's judge value is one of {judge_levels} (three draws). Quartiles and median by "
              "numpy percentile (linear), as S457.summary. "
              + ("Whiskers (Tukey): from the box to the most extreme question value within 1.5 x the interquartile "
                 "range of the box" if reading == "loose" else
                 "Whiskers: from the box to the smallest and the largest question value (Valerio, 2 Nov: one "
                 "whisker rule, the range, in every figure)")
              + ", black, 0.5 pt, with caps, drawn over "
              "the grey dots; a whisker of zero length shows its cap only. No means or intervals (28 Oct review: the "
              f"boxes already show the spread). Single pass's Judge box has zero width: only {sp_below} of "
              f"{len(sp_pass)} questions score below 100 (under a quarter), so its 25th percentile, median and 75th "
              f"percentile are all 100, where {a_coll_at} of {a_coll_n} questions sit; it is drawn as the median "
              "line, taller than the dots. Column names are plain text; the draws and the n per strategy are in the legend. The W "
              f"questions' answers with no MiniCheck value: {null_txt}."),
        ("b", f"Papers above the median: MiniCheck precision at or above {dat['b_median']:.4f}, the median of all "
              f"{len(pts_b)} draw-1 answers of the six strategies pooled; the {dat['b_on']} answers exactly on it "
              "count as above. In the key, papers high = at or above this median, papers low = below it. "
              f"Judge pass = correctness {PASS_T} or more. n per strategy: "
              + ", ".join(f"{LABEL[c]} {dat['B'][c][4]}" for c in CONFIGS)
              + f" (the {len(nulls)} answers listed under a have no papers score). Light grey: judge passes and papers at or "
              "above the median; dark grey: judge fails and papers below. Reddish purple (judge passes, papers "
              "below) is used instead of vermillion, which read as the concepts orange. Counts too narrow for their "
              "segment are not printed: " + ", ".join(f"{a_} {v_}" for a_, v_ in Z["B_UNPRINTED"]) + "."),
        ("c", ("Every key concept: concept recall 1 (loose matcher; L3's found_loose equal to n_concepts). The n at "
               if reading == "loose" else
               "Every key concept: concept recall 1 (D181's reading; L3_d181's found equal to n_counted, the concepts "
               "left after the question rule). The n at ") +
              "right counts the strategy's answers that state every concept, not all its answers, so it differs by "
              f"strategy (header 'n, all concepts'). Judge fails = correctness {PASS_T - 1} or less. "
              f"{len(nulls)} answers of the {6 * len(qw)} are left out (no MiniCheck score), so the set equals b's. "
              f"Of the {len(c_rlm_fail)} RLM answers the judge fails, {c_at3} score {PASS_T - 1}"
              + "".join(f"; {LABEL[s]} {q} scores {v}" for v, q, s in c_other)
              + f"; at a pass mark of {PR} the {len(c_rlm_fail)} would be {c_fail_relaxed}."),
        ("d", "Per question: judge correctness (0 to 5) and concept recall averaged over draws 1 to 3; MiniCheck "
              "precision from draw 1; higher = strictly higher, tie = equal within 1e-9. Colours: reddish purple, single "
              "pass higher; grey, tie; bluish green, strategy higher (not orange and blue, which are the concept and "
              "judge colours). Column names are plain text (28 Oct review)."),
        ("e", "Margin = (wins minus losses) / (wins + ties + losses) x 100 for draw d of the strategy against draw d "
              "of single pass, on the W questions where both values exist; ties count in the denominator only. The "
              "judge compares the 0 to 5 scores, not the pass rate of a. Within a row Judge marks sit highest and "
              "Papers lowest. Single draws tie more often than d's three-draw means, so e's margins differ from d's "
              "bars. Marks closer than one marker width are moved up or down (never sideways): marks "
              f"{Z['MSZ_MM']} mm, offsets {Z['DODGE']} mm, closest centres {Z['E_MIN_GAP']:.2f} mm apart, so no two "
              f"marks overlap. Against d: in {e_shorter} of {len(e_vs_d)} judge and concept marks e's margin is "
              f"shorter than d's net share, and in {e_more_ties} of {len(e_vs_d)} the draw has more ties than d's "
              "three-draw means. Grey lines separate the strategies (D166). e repeats the strategy names and its key "
              "sits at the top left; the x axis reads 'Strategy minus single pass (% of questions)'. Kendall's W "
              f"over the three rankings of the six strategy means: W = {S457.half_up(cc['W'], 2)}, exact one-sided "
              f"P = {S457.half_up(cc['P'], 3)} (S473's compute; not drawn)."),
        ("f", "Faithfulness from the judge's call with passages (S3 'b'); pass = correctness of the plain call "
              f"{PASS_T} or more (Rule 5). Answers with no text and unscored faithfulness calls are left out: "
              + F_OUT_TXT + f" (each strategy has {dat['f_nq']} x 3 = {dat['f_nq'] * 3} answers)" + F_ERR_TXT + "."),
        ("g", "Answers with a scored faithfulness call and a MiniCheck precision (draw 1, every L1 papers row, so "
              f"{dat['G_NQ']} questions here against b's {len(qw)}). Swarm half width 1.1 mm; quartiles by numpy "
              "percentile (linear). g repeats the strategy names; one heading 'Faithfulness' over sub-rows '5' and "
              "'0–4' (28 Oct review)."),
    ]
    return {"legend": LEGEND, "words": n_words, "methods": METHODS, "e_vs_d": e_vs_d, "e_shorter": e_shorter,
            "e_more_ties": e_more_ties, "c_rlm_fail": c_rlm_fail, "papers_nulls_W": nulls}


def caption_text(stamp, reading: str = "D181") -> str:
    return (
        f"# Source Data Fig. 5, caption\n\n**Source Data Fig. 5 | Numerical values plotted in Figure 5.** "
        f"Data stamp: {stamp}. One sheet per panel. "                   # S448 R8 (4): the caption carries the stamp
        "Fig. 5a: per strategy and signal a summary row (median, quartiles, "
        + ("Tukey whisker ends" if reading == "loose" else "whisker ends, the range") + ", questions) and one row "
        "per plotted question. Fig. 5b: per strategy the draw-1 "
        "answers in the four groups of the judge's verdict and the papers' precision against the pooled median. Fig. "
        "5c: per strategy the draw-1 answers that state every key concept, by the judge's verdict, and their total. "
        "Fig. 5d: per strategy and signal the questions where single pass scores higher, ties and where the strategy "
        "scores higher. Fig. 5e: per strategy against single pass, signal and draw, the wins, ties, losses, questions "
        "and the margin. Fig. 5f: per strategy and judge verdict the answers at each "
        "faithfulness score and their share. Fig. 5g: per strategy and faithfulness group a summary row (n, "
        "quartiles, median) and one row per plotted answer. Generated by "
        f"`uv run --frozen python {SCRIPT} figure` from S3's collect output (findings/recompute/fig2_inputs, each "
        f"answer's judge row read through scripts/judge_rows_v25.py), L1's rows (findings/recompute/{SET_DIR}) and "
        + ("L3's rows (findings/recompute/L3/concept_recall.jsonl, pinned by sha256 in S473)" if reading == "loose" else
           "concept recall on D181's reading (findings/recompute/L3_d181/concept_recall.jsonl, pinned by sha256 in "
           "S497, held to L3's answers)")
        + f", with G1's answer texts from {K1_TAR}.tar and {G1R15_TAR}.tar.\n\n"
        "Proposed Data Availability sentence: \"The source data for Figure 5 is in Supplementary Data 6.\"\n")   # D303 follow-up: the D166 path keeps Figure 5, so Data 6 (D302)


def changed_cells(before: dict, after: dict) -> dict:
    """Per Source Data sheet, the cells that differ between two builds (rows compared in order; a sheet whose row
    count or columns differ is given as its two row counts)."""
    out = {}
    for name in after:
        a, b = before.get(name) or {"columns": None, "rows": []}, after[name]
        if a["columns"] != b["columns"] or len(a["rows"]) != len(b["rows"]):
            out[name] = {"rows_before": len(a["rows"]), "rows_after": len(b["rows"])}
            continue
        out[name] = sum(1 for ra, rb in zip(a["rows"], b["rows"]) for x, y in zip(ra, rb) if jnorm(x) != jnorm(y))
    return out


# ---------------------------------------------------------------------------------------------------------------
# D200: the plate of the module docstring's D200 section. Everything above stays the reproduce step.
# ---------------------------------------------------------------------------------------------------------------
D200_SET, S6_SET = "fig5_d200", "fig3_s6"
D200_DIR = FR.RECOMPUTE / f"{D200_SET}_inputs"
L1_PLANNED = {"papers": 810, "key": 2430, "overlap": 2430}      # plan.csv row L1; fig5.md section 7, R2
PLATE_KINDS = ("comparison",)                                   # c (old 5d); old 5b's verdict colours left with it (D295)
CONCEPT_PASS, PAPERS_PASS = 0.5, 0.5                            # S08b:281-287, the protocol's pass marks
SUBSETS = (("Judge", ("judge",)), ("Concepts", ("concept",)), ("Papers", ("papers",)),
           ("Judge + Concepts", ("judge", "concept")), ("Judge + Papers", ("judge", "papers")),
           ("Concepts + Papers", ("concept", "papers")), ("All three", ("judge", "concept", "papers")))
# D296 (Valerio, 7 November, thread 103fc108): the mixes' labels spelled out (were "J + C", "J + P", "C + P"), and b's
# right-hand column of left-out counts removed, with LEFT_OUT and ablation's counts
SIG_NAME = {"judge": "Judge", "concept": "Concepts", "papers": "Papers"}
S06_SUBSET = {"det": ("det",), "judge": ("judge",), "mc": ("mc",), "det+judge": ("det", "judge"),
              "det+mc": ("det", "mc"), "judge+mc": ("judge", "mc"), "det+judge+mc": ("det", "judge", "mc")}
S06_COLS = {"det": "det_score_correctness", "judge": "judge_correctness", "mc": "mc_f1"}   # S06_metric_ablation.py
# 5e's rows drawn. fig5.md section 1: if the reading by rows is refused (Q3), this becomes (), and nothing else changes.
E_ROWS_DRAWN = tuple(r[0] for r in S540.ROWS_5E if r[2] is not None)
# D208 (Valerio, 2 Nov): Papers' claims go through a Claimify-style selection (S564) before MiniCheck's precision is taken,
# and HEADING_RULE stayed unset. While no reader of S564's frozen selection exists (PAPERS_SELECTION) and HEADING_RULE is
# None, every Papers value of the D200 plate waits: drawn nowhere, its Source Data cells blank, the reason in its row, as
# D206's --papers-waits does on Figure 2 and Supplementary Figure 3. With a heading rule set (no_heading since D245, or a
# test's fixture rule in S497_fig5_d200_test.py) the plate draws filtered Papers instead. D212 Q6 (Valerio, 3 Nov): 5c and 5e on the re-run answers, so the plate is built without waiting.
#
# PAPERS_SELECTION (4 Nov): the reader of S564's frozen selection. It names the 8 shards of S564 --set full, their one
# run_sha256 and each rows.jsonl's sha256; read_selection() reads them and refuses another run, a changed file, a
# sentence twice, a sentence outside S564's unit list, a gap, or a tally that differs from the shard's summary.json (the
# known number S564 wrote). An answer's Papers is then MiniCheck's supported share over its sentences S564 selected (every
# outcome but "none", D208 (d)) that minicheck_filter.kept also keeps (its source-list pattern and HEADING_RULE, no_heading
# since D245). None turns the selection off: Papers is then the filter alone, or waits when HEADING_RULE is None too.
S564_FULL = ROOT / "findings" / "recompute" / "S564_claimify_selection" / "full"
PAPERS_SELECTION = {
    "dir": S564_FULL, "shards": 8,
    "run_sha256": "6934ed46ccabd396a32f2cab73774f7ac06e6d6689ff9fb57bcf1f4941b6904c",
    "rows_sha256": {0: "625c826c7d9754fdf4138706a473be0c1db2a27cfac6b81e24119d6ed24957e2",
                    1: "9d16d8ef2e3728cf4a1ee7496533137b52b81ba378b49879a6261a9fc97a51c8",
                    2: "c468afe65bf3ec2e8f1d3378f6c4c25e76bf0c843c1f4abb5457541e56ea8a1e",
                    3: "285557e2076d4929b9884d357c77d06a837f12ff4ad04ab899697f202fab346c",
                    4: "02836c18e7beb0e153cadd155e426e300a6ff64616084cd6539c6d2bfd18d8a2",
                    5: "98aa0c9a01228b529822db4afb417ff2d089e0a57ad5858723aa329d1d381143",
                    6: "c2207de96ab259dfe75f845250f4854fe1f8c76a1f20ce7c93e0a3c9fe96bd9d",
                    7: "d79480616e40d3ffa7c7043eb7ab62ab88fbea9ce4ecb63061e7137af8b66eb0"}}
# A sentence S564 gave no verdict: status "unparseable" (devstral's output did not parse; S564 does not retry at
# temperature 0) or "length" (its reply reached the lock's num_predict 16,384). S564's run has 8 and 4 (4 Nov).
#   "left out and counted"  the sentence leaves Papers, as a "none" sentence does, and is counted in the note
#   "kept as selected"      the sentence stays in Papers, as an "all", "some" or "contains" sentence does
# The default follows S564's own frozen record: S564 writes leaves_papers false on every row with no verdict
# (S564_claimify_selection.py:375, bool(parsed) and ...), so the selection D208 built keeps them (review wf_6a31c890-5ce F3).
# The other reading stays available and tested; changing it is the first author's call. fig5_data_state.json's
# claim_filter counts the sentences and answers each reading touches.
NO_VERDICT_READINGS = ("left out and counted", "kept as selected")
NO_VERDICT = "kept as selected"
STORED_CLAIM_CHARS = 300                # S19.check stores claims[i][:300] (as S564.STORED_CLAIM_CHARS)
NO_SELECTION = "no S564 selection: the answer is not among the L1 answers S564 judged (D208's 506 of 28 October)"
NONE_SELECTED = "no sentence left after S564's selection and the source-list filter"
PAPERS_WAITS = "waits for S564's selection (D208)"
PENDING = "[PENDING]"


def papers_waits() -> bool:
    """True while Papers has no final value: no S564 selection reader and HEADING_RULE None (no_heading since D245)."""
    return PAPERS_SELECTION is None and MF.HEADING_RULE is None


def selection_units() -> list:
    """S564's unit list for --set full, as sentence ids: S564's L1 units (S564.build("l1"): S560's census and the D5 key,
    both pinned by S564), in order, then the sentences of Figure 2's 49 answers, exp04|<config>|<question>|<eval_id>#i
    for i below n_claims of S498's stored row (S564.h49_units' answer_key). S564.build("full") would rebuild the 49 from
    S498.read_items, whose item file this figure does not open, so the 49 are checked as a set and never read further."""
    S564 = _load("S564_claimify_selection", ROOT / "scripts" / "S564_claimify_selection.py")
    questions, _ = S564.key_questions()
    l1 = [u["sentence_id"] for u in S564.l1_units(questions=questions)]
    h49 = [f"exp04|{r['config']}|{r['question_id']}|{r['eval_id']}#{i}" for r in jl(S564.S498_ROWS)
           for i in range(r["n_claims"])]
    if len(l1) != S564.N_L1 or len(h49) != S564.N_H49:
        raise Refused(f"S564's unit list: {len(l1)} L1 and {len(h49)} Figure 2 sentences, not {S564.N_L1} and "
                      f"{S564.N_H49}; nothing written")
    return l1 + h49


def read_selection(sel: dict | None = None, units: list | None = None) -> dict:
    """S564's rows, one per sentence id, read whole from the shards PAPERS_SELECTION names, or Refused. Checks: each
    rows.jsonl has its pinned sha256 (sel["rows_sha256"]; a test passes None to skip it), every row is under
    sel["run_sha256"], no sentence id twice, every id one of S564's units, an L1 row in the shard S564's rule puts it in
    (place in the set modulo the shards), every unit present, each row's status ok, unparseable or length (an ok row
    with an outcome), and per shard the tally of status, outcome and leaves_papers equal to its summary.json."""
    sel = PAPERS_SELECTION if sel is None else sel
    units = selection_units() if units is None else units
    n = sel["shards"]
    pos = {s: j for j, s in enumerate(units)}
    if len(pos) != len(units):
        raise Refused("S564's unit list names a sentence twice; nothing written")
    rows, files = {}, {}
    for k in range(n):
        d = Path(sel["dir"]) / f"shard_{k}_of_{n}"
        f = d / "rows.jsonl"
        if not f.exists() or any(p.is_dir() and p.name.startswith("part_") for p in d.iterdir()):
            raise Refused(f"{f}: missing, or the shard is split into parts, which this reader does not read")
        files[k] = sha256_file(f)
        pins = sel.get("rows_sha256")
        if pins is not None and k not in pins:          # review F4: only None (a test) skips the pin
            raise Refused(f"{f}: PAPERS_SELECTION pins no sha256 for shard {k}")
        want = (pins or {}).get(k)
        if want and files[k] != want:
            raise Refused(f"{f} is {files[k][:12]}, PAPERS_SELECTION pins {want[:12]}: not the frozen selection")
        tally = {"status": Counter(), "outcome": Counter(), "leaves_papers": 0}
        for r in jl(f):
            sid = r["sentence_id"]
            if r["run_sha256"] != sel["run_sha256"]:
                raise Refused(f"{f}: {sid} under run {r['run_sha256'][:12]}, not {sel['run_sha256'][:12]}")
            if sid in rows and rows[sid]["status"] == "ok":   # a later row only follows a row with no verdict (a retry)
                raise Refused(f"{f}: {sid} has a second row after an ok row; nothing written")
            if sid not in pos:
                raise Refused(f"{f}: {sid} is not one of S564's units; nothing written")
            if r["set"] == "l1" and pos[sid] % n != k:
                raise Refused(f"{f}: {sid} is in shard {k}, S564's rule puts it in {pos[sid] % n}")
            if r["status"] not in ("ok", "unparseable", "length") or (r["status"] == "ok") != bool(r.get("outcome")):
                raise Refused(f"{f}: {sid} has status {r['status']!r} and outcome {r.get('outcome')!r}")
            if r["status"] == "ok" and bool(r["leaves_papers"]) != (r["outcome"] == "none"):   # review F3
                raise Refused(f"{f}: {sid} leaves_papers {r['leaves_papers']} disagrees with outcome {r['outcome']!r}")
            if sid in rows:                                 # the retried row is replaced: undo its tally
                o = rows[sid]
                tally["status"][o["status"]] -= 1
                tally["outcome"][o["outcome"]] -= bool(o["outcome"])
                tally["leaves_papers"] -= bool(o["leaves_papers"])
            rows[sid] = r
            tally["status"][r["status"]] += 1
            tally["outcome"][r["outcome"]] += bool(r["outcome"])
            tally["leaves_papers"] += bool(r["leaves_papers"])
        s = json.loads((d / "summary.json").read_text())
        mine = ({k_: v for k_, v in tally["status"].items() if v}, {k_: v for k_, v in tally["outcome"].items() if v},
                tally["leaves_papers"])
        if s["run_sha256"] != sel["run_sha256"] or mine != (s["status"], s["outcome"], s["leaves_papers"]):
            raise Refused(f"{d}: rows give status {mine[0]}, outcome {mine[1]}, leaves {mine[2]}; summary.json "
                          f"{s['status']}, {s['outcome']}, {s['leaves_papers']}")
    gaps = [s for s in units if s not in rows]
    if gaps:
        raise Refused(f"S564's selection has no row for {len(gaps)} units, first {gaps[0]}; nothing written")
    d = Path(sel["dir"]).resolve()
    return {"rows": rows, "files": files, "run_sha256": sel["run_sha256"],
            "dir": d.relative_to(ROOT).as_posix() if d.is_relative_to(ROOT) else "a test's folder",
            "status": dict(Counter(r["status"] for r in rows.values()))}


def selected(r: dict, reading: str) -> bool:
    """One S564 row: does its sentence stay in Papers? An ok row stays unless its outcome is "none" (D208 (d)); a row
    with no verdict follows the reading (NO_VERDICT)."""
    if reading not in NO_VERDICT_READINGS:
        raise Refused(f"NO_VERDICT is {reading!r}, not one of {NO_VERDICT_READINGS}")
    if r["status"] == "ok":
        return r["outcome"] != "none"
    return reading == "kept as selected"


def d200_waits(anchor_applies=None, set_dir=None) -> list:
    """What the D200 plate still waits for; empty when `figure` builds it. Since D208 the heading rule is not waited for:
    Papers waits inside the plate (papers_waits). anchor_applies: this run's srcs["anchor_applies"], empty when its rows
    are not the frozen ones, so the D166 plate was not held to anchor_d166 and nothing new may be drawn (fig5.md section
    8). set_dir: a test's folder."""
    w = []
    if not (set_dir or D200_DIR.exists()):
        w.append(f"findings/recompute/{D200_SET}_inputs is not frozen")
    if not anchor_applies:
        w.append("this run did not hold the D166 plate to anchor_d166 (its rows are not the frozen ones)")
    return w


def d200_sources(set_dir=None) -> dict:
    """The frozen D200 set: l1/ and k1/ of fig5_d200_inputs, each committed file held to frozen_inputs/SHA256SUMS, and
    the S6 rows of fig3_s6_inputs (build order F3), held to that set's own SHA256SUMS by fig_repro.frozen. set_dir: a
    folder in the same layout, for a test only; it is not pinned and its provenance says so."""
    if set_dir is None:
        base = FR.check_committed(FR.frozen(D200_SET))
        pinned = True
    else:
        base, pinned = Path(set_dir), False
    s6 = FR.frozen(S6_SET)
    sha = {f"{D200_DIR.name}/{p.relative_to(base).as_posix()}": sha256_file(p)
           for p in sorted(base.rglob("*")) if p.is_file()}
    if PAPERS_SELECTION is not None:          # D208: S564's rows, which read_selection holds to these same pins
        n = PAPERS_SELECTION["shards"]
        for k in range(n):
            p = Path(PAPERS_SELECTION["dir"]) / f"shard_{k}_of_{n}" / "rows.jsonl"
            if p.exists():
                sha[p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)] = sha256_file(p)
    return {"l1": base / "l1", "k1": base / "k1", "s6": s6, "sha": sha, "pinned": pinned}


def apply_claim_filter(l1: dict, tmp=None, selection: dict | None = None, reading: str | None = None) -> dict:
    """On a copy, each papers row's signals.precision through minicheck_filter (D172 A5-Q1, every strategy). A row with
    stored null keeps it and its reason. A stored value with no detail.per_claim cannot be recomputed, so it is refused.
    With no claim left the value is null with the filter's reason. tmp: where the filtered rows are written, because
    panel_data reads the raw L1 rows from its folder. Returns the copy, with "filter_note" (rows read, rows with a value,
    values changed, values now null) and "dir".
    selection: read_selection()'s result (D208). Each claim i of a row is then S564's sentence <answer_key>#i, its text
    held to the first 300 characters of S564's sentence (S19 stores claims cut at 300), and only the claims S564 selected
    (selected(), under reading) go to minicheck_filter; each claim of the copy carries "selected". A row whose answer S564
    did not judge is null (NO_SELECTION), one with no claim left is null (NONE_SELECTED); both are counted, by group."""
    reading = NO_VERDICT if reading is None else reading
    rows, changed, nulled, with_v = {}, 0, 0, 0
    sel_rows = selection["rows"] if selection else None
    by_answer: dict = {}
    if sel_rows is not None:
        for sid, s in sel_rows.items():
            by_answer.setdefault(sid.rsplit("#", 1)[0], {})[int(sid.rsplit("#", 1)[1])] = s
    sn = {"not_judged": Counter(), "none_selected": Counter(), "no_verdict_sentences": Counter(),
          "no_verdict_answers": set(), "sentences_read": 0, "sentences_selected": 0, "no_verdict_changed": []}
    for k, r in l1["stages"]["papers"].items():
        pc = (r.get("detail") or {}).get("per_claim")
        old = (r.get("signals") or {}).get("precision")
        if old is None:
            rows[k] = r
            continue
        if not pc:
            raise Refused(f"L1 papers row {k}: a stored precision with no detail.per_claim, which the filter cannot "
                          "recompute; nothing written")
        with_v += 1
        nr = dict(r.get("null_reasons") or {})
        if sel_rows is None:
            v, why = MF.precision_and_reason(pc)
        else:
            s_ans = by_answer.get(r["answer_key"])
            if s_ans is None:
                v, why = None, NO_SELECTION
                sn["not_judged"][r.get("group")] += 1
            else:
                if sorted(s_ans) != list(range(len(pc))):
                    raise Refused(f"L1 papers row {k}: {len(pc)} claims, S564 holds sentences {min(s_ans)} to "
                                  f"{max(s_ans)} ({len(s_ans)}); nothing written")
                pc = [dict(c) for c in pc]
                other = []
                for i, c in enumerate(pc):
                    s = s_ans[i]
                    if c["claim"] != s["sentence"][:STORED_CLAIM_CHARS]:
                        raise Refused(f"L1 papers row {k}: claim {i} is not S564's sentence {r['answer_key']}#{i}")
                    c["selected"] = selected(s, reading)
                    if s["status"] != "ok":
                        sn["no_verdict_sentences"][s["status"]] += 1
                        sn["no_verdict_answers"].add(r["answer_key"])
                        other.append(c)
                sn["sentences_read"] += len(pc)
                sn["sentences_selected"] += sum(c["selected"] for c in pc)
                left = [c for c in pc if c["selected"]]
                v, why = MF.precision_and_reason(left) if left else (None, NONE_SELECTED)
                if v is None:
                    why = NONE_SELECTED
                    sn["none_selected"][r.get("group")] += 1
                if other:           # the value under the other reading, so the note shows what the choice moves
                    flip = [dict(c, selected=selected(s_ans[i], [x for x in NO_VERDICT_READINGS if x != reading][0]))
                            for i, c in enumerate(pc)]
                    left2 = [c for c in flip if c["selected"]]
                    v2 = MF.precision_and_reason(left2)[0] if left2 else None
                    sn["no_verdict_changed"].append([r["answer_key"], v, v2])
                r = {**r, "detail": {**r["detail"], "per_claim": pc}}
        if v is None:
            nulled += 1
            nr["precision"] = why
        changed += v != old
        rows[k] = {**r, "signals": {**r["signals"], "precision": v}, "null_reasons": nr}
    note = {"rows_read": len(rows), "rows_with_a_value": with_v, "values_changed": changed, "values_now_null": nulled}
    if sel_rows is not None:
        note["selection"] = {
            "s564_run_sha256": selection["run_sha256"], "dir": selection["dir"], "no_verdict_reading": reading,
            "rows_sha256": selection["files"], "s564_status": selection["status"],
            "sentences_read": sn["sentences_read"], "sentences_selected": sn["sentences_selected"],
            "answers_not_judged_by_group": dict(sn["not_judged"]),
            "answers_none_selected_by_group": dict(sn["none_selected"]),
            "no_verdict_sentences_by_status": dict(sn["no_verdict_sentences"]),
            "no_verdict_answers": len(sn["no_verdict_answers"]),
            "no_verdict_answers_value_this_reading_and_other": sorted(sn["no_verdict_changed"])}
    out = {**l1, "stages": {**l1["stages"], "papers": rows}, "filter_note": note}
    if tmp is not None:
        d = Path(tmp) / "l1_filtered"
        (d / "papers").mkdir(parents=True, exist_ok=True)
        with open(d / "papers" / "filtered.jsonl", "w") as fh:
            for r in rows.values():
                fh.write(json.dumps(r) + "\n")
        out["dir"] = d
    return out


def subset_ranks(means: dict, subsets, configs) -> dict:
    """R7: each signal's rank, 1 best, ties sharing the average rank (rankdata(-means), S06_metric_ablation.py:95-98);
    a subset's rank is rankdata of the mean of its members' ranks. A one-signal subset goes through the same call."""
    import numpy as np
    from scipy.stats import rankdata
    rk = {s: rankdata([-means[s][c] for c in configs]) for s in means}
    out = {}
    for name, members in subsets:
        r = rankdata(np.mean([rk[m] for m in members], axis=0))
        out[name] = {c: float(v) for c, v in zip(configs, r)}
    return out


def check_ablation_s06() -> str:
    """R7's gate. subset_ranks on S06's per-configuration means (master_join.csv, answerable rows, its three columns)
    gives S06_metric_ablation.json's subset_table: S06 ranks 1 worst, so its rank is 7 minus this one."""
    import csv
    p = ROOT / "findings" / "recompute" / "master_join.csv"
    with open(p) as fh:
        rows = [r for r in csv.DictReader(fh) if r["answerable"] == "True"]
    means = {s: {c: statistics.mean(float(r[col]) for r in rows if r["config"] == c) for c in CONFIGS}
             for s, col in S06_COLS.items()}
    got = subset_ranks(means, tuple(S06_SUBSET.items()), CONFIGS)
    table = json.loads((ROOT / "findings" / "recompute" / "S06_metric_ablation.json").read_text())["subset_table"]
    bad = [t["subset"] for t in table
           if any(abs(7 - got[t["subset"]][c] - t["ranks"][c]) > 1e-9 for c in CONFIGS)]
    if bad or len(table) != len(S06_SUBSET) or len(rows) != 528:
        raise Refused(f"5c's ranks differ from S06_metric_ablation.json on {bad}; nothing written")
    return f"5c's rank rule gives S06's subset_table on S06's means ({len(table)} subsets, {len(rows)} answers)"


def rank_text(v: float) -> str:
    """A rank as printed: "3" and "3.5", so both come out as written (fig5.md section 3)."""
    return f"{v:g}"


def papers_n(ns: dict) -> str:
    """A precise n per strategy for a legend, never a range (S448 R9). ns: strategy to n. The largest n, then the
    strategies that have another: "83, or 82 for multi-hop, RLM-5 and RLM-10"."""
    top = max(ns.values())
    others = {}
    for c, v in ns.items():
        if v != top:
            others.setdefault(v, []).append(LABEL[c])
    if not others:
        return str(top)
    parts = [f"{v} for {' and '.join([', '.join(names[:-1]), names[-1]] if len(names) > 1 else names)}"
             for v, names in sorted(others.items(), reverse=True)]
    return f"{top}, or {', '.join(parts)}"


def ablation(dat: dict) -> dict:
    """5c. Ranks of the six strategies under each subset from compute's means on the W questions. While Papers waits, a
    subset holding Papers has no rank. The left-out counts were removed under D296."""
    if papers_waits():
        keep = tuple((n, m) for n, m in SUBSETS if "papers" not in m)
        got = subset_ranks({s: dat["cc"]["means"][s] for s in ("judge", "concept")}, keep, CONFIGS)
        return {"ranks": {n: got.get(n, {c: None for c in CONFIGS}) for n, _ in SUBSETS}, "kendall": None}
    ranks = subset_ranks(dat["cc"]["means"], SUBSETS, CONFIGS)
    singles = [n for n, m in SUBSETS if len(m) == 1]
    kw = kendall_w_exact([[ranks[n][c] for c in CONFIGS] for n in singles], singles)
    # reproduce before writing: the same W and P as S473's concordance on the means (fig5_data_state.json c.W, c.P)
    if any(abs(kw[a] - dat["cc"][b]) > 1e-9 for a, b in (("W", "W"), ("exact_P", "P")) if dat["cc"].get(b) is not None):
        raise Refused(f"Kendall's W from b's ranks {kw['W']}, P {kw['exact_P']} differ from S473's {dat['cc'].get('W')}, "
                      f"{dat['cc'].get('P')}")
    return {"ranks": ranks, "kendall": kw}


def kendall_w_exact(rk: list, names: list) -> dict:
    """D309 N6 O1 (and A70): Kendall's W of the single signals' ranks of the strategies (b's one-signal rows), with the
    tie correction, and its exact P: the share of all orderings of every signal's ranks but the first (6!^2 = 518,400 for
    three signals and six strategies) whose W is at least the observed. One-sided by construction (W >= observed)."""
    import itertools
    import numpy as np
    rk = np.asarray(rk, float)
    m, n = rk.shape

    def spread(tot):
        return ((tot - tot.mean(-1, keepdims=True)) ** 2).sum(-1)
    ties = sum(float(sum(t ** 3 - t for t in np.unique(r, return_counts=True)[1])) for r in rk)
    s_obs = float(spread(rk.sum(0)))
    W = 12 * s_obs / (m * m * (n ** 3 - n) - m * ties)
    tot = rk[0][None, :]
    for r in rk[1:]:
        perms = np.array(list(itertools.permutations(r)))
        tot = (tot[:, None, :] + perms[None, :, :]).reshape(-1, n)
    P = float(np.mean(spread(tot) >= s_obs - 1e-9))
    return {"W": W, "exact_P": P, "signals": list(names), "strategies": n, "orderings": int(tot.shape[0])}


def panel_data_d200(R: dict) -> dict:
    """panel_data's numbers, plus: a's range whiskers and counts, 5c, the table of answers and 5e's rows. The rows of
    fn["e"] hold S540.rho_box to S473.answer_rho first (R5)."""
    dat = panel_data(R)
    # R5's gate runs on S473's e rows as stored (faithfulness against L1's stored precision): it holds the statistic to
    # answer_rho; while Papers waits none of these values is drawn or written
    rep = S540.check_rho_box([(p["question_id"], p["faithfulness"], p["papers_precision"])
                              for p in R["fn"]["e"]["points"]])
    waits = papers_waits()
    if waits:
        dat = blank_papers(dat)
    dat["box"] = {col: {c: (hs.box_stats([v for _, v in dat["A"][col]["rows"][c]], "range")
                            if dat["A"][col]["rows"][c] else None) for c in CONFIGS}
                  for col, *_ in dat["a_specs"]}
    dat["a_counts"] = {c: Counter(round(v, 9) for _, v in dat["A"]["pass"]["rows"][c]) for c in CONFIGS}
    dat["ablation"] = ablation(dat)
    dat["table"] = S540.answer_table(R["read"]["cells"], R["faith_rows"], R["l3"]["rows"], R["l1"]["stages"], R["k1"],
                                     R["groups"], CONFIGS)
    if waits:
        dat["table"] = [{**r, "papers": None} for r in dat["table"]]
    # D267 (rulings page 6 Nov, FIG5E: O1): 5e's last row from S518's second-judge rows on the final key
    sj = S540.second_judge_final()
    dat["table"] = S540.second_judge_table(dat["table"], sj["rows"])
    dat["second_judge"] = {k: v for k, v in sj.items() if k != "rows"}
    drawn = tuple(x for x in E_ROWS_DRAWN if not (waits and x == "Papers"))
    dat["e_rows"] = S540.evaluator_rows(dat["table"], drawn=drawn)
    if waits:
        for r in dat["e_rows"]:
            if r["row"] == "Papers":
                r["source"] = PAPERS_WAITS
    dat["papers_waits"] = waits
    dat["rho_gate"] = rep
    return dat


def blank_papers(dat: dict) -> dict:
    """While Papers waits (papers_waits), every value panel_data took from L1's stored precision is removed, so none is
    drawn or written: a's Papers column, b (every answer of it needs Papers), the old c built on b's answers, d's
    Papers facet, the margins of Papers and g. What stays reads no Papers value; the W questions are those whose six
    draw-1 answers have an L1 papers row, which does not depend on its value."""
    A = dict(dat["A"])
    A["papers"] = {"rows": {c: [] for c in CONFIGS}, "summary": {c: None for c in CONFIGS}, "n": 0}
    D = {k: (v if k[1] != "papers" else {"sp": None, "tie": None, "ot": None, "n": None}) for k, v in dat["D"].items()}
    cc = {k: v for k, v in dat["cc"].items() if k in ("questions", "partial_blocks_left_out")}
    cc["means"] = {s: dict(dat["cc"]["means"][s]) for s in ("judge", "concept")}
    return {**dat, "A": A, "pts_b": [], "B": {c: [None] * 5 for c in CONFIGS}, "b_median": None, "b_on": None,
            "pts_c": [], "C": None, "C_TOT": None, "D": D,
            "E_DRAWN": [e for e in dat["E_DRAWN"] if e["signal"] != "papers"], "cc": cc, "G": [], "G_N": None,
            "G_NQ": None}


def papers_left(sheets: dict) -> list:
    """While Papers waits: the Source Data cells that hold a value read from Papers, each as (sheet, row index, column).
    figure refuses to write when any is found."""
    out = []
    for name, sh in sheets.items():
        cols = sh["columns"]
        for i, row in enumerate(sh["rows"]):
            r = dict(zip(cols, row))
            if name == f"Fig. {FIG_N}a" and r["signal"] == "papers":
                keys = ("value", "median", "quartile_25", "quartile_75", "whisker_low", "whisker_high", "n_questions")
            elif name == f"Fig. {FIG_N}b" and "Papers" in (r["members"] or "").split(" + ") or (
                    name == f"Fig. {FIG_N}b" and r["row_kind"] == "left-out count"):
                keys = ("rank", "rank_text", "fails_n", "n_answers")
            elif name == f"Fig. {FIG_N}c" and r["signal"] == "papers":
                keys = ("single_pass_higher", "tie", "strategy_higher", "n_questions")
            elif name == f"Fig. {FIG_N}e" and r["row"] == "Papers":
                keys = ("rho", "resample_q25", "resample_median", "resample_q75", "interval_lo", "interval_hi",
                        "within_question_rho", "answers", "questions")
            else:
                continue
            out += [(name, i, k) for k in keys if r.get(k) is not None]
    return out


class Page:
    """One plate in house style: a page axes in mm from the top left and the printed map S448 R8 (6) reads."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.fig = hs.figure(w, h)
        self.pg = self.fig.add_axes((0, 0, 1, 1))
        self.pg.set_xlim(0, w)
        self.pg.set_ylim(h, 0)
        self.pg.axis("off")
        self.printed = {}
        self.k = 0

    def t(self, x, y, s, printed=None, why="a label", **kw):
        txt = hs.text_mm(self.fig, x, y, s, **kw)
        if re.search(r"\d", s):
            gid = f"s448num_{self.k}"
            self.k += 1
            txt.set_gid(gid)
            self.printed[gid] = printed if printed else {"fixed": s, "why": why}
        return txt

    def letter(self, x, y, s):
        hs.panel_letter(self.fig, x, y, s)

    def rect(self, x, y, w, h, fc, ec="none", lw=0.0, z=1):
        from matplotlib.patches import Rectangle
        self.pg.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))

    def ax(self, x, y, w, h, xlim, ylim):
        a = hs.axes_mm(self.fig, x, y, w, h, spines_on=("bottom",))
        a.set_xlim(*xlim)
        a.set_ylim(*ylim)
        a.set_yticks([])
        return a


def d200_layout() -> dict:
    """fig5.md section 4's geometry in mm, with Valerio's note of 2 November: 3.6 mm more between bands, so an axis title
    reads as its own panel's. PAD holds an axis (ticks and title); GAP is PAD plus the space between bands. The 7.2 mm
    came from the 1.2 mm spare and from band 2's rows, 7.6 to 6.4 (evaluator rows 3.79 to 3.25; FF2 a allows 3.0)."""
    tw = hs._text_width_mm
    LABW = max(tw(LABEL[c]) for c in CONFIGS) + 0.4
    # D295 (Valerio's "go", 7 November, thread 206c8013): six panels in three bands. Band 1: a (each signal per
    # strategy) and b (ranks, old c); band 2: c (wins, old d) and d (faithfulness by verdict, old f); band 3: e (Papers
    # by faithfulness, old g) and f (evaluators, old e). Old b moved to Supplementary Figure 12c (S543). a's column heads
    # sit on the letter line, so its rows start at 7 mm; d and e keep old f's and g's 12 sub-rows at 3.1 mm (3.2 before)
    # with 0.9 mm (1.0) between strategies, so the plate stays under 170 mm.
    g = {"LINE": 3.7, "LABW": LABW, "P1": 6.0, "P2": 6.4, "SP": 3.1, "GG": 0.9, "PAD": 8.4, "GAP": 12.0}
    g["Y1"], g["R1"] = 0.0, 7.0
    g["R1B"] = g["R1"] + 6 * g["P1"]
    # D296: b's spelled-out row labels just left of its tiles; B_X, b's left edge (its letter and longest label),
    # follows, and a's three facets take what is left. D297 (Valerio, 7 November, thread 1c64eb04, "can we shrink panel
    # a) enough to have panel b right most side align with the heatmap underneath?"): b's tiles end where d's bars end
    # (d's 100 tick, D_END below), no longer 0.2 mm inside the page, so a's facets narrow by the width of d's (n) column
    g["F_W"] = 34.0
    g["D_END"] = hs.PAGE_W_MM - 0.2 - max(tw("(n)"), tw("888")) - 1.2   # d's bars end here (x0 + w in _draw_5f)
    g["B_CW"], g["B_HEAD"] = 5.4, 19.4                 # b's tile width and the top of its tiles; 11 Nov (F3): 5.4 for
                                                       # 4.4, so neighbouring ranks "3.5" "3.5" stand 1.5 mm apart
    g["B_X1"] = g["D_END"] - 6 * g["B_CW"]
    g["B_X"] = round(g["B_X1"] - 0.8 - max(tw(s) for s, _ in SUBSETS), 1)
    g["B_TH"] = min(5.1, (g["R1B"] + g["PAD"] - 0.5 - g["B_HEAD"]) / 7)   # tiles end level with a's axis title
    g["A_X"], g["A_G"] = LABW + 1.8, 3.0              # 11 Nov (F3): a's gaps 3.0 for 3.6 and 4.0 for 6.0 before b,
    g["A_W"] = (g["B_X"] - 4.0 - g["A_X"] - 2 * g["A_G"]) / 3   # so b's wider tiles cost a's facets under 1 mm each
    g["Y2"] = g["R1B"] + g["GAP"] + 0.6
    g["R2"] = g["Y2"] + 8.4                            # c's rows, under its key and facet heads
    g["R2B"] = g["R2"] + 5 * g["P2"]
    g["DR"] = g["Y2"] + 4.4                            # d's rows, under its key line
    g["DRB"] = g["DR"] + 12 * g["SP"] + 5 * g["GG"]
    g["Y3"] = max(g["R2B"], g["DRB"]) + g["GAP"] + 0.6
    g["R3"] = g["Y3"] + 4.4
    g["R3B"] = g["R3"] + 12 * g["SP"] + 5 * g["GG"]
    g["H"] = round(g["R3B"] + g["PAD"], 1)         # the axis text ends inside the last 8.4 mm (finish_plate)
    # band 3: e (the evaluators, f until D298) across the page: its letter at the left edge, the names just right of
    # it, the two columns sharing what is left. Its last head and its axis text stay on the page.
    g["E_LET"], g["E_GAP"] = 0.0, 6.0
    g["E_LABR"] = g["E_LET"] + max(tw(r[0]) for r in S540.ROWS_5E) + 0.3
    g["E_X"] = g["E_LABR"] + 1.6
    g["E_CW"] = (hs.PAGE_W_MM - 0.2 - g["E_X"] - g["E_GAP"]) / 2
    if max(tw(h) for _, h in S540.JUDGE_SIGNALS) > g["E_CW"]:
        raise Refused("e: a column head is wider than its column")
    # band 2, right: d (faithfulness by verdict), its n column ending 0.2 mm inside the page (F_W set above, D297)
    g["F_LET"] = hs.PAGE_W_MM - 0.2 - (LABW + 3.2 + tw("judge pass") + 1.4 + g["F_W"] + 1.2
                                       + max(tw("(n)"), tw("888")))
    # band 2, left: c's three facets, a count printed right of a bar (up to two digits) ending 2 mm before d's letter
    g["D_X"], g["D_G"] = LABW + 1.8, 4.2
    g["D_W"] = (g["F_LET"] - 2.0 - C_OUT - tw("88") - g["D_X"] - 2 * g["D_G"]) / 3
    return g


# c's counts (11 Nov, F3): one prints inside its segment only with C_IN mm to spare (0.4 mm each side; 0.3 before, so
# "7" and "11" filled their segments edge to edge); a last segment's count too wide for it prints C_OUT mm right of the bar
# (0.5 before, so "5" sat against its thin segment); any other stays in the sheet and in methods_notes.
C_IN, C_OUT = 0.8, 1.0


def _row_labels(pl, x, ys, names):
    for y, name in zip(ys, names):
        pl.t(x, y, name, ha="right", va="center_baseline", why="strategy name")


def _draw_5a(pl, dat, g, sheet):
    LABW, P1, R1 = g["LABW"], g["P1"], g["R1"]
    x0, a_w, a_g = g["A_X"], g["A_W"], g["A_G"]
    xs = [x0 + j * (a_w + a_g) for j in range(3)]
    y_head = 2.9                                    # the column heads on the letter line (D295)
    pl.letter(0, 2.9, "a")
    _row_labels(pl, LABW, [R1 + (i + 0.5) * P1 for i in range(6)], [LABEL[c] for c in CONFIGS])
    heads = [(s, FN.PAPERS_PRECISION if s == FN.PAPERS else {FN.JUDGE: "Judge pass rate (%)",
                                                            FN.CONCEPTS: "Concept recall"}[s]) for s in FN.SIGNALS]
    cols = [c[0] for c in dat["a_specs"]]
    drs = {c[0]: c[-1] for c in dat["a_specs"]}
    for j, (x, (head, xlabel)) in enumerate(zip(xs, heads)):
        pl.t(x + a_w / 2, y_head, head, ha="center")
        col = cols[j]
        if col == "pass":
            lim = (-11.0, 113.0)
            ax = pl.ax(x, R1, a_w, 6 * P1, lim, (6 * P1, 0))
            ax.set_xticks([0, 50, 100], ["0", "50", "100"])
            mmx = a_w / (lim[1] - lim[0])
            for i, c in enumerate(CONFIGS):
                rb = (i + 1) * P1 - 0.25
                for v in sorted(dat["a_counts"][c]):
                    n = dat["a_counts"][c][v]
                    ncol = -(-n // 5)
                    sx, sy = [], []
                    for m in range(n):
                        cl, rw = divmod(m, 5)
                        sx.append(v + (cl - (ncol - 1) / 2) * 0.55 / mmx)
                        sy.append(rb - rw * 0.55)
                    ax.plot(sx, sy, ls="none", marker="o", ms=hs.DOT_MM / hs.MM_PT, mfc=hs.GREY["dot"], mec="none",
                            mew=0, clip_on=False, zorder=2)
                    row_i = len(sheet["rows"])
                    sheet["rows"].append([LABEL[c], col, "key", "questions at this value", None, v, None, None, None,
                                          None, None, n, dat["A"][col]["n"], drs[col]])
                    pl.t(x + (v - lim[0]) * mmx, R1 + rb - 3.15, str(n), ha="center",
                         printed={"sheet": f"Fig. {FIG_N}a", "row": row_i, "format": "{n_questions}"})
        else:
            ax = pl.ax(x, R1, a_w, 6 * P1, (-0.03, 1.03), (6, 0))
            ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
            for i, c in enumerate(CONFIGS):
                if dat["A"][col]["rows"][c]:                # empty only while Papers waits (blank_papers)
                    hs.boxplot(ax, i + 0.5, [v for _, v in dat["A"][col]["rows"][c]], whis="range", dot_mm=hs.DOT_MM)
        ax.set_xlabel(xlabel, labelpad=1.5)
    for col in cols:
        for c in CONFIGS:
            b = dat["box"][col][c]
            ref = "key" if col != "papers" else "papers"
            if b is None:
                sheet["rows"].append([LABEL[c], col, ref, PAPERS_WAITS] + [None] * 9 + [drs[col]])
                continue
            sheet["rows"].append([LABEL[c], col, ref, "summary", None, None, b["median"], b["q1"], b["q3"],
                                  b["whisker_low"], b["whisker_high"], b["n"], dat["A"][col]["n"], drs[col]])
            for q, v in dat["A"][col]["rows"][c]:
                sheet["rows"].append([LABEL[c], col, ref, "question", q, v, None, None, None, None, None, None, None,
                                      drs[col]])


def draw_verdict_papers(pl, dat, sheet, unprinted, *, let, x0, w, y0, r1, p1, line, letter, sheet_name):
    """Old Figure 5b (the draw-1 answers by the judge's verdict and Papers high or low), drawn since D295 as
    Supplementary Figure 12c by S543: the letter at (let, y0 + 2.9), the key on the three lines below it, the bars of
    the six strategies from r1 at pitch p1, between x0 and x0 + w. Fills sheet (columns VERDICT_COLS) as old 5b did."""
    tw = hs._text_width_mm
    P1, R1 = p1, r1
    waits = dat["B"][CONFIGS[0]][4] is None                  # Papers waits: the frame alone, its axis to the W questions
    xmax = (len(dat["qw"]) if waits else max(dat["B"][c][4] for c in CONFIGS)) + 2
    nx = x0 + w + 1.2
    bl = [y0 + 2.9, y0 + 2.9 + line, y0 + 2.9 + 2 * line]
    pl.letter(let, bl[0], letter)
    cw = max(tw("papers high"), tw("papers low")) + 0.6
    rh = let + 0.4 + max(tw("judge pass"), tw("judge fail"))
    cx = [rh + 1.0, rh + 1.0 + cw + 0.6]
    if cx[1] + cw >= nx - 0.5:
        raise Refused(f"the verdict panel's key ends at {cx[1] + cw:.2f}, over {nx - 0.5:.2f}")
    key = {("pass", "high"): "judge passes, papers high", ("pass", "low"): "judge passes, papers low",
           ("fail", "high"): "judge fails, papers high", ("fail", "low"): "judge fails, papers low"}
    for x, hl in zip(cx, ("high", "low")):
        pl.t(x + cw / 2, bl[0], f"papers {hl}", ha="center")
    sw = 3.0
    for yb, pf in zip(bl[1:], ("pass", "fail")):
        pl.t(rh, yb, f"judge {pf}", ha="right")
        for x, hl in zip(cx, ("high", "low")):
            pl.rect(x, yb - sw + 0.3, cw, sw, hs.colour("verdict", key[(pf, hl)]))
    order = [key[("fail", "high")], key[("pass", "high")], key[("fail", "low")], key[("pass", "low")]]
    colours = [hs.colour("verdict", n) for n in order]
    ax = pl.ax(x0, R1, w, 6 * P1, (0, xmax), (6, 0))
    ax.set_xticks([t for t in range(0, xmax + 1, 20)])
    ax.set_xlabel("Answers (n)", labelpad=1.5)
    mm = w / xmax
    pl.t(nx, bl[2], "(n)")
    for i, c in enumerate(CONFIGS):
        sheet["rows"].append([LABEL[c]] + list(dat["B"][c]) + [dat["b_median"]])
        if waits:
            continue
        y = i + 0.5
        yc = R1 + y * P1
        left = 0
        for k, (v, col) in enumerate(zip(dat["B"][c][:4], colours)):
            hs.bar(ax, y, [v], [col], start=left, slot=4.0 / P1 / hs.BAR_FRAC)
            s = str(v)
            if v and v * mm >= tw(s) + 0.6:
                pl.t(x0 + (left + v / 2) * mm, yc, s, ha="center", va="center_baseline", color=hs.ink_on(col),
                     printed={"sheet": sheet_name, "row": i, "format": "{" + B_KEYS[k] + "}"})
            elif v:
                unprinted.append((LABEL[c], B_KEYS[k], v))
            left += v
        pl.t(nx, yc, str(dat["B"][c][4]), va="center_baseline", printed={"sheet": sheet_name, "row": i, "format": "{n}"})


def _draw_5c(pl, dat, g, sheet):
    """Panel b since D295 (old c): each strategy's rank per signal and mix. D296: the left-out counts removed. D297:
    the tiles end where d's bars end (d200_layout's B_X1, D_END)."""
    x0, head, th, cw = g["B_X"], g["B_HEAD"], g["B_TH"], g["B_CW"]   # th: tiles end level with a's axis title
    x1 = g["B_X1"]
    pl.letter(x0, 2.9, "b")
    for j, c in enumerate(CONFIGS):
        pl.t(x1 + (j + 0.5) * cw, head - 0.9, LABEL[c], rotation=90, ha="center", va="bottom")
    nq = len(dat["qw"])
    for i, (sub, members) in enumerate(SUBSETS):
        y = head + i * th
        pl.t(x1 - 0.8, y + th / 2, sub, ha="right", va="center_baseline")
        for j, c in enumerate(CONFIGS):
            r = dat["ablation"]["ranks"][sub][c]
            row_i = len(sheet["rows"])
            if r is None:                                    # a subset holding Papers while Papers waits: a grey tile
                sheet["rows"].append(["rank", sub, " + ".join(SIG_NAME[m] for m in members), LABEL[c], None, None,
                                      nq, None, None])
                pl.rect(x1 + j * cw, y, cw, th, hs.GREY["band"], ec=hs.WHITE, lw=0.5)
                continue
            fc = hs.cividis_value(7 - r, 1, 6)
            sheet["rows"].append(["rank", sub, " + ".join(SIG_NAME[m] for m in members), LABEL[c], r, rank_text(r), nq,
                                  None, None])
            pl.rect(x1 + j * cw, y, cw, th, fc, ec=hs.WHITE, lw=0.5)
            pl.t(x1 + (j + 0.5) * cw, y + th / 2, rank_text(r), ha="center", va="center_baseline",
                 color=hs.ink_on(fc), printed={"sheet": f"Fig. {FIG_N}b", "row": row_i, "format": "{rank_text}"})
    kw = dat["ablation"].get("kendall")         # D309 N6 O1: not drawn; the SI's W and its exact P stand in this row
    sheet["rows"].append(["kendall_W", ", ".join(kw["signals"]) if kw else None, None,
                          f"{kw['strategies']} strategies" if kw else None, None, None, nq,
                          kw["W"] if kw else None, kw["exact_P"] if kw else None])


def _draw_5d(pl, dat, g, sheet, unprinted):
    """Old d with its counts printed (Valerio's note of 2 November): per signal, the questions where single pass or the
    strategy scores higher, and ties. A count goes in the middle of its segment. One too narrow for its segment prints
    just right of the bar if it is the last segment; any other stays in the sheet and in methods_notes."""
    tw = hs._text_width_mm
    LABW, P2, R2 = g["LABW"], g["P2"], g["R2"]
    x0, fw, fg = g["D_X"], g["D_W"], g["D_G"]
    bl = [g["Y2"] + 2.9, g["Y2"] + 2.9 + g["LINE"]]
    pl.letter(0, bl[0], "c")
    worse, tie, better = (hs.colour("comparison", k) for k in ("worse", "tie", "better"))
    hs.key(pl.fig, [("swatch", worse, "single pass higher"), ("swatch", tie, "tie"), ("swatch", better, "strategy higher")],
           centre_x=x0 + 1.5 * fw + fg, y=bl[0])
    _row_labels(pl, LABW, [R2 + (i + 0.5) * P2 for i in range(5)], [LABEL[c] for c in OTHERS])
    top_n = max(dat["D"][(o, s)]["n"] for o in OTHERS for s in SIGS if dat["D"][(o, s)]["n"] is not None)
    mm = fw / top_n
    axes = {}
    for j, s in enumerate(SIGS):
        x = x0 + j * (fw + fg)
        pl.t(x + fw / 2, bl[1], SIG_NAME[s], ha="center")
        axes[s] = pl.ax(x, R2, fw, 5 * P2, (0, top_n), (5, 0))
        axes[s].set_xticks([t for t in (0, 40, 80) if t <= top_n])
        if j == 1:
            axes[s].set_xlabel("Questions (n)", labelpad=1.5)
    segs = (("sp", "single_pass_higher", worse), ("tie", "tie", tie), ("ot", "strategy_higher", better))
    for i, o in enumerate(OTHERS):
        yc = R2 + (i + 0.5) * P2
        for j, s in enumerate(SIGS):
            m = dat["D"][(o, s)]
            x = x0 + j * (fw + fg)
            row_i = len(sheet["rows"])
            sheet["rows"].append([LABEL[o], FN.SINGLE_PASS, s, m["sp"], m["tie"], m["ot"], m["n"]])
            if m["n"] is None:                               # Papers waits (blank_papers): the facet's axis alone
                continue
            left = 0
            for key, col, fc in segs:
                v = m[key]
                hs.bar(axes[s], i + 0.5, [v], [fc], start=left, slot=4.4 / P2 / hs.BAR_FRAC)
                pr = {"sheet": f"Fig. {FIG_N}c", "row": row_i, "format": "{" + col + "}"}
                if v and v * mm >= tw(str(v)) + C_IN:
                    pl.t(x + (left + v / 2) * mm, yc, str(v), ha="center", va="center_baseline", color=hs.ink_on(fc),
                         printed=pr)
                elif v and key == "ot":
                    pl.t(x + m["n"] * mm + C_OUT, yc, str(v), va="center_baseline", printed=pr)
                elif v:
                    unprinted.append((LABEL[o], SIG_NAME[s], col, v))
                left += v


def _e_limits(rows):
    vals = [r[k] for r in rows for k in ("interval_lo", "interval_hi", "within_question_rho") if r[k] is not None]
    if not vals:
        return (-0.05, 1.05)
    return (min(0.0, min(vals)) - 0.05, max(1.0, max(vals)) + 0.05)


def _draw_5e(pl, dat, g, sheet):
    """Panel e since D298 (f from D295, e before): the evaluators against the judge, band 3 across the page."""
    y0 = g["Y3"]
    let, labr, x_c, cw, gap = g["E_LET"], g["E_LABR"], g["E_X"], g["E_CW"], g["E_GAP"]
    head_y = y0 + 2.9
    rtop = y0 + 4.7
    n = len(S540.ROWS_5E)
    pitch = (g["R3B"] - rtop) / n
    pl.letter(let, head_y, "e")
    rows = dat["e_rows"]
    lim = _e_limits(rows)
    for k, (_, head) in enumerate(S540.JUDGE_SIGNALS):
        x = x_c + k * (cw + gap)
        pl.t(x + cw / 2, head_y, head, ha="center")
        ax = pl.ax(x, rtop, cw, n * pitch, lim, (n, 0))
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        hs.reference_line(ax, 0)
        for i, (label, group, _) in enumerate(S540.ROWS_5E):
            r = rows[2 * i + k]
            if r["rho"] is not None:
                hs.boxplot(ax, i + 0.5, stats={"q1": r["resample_q25"], "median": r["resample_median"],
                                               "q3": r["resample_q75"], "whisker_low": r["interval_lo"],
                                               "whisker_high": r["interval_hi"]}, dots=False, zorder=3)
            if r["within_question_rho"] is not None:
                ax.plot([r["within_question_rho"]], [i + 0.5], ls="none", marker="o", ms=hs.MARK_MM / hs.MM_PT,
                        mfc=hs.WHITE, mec=hs.BLACK, mew=0.5, zorder=8, clip_on=False)
            if i and S540.ROWS_5E[i - 1][1] != group:
                ax.plot(lim, [i, i], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0, clip_on=False)
    for i, (label, group, _) in enumerate(S540.ROWS_5E):
        pl.t(labr, rtop + (i + 0.5) * pitch, label, ha="right", va="center_baseline", why="evaluator's name")
        if i and S540.ROWS_5E[i - 1][1] != group:
            yy = rtop + i * pitch
            pl.pg.plot([let, labr + 1.0], [yy, yy], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0,
                       solid_capstyle="butt", clip_on=False)
    y_ax = g["R3B"] + 7.0
    # fig5.md 5e Labels: the spec's words are wider than the two columns, so the text is centred on them unless that
    # would pass the page edge, then ends 0.2 mm inside it; the key moves left by as much as it needs to clear it
    ax_text = "Spearman's \u03c1 with the judge, per answer"
    ax_w = hs._text_width_mm(ax_text)
    ax_cx = min(x_c + cw + gap / 2, hs.PAGE_W_MM - 0.2 - ax_w / 2)
    pl.t(ax_cx, y_ax, ax_text, ha="center")
    key_item = ("open", (hs.BLACK, "o"), "within one question")
    key_w = hs._glyph_w("open") + 0.8 + hs._text_width_mm(key_item[2])
    key_cx = max(let + key_w / 2, min((let + labr) / 2, ax_cx - ax_w / 2 - 1.5 - key_w / 2))
    hs.key(pl.fig, [key_item], centre_x=key_cx, y=y_ax)
    for r in rows:
        sheet["rows"].append([r[k] for k in sheet["columns"]])


F_AXIS = "Share of each row's answers (%)"     # the row's answers of all three draws pooled; no mean is taken


def _draw_5f(pl, dat, g, sheet):
    """Panel d since D295 (old f): faithfulness of the answers the judge passes and fails, in band 2 right of c."""
    tw = hs._text_width_mm
    ox = g["F_LET"]
    LABW, SP, GG, R3, R3B = g["LABW"], g["SP"], g["GG"], g["DR"], g["DRB"]
    ly = g["Y2"] + 2.9
    sub_r = ox + LABW + 3.2 + tw("judge pass")
    x0, w = sub_r + 1.4, g["F_W"]
    nx = x0 + w + 1.2
    pl.letter(ox, ly, "d")
    cols = hs.cividis_levels(6)
    title = "Faithfulness score"
    total = tw(title) + 1.6 + sum(3.0 + tw(str(k)) + 1.8 for k in range(6)) - 1.8
    kx = (ox + 2.8 + x0 + w) / 2 - total / 2
    pl.t(kx, ly, title)
    kx += tw(title) + 1.6
    for k in range(6):
        pl.rect(kx, ly - 2.4 + 0.3, 2.6, 2.4, cols[k])
        pl.t(kx + 3.0, ly, str(k), why="faithfulness score of the swatch")
        kx += 3.0 + tw(str(k)) + 1.8
    if kx - 1.8 >= nx - 1.0:
        raise Refused(f"d's key ends at {kx - 1.8:.2f}, over the (n) head at {nx:.2f}")
    pl.t(nx, ly, "(n)")
    h = R3B - R3
    ax = pl.ax(x0, R3, w, h, (0, 100), (h, 0))
    ax.set_xticks([0, 50, 100], ["0", "50", "100"])
    ax.set_xlabel(F_AXIS, labelpad=1.5)
    for i, c in enumerate(CONFIGS):
        top = i * (2 * SP + GG)
        pl.t(ox + LABW, R3 + top + SP, LABEL[c], ha="right", va="center_baseline", why="strategy name")
        for j, word in enumerate(("pass", "fail")):
            y = top + (j + 0.5) * SP
            cnt, n = dat["F"][(c, word)]["counts"], dat["F"][(c, word)]["n"]
            left = 0.0
            for k in range(6):
                v = 100 * cnt[k] / n if n else 0
                if v > 0:
                    ax.barh([y], [v], left=[left], height=0.78 * SP, color=cols[k], lw=0, zorder=2)
                left += v
            row_i = len(sheet["rows"])
            sheet["rows"].append([LABEL[c], word] + cnt + [n] + [100 * x / n for x in cnt])
            pl.t(sub_r, R3 + y, f"judge {word}", ha="right", va="center_baseline")
            pl.t(nx, R3 + y, str(n), va="center_baseline", printed={"sheet": f"Fig. {FIG_N}d", "row": row_i, "format": "{n}"})


def draw_papers_by_faithfulness(pl, dat, g, sheet, *, let, y0, nx, letter, sheet_name):
    """Old Figure 6e (old 5g): Papers of the draw-1 answers at faithfulness 5 and below, drawn since D298 as
    Supplementary Figure 12d by S543: the letter and heads at (let, y0 + 2.9), the strategies' names right-aligned at
    let + LABW, twelve sub-rows from y0 + 4.4 at g's SP and GG, the n column from nx. Fills sheet (PAPERS_FAITH_COLS)."""
    tw = hs._text_width_mm
    LABW, SP, GG = g["LABW"], g["SP"], g["GG"]
    R3 = y0 + 4.4
    R3B = R3 + 12 * SP + 5 * GG
    ly = y0 + 2.9
    labr = let + LABW
    subr = labr + 1.6 + tw("0–4")
    x0 = subr + 1.4
    x1 = nx - 1.2
    pl.letter(let, ly, letter)
    pl.t(subr, ly, "Faithfulness", ha="right")
    pl.t(nx, ly, "(n)")
    h = R3B - R3
    ax = pl.ax(x0, R3, x1 - x0, h, (-0.02, 1.02), (h, 0))
    ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
    ax.set_xlabel(FN.PAPERS_PRECISION, labelpad=1.5)
    for i, c in enumerate(CONFIGS):
        pl.t(labr, R3 + i * (2 * SP + GG) + SP, LABEL[c], ha="right", va="center_baseline", why="strategy name")
        if not dat["G"]:                                     # Papers waits (blank_papers): the rows' names alone
            for j, grp in enumerate(("5", "0–4")):
                pl.t(subr, R3 + i * (2 * SP + GG) + (j + 0.5) * SP, grp, ha="right", va="center_baseline",
                     why="faithfulness score group")
                sheet["rows"].append([LABEL[c], "5" if j == 0 else "0 to 4", PAPERS_WAITS] + [None] * 8)
    for row in dat["G"]:
        i, j = CONFIGS.index(row["strategy"]), (0 if row["grp"] == "5" else 1)
        y = i * (2 * SP + GG) + (j + 0.5) * SP
        v = row["values"]
        b = hs.box_stats(v, "range") if len(v) >= 1 else None
        row_i = len(sheet["rows"])
        sheet["rows"].append([LABEL[row["strategy"]], row["grp"], "summary", None, None, len(v), b["q1"], b["median"],
                              b["q3"], b["whisker_low"], b["whisker_high"]])
        for q, x in zip(row["qids"], v):
            sheet["rows"].append([LABEL[row["strategy"]], row["grp"], "answer", q, x, None, None, None, None, None, None])
        if len(v) >= hs.SMALL_N:
            hs.boxplot(ax, y, v, slot=SP, whis="range", dot_mm=hs.DOT_MM)
        else:
            hs.strip(ax, y, v, slot=SP, size_mm=hs.DOT_MM, colour=hs.GREY["dot"])
            hs.summary_tick(ax, y, b["median"], slot=SP)
        pl.t(subr, R3 + y, "5" if row["grp"] == "5" else "0–4", ha="right", va="center_baseline",
             why="faithfulness score group")
        pl.t(nx, R3 + y, str(len(v)), va="center_baseline", printed={"sheet": sheet_name, "row": row_i, "format": "{n}"})


# D295: the sheets follow the new letters (old c is b, d is c, f is d, g is e, e is f); old b's columns are
# VERDICT_COLS, its sheet Supplementary Fig. 12c (S543). D298: old e's columns are PAPERS_FAITH_COLS, its sheet
# Supplementary Fig. 12d (S543); the evaluators' sheet is e (f before)
VERDICT_COLS = ["strategy"] + B_KEYS + ["papers_median_pooled"]
PAPERS_FAITH_COLS = ["strategy", "faithfulness", "row", "question_id", "papers_precision", "n", "quartile_25", "median",
                     "quartile_75", "whisker_low", "whisker_high"]
SHEET_COLS = {"a": ["strategy", "signal", "reference", "row", "question_id", "value", "median", "quartile_25",
                    "quartile_75", "whisker_low", "whisker_high", "n_questions", "n_questions_column", "draws"],
              "b": ["row_kind", "subset", "members", "strategy", "rank", "rank_text", "n_questions", "kendall_W",
                    "kendall_W_exact_P"],   # D296; D309 N6: one 'kendall_W' row after the rank rows
              "c": ["strategy", "reference", "signal", "single_pass_higher", "tie", "strategy_higher", "n_questions"],
              "d": ["strategy", "judge"] + [f"faithfulness_{k}" for k in range(6)] + ["n"]
                   + [f"share_pct_{k}" for k in range(6)],
              "e": ["row", "family", "judge_signal", "rho", "resample_q25", "resample_median", "resample_q75",
                    "interval_lo", "interval_hi", "within_question_rho", "answers", "questions", "source"]}
LETTERS = "abcde"


def build_d200(dat: dict) -> dict:
    """Draw Figure 5 of D200 in memory (fig5.md section 4). finish is the caller's: hs.check_figure_colours, then
    S457.finish_plate. Sheet Fig. 5f is written as build writes it, because S486 reads it."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    hs.apply_rc(SALT)
    hs.check_plate_kinds(PLATE_KINDS)
    g = d200_layout()
    if g["H"] > hs.PAGE_H_MAX_MM:
        raise Refused(f"Figure {FIG_N} is {g['H']} mm high, over {hs.PAGE_H_MAX_MM}")
    pl = Page(hs.PAGE_W_MM, g["H"])
    sheet = {k: {"columns": SHEET_COLS[k], "rows": []} for k in LETTERS}
    d_unprinted = []
    _draw_5a(pl, dat, g, sheet["a"])
    _draw_5c(pl, dat, g, sheet["b"])                 # D295: old c is b
    _draw_5d(pl, dat, g, sheet["c"], d_unprinted)    # old d is c
    _draw_5f(pl, dat, g, sheet["d"])                 # old f is d
    _draw_5e(pl, dat, g, sheet["e"])                 # old e is e (f from D295 to D298); old g is Supp. 19d
    bad = hs.check_figure_colours(pl.fig)
    if bad:
        raise Refused(f"Figure {FIG_N}: colours outside the house palette: {bad}")
    return {"PL": pl, "SHEET": sheet, "W": pl.w, "H": pl.h, "d_unprinted": d_unprinted, "layout": g}


def faith_left_out(dat: dict, R: dict) -> dict:
    """The answers d (and Supplementary Figure 12d, D298) leave out: no text, or a call with passages that ended in an
    error. Refuses unless every error is a request longer than the judge's context, the only cause the legends name."""
    f_no_text = sum(dat["f_out"][c]["no_answer"] for c in CONFIGS)
    f_errors = sum(dat["f_out"][c]["error"] for c in CONFIGS)
    f_ctx = sum(1 for (c, q, d), (st, _, m) in R["faith_rows"].items()
                if st == "error" and q in dat["qa"] and "exceeds the available context" in str(m))
    if f_ctx != f_errors:
        raise Refused(f"d: {f_errors} faithfulness errors, {f_ctx} of them longer than the judge's context; the legend "
                      "names only that cause; nothing written")
    f_drawn = sum(dat["F"][(c, w)]["n"] for c in CONFIGS for w in ("pass", "fail"))
    return {"no_text": f_no_text, "errors": f_errors, "ctx": f_ctx, "drawn": f_drawn}


def texts_d200(dat: dict, Z: dict, R: dict) -> dict:
    """Figure 5's legend (fig5.md section 4), every count from the data, and the Methods notes."""
    A, fn = dat["A"], R["fn"]
    qw, pts_b, table = dat["qw"], dat["pts_b"], dat["table"]
    n_e = len(table)
    waits = dat["papers_waits"]
    if waits:                         # every Papers count is [PENDING], as the letter marks what waits (D212 Q5)
        a_pn = f"n = {PENDING} answerable questions with a Papers score per box"
    else:
        # 8 Nov (Valerio, after editor row 45): a panel that draws derived statistics states its n once, as "n = X
        # <unit>", inside its own description. a's Papers boxes hold one draw-1 value per question, so the n of each
        # box is its questions with a Papers score (sheet Fig. 6a, n_questions), listed in the rows' order
        p_ns = [len(A["papers"]["rows"][c]) for c in CONFIGS]
        a_pn = (f"n = {p_ns[0]} answerable questions with a Papers score per box" if len(set(p_ns)) == 1 else
                "n = " + ", ".join(map(str, p_ns[:-1])) + f" and {p_ns[-1]} answerable questions with a Papers score, "
                "top to bottom")
    j_n = sorted({dat["D"][(o, s)]["n"] for o in OTHERS for s in ("judge", "concept")})
    if j_n != [len(qw)]:
        raise Refused(f"c's legend: Judge and Concepts n {j_n}, not the {len(qw)} W questions; nothing written")
    # d leaves out an answer whose call with passages is not ok: no text, or an error (fig5.md legend {k})
    fo = faith_left_out(dat, R)
    f_no_text, f_errors, f_ctx, f_drawn = fo["no_text"], fo["errors"], fo["ctx"], fo["drawn"]
    # 8 Nov (Valerio, 20:40Z and 20:45Z, editor row 45): no "n = " tag tacked on; a panel with derived statistics
    # (a's boxes, e's resampled boxes and interval) defines its n inside its own description, a panel without them
    # (b ranks, c counts, d shares) carries none; every panel is described in full, with no "as in a"
    n_q = A["pass"]["n"]
    c_ns = {len(A["concept"]["rows"][c]) for c in CONFIGS}
    if len(c_ns) != 1:
        raise Refused(f"a's legend gives one n per Concepts box, the boxes hold {sorted(c_ns)} questions; nothing written")
    c_conc = c_ns.pop()
    e_q = len({r["question_id"] for r in table})
    b_q = "the answerable questions" if len(qw) == n_q else f"the {len(qw)} questions every strategy has a value for"
    f_n = "" if dat["f_nq"] == n_q else f", on {dat['f_nq']} questions"
    LEGEND = (
        f"**Figure {FIG_N} | Three signals and other evaluators on the same answers.** "
        f"Answers of gemini-3-flash to the {n_q} answerable questions under six strategies. Judge, correctness score "
        f"against the key (pass, {PASS_T} or more of 5); Concepts, concept recall against the key; Papers, MiniCheck "
        "precision against the key's source papers. "
        "**a**, Each signal per strategy (rows). Judge: grey dots, questions, stacked at the share of three draws "
        "passed; numbers, questions per stack. Concepts: grey dots, each question's mean of three draws; box, "
        f"quartiles; line, median; whiskers, range; n = {c_conc} answerable questions per box. Papers: grey dots, "
        f"each question's draw-1 value; box, quartiles; line, median; whiskers, range; {a_pn}. "
        "**b**, Rank of each strategy (columns; 1, best) under each signal and mix of signals (rows), by its mean "
        f"over {b_q} (Judge, correctness score); a mix ranks by its members' mean rank. "
        "**c**, Each strategy (rows) against single pass per signal: questions where single pass scores higher "
        "(vermilion), ties (grey) or the strategy scores higher (blue), counted in the bars. Judge correctness score "
        "and Concepts, means of three draws; Papers, draw 1, questions with both scores. "
        "**d**, Faithfulness score (0 to 5) from the judge reading the retrieved passages, for each strategy's answers "
        f"the judge passes or fails, three draws pooled{f_n}: bars, share of the row's answers at each score; right, "
        "the row's answers. "
        "**e**, Spearman's \u03c1 of each evaluator (rows) with the judge's correctness (left) or faithfulness (right), "
        f"over the draw-1 answers both scored (at most {n_e}; each row's count in Source Data). Box, quartiles of "
        f"\u03c1 over 10,000 question resamples, n = {e_q} answerable questions; line, median; whiskers, two-sided "
        "95% percentile interval; open circle, \u03c1 within one question. "
        f"Second judge, {S540.SECOND_JUDGE}."
    )
    n_words = len(LEGEND.split())
    if n_words >= 350:
        raise Refused(f"the legend has {n_words} words, the journal's limit is under 350; nothing written")
    bert_rows = [r for r in R["l1"]["stages"]["overlap"].values() if r.get("group") == "answerable" and r.get("draw") == 1]
    bert_why = Counter((r.get("null_reasons") or {}).get("bertscore_f1", "no reason stored") for r in bert_rows
                       if (r.get("signals") or {}).get("bertscore_f1") is None)
    bert_null = sum(bert_why.values())
    bert_text = ", ".join(f"{n} {why}" for why, n in sorted(bert_why.items(), key=lambda x: (-x[1], x[0])))
    cd006 = sum(1 for r in table if r["question_id"] == "CD_006")
    note = R["l1"]["filter_note"]
    if waits:
        papers_how = (f"Papers {PAPERS_WAITS}: MiniCheck precision against the key's source papers, draw 1, over the "
                      "claims left after a Claimify-style selection drops each sentence with no verifiable claim "
                      "(S564, devstral at the lock's instrument settings). Until that run is frozen and read, no Papers "
                      f"value is drawn: the Papers parts of a, b, c and e are empty, their Source Data "
                      f"cells blank. L1's papers stage holds {note['rows_read']} rows, {note['rows_with_a_value']} with "
                      "a stored value; the W questions are those whose six draw-1 answers have a papers row, which "
                      "does not depend on its value. MiniCheck ")
    elif "selection" in note:
        sn = note["selection"]
        nv = sn["no_verdict_sentences_by_status"]
        papers_how = (
            "Papers is MiniCheck precision against the key's source papers, draw 1, over the sentences MiniCheck scored "
            "that a Claimify-style selection keeps (D208; Metropolitansky and Larson 2025, arXiv 2502.10855, Selection "
            "stage): S564 asked devstral-small-2:24b, at the lock's instrument settings, whether each sentence holds a "
            "specific and verifiable proposition, and a sentence S564 judged leaves Papers only on \"does not contain\"; a partial "
            "verdict keeps the original sentence, which MiniCheck scored. scripts/minicheck_filter.py then leaves out "
            "a sentence matching its source-list pattern; no heading filter is applied (D245). S564 run "
            f"{sn['s564_run_sha256'][:12]}: {sn['sentences_read']:,} sentences of the answers read, "
            f"{sn['sentences_selected']:,} selected. S564 gave no verdict on "
            + ", ".join(f"{v} sentence{'s' * (v != 1)} ({k})" for k, v in sorted(nv.items()))
            + f" in {sn['no_verdict_answers']} answers; these are {sn['no_verdict_reading']}, as S564 records them. "
            + (f"{sum(sn['answers_not_judged_by_group'].values())} answers with a stored value were not among the "
               f"answers S564 judged ({', '.join(f'{v} {k}' for k, v in sorted(sn['answers_not_judged_by_group'].items()))}) "
               "and have no Papers value. " if sn["answers_not_judged_by_group"] else "")
            + (f"{(nn := sum(sn['answers_none_selected_by_group'].values()))} answer{'s' * (nn != 1)} "
               f"ha{'ve' if nn != 1 else 's'} no sentence left and no Papers value. "
               if sn["answers_none_selected_by_group"] else "")
            + f"Of {note['rows_with_a_value']} rows with a stored value, {note['values_changed']} changed. MiniCheck ")
    else:
        rule_doc = (getattr(MF.HEADING_RULE, "__doc__", None) or "the rule set in scripts/minicheck_filter.py").strip()
        papers_how = ("Papers is MiniCheck precision against the key's source papers, draw 1, recomputed by "
                      + ("scripts/minicheck_filter.py for every strategy: a claim matching its source-list pattern is left "
                         "out; no heading filter is applied (D245). " if MF.HEADING_RULE is getattr(MF, "no_heading", None) else
                         "scripts/minicheck_filter.py for every strategy: a claim matching its source-list pattern or its "
                         f"heading rule is left out ({rule_doc}). ") + f"Of {note['rows_with_a_value']} rows with a value, "
                      f"{note['values_changed']} changed and {note['values_now_null']} have no claim left. MiniCheck ")
    METHODS = [
        ("all panels", "Concept recall is D181's reading (D186 (4); findings/recompute/L3_d181). Judge rows are read "
                       "through scripts/judge_rows_v25.py: a key v2.5 row where one exists, else key v2.4. "
                       + papers_how +
                       "checks only the key's source papers (S470_l1_signals.py, papers stage), so a claim taken correctly "
                       "from another paper of the corpus counts as unsupported; how often that happens (review finding S12) is "
                       "not stated here, because it comes from the review's work script "
                       "findings/recompute/findings_review_2026-10-30/scripts/out/D03_work/a14.py, which no step of this "
                       "build runs. The judge's prompt holds the expert answer and the expected concepts "
                       "(experiments/scorers/judge_passages.py:8-11), and the judge was chosen partly for following "
                       "concept recall, so part of the agreement between Judge and Concepts is built in (review finding O12)."),
        ("a", "Judge: per question the share of three draws at 4 or more, one grey dot per question, stacked five high. "
              "Concepts, mean of three draws; Papers, draw 1. Quartiles by numpy percentile (linear); whiskers to the "
              "smallest and largest value (hs.box_stats, whis range)."),
        ("b", "Each signal's rank is rankdata of minus its six means on the W questions (S473.compute; S06_metric_ablation"
              ".py:95-98), 1 best, ties sharing the average rank. A mix's rank is rankdata of the mean of its members' "
              "ranks. The Judge value here is mean correctness 0 to 5 over three draws, not a's pass rate."
              + (f" Papers {PAPERS_WAITS}: the four rows holding Papers are grey tiles with no rank." if waits else "")),
        ("c", "Per W question where both values exist: judge correctness (0 to 5, not a's pass mark) and concept recall "
              "averaged over three draws, Papers draw 1. A strictly higher value wins; equal within 1e-9 is a tie. A count "
              "too narrow for its segment prints just right of the bar if it is the last segment; any other is not "
              "printed and stays in the sheet: " + (", ".join(f"{o_} {s_} {k_.replace('_', ' ')} {v_}"
                                                              for o_, s_, k_, v_ in Z["d_unprinted"]) or "none") + "."
              + (f" Papers {PAPERS_WAITS}: W is the {len(qw)} questions whose six draw-1 answers have a papers row, so "
                 "the Judge and Concepts counts are provisional on W. The D166 plate's W, which also needed a Papers value, "
                 "was smaller; when S564's Papers is read, W can shrink and these counts change." if waits else "")),
        ("d", "Faithfulness from the judge's call with passages; pass = correctness of the plain call at 4 or more. Each "
              "row pools the answers of all three draws (no mean is taken): its bar shows what share of those answers "
              f"scored 0 to 5, and n at right counts them. Of the {f_drawn + f_errors + f_no_text:,} answers of the "
              f"{dat['f_nq']} questions, {f_drawn:,} are drawn: {f_errors} calls with passages ended in an error, every "
              "one a request longer than the judge's context, which the lock never cuts (LOCK.toml truncate = false), "
              f"and {f_no_text} answers have no text. Calls longer than the judge's context are refused ({f_ctx}). "
              "Supplementary Figure 12d leaves out the same answers."),
        ("e", "All pairs where both values exist, draw 1. Column 1: judge correctness, plain call. Column 2: judge "
              "faithfulness, call with passages. RAGAS rows of status ok or ok_with_nulls, RAGChecker rows of status ok. "
              "Simple scores from L1's overlap stage. Box: quartiles of the 10,000 question resamples, not of the data. "
              "Open mark: within one question each signal is ranked, centred, and Pearson's r taken over all pairs. "
              "RAGAS and RAGChecker have no comparison with a person, because the rated answers keep no passages; "
              "Supplementary Figure 3 sets simple evaluators against a person. "
              f"BERTScore is left out (FF19 a): {bert_null} of {len(bert_rows)} draw-1 answerable answers have no value "
              f"({bert_text}). K1's and L1's key and overlap stages ran on key v2.4: the {cd006} answers to CD_006, whose "
              "expected answer key v2.5 changed, stay in as scored (fig5.md Q2's default)."),
    ]
    return {"legend": LEGEND, "words": n_words, "methods": METHODS}


def caption_d200(stamp: str) -> str:
    return (
        f"# Source Data Fig. {FIG_N}, caption\n\n**Source Data Fig. {FIG_N} | Numerical values plotted in Figure {FIG_N}.** "
        f"Data stamp: {stamp}. One sheet per panel. "
        f"Fig. {FIG_N}a: per strategy and signal a summary row (median, quartiles, whisker ends at the range, questions), one "
        f"row per plotted question, and for the Judge the questions at each pass rate. Fig. {FIG_N}b: each strategy's "
        f"rank under each signal and mix of signals, then one 'kendall_W' row, not drawn: Kendall's W of the three "
        "single signals' ranks of the six strategies (tie-corrected) and its exact P, the share of all 518,400 orderings "
        f"of the second and third signals' ranks whose W is at least as large. Fig. {FIG_N}c: per "
        "strategy against single pass and signal, the questions where single pass scores higher, the ties, the questions "
        f"where the strategy scores higher and the questions compared. Fig. {FIG_N}d: per strategy and judge verdict the "
        f"answers of the three draws pooled at each faithfulness score and their share of that row. Fig. {FIG_N}e: per "
        "evaluator and judge signal rho, the quartiles and 2.5th and 97.5th percentiles of its 10,000 question resamples, "
        f"the within-question rho and the pairs used. Generated by `uv run --frozen python {SCRIPT} figure` from the frozen sets "
        f"findings/recompute/{D200_SET}_inputs, findings/recompute/{S6_SET}_inputs and findings/recompute/fig2_inputs, "
        "with concept recall from findings/recompute/L3_d181.\n\n"
        f"Proposed Data Availability sentence: \"The source data for Figure {FIG_N} is in Supplementary Data {FIG_N + 1}.\"\n")   # D303 (D302)


def d200_read(R: dict, srcs: dict, d200: dict, tmp: Path) -> dict:
    """The D200 data, after the locked plate is held to anchor_d166: the judge rows through judge_rows_v25 with the
    frozen S6 rows, D181's concept recall, L1's final rows (R2), the claim filter, K1's final rows (R1), compute, and
    Figure 3's pass rates (check 3). Returns the new R."""
    R = with_judge_rows(R, {**srcs, "s6": d200["s6"]})
    rep = R["rep"]
    l3d = read_l3_d181(R["groups"], R["l3"])
    rep.append(l3d["reproduced"])
    l1 = S473.read_l1(d200["l1"], R["l3"]["header"], R["groups"])
    S473.check_same_answers(l1, R["l3"])
    got = {k: len(v) for k, v in l1["stages"].items()}
    if L1_PLANNED and got != L1_PLANNED:
        raise Refused(f"L1's final rows: {got}, planned {L1_PLANNED}; nothing written")
    if papers_waits():
        # S473.compute needs a Papers value on every row it reads, so it runs on L1's stored precision; panel_data_d200
        # then removes every Papers value (blank_papers) and write_d200 refuses if one reaches a sheet
        vals = [(r.get("signals") or {}).get("precision") for r in l1["stages"]["papers"].values()]
        l1f = {**l1, "dir": d200["l1"], "filter_note": {
            "papers": PAPERS_WAITS, "rows_read": len(vals), "rows_with_a_value": sum(v is not None for v in vals)}}
        rep.append(f"L1 rows {got}; Papers {PAPERS_WAITS}: no Papers value is drawn or written")
    else:
        sel = read_selection() if PAPERS_SELECTION is not None else None
        if sel is not None:
            rep.append(f"S564's selection read whole: {len(sel['rows']):,} sentences under run "
                       f"{sel['run_sha256'][:12]}, status {sel['status']}; each shard's tally equals its summary.json")
        l1f = apply_claim_filter(l1, tmp, selection=sel)
        rep.append(f"L1 rows {got}; the claim filter on {l1f['filter_note']}")
    k1 = S540.read_k1_final(d200["k1"])
    rep.append(f"K1's final rows {({t: len(v) for t, v in k1['rows'].items()})}, chain head {k1['head'][:12]}, "
               f"{len(k1['replaced']['ragas'])} rows replaced from {S540.Q7_WORKER}; "
               f"{len(k1['length_done'])} RAGChecker answers failed twice by a length stop, done under D110 "
               f"({', '.join('|'.join(map(str, a[:2])) for a in k1['length_done'])})")
    fn = S473.compute(R["read"], l3d, l1f, R["faith_rows"], R["groups"])
    rep.append(S473.check_fig2(S473.build_sheets(fn, ""), sha256_file(srcs["collect"]), at=None))    # D201 Q2: on v2.5
    return {**R, "l3": l3d, "l1": l1f, "l1_dir": l1f["dir"], "k1": k1, "fn": fn}


def d200_data(tmp: Path, set_dir=None) -> tuple:
    """For S542, S543 and S544, so their numbers have one source: read_and_compute with its checks, then d200_read and
    panel_data_d200. It does not draw the locked plate again: S497 `figure` holds that to anchor_d166. With the rule
    unset this exits as minicheck_filter does; with the set absent it refuses."""
    MF._need_rule()
    if not (set_dir or D200_DIR.exists()):
        raise Refused(f"findings/recompute/{D200_SET}_inputs is not frozen; nothing written")
    srcs = frozen_sources(Path(tmp))
    R = read_and_compute(srcs)
    R["l1_dir"] = srcs["l1"]
    d200 = d200_sources(set_dir)
    R = d200_read(R, srcs, d200, Path(tmp))
    return R, panel_data_d200(R), srcs, d200


def write_d200(out: Path, R: dict, srcs: dict, d200: dict, dat: dict, Z: dict, T: dict, pull_log: dict, rep: list) -> None:
    """Every output of the D200 plate into a staging folder, then moved over the earlier Figure 5 files."""
    fn, read = R["fn"], R["read"]
    waits = dat["papers_waits"]
    have, n4, planned = fn["have"], (0 if waits else fn["all4"]), S473.PLANNED
    when = (read["side"].get("_provenance") or {}).get("at")
    when = collect_utc(when, pull_log) if when else None
    papers_stamp = (f"Papers 0 of {planned['papers']:,} ({PAPERS_WAITS}; L1's papers stage {have['papers']:,} rows)"
                    if waits else f"MiniCheck against the papers {have['papers']:,} of {planned['papers']:,} (draw 1, "
                                  + ("S564's selection D208 and the claim filter D172)"
                                     if "selection" in R["l1"]["filter_note"] else "claim filter D172)"))
    stamp = (f"{n4} of {planned['papers']} draw-1 answerable answers have a final row from all four "
             f"scorers; judge plain call {have['judge']:,} of {planned['judge']:,}, concept recall "
             f"{have['concept']:,} of {planned['concept']:,} (D181's reading, L3_d181), {papers_stamp}, judge with passages "
             f"{have['faith']:,} of {planned['faith']:,}; RAGAS {len(R['k1']['rows']['ragas'])} and RAGChecker "
             f"{len(R['k1']['rows']['ragchecker'])} rows (K1); the Second judge row of panel e from S518's {S540.SECOND_JUDGE} rows (D267); S3 collect "
             f"{when}, run_sha256 {str(read['run_sha256'])[:12]}")
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    plate, sd = f"Figure {FIG_N}{tag}", f"Source Data Fig. {FIG_N}{tag}"
    sheets = {f"Fig. {FIG_N}{k}": Z["SHEET"][k] for k in LETTERS}
    PL = Z["PL"]
    if waits:
        left = papers_left(sheets)
        if left:
            raise Refused(f"Papers waits, yet {len(left)} Source Data cells hold a Papers value, first {left[:3]}; "
                          "nothing written")
    stage = out.with_name(out.name + ".staging")
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    try:
        paths = {k: stage / f"{plate}.{k}" for k in ("pdf", "svg", "png")}
        S457.finish_plate(PL.fig, Z["W"], Z["H"], paths, title=f"Figure {FIG_N}")
        FR.check_pdf_deterministic(paths["pdf"])
        FR.check_svg_deterministic(paths["svg"])
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for name, sh in sheets.items():
            ws = wb.create_sheet(name)
            ws.append(sh["columns"])
            for r in sh["rows"]:
                if len(r) != len(sh["columns"]):
                    raise Refused(f"{name}: a row of {len(r)} cells under {len(sh['columns'])} columns")
                ws.append(r)
        wb.save(stage / f"{sd}.xlsx")
        FR.deterministic_xlsx(stage / f"{sd}.xlsx")
        (stage / f"Source Data Fig. {FIG_N} caption{tag}.md").write_text(caption_d200(stamp))
        (stage / f"figure{FIG_N}_numbers.json").write_text(json.dumps(
            {"stamp": stamp, "what": f"Figure {FIG_N} (D200), Source Data values and printed numbers (S448 R8 compares the "
                                     "workbook with this file)",
             "sheets": sheets, "printed": PL.printed, "kendall": dat["ablation"].get("kendall")}, indent=1,
            default=float) + "\n")
        (stage / "legend_draft.md").write_text(
            f"# Figure {FIG_N}, title and legend (draft)\n\n"
            f"Written by `{SCRIPT} figure`.\n\n" + T["legend"] + "\n")
        (stage / "methods_notes.md").write_text(
            f"# Figure {FIG_N}, notes for the Methods\n\nDetail that left the legend to keep it under 350 words. Written by "
            f"`{SCRIPT} figure`.\n\n" + "\n".join(f"- **{k}**: {v}" for k, v in T["methods"]) + "\n")
        if CLAIMS_OUT is None:          # D2: the claims list is the editorial step's (S616 claims)
            pass
        elif waits:                     # every claim of S473.CLAIMS reads Papers (W, the three-signal rho, e)
            write_claims(
                f"# Figure {FIG_N}: claims list (D82)\n\nWritten by `{SCRIPT} figure` with the plate it sits beside. Data "
                f"stamp: {stamp}.\n\nNo claim is computed: Papers {PAPERS_WAITS}, and every row of S473's claims list "
                "(S473.CLAIMS) reads it.\n")
        else:
            write_claims(S473.claims_md(fn, stamp).replace(
                "Written by `scripts/S473_fig5_panels.py figure` with the plate it sits beside.",
                f"Written by `{SCRIPT} figure` with the plate it sits beside, through S473's claims list (S473.CLAIMS)."))
        c_state = ({"means": dat["cc"]["means"], "papers": PAPERS_WAITS} if waits else
                   {k: v for k, v in fn["c"].items() if k != "questions"})
        e_state = ({"papers": PAPERS_WAITS} if waits else {k: v for k, v in fn["e"].items() if k != "points"})
        state = {"stamp": stamp, "planned": planned, "have": have, "answers_with_all_four": n4,
                 "judge_key": "v2.5",                 # D201 Q2: S486 holds this plate on key v2.5 rows
                 "W_questions": dat["qw"], "W_partial_blocks_left_out": fn["c"]["partial_blocks_left_out"],
                 "c": c_state, "e": e_state, "d_all": fn["d_all"], "papers_waits": PAPERS_WAITS if waits else None,
                 "ablation": dat["ablation"], "k1_length_done": R["k1"].get("length_done"),
                 "d_status": {c: fn["d"][c]["status"] for c in CONFIGS}, "plate_mm": [Z["W"], Z["H"]],
                 "layout": {k: round(v, 3) for k, v in Z["layout"].items()}, "legend_words": T["words"],
                 "c_unprinted": Z["d_unprinted"], "d_left_out": dat["f_out"],
                 "claim_filter": R["l1"]["filter_note"], "k1_status": S540.row_groups(R["k1"]),
                 "k1_replaced": R["k1"]["replaced"], "judge_rows": R["judge_rows"]}
        (stage / "fig5_data_state.json").write_text(json.dumps(state, indent=1, default=float) + "\n")
        files = {p.name: sha256_file(p) for p in sorted(stage.iterdir()) if p.name != f"figure{FIG_N}_provenance.json"}
        (stage / f"figure{FIG_N}_provenance.json").write_text(json.dumps({
            "provenance": {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT),
                           "imports_sha256": {m: sha256_file(ROOT / "scripts" / m) for m in (
                               "S473_fig5_panels.py", "S457_fig2_panels.py", "S463_fig2_ranking.py", "fig_repro.py",
                               "judge_rows_v25.py", "house_style.py", "figure_names.py", "minicheck_filter.py",
                               "S540_fig5_evaluators.py", "S564_claimify_selection.py", "pdf_font_determinism.py")},
                           "reads_sha256": {x: sha256_file(ROOT / x) for x in (
                               "experiments/scorers/assignment.py", "findings/recompute/master_join.csv",
                               "findings/recompute/S06_metric_ablation.json")},
                           "command": f"uv run --frozen python {SCRIPT} figure",
                           "design": "D200 on D166's bands (build spec fig5.md section 4), with Valerio's notes of 2 "
                                     "November on the bands and on panels d and f"},
            "stamp": stamp, "reproduced": rep, "page_mm": [Z["W"], Z["H"]],
            "concept_reading": READINGS["D181"], "judge_rows": R["judge_rows"],
            "anchor": {"compared": bool(srcs["anchor_applies"]), "why": srcs["anchor_applies"],
                       "files": {n: sha256_file(p) for n, p in srcs["anchor"].items()}},
            "second_judge": {"decision": S540.SECOND_DECISION, "model": S540.SECOND_JUDGE, **dat["second_judge"]},
            "inputs_sha256": dict(sorted({**srcs["sha"], **d200["sha"]}.items())), "inputs_checked": srcs["checked"],
            "d200_set_pinned": d200["pinned"],
            "lock": {"path": "experiments/LOCK.toml", "sha256": sha256_file(S463.LOCK_TOML)},
            "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha256_file(S457.FIGURE_LOCK),
                            "status": S457.FLOCK.get("status")},
            "files": files}, indent=1, default=str) + "\n")
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    out.mkdir(parents=True, exist_ok=True)
    for pat in OWNED:
        for p in out.glob(pat):
            p.unlink()
    for p in stage.iterdir():
        shutil.move(str(p), out / p.name)
    stage.rmdir()
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {plate}; {stamp}")


# ---------------------------------------------------------------------------------------------------------------
# figure
# ---------------------------------------------------------------------------------------------------------------
def figure(args):
    with tempfile.TemporaryDirectory(prefix="S497_views_") as tmp:
        return _figure(args, Path(tmp))


def _figure(args, tmp: Path):
    out = Path(args.out).resolve() if args.out else OUT
    S457.figure_lock_agreed()
    try:
        srcs = pull_sources(Path(args.src).expanduser().resolve(), tmp) if args.src else frozen_sources(tmp)
    except FR.FrozenInputError as e:
        raise Refused(f"frozen input: {e}") from None
    if getattr(args, "s6", None):
        srcs["s6"] = Path(args.s6).expanduser().resolve()
    elif not args.src:                  # D203 (2 Nov): every figure on key v2.5; the frozen S6 rows Figure 3 reads
        try:
            srcs["s6"] = FR.frozen(S6_SET)
        except FR.FrozenInputError as e:
            raise Refused(f"frozen input: {e}") from None
    R = read_and_compute(srcs)
    R["l1_dir"] = srcs["l1"]
    rep = R["rep"]
    dat0 = panel_data(R)                                 # L3's loose reading: the locked plate's
    anchor_numbers = json.loads(srcs["anchor"]["numbers.json"].read_text())
    anchor_numbers["_legend"] = srcs["anchor"]["legend.md"].read_text().rstrip("\n")
    anchor_f5 = json.loads(srcs["anchor"]["figure5_numbers.json"].read_text())
    if srcs["anchor_applies"]:
        rep.append(compare_anchor_data(dat0, anchor_numbers))
    pull_log = json.loads(srcs["pull"].read_text())
    R["pull_ended"] = pull_log["ended_utc"]
    # 4 after drawing, on the loose reading: the locked plate drawn again into a temporary folder, every drawn number,
    # sheet, printed number, the legend and the PNG held to anchor_d166 before the D181 reading is read (D186 (4))
    sheets0 = None
    if srcs["anchor_applies"]:
        Z0 = build(dat0)
        T0 = texts(dat0, Z0, R, "loose")
        sheets0 = {f"Fig. 5{k}": Z0["SHEET"][k] for k in "abcdefg"}
        rep.append(compare_anchor_drawn(Z0["DRAWN"], sheets0, Z0["PL"].printed, T0["legend"], anchor_numbers,
                                        anchor_f5))
        p0 = {k: tmp / f"locked_plate.{k}" for k in ("pdf", "svg", "png")}
        S457.finish_plate(Z0["PL"].fig, Z0["W"], Z0["H"], p0, title="Figure 5")
        rep.append("the locked plate, drawn again on L3's loose reading in a temporary folder: "
                   + png_equal(p0["png"], srcs["anchor"][ANCHOR_PNG]))
    # D200: built only when its rule and its frozen set both exist, and only after every comparison above was made
    d200_set = getattr(args, "d200_set", None)            # a test's folder; `figure` on the command line has no such option
    waits = d200_waits(srcs["anchor_applies"], d200_set)
    if not waits:
        d200 = d200_sources(d200_set)
        if getattr(args, "s6", None):
            rep.append(f"--s6 not used: the D200 plate reads the S6 rows of {S6_SET}_inputs")
            print(rep[-1])
        R = d200_read(R, srcs, d200, tmp)
        dat = panel_data_d200(R)
        R["rep"] += [dat["rho_gate"], check_ablation_s06()]
        Z = build_d200(dat)
        T = texts_d200(dat, Z, R)
        write_d200(out, R, srcs, d200, dat, Z, T, pull_log, R["rep"])
        print("\n".join(["reproduced:"] + [f"  {x}" for x in R["rep"]]))
        return
    print("D200 plate waits: " + "; ".join(waits) + ". This run goes on to the plate of D166 and D186.")
    # D186 (3), after the locked plate was reproduced on key v2.4: the judge rows through judge_rows_v25
    R = with_judge_rows(R, srcs)
    rep = R["rep"]
    # D186 (4): concept recall on D181's reading (L3_d181), checked against L3 (read_l3_d181), then every panel again
    l3d = read_l3_d181(R["groups"], R["l3"])
    rep.append(l3d["reproduced"])
    fn = S473.compute(R["read"], l3d, R["l1"], R["faith_rows"], R["groups"])
    R = {**R, "l3": l3d, "fn": fn}
    read = R["read"]
    # 3: Figure 2's pass rates from the same collect and judge rows, through S473's own sheet a (judge values only)
    # D203: on the S6 rows, held to Figure 3's current files (key v2.5); without them to Figure 3 at FIG3_V24_AT
    rep.append(S473.check_fig2(S473.build_sheets(fn, ""), sha256_file(srcs["collect"]),
                               at=None if srcs.get("s6") else S473.FIG3_V24_AT))
    dat = panel_data(R)
    have, n4, planned = fn["have"], fn["all4"], S473.PLANNED
    when = (read["side"].get("_provenance") or {}).get("at")
    if when:
        when = collect_utc(when, pull_log)
    stamp = (f"{n4} of {planned['papers']} draw-1 answerable answers have a final row from all four "
             f"scorers; judge plain call {have['judge']:,} of {planned['judge']:,}, concept recall "
             f"{have['concept']:,} of {planned['concept']:,} (D181's reading, L3_d181), MiniCheck against the papers "
             f"{have['papers']:,} of {planned['papers']:,} (draw 1), judge with passages {have['faith']:,} of "
             f"{planned['faith']:,}; read {pull_log['ended_utc']} (S3 collect {when}, run_sha256 "
             f"{str(read['run_sha256'])[:12]})")
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    plate, sd = f"Figure 5{tag}", f"Source Data Fig. 5{tag}"
    Z = build(dat, g_whiskers=True, a_range=True)
    T = texts(dat, Z, R, "D181")
    SHEETS = {f"Fig. 5{k}": Z["SHEET"][k] for k in "abcdefg"}
    PL, DRAWN = Z["PL"], Z["DRAWN"]
    changed = None if sheets0 is None else changed_cells(sheets0, SHEETS)
    stage = out.with_name(out.name + ".staging")
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    try:
        paths = {k: stage / f"{plate}.{k}" for k in ("pdf", "svg", "png")}
        S457.finish_plate(PL.fig, Z["W"], Z["H"], paths, title="Figure 5")
        FR.check_pdf_deterministic(paths["pdf"])                 # D155: no write time in the PDF or the SVG
        FR.check_svg_deterministic(paths["svg"])
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for name, sh in SHEETS.items():
            ws = wb.create_sheet(name)
            ws.append(sh["columns"])
            for r in sh["rows"]:
                if len(r) != len(sh["columns"]):
                    raise Refused(f"{name}: a row of {len(r)} cells under {len(sh['columns'])} columns")
                ws.append(r)
        wb.save(stage / f"{sd}.xlsx")
        FR.deterministic_xlsx(stage / f"{sd}.xlsx")              # D155: openpyxl's write times removed
        (stage / f"Source Data Fig. 5 caption{tag}.md").write_text(caption_text(stamp, "D181"))
        (stage / "figure5_numbers.json").write_text(json.dumps(
            {"stamp": stamp, "what": "Figure 5 (D166), Source Data values and printed numbers (S448 R8 compares the "
                                     "workbook with this file)",
             "sheets": SHEETS, "printed": PL.printed}, indent=1, default=float) + "\n")
        (stage / "legend_draft.md").write_text(
            "# Figure 5, title and legend (draft)\n\n"
            f"Written by `{SCRIPT} figure` (the legend D166 locked; since D186 (4) with c's RLM fails counted from the "
            f"data).\n\n" + T["legend"] + "\n")
        (stage / "methods_notes.md").write_text(
            "# Figure 5, notes for the Methods\n\nDetail that left the legend to keep it under 350 words. Written by "
            f"`{SCRIPT} figure`.\n\n" + "\n".join(f"- **{k}**: {v}" for k, v in T["methods"]) + "\n")
        if CLAIMS_OUT is not None:      # D2: the editorial step only
            write_claims(S473.claims_md(fn, stamp).replace(
                "Written by `scripts/S473_fig5_panels.py figure` with the plate it sits beside.",
                f"Written by `{SCRIPT} figure` with the plate it sits beside, through S473's claims list (S473.CLAIMS)."))
        g = Z
        state = {"stamp": stamp, "planned": planned, "have": have, "answers_with_all_four": n4,
                 "W_questions": dat["qw"], "W_partial_blocks_left_out": fn["c"]["partial_blocks_left_out"],
                 "c": {k: v for k, v in fn["c"].items() if k != "questions"},
                 "e": {k: v for k, v in fn["e"].items() if k != "points"}, "d_all": fn["d_all"],
                 "d_status": {c: fn["d"][c]["status"] for c in CONFIGS},
                 "panels": DRAWN, "plate_mm": [g["W"], g["H"]], "layout_chosen": "A", "layout_plan": g["LAYOUTS"],
                 "geometry_mm": {"label_column_right": round(g["LABR"], 2), "band1": [g["Y1"], g["R1"], g["R1B"]],
                                 "band2": [g["Y2"], g["R2"], g["R2B"]], "band3": [g["Y3"], g["R3"], g["R3B"]],
                                 "a_columns_x": [round(x, 2) for x in g["A_XS"]], "a_column_w": g["A_W"],
                                 "b_bars_x": [round(g["B_X0"], 2), round(g["B_X1"], 2)],
                                 "c_bars_x": [round(g["C_X0"], 2), round(g["C_X1"], 2)],
                                 "d_facets_x": [round(x, 2) for x in g["D_XS"]], "d_facet_w": g["D_W"],
                                 "e_names_right": round(g["E_LABR"], 2),
                                 "e_plot_x": [round(g["E_X0"], 2), round(g["E_X1"], 2)],
                                 "f_bars_x": [round(g["F_X0"], 2), round(g["F_X1"], 2)],
                                 "g_plot_x": [round(g["G_X0"], 2), round(g["G_X1"], 2)],
                                 "row_pitch": {"band1": g["P1"], "band2": g["P2"], "band3_sub": g["SP"],
                                               "band3_group_gap": g["GG"]}},
                 "legend_words": T["words"], "a_collapsed_boxes": g["A_COLLAPSED"], "b_unprinted": g["B_UNPRINTED"],
                 "e_min_gap_mm": g["E_MIN_GAP"],
                 "e_vs_d": {"shorter": T["e_shorter"], "more_ties": T["e_more_ties"], "of": len(T["e_vs_d"]),
                            "rows": T["e_vs_d"]},
                 "c_rlm_fail_judge_scores": T["c_rlm_fail"], "papers_nulls_on_W": T["papers_nulls_W"],
                 "f_left_out": dat["f_out"], "pull": pull_log,
                 "concept_reading": {"drawn": READINGS["D181"], "reproduced_first": READINGS["loose"],
                                     "source_data_cells_changed_vs_loose": changed},
                 "judge_rows": R["judge_rows"]}
        if R["judge_rows"].get("awaiting_s6_all_draws") == 0 and R["judge_rows"].get("cells_from_v25"):
            state["judge_key"] = "v2.5"           # D203: every answer on its final key, so S486 holds this plate on v2.5
        (stage / "fig5_data_state.json").write_text(json.dumps(state, indent=1, default=float) + "\n")
        files = {p.name: sha256_file(p) for p in sorted(stage.iterdir()) if p.name != "figure5_provenance.json"}
        (stage / "figure5_provenance.json").write_text(json.dumps({
            # D155: no build time and no HEAD; the code is named by the sha256 of the script and of the modules it
            # imports, the data by inputs_sha256
            "provenance": {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT),
                           "imports_sha256": {m: sha256_file(ROOT / "scripts" / m) for m in (
                               "S473_fig5_panels.py", "S457_fig2_panels.py", "S463_fig2_ranking.py",
                               "fig_repro.py", "judge_rows_v25.py")},
                           "command": f"uv run --frozen python {SCRIPT} figure" + (" --from <pull dir>" if args.src
                                                                                     else ""),
                           "design": "D166: the assembled plate of 28 October, version 2 "
                                     f"(findings/recompute/{SET_DIR}/{ANCHOR}/build_fig5.py)"},
            "stamp": stamp, "reproduced": rep, "page_mm": [Z["W"], Z["H"]],
            "concept_reading": READINGS["D181"], "judge_rows": R["judge_rows"],
            "anchor": {"compared": bool(srcs["anchor_applies"]), "why": srcs["anchor_applies"]
                       or "other inputs than the frozen 28 October pull: not compared",
                       "files": {n: sha256_file(p) for n, p in srcs["anchor"].items()}},
            "inputs": {"s3_collect": {"path": srcs["collect_name"], "sha256": sha256_file(srcs["collect"]),
                                      "sidecar": srcs["side"]},
                       "answers": {S473.label_of(k, srcs["labels"]): v for k, v in R["ans_inputs"].items()},
                       "l3": {"path": "findings/recompute/L3/concept_recall.jsonl",
                              "sha256": sha256_file(S473.L3_DIR / "concept_recall.jsonl")},
                       "l3_d181": {f"findings/recompute/L3_d181/{n}": sha256_file(L3_D181 / n)
                                   for n in ("concept_recall.jsonl", "header.json")},
                       "l1": {s: len(v) for s, v in R["l1"]["stages"].items()},
                       "l1_files": {f"l1/{p.relative_to(srcs['l1']).as_posix()}": sha256_file(p)
                                    for p in sorted(Path(srcs["l1"]).rglob("*.jsonl"))},
                       "pull_sources": pull_log.get("sources")},
            "inputs_sha256": dict(sorted(srcs["sha"].items())), "inputs_checked": srcs["checked"],
            "lock": {"path": "experiments/LOCK.toml", "sha256": sha256_file(S463.LOCK_TOML)},
            "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha256_file(S457.FIGURE_LOCK),
                            "status": S457.FLOCK.get("status")},
            "files": files}, indent=1, default=str) + "\n")
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    # move in: the earlier Figure 5 files of --out removed only now
    out.mkdir(parents=True, exist_ok=True)
    for pat in OWNED:
        for p in out.glob(pat):
            p.unlink()
    for p in stage.iterdir():
        shutil.move(str(p), out / p.name)
    stage.rmdir()
    print("\n".join(["reproduced:"] + [f"  {x}" for x in rep]))
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {plate}; {stamp}")


# ---------------------------------------------------------------------------------------------------------------
# selftest: offline, no model call
# ---------------------------------------------------------------------------------------------------------------
def d200_branch(tmp: Path, anchor_applies) -> str:
    """Runs _figure on the frozen inputs with a heading rule and a set folder, as a test does, and reports which plate it
    goes on to: "D200" or "D166". anchor_applies stands for the source's value. A truthy value here skips the drawn
    comparisons, which S497_fig5_d200_test.py makes for real; this checks the decision. Nothing is drawn or written."""
    class Reached(Exception):
        pass

    def stop(name):
        def f(*a, **k):
            raise Reached(name)
        return f
    g = globals()
    keep = {k: g[k] for k in ("frozen_sources", "d200_sources", "with_judge_rows", "compare_anchor_data",
                              "compare_anchor_drawn", "build", "texts", "png_equal")}
    rule = MF.HEADING_RULE
    finish = S457.finish_plate
    real = keep["frozen_sources"]
    tmp.mkdir()
    try:
        MF.HEADING_RULE = len
        g["frozen_sources"] = lambda t: {**real(t), "anchor_applies": anchor_applies}
        g["d200_sources"], g["with_judge_rows"] = stop("D200"), stop("D166")
        if anchor_applies:
            for k in ("compare_anchor_data", "compare_anchor_drawn", "png_equal"):
                g[k] = lambda *a, **k_: "stand-in"
            g["build"] = lambda d: {"SHEET": {x: {} for x in "abcdefg"}, "DRAWN": {}, "PL": type("P", (), {
                "printed": {}, "fig": None}), "W": 0, "H": 0}
            g["texts"] = lambda *a: {"legend": ""}
            S457.finish_plate = lambda *a, **k: None
        _figure(argparse.Namespace(src=None, out=str(tmp / "out"), s6=None, d200_set=str(tmp)), tmp)
    except Reached as e:
        return str(e)
    finally:
        g.update(keep)
        MF.HEADING_RULE = rule
        S457.finish_plate = finish
    return "neither"


def selftest() -> int:
    """The checks that gate the build, each shown to pass on the frozen files and to refuse an altered input."""
    n = killed = 0
    ok = True

    def expect_refused(name, f):
        nonlocal n, killed
        n += 1
        try:
            f()
            print(f"  SURVIVED {name}")
        except Refused:
            killed += 1
            print(f"  killed  {name}")

    with tempfile.TemporaryDirectory(prefix="S497_selftest_") as t:
        srcs = frozen_sources(Path(t))
        print(f"  PASS    the frozen inputs: {srcs['checked']}")
        sha, committed = srcs["sha"], {k for k in srcs["sha"] if k.startswith((f"{SET_DIR}/", "fig2_inputs/"))}
        tsv = S473.identical_files(FR.frozen(SET, "s3/IDENTICAL_FILES.tsv"))
        k_pin = next(k for k in PINS)
        k_tsv = next(k for k in tsv if k in sha and k not in PINS and k not in committed)
        for name, (s_, t_, c_) in {
                f"a pinned input changed ({k_pin})": ({**sha, k_pin: "0" * 64}, tsv, committed),
                f"a file IDENTICAL_FILES.tsv names changed ({k_tsv})": ({**sha, k_tsv: "0" * 64}, tsv, committed),
                f"a pinned input not read ({k_pin})": ({k: v for k, v in sha.items() if k != k_pin}, tsv, committed),
                "an input read and pinned nowhere": ({**sha, "elsewhere/extra.jsonl": "0" * 64}, tsv, committed)}.items():
            expect_refused(name, lambda s_=s_, t_=t_, c_=c_: check_inputs(s_, t_, c_))
        # a committed frozen file changed by one byte: check_committed refuses it (a copy in a repository layout)
        src_h = FR.frozen(SET, "l1/header.json")
        rel = src_h.relative_to(ROOT).as_posix()
        line = next(x for x in (ROOT / "findings/recompute/frozen_inputs/SHA256SUMS").read_text().splitlines()
                    if x.endswith("  " + rel))
        fake_rec = Path(t) / "repo" / "findings" / "recompute"
        fake = fake_rec.parents[1] / rel
        fake.parent.mkdir(parents=True)
        fake.write_bytes(src_h.read_bytes() + b" ")
        (fake_rec / "frozen_inputs").mkdir(parents=True)
        (fake_rec / "frozen_inputs" / "SHA256SUMS").write_text(line + "\n")

        def bent_file():
            try:
                FR.check_committed(fake, root=fake_rec)
            except FR.FrozenInputError as e:
                raise Refused(str(e)) from None
        expect_refused("a committed frozen file changed by one byte (check_committed)", bent_file)
        # the locked plate: its own numbers pass both comparisons; a moved number, a count and a reordered list do not
        an = json.loads(srcs["anchor"]["numbers.json"].read_text())
        an["_legend"] = srcs["anchor"]["legend.md"].read_text().rstrip("\n")
        f5 = json.loads(srcs["anchor"]["figure5_numbers.json"].read_text())
        try:
            compare_anchor_drawn(an["panels"], f5["sheets"], f5["printed"], an["_legend"], an, f5)
            print("  PASS    the locked plate's numbers equal themselves (compare_anchor_drawn)")
        except Refused as e:
            ok = False
            print(f"  FAIL    the locked plate's numbers against themselves: {e}")
        moved = json.loads(json.dumps(an["panels"]))
        moved["e"]["marks"][0]["margin_pct"] += 1e-9
        expect_refused("a drawn margin moved by 1e-9",
                       lambda: compare_anchor_drawn(moved, f5["sheets"], f5["printed"], an["_legend"], an, f5))
        cnt = json.loads(json.dumps(an["panels"]))
        cnt["b"]["counts"]["single pass"]["both_high"] += 1
        expect_refused("a panel b count moved by 1",
                       lambda: compare_anchor_drawn(cnt, f5["sheets"], f5["printed"], an["_legend"], an, f5))
        sh = json.loads(json.dumps(f5["sheets"]))
        sh["Fig. 5g"]["rows"][1], sh["Fig. 5g"]["rows"][2] = sh["Fig. 5g"]["rows"][2], sh["Fig. 5g"]["rows"][1]
        expect_refused("two Source Data rows of g swapped",
                       lambda: compare_anchor_drawn(an["panels"], sh, f5["printed"], an["_legend"], an, f5))
        expect_refused("a legend word changed",
                       lambda: compare_anchor_drawn(an["panels"], f5["sheets"], f5["printed"],
                                                    an["_legend"].replace("68 of 86", "67 of 86"), an, f5))
        av = anchor_view(an["panels"])
        rev = json.loads(json.dumps(av))
        rev["a"]["columns"]["pass"]["per_strategy"]["single pass"]["per_question"].reverse()

        def before_drawing():
            d_ = first_diff(rev["a"], av["a"], "a")
            if d_:
                raise Refused(d_)
        expect_refused("a's per-question values reordered (the comparison before drawing)", before_drawing)
        # the PNG: equal to itself; one pixel changed is refused
        png = srcs["anchor"][ANCHOR_PNG]
        try:
            png_equal(png, png)
            print("  PASS    the locked plate's PNG equals itself pixel for pixel")
        except Refused as e:
            ok = False
            print(f"  FAIL    png_equal on the same file: {e}")
        import fitz
        pm = fitz.Pixmap(str(png))
        pm.set_pixel(pm.width // 2, pm.height // 2, (0, 0, 0) if pm.pixel(pm.width // 2, pm.height // 2)[0] else
                     (255, 255, 255))
        one = Path(t) / "one_pixel.png"
        pm.save(str(one))
        expect_refused("one pixel of the PNG changed", lambda: png_equal(one, png))
        # the collect's time: read in COLLECT_TZ it falls inside the pull's window; read in another zone it does not
        pull_log = json.loads(srcs["pull"].read_text())
        at = (json.loads(FR.frozen(SET, "s3/g1_collect.jsonl.json").read_text())["_provenance"])["at"]
        try:
            print(f"  PASS    the collect's time {at} in {COLLECT_TZ} is {collect_utc(at, pull_log)}, inside the pull")
        except Refused as e:
            ok = False
            print(f"  FAIL    collect_utc on the frozen pull: {e}")
        expect_refused("the collect's time read in another zone (America/New_York)",
                       lambda: collect_utc(at, pull_log, "America/New_York"))
        # the raw-judge cross-check: a collect row with another correctness is refused
        row = {"a": {"status": "ok", "scores": {"correctness": 4}}}
        if (jscore(row), jscore({"a": {"status": "no_answer"}}), jscore({"a": {"status": "error"}})) != (4, 0, None):
            ok = False
            print("  FAIL    jscore: ok -> correctness, no_answer -> 0, error -> no value")
        else:
            print("  PASS    jscore reads ok, no_answer and error as the recount did")
        f_ = {"n_concepts": 3, "found_loose": 3}
        if not every_concept(f_) or every_concept({"n_concepts": 3, "found_loose": 2}) or \
                not every_concept({"concept_recall_loose": 1.0}):
            ok = False
            print("  FAIL    every_concept")
        else:
            print("  PASS    every_concept: found_loose equal to n_concepts")
        # D186 (4): read_l3_d181 passes on the committed files and refuses each altered copy
        groups = S463.key_groups()
        l3 = S473.read_l3(groups)
        try:
            got = read_l3_d181(groups, l3)
            print(f"  PASS    {got['reproduced']}")
        except Refused as e:
            ok = False
            print(f"  FAIL    read_l3_d181 on the committed L3_d181: {e}")
        expect_refused("L3_d181 at a sha256 other than the pinned one",
                       lambda: read_l3_d181(groups, l3, pins={**L3_D181_SHA256, "header.json": "0" * 64}))
        k24, k25 = S463.JR.S512.keys()
        same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}

        def altered(name, edit_rows=None, edit_header=None):
            d_ = Path(t) / f"l3d_{name}"
            d_.mkdir()
            rows_ = S473.read_jsonl(L3_D181 / "concept_recall.jsonl")
            hdr_ = json.loads((L3_D181 / "header.json").read_text())
            if edit_rows:
                edit_rows(rows_)
            if edit_header:
                edit_header(hdr_)
            (d_ / "concept_recall.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows_))
            (d_ / "header.json").write_text(json.dumps(hdr_))
            return lambda: read_l3_d181(groups, l3, d_, {n: sha256_file(d_ / n) for n in L3_D181_SHA256})

        def first(rows_, held):
            return next(r for r in rows_ if r["group"] == "answerable" and (r["question_id"] in same_c) == held)
        expect_refused("an L3_d181 row of another answer (answer_sha256)",
                       altered("sha", lambda R_: first(R_, True).update(answer_sha256="0" * 64)))
        expect_refused("an L3_d181 loose base differing from L3 on a question whose concepts v2.5 left unchanged",
                       altered("base", lambda R_: first(R_, True).update(found_loose_base=-1)))
        expect_refused("an L3_d181 header that is provisional",
                       altered("prov", edit_header=lambda h_: h_.update(provisional=True)))
        expect_refused("an L3_d181 header on another answer copy",
                       altered("copy", edit_header=lambda h_: h_["inputs"].update(manifest_sha256="0" * 64)))
        expect_refused("an L3_d181 row missing",
                       altered("drop", lambda R_: R_.pop()))
        try:
            got = altered("changed", lambda R_: first(R_, False).update(concept_recall=0.0))()
            print("  PASS    a D181 value of a question whose concepts v2.5 changed is read as written (no L3 value "
                  "to hold it to)")
        except Refused as e:
            ok = False
            print(f"  FAIL    a changed-concept D181 value refused: {e}")
        # D186 (3): with_judge_rows works on a copy, so the key v2.4 result the locked plate is reproduced from stays
        # as read; a v2.5 row chosen replaces its answer's row in panel f's call with passages and in b's raw rows
        R0 = read_and_compute(srcs)
        import copy
        cells0 = copy.deepcopy(R0["read"]["cells"])
        faith0, raw0 = dict(R0["faith_rows"]), dict(R0["raw"])
        pick = next(x for x in R0["col_rows"] if x["draw"] == 1 and (x.get("b") or {}).get("status") == "ok")
        kk = (pick["config"], pick["question_id"], pick["draw"])
        new_row = json.loads(json.dumps(pick))
        new_row["b"]["scores"]["faithfulness"] = -7
        new_row["key_version"] = "v2.5"

        def stand_in(read, *a, **k):
            jr = S463.judge_rows(read, *a, **k)
            ck = next(c for c in jr["choice"] if c != "_sources" and tuple(c[1:]) == kk)
            jr["choice"][ck] = {"status": "v2.5", "row": new_row}
            return jr
        R1 = with_judge_rows(R0, srcs, stand_in)
        checks = [
            ("the v2.4 result is left as read (cells, panel f's rows, b's raw rows)",
             R0["read"]["cells"] == cells0 and R0["faith_rows"] == faith0
             and R0["raw"] == raw0 and R1["read"] is not R0["read"]),
            ("the v2.5 row chosen replaces its answer's faithfulness in f and its raw row in b",
             R1["faith_rows"][kk] == ("ok", -7, None) and R1["raw"][kk] is new_row and R1["v25_rows"] == 1
             and all(R1["faith_rows"][x] == faith0[x] for x in faith0 if x != kk)),
            ("with the frozen inputs (no S6 outs) the reader reads every answer of the 132 from key v2.4",
             R1["judge_rows"]["awaiting_s6_read"] == 1080 and R1["judge_rows"]["cells_from_v25"] == 0)]
        src_fig = Path(__file__).read_text().split("def _figure(", 1)[1].split("\ndef ", 1)[0]
        checks.append(("_figure reads the v2.5 rows only after the locked plate is held to anchor_d166 (data, drawn "
                       "numbers, PNG)",
                       src_fig.index("with_judge_rows(") > max(src_fig.index("compare_anchor_data("),
                                                               src_fig.index("compare_anchor_drawn("),
                                                               src_fig.index("png_equal("))
                       and src_fig.index("dat0 = panel_data(R)") < src_fig.index("with_judge_rows(")))
        for name, good in checks:
            ok = ok and good
            print(f"  {'PASS' if good else 'FAIL'}    with_judge_rows: {name}")
        # D200: the filter's gate, 5c's rule on S06's means, rho_box on S473's e rows, the held row, and the order
        for name, f in (("the filter's gate on the 28 October rows", lambda: bool(MF.gate(MF.read_rows())["passed"])),
                        ("5c on S06's means", lambda: bool(print(f"  PASS    {check_ablation_s06()}")) is False),
                        ("rho_box on S473's e rows", lambda: bool(print("  PASS    " + S540.check_rho_box(
                            [(p["question_id"], p["faithfulness"], p["papers_precision"])
                             for p in R0["fn"]["e"]["points"]]))) is False)):
            try:
                good = f()
            except (Refused, S540.Refused, MF.GateFail) as e:
                good = False
                print(f"  FAIL    {name}: {e}")
            ok = ok and good
            print(f"  {'PASS' if good else 'FAIL'}    {name}")
        made = [{"question_id": f"q{i // 6}", "correctness": i % 6, "faithfulness": (i * 5) % 6, "concept": i / 40,
                 "papers": (i * 7 % 40) / 40, "ragas:faithfulness": (i * 3 % 40) / 40} for i in range(40)]
        e_rows = S540.evaluator_rows(made, S540.ROWS_5E[:1] + S540.ROWS_5E[-1:])
        held = [r for r in e_rows if r["row"] == "Second judge"]
        keys = list(e_rows[0])
        blank = all(r[k] is None for r in held for k in keys if k not in ("row", "family", "judge_signal", "source"))
        checks2 = [("without second-judge rows the row is blank with its source 'held, D195'; S518's file exists "
                    "(S518 ran on Valerio's word, 2 Nov, e241d6e3)",
                    blank and {r["source"] for r in held} == {S540.HELD} and S540.RELEASE.exists()),
                   ("build_d200 comes after every anchor comparison in _figure",
                    src_fig.index("build_d200(") > max(src_fig.index("compare_anchor_data("),
                                                       src_fig.index("compare_anchor_drawn("),
                                                       src_fig.index("png_equal("))),
                   ("rank_text prints 3 and 3.5 as written", (rank_text(3.0), rank_text(3.5)) == ("3", "3.5")),
                   ("papers_n gives one n, or the largest and those that differ, never a range",
                    papers_n({"rlm_5": 83, "rlm_10": 83}) == "83"
                    and papers_n({"rlm_5": 82, "rlm_10": 83, "rlm_20": 82, "multi_hop": 83})
                    == "83, or 82 for RLM-5 and RLM-20"
                    and papers_n({"rlm_5": 82, "rlm_10": 83, "rlm_20": 81, "multi_hop": 82, "single_pass": 82})
                    == "83, or 82 for RLM-5, multi-hop and single pass, 81 for RLM-20")]
        for name, good in checks2:
            ok = ok and good
            print(f"  {'PASS' if good else 'FAIL'}    D200: {name}")
        expect_refused("a stored precision with no per_claim (apply_claim_filter)", lambda: apply_claim_filter(
            {"stages": {"papers": {"k": {"signals": {"precision": 0.5}, "detail": {"per_claim": []}}}}}))
        # which branch _figure takes, with its decision made in _figure itself, on rows that are not the frozen ones
        rule = MF.HEADING_RULE
        waits = {}
        try:
            MF.HEADING_RULE = None
            waits["no rule"] = d200_waits("frozen inputs", t)
            MF.HEADING_RULE = len
            waits["all three"] = d200_waits("frozen inputs", t)
            waits["no set"] = d200_waits("frozen inputs", None)
            waits["no anchor"] = d200_waits(None, t)
        finally:
            MF.HEADING_RULE = rule
        # D208: the rule is no longer waited for; Papers waits inside the plate (papers_waits) while no rule is set
        try:
            MF.HEADING_RULE = None
            pw_none = papers_waits()
            MF.HEADING_RULE = len
            pw_rule = papers_waits()
        finally:
            MF.HEADING_RULE = rule
        blank = blank_papers({"A": {"papers": {}, "pass": {}}, "D": {("multi_hop", "papers"): {"n": 3},
                                                                     ("multi_hop", "judge"): {"n": 3}},
                              "cc": {"means": {"judge": {}, "concept": {}, "papers": {"x": 1.0}}, "W": 0.9},
                              "E_DRAWN": [{"signal": "papers"}, {"signal": "judge"}]})
        # D298: the evaluators' sheet is e (f from D295); a blank sheet c (old d's columns) stands in for the blank one
        sh = {f"Fig. {FIG_N}e": {"columns": ["row", "rho"], "rows": [["Papers", 0.3], ["Concepts", 0.4]]},
              f"Fig. {FIG_N}c": {"columns": SHEET_COLS["c"], "rows": [["x", "single pass", "papers"] + [None] * 4]}}
        for name, good in (("d200_waits is empty with the set and the anchor comparison, rule or not (D208)",
                            not waits["all three"] and not waits["no rule"] and bool(waits["no anchor"])
                            and (bool(waits["no set"]) != D200_DIR.exists())),
                           ("Papers waits with no rule and no S564 reader, and not under a test's rule",
                            pw_none is (PAPERS_SELECTION is None) and pw_rule is False),
                           ("blank_papers leaves no Papers value: a, b, d's Papers facet, the margins, W and rho, g",
                            blank["A"]["papers"]["n"] == 0 and blank["b_median"] is None and blank["G"] == []
                            and blank["D"][("multi_hop", "papers")]["n"] is None
                            and blank["D"][("multi_hop", "judge")]["n"] == 3
                            and blank["E_DRAWN"] == [{"signal": "judge"}] and "papers" not in blank["cc"]["means"]
                            and "W" not in blank["cc"]),
                           ("papers_left finds a Papers value in sheet Fig. 6e and none in a blank Fig. 6c",
                            papers_left(sh) == [(f"Fig. {FIG_N}e", 0, "rho")]),
                           ("_figure with the rule and a set, on rows the anchor did not compare, does not reach D200",
                            d200_branch(Path(t) / "branch", None) == "D166"),
                           ("the same run with the comparisons made (stood in here, real in the d200 test) reaches D200",
                            d200_branch(Path(t) / "branch2", "stand-in") == "D200")):
            ok = ok and good
            print(f"  {'PASS' if good else 'FAIL'}    D200: {name}")
        a_ = {"Fig. 5x": {"columns": ["a", "b"], "rows": [[1, 2.0], [3, 4]]}}
        b_ = {"Fig. 5x": {"columns": ["a", "b"], "rows": [[1, 2], [3, 5]]}}
        if changed_cells(a_, b_) != {"Fig. 5x": 1} or changed_cells(a_, {"Fig. 5x": {"columns": ["a"], "rows": []}}) \
                != {"Fig. 5x": {"rows_before": 2, "rows_after": 0}}:
            ok = False
            print("  FAIL    changed_cells")
        else:
            print("  PASS    changed_cells counts the cells that differ, and gives row counts when the shape differs")
    print(f"selftest: {'checks pass' if ok else 'a check FAILED'}; mutants {killed} of {n} killed")
    return 0 if ok and killed == n else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--from", dest="src", help="a pull folder (S473 pull --to); without it the frozen inputs (D155)")
    f.add_argument("--out")
    f.add_argument("--s6", help="the folder holding out_s6_g1 and out_s6_g1r15 (S6G1, key v2.5; D186 (3)); default the "
                                "folder holding the outs the collect read")
    f.add_argument("--claims-out", help="D2: also write the claims list (claims.md, read from the documents) into "
                                        "this folder; the editorial step, never the figure build")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    global CLAIMS_OUT
    if getattr(a, "claims_out", None):
        CLAIMS_OUT = Path(a.claims_out).resolve()
    try:
        if a.cmd == "selftest":
            return selftest()
        FR.pin_hash_seed()                     # D155: the PDF's font subsets depend on the string-hash seed
        figure(a)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
