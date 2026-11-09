#!/usr/bin/env python3
"""S476 - Supplementary Figure 8 (main Figure 3 until FF3 a's one list), as D123 sets it (Valerio, 23 October, "I agree with Q5:O1, Q7: keep the author RLM as main too"):
a, concept recall against the turn cap for Mentori's RLM (G5) and the authors' RLM package (G6), both main lines;
b, T1's four local models by cap on the same measure; c, corpus scale from G4: since D150 (PANEL C AS D150 SETS IT,
below) a grid, each of five strategies minus single pass on each index (core papers x distractor ratio) at judge score
4 and 3, each index on the questions it can answer as D126 sets it (Valerio, 23 October, "Q10: [...] I say O2"; D125's
bars and ticks of RLM-10 against single pass were replaced by the grid, audit 27 Oct F5); d, the share of answers
reaching the cap, drawn small, until D149 (Valerio, 26 October 18:40, D-3b) made it a strip under a: per system and
cap two bars side by side under that system's box, the share of answers whose turns reached the cap (plain) and the
share the cap cut off (stopped by it, hatched with drawn diagonal lines); a second key line names the two; its rows
go to sheet Supplementary Fig. 8a; c takes the width d had. Provisional.

VALERIO'S PICKS OF 26 OCTOBER (Figure 3 options page). a is A-1: at each turn cap two boxes, Mentori's RLM (G5) left
and the authors' RLM package (G6) right; box first to third quartile (numpy linear percentiles), thick line the median,
whiskers the full range, every question a dot, a thin line joining each system's medians, caps evenly spaced, no mean
(the mean and its interval stay in the data workbook, D128). b is B-2: one small panel per local model, caps evenly spaced as in a,
a grey line per question (one grey, Q_GREY, for every model; Valerio's follow-up at 15:00), a thick black line
for the median over the questions, and a reference line, the median of the same questions with gemini-3-flash-preview (Mentori's RLM, a's G5 run, draw 1) in GEMINI_REF_COLOUR,
drawn on top; the key is a short sample of each line with its meaning only, no line style in words.

THE RANGE STRIP (FF30 a; supp.md section 7). Under the strip of a, a second strip draws, per cap and system, the range of the
mean concept recall over three draws on D98's 29 questions (draw_range_rows): Mentori RLM's from S514 l2g7's noise_tables.json,
Zhang RLM's from the rows a draws. While noise_tables.json has read draw 1 alone it draws its axis only, its sheet rows are
blank and the legend has no clause for it. Numbers print as "{d_sign}{d_size_pp:.1f}" from two sheet columns (build_order F6).

WHY A SCRIPT OF ITS OWN. S475 (two panels, L2 only) stays as committed; D123 adds two sources that need a pull from
the Studio and a scoring step (T1's answers, S3's judging of G4). S476 imports S475, S474, S463, S457, S459 and
check_t1 and changes none of them.

THE ONE COMMAND (D155; S494 calls it) rebuilds Supplementary Figure 8 from the frozen inputs, every step in order, each
reproducing before it writes:

    uv run --frozen python scripts/S476_fig3_d123.py rebuild [--out <an empty folder>]

  1. S474 --frozen: findings/recompute/L2_inputs (G5's draw-1 file 52abab86, G6 before the D92 reruns) -> L2/
  2. t1 on the frozen copy: fig3_t1.tar (with fig3_g4_inputs.tar for check_copy)              -> T1_L2/
  3. g4c on the frozen copy: findings/recompute/fig3_inputs (g4_collect.jsonl 8f10e30a, G4's final judging, refrozen
     27 October by frozen_inputs/refreeze_fig3.py, D156; 5ca931f4 until then; its sidecar, s3/) and
     fig3_g4_inputs.tar                                                                         -> G4_fig3c/
  4. plate                                                                -> figures_provisional/supp_fig8_depth/
  D160 (7) Q23 (Valerio, 27 October, "Yes, as D156"): when G6's records after the D135 reruns are frozen
  (findings/recompute/g6_d135_inputs, frozen_inputs/freeze_g6_d135.py), step 1 also writes L2_d135/ (S474's method on
  them, held to L2/ but for the answers the reruns acted on) and a draws it; L2/ stays the reading S475.reproduce and
  its anchors gate. Until then there is no L2_d135/ and a draws L2/; supplementary_figure8_provenance.json's l2_readings says which.
  D160 (6) Q18: g4c also checks every grid cell against the grid as committed before D156 (anchor_pre_d156_grid.json,
  on the reading with the judged G4R38 reruns held out), each drawn cell against its S3 judge row, and, once frozen
  (findings/recompute/fig3_g4r38_inputs, frozen_inputs/freeze_g4r38.py), G4R38's 38 rerun answer texts; header.json's
  grid.checks_d160 records all three. D160 (15) S1: the stamp's c counts the covered draw-1 answers ("of 4284").
  D186 (4) (Valerio, 31 October, Q10): a draws D181's concept recall (S505's loose matcher with the question rule,
  Q-need, reading (b), key v2.5) by default: findings/recompute/L2_d135_d181 (S474 --d181 --frozen-d135), gated by
  L2_d181 (S474 --d181 --frozen). Reproduce first: L2/ and S475's v2.4 loose anchors (G5 cap 20 76.8%, G6 cap 50
  65.9%) run as before, and L2_d135/ is held to L2/; then reproduce_l2_d181 holds each D181 folder to its loose
  reading (header S474's final D181 one on key v2.5; the same answers one for one; on the questions whose concepts
  v2.5 left unchanged the loose base equal to the loose value; cap_tables.json equal to S474.tables(d181) of its rows),
  holds L2_d135_d181 to L2_d181 but for the answers the reruns acted on (the D160 Q23 check, the same count as the
  loose one), and runs S475.reproduce with the D181 anchors (ANCHORS_D181: G5 cap 20 71.9%, G6 cap 50 63.1%, as
  S474 --d181 printed them) on L2_d181. The two D181 folders are read here, not rebuilt; S494's step d181 rebuilds their
  rows and tables (D201 Q9 O1, 2 November 2026), and check_d181_L3_L2.py checks them.
  D188 (Valerio, 31 October, "every figure using v2.4 needs to move to v2.5"): b draws T1's D181 reading,
  findings/recompute/T1_L2_d181 (scripts/S514_fig3_d185.py t1), and its gemini-3-flash-preview reference line a's
  D181 G5 rows (L2_d135_d181), so b's lines and reference stay on one measure, now a's; c draws S514 g4c's draw-1
  reading, findings/recompute/G4_fig3c_d185 (per answer the key v2.5 judge row where S6 has judged one of the 132
  questions v2.5 changed, else the v2.4 row; scripts/judge_rows_v25.py). Reproduce first: T1_L2 and G4_fig3c are
  rebuilt and reproduced as before, then reproduce_t1_d181 holds T1_L2_d181 to T1_L2 (header S514's D181 reading on
  key v2.5, held_to the sha256 of T1_L2's rows and tables; the same answers, each with the same identity, text and
  status fields; on the questions whose concepts v2.5 left unchanged the loose base equal to T1_L2's loose value of the
  text; a failed answer 0; cap_tables.json equal to t1_tables on concept_recall) and reproduce_g4_d185 holds
  G4_fig3c_d185 to G4_fig3c (header S514's, provisional, with the draw-1 units; the same rows and flags, every row of a
  question v2.5 left unchanged equal to G4_fig3c's; passes equal to correctness against 4 and 3; grid_tables.json equal
  to grid_tables of its rows and units, each cell's answers awaiting S6 recounted from key_versions). Both folders are
  read, not rebuilt (S514 t1 imports d181_concept_recall). The selftest and mutants draw b and c on fixtures of both
  shapes (fixture_t1_d181, fixture_g4_d185) and on the v2.4 readings.
With --out every output goes under that folder (L2/, T1_L2/, G4_fig3c/, supp_fig8_depth/) and the committed files are
not touched, so a rebuild can be compared with them; without it, the committed folders are rewritten in place. The
frozen copy is read through scripts/fig_repro.frozen() (the tars from env FROZEN_TARS, default
~/Mentori_scratch_keep/frozen_2026-10-26, checked against findings/recompute/frozen_inputs/SHA256SUMS; every committed
frozen file against its SHA256SUMS line). Before t1 and g4c write, the sha256 of every frozen input they read must
equal what the committed T1_L2/header.json and G4_fig3c/header.json recorded (frozen_inputs_sha256; before that
record existed, the T1 files' and the collect sidecar's fields), else exit 2 with nothing written. Every output is
deterministic: no write time, git state or temporary path in any header, provenance or workbook (the data workbook through
fig_repro.deterministic_xlsx; PDF and SVG with no date and a fixed SVG salt, checked by fig_repro).

OTHER COMMANDS, from the repository root, all under `uv run --frozen`. Every step reproduces before it writes and
exits 2 with nothing written on any difference. pull, t1 --copy and g4c --copy are for a new pull of live runs.

    python scripts/S476_fig3_d123.py pull --to <a new, empty folder>
    python scripts/S476_fig3_d123.py t1 --copy <that folder>       -> findings/recompute/T1_L2/
    python scripts/S476_fig3_d123.py g4c --copy <that folder>      -> findings/recompute/G4_fig3c/
    python scripts/S476_fig3_d123.py plate                         -> findings/figures_provisional/supp_fig8_depth/
    python scripts/S476_fig3_d123.py selftest [--keep <empty folder>] (offline, fixtures; --keep keeps the fixture plate)
    python scripts/S476_fig3_d123.py mutants                       (offline, fixtures)
    python scripts/S476_fig3_d123.py anchor                        -> findings/recompute/G4_fig3c/anchor_d149_rlm10.json
                                                                      (once: D149's RLM-10 reading, from git at 818eff68)
    python scripts/S476_fig3_d123.py anchor-pre-d156               -> findings/recompute/G4_fig3c/anchor_pre_d156_grid.json
                                                                      (once: panel c's grid before D156, from git at
                                                                      8ab8614a; D160 Q18)

PULL (read only on the Studio). One subprocess, `ssh -o ConnectTimeout=20 10.15.212.253 bash -s`, with the remote
script PULL_SH on stdin (never on a command line, never written on the Studio). The remote script runs
/usr/bin/python3 - and writes one tar stream to stdout: T1's clone (git HEAD, assignment.toml, the walk log, every
results file of the four models by check_t1.prefix(), globbed inside Python, each with its sha256, size and mtime
taken there from the very bytes sent, and the count of files the held models have), S3's G4 judging (each judge
folder's rows, headers, recheck and summary, start records, units lists and the claim names, read before the rows),
out_g4r38 the same way if it exists, and the frozen G4 inputs (COPY.json, MANIFEST.sha256, the six strategies'
runs' answers.jsonl and run_identity.json, D150). No port, no results file name, no K1 path is on any command line. On the
laptop: members checked, extracted with filter="data", a partial last line cut (S463.cut_partial), every T1 file
against the sha256 sent with it, every G4 input against its MANIFEST.sha256 line, the clone's assignment.toml equal to
the repository's, then s3_guard.py collect (--set G4, --replace out_g4r38 when present).

T1 (panel b). Gate first: S474.gate reproduces S383 on 1,362 of 1,362 rows. Then check_t1's own checks on the copy:
the stored cells follow the written order (interleave_problems: no problem), no key outside the order, each row's
question, cap, draw, max_turns and model match its key, the stored cells are exactly the walk log's "end" records
with rc 0 and stored true, the held models store nothing. Each stored answer is scored by S474.score (loose matcher,
v2.4 key, Mentori's turn-limit note removed where the record flags it); an answer with a stored error is failed and
scores 0 (LIST.md Rule 10). The plotted value of a model at a cap is the median over the questions every model not
held has stored at every cap (check_t1 complete_questions, D118; B-2's thick black line, plate: bcap median_pct); the
mean and its Rule 2 interval (seed 20261013, 10,000 resamples of those questions sorted, S463.interval) go to the data
workbook only (sheet Supplementary Fig. 8b's mean_pct, ci95_lo_pct, ci95_hi_pct).

G4C (panel c). Draw 1 of G4's rlm_10 and single_pass, judged by S3 (plain call (a), devstral-small-2:24b). Cell of
(index, config, question): 1 when (a) is ok and correctness 4 or more (Rule 5, D154: the pass rate), else 0, and
the same at 3 or more (the relaxed threshold); an input answer with a
generation error or no text (S3 judges answered answers only) is a failure of the system under test and scores 0
(Rule 10); a G4R38 key with no judged rerun is held out as a setup error (Rule 10); an (a) of a failed judge call
(error, stalled, length, cancelled, unparseable) is a missing measurement. An index is drawn only when both its units
are complete (no claim, summary present, judged rows plus failed answers equal the copy's answer lines, the summary's
status counts equal the rows'). Paired questions (D126): of the common set's answerable group (Rule 8, Q105; 86),
those the index can answer, whose source papers (the D5 key's source_files) are all among its core papers; an index
of N core papers holds papers 01 to N (recovered_harness/tests/experiments_v4/create_indexes.py:79-87, 182-215).
covered_set() derives the set; coverage_check() reproduces it before use: 22, 44, 86 and 86 at 5, 10, 20 and 50 core
papers, each equal to the per-size answerable questions (experiment.py scaling_questions, min_core <= N) restricted to
the 86; plate derives every row's covered flag again from the key. Point: d = the mean over the paired questions with
both cells present of (rlm_10 minus single pass), in percentage points, with S463.interval's two-sided 95% percentile
interval over 10,000 resamples of those questions sorted. g4c writes this two-strategy reading to G4_fig3c's
point_tables.json and pairs.jsonl, the reproduction reference: Rule 3's sign-flip P, the helped, harmed and equal
counts, the same at threshold 4, d with the failures left out, the per-config counts, the per-size-answerable reading
(April's question set) and the reading on all 86 common answerable questions (common86, D125's pairing). The data workbook's
sheet Supplementary Fig. 8c holds the grid's cells only (below), each with its sign-flip P.

PANEL C AS D150 SETS IT (Valerio, 26 October 19:00, layout O-b1). The same rules on all six strategies (g4_cells with
configs=G4_ALL: each unit complete by g4_cells' own rule, every strategy's answers in the copy; a G4R38 key's stop
reason as g4r38_keys.txt lists it). A cell of the grid is a strategy minus single pass on one index at judge score 4
(the pass rate, D154) or 3 (the relaxed threshold) (grid_point: the covered questions with both cells present, d in percentage points, S463.interval's two-sided 95%
interval, S463.signflip_p), drawn when both units are complete. Before anything is written, grid_gate reproduces the
two-strategy reading: the six-strategy cells of rlm_10 and single pass equal the two-strategy ones question by question,
RLM-10's grid cells equal g4_point's reading (n, d, interval, P at 3 and 4), and equal D149's committed Source Data
(anchor_d149_rlm10.json); any difference exits 2. D156 (Valerio, 27 October, Q14 O1): the anchor is checked on the
reading with the judged G4R38 reruns held out (g4_cells hold_g4r38, the reading D149 was drawn from), which must
reproduce it exactly; the reading with them judged is checked for the first two and is the one written and drawn.
header.json's grid gate records both (anchor_reading, drawn_reading, g4r38_held_for_anchor), and reproduce_g4 holds
the same keys out of the committed rows (hold_rows) to check the anchor again. g4c writes grid_pairs.jsonl and grid_tables.json beside the
two-strategy files, which stay as the reproduction reference (their common-86 and per-size readings are no longer in
the data workbook). Panel c draws the grid: score 4 above score 3 (D154; score 3 above 4 until then), one cividis scale
centred on 0, the number in each cell at
8 pt, a frame where the interval excludes 0, an empty outlined cell where a unit is not complete. Sheet Supplementary Fig. 8c holds
every cell. c's answers drawn count each answer that enters a complete cell once; planned (D160 S1), the draw-1 answers
the cells can hold: 6 strategies x the covered questions of the 12 indexes (22, 44, 86 and 86 at 5, 10, 20 and 50
core papers, three distractor ratios each), not G4's whole plan with draws 2 and 3 (c_planned, from G4's design,
4,284). D161 (9) N9: plate refuses when a panel draws more answers than it planned (over_plan: a's G5 against its D98
plan, a's G6 against G6_DRAWS x a's questions x caps, b against T1's 360, c against c_planned);
scripts/S476_fig3_d123_test.py pins c's stamp count and how it is derived, and proves each refusal.

PLATE. Reads findings/recompute/L2, L2_d135, L2_d181, L2_d135_d181, T1_L2, T1_L2_d181, G4_fig3c and G4_fig3c_d185. Reproduces S475 on L2 (every cap_tables value, the
anchors), S459's design constants, T1_L2's and G4_fig3c's tables from their rows, and S463.reproduce(). Draws a (A-1
on S475's numbers, with the strip of D149 under it on S475's panel b numbers), b (B-2) and c at [page] width_double_mm, under FIGURE_LOCK.toml; the
Gemini reference of b is taken from L2's G5 rows and must equal the median of the data workbook's a rows on the same
questions; check_drawn compares every drawn value with the data workbook (a: each dot, box, whisker, median and median line;
b: each question line, median and the reference; c: each complete cell's value against its sheet Supplementary Fig. 8c row, and each
cell's printed number tied to that row by the printed map, which S448 R8 checks); each cell's interval and sign-flip P
are in the data workbook only (the interval shown only as a frame where it excludes 0); every digit-bearing text is a tick label or in the printed map. Writes the plate,
the data workbook "Supplementary Figure 8 data" (one sheet per panel), its caption, supplementary_figure8_numbers.json,
supplementary_figure8_provenance.json and legend_draft.md, after deleting the earlier "Supplementary Figure 8*" files of
the folder.

No model call. No Ollama port contacted. The Studio is only read.
"""
from __future__ import annotations

import argparse
import collections
import copy as copymod
import datetime as dt
import hashlib
import importlib.util
import contextlib
import io
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from fractions import Fraction
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


S475 = _load("S475", ROOT / "scripts" / "S475_fig3a_rlm_depth.py")    # reproduce, compute, per_question, ANCHORS
S457 = S475.S457                                                       # plate_rc, finish_plate, swarm, half_up
S459 = S475.S459                                                       # design_constants, planned_total
import S474_l2_concept_recall as S474  # noqa: E402                    # score, status_of, gate, CAP_STOPS
import fig_repro  # noqa: E402                                          # frozen inputs, deterministic outputs (D155)
import house_style as hs  # noqa: E402                                  # one drawing style for every plate
import S470_l1_signals as S470  # noqa: E402                           # the_key
S463 = _load("S463", ROOT / "scripts" / "S463_fig2_ranking.py")       # interval, signflip_p, reproduce, cut_partial
CT = _load("check_t1", ROOT / "findings" / "recompute" / "T1_runs" / "check_t1.py")

SCRIPT = "scripts/S476_fig3_d123.py"
SUPP_N = 8                                         # D302 (7 before; 8 before D257 too)
OUT = ROOT / "findings" / "figures_provisional" / f"supp_fig{SUPP_N}_depth"
SI_LABEL = S457.FLOCK["files"]["supplementary_name"].format(n=SUPP_N)   # "Supplementary Figure 8" (D92 Q194)
SIDE = f"supplementary_figure{SUPP_N}"           # the numbers and provenance files S448 --supplementary reads
SHEET = f"Supplementary Fig. {SUPP_N}"           # the data workbook's one sheet (panel c, its only panel since D283)
C_SHEET = SHEET
# D283 (Valerio, 6 November 2026, "I like. Let's go."): panels a (with its two strips) and b are main Figure 4, drawn
# here beside the Supplementary plate, which keeps panel c alone (no letter). Its folder is fig4_depth.
import figure_names as FN  # noqa: E402
MAIN_N = FN.FIG_DEPTH
MAIN_OUT = ROOT / "findings" / "figures_provisional" / "fig4_depth"
MAIN_LABEL = S457.FLOCK["files"]["name"].format(n=MAIN_N)            # "Figure 4"
MAIN_SIDE = f"figure{MAIN_N}"                    # figure4_numbers.json and figure4_provenance.json (S448 R8)
MAIN_SHEET = f"Fig. {MAIN_N}"                    # Source Data sheets "Fig. 4a" and "Fig. 4b"
MAIN_SD = S457.FLOCK["source_data"]["workbook_name"].format(n=MAIN_N).removesuffix(".xlsx")   # "Source Data Fig. 4"
T1_L2 = ROOT / "findings" / "recompute" / "T1_L2"
G4_FIG3C = ROOT / "findings" / "recompute" / "G4_fig3c"
L2 = S475.L2
FIGURE_LOCK = S475.FIGURE_LOCK
GUARD = ROOT / "findings" / "recompute" / "S3_runs" / "s3_guard.py"
G4R38_KEYS = ROOT / "findings" / "recompute" / "G4_runs" / "g4r38_keys.txt"
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"
STUDIO = "10.15.212.253"
SSH = ["ssh", "-o", "ConnectTimeout=20", STUDIO, "bash", "-s"]        # the one form allowed on the Studio
T1_CLONE, S3_CLONE = "projects/mentori-runs-t1", "projects/mentori-runs-s3-g4"
T1_FOUR = ("devstral-small-2:24b", "gemma3:27b", "qwen3-coder:30b", "qwen3-coder-next:q4_K_M")   # D121
G4_CONFIGS = ("rlm_10", "single_pass")                               # D125's pairing, kept as the reproduction reference
G4_ALL = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")   # D150: panel c, S457.G1's order
GRID_STRATS = G4_ALL[1:]                                               # each against single pass
G4R38_WANT_ALL = {"single_pass": 0, "multi_hop": 0, "verified_pass": 1, "rlm_5": 4, "rlm_10": 11, "rlm_20": 22}
G4_RUN = "exp_02_scaling_factorial__{config}__{index}"
G4R38_WANT = {"rlm_10": 11, "single_pass": 0}                         # g4r38_keys.txt (G4 README, by strategy)
ANCHOR = ROOT / "findings" / "recompute" / "G4_fig3c" / "anchor_d149_rlm10.json"   # D150: RLM-10 vs single pass as D149 drew it
ANCHOR_FROM = ("818eff68", "findings/figures_provisional/fig3a_rlm_depth/figure3_numbers.json")
# D160 (6) Q18 (Valerio, 27 October, "Yes to all five"): panel c's every cell against the numbers drawn before D156,
# frozen from git at the last commit before D156's rebuild (96936742's parent; grid_tables.json last changed at 0febfc67)
ANCHOR_PRE_D156 = ROOT / "findings" / "recompute" / "G4_fig3c" / "anchor_pre_d156_grid.json"
ANCHOR_PRE_D156_FROM = ("8ab8614a", "findings/recompute/G4_fig3c/grid_tables.json")
# D160 (6) Q18: G4R38's 38 rerun answer texts, frozen (findings/recompute/frozen_inputs/freeze_g4r38.py) from the
# Studio's ~/s3_inputs/g4r38 (snap_g4r38.py make), the inputs S3 judged into out_g4r38
G4R38_TEXTS = ROOT / "findings" / "recompute" / "fig3_g4r38_inputs"
ANCHOR_KEYS = (("questions_paired", "n3"), ("d_pp", "d3"), ("ci95_lo_pp", "lo3"), ("ci95_hi_pp", "hi3"),
               ("p_signflip_two_sided", "p3"), ("t4_questions_paired", "n4"), ("t4_d_pp", "d4"),
               ("t4_ci95_lo_pp", "lo4"), ("t4_ci95_hi_pp", "hi4"), ("t4_p_signflip_two_sided", "p4"))
LOCK_WANT = S463.LOCK_WANT                                             # d66daa28 (D88)
LOCKS_OK = S463.LOCKS_OK                                               # D205
JUDGE_FAILED = S463.JUDGE_FAILED
SEED, N_BOOT = S463.SEED, S463.N_BOOT
PASS3, PASS4 = 3, 4                                                    # Rule 5
PLATE_SCORES = (PASS4, PASS3)                  # D154: 4 the pass rate (upper block, first in the data workbook), 3 relaxed
BLOCK_LABEL = {PASS4: "Pass rate 4+", PASS3: "Pass rate 3+\n(relaxed)"}   # D151's wording, sentence case
FORBIDDEN_ARGV = re.compile(r"1145[1-6]|11441|mentori-runs-k1|recompute/K1/|judge_passages|exp_\d+\S*\.py|"
                            r"ragchecker|S449|S357_ragas|run_s2_laptop")
# Panel b's reference line (Valerio, 26 October, B-2): the median of the same questions with gemini-3-flash-preview
# (Mentori's RLM, panel a's G5 run, draw 1). Its colour is this one constant, a colour of FIGURE_LOCK [colour]
# categorical (plate refuses any other). Vermillion until 26 October 16:00, then panel a's blue (Q12).
GEMINI_REF_COLOUR = S475.OKABE["blue"]                                  # Valerio, 26 October 16:00 (Q12): panel a's blue
GEMINI_REF_DASHES = (3.0, 1.5)                                         # on, off (points, times the line width); None: solid
# b's question lines (Valerio, 26 October, 15:00): one light grey for every model (the panel names the model); the
# plate's grey already (c's zero line), a grey of S448 R5 (channels within [colour] grey_tol), at least 0.6 pt wide.
Q_GREY = "#ABABAB"
LW_Q_MIN = 0.6                                                         # b's question lines, points
COLOUR_WORD = {v: k.replace("vermillion", "vermilion") for k, v in S475.OKABE.items()}   # the legend's colour names


