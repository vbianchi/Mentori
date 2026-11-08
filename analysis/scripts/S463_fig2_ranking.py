#!/usr/bin/env python3
"""S463 - Figure 3 and Supplementary Figure 16: the judge's scores of G1, read from S3's collect output, as pass rates,
refusals, failed answers and Rule 4's flips by the rules of experiments/LIST.md, with G1's model calls and times, drawn as
Figure 3's six panels since D200 (1 November): a pass tiles and rates, b refusal tiles, c each strategy against single
pass at score 4, d cost scatters, e the T2 panel (S518's committed verdicts, D195; read_s518), f corpus size
(findings/recompute/fig3e/, S522; D218 (3) swapped e and f, 3 November, so the text names them in order); and Supplementary Figure 16, the same tiles and flips at score 3. The file keeps its name:
S472, S473, S476, S465, S484, S486 and S514 import it.

THE PLATE SINCE D200 (fig3.md, the sheets of each panel in sheets()). Old panels a, d, e and c became 3a, 3b, 3c and 3d;
old panel b's numbers stay as rows of sheet Fig. 3a, 'concept recall (not drawn)'. Sheet Fig. 3a adds, beside the six
strategies, G2 (matched budget) and G6's cap 10 (Zhang RLM-10), read by read_extra through judge_rows_v25 from
findings/recompute/fig3_s6_inputs/ (S528), and each row's rate on the one-paper and many-paper questions
(S511.questions()). G2 and G6 stand outside the six: CONFIGS stays six, so Rule 6, compute() and every importer read
what they read before (LIST.md:310-311). What follows up to JUDGE ROWS is the record of how the plate got here.

WHY. D94 (Valerio, 18 October: "faster to results to look at"): S3 judges the plain call (a) on draw 1 of all six G1
strategies first (phase 1, 810 answers), so Figure 3's first ranking can be read minutes after phase 1 ends. D82: a
panel is drawn as soon as its data exist, by a committed script, stamped with how much data it holds; the final panel
is the same script run again (here with --draws 1,2,3). D84: exploratory phase, no new analysis rule; every statistic
below is a rule LIST.md already states (approved in D78 Q130), cited where it is computed. The panels are the ones the
figure story review lists for the ranking (findings/audits/FIGURE_STORY_REVIEW_2026-10-18.md, "The panel list it
should have") and A1's layout (19 October): a, the pass rate at thresholds 3 and 4 in one forest; c, model calls per
answer against the pass rate at 4 (Q2: calls, not time; times in the legend and Source Data); d, refusal on the 39
not-answerable questions (the 10 false-premise questions as counts in the legend and Source Data); e, Rule 4 for each
strategy against single pass with the noise baseline. Panels b and f are empty frames until their data exist; panel
b is drawn since 22 October from plan row L3's concept recall when rank is given --concept-recall, each row first
scored again from the record S3 judged (read_concept_recall); since D188 the values drawn are D181's reading on key
v2.5 (PANEL B ON KEY v2.5 below).
Since 23 October the plate draws the panels Valerio chose that day (experiments/README.md D127 to D131; draw()): a, the
86 answerable questions by strategy as tiles coloured by draws passed, per threshold, with each rate and interval in a
margin; b, a box per strategy over the questions' concept recall with the questions as dots; c, six small scatters of
the questions' model calls against their pass share at score 4, with each strategy's mean as a cross; d, as a on the
39 not-answerable questions by draws refused; e, a butterfly per threshold of harmed and helped against single pass
with the pairings and the reruns as dots; f, an empty frame. Valerio's plate notes of 2 November, on today's letters: 3a
and 3b's margin axes run 50 to 100 (A_VIEW, margin_view: a value below 50 stands left of the axis line on the same scale,
nothing is clipped); 3c draws its bars and the n = 9 pairings only, the lock's minimum, and S5b keeps the reruns; 3d prints
only each strategy's name, the multiples stay in sheet 3d; 3e's key (3f since D218) is the colour bar alone. D215 and D216 (Valerio, 3
November): 3a loses its three margin columns (All, One paper, Many papers) and its tiles take their width; 3d draws, per
strategy, the pass rate of All (black circle), One paper (blue square) and Many papers (orange diamond) at the mean model
calls of their questions, filled at score 4 and open at 3, with no interval on any mark (they stay in sheet 3d, rows
GROUP_D_KIND); the matched-budget cross in vermilion, as the draft he kept, with no bar; the key one line, no entry for
the grey dots. D218 (Valerio, 3 November): 3a gains a clock-time margin beside its eight rows (clock_margin,
draw_clock_margin): per answerable question its clock time per answer less the wait for the local server, the mean over
its draws, as a grey dot jittered within the row, the mean over the questions as a black dot, printed in seconds;
held first to Supplementary Figure 17c's per-question means (hold_margin_to_supp6); and panels e and f swap, so 3e is
the T2 frame and 3f corpus size (sheet Fig. 3f). check_drawn reads every drawn mark back from its artist, positions included, and holds it to the Source
Data workbook before the plate is saved.

A NEW SCRIPT BESIDE S457, NOT A MODE OF IT: S457 reads the generation records (mirrored from the Studio, with G6 and
S455's files) and draws the judge-free plate; this reads the judge's rows and must run without that mirror. S457's
figure step deletes every plate file of its own folder, and S448 R1 wants one plate per folder, so this plate has its
own folder, findings/figures_provisional/fig3_strategies/. It draws through S457's code: S457.plate_rc() and
S457.finish_plate() (the lock's type, lines, text checks, the PDF, the SVG and the PNG rasterised from the PDF), and
S457's marks (grey dots, blue mean and interval), half_up, write_source_data.

ONE COMMAND (D155), from the repository root: the committed plate, rebuilt from the frozen inputs only:

  uv run --frozen python scripts/S463_fig2_ranking.py rebuild [--out <dir>]

It writes every file of findings/figures_provisional/fig3_strategies/ (or of --out) byte-equal to the committed one
(26 October: PDF, SVG, PNG, workbook, caption, legend, claims.md, ranking.json, ranking_report.md, figure3_numbers.json
and figure3_provenance.json; run twice, the same bytes). The frozen inputs and how each is checked: rebuild() below.
The tars come from the folder in env FROZEN_TARS (default ~/Mentori_scratch_keep/frozen_2026-10-26; the paper's
Zenodo deposit holds them), extracted once into findings/recompute/frozen_inputs/extracted/ (gitignored). Every
command re-executes itself under PYTHONHASHSEED=0 (fig_repro.pin_hash_seed: the PDF's font subsets depend on it).

COMMANDS, from the repository root (uv run only; no model call anywhere):

  rebuild  uv run --frozen python scripts/S463_fig2_ranking.py rebuild [--out <dir>]
           rank --draws 1,2,3 --concept-recall on the frozen copies (D155), each checked against the sha256 the
           committed figure3_provenance.json records before anything is read further; nothing is pulled.
  pull     uv run --frozen python scripts/S463_fig2_ranking.py pull --to <new dir>
           Read-only copies from the Studio (nothing written there): from the S3 clone's
           out/ and out_g1r15/, each judge/<run>/ folder's judge_passages.jsonl, judge_passages_headers.jsonl and
           judge_passages_recheck.jsonl, and each out's start_*.json; ~/s3_inputs/g1r15's answers files with its
           MANIFEST.sha256 (each copy checked against it). One ssh session whose script comes on stdin (PULL_SH)
           writes them as one tar stream, extracted here with tarfile's data filter, each file's mtime kept: no
           file name, path or port is on a command line on either machine, so no K1 or S3 guard that reads command
           lines is tripped by the copy (22 Oct; the first pulls used rsync, whose arguments name the judge files).
           No git runs on the Studio (23 October guards): the S3 clone's HEAD is read from its .git files (A8).
           A file still being appended is cut after its last whole line (counted in PULL.json). Then s3_guard.py collect on the copies, as the S3 README says (--out
           <dir>/out --replace <dir>/out_g1r15 --set G1 --dest <dir>/g1_collect.jsonl), and prints the rank command.
  rank     uv run --frozen python scripts/S463_fig2_ranking.py rank --collect <dir>/g1_collect.jsonl --draws 1 \
               --answers <K1 runs> --answers <dir>/g1r15_inputs/runs [--out <dir>] [--no-plate] \
               [--concept-recall findings/recompute/L3/concept_recall.jsonl] \
               [--concept-recall-d181 findings/recompute/L3_d181]
           Reads, checks, computes, and writes into --out (default findings/figures_provisional/fig3_strategies/):
           the plate "Figure 3 (provisional, <n> of 2430).{pdf,svg,png}", "Source Data Fig. 3 (...).xlsx" and its
           caption, figure3_numbers.json, figure3_provenance.json, legend_draft.md (what S448 reads), ranking.json
           (every number with the answer keys it is counted from), ranking_report.md (one page, plain English) and
           claims.md (D82's claims list), and beside --out, in supp_fig16_score3/, Supplementary Figure 16's plate, data
           workbook, numbers, provenance and legend. --extra <folder> (fig3_s6_inputs) and --fig3e <folder> are needed for a
           plate. Every file is first written into a staging folder beside --out; only when
           all are written are the earlier S463 files of --out removed and the new ones moved in, so a refusal or a
           plate that fails to draw leaves --out as it was (exit 1, nothing written). With --no-plate only
           ranking.json, ranking_report.md and claims.md are written, and an earlier plate in --out is removed with
           the rest, so no file of an earlier reading stays beside them.
           --s6 <folder>: where out_s6_g1 and out_s6_g1r15 are (D186 (3), JUDGE ROWS below). --answers (K1's runs, then G1R15's) is
           required: the stop reasons and the verifier status come from the records judged.
  fixture  uv run --frozen python scripts/S463_fig2_ranking.py fixture --to <new dir> [--draws 1,2,3]
           A fake S3 output of the real shape (judge rows, headers, rechecks and start files as judge_passages.py and
           run_s3.sh write them, in out/ and out_g1r15/), the generation records it judged with their MANIFEST.sha256,
           and the collect output made by s3_guard.py's own collect. Not data: a FIXTURE.txt beside it makes rank
           refuse to write it into the repository's figure folder.
  selftest uv run --frozen python scripts/S463_fig2_ranking.py selftest
           Offline: the method against known values (S04a's P values, full enumeration, an interval computed apart),
           Rule 6 and Rule 11 on built cases (a separation in the wrong direction, a shared first place, a zero and
           a negative difference, equal rates whose float means differ), the fixture's numbers against values worked
           by hand or computed apart, the plate drawn from the fixture checked by S448 (must pass), the staging
           (a refusal and a failed plate leave --out as it was; --no-plate leaves no earlier file), and input mutants
           that must each be refused with their own message. Last line "selftest: <k> of <n> checks pass".
  mutants  uv run --frozen python scripts/S463_fig2_ranking.py mutants [--only <words>] [--shard <k>/<n>]
           Each code mutant of MUTANTS (one line of this file changed) runs the whole selftest and must make a check
           fail (a FAIL line), not only crash. --only keeps the mutants whose name holds those words, --shard the k-th of n
           (from 1), so the list can run in parts. Last line "mutants: <k> of <n> killed by a failing check".

JUDGE ROWS, KEY v2.4 OR v2.5 (D186 (3), Valerio, 31 October; the default since): after read_collect's checks below
have passed on the v2.4 collect, judge_rows() reads every answer through scripts/judge_rows_v25.py, as Supplementary Figure 6 does:
its key v2.5 row (S512 on the 132 changed questions, out_s6_g1 with out_s6_g1r15 as --replace, under --s6 or beside
the outs collect read) where one exists, else its key v2.4 row. Without S6 outs every answer is read from key v2.4
and ranking.json, ranking_report.md and figure3_provenance.json record "awaiting S6" with the count (the answers of
the 60 changed questions G1 asks, 1,080 of 2,430 over three draws). The human-rating panels are not drawn here (D168).

OLD PANEL B ON KEY v2.5 (D188, Valerio, 31 October: "every figure using v2.4 needs to move to v2.5"): old panel b, now
rows of sheet Fig. 3a and not drawn, carries D181's
reading, findings/recompute/L3_d181 (S471 --d181: S505's loose matcher with the question rule, Q-need, reading (b), on
key v2.5), the folder Figure 5 reads since D186 (4). Reproduce first (README.md:75-79): --concept-recall's L3 rows
(D12's loose matcher on key v2.4) are read and scored again from the records as before (read_concept_recall), and on
the committed L3 rows over draws 1 to 3 check_cr_anchor holds their panel b to the committed v2.4 panel b
(CR_ANCHOR_V24: mean, interval, exact value and failed answers of each strategy). Only then is L3_d181 read
(read_concept_recall_d181, the checks of S497.read_l3_d181: both files pinned, the header D181's final reading on key
v2.5 of L3's answer copy, its rows L3's answers one for one, the loose base equal to L3's loose value on the questions
whose concepts v2.5 left unchanged) and drawn: per answer found over the concepts counted (a concept made only of
words of its question is not counted), D12's exact substring test on the v2.5 concepts beside it. ranking.json keeps
the v2.4 anchor's six strategy values under concept_recall.anchor_v24_loose.

WHAT RANK REFUSES (each a missing or doubtful row; the analysis never guesses):
  - experiments/LOCK.toml not at D88's sha256 d66daa28 (the judge and its digest are read from it);
  - no sidecar <collect>.json, or one whose rows, run_sha256 or set (G1) differ from the file;
  - rows under more than one run_sha256 (another lock, code or judge setting); a row under a lock_sha256 other than
    d66daa28 (D88; run_s3.sh:89, 163); a row twice;
  - a row outside G1 (run id, configuration, answer key, a question outside the D5 key); a row whose judge prompt
    (answerable_prompt) disagrees with Rule 8's group from the D5 key (LIST.md:332-349);
  - a missing row: every (strategy, question, draw) of the six strategies x 135 questions x the draws read must be
    there (phase 1 incomplete is a refusal, never a partial ranking);
  - an (a) status that is neither ok, no_answer nor a judge-call failure (error, stalled, length, cancelled,
    unparseable; judge_passages.py STATUS);
  - G1's reruns of 18 October (D93 Q-c) not taken from their own pass: every rerun key of the draws read
    (findings/recompute/G1_runs/rerun_d89.sh KEYS, as snap_s3_inputs.sh:59 reads them) must be in the collect file
    with the item_sha256 and run_sha256 of its latest row in the replace out (default <first out's folder>/out_g1r15),
    the replace out must hold no other answer, and the sidecar's replaced + added counts must equal its rows taken
    from that out;
  - a judging unit that did not end as run_s3.sh accepts one (check_units): an out with no start_*.json or one under
    another lock; a run folder whose rows have no header line for their run_sha256, or a header naming another judge,
    digest or lock; a recheck line that is not equal (the recheck failed), or fewer recheck lines than the unit
    judges again (the unit is still in its recheck, or stopped in it);
  - --answers missing, an answers folder without MANIFEST.sha256 or a file that is not its line there, and a
    generation record that disagrees with the judge row (the judge wrote no_answer exactly when the record's status
    is not ok, records.py:153-156), so the stop reasons counted are those of the answers judged.

HOW EACH NUMBER IS MADE (LIST.md rules; pass on threshold t = judge score t or more):
  groups     Rule 8: the D5 key's answer type (experiments.runner.experiment.questions(), records.GROUP_OF_TYPE):
             86 answerable, 10 false premise, 39 not answerable.
  outcomes   Rule 10: an answer with no text or a generation error (judge status no_answer) is a failure of the
             system under test: it stays in every denominator and counts as a fail (and as not refused). A judge call
             that gave no score (error, stalled, length, cancelled, unparseable, or no score for the dimension read) is
             a missing measurement: left out and counted, never 0. Cut answers (stop reason max_turns_partial, length)
             carry text and are scored as written. An answer whose Gemini calls hold a block or a recitation stop is
             counted as "stopped by Google" (failed when it has no text; scored as written and counted when it kept
             its text, D90 Q1); one holding another returned status (empty, malformed, D92 Q188's reasons) is
             counted with that status (D90 Q2).
  pass rate  Rule 2: per question, its pass share p over the draws read (the draws with a measurement); the rate is the
             mean of p over the questions of the group that have one, kept exact (a Fraction), so ranks and ties
             compare exact values; Rule 5: at thresholds 4 (the pass rate, D154) and 3 (the relaxed threshold).
  interval   Rule 2: 95% percentile interval over 10,000 resamples of the group's questions (sorted ids), S407's
             convention (scripts/S407_strategy_contrasts_v24.py:190-191, 246-257: numpy default_rng(20261013)
             .integers(0, n, size=(10000, n)) counted per question; a resample's rate is the sum of p over the
             questions drawn, each as often as drawn, over the number of them with a p; percentiles 2.5 and 97.5,
             linear interpolation). With every question measured this is the mean of p over the questions drawn.
  per draw   Rule 2: each draw's pass rate beside the pooled one (Source Data, not drawn), over the questions
             measured then.
  pairs      Rule 3: d = the mean over the questions both strategies have a p for of (p of A minus p of B), exact,
             with the Rule 2 interval (the same resamples); P = the exact two-sided sign-flip test on those
             per-question differences, every sign pattern enumerated by convolution (on one draw it is the exact
             McNemar test: it reproduces S04a's 0.0192108154296875 for 15 against 4 and 0.007537841796875 for 15
             against 3 before any number is written). All 15 pairs are printed with unadjusted P values and intervals,
             as Rule 12 says such a table is printed; no Holm (Rule 12 states Holm for Figure 4's family only). No
             sentence of the legend is taken from that table (LIST.md:440-441).
  highest    Rule 6: a strategy is called highest (lowest) of the six only if it alone is first (last) by mean and
             Rule 3's test separates it from every other at P < 0.05 in its favour; else the text names those it
             cannot be told apart from. Stated at threshold 4 (LIST.md Rule 6, D154), given at 3 as well (Rule 5, Rule 11).
  verdicts   Rule 11, at each threshold, for the letter's Figure 2 claims on panels a and d as S393 lists them (E1:
             RLM-10 highest, verified pass lowest; E4: RLM-10 above verified pass; E5: RLM-10 above single pass; E6:
             RLM-10 refuses more than multi-hop, on refusal at score 3 only) and Rule 11's named comparison verified
             pass below single pass (R11): holds, weakens or reverses (verdict()). On draw 1 only, every verdict is
             provisional.
  refusal    Rule 9: on the 39, refused = the judge's refusal_accuracy 3 or more under its decline prompt (one level:
             Rule 5's second threshold is for pass-based statistics); the rate is the mean over the 39 of each
             question's refused share, with the Rule 2 interval; a zero is written with its one-sided 95% upper bound
             over questions, 1 - 0.05^(1/n) (0 of 39: 7.4%), drawn dashed from 0 to it; a 100% (every question
             refused on every draw) with its one-sided 95% lower bound, 0.05^(1/n) (39 of 39: 92.6%), drawn dashed
             from 100 back to it (O2, 24 October, the mirror; each dashed bar starts at its dot). Pairs as Rule 3
             (Rule 9: set-ups are compared by Rule 3).
  false prem Rule 9: passed = correctness t or more against the refutation, at 3 and 4 (pass-based, Rule 5); per
             strategy k of the answers, each draw's k of 10 and the passes per question; no interval, no test, no
             ranking.
  cost       panel d (cost_summary): per answer the entries of generation.calls, generation.latency_s (and the
             wait for the local server), generation.tokens_used and the sum of the calls' wall_s (model-call time), read
             by S457.exp01_row; per question the mean over its draws, then the mean over the 86 answerable questions
             (plotted) and over all 135, with the Rule 2 interval. Above each scatter, each strategy over single pass on
             the 86: model-call time as a ratio of means; tokens as a ratio of means and a ratio of medians.
  flips      panel c at score 4 and Supplementary Figure 16b at score 3 (flips, self_flips), Rule 4: every single-pass draw of a question against every draw of the
             strategy; harmed = sum s(1 - v), helped = sum (1 - s)v (the means over the pairings of the questions
             changed), both denominators with the Rule 2 interval, Rule 3's P; each draw's 2 x 2 table; the noise
             baseline (Rule 4 (b)) per strategy, and per ordered pair of distinct draws the questions passing on one
             and failing on the other (S5b's grey dots; single pass's fewest to most is its band; rows of sheet 3c, not
             drawn there), and per pairing of a single-pass draw with a strategy draw the questions harmed and helped
             (the black dots).
  concept   sheet Fig. 3a's 'concept recall (not drawn)' rows, old panel b (read_concept_recall, compute_cr), --concept-recall: L3's rows (S471), refused unless S471's gate
             reproduces S432's 107 values, every row of the draws read is there once in its Rule 8 group and is the
             answer S3 judged (answer sha256 and status of the record read here), and S471.score on that record gives
             the row again. Per answer found / concepts (exact Fraction; an empty answer 0, Rule 10); per question the
             mean over the draws; the mean over the 86 answerable questions with the Rule 2 interval; each draw's
             mean; Rule 3 on per-question means for all 15 pairs and Rule 6 (LIST.md Rule 6, continuous signal). The
             loose value is drawn; the exact-substring value is beside it in the Source Data and the report (D12).
  failures   Rule 10: per strategy, every outcome above with its answer keys (ranking.json, Source Data).
             Sensitivity: every pass rate, P value and verdict also with the failures left out, and each verdict that
             differs is named.
  verifier   Rule 4, Q78 (LIST.md:286-289): chunk_verifier.verifier_status_report over the verified-pass records
             given; the answers of the draws read whose verifier status is not ok are counted by status, and every
             reading is given again without them (verified pass's rates and the verdicts).
  claims     D82: claims.md, every number the Main Text, the Figure 2 legend, Supplementary Tables 2 and 8 and the
             letter give for panels a, c, d and e (CLAIM_ROWS), with the provisional value, a status and whether the words
             are still in the document's accepted text. A printed pass rate used score 3: its row's status compares the
             score-3 value, and the row gives the score-4 value (D154's pass rate) beside it (D160 Q11).
  panel f    S522 (findings/recompute/fig3e/): read, not computed here (3e before D218 (3)).
  panel e    The T2 panel (3f before D218 (3)): S518's committed verdicts (findings/recompute/S518_split_confirmation/
             <source>.json, D195), read by read_s518 and not computed here: per source, RLM-10 minus single pass at
             score 4 on the one-paper and the many-paper questions (D_one, D_many) and I = D_many - D_one, each with
             the interval S518 stored, and S518's reading of I (kept in the workbook, not drawn: Valerio, 4 November).
             Beside them, the reference row (D235 Q4): S518's gemini-3-flash-preview.json, Gemini 3 Flash judged on
             key v2.5, held to D235 and its values to their intervals. D289 (Valerio, 7 Nov): the plate draws I alone,
             on "Many-paper gain minus one-paper gain" at the panel's full width, each value printed beside its row;
             no key and no group heads; rows Flash with the main judge, Flash with the second judge, gemma3:27b,
             qwen3-coder:30b, then after a gap claude-haiku-4-5 and gemini-2.5-pro. D_one and D_many stay in the
             workbook, not drawn. No T2 judge row is opened (the blind rule's check).
             panel_f_judge_codes, its name kept for S495, is the rule a reader of T2's judge rows applies to G1's and T2's run_sha256 (D160 (5)):
             one judge code, or G1's 38ae79ab beside T2's 11e51fde only with S495's passed verdict.json, and only
             when that verdict matches its row file (D161 (9)): its rows_sha256 is the sha256 of online/rows.jsonl,
             the rows are sample.jsonl's answers, and its counts are the rows' counts.
  reproduce  Before anything is written: the sign-flip test on S04a's two contingency tables
             (findings/recompute/S04a_flip_stats.json) must give its stored exact P values, and the resample counts
             must equal those of S457's boot_matrix() (tracked) and of S407's resample_counts() when S407 (committed
             since f5470b4c) imports, so the method is the one Rule 2 names; S457.s77_values() must give the letter's cost numbers
             (5.87 and 1.00 calls, 82.4 and 10.4 s, six and eight times), which claims.md sets against G1's records.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import types
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import S457_fig2_panels as S457  # noqa: E402  (the plate's drawing code, FIGURE_LOCK's values)
import S511_g2_matched_budget as S511  # noqa: E402  (S511.questions(): one-paper and many-paper questions)
import fig_repro as FR  # noqa: E402  (D155: frozen inputs, deterministic files)
import figure_names as fn  # noqa: E402  (one spelling of every printed name)
import house_style as hs  # noqa: E402  (one drawing style)
import judge_rows_v25 as JR  # noqa: E402  (D186 (3): the key v2.5 judge row where one exists, else key v2.4's)

# Panel d and the claims read G1's records and the letter's S77 numbers through these three S457 functions, which
# S457 gained after its commit of 19 October (its working-tree edits, not yet committed when A1 was built): say so
# plainly rather than fail on an attribute. The provenance file records the sha256 of the S457 that drew the plate.
_S457_NEEDS = [n for n in ("exp01_row", "s77_values", "printed_as") if not hasattr(S457, n)]
if _S457_NEEDS:
    raise SystemExit(f"S463 needs S457.{', S457.'.join(_S457_NEEDS)}: this S457 is older than the A1 plate (its "
                     f"edits after the 19 October commit carry them)")

OUT = ROOT / "findings" / "figures_provisional" / "fig3_strategies"
OUT_S5_NAME = "supp_fig16_score3"                      # beside --out (fig3.md section 6)
OUT_S5 = OUT.parent / OUT_S5_NAME
FIG3_S6 = ROOT / "findings" / "recompute" / "fig3_s6_inputs"   # S528: S6G1, S6G2, S6G6, G2, G6
FIG3E = ROOT / "findings" / "recompute" / "fig3e"     # S522: Figure 3f's rows (3e before D218 (3); the name kept)
S518_DIR = ROOT / "findings" / "recompute" / "S518_split_confirmation"   # D195: Figure 3e's verdicts, one file per source
S511_RESULTS = ROOT / "findings" / "recompute" / "S511_g2_budget" / "results.json"
# D231, D306: the person's refusal check (D223, D227), counts only, as S607 wrote them; Fig. 3b's diamonds
S607_SUMMARY = ROOT / "findings" / "recompute" / "S607_refusal_person_check" / "summary.json"
S607_NAMES = {"single_pass": "Single pass", "rlm_10": "RLM-10"}   # S607's strategy names, in plate order
PERSON_KIND = "person check, draw 1 (diamond)"
S3_DIR = ROOT / "findings" / "recompute" / "S3_runs"
GUARD = S3_DIR / "s3_guard.py"
RERUN_SH = ROOT / "findings" / "recompute" / "G1_runs" / "rerun_d89.sh"
S04A = ROOT / "findings" / "recompute" / "S04a_flip_stats.json"
STUDIO, S3_CLONE = S457.STUDIO, "projects/mentori-runs-s3"
SSH = S457.SSH
INDEX = S457.INDEX
CONFIGS = [c for c, _ in S457.G1]
LABEL = dict(S457.G1)
N_Q, N_DRAWS = 135, 3
# k of m (fig3.md section 3): the answers the plate reads, by set. T2's rows join m only after S518.
PLANNED_PARTS = {"G1": 6 * 135 * 3, "G2": 135 * 3, "G6 cap 10": 135 * 3, "G4 draw 1": 11682, "G4 draws 2 and 3": 6480}
PLANNED = sum(PLANNED_PARTS.values())                 # 21,402
PLANNED_S5 = PLANNED_PARTS["G1"]                      # Supplementary Figure 16 reads G1 only
# the two rows outside the six strategies (LIST.md:310-311, D200): (config, set, label on the plate)
EXTRA = (("matched_budget", "G2", fn.MATCHED_BUDGET), ("cap10", "G6", fn.PACKAGE_RLM_N.format(n=10)))
EXTRA_DRAWN = tuple(c for c, _, _ in EXTRA)
G2_ANSWERS_SHA = S511.G2_ANSWERS_SHA                  # the copy S3 judged
# D218 (2): Zhang RLM-10's generation records, for 3a's clock-time margin, where S457's rebuild draws Supplementary
# Figure 15 from (G6 after the D135 reruns, findings/recompute/g6_d135_inputs, each file pinned by its SOURCE_MTIMES.json)
G6_SET, G6_RUN10 = "g6_d135", "b4_rlm_ref__cap10__all135"
SUPP6_DIR = ROOT / "findings" / "figures_provisional" / "supp_fig17_outcomes"   # D218 (2): the margin's gate
SUPP6_SHEET = "Supplementary Fig. 17c"
THRESHOLDS, PRIMARY = (4, 3), 4                       # Rule 5, pass-based only; D154: 4 the pass rate, 3 relaxed
REFUSAL_T = 3                                         # Rule 9: refused = refusal accuracy 3 or more (no second level)
N_BOOT, SEED = 10000, 20261013                        # Rule 2: S407's resamples and seed (S407:190)
PCT = (2.5, 97.5)                                     # Rule 2: S407's percentiles (S407:191)
ALPHA = 0.05                                          # Rule 11: two-sided alpha 0.05
JUDGE_FAILED = {"error", "stalled", "length", "cancelled", "unparseable"}   # judge_passages.py STATUS: never scored
METRIC = {"answerable": "correctness", "false_premise": "correctness", "not_answerable": "refusal_accuracy"}
CUT = {"max_turns_partial", "length"}       # Rule 10: text kept, scored as written. closing_length and
#                                             closing_search_request store no text (exp1_rlm_vs_singlepass.py:423-425)
LOCK_TOML = ROOT / "experiments" / "LOCK.toml"
LOCK_WANT = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"   # D88; run_s3.sh:89 LOCK_WANT
LOCKS_OK = __import__("lock_equiv").EQUIVALENT   # D205: D88 and the locks lock_equiv proves equal to it in every sent setting
# Rule 10 (D83 Q145, D89, D90): the Gemini call statuses a caller returns (experiments/runner/gemini_client.py:94-106).
# Blocks and recitation stops are grouped as "stopped by Google"; the others are recorded with their status.
GOOGLE_STOP = ("blocked", "recitation")
RETURNED = ("empty", "blocked", "recitation", "malformed_function_call", "malformed_response", "language", "other",
            "unexpected_tool_call", "too_many_tool_calls")
_LOCK = __import__("tomllib").loads(LOCK_TOML.read_text())
JUDGE = _LOCK["judge"]["model"]                         # LOCK [judge] model (devstral-small-2:24b)


def judge2() -> str:
    return _LOCK["judge"]["second_model"]                # LOCK [judge] second_model (D85): S518's second_judge source
JUDGE_DIGEST = _LOCK["models"][JUDGE]["digest"]         # LOCK [models]: the digest every judge call must have
GREY_DOT_MM, GREY_PITCH_MM = 0.70, 0.85                 # FIGURE_RULES.md E2 (Figure 6c's grey dots)
GREY_UP_MM = 1.1 + 0.75 + GREY_DOT_MM / 2               # clear of the mean's 1.5 mm marker, 1.1 mm above the line
# Rule 11's rows for the letter's Figure 2 claims on panels a and d, in S393's words (findings/recompute/
# S393_early_claims.md:18-23, "Where each claim is printed" :114-136), and Rule 3's two named comparisons
# (LIST.md Rule 11 table, first row). (id, claim, kind, A, B, group): group "answerable" is the pass rate on the 86,
# "refusal" the refused share on the 39 (Rule 9: set-ups compared by Rule 3).
CLAIMS = [
    ("E1a", "RLM-10 has the highest pass rate of the six strategies", "highest", "rlm_10", None, "answerable"),
    ("E1b", "verified pass has the lowest pass rate of the six strategies", "lowest", "verified_pass", None,
     "answerable"),
    ("E4", "RLM-10 passes more than verified pass", "above", "rlm_10", "verified_pass", "answerable"),
    ("E5", "RLM-10 passes more than single pass", "above", "rlm_10", "single_pass", "answerable"),
    ("R11", "verified pass passes less than single pass", "below", "verified_pass", "single_pass", "answerable"),
    ("E6", "RLM-10 refuses more not-answerable questions than multi-hop", "above", "rlm_10", "multi_hop",
     "refusal")]


class Refused(Exception):
    """A check failed: nothing is written, exit 1."""


# Panel f (plan row T2, D83 Q174): the judge code fingerprints it may compare (D160 (5), Valerio's Q16 O-a). G1's rows
# were judged on judge_passages.py at commit d0312bc (run_sha256 38ae79ab), T2's on main's newer judge code (11e51fde;
# findings/recompute/S3_runs/README.md "T2"). Panel f may set T2's scores beside G1's under the two fingerprints only
# when scripts/S495_t2_judge_code_proof.py has written a verdict that passed: offline, every one of G1's (a) requests
# byte-identical under both codes; online, its sample of G1's own answers judged again on the new code with every
# score equal to G1's. Panel f is not drawn yet and rank reads no T2 row, so nothing calls this today: it is the rule
# the panel-f reader applies to the run_sha256 of its G1 and T2 rows, and selftest holds it to its cases.
S495_DIR = ROOT / "findings" / "recompute" / "S495_t2_judge_code_proof"
# D256 Q1 (Valerio, 5 Nov 18:46, "Q1: ok"): on key v2.5, G1's rows carry S6G1's run_sha256 211568db
# (fig3_s6_inputs/s6_g1_collect.jsonl.json). A T2 run under another v2.5 run_sha256 is accepted beside it only when every
# header of both runs names one judge_passages code identity (the header's code.judge_passages, sorted JSON, sha256):
# S512 hashes its own file and the set's question scope into run_sha256 (S512_s6_rejudge_v25.py:382-393), so two runs of
# one judge code differ there by design. The caller binds each header to its rows (judge_rows_v25 recomputes run_sha256
# from the header's own fields). Key v2.4 keeps S495's proof for 11e51fde unchanged.
G1_V25_RUN_SHA = "211568dbdfa09482e9c0abfb3b1da92d0bbd62d14a7646058663a990cbb54235"


def judge_passages_code(h: dict) -> str | None:
    """sha256 of a judge header's code.judge_passages as sorted JSON (D256 Q1), or None when it has none."""
    jp = (h.get("code") or {}).get("judge_passages") if isinstance(h.get("code"), dict) else None
    return hashlib.sha256(json.dumps(jp, sort_keys=True).encode()).hexdigest() if isinstance(jp, dict) and jp else None


def v25_judge_codes(g1_run_sha: str, t2_run_sha: str, g1_headers, t2_headers) -> dict:
    """D256 Q1: G1's v2.5 run 211568db beside a T2 v2.5 run: one run_sha256, or one judge_passages code identity in every
    header of both runs (each header's run_sha256 its run's, key_version v2.5). Refuses otherwise."""
    if g1_run_sha != G1_V25_RUN_SHA:
        raise Refused(f"panel e (T2), key v2.5: G1's rows carry run_sha256 {str(g1_run_sha)[:12]}, not S6G1's "
                      f"{G1_V25_RUN_SHA[:12]}")
    if t2_run_sha == g1_run_sha:
        return {"judge_codes": 1, "run_sha256": [g1_run_sha], "key": "v2.5"}
    g1h, t2h = list(g1_headers or []), list(t2_headers or [])
    if not g1h or not t2h:
        raise Refused(f"panel e (T2), key v2.5 (D256 Q1): T2's run_sha256 {str(t2_run_sha)[:12]} differs from G1's and "
                      f"{'G1' if not g1h else 'T2'} gives no judge header to compare the judge code on")
    codes = set()
    for who, run, hs_ in (("G1", g1_run_sha, g1h), ("T2", t2_run_sha, t2h)):
        for h in hs_:
            if h.get("run_sha256") != run or h.get("key_version") != "v2.5":
                raise Refused(f"panel e (T2), key v2.5 (D256 Q1): a {who} header carries run_sha256 "
                              f"{str(h.get('run_sha256'))[:12]}, key_version {h.get('key_version')!r}; its rows' "
                              f"{str(run)[:12]}, v2.5")
            c = judge_passages_code(h)
            if c is None:
                raise Refused(f"panel e (T2), key v2.5 (D256 Q1): a {who} header has no code.judge_passages")
            codes.add((who, c))
    by = {c for _, c in codes}
    if len(by) != 1:
        raise Refused(f"panel e (T2), key v2.5 (D256 Q1): the judge_passages code identity differs: "
                      f"{sorted((w, c[:8]) for w, c in codes)}")
    return {"judge_codes": 2, "run_sha256": [g1_run_sha, t2_run_sha], "key": "v2.5", "rule": "D256 Q1",
            "judge_passages_code_sha256": next(iter(by)), "headers": {"G1": len(g1h), "T2": len(t2h)}}


def panel_f_judge_codes(g1_run_sha: str, t2_run_sha: str, proof_dir: Path = S495_DIR, *, g1_headers=None,
                        t2_headers=None) -> dict:
    """Accept panel e's (T2, 3f before D218) two judge-code fingerprints, or refuse. Rows under one fingerprint are accepted as they are;
    T2 under 11e51fde beside G1 under 38ae79ab only with S495's verdict.json passed, its counts complete, its
    sample the one in offline.json beside it (which must have passed too) and the verdict matching its row file
    online/rows.jsonl (D161 (9)). Key v2.5 (D256 Q1): G1 under 211568db goes to v25_judge_codes with the two runs'
    headers. Returns what the provenance records."""
    import S495_t2_judge_code_proof as S495
    if g1_run_sha == G1_V25_RUN_SHA:
        return v25_judge_codes(g1_run_sha, t2_run_sha, g1_headers, t2_headers)
    if g1_run_sha != S495.G1_RUN_SHA:
        raise Refused(f"panel e (T2): G1's rows carry run_sha256 {str(g1_run_sha)[:12]}, not G1's {S495.G1_RUN_SHA[:12]}")
    if t2_run_sha == g1_run_sha:
        return {"judge_codes": 1, "run_sha256": [g1_run_sha]}
    if t2_run_sha != S495.T2_RUN_SHA:
        raise Refused(f"panel e (T2): T2's rows carry run_sha256 {str(t2_run_sha)[:12]}, neither G1's "
                      f"{S495.G1_RUN_SHA[:12]} nor the T2 code S495 proves ({S495.T2_RUN_SHA[:12]})")
    vf, of = Path(proof_dir) / "verdict.json", Path(proof_dir) / "offline.json"
    if not vf.is_file() or not of.is_file():
        raise Refused(f"panel e (T2): T2's judge code {S495.T2_RUN_SHA[:12]} differs from G1's and {vf} or {of} is "
                      f"missing: run S495 offline, then online on a judge port (D160 (5))")
    try:
        v, o = json.loads(vf.read_text()), json.loads(of.read_text())
    except ValueError as e:
        raise Refused(f"panel e (T2): S495's verdict or offline record does not parse: {e}") from None
    want = {"mode": "online", "g1_run_sha256": S495.G1_RUN_SHA, "t2_run_sha256": S495.T2_RUN_SHA,
            "run_sha256_now": S495.T2_RUN_SHA, "offline_passed": True, "passed": True,
            "sample_sha256": (o.get("sample") or {}).get("sha256")}
    bad = {k: v.get(k) for k, w in want.items() if v.get(k) != w}
    n, m = v.get("n"), 6 * sum(S495.PER_STRATEGY.values())
    full = (n == m and all(v.get(k) == n for k in ("calls_ok", "equal_scores", "prompt_sha256_g1", "model_digest_g1"))
            and not v.get("differences"))
    oc, oj = o.get("counts") or {}, o.get("judged_a_ok")
    off = (o.get("passed") is True and isinstance(oj, int) and oj > 0
           and all(oc.get(k) == oj for k in ("identical", "prompt_sha256_g1", "scores_new_g1")))
    if bad or not full or not off:
        raise Refused(f"panel e (T2): S495's verdict does not prove T2's judge code: fields {bad}; sample counts complete "
                      f"{full} (n {n}, want {m}); offline record passed with every request identical {off}")
    # D161 (9): the verdict must match the row file it was computed from. Its rows_sha256 must be the sha256 of
    # online/rows.jsonl beside it, the rows must be the sample.jsonl answers of the offline record, in its order, and
    # the verdict's counts are counted again from the rows, so a verdict edited by hand to "passed" is refused.
    rf, sf = Path(proof_dir) / "online" / "rows.jsonl", Path(proof_dir) / "sample.jsonl"
    rsha = sha256_file(rf) if rf.is_file() else None
    if rsha is None or v.get("rows_sha256") != rsha:
        raise Refused(f"panel e (T2): S495's verdict does not match its row file: the verdict records rows_sha256 "
                      f"{str(v.get('rows_sha256'))[:12]}, {rf} " + (f"has {rsha[:12]}" if rsha else "is missing"))
    if not sf.is_file() or sha256_file(sf) != (o.get("sample") or {}).get("sha256"):
        raise Refused(f"panel e (T2): S495's verdict does not match its row file: {sf} is missing or not the offline "
                      f"record's sample")
    try:
        rows = [json.loads(x) for x in rf.read_text().splitlines()]
        sample = [json.loads(x) for x in sf.read_text().splitlines()]
    except ValueError as e:
        raise Refused(f"panel e (T2): S495's row or sample file does not parse: {e}") from None
    ok_ = [r.get("status") == "ok" for r in rows]
    recount = {"n": len(rows), "calls_ok": sum(ok_),
               "equal_scores": sum(k and r.get("equal") is True and r.get("scores") == r.get("g1_scores")
                                   for k, r in zip(ok_, rows)),
               "prompt_sha256_g1": sum(r.get("prompt_sha256_g1") is True for r in rows),
               "model_digest_g1": sum(r.get("model_digest_g1") is True for r in rows)}
    same_answers = ([(r.get("run_id"), r.get("answer_key"), r.get("g1_scores")) for r in rows]
                    == [(x.get("run_id"), x.get("answer_key"), x.get("g1_scores")) for x in sample])
    code_ok = all(r.get("run_sha256") == S495.T2_RUN_SHA for r in rows)
    off_count = {k: (v.get(k), w) for k, w in recount.items() if v.get(k) != w}
    if off_count or not same_answers or not code_ok:
        raise Refused(f"panel e (T2): S495's verdict does not match its row file: counts (verdict, rows) {off_count}; "
                      f"the rows are the sample's answers {same_answers}; every row under T2's code {code_ok}")
    return {"judge_codes": 2, "run_sha256": [S495.G1_RUN_SHA, S495.T2_RUN_SHA],
            "proof": str(vf.relative_to(ROOT)) if vf.is_relative_to(ROOT) else str(vf),
            "verdict_sha256": sha256_file(vf), "offline_sha256": sha256_file(of), "rows_sha256": rsha, "n": n}


def run_of(c):
    return f"exp_01__{c}__{INDEX}"


def sha256_file(p) -> str:
    return S457.sha256_file(Path(p))


def label(p) -> str:
    """How a provenance or ranking file names an input: "frozen:<set>/<rel>" or "frozen:<tar>/<rel>" for a frozen
    copy (fig_repro.frozen_label), a repository-relative path for another file of the repository, and the path as
    given for a file outside it (D155: no name that holds this machine's folders when the input is in the repository).
    """
    q = Path(p).expanduser().resolve()
    return FR.frozen_label(q) if q.is_relative_to(ROOT) else str(p)


def pct(x, nd=1):
    return "-" if x is None else S457.half_up(100 * x, nd)


def pfmt(p):
    if p is None:
        return "-"
    return "< 0.001" if p < 0.001 else S457.half_up(p, 3)


# ---------------------------------------------------------------------------------------------------------------
# the key, the reruns, the answers
# ---------------------------------------------------------------------------------------------------------------
def key_groups() -> dict:
    """{question id: Rule 8 group}, from the D5 key the runner pins (experiment.questions(), sha256-checked)."""
    from experiments.runner.experiment import questions
    from experiments.scorers.records import GROUP_OF_TYPE
    g = {q["id"]: GROUP_OF_TYPE[q["answer_type"]] for q in questions()}
    want = {"answerable": 86, "false_premise": 10, "not_answerable": 39}
    if len(g) != N_Q or Counter(g.values()) != Counter(want):
        raise Refused(f"the D5 key gives {len(g)} questions {dict(Counter(g.values()))}, want {N_Q} {want}")
    return g


def rerun_keys(path: Path = RERUN_SH) -> list[str]:
    """The 15 answer keys G1 reran on 18 October, read from rerun_d89.sh's KEYS as snap_s3_inputs.sh:59 reads them
    (lines of six fields whose first is an exp_01 run: index|config|question|d<draw>)."""
    keys = []
    for ln in path.read_text().splitlines():
        f = ln.strip().split("|")
        if len(f) == 6 and f[0].startswith("exp_01__"):
            keys.append("|".join(f[1:5]))
    if len(keys) != 15 or len(set(keys)) != 15:
        raise Refused(f"{path.relative_to(ROOT)}: {len(keys)} rerun keys, want 15 distinct")
    return keys


def read_answers(dirs: list[Path], manifests: dict | None = None) -> tuple[dict, dict, list]:
    """{answer_key: record} from <dir>/<run>/answers.jsonl, each key's last line (exp_01 appends; records.py _exp01);
    a later --answers dir replaces an earlier one's record of the same key (the G1R15 copy over K1's). Each answers
    file must match its line in <dir>/../MANIFEST.sha256 (K1's copy and snap's copies each carry one);
    a folder without that file is refused. Status as records.py:153-156. Also every line of the verified-pass files,
    in the order given, for chunk_verifier.verifier_status_report (Rule 4, Q78), which keeps each key's last line.
    manifests ({str(dir): {"runs/<run>/answers.jsonl": sha256}}) gives a folder's lines in place of that file: the
    frozen K1 copy (k1_inputs_runs.tar) holds runs/ only, and its committed members list is its manifest (rebuild)."""
    out, inputs, vp_lines = {}, {}, []
    for d in dirs:
        d = Path(d).expanduser()
        man = d.parent / "MANIFEST.sha256"
        given = (manifests or {}).get(str(d))
        if given is None and not man.exists():
            raise Refused(f"--answers {d}: no MANIFEST.sha256 beside it ({man}); the records judged cannot be checked")
        want = dict(given) if given is not None else {}
        for ln in (man.read_text().splitlines() if given is None else []):
            if ln.strip():
                h, p = ln.split(None, 1)
                want[p.strip()] = h
        found = 0
        for c in CONFIGS:
            p = d / run_of(c) / "answers.jsonl"
            if not p.exists():
                continue
            found += 1
            h = sha256_file(p)
            rel = f"runs/{run_of(c)}/answers.jsonl"
            if want.get(rel) != h:
                raise Refused(f"{p}: sha256 {h[:12]} is not its MANIFEST.sha256 line ({str(want.get(rel))[:12]})")
            inputs[str(p)] = h
            last = {}
            for n, raw in enumerate(p.read_text().splitlines(), 1):
                if raw.strip():
                    r = json.loads(raw)
                    last[r["answer_key"]] = (n, r)
                    if c == "verified_pass":
                        vp_lines.append(r)
            for k, (n, r) in last.items():
                g = r.get("generation") or {}
                err, ans = g.get("error"), g.get("answer") or ""
                calls = [x.get("status") for x in (g.get("calls") or []) if isinstance(x, dict)]
                try:                                     # panel d: S457's reader of a G1 record (tokens, times, calls)
                    x = S457.exp01_row(k, r, c)
                except (SystemExit, KeyError, TypeError) as e:
                    raise Refused(f"{p}:{n}: S457.exp01_row cannot read the record's calls and times: {e}") from None
                cost = {"calls": x["calls_n"], "clock_s": x["clock"], "clock_less_wait_s": x["clock_less_wait"],
                        "wait_s": x["wait"], "tokens": x["tokens"], "model_s": x["model"]}
                out[k] = {"status": "error" if err else ("ok" if ans.strip() else "no_answer"), "error": err,
                          "cost": cost, "answer": ans, "answer_sha256": hashlib.sha256(ans.encode("utf-8")).hexdigest(),
                          "turn_limit_note": (((g.get("rlm") or {}).get("metadata") or {}).get("turn_limit_note")),
                          "stop_reason": g.get("stop_reason"), "source": f"{p}:{n}", "run_id": r.get("run_id") or run_of(c),
                          "gen_model": r.get("gen_model"),
                          "returned": sorted({s for s in calls if s in RETURNED})}
        if not found:
            raise Refused(f"--answers {d}: no {run_of('<strategy>')}/answers.jsonl in it")
    return out, inputs, vp_lines


# ---------------------------------------------------------------------------------------------------------------
# reading the collect output
# ---------------------------------------------------------------------------------------------------------------
def judge_module():
    from experiments.scorers import judge_passages as JP
    return JP


def latest_by_ident(folder: Path) -> dict:
    """The latest row of each answer in every judge_passages.jsonl under <folder>/judge/ (collect's rows_of)."""
    JP = judge_module()
    got = {}
    for f in sorted(folder.glob("judge/*/judge_passages.jsonl")):
        for d in JP.read_rows(f):
            got[JP.ident(d)] = d
    return got


def cell_of(r: dict, group: str) -> tuple[dict | None, str | None]:
    """One judge row's cell by Rule 10 (module docstring, outcomes): (cell, None), or (None, why) for an (a) status
    that is none of ok, no_answer or a judge-call failure. read_collect and judge_rows apply the same rule."""
    st = (r.get("a") or {}).get("status")
    if st == "ok":
        v = ((r["a"].get("scores") or {}).get(METRIC[group]))
        cell = {"kind": "scored", "score": v} if isinstance(v, (int, float)) and not isinstance(v, bool) \
            else {"kind": "unscored", "why": f"ok, no {METRIC[group]} score"}
    elif st == "no_answer":
        cell = {"kind": "failed", "why": r.get("error") or "no answer stored"}
    elif st in JUDGE_FAILED:
        cell = {"kind": "unscored", "why": st}
    else:
        return None, f"(a) status {st!r} is none of ok, no_answer, {sorted(JUDGE_FAILED)}"
    cell.update(key=r["answer_key"], item_sha256=r.get("item_sha256"), at=r.get("at"))
    return cell, None


def read_collect(collect: Path, draws: list[int], groups: dict, reruns: list[str], replace_out: Path | None = None,
                 answers: dict | None = None, relocate: dict | None = None) -> dict:
    """The checked cells: {(config, question, draw): cell} for the draws read, and what was read (module docstring,
    WHAT RANK REFUSES). relocate ({folder the sidecar records: the folder that holds that copy here}) reads the outs
    collect read from a frozen copy (D155, rebuild) while every check and every output keeps the recorded names, so
    the sidecar's counts and paths are compared as written; without it the recorded folders are read in place."""
    relocate = {str(k).rstrip("/"): Path(v) for k, v in (relocate or {}).items()}

    def here(p) -> Path:
        s_ = str(p)
        for k, v in relocate.items():
            if s_ == k or s_.startswith(k + "/"):
                return v / s_[len(k):].lstrip("/") if s_ != k else v
        return Path(p)

    def shown(p) -> str:
        s_ = str(p)
        for k, v in relocate.items():
            if s_ == str(v) or s_.startswith(str(v) + "/"):
                return k + s_[len(str(v)):]
        return s_
    side_p = collect.with_name(collect.name + ".json")
    if not collect.exists():
        raise Refused(f"{collect} does not exist")
    if not side_p.exists():
        raise Refused(f"{side_p.name} missing: collect writes it beside its output; without it the rows cannot be tied "
                      f"to one run_sha256 and to the reruns' pass")
    side = json.loads(side_p.read_text())
    rows = [json.loads(x) for x in collect.read_text().splitlines() if x.strip()]
    if side.get("rows") != len(rows):
        raise Refused(f"the sidecar says {side.get('rows')} rows, the file holds {len(rows)}")
    if side.get("set") != "G1":
        raise Refused(f"the sidecar's set is {side.get('set')!r}: run collect with --set G1 (S3 README)")
    runs = Counter(r.get("run_sha256") for r in rows)
    if len(runs) > 1:
        raise Refused(f"the rows carry {len(runs)} run_sha256 values (another lock, code or judge setting): "
                      + "; ".join(f"{str(k)[:12]} {n} rows" for k, n in runs.most_common()))
    run_sha = next(iter(runs), None)
    if rows and side.get("run_sha256") != run_sha:
        raise Refused(f"the sidecar's run_sha256 {str(side.get('run_sha256'))[:12]} is not the rows' {str(run_sha)[:12]}")
    locks = Counter(r.get("lock_sha256") for r in rows)
    if set(locks) - LOCKS_OK:
        raise Refused(f"the rows carry lock_sha256 {', '.join(f'{str(k)[:8]} ({n} rows)' for k, n in locks.items())}; "
                      f"D88 judges under {LOCK_WANT[:8]} only (run_s3.sh:89, 163)")
    seen, cells, bad, other_draws = {}, {}, [], Counter()
    for i, r in enumerate(rows, 1):
        c, q, d = r.get("config"), r.get("question_id"), r.get("draw")
        k = (c, q, d)
        if k in seen:
            raise Refused(f"rows {seen[k]} and {i} are both {k}: collect writes one row per answer")
        seen[k] = i
        if c not in CONFIGS or r.get("run_id") != run_of(c) or q not in groups or d not in (1, 2, 3) \
                or r.get("answer_key") != f"{INDEX}|{c}|{q}|d{d}":
            bad.append(f"row {i} {k}: not a G1 answer (run_id {r.get('run_id')!r}, answer_key {r.get('answer_key')!r})")
            continue
        if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
            bad.append(f"row {i} {k}: judged with the {'answerable' if r.get('answerable_prompt') else 'decline'} "
                       f"prompt, Rule 8's group is {groups[q]}")
            continue
        if d not in draws:
            other_draws[d] += 1
            continue
        cell, why = cell_of(r, groups[q])
        if why:
            bad.append(f"row {i} {k}: {why}")
            continue
        cells[k] = cell
    if bad:
        raise Refused(f"{len(bad)} rows refused, first: {bad[0]}")
    want = [(c, q, d) for c in CONFIGS for q in sorted(groups) for d in draws]
    missing = [k for k in want if k not in cells]
    if missing:
        per = Counter((c, d) for c, _, d in missing)
        raise Refused(f"{len(missing)} of {len(want)} answers of draw(s) {','.join(map(str, draws))} have no row "
                      f"(phase not finished?): " + "; ".join(f"{LABEL[c]} draw {d}: {n} missing"
                                                              for (c, d), n in sorted(
                                                                  per.items(), key=lambda z: (CONFIGS.index(z[0][0]),
                                                                                              z[0][1]))))
    # the reruns (D93 Q-c): each of the draws read from its own pass, with that pass's latest row
    rp = replace_out
    ins = (side.get("_provenance") or {}).get("inputs") or []
    if rp is None and ins:
        rp = Path(ins[0]).parent / "out_g1r15"
    rp = Path(rp) if rp else None
    want_r = [k for k in reruns if int(k.rsplit("|d", 1)[1]) in draws]
    if rp is None or str(rp) not in ins:
        raise Refused(f"collect was not given the reruns' out ({rp}) as --replace: G1's {len(want_r)} rerun answers of "
                      f"the draws read would be their old, failed versions (D93 Q-c)")
    rp_here = here(rp)
    if not rp_here.is_dir():
        raise Refused(f"the replace out {rp_here} is not here: run rank where collect ran (pull keeps both)")
    from_rp = sum(n for f, n in (side.get("from") or {}).items() if f.startswith(str(rp) + "/"))
    if from_rp != side.get("replaced", 0) + side.get("added_by_replace", 0):
        raise Refused(f"the sidecar takes {from_rp} rows from {rp} but counts {side.get('replaced')} replaced and "
                      f"{side.get('added_by_replace')} added")
    latest = latest_by_ident(rp_here)
    key_of = {(d["run_id"], d["config"], d["question_id"], d["draw"]): d for d in latest.values()}
    extra = sorted(d["answer_key"] for d in latest.values() if d.get("answer_key") not in set(reruns))
    if extra:
        raise Refused(f"the replace out holds {len(extra)} answers that are not G1's reruns, first {extra[0]}")
    wrong = []
    for k in want_r:
        _, c, q, dd = k.split("|")
        dr = int(dd[1:])
        src = key_of.get((run_of(c), c, q, dr))
        cell = cells[(c, q, dr)]
        if src is None:
            wrong.append(f"{k}: not in the replace out (its phase not judged yet?)")
        elif (src.get("item_sha256"), src.get("run_sha256")) != (cell["item_sha256"], run_sha):
            wrong.append(f"{k}: the collect row is not the replace out's latest row")
    if wrong:
        raise Refused(f"{len(wrong)} of G1's {len(want_r)} rerun answers of the draws read are not from their own "
                      f"pass: {wrong[0]}")
    units = check_units([here(x) for x in ins], run_sha, draws, shown)
    # the answers judged: their stop reasons (Rule 10), each record agreeing with its judge row
    disagree, stops = [], {}
    if answers is not None:
        for k, cell in cells.items():
            rec = answers.get(cell["key"])
            if rec is None:
                disagree.append(f"{cell['key']}: no generation record in --answers")
                continue
            if (cell["kind"] == "failed") != (rec["status"] != "ok"):
                disagree.append(f"{cell['key']}: judge {'no_answer' if cell['kind'] == 'failed' else 'scored'}, "
                                f"record status {rec['status']} ({rec['source']})")
                continue
            stops[k] = rec
        if disagree:
            raise Refused(f"{len(disagree)} answers in --answers are not the versions S3 judged, first: {disagree[0]}")
    for k, rec in stops.items():
        cells[k].update(stop_reason=rec["stop_reason"], record=rec["source"], gen_error=rec["error"],
                        gen_model=rec.get("gen_model"), returned=rec.get("returned") or [], cost=rec["cost"])
    return {"cells": cells, "rows": len(rows), "rows_other_draws": dict(other_draws), "run_sha256": run_sha,
            "lock_sha256": next(iter(locks), None), "side": side, "replace_out": str(rp),
            "replace_out_here": str(rp_here), "outs_here": [str(here(x)) for x in ins],
            "reruns_read": want_r, "rows_from_replace": from_rp, "answers_joined": answers is not None,
            "units": units}


JOIN = ("stop_reason", "record", "gen_error", "gen_model", "returned", "cost")   # read_collect's fields from --answers


def judge_rows(read: dict, collect: Path, groups: dict, reruns: list[str], draws: list[int],
               s6_root: Path | None = None, answers: dict | None = None) -> dict:
    """D186 (3): every cell read_collect made is read through scripts/judge_rows_v25.py, which takes an answer's key
    v2.5 judge row where one exists, else its key v2.4 row. Called after read_collect, whose checks of the v2.4 collect
    (one run_sha256, lock, G1's rows, prompts, reruns, units) are the reproduction made first.
      - the v2.4 source: the collect read_collect read, held to the outs it read (out/, out_g1r15/ as --replace;
        judge_rows_v25.check_v24: key_hash on all_v2_4.json, headers' run_sha256 recomputed), the 15 rerun keys held
        to out_g1r15 (check_replace);
      - the v2.5 source: out_s6_g1 with out_s6_g1r15 as --replace under s6_root (default: the folder holding the outs
        collect read), present only when both are; s3_guard.py collect run on them into a temporary file, then
        check_v25 (S512's key_hash, pins, run_sha256, the 132) and check_replace, and check_units on both outs (each
        unit ended as run_s3.sh accepts one);
      - choose(..., all_draws=True) on G1's 6 x 135 x 3 answers. A cell whose answer has a v2.5 row is made again from
        that row by cell_of, with read_collect's prompt check and, with answers, the record check (failed exactly when
        the record's status is not ok) and its joined fields; every other cell must be the v2.4 row chosen
        (item_sha256). An answer of the draws read with no row chosen is refused.
    Returns the counts the outputs record ("awaiting_s6": the answers of the 132 changed questions still read from
    key v2.4; "provisional" while any is)."""
    v24_root = Path(read["replace_out_here"]).parent
    srcs = JR.sources(v24_root, "G1")
    src24 = srcs[0]
    if [str(o) for o in src24["outs"]] + [str(src24["replace"])] != [str(x) for x in read["outs_here"]]:
        raise Refused(f"judge_rows: the reader's v2.4 outs {[str(o) for o in src24['outs']]} and replace "
                      f"{src24['replace']} are not the outs collect read ({read['outs_here']})")
    s6_root = Path(s6_root) if s6_root is not None else v24_root
    s6 = JR.sources(s6_root, "G1")[1]
    names = {str(s6_root / n): n for n in ("out_s6_g1", "out_s6_g1r15")}
    info_src = {"G1": {"kind": JR.V24, "present": True, "run_sha256": None, "rows": None},
                "S6G1": {"kind": JR.V25_CHANGED, "present": s6["present"],
                         "missing": [names.get(m, m) for m in s6["missing"]], "run_sha256": None, "rows": None}}
    units25 = None
    try:
        L24 = JR.read_source(src24, collect, replace_keys=reruns)
        loaded = [L24]
        if s6["present"]:
            with tempfile.TemporaryDirectory(prefix="S463_s6_") as t:
                dest = Path(t) / "s6g1_collect.jsonl"
                buf = io.StringIO()
                import contextlib
                with contextlib.redirect_stdout(buf):
                    rc = JR.guard().collect(s6["outs"], s6["replace"], dest, s6["set"])
                if rc:
                    raise Refused(f"judge_rows: s3_guard collect refused S6G1: {buf.getvalue().strip()[-300:]}")
                L25 = JR.read_source(s6, dest, replace_keys=reruns)
            units25 = check_units([*s6["outs"], s6["replace"]], L25.run_sha256, draws, lambda p: str(p))
            loaded.append(L25)
        ans = [{"run_id": run_of(c), "config": c, "question_id": q, "draw": d, "answer_key": f"{INDEX}|{c}|{q}|d{d}"}
               for c in CONFIGS for q in sorted(groups) for d in (1, 2, 3)]
        choice = JR.choose(ans, loaded, all_draws=True)
        rep = JR.report(choice, all_draws=True)
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25: {e}") from None
    for L in loaded:
        info_src[L.name].update(run_sha256=L.run_sha256, rows=len(L.rows), replace=L.extra.get("replace"))
    n25, awaiting_read, bad = 0, 0, []
    for k in sorted(read["cells"], key=lambda t: (CONFIGS.index(t[0]), t[1], t[2])):
        c, q, d = k
        cell = read["cells"][k]
        ch = choice[(run_of(c), c, q, d)]
        if ch["status"] == "v2.5":
            r = ch["row"]
            if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
                bad.append(f"{k}: the v2.5 row was judged with the {'answerable' if r.get('answerable_prompt') else 'decline'} "
                           f"prompt, Rule 8's group is {groups[q]}")
                continue
            new, why = cell_of(r, groups[q])
            if why:
                bad.append(f"{k}: v2.5 row {why}")
                continue
            if answers is not None:
                rec = answers.get(new["key"])
                if rec is None or (new["kind"] == "failed") != (rec["status"] != "ok"):
                    bad.append(f"{k}: the v2.5 row is {'no_answer' if new['kind'] == 'failed' else 'scored'}, the "
                               f"record's status is {rec and rec['status']}")
                    continue
            new.update({f: cell[f] for f in JOIN if f in cell}, key_version="v2.5")
            read["cells"][k] = new
            n25 += 1
        elif ch["status"] in ("v2.4", "v2.4 awaiting S6"):
            if (ch["row"] or {}).get("item_sha256") != cell.get("item_sha256"):
                bad.append(f"{k}: the v2.4 row chosen is not the collect's row read")
            awaiting_read += ch["status"] == "v2.4 awaiting S6"
        else:
            bad.append(f"{k}: no judge row chosen ({ch['status']})")
    if bad:
        raise Refused(f"judge_rows: {len(bad)} cells refused, first: {bad[0]}")
    n_read = len(read["cells"])
    status = (f"awaiting S6: {awaiting_read:,} of the {n_read:,} answers read (the {len({q for (_, q, _) in read['cells'] if q in set(JR.S512.changed_ids())})} "
              f"questions of S512's 132 changed ones that G1 asks) are read from key v2.4 until S6G1 judges them on "
              f"key v2.5" if awaiting_read else
              f"key v2.5 for every answer of the 132 changed questions read ({n25:,})")
    return {"reader": "scripts/judge_rows_v25.py (D186 (3)): an answer's key v2.5 row (S512, out_s6_g1 with "
                      "out_s6_g1r15 as --replace) where one exists, else its key v2.4 row (out/ with out_g1r15/)",
            "sources": info_src, "status": status, "provisional": bool(awaiting_read),
            "answers_read": n_read, "cells_from_v25": n25, "awaiting_s6_read": awaiting_read,
            "awaiting_s6_all_draws": rep["awaiting_s6"]["count"], "by_status": rep["by_status"],
            "by_draw": {str(d): v for d, v in rep["by_draw"].items()}, "units_v25": units25,
            "choice": choice}


def judge_rows_record(jr: dict) -> dict:
    """judge_rows' result without the rows chosen: what ranking.json and the provenance keep. The v2.5 units are named
    relative to the repository, since check_units names each folder as it was read here and D155 keeps machine folders
    out of a record. S472, S486, S497 and S532 call this too; S472's rel_units gives the same names from these."""
    def in_repo(p):
        q = Path(p).resolve()
        return str(q.relative_to(ROOT)) if q.is_relative_to(ROOT) else str(p)
    out = {k: v for k, v in jr.items() if k != "choice"}
    u = out.get("units_v25")
    if u:
        out["units_v25"] = {k: ({in_repo(p): x for p, x in v.items()} if k in ("folders", "starts") else v)
                            for k, v in u.items()}
    return out


PHASE_OF_DRAW = {1: 1, 2: 2, 3: 2}                      # S3 README phase table: draw 1 is phase 1, draws 2, 3 phase 2


def key_draw(key) -> int | None:
    """The draw of an answer key or a recheck key (<run id>|<answer key>), from its last field d<draw>."""
    m = re.search(r"\|d(\d+)$", str(key))
    return int(m.group(1)) if m else None


def check_units(dirs: list[Path], run_sha: str, draws: list[int], shown=str) -> dict:
    """Every judging unit whose rows are read ended as run_s3.sh accepts one (review of 18 October, defect 1). For
    each out collect read (its sidecar's inputs: the outs, then the replace out):
      - its start_<port>_*.json files: at least one, and every one names LOCK_WANT (run_s3.sh:163 refuses another);
      - per judge/<run>/ folder holding rows of the draws read under this run_sha256 (the latest row of each answer):
        * judge_passages_headers.jsonl has a line with this run_sha256, and every such line names the lock's judge,
          its digest and LOCK_WANT (judge_passages.py:636-640), so the scores are devstral's under D88's lock;
        * the recheck (judge_passages.py:80-82, 694-714): per phase of the draws read (draw 1 is phase 1, draws 2
          and 3 phase 2), the lines of judge_passages_recheck.jsonl under this run_sha256 whose answer is of that
          phase are all "equal": true, and cover min(RECHECK_N, that phase's answers in the folder whose (a) is not
          no_answer) distinct answers. A false line is a recheck that failed (judge_passages exits 1, run_s3.sh:298
          stops); fewer lines are a unit still in its recheck, or stopped in it (a resume with nothing left to judge
          makes no recheck, judge_passages.py:630-631).
    shown(path) gives the name a folder or file is reported under (read_collect's recorded name for a relocated
    copy)."""
    JP = judge_module()
    phases = sorted({PHASE_OF_DRAW[d] for d in draws})
    got = {"folders": {}, "starts": {}}
    for o in dirs:
        if not o.is_dir():
            raise Refused(f"{o} (an input of collect) is not here: run rank where collect ran (pull keeps all)")
        starts = sorted(o.glob("start_*.json"))
        if not starts:
            raise Refused(f"{o}: no start_*.json (run_s3.sh writes one per start with its commit and lock)")
        for s in starts:
            lk = json.loads(s.read_text()).get("lock_sha256")
            if lk not in LOCKS_OK:
                raise Refused(f"{s.name}: lock {str(lk)[:8]}, not {LOCK_WANT[:8]} (D88)")
            got["starts"][shown(s)] = lk[:8]
        for f in sorted(o.glob("judge/*/judge_passages.jsonl")):
            rows = {}
            for d in JP.read_rows(f):
                if d.get("run_sha256") == run_sha:
                    rows[JP.ident(d)] = d
            rows = {k: d for k, d in rows.items() if d.get("draw") in draws}
            if not rows:
                continue
            folder = f.parent
            heads = [json.loads(x) for x in (folder / "judge_passages_headers.jsonl").read_text().splitlines()
                     if x.strip()] if (folder / "judge_passages_headers.jsonl").exists() else []
            heads = [h for h in heads if h.get("run_sha256") == run_sha]
            if not heads:
                raise Refused(f"{folder}: no judge_passages_headers.jsonl line for run_sha256 {run_sha[:12]}: which "
                              f"judge wrote these rows cannot be checked")
            off = [h for h in heads if (h.get("model"), h.get("model_digest")) != (JUDGE, JUDGE_DIGEST)
                   or h.get("lock_sha256") not in LOCKS_OK]
            if off:
                h = off[0]
                raise Refused(f"{folder}: a header names judge {h.get('model')} digest {str(h.get('model_digest'))[:12]} "
                              f"lock {str(h.get('lock_sha256'))[:8]}; the lock's judge is {JUDGE} "
                              f"{JUDGE_DIGEST[:12]} under {LOCK_WANT[:8]}")
            rc_f = folder / "judge_passages_recheck.jsonl"
            rlines = [json.loads(x) for x in rc_f.read_text().splitlines() if x.strip()] if rc_f.exists() else []
            rlines = [x for x in rlines if x.get("run_sha256") == run_sha]
            seen = {}
            for ph in phases:
                eligible = sum(1 for d in rows.values() if PHASE_OF_DRAW[d["draw"]] == ph
                               and (d.get("a") or {}).get("status") != "no_answer")
                mine = [x for x in rlines if PHASE_OF_DRAW.get(key_draw(x.get("key"))) == ph]
                bad = [x["key"] for x in mine if x.get("equal") is not True]
                if bad:
                    raise Refused(f"{folder}: the recheck gave other scores for {len(bad)} answers (first {bad[0]}): "
                                  f"the unit did not pass (judge_passages.py:685-688)")
                n = len({x["key"] for x in mine})
                need = min(JP.RECHECK_N, eligible)
                if n < need:
                    raise Refused(f"{folder}: the recheck of phase {ph} covers {n} of the {need} answers it judges "
                                  f"again: the unit is still in its recheck or stopped in it")
                seen[f"phase {ph}"] = f"{n} of {need} equal"
            got["folders"][shown(folder)] = {"rows": len(rows), "recheck": seen,
                                          "judge": f"{JUDGE} {JUDGE_DIGEST[:12]}"}
    return got


# ---------------------------------------------------------------------------------------------------------------
# statistics (LIST.md Rules 2, 3, 6, 9, 10, 11)
# ---------------------------------------------------------------------------------------------------------------
def resample_counts(n: int):
    """S407's resample_index and resample_counts (scripts/S407_strategy_contrasts_v24.py:246-257): (10,000, n), how
    often each of the n questions is drawn in each resample of default_rng(20261013).integers(0, n, size=(10000, n))."""
    import numpy as np
    idx = np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))
    flat = np.bincount((idx + n * np.arange(N_BOOT)[:, None]).ravel(), minlength=N_BOOT * n)
    return flat.reshape(N_BOOT, n).astype(float)


_COUNTS: dict = {}


def interval(num: list, den: list) -> list[float]:
    """Rule 2's 95% percentile interval: per resample, the sum of num over the questions drawn (each as often as
    drawn) over the same sum of den; resamples with no den left out; percentiles 2.5 and 97.5 (S407
    percentile_interval)."""
    import numpy as np
    n = len(num)
    if n not in _COUNTS:
        _COUNTS[n] = resample_counts(n)
    w = _COUNTS[n]
    top, bottom = w @ np.array(num, dtype=float), w @ np.array(den, dtype=float)
    ok = bottom > 0
    return [float(v) for v in np.percentile(top[ok] / bottom[ok], PCT)]


def signflip_p(diffs: list) -> float:
    """Rule 3: the exact two-sided sign-flip test on per-question differences (Fractions). Under no difference each
    nonzero difference is as likely positive as negative; P = the share of the 2^m sign patterns whose sum is at least
    as far from 0 as the one observed, enumerated by convolution on the differences scaled to whole numbers."""
    nz = [Fraction(x) for x in diffs if x != 0]
    if not nz:
        return 1.0
    L = math.lcm(*[x.denominator for x in nz])
    v = [abs(int(x * L)) for x in nz]
    obs = abs(sum(int(x * L) for x in nz))
    dist = {0: 1}
    for x in v:
        new = defaultdict(int)
        for s, k in dist.items():
            new[s + x] += k
            new[s - x] += k
        dist = new
    return float(Fraction(sum(k for s, k in dist.items() if abs(s) >= obs), 2 ** len(v)))


def zero_bound(n: int) -> float:
    """Rule 9: a zero's one-sided 95% upper bound over n questions, 1 - 0.05^(1/n) (0 of 39: 7.4%)."""
    return 1 - 0.05 ** (1 / n)


def full_bound(n: int) -> float:
    """O2 (Valerio, 24 October), the mirror of zero_bound: a rate of 100%'s one-sided 95% lower bound over n
    questions, 0.05^(1/n) (39 of 39: 92.6%)."""
    return 0.05 ** (1 / n)


def one_sided(row: dict) -> bool:
    """A Source Data margin row whose bar is a one-sided bound (a 0's upper or a 100%'s lower), drawn dashed. Only
    Fig. 3b's 'refusal' rows carry these columns; a's 'strategy' rows have none, so their bars are never dashed."""
    return (row.get("zero_one_sided_upper_bound_pct") is not None
            or row.get("full_one_sided_lower_bound_pct") is not None)


def shares(cells, qids, draws, t, failures_as_fail=True):
    """{config: {question: (Fraction p or None, {draw: 1, 0 or None})}}: per question its pass share over the draws
    with a measurement (Rule 2, Rule 10: a failed answer counts as a fail, or is left out in the sensitivity run)."""
    out = {}
    for c in CONFIGS:
        out[c] = {}
        for q in qids:
            k = n = 0
            per = {}
            for d in draws:
                cell = cells[(c, q, d)]
                if cell["kind"] == "scored":
                    hit = int(cell["score"] >= t)
                    k, n, per[d] = k + hit, n + 1, hit
                elif cell["kind"] == "failed" and failures_as_fail:
                    n, per[d] = n + 1, 0
                else:
                    per[d] = None
            out[c][q] = (Fraction(k, n) if n else None, per)
    return out


def summarise(sh, qids, draws):
    """Per config: the rate (mean of p over the questions with one), exact as a Fraction (rate_x: ranks, ties and
    Rule 6 compare these, so two equal rates are equal; review of 18 October, defect 2) and as a float; Rule 2's
    interval, n, each draw's rate."""
    res = {}
    for c in CONFIGS:
        ps = [sh[c][q][0] for q in qids]
        num = [float(p) if p is not None else 0.0 for p in ps]
        den = [1.0 if p is not None else 0.0 for p in ps]
        have = [p for p in ps if p is not None]
        n = len(have)
        rate_x = sum(have, Fraction(0)) / n if n else None
        lo, hi = interval(num, den) if n else (None, None)
        per = {}
        for d in draws:
            v = [sh[c][q][1][d] for q in qids if sh[c][q][1][d] is not None]
            per[d] = (sum(v) / len(v) if v else None, len(v))
        res[c] = {"rate": None if rate_x is None else float(rate_x), "rate_x": rate_x, "lo": lo, "hi": hi,
                  "questions_with_share": n, "per_draw": per,
                  "zero_bound": zero_bound(n) if n and rate_x == 0 else None,
                  "full_bound": full_bound(n) if n and rate_x == 1 else None}
    return res


def pairs(sh, qids):
    """Rule 3 on all 15 pairs (in G1's order, A before B): d, its Rule 2 interval, the exact P."""
    out = {}
    for a, b in combinations(CONFIGS, 2):
        diffs, num, den = [], [], []
        for q in qids:
            pa, pb = sh[a][q][0], sh[b][q][0]
            if pa is None or pb is None:
                num.append(0.0)
                den.append(0.0)
                continue
            diffs.append(pa - pb)
            num.append(float(pa - pb))
            den.append(1.0)
        n = len(diffs)
        dx = sum(diffs, Fraction(0)) / n if n else None
        lo, hi = interval(num, den) if n else (None, None)
        out[(a, b)] = {"d": None if dx is None else float(dx), "d_x": dx, "lo": lo, "hi": hi, "p": signflip_p(diffs),
                       "questions": n,
                       "a_higher": sum(1 for x in diffs if x > 0), "b_higher": sum(1 for x in diffs if x < 0)}
    return out


def pair(pr, a, b):
    """The pair (a, b) whichever order it is stored in, as a minus b."""
    if (a, b) in pr:
        return pr[(a, b)]
    x = pr[(b, a)]
    return {**x, "d": None if x["d"] is None else -x["d"], "d_x": None if x["d_x"] is None else -x["d_x"],
            "lo": None if x["hi"] is None else -x["hi"],
            "hi": None if x["lo"] is None else -x["lo"], "a_higher": x["b_higher"], "b_higher": x["a_higher"]}


def rule6(summ, pr, which):
    """Rule 6: the strategy first (last) by mean, whether ties share that place, and whether Rule 3's test separates
    it from every other at P < ALPHA in its favour; the members it cannot be told apart from."""
    sign = 1 if which == "highest" else -1
    rates = {c: summ[c]["rate_x"] for c in CONFIGS if summ[c]["rate_x"] is not None}
    best = max(rates.values()) if sign == 1 else min(rates.values())
    firsts = [c for c, r in rates.items() if r == best]
    top = firsts[0]
    apart, not_apart = [], []
    for o in CONFIGS:
        if o == top:
            continue
        x = pair(pr, top, o)
        ok = x["d_x"] is not None and sign * x["d_x"] > 0 and x["p"] < ALPHA
        (apart if ok else not_apart).append(o)
    return {"strategy": top, "tied_with": firsts[1:], "met": len(firsts) == 1 and not not_apart,
            "separated_from": apart, "not_separated_from": not_apart}


def verdict(claim, summ, pr, r6):
    """Rule 11's table: holds, weakens or reverses. Highest or lowest: holds when Rule 6 is met; weakens when the
    strategy is first (last) by mean, alone or shared, and Rule 6 is not met (a shared place cannot meet it);
    reverses when another strategy is first (last). A paired direction (Rule 3): holds in the claimed direction with
    P < 0.05; weakens in that direction with P >= 0.05, and at a difference of exactly 0 (S393's v_better; Q4);
    reverses in the opposite direction, whatever its P. Differences are compared exact (Fractions)."""
    _, _, kind, a, b, _ = claim
    if kind in ("highest", "lowest"):
        r = r6[kind]
        if r["strategy"] == a and not r["tied_with"]:
            return "holds" if r["met"] else "weakens"
        if a in [r["strategy"]] + r["tied_with"]:
            return "weakens"                       # first (last) by mean, shared: Rule 6 cannot be met
        return "reverses"
    x = pair(pr, a, b)
    d = x["d_x"] if kind == "above" else -x["d_x"]
    if d < 0:
        return "reverses"
    return "holds" if d > 0 and x["p"] < ALPHA else "weakens"   # S393 v_better: no difference is "weakens"


FLIPPED = [c for c in CONFIGS if c != "single_pass"]      # panel c: each strategy set against single pass


def flips(sh, pr, qids, draws):
    """Rule 4 (LIST.md:268-292), each strategy against single pass on the answerable questions. Every single-pass draw
    of a question is set against every draw of the other strategy (with three draws, 9 pairings; Rule 1: draws are
    not paired by their number). With pass shares s (single pass) and v (the strategy) over the draws measured, a
    question gives s(1 - v) harmed pairings (single pass passes, the strategy fails), (1 - s)v helped ones and s
    correct at baseline, each as a share of its pairings, so the sums over questions are the mean over the pairings of
    the number of questions harmed (helped); on one draw they are the counts of the 2 x 2 table (15 against 4 in
    S04a). Harmful share of changed outcomes = sum s(1 - v) / sum [s(1 - v) + (1 - s)v]; share of initially correct
    answers degraded = sum s(1 - v) / sum s; both with the Rule 2 interval (the same resamples); P = Rule 3's P for
    the pair. Also (Rule 4 (a)) each draw's 2 x 2 table, draw d against draw d, and their totals over the draws.
    A question without a share in either strategy is left out of every sum."""
    out = {}
    for c in FLIPPED:
        harm = helped = base = Fraction(0)
        n_h, d_ch, d_b = [], [], []
        n = 0
        for q in qids:
            s, v = sh["single_pass"][q][0], sh[c][q][0]
            if s is None or v is None:
                n_h.append(0.0), d_ch.append(0.0), d_b.append(0.0)
                continue
            h, g = s * (1 - v), (1 - s) * v
            harm, helped, base, n = harm + h, helped + g, base + s, n + 1
            n_h.append(float(h)), d_ch.append(float(h + g)), d_b.append(float(s))
        per = {}
        for d in draws:
            t = Counter()
            for q in qids:
                a, b = sh["single_pass"][q][1][d], sh[c][q][1][d]
                if a is not None and b is not None:
                    t[(a, b)] += 1
            per[d] = {"both_pass": t[(1, 1)], "harmed": t[(1, 0)], "helped": t[(0, 1)], "both_fail": t[(0, 0)]}
        ch = harm + helped
        lo_s, hi_s = interval(n_h, d_ch) if ch else (None, None)
        lo_b, hi_b = interval(n_h, d_b) if base else (None, None)
        out[c] = {"harmed": float(harm), "harmed_x": harm, "helped": float(helped), "helped_x": helped,
                  "baseline_correct": float(base), "changed": float(ch), "questions": n,
                  "harm_share": float(harm / ch) if ch else None, "harm_share_lo": lo_s, "harm_share_hi": hi_s,
                  "degraded_share": float(harm / base) if base else None, "degraded_lo": lo_b, "degraded_hi": hi_b,
                  "p": pair(pr, "single_pass", c)["p"], "per_draw": per,
                  "same_draw_harmed": sum(x["harmed"] for x in per.values()),
                  "same_draw_helped": sum(x["helped"] for x in per.values())}
    return out


def self_flips(sh, qids, draws):
    """Rule 4 (b), the noise baseline, within each strategy: the share of pairs of draws of one question that disagree
    (k passes of n measured draws give k(n - k) disagreeing pairs of n(n - 1)/2), and per ordered pair of distinct
    draws (d, d') the questions that pass on d and fail on d' (both measured). Panel c's reference band is single
    pass's: from the least to the most of those counts over its ordered pairs (6 with three draws), each one a count
    of questions 'harmed' by rerunning single pass, in the units of the strategies' points. None with one draw."""
    from itertools import permutations
    out = {}
    for c in CONFIGS:
        dis = pairs_n = 0
        for q in qids:
            hits = [sh[c][q][1][d] for d in draws if sh[c][q][1][d] is not None]
            k, n = sum(hits), len(hits)
            dis, pairs_n = dis + k * (n - k), pairs_n + n * (n - 1) // 2
        ordered = {f"{d}>{e}": sum(1 for q in qids if sh[c][q][1][d] == 1 and sh[c][q][1][e] == 0)
                   for d, e in permutations(draws, 2)}
        v = list(ordered.values())
        out[c] = {"disagree_share": dis / pairs_n if pairs_n else None, "disagreeing_pairs": dis,
                  "draw_pairs": pairs_n, "ordered": ordered,
                  "ordered_mean": sum(v) / len(v) if v else None, "ordered_min": min(v) if v else None,
                  "ordered_max": max(v) if v else None}
    return out


def compute(cells, groups, draws, failures_as_fail=True):
    """Everything one reading gives, at each threshold."""
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    qn = sorted(q for q, g in groups.items() if g == "not_answerable")
    qf = sorted(q for q, g in groups.items() if g == "false_premise")
    out = {"answerable": {}, "refusal": {}, "false_premise": {}, "rule6": {}, "verdicts": {}, "flips": {},
           "self_flips": {}}
    # refusal: Rule 9 defines refused at refusal accuracy 3 or more only (Rule 5's second threshold is for
    # pass-based statistics), so it is read at REFUSAL_T alone
    shn = shares(cells, qn, draws, REFUSAL_T, failures_as_fail)
    summ_n, pr_n = summarise(shn, qn, draws), pairs(shn, qn)
    out["refusal"][REFUSAL_T] = {"summary": summ_n, "pairs": pr_n, "shares": shn,
                                 "rule6": {w: rule6(summ_n, pr_n, w) for w in ("highest", "lowest")}}
    for t in THRESHOLDS:
        sh = shares(cells, qa, draws, t, failures_as_fail)
        summ, pr = summarise(sh, qa, draws), pairs(sh, qa)
        r6 = {w: rule6(summ, pr, w) for w in ("highest", "lowest")}
        out["answerable"][t] = {"summary": summ, "pairs": pr, "shares": sh}
        out["flips"][t] = flips(sh, pr, qa, draws)
        out["self_flips"][t] = self_flips(sh, qa, draws)
        out["rule6"][t] = r6
        out["verdicts"][t] = {cl[0]: verdict(cl, summ, pr, r6) for cl in CLAIMS if cl[5] == "answerable"}
        if t == REFUSAL_T:
            out["verdicts"][t].update({cl[0]: verdict(cl, summ_n, pr_n, out["refusal"][t]["rule6"])
                                       for cl in CLAIMS if cl[5] == "refusal"})
        else:
            out["verdicts"][t].update({cl[0]: None for cl in CLAIMS if cl[5] == "refusal"})
        fp = {}
        for c in CONFIGS:
            per_q, per_d = {}, {}
            for q in qf:
                hits = []
                for d in draws:
                    cell = cells[(c, q, d)]
                    if cell["kind"] == "scored":
                        hits.append(int(cell["score"] >= t))
                    elif cell["kind"] == "failed" and failures_as_fail:
                        hits.append(0)
                    else:
                        hits.append(None)
                per_q[q] = hits
            for i, d in enumerate(draws):
                v = [per_q[q][i] for q in qf if per_q[q][i] is not None]
                per_d[d] = (sum(v), len(v))
            allv = [h for q in qf for h in per_q[q] if h is not None]
            fp[c] = {"passed": sum(allv), "answers": len(allv), "per_draw": per_d, "per_question": per_q}
        out["false_premise"][t] = fp
    return out


COST_MEASURES = (("calls", "model calls per answer"), ("clock_s", "clock time per answer (s)"),
                 ("clock_less_wait_s", "clock time less the wait for the local server (s)"),
                 ("wait_s", "wait for the local server (s)"), ("tokens", "tokens per answer"),
                 ("model_s", "model-call time per answer (s)"))


def cost_summary(cells, groups, draws):
    """Panel d's x and the times beside it, from each answer's generation record (S457.exp01_row): model calls = the
    number of entries in generation.calls; clock time = generation.latency_s; the wait = the sum of the calls'
    waited_for_server_s (only verified pass's verifier waits, D95 Q200). Every answer of the draws read counts, a
    failed one included (its calls and time were spent). Per question the mean over its draws, then the mean over the
    questions, with Rule 2's interval (the same resamples of the group's questions as the pass rates). Tokens also have
    their median over the questions (fig3.md R7). Tokens = generation.tokens_used, and model-call time = the sum of the
    calls' wall_s (S457.exp01_row reads both). Read on the 86 answerable questions (panel d's y is the pass rate on them)
    and on all 135 (the letter's cost numbers are over every question, S77 n_rows); and RLM-10 over single pass on each."""
    out = {}
    for grp, qids in (("answerable", sorted(q for q, g in groups.items() if g == "answerable")),
                      ("all", sorted(groups))):
        out[grp] = {}
        for c in CONFIGS:
            row = {"questions": len(qids)}
            for m, _ in COST_MEASURES:
                perq = []
                for q in qids:
                    v = [cells[(c, q, d)]["cost"][m] for d in draws if "cost" in cells[(c, q, d)]]
                    if len(v) != len(draws):
                        raise Refused(f"{LABEL[c]} {q}: {len(v)} of {len(draws)} answers carry a generation record")
                    perq.append(sum(v) / len(v))
                lo, hi = interval(perq, [1.0] * len(perq))
                row[m] = {"mean": sum(perq) / len(perq), "lo": lo, "hi": hi}
                if m == "tokens":
                    row[m]["median"] = float(sorted(perq)[len(perq) // 2] if len(perq) % 2 else
                                             (sorted(perq)[len(perq) // 2 - 1] + sorted(perq)[len(perq) // 2]) / 2)
            out[grp][c] = row
        out[grp]["ratio_rlm10_single"] = {m: out[grp]["rlm_10"][m]["mean"] / out[grp]["single_pass"][m]["mean"]
                                          for m in ("calls", "clock_s")}
    return out


# The letter's cost numbers (Reviewer 4, Question 2, "We now report compute accounting": 5.87 calls against 1.00,
# 82.4 s against 10.4; the Discussion's "six times the model calls and eight times the wall-clock time"), from the
# artifact the letter cites, findings/recompute/S77_r2q2_cost.json (read by S457.s77_values()): reproduced before
# anything is written, then set against G1's records in claims.md (C22, C47).
S77_PRINTED = {("rlm_10", "llm_calls", 2): "5.87", ("single_pass", "llm_calls", 2): "1.00",
               ("rlm_10", "latency_s", 1): "82.4", ("single_pass", "latency_s", 1): "10.4"}
S77_RATIO_WORDS = {"llm_calls": "six times", "latency_s": "eight times"}


OUTCOME_KINDS = {"failed": "failed, counted as fails", "unscored": "judge gave no score, left out",
                 "google_scored": "stopped by Google, scored as written",
                 "returned_scored": "a Gemini reply returned with its status, scored as written",
                 "cut_scored": "cut, scored as written"}


def outcomes(cells, groups):
    """Rule 10's table: per strategy, with the answer keys of each row,
      failed           the answers with no text or a generation error (judge no_answer), by stop reason; an answer
                       with a block or a recitation stop among its Gemini calls is "stopped by Google (<statuses>)"
                       (Rule 10, D83 Q145, D89: grouped, each status shown);
      unscored         the judge calls that gave no score, by judge status;
      google_scored    answers with text whose calls hold a block or a recitation stop (D90 Q1: a recitation stop
                       passes its text on), scored as written and counted here;
      returned_scored  answers with text whose calls hold another returned status (empty, malformed, the D92 Q188
                       reasons), scored as written, the status recorded (D90 Q2);
      cut_scored       answers with text cut by a limit (max_turns_partial, length), scored as written."""
    t = {c: {k: defaultdict(list) for k in OUTCOME_KINDS} for c in CONFIGS}
    for (c, q, d), cell in sorted(cells.items()):
        ret = cell.get("returned") or []
        google = [x for x in ret if x in GOOGLE_STOP]
        if cell["kind"] == "failed":
            sr = cell.get("stop_reason") or "(stop reason not read)"
            if google:
                sr = f"stopped by Google ({', '.join(google)}; stop reason {sr})"
            elif ret:
                sr = f"{sr} (call statuses {', '.join(ret)})"
            t[c]["failed"][sr].append(cell["key"])
        elif cell["kind"] == "unscored":
            t[c]["unscored"][cell["why"]].append(cell["key"])
        elif google:
            t[c]["google_scored"][f"stopped by Google ({', '.join(google)})"].append(cell["key"])
        elif ret:
            t[c]["returned_scored"][", ".join(ret)].append(cell["key"])
        elif cell.get("stop_reason") in CUT:
            t[c]["cut_scored"][cell["stop_reason"]].append(cell["key"])
    return {c: {k: dict(v) for k, v in x.items()} for c, x in t.items()}


# ---------------------------------------------------------------------------------------------------------------
# old panel b, now rows of sheet Fig. 3a and not drawn; 'panel b' below means it: concept recall (plan row L3, S471), read from its rows and regenerated from the records before it is used
# ---------------------------------------------------------------------------------------------------------------
# A cell holds two measures: "value", the reading's headline concept recall (L3: D12's loose matcher; L3_d181: D181's
# reading), and "exact", D12's rule 1 (the exact substring test) on the same key's concepts, every concept counted
CR_MEASURES = ("value", "exact")
CR_FIELDS = ("n_concepts", "found_loose", "found_exact", "concept_recall_loose", "concept_recall_exact", "found_by",
             "note_removed", "scored_text_sha256")
# D188 (Valerio, 31 October): panel b draws D181's reading on key v2.5, findings/recompute/L3_d181 (S471 --d181), the
# folder Figure 5 reads since D186 (4); both files pinned as S497 pins them (scripts/S497_fig5_d166.py L3_D181_SHA256)
L3_D181 = ROOT / "findings" / "recompute" / "L3_d181"
L3_D181_SHA256 = {"concept_recall.jsonl": "2ce0985ee014cf33f84417410282271b518c06a220138d2d6f67145c539e6371",
                  "header.json": "6a3fea6221df0142be83c1ec51e765bbac37dc10a63ca246385ad8994673fc9e"}
L3_SHA256 = "56f0f23b3415169a2ec5a79f6fb9cbf427939054279b9ebc32b21cf07c6e2f36"   # findings/recompute/L3/concept_recall.jsonl
# The locked v2.4 anchor (README.md:75-79): panel b as committed before D188 (findings/figures_provisional/fig2_ranking/
# ranking.json at 56478637, sheet "Fig. 2b", the six "strategy" rows), L3's loose matcher on key v2.4, draws 1 to 3:
# concept_recall_loose_pct, ci95_lo_pct, ci95_hi_pct, concept_recall_exact_pct, answers_failed_scored_0
CR_ANCHOR_V24 = {"single_pass": (71.242617202, 65.701088963, 76.835628922, 28.200442968, 0),
                 "multi_hop": (52.44416759, 46.972499077, 58.009563031, 20.622923588, 0),
                 "verified_pass": (71.015596161, 65.596126338, 76.460432817, 28.952104097, 1),
                 "rlm_5": (78.803063861, 74.517303433, 82.89697536, 38.676172019, 1),
                 "rlm_10": (79.694075305, 75.833241048, 83.367086563, 37.696566999, 1),
                 "rlm_20": (78.223514212, 74.231231543, 82.095837948, 38.491140642, 0)}
READING_TEXT = {"loose": "L3's loose matcher (D12, scripts/concept_match_loose.py) on key v2.4",
                "D181": "D181's reading on key v2.5: S505's loose matcher with the question rule, Q-need, reading (b) "
                        "(findings/recompute/L3_d181, S471 --d181)"}


def s471_module():
    import S471_l3_concept_recall as S471
    return S471


def read_concept_recall(path: Path, answers: dict, groups: dict, draws: list[int]) -> dict:
    """Plan row L3's concept recall (scripts/S471_l3_concept_recall.py: one row per G1 answer, D12's loose matcher,
    provisional, D114 Q37 O-a), used for panel b only after three checks; any failure is a refusal, nothing written.
      (1) S471's own gate: its score() on S432's 107 completed answers gives S432's stored values (the known value).
      (2) Every row of the draws read is there once, in the D5 key's group (Rule 8: null and "not applicable" on the
          39), and is the answer this script read and S3 judged: its answer_sha256 and status are those of the
          generation record read here (--answers, the reruns' copy over K1's).
      (3) Regenerated from that record: S471.score(the record's answer, the key's concepts, the record's turn-limit
          flag) gives the row's counts, values, per-concept matches, note removal and scored-text sha256 exactly.
    A value is the row's count over its concepts, kept exact (found / n_concepts as a Fraction; the stored
    concept_recall_loose is that rounded to 4 decimals, checked). An empty answer (a failure, Rule 10) is scored 0 by
    S471 and stays in every mean."""
    S471 = s471_module()
    path = Path(path).expanduser().resolve()
    head_p = path.parent / "header.json"
    if not path.exists() or not head_p.exists():
        raise Refused(f"--concept-recall {path}: the rows and a header.json beside them are needed (S471's output)")
    head = json.loads(head_p.read_text())
    if head.get("plan_row") != "L3" or head.get("script") != "scripts/S471_l3_concept_recall.py":
        raise Refused(f"{head_p}: not S471's L3 header (plan_row {head.get('plan_row')!r})")
    key = S471.S470.the_key()
    if head.get("key", {}).get("sha256") != key["sha256"]:
        raise Refused(f"{head_p}: scored on key {str(head.get('key', {}).get('sha256'))[:12]}, not the D5 key "
                      f"{key['sha256'][:12]}")
    try:
        g = S471.gate(key)                               # (1): S432's 107 values must reproduce
    except S471.GateFail as e:
        raise Refused(f"--concept-recall: S471's gate does not reproduce S432: {e}; nothing written") from None
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    by, twice = {}, []
    for r in rows:
        k = r["answer_key"]
        if k in by:
            twice.append(k)
        by[k] = r
    if twice:
        raise Refused(f"{path}: {len(twice)} answers have two rows ({twice[:2]})")
    cells, bad, missing = {}, [], []
    for c in CONFIGS:
        for q, grp in sorted(groups.items()):
            for d in draws:
                k = f"{INDEX}|{c}|{q}|d{d}"
                r, a = by.get(k), answers.get(k)
                if r is None or a is None:
                    missing.append(k)
                    continue
                if (r["config"], r["question_id"], r["draw"], r["group"]) != (c, q, d, grp):
                    bad.append(f"{k}: row names {r['config']} {r['question_id']} d{r['draw']} {r['group']}")
                    continue
                if (r["answer_sha256"], r["status"]) != (a["answer_sha256"], a["status"]):
                    bad.append(f"{k}: L3 scored another answer than the record read here (answer sha256 "
                               f"{r['answer_sha256'][:12]} against {a['answer_sha256'][:12]}, status {r['status']} "
                               f"against {a['status']})")
                    continue
                if grp == "not_answerable":
                    if r.get("reason") != "not applicable" or r.get("concept_recall_loose") is not None:
                        bad.append(f"{k}: a not-answerable row holds a value (Rule 8)")
                    continue
                if grp != "answerable":
                    continue                              # the ten false-premise questions: not in panel b
                got = S471.score(a["answer"], key["questions"][q]["expected_concepts"], a["turn_limit_note"])
                want = {f: r.get(f) for f in CR_FIELDS}
                if {f: got[f] for f in CR_FIELDS} != want:
                    diff = [f for f in CR_FIELDS if got[f] != want[f]]
                    bad.append(f"{k}: does not reproduce from its record ({', '.join(diff)})")
                    continue
                n = r["n_concepts"]
                if round(r["found_loose"] / n, 4) != r["concept_recall_loose"]:
                    bad.append(f"{k}: concept_recall_loose {r['concept_recall_loose']} is not {r['found_loose']}/{n}")
                    continue
                cells[(c, q, d)] = {"key": k, "failed": a["status"] != "ok", "n": n,
                                    "empty": not a["answer"].strip(), "note_removed": bool(r["note_removed"]),
                                    "value": Fraction(r["found_loose"], n), "exact": Fraction(r["found_exact"], n)}
    if missing:
        raise Refused(f"--concept-recall: {len(missing)} answers of the draws read have no row ({missing[:2]})")
    if bad:
        raise Refused(f"--concept-recall: {len(bad)} rows refused, nothing written; first: {bad[0]}")
    return {"cells": cells, "rows": by, "header_doc": head, "reading": "loose", "path": label(path),
            "sha256": sha256_file(path), "header": label(head_p),
            "header_sha256": sha256_file(head_p), "written_utc": head.get("written_utc"),
            "provisional": bool(head.get("provisional")), "matcher": head.get("matcher"),
            "gate": f"S471's gate: S432 reproduced on {g['reproduced']} completed answers",
            "regenerated": sum(1 for _ in cells), "failed": sorted(v["key"] for v in cells.values() if v["failed"])}


CR_INFO_DROP = ("cells", "rows", "header_doc")         # read_concept_recall's parts that ranking.json does not keep


def check_cr_anchor(lo: dict, cr: dict, draws: list[int]) -> str | None:
    """README.md:75-79, D188: panel b on L3's loose reading (compute_cr of read_concept_recall's cells) gives the
    committed v2.4 panel b, CR_ANCHOR_V24, value for value as cr_rows writes them (r9 of the percentages, the failed
    answers counted). Applies to the committed L3 rows (sha256 L3_SHA256) on draws 1 to 3; any other input (the
    fixture, a single draw) returns None, and the caller records that no anchor applied."""
    if cr["sha256"] != L3_SHA256 or draws != [1, 2, 3]:
        return None
    vs, es = lo["value"]["summary"], lo["exact"]["summary"]
    got = {c: (r9(100 * vs[c]["rate"]), r9(100 * vs[c]["lo"]), r9(100 * vs[c]["hi"]), r9(100 * es[c]["rate"]),
               len(lo["failed"][c])) for c in CONFIGS}
    if got != CR_ANCHOR_V24:
        diff = [c for c in CONFIGS if got[c] != CR_ANCHOR_V24[c]]
        raise Refused(f"panel b's v2.4 anchor not reproduced: L3's loose reading gives {got[diff[0]]} for {diff[0]}, "
                      f"the committed panel b {CR_ANCHOR_V24[diff[0]]} ({len(diff)} of 6 strategies differ); nothing "
                      f"written")
    return ("panel b's v2.4 anchor: L3's loose reading gives the committed panel b (ranking.json at 56478637) on all "
            "6 strategies (mean, interval, exact value, failed answers)")


def read_concept_recall_d181(folder: Path, cr: dict, groups: dict, draws: list[int],
                             pins: dict | None = None) -> dict:
    """D188: D181's reading (S471 --d181) of the answers L3 scored, checked as S497.read_l3_d181 checks it (D186 (4))
    and read into read_concept_recall's cell shape. cr is read_concept_recall's result (L3, already reproduced from the
    records). Refused, nothing written, unless:
      (1) pins (default L3_D181_SHA256 for findings/recompute/L3_d181; another folder is read with pins=None and its
          sha256 recorded) give both files' sha256;
      (2) the header is S471's, plan row L3, reading D181, provisional false, key v2.5 (S512.KEY25_SHA256), on the same
          answer copy as L3 (inputs manifest_sha256), and its counts are the rows' (rows, scored, status, groups);
      (3) the rows are L3's answers one for one (answer key, config, question, draw, group, status, answer sha256);
      (4) on the questions whose expected_concepts v2.5 left unchanged (S512.keys) each scored row's D12 loose base
          (concept_recall_loose_base, found_loose_base, n_concepts) is L3's loose value of that answer;
      (5) every answerable row of the draws read has a value: concept_recall is found / n_counted to 4 decimals and
          n_counted is at least 1.
    A cell's "value" is found / n_counted (D181: a concept made only of question words leaves the denominator) and its
    "exact" found_exact_base / n_concepts (D12's exact substring test on the v2.5 concepts, every concept counted)."""
    folder = Path(folder).expanduser().resolve()
    if pins is None and folder == L3_D181.resolve():
        pins = L3_D181_SHA256
    files = {n: folder / n for n in ("concept_recall.jsonl", "header.json")}
    for n, f in files.items():
        if not f.exists():
            raise Refused(f"--concept-recall-d181 {folder}: {n} is missing; nothing written")
        if pins is not None and sha256_file(f) != pins[n]:
            raise Refused(f"{n} of {folder.name} is {sha256_file(f)[:12]}, not the {pins[n][:12]} pinned (D188); "
                          f"nothing written")
    hdr = json.loads(files["header.json"].read_text())
    S512 = JR.S512
    want = {"script": "scripts/S471_l3_concept_recall.py", "plan_row": "L3", "reading": "D181", "provisional": False}
    got_h = {k: hdr.get(k) for k in want}
    l3_man = (cr["header_doc"].get("inputs") or {}).get("manifest_sha256")
    if got_h != want or (hdr.get("key") or {}).get("sha256") != S512.KEY25_SHA256 or l3_man is None or \
            (hdr.get("inputs") or {}).get("manifest_sha256") != l3_man:
        raise Refused(f"{folder.name}/header.json is not S471's final D181 reading of L3's answers on key v2.5 "
                      f"({got_h}, key {str((hdr.get('key') or {}).get('sha256'))[:12]}); nothing written")
    rows = [json.loads(x) for x in files["concept_recall.jsonl"].read_text().splitlines() if x.strip()]
    cnt = hdr.get("counts") or {}
    got = {"rows": len(rows), "scored": sum(1 for r in rows if r.get("group") != "not_answerable"),
           "status_scored": dict(Counter(r["status"] for r in rows if r.get("group") != "not_answerable")),
           "by_group": dict(Counter(r["group"] for r in rows))}
    if got != {k: cnt.get(k) for k in got}:
        raise Refused(f"{folder.name}: the rows give {got}, the header {({k: cnt.get(k) for k in got})}; nothing written")
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}
    l3 = cr["rows"]
    by, held, bad = {}, 0, []
    for r in rows:
        k = r.get("answer_key")
        a = l3.get(k)
        if k in by or a is None or any(r.get(f) != a.get(f) for f in ("config", "question_id", "draw", "group",
                                                                         "status", "answer_sha256")):
            bad.append(f"{k}: not L3's answer one for one")
            continue
        by[k] = r
        if r["group"] != "not_answerable" and r["question_id"] in same_c:
            if (r.get("concept_recall_loose_base"), r.get("found_loose_base"), r.get("n_concepts")) != \
                    (a.get("concept_recall_loose"), a.get("found_loose"), a.get("n_concepts")):
                bad.append(f"{k}: the loose base on concepts v2.5 left unchanged is not L3's loose value")
                continue
            held += 1
    if bad or set(by) != set(l3):
        raise Refused(f"{folder.name}: {len(bad)} rows refused (first: {bad[:1]}), {len(set(l3) - set(by))} of L3's "
                      f"answers missing; nothing written")
    cells, bad = {}, []
    for (c, q, d), old in cr["cells"].items():
        r = by[old["key"]]
        n, nc, f = r.get("n_counted"), r.get("n_concepts"), r.get("found")
        if r.get("concept_recall") is None or not n or f is None or round(f / n, 4) != r["concept_recall"]:
            bad.append(f"{old['key']}: concept_recall {r.get('concept_recall')} is not found {f} over n_counted {n}")
            continue
        cells[(c, q, d)] = {"key": old["key"], "failed": old["failed"], "n": n, "empty": bool(r.get("empty_text")),
                            "note_removed": bool(r.get("note_removed")), "value": Fraction(f, n),
                            "exact": Fraction(r["found_exact_base"], nc)}
    if bad:
        raise Refused(f"{folder.name}: {len(bad)} answerable rows of the draws read have no D181 value, first: "
                      f"{bad[0]}; nothing written")
    nq = len({q for q in same_c if groups.get(q) not in (None, "not_answerable")})
    return {"cells": cells, "reading": "D181", "path": label(files["concept_recall.jsonl"]),
            "sha256": sha256_file(files["concept_recall.jsonl"]), "header": label(files["header.json"]),
            "header_sha256": sha256_file(files["header.json"]), "pinned": pins is not None,
            "written_utc": hdr.get("written_utc"), "provisional": bool(hdr.get("provisional")),
            "matcher": hdr.get("matcher"), "key": hdr.get("key"),
            "gate": (f"L3_d181 held to L3: {'both files at their pinned sha256, ' if pins is not None else ''}the header "
                     f"S471's final D181 reading on key v2.5 of L3's answer copy, its {len(by):,} rows L3's answers "
                     f"one for one, and on the {nq} scored questions (answerable and false premise) whose concepts "
                     f"v2.5 left unchanged the loose base of {held:,} scored rows equal to L3's loose value"),
            "regenerated": 0, "failed": cr["failed"]}


def compute_cr(cr: dict, groups: dict, draws: list[int]) -> dict:
    """Panel b on the 86 answerable questions, each measure (value, exact): per question the mean of its draws' values
    (Rule 2; every answer has a value, a failed one 0), the summary as summarise() gives it (mean over questions,
    Rule 2 interval, each draw's mean); for the headline value, all 15 pairs by Rule 3 on per-question means and Rule
    6's highest and lowest (Rule 6: "For a continuous signal (concept recall), Rule 3's test runs on per-question
    means of the signal")."""
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    out = {}
    for m in CR_MEASURES:
        sh = {}
        for c in CONFIGS:
            sh[c] = {}
            for q in qa:
                per = {d: cr["cells"][(c, q, d)][m] for d in draws}
                sh[c][q] = (sum(per.values(), Fraction(0)) / len(draws), per)
        summ = summarise(sh, qa, draws)
        out[m] = {"summary": summ, "shares": sh}
        if m == "value":
            pr = pairs(sh, qa)
            out[m]["pairs"] = pr
            out[m]["rule6"] = {w: rule6(summ, pr, w) for w in ("highest", "lowest")}
    out["failed"] = {c: sorted(v["key"] for (cc, q, d), v in cr["cells"].items() if cc == c and v["failed"]
                               and groups[q] == "answerable") for c in CONFIGS}
    # what the legend counts (22 Oct review): answers with no text (scored 0 by S471), and RLM answers scored with
    # Mentori's fixed turn-limit note removed (D115 L1e O-a), each over the answerable answers of the draws read
    out["empty"] = sum(1 for (cc, q, d), v in cr["cells"].items() if v["empty"] and groups[q] == "answerable")
    out["note_removed"] = sum(1 for (cc, q, d), v in cr["cells"].items() if v["note_removed"]
                              and groups[q] == "answerable")
    return out


def reproduce():
    """Reproduce before writing (README.md:75-79): the sign-flip test on S04a's two tables gives S04a's exact P
    values; the resample counts equal S407's own (or S457's matrix when S407 does not import)."""
    j = json.loads(S04A.read_text())["part1_verified_vs_single"]
    done = []
    for t in ("threshold_3", "threshold_4"):
        x = j[t]
        c = x["contingency"]
        diffs = [1] * c["CI"] + [-1] * c["IC"] + [0] * (c["CC"] + c["II"])
        got = signflip_p(diffs)
        if got != x["mcnemar_exact_p"]:
            raise Refused(f"reproduce: the sign-flip test gives {got!r} on S04a {t} ({c['CI']} against {c['IC']}), "
                          f"S04a stored {x['mcnemar_exact_p']!r}; nothing written")
        done.append(f"S04a {t}: {c['CI']} against {c['IC']}, P {got!r}")
    import numpy as np
    # the committed reference: S457's boot_matrix (tracked; scripts/S457_fig2_panels.py:413-415 at HEAD), counted
    # per question here; S407 (scripts/S407_strategy_contrasts_v24.py, committed f5470b4c) is compared as well when
    # it imports, never alone
    refs = [("S457.boot_matrix", lambda n: np.stack([np.bincount(r, minlength=n) for r in S457.boot_matrix(n)])
             .astype(float))]
    try:
        spec = importlib.util.spec_from_file_location("S407_ref", ROOT / "scripts" / "S407_strategy_contrasts_v24.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        refs.append(("S407.resample_counts", m.resample_counts))
    except Exception:                                  # noqa: BLE001  S407 does not import; S457 alone then
        pass
    for src, ref in refs:
        for n in (39, 86):
            if not np.array_equal(resample_counts(n), ref(n)):
                raise Refused(f"reproduce: the resample counts for n = {n} differ from {src}; nothing written")
    done.append(f"resample counts for n = 39 and 86 equal to {' and '.join(s for s, _ in refs)} (seed {SEED}, "
                f"{N_BOOT} resamples)")
    t = S457.s77_values()
    got = {k: S457.half_up(t[k[0]][k[1]], k[2]) for k in S77_PRINTED}
    words = {m: S457.printed_as("words", t["ratio"][m]) for m in S77_RATIO_WORDS}
    if got != {k: v for k, v in S77_PRINTED.items()} or words != S77_RATIO_WORDS:
        raise Refused(f"reproduce: S77 gives {got} and {words}, the letter prints {S77_PRINTED} and {S77_RATIO_WORDS}; "
                      f"nothing written")
    done.append("the letter's cost numbers from S77 (" + ", ".join(f"{k[0]} {k[1]} {v}" for k, v in got.items())
                + f"; RLM-10 over single pass {words['llm_calls']} the calls, {words['latency_s']} the time)")
    return done


# ---------------------------------------------------------------------------------------------------------------
# tables: Source Data rows, ranking.json, the report
# ---------------------------------------------------------------------------------------------------------------
def r9(x, nd=9):
    return None if x is None else round(float(x), nd)


GROUP_KIND = "strategy, question group"                  # Fig. 3a: one row's rate on one-paper or many-paper questions
CR_NOT_DRAWN = "concept recall (not drawn)"              # Fig. 3a: old panel b's rows (plan_final.json dropped list)
MULT_KIND = "multiple"                                   # Fig. 3d: a strategy's ratios to single pass
CROSS_KIND = "matched budget cross"                      # Fig. 3d: G2's calls and pass rate on the 86
GROUP_D_KIND = "strategy, question group (plotted)"      # Fig. 3d (D216): a strategy's mark per question group
DRAWN_IN = "drawn_in"                                    # Fig. 3a's rate rows: where the plate draws the rate (D216)
S5_SHEET = {"a": "Supplementary Fig. 16a", "b": "Supplementary Fig. 16b"}


def cr_rows(crx, draws):
    """Sheet Fig. 3a's concept-recall rows: per strategy the plotted concept recall (the reading crx holds: D181's on key v2.5 since D188) on the
    86 answerable questions with its Rule 2 interval, D12's exact-substring value on the same key's concepts beside it
    and the failed answers in it (scored 0); each draw's mean; all 15 pairs (Rule 3 on per-question means,
    unadjusted)."""
    rows = []
    lo_s, ex_s = crx["res"]["value"]["summary"], crx["res"]["exact"]["summary"]
    for c in CONFIGS:
        x, e = lo_s[c], ex_s[c]
        rows.append({"row_kind": "strategy", "strategy": c, "strategy_label": LABEL[c], "questions_in_group": 86,
                     "questions_with_a_value": x["questions_with_share"], "draws_read": ",".join(map(str, draws)),
                     "concept_recall_pct": r9(100 * x["rate"]), "ci95_lo_pct": r9(100 * x["lo"]),
                     "ci95_hi_pct": r9(100 * x["hi"]), "interval": "Rule 2 question bootstrap, percentile",
                     "resamples": N_BOOT, "resample_seed": SEED,
                     "concept_recall_exact_pct": r9(100 * e["rate"]), "exact_ci95_lo_pct": r9(100 * e["lo"]),
                     "exact_ci95_hi_pct": r9(100 * e["hi"]),
                     "answers_failed_scored_0": len(crx["res"]["failed"][c]),
                     "answer_keys_failed": "; ".join(crx["res"]["failed"][c]),
                     "reading": READING_TEXT[crx["info"]["reading"]],
                     "rows_written_utc": crx["info"]["written_utc"]})
    for c in CONFIGS:
        for d in draws:
            v, n = lo_s[c]["per_draw"][d]
            ve, _ = ex_s[c]["per_draw"][d]
            rows.append({"row_kind": "draw", "strategy": c, "strategy_label": LABEL[c], "draw": d,
                         "draw_concept_recall_pct": r9(None if v is None else 100 * v),
                         "draw_concept_recall_exact_pct": r9(None if ve is None else 100 * ve), "draw_questions": n})
    for (x1, x2), p in crx["res"]["value"]["pairs"].items():
        rows.append({"row_kind": "pair (unadjusted)", "strategy": x1, "strategy_b": x2,
                     "pair_questions": p["questions"], "questions_a_higher": p["a_higher"],
                     "questions_b_higher": p["b_higher"], "difference_pct_points": r9(100 * p["d"]),
                     "difference_ci95_lo": r9(100 * p["lo"]), "difference_ci95_hi": r9(100 * p["hi"]),
                     "p_two_sided_exact_sign_flip": r9(p["p"], 15), "separated_at_0_05": p["p"] < ALPHA})
    # what the plate draws (D128): each question's value (the grey dots) and each strategy's box over them
    import numpy as np
    sh = crx["res"]["value"]["shares"]
    for c in CONFIGS:
        for q, (v, _) in sh[c].items():
            rows.append({"row_kind": BQ_KIND, "strategy": c, "strategy_label": LABEL[c], "question_id": q,
                         "concept_recall_question_pct": r9(100 * v), "draws_read": ",".join(map(str, draws))})
    for c in CONFIGS:
        v = np.array([100 * float(x) for x, _ in sh[c].values()])
        st = np.percentile(v, [0, 25, 50, 75, 100])
        rows.append({"row_kind": BOX_KIND, "strategy": c, "strategy_label": LABEL[c], "box_questions": len(v),
                     **{k: r9(x) for k, x in zip(("min_pct", "quartile_25_pct", "median_pct", "quartile_75_pct",
                                                  "max_pct"), st)},
                     "quartile_method": "numpy percentile, linear interpolation"})
    return rows


def arm_shares(cells, c, qids, draws, t, failures_as_fail=True):
    """shares() for one arm outside CONFIGS (G2, G6): {question: (Fraction p or None, {draw: 1, 0 or None})}."""
    out = {}
    for q in qids:
        k = n = 0
        per = {}
        for d in draws:
            cell = cells[(c, q, d)]
            if cell["kind"] == "scored":
                hit = int(cell["score"] >= t)
                k, n, per[d] = k + hit, n + 1, hit
            elif cell["kind"] == "failed" and failures_as_fail:
                n, per[d] = n + 1, 0
            else:
                per[d] = None
        out[q] = (Fraction(k, n) if n else None, per)
    return out


def arm_summary(sh_c, qids, draws):
    """summarise() for one arm's shares on qids: the rate, Rule 2's interval, n, each draw's rate."""
    ps = [sh_c[q][0] for q in qids]
    have = [p for p in ps if p is not None]
    n = len(have)
    rate_x = sum(have, Fraction(0)) / n if n else None
    lo, hi = interval([float(p) if p is not None else 0.0 for p in ps],
                      [1.0 if p is not None else 0.0 for p in ps]) if n else (None, None)
    per = {}
    for d in draws:
        v = [sh_c[q][1][d] for q in qids if sh_c[q][1][d] is not None]
        per[d] = (sum(v) / len(v) if v else None, len(v))
    return {"rate": None if rate_x is None else float(rate_x), "rate_x": rate_x, "lo": lo, "hi": hi,
            "questions_with_share": n, "per_draw": per}


def read_g6_clock(path: Path | None, groups: dict, draws: list[int]) -> dict:
    """D218 (2): Zhang RLM-10's clock time per answer, its record's wall_s (the package waits for no local server, so
    its clock time less the wait is wall_s, as S457.load reads it), each answer key's last line. path None: the frozen
    G6 records after the D135 reruns, held to their SOURCE_MTIMES.json sha256. Refuses a (question, draw) of the key
    without a record. Returns {"perq": {q: [s per draw]}, "path", "sha256"}."""
    if path is None:
        base = FR.check_committed(FR.frozen(G6_SET))
        path = base / G6_RUN10 / "answers.jsonl"
        want = json.loads((base / "SOURCE_MTIMES.json").read_text())["files"][
            f"findings/runs/{G6_RUN10}/answers.jsonl"]["sha256"]
        if sha256_file(path) != want:
            raise Refused(f"{path}: not the file its SOURCE_MTIMES.json records ({want[:8]})")
    path = Path(path)
    last = {}
    for raw in path.read_text().splitlines():
        if raw.strip():
            r = json.loads(raw)
            last[r["answer_key"]] = r
    perq, bad = {}, []
    for q in sorted(groups):
        v = []
        for d in draws:
            r = last.get(f"cap10|{q}|d{d}")
            if r is None or r.get("question_id") != q or r.get("draw") != d or not isinstance(r.get("wall_s"), (int, float)):
                bad.append(f"cap10|{q}|d{d}")
                continue
            v.append(float(r["wall_s"]))
        perq[q] = v
    if bad:
        raise Refused(f"read_g6_clock: {len(bad)} Zhang RLM-10 answers have no record with a wall_s, first: {bad[0]}")
    return {"perq": perq, "path": str(path), "sha256": sha256_file(path)}


def read_extra(root: Path, groups: dict, draws: list[int], g2_answers: Path | None = None,
               g6_answers: Path | None = None) -> dict:
    """R2 (fig3.md): G2's and G6's cap 10 judge rows beside read["cells"], through judge_rows_v25 with G1's rule: each
    answer's key v2.5 row where one exists, else its key v2.4 row. For each set: its collects in root, each held to its
    outs and checked (read_source), check_units on each out, choose. G6's caps 5 and 20 are set aside (read_only). A cell
    is made by cell_of, as G1's are. G2's generation records (the copy S3 judged, sha256 pinned) give each answer's calls,
    and a judged answer must agree with its record, as read_collect holds G1's. Returns {"cells", "info", "final_key"
    (answers read from a final-key row), "cost" (G2's calls per answer on the answerable questions)}.
    G13 (D236, D237): when G2's answers are the frozen copy S3 judged (g2_answers None, as rebuild reads them), G2's 15
    replanned answers are G13's, records and judge rows both (scripts/g13_merge.py: merge_answers, replace_rows);
    "g13" holds the merge's report and its inputs' sha256. A fixture (g2_answers given) is read as it is."""
    import g13_merge as M
    g13 = g2_answers is None
    g13_info = {}
    root = Path(root)
    qids = sorted(groups)
    cells, info, final = {}, {}, 0
    for c, name, _ in EXTRA:
        low = name.lower()
        s24, s25 = JR.sources(root, name)
        try:
            loaded = [JR.read_source(s24, root / f"{low}_collect.jsonl")]
            if s25["present"]:
                loaded.append(JR.read_source(s25, root / f"s6_{low}_collect.jsonl"))
            run = f"exp_01__{c}__{INDEX}" if name == "G2" else f"b4_rlm_ref__{c}__all135"
            key = (lambda q, d: f"{INDEX}|{c}|{q}|d{d}") if name == "G2" else (lambda q, d: f"{c}|{q}|d{d}")
            ans = [{"run_id": run, "config": c, "question_id": q, "draw": d, "answer_key": key(q, d)}
                   for q in qids for d in draws]
            keep = set(draws)
            choice = JR.choose(ans, loaded, all_draws=True,
                               read_only=lambda r, c=c, keep=keep: r.get("config") == c and r.get("draw") in keep)
            if name == "G2" and g13:
                choice, g13_info["rows"] = M.replace_rows(choice)
            rep = JR.report(choice, all_draws=True)
        except JR.Refused as e:
            raise Refused(f"judge_rows_v25 on {name}: {e}") from None
        except M.Refused as e:
            raise Refused(f"g13_merge on {name}: {e}") from None
        units = {}
        for L, src in zip(loaded, (s24, s25)):
            units[L.name] = check_units(list(src["outs"]), L.run_sha256, draws, lambda p: str(Path(p).name))
        bad = []
        for a in ans:
            q, d = a["question_id"], a["draw"]
            ch = choice[JR.answer_ident(a)]
            if ch["row"] is None:
                bad.append(f"{a['answer_key']}: {ch['status']}")
                continue
            if bool(ch["row"].get("answerable_prompt")) != (groups[q] != "not_answerable"):
                bad.append(f"{a['answer_key']}: judged with the other prompt")
                continue
            cell, why = cell_of(ch["row"], groups[q])
            if why:
                bad.append(f"{a['answer_key']}: {why}")
                continue
            cell["key_version"] = "v2.5" if ch["status"] == "v2.5" else "v2.4"
            if ch["source"] == M.SOURCE:
                cell["g13"] = True
            cells[(c, q, d)] = cell
            final += ch["status"] in ("v2.4", "v2.5")
        if bad:
            raise Refused(f"read_extra {name}: {len(bad)} answers refused, first: {bad[0]}")
        info[name] = {"answers": len(ans), "by_status": rep["by_status"], "awaiting_s6": rep["awaiting_s6"]["count"],
                      **({"g13": g13_info.get("rows")} if name == "G2" and g13 else {}),
                      "run_sha256": {L.name: L.run_sha256 for L in loaded}, "units": units}
    f = Path(g2_answers) if g2_answers else FR.frozen("s457_mirror_20261022", "s457_mirror_20261022/matched_budget") / \
        "answers.jsonl"
    if g2_answers is None and sha256_file(f) != G2_ANSWERS_SHA:
        raise Refused(f"G2's answers.jsonl is not the copy S3 judged ({G2_ANSWERS_SHA[:8]})")
    last = {}
    for raw in f.read_text().splitlines():
        if raw.strip():
            r = json.loads(raw)
            last[r["answer_key"]] = r
    if g13:
        try:
            g13_info["sha256"] = M.check_sums()
            last, g13_info["answers"] = M.merge_answers(last)
        except M.Refused as e:
            raise Refused(f"g13_merge on G2's records: {e}") from None
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    perq, bad = {}, []
    clock = {"matched_budget": {}}                      # D218 (2): G2's clock time less the wait, and with it, per draw
    for q in qids:
        v = []
        clock["matched_budget"][q] = []
        for d in draws:
            k = f"{INDEX}|matched_budget|{q}|d{d}"
            r = last.get(k)
            cell = cells[("matched_budget", q, d)]
            if r is None:
                bad.append(f"{k}: no generation record")
                continue
            g = r.get("generation") or {}
            ok = not g.get("error") and (g.get("answer") or "").strip()
            if (cell["kind"] == "failed") != (not ok):
                bad.append(f"{k}: judge {cell['kind']}, record {'ok' if ok else 'failed'}")
                continue
            try:
                row_ = S457.exp01_row(k, r, "matched_budget")
                v.append(row_["calls_n"])
                clock["matched_budget"][q].append((row_["clock_less_wait"], row_["clock"]))
            except (SystemExit, KeyError, TypeError) as e:
                bad.append(f"{k}: S457.exp01_row: {e}")
        if v:
            perq[q] = sum(v) / len(v)
    if bad:
        raise Refused(f"read_extra G2: {len(bad)} answers do not match their records, first: {bad[0]}")
    g6 = read_g6_clock(g6_answers, groups, draws)
    clock["cap10"] = {q: [(s, s) for s in v] for q, v in g6["perq"].items()}
    x = [perq[q] for q in qa]
    lo, hi = interval(x, [1.0] * len(x))
    return {"cells": cells, "info": info, "final_key": final, "records": str(f), "records_sha256": sha256_file(f),
            "g13": g13_info or None,
            "g6_records": g6["path"], "g6_records_sha256": g6["sha256"], "clock": clock,
            "cost": {"questions": len(x), "calls_mean": sum(x) / len(x), "calls_ci95_lo": lo, "calls_ci95_hi": hi}}


def hold_g2_to_s511(extra: dict, path: Path, groups: dict, draws: list[int], kinds: dict) -> str:
    """fig3.md R8: G2's pass rate here equals S511's key v2.5 reading, at both thresholds, on the 86 and on each half."""
    v25 = json.loads(Path(path).read_text()).get("v25")
    if v25 is None:
        raise Refused(f"{Path(path).name} holds no key v2.5 reading: run scripts/S511_g2_matched_budget.py")
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    sets = {"all answerable": qa, "one-paper": [q for q in qa if kinds[q]["kind"] == "one"],
            "many-paper": [q for q in qa if kinds[q]["kind"] == "many"]}
    n = 0
    for t in THRESHOLDS:
        sh = arm_shares(extra["cells"], "matched_budget", qa, draws, t)
        for name, sub in sets.items():
            mine = arm_summary(sh, sub, draws)["rate"]
            want = v25["pass"][str(t)][name]["matched_budget"]["rate"]
            n += 1
            if abs(mine - want) > 1e-9:
                raise Refused(f"G2's pass rate at {t} on {name}: {mine} here, {want} in S511's results.json")
    rd = (v25.get("reading") or json.loads(Path(path).read_text())["reading"])["by_set"]["all answerable"]
    if not rd["matched_budget"]["passages_median"] > rd["rlm_10"]["passages_median"]:
        raise Refused("S511's medians say matched budget did not read more passages than RLM-10, the claim cef272fd "
                      "moved out of Figure 3's legend for Methods to hold")
    return (f"G2's pass rate equals S511's key v2.5 reading: {n} of 6 (thresholds 4 and 3, the 86 and each half); "
            f"matched budget's median passages exceed RLM-10's (S511), the claim cef272fd moved out of the legend")


def clock_margin(read: dict, extra: dict | None, groups: dict, draws: list[int]) -> dict:
    """D218 (1, 2): 3a's clock-time margin, per row and answerable question the clock time per answer less the wait for
    the local server (generation.latency_s less the calls' waited_for_server_s, S457.exp01_row; Zhang RLM-10 its
    wall_s) and the clock time with the wait, each the mean over its draws: {setup: {q: (less the wait, with it)}}. The
    six strategies from read["cells"] (cost_summary's values), matched budget and Zhang RLM-10 from read_extra."""
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    out = {}
    for c in CONFIGS:
        out[c] = {}
        for q in qa:
            v = [read["cells"][(c, q, d)]["cost"] for d in draws]
            out[c][q] = (sum(x["clock_less_wait_s"] for x in v) / len(v), sum(x["clock_s"] for x in v) / len(v))
    for c in (EXTRA_DRAWN if extra else ()):
        out[c] = {}
        for q in qa:
            v = extra["clock"][c][q]
            if len(v) != len(draws):
                raise Refused(f"{c} {q}: {len(v)} of {len(draws)} answers carry a clock time")
            out[c][q] = (sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v))
    return out


def supp6_workbook(folder: Path = SUPP6_DIR) -> Path:
    found = sorted(Path(folder).glob("Supplementary Figure 17 data*.xlsx"))
    if len(found) != 1:
        raise Refused(f"{folder}: {len(found)} Supplementary Figure 17 data workbooks, want 1 (run S457 rebuild)")
    return found[0]


def hold_margin_to_supp6(margin: dict, xlsx: Path) -> str:
    """D218 (2), reproduce first: every answerable question's clock time less the wait (the mean over its draws) of
    the eight rows equals sheet Supplementary Fig. 17c's clock_less_wait_mean_over_draws (rows 'question', answer type
    extractive or synthesis), and so does each row's mean over the questions. Refuses on the first difference."""
    from openpyxl import load_workbook
    wb = load_workbook(xlsx, read_only=True)
    if SUPP6_SHEET not in wb.sheetnames:
        raise Refused(f"{Path(xlsx).name} holds no sheet {SUPP6_SHEET}")
    rows = list(wb[SUPP6_SHEET].iter_rows(values_only=True))
    head = rows[0]
    want = defaultdict(dict)
    for r in rows[1:]:
        r = dict(zip(head, r))
        if r.get("row") == "question" and r.get("answer_type") in ("extractive", "synthesis"):
            want[r["setup"]][r["question_id"]] = r["clock_less_wait_mean_over_draws"]
    n, means = 0, []
    for c, perq in margin.items():
        w = want.get(c)
        if w is None or set(w) != set(perq):
            raise Refused(f"{SUPP6_SHEET}: {c}'s answerable questions are not the {len(perq)} the margin draws")
        for q, (v, _) in perq.items():
            if not abs(v - float(w[q])) <= 1e-9 * max(1.0, abs(v)):
                raise Refused(f"{SUPP6_SHEET}: {c} {q} clock less the wait {w[q]}, here {v}")
            n += 1
        m, mw = sum(v for v, _ in perq.values()) / len(perq), sum(float(x) for x in w.values()) / len(w)
        if abs(m - mw) > 1e-9 * max(1.0, m):
            raise Refused(f"{SUPP6_SHEET}: {c}'s mean {mw}, here {m}")
        means.append(f"{fn_label(c)} {m:.1f}")
    return (f"3a's clock-time margin equals {SUPP6_SHEET}: {n} per-question means of {len(margin)} rows, means "
            f"{', '.join(means)} s ({Path(xlsx).name})")


def fn_label(c):
    return LABEL.get(c) or {x: lb for x, _, lb in EXTRA}[c]


def read_fig3e(folder: Path) -> dict:
    """S522's tables and their sha256 (R4, R5). Refuses a tables.json that is not the one its header records."""
    folder = Path(folder)
    t, h = folder / "tables.json", folder / "header.json"
    if not t.is_file() or not h.is_file():
        raise Refused(f"{folder} holds no tables.json and header.json: run scripts/S522_fig3e_rows.py")
    hd = json.loads(h.read_text())
    if hd.get("tables_sha256") != sha256_file(t):
        raise Refused(f"{t.name} is not the file {h.name} records")
    return {"tables": json.loads(t.read_text()), "paths": [t, h], "reproduced": hd.get("reproduced") or []}


def fig3e_rows(fe) -> list[dict]:
    """Sheet Fig. 3f (D218 (3): corpus size, 3e before): S522's rows, in cell and n order. S522's run-to-run rows
    (noise_strategy, noise_cell) are not read: the plate draws no run-to-run row (rulings page 6 Nov, FIG3F: O2), so
    its Source Data carries none. The function keeps S522's name for the panel."""
    if fe is None:
        return placeholder_rows("f")
    t = fe["tables"]
    return t["cells"] + t["n"]


# Figure 3e, the T2 panel (D218 (3); D195's test, fig3.md "T2 panel"): S518's verdicts, read and not computed here
E3_KIND = "split (RLM-10 minus single pass)"              # Fig. 3e: one row per source and measure, as S518 stored it
E3_MEASURES = ("one_paper", "many_paper", "interaction")  # D_one, D_many and I = D_many - D_one (S518.analyse)
E3_MEASURE_LABEL = {"one_paper": "one paper (D_one)", "many_paper": "many papers (D_many)",
                    "interaction": "many-paper gain minus one-paper gain (I)"}
E3_LABEL = {"second_judge": "gemini-3-flash, second judge", "gemma3": "gemma3:27b", "qwen3-coder": "qwen3-coder:30b",
            "claude-haiku-4-5": "claude-haiku-4-5", "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-3-flash-preview": "gemini-3-flash"}   # D289: the paper's model names (S523.GEN_LABEL, Figure 6)
E3_ROLE_HEAD = {"test": "In the test", "beside": "Beside the test",   # D195: Haiku and gemini-2.5-pro count for nothing in it
                "reference": "Reference"}                  # D235 Q4: Flash on key v2.5, nothing in the test either


def s518_module():
    import S518_split_confirmation as S518                # its SOURCES, THRESHOLD and reading(), the one rule
    return S518


def read_s518(folder: Path) -> dict:
    """S518's five committed verdict files (D195), one per source of S518.SOURCES, in that order (the test sources,
    then those beside it), then the reference row (D235, read_s518_reference, last). Refuses a file whose source, role, decision or threshold is not S518's, a measure missing
    or outside its own interval, or a reading of I that S518.reading does not give for its interval. Nothing is
    recomputed: S518 is the only reader of the T2 and second-judge rows (D195)."""
    S518 = s518_module()
    folder = Path(folder)
    if S518.THRESHOLD != PRIMARY:
        raise Refused(f"S518 reads pass at score {S518.THRESHOLD}, Figure 3's primary threshold is {PRIMARY}")
    out, paths, rep = {}, [], []
    for src, role in S518.SOURCES.items():
        p = folder / f"{src}.json"
        if not p.is_file():
            raise Refused(f"{p} is missing: S518 has not written {src}'s verdict")
        d = json.loads(p.read_text())
        if (d.get("source"), d.get("role"), d.get("decision"), d.get("threshold")) != (src, role, "D195", S518.THRESHOLD):
            raise Refused(f"{p.name}: source {d.get('source')!r}, role {d.get('role')!r}, decision {d.get('decision')!r}, "
                          f"threshold {d.get('threshold')!r}; S518 gives {src!r}, {role!r}, 'D195', {S518.THRESHOLD}")
        r = d.get("result") or {}
        for m in E3_MEASURES:
            v = r.get(m) or {}
            x = v.get("I" if m == "interaction" else "d")
            if x is None or v.get("lo") is None or v.get("hi") is None or not v["lo"] <= x <= v["hi"]:
                raise Refused(f"{p.name}: {m} {x} is not inside its interval ({v.get('lo')}, {v.get('hi')})")
            if m != "interaction" and not (isinstance(v.get("questions"), int) and v["questions"] > 0):
                raise Refused(f"{p.name}: {m} holds no question count")
        it = r["interaction"]
        if it.get("reading") != S518.reading(it["lo"], it["hi"]):
            raise Refused(f"{p.name}: reading {it.get('reading')!r}, S518.reading gives "
                          f"{S518.reading(it['lo'], it['hi'])!r} for ({it['lo']}, {it['hi']})")
        out[src] = d
        paths.append(p)
        rep.append(f"{src} ({role}) I {100 * it['I']:.1f} points, {it['reading']}")
    d, p = read_s518_reference(folder, S518)
    out[S518.REFERENCE] = d
    paths.append(p)
    rep.append(f"{S518.REFERENCE} ({S518.REF_ROLE}, key {S518.REF_KEY}) I {100 * d['result']['interaction']['I']:.1f} "
               f"points, {d['result']['interaction']['reading']}")
    return {"sources": out, "paths": paths, "sha256": {str(p): sha256_file(p) for p in paths},
            "reproduced": [f"panel e: S518's verdicts read, each reading S518.reading's for its interval: " + "; ".join(rep)]}


def read_s518_reference(folder: Path, S518) -> tuple[dict, Path]:
    """D235 Q4: S518's reference row, gemini-3-flash-preview.json (S518 reference). Its own checks, the five D195
    sources' left as read_s518 holds them: source, role, key and decision S518's (REFERENCE, REF_ROLE, REF_KEY, D235),
    method D195 and threshold S518's; each measure inside its own interval with a question count; I's reading
    S518.reading's for its interval. Refuses the file missing."""
    p = Path(folder) / f"{S518.REFERENCE}.json"
    if not p.is_file():
        raise Refused(f"{p} is missing: S518 reference has not written the reference row (D235)")
    d = json.loads(p.read_text())
    want = (S518.REFERENCE, S518.REF_ROLE, S518.REF_KEY, S518.REF_DECISION.strip("*"), "D195", S518.THRESHOLD)
    got = tuple(d.get(k) for k in ("source", "role", "key", "decision", "method", "threshold"))
    if got != want:
        raise Refused(f"{p.name}: (source, role, key, decision, method, threshold) {got}; S518 gives {want}")
    r = d.get("result") or {}
    for m in E3_MEASURES:
        v = r.get(m) or {}
        x = v.get("I" if m == "interaction" else "d")
        if x is None or v.get("lo") is None or v.get("hi") is None or not v["lo"] <= x <= v["hi"]:
            raise Refused(f"{p.name}: the reference's {m} {x} is not inside its interval ({v.get('lo')}, {v.get('hi')})")
        if m != "interaction" and not (isinstance(v.get("questions"), int) and v["questions"] > 0):
            raise Refused(f"{p.name}: the reference's {m} holds no question count")
    ref_it = r["interaction"]
    if ref_it.get("reading") != S518.reading(ref_it["lo"], ref_it["hi"]):
        raise Refused(f"{p.name}: the reference's reading {ref_it.get('reading')!r}, S518.reading gives "
                      f"{S518.reading(ref_it['lo'], ref_it['hi'])!r}")
    return d, p


def s518_rows(t2) -> list[dict]:
    """Sheet Fig. 3e: per source (S518.SOURCES order) and measure (E3_MEASURES) the value and interval S518 stored, in
    percentage points; I's reading; the file and its sha256. With no verdicts read, the placeholder row."""
    if t2 is None:
        return placeholder_rows("e")
    rows = []
    for src, d in t2["sources"].items():
        r = d["result"]
        p = next(q for q in t2["paths"] if q.stem == src)
        for m in E3_MEASURES:
            v = r[m]
            rows.append({"row_kind": E3_KIND, "source": src, "source_label": E3_LABEL[src], "role": d["role"],
                         "measure": m, "measure_label": E3_MEASURE_LABEL[m],
                         "questions_one_paper": r["one_paper"]["questions"],
                         "questions_many_paper": r["many_paper"]["questions"],
                         "threshold": d["threshold"], "d_pp": r9(100 * v["I" if m == "interaction" else "d"]),
                         "ci95_lo_pp": r9(100 * v["lo"]), "ci95_hi_pp": r9(100 * v["hi"]),
                         "p_signflip_exact_two_sided": None if m == "interaction" else v["p_signflip_exact_two_sided"],
                         "reading": r["interaction"]["reading"] if m == "interaction" else None,
                         "s518_file": label(p), "s518_sha256": t2["sha256"][str(p)]})
    return rows


def read_person_check(path: Path, res: dict, draws: list[int]) -> dict:
    """D231, D306: S607's counts of the person's blind reading (D223) of draw 1's single pass and RLM-10 answers to the
    39 out-of-scope questions, 'partly' counted as refused (D227, its note). Reproduce first: S607's judge counts must
    equal this build's own draw-1 refusals (refusal score REFUSAL_T or more, a failed answer not refused) on the same
    39 questions, strategy by strategy, or nothing is drawn. Returns {"rows": {strategy: S607's final row}, ...}."""
    if 1 not in draws:
        raise Refused(f"{label(path)}: the person read draw 1, which --draws {draws} does not include")
    s = json.loads(Path(path).read_text())
    fin = s["results"]["final"]
    shn = res["refusal"][REFUSAL_T]["shares"]
    rows, held = {}, []
    for c, nm in S607_NAMES.items():
        r = fin[nm]
        per = [shn[c][q][1].get(1) for q in shn[c]]
        mine, n = sum(1 for h in per if h == 1), sum(1 for h in per if h is not None)
        if r["n"] != n or r["judge_refused"] != mine:
            raise Refused(f"{label(path)}: {nm}'s judge refused {r['judge_refused']} of {r['n']}, this build's draw 1 "
                          f"{mine} of {n}: S607 and Figure 3 do not read the same answers")
        t = r["table_2x2"]
        if t["both_refused"] + t["person_refused_judge_not"] != r["person_refused"] \
                or t["both_refused"] + t["person_not_judge_refused"] != r["judge_refused"] \
                or t["both_refused"] + t["both_not"] != r["agreement"] or sum(t.values()) != r["n"]:
            raise Refused(f"{label(path)}: {nm}'s 2x2 {t} does not add up to its counts")
        rows[c] = r
        held.append(f"{nm} {mine} of {n}")
    return {"rows": rows, "path": Path(path), "sha256": sha256_file(path), "reading": s["readings"]["final"],
            "reproduced": f"person check (S607, D306): S607's judge counts equal this build's draw-1 refusals "
                          f"({'; '.join(held)}); S607 itself: {s['_provenance']['reproduced']}"}


def person_rows(person) -> list[dict]:
    """Sheet Fig. 3b's rows '{PERSON_KIND}': per strategy read, the person's refused count (the diamond) beside the
    judge's on the same draw-1 answers, S607's 2x2 and the file read with its sha256."""
    if person is None:
        return []
    out = []
    for c, r in person["rows"].items():
        t = r["table_2x2"]
        out.append({"row_kind": PERSON_KIND, "strategy": c, "strategy_label": LABEL[c], "draw": 1,
                    "questions": r["n"], "person_refused": r["person_refused"],
                    "person_refused_pct": r9(100 * r["person_refused"] / r["n"]),
                    "judge_refused_draw_1": r["judge_refused"],
                    "judge_refused_draw_1_pct": r9(100 * r["judge_refused"] / r["n"]),
                    "agreement": r["agreement"], "both_refused": t["both_refused"],
                    "person_refused_judge_not": t["person_refused_judge_not"],
                    "person_not_judge_refused": t["person_not_judge_refused"], "both_not": t["both_not"],
                    "kappa": "not defined (the judge gave one category to every answer)" if r["kappa"] is None
                    else r9(r["kappa"]),
                    "reading": person["reading"], "s607_file": label(person["path"]),
                    "s607_sha256": person["sha256"]})
    return out


def sheets(res, res_out, out_t, draws, read, cost, q78, crx=None, extra=None, fe=None, kinds=None, margin=None,
           t2=None, person=None):
    """Sheets by panel letter on the plate, each a list of row dicts with rows of several kinds, each named in row_kind;
    then the two of Supplementary Figure 16 (rank writes each plate its own). Fig. 3a: the pass rates of the eight rows
    (the six strategies, G2 and G6 at cap 10), on all the answerable questions and per question group, the tiles at score
    4, the question order; old panel b's numbers as 'concept recall (not drawn)' rows. Fig. 3b: refusal on the 39, the
    false-premise counts. Fig. 3c: Rule 4 at score 4, the noise baselines. Fig. 3d: model calls and pass rate at score 4,
    the times, each strategy's multiples of single pass, the matched-budget cross. Fig. 3e: S518's verdicts (s518_rows).
    Fig. 3f: S522's rows (D218 (3): e and f swapped). Fig. 3a also holds the clock-time margin (D218, margin from
    clock_margin). Supplementary Fig. 16a and 16b: the tiles and Rule 4 at score 3. 'strategy' rows hold question
    group 'all' only, so S473 and S480 read them as they did."""
    kinds = kinds or S511.questions()
    a, dd = [], []
    rank = {}
    sp = res["answerable"][PRIMARY]["summary"]
    order = sorted(CONFIGS, key=lambda c: -(sp[c]["rate_x"] or 0))
    for c in CONFIGS:
        rank[c] = 1 + sum(1 for o in CONFIGS if (sp[o]["rate_x"] or 0) > (sp[c]["rate_x"] or 0))
    qa = sorted(q for q, g in read["groups"].items() if g == "answerable")
    part = {"one": [q for q in qa if kinds[q]["kind"] == "one"], "many": [q for q in qa if kinds[q]["kind"] == "many"]}
    ex_cells = (extra or {}).get("cells") or {}
    arms_x = [(c, lb) for c, _, lb in EXTRA] if extra else []
    sh_x = {t: {c: arm_shares(ex_cells, c, qa, draws, t) for c, _ in arms_x} for t in THRESHOLDS}
    sh_xo = {t: {c: arm_shares(ex_cells, c, qa, draws, t, False) for c, _ in arms_x} for t in THRESHOLDS}
    x_kind = "answers_failed_counted_as_fail"

    def s_row(c, lb, t, x, xo, n_group, kind="strategy", group="all", more=None):
        return {"row_kind": kind, "strategy": c, "strategy_label": lb, "threshold": t, "question_group": group,
                "questions_in_group": n_group, "questions_with_a_share": x["questions_with_share"],
                "draws_read": ",".join(map(str, draws)),
                "pass_rate_pct": r9(100 * x["rate"]), "ci95_lo_pct": r9(100 * x["lo"]),
                "ci95_hi_pct": r9(100 * x["hi"]), "interval": "Rule 2 question bootstrap, percentile",
                "resamples": N_BOOT, "resample_seed": SEED, **(more or {}),
                "pass_rate_pct_failures_left_out": r9(None if xo["rate"] is None else 100 * xo["rate"])}
    for t in THRESHOLDS:
        s = res["answerable"][t]["summary"]
        so = res_out["answerable"][t]["summary"]
        for c in CONFIGS:
            a.append(s_row(c, LABEL[c], t, s[c], so[c], 86, more={
                f"rank_by_mean_threshold_{PRIMARY}": rank[c],
                x_kind: sum(1 for (cc, q, d), cl in read["cells"].items() if cc == c and cl["kind"] == "failed"
                            and read["groups"][q] == "answerable"),
                "judge_calls_without_score": sum(1 for (cc, q, d), cl in read["cells"].items()
                                                 if cc == c and cl["kind"] == "unscored"
                                                 and read["groups"][q] == "answerable")}))
        for c, lb in arms_x:
            a.append(s_row(c, lb, t, arm_summary(sh_x[t][c], qa, draws), arm_summary(sh_xo[t][c], qa, draws), 86, more={
                x_kind: sum(1 for (cc, q, d), cl in ex_cells.items() if cc == c and cl["kind"] == "failed"
                            and read["groups"][q] == "answerable"),
                "judge_calls_without_score": sum(1 for (cc, q, d), cl in ex_cells.items()
                                                 if cc == c and cl["kind"] == "unscored"
                                                 and read["groups"][q] == "answerable")}))
        sh_t = res["answerable"][t]["shares"]
        sho_t = res_out["answerable"][t]["shares"]
        for g, sub in part.items():
            for c in CONFIGS:
                a.append(s_row(c, LABEL[c], t, arm_summary(sh_t[c], sub, draws), arm_summary(sho_t[c], sub, draws),
                               len(sub), GROUP_KIND, g))
            for c, lb in arms_x:
                a.append(s_row(c, lb, t, arm_summary(sh_x[t][c], sub, draws), arm_summary(sh_xo[t][c], sub, draws),
                               len(sub), GROUP_KIND, g))
        for c in CONFIGS:
            for d in draws:
                v, n = s[c]["per_draw"][d]
                a.append({"row_kind": "draw", "strategy": c, "strategy_label": LABEL[c], "threshold": t, "draw": d,
                          "draw_pass_rate_pct": r9(None if v is None else 100 * v), "draw_questions": n})
        for c, lb in arms_x:
            for d, (v, n) in arm_summary(sh_x[t][c], qa, draws)["per_draw"].items():
                a.append({"row_kind": "draw", "strategy": c, "strategy_label": lb, "threshold": t, "draw": d,
                          "draw_pass_rate_pct": r9(None if v is None else 100 * v), "draw_questions": n})
        for (x1, x2), p in res["answerable"][t]["pairs"].items():
            a.append({"row_kind": "pair (unadjusted)", "strategy": x1, "strategy_b": x2, "threshold": t,
                      "pair_questions": p["questions"], "questions_a_higher": p["a_higher"],
                      "questions_b_higher": p["b_higher"], "difference_pct_points": r9(100 * p["d"]),
                      "difference_ci95_lo": r9(100 * p["lo"]), "difference_ci95_hi": r9(100 * p["hi"]),
                      "p_two_sided_exact_sign_flip": r9(p["p"], 15), "separated_at_0_05": p["p"] < ALPHA})
    for c in CONFIGS:
        for kind, d in out_t[c].items():
            for why, keys in d.items():
                a.append({"row_kind": f"outcome: {kind}", "strategy": c, "strategy_label": LABEL[c],
                          "outcome": why, "answers": len(keys), "answer_keys": "; ".join(keys)})
    for c, lb in arms_x:                                # G2 and G6: the failed and unscored answers, each reason as stored
        for kind in ("failed", "unscored"):
            by_why = defaultdict(list)
            for (cc, q, d), cl in sorted(ex_cells.items()):
                if cc == c and cl["kind"] == kind:
                    by_why[cl["why"]].append(cl["key"])
            for why, keys in by_why.items():
                a.append({"row_kind": f"outcome: {kind}", "strategy": c, "strategy_label": lb, "outcome": why,
                          "answers": len(keys), "answer_keys": "; ".join(keys)})
    # what the plate draws (D127, D200): the 86 questions in plot order, one-paper then many-paper, in each the easiest
    # left (draws passed summed over the six strategies at score 4 or more, then at 3 or more, then the question id), and
    # one tile per row and question
    sh_a = {t: res["answerable"][t]["shares"] for t in THRESHOLDS}

    def passed(t, c, q):
        return sum(1 for h in sh_a[t][c][q][1].values() if h == 1)
    tot = {t: {q: sum(passed(t, c, q) for c in CONFIGS) for q in qa} for t in THRESHOLDS}
    order_a = [q for g in ("one", "many") for q in sorted(part[g], key=lambda q: (-tot[4][q], -tot[3][q], q))]
    o_rows = [{"row_kind": ORDER_KIND, "plot_position": pos, "question_id": q, "question_type": kinds[q]["kind"],
               "draws_passed_sum_t4": tot[4][q], "draws_passed_sum_t3": tot[3][q]} for pos, q in enumerate(order_a, 1)]
    a += o_rows
    s5a = list(o_rows)

    def tile(c, lb, t, pos, q, per):
        return {"row_kind": TILE_KIND, "threshold": t, "strategy": c, "strategy_label": lb, "plot_position": pos,
                "question_id": q, "draws_passed": sum(1 for h in per.values() if h == 1),
                "draws_scored": sum(1 for h in per.values() if h is not None)}
    for c in CONFIGS:
        for pos, q in enumerate(order_a, 1):
            a.append(tile(c, LABEL[c], 4, pos, q, sh_a[4][c][q][1]))
            s5a.append(tile(c, LABEL[c], 3, pos, q, sh_a[3][c][q][1]))
    for c, lb in arms_x:
        for pos, q in enumerate(order_a, 1):
            a.append(tile(c, lb, 4, pos, q, sh_x[4][c][q][1]))
    # D218 (1, 2): the clock-time margin, per row and answerable question (the grey dots, in question-id order) and per
    # row the mean over the questions (the black dot and its printed value) with Rule 2's interval (not drawn); the
    # clock time with the wait beside each, not drawn (verified pass's is the caption's)
    names_x = {c: lb for c, lb in arms_x}
    for c in [*CONFIGS, *names_x]:
        if c not in (margin or {}):
            continue
        perq = margin[c]
        for q in sorted(perq):
            a.append({"row_kind": MARGIN_Q_KIND, "strategy": c, "strategy_label": LABEL.get(c) or names_x[c],
                      "question_id": q, "question_type": kinds[q]["kind"], "draws_read": ",".join(map(str, draws)),
                      "clock_less_wait_s_mean_over_draws": r9(perq[q][0]),
                      "clock_s_mean_over_draws": r9(perq[q][1])})
        v = [perq[q][0] for q in sorted(perq)]
        w = [perq[q][1] for q in sorted(perq)]
        lo, hi = interval(v, [1.0] * len(v))
        lo_w, hi_w = interval(w, [1.0] * len(w))
        a.append({"row_kind": MARGIN_KIND, "strategy": c, "strategy_label": LABEL.get(c) or names_x[c],
                  "questions": len(v), "draws_read": ",".join(map(str, draws)),
                  "clock_less_wait_s_mean": r9(sum(v) / len(v)), "clock_less_wait_s_ci95_lo": r9(lo),
                  "clock_less_wait_s_ci95_hi": r9(hi), "printed": S457.half_up(sum(v) / len(v), 0) + " s",
                  "interval": "Rule 2 question bootstrap, percentile; not drawn", "resamples": N_BOOT,
                  "resample_seed": SEED, "clock_s_mean_with_wait": r9(sum(w) / len(w)),
                  "clock_s_with_wait_ci95_lo": r9(lo_w), "clock_s_with_wait_ci95_hi": r9(hi_w),
                  "with_wait": "not drawn"})
    s5a +=[dict(r) for r in a if r["row_kind"] == "strategy" and r["threshold"] == 3 and r["strategy"] in CONFIGS]
    for r in a:                                         # D216: 3a draws no rate since its margins went; say where
        if r["row_kind"] in ("strategy", GROUP_KIND):
            r[DRAWN_IN] = ("not in 3a; Fig. 3d, the " + D_MARK_NAME[r.get("question_group") or "all"]
                           + " (interval not drawn)" if r["strategy"] in CONFIGS
                           else "not in 3a; Fig. 3d, the matched-budget cross (interval not drawn)"
                           if r["strategy"] == "matched_budget" and r["question_group"] == "all"
                           and r["threshold"] == PRIMARY else "not drawn")
    for t in (REFUSAL_T,):
        s = res["refusal"][t]["summary"]
        for c in CONFIGS:
            x = s[c]
            dd.append({"row_kind": "refusal", "strategy": c, "strategy_label": LABEL[c], "threshold": t,
                       "questions_in_group": 39, "questions_with_a_share": x["questions_with_share"],
                       "draws_read": ",".join(map(str, draws)),
                       "refused_pct": r9(100 * x["rate"]), "ci95_lo_pct": r9(100 * x["lo"]),
                       "ci95_hi_pct": r9(100 * x["hi"]),
                       "zero_one_sided_upper_bound_pct": r9(None if x["zero_bound"] is None else 100 * x["zero_bound"]),
                       "full_one_sided_lower_bound_pct": r9(None if x["full_bound"] is None else 100 * x["full_bound"]),
                       "bar_drawn_to_pct": r9(100 * (x["zero_bound"] if x["zero_bound"] is not None else
                                                     1.0 if x["full_bound"] is not None else x["hi"])),
                       "bar_drawn_from_pct": r9(100 * (0.0 if x["zero_bound"] is not None else
                                                       x["full_bound"] if x["full_bound"] is not None else x["lo"])),
                       "bar_is": "one-sided 95% upper bound (dashed)" if x["zero_bound"] is not None
                       else "one-sided 95% lower bound (dashed)" if x["full_bound"] is not None
                       else "95% percentile interval",
                       "interval_degenerate": x["lo"] == x["hi"],
                       "refused_pct_failures_left_out": r9(None if res_out["refusal"][t]["summary"][c]["rate"] is None
                                                           else 100 * res_out["refusal"][t]["summary"][c]["rate"])})
        for c in CONFIGS:
            for d in draws:
                v, n = s[c]["per_draw"][d]
                dd.append({"row_kind": "draw", "strategy": c, "strategy_label": LABEL[c], "threshold": t, "draw": d,
                           "draw_refused_pct": r9(None if v is None else 100 * v), "draw_questions": n})
        for (x1, x2), p in res["refusal"][t]["pairs"].items():
            dd.append({"row_kind": "pair (unadjusted)", "strategy": x1, "strategy_b": x2, "threshold": t,
                       "pair_questions": p["questions"], "questions_a_higher": p["a_higher"],
                       "questions_b_higher": p["b_higher"], "difference_pct_points": r9(100 * p["d"]),
                       "difference_ci95_lo": r9(100 * p["lo"]), "difference_ci95_hi": r9(100 * p["hi"]),
                       "p_two_sided_exact_sign_flip": r9(p["p"], 15), "separated_at_0_05": p["p"] < ALPHA})
        # what the plate draws (D130): the 39 questions in plot order (most refused left: the refused share summed
        # over the six strategies, then the question id) and one tile per strategy and question
        shn = res["refusal"][t]["shares"]
        qn = sorted(q for q, g in read["groups"].items() if g == "not_answerable")
        tot_n = {q: sum((shn[c][q][0] or Fraction(0)) for c in CONFIGS) for q in qn}
        order_d = sorted(qn, key=lambda q: (-tot_n[q], q))
        for pos, q in enumerate(order_d, 1):
            dd.append({"row_kind": ORDER_KIND, "plot_position": pos, "question_id": q,
                       "refused_share_sum": r9(tot_n[q]),
                       "draws_refused_sum": sum(1 for c in CONFIGS for h in shn[c][q][1].values() if h == 1)})
        for c in CONFIGS:
            for pos, q in enumerate(order_d, 1):
                per = shn[c][q][1]
                dd.append({"row_kind": TILE_KIND, "threshold": t, "strategy": c, "strategy_label": LABEL[c],
                           "plot_position": pos, "question_id": q,
                           "draws_refused": sum(1 for h in per.values() if h == 1),
                           "draws_scored": sum(1 for h in per.values() if h is not None)})
    for c in CONFIGS:
        f3, f4 = res["false_premise"][3][c], res["false_premise"][4][c]
        dd.append({"row_kind": "false premise", "strategy": c, "strategy_label": LABEL[c],
                   "fp_passed_t4": f4["passed"], "fp_answers_t4": f4["answers"], "fp_passed_t3": f3["passed"],
                   "fp_answers": f3["answers"], "draws_read": ",".join(map(str, draws)),
                   **{f"fp_draw_{d}_passed_t3": f3["per_draw"][d][0] for d in draws},
                   **{f"fp_draw_{d}_answers": f3["per_draw"][d][1] for d in draws}})
    for c in CONFIGS:
        for q, hits in res["false_premise"][3][c]["per_question"].items():
            h4 = res["false_premise"][4][c]["per_question"][q]
            dd.append({"row_kind": "false premise question", "strategy": c, "strategy_label": LABEL[c],
                       "question_id": q, "fp_passes_t4": sum(h for h in h4 if h is not None),
                       "fp_passes_t3": sum(h for h in hits if h is not None),
                       "fp_answers": sum(1 for h in hits if h is not None)})
    a += [{**r, "row_kind": f"{CR_NOT_DRAWN}: {r['row_kind']}"} for r in (cr_rows(crx, draws) if crx else [])]
    e_all = flip_rows(res, q78, draws)
    d_rows = cost_rows(res, cost, draws, read, kinds)
    # D216: 3d's marks, per strategy and question group (all, one paper, many papers): x the mean of the group's
    # questions' model calls (each the mean over its draws, as the grey dots), y the group's pass rate at score 4
    # (filled) and 3 (open), the rates exactly sheet Fig. 3a's rows; the intervals stay here and are not drawn
    a_rate = {(r["strategy"], r["question_group"], r["threshold"]): r for r in a
              if r["row_kind"] in ("strategy", GROUP_KIND) and r["strategy"] in CONFIGS}
    calls_q = {(c, q): sum(read["cells"][(c, q, d)]["cost"]["calls"] for d in draws) / len(draws)
               for c in CONFIGS for q in qa}
    for c in CONFIGS:
        for g, sub in (("all", qa), ("one", part["one"]), ("many", part["many"])):
            x = (cost["answerable"][c]["calls"]["mean"] if g == "all"
                 else sum(calls_q[(c, q)] for q in sorted(sub)) / len(sub))
            r4, r3 = a_rate[(c, g, 4)], a_rate[(c, g, 3)]
            d_rows.append({"row_kind": GROUP_D_KIND, "strategy": c, "strategy_label": LABEL[c], "question_group": g,
                           "questions": len(sub), "draws_read": ",".join(map(str, draws)), "calls_mean": r9(x),
                           "pass_rate_t4_pct": r4["pass_rate_pct"], "pass_rate_t3_pct": r3["pass_rate_pct"],
                           "pass_t4_ci95_lo_pct": r4["ci95_lo_pct"], "pass_t4_ci95_hi_pct": r4["ci95_hi_pct"],
                           "pass_t3_ci95_lo_pct": r3["ci95_lo_pct"], "pass_t3_ci95_hi_pct": r3["ci95_hi_pct"],
                           "intervals": "not drawn"})
    ca = cost["answerable"]
    n_q = ca["single_pass"]["questions"]
    for c in FLIPPED:
        sp_c = ca["single_pass"]
        d_rows.append({"row_kind": MULT_KIND, "strategy": c, "strategy_label": LABEL[c], "measure": "model-call time",
                       "ratio_of_means": r9(ca[c]["model_s"]["mean"] / sp_c["model_s"]["mean"]), "ratio_of_medians": None,
                       "questions": n_q})
        d_rows.append({"row_kind": MULT_KIND, "strategy": c, "strategy_label": LABEL[c], "measure": "tokens",
                       "ratio_of_means": r9(ca[c]["tokens"]["mean"] / sp_c["tokens"]["mean"]),
                       "ratio_of_medians": r9(ca[c]["tokens"]["median"] / sp_c["tokens"]["median"]), "questions": n_q})
    if extra:
        x = extra["cost"]
        g2 = arm_summary(sh_x[4]["matched_budget"], qa, draws)
        d_rows.append({"row_kind": CROSS_KIND, "strategy": "matched_budget", "strategy_label": fn.MATCHED_BUDGET,
                       "questions": x["questions"], "draws_read": ",".join(map(str, draws)),
                       "calls_mean": r9(x["calls_mean"]), "calls_ci95_lo": r9(x["calls_ci95_lo"]),
                       "calls_ci95_hi": r9(x["calls_ci95_hi"]), "pass_rate_t4_pct": r9(100 * g2["rate"]),
                       "pass_t4_ci95_lo_pct": r9(100 * g2["lo"]), "pass_t4_ci95_hi_pct": r9(100 * g2["hi"]),
                       "intervals": "not drawn"})
    return {"Fig. 3a": a, "Fig. 3b": dd + person_rows(person), "Fig. 3c": [r for r in e_all if r["threshold"] == 4], "Fig. 3d": d_rows,
            "Fig. 3e": s518_rows(t2), "Fig. 3f": fig3e_rows(fe),                    # D218 (3): e and f swapped
            S5_SHEET["a"]: s5a, S5_SHEET["b"]: [r for r in e_all if r["threshold"] == 3]}, order


PLACEHOLDER = {"e": ("replication on other generators", "",          # D122 Q4: the frame is left empty
                     "not drawn yet: the replication on other generators (plan row T2)"),
               "f": ("corpus size", "", "not read: no --fig3e given")}
MARGIN_Q_KIND = "clock time per question (margin dot)"   # D218: 3a's margin rows
MARGIN_KIND = "clock time per answer (margin mean)"


def placeholder_rows(k):
    what, text, state = PLACEHOLDER[k]
    return [{"row_kind": "placeholder", "panel": k, "measure": what, "text_in_frame": text, "state": state}]


def cost_rows(res, cost, draws, read, kinds=None):
    """Fig. 3d: per strategy the plotted point (model calls per answer on the 86, with its interval; the pass rate at
    score 4 with its interval, as in Fig. 3a) and the times per answer; then each cost on all 135 questions, and
    RLM-10 over single pass."""
    rows = []
    s4 = res["answerable"][4]["summary"]
    for grp, kind in (("answerable", "strategy (plotted)"), ("all", "strategy, all 135 questions (not plotted)")):
        for c in CONFIGS:
            x = cost[grp][c]
            r = {"row_kind": kind, "strategy": c, "strategy_label": LABEL[c], "questions": x["questions"],
                 "draws_read": ",".join(map(str, draws))}
            if grp == "answerable":
                r.update(pass_rate_t4_pct=r9(100 * s4[c]["rate"]), pass_t4_ci95_lo_pct=r9(100 * s4[c]["lo"]),
                         pass_t4_ci95_hi_pct=r9(100 * s4[c]["hi"]), intervals="not drawn")   # D216: no interval drawn
            for m, _ in COST_MEASURES:
                r.update({f"{m}_mean": r9(x[m]["mean"]), f"{m}_ci95_lo": r9(x[m]["lo"]),
                          f"{m}_ci95_hi": r9(x[m]["hi"])})
            rows.append(r)
    for grp, n in (("answerable", 86), ("all", 135)):
        rr = cost[grp]["ratio_rlm10_single"]
        rows.append({"row_kind": "ratio, RLM-10 over single pass", "questions": n,
                     "calls_ratio": r9(rr["calls"]), "clock_s_ratio": r9(rr["clock_s"])})
    # what the plate draws (D129): per strategy and answerable question, its model calls per answer (the mean over
    # its draws, as cost_summary averages them) and its share of draws passing at score 4 or more (the grey dots)
    sh4 = res["answerable"][4]["shares"]
    for c in CONFIGS:
        for q in sh4[c]:
            v = [read["cells"][(c, q, d)]["cost"]["calls"] for d in draws]
            p = sh4[c][q][0]
            rows.append({"row_kind": CQ_KIND, "strategy": c, "strategy_label": LABEL[c], "question_id": q,
                         "question_type": (kinds or {}).get(q, {}).get("kind"),
                         "calls_per_answer_question_mean": r9(sum(v) / len(v)),
                         "pass_share_t4_pct": r9(None if p is None else 100 * p), "draws_read": ",".join(map(str, draws))})
    return rows


def flip_rows(res, q78, draws):
    """Fig. 3c (score 4) and Supplementary Figure 16b (score 3): Rule 4 per strategy and threshold (the plotted means of harmed and helped over the pairings, both
    denominators with their intervals, Rule 3's P, the same-draw totals); each draw's 2 x 2 table; each strategy's
    noise baseline (the reference band is single pass's, each other strategy's own is drawn on its row); verified pass
    without the answers whose verifier was not ok (Q78)."""
    rows = []
    npair = len(draws) ** 2
    for t in THRESHOLDS:
        for c in FLIPPED:
            f = res["flips"][t][c]
            rows.append({"row_kind": "strategy against single pass", "strategy": c, "strategy_label": LABEL[c],
                         "threshold": t, "questions": f["questions"], "pairings_per_question": npair,
                         "harmed_mean_over_pairings": r9(f["harmed"]), "helped_mean_over_pairings": r9(f["helped"]),
                         "single_pass_correct_sum": r9(f["baseline_correct"]), "changed": r9(f["changed"]),
                         "harmful_share_of_changed_pct": r9(None if f["harm_share"] is None else 100 * f["harm_share"]),
                         "harmful_share_ci95_lo_pct": r9(None if f["harm_share_lo"] is None else 100 * f["harm_share_lo"]),
                         "harmful_share_ci95_hi_pct": r9(None if f["harm_share_hi"] is None else 100 * f["harm_share_hi"]),
                         "correct_degraded_pct": r9(None if f["degraded_share"] is None else 100 * f["degraded_share"]),
                         "correct_degraded_ci95_lo_pct": r9(None if f["degraded_lo"] is None else 100 * f["degraded_lo"]),
                         "correct_degraded_ci95_hi_pct": r9(None if f["degraded_hi"] is None else 100 * f["degraded_hi"]),
                         "p_two_sided_exact_sign_flip": r9(f["p"], 15),
                         "same_draw_harmed_total": f["same_draw_harmed"], "same_draw_helped_total": f["same_draw_helped"]})
        for c in FLIPPED:
            for d, x in res["flips"][t][c]["per_draw"].items():
                rows.append({"row_kind": "draw against the same draw (Rule 4 (a), not plotted)", "strategy": c,
                             "strategy_label": LABEL[c], "threshold": t, "draw": d, **x})
        for c in FLIPPED:                                  # the black dots (D131): every pairing of draws
            for d, e, h, g in pairing_counts(res["answerable"][t]["shares"], c, draws):
                rows.append({"row_kind": PAIR_KIND, "strategy": c, "strategy_label": LABEL[c], "threshold": t,
                             "single_pass_draw": d, "strategy_draw": e, "harmed": h, "helped": g})
        for c in CONFIGS:
            x = res["self_flips"][t][c]
            rows.append({"row_kind": "noise baseline (the strategy against itself)", "strategy": c,
                         "strategy_label": LABEL[c], "threshold": t,
                         "disagreeing_draw_pairs_pct": r9(None if x["disagree_share"] is None
                                                          else 100 * x["disagree_share"]),
                         "disagreeing_draw_pairs": x["disagreeing_pairs"], "draw_pairs": x["draw_pairs"],
                         **{f"pass_on_{k.split('>')[0]}_fail_on_{k.split('>')[1]}": v for k, v in x["ordered"].items()},
                         "ordered_pairs_min": x["ordered_min"], "ordered_pairs_max": x["ordered_max"],
                         "ordered_pairs_mean": r9(x["ordered_mean"]),
                         "drawn_as": "not drawn on Figure 3c" if t == PRIMARY else
                         "the top row's grey dots and the band" if c == "single_pass" else "the grey dots under its bars"})
    w = q78.get("res_without")
    for t in THRESHOLDS:
        if w is None:
            rows.append({"row_kind": "verified pass without the verifier not ok (Q78)", "threshold": t,
                         "note": "no verified-pass answer of the draws read had a verifier status other than ok"})
            continue
        f = w["flips"][t]["verified_pass"]
        rows.append({"row_kind": "verified pass without the verifier not ok (Q78)", "strategy": "verified_pass",
                     "threshold": t, "answers_left_out": len(q78["not_ok"]), "questions": f["questions"],
                     "harmed_mean_over_pairings": r9(f["harmed"]), "helped_mean_over_pairings": r9(f["helped"]),
                     "harmful_share_of_changed_pct": r9(None if f["harm_share"] is None else 100 * f["harm_share"]),
                     "correct_degraded_pct": r9(None if f["degraded_share"] is None else 100 * f["degraded_share"]),
                     "p_two_sided_exact_sign_flip": r9(f["p"], 15)})
    return rows


def table(rows):
    cols = []
    for r in rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    return cols, [[r.get(c) for c in cols] for r in rows]


def trace(res, read, out_t):
    """ranking.json: every number with the answer keys it is counted from."""
    cells, groups = read["cells"], read["groups"]
    tr = {}
    for t in THRESHOLDS:
        for grp, metric in (("answerable", "correctness"), ("not_answerable", "refusal_accuracy"),
                            ("false_premise", "correctness")):
            if grp == "not_answerable" and t != REFUSAL_T:
                continue                                  # Rule 9: refused at REFUSAL_T only
            for c in CONFIGS:
                ks = defaultdict(list)
                for (cc, q, d), cl in sorted(cells.items()):
                    if cc != c or groups[q] != grp:
                        continue
                    if cl["kind"] == "scored":
                        ks["pass" if cl["score"] >= t else "fail"].append(cl["key"])
                    else:
                        ks[cl["kind"]].append(cl["key"])
                tr[f"{grp}|{metric} {t} or more|{c}"] = dict(ks)
    return tr


def summary_lines(res, res_out, dtext):
    """Plain sentences: who is first and last by mean at score 4 (PRIMARY, D154), and whether the test separates them
    (Rule 6)."""
    r6 = res["rule6"][PRIMARY]
    hi, lo = r6["highest"], r6["lowest"]

    def one(r, w):
        tie = f" (tied with {', '.join(LABEL[x] for x in r['tied_with'])})" if r["tied_with"] else ""
        if r["met"]:
            return f"{LABEL[r['strategy']]} has the {w} mean{tie}, and the test separates it from all five others"
        return (f"{LABEL[r['strategy']]} has the {w} mean{tie}, but the test cannot tell it apart from "
                + ", ".join(LABEL[x] for x in r["not_separated_from"]))
    return (f"At judge score {PRIMARY} or more, the pass rate ({dtext}): {one(hi, 'highest')}; {one(lo, 'lowest')}. "
            + ("Every number below rests on all three draws and stays provisional (D82) until the plate is made final."
               if dtext == dtext_of([1, 2, 3]) else
               "Every number below is provisional until the draws not read are judged and read."))


def dtext_of(draws):
    return "draw 1 of 3" if draws == [1] else f"draws {', '.join(map(str, draws))} of 3"


def vtxt(v):
    return "-" if v is None else v


def cr_report(crx, draws):
    """The report's concept-recall section (old panel b): the table and Rule 6 on the value drawn (D181's reading on key v2.5,
    D188), with the v2.4 loose anchor beside it."""
    if crx is None:
        return []
    lo_s, ex_s = crx["res"]["value"]["summary"], crx["res"]["exact"]["summary"]
    order = sorted(CONFIGS, key=lambda c: -lo_s[c]["rate_x"])
    an = crx.get("anchor") or {}
    L = ["## Concept recall on the 86 answerable questions (sheet Fig. 3a, not drawn)", "",
         f"{READING_TEXT[crx['info']['reading']]}, rows of {crx['info']['written_utc']}. {crx['info']['gate']}. "
         f"Read first: plan row L3's loose reading on key v2.4 (S471, {an.get('written_utc')}); {an.get('gate')}; "
         f"every answerable L3 row was scored again here from the generation record S3 judged and gave the same "
         f"values; {an.get('reproduced') or 'no committed v2.4 anchor applies to these inputs'}. "
         f"Per answer, the key's expected concepts found in it over the concepts counted (D181: a concept made only "
         f"of words of its question is not counted); per question the mean over {dtext_of(draws)}; the mean over the "
         f"86 questions with the Rule 2 interval. An answer with no text scores 0 and stays in (Rule 10): "
         f"{crx['res']['empty']} answers. An RLM answer whose record flags Mentor::i's fixed turn-limit note is scored "
         f"with the note removed (D115 L1e O-a): {crx['res']['note_removed']} answers.", "",
         "| Strategy | Concept recall (95% interval) | Exact substring, every concept (95% interval) | Failed answers, "
         "scored 0 |",
         "|---|---|---|---|"]
    for c in order:
        x, e = lo_s[c], ex_s[c]
        L.append(f"| {LABEL[c]} | {pct(x['rate'])}% ({pct(x['lo'])} to {pct(x['hi'])}) | {pct(e['rate'])}% "
                 f"({pct(e['lo'])} to {pct(e['hi'])}) | {len(crx['res']['failed'][c])} |")
    L.append("")
    for w in ("highest", "lowest"):
        r = crx["res"]["value"]["rule6"][w]
        tie = f", tied with {', '.join(LABEL[x] for x in r['tied_with'])}" if r["tied_with"] else ""
        L.append(f"- Concept recall, {w} by mean: {LABEL[r['strategy']]}{tie}. "
                 + ("Rule 6 is met: the test separates it from every other strategy." if r["met"] else
                    "Rule 6 is not met: it cannot be told apart from "
                    + ", ".join(LABEL[x] for x in r["not_separated_from"]) + "."))
    L += ["", "Rule 6 runs Rule 3's test on per-question means of the signal (LIST.md, Rule 6). All 15 pairs, "
          "unadjusted, are in the Source Data (sheet Fig. 3a) and ranking.json.", ""]
    return L


def cost_report(res, cost, draws):
    """The report's section for panel d."""
    ca, cl = cost["answerable"], cost["all"]
    s4 = res["answerable"][4]["summary"]
    f = lambda x, nd=1: S457.half_up(x, nd)                                 # noqa: E731
    L = ["## Quality against cost (panel d)", "",
         "Model calls per answer are the entries of each answer's generation.calls; clock time is generation.latency_s "
         "(S457.exp01_row reads both). Per question the mean over its draws, then the mean over the questions, with "
         "the Rule 2 interval from the same resamples as the pass rates. Failed answers count (their calls were made).",
         "", "| Strategy | Pass rate, score 4 or more (86) | Model calls per answer, 86 (95% interval) | all 135 | "
         "Clock time per answer (s), 86 | all 135 | of which waiting for the local server (s), 86 |",
         "|---|---|---|---|---|---|---|"]
    for c in CONFIGS:
        L.append(f"| {LABEL[c]} | {pct(s4[c]['rate'])}% | {f(ca[c]['calls']['mean'], 2)} ({f(ca[c]['calls']['lo'], 2)} "
                 f"to {f(ca[c]['calls']['hi'], 2)}) | {f(cl[c]['calls']['mean'], 2)} | {f(ca[c]['clock_s']['mean'])} | "
                 f"{f(cl[c]['clock_s']['mean'])} | {f(ca[c]['wait_s']['mean'])} |")
    ra, rl = cost["answerable"]["ratio_rlm10_single"], cost["all"]["ratio_rlm10_single"]
    L += ["", f"RLM-10 over single pass: {f(rl['calls'], 2)} times the model calls and {f(rl['clock_s'], 2)} times the "
          f"clock time on all 135 questions ({f(ra['calls'], 2)} and {f(ra['clock_s'], 2)} on the 86). The letter's "
          f"5.87 calls against 1.00 and 82.4 s against 10.4 (six and eight times) come from the submitted run "
          f"(findings/recompute/S77_r2q2_cost.json, reproduced by this run); claims.md sets them against these "
          f"records (C22, C47).", ""]
    return L


def flip_report(res, q78, draws):
    """The report's section for panel c."""
    nd = len(draws)
    L = ["## Each strategy against single pass (panel c, Rule 4)", "",
         f"Every single-pass draw of a question against every draw of the strategy ({nd * nd} pairings). Harmed and "
         "helped are means over the pairings of the questions changed; the shares are Rule 4's two denominators with "
         "the Rule 2 interval; P is Rule 3's exact two-sided sign-flip test (harmed minus helped is s - v per "
         "question). Same-draw totals are Rule 4 (a)'s three draw-d-against-draw-d tables added up.", "",
         "| Strategy | Score | Harmed | Helped | Harmful share of changed (95% interval) | Single pass's correct "
         "answers degraded (95% interval) | P | Same-draw totals, harmed / helped |", "|---|---|---|---|---|---|---|---|"]
    for t in THRESHOLDS:
        for c in FLIPPED:
            x = res["flips"][t][c]
            L.append(f"| {LABEL[c]} | {t} | {S457.half_up(x['harmed'], 2)} | {S457.half_up(x['helped'], 2)} | "
                     f"{pct(x['harm_share'])}% ({pct(x['harm_share_lo'])} to {pct(x['harm_share_hi'])}) | "
                     f"{pct(x['degraded_share'])}% ({pct(x['degraded_lo'])} to {pct(x['degraded_hi'])}) | "
                     f"{pfmt(x['p'])} | {x['same_draw_harmed']} / {x['same_draw_helped']} |")
    L += ["", "Noise baseline (Rule 4 (b)): each strategy's draws against each other, the share of a question's pairs "
          "of draws that disagree, and the fewest to the most questions passing on one draw and failing on another "
          "over the ordered pairs of draws (single pass's is the panel's band).", "",
          "| Strategy | Score | Disagreeing pairs of draws | Fewest to most per ordered pair |", "|---|---|---|---|"]
    for t in THRESHOLDS:
        for c in CONFIGS:
            x = res["self_flips"][t][c]
            L.append(f"| {LABEL[c]} | {t} | {pct(x['disagree_share'])}% | "
                     + ("-" if x["ordered_min"] is None else f"{x['ordered_min']} to {x['ordered_max']}") + " |")
    w = q78.get("res_without")
    if w:
        x3, x4 = w["flips"][3]["verified_pass"], w["flips"][4]["verified_pass"]
        L += ["", f"Verified pass without its {len(q78['not_ok'])} answers whose verifier was not ok (Q78): harmful "
              f"share {pct(x4['harm_share'])}% at score 4 and {pct(x3['harm_share'])}% at 3; degraded "
              f"{pct(x4['degraded_share'])}% and {pct(x3['degraded_share'])}%."]
    return L + [""]


def write_report(path, res, res_out, read, out_t, draws, stamp, order, collect, q78, cost, crx=None):
    s3, s4 = res["answerable"][3]["summary"], res["answerable"][4]["summary"]
    rf = res["refusal"][REFUSAL_T]["summary"]
    dtext = dtext_of(draws)
    nf = sum(len(v) for c in CONFIGS for v in out_t[c]["failed"].values())
    units = read["units"]["folders"]
    L = [f"# Figure 3, first ranking: {dtext}, provisional (D82, D88)", "",
         f"{stamp}.", "",
         f"Read by `scripts/S463_fig2_ranking.py rank` from `{collect}`: {read['rows']} rows under one run_sha256 "
         f"({str(read['run_sha256'])[:12]}) and lock {LOCK_WANT[:8]} (D88). {read['rows_read']} answers of the draws "
         f"read: {read['rows_read'] - nf} went to the judge, {nf} had no text and no judge call. The judge is {JUDGE} "
         f"(digest {JUDGE_DIGEST[:12]}, checked in each unit's headers), the plain call (a), with no passages in its "
         f"prompt. Each of the {len(units)} judging units read passed its recheck (the first answers judged again "
         f"after a fresh load gave the same scores). G1's reruns of 18 October in the draws read "
         f"({len(read['reruns_read'])} answers) come from their own pass (D93 Q-c), checked row by row. "
         f"The rules are experiments/LIST.md's (Rules 2, 3, 4, 5, 6, 9, 10, 11, 12); no rule is new (D84).", "",
         *([f"Judge rows (D186 (3)): each answer is read through scripts/judge_rows_v25.py, its key v2.5 row where "
            f"one exists, else its key v2.4 row; {read['judge_rows']['status']}.", ""] if read.get("judge_rows") else []),
         "## In short", "", summary_lines(res, res_out, dtext), "",
         "## Pass rate on the 86 answerable questions, highest first", "",
         "The pass rate is the share of answers the judge scores 4 or more; 3 or more is the relaxed threshold "
         "(LIST.md Rule 5, D154). Rank by the pass rate at 4.", "",
         "| Rank | Strategy | Score 4 or more, the pass rate (95% interval) | Score 3 or more, relaxed (95% interval) | "
         "Failed answers on the 86, counted as fails | Judge calls with no score on the 86, left out |",
         "|---|---|---|---|---|---|"]
    # audit 27 Oct F12 (fig1_2_5): counted within the 86 answerable questions, the table's group, as Source Data Fig.
    # 3a's answers_failed_counted_as_fail and judge_calls_without_score are (the table gave RLM-5 3 failed answers,
    # 2 of them on not-answerable questions)
    in_86 = lambda c, kind: sum(1 for (cc, q, d), cl in read["cells"].items()   # noqa: E731
                                if cc == c and cl["kind"] == kind and read["groups"][q] == "answerable")
    fails = {c: in_86(c, "failed") for c in CONFIGS}
    uns = {c: in_86(c, "unscored") for c in CONFIGS}
    for c in order:
        rk = 1 + sum(1 for o in CONFIGS if s4[o]["rate_x"] > s4[c]["rate_x"])
        L.append(f"| {rk} | {LABEL[c]} | {pct(s4[c]['rate'])}% ({pct(s4[c]['lo'])} to {pct(s4[c]['hi'])}) | "
                 f"{pct(s3[c]['rate'])}% ({pct(s3[c]['lo'])} to {pct(s3[c]['hi'])}) | {fails[c]} | {uns[c]} |")
    L += ["", f"Each rate is the mean over the questions of each question's pass share over the draws read "
          f"({dtext}); the interval resamples the questions 10,000 times (Rule 2). Questions with a share: "
          + ", ".join(f"{LABEL[c]} {s4[c]['questions_with_share']}" for c in CONFIGS) + ". The failed answers "
          "count for every strategy, on all three groups of questions; the table gives those on the 86.", ""]
    L += ["## Which pairs the test separates (all 15, unadjusted)", "",
          "Rule 3's exact two-sided sign-flip test on the per-question differences (on one draw, the exact McNemar "
          "test), P < 0.05, not adjusted for the 15 pairs (Rule 12). This describes; it claims nothing: a sentence "
          "about one pair rests on Rule 3 or Rule 6 for a comparison named there (the claims below). Each pair's "
          "difference, interval and P value are in ranking.json and the Source Data.", "",
          "| Strategy | Score 4 or more: above | below | not told apart from | Score 3 or more: above | below | not told "
          "apart from |", "|---|---|---|---|---|---|---|"]
    for c in order:
        cells_ = []
        for t in THRESHOLDS:
            pr = res["answerable"][t]["pairs"]
            up, down, same_ = [], [], []
            for o in CONFIGS:
                if o == c:
                    continue
                x = pair(pr, c, o)
                (same_ if x["p"] >= ALPHA else up if x["d_x"] > 0 else down).append(LABEL[o])
            cells_ += [", ".join(up) or "none", ", ".join(down) or "none", ", ".join(same_) or "none"]
        L.append(f"| {LABEL[c]} | " + " | ".join(cells_) + " |")
    L += ["",
          "## Highest and lowest (Rule 6) and the letter's claims (Rule 11)", "",
          "Rule 6 is stated at threshold 4, the pass rate (LIST.md Rule 6, D154). It is also given at 3, the relaxed "
          "threshold, because Rule 5 reports every pass-based statistic at both and Rule 11 gives a verdict at each "
          "threshold (D115 F2Q1 O-a: both thresholds kept).", ""]
    for t in THRESHOLDS:
        r6 = res["rule6"][t]
        for w in ("highest", "lowest"):
            r = r6[w]
            tie = f", tied with {', '.join(LABEL[x] for x in r['tied_with'])}" if r["tied_with"] else ""
            L.append(f"- Score {t} or more, {w} by mean: {LABEL[r['strategy']]}{tie}. "
                     + ("Rule 6 is met: the test separates it from every other strategy." if r["met"] else
                        "Rule 6 is not met: it cannot be told apart from "
                        + ", ".join(LABEL[x] for x in r["not_separated_from"]) + "."))
    L.append("")
    vp = q78.get("res_without")
    L.append("| Claim | Score 4 or more | Score 3 or more | With failed answers left out (4; 3) | "
             "Without the verified-pass answers whose verifier was not ok (4; 3) |")
    L.append("|---|---|---|---|---|")
    for cl in CLAIMS:
        k = cl[0]
        L.append(f"| {cl[1]} ({k}) | {vtxt(res['verdicts'][4][k])} | {vtxt(res['verdicts'][3][k])} | "
                 f"{vtxt(res_out['verdicts'][4][k])}; {vtxt(res_out['verdicts'][3][k])} | "
                 + (f"{vtxt(vp['verdicts'][4][k])}; {vtxt(vp['verdicts'][3][k])}" if vp else "none left out") + " |")
    diff = [f"{cl[0]} at score {t}" for t in THRESHOLDS for cl in CLAIMS
            if res["verdicts"][t][cl[0]] != res_out["verdicts"][t][cl[0]]]
    L += ["", "E6 is on refusal, which Rule 9 defines at score 3 only, so it has no verdict at 4. Verdict changed by "
          "leaving the failed answers out (Rule 10's sensitivity): " + (", ".join(diff) if diff else "none")
          + ". Every verdict here rests on " + dtext + " and is provisional.", "",
          "## Refusal on the 39 questions the papers cannot answer (Rule 9)", "",
          "| Strategy | Refused, refusal score 3 or more (95% interval) | False-premise passed, correctness 4 or more "
          "| Correctness 3 or more (relaxed) |", "|---|---|---|---|"]
    for c in CONFIGS:
        x = rf[c]
        rt = (f"0% (at most {pct(x['zero_bound'])}%, one-sided 95% upper bound)" if x["zero_bound"] is not None
              else f"100% (at least {pct(x['full_bound'])}%, one-sided 95% lower bound)" if x["full_bound"] is not None
              else f"{pct(x['rate'])}% ({pct(x['lo'])} to {pct(x['hi'])})")
        f3, f4 = res["false_premise"][3][c], res["false_premise"][4][c]
        L.append(f"| {LABEL[c]} | {rt} | {f4['passed']} of {f4['answers']} | {f3['passed']} of {f3['answers']} |")
    r6n = res["refusal"][REFUSAL_T]["rule6"]["highest"]
    tie = f" (tied with {', '.join(LABEL[x] for x in r6n['tied_with'])})" if r6n["tied_with"] else ""
    L += ["", f"Highest refusal by mean: {LABEL[r6n['strategy']]}{tie}; "
          + ("the test separates it from every other strategy." if r6n["met"] else
             "the test cannot tell it apart from " + ", ".join(LABEL[x] for x in r6n["not_separated_from"]) + ".")
          + " An answer with no text counts as not refused. The false-premise questions are counts only: ten "
          "questions give no interval and no test (Rule 9). Refusal is read at refusal score 3 or more only: Rule 9 "
          "defines it so, and Rule 5's second threshold is for pass-based statistics.", "",
          *cr_report(crx, draws), *cost_report(res, cost, draws), *flip_report(res, q78, draws),
          "## Verified pass: answers whose verifier was not ok (Rule 4, Q78)", ""]
    if not q78["read"]:
        L.append("Not read: rank was given no generation records.")
    else:
        L.append(f"Of the {q78['n_read']} verified-pass answers in the draws read, {len(q78['not_ok'])} had a verifier "
                 f"status other than ok ({', '.join(f'{k} {v}' for k, v in q78['status_counts_read'].items()) or 'none'}"
                 f"), and {len(q78['no_verification'])} stopped before the verifier ran. "
                 + ("Their keys: " + ", ".join(x["answer_key"] for x in q78["not_ok"]) + "." if q78["not_ok"] else ""))
        L.append("")
        L.append(f"Verified pass's verifier model: {q78['verifier']}, "
                 f"the local model of the verified-pass answers' calls in the draws read, named as S457 names it "
                 f"(F3-04, rulings page 6 Nov).")
        if vp:
            a3 = vp["answerable"][3]["summary"]["verified_pass"]
            a4 = vp["answerable"][4]["summary"]["verified_pass"]
            r3 = vp["refusal"][REFUSAL_T]["summary"]["verified_pass"]
            L.append("")
            L.append(f"Verified pass with them: pass rate {pct(s4['verified_pass']['rate'])}% at score 4, "
                     f"{pct(s3['verified_pass']['rate'])}% at 3, refused {pct(rf['verified_pass']['rate'])}%. Without "
                     f"them: {pct(a4['rate'])}% at 4, {pct(a3['rate'])}% at 3, refused {pct(r3['rate'])}%.")
    L += ["", "## Failed answers and other outcomes (Rule 10)", ""]
    any_f = False
    for c in CONFIGS:
        parts = []
        for kind, label in OUTCOME_KINDS.items():
            got = [f"{len(v)} {k}" for k, v in out_t[c][kind].items()]
            if got:
                parts.append(f"{label}: {', '.join(got)}")
        if parts:
            any_f = True
            L.append(f"- {LABEL[c]}: " + "; ".join(parts) + ".")
    if not any_f:
        L.append("- None.")
    L += ["", "The answer keys behind every count are in ranking.json. claims.md sets every number the main text, the "
          "submitted Figure 2 legend and the letter give for panels a, c, d and e against these values (D82).", "",
          "## What this does not show yet", "",
          *([f"- {dtext}: the pooled rate and the draw-to-draw spread (Rule 2) need all three draws. The same "
             "command with --draws 1,2,3 redraws everything."] if draws != [1, 2, 3] else []),
          *(["- Concept recall (sheet Fig. 3a, plan row L3): not given (--concept-recall)."]
            if crx is None else []),
          "- The replication on other generators (panel e, plan row T2): not drawn yet; its frame is empty.", ""]
    path.write_text("\n".join(L))


# ---------------------------------------------------------------------------------------------------------------
# the plates (D200, fig3.md section 4 and 6): Figure 3 and Supplementary Figure 16, on house_style's helpers
# ---------------------------------------------------------------------------------------------------------------
TEXT_GREY = hs.GREY["text"]                             # placeholder text: grey, 7.0:1 on white (lock 4.5:1)
BAND_GREY = hs.GREY["band"]                             # 3c's reference band (no text under 4.5:1)
NO_SCORE = "#D9D9D9"                                    # a tile whose question has a draw the judge gave no score
PLATE_H = 162.6                                         # measured on the 1 Nov plate; under [page] height_max_mm
PLATE_H_E3 = 169.5                                      # with 3e drawn (two axes, the reference group; 4 November):
#                                                          under FIGURE_LOCK [page] height_max_mm 170
PLATE_H_S5 = 95.0
ROWS_Y = (0.0, 50.0, 108.0)                             # the three rows of Figure 3
# Source Data row kinds of the marks the panels draw (each read back by check_drawn)
ORDER_KIND = "question order (columns, left to right)"   # Fig. 3a (86) and Fig. 3b (39): the question ids in plot order
TILE_KIND = "tile (question by strategy)"                # Fig. 3a, Fig. 3b: one tile per strategy, question (threshold)
BQ_KIND = "question (grey dot)"                          # concept recall, not drawn: a question's mean over its draws
BOX_KIND = "box (median, quartiles, range)"              # concept recall, not drawn: a strategy's box
CQ_KIND = "question (grey dot)"                          # Fig. 3d: a question's calls (mean over draws), pass share
PAIR_KIND = "pairing of draws (black dot)"               # Fig. 3c: one single-pass draw against one strategy draw
NOISE_KIND = "noise baseline (the strategy against itself)"
FLIP_KIND = "strategy against single pass"
C_JIT_X, C_JIT_Y = 0.07, 4.0                             # 3d's jitter: a factor exp(+-0.07) on calls, +-4 points
C_TICKS = (1, 2, 4, 8, 16, 32)                           # D129: log axis, ticks by doubling
C_XLIM = (0.8, 40.0)
E_SCALE = 20.0                                           # 3f's colour scale runs -20 to +20 points (S484.V); a cell
#                                                          past it takes the scale's end and prints its own number
E_ROWS = (("multi_hop", "all"), ("verified_pass", "all"), ("rlm_5", "all"), ("rlm_10", "all"), ("rlm_10", "one"),
          ("rlm_10", "many"), ("rlm_20", "all"))         # D200: the two split rows, first block only
A_ROW, A_TILE, A_GAP = 3.8, 3.4, 1.0                     # 3a: row pitch, tile height, gap before the two extra rows
A_H = 6 * A_ROW + A_GAP + 2 * A_ROW                      # 3a and 3b: the tile blocks' height
PERSON_DY = 1.5                                         # D231, D306: 3b's diamond, mm below its row's judge dot
PERSON_MS_MM = hs.ESTIMATE_MM * hs.MARKER_SCALE["D"]    # as large as the judge's dot, a diamond drawn at house scale
PERSON_MEW = 0.5                                        # its edge in pt, as the key's open marks (over [lines] 0.3 pt)
A_VIEW = (50.0, 100.0)                                   # 3a's and 3b's margin axes (Valerio's plate note, 2 November):
#                                                          the axis line and its two labels run 50 to 100; a value below
#                                                          50 stands left of the line on the same scale (margin_layout)
A_PAD = 2.5                                              # points of room beyond each end of that axis line
A_TILES_W = 64.5                                         # 3a's tiles, both blocks and their gap (D216 gave them the
#                                                          margins' width; D218 takes 34 mm back for the clock margin)
T_GAP, T_W, T_RIGHT = 2.5, 26.0, 123.5                   # D218: 3a's clock margin, gap after the tiles, axes width; the
#                                                          printed means end at T_RIGHT mm (3b starts at 127)
T_TICKS = (30, 100, 300)                                 # D218: log axis, these ticks only, no minor tick labels
T_XLIM = (10.0, 2000.0)                                  # widened only to hold a value beyond it (by 1.15 past it)
T_JIT_Y = 1.1                                            # the grey dots' vertical jitter within the row (mm, +-)
F_X = 80.0                                               # D218 (3): 3f (corpus size) left edge; 3e's frame at the left
D_GROUPS = (("one", "One paper", hs.OKABE["blue"], "s"), ("many", "Many papers", hs.OKABE["orange"], "D"),
            ("all", "All", hs.BLACK, "o"))               # D216: 3d's three marks, drawn in this order (All on top)
D_CROSS = hs.OKABE["vermillion"]                         # D224 Q2: vermilion, as Valerio's kept draft (corrects
#                                                          D216's "orange"); the key's entry takes this colour
D_MARK_NAME = {"all": "strategy's (All) black circle", "one": "one-paper blue square",
               "many": "many-paper orange diamond"}      # sheet Fig. 3a's drawn_in: the 3d mark that draws each rate
E_LAB, E_BG, E_CP, E_TW, E_TH, E_RP = 26.0, 2.0, 6.0, 5.6, 4.0, 4.4   # 3f: labels, block gap, column pitch, tile, row pitch
E_BLOCKS = ("All in scope", "The same 22", "Refusal, the same 39")
E_HEADS = ("All in scope", "The same 22", "Refusal, same 39")   # the drawn heads; E_BLOCKS stays the sheet key
# 3e (the T2 panel, D218 (3)): D289 (Valerio, manuscript tab, 7 Nov 10:50): only I is drawn, the many-paper gain
# minus the one-paper gain, on one axes at the panel's full width; D_one and D_many stay in sheet Fig. 3e, not drawn.
# No group heads; rows in E3_ROW_ORDER, a gap of E3_GAP before the sources beside the test; each I printed at E3_VX.
# Label column right edge, axes left and width, value column left edge, mm. E3_XLIM, E3_TICKS, E3_KEY and
# E3_ROLE_HEAD are no longer drawn here: S523 (Supplementary Figure 6) still reads them.
E3_LAB, E3_IX, E3_IXW, E3_VX = 37.0, 38.5, 32.0, 72.0
E3_RP, E3_OFF, E3_GAP = 4.6, 0.8, 2.0                    # a source's row pitch, the marks' offsets (S523), the gap
E3_ROW_ORDER = ("gemini-3-flash-preview", "second_judge", "gemma3", "qwen3-coder", "claude-haiku-4-5",
                "gemini-2.5-pro")                        # D289: Flash with each judge first, then the test, then beside
E3_XLIM, E3_TICKS = (-40.0, 70.0), (-25, 0, 25, 50)      # S523's axis (D_one, D_many), percentage points
E3_IXLIM, E3_ITICKS = (-20.0, 80.0), (-20, 0, 20, 40, 60, 80)   # I's axis, percentage points; a value outside is refused
E3_AXIS = {"one_paper": "D", "many_paper": "D", "interaction": "I"}   # the axes each measure belongs on (only I drawn)
E3_XLABEL = {"I": "Many-paper gain minus\none-paper gain\n(percentage points)"}   # under its axes, clear of 3f
E3_MARK = {"one_paper": (hs.OKABE["blue"], "s"), "many_paper": (hs.OKABE["orange"], "D"),
           "interaction": (hs.BLACK, "o")}               # D216's one-paper and many-paper marks (3d), I black
E3_DY = {"one_paper": -E3_OFF, "many_paper": E3_OFF, "interaction": 0.0}
E3_KEY = ("One paper", "Many papers", "Many-paper gain minus one-paper gain")   # S523's key; 3e draws none (D289)


def e3_layout(sources: list[tuple[str, str]]) -> tuple[dict, float]:
    """3e's rows in its axes' mm, top down (D289): the sources in E3_ROW_ORDER (any other after them, in the order
    given), one row pitch each, and a gap of E3_GAP before the first source beside the test. No heads. sources:
    (source, role) in S518.SOURCES order. Returns ({source: row centre}, height)."""
    role = dict(sources)
    order = [s for s in E3_ROW_ORDER if s in role] + list(dict.fromkeys(s for s, _ in sources if s not in E3_ROW_ORDER))
    y, ys, prev = 0.0, {}, None
    for s in order:
        if prev is not None and role[s] == "beside" and role[prev] != "beside":
            y += E3_GAP
        ys[s] = y + E3_RP / 2
        y += E3_RP
        prev = s
    return ys, y
LABEL_LONG = {"single_pass": fn.SINGLE_PASS, "multi_hop": fn.MULTI_HOP, "verified_pass": fn.VERIFIED_PASS,
              "rlm_5": fn.MENTORI_RLM_N.format(n=5), "rlm_10": fn.MENTORI_RLM_N.format(n=10),
              "rlm_20": fn.MENTORI_RLM_N.format(n=20), **{c: lb for c, _, lb in EXTRA}}
LABEL_E = {("multi_hop", "all"): fn.MULTI_HOP, ("verified_pass", "all"): fn.VERIFIED_PASS, ("rlm_5", "all"): fn.RLM_5,
           ("rlm_10", "all"): fn.RLM_10, ("rlm_10", "one"): "RLM-10, one paper", ("rlm_10", "many"): "RLM-10, many papers",
           ("rlm_20", "all"): fn.RLM_20}


def tile_colours(nd: int) -> dict:
    """Draws passed (refused) k of nd -> a cividis entry from [colour] continuous (S448 R5): more draws lighter, nd of
    nd yellow (D171 (1)), through hs.cividis_levels; with three draws the entries of the chosen mock-up (D127)."""
    lev = hs.cividis_levels(nd + 1)
    return {k: lev[k].upper() for k in range(nd + 1)}


def tile_rows(plate, pan):
    """A tile block's rows, top to bottom: (arms, each row's top in mm from the axes' top, row pitch, tile height). draw
    places the rows from here and check_drawn holds each artist's own y to it."""
    if plate == "s5":
        return list(CONFIGS), [i * A_ROW for i in range(6)], A_ROW, A_TILE
    if pan == "a":
        return ([*CONFIGS, *EXTRA_DRAWN], [i * A_ROW for i in range(6)] + [6 * A_ROW + A_GAP + i * A_ROW for i in range(2)],
                A_ROW, A_TILE)
    row_b = A_H / 6
    return list(CONFIGS), [i * row_b for i in range(6)], row_b, row_b - 0.4


def margin_layout(lows, x0, x1):
    """Margin columns side by side from x0 to x1 mm, one per lowest value drawn, on A_VIEW: [(axes x, axes width, x limits)].
    Every column has one scale, and the axis line of each runs A_VIEW. A value below the view gives its column room on
    the left at that same scale, so the mark stands where it belongs, left of the axis line's end, and nothing is clipped
    or moved. The gap leaves room for the tick labels 100 and 50 unless the room on the left already does."""
    lo, hi = A_VIEW
    span = hi - lo + 2 * A_PAD
    under = [max(0.0, lo - v) for v in lows]
    gaps = [0.0] + [3.5] * (len(under) - 1)
    for _ in range(3):
        mm = (x1 - x0 - sum(gaps)) / (len(under) * span + sum(under))
        gaps = [0.0] + [max(1.2, 3.5 - u * mm) for u in under[1:]]
    out, x = [], x0
    for g, u in zip(gaps, under):
        x += g
        out.append((x, (span + u) * mm, (lo - A_PAD - u, hi + A_PAD)))
        x += (span + u) * mm
    return out


def margin_axis(vals):
    """A margin's percent axis: its low end, step and limits. 60 to 100 by 20 when every value drawn is 60 or more;
    lower ends by 20 down to 40; below that 0 or 50 by 50."""
    lo = min([60.0] + [20 * math.floor(v / 20) for v in vals if v is not None])
    if 100 - lo > 60:
        lo, step = 50 * math.floor(lo / 50), 50
    else:
        step = 20
    pad = 0.05 * (100 - lo)
    return lo, step, (lo - pad, 100 + pad)


def pairing_counts(sh, c, draws):
    """3c's black dots: for each single-pass draw d and strategy draw e (Rule 1: draws are not paired by their number),
    the questions single pass passes on d and the strategy fails on e (harmed), and the reverse (helped)."""
    from itertools import product
    out = []
    for d, e in product(draws, draws):
        h = sum(1 for q in sh["single_pass"] if sh["single_pass"][q][1][d] == 1 and sh[c][q][1][e] == 0)
        g = sum(1 for q in sh["single_pass"] if sh["single_pass"][q][1][d] == 0 and sh[c][q][1][e] == 1)
        out.append((d, e, h, g))
    return out


def stack(vals, pitch):
    """Equal values get offsets across the row centred on 0, pitch apart."""
    seen, n = Counter(), Counter(vals)
    out = []
    for v in vals:
        out.append((seen[v] - (n[v] - 1) / 2) * pitch)
        seen[v] += 1
    return out


def read_book(sd: Path) -> dict:
    """The Source Data workbook as written, read back: {sheet: [row dict]} (an empty cell is None)."""
    from openpyxl import load_workbook
    wb = load_workbook(sd, read_only=True)
    out = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        out[ws.title] = [{k: (None if v == "" else v) for k, v in zip(rows[0], r)} for r in rows[1:]]
    return out


class Plate:
    """One figure on house_style: the page, the printed-number map S448 R8 (6) reads, and rb, every data mark with what
    check_drawn needs to find its row."""

    def __init__(self, W, H):
        import logging
        logging.getLogger("fontTools").setLevel(logging.ERROR)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update(hs.rc("S463"))
        self.W, self.H, self.plt = W, H, plt
        if H > S457.FIG_H_MAX_MM - S457.H_ROOM_MM:
            raise Refused(f"a plate of {H} mm is over the lock's {S457.FIG_H_MAX_MM} mm")
        self.fig = hs.figure(W, H)
        self.printed, self.rb = {}, []

    def num(self, artist, entry):
        gid = f"s448num_{len(self.printed)}"
        artist.set_gid(gid)
        self.printed[gid] = entry
        return artist

    def fixed(self, artist, why):
        return self.num(artist, {"fixed": artist.get_text(), "why": why})

    def text(self, x, y, s, why="a label", **kw):
        """Text at (x, y) mm, its centre on y unless va is given; a text holding a digit is declared fixed."""
        t = hs.text_mm(self.fig, x, y, s, **{"va": "center", **kw})
        if any(ch.isdigit() for ch in s):
            self.fixed(t, why)
        return t

    def key(self, items, why="the key to the marks", **kw):
        n0 = len(self.fig.texts)
        out = hs.key(self.fig, items, **kw)
        for t in self.fig.texts[n0:]:
            if any(ch.isdigit() for ch in t.get_text()):
                self.fixed(t, why)
        return out

    def frame(self, x, y, w, h):
        """An empty frame, four spines and nothing inside (D122 Q4)."""
        ax = hs.axes_mm(self.fig, x, y, w, h, spines_on=("left", "right", "top", "bottom"))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        return ax

    def finish(self, paths, title, sd, nd, plate):
        probs, summary = check_drawn(self.rb, read_book(sd), nd, plate)
        if probs:
            self.plt.close(self.fig)
            raise Refused(f"check_drawn: {len(probs)} drawn mark(s) differ from the workbook: {probs[:3]}")
        bad = hs.check_figure_colours(self.fig)
        if bad:
            self.plt.close(self.fig)
            raise Refused(f"{title}: colours outside the house palette: {bad}")
        try:
            S457.finish_plate(self.fig, self.W, self.H, paths, title)
        except SystemExit as e:                          # texts off the page or on each other: no plate
            self.plt.close(self.fig)
            raise Refused(str(e)) from None
        return self.W, self.H, self.printed, {"marks": self.rb, "summary": summary, "nd": nd, "fig_texts": list(self.fig.texts)}


def rows_of(book, sheet, kind):
    return [r for r in book[sheet] if r["row_kind"] == kind]


def order_blocks(book, sheet):
    """The question ids in plot order, as one list per question type (3a, S5a) or one list (3b)."""
    rows = sorted(rows_of(book, sheet, ORDER_KIND), key=lambda r: r["plot_position"])
    if rows and rows[0].get("question_type"):
        return [[r["question_id"] for r in rows if r["question_type"] == g] for g in ("one", "many")]
    return [[r["question_id"] for r in rows]]


def draw_tiles(P, panel, sheet, book, x_t, top, ws, gap, h, ypos, row, tile, arms, t, val, lev, nd):
    """Question-by-row tiles, one axes per block of questions: each tile coloured by its draws passed (refused), the
    no-score grey when a draw has no score, stroked in its own colour so no hairline shows between neighbours."""
    from matplotlib.patches import Rectangle
    blocks = order_blocks(book, sheet)
    tiles = {(r["threshold"], r["strategy"], r["question_id"]): r for r in rows_of(book, sheet, TILE_KIND)}
    x, noscore = x_t, False
    for b, (ids, w) in enumerate(zip(blocks, ws)):
        ax = hs.axes_mm(P.fig, x, top, w, h)
        ax.set_xlim(0, len(ids))
        ax.set_ylim(h, 0)
        ax.spines["left"].set_visible(False)
        ax.set_yticks([])
        ticks, labels = ([0.5, len(ids) - 0.5], ["1", str(len(ids))]) if b == 0 else ([len(ids) - 0.5], [str(len(ids))])
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        ax.tick_params(axis="x", pad=1)
        if panel == "b":                                 # clear of the margin's first tick label
            ax.get_xticklabels()[-1].set_ha("right")
        for c, y in zip(arms, ypos):
            for j, q in enumerate(ids):
                r = tiles[(t, c, q)]
                col = lev[r[val]] if r["draws_scored"] == nd else NO_SCORE
                noscore |= r["draws_scored"] != nd
                p = Rectangle((j, y + (row - tile) / 2), 1, tile, fc=col, ec=col, lw=0.35)
                ax.add_patch(p)
                P.rb.append({"panel": panel, "kind": "tile", "t": t, "c": c, "q": q, "artist": p, "ax": ax, "block": b})
        x += w + gap
    return noscore


def margin_column(P, panel, x, top, w, h, lim, lo, step, rows, ypos, row, col, vkey, lokey, hikey, bounds=None):
    """One margin column (3b, S5a): per row a filled dot and its interval, dashed from the dot where a rate of 0 or 100%
    has its one-sided bound; with bounds the axis line stops at those two values."""
    ax = hs.axes_mm(P.fig, x, top, w, h)
    ax.set_xlim(*lim)
    ax.set_ylim(h, 0)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    if bounds:
        ax.spines["bottom"].set_bounds(*bounds)
    tk = [lo + step * k for k in range(int((100 - lo) / step) + 1)]
    if tk[0] < 75 < tk[-1] and 75 not in tk:                  # Valerio, 3 Nov: 75 marked, near the RLM rows
        tk = sorted(tk + [75])
    room = (hs._text_width_mm("75") + hs._text_width_mm("100")) / 2 + 0.4   # 75 labelled where its label clears 100's
    lab75 = 25 * w / (lim[1] - lim[0]) >= room                # (a column squeezed by a value below 50 has no room)
    ax.set_xticks(tk)
    ax.set_xticklabels([f"{v:g}" if v in (tk[0], tk[-1]) or (v == 75 and lab75) else "" for v in tk])   # a narrow column
    ax.tick_params(axis="x", pad=1)
    for c, y in zip(rows, ypos):
        r = rows[c]
        yy = y + row / 2
        dashed = one_sided(r)
        if r[hikey] > r[lokey]:
            ends = [r[hikey], r[lokey]] if dashed and r[vkey] == r[hikey] else [r[lokey], r[hikey]]
            ln = ax.plot(ends, [yy, yy], color=hs.BLACK, lw=hs.LW["interval"], solid_capstyle="butt", zorder=6,
                         clip_on=False, **({"ls": (0, (2.0, 1.2)), "dash_capstyle": "butt"} if dashed else {}))[0]
            P.rb.append({"panel": panel, "kind": "margin bar", "col": col, "c": c, "artist": ln, "ax": ax,
                         "dashed": dashed})
        dt = ax.plot([r[vkey]], [yy], ls="none", marker="o", ms=hs.ESTIMATE_MM / hs.MM_PT, mfc=hs.BLACK, mec="none",
                     mew=0, zorder=7, clip_on=False)[0]
        P.rb.append({"panel": panel, "kind": "margin dot", "col": col, "c": c, "artist": dt, "ax": ax})
    return ax


def clock_xlim(vals):
    """3a's clock margin limits: T_XLIM, or past a value outside it by a factor 1.15 (nothing clipped)."""
    lo, hi = T_XLIM
    if not vals:
        return T_XLIM
    return (lo if min(vals) >= lo else min(vals) / 1.15, hi if max(vals) <= hi else max(vals) * 1.15)


def draw_clock_margin(P, book, x, top, w, h, arms, ypos, row):
    """D218 (1): per 3a row its questions' clock time per answer less the wait for the local server (each the mean over
    its draws) as grey dots, jittered up and down within the row only (+-T_JIT_Y mm); the mean over the questions as a
    black dot; the mean printed in seconds right of the margin. Log axis, ticks T_TICKS, no interval drawn."""
    import numpy as np
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    A = book["Fig. 3a"]
    dots = defaultdict(list)
    for r in A:
        if r["row_kind"] == MARGIN_Q_KIND:
            dots[r["strategy"]].append(r["clock_less_wait_s_mean_over_draws"])
    means = {r["strategy"]: (i, r) for i, r in enumerate(A) if r["row_kind"] == MARGIN_KIND}
    ax = hs.axes_mm(P.fig, x, top, w, h)
    ax.set_xscale("log")
    lim = clock_xlim([v for vs in dots.values() for v in vs])
    ax.set_xlim(*lim)
    ax.set_ylim(h, 0)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(FixedLocator(list(T_TICKS)))
    ax.set_xticklabels([str(t) for t in T_TICKS])
    ax.get_xticklabels()[0].set_ha("right")             # the end labels lean outwards: on 26 mm, 100 and 300 are
    ax.get_xticklabels()[-1].set_ha("left")             # about 5 mm apart, as wide as one label, so centred they touch
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="x", pad=1)
    for j, (c, y) in enumerate(zip(arms, ypos)):
        yy = y + row / 2
        xs = dots.get(c, [])
        rng = np.random.default_rng(SEED + 100 + j)      # the jitter, the same on every run
        jy = rng.uniform(-T_JIT_Y, T_JIT_Y, len(xs))
        gd = ax.plot(xs, [yy + g for g in jy], ls="none", marker="o", ms=hs.DOT_MM / hs.MM_PT, mfc=hs.GREY["dot"],
                     mec="none", mew=0, zorder=2, clip_on=False)[0]
        P.rb.append({"panel": "a", "kind": "clock dots", "c": c, "artist": gd, "ax": ax})
        if c not in means:
            continue
        i, r = means[c]
        md = ax.plot([r["clock_less_wait_s_mean"]], [yy], ls="none", marker="o", ms=hs.ESTIMATE_MM / hs.MM_PT,
                     mfc=hs.BLACK, mec=hs.WHITE, mew=0.3, zorder=7, clip_on=False)[0]
        P.rb.append({"panel": "a", "kind": "clock mean", "c": c, "artist": md, "ax": ax})
        t_ = P.num(hs.text_mm(P.fig, T_RIGHT, top + yy, r["printed"], ha="right", va="center"),
                   {"sheet": "Fig. 3a", "row": i, "format": "{clock_less_wait_s_mean:.0f} s"})
        P.rb.append({"panel": "a", "kind": "clock value", "c": c, "text": t_, "ax": ax, "artist": None})
    return ax


def group_rows(book, sheet, t, group):
    kind = "strategy" if group == "all" else GROUP_KIND
    return {r["strategy"]: r for r in rows_of(book, sheet, kind) if r["threshold"] == t
            and r.get("question_group", "all") == group}


def draw_butterfly(P, panel, sheet, book, x_a, top, w, h, labels_x, nd, reruns):
    """Each strategy against single pass: harmed bars left, helped right (vermillion, blue), the means over the draw
    pairings, the pairings as black dots. With reruns (S5b; 3c has none, Valerio's plate note of 2 November) also under
    each bar the strategy's ordered rerun counts as grey dots, a top row and a band with single pass's own."""
    from matplotlib.patches import Rectangle
    E = book[sheet]
    t = E[0]["threshold"]
    fl = {r["strategy"]: r for r in E if r["row_kind"] == FLIP_KIND}
    nb = {r["strategy"]: r for r in E if r["row_kind"] == NOISE_KIND}
    pr = defaultdict(list)
    for r in E:
        if r["row_kind"] == PAIR_KIND:
            pr[r["strategy"]].append((r["harmed"], r["helped"]))

    def ordered(c):
        return sorted(v for k_, v in nb[c].items() if k_.startswith("pass_on_") and v is not None)
    rows = (["single_pass"] if reruns else []) + FLIPPED
    vmax = max([1.0] + [v for x in pr.values() for p in x for v in p]
               + [v for k_ in fl.values() for v in (k_["harmed_mean_over_pairings"], k_["helped_mean_over_pairings"])]
               + ([v for c in CONFIGS for v in ordered(c)] if reruns else []))
    XM = 5 * math.ceil((vmax + 1) / 5)
    step = 10 if XM >= 20 else 5
    ax = hs.axes_mm(P.fig, x_a, top, w, h)
    ax.set_xlim(-XM, XM)
    ax.set_ylim(h, 0)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    tk = [step * k for k in range(-int(XM // step), int(XM // step) + 1)]
    ax.set_xticks(tk)
    ax.set_xticklabels([f"{abs(v):g}" for v in tk])
    ax.tick_params(axis="x", pad=1)
    pitch = h / len(rows)
    worse, better = hs.colour("comparison", "worse"), hs.colour("comparison", "better")
    if reruns:
        b0, b1 = nb["single_pass"]["ordered_pairs_min"], nb["single_pass"]["ordered_pairs_max"]
        for sgn in (-1, 1):
            if b1 > b0:
                bd = Rectangle((min(sgn * b0, sgn * b1), 0), b1 - b0, h, fc=BAND_GREY, ec="none", lw=0, zorder=0)
                ax.add_patch(bd)
            else:
                bd = ax.plot([sgn * b0] * 2, [0, h], color=BAND_GREY, lw=1.2, zorder=0)[0]
            P.rb.append({"panel": panel, "kind": "band", "side": sgn, "artist": bd, "ax": ax})
    hs.reference_line(ax, 0, zorder=5)
    for j, c in enumerate(rows):
        y = j * pitch
        lb_ = P.text(labels_x, top + y + pitch / 2, "single pass rerun" if c == "single_pass" else LABEL[c], ha="right",
                     why="the strategy's name")
        P.rb.append({"panel": panel, "kind": "row label", "c": c, "text": lb_, "ax": ax, "artist": None})
        bar_y = y + pitch * (0.40 if reruns else 0.5)
        grey_y = y + pitch * 0.5 if c == "single_pass" else y + pitch * 0.84
        if reruns:
            rr = ordered(c)
            for sgn in (-1, 1):
                off = stack(rr, 0.42)
                gd = ax.plot([sgn * v for v in rr], [grey_y + o for o in off], ls="none", marker="o", ms=0.55 / hs.MM_PT,
                             mfc=hs.GREY["dot"], mec="none", mew=0, zorder=3)[0]
                P.rb.append({"panel": panel, "kind": "rerun dots", "c": c, "side": sgn, "artist": gd, "ax": ax})
        if c == "single_pass":
            continue
        r = fl[c]
        th = pitch * 0.52
        for sgn, v, col in ((-1, r["harmed_mean_over_pairings"], worse), (1, r["helped_mean_over_pairings"], better)):
            br = Rectangle((min(0, sgn * v), bar_y - th / 2), v, th, fc=col, ec="none", lw=0, zorder=2)
            ax.add_patch(br)
            P.rb.append({"panel": panel, "kind": "bar", "c": c, "side": sgn, "artist": br, "ax": ax})
            vs = sorted(p[0 if sgn < 0 else 1] for p in pr[c])
            off = stack(vs, 0.30)
            bd = ax.plot([sgn * v_ for v_ in vs], [bar_y + o for o in off], ls="none", marker="o", ms=0.42 / hs.MM_PT,
                         mfc=hs.BLACK, mec="none", mew=0, zorder=4)[0]
            P.rb.append({"panel": panel, "kind": "pairing dots", "c": c, "side": sgn, "artist": bd, "ax": ax})
    return t, rows


def butterfly_key(P, x, y, w, reruns):
    items = [("swatch", hs.colour("comparison", "worse"), "harmed"), ("swatch", hs.colour("comparison", "better"), "helped"),
             ("mark", (hs.BLACK, "o"), "one pairing of draws")]
    if reruns:
        items += [("mark", (hs.GREY["dot"], "o"), "one rerun"),
                  ("swatch", hs.GREY["band"], "single pass rerun, lowest to highest")]
    P.key(items, centre_x=x + 4 + w / 2, y=y, max_width=w - 8)


def draw(book, paths, sd, nd):
    """Figure 3's six panels (fig3.md section 4), 183 x PLATE_H mm, in three rows: a | b, c | d, e | f. Every mark comes
    from the Source Data rows in book; check_drawn then reads each mark back from its artist and holds it to the workbook
    written at sd before the plate is saved (a mismatch is a refusal, no plate). Returns (W, H, printed, drawn)."""
    import numpy as np
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    hs.check_plate_kinds(["comparison"])
    W, H = S457.FIG_W_MM, (PLATE_H_E3 if "Fig. 3e" in book and rows_of(book, "Fig. 3e", E3_KIND) else PLATE_H)
    P = Plate(W, H)
    fig = P.fig
    LEV = tile_colours(nd)
    R1, R2, R3 = ROWS_Y

    # ---- a: pass tiles (D215, D216: the three margin columns went; 3d draws their rates) ---------------------------
    X, Y, WA = 0.0, R1, 124.0
    LAB, GAPG, TW_ = 23.0, 1.5, A_TILES_W
    top = Y + 7.2
    h_a = A_H
    arms, ypos, row_a, tile_a = tile_rows("fig3", "a")
    x_t = X + LAB
    blocks = order_blocks(book, "Fig. 3a")
    n1, n2 = (len(b) for b in blocks)
    w1, w2 = (TW_ - GAPG) * n1 / (n1 + n2), (TW_ - GAPG) * n2 / (n1 + n2)
    hs.panel_letter(fig, X, Y + 2.4, "a")
    noa = draw_tiles(P, "a", "Fig. 3a", book, x_t, top, (w1, w2), GAPG, h_a, ypos, row_a, tile_a, arms, PRIMARY,
                     "draws_passed", LEV, nd)
    P.key([("swatch", LEV[k], f"{k}" + (f" of {nd}" if k == 0 else "")) for k in range(nd, -1, -1)]
          + ([("swatch", NO_SCORE, "no score")] if noa else []),
          centre_x=X + 3.0 + WA / 2, y=Y + 2.4, title="Draws passed:", max_width=WA + 12)
    for b, (head, x_h) in enumerate((("One paper", x_t), ("Many papers", x_t + w1 + GAPG))):
        P.rb.append({"panel": "a", "kind": "block head", "block": b, "text": P.text(x_h, Y + 5.3, head), "artist": None})
    for c, y in zip(arms, ypos):
        lb_ = P.text(x_t - 1.0, top + y + row_a / 2, LABEL_LONG[c], ha="right", why="the row's name")
        P.rb.append({"panel": "a", "kind": "row label", "c": c, "text": lb_, "artist": None})
    y_lab = top + h_a + 6.2
    hs.text_mm(fig, x_t + TW_ / 2, y_lab, "Question, sorted within each group", ha="center")
    x_m = x_t + TW_ + T_GAP                              # D218 (1): the clock-time margin
    draw_clock_margin(P, book, x_m, top, T_W, h_a, arms, ypos, row_a)
    hs.text_mm(fig, x_m + T_W / 2, y_lab, "Time per answer (s)", ha="center")

    # ---- b: refusal tiles ----------------------------------------------------------------------------------------
    X, WB = 127.0, 56.0
    LAB, TWB, MW = 21.5, 18.5, 11.0
    x_t = X + LAB
    _, ypb, row_b, tile_b = tile_rows("fig3", "b")
    hs.panel_letter(fig, X, Y + 2.4, "b")
    srows = {r["strategy"]: r for r in rows_of(book, "Fig. 3b", "refusal")}
    draw_tiles(P, "b", "Fig. 3b", book, x_t, top, (TWB,), 0, h_a, ypb, row_b, tile_b, CONFIGS, REFUSAL_T,
               "draws_refused", LEV, nd)
    for c, y in zip(CONFIGS, ypb):
        lb_ = P.text(x_t - 1.0, top + y + row_b / 2, LABEL_LONG[c], ha="right", why="the row's name")
        P.rb.append({"panel": "b", "kind": "row label", "c": c, "text": lb_, "artist": None})
    xm = x_t + TWB + 2.5
    x_m, w_m, lim = margin_layout([min(v for r in srows.values() for v in (r["refused_pct"], r["bar_drawn_from_pct"]))],
                                  xm, xm + MW)[0]
    ax_bm = margin_column(P, "b", x_m, top, w_m, h_a, lim, A_VIEW[0], 25, {c: srows[c] for c in CONFIGS}, ypb, row_b,
                          "all", "refused_pct", "bar_drawn_from_pct", "bar_drawn_to_pct", bounds=A_VIEW)
    # D231, D306: the person's refused share on draw 1 (an open diamond, PERSON_DY below the judge's dot on its row)
    prow = {r["strategy"]: r for r in rows_of(book, "Fig. 3b", PERSON_KIND)}
    for c, y in zip(CONFIGS, ypb):
        if c in prow:
            dm = ax_bm.plot([prow[c]["person_refused_pct"]], [y + row_b / 2 + PERSON_DY], ls="none", marker="D",
                            ms=PERSON_MS_MM / hs.MM_PT, mfc=hs.WHITE, mec=hs.BLACK, mew=PERSON_MEW, zorder=8,
                            clip_on=False)[0]
            P.rb.append({"panel": "b", "kind": "person mark", "c": c, "artist": dm, "ax": ax_bm})
    if prow:
        n0 = len(fig.texts)
        P.key([("mark", (hs.BLACK, "o"), "judge, 3 draws"), ("open", (hs.BLACK, "D"), "person, draw 1")],
              centre_x=X + WB / 2, y=Y + 2.4, max_width=WB - 4)
        for t_ in fig.texts[n0:]:
            P.rb.append({"panel": "b", "kind": "key text", "text": t_, "artist": None})
    hs.text_mm(fig, x_t + TWB / 2, y_lab, "Question", ha="center")
    hs.text_mm(fig, xm + MW / 2, y_lab, "Refused (%)", ha="center")

    # ---- c: harmed and helped at score 4 ---------------------------------------------------------------------------
    X, Y, WC, LAB = 0.0, R2, 73.0, 22.5
    hs.panel_letter(fig, X, Y + 2.4, "c")
    butterfly_key(P, X, Y + 2.4, WC, False)
    t_c, _ = draw_butterfly(P, "c", "Fig. 3c", book, X + LAB, Y + 8.0, WC - LAB, 35.2, X + LAB - 1.0, nd, False)
    hs.text_mm(fig, X + LAB + (WC - LAB) / 2, Y + 8.0 + 35.2 + 6.5, "Questions harmed (left) or helped (right)", ha="center")
    P.text(X + LAB + (WC - LAB) / 2, Y + 8.0 + 35.2 + 10.0, f"at judge score {t_c} or more", ha="center", va="baseline",
           why="the axis label")

    # ---- d: six cost scatters --------------------------------------------------------------------------------------
    X, Y, WD = 76.0, R2, 107.0
    AX0, GAPC, GH = 11.5, 3.0, 15.6
    cw = (WD - AX0 - 2 * GAPC) / 3
    tops = (Y + 8.0, Y + 28.6)
    hs.panel_letter(fig, X, Y + 2.4, "d")
    D = "Fig. 3d"
    gm = {(r["strategy"], r["question_group"]): r for r in rows_of(book, D, GROUP_D_KIND)}
    nq_g = {g: gm[(CONFIGS[0], g)]["questions"] for g, *_ in D_GROUPS}
    # D216: one line, centred over 3d, no entry for the grey dots; each group's n read from its rows
    n0 = len(fig.texts)
    P.key([("mark", (col_, mk_), f"{head} {nq_g[g]}") for g, head, col_, mk_ in (D_GROUPS[2], D_GROUPS[0], D_GROUPS[1])]
          + [("open", (hs.BLACK, "o"), f"score {THRESHOLDS[1]}"), ("mark", (D_CROSS, "X"), fn.MATCHED_BUDGET)],
          centre_x=X + WD / 2, y=Y + 2.4, max_width=None)
    for t_ in fig.texts[n0:]:
        P.rb.append({"panel": "d", "kind": "key text", "text": t_, "artist": None})
    cq = defaultdict(list)
    for r in rows_of(book, D, CQ_KIND):
        if r["pass_share_t4_pct"] is not None:
            cq[r["strategy"]].append((r["calls_per_answer_question_mean"], r["pass_share_t4_pct"]))
    out_c = [f"{c} {x}" for c, v in cq.items() for x, _ in v if not C_XLIM[0] * 1.08 <= x <= C_XLIM[1] / 1.08]
    if out_c:
        raise Refused(f"panel d: model calls per answer outside the log axis {C_XLIM}: {out_c[:3]}")
    cross = next((r for r in book[D] if r["row_kind"] == CROSS_KIND), None)
    for j, c in enumerate(CONFIGS):
        r_, col = divmod(j, 3)
        x0, y0 = X + AX0 + col * (cw + GAPC), tops[r_]
        ax = hs.axes_mm(fig, x0, y0, cw, GH)
        ax.set_xscale("log", base=2)
        ax.set_xlim(*C_XLIM)
        ax.xaxis.set_major_locator(FixedLocator(list(C_TICKS)))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_ylim(-10, 110)
        ax.set_yticks([0, 50, 100])
        ax.spines["left"].set_bounds(0, 100)
        ax.tick_params(pad=1)
        if col:
            ax.set_yticklabels([])
        if r_ == 0:
            ax.set_xticklabels([])
        rng = np.random.default_rng(SEED + j)            # the jitter, the same on every run
        xy = cq[c]
        jx = np.exp(rng.uniform(-C_JIT_X, C_JIT_X, len(xy)))
        jy = rng.uniform(-C_JIT_Y, C_JIT_Y, len(xy))
        dt = ax.plot([x * f for (x, _), f in zip(xy, jx)], [y + g for (_, y), g in zip(xy, jy)], ls="none", marker="o",
                     ms=hs.DOT_MM / hs.MM_PT, mfc=hs.GREY["dot"], mec="none", mew=0, zorder=2, clip_on=False)[0]
        P.rb.append({"panel": "d", "kind": "dots", "c": c, "artist": dt, "ax": ax})
        # D216: per question group one mark at its mean calls, filled at score 4, open (white, its colour's edge) at 3;
        # no interval on any mark (the grey dots show the spread; the intervals stay in sheet Fig. 3d)
        for k_, (g, _, col_, mk_) in enumerate(D_GROUPS):
            r = gm[(c, g)]
            for t, key_ in ((THRESHOLDS[1], "pass_rate_t3_pct"), (PRIMARY, "pass_rate_t4_pct")):
                st = ({"mfc": col_, "mec": hs.WHITE} if t == PRIMARY else {"mfc": hs.WHITE, "mec": col_})
                mk = ax.plot([r["calls_mean"]], [r[key_]], ls="none", marker=mk_, mew=0.5, clip_on=False,
                             ms=hs.ESTIMATE_MM * hs.MARKER_SCALE.get(mk_, 1.0) / hs.MM_PT,
                             zorder=(10 if t == PRIMARY else 6) + k_, **st)[0]   # open marks under all filled
                P.rb.append({"panel": "d", "kind": "group mark", "c": c, "g": g, "t": t, "artist": mk, "ax": ax})
        if c == "rlm_10" and cross is not None:
            mk = ax.plot([cross["calls_mean"]], [cross["pass_rate_t4_pct"]], ls="none", marker="X", ms=2.4 / hs.MM_PT,
                         mfc=D_CROSS, mec="none", mew=0, zorder=13, clip_on=False)[0]
            P.rb.append({"panel": "d", "kind": "cross", "artist": mk, "ax": ax})
        # the strategy's name on top and no other text (Valerio's plate note, 2 November); the multiples stay in sheet 3d
        P.rb.append({"panel": "d", "kind": "name", "c": c, "ax": ax, "artist": None,
                     "text": P.text(x0 + cw / 2, y0 - 0.9, LABEL[c], ha="center", va="baseline", why="the strategy's name")})
    hs.text_mm(fig, X + 3.4, (tops[0] + tops[1] + GH) / 2, "Share of draws passing (%)", ha="center", va="center",
               rotation=90)
    hs.text_mm(fig, X + AX0 + (WD - AX0) / 2, tops[1] + GH + 7.1, "Model calls per question (agent and sub-agent calls)",
               ha="center")

    # ---- e: the T2 panel (D218 (3), at the left): S518's verdicts (D195), or an empty frame with none read ---------
    hs.panel_letter(fig, 0.0, R3 + 2.4, "e")
    E3 = [r for r in book["Fig. 3e"] if r["row_kind"] == E3_KIND]
    if not E3:
        P.frame(4.0, R3 + 8.4, 70.0, 45.6)
    else:
        lim3 = {"D": E3_XLIM, "I": E3_IXLIM}
        out_e = [f"{r['source']} {r['measure']}" for r in E3 for v in (r["d_pp"], r["ci95_lo_pp"], r["ci95_hi_pp"])
                 if not lim3[E3_AXIS[r["measure"]]][0] <= v <= lim3[E3_AXIS[r["measure"]]][1]]
        if out_e:
            raise Refused(f"panel e: a value outside its axis {lim3}: {out_e[:3]}")
        # D289: no key (one kind of mark, named by its axis label) and no group heads
        srcs = list(dict.fromkeys((r["source"], r["role"]) for r in E3))
        ys, h3 = e3_layout(srcs)
        top3 = R3 + 6.0
        axes3 = {}
        for a_, (x_, w_, lim_, ticks_) in {"I": (E3_IX, E3_IXW, E3_IXLIM, E3_ITICKS)}.items():
            ax = hs.axes_mm(fig, x_, top3, w_, h3, spines_on=("bottom",))
            ax.set_xlim(*lim_)
            ax.set_ylim(h3, 0)
            ax.set_yticks([])
            ax.tick_params(left=False, pad=1)
            ax.xaxis.set_major_locator(FixedLocator(list(ticks_)))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: hs.fmt_num(v)))
            ax.xaxis.set_minor_locator(NullLocator())
            hs.reference_line(ax, 0.0, dashed=True)           # each axis its own zero line
            axes3[a_] = ax
            P.rb.append({"panel": "e", "kind": "axis label", "axis": a_, "ax": ax, "artist": None,
                         "text": P.text(x_ + w_ / 2, top3 + h3 + 4.5, E3_XLABEL[a_], ha="center", va="top",
                                        linespacing=1.05, why="the axis label")})
        ax = axes3["I"]
        for i, r in enumerate(book["Fig. 3e"]):
            if r["row_kind"] != E3_KIND or r["measure"] != "interaction":
                continue                                 # D289: D_one and D_many stay in the sheet, not drawn
            col_, mk_ = E3_MARK[r["measure"]]
            ax_ = axes3[E3_AXIS[r["measure"]]]
            art = hs.estimate(ax_, ys[r["source"]] + E3_DY[r["measure"]], r["d_pp"], r["ci95_lo_pp"], r["ci95_hi_pp"],
                              marker_=mk_, colour=col_, zorder=6.0 + E3_MEASURES.index(r["measure"]))
            P.rb.append({"panel": "e", "kind": "mark", "i": i, "artist": art["mark"], "interval": art["interval"],
                         "ax": ax_, "axis": E3_AXIS[r["measure"]]})
            # the source's name; S518's reading stays in the workbook only
            P.rb.append({"panel": "e", "kind": "row label", "i": i, "ax": ax, "artist": None,
                         "text": P.text(E3_LAB, top3 + ys[r["source"]], r["source_label"], ha="right",
                                        why="the source's name")})
            t_ = P.num(hs.text_mm(fig, E3_VX, top3 + ys[r["source"]], S457.half_up(r["d_pp"], 1), ha="left",
                                  va="center"), {"sheet": "Fig. 3e", "row": i, "format": "{d_pp:.1f}"})
            P.rb.append({"panel": "e", "kind": "value", "i": i, "ax": ax, "artist": None, "text": t_})

    # ---- f: corpus size (D218 (3): f, at the right) ---------------------------------------------------------------
    X, Y, WE = F_X, R3, 103.0
    LAB, BG, CP, TWE, THE, RP = E_LAB, E_BG, E_CP, E_TW, E_TH, E_RP
    E = book["Fig. 3f"]
    sizes = sorted({r["core_papers"] for r in E if r["row_kind"] == "cell"})
    x0s = [X + LAB + b * (len(sizes) * CP + BG) for b in range(3)]
    hs.panel_letter(fig, X, Y + 2.4, "f")
    bx = X + 5.0
    hs.vector_colourbar(fig, Y + 0.3, 26.0, -E_SCALE, E_SCALE, [-20, -10, 0, 10, 20], ["−20", "−10", "0", "+10", "+20"],
                        None, x_left=bx, h=2.2)
    hs.text_mm(fig, bx + 28.5, Y + 2.4, "Strategy minus single pass", ha="left")
    P.text(X + LAB - 1.0, Y + 14.0, "Core papers", ha="right", va="baseline")
    blocks_e = E_BLOCKS
    for b, head in enumerate(blocks_e):
        P.rb.append({"panel": "f", "kind": "block head", "block": b, "artist": None,
                     "text": P.text(x0s[b] + 2 * CP - 0.2, Y + 10.6, E_HEADS[b], ha="center", va="baseline", why="the block's name")})
        for k, sz in enumerate(sizes):
            t_ = P.num(hs.text_mm(fig, x0s[b] + k * CP + TWE / 2, Y + 14.0, str(sz), ha="center"),
                       {"fixed": str(sz), "why": "a core-paper size"})
            P.rb.append({"panel": "f", "kind": "size head", "block": b, "k": k, "size": sz, "text": t_, "artist": None})
    top_e = Y + 14.8
    n_rows = len(E_ROWS)
    h_e = (n_rows - 1) * RP + THE                      # FIG3F O2 (rulings page 6 Nov): no run-to-run row under the rows
    ax = hs.axes_mm(fig, X, top_e, WE, h_e, spines_on=())
    ax.set_xlim(0, WE)
    ax.set_ylim(h_e, 0)
    ax.set_xticks([])
    ax.set_yticks([])
    idx = {(r["block"], r["core_papers"], r["strategy"], r["question_group"]): i for i, r in enumerate(E)
           if r["row_kind"] == "cell"}
    for ri, rk in enumerate(E_ROWS):
        yy = ri * RP
        lb_ = P.text(X + LAB - 1.0, top_e + yy + THE / 2, LABEL_E[rk], ha="right", why="the row's name")
        P.rb.append({"panel": "f", "kind": "row label", "rk": rk, "text": lb_, "ax": ax, "artist": None})
        for b, block in enumerate(blocks_e):
            if rk[1] != "all" and b:
                continue                                 # D200: the split rows are in the first block only
            for k, sz in enumerate(sizes):
                i = idx[(block, sz, rk[0], rk[1])]
                r = E[i]
                xx = x0s[b] - X + k * CP
                if r["d_pp"] is None:
                    P.rb.append({"panel": "f", "kind": "no value", "i": i, "ax": ax, "artist": None})
                    continue
                c = hs.cividis_value(r["d_pp"], -E_SCALE, E_SCALE)
                cell = Rectangle((xx, yy), TWE, THE, fc=c, ec="none", lw=0)
                ax.add_patch(cell)
                fr = None
                if r["interval_excludes_0"] == "yes":
                    fr = Rectangle((xx + 0.25, yy + 0.25), TWE - 0.5, THE - 0.5, fc="none", ec=hs.BLACK, lw=1.0, zorder=4)
                    ax.add_patch(fr)
                s_ = (r["d_sign"] or "") + S457.half_up(r["d_size_pp"], 0)
                t_ = P.num(hs.text_mm(fig, X + xx + TWE / 2, top_e + yy + THE / 2, s_, ha="center", va="center",
                                      color=hs.ink_on(c)),
                           {"sheet": "Fig. 3f", "row": i, "format": "{d_sign}{d_size_pp:.0f}"})
                P.rb.append({"panel": "f", "kind": "cell", "i": i, "artist": cell, "ax": ax, "frame": fr, "text": t_})
    # FIG3F O2 (rulings page 6 Nov): the grey run-to-run row is dropped; the n row sits under the last strategy row
    nidx = {(r["block"], r["core_papers"]): i for i, r in enumerate(E) if r["row_kind"] == "n"
            and r["question_group"] == "all"}
    y_n = top_e + (n_rows - 1) * RP + THE + 2.3
    P.text(X + LAB - 1.0, y_n, "Questions (n)", ha="right")
    for b, block in enumerate(blocks_e):
        for k, sz in enumerate(sizes):
            xx = x0s[b] - X + k * CP
            j_ = nidx[(block, sz)]
            t_ = P.num(hs.text_mm(fig, X + xx + TWE / 2, y_n, str(E[j_]["n_questions"]), ha="center", va="center"),
                       {"sheet": "Fig. 3f", "row": j_, "format": "{n_questions}"})
            P.rb.append({"panel": "f", "kind": "n", "i": j_, "text": t_, "ax": ax, "artist": None})

    return P.finish(paths, "Figure 3", sd, nd, "fig3")


def draw_s5(book, paths, sd, nd):
    """Supplementary Figure 16 (fig3.md section 6), 183 x PLATE_H_S5 mm: a, 3a's top at score 3, six rows in 3a's question
    order, one margin column with each rate and interval; b, the butterfly at score 3."""
    hs.check_plate_kinds(["comparison"])
    W, H = S457.FIG_W_MM, PLATE_H_S5
    P = Plate(W, H)
    fig = P.fig
    LEV = tile_colours(nd)
    A, B = S5_SHEET["a"], S5_SHEET["b"]
    LAB, GAPG, MW = 23.0, 1.5, 30.0
    xm = 179.0 - MW
    TW_ = xm - 6.0 - LAB
    top = 7.2
    h_a = 6 * A_ROW
    _, ypos, row_a, tile_a = tile_rows("s5", "a")
    blocks = order_blocks(book, A)
    n1, n2 = (len(b) for b in blocks)
    w1, w2 = (TW_ - GAPG) * n1 / (n1 + n2), (TW_ - GAPG) * n2 / (n1 + n2)
    hs.panel_letter(fig, 0, 2.4, "a")
    noa = draw_tiles(P, "a", A, book, LAB, top, (w1, w2), GAPG, h_a, ypos, row_a, tile_a, CONFIGS, 3, "draws_passed", LEV,
                     nd)
    P.key([("swatch", LEV[k], f"{k}" + (f" of {nd}" if k == 0 else "")) for k in range(nd, -1, -1)]
          + ([("swatch", NO_SCORE, "no score")] if noa else []) + [("estimate", None, "rate, 95% interval")],
          centre_x=W / 2, y=2.4, title="Draws passing at score 3:", max_width=W - 20)
    for b, (head, x_h) in enumerate((("One paper", LAB), ("Many papers", LAB + w1 + GAPG))):
        P.rb.append({"panel": "a", "kind": "block head", "block": b, "text": P.text(x_h, 5.3, head), "artist": None})
    for c, y in zip(CONFIGS, ypos):
        lb_ = P.text(LAB - 1.0, top + y + row_a / 2, LABEL_LONG[c], ha="right", why="the row's name")
        P.rb.append({"panel": "a", "kind": "row label", "c": c, "text": lb_, "artist": None})
    srows = {r["strategy"]: r for r in rows_of(book, A, "strategy")}
    lo_, step_, lim = margin_axis([v for r in srows.values() for v in (r["pass_rate_pct"], r["ci95_lo_pct"])])
    margin_column(P, "a", xm, top, MW, h_a, lim, lo_, step_, {c: srows[c] for c in CONFIGS}, ypos, A_ROW, "all",
                  "pass_rate_pct", "ci95_lo_pct", "ci95_hi_pct")
    y_lab = top + h_a + 6.2
    P.text(LAB + TW_ / 2, y_lab, "Question, order as Figure 3a", ha="center", va="baseline", why="the axis label")
    hs.text_mm(fig, xm + MW / 2, y_lab, "Pass rate (%)", ha="center")
    Y, LABB, WB = 41.0, 22.5, 179.0
    hs.panel_letter(fig, 0, Y + 2.4, "b")
    butterfly_key(P, 0, Y + 2.4, WB, nd > 1)
    t_c, _ = draw_butterfly(P, "b", B, book, LABB, Y + 8.0, WB - LABB, 35.2, LABB - 1.0, nd, nd > 1)
    hs.text_mm(fig, LABB + (WB - LABB) / 2, Y + 8.0 + 35.2 + 6.5, "Questions harmed (left) or helped (right)", ha="center")
    P.text(LABB + (WB - LABB) / 2, Y + 8.0 + 35.2 + 10.0, f"at judge score {t_c} or more", ha="center", va="baseline",
           why="the axis label")
    return P.finish(paths, "Supplementary Figure 16", sd, nd, "s5")


def check_drawn(rb, sheets, nd, plate="fig3"):
    """Every mark of the plate against the Source Data workbook as written, from what each artist holds (its data
    coordinates, its geometry, its colour). Returns (problems, summary). plate "fig3" or "s5". Checked:
      tiles (3a, 3b, S5a)  each drawn exactly once, its x its question's column and its y its row's (tile_rows gives the
            rows top to bottom and the artist's own y is held to them), in the colour of its draws passed (refused), or
            the no-score grey when a draw has no score; each row label on its row, each block head over its block;
      margins (3b, S5a; 3a has none since D216)  the dot on its row (the artist's y) at the row's value, its bar on the same
            row at the interval's ends, dashed exactly where a 0 or a 100% has a one-sided bound and then starting at its
            dot, none where the interval has no width; 3a's open ring on its row at the rate at score 3; each 'all' dot
            equals the mean of its tiles; on Figure 3 each column's axis line and its two labels run A_VIEW, the columns
            of one panel share one scale, 3a's heads stand over their columns in the order all, one, many;
      butterfly (3c, S5b)  each bar from 0 to the mean on the strategy's row, each label on its row, the black dots the
            pairing counts as multisets; on S5b also the grey dots the ordered rerun counts and single pass's band from
            its fewest to its most; on 3c no rerun mark at all;
      3d    each scatter under its strategy's name; each grey dot within the jitter of its question's row, in the sheet's
            order; per strategy and question group (D216) one filled mark at score 4 and one open at 3, in the group's
            shape and colour, at the row's calls and rates, the calls the mean of the group's questions', the rates
            sheet Fig. 3a's, All the strategy's plotted point; no mean mark or interval of the old 3d; the key one line,
            each group's n from its rows; the cross at G2's row, with no bar;
      3a's clock margin (D218)  per row one grey dot set, its x the sheet's per-question values in order and its y
            within T_JIT_Y of the row; the black mean at the row's mean, itself the mean of those values; the printed
            value the row's mean in whole seconds, on the row; a log axis with ticks 30, 100, 300 and no minor labels;
      3e    (D218 (3), the T2 panel; D289) each I row of sheet Fig. 3e drawn once and no D_one or D_many row: its mark
            at its value on its source's row (e3_layout's order), in I's shape and colour, on I's axes and x range, its
            interval from the row's ends at the same height and colour; per source its name and its value (one
            decimal) on its row; S518's reading of I nowhere on the plate (4 November); the axis label E3_XLABEL's;
            no group head and no key;
      3f    (3e before D218) each cell at the column of its block and size and the row of its strategy and group, read from the artist;
            its colour from its d_pp on the fixed scale, its frame exactly where the interval excludes 0, its text in the
            cell and the sign and size printed from the row; each label, block head, size head and n on its row or
            column; each grey cell's text its median, none when it has no value."""
    from matplotlib.colors import to_hex
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle as Rect
    probs, n = [], Counter()

    def close(a, b):
        return a is not None and b is not None and abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))

    def rows(sh, kind):
        return [r for r in sheets.get(sh, []) if r.get("row_kind") == kind]

    def marks(panel, kind):
        return [e for e in rb if e["panel"] == panel and e["kind"] == kind]

    def at_mm(t):                                       # a text's anchor on the page, from the artist
        W_, H_ = t.figure._hs_mm
        x_, y_ = t.get_position()
        return x_ * W_, (1 - y_) * H_

    def ax_mm(ax):                                      # an axes' left and top on the page
        W_, H_ = ax.figure._hs_mm
        p_ = ax.get_position()
        return p_.x0 * W_, (1 - p_.y1) * H_

    for e in rb:                                        # each mark in its own axes, placed by that axes' data transform
        a = e["artist"]
        if a is None:
            continue
        tr = a.get_data_transform() if isinstance(a, Rect) else a.get_transform()
        if a.axes is not e["ax"] or tr != e["ax"].transData:
            probs.append(f"{e['panel']} {e['kind']}: not drawn by its axes' data transform")
        if isinstance(a, Line2D) and a.get_marker() not in (None, "None", ""):
            (x0, x1), (y0, y1) = sorted(e["ax"].get_xlim()), sorted(e["ax"].get_ylim())
            if any(not (x0 <= x <= x1 and y0 <= y <= y1) for x, y in zip(a.get_xdata(), a.get_ydata())):
                probs.append(f"{e['panel']} {e['kind']}: a dot outside its axes (clipped)")
        if e["kind"] == "margin bar":
            x0, x1 = sorted(e["ax"].get_xlim())
            if any(not x0 <= x <= x1 for x in a.get_xdata()):
                probs.append(f"{e['panel']} {e['kind']} {e['c']}: an interval end outside its axes")
    lev = tile_colours(nd)
    A, B = ("Fig. 3a", "Fig. 3b") if plate == "fig3" else (S5_SHEET["a"], None)
    # ---- tiles and margins
    specs = ([("a", A, "draws_passed", 4), ("b", B, "draws_refused", REFUSAL_T)] if plate == "fig3"
             else [("a", A, "draws_passed", 3)])
    for pan, sh, val, th in specs:
        bad = []
        arms_t, ys_t, row_t, tile_t = tile_rows(plate, pan)
        top_of = dict(zip(arms_t, ys_t))
        want = {(r["threshold"], r["strategy"], r["question_id"]): r for r in rows(sh, TILE_KIND)}
        ords = rows(sh, ORDER_KIND)
        if sorted(r["plot_position"] for r in ords) != list(range(1, len(ords) + 1)) \
                or len({r["question_id"] for r in ords}) != len(ords):
            bad.append("the question order is not one position per question")
        blocks = order_blocks(sheets, sh)
        got = Counter()
        for e in marks(pan, "tile"):
            p = e["artist"]
            x = p.get_x()
            col = round(x)
            ids = blocks[e["block"]]
            if abs(x - col) > 1e-9 or not 0 <= col < len(ids) or ids[col] != e["q"] or abs(p.get_width() - 1) > 1e-9 \
                    or e["c"] not in top_of or abs(p.get_y() - (top_of[e["c"]] + (row_t - tile_t) / 2)) > 1e-9 \
                    or abs(p.get_height() - tile_t) > 1e-9:
                bad.append(f"tile {e['c']} {e['q']} off the grid at ({x}, {p.get_y()})")
                continue
            r = want.get((e["t"], e["c"], e["q"]))
            if r is None:
                bad.append(f"tile {e['t']} {e['c']} {e['q']}: no row")
                continue
            exp = lev[r[val]] if r["draws_scored"] == nd else NO_SCORE
            if to_hex(p.get_facecolor()).upper() != exp.upper():
                bad.append(f"tile {e['t']} {e['c']} {e['q']}: {to_hex(p.get_facecolor())}, its {val} {r[val]} of "
                           f"{r['draws_scored']} gives {exp}")
            got[(e["t"], e["c"], e["q"])] += 1
        wrong = [k for k in want if k[0] == th and got[k] != 1] + [k for k in got if k not in want]
        if wrong:
            bad.append(f"{len(wrong)} tiles not drawn exactly once, e.g. {wrong[:2]}")
        n[f"{pan} tiles"] = sum(got.values())
        ax_b = {e["block"]: e["ax"] for e in marks(pan, "tile")}
        lefts = [ax_mm(ax_b[b])[0] for b in sorted(ax_b)]
        if lefts != sorted(lefts):
            bad.append(f"the tile blocks stand out of order: {lefts}")
        top_mm = ax_mm(ax_b[0])[1] if ax_b else 0.0
        heads = marks(pan, "block head")
        kind_of = {r["question_id"]: r.get("question_type") for r in ords}
        if len(blocks) > 1 and len(heads) != len(blocks):
            bad.append(f"{len(heads)} block heads for {len(blocks)} blocks")
        for e in heads:
            b = e["block"]
            head = {"one": "One paper", "many": "Many papers"}.get(kind_of.get(blocks[b][0]))
            if e["text"].get_text() != head or abs(at_mm(e["text"])[0] - ax_mm(ax_b[b])[0]) > 1e-6:
                bad.append(f"block {b}: head {e['text'].get_text()!r} at {at_mm(e['text'])[0]}, its questions are {head!r}")
        lbs = marks(pan, "row label")
        if sorted(e["c"] for e in lbs) != sorted(arms_t):
            bad.append(f"row labels {sorted(e['c'] for e in lbs)}, rows {sorted(arms_t)}")
        names = {**LABEL, **{c: lb for c, _, lb in EXTRA}}
        for e in lbs:
            if e["c"] in top_of and (names[e["c"]] not in e["text"].get_text()
                                     or abs(at_mm(e["text"])[1] - (top_mm + top_of[e["c"]] + row_t / 2)) > 1e-6):
                bad.append(f"row label {e['text'].get_text()!r} is not on {e['c']}'s row")
        n[f"{pan} row labels"] = len(lbs)
        if pan == "b":
            sel = {"all": ({r["strategy"]: r for r in rows(sh, "refusal")}, "refused_pct", "bar_drawn_from_pct",
                           "bar_drawn_to_pct")}
        elif plate == "s5":
            sel = {"all": ({r["strategy"]: r for r in rows(sh, "strategy")}, "pass_rate_pct", "ci95_lo_pct", "ci95_hi_pct")}
        else:                                           # D216: 3a draws no margin; any margin mark there is wrong
            sel = {}
            if [e for e in rb if e["panel"] == "a" and e["kind"].startswith("margin")]:
                bad.append("3a draws margin marks; since D216 its rates are drawn in 3d only")
        for g, (srows, vkey, lokey, hikey) in sel.items():
            seen, bars = Counter(), Counter()
            for e in (x for x in marks(pan, "margin dot") if x["col"] == g):
                a_ = e["artist"]
                r = srows.get(e["c"])
                if r is None or not close(a_.get_xdata()[0], r[vkey]):
                    bad.append(f"margin {g} {e['c']}: dot at {a_.get_xdata()[0]}, the row gives {r and r[vkey]}")
                    continue
                if e["c"] not in top_of or not close(a_.get_ydata()[0], top_of[e["c"]] + row_t / 2):
                    bad.append(f"margin {g} {e['c']}: dot at y {a_.get_ydata()[0]}, not on its row")
                    continue
                seen[e["c"]] += 1
                if g == "all":
                    ts = [w for k, w in want.items() if k[0] == th and k[1] == e["c"] and w["draws_scored"]]
                    if ts and not close(a_.get_xdata()[0], 100 * sum(w[val] / w["draws_scored"] for w in ts) / len(ts)):
                        bad.append(f"margin dot {e['c']}: {a_.get_xdata()[0]}, the mean of its tiles "
                                   f"{100 * sum(w[val] / w['draws_scored'] for w in ts) / len(ts)}")
            for e in (x for x in marks(pan, "margin bar") if x["col"] == g):
                xs = sorted(e["artist"].get_xdata())
                r = srows.get(e["c"])
                if r is None or not (close(xs[0], r[lokey]) and close(xs[1], r[hikey])):
                    bad.append(f"margin bar {g} {e['c']}: {xs}, the row gives {None if r is None else (r[lokey], r[hikey])}")
                    continue
                if e["c"] not in top_of or not all(close(v, top_of[e["c"]] + row_t / 2) for v in e["artist"].get_ydata()):
                    bad.append(f"margin bar {g} {e['c']}: not on its row")
                    continue
                if e["dashed"] != one_sided(r) or (e["artist"].get_linestyle() not in ("-", "solid")) != e["dashed"]:
                    bad.append(f"margin bar {e['c']}: dashed where no one-sided bound (of a 0 or a 100%), or solid "
                               f"where one")
                elif e["dashed"] and not close(e["artist"].get_xdata()[0], r[vkey]):
                    bad.append(f"margin bar {e['c']}: dashed from {e['artist'].get_xdata()[0]}, not from its dot at "
                               f"{r[vkey]}")
                bars[e["c"]] += 1
            for c, r in srows.items():
                if seen[c] != 1:
                    bad.append(f"margin {g} {c}: {seen[c]} dots")
                if bars[c] != (1 if r[hikey] > r[lokey] else 0):
                    bad.append(f"margin {g} {c}: {bars[c]} bars for the interval {r[lokey]} to {r[hikey]}")
            n[f"{pan} margin marks"] += sum(seen.values()) + sum(bars.values())
        if plate == "fig3" and pan == "b":              # 3b's margin axis: A_VIEW's two ends
            axs = list({id(e["ax"]): e["ax"] for e in marks(pan, "margin dot")}.values())
            for ax_ in axs:
                tk, tl = list(ax_.get_xticks()), [t.get_text() for t in ax_.get_xticklabels()]
                ends = tuple(float(v) for v in ax_.spines["bottom"].get_bounds() or ())
                if ends != A_VIEW or (float(tk[0]), float(tk[-1])) != A_VIEW \
                        or (tl[0], tl[-1]) != tuple(f"{v:g}" for v in A_VIEW) \
                        or any(x not in ("", "75") for x in tl[1:-1]):          # 75 labelled (Valerio, 3 Nov)
                    bad.append(f"a margin axis runs {ends}, ticks {tk}, labels {tl}, not {A_VIEW}")
            if len({round(hs.mm_per_unit(ax_)[0], 9) for ax_ in axs}) != 1:
                bad.append("the margin columns have different scales")
            # D231, D306: one open diamond per person row, at its refused share, PERSON_DY below its row's dot, on the
            # margin's axes; none where the sheet has no person row, and the key only beside diamonds
            prow = {r["strategy"]: r for r in rows(sh, PERSON_KIND)}
            pm = marks(pan, "person mark")
            got_p = Counter(e["c"] for e in pm)
            if sorted(got_p.elements()) != sorted(prow):
                bad.append(f"person marks {sorted(got_p.elements())}, the sheet's person rows {sorted(prow)}")
            for e in pm:
                a_, r = e["artist"], prow.get(e["c"])
                if r is None:
                    continue
                if e["ax"] not in axs or not close(a_.get_xdata()[0], r["person_refused_pct"]) \
                        or not close(a_.get_ydata()[0], top_of[e["c"]] + row_t / 2 + PERSON_DY) \
                        or a_.get_marker() != "D" or to_hex(a_.get_markerfacecolor()).upper() != hs.WHITE \
                        or not close(r["person_refused_pct"], 100 * r["person_refused"] / r["questions"]):
                    bad.append(f"person mark {e['c']}: at ({a_.get_xdata()[0]}, {a_.get_ydata()[0]}), the row gives "
                               f"{r['person_refused']} of {r['questions']} on {e['c']}'s row")
            keys = [e["text"].get_text() for e in marks(pan, "key text")]
            if bool(keys) != bool(prow) or (prow and "person, draw 1" not in keys):
                bad.append(f"3b's key {keys} with {len(prow)} person rows")
            n[f"{pan} person marks"] = len(pm)
        probs += [f"{pan}: {x}" for x in bad]
    # ---- 3a's clock margin (D218)
    if plate == "fig3":
        bad = []
        arms_t, ys_t, row_t, _ = tile_rows("fig3", "a")
        top_of = dict(zip(arms_t, ys_t))
        qrows, mrows = defaultdict(list), {}
        for r in rows(A, MARGIN_Q_KIND):
            qrows[r["strategy"]].append(r)
        for r in rows(A, MARGIN_KIND):
            mrows[r["strategy"]] = r
        axs = {id(e["ax"]): e["ax"] for e in rb if e["panel"] == "a" and e["kind"] in ("clock dots", "clock mean")}
        if len(axs) != 1:
            bad.append(f"the clock marks stand in {len(axs)} axes, not one")
        for ax_ in axs.values():
            tk = [float(v) for v in ax_.get_xticks()]
            tl = [t.get_text() for t in ax_.get_xticklabels()]
            minor = [t.get_text() for t in ax_.get_xticklabels(minor=True) if t.get_text()]
            if ax_.get_xscale() != "log" or tk != [float(v) for v in T_TICKS] or tl != [str(v) for v in T_TICKS] \
                    or minor:
                bad.append(f"the clock axis is {ax_.get_xscale()}, ticks {tk} labelled {tl}, minor labels {minor}")
        for c in arms_t:
            dd = [e for e in rb if e["panel"] == "a" and e["kind"] == "clock dots" and e["c"] == c]
            mm_ = [e for e in rb if e["panel"] == "a" and e["kind"] == "clock mean" and e["c"] == c]
            vv = [e for e in rb if e["panel"] == "a" and e["kind"] == "clock value" and e["c"] == c]
            qs, m = qrows.get(c, []), mrows.get(c)
            if len(dd) != 1 or len(mm_) != 1 or len(vv) != 1 or m is None or not qs:
                bad.append(f"{c}: {len(dd)} dot sets, {len(mm_)} means, {len(vv)} values, {len(qs)} question rows, "
                           f"mean row {m is not None}")
                continue
            yc = top_of[c] + row_t / 2
            xs, ys_ = list(dd[0]["artist"].get_xdata()), list(dd[0]["artist"].get_ydata())
            want = [r["clock_less_wait_s_mean_over_draws"] for r in qs]
            if len(xs) != len(want) or not all(close(x, w) for x, w in zip(xs, want)):
                bad.append(f"{c}: {len(xs)} grey dots, not the sheet's {len(want)} question values in order")
            if any(abs(y - yc) > T_JIT_Y + 1e-9 for y in ys_):
                bad.append(f"{c}: a grey dot beyond the row's jitter")
            if not close(m["clock_less_wait_s_mean"], sum(want) / len(want)) or m["questions"] != len(want):
                bad.append(f"{c}: the mean row {m['clock_less_wait_s_mean']} is not the mean of its {len(want)} "
                           f"questions {sum(want) / len(want)}")
            a_ = mm_[0]["artist"]
            if not (close(a_.get_xdata()[0], m["clock_less_wait_s_mean"]) and close(a_.get_ydata()[0], yc)) \
                    or to_hex(a_.get_markerfacecolor()).upper() != hs.BLACK.upper():
                bad.append(f"{c}: the black mean at ({a_.get_xdata()[0]}, {a_.get_ydata()[0]}), the row gives "
                           f"({m['clock_less_wait_s_mean']}, {yc})")
            t_ = vv[0]["text"]
            wtxt = S457.half_up(m["clock_less_wait_s_mean"], 0) + " s"
            if t_.get_text() != wtxt or m["printed"] != wtxt \
                    or abs(at_mm(t_)[1] - (ax_mm(a_.axes)[1] + yc)) > 1e-6:
                bad.append(f"{c}: prints {t_.get_text()!r}, the row gives {wtxt!r}, or not on its row")
            n["a clock dots"] += len(xs)
            n["a clock means"] += 1
        extra_c = set(qrows) - set(arms_t)
        if extra_c:
            bad.append(f"clock rows for {sorted(extra_c)}, not on 3a")
        probs += [f"a clock: {x}" for x in bad]
    # ---- the butterfly
    pan, sh = ("c", "Fig. 3c") if plate == "fig3" else ("b", S5_SHEET["b"])
    bad = []
    E = sheets.get(sh, [])
    fl = {r["strategy"]: r for r in E if r.get("row_kind") == FLIP_KIND}
    nb = {r["strategy"]: r for r in E if r.get("row_kind") == NOISE_KIND}
    pr = defaultdict(list)
    for r in E:
        if r.get("row_kind") == PAIR_KIND:
            pr[r["strategy"]].append(r)
    reruns = plate == "s5" and nd > 1                   # 3c draws no rerun mark (Valerio's plate note, 2 November)
    rows_e = (["single_pass"] if reruns else []) + FLIPPED
    bars_ = marks(pan, "bar")
    pitch = abs(bars_[0]["ax"].get_ylim()[0] - bars_[0]["ax"].get_ylim()[1]) / len(rows_e) if bars_ else 1.0
    top_b = ax_mm(bars_[0]["ax"])[1] if bars_ else 0.0
    lbs = marks(pan, "row label")
    if [e["c"] for e in lbs] != rows_e:
        bad.append(f"row labels {[e['c'] for e in lbs]}, rows {rows_e}")
    for e in lbs:
        i_ = (at_mm(e["text"])[1] - top_b) / pitch
        if not 0 <= i_ < len(rows_e) or rows_e[math.floor(i_)] != e["c"] \
                or (e["c"] != "single_pass" and e["text"].get_text() != LABEL[e["c"]]):
            bad.append(f"row label {e['text'].get_text()!r} is not on {e['c']}'s row")

    def ordered(c):
        return sorted(v for k_, v in nb[c].items() if k_.startswith("pass_on_") and v is not None)
    for c in FLIPPED:
        r = fl.get(c)
        for sgn, k_ in ((-1, "harmed"), (1, "helped")):
            bs = [e for e in marks(pan, "bar") if e["c"] == c and e["side"] == sgn]
            if r is None or len(bs) != 1:
                bad.append(f"{c} {k_}: {len(bs)} bars")
                continue
            p = bs[0]["artist"]
            yc = p.get_y() + p.get_height() / 2
            row = rows_e[math.floor(yc / pitch)] if 0 <= yc < pitch * len(rows_e) else None
            end = p.get_x() if sgn < 0 else p.get_x() + p.get_width()
            start = p.get_x() + p.get_width() if sgn < 0 else p.get_x()
            if row != c or not close(start, 0) or not close(sgn * end, r[f"{k_}_mean_over_pairings"]):
                bad.append(f"{c} {k_}: bar on row {row} to {end}, the row gives {r[f'{k_}_mean_over_pairings']}")
            dts = [e for e in marks(pan, "pairing dots") if e["c"] == c and e["side"] == sgn]
            want = sorted(x[k_] for x in pr[c])
            gotv = sorted(sgn * x for x in dts[0]["artist"].get_xdata()) if len(dts) == 1 else None
            if gotv is None or len(gotv) != len(want) or not all(close(g, w) for g, w in zip(gotv, want)):
                bad.append(f"{c} {k_}: pairing dots {gotv}, the sheet {want}")
            n[f"{pan} bars"] += 1
            n[f"{pan} pairing dots"] += len(want)
    for c in rows_e if reruns else []:
        for sgn in (-1, 1):
            dts = [e for e in marks(pan, "rerun dots") if e["c"] == c and e["side"] == sgn]
            want = ordered(c)
            gotv = sorted(sgn * x for x in dts[0]["artist"].get_xdata()) if len(dts) == 1 else None
            if gotv is None or gotv != [float(w) for w in want]:
                bad.append(f"{c} rerun dots {gotv}, the sheet {want}")
            n[f"{pan} rerun dots"] += len(want)
    if reruns:
        b0, b1 = nb["single_pass"]["ordered_pairs_min"], nb["single_pass"]["ordered_pairs_max"]
        for sgn in (-1, 1):
            bs = [e for e in marks(pan, "band") if e["side"] == sgn]
            if len(bs) != 1:
                bad.append(f"band {sgn}: {len(bs)} drawn")
                continue
            a_ = bs[0]["artist"]
            xs = sorted((a_.get_x(), a_.get_x() + a_.get_width())) if isinstance(a_, Rect) else sorted(a_.get_xdata())
            if not (close(xs[0], min(sgn * b0, sgn * b1)) and close(xs[1], max(sgn * b0, sgn * b1))):
                bad.append(f"band {sgn}: {xs}, the sheet {b0} to {b1}")
            n[f"{pan} band"] += 1
    elif marks(pan, "band") or marks(pan, "rerun dots"):
        bad.append("rerun marks on a butterfly that has none")
    probs += [f"{pan}: {x}" for x in bad]
    if plate == "s5":
        return probs, (", ".join(f"{v:,} {k}" for k, v in n.items())
                       + " read back from the plate's artists and equal to the workbook")
    # ---- d
    bad = []
    D = "Fig. 3d"
    pts = {r["strategy"]: r for r in rows(D, "strategy (plotted)")}
    gr = {(r["strategy"], r["question_group"]): r for r in rows(D, GROUP_D_KIND)}
    cq = defaultdict(list)
    for r in rows(D, CQ_KIND):
        cq[r["strategy"]].append(r)
    for c in CONFIGS:
        p, qs = pts.get(c), [r for r in cq[c] if r["pass_share_t4_pct"] is not None]
        dd = [e for e in marks("d", "dots") if e["c"] == c]
        if p is None or len(dd) != 1:
            bad.append(f"{c}: strategy row {p is not None}, dot sets {len(dd)}")
            continue
        nm = [e for e in marks("d", "name") if e["c"] == c]
        if len(nm) != 1 or nm[0]["ax"] is not dd[0]["ax"] or nm[0]["text"].get_text() != LABEL[c]:
            bad.append(f"{c}: the scatter is not under its strategy's name: {[e['text'].get_text() for e in nm]}")
        xs, ys_ = list(dd[0]["artist"].get_xdata()), list(dd[0]["artist"].get_ydata())
        if len(xs) != len(qs):
            bad.append(f"{c}: {len(xs)} dots for {len(qs)} questions with a share")
        else:
            beyond = [r["question_id"] for x, y, r in zip(xs, ys_, qs)
                      if abs(math.log(x / r["calls_per_answer_question_mean"])) > C_JIT_X + 1e-9
                      or abs(y - r["pass_share_t4_pct"]) > C_JIT_Y + 1e-9]
            if beyond:
                bad.append(f"{c}: {len(beyond)} dots beyond the jitter of their question, e.g. {beyond[:2]}")
        n["d dots"] += len(xs)
        allq = cq[c]
        if allq and not close(p["calls_mean"], sum(r["calls_per_answer_question_mean"] for r in allq) / len(allq)):
            bad.append(f"{c}: calls mean {p['calls_mean']} is not the mean of its questions' calls")
        # D216: the three group marks, each at its row; the row's calls the mean of its questions', its rates sheet
        # Fig. 3a's; group all the strategy's plotted point
        for g, head, col_, mk_ in D_GROUPS:
            r = gr.get((c, g))
            qg = [x for x in allq if g == "all" or x.get("question_type") == g]
            if r is None:
                bad.append(f"{c} {g}: no row '{GROUP_D_KIND}'")
                continue
            if r["questions"] != len(qg) or not qg or not close(
                    r["calls_mean"], sum(x["calls_per_answer_question_mean"] for x in qg) / len(qg)):
                bad.append(f"{c} {g}: {r['questions']} questions, calls {r['calls_mean']}; its {len(qg)} questions' "
                           f"calls give another mean")
            for t, k3a, kd in ((PRIMARY, "pass_rate_pct", "pass_rate_t4_pct"), (THRESHOLDS[1], "pass_rate_pct",
                                                                               "pass_rate_t3_pct")):
                ra = group_rows(sheets, "Fig. 3a", t, g).get(c)
                if ra is None or not close(r[kd], ra[k3a]) or ra["questions_in_group"] != r["questions"]:
                    bad.append(f"{c} {g}: the rate at score {t} {r[kd]} is not sheet Fig. 3a's "
                               f"{None if ra is None else ra[k3a]}")
            if g == "all" and not (close(r["calls_mean"], p["calls_mean"])
                                   and close(r["pass_rate_t4_pct"], p["pass_rate_t4_pct"])):
                bad.append(f"{c}: All at ({r['calls_mean']}, {r['pass_rate_t4_pct']}), the strategy row at "
                           f"({p['calls_mean']}, {p['pass_rate_t4_pct']})")
            for t, kd in ((PRIMARY, "pass_rate_t4_pct"), (THRESHOLDS[1], "pass_rate_t3_pct")):
                ms_ = [e for e in marks("d", "group mark") if e["c"] == c and e["g"] == g and e["t"] == t]
                if len(ms_) != 1:
                    bad.append(f"{c} {g} score {t}: {len(ms_)} marks")
                    continue
                a_ = ms_[0]["artist"]
                if ms_[0]["ax"] is not dd[0]["ax"] or not (close(a_.get_xdata()[0], r["calls_mean"])
                                                          and close(a_.get_ydata()[0], r[kd])):
                    bad.append(f"{c} {g} score {t}: the mark at ({a_.get_xdata()[0]}, {a_.get_ydata()[0]}), the row "
                               f"gives ({r['calls_mean']}, {r[kd]})")
                face, edge = (col_, hs.WHITE) if t == PRIMARY else (hs.WHITE, col_)
                if a_.get_marker() != mk_ or to_hex(a_.get_markerfacecolor()).upper() != face.upper() \
                        or to_hex(a_.get_markeredgecolor()).upper() != edge.upper():
                    bad.append(f"{c} {g} score {t}: drawn as {a_.get_marker()} {to_hex(a_.get_markerfacecolor())} on "
                               f"{to_hex(a_.get_markeredgecolor())}, not {mk_} {face} on {edge}")
                n["d group marks"] += 1
    if [e for e in rb if e["panel"] == "d" and e["kind"] in ("mean", "calls bar", "pass bar", "cross bar")]:
        bad.append("an interval or a mean mark of the old 3d is drawn (D216: no interval on any mark)")
    want_k = [f"{h} {gr[(CONFIGS[0], g)]['questions']}" for g, h, *_ in (D_GROUPS[2], D_GROUPS[0], D_GROUPS[1])
              if (CONFIGS[0], g) in gr] + [f"score {THRESHOLDS[1]}", fn.MATCHED_BUDGET]
    kt = [e["text"] for e in marks("d", "key text")]
    if [t.get_text() for t in kt] != want_k or len({round(at_mm(t)[1], 6) for t in kt}) != 1:
        bad.append(f"the key reads {[t.get_text() for t in kt]} on {len({round(at_mm(t)[1], 6) for t in kt})} "
                   f"lines, not {want_k} on one")
    x_ = rows(D, CROSS_KIND)
    cr = marks("d", "cross")
    if len(x_) != 1 or len(cr) != 1:
        bad.append(f"the matched-budget cross: {len(x_)} rows, {len(cr)} crosses")
    else:
        r = x_[0]
        if not (close(cr[0]["artist"].get_xdata()[0], r["calls_mean"])
                and close(cr[0]["artist"].get_ydata()[0], r["pass_rate_t4_pct"])):
            bad.append(f"the cross is not at ({r['calls_mean']}, {r['pass_rate_t4_pct']})")
        n["d cross"] += 1
    probs += [f"d: {x}" for x in bad]
    # ---- e (D218 (3): the T2 panel): S518's verdicts, one mark and interval per source and measure
    bad = []
    E3s = sheets.get("Fig. 3e", [])
    e3 = {i: r for i, r in enumerate(E3s) if r.get("row_kind") == E3_KIND}
    if e3:
        ys3, _ = e3_layout(list(dict.fromkeys((r["source"], r["role"]) for r in e3.values())))
        want_v = {i for i, r in e3.items() if r["measure"] == "interaction"}
        got = Counter(e["i"] for e in marks("e", "mark"))
        if set(got) != want_v or set(got.values()) != {1}:
            bad.append(f"{sum(got.values())} marks for {len(want_v)} I rows of sheet Fig. 3e, each to be drawn once "
                       f"(D289: D_one and D_many are not drawn)")
        for e in marks("e", "mark"):
            r = e3.get(e["i"])
            if r is None:
                continue
            a_, iv = e["artist"], e["interval"]
            y_ = ys3[r["source"]] + E3_DY[r["measure"]]
            col_, mk_ = E3_MARK[r["measure"]]
            if not (close(a_.get_xdata()[0], r["d_pp"]) and close(a_.get_ydata()[0], y_)):
                bad.append(f"{r['source']} {r['measure']}: the mark at ({a_.get_xdata()[0]}, {a_.get_ydata()[0]}), the "
                           f"row gives ({r['d_pp']}, {y_})")
            if e.get("axis") != E3_AXIS[r["measure"]] or tuple(e["ax"].get_xlim()) != {"D": E3_XLIM, "I": E3_IXLIM}[
                    E3_AXIS[r["measure"]]]:
                bad.append(f"{r['source']} {r['measure']}: drawn on axes {e.get('axis')!r} {tuple(e['ax'].get_xlim())}, "
                           f"not on {E3_AXIS[r['measure']]!r}, the axis whose x is what the measure computes")
            if a_.get_marker() != mk_ or to_hex(a_.get_markerfacecolor()).upper() != col_.upper():
                bad.append(f"{r['source']} {r['measure']}: drawn as {a_.get_marker()} {to_hex(a_.get_markerfacecolor())}, "
                           f"not {mk_} {col_}")
            ix, iy = list(iv.get_xdata()), list(iv.get_ydata())
            if not (len(ix) == 2 and close(min(ix), r["ci95_lo_pp"]) and close(max(ix), r["ci95_hi_pp"])
                    and all(close(v, y_) for v in iy)) or to_hex(iv.get_color()).upper() != col_.upper():
                bad.append(f"{r['source']} {r['measure']}: the interval {ix} at {iy}, the row gives "
                           f"({r['ci95_lo_pp']}, {r['ci95_hi_pp']}) at {y_}")
            n["e marks"] += 1
        # Valerio, 4 November: S518's reading of I stays in the workbook and is not drawn
        readings = {r["reading"] for r in e3.values() if r.get("reading")}
        figs3 = {id(e["ax"].figure): e["ax"].figure for e in marks("e", "mark")}
        drawn_r = [t.get_text() for f_ in figs3.values() for t in f_.texts if t.get_text() in readings]
        if marks("e", "verdict") or drawn_r:
            bad.append(f"S518's reading drawn on the plate ({drawn_r[:2] or 'a verdict mark'}); it stays in the workbook")
        ax_l = sorted((e["axis"], e["text"].get_text()) for e in marks("e", "axis label"))
        if ax_l != sorted(E3_XLABEL.items()):
            bad.append(f"the axis labels read {ax_l}, not {sorted(E3_XLABEL.items())}")
        for e in marks("e", "row label"):
            r = e3[e["i"]]
            if e["text"].get_text() != r["source_label"] or abs(at_mm(e["text"])[1] - (ax_mm(e["ax"])[1]
                                                                                       + ys3[r["source"]])) > 1e-6:
                bad.append(f"the row label {e['text'].get_text()!r} is not {r['source']}'s row")
        if len(marks("e", "row label")) != len(want_v):
            bad.append(f"{len(marks('e', 'row label'))} row labels for {len(want_v)} sources")
        vals = marks("e", "value")
        for e in vals:
            r = e3[e["i"]]
            if e["text"].get_text() != S457.half_up(r["d_pp"], 1) or abs(at_mm(e["text"])[1] - (
                    ax_mm(e["ax"])[1] + ys3[r["source"]])) > 1e-6:
                bad.append(f"the value {e['text'].get_text()!r} is not {r['source']}'s I on its row")
        if sorted(e["i"] for e in vals) != sorted(want_v):
            bad.append(f"{len(vals)} printed values for {len(want_v)} sources")
        # D289: no group heads and no key on 3e
        gone = set(E3_ROLE_HEAD.values())                # "One paper" and "Many papers" stay as 3a's and 3d's heads
        drawn_g = [t.get_text() for f_ in figs3.values() for t in f_.texts if t.get_text() in gone]
        if marks("e", "role head") or marks("e", "key text") or drawn_g:
            bad.append(f"a group head or key drawn on 3e ({drawn_g[:2]}); D289 removed them")
    elif marks("e", "mark"):
        bad.append("marks drawn with no S518 row in sheet Fig. 3e")
    probs += [f"e: {x}" for x in bad]
    # ---- f (D218 (3): corpus size, 3e before), at F_X
    bad = []
    E = sheets.get("Fig. 3f", [])
    sizes = sorted({r["core_papers"] for r in E if r.get("row_kind") == "cell"})

    def e_x(block, size):                               # the left edge of a block's column, in the panel's mm
        return E_LAB + E_BLOCKS.index(block) * (len(sizes) * E_CP + E_BG) + sizes.index(size) * E_CP

    def in_cell(t, ax, x_, y_):                         # the text stands at the middle of the cell at (x_, y_)
        ax0 = ax_mm(ax)
        tx, ty = at_mm(t)
        return abs(tx - (ax0[0] + x_ + E_TW / 2)) <= 1e-6 and abs(ty - (ax0[1] + y_ + E_TH / 2)) <= 1e-6
    for e in marks("f", "cell"):
        r = E[e["i"]]
        ri = E_ROWS.index((r["strategy"], r["question_group"]))
        x_, y_ = e_x(r["block"], r["core_papers"]), ri * E_RP
        a_ = e["artist"]
        if abs(a_.get_x() - x_) > 1e-9 or abs(a_.get_y() - y_) > 1e-9 or abs(a_.get_width() - E_TW) > 1e-9 \
                or abs(a_.get_height() - E_TH) > 1e-9:
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']} {r['question_group']}: at "
                       f"({a_.get_x()}, {a_.get_y()}), its column and row are at ({x_}, {y_})")
        if e["frame"] is not None and (abs(e["frame"].get_x() - x_ - 0.25) > 1e-9 or abs(e["frame"].get_y() - y_ - 0.25) > 1e-9):
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']}: the frame is not on its cell")
        if not in_cell(e["text"], e["ax"], x_, y_):
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']}: its number is not in its cell")
        c = hs.cividis_value(r["d_pp"], -E_SCALE, E_SCALE).upper()
        if to_hex(e["artist"].get_facecolor()).upper() != c:
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']} {r['question_group']}: "
                       f"{to_hex(e['artist'].get_facecolor())}, its d_pp {r['d_pp']} gives {c}")
        if (e["frame"] is not None) != (r["interval_excludes_0"] == "yes"):
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']}: frame {e['frame'] is not None}, "
                       f"interval_excludes_0 {r['interval_excludes_0']}")
        want = (r.get("d_sign") or "") + S457.half_up(r["d_size_pp"], 0)
        if e["text"].get_text() != want:
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']}: text {e['text'].get_text()!r}, the row "
                       f"gives {want!r}")
        if (r["d_size_pp"] is None) or abs(abs(r["d_pp"]) - r["d_size_pp"]) > 1e-9:
            bad.append(f"cell {r['block']} {r['core_papers']} {r['strategy']}: d_size_pp is not |d_pp|")
        n["f cells"] += 1
    drawn = {e["i"] for e in marks("f", "cell")} | {e["i"] for e in marks("f", "no value")}
    want_i = {i for i, r in enumerate(E) if r.get("row_kind") == "cell"
              and (r["question_group"] == "all" or r["block"] == "All in scope")}
    if drawn != want_i or len(drawn) != len(marks("f", "cell")) + len(marks("f", "no value")):
        bad.append(f"{len(drawn)} cells drawn, the sheet holds {len(want_i)}")
    lbs = marks("f", "row label")
    if sorted(str(e["rk"]) for e in lbs) != sorted(str(k) for k in E_ROWS):
        bad.append(f"{len(lbs)} row labels for {len(E_ROWS)} rows")
    for e in lbs:
        s_, g_ = e["rk"]
        want_l = LABEL[s_] if g_ == "all" else {"one": "RLM-10, one paper", "many": "RLM-10, many papers"}[g_]
        if e["text"].get_text() != want_l or abs(at_mm(e["text"])[1] - (ax_mm(e["ax"])[1] + E_ROWS.index(e["rk"]) * E_RP
                                                                         + E_TH / 2)) > 1e-6:
            bad.append(f"row label {e['text'].get_text()!r} is not the row {e['rk']}")
    grid = {round(F_X + e_x(bk, sz) + E_TW / 2, 6): (bk, sz) for bk in E_BLOCKS for sz in sizes}
    got_h = Counter()
    for e in marks("f", "size head"):
        k_ = grid.get(round(at_mm(e["text"])[0], 6))
        got_h[k_] += 1
        if k_ is None or e["text"].get_text() != str(k_[1]):
            bad.append(f"the size head {e['text'].get_text()!r} is not over its column")
    if sorted(got_h.values()) != [1] * len(grid) or None in got_h:
        bad.append(f"{sum(got_h.values())} size heads for {len(grid)} columns")
    for e in marks("f", "block head"):
        if e["text"].get_text() != E_HEADS[e["block"]] or abs(at_mm(e["text"])[0] - (
                F_X + E_LAB + e["block"] * (len(sizes) * E_CP + E_BG) + 2 * E_CP - 0.2)) > 1e-6:
            bad.append(f"the block head {e['text'].get_text()!r} is not over block {e['block']}")
    for e in marks("f", "n"):
        r = E[e["i"]]
        if abs(at_mm(e["text"])[0] - (ax_mm(e["ax"])[0] + e_x(r["block"], r["core_papers"]) + E_TW / 2)) > 1e-6:
            bad.append(f"the n of {r['block']} {r['core_papers']} is not under its column")
    probs += [f"f: {x}" for x in bad]
    return probs, ", ".join(f"{v:,} {k}" for k, v in n.items()) + (" read back from the plate's artists and equal to "
                                                                   "the Source Data workbook")


# ---------------------------------------------------------------------------------------------------------------
# the claims list (D82): every number the main text, the Figure 3 legend, the Supplementary Notes and the letter give
# for panels a to d, re-anchored on the agreed text (D304)
# ---------------------------------------------------------------------------------------------------------------
from doc_paths import LETTER as _LETTER_LIVE, ROOT as _DOC_ROOT, doc as _doc  # noqa: E402  the live documents (4 Nov)
# D304 (8 Nov): the rows are anchored on the agreed text, Claude Docs rev 3688, as the live documents read with every
# mark accepted: 02_Main_Text and 04_Figures_Tables (S605's tracked round), and the Supplementary Notes as S602 wrote
# them from the same export (Supplementary_Information.docx, named Supplementary_Information_20261107.docx until D305 of
# 8 Nov; the older 06_Supplementary_Information.docx, deleted on 8 Nov (D305), held
# the submitted Supplementary Tables 2 and 8, which the agreed Supplementary Information does not carry). The letter
# is read with every mark accepted too; its round will be rebuilt, so the letter's anchors are provisional.
DOCS = {"MT": _doc("02_Main_Text.docx"),
        "FT": _doc("04_Figures_Tables.docx"),
        "SI": _DOC_ROOT / "resubmission/06_supplementary/Supplementary_Information.docx",
        "LT": _LETTER_LIVE}
DOC_NAME = {"MT": "Main Text", "FT": "Figures and Tables (Figure 3 legend)",
            "SI": "Supplementary Information (Supplementary Notes)", "LT": "letter (point-by-point response)"}
SEC_GEN = "Results, 'The better strategy depends on the question'"
SEC_DISC = "Discussion"
SEC_N3 = "Supplementary Note 3, 'The strategy comparison in detail'"
SEC_N6 = "Supplementary Note 6, 'The three evaluation signals in detail'"
LEG = "Figure 3 legend"
# opening words of the agreed paragraphs the rows sit in (rev 3688)
P_POOLED = "No iterative strategy passed more answers than single pass retrieval"
P_SCOPE = "Answering well also means declining what the corpus does not cover"
P_COST = "RLM-10 also cost more"
P_FIG3 = "Figure 3 | Answer strategies against single pass, by the judge's pass rate."
P_N3_POOLED = "Pooled over the answerable questions, no iterative strategy passed more answers"
P_N3_FLIP = "Against single pass retrieval, each strategy turned some correct answers incorrect"
P_N3_REFUSAL = "Strategy choice also governed refusal on out-of-scope questions"
P_LT_R1 = "Iterative retrieval. Pooled over the 86 answerable questions"
P_LT_R1_SELF = "Self-correction. We renamed the strategy passage verification"
P_LT_TABLE = "Every answer record now keeps each model call with its tokens"
P_LT_R4C1 = "Per pairing, passage verification turned a mean of 5.6 correct answers incorrect"
P_LT_R3MP3 = "In the reviewer's example the figure was right and the text wrong"
P_LT_FP = "In the revision each of the six strategies answered the ten false-premise questions"
GONE_T8 = ("Supplementary Table 8 is not in the agreed Supplementary Information, which holds Tables 1 to 3; each "
           "strategy's pass rate is in the letter's Table R4.1 (C41 to C46), RLM-10's in the Results (C02)")
GONE_T2 = ("the agreed Supplementary Table 2 is the generator and judge pairing and has no exp04 row; the agreed text "
           "gives no draw-by-draw RLM-10 against single pass table")
# One row per number or claim. loc: ("text", opening words of the paragraph, the exact words that must be in it) or
# ("cell", opening words of the paragraph before the table, the row's label, the cell's place after the label).
# claimed: the number as printed. m: what S463 gives for it (see claim_value). t: the judge score the row's status is
# read at (3 when absent: the submitted text's threshold; 4, the paper's pass, D154, for every row re-anchored on the
# agreed text). retired: why the agreed text no longer states the claim; the row keeps its submitted words and its
# value is still computed and shown. The rows were first found on 18 October; D304 (8 November) re-anchored every one
# on the agreed text or retired it (findings/audits/claims_after_rev3688.md).
CLAIM_ROWS = [
    dict(id="C01", doc="MT", sec=SEC_GEN, loc=("text", "With the judge and the signals fixed, we compared six generation",
         "we compared six generation strategies on the 135 questions in scope"), claimed="135 questions",
         m=("n", "questions")),
    dict(id="C02", doc="MT", sec=SEC_GEN, loc=("text", P_POOLED, "and RLM-10 74.0% (95% CI: 67.8% to 79.8%)"),
         claimed="74.0", m=("rate", "rlm_10"), t=4),
    dict(id="C03", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "RLM-10 achieved the highest pass rate"), claimed="RLM-10 highest of the six", m=("verdict", "E1a"),
         retired="the agreed text claims no highest strategy; it says no iterative strategy passed more answers than "
                 "single pass (C02)"),
    dict(id="C04", doc="SI", sec=SEC_N3, loc=("text", P_N3_POOLED, "passage verification 83.3% (95% CI: 76.4% to 89.9%)"),
         claimed="83.3", m=("rate", "verified_pass"), t=4),
    dict(id="C05", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "performed worst overall"), claimed="verified pass lowest of the six", m=("verdict", "E1b"),
         retired="the agreed text claims no lowest strategy"),
    dict(id="C06", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "Relative to single-pass retrieval, verification actively degraded valid responses."),
         claimed="verified pass below single pass", m=("verdict", "R11"),
         retired="the agreed text no longer says passage verification passes fewer answers than single pass; it gives "
                 "both rates (C04) and the harmed share (C57)"),
    dict(id="C07", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "RLM-10's pass rate significantly outperformed passage verification (two-sided exact McNemar P < 0.001"),
         claimed="RLM-10 above verified pass, P < 0.001", m=("verdict", "E4"),
         retired="the agreed text makes no RLM-10 against passage verification test"),
    dict(id="C08", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "Cohen's h = 0.65"), claimed="Cohen's h 0.65", m=("none", "Cohen's h is no statistic of a LIST.md rule"),
         retired="the agreed text gives no Cohen's h"),
    dict(id="C09", doc="SI", sec=SEC_N3, loc=("text", P_N3_REFUSAL, "multi-hop retrieval 88.0%"), claimed="88.0",
         m=("refused", "multi_hop")),
    dict(id="C10", doc="MT", sec=SEC_GEN, loc=("text", P_SCOPE, "RLM-10 97.4%"), claimed="97.4",
         m=("refused", "rlm_10")),
    dict(id="C11", doc="MT", sec=SEC_GEN, loc=("text", "Strategy choice also governed performance on unanswerable",
         "Multi-hop retrieval correctly refused 40.0% of the OOD questions, whereas RLM-10 refused 82.0%"),
         claimed="RLM-10 refuses more than multi-hop", m=("verdict", "E6"),
         retired="the agreed text sets no refusal of RLM-10 against multi-hop; it gives each rate (C09, C10)"),
    dict(id="C12", doc="MT", sec=SEC_GEN, loc=("text", "Strategy choice also governed performance on unanswerable",
         "while sustaining its 92.0% pass rate"), claimed="92.0", m=("rate", "rlm_10"),
         retired="the refusal paragraph no longer repeats RLM-10's pass rate (C02 carries it)"),
    dict(id="C13", doc="MT", sec=SEC_GEN, loc=("text", P_SCOPE, "Single pass and passage verification refused every "
         "answer to the 39 out-of-scope questions"), claimed="100.0", m=("refused2", "single_pass", "verified_pass")),
    dict(id="C14", doc="MT", sec=SEC_GEN, loc=("text", "Strategy choice also governed performance on unanswerable",
         "achieved the highest refusal rates"), claimed="verified pass and RLM-20 refuse most",
         m=("refusal_rank",), retired="the agreed text ranks no strategy by refusal; it gives the rates (C10, C13)"),
    dict(id="C15", doc="MT", sec=SEC_GEN, loc=("text", "Strategy choice also governed performance on unanswerable",
         "a 33.0% failure rate on answerable questions"), claimed="33.0", m=("fail_rate", "verified_pass"),
         retired="the agreed text gives no failure rate; it gives the pass rate (C04)"),
    dict(id="C16", doc="MT", sec=SEC_GEN, loc=("text", P_SCOPE, "On the ten false-premise questions, single pass passed "
         "all 30 of its answers and the other strategies 25 to 28"), claimed="single pass 30 of 30, the others 25 to 28",
         m=("fp", ("range", 30, 25, 28)), t=4),
    dict(id="C17", doc="MT", sec=SEC_GEN, loc=("text", "On the ten false-premise questions",
         "Of the 43 responses that engaged, 33 contradicted the premise, eight hedged and none affirmed it"),
         claimed="43 engaged, none affirmed", m=("none", "needs the hand classes; Rule 9: not claimed from judge "
                                                        "scores"),
         retired="the agreed text gives the judge's counts only (C16), no hand classes"),
    dict(id="C18", doc="MT", sec=SEC_DISC, loc=("text", "These results give concrete deployment guidance",
         "(88 answerable questions over 20 core papers)"), claimed="88 answerable questions",
         m=("n", "answerable"), retired="the Discussion no longer gives the question count (C01, C23 carry it)"),
    dict(id="C19", doc="MT", sec=SEC_DISC, loc=("text", "These results give concrete deployment guidance",
         "RLM-10 exceeded single-pass retrieval by 12.5 percentage points"), claimed="12.5",
         m=("diff", "rlm_10", "single_pass"),
         retired="the agreed manuscript gives no RLM-10 minus single pass difference (the letter's is C40)"),
    dict(id="C20", doc="MT", sec=SEC_DISC, loc=("text", "These results give concrete deployment guidance",
         "(two-sided exact McNemar P = 0.019)"), claimed="0.019", m=("p", "rlm_10", "single_pass"),
         retired="the agreed manuscript gives no P for RLM-10 against single pass (the letter's is C40)"),
    dict(id="C21", doc="MT", sec=SEC_DISC, loc=("text", "These results give concrete deployment guidance",
         "RLM-10 exceeded single-pass retrieval by 12.5 percentage points"), claimed="RLM-10 above single pass",
         m=("verdict", "E5"), retired="the agreed text no longer claims RLM-10 above single pass; it gives both "
                                      "rates (C02)"),
    dict(id="C22", doc="MT", sec=SEC_GEN, loc=("text", P_COST, "about six times the model calls"),
         claimed="about six times the model calls", m=("cost_words", "answerable", "calls")),
    dict(id="C23", doc="FT", sec=LEG, loc=("text", P_FIG3, "a, The n = 86 answerable questions (n = 60 one-paper, "
         "n = 26 many-paper) by strategy"), claimed="n = 86 answerable (60 one-paper, 26 many-paper)",
         m=("n", "answerable_split")),
    dict(id="C24", doc="FT", sec=LEG, loc=("text", P_FIG3, "judged by devstral-small-2:24b for judge correctness (pass, "
         "score 4 or more; relaxed, 3 or more)"), claimed="devstral-small-2:24b, n = 3 draws", m=("judge",)),
    dict(id="C25", doc="FT", sec=LEG, loc=("text", P_FIG3, "b, As a for the n = 39 out-of-scope questions"),
         claimed="n = 39", m=("n", "not_answerable")),
    *[dict(id=f"C{26 + i}", doc="SI", sec="Supplementary Table 8, Pass %",
           loc=("cell", "Supplementary Table 8 | Compute cost per answer by generation strategy", c, 9),
           claimed=v, m=("rate", c), retired=GONE_T8)
      for i, (c, v) in enumerate([("single_pass", "79.5"), ("multi_hop", "77.3"), ("verified_pass", "67.0"),
                                  ("rlm_5", "88.6"), ("rlm_10", "92.0"), ("rlm_20", "86.4")])],
    dict(id="C32", doc="SI", sec="Supplementary Table 2, row 'exp04, generation-strategy run', Pass %",
         loc=("cell", "Supplementary Table 2 | Independent draws", "exp04, generation-strategy run", 8),
         claimed="92.0", m=("rate", "rlm_10"), retired=GONE_T2),
    dict(id="C33", doc="SI", sec="Supplementary Table 2, same row, difference from single-pass (pp)",
         loc=("cell", "Supplementary Table 2 | Independent draws", "exp04, generation-strategy run", 9),
         claimed="12.5", m=("diff", "rlm_10", "single_pass"), retired=GONE_T2),
    dict(id="C34", doc="SI", sec="Supplementary Table 2, same row, single-pass passes only",
         loc=("cell", "Supplementary Table 2 | Independent draws", "exp04, generation-strategy run", 10),
         claimed="4", m=("only_b", "rlm_10", "single_pass"), retired=GONE_T2),
    dict(id="C35", doc="SI", sec="Supplementary Table 2, same row, draw passes only",
         loc=("cell", "Supplementary Table 2 | Independent draws", "exp04, generation-strategy run", 11),
         claimed="15", m=("only_a", "rlm_10", "single_pass"), retired=GONE_T2),
    dict(id="C36", doc="SI", sec="Supplementary Table 2, same row, McNemar exact P",
         loc=("cell", "Supplementary Table 2 | Independent draws", "exp04, generation-strategy run", 12),
         claimed="0.019", m=("p", "rlm_10", "single_pass"), retired=GONE_T2),
    dict(id="C37", doc="LT", sec="Reviewer 1, Comment 1.1, iterative retrieval", loc=(
         "text", P_LT_R1, "single pass passed 82.9% of answers and RLM-10 74.0%"), claimed="74.0",
         m=("rate", "rlm_10"), t=4),
    dict(id="C38", doc="LT", sec="Reviewer 3, Major Point 3", loc=(
         "text", "Here, the figure was correct, but the text was wrong",
         "92.0% against the 90.9% printed in the submitted manuscript"), claimed="92.0", m=("rate", "rlm_10"),
         retired="the letter no longer sets the re-judged rate against the printed one; Major Point 3 quotes the "
                 "agreed sentence (C39)"),
    dict(id="C39", doc="LT", sec="Reviewer 3, Major Point 3 (the sentence quoted)", loc=(
         "text", P_POOLED, "and RLM-10 74.0% (95% CI: 67.8% to 79.8%)"), claimed="74.0", m=("rate", "rlm_10"), t=4),
    dict(id="C40", doc="LT", sec="Reviewer 1, Comment 1.1, iterative retrieval", loc=(
         "text", P_LT_R1, "The difference, 8.9 points in favour of single pass, did not reach significance (95% CI 0.0 "
         "to 17.8; exact P = 0.067)"), claimed="8.9", m=("diff", "single_pass", "rlm_10"), t=4),
    *[dict(id=f"C{41 + i}", doc="LT", sec="Reviewer 4, Question 2, Table R4.1, pass rate at score 4",
           loc=("cell", P_LT_TABLE, lab, 6), claimed=v, m=("rate", c), t=4)
      for i, (c, lab, v) in enumerate([("single_pass", "single pass", "82.9"), ("multi_hop", "multi-hop", "78.7"),
                                       ("verified_pass", "passage verification", "83.3"),
                                       ("rlm_5", "RLM-5", "73.3"), ("rlm_10", "RLM-10", "74.0"),
                                       ("rlm_20", "RLM-20", "70.5")])],
    dict(id="C47", doc="LT", sec="Reviewer 4, Question 2, Table R4.1, model calls per answer (135 questions)",
         loc=("cell", P_LT_TABLE, "RLM-10", 1), claimed="7.29", m=("cost_mean", "all", "rlm_10", "calls", 2)),
    dict(id="C48", doc="LT", sec="Reviewer 4, Question 2, the comparators", loc=(
         "text", "Two of the three comparators the reviewer names were run",
         "with RLM-10 ahead on 13 more of the 88 questions, 14.8 points"), claimed="13 more, 14.8 points",
         m=("net", "rlm_10", "multi_hop"),
         retired="the letter no longer gives the net count; it gives both rates (C49)"),
    dict(id="C49", doc="LT", sec="Reviewer 4, Question 2, the multi-query baseline", loc=(
         "text", "Retrieval calls follow from each design", "it passed 78.7% of answers, against 74.0% for RLM-10"),
         claimed="78.7 against 74.0", m=("rate_pair", "multi_hop", "rlm_10"), t=4),
    *[dict(id=f"C{50 + i}", doc="LT", sec="Reviewer 4, Question 2, the eight draws",
           loc=("cell", "We also recovered judge scores for eight draws", "exp04, generation-strategy run", k),
           claimed=v, m=mm, retired="the eight-draws table is not in the letter any more")
      for i, (k, v, mm) in enumerate([(2, "92.0", ("rate", "rlm_10")), (3, "+12.5", ("diff", "rlm_10", "single_pass")),
                                      (4, "0.019", ("p", "rlm_10", "single_pass"))])],
    dict(id="C53", doc="LT", sec="Reviewer 4, Comment 2d", loc=(
         "text", P_LT_FP, "single pass passed all 30 of its answers. Multi-hop retrieval and passage verification passed "
         "28, RLM-5 and RLM-20 26 and RLM-10 25 of 30"),
         claimed="single pass 30, multi-hop 28, verified pass 28, RLM-5 26, RLM-10 25, RLM-20 26 of 30",
         m=("fp", {"single_pass": 30, "multi_hop": 28, "verified_pass": 28, "rlm_5": 26, "rlm_10": 25, "rlm_20": 26}),
         t=4),
    # panel c (Rule 4): the passage-verification flip
    dict(id="C54", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "15 of 19 altered outputs became incorrect (78.9%; two-sided exact McNemar P = 0.019)"),
         claimed="15 of 19, 78.9%", m=("flip", "verified_pass", 3, "share"),
         retired="the agreed text gives the harmed share at score 4 only (C57)"),
    dict(id="C55", doc="SI", sec=SEC_N3, loc=("text", P_N3_FLIP, "harmed share 48.5%, 95% CI: 28.2% to 73.4%; two-sided "
         "exact P = 1)"), claimed="1", m=("flip_p", "verified_pass", 4)),
    dict(id="C56", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "degrading 15 of 70 baseline-correct answers (21.4%; Fig. 2e)"), claimed="15 of 70, 21.4%",
         m=("flip", "verified_pass", 3, "degraded"),
         retired="the agreed text gives the degraded share at score 4 only (C58)"),
    dict(id="C57", doc="SI", sec=SEC_N3, loc=("text", P_N3_FLIP, "passage verification, which filters retrieved passages "
         "with an intermediate LLM check before generation, harmed a mean of 5.6 answers and helped 5.9 (harmed share "
         "48.5%"), claimed="48.5%", m=("flip", "verified_pass", 4, "share")),
    dict(id="C58", doc="SI", sec=SEC_N3, loc=("text", P_N3_FLIP, "Of the answers single pass got right, passage "
         "verification degraded 7.8% (95% CI: 4.0% to 12.2%)"), claimed="7.8%",
         m=("flip", "verified_pass", 4, "degraded")),
    dict(id="C59", doc="MT", sec="Introduction", loc=("text", "We report a factorial evaluation of the design",
         "78.9% of the outcomes it changes go from correct to incorrect"), claimed="78.9%",
         m=("flip", "verified_pass", 3, "share"), retired="the Introduction no longer gives a flip share"),
    dict(id="C60", doc="MT", sec=SEC_DISC, loc=("text", "Across our experiments, steps that processed the model",
         "our passage verifier turned 15 of 70 (21.4%)"), claimed="15 of 70, 21.4%",
         m=("flip", "verified_pass", 3, "degraded"),
         retired="the Discussion says it in words only, 'changed as many answers for the worse as for the better' "
                 "(the numbers are C57, C58)"),
    *[dict(id=f"C{61 + i}", doc="FT", sec="Figure 2 legend", loc=("text", "Figure 2 | Generation strategy.", w),
           claimed=v, m=mm, retired="the agreed Figure 3 legend depicts panel c without results (FIGURE_LOCK [legend] "
                                    "depicts_not_results); the numbers are C57, C58")
      for i, (w, v, mm) in enumerate([
          ("15 of the 19 changed outcomes became incorrect (78.9%; two-sided exact McNemar P = 0.019)",
           "15 of 19, 78.9%", ("flip", "verified_pass", 3, "share")),
          ("degrading 15 of the 70 answers single-pass got right (21.4%)", "15 of 70, 21.4%",
           ("flip", "verified_pass", 3, "degraded")),
          ("At a threshold of 4, 15 of 18 did (83.3%; exact P = 0.0075), degrading 15 of 47 (31.9%)",
           "15 of 18, 83.3%", ("flip", "verified_pass", 4, "share"))])],
    dict(id="C64", doc="FT", sec=LEG, loc=("text", P_FIG3, "Bars, means over n = 9 pairings of draws"),
         claimed="n = 9 pairings of draws", m=("n", "pairings")),
    dict(id="C65", doc="LT", sec="Reviewer 1, Comment 1.1, self-correction", loc=(
         "text", P_LT_R1_SELF, "The harmed share of changed answers was 48.5% (95% CI 28.2% to 73.4%; two-sided exact "
         "P = 1)"), claimed="48.5%", m=("flip", "verified_pass", 4, "share")),
    dict(id="C66", doc="LT", sec="Reviewer 1, Comment 1.1, the revised abstract quoted", loc=(
         "text", "Retrieval-augmented generation grounds large language models",
         "78.9% of the answers whose outcome it changes become incorrect, degrading 21.4% of initially correct"),
         claimed="78.9%, 21.4%", m=("flip", "verified_pass", 3, "share"),
         retired="the agreed abstract the letter quotes gives no flip share"),
    dict(id="C67", doc="LT", sec="Reviewer 2, Comment 1", loc=(
         "text", "The contribution is the ablation and what it found",
         "among answers whose outcome it changes, 78.9% flip from correct to incorrect"), claimed="78.9%",
         m=("flip", "verified_pass", 3, "share"), retired="the letter's answer to Reviewer 2, Comment 1 no longer gives "
                                                          "a flip share"),
    dict(id="C68", doc="LT", sec="Reviewer 4, Comment 1", loc=(
         "text", P_LT_R4C1, "Of the answers single pass got right, it degraded 7.8% (95% CI 4.0% to 12.2%"),
         claimed="7.8%", m=("flip", "verified_pass", 4, "degraded")),
    dict(id="C69", doc="LT", sec="Reviewer 4, Comment 1", loc=(
         "text", P_LT_R4C1, "Of the changed outcomes, 48.5% were harmed (95% CI 28.2% to 73.4%; two-sided exact P = 1)"),
         claimed="48.5%", m=("flip", "verified_pass", 4, "share")),
]
# Panel b's rows, listed only when rank is given --concept-recall (22 October): the documents' concept-recall numbers
# for Figure 3, set against the values sheet Fig. 3a draws (D181's reading on key v2.5 since D188).
CLAIM_ROWS_B = [
    dict(id="B1", doc="MT", sec=SEC_GEN, loc=("text", "Among iterative strategies, RLM-10 achieved the highest",
         "RLM-20 achieved the highest concept recall (72.3%; Fig. 2b)"), claimed="72.3", m=("cr", "rlm_20"),
         retired="the agreed text gives no strategy's concept recall value (the letter's is B3; the rank is B2)"),
    dict(id="B2", doc="MT", sec="Results, 'The three signals disagree on the best strategy'", loc=(
         "text", "The strategy comparison above rests on the judge's pass rate",
         "whereas concept recall ranked RLM-10 first and single pass fifth"),
         claimed="RLM-10 highest concept recall of the six", m=("cr_verdict", "highest", "rlm_10")),
    dict(id="B3", doc="LT", sec="Reviewer 3, Major Point 3", loc=(
         "text", P_LT_R3MP3, "RLM-10 has the highest mean concept recall, 76.2% against 75.1% for RLM-20"),
         claimed="76.2 against 75.1", m=("cr_pair", "rlm_10", "rlm_20")),
    dict(id="B4", doc="LT", sec="Reviewer 3, Major Point 3 (the sentence quoted)", loc=(
         "text", "Among iterative strategies, RLM-10 achieved the highest",
         "RLM-20 achieved the highest concept recall (72.3%; Fig. 2b)"), claimed="72.3", m=("cr", "rlm_20"),
         retired="the sentence the letter quotes now gives no concept recall"),
]
DESIGN = {
    "questions": ("135 questions: 86 answerable, 10 false premise, 39 not answerable (D7 drops 3; D5 moves the ten "
                  "false-premise questions out of refusal; Rule 8)", "differs: design"),
    "answerable": ("86 answerable questions (D7)", "differs: design"),
    "legend_a": ("86 answerable questions; the interval is Rule 2's question bootstrap, not Wilson",
                 "differs: design"),
    "judge": (f"{JUDGE} (LOCK [judge], D88), n = 86 per strategy", "differs: design"),
    "legend_d": ("39 not-answerable questions per strategy; an answer with no text counts as not refused (Rule 10), "
                 "so n = 39 for every strategy", "differs: design"),
    "legend_e": ("86 answerable questions, every single-pass draw against every draw of the strategy (Rule 4: 9 "
                 "pairings with three draws), means over the pairings", "differs: design"),
}


def read_docs() -> dict:
    """{doc key: [paragraph accepted text, ...]} for the documents that exist (every w:t, deleted text left out)."""
    import zipfile
    from lxml import etree
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    out = {}
    for k, p in DOCS.items():
        if p.exists():
            x = etree.fromstring(zipfile.ZipFile(p).read("word/document.xml"))
            out[k] = ["".join(t.text or "" for t in q.iter(w + "t")) for q in x.iter(w + "p")]
    return out


def locate(paras: list[str], loc) -> bool:
    """Whether the row's words (or cell) are in the document now."""
    if loc[0] == "text":
        return any(q.startswith(loc[1]) and loc[2] in q for q in paras)
    _, anchor, label, k = loc
    for i, q in enumerate(paras):
        if q.startswith(anchor):
            for j in range(i + 1, len(paras)):
                if paras[j].strip() == label:
                    return True
    return False


def cell_text(paras, loc):
    _, anchor, label, k = loc
    for i, q in enumerate(paras):
        if q.startswith(anchor):
            for j in range(i + 1, len(paras) - k):
                if paras[j].strip() == label:
                    return paras[j + k].strip()
    return None


DEF_39 = "; definition: 39 questions, not 50 (D5, D7)"   # said of the submitted text's rows (retired since D304)


def claim_value(row, res, cost=None, crx=None, read=None, draws=None):
    """(what S463 gives, status) for one claims-list row. Numbers are compared at the text's precision, at the row's
    judge score t (3 when the row gives none)."""
    m = row["m"]
    t = row.get("t", 3)
    if m[0] == "n":                           # D304: a count the agreed text prints, recounted from the rows read
        ng = Counter(read["groups"].values())
        if m[1] == "questions":
            got = f"{sum(ng.values())} questions"
            what = (f"{sum(ng.values())} questions read: {ng['answerable']} answerable, {ng['not_answerable']} out of "
                    f"scope, {sum(ng.values()) - ng['answerable'] - ng['not_answerable']} false premise")
        elif m[1] == "not_answerable":
            got = what = f"n = {ng['not_answerable']}"
        elif m[1] == "pairings":
            got = what = f"n = {len(draws) ** 2} pairings of draws"
            what += f" (draws {', '.join(map(str, draws))}, every single-pass draw against every draw)"
        else:
            kinds = S511.questions()
            qa = list(res["answerable"][4]["shares"]["single_pass"])
            k = Counter(kinds[q]["kind"] for q in qa)
            got = (f"n = {len(qa)} answerable ({k['one']} one-paper, {k['many']} many-paper)" if m[1] == "answerable_split"
                   else f"{len(qa)} answerable questions")
            what = got
        return what, "matches" if got == row["claimed"] else "differs"
    if m[0] == "judge":
        got = f"{JUDGE}, n = {len(draws)} draws"
        return f"{got} (LOCK [judge], D88)", "matches" if got == row["claimed"] else "differs"
    if m[0] == "cost_words":                  # D304: "about six times the model calls", on the questions the row names
        r = cost[m[1]]["ratio_rlm10_single"]
        w = S457.printed_as("words", r[m[2]])
        ok = f"{w} the model calls" in row["claimed"]
        return (f"RLM-10 over single pass, {'all 135' if m[1] == 'all' else 'the 86 answerable'} questions: "
                f"{S457.half_up(r[m[2]], 2)} times the model calls ({w}); G1's records",
                "matches" if ok else f"differs: {w}")
    if m[0] == "cost_mean":                   # D304: a mean per answer from G1's records (the letter's Table R4.1)
        _, scope, c, what, nd = m
        got = S457.half_up(cost[scope][c][what]["mean"], nd)
        return (f"{LABEL[c]} {got} {'model calls' if what == 'calls' else 's'} per answer, "
                f"{'all 135' if scope == 'all' else 'the 86 answerable'} questions, G1's records",
                "matches" if got == row["claimed"] else "differs")
    if m[0] == "fp":                          # D304: the false-premise counts at the row's score
        fp = res["false_premise"][t]
        txt = (f"passed against the refutation at score {t}: "
               + ", ".join(f"{LABEL[c]} {fp[c]['passed']} of {fp[c]['answers']}" for c in CONFIGS))
        if isinstance(m[1], dict):
            ok = all(fp[c]["passed"] == n for c, n in m[1].items())
        else:
            _, sp, lo, hi = m[1]
            others = [fp[c]["passed"] for c in CONFIGS if c != "single_pass"]
            ok = fp["single_pass"]["passed"] == sp and (min(others), max(others)) == (lo, hi)
        return txt, "matches" if ok else "differs"
    if m[0] == "flip_p":                      # D304: the flip's exact P, at the precision printed
        p = res["flips"][m[2]][m[1]]["p"]
        nd = len(row["claimed"].split(".")[1]) if "." in row["claimed"] else 0
        got = S457.half_up(p, nd)
        return (f"score {m[2]} or more, {LABEL[m[1]]} against single pass: P {pfmt(p)}",
                "matches" if got == row["claimed"] else "differs")
    if m[0].startswith("cr"):               # panel b (CLAIM_ROWS_B): the concept recall panel b draws
        s = crx["res"]["value"]["summary"]
        cv = lambda c: S457.half_up(100 * s[c]["rate"], 1)                           # noqa: E731
        if m[0] == "cr":
            got = cv(m[1])
            return (f"{LABEL[m[1]]} {got}% ({crx['info']['reading']} reading)",
                    "matches" if got == row["claimed"] else "differs")
        if m[0] == "cr_pair":
            got = f"{cv(m[1])} against {cv(m[2])}"
            x = pair(crx["res"]["value"]["pairs"], m[1], m[2])
            return (f"{LABEL[m[1]]} {cv(m[1])}% against {LABEL[m[2]]} {cv(m[2])}% (P {pfmt(x['p'])})",
                    "matches" if got == row["claimed"] else "differs")
        r6 = crx["res"]["value"]["rule6"]
        claim = (row["id"], row["claimed"], m[1], m[2], None, "answerable")
        r = r6[m[1]]
        tie = f", tied with {', '.join(LABEL[x] for x in r['tied_with'])}" if r["tied_with"] else ""
        return (f"{m[1]} by mean: {LABEL[r['strategy']]}{tie}; Rule 6 " + ("met" if r["met"] else "not met"),
                verdict(claim, s, crx["res"]["value"]["pairs"], r6))
    if m[0] == "cost_ratio":                 # the Discussion's words, on all 135 questions as S77 reads the letter's
        r = cost["all"]["ratio_rlm10_single"]
        w = (S457.printed_as("words", r["calls"]), S457.printed_as("words", r["clock_s"]))
        ok = w == ("six times", "eight times")
        ra = cost["answerable"]["ratio_rlm10_single"]
        return (f"RLM-10 over single pass, all 135 questions: {S457.half_up(r['calls'], 2)} times the model calls "
                f"({w[0]}), {S457.half_up(r['clock_s'], 2)} times the clock time ({w[1]}); on the 86 answerable: "
                f"{S457.half_up(ra['calls'], 2)} and {S457.half_up(ra['clock_s'], 2)}",
                "holds" if ok else "changes: " + ", ".join(f"{a} where the text says {b}" for a, b in
                                                          zip(w, ("six times", "eight times")) if a != b)
                + "; G1's records, not the submitted run (S77)")
    if m[0] == "cost_letter":
        cl = cost["all"]
        got = (S457.half_up(cl["rlm_10"]["calls"]["mean"], 2), S457.half_up(cl["single_pass"]["calls"]["mean"], 2),
               S457.half_up(cl["rlm_10"]["clock_s"]["mean"], 1), S457.half_up(cl["single_pass"]["clock_s"]["mean"], 1))
        want = ("5.87", "1.00", "82.4", "10.4")
        return (f"all 135 questions: RLM-10 {got[0]} calls against {got[1]}, {got[2]} s against {got[3]} s",
                "holds" if got == want else "changes: " + ", ".join(f"{a} where the text says {b}"
                                                                    for a, b in zip(got, want) if a != b)
                + "; G1's records, not the submitted run (S77)")
    if m[0] == "flip":
        def flip_at(t):
            x = res["flips"][t][m[1]]
            if m[3] == "share":
                v, k, n = x["harm_share"], x["harmed"], x["changed"]
            else:
                v, k, n = x["degraded_share"], x["harmed"], x["baseline_correct"]
            g = S457.half_up(100 * v, 1) if v is not None else "-"
            return g, (f"{g}% ({S457.half_up(k, 2)} of {S457.half_up(n, 2)}, means over the draw pairings; "
                       f"P {pfmt(x['p'])})")
        what = "harmful share of changed outcomes" if m[3] == "share" else "single pass's correct answers degraded"
        claimed_pct = re.findall(r"(\d+\.\d)%", row["claimed"])
        got, txt = flip_at(m[2])
        # D160 (12), Q11: a row read at score 3 also gives the score-4 value beside it; the status compares score 3
        also4 = f"; score 4 or more: {flip_at(4)[1]}" if m[2] == 3 else ""
        return (f"score {m[2]} or more, {what}: {txt}{also4}",
                "matches" if claimed_pct and claimed_pct[0] == got else "differs")
    # D160 (12), Q11: the printed numbers used score 3, so each row is compared at 3 (its status) and also gives the
    # score-4 value (D154's pass rate) beside it, so the rewrite of each sentence sees both; no figure number changes
    a3, a4 = res["answerable"][3], res["answerable"][4]
    rf = res["refusal"][REFUSAL_T]
    rate = lambda c: 100 * a3["summary"][c]["rate"]                                  # noqa: E731
    rate4 = lambda c: 100 * a4["summary"][c]["rate"]                                 # noqa: E731
    refd = lambda c: 100 * rf["summary"][c]["rate"]                                  # noqa: E731

    def same(v, claimed, nd):
        got = S457.half_up(v, nd)
        return got, ("matches" if got == claimed.lstrip("+") else "differs")
    nd = len(row["claimed"].split(".")[1]) if "." in row["claimed"] and m[0] in ("rate", "refused", "diff", "p",
                                                                                 "fail_rate") else 1
    if m[0] == "rate":
        got, st = same(rate(m[1]) if t == 3 else rate4(m[1]), row["claimed"], nd)
        return (f"{LABEL[m[1]]} {S457.half_up(rate(m[1]), nd)}% at score 3; {S457.half_up(rate4(m[1]), nd)}% at "
                f"score 4"), st
    if m[0] == "rate_after_slash":
        claimed = row["claimed"].split("/")[-1].strip()
        got, st = same(rate(m[1]), claimed, 1)
        return (f"{LABEL[m[1]]} {got}% at score 3 (against the re-judged {claimed}); "
                f"{S457.half_up(rate4(m[1]), 1)}% at score 4", st)
    def bound(c):
        """A 0's one-sided 95% upper bound (Rule 9) or a 100%'s lower bound (O2) beside the rate, as panel b draws it."""
        x = rf["summary"][c]
        return (f" (one-sided 95% upper bound {S457.half_up(100 * x['zero_bound'], 1)}%)" if x["zero_bound"] is not None
                else f" (one-sided 95% lower bound {S457.half_up(100 * x['full_bound'], 1)}%)"
                if x["full_bound"] is not None else "")
    if m[0] == "refused":
        got, st = same(refd(m[1]), row["claimed"], nd)
        return f"{LABEL[m[1]]} {got}% of 39{bound(m[1])}", st + (DEF_39 if row.get("retired") else "")
    if m[0] == "refused2":
        g1, s1 = same(refd(m[1]), row["claimed"], 1)
        g2, s2 = same(refd(m[2]), row["claimed"], 1)
        return (f"{LABEL[m[1]]} {g1}%{bound(m[1])}, {LABEL[m[2]]} {g2}%{bound(m[2])} of 39",
                ("matches" if s1 == s2 == "matches" else "differs") + (DEF_39 if row.get("retired") else ""))
    if m[0] == "fail_rate":
        got, st = same(100 - rate(m[1]), row["claimed"], nd)
        return (f"{LABEL[m[1]]} fails {got}% of the 86 at score 3; {S457.half_up(100 - rate4(m[1]), nd)}% at "
                f"score 4"), st
    if m[0] in ("diff", "p", "only_a", "only_b", "net"):
        x, x4 = pair(a3["pairs"], m[1], m[2]), pair(a4["pairs"], m[1], m[2])
        if m[0] == "diff":
            got, st = same(100 * (x if t == 3 else x4)["d"], row["claimed"], nd)
            return (f"{LABEL[m[1]]} minus {LABEL[m[2]]} {S457.half_up(100 * x['d'], nd)} points (P {pfmt(x['p'])}) at "
                    f"score 3; {S457.half_up(100 * x4['d'], nd)} points (P {pfmt(x4['p'])}) at score 4"), st
        if m[0] == "p":
            got = pfmt((x if t == 3 else x4)["p"])
            return (f"P {pfmt(x['p'])} at score 3; P {pfmt(x4['p'])} at score 4",
                    "matches" if got == row["claimed"] else "differs")
        if m[0] == "net":
            net, got = x["a_higher"] - x["b_higher"], S457.half_up(100 * x["d"], 1)
            ok = f"{net} more" in row["claimed"] and f"{got} points" in row["claimed"]
            return (f"{LABEL[m[1]]} ahead on {net} more of {x['questions']}, {got} points at score 3; "
                    f"{x4['a_higher'] - x4['b_higher']} more of {x4['questions']}, "
                    f"{S457.half_up(100 * x4['d'], 1)} points at score 4", "matches" if ok else "differs")
        v = x["a_higher"] if m[0] == "only_a" else x["b_higher"]
        v4 = x4["a_higher"] if m[0] == "only_a" else x4["b_higher"]
        return (f"{v} questions only {LABEL[m[1] if m[0] == 'only_a' else m[2]]} passes at score 3; {v4} at score 4",
                "matches" if str(v) == row["claimed"] else "differs")
    if m[0] == "rate_pair":
        g1, g2 = S457.half_up(rate(m[1]), 1), S457.half_up(rate(m[2]), 1)
        h1, h2 = S457.half_up(rate4(m[1]), 1), S457.half_up(rate4(m[2]), 1)
        return (f"{g1}% against {g2}% at score 3; {h1}% against {h2}% at score 4",
                "matches" if row["claimed"] == (f"{g1} against {g2}" if t == 3 else f"{h1} against {h2}") else "differs")
    if m[0] == "verdict":
        v3, v4 = res["verdicts"][3][m[1]], res["verdicts"][4][m[1]]
        return f"Rule 11 {m[1]}", (f"{v4} at score 4, {v3} at 3" if v4 else f"{v3} at score 3")
    if m[0] == "refusal_rank":
        r = rf["rule6"]["highest"]
        tie = f" tied with {', '.join(LABEL[x] for x in r['tied_with'])}" if r["tied_with"] else ""
        return (f"first by mean: {LABEL[r['strategy']]}{tie}",
                "no rule decides a shared first place (S393_early_claims.md:233); "
                + ("Rule 6 met" if r["met"] else "Rule 6 not met"))
    if m[0] == "fp_changed":
        fp = lambda t: ", ".join(f"{LABEL[c]} {res['false_premise'][t][c]['passed']} of "   # noqa: E731
                                 f"{res['false_premise'][t][c]['answers']}" for c in CONFIGS)
        return (f"passed against the refutation at score 3: {fp(3)}; at score 4: {fp(4)}",
                "no longer applies: Rule 9 scores the ten as passed against the refutation, counts only")
    if m[0] == "design":
        return DESIGN[m[1]]
    return "-", f"not measured here: {m[1]}"


def claims_md(res, read, draws, stamp, cost, crx=None) -> str:
    docs = read_docs()
    dtext = dtext_of(draws)
    L = [f"# Figure 3, panels {'a to e' if crx else 'a, c, d and e'}: claims list (D82)", "",
         f"Written by `scripts/S463_fig2_ranking.py rank` with the ranking it sits beside. Data stamp: {stamp}.", "",
         "Every number the Main Text, the Figure 3 legend, the Supplementary Notes and the letter give for "
         "Figure 3's pass rate (panel a), refusal (panel b), verified pass against single pass (panel c) and cost (panel d)"
         + (", and concept recall (sheet Fig. 3a, D181's reading on key v2.5)" if crx else "")
         + ", set against what S463 computes from the judge's scores and G1's generation records. Every value "
         f"here is provisional ({dtext}, D82, D88): a status says how the provisional value "
         "compares, at the text's precision, and is read again on the final run. Paragraphs are located by section "
         "and opening words, never by number. 'In the text now' says whether those words are in the document's "
         "accepted text (every mark accepted, deleted text left out) as read by this run.", "",
         "D304 (8 November): every row is anchored on the agreed text (Claude Docs rev 3688, as the live documents "
         "read with every mark accepted) or retired. A retired row keeps the submitted words it was found by and says "
         "why the agreed text no longer states it; its value is still computed. The letter's rows are anchored on the "
         "letter with every mark accepted; the letter round will be rebuilt (numbers that are never regenerated come "
         "out), so those anchors are provisional.", "",
         "Each row's status compares the value at the judge score the row is read at: 4, the paper's pass (D154), for "
         "every row re-anchored on the agreed text; 3 for the retired rows, whose submitted text used 3. 'S463 gives' "
         "shows both scores on every row that reads a pass at a threshold (D160 Q11). Refusal (Rule 9: score 3 only), "
         "cost and concept recall have no score-4 value; Rule 11's verdicts give each threshold they are read at (E6, "
         "a refusal claim, at 3 only).", "",
         "Documents read: " + "; ".join(f"{DOC_NAME[k]} `{DOCS[k].relative_to(ROOT)}` sha256 "
                                       f"{sha256_file(DOCS[k])[:12]}" for k in DOCS if k in docs)
         + ("; not found: " + ", ".join(str(DOCS[k].relative_to(ROOT)) for k in DOCS if k not in docs)
            if len(docs) < len(DOCS) else "") + ".", "",
         "| Row | Where (search for) | Claimed | S463 gives | Status | In the text now |", "|---|---|---|---|---|---|"]
    counts, here_n = Counter(), Counter()
    for row in CLAIM_ROWS + (CLAIM_ROWS_B if crx else []):
        paras = docs.get(row["doc"])
        if row.get("retired"):
            here = f"retired: {row['retired']}"
        elif paras is None:
            here = "document not read"
        else:
            here = "yes" if locate(paras, row["loc"]) else "NOT FOUND: re-read the document"
            if row["loc"][0] == "cell" and here == "yes":
                got = cell_text(paras, row["loc"])
                here = "yes" if (got or "").rstrip("%") == row["claimed"] else f"the cell now reads {got!r}"
        here_n["retired" if here.startswith("retired") else "found" if here == "yes" else "not found"] += 1
        val, st = claim_value(row, res, cost, crx, read, draws)
        m_ = re.match(r"(matches|differs: design|differs|changes|no longer applies|not measured here|no rule decides|"
                      r"holds|weakens|reverses)", st)
        counts[m_.group(1) if m_ else st] += 1
        if row.get("t") and row["m"][0] in ("rate", "diff", "p", "rate_pair", "fp"):
            st += f" (at score {row['t']})"
        where = (f"{DOC_NAME[row['doc']]}, {row['sec']}: '{row['loc'][1]}'"
                 + (f", row '{row['loc'][2]}'" if row["loc"][0] == "cell" else ""))
        L.append(f"| {row['id']} | {where} | {row['claimed']} | {val} | {st} | {here} |")
    L += ["", "Rows by status: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".",
          "Rows in the text: " + ", ".join(f"{k} {v}" for k, v in sorted(here_n.items())) + ".", "",
          "Status words: matches and differs compare the provisional value with the printed one at its precision; "
          "'differs: design' is a count or a method the revision changed (the row says which decision); a Rule 11 "
          "verdict (holds, weakens, reverses) is given for each claim of direction or rank; 'no longer applies' and "
          "'not measured here' say why no value is set against the text. Every mismatch feeds W1 (D82).", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------
# rank
# ---------------------------------------------------------------------------------------------------------------
def generator(read):
    """The generator the records judged name (gen_model, one value), or a plain phrase when --answers was not given."""
    g = {str(c.get("gen_model")).split("::")[-1] for c in read["cells"].values() if c.get("gen_model")}
    if len(g) > 1:
        raise Refused(f"the generation records name {len(g)} generators: {sorted(g)}")
    return next(iter(g)) if g else "G1's generator"


LEGEND_CONCEPT_RECALL = False                            # S456's "Concept recall" row named Figure 3's legend until B1's
#                                                          part 2 took Figure 3 off it (fig1.md:125)


def legend_text(res, read, draws, stamp, out_t, cost, q78, crx=None, extra=None, book=None, fe=None):
    """The title and legend of Figure 3 (fig3.md section 5): what the plate depicts, panel by panel (FIGURE_LOCK [legend]
    depicts_not_results), with no provisional wording, no results, no codes. Each count and n is read from the rows
    drawn: answers with no text from sheet 3a's eight rows and sheet 3b's cells, the split and block n from sheet 3f,
    the distractor ratios and the draws read from S522's tables."""
    a4 = [r for r in rows_of(book, "Fig. 3a", "strategy") if r["threshold"] == PRIMARY]
    nua = sum(r["judge_calls_without_score"] for r in a4)
    ng = Counter(read["groups"].values())
    na, nn = ng["answerable"], ng["not_answerable"]
    o = rows_of(book, "Fig. 3a", ORDER_KIND)
    n1, n2 = (sum(1 for r in o if r["question_type"] == g) for g in ("one", "many"))
    rf = res["refusal"][REFUSAL_T]["summary"]
    dashed = any(rf[c]["zero_bound"] is not None or rf[c]["full_bound"] is not None for c in CONFIGS)
    nd = len(draws)
    E = book["Fig. 3f"]
    ns = {(r["block"], r["question_group"], r["core_papers"]): r["n_questions"] for r in E if r["row_kind"] == "n"}
    sizes = sorted({k[2] for k in ns})

    def nlist(block, group):
        return ", ".join(str(ns[(block, group, c)]) for c in sizes)
    over = any(r["row_kind"] == "cell" and r["d_pp"] is not None and abs(r["d_pp"]) > E_SCALE for r in E)
    past = f"; colour capped at {E_SCALE:.0f} points" if over else ""
    mk = {r["strategy"]: r for r in rows_of(book, "Fig. 3a", MARGIN_KIND)}
    vp_wait = S457.half_up(mk["verified_pass"]["clock_s_mean_with_wait"], 0) if "verified_pass" in mk else None
    # 3e (the T2 panel): with S518's rows drawn, fig3.md section 5's room for the filled panel: the resampling clause
    # and the pass definition move to Methods (n, "two-sided" and each interval's definition stay); n by source from
    # the rows, the test sources' counts first
    e3 = rows_of(book, "Fig. 3e", E3_KIND) if "Fig. 3e" in book else []
    if e3:
        nq = list(dict.fromkeys((r["questions_one_paper"], r["questions_many_paper"]) for r in e3))
        lab = defaultdict(list)
        for r in e3:
            if r["measure"] == "interaction":
                lab[(r["questions_one_paper"], r["questions_many_paper"])].append(r["source_label"])
        full = max(nq)
        part = "; ".join(f"{', '.join(lab[k])}: {k[0]}, {k[1]}" for k in nq if k != full)
        # D289: I alone is drawn; the rows' groups are named by their place on the plate (e3_layout), not by heads
        ys_e, _ = e3_layout(list(dict.fromkeys((r["source"], r["role"]) for r in e3)))
        role_e = {r["source"]: r["role"] for r in e3}
        order_e = [role_e[s] for s in sorted(ys_e, key=ys_e.get)]
        t_rows = [k + 1 for k, ro in enumerate(order_e) if ro == "test"]
        where = []
        if t_rows:
            where.append(f"rows {t_rows[0]} to {t_rows[-1]}, the prespecified test" if len(t_rows) > 1
                         else f"row {t_rows[0]}, the prespecified test")
        where_t = "; ".join(where)
        where_t = (where_t[0].upper() + where_t[1:] + ". ") if where_t else ""
        # Valerio, 8 Nov ("too long"): the strategy names, the matched budget, the resample count, the no-text rule
        # and the distractor pooling are in Methods; per-model and split-row n, and the no-text count, in Source Data
        e_t = (f"**e**, RLM-10's gain over single pass, many-paper minus one-paper; lines, intervals. {where_t}"
               f"Second judge, {judge2()}; "
               + ("n as **a**" if full == (n1, n2) else f"n = {full[0]} one-paper and n = {full[1]} many-paper questions")
               + ("; other models' n in Source Data" if part else "") + ". ")
        pass_t = f" (pass, score {PRIMARY} or more; relaxed, {THRESHOLDS[1]} or more)"
        iv_t = "Intervals: two-sided 95%, question bootstrap. "
    else:
        e_t = "**e**, Replication on other generators. "
        pass_t = f" (pass, score {PRIMARY} or more; relaxed, {THRESHOLDS[1]} or more)"
        iv_t = "Intervals: two-sided 95%, question bootstrap. "
    return (
        f"# Figure 3, title and legend (draft)\n\n"
        f"Written by `scripts/S463_fig2_ranking.py rank` from the plotted numbers. Data stamp: {stamp}.\n\n"
        f"**Figure 3 | Answer strategies against single pass, by the judge's pass rate.** Six strategies answered "
        f"{sum(ng.values())} questions with {E3_LABEL.get(generator(read), generator(read))} in n = {nd} draws, judged by {JUDGE} for judge correctness"
        f"{pass_t}. "
        f"{iv_t}**a**, The n = {na} answerable questions "
        f"(n = {n1} one-paper, n = {n2} many-paper) by strategy; tiles, draws passed at score {PRIMARY}."
        + (f" Judge calls with no score (n = {nua}) are left out." if nua else "")
        + (" Right, time per answer less the local server's wait; black, mean."
           if vp_wait else "")
        + f" **b**, As **a** for the n = {nn} {fn.OUT_OF_SCOPE_QUESTIONS}; tiles, draws refused (refusal score "
        f"{REFUSAL_T} or more); right, refusal rate and interval"
        + ("; dashed, one-sided 95% bound at 0 or 100%" if dashed else "") + "."
        + f" **c**, Questions single pass passes and the strategy fails (harmed, {fn.VERMILION}) or the "
        f"reverse (helped, blue). Bars, means over n = {nd * nd} pairing{'s' if nd > 1 else ''} of "
        f"draws. "
        f"**d**, Grey dots, questions; marks, pass rates at mean calls, open at score {THRESHOLDS[1]}. "
        + ("Intervals in Source Data and concept recall, not drawn. " if LEGEND_CONCEPT_RECALL else "")
        + f"{e_t}"
        f"**f**, Strategy minus single pass (percentage points) by core papers, draw 1; split rows' n in Source "
        f"Data. Thick frame, interval excludes 0{past}.\n")                # FIG3F O2: no grey-row clause


def legend_s5(stamp, draws, book):
    """Supplementary Figure 16's legend (fig3.md section 6), each count read from the rows drawn."""
    o = rows_of(book, S5_SHEET["a"], ORDER_KIND)
    n1, n2 = (sum(1 for r in o if r["question_type"] == g) for g in ("one", "many"))
    nd = len(draws)
    return (
        f"# Supplementary Figure 16, title and legend (draft)\n\n"
        f"Written by `scripts/S463_fig2_ranking.py rank` from the plotted numbers. Data stamp: {stamp}.\n\n"
        f"**Supplementary Figure 16 | Figure 3's pass tiles and flips at the relaxed threshold.** As Figure 3a and 3c, at "
        f"judge score 3 or more. **a**, The n = {n1 + n2} answerable questions by strategy (n = {n1} one-paper, "
        f"n = {n2} many-paper, an exploratory split), in Figure 3a's order; tile colour, draws passing of n = {nd}. "
        f"Right, pass rate (dot) with its two-sided 95% percentile interval over {N_BOOT:,} question resamples (bar). "
        f"**b**, Against single pass: {fn.VERMILION}, questions single pass passes and the strategy fails (harmed); blue, "
        f"the reverse (helped). Bars, means over n = {nd * nd} pairing{'s' if nd > 1 else ''} of draws; black dots, pairings"
        + (f"; grey dots, the strategy's own reruns (n = {nd * (nd - 1)} ordered pairs); band, single pass's reruns, lowest "
           f"to highest" if nd > 1 else "") + ".\n")


def caption_text(stamp, n_read, with_cr=False, command=None, vp_wait=None, with_e=False, with_person=False):
    ng = Counter(key_groups().values())
    na, nn, nq = ng["answerable"], ng["not_answerable"], sum(ng.values())
    return (f"# Source Data Fig. 3, caption\n\n"
            f"**Source Data Fig. 3 | Numerical values plotted in Figure 3.** Provisional: {n_read:,} of the "
            f"{PLANNED:,} answers read from their final-key row. Data stamp: {stamp}. One sheet per panel; the row_kind "
            f"column names each row's kind. The pass rate is the share of answers the judge scores 4 or more; 3 or more "
            f"is the relaxed threshold, given beside it (threshold column, 4 first). Sheet Fig. 3a, the {na} answerable "
            f"questions: rows '{ORDER_KIND}', the question ids in the plate's column order, one-paper then many-paper "
            f"(question_type), with their sort keys (draws passed summed over the six strategies at score 4 or more, then "
            f"at 3 or more); rows '{TILE_KIND}', per strategy and question at score 4 the draws passed and the draws "
            f"scored (the tile's colour); rows 'strategy', per row and threshold the pass rate on all {na} with its 95% "
            f"percentile interval over {N_BOOT:,} question resamples (seed {SEED}), the failed answers counted as fails, "
            f"the judge calls left out and the rate with the failed answers left out; rows '{GROUP_KIND}', the same on "
            f"the one-paper and the many-paper questions; neither is drawn in 3a, and column {DRAWN_IN} says where the "
            f"plate draws each rate (3d, without its interval); rows 'draw', each draw's rate (not "
            f"drawn); rows 'pair (unadjusted)', all {math.comb(len(CONFIGS), 2)} pairs of the six strategies: the difference in points with its "
            f"interval, the questions each side is higher on and the exact two-sided sign-flip P value, not adjusted; "
            f"rows 'outcome', the answer keys of each failed, unscored, stopped, returned and cut answer of the six "
            f"strategies, and of each failed or unscored answer of matched budget and Zhang RLM-10; rows "
            f"'{MARGIN_Q_KIND}', per row (the six strategies, matched budget, Zhang RLM-10) and answerable question "
            f"its clock time per answer less the wait for the local server (generation.latency_s less the calls' "
            f"waited_for_server_s; Zhang RLM-10, which waits for no local server, its wall_s), the mean over its draws "
            f"(the grey dot; the plate moves it up or down within its row only), and the same with the wait (not drawn); "
            f"rows '{MARGIN_KIND}', per row the mean over the questions (the black dot and its printed value) with its "
            f"95% interval (not drawn), and the mean with the wait (not drawn"
            + (f"; verified pass's is {vp_wait} s" if vp_wait else "") + ")"
            + (f"; rows '{CR_NOT_DRAWN}', concept recall on the {na} answerable questions (key v2.5, the loose matcher with "
               f"the question rule: a concept's words that also occur in its question are not counted, and a concept "
               f"made only of such words is left out; D181), not drawn. " if with_cr else ". ")
            + f"Sheet Fig. 3b, the {nn} {fn.OUT_OF_SCOPE_QUESTIONS} at refusal score {REFUSAL_T} or more: rows '{ORDER_KIND}' (sort "
            f"key the refused share summed over the six strategies), rows '{TILE_KIND}' (draws refused and draws scored), "
            f"rows 'refusal' (the margin's dot and the ends of its bar, with the one-sided 95% upper bound where the rate "
            f"is 0, the one-sided 95% lower bound where it is 100% and whether the interval has zero width), rows 'draw' "
            f"(not drawn) and 'pair (unadjusted)' as in Fig. 3a, then rows 'false premise' (passed of the answers, per "
            f"threshold and draw) and 'false premise question' (passes per question), not drawn"
            + (f"; rows '{PERSON_KIND}', for single pass and RLM-10, the answers of draw 1 that a person read blind "
               f"to strategy and judge score as refused, answered or partly (D223), 'partly' counted as refused "
               f"(D227): the person's refused count and share (the diamond), the judge's refused "
               f"count on the same answers (not drawn), their agreement, the 2x2 (both refused, person only, judge "
               f"only, neither), kappa (not defined when the judge gives every answer one category) and the S607 "
               f"file read with its sha256" if with_person else "")
            + f". Sheet Fig. 3c, Rule 4 at "
            f"score 4: rows '{FLIP_KIND}', harmed and helped as means over the draw pairings (the bars), the harmful share "
            f"of changed outcomes and the share of single pass's correct answers degraded with their intervals, the exact "
            f"two-sided sign-flip P value and the same-draw totals; rows '{PAIR_KIND}', per strategy and pairing the "
            f"questions harmed and helped; rows 'draw against the same draw' (not drawn); rows '{NOISE_KIND}', per ordered "
            f"pair of draws the questions that pass on one run and fail on another (not drawn here; Supplementary Figure "
            f"16b draws the same rows at score 3); verified pass without the answers whose verifier was not ok (not "
            f"drawn). Sheet "
            f"Fig. 3d: rows '{CQ_KIND}', per strategy and answerable question its question type, its model calls per "
            f"answer (the mean over its draws) and its share of draws passing at score 4 or more (the plate moves each dot "
            f"by at most a factor of exp(0.07) in calls and 4 points in share, so equal values stay visible); rows "
            f"'{GROUP_D_KIND}', per strategy and question group (all, one paper, many papers) the questions, the mean "
            f"of their model calls (the mark's x) and the pass rate at score 4 (the filled mark) and at 3 (the open "
            f"mark), as sheet Fig. 3a gives them, with their 95% intervals (not drawn); rows 'strategy (plotted)', the "
            f"mean calls and pass rate at score 4 on all {na} (group all's filled mark) with both intervals (not drawn), "
            f"the clock time, the clock time less the wait for the local server, the wait, the tokens and the model-call "
            f"time, per answer; the same on all {nq} questions (not drawn); RLM-10 over single pass; rows "
            f"'{MULT_KIND}', each strategy's ratios to single pass (ratio of means, and of medians for tokens; not "
            f"printed on the plate); row '{CROSS_KIND}', matched budget's calls and pass rate (the cross; its interval "
            f"not drawn). "
            + (f"Sheet Fig. 3e (S518, D195; the reference row D235), rows '{E3_KIND}': per source (the test, beside "
               f"it, then the reference, Gemini 3 Flash judged on key v2.5) and measure (one paper D_one, many papers "
               f"D_many, many-paper gain minus one-paper gain I), RLM-10 minus single pass at score {PRIMARY} in "
               f"points as S518 stored it, with its 95% interval (I's with each question type resampled apart), the "
               f"exact two-sided sign-flip P of D_one and D_many, the questions of each type, I's reading (not drawn; "
               f"of the three measures only I is drawn, D289), "
               f"and the S518 file read with its sha256. " if with_e else
               "Sheet Fig. 3e: empty, panel e (replication on other generators) not drawn yet. ")
            + f"Sheet Fig. 3f "
            f"(S522): rows 'cell', per block, core-paper size, strategy and question group the strategy minus single pass "
            f"in points at draw 1 (block 3, refusal), with its interval, its pairs, the sign and size printed and the "
            f"answers awaiting key v2.5; rows 'n', the questions of each cell. "
            + (f"Generated by `{command}` (rank on the frozen copies of S3's collect output, fig3_s6_inputs, G1's "
               f"generation records and findings/recompute/fig3e/).\n\n" if command else
               "Generated by `uv run --frozen python scripts/S463_fig2_ranking.py rank` from S3's collect output and "
               "G1's generation records.\n\n")
            + "Proposed Data Availability sentence: \"The source data for Figure 3 is in Supplementary Data 4.\"\n")   # D303: Data n + 1 (D302)


def caption_s5(stamp, n_read, command=None):
    return (f"# Supplementary Figure 16 data, caption\n\n"
            f"**Supplementary Figure 16 data | Numerical values plotted in Supplementary Figure 16.** Provisional: {n_read:,} "
            f"of the {PLANNED_S5:,} G1 answers read from their final-key row. Data stamp: {stamp}. Sheet {S5_SHEET['a']}: "
            f"rows '{ORDER_KIND}' as Figure 3a; rows '{TILE_KIND}', per strategy and question at score 3 the draws passed "
            f"and the draws scored; rows 'strategy', each strategy's pass rate at score 3 with its interval. Sheet "
            f"{S5_SHEET['b']}: Rule 4 at score 3, rows as sheet Fig. 3c of Figure 3's Source Data. "
            + (f"Generated by `{command}`.\n" if command else "Generated by `scripts/S463_fig2_ranking.py rank`.\n"))


def verifier_name(vp_lines, keys) -> str:
    """F3-04 O1 (rulings page 6 Nov): the verified-pass verifier as S457 names it (scripts/S457_fig2_panels.py:2423-2425):
    the local (ollama) models of the calls of each verified-pass answer of the draws read, each key's last line, read by
    S457.exp01_row, joined with " and "; gpt-oss:20b's date-fixed copy alone gets S457's note. ranking_report.md prints
    it (ranking.json does not)."""
    last = {r["answer_key"]: r for r in vp_lines if r.get("answer_key") in keys}
    vm = sorted({m for k, r in last.items() for m in S457.exp01_row(k, r, "verified_pass")["local_models"] if m})
    if not vm:
        return "none (no local model call in the verified-pass records read)"
    return " and ".join(vm) + (" (gpt-oss:20b with the date fixed, LOCK [date])"
                               if vm == ["gpt-oss:20b-date20261010"] else "")


def verifier_q78(vp_lines, cells, groups, draws) -> dict:
    """Rule 4, Q78 (LIST.md:286-289): chunk_verifier.verifier_status_report over the verified-pass records given (each
    key's last line, the G1R15 copy after K1's), restricted to the G1 answers of the draws read; when any is not ok,
    every reading again with those answers left out (their cells set aside), so Figure 3's verified-pass score is
    given with and without them."""
    rep = S457.verifier_report_fn()(vp_lines)
    keys = {c["key"] for c in cells.values()}
    not_ok = [x for x in rep["not_ok"] if x["answer_key"] in keys]
    no_ver = [k for k in rep["no_verification"] if k in keys]
    counts = Counter(x["status"] for x in not_ok)
    n_read = sum(1 for (c, q, d) in cells if c == "verified_pass")
    out = {"read": True, "n_read": n_read, "not_ok": not_ok, "no_verification": no_ver,
           "status_counts_read": dict(counts), "report_all_records": {k: rep[k] for k in ("n_verified_pass",
                                                                                          "status_counts")},
           "res_without": None}
    out["verifier"] = verifier_name(vp_lines, keys)
    if not_ok:
        drop = {x["answer_key"] for x in not_ok}
        cells2 = {k: ({**v, "kind": "set_aside"} if v["key"] in drop else v) for k, v in cells.items()}
        out["res_without"] = compute(cells2, groups, draws, True)
    return out


def record_text(obj, args) -> str:
    """A record as JSON, the folder the frozen sidecar recorded for the pull (rebuild's relocate) written as its frozen
    copy, so ranking.json and the provenance hold no machine folder (D155). rank's own results keep the recorded names."""
    t = json.dumps(obj, indent=1, default=str) + "\n"
    for k, v in (getattr(args, "relocate", None) or {}).items():
        t = t.replace(str(k).rstrip("/"), label(v))
    return t


OWNED = ("Figure 3*", "Source Data Fig. 3*", "figure3_numbers.json", "figure3_provenance.json", "legend_draft.md",
         "ranking.json", "ranking_report.md", "claims.md")
OWNED_S5 = ("Supplementary Figure 16*", "supplementary_figure16_numbers.json", "supplementary_figure16_provenance.json",
            "legend_draft.md")


def rank(args, *, out_dir: Path | None = None, quiet=False) -> dict:
    draws = sorted({int(x) for x in str(args.draws).split(",")})
    if not draws or any(d not in (1, 2, 3) for d in draws):
        raise Refused(f"--draws {args.draws}: draws are 1, 2, 3")
    collect = Path(args.collect).expanduser().resolve()
    out_dir = Path(out_dir or args.out or OUT).resolve()
    fixture = (collect.parent / "FIXTURE.txt").exists()
    if fixture and out_dir == OUT.resolve():
        raise Refused("this collect output is the fixture (FIXTURE.txt beside it): it is never written into "
                      f"{OUT.relative_to(ROOT)}; pass --out")
    if not args.answers:
        raise Refused("--answers is needed (K1's runs, then G1R15's): the stop reasons (Rule 10) and the verifier "
                      "status (Rule 4, Q78) come from the generation records judged")
    import lock_equiv                                       # D204: d66daa28 but for the second judge's machines
    if not lock_equiv.accepts(LOCK_TOML):
        raise Refused(f"experiments/LOCK.toml is {sha256_file(LOCK_TOML)[:8]}, not D88's {LOCK_WANT[:8]} "
                      f"({lock_equiv.why_not(LOCK_TOML.read_text())}): the judge and its digest checked against the rows come from it")
    S457.figure_lock_agreed()
    groups = key_groups()
    reruns = rerun_keys()
    answers, ans_inputs, vp_lines = read_answers([Path(x) for x in args.answers],
                                                 getattr(args, "answers_manifests", None))
    read = read_collect(collect, draws, groups, reruns, Path(args.replace_out) if args.replace_out else None, answers,
                        getattr(args, "relocate", None))
    jr = judge_rows(read, collect, groups, reruns, draws, getattr(args, "s6", None), answers)   # D186 (3)
    read["judge_rows"] = judge_rows_record(jr)
    read["groups"] = groups
    read["rows_read"] = len(read["cells"])
    rep = reproduce()
    res = compute(read["cells"], groups, draws, True)
    res_out = compute(read["cells"], groups, draws, False)        # Rule 10's sensitivity
    out_t = outcomes(read["cells"], groups)
    q78 = verifier_q78(vp_lines, read["cells"], groups, draws)
    cost = cost_summary(read["cells"], groups, draws)
    crx = None
    if getattr(args, "concept_recall", None):
        # D188, reproduce first (README.md:75-79): L3's loose reading on key v2.4, every row scored again from its
        # record, gives the committed v2.4 panel b (check_cr_anchor); only then is D181's reading read and drawn
        cr = read_concept_recall(Path(args.concept_recall), answers, groups, draws)
        lo = compute_cr(cr, groups, draws)
        anchored = check_cr_anchor(lo, cr, draws)
        rep.append(f"panel b, v2.4 anchor: {cr['gate']}; {cr['regenerated']:,} answerable concept-recall rows of L3 "
                   f"regenerated from the records read here (S471.score), each the answer S3 judged"
                   + (f"; {anchored}" if anchored else "; no committed v2.4 anchor applies to these inputs"))
        crd = read_concept_recall_d181(Path(getattr(args, "concept_recall_d181", None) or L3_D181), cr, groups,
                                       draws)
        crx = {"res": compute_cr(crd, groups, draws), "info": {k: v for k, v in crd.items() if k != "cells"},
               "anchor": {"reading": READING_TEXT["loose"], "reproduced": anchored, "gate": cr["gate"],
                          "written_utc": cr["written_utc"],
                          "read": {k: v for k, v in cr.items() if k not in CR_INFO_DROP},
                          "strategies": {c: dict(zip(("concept_recall_loose_pct", "ci95_lo_pct", "ci95_hi_pct",
                                                      "concept_recall_exact_pct"),
                                                     (r9(100 * lo[m]["summary"][c][f]) for m, f in
                                                      (("value", "rate"), ("value", "lo"), ("value", "hi"),
                                                       ("exact", "rate")))),
                                             answers_failed_scored_0=len(lo["failed"][c])) for c in CONFIGS}}}
        rep.append(f"panel b: {crd['gate']}")
    kinds = S511.questions()
    extra = read_extra(Path(args.extra), groups, draws, getattr(args, "g2_answers", None),
                       getattr(args, "g6_answers", None)) if getattr(args, "extra", None) else None
    fe = read_fig3e(args.fig3e) if getattr(args, "fig3e", None) else None
    if not args.no_plate and (extra is None or fe is None):
        raise Refused("a plate needs --extra (fig3_s6_inputs: G2 and G6) and --fig3e (S522's tables)")
    if extra is not None and getattr(args, "s511_results", None):
        rep.append(hold_g2_to_s511(extra, Path(args.s511_results), groups, draws, kinds))
    if fe is not None:
        rep += [f"panel f: {x}" for x in fe["reproduced"]]
    t2 = read_s518(args.s518) if getattr(args, "s518", None) else None   # 3e: S518's verdicts; without, its frame
    if t2 is not None:
        rep += t2["reproduced"]
    # D231, D306: 3b's diamonds, the person's refusal check; never on a fixture (its answers are not the ones read)
    person = None if fixture else read_person_check(getattr(args, "s607", None) or S607_SUMMARY, res, draws)
    if person is not None:
        rep.append(person["reproduced"])
    margin = clock_margin(read, extra, groups, draws)
    supp6 = getattr(args, "supp6", None) or (None if fixture else SUPP6_DIR)
    if extra is not None and supp6 is not None and draws == [1, 2, 3]:
        supp6 = supp6_workbook(Path(supp6))           # D218 (2): reproduce first, before anything is written
        rep.append(hold_margin_to_supp6(margin, supp6))
    else:
        supp6 = None
    book, order = sheets(res, res_out, out_t, draws, read, cost, q78, crx, extra, fe, kinds, margin, t2, person)
    side = read["side"]
    when = (side.get("_provenance") or {}).get("at")
    dtext = dtext_of(draws)
    nf = sum(len(v) for c in CONFIGS for v in out_t[c]["failed"].values())
    k1 = read["judge_rows"]["answers_read"] - read["judge_rows"]["awaiting_s6_read"]   # read from a final-key row
    kx = extra["final_key"] if extra else 0
    kg = fe["tables"]["g4_answers_final_key"] if fe else 0
    k_all = k1 + kx + kg
    head = f"{'PROVISIONAL FIXTURE, NOT DATA' if fixture else 'PROVISIONAL'}: {dtext} (D82, D88), "
    tail = (f"{read['rows_read'] - nf:,} G1 answers judged ({JUDGE}, plain call), collect of {when}, run_sha256 "
            f"{str(read['run_sha256'])[:12]}")
    stamp = (head + f"{k_all:,} of {PLANNED:,} answers read from their final-key row (G1 {k1:,}, G2 and G6 {kx:,}, G4 "
             f"{kg:,}), " + tail
             + (f"; concept recall: D181's reading on key v2.5, L3_d181 rows of {crx['info']['written_utc']}" if crx
                else ""))
    stamp5 = head + f"{k1:,} of {PLANNED_S5:,} G1 answers read from their final-key row, " + tail
    tag = f" (provisional, {k_all} of {PLANNED})"
    tag5 = f" (provisional, {k1} of {PLANNED_S5})"
    s4 = res["answerable"][4]["summary"]
    if not quiet:
        print(f"reproduce: {'; '.join(rep)}")
        print(stamp)
        print(f"{'strategy':14s} {'pass>=4':>8s} {'95% interval':>14s} {'pass>=3':>8s} {'refused>=3':>10s} "
              f"{'false premise>=3':>17s} {'failed':>6s} {'no score':>8s}")
        for c in order:
            s3 = res["answerable"][3]["summary"][c]
            rf = res["refusal"][REFUSAL_T]["summary"][c]
            f3 = res["false_premise"][3][c]
            print(f"{LABEL[c]:14s} {pct(s4[c]['rate']):>7s}% {pct(s4[c]['lo']):>6s} to {pct(s4[c]['hi']):>5s} "
                  f"{pct(s3['rate']):>7s}% {pct(rf['rate']):>9s}% {f3['passed']:>8d} of {f3['answers']:<5d} "
                  f"{sum(len(v) for v in out_t[c]['failed'].values()):>6d} "
                  f"{sum(len(v) for v in out_t[c]['unscored'].values()):>8d}")
        print("verdicts (score 4; 3): " + "; ".join(f"{cl[0]} {vtxt(res['verdicts'][4][cl[0]])}; "
                                                   f"{vtxt(res['verdicts'][3][cl[0]])}" for cl in CLAIMS))
        print(f"verifier status (Rule 4, Q78): {len(q78['not_ok'])} of {q78['n_read']} verified-pass answers read not "
              f"ok {q78['status_counts_read']}")
        print(f"judge rows (D186 (3)): {read['judge_rows']['status']}")
    # everything is written into a staging folder beside --out first; only when every file is written are the
    # earlier S463 files of --out removed and the new ones moved in (review of 18 October, defect 8): a refusal or
    # a failed plate leaves --out as it was, and no file of an earlier reading stays beside a new one
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out5 = Path(getattr(args, "out_s5", None) or out_dir.parent / OUT_S5_NAME).resolve()
    stage = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.stage-", dir=out_dir.parent))
    stage5 = stage / "s5"
    names5, drawn5 = [], None
    try:
        write_report(stage / "ranking_report.md", res, res_out, read, out_t, draws, stamp, order,
                     collect if fixture else collect.name, q78, cost, crx)
        (stage / "claims.md").write_text(claims_md(res, read, draws, stamp, cost, crx))
        tr = trace(res, read, out_t)
        jres = {"stamp": stamp, "draws": draws, "reproduced": rep,
                "what": "every number of the ranking with the answer keys it is counted from (S463 rank)",
                "read": {k: read[k] for k in ("rows", "rows_read", "rows_other_draws", "run_sha256", "lock_sha256",
                                             "replace_out", "reruns_read", "rows_from_replace", "answers_joined",
                                             "units")},
                "judge_rows": read["judge_rows"], "extra": None if extra is None else extra["info"],
                "sheets": book,
                "rule6": {str(t): res["rule6"][t] for t in THRESHOLDS},
                "rule6_refusal": res["refusal"][REFUSAL_T]["rule6"],
                "verdicts": {str(t): res["verdicts"][t] for t in THRESHOLDS},
                "verdicts_failures_left_out": {str(t): res_out["verdicts"][t] for t in THRESHOLDS},
                "verifier_q78": {k: v for k, v in q78.items() if k not in ("res_without", "verifier")},
                "verdicts_without_verifier_not_ok": None if q78["res_without"] is None else
                {str(t): q78["res_without"]["verdicts"][t] for t in THRESHOLDS},
                "verified_pass_without_verifier_not_ok": None if q78["res_without"] is None else {
                    "pass_rate_4": q78["res_without"]["answerable"][4]["summary"]["verified_pass"]["rate"],
                    "pass_rate_3": q78["res_without"]["answerable"][3]["summary"]["verified_pass"]["rate"],
                    "refused_3": q78["res_without"]["refusal"][REFUSAL_T]["summary"]["verified_pass"]["rate"]},
                "cost": cost, "claims": {cl[0]: cl[1] for cl in CLAIMS}, "outcomes": out_t, "keys": tr,
                "concept_recall": None if crx is None else {
                    "read": crx["info"], "rule6": crx["res"]["value"]["rule6"],
                    "failed_scored_0": crx["res"]["failed"], "anchor_v24_loose": crx["anchor"]}}
        (stage / "ranking.json").write_text(record_text(jres, args))
        names = ["ranking.json", "ranking_report.md", "claims.md"]
        if not args.no_plate:
            paths = {x: stage / f"Figure 3{tag}.{x}" for x in ("pdf", "svg", "png")}
            sheet_list = [(nm, *table(rows)) for nm, rows in book.items() if nm.startswith("Fig. 3")]
            sd = stage / f"Source Data Fig. 3{tag}.xlsx"
            S457.write_source_data(sheet_list, sd)          # first: check_drawn holds the plate to it as written
            FR.deterministic_xlsx(sd)                       # D155: no write time; every cell as written
            W, H, printed, drawn = draw(book, paths, sd, len(draws))
            FR.check_pdf_deterministic(paths["pdf"])        # D155: S457.finish_plate saves no date; refuse one
            FR.check_svg_deterministic(paths["svg"])
            if not quiet:
                print(f"check_drawn: {drawn['summary']}")
            (stage / "figure3_numbers.json").write_text(json.dumps(
                {"stamp": stamp, "what": "every number the plate draws, sheet by sheet as Source Data Fig. 3 holds "
                 "them (S448 R8 compares the workbook with this file)",
                 "sheets": {nm: {"columns": c, "rows": r} for nm, c, r in sheet_list}, "printed": printed},
                indent=1, default=str) + "\n")
            (stage / "legend_draft.md").write_text(legend_text(res, read, draws, stamp, out_t, cost, q78, crx, extra,
                                                               book, fe))
            capf = stage / f"Source Data Fig. 3 caption{tag}.md"
            vpw = next((S457.half_up(r["clock_s_mean_with_wait"], 0) for r in rows_of(book, "Fig. 3a", MARGIN_KIND)
                        if r["strategy"] == "verified_pass"), None)
            capf.write_text(caption_text(stamp, k_all, crx is not None, getattr(args, "command", None), vpw,
                                         t2 is not None, person is not None))
            names += [x.name for x in paths.values()] + [sd.name, capf.name, "figure3_numbers.json", "legend_draft.md"]
            s6_here = [] if not jr["sources"]["S6G1"]["present"] else [
                Path(getattr(args, "s6", None) or Path(read["replace_out_here"]).parent) / n
                for n in ("out_s6_g1", "out_s6_g1r15")]
            outs_read = sorted({q for o in [*read["outs_here"], *s6_here]
                                for pat in ("start_*.json", "judge/*/judge_passages*.jsonl") for q in Path(o).glob(pat)})
            ex_files = [] if extra is None else sorted(
                q for pat in ("*_collect.jsonl", "*_collect.jsonl.json", "out*/start_*.json",
                              "out*/judge/*/judge_passages*.jsonl") for q in Path(args.extra).glob(pat))
            inputs = {label(collect): sha256_file(collect),
                      label(collect.with_name(collect.name + ".json")): sha256_file(collect.with_name(collect.name
                                                                                                     + ".json")),
                      **{label(q): sha256_file(q) for q in outs_read},
                      **{label(k): v for k, v in ans_inputs.items()},
                      **{label(k): sha256_file(k) for k in getattr(args, "extra_inputs", [])},
                      **{label(q): sha256_file(q) for q in ex_files},
                      **({} if fe is None else {label(q): sha256_file(q) for q in fe["paths"]}),
                      **({} if t2 is None else {label(q): sha256_file(q) for q in t2["paths"]}),
                      **({} if person is None else {label(person["path"]): person["sha256"]}),
                      **({} if t2 is None else {"scripts/S518_split_confirmation.py":
                                                sha256_file(ROOT / "scripts/S518_split_confirmation.py")}),
                      **({} if extra is None else {label(extra["records"]): extra["records_sha256"],
                                                   label(extra["g6_records"]): extra["g6_records_sha256"]}),
                      **({} if extra is None or not extra.get("g13") else
                         {**extra["g13"]["sha256"], "scripts/g13_merge.py": sha256_file(ROOT / "scripts/g13_merge.py")}),
                      **({} if supp6 is None else {label(supp6): sha256_file(supp6)}),
                      **({} if not getattr(args, "s511_results", None) else
                         {label(args.s511_results): sha256_file(args.s511_results)}),
                      "scripts/house_style.py": sha256_file(ROOT / "scripts/house_style.py"),
                      "scripts/figure_names.py": sha256_file(ROOT / "scripts/figure_names.py"),
                      "scripts/S511_g2_matched_budget.py": sha256_file(ROOT / "scripts/S511_g2_matched_budget.py"),
                      str(RERUN_SH.relative_to(ROOT)): sha256_file(RERUN_SH),
                      str(S04A.relative_to(ROOT)): sha256_file(S04A),
                      str(LOCK_TOML.relative_to(ROOT)): sha256_file(LOCK_TOML),
                      str(S457.FIGURE_LOCK.relative_to(ROOT)): sha256_file(S457.FIGURE_LOCK),
                      "scripts/S457_fig2_panels.py": sha256_file(ROOT / "scripts/S457_fig2_panels.py"),
                      "scripts/judge_rows_v25.py": sha256_file(ROOT / "scripts/judge_rows_v25.py"),
                      **({} if crx is None else {
                          crx["anchor"]["read"]["path"]: crx["anchor"]["read"]["sha256"],
                          crx["anchor"]["read"]["header"]: crx["anchor"]["read"]["header_sha256"],
                          crx["info"]["path"]: crx["info"]["sha256"], crx["info"]["header"]: crx["info"]["header_sha256"],
                          "scripts/S471_l3_concept_recall.py": sha256_file(ROOT / "scripts/S471_l3_concept_recall.py"),
                          "scripts/concept_match_loose.py": sha256_file(ROOT / "scripts/concept_match_loose.py"),
                          "scripts/turn_limit_note.py": sha256_file(ROOT / "scripts/turn_limit_note.py")})}
            prov = {"provenance": {"script": "scripts/S463_fig2_ranking.py", "script_sha256": sha256_file(Path(__file__)),
                                   "command": getattr(args, "command", None)
                                   or "uv run --frozen python scripts/S463_fig2_ranking.py " + " ".join(sys.argv[1:]),
                                   "python": platform.python_version(),
                                   "deterministic": "D155: no build time and no repository HEAD are recorded; the "
                                                    "script's and every input's sha256 identify the build",
                                   "inputs_sha256": inputs, "model_calls": 0},
                    "stamp": stamp, "reproduced": rep, "page_mm": [W, H], "collect_sidecar": side,
                    "check_drawn": drawn["summary"],
                    "units": read["units"], "judge_rows": read["judge_rows"],
                    "figure_lock": {"path": str(S457.FIGURE_LOCK.relative_to(ROOT)),
                                    "sha256": sha256_file(S457.FIGURE_LOCK), "status": S457.FLOCK.get("status")},
                    "files": {n: sha256_file(stage / n) for n in names}}
            (stage / "figure3_provenance.json").write_text(record_text(prov, args))
            names.append("figure3_provenance.json")
            # Supplementary Figure 16, the same rows at score 3
            stage5.mkdir()
            sh5 = [(nm, *table(book[nm])) for nm in S5_SHEET.values()]
            sd5 = stage5 / f"Supplementary Figure 16 data{tag5}.xlsx"
            S457.write_source_data(sh5, sd5)
            FR.deterministic_xlsx(sd5)
            p5 = {x: stage5 / f"Supplementary Figure 16{tag5}.{x}" for x in ("pdf", "svg", "png")}
            W5, H5, printed5, drawn5 = draw_s5(book, p5, sd5, len(draws))
            FR.check_pdf_deterministic(p5["pdf"])
            FR.check_svg_deterministic(p5["svg"])
            (stage5 / "supplementary_figure16_numbers.json").write_text(json.dumps(
                {"stamp": stamp5, "what": "every number the plate draws, sheet by sheet as the data workbook holds them",
                 "sheets": {nm: {"columns": c, "rows": r} for nm, c, r in sh5}, "printed": printed5},
                indent=1, default=str) + "\n")
            (stage5 / "legend_draft.md").write_text(legend_s5(stamp5, draws, book))
            cap5 = stage5 / f"Supplementary Figure 16 data caption{tag5}.md"
            cap5.write_text(caption_s5(stamp5, k1, getattr(args, "command", None)))
            names5 = [x.name for x in p5.values()] + [sd5.name, cap5.name, "supplementary_figure16_numbers.json",
                                                      "legend_draft.md"]
            prov5 = {"provenance": {**prov["provenance"], "inputs_sha256": inputs}, "stamp": stamp5,
                     "reproduced": rep, "page_mm": [W5, H5], "check_drawn": drawn5["summary"],
                     "judge_rows": read["judge_rows"],
                     "figure_lock": prov["figure_lock"], "files": {n: sha256_file(stage5 / n) for n in names5}}
            (stage5 / "supplementary_figure16_provenance.json").write_text(record_text(prov5, args))
            names5.append("supplementary_figure16_provenance.json")
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    out_dir.mkdir(parents=True, exist_ok=True)
    for pat in OWNED:
        for old in out_dir.glob(pat):
            old.unlink()
    for n in names:
        (stage / n).replace(out_dir / n)
    # D302 (Valerio, 7 Nov, "Q1: drop them"): Supplementary Figure 16 (score 3) is drawn and checked in the staging
    # folder but no longer written, except to a folder named with --out-s5 or beside a fixture's plate (the selftest)
    if names5 and (fixture or getattr(args, "out_s5", None)):
        out5.mkdir(parents=True, exist_ok=True)
        for pat in OWNED_S5:
            for old in out5.glob(pat):
                old.unlink()
        for n in names5:
            (stage5 / n).replace(out5 / n)
    shutil.rmtree(stage, ignore_errors=True)
    if not quiet:
        print(f"wrote {', '.join(names)} into {out_dir}")
    return {"res": res, "res_out": res_out, "read": read, "out_t": out_t, "out_dir": out_dir, "stamp": stamp,
            "q78": q78, "cost": cost, "book": book, "drawn": None if args.no_plate else drawn, "crx": crx,
            "extra": extra, "drawn_s5": drawn5, "out_s5": out5}


# ---------------------------------------------------------------------------------------------------------------
# rebuild: the committed plate again, from the frozen copies only (D155)
# ---------------------------------------------------------------------------------------------------------------
REBUILD_CMD = "uv run --frozen python scripts/S463_fig2_ranking.py rebuild"
CONCEPT_RECALL = ROOT / "findings" / "recompute" / "L3" / "concept_recall.jsonl"
PROVENANCE = OUT / "figure3_provenance.json"


def rebuild(args) -> dict:
    """D155: rank --draws 1,2,3 with panel b on the frozen inputs only, checked against the committed plate's record.

    Reads (fig_repro.frozen(), each file checked: a committed set against frozen_inputs/SHA256SUMS, a tar's files
    against its committed sha256 and their extraction record):
      collect   frozen fig2 g1_collect.jsonl and its sidecar (findings/recompute/fig2_inputs/, A1); the outs the
                sidecar records (the 23 October pull's out/ and out_g1r15/) are read from fig2_inputs/out and
                fig2_inputs/out_g1r15 (read_collect's relocate), every output keeping the recorded names
      answers   K1's runs, frozen k1_inputs_runs.tar (A1b), checked against its committed members list in place of
                ~/k1_inputs/MANIFEST.sha256 (the tar holds runs/ only); then G1R15's, frozen fig2_g1r15_inputs.tar
                (A1), with its own MANIFEST.sha256
      extra     G1's, G2's and G6's judge rows on key v2.5, frozen fig3_s6 (findings/recompute/fig3_s6_inputs/, S528), and
                G2's answers, the copy S3 judged in frozen s457_mirror_20261022; panel e reads FIG3E (S522) and the plate
                holds G2 to S511_RESULTS (S511)
      panel b   D188: findings/recompute/L3_d181/ (committed, S471 --d181; both files pinned, L3_D181_SHA256), drawn
                after findings/recompute/L3/concept_recall.jsonl (committed, S471), the v2.4 anchor it is held to, has
                reproduced the committed v2.4 panel b (check_cr_anchor); S471's gate (S432's 107 values) reads
                the deposit's exp00_phase2_latest.json from frozen upstream_inputs (S471.PHASE2 set to it; S471 checks
                its sha256 against S432's record) instead of the sibling checkout scripts/machine.py finds, and S432's
                output from the frozen fig2_repo_inputs/S432_selection_concept_recall_v24.json (S471.S432_JSON,
                checked against SHA256SUMS), recorded among the inputs
    Before anything is written, every frozen input the committed figure3_provenance.json records must have that
    sha256 (fig_repro.check_recorded; a record written before D155 names the scratch and home folders, translated by
    frozen_inputs/MANIFEST.json, fig_repro.recorded_label). --out (default the plate's folder) is where the files go;
    the committed record is read from the plate's folder either way, so a rebuild into a temporary folder is checked
    the same way and can be compared file by file with the committed plate."""
    if not PROVENANCE.exists():
        raise Refused(f"{PROVENANCE.relative_to(ROOT)} is missing: there is no committed plate to rebuild")
    recorded = json.loads(PROVENANCE.read_text())["provenance"]["inputs_sha256"]
    fig2 = FR.check_committed(FR.frozen("fig2"))
    collect = fig2 / "g1_collect.jsonl"
    side = json.loads(collect.with_name(collect.name + ".json").read_text())
    outs = (side.get("_provenance") or {}).get("inputs") or []
    if sorted(Path(o).name for o in outs) != ["out", "out_g1r15"] or len({str(Path(o).parent) for o in outs}) != 1:
        raise Refused(f"the frozen sidecar records the outs {outs}, not one pull's out/ and out_g1r15/")
    relocate = {str(Path(outs[0]).parent): str(fig2)}
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs")
    g1r15 = FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs")
    members = FR.RECOMPUTE / "frozen_inputs" / "members" / "k1_inputs_runs.sha256"
    k1_man = {}
    for ln in members.read_text().splitlines():
        if ln.strip():
            h, n = ln.split(None, 1)
            k1_man["runs/" + n.strip().split("/", 1)[1]] = h
    phase2 = FR.check_committed(FR.frozen("upstream", "publication/results/exp00_phase2_latest.json"))
    s471_module().PHASE2 = phase2                   # S471's gate reads its module's PHASE2 when it runs
    s432 = FR.check_committed(FR.frozen("fig2_repo", "S432_selection_concept_recall_v24.json"))
    if s432 != Path(s471_module().S432_JSON).resolve():
        raise Refused(f"S471 reads S432's output from {s471_module().S432_JSON}, not the frozen {s432}")
    s6 = FR.frozen("fig3_s6")                       # checked against its own SHA256SUMS
    g2_answers = FR.frozen("s457_mirror_20261022", "s457_mirror_20261022/matched_budget") / "answers.jsonl"   # read_extra's
    g6_answers = FR.check_committed(FR.frozen(G6_SET)) / G6_RUN10 / "answers.jsonl"   # read_g6_clock's (D218 (2))
    ns = argparse.Namespace(collect=str(collect), draws="1,2,3", answers=[str(k1), str(g1r15 / "runs")],
                            replace_out=None, out=args.out, no_plate=False, concept_recall=str(CONCEPT_RECALL),
                            concept_recall_d181=str(L3_D181), s6=str(s6), extra=str(s6), fig3e=str(FIG3E),
                            s518=str(S518_DIR),   # 3e, S518's committed verdicts (D195, D218 (3); Valerio 5 Nov: "where is panel e?")
                            g2_answers=None, s511_results=str(S511_RESULTS), out_s5=getattr(args, "out_s5", None),
                            answers_manifests={str(k1): k1_man}, relocate=relocate,
                            extra_inputs=[members, phase2, s432], command=REBUILD_CMD)
    # the inputs this build reads, by the names the provenance file gives them, checked against the committed record
    # before rank reads anything (rank computes them again for the new record; they must agree)
    now = {FR.frozen_label(f): FR.sha256_file(f) for f in [collect, collect.with_name(collect.name + ".json"),
                                                           members, phase2, s432,
                                                           *sorted((fig2 / "out").rglob("*")),
                                                           *sorted((fig2 / "out_g1r15").rglob("*")),
                                                           *sorted(k1.rglob("answers.jsonl")),
                                                           *sorted((g1r15 / "runs").rglob("answers.jsonl")),
                                                           *sorted(s6.rglob("*")), g2_answers, g6_answers]
           if f.is_file()}
    seen = FR.check_recorded(now, recorded, FR.recorded_label)
    print(f"frozen inputs: {seen['compared']} recorded by the committed plate, each equal; "
          f"{len(seen['not_recorded_before'])} read and not recorded before")
    return rank(ns)


# ---------------------------------------------------------------------------------------------------------------
# pull: read-only copies from the Studio, then collect on them
# ---------------------------------------------------------------------------------------------------------------
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def cut_partial(p: Path) -> int:
    """A copy of a file still being appended: cut after its last whole line (snap's rule). Returns bytes cut."""
    b = p.read_bytes()
    if not b or b.endswith(b"\n"):
        return 0
    keep = b.rfind(b"\n") + 1
    p.write_bytes(b[:keep])
    return len(b) - keep


# The remote half of pull, sent on ssh's stdin (never on a command line). It writes one tar stream to stdout: the S3
# clone's HEAD as HEAD.txt; under out/ and out_g1r15/ each judge/<run>/ folder's three judge files and the out's
# start_*.json; under g1r15_inputs/ the answers files, MANIFEST.sha256 and keys.txt of ~/s3_inputs/g1r15 (followed if
# a link). Read only: it opens files for reading and runs no command: the clone's HEAD is read from its .git files
# (_head: HEAD, a loose ref, a worktree's commondir, packed-refs), never by git, which the 23 October guards forbid
# on the Studio (inventory A8: figs_1023/fig5/refresh_pull.py patched this at run time for Figure 5's pull of 23
# October; ported here, 26 October).
PULL_SH = r"""set -e
cd "$HOME/__CLONE__"
python3 - <<'PY'
import glob, io, os, sys, tarfile
src = "findings/recompute/S3_runs"
keep = ("judge_passages.jsonl", "judge_passages_headers.jsonl", "judge_passages_recheck.jsonl")
def _head():
    g = ".git"
    if os.path.isfile(g):
        g = open(g).read().split("gitdir:", 1)[1].strip()
    h = open(os.path.join(g, "HEAD")).read().strip()
    if h.startswith("ref:"):
        ref = h.split(None, 1)[1]
        p = os.path.join(g, ref)
        if os.path.isfile(p):
            return open(p).read().strip()[:7]
        cg = g
        cd = os.path.join(g, "commondir")
        if os.path.isfile(cd):
            cg = os.path.normpath(os.path.join(g, open(cd).read().strip()))
            p = os.path.join(cg, ref)
            if os.path.isfile(p):
                return open(p).read().strip()[:7]
        for line in open(os.path.join(cg, "packed-refs")):
            if line.strip().endswith(" " + ref):
                return line.split()[0][:7]
        return "unknown"
    return h[:7]
head = _head()
tf = tarfile.open(fileobj=sys.stdout.buffer, mode="w|", dereference=True)
b = (head + "\n").encode()
ti = tarfile.TarInfo("HEAD.txt"); ti.size = len(b)
tf.addfile(ti, io.BytesIO(b))
for o in ("out", "out_g1r15"):
    for f in sorted(glob.glob(f"{src}/{o}/judge/*/*")):
        if os.path.basename(f) in keep and os.path.isfile(f):
            tf.add(f, arcname=os.path.relpath(f, src), recursive=False)
    for f in sorted(glob.glob(f"{src}/{o}/start_*.json")):
        tf.add(f, arcname=os.path.relpath(f, src), recursive=False)
g = os.path.realpath(os.path.expanduser("~/s3_inputs/g1r15"))
for dp, dn, fn in os.walk(g):
    dn.sort()
    for n in sorted(fn):
        p = os.path.join(dp, n)
        rel = os.path.relpath(p, g)
        if n == "answers.jsonl" or rel in ("MANIFEST.sha256", "keys.txt"):
            tf.add(p, arcname="g1r15_inputs/" + rel, recursive=False)
tf.close()
PY
"""


def pull(args):
    to = Path(args.to).expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    to.mkdir(parents=True, exist_ok=True)
    src = f"{S3_CLONE}/findings/recompute/S3_runs"
    r = subprocess.run(SSH + [STUDIO, "bash", "-s"], input=PULL_SH.replace("__CLONE__", S3_CLONE).encode(),
                       capture_output=True)
    if r.returncode:
        raise Refused(f"pull from {STUDIO}: exit {r.returncode}: {r.stderr.decode(errors='replace').strip()[:300]}")
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as tf:
        names = tf.getnames()
        bad = [n for n in names if n != "HEAD.txt" and not n.startswith(("out/", "out_g1r15/", "g1r15_inputs/"))]
        if bad:
            raise Refused(f"pull: unexpected members in the stream: {bad[:3]}")
        tf.extractall(to, filter="data")
    head = (to / "HEAD.txt").read_text().strip()
    (to / "HEAD.txt").unlink()
    cut = {}
    for o in ("out", "out_g1r15"):
        (to / o).mkdir(exist_ok=True)
        for f in sorted((to / o).glob("judge/*/judge_passages*.jsonl")):
            n = cut_partial(f)
            if n:
                cut[str(f.relative_to(to))] = n
    g = to / "g1r15_inputs"
    read_answers([g / "runs"])                          # each answers file against its MANIFEST.sha256 line
    keys = sorted(x for x in (g / "keys.txt").read_text().splitlines() if x.strip())
    if keys != sorted(rerun_keys()):
        raise Refused(f"{g / 'keys.txt'} is not rerun_d89.sh's 15 keys")
    rows = {str(f.relative_to(to)): sum(1 for x in f.read_text().splitlines() if x.strip())
            for f in sorted(to.glob("out*/judge/*/judge_passages.jsonl"))}
    (to / "PULL.json").write_text(json.dumps({"from": f"{STUDIO}:~/{src}", "s3_clone_head": head,
                                              "s3_clone_head_how": "read from the clone's .git files (no git command "
                                                                   "on the Studio, 23 October guards)",
                                              "pulled_utc": S457.utc_now(), "rows": rows,
                                              "bytes_cut_after_the_last_whole_line": cut}, indent=1) + "\n")
    dest = to / "g1_collect.jsonl"
    c = run([sys.executable, str(GUARD), "collect", "--out", str(to / "out"), "--replace", str(to / "out_g1r15"),
             "--set", "G1", "--dest", str(dest)], cwd=ROOT)
    print((c.stdout + c.stderr).strip())
    if c.returncode:
        raise Refused(f"collect refused (exit {c.returncode})")
    print(f"pulled from {STUDIO} (S3 clone at {head}): {sum(rows.values())} judge rows in {len(rows)} files"
          f"{'; cut a partial last line in ' + str(len(cut)) + ' files' if cut else ''}; collect into {dest}")
    print("next: uv run --frozen python scripts/S463_fig2_ranking.py rank --collect "
          f"{dest} --draws 1 --answers <K1's runs: the frozen k1_inputs_runs.tar extracted, with its MANIFEST.sha256 "
          f"beside it> --answers {g / 'runs'}")


# ---------------------------------------------------------------------------------------------------------------
# fixture: a fake S3 output of the real shape (NOT DATA)
# ---------------------------------------------------------------------------------------------------------------
FAKE_LOCK = LOCK_WANT


def fake_header(kind: str = "v24") -> dict:
    """A judge header as judge_passages run (kind "v24") or S512 run in its default mode (kind "s6") writes one, on the
    real lock and judge call, so judge_rows_v25 recomputes its run_sha256 from its own fields (D186 (3))."""
    from experiments.runner.lock import load as load_lock
    lock = load_lock()
    call = lock.ollama(JUDGE, role="judge")
    JP = judge_module()
    h = {"model": JUDGE, "model_digest": JUDGE_DIGEST, "lock_sha256": lock.sha256, "options": call.options,
         "fields": call.fields, "system_prompt_sha256": call.system and JP.sha(call.system), "variants": "a"}
    if kind == "v24":
        return dict(h, code=JP.code_identity(), run_sha256=JP.run_identity(lock, call))
    S512 = JR.S512
    return dict(h, code=S512.code_identity(), run_sha256=S512.run_identity(lock, call, "changed"),
                key_version=S512.KEY_VERSION, check={"kind": "s6_check"},
                questions={"changed": S512.N_CHANGED, "sha256": S512.CHANGED_SHA256})


_FAKE_RUN: dict = {}


def fake_run_sha(kind: str = "v24") -> str:
    """The fixture rows' run_sha256: fake_header's (judge_passages.run_identity, or S512.run_identity for "s6")."""
    if kind not in _FAKE_RUN:
        _FAKE_RUN[kind] = fake_header(kind)["run_sha256"]
    return _FAKE_RUN[kind]


def planned(c, q, d, groups, idx):
    """The fixture's outcome of (strategy, question, draw): ("scored", score, call status), ("failed", stop reason,
    call status) or ("unscored", judge status, None); call status is a Gemini call's status (None: every call ok).
    Draw 1 is built so that single pass against verified pass gives S04a's tables: at score 3, 15 questions only
    single pass passes and 4 only verified pass passes; at score 4, 15 and 3."""
    g, i = groups[q], idx[q]
    if d == 1 and c == "rlm_5" and g == "answerable" and i == 0:
        return ("failed", "max_turns_empty", None)                 # an empty answer: a fail (Rule 10)
    if d == 1 and c == "rlm_10" and g == "answerable" and i == 1:
        return ("unscored", "error", None)                         # a failed judge call: left out, counted
    if d == 1 and c == "multi_hop" and g == "not_answerable" and i == 25:
        return ("failed", "final_answer", "blocked")               # stopped by Google, no text: a fail (D89)
    if d == 1 and c == "rlm_20" and g == "false_premise" and i == 9:
        return ("failed", "final", "recitation")                   # a recitation stop with no text: a fail
    if (c, q, d) == ("verified_pass", "19_hpai_canada_TE3", 3):
        return ("failed", "ok", "blocked")                         # a rerun whose new version failed again
    call = None
    if d == 1 and c == "single_pass" and g == "answerable" and i == 3:
        call = "recitation"                                        # a recitation stop that kept its text (D90 Q1)
    if d == 1 and c == "rlm_10" and g == "answerable" and i == 5:
        call = "malformed_function_call"                           # returned with what it held (D90 Q2)
    if g == "answerable":
        s = {"single_pass": 4 if i < 65 else 2,
             "verified_pass": 4 if i < 50 or 65 <= i < 68 else (3 if i == 68 else 2),
             "multi_hop": 3 if i < 60 else 1, "rlm_5": 5 if i < 70 else 1, "rlm_10": 5 if i < 75 else 2,
             "rlm_20": 4 if i < 72 else 2}[c]
    elif g == "not_answerable":
        s = {"single_pass": 5 if i < 30 else 1, "verified_pass": 4 if i < 35 else 1, "multi_hop": 3 if i < 20 else 1,
             "rlm_5": 1, "rlm_10": 5 if i < 10 else 1, "rlm_20": 5}[c]
    else:
        s = {"single_pass": 4 if i < 7 else 1, "verified_pass": 4 if i < 5 else 3, "multi_hop": 2,
             "rlm_5": 5 if i < 9 else 1, "rlm_10": 3, "rlm_20": 4 if i < 8 else 2}[c]
    if d > 1 and int(hashlib.sha256(f"{c}|{q}|{d}".encode()).hexdigest(), 16) % 4 == 0:
        s = 1 if s >= 3 else 5                                     # draws 2 and 3 differ from draw 1 in a quarter
    return ("scored", s, call)


FIXTURE_WAIT = 7.0                                      # the fixture verifier call's wait for the local server (s)


def fixture_calls(c, i, d):
    """The fixture's model calls of one answer (each 3.0 s): single pass 1, verified pass 2, multi-hop 1 to 3, the
    RLMs 4 + (i + d) mod (cap / 5 + 2), so each question's mean over its draws differs from its draw-1 value."""
    if c == "single_pass":
        return 1
    if c == "verified_pass":
        return 2
    if c == "multi_hop":
        return 1 + i % 3
    return 4 + (i + d) % ({"rlm_5": 5, "rlm_10": 10, "rlm_20": 20}[c] // 5 + 2)


def verifier_status(c, q, d, groups, idx):
    """The fixture's verifier status of a verified-pass answer (Rule 4, Q78): two not ok on draw 1, one answerable
    that passes and one not-answerable that is not refused; the rest ok."""
    if c != "verified_pass":
        return None
    g, i = groups[q], idx[q]
    if d == 1 and g == "answerable" and i == 10:
        return "empty"
    if d == 1 and g == "not_answerable" and i == 36:
        return "unparsed"
    return "ok"


def fake_row(c, q, d, groups, outcome, version, judged_on="v24"):
    """A judge row as judge_passages.py writes one in phase 1 or 2 ((b) deferred or not applicable), or, judged_on
    "s6", as S512 writes one on key v2.5 (its key_hash and key_version). The judge's dimensions get different scores
    (correctness s, completeness 6 - s; refusal_accuracy s, hallucination_avoidance 6 - s), so reading the wrong
    dimension changes every rate (review of 18 October, defect 7). key_hash is S373's formula on the key the row
    names, so judge_rows_v25 accepts the row (D186 (3))."""
    key = f"{INDEX}|{c}|{q}|d{d}"
    item = hashlib.sha256(f"{key}|{version}|{judged_on}".encode()).hexdigest() if judged_on != "v24" else \
        hashlib.sha256(f"{key}|{version}".encode()).hexdigest()
    ans = groups[q] != "not_answerable"
    _, v2 = JR._keys24()
    kh = JR.S373.key_hash(q, v2) if judged_on == "v24" else JR.S512.key_hash25(q, JR.S512.v2_records())
    row = {"question_id": q, "config": c, "draw": d, "key_hash": kh, "item_sha256": item,
           "answerable_prompt": ans, "n_passages": 3, "passage_chars": 1500, "contexts_capture": "ids",
           "a_stored": None, "a_equals_stored": None, "run_id": run_of(c), "answer_key": key, "passages_kind": "ids"}
    kind, v = outcome[0], outcome[1]
    if kind == "failed":
        row.update(a={"status": "no_answer"}, b={"status": "no_answer"}, error=f"{v}: fixture")
    else:
        if kind == "scored":
            sc = ({"correctness": v, "completeness": 6 - v, "faithfulness": 1, "citation_quality": 5} if ans else
                  {"refusal_accuracy": v, "hallucination_avoidance": 6 - v, "explanation_quality": 1})
            a = {"status": "ok", "scores": sc, "justification": "fixture", "text": "fixture",
                 "attempts": 1, "stop_reason": "stop", "error": None}
        else:
            a = {"status": v, "scores": None, "justification": None, "text": "", "attempts": 2,
                 "stop_reason": None, "error": "HTTP 500: fixture"}
        row.update(a=a, b={"status": "deferred" if ans else "not_applicable"})
    row.update(faithfulness_a=(row["a"].get("scores") or {}).get("faithfulness"), faithfulness_b=None,
               b_faithfulness_missing=False, wall_s=1.0, at="2026-10-18T13:00:00", lock_sha256=FAKE_LOCK,
               run_sha256=fake_run_sha(judged_on))
    if judged_on != "v24":
        row["key_version"] = JR.S512.KEY_VERSION
    return row


def guard_module():
    spec = importlib.util.spec_from_file_location("s3_guard_s463", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def unit_files(folder: Path, rows: list[dict], draws, kind="v24"):
    """What a judging unit leaves beside its rows (judge_passages.py:636-645, 694-714): one header line per phase,
    and the recheck of each phase: its first RECHECK_N answers that reached the judge, all equal. kind "s6": S512's
    header (fake_header)."""
    JP = judge_module()
    heads, checks = [], []
    run_sha = fake_run_sha(kind)
    for ph in sorted({PHASE_OF_DRAW[d] for d in draws}):
        heads.append(dict(fake_header(kind), draws="1" if ph == 1 else "2,3"))
        mine = [r for r in rows if PHASE_OF_DRAW[r["draw"]] == ph and r["a"]["status"] != "no_answer"]
        for r in mine[:JP.RECHECK_N]:
            checks.append({"key": f"{r['run_id']}|{r['answer_key']}", "item_sha256": r["item_sha256"],
                           "run_sha256": run_sha, "equal": True, "now": {"a": (r["a"].get("scores"))},
                           "written": {"a": r["a"].get("scores")}, "at": "2026-10-18T13:30:00"})
    (folder / "judge_passages_headers.jsonl").write_text("".join(json.dumps(h) + "\n" for h in heads))
    (folder / "judge_passages_recheck.jsonl").write_text("".join(json.dumps(x) + "\n" for x in checks))


_FIX_KEY: dict = {}


def fixture_text(key, c, q, d, i):
    """A fixture answer's text: its key, then the first k of the question's expected concepts in the D5 key, k = (i +
    the strategy's place + d) mod (concepts + 1), so concept recall (panel b) differs by strategy, question and
    draw."""
    if not _FIX_KEY:
        _FIX_KEY.update(s471_module().S470.the_key()["questions"])
    con = _FIX_KEY[q].get("expected_concepts") or []
    k = (i + CONFIGS.index(c) + d) % (len(con) + 1)
    return " ".join([f"fixture answer {key}."] + list(con[:k]))


def fixture_l3(base: Path, rows_out: Path) -> Path:
    """S471's rows for the fixture's answers (the records --answers reads, the reruns' copy over K1's), written as
    S471 writes them, with a header naming plan row L3: what --concept-recall reads. Not data."""
    S471 = s471_module()
    key = S471.S470.the_key()
    groups = key_groups()
    answers, _, _ = read_answers([base / "k1_runs" / "runs", base / "g1r15_runs" / "runs"])
    rows = []
    for k, a in sorted(answers.items()):
        _, c, q, dd = k.split("|")
        r = {"answer_key": k, "config": c, "question_id": q, "draw": int(dd[1:]), "group": groups[q],
             "status": a["status"], "answer_sha256": a["answer_sha256"], "turn_limit_note": a["turn_limit_note"]}
        if groups[q] == "not_answerable":
            r.update({f: None for f in CR_FIELDS}, reason="not applicable")
            r["note_removed"] = False
        else:
            r.update(S471.score(a["answer"], key["questions"][q]["expected_concepts"], a["turn_limit_note"]),
                     reason=None)
        rows.append(r)
    rows_out.parent.mkdir(parents=True, exist_ok=True)
    rows_out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (rows_out.parent / "header.json").write_text(json.dumps(
        {"plan_row": "L3", "script": "scripts/S471_l3_concept_recall.py", "provisional": True,
         "written_utc": "fixture, not data", "matcher": "loose (fixture)", "key": {"sha256": key["sha256"]},
         "inputs": {"manifest_sha256": "fixture"}}))
    return rows_out


def fixture_l3_d181(base: Path, l3_rows: Path, out: Path) -> Path:
    """S471 --d181's rows for the fixture's answers, written as S471 --d181 writes them: one row per row of l3_rows (the
    fixture's L3 rows), d181_concept_recall.score() on key v2.5's concepts and question text for every scored answer,
    na_fields() for the not-answerable ones; a header naming the D181 reading on key v2.5 and L3's answer copy, with
    the rows' counts. Not data. Imports d181_concept_recall (S505 sets two KMP_* variables in os.environ), so only the
    selftest calls it."""
    import d181_concept_recall as D181
    S471 = s471_module()
    key25 = D181.the_key_v25(S471.S470.the_key())
    answers, _, _ = read_answers([base / "k1_runs" / "runs", base / "g1r15_runs" / "runs"])
    rows = []
    for r in (json.loads(x) for x in l3_rows.read_text().splitlines() if x.strip()):
        x = {f: r[f] for f in ("answer_key", "config", "question_id", "draw", "group", "status", "answer_sha256",
                               "turn_limit_note")}
        if r["group"] == "not_answerable":
            x.update(D181.na_fields(), reason="not applicable")
        else:
            q = key25["questions"][r["question_id"]]
            a = answers[r["answer_key"]]
            x.update(D181.score(a["answer"], q["expected_concepts"], q["question"], a["turn_limit_note"]), reason=None)
        rows.append(x)
    out.mkdir(parents=True, exist_ok=True)
    (out / "concept_recall.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    sc = [r for r in rows if r["group"] != "not_answerable"]
    (out / "header.json").write_text(json.dumps(
        {"plan_row": "L3", "script": "scripts/S471_l3_concept_recall.py", "reading": "D181", "provisional": False,
         "written_utc": "fixture, not data", "matcher": "D181 (fixture)",
         "key": {"sha256": D181.KEY25_SHA256, "version": "2.5"}, "inputs": {"manifest_sha256": "fixture"},
         "counts": {"rows": len(rows), "scored": len(sc), "status_scored": dict(Counter(r["status"] for r in sc)),
                    "by_group": dict(Counter(r["group"] for r in rows))}}))
    return out


def s6_outcome(o):
    """The fixture's key v2.5 outcome of an answer whose key v2.4 outcome is o: a score s becomes 6 - s (so every
    rate of a changed question moves), a failure or a judge-call failure stays as it is."""
    return ("scored", 6 - o[1]) if o[0] == "scored" else o


def build_fixture(to: Path, draws=(1,), replace=True, quiet=True, s6=False) -> Path:
    """out/ (G1's main pass: the 15 reruns in their old, failed versions), out_g1r15/ (their new versions, the draws
    given), each with a start_*.json and, per run folder, the judge's headers and a passed recheck; k1_runs/ and
    g1r15_runs/ (the generation records judged, with a MANIFEST.sha256 each); g1_collect.jsonl made by s3_guard.py's
    collect. s6 (D186 (3)): also out_s6_g1/ and out_s6_g1r15/ as S512 writes them, key v2.5 rows of the answers to
    S512's 132 changed questions at the draws given (s6_outcome of each answer's outcome; the reruns old in
    out_s6_g1, new in out_s6_g1r15). Returns the collect file."""
    import contextlib
    import io
    groups = key_groups()
    idx = {}
    for g in ("answerable", "not_answerable", "false_premise"):
        for i, q in enumerate(sorted(q for q, gg in groups.items() if gg == g)):
            idx[q] = i
    reruns = set(rerun_keys())
    changed = set(JR.S512.changed_ids())
    to.mkdir(parents=True, exist_ok=True)
    (to / "FIXTURE.txt").write_text("A fake S3 output made by S463 fixture: not data.\n")
    for sub in ("out", "out_g1r15") + (("out_s6_g1", "out_s6_g1r15") if s6 else ()):
        for c in CONFIGS:
            (to / sub / "judge" / run_of(c)).mkdir(parents=True, exist_ok=True)
        (to / sub / "start_11455_20261018T120423.json").write_text(json.dumps(
            {"worker": "fixture_11455", "sets": "G1R15 G1", "commit": "0" * 40, "lock_sha256": FAKE_LOCK,
             "started": "2026-10-18T12:04:23"}) + "\n")
    ans = {"k1_runs": defaultdict(list), "g1r15_runs": defaultdict(list)}
    for c in CONFIGS:
        main, new, main6, new6 = [], [], [], []
        for q in sorted(groups):
            for d in (1, 2, 3):
                key = f"{INDEX}|{c}|{q}|d{d}"
                o = planned(c, q, d, groups, idx)

                def rec(oo, key=key, q=q, d=d):
                    failed = oo[0] == "failed"
                    google = failed and oo[2] in GOOGLE_STOP
                    stop = oo[1] if failed else (
                        "max_turns_partial" if c == "rlm_5" and idx[q] % 9 == 4 else
                        ("ok" if c in ("single_pass", "verified_pass") else "final"))
                    vs = verifier_status(c, q, d, groups, idx)
                    calls = [{"provider": "gemini", "status": oo[2] or "ok", "prompt_tokens": 100,
                              "output_tokens": 10, "thinking_tokens": 0, "wall_s": 3.0}
                             for _ in range(fixture_calls(c, idx[q], d))]
                    if c == "verified_pass":                 # its verifier call, local, after a wait (D95 Q200)
                        calls[1].update(provider="ollama", status="ok", waited_for_server_s=FIXTURE_WAIT)
                    lat = sum(x["wall_s"] for x in calls) + sum(x.get("waited_for_server_s", 0) for x in calls)
                    return {"answer_key": key, "question_id": q, "draw": d, "config": c, "run_id": run_of(c),
                            "gen_model": "gemini::gemini-3-flash-preview",
                            "generation": {"answer": "" if failed else fixture_text(key, c, q, d, idx[q]),
                                           "error": None if (not failed or google) else f"{oo[1]}: fixture",
                                           "stop_reason": stop, "config": c, "calls": calls,
                                           "tokens_used": 110 * len(calls), "latency_s": lat,
                                           "verification": None if vs is None else {"status": vs}}}
                if key in reruns:
                    old = ("failed", "call_error", None)
                    ans["k1_runs"][c].append(rec(old))
                    ans["g1r15_runs"][c].append(rec(o))
                    if d in draws:
                        main.append(fake_row(c, q, d, groups, old, "old"))
                        new.append(fake_row(c, q, d, groups, o, "rerun"))
                        if s6 and q in changed:
                            main6.append(fake_row(c, q, d, groups, old, "old", "s6"))
                            new6.append(fake_row(c, q, d, groups, s6_outcome(o), "rerun", "s6"))
                else:
                    ans["k1_runs"][c].append(rec(o))
                    if c in ("verified_pass", "rlm_5", "rlm_10", "rlm_20"):
                        ans["g1r15_runs"][c].append(rec(o))
                    if d in draws:
                        main.append(fake_row(c, q, d, groups, o, "v1"))
                        if s6 and q in changed:
                            main6.append(fake_row(c, q, d, groups, s6_outcome(o), "v1", "s6"))
        for sub, rows, kind in (("out", main, "v24"), ("out_g1r15", new, "v24"), ("out_s6_g1", main6, "s6"),
                                ("out_s6_g1r15", new6, "s6")):
            if kind == "s6" and not s6:
                continue
            folder = to / sub / "judge" / run_of(c)
            (folder / "judge_passages.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            if rows:
                unit_files(folder, rows, draws, kind)
    for sub, by in ans.items():
        lines = []
        for c, recs in by.items():
            p = to / sub / "runs" / run_of(c) / "answers.jsonl"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("".join(json.dumps(r) + "\n" for r in recs))
            lines.append(f"{sha256_file(p)}  runs/{run_of(c)}/answers.jsonl")
        (to / sub / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    dest = to / "g1_collect.jsonl"
    G = guard_module()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = G.collect([to / "out"], (to / "out_g1r15") if replace else None, dest, "G1")
    if rc:
        raise SystemExit(f"fixture: collect refused: {buf.getvalue()}")
    if not quiet:
        print(buf.getvalue().strip())
    return dest


def fixture_extra_score(c, i):
    """The fixture's score of arm c on the i-th answerable question."""
    return (5 if i < 80 else 2) if c == "matched_budget" else (5 if i < 45 else 2)


def fixture_extra(root: Path, draws=(1,), s6=False) -> Path:
    """G2's and G6's folder as S528 lays it out, made up: out_g2 and out_g6 with their rows, headers, rechecks and start
    files, on request out_s6_g2 and out_s6_g6, the collects by s3_guard's own collect, and G2's answers records. Not
    data. Only cap 10 of G6, whose collect read_extra sets aside by configuration."""
    import contextlib
    import io
    groups = key_groups()
    idx = {}
    for g in ("answerable", "not_answerable", "false_premise"):
        for i, q in enumerate(sorted(q for q, gg in groups.items() if gg == g)):
            idx[q] = i
    changed = set(JR.S512.changed_ids())
    G = guard_module()
    recs = []
    for c, name, _ in EXTRA:
        low = name.lower()
        run = f"exp_01__{c}__{INDEX}" if name == "G2" else f"b4_rlm_ref__{c}__all135"
        akey = (lambda q, d: f"{INDEX}|{c}|{q}|d{d}") if name == "G2" else (lambda q, d: f"{c}|{q}|d{d}")
        rows24, rows25 = [], []
        for q in sorted(groups):
            for d in draws:
                g, i = groups[q], idx[q]
                s = fixture_extra_score(c, i) if g == "answerable" else (5 if i < 30 else 1)
                r = fake_row(c, q, d, groups, ("scored", s), "v1")
                r.update(run_id=run, answer_key=akey(q, d))
                rows24.append(r)
                if s6 and q in changed:
                    r5 = fake_row(c, q, d, groups, ("scored", 6 - s), "v1", "s6")
                    r5.update(run_id=run, answer_key=akey(q, d))
                    rows25.append(r5)
                if name == "G2":
                    calls = [{"provider": "gemini", "status": "ok", "prompt_tokens": 100, "output_tokens": 10,
                              "thinking_tokens": 0, "wall_s": 3.0}]
                    recs.append({"answer_key": akey(q, d), "question_id": q, "draw": d, "config": c, "run_id": run,
                                 "generation": {"answer": f"fixture answer {akey(q, d)}.", "error": None, "stop_reason": "ok",
                                                "calls": calls, "tokens_used": 110, "latency_s": 3.0}})
        for sub, rows, kind in ((f"out_{low}", rows24, "v24"), (f"out_s6_{low}", rows25, "s6")):
            if kind == "s6" and not s6:
                continue
            folder = root / sub / "judge" / run
            folder.mkdir(parents=True, exist_ok=True)
            (root / sub / "start_11455_20261018T120423.json").write_text(json.dumps(
                {"worker": "fixture_11455", "sets": name, "commit": "0" * 40, "lock_sha256": FAKE_LOCK,
                 "started": "2026-10-18T12:04:23"}) + "\n")
            (folder / "judge_passages.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            unit_files(folder, rows, draws, kind)
            dest = root / (f"{low}_collect.jsonl" if kind == "v24" else f"s6_{low}_collect.jsonl")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = G.collect([root / sub], None, dest, name if kind == "v24" else "S6" + name)
            if rc:
                raise SystemExit(f"fixture: collect refused {name}: {buf.getvalue()}")
    (root / "matched_budget_answers.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
    g6 = [{"answer_key": f"cap10|{q}|d{d}", "question_id": q, "draw": d, "status": "ok", "run_id": G6_RUN10,
           "answer": f"fixture answer cap10|{q}|d{d}.", "wall_s": fixture_g6_wall(idx[q], d)}
          for q in sorted(groups) for d in draws]
    (root / G6_FIXTURE).write_text("".join(json.dumps(r) + "\n" for r in g6))
    return root


G6_FIXTURE = "package_rlm10_answers.jsonl"              # fixture_extra's G6 cap 10 generation records (D218)


def fixture_g6_wall(i, d):
    """The fixture's Zhang RLM-10 wall_s of an answer: differs by question and draw. Not data."""
    return 20.0 + 5.0 * (i % 7) + 1.5 * d


def fixture_s518(folder: Path) -> Path:
    """S518's five verdict files, made up, of their real shape (D195's sources and roles, S518.reading's readings).
    Not data: no T2 or second-judge row is read to make them."""
    S518 = s518_module()
    if (folder / "second_judge.json").exists():
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    for k, (src, role) in enumerate(S518.SOURCES.items()):
        n1, n2 = (20, 9) if src in ("gemma3", "qwen3-coder") else (60, 26)
        d1, d2 = -0.10 - 0.01 * k, 0.20 + 0.05 * k
        lo, hi = (d2 - d1) - (0.15 + 0.2 * (k % 3)), (d2 - d1) + 0.15   # k = 2: an interval containing 0
        res = {"one_paper": {"questions": n1, "d": d1, "lo": d1 - 0.05, "hi": d1 + 0.05, "p_signflip_exact_two_sided": 0.01},
               "many_paper": {"questions": n2, "d": d2, "lo": d2 - 0.2, "hi": d2 + 0.2, "p_signflip_exact_two_sided": 0.2},
               "interaction": {"I": d2 - d1, "lo": lo, "hi": hi, "reading": S518.reading(lo, hi)}}
        (folder / f"{src}.json").write_text(json.dumps(
            {"source": src, "role": role, "script_commit": "fixture", "decision": "D195", "threshold": S518.THRESHOLD,
             "inputs": [], "rows": {}, "result": res, "note": "FIXTURE, NOT DATA"}, indent=1) + "\n")
    lo, hi = 0.35, 0.75                                       # the reference row (D235): S518 reference's shape
    res = {"one_paper": {"questions": 60, "d": -0.25, "lo": -0.33, "hi": -0.19, "p_signflip_exact_two_sided": 1e-9},
           "many_paper": {"questions": 26, "d": 0.30, "lo": 0.14, "hi": 0.47, "p_signflip_exact_two_sided": 0.003},
           "interaction": {"I": 0.55, "lo": lo, "hi": hi, "reading": S518.reading(lo, hi)}}
    (folder / f"{S518.REFERENCE}.json").write_text(json.dumps(
        {"source": S518.REFERENCE, "role": S518.REF_ROLE, "key": S518.REF_KEY, "judge": "devstral-small-2:24b",
         "script_commit": "fixture", "decision": S518.REF_DECISION.strip("*"), "method": "D195",
         "threshold": S518.THRESHOLD, "inputs": [], "rows": {}, "result": res, "note": "FIXTURE, NOT DATA"},
        indent=1) + "\n")
    return folder


def fixture_fig3e(folder: Path) -> Path:
    """S522's tables.json and header.json, made up, of its real shape. Not data."""
    import S522_fig3e_rows as S522
    if (folder / "tables.json").exists():
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    sizes, cells, ns_, st, gc = (5, 10, 20, 50), [], [], [], []
    n_ = {S522.ALL: (22, 44, 86, 86), S522.SAME: (22,) * 4, S522.REFUSAL: (39,) * 4}
    i = 0
    for block in S522.BLOCKS:
        for c, nq in zip(sizes, n_[block]):
            ns_.append({"row_kind": "n", "block": block, "core_papers": c, "question_group": "all", "n_questions": nq})
            for s, g in E_ROWS:
                if g != "all" and block != S522.ALL:
                    continue
                if g != "all":
                    nq2 = S522.N_SPLIT_WANT[g][c]
                    ns_.append({"row_kind": "n", "block": block, "core_papers": c, "question_group": g, "n_questions": nq2})
                d = float((i * 7) % 31 - 15) + 0.25
                lo, hi = d - 4.0, d + 4.0
                sign, size = S522.d_parts(d)
                cells.append({"row_kind": "cell", "block": block, "core_papers": c, "strategy": s, "question_group": g,
                              "n_questions": nq, "n_pairs": 3 * nq, "pass_strategy_pct": 50.0 + d,
                              "pass_single_pass_pct": 50.0, "d_pp": d, "ci95_lo_pp": lo, "ci95_hi_pp": hi,
                              "interval_excludes_0": "yes" if (lo > 0 or hi < 0) else "no", "awaiting_s6_answers": 0,
                              "d_sign": sign, "d_size_pp": size})
                i += 1
            five = [{"row_kind": "run-to-run strategy", "block": block, "core_papers": c, "strategy": s,
                     "n_questions": 6, "d_pp_by_draw": "{}", "range_pp": 2.0 + k, "withheld": None}
                    for k, s in enumerate(S522.FIVE)]
            st += five
            gc.append(S522.noise_cell(five))
    gc[1].update(median_range_pp=None, withheld="made up: withheld")
    t = {"cells": cells, "n": ns_, "noise_strategy": st, "noise_cell": gc, "draws_read": [1, 2, 3], "ratios": [0, 1, 3],
         "g4_answers_final_key": 7000, "g4_answers_planned": S522.PLANNED_G4}
    (folder / "tables.json").write_text(json.dumps(t))
    (folder / "header.json").write_text(json.dumps({"script": S522.SCRIPT, "tables_sha256": sha256_file(folder / "tables.json"),
                                                    "reproduced": ["fixture, not data"]}))
    return folder


# D195, D168: what rank may never open (selftest's blind_checks, under the audit hook below)
BLIND_PATHS = re.compile(r"out_t2|out_s6_t2|mentori-runs-s6-second|human_eval_v22|rater_packets|internal_review|"
                         r"human_eval_sheet|all_v2_1_signoff|concept_match_labels|mentori-runs/|/S354|/S500|/S501|/S510|"
                         r"/S517")
_AUDIT = {"on": False, "seen": None}


def _audit_opens() -> list:
    """Every path opened while _AUDIT["on"], through one sys.addaudithook (it cannot be removed)."""
    if _AUDIT["seen"] is None:
        _AUDIT["seen"] = []

        def hook(ev, a):
            if _AUDIT["on"] and ev == "open" and isinstance(a[0], (str, Path)):
                _AUDIT["seen"].append(str(a[0]))
        sys.addaudithook(hook)
    return _AUDIT["seen"]


def fixture(args):
    to = Path(args.to).expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty")
    draws = tuple(sorted({int(x) for x in args.draws.split(",")}))
    dest = build_fixture(to, draws, quiet=False)
    print(f"fixture (not data) in {to}; draws {draws}; try: uv run --frozen python scripts/S463_fig2_ranking.py rank "
          f"--collect {dest} --draws {','.join(map(str, draws))} --answers {to / 'k1_runs' / 'runs'} "
          f"--answers {to / 'g1r15_runs' / 'runs'} --out {to / 'plate'}")


# ---------------------------------------------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------------------------------------------
def selftest(args, quiet=False):
    """Offline checks (module docstring, selftest). Each check computes its expected value apart from the code it
    checks; a check whose code raises reports the exception as its failure. Returns 0 when every check passes."""
    import numpy as np
    results = []

    def check(name, ok, detail=""):
        results.append(bool(ok))
        if not quiet or not ok:
            print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

    def attempt(name, fn):
        """Run one block of checks; an exception in it is a failed check named after the block."""
        try:
            fn()
        except Exception as e:                                       # noqa: BLE001
            check(f"{name}: ran without an error", False, f"{type(e).__name__}: {str(e)[:300]}")

    tmp = Path(tempfile.mkdtemp(prefix="s463_selftest_"))
    groups = key_groups()
    qa = sorted(q for q, g in groups.items() if g == "answerable")

    def ns(collect, draws="1", answers=True, out=None, replace_out=None, no_plate=True, concept_recall=None,
           concept_recall_d181=None):
        base = collect.parent
        kw = {}
        if not no_plate:                                 # a plate needs G2, G6 and Figure 3f's rows (made-up here)
            dd = tuple(int(x) for x in draws.split(","))
            ex = base / f"extra_{'_'.join(map(str, dd))}"
            if not ex.exists():
                fixture_extra(ex, dd)
            kw = {"extra": str(ex), "fig3e": str(fixture_fig3e(base / "fig3e")), "s518": str(fixture_s518(base / "s518")),
                  "g2_answers": str(ex / "matched_budget_answers.jsonl"), "g6_answers": str(ex / G6_FIXTURE)}
        return types.SimpleNamespace(collect=str(collect), draws=draws, out=str(out or base / "plate"),
                                     answers=[str(base / "k1_runs" / "runs"), str(base / "g1r15_runs" / "runs")]
                                     if answers else None, replace_out=replace_out, no_plate=no_plate,
                                     concept_recall=None if concept_recall is None else str(concept_recall),
                                     concept_recall_d181=None if concept_recall_d181 is None
                                     else str(concept_recall_d181), **kw)

    def refused(fn, *a, **k):
        """The refusal's message; "NOT REFUSED" when fn returns; "CRASH ..." for any other exception (a crash is
        never taken as a refusal)."""
        try:
            fn(*a, **k)
        except Refused as e:
            return str(e)
        except Exception as e:                                       # noqa: BLE001
            return f"CRASH {type(e).__name__}: {e}"
        return "NOT REFUSED"

    def boot_apart(vals, has):
        """Rule 2's interval computed apart: its own generator draw, the drawn questions' values averaged over those
        with a value, numpy's percentiles at the literal 2.5 and 97.5 (S407:191)."""
        vals, has = np.array(vals, dtype=float), np.array(has, dtype=float)
        idx = np.random.default_rng(20261013).integers(0, len(vals), size=(10000, len(vals)))
        top, bot = (vals * has)[idx].sum(axis=1), has[idx].sum(axis=1)
        return np.percentile(top[bot > 0] / bot[bot > 0], [2.5, 97.5])

    # ---- the test and the resamples, apart from any data
    def method():
        for t, p in (("threshold_3", 0.0192108154296875), ("threshold_4", 0.007537841796875)):
            x = json.loads(S04A.read_text())["part1_verified_vs_single"][t]
            c = x["contingency"]
            got = signflip_p([1] * c["CI"] + [-1] * c["IC"] + [0] * (c["CC"] + c["II"]))
            check(f"sign-flip reproduces S04a {t}: {c['CI']} against {c['IC']}, P {p}",
                  got == p == x["mcnemar_exact_p"], f"{got!r}")
        rng = np.random.default_rng(7)

        def by_groups(diffs):
            nz = [Fraction(x) for x in diffs if x != 0]
            L = math.lcm(*[x.denominator for x in nz])
            obs = abs(sum(int(x * L) for x in nz))
            cnt = Counter(abs(int(x * L)) for x in nz)
            dist = {0: 1}
            for v, k in cnt.items():
                new = defaultdict(int)
                for s_, w in dist.items():
                    for j in range(k + 1):
                        new[s_ + v * (2 * j - k)] += w * math.comb(k, j)
                dist = new
            return float(Fraction(sum(w for s_, w in dist.items() if abs(s_) >= obs), 2 ** len(nz)))
        ok = True
        for trial in range(40):
            n = int(rng.integers(3, 14))
            dif = [Fraction(int(a) - int(b), 3) for a, b in zip(rng.integers(0, 4, n), rng.integers(0, 4, n))]
            if not any(dif):
                continue
            brute = sum(1 for s_ in range(2 ** n) if abs(sum((1 if s_ >> i & 1 else -1) * abs(x)
                                                             for i, x in enumerate(dif))) >= abs(sum(dif))) / 2 ** n
            ok &= abs(signflip_p(dif) - brute) < 1e-12 and abs(by_groups(dif) - signflip_p(dif)) < 1e-12
        check("sign-flip equals full enumeration and the grouped binomial method on 40 random sets of thirds", ok)
        msg = refused(reproduce)
        check("reproduce() passes: S04a's P values, resample counts equal to S457.boot_matrix (tracked)",
              msg == "NOT REFUSED", msg)
        check("zero bound: 0 of 39 questions gives 7.4% (LIST.md:363-364)",
              S457.half_up(100 * zero_bound(39), 1) == "7.4")
        check("full bound (O2, the mirror): 39 of 39 questions gives 92.6%, 1 minus the zero bound",
              S457.half_up(100 * full_bound(39), 1) == "92.6" and abs(full_bound(39) + zero_bound(39) - 1) < 1e-15)
        v = [float(x) for x in np.random.default_rng(3).integers(0, 2, 86)]
        h = [0.0 if i in (5, 40) else 1.0 for i in range(86)]
        lo, hi = interval([a * b for a, b in zip(v, h)], h)
        lo2, hi2 = boot_apart(v, h)
        check("Rule 2 interval equals one computed apart (own draw, literal percentiles 2.5 and 97.5, two questions "
              "without a value)", abs(lo - lo2) < 1e-12 and abs(hi - hi2) < 1e-12, f"{lo} {hi} against {lo2} {hi2}")
        sm = summarise({c: {f"q{i}": (Fraction(int(i == 0 and c == "rlm_5")), {1: int(i == 0 and c == "rlm_5")})
                            for i in range(39)} for c in CONFIGS}, [f"q{i}" for i in range(39)], [1])
        check("Rule 9 bound written only for a zero: a rate of 1/39 has none, 0/39 has one",
              sm["rlm_5"]["zero_bound"] is None and sm["rlm_10"]["zero_bound"] is not None)
        sm2 = summarise({c: {f"q{i}": (Fraction(int(c == "rlm_5" or i > 0)), {1: int(c == "rlm_5" or i > 0)})
                             for i in range(39)} for c in CONFIGS}, [f"q{i}" for i in range(39)], [1])
        check("O2 bound written only for a 100%: a rate of 38/39 has none, 39/39 has one (0.05^(1/39)); neither has "
              "a zero bound",
              sm2["rlm_10"]["full_bound"] is None and abs(sm2["rlm_5"]["full_bound"] - full_bound(39)) < 1e-15
              and sm["rlm_10"]["full_bound"] is None
              and sm2["rlm_5"]["zero_bound"] is None and sm2["rlm_10"]["zero_bound"] is None)
    attempt("method", method)

    # ---- Rule 6 and Rule 11 on built summaries (each case one the fixture does not reach)
    def rules():
        def summ_of(rates):
            return {c: {"rate_x": Fraction(r), "rate": float(Fraction(r))} for c, r in rates.items()}

        def pr_of(top, d_p):
            out = {}
            for a_, b_ in combinations(CONFIGS, 2):
                if top in (a_, b_):
                    o = b_ if a_ == top else a_
                    d, p = d_p[o]
                    d = Fraction(d) if a_ == top else -Fraction(d)
                else:
                    d, p = Fraction(1, 100), 0.5
                out[(a_, b_)] = {"d": float(d), "d_x": d, "lo": None, "hi": None, "p": p, "a_higher": 0,
                                 "b_higher": 0, "questions": 86}
            return out
        rates = {"single_pass": "6/10", "verified_pass": "5/10", "multi_hop": "55/100", "rlm_5": "65/100",
                 "rlm_10": "8/10", "rlm_20": "7/10"}
        # 1. RLM-10 first by mean, separated from four in its favour, and from RLM-20 at P < 0.05 in the WRONG
        #    direction (a pair difference can disagree with the rates when questions lack a share): not met
        favour = {o: ("1/10", 0.001) for o in CONFIGS if o != "rlm_10"}
        r = rule6(summ_of(rates), pr_of("rlm_10", {**favour, "rlm_20": ("-1/20", 0.01)}), "highest")
        check("Rule 6: a separation in the wrong direction does not count (RLM-20 not separated)",
              r["strategy"] == "rlm_10" and not r["met"] and r["not_separated_from"] == ["rlm_20"], str(r))
        r = rule6(summ_of(rates), pr_of("rlm_10", favour), "highest")
        check("Rule 6: separated from all five in its favour at P < 0.05 is met", r["met"], str(r))
        # 2. a tie at the top by mean, though the pair test separates them: Rule 6 not met, E1a weakens
        tied = {**rates, "rlm_20": "8/10"}
        pr = pr_of("rlm_10", favour)
        r6 = {"highest": rule6(summ_of(tied), pr, "highest"), "lowest": rule6(summ_of(tied), pr, "lowest")}
        check("Rule 6: a shared first place is never met, even when the pair test separates the two",
              not r6["highest"]["met"] and r6["highest"]["tied_with"] == ["rlm_20"], str(r6["highest"]))
        check("Rule 11: a shared first place gives E1a 'weakens'", verdict(CLAIMS[0], None, pr, r6) == "weakens")
        r6b = {"highest": rule6(summ_of(rates), pr, "highest"), "lowest": rule6(summ_of(rates), pr, "lowest")}
        check("Rule 11: a claim that RLM-20 is lowest, when verified pass is last by mean, gives 'reverses'",
              r6b["lowest"]["strategy"] == "verified_pass"
              and verdict(("X", "", "lowest", "rlm_20", None, "answerable"), None, pr, r6b) == "reverses")
        # 3. paired directions
        e5 = next(c for c in CLAIMS if c[0] == "E5")
        for d, p, want in (("-1/86", 0.9, "reverses"), ("-5/86", 0.001, "reverses"), ("0", 1.0, "weakens"),
                           ("3/86", 0.25, "weakens"), ("10/86", 0.002, "holds")):
            prx = pr_of("rlm_10", {**favour, "single_pass": (d, p)})
            check(f"Rule 11 direction: RLM-10 minus single pass {d}, P {p} gives {want}",
                  verdict(e5, None, prx, None) == want, verdict(e5, None, prx, None))
        r11 = next(c for c in CLAIMS if c[0] == "R11")
        prx = pr_of("verified_pass", {**{o: ("1/10", 0.5) for o in CONFIGS}, "single_pass": ("-15/86", 0.01)})
        check("Rule 11 'below': verified pass under single pass at P < 0.05 holds", verdict(r11, None, prx, None)
              == "holds")
        # 4. equal rates whose float means differ tie exactly (review of 18 October, defect 2): two strategies'
        #    passes per question (0 to 3 of 3 draws) with the same total, built until their float means differ
        rng = np.random.default_rng(11)
        qs = [f"q{i}" for i in range(86)]
        found = None
        for _ in range(200):
            a_ = [int(x) for x in rng.integers(0, 4, 86)]
            b_ = [int(x) for x in rng.integers(0, 4, 86)]
            gap, i = sum(a_) - sum(b_), 0
            while gap and i < 86:
                if gap > 0 and b_[i] < 3:
                    b_[i], gap = b_[i] + 1, gap - 1
                elif gap < 0 and b_[i] > 0:
                    b_[i], gap = b_[i] - 1, gap + 1
                else:
                    i += 1
            if not gap and sum(x / 3 for x in a_) / 86 != sum(x / 3 for x in b_) / 86:
                found = (a_, b_)
                break
        check("a pair of equal rates whose float means differ was built to test ties", found is not None)
        if found:
            sh = {}
            for c in CONFIGS:
                k3 = found[0] if c == "rlm_10" else found[1] if c == "rlm_20" else [0] * 86
                sh[c] = {q: (Fraction(k3[i], 3), {1: int(k3[i] >= 1), 2: int(k3[i] >= 2), 3: int(k3[i] >= 3)})
                         for i, q in enumerate(qs)}
            summ = summarise(sh, qs, [1, 2, 3])
            r = rule6(summ, pairs(sh, qs), "highest")
            check("equal rates tie exactly in Rule 6 (RLM-10 and RLM-20 share first place)",
                  summ["rlm_10"]["rate_x"] == summ["rlm_20"]["rate_x"] and r["tied_with"] in (["rlm_20"], ["rlm_10"]),
                  str((summ["rlm_10"]["rate_x"], summ["rlm_20"]["rate_x"], r["tied_with"])))
    attempt("Rule 6 and Rule 11", rules)

    # ---- the draw-1 fixture
    f1 = build_fixture(tmp / "d1", (1,))
    R = None
    try:
        R = rank(ns(f1), quiet=True)
    except Exception as e:                                           # noqa: BLE001
        check("rank reads the draw-1 fixture", False, f"{type(e).__name__}: {e}")
    if R is None:
        print(f"selftest: {sum(results)} of {len(results)} checks pass")
        return 1
    known = {"single_pass": (65, 86, 65, 86), "verified_pass": (54, 86, 53, 86), "multi_hop": (60, 86, 0, 86),
             "rlm_5": (69, 86, 69, 86), "rlm_10": (74, 85, 74, 85), "rlm_20": (72, 86, 72, 86)}
    idx_a = {q: i for i, q in enumerate(qa)}

    def fixture_checks():
        check("rank reads the draw-1 fixture (810 rows, 5 reruns from their own pass)",
              R["read"]["rows_read"] == 810 and len(R["read"]["reruns_read"]) == 5
              and R["read"]["rows_from_replace"] == 5)
        u = R["read"]["units"]["folders"]
        g1u = {k_: v for k_, v in u.items() if "/out/" in k_}
        check("every judging unit read passed its recheck (10 of 10 in each of G1's six, all of G1R15's few)",
              len(g1u) == 6 and all(v["recheck"]["phase 1"] == "10 of 10 equal" for v in g1u.values())
              and all(v["recheck"]["phase 1"].split(" of ")[0] == v["recheck"]["phase 1"].split(" of ")[1].split()[0]
                      for v in u.values()), str(u)[:300])
        s3, s4 = R["res"]["answerable"][3]["summary"], R["res"]["answerable"][4]["summary"]
        for c, (k3, n3, k4, n4) in known.items():
            check(f"{LABEL[c]}: pass rate {k3}/{n3} at score 3 and {k4}/{n4} at 4 (worked by hand from the fixture; "
                  f"the judge's other dimensions hold other scores)",
                  s3[c]["rate_x"] == Fraction(k3, n3) and s4[c]["rate_x"] == Fraction(k4, n4)
                  and s3[c]["questions_with_share"] == n3,
                  f"{s3[c]['rate']} {s4[c]['rate']} n {s3[c]['questions_with_share']}")
        check("each draw's rate is over the questions measured on that draw (RLM-10: 74 of 85)",
              s3["rlm_10"]["per_draw"][1] == (74 / 85, 85), str(s3["rlm_10"]["per_draw"]))
        pr3, pr4 = R["res"]["answerable"][3]["pairs"], R["res"]["answerable"][4]["pairs"]
        sv = pr3[("single_pass", "verified_pass")]
        check("single pass against verified pass reproduces S04a through the reader: P 0.0192108154296875 (15 "
              "against 4) and 0.007537841796875 (15 against 3)",
              sv["p"] == 0.0192108154296875 and (sv["a_higher"], sv["b_higher"]) == (15, 4)
              and pr4[("single_pass", "verified_pass")]["p"] == 0.007537841796875)
        for c in CONFIGS:
            vals, has = [], []
            for q in qa:
                o = planned(c, q, 1, groups, idx_a)
                vals.append(float(o[0] != "unscored" and o[0] == "scored" and o[1] >= 3))
                has.append(float(o[0] != "unscored"))
            lo, hi = boot_apart(vals, has)
            check(f"{LABEL[c]}: Rule 2 interval at score 3 equals one computed apart ({100 * lo:.1f} to {100 * hi:.1f})",
                  abs(lo - s3[c]["lo"]) < 1e-12 and abs(hi - s3[c]["hi"]) < 1e-12, f"{s3[c]['lo']} {s3[c]['hi']}")
        # the pair interval, apart: per question RLM-10 minus single pass where both have a share
        va, vb = ([float(planned(c, q, 1, groups, idx_a)[0] == "scored" and planned(c, q, 1, groups, idx_a)[1] >= 3)
                   for q in qa] for c in ("rlm_10", "single_pass"))
        hs = [float(planned("rlm_10", q, 1, groups, idx_a)[0] != "unscored") for q in qa]
        lo, hi = boot_apart([a_ - b_ for a_, b_ in zip(va, vb)], hs)
        x = pair(pr3, "rlm_10", "single_pass")
        check(f"RLM-10 minus single pass: difference 10/85 and its Rule 2 interval computed apart ({100 * lo:.1f} to "
              f"{100 * hi:.1f})", x["d_x"] == Fraction(10, 85) and abs(lo - x["lo"]) < 1e-12
              and abs(hi - x["hi"]) < 1e-12, f"{x['d_x']} {x['lo']} {x['hi']}")
        rf = R["res"]["refusal"][REFUSAL_T]["summary"]
        check("refusal at score 3: single pass 30/39, verified pass 35/39, multi-hop 20/39 (its blocked answer is "
              "not refused), RLM-10 10/39, RLM-20 39/39",
              (rf["single_pass"]["rate_x"], rf["verified_pass"]["rate_x"], rf["multi_hop"]["rate_x"],
               rf["rlm_10"]["rate_x"], rf["rlm_20"]["rate_x"]) == (Fraction(30, 39), Fraction(35, 39),
                                                                   Fraction(20, 39), Fraction(10, 39), 1),
              str({c: rf[c]["rate_x"] for c in CONFIGS}))
        check("refusal is read at score 3 only (Rule 9)", set(R["res"]["refusal"]) == {3})
        check("refusal zero: RLM-5 refuses 0 of 39, with its one-sided bound 7.4%; no other strategy has a bound",
              rf["rlm_5"]["rate_x"] == 0 and abs(rf["rlm_5"]["zero_bound"] - zero_bound(39)) < 1e-15
              and all(rf[c]["zero_bound"] is None for c in CONFIGS if c != "rlm_5"))
        check("refusal 100% (O2): RLM-20 refuses 39 of 39, with its one-sided lower bound 92.6%; no other strategy "
              "has one",
              rf["rlm_20"]["rate_x"] == 1 and abs(rf["rlm_20"]["full_bound"] - full_bound(39)) < 1e-15
              and all(rf[c]["full_bound"] is None for c in CONFIGS if c != "rlm_20"))
        c13 = claim_value(dict(id="t", claimed="86.0", m=("refused2", "verified_pass", "rlm_20")), R["res"])[0]
        c10 = claim_value(dict(id="t", claimed="82.0", m=("refused", "rlm_5")), R["res"])[0]
        check("claims list: a 100% given with its one-sided lower bound (O2), a 0 with its upper bound (Rule 9), "
              "any other rate with none",
              c13 == "verified pass 89.7%, RLM-20 100.0% (one-sided 95% lower bound 92.6%) of 39" and c10 == "RLM-5 0.0% of 39 (one-sided 95% upper bound 7.4%)",
              f"{c13!r} {c10!r}")
        fp3, fp4 = R["res"]["false_premise"][3], R["res"]["false_premise"][4]
        check("false premise: single pass 7 of 10, verified pass 10 of 10 (5 at score 4), RLM-20 8 of 10 (its "
              "recitation stop counted as a fail)",
              (fp3["single_pass"]["passed"], fp3["verified_pass"]["passed"], fp4["verified_pass"]["passed"],
               fp3["rlm_20"]["passed"], fp3["rlm_20"]["answers"]) == (7, 10, 5, 8, 10))
        ot = R["out_t"]
        k = lambda c, q: f"{INDEX}|{c}|{q}|d1"                                     # noqa: E731
        check("failures: RLM-5's empty answer counted as a fail by its stop reason max_turns_empty; RLM-10's failed "
              "judge call counted as unscored",
              ot["rlm_5"]["failed"] == {"max_turns_empty": [k("rlm_5", qa[0])]}
              and ot["rlm_10"]["unscored"] == {"error": [k("rlm_10", qa[1])]})
        check("Rule 10: a block and a recitation stop with no text are fails grouped as 'stopped by Google'",
              list(ot["multi_hop"]["failed"]) == ["stopped by Google (blocked; stop reason final_answer)"]
              and list(ot["rlm_20"]["failed"]) == ["stopped by Google (recitation; stop reason final)"],
              str((ot["multi_hop"]["failed"], ot["rlm_20"]["failed"])))
        check("Rule 10: a recitation stop that kept its text is scored as written and counted; a malformed reply "
              "too; cut answers counted",
              ot["single_pass"]["google_scored"] == {"stopped by Google (recitation)": [k("single_pass", qa[3])]}
              and ot["rlm_10"]["returned_scored"] == {"malformed_function_call": [k("rlm_10", qa[5])]}
              and sum(len(v) for v in ot["rlm_5"]["cut_scored"].values()) > 0, str(ot["single_pass"]))
        so = R["res_out"]["answerable"][3]["summary"]
        check("sensitivity: with the failed answer left out RLM-5 passes 69/85", so["rlm_5"]["rate_x"] == Fraction(69, 85))
        r6 = R["res"]["rule6"][3]
        check("Rule 6 at score 3: RLM-10 first by mean, not separated from RLM-20 (3 questions against 0, P 0.25); "
              "verified pass last, not separated from multi-hop",
              r6["highest"]["strategy"] == "rlm_10" and not r6["highest"]["met"] and "rlm_20" in
              r6["highest"]["not_separated_from"] and r6["lowest"]["strategy"] == "verified_pass"
              and not r6["lowest"]["met"] and pair(pr3, "rlm_10", "rlm_20")["p"] == 0.25)
        v3, v4 = R["res"]["verdicts"][3], R["res"]["verdicts"][4]
        want = {"E1a": "weakens", "E1b": "weakens", "E4": "holds", "E5": "holds", "R11": "holds", "E6": "reverses"}
        check(f"Rule 11 at score 3: {want}", v3 == want, str(v3))
        check("E6 (refusal) has no verdict at score 4", v4["E6"] is None)
        q = R["q78"]
        a3 = q["res_without"]["answerable"][3]["summary"]["verified_pass"]
        r3 = q["res_without"]["refusal"][3]["summary"]["verified_pass"]
        check("Rule 4 Q78: 2 verified-pass answers not ok (empty, unparsed); without them verified pass passes 53/85 "
              "at score 3 and refuses 35/38",
              sorted(x["status"] for x in q["not_ok"]) == ["empty", "unparsed"] and a3["rate_x"] == Fraction(53, 85)
              and r3["rate_x"] == Fraction(35, 38), str((q["status_counts_read"], a3["rate_x"], r3["rate_x"])))
        # panel e on one draw: Rule 4 reduces to the 2 x 2 table (S04a's 15 against 4 at score 3, 15 against 3 at 4;
        # single pass passes 65 of the 86 at both)
        f3_, f4_ = R["res"]["flips"][3]["verified_pass"], R["res"]["flips"][4]["verified_pass"]
        check("Rule 4 on draw 1: verified pass harmed 15, helped 4 (15/19 harmful, 15/65 degraded) at score 3; 15 and "
              "3 (15/18, 15/65) at 4; P equals Rule 3's",
              (f3_["harmed_x"], f3_["helped_x"], f4_["harmed_x"], f4_["helped_x"]) == (15, 4, 15, 3)
              and abs(f3_["harm_share"] - 15 / 19) < 1e-12 and abs(f3_["degraded_share"] - 15 / 65) < 1e-12
              and abs(f4_["harm_share"] - 15 / 18) < 1e-12 and abs(f4_["degraded_share"] - 15 / 65) < 1e-12
              and f3_["p"] == 0.0192108154296875 and f3_["per_draw"][1]["harmed"] == 15,
              str((f3_["harmed_x"], f3_["helped_x"], f3_["degraded_share"], f4_["harmed_x"], f4_["helped_x"])))
        num_ = [float(planned("single_pass", q, 1, groups, idx_a)[1] >= 3) * float(
            planned("verified_pass", q, 1, groups, idx_a)[1] < 3) for q in qa]
        lo, hi = boot_apart(num_, [float(planned("single_pass", q, 1, groups, idx_a)[1] >= 3) for q in qa])
        check(f"Rule 4's degraded share interval equals one computed apart ({100 * lo:.1f} to {100 * hi:.1f})",
              abs(lo - f3_["degraded_lo"]) < 1e-12 and abs(hi - f3_["degraded_hi"]) < 1e-12)
        check("one draw: no noise baseline (no pair of draws)",
              all(R["res"]["self_flips"][t][c]["ordered_min"] is None for t in THRESHOLDS for c in CONFIGS))
        # panel c on one draw, against the fixture's own call counts (fixture_calls) computed apart
        ca_ = R["cost"]["answerable"]
        want_c = {c: sum(fixture_calls(c, idx_a[q], 1) for q in qa) / len(qa) for c in CONFIGS}
        check("panel c: model calls per answer on the 86 equal the fixture's calls computed apart; verified pass "
              f"waits {FIXTURE_WAIT} s and its clock time is 2 x 3.0 s plus the wait",
              all(abs(ca_[c]["calls"]["mean"] - want_c[c]) < 1e-12 for c in CONFIGS)
              and abs(ca_["verified_pass"]["wait_s"]["mean"] - FIXTURE_WAIT) < 1e-12
              and abs(ca_["verified_pass"]["clock_s"]["mean"] - (6.0 + FIXTURE_WAIT)) < 1e-12
              and ca_["single_pass"]["calls"]["mean"] == 1.0,
              str({c: (ca_[c]["calls"]["mean"], want_c[c]) for c in CONFIGS}))
        lo, hi = boot_apart([float(fixture_calls("rlm_10", idx_a[q], 1)) for q in qa], [1.0] * len(qa))
        check(f"panel c: RLM-10's calls interval equals one computed apart ({lo:.2f} to {hi:.2f})",
              abs(lo - ca_["rlm_10"]["calls"]["lo"]) < 1e-12 and abs(hi - ca_["rlm_10"]["calls"]["hi"]) < 1e-12)
        orig = S457.s77_values

        def tampered():
            t_ = orig()
            t_["rlm_10"] = {**t_["rlm_10"], "llm_calls": 5.9}
            return t_
        S457.s77_values = tampered
        try:
            msg = refused(reproduce)
        finally:
            S457.s77_values = orig
        check("reproduce refuses when S77 no longer gives the letter's 5.87 calls", "the letter prints" in msg, msg)
        cl = (R["out_dir"] / "claims.md").read_text()
        w22 = S457.printed_as("words", R["cost"]["answerable"]["ratio_rlm10_single"]["calls"])
        g47 = S457.half_up(R["cost"]["all"]["rlm_10"]["calls"]["mean"], 2)
        check("claims list (D304): C22 (the agreed 'about six times the model calls', on the 86) and C47 (the letter's "
              "Table R4.1, 7.29 calls on all 135) set against the fixture's records, each status following the record",
              re.search(r"\| C22 \|.*the 86 answerable questions: [0-9.]+ times the model calls \(" + w22 + r"\); "
                        r"G1's records \| " + ("matches" if w22 == "six times" else "differs: " + w22) + r" \|", cl)
              is not None
              and re.search(r"\| C47 \|.*RLM-10 " + re.escape(g47) + r" model calls per answer, all 135 questions, "
                            r"G1's records \| " + ("matches" if g47 == "7.29" else "differs") + r" \|", cl) is not None,
              "\n".join(x for x in cl.splitlines() if x.startswith(("| C22", "| C47")))[:400])
        check("claims list written: every row, RLM-10's 92.0% set against the provisional 87.1% as 'differs'",
              all(f"| {row['id']} |" in cl for row in CLAIM_ROWS)
              and "| C02 |" in cl and "RLM-10 87.1% at score 3; 87.1% at score 4 | differs" in cl, cl[:200])
        rows_ = {x.split(" | ")[0][2:]: x for x in cl.splitlines() if x.startswith("| C")}
        check("claims list (D160 Q11, D304): each row gives both scores' values, from each score's reading (the "
              "fixture's multi-hop passes nothing at 4; verified pass fails 37.2% at 3 and 38.4% at 4; 5 of its 10 "
              "false-premise answers pass at 4); a row re-anchored on the agreed text compares the value at score 4, "
              "a retired row the value at 3",
              "| 69.8% against 87.1% at score 3; 0.0% against 87.1% at score 4 | differs (at score 4) |" in rows_["C49"]
              and "verified pass fails 37.2% of the 86 at score 3; 38.4% at score 4 | differs |" in rows_["C15"]
              and "ahead on 15 more of 85, 17.6 points at score 3; 74 more of 85, 87.1 points at score 4" in rows_["C48"]
              and "at score 4: single pass 7 of 10, multi-hop 0 of 10, verified pass 5 of 10," in rows_["C16"]
              and "at score 3; 75.6% at score 4 | differs (at score 4) |" in rows_["C41"]
              and claim_value(dict(id="t", claimed="0.0", m=("rate", "multi_hop"), t=4), R["res"])[1] == "matches"
              and claim_value(dict(id="t", claimed="0.0", m=("rate", "multi_hop")), R["res"])[1] == "differs",
              "\n".join(rows_.get(k, k) for k in ("C15", "C16", "C41", "C48", "C49"))[:900])

        def flip_parts(rid, t):
            """The score-t reading a flip row gives, as its 'S463 gives' cell writes it ("" when absent)."""
            cell = rows_[rid].split(" | ")[3]
            head = f"score {t} or more, " if cell.startswith(f"score {t} ") else f"; score {t} or more: "
            return cell.split(head, 1)[1].split("; score 4 or more: ")[0].split(": ", 1)[-1] if head in cell else ""
        check("claims list (D160 Q11, D304): a passage-verification row printed at score 3 (C54, C56, the letter's "
              "C66 and C67, all retired) gives the score-4 reading beside it, equal to the score-4 rows C57 and C58 and "
              "not the score-3 one; a row printed at 4 (C57, the letter's C65, C68, C69) gives no score-3 reading",
              flip_parts("C54", 4) == flip_parts("C57", 4) != "" and flip_parts("C56", 4) == flip_parts("C58", 4) != ""
              and flip_parts("C54", 4) != flip_parts("C54", 3)
              and all(flip_parts(r, 4) == flip_parts("C57", 4) for r in ("C65", "C66", "C67", "C69"))
              and flip_parts("C68", 4) == flip_parts("C58", 4)
              and all("score 3" not in rows_[r].split(" | ")[3] for r in ("C57", "C65", "C68", "C69")),
              "\n".join(rows_.get(k, k) for k in ("C54", "C56", "C57", "C58", "C65"))[:900])
    attempt("the draw-1 fixture", fixture_checks)

    # ---- the plate from the fixture, checked by S448; --no-plate and a refusal leave no stale file
    def plate_checks():
        plate = tmp / "d1" / "plate"
        Rp = rank(ns(f1, out=plate, no_plate=False), quiet=True)
        sd1 = next(plate.glob("Source Data Fig. 3*.xlsx"))
        pr_, summ_ = check_drawn(Rp["drawn"]["marks"], read_book(sd1), 1)
        check("check_drawn on the draw-1 plate: every tile, margin mark, dot and bar equals the workbook (no rerun "
              "marks from one draw)", not pr_ and "e rerun dots" not in summ_ and "a tiles" in summ_, "; ".join(pr_)[:300])
        b1 = read_book(sd1)
        r20 = next(r for r in b1["Fig. 3b"] if r.get("row_kind") == "refusal" and r["strategy"] == "rlm_20")
        bar20 = [e for e in Rp["drawn"]["marks"] if e["panel"] == "b" and e["kind"] == "margin bar"
                 and e["c"] == "rlm_20"]
        check("O2: RLM-20's 39 of 39 is drawn as one dashed bar from its one-sided lower bound (92.6) to 100",
              len(bar20) == 1 and bar20[0]["dashed"] and bar20[0]["artist"].get_linestyle() not in ("-", "solid")
              and abs(r20["bar_drawn_from_pct"] - 100 * full_bound(39)) < 1e-6 and r20["bar_drawn_to_pct"] == 100
              and abs(sorted(bar20[0]["artist"].get_xdata())[0] - 100 * full_bound(39)) < 1e-6
              and r20["bar_is"] == "one-sided 95% lower bound (dashed)", str(r20)[:300])
        if len(bar20) == 1:
            ln20 = bar20[0]["artist"]
            check("O2: RLM-20's dashed bar starts at its dot (100) and runs back to its lower bound, the mirror of a "
                  "0's bar from 0", list(ln20.get_xdata())[0] == 100, str(list(ln20.get_xdata())))
            xs20 = list(ln20.get_xdata())
            ln20.set_xdata(xs20[::-1])
            check("check_drawn catches a 100%'s dashed bar drawn from its lower bound towards the dot",
                  any("not from its dot" in x for x in check_drawn(Rp["drawn"]["marks"], b1, 1)[0]))
            ln20.set_xdata(xs20)
        r20["full_one_sided_lower_bound_pct"] = None
        check("check_drawn catches a dashed bar whose row has no one-sided bound (RLM-20's lower bound removed)",
              any("dashed where no one-sided bound" in x for x in check_drawn(Rp["drawn"]["marks"], b1, 1)[0]))
        s448 = run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", "3", "--dir",
                    str(plate)], cwd=ROOT)
        lines = [x for x in s448.stdout.splitlines() if x.strip()]
        fails = [x for x in lines if re.match(r"^R\d+\s+FAIL", x)]
        check("S448 passes the plate drawn from the fixture (no rule FAILs, exit 0)",
              s448.returncode == 0 and not fails, "; ".join(fails)[:600] or s448.stderr[-400:])
        if not quiet:
            for x in lines:
                if re.match(r"^R\d+\s+(FAIL|WARN)", x) or x.startswith(("S448", "lock")):
                    print(f"      S448 on the fixture plate: {x[:300]}")
        legend = (plate / "legend_draft.md").read_text()
        check("the legend states no result (no count of pairs that differ, no P value)",
              "differ at P" not in legend and "P <" not in legend and "pairs differ" not in legend)
        s5 = plate.parent / OUT_S5_NAME
        s448 = run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", "16",
                    "--supplementary", "--dir", str(s5)], cwd=ROOT)
        fails = [x for x in s448.stdout.splitlines() if re.match(r"^R\d+\s+FAIL", x)]
        check("S448 passes Supplementary Figure 16 drawn from the fixture, written beside the plate",
              s448.returncode == 0 and not fails, "; ".join(fails)[:600] or s448.stderr[-400:])
        sd5 = next(s5.glob("Supplementary Figure 16 data*.xlsx"))
        p5, s5s = check_drawn(Rp["drawn_s5"]["marks"], read_book(sd5), 1, "s5")
        check("check_drawn on Supplementary Figure 16: its 516 tiles at score 3, margin and butterfly equal its workbook",
              not p5 and "516 a tiles" in s5s, "; ".join(p5)[:300] or s5s)
        msg = refused(rank, types.SimpleNamespace(**{**vars(ns(f1, out=plate, no_plate=False)), "extra": None}), quiet=True)
        check("a plate without G2 and G6 is refused", "a plate needs --extra" in msg, msg[:200])
        before = {x.name: x.read_bytes() for x in plate.iterdir()}
        msg = refused(rank, ns(f1, out=plate, no_plate=False, draws="1,2"), quiet=True)
        after = {x.name: x.read_bytes() for x in plate.iterdir()}
        check("a refusal writes nothing: --out is byte for byte as before", "have no row" in msg and before == after,
              msg[:200])
        orig = S457.finish_plate

        def boom(*a, **k):
            raise SystemExit("Figure 3: texts past the page (selftest)")
        S457.finish_plate = boom
        try:
            msg = refused(rank, ns(f1, out=plate, no_plate=False), quiet=True)
        finally:
            S457.finish_plate = orig
        after = {x.name: x.read_bytes() for x in plate.iterdir()}
        check("a plate that fails to draw is a refusal and --out stays as before", "texts past the page" in msg
              and before == after and not any(x.name.startswith(".") for x in plate.parent.iterdir()), msg[:200])
        rank(ns(f1, out=plate, no_plate=True), quiet=True)
        left = sorted(x.name for x in plate.iterdir())
        check("--no-plate leaves only ranking.json, ranking_report.md and claims.md (no plate or legend of an earlier "
              "reading beside them)", left == ["claims.md", "ranking.json", "ranking_report.md"], str(left))
    attempt("the plate", plate_checks)

    # ---- panel b: concept recall read from L3's rows, regenerated from the records, drawn, and each row checked
    def cr_checks():
        f3c = build_fixture(tmp / "d3cr", (1, 2, 3))
        l3 = fixture_l3(f3c.parent, tmp / "l3" / "concept_recall.jsonl")
        l3d = fixture_l3_d181(f3c.parent, l3, tmp / "l3_d181")
        plate = f3c.parent / "plate_cr"
        Rc = rank(ns(f3c, draws="1,2,3", out=plate, no_plate=False, concept_recall=l3, concept_recall_d181=l3d),
                  quiet=True)
        rows = [json.loads(x) for x in l3.read_text().splitlines()]
        rows_d = [json.loads(x) for x in (l3d / "concept_recall.jsonl").read_text().splitlines()]
        cr_kind = f"{CR_NOT_DRAWN}: strategy"
        sheet = {r["strategy"]: r for r in Rc["book"]["Fig. 3a"] if r["row_kind"] == cr_kind}
        anc = Rc["crx"]["anchor"]["strategies"]
        ok, bad, ok_a, bad_a = True, [], True, []
        for c in CONFIGS:          # computed apart: plain floats from the rows, all answers of the three draws
            mine = [r for r in rows_d if r["config"] == c and r["group"] == "answerable"]
            v = [r["found"] / r["n_counted"] for r in mine]
            e = [r["found_exact_base"] / r["n_concepts"] for r in mine]
            nf = sum(1 for r in mine if r["status"] != "ok")
            got = sheet[c]
            if len(v) != 258 or abs(got["concept_recall_pct"] - 100 * sum(v) / 258) > 1e-6 \
                    or abs(got["concept_recall_exact_pct"] - 100 * sum(e) / 258) > 1e-6 \
                    or got["answers_failed_scored_0"] != nf:
                ok = False
                bad.append(f"{c}: {got['concept_recall_pct']} against {100 * sum(v) / max(len(v), 1)}, failed "
                           f"{got['answers_failed_scored_0']} against {nf}")
            lv = [r["found_loose"] / r["n_concepts"] for r in rows if r["config"] == c and r["group"] == "answerable"]
            if len(lv) != 258 or abs(anc[c]["concept_recall_loose_pct"] - 100 * sum(lv) / 258) > 1e-6:
                ok_a = False
                bad_a.append(f"{c}: anchor {anc[c]['concept_recall_loose_pct']} against {100 * sum(lv) / 258}")
        check("panel b (D188): each strategy's concept recall (D181's found over the concepts counted, and the exact "
              "substring value over every v2.5 concept) and its failed answers equal values computed apart from the "
              "L3_d181 rows", ok, "; ".join(bad)[:400])
        check("panel b (D188): the v2.4 anchor kept in ranking.json is L3's loose value of each strategy, computed "
              "apart from L3's rows", ok_a, "; ".join(bad_a)[:400])
        check("old panel b (D188): sheet 3a keeps D181's reading, not the loose one (the two differ on the fixture)",
              any(abs(sheet[c]["concept_recall_pct"] - anc[c]["concept_recall_loose_pct"]) > 1e-6 for c in CONFIGS)
              and any(r["found"] != r["found_loose_base"] for r in rows_d if r["group"] == "answerable"))
        check("panel b (D188): no committed v2.4 anchor is claimed on the fixture's L3 rows",
              Rc["crx"]["anchor"]["reproduced"] is None)
        means = sorted(sheet[c]["concept_recall_pct"] for c in CONFIGS)
        check("panel b: the fixture's strategies differ in concept recall (the check above is not of equal zeros)",
              means[0] < means[-1] and means[-1] > 0, str(means))
        s448 = run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", "3", "--dir",
                    str(plate)], cwd=ROOT)
        fails = [x for x in s448.stdout.splitlines() if re.match(r"^R\d+\s+FAIL", x)]
        check("S448 passes the three-draw plate", s448.returncode == 0 and not fails,
              "; ".join(fails)[:600] or s448.stderr[-400:])
        legend = (plate / "legend_draft.md").read_text()
        # Valerio, 8 Nov ("too long"): the split rows' n and the no-text count leave the legend for Source Data
        book3_ = read_book(next(plate.glob("Source Data Fig. 3*.xlsx")))
        n_split = {g: [r["n_questions"] for r in sorted(
            (r for r in book3_["Fig. 3f"] if r["row_kind"] == "n" and r["block"] == "All in scope"
             and r["question_group"] == g), key=lambda r: r["core_papers"])] for g in ("one", "many")}
        check("the legend reads its counts from the rows: 60 and 26, nine pairings; the split's n (15, 30, 60, 60 and "
              "7, 14, 26, 26) in sheet 3f, pointed to",
              "n = 60 one-paper, n = 26 many-paper" in legend and "split rows' n in Source Data" in legend
              and n_split == {"one": [15, 30, 60, 60], "many": [7, 14, 26, 26]}
              and "n = 9 pairings" in legend and "reruns" not in legend, str(n_split))
        n_x = sum(r["answers_failed_counted_as_fail"] for r in book3_["Fig. 3a"]
                  if r["row_kind"] == "strategy" and r["threshold"] == 4)
        check("the legend gives no count of answers with no text (Methods states the rule); sheet 3a's eight rows at "
              "score 4 hold it",
              "count as fails" not in legend and n_x >= 0, legend[:200])
        # Zhang RLM-10's stream failures, on made-up rows: the fixture's G6 has no failed answer
        b4_ = json.loads(json.dumps(Rc["book"], default=str))
        for r in b4_["Fig. 3a"]:
            if r["row_kind"] == "strategy" and r["strategy"] == "cap10":
                r["answers_failed_counted_as_fail"] = 2
        b4_["Fig. 3a"].append({"row_kind": "outcome: failed", "strategy": "cap10", "answers": 2, "answer_keys": "x; y",
                               "outcome": "root call root turn 5: status error: the stream ended without a finishReason"})
        leg4 = legend_text(Rc["res"], Rc["read"], [1, 2, 3], "x", Rc["out_t"], Rc["cost"], Rc["q78"], Rc["crx"], Rc["extra"],
                           b4_, read_fig3e(f3c.parent / "fig3e"))
        check("a legend over rows with Zhang RLM-10's failed answers still gives no count of them (Source Data holds it)",
              "count as fails" not in leg4, leg4[300:500])
        check("the legend says out-of-scope, vermilion and two-sided, names judge correctness (S456's regex), and names "
              "concept recall only as not drawn while S456 asks for it",
              fn.OUT_OF_SCOPE_QUESTIONS in legend and fn.VERMILION in legend and "two-sided 95%" in legend
              and "not-answerable" not in legend and "judged by " + JUDGE + " for judge correctness" in legend
              and (not LEGEND_CONCEPT_RECALL or " and concept recall, not drawn" in legend))
        check("the legend names no mark the plate no longer draws, and says only what the rows hold on failures",
              "Grey dots, the strategy" not in legend and "grey dots, the strategy" not in legend
              and "band" not in legend.split("**Figure 3")[1] and "Server faults" not in legend
              and "Above, multiples" not in legend)
        # check_drawn: the three-draw plate's marks against its workbook, then against workbooks with one value changed
        sd3 = next(plate.glob("Source Data Fig. 3*.xlsx"))
        book3 = read_book(sd3)
        pr_, summ_ = check_drawn(Rc["drawn"]["marks"], book3, 3)
        check("check_drawn on the three-draw plate: 688 tiles of a and no margin, 234 of b, 10 bars of c with their 90 "
              "pairing dots and no rerun mark, 516 dots of d, its 36 group marks and its cross, 68 cells of f and no "
              "grey cell (FIG3F O2), 6 marks of e (I of five sources and the reference, D289) and no reading equal the workbook",
              not pr_ and all(x in summ_ for x in ("688 a tiles", "234 b tiles", "36 d group marks", "516 d dots",
                                                     "10 c bars", "90 c pairing dots", "1 d cross", "68 f cells",
                                                     "688 a clock dots", "8 a clock means",
                                                     "6 e marks")) and "rerun" not in summ_ and "grey" not in summ_
              and "a margin" not in summ_ and "e readings" not in summ_, "; ".join(pr_)[:300] or summ_)
        drawn3 = Rc["drawn"]["marks"]
        # D218 (2), worked apart: the fixture's verified pass makes 2 calls of 3.0 s and waits 7.0 s for the local server
        vq = [r for r in book3["Fig. 3a"] if r["row_kind"] == MARGIN_Q_KIND and r["strategy"] == "verified_pass"]
        vm = next(r for r in book3["Fig. 3a"] if r["row_kind"] == MARGIN_KIND and r["strategy"] == "verified_pass")
        check("3a's clock margin (D218): verified pass's 86 questions at 6.0 s less the wait and 13.0 s with it, the "
              "mean printed '6 s'",
              len(vq) == 86 and all(abs(r["clock_less_wait_s_mean_over_draws"] - 6.0) < 1e-9
                                    and abs(r["clock_s_mean_over_draws"] - 6.0 - FIXTURE_WAIT) < 1e-9 for r in vq)
              and vm["printed"] == "6 s" and abs(vm["clock_s_mean_with_wait"] - 13.0) < 1e-9, str(vm)[:200])
        # Valerio's plate notes of 2 November, read from the artists
        mx = [e for e in drawn3 if e["kind"] == "margin dot"]
        vw = {tuple(float(v) for v in e["ax"].spines["bottom"].get_bounds()) for e in mx}
        lb = {t.get_text() for e in mx for t in (e["ax"].get_xticklabels()[0], e["ax"].get_xticklabels()[-1])}
        check("3b: its margin's axis line runs 50 to 100, labelled 50 and 100 at its ends; 3a draws no margin (D216)",
              vw == {(50.0, 100.0)} and lb == {"50", "100"} and {e["panel"] for e in mx} == {"b"}, f"{vw} {lb}")
        gm3 = [e for e in drawn3 if e["kind"] == "group mark"]
        check("3d (D216): per strategy three groups at two thresholds, white-filled at score 3 and white-edged at 4, "
              "no interval or mean mark, a cross with no bar, the key on one line",
              len(gm3) == 36 and all(
                  (e["artist"].get_markerfacecolor() == hs.WHITE) == (e["t"] == 3) for e in gm3)
              and not [e for e in drawn3 if e["kind"] in ("mean", "calls bar", "pass bar", "cross bar")]
              and [t.get_text() for t in (e["text"] for e in drawn3 if e["kind"] == "key text" and e["panel"] == "d")]
              == ["All 86", "One paper 60", "Many papers 26", "score 3", fn.MATCHED_BUDGET])
        check("3c: no rerun dots, no band, no 'single pass rerun' row",
              not [e for e in drawn3 if e["panel"] == "c" and e["kind"] in ("rerun dots", "band")]
              and "single_pass" not in [e["c"] for e in drawn3 if e["panel"] == "c" and e["kind"] == "row label"])
        txt = [t.get_text() for t in Rc["drawn"]["fig_texts"]]
        check("the key reads 'Draws passed:'; 3d prints only each strategy's name (no time, tokens or 'reference'); 3f's key "
              "has no 'interval excludes 0' or 'run-to-run row'",
              "Draws passed:" in txt and not any(("×" in x or "tokens" in x or x == "reference"
                                                  or x in ("interval excludes 0", "run-to-run row", "one rerun")
                                                  or "or refused" in x) for x in txt), str(txt)[:300])
        check("FIG3F O2 (rulings page 6 Nov): 3f draws no run-to-run row, its sheet holds no run-to-run rows and the "
              "legend names no grey row",
              "run-to-run" not in txt and not [e for e in Rc["drawn"]["marks"] if e["panel"] == "f" and e["kind"] == "grey"]
              and not [r for r in Rc["book"]["Fig. 3f"] if str(r.get("row_kind", "")).startswith("run-to-run")]
              and "Grey row" not in legend and "run-to-run" not in legend)
        v_ = margin_layout([60.0, 20.0, 70.0], 10.0, 60.0)
        mm_ = [w / (lm[1] - lm[0]) for _, w, lm in v_]
        check("margin_layout: a value below 50 gives its column room at one shared scale, the columns stay apart and in "
              "the width, and a column with none starts its axes 2.5 points below 50",
              v_[1][2] == (17.5, 102.5) and v_[0][2] == v_[2][2] == (47.5, 102.5) and max(mm_) - min(mm_) < 1e-9
              and v_[0][0] == 10.0 and abs(v_[2][0] + v_[2][1] - 60.0) < 1e-9
              and v_[0][0] + v_[0][1] < v_[1][0] and v_[1][0] + v_[1][1] < v_[2][0]
              and margin_layout([60.0], 10.0, 21.0) == [(10.0, 11.0, (47.5, 102.5))], str(v_))

        def moved(pick, change):
            """check_drawn on the plate with one artist moved, then the artist put back."""
            e_ = next(x for x in drawn3 if pick(x))
            undo = change(e_)
            got = check_drawn(drawn3, book3, 3)[0]
            undo()
            return got

        def set_y(a_, v):
            old = a_.get_y()
            a_.set_y(v)
            return lambda: a_.set_y(old)

        def set_x(a_, v):
            old = a_.get_x()
            a_.set_x(v)
            return lambda: a_.set_x(old)

        def set_yd(a_, v):
            old = list(a_.get_ydata())
            a_.set_ydata([v] * len(old))
            return lambda: a_.set_ydata(old)

        def set_xd(a_, f):
            old = list(a_.get_xdata())
            a_.set_xdata([x * f for x in old])
            return lambda: a_.set_xdata(old)

        def set_txt(t_, v):
            old = t_.get_text()
            t_.set_text(v)
            return lambda: t_.set_text(old)

        for name, pick, change in (
                ("a tile on another row", lambda x: x["kind"] == "tile" and x["panel"] == "a" and x["c"] == "single_pass",
                 lambda e_: set_y(e_["artist"], e_["artist"].get_y() + A_ROW)),
                ("a 3d many-paper mark at another rate", lambda x: x["kind"] == "group mark" and x["g"] == "many"
                 and x["t"] == 4, lambda e_: set_yd(e_["artist"], e_["artist"].get_ydata()[0] + 2.0)),
                ("a 3d one-paper mark at score 3 at another rate", lambda x: x["kind"] == "group mark"
                 and x["g"] == "one" and x["t"] == 3, lambda e_: set_yd(e_["artist"], e_["artist"].get_ydata()[0] - 2.0)),
                ("a 3d key entry with another n", lambda x: x["kind"] == "key text" and x["text"].get_text().startswith("One"),
                 lambda e_: set_txt(e_["text"], "One paper 59")),
                ("a margin bar on another row", lambda x: x["kind"] == "margin bar" and x["panel"] == "b",
                 lambda e_: set_yd(e_["artist"], e_["artist"].get_ydata()[0] + 2.0)),
                ("a 3f cell in another column", lambda x: x["kind"] == "cell", lambda e_: set_x(e_["artist"], e_["artist"].get_x() + E_CP)),
                ("a 3f cell on another row", lambda x: x["kind"] == "cell", lambda e_: set_y(e_["artist"], e_["artist"].get_y() + E_RP)),
                ("a 3f row label swapped", lambda x: x["panel"] == "f" and x["kind"] == "row label" and x["rk"][1] == "one",
                 lambda e_: set_txt(e_["text"], "RLM-10, many papers")),
                ("a 3a clock mean at another time", lambda x: x["kind"] == "clock mean" and x["c"] == "rlm_10",
                 lambda e_: set_xd(e_["artist"], 1.2)),
                ("a 3a clock dot set at another time", lambda x: x["kind"] == "clock dots" and x["c"] == "cap10",
                 lambda e_: set_xd(e_["artist"], 0.8)),
                ("a 3a clock dot set beyond its row", lambda x: x["kind"] == "clock dots" and x["c"] == "single_pass",
                 lambda e_: set_yd(e_["artist"], e_["artist"].get_ydata()[0] + A_ROW)),
                ("a 3a clock value with another number", lambda x: x["kind"] == "clock value" and x["c"] == "verified_pass",
                 lambda e_: set_txt(e_["text"], "1 s")),
                ("a 3a row label swapped", lambda x: x["panel"] == "a" and x["kind"] == "row label" and x["c"] == "rlm_5",
                 lambda e_: set_txt(e_["text"], "RLM-10")),
                ("a 3a block head swapped", lambda x: x["panel"] == "a" and x["kind"] == "block head" and x["block"] == 0,
                 lambda e_: set_txt(e_["text"], "Many papers")),
                ("a 3d name on another scatter", lambda x: x["kind"] == "name" and x["c"] == "rlm_5",
                 lambda e_: set_txt(e_["text"], "RLM-10")),
                ("a 3f size head on another column", lambda x: x["kind"] == "size head" and x["k"] == 0,
                 lambda e_: set_txt(e_["text"], "50"))):
            got_ = moved(pick, change)
            check(f"check_drawn catches {name}, from the artist's own position or text", bool(got_), "no problem reported")
        s5m = Rc["drawn_s5"]["marks"]
        book5 = read_book(next((plate.parent / OUT_S5_NAME).glob("Supplementary Figure 16 data*.xlsx")))
        p53, s53 = check_drawn(s5m, book5, 3, "s5")
        check("Supplementary Figure 16b keeps its rerun dots and band: 72 dots, 2 bands",
              not p53 and "72 b rerun dots" in s53 and "2 b band" in s53, "; ".join(p53)[:300] or s53)
        b5 = json.loads(json.dumps(book5, default=str))
        next(r for r in b5[S5_SHEET["b"]] if r.get("row_kind") == NOISE_KIND)["pass_on_1_fail_on_2"] += 1
        check("check_drawn catches a changed rerun count on Supplementary Figure 16b",
              bool(check_drawn(s5m, b5, 3, "s5")[0]), "no problem reported")
        fake = dict(next(e for e in s5m if e["kind"] == "rerun dots"))
        check("check_drawn refuses a rerun mark on 3c", any("rerun marks" in x for x in check_drawn(
            [*drawn3, {**fake, "panel": "c"}], book3, 3)[0]))

        def tamper(sheet, kind, field, fn, pick=lambda r: True):
            b2 = json.loads(json.dumps(book3, default=str))
            r = next(r for r in b2[sheet] if r.get("row_kind") == kind and pick(r))
            r[field] = fn(r[field])
            return check_drawn(Rc["drawn"]["marks"], b2, 3)[0]
        for name, args_ in (
                ("a tile's draws passed", ("Fig. 3a", TILE_KIND, "draws_passed", lambda v: (v + 1) % 4,
                                           lambda r: r["draws_scored"] == 3)),
                ("two questions' places in a's order", ("Fig. 3a", ORDER_KIND, "question_id",
                                                        lambda v: sorted(qa)[0] if v != sorted(qa)[0] else sorted(qa)[1])),
                ("a's margin rate", ("Fig. 3a", "strategy", "pass_rate_pct", lambda v: v - 1)),
                ("a's open dot at score 3", ("Fig. 3a", "strategy", "pass_rate_pct", lambda v: v - 1,
                                             lambda r: r["threshold"] == 3)),
                ("a's many-paper rate", ("Fig. 3a", GROUP_KIND, "pass_rate_pct", lambda v: v - 1,
                                         lambda r: r["threshold"] == 4 and r["question_group"] == "many")),
                ("a tile of the package row", ("Fig. 3a", TILE_KIND, "draws_passed", lambda v: (v + 1) % 4,
                                               lambda r: r["strategy"] == "cap10")),
                ("b tile's draws refused", ("Fig. 3b", TILE_KIND, "draws_refused", lambda v: (v + 1) % 4)),
                ("d question's calls beyond the jitter", ("Fig. 3d", CQ_KIND, "calls_per_answer_question_mean",
                                                          lambda v: v * 1.2)),
                ("d's strategy point", ("Fig. 3d", "strategy (plotted)", "pass_rate_t4_pct", lambda v: v + 1)),
                ("d's one-paper calls", ("Fig. 3d", GROUP_D_KIND, "calls_mean", lambda v: v * 1.1,
                                         lambda r: r["question_group"] == "one")),
                ("d's many-paper rate at score 3", ("Fig. 3d", GROUP_D_KIND, "pass_rate_t3_pct", lambda v: v - 1,
                                                    lambda r: r["question_group"] == "many")),
                ("a question's type on d", ("Fig. 3d", CQ_KIND, "question_type",
                                            lambda v: "many" if v == "one" else "one")),
                ("d's cross", ("Fig. 3d", CROSS_KIND, "pass_rate_t4_pct", lambda v: v - 1)),
                ("c's harmed mean", ("Fig. 3c", FLIP_KIND, "harmed_mean_over_pairings", lambda v: v + 0.5)),
                ("c pairing count", ("Fig. 3c", PAIR_KIND, "harmed", lambda v: v + 1)),
                ("f cell's difference", ("Fig. 3f", "cell", "d_pp", lambda v: v + 3.0)),
                ("e's mark", ("Fig. 3e", E3_KIND, "d_pp", lambda v: v + 1.0,
                              lambda r: r["measure"] == "interaction")),
                ("e's interval end", ("Fig. 3e", E3_KIND, "ci95_lo_pp", lambda v: v - 1.0,
                                      lambda r: r["measure"] == "interaction" and r["role"] == "beside")),
                ("e's reference mark", ("Fig. 3e", E3_KIND, "d_pp", lambda v: v + 1.0,
                                        lambda r: r["role"] == "reference" and r["measure"] == "interaction")),
                ("e's source name", ("Fig. 3e", E3_KIND, "source_label", lambda v: v + "x",
                                     lambda r: r["measure"] == "interaction")),
                ("f cell's printed size", ("Fig. 3f", "cell", "d_size_pp", lambda v: v + 3.0)),
                ("f cell's frame", ("Fig. 3f", "cell", "interval_excludes_0", lambda v: "no" if v == "yes" else "yes")),
                ("a clock dot's value", ("Fig. 3a", MARGIN_Q_KIND, "clock_less_wait_s_mean_over_draws",
                                         lambda v: v * 1.05, lambda r: r["strategy"] == "verified_pass")),
                ("a clock dot of Zhang RLM-10", ("Fig. 3a", MARGIN_Q_KIND, "clock_less_wait_s_mean_over_draws",
                                                  lambda v: v + 1.0, lambda r: r["strategy"] == "cap10")),
                ("a clock mean", ("Fig. 3a", MARGIN_KIND, "clock_less_wait_s_mean", lambda v: v + 1.0,
                                  lambda r: r["strategy"] == "matched_budget")),
                ("a clock mean's printed value", ("Fig. 3a", MARGIN_KIND, "printed", lambda v: "1 s"))):
            got_ = tamper(*args_)
            check(f"check_drawn catches a changed workbook value: {name}", bool(got_), "no problem reported")
        # 3e (4 November): S518's reading is not drawn, and each mark sits on the axes whose x is what it computes
        e_m = next(e for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] == "mark"
                   and e.get("axis") == "I")
        rd_ = next(r["reading"] for r in book3["Fig. 3e"] if r.get("row_kind") == E3_KIND and r.get("reading"))
        t_rd = e_m["ax"].figure.text(0.5, 0.5, rd_)
        bad_r = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        t_rd.remove()
        check("check_drawn catches S518's reading drawn on the plate (3e draws no reading)",
              any("reading drawn" in x for x in bad_r), str(bad_r[:2]))
        e_m["axis"] = "D"
        bad_ax = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        e_m["axis"] = "I"
        check("check_drawn catches I's mark recorded on the left axes (its x RLM-10 minus single pass)",
              any("the axis whose x" in x for x in bad_ax), str(bad_ax[:2]))
        v_e = next(e for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] == "value")
        tv0 = v_e["text"].get_text()
        v_e["text"].set_text(tv0 + "9")
        bad_v = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        v_e["text"].set_text(tv0)
        check("check_drawn catches a 3e value printing another number than its I row gives (D289)",
              any("on its row" in x for x in bad_v), str(bad_v[:2]))
        # the printed value (D289) also catches a changed d_pp, so the mark is moved on its artist alone
        m_e = next(e for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] == "mark")
        mx0 = list(m_e["artist"].get_xdata())
        m_e["artist"].set_xdata([mx0[0] + 1.0])
        bad_m = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        m_e["artist"].set_xdata(mx0)
        check("check_drawn catches a 3e mark drawn off its I value, its printed value unchanged (D289)",
              any("the mark at" in x for x in bad_m), str(bad_m[:2]))
        check("3e (D289) draws I alone on one axes, no reading, no group head or key, the reference row first",
              not check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
              and {e["axis"] for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] == "mark"} == {"I"}
              and not [e for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] in ("role head", "key text")]
              and min(e3_layout([(r["source"], r["role"]) for r in book3["Fig. 3e"] if r.get("row_kind") == E3_KIND])[0]
                      .items(), key=lambda kv: kv[1])[0] == "gemini-3-flash-preview"
              and not [e for e in Rc["drawn"]["marks"] if e["panel"] == "e" and e["kind"] == "verdict"]
              and any(r.get("role") == "reference" for r in book3["Fig. 3e"]))
        # 3f's colour and text guard each other on a changed row, so each is changed on the drawn artist alone
        cell_e = next(e for e in Rc["drawn"]["marks"] if e["panel"] == "f" and e["kind"] == "cell")
        fc0, tx0 = cell_e["artist"].get_facecolor(), cell_e["text"].get_text()
        cell_e["artist"].set_facecolor("#000000")
        bad_c = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        cell_e["artist"].set_facecolor(fc0)
        cell_e["text"].set_text(tx0 + "9")
        bad_t = check_drawn(Rc["drawn"]["marks"], book3, 3)[0]
        cell_e["text"].set_text(tx0)
        check("check_drawn catches a 3f cell drawn in another colour than its d_pp gives",
              any("its d_pp" in x for x in bad_c), str(bad_c[:2]))
        check("check_drawn catches a 3f cell printing another number than its row gives",
              any("the row gives" in x for x in bad_t), str(bad_t[:2]))
        # two tiles of one row trade their draws passed: the row's mean is unchanged, so only the colours tell
        b2 = json.loads(json.dumps(book3, default=str))
        row_ = [r for r in b2["Fig. 3a"] if r.get("row_kind") == TILE_KIND and r["threshold"] == 4
                and r["strategy"] == "rlm_10" and r["draws_scored"] == 3]
        hi_ = next(r for r in row_ if r["draws_passed"] == 3)
        lo_ = next(r for r in row_ if r["draws_passed"] < 3)
        hi_["draws_passed"], lo_["draws_passed"] = lo_["draws_passed"], 3
        check("check_drawn catches two tiles of one row that trade their draws passed (same mean, other colours)",
              bool(check_drawn(Rc["drawn"]["marks"], b2, 3)[0]), "no problem reported")
        # the two plot orders, computed apart from the shares (D127: easiest left; D130: most refused left), 3a's within
        # the one-paper then the many-paper questions (D200)
        sh3 = Rc["res"]["answerable"]
        k_ = {(t, q): sum(1 for c in CONFIGS for d in (1, 2, 3) if sh3[t]["shares"][c][q][1][d] == 1)
              for t in THRESHOLDS for q in qa}
        kd_ = S511.questions()
        want_a = [q for g in ("one", "many")
                  for q in sorted((x for x in qa if kd_[x]["kind"] == g), key=lambda q: (-k_[(4, q)], -k_[(3, q)], q))]
        got_a = [r["question_id"] for r in sorted((r for r in book3["Fig. 3a"] if r["row_kind"] == ORDER_KIND),
                                                 key=lambda r: r["plot_position"])]
        qn_ = sorted(q for q, g in groups.items() if g == "not_answerable")
        shn_ = Rc["res"]["refusal"][REFUSAL_T]["shares"]
        want_d = sorted(qn_, key=lambda q: (-sum(1 for c in CONFIGS for d in (1, 2, 3) if shn_[c][q][1][d] == 1), q))
        got_d = [r["question_id"] for r in sorted((r for r in book3["Fig. 3b"] if r["row_kind"] == ORDER_KIND),
                                                 key=lambda r: r["plot_position"])]
        check("panel a's sheet lists the 86 answerable ids in plot order (one-paper then many-paper; in each, draws "
              "passed at 4, then 3, then id), panel b's the 39 out-of-scope ids (draws refused, then id), computed apart",
              got_a == want_a and len(got_a) == 86 and got_d == want_d and len(got_d) == 39)
        s5o = [r["question_id"] for r in sorted((r for r in read_book(next((plate.parent / OUT_S5_NAME).glob(
            "Supplementary Figure 16 data*.xlsx")))[S5_SHEET["a"]] if r["row_kind"] == ORDER_KIND),
            key=lambda r: r["plot_position"])]
        check("Supplementary Figure 16a keeps Figure 3a's question order", s5o == got_a)
        one = sorted(q for q in qa if kd_[q]["kind"] == "one")
        ga = next(r for r in book3["Fig. 3a"] if r["row_kind"] == GROUP_KIND and r["strategy"] == "rlm_10"
                  and r["threshold"] == 4 and r["question_group"] == "one")
        shg = sh3[4]["shares"]["rlm_10"]
        wg = [shg[q][0] for q in one if shg[q][0] is not None]
        check("3a's one-paper rate of RLM-10 is the mean of its question shares, computed apart",
              abs(ga["pass_rate_pct"] - float(100 * sum(wg) / len(wg))) < 1e-6)
        st_all = [r for r in book3["Fig. 3a"] if r["row_kind"] == "strategy"]
        check("'strategy' rows hold question group all only, so S473 and S480 read one row per strategy and threshold",
              {r["question_group"] for r in st_all} == {"all"} and len(st_all) == 8 * 2
              and len({(r["strategy"], r["threshold"]) for r in st_all}) == 16)
        lf = [r for r in book3["Fig. 3d"] if r["row_kind"] == MULT_KIND]
        ca = Rc["cost"]["answerable"]
        rt = next(r for r in lf if r["strategy"] == "rlm_10" and r["measure"] == "model-call time")
        rk2 = next(r for r in lf if r["strategy"] == "rlm_10" and r["measure"] == "tokens")
        cells_ = Rc["read"]["cells"]

        def perq(c, m):
            return [sum(cells_[(c, q, d)]["cost"][m] for d in (1, 2, 3)) / 3 for q in qa]
        med = lambda v: float(np.median(v))                                         # noqa: E731
        check("the multiples are ratios of means of model-call time, and of means and medians of tokens, per question "
              "the mean over draws, computed apart",
              abs(rt["ratio_of_means"] - sum(perq("rlm_10", "model_s")) / sum(perq("single_pass", "model_s"))) < 1e-6
              and abs(rk2["ratio_of_means"] - sum(perq("rlm_10", "tokens")) / sum(perq("single_pass", "tokens"))) < 1e-6
              and abs(rk2["ratio_of_medians"] - med(perq("rlm_10", "tokens")) / med(perq("single_pass", "tokens"))) < 1e-6
              and ca["rlm_10"]["model_s"]["mean"] > 0)
        rv = next(r for r in lf if r["strategy"] == "verified_pass" and r["measure"] == "model-call time")
        check("verified pass's time multiple leaves out the wait for the local server (model-call time, not the clock)",
              abs(rv["ratio_of_means"] - sum(perq("verified_pass", "model_s")) / sum(perq("single_pass", "model_s"))) < 1e-6
              and abs(rv["ratio_of_means"] - sum(perq("verified_pass", "clock_s")) / sum(perq("single_pass", "clock_s"))) > 1e-3)
        check("the tiles lighten with draws passed: 3 of 3 yellow (D171 (1)), 0 of 3 the dark end",
              tile_colours(3)[3] == hs.cividis_levels(4)[3].upper() and tile_colours(3)[0] == hs.cividis_levels(4)[0].upper()
              and tile_colours(3)[0] != tile_colours(3)[3])
        check("the stamp counts answers read from a final-key row, and the file name and the stamp agree: G1's 1,350 on "
              "unchanged questions here, and the fixture's G2, G6 and G4",
              "1,350" in Rc["stamp"] and "of 21,402 answers" in Rc["stamp"]
              and next(plate.glob("Figure 3 *.pdf")).name.split(", ")[1].split(" of ")[1].startswith("21402"))
        # D154: the pass rate is score 4 (PRIMARY), 3 the relaxed threshold, 4 first wherever both appear
        st_ = [r for r in book3["Fig. 3a"] if r["row_kind"] == "strategy"]
        s4_ = Rc["res"]["answerable"][4]["summary"]
        rk_ = {c: 1 + sum(1 for o in CONFIGS if (s4_[o]["rate_x"] or 0) > (s4_[c]["rate_x"] or 0)) for c in CONFIGS}
        check("D154: Fig. 3a's strategy rows give threshold 4 first, each of the six ranked by the pass rate at 4 "
              "(computed apart), G2 and G6 unranked, and the report's first sentence reads score 4",
              [r["threshold"] for r in st_[:8]] == [4] * 8
              and all(r.get("rank_by_mean_threshold_4") == rk_.get(r["strategy"]) for r in st_)
              and summary_lines(Rc["res"], Rc["res"], dtext_of([1, 2, 3])).startswith("At judge score 4 or more"))
        bx_ = {r["strategy"]: r for r in book3["Fig. 3a"] if r["row_kind"] == f"{CR_NOT_DRAWN}: {BOX_KIND}"}
        v_ = sorted(r["concept_recall_question_pct"] for r in book3["Fig. 3a"]
                    if r["row_kind"] == f"{CR_NOT_DRAWN}: {BQ_KIND}" and r["strategy"] == "rlm_10")
        check("old panel b's box row, kept in sheet 3a, is the median and range of its 86 question values (computed apart)",
              len(v_) == 86 and abs(bx_["rlm_10"]["median_pct"] - (v_[42] + v_[43]) / 2) < 1e-6
              and bx_["rlm_10"]["min_pct"] == v_[0] and bx_["rlm_10"]["max_pct"] == v_[-1])

        def tampered(name, fn, want):
            d = tmp / f"l3_{len(results)}"
            d.mkdir()
            rr = [json.loads(x) for x in l3.read_text().splitlines()]
            hd = json.loads((l3.parent / "header.json").read_text())
            rr, hd = fn(rr, hd)
            (d / "concept_recall.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rr))
            (d / "header.json").write_text(json.dumps(hd))
            msg = refused(rank, ns(f3c, draws="1,2,3", out=f3c.parent / "plate_x",
                                   concept_recall=d / "concept_recall.jsonl", concept_recall_d181=l3d), quiet=True)
            check(f"--concept-recall refused: {name}", want in msg, msg[:200])

        def first(rr, grp):
            return next(i for i, r in enumerate(rr) if r["group"] == grp and r["draw"] == 1 and r["status"] == "ok")

        def bump(rr, hd):
            i = first(rr, "answerable")
            rr[i]["found_loose"] = (rr[i]["found_loose"] + 1) % (rr[i]["n_concepts"] + 1)
            return rr, hd

        def other_answer(rr, hd):
            rr[first(rr, "answerable")]["answer_sha256"] = "0" * 64
            return rr, hd

        def na_value(rr, hd):
            i = first(rr, "not_answerable")
            rr[i].update(concept_recall_loose=0.5, reason=None)
            return rr, hd

        def drop(rr, hd):
            return [r for r in rr if not (r["config"] == "rlm_10" and r["draw"] == 1)], hd

        def twice(rr, hd):
            return rr + [rr[0]], hd

        def other_row(rr, hd):
            return rr, {**hd, "plan_row": "L1"}

        def rounded(rr, hd):
            i = first(rr, "answerable")
            rr[i]["concept_recall_loose"] = round(rr[i]["concept_recall_loose"] + 0.01, 4)
            return rr, hd
        tampered("a count that does not reproduce from the record", bump, "does not reproduce from its record")
        tampered("a row of another answer than the one judged", other_answer, "another answer than the record")
        tampered("a value on a not-answerable question (Rule 8)", na_value, "(Rule 8)")
        tampered("a missing row", drop, "have no row")
        tampered("an answer with two rows", twice, "have two rows")
        tampered("a header of another plan row", other_row, "not S471's L3 header")
        tampered("a stored value that is not its count over the concepts", rounded, "does not reproduce")

        # D188: the D181 folder, each alteration refused before anything is written
        def tampered_d(name, fn, want):
            d = tmp / f"l3d_{len(results)}"
            d.mkdir()
            rr = [json.loads(x) for x in (l3d / "concept_recall.jsonl").read_text().splitlines()]
            hd = json.loads((l3d / "header.json").read_text())
            rr, hd = fn(rr, hd)
            (d / "concept_recall.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rr))
            (d / "header.json").write_text(json.dumps(hd))
            msg = refused(rank, ns(f3c, draws="1,2,3", out=f3c.parent / "plate_x", concept_recall=l3,
                                   concept_recall_d181=d), quiet=True)
            check(f"--concept-recall-d181 refused: {name}", want in msg, msg[:200])
        k24_, k25_ = JR.S512.keys()
        same_ = {q for q in k24_ if k24_[q].get("expected_concepts") == k25_[q].get("expected_concepts")}

        def pick(rr, unchanged):
            return next(i for i, r in enumerate(rr) if r["group"] == "answerable" and r["status"] == "ok"
                        and (r["question_id"] in same_) == unchanged and r["n_concepts"] > 1)

        def d_base(rr, hd):
            i = pick(rr, True)
            rr[i]["found_loose_base"] = (rr[i]["found_loose_base"] + 1) % (rr[i]["n_concepts"] + 1)
            return rr, hd

        def d_value(rr, hd):
            i = pick(rr, False)
            rr[i]["concept_recall"] = round(rr[i]["concept_recall"] + 0.01, 4)
            return rr, hd

        def d_none(rr, hd):
            i = pick(rr, False)
            rr[i].update(concept_recall=None, n_counted=0)
            return rr, hd

        def d_other(rr, hd):
            rr[pick(rr, False)]["answer_sha256"] = "0" * 64
            return rr, hd
        tampered_d("a header that is provisional", lambda rr, hd: (rr, {**hd, "provisional": True}),
                   "not S471's final D181 reading")
        tampered_d("a header on key v2.4", lambda rr, hd: (rr, {**hd, "key": {"sha256": JR.S512.KEY24_SHA256}}),
                   "not S471's final D181 reading")
        tampered_d("a header on another answer copy", lambda rr, hd: (rr, {**hd, "inputs": {"manifest_sha256": "x"}}),
                   "not S471's final D181 reading")
        tampered_d("a row missing", lambda rr, hd: (rr[1:], hd), "the rows give")
        tampered_d("a row of another answer", d_other, "not L3's answer one for one")
        tampered_d("a loose base differing from L3 on a question whose concepts v2.5 left unchanged", d_base,
                   "the loose base on concepts v2.5 left unchanged is not L3's loose value")
        tampered_d("a stored value that is not found over the concepts counted", d_value, "have no D181 value")
        tampered_d("an answerable row with no concept counted", d_none, "have no D181 value")
        msg = refused(read_concept_recall_d181, l3d, read_concept_recall(l3, read_answers(
            [f3c.parent / "k1_runs" / "runs", f3c.parent / "g1r15_runs" / "runs"])[0], groups, [1, 2, 3]),
            groups, [1, 2, 3], pins={"concept_recall.jsonl": "0" * 64, "header.json": "0" * 64})
        check("--concept-recall-d181 refused: a file at a sha256 other than the one pinned", "pinned (D188)" in msg,
              msg[:200])

        # D188: check_cr_anchor on the committed L3's sha256, draws 1 to 3; another input claims no anchor
        def lo_of(vals):
            return {"value": {"summary": {c: {"rate": v[0] / 100, "lo": v[1] / 100, "hi": v[2] / 100}
                                          for c, v in vals.items()}},
                    "exact": {"summary": {c: {"rate": v[3] / 100} for c, v in vals.items()}},
                    "failed": {c: ["k"] * v[4] for c, v in vals.items()}}
        cr_c = {"sha256": L3_SHA256}
        check("check_cr_anchor accepts the committed v2.4 panel b on the committed L3 rows, draws 1 to 3",
              (check_cr_anchor(lo_of(CR_ANCHOR_V24), cr_c, [1, 2, 3]) or "").startswith("panel b's v2.4 anchor"))
        for i_, what in enumerate(("mean", "interval low end", "interval high end", "exact value", "failed answers")):
            bent = {c: tuple(x + (1 if j == i_ and c == "rlm_10" else 0) for j, x in enumerate(v))
                    for c, v in CR_ANCHOR_V24.items()}
            msg = refused(check_cr_anchor, lo_of(bent), cr_c, [1, 2, 3])
            check(f"check_cr_anchor refuses a v2.4 panel b whose {what} differs", "anchor not reproduced" in msg,
                  msg[:200])
        check("check_cr_anchor claims no anchor on other L3 rows or on one draw",
              check_cr_anchor(lo_of(CR_ANCHOR_V24), {"sha256": "0" * 64}, [1, 2, 3]) is None
              and check_cr_anchor(lo_of(CR_ANCHOR_V24), cr_c, [1]) is None)
    attempt("panel b", cr_checks)

    # ---- input mutants: each must be refused, with its own message
    def mutate(name, fn, want):
        d = tmp / f"m_{len(results)}"
        shutil.copytree(tmp / "d1", d, ignore=shutil.ignore_patterns("plate"))
        col = d / "g1_collect.jsonl"
        side = col.with_name(col.name + ".json")
        side.write_text(side.read_text().replace(str(tmp / "d1"), str(d)))
        kw = fn(d, col)
        kw = kw if isinstance(kw, dict) else {}
        msg = refused(rank, ns(col, **kw), quiet=True)
        check(f"input mutant ({name}): refused", want in msg, msg[:300])

    def rows_edit(col, f, keep_count=True):
        rows = [json.loads(x) for x in col.read_text().splitlines() if x.strip()]
        rows = f(rows)
        col.write_text("".join(json.dumps(r) + "\n" for r in rows))
        side = col.with_name(col.name + ".json")
        s_ = json.loads(side.read_text())
        if keep_count:
            s_["rows"] = len(rows)
        side.write_text(json.dumps(s_))

    def side_edit(col, **kv):
        side = col.with_name(col.name + ".json")
        side.write_text(json.dumps({**json.loads(side.read_text()), **kv}))

    def jsonl_edit(p, f):
        rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        p.write_text("".join(json.dumps(r) + "\n" for r in f(rows)))

    def input_mutants():
        g1 = lambda d, c: d / "out" / "judge" / run_of(c)                          # noqa: E731
        mutate("a row missing", lambda d, col: rows_edit(col, lambda r: [x for x in r if not (
            x["config"] == "multi_hop" and x["question_id"] == qa[5])]), "have no row")
        mutate("a row under another run_sha256", lambda d, col: rows_edit(col, lambda r: [
            {**x, "run_sha256": "ab" * 32} if i == 3 else x for i, x in enumerate(r)]), "run_sha256 values")
        mutate("the sidecar's run_sha256 not the rows'", lambda d, col: side_edit(col, run_sha256="cd" * 32),
               "sidecar's run_sha256")
        mutate("no sidecar", lambda d, col: col.with_name(col.name + ".json").unlink(), "missing")
        mutate("the sidecar's row count not the file's", lambda d, col: side_edit(col, rows=809), "the sidecar says")
        mutate("the sidecar's replaced count not its rows from the reruns' out",
               lambda d, col: side_edit(col, replaced=4), "counts 4 replaced")
        mutate("a row twice", lambda d, col: rows_edit(col, lambda r: r + [r[0]]), "both")
        mutate("a row under another lock (same run_sha256)", lambda d, col: rows_edit(col, lambda r: [
            {**x, "lock_sha256": "ee" * 32} if i == 9 else x for i, x in enumerate(r)]), "eeeeeeee (1 rows)")
        mutate("a judge prompt that disagrees with Rule 8", lambda d, col: rows_edit(col, lambda r: [
            {**x, "answerable_prompt": not x["answerable_prompt"]} if i == 7 else x for i, x in enumerate(r)]),
            "Rule 8")
        mutate("an unknown (a) status", lambda d, col: rows_edit(col, lambda r: [
            {**x, "a": {**x["a"], "status": "deferred"}} if i == 11 else x for i, x in enumerate(r)]), "status")
        mutate("a row of another index", lambda d, col: rows_edit(col, lambda r: [
            {**x, "run_id": "exp_01__rlm_5__exp_v4_s50_n0"} if i == 13 else x for i, x in enumerate(r)]),
            "not a G1 answer")

        def no_replace(d, col):
            G = guard_module()
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                G.collect([d / "out"], None, col, "G1")
        mutate("collect run without --replace (the reruns' old versions)", no_replace, "--replace")

        def replace_changed(d, col):
            p_ = d / "out_g1r15" / "judge" / run_of("rlm_20") / "judge_passages.jsonl"
            jsonl_edit(p_, lambda rows: rows + [{**rows[0], "item_sha256": "ee" * 32}])
        mutate("the reruns' pass changed after collect", replace_changed, "not from their own pass")

        def replace_extra(d, col):
            p_ = d / "out_g1r15" / "judge" / run_of("single_pass") / "judge_passages.jsonl"
            r0 = json.loads((g1(d, "single_pass") / "judge_passages.jsonl").read_text().splitlines()[0])
            p_.write_text(json.dumps(r0) + "\n")
        mutate("the reruns' out holds an answer that is no rerun", replace_extra, "not G1's reruns")
        mutate("an --answers folder with no answers file", lambda d, col: shutil.rmtree(d / "g1r15_runs" / "runs"),
               "--answers")
        mutate("no --answers", lambda d, col: {"answers": False}, "--answers is needed")

        def answers_edited(d, col):
            p_ = d / "k1_runs" / "runs" / run_of("rlm_20") / "answers.jsonl"
            p_.write_text(p_.read_text().replace("fixture answer", "fixture answer edited", 1))
        mutate("an answers file that is not its MANIFEST.sha256 line", answers_edited, "MANIFEST.sha256 line")
        mutate("an answers folder without MANIFEST.sha256", lambda d, col: (d / "k1_runs" / "MANIFEST.sha256").unlink(),
               "no MANIFEST.sha256")

        def old_answers(d, col):
            shutil.rmtree(d / "g1r15_runs")
            shutil.copytree(d / "k1_runs", d / "g1r15_runs")
        mutate("the answers judged differ from the records given", old_answers, "not the versions S3 judged")
        mutate("draw 2 asked of a draw-1 output", lambda d, col: {"draws": "1,2"}, "have no row")
        mutate("a recheck that gave other scores", lambda d, col: jsonl_edit(
            g1(d, "rlm_10") / "judge_passages_recheck.jsonl",
            lambda rows: [{**x, "equal": False} if i == 4 else x for i, x in enumerate(rows)]),
            "recheck gave other scores")
        mutate("a unit still in its recheck (4 of 10 lines)", lambda d, col: jsonl_edit(
            g1(d, "multi_hop") / "judge_passages_recheck.jsonl", lambda rows: rows[:4]), "still in its recheck")
        mutate("a unit with no recheck file", lambda d, col: (g1(d, "single_pass") / "judge_passages_recheck.jsonl")
               .unlink(), "still in its recheck")
        mutate("a header naming another judge", lambda d, col: jsonl_edit(
            g1(d, "rlm_5") / "judge_passages_headers.jsonl", lambda rows: [{**rows[0], "model": "qwen3.8:27b"}]),
            "a header names judge qwen3.8:27b")
        mutate("a header with another digest", lambda d, col: jsonl_edit(
            g1(d, "rlm_5") / "judge_passages_headers.jsonl", lambda rows: [{**rows[0], "model_digest": "0" * 64}]),
            "a header names judge")
        mutate("no header line for the rows' run_sha256", lambda d, col: jsonl_edit(
            g1(d, "verified_pass") / "judge_passages_headers.jsonl",
            lambda rows: [{**x, "run_sha256": "77" * 32} for x in rows]), "no judge_passages_headers.jsonl line")
        mutate("a start file under another lock", lambda d, col: (d / "out" / "start_11455_x.json").write_text(
            json.dumps({"lock_sha256": "aa" * 32})), "not d66daa28")
        mutate("an out with no start file", lambda d, col: [x.unlink() for x in (d / "out_g1r15").glob("start_*")],
               "no start_*.json")
    attempt("input mutants", input_mutants)

    # ---- three draws: pooled shares in thirds, each draw's rate, the test against the grouped method
    def three_draws():
        f3 = build_fixture(tmp / "d3", (1, 2, 3))
        R3 = rank(ns(f3, draws="1,2,3"), quiet=True)
        s_ = R3["res"]["answerable"][3]
        sh = s_["shares"]
        okp = True
        for c in CONFIGS:
            ps = []
            for q in qa:
                k_ = n_ = 0
                for d in (1, 2, 3):
                    o = planned(c, q, d, groups, idx_a)
                    if o[0] == "scored":
                        k_, n_ = k_ + (o[1] >= 3), n_ + 1
                    elif o[0] == "failed":
                        n_ += 1
                ps.append(Fraction(k_, n_) if n_ else None)
            mean = sum(p for p in ps if p is not None) / sum(1 for p in ps if p is not None)
            okp &= s_["summary"][c]["rate_x"] == mean
        check("three draws: each strategy's rate is the mean over questions of its pass share (computed apart)", okp)
        x = s_["pairs"][("single_pass", "rlm_10")]
        diffs = [sh["single_pass"][q][0] - sh["rlm_10"][q][0] for q in qa
                 if sh["single_pass"][q][0] is not None and sh["rlm_10"][q][0] is not None]
        nz = [Fraction(v) for v in diffs if v != 0]
        L = math.lcm(*[v.denominator for v in nz])
        cnt, dist = Counter(abs(int(v * L)) for v in nz), {0: 1}
        for v, k_ in cnt.items():
            new = defaultdict(int)
            for s2, w in dist.items():
                for j in range(k_ + 1):
                    new[s2 + v * (2 * j - k_)] += w * math.comb(k_, j)
            dist = new
        obs = abs(sum(int(v * L) for v in nz))
        pg = float(Fraction(sum(w for s2, w in dist.items() if abs(s2) >= obs), 2 ** len(nz)))
        check("three draws: the pair's exact P equals the grouped binomial method", abs(x["p"] - pg) < 1e-12)
        check("three draws: 2,430 rows read, 15 reruns from their own pass, phase 1 and 2 rechecks read",
              R3["read"]["rows_read"] == 2430 and len(R3["read"]["reruns_read"]) == 15 and all(
                  set(v["recheck"]) == {"phase 1", "phase 2"} for k_, v in R3["read"]["units"]["folders"].items()
                  if "/out/" in k_))
        check("three draws: a rerun whose new version failed again is a fail, read from its own pass",
              any(f"{INDEX}|verified_pass|19_hpai_canada_TE3|d3" in v
                  for k_, v in R3["out_t"]["verified_pass"]["failed"].items() if k_.startswith("stopped by Google")))
        # panel e on three draws: harmed and helped are sum s(1 - v) and sum (1 - s)v (the mean over the 9 pairings),
        # and the band is single pass's own ordered pairs, both computed apart from planned()
        okf, oks = True, True
        for t in THRESHOLDS:
            hit = {(c, q, d): (lambda o: None if o[0] == "unscored" else int(o[0] == "scored" and o[1] >= t))(
                planned(c, q, d, groups, idx_a)) for c in CONFIGS for q in qa for d in (1, 2, 3)}
            share = {}
            for c in CONFIGS:
                for q in qa:
                    v = [hit[(c, q, d)] for d in (1, 2, 3) if hit[(c, q, d)] is not None]
                    share[(c, q)] = Fraction(sum(v), len(v)) if v else None
            for c in FLIPPED:
                qs_ = [q for q in qa if share[("single_pass", q)] is not None and share[(c, q)] is not None]
                hm = sum(share[("single_pass", q)] * (1 - share[(c, q)]) for q in qs_)
                hp = sum((1 - share[("single_pass", q)]) * share[(c, q)] for q in qs_)
                # on the questions measured in all six answers, the sum is also the harmed pairings counted / 9
                full = [q for q in qs_ if all(hit[(k_, q, d)] is not None for k_ in ("single_pass", c)
                                              for d in (1, 2, 3))]
                pairs9 = Fraction(sum(1 for q in full for d in (1, 2, 3) for e in (1, 2, 3)
                                      if hit[("single_pass", q, d)] == 1 and hit[(c, q, e)] == 0), 9)
                hm_full = sum(share[("single_pass", q)] * (1 - share[(c, q)]) for q in full)
                x = R3["res"]["flips"][t][c]
                okf &= x["harmed_x"] == hm and hm_full == pairs9 and x["helped_x"] == hp
            want = sorted(sum(1 for q in qa if hit[("single_pass", q, d)] == 1 and hit[("single_pass", q, e)] == 0)
                          for d in (1, 2, 3) for e in (1, 2, 3) if d != e)
            sp = R3["res"]["self_flips"][t]["single_pass"]
            oks &= sorted(sp["ordered"].values()) == want and (sp["ordered_min"], sp["ordered_max"]) == (want[0],
                                                                                                      want[-1])
        check("three draws: harmed equals sum s(1 - v) and the count over the 9 pairings / 9, helped sum (1 - s)v, "
              "computed apart, at both thresholds", okf)
        check("three draws: the band is single pass's 6 ordered draw pairs, computed apart, at both thresholds", oks)
        d1 = R3["res"]["answerable"][3]["summary"]["single_pass"]["per_draw"]
        check("three draws: each draw's rate beside the pooled one; draw 1 equals the draw-1 reading",
              abs(d1[1][0] - 65 / 86) < 1e-12 and set(d1) == {1, 2, 3})
    # ---- D155: the outs read where the frozen copy holds them; the pull's HEAD read without git; rebuild's record
    def d155_checks():
        import subprocess as sp
        f1 = build_fixture(tmp / "d155", (1,))
        base = rank(ns(f1), quiet=True)
        recorded_outs = json.loads(f1.with_name(f1.name + ".json").read_text())["_provenance"]["inputs"]
        moved = tmp / "d155_moved"
        moved.mkdir()
        for sub in ("out", "out_g1r15"):
            shutil.move(str(f1.parent / sub), str(moved / sub))
        a = ns(f1)
        msg = refused(rank, a, quiet=True)
        check("D155 relocate: without it, outs moved from where collect read them are refused", "is not here" in msg,
              msg[:160])
        a.relocate = {str(Path(recorded_outs[0]).parent): str(moved)}
        got = rank(a, quiet=True)
        check("D155 relocate: the moved outs are read, every unit and the replace out named as collect recorded them",
              got["read"]["units"] == base["read"]["units"] and got["read"]["replace_out"] == base["read"]["replace_out"]
              and got["read"]["replace_out_here"] == str(moved / "out_g1r15")
              and set(got["read"]["outs_here"]) == {str(moved / "out"), str(moved / "out_g1r15")},
              f"{got['read']['replace_out_here']} {sorted(got['read']['units']['folders'])[:1]}")
        check("D155 relocate: the same numbers as read in place",
              got["res"]["answerable"][4]["summary"] == base["res"]["answerable"][4]["summary"]
              and got["res"]["refusal"][REFUSAL_T]["summary"] == base["res"]["refusal"][REFUSAL_T]["summary"])

        # A8: PULL_SH run here on a fake clone, with a git that fails if called and python3 = this interpreter
        home, home2 = tmp / "d155_home", tmp / "d155_home2"
        clone = home / S3_CLONE
        jd = clone / "findings" / "recompute" / "S3_runs" / "out" / "judge" / run_of("rlm_10")
        jd.mkdir(parents=True)
        (jd / "judge_passages.jsonl").write_text("{}\n")
        g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
        sp.run(g + ["init", "-q", "-b", "main", str(clone)], check=True, capture_output=True)
        sp.run(g + ["-C", str(clone), "add", "-A"], check=True, capture_output=True)
        sp.run(g + ["-C", str(clone), "commit", "-q", "-m", "fixture"], check=True, capture_output=True)
        want = sp.run(["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:7]
        fakebin = tmp / "d155_bin"
        fakebin.mkdir()
        (fakebin / "git").write_text(f"#!/bin/sh\necho called >> {tmp / 'd155_git_called'}\nexit 97\n")
        (fakebin / "python3").write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n")
        for x in ("git", "python3"):
            (fakebin / x).chmod(0o755)

        def remote(h):
            env = {**{k: v for k, v in __import__("os").environ.items()}, "HOME": str(h),
                   "PATH": f"{fakebin}:{__import__('os').environ.get('PATH', '')}"}
            r = sp.run(["bash", "-s"], input=PULL_SH.replace("__CLONE__", S3_CLONE).encode(), env=env,
                       capture_output=True)
            if r.returncode:
                return f"exit {r.returncode}: {r.stderr.decode(errors='replace')[:200]}", []
            with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as tf:
                return tf.extractfile("HEAD.txt").read().decode().strip(), tf.getnames()
        h1, names = remote(home)
        sp.run(g + ["-C", str(clone), "pack-refs", "--all"], check=True, capture_output=True)
        h2, _ = remote(home)
        wt = home2 / S3_CLONE
        wt.parent.mkdir(parents=True)
        sp.run(g + ["-C", str(clone), "worktree", "add", "-q", "--detach", str(wt)], check=True, capture_output=True)
        sp.run(g + ["-C", str(wt), "checkout", "-q", "-b", "wtb"], check=True, capture_output=True)
        h3, _ = remote(home2)
        check("A8: the pull's remote script reads the clone's HEAD from .git (loose ref, packed ref, a worktree's "
              "commondir) and runs no git", (h1, h2, h3) == (want, want, want) and not (tmp / "d155_git_called").exists()
              and "out/judge/" + run_of("rlm_10") + "/judge_passages.jsonl" in names, f"{(h1, h2, h3)} want {want}")

        # rebuild: a committed record whose sha256 of a frozen input differs is refused before anything is written
        global PROVENANCE
        keep_p = PROVENANCE
        fake = tmp / "d155_provenance.json"
        fake.write_text(json.dumps({"provenance": {"inputs_sha256": {"frozen:fig2/g1_collect.jsonl": "0" * 64}}}))
        out_r = tmp / "d155_rebuild_out"
        PROVENANCE = fake
        try:
            rebuild(argparse.Namespace(out=str(out_r)))
            msg = "NOT REFUSED"
        except (Refused, FR.FrozenInputError) as e:
            msg = str(e)
        finally:
            PROVENANCE = keep_p
        check("D155 rebuild: a frozen input whose sha256 differs from the committed record is refused, nothing written",
              "frozen:fig2/g1_collect.jsonl" in msg and "committed plate recorded" in msg and not out_r.exists(),
              msg[:200])

    attempt("D155", d155_checks)

    def panel_f_codes():
        """D160 (5): panel e's (T2) fingerprint rule, on verdict files built here (S495's format)."""
        import S495_t2_judge_code_proof as S495
        g1, t2 = S495.G1_RUN_SHA, S495.T2_RUN_SHA
        pd = tmp / "s495_proof"
        (pd / "online").mkdir(parents=True)
        sc = {"citation_quality": 5, "completeness": 4, "correctness": 4, "faithfulness": 5}
        smp = [{"run_id": f"exp_01__c{i % 6}", "answer_key": f"k{i}", "g1_scores": sc} for i in range(120)]
        rows = [{"run_id": x["run_id"], "answer_key": x["answer_key"], "status": "ok", "scores": sc, "g1_scores": sc,
                 "equal": True, "prompt_sha256_g1": True, "model_digest_g1": True, "run_sha256": t2} for x in smp]

        def lines(xs):
            return "".join(json.dumps(x, sort_keys=True) + "\n" for x in xs)
        (pd / "sample.jsonl").write_text(lines(smp))
        (pd / "online" / "rows.jsonl").write_text(lines(rows))
        ssha = hashlib.sha256(lines(smp).encode()).hexdigest()
        off = {"passed": True, "judged_a_ok": 2425, "sample": {"sha256": ssha},
               "counts": {"identical": 2425, "prompt_sha256_g1": 2425, "scores_new_g1": 2425}}
        ver = {"mode": "online", "g1_run_sha256": g1, "t2_run_sha256": t2, "run_sha256_now": t2,
               "offline_passed": True, "passed": True, "sample_sha256": ssha, "n": 120, "calls_ok": 120,
               "equal_scores": 120, "prompt_sha256_g1": 120, "model_digest_g1": 120, "differences": [],
               "rows_sha256": hashlib.sha256(lines(rows).encode()).hexdigest()}

        def put(v=None, o=None):
            for f, d in (("verdict.json", v), ("offline.json", o)):
                if d is None:
                    (pd / f).unlink(missing_ok=True)
                else:
                    (pd / f).write_text(json.dumps(d))
        put()
        check("panel e (T2): G1 and T2 under G1's one judge code accepted with no proof",
              panel_f_judge_codes(g1, g1, pd)["judge_codes"] == 1)
        check("panel e (T2): T2 under 11e51fde beside G1 refused while S495 has written no verdict",
              "is missing" in refused(panel_f_judge_codes, g1, t2, pd))
        put(ver, off)
        got = panel_f_judge_codes(g1, t2, pd)
        check("panel e (T2): T2 under 11e51fde beside G1 under 38ae79ab accepted with S495's passed verdict, its sha256 "
              "and its row file's recorded (the verdict matches its row file)", got["judge_codes"] == 2
              and got["run_sha256"] == [g1, t2] and got["n"] == 120
              and got["verdict_sha256"] == sha256_file(pd / "verdict.json")
              and got["rows_sha256"] == hashlib.sha256(lines(rows).encode()).hexdigest(), str(got))
        for name, v, o, msg in (
                ("a verdict that did not pass", dict(ver, passed=False), off, "does not prove"),
                ("one score that differs (119 of 120)", dict(ver, equal_scores=119), off, "does not prove"),
                ("a smaller sample (60)", {**ver, **{k: 60 for k in ("n", "calls_ok", "equal_scores",
                                                                     "prompt_sha256_g1", "model_digest_g1")}},
                 off, "does not prove"),
                ("a verdict of another sample", dict(ver, sample_sha256="cd" * 32), off, "does not prove"),
                ("an offline record that did not pass", ver, dict(off, passed=False), "does not prove"),
                ("an offline record with one request not identical", ver,
                 dict(off, counts=dict(off["counts"], identical=2424)), "does not prove"),
                ("a verdict made with other code", dict(ver, run_sha256_now="ef" * 32), off, "does not prove"),
                ("no offline record beside the verdict", ver, None, "is missing")):
            put(v, o)
            check(f"panel e (T2) refuses {name}", msg in refused(panel_f_judge_codes, g1, t2, pd),
                  refused(panel_f_judge_codes, g1, t2, pd))
        # D161 (9): the verdict must match its row file. One answer the judge scored otherwise (row 7), as S495
        # would record it, then the two hand edits: the row file made to agree, or the verdict made to pass.
        rf = pd / "online" / "rows.jsonl"
        diff = [dict(r, scores=dict(sc, correctness=1), equal=False) if i == 7 else r for i, r in enumerate(rows)]
        rf.write_text(lines(rows[:7] + [dict(rows[7], scores=dict(sc, correctness=3))] + rows[8:]))
        put(ver, off)
        check("panel e (T2) refuses a passed verdict whose row file was edited after it (sha256 differs)",
              "does not match its row file" in refused(panel_f_judge_codes, g1, t2, pd),
              refused(panel_f_judge_codes, g1, t2, pd))
        rf.write_text(lines(diff))
        dsha = hashlib.sha256(lines(diff).encode()).hexdigest()
        put(dict(ver, rows_sha256=dsha, passed=False, equal_scores=119, differences=[diff[7]]), off)
        check("panel e (T2) refuses S495's own verdict of a run with one score that differs",
              "does not prove" in refused(panel_f_judge_codes, g1, t2, pd), refused(panel_f_judge_codes, g1, t2, pd))
        put(dict(ver, rows_sha256=dsha), off)
        check("panel e (T2) refuses that verdict edited by hand to PASS (equal_scores 120, no differences): the rows "
              "count 119", "equal_scores': (120, 119)" in refused(panel_f_judge_codes, g1, t2, pd),
              refused(panel_f_judge_codes, g1, t2, pd))
        rf.write_text(lines(rows))
        for name, v, msg in (
                ("a verdict that records no row file sha256", {k: x for k, x in ver.items() if k != "rows_sha256"},
                 "does not match its row file"),
                ("a verdict whose row file is missing", ver, "is missing")):
            put(v, off)
            if name.endswith("missing"):
                rf.rename(rf.with_suffix(".away"))
            check(f"panel e (T2) refuses {name}", msg in refused(panel_f_judge_codes, g1, t2, pd),
                  refused(panel_f_judge_codes, g1, t2, pd))
            if name.endswith("missing"):
                rf.with_suffix(".away").rename(rf)
        other = [dict(r, answer_key=r["answer_key"] + "x") if i == 0 else r for i, r in enumerate(rows)]
        rf.write_text(lines(other))
        put(dict(ver, rows_sha256=hashlib.sha256(lines(other).encode()).hexdigest()), off)
        check("panel e (T2) refuses rows that are not the sample's answers, their sha256 recorded",
              "the rows are the sample's answers False" in refused(panel_f_judge_codes, g1, t2, pd),
              refused(panel_f_judge_codes, g1, t2, pd))
        rf.write_text(lines(rows))
        (pd / "sample.jsonl").write_text(lines(smp[:-1]))
        put(ver, off)
        check("panel e (T2) refuses a sample.jsonl that is not the offline record's sample",
              "not the offline record's sample" in refused(panel_f_judge_codes, g1, t2, pd),
              refused(panel_f_judge_codes, g1, t2, pd))
        (pd / "sample.jsonl").write_text(lines(smp))
        check("panel e (T2) accepts the verdict again once its row file and sample are restored",
              panel_f_judge_codes(g1, t2, pd)["judge_codes"] == 2)
        check("panel e (T2) refuses T2 rows under a third judge code, even with the verdict",
              "neither G1's" in refused(panel_f_judge_codes, g1, "77" * 32, pd))
        check("panel e (T2) refuses G1 rows under another judge code",
              "not G1's" in refused(panel_f_judge_codes, "77" * 32, t2, pd))
        # D256 Q1: key v2.5, G1 under 211568db, a T2 run under another run_sha256 with one judge_passages code
        g5, t5 = G1_V25_RUN_SHA, "5a" * 32
        jp = {"judge_passages_py": "aa" * 32, "template_file": "bb" * 32}
        hg = [{"run_sha256": g5, "key_version": "v2.5", "code": {"judge_passages": jp, "s512_py": "11" * 32}}] * 2
        ht = [{"run_sha256": t5, "key_version": "v2.5", "code": {"judge_passages": jp, "s512_py": "22" * 32}}] * 3
        put()
        check("panel e (T2), v2.5: one run_sha256 accepted with no header",
              panel_f_judge_codes(g5, g5, pd)["judge_codes"] == 1)
        got5 = panel_f_judge_codes(g5, t5, pd, g1_headers=hg, t2_headers=ht)
        check("panel e (T2), v2.5 (D256 Q1): another run_sha256 under one judge_passages code accepted with no S495 "
              "verdict (s512_py may differ)", got5["judge_codes"] == 2 and got5["run_sha256"] == [g5, t5]
              and got5["headers"] == {"G1": 2, "T2": 3} and got5["judge_passages_code_sha256"] == judge_passages_code(hg[0]),
              str(got5))
        other_jp = [dict(ht[0], code={"judge_passages": dict(jp, judge_passages_py="cc" * 32)})] + ht[1:]
        for name, kw, msg in (
                ("no T2 header", {"g1_headers": hg}, "gives no judge header"),
                ("no G1 header", {"t2_headers": ht}, "gives no judge header"),
                ("one T2 header of another judge code", {"g1_headers": hg, "t2_headers": other_jp}, "code identity differs"),
                ("a T2 header of another run", {"g1_headers": hg, "t2_headers": [dict(ht[0], run_sha256="66" * 32)]},
                 "its rows'"),
                ("a T2 header on key v2.4", {"g1_headers": hg, "t2_headers": [dict(ht[0], key_version=None)]}, "its rows'"),
                ("a T2 header with no judge_passages code", {"g1_headers": hg,
                                                             "t2_headers": [dict(ht[0], code={"s512_py": "22" * 32})]},
                 "no code.judge_passages")):
            check(f"panel e (T2), v2.5 (D256 Q1) refuses {name}", msg in refused(panel_f_judge_codes, g5, t5, pd, **kw),
                  refused(panel_f_judge_codes, g5, t5, pd, **kw))
        check("panel e (T2), v2.5: a v2.4 T2 code beside G1's v2.5 run is refused (the S495 proof is v2.4's only)",
              "code identity differs" in refused(panel_f_judge_codes, g5, t2, pd, g1_headers=hg, t2_headers=[
                  {"run_sha256": t2, "key_version": "v2.5", "code": {"judge_passages": {"x": 1}}}])
              and "not S6G1's" in refused(v25_judge_codes, g1, t5, hg, ht))
    attempt("panel e (T2) judge codes (D160 Q16)", panel_f_codes)
    attempt("three draws", three_draws)

    # ---- D186 (3): the judge rows through judge_rows_v25 (key v2.5 where a row exists, else key v2.4)
    def judge_rows_checks():
        changed = set(JR.S512.changed_ids())
        f0 = build_fixture(tmp / "jr0", (1, 2, 3))
        R0 = rank(ns(f0, draws="1,2,3"), quiet=True)
        jr0 = R0["read"]["judge_rows"]
        n_ch = sum(1 for (_, q, _) in R0["read"]["cells"] if q in changed)
        check("judge rows without S6 outs: every answer of the 132 changed questions read from key v2.4 and counted "
              "awaiting S6 (6 strategies x 3 draws x the changed questions G1 asks); provisional; S6G1 not present",
              n_ch == 18 * len(changed & set(groups)) and jr0["awaiting_s6_read"] == n_ch
              and jr0["awaiting_s6_all_draws"] == n_ch and jr0["cells_from_v25"] == 0 and jr0["provisional"]
              and not jr0["sources"]["S6G1"]["present"]
              and jr0["sources"]["S6G1"]["missing"] == ["out_s6_g1", "out_s6_g1r15"]
              and jr0["status"].startswith(f"awaiting S6: {n_ch:,} of the 2,430 answers read"),
              json.dumps({k: jr0[k] for k in ("status", "awaiting_s6_read", "cells_from_v25")}))
        f6 = build_fixture(tmp / "jr6", (1, 2, 3), s6=True)
        R6 = rank(ns(f6, draws="1,2,3"), quiet=True)
        jr6 = R6["read"]["judge_rows"]
        check("judge rows with S6 outs (out_s6_g1, out_s6_g1r15 as --replace): every answer of the 132 from its key "
              "v2.5 row, none awaiting S6, not provisional",
              jr6["cells_from_v25"] == n_ch and jr6["awaiting_s6_read"] == 0 and not jr6["provisional"]
              and jr6["sources"]["S6G1"]["present"] and jr6["sources"]["S6G1"]["rows"] == n_ch,
              json.dumps({k: jr6[k] for k in ("status", "awaiting_s6_read", "cells_from_v25")}))
        bad = []
        for k, cell in R0["read"]["cells"].items():
            c6 = R6["read"]["cells"][k]
            want = (cell["kind"], (6 - cell["score"]) if k[1] in changed and cell["kind"] == "scored"
                    else cell.get("score"))
            rel_rec = lambda c_, base: str(c_.get("record")).replace(str(base), "")       # noqa: E731
            if (c6["kind"], c6.get("score")) != want or (k[1] in changed) != (c6.get("key_version") == "v2.5") \
                    or any(c6.get(f) != cell.get(f) for f in JOIN if f != "record") \
                    or rel_rec(c6, tmp / "jr6") != rel_rec(cell, tmp / "jr0"):
                bad.append(k)
        check("judge rows with S6 outs: each changed answer's cell is its v2.5 row's (score 6 - s, computed apart), "
              "with the record's joined fields; every other cell is the v2.4 one", not bad, str(bad[:3]))
        cells_apart = {k: (dict(v, score=6 - v["score"]) if k[1] in changed and v["kind"] == "scored" else v)
                       for k, v in R0["read"]["cells"].items()}
        res_apart = compute(cells_apart, groups, [1, 2, 3], True)
        check("judge rows with S6 outs: every strategy's pass rate at 4 and 3 is compute() on the cells made apart",
              all(R6["res"]["answerable"][t]["summary"][c]["rate_x"] == res_apart["answerable"][t]["summary"][c]["rate_x"]
                  for t in THRESHOLDS for c in CONFIGS)
              and any(R6["res"]["answerable"][4]["summary"][c]["rate_x"] != R0["res"]["answerable"][4]["summary"][c]["rate_x"]
                      for c in CONFIGS))
        rk = [k for k in rerun_keys() if k.split("|")[2] in changed]
        got = [R6["read"]["cells"][(k.split("|")[1], k.split("|")[2], int(k.rsplit("|d", 1)[1]))] for k in rk]
        check(f"judge rows with S6 outs: the {len(rk)} reruns of changed questions are read from out_s6_g1r15 (their "
              f"new version), not from out_s6_g1's judging of the old, failed one",
              len(rk) == 5 and all(c_["key_version"] == "v2.5" and c_["kind"] != "failed" for c_ in got)
              and jr6["sources"]["S6G1"]["replace"] == {"keys": 15, "rows_from_replace": 5}, str(got[:2]))
        # a v2.5 row judged with the wrong prompt: refused by judge_rows_v25.check_v25
        fm = build_fixture(tmp / "jrm", (1,), s6=True)
        jf = sorted((tmp / "jrm" / "out_s6_g1" / "judge").glob("*/judge_passages.jsonl"))[0]
        rows_ = [json.loads(x) for x in jf.read_text().splitlines() if x.strip()]
        rows_[0]["answerable_prompt"] = not rows_[0]["answerable_prompt"]
        jf.write_text("".join(json.dumps(r) + "\n" for r in rows_))
        msg = refused(rank, ns(fm, draws="1"))
        check("judge rows: a v2.5 row judged with the other prompt is refused (judge_rows_v25 [prompt])",
              "judge_rows_v25" in msg and "[prompt]" in msg, msg[:200])
        # out_s6_g1r15 absent: S6G1 is not read at all (the reruns would be their old versions), every changed
        # answer awaits S6
        fa = build_fixture(tmp / "jra", (1,), s6=True)
        shutil.rmtree(tmp / "jra" / "out_s6_g1r15")
        Ra = rank(ns(fa, draws="1"), quiet=True)
        ja = Ra["read"]["judge_rows"]
        check("judge rows: out_s6_g1 without out_s6_g1r15 is not read; every changed answer of draw 1 awaits S6",
              not ja["sources"]["S6G1"]["present"] and ja["sources"]["S6G1"]["missing"] == ["out_s6_g1r15"]
              and ja["cells_from_v25"] == 0 and ja["awaiting_s6_read"] == 6 * len(changed & set(groups)),
              json.dumps(ja["sources"]["S6G1"]))
    attempt("judge rows (D186 (3))", judge_rows_checks)

    # ---- D195: rank, with G2, G6 and every file of a plate, opens no T2 or second-judge file, and no early-look file
    def blind_checks():
        fb = build_fixture(tmp / "blind", (1,))
        seen = _audit_opens()
        seen.clear()
        _AUDIT["on"] = True
        try:
            rank(ns(fb, out=tmp / "blind" / "plate", no_plate=False), quiet=True)
        finally:
            _AUDIT["on"] = False
        bad = [p for p in seen if BLIND_PATHS.search(p)]
        check(f"D195 and D168: rank opened {len(seen)} files, none of a T2 run, of the second judge or of an early look",
              len(seen) > 20 and not bad, str(bad[:3]))
        msg = refused(read_extra, tmp / "blind" / "extra_1", groups, [1], tmp / "blind" / "extra_1" / "no_such_file",
                      tmp / "blind" / "extra_1" / G6_FIXTURE)
        check("a missing G2 records file is not read as empty", msg.startswith("CRASH FileNotFoundError") or "G2" in msg, msg[:160])
    attempt("the blind rule", blind_checks)

    def s518_checks():
        f = fixture_s518(tmp / "s518_ok")
        t = read_s518(f)
        rd = [d["result"]["interaction"]["reading"] for d in t["sources"].values()]
        S518_ = s518_module()
        check("3e: read_s518 reads S518's five sources in S518.SOURCES order, each reading S518's, then the reference",
              list(t["sources"]) == list(S518_.SOURCES) + [S518_.REFERENCE] and "not shown" in rd and "agrees" in rd,
              str(rd))
        rows_ = s518_rows(t)
        check("3e: sheet Fig. 3e holds 3 rows per source and the reference, in points, the reading on I's row only",
              len(rows_) == 18 and all((r["reading"] is None) == (r["measure"] != "interaction") for r in rows_)
              and abs(rows_[0]["d_pp"] - 100 * t["sources"]["second_judge"]["result"]["one_paper"]["d"]) < 1e-9
              and [r["role"] for r in rows_[-3:]] == ["reference"] * 3
              and rows_[-1]["source_label"] == "gemini-3-flash")
        for name, edit, msg in (
                ("another decision", lambda d: d.update(decision="D195"), "S518 gives"),
                ("another key", lambda d: d.update(key="v2.4"), "S518 gives"),
                ("another role", lambda d: d.update(role="test"), "S518 gives"),
                ("a value outside its interval", lambda d: d["result"]["many_paper"].update(d=-1.0), "not inside"),
                ("a reading S518.reading does not give", lambda d: d["result"]["interaction"].update(
                    reading="not shown"), "S518.reading gives")):
            bad_ = tmp / f"s518_refbad_{len(name)}_{abs(hash(name)) % 1000}"
            shutil.copytree(f, bad_)
            fp = bad_ / f"{S518_.REFERENCE}.json"
            d = json.loads(fp.read_text())
            edit(d)
            fp.write_text(json.dumps(d))
            check(f"3e: read_s518 refuses a reference row with {name}", msg in refused(read_s518, bad_),
                  refused(read_s518, bad_)[:160])
        gone_r = tmp / "s518_refgone"
        shutil.copytree(f, gone_r)
        (gone_r / f"{S518_.REFERENCE}.json").unlink()
        check("3e: read_s518 refuses the reference row missing", "is missing" in refused(read_s518, gone_r))
        for name, edit, msg in (
                ("a reading S518.reading does not give", lambda d: d["result"]["interaction"].update(
                    reading="opposite"), "S518.reading gives"),
                ("a role that is not S518's", lambda d: d.update(role="beside"), "role"),
                ("another decision", lambda d: d.update(decision="D194"), "decision"),
                ("a value outside its interval", lambda d: d["result"]["one_paper"].update(d=1.0), "not inside")):
            bad_ = tmp / f"s518_bad_{len(name)}_{abs(hash(name)) % 1000}"
            shutil.copytree(f, bad_)
            d = json.loads((bad_ / "gemma3.json").read_text())
            edit(d)
            (bad_ / "gemma3.json").write_text(json.dumps(d))
            check(f"3e: read_s518 refuses {name}", msg in refused(read_s518, bad_), refused(read_s518, bad_)[:160])
        gone = tmp / "s518_gone"
        shutil.copytree(f, gone)
        (gone / "qwen3-coder.json").unlink()
        check("3e: read_s518 refuses a source S518 has not written", "is missing" in refused(read_s518, gone))
    attempt("3e reads S518's verdicts (D195)", s518_checks)

    def record_checks():
        rec = judge_rows_record({"choice": {}, "units_v25": {"folders": {str(FIG3_S6 / "out_s6_g1" / "judge" / "u"): 1},
                                                             "starts": {str(FIG3_S6 / "out_s6_g1" / "s.json"): "d66daa28"}}})
        check("the v2.5 units are named relative to the repository, with no machine folder (D155), and the rows chosen "
              "are not kept", "choice" not in rec and str(ROOT) not in json.dumps(rec)
              and list(rec["units_v25"]["folders"]) == ["findings/recompute/fig3_s6_inputs/out_s6_g1/judge/u"],
              json.dumps(rec)[:200])
        a_ = types.SimpleNamespace(relocate={"/somewhere/pull_20261023": str(FIG3_S6)})
        t_ = record_text({"p": "/somewhere/pull_20261023/out/x"}, a_)
        check("record_text writes the recorded pull folder as its frozen copy", "/somewhere" not in t_
              and "findings/recompute/fig3_s6_inputs/out/x" in t_, t_)
    attempt("records", record_checks)
    fx_e = tmp / "fx_e"

    def extra_checks():
        fe = build_fixture(fx_e, (1, 2, 3), s6=True)
        ex = fx_e / "extra_1_2_3"
        fixture_extra(ex, (1, 2, 3), s6=True)
        cs_ = {("x", "q1", 1): {"kind": "scored", "score": 4}, ("x", "q2", 1): {"kind": "scored", "score": 3},
               ("x", "q3", 1): {"kind": "failed"}, ("x", "q4", 1): {"kind": "unscored"}}
        qs_ = ["q1", "q2", "q3", "q4"]
        sh_ = arm_shares(cs_, "x", qs_, [1], 4)
        check("arm_shares, worked by hand: a score at the threshold passes, one under it fails, a failure fails, no score "
              "has no share", [sh_[q][0] for q in qs_] == [Fraction(1), Fraction(0), Fraction(0), None])
        sm_ = arm_summary(sh_, qs_, [1])
        check("arm_summary, worked by hand: the rate is over the questions with a share (1 of 3)",
              sm_["rate_x"] == Fraction(1, 3) and sm_["questions_with_share"] == 3 and sm_["per_draw"][1][1] == 3)
        x = read_extra(ex, groups, [1, 2, 3], ex / "matched_budget_answers.jsonl", ex / G6_FIXTURE)
        check("read_extra: 405 answers of each arm, all on a final-key row, G6's caps 5 and 20 not read",
              len(x["cells"]) == 810 and x["final_key"] == 810 and {c for c, _, _ in x["cells"]} == set(EXTRA_DRAWN))
        # D218: the clock margin's records, worked apart from the code: G2's fixture latency 3.0 s with no wait, package
        # RLM-10's fixture wall_s, the mean over the three draws
        ia = {q: i for i, q in enumerate(sorted(q for q, g in groups.items() if g == "answerable"))}
        i_all = {}
        for g in ("answerable", "not_answerable", "false_premise"):
            for i, q in enumerate(sorted(q for q, gg in groups.items() if gg == g)):
                i_all[q] = i
        g6w = {q: sum(fixture_g6_wall(i_all[q], d) for d in (1, 2, 3)) / 3 for q in ia}
        ok_c = all(abs(sum(a for a, _ in x["clock"]["cap10"][q]) / 3 - g6w[q]) < 1e-12 for q in ia) \
            and all(v == [(3.0, 3.0)] * 3 for q, v in x["clock"]["matched_budget"].items())
        check("read_extra (D218): Zhang RLM-10's clock time is its records' wall_s and matched budget's its latency_s "
              "less no wait, per draw, as the fixture wrote them", ok_c)
        g6p = ex / G6_FIXTURE
        keep_ = g6p.read_text()
        g6p.write_text("".join(z + "\n" for z in keep_.splitlines()[1:]))
        msg = refused(read_g6_clock, g6p, groups, [1, 2, 3])
        g6p.write_text(keep_)
        check("read_g6_clock refuses a Zhang RLM-10 answer with no record", "have no record" in msg, msg[:160])
        # the gate against Supplementary Figure 17c, on a workbook written here
        from openpyxl import Workbook
        m_ = {"single_pass": {"qa": (10.0, 10.0), "qb": (20.0, 25.0)}, "cap10": {"qa": (5.0, 5.0), "qb": (7.5, 7.5)}}

        def supp6_book(vals, path):
            wb = Workbook()
            ws = wb.active
            ws.title = SUPP6_SHEET
            ws.append(["setup", "row", "question_id", "answer_type", "clock_less_wait_mean_over_draws"])
            for c_, perq in vals.items():
                for q_, v_ in perq.items():
                    ws.append([c_, "question", q_, "extractive" if q_ == "qa" else "synthesis", v_])
                ws.append([c_, "question", "qn", "not_answerable", 999.0])
                ws.append([c_, "set-up", None, None, None])
            wb.save(path)
            return path
        bk = supp6_book({c_: {q_: v_[0] for q_, v_ in p_.items()} for c_, p_ in m_.items()}, fx_e / "s6c_ok.xlsx")
        check("the margin's gate passes a Supplementary Fig. 17c of the same values (4 per-question means, 2 rows)",
              "4 per-question means of 2 rows" in hold_margin_to_supp6(m_, bk))
        bk2 = supp6_book({"single_pass": {"qa": 10.0, "qb": 20.0}, "cap10": {"qa": 5.0, "qb": 7.6}}, fx_e / "s6c_x.xlsx")
        check("the margin's gate refuses a Supplementary Fig. 17c whose one value differs",
              "cap10 qb" in refused(hold_margin_to_supp6, m_, bk2))
        bk3 = supp6_book({"single_pass": {"qa": 10.0}, "cap10": {"qa": 5.0, "qb": 7.5}}, fx_e / "s6c_q.xlsx")
        check("the margin's gate refuses a Supplementary Fig. 17c with another set of questions",
              "are not the 2" in refused(hold_margin_to_supp6, m_, bk3))
        changed = set(JR.S512.changed_ids())
        q_ch = next(q for q in sorted(groups) if q in changed and groups[q] == "answerable")
        q_un = next(q for q in sorted(groups) if q not in changed and groups[q] == "answerable")
        i_ = sorted(q for q, g in groups.items() if g == "answerable").index(q_ch)
        check("read_extra: a changed question's cell is its key v2.5 row (score 6 - s), an unchanged one's its v2.4 row",
              x["cells"][("matched_budget", q_ch, 1)]["score"] == 6 - fixture_extra_score("matched_budget", i_)
              and x["cells"][("matched_budget", q_ch, 1)]["key_version"] == "v2.5"
              and x["cells"][("matched_budget", q_un, 1)]["key_version"] == "v2.4")
        kd = S511.questions()
        res_v = {}
        for t in THRESHOLDS:
            sh = arm_shares(x["cells"], "matched_budget", qa, [1, 2, 3], t)
            res_v[str(t)] = {nm: {"matched_budget": {"rate": arm_summary(sh, sub, [1, 2, 3])["rate"]}} for nm, sub in (
                ("all answerable", qa), ("one-paper", [q for q in qa if kd[q]["kind"] == "one"]),
                ("many-paper", [q for q in qa if kd[q]["kind"] == "many"]))}
        rj = fx_e / "s511.json"
        rd = {"all answerable": {"matched_budget": {"passages_median": 50}, "rlm_10": {"passages_median": 30}}}
        rj.write_text(json.dumps({"v25": {"pass": res_v}, "reading": {"by_set": rd}}))
        check("G2's rates are held to S511's: equal values pass", "6 of 6" in hold_g2_to_s511(x, rj, groups, [1, 2, 3], kd))
        res_v["4"]["many-paper"]["matched_budget"]["rate"] += 0.01
        rj.write_text(json.dumps({"v25": {"pass": res_v}, "reading": {"by_set": rd}}))
        msg = refused(hold_g2_to_s511, x, rj, groups, [1, 2, 3], kd)
        check("G2's rates are held to S511's: a differing rate is refused", "in S511's results.json" in msg, msg[:200])
        res_v["4"]["many-paper"]["matched_budget"]["rate"] -= 0.01
        rd_ = {"all answerable": {"matched_budget": {"passages_median": 30}, "rlm_10": {"passages_median": 30}}}
        rj.write_text(json.dumps({"v25": {"pass": res_v}, "reading": {"by_set": rd_}}))
        msg = refused(hold_g2_to_s511, x, rj, groups, [1, 2, 3], kd)
        check("G2's passages are held to S511's: matched budget not above RLM-10 is refused, naming no legend wording",
              "did not read more passages" in msg and "legend says" not in msg, msg[:200])
        rj.write_text(json.dumps({"reading": {"by_set": rd}}))
        check("S511's results with no key v2.5 reading are refused",
              "no key v2.5 reading" in refused(hold_g2_to_s511, x, rj, groups, [1, 2, 3], kd))
        ms = ex / "matched_budget_answers.jsonl"
        rr = [json.loads(z) for z in ms.read_text().splitlines()]
        rr[0]["generation"]["answer"] = ""
        ms.write_text("".join(json.dumps(z) + "\n" for z in rr))
        msg = refused(read_extra, ex, groups, [1, 2, 3], ms, ex / G6_FIXTURE)
        check("read_extra refuses a G2 record that disagrees with its judge row", "do not match their records" in msg,
              msg[:200])
        t_ = fixture_fig3e(fx_e / "fig3e")
        (t_ / "tables.json").write_text((t_ / "tables.json").read_text() + " ")
        check("a tables.json that is not the one S522's header records is refused",
              "is not the file" in refused(read_fig3e, t_))
    attempt("G2 and G6", extra_checks)
    shutil.rmtree(tmp, ignore_errors=True) if not getattr(args, "keep", False) else print(f"kept {tmp}")
    print(f"selftest: {sum(results)} of {len(results)} checks pass")
    return 0 if all(results) else 1


# Code mutants (`mutants`): each changes one line of this file; the whole selftest then runs on the changed code and
# must fail one of its checks (a FAIL line), never only crash. (name, the text replaced, its replacement)
MUTANTS = [
    ("a failed answer left out instead of counted as a fail",
     '                elif cell["kind"] == "failed" and failures_as_fail:\n                    n, per[d] = n + 1, 0\n',
     '                elif False:\n                    n, per[d] = n + 1, 0\n'),
    ("a failed answer on the 39 counted as refused",
     '                elif cell["kind"] == "failed" and failures_as_fail:\n                    n, per[d] = n + 1, 0\n',
     '                elif cell["kind"] == "failed" and failures_as_fail:\n                    k, n, per[d] = k + '
     '(q.startswith("OOD")), n + 1, int(q.startswith("OOD"))\n'),
    ("a failed judge call counted as a fail",
     '    elif st in JUDGE_FAILED:\n        cell = {"kind": "unscored", "why": st}\n',
     '    elif st in JUDGE_FAILED:\n        cell = {"kind": "failed", "why": st}\n'),
    ("pass taken as above the threshold", '                    hit = int(cell["score"] >= t)\n',
     '                    hit = int(cell["score"] > t)\n'),
    ("G2 and G6: pass taken as above the threshold", '\n                hit = int(cell["score"] >= t)\n',
     '\n                hit = int(cell["score"] > t)\n'),
    ("the answerable score read from another dimension", '"answerable": "correctness", "false_premise"',
     '"answerable": "completeness", "false_premise"'),
    ("the refusal score read from another dimension", '"not_answerable": "refusal_accuracy"}',
     '"not_answerable": "hallucination_avoidance"}'),
    ("refusal read at score 4", "REFUSAL_T = 3 ", "REFUSAL_T = 4 "),
    ("Q16: panel e (T2) takes any T2 judge code", "    if t2_run_sha != S495.T2_RUN_SHA:\n",
     "    if False:\n"),
    ("Q16: panel e (T2) takes a verdict whose sample counts are short",
     "    if bad or not full or not off:\n", "    if bad or not off:\n"),
    ("Q16: panel e (T2) takes a verdict whose offline record did not pass",
     "    if bad or not full or not off:\n", "    if bad or not full:\n"),
    ("D161: panel e (T2) takes a verdict whose row file's sha256 differs",
     '    if rsha is None or v.get("rows_sha256") != rsha:\n', "    if rsha is None:\n"),
    ("D161: panel e (T2) takes a verdict whose counts are not its rows' counts",
     "    if off_count or not same_answers or not code_ok:\n", "    if not same_answers or not code_ok:\n"),
    ("D256 Q1: panel e (T2), v2.5, takes two judge_passages codes", "    if len(by) != 1:\n", "    if len(by) > 2:\n"),
    ("D256 Q1: panel e (T2), v2.5, takes a header of another run",
     "            if h.get(\"run_sha256\") != run or h.get(\"key_version\") != \"v2.5\":\n",
     "            if h.get(\"key_version\") != \"v2.5\":\n"),
    ("D256 Q1: panel e (T2), v2.5, takes a run with no header", "    if not g1h or not t2h:\n", "    if not g1h:\n"),
    ("Q11: the claims list's score-4 rate read at score 3",
     'rate4 = lambda c: 100 * a4["summary"][c]["rate"]', 'rate4 = lambda c: 100 * a3["summary"][c]["rate"]'),
    ("Q11: the claims list's score-4 pairs read at score 3",
     'x, x4 = pair(a3["pairs"], m[1], m[2]), pair(a4["pairs"], m[1], m[2])',
     'x, x4 = pair(a3["pairs"], m[1], m[2]), pair(a3["pairs"], m[1], m[2])'),
    ("Q11: the claims list's passage-verification reading at score 4 read at score 3",
     'also4 = f"; score 4 or more: {flip_at(4)[1]}"', 'also4 = f"; score 4 or more: {flip_at(3)[1]}"'),
    ("Q11: the claims list's passage-verification rows at score 3 give no score-4 reading",
     'if m[2] == 3 else ""', 'if False else ""'),
    ("Q11: the claims list's false-premise counts at score 4 read at score 3",
     'at score 4: {fp(4)}"', 'at score 4: {fp(3)}"'),
    ("D154 undone: the pass rate at score 3, 3 first", "THRESHOLDS, PRIMARY = (4, 3), 4 ",
     "THRESHOLDS, PRIMARY = (3, 4), 3 "),
    ("the test one-sided",
     "    return float(Fraction(sum(k for s, k in dist.items() if abs(s) >= obs), 2 ** len(v)))\n",
     "    return float(Fraction(sum(k for s, k in dist.items() if s >= obs), 2 ** len(v)))\n"),
    ("another resample seed", "    idx = np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))\n    flat",
     "    idx = np.random.default_rng(SEED + 1).integers(0, n, size=(N_BOOT, n))\n    flat"),
    ("the interval's percentiles 5 and 95", "PCT = (2.5, 97.5) ", "PCT = (5.0, 95.0) "),
    ("the pair interval's sign flipped", "            num.append(float(pa - pb))\n",
     "            num.append(float(pb - pa))\n"),
    ("each draw's rate over every question", "per[d] = (sum(v) / len(v) if v else None, len(v))\n        res[c] =",
     "per[d] = (sum(v) / len(qids) if v else None, len(v))\n        res[c] ="),
    ("rates summed as floats (ties broken by rounding)",
     "rate_x = sum(have, Fraction(0)) / n if n else None\n        lo, hi = interval(num, den)",
     "rate_x = sum(float(p) for p in have) / n if n else None\n        lo, hi = interval(num, den)"),
    ("G2 and G6: a rate over every question, not those with a share",
     "rate_x = sum(have, Fraction(0)) / n if n else None\n    lo, hi = interval([float",
     "rate_x = sum(have, Fraction(0)) / len(ps) if n else None\n    lo, hi = interval([float"),
    ("Rule 6 ignores the direction of the difference",
     'ok = x["d_x"] is not None and sign * x["d_x"] > 0 and x["p"] < ALPHA',
     'ok = x["d_x"] is not None and x["p"] < ALPHA'),
    ("Rule 6 met with a shared first place", '"met": len(firsts) == 1 and not not_apart', '"met": not not_apart'),
    ("Rule 11 reverses only when significant", '    if d < 0:\n        return "reverses"',
     '    if d < 0 and x["p"] < ALPHA:\n        return "reverses"'),
    ("Rule 11 holds at a zero difference", 'return "holds" if d > 0 and x["p"] < ALPHA else "weakens"',
     'return "holds" if d >= 0 and x["p"] <= 1 else "weakens"'),
    ("the zero bound given for any rate", '"zero_bound": zero_bound(n) if n and rate_x == 0 else None',
     '"zero_bound": zero_bound(n) if n else None'),
    ("the full bound given for any rate", '"full_bound": full_bound(n) if n and rate_x == 1 else None',
     '"full_bound": full_bound(n) if n else None'),
    ("recitation stops not grouped as stopped by Google", 'GOOGLE_STOP = ("blocked", "recitation")',
     'GOOGLE_STOP = ("blocked",)'),
    ("a Google stop with text not counted", '            t[c]["google_scored"][f"stopped by Google',
     '            t[c]["cut_scored"][f"stopped by Google'),
    ("the sensitivity reading the same as the main one",
     'res_out = compute(read["cells"], groups, draws, False)', 'res_out = compute(read["cells"], groups, draws, True)'),
    ("the verifier answers not set aside", '        cells2 = {k: ({**v, "kind": "set_aside"} if v["key"] in drop',
     '        cells2 = {k: ({**v} if v["key"] in drop'),
    ("the missing-row check removed", "    if missing:\n        per = Counter", "    if False:\n        per = Counter"),
    ("the reruns' row-by-row check removed", "    if wrong:\n        raise Refused", "    if False:\n        raise Refused"),
    ("the reruns' check on run_sha256 only",
     'elif (src.get("item_sha256"), src.get("run_sha256")) != (cell["item_sha256"], run_sha):',
     'elif src.get("run_sha256") != run_sha:'),
    ("the reruns' out not required among collect's inputs", "    if rp is None or str(rp) not in ins:\n",
     "    if rp is None:\n"),
    ("the Rule 8 prompt check removed",
     '        if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):\n            bad.append(f"row {i}',
     '        if False:\n            bad.append(f"row {i}'),
    ("D186 (3): a v2.5 row's cell not used", '            read["cells"][k] = new\n', '            pass\n'),
    ("D186 (3): the answers awaiting S6 not counted",
     '            awaiting_read += ch["status"] == "v2.4 awaiting S6"\n', '            awaiting_read += 0\n'),
    ("the MANIFEST check removed", "            if want.get(rel) != h:", "            if False:"),
    ("the sidecar's row count check removed", '    if side.get("rows") != len(rows):', "    if False:"),
    ("the sidecar's replaced count check removed",
     '    if from_rp != side.get("replaced", 0) + side.get("added_by_replace", 0):', "    if False:"),
    ("the lock check removed", "    if set(locks) - LOCKS_OK:", "    if False:"),
    ("the recheck's equal check removed", "                if bad:\n                    raise Refused(f\"{folder}: the recheck",
     "                if False:\n                    raise Refused(f\"{folder}: the recheck"),
    ("the recheck's coverage check removed", "                if n < need:", "                if False:"),
    ("the judge header check removed", "            if off:\n", "            if False:\n"),
    ("the start file check removed", "            if lk not in LOCKS_OK:", "            if False:"),
    ("panel e: harmed and helped swapped", "h, g = s * (1 - v), (1 - s) * v", "h, g = (1 - s) * v, s * (1 - v)"),
    ("panel e: the degraded share over the changed outcomes",
     '"degraded_share": float(harm / base) if base else None', '"degraded_share": float(harm / ch) if ch else None'),
    ("panel e: the band from unordered draw pairs", "for d, e in permutations(draws, 2)}",
     "for d, e in combinations(draws, 2)}"),
    ("panel c: one model call per answer", '"calls": x["calls_n"]', '"calls": 1'),
    ("panel d: the wait not read", '"wait_s": x["wait"], "tokens"', '"wait_s": 0.0, "tokens"'),
    ("the S77 reproduce check removed",
     "    if got != {k: v for k, v in S77_PRINTED.items()} or words != S77_RATIO_WORDS:", "    if False:"),
    ("panel b: the record check removed", "                if {f: got[f] for f in CR_FIELDS} != want:",
     "                if False:"),
    ("panel b: the answer identity check removed",
     '                if (r["answer_sha256"], r["status"]) != (a["answer_sha256"], a["status"]):', "                if False:"),
    ("panel b: the exact value plotted as the headline one", '"concept_recall_pct": r9(100 * x["rate"])',
     '"concept_recall_pct": r9(100 * e["rate"])'),
    ("panel b: the D12 loose base drawn in place of the D181 value",
     '"note_removed": bool(r.get("note_removed")), "value": Fraction(f, n),',
     '"note_removed": bool(r.get("note_removed")), "value": Fraction(r["found_loose_base"], nc),'),
    ("panel b: the loose base check on unchanged concepts removed",
     '        if r["group"] != "not_answerable" and r["question_id"] in same_c:\n            if (r.get(',
     '        if False:\n            if (r.get('),
    ("panel b: the v2.4 anchor compared on the exact value only", "    if got != CR_ANCHOR_V24:",
     "    if {c: v[3] for c, v in got.items()} != {c: v[3] for c, v in CR_ANCHOR_V24.items()}:"),
    ("panel b: the Rule 8 check removed",
     '                    if r.get("reason") != "not applicable" or r.get("concept_recall_loose") is not None:',
     "                    if False:"),
    ("panel b: each question's first draw only", "                sh[c][q] = (sum(per.values(), Fraction(0)) / len(draws), per)",
     "                sh[c][q] = (per[draws[0]], per)"),
    ("check_drawn: a tile's colour not compared", "            if to_hex(p.get_facecolor()).upper() != exp.upper():",
     "            if False:"),
    ("check_drawn: the pairing dots not compared",
     "            if gotv is None or len(gotv) != len(want) or not all(close(g, w) for g, w in zip(gotv, want)):",
     "            if gotv is None:"),
    ("the tiles reversed: more draws darker", "    return {k: lev[k].upper() for k in range(nd + 1)}\n",
     "    return {k: lev[nd - k].upper() for k in range(nd + 1)}\n"),
    ("3a: the two groups sorted as one order", 'order_a = [q for g in ("one", "many") for q in sorted(part[g], key=',
     'order_a = [q for g in ("all",) for q in sorted(qa, key='),
    ("3a: the group rates read on every question", "        for g, sub in part.items():\n            for c in CONFIGS:",
     "        for g, sub in {k_: qa for k_ in part}.items():\n            for c in CONFIGS:"),
    ("the multiples: time from the clock, not the model calls",
     'r9(ca[c]["model_s"]["mean"] / sp_c["model_s"]["mean"])', 'r9(ca[c]["clock_s"]["mean"] / sp_c["clock_s"]["mean"])'),
    ("the tokens' median taken as their mean", '"ratio_of_medians": r9(ca[c]["tokens"]["median"] / sp_c["tokens"]["median"])',
     '"ratio_of_medians": r9(ca[c]["tokens"]["mean"] / sp_c["tokens"]["mean"])'),
    ("check_drawn: 3d's group marks not compared",
     """                if ms_[0]["ax"] is not dd[0]["ax"] or not (close(a_.get_xdata()[0], r["calls_mean"])""",
     """                if False and not (close(a_.get_xdata()[0], r["calls_mean"])"""),
    ("check_drawn: 3d's rates not held to sheet Fig. 3a",
     '                if ra is None or not close(r[kd], ra[k3a]) or ra["questions_in_group"] != r["questions"]:',
     "                if ra is None:"),
    ("3d: score 3 and 4 swapped", '            for t, key_ in ((THRESHOLDS[1], "pass_rate_t3_pct"), (PRIMARY, "pass_rate_t4_pct")):',
     '            for t, key_ in ((THRESHOLDS[1], "pass_rate_t4_pct"), (PRIMARY, "pass_rate_t3_pct")):'),
    ("3d: the one-paper and many-paper calls swapped",
     '        for g, sub in (("all", qa), ("one", part["one"]), ("many", part["many"])):',
     '        for g, sub in (("all", qa), ("one", part["many"]), ("many", part["one"])):'),
    ("check_drawn: the cross not compared",
     """        if not (close(cr[0]["artist"].get_xdata()[0], r["calls_mean"])
                and close(cr[0]["artist"].get_ydata()[0], r["pass_rate_t4_pct"])):""", "        if False:"),
    ("D218: the margin reads the clock time with the wait",
     '            out[c][q] = (sum(x["clock_less_wait_s"] for x in v) / len(v), sum(x["clock_s"] for x in v) / len(v))',
     '            out[c][q] = (sum(x["clock_s"] for x in v) / len(v), sum(x["clock_s"] for x in v) / len(v))'),
    ("D218: check_drawn: the clock dots not compared",
     "            if len(xs) != len(want) or not all(close(x, w) for x, w in zip(xs, want)):", "            if False:"),
    ("D218: the black mean drawn at the clock time with the wait",
     'md = ax.plot([r["clock_less_wait_s_mean"]], [yy]', 'md = ax.plot([r["clock_s_mean_with_wait"]], [yy]'),
    ("D218: Zhang RLM-10's clock read from another draw",
     '            r = last.get(f"cap10|{q}|d{d}")', '            r = last.get(f"cap10|{q}|d{draws[0]}")'),
    ("check_drawn: a cell's colour not compared",
     '        if to_hex(e["artist"].get_facecolor()).upper() != c:', "        if False:"),
    ("check_drawn: a cell's frame not compared",
     '        if (e["frame"] is not None) != (r["interval_excludes_0"] == "yes"):', "        if False:"),
    ("check_drawn: a cell's text not compared", '        if e["text"].get_text() != want:', "        if False:"),
    ("check_drawn: 3e's mark not compared",
     '            if not (close(a_.get_xdata()[0], r["d_pp"]) and close(a_.get_ydata()[0], y_)):', "            if False:"),
    ("check_drawn: 3e's interval not compared",
     '            if not (len(ix) == 2 and close(min(ix), r["ci95_lo_pp"]) and close(max(ix), r["ci95_hi_pp"])',
     '            if False and not (len(ix) == 2 and close(min(ix), r["ci95_lo_pp"]) and close(max(ix), r["ci95_hi_pp"])'),
    ("read_s518: S518's reading not held", '        if it.get("reading") != S518.reading(it["lo"], it["hi"]):',
     "        if False:"),
    ("read_s518_reference: D235's source, role, key and decision not held", "    if got != want:\n",
     "    if False:\n"),
    ("read_s518_reference: the reference's reading not held",
     '    if ref_it.get("reading") != S518.reading(ref_it["lo"], ref_it["hi"]):', "    if False:"),
    ("check_drawn: 3e's axes not compared", '            if e.get("axis") != E3_AXIS[r["measure"]] or tuple',
     '            if False and e.get("axis") != E3_AXIS[r["measure"]] or tuple'),
    ("check_drawn: a reading drawn on 3e not caught", '        if marks("e", "verdict") or drawn_r:', "        if False:"),
    ("3a and 3b: tile rows reversed", "        for c, y in zip(arms, ypos):\n            for j, q in enumerate(ids):",
     "        for c, y in zip(arms, reversed(ypos)):\n            for j, q in enumerate(ids):"),
    ("margins: rows reversed", "    for c, y in zip(rows, ypos):\n        r = rows[c]", "    for c, y in zip(rows, reversed(ypos)):\n        r = rows[c]"),
    ("3f: columns reversed", "                xx = x0s[b] - X + k * CP\n                if r[\"d_pp\"] is None:",
     "                xx = x0s[b] - X + (3 - k) * CP\n                if r[\"d_pp\"] is None:"),
    ("3f: rows reversed", "    for ri, rk in enumerate(E_ROWS):\n        yy = ri * RP\n",
     "    for ri, rk in enumerate(E_ROWS):\n        yy = (len(E_ROWS) - 1 - ri) * RP\n"),
    ("3f: the 'one paper' and 'many papers' labels swapped",
     '("rlm_10", "one"): "RLM-10, one paper", ("rlm_10", "many"): "RLM-10, many papers"',
     '("rlm_10", "one"): "RLM-10, many papers", ("rlm_10", "many"): "RLM-10, one paper"'),
    ("3a: the tile blocks' heads swapped", '(("One paper", x_t), ("Many papers", x_t + w1 + GAPG))',
     '(("Many papers", x_t), ("One paper", x_t + w1 + GAPG))'),
    ("3a: the margin axis from 40", "A_VIEW = (50.0, 100.0) ", "A_VIEW = (40.0, 100.0) "),
    ("3a: a value below 50 clipped by the axes", "    under = [max(0.0, lo - v) for v in lows]\n",
     "    under = [0.0 for v in lows]\n"),
    ("3a: the axis line not cut at 50", "    if bounds:\n        ax.spines", "    if False:\n        ax.spines"),
    ("3c: the reruns drawn again", 'book, X + LAB, Y + 8.0, WC - LAB, 35.2, X + LAB - 1.0, nd, False)',
     'book, X + LAB, Y + 8.0, WC - LAB, 35.2, X + LAB - 1.0, nd, nd > 1)'),
    ("3d: a name on another scatter", '"text": P.text(x0 + cw / 2, y0 - 0.9, LABEL[c], ha="center"',
     '"text": P.text(x0 + cw / 2, y0 - 0.9, LABEL[CONFIGS[-1 - j]], ha="center"'),
    ("the v2.5 units keep the folders as read", 'out["units_v25"] = {k: ({in_repo(p): x for p, x',
     'out["units_v25"] = {k: ({str(p): x for p, x'),
    ("FIG3F O2 undone: sheet Fig. 3f carries S522's run-to-run rows again",
     '    return t["cells"] + t["n"]',
     '    return t["cells"] + t["noise_strategy"] + t["noise_cell"] + t["n"]'),
    ("the stamp counts every answer read, not those on a final-key row",
     '    k1 = read["judge_rows"]["answers_read"] - read["judge_rows"]["awaiting_s6_read"]',
     '    k1 = read["judge_rows"]["answers_read"]'),
    ("G2 not held to its records", "            if (cell[\"kind\"] == \"failed\") != (not ok):", "            if False:"),
    ("G2 not held to S511", "            if abs(mine - want) > 1e-9:", "            if False:"),
    ("read_extra reads a changed question's v2.4 row", '            cell, why = cell_of(ch["row"], groups[q])\n',
     '            cell, why = cell_of(loaded[0].rows[JR.answer_ident(a)], groups[q])\n'),
    ("D155: relocate ignored", "                return v / s_[len(k):].lstrip(\"/\") if s_ != k else v",
     "                return Path(p)"),
    ("D155: units named by the folder read, not the recorded one", "            got[\"folders\"][shown(folder)] =",
     "            got[\"folders\"][str(folder)] ="),
    ("A8: the pull's HEAD from a loose ref only", "        for line in open(os.path.join(cg, \"packed-refs\")):",
     "        for line in []:"),
    ("D155: rebuild does not check the committed record", "    seen = FR.check_recorded(now, recorded, FR.recorded_label)",
     "    seen = {\"compared\": 0, \"not_recorded_before\": []}"),
    ("staging removed: old files deleted before writing", "    for pat in OWNED:\n        for old in out_dir.glob(pat):",
     "    for pat in ():\n        for old in out_dir.glob(pat):"),
]


def mutants(args) -> int:
    """Each code mutant in MUTANTS, run through the whole selftest in this process; killed when the selftest prints
    at least one FAIL line and returns non-zero. A mutant whose selftest crashes outside its checks is not counted as
    killed."""
    import contextlib
    import io
    src = Path(__file__).read_text()
    i0, i1 = src.index("\nMUTANTS = [\n"), src.index("\n\n\ndef mutants(")
    body = src[:i0] + "\x00" + src[i1:]                 # the list itself holds every anchor: left out of the search
    killed, rows = 0, []
    chosen = [m for m in MUTANTS if not getattr(args, "only", None) or args.only in m[0]]
    if getattr(args, "shard", None):
        k, n = (int(x) for x in args.shard.split("/"))
        chosen = chosen[k - 1::n]
    for name, old, new in chosen:
        if body.count(old) != 1:
            rows.append(f"ANCHOR {body.count(old)}x  {name}")
            continue
        m = types.ModuleType("s463_mutant")
        m.__file__ = __file__
        sys.modules["s463_mutant"] = m
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(body.replace(old, new).replace("\x00", src[i0:i1]), __file__, "exec"), m.__dict__)
                rc = m.selftest(types.SimpleNamespace(keep=False), quiet=True)
            fails = [x for x in buf.getvalue().splitlines() if x.startswith("FAIL")]
            ok = rc != 0 and bool(fails)
            killed += ok
            rows.append(f"{'killed' if ok else 'SURVIVED'}  {name}" + (f"  (first: {fails[0][6:120]})" if fails else ""))
        except BaseException as e:                                  # noqa: BLE001
            rows.append(f"CRASHED  {name}  ({type(e).__name__}: {str(e)[:100]})")
    for r in rows:
        print(r)
    print(f"mutants: {killed} of {len(chosen)} killed by a failing check")
    return 0 if killed == len(chosen) else 1


def main(argv=None):
    FR.pin_hash_seed()                              # D155: PDF font subsets depend on the string-hash seed
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("rebuild", help="the committed plate from the frozen inputs (D155)")
    b.add_argument("--out", help=f"default {OUT.relative_to(ROOT)}")
    b.add_argument("--out-s5", help=f"Supplementary Figure 16's folder; default {OUT_S5_NAME} beside --out")
    p = sub.add_parser("pull")
    p.add_argument("--to", required=True)
    r = sub.add_parser("rank")
    r.add_argument("--collect", required=True)
    r.add_argument("--draws", default="1")
    r.add_argument("--answers", action="append", help="a runs folder of generation records; later ones replace "
                                                       "earlier ones' records of the same answer")
    r.add_argument("--replace-out", help="the reruns' out collect was given as --replace (default: out_g1r15 beside "
                                         "the first out)")
    r.add_argument("--out", help=f"default {OUT.relative_to(ROOT)}")
    r.add_argument("--no-plate", action="store_true")
    r.add_argument("--concept-recall-d181", help="D188: the D181 reading of the same answers drawn in panel b "
                                                 "(S471 --d181; default findings/recompute/L3_d181, pinned); read "
                                                 "after --concept-recall, which it is held to")
    r.add_argument("--concept-recall", help="plan row L3's rows (S471: findings/recompute/L3/concept_recall.jsonl, "
                                            "header.json beside it) for panel b; without it panel b is an empty frame")
    r.add_argument("--s6", help="the folder holding out_s6_g1 and out_s6_g1r15 (S6G1, key v2.5; D186 (3)); default the "
                                "folder holding the outs collect read")
    r.add_argument("--extra", help="the folder holding G2's and G6's collects and outs (fig3_s6_inputs); a plate needs it")
    r.add_argument("--fig3e", help="S522's folder (findings/recompute/fig3e); a plate needs it")
    r.add_argument("--s518", help="S518's verdicts (findings/recompute/S518_split_confirmation), drawn as 3e (D195, "
                                  "D218 (3)); without it 3e is an empty frame")
    r.add_argument("--g2-answers", help="G2's answers.jsonl; default the frozen copy S3 judged")
    r.add_argument("--g6-answers", help="D218: Zhang RLM-10's answers.jsonl (3a's clock-time margin); default the "
                                        "frozen G6 records after the D135 reruns (g6_d135_inputs)")
    r.add_argument("--supp6", help="D218 (2): the folder of Supplementary Figure 17's data workbook the margin is held "
                                   f"to; default {SUPP6_DIR.relative_to(ROOT)} (a fixture: not held)")
    r.add_argument("--s511-results", help="S511's results.json: G2's rates are held to its key v2.5 reading")
    r.add_argument("--out-s5", help=f"Supplementary Figure 16's folder; default {OUT_S5_NAME} beside --out")
    f = sub.add_parser("fixture")
    f.add_argument("--to", required=True)
    f.add_argument("--draws", default="1")
    s = sub.add_parser("selftest")
    s.add_argument("--keep", action="store_true")
    mu = sub.add_parser("mutants")
    mu.add_argument("--only", help="the mutants whose name holds these words")
    mu.add_argument("--shard", help="k/n: the k-th of n parts of the list")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "rebuild":
            rebuild(a)
        elif a.cmd == "pull":
            pull(a)
        elif a.cmd == "rank":
            rank(a)
        elif a.cmd == "fixture":
            fixture(a)
        elif a.cmd == "mutants":
            return mutants(a)
        else:
            return selftest(a)
    except (Refused, FR.FrozenInputError) as e:
        print(f"REFUSED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