class Refused(Exception):
    """Refused before anything is written (exit 2)."""


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def sha256_file(p) -> str:
    return S457.sha256_file(Path(p))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def write_files(outdir: Path, files: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        tmp = outdir / f".{name}.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, outdir / name)


def guarded_run(cmd, **kw):
    """S463.run with the machine guards checked on the argv first (a forbidden word stops a running job)."""
    bad = [x for x in cmd if FORBIDDEN_ARGV.search(str(x))]
    if bad:
        raise Refused(f"refused to start a process whose command line carries {bad[:2]} (machine guards)")
    return S463.run(cmd, **kw)


# ---------------------------------------------------------------------------------------------------------------
# PULL
# ---------------------------------------------------------------------------------------------------------------
PULL_SH = r"""set -e
/usr/bin/python3 - <<'PY'
import glob, hashlib, io, json, os, subprocess, sys, tarfile, time
H = os.path.expanduser("~")
PREFIXES = __PREFIXES__
HELD_PREFIXES = __HELD_PREFIXES__
KEEP = ("judge_passages.jsonl", "judge_passages_headers.jsonl", "judge_passages_recheck.jsonl",
        "judge_passages_summary.json")
tf = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
now = int(time.time())
def put(arc, b):
    if isinstance(b, str):
        b = b.encode()
    ti = tarfile.TarInfo(arc); ti.size = len(b); ti.mtime = now
    tf.addfile(ti, io.BytesIO(b))
def head(d):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
def rd(p):
    with open(p, "rb") as fh:
        return fh.read()
# T1: results first, then the walk log (a cell's begin record is written before its answer)
t1 = os.path.join(H, "__T1_CLONE__")
man = {"clone_head": head(t1), "taken_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": {},
       "held_model_files": {}}
res = os.path.join(t1, "experiments/mentori/publication/scripts/results_v4")
for m, pre in PREFIXES.items():
    for f in sorted(glob.glob(os.path.join(res, pre + "*.json"))):
        n = os.path.basename(f)
        if n.endswith("_merged.json") or "smoke" in n:
            continue
        st = os.stat(f)
        b = rd(f)
        put("t1/results_v4/" + n, b)
        man["files"]["results_v4/" + n] = {"model": m, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                                          "mtime": st.st_mtime}
for m, pre in HELD_PREFIXES.items():
    man["held_model_files"][m] = len([f for f in glob.glob(os.path.join(res, pre + "*.json")) if "smoke" not in f])
for arc, p in (("assignment.toml", "findings/recompute/T1_runs/assignment.toml"),
               ("interleaved_walk.jsonl", "findings/recompute/T1_runs/interleaved_walk.jsonl")):
    b = rd(os.path.join(t1, p))
    put("t1/" + arc, b)
    man["files"][arc] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
put("t1/PULL.json", json.dumps(man, indent=1))
# S3's G4 judging: the claim names first, then the rows
s3 = os.path.join(H, "__S3_CLONE__")
put("s3/HEAD.txt", head(s3) + "\n")
src = os.path.join(s3, "findings/recompute/S3_runs")
for o in ("out_g4", "out_g4r38"):
    od = os.path.join(src, o)
    if not os.path.isdir(od):
        continue
    cd = os.path.join(od, "claims")
    claims = sorted(os.listdir(cd)) if os.path.isdir(cd) else []
    put("s3/" + o + "/claims.txt", "".join(c + "\n" for c in claims))
    for d in sorted(glob.glob(os.path.join(od, "judge", "*"))):
        for n in KEEP:
            p = os.path.join(d, n)
            if os.path.isfile(p):
                put("s3/" + o + "/judge/" + os.path.basename(d) + "/" + n, rd(p))
    for pat in ("start_*.json", "units_*.tsv"):
        for f in sorted(glob.glob(os.path.join(od, pat))):
            put("s3/" + o + "/" + os.path.basename(f), rd(f))
# the frozen G4 inputs
g = os.path.realpath(os.path.join(H, "s3_inputs/g4"))
put("g4_inputs/REALPATH.txt", g + "\n")
for n in ("COPY.json", "MANIFEST.sha256"):
    put("g4_inputs/" + n, rd(os.path.join(g, n)))
for cfg in __G4_ALL__:
    for d in sorted(glob.glob(os.path.join(g, "runs", "exp_02_scaling_factorial__" + cfg + "__*"))):
        for n in ("answers.jsonl", "run_identity.json"):
            put("g4_inputs/runs/" + os.path.basename(d) + "/" + n, rd(os.path.join(d, n)))
tf.close()
PY
"""


def pull_script(asg) -> str:
    four = {m: CT.prefix(m) for m in T1_FOUR}
    held = {m: CT.prefix(m) for m in asg["model_order"] if m not in T1_FOUR}
    txt = (PULL_SH.replace("__PREFIXES__", json.dumps(four)).replace("__HELD_PREFIXES__", json.dumps(held))
           .replace("__G4_ALL__", json.dumps(list(G4_ALL))).replace("__T1_CLONE__", T1_CLONE).replace("__S3_CLONE__", S3_CLONE))
    if re.search(r"1145\d", txt):
        raise Refused("the remote script would carry a Studio port")
    return txt


def read_manifest(p: Path) -> dict:
    out = {}
    for line in p.read_text().splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            out[name.strip()] = h
    return out


def check_copy(to: Path) -> dict:
    """The laptop's checks on a pulled copy (also run again by t1 and g4c): T1 files against the sha256 sent with
    them, G4 inputs against MANIFEST.sha256, the clone's assignment.toml equal to the repository's."""
    t1 = to / "t1"
    pull = json.loads((t1 / "PULL.json").read_text())
    for name, info in pull["files"].items():
        if sha256_file(t1 / name) != info["sha256"]:
            raise Refused(f"T1 copy: {name.split('/')[0]} file differs from the sha256 taken on the Studio")
    have = {f"results_v4/{p.name}" for p in (t1 / "results_v4").glob("*.json")}
    if have != {k for k in pull["files"] if k.startswith("results_v4/")}:
        raise Refused("T1 copy: the results files are not those PULL.json lists")
    if any(pull["held_model_files"].values()):
        raise Refused(f"T1: a held model has results files on the Studio: {pull['held_model_files']}")
    if (t1 / "assignment.toml").read_bytes() != CT.ASSIGNMENT.read_bytes():
        raise Refused("T1: the clone's assignment.toml differs from the repository's")
    g = to / "g4_inputs"
    man = read_manifest(g / "MANIFEST.sha256")
    n = 0
    for p in sorted((g / "runs").glob("*/*")):
        k = f"runs/{p.parent.name}/{p.name}"
        if man.get(k) != sha256_file(p):
            raise Refused(f"G4 inputs: {p.parent.name.split('__')[1]} {p.name} differs from its MANIFEST.sha256 line")
        n += 1
    return {"t1_files": len(pull["files"]), "g4_files_checked": n, "t1_clone_head": pull["clone_head"]}


def pull(to: Path) -> int:
    to = to.expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    to.mkdir(parents=True, exist_ok=True)
    asg = CT.load_assignment()
    script = pull_script(asg)
    stream = to / ".stream.tar"
    with open(stream, "wb") as fh:
        r = subprocess.run(SSH, input=script.encode(), stdout=fh, stderr=subprocess.PIPE)
    if r.returncode:
        stream.unlink(missing_ok=True)
        raise Refused(f"pull: ssh exit {r.returncode}: {r.stderr.decode(errors='replace').strip()[:300]}")
    with tarfile.open(stream, mode="r:") as tf:
        names = tf.getnames()
        bad = [x for x in names if not x.startswith(("t1/", "s3/", "g4_inputs/")) or ".." in x]
        if bad:
            raise Refused(f"pull: unexpected members in the stream: {bad[:3]}")
        tf.extractall(to, filter="data")
    stream.unlink()
    cut = {}
    for f in sorted(to.rglob("*.jsonl")):
        k = S463.cut_partial(f)
        if k:
            cut[str(f.relative_to(to))] = k
    t1rows, problems = {}, []
    for m in T1_FOUR:
        rows, pr = CT.answers(m, False, to / "t1" / "results_v4")
        t1rows[m] = len(rows)
        problems += pr
    if problems:
        raise Refused(f"pull: T1 results not readable (a file being rewritten?), pull again: {problems[:2]}")
    chk = check_copy(to)
    cmd = [sys.executable, str(GUARD), "collect", "--out", str(to / "s3" / "out_g4")]
    if (to / "s3" / "out_g4r38").is_dir():
        cmd += ["--replace", str(to / "s3" / "out_g4r38")]
    cmd += ["--set", "G4", "--dest", str(to / "g4_collect.jsonl")]
    c = guarded_run(cmd, cwd=ROOT)
    print((c.stdout + c.stderr).strip()[-600:])
    if c.returncode:
        raise Refused(f"collect refused (exit {c.returncode})")
    summary = {"pulled_utc": utc(), "from": STUDIO, "t1_rows": t1rows, "bytes_cut_after_the_last_whole_line": cut,
               "s3_clone_head": (to / "s3" / "HEAD.txt").read_text().strip(),
               "g4_inputs": (to / "g4_inputs" / "REALPATH.txt").read_text().strip(), **chk}
    (to / "PULL_SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"pulled into {to}: T1 stored answers {t1rows}; {chk['g4_files_checked']} G4 input files equal to their "
          f"MANIFEST lines; {len(cut)} partial last lines cut; collect into g4_collect.jsonl")
    return 0


# ---------------------------------------------------------------------------------------------------------------
# FROZEN COPY (D155): the pull of 26 October 18:30 (D150), frozen in findings/recompute/fig3_inputs and two tars; its
# S3 part (the collect, its sidecar, s3/) refrozen on 27 October with G4's final judging (D156, refreeze_fig3.py), the
# 26 October S3 part kept in findings/recompute/fig3_1026_inputs for S484's gate (2)
# ---------------------------------------------------------------------------------------------------------------
FROZEN_LABEL = ("frozen (D155, S3 part refrozen 27 October, D156): findings/recompute/fig3_inputs (g4_collect.jsonl, "
                "its sidecar, s3/, PULL_SUMMARY.json), fig3_t1.tar (t1/), fig3_g4_inputs.tar (g4_inputs/)")
FROZEN_LABEL_1026 = ("frozen (D155): findings/recompute/fig3_1026_inputs (the 26 October 18:30 S3 part: g4_collect.jsonl, "
                     "its sidecar, s3/, PULL_SUMMARY.json), fig3_g4_inputs.tar (g4_inputs/)")
FROZEN_SETS = {"fig3": FROZEN_LABEL, "fig3_1026": FROZEN_LABEL_1026}
FROZEN_TARS = {"t1": "fig3_t1", "g4_inputs": "fig3_g4_inputs"}         # pull folder -> tar stem (its top folder)
FROZEN_COMMITTED = ("g4_collect.jsonl", "g4_collect.jsonl.json", "s3", "PULL_SUMMARY.json")


class FrozenCopy:
    """The pull folder's layout (t1/, s3/, g4_inputs/, g4_collect.jsonl ...) over the frozen copy: copy / name gives
    the frozen path of that part; str() is FROZEN_LABEL, the copy's name in every header."""

    def __init__(self, parts: dict, label: str = FROZEN_LABEL):
        self.parts = parts
        self.label = label

    def __truediv__(self, name):
        if name not in self.parts:
            raise Refused(f"the frozen copy has no part {name!r}")
        return self.parts[name]

    def __str__(self):
        return self.label

    def expanduser(self):
        return self

    def resolve(self):
        return self


def frozen_copy(set_name: str = "fig3") -> FrozenCopy:
    """set_name "fig3": the copy Supplementary Figure 8 is drawn from; "fig3_1026": the 26 October S3 part with the same tars, the
    pull S484's gate (2) reproduces the scratch S-2 on (D156)."""
    parts = {name: S474.frozen_checked(set_name, name) for name in FROZEN_COMMITTED}
    for name, stem in FROZEN_TARS.items():
        try:
            parts[name] = fig_repro.frozen(stem, stem)
        except fig_repro.FrozenInputError as e:
            raise Refused(str(e)) from e
    return FrozenCopy(parts, FROZEN_SETS[set_name])


def frozen_shas(copy: FrozenCopy, committed=("g4_collect.jsonl", "g4_collect.jsonl.json", "s3"),
                tars=("t1", "g4_inputs")) -> dict:
    """{name: sha256} of the frozen inputs a step reads: every committed file by its repository path, and each tar
    by its name (fig_repro checked the tar against SHA256SUMS before extracting it, and checks every extracted file
    against the tar's record on each call)."""
    out = {}
    for name in committed:
        p = copy / name
        for f in ([p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())):
            out[f.resolve().relative_to(ROOT).as_posix()] = sha256_file(f)
    sums = S474.read_sums()
    for name in tars:
        t = FROZEN_TARS[name] + ".tar"
        out[t] = sums[t]
    return out


def check_frozen_record(new: dict, committed_header: Path, legacy) -> str:
    """Refuse when the frozen inputs' sha256 differ from what the committed header recorded. A header written
    before the record existed is checked by legacy(header) instead (fields the old header holds)."""
    if not committed_header.exists():
        raise Refused(f"{rel(committed_header)} is missing: nothing to reproduce against")
    h = json.loads(committed_header.read_text())
    rec = h.get("frozen_inputs_sha256")
    if rec is not None:
        if rec != new:
            diff = sorted(k for k in set(rec) | set(new) if rec.get(k) != new.get(k))
            raise Refused(f"frozen inputs differ from those {rel(committed_header)} recorded ({len(diff)}): {diff[:3]}")
        return f"{len(new)} sha256 equal to {rel(committed_header)}"
    bad = legacy(h)
    if bad:
        raise Refused(f"frozen inputs differ from {rel(committed_header)}: {bad[:3]}")
    return f"{rel(committed_header)} holds no frozen_inputs_sha256 yet; its recorded fields equal"


# ---------------------------------------------------------------------------------------------------------------
# T1 -> findings/recompute/T1_L2
# ---------------------------------------------------------------------------------------------------------------
B_CAP_COLS = ["model", "cap", "questions_complete", "answers", "median_pct", "mean_pct", "ci95_lo_pct", "ci95_hi_pct",
              "failed", "cap_reached_n", "stopped_by_cap_n"]
A_BOX_COLS = ["median_pct", "q1_pct", "q3_pct", "min_pct", "max_pct"]   # A-1's boxes, on a's 'cap' rows
D_COLS = ["cap_reached_n", "cap_reached_pct", "stopped_by_cap_n", "stopped_by_cap_pct"]   # the strip under a
RANGE_COLS = ["draws_read", "draw_min_pct", "draw_max_pct", "range_pp"]           # the range strip's 'draw_range' rows ("questions" is S475's)
# D286 (Valerio, 6 Nov, tab "O1"): a's 'paired_test' rows, one per cap and one 'paired_test_combined' (cap blank): RLM
# minus Zhang RLM per question, paired on the same questions (exploratory: specified after the data were seen)
TEST_COLS = ["d_pp", "d_ci95_lo_pp", "d_ci95_hi_pp", "p_signflip_two_sided", "p_holm", "rlm_higher", "zhang_higher",
             "tied"]
A_COLS = S475.A_COLS + A_BOX_COLS + D_COLS + RANGE_COLS + TEST_COLS
GEMINI_REF_NAME = "gemini-3-flash-preview (RLM, G5, mean of draws 1 to 3; failed and cap counts draw 1)"   # D284: gemini_ref medians and means are over each question's three-draw mean; its counts read draw 1
# D291 (Valerio, 7 Nov): plates and legends print the paper's name for the generator; data, keys and Source Data keep
# the API id gemini-3-flash-preview
GEN_DISPLAY = "gemini-3-flash"
B_COLS = ["row"] + B_CAP_COLS + ["question_id", "in_complete_question", "recall_pct", "recall_loose_pct",
                                 "recall_exact_pct",
                                 "stop_reason", "turns_used", "answer_key"]


def t1_rows(copy: Path, key: dict, asg=None) -> tuple[list, dict]:
    """Every stored T1 answer of the four models, scored, and the checks' summary."""
    asg = asg or CT.load_assignment()
    chk = check_copy(copy) if (copy / "g4_inputs").is_dir() else None
    t1 = copy / "t1"
    if chk is None:                                     # a fixture holds T1 only
        pull = json.loads((t1 / "PULL.json").read_text())
        for name, info in pull["files"].items():
            if sha256_file(t1 / name) != info["sha256"]:
                raise Refused(f"T1 copy: {name.split('/')[0]} file differs from the sha256 taken on the Studio")
        if any(pull["held_model_files"].values()):
            raise Refused(f"T1: a held model has results files: {pull['held_model_files']}")
    pull = json.loads((t1 / "PULL.json").read_text())
    models = [m for m in asg["model_order"] if m not in CT.HELD]
    if tuple(models) != T1_FOUR:
        raise Refused(f"assignment.toml model_order less check_t1.HELD is {models}, not D121's four {T1_FOUR}")
    results = t1 / "results_v4"
    order = CT.cells(asg, 1)
    have, extra, problems = CT.stored_cells(asg, 1, results)
    log = [r for r in CT.read_jsonl(t1 / "interleaved_walk.jsonl") if r.get("draw", 1) == 1]
    held_now = [m for m in asg["model_order"] if m in CT.HELD]
    p, s = CT.interleave_problems(order, have, log, held_now)
    if problems or p or extra:
        raise Refused(f"T1 order check: {(problems + p)[:3]}, {extra} keys outside the order")
    ends = {tuple(r["cell"]) for r in log if r.get("action") == "end" and r.get("rc") == 0 and r.get("stored") is True}
    if have != ends:
        raise Refused(f"T1: {len(have)} stored cells, {len(ends)} walk 'end' records with rc 0 and stored true; "
                      f"stored not ended {sorted(have - ends)[:2]}, ended not stored {sorted(ends - have)[:2]}")
    complete = list(s["complete_questions"])
    rows = []
    for m in models:
        stored, pr = CT.answers(m, False, results)
        if pr:
            raise Refused(f"T1 {m}: {pr[:2]}")
        for (q, c, mm, d) in order:
            if mm != m or (q, c, mm, d) not in have:
                continue
            k = CT.ex.answer_key(f"rlm_{c}", q, d)
            r = stored[k]
            rlm = r.get("rlm") or {}
            if (r.get("question_id"), r.get("depth"), r.get("draw"), rlm.get("max_turns"), r.get("model")) != \
                    (q, c, d, c, CT.LOCAL + m):
                raise Refused(f"T1 {m} {k}: its row says {r.get('question_id')}, depth {r.get('depth')}, draw "
                              f"{r.get('draw')}, max_turns {rlm.get('max_turns')}, model {r.get('model')}")
            ans = r.get("answer") or ""
            status = S474.status_of(ans, r.get("error"))
            failed = status == "error"
            try:
                sc = S474.score(ans, key["questions"][q]["expected_concepts"], rlm.get("turn_limit_note"))
            except Exception as e:                       # noqa: BLE001  turn_limit_note.NoteMismatch
                raise Refused(f"T1 {m} {k}: the flagged turn-limit note is not where the record says ({e})")
            turns = rlm.get("turns")
            rows.append({"model": m, "cap": c, "question_id": q, "draw": d, "answer_key": k,
                         "run_id": r.get("run_id"), "status": status, "failed": failed,
                         "error_kind": CT.error_kind(r), "stop_reason": r.get("stop_reason"), "turns_used": turns,
                         "turn_limit_note": rlm.get("turn_limit_note"), "note_removed": sc["note_removed"],
                         "answer_sha256": S470.sha256_text(ans), "n_concepts": sc["n_concepts"],
                         "found_loose": sc["found_loose"], "found_exact": sc["found_exact"],
                         "text_recall_loose": sc["concept_recall_loose"],
                         "text_recall_exact": sc["concept_recall_exact"],
                         "concept_recall_loose": 0.0 if failed else sc["concept_recall_loose"],
                         "concept_recall_exact": 0.0 if failed else sc["concept_recall_exact"],
                         "cap_reached": turns is not None and turns >= c,
                         "stopped_by_cap": r.get("stop_reason") in S474.CAP_STOPS["G5"],
                         "in_complete_question": q in complete})
    info = {"stored_cells": len(have), "cells_in_order": len(order), "front_g": s["front_g"], "k_per_model": s["k"],
            "complete_questions": complete, "held_now": held_now, "walk_records": len(log),
            "walk_end_records_stored": len(ends), "clone_head": pull["clone_head"], "taken_utc": pull.get("taken_utc"),
            "files": sorted(({"model": v.get("model"), "sha256": v["sha256"], "bytes": v["bytes"],
                              "studio_mtime": v.get("mtime")} for k, v in pull["files"].items()
                             if k.startswith("results_v4/")), key=lambda x: (x["model"], x["studio_mtime"] or 0)),
            "walk_log_sha256": pull["files"]["interleaved_walk.jsonl"]["sha256"],
            "assignment_sha256": pull["files"]["assignment.toml"]["sha256"]}
    return rows, info


def t1_tables(rows: list, models, caps, complete, field: str = "concept_recall_loose") -> dict:
    """Per model and cap, over the complete questions: the mean of field (T1_L2: concept_recall_loose; T1_L2_d181,
    D188: concept_recall), its Rule 2 interval, failed, cap reached and stopped by the cap."""
    qs = sorted(complete)
    k = len(qs)
    out = {"k": k, "complete_questions": qs, "models": list(models), "caps": list(caps), "cells": []}
    for m in models:
        for c in caps:
            R = {r["question_id"]: r for r in rows if r["model"] == m and r["cap"] == c and r["in_complete_question"]}
            if set(R) != set(qs):
                raise Refused(f"T1 {m} cap {c}: the complete questions {qs} are not all stored")
            vals = [R[q][field] for q in qs]
            mean = float(np.mean(vals)) if k else None
            ci = S463.interval(vals, [1.0] * k) if k >= 2 else None
            out["cells"].append({"model": m, "cap": c, "questions_complete": k, "answers": k, "mean": mean,
                                 "ci95": ci, "failed": sum(R[q]["failed"] for q in qs),
                                 "cap_reached_n": sum(R[q]["cap_reached"] for q in qs),
                                 "stopped_by_cap_n": sum(R[q]["stopped_by_cap"] for q in qs)})
    return out


def t1_build(copy: Path, outdir: Path, asg=None, gate=True, committed_header: Path | None = None) -> dict:
    """committed_header: a frozen rebuild (D155), refused unless the frozen inputs are those it recorded."""
    key = S470.the_key()
    g = S474.gate(key) if gate else {"reproduced": "skipped (fixture)"}
    asg = asg or CT.load_assignment()
    rows, info = t1_rows(copy, key, asg)
    tables = t1_tables(rows, T1_FOUR, asg["depths"], info["complete_questions"])
    shas, checked = None, None
    if committed_header is not None:
        shas = frozen_shas(copy, committed=(), tars=("t1", "g4_inputs"))

        def legacy(h):
            i = h.get("inputs") or {}
            return [k for k in ("files", "walk_log_sha256", "assignment_sha256", "clone_head", "taken_utc")
                    if i.get(k) != info.get(k)]
        checked = check_frozen_record(shas, committed_header, legacy)
    header = {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)), "provisional": True,
              "command": (f"uv run --frozen python {SCRIPT} rebuild" if shas is not None
                          else f"uv run --frozen python {SCRIPT} t1 --copy <copy>"), "copy": str(copy),
              "frozen_inputs_sha256": shas,
              "what": "T1 (D97, D118, D121): every stored draw-1 answer of the four local models, concept recall on "
                      "the loose matcher (S474.score, provisional until P2's labels choose the matcher, D17), a "
                      "failed answer 0 (Rule 10); per model and cap the mean over the questions every model not held "
                      "stored at every cap (D118)",
              "key": {"path": key["path"], "sha256": key["sha256"], "version": key["version"]}, "gate": g,
              "matcher_sha256": {"concept_recall_loose (source)": S470.source_sha(
                  S474.concept_match_loose.concept_recall_loose), "scripts/S474_l2_concept_recall.py":
                  sha256_file(ROOT / "scripts" / "S474_l2_concept_recall.py")},
              "inputs": info, "models": list(T1_FOUR), "caps": list(asg["depths"]),
              "question_order": list(asg["question_order"]), "rows": len(rows), "k": tables["k"],
              "seed": SEED, "n_boot": N_BOOT,
              "names": "results file names hold the server and the time; written here by sha256 only (machine guards)"}
    write_files(outdir, {"concept_recall.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                         "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n",
                         "cap_tables.json": json.dumps(tables, indent=1, sort_keys=True) + "\n"})
    return {"rows": len(rows), "k": tables["k"], "gate": g["reproduced"],
            "per_model": dict(collections.Counter(r["model"] for r in rows)),
            "failed": sum(r["failed"] for r in rows), "frozen_check": checked}


# ---------------------------------------------------------------------------------------------------------------
# G4 -> findings/recompute/G4_fig3c
# ---------------------------------------------------------------------------------------------------------------
def index_parts(idx: str) -> tuple[int, int]:
    m = re.fullmatch(r"exp_v4_s(\d+)_n(\d+)", idx)
    if not m:
        raise Refused(f"index name {idx!r} is not exp_v4_s<core>_n<ratio>")
    return int(m.group(1)), int(m.group(2))


COVERED_WANT = {5: 22, 10: 44, 20: 86, 50: 86}   # D126: the common 86 an index of N core papers can answer
G4_RATIOS = (0, 1, 3)                             # G4's distractor ratios, three indexes per core size (12 in all)
# D161 (9) N9: G6's planned answers are its draws x a's questions x a's caps; 3 is experiments/draws.csv's draws on
# both G6 rows ("Package RLM at caps 5 10 20", "Package RLM depth caps"; D78 Q116, D98 keeps Figure 2's three
# full draws), the 2,580 of S459's "10 caps x 86 x 3" (scripts/S476_fig3_d123_test.py checks it against draws.csv)
G6_DRAWS = 3


def c_planned() -> int:
    """D160 (15) S1: c's planned answers from G4's design, the draw-1 answers its cells can hold: the six strategies
    on each index's covered questions (D126), each core size's COVERED_WANT x G4_RATIOS' three indexes (4,284)."""
    from experiments.runner import experiment as ex
    if tuple(sorted(COVERED_WANT)) != tuple(ex.SCALING_CORE_SIZES):
        raise Refused(f"COVERED_WANT's sizes {sorted(COVERED_WANT)} are not G4's {ex.SCALING_CORE_SIZES}")
    return len(G4_ALL) * len(G4_RATIOS) * sum(COVERED_WANT[c] for c in ex.SCALING_CORE_SIZES)


def c_drawn(rows6: list, grid: dict) -> set:
    """c's answers drawn: each answer (strategy, index, question) that enters a complete cell's pairing once, single
    pass's counted once per index however many strategies it is paired with (D150)."""
    done = {(e["index"], e["strategy"]) for e in grid["cells"] if e["complete"]}
    out = set()
    for r in rows6:
        if not r["covered"]:
            continue
        for s_ in GRID_STRATS:
            if (r["index"], s_) in done and r["cells"][s_]["pass4"] is not None and \
                    r["cells"]["single_pass"]["pass4"] is not None:
                out |= {(s_, r["index"], r["question_id"]), ("single_pass", r["index"], r["question_id"])}
    return out


def over_plan(drawn: dict, planned: dict) -> list:
    """D161 (9) N9: each panel (a by system) whose answers drawn exceed its planned answers, as text; [] when none."""
    if set(drawn) != set(planned):
        return [f"the panels drawn {sorted(drawn)} are not the panels planned {sorted(planned)}"]
    return [f"{p} draws {drawn[p]} answers, {planned[p]} planned" for p in sorted(planned) if drawn[p] > planned[p]]


def paper_number(source_file: str) -> int:
    """A source paper's number from its file name, '01_sarek.pdf' -> 1 (create_indexes.py _get_all_core_papers)."""
    m = re.match(r"(\d+)_", source_file)
    if not m:
        raise Refused(f"source file {source_file!r} has no paper number before its first underscore")
    return int(m.group(1))


def covered_set(key_questions: dict, core: int, among) -> set:
    """D126: the questions of `among` an index of `core` core papers can answer, those whose source papers (the D5
    key's source_files) are all among the index's core papers. An index of N core papers holds papers 01 to N
    (recovered_harness/tests/experiments_v4/create_indexes.py:79-87, 182-215: CORE_5_IDS, CORE_10_IDS, CORE_20_IDS
    and, at 50, every core paper, papers[:50])."""
    out = set()
    for q in among:
        files = key_questions[q].get("source_files") or []
        if not files:
            raise Refused(f"{q}: the D5 key gives no source_files")
        if all(paper_number(f) <= core for f in files):
            out.add(q)
    return out


def coverage_check(key_questions: dict, common_answerable: set) -> dict:
    """Reproduce before use: each index's covered set has COVERED_WANT's count and equals the per-size answerable
    questions (experiments/runner/experiment.py scaling_questions, the Q55 rule min_core <= N) restricted to the
    common answerable set. Returns {core: sorted covered ids}."""
    from experiments.runner import experiment as ex
    if tuple(sorted(COVERED_WANT)) != tuple(ex.SCALING_CORE_SIZES):
        raise Refused(f"COVERED_WANT's sizes {sorted(COVERED_WANT)} are not G4's {ex.SCALING_CORE_SIZES}")
    out = {}
    for core in ex.SCALING_CORE_SIZES:
        cov = covered_set(key_questions, core, common_answerable)
        per = {q["id"] for q in ex.scaling_questions(core)["per_size"] if q["answerable"]} & set(common_answerable)
        if cov != per:
            raise Refused(f"{core} core papers: the questions whose source papers are all in the index "
                          f"({len(cov)}) are not the per-size answerable ones among the common set ({len(per)}); "
                          f"differ {sorted(cov ^ per)[:3]}")
        if len(cov) != COVERED_WANT[core]:
            raise Refused(f"{core} core papers: {len(cov)} common answerable questions covered, not "
                          f"{COVERED_WANT[core]} (D126)")
        out[core] = sorted(cov)
    return out


def read_g4r38(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            run_id, idx, cfg, q, draw, stop, code = line.split("|")
            out[f"{idx}|{cfg}|{q}|d{int(draw.lstrip('d'))}"] ={"config": cfg, "stop": stop, "http": code, "run_id": run_id}
    return out


def judge_rows(folder: Path) -> dict:
    """ident (run_id, config, question, draw) -> the latest row of a judge folder (judge_passages.ident's rule)."""
    out = {}
    f = folder / ("judge_" + "passages.jsonl")
    if f.exists():
        for x in f.read_text().splitlines():
            if x.strip():
                d = json.loads(x)
                out[(d.get("run_id"), d["config"], d["question_id"], d["draw"])] = d
    return out


def g4_cells(copy: Path, g4r38_path: Path = G4R38_KEYS, g4r38_want=G4R38_WANT,
             configs=G4_CONFIGS, hold_g4r38: bool = False) -> tuple[list, dict]:
    """hold_g4r38 (D156): every G4R38 key held out as if its rerun were not judged, the reading D149's anchor was
    drawn from; the default reads the judged reruns (the drawn reading)."""
    from experiments.scorers import records
    from experiments.runner import experiment as ex
    inp = copy / "g4_inputs"
    copyj = json.loads((inp / "COPY.json").read_text())
    man = read_manifest(inp / "MANIFEST.sha256")
    lines_want = copyj["answer_lines"]
    indexes = sorted({k.split("__")[2] for k in lines_want if k.split("__")[1] == "rlm_10"},
                     key=index_parts)
    if len(indexes) != 12 or {index_parts(i) for i in indexes} != {(c, r) for c in (5, 10, 20, 50) for r in G4_RATIOS}:
        raise Refused(f"COPY.json names {len(indexes)} rlm_10 indexes, not the 12 of 5, 10, 20, 50 x 0, 1, 3")
    common_answerable = {q["id"] for q in ex.questions() if records.group_of(q["id"]) == "answerable"}
    covered = coverage_check(S470.the_key()["questions"], common_answerable)     # D126
    g4r38 = read_g4r38(g4r38_path)
    out_g4 = copy / "s3" / "out_g4"
    out_r38 = copy / "s3" / "out_g4r38"
    claims = [x for x in (out_g4 / "claims.txt").read_text().splitlines() if x.strip()]
    r38_judged = set()
    if out_r38.is_dir():
        for fo in sorted((out_r38 / "judge").glob("*")):
            r38_judged |= {d.get("answer_key") for d in judge_rows(fo).values()}
    judged_used = set() if hold_g4r38 else r38_judged
    collect = {}
    for x in (copy / "g4_collect.jsonl").read_text().splitlines():
        if x.strip():
            d = json.loads(x)
            if d["config"] in configs:
                if d.get("answer_key") in collect:
                    raise Refused(f"collect: {d.get('answer_key')} twice")
                collect[d["answer_key"]] = d
    side = copy / "g4_collect.jsonl.json"
    side_j = json.loads(side.read_text()) if side.exists() else {}
    answers, units, probs = {}, {}, []
    for cfg in configs:
        for idx in indexes:
            run = G4_RUN.format(config=cfg, index=idx)
            f = inp / "runs" / run / "answers.jsonl"
            if not f.exists() or man.get(f"runs/{run}/answers.jsonl") != sha256_file(f):
                raise Refused(f"G4 inputs: {cfg} {idx} answers missing or not its MANIFEST line")
            L = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
            if len(L) != lines_want.get(run):
                raise Refused(f"G4 inputs: {cfg} {idx} holds {len(L)} answer lines, COPY.json {lines_want.get(run)}")
            for a in L:
                if a["answer_key"] != f"{idx}|{cfg}|{a['question_id']}|d{a['draw']}" or a["config"] != cfg \
                        or a["index_name"] != idx:
                    raise Refused(f"G4 inputs: {a['answer_key']} in {cfg} {idx}: key, config or index differ")
                if a["answer_key"] in answers:
                    raise Refused(f"G4 inputs: {a['answer_key']} twice")
                answers[a["answer_key"]] = a
            failed_nj = [a for a in L if (a["generation"].get("error") or not (a["generation"].get("answer") or "")
                                          .strip())]
            fo = out_g4 / "judge" / run
            jr = judge_rows(fo)
            claimed = [c for c in claims if c.endswith("__" + run)]
            summ_f = fo / ("judge_" + "passages_summary.json")
            summ = json.loads(summ_f.read_text()) if summ_f.exists() else None
            d1 = [d for d in jr.values() if d["draw"] == 1]
            complete = not claimed and summ is not None and len(d1) + len(failed_nj) == len(L)
            if complete:
                sd = set(summ.get("draws") or [])
                got = collections.Counter(d["a"]["status"] for d in jr.values() if d["draw"] in sd)
                if dict(got) != summ.get("status_a", {}) or summ.get("rows") != sum(got.values()):
                    raise Refused(f"S3 {cfg} {idx}: the rows' (a) status counts {dict(got)} are not the summary's "
                                  f"{summ.get('status_a')}")
            units[(cfg, idx)] = {"complete": complete, "claimed": bool(claimed), "summary": summ is not None,
                                 "judged_rows_d1": len(d1), "failed_not_judged": len(failed_nj),
                                 "answer_lines": len(L)}
    # every judged row of these configs is an answer of the copy, on the answerable prompt where Rule 8 says so,
    # under the lock of D88, and one run_sha256
    runs_sha = collections.Counter(d.get("run_sha256") for d in collect.values())
    if len(runs_sha) > 1:
        raise Refused(f"collect: {len(runs_sha)} run_sha256 values")
    for k, d in collect.items():
        a = answers.get(k)
        if a is None:
            raise Refused(f"collect: judged row {k} is not an answer of the copied inputs")
        if bool(d.get("answerable_prompt")) != (records.group_of(d["question_id"]) != "not_answerable"):
            raise Refused(f"collect: {k} judged on the wrong prompt for Rule 8's group")
        if d.get("lock_sha256") not in LOCKS_OK:
            raise Refused(f"collect: {k} under lock {str(d.get('lock_sha256'))[:8]}, not d66daa28 or a lock equal to it (D205)")
    # G4R38: the listed keys of these configs are failures in the inputs, stored as call_error
    r38 = {k: v for k, v in g4r38.items() if v["config"] in configs}
    by_cfg = collections.Counter(v["config"] for v in r38.values())
    if g4r38_want is not None and {c: by_cfg.get(c, 0) for c in configs} != g4r38_want:
        raise Refused(f"g4r38_keys.txt lists {dict(by_cfg)} keys of {', '.join(configs)}, not {g4r38_want}")
    for k, v in r38.items():                      # the stop reason g4r38_keys.txt lists (call_error, or error for the
        a = answers.get(k)                        # one verified_pass answer, G4 README "G4R38")
        if a is None or not a["generation"].get("error") or a["generation"].get("stop_reason") != v["stop"]:
            raise Refused(f"G4R38 key {k} is not a {v['stop']} failure in the inputs")
    # the cells
    cells = []
    for idx in indexes:
        core, ratio = index_parts(idx)
        qrows = {}
        for cfg in configs:
            for a in answers.values():
                if a["index_name"] != idx or a["config"] != cfg or a["draw"] != 1:
                    continue
                q = a["question_id"]
                sets = a.get("question_sets") or []
                if records.group_of(q) != "answerable" or not ({"common", "per_size"} & set(sets)):
                    continue
                k = a["answer_key"]
                gen = a["generation"]
                cell = {"status": None, "correctness": None, "pass3": None, "pass4": None, "failed": False}
                if k in r38 and k not in judged_used:
                    cell["status"] = "held_g4r38"
                elif k not in r38 and (gen.get("error") or not (gen.get("answer") or "").strip()):
                    cell.update(status="failed", pass3=0, pass4=0, failed=True)
                else:
                    d = collect.get(k)
                    if d is None:
                        if units[(cfg, idx)]["complete"]:
                            raise Refused(f"S3: {k} answered and not judged in a complete unit")
                        cell["status"] = "not_judged"
                    else:
                        st = d["a"]["status"]
                        if st == "ok":
                            c = (d["a"].get("scores") or {}).get("correctness")
                            if not isinstance(c, (int, float)):
                                raise Refused(f"S3: {k} (a) ok without a correctness score")
                            cell.update(status="ok", correctness=c, pass3=int(c >= PASS3), pass4=int(c >= PASS4))
                        elif st in JUDGE_FAILED:
                            cell["status"] = "unscored"
                        elif st == "no_answer":
                            cell.update(status="failed", pass3=0, pass4=0, failed=True)
                        else:
                            raise Refused(f"S3: {k} (a) status {st!r}")
                row = qrows.setdefault(q, {"index": idx, "core_papers": core, "distractor_ratio": ratio,
                                           "question_id": q, "common": "common" in sets,
                                           "covered": "common" in sets and q in covered[core],
                                           "per_size": "per_size" in sets, "cells": {}})
                if row["common"] != ("common" in sets) or row["per_size"] != ("per_size" in sets):
                    raise Refused(f"G4 {idx} {q}: the two configs carry different question_sets")
                row["cells"][cfg] = cell
        com = {q for q, r in qrows.items() if r["common"]}
        if com != common_answerable:
            probs.append(f"{idx}: the common set's answerable questions are {len(com)}, not Rule 8's 86")
        for q in sorted(qrows):
            r = qrows[q]
            if set(r["cells"]) != set(configs):
                raise Refused(f"G4 {idx} {q}: answered by {sorted(r['cells'])} only")
            r["both_units_complete"] = all(units[(c, idx)]["complete"] for c in configs)
            cells.append(r)
    if probs:
        raise Refused("; ".join(probs[:3]))
    info = {"indexes": indexes, "units": {f"{c} {i}": v for (c, i), v in units.items()},
            "claims": claims, "collect_rows_rlm10_sp": len(collect), "run_sha256": next(iter(runs_sha), None),
            "collect_sidecar": {k: side_j.get(k) for k in ("rows", "run_sha256", "replaced", "added_by_replace",
                                                            "status_a")},
            "g4r38_keys": {c: by_cfg.get(c, 0) for c in configs}, "g4r38_judged": len(r38_judged & set(r38)),
            "g4r38_judged_keys": sorted(r38_judged & set(r38)),
            "reading": ("G4R38 reruns held out (D156: the reading D149's anchor gates)" if hold_g4r38
                        else "G4R38 reruns judged (D156: the reading drawn)"),
            "out_g4r38": out_r38.is_dir(), "copy": copyj.get("copied"), "copy_from": copyj.get("from"),
            "answer_lines": {G4_RUN.format(config=c, index=i): units[(c, i)]["answer_lines"]
                             for c in configs for i in indexes},
            "common_answerable": len(common_answerable),
            "covered": {str(c): len(v) for c, v in covered.items()},
            "covered_how": "D126: of the common set's answerable questions, those whose source papers (the D5 key's "
                           "source_files) are all among the index's core papers 01 to N; equal to the per-size "
                           "answerable questions restricted to the common set (coverage_check)"}
    return cells, info


def g4_point(rows: list, which: str = "pass3", drop_failed: bool = False, set_name: str = "covered") -> dict:
    """d, its interval, the sign-flip P and the counts over the questions of one index with both cells present."""
    pairs = []
    for r in sorted(rows, key=lambda x: x["question_id"]):
        if not r[set_name]:
            continue
        a, b = r["cells"]["rlm_10"], r["cells"]["single_pass"]
        if a[which] is None or b[which] is None or (drop_failed and (a["failed"] or b["failed"])):
            continue
        pairs.append(a[which] - b[which])
    n = len(pairs)
    if not n:
        return {"questions_paired": 0, "d_pp": None, "ci95_pp": None, "p_signflip": None, "helped": 0, "harmed": 0,
                "equal": 0}
    ci = S463.interval(pairs, [1.0] * n)
    return {"questions_paired": n, "d_pp": 100 * float(np.mean(pairs)), "ci95_pp": [100 * ci[0], 100 * ci[1]],
            "p_signflip": S463.signflip_p(pairs), "helped": sum(x > 0 for x in pairs),
            "harmed": sum(x < 0 for x in pairs), "equal": sum(x == 0 for x in pairs)}


def g4_tables(cells: list, indexes) -> dict:
    out = {"seed": SEED, "n_boot": N_BOOT, "points": []}
    for idx in indexes:
        core, ratio = index_parts(idx)
        R = [r for r in cells if r["index"] == idx]
        drawn = bool(R) and all(r["both_units_complete"] for r in R)
        counts = {cfg: collections.Counter(r["cells"][cfg]["status"] for r in R if r["covered"]) for cfg in G4_CONFIGS}
        counts86 = {cfg: collections.Counter(r["cells"][cfg]["status"] for r in R if r["common"])
                    for cfg in G4_CONFIGS}
        pt = {"index": idx, "core_papers": core, "distractor_ratio": ratio, "both_units_complete": drawn,
              "drawn": False, "covered_questions": sum(r["covered"] for r in R),
              "counts": {c: dict(v) for c, v in counts.items()},
              "counts_common86": {c: dict(v) for c, v in counts86.items()}}
        if drawn:                                    # D126: the drawn pairing is the covered set
            # "main" is the reading at score 3 (g4_point's default which="pass3"), named before D154 made score 4 the
            # pass rate; "threshold4" is score 4. The keys are kept: renaming them would change the committed
            # point_tables.json (audit 27 Oct F6, fig3_supp4_20); its readers use it as score 3 (grid_gate) or for the
            # paired-question count, the same at both scores.
            main = g4_point(R, set_name="covered")
            pt.update(main=main, threshold4=g4_point(R, "pass4", set_name="covered"),
                      failed_left_out=g4_point(R, drop_failed=True, set_name="covered"),
                      common86=g4_point(R, set_name="common"), per_size=g4_point(R, set_name="per_size"),
                      drawn=main["questions_paired"] > 0)
        out["points"].append(pt)
    return out


def grid_point(rows, strat, which):
    """D150: one cell of panel c, strat minus single pass over the covered questions (D126) with both cells present;
    the same pairing, order and interval as g4_point, so RLM-10's cell is g4_point's reading exactly."""
    pairs = []
    for r in sorted(rows, key=lambda x: x["question_id"]):
        if not r["covered"]:
            continue
        a, b = r["cells"][strat][which], r["cells"]["single_pass"][which]
        if a is None or b is None:
            continue
        pairs.append((a, b))
    n = len(pairs)
    if not n:
        return {"n_paired": 0}
    diffs = [a - b for a, b in pairs]
    ci = S463.interval(diffs, [1.0] * n)
    return {"n_paired": n, "pass_strategy_pct": 100 * sum(a for a, _ in pairs) / n,
            "pass_single_pass_pct": 100 * sum(b for _, b in pairs) / n, "d_pp": 100 * float(np.mean(diffs)),
            "ci95_pp": [100 * ci[0], 100 * ci[1]], "p_signflip": S463.signflip_p(diffs)}


def grid_tables(cells, indexes, units) -> dict:
    """D150: every strategy against single pass on every index, at judge score 3 and 4. A cell is drawn when both
    units (the strategy's and single pass's on that index) are complete (g4_cells' rule)."""
    out = {"seed": SEED, "n_boot": N_BOOT, "cells": []}
    by_idx = collections.defaultdict(list)
    for r in cells:
        by_idx[r["index"]].append(r)
    for score, which in ((3, "pass3"), (4, "pass4")):
        for strat in GRID_STRATS:
            for idx in indexes:
                core, ratio = index_parts(idx)
                complete = bool(units[f"{strat} {idx}"]["complete"] and units[f"single_pass {idx}"]["complete"])
                e = {"score": score, "index": idx, "core_papers": core, "distractor_ratio": ratio, "strategy": strat,
                     "complete": complete}
                if complete:
                    e.update(grid_point(by_idx[idx], strat, which))
                    if not e["n_paired"]:
                        raise Refused(f"c {strat} {idx} score {score}: complete with no paired question")
                out["cells"].append(e)
    return out


HELD_CELL = {"status": "held_g4r38", "correctness": None, "pass3": None, "pass4": None, "failed": False}


def hold_rows(rows: list, keys) -> list:
    """D156: the rows with each listed G4R38 key's cell held out, as g4_cells holds a key whose rerun is not judged
    (HELD_CELL); every other cell unchanged. A listed cell already held is refused: the rows are not the judged
    reading. keys: answer keys index|config|question|d1 (draw 1, the only draw of the rows)."""
    keys = set(keys)
    out = copymod.deepcopy(rows)
    for r in out:
        for cfg in r["cells"]:
            if f"{r['index']}|{cfg}|{r['question_id']}|d1" in keys:
                if r["cells"][cfg]["status"] == "held_g4r38":
                    raise Refused(f"G4R38 key {r['index']}|{cfg}|{r['question_id']}|d1 is held in the judged reading")
                r["cells"][cfg] = dict(HELD_CELL)
    return out


def read_anchor(path: Path = ANCHOR) -> dict:
    a = json.loads(path.read_text())
    if a.get("from_commit") != ANCHOR_FROM[0] or not a.get("points"):
        raise Refused(f"{rel(path)} is not D149's RLM-10 reading")
    return a


def grid_gate(cells2, tab2, cells6, grid, anchor) -> dict:
    """D150, reproduce before drawing: (1) the six-strategy cells of rlm_10 and single pass equal the two-strategy
    cells question by question; (2) the grid's RLM-10 cells equal g4_point's reading of the same copy (n, d, interval,
    sign-flip P at 3 and 4); (3) they equal D149's committed Source Data (anchor_d149_rlm10.json), when an anchor is
    given. Any difference refuses (exit 2)."""
    bad, n = [], 0
    six = {(r["index"], r["question_id"]): r for r in cells6}
    if len(six) != len(cells2):
        bad.append(f"{len(six)} question rows with six strategies, {len(cells2)} with two")
    for r in cells2:
        s = six.get((r["index"], r["question_id"]))
        n += 1
        if s is None or s["covered"] != r["covered"] or any(s["cells"][c] != r["cells"][c] for c in G4_CONFIGS):
            bad.append(f"{r['index']} {r['question_id']}: the six-strategy cells differ from the two-strategy ones")
    pts = {p["index"]: p for p in tab2["points"]}
    tol = 1e-9

    def cmp(what, a, b):
        nonlocal n
        n += 1
        if a is None or b is None or abs(float(a) - float(b)) > tol:
            bad.append(f"{what}: {a} against {b}")
    for e in grid["cells"]:
        if e["strategy"] != "rlm_10":
            continue
        p = pts[e["index"]]
        if e["complete"] != p["drawn"]:
            bad.append(f"{e['index']}: grid complete {e['complete']}, two-strategy drawn {p['drawn']}")
            continue
        if not e["complete"]:
            continue
        ref = p["main"] if e["score"] == 3 else p["threshold4"]
        w = f"RLM-10 {e['index']} score {e['score']}"
        cmp(w + " n", e["n_paired"], ref["questions_paired"])
        cmp(w + " d", e["d_pp"], ref["d_pp"])
        cmp(w + " lo", e["ci95_pp"][0], ref["ci95_pp"][0])
        cmp(w + " hi", e["ci95_pp"][1], ref["ci95_pp"][1])
        cmp(w + " P", e["p_signflip"], ref["p_signflip"])
        if anchor is not None:
            ap = anchor["points"].get(e["index"])
            s = str(e["score"])
            if ap is None:
                bad.append(f"{e['index']}: not in the anchor")
                continue
            cmp(w + " n (D149)", e["n_paired"], ap["n" + s])
            cmp(w + " d (D149)", e["d_pp"], ap["d" + s])
            cmp(w + " lo (D149)", e["ci95_pp"][0], ap["lo" + s])
            cmp(w + " hi (D149)", e["ci95_pp"][1], ap["hi" + s])
            cmp(w + " P (D149)", e["p_signflip"], ap["p" + s])
    if anchor is not None and sorted(anchor["points"]) != sorted(i for i, p in pts.items() if p["drawn"]):
        bad.append(f"the anchor's indexes {sorted(anchor['points'])} are not the drawn ones")
    if bad:
        raise Refused(f"panel c does not reproduce RLM-10 against single pass ({len(bad)}): " + "; ".join(bad[:4]))
    return {"compared": n, "anchor": None if anchor is None else "given"}


def write_anchor() -> int:
    """D150: freeze D149's committed RLM-10 against single pass (sheet Fig. 3c 'point' rows) as the reference."""
    commit, path = ANCHOR_FROM
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True)
    if r.returncode:
        raise Refused(f"git show {commit}:{path} failed")
    nj = json.loads(r.stdout)
    sh = nj["sheets"]["Fig. 3c"]                  # the sheet's name at that commit, before the plate became S8
    rows = [dict(zip(sh["columns"], x)) for x in sh["rows"]]
    pts = {x["index"]: {new: x[old] for old, new in ANCHOR_KEYS} for x in rows if x["row"] == "point" and x["drawn"]}
    if len(pts) != 12:
        raise Refused(f"D149's sheet Fig. 3c has {len(pts)} drawn points, not 12")
    ANCHOR.write_text(json.dumps({"what": "D149's committed Source Data for RLM-10 against single pass (Figure 3c, "
                                          "D125/D126): per index n, d, two-sided 95% interval and sign-flip P at judge "
                                          "score 3 and 4. D150's panel c must reproduce it before it is drawn.",
                                  "from_commit": commit, "path": path, "blob_sha256": sha256_bytes(r.stdout),
                                  "written_by": SCRIPT + " anchor", "points": pts}, indent=1, sort_keys=True) + "\n")
    print(f"wrote {rel(ANCHOR)}: {len(pts)} indexes from {commit}:{path}")
    return 0


def gate_record(gate_drawn: dict, gate_held: dict, anchor_path, held_keys) -> dict:
    """D156: which reading was gated on D149's anchor and which is drawn, as header.json records them."""
    return {"anchor": None if anchor_path is None else rel(anchor_path),
            "anchor_reading": "G4R38 reruns held out (as g4_cells holds a key whose rerun is not judged): D149's "
                              "anchor is checked on this reading, which is not drawn (D156)",
            "anchor_reading_compared": gate_held["compared"],
            "drawn_reading": "G4R38 reruns judged: drawn (pairs.jsonl, point_tables.json, grid_pairs.jsonl, "
                             "grid_tables.json); checked for (1) and (2) of grid_gate, not against the anchor (D156)",
            "drawn_reading_compared": gate_drawn["compared"],
            "g4r38_held_for_anchor": list(held_keys),
            "compared": gate_held["compared"] + gate_drawn["compared"]}


# ---------------------------------------------------------------------------------------------------------------
# D160 (7) Q23 (Valerio, 27 October, "Yes, as D156"): panel a draws G6 after the D135 reruns; the gates check the
# reading before them. L2/ (S474 --frozen on L2_inputs/g6/, before the reruns) stays the gated reading: S475.reproduce
# and its anchors run on it. L2_d135/ is S474's method on the same G5 file and on G6's frozen records after the reruns
# (findings/recompute/g6_d135_inputs, frozen_inputs/freeze_g6_d135.py); before it is written, every row equals L2's
# but for the answers the reruns acted on (rerun_d89.sh's 44 rerun and 72 rebuilt; the 15 left failed unchanged).
# Until the set is frozen there is no L2_d135/ and panel a draws L2/, as before D160, and the provenance says so.
# ---------------------------------------------------------------------------------------------------------------
G6_D135_SET = "g6_d135"
G6_D135 = ROOT / "findings" / "recompute" / f"{G6_D135_SET}_inputs"
L2_D135 = ROOT / "findings" / "recompute" / "L2_d135"
FREEZE_G6 = ROOT / "findings" / "recompute" / "frozen_inputs" / "freeze_g6_d135.py"
L2_FILES = ("concept_recall.jsonl", "cap_tables.json", "header.json")
L2_D181 = ROOT / "findings" / "recompute" / "L2_d181"             # D186 (4): S474 --d181 --frozen (the gated D181)
L2_D135_D181 = ROOT / "findings" / "recompute" / "L2_d135_d181"   # D186 (4): S474 --d181 --frozen-d135 (a draws it)
L2_D135_D181_G7 = ROOT / "findings" / "recompute" / "L2_d135_d181_g7"   # S514 l2g7: Mentori RLM's draws 2 and 3 (the range strip)
L2_D135_D181_D284 = ROOT / "findings" / "recompute" / "L2_d135_d181_d284"   # D284: S514 l2g7 --all86, RLM's draws 2 and 3 on the 86
# D186 (4): the files of the two D181 folders reproduce_l2_d181 reads, pinned at their committed sha256 (8334dd9f), as
# S497 pins L3_d181; a regenerated folder is refused until these are changed on purpose
L2_D181_SHA256 = {
    "gated": {"concept_recall.jsonl": "713773461aab4575e0ea0d746ae3dc8e42735db7509b8a474e19184cb1e1355d",
              "cap_tables.json": "982f658d268d3175b45a4a5ee8f5f4de5a6557e081541fafe70caf54cac6b2d6",
              "header.json": "078155046fdb8d89bcb149a150852187903ca994d84e8166d6ba51259870ffe6"},
    "drawn": {"concept_recall.jsonl": "43307c4b4a6c56adfdfd9297ef90be27e8ed577c64e66c2781ac9b933d85684f",
              "cap_tables.json": "95cf480c1824404f5c383573cba974bc579e9299903b710f4488882b8a7406fe",
              "header.json": "40ad807a471d70c486c91088a03656eb10410375b7f54b9dafcb9c1795719d06"}}
D181_ROW_TIE = ("system", "answer_key", "answer_sha256", "scored_text_sha256", "cap", "draw", "question_id", "failed",
                "status", "cap_reached", "stopped_by_cap", "d92_action", "turns_used", "group")


def g6_d135_listed() -> dict:
    """{(cap, answer_key): action} of the answers the reruns acted on (rerun_d89.sh's KEYS, as freeze_g6_d135 reads
    them): rerun 44, rebuild 72, stays_failed 15."""
    fz = _load("freeze_g6_d135", FREEZE_G6)
    return {(int(k.split("|")[0][3:]), k): a for (_, k), a in fz.keys_listed().items()}


def l2_held_check(gate_rows: list, drawn_rows: list) -> dict:
    """D160 Q23, the D156 pattern: the drawn rows are the gated rows but for the answers the reruns acted on. Every G5
    row equal; every G6 row equal but for 'source' (the file and line it was read from) unless its answer was rerun or
    rebuilt; a changed row is one of those. Returns the counts header.json keeps."""
    strip = lambda r: {k: v for k, v in r.items() if k != "source"}            # noqa: E731
    g = {(r["system"], r["answer_key"]): r for r in gate_rows}
    d = {(r["system"], r["answer_key"]): r for r in drawn_rows}
    if set(g) != set(d) or len(g) != len(gate_rows) or len(d) != len(drawn_rows):
        raise Refused("D160 Q23: L2_d135's answers are not L2's")
    acted = {k for (_, k), a in g6_d135_listed().items() if a in ("rerun", "rebuild")}
    bad, changed = [], collections.Counter()
    for k, a in g.items():
        b = d[k]
        same = (a == b) if k[0] == "G5" else (strip(a) == strip(b))
        if same:
            continue
        if k[0] == "G6" and k[1] in acted:
            changed[("failed before" if a["failed"] else "ok before") + ", " +
                    ("failed after" if b["failed"] else "ok after")] += 1
            continue
        bad.append(f"{k[0]} {k[1]}")
    if bad:
        raise Refused(f"D160 Q23: {len(bad)} L2_d135 rows differ from L2's though the reruns did not act on them, "
                      f"e.g. {bad[:3]}")
    fail = lambda R: sum(r["failed"] for r in R if r["system"] == "G6")       # noqa: E731
    return {"rows": len(d), "g6_rows_changed": sum(changed.values()), "changed_by_outcome": dict(sorted(changed.items())),
            "g6_failed_gated": fail(gate_rows), "g6_failed_drawn": fail(drawn_rows),
            "acted_on": "rerun_d89.sh's rerun and rebuild keys (D89, D90, D92; D135)"}


def l2_d135_build(outdir: Path, gate_dir: Path = L2, committed_header: Path | None = None) -> dict:
    """L2_d135/: S474's method (read_g5, read_g6, rows_for, counts, tables) on the frozen G5 draw-1 file and G6's
    frozen records after the D135 reruns; held to L2/ (l2_held_check) before anything is written."""
    g6_post = S474.frozen_checked(G6_D135_SET)
    g5_copy, _, g5_shas = S474.frozen_inputs()
    key = S470.the_key()
    ids, caps, fig2_caps, experiment = S474.design()
    g5, g5_info = S474.read_g5(g5_copy, ids, caps)
    g5_info["copy"] = rel(g5_copy)
    g6, g6_info = S474.read_g6(g6_post, ids, caps, fig2_caps, experiment)
    d92, d92_info = S474.read_d92(S474.D92_LIST)
    answers = g5 + g6
    rows = S474.rows_for(answers, key, d92)
    c = S474.counts(rows, answers)
    t = S474.tables(rows, caps, ids)
    gate_rows = load_rows(gate_dir / "concept_recall.jsonl")
    held = l2_held_check(gate_rows, rows)
    shas = {k: v for k, v in g5_shas.items() if "/g6/" not in k}
    shas.update({rel(f): sha256_file(f) for f in sorted(g6_post.glob("*/answers.jsonl"))})
    if committed_header is not None and committed_header.exists():
        rec = json.loads(committed_header.read_text()).get("frozen_inputs_sha256")
        if rec != shas:
            raise Refused(f"frozen inputs differ from those {rel(committed_header)} recorded")
    gh = json.loads((gate_dir / "header.json").read_text())
    header = {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)), "provisional": True,
              "command": f"uv run --frozen python {SCRIPT} rebuild", "plan_row": "L2",
              "what": "D160 (7) Q23: L2 on G6's records after the D135 reruns, the reading Supplementary Figure 8a draws; L2/ (S474 "
                      "--frozen, G6 before the reruns) is the reading its gates check (S475.reproduce and its anchors)",
              "gated_reading": {"dir": rel(L2), "header_sha256": sha256_file(gate_dir / "header.json"),
                                "rows_sha256": sha256_file(gate_dir / "concept_recall.jsonl")},
              "held_check": held, "frozen_inputs_sha256": shas, "matcher": gh.get("matcher"),
              "turn_limit_note": gh.get("turn_limit_note"), "failed_answers": gh.get("failed_answers"),
              "code_sha256": gh.get("code_sha256"), "key": gh.get("key"),
              "inputs": {"G5": g5_info, "G6": g6_info, "D92_list": d92_info},
              "caps": list(caps), "questions": len(ids), "counts": c}
    if gh.get("code_sha256", {}).get("scripts/concept_match_loose.py") != \
            S470.sha256_file(ROOT / "scripts" / "concept_match_loose.py"):
        raise Refused("the loose matcher is not the one L2/ was scored with")
    write_files(outdir, {"concept_recall.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                         "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n",
                         "cap_tables.json": json.dumps(t, indent=1, sort_keys=True) + "\n",
                         "cap_tables.md": S474.tables_md(t, caps)})
    return {"rows": len(rows), "held": held, "g6_status": c["G6"]["status"]}


def reproduce_l2_drawn(drawn_dir: Path, gate_rows: list, caps) -> tuple[list, dict, dict]:
    """The plate's check of L2_d135/: its header names S476 and the gated L2 files it was held to, its tables are
    S474.tables of its rows, and l2_held_check holds again."""
    header = json.loads((drawn_dir / "header.json").read_text())
    tables = json.loads((drawn_dir / "cap_tables.json").read_text())
    rows = load_rows(drawn_dir / "concept_recall.jsonl")
    if header.get("script") != SCRIPT or header.get("provisional") is not True or "held_check" not in header:
        raise Refused(f"{rel(drawn_dir)}/header.json is not S476's L2 after the D135 reruns")
    ids, _, _, _ = S474.design()
    if tuple(header["caps"]) != tuple(caps) or not same_json(S474.tables(rows, caps, ids), tables):
        raise Refused(f"{rel(drawn_dir)}: cap_tables.json is not what its rows give")
    held = l2_held_check(gate_rows, rows)
    if not same_json(held, header["held_check"]):
        raise Refused(f"{rel(drawn_dir)}/header.json: the held check recorded is not what the rows give")
    return rows, tables, header


def reproduce_l2_d181(gate_rows: list, drawn_rows: list, caps, gate_dir: Path = L2_D181,
                      drawn_dir: Path = L2_D135_D181, loose_held: dict | None = None,
                      pins: dict | None = None) -> dict:
    """D186 (4): the D181 readings a draws, checked against the loose ones before use (module docstring). gate_rows
    and drawn_rows are L2/'s and L2_d135/'s loose rows, already reproduced. pins: {"gated"|"drawn": {file: sha256}}
    for the files read (default L2_D181_SHA256, the committed folders'); a file at another sha256 is refused before
    it is read. Returns the drawn D181 rows and tables, the gated ones, S475.reproduce's record with ANCHORS_D181,
    and the counts the provenance keeps."""
    pins = L2_D181_SHA256 if pins is None else pins
    S512 = S463.JR.S512
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}
    ids, _, _, _ = S474.design()
    got = {}
    for name, d, loose in (("gated", Path(gate_dir), gate_rows), ("drawn", Path(drawn_dir), drawn_rows)):
        off = [n for n in L2_FILES if sha256_file(d / n) != (pins.get(name) or {}).get(n)]
        if off:
            raise Refused(f"{d.name}: {', '.join(off)} not at the pinned sha256 (L2_D181_SHA256 {name}); nothing "
                          f"written")
        header = json.loads((d / "header.json").read_text())
        tables = json.loads((d / "cap_tables.json").read_text())
        rows = load_rows(d / "concept_recall.jsonl")
        want = {"script": "scripts/S474_l2_concept_recall.py", "plan_row": "L2", "reading": "D181", "provisional": False}
        if {k: header.get(k) for k in want} != want or (header.get("key") or {}).get("sha256") != S512.KEY25_SHA256 \
                or tuple(header.get("caps") or ()) != tuple(caps):
            raise Refused(f"{d.name}/header.json is not S474's final D181 reading on key v2.5 at a's caps")
        lo = {(r["system"], r["answer_key"]): r for r in loose}
        dd = {(r["system"], r["answer_key"]): r for r in rows}
        if set(lo) != set(dd) or len(dd) != len(rows):
            raise Refused(f"{d.name}: its answers are not its loose reading's ({len(dd)} against {len(lo)})")
        bad, held = [], 0
        for k_, r in dd.items():
            a = lo[k_]
            if any(r.get(f) != a.get(f) for f in D181_ROW_TIE):
                bad.append(f"{k_}: {[f for f in D181_ROW_TIE if r.get(f) != a.get(f)]}")
            elif r["question_id"] in same_c:
                if (r.get("concept_recall_loose_base"), r.get("found_loose_base"), r.get("n_concepts")) != \
                        (a.get("concept_recall_loose"), a.get("found_loose"), a.get("n_concepts")):
                    bad.append(f"{k_}: the loose base on unchanged concepts is not the loose value")
                else:
                    held += 1
        if bad:
            raise Refused(f"{d.name}: {len(bad)} rows are not their loose reading's answers, first {bad[0]}")
        if not same_json(S474.tables(rows, caps, ids, d181=True), tables):
            raise Refused(f"{d.name}: cap_tables.json is not S474.tables(d181) of its rows")
        got[name] = {"rows": rows, "tables": tables, "header": header, "held_loose_base": held,
                     "questions_unchanged": len({r["question_id"] for r in rows} & same_c)}
    held_d135 = l2_held_check(got["gated"]["rows"], got["drawn"]["rows"])
    if loose_held is not None and (held_d135["g6_rows_changed"], held_d135["changed_by_outcome"]) != \
            (loose_held["g6_rows_changed"], loose_held["changed_by_outcome"]):
        raise Refused(f"the D181 readings change {held_d135['g6_rows_changed']} G6 rows between them, the loose "
                      f"readings {loose_held['g6_rows_changed']}")
    reproduced, _ = S475.reproduce(got["gated"]["rows"], got["gated"]["tables"], caps, S475.D181_FIELD)
    return {"rows": got["drawn"]["rows"], "tables": got["drawn"]["tables"], "reproduced": reproduced,
            "record": {"gated": rel(Path(gate_dir)), "drawn": rel(Path(drawn_dir)),
                       "matcher": got["drawn"]["header"].get("matcher"),
                       "loose_base_held": {n: got[n]["held_loose_base"] for n in got},
                       "questions_concepts_unchanged": got["drawn"]["questions_unchanged"],
                       "held_check_d135": held_d135,
                       "anchors": {f"{s_} cap {c_}": v for (s_, c_), v in S475.ANCHORS_D181.items()}}}


def add_g5_d284(rows: list, caps, d284dir: Path) -> tuple[list, dict, dict]:
    """D284 (Valerio, tab, 6 Nov 20:31): RLM's draws 2 and 3 on all 86 questions, read from S514 l2g7 --all86's
    folder. Its rows are S474.rows_for(d181) rows of the same answers' design (S514 holds its draw 1 to L2_d135_d181
    before it scores 2 and 3), so they join a's D181 rows as they are; the tables are S474.tables(d181) of the
    joined rows, as S474 makes them for G6's three draws."""
    h = json.loads((d284dir / "header.json").read_text())
    new = load_rows(d284dir / "concept_recall_g7.jsonl")
    ids, _, _, _ = S474.design()
    want = {"script": S514_SCRIPT, "all86": True}
    if {k: h.get(k) for k in want} != want or not str(h.get("reading", "")).startswith("D181") \
            or len(new) != 2 * len(ids) * len(caps) or {r["system"] for r in new} != {"G5"} \
            or sorted({r["draw"] for r in new}) != [2, 3]:
        raise Refused(f"{d284dir.name}: not S514 l2g7 --all86's D181 rows of G5 draws 2 and 3 on the 86 at a's caps")
    have = {r["answer_key"] for r in rows if r["system"] == "G5"}
    if have & {r["answer_key"] for r in new} or {r["draw"] for r in rows if r["system"] == "G5"} != {1}:
        raise Refused(f"{d284dir.name}: a's G5 rows already hold draws other than 1")
    joined = rows + new
    tables = S474.tables(joined, caps, ids, d181=True)
    return joined, tables, {"folder": rel(d284dir), "rows": len(new),
                            "sha256": {n: sha256_file(d284dir / n) for n in ("concept_recall_g7.jsonl", "header.json")}}


# ---------------------------------------------------------------------------------------------------------------
# D188: b and c on key v2.5. The folders are written by scripts/S514_fig3_d185.py (t1, g4c) and read here, not
# rebuilt here: S494's step d181 runs S514 t1 and g4c (D201 Q9 O1). Each is held to the
# v2.4 reading this script has just reproduced before a value of it is drawn.
# ---------------------------------------------------------------------------------------------------------------
T1_L2_D181 = ROOT / "findings" / "recompute" / "T1_L2_d181"        # D188: S514 t1 (D181's reading of T1, key v2.5)
G4_FIG3C_D185 = ROOT / "findings" / "recompute" / "G4_fig3c_d185"  # D188: S514 g4c (judge_rows_v25, draw 1 main)
S514_SCRIPT = "scripts/S514_fig3_d185.py"
T1_D181_FILES = ("concept_recall.jsonl", "cap_tables.json", "header.json")
G4_D185_FILES = ("grid_pairs.jsonl", "grid_tables.json", "header.json")
T1_D181_TIE = ("model", "cap", "question_id", "draw", "answer_key", "run_id", "status", "failed", "stop_reason",
               "turns_used", "turn_limit_note", "answer_sha256", "cap_reached", "stopped_by_cap", "in_complete_question",
               "note_removed")
D185_ADDED_ROW = ("draw", "key_versions")                          # S514 g4c's grid_pairs.jsonl adds these to S476's
D185_ADDED_CELL = ("awaiting_s6_answers",)                         # and these to each grid_tables.json cell
D185_ADDED_TOP = ("provisional", "awaiting_s6", "rests_on")        # and these to grid_tables.json
D185_AWAIT = "v2.4 awaiting S6"


def reproduce_t1_d181(d181dir: Path, t1dir: Path, t1rows: list, t1tab: dict) -> tuple[list, dict, dict]:
    """D188: T1_L2_d181 (S514 t1) held to the T1_L2 reading just reproduced (t1rows, t1tab from t1dir): its header
    S514's D181 reading on key v2.5, held to t1dir's rows by their sha256; the same answers one for one, each with
    the same T1_D181_TIE fields; on the questions whose concepts v2.5 left unchanged, the loose base equal to the
    loose value of the text (text_recall_loose, found_loose, n_concepts); a failed answer 0; cap_tables.json equal to
    t1_tables of its rows on concept_recall."""
    d181dir = Path(d181dir)
    header = json.loads((d181dir / "header.json").read_text())
    tables = json.loads((d181dir / "cap_tables.json").read_text())
    rows = load_rows(d181dir / "concept_recall.jsonl")
    S512 = S463.JR.S512
    if header.get("script") != S514_SCRIPT or header.get("reading") != "D181" or \
            (header.get("key") or {}).get("sha256") != S512.KEY25_SHA256:
        raise Refused(f"{rel(d181dir)}/header.json is not S514 t1's D181 reading on key v2.5")
    held = header.get("held_to") or {}
    want = {"concept_recall.jsonl": sha256_file(Path(t1dir) / "concept_recall.jsonl"),
            "cap_tables.json": sha256_file(Path(t1dir) / "cap_tables.json")}
    if {k: (held.get(k) or {}).get("sha256") for k in want} != want:
        raise Refused(f"{rel(d181dir)} was held to another T1_L2 reading than {rel(Path(t1dir))} (rows or tables "
                      f"sha256 differ)")
    if len(rows) != header.get("rows") or len(rows) != len(t1rows):
        raise Refused(f"{rel(d181dir)}: {len(rows)} rows, header {header.get('rows')}, T1_L2 {len(t1rows)}")
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}
    lo = {(r["model"], r["answer_key"]): r for r in t1rows}
    bad, held_base = [], 0
    for r in rows:
        a = lo.get((r.get("model"), r.get("answer_key")))
        if a is None:
            bad.append(f"{r.get('model')} {r.get('answer_key')}: not a T1_L2 answer")
            continue
        off = [f for f in T1_D181_TIE if r.get(f) != a.get(f)]
        if off:
            bad.append(f"{r['model']} {r['answer_key']}: {off}")
            continue
        if not isinstance(r.get("concept_recall"), (int, float)) or \
                (r["failed"] and r["concept_recall"] != 0.0) or \
                (not r["failed"] and r["concept_recall"] != r.get("text_concept_recall")):
            bad.append(f"{r['model']} {r['answer_key']}: concept_recall {r.get('concept_recall')} is not its text's "
                       f"value (0 when failed)")
            continue
        if r["question_id"] in same_c:
            if (r.get("concept_recall_loose_base"), r.get("found_loose_base"), r.get("n_concepts")) != \
                    (a.get("text_recall_loose"), a.get("found_loose"), a.get("n_concepts")):
                bad.append(f"{r['model']} {r['answer_key']}: the loose base on unchanged concepts is not the loose "
                           f"value")
                continue
            held_base += 1
    if bad or len({(r["model"], r["answer_key"]) for r in rows}) != len(lo):
        raise Refused(f"{rel(d181dir)}: {len(bad)} rows not tied to T1_L2's, first {bad[:1]}")
    again = t1_tables(rows, t1tab["models"], t1tab["caps"], t1tab["complete_questions"], field="concept_recall")
    if not same_json(again, tables):
        raise Refused(f"{rel(d181dir)}: cap_tables.json is not t1_tables of its rows on concept_recall")
    return rows, tables, {"dir": rel(d181dir), "rows": len(rows), "loose_base_held": held_base,
                          "questions_concepts_unchanged": len({r["question_id"] for r in rows} & same_c),
                          "matcher": header.get("matcher"), "key_sha256": header["key"]["sha256"],
                          "held_to": {k: v[:8] for k, v in want.items()}}


def reproduce_g4_d185(d185dir: Path, rows6_v24: list, indexes) -> tuple[list, dict, dict]:
    """D188: G4_fig3c_d185 (S514 g4c, judge_rows_v25: a v2.5 row where S6 judged an answer of the 132 changed
    questions, else the v2.4 row) held to the G4_fig3c reading just reproduced (rows6_v24): its header S514's,
    provisional, draw 1 the main estimate, with the draw-1 units; grid_pairs.jsonl at draw 1, the rows of S476's
    shape plus draw and key_versions, the same (index, question) rows with the same flags, every row of a question
    v2.5 left unchanged equal to G4_fig3c's (S512.changed_ids, the D156 pattern); each ok cell's passes its
    correctness against 4 and 3; grid_tables.json equal to grid_tables of the rows and units, with each cell's
    answers awaiting S6 recounted from key_versions. Returns the rows (S476's shape), the grid (S476's shape) and a
    record."""
    d185dir = Path(d185dir)
    header = json.loads((d185dir / "header.json").read_text())
    grid_f = json.loads((d185dir / "grid_tables.json").read_text())
    rows_kv = load_rows(d185dir / "grid_pairs.jsonl")
    if header.get("script") != S514_SCRIPT or header.get("provisional") is not True or \
            (header.get("draws") or {}).get("main") != 1:
        raise Refused(f"{rel(d185dir)}/header.json is not S514 g4c's provisional draw-1 reading")
    units = header.get("units_draw1")
    if not isinstance(units, dict) or set(units) != {f"{s} {i}" for s in G4_ALL for i in indexes}:
        raise Refused(f"{rel(d185dir)}/header.json holds no draw-1 units for the {len(G4_ALL) * len(indexes)} "
                      f"strategy and index units (rebuild it with S514 g4c)")
    if len(rows_kv) != (header.get("rows") or {}).get("grid_pairs") or any(r.get("draw") != 1 for r in rows_kv):
        raise Refused(f"{rel(d185dir)}/grid_pairs.jsonl: {len(rows_kv)} rows (header "
                      f"{(header.get('rows') or {}).get('grid_pairs')}), or a row not of draw 1")
    rows = [{k: v for k, v in r.items() if k not in D185_ADDED_ROW} for r in rows_kv]
    changed = set(S463.JR.S512.changed_ids())
    ref = {(r["index"], r["question_id"]): r for r in rows6_v24}
    mine = {(r["index"], r["question_id"]): r for r in rows}
    if set(ref) != set(mine) or len(mine) != len(rows):
        raise Refused(f"{rel(d185dir)}: its (index, question) rows are not G4_fig3c's")
    flags = ("core_papers", "distractor_ratio", "common", "covered", "per_size", "both_units_complete")
    bad, moved = [f"{r['index']} {r['question_id']}: key_versions not of the six strategies" for r in rows_kv
                  if set(r.get("key_versions") or {}) != set(G4_ALL)], 0
    for k_, r in mine.items():
        a = ref[k_]
        if any(r.get(f) != a.get(f) for f in flags) or set(r["cells"]) != set(G4_ALL):
            bad.append(f"{k_}: flags or strategies")
        elif r["question_id"] not in changed and not same_json(r, a):
            bad.append(f"{k_}: an unchanged question's row differs from G4_fig3c's")
        elif not same_json(r, a):
            moved += 1
    if bad:
        raise Refused(f"{rel(d185dir)}: {len(bad)} rows not held to G4_fig3c, first {bad[0]}")
    off = [(r["index"], r["question_id"], c) for r in rows for c, x in r["cells"].items() if x["status"] == "ok" and
           (not isinstance(x["correctness"], (int, float)) or x["pass4"] != int(x["correctness"] >= PASS4) or
            x["pass3"] != int(x["correctness"] >= PASS3))]
    if off:
        raise Refused(f"{rel(d185dir)}/grid_pairs.jsonl: {len(off)} cells whose pass is not their correctness "
                      f"against the threshold, e.g. {off[0]}")
    grid = grid_tables(rows, indexes, units)
    got = {k: v for k, v in grid_f.items() if k not in D185_ADDED_TOP}
    got["cells"] = [{k: v for k, v in e.items() if k not in D185_ADDED_CELL} for e in grid_f["cells"]]
    if not same_json(grid, got):
        raise Refused(f"{rel(d185dir)}: grid_tables.json is not what grid_pairs.jsonl and the draw-1 units give")
    aw = []
    for e in grid_f["cells"]:
        n = sum((r["key_versions"].get(e["strategy"]) == D185_AWAIT) + (r["key_versions"].get("single_pass") ==
                                                                        D185_AWAIT)
                for r in rows_kv if r["index"] == e["index"] and r.get("covered"))
        if e.get("awaiting_s6_answers") != n:
            aw.append((e["score"], e["index"], e["strategy"]))
    if aw:
        raise Refused(f"{rel(d185dir)}/grid_tables.json: {len(aw)} cells' answers awaiting S6 are not their rows' "
                      f"key_versions count, e.g. {aw[0]}")
    kv = collections.Counter(v for r in rows_kv if r.get("covered") for v in r["key_versions"].values())
    return rows, grid, {"dir": rel(d185dir), "rows": len(rows), "rows_moved_by_v25": moved,
                        "covered_answers_by_key": dict(sorted(("not judged" if k is None else k, v)
                                                                for k, v in kv.items())),
                        "awaiting_s6_covered": kv.get(D185_AWAIT, 0),
                        "units_complete": sum(bool(v["complete"]) for v in units.values()),
                        "units": units, "choice_report": header.get("choice_report")}


# ---------------------------------------------------------------------------------------------------------------
# D160 (6) Q18, the Figure 3 part: every cell against the numbers drawn before D156, each judge row against the score
# drawn, and G4R38's rerun answer texts frozen and read
# ---------------------------------------------------------------------------------------------------------------
CELL_TOL = 1e-9


def write_anchor_pre_d156() -> int:
    """Freeze panel c's grid as committed before D156 (grid_tables.json at ANCHOR_PRE_D156_FROM), once."""
    commit, path = ANCHOR_PRE_D156_FROM
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True)
    if r.returncode:
        raise Refused(f"git show {commit}:{path} failed")
    grid = json.loads(r.stdout)
    if len(grid.get("cells") or []) != 2 * len(GRID_STRATS) * 12:
        raise Refused(f"{commit}:{path} holds {len(grid.get('cells') or [])} cells, not {2 * len(GRID_STRATS) * 12}")
    ANCHOR_PRE_D156.write_text(json.dumps({
        "what": "Figure 3c's grid as committed before D156 (G4's judging of 26 October, g4_collect.jsonl 5ca931f4): "
                "every strategy against single pass on every index at judge score 3 and 4. D160 (6) Q18: each cell "
                "complete here must equal the build's cell on the reading with the judged G4R38 reruns held out, and "
                "the cells the drawn reading changes are recorded beside their values here.",
        "from_commit": commit, "path": path, "blob_sha256": sha256_bytes(r.stdout),
        "written_by": SCRIPT + " anchor-pre-d156", "cells": grid["cells"]}, indent=1, sort_keys=True) + "\n")
    print(f"wrote {rel(ANCHOR_PRE_D156)}: {len(grid['cells'])} cells from {commit}:{path}, "
          f"{sum(e['complete'] for e in grid['cells'])} complete")
    return 0


def read_anchor_pre_d156(path: Path = ANCHOR_PRE_D156) -> dict:
    a = json.loads(path.read_text())
    if a.get("from_commit") != ANCHOR_PRE_D156_FROM[0] or len(a.get("cells") or []) != 2 * len(GRID_STRATS) * 12:
        raise Refused(f"{rel(path)} is not panel c's grid as committed before D156")
    return a


def cells_equal(a: dict, b: dict) -> bool:
    if set(a) != set(b):
        return False
    for k, v in a.items():
        w = b[k]
        if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(w, (int, float)) \
                and not isinstance(w, bool):
            if abs(float(v) - float(w)) > CELL_TOL:
                return False
        elif isinstance(v, list) and isinstance(w, list):
            if len(v) != len(w) or any(abs(float(x) - float(y)) > CELL_TOL for x, y in zip(v, w)):
                return False
        elif v != w:
            return False
    return True


def cell_numbers(e: dict | None) -> dict | None:
    if e is None or not e.get("complete"):
        return None
    return {"n_paired": e["n_paired"], "pass_strategy_pct": e["pass_strategy_pct"],
            "pass_single_pass_pct": e["pass_single_pass_pct"], "d_pp": e["d_pp"], "ci95_pp": e["ci95_pp"],
            "p_signflip": e["p_signflip"]}


def pre_d156_check(hgrid: dict, grid: dict, anchor: dict, held_keys) -> dict:
    """D160 (6) Q18: (1) every cell complete before D156 equals, value for value, the cell of the reading with the
    judged G4R38 reruns held out (that reading differs from the 26 October one only by the units judged since);
    (2) a cell the drawn reading changes against the held one is a cell of an index and strategy (or single pass) a
    held key belongs to; any other change refuses. Returns the record header.json keeps: the counts, the cells complete
    since D156, and every drawn cell that differs from its pre-D156 value, old and new."""
    k_ = lambda e: (e["score"], e["strategy"], e["index"])          # noqa: E731
    pre = {k_(e): e for e in anchor["cells"]}
    held = {k_(e): e for e in hgrid["cells"]}
    drawn = {k_(e): e for e in grid["cells"]}
    if set(pre) != set(held) or set(pre) != set(drawn):
        raise Refused("D160 Q18: the grid's cells are not the pre-D156 grid's cells")
    touched = set()
    for key in held_keys:                            # a cell is a strategy against single pass on one index, so a
        idx, cfg, _, _ = key.split("|")              # single pass rerun touches every strategy's cell on its index
        touched |= {(s_, idx) for s_ in GRID_STRATS} if cfg == "single_pass" else {(cfg, idx)}
    bad, equal, since = [], 0, []
    for k, a in sorted(pre.items()):
        if a["complete"]:
            if cells_equal(a, held[k]):
                equal += 1
            else:
                bad.append(f"score {k[0]} {k[1]} {k[2]}: held reading {cell_numbers(held[k])}, before D156 "
                           f"{cell_numbers(a)}")
        elif held[k]["complete"]:
            since.append(k)
    changed = []
    for k, d in sorted(drawn.items()):
        if not cells_equal(d, held[k]) and (k[1], k[2]) not in touched:
            bad.append(f"score {k[0]} {k[1]} {k[2]}: the drawn reading differs from the held one, and no judged "
                       f"G4R38 rerun is of this strategy or its single pass on this index")
        if not cells_equal(d, pre[k]):
            changed.append({"score": k[0], "strategy": k[1], "index": k[2],
                            "why": ("complete since D156" if not pre[k]["complete"] else
                                    "a judged G4R38 rerun enters it" if not cells_equal(d, held[k]) else "other"),
                            "pre_d156": cell_numbers(pre[k]), "drawn": cell_numbers(d)})
    other = [c for c in changed if c["why"] == "other"]
    if other:
        bad.append(f"{len(other)} drawn cells differ from before D156 for no recorded reason, e.g. {other[0]}")
    if bad:
        raise Refused(f"D160 Q18: panel c against the numbers drawn before D156 ({len(bad)}): " + "; ".join(bad[:3]))
    return {"anchor_from": f"{anchor['from_commit']}:{anchor['path']}", "cells": len(pre),
            "complete_before_d156": sum(e["complete"] for e in pre.values()),
            "equal_on_held_reading": equal,
            "complete_since_d156": [f"score {s} {st} {i}" for s, st, i in since],
            "drawn_changed": changed}


def judge_row_check(copy, cells6: list, judged_keys) -> dict:
    """D160 (6) Q18: each drawn cell against the judge row it comes from, read from S3's judge folders (not the
    collect the cells were built from): a G4R38 key judged again from out_g4r38/judge/<run>, any other answer from
    out_g4/judge/<run> (the latest row of its ident, judge_passages' rule). An ok cell's correctness equals the row's
    and its pass at 4 and 3 is that correctness against the threshold; an unscored cell's row is a failed judge call;
    a failed cell is an input failure with no row, or a row of status no_answer; a G4R38 key has no row in out_g4 and
    an other answer none in out_g4r38. Conversely every draw-1 judge row of an answer in the rows is one of them."""
    out_g4 = copy / "s3" / "out_g4" / "judge"
    out_r38 = copy / "s3" / "out_g4r38" / "judge"
    judged_keys = set(judged_keys)
    jr4, jr38 = {}, {}
    for r in cells6:
        for cfg in r["cells"]:
            run = G4_RUN.format(config=cfg, index=r["index"])
            if run not in jr4:
                jr4[run] = judge_rows(out_g4 / run)
                jr38[run] = judge_rows(out_r38 / run) if out_r38.is_dir() else {}
    bad, n, by = [], 0, collections.Counter()
    seen = set()
    for r in cells6:
        for cfg, cell in r["cells"].items():
            run = G4_RUN.format(config=cfg, index=r["index"])
            ident = (run, cfg, r["question_id"], 1)
            key = f"{r['index']}|{cfg}|{r['question_id']}|d1"
            j4, j38 = jr4[run].get(ident), jr38[run].get(ident)
            if key in judged_keys:
                if j4 is not None:
                    bad.append(f"{key}: a G4R38 key with a row in out_g4")
                j = j38
            else:
                if j38 is not None:
                    bad.append(f"{key}: a row in out_g4r38, not a G4R38 key judged again")
                j = j4
            if j is not None:
                seen.add(ident)
            st = cell["status"]
            n += 1
            by[st] += 1
            if st == "ok":
                c = None if j is None else ((j.get("a") or {}).get("scores") or {}).get("correctness")
                if j is None or (j.get("a") or {}).get("status") != "ok" or c != cell["correctness"] or \
                        cell["pass4"] != int(c >= PASS4) or cell["pass3"] != int(c >= PASS3):
                    bad.append(f"{key}: drawn correctness {cell['correctness']} pass4 {cell['pass4']} pass3 "
                               f"{cell['pass3']}, judge row {None if j is None else (j.get('a') or {}).get('status')} "
                               f"{c}")
            elif st == "unscored":
                if j is None or (j.get("a") or {}).get("status") not in JUDGE_FAILED:
                    bad.append(f"{key}: unscored, judge row {None if j is None else (j.get('a') or {}).get('status')}")
            elif st == "failed":
                if j is not None and (j.get("a") or {}).get("status") != "no_answer":
                    bad.append(f"{key}: failed, judge row {(j.get('a') or {}).get('status')}")
                if cell["pass4"] != 0 or cell["pass3"] != 0:
                    bad.append(f"{key}: failed with pass4 {cell['pass4']} pass3 {cell['pass3']}")
            elif st in ("not_judged", "held_g4r38"):
                if j is not None:
                    bad.append(f"{key}: {st} with a judge row")
            else:
                bad.append(f"{key}: status {st!r}")
    rows_keys = {(r["index"], r["question_id"]) for r in cells6}
    unmatched = []
    for run in jr4:
        for jr in (jr4[run], jr38[run]):
            for ident, d in jr.items():
                idx = run.split("__")[2]
                if d["draw"] == 1 and (idx, d["question_id"]) in rows_keys and ident not in seen:
                    unmatched.append(f"{run} {d['question_id']}")
    if unmatched:
        bad.append(f"{len(unmatched)} draw-1 judge rows of the rows' answers match no drawn cell, e.g. {unmatched[0]}")
    if bad:
        raise Refused(f"D160 Q18: the drawn cells against S3's judge rows ({len(bad)}): " + "; ".join(bad[:3]))
    return {"cells": n, "by_status": dict(sorted(by.items())), "judge_rows_matched": len(seen),
            "g4r38_from_out_g4r38": len(judged_keys & {f"{i[0].split('__')[2]}|{i[1]}|{i[2]}|d1" for i in seen})}


def g4r38_texts_check(judged_keys, texts: Path = G4R38_TEXTS, sums: dict | None = None) -> dict:
    """D160 (6) Q18: the 38 rerun answer texts S3 judged into out_g4r38, as frozen in G4R38_TEXTS (COPY.json,
    MANIFEST.sha256 and runs/<run>/ as snap_g4r38.py made them on the Studio): every file equal to its MANIFEST.sha256
    line and to its frozen_inputs/SHA256SUMS line; the answer lines exactly the judged G4R38 keys, each once, in the
    run its key names, draw 1, with text and no error. Before the set is frozen, the record says so and nothing else
    is checked (the texts are on the Studio only)."""
    judged_keys = set(judged_keys)
    if not texts.exists():
        return {"frozen": False, "what": f"{rel(texts)} not frozen yet: the 38 rerun answer texts are on the Studio "
                                         f"(~/s3_inputs/g4r38, snap_g4r38.py make); freeze_g4r38.py freezes them"}
    sums = S474.read_sums() if sums is None else sums
    man = read_manifest(texts / "MANIFEST.sha256")
    files = sorted(p for p in texts.rglob("*") if p.is_file())
    bad, shas = [], {}
    for p in files:
        k = rel(p)
        h = sha256_file(p)
        shas[k] = h
        if sums.get(k) != h:
            bad.append(f"{k} is not its SHA256SUMS line")
        sub = p.relative_to(texts).as_posix()
        if sub not in ("COPY.json", "MANIFEST.sha256") and man.get(sub) != h:
            bad.append(f"{sub} is not its MANIFEST.sha256 line")
    if set(man) != {p.relative_to(texts).as_posix() for p in files} - {"COPY.json", "MANIFEST.sha256"}:
        bad.append("MANIFEST.sha256 lists other files than the set holds")
    got = collections.Counter()
    text_sha = {}
    for f in sorted(texts.glob("runs/*/answers.jsonl")):
        for x in f.read_text().splitlines():
            if not x.strip():
                continue
            a = json.loads(x)
            k = a.get("answer_key")
            got[k] += 1
            idx, cfg, q, d = (k or "|||").split("|")
            gen = a.get("generation") or {}
            if a.get("run_id") != f.parent.name or f.parent.name != G4_RUN.format(config=cfg, index=idx) or \
                    a.get("question_id") != q or a.get("config") != cfg or a.get("draw") != 1 or d != "d1":
                bad.append(f"{k}: run, question, config or draw differ from its key")
            if gen.get("error") or not (gen.get("answer") or "").strip():
                bad.append(f"{k}: a rerun answer with an error or no text")
            text_sha[k] = sha256_bytes((gen.get("answer") or "").encode("utf-8"))
    if set(got) != judged_keys or any(v != 1 for v in got.values()):
        bad.append(f"the frozen texts hold {len(got)} keys ({sum(got.values())} lines), not the {len(judged_keys)} "
                   f"judged G4R38 keys once each")
    if bad:
        raise Refused(f"D160 Q18: G4R38's frozen rerun texts ({len(bad)}): " + "; ".join(bad[:3]))
    return {"frozen": True, "set": rel(texts), "files_sha256": shas, "answers": len(got),
            "answer_text_sha256": dict(sorted(text_sha.items()))}


def d160_summary(c: dict) -> str:
    j, p, t = c.get("judge_rows") or {}, c.get("pre_d156"), c.get("g4r38_texts") or {}
    out = [f"{j.get('cells')} cells against their judge rows ({j.get('judge_rows_matched')} rows, "
           f"{j.get('g4r38_from_out_g4r38')} from out_g4r38)"]
    if p is not None:
        out.append(f"{p['equal_on_held_reading']} of {p['complete_before_d156']} cells complete before D156 equal on "
                   f"the held reading, {len(p['complete_since_d156'])} complete since, {len(p['drawn_changed'])} drawn "
                   f"cells differ from before D156")
    out.append(f"G4R38 texts {'frozen, ' + str(t.get('answers')) + ' answers' if t.get('frozen') else 'not frozen'}"
               if t else "G4R38 texts not checked")
    return "; ".join(out)


def g4_build(copy: Path, outdir: Path, g4r38_path: Path = G4R38_KEYS, g4r38_want=G4R38_WANT,
             g4r38_want_all=G4R38_WANT_ALL, anchor_path=ANCHOR, committed_header: Path | None = None,
             pre_anchor_path: Path | None = ANCHOR_PRE_D156, g4r38_texts: Path | None = G4R38_TEXTS) -> dict:
    """committed_header: a frozen rebuild (D155), refused unless the frozen inputs are those it recorded (A9).
    pre_anchor_path, g4r38_texts: D160 (6) Q18's checks (None: not run, the fixtures)."""
    shas = frozen_shas(copy, tars=("g4_inputs",)) if committed_header is not None else None
    # D156 (Valerio, 27 October, O1): the drawn reading reads the judged G4R38 reruns; D149's anchor is checked on the
    # reading with those reruns held out, which must reproduce it exactly before anything is written
    cells, info = g4_cells(copy, g4r38_path, g4r38_want)
    tables = g4_tables(cells, info["indexes"])
    cells6, info6 = g4_cells(copy, g4r38_path, g4r38_want_all, configs=G4_ALL)     # D150: panel c
    grid = grid_tables(cells6, info6["indexes"], info6["units"])
    gate_drawn = grid_gate(cells, tables, cells6, grid, None)
    hcells, hinfo = g4_cells(copy, g4r38_path, g4r38_want, hold_g4r38=True)
    hcells6, hinfo6 = g4_cells(copy, g4r38_path, g4r38_want_all, configs=G4_ALL, hold_g4r38=True)
    held_keys = info6["g4r38_judged_keys"]
    if not same_json(hold_rows(cells, held_keys), hcells) or not same_json(hold_rows(cells6, held_keys), hcells6) \
            or hinfo6["units"] != info6["units"]:
        raise Refused("D156: the held reading is not the judged reading with the judged G4R38 reruns held out")
    htables = g4_tables(hcells, hinfo["indexes"])
    hgrid = grid_tables(hcells6, hinfo6["indexes"], hinfo6["units"])
    anchor = read_anchor(anchor_path) if anchor_path is not None else None
    gate_held = grid_gate(hcells, htables, hcells6, hgrid, anchor)
    gate = gate_record(gate_drawn, gate_held, anchor_path if anchor is not None else None, held_keys)
    # D160 (6) Q18 (Valerio, 27 October): every cell against the numbers drawn before D156, each drawn cell against
    # the judge row it comes from, and the G4R38 rerun texts S3 judged, frozen; any failure refuses, nothing written
    checks = {"judge_rows": judge_row_check(copy, cells6, held_keys)}
    if pre_anchor_path is not None:
        checks["pre_d156"] = {**pre_d156_check(hgrid, grid, read_anchor_pre_d156(pre_anchor_path), held_keys),
                              "anchor": rel(pre_anchor_path), "anchor_sha256": sha256_file(pre_anchor_path)}
    if g4r38_texts is not None:
        checks["g4r38_texts"] = g4r38_texts_check(held_keys, g4r38_texts)
    checked = None
    if shas is not None:
        def legacy(h):
            i = h.get("inputs") or {}
            return [k for k in ("collect_sidecar", "run_sha256", "collect_rows_rlm10_sp", "units", "answer_lines")
                    if i.get(k) != info.get(k)]
        checked = check_frozen_record(shas, committed_header, legacy)
    header = {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)), "provisional": True,
              "command": (f"uv run --frozen python {SCRIPT} rebuild" if shas is not None
                          else f"uv run --frozen python {SCRIPT} g4c --copy <copy>"), "copy": str(copy),
              "frozen_inputs_sha256": shas,
              "what": "G4 draw 1, rlm_10 and single_pass, judged by S3 (plain call (a)); a cell passes at correctness "
                      "4 or more (Rule 5, D154), and at 3 or more on the relaxed threshold; an input answer with an error or no text fails (Rule 10); a G4R38 key not "
                      "judged again is held out (setup error, Rule 10); a failed judge call is unscored; an index is "
                      "drawn when both units are complete; d over the questions the index can answer (D126: of the "
                      "common set's answerable questions, those whose source papers are all in the index); the "
                      "common-86 reading (Q105) kept beside it",
              "inputs": info, "g4r38_keys_file": {"path": rel(g4r38_path), "sha256": sha256_file(g4r38_path)},
              "rows": len(cells), "seed": SEED, "n_boot": N_BOOT,
              "drawn_indexes": [p["index"] for p in tables["points"] if p["drawn"]],
              "grid": {"what": "D150: all six strategies (grid_pairs.jsonl, g4_cells on G4_ALL) and every strategy "
                               "against single pass at score 3 and 4 (grid_tables.json)", "inputs": info6,
                       "rows": len(cells6), "gate": gate, "checks_d160": checks,
                       "held_cells_complete": sum(e["complete"] for e in hgrid["cells"]) // 2,
                       "anchor_sha256": None if anchor is None else sha256_file(anchor_path),
                       "cells_complete": sum(e["complete"] for e in grid["cells"]) // 2}}
    write_files(outdir, {"pairs.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in cells),
                         "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n",
                         "point_tables.json": json.dumps(tables, indent=1, sort_keys=True) + "\n",
                         "grid_pairs.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in cells6),
                         "grid_tables.json": json.dumps(grid, indent=1, sort_keys=True) + "\n"})
    units = info["units"]
    return {"rows": len(cells), "units_complete": sorted(k for k, v in units.items() if v["complete"]),
            "drawn": header["drawn_indexes"], "judged_rows": info["collect_rows_rlm10_sp"],
            "units6_complete": sorted(k for k, v in info6["units"].items() if v["complete"]),
            "grid_cells_complete": header["grid"]["cells_complete"], "gate": gate, "frozen_check": checked,
            "checks_d160": checks}


# ---------------------------------------------------------------------------------------------------------------
# PLATE
# ---------------------------------------------------------------------------------------------------------------
MODEL_COLOUR_MUT = {"devstral-small-2:24b": "orange", "gemma3:27b": "sky blue", "qwen3-coder:30b": "bluish green",
                    "qwen3-coder-next:q4_K_M": "reddish purple"}   # mutant b_model_colours only (b's lines are grey)


def load_rows(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def same_json(a, b) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def reproduce_t1(t1dir: Path) -> tuple[list, dict, dict]:
    header = json.loads((t1dir / "header.json").read_text())
    tables = json.loads((t1dir / "cap_tables.json").read_text())
    rows = load_rows(t1dir / "concept_recall.jsonl")
    if header.get("script") != SCRIPT or not header.get("script_sha256") or header.get("provisional") is not True \
            or not header.get("inputs"):
        raise Refused(f"{rel(t1dir)}/header.json does not name S476, its sha256 and its inputs")
    if len(rows) != header["rows"]:
        raise Refused(f"{rel(t1dir)}: {len(rows)} rows, header {header['rows']}")
    again = t1_tables(rows, tables["models"], tables["caps"], tables["complete_questions"])
    comp = sorted({r["question_id"] for r in rows if r["in_complete_question"]})
    if not same_json(again, tables) or comp != tables["complete_questions"] or tables["k"] != len(comp) \
            or header["k"] != tables["k"]:
        raise Refused(f"{rel(t1dir)}: cap_tables.json is not what its rows give (k {tables['k']}, rows say "
                      f"{len(comp)})")
    return rows, tables, header


def reproduce_g4(g4dir: Path, anchor_path: Path = ANCHOR) -> tuple[list, dict, dict]:
    header = json.loads((g4dir / "header.json").read_text())
    tables = json.loads((g4dir / "point_tables.json").read_text())
    rows = load_rows(g4dir / "pairs.jsonl")
    if header.get("script") != SCRIPT or not header.get("script_sha256") or header.get("provisional") is not True \
            or not header.get("inputs"):
        raise Refused(f"{rel(g4dir)}/header.json does not name S476, its sha256 and its inputs")
    from experiments.runner import experiment as ex
    from experiments.scorers import records
    common_answerable = {q["id"] for q in ex.questions() if records.group_of(q["id"]) == "answerable"}
    covered = coverage_check(S470.the_key()["questions"], common_answerable)     # D126, derived again from the key
    bad = [(r["index"], r["question_id"]) for r in rows
           if r.get("covered") is not (r["common"] and r["question_id"] in covered[r["core_papers"]])]
    if bad:
        raise Refused(f"{rel(g4dir)}: {len(bad)} rows' covered flag is not what the key's source papers give, e.g. "
                      f"{bad[:2]}")
    if header["inputs"].get("covered") != {str(c): len(v) for c, v in covered.items()}:
        raise Refused(f"{rel(g4dir)}/header.json covered counts {header['inputs'].get('covered')} are not the key's")
    again = g4_tables(rows, header["inputs"]["indexes"])
    if not same_json(again, tables) or len(rows) != header["rows"]:
        raise Refused(f"{rel(g4dir)}: point_tables.json is not what pairs.jsonl gives")
    # D150: the grid, recomputed from its rows, its covered flags from the key, RLM-10 reproduced again
    gh = header.get("grid") or {}
    rows6 = load_rows(g4dir / "grid_pairs.jsonl")
    grid = json.loads((g4dir / "grid_tables.json").read_text())
    bad6 = [(r["index"], r["question_id"]) for r in rows6
            if r.get("covered") is not (r["common"] and r["question_id"] in covered[r["core_papers"]])]
    if bad6 or len(rows6) != gh.get("rows") or {c for r in rows6 for c in r["cells"]} != set(G4_ALL):
        raise Refused(f"{rel(g4dir)}/grid_pairs.jsonl: {len(rows6)} rows (header {gh.get('rows')}), covered flags "
                      f"off on {len(bad6)}, or not the six strategies")
    if not same_json(grid_tables(rows6, gh["inputs"]["indexes"], gh["inputs"]["units"]), grid):
        raise Refused(f"{rel(g4dir)}: grid_tables.json is not what grid_pairs.jsonl gives")
    # D160 (6) Q18: each drawn cell's pass at 4 and 3 is its stored correctness against the threshold
    off = [(r["index"], r["question_id"], c) for r in rows6 for c, x in r["cells"].items() if x["status"] == "ok" and
           (not isinstance(x["correctness"], (int, float)) or x["pass4"] != int(x["correctness"] >= PASS4) or
            x["pass3"] != int(x["correctness"] >= PASS3))]
    if off:
        raise Refused(f"{rel(g4dir)}/grid_pairs.jsonl: {len(off)} cells whose pass is not their correctness against "
                      f"the threshold, e.g. {off[0]}")
    anchor = None
    if gh.get("anchor_sha256") is not None:
        if sha256_file(anchor_path) != gh["anchor_sha256"]:
            raise Refused(f"{rel(anchor_path)} is not the anchor G4_fig3c was gated on")
        anchor = read_anchor(anchor_path)
    gate = gh.get("gate") or {}
    if "g4r38_held_for_anchor" not in gate:          # a header from before D156: one reading, gated on the anchor
        grid_gate(rows, tables, rows6, grid, anchor)
        return rows, tables, header, rows6, grid
    # D156: the drawn rows hold the judged G4R38 reruns; the anchor is checked on the same rows with those reruns
    # held out, each of them a key of the g4r38_keys.txt header.json names, with its recorded sha256
    grid_gate(rows, tables, rows6, grid, None)
    held = gate["g4r38_held_for_anchor"]
    kf = Path(header["g4r38_keys_file"]["path"])
    kf = kf if kf.is_absolute() else ROOT / kf
    if not kf.is_file() or sha256_file(kf) != header["g4r38_keys_file"]["sha256"]:
        raise Refused(f"{rel(kf)} is not the G4R38 key list G4_fig3c was built with")
    if not set(held) <= set(read_g4r38(kf)) or held != gh["inputs"].get("g4r38_judged_keys"):
        raise Refused(f"{rel(g4dir)}/header.json: the G4R38 keys held for the anchor are not the judged keys of "
                      f"{rel(kf)}")
    hrows, hrows6 = hold_rows(rows, held), hold_rows(rows6, held)
    htables = g4_tables(hrows, header["inputs"]["indexes"])
    hgrid = grid_tables(hrows6, gh["inputs"]["indexes"], gh["inputs"]["units"])
    grid_gate(hrows, htables, hrows6, hgrid, anchor)
    pre = (gh.get("checks_d160") or {}).get("pre_d156")
    if pre is not None:                              # D160 (6) Q18: the pre-D156 comparison again, on the rows written
        ap = ROOT / pre["anchor"]
        if not ap.is_file() or sha256_file(ap) != pre["anchor_sha256"]:
            raise Refused(f"{pre['anchor']} is not the pre-D156 grid G4_fig3c was checked against")
        again = pre_d156_check(hgrid, grid, read_anchor_pre_d156(ap), held)
        if not same_json(again, {k: v for k, v in pre.items() if k not in ("anchor", "anchor_sha256")}):
            raise Refused(f"{rel(g4dir)}/header.json: the pre-D156 comparison recorded is not what the rows give")
    return rows, tables, header, rows6, grid


def box_stats(vals) -> dict:
    """A-1's box of one system at one cap (the draft's numbers: numpy linear percentiles, np.median)."""
    a = np.asarray(vals, dtype=float)
    q1, q3 = np.percentile(a, [25, 75])
    return {"median_pct": float(np.median(a)), "q1_pct": float(q1), "q3_pct": float(q3), "min_pct": float(a.min()),
            "max_pct": float(a.max())}


def draw_range_rows(noise, l2rows, caps, field, subset, a_cols) -> list:
    """Sheet a's 'draw_range' rows: per cap and system, the mean concept recall (%) over D98's questions at each draw,
    failed answers kept at their stored value (Rule 10), then the smallest mean, the largest and the range between them
    in points. A mean, since the noise table holds means (S514 l2g7's table). Mentori RLM's means come from noise_tables.json; package
    RLM's from the same rows a draws, by the same rule. While noise_tables.json has read draw 1 alone, there is no
    run-to-run range for Mentori RLM, so every value cell stays blank and the strip draws its axis only."""
    read = list(noise["draws_read"]) if noise else [1]
    out = []
    sub = sorted(subset)
    for s, info in S475.SYSTEMS.items():
        for c in caps:
            if len(read) < 2:
                lo, hi, used = None, None, "1"
            elif s == "G5":
                e = noise["per_cap"][str(c)]
                lo, hi, used = 100 * e["min"], 100 * e["max"], ", ".join(str(d) for d in read)
            else:
                ms = []
                for d in sorted({r["draw"] for r in l2rows if r["system"] == s}):
                    R = [r for r in l2rows if r["system"] == s and r["cap"] == c and r["draw"] == d
                         and r["question_id"] in subset]
                    if len(R) != len(sub):
                        raise Refused(f"range strip: {s} cap {c} draw {d} holds {len(R)} of {len(sub)} questions")
                    ms.append(100 * float(np.mean([r[field] for r in R])))
                lo, hi, used = min(ms), max(ms), ", ".join(str(d) for d in sorted({r["draw"] for r in l2rows if r["system"] == s}))
            out.append({**{k: None for k in a_cols}, "row": "draw_range", "system": s, "system_name": info["sheet_name"],
                        "cap": c, "questions": len(sub), "draws_read": used, "draw_min_pct": lo, "draw_max_pct": hi,
                        "range_pp": None if lo is None else hi - lo})
    return out


def a_with_boxes(a_rows, caps) -> list:
    """S475's sheet a with A-1's box columns on each 'cap' row, from the sheet's own 'question' rows."""
    out = []
    for r in a_rows:
        r = dict(r)
        if r["row"] == "cap":
            v = [x["value_pct"] for x in a_rows if x["row"] == "question" and x["system"] == r["system"]
                 and x["cap"] == r["cap"]]
            if len(v) != r["questions"]:
                raise Refused(f"a {r['system']} cap {r['cap']}: {len(v)} question rows, the cap row says "
                              f"{r['questions']}")
            r.update(box_stats(v))
        else:
            r.update({k: None for k in A_BOX_COLS})
        out.append({k: r.get(k) for k in A_COLS})
    return out


def gemini_ref(l2rows, a_rows, t1caps, complete, field: str = "concept_recall_loose") -> list:
    """b's reference (B-2): per T1 cap, the median over T1's complete questions of Mentori's RLM with
    gemini-3-flash-preview, from L2's G5 rows (draw 1, one row per question and cap) on field (the loose value, or
    D181's concept_recall when b draws T1_L2_d181, D188), equal to the median of sheet a's G5 question rows on the same
    questions (two paths to one number; a_rows on the same field)."""
    g = [r for r in l2rows if r["system"] == "G5"]
    draws = sorted({r["draw"] for r in g})
    if draws not in ([1], [1, 2, 3]):                # D284: draws 1 to 3 on all 86; a question's value is its mean
        raise Refused(f"L2's G5 rows carry draws {draws}, not draw 1 only or draws 1 to 3")
    qs = sorted(complete)
    out = []
    for c in t1caps:
        by_q = collections.defaultdict(list)
        for r in g:
            if r["cap"] == c:
                by_q[r["question_id"]].append(r)
        if not by_q:
            raise Refused(f"G5 has no answers at T1's cap {c}")
        miss = [q for q in qs if len(by_q.get(q, [])) != len(draws)]
        if miss:
            raise Refused(f"G5 at cap {c}: T1's complete questions {miss[:3]} lack exactly one answer per draw")
        v = [100 * float(np.mean([x[field] for x in by_q[q]])) for q in qs]
        va = {x["question_id"]: x["value_pct"] for x in a_rows if x["row"] == "question" and x["system"] == "G5"
              and x["cap"] == c}
        if [va.get(q) for q in qs] != v:
            raise Refused(f"G5 cap {c}: L2's values on T1's questions differ from the data workbook's a rows")
        out.append({"row": "gemini_ref", "model": GEMINI_REF_NAME, "cap": c, "questions_complete": len(qs),
                    "answers": len(qs), "median_pct": float(np.median(v)) if qs else None,
                    "mean_pct": float(np.mean(v)) if qs else None, "failed": sum(by_q[q][0]["failed"] for q in qs),
                    "cap_reached_n": sum(by_q[q][0]["cap_reached"] for q in qs),
                    "stopped_by_cap_n": sum(by_q[q][0]["stopped_by_cap"] for q in qs)})
    return out


def b_sheet(t1rows, t1tab, gref=(), d181: bool = False):
    """Sheet Supplementary Fig. 8b. Each answer row's recall_pct is the value drawn: T1_L2's loose concept recall, or with d181
    (D188, T1_L2_d181's rows) D181's concept_recall; recall_loose_pct and recall_exact_pct are the loose matcher and the
    exact test on the same concepts (with d181 the rows' base values on key v2.5), 0 for a failed answer."""
    field = "concept_recall" if d181 else "concept_recall_loose"
    out = []
    for c in t1tab["cells"]:
        v = [100 * r[field] for r in t1rows if r["model"] == c["model"] and r["cap"] == c["cap"]
             and r["in_complete_question"]]
        if len(v) != c["questions_complete"]:
            raise Refused(f"b {c['model']} cap {c['cap']}: {len(v)} complete answers, the table says "
                          f"{c['questions_complete']}")
        out.append({"row": "cap", "model": c["model"], "cap": c["cap"], "questions_complete": c["questions_complete"],
                    "answers": c["answers"], "median_pct": float(np.median(v)) if v else None,
                    "mean_pct": None if c["mean"] is None else 100 * c["mean"],
                    "ci95_lo_pct": None if c["ci95"] is None else 100 * c["ci95"][0],
                    "ci95_hi_pct": None if c["ci95"] is None else 100 * c["ci95"][1], "failed": c["failed"],
                    "cap_reached_n": c["cap_reached_n"], "stopped_by_cap_n": c["stopped_by_cap_n"]})
    out += [dict(r) for r in gref]
    for r in t1rows:
        if d181:
            lo_, ex_ = (0.0, 0.0) if r["failed"] else (r["concept_recall_loose_base"], r["concept_recall_exact_base"])
        else:
            lo_, ex_ = r["concept_recall_loose"], r["concept_recall_exact"]
        out.append({"row": "answer", "model": r["model"], "cap": r["cap"], "question_id": r["question_id"],
                    "in_complete_question": r["in_complete_question"], "recall_pct": 100 * r[field],
                    "recall_loose_pct": 100 * lo_, "recall_exact_pct": 100 * ex_, "failed": r["failed"],
                    "stop_reason": r["stop_reason"], "turns_used": r["turns_used"], "answer_key": r["answer_key"]})
    return [{k: r.get(k) for k in B_COLS} for r in out]


GRID_COLS = ["row", "score", "index", "core_papers", "distractor_ratio", "strategy", "complete", "n_paired",
             "pass_strategy_pct", "pass_single_pass_pct", "d_pp", "ci95_lo_pp", "ci95_hi_pp", "interval_excludes_0",
             "p_signflip_two_sided", "d_sign", "d_size_pp"]


def grid_sheet(grid, mut=None) -> list:
    """Sheet Supplementary Fig. 8c (D150): one 'cell' row per judge score, strategy and index, in the grid's order within a score;
    score 4 (the pass rate) first, then 3 (the relaxed threshold), D154."""
    by = {(e["score"], e["index"], e["strategy"]): e for e in grid["cells"]}
    out = []
    for e in [e for sc in PLATE_SCORES for e in grid["cells"] if e["score"] == sc]:
        src = by[(3, e["index"], e["strategy"])] if mut == "c_s4_from_s3" and e["score"] == 4 else e
        r = {"row": "cell", "score": e["score"], "index": e["index"], "core_papers": e["core_papers"],
             "distractor_ratio": e["distractor_ratio"], "strategy": e["strategy"], "complete": e["complete"]}
        if e["complete"]:
            lo, hi = src["ci95_pp"]
            r.update(n_paired=src["n_paired"], pass_strategy_pct=src["pass_strategy_pct"],
                     pass_single_pass_pct=src["pass_single_pass_pct"], d_pp=src["d_pp"], ci95_lo_pp=lo, ci95_hi_pp=hi,
                     interval_excludes_0=bool(lo > 0 or hi < 0), p_signflip_two_sided=src["p_signflip"],
                     d_sign=d_sign_of(src["d_pp"]), d_size_pp=abs(src["d_pp"]))
        out.append({k: r.get(k) for k in GRID_COLS})
    return out


def d_sign_of(d) -> str:
    """The sign printed before a grid number: + or U+2212, none when it rounds to 0.0 (build_order.md F6: S448 R8 ties
    "{d_sign}{d_size_pp:.1f}" from two sheet columns, and has no reading of U+2212 in a number format)."""
    return "" if S457.half_up(abs(d), 1) == "0.0" else ("+" if d > 0 else hs.MINUS)


def cell_text(d) -> str:
    """A grid number as printed: one decimal, half up, a plus sign above 0, U+2212 below it."""
    return d_sign_of(d) + S457.half_up(abs(d), 1)


def write_source_data(sheets, path):
    S475.write_source_data(sheets, path)
    fig_repro.deterministic_xlsx(path)                 # D155: no write time in core.xml or the zip members


def untied_digits(fig, printed_gids, axes) -> list:
    """Every visible text holding a digit must be a tick label or carry a gid of the printed map."""
    from matplotlib.text import Text
    ticks = set()
    for ax in axes:
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            ticks.add(id(t))
    bad = []
    for t in fig.findobj(Text):
        if t.get_visible() and re.search(r"\d", t.get_text()) and id(t) not in ticks and t.get_gid() not in printed_gids:
            bad.append(t.get_text())
    return bad


def hatch_segments(w, h, step=0.8):
    """The hatching of a w x h mm bar as plain line segments (slope 1, step mm apart) inside it, in mm from its
    lower left corner: S448 reads plain strokes, and an SVG pattern fill is not one."""
    out, k = [], -w + step / 2
    while k < h:
        x0, x1 = max(0.0, -k), min(w, h - k)
        if x1 - x0 > 1e-6:
            out.append(((x0, x0 + k), (x1, x1 + k)))
        k += step
    return out


def draw_figure(fn, caps, t1caps, paths, mut=None, part="ab"):
    """part "ab": main Figure 4, panels a (with its two strips) and b; part "c": Supplementary Figure 8, the grid alone,
    with no letter (D283). The layout of each part is the one both had on the single plate before D283."""
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

    PT, FONT, MM_PT = S475.PT, S475.FONT, S475.MM_PT
    OKABE, SYSTEMS = S475.OKABE, S475.SYSTEMS
    LW = S475.LW_MEAN
    plt.rcParams.update(S457.plate_rc("S476"))
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["hatch.linewidth"] = 0.5
    t2p = TextToPath()

    def tw(s):
        return t2p.get_text_width_height_descent(s, FontProperties(family=FONT, size=PT), ismath=False)[0] * MM_PT

    W = S475.FIG_W_MM
    RIGHT = 2.0
    LINE = PT * MM_PT * 1.25
    XAX = 2 * MM_PT + 2 * MM_PT + LINE + 2 * MM_PT + LINE
    PITCH = 3.5
    # layout O-b1 (D150, Valerio 26 October 19:00): a with its strip (D149) left and b right on top, c full width below
    G_LEFT, G_GAP, PADC, CELL_H, KEYC_H = 28.0, 2.4, 0.3, 4.4, 2.4      # c, the grid
    CELL_W = (W - G_LEFT - RIGHT - 3 * G_GAP) / 12
    C_H = KEYC_H + 1.0 + LINE + 1.5 + 2 * 5 * CELL_H + 3.0 + 1.2 + 3 * LINE + 1.6 + 1.0
    CY0_FULL = S475.FIG_H_MAX_MM - 0.4 - C_H    # where c began on the single plate; a and b keep their sizes
    TOP_H = CY0_FULL - 3.0                           # a and b end here, their x axes included
    CY0 = CY0_FULL if part == "ab" else 1.0          # c alone (D283): its colour key at the top of its own page
    LEFT, AX_W = 13.0, 84.0                          # a and its strip
    KEY1 = 3.4
    KEY2 = KEY1 + 2 * 3.5                            # the systems on two lines, the strip's key on the third
    A_TOP = KEY2 + 2.7
    STRIP_H, STRIP_GAP = 12.0, 2.0
    RANGE_H, RANGE_GAP = 6.0, 3.8                    # supp.md section 7 and its R3: 8 to 6 mm, a's height kept; the
    #                                                  gap holds the strip's axis words, too long to stand beside 6 mm
    A_H = TOP_H - XAX - RANGE_H - RANGE_GAP - STRIP_H - STRIP_GAP - A_TOP
    HEAD0 = 3.4                                      # b's key
    BX, BW, B_NCOL = 112.0, 69.0, 2
    R2_TOP, R2_H = 0.0, TOP_H - XAX                  # b's panels end at R2_TOP + R2_H
    GRID0 = CY0 + KEYC_H + 1.0 + LINE + 1.5
    BLOCK_H, BLOCK_GAP = 5 * CELL_H, 3.0
    YB = GRID0 + 2 * BLOCK_H + BLOCK_GAP + 1.2
    H = YB + 3 * LINE + 1.6 + 1.0 if part == "c" else TOP_H + 1.0
    if H > S475.FIG_H_MAX_MM - 0.05:
        raise Refused(f"the page would be {H:.1f} mm high, over [page] height_max_mm {S475.FIG_H_MAX_MM}")
    SC = (AX_W / len(caps)) / 16.5                   # a's marks scale with its mm per cap (16.5 on the full-width a)
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
        text_mm(x, y, S475.LETTER_CASE(s), fontsize=S475.PT_LETTER, fontweight=S475.LETTER_WEIGHT, va="center",
                ha="left")

    def marker_mm(x, y, colour, marker, size=1.5):
        fig.add_artist(Line2D([x / W], [1 - y / H], transform=fig.transFigure, ls="none", marker=marker,
                              ms=size / MM_PT, color=colour, mfc=colour, mec=colour, mew=0))

    XLO, XHI = 0.85, 58.0
    nC = len(caps)
    A_SLOT = AX_W / nC                               # A-1: caps evenly spaced, mm per cap
    A_OFF, A_HALF, A_BOXH = 3.9 * SC, 3.4 * SC, 2.6 * SC            # mm: system offset from the cap, dot strip half width, box half width
    if 2 * (A_OFF + A_HALF + S475.DOT_MM / 2) >= A_SLOT or A_OFF - A_HALF - S475.DOT_MM / 2 <= 0:
        raise Refused(f"a: the dot strips would touch ({A_SLOT:.1f} mm per cap)")

    def spines(ax):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    def y_axis(ax, ylabel, ylim, yticks, labels=True):
        ax.set_ylim(*ylim)
        ax.yaxis.set_major_locator(FixedLocator(yticks))
        ax.yaxis.set_major_formatter(FixedFormatter([str(v) for v in yticks] if labels else [""] * len(yticks)))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_ylabel(ylabel, labelpad=2)

    def cap_axis(ax, ticks, labels, ylabel, ylim, yticks, ylabels=True, xlabel="turn cap"):
        ax.set_xscale("log")
        ax.set_xlim(XLO, XHI)
        ax.xaxis.set_major_locator(FixedLocator(list(ticks)))
        ax.xaxis.set_major_formatter(FixedFormatter(labels))
        ax.xaxis.set_minor_locator(NullLocator())
        y_axis(ax, ylabel, ylim, yticks, ylabels)
        ax.set_xlabel(xlabel, labelpad=2)
        spines(ax)

    from matplotlib.colors import to_hex
    ax = sx = rx = None
    b_axes, b_style, strip_bars, grid_drawn = [], [], [], []
    B_MW = B_MH = None
    LW_BOX, LW_MED = max(0.5, S475.LINE_MIN_PT), 1.6
    if part == "ab":
        a_rows = fn["a"]
        a_idx = {(r["system"], r["cap"]): i for i, r in enumerate(a_rows) if r["row"] == "cap"}
        d_idx = {(r["system"], r["cap"]): i for i, r in enumerate(fn["d"])}

        # ---- a (A-1, Valerio 26 October; D128): per cap two boxes, Mentori's RLM left, the package right; no mean
        ax = axes_mm(LEFT, A_TOP, AX_W, A_H)
        unit = 1.0 / A_SLOT                              # x data units per mm (caps at 0 .. nC-1)
        ax.set_xlim(-0.5, nC - 0.5)
        ax.xaxis.set_major_locator(FixedLocator(list(range(nC))))
        ax.xaxis.set_major_formatter(FixedFormatter([""] * nC))
        ax.xaxis.set_minor_locator(NullLocator())
        y_axis(ax, "Concept recall (%)", (-2, 102), [0, 25, 50, 75, 100])
        spines(ax)
        y_mm = A_H / 104.0                               # mm per y unit
        for s, info in SYSTEMS.items():
            col = info["colour"]
            meds = []
            for i, c in enumerate(caps):
                r = a_rows[a_idx[(s, c)]]
                vals = [x["value_pct"] for x in a_rows if x["row"] == "question" and x["system"] == s and x["cap"] == c]
                x0 = i + info["side"] * A_OFF * unit
                off, over = S457.swarm([v * y_mm for v in vals], half=A_HALF, pitch=S475.DOT_PITCH_MM, dot=S475.DOT_MM)
                overlaps[f"{s} cap {c}"] = over
                ln, = ax.plot([x0 + o * unit for o in off], vals, ls="none", marker="o", ms=S475.DOT_MM / MM_PT, color=col, mfc=col,
                              mew=0, zorder=2, clip_on=False)
                readback.append((f"a {s} cap {c} dots", list(ln.get_ydata()), vals))
                hb = A_BOXH * unit
                q3 = r["q3_pct"] + (0.5 if mut == "box_off" else 0.0)
                ln, = ax.plot([x0 - hb, x0 + hb, x0 + hb, x0 - hb, x0 - hb], [r["q1_pct"], r["q1_pct"], q3, q3, r["q1_pct"]],
                              color="#000000", lw=LW_BOX, solid_joinstyle="miter", zorder=5)
                readback.append((f"a {s} cap {c} box", list(ln.get_ydata()), [r["q1_pct"], r["q1_pct"], r["q3_pct"],
                                                                              r["q3_pct"], r["q1_pct"]]))
                for nm_, ys_ in (("lower whisker", [r["min_pct"], r["q1_pct"]]), ("upper whisker", [r["q3_pct"], r["max_pct"]])):
                    ln, = ax.plot([x0, x0], ys_, color="#000000", lw=LW_BOX, solid_capstyle="butt", zorder=5)
                    readback.append((f"a {s} cap {c} {nm_}", list(ln.get_ydata()), ys_))
                for nm_, yc_ in (("lower cap", r["min_pct"]), ("upper cap", r["max_pct"])):   # 5/12 of the box's thickness
                    ln, = ax.plot([x0 - hs.CAP_FRAC * hb, x0 + hs.CAP_FRAC * hb], [yc_] * 2, color="#000000",
                                  lw=hs.LW["whisker"], solid_capstyle="butt", zorder=5)
                    readback.append((f"a {s} cap {c} {nm_}", list(ln.get_ydata()), [yc_] * 2))
                ln, = ax.plot([x0 - hb, x0 + hb], [r["median_pct"]] * 2, color="#000000", lw=hs.LW["median"],
                              solid_capstyle="butt", zorder=6)
                readback.append((f"a {s} cap {c} median", list(ln.get_ydata()), [r["median_pct"]] * 2))
                meds.append((x0, r["median_pct"]))
            ln, = ax.plot([m_[0] for m_ in meds], [m_[1] for m_ in meds], color=col, lw=LW_BOX, zorder=4)
            readback.append((f"a {s} line joining the medians", list(ln.get_ydata()),
                             [a_rows[a_idx[(s, c)]]["median_pct"] for c in caps]))
        letter(1.5, KEY1, "a")
        for s, info in SYSTEMS.items():                  # each key line centred over a's plotting area
            col = info["colour"]
            g5_one = all((r["draws"] or 1) == 1 for r in a_rows if r["row"] == "question" and r["system"] == "G5")
            fmt = info["name"] + (", one draw" if s == "G5" and g5_one else ", mean of three draws") + ", n = {questions} questions"
            txt_ = fmt.format(questions=a_rows[a_idx[(s, caps[0])]]["questions"])
            x0k = LEFT + AX_W / 2 - (hs.KEY_MARK_MM + 0.8 + tw(txt_)) / 2
            marker_mm(x0k + hs.KEY_MARK_MM / 2, KEY1, col, "o", size=hs.KEY_MARK_MM)
            t = text_mm(x0k + hs.KEY_MARK_MM + 0.8, KEY1, txt_, va="center", ha="left")
            num(t, {"sheet": f"{MAIN_SHEET}a", "row": a_idx[(s, caps[0])], "format": fmt})
            KEY1 += 3.5                                  # O-b1: one system per key line
        # ---- the strip under a (D-3, Valerio 26 October 18:20): bars side by side, aligned with a's boxes
        sx = axes_mm(LEFT, A_TOP + A_H + STRIP_GAP, AX_W, STRIP_H)
        sx.set_xlim(-0.5, nC - 0.5)
        sx.xaxis.set_major_locator(FixedLocator(list(range(nC))))
        sx.xaxis.set_major_formatter(FixedFormatter([""] * nC))
        sx.xaxis.set_minor_locator(NullLocator())
        y_axis(sx, "Answers (%)", (0, 104), [0, 50, 100])
        spines(sx)
        s_idx = {(r["system"], r["cap"]): i for i, r in enumerate(a_rows) if r["row"] == "strip"}
        strip_bars = []                                  # (system, cap, what, value drawn, hatch lines drawn)
        for s, info in SYSTEMS.items():
            col = info["colour"]
            for i, c in enumerate(caps):
                r = a_rows[s_idx[(s, c)]]
                x0 = i + info["side"] * A_OFF * unit
                bw = 2.3 * SC * unit
                bars = [(x0 - 1.25 * SC * unit, bw, "cap_reached_pct", False), (x0 + 1.25 * SC * unit, bw, "stopped_by_cap_pct", True)]
                for xb, wb, k, hatched in bars:
                    v = r[k]
                    if mut == "strip_reached_as_cutoff" and k == "stopped_by_cap_pct":
                        v = r["cap_reached_pct"]
                    if mut == "strip_cutoff_plain":
                        hatched = False
                    nh = 0
                    if hatched:                          # outline, and the hatching drawn as plain lines inside it
                        br = sx.bar([xb], [v], width=wb, bottom=0, facecolor="#FFFFFF", edgecolor=col,
                                    linewidth=LW_BOX, zorder=2)[0]
                        w_mm, h_mm = wb / unit, v * STRIP_H / 104.0
                        for (u0, v0), (u1, v1) in hatch_segments(w_mm, h_mm):
                            sx.plot([xb - wb / 2 + u0 * unit, xb - wb / 2 + u1 * unit],
                                    [v0 * 104.0 / STRIP_H, v1 * 104.0 / STRIP_H], color=col, lw=LW_BOX,
                                    solid_capstyle="butt", zorder=3)
                            nh += 1
                    else:
                        br = sx.bar([xb], [v], width=wb, bottom=0, color=col, linewidth=0, zorder=2)[0]
                    readback.append((f"strip {s} cap {c} {k}", [br.get_y(), br.get_y() + br.get_height()], [0.0, r[k]]))
                    strip_bars.append((s, c, k, v, nh))
        # D149 held: every cut-off bar with a height is hatched, no reached bar is
        bad_strip = [f"{s} cap {c} {k}" for s, c, k, v, nh in strip_bars
                     if (k == "stopped_by_cap_pct" and v > 0 and nh == 0) or (k == "cap_reached_pct" and nh)]
        if bad_strip:
            plt.close(fig)
            raise Refused(f"the strip's cut-off bars must be hatched and its reached bars plain: {bad_strip[:3]}")
        # key line 2 (D149): what each strip bar stands for, a swatch per system colour
        kw_ = sum(2 * 3.2 + 0.6 + tw(lb_) for lb_ in ("reached the cap", "cut off by the cap")) + 6.0
        xk = LEFT + AX_W / 2 - kw_ / 2                   # the strip's key line centred over a's plotting area
        for hatched, lab in ((False, "reached the cap"), (True, "cut off by the cap")):
            for s, info in SYSTEMS.items():
                fig.add_artist(Rectangle((xk / W, 1 - (KEY2 + 1.1) / H), 2.4 / W, 2.2 / H, transform=fig.transFigure,
                                         facecolor="#FFFFFF" if hatched else info["colour"],
                                         edgecolor=info["colour"] if hatched else "none", lw=LW_BOX if hatched else 0))
                if hatched:
                    for (u0, v0), (u1, v1) in hatch_segments(2.4, 2.2):
                        fig.add_artist(Line2D([(xk + u0) / W, (xk + u1) / W],
                                              [1 - (KEY2 + 1.1 - v0) / H, 1 - (KEY2 + 1.1 - v1) / H],
                                              transform=fig.transFigure, color=info["colour"], lw=LW_BOX,
                                              solid_capstyle="butt"))
                xk += 3.2
            text_mm(xk + 0.6, KEY2, lab, va="center", ha="left")
            xk += 0.6 + tw(lab) + 6.0
        # ---- the range strip under the first (FF30 a; supp.md section 7): the run-to-run range per cap and system, bars
        # under each system's box; an axis alone until Mentori RLM's draws 2 and 3 are scored
        rx = axes_mm(LEFT, A_TOP + A_H + STRIP_GAP + STRIP_H + RANGE_GAP, AX_W, RANGE_H)
        rx.set_xlim(-0.5, nC - 0.5)
        rx.xaxis.set_major_locator(FixedLocator(list(range(nC))))
        rx.xaxis.set_major_formatter(FixedFormatter([str(c) for c in caps]))
        rx.xaxis.set_minor_locator(NullLocator())
        rx.set_xlabel("Turn cap (caps evenly spaced)", labelpad=2)
        range_rows = [r for r in a_rows if r["row"] == "draw_range"]
        top_r = max([r["range_pp"] for r in range_rows if r["range_pp"] is not None] + [10.0])
        top_r = 5 * math.ceil(top_r / 5 - 1e-12)
        y_axis(rx, "", (0, top_r), [0, top_r])
        spines(rx)
        text_mm(LEFT + 1.0, A_TOP + A_H + STRIP_GAP + STRIP_H + RANGE_GAP - 0.3, "Range over draws (points)", va="bottom",
                ha="left")
        for r in range_rows:
            if r["range_pp"] is None:
                continue
            info = SYSTEMS[r["system"]]
            br = rx.bar([caps.index(r["cap"]) + info["side"] * A_OFF * unit], [r["range_pp"]], width=2.3 * SC * unit, bottom=0,
                        color=info["colour"], linewidth=0, zorder=2)[0]
            readback.append((f"range {r['system']} cap {r['cap']}", [br.get_y(), br.get_y() + br.get_height()],
                             [0.0, r["range_pp"]]))
        # D147 (Valerio, 26 October 16:10): a's key is the colour key only; box, median, whiskers and dots are defined
        # in the written legend (editor row 47, [legend] errors_defined), never in words on the plate
        if mut == "a_words_key":
            text_mm(LEFT, KEY1 + 3.8, "box: quartiles; thick line: median; whiskers: range; dot: one question",
                    va="center", ha="left")

        # ---- b (B-2, Valerio 26 October): one small panel per local model, a line per question, the median, and the
        # median of the same questions with gemini-3-flash-preview; the key is line samples and meanings only
        bcap = {(r["model"], r["cap"]): r for r in fn["b"] if r["row"] == "cap"}
        gref = {r["cap"]: r for r in fn["b"] if r["row"] == "gemini_ref"}
        bq = collections.defaultdict(dict)
        for r in fn["b"]:
            if r["row"] == "answer" and r["in_complete_question"]:
                bq[(r["model"], r["cap"])][r["question_id"]] = r["recall_pct"]
        bqs = sorted(bq[(T1_FOUR[0], t1caps[0])])
        LW_Q, LW_BMED, LW_REF = max(LW_Q_MIN, S475.LINE_MIN_PT), LW * 1.4, LW * 1.2
        B_GAP, NAME_H = 3.5, 3.2
        TICKD = 2 * MM_PT + 2 * MM_PT + LINE             # an x axis with tick labels and no axis name
        B_ROW0 = HEAD0 + PITCH + 2.3                     # top of the first row of names
        B_NROW = 4 // B_NCOL
        B_MW = (BW - (B_NCOL - 1) * B_GAP) / B_NCOL
        B_MH = (R2_TOP + R2_H - (B_ROW0 + NAME_H) - (B_NROW - 1) * (TICKD + 1.0 + NAME_H)) / B_NROW
        if B_MH < 20.0:
            raise Refused(f"b: the small panels would be {B_MH:.1f} mm high")
        b_axes = []
        bx_pos = list(range(len(t1caps)))               # Valerio, 26 October: b's caps evenly spaced, as a's
        b_style = []                                     # (what, colour, x positions) of every line b draws
        for i, m in enumerate(T1_FOUR):
            row_, colm = divmod(i, B_NCOL)
            x_ = BX + colm * (B_MW + B_GAP)
            y_ = B_ROW0 + row_ * (NAME_H + B_MH + TICKD + 1.0)
            num(text_mm(x_, y_ + 1.4, m, va="center", ha="left"), {"fixed": m, "why": "the model's Ollama tag"})
            bxi = axes_mm(x_, y_ + NAME_H, B_MW, B_MH)
            bxi.set_xlim(-0.5, len(t1caps) - 0.5)
            bxi.xaxis.set_major_locator(FixedLocator(bx_pos))
            bxi.xaxis.set_major_formatter(FixedFormatter([str(c) for c in t1caps]))
            bxi.xaxis.set_minor_locator(NullLocator())
            y_axis(bxi, "Concept recall (%)" if colm == 0 else "", (-2, 102), [0, 25, 50, 75, 100], labels=(colm == 0))
            spines(bxi)
            if mut == "b_log_x":
                bxi.set_xscale("log")
                bxi.set_xlim(XLO, XHI)
            xs_ = list(t1caps) if mut == "b_log_x" else bx_pos
            b_axes.append(bxi)
            qcol = OKABE[MODEL_COLOUR_MUT[m]] if mut == "b_model_colours" else Q_GREY
            for q in bqs:
                ys_ = [bq[(m, c)][q] for c in t1caps]
                ln, = bxi.plot(xs_, ys_, color=qcol, lw=LW_Q, marker="o", ms=0.45 / MM_PT, mew=0, zorder=3,
                               clip_on=False)
                readback.append((f"b {m} {q}", list(ln.get_ydata()), ys_))
                b_style.append(("question", ln.get_color(), list(ln.get_xdata())))
            want = [bcap[(m, c)]["median_pct"] for c in t1caps]
            ln, = bxi.plot(xs_, want, color="#000000", lw=LW_BMED, solid_capstyle="butt", zorder=4, clip_on=False)
            readback.append((f"b {m} median", list(ln.get_ydata()), want))
            b_style.append(("median", ln.get_color(), list(ln.get_xdata())))
            want = [gref[c]["median_pct"] for c in t1caps]
            drawn = [v + (0.5 if mut == "gemref_off" else 0.0) for v in want]
            ln, = bxi.plot(xs_, drawn, color=GEMINI_REF_COLOUR, lw=LW_REF, solid_capstyle="butt",
                           dash_capstyle="butt", zorder=5, clip_on=False)
            if GEMINI_REF_DASHES:
                ln.set_dashes(GEMINI_REF_DASHES)
            readback.append((f"b {m} gemini-3-flash-preview reference", list(ln.get_ydata()), want))
            b_style.append(("reference", ln.get_color(), list(ln.get_xdata())))
        # Valerio's follow-up, held: every question line one grey, the median black, the reference GEMINI_REF_COLOUR,
        # every line at the evenly spaced positions, each panel's ticks the caps
        from matplotlib.colors import to_hex
        want_col = {"question": Q_GREY, "median": "#000000", "reference": GEMINI_REF_COLOUR}
        bad_style = sorted({f"{w} {to_hex(c).upper()} at x {xd}" for w, c, xd in b_style
                            if to_hex(c).upper() != want_col[w].upper() or [float(v) for v in xd] != bx_pos})
        for a_ in b_axes:
            if a_.get_xscale() != "linear" or list(a_.get_xticks()) != bx_pos or \
                    [tl.get_text() for tl in a_.get_xticklabels()] != [str(c) for c in t1caps]:
                bad_style.append("a small panel of b whose caps are not evenly spaced and labelled")
        if bad_style:
            plt.close(fig)
            raise Refused(f"b: lines or cap axis not as Valerio's follow-up of 26 October: {bad_style[:2]}")
        text_mm(BX + BW / 2, R2_TOP + R2_H + XAX - LINE / 2, "Turn cap (caps evenly spaced)", va="center", ha="center")
        BK1 = BX + BW / 2 - (6.2 + tw("one question") + 5.0 + 6.2 + tw("median")) / 2   # b's keys centred over its panels
        fig.add_artist(Line2D([BK1 / W, (BK1 + 5.0) / W], [1 - HEAD0 / H] * 2, transform=fig.transFigure,   # key
                              color=Q_GREY, lw=LW_Q, solid_capstyle="butt"))
        text_mm(BK1 + 6.2, HEAD0, "one question", va="center", ha="left")
        xk = BK1 + 6.2 + tw("one question") + 5.0
        fig.add_artist(Line2D([xk / W, (xk + 5.0) / W], [1 - HEAD0 / H] * 2, transform=fig.transFigure, color="#000000",
                              lw=LW_BMED, solid_capstyle="butt"))
        text_mm(xk + 6.2, HEAD0, "median", va="center", ha="left")
        gk = f"{GEN_DISPLAY}, median"
        BK2 = BX + BW / 2 - (7.2 + tw(gk)) / 2
        kl = Line2D([BK2 / W, (BK2 + 6.0) / W], [1 - (HEAD0 + PITCH) / H] * 2, transform=fig.transFigure,
                    color=GEMINI_REF_COLOUR, lw=LW_REF, solid_capstyle="butt", dash_capstyle="butt")
        if GEMINI_REF_DASHES:
            kl.set_dashes(GEMINI_REF_DASHES)
        fig.add_artist(kl)
        num(text_mm(BK2 + 7.2, HEAD0 + PITCH, gk, va="center", ha="left"),
            {"fixed": gk, "why": "the model's name; the reference line's key"})
        letter(BX - 12.0, HEAD0, "b")

    if part == "c":
        # ---- c (D150, layout O-b1): every strategy minus single pass per index, score 4 above score 3 (D154), one scale
        import matplotlib as _mpl
        from matplotlib.colors import to_hex as _hex
        cmap = _mpl.colormaps[S475.FLOCK["colour"]["continuous"]]
        lim = fn["c_scale"]
        c_rows = fn["c"]
        c_idx = {(r["score"], r["index"], r["strategy"]): i for i, r in enumerate(c_rows)}
        c_indexes = sorted({r["index"] for r in c_rows}, key=index_parts)
        if len(c_indexes) != 12:
            raise Refused(f"c: {len(c_indexes)} indexes, not 12")
        label = dict(S457.G1)

        def ccol_x(i):
            return G_LEFT + i * CELL_W + (i // 3) * G_GAP

        def frect(x, y, w, h, **kw):
            r_ = Rectangle((x / W, 1 - (y + h) / H), w / W, h / H, transform=fig.transFigure, **kw)
            fig.add_artist(r_)
            return r_

        def lum(rgb):
            f_ = [c_ / 12.92 if c_ <= 0.04045 else ((c_ + 0.055) / 1.055) ** 2.4 for c_ in rgb[:3]]
            return 0.2126 * f_[0] + 0.7152 * f_[1] + 0.0722 * f_[2]
        KW = 50.0                                        # the colour scale: 256 vector strips (no raster, [colour] vector_only)
        for k_ in range(256):
            frect(G_LEFT + k_ * KW / 256, CY0, KW / 256 + 0.02, KEYC_H, facecolor=cmap(k_ / 255), edgecolor="none",
                  linewidth=0)
        for v in range(-10 * (lim // 10), 10 * (lim // 10) + 1, 10):
            xk_ = G_LEFT + (v + lim) / (2 * lim) * KW
            fig.add_artist(Line2D([xk_ / W] * 2, [1 - (CY0 + KEYC_H) / H, 1 - (CY0 + KEYC_H + 0.8) / H],
                                  transform=fig.transFigure, color="#000000", lw=LW_BOX, solid_capstyle="butt"))
            lab = "0" if v == 0 else (f"+{v}" if v > 0 else f"{hs.MINUS}{-v}")
            num(text_mm(xk_, CY0 + KEYC_H + 1.0, lab, ha="center", va="top"),
                {"fixed": lab, "why": "a tick of the colour scale, percentage points"})
        text_mm(G_LEFT + KW + 3.0, CY0 + KEYC_H / 2, "Pass rate minus single pass's (percentage points)", ha="left",
                va="center")
        grid_drawn = []                                  # (score, index, strategy, text or None, framed, fill)
        for b_, score in enumerate(PLATE_SCORES):
            top = GRID0 + b_ * (BLOCK_H + BLOCK_GAP)
            for j, strat in enumerate(GRID_STRATS):
                y = top + j * CELL_H
                t = text_mm(G_LEFT - 1.5, y + CELL_H / 2, label[strat], ha="right", va="center")
                if re.search(r"\d", label[strat]):
                    num(t, {"fixed": label[strat], "why": "the strategy's name"})
                for i, idx in enumerate(c_indexes):
                    ri = c_idx[(score, idx, strat)]
                    r = c_rows[ri]
                    x = ccol_x(i)
                    if not r["complete"]:
                        frect(x + PADC + 0.1, y + PADC + 0.1, CELL_W - 2 * PADC - 0.2, CELL_H - 2 * PADC - 0.2,
                              facecolor="none", edgecolor=Q_GREY, linewidth=LW_BOX)
                        grid_drawn.append((score, idx, strat, None, False, None))
                        continue
                    d = r["d_pp"] + (0.5 if mut == "c_off" else 0.0)
                    if abs(d) > lim:
                        raise Refused(f"c {idx} {strat} score {score}: {d} outside the scale +-{lim}")
                    fc = cmap((d + lim) / (2 * lim))
                    frect(x + PADC, y + PADC, CELL_W - 2 * PADC, CELL_H - 2 * PADC, facecolor=fc, edgecolor="none",
                          linewidth=0)
                    lf = lum(fc)
                    cb, cw = (lf + 0.05) / 0.05, 1.05 / (lf + 0.05)
                    tc = "#000000" if cb >= cw else "#FFFFFF"
                    if max(cb, cw) < S475.FLOCK["type"]["contrast_min_ratio"]:
                        raise Refused(f"c {idx} {strat}: number contrast {max(cb, cw):.2f}")
                    s = cell_text(d)
                    num(text_mm(x + CELL_W / 2, y + CELL_H / 2, s, ha="center", va="center", color=tc),
                        {"sheet": C_SHEET, "row": ri,
                         "format": "{d_sign}{d_size_pp:.1f}" if r["d_sign"] else "{d_size_pp:.1f}"})
                    readback.append((f"c {idx} {strat} score {score} cell", [d], [r["d_pp"]]))
                    framed = bool(r["interval_excludes_0"]) != (mut == "c_frame_wrong" and i == 0 and j == 0)
                    if framed:
                        ins = PADC + 0.45
                        frect(x + ins, y + ins, CELL_W - 2 * ins, CELL_H - 2 * ins, facecolor="none", edgecolor=tc,
                              linewidth=0.75)
                    grid_drawn.append((score, idx, strat, s, framed, _hex(fc)))
            lab = BLOCK_LABEL[score]
            num(text_mm(5.0, top + BLOCK_H / 2, lab, rotation=90, ha="center", va="center", multialignment="center"),
                {"fixed": lab, "why": "the judge score a pass needs (Rule 5, D154: 4 the pass rate, 3 relaxed)"})
        for i, idx in enumerate(c_indexes):
            lab = str(index_parts(idx)[1])
            num(text_mm(ccol_x(i) + CELL_W / 2, YB, lab, ha="center", va="top"),
                {"fixed": lab, "why": "distractor papers per core paper (the index's n<ratio>)"})
        text_mm(G_LEFT - 1.5, YB, "Distractors", ha="right", va="top")
        for g, core in enumerate((5, 10, 20, 50)):
            x0, x1 = ccol_x(3 * g) + PADC, ccol_x(3 * g + 2) + CELL_W - PADC
            fig.add_artist(Line2D([x0 / W, x1 / W], [1 - (YB + LINE + 0.6) / H] * 2, transform=fig.transFigure,
                                  color="#000000", lw=LW_BOX, solid_capstyle="butt"))
            num(text_mm((x0 + x1) / 2, YB + LINE + 1.0, str(core), ha="center", va="top"),
                {"fixed": str(core), "why": "core papers in the index (the index's s<core>)"})
        text_mm(G_LEFT + (W - G_LEFT - RIGHT) / 2, YB + 2 * LINE + 1.6, "Core papers in the index", ha="center", va="top")
        # D150 held: a number on every complete cell and only there, equal to the data workbook; a frame exactly where the
        # interval excludes 0
        bad_c = []
        for score, idx, strat, s, framed, _ in grid_drawn:
            r = c_rows[c_idx[(score, idx, strat)]]
            if (s is None) != (not r["complete"]):
                bad_c.append(f"{strat} {idx} score {score}: drawn {s is not None}, complete {r['complete']}")
            elif s is not None and (s != cell_text(r["d_pp"]) or framed != bool(r["interval_excludes_0"])):
                bad_c.append(f"{strat} {idx} score {score}: {s!r} framed {framed}, workbook {cell_text(r['d_pp'])!r} "
                             f"excludes 0 {r['interval_excludes_0']}")
        if bad_c:
            plt.close(fig)
            raise Refused(f"c's grid is not its data workbook: {bad_c[:3]}")

    if mut == "ninth_number":
        text_mm(60.0, HEAD0, "n = 9", va="center", ha="left")
    from matplotlib.text import Text
    style_words = re.compile(r"quartile|whisker|thick line|thin line|dashed|\bbox\b|\bdots?\b:", re.I)
    worded = [t_.get_text() for t_ in fig.findobj(Text) if t_.get_visible() and style_words.search(t_.get_text())]
    if worded:                                       # D147, and B-2's key: marks are defined in the legend only
        plt.close(fig)
        raise Refused(f"the plate names marks or line styles in words: {worded[:2]}")
    bad = untied_digits(fig, set(printed), [a_ for a_ in (ax, sx, rx, *b_axes) if a_ is not None])
    if bad:
        plt.close(fig)
        raise Refused(f"texts holding a digit tied to no data workbook cell and not a tick label: {bad[:4]}")
    # the x tick labels of d and of b's small panels must not touch
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    for nm_, axx in ([("strip", rx)] if rx is not None else []) + [(f"b {m}", a_) for m, a_ in zip(T1_FOUR, b_axes)]:
        boxes = [t.get_window_extent(rend) for t in axx.get_xticklabels() if t.get_text()]
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if a.x0 < b.x1 and b.x0 < a.x1:
                    plt.close(fig)
                    raise Refused(f"two tick labels of {nm_} overlap")
    if mut == "shift_drawn":
        w, got, want = readback[0]
        readback[0] = (w, [got[0] + 0.5] + got[1:], want)
    bad_c = hs.check_figure_colours(fig)
    if bad_c:
        plt.close(fig)
        raise Refused(f"colours outside the house palette: {bad_c}")
    S457.finish_plate(fig, W, H, paths, title=MAIN_LABEL if part == "ab" else SI_LABEL)
    b_summary = {"question_line_colours": sorted({to_hex(c).upper() for w, c, _ in b_style if w == "question"}),
                 "x_positions": sorted({tuple(float(v) for v in xd) for _, _, xd in b_style}),
                 "question_lines": sum(1 for w, _, _ in b_style if w == "question"),
                 "strip": [{"system": s, "cap": c, "what": k, "value": v, "hatch_lines": nh}
                           for s, c, k, v, nh in strip_bars],
                 "grid": [{"score": sc_, "index": ix_, "strategy": st_, "text": tx_, "framed": fr_, "fill": fl_}
                          for sc_, ix_, st_, tx_, fr_, fl_ in grid_drawn],
                 "page_mm": [W, H], "a_mm": [AX_W, A_H], "b_panel_mm": [B_MW, B_MH],
                 "cell_mm": [CELL_W - 2 * PADC, CELL_H - 2 * PADC]}
    return W, H, printed, readback, overlaps, b_summary


def check_drawn(readback):
    return S475.check_drawn(readback)


def signflip_p_exact(diffs: list) -> float:
    """S463.signflip_p's exact two-sided sign-flip test (Rule 3), the same enumeration of all 2^m sign patterns of the
    m nonzero differences, scaled to whole numbers, carried as a probability array (numpy, float64) instead of a dict
    of counts: concept recall's denominators make the dict too large at n = 86 (D286). P = the share of the patterns
    whose sum is at least as far from 0 as the one observed."""
    import numpy as np
    nz = [Fraction(x) for x in diffs if x != 0]
    if not nz:
        return 1.0
    L = math.lcm(*[x.denominator for x in nz])
    v = [abs(int(x * L)) for x in nz]
    obs = abs(sum(int(x * L) for x in nz))
    S = sum(v)
    dist = np.zeros(2 * S + 1)
    dist[S] = 1.0
    for x in v:
        new = np.zeros_like(dist)
        new[x:] += dist[:-x]
        new[:-x] += dist[x:]
        dist = 0.5 * new
    s = np.arange(-S, S + 1)
    return float(min(1.0, dist[np.abs(s) >= obs].sum()))


def holm(ps: dict) -> dict:
    """Holm's step-down adjustment (S472.holm, Rule 12): the i-th smallest P (from 0) times (m - i), capped at 1, kept
    from falling below the one before it."""
    out, run, order = {}, 0.0, sorted(ps, key=lambda c: (ps[c], c))
    for i, c in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[c]))
        out[c] = run
    return out


def paired_test_rows(a_rows: list, caps: list, cols: list) -> list:
    """D286: per cap, each question's RLM (G5) concept recall minus Zhang RLM's (G6), each the 'question' row's value,
    the mean over the draws that system holds for it; the mean difference in points, S463.interval's two-sided 95%
    percentile interval (10,000 resamples of the questions sorted, seed 20261013), signflip_p_exact's two-sided P and
    Holm's P over the caps; then the same on each question's difference averaged over the caps ('paired_test_combined',
    Holm not applied). Values are read as Fractions (limit_denominator(30000): a share of at most 30 concepts over at
    most 3 draws, stored to float precision)."""
    val = collections.defaultdict(dict)
    draws = collections.defaultdict(set)
    for r in a_rows:
        if r["row"] == "question" and r["value_pct"] is not None:
            val[(r["system"], r["cap"])][r["question_id"]] = Fraction(r["value_pct"] / 100).limit_denominator(30000)
            draws[r["system"]].add(r["draws"])
    qs = sorted(set.intersection(*[set(val[("G5", c)]) & set(val[("G6", c)]) for c in caps]))
    if not qs:
        raise Refused("paired test: no question has both systems at every cap")
    def one(diffs):
        n = len(diffs)
        lo, hi = S463.interval([float(x) for x in diffs], [1.0] * n)
        return {"questions": n, "d_pp": 100 * float(sum(diffs, Fraction(0)) / n), "d_ci95_lo_pp": 100 * lo,
                "d_ci95_hi_pp": 100 * hi, "p_signflip_two_sided": signflip_p_exact(diffs),
                "rlm_higher": sum(x > 0 for x in diffs), "zhang_higher": sum(x < 0 for x in diffs),
                "tied": sum(x == 0 for x in diffs)}
    per = {c: one([val[("G5", c)][q] - val[("G6", c)][q] for q in qs]) for c in caps}
    for c, p in holm({c: per[c]["p_signflip_two_sided"] for c in caps}).items():
        per[c]["p_holm"] = p
    comb = one([sum((val[("G5", c)][q] - val[("G6", c)][q] for c in caps), Fraction(0)) / len(caps) for q in qs])
    dn = "; ".join(f"{s} draws {sorted(d)}" for s, d in sorted(draws.items()))
    out = []
    for kind, c, x in [*(("paired_test", c, per[c]) for c in caps), ("paired_test_combined", None, comb)]:
        r = {k: None for k in cols}
        r.update(row=kind, system="G5 minus G6", system_name=f"RLM minus Zhang RLM, per question ({dn})", cap=c,
                 **{k: x.get(k) for k in ("questions", *TEST_COLS)})
        out.append(r)
    return out


def legend_and_caption(fn, caps, t1caps, k, stamp, detail, d181: bool = False, b_d181: bool = False):
    """d181 (D186 (4)): a's concept recall is D181's (key v2.5; words a concept shares with its question not
    counted); b_d181 (D188): b's too; with d181 alone b is the loose matcher's (key v2.4, every
    concept word counted), and the legend says so in b."""
    b_loose = d181 and not b_d181
    A, B, C, D = (f"**{S475.LETTER_CASE(x)}**" for x in "abcd")
    caps_txt = ", ".join(str(c) for c in caps[:-1]) + f" and {caps[-1]}"
    t1_txt = ", ".join(str(c) for c in t1caps[:-1]) + f" and {t1caps[-1]}"
    dn = {r["system"]: r["answers"] for r in fn["d"] if r["cap"] == caps[0]}
    if any(r["answers"] != dn[r["system"]] for r in fn["d"]):     # d's legend gives one n per system for every cap
        raise Refused(f"d: the answers per cap differ within a system: {[(r['system'], r['cap'], r['answers']) for r in fn['d']]}")
    ref_style = ("dashed " if GEMINI_REF_DASHES else "") + COLOUR_WORD[GEMINI_REF_COLOUR]
    # D156: say "fewer" and "Empty" only where the drawn grid has a cell short of its covered questions or not complete
    c_short = any(r["complete"] and r["n_paired"] < COVERED_WANT[r["core_papers"]] for r in fn["c"])
    c_empty = any(not r["complete"] for r in fn["c"])
    range_on = any(r["range_pp"] is not None for r in fn["a"] if r["row"] == "draw_range")
    n_range = next(r["questions"] for r in fn["a"] if r["row"] == "draw_range")
    # D283: a and b are main Figure 4, c alone is Supplementary Figure 8; each has its own title, legend and caption
    title = "Recursive language models across turn caps and local generators"
    # 8 Nov (Valerio, "the figure legends are too long"): the panels, the signal, the marks and every n kept; the
    #   45-question subset behind the lower bars, the repeated "mean of three draws" and the repeated per-system n
    #   dropped (Source Data Fig. 4 sheet a's draw_range rows and Methods keep them)
    g5_one = all((r['draws'] or 1) == 1 for r in fn['a'] if r['row'] == 'question' and r['system'] == 'G5')
    # 8 Nov (Valerio, 20:40Z and 20:45Z, editor row 45): an "n = X <unit>" only where a panel draws a derived statistic
    #   (a's boxes and the lower bars' range, b's medians), once, inside that description; no other n tag (the upper
    #   bars' "n = 258 answers per system and cap" goes; they are shares of all three draws' answers); every panel
    #   described in full, never "as in a"
    n_q = sorted({r["questions"] for r in fn["a"] if r["row"] == "cap"})
    if len(n_q) != 1:                               # a's legend gives one n of questions for every system and cap
        raise Refused(f"a: the questions per system and cap differ: {n_q}")
    dots = ("each question's value (RLM, one draw) or mean over three draws (Zhang RLM)" if g5_one
            else "each question's mean over three draws")
    legend = (
        f"{A}, Concept recall (%) by turn cap for RLM (blue, left of each cap) and Zhang RLM (vermilion, right), both "
        f"with {GEN_DISPLAY}: the share of a question's expected concepts found in the answer"
        + (", not counting words the question also holds" if b_loose else "")   # the method is in Methods; said
        #   here only when b is scored otherwise and its legend sets the two readings side by side
        + f" (a failed answer scores 0). Dots: {dots}; boxes: quartiles and median; whiskers: full range; thin line: joins the "
        f"medians; n = {n_q[0]} questions per system and cap. " + (
        f"{'Upper bars' if range_on else 'Bars'}: share of the answers of all draws (%) reaching the cap (plain) "
        f"or cut off by it (hatched). " + (
            f"Lower bars: the highest minus the lowest of the three draws' mean concept recall (percentage points), "
            f"each draw's mean taken over n = {n_range} questions. "
            if range_on else "")) +
        f"{B}, Concept recall (%) by turn cap for RLM with four local models (one panel each, one draw) at "
        f"{len(t1caps)} turn caps: the share of a question's expected concepts found in the answer"
        + (", scored on key v2.4, with every concept word counted" if b_loose else "") +
        f" (a failed answer scores 0). Grey lines: each of the n = {k} question{'s' if k != 1 else ''} answered by "
        f"every model at every cap; black line: median over these questions; {ref_style} line: median over the same "
        f"questions of RLM with {GEN_DISPLAY}, each question's "
        f"{'value in its one draw' if g5_one else 'mean over three draws'}"
        f"{', on the same reading' if b_loose else ''}. "
        "RLM: Mentor::i's own; Zhang RLM: the authors' package (rlms 0.1.3).")
    title_c = "Generation strategies against single pass across corpus sizes"
    # 8 Nov (Valerio, editor row 45, extended to the Supplementary legends): the frame marks a derived statistic (the
    #   interval), so the grid states its n once, as "n = X questions", beside the frame; rows, columns, colour scale
    #   and frame described in full
    lim_c = fn["c_scale"]
    legend_c = (
        f"One cell per strategy (rows: multi-hop, verified pass, and RLM stopped at 5, 10 and 20 turns, RLM-5, "
        f"RLM-10 and RLM-20) and per index (columns). Each index holds 5, 10, 20 or 50 core papers (column groups) "
        f"and 0, 1 or 3 distractor papers for every core paper (columns). Answers are from {GEN_DISPLAY}, one draw, to the "
        f"answerable questions whose source papers are all in that index, with the strategy's and single pass's "
        f"answers both judged. Each cell gives the strategy's pass rate minus single pass's on the same questions, in "
        f"percentage points, printed in the cell and coloured from −{lim_c} (dark blue) through 0 (grey) to "
        f"+{lim_c} (yellow). Upper block: pass is judge correctness 4 or more; lower block (relaxed): 3 or more. "
        f"Frame inside a cell: the two-sided 95% percentile interval of the difference, from 10,000 resamples of the "
        f"questions, excludes 0; n = {COVERED_WANT[5]} questions per index at 5 core papers, {COVERED_WANT[10]} at "
        f"10, {COVERED_WANT[20]} at 20 and {COVERED_WANT[50]} at 50"
        + (", fewer where a judge call failed or an answer was held out" if c_short else "") + "."
        + (" Empty cell: judging incomplete." if c_empty else ""))
    stamp_ab, stamp_c = stamp
    lines = [f"# {MAIN_LABEL} (D283; D123), title and legend (draft)", "",
             f"Data stamp: {stamp_ab}.", "", detail, "",
             f"**{MAIN_LABEL} | {title}.** {legend}", ""]
    lines_c = [f"# {SI_LABEL} (D283; D150), title and legend (draft)", "",
               f"Data stamp: {stamp_c}.", "", detail, "",
               f"**{SI_LABEL} | {title_c}.** {legend_c}", ""]
    cap = [f"# {MAIN_SD}, caption", "",
           (f"**{MAIN_SD} | Numerical values plotted in {MAIN_LABEL}.** Provisional. Data stamp: {stamp_ab}. One "
            f"sheet per panel. Sheet {MAIN_SHEET}a: one 'cap' row per system and turn cap (questions, answers, mean concept "
            f"recall (%) and its 95% interval (%), not drawn, failed answers, and the box drawn: median, first and "
            f"third quartiles, minimum and maximum (%)), then one 'question' row per system, cap and question with "
            f"its value (%) and its draws, then one 'strip' row per system and cap for the bars under a (answers, "
            f"those whose turns used reached the cap and those the cap stopped, count and %), then one 'draw_range' row "
            f"per system and cap for the lower strip (draws read, questions, smallest and largest mean over the draws "
            f"(%), range in points; blank until a second draw of RLM is read), then one 'paired_test' row per turn cap and one "
            f"'paired_test_combined' row (each question's difference averaged over the caps): RLM minus Zhang RLM per "
            f"question, on the questions both hold at every cap, each the mean over the draws it holds (questions, mean "
            f"difference in points and its two-sided 95% percentile interval over 10,000 question resamples, the exact "
            f"two-sided sign-flip P, Holm's P over the caps on the per-cap rows, and the questions where RLM, Zhang RLM "
            f"or neither is higher); an exploratory test, specified after the data were seen. Sheet {MAIN_SHEET}b: one 'cap' row per local model and turn cap (questions "
            f"answered by all four models at all six caps, answers, median concept recall (%), drawn, mean and its "
            f"95% interval (%) when two or more questions are complete, not drawn, failed answers, answers whose "
            f"turns used reached the cap, answers stopped by the cap), one 'gemini_ref' row per cap (the same "
            f"questions with gemini-3-flash-preview, RLM: median (%), drawn, and mean of each question's mean over draws 1 to 3; "
            f"failed answers, answers whose turns used reached the cap and answers stopped by the cap, of draw 1), then "
            f"one 'answer' row per stored answer (whether its question is complete, the concept recall drawn (%), "
            f"the loose matcher's and the exact test's concept recall on the same concepts (%), failed, stop reason, "
            f"turns used, answer key)."),
           "",
           f"Proposed Data Availability sentence: \"The source data for {MAIN_LABEL} is in Supplementary Data {MAIN_N + 1}.\"",   # D303 (D302)
           ""]
    cap_c = [f"# {SI_LABEL} data, caption", "",
             (f"**{SI_LABEL} data | Numerical values plotted in {SI_LABEL}.** Provisional. Data stamp: {stamp_c}. One "
              f"sheet. Sheet {C_SHEET}: one "
              f"'cell' row per judge score (4, the pass rate, then 3, the relaxed threshold), strategy and index (core papers, distractor papers per core paper, "
              f"whether both units are judged in full, questions paired, the strategy's and single pass's pass rates "
              f"(%), the difference in percentage points with its two-sided 95% percentile interval and whether that "
              f"excludes 0, the two-sided sign-flip P, not adjusted for multiple comparisons)."),
             ""]
    return {"ab": ("\n".join(lines), "\n".join(cap), legend, title),
            "c": ("\n".join(lines_c), "\n".join(cap_c), legend_c, title_c)}


def plate(out: Path = OUT, t1dir: Path = T1_L2, g4dir: Path = G4_FIG3C, mut=None, quiet=False, main_out: Path | None = None,
          l2dir: Path = L2, l2_drawn_dir: Path | None = None,
          l2_d181_dirs: tuple | None = (L2_D181, L2_D135_D181), t1_d181_dir: Path | None = T1_L2_D181,
          g4_d185_dir: Path | None = G4_FIG3C_D185, g5_d284_dir: Path | None = L2_D135_D181_D284) -> dict:
    """l2_drawn_dir (D160 Q23): L2 after the D135 reruns, the reading a draws; None: a draws l2dir, the gated
    reading (before the reruns), as before D160. l2_d181_dirs (D186 (4), the default): (gated, drawn) D181 folders;
    a draws the drawn one after reproduce_l2_d181 (needs l2_drawn_dir); None: a draws the loose reading, as before
    D186 (the fixtures of selftest and mutants). t1_d181_dir (D188, the default T1_L2_d181): b draws T1's D181
    reading after reproduce_t1_d181 holds it to t1dir, and b's gemini-3-flash-preview reference is then a's D181 G5
    rows (needs l2_d181_dirs); None: b and its reference on the loose matcher, as before D188. g4_d185_dir (D188, the
    default G4_fig3c_d185): c draws S514's draw-1 reading (key v2.5 judge rows where S6 has judged) after
    reproduce_g4_d185 holds it to g4dir; None: c draws g4dir, as before D188 (the fixtures)."""
    flock = S475.FLOCK
    if flock.get("status") != "agreed":
        raise Refused(f"{rel(FIGURE_LOCK)} has status {flock.get('status')!r}, not 'agreed' (D87)")
    for colour in [s["colour"] for s in S475.SYSTEMS.values()] + [GEMINI_REF_COLOUR]:
        if str(colour).upper() not in S475._CAT or colour not in COLOUR_WORD:
            raise Refused(f"{colour} is not in [colour] categorical")
    rgb = [int(Q_GREY[i:i + 2], 16) for i in (1, 3, 5)]
    if max(rgb) - min(rgb) > int(flock["colour"]["grey_tol"]) or LW_Q_MIN < float(flock["lines"]["line_min_pt"]):
        raise Refused(f"b's question grey {Q_GREY} is not a grey within [colour] grey_tol, or its width is under "
                      f"[lines] line_min_pt")
    # L2 (a, d): S475's reproduction
    l2_files = {n: l2dir / n for n in ("concept_recall.jsonl", "cap_tables.json", "header.json")}
    header = json.loads(l2_files["header.json"].read_text())
    tables = json.loads(l2_files["cap_tables.json"].read_text())
    rows = [json.loads(x) for x in l2_files["concept_recall.jsonl"].read_text().splitlines() if x.strip()]
    if header.get("script") != "scripts/S474_l2_concept_recall.py" or header.get("provisional") is not True:
        raise Refused("findings/recompute/L2/header.json is not S474's provisional L2 header")
    caps = tuple(header["caps"])
    want_n = {s: header["counts"][s]["rows"] for s in S475.SYSTEMS}
    if dict(collections.Counter(r["system"] for r in rows)) != want_n:
        raise Refused("L2 rows differ from header.json counts")
    ids, design_caps, _, _ = S459.design_constants()
    if tuple(design_caps) != caps or set(ids) != {r["question_id"] for r in rows}:
        raise Refused("S474's caps or questions are not run_rlm_ref.py's DEPTH_SWEEP86 and caps")
    reproduced, qorder = S475.reproduce(rows, tables, caps)     # the gate: the reading before the D135 reruns
    gate_rows = rows
    l2_drawn = None
    if l2_drawn_dir is not None:                                 # D160 Q23: a draws the reading after them
        rows, tables, l2_drawn = reproduce_l2_drawn(l2_drawn_dir, gate_rows, caps)
        if dict(collections.Counter(r["system"] for r in rows)) != want_n:
            raise Refused("L2_d135 rows differ from L2's counts")
    loose_rows, loose_tables = rows, tables                      # b's gemini reference keeps the loose reading
    d181 = None
    d284 = None
    if l2_d181_dirs is not None:                                 # D186 (4): a draws D181's reading
        if l2_drawn is None:
            raise Refused("D186 (4): the D181 reading a draws is G6 after the D135 reruns; L2_d135 is needed")
        d181 = reproduce_l2_d181(gate_rows, rows, caps, *l2_d181_dirs, loose_held=l2_drawn["held_check"])
        if mut != "a_loose_with_d181":           # a mutant: the D181 reading read and checked but not drawn
            rows, tables = d181["rows"], d181["tables"]
            if g5_d284_dir is not None and Path(g5_d284_dir).exists():     # D284: RLM's draws 2 and 3 on all 86
                rows, tables, d284 = add_g5_d284(rows, caps, Path(g5_d284_dir))
    a_field = S475.D181_FIELD if d181 and mut != "a_loose_with_d181" else S475.LOOSE
    g5_three = any(r["system"] == "G5" and r["draw"] != 1 for r in rows)
    s463 = S463.reproduce()
    t1rows, t1tab, t1head = reproduce_t1(t1dir)
    g4rows, g4tab, g4head, g4rows6, grid = reproduce_g4(g4dir)
    if tuple(t1tab["models"]) != T1_FOUR:
        raise Refused(f"T1_L2 models {t1tab['models']} are not D121's four")
    # D188: b on T1's D181 reading and c on S514's key v2.5 reading, each held to the v2.4 reading just reproduced
    t1d = None
    t1rows_b, t1tab_b = t1rows, t1tab
    if t1_d181_dir is not None:
        if d181 is None:
            raise Refused("D188: b on D181's reading needs a on it (b's gemini-3-flash-preview line is a's G5 rows)")
        t1d_rows, t1d_tab, t1d = reproduce_t1_d181(t1_d181_dir, t1dir, t1rows, t1tab)
        if mut != "b_loose_with_d181":           # a mutant: T1_L2_d181 read and checked but b drawn on the loose rows
            t1rows_b, t1tab_b = t1d_rows, t1d_tab
    b_d181 = t1d is not None and mut != "b_loose_with_d181"
    g4d = None
    rows6_c, grid_c = g4rows6, grid
    if g4_d185_dir is not None:
        rows6_d, grid_d, g4d = reproduce_g4_d185(g4_d185_dir, g4rows6, g4head["grid"]["inputs"]["indexes"])
        if mut != "c_v24_with_d185":             # a mutant: G4_fig3c_d185 read and checked but c drawn on G4_fig3c
            rows6_c, grid_c = rows6_d, grid_d
    t1caps = tuple(t1tab["caps"])
    k = t1tab["k"]
    f475 = S475.compute(rows, tables, caps, qorder, a_field)
    a_rows = a_with_boxes(f475["a"], caps)
    if set(t1caps) - set(caps):
        raise Refused(f"T1's caps {sorted(set(t1caps) - set(caps))} are not caps of a's G5 run")
    a_loose = a_rows if d181 is None else a_with_boxes(S475.compute(loose_rows, loose_tables, caps, qorder)["a"], caps)
    if b_d181:                                       # D188: b's reference on b's measure, a's D181 G5 rows
        a_d181 = a_rows if a_field == S475.D181_FIELD else a_with_boxes(
            S475.compute(d181["rows"], d181["tables"], caps, qorder, S475.D181_FIELD)["a"], caps)
        gref = gemini_ref(rows if d284 is not None and a_field == S475.D181_FIELD else d181["rows"], a_d181, t1caps,
                          t1tab["complete_questions"], field=S475.D181_FIELD)
        if mut == "gref_from_loose":             # a mutant: b on D181 with its reference on the loose rows
            gref = gemini_ref(loose_rows, a_loose, t1caps, t1tab["complete_questions"])
    else:
        gref = gemini_ref(loose_rows, a_loose, t1caps, t1tab["complete_questions"])
    if mut == "gref_from_d181" and d181 and not b_d181:   # a mutant: b's reference read from a's D181 rows
        gref = gemini_ref([{**r, S475.LOOSE: r[S475.D181_FIELD]} for r in rows], a_rows, t1caps,
                          t1tab["complete_questions"])
    a_rows = a_rows + [{**{k: None for k in A_COLS}, "row": "strip", "system": r["system"],
                        "system_name": r["system_name"], "cap": r["cap"], "answers": r["answers"],
                        **{k: r[k] for k in D_COLS}} for r in f475["b"]]
    if mut == "strip_rows_swapped":                  # a mutant: the strip's two shares written into each other
        for r in a_rows:
            if r["row"] == "strip":
                r["cap_reached_pct"], r["stopped_by_cap_pct"] = r["stopped_by_cap_pct"], r["cap_reached_pct"]
    noise = json.loads((L2_D135_D181_G7 / "noise_tables.json").read_text()) if d181 is not None else None
    a_rows = a_rows + draw_range_rows(noise, rows, caps, a_field, set(json.loads(D98_SUBSET.read_text())["ids"]) & set(ids),
                                      A_COLS)
    a_rows = a_rows + paired_test_rows(a_rows, caps, A_COLS)
    fn = {"a": a_rows, "d": f475["b"], "b": b_sheet(t1rows_b, t1tab_b, gref, d181=b_d181), "c": grid_sheet(grid_c, mut)}
    top = max([abs(r["d_pp"]) for r in fn["c"] if r["complete"]] + [5.0])
    fn["c_scale"] = 5 * math.ceil(top / 5 - 1e-12)     # one colour scale for both blocks, +-the smallest multiple of 5
    # n and m
    plan = S459.planned_total(ids, caps)
    from experiments.scorers import records
    sub = json.loads(D98_SUBSET.read_text())["ids"]
    common_ans = g4head["inputs"]["common_answerable"]
    sub_ans = sum(1 for q in sub if records.group_of(q) == "answerable")
    asg_q = len(t1head["question_order"])
    # D160 (15) S1 (Valerio, 27 October): c's planned answers are the draw-1 answers its cells can hold, each of the six
    # strategies on each index's covered questions (D126), not G4's whole plan (draws 2 and 3 and the D98 subset,
    # 6 x 12 x (common_ans + 2 x sub_ans), which panel c does not use)
    cov_n = g4head["inputs"]["covered"]
    g4c_indexes = g4head["inputs"]["indexes"]
    g4c_planned = c_planned()                        # from G4's design; G4_fig3c's own indexes and covered counts agree
    if {index_parts(i) for i in g4c_indexes} != {(c, r) for c in COVERED_WANT for r in G4_RATIOS} or \
            len(g4c_indexes) != len(COVERED_WANT) * len(G4_RATIOS) or \
            len(G4_ALL) * sum(int(cov_n[str(index_parts(i)[0])]) for i in g4c_indexes) != g4c_planned:
        raise Refused(f"G4_fig3c's indexes and covered counts ({cov_n}) do not give c's planned {g4c_planned}")
    m_parts = {"G5": (G6_DRAWS * len(ids) * len(caps)) if g5_three else plan["G5"], "G6": want_n["G6"], "T1": len(T1_FOUR) * asg_q * len(t1caps), "G4c": g4c_planned}
    c_answers = c_drawn(rows6_c, grid_c)
    if mut == "c_over_plan":                         # a mutant: an answer outside the covered set counted in c
        c_answers.add(("rlm_10", g4c_indexes[0], "not_a_covered_question"))
    n_parts = {"a": len(rows), "b": len(T1_FOUR) * len(t1caps) * k, "c": len(c_answers)}
    # D161 (9) N9 (Valerio, 27 October, "Yes to all three"): no panel draws more answers than it planned; a by system,
    # G5 against its D98 plan, G6 against its G6_DRAWS full draws of a's questions and caps (m_parts' G6 is the
    # answers held, so no bound on them)
    drawn_by = {f"a {s}": v for s, v in collections.Counter(r["system"] for r in rows).items()}
    drawn_by.update({"b": n_parts["b"], "c": n_parts["c"]})
    planned_by = {"a G5": m_parts["G5"], "a G6": G6_DRAWS * len(ids) * len(caps), "b": m_parts["T1"],
                  "c": m_parts["G4c"]}
    if mut is not None and mut.startswith("over_plan "):      # a mutant: one answer more than the panel planned
        drawn_by[mut[len("over_plan "):]] = planned_by[mut[len("over_plan "):]] + 1
    over = over_plan(drawn_by, planned_by)
    if over:
        raise Refused("a panel draws more answers than it planned (D161 (9)): " + "; ".join(over))
    n, m = sum(n_parts.values()), sum(m_parts.values())
    if n > m:
        raise Refused(f"n {n} > m {m}")
    cells_done = sum(1 for e in grid_c["cells"] if e["complete"] and e["score"] == PASS4)
    if d181 is None:
        concept_txt = "concept recall on D12's loose matcher, no judge, for a and b"
    elif b_d181:
        concept_txt = ("concept recall, no judge: a and b on D181's reading (the loose matcher with the question "
                       "rule, key v2.5)")
    else:
        concept_txt = ("concept recall, no judge: a on D181's reading (the loose matcher with the question rule, key "
                       "v2.5), b on D12's loose matcher (key v2.4)")
    c_key_txt = ("" if g4d is None else
                 f"; c's judge rows on key v2.5 where S6 has judged an answer of the 132 questions v2.5 changed, key "
                 f"v2.4 for the {g4d['awaiting_s6_covered']} covered draw-1 answers awaiting it")
    range_txt = ("" if any(r["range_pp"] is not None for r in a_rows if r["row"] == "draw_range") else
                 "; the lower strip under a an empty axis until RLM's draws 2 and 3 are scored")
    # D283: two plates, each with its own count. Figure 4: a and b; Supplementary Figure 8: the grid (c)
    n_ab, m_ab = n_parts["a"] + n_parts["b"], m_parts["G5"] + m_parts["G6"] + m_parts["T1"]
    n_c, m_c = n_parts["c"], m_parts["G4c"]
    stamp_ab = (f"PROVISIONAL: {n_ab} of {m_ab} answers; a and the strip under it, RLM ({'three draws' if g5_three else 'draw 1'}, "
                f"{sum(r['system'] == 'G5' for r in rows)} of "
                f"{m_parts['G5']}) and Zhang RLM (three draws, {want_n['G6']} of {m_parts['G6']}) at {len(caps)} turn "
                f"caps{range_txt}; b, T1's four local models, {n_parts['b']} of {m_parts['T1']} (the {k} "
                f"question{'s' if k != 1 else ''} stored by every model at every cap); {concept_txt}")
    stamp_c = (f"PROVISIONAL: {n_c} of {m_c} answers; G4 draw 1 of the six strategies judged by S3 ({cells_done} of "
               f"{len(GRID_STRATS) * 12} strategy and index cells with both units judged){c_key_txt}")
    stamp = f"{stamp_ab} | {stamp_c}"
    tag, tag_ab = f" (provisional, {n_c} of {m_c})", f" (provisional, {n_ab} of {m_ab})"
    t1f = sum(r["failed"] for r in t1rows)
    st6 = {s_: collections.Counter(r["cells"][s_]["status"] for r in rows6_c if r["covered"]) for s_ in G4_ALL}
    cov_n = g4head["inputs"]["covered"]
    u6 = g4d["units"] if g4d is not None and mut != "c_v24_with_d185" else g4head["grid"]["inputs"]["units"]
    units_done = sorted(k_ for k_, v in u6.items() if v["complete"])
    empty = [f"{e['strategy']} {e['index']}" for e in grid_c["cells"] if e["score"] == PASS4 and not e["complete"]]
    failed6 = ", ".join(f"{s_} {st6[s_].get('failed', 0)}" for s_ in G4_ALL)
    held6 = ", ".join(f"{s_} {st6[s_].get('held_g4r38', 0)}" for s_ in G4_ALL)
    g5_files = sorted(set((header["inputs"]["G5"].get("files") or {}).values()))
    if l2_drawn is None:
        g6_reading = "G6 before the D92 reruns"
    else:
        hc = l2_drawn["held_check"]
        g6_reading = (f"G6 after the D135 reruns (D160): {hc['g6_rows_changed']} answers changed by the reruns and "
                      f"rebuilds, failed {hc['g6_failed_drawn']} of {want_n['G6']} (before them {hc['g6_failed_gated']}); the gates "
                      f"check the reading before them")
    held_anchor = (g4head["grid"].get("gate") or {}).get("g4r38_held_for_anchor") or []
    anchor_txt = (f"RLM-10's cells reproduce D125's reading of the same copy; with the {len(held_anchor)} judged G4R38 "
                  f"reruns held out they reproduce D149's Source Data (anchor_d149_rlm10.json), and c draws them "
                  f"judged (D156)" if held_anchor else
                  "RLM-10's cells reproduce D125's reading of the same copy and D149's Source Data "
                  "(anchor_d149_rlm10.json)")
    d181_txt = ("" if d181 is None else
                f" a draws D181's concept recall ({d181['record']['drawn']}, gated by {d181['record']['gated']}; "
                f"S475's method with the D181 anchors {', '.join(f'{k_} {v_}%' for k_, v_ in d181['record']['anchors'].items())}, "
                f"after the loose anchors on L2); " + (
                    f"b draws {t1d['dir']} (D181's reading of T1's answers, key v2.5, held to {rel(T1_L2)}: the same "
                    f"answers, the loose base equal to the loose value on the {t1d['questions_concepts_unchanged']} "
                    f"questions whose concepts v2.5 left unchanged) and its gemini-3-flash-preview line a's D181 G5 "
                    f"rows (D188)." if b_d181 else
                    "b and its gemini-3-flash-preview line stay on the loose matcher (key v2.4)."))
    c_d185_txt = ("" if g4d is None or mut == "c_v24_with_d185" else
                  f" c draws {g4d['dir']} (S514 g4c, D188: per answer the key v2.5 judge row where S6 has judged one "
                  f"of the 132 questions v2.5 changed, else the v2.4 row; {g4d['rows_moved_by_v25']} question rows "
                  f"differ from {rel(G4_FIG3C)}'s, every other row equal to it; covered draw-1 answers by key "
                  f"{g4d['covered_answers_by_key']}).")
    detail = (f"**Data detail (not part of the legend).** a's boxes and the strip under it from S475's numbers (S474's L2 on "
              f"G5 results {', '.join(x[:8] for x in g5_files)}; {g6_reading}).{d181_txt} b: {len(t1rows)} T1 answers stored (walk to "
              f"{t1head['inputs']['front_g']} of {t1head['inputs']['cells_in_order']} cells, clone "
              f"{t1head['inputs']['clone_head'][:7]}, taken {t1head['inputs']['taken_utc']}), {t1f} failed (scored 0); "
              f"complete questions {k} ({', '.join(t1tab['complete_questions']) or 'none'}); "
              + ("" if b_d181 else "the loose matcher is provisional until P2's labels choose one (D17); ") +
              f"April's rescored answers (D97) are not drawn until a "
              f"cut-off is set (D79). c (D150): units complete {len(units_done)} of 72; empty cells "
              f"{len(empty)} ({'; '.join(empty) or 'none'}); among the covered questions, failed answers (scored 0) "
              f"{failed6}; G4R38 keys held out (not judged again) {held6}. "
              f"Question set of c (D126): of the common set's answerable group (Q105), the questions whose source "
              f"papers are all in the index, {', '.join(str(cov_n[str(c)]) for c in (5, 10, 20))} and {cov_n['50']} "
              f"at 5, 10, 20 and 50 core papers. {anchor_txt}; that reading's common-86 and per-size columns stay in "
              f"findings/recompute/G4_fig3c/point_tables.json.{c_d185_txt}")
    texts_ = legend_and_caption(fn, caps, t1caps, k, (stamp_ab, stamp_c), detail, d181 is not None, b_d181)
    status_words = re.compile(r"provisional|not yet|to come|pending|so far|not drawn|to be run|\bS\d{3}\b|\bD\d+\b|"
                              r"\bQ\d+\b|scripts/|findings/", re.I)
    words_by = {}
    for part_, label_ in (("ab", MAIN_LABEL), ("c", SI_LABEL)):
        _, _, legend_, title_ = texts_[part_]
        words_by[part_] = len(f"**{label_} | {title_}.** {legend_}".split())
        if words_by[part_] >= int(flock["legend"]["words_under"]):
            raise Refused(f"{label_}'s legend has {words_by[part_]} words, not under {flock['legend']['words_under']}")
        if status_words.search(legend_) or status_words.search(title_):
            raise Refused(f"{label_}'s legend carries a status word, script, path or decision code: "
                          f"{status_words.search(legend_ + title_).group(0)!r}")
    words = words_by["ab"]
    main_out = (out.parent / MAIN_OUT.name) if main_out is None else main_out
    plates_ = {"ab": {"out": main_out, "label": MAIN_LABEL, "tag": tag_ab, "side": MAIN_SIDE,
                      "sd_stem": MAIN_SD, "old": [f"{MAIN_LABEL}*", f"{MAIN_SD}*"],
                      "sheets": [(f"{MAIN_SHEET}a", A_COLS, "a"), (f"{MAIN_SHEET}b", B_COLS, "b")], "stamp": stamp_ab},
               "c": {"out": out, "label": SI_LABEL, "tag": tag, "side": SIDE, "sd_stem": f"{SI_LABEL} data",
                     "old": [f"{SI_LABEL}*"], "sheets": [(C_SHEET, GRID_COLS, "c")], "stamp": stamp_c}}
    drawn_ = {}
    readback_all = []
    for part_, P_ in plates_.items():
        P_["out"].mkdir(parents=True, exist_ok=True)
        old = [q for g_ in P_["old"] for q in P_["out"].glob(g_)]
        paths = {x: P_["out"] / f"{P_['label']}{P_['tag']}.{x}" for x in ("pdf", "svg", "png")}
        tmpd = Path(tempfile.mkdtemp(prefix="S476_plate_"))
        tpaths = {x: tmpd / q.name for x, q in paths.items()}
        try:
            W, H, printed, readback, overlaps, b_summary = draw_figure(fn, caps, t1caps, tpaths, mut=mut, part=part_)
            bad, n_checked = check_drawn(readback)
            if bad:
                raise Refused("check_drawn FAILED, nothing kept: " + "; ".join(bad[:5]))
            fig_repro.check_pdf_deterministic(tpaths["pdf"])     # D155: no date in the PDF or the SVG
            fig_repro.check_svg_deterministic(tpaths["svg"])
            for q in old:
                q.unlink()
            for x in paths:
                shutil.move(str(tpaths[x]), paths[x])
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
        readback_all += readback
        sheets = [(nm, cols, [[r[c] for c in cols] for r in fn[key_]]) for nm, cols, key_ in P_["sheets"]]
        sd = P_["out"] / f"{P_['sd_stem']}{P_['tag']}.xlsx"
        write_source_data(sheets, sd)
        numbers = P_["out"] / f"{P_['side']}_numbers.json"
        numbers.write_text(json.dumps({"stamp": P_["stamp"], "what": "every number the plate draws, sheet by sheet as "
                                       f"the data workbook {sd.name} holds them (S448 R8 compares the workbook with "
                                       "this file)",
                                       "sheets": {nm: {"columns": cols, "rows": rws} for nm, cols, rws in sheets},
                                       "printed": printed,
                                       "printed_what": "every number printed on the plate: the SVG group id of its text, "
                                                       "and the data workbook sheet, row and format it is written from, or "
                                                       "the fixed text"}, indent=1, default=str) + "\n")
        legend_md, cap_md, _, _ = texts_[part_]
        (P_["out"] / "legend_draft.md").write_text(legend_md)
        capf = P_["out"] / f"{P_['sd_stem']} caption{P_['tag']}.md"
        capf.write_text(cap_md)
        drawn_[part_] = {"W": W, "H": H, "n_checked": n_checked, "overlaps": overlaps, "b_summary": b_summary,
                         "paths": paths, "files": [*paths.values(), sd, capf, numbers, P_["out"] / "legend_draft.md"]}
    readback = readback_all
    n_checked = drawn_["ab"]["n_checked"] + drawn_["c"]["n_checked"]
    c_cells = sum(1 for w, _, _ in readback if w.startswith("c ") and w.endswith(" cell"))
    a_boxes = sum(1 for w, _, _ in readback if w.startswith("a ") and w.endswith(" box"))
    b_refs = sum(1 for w, _, _ in readback if w.startswith("b ") and w.endswith(" reference"))
    b_medians = sum(1 for w, _, _ in readback if w.startswith("b ") and w.endswith(" median"))
    b_lines = sum(1 for w, _, _ in readback if w.startswith("b ")) - b_refs - b_medians
    b_summary = {**drawn_["ab"]["b_summary"], "grid": drawn_["c"]["b_summary"]["grid"],
                 "cell_mm": drawn_["c"]["b_summary"]["cell_mm"], "page_mm_c": drawn_["c"]["b_summary"]["page_mm"]}
    overlaps = {**drawn_["ab"]["overlaps"], **drawn_["c"]["overlaps"]}
    W, H = drawn_["ab"]["W"], drawn_["ab"]["H"]
    # D155: each input under its committed path (a rebuild into --out reads the same names under that folder), so
    # the provenance does not depend on where the derived folders were written
    canon = [(L2 / n, p) for n, p in l2_files.items()]
    if l2_drawn is not None:
        canon += [(L2_D135 / n, l2_drawn_dir / n) for n in L2_FILES]
    if d181 is not None:
        canon += [(c_ / n, Path(d_) / n) for c_, d_ in zip((L2_D181, L2_D135_D181), l2_d181_dirs) for n in L2_FILES]
    canon += [(T1_L2 / n, t1dir / n) for n in ("concept_recall.jsonl", "cap_tables.json", "header.json")]
    canon += [(G4_FIG3C / n, g4dir / n) for n in ("pairs.jsonl", "point_tables.json", "header.json",
                                                  "grid_pairs.jsonl", "grid_tables.json")]
    if t1d is not None:
        canon += [(T1_L2_D181 / n, Path(t1_d181_dir) / n) for n in T1_D181_FILES]
    if g4d is not None:
        canon += [(G4_FIG3C_D185 / n, Path(g4_d185_dir) / n) for n in G4_D185_FILES]
    canon += [(q, q) for q in (FIGURE_LOCK, ROOT / "experiments" / "rlm_ref" / "run_rlm_ref.py", S459.G4_README,
                               S459.G5_README, D98_SUBSET)]
    if d181 is not None:
        canon.append((L2_D135_D181_G7 / "noise_tables.json",) * 2)
    inputs = {rel(c): sha256_file(q) for c, q in canon}
    me = sha256_file(Path(__file__))
    prov = {"script": SCRIPT, "script_sha256": me, "command": f"uv run --frozen python {SCRIPT} plate",
            "python": platform.python_version(), "inputs_sha256": inputs,
            "model_calls": 0, "stamp": stamp, "page_mm": [W, H],
            "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK), "status": flock["status"]},
            "l2_readings": ({"gated": f"{rel(L2)} (G6 before the D135 reruns): S475.reproduce and its anchors",
                             "drawn": f"{rel(L2_D135)} (G6 after the D135 reruns, D160 Q23): held to {rel(L2)} but for "
                                      f"the answers the reruns acted on", "held_check": l2_drawn["held_check"]}
                            if l2_drawn is not None else
                            {"gated": f"{rel(L2)} (G6 before the D135 reruns)", "drawn": f"{rel(L2)}: G6 after the "
                             f"reruns not frozen yet ({rel(G6_D135)} missing), so a draws the reading before them"}),
            "concept_reading_a": ("D186 (4): D181's reading, a draws " + d181["record"]["drawn"] + "; the loose "
                                  "readings above are reproduced first and held to it" if d181 is not None else
                                  "D12's loose matcher (the drawn reading above)"),
            "l2_d181": None if d181 is None else d181["record"],
            "concept_reading_b": ("D188: D181's reading, b draws " + t1d["dir"] + " and its gemini-3-flash-preview "
                                  "line a's D181 G5 rows; T1_L2 (the loose reading) is reproduced first and held to "
                                  "it" if b_d181 else "D12's loose matcher (T1_L2, key v2.4) for b and its line"),
            "t1_d181": None if t1d is None else t1d,
            "g4_d185": None if g4d is None else {k_: v_ for k_, v_ in g4d.items() if k_ != "units"},
            "reproduced": {"L2 (S475.reproduce)": reproduced, "S463.reproduce": s463,
                           **({} if d181 is None else {"L2_d181 (S475.reproduce, ANCHORS_D181)": d181["reproduced"]}),
                           "T1_L2": f"cap_tables.json recomputed from {len(t1rows)} rows, equal (k {k})",
                           **({} if t1d is None else {"T1_L2_d181": f"held to T1_L2: {t1d['rows']} answers tied one "
                                                                    f"for one, cap_tables.json recomputed on "
                                                                    f"concept_recall, equal"}),
                           **({} if g4d is None else {"G4_fig3c_d185": f"held to G4_fig3c: {g4d['rows']} rows, "
                                                                       f"{g4d['rows_moved_by_v25']} of the 132 changed "
                                                                       f"questions' rows differ; grid_tables.json "
                                                                       f"recomputed from its rows and draw-1 units, "
                                                                       f"equal"}),
                           "G4_fig3c": f"point_tables.json recomputed from {len(g4rows)} rows, equal; grid_tables.json "
                                       f"from {len(g4rows6)} rows, equal; RLM-10's cells equal to point_tables.json"
                                       + ((f" and, with the {len(held_anchor)} judged G4R38 reruns held out "
                                           f"(D156), to D149's anchor; the judged reading drawn" if held_anchor
                                           else " and to D149's anchor") if g4head["grid"].get("anchor_sha256")
                                          else ""),
                           "T1_L2 written by this script": t1head["script_sha256"] == me,
                           "G4_fig3c written by this script": g4head["script_sha256"] == me},
            "answers_drawn": n_parts, "answers_planned": m_parts, "n": n, "m": m,
            "planned_how": {"G5": plan["how"]["G5"], "G6": "three full draws (D98 keeps Figure 2's experiments)",
                            "T1": "4 models x 15 questions x 6 caps, draw 1 (D119 Q5)",
                            "G4c": f"D160 S1: draw 1, {len(G4_ALL)} strategies x the covered questions of the "
                                   f"{len(g4c_indexes)} indexes (D126, {cov_n} by core papers, three distractor "
                                   f"ratios each); G4's whole plan, {len(G4_ALL)} x 12 x ({common_ans} common "
                                   f"answerable + 2 x {sub_ans} of the D98 subset's answerable) = "
                                   f"{len(G4_ALL) * 12 * (common_ans + 2 * sub_ans)}, holds draws 2 and 3, which c "
                                   f"does not use"},
            "drawn_check": f"check_drawn(): {n_checked} drawn values equal their data workbook",
            "dot_overlaps": {"total": sum(overlaps.values()), "by_strip": overlaps},
            "panels": {"a": "A-1 (Valerio, 26 October): per cap two boxes, Mentori's RLM left, the package right, "
                            "quartiles, median, full range, every question a dot, a thin line joining the medians, "
                            "caps evenly spaced, no mean (L2 all mode; the mean and its interval in the data workbook, D128)",
                       "b": "B-2 (Valerio, 26 October), with his 15:00 follow-up (question lines one grey, "
                            f"{Q_GREY}, caps evenly spaced): one small panel per local model, a line per complete question, "
                            "the median, and the median of the same questions with gemini-3-flash-preview (G5, each question's "
                            f"mean over draws 1 to 3) in {GEMINI_REF_COLOUR}" + (" dashed" if GEMINI_REF_DASHES else " solid") +
                            "; the key is line samples with their meanings",
                       "c": "D150 (Valerio, 26 October 19:00, layout O-b1): every strategy minus single pass per "
                            "index, judge score 4 (the pass rate) above score 3 (relaxed, D154), one cividis scale, the number in each cell, a frame "
                            "where the two-sided 95% interval excludes 0, empty where a unit is not complete; on the "
                            f"questions the index can answer (D126, {g4head['inputs']['covered']} by core papers)",
                       "strip": "D-3b (D149, Valerio 26 October 18:40): under a, per system and cap two bars side by side, "
                                "reached the cap (plain) and cut off by the cap (hatched); no panel d",
                       "range strip": "FF30 a (supp.md section 7): under the first strip, per system and cap the range "
                                      "of the mean over the draws on D98's questions; an axis alone until G7 is read"},
            "legend_words": words, "font": S475.FONT,
            "plates": {"Figure 4 (D283)": {"folder": main_out.name,   # the name only, so S494 --out rebuilds it byte-equal
                                           "panels": "a, b", "stamp": stamp_ab, "page_mm": [drawn_["ab"]["W"], drawn_["ab"]["H"]],
                                           "legend_words": words_by["ab"]},
                       "Supplementary Figure 8 (D283)": {"folder": out.name,
                                                         "panels": "c, drawn with no letter", "stamp": stamp_c,
                                                         "page_mm": [drawn_["c"]["W"], drawn_["c"]["H"]],
                                                         "legend_words": words_by["c"]}}}
    for part_, P_ in plates_.items():
        prov_ = {**prov, "stamp": P_["stamp"], "page_mm": [drawn_[part_]["W"], drawn_[part_]["H"]],
                 "legend_words": words_by[part_],
                 "files": {q.name: sha256_file(q) for q in drawn_[part_]["files"]}}
        (P_["out"] / f"{P_['side']}_provenance.json").write_text(json.dumps(prov_, indent=1, default=str) + "\n")
    if not quiet:
        print(stamp)
        print(f"reproduced: L2 {reproduced['compared']} values and anchors; S463 {len(s463)} checks; T1_L2 k {k}; "
              f"G4_fig3c grid {cells_done} of {len(GRID_STRATS) * 12} cells complete")
        for part_, P_ in plates_.items():
            print(f"{P_['label']}: legend {words_by[part_]} words; page {drawn_[part_]['W']:.0f} x "
                  f"{drawn_[part_]['H']:.1f} mm; wrote {', '.join(q.name for q in drawn_[part_]['paths'].values())} "
                  f"and the rest into {rel(P_['out']) if P_['out'].is_relative_to(ROOT) else P_['out']}")
        print(f"check_drawn: {n_checked} drawn values equal their data workbooks")
    return {"n": n, "m": m, "n_parts": n_parts, "k": k, "words": words, "checked": n_checked,
            "c_cells": c_cells, "out": str(out), "main_out": str(main_out), "a_boxes": a_boxes, "b_lines": b_lines,
            "b_medians": b_medians, "b_refs": b_refs, "gemini_ref": [(r["cap"], r["median_pct"]) for r in gref],
            "b_summary": b_summary, "t1caps": list(t1caps), "page_mm": [W, H], "b_d181": b_d181,
            "c_d185": g4d is not None and mut != "c_v24_with_d185",
            "strip": [(x["system"], x["cap"], x["what"], x["value"]) for x in b_summary["strip"]],
            "a_medians": [(r["system"], r["cap"], r["median_pct"]) for r in fn["a"] if r["row"] == "cap"],
            "grid": [(r["score"], r["index"], r["strategy"], r["d_pp"], r["interval_excludes_0"]) for r in fn["c"]],
            "cells_done": cells_done,
            "b_means": [(r["model"], r["cap"], r["mean_pct"], r["median_pct"]) for r in fn["b"] if r["row"] == "cap"]}


# ---------------------------------------------------------------------------------------------------------------
# SELFTEST and MUTANTS (offline fixtures, NOT DATA)
# ---------------------------------------------------------------------------------------------------------------
def make_fixture(root: Path) -> dict:
    """A fake pull of the real shape: T1 (question 1 complete for the four models, question 2 begun) and G4 (every
    index both strategies, one index's single pass unit still claimed), with the real 15 and 135 question ids."""
    from experiments.runner import experiment as ex
    from experiments.scorers import records
    asg = CT.load_assignment()
    key = S470.the_key()
    t1 = root / "t1"
    (t1 / "results_v4").mkdir(parents=True)
    (t1 / "assignment.toml").write_bytes(CT.ASSIGNMENT.read_bytes())
    order = CT.cells(asg, 1)
    q1, q2 = asg["question_order"][:2]
    stored = [c for c in order if c[0] == q1 and c[2] in T1_FOUR] + \
             [c for c in order if c[0] == q2 and c[1] == asg["depths"][0] and c[2] == T1_FOUR[0]]
    front = max(order.index(c) for c in stored)
    log, rows_by = [], collections.defaultdict(list)
    for g, c in enumerate(order[:front + 1]):
        cell = list(c)
        if c[2] in CT.HELD:
            log.append({"pass": "P1", "draw": 1, "action": "held", "g": g, "cell": cell})
            continue
        if c not in stored:
            continue
        log.append({"pass": "P1", "draw": 1, "action": "begin", "g": g, "cell": cell})
        log.append({"pass": "P1", "draw": 1, "action": "end", "g": g, "cell": cell, "rc": 0, "stored": True,
                    "load_ok": True})
        q, cap, m, d = c
        concepts = key["questions"][q]["expected_concepts"]
        j = T1_FOUR.index(m)
        take = concepts[: max(1, (len(concepts) * (1 + (cap + j) % 4)) // 4)]
        failed = (m == T1_FOUR[1] and cap == asg["depths"][0])
        rows_by[m].append({"answer_key": CT.ex.answer_key(f"rlm_{cap}", q, d), "question_id": q, "depth": cap,
                           "draw": d, "model": CT.LOCAL + m, "run_id": f"fixture_{cap}",
                           "answer": "" if failed else " ".join(take),
                           "error": "max_turns_empty: fixture" if failed else None,
                           "stop_reason": "max_turns_empty" if failed else "final",
                           "rlm": {"turns": cap if failed else max(1, cap // 2), "max_turns": cap,
                                   "turn_limit_note": False}})
    files = {}
    for m, rr in rows_by.items():
        p = t1 / "results_v4" / f"{CT.prefix(m)}_fixture.json"
        p.write_text(json.dumps({"results": rr}))
        files[f"results_v4/{p.name}"] = {"model": m, "sha256": sha256_file(p), "bytes": p.stat().st_size, "mtime": 1}
    (t1 / "interleaved_walk.jsonl").write_text("".join(json.dumps(r) + "\n" for r in log))
    for n in ("assignment.toml", "interleaved_walk.jsonl"):
        files[n] = {"sha256": sha256_file(t1 / n), "bytes": (t1 / n).stat().st_size}
    (t1 / "PULL.json").write_text(json.dumps({"clone_head": "f" * 40, "taken_utc": "2026-10-23T00:00:00Z",
                                              "files": files, "held_model_files": {m: 0 for m in CT.HELD}}))
    # G4
    qs = [q["id"] for q in ex.questions()]
    inp = root / "g4_inputs"
    out_g4 = root / "s3" / "out_g4"
    (out_g4 / "judge").mkdir(parents=True)
    copyj = {"copied": "fixture", "set": "G4", "from": "fixture", "answer_lines": {}}
    man, collect = [], []
    idxs = [f"exp_v4_s{c}_n{r}" for c in (5, 10, 20, 50) for r in (0, 1, 3)]
    r38_keys = []
    for cfg in G4_ALL:                            # D150: all six strategies
        for idx in idxs:
            run = G4_RUN.format(config=cfg, index=idx)
            rd = inp / "runs" / run
            rd.mkdir(parents=True)
            L, J = [], []
            for i, q in enumerate(qs):
                k = f"{idx}|{cfg}|{q}|d1"
                h = int(hashlib.sha256(k.encode()).hexdigest()[:8], 16)
                err = None
                stop = "final"
                if cfg == "rlm_10" and idx == "exp_v4_s5_n0" and i == 0:
                    err, stop = "RLMRunError: Maximum turns", "max_turns_empty"
                if cfg == "rlm_10" and idx == "exp_v4_s10_n0" and i == 1:
                    err, stop = "RLMRunError: LLM error", "call_error"
                    r38_keys.append(f"{run}|{idx}|{cfg}|{q}|d1|call_error|503")
                L.append({"answer_key": k, "run_id": run, "index_name": idx, "question_id": q, "config": cfg,
                          "draw": 1, "question_sets": ["common", "per_size"] if i % 3 else ["common"],
                          "generation": {"answer": "" if err else "text", "error": err, "stop_reason": stop}})
                if err:
                    continue
                corr = 1 + (h % 5) if cfg == "rlm_10" else 1 + ((h // (7 + G4_ALL.index(cfg))) % 5)
                J.append({"run_id": run, "config": cfg, "question_id": q, "draw": 1, "answer_key": k,
                          "item_sha256": "i" * 64, "run_sha256": "38ae" + "0" * 60,
                          "answerable_prompt": records.group_of(q) != "not_answerable", "lock_sha256": LOCK_WANT,
                          "a": {"status": "ok", "scores": {"correctness": corr}}, "b": {"status": "deferred"}})
            if cfg == "single_pass" and idx == "exp_v4_s20_n1":
                J[3]["a"] = {"status": "unparseable"}
            (rd / "answers.jsonl").write_text("".join(json.dumps(a) + "\n" for a in L))
            (rd / "run_identity.json").write_text("{}")
            for n in ("answers.jsonl", "run_identity.json"):
                man.append(f"{sha256_file(rd / n)}  runs/{run}/{n}")
            copyj["answer_lines"][run] = len(L)
            jd = out_g4 / "judge" / run
            jd.mkdir(parents=True)
            (jd / ("judge_" + "passages.jsonl")).write_text("".join(json.dumps(x) + "\n" for x in J))
            (jd / ("judge_" + "passages_summary.json")).write_text(json.dumps({
                "draws": [1], "rows": len(J), "status_a": dict(collections.Counter(x["a"]["status"] for x in J))}))
            collect += J
    (inp / "COPY.json").write_text(json.dumps(copyj))
    (inp / "MANIFEST.sha256").write_text("\n".join(man) + "\n")
    (out_g4 / "claims.txt").write_text("".join(f"p1__{G4_RUN.format(config=c, index=i)}\n" for c, i in (
        ("single_pass", "exp_v4_s50_n3"), ("verified_pass", "exp_v4_s5_n0"), ("verified_pass", "exp_v4_s5_n1"))))
    (root / "g4_collect.jsonl").write_text("".join(json.dumps(x) + "\n" for x in collect))
    g4r38 = root / "g4r38_keys.txt"
    g4r38.write_text("# fixture\n" + "".join(x + "\n" for x in r38_keys))
    return {"g4r38": g4r38, "g4r38_want": {"rlm_10": len(r38_keys), "single_pass": 0},
            "g4r38_want_all": {c: (len(r38_keys) if c == "rlm_10" else 0) for c in G4_ALL}}


def fixture_t1_d181(t1dir: Path, out: Path, mutate=None) -> Path:
    """D188: a T1_L2_d181 of S514 t1's shape from the fixture's T1_L2 (FIXTURE, NOT DATA): each row's D181 value half
    its loose value (0 when failed), its loose base the loose value, the header held to t1dir's rows and tables.
    mutate(rows, header) alters it before the tables are written."""
    rows = []
    for r in load_rows(t1dir / "concept_recall.jsonl"):
        x = {k: r[k] for k in T1_D181_TIE + ("error_kind",)}
        x.update(n_concepts=r["n_concepts"], found_loose_base=r["found_loose"], found_exact_base=r["found_exact"],
                 concept_recall_loose_base=r["text_recall_loose"], concept_recall_exact_base=r["text_recall_exact"],
                 text_concept_recall=round(r["text_recall_loose"] / 2, 4))
        x["concept_recall"] = 0.0 if r["failed"] else x["text_concept_recall"]
        rows.append(x)
    tab = json.loads((t1dir / "cap_tables.json").read_text())
    header = {"script": S514_SCRIPT, "reading": "D181", "provisional": False, "rows": len(rows),
              "key": {"sha256": S463.JR.S512.KEY25_SHA256},
              "held_to": {n: {"sha256": sha256_file(t1dir / n)} for n in ("concept_recall.jsonl", "cap_tables.json")}}
    if mutate:
        mutate(rows, header)
    out.mkdir(parents=True, exist_ok=True)
    write_files(out, {"concept_recall.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                      "cap_tables.json": json.dumps(t1_tables(rows, tab["models"], tab["caps"],
                                                              tab["complete_questions"], field="concept_recall"),
                                                    indent=1, sort_keys=True) + "\n",
                      "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n"})
    return out


def fixture_g4_d185(g4dir: Path, out: Path, mutate=None) -> tuple[Path, dict]:
    """D188: a G4_fig3c_d185 of S514 g4c's shape from the fixture's G4_fig3c (FIXTURE, NOT DATA): every row at draw 1,
    one covered RLM-10 cell of a question v2.5 changed given another correctness (key_versions "v2.5"), the other cells
    of the 132 "v2.4 awaiting S6", the rest "v2.4"; the header with the draw-1 units. mutate(rows, header) alters it
    before the tables are written. Returns the folder and the changed cell."""
    h = json.loads((g4dir / "header.json").read_text())
    units, indexes = h["grid"]["inputs"]["units"], h["grid"]["inputs"]["indexes"]
    changed = set(S463.JR.S512.changed_ids())
    rows = load_rows(g4dir / "grid_pairs.jsonl")
    pick = next(r for r in rows if r["covered"] and r["question_id"] in changed and r["cells"]["rlm_10"]["status"] ==
                "ok" and units[f"rlm_10 {r['index']}"]["complete"] and units[f"single_pass {r['index']}"]["complete"])
    c = pick["cells"]["rlm_10"]
    c["correctness"] = 1 if c["correctness"] >= PASS3 else 5
    c["pass3"], c["pass4"] = int(c["correctness"] >= PASS3), int(c["correctness"] >= PASS4)
    for r in rows:
        r["draw"] = 1
        r["key_versions"] = {s_: ("v2.5" if r is pick and s_ == "rlm_10" else
                                  D185_AWAIT if r["question_id"] in changed else "v2.4") for s_ in r["cells"]}
    header = {"script": S514_SCRIPT, "provisional": True, "draws": {"main": 1, "present": [1], "read_for_noise": [1]},
              "units_draw1": units, "rows": {"grid_pairs": len(rows)}}
    if mutate:
        mutate(rows, header)
    strip = [{k: v for k, v in r.items() if k not in D185_ADDED_ROW} for r in rows]
    grid = grid_tables(strip, indexes, header.get("units_draw1") or units)
    for e in grid["cells"]:
        e["awaiting_s6_answers"] = sum((r["key_versions"].get(e["strategy"]) == D185_AWAIT) +
                                       (r["key_versions"].get("single_pass") == D185_AWAIT)
                                       for r in rows if r["index"] == e["index"] and r.get("covered"))
    grid.update(provisional=True, awaiting_s6={}, rests_on="fixture")
    out.mkdir(parents=True, exist_ok=True)
    write_files(out, {"grid_pairs.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                      "grid_tables.json": json.dumps(grid, indent=1, sort_keys=True) + "\n",
                      "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n"})
    return out, {"index": pick["index"], "question_id": pick["question_id"], "strategy": "rlm_10"}


def _run_fixture(root: Path, mutate=None, plate_mut=None, d181: bool = False, d188: dict | None = None) -> dict:
    """d181 (D186 (4)): a draws the committed L2_d135_d181 after reproduce_l2_d181 (the committed L2_d135 as the
    loose reading it is held to), as the plate's default; otherwise a draws L2/'s loose reading. b and c are the
    fixture's either way (FIXTURE, NOT DATA). d188 (with d181): b draws fixture_t1_d181 and c fixture_g4_d185, built
    from the fixture's T1_L2 and G4_fig3c (d188's "t1_mut" and "g4_mut" alter them)."""
    fx = make_fixture(root)
    if mutate:
        mutate(root, fx)
    t1o, g4o, outp = root / "T1_L2", root / "G4_fig3c", root / "plate"
    r1 = t1_build(root, t1o, gate=False)
    r2 = g4_build(root, g4o, fx["g4r38"], fx["g4r38_want"], fx["g4r38_want_all"], anchor_path=None,
                  pre_anchor_path=None, g4r38_texts=None)
    if mutate and getattr(mutate, "after_build", None):
        mutate.after_build(root)
    t1_d181 = g4_d185 = changed_cell = None
    if d188 is not None:
        t1_d181 = fixture_t1_d181(t1o, root / "T1_L2_d181", d188.get("t1_mut"))
        g4_d185, changed_cell = fixture_g4_d185(g4o, root / "G4_fig3c_d185", d188.get("g4_mut"))
    if d181:
        # the fixture's c has incomplete cells, whose two legend clauses with D181's words take the legend over the
        # lock's limit; the limit is lifted for the fixture only (the real plate is held to it)
        lg = S475.FLOCK["legend"]
        saved = lg["words_under"]
        lg["words_under"] = int(saved) + 50
        try:
            r3 = plate(outp, t1o, g4o, mut=plate_mut, quiet=True, l2_drawn_dir=L2_D135, t1_d181_dir=t1_d181,
                       g4_d185_dir=g4_d185)
        finally:
            lg["words_under"] = saved
    else:
        r3 = plate(outp, t1o, g4o, mut=plate_mut, quiet=True, l2_d181_dirs=None, t1_d181_dir=None,
                   g4_d185_dir=None)                                               # loose (D186 (4))
    pts = json.loads((g4o / "point_tables.json").read_text())["points"]
    return {"t1": r1, "g4": r2, "plate": r3, "g4dir": g4o, "changed_cell": changed_cell, "t1_d181": t1_d181,
            "c": [(p["index"], p["drawn"], (p.get("main") or {}).get("d_pp")) for p in pts]}


def fixture_anchor(path: Path, tables: dict) -> Path:
    """An anchor of read_anchor's shape from a two-strategy reading's drawn points (FIXTURE, NOT DATA)."""
    pts = {}
    for p in tables["points"]:
        if p["drawn"]:
            m, t = p["main"], p["threshold4"]
            pts[p["index"]] = {"n3": m["questions_paired"], "d3": m["d_pp"], "lo3": m["ci95_pp"][0],
                               "hi3": m["ci95_pp"][1], "p3": m["p_signflip"], "n4": t["questions_paired"],
                               "d4": t["d_pp"], "lo4": t["ci95_pp"][0], "hi4": t["ci95_pp"][1], "p4": t["p_signflip"]}
    path.write_text(json.dumps({"from_commit": ANCHOR_FROM[0], "points": pts}, indent=1, sort_keys=True) + "\n")
    return path


def selftest_d156(root: Path) -> list:
    """D156 (O1): with a G4R38 rerun judged, D149's anchor is checked on the reading with it held out (that reading
    must equal the anchor or g4_build refuses), and the judged reading is the one written and drawn. FIXTURE, NOT
    DATA: the fixture's G4R38 key (rlm_10, exp_v4_s10_n0, a covered question) gets a judged rerun in out_g4r38, as
    s3_guard collect --replace puts it in the collect."""
    fails = []
    fx = make_fixture(root)
    key = next(k for k in read_g4r38(fx["g4r38"]))
    idx, cfg, q, _ = key.split("|")
    run = G4_RUN.format(config=cfg, index=idx)
    row = {"run_id": run, "config": cfg, "question_id": q, "draw": 1, "answer_key": key, "item_sha256": "i" * 64,
           "run_sha256": "38ae" + "0" * 60, "answerable_prompt": True, "lock_sha256": LOCK_WANT,
           "a": {"status": "ok", "scores": {"correctness": 5}}, "b": {"status": "deferred"}}
    jd = root / "s3" / "out_g4r38" / "judge" / run
    jd.mkdir(parents=True)
    (jd / ("judge_" + "passages.jsonl")).write_text(json.dumps(row) + "\n")
    with open(root / "g4_collect.jsonl", "a") as fh:
        fh.write(json.dumps(row) + "\n")
    want = (fx["g4r38"], fx["g4r38_want"], fx["g4r38_want_all"])
    hcells, hinfo = g4_cells(root, fx["g4r38"], fx["g4r38_want"], hold_g4r38=True)
    jcells, jinfo = g4_cells(root, fx["g4r38"], fx["g4r38_want"])
    held_tab, judged_tab = g4_tables(hcells, hinfo["indexes"]), g4_tables(jcells, jinfo["indexes"])
    hp = {p["index"]: p for p in held_tab["points"]}[idx]["main"]["questions_paired"]
    jp = {p["index"]: p for p in judged_tab["points"]}[idx]["main"]["questions_paired"]
    if jp != hp + 1:
        fails.append(f"D156 fixture: {idx} paired {jp} judged, {hp} held; want one more when judged")
    a_held = fixture_anchor(root / "anchor_held.json", held_tab)
    a_judged = fixture_anchor(root / "anchor_judged.json", judged_tab)
    out = root / "G4_d156"
    try:
        r = g4_build(root, out, *want, anchor_path=a_held, pre_anchor_path=None, g4r38_texts=None)
    except Refused as e:
        return fails + [f"D156: the build refused with the anchor of the held reading: {e}"]
    h = json.loads((out / "header.json").read_text())
    g = h["grid"]["gate"]
    cell = next(x for x in load_rows(out / "pairs.jsonl") if x["index"] == idx and x["question_id"] == q)["cells"][cfg]
    if cell["status"] != "ok" or cell["pass4"] != 1:
        fails.append(f"D156: the drawn reading's {key} cell is {cell}, not the judged rerun")
    if g["g4r38_held_for_anchor"] != [key] or "held out" not in g["anchor_reading"] or \
            "judged" not in g["drawn_reading"] or g["anchor"] != rel(a_held) or r["drawn"] != h["drawn_indexes"]:
        fails.append(f"D156: header.json's gate does not record the held reading gated and the judged one drawn: {g}")
    drawn_n = {p["index"]: p for p in json.loads((out / "point_tables.json").read_text())["points"]}
    if drawn_n[idx]["main"]["questions_paired"] != jp:
        fails.append(f"D156: point_tables.json {idx} paired {drawn_n[idx]['main']['questions_paired']}, judged {jp}")
    try:
        reproduce_g4(out, anchor_path=a_held)
    except Refused as e:
        fails.append(f"D156: reproduce_g4 refused the build it gated: {e}")
    # refusals: the judged reading's anchor (the gate run on the drawn reading would pass it); an anchor one off
    off = json.loads(a_held.read_text())
    off["points"][idx]["n3"] += 1
    a_off = root / "anchor_off.json"
    a_off.write_text(json.dumps(off, indent=1, sort_keys=True) + "\n")
    for name, a in (("the judged reading's anchor", a_judged), ("an anchor one question off", a_off)):
        try:
            g4_build(root, root / ("G4_refused_" + a.stem), *want, anchor_path=a, pre_anchor_path=None,
                     g4r38_texts=None)
            fails.append(f"D156: g4_build accepted {name}")
        except Refused as e:
            if "(D149)" not in str(e):
                fails.append(f"D156: {name} refused for another reason: {e}")
    try:
        reproduce_g4(out, anchor_path=a_off)
        fails.append("D156: reproduce_g4 accepted another anchor than the one recorded")
    except Refused:
        pass
    sw = root / "G4_d156_anchor_swapped"             # the judged reading's anchor recorded as the one gated on
    shutil.copytree(out, sw)
    hs = json.loads((sw / "header.json").read_text())
    hs["grid"]["anchor_sha256"] = sha256_file(a_judged)
    (sw / "header.json").write_text(json.dumps(hs, indent=1, sort_keys=True) + "\n")
    try:
        reproduce_g4(sw, anchor_path=a_judged)
        fails.append("D156: reproduce_g4 checked the anchor on the judged reading (the judged reading's anchor passed)")
    except Refused as e:
        if "(D149)" not in str(e):
            fails.append(f"D156: reproduce_g4 refused the judged reading's anchor for another reason: {e}")
    tam = root / "G4_d156_tampered"                  # the rerun's cell written back as held: no longer the judged rows
    shutil.copytree(out, tam)
    prs = load_rows(tam / "grid_pairs.jsonl")
    for x in prs:
        if x["index"] == idx and x["question_id"] == q:
            x["cells"][cfg] = dict(HELD_CELL)
    (tam / "grid_pairs.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in prs))
    try:
        reproduce_g4(tam, anchor_path=a_held)
        fails.append("D156: reproduce_g4 accepted grid rows with the judged rerun held")
    except Refused:
        pass
    return fails


def selftest_d160(root: Path) -> list:
    """D160 (6) Q18 on the D156 fixture (FIXTURE, NOT DATA): the pre-D156 comparison passes on an anchor made from the
    held reading and refuses a cell changed by one question or a change outside the G4R38 cells; the judge-row check
    refuses a judge row whose correctness differs from the drawn cell and a G4R38 key with a row in out_g4; the frozen
    rerun texts pass when they are the judged keys and refuse one missing or with an error."""
    fails = []
    fx = make_fixture(root)
    key = next(k for k in read_g4r38(fx["g4r38"]))
    idx, cfg, q, _ = key.split("|")
    run = G4_RUN.format(config=cfg, index=idx)
    row = {"run_id": run, "config": cfg, "question_id": q, "draw": 1, "answer_key": key, "item_sha256": "i" * 64,
           "run_sha256": "38ae" + "0" * 60, "answerable_prompt": True, "lock_sha256": LOCK_WANT,
           "a": {"status": "ok", "scores": {"correctness": 5}}, "b": {"status": "deferred"}}
    jd = root / "s3" / "out_g4r38" / "judge" / run
    jd.mkdir(parents=True)
    (jd / ("judge_" + "passages.jsonl")).write_text(json.dumps(row) + "\n")
    with open(root / "g4_collect.jsonl", "a") as fh:
        fh.write(json.dumps(row) + "\n")
    cells6, info6 = g4_cells(root, fx["g4r38"], fx["g4r38_want_all"], configs=G4_ALL)
    hcells6, hinfo6 = g4_cells(root, fx["g4r38"], fx["g4r38_want_all"], configs=G4_ALL, hold_g4r38=True)
    grid = grid_tables(cells6, info6["indexes"], info6["units"])
    hgrid = grid_tables(hcells6, hinfo6["indexes"], hinfo6["units"])
    held = info6["g4r38_judged_keys"]
    pre = {"from_commit": ANCHOR_PRE_D156_FROM[0], "path": "fixture", "cells": copymod.deepcopy(hgrid["cells"])}
    ap = root / "anchor_pre.json"
    ap.write_text(json.dumps(pre))
    # (1) passes; the cell the rerun enters is recorded with its old and new value
    try:
        rec = pre_d156_check(hgrid, grid, read_anchor_pre_d156(ap), held)
        hit = [c for c in rec["drawn_changed"] if c["strategy"] == cfg and c["index"] == idx]
        if not hit or any(c["why"] != "a judged G4R38 rerun enters it" for c in hit) or \
                rec["equal_on_held_reading"] != rec["complete_before_d156"]:
            fails.append(f"D160 pre-D156: the rerun's cells are not recorded as changed by it: {rec['drawn_changed']}")
    except Refused as e:
        fails.append(f"D160 pre-D156: refused the held reading's own anchor: {e}")
    # (2) a complete cell one question off refuses; (3) a cell incomplete before is recorded as complete since
    one = next(i for i, e in enumerate(pre["cells"]) if e["complete"] and e["strategy"] != cfg)
    off = copymod.deepcopy(pre)
    off["cells"][one]["n_paired"] += 1
    ap.write_text(json.dumps(off))
    try:
        pre_d156_check(hgrid, grid, read_anchor_pre_d156(ap), held)
        fails.append("D160 pre-D156: accepted a cell one question off")
    except Refused:
        pass
    inc = copymod.deepcopy(pre)
    inc["cells"][one] = {k: inc["cells"][one][k] for k in ("score", "index", "core_papers", "distractor_ratio",
                                                           "strategy")} | {"complete": False}
    ap.write_text(json.dumps(inc))
    try:
        rec = pre_d156_check(hgrid, grid, read_anchor_pre_d156(ap), held)
        if len(rec["complete_since_d156"]) != 1:
            fails.append(f"D160 pre-D156: an incomplete cell not recorded as complete since: {rec}")
    except Refused as e:
        fails.append(f"D160 pre-D156: refused a cell complete since D156: {e}")
    # (4) a drawn change outside the G4R38 cells refuses
    g2 = copymod.deepcopy(grid)
    e2 = next(e for e in g2["cells"] if e["complete"] and e["strategy"] not in (cfg, "single_pass"))
    e2["d_pp"] += 1.0
    ap.write_text(json.dumps(pre))
    try:
        pre_d156_check(hgrid, g2, read_anchor_pre_d156(ap), held)
        fails.append("D160 pre-D156: accepted a drawn change outside the G4R38 cells")
    except Refused:
        pass
    # (5) a single pass rerun on an index touches every strategy's cell there (each is that strategy against single
    # pass): a drawn change in such a cell, on an index no other held key names, is recorded, not refused
    e3 = next((e for e in g2["cells"] if e is not e2 and e["complete"] and e["index"] != idx
               and e["strategy"] != cfg), None)
    if e3 is None:
        fails.append("D160 pre-D156: the fixture has no complete cell on another index for the single pass case")
    else:
        g3 = copymod.deepcopy(grid)
        next(e for e in g3["cells"] if (e["score"], e["strategy"], e["index"]) ==
             (e3["score"], e3["strategy"], e3["index"]))["d_pp"] += 1.0
        try:
            rec = pre_d156_check(hgrid, g3, read_anchor_pre_d156(ap), list(held) + [f"{e3['index']}|single_pass|{q}|d1"])
            if not any(c["strategy"] == e3["strategy"] and c["index"] == e3["index"] and
                       c["why"] == "a judged G4R38 rerun enters it" for c in rec["drawn_changed"]):
                fails.append(f"D160 pre-D156: a single pass rerun's cell not recorded as changed by it: {rec}")
        except Refused as e:
            fails.append(f"D160 pre-D156: refused a cell changed by a single pass rerun on its index: {e}")
    # judge rows: passes; a row in a judge folder with another correctness refuses; a G4R38 key in out_g4 refuses
    try:
        rec = judge_row_check(root, cells6, held)
        if rec["g4r38_from_out_g4r38"] != 1:
            fails.append(f"D160 judge rows: the G4R38 rerun not read from out_g4r38: {rec}")
    except Refused as e:
        fails.append(f"D160 judge rows: refused the fixture: {e}")
    jf = root / "s3" / "out_g4" / "judge" / G4_RUN.format(config="rlm_20", index="exp_v4_s20_n0") / \
        ("judge_" + "passages.jsonl")
    keep_bytes = jf.read_bytes()
    lines = [json.loads(x) for x in keep_bytes.decode().splitlines() if x.strip()]
    c0 = next(x for x in lines if x["a"].get("status") == "ok")
    c0["a"]["scores"]["correctness"] = 4 if c0["a"]["scores"]["correctness"] < 4 else 1
    jf.write_text("".join(json.dumps(x) + "\n" for x in lines))
    try:
        judge_row_check(root, cells6, held)
        fails.append("D160 judge rows: accepted a judge row whose correctness is not the drawn cell's")
    except Refused:
        pass
    jf.write_bytes(keep_bytes)
    j4 = root / "s3" / "out_g4" / "judge" / run / ("judge_" + "passages.jsonl")
    with open(j4, "a") as fh:
        fh.write(json.dumps(row) + "\n")
    try:
        judge_row_check(root, cells6, held)
        fails.append("D160 judge rows: accepted a G4R38 key with a row in out_g4")
    except Refused:
        pass
    # the frozen rerun texts
    tx = root / "g4r38_texts"
    rd = tx / "runs" / run
    rd.mkdir(parents=True)
    line = {"answer_key": key, "run_id": run, "index_name": idx, "question_id": q, "config": cfg, "draw": 1,
            "generation": {"answer": "rerun text", "error": None, "stop_reason": "final"}}
    (rd / "answers.jsonl").write_text(json.dumps(line) + "\n")
    (tx / "COPY.json").write_text("{}")
    (tx / "MANIFEST.sha256").write_text(f"{sha256_file(rd / 'answers.jsonl')}  runs/{run}/answers.jsonl\n")
    sums = {rel(p): sha256_file(p) for p in tx.rglob("*") if p.is_file()}
    try:
        rec = g4r38_texts_check(held, tx, sums)
        if not rec["frozen"] or rec["answers"] != 1:
            fails.append(f"D160 G4R38 texts: {rec}")
    except Refused as e:
        fails.append(f"D160 G4R38 texts: refused the fixture: {e}")
    for name, bad_line in (("an error", {**line, "generation": {"answer": "", "error": "503"}}),
                           ("another key", {**line, "answer_key": key.replace("|d1", "|d2")})):
        (rd / "answers.jsonl").write_text(json.dumps(bad_line) + "\n")
        (tx / "MANIFEST.sha256").write_text(f"{sha256_file(rd / 'answers.jsonl')}  runs/{run}/answers.jsonl\n")
        s2 = {rel(p): sha256_file(p) for p in tx.rglob("*") if p.is_file()}
        try:
            g4r38_texts_check(held, tx, s2)
            fails.append(f"D160 G4R38 texts: accepted {name}")
        except Refused:
            pass
    try:
        g4r38_texts_check(held, tx, sums)
        fails.append("D160 G4R38 texts: accepted files that are not their SHA256SUMS lines")
    except Refused:
        pass
    return fails


def selftest_d181(root: Path) -> list:
    """D186 (4) on the committed folders (not a fixture: the D181 readings exist only as committed): reproduce_l2_d181
    passes on L2/, L2_d135/, L2_d181/ and L2_d135_d181/, and refuses a copy whose header is provisional or on another
    key, whose row is another answer, whose loose base on an unchanged-concept question is not the loose value,
    whose D181 value no longer gives cap_tables.json, or whose drawn G6 row's turns used differ from the loose row
    (each copy read at its own sha256, and an unaltered copy passes); it also refuses a file at another sha256 than
    pinned, a count of G6 rows changed between the readings other than the loose one, and other caps; S475's D181
    anchors moved by 0.1 stop it (exit 2)."""
    fails = []
    caps = tuple(json.loads((L2 / "header.json").read_text())["caps"])
    gate = load_rows(L2 / "concept_recall.jsonl")
    drawn, _, l2h = reproduce_l2_drawn(L2_D135, gate, caps)
    try:
        ok = reproduce_l2_d181(gate, drawn, caps, loose_held=l2h["held_check"])
        if ok["record"]["anchors"] != {"G5 cap 20": "71.9", "G6 cap 50": "63.1"}:
            fails.append(f"D181 anchors recorded {ok['record']['anchors']}")
    except (Refused, SystemExit) as e:
        return [f"reproduce_l2_d181 refused the committed D181 folders: {e}"]
    S512 = S463.JR.S512
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}

    def copy_with(name, which, edit_rows=None, edit_header=None):
        out = {}
        for tag, src in (("gated", L2_D181), ("drawn", L2_D135_D181)):
            d = root / name / tag
            d.mkdir(parents=True)
            rows = load_rows(src / "concept_recall.jsonl")
            hdr = json.loads((src / "header.json").read_text())
            if tag == which and edit_rows:
                edit_rows(rows)
            if tag == which and edit_header:
                edit_header(hdr)
            (d / "concept_recall.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
            (d / "header.json").write_text(json.dumps(hdr))
            shutil.copy(src / "cap_tables.json", d / "cap_tables.json")
            out[tag] = d
        return out["gated"], out["drawn"]

    def pins_of(g_, d_):                         # an altered copy is read at its own sha256, so the case tests its
        return {t_: {n: sha256_file(x_ / n) for n in L2_FILES} for t_, x_ in (("gated", g_), ("drawn", d_))}

    def first(rows, pred):
        return next(r for r in rows if pred(r))
    acted = {k for (_, k), a in g6_d135_listed().items() if a in ("rerun", "rebuild")}
    cases = [("a provisional header", "gated", None, lambda h: h.update(provisional=True)),
             ("a row of another answer", "drawn", lambda R: first(R, lambda r: True).update(answer_sha256="0" * 64), None),
             ("a loose base on an unchanged-concept question moved", "gated",
              lambda R: first(R, lambda r: r["question_id"] in same_c).update(found_loose_base=-1), None),
             ("a D181 value that no longer gives cap_tables.json", "drawn",
              lambda R: first(R, lambda r: r["question_id"] not in same_c).update(concept_recall=0.123), None),
             ("a drawn G6 row whose turns used differ from its loose row", "drawn",
              lambda R: first(R, lambda r: r["system"] == "G6" and r["answer_key"] not in acted).update(
                  turns_used=-1), None),
             ("a header on another key than v2.5", "drawn", None,
              lambda h: h.setdefault("key", {}).update(sha256="0" * 64))]
    for name, which, er, eh in cases:
        g_, d_ = copy_with(name.replace(" ", "_"), which, er, eh)
        try:
            reproduce_l2_d181(gate, drawn, caps, g_, d_, loose_held=l2h["held_check"], pins=pins_of(g_, d_))
            fails.append(f"reproduce_l2_d181 did not refuse {name}")
        except Refused:
            pass
    # an unaltered copy at its own sha256 passes, so the cases above are refused for what they alter
    g_, d_ = copy_with("unaltered", None)
    try:
        reproduce_l2_d181(gate, drawn, caps, g_, d_, loose_held=l2h["held_check"], pins=pins_of(g_, d_))
    except Refused as e:
        fails.append(f"reproduce_l2_d181 refused an unaltered copy: {e}")
    held_off = {**l2h["held_check"], "g6_rows_changed": l2h["held_check"]["g6_rows_changed"] + 1}
    more = [("a file of the committed folders at another sha256 than pinned (F5)",
             lambda: reproduce_l2_d181(gate, drawn, caps, loose_held=l2h["held_check"], pins={
                 **L2_D181_SHA256, "drawn": {**L2_D181_SHA256["drawn"], "header.json": "0" * 64}})),
            ("an unaltered copy read against the committed pins",
             lambda: reproduce_l2_d181(gate, drawn, caps, g_, d_, loose_held=l2h["held_check"])),
            ("the D181 readings changing another count of G6 rows than the loose ones",
             lambda: reproduce_l2_d181(gate, drawn, caps, loose_held=held_off)),
            ("a's caps other than the headers' caps",
             lambda: reproduce_l2_d181(gate, drawn, caps[:-1], loose_held=l2h["held_check"]))]
    for name, f_ in more:
        try:
            f_()
            fails.append(f"reproduce_l2_d181 did not refuse {name}")
        except Refused:
            pass
    saved = dict(S475.ANCHORS_D181)
    try:
        S475.ANCHORS_D181[("G5", 20)] = "72.0"
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                reproduce_l2_d181(gate, drawn, caps, loose_held=l2h["held_check"])
            fails.append("a D181 anchor moved by 0.1 did not stop S475.reproduce")
        except SystemExit:
            pass
    finally:
        S475.ANCHORS_D181.clear()
        S475.ANCHORS_D181.update(saved)
    return fails


def selftest_d181_plate(root: Path) -> list:
    """D186 (4), the plate's wiring (FIXTURE, NOT DATA for b and c; a reads the committed L2 folders): the fixture
    drawn with a on L2_d135_d181 (the default) and again with a on L2_d135's loose reading. a's numbers must differ
    and equal S475.compute of the D181 rows on the D181 field; b (its lines, medians and gemini-3-flash-preview
    reference) and c must be the same in both, b's reference equal to the loose G5 values; the provenance and the
    legend name each panel's reading."""
    fails = []
    r1 = _run_fixture(root / "d181", d181=True)
    r0 = _run_fixture(root / "loose", d181=False)
    p1, p0 = r1["plate"], r0["plate"]
    caps = tuple(json.loads((L2 / "header.json").read_text())["caps"])
    drawn = load_rows(L2_D135_D181 / "concept_recall.jsonl")
    tab = json.loads((L2_D135_D181 / "cap_tables.json").read_text())
    _, qorder = S475.reproduce(load_rows(L2 / "concept_recall.jsonl"),
                               json.loads((L2 / "cap_tables.json").read_text()), caps)
    want_a = [(x["system"], x["cap"], x["median_pct"]) for x in
              a_with_boxes(S475.compute(drawn, tab, caps, qorder, S475.D181_FIELD)["a"], caps) if x["row"] == "cap"]
    if p1["a_medians"] != want_a:
        fails.append("D181 plate: a's medians are not S475.compute of L2_d135_d181 on the D181 field")
    if p1["a_medians"] == p0["a_medians"]:
        fails.append("D181 plate: a's medians equal the loose reading's")
    for k_ in ("gemini_ref", "b_means", "grid"):
        if p1[k_] != p0[k_]:
            fails.append(f"D181 plate: {k_} differs from the loose reading's (b and c stay on it)")
    l2d = load_rows(L2_D135 / "concept_recall.jsonl")
    t1t = json.loads((root / "d181" / "T1_L2" / "cap_tables.json").read_text())
    want_ref = [(c, float(np.median([100 * x[S475.LOOSE] for x in l2d if x["system"] == "G5" and x["cap"] == c
                                     and x["question_id"] in t1t["complete_questions"]]))) for c in t1t["caps"]]
    if p1["gemini_ref"] != want_ref:
        fails.append(f"D181 plate: b's reference {p1['gemini_ref']} is not L2_d135's loose G5 median {want_ref}")
    prov = json.loads((Path(p1["out"]) / f"{SIDE}_provenance.json").read_text())
    if rel(L2_D135_D181) not in json.dumps(prov):
        fails.append("D181 plate: the provenance does not name L2_d135_d181")
    leg = (Path(p1["main_out"]) / "legend_draft.md").read_text()          # a and b: Figure 4 (D283)
    if "words the question also holds" not in leg or "scored on key v2.4, with every concept word counted" not in leg:
        fails.append("D181 plate: the legend does not say which reading a and b draw")
    return fails


def selftest_d188(root: Path) -> list:
    """D188, the plate's wiring of b and c on key v2.5 (FIXTURE, NOT DATA for b and c; a reads the committed L2
    folders): the fixture drawn with b on fixture_t1_d181 and c on fixture_g4_d185, and again with b and c on the
    fixture's v2.4 readings. b's medians must be the medians of the D181 rows, its gemini-3-flash-preview reference the
    median of L2_d135_d181's G5 concept_recall on T1's complete questions; c's cells must differ exactly in the changed
    cell's index and strategy; the legend must not name key v2.4 for b. Then each tie is refused when broken."""
    fails = []
    r1 = _run_fixture(root / "d188", d181=True, d188={})
    r0 = _run_fixture(root / "d181", d181=True)
    p1, p0 = r1["plate"], r0["plate"]
    if not (p1["b_d181"] and p1["c_d185"]) or p0["b_d181"] or p0["c_d185"]:
        fails.append(f"D188 plate: b_d181 {p1['b_d181']}, c_d185 {p1['c_d185']} (want True), the v2.4 run "
                     f"{p0['b_d181']}, {p0['c_d185']} (want False)")
    t1d = load_rows(r1["t1_d181"] / "concept_recall.jsonl")
    t1t = json.loads((root / "d188" / "T1_L2" / "cap_tables.json").read_text())
    comp = t1t["complete_questions"]
    want_med = [(m, c, float(np.median([100 * x["concept_recall"] for x in t1d if x["model"] == m and x["cap"] == c
                                         and x["question_id"] in comp]))) for m in T1_FOUR for c in t1t["caps"]]
    got_med = [(m, c, med) for m, c, _, med in p1["b_means"]]
    if got_med != want_med or [x[3] for x in p1["b_means"]] == [x[3] for x in p0["b_means"]]:
        fails.append("D188 plate: b's medians are not the D181 rows' (or equal the loose reading's)")
    l2d = load_rows(L2_D135_D181 / "concept_recall.jsonl")
    want_ref = [(c, float(np.median([100 * x["concept_recall"] for x in l2d if x["system"] == "G5" and x["cap"] == c
                                     and x["question_id"] in comp]))) for c in t1t["caps"]]
    if p1["gemini_ref"] != want_ref:
        fails.append(f"D188 plate: b's reference {p1['gemini_ref']} is not L2_d135_d181's G5 median {want_ref}")
    cc = r1["changed_cell"]
    diff = {(sc, i, st) for (sc, i, st, d, _), (_, _, _, d0, _) in zip(p1["grid"], p0["grid"]) if d != d0}
    if not diff or {(i, st) for _, i, st in diff} != {(cc["index"], cc["strategy"])}:
        fails.append(f"D188 plate: c's differing cells {sorted(diff)}, want those of {cc}")
    leg = (Path(p1["main_out"]) / "legend_draft.md").read_text()          # b: Figure 4 (D283)
    prov = json.loads((Path(p1["out"]) / f"{SIDE}_provenance.json").read_text())
    if "scored on key v2.4" in leg or "scored as in b" in leg or not prov.get("t1_d181") or not prov.get("g4_d185"):
        fails.append("D188 plate: the legend still names key v2.4 for b, or the provenance lacks t1_d181 or g4_d185")
    # each tie broken is refused
    changed = set(S463.JR.S512.changed_ids())

    def g4_unchanged(rows, header):              # an unchanged question's cell changed
        r = next(r for r in rows if r["question_id"] not in changed and r["cells"]["single_pass"]["status"] == "ok")
        c = r["cells"]["single_pass"]
        c["correctness"] = 1 if c["correctness"] >= PASS3 else 5
        c["pass3"], c["pass4"] = int(c["correctness"] >= PASS3), int(c["correctness"] >= PASS4)

    def g4_no_units(rows, header):
        header.pop("units_draw1")

    def g4_key_versions(rows, header):           # a row whose key_versions miss a strategy
        rows[0]["key_versions"].pop("rlm_20")

    def t1_answer(rows, header):                 # a row tied to another text
        rows[0]["answer_sha256"] = "0" * 64

    def t1_held(rows, header):                   # held to another T1_L2 reading
        header["held_to"]["concept_recall.jsonl"]["sha256"] = "0" * 64

    def t1_failed(rows, header):                 # a failed answer given its text's value
        r = next(r for r in rows if r["failed"])
        r["concept_recall"] = 0.5

    def t1_key(rows, header):
        header["key"]["sha256"] = "0" * 64
    for name, d188 in (("an unchanged question's cell changed in G4_fig3c_d185", {"g4_mut": g4_unchanged}),
                       ("G4_fig3c_d185 without its draw-1 units", {"g4_mut": g4_no_units}),
                       ("a G4_fig3c_d185 row's key_versions short of a strategy", {"g4_mut": g4_key_versions}),
                       ("a T1_L2_d181 row tied to another text", {"t1_mut": t1_answer}),
                       ("T1_L2_d181 held to another T1_L2", {"t1_mut": t1_held}),
                       ("a failed T1 answer given a value", {"t1_mut": t1_failed}),
                       ("T1_L2_d181 on another key", {"t1_mut": t1_key})):
        sub = root / ("x_" + re.sub(r"\W+", "_", name))
        try:
            _run_fixture(sub, d181=True, d188=d188)
            fails.append(f"D188: {name} was not refused")
        except Refused:
            pass
    try:
        plate(root / "nod181", root / "d188" / "T1_L2", root / "d188" / "G4_fig3c", quiet=True, l2_d181_dirs=None,
              t1_d181_dir=r1["t1_d181"], g4_d185_dir=None)
        fails.append("D188: b on D181 with a on the loose reading was not refused")
    except Refused:
        pass
    return fails


def selftest(keep: Path | None = None) -> int:
    """keep: an empty folder (or one not yet made) to hold the fixture and its plate (FIXTURE, NOT DATA), to look at panel c drawn."""
    if keep is not None:
        keep = keep.expanduser().resolve()
        if keep.exists() and any(keep.iterdir()):
            raise Refused(f"{keep} exists and is not empty: keep the fixture in an empty folder")
        keep.mkdir(parents=True, exist_ok=True)
        r = _run_fixture(keep)
    else:                                          # kept until the checks below have read it (they read its files)
        tmp = tempfile.TemporaryDirectory(prefix="S476_selftest_")
        r = _run_fixture(Path(tmp.name))
    fails = []
    if r["t1"]["k"] != 1:
        fails.append(f"T1 fixture: k {r['t1']['k']}, want 1 (question 1 stored by the four models at six caps)")
    if r["t1"]["failed"] != 1:
        fails.append(f"T1 fixture: failed {r['t1']['failed']}, want 1")
    if len(r["g4"]["drawn"]) != 11:
        fails.append(f"G4 fixture: {len(r['g4']['drawn'])} indexes drawn, want 11 (one unit still claimed)")
    if r["plate"]["n_parts"]["b"] != 24:
        fails.append(f"plate: b answers {r['plate']['n_parts']['b']}, want 24")
    if not all(isinstance(x[2], float) for x in r["c"] if x[1]):
        fails.append("G4 fixture: a drawn index without d")
    # D150: panel c, the grid. 120 cells; empty exactly where a unit is not complete (the fixture's claims: single
    # pass at s50_n3, verified pass at s5_n0 and s5_n1); every number and frame equal to the data workbook
    pl = r["plate"]
    gd = pl["b_summary"]["grid"]
    u6 = json.loads((r["g4dir"] / "header.json").read_text())["grid"]["inputs"]["units"]
    nc = json.loads((Path(pl["out"]) / f"{SIDE}_numbers.json").read_text())
    sc_ = nc["sheets"][C_SHEET]
    sdc = {(x["score"], x["index"], x["strategy"]): x for x in (dict(zip(sc_["columns"], rr)) for rr in sc_["rows"])}
    if len(gd) != 2 * len(GRID_STRATS) * 12 or len(sdc) != len(gd):
        fails.append(f"c: {len(gd)} cells drawn, {len(sdc)} in the data workbook, want {2 * len(GRID_STRATS) * 12}")
    want_empty = {(i, s_) for s_ in GRID_STRATS for i in {x["index"] for x in gd}
                  if not (u6[f"{s_} {i}"]["complete"] and u6[f"single_pass {i}"]["complete"])}
    fixture_empty = {(i, s_) for s_ in GRID_STRATS for i in ("exp_v4_s50_n3",)} | \
        {("exp_v4_s5_n0", "verified_pass"), ("exp_v4_s5_n1", "verified_pass")}
    got_empty = {(x["index"], x["strategy"]) for x in gd if x["text"] is None}
    if got_empty != want_empty or want_empty != fixture_empty:
        fails.append(f"c: empty cells {sorted(got_empty)}, incomplete units give {sorted(want_empty)}, the fixture "
                     f"claims {sorted(fixture_empty)}")
    for x in gd:
        sd = sdc[(x["score"], x["index"], x["strategy"])]
        if x["text"] is None:
            continue
        excl = sd["ci95_lo_pp"] > 0 or sd["ci95_hi_pp"] < 0
        if x["text"] != cell_text(sd["d_pp"]) or x["framed"] != excl or bool(sd["interval_excludes_0"]) != excl:
            fails.append(f"c {x['strategy']} {x['index']} score {x['score']}: printed {x['text']!r} framed "
                         f"{x['framed']}, workbook {cell_text(sd['d_pp'])!r} interval {sd['ci95_lo_pp']:.2f} to "
                         f"{sd['ci95_hi_pp']:.2f}")
    n_c_printed = sum(1 for e in nc["printed"].values() if e.get("sheet") == C_SHEET)
    if n_c_printed != sum(1 for x in gd if x["text"] is not None) or pl["c_cells"] != n_c_printed:
        fails.append(f"c: {n_c_printed} numbers tied to sheet {C_SHEET}, {pl['c_cells']} cells read back, "
                     f"{sum(1 for x in gd if x['text'] is not None)} drawn")
    # A-1 and B-2 (Valerio, 26 October): two boxes per cap in a; per small panel of b a line per complete question,
    # the median and the Gemini reference, the reference equal to L2's G5 values on T1's complete questions
    pl = r["plate"]
    a_caps = json.loads(S475.HEADER_F.read_text())["caps"]
    if pl["a_boxes"] != 2 * len(a_caps):
        fails.append(f"plate a: {pl['a_boxes']} boxes checked, want {2 * len(a_caps)} (two per cap)")
    kk = r["t1"]["k"]
    if (pl["b_lines"], pl["b_medians"], pl["b_refs"]) != (len(T1_FOUR) * kk, len(T1_FOUR), len(T1_FOUR)):
        fails.append(f"plate b: {pl['b_lines']} question lines, {pl['b_medians']} medians, {pl['b_refs']} references "
                     f"checked, want {len(T1_FOUR) * kk}, {len(T1_FOUR)} and {len(T1_FOUR)}")
    bs = pl["b_summary"]                         # Valerio's follow-up: grey question lines, caps evenly spaced
    if bs["question_line_colours"] != [Q_GREY] or bs["x_positions"] != [tuple(float(i) for i in
                                                                        range(len(pl["t1caps"])))]:
        fails.append(f"plate b: question line colours {bs['question_line_colours']}, x positions "
                     f"{bs['x_positions']}; want [{Q_GREY}] and the caps at 0 to {len(pl['t1caps']) - 1}")
    # D149: the strip under a, two bars per system and cap, each equal to the data workbook and to L2, cut-off bars hatched
    st = bs["strip"]
    if len(st) != 2 * 2 * len(a_caps):
        fails.append(f"strip: {len(st)} bars, want {2 * 2 * len(a_caps)} (reached and cut off, two systems, each cap)")
    if any((x["what"] == "stopped_by_cap_pct") != (x["hatch_lines"] > 0) for x in st if x["value"] > 0) or \
            any(x["hatch_lines"] for x in st if x["what"] == "cap_reached_pct"):
        fails.append("strip: hatching is not on the cut-off bars only")
    nums = json.loads((Path(pl["main_out"]) / f"{MAIN_SIDE}_numbers.json").read_text())["sheets"][f"{MAIN_SHEET}a"]
    sd = {(x["system"], x["cap"]): x for x in (dict(zip(nums["columns"], rr)) for rr in nums["rows"])
          if x["row"] == "strip"}
    l2a = [json.loads(x) for x in S475.ROWS_F.read_text().splitlines() if x.strip()]
    for x in st:
        if x["value"] != sd[(x["system"], x["cap"])][x["what"]]:
            fails.append(f"strip {x['system']} cap {x['cap']} {x['what']}: drawn {x['value']}, workbook "
                         f"{sd[(x['system'], x['cap'])][x['what']]}")
        R = [y for y in l2a if y["system"] == x["system"] and y["cap"] == x["cap"]]
        flag = "cap_reached" if x["what"] == "cap_reached_pct" else "stopped_by_cap"
        if abs(x["value"] - 100 * sum(y[flag] for y in R) / len(R)) > 0.005 + 1e-9:   # S474 keeps 4-decimal shares
            fails.append(f"strip {x['system']} cap {x['cap']} {x['what']}: drawn {x['value']}, L2 rows give "
                         f"{100 * sum(y[flag] for y in R) / len(R)}")
    for pm_ in (pl["page_mm"], pl["b_summary"]["page_mm_c"]):
        if pm_[1] > S475.FIG_H_MAX_MM + 1e-9:
            fails.append(f"plate {pm_[1]:.1f} mm high, over {S475.FIG_H_MAX_MM} mm")
    t1t = json.loads((Path(r["plate"]["out"]).parent / "T1_L2" / "cap_tables.json").read_text())
    l2 = [json.loads(x) for x in S475.ROWS_F.read_text().splitlines() if x.strip()]
    want_ref = [(c, float(np.median([100 * x["concept_recall_loose"] for x in l2 if x["system"] == "G5"
                                     and x["cap"] == c and x["question_id"] in t1t["complete_questions"]])))
                for c in t1t["caps"]]
    if pl["gemini_ref"] != want_ref:
        fails.append(f"plate b: the Gemini reference {pl['gemini_ref']} is not L2's G5 median on T1's complete "
                     f"questions {want_ref}")
    # D126: the drawn pairing is the covered set, the common-86 reading is kept beside it
    g4h = json.loads((r["g4dir"] / "header.json").read_text())
    if g4h["inputs"].get("covered") != {str(c): n for c, n in COVERED_WANT.items()}:
        fails.append(f"G4 fixture: covered counts {g4h['inputs'].get('covered')}, want {COVERED_WANT}")
    prs = load_rows(r["g4dir"] / "pairs.jsonl")
    both = lambda q: all(q["cells"][c]["pass3"] is not None for c in G4_CONFIGS)   # noqa: E731
    for p in json.loads((r["g4dir"] / "point_tables.json").read_text())["points"]:
        if not p["drawn"]:
            continue
        R = [q for q in prs if q["index"] == p["index"]]
        want_cov = sum(q["covered"] and both(q) for q in R)
        want_86 = sum(q["common"] and both(q) for q in R)
        if sum(q["covered"] for q in R) != COVERED_WANT[p["core_papers"]]:
            fails.append(f"{p['index']}: {sum(q['covered'] for q in R)} covered rows, want "
                         f"{COVERED_WANT[p['core_papers']]}")
        if p["main"]["questions_paired"] != want_cov or p["common86"]["questions_paired"] != want_86:
            fails.append(f"{p['index']}: paired {p['main']['questions_paired']} (want {want_cov} covered), common86 "
                         f"{p['common86']['questions_paired']} (want {want_86})")
        if p["core_papers"] in (5, 10) and not p["main"]["questions_paired"] < p["common86"]["questions_paired"]:
            fails.append(f"{p['index']}: the covered pairing is not smaller than the common 86")
    with tempfile.TemporaryDirectory(prefix="S476_d156_") as d:
        f156 = selftest_d156(Path(d))
    fails += f156
    with tempfile.TemporaryDirectory(prefix="S476_d160_") as d:
        f160 = selftest_d160(Path(d))
    fails += f160
    with tempfile.TemporaryDirectory(prefix="S476_d181_") as d:
        f181 = selftest_d181(Path(d))
    fails += f181
    with tempfile.TemporaryDirectory(prefix="S476_d181plate_") as d:
        f181p = selftest_d181_plate(Path(d))
    fails += f181p
    with tempfile.TemporaryDirectory(prefix="S476_d188_") as d:
        f188 = selftest_d188(Path(d))
    fails += f188
    for f in fails:
        print("SELFTEST FAIL:", f)
    print(f"selftest: {'PASS' if not fails else 'FAIL'}; D156 (anchor on the held reading, judged drawn) "
          f"{'PASS' if not f156 else 'FAIL'}; D160 Q18 checks {'PASS' if not f160 else 'FAIL'}; D186 (4) D181 "
          f"readings {'PASS (passes on the committed folders; 6 altered copies, 4 other refusals and a moved anchor refused)' if not f181 else 'FAIL'}; "
          f"D186 (4) plate wiring {'PASS' if not f181p else 'FAIL'}; D188 b and c on key v2.5 "
          f"{'PASS (wiring, 8 refusals)' if not f188 else 'FAIL'}; a boxes {pl['a_boxes']}; strip bars {len(st)}, hatched "
          f"{sum(1 for x in st if x['hatch_lines'])}; page {pl['page_mm'][1]:.1f} mm; b lines {pl['b_lines']}, medians "
          f"{pl['b_medians']}, references {pl['b_refs']}; T1 k {r['t1']['k']}, rows {r['t1']['rows']}; G4 drawn "
          f"{len(r['g4']['drawn'])}; c cells drawn {pl['c_cells']} of {len(gd)}, empty {len(got_empty)} x 2, framed "
          f"{sum(1 for x in gd if x['framed'])}; plate n "
          f"{r['plate']['n']} of {r['plate']['m']}" + (f"; fixture plate in {r['plate']['out']}" if keep else ""))
    if keep is None:
        tmp.cleanup()
    return 1 if fails else 0


def mutants() -> int:
    def m_flip(root, fx):                         # a correctness flipped across 3
        p = root / "g4_collect.jsonl"
        L = [json.loads(x) for x in p.read_text().splitlines()]
        for x in L:
            if x["config"] == "rlm_10" and x["answer_key"].startswith("exp_v4_s5_n1|") and x["a"]["status"] == "ok":
                c = x["a"]["scores"]["correctness"]
                x["a"]["scores"]["correctness"] = 2 if c >= 3 else 4
                fo = root / "s3" / "out_g4" / "judge" / x["run_id"] / ("judge_" + "passages.jsonl")
                J = [json.loads(y) for y in fo.read_text().splitlines()]
                for y in J:
                    if y["answer_key"] == x["answer_key"]:
                        y["a"] = x["a"]
                fo.write_text("".join(json.dumps(y) + "\n" for y in J))
                break
        p.write_text("".join(json.dumps(x) + "\n" for x in L))

    def m_drop_failure(root, fx):                 # a failure dropped from the inputs
        run = G4_RUN.format(config="rlm_10", index="exp_v4_s5_n0")
        p = root / "g4_inputs" / "runs" / run / "answers.jsonl"
        L = p.read_text().splitlines()
        p.write_text("\n".join(L[1:]) + "\n")
        mp = root / "g4_inputs" / "MANIFEST.sha256"
        mp.write_text(re.sub(r"^\w+  runs/" + re.escape(run) + "/answers.jsonl$", f"{sha256_file(p)}  runs/{run}/"
                             "answers.jsonl", mp.read_text(), flags=re.M))

    def m_g4r38_counted(root, fx):                # a G4R38 key counted as a failure
        fx["g4r38"].write_text("# fixture, emptied\n")
        fx["g4r38_want"] = {"rlm_10": 0, "single_pass": 0}
        fx["g4r38_want_all"] = {c: 0 for c in G4_ALL}

    def m_claimed(root, fx):                      # a unit still claimed
        p = root / "s3" / "out_g4" / "claims.txt"
        p.write_text(p.read_text() + "p1__" + G4_RUN.format(config="rlm_10", index="exp_v4_s5_n1") + "\n")

    def m_walk(root, fx):                         # a missing walk record
        p = root / "t1" / "interleaved_walk.jsonl"
        L = p.read_text().splitlines()
        i = next(i for i, x in enumerate(L) if json.loads(x)["action"] == "begin")
        L.pop(i)
        p.write_text("\n".join(L) + "\n")
        pj = json.loads((root / "t1" / "PULL.json").read_text())
        pj["files"]["interleaved_walk.jsonl"]["sha256"] = sha256_file(p)
        (root / "t1" / "PULL.json").write_text(json.dumps(pj))

    def m_k(root, fx):                            # k miscounted in T1_L2
        pass

    def k_after(root):
        p = root / "T1_L2" / "cap_tables.json"
        t = json.loads(p.read_text())
        t["k"] = t["k"] + 1
        p.write_text(json.dumps(t))
    m_k.after_build = k_after

    def m_cov_ignored(root, fx):                  # D126: the covered set ignored at its source (every common question)
        globals()["covered_set"] = lambda key_questions, core, among: set(among)
    m_cov_ignored.restore = lambda: globals().__setitem__("covered_set", _covered_set)

    def m_cov_flags(root, fx):                    # D126: G4_fig3c's covered flags rewritten to the common 86
        pass

    def cov_flags_after(root):
        g = root / "G4_fig3c"
        rows = load_rows(g / "pairs.jsonl")
        for x in rows:
            x["covered"] = x["common"]
        (g / "pairs.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
        idx = json.loads((g / "header.json").read_text())["inputs"]["indexes"]
        (g / "point_tables.json").write_text(json.dumps(g4_tables(rows, idx), indent=1, sort_keys=True) + "\n")
    m_cov_flags.after_build = cov_flags_after

    def m_pair86(root, fx):                       # D126: the drawn pairing ignores the covered set (the common 86)
        globals()["g4_point"] = lambda rows, which="pass3", drop_failed=False, set_name="covered": _g4_point(
            rows, which, drop_failed, "common" if set_name == "covered" else set_name)
    m_pair86.restore = lambda: globals().__setitem__("g4_point", _g4_point)

    def m_ref_all86(root, fx):                    # B-2: the Gemini reference over all of G5's questions, not T1's
        globals()["gemini_ref"] = lambda l2rows, a_rows, t1caps, complete: _gemini_ref(
            l2rows, a_rows, t1caps, sorted({x["question_id"] for x in l2rows if x["system"] == "G5"}))
    m_ref_all86.restore = lambda: globals().__setitem__("gemini_ref", _gemini_ref)

    def m_red(root, fx):                          # B-2: a pure red reference, outside the lock's palette
        globals()["GEMINI_REF_COLOUR"] = "#FF0000"
    m_red.restore = lambda: globals().__setitem__("GEMINI_REF_COLOUR", _ref_colour)

    def m_box_mean(root, fx):                     # A-1: the box's median written as the mean
        def boxes(a_rows, caps):
            out = _a_with_boxes(a_rows, caps)
            for x in out:
                if x["row"] == "cap":
                    x["median_pct"] = x["mean_pct"]
            return out
        globals()["a_with_boxes"] = boxes
    m_box_mean.restore = lambda: globals().__setitem__("a_with_boxes", _a_with_boxes)

    def m_grid_off(root, fx):                     # D150: RLM-10's grid cell off the two-strategy reading
        def gp(rows, strat, which):
            e = _grid_point(rows, strat, which)
            if strat == "rlm_10" and e.get("n_paired"):
                e["d_pp"] += 1e-6
            return e
        globals()["grid_point"] = gp
    m_grid_off.restore = lambda: globals().__setitem__("grid_point", _grid_point)

    def m_incomplete(root, fx):                   # D150: a unit not judged in full drawn as complete
        def gt(cells, indexes, units):
            return _grid_tables(cells, indexes, {k: {**v, "complete": True} for k, v in units.items()})
        globals()["grid_tables"] = gt
    m_incomplete.restore = lambda: globals().__setitem__("grid_tables", _grid_tables)

    _covered_set, _g4_point = covered_set, g4_point
    _grid_point, _grid_tables = grid_point, grid_tables
    _gemini_ref, _ref_colour, _a_with_boxes = gemini_ref, GEMINI_REF_COLOUR, a_with_boxes
    cases = [("the covered set ignored (D126)", m_cov_ignored, None),
             ("covered flags rewritten to the common 86 (D126)", m_cov_flags, None),
             ("the pairing drawn on the common 86 (D126)", m_pair86, None), ("correctness flipped across 3", m_flip, None), ("a failure dropped", m_drop_failure, None),
             ("a G4R38 key counted", m_g4r38_counted, None), ("a unit still claimed", m_claimed, None),
             ("a missing walk record", m_walk, None), ("k miscounted", m_k, None),
             ("a drawn value shifted", None, "shift_drawn"), ("a ninth printed number", None, "ninth_number"),
             ("a grid number of c drawn off its cell (D150)", None, "c_off"),
             ("a frame flipped on a cell of c (D150)", None, "c_frame_wrong"),
             ("the score-4 block fed score-3 values (D150)", None, "c_s4_from_s3"),
             ("RLM-10's grid cell off the two-strategy reading (D150)", m_grid_off, None),
             ("an incomplete unit drawn as complete (D150)", m_incomplete, None),
             ("a box of a drawn off its quartile (A-1)", None, "box_off"),
             ("the Gemini reference of b drawn off its median (B-2)", None, "gemref_off"),
             ("the Gemini reference over all of G5's questions (B-2)", m_ref_all86, None),
             ("the Gemini reference in a pure red outside the lock (B-2)", m_red, None),
             ("a's box median written as the mean (A-1)", m_box_mean, None),
             ("b's question lines in the model colours (follow-up, 26 October)", None, "b_model_colours"),
             ("b's caps on a log axis (follow-up, 26 October)", None, "b_log_x"),
             ("a's words key put back on the plate (D147)", None, "a_words_key"),
             ("the strip's cut-off bars drawn plain (D149)", None, "strip_cutoff_plain"),
             ("the strip reading 'reached' into the cut-off bars (D149)", None, "strip_reached_as_cutoff"),
             ("the strip's two shares swapped in the data workbook (D149)", None, "strip_rows_swapped")]
    with tempfile.TemporaryDirectory(prefix="S476_base_") as d:
        base = _run_fixture(Path(d))
    key = lambda r: (r["plate"]["n"], r["c"], r["plate"]["b_means"], r["plate"]["gemini_ref"],   # noqa: E731
                     r["plate"]["a_medians"], r["plate"]["strip"], r["plate"]["grid"])
    caught = 0
    for name, mut, pm in cases:
        with tempfile.TemporaryDirectory(prefix="S476_mut_") as d:
            try:
                r = _run_fixture(Path(d), mut, pm)
                ok = key(r) != key(base)
                how = "numbers changed" if ok else "NOT CAUGHT: same numbers"
            except Refused as e:
                ok, how = True, f"refused ({str(e)[:90]})"
            except SystemExit as e:
                ok, how = True, f"stopped ({str(e)[:90]})"
            finally:
                if mut is not None and getattr(mut, "restore", None):
                    mut.restore()
        caught += ok
        print(f"  mutant {name}: {'caught' if ok else 'MISSED'}, {how}")
    # D186 (4): the plate's D181 wiring, against the fixture drawn with a on L2_d135_d181 (F4 of the 31 October review)
    cases181 = [("a draws the loose reading although D181 was read and checked (D186 (4))", "a_loose_with_d181"),
                ("b's gemini-3-flash-preview reference read from a's D181 rows (D186 (4))", "gref_from_d181")]
    with tempfile.TemporaryDirectory(prefix="S476_base181_") as d:
        base181 = _run_fixture(Path(d), d181=True)
    for name, pm in cases181:
        with tempfile.TemporaryDirectory(prefix="S476_mut181_") as d:
            try:
                r = _run_fixture(Path(d), None, pm, d181=True)
                ok = key(r) != key(base181)
                how = "numbers changed" if ok else "NOT CAUGHT: same numbers"
            except Refused as e:
                ok, how = True, f"refused ({str(e)[:90]})"
        caught += ok
        print(f"  mutant {name}: {'caught' if ok else 'MISSED'}, {how}")
    # D188: b and c on key v2.5, against the fixture drawn with b on fixture_t1_d181 and c on fixture_g4_d185
    cases188 = [("b draws T1's loose rows although T1_L2_d181 was read and checked (D188)", "b_loose_with_d181"),
                ("b on D181 with its gemini-3-flash-preview reference on the loose rows (D188)", "gref_from_loose"),
                ("c draws G4_fig3c although G4_fig3c_d185 was read and checked (D188)", "c_v24_with_d185")]
    with tempfile.TemporaryDirectory(prefix="S476_base188_") as d:
        base188 = _run_fixture(Path(d), d181=True, d188={})
    for name, pm in cases188:
        with tempfile.TemporaryDirectory(prefix="S476_mut188_") as d:
            try:
                r = _run_fixture(Path(d), None, pm, d181=True, d188={})
                ok = key(r) != key(base188)
                how = "numbers changed" if ok else "NOT CAUGHT: same numbers"
            except Refused as e:
                ok, how = True, f"refused ({str(e)[:90]})"
        caught += ok
        print(f"  mutant {name}: {'caught' if ok else 'MISSED'}, {how}")
    n_all = len(cases) + len(cases181) + len(cases188)
    print(f"mutants: {caught} of {n_all} caught")
    return 0 if caught == n_all else 1


# ---------------------------------------------------------------------------------------------------------------
def rebuild(out: Path | None = None) -> dict:
    """D155's one command: L2 (S474 --frozen), T1_L2 and G4_fig3c from the frozen copy, then the plate; under out
    when given (the committed files untouched), else in place."""
    if out is not None:
        out = out.expanduser().resolve()
        if out.exists() and any(out.iterdir()):
            raise Refused(f"{out} exists and is not empty: rebuild into a new folder")
        dirs = {"L2": out / "L2", "T1_L2": out / "T1_L2", "G4_fig3c": out / "G4_fig3c", "plate": out / OUT.name,
                "L2_d135": out / "L2_d135"}
    else:
        dirs = {"L2": L2, "T1_L2": T1_L2, "G4_fig3c": G4_FIG3C, "plate": OUT, "L2_d135": L2_D135}
    rc = S474.main(["--frozen", "--outdir", str(dirs["L2"])])
    if rc:
        raise Refused(f"S474 --frozen exit {rc}")
    # D160 Q23: L2 after the D135 reruns, drawn by a, when G6's records after them are frozen
    l2_drawn = None
    if G6_D135.exists():
        r0 = l2_d135_build(dirs["L2_d135"], dirs["L2"], committed_header=L2_D135 / "header.json")
        print(f"L2_d135: {r0['rows']} rows, G6 {r0['g6_status']}; held to L2: {r0['held']}")
        l2_drawn = dirs["L2_d135"]
    elif L2_D135.exists():
        raise Refused(f"{rel(L2_D135)} exists but {rel(G6_D135)} does not: the drawn reading has no frozen input")
    else:
        print(f"L2_d135: {rel(G6_D135)} not frozen yet (freeze_g6_d135.py); a draws G6 before the D135 reruns")
    copy = frozen_copy()
    r1 = t1_build(copy, dirs["T1_L2"], committed_header=T1_L2 / "header.json")
    print(f"T1: {r1['rows']} answers, k {r1['k']}, gate {r1['gate']}; frozen inputs: {r1['frozen_check']}")
    r2 = g4_build(copy, dirs["G4_fig3c"], committed_header=G4_FIG3C / "header.json")
    print(f"G4c: {r2['rows']} rows, grid cells complete {r2['grid_cells_complete']} of 60, RLM-10 reproduced "
          f"({r2['gate']['compared']} values); frozen inputs: {r2['frozen_check']}")
    print(f"G4c D160 Q18: {d160_summary(r2['checks_d160'])}")
    r3 = plate(out=dirs["plate"], t1dir=dirs["T1_L2"], g4dir=dirs["G4_fig3c"], l2dir=dirs["L2"],
               l2_drawn_dir=l2_drawn)
    return {"dirs": {k: str(v) for k, v in dirs.items()}, "t1": r1, "g4c": r2, "plate_n": r3["n"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rebuild").add_argument("--out", type=Path, default=None)
    sub.add_parser("pull").add_argument("--to", required=True, type=Path)
    sub.add_parser("t1").add_argument("--copy", required=True, type=Path)
    sub.add_parser("g4c").add_argument("--copy", required=True, type=Path)
    sub.add_parser("plate")
    sub.add_parser("selftest").add_argument("--keep", type=Path, default=None)
    sub.add_parser("mutants")
    sub.add_parser("anchor")
    sub.add_parser("anchor-pre-d156")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "pull":
            return pull(a.to)
        if a.cmd == "rebuild":
            r = rebuild(a.out)
            print(f"rebuilt {MAIN_LABEL} and {SI_LABEL} from the frozen inputs into {r['dirs']['plate']} and its sibling "
                  f"{MAIN_OUT.name}")
            return 0
        if a.cmd == "t1":
            r = t1_build(a.copy.expanduser().resolve(), T1_L2)
            print(f"T1: gate S383 {r['gate']}; {r['rows']} answers scored {r['per_model']}, {r['failed']} failed; "
                  f"k = {r['k']} questions complete for the four models; wrote {rel(T1_L2)}")
            return 0
        if a.cmd == "g4c":
            r = g4_build(a.copy.expanduser().resolve(), G4_FIG3C)
            print(f"G4c: {r['rows']} question rows; {r['judged_rows']} judged rows of rlm_10 and single pass; units "
                  f"complete {len(r['units_complete'])} of 24 (rlm_10, single pass), {len(r['units6_complete'])} of 72 "
                  f"(six strategies); grid cells complete {r['grid_cells_complete']} of 60; RLM-10 reproduced "
                  f"({r['gate']['compared']} values, anchor {r['gate']['anchor']}); wrote {rel(G4_FIG3C)}")
            return 0
        if a.cmd == "anchor":
            return write_anchor()
        if a.cmd == "anchor-pre-d156":
            return write_anchor_pre_d156()
        if a.cmd == "plate":
            plate(l2_drawn_dir=L2_D135 if L2_D135.exists() else None)
            return 0
        if a.cmd == "selftest":
            return selftest(a.keep)
        if a.cmd == "mutants":
            return mutants()
    except Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    except S474.GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
