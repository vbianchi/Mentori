#!/usr/bin/env python3
"""S447 - plan row A0 (D82): Figure 6's provisional panels, drawn from the S2 records as they stand.

WHY. D82 (experiments/README.md): every panel is drawn as soon as its data exist, by a committed script from the raw
records, stamped with how much data it holds, and the final panel is the same script run again. Figure 6 first: it
needs no judge (a record passes by the field-by-field comparison, the soft-pass judge never decides `passed`,
exp_v2_8_coder_benchmark.py _evaluate_failed_result) and has no open design decision.

Q4 (Valerio, 24 Oct): lung_9_schoenfeld's boolean field could not be read by the harness (fixed in 1f4a9f6), so
draw and figure apply scripts/S477_lung9_rescore.py's flips (its attempts run again with the fixed extraction, no
model call) and stop when its file is missing or was written on other records (apply_q4_rescore()).

TWO STEPS, two commands, both from the repository root:

  1. mirror   uv run --frozen python scripts/S447_fig6_panels.py mirror
     Copies (rsync -a --delete, read only on the source) every S2 sink findings/runs/exp_05__* of the four S2 clones
     (Studio ~/projects/mentori-runs-s2 and -s2-d75 over ssh, laptop ~/projects/mentori-runs-s2-laptop and
     -s2-laptop-d75) into this repository's findings/runs/ under its own run id, and writes
     findings/figures_provisional/fig6/records_manifest.json: per run, the source machine and clone, the clone's
     commit, every file's sha256, size and mtime (rsync -a keeps the source's mtime), the attempts its
     answers.json holds and, per attempt, its own code version (D252: attempt_code_commit, the code_commit its own
     calls record, joined by ctx_uid; null when they record none, never filled in from the clone). A run id found in two clones stops the mirror (nothing is copied). A variant still running is
     copied as far as it is; an answers.json caught mid-write (it does not parse) is copied again, up to 3 times.
     mirror --from-copy <dir> [--complete-only] reads a local copy of the four clones' sinks in S468's layout instead,
     checked against its SHA256SUMS first. A Studio clone's commit is not read again: it is the one the last manifest
     records, and a run the last manifest holds keeps the commit that manifest gave it. --complete-only keeps the
     variants with all 220 attempts stored (D114 Q30 O-a: the 11 complete variants while the Studio is away).

     D155 (Valerio, 26 October: "it should be all reproducible"): the mirror only writes the manifest and the
     gitignored findings/runs/; what draw, figure and the scripts that import load_mirror() and reproduce() (S478,
     S479, S481, S491) read is the frozen copy the manifest was mirrored from, FROZEN_S2, through
     scripts/fig_repro.frozen() (run_dirs(): the manifest's from_copy SHA256SUMS hash must be the copy's, and every
     file it lists must be there with its sha256). A new mirror is read only once its copy is frozen and named in
     FROZEN_S2.

  2. draw     uv run --frozen python scripts/S447_fig6_panels.py draw [--view-dir <dir>]
     Reads the mirrored sinks only (the trust boundary, README.md:13-27), from the frozen copy (D155, above), each
     answers.json checked against the manifest's sha256, and writes into findings/figures_provisional/fig6/:
       fig6_cells.csv              tidy: one row per (variant, strategy): attempts, pass, fail, failures by kind
       fig6_numbers.json           every plotted number, the data stamp and the provenance
     and the working view fig6_provisional.{png,svg} (panels below) into --view-dir, by default
     <system temporary folder>/S447_fig6_working_view, never into the repository: the view breaks FIGURE_LOCK
     (type from 6.5 to 13 px, a stamp on every panel, provenance in an SVG comment), so it is for reading on this
     computer and is not committed (D92 Q195, audit of 17 October F42). A --view-dir inside the repository is
     refused. Every panel of the view carries the stamp "PROVISIONAL: <n> of <N> attempts, <k> of <V> variants
     complete, records of <time>; after the S4 reruns (D75, D80 V1, D81)", <time> the newest answers.json
     mtime among the mirrored files, <V> and <N> the design's variants and attempts (THE DESIGN below: 11 and 2,420
     while D100's three if-time variants are not complete; D116 took nemotron-3-nano:30b's two out).

  3. figure   uv run --frozen python scripts/S447_fig6_panels.py figure [--final]
     The submission plate, drawn to the editor's figure rules (experiments/FIGURE_RULES.md E1-E8; checked by
     scripts/S448_figure_rules_check.py --figure 6 --dir findings/figures_provisional/fig6). Same reproduce-first
     check and the same records as draw. Writes into findings/figures_provisional/fig6/:
       Figure 6 (provisional, <n> of <N>).{pdf,svg,png}    one page; every size, font, colour and limit read from
                                    experiments/FIGURE_LOCK.toml (D84, D87), none written here: [page]
                                    width_double_mm wide, at most height_max_mm high; the first of [type]
                                    font_families; every text at [type] font_min_pt, panel letters
                                    panel_letter_pt and panel_letter_weight and no panel titles (the journal: no
                                    titles inside a figure; Valerio, Q2, 17 October); [colour] categorical and
                                    continuous; no line under [lines] line_min_pt; text on a coloured cell black or
                                    white, whichever stands out more, held to [type] contrast_min_ratio (ink_on());
                                    no ligatures (FIGURE_RULES.md E1); the PNG is the PDF rasterised at 600 dpi
                                    (MuPDF), so S448 R7 can compare
                                    them pixel by pixel; nothing on the plate but the figure: the data state is in
                                    the file name, never in the file
       Source Data Fig. 6 (provisional, ...).xlsx    one sheet per panel, the numbers plotted
       figure6_numbers.json        the same sheets as JSON (S448 R8 compares the workbook with it), and "printed":
                                    every number printed on the plate, by its SVG group id, with the sheet, row and
                                    format it is written from (S448 R8 (6) holds the plate to the workbook)
       Source Data Fig. 6 caption (provisional, ...).md, legend_draft.md (title and legend), figure6_provenance.json
     Files of an earlier data state ("Figure 6*", "Source Data Fig. 6*") are deleted first. --final names them
     "Figure 6" and is refused unless every attempt of the design is stored (2,420 while D100's three if-time
     variants are not complete; D112 Q15 O-a, D116). The panels:
       a  pass rate per strategy (rows) and variant (columns), [colour] continuous of
          FIGURE_LOCK.toml (cividis), n = 20 per cell, each value in black or white by contrast (ink_on()); the
          variants complete in all 11 strategies only (the panel a rule below), ordered by pooled rate
       b  each strategy's gain over free-form in points, one dot per variant of
          a, median line drawn over the dots; rows in a's order (its own strategy labels under a's, or a's rows
          beside it); tied gains stacked across the row, at right angles to the value axis and never along it,
          1.0 mm apart (0.85 mm dots), so every dot sits at its exact gain and can be counted (tie_offsets()). With
          up to 7 complete variants the rows of b are as tall as its largest tie group needs (from 4.6 mm); with
          more (4.0 mm rows), or a row the height bound shrank, a group the row cannot hold is drawn closer, inside
          the row, with its count printed beside it (and the legend says so)
       c  per model with two or more settings stored, one row per setting, on the
          attempts every setting of the model holds: the pass rate as experiments/LIST.md Rule 2 defines it (approved
          as Q130), the mean over the 20 operations of each operation's share of passing attempts, with the 95%
          percentile interval of that mean over 10,000 resamples of the operations (op_mean(), op_bootstrap(): the
          unit is the operation, Rule 1); n = the operations, with how many attempts each holds; grey dots: the
          strategies whose 20 operations are all in the matched set, stacked upward from just above their
          setting's bar (nearest 1.1 mm above it, so never on the bar or under its marker; the top one at least
          1.95 mm below the bar above, so a group reads with its own bar), ties as in b; no line
          joins a model's settings (the settings are rows, so a line's slope would carry no quantity)
       d  per variant with records, the share of its n attempts failed, stacked by folded
          kind in fail_kind()'s order, Okabe-Ito colours, and each kind also its own fill pattern (KIND_PATTERN: the
          journal asks for patterns instead of or in addition to colours, FIGURE_LOCK.toml [colour] patterns), in
          the bars and in the key; a variant with fewer than 20 attempts gets no bar ("too few attempts"); every kind
          is named in the key, and the legend defines the three whose key label does not explain itself
          (LEGEND_KIND_DEF; KIND_DEF holds every kind's full rule)
     Both layouts read a, b along the first row and c, d along the second, a's colour bar upright at a's right.
     With up to 7 complete variants b has its own strategy labels and d's key lies under d; with more, b reads a's
     strategy rows (4.0 mm rows) and d's key runs across the page below. Rows shrink, d's and a's first, only when
     the page would pass the lock's height; no plate is drawn if a text would reach past the page (draw_figure()).

  4. claims   uv run --frozen python scripts/S447_fig6_panels.py claims
     findings/figures_provisional/fig6/claims.md from scripts/S447_fig6_claims_template.md: the Where and Claimed
     columns are the template's (the documents as read on 16 October), every provisional value and the summary are
     computed from fig6_numbers.json (and S445's audit for D75 S4). Refused unless fig6_numbers.json (draw) and
     figure6_provenance.json (figure) carry the same data stamp and records_manifest.json is the one draw read, and
     once every attempt is stored. A clone commit the mirror did not read itself is said to be so.

  5. selftest uv run --frozen python scripts/S447_fig6_panels.py selftest
     Synthetic records only (no run record read, nothing written to the repository): 13 complete variants whose gains
     all tie (every variant but glm-4.7-flash off, which D100 does not run, and nemotron-3-nano:30b's two, which D116
     removed; the layout for more than 7 variants, 13 dots per row of panel b, count labels) and 7 complete variants with mixed ties (1,694 attempts); in both, the
     failed attempts are given every kind of panel d in turn (give_kinds()), so all ten groups are drawn and keyed,
     the tools-refused group among them (D112 Q12 O2); each plate must pass check_drawn() (below) and fit the page,
     hold the tools-refused group in its Source Data and legend, and S448 must pass on it. The stamp has the real form
     ("PROVISIONAL: <n> of <N> attempts, synthetic records ..."), so S448 R8 checks it. Then the second plate is drawn
     seven times more, altered once each (draw_figure's mutate: b_shift, c_shift, c_on_bar, b_crowd, b_offset,
     c_wrong_band, c_clipped), and check_drawn() must fail every one with the problem it was built for. Then panel
     d's patterns (one per kind, all different, each at its smallest whole mark and not below it), the kind rule
     (q193_cases()), the length rule (length_rule_cases(): D114 Q29 O2, with D115 LS1 and LS2), the earlier-event count
     (earlier_label_cases(): D115 L1b), the calls means (calls_mean_cases(): D115 LS1), mirror --from-copy
     --complete-only (copy_cases(): D114 Q30 O-a), claims.md's notes on a commit not read again
     (commit_note_cases()), each attempt's own code commit (attempt_commit_cases(): D252, with a mutant), a
     mutant for each of LS1 (two), LS2, L1b, Q30 and those notes, the design total
     (design_cases(): D100, D112 Q15 O-a) and the thinking diagnostic
     (thinking_cases(): D112 Q17 O-a). Last, the rounding rule (half_up(), and S448's formatter) on exact quarters,
     float noise and signs, and the A25 gap from exact values. The first plate is drawn FINAL (every attempt of its
     design stored), so S448 holds its legend to [legend] words_under, which the short legend (Valerio, 23 October)
     meets. The second is provisional; since D122 (Q3) S448 R9 no longer asks its legend to say "provisional" (the
     legend describes the image only, Valerio, 23 October), so S448 passes both.
     check_drawn() also runs on every plate the figure step writes (a failure keeps nothing, exit 1): every dot of
     b and grey dot of c, read back from the drawn artist (Line2D get_xdata / get_ydata), holds its Source Data
     value as the workbook just written holds it, and lands on the page (placed by the artist's own transform,
     artist.get_transform()) within 0.01 mm of where its axes put that value, as do c's mean markers and bar ends;
     b's dots stay inside their rows; c's grey dots stay whole inside their own setting's band and inside the axes
     (none clipped); no dot overlaps a dot of another group; every tie is countable (white between neighbours) or
     counted; no count label covers a dot, a median or another label; and no grey dot of c has its centre within a
     mean marker's radius or touches a marker or bar.
  ROUNDING. Every number S447 prints (the plates, the legend, the Source Data caption, claims.md and its gap table)
     is rounded once by half_up(): to 1e-9 first, so float noise is gone (54.25000000000001 is 54.25), then half away
     from zero (69.25 -> 69.3, 12.5 -> 13). A gap is the exact provisional value less the exact text value, then
     rounded. The plate's printed numbers are written through HalfUpFormatter from the format the numbers file
     records, and S448 R8 (6) fills that format the same way.
     S447_SELFTEST_KEEP=<dir> keeps both folders (S448 --mutants --stale-from <dir>/7_mixed uses the second).

THE DESIGN (experiments/LIST.md "Figure 6. Code generation"; D22, D49, D63, D71, Q13). 16 variants (the runner's own
list: exp_05_coder_benchmark.py --dry-run, "variants: 16 of 10 models; attempts: 3520") x 11 strategies x 20
operations x one draw. D100 demoted three of them to if-time (deepseek-r1:70b default and glm-4.7-flash:bf16 default,
stopped 19 October; glm off, not run): each is out of the figure's total, its stamp and the --final test, and is not
drawn, unless all its 220 attempts are stored (D112 Q15 O-a, audit A21-19; IF_TIME, design_of()), so the figure's
design is 13 variants and 2,860 attempts while none of them is complete. D116 (Valerio, 22 October) removed
nemotron-3-nano:30b from every experiment: its two variants are out of the design, the stamp, the --final test and
every panel whether or not their attempts are stored (their stored attempts are kept, not reported; REMOVED,
design_of()), and the legend says so in one sentence; the design is 11 variants and 2,420 attempts. Since every one
of them is complete while the reruns are still owed, the legend's provisional sentence follows the stamp (PROVISIONAL
until figure --final), not the stored count. The submitted plate
(manuscript/submission/figures/Figure_6.png, scripts/S290_figure6.R) had
  a  per strategy, the median model, IQR and range of the per-model pass rates;
  b  the model by strategy heatmap of pass rates, models ordered by their pooled rate;
  c  the 2,048-token arm against 24,576, removed by D22.
Here a and b are kept as they were drawn (same strategy order and labels as S290's SLAB), and c is replaced by the
named factor of the new design (Q13): the thinking level, per model, pass rate with its 95% interval over resampled
operations at each setting the model runs (off and default; gpt-oss:20b low, medium, high). In the plate the heatmap is a and the
per-strategy spread is replaced by each strategy's gain over free-form (b). A fourth panel d shows the failures by
kind per variant, the counts behind the reruns S4 owes (D80 V1, D81).
Panel a compares the strategies over one set of variants: those complete in every strategy (all 220 attempts
stored), so a strategy never rests on more variants than another's. In the working view (draw) a variant still
partial appears in the heatmap with its n (and in c and d), never in the per-strategy panel; in the plate it appears
in c and d only. A model with one variant is labelled in c from
LOCK.toml [sampling.models] think: "omit" (no thinking mode) reads "default (= off)", "always" reads "default
(always thinks)".

WHAT COUNTS. An attempt is one entry of answers.json `results` (deduplicated by answer_key: a key seen twice keeps
the last entry and the duplicate is counted). PASS is the record's `passed` (all fields within tolerance,
verify_results), with one rule over it, D114 Q29 O2 (Valerio, 22 October): an attempt ends at its first length stop
(a generator call with status or stop_reason "length") and is recorded as "length", for every variant's stored
attempts alike, whichever --length-stop rule exp_05 ran them under. apply_length_rule() reads each attempt only up to
that call: a pass after it is a failure (passed False, exec_outcome "length", the stored values kept in the attempt's
length_rule), its later calls are neither its kind nor a rerun it owes, and fig6_numbers.json counts what the rule
changed per variant (length_rule_d114_by_variant). A cell is a (variant, strategy) pair; its rate is pass / attempts stored, so a cell still running
is a rate over fewer than 20 and is drawn with its n. Failures by kind: each failed attempt gets the first kind
that applies, in this order (fail_kind() below). Kinds 1 to 6 are read from the call that ended the attempt: its last
generator call in calls.jsonl (joined by ctx_uid, the highest seq; D92 Q193, audit of 17 October F20), and kinds 1 to
5 also from an earlier generator call after which the attempt made no notebook cell (D94 Q-b O2): an event the
attempt went on to make a cell after is not its cause, one it never made a cell after stays its cause. A call makes a
cell when it returns add_cell as a native tool call, or as a call D81's reader took from its text (the record's
tool_calls_from_text); the event's own call counts, since a call read from text made its cell (cell_after()). In a
best-of-3 or combined round the cell is made after the round's last call (candidates and cell judge,
step_executor.py:418-432), and a candidate's add_cell is not a cell (cell_seqs()). Only
the structured strategies (coder_v2) call add_cell; in the others the harness runs the reply's code itself and no call
makes a cell, so there an earlier event always stays the cause; draw and figure print how many failed attempts of
those strategies take their kind from an earlier event, on screen only (earlier_label_count(); D115 L1b O-a): 0 of
380 on the copy of 21 October (records_manifest.json of 22 October). On the records of 16 October (that day's
records_manifest.json) Q193 alone moved 44 of the 69 attempts that had
the event kinds (then 1 to 4) to later kinds; O2 returns the 7 of them that made no cell after the event (all
deepseek-r1:70b, structured, none with a cell at all) to tool call written as text. rerun_tally() still counts an event
on any call, since D80 V1 owes a rerun for it either way:
  tool-call parse error      a call errored with "error parsing tool call" (D80 V1 retries these, Ollama only)
  tool call written as text  a step_executor reply with no native tool call writes add_cell as text (D80 V1, D81
                             Q137)
  stall                      a call has status "stalled" (D80 V1)
  tools refused by Ollama    a call failed with Ollama's HTTP 400 "does not support tools" (the model as Ollama serves
                             it has no tool template, so the tools never reached it; gemma3:27b's structured
                             strategies), or the attempt's exec_error carries that text; its own kind and its own
                             group in panel d (D112 Q12 O2, audit A21-21), never "other call error"
  other call error           a call failed otherwise: another HTTP 400, an HTTP 500, a dropped connection, Gemini's
                             malformed call; or the attempt's exec_outcome is "call_error"
                             (each of these five: the last call, or an earlier one with no cell made after it)
  length stop                the last call stopped on "length"; since D114 Q29 O2 an attempt is read only up to its
                             first length stop (apply_length_rule()), so this is every attempt with one, unless an
                             event of kinds 1 to 5 before it is its cause
  harness error              exec_outcome "exception": the harness raised, not the model's code (Q60's 'module')
  step produced no cell and no error   exec_error carries "Step failed: None". coder_v2 ends a structured step with a
                             step_failed event when an execution of the step created no notebook cell, and sends as
                             its error the execution's error message (coder_v2.py:512-518). execute_step sets that
                             message only from an exception or from an executed cell that errored
                             (step_executor.py:532-555), so an execution that returned normally and created no cell
                             sends None, which the harness stored as "Step failed: None" (exp_v2_8_coder_benchmark.py
                             :1314-1322). The execution may be the step's first or a retry its cell evaluation asked
                             for. Records written by D75 Q101's code store the reason instead ("Step failed: step <k>:
                             no cell created, ...", exp_v2_8_coder_benchmark.py:1208-1219) and do not match here: 2
                             such records on 16 October (gpt-oss:20b medium), one counted as tool call written as text
                             and one as code raised or timed out (proposal O1 of round 3: match both forms)
  Gemini empty reply         a Gemini attempt whose last generation stored an empty reply
  no code                    exec_outcome "not_run", or no code or code cells stored
  code raised or timed out   the code raised or timed out and printed no result
  result wrong or missing    the code ran and its printed result does not match
  other                      anything else
Panel d folds these to ten groups (FOLD). Gemini calls that return no text but a native tool call are normal and
are not read as empty.

REPRODUCE FIRST (README.md:75-79). Before writing anything, draw recounts the attempts per variant that S445's audit
states (findings/recompute/S445_s2_d75_audit/{studio,laptop}.json, status.variants.*.attempts) on the very files S445
read: each answers.json named in S445's inputs_sha256 is located by its sha256 in the frozen sets (D155: FROZEN_S2 and
FROZEN_S445; S445's own path, outside the repository, is not read),
counted with the same function the panels use, and every variant must give S445's count; it stops (exit 2, nothing
written) if one differs or a file cannot be found.

No model call; no Ollama port is contacted.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "findings" / "runs"
OUT = ROOT / "findings" / "figures_provisional" / "fig6"
MANIFEST = OUT / "records_manifest.json"
S445 = ROOT / "findings" / "recompute" / "S445_s2_d75_audit"
# D155 (Valerio, 26 October: "it should be all reproducible"): draw, figure and every script that calls load_mirror()
# or reproduce() (S478, S479, S481) read the S2 records from frozen copies only, through scripts/fig_repro.frozen(),
# never from a live clone, a scratch folder or the gitignored findings/runs/. FROZEN_S2 is the copy the committed
# records_manifest.json was mirrored from (mirror --from-copy): since 5 November 2026 (fig6 spec A4, D201 Q2) the tar of
# ~/Mentori_scratch_keep/s2_after_s4_20261105, the four clones' sinks after S4's 165 reruns
# (frozen_inputs/freeze_s2_s4.py); before it, s2_length_retries_20261021 (the copy of 21 October, mirrored 22
# October), which S525 and S481's reproduce-first gate still read. Both are listed in
# findings/recompute/frozen_inputs/SHA256SUMS and laid out as S468's copy (copy_runs()). FROZEN_S445 (committed, findings/recompute/fig6_inputs/s445_records/) holds the 4 of the
# 80 answers.json S445's audit read on 16 October whose bytes changed before the copy of 21 October, so reproduce()
# finds every file S445 read, by sha256, in the two frozen sets.
FROZEN_S2 = "s2_after_s4_20261105"
FROZEN_S2_BEFORE_S4 = "s2_length_retries_20261021"   # reproduce() and S481's gate still read it
FROZEN_S445 = ("fig6", "s445_records")
STAMP_TZ = "Europe/Amsterdam"   # the zone every stamp prints its time in, whatever the building computer's zone
LOCK = ROOT / "experiments" / "LOCK.toml"
D80_COMMIT = "6f0a67a"          # D80 V1/V4/V5/V6 and D81 built (git log); a clone at a commit without it ran the old code
STUDIO = "10.15.212.253"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]

# The four S2 clones (experiments/RUNNING.md, "S2: Figure 6"): (machine, host or None for local, clone path)
SOURCES = [
    ("studio", STUDIO, "projects/mentori-runs-s2"),
    ("studio", STUDIO, "projects/mentori-runs-s2-d75"),
    ("laptop", None, "projects/mentori-runs-s2-laptop"),
    ("laptop", None, "projects/mentori-runs-s2-laptop-d75"),
]

# Figure 6's 16 variants, as exp_05_coder_benchmark.py --dry-run lists them (run_id extra), with the model each
# belongs to and the thinking setting; and the 11 strategies in S290_figure6.R's order and labels (SLAB).
VARIANTS = [
    ("qwen3-coder-30b+default", "qwen3-coder:30b", "default"),
    ("qwen3-coder-next-q4_K_M+default", "qwen3-coder-next", "default"),
    ("gpt-oss-20b+low", "gpt-oss:20b", "low"),
    ("gpt-oss-20b+medium", "gpt-oss:20b", "medium"),
    ("gpt-oss-20b+high", "gpt-oss:20b", "high"),
    ("glm-4.7-flash-bf16+default", "glm-4.7-flash", "default"),
    ("glm-4.7-flash-bf16+off", "glm-4.7-flash", "off"),
    ("nemotron-3-nano-30b+default", "nemotron-3-nano:30b", "default"),
    ("nemotron-3-nano-30b+off", "nemotron-3-nano:30b", "off"),
    ("gemma3-27b+default", "gemma3:27b", "default"),
    ("devstral-small-2-24b+default", "devstral-small-2:24b", "default"),
    ("deepseek-r1-70b+default", "deepseek-r1:70b", "default"),
    ("gemini-2.5-pro+default", "gemini-2.5-pro", "default"),
    ("gemini-2.5-pro+off", "gemini-2.5-pro", "off"),
    ("gemini-3-flash-preview+default", "gemini-3-flash", "default"),
    ("gemini-3-flash-preview+off", "gemini-3-flash", "off"),
]
VMODEL = {v: m for v, m, _ in VARIANTS}
VTHINK = {v: t for v, _, t in VARIANTS}
STRATEGIES = [
    ("free_form", "free-form"), ("free_form_n3_best", "free-form best of 3"),
    ("free_form_n3_combined", "free-form combined"), ("error_recovery_introspect", "error-recovery introspect"),
    ("introspect_then_code", "introspect then code"), ("introspect_with_recovery", "introspect with recovery"),
    ("thinker_coder_split", "thinker-coder split"), ("coder_v2_n1", "structured"),
    ("coder_v2_n1_cell3_best", "structured best of 3"), ("coder_v2_n1_cell3_combined", "structured combined"),
    ("coder_v2_n3", "structured x3"),
]
SLAB = dict(STRATEGIES)
N_OPS, N_DRAWS = 20, 1
PER_CELL = N_OPS * N_DRAWS
PER_VARIANT = PER_CELL * len(STRATEGIES)
TOTAL = PER_VARIANT * len(VARIANTS)          # 3,520 (D71): the runner's design; the figure's total is design_of()'s
# D100 (Valerio, 19 October): deepseek-r1:70b default and glm-4.7-flash:bf16 default demoted to if-time and out of
# Figure 6 unless time allows (both stopped 19 Oct 19:34, their records kept); glm off, queued behind them, not run.
# D112 Q15 O-a (audit A21-19): out of the figure's total, its stamp and the --final test unless all PER_VARIANT of a
# variant's attempts are stored; a variant of this set with fewer is not drawn (design_of(), keep_design()).
IF_TIME = {"deepseek-r1-70b+default": "D100", "glm-4.7-flash-bf16+default": "D100", "glm-4.7-flash-bf16+off": "D100"}
assert set(IF_TIME) <= {v for v, _, _ in VARIANTS}
# D116 (Valerio, 22 October): nemotron-3-nano:30b removed from every experiment; both variants stopped 22 Oct 16:08,
# their stored attempts kept intact and not reported. Out of the design whether or not their attempts are stored.
REMOVED = {"nemotron-3-nano-30b+default": "D116", "nemotron-3-nano-30b+off": "D116"}
assert set(REMOVED) <= {v for v, _, _ in VARIANTS} and not set(REMOVED) & set(IF_TIME)
REMOVED_SENTENCE = ("Not shown: nemotron-3-nano:30b, dropped from every experiment because it could not finish "
                    "within the revision (D116).")


def design_of(attempts):
    """The figure's design over these attempts (D100, D112 Q15 O-a, D116): (variants, total, left out). The variants
    are VARIANTS in order, less each REMOVED variant (D116, always) and each IF_TIME variant that does not have all
    PER_VARIANT attempts stored; total is PER_VARIANT times their number (2,420 for 11 variants, 3,080 when all three
    if-time variants are complete); left out maps each if-time variant with some but not all attempts stored to that
    count (a REMOVED variant is never in it: its attempts are not reported)."""
    stored = Counter(variant_of(a["run_id"]) for a in attempts)
    vs = [v for v, _, _ in VARIANTS if v not in REMOVED and (v not in IF_TIME or stored[v] == PER_VARIANT)]
    left = {v: stored[v] for v, _, _ in VARIANTS if v in IF_TIME and v not in vs and stored[v]}
    return vs, PER_VARIANT * len(vs), left


def keep_design(attempts):
    """The attempts of the design's variants only (design_of()), and the design: (kept, variants, total, left out)."""
    vs, total, left = design_of(attempts)
    keep = set(vs)
    return [a for a in attempts if variant_of(a["run_id"]) in keep], vs, total, left


# ---------------------------------------------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args, cwd=ROOT) -> str:
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_local(ts: float) -> str:
    """A time as the stamps print it, in STAMP_TZ whatever the zone of the computer that builds (D155: one text on
    every machine; the plates of 25 and 26 October were built in this zone)."""
    from zoneinfo import ZoneInfo
    return dt.datetime.fromtimestamp(ts, ZoneInfo(STAMP_TZ)).strftime("%Y-%m-%d %H:%M %Z")


def frozen_copy() -> Path:
    """The frozen S2 copy's top folder (FROZEN_S2). fig_repro.frozen() checks the tar's sha256 against
    findings/recompute/frozen_inputs/SHA256SUMS, extracts it once, and checks every extracted file on each call."""
    import fig_repro
    return fig_repro.frozen(FROZEN_S2, FROZEN_S2)


def run_dirs(man) -> dict:
    """{run id: its folder in the frozen copy} for every run of the manifest. Refused unless the manifest was mirrored
    from this copy (its from_copy SHA256SUMS hash is the copy's) and every file the manifest lists for a run is in
    the copy with the sha256 the manifest records. A manifest of a later mirror is refused here until its copy is
    frozen too (D155) and named in FROZEN_S2."""
    copy = frozen_copy()
    via = man["provenance"].get("from_copy") or {}
    got = sha256_file(copy / "SHA256SUMS")
    if via.get("sha256sums_sha256") != got:
        raise SystemExit(f"{MANIFEST.relative_to(ROOT)} was not mirrored from the frozen copy {FROZEN_S2} (its "
                         f"SHA256SUMS {got[:12]}, the manifest's {str(via.get('sha256sums_sha256'))[:12]}): freeze the "
                         f"copy the manifest was mirrored from and name it in FROZEN_S2 (D155)")
    out = {}
    for rid, info in man["runs"].items():
        d = copy_runs(copy, info["machine"] == "studio", info["clone"].removeprefix("~/")) / rid
        for name, f in info["files"].items():
            p = d / name
            if not p.is_file() or sha256_file(p) != f["sha256"]:
                raise SystemExit(f"{rid}/{name}: not in the frozen copy {FROZEN_S2} with the manifest's sha256 "
                                 f"{f['sha256'][:12]}")
        out[rid] = d
    return out


def variant_of(run_id: str) -> str:
    return run_id.split("__", 2)[2]


def config_of(run_id: str) -> str:
    return run_id.split("__", 2)[1]


def attempts_of(answers_path: Path):
    """The attempts of one answers.json, deduplicated by answer_key (last entry kept). Returns (attempts, n_dup)."""
    res = json.loads(answers_path.read_text())["results"]
    by_key = {}
    for a in res:
        by_key[a["answer_key"]] = a
    return list(by_key.values()), len(res) - len(by_key)


def count_per_variant(paths):
    """Attempts per variant over these answers.json files (the panels' own count)."""
    c = Counter()
    for p in paths:
        atts, _ = attempts_of(p)
        for a in atts:
            c[variant_of(a["run_id"])] += 1
    return c


# ---------------------------------------------------------------------------------------------------------------
# Step 1: mirror
# ---------------------------------------------------------------------------------------------------------------
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def list_sinks(host, clone, copy=None):
    if copy is not None:                              # a local copy of the clone's sinks (mirror --from-copy)
        base = copy_runs(copy, host, clone)
        return sorted(d.name for d in base.glob("exp_05__*") if d.is_dir()) if base.is_dir() else []
    if host is None:
        base = Path.home() / clone / "findings" / "runs"
        return sorted(d.name for d in base.glob("exp_05__*") if d.is_dir()) if base.is_dir() else []
    r = run(SSH + [host, f"cd ~/{clone}/findings/runs 2>/dev/null && for d in exp_05__*; do [ -d \"$d\" ] && "
                         f"echo \"$d\"; done; true"])
    if r.returncode != 0:
        raise SystemExit(f"ssh {host}: {r.stderr.strip()}")
    return sorted(x for x in r.stdout.split() if x.startswith("exp_05__"))


def clone_commit(host, clone):
    if host is None:
        return git("rev-parse", "HEAD", cwd=Path.home() / clone)
    return run(SSH + [host, f"git -C ~/{clone} rev-parse HEAD"]).stdout.strip()


def copy_runs(copy, host, clone):
    """A clone's sinks in a local copy laid out as S468's (<copy>/<machine>/<clone name>/runs/exp_05__*/), the
    machine named by the host as SOURCES does."""
    return Path(copy) / ("studio" if host else "laptop") / Path(clone).name / "runs"


def rsync_one(host, clone, run_id, copy=None):
    src = (f"{copy_runs(copy, host, clone) / run_id}/" if copy is not None else
           f"{host}:~/{clone}/findings/runs/{run_id}/" if host else
           f"{Path.home() / clone / 'findings' / 'runs' / run_id}/")
    host = None if copy is not None else host
    dst = RUNS / run_id
    dst.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a", "--delete"] + (["-e", " ".join(SSH)] if host else []) + [src, f"{dst}/"]
    r = run(cmd)
    if r.returncode != 0:
        raise SystemExit(f"rsync {src}: {r.stderr.strip()}")


def attempt_code_commits(run_dir):
    """D252: each attempt's own code version, {answer_key: commit or None}, for the attempts of one run (answers.json
    deduplicated as attempts_of()). The commit is the code_commit the attempt's own calls record (calls.jsonl, joined
    by ctx_uid); None when none of its calls records one (the October code wrote no code_commit), never filled in from
    the clone's commit. Refused when one attempt's calls name two commits, or a call records code_dirty true."""
    by_ctx = defaultdict(set)
    calls = run_dir / "calls.jsonl"
    if calls.exists():
        with open(calls) as f:
            for ln in f:
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if r.get("code_commit") and r.get("ctx_uid"):
                    if r.get("code_dirty"):
                        raise SystemExit(f"{run_dir.name}: a call of ctx_uid {r['ctx_uid']} ran on a dirty tree at "
                                         f"{r['code_commit'][:9]}; no version recorded")
                    by_ctx[r["ctx_uid"]].add(r["code_commit"])
    out = {}
    ans = run_dir / "answers.json"
    for a in (attempts_of(ans)[0] if ans.exists() else []):
        cs = by_ctx.get(a.get("ctx_uid"), set()) if a.get("ctx_uid") else set()
        if len(cs) > 1:
            raise SystemExit(f"{run_dir.name} {a['answer_key']}: its calls name {len(cs)} commits {sorted(cs)}")
        out[a["answer_key"]] = next(iter(cs), None)
    return out


def complete_in(paths_by_rid):
    """The variants whose sinks hold all PER_VARIANT attempts (mirror --complete-only; D114 Q30 O-a)."""
    c = Counter()
    for rid, p in paths_by_rid.items():
        if p.exists():
            c[variant_of(rid)] += len(attempts_of(p)[0])
    return {v for v, n in c.items() if n == PER_VARIANT}


def mirror(argv, copy=None, complete_only=False):
    """copy: a local copy of the four clones' sinks in S468's layout (copy_runs()), read instead of the clones when
    the Studio cannot be reached; its copy_log.tsv and SHA256SUMS go into the manifest, every file is checked against
    SHA256SUMS first, a Studio clone's commit is the one the last manifest read over ssh (not read again), and a run
    the last manifest holds from the same clone keeps that manifest's commit for it.
    complete_only: only the variants with all PER_VARIANT attempts stored (D114 Q30 O-a: the 11 complete variants).
    complete_only without copy is refused before any clone is listed or read (no ssh)."""
    if complete_only and copy is None:
        raise SystemExit("--complete-only reads the sinks before copying: give --from-copy")
    found = {}
    for machine, host, clone in SOURCES:
        for rid in list_sinks(host, clone, copy):
            if rid in found:
                raise SystemExit(f"{rid} is in two clones ({found[rid][1]} and {clone}); nothing copied")
            found[rid] = (machine, clone, host)
    if copy is None:
        commits = {clone: clone_commit(host, clone) for _, host, clone in SOURCES}
        via = None
    else:
        copy = Path(copy).expanduser().resolve()
        sums = {}
        for ln in (copy / "SHA256SUMS").read_text().splitlines():
            if ln.strip():
                h, rel = ln.split(None, 1)
                sums[rel.lstrip("*").removeprefix("./")] = h
        bad = [rel for rel, h in sums.items() if sha256_file(copy / rel) != h]
        if bad:
            raise SystemExit(f"{len(bad)} file(s) of {copy} differ from its SHA256SUMS, e.g. {bad[0]}; nothing copied")
        before = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"sources": [], "runs": {}}
        was = f"the manifest of {before['provenance']['written_utc']}" if before["sources"] else ""
        last = {s["clone"]: (s["commit"], s.get("commit_read", f"ssh, {was}")) for s in before["sources"]}
        commits, read = {}, {}
        for _, host, clone in SOURCES:
            if host is None:
                commits[clone], read[clone] = clone_commit(None, clone), f"git rev-parse HEAD, {utc_now()}"
            else:
                commits[clone], read[clone] = last.get(f"~/{clone}", ("", "not known"))
        # a variant never mixes code (experiments/RUNNING.md, S2): a run the last manifest holds from the same clone
        # keeps the commit it was mirrored with, though the clone has moved since (gpt-oss:20b medium: e89eaf5, its
        # clone at 6457ae6 from 17 October)
        run_commit = {rid: (r["clone_commit"], was) for rid, r in before["runs"].items()}
        via = {"copy": str(copy).replace(str(Path.home()), "~"), "copy_log_tsv": (copy / "copy_log.tsv").read_text(),
               "sha256sums_sha256": sha256_file(copy / "SHA256SUMS"), "files_checked": len(sums),
               "commit_read": read, "run_commit_from_last_manifest": []}
    if complete_only:
        keep = complete_in({rid: copy_runs(copy, host, clone) / rid / "answers.json"
                            for rid, (_, clone, host) in found.items()})
        found = {rid: x for rid, x in found.items() if variant_of(rid) in keep}
    RUNS.mkdir(parents=True, exist_ok=True)
    runs_out = {}
    for rid, (machine, clone, host) in sorted(found.items()):
        for attempt in range(3):
            rsync_one(host, clone, rid, copy)
            ans = RUNS / rid / "answers.json"
            try:
                n = len(attempts_of(ans)[0]) if ans.exists() else 0
                break
            except (json.JSONDecodeError, KeyError):
                if attempt == 2:
                    raise SystemExit(f"{rid}: answers.json does not parse after 3 copies")
        files = {}
        for p in sorted((RUNS / rid).rglob("*")):
            if p.is_file():
                st = p.stat()
                files[str(p.relative_to(RUNS / rid))] = {
                    "sha256": sha256_file(p), "bytes": st.st_size,
                    "mtime": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        cm = commits[clone]
        if via and rid in run_commit and before["runs"][rid]["clone"] == f"~/{clone}" and run_commit[rid][0] != cm:
            cm = run_commit[rid][0]
            via["run_commit_from_last_manifest"].append(f"{rid}: {cm[:9]} ({run_commit[rid][1]})")
        runs_out[rid] = {"machine": machine, "clone": f"~/{clone}", "clone_commit": cm, "attempts": n,
                         "attempt_code_commit": attempt_code_commits(RUNS / rid), "files": files}
    own = Counter(c or "none in the record" for r in runs_out.values() for c in r["attempt_code_commit"].values())
    OUT.mkdir(parents=True, exist_ok=True)
    man = {
        "provenance": {"script": "scripts/S447_fig6_panels.py", "script_sha256": sha256_file(Path(__file__)),
                       "command": "uv run --frozen python scripts/S447_fig6_panels.py " + " ".join(argv),
                       "written_utc": utc_now(), "repo_head": git("rev-parse", "--short", "HEAD"),
                       "script_dirty_vs_head": git("status", "--short", "--", str(Path(__file__))),
                       "method": "rsync -a --delete per run directory, read only on the source; mtime is the "
                                 "source's (rsync -a)", "model_calls": 0,
                       "from_copy": via, "complete_only": complete_only,
                       "attempt_code_commit": "D252: per run, each attempt's own code version by answer_key, the "
                                              "code_commit its own calls record (calls.jsonl, joined by ctx_uid); "
                                              "null when its calls record none, never filled in. clone_commit is "
                                              "the clone's commit the mirror gives the run, not read from a record"},
        "sources": [{"machine": m, "clone": f"~/{c}", "commit": commits[c],
                     **({"commit_read": via["commit_read"][c]} if via else {}),
                     "runs": sorted(r for r, v in found.items() if v[1] == c)} for m, _, c in SOURCES],
        "runs": runs_out,
        "attempts_total": sum(v["attempts"] for v in runs_out.values()),
        "attempts_by_own_code_commit": dict(sorted(own.items())),
    }
    MANIFEST.write_text(json.dumps(man, indent=1) + "\n")
    print(f"mirrored {len(runs_out)} runs, {man['attempts_total']} attempts -> "
          f"{MANIFEST.relative_to(ROOT) if ROOT in MANIFEST.parents else MANIFEST}")
    for s in man["sources"]:
        print(f"  {s['machine']:7s} {s['clone']:38s} {s['commit'][:9]}  {len(s['runs'])} runs")
    print("  attempts by their own code commit (D252): " +
          ", ".join(f"{k if k.startswith('none') else k[:9]} {n}" for k, n in man["attempts_by_own_code_commit"].items()))


# ---------------------------------------------------------------------------------------------------------------
# Step 2: draw. Reading the mirrored records
# ---------------------------------------------------------------------------------------------------------------
def load_mirror():
    """Every attempt of the mirrored sinks, each answers.json checked against the manifest. Returns (attempts by
    variant, call flags by ctx_uid, inputs, notes).
    D155: the files are read from the frozen copy the manifest was mirrored from (run_dirs()), not from findings/runs/.
    inputs keeps the names the manifest gives them (findings/runs/<run id>/<file>, the mirror's paths, which S477's
    re-score and the committed provenance files name too), each with the sha256 of the bytes read; the frozen tar's
    sha256 is added under its own name. The newest answers.json time is the one the manifest records (the source's
    mtime, rsync -a), since a tar member's mtime is 0."""
    if not MANIFEST.exists():
        raise SystemExit(f"{MANIFEST.relative_to(ROOT)} missing: run the mirror step first")
    man = json.loads(MANIFEST.read_text())
    dirs = run_dirs(man)
    attempts, inputs, dups, unreadable = [], {}, Counter(), Counter()
    flags = defaultdict(set)
    last = {}                                     # per ctx_uid: (seq, flags, made a cell) of each generator call
    call_dates = {}
    reasoning = defaultdict(Counter)              # per variant: generator calls, and those that returned reasoning
    by_machine = defaultdict(Counter)             # per variant: attempts by machine, clone and clone commit
    for rid, info in sorted(man["runs"].items()):
        d = dirs[rid]
        for name in ("answers.json", "calls.jsonl"):
            p = d / name
            if name not in info["files"]:
                continue
            h = sha256_file(p)
            if h != info["files"][name]["sha256"]:
                raise SystemExit(f"{p} differs from the manifest (sha256 {h[:12]} against "
                                 f"{info['files'][name]['sha256'][:12]})")
            inputs[str((RUNS / rid / name).relative_to(ROOT))] = h
        by_machine[variant_of(rid)][f"{info['machine']} {info['clone']} {info['clone_commit'][:9]}"] += \
            info["attempts"]
        if (d / "answers.json").exists():
            atts, n_dup = attempts_of(d / "answers.json")
            dups[rid] = n_dup
            attempts.extend(atts)
        if (d / "calls.jsonl").exists():
            with open(d / "calls.jsonl") as f:
                for ln in f:
                    if not ln.strip():
                        continue
                    try:
                        r = json.loads(ln)
                    except json.JSONDecodeError:
                        unreadable[rid] += 1
                        continue
                    call_flags(r, flags, last)
                    if r.get("role") == "generator":
                        rv = reasoning[variant_of(rid)]
                        rv["generator_calls"] += 1
                        rv[thinking_sent(r)] += 1
                        rv["returned_reasoning_text"] += bool((r.get("thinking_text") or "").strip())
                    if r.get("role") == "generator" and r.get("at"):
                        prov = r.get("provider") or "?"
                        lo_hi = call_dates.setdefault(prov, [r["at"], r["at"]])
                        lo_hi[0], lo_hi[1] = min(lo_hi[0], r["at"]), max(lo_hi[1], r["at"])
    length_rule = apply_length_rule(attempts, flags, last)   # D114 Q29 O2: before the kinds are read
    end_flags(flags, last)                        # the cause's calls (D92 Q193, D94 Q-b O2): their flags as "end:"
    newest = max(dt.datetime.strptime(info["files"]["answers.json"]["mtime"], "%Y-%m-%dT%H:%M:%SZ")
                 .replace(tzinfo=dt.timezone.utc).timestamp()
                 for rid, info in man["runs"].items() if "answers.json" in info["files"])
    notes = {"duplicates_dropped": {k: v for k, v in dups.items() if v}, "calls_lines_unreadable": dict(unreadable),
             "manifest_written_utc": man["provenance"]["written_utc"],
             "sources": [{k: s[k] for k in ("machine", "clone", "commit")} | {"runs": len(s["runs"])}
                         for s in man["sources"]],
             "newest_answers_mtime": newest, "generator_call_dates_by_provider": call_dates,
             "attempts_by_machine": {v: dict(c) for v, c in sorted(by_machine.items())},
             "generator_reasoning_by_variant": {v: dict(c) for v, c in sorted(reasoning.items())},
             "length_rule_d114_by_variant": length_rule}
    notes["q4_lung9_rescore"] = apply_q4_rescore(attempts, inputs)   # Q4 (24 Oct): after the kinds' inputs are read
    inputs[str(MANIFEST.relative_to(ROOT))] = sha256_file(MANIFEST)
    import fig_repro
    inputs[f"frozen {FROZEN_S2}.tar"] = fig_repro._read_sums(fig_repro.RECOMPUTE / "frozen_inputs" /
                                                             "SHA256SUMS")[f"{FROZEN_S2}.tar"]
    return attempts, flags, inputs, notes


Q4_RESCORE = ROOT / "findings" / "recompute" / "S477_lung9_rescore.json"


def apply_q4_rescore(attempts, inputs):
    """Q4 (Valerio, 24 Oct): the harness could not read lung_9_schoenfeld's boolean field (fixed in 1f4a9f6), so
    every attempt of it failed. scripts/S477_lung9_rescore.py ran each attempt's own code again (no model call) with
    the fixed extraction; an attempt that reproduced its stored run and passes now is a flip. Each flip passes here,
    with S477's field and actual results. S477's file is required, must name this manifest by sha256 and every
    answers.json this read by the sha256 read here; otherwise this stops (run S477 again after a mirror). Returns
    S477's counts and its sha256, for the numbers file."""
    if not Q4_RESCORE.exists():
        raise SystemExit(f"{Q4_RESCORE.relative_to(ROOT)} missing: run scripts/S477_lung9_rescore.py (Q4)")
    q4 = json.loads(Q4_RESCORE.read_text())
    prov = q4["provenance"]
    if prov["manifest_sha256"] != sha256_file(MANIFEST):
        raise SystemExit(f"{Q4_RESCORE.relative_to(ROOT)} was written on another manifest: run S477 again")
    for path, h in prov["inputs"].items():
        if inputs.get(path) != h:
            raise SystemExit(f"{Q4_RESCORE.relative_to(ROOT)}: {path} is not the file S477 read: run S477 again")
    rows = {(r["run_id"], r["answer_key"]): r for r in q4["attempts"] if r.get("flip")}
    done = 0
    for a in attempts:
        r = rows.get((a["run_id"], a["answer_key"]))
        if r is None:
            continue
        if a["passed"] or a["op_id"] != q4["operation"]:
            raise SystemExit(f"S477 flip {a['run_id']} {a['answer_key']} is not a stored failure of {q4['operation']}")
        a["passed"] = True
        a["field_results"] = r["replay"]["field_results"]
        a["actual_results"] = r["replay"]["actual_results"]
        a["q4_rescored"] = True
        done += 1
    if done != len(rows):
        raise SystemExit(f"S477 lists {len(rows)} flips, {done} found among the mirrored attempts")
    inputs[str(Q4_RESCORE.relative_to(ROOT))] = sha256_file(Q4_RESCORE)
    return {**q4["counts"], "applied": done, "sha256": sha256_file(Q4_RESCORE)}


def thinking_sent(r) -> str:
    """The diagnostic's key for what one generator call sent to set thinking (D112 Q17 O-a, audit A21-28): Ollama's
    think field (fields_sent.think, as before: "think_sent=<value>"), else Gemini's thinkingConfig (options_sent,
    "thinkingConfig_sent=<its JSON>": thinkingBudget 128 for gemini-2.5-pro off, thinkingLevel minimal for
    gemini-3-flash-preview off), else "think_sent=not sent" (a Gemini default call sends neither)."""
    fs = r.get("fields_sent") or {}
    if "think" in fs:
        return f"think_sent={fs['think']}"
    tc = (r.get("options_sent") or {}).get("thinkingConfig")
    if tc is not None:
        return f"thinkingConfig_sent={json.dumps(tc, sort_keys=True)}"
    return "think_sent=not sent"


def call_flags(r, flags, last=None):
    """What one generator call of calls.jsonl says about its attempt (joined by ctx_uid). The judge's calls are not
    read: the soft-pass judge never decides `passed`. flags[ctx_uid] collects every call's flags (rerun_tally() counts
    an event anywhere in the attempt, the reruns D80 V1 owes); last[ctx_uid] lists every generator call's (seq, flags,
    made a cell, its part of a cell round), from which end_flags() picks the calls fail_kind() reads (D92 Q193, D94
    Q-b O2)."""
    if r.get("role") != "generator":
        return
    u, st, err = r.get("ctx_uid"), r.get("status"), str(r.get("error") or "")
    own = set()
    if st == "stalled":
        own.add("stall")
    elif "error parsing tool call" in err:
        own.add("parse")
    elif st not in ("ok", "length") and NO_TOOLS in err:
        own.add("no_tools")                             # D112 Q12 O2: Ollama refused the tools (HTTP 400), own kind
    elif st not in ("ok", "length"):
        own.add("call_error")                           # HTTP 400/500, a dropped connection, Gemini's malformed call
        # D80 V1 retries an HTTP 500 and a dropped connection on Ollama only (never Gemini, never a 400)
        if r.get("provider") == "ollama" and ("500" in err or "connection" in err.lower()
                                              or "disconnect" in err.lower()):
            own.add("retry_call_error")
    if st == "length" or r.get("stop_reason") == "length":
        own.add("length")
    # a step reply with no native tool call that writes add_cell as text (audit A5/F35's tally,
    # findings/recompute/AUDIT_2026-10-16/COUNTERCHECKS.md:306-318; D80 V1, D81 Q137)
    if "step_executor" in str(r.get("call_site") or "") and st in ("ok", "length") and not r.get("tool_calls") \
            and "add_cell" in (r.get("text") or ""):
        own.add("as_text")
    flags[u] |= own
    if last is not None:
        last.setdefault(u, []).append((int(r.get("seq") or 0), own, made_cell(r), round_part(r)))


def tool_names(calls):
    """The tool names of a record's tool calls: Ollama's {"function": {"name"}} or Gemini's {"name"}."""
    return [(t.get("function") or {}).get("name") or t.get("name") for t in calls or [] if isinstance(t, dict)]


def made_cell(r) -> bool:
    """Whether a generator call asked for a notebook cell: it returned add_cell as a native tool call
    (step_executor.py:411), or D81's reader took the call from its text, which the adapter records as
    tool_calls_from_text and hands on as the call (lock_adapter.py:500-524). A cell a later failed execution deleted
    (coder_v2.py:586-593) was still made, so answers.json n_cells, the cells left at the end, is not read here. A
    candidate's add_cell in a cell round is an alternative source, not a cell: cell_seqs() reads a step call's only."""
    read = r.get("tool_calls_from_text")
    return "add_cell" in tool_names(r.get("tool_calls")) or \
        "add_cell" in tool_names(read.get("calls") if isinstance(read, dict) else None)


EVENTS = {"parse", "as_text", "stall", "no_tools", "call_error"}   # kinds 1 to 5: an earlier call's event can be it
FAILED = {"parse", "stall", "no_tools", "call_error"}               # a call that returned no reply
# Ollama's refusal of a request that offers tools to a model whose template has none (D112 Q12 O2, audit A21-21): 380
# of gemma3:27b's generator calls in the four structured strategies (Studio mentori-runs-s2-d75, read 21 October: 95,
# 95, 92 and 98 per strategy, of 230, 230, 224 and 296 generator calls) read "HTTP 400:
# registry.ollama.ai/library/gemma3:27b does not support tools", and 78 of those 80 attempts' exec_error carries it
NO_TOOLS = "does not support tools"


def round_part(r):
    """A call of a cell round (best-of-3 or combined, step_executor.py:418, _judge_cell_candidates :599): "candidate"
    for candidate 2 or 3 (the record's candidate number), "cell judge" for the call that picks or combines them, None
    for every other call."""
    if "_judge_cell_candidates" not in str(r.get("call_site") or ""):
        return None
    return "candidate" if r.get("candidate") is not None else "cell judge"


def cell_seqs(calls):
    """The seqs at which the attempt made a notebook cell (D94 Q-b O2), from call_flags()'s last[ctx_uid]. A step call
    that asked for a cell (made_cell()) makes it at its own seq, unless a cell round follows it (the calls right after
    it by seq that round_part() names): step_executor.py:418-432 makes the cell only after the round, from the picked
    or combined source, so the cell is made at the round's last call, and not at all when that call is the cell judge
    and returned no reply (the round raised; a redone round, D83 Q156, ends on its own last call)."""
    calls = sorted(calls, key=lambda c: c[0])
    out = []
    for i, (s, _, cell, part) in enumerate(calls):
        if not cell or part:
            continue
        j = i
        while j + 1 < len(calls) and calls[j + 1][3]:
            j += 1
        if not (calls[j][3] == "cell judge" and calls[j][1] & FAILED):
            out.append(calls[j][0])
    return out


def cell_after(calls, seq) -> bool:
    """Whether the attempt made a notebook cell at or after generator call `seq` (cell_seqs()); at: a reply D81's
    reader took as the call made its cell from the very text that raised the as_text event."""
    return any(m >= seq for m in cell_seqs(calls))


LENGTH_RULE = "D114 Q29 O2"


def first_length_seq(calls):
    """D114 Q29 O2: the seq of the attempt's first generator call that ended on "length" (call_flags()' "length":
    status or stop_reason "length"; the judge's calls are never read), or None. calls is last[ctx_uid]."""
    return min((s for s, own, _, _ in calls if "length" in own), default=None)


def apply_length_rule(attempts, flags, last):
    """D114 Q29 O2 (Valerio, 22 October): an attempt ends at its first length stop and is recorded as "length",
    identically for every variant's stored attempts, whichever rule exp_05 ran them under (--length-stop retry, as
    submitted, or stop, S2 nemotron off from 22 October). load_mirror() calls it on call_flags()' per-call lists
    before end_flags(): every generator call of an attempt after its first length stop is dropped (last[ctx_uid] and
    flags[ctx_uid] rebuilt from the calls left), so its kind is read with that stop as its last call, and an event
    after the stop is neither its kind nor a rerun it owes; the stop call itself keeps only its "length" flag (a reply
    cut at the limit that names add_cell is no add_cell written as text: review of 22 October, F2), so an earlier
    event of kinds 1 to 5 with no cell after it is the only cause that outranks "length" (D94 Q-b O2); and its passed and exec_outcome become False and "length",
    the stored values kept in length_rule (passed_as_stored, exec_outcome_as_stored). A pass after a length stop is
    therefore a failure. Under "stop" exp_05 makes few or no calls after the first stop (coder_v2: those before its next
    event), and they are dropped here as under "retry", so both rules give the same reading. Returns, per variant, the
    attempts with a length stop, those of them stored as passed, those whose stored exec_outcome was not "length", and
    the generator calls dropped."""
    cut = {}
    for u, calls in last.items():
        s = first_length_seq(calls)
        if s is None:
            continue
        kept = [c if c[0] < s else (c[0], c[1] & {"length"}, c[2], c[3]) for c in calls if c[0] <= s]
        cut[u] = (s, len(calls) - len(kept))
        last[u] = kept
        flags[u] = set().union(*(c[1] for c in kept))
    out = defaultdict(Counter)
    for a in attempts:
        if a.get("ctx_uid") not in cut:
            continue
        s, dropped = cut[a["ctx_uid"]]
        a["length_rule"] = {"decision": LENGTH_RULE, "first_length_seq": s, "passed_as_stored": a["passed"],
                            "exec_outcome_as_stored": a.get("exec_outcome"), "generator_calls_dropped": dropped,
                            "generator_calls_to_stop": len(last[a["ctx_uid"]])}   # D115 LS1 (llm_calls())
        o = out[variant_of(a["run_id"])]
        o["attempts_with_length_stop"] += 1
        o["stored_as_passed"] += bool(a["passed"])
        o["stored_exec_outcome_not_length"] += a.get("exec_outcome") != "length"
        o["generator_calls_dropped"] += dropped
        a["passed"], a["exec_outcome"] = False, "length"
    return {v: dict(c) for v, c in sorted(out.items())}


def llm_calls(a):
    """D115 LS1: an attempt's model calls for the means of extras(). A length-cut attempt (apply_length_rule()) counts
    its generator calls up to and including its first length stop, whichever rule exp_05 stored it under; any other
    attempt its stored n_llm_calls. n_llm_calls is the harness's design count, not a count of calls: free-form 1
    (exp_v2_8_coder_benchmark.py:1139), best-of-3 its candidates plus the generator call that picks among them (:1279),
    None under "stop" when the attempt ended at a length stop (:1378). On the copy of 21 October (S468's data) it
    equals the generator records on all 600 free-form and best-of-3 attempts; a transient retry would make the two
    differ, and extras() counts such attempts (n_llm_calls_d115_ls1)."""
    lr = a.get("length_rule")
    return lr["generator_calls_to_stop"] if lr else a.get("n_llm_calls")


def end_flags(flags, last):
    """Adds to flags[ctx_uid], each as "end:<flag>", the flags fail_kind() reads: those of the attempt's last generator
    call by seq (D92 Q193), and the kind 1 to 5 events of every earlier generator call after which the attempt made no
    notebook cell (cell_after(); D94 Q-b O2: an earlier event stays the cause unless a cell was made after it). When
    several apply, fail_kind()'s order picks, as it did when every call was read. A cause that only an earlier call
    gives is also added as "early:<flag>" (earlier_label(), D115 L1b)."""
    for u, calls in last.items():
        end = max(calls, key=lambda c: c[0])
        cause = set(end[1]) | {x for s, own, _, _ in calls for x in own & EVENTS if not cell_after(calls, s)}
        flags[u] |= {f"end:{x}" for x in cause} | {f"early:{x}" for x in cause - set(end[1])}


def earlier_label(a, fl) -> bool:
    """D115 L1b: whether a failed attempt's kind comes from an earlier call's event, not from the call that ended it
    (fail_kind() gives another kind once the "end:" flags only an earlier call gave are taken away)."""
    early = {f"end:{x.removeprefix('early:')}" for x in fl if x.startswith("early:")}
    return not a["passed"] and bool(early) and fail_kind(a, fl) != fail_kind(a, set(fl) - early)


def earlier_label_count(attempts, flags):
    """D115 L1b: (failed attempts outside the structured strategies whose kind comes from an earlier call's event, the
    failed attempts outside the structured strategies). In those strategies the harness runs the reply's code and no
    call makes a cell, so an earlier event always stays the cause (D94 Q-b O2); the count is printed, never drawn."""
    xs = [a for a in attempts if not a["config"].startswith("coder_v2") and not a["passed"]]
    return sum(earlier_label(a, flags.get(a.get("ctx_uid"), set())) for a in xs), len(xs)


def print_earlier_label(attempts, flags):
    """D115 L1b: the one line on screen; nothing in the figure."""
    n, of = earlier_label_count(attempts, flags)
    print(f"failed attempts outside the structured strategies whose kind comes from an earlier call's event (D115 "
          f"L1b, not drawn): {n} of {of}")


def earlier_label_cases(count=None):
    """D115 L1b on synthetic records, through call_flags(), apply_length_rule(), end_flags() and earlier_label_count()
    (or the count given, for a mutant). Returns (problems, cases)."""
    count = count or earlier_label_count
    pe = "error parsing tool call: x"

    def call(u, seq, status="ok", error=None, as_text=False):
        return {"role": "generator", "ctx_uid": u, "seq": seq, "status": status, "error": error,
                "stop_reason": "length" if status == "length" else "stop", "provider": "ollama",
                "call_site": "exp_v2_8_coder_benchmark.py:1 _run_free_form", "candidate": None,
                "text": "add_cell(code='x')" if as_text else "", "tool_calls": None}

    def att(u, config, passed=False):
        return {"ctx_uid": u, "run_id": f"exp_05__{config}__gpt-oss-20b+low", "config": config, "passed": passed,
                "gen_model": "ollama::x", "generations": [], "exec_outcome": "ok", "code": "x",
                "actual_results": {"r": 1}}
    calls = [call("e1", 1, "error", pe), call("e1", 2),                    # earlier parse error, ok last: counted
             call("e2", 1), call("e2", 2, "error", pe),                    # the last call's own error: not counted
             call("e3", 1, "error", pe), call("e3", 2),                    # e1's calls, but structured: not counted
             call("e4", 1, "error", pe), call("e4", 2),                    # passed: not counted
             call("e5", 1, "stalled"), call("e5", 2, "length"),            # an earlier stall, a length stop: counted
             call("e6", 1, "error", pe), call("e6", 2, "error", pe)]       # the same event last as well: not counted
    atts = [att("e1", "free_form_n3_best"), att("e2", "free_form"), att("e3", "coder_v2_n1"),
            att("e4", "free_form", passed=True), att("e5", "error_recovery_introspect"), att("e6", "free_form")]
    flags, last = defaultdict(set), {}
    for r in calls:
        call_flags(r, flags, last)
    apply_length_rule(atts, flags, last)
    end_flags(flags, last)
    got, want = count(atts, flags), (2, 4)
    return ([] if got == want else [f"(counted, failed outside structured) {got}, want {want}"]), 1


def q193_cases():
    """Synthetic call sequences through call_flags(), end_flags() and fail_kind(), as load_mirror() runs them (the
    selftest's check of D92 Q193 and D94 Q-b O2; review F1, 18 October). Returns the problems, empty when every case
    is as wanted. Each case: the generator calls in file order (seq, status, error, step reply, whether it returned
    add_cell), the attempt, the kind wanted and the flags rerun_tally() must still see anywhere in the attempt."""
    def call(u, seq, status="ok", error=None, as_text=False, role="generator", cell=False, provider="ollama",
             read=False, part=None, stop=None):
        tc = [{"function": {"name": "add_cell" if cell else "execute_cell"}}]
        if provider == "gemini":                        # Gemini's records keep the flat {"name"} shape
            tc = [{"name": "add_cell" if cell else "execute_cell"}]
        r = {"role": role, "ctx_uid": u, "seq": seq, "status": status, "error": error, "provider": provider,
             "call_site": "step_executor.py:1 " + ("_judge_cell_candidates" if part else "execute_step"),
             "candidate": 2 if part == "candidate" else None, "stop_reason": stop,
             "text": "add_cell(code='x')" if as_text else "", "tool_calls": None if as_text else tc}
        if read:                                        # D81's reader took the call from the text
            r["tool_calls_from_text"] = {"calls": [{"function": {"name": "add_cell", "arguments": {}}}],
                                         "form": "python"}
        return r
    pe = "error parsing tool call: x"
    ran = {"exec_outcome": "ok", "code": "x", "actual_results": {"r": 1}}
    no_cell = {"exec_outcome": "step_failed", "exec_error": "Step failed: None", "code": "x"}
    raised = {"exec_outcome": "error", "code": "x", "actual_results": {}}
    nt = "HTTP 400: registry.ollama.ai/library/gemma3:27b does not support tools"
    refused = {"exec_outcome": "step_failed", "code": "x", "exec_error": f"Step failed: gemma3:27b: status error: {nt}"}
    cases = [
        ("an earlier parse error, a cell made after it, the code ran: not the parse error",
         [call("u1", 1), call("u1", 2, "error", pe), call("u1", 3, cell=True)], ran, "result wrong or missing",
         {"parse"}),
        ("an earlier parse error, no cell made after it (only before): the parse error",
         [call("u1b", 1, cell=True), call("u1b", 2, "error", pe), call("u1b", 3)], ran, "tool-call parse error",
         {"parse"}),
        ("the last call a parse error", [call("u2", 1, cell=True), call("u2", 2, "error", pe)], ran,
         "tool-call parse error", {"parse"}),
        ("the last call by seq written first in the file",
         [call("u3", 3, "error", pe), call("u3", 2, cell=True)], ran, "tool-call parse error", {"parse"}),
        ("add_cell as text early, no cell after it, a stall last: the text (kind 2 comes before kind 3)",
         [call("u4", 1, as_text=True), call("u4", 2, "stalled")], ran, "tool call written as text",
         {"as_text", "stall"}),
        ("add_cell as text early, a cell after it, a stall last: the stall",
         [call("u4b", 1, as_text=True), call("u4b", 2, cell=True), call("u4b", 3, "stalled")], ran, "stall",
         {"as_text", "stall"}),
        ("add_cell as text, then no cell, the step failed: the as-text kind",
         [call("u5", 1, as_text=True), call("u5", 2)], no_cell, "tool call written as text", {"as_text"}),
        ("add_cell as text, then a cell, the step failed with no cell: the later kind",
         [call("u5b", 1, as_text=True), call("u5b", 2, cell=True), call("u5b", 3)], no_cell,
         "step produced no cell and no error", {"as_text"}),
        ("add_cell as text that D81's reader took as the call (its own cell), the step failed: the later kind",
         [call("u5c", 1, as_text=True, read=True), call("u5c", 2)], no_cell, "step produced no cell and no error",
         {"as_text"}),
        ("a Gemini call error, then a cell in Gemini's flat shape, the code raised: the later kind",
         [call("u5d", 1, "error", "HTTP 500", provider="gemini"), call("u5d", 2, cell=True, provider="gemini")],
         raised, "code raised or timed out", {"call_error"}),
        ("no flagged call, the attempt's own outcome a call error", [call("u6", 1)],
         {"exec_outcome": "call_error", "code": ""}, "other call error", set()),
        ("a length stop on the last call: the length stop", [call("u8", 1, cell=True), call("u8", 2, stop="length")],
         ran, "length stop", {"length"}),
        ("an earlier length stop, then a call with no cell: the attempt ends at that stop (D114 Q29 O2)",
         [call("u8b", 1, "length"), call("u8b", 2)], ran, "length stop", {"length"}),
        ("a length stop on the last call by seq, written first in the file, no earlier event",
         [call("u8c", 3, stop="length"), call("u8c", 2, cell=True)], ran, "length stop", {"length"}),
        ("the last call wrote add_cell as text that D81's reader took (it made a cell): still the as-text kind (Q193)",
         [call("u8d", 1, cell=True), call("u8d", 2, as_text=True, read=True)], no_cell, "tool call written as text",
         {"as_text"}),
        ("a parse error on a round's last candidate, the round's cell made after it, the step failed: the later kind",
         [call("u9", 1, cell=True), call("u9", 2, part="candidate", cell=True),
          call("u9", 3, "error", pe, part="candidate"), call("u9", 4, part="cell judge"), call("u9", 5)], no_cell,
         "step produced no cell and no error", {"parse"}),
        ("a parse error on a candidate, a later candidate's add_cell, the cell judge failed (no cell): the parse error",
         [call("u9b", 1, cell=True), call("u9b", 2, "error", pe, part="candidate"),
          call("u9b", 3, part="candidate", cell=True), call("u9b", 4, "error", "HTTP 500", part="cell judge")], ran,
         "tool-call parse error", {"parse", "call_error"}),
        ("a judge call after the last generator call is not read",
         [call("u7", 1, "error", pe), call("u7", 2, "error", "HTTP 500", role="judge")], ran,
         "tool-call parse error", {"parse"}),
        # D112 Q12 O2 (audit A21-21): Ollama's tool refusal is its own kind, never "other call error"
        ("the last call refused by Ollama for tools (HTTP 400 'does not support tools'): its own kind",
         [call("u10", 1, "error", nt)], refused, "tools refused by Ollama", {"no_tools"}),
        ("a tool refusal, the record's exec_error not naming it: still its own kind (read from the call)",
         [call("u10b", 1, "error", nt)], no_cell, "tools refused by Ollama", {"no_tools"}),
        ("a tool refusal on an earlier call, no cell after it, a later call ok: the refusal",
         [call("u10c", 1, "error", nt), call("u10c", 2)], ran, "tools refused by Ollama", {"no_tools"}),
        ("another HTTP 400 stays other call error", [call("u11", 1, "error", "HTTP 400: bad request")], ran,
         "other call error", {"call_error"}),
    ]
    bad = []
    for what, calls, att, want, anywhere in cases:
        flags, last = defaultdict(set), {}
        for r in calls:
            call_flags(r, flags, last)
        u = calls[0]["ctx_uid"]
        a = {"gen_model": "ollama::x", "generations": [], "ctx_uid": u, "run_id": "exp_05__free_form__x+off",
             "passed": False, **att}
        apply_length_rule([a], flags, last)       # as load_mirror() runs them (D114 Q29 O2)
        end_flags(flags, last)
        got = fail_kind(a, flags[u])
        plain = {x for x in flags[u] if not x.startswith("end:")}
        if got != want or not anywhere <= plain:
            bad.append(f"{what}: kind {got!r} (want {want!r}), flags anywhere {sorted(plain)} (want "
                       f"{sorted(anywhere)} among them)")
    return bad, len(cases)


def length_rule_cases(rule=None, ends=None, calls_of=None):
    """D114 Q29 O2 on synthetic records, through call_flags(), apply_length_rule() (or the rule given, for a mutant),
    end_flags() (or ends), fail_kind(), compute() and llm_calls() (or calls_of), as load_mirror() and draw run them
    (calls_mean_cases() runs the means of extras()). LS2 of D115: an earlier event with no cell after it keeps the
    kind over a later length stop, the outcome stays "length" (u8, u9). LS1 of D115: a length-cut attempt's calls are
    counted to its stop (u1, u4).
    Returns (problems, cases); problems is empty when every case is as wanted."""
    rule, ends, calls_of = rule or apply_length_rule, ends or end_flags, calls_of or llm_calls

    def call(u, seq, status="ok", stop=None, error=None, role="generator", cell=False, as_text=False):
        return {"role": role, "ctx_uid": u, "seq": seq, "status": status, "stop_reason": stop or (
                "length" if status == "length" else "stop"), "error": error, "provider": "ollama",
                "call_site": "step_executor.py:1 execute_step", "candidate": None,
                "text": "add_cell(code='x'" if as_text else "",
                "tool_calls": None if as_text else [{"function": {"name": "add_cell" if cell else "execute_cell"}}]}

    def att(u, variant, passed, eo, config="coder_v2_n1", **kw):
        return {"ctx_uid": u, "run_id": f"exp_05__{config}__{variant}", "config": config, "op_id": f"op_{u}",
                "answer_key": f"{config}|op_{u}|d1", "gen_model": "ollama::x", "generations": [], "passed": passed,
                "exec_outcome": eo, "code": "x", "actual_results": {"r": 1}, **kw}

    nt = "HTTP 400: registry.ollama.ai/library/x does not support tools"
    e400 = "HTTP 400: request (132201 tokens) exceeds the available context size (131072 tokens)"
    V1, V2 = "glm-4.7-flash-bf16+default", "nemotron-3-nano-30b+off"
    calls = [
        # u1: a pass after a length stop (glm-4.7-flash default's stored coder_v2_n1 pass, S468): a failure now
        call("u1", 1), call("u1", 2, "length"), call("u1", 3, cell=True), call("u1", 4),
        # u2: no length stop: unchanged
        call("u2", 1, cell=True),
        # u3 and u4: the nemotron off pattern, a length stop then a call refused as too long; stored under "retry"
        # (step_failed, the step went on) and under "stop" (length): read the same
        call("u3", 1), call("u3", 2, "length"), call("u3", 3, "error", error=e400), call("u3", 4, cell=True),
        call("u4", 1), call("u4", 2, "length"), call("u4", 3, "error", error=e400),
        # u5: a length stop by stop_reason alone, then a tool refusal named in exec_error: the length stop
        call("u5", 1, "ok", stop="length"), call("u5", 2, "error", error=nt),
        # u6: the soft-pass judge's length stop is an instrument's: not read, the attempt keeps its pass
        call("u6", 1, cell=True), call("u6", 2, "length", role="judge"),
        # u7: the stop call's cut-off text names add_cell (S468 copy, qwen3-coder-next default, seq 21): the length
        # stop, not "tool call written as text", and no as-text event (review of 22 October, F2)
        call("u7", 1, cell=True), call("u7", 2, "length", as_text=True), call("u7", 3, cell=True),
        # u8: an add_cell written as text, then the length stop with no cell between (S468 copy, deepseek-r1:70b
        # default, seq 8 and 9): the earlier event stays the cause (D94 Q-b O2; D115 LS2 O-a)
        call("u8", 1, as_text=True), call("u8", 2, "length"),
        # u9: a parse error, then the length stop with no cell between, then a cell: the parse error (D115 LS2 O-a)
        call("u9", 1, "error", error="error parsing tool call: x"), call("u9", 2, "length"), call("u9", 3, cell=True),
    ]
    atts = [att("u1", V1, True, "ok", n_llm_calls=4), att("u2", V1, True, "ok", n_llm_calls=1),
            att("u3", V2, False, "step_failed", exec_error=f"Step failed: {e400}", length_stop_rule="retry"),
            att("u4", V2, False, "length", exec_error="the attempt ended at its first length stop",
                length_stop_rule="stop", n_llm_calls=None),
            att("u5", V2, False, "step_failed", exec_error=f"Step failed: {nt}"),
            att("u6", V1, True, "ok"),
            att("u7", V2, False, "step_failed", exec_error="Step failed: x"),
            att("u8", V2, False, "step_failed", exec_error="Step failed: x"),
            att("u9", V1, False, "step_failed", config="coder_v2_n3", exec_error="Step failed: x")]
    flags, last = defaultdict(set), {}
    for r in calls:
        call_flags(r, flags, last)
    summary = rule(atts, flags, last)
    ends(flags, last)
    by = {a["ctx_uid"]: a for a in atts}
    kind = {u: (fail_kind(a, flags.get(u, set())) if not a["passed"] else "pass") for u, a in by.items()}
    want = {"u1": (False, "length", "length stop"), "u2": (True, "ok", "pass"), "u3": (False, "length", "length stop"),
            "u4": (False, "length", "length stop"), "u5": (False, "length", "length stop"),
            "u6": (True, "ok", "pass"), "u7": (False, "length", "length stop"),
            "u8": (False, "length", "tool call written as text"), "u9": (False, "length", "tool-call parse error")}
    bad = []
    for u, (p, eo, k) in want.items():
        got = (by[u]["passed"], by[u]["exec_outcome"], kind[u])
        if got != (p, eo, k):
            bad.append(f"{u}: (passed, exec_outcome, kind) {got}, want {(p, eo, k)}")
    if (by["u1"].get("length_rule") or {}).get("passed_as_stored") is not True:
        bad.append(f"u1: the stored pass is not kept in length_rule ({by['u1'].get('length_rule')})")
    if "call_error" in flags["u3"] or "call_error" in flags["u4"]:
        bad.append("u3/u4: the refused call after the length stop is still read")
    if "as_text" in flags["u7"] or "as_text" not in flags["u8"]:
        bad.append(f"as-text events: u7 {sorted(flags['u7'])} (want none), u8 {sorted(flags['u8'])} (want one)")
    if summary != {V1: {"attempts_with_length_stop": 2, "stored_as_passed": 1, "stored_exec_outcome_not_length": 2,
                        "generator_calls_dropped": 3},
                   V2: {"attempts_with_length_stop": 5, "stored_as_passed": 0, "stored_exec_outcome_not_length": 4,
                        "generator_calls_dropped": 5}}:
        bad.append(f"summary per variant {summary}")
    cells = compute(atts, flags)[0]
    c1 = next(c for c in cells if c["variant"] == V1 and c["strategy"] == "coder_v2_n1")
    if (c1["attempts"], c1["pass"], c1["kind: length stop"]) != (3, 2, 1):
        got = (c1["attempts"], c1["pass"], c1["kind: length stop"])
        bad.append(f"compute: {V1} coder_v2_n1 (attempts, pass, length stops) {got}, want (3, 2, 1)")
    # D115 LS1: calls counted up to and including the first length stop, under either stored rule; else as stored
    n_calls = {u: calls_of(by[u]) for u in ("u1", "u2", "u4", "u9")}
    if n_calls != {"u1": 2, "u2": 1, "u4": 2, "u9": 2}:
        bad.append(f"calls for the means (D115 LS1) {n_calls}, want u1 2 (stored 4), u2 1, u4 2 (stored None), u9 2")
    return bad, len(want) + 6


def fail_kind(a, fl) -> str:
    """The kind of one failed attempt: the first that applies, in KINDS_ALL's order. Kinds 1 to 6 are read from the
    "end:" flags (end_flags()): the attempt's last generator call (D92 Q193) and, for kinds 1 to 5, an earlier
    call after which the attempt made no notebook cell (D94 Q-b O2). An error the attempt made a cell after is not its
    cause, and the attempt falls to the later kinds. Two kinds are also read from the attempt's own record: kind 4 when
    its exec_error carries Ollama's "does not support tools", kind 5 when its exec_outcome is "call_error"."""
    eo, err = a.get("exec_outcome"), a.get("exec_error") or ""
    gens = a.get("generations") or []
    if "end:parse" in fl:
        return "tool-call parse error"
    if "end:as_text" in fl:
        return "tool call written as text"
    if "end:stall" in fl:
        return "stall"
    if "end:no_tools" in fl or (NO_TOOLS in err and "length_rule" not in a):   # D114: err may tell of later calls
        return "tools refused by Ollama"
    if "end:call_error" in fl or eo == "call_error":
        return "other call error"
    if "end:length" in fl:
        return "length stop"
    if eo == "exception":
        return "harness error"
    if "Step failed: None" in err:
        return "step produced no cell and no error"
    if a["gen_model"].startswith("gemini::") and gens and not (gens[-1].get("raw_reply") or "").strip():
        return "Gemini empty reply"
    if eo == "not_run" or not (a.get("code") or a.get("code_cells")):
        return "no code"
    if eo in ("error", "exec_timeout", "step_failed") and not a.get("actual_results"):
        return "code raised or timed out"
    if eo in ("ok", "error", "step_failed"):
        return "result wrong or missing"
    return "other"


Q101_FORM = r"Step failed: step \d+: no cell created"       # D75 Q101's record of kind 8's event
KINDS_ALL = ["tool-call parse error", "tool call written as text", "stall", "tools refused by Ollama",
             "other call error", "length stop", "harness error", "step produced no cell and no error",
             "Gemini empty reply", "no code", "code raised or timed out", "result wrong or missing", "other"]
# panel d folds to eight hues and two greys (dataviz: a ninth series folds into "other"); the Ollama tool refusal is
# its own group (D112 Q12 O2), never folded into "other call error"
FOLD = {"tool-call parse error": "tool-call parse error", "tool call written as text": "tool call written as text",
        "stall": "stall or other call error", "other call error": "stall or other call error",
        "tools refused by Ollama": "tools refused by Ollama",
        "length stop": "length stop", "harness error": "harness error",
        "step produced no cell and no error": "step produced no cell and no error",
        "code raised or timed out": "code raised or timed out", "result wrong or missing": "result wrong or missing",
        "Gemini empty reply": "other (Gemini empty, no code, other)", "no code": "other (Gemini empty, no code, other)",
        "other": "other (Gemini empty, no code, other)"}
FOLDED = list(dict.fromkeys(FOLD.values()))
FOLD_COL = ["#2a78d6", "#eb6834", "#1baf7a", "#5a5a5a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948",
            "#a3a29c"]                            # the working view's colours, one per FOLDED group in its order
assert len(FOLD_COL) == len(FOLDED)


def kind_number(kind):
    """A kind's number in the legend: its place in KINDS_ALL, from 1."""
    return KINDS_ALL.index(kind) + 1


def numbers_words(ns):
    """1 -> '1'; [3, 5] -> '3 and 5'; [9, 10, 13] -> '9, 10 and 13'."""
    ns = [str(x) for x in ns]
    return ns[0] if len(ns) == 1 else ", ".join(ns[:-1]) + " and " + ns[-1]


def wilson(k, n, z=1.959964):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (100 * (c - h), 100 * (c + h))


def pct(k, n):
    return None if n == 0 else 100 * k / n


def exact(x):
    """x as a Decimal, rounded to 1e-9 first, so float noise (54.25000000000001, 80.74999999999999) is removed before
    any printed rounding: every value S447 prints is a ratio of counts or a difference of such, whose float error is
    far below 1e-9."""
    from decimal import Decimal
    if isinstance(x, Decimal):
        return x.quantize(Decimal("1e-9"))
    return Decimal(repr(round(float(x), 9)))


def half_up(x, nd=1, sign=False):
    """Every number S447 prints, rounded once: to 1e-9 (exact()), then to nd decimals half away from zero (Decimal
    ROUND_HALF_UP), so an exact quarter always rounds up in size (69.25 -> 69.3, 54.25000000000001 -> 54.3, 12.5 ->
    13 at nd 0); Python's format() rounds the binary value instead (69.25 -> 69.2, 54.25000000000001 -> 54.3).
    sign: a leading + on a positive value; a value that rounds to zero prints unsigned. S448 R8 (6) fills the
    printed formats with the same rule (its HalfUpFormatter)."""
    from decimal import Decimal, ROUND_HALF_UP
    q = exact(x).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    return f"{q:+.{nd}f}" if sign and q != 0 else f"{q:.{nd}f}"


class HalfUpFormatter(__import__("string").Formatter):
    """str.format with half_up() for every fixed-point field ("{x:.1f}", "{x:+.0f}"): the plate's printed numbers are
    written through it from the format the numbers file records, and S448 fills that format the same way."""

    def format_field(self, value, spec):
        import re
        m = re.fullmatch(r"(\+?)\.(\d+)f", spec)
        if m and isinstance(value, (int, float)) and not isinstance(value, bool):
            return half_up(value, int(m.group(2)), sign=bool(m.group(1)))
        return format(value, spec)


HALF_UP = HalfUpFormatter()


# The pass rate over several attempts per operation, and its interval: experiments/LIST.md, "Analysis rules for three
# draws", Rules 1 and 2 (approved as Q130, experiments/README.md:224), on Figure 6's one draw. Rule 1: the unit is the
# operation (the question of the QA experiments). Rule 2: the pass rate is the mean over the units of each unit's
# pass share p. In the QA experiments p is a question's share over its three draws; here, with one draw, an
# operation's attempts in the set being summarised (one per strategy: 11 for a complete variant, 4 or 5 per operation
# on gpt-oss:20b's matched set) take the draws' place, so p = the operation's passes over its attempts in the set,
# and every operation weighs the same however many attempts it holds. The interval is Rule 2's: 95% percentile
# interval of that mean over 10,000 resamples of the operations, as S407 draws them
# (scripts/S407_strategy_contrasts_v24.py:45-57: one resample matrix per number of operations n,
# numpy.random.default_rng(BOOT_SEED).integers(0, n, size=(N_BOOT, n)), seed and count of S407:190; percentiles
# 2.5 and 97.5, numpy.percentile, linear). An operation with no attempt in the set has no share and is left out of
# the units (counted). A Wilson interval would treat the attempts of one operation as independent. With the same
# number of attempts on every operation the mean of p equals passes over attempts.
BOOT_SEED, N_BOOT = 20261013, 10000
_BOOT = {}


def boot_matrix(n):
    import numpy as np
    if n not in _BOOT:
        _BOOT[n] = np.random.default_rng(BOOT_SEED).integers(0, n, size=(N_BOOT, n))
    return _BOOT[n]


def _shares(per_op, ops):
    import numpy as np
    units = [o for o in ops if per_op.get(o, (0, 0))[1] > 0]
    p = np.array([per_op[o][0] / per_op[o][1] for o in units], dtype=float)
    return p, len(ops) - len(units)


def op_mean(per_op, ops):
    """Rule 2's pass rate in %: the mean over the operations of each one's share of passing attempts."""
    p, _ = _shares(per_op, ops)
    return float(100 * p.mean()) if len(p) else None


def op_bootstrap(per_op, ops):
    """per_op: {op_id: (passes, attempts)}; ops: the sorted operations resampled (the unit). Returns
    (lo, hi, left_out): the 95% percentile interval of op_mean in %, over N_BOOT resamples of the operations with an
    attempt, and the number of operations left out because they hold none."""
    p, left = _shares(per_op, ops)
    if not len(p):
        return None, None, left
    import numpy as np
    r = 100 * p[boot_matrix(len(p))].mean(axis=1)
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5)), left


def per_op_counts(atts):
    """{op_id: (passes, attempts)} over these attempts."""
    c = defaultdict(lambda: [0, 0])
    for a in atts:
        c[a["op_id"]][0] += bool(a["passed"])
        c[a["op_id"]][1] += 1
    return {o: tuple(x) for o, x in c.items()}


# ---------------------------------------------------------------------------------------------------------------
# Reproduce first
# ---------------------------------------------------------------------------------------------------------------
def reproduce():
    """S445's attempts per variant, recounted with count_per_variant() on the files S445 read (found by sha256).
    D155: each is looked for, by its sha256, in the frozen S2 copy and the frozen set FROZEN_S445 only; S445's own
    paths (~/projects/mentori-evidence/2026-10-16/s4_records, outside the repository) are not read."""
    import fig_repro
    mirror_by_sha = {}
    # S445 read the sinks of 16 October; S4 (D201 Q2) rewrote 40 of them, so the copy before S4 is searched as well
    before_s4 = sorted(fig_repro.frozen(FROZEN_S2_BEFORE_S4, FROZEN_S2_BEFORE_S4).glob(
        "*/*/runs/exp_05__*/answers.json")) if FROZEN_S2 != FROZEN_S2_BEFORE_S4 else []
    for p in sorted(frozen_copy().glob("*/*/runs/exp_05__*/answers.json")) + before_s4 + \
            sorted(fig_repro.frozen(*FROZEN_S445).glob("*/exp_05__*/answers.json")):
        mirror_by_sha[sha256_file(p)] = p
    out = []
    for machine in ("studio", "laptop"):
        f = S445 / f"{machine}.json"
        r = json.loads(f.read_text())
        paths, missing = [], []
        for path, h in r["provenance"]["inputs_sha256"].items():
            if not path.endswith("answers.json") or not path.startswith(r["runs"].rstrip("/") + "/"):
                continue                      # S445's own check R1 also hashes 8 discarded records; not counted
            if h in mirror_by_sha:
                paths.append(mirror_by_sha[h])
            else:
                missing.append(path)
        if missing:
            print(f"REPRODUCE FAILED: {len(missing)} of S445 {machine}'s answers.json not found by sha256, e.g. "
                  f"{missing[0]}", file=sys.stderr)
            sys.exit(2)
        got = count_per_variant(paths)
        want = {v: s["attempts"] for v, s in r["status"]["variants"].items()}
        diff = {v: (want[v], got.get(v, 0)) for v in want if want[v] != got.get(v, 0)}
        if diff or set(got) - set(want):
            print(f"REPRODUCE FAILED: S445 {machine} attempts per variant (S445, here): {diff}", file=sys.stderr)
            sys.exit(2)
        out.append({"s445": str(f.relative_to(ROOT)), "s445_sha256": sha256_file(f), "files": len(paths),
                    "attempts_per_variant": want, "total": sum(want.values()), "matches": True})
        print(f"reproduced S445 {machine}: {sum(want.values())} attempts over {len(want)} variants, every variant "
              f"equal ({len(paths)} answers.json found by sha256)")
    return out


# ---------------------------------------------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------------------------------------------
def vlabel(v):
    return f"{VMODEL[v]} [{VTHINK[v]}]"


def compute(attempts, flags):
    by_cell = defaultdict(list)
    for a in attempts:
        by_cell[(variant_of(a["run_id"]), a["config"])].append(a)
    unknown = sorted({v for v, _ in by_cell} - set(VMODEL)) + sorted({c for _, c in by_cell} - set(SLAB))
    if unknown:
        raise SystemExit(f"records name variants or strategies outside the design: {unknown}")
    cells = []
    for v, _, _ in VARIANTS:
        for c, lab in STRATEGIES:
            atts = by_cell.get((v, c), [])
            k = sum(1 for a in atts if a["passed"])
            kinds = Counter(fail_kind(a, flags.get(a.get("ctx_uid"), set())) for a in atts if not a["passed"])
            lo, hi = wilson(k, len(atts))
            cells.append({"variant": v, "model": VMODEL[v], "thinking": VTHINK[v], "strategy": c, "label": lab,
                          "attempts": len(atts), "pass": k, "fail": len(atts) - k, "pass_rate_pct": pct(k, len(atts)),
                          "wilson_lo": lo, "wilson_hi": hi, "complete": len(atts) == PER_CELL,
                          "soft_pass_judge_PASS_WITH_RESERVE": sum(1 for a in atts if not a["passed"]
                                                                   and a.get("judge_score") == "PASS_WITH_RESERVE"),
                          **{f"kind: {x}": kinds.get(x, 0) for x in KINDS_ALL}})
    variants = {}
    for v, _, _ in VARIANTS:
        cs = [c for c in cells if c["variant"] == v]
        n, k = sum(c["attempts"] for c in cs), sum(c["pass"] for c in cs)
        po = per_op_counts([a for c, _ in STRATEGIES for a in by_cell.get((v, c), [])])
        lo, hi, _ = op_bootstrap(po, sorted(po))
        variants[v] = {"label": vlabel(v), "attempts": n, "pass": k, "pass_rate_pct": pct(k, n),
                       "operations_n": len(po), "op_mean_pass_rate_pct": op_mean(po, sorted(po)),
                       "op_boot95_lo": lo, "op_boot95_hi": hi,
                       "complete": n == PER_VARIANT,
                       "cells_complete": sum(c["complete"] for c in cs),
                       "fail_kinds": {x: sum(c[f"kind: {x}"] for c in cs) for x in KINDS_ALL}}
    # panel a: per strategy, over one set of variants, those complete in every strategy, so every box rests on the
    # same variants (a partial variant is drawn in panel b only)
    panel_a_set = [v for v, _, _ in VARIANTS if variants[v]["cells_complete"] == len(STRATEGIES)]
    strat = {}
    for c, lab in STRATEGIES:
        rates = sorted(x["pass_rate_pct"] for x in cells if x["strategy"] == c and x["variant"] in panel_a_set)
        q = quantiles(rates)
        strat[c] = {"label": lab, "variants": len(rates), **q}
    # panel c: the thinking factor, per model, matched on the attempts every variant of the model with data holds
    by_variant_key = defaultdict(dict)
    op_of = {}
    for a in attempts:
        by_variant_key[variant_of(a["run_id"])][a["answer_key"]] = a["passed"]
        op_of[a["answer_key"]] = a["op_id"]
    models = list(dict.fromkeys(VMODEL.values()))
    think = {}
    for m in models:
        vs = [v for v, mm, _ in VARIANTS if mm == m]
        with_data = [v for v in vs if by_variant_key.get(v)]
        common = set.intersection(*(set(by_variant_key[v]) for v in with_data)) if with_data else set()
        ops = sorted({op_of[key] for key in common})
        per_op_n = Counter(op_of[key] for key in common)
        rows = []
        for v in vs:
            d = by_variant_key.get(v, {})
            km = sum(1 for key in common if d.get(key)) if v in with_data else 0
            nm = len(common) if v in with_data else 0
            po = {}
            if v in with_data:
                po = per_op_counts([{"op_id": op_of[key], "passed": d[key]} for key in common])
            lo, hi, left_out = op_bootstrap(po, ops)
            rows.append({"variant": v, "thinking": VTHINK[v], "attempts_stored": len(d),
                         "matched_attempts": nm, "matched_pass": km, "matched_pass_rate_pct": pct(km, nm),
                         "op_mean_pass_rate_pct": op_mean(po, ops) if v in with_data else None,
                         "operations_n": len(ops) if v in with_data else 0,
                         "op_boot95_lo": lo, "op_boot95_hi": hi, "operations_left_out_no_attempt": left_out,
                         "per_operation": {o: list(po[o]) for o in ops if o in po},
                         "pass_rate_all_stored_pct": pct(sum(d.values()), len(d))})
        think[m] = {"variants": rows, "matched_on": len(common), "variants_with_data": len(with_data),
                    "operations_n": len(ops), "attempts_per_operation_min": min(per_op_n.values(), default=0),
                    "attempts_per_operation_max": max(per_op_n.values(), default=0),
                    "operations_by_attempts": {str(k): x for k, x in sorted(Counter(per_op_n.values()).items())},
                    "point": "op_mean_pass_rate_pct: the mean over the operations of each one's share of passing "
                             "matched attempts (experiments/LIST.md Rule 2); matched_pass_rate_pct is passes over "
                             "attempts, for reference",
                    "interval": f"95% percentile interval of op_mean over {N_BOOT} resamples of the operations "
                                f"(numpy default_rng seed {BOOT_SEED}), the same resamples for every setting"}
        lt = lock_think(m)
        for row in rows:
            row["lock_think_off_setting"] = lt
            row["panel_label"] = think_label(row["thinking"], len(rows) == 1, lt)
    # pooled structured (coder_v2_*) against free-form (free_form), as the submitted legend pools them,
    # over complete variants only
    done = [v for v, s in variants.items() if s["complete"]]
    def pool(prefix_test):
        cs = [c for c in cells if c["variant"] in done and prefix_test(c["strategy"])]
        n, k = sum(c["attempts"] for c in cs), sum(c["pass"] for c in cs)
        return {"attempts": n, "pass": k, "pass_rate_pct": pct(k, n)}
    pooled = {"over_complete_variants": done,
              "structured_family": pool(lambda s: s.startswith("coder_v2")),
              "free_form_family": pool(lambda s: s.startswith("free_form")),
              "free_form_single": pool(lambda s: s == "free_form"),
              "introspection_family": pool(lambda s: "introspect" in s or s == "thinker_coder_split"),
              "all": pool(lambda s: True)}
    chi = interaction_chi2([c for c in cells if c["variant"] in done])
    return cells, variants, strat, panel_a_set, think, pooled, chi


def lock_think(m):
    """The model's think setting in LOCK.toml [sampling.models] (its setting for thinking off: off, a level, "omit" =
    no thinking mode, "always" = cannot be turned off), matched by the tag or the tag's name before its size."""
    import tomllib
    rows = tomllib.loads(LOCK.read_text())["sampling"]["models"]
    for key in [m] + sorted(k for k in rows if k.startswith(m + ":")):
        if key in rows:
            return rows[key].get("think")
    return None


def think_label(thinking, single, lt):
    """Panel c's label for one variant: a model with one variant says why it has no off arm, from the lock."""
    if not single:
        return thinking
    return {"omit": f"{thinking} (= off)", "always": f"{thinking} (always thinks)"}.get(lt, thinking)


def quantiles(rates):
    if not rates:
        return {"median": None, "q1": None, "q3": None, "min": None, "max": None}
    import numpy as np
    r = np.array(rates)
    return {"median": float(np.median(r)), "q1": float(np.quantile(r, 0.25)), "q3": float(np.quantile(r, 0.75)),
            "min": float(r.min()), "max": float(r.max())}


def interaction_chi2(cells):
    """Pearson chi-square on the strategy by variant table of pass counts (as the submitted legend computes it,
    S290_figure6.R), over complete variants only; None with fewer than 2 variants."""
    vs = sorted({c["variant"] for c in cells})
    if len(vs) < 2:
        return None
    from scipy.stats import chi2_contingency
    import numpy as np
    t = np.array([[next(c["pass"] for c in cells if c["variant"] == v and c["strategy"] == s)
                   for s, _ in STRATEGIES] for v in vs])
    keep = t.sum(axis=0) > 0
    t = t[:, keep]
    t = t[t.sum(axis=1) > 0]
    stat, p, dof, _ = chi2_contingency(t, correction=False)
    return {"chi2": float(stat), "df": int(dof), "p": float(p), "variants": vs,
            "table": "pass counts, rows variants, columns strategies with any pass"}


INTROSPECTION = ["introspect_then_code", "error_recovery_introspect", "thinker_coder_split", "introspect_with_recovery"]


def mcnemar_exact(pairs):
    """Two-sided exact McNemar on (a, b) pass pairs: b discordant counts as in the submitted analysis."""
    from scipy.stats import binomtest
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    p = binomtest(b, b + c, 0.5).pvalue if b + c else None
    return {"pairs": len(pairs), "a_only": b, "b_only": c, "p_two_sided": p}


def rerun_tally(attempts, flags, by_machine):
    """Per variant, from the generator calls of calls.jsonl joined by ctx_uid: the failed attempts that owe the D80 V1
    rerun (an Ollama call with a tool-call parse error, a stall, or an HTTP 500 or dropped connection; Gemini is never
    retried), the failed attempts with add_cell written as text (D81 Q137; counted whether or not they also owe D80 V1,
    and the overlap given), and, apart, the passing attempts that met one of these events. With whether the clone
    that wrote the variant's records ran code that has D80 (the manifest's clone commit, against D80_COMMIT)."""
    out = {}
    for v, _, _ in VARIANTS:
        xs = [a for a in attempts if variant_of(a["run_id"]) == v]
        if not xs:
            continue
        c = Counter()
        for a in xs:
            fl = flags.get(a.get("ctx_uid"), set())
            ev = [] if a["gen_model"].startswith("gemini::") else \
                [e for e in ("parse", "stall", "retry_call_error") if e in fl]
            side = "passed" if a["passed"] else "failed"
            if ev:
                c[f"{side}_with_d80v1_event"] += 1
                c[f"{side}_with_d80v1_event: {ev[0]}"] += 1
            if "as_text" in fl:
                c[f"{side}_with_add_cell_as_text"] += 1
                if ev:
                    c[f"{side}_with_add_cell_as_text_and_d80v1_event"] += 1
        commits = sorted({k.split()[-1] for k in by_machine.get(v, {})})
        has = {cm: subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", D80_COMMIT, cm],
                                  capture_output=True).returncode == 0 for cm in commits}
        out[v] = {"attempts": len(xs), "failed_owing_d80v1_rerun": c["failed_with_d80v1_event"],
                  "failed_with_add_cell_as_text_d81": c["failed_with_add_cell_as_text"],
                  "clone_commits_have_d80": has, **dict(sorted(c.items()))}
    tot = Counter()
    for r in out.values():
        for k, n in r.items():
            if isinstance(n, int):
                tot[k] += n
    return {"by_variant": out, "totals": dict(sorted(tot.items())),
            "definition": " ".join(rerun_tally.__doc__.split())}


def calls_measures(by, done, ops, get=None):
    """Best-of-3 against free-form over the complete variants (by: attempts by (variant, strategy, operation)): the mean
    model calls per attempt, each attempt counted by llm_calls() (D115 LS1; or get, for a mutant), the mean latency_s,
    each ratio, and n_llm_calls_d115_ls1: per strategy, the length-cut attempts counted to their stop and the other
    attempts whose stored n_llm_calls differs from their generator records (the attempt's own calls list). The keys
    extras() writes."""
    get = get or llm_calls
    out = {}

    def mean_of(c, field):
        g = get if field == "n_llm_calls" else (lambda x: x.get(field))
        xs = [g(by[(v, c, o)]) for v in done for o in ops if (v, c, o) in by]
        xs = [x for x in xs if isinstance(x, (int, float))]
        return sum(xs) / len(xs) if xs else None
    for f in ("n_llm_calls", "latency_s"):
        a, b = mean_of("free_form_n3_best", f), mean_of("free_form", f)
        out[f"ratio_{f}_best_of_3_to_free_form"] = (a / b) if a and b else None
        out[f"mean_{f}"] = {"free_form_n3_best": a, "free_form": b}
    ls1 = {}
    for c in ("free_form_n3_best", "free_form"):
        xs = [by[(v, c, o)] for v in done for o in ops if (v, c, o) in by]
        rest = [x for x in xs if "length_rule" not in x]
        ls1[c] = {"attempts": len(xs), "length_cut_counted_to_stop": len(xs) - len(rest),
                  "n_llm_calls_differs_from_generator_records": sum(
                      x.get("n_llm_calls") != sum(1 for k in x.get("calls") or [] if k.get("role") == "generator")
                      for x in rest)}
    out["n_llm_calls_d115_ls1"] = ls1
    return out


def calls_mean_cases(get=None):
    """D115 LS1 through call_flags(), apply_length_rule() and calls_measures() (get replaces llm_calls(), for a
    mutant), as load_mirror() and extras() run them. One complete variant: best-of-3 b1 length-cut under "retry"
    (stored 4, 2 calls to its stop) and b2 not cut (stored 4, 4 calls); free-form f1 length-cut under "stop" (stored
    None, a transient error then the stop: 2 calls), f2 not cut (stored 1, 1 call) and f3 not cut with a transient
    retry (stored 1, 2 generator records). Wanted: means 3.0 and 4/3, ratio 2.25, and the two counters. Returns
    (problems, cases)."""
    V = "gpt-oss-20b+low"

    def call(u, seq, status="ok", error=None):
        return {"role": "generator", "ctx_uid": u, "seq": seq, "status": status, "error": error,
                "stop_reason": "length" if status == "length" else "stop", "provider": "ollama",
                "call_site": "exp_v2_8_coder_benchmark.py:1 _run_free_form", "candidate": None, "text": "",
                "tool_calls": None}
    seqs = {"b1": [call("b1", 1), call("b1", 2, "length"), call("b1", 3), call("b1", 4)],
            "b2": [call("b2", k) for k in (1, 2, 3, 4)],
            "f1": [call("f1", 1, "error", "HTTP 500"), call("f1", 2, "length")],
            "f2": [call("f2", 1)],
            "f3": [call("f3", 1, "error", "HTTP 500"), call("f3", 2)]}
    stored = {"b1": ("free_form_n3_best", 4, "retry"), "b2": ("free_form_n3_best", 4, None),
              "f1": ("free_form", None, "stop"), "f2": ("free_form", 1, None), "f3": ("free_form", 1, None)}
    atts = [{"ctx_uid": u, "run_id": f"exp_05__{c}__{V}", "config": c, "op_id": f"op_{u[1]}", "passed": False,
             "exec_outcome": "length" if rule == "stop" else "ok", "n_llm_calls": n, "length_stop_rule": rule,
             "latency_s": 1.0, "calls": seqs[u]} for u, (c, n, rule) in stored.items()]
    flags, last = defaultdict(set), {}
    for u in seqs:
        for r in seqs[u]:
            call_flags(r, flags, last)
    apply_length_rule(atts, flags, last)
    by = {(variant_of(a["run_id"]), a["config"], a["op_id"]): a for a in atts}
    got = calls_measures(by, [V], sorted({a["op_id"] for a in atts}), get=get)
    bad = []
    m, r = got["mean_n_llm_calls"], got["ratio_n_llm_calls_best_of_3_to_free_form"]
    if (m["free_form_n3_best"], round(m["free_form"], 9), round(r or 0, 9)) != (3.0, round(4 / 3, 9), 2.25):
        bad.append(f"calls means {m}, ratio {r} (want 3.0, 1.333, 2.25)")
    want = {"free_form_n3_best": {"attempts": 2, "length_cut_counted_to_stop": 1,
                                  "n_llm_calls_differs_from_generator_records": 0},
            "free_form": {"attempts": 3, "length_cut_counted_to_stop": 1,
                          "n_llm_calls_differs_from_generator_records": 1}}
    if got["n_llm_calls_d115_ls1"] != want:
        bad.append(f"n_llm_calls_d115_ls1 {got['n_llm_calls_d115_ls1']}, want {want}")
    return bad, 2


def extras(attempts, cells, variants, flags, notes):
    """The measures the claims list compares with the text (findings/figures_provisional/fig6/claims.md). Every
    measure over 'complete variants' uses only the variants with all 220 attempts stored."""
    done = [v for v, s in variants.items() if s["complete"]]
    by = {(variant_of(a["run_id"]), a["config"], a["op_id"]): a for a in attempts}
    ops = sorted({a["op_id"] for a in attempts})
    out = {"complete_variants": done}
    # mean across variants of the per-variant cell rate, per strategy (the text's "mean pass rate across models")
    out["strategy_mean_over_complete_variants"] = {
        c: (sum(x["pass_rate_pct"] for x in cells if x["strategy"] == c and x["variant"] in done) / len(done)
            if done else None) for c, _ in STRATEGIES}

    def paired(c1, c2):
        return [(by[(v, c1, o)]["passed"], by[(v, c2, o)]["passed"]) for v in done for o in ops
                if (v, c1, o) in by and (v, c2, o) in by]
    out["mcnemar_best_of_3_vs_free_form"] = mcnemar_exact(paired("free_form_n3_best", "free_form"))
    out["mcnemar_combined_vs_free_form"] = mcnemar_exact(paired("free_form_n3_combined", "free_form"))

    out.update(calls_measures(by, done, ops))
    # every stored variant, outside structured output (the text's gpt-oss levels, nemotron, glm)
    out["outside_structured_by_variant"] = {}
    for v, _, _ in VARIANTS:
        xs = [a for a in attempts if variant_of(a["run_id"]) == v and not a["config"].startswith("coder_v2")]
        k = sum(a["passed"] for a in xs)
        out["outside_structured_by_variant"][v] = {"attempts": len(xs), "of": PER_CELL * 7, "pass": k,
                                                   "pass_rate_pct": pct(k, len(xs))}
    # introspection: per complete variant, its best introspection strategy minus free-form, in points
    gains = {}
    for v in done:
        r = {x["strategy"]: x["pass_rate_pct"] for x in cells if x["variant"] == v}
        gains[v] = max(r[c] for c in INTROSPECTION) - r["free_form"]
    out["introspection_best_minus_free_form_pts"] = gains
    # structured output per variant with data: best structured cell, records with no code
    st = {}
    for v, _, _ in VARIANTS:
        xs = [a for a in attempts if variant_of(a["run_id"]) == v and a["config"].startswith("coder_v2")]
        if not xs:
            continue
        rates = [x["pass_rate_pct"] for x in cells if x["variant"] == v and x["strategy"].startswith("coder_v2")
                 and x["attempts"]]
        st[v] = {"attempts": len(xs), "best_cell_pct": max(rates), "records_with_no_code":
                 sum(1 for a in xs if not (a.get("code") or a.get("code_cells"))),
                 "complete_cells": sum(1 for x in cells if x["variant"] == v and x["strategy"].startswith("coder_v2")
                                       and x["complete"])}
    out["structured_by_variant"] = st
    out["cells_where_no_record_produced_code"] = [
        (x["variant"], x["strategy"], x["attempts"]) for x in cells if x["attempts"] and
        not any((a.get("code") or a.get("code_cells")) for a in attempts
                if variant_of(a["run_id"]) == x["variant"] and a["config"] == x["strategy"])]
    # field coverage (the SI table of stored fields: judge_score, passed, field_results, exec_error)
    n = len(attempts)
    out["field_coverage_pct"] = {f: pct(sum(1 for a in attempts if a.get(f) not in (None, "", {}, [])), n)
                                 for f in ("judge_score", "passed", "field_results", "exec_error")}
    out["field_present_pct"] = {f: pct(sum(1 for a in attempts if f in a), n)
                                for f in ("judge_score", "passed", "field_results", "exec_error")}
    # operations: datasets and complexity tiers, as the records name them
    opinfo = {a["op_id"]: (a.get("dataset"), a.get("complexity")) for a in attempts}
    out["operations"] = {"n": len(opinfo), "by_dataset": dict(Counter(d for d, _ in opinfo.values())),
                         "by_complexity": dict(Counter(c for _, c in opinfo.values()))}
    # the reference values the airway and lung data give (field_results expected, operation 1 of each)
    exp = {}
    for a in attempts:
        if a["op_id"] in ("airway_1_dimensions", "lung_1_dimensions") or a["op_id"].endswith("_1_dimensions"):
            exp[a["op_id"]] = {k: v.get("expected") for k, v in (a.get("field_results") or {}).items()}
    out["reference_values_op1"] = exp
    # what the generator calls sent: num_ctx, and the temperature of free-form best-of-3's candidate calls
    ctx, temp = Counter(), defaultdict(Counter)
    for a in attempts:
        for c in a.get("calls") or []:
            if c.get("role") != "generator":
                continue
            o = c.get("options_sent") or {}
            ctx[str(o.get("num_ctx"))] += 1
            if a["config"] == "free_form_n3_best" and c.get("candidate") is not None:
                temp[variant_of(a["run_id"])][str(o.get("temperature"))] += 1
    out["generator_num_ctx_sent"] = dict(ctx)
    out["best_of_3_candidate_temperature_sent"] = {v: dict(t) for v, t in temp.items()}
    # records per model, as Supplementary Table 2 (S534 t7) counts them per run file (design and stored)
    d_vs = design_of(attempts)[0]                 # D100, D112 Q15 O-a
    out["records_per_model"] = {m: {"design": PER_VARIANT * sum(1 for v in d_vs if VMODEL[v] == m),
                                    "stored": sum(variants[v]["attempts"] for v, mm, _ in VARIANTS if mm == m)}
                                for m in dict.fromkeys(VMODEL.values())}
    out["best_of_3_design_attempts"] = PER_CELL * len(d_vs)
    out["reruns_owed"] = rerun_tally(attempts, flags, notes["attempts_by_machine"])
    out["length_rule_d114_by_variant"] = notes["length_rule_d114_by_variant"]   # D114 Q29 O2 (apply_length_rule)
    out["q4_lung9_rescore"] = notes["q4_lung9_rescore"]   # Q4 (24 Oct): S477, lung_9 read with the fixed extraction
    out["attempts_by_machine"] = notes["attempts_by_machine"]
    out["generator_reasoning_by_variant"] = notes["generator_reasoning_by_variant"]
    out["strategies_stored_by_variant"] = {
        v: {x["strategy"]: x["attempts"] for x in cells if x["variant"] == v and x["attempts"]}
        for v, _, _ in VARIANTS if variants[v]["attempts"]}
    return out


# ---------------------------------------------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------------------------------------------
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def draw_plate(cells, variants, strat, panel_a_set, think, stamp, png, svg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np

    plt.rcParams.update({"font.family": "Helvetica", "font.size": 9, "axes.edgecolor": GRID,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                         "svg.fonttype": "none"})
    fig = plt.figure(figsize=(11, 22), facecolor=SURF)
    gs = fig.add_gridspec(4, 1, height_ratios=[2.0, 6.4, 4.6, 5.0], hspace=0.30,
                          left=0.22, right=0.88, top=0.975, bottom=0.04)
    labels = [lab for _, lab in STRATEGIES]
    order = sorted([v for v, _, _ in VARIANTS], key=lambda v: (variants[v]["attempts"] == 0,
                                                               -(variants[v]["pass_rate_pct"] or 0)))

    def stamp_on(ax):
        ax.text(1.0, 1.015, stamp, transform=ax.transAxes, ha="right", va="bottom", fontsize=7.2, color="#7a1f1f",
                bbox=dict(boxstyle="square,pad=0.25", fc="#fbeaea", ec="#d9a3a3", lw=0.6))

    def letter(ax, s):
        ax.text(-0.29, 1.03, s, transform=ax.transAxes, fontsize=13, fontweight="bold", color=INK, va="bottom")

    # a
    ax = fig.add_subplot(gs[0])
    for i, (c, lab) in enumerate(STRATEGIES):
        s = strat[c]
        if s["median"] is None:
            ax.text(i, 50, "no variant\ncomplete", ha="center", va="center", fontsize=7, color=INK2)
            continue
        ax.plot([i, i], [s["min"], s["max"]], color="#2a78d6", lw=1, solid_capstyle="round")
        ax.plot([i, i], [s["q1"], s["q3"]], color="#2a78d6", lw=5, solid_capstyle="butt")
        ax.plot(i, s["median"], "o", color=INK, ms=6, mec=SURF, mew=1.5, zorder=3)
    ax.set_xlim(-0.5, len(STRATEGIES) - 0.5)
    ax.set_ylim(-20, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xticks([])
    ax.set_ylabel("pass rate (%)")
    names = defaultdict(list)
    for v in panel_a_set:
        names[VMODEL[v]].append(VTHINK[v])
    ax.text(-0.45, -8, f"The same {len(panel_a_set)} variants in every strategy, those complete in all 11 "
            "(variants still partial are shown in b only):\n"
            + "; ".join(f"{m} [{', '.join(t)}]" for m, t in names.items()) + ".",
            ha="left", va="top", fontsize=6.8, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.set_axisbelow(True)
    letter(ax, "a")
    stamp_on(ax)

    # b
    ax = fig.add_subplot(gs[1])
    cmap = LinearSegmentedColormap.from_list("seq", ["#eef4fc", "#9cc1ee", "#2a78d6", "#123a6e"])
    grid = np.full((len(order), len(STRATEGIES)), np.nan)
    for r, v in enumerate(order):
        for j, (c, _) in enumerate(STRATEGIES):
            cell = next(x for x in cells if x["variant"] == v and x["strategy"] == c)
            if cell["attempts"]:
                grid[r, j] = cell["pass_rate_pct"]
            val = cell["pass_rate_pct"]
            if cell["attempts"] == 0:
                txt, col = "pending", INK2
            else:
                txt = half_up(val, 1) + ("" if cell["complete"] else f"\nn={cell['attempts']}")
                col = "white" if val >= 55 else INK
            ax.text(j, r, txt, ha="center", va="center", fontsize=7.5 if cell["complete"] else 6.5, color=col)
    shown = np.ma.masked_invalid(grid)
    ax.imshow(np.zeros_like(grid), cmap=LinearSegmentedColormap.from_list("bg", ["#f1f0ed", "#f1f0ed"]),
              aspect="auto")
    ax.imshow(shown, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for r in range(len(order) + 1):
        ax.axhline(r - 0.5, color=SURF, lw=2)
    for j in range(len(STRATEGIES) + 1):
        ax.axvline(j - 0.5, color=SURF, lw=2)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{vlabel(v)}  ({variants[v]['attempts']}/{PER_VARIANT})" for v in order], fontsize=8)
    ax.set_xticks(range(len(STRATEGIES)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    letter(ax, "b")
    stamp_on(ax)

    # c: thinking level
    ax = fig.add_subplot(gs[2])
    role = {"off": 0, "low": 0, "default": 1, "medium": 1, "high": 2}
    cols, marks = ["#2a78d6", "#eb6834", "#1baf7a"], ["o", "^", "s"]
    models = list(think)
    models.sort(key=lambda m: (think[m]["variants_with_data"] == 0, m))
    for r, m in enumerate(models):
        rows = think[m]["variants"]
        single = len(rows) == 1
        for i, row in enumerate(rows):
            y = r + (0 if single else (i - (len(rows) - 1) / 2) * 0.22)
            if row["op_mean_pass_rate_pct"] is None:
                continue
            k = role[row["thinking"]]
            ax.plot([row["op_boot95_lo"], row["op_boot95_hi"]], [y, y], color=cols[k], lw=1.6,
                    solid_capstyle="round")
            ax.plot(row["op_mean_pass_rate_pct"], y, marks[k], color=cols[k], ms=7, mec=SURF, mew=1.2, zorder=3)
            ax.text(row["op_boot95_hi"] + 1.2, y, row["panel_label"], va="center", fontsize=6.8, color=INK2)
        note = "pending" if think[m]["variants_with_data"] == 0 else \
            f"n = {think[m]['operations_n']} operations ({think[m]['matched_on']} attempts)"
        ax.text(101.5, r, note, va="center", fontsize=6.8, color=INK2, clip_on=False)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"pass rate (%), matched attempts; 95% interval over {N_BOOT:,} resamples of the operations")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], color=cols[i], marker=marks[i], lw=1.6, label=l) for i, l in
                       enumerate(["off (gpt-oss: low, its lowest level)", "default (gpt-oss: medium)",
                                  "high (gpt-oss only)"])],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False, fontsize=7.5)
    letter(ax, "c")
    stamp_on(ax)

    # d: failures by kind
    ax = fig.add_subplot(gs[3])
    for r, v in enumerate(order):
        left = 0
        fk = variants[v]["fail_kinds"]
        folded = Counter()
        for x, n in fk.items():
            folded[FOLD[x]] += n
        for i, f in enumerate(FOLDED):
            n = folded.get(f, 0)
            if n:
                ax.barh(r, n, left=left, color=FOLD_COL[i], height=0.7, edgecolor=SURF, linewidth=1)
            left += n
        nf = variants[v]["attempts"] - variants[v]["pass"]
        ax.text(left + 2, r, f"{nf} failed of {variants[v]['attempts']}" if variants[v]["attempts"] else "pending",
                va="center", fontsize=6.8, color=INK2)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([vlabel(v) for v in order], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("failed attempts (count)")
    xmax = max((variants[v]["attempts"] - variants[v]["pass"]) for v in order)
    ax.set_xlim(0, max(10, xmax * 1.25))
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=FOLD_COL[i], label=f) for i, f in enumerate(FOLDED)], loc="upper center",
              bbox_to_anchor=(0.5, -0.07), ncol=3, frameon=False, fontsize=7.5)
    letter(ax, "d")
    stamp_on(ax)

    fig.savefig(png, dpi=200, facecolor=SURF)
    fig.savefig(svg, facecolor=SURF)
    plt.close(fig)


def provenance(argv, inputs):
    return {"script": "scripts/S447_fig6_panels.py", "script_sha256": sha256_file(Path(__file__)),
            "command": "uv run --frozen python scripts/S447_fig6_panels.py " + " ".join(argv),
            "python": platform.python_version(), "written_utc": utc_now(),
            "repo_head": git("rev-parse", "--short", "HEAD"),
            "script_dirty_vs_head": git("status", "--short", "--", str(Path(__file__))),
            "inputs_sha256": inputs, "model_calls": 0}


def header_lines(p, stamp):
    return [f"provenance: script {p['script']} sha256 {p['script_sha256'][:16]}",
            f"command: {p['command']}", f"written {p['written_utc']}, repository HEAD {p['repo_head']}"
            f"{' (script uncommitted: ' + p['script_dirty_vs_head'] + ')' if p['script_dirty_vs_head'] else ''}",
            f"inputs: {len(p['inputs_sha256'])} files hashed (sha256 in fig6_numbers.json), records manifest "
            f"{p['inputs_sha256'].get(str(MANIFEST.relative_to(ROOT)), '')[:16]}", f"data stamp: {stamp}",
            "no model call"]


VIEW_DIR = Path(tempfile.gettempdir()) / "S447_fig6_working_view"   # the working view's default folder (D92 Q195)


def draw(argv, view_dir=None):
    view_dir = Path(view_dir or VIEW_DIR).expanduser().resolve()
    if view_dir == ROOT or ROOT in view_dir.parents:
        raise SystemExit(f"--view-dir {view_dir} is inside the repository: the working view breaks FIGURE_LOCK and is "
                         f"not committed (D92 Q195); give a folder outside {ROOT}")
    reproduced = reproduce()                      # stops (exit 2) before anything is written
    attempts, flags, inputs, notes = load_mirror()
    inputs[str(LOCK.relative_to(ROOT))] = sha256_file(LOCK)          # panel c's labels read its [sampling.models]
    attempts, d_vs, d_total, d_left = keep_design(attempts)          # D100, D112 Q15 O-a
    cells, variants, strat, panel_a_set, think, pooled, chi = compute(attempts, flags)
    claims_support = extras(attempts, cells, variants, flags, notes)
    n = sum(v["attempts"] for v in variants.values())
    k = sum(v["complete"] for v in variants.values())
    when = iso_local(notes["newest_answers_mtime"])
    stamp = (f"PROVISIONAL: {n:,} of {d_total:,} attempts, {k} of {len(d_vs)} variants complete, records of "
             f"{when}; after the S4 reruns (D75, D80 V1, D81)")
    notes["newest_answers_mtime"] = when
    OUT.mkdir(parents=True, exist_ok=True)
    prov = provenance(argv, inputs)
    view_dir.mkdir(parents=True, exist_ok=True)
    png, svg = view_dir / "fig6_provisional.png", view_dir / "fig6_provisional.svg"
    draw_plate(cells, variants, strat, panel_a_set, think, stamp, png, svg)
    # provenance into the SVG as a comment after the XML declaration
    head = "\n".join(header_lines(prov, stamp)).replace("--", "- -")
    s = svg.read_text()
    i = s.find("?>") + 2
    svg.write_text(s[:i] + f"\n<!--\n{head}\n-->" + s[i:])
    try:
        from PIL import Image, PngImagePlugin
        im = Image.open(png)
        meta = PngImagePlugin.PngInfo()
        meta.add_text("provenance", head)
        im.save(png, pnginfo=meta)
    except ImportError:
        pass
    with open(OUT / "fig6_cells.csv", "w", newline="") as f:
        for ln in header_lines(prov, stamp):
            f.write(f"# {ln}\n")
        w = csv.DictWriter(f, fieldnames=list(cells[0]))
        w.writeheader()
        w.writerows(cells)
    out = {"provenance": prov, "stamp": stamp, "records": notes | {"attempts": n, "variants_complete": k,
                                                                    "of_attempts": d_total, "of_variants": len(d_vs),
                                                                    "if_time_not_drawn": d_left},
           "reproduced": reproduced, "design": {"variants": len(d_vs), "variant_list": d_vs,
                                                "strategies": len(STRATEGIES), "operations": N_OPS, "draws": N_DRAWS,
                                                "attempts": d_total, "runner_variants": len(VARIANTS),
                                                "runner_attempts": TOTAL, "if_time": IF_TIME, "removed": REMOVED,
                                                "rule": "D100; D112 Q15 O-a: an if-time variant is in the design "
                                                        "only with all its attempts stored; D116: a removed variant "
                                                        "is never in it"},
           "fail_kinds_order": KINDS_ALL, "fail_kinds_folded_in_panel_d": FOLD,
           "panel_a_per_strategy": strat, "panel_a_variants": panel_a_set, "panel_b_cells": cells, "panel_b_variant_order_and_pooled": variants,
           "panel_c_thinking": think, "pooled_structured_vs_free_form": pooled, "interaction_chi2": chi,
           "claims_support": claims_support,
           "panels": {"a": "per strategy: median, IQR and range of the per-variant pass rates, over the same "
                           "variants in every strategy: those complete in all 11 (panel_a_variants)",
                      "b": "variant by strategy pass rate, variants ordered by pooled rate over stored attempts; "
                           "a partial cell shows its n, an empty one reads pending",
                      "c": "thinking setting per model, pass rate on the attempts every variant of the model with "
                           "data holds (matched by answer_key), 95% percentile interval over 10,000 resamples of the "
                           "operations (op_bootstrap); a one-variant model's "
                           "label reads LOCK.toml [sampling.models] think (omit: '(= off)', always: "
                           "'(always thinks)')",
                      "d": "failed attempts per variant by kind (fail_kind), folded to nine groups"}}
    (OUT / "fig6_numbers.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(stamp)
    for v in sorted(variants, key=lambda v: -variants[v]["attempts"]):
        s = variants[v]
        print(f"  {s['label']:38s} {s['attempts']:4d} stored  pass {s['pass']:4d}"
              f"  {('%.1f%%' % s['pass_rate_pct']) if s['attempts'] else '':>6s}"
              f"  {'complete' if s['complete'] else ''}")
    print_earlier_label(attempts, flags)
    print(f"wrote {(OUT / 'fig6_cells.csv').relative_to(ROOT)}, fig6_numbers.json; the working view (not committed, "
          f"D92 Q195) {png}, {svg.name}")


# ---------------------------------------------------------------------------------------------------------------
# Step 3: figure. The submission plate, drawn to the editor's figure rules (experiments/FIGURE_RULES.md E1-E8)
# ---------------------------------------------------------------------------------------------------------------
# The figure rules (D84, D87): every size, font, colour and limit the plate takes is read from
# experiments/FIGURE_LOCK.toml, never written here a second time. The figure step refuses to draw unless the lock's
# status is "agreed" (figure_lock_agreed()).
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"


def _figure_lock():
    import tomllib
    return tomllib.loads(FIGURE_LOCK.read_text())


FLOCK = _figure_lock()


def figure_lock_agreed():
    if FLOCK.get("status") != "agreed":
        raise SystemExit(f"{FIGURE_LOCK.relative_to(ROOT)} has status {FLOCK.get('status')!r}, not 'agreed' (D87): "
                         f"no plate is drawn")
    if FLOCK["type"]["panel_letter_case"] not in ("lowercase", "uppercase"):
        raise SystemExit(f"[type] panel_letter_case {FLOCK['type']['panel_letter_case']!r}: S447 draws lowercase or "
                         f"uppercase panel letters")


# Okabe and Ito's eight colours for categories, as [colour] categorical lists them (Wong 2011, Nat. Methods 8, 441,
# in that paper's order: black, orange, sky blue, bluish green, yellow, blue, vermillion, reddish purple; S447 names
# them by their place in the lock's list, so a reordered list reassigns them, and figure6_provenance.json records which
# colour each kind of d got), and
# [colour] continuous (cividis) for the one sequential scale (E1, E3). Grey is Okabe-Ito's own #999999, a grey under
# [colour] grey_tol.
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
assert len(_CAT) == 8, f"[colour] categorical holds {len(_CAT)} colours; S447 names Okabe and Ito's eight"
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
OKABE_GREY = "#999999"
CMAP_NAME = FLOCK["colour"]["continuous"]
# The tools-refused group's fill (D112 Q12 O2): Okabe and Ito's eight colours and their grey are all taken, so a dark
# grey, a grey under [colour] grey_tol (S448 R5), far from black (length stop) and from OKABE_GREY, and carrying its own
# pattern (KIND_PATTERN "*"); its pattern lines are white (ink_on(), 6.9:1)
TOOLS_GREY = "#5A5A5A"
# panel d: the ten folded kinds (FOLD) in the order fail_kind() tries them, the folded "other" group last (its three
# kinds come 9th, 10th and 13th in that order; the legend defines all thirteen in order)
FIG_KINDS = [("tool-call parse error", OKABE["vermillion"]), ("tool call written as text", OKABE["reddish purple"]),
             ("stall or other call error", OKABE["bluish green"]), ("tools refused by Ollama", TOOLS_GREY),
             ("length stop", OKABE["black"]),
             ("harness error", OKABE["yellow"]), ("step produced no cell and no error", OKABE["sky blue"]),
             ("code raised or timed out", OKABE["orange"]), ("result wrong or missing", OKABE["blue"]),
             ("other (Gemini empty, no code, other)", OKABE_GREY)]
assert [k for k, _ in FIG_KINDS] and set(k for k, _ in FIG_KINDS) == set(FOLDED)
# Each kind as fail_kind() and call_flags() decide it, in fail_kind()'s order (the legend prints these)
KIND_DEF = {
    "tool-call parse error": "a model call failed because Ollama could not parse the tool call the model wrote",
    "tool call written as text": "a structured step's reply carried no tool call but wrote the add_cell call as plain "
                                 "text",
    "stall": "a model call stopped receiving tokens for 600 s after its first one",
    "tools refused by Ollama": "Ollama refused a model call that offered tools, because the model as Ollama serves it "
                               "has no tool support (HTTP 400, 'does not support tools'), so the tools never reached "
                               "the model",
    "other call error": "a model call failed in another way (another HTTP 400 reply, an HTTP 500 reply, a dropped "
                        "connection, a malformed Gemini call), or the attempt's record says a call error ended it",
    "length stop": "a model call stopped at its length limit, which ends the attempt there (D114)",
    "harness error": "the benchmark harness raised an exception, not the generated code",
    "step produced no cell and no error": "a structured step's code-writing turn ended normally without creating a "
                                          "notebook cell and without an error message, so the step was recorded as "
                                          "failed with no error text",
    "Gemini empty reply": "a Gemini attempt whose last reply was empty",
    "no code": "no code was written or run",
    "code raised or timed out": "the generated code raised an error or timed out and printed no result",
    "result wrong or missing": "the code ran but its printed result did not match the reference",
    "other": "none of the above",
}
assert list(KIND_DEF) == KINDS_ALL
# Panel d's keyed groups whose key label does not explain itself, as the legend defines them (KIND_DEF above is the
# full rule); the other labels are read from the key on the plate
LEGEND_KIND_DEF = {
    "stall or other call error": "a stall is 600 s with no further token",
    "tools refused by Ollama": "tools refused by Ollama means the model as Ollama serves it has no tool support",
    "other (Gemini empty, no code, other)": "other is an empty Gemini reply, no code written or none of the kinds "
                                            "keyed",
}
assert set(LEGEND_KIND_DEF) <= {k for k, _ in FIG_KINDS}
# Type (experiments/FIGURE_RULES.md E1), from the lock: every text at [type] font_min_pt, the one size, since the lock
# asks type sizes within a plate to vary as little as they can ([type] size_variance); no panel titles ([files]
# titles_in_figure, Valerio Q2, 17 October); panel letters [type] panel_letter_pt, panel_letter_weight,
# panel_letter_case; the first family of [type]
# font_families, embedded as TrueType (pdf.fonttype 42; [type] font_types_refused names Type3).
PT_TEXT = float(FLOCK["type"]["font_min_pt"])
PT_AXIS = PT_TEXT
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper


# D283 (6 November 2026): code generation is main Figure 7 (6 until then); the folder stays fig6
FIG_N = 7


def sheet_name(letter):
    """The Source Data sheet of a panel, named by the panel's letter as drawn ([type] panel_letter_case)."""
    return f"Fig. {FIG_N}{LETTER_CASE(letter)}"


def bold_letter(letter):
    """A panel letter as the legend writes it (bold, in [type] panel_letter_case)."""
    return f"**{LETTER_CASE(letter)}**"
FONT = FLOCK["type"]["font_families"][0]
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])    # text against what is painted under it (R11)
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])            # the thinnest line drawn (R12)
FIG_W_MM = float(FLOCK["page"]["width_double_mm"])            # double column
FIG_H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
MIN_D = 20                                        # panel d draws no share over fewer attempts than one strategy holds
# Text colours other than black and white: b's "reference" and d's "too few attempts" with its row label. Each is the
# grey named here where it reaches [type] contrast_min_ratio on the white page, else the lightest grey that does
# (grey_text below)
GREY_NOTE_WANT, GREY_FEW_WANT = "#5A5A5A", "#767676"
# panel c's grey dots (one strategy): a mid grey at 3.4:1 on white, so the points are not faint ([lines] faint_lines;
# WCAG 2.1 1.4.11 asks 3:1 of a graphic object), lighter than the blue marker and bar they sit above
C_DOT_GREY = "#8C8C8C"


def wcag_ratio(c1, c2):
    """WCAG 2.1 contrast ratio of two colours given as '#RRGGBB' or (r, g, b) from 0 to 1 (S448 R11's measure)."""
    def lum(c):
        if isinstance(c, str):
            c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3]]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def ink_on(fill):
    """Black or white, whichever stands out more from fill; it must reach [type] contrast_min_ratio, or no plate is
    drawn."""
    best = max(("#000000", "#FFFFFF"), key=lambda c: wcag_ratio(c, fill))
    if wcag_ratio(best, fill) < CONTRAST_MIN:
        hexed = fill if isinstance(fill, str) else "#" + "".join(f"{round(float(x) * 255):02X}" for x in fill[:3])
        raise SystemExit(f"no text colour reaches [type] contrast_min_ratio {CONTRAST_MIN:g} on {hexed}: black or "
                         f"white reaches {wcag_ratio(best, fill):.2f}; no plate is drawn")
    return best


def grey_text(want):
    """want where it reaches [type] contrast_min_ratio on white, else the lightest grey that does (black at worst)."""
    if wcag_ratio(want, "#FFFFFF") >= CONTRAST_MIN:
        return want
    return next((c for c in (f"#{v:02X}{v:02X}{v:02X}" for v in range(255, -1, -1))
                 if wcag_ratio(c, "#FFFFFF") >= CONTRAST_MIN), "#000000")


GREY_NOTE, GREY_FEW = grey_text(GREY_NOTE_WANT), grey_text(GREY_FEW_WANT)
# Panel d's second cue (FIGURE_LOCK.toml [colour] patterns: the journal asks for patterns instead of or in addition to
# colours): each folded kind also has its own fill pattern, drawn in the bars and in the key, in black or white
# lines (ink_on) of [lines] line_min_pt: "/" and "\" diagonal lines, "x" both, "-" horizontal, "|" vertical, "+" both,
# "*" all four at twice the spacing (a star mesh), "." dots, "o" rings, "z" horizontal zigzag lines. Every kind has a
# pattern (Valerio, Q4, 17 October), so a segment drawn plain is only one narrower than its pattern's smallest whole
# mark (pattern_min_mm), which carries its colour alone (one attempt of 220 is about 0.5 mm of bar)
KIND_PATTERN = {"tool-call parse error": "/", "tool call written as text": "\\", "stall or other call error": "x",
                "tools refused by Ollama": "*", "length stop": "-", "harness error": "|",
                "step produced no cell and no error": "+", "code raised or timed out": ".",
                "result wrong or missing": "z", "other (Gemini empty, no code, other)": "o"}
HATCH_MM = 0.8                                    # distance between pattern lines (and between dots)
THINK_ORDER = {"off": 0, "low": 0, "default": 1, "medium": 1, "high": 2}
FIG_DIR_NAME = f"Figure {FIG_N}"


def short_variant(v):
    """A variant's label on the plate: the model's label (VARIANTS), with the thinking setting only when the model
    has more than one variant in the runner's list (VARIANTS, not the figure's design)."""
    m = VMODEL[v]
    multi = sum(1 for _, mm, _ in VARIANTS if mm == m) > 1
    return f"{m} ({VTHINK[v]})" if multi else m


def figure_numbers(attempts, cells, variants, think, panel_a_set, flags=None):
    """Every number the plate draws, as the Source Data sheets hold them (one table per panel), and d_exceptions: the
    plotted failed attempts whose record states kind 8's event in the newer form (Q101_FORM) but that fail_kind()
    files under a later kind (its test is the older text "Step failed: None"; matching both forms is proposal O1)."""
    cell = {(c["variant"], c["strategy"]): c for c in cells}
    a_cols = sorted(panel_a_set, key=lambda v: -(variants[v]["pass_rate_pct"] or 0))
    sheet_a = []
    for s, lab in STRATEGIES:
        for v in a_cols:
            c = cell[(v, s)]
            assert c["attempts"] == PER_CELL, (v, s, c["attempts"])        # panel a holds complete cells only
            sheet_a.append({"strategy": s, "strategy_label": lab, "variant": v, "model": VMODEL[v],
                            "thinking": VTHINK[v], "column_label": short_variant(v), "operations_n": c["attempts"],
                            "pass": c["pass"], "pass_rate_pct": c["pass_rate_pct"]})
    sheet_b = []
    for s, lab in STRATEGIES:
        if s == "free_form":
            continue
        gains = []
        for v in a_cols:
            g = cell[(v, s)]["pass_rate_pct"] - cell[(v, "free_form")]["pass_rate_pct"]
            gains.append(g)
            sheet_b.append({"strategy": s, "strategy_label": lab, "row": "variant (dot)", "variant": v,
                            "column_label": short_variant(v), "operations_n": PER_CELL,
                            "strategy_pass_rate_pct": cell[(v, s)]["pass_rate_pct"],
                            "free_form_pass_rate_pct": cell[(v, "free_form")]["pass_rate_pct"],
                            "gain_pct_points": g})
        q = quantiles(sorted(gains))
        sheet_b.append({"strategy": s, "strategy_label": lab, "row": f"median over {len(gains)} variants (line)",
                        "variant": "", "column_label": "", "operations_n": PER_CELL, "strategy_pass_rate_pct": None,
                        "free_form_pass_rate_pct": None, "gain_pct_points": q["median"]})
    # panel c: models with two or more settings stored, on the attempts every setting of the model holds. The point is
    # Rule 2's pass rate (op_mean: the mean over the operations of each one's share of passing attempts) and the
    # interval resamples the operations (op_bootstrap); n is the number of operations, with the attempts each holds.
    # The sheet also holds each operation's passes and attempts (the units behind the point and the interval)
    by_vk = defaultdict(dict)
    for a in attempts:
        by_vk[variant_of(a["run_id"])][a["answer_key"]] = a
    sheet_c, c_models = [], []
    blank = {"strategy": "", "operation": "", "operations_by_attempts": "", "boot95_lo_pct": None,
             "boot95_hi_pct": None, "resamples": None, "resample_seed": None}
    for m, t in think.items():
        if t["variants_with_data"] < 2:
            continue
        vs = [r for r in t["variants"] if r["matched_attempts"]]
        vs.sort(key=lambda r: THINK_ORDER[r["thinking"]])
        common = set.intersection(*(set(by_vk[r["variant"]]) for r in vs))
        assert len(common) == t["matched_on"], (m, len(common), t["matched_on"])
        per_s = Counter(by_vk[vs[0]["variant"]][k]["config"] for k in common)
        full = [s for s, _ in STRATEGIES if per_s.get(s) == PER_CELL]
        by_att = {int(k): x for k, x in t["operations_by_attempts"].items()}
        by_att_txt = ", ".join(f"{x} with {k}" for k, x in sorted(by_att.items()))
        c_models.append({"model": m, "settings": [r["thinking"] for r in vs], "matched": len(common),
                         "operations_n": t["operations_n"], "operations_by_attempts": by_att,
                         "full_strategies": full})
        for r in vs:
            sheet_c.append({**blank, "model": m, "thinking": r["thinking"], "variant": r["variant"],
                            "row": "setting (point and interval)", "operations_by_attempts": by_att_txt,
                            "operations_n": r["operations_n"], "attempts": r["matched_attempts"],
                            "pass": r["matched_pass"], "pass_rate_pct": r["op_mean_pass_rate_pct"],
                            "boot95_lo_pct": r["op_boot95_lo"], "boot95_hi_pct": r["op_boot95_hi"],
                            "resamples": N_BOOT, "resample_seed": BOOT_SEED})
            for o, (kp, na) in sorted(r["per_operation"].items()):
                sheet_c.append({**blank, "model": m, "thinking": r["thinking"], "variant": r["variant"],
                                "row": "operation (unit of the mean and the resamples)", "operation": o,
                                "operations_n": 1, "attempts": na, "pass": kp, "pass_rate_pct": pct(kp, na)})
            for s in full:
                ks = [k for k in common if by_vk[r["variant"]][k]["config"] == s]
                kp = sum(1 for k in ks if by_vk[r["variant"]][k]["passed"])
                sheet_c.append({**blank, "model": m, "thinking": r["thinking"], "variant": r["variant"],
                                "row": "strategy (grey dot)", "strategy": s, "operations_n": len(ks),
                                "attempts": len(ks), "pass": kp, "pass_rate_pct": pct(kp, len(ks))})
    # fixed column order for the sheet
    c_cols = ["model", "thinking", "variant", "row", "strategy", "operation", "operations_n", "operations_by_attempts",
              "attempts", "pass", "pass_rate_pct", "boot95_lo_pct", "boot95_hi_pct", "resamples", "resample_seed"]
    sheet_c = [{k: r[k] for k in c_cols} for r in sheet_c]
    # panel d: every variant with records; the complete ones in panel a's order, then the partial ones. The share of
    # the attempts stored that failed by each kind; a variant with fewer than MIN_D attempts gets no bar
    d_rows = a_cols + sorted([v for v, _, _ in VARIANTS if variants[v]["attempts"] and v not in a_cols],
                             key=lambda v: -variants[v]["attempts"])
    sheet_d = []
    for v in d_rows:
        s = variants[v]
        n = s["attempts"]
        folded = Counter()
        for x, c in s["fail_kinds"].items():
            folded[FOLD[x]] += c
        assert sum(folded.values()) == n - s["pass"], v
        drawn = n >= MIN_D
        sheet_d.append({"variant": v, "row_label": short_variant(v), "attempts_n": n, "of_design": PER_VARIANT,
                        "failed": n - s["pass"], "failed_share_pct": pct(n - s["pass"], n) if drawn else None,
                        "status": "plotted" if drawn else f"too few attempts (fewer than {MIN_D}), no bar",
                        **{f"share %: {k}": (pct(folded.get(k, 0), n) if drawn else None) for k, _ in FIG_KINDS},
                        **{f"count: {k}": folded.get(k, 0) for k, _ in FIG_KINDS},
                        **{f"unfolded count: {k}": s["fail_kinds"].get(k, 0) for k in KINDS_ALL}})
    import re
    k7 = KINDS_ALL.index("step produced no cell and no error")
    exc = Counter()
    plotted = {r["variant"] for r in sheet_d if r["failed_share_pct"] is not None}
    for a in attempts:
        v = variant_of(a["run_id"])
        if a["passed"] or v not in plotted or not re.search(Q101_FORM, a.get("exec_error") or ""):
            continue
        kd = fail_kind(a, (flags or {}).get(a.get("ctx_uid"), set()))
        if KINDS_ALL.index(kd) > k7:
            exc[(v, kd)] += 1
    d_exc = [{"variant": v, "row_label": short_variant(v), "kind": kd, "kind_number": KINDS_ALL.index(kd) + 1,
              "attempts": x} for (v, kd), x in sorted(exc.items())]
    return {"a_cols": a_cols, "a": sheet_a, "b": sheet_b, "c": sheet_c, "c_models": c_models, "d_rows": d_rows,
            "d": sheet_d, "d_exceptions": d_exc}


# Tied dots (panels b and c, FIGURE_RULES.md E2). Every tied dot is countable at print size: the dots of one value are
# set PITCH apart at right angles to the value axis (white between them), never along it. A row is made tall enough
# for the largest tie group it holds where the page allows (the layout for up to 7 variants, so up to 7 ties in b);
# where more tie than the row holds (the layout for 8 to 16 variants, 4.0 mm rows), the group is drawn closer, inside
# its band, and its count is printed beside it (count_label), so the number is read, not guessed.
B_DOT_MM, B_PITCH_MM = 0.85, 1.0                  # panel b: dot diameter, centre-to-centre distance of tied dots
C_DOT_MM, C_PITCH_MM = 0.70, 0.85                 # panel c: grey dot diameter and tied pitch
COUNT_GAP_MM = 0.10                               # tied dots are countable when this much white separates them
C_MARK_PT, C_BAR_PT = 3.6, 1.0                    # panel c: the mean marker (pt) and the interval bar's width (pt)
C_CLEAR_MM = 1.10                                 # panel c: grey dot centres keep this far from any bar's line
C_TOP_CLEAR_MM = C_CLEAR_MM + C_PITCH_MM          # panel c: and one tied place further from the bar above their own,
#                                                   so a group is read with the bar below it, never as one column with
#                                                   the dots of the next setting
H_ROOM_MM = 0.05                                  # the page stays this far under [page] height_max_mm: the PDF holds
#                                                   its size in points, so a page drawn at the bound measures over it
#                                                   (170 mm is written as 170.0000024 mm)
POS_TOL_MM = 0.01                                 # check_drawn: a mark lands within this of its workbook value
MM_PER_PT = 25.4 / 72


def ms_pt(mm):
    return mm / MM_PER_PT


def tie_offsets(values, half_mm, pitch_mm):
    """Offsets in mm (at right angles to the value axis) for dots at these values: the k dots of one value sit
    pitch_mm apart, centred, when (k - 1) * pitch_mm <= 2 * half_mm; otherwise they are spread evenly over the band
    and the value is returned among the overflowing ones (its count is printed). A dot keeps its exact value."""
    groups = defaultdict(list)
    for i, x in enumerate(values):
        groups[x].append(i)
    out, over = [None] * len(values), {}
    for x, idx in groups.items():
        k = len(idx)
        fits = (k - 1) * pitch_mm <= 2 * half_mm + 1e-9
        gap = pitch_mm if fits else 2 * half_mm / (k - 1)
        for j, i in enumerate(idx):
            out[i] = (j - (k - 1) / 2) * gap
            assert abs(out[i]) <= half_mm + 1e-9
        if not fits:
            over[x] = k
    return out, over


def pattern_marks(rect, pattern, step=HATCH_MM):
    """The lines and dots of one fill pattern (KIND_PATTERN) inside rect (x0, y0, x1, y1), in mm on the page, y
    downward: (lines, dots, rings), lines as point sequences ((xa, ya), (xb, yb), ...) inside rect (a straight line
    clipped to it, a zigzag of whole arms), dots and rings as centres at least their radius inside it. Every pattern is
    laid from the box's centre, so a narrow box still holds the pattern's middle: "|" and "+" a vertical line through
    the centre, "x" its two diagonals crossing on the centre, "." and "o" a column of marks on the centre line, "z" a
    column of zigzags each with a vertex on the centre line. A box narrower than the pattern's smallest whole mark
    (pattern_min_mm) gets no marks, so a pattern is never cut down into another kind's pattern ("+" into "-", "x" into
    "/", a zigzag into one diagonal arm: a zigzag keeps only its whole arms, at least two, one V). Dots and rings
    sit on a staggered grid where it fits: an odd row is shifted half a step, and in a box too narrow for any shifted
    mark the odd row keeps the even row's places; a shifted mark that would cross the edge is left out, never left
    unshifted beside its neighbour."""
    x0, y0, x1, y1 = rect
    lines, dots, rings = [], [], []
    if x1 - x0 < pattern_min_mm(pattern) - 1e-9 or y1 - y0 <= 1e-6 or not pattern:
        return lines, dots, rings
    xc, yc = (x0 + x1) / 2, (y0 + y1) / 2

    def around(c, lo, hi, st, half=False):
        """Positions c + k * st (k + 0.5 with half) strictly inside (lo, hi), in order."""
        k0 = math.floor((lo - c) / st) - 1
        out, k = [], k0
        while c + (k + (0.5 if half else 0)) * st < hi:
            v = c + (k + (0.5 if half else 0)) * st
            if lo < v:
                out.append(v)
            k += 1
        return out
    if pattern == "*":                            # a star mesh: "+" and "x" together, at twice their spacing
        step = 2 * step
    if pattern in ("-", "+", "*"):
        lines += [((x0, y), (x1, y)) for y in around(yc, y0 + 1e-9, y1 - 1e-9, step)]
    if pattern in ("|", "+", "*"):
        lines += [((x, y0), (x, y1)) for x in around(xc, x0 + 1e-9, x1 - 1e-9, step)]
    d = step * math.sqrt(2)
    if pattern in ("/", "x", "*"):                # rising to the right: x + y = c on the page (y downward)
        for c in around(xc + yc, x0 + y0 + 1e-9, x1 + y1 - 1e-9, d):
            xa, xb = max(x0, c - y1), min(x1, c - y0)
            if xb - xa > 1e-6:
                lines.append(((xa, c - xa), (xb, c - xb)))
    if pattern in ("\\", "x", "*"):               # falling to the right: x - y = c
        for c in around(xc - yc, x0 - y1 + 1e-9, x1 - y0 - 1e-9, d):
            xa, xb = max(x0, c + y0), min(x1, c + y1)
            if xb - xa > 1e-6:
                lines.append(((xa, xa - c), (xb, xb - c)))
    if pattern in (".", "o"):
        r = pattern_min_mm(pattern) / 2
        st = step if pattern == "." else 1.25 * step
        for j, y in enumerate(around(yc, y0 + r - 1e-9, y1 - r + 1e-9, st)):
            xs = around(xc, x0 + r - 1e-9, x1 - r + 1e-9, st, half=bool(j % 2))
            if j % 2 and not xs:                  # too narrow for a shifted mark: the even row's places
                xs = around(xc, x0 + r - 1e-9, x1 - r + 1e-9, st)
            (dots if pattern == "." else rings).extend((x, y) for x in xs)
    if pattern == "z":                            # rows ZIG_ROW_MM apart, arms ZIG_HALF_MM wide, ZIG_AMP_MM high
        a, h = ZIG_AMP_MM / 2, ZIG_HALF_MM
        pad = LINE_MIN_PT * MM_PER_PT / 2         # a vertex's line stays inside the box
        for y in around(yc, y0 + a + pad - 1e-9, y1 - a - pad + 1e-9, ZIG_ROW_MM):
            ks = [k for k in range(-int((x1 - x0) / h) - 2, int((x1 - x0) / h) + 3)
                  if x0 + pad - 1e-9 <= xc + k * h <= x1 - pad + 1e-9]
            if len(ks) >= 3:                      # at least two whole arms
                lines.append(tuple((xc + k * h, y - a if k % 2 == 0 else y + a) for k in ks))
    return lines, dots, rings


def pattern_min_mm(pattern):
    """The narrowest box (mm) that holds one whole mark of the pattern: a dot or a ring with its line, or, for a
    line pattern, a line with as much colour as the line's own width on either side of it."""
    if pattern == ".":
        return DOT_PATTERN_MM
    if pattern == "o":
        return RING_PATTERN_MM + LINE_MIN_PT * MM_PER_PT
    if pattern == "z":                            # one V: two whole arms, the line's width inside either edge
        return 2 * ZIG_HALF_MM + LINE_MIN_PT * MM_PER_PT
    return 3 * LINE_MIN_PT * MM_PER_PT if pattern else 0.0


DOT_PATTERN_MM, RING_PATTERN_MM = 0.40, 0.55      # panel d's "." dots and "o" rings (diameters)
# panel d's "z" zigzag: arms ZIG_HALF_MM wide rising and falling ZIG_AMP_MM (about 32 degrees, shallower than the
# diagonals' 45, so an arm does not read as "/" or "\"), rows ZIG_ROW_MM apart (sparser than the straight lines'
# HATCH_MM, so the zigzags stay apart)
ZIG_HALF_MM, ZIG_AMP_MM, ZIG_ROW_MM = 0.5, 0.32, 1.0
assert set(KIND_PATTERN) == {k for k, _ in FIG_KINDS} and len(set(KIND_PATTERN.values())) == len(KIND_PATTERN)


def draw_figure(fn, paths, mutate=None):
    """The plate: one page, [page] width_double_mm wide and at most [page] height_max_mm high (FIGURE_LOCK.toml), every
    text at [type] font_min_pt, every text whole on the page. Nothing on it but the figure (E5): no stamp, no
    provenance, no caption. Two layouts, both read a, b in the first row and c, d in the second; a's colour bar stands
    upright at a's right. With up to 7 columns in a ("a and b, c and d"): b has its own strategy labels and d's key lies
    under d. With more ("b on a's rows, c and d"): b reads a's strategy rows and labels, d's key runs across the page
    below. Rows are as tall as the data need (b's and c's largest tie groups held at their pitch) and shrink, rows of d
    and a first, only when the page would pass the height bound. Every number printed
    on the plate is a text with an id (s448num_<k>) that printed names: the Source Data sheet, row and format it comes
    from (S448 R8 (6) checks them against the workbook; a heatmap value also names the mesh cell it must sit in, a "n ="
    label of d the bar whose row it must sit on). Returns the page size, the printed map and what was drawn, read back
    from the artists (positions in mm from the page's top left, each through the artist's own transform), for
    check_drawn(). mutate (selftest only) alters the drawing once: "b_shift" moves the first dot of b 0.5 points along
    the axis, "c_shift" the first grey dot of c, "c_on_bar" draws c's grey dots on the bar's line, "b_crowd" sets b's
    tied dots 0.4 mm apart with no count, "b_offset" keeps the first dot of b at its datum but offsets its transform 1
    mm along the value axis, "c_wrong_band" draws the first setting's grey dots one band down (in the next setting's
    band), "c_clipped" above the axes (lifted by their bar's height)."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import colormaps
    from matplotlib.font_manager import FontProperties
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath
    from matplotlib.transforms import blended_transform_factory
    import numpy as np

    lw_axis = max(0.5, LINE_MIN_PT)
    plt.rcParams.update({"font.family": FONT, "font.size": PT_TEXT, "svg.fonttype": "none", "pdf.fonttype": 42,
                         "axes.linewidth": lw_axis, "xtick.major.width": lw_axis, "ytick.major.width": lw_axis,
                         "xtick.major.size": 2, "ytick.major.size": 2, "xtick.labelsize": PT_TEXT,
                         "ytick.labelsize": PT_TEXT, "axes.labelsize": PT_AXIS, "legend.fontsize": PT_TEXT,
                         "axes.edgecolor": "#000000", "xtick.color": "#000000", "ytick.color": "#000000",
                         "text.color": "#000000", "axes.labelcolor": "#000000", "svg.hashsalt": "S447"})
    cmap = colormaps[CMAP_NAME]
    W = FIG_W_MM
    a_cols, nS = fn["a_cols"], len(STRATEGIES)
    side = len(a_cols) <= 7
    t2p = TextToPath()

    def tw(s, bold=False):
        """The width in mm of s at PT_TEXT in FONT (its widest line), as matplotlib measures it."""
        fp = FontProperties(family=FONT, size=PT_TEXT, weight="bold" if bold else "normal")
        return max(t2p.get_text_width_height_descent(x, fp, ismath=False)[0] for x in str(s).split("\n")) * MM_PER_PT

    def wrap(s, width):
        """s broken at spaces into lines no wider than width mm where a word allows; a text that takes two lines is
        broken at the space that makes its longer line shortest, so no word is left alone on a line."""
        out = []
        for w in s.split(" "):
            if out and tw(out[-1] + " " + w) <= width:
                out[-1] += " " + w
            else:
                out.append(w)
        if len(out) == 2:
            ws = s.split(" ")
            out = list(min(((" ".join(ws[:i]), " ".join(ws[i:])) for i in range(1, len(ws))),
                           key=lambda p: max(tw(p[0]), tw(p[1]))))
        return "\n".join(out)

    # ---- measures (mm). LINE: one line of text; XAX(k): an x axis's ticks, tick labels and a k-line axis label;
    # HEAD: a panel letter's baseline above its axes, HEAD_TOP: the row's top above that baseline
    M, LINE = 1.5, PT_TEXT * MM_PER_PT * 1.2
    PAD = 2 * MM_PER_PT                           # tick pad and label pad (2 pt)

    def XAX(k):
        return 2 * MM_PER_PT + PAD + LINE + PAD + k * LINE
    EM_HEAD = PT_LETTER * MM_PER_PT               # the letter's type size in mm: the band grows with the type
    HEAD_TOP, HEAD = 0.85 * EM_HEAD, 1.2 * EM_HEAD
    LA = max(tw(lab) for _, lab in STRATEGIES) + PAD + 0.5          # a's (and b's) strategy labels
    col_lab = {v: short_variant(v) for v in a_cols}
    COL_ROT = 45.0                                # a's column labels, one line each, turned 45 degrees
    band_a = (max(tw(x) for x in col_lab.values()) * math.sin(math.radians(COL_ROT))
              + LINE * math.cos(math.radians(COL_ROT)) + PAD + 0.5)
    LD = max(tw(r["row_label"]) for r in fn["d"]) + PAD + 0.5
    n_w = 1.5 + max([tw(HALF_UP.format("n = {attempts_n}", **r)) for r in fn["d"] if r["failed_share_pct"] is not None]
                    + [0.0])
    LCM = max([tw(cm["model"]) for cm in fn["c_models"]] +
              [tw(f"n = {cm['operations_n']} operations") for cm in fn["c_models"]] + [0.0]) + 1.5
    LCS = max([tw(st) for cm in fn["c_models"] for st in cm["settings"]] + [0.0]) + PAD + 2.5   # 2.5 mm of white
    # between a setting's label and the model's
    c_rows, y = [], 0.0                           # c: one bar per model and setting, a gap of 0.4 row between models
    for cm in fn["c_models"]:
        for st in cm["settings"]:
            y += 1
            c_rows.append((cm["model"], st, y))
        y += 0.4
    c_span = (c_rows[-1][2] if c_rows else 1.0) + 0.45
    nD = len(fn["d"])
    b_xlabel = "gain over free-form (percentage points)"
    c_leg_txt = ("mean over operations, 95% interval", "one strategy")
    b_leg_txt = (f"one model and setting ({len(a_cols)})", "median")

    def leg_w(texts, handle_em, cols_em):
        """A one-row legend's width in mm (handle, handle pad 0.8 em, text, column spacing)."""
        em = PT_TEXT * MM_PER_PT
        return sum(handle_em * em + 0.8 * em + tw(t) for t in texts) + cols_em * em * (len(texts) - 1)

    shown_kinds = [(k, col) for k, col in FIG_KINDS if any(r[f"count: {k}"] for r in fn["d"]
                                                          if r["failed_share_pct"] is not None)]
    SW, SH, SGAP, KGAP = 4.0, 2.6, 1.0, 2.5       # key: swatch width and height, swatch to text, between columns

    def key_layout(width, ncol_max):
        """d's key in width mm: the fewest rows, column by column in FIG_KINDS order, a label broken over lines where
        its column is too narrow. Returns (columns, entries [(kind, colour, text, x, y)], height)."""
        best = None
        for nc in range(min(ncol_max, len(shown_kinds)), 0, -1):
            per = math.ceil(len(shown_kinds) / nc)
            cols = [shown_kinds[i * per:(i + 1) * per] for i in range(nc)]
            cols = [c for c in cols if c]
            txt_w = [max(tw(k) for k, _ in c) for c in cols]
            avail = width - sum(SW + SGAP for _ in cols) - KGAP * (len(cols) - 1)
            if avail <= 0:
                continue
            # columns as wide as their text; when they do not fit, the widest is narrowed first (its labels broken
            # at spaces), down to the next widest, and so on
            col_w = list(txt_w)
            while sum(col_w) > avail + 1e-9:
                order = sorted(range(len(col_w)), key=lambda i: -col_w[i])
                top, nxt = order[0], (col_w[order[1]] if len(order) > 1 else 0.0)
                col_w[top] = max(nxt, col_w[top] - (sum(col_w) - avail))
                if len(order) > 1 and col_w[top] == nxt and sum(col_w) > avail + 1e-9:
                    excess = sum(col_w) - avail
                    tied = [i for i in range(len(col_w)) if abs(col_w[i] - nxt) < 1e-9]
                    for i in tied:
                        col_w[i] -= excess / len(tied)
            if min(col_w) < 12.0:
                continue
            # the entries on a grid: an entry broken over two lines makes its whole key row taller, so the rows of
            # every column stay level with each other
            txt = [[k if tw(k) <= cw_ + 1e-6 else wrap(k, cw_) for k, _ in c] for c, cw_ in zip(cols, col_w)]
            row_h = [max(LINE * (tc[i].count("\n") + 1) for tc in txt if i < len(tc)) + 0.4 for i in range(per)]
            row_y = [sum(row_h[:i]) for i in range(per)]
            ents, x, h = [], 0.0, 0.0
            for c, tc, cw_ in zip(cols, txt, col_w):
                for i, ((k, col), t) in enumerate(zip(c, tc)):
                    ents.append((k, col, t, x, row_y[i]))
                h = max(h, row_y[len(c) - 1] + row_h[len(c) - 1])
                x += SW + SGAP + cw_ + KGAP
            if best is None or h < best[2] - 1e-6:
                best = (len(cols), ents, h)
        return best

    kb = max([n for n in Counter((r["strategy"], r["gain_pct_points"]) for r in fn["b"]
                                 if r["row"] == "variant (dot)").values()] + [1])
    kc = max([n for n in Counter((r["variant"], r["pass_rate_pct"]) for r in fn["c"]
                                 if r["row"] == "strategy (grey dot)").values()] + [1])
    need_b = math.ceil(((kb - 1) * B_PITCH_MM + B_DOT_MM + 0.2) * 10 - 1e-9) / 10
    need_c = math.ceil(((kc - 1) * C_PITCH_MM + C_CLEAR_MM + C_TOP_CLEAR_MM + 0.05) * 10 - 1e-9) / 10

    def geometry(R):
        """Every box of the plate in mm for row heights R (a, b, c, d), and the page height."""
        g = {}
        g["a_x"] = M + LA
        cb_w = 1.5 + 2.0 + 2 * MM_PER_PT + PAD + tw("100") + PAD + LINE      # a's edge to the colour bar's label
        if side:
            cw = 7.0
        else:
            # columns of a narrower than 5.8 mm (never narrower than a printed "100" with 0.2 mm on either side) where
            # b's block, beside a, would be narrower than 45 mm
            b_need = 45.0
            cw = max(min(5.8, (W - M - b_need - 2.0 - cb_w - g["a_x"]) / len(a_cols)), tw("100") + 0.4)
        g["a_w"] = len(a_cols) * cw
        g["a_h"], g["b_h"] = nS * (R["a"] if side else R["b"]), nS * R["b"]   # side by side, a reads b's rows
        # a's colour bar, upright at a's right, so it is read with a, never with b
        cb_x, cb_end = g["a_x"] + g["a_w"] + 1.5, g["a_x"] + g["a_w"] + cb_w
        if side:
            # row 1: a, then b with its own strategy labels; row 2: c, then d with d's key under d. Read a, b, c, d
            g["b_blk"] = cb_end + 3.0
            g["b_x"], g["b_lab"] = g["b_blk"] + LA, True
            g["b_w"] = W - M - 1.0 - g["b_x"]
        else:
            # row 1: a, then b on a's strategy rows; row 2: c, then d; d's key across the page below
            g["b_blk"] = g["b_x"] = cb_end + 2.0
            g["b_lab"] = False
            g["b_w"] = W - M - 2.0 - g["b_x"]
        g["a_top"] = g["b_top"] = HEAD_TOP + HEAD
        g["cb"] = (cb_x, g["a_top"], 2.0, g["a_h"])
        g["b_xl"] = 1 if tw(b_xlabel) <= g["b_w"] else 2
        g["b_leg_x"], g["b_leg_room"] = g["b_blk"], W - M - g["b_blk"]
        g["b_leg_cols"] = 2 if leg_w(b_leg_txt, 1.2, 1.2) <= g["b_leg_room"] else 1
        b_end = g["b_top"] + g["b_h"] + XAX(g["b_xl"]) + 0.6 + (3 - g["b_leg_cols"]) * LINE
        row1 = max(g["a_top"] + g["a_h"] + band_a, b_end)
        r2 = row1 + 1.5
        g["c_top"] = g["d_top"] = r2 + HEAD_TOP + HEAD
        g["c_blk"] = M
        g["c_x"] = M + LCM + LCS
        g["c_h"], g["d_h"] = c_span * R["c"], nD * R["d"]
        if side:
            # what c's and d's axes share of the row: c 45%, d (whose narrow segments carry patterns) 55%
            room = W - M - n_w - g["c_x"] - 5.0 - LD
            g["c_w"] = 0.45 * room
            g["d_lab_x"] = g["c_x"] + g["c_w"] + 5.0
        else:
            g["c_w"] = 40.0
            g["d_lab_x"] = g["c_x"] + g["c_w"] + 1.0 + 4.0
        g["d_x"] = g["d_lab_x"] + LD
        g["d_w"] = W - M - n_w - g["d_x"]
        g["c_leg_cols"] = 2 if leg_w(c_leg_txt, 1.6, 1.0) <= g["d_lab_x"] - 2.0 - M else 1
        c_end = g["c_top"] + g["c_h"] + XAX(1) + 0.6 + (3 - g["c_leg_cols"]) * LINE
        d_end = g["d_top"] + g["d_h"] + XAX(1)
        if side:
            g["key_x"], g["key_y"] = g["d_lab_x"], d_end + 1.0
            g["key"] = key_layout(W - M - g["key_x"], 2)
            g["H"] = max(c_end, g["key_y"] + g["key"][2]) + 1.0
        else:
            g["key_x"], g["key_y"] = M, max(c_end, d_end) + 1.0
            g["key"] = key_layout(W - 2 * M, 3)
            g["H"] = g["key_y"] + g["key"][2] + 1.0
        g["H"] = math.ceil(g["H"] * 10) / 10
        return g

    # rows: a's and d's text rows at 4.6 mm (4.0 mm in the layout for more than 7 variants); c's as tall as its
    # largest tie group needs; b's too with up to 7 variants (so at most 7 ties), else 4.0 mm with counts beside a
    # group the row cannot hold.
    # Over the height bound (less H_ROOM_MM), rows shrink 0.1 mm at a time, in the order d, a, c, b (d, b, c in the
    # layout for more than 7 variants; to 3.8 mm, c and b to 4.0 mm in the layout for up to 7), each time the first
    # of them whose shrinking lowers the page (a row beside a taller one is left as it is), else the first not yet at
    # its floor; a tie group drawn closer has its count printed
    R = {"a": 4.6 if side else 4.0, "d": 4.6 if side else 4.0, "b": max(4.6, need_b) if side else 4.0,
         "c": max(4.6 if side else 4.0, need_c)}
    floor = {"d": 3.8, "a": 3.8, "c": 4.0 if side else 3.8, "b": 4.0 if side else 3.8}
    order = ("d", "a", "c", "b") if side else ("d", "b", "c")   # side by side, a's rows are b's, and b's 4.0 mm rows
    #                                                             already print counts
    g = geometry(R)
    while g["H"] > FIG_H_MAX_MM - H_ROOM_MM:
        free = [k for k in order if R[k] - 0.1 >= floor[k] - 1e-9]
        if not free:
            raise SystemExit(f"Figure {FIG_N} does not fit {W:g} x {FIG_H_MAX_MM:g} mm at {PT_TEXT:g} pt even with every row "
                             f"at its floor ({g['H']} mm high)")
        k = next((k for k in free if geometry({**R, k: round(R[k] - 0.1, 1)})["H"] < g["H"] - 1e-9), free[0])
        R[k] = round(R[k] - 0.1, 1)
        g = geometry(R)
    if not side:
        R["a"] = R["b"]
    H = g["H"]
    if g["d_w"] < 20 or g["b_w"] < 25:
        raise SystemExit(f"Figure {FIG_N}: d ({g['d_w']:.1f} mm) or b ({g['b_w']:.1f} mm) too narrow at {W:g} mm")
    ROW, ROW_C, ROW_D = R["b"], R["c"], R["d"]
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    printed = {}

    def num(artist, entry):
        """Tie a printed number to its Source Data cell: the artist's SVG group gets an id S448 looks up."""
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    def row_index(sheet, **where):
        rows = fn[sheet]
        return next(i for i, r in enumerate(rows) if all(r[k] == v for k, v in where.items()))

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])

    def text_mm(x, y, s, **kw):
        return fig.text(x / W, 1 - y / H, s, **kw)

    def head(x, y, letter):
        """The panel letter on baseline y. No panel title: the journal's "Do not include titles or captions within
        your illustrations" ([files] titles_in_figure), applied to panel titles by Valerio (Q2, 17 October); the
        legend defines each panel."""
        text_mm(x, y, LETTER_CASE(letter), fontsize=PT_LETTER, fontweight=LETTER_WEIGHT, va="baseline", ha="left")

    def mm_data(ax_, pts):
        """Page positions in mm (y downward) as data coordinates of ax_ (its axes box and limits already set)."""
        p = np.asarray(pts, dtype=float).reshape(-1, 2)
        disp = np.column_stack([p[:, 0] / 25.4 * fig.dpi, (H - p[:, 1]) / 25.4 * fig.dpi])
        return ax_.transData.inverted().transform(disp)

    def data_mm(ax_, pts):
        p = ax_.transData.transform(np.asarray(pts, dtype=float).reshape(-1, 2))
        return np.column_stack([p[:, 0] / fig.dpi * 25.4, H - p[:, 1] / fig.dpi * 25.4])

    def draw_pattern(ax_, rect_mm, pattern, fill, z):
        """KIND_PATTERN's pattern inside a box given in page mm, drawn in ax_'s data coordinates, in black or white
        lines of [lines] line_min_pt (whichever stands out more from fill)."""
        ink = ink_on(fill)
        lines, dots, rings = pattern_marks(rect_mm, pattern)
        for pts in lines:                          # one path per line, so the PDF and the SVG hold the same paths
            arr = mm_data(ax_, list(pts))
            ax_.plot(arr[:, 0], arr[:, 1], color=ink, lw=LINE_MIN_PT, solid_capstyle="butt",
                     solid_joinstyle="miter", zorder=z)
        for pts, filled, dmm in ((dots, True, DOT_PATTERN_MM), (rings, False, RING_PATTERN_MM)):
            if pts:
                arr = mm_data(ax_, pts)
                ax_.plot(arr[:, 0], arr[:, 1], ls="", marker="o", ms=ms_pt(dmm), mfc=ink if filled else "none",
                         mec="none" if filled else ink, mew=0 if filled else LINE_MIN_PT, zorder=z)

    # ---- a: model x strategy heatmap
    a_top, a_x, a_w, a_h = g["a_top"], g["a_x"], g["a_w"], g["a_h"]
    head(M, a_top - HEAD, "a")
    ax = axes_mm(a_x, a_top, a_w, a_h)
    rate = {(r["strategy"], r["variant"]): r["pass_rate_pct"] for r in fn["a"]}
    Z = np.array([[rate[(s, v)] for v in a_cols] for s, _ in STRATEGIES])
    mesh = ax.pcolormesh(np.arange(len(a_cols) + 1), np.arange(nS + 1), Z, cmap=cmap, vmin=0, vmax=100,
                         edgecolors="#FFFFFF", linewidth=max(0.6, LINE_MIN_PT))
    # the mesh's SVG group holds one path per cell, row by row (Z's order: strategy i, column j), so path
    # i * len(a_cols) + j is the cell of (strategy i, variant j); S448 R8 (6) checks each value's text sits inside it
    mesh.set_gid("s448cells_a")
    for i, (s, _) in enumerate(STRATEGIES):
        for j, v in enumerate(a_cols):
            z = Z[i, j]
            ri = row_index("a", strategy=s, variant=v)
            entry = {"sheet": sheet_name("a"), "row": ri, "format": "{pass_rate_pct:.0f}",
                     "inside": {"gid": "s448cells_a", "path": i * len(a_cols) + j}}
            t = ax.text(j + 0.5, i + 0.5, HALF_UP.format(entry["format"], **fn["a"][ri]), ha="center", va="center",
                        fontsize=PT_TEXT, color=ink_on(cmap(z / 100)))
            num(t, entry)
    ax.set_xlim(0, len(a_cols))
    ax.set_ylim(nS, 0)
    ax.set_yticks(np.arange(nS) + 0.5, [lab for _, lab in STRATEGIES])
    # column labels: one line each (a one-line text keeps its font features: no ligatures, below), at 45 degrees,
    # ending under their column
    ax.set_xticks(np.arange(len(a_cols)) + 0.5, [col_lab[v] for v in a_cols], rotation=COL_ROT, ha="right",
                  va="center", rotation_mode="anchor")
    ax.tick_params(length=0, pad=2)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cx_, cy_, cw_, ch_ = g["cb"]
    cax = axes_mm(cx_, cy_, cw_, ch_)
    cb = fig.colorbar(mesh, cax=cax, ticks=[0, 25, 50, 75, 100], orientation="vertical")
    cb.solids.set_rasterized(False)               # matplotlib rasterises a colorbar of 50+ levels; vector here
    cb.outline.set_linewidth(max(0.4, LINE_MIN_PT))
    cb.ax.tick_params(length=1.5, pad=1.5, width=lw_axis)
    cb.set_label("pass rate (%)", fontsize=PT_AXIS, labelpad=2)

    # ---- b: each strategy's gain over free-form, one dot per variant, median line drawn over the dots (E2); in the
    # side layout its own row labels, in the other the rows of a beside it
    b_top, b_x, b_w, b_h = g["b_top"], g["b_x"], g["b_w"], g["b_h"]
    head(g["b_blk"], b_top - HEAD, "b")
    axb = ax = axes_mm(b_x, b_top, b_w, b_h)
    gains_all = [r["gain_pct_points"] for r in fn["b"] if r["row"] == "variant (dot)"]
    lo = 10 * math.floor(min(gains_all + [0]) / 10) - 5
    hi = 10 * math.ceil(max(gains_all + [0]) / 10) + 5
    b_half = ROW / 2 - B_DOT_MM / 2 - 0.1         # centres stay this close to the row's middle: edges inside the row
    b_dots, b_meds, b_labels = [], [], []
    for i, (s, _) in enumerate(STRATEGIES):
        if s == "free_form":
            ax.text(1.0, i + 0.5, "reference", va="center", ha="left", fontsize=PT_TEXT, color=GREY_NOTE)
            continue
        rows = [r for r in fn["b"] if r["strategy"] == s and r["row"] == "variant (dot)"]
        g_ = [r["gain_pct_points"] for r in rows]
        med = next(r["gain_pct_points"] for r in fn["b"] if r["strategy"] == s and r["row"] != "variant (dot)")
        offs, over = tie_offsets(g_, b_half, B_PITCH_MM if mutate != "b_crowd" else 0.4)
        if mutate == "b_crowd":
            over = {}
        for n_, (r, x, dy) in enumerate(zip(rows, g_, offs)):
            xd = x + (0.5 if mutate == "b_shift" and not b_dots else 0)
            art, = ax.plot(xd, i + 0.5 + dy / ROW, "o", ms=ms_pt(B_DOT_MM), mfc=OKABE["blue"], mec="none", zorder=5)
            if mutate == "b_offset" and not b_dots:
                # its datum kept, its transform offset 1 mm along the value axis: the dot lands off its value
                from matplotlib.transforms import Affine2D
                art.set_transform(ax.transData + Affine2D().translate(fig.dpi / 25.4, 0))
            b_dots.append({"artist": art, "row": i, "strategy": s, "variant": r["variant"], "ax": ax})
        for x, k in over.items():
            b_labels.append({"value": x, "count": k, "row": i, "strategy": s, "ax": ax,
                             "entry": {"sheet": sheet_name("b"), "where": {"strategy": s, "row": "variant (dot)",
                                                                       "gain_pct_points": x}, "format": "{count}"}})
        art, = ax.plot([med, med], [i + 0.04, i + 0.96], color="#000000", lw=max(0.8, LINE_MIN_PT),
                       solid_capstyle="butt", zorder=6)
        b_meds.append({"artist": art, "row": i, "ax": ax})
    ax.axvline(0, color=OKABE_GREY, lw=max(0.6, LINE_MIN_PT), zorder=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(nS, 0)
    ax.set_yticks(np.arange(nS) + 0.5, [lab for _, lab in STRATEGIES] if g["b_lab"] else [])
    ax.tick_params(axis="y", length=0, pad=2)
    step = 20 if hi - lo > 80 else 10
    ax.set_xticks(range(int(math.ceil(lo / step) * step), int(hi) + 1, step))
    ax.set_xlabel(b_xlabel if g["b_xl"] == 1 else "gain over free-form\n(percentage points)", labelpad=2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    leg = ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=ms_pt(B_DOT_MM), mfc=OKABE["blue"], mec="none",
                                    label=b_leg_txt[0]),
                             Line2D([], [], color="#000000", lw=max(0.8, LINE_MIN_PT), label=b_leg_txt[1])],
                    loc="upper left", bbox_to_anchor=((g["b_leg_x"] - b_x) / b_w,
                                                      -(XAX(g["b_xl"]) + 0.6) / b_h),
                    ncol=g["b_leg_cols"], frameon=False, fontsize=PT_TEXT, handlelength=1.2, columnspacing=1.2,
                    borderaxespad=0, borderpad=0)
    num(leg.get_texts()[0], {"sheet": sheet_name("a"), "distinct": "variant",
                             "format": "one model and setting ({count})"})

    # ---- c: thinking, within each model: pass rate on matched attempts, 95% interval over resampled operations;
    # one grey dot per strategy with all its operations matched, in the band above its setting's bar (E2, E7)
    c_top, c_x, c_w, c_h = g["c_top"], g["c_x"], g["c_w"], g["c_h"]
    head(g["c_blk"], c_top - HEAD, "c")
    axc = ax = axes_mm(c_x, c_top, c_w, c_h)
    setting_rows = {(r["model"], r["thinking"]): r for r in fn["c"] if r["row"].startswith("setting")}
    c_half = (ROW_C - C_CLEAR_MM - C_TOP_CLEAR_MM) / 2   # a group spans at most 2 * c_half: C_CLEAR_MM above its
    #                                              own bar, C_TOP_CLEAR_MM below the bar above
    c_dots, c_marks, c_bars, c_labels = [], [], [], []
    for cm in fn["c_models"]:
        ys = []
        for model, st, y in c_rows:
            if model != cm["model"]:
                continue
            r = setting_rows[(model, st)]
            drows = [d for d in fn["c"] if d["variant"] == r["variant"] and d["row"].startswith("strategy")]
            dots = [d["pass_rate_pct"] for d in drows]
            offs, over = tie_offsets(dots, c_half, C_PITCH_MM)
            # each group stacked upward from its own bar: its nearest dot C_CLEAR_MM above the bar, so a dot is read
            # with the setting below it, never midway between two bars
            lowest = {}
            for x, dy in zip(dots, offs):
                lowest[x] = max(lowest.get(x, -1e9), dy)
            offs = [dy - lowest[x] - C_CLEAR_MM for x, dy in zip(dots, offs)]
            centre = 0.0
            if mutate == "c_on_bar":
                offs = [dy + C_CLEAR_MM for dy in offs]
            if mutate in ("c_wrong_band", "c_clipped") and not c_dots:
                # the first setting with grey dots: its dots one band down (into the next setting's band), or lifted
                # by the height of their bar above the axes' top, so they sit above the axes as far as they sat above
                # the bar (outside the axes, clipped)
                offs = [dy + (ROW_C if mutate == "c_wrong_band" else -y * ROW_C) for dy in offs]
            for d, x, dy in zip(drows, dots, offs):
                xd = x + (0.5 if mutate == "c_shift" and not c_dots else 0)
                art, = ax.plot(xd, y + centre + dy / ROW_C, "o", ms=ms_pt(C_DOT_MM), mfc=C_DOT_GREY, mec="none",
                               zorder=4)
                c_dots.append({"artist": art, "variant": r["variant"], "strategy": d["strategy"], "bar_y": y,
                               "ax": ax})
            for x, k in over.items():
                mid = sum(dy for xx, dy in zip(dots, offs) if xx == x) / k / ROW_C
                c_labels.append({"value": x, "count": k, "bar_y": y, "centre": mid, "ax": ax,
                                 "entry": {"sheet": sheet_name("c"), "where": {"variant": r["variant"],
                                                                           "row": "strategy (grey dot)",
                                                                           "pass_rate_pct": x}, "format": "{count}"}})
            bar, = ax.plot([r["boot95_lo_pct"], r["boot95_hi_pct"]], [y, y], color=OKABE["blue"],
                           lw=max(C_BAR_PT, LINE_MIN_PT),
                           zorder=2, solid_capstyle="butt")
            mk, = ax.plot(r["pass_rate_pct"], y, "o", ms=C_MARK_PT, mfc=OKABE["blue"], mec="#FFFFFF",
                          mew=max(0.4, LINE_MIN_PT),
                          zorder=3)
            c_bars.append({"artist": bar, "y": y, "variant": r["variant"], "ax": ax})
            c_marks.append({"artist": mk, "y": y, "variant": r["variant"], "ax": ax})
            ys.append(y)
        # the model and its n, two one-line texts (one line above the other, centred on the model's bars), each
        # tied to its Source Data row
        ri = row_index("c", model=cm["model"], row="setting (point and interval)")
        for fmt_, dy_ in (("{model}", -0.5), ("n = {operations_n} operations", 0.5)):
            t = ax.text(-LCS / c_w, (ys[0] + ys[-1]) / 2 + dy_ * PT_TEXT * MM_PER_PT * 1.25 / ROW_C,
                        HALF_UP.format(fmt_, **fn["c"][ri]),
                        transform=blended_transform_factory(ax.transAxes, ax.transData), ha="right", va="center",
                        fontsize=PT_TEXT)
            num(t, {"sheet": sheet_name("c"), "row": ri, "format": fmt_})
    ax.set_yticks([y for _, _, y in c_rows], [st for _, st, _ in c_rows])
    ax.set_ylim(c_span, 0)
    ax.tick_params(axis="y", length=0, pad=2)
    ax.set_xlim(-3, 103)                          # a dot or marker at 0 or 100 is drawn whole, never clipped
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("pass rate (%)", labelpad=2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    leg = ax.legend(handles=[Line2D([], [], color=OKABE["blue"], lw=max(C_BAR_PT, LINE_MIN_PT), marker="o",
                                    ms=C_MARK_PT, mec="#FFFFFF", mew=max(0.4, LINE_MIN_PT), label=c_leg_txt[0]),
                             Line2D([], [], ls="", marker="o", ms=ms_pt(C_DOT_MM), mfc=C_DOT_GREY, mec="none",
                                    label=c_leg_txt[1])],
                    loc="upper left", bbox_to_anchor=(-(c_x - g["c_blk"]) / c_w, -(XAX(1) + 0.6) / c_h),
                    ncol=g["c_leg_cols"], frameon=False, fontsize=PT_TEXT, handlelength=1.6, columnspacing=1.0,
                    borderaxespad=0, borderpad=0)
    num(leg.get_texts()[0], {"fixed": "mean over operations, 95% interval",
                             "why": "the interval's level, a constant of the method (no Source Data cell)"})

    # ---- d: share of the attempts stored that failed, by kind, per model and setting: Okabe-Ito colours, each kind
    # also with its own fill pattern (KIND_PATTERN), in the bars and in the key
    d_top, d_x, d_w, d_h = g["d_top"], g["d_x"], g["d_w"], g["d_h"]
    head(g["d_lab_x"], d_top - HEAD, "d")
    ax = axes_mm(d_x, d_top, d_w, d_h)
    shares = [r["failed_share_pct"] for r in fn["d"] if r["failed_share_pct"] is not None]
    xmax = max(20, 10 * math.ceil(max(shares + [0]) / 10))
    ax.set_ylim(nD - 0.5, -0.5)
    ax.set_xlim(0, xmax)
    inset = LINE_MIN_PT * MM_PER_PT               # patterns stop short of the white edge between segments
    for i, r in enumerate(fn["d"]):
        if r["failed_share_pct"] is None:
            t = ax.text(0.5, i, f"too few attempts (n = {r['attempts_n']})", va="center", ha="left",
                        fontsize=PT_TEXT, color=GREY_FEW)
            num(t, {"sheet": sheet_name("d"), "row": i, "format": "too few attempts (n = {attempts_n})"})
            continue
        left, bar_gid = 0.0, None
        for kk, (k, col) in enumerate(FIG_KINDS):
            v = r[f"share %: {k}"]
            if v:
                seg = ax.barh(i, v, left=left, color=col, height=0.72, edgecolor="#FFFFFF", linewidth=LINE_MIN_PT)
                seg.patches[0].set_gid(f"s448bar_d_{i}_{kk}")
                bar_gid = bar_gid or f"s448bar_d_{i}_{kk}"
                (x0m, y0m), (x1m, y1m) = data_mm(ax, [(left, i - 0.36), (left + v, i + 0.36)])
                draw_pattern(ax, (min(x0m, x1m) + inset, min(y0m, y1m) + inset, max(x0m, x1m) - inset,
                                  max(y0m, y1m) - inset), KIND_PATTERN[k], col, z=3)
            left += v
        t = ax.text(1.0 + 1.5 / d_w, 1 - (i + 0.5) / nD, HALF_UP.format("n = {attempts_n}", **r),
                    transform=ax.transAxes, va="center", ha="left", fontsize=PT_TEXT)
        num(t, {"sheet": sheet_name("d"), "row": i, "format": "n = {attempts_n}",
                **({"on_row": {"gid": bar_gid}} if bar_gid else {})})
    ax.set_yticks(range(nD), [r["row_label"] for r in fn["d"]])
    for lab, r in zip(ax.get_yticklabels(), fn["d"]):
        if r["failed_share_pct"] is None:
            lab.set_color(GREY_FEW)
    ax.set_xticks(range(0, xmax + 1, 20 if xmax > 60 else 10))
    ax.set_xlabel("attempts failed (% of n)", labelpad=2)
    ax.tick_params(axis="y", length=0, pad=2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    # the key: each kind's colour and pattern, as drawn in the bars
    ncol_k, ents, kh = g["key"]
    kax = axes_mm(g["key_x"], g["key_y"], W - M - g["key_x"], kh)
    kax.set_xlim(0, W - M - g["key_x"])
    kax.set_ylim(kh, 0)
    kax.axis("off")
    kax.patch.set_visible(False)
    for k, col, txt, x, yk in ents:
        kax.add_patch(Rectangle((x, yk + 0.35), SW, SH, facecolor=col, edgecolor="none"))
        draw_pattern(kax, (g["key_x"] + x, g["key_y"] + yk + 0.35, g["key_x"] + x + SW, g["key_y"] + yk + 0.35 + SH),
                     KIND_PATTERN[k], col, z=3)
        kax.text(x + SW + SGAP, yk, txt, va="top", ha="left", fontsize=PT_TEXT, linespacing=1.0)

    # ---- count labels for tie groups that overflow their band: right of the group, else left; the gate checks
    # that a label covers no dot, no median line and no other label
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    dpi = fig.dpi

    def to_mm(ax_, x, y):
        """Where a datum of these axes falls on the page (the axes' own data transform): the position a value
        implies."""
        px, py = ax_.transData.transform((x, y))
        return px / dpi * 25.4, H - py / dpi * 25.4

    def art_mm(artist, x, y):
        """Where the artist itself puts its datum on the page: its own transform, composed by matplotlib (the axes'
        data transform unless the artist was given another), so a dot whose transform is offset is read where it
        lands, not where its datum says."""
        px, py = artist.get_transform().transform((x, y))
        return px / dpi * 25.4, H - py / dpi * 25.4

    def ext_mm(artist):
        bb = artist.get_window_extent(renderer)
        return (bb.x0 / dpi * 25.4, H - bb.y1 / dpi * 25.4, bb.x1 / dpi * 25.4, H - bb.y0 / dpi * 25.4)

    def place(lb, y_data, dot_mm, others):
        """The count beside its group, in data coordinates (the vector files are written at 72 dpi): right of the
        group, else left; if both cover something it stays right and check_drawn() fails the plate."""
        ax_ = lb["ax"]
        px0, py0 = ax_.transData.transform((lb["value"], y_data))
        tries = []
        for side_, ha in ((1, "left"), (-1, "right")):
            xd = ax_.transData.inverted().transform((px0 + side_ * (dot_mm / 2 + 0.3) / 25.4 * dpi, py0))[0]
            t = ax_.text(xd, y_data, str(lb["count"]), ha=ha, va="center", fontsize=PT_TEXT, color="#000000",
                         zorder=7)
            num(t, lb["entry"])
            if not any(boxes_hit(ext_mm(t), o) for o in others):
                return t
            del printed[t.get_gid()]
            t.remove()
            tries.append((xd, ha))
        t = ax_.text(tries[0][0], y_data, str(lb["count"]), ha="left", va="center", fontsize=PT_TEXT,
                     color="#000000", zorder=7)
        num(t, lb["entry"])
        return t
    dot_boxes = []
    for d in b_dots:
        xm, ym = art_mm(d["artist"], d["artist"].get_xdata()[0], d["artist"].get_ydata()[0])
        dot_boxes.append((xm - B_DOT_MM / 2, ym - B_DOT_MM / 2, xm + B_DOT_MM / 2, ym + B_DOT_MM / 2))
    for d in c_dots:
        xm, ym = art_mm(d["artist"], d["artist"].get_xdata()[0], d["artist"].get_ydata()[0])
        dot_boxes.append((xm - C_DOT_MM / 2, ym - C_DOT_MM / 2, xm + C_DOT_MM / 2, ym + C_DOT_MM / 2))
    placed = []
    for lb in b_labels:
        lb["artist"] = place(lb, lb["row"] + 0.5, B_DOT_MM, dot_boxes + placed)
        placed.append(ext_mm(lb["artist"]))
    for lb in c_labels:
        lb["artist"] = place(lb, lb["bar_y"] + lb["centre"], C_DOT_MM, dot_boxes + placed)
        placed.append(ext_mm(lb["artist"]))
    fig.canvas.draw()

    # ---- read back what was drawn, from the artists: the datum each holds and where its own transform puts it on
    # the page; and, per panel, where the axes put a value (the value axis is linear: x_mm = x0_mm + value *
    # per_unit_mm), the axes' box, and panel c's bands (a setting's band runs from the bar above it, or the axes' top,
    # down to its own bar)
    def pos(d):
        a = d["artist"]
        x, y = a.get_xdata()[0], a.get_ydata()[0]
        return float(x), art_mm(a, x, y)
    rb = {"b_dots": [], "b_meds": [], "b_rows": [], "c_dots": [], "c_marks": [], "c_bars": [], "labels": [],
          "axes": {}, "c_bands": {}}
    for nm, ax_ in (("b", axb), ("c", axc)):
        x0 = to_mm(ax_, 0, 0)[0]
        rb["axes"][nm] = {"x0_mm": x0, "per_unit_mm": to_mm(ax_, 1, 0)[0] - x0, "box_mm": ext_mm(ax_)}
    prev = 0.0
    for model, st, y in c_rows:
        rb["c_bands"][setting_rows[(model, st)]["variant"]] = {"top_mm": to_mm(axc, 0, prev)[1],
                                                               "bottom_mm": to_mm(axc, 0, y)[1]}
        prev = y
    for d in b_dots:
        x, (xm, ym) = pos(d)
        rb["b_dots"].append({"strategy": d["strategy"], "variant": d["variant"], "row": d["row"], "x": x,
                             "x_mm": xm, "y_mm": ym, "dot_mm": B_DOT_MM, "panel": "b"})
    for i in range(nS):
        rb["b_rows"].append({"row": i, "top_mm": to_mm(axb, 0, i)[1], "bottom_mm": to_mm(axb, 0, i + 1)[1]})
    for d in b_meds:
        xs, ys_ = d["artist"].get_xdata(), d["artist"].get_ydata()
        x0, y0 = art_mm(d["artist"], xs[0], ys_[0])
        _, y1 = art_mm(d["artist"], xs[1], ys_[1])
        rb["b_meds"].append({"row": d["row"], "x_mm": x0, "y0_mm": min(y0, y1), "y1_mm": max(y0, y1),
                             "lw_mm": d["artist"].get_linewidth() * MM_PER_PT})
    for d in c_dots:
        x, (xm, ym) = pos(d)
        rb["c_dots"].append({"variant": d["variant"], "strategy": d["strategy"], "x": x, "x_mm": xm, "y_mm": ym,
                             "dot_mm": C_DOT_MM, "bar_y_mm": to_mm(d["ax"], 0, d["bar_y"])[1], "panel": "c"})
    for d in c_marks:
        x, (xm, ym) = pos(d)
        rb["c_marks"].append({"variant": d["variant"], "x": x, "x_mm": xm, "y_mm": ym,
                              "radius_mm": d["artist"].get_markersize() * MM_PER_PT / 2})
    for d in c_bars:
        xs, ys_ = d["artist"].get_xdata(), d["artist"].get_ydata()
        x0, y0 = art_mm(d["artist"], xs[0], ys_[0])
        x1, _ = art_mm(d["artist"], xs[1], ys_[1])
        rb["c_bars"].append({"variant": d["variant"], "x0_mm": x0, "x1_mm": x1, "y_mm": y0,
                             "half_mm": d["artist"].get_linewidth() * MM_PER_PT / 2})
    for lb, panel in [(x, "b") for x in b_labels] + [(x, "c") for x in c_labels]:
        rb["labels"].append({"panel": panel, "text": lb["artist"].get_text(), "count": lb["count"],
                             "value": lb["value"], "key": lb.get("strategy") or lb["entry"]["where"]["variant"],
                             "box_mm": ext_mm(lb["artist"])})

    # no ligatures: an "fl" (gemini-3-flash, glm-4.7-flash) stays two letters, each where the font's advance puts it,
    # as the SVG's text holds them (S448 R10 pairs the two files character by character)
    from matplotlib.text import Text
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    # every text whole on the page: a panel letter, label or key text the layout pushed past an edge (a lock with larger
    # type or a narrower page) stops the plate instead of being cut off
    fig.canvas.draw()
    off_page = []
    for t_ in fig.findobj(Text):
        if t_.get_visible() and t_.get_text().strip():
            x0_, y0_, x1_, y1_ = ext_mm(t_)
            if x0_ < -0.01 or y0_ < -0.01 or x1_ > W + 0.01 or y1_ > H + 0.01:
                off_page.append(f"{t_.get_text()!r} at x {x0_:.2f} to {x1_:.2f} mm, y {y0_:.2f} to {y1_:.2f} mm")
    if off_page:
        plt.close(fig)
        raise SystemExit(f"Figure {FIG_N}: {len(off_page)} text(s) reach past the {W:g} x {H:g} mm page, e.g. "
                         f"{off_page[:3]}; no plate is drawn")
    meta_pdf ={"Title": FIG_DIR_NAME, "Author": None, "Subject": None, "Keywords": None, "Creator": None,
                "Producer": None, "CreationDate": None, "ModDate": None}
    fig.savefig(paths["pdf"], facecolor="#FFFFFF", metadata=meta_pdf)
    fig.savefig(paths["svg"], facecolor="#FFFFFF", metadata={"Title": FIG_DIR_NAME, "Date": None, "Creator": None})
    plt.close(fig)
    # the raster is the PDF rasterised (MuPDF, 600 dpi, no alpha), so the two cannot differ: S448 R7 rasterises the
    # PDF again and compares pixel by pixel, which a stamp or any edit of the PNG fails
    import fitz
    pix = fitz.open(paths["pdf"])[0].get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    pix.save(paths["png"])
    return W, H, {"layout": "a and b, c and d" if side else "b on a's rows, c and d", "row_mm": ROW,
                  "row_a_mm": R["a"], "row_c_mm": ROW_C, "row_d_mm": ROW_D, "printed": printed, "readback": rb}


def boxes_hit(a, b, pad=0.05):
    """Two boxes (x0, y0, x1, y1) in mm overlap (closer than pad)."""
    return a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def read_sheets(xlsx):
    """The workbook as written: {sheet: [row dicts]} (what the reader of Source Data gets)."""
    from openpyxl import load_workbook
    wb = load_workbook(xlsx, read_only=True)
    out = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        out[ws.title] = [dict(zip(rows[0], r)) for r in rows[1:]]
    return out


def check_drawn(rb, xlsx):
    """The plate's dots against the Source Data workbook, from positions read back from the drawn artists. Returns
    (problems, summary). Checked: (1) every dot of b sits at its variant's gain in sheet Fig. 6b and every grey dot of
    c at its strategy's pass rate in sheet Fig. 6c (the artist's value-axis datum against the workbook cell, 1e-9),
    and every workbook dot is drawn once; (2) a dot of b stays inside its row (its edges); (3) tied dots are countable:
    within a group of equal values on one row, neighbouring centres are at least the dot's diameter plus
    COUNT_GAP_MM apart, or the group has a count label reading its number; (4) no count label overlaps a dot, a median
    line or another label; (5) panel c: no grey dot centre within the mean marker's radius of any marker (F3's gate),
    and none touches a marker or a bar (centre at least marker radius + dot radius from every marker centre, at least
    bar half-width + dot radius from a bar's line where the bar spans the dot); (6) where each mark lands on the page:
    every dot of b, grey dot of c, mean marker of c and end of c's interval bars, placed by the artist's own transform,
    sits within POS_TOL_MM along the value axis of where its axes put the workbook value (the setting rows of sheet
    Fig. 6c for markers and bars), so a mark whose datum is right but whose transform is offset fails; (7) panel c:
    every grey dot lies whole inside its own setting's band (from the bar above it, or the axes' top, down to its own
    bar) and whole inside the axes, so none is clipped; (8) no dot of b or c overlaps a dot of another group (another
    value or another row or setting)."""
    S = read_sheets(xlsx)
    probs = []
    want_b = {(r["strategy"], r["variant"]): r["gain_pct_points"] for r in S[sheet_name("b")]
              if r["row"] == "variant (dot)"}
    want_c = {(r["variant"], r["strategy"]): r["pass_rate_pct"] for r in S[sheet_name("c")]
              if r["row"] == "strategy (grey dot)"}
    got_b = Counter((d["strategy"], d["variant"]) for d in rb["b_dots"])
    got_c = Counter((d["variant"], d["strategy"]) for d in rb["c_dots"])
    if set(got_b) != set(want_b) or max(got_b.values(), default=1) > 1:
        probs.append(f"b: dots drawn {sum(got_b.values())}, workbook dots {len(want_b)}")
    if set(got_c) != set(want_c) or max(got_c.values(), default=1) > 1:
        probs.append(f"c: grey dots drawn {sum(got_c.values())}, workbook rows {len(want_c)}")
    off = [f"b {d['strategy']} {d['variant']}: drawn at {d['x']}, workbook {want_b.get((d['strategy'], d['variant']))}"
           for d in rb["b_dots"] if not abs(d["x"] - want_b.get((d["strategy"], d["variant"]), float("nan"))) <= 1e-9]
    off += [f"c {d['variant']} {d['strategy']}: drawn at {d['x']}, workbook "
            f"{want_c.get((d['variant'], d['strategy']))}" for d in rb["c_dots"]
            if not abs(d["x"] - want_c.get((d["variant"], d["strategy"]), float("nan"))) <= 1e-9]
    if off:
        probs.append(f"{len(off)} dot(s) off their Source Data value, e.g. {off[:2]}")
    # (6) where each mark lands, against where the workbook value puts it
    setting = {r["variant"]: r for r in S[sheet_name("c")] if r["row"].startswith("setting")}
    ax_b, ax_c = rb["axes"]["b"], rb["axes"]["c"]
    at = lambda a, v: a["x0_mm"] + v * a["per_unit_mm"]
    placed_off = []
    for nm, a, ds, want in (("b dot", ax_b, rb["b_dots"], lambda d: want_b.get((d["strategy"], d["variant"]))),
                            ("c grey dot", ax_c, rb["c_dots"], lambda d: want_c.get((d["variant"], d["strategy"]))),
                            ("c marker", ax_c, rb["c_marks"],
                             lambda d: setting.get(d["variant"], {}).get("pass_rate_pct"))):
        for d in ds:
            w = want(d)
            if w is None or abs(d["x_mm"] - at(a, w)) > POS_TOL_MM:
                placed_off.append(f"{nm} {d.get('strategy') or ''} {d['variant']}: on the page at {d['x_mm']:.2f} mm, "
                                  f"the workbook's {w} at {at(a, w) if w is not None else float('nan'):.2f} mm")
    for b in rb["c_bars"]:
        r_ = setting.get(b["variant"], {})
        for end, col in (("x0_mm", "boot95_lo_pct"), ("x1_mm", "boot95_hi_pct")):
            if r_.get(col) is None or abs(b[end] - at(ax_c, r_[col])) > POS_TOL_MM:
                placed_off.append(f"c bar {b['variant']} {col}: on the page at {b[end]:.2f} mm")
    if placed_off:
        probs.append(f"{len(placed_off)} mark(s) placed on the page off where the workbook value puts them (page "
                     f"position from the artist's own transform), e.g. {placed_off[:2]}")
    # (7) panel c: each grey dot whole inside its own setting's band and inside the axes
    out_band, clipped = [], []
    bx0, by0, bx1, by1 = ax_c["box_mm"]
    for d in rb["c_dots"]:
        r, band = d["dot_mm"] / 2, rb["c_bands"].get(d["variant"])
        if band is None or not (band["top_mm"] - 1e-6 <= d["y_mm"] - r and d["y_mm"] + r <= band["bottom_mm"] + 1e-6):
            out_band.append(f"{d['variant']} {d['strategy']}")
        if not (bx0 - 1e-6 <= d["x_mm"] - r and d["x_mm"] + r <= bx1 + 1e-6 and by0 - 1e-6 <= d["y_mm"] - r and
                d["y_mm"] + r <= by1 + 1e-6):
            clipped.append(f"{d['variant']} {d['strategy']}")
    if out_band:
        probs.append(f"{len(out_band)} grey dot(s) of c outside their setting's band, e.g. {out_band[:2]}")
    if clipped:
        probs.append(f"{len(clipped)} grey dot(s) of c outside the axes (clipped), e.g. {clipped[:2]}")
    # (8) no dot overlaps a dot of another group
    overlap = []
    for nm, ds, gk in (("b", rb["b_dots"], lambda d: (d["strategy"], d["x"])),
                       ("c", rb["c_dots"], lambda d: (d["variant"], d["x"]))):
        for i, d in enumerate(ds):
            for e in ds[i + 1:]:
                if gk(d) != gk(e) and math.hypot(d["x_mm"] - e["x_mm"], d["y_mm"] - e["y_mm"]) < \
                        (d["dot_mm"] + e["dot_mm"]) / 2 - 1e-6:
                    overlap.append(f"{nm} {gk(d)} and {gk(e)}")
    if overlap:
        probs.append(f"{len(overlap)} pair(s) of dots of different groups overlap, e.g. {overlap[:2]}")
    rows = {r["row"]: r for r in rb["b_rows"]}
    out_row = [d for d in rb["b_dots"] if not (rows[d["row"]]["top_mm"] <= d["y_mm"] - d["dot_mm"] / 2 - 1e-6 and
                                               d["y_mm"] + d["dot_mm"] / 2 + 1e-6 <= rows[d["row"]]["bottom_mm"])]
    if out_row:
        probs.append(f"{len(out_row)} dot(s) of b reach outside their row")
    # countable ties
    labelled = {(lb["panel"], lb["key"], lb["value"]): lb for lb in rb["labels"]}
    groups = defaultdict(list)
    for d in rb["b_dots"]:
        groups[("b", d["strategy"], d["x"])].append(d)
    for d in rb["c_dots"]:
        groups[("c", d["variant"], d["x"])].append(d)
    crowded, max_tie, n_lab, min_pitch = [], 0, 0, {"b": float("inf"), "c": float("inf")}
    for key, ds in groups.items():
        max_tie = max(max_tie, len(ds))
        if len(ds) < 2:
            continue
        ys = sorted(d["y_mm"] for d in ds)
        pitch = min(b - a for a, b in zip(ys, ys[1:]))
        lb = labelled.get(key)
        if lb is not None and lb["text"] == str(len(ds)):
            n_lab += 1
            continue
        min_pitch[key[0]] = min(min_pitch[key[0]], pitch)
        if pitch < ds[0]["dot_mm"] + COUNT_GAP_MM - 1e-6:
            crowded.append(f"{key[0]} {key[1]} at {key[2]:g}: {len(ds)} dots {pitch:.2f} mm apart, no count")
    if crowded:
        probs.append(f"{len(crowded)} tie group(s) not countable, e.g. {crowded[:2]}")
    bad_lab = [lb for lb in rb["labels"] if (lb["panel"], lb["key"], lb["value"]) not in groups or
               lb["text"] != str(len(groups[(lb["panel"], lb["key"], lb["value"])]))]
    if bad_lab:
        probs.append(f"{len(bad_lab)} count label(s) not equal to their group's size")
    # labels against dots, medians and each other
    dots_all = rb["b_dots"] + rb["c_dots"]
    hits = 0
    for i, lb in enumerate(rb["labels"]):
        own = groups.get((lb["panel"], lb["key"], lb["value"]), [])
        for d in dots_all:
            if any(d is o for o in own):
                continue
            r = d["dot_mm"] / 2
            if boxes_hit(lb["box_mm"], (d["x_mm"] - r, d["y_mm"] - r, d["x_mm"] + r, d["y_mm"] + r)):
                hits += 1
        for m in rb["b_meds"]:
            if boxes_hit(lb["box_mm"], (m["x_mm"] - m["lw_mm"] / 2, m["y0_mm"], m["x_mm"] + m["lw_mm"] / 2,
                                        m["y1_mm"])):
                hits += 1
        hits += sum(boxes_hit(lb["box_mm"], o["box_mm"]) for o in rb["labels"][i + 1:])
    if hits:
        probs.append(f"count labels overlap {hits} dot(s), median line(s) or label(s)")
    # panel c: grey dots clear of every marker and bar
    under, touch, dmin = [], [], float("inf")
    for d in rb["c_dots"]:
        r = d["dot_mm"] / 2
        for m in rb["c_marks"]:
            dist = math.hypot(d["x_mm"] - m["x_mm"], d["y_mm"] - m["y_mm"])
            dmin = min(dmin, dist)
            if dist <= m["radius_mm"]:
                under.append(f"{d['variant']} {d['strategy']} ({dist:.2f} mm from a marker centre)")
            elif dist < m["radius_mm"] + r:
                touch.append(f"{d['variant']} {d['strategy']} touches a marker")
        for b in rb["c_bars"]:
            if b["x0_mm"] - r <= d["x_mm"] <= b["x1_mm"] + r and abs(d["y_mm"] - b["y_mm"]) < b["half_mm"] + r:
                touch.append(f"{d['variant']} {d['strategy']} on a bar")
    if under:
        probs.append(f"{len(under)} grey dot centre(s) of c within a mean marker's radius, e.g. {under[:2]}")
    if touch:
        probs.append(f"{len(touch)} grey dot(s) of c touch a marker or bar, e.g. {touch[:2]}")
    worst_pos = max([abs(d["x_mm"] - at(a, w)) for a, ds, wf in
                     ((ax_b, rb["b_dots"], lambda d: want_b.get((d["strategy"], d["variant"]))),
                      (ax_c, rb["c_dots"], lambda d: want_c.get((d["variant"], d["strategy"]))),
                      (ax_c, rb["c_marks"], lambda d: setting.get(d["variant"], {}).get("pass_rate_pct")))
                     for d in ds for w in [wf(d)] if w is not None]
                    + [abs(b[e] - at(ax_c, setting[b["variant"]][c])) for b in rb["c_bars"] if b["variant"] in setting
                       for e, c in (("x0_mm", "boot95_lo_pct"), ("x1_mm", "boot95_hi_pct"))
                       if setting[b["variant"]][c] is not None], default=0.0)
    pitch_txt = {p: "no unlabelled tie" if x == float("inf") else f"{x:.2f} mm" for p, x in min_pitch.items()}
    summary = (f"b {len(rb['b_dots'])} dots and c {len(rb['c_dots'])} grey dots read back from the drawn artists, "
               f"each at its Source Data value (the workbook as written); largest tie {max_tie}; smallest distance "
               f"between unlabelled tied dots: b {pitch_txt['b']} (countable from {B_DOT_MM + COUNT_GAP_MM:.2f} mm), "
               f"c {pitch_txt['c']} (from {C_DOT_MM + COUNT_GAP_MM:.2f} mm); {n_lab} group(s) with a count label; "
               f"{len(under)} grey dot centre(s) within a marker's radius; nearest grey dot to "
               f"a mean marker centre {dmin:.2f} mm (marker radius {C_MARK_PT * MM_PER_PT / 2:.2f} mm); "
               f"{len(rb['b_dots']) + len(rb['c_dots']) + len(rb['c_marks']) + 2 * len(rb['c_bars'])} marks (dots of "
               f"b and c, c's markers and bar ends) placed by their own transforms within {POS_TOL_MM} mm of where the "
               f"workbook value puts them, the largest distance {worst_pos:.4f} mm; {len(rb['c_dots']) - len(out_band)} "
               f"of {len(rb['c_dots'])} grey dots whole inside their setting's band, "
               f"{len(rb['c_dots']) - len(clipped)} inside the axes; {len(overlap)} overlapping pair(s) of dots of "
               f"different groups")
    return probs, summary


def sheets_of(fn):
    """The Source Data sheets, as (name, columns, rows): exactly what the workbook and figure6_numbers.json hold."""
    out = []
    for letter in "abcd":
        rows = fn[letter]
        cols = list(rows[0])
        assert all(list(r) == cols for r in rows), letter
        out.append((sheet_name(letter), cols, [[r[c] for c in cols] for r in rows]))
    return out


def write_source_data(sheets, path):
    """Source Data Fig. 6: one sheet per panel, the numbers plotted, nothing else (E4)."""
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
    import fig_repro
    fig_repro.deterministic_xlsx(path)        # D155: no write time in core.xml or the zip members


def legend_and_caption(fn, stamp, n, k, ops, counted=(), design=None):
    """legend_draft.md (title and legend, E6 and E7) and the Source Data caption (E4), from the plotted numbers.
    counted: the panels ("b", "c") where the plate printed a count beside a tie group (draw_figure's read-back).
    design: design_of()'s (variants, total, left out) for the attempts drawn (D100, D112 Q15 O-a); by default the
    runner's 16 variants and 3,520 attempts."""
    d_vs, d_total, d_left = design or ([v for v, _, _ in VARIANTS], TOTAL, {})
    A, B, C, D = (bold_letter(x) for x in "abcd")
    na = len(fn["a_cols"])
    cm = fn["c_models"]

    def per_op(c):
        """Exact counts, never a range: '20 operations, 15 with 4 matched attempts and 5 with 5'."""
        ks = sorted(c["operations_by_attempts"].items())
        if len(ks) == 1:
            return f"{c['operations_n']} operations, {ks[0][0]} matched attempts each"
        parts = [f"{x} with {k}" for k, x in ks]
        parts[0] += " matched attempts"
        return f"{c['operations_n']} operations, " + ", ".join(parts[:-1]) + f" and {parts[-1]}"
    cms = "; ".join(f"{c['model']} ({', '.join(c['settings'])}), n = {per_op(c)}, {c['matched']} matched attempts "
                    f"per setting" for c in cm)
    # the stamp decides (figure --final writes FINAL): D116 left every variant of the design complete while the
    # reruns are still owed, so "every attempt stored" no longer means final
    final = stamp.startswith("FINAL")
    held = (f"all {n:,} attempts of the design ({len(d_vs)} model and thinking-setting variants, every one complete)"
            if n == d_total else
            f"{n:,} of the {d_total:,} attempts of the design ({k} of {len(d_vs)} model and thinking-setting variants "
            f"complete)")
    prov = "" if final else (
        f"Provisional: drawn from {held}, after the S4 reruns (D75, D80 V1, D81); every value will be redrawn from the "
        f"full records by the same script. ")
    if not final and set(REMOVED) - set(d_vs):
        prov += REMOVED_SENTENCE + " "
    # D100, D112 Q15 O-a: a variant stopped before completion and left out of the design is named, with its count
    if d_left:
        named = "; ".join(f"{short_variant(v)}, {x:,} of {PER_VARIANT} attempts stored" for v, x in d_left.items())
        prov += (f"Not drawn, as {'variants' if len(d_left) > 1 else 'a variant'} stopped before completion and left "
                 f"out of this figure: {named}. ")
    by_ds = ", ".join(f"{v} on {d.replace('_', ' ')}" for d, v in ops["by_dataset"].items())
    # panel d's key, one short definition per keyed group (FIG_KINDS order); KIND_DEF keeps the full definitions
    # for the Source Data and the Methods (Valerio, 23 October: the legend describes the image, in the length of the
    # resubmission captions)
    kinds = "; ".join(LEGEND_KIND_DEF[k] for k, _ in FIG_KINDS if k in LEGEND_KIND_DEF)
    kinds = kinds[:1].upper() + kinds[1:]
    title = "Code-generation pass rates by model, prompting strategy and thinking setting"
    d_few = [r for r in fn["d"] if r["failed_share_pct"] is None]
    d_full = [r for r in fn["d"] if r["failed_share_pct"] is not None and r["attempts_n"] == PER_VARIANT]
    d_part = [r for r in fn["d"] if r["failed_share_pct"] is not None and r["attempts_n"] != PER_VARIANT]
    d_n = (f"n = {PER_VARIANT} per variant, printed at right" if d_full else "")
    if d_part:
        d_n += ("; " if d_n else "") + "; ".join(f"{r['row_label']}, n = {r['attempts_n']}" for r in d_part)
    # the clause on printed counts, in the panels where the plate printed a count beside a tie group (draw_figure's
    # read-back), so the legend describes what is drawn
    b_over = ", a number giving a group's count" if "b" in counted else ""
    c_over = "; a number beside a group is its count" if "c" in counted else ""
    ex = fn.get("d_exceptions") or []
    d_exc = ""
    if ex:
        nx = sum(e["attempts"] for e in ex)
        d_exc = (f"Kind {kind_number('step produced no cell and no error')} is recognised by the record's text "
                 f"'Step failed: None'; {nx} plotted attempt"
                 f"{'s' if nx != 1 else ''} whose record states the same event in the wording a later version of "
                 f"the harness writes ('Step failed: step <k>: no cell created, ...') "
                 f"{'are' if nx != 1 else 'is'} counted under the first later kind that applies: "
                 + "; ".join(f"{e['attempts']} under kind {e['kind_number']} ({e['kind']}), {e['row_label']}"
                             for e in ex) + ". ")
    # panel c's models and n: one clause when every model holds the same operations and matched attempts, else one
    # per model (exact counts, never a range: per_op())
    c_names = [f"{c['model']} ({', '.join(c['settings'])})" for c in cm]
    c_list = (", ".join(c_names[:-1]) + " and " + c_names[-1]) if len(c_names) > 1 else "".join(c_names)
    if len({(per_op(c), c["matched"]) for c in cm}) == 1:
        c_n = f"n = {cm[0]['operations_n']} operations, {cm[0]['matched']} attempts per setting"
    else:
        c_n = "; ".join(f"{c['model']}, n = {per_op(c)}, {c['matched']} attempts per setting" for c in cm)
    legend = (
        f"An attempt (one model and setting, one prompting strategy, one of {ops['n']} data-analysis operations) "
        f"passes when its result matches the reference field by field. "
        f"{A}, Pass rate (%) of each strategy (rows) for each of {na} model and setting variants (columns, ordered "
        f"by overall pass rate); n = {PER_CELL} operations per cell; {CMAP_NAME} colour scale. "
        f"{B}, Gain of each strategy over free-form (percentage points), rows as in {A}, one dot per variant "
        f"(n = {na} per row); black line, median; grey line, no gain, labelled reference in the free-form row; tied "
        f"dots stacked vertically within their row{b_over}. "
        f"{C}, Pass rate at each thinking setting of {c_list}, on the attempts all settings of a model share "
        f"({c_n}). Blue point, mean of the operations' pass rates; bar, two-sided 95% percentile interval over "
        f"{N_BOOT:,} resamples of the operations; grey dots, one per strategy (n = {PER_CELL} operations each)"
        f"{c_over}. Low (gpt-oss:20b) and off (Gemini) are each model's lowest thinking setting; medium is "
        f"gpt-oss:20b's default. "
        f"{D}, Share of each variant's attempts that failed ({d_n}), by kind of failure, one kind per attempt. "
        f"{kinds}. "
        + (f"A variant with fewer than {MIN_D} attempts is listed without a bar "
           f"({', '.join(f'{r['row_label']}, n = {r['attempts_n']}' for r in d_few)}). " if d_few else "")
        + "gemini-3-flash is gemini-3-flash-preview and qwen3-coder-next is qwen3-coder-next:q4_K_M; a variant "
        "without a setting runs at its maker's default.")
    lines = [f"# Figure {FIG_N}, title and legend (draft)", "",
             f"Written by `scripts/S447_fig6_panels.py figure` from the plotted numbers. Data stamp: {stamp}.", "",
             f"**Figure {FIG_N} | {title}.** {legend}", ""]
    cap = [f"# Source Data Fig. {FIG_N}, caption", "",
           (f"**Source Data Fig. {FIG_N} | Numerical values plotted in Figure {FIG_N}.** " + prov +
            f"Data stamp: {stamp}. One sheet per panel. Sheet {sheet_name('a')}: pass count and pass rate (%) of "
            f"each strategy for each of the {na} complete variants, n = {PER_CELL} operations per cell. Sheet "
            f"{sheet_name('b')}: each strategy's and free-form's pass rate per variant and the gain in percentage "
            f"points (dots), and the median gain per strategy (line). Sheet {sheet_name('c')}: per model and thinking "
            f"setting (rows 'setting'), the operations n and how many matched attempts each holds, the matched "
            f"attempts and passes, the pass rate "
            f"(the mean over the operations of each operation's share of passing attempts) and its 95% percentile "
            f"interval over {N_BOOT:,} resamples of the operations (seed {BOOT_SEED}; points and bars); each "
            f"operation's passes, attempts and share (rows 'operation', the units of that mean and of the "
            f"resamples); and the per-strategy pass rates on the matched set (rows 'strategy', grey dots). Sheet "
            f"{sheet_name('d')}: per variant, attempts stored (n), failed attempts, the share of n failed "
            f"by each plotted kind (columns 'share %:', empty for a variant with fewer than {MIN_D} attempts, drawn "
            f"without a bar), the counts behind them (columns 'count:') and the unfolded kinds the plotted groups "
            f"combine (columns 'unfolded count:'). {d_exc}Generated by `uv run --frozen python "
            f"scripts/S447_fig6_panels.py figure` from the run records."), "",
           f"Proposed Data Availability sentence: \"The source data for Figure {FIG_N} is in Supplementary Data [Y].\" "
           "(Y is assigned when the Supplementary Data files are numbered.)", ""]
    return "\n".join(lines), "\n".join(cap)


def render(attempts, flags, out_dir, final, stamp, meta, mutate=None, strict=True):
    """Draw the plate and write its Source Data, numbers, legend and provenance into out_dir. Then check_drawn():
    the dots read back from the drawn artists against the workbook as written; strict (the figure step), a failure
    deletes what was written and stops (exit 1). Returns the page size, what draw_figure reports and the check."""
    figure_lock_agreed()                          # D87: no plate unless the figure lock is agreed
    attempts, d_vs, d_total, d_left = keep_design(attempts)      # D100, D112 Q15 O-a
    cells, variants, strat, panel_a_set, think, pooled, chi = compute(attempts, flags)
    n = sum(v["attempts"] for v in variants.values())
    k = sum(v["complete"] for v in variants.values())
    tag = "" if final else f" (provisional, {n} of {d_total})"
    fn = figure_numbers(attempts, cells, variants, think, panel_a_set, flags)
    ops = {"n": len({a["op_id"] for a in attempts}),
           "by_dataset": dict(Counter(d for d in {a["op_id"]: a.get("dataset") for a in attempts}.values()))}
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in list(out_dir.glob(f"Figure {FIG_N}*")) + list(out_dir.glob(f"Source Data Fig. {FIG_N}*")):
        old.unlink()                              # a plate of another data state is never left beside this one
    paths = {x: out_dir / f"Figure {FIG_N}{tag}.{x}" for x in ("pdf", "svg", "png")}
    W, H, drawn = draw_figure(fn, paths, mutate=mutate)
    if H > FIG_H_MAX_MM - H_ROOM_MM or W != FIG_W_MM:
        raise SystemExit(f"the plate is {W} x {H} mm; FIGURE_LOCK.toml [page] wants {FIG_W_MM} wide, at most "
                         f"{FIG_H_MAX_MM} high")
    sheets = sheets_of(fn)
    sd = out_dir / f"Source Data Fig. {FIG_N}{tag}.xlsx"
    write_source_data(sheets, sd)
    numbers = out_dir / f"figure{FIG_N}_numbers.json"
    numbers.write_text(json.dumps({"stamp": stamp, "what": "every number the plate draws, sheet by sheet as Source "
                                   f"Data Fig. {FIG_N} holds them (S448 R8 compares the workbook with this file)",
                                   "sheets": {nm: {"columns": cols, "rows": rows} for nm, cols, rows in sheets},
                                   "printed": drawn["printed"],
                                   "printed_what": "every number printed on the plate: the SVG group id of its text, "
                                                   "and the Source Data sheet and row (or the rows counted) and "
                                                   "format it is written from; S448 R8 (6) holds the plate's texts "
                                                   "to the workbook through it"},
                                  indent=1, default=str) + "\n")
    gate = check_drawn(drawn["readback"], sd)
    legend, cap = legend_and_caption(fn, stamp, n, k, ops,
                                     counted={lb["panel"] for lb in drawn["readback"]["labels"]},
                                     design=(d_vs, d_total, d_left))
    (out_dir / "legend_draft.md").write_text(legend)
    capf = out_dir / f"Source Data Fig. {FIG_N} caption{tag}.md"
    capf.write_text(cap)
    out = {**meta, "stamp": stamp, "page_mm": [W, H], "layout": drawn["layout"], "row_mm": drawn["row_mm"],
           "design": {"variants": d_vs, "attempts": d_total, "runner_variants": len(VARIANTS), "runner_attempts": TOTAL,
                      "if_time_not_drawn": d_left, "removed": REMOVED,
                      "rule": "D100; D112 Q15 O-a: an IF_TIME variant is in the design only with all its attempts "
                              "stored; D116: a REMOVED variant is never in it"},
           "row_a_mm": drawn["row_a_mm"],
           "figure_lock": {"path": str(FIGURE_LOCK.relative_to(ROOT)), "sha256": sha256_file(FIGURE_LOCK),
                           "status": FLOCK.get("status")},
           "type_pt": {"panel letters (bold)": PT_LETTER, "panel titles": None, "axis titles": PT_AXIS,
                       "all other text": PT_TEXT}, "font": FONT,
           "patterns_panel_d": KIND_PATTERN, "colours_panel_d": dict(FIG_KINDS),
           "count_labels": Counter(lb["panel"] for lb in drawn["readback"]["labels"]),
           "files": {p.name: sha256_file(p) for p in list(paths.values()) + [sd, capf, numbers,
                                                                            out_dir / "legend_draft.md"]},
           "row_c_mm": drawn["row_c_mm"], "row_d_mm": drawn["row_d_mm"],
           "drawn_check": "check_drawn(): " + gate[1] + ("" if not gate[0] else " | FAILED: " + "; ".join(gate[0])),
           "panels": {"a": f"pass rate per strategy (rows) and complete variant (columns), {CMAP_NAME} 0-100, "
                           f"n = 20",
                      "b": "gain over free-form (points) per strategy (rows as a), one dot per complete "
                           f"variant, tied dots {B_PITCH_MM} mm apart across the row (tie_offsets), a count beside a "
                           "group the row cannot hold, median line over the dots",
                      "c": f"per model with 2+ settings stored: matched pass rate, 95% percentile interval over "
                           f"{N_BOOT} resamples of the operations (seed {BOOT_SEED}), grey dots the strategies with "
                           f"all 20 operations in the matched set, stacked upward from {C_CLEAR_MM} mm above the "
                           f"setting's bar, at least {C_TOP_CLEAR_MM} mm below the bar above; "
                           f"n = operations",
                      "d": f"share of n failed, by folded kind (FOLD) in fail_kind's order, Okabe-Ito colours and "
                           f"a fill pattern per kind (patterns_panel_d); no bar under {MIN_D} attempts"},
           "numbers": {x: fn[x] for x in ("a_cols", "c_models", "d_rows")}}
    (out_dir / f"figure{FIG_N}_provenance.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    if strict and gate[0]:
        for p in list(paths.values()) + [sd, capf, numbers, out_dir / "legend_draft.md",
                                         out_dir / f"figure{FIG_N}_provenance.json"]:
            p.unlink(missing_ok=True)
        print("check_drawn FAILED, nothing kept: " + "; ".join(gate[0]), file=sys.stderr)
        sys.exit(1)
    return n, k, W, H, drawn, paths, sd, capf, gate


def figure(argv, final=False):
    reproduced = reproduce()                      # stops (exit 2) before anything is written
    attempts, flags, inputs, notes = load_mirror()
    inputs[str(LOCK.relative_to(ROOT))] = sha256_file(LOCK)
    kept, d_vs, d_total, d_left = keep_design(attempts)              # D100, D112 Q15 O-a
    n = len(kept)
    if final and n != d_total:
        raise SystemExit(f"--final: {n} of {d_total} attempts of the design stored; the plate is still provisional")
    variants_done = sum(1 for v in d_vs if sum(1 for a in kept if variant_of(a["run_id"]) == v) == PER_VARIANT)
    when = iso_local(notes["newest_answers_mtime"])
    stamp = (f"PROVISIONAL: {n:,} of {d_total:,} attempts, {variants_done} of {len(d_vs)} variants complete, "
             f"records of {when}; after the S4 reruns (D75, D80 V1, D81)") if not final else \
        f"FINAL: {n:,} of {d_total:,} attempts, records of {when}"
    if d_left:
        print("not drawn (D100, D112 Q15 O-a): " + ", ".join(f"{v} {x} of {PER_VARIANT}" for v, x in d_left.items()))
    meta = {"provenance": provenance(argv, inputs), "reproduced": reproduced}
    n, k, W, H, drawn, paths, sd, capf, gate = render(attempts, flags, OUT, final, stamp, meta)
    print(stamp)
    print_earlier_label(kept, flags)
    print("check_drawn: " + gate[1])
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W:.0f} x {H:.1f} mm, {drawn['layout']}), "
          f"{sd.name}, {capf.name}, figure{FIG_N}_numbers.json, legend_draft.md, figure{FIG_N}_provenance.json into "
          f"{OUT.relative_to(ROOT)}")


def copy_cases(keep_fn=None):
    """mirror --from-copy --complete-only on a synthetic copy in a temporary folder (RUNS, OUT and MANIFEST pointed
    there for the call): gemini-2.5-pro off complete in the Studio's old clone, gpt-oss:20b medium partial on the
    laptop. Wanted: only the complete variant mirrored (220 attempts), its free_form run keeping the commit the last
    manifest gave it and its other runs the Studio clone's commit from that manifest, and a copy whose file differs
    from its SHA256SUMS refused, and --complete-only without a copy refused before list_sinks() or clone_commit() runs
    (both replaced by recorders, so nothing reaches ssh). keep_fn replaces complete_in() (a mutant). Returns
    (problems, cases)."""
    import shutil
    g = globals()
    saved = {k: g[k] for k in ("RUNS", "OUT", "MANIFEST", "complete_in", "list_sinks", "clone_commit")}
    bad = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        copy = d / "copy"
        sinks = [("studio", "mentori-runs-s2", f"exp_05__{s}__gemini-2.5-pro+off", 20) for s, _ in STRATEGIES] + \
            [("laptop", "mentori-runs-s2-laptop-d75", "exp_05__free_form__gpt-oss-20b+medium", 5)]
        lines = []
        for machine, clone, rid, n in sinks:
            p = copy / machine / clone / "runs" / rid / "answers.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"results": [{"answer_key": f"{rid}|op{i}|d1", "run_id": rid}
                                                 for i in range(n)]}))
            lines.append(f"{sha256_file(p)}  {p.relative_to(copy)}")
        (copy / "SHA256SUMS").write_text("\n".join(lines) + "\n")
        (copy / "copy_log.tsv").write_text("copy\tsource\tcopied_at\n")
        ff = "exp_05__free_form__gemini-2.5-pro+off"
        old = {"provenance": {"written_utc": "2026-10-16T21:27:40Z"},
               "sources": [{"machine": "studio", "clone": "~/projects/mentori-runs-s2", "commit": "a" * 40, "runs": []}],
               "runs": {ff: {"clone": "~/projects/mentori-runs-s2", "clone_commit": "b" * 40}}}
        try:
            g.update(RUNS=d / "runs", OUT=d / "out", MANIFEST=d / "out" / "manifest.json")
            if keep_fn:
                g["complete_in"] = keep_fn
            g["OUT"].mkdir()
            g["MANIFEST"].write_text(json.dumps(old))
            with open(os.devnull, "w") as quiet, __import__("contextlib").redirect_stdout(quiet):
                mirror(["mirror", "--selftest"], copy, complete_only=True)
            man = json.loads(g["MANIFEST"].read_text())
            vs = sorted({variant_of(r) for r in man["runs"]})
            cms = {r: x["clone_commit"][:1] for r, x in man["runs"].items()}
            if vs != ["gemini-2.5-pro+off"] or man["attempts_total"] != PER_VARIANT:
                bad.append(f"complete only: variants {vs}, {man['attempts_total']} attempts (want gemini-2.5-pro+off, "
                           f"{PER_VARIANT})")
            own = [c for x in man["runs"].values() for c in x.get("attempt_code_commit", {}).values()]
            if len(own) != PER_VARIANT or any(own):        # D252: no calls.jsonl, so no version, and none filled in
                bad.append(f"attempt_code_commit: {len(own)} attempts, {sum(map(bool, own))} with a commit "
                           f"(want {PER_VARIANT}, none)")
            if cms.get(ff) != "b" or any(c != "a" for r, c in cms.items() if r != ff):
                bad.append(f"run commits {sorted(set(cms.values()))}, {ff} {cms.get(ff)!r} (want b, the rest a)")
            p = copy / "studio" / "mentori-runs-s2" / "runs" / ff / "answers.json"
            p.write_text(p.read_text() + " ")
            shutil.rmtree(g["RUNS"])
            try:
                mirror(["mirror", "--selftest"], copy, complete_only=True)
                bad.append("a copy differing from its SHA256SUMS was mirrored")
            except SystemExit as e:
                if "differ from its SHA256SUMS" not in str(e) or g["RUNS"].exists():
                    bad.append(f"a changed copy: {e}")
            # --complete-only without a copy: refused before a clone is listed or its commit read (no ssh)
            reached = []
            g.update(list_sinks=lambda *a: reached.append("list_sinks") or [],
                     clone_commit=lambda *a: reached.append("clone_commit") or "")
            try:
                mirror(["mirror", "--selftest"], None, complete_only=True)
                bad.append("--complete-only without --from-copy was not refused")
            except (SystemExit, Exception) as e:
                if "give --from-copy" not in str(e) or reached:
                    bad.append(f"--complete-only without --from-copy: {e}; reached {reached} first")
        finally:
            g.update(saved)
    return bad, 4


def attempt_commit_cases(commits_fn=None):
    """D252: attempt_code_commits() (or commits_fn, for a mutant) on a synthetic run folder. Four attempts: k1 whose
    two calls name commit A, k2 whose calls carry no code_commit key (the October records), k3 stored twice (the first
    entry's ctx_uid at A, the kept last entry's at B), k4 with no call at all; a call of another ctx_uid at C, which
    names no stored attempt. Wanted {k1: A, k2: None, k3: B, k4: None}, and a run refused when one attempt's calls
    name two commits and when a call records code_dirty true. Returns (problems, cases)."""
    commits_fn = commits_fn or attempt_code_commits
    A, B, C = "a" * 40, "b" * 40, "c" * 40
    bad = []
    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d) / "exp_05__free_form__x"
        run_dir.mkdir()
        res = [{"answer_key": "k1", "ctx_uid": "u1"}, {"answer_key": "k2", "ctx_uid": "u2"},
               {"answer_key": "k3", "ctx_uid": "u3old"}, {"answer_key": "k3", "ctx_uid": "u3"},
               {"answer_key": "k4", "ctx_uid": "u4"}]
        calls = [{"ctx_uid": "u1", "code_commit": A, "code_dirty": False},
                 {"ctx_uid": "u1", "code_commit": A, "code_dirty": False}, {"ctx_uid": "u2", "role": "generator"},
                 {"ctx_uid": "u3old", "code_commit": A, "code_dirty": False},
                 {"ctx_uid": "u3", "code_commit": B, "code_dirty": False},
                 {"ctx_uid": "u9", "code_commit": C, "code_dirty": False}]

        def write(cs):
            (run_dir / "answers.json").write_text(json.dumps({"results": res}))
            (run_dir / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cs) + "not json\n")
        write(calls)
        got, want = commits_fn(run_dir), {"k1": A, "k2": None, "k3": B, "k4": None}
        if got != want:
            bad.append(f"commits {got}, want {want}")
        for name, cs, msg in (("two commits", calls + [{"ctx_uid": "u1", "code_commit": B}], "commits"),
                              ("dirty", calls + [{"ctx_uid": "u2", "code_commit": A, "code_dirty": True}], "dirty")):
            write(cs)
            try:
                commits_fn(run_dir)
                bad.append(f"{name}: not refused")
            except SystemExit as e:
                if msg not in str(e):
                    bad.append(f"{name}: refused with {e}")
    return bad, 3


def design_cases():
    """D112 Q15 O-a (audit A21-19): design_of() and keep_design() on synthetic attempt lists. Returns (problems,
    cases). The figure step's --final test and every stamp read the same function, so --final passes on 11 complete
    variants with D100's three if-time variants absent or partial, an if-time variant counts once complete, and a
    REMOVED variant (D116) never counts, even complete."""
    def atts(v, n):
        return [{"run_id": f"exp_05__{STRATEGIES[i % len(STRATEGIES)][0]}__{v}", "answer_key": f"{v}|{i}"}
                for i in range(n)]
    core = [v for v, _, _ in VARIANTS if v not in IF_TIME and v not in REMOVED]
    full = [a for v in core for a in atts(v, PER_VARIANT)]
    ds, gl = "deepseek-r1-70b+default", "glm-4.7-flash-bf16+default"
    nd, no = "nemotron-3-nano-30b+default", "nemotron-3-nano-30b+off"
    cases = [("no if-time records", full, 11, 2420, {}, len(full)),
             ("deepseek 118 and glm default 74 stored (D100's state)", full + atts(ds, 118) + atts(gl, 74), 11, 2420,
              {ds: 118, gl: 74}, len(full)),
             ("deepseek complete", full + atts(ds, PER_VARIANT), 12, 2640, {}, len(full) + PER_VARIANT),
             ("all if-time complete", full + [a for v in IF_TIME for a in atts(v, PER_VARIANT)], 14,
              TOTAL - len(REMOVED) * PER_VARIANT, {}, TOTAL - len(REMOVED) * PER_VARIANT),
             ("nemotron default 76 and off 63 stored (D116's state)", full + atts(nd, 76) + atts(no, 63), 11, 2420, {},
              len(full)),
             ("nemotron both complete (D116: still out)", full + atts(nd, PER_VARIANT) + atts(no, PER_VARIANT), 11,
              2420, {}, len(full)),
             ("a core variant partial", full[PER_VARIANT // 2:], 11, 2420, {}, len(full) - PER_VARIANT // 2)]
    bad = []
    for what, xs, nv, tot, left, nkept in cases:
        kept, vs, total, lo = keep_design(xs)
        final = len(kept) == total
        want_final = nkept == tot
        if len(vs) != nv or total != tot or lo != left or len(kept) != nkept or final != want_final:
            bad.append(f"{what}: {len(vs)} variants, total {total}, left out {lo}, {len(kept)} kept, final {final} "
                       f"(want {nv}, {tot}, {left}, {nkept}, {want_final})")
    return bad, len(cases)


def thinking_cases():
    """D112 Q17 O-a (audit A21-28): thinking_sent() on the record shapes S2 writes (read from the mirrored records, 21
    October: Ollama fields_sent.think low, medium, high or true, or no think field; Gemini fields_sent null and
    options_sent.thinkingConfig {"thinkingBudget": 128}, {"thinkingLevel": "minimal"} or none). Returns (problems,
    cases)."""
    cases = [({"fields_sent": {"think": "low"}, "options_sent": {"num_ctx": 131072}}, "think_sent=low"),
             ({"fields_sent": {"think": True}}, "think_sent=True"),
             ({"fields_sent": {"truncate": False}, "options_sent": {"temperature": 0.7}}, "think_sent=not sent"),
             ({"fields_sent": None, "options_sent": {"thinkingConfig": {"thinkingBudget": 128}}},
              'thinkingConfig_sent={"thinkingBudget": 128}'),
             ({"fields_sent": None, "options_sent": {"thinkingConfig": {"thinkingLevel": "minimal"}}},
              'thinkingConfig_sent={"thinkingLevel": "minimal"}'),
             ({"fields_sent": None, "options_sent": {"temperature": 1.0}}, "think_sent=not sent")]
    bad = [f"{r}: {thinking_sent(r)!r}, want {want!r}" for r, want in cases if thinking_sent(r) != want]
    return bad, len(cases)


def give_kinds(atts):
    """The selftest's plates hold every kind of panel d (D112 Q12 O2: the tools-refused group drawn and keyed beside
    the other nine): the failed attempts, in order, are given the kinds of KINDS_ALL in turn, each by the record
    fields or the "end:" flags that make fail_kind() return it (Gemini empty reply only on a Gemini variant; elsewhere
    that turn is skipped). Returns (flags by ctx_uid, kinds given). Every attempt keeps its passed value, so panels a
    to c do not change."""
    make = {"tool-call parse error": ({}, {"end:parse"}), "tool call written as text": ({}, {"end:as_text"}),
            "stall": ({}, {"end:stall"}),
            "tools refused by Ollama": ({"exec_outcome": "step_failed", "exec_error": "Step failed: x: status error: "
                                         "HTTP 400: registry.ollama.ai/library/x does not support tools"}, set()),
            "other call error": ({}, {"end:call_error"}), "length stop": ({}, {"end:length"}),
            "harness error": ({"exec_outcome": "exception"}, set()),
            "step produced no cell and no error": ({"exec_outcome": "step_failed", "exec_error": "Step failed: None"},
                                                   set()),
            "Gemini empty reply": ({"generations": [{"raw_reply": ""}]}, set()),
            "no code": ({"exec_outcome": "not_run", "code": ""}, set()),
            "code raised or timed out": ({"exec_outcome": "error", "actual_results": {}}, set()),
            "result wrong or missing": ({}, set()), "other": ({"exec_outcome": "unlisted"}, set())}
    assert list(make) == KINDS_ALL
    flags, given, i = {}, Counter(), 0
    for j, a in enumerate(x for x in atts if not x["passed"]):
        kd = KINDS_ALL[i % len(KINDS_ALL)]
        if kd == "Gemini empty reply" and not a["gen_model"].startswith("gemini::"):
            continue
        i += 1
        rec, fl = make[kd]
        a.update(rec)
        a["ctx_uid"] = f"selftest-{j}"
        flags[a["ctx_uid"]] = set(fl)
        got = fail_kind(a, flags[a["ctx_uid"]])
        assert got == kd, (kd, got)
        given[kd] += 1
    return flags, given


def selftest(argv):
    """Synthetic records (no run record read; LOCK.toml is read for panel c's labels; nothing written to the
    repository): (1) 13 complete variants that all score alike (every variant but glm-4.7-flash off, which D100 does not
    run, and nemotron-3-nano:30b's two, which D116 removed), so every strategy of panel b holds 13 tied gains (the layout for more than 7 variants, count labels); (2) 7
    complete variants with mixed ties (the layout for up to 7) and two partial variants. In both the failed attempts
    are given every kind of panel d (give_kinds()), so all ten groups are drawn and keyed (D112 Q12 O2). Each plate is
    drawn into a temporary folder and must pass check_drawn() (positions read back from the drawn artists against the
    workbook as written), fit the page and hold the tools-refused group in sheet d and the legend; S448 is run on the
    folder. Then the gate
    itself is checked: case 2 is drawn seven more times, each altered once (draw_figure's mutate), and check_drawn()
    must fail each with the problem it was built for: b_shift (a dot of b 0.5 points off its gain), c_shift (a grey dot
    of c 0.5 points off), c_on_bar (c's grey dots drawn on the bar's line, under the mean marker), b_crowd (b's tied
    dots 0.4 mm apart, no count), b_offset (a dot of b at its datum, its transform offset 1 mm along the value axis),
    c_wrong_band (a setting's grey dots in the next setting's band) and c_clipped (above the axes). Then panel d's
    patterns: one per kind, all different, each drawn in a box as wide as its smallest whole mark and not in one 0.01 mm
    narrower, a zigzag never under one whole V. Then panel d's kind rule (D92 Q193, D94 Q-b O2, q193_cases()):
    twenty-two synthetic call sequences, each labelled by the call that ended it or by an earlier event with no cell
    made after it (a cell round's cell made after its last call), and every call's event still counted, four of them
    on Ollama's tool refusal (D112 Q12 O2). Then the design total (design_cases(), D112 Q15 O-a) and the thinking
    diagnostic (thinking_cases(), D112 Q17 O-a). Last, the rounding
    rule: half_up() and S448's HalfUpFormatter on exact quarters, float noise and signs, and the A25 gap from exact
    values."""
    import random
    import tempfile
    ops = [f"airway_{i}_op" for i in range(1, 11)] + [f"lung_{i}_op" for i in range(1, 11)]

    def synth(vs, rule, partial=()):
        out = []
        for v in vs:
            for s, _ in STRATEGIES:
                for j, o in enumerate(ops):
                    if (v, s) in partial and j >= 7:
                        continue
                    out.append({"run_id": f"exp_05__{s}__{v}", "config": s, "op_id": o, "answer_key": f"{s}|{o}|d1",
                                "dataset": o.split("_")[0], "gen_model": "gemini::x" if "gemini" in v else "ollama::x",
                                "passed": rule(v, s, j), "exec_outcome": "ok", "code": "x"})
        return out
    every = [v for v, _, _ in VARIANTS]
    rng = random.Random(7)
    pr = {(v, s): rng.choice([0.5, 0.6, 0.7, 0.75, 0.8]) for v in every for s, _ in STRATEGIES}
    idx = {s: i for i, (s, _) in enumerate(STRATEGIES)}
    # the partial pair of case 2: gpt-oss:20b high (a third setting of a model in c) and gemma3:27b default (a model
    # with one setting, in d only; nemotron-3-nano:30b default until D116 removed it); not glm-4.7-flash default,
    # which D100 left out of the design unless complete (D112 Q15 O-a), so a partial one is not drawn
    part2 = [every[4], every[9]]
    # case 1: the largest design D100 and D116 allow, every variant but glm-4.7-flash off (D100: not run) and
    # nemotron-3-nano:30b's two (D116), 13 complete, all tied. Sixteen variants with all ten groups of panel d keyed
    # needed 172.4 mm and were refused (above [page] height_max_mm); fifteen fit (D112 Q12 O2 added the tenth group)
    every13 = [v for v in every if v != "glm-4.7-flash-bf16+off" and v not in REMOVED]
    cases = [("13 tied", synth(every13, lambda v, s, j: j < 10 + idx[s] % 4)),
             ("7 mixed", synth(every[:4] + every[11:16][:3] + part2,
                               lambda v, s, j: j < round(20 * pr[(v, s)]),
                               partial={(v, s) for v in part2 for s, _ in STRATEGIES}))]
    # every kind of panel d in both plates, the tools-refused group among them (D112 Q12 O2)
    case_flags = {}
    for name, atts in cases:
        case_flags[name], given = give_kinds(atts)
        print(f"selftest {name}: panel d kinds given to its failed attempts: "
              + ", ".join(f"{k} {given[k]}" for k in KINDS_ALL))
    bad = 0
    for name, atts in cases:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            kept, d_vs, d_total, _ = keep_design(atts)
            final = len(kept) == d_total
            stamp = (f"{'FINAL' if final else 'PROVISIONAL'}: {len(kept):,} of {d_total:,} attempts, synthetic "
                     f"records (S447 selftest {name})")
            n, k, W, H, drawn, paths, sd, capf, gate = render(atts, case_flags[name], d, final, stamp,
                                                              {"selftest": name}, strict=False)
            rb = drawn["readback"]
            print(f"selftest {name}: {n} attempts, {k} variants complete, {W:.0f} x {H:.1f} mm "
                  f"({drawn['layout']}, rows a {drawn['row_a_mm']} mm, b {drawn['row_mm']} mm, c "
                  f"{drawn['row_c_mm']} mm, d {drawn['row_d_mm']} mm); "
                  f"{len(rb['labels'])} count label(s)")
            print(f"  check_drawn: {'FAILED: ' + '; '.join(gate[0]) if gate[0] else 'passed'}: {gate[1]}")
            bad += bool(gate[0]) + (H > FIG_H_MAX_MM)
            # the tools-refused group is drawn, keyed and defined (D112 Q12 O2)
            nums = json.loads((d / f"figure{FIG_N}_numbers.json").read_text())
            d_sheet = nums["sheets"][sheet_name("d")]
            col = d_sheet["columns"].index("count: tools refused by Ollama")
            n_tools = sum(r[col] for r in d_sheet["rows"] if isinstance(r[col], int))
            leg = (d / "legend_draft.md").read_text()
            svg_txt = paths["svg"].read_text()
            t_ok = n_tools > 0 and "tools refused by Ollama means" in leg \
                and "refused" in svg_txt and all(v[1:] in leg for v in LEGEND_KIND_DEF.values())
            print(f"  tools refused by Ollama: {n_tools} attempt(s) in sheet {sheet_name('d')}, "
                  f"{'defined in the legend and keyed on the plate' if t_ok else 'MISSING from the legend or the key'}")
            bad += not t_ok
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", "6",
                                "--dir", str(d)], capture_output=True, text=True)
            print("  S448: " + "\n  S448: ".join(ln[:300] for ln in r.stdout.splitlines()
                                                if " FAIL " in ln or ln.startswith(("every", "FAIL"))))
            bad += r.returncode != 0
            if os.environ.get("S447_SELFTEST_KEEP"):
                import shutil
                keep = Path(os.environ["S447_SELFTEST_KEEP"]) / name.replace(" ", "_")
                shutil.copytree(d, keep, dirs_exist_ok=True)
    # each mutant must fail check_drawn with the problem it was built for (its message), not merely fail
    name, atts = cases[1]
    muts = [("b_shift", "off their Source Data value"), ("c_shift", "off their Source Data value"),
            ("c_on_bar", "touch a marker or bar"), ("b_crowd", "not countable"),
            ("b_offset", "placed on the page off where the workbook value puts them"),
            ("c_wrong_band", "outside their setting's band"), ("c_clipped", "outside the axes (clipped)")]
    n_caught = 0
    for m, want in muts:
        with tempfile.TemporaryDirectory() as d:
            kept, _, d_total, _ = keep_design(atts)
            *_, gate = render(atts, case_flags[name], Path(d), False, f"PROVISIONAL: {len(kept):,} of {d_total:,} "
                              f"attempts, synthetic records (S447 selftest mutant {m})", {"selftest": m}, mutate=m,
                              strict=False)
            caught = any(want in x for x in gate[0])
            n_caught += caught
            print(f"mutant {m:12s} {'CAUGHT' if caught else 'MISSED'} (wants {want!r}): "
                  + ("; ".join(gate[0]) if gate[0] else "check_drawn passed"))
    bad += n_caught != len(muts)
    # panel d's patterns: every kind has one, all different; a box as wide as a pattern's smallest whole mark holds
    # marks and a box 0.01 mm narrower holds none; a zigzag keeps at least one whole V (3 vertices), never one arm,
    # and every vertex inside its box
    p_bad = []
    if len(set(KIND_PATTERN.values())) != len(KIND_PATTERN) or not all(KIND_PATTERN.values()):
        p_bad.append(f"patterns not one per kind, all set: {KIND_PATTERN}")
    for k, pat in KIND_PATTERN.items():
        wmin = pattern_min_mm(pat)
        for w, want in ((wmin, True), (wmin - 0.01, False)):
            ln, dt, rg = pattern_marks((10.0, 5.0, 10.0 + w, 8.0), pat)
            if bool(ln or dt or rg) != want:
                p_bad.append(f"{k} ({pat!r}) in a {w:.2f} mm box: {'marks' if not want else 'no marks'}")
            if pat == "z" and ln and (min(len(x) for x in ln) < 3 or any(
                    not (10.0 <= px <= 10.0 + w and 5.0 <= py <= 8.0) for x in ln for px, py in x)):
                p_bad.append(f"{k}: a zigzag of fewer than 3 vertices or a vertex outside its box: {ln}")
    print(f"patterns: {len(KIND_PATTERN)} kinds, {len(set(KIND_PATTERN.values()))} patterns"
          + (": " + "; ".join(p_bad) if p_bad else ", each drawn at its smallest whole mark and not below it, the "
                                                   "zigzag never under one whole V"))
    bad += bool(p_bad)
    # panel d's kind rule (D92 Q193, D94 Q-b O2): kinds 1 to 5 are read from the call that ended the attempt, kinds 1
    # to 4 also from an earlier call with no cell made after it
    q_bad, q_n = q193_cases()
    print(f"panel d kind rule: {q_n - len(q_bad)} of {q_n} call sequences as wanted"
          + (": " + "; ".join(q_bad) if q_bad else " (an earlier error with a cell made after it is not the kind, "
                                                   "one with no cell after it is, the last call by seq is, a judge "
                                                   "call is not read, every call's event still counted for the "
                                                   "reruns; D92 Q193, D94 Q-b O2)"))
    bad += bool(q_bad)
    # D114 Q29 O2: an attempt is read up to its first length stop and is a "length" failure
    l_bad, l_n = length_rule_cases()
    print(f"length rule (D114 Q29 O2): {l_n - len(l_bad)} of {l_n} cases as wanted"
          + (": " + "; ".join(l_bad) if l_bad else " (a pass after a length stop fails, the calls after it are not "
                                                   "read, a judge's length stop is not one, both exp_05 rules read "
                                                   "the same)"))
    bad += bool(l_bad)
    # D115 L1b: the printed count of failed attempts outside the structured strategies labelled by an earlier event
    e_bad, e_n = earlier_label_cases()
    print(f"earlier-event count (D115 L1b): {e_n - len(e_bad)} of {e_n} case sets as wanted"
          + (": " + "; ".join(e_bad) if e_bad else " (an earlier event counted, the ending call's own not, the "
                                                   "structured strategies and passes left out)"))
    bad += bool(e_bad)
    # D115 LS1: the calls means and their counters, as extras() computes them
    m_bad, m_n = calls_mean_cases()
    print(f"calls means (D115 LS1): {m_n - len(m_bad)} of {m_n} checks as wanted"
          + (": " + "; ".join(m_bad) if m_bad else " (a length-cut attempt counted to its stop under both stored "
                                                   "rules, the others as stored; the two counters)"))
    bad += bool(m_bad)
    # D115 LS1, LS2 and L1b mutants: each change undone must fail its cases
    def length_outranks(flags, last):             # LS2 O-b: a length stop outranks every earlier event
        end_flags(flags, last)
        for u in flags:
            if "end:length" in flags[u]:
                flags[u] -= {f"end:{x}" for x in EVENTS}
    def ending_call_too(attempts, flags):         # L1b: any event of kinds 1 to 5 counted, the ending call's too
        xs = [a for a in attempts if not a["config"].startswith("coder_v2") and not a["passed"]]
        return sum(any(f"end:{x}" in flags.get(a["ctx_uid"], set()) for x in EVENTS) for a in xs), len(xs)
    c_bad, c_n = copy_cases()
    print(f"mirror --from-copy --complete-only (D114 Q30 O-a): {c_n - len(c_bad)} of {c_n} cases as wanted"
          + (": " + "; ".join(c_bad) if c_bad else " (the complete variant only, a run's commit from the last "
                                                   "manifest, a copy differing from its SHA256SUMS refused, "
                                                   "--complete-only without a copy refused before any ssh)"))
    bad += bool(c_bad)
    n_bad, n_n = commit_note_cases()
    print(f"claims.md commit notes (review of 22 October): {n_n - len(n_bad)} of {n_n} cases as wanted"
          + (": " + "; ".join(n_bad) if n_bad else " (a commit an earlier manifest read over ssh, or carried, is "
                                                   "said to be so; one read by git rev-parse, or over ssh, is not)"))
    bad += bool(n_bad)
    a_bad, a_n = attempt_commit_cases()
    print(f"each attempt's own code commit (D252): {a_n - len(a_bad)} of {a_n} cases as wanted"
          + (": " + "; ".join(a_bad) if a_bad else " (read from its own calls by ctx_uid, the kept entry's; none "
                                                   "recorded gives null; two commits or a dirty tree refused)"))
    bad += bool(a_bad)
    d252_mut = attempt_commit_cases(commits_fn=lambda rd: {
        a["answer_key"]: next((json.loads(ln).get("code_commit") for ln in open(rd / "calls.jsonl")
                               if ln.startswith("{") and json.loads(ln).get("code_commit")), None)
        for a in attempts_of(rd / "answers.json")[0]})[0]
    print(f"mutant D252: the run's first recorded commit given to every attempt: "
          f"{'CAUGHT: ' + '; '.join(d252_mut) if d252_mut else 'MISSED'}")
    bad += not d252_mut
    d115_muts = [("LS2: length outranks an earlier event", length_rule_cases(ends=length_outranks)[0]),
                 ("Q30: every variant mirrored", copy_cases(
                     keep_fn=lambda paths: {variant_of(r) for r in paths})[0]),
                 ("LS1: the stored n_llm_calls", length_rule_cases(calls_of=lambda a: a.get("n_llm_calls"))[0]),
                 ("LS1: the means read the stored n_llm_calls",
                  calls_mean_cases(get=lambda a: a.get("n_llm_calls"))[0]),
                 ("L1b: the ending call's events counted too", earlier_label_cases(count=ending_call_too)[0]),
                 ("claims: a carried commit stated as read", commit_note_cases(notes_fn=lambda man, rids: [])[0])]
    for m, problems in d115_muts:
        print(f"mutant {m}: {'CAUGHT: ' + '; '.join(problems) if problems else 'MISSED'}")
    bad += sum(not p for _, p in d115_muts)
    # D112 Q15 O-a: the design total, the left-out if-time variants and the --final test
    g_bad, g_n = design_cases()
    print(f"design total (D100, D112 Q15 O-a): {g_n - len(g_bad)} of {g_n} cases as wanted"
          + (": " + "; ".join(g_bad) if g_bad else " (11 variants and 2,420 attempts while an if-time variant is "
                                                   "absent or partial, which is not drawn; one counted once "
                                                   "complete; nemotron never counted, D116; --final on the "
                                                   "design's total)"))
    bad += bool(g_bad)
    # D112 Q17 O-a: the thinking diagnostic reads Gemini's thinkingConfig
    t_bad, t_n = thinking_cases()
    print(f"thinking diagnostic (D112 Q17 O-a): {t_n - len(t_bad)} of {t_n} record shapes as wanted"
          + (": " + "; ".join(t_bad) if t_bad else " (Ollama's think field, Gemini's thinkingConfig, neither sent)"))
    bad += bool(t_bad)
    # rounding: every printed number is rounded once, half away from zero, after exact() removes float noise; S448
    # fills the plate's printed formats with the same rule
    import importlib.util
    spec = importlib.util.spec_from_file_location("S448", ROOT / "scripts" / "S448_figure_rules_check.py")
    s448 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s448)
    cases_r = [(69.25, 1, False, "69.3"), (54.25000000000001, 1, False, "54.3"), (80.74999999999999, 1, False, "80.8"),
               (12.5, 0, False, "13"), (2.5, 0, False, "3"), (2.675, 2, False, "2.68"), (-0.05, 1, True, "-0.1"),
               (-0.04, 1, True, "0.0"), (21.05, 1, True, "+21.1"), (54.25000000000001 - 33.2, 1, True, "+21.1"),
               (68.18181818181817, 1, False, "68.2"), (0.0, 0, False, "0")]
    r_bad = []
    for x, nd, sg, want in cases_r:
        got = half_up(x, nd, sign=sg)
        fmt = "{v:" + ("+" if sg else "") + f".{nd}f" + "}"
        got448 = s448.HALF_UP.format(fmt, v=x)
        if got != want or got448 != want:
            r_bad.append(f"{x!r} to {nd}: S447 {got!r}, S448 {got448!r}, want {want!r}")
    gap = half_up(exact(54.25000000000001) - exact(33.2), 1, sign=True)
    if gap != "+21.1":
        r_bad.append(f"A25 gap from exact values {gap!r}, want '+21.1'")
    print(f"rounding: {len(cases_r) + 1 - len(r_bad)} of {len(cases_r) + 1} cases as wanted in S447 and S448"
          + (": " + "; ".join(r_bad) if r_bad else " (exact quarters up in size, float noise removed first, the "
                                                   "A25 gap from exact values)"))
    bad += bool(r_bad)
    print("selftest " + ("FAILED" if bad else "passed: in both plates every dot of b and c sits at its Source Data "
                         "value as read back from the drawn artists and lands on the page where that value puts it, "
                         "every dot of b inside its row, every grey dot of c inside its setting's band and the axes, "
                         "no dots of two groups overlapping, every tie countable or counted, no grey dot of c on a "
                         f"marker or bar, every page within {FIG_H_MAX_MM:.0f} mm, S448 passing; {n_caught} of "
                         f"{len(muts)} mutants caught by the problem each was built for; the rounding cases as wanted"))
    sys.exit(1 if bad else 0)

# ---------------------------------------------------------------------------------------------------------------
# Step 4: claims. The claims list (E8, D82) from the same data state as the plate
# ---------------------------------------------------------------------------------------------------------------
CLAIMS_TEMPLATE = ROOT / "scripts" / "S447_fig6_claims_template.md"


def unread_commit_notes(man, rids):
    """For the runs rids of a records manifest, a note for each commit the mirror did not read itself (mirror
    --from-copy: a Studio clone's commit as an earlier manifest read it over ssh, or a run's commit carried from the
    last manifest), so claims.md does not state as read what was carried (review of 22 October, defect 5). A commit
    read by git rev-parse in that mirror, or a manifest with no commit_read (a mirror over ssh), gives no note."""
    carried = {x.split(": ", 1)[0]: x.rsplit(" (", 1)[-1].rstrip(")")
               for x in (man["provenance"].get("from_copy") or {}).get("run_commit_from_last_manifest", [])}
    commit_read = {s["clone"]: s.get("commit_read", "") for s in man["sources"]}
    notes = set()
    for rid in rids:
        r = man["runs"][rid]
        cm = r["clone_commit"][:9]
        how, _, when = commit_read.get(r["clone"], "").partition(", ")
        if rid in carried:
            notes.add(f"{cm}: carried for the run from {carried[rid]}, not read again, so not yet checked as the "
                      f"commit that wrote it")
        elif how and how != "git rev-parse HEAD":
            notes.add(f"{cm}: the commit {r['clone']} had at {when}, read over {how}; not read again, so not yet "
                      f"checked as the commit that wrote these runs" if when else
                      f"{cm}: {r['clone']}'s commit from an earlier manifest, where it was read {how}")
    return sorted(notes)


def commit_note_cases(notes_fn=None):
    """unread_commit_notes() (or notes_fn, for a mutant) on a synthetic manifest written by mirror --from-copy: a run
    of a Studio clone whose commit an earlier manifest read over ssh gets the note, a laptop run read by git rev-parse
    gets none, a carried run gets the carried note, and a manifest written over ssh gets none. Returns (problems,
    cases)."""
    notes_fn = notes_fn or unread_commit_notes
    w = "the manifest of 2026-10-16T21:27:40Z"
    man = {"provenance": {"from_copy": {"run_commit_from_last_manifest": [f"r3: e89eaf5cb ({w})"]}},
           "sources": [{"clone": "~/s", "commit_read": f"ssh, {w}"},
                       {"clone": "~/l", "commit_read": "git rev-parse HEAD, 2026-10-22T12:02:17Z"}],
           "runs": {"r1": {"clone": "~/s", "clone_commit": "6457ae69c" + "0" * 31},
                    "r2": {"clone": "~/l", "clone_commit": "6457ae69c" + "0" * 31},
                    "r3": {"clone": "~/l", "clone_commit": "e89eaf5cb" + "0" * 31}}}
    ssh = {"provenance": {"from_copy": None}, "sources": [{"clone": "~/s"}], "runs": {"r1": man["runs"]["r1"]}}
    got = [notes_fn(man, ["r1"]), notes_fn(man, ["r2"]), notes_fn(man, ["r3"]), notes_fn(ssh, ["r1"])]
    want = [[f"6457ae69c: the commit ~/s had at {w}, read over ssh; not read again, so not yet checked as the commit "
             f"that wrote these runs"], [],
            [f"e89eaf5cb: carried for the run from {w}, not read again, so not yet checked as the commit that wrote "
             f"it"], []]
    return [f"case {i + 1}: {g}, want {x}" for i, (g, x) in enumerate(zip(got, want)) if g != x], len(want)


def claims(argv):
    """findings/figures_provisional/fig6/claims.md from scripts/S447_fig6_claims_template.md: every {{expression}} is
    evaluated over fig6_numbers.json (S447 draw) and S445's audit; the Where and Claimed columns are the template's.
    Refused unless fig6_numbers.json and figure6_provenance.json (S447 figure) carry the same data stamp and
    records_manifest.json is the one draw read (its commit notes, unread_commit_notes()), and refused once every
    attempt is stored (the final list needs its statuses decided afresh, not carried)."""
    import re
    N = json.loads((OUT / "fig6_numbers.json").read_text())
    plate = json.loads((OUT / f"figure{FIG_N}_provenance.json").read_text())
    if N["stamp"] != plate["stamp"]:
        raise SystemExit(f"fig6_numbers.json ({N['stamp']}) and the plate ({plate['stamp']}) are of different data "
                         f"states: run draw and figure on the same records first")
    cs, V = N["claims_support"], N["panel_b_variant_order_and_pooled"]
    n, T = N["records"]["attempts"], N["design"]["attempts"]
    if n == T:
        raise SystemExit("every attempt is stored: the final claims list needs its statuses decided, not carried")
    done = cs["complete_variants"]
    cells = {(x["variant"], x["strategy"]): x for x in N["panel_b_cells"]}

    def lab(v):
        return f"{VMODEL[v]} {VTHINK[v]}" if sum(1 for _, m, _ in VARIANTS if m == VMODEL[v]) > 1 else VMODEL[v]

    def c(x):
        return f"{x:,}"

    def f1(x):
        return "none" if x is None else half_up(x, 1)

    def f2(x):
        return half_up(x, 2)

    def sgn(x):
        return half_up(x, 1, sign=True)

    def stored(v):
        return V[v]["attempts"]

    def sm(s):
        return f1(cs["strategy_mean_over_complete_variants"][s])

    def top_strategy():
        m = cs["strategy_mean_over_complete_variants"]
        best = max(m.values())
        return [s for s, x in m.items() if x == best]

    def mc(key, short=False):
        r = cs[key]
        d = 100 * (r["a_only"] - r["b_only"]) / r["pairs"]
        p = "none" if r["p_two_sided"] is None else f2(r["p_two_sided"])
        return f"{sgn(d)} points, P = {p}" + ("" if short else f", n = {r['pairs']} pairs")

    def outside(v):
        r = cs["outside_structured_by_variant"][v]
        return (f"{f1(r['pass_rate_pct'])}%, {r['attempts']} of {r['of']}" + ("" if r["attempts"] == r["of"]
                                                                               else " stored")) if r["attempts"] \
            else "none stored"

    def outside_pair(v_off, v_on):
        a, b = outside(v_off), outside(v_on)
        return "none stored" if a == b == "none stored" else f"off {a}; reasoning {b}"

    def pooled(v):
        return f"{f1(V[v]['pass_rate_pct'])}%, {V[v]['attempts']} of {PER_VARIANT} stored"

    def c_row(v):
        t = N["panel_c_thinking"].get(VMODEL[v], {})
        if t.get("variants_with_data", 0) < 2:
            return None
        return next((r for r in t["variants"] if r["variant"] == v and r["matched_attempts"]), None)

    def plate_c(v):
        """What plate c draws for this variant: Rule 2's mean of the operations' shares on the matched attempts."""
        r = c_row(v)
        if r is None:
            return "plate c: not drawn (no second setting of the model stored)"
        return (f"plate c (Rule 2: mean of the {r['operations_n']} operations' shares, on the "
                f"{r['matched_attempts']} matched attempts): {f1(r['op_mean_pass_rate_pct'])}% (95% interval "
                f"{f1(r['op_boot95_lo'])} to {f1(r['op_boot95_hi'])})")

    def strategies_desc(v):
        st = cs["strategies_stored_by_variant"].get(v, {})
        return f"{len(st)} strategies: " + ", ".join(f"{s} {k}" for s, k in st.items())

    rer = cs["reruns_owed"]["by_variant"]

    def owes(v):
        r = rer.get(v, {})
        parts = []
        if r.get("failed_owing_d80v1_rerun"):
            k = r["failed_owing_d80v1_rerun"]
            parts.append(f"{k} failed attempt{'s owe' if k != 1 else ' owes'} the D80 V1 rerun")
        if r.get("failed_with_add_cell_as_text_d81"):
            k = r["failed_with_add_cell_as_text_d81"]
            parts.append(f"{k} add_cell-as-text attempt{'s owe' if k != 1 else ' owes'} the D81 rerun")
        return "; ".join(parts) or "no rerun owed"

    def listing(key, sub=None):
        xs = sorted(((r.get(key, 0), v) for v, r in rer.items() if r.get(key)), key=lambda t: -t[0])
        return ", ".join(f"{lab(v)} {k}" + (f" ({'parse' if rer[v].get(key + ': parse') else 'stall'})" if sub else "")
                         for k, v in xs)
    tot = cs["reruns_owed"]["totals"]
    rer_d80 = (f"{tot.get('failed_with_d80v1_event', 0)} failed attempts met a tool-call parse error or a stall: "
               f"{listing('failed_with_d80v1_event', sub=True)}. "
               + ("No Ollama call met an HTTP 500 or a dropped connection. " if not tot.get(
                   "failed_with_d80v1_event: retry_call_error") else "")
               + (f"Apart, {tot['passed_with_d80v1_event']} attempts passed although a call met such an event: "
                  f"{listing('passed_with_d80v1_event')}." if tot.get("passed_with_d80v1_event") else ""))
    both = tot.get("failed_with_add_cell_as_text_and_d80v1_event", 0)
    rer_d81 = (f"{tot.get('failed_with_add_cell_as_text', 0)} failed attempts wrote add_cell as text: "
               f"{listing('failed_with_add_cell_as_text')}; {both or 'none'} of them also owe{'s' if both == 1 else ''}"
               f" D80 V1. "
               + (f"Apart, {tot['passed_with_add_cell_as_text']} passing attempts did the same "
                  f"({listing('passed_with_add_cell_as_text')}); see open item R4 for the call sites counted."
                  if tot.get("passed_with_add_cell_as_text") else ""))
    with_d80 = sorted({cm for r in rer.values() for cm, has in r["clone_commits_have_d80"].items() if has})
    # a commit the mirror did not read (mirror --from-copy: a Studio clone's, or a run's carried from the last
    # manifest) is said to be so, with where it was read (review of 22 October, defect 5)
    man = json.loads(MANIFEST.read_text())
    if sha256_file(MANIFEST) != N["provenance"]["inputs_sha256"].get(str(MANIFEST.relative_to(ROOT))):
        raise SystemExit(f"{MANIFEST.name} has changed since draw: run draw and figure on the same records first")

    def wrote(v):
        notes = unread_commit_notes(man, [rid for rid, r in man["runs"].items() if variant_of(rid) == v and
                                          rer[v]["clone_commits_have_d80"].get(r["clone_commit"][:9])])
        return lab(v) + (f" ({'; '.join(notes)})" if notes else "")
    d80_runs = [wrote(v) for v, r in rer.items() if any(r["clone_commits_have_d80"].values())]
    d80_commits = ("every clone commit in the manifest predates D80 (`clone_commits_have_d80` false), so every stored "
                   "attempt ran without the D80 V1 retry" if not with_d80 else
                   f"every clone commit in the manifest predates D80 except {', '.join(with_d80)} "
                   f"(`clone_commits_have_d80`), the commit the manifest records for {', '.join(d80_runs)}; every "
                   f"other stored attempt ran without the D80 V1 retry")
    # D75 S4 from S445's audit (the records it read, an earlier data state than this list's)
    s4, q62, s445_n = Counter(), set(), 0
    for m in ("studio", "laptop"):
        r = json.loads((S445 / f"{m}.json").read_text())
        s445_n += r["n_attempts"]
        for k, x in r["cards_by_treatment"].items():
            s4[k.split("\t")[0]] += x
        q62 |= {(x["run_id"], x["answer_key"]) for x in r["q62_calls"]}
    s445_s4 = (f"Q62 {len(q62)} structured attempts across {len({variant_of(a) for a, _ in q62})} variants, "
               + ", ".join(f"{k} {s4[k]}" for k in sorted(s4) if k != "Q101")
               + f" (S445's audit, `findings/recompute/S445_s2_d75_audit/`, over the {c(s445_n)} attempts it read; "
                 f"Q101 changes only the record, {s4.get('Q101', 0)} attempts)")
    d_vs = N["design"].get("variant_list") or [v for v, _, _ in VARIANTS]     # D100, D112 Q15 O-a
    incomplete = [v for v in d_vs if not V[v]["complete"]]
    incomplete_desc = ((f"{len(incomplete)} of {len(d_vs)} are incomplete, attempts stored of {PER_VARIANT}: "
                        + ", ".join(f"{lab(v)} {stored(v)}" for v in incomplete)) if incomplete else
                       f"none of the {len(d_vs)} is incomplete; nemotron-3-nano:30b was removed by D116")

    def group(vs):
        by = defaultdict(list)
        for v in vs:
            by[VMODEL[v]].append(VTHINK[v])
        return ", ".join(m + (" " + " and ".join(t) if sum(1 for _, mm, _ in VARIANTS if mm == m) > 1 else "")
                         for m, t in by.items())
    gains = cs["introspection_best_minus_free_form_pts"]

    def gain_range():
        return f"{sgn(min(gains.values()))} to {sgn(max(gains.values()))}"

    def gains_grouped():
        by = defaultdict(list)
        for v, g in gains.items():
            by[g].append(v)
        return ", ".join(f"{sgn(g)} ({group(vs)})" for g, vs in sorted(by.items()))

    def lowest_four():
        vs = sorted(done, key=lambda v: V[v]["pass_rate_pct"])[:4]
        return ", ".join(f"{lab(v)} ({sgn(gains[v])})" for v in vs)

    st = cs["structured_by_variant"]

    def no_code_desc():
        out = []
        for v in ("deepseek-r1-70b+default", "gemma3-27b+default", "nemotron-3-nano-30b+default",
                  "nemotron-3-nano-30b+off"):
            if v in REMOVED:
                if v == "nemotron-3-nano-30b+default":
                    out.append("nemotron-3-nano:30b removed from every experiment (D116), not reported")
                continue
            if v not in st:
                out.append(f"{lab(v)} none stored")
                continue
            r = st[v]
            ran = [s for s, k in cs["strategies_stored_by_variant"].get(v, {}).items() if s.startswith("coder_v2")]
            out.append(f"{lab(v)} structured: {r['records_with_no_code']} of {r['attempts']} records hold no code "
                       f"({', '.join(ran)} stored; {4 - r['complete_cells']} of the 4 structured strategies not "
                       f"complete)")
        return "; ".join(out)

    def best_structured(v):
        rs = [(cells[(v, s)]["pass_rate_pct"], SLAB[s]) for s, _ in STRATEGIES
              if s.startswith("coder_v2") and cells[(v, s)]["attempts"]]
        b = max(r for r, _ in rs)
        return ", ".join(lab for r, lab in rs if r == b)

    def kind(v, k):
        return sum(cells[(v, s)][f"kind: {k}"] for s, _ in STRATEGIES)

    def deepseek_structured():
        v = "deepseek-r1-70b+default"
        cs_ = [cells[(v, s)] for s, _ in STRATEGIES if s.startswith("coder_v2") and cells[(v, s)]["attempts"]]
        f = sum(x["fail"] for x in cs_)
        ks = Counter()
        for x in cs_:
            for k in KINDS_ALL:
                ks[k] += x[f"kind: {k}"]
        return (f"deepseek's {f} failed structured records: {ks['tool-call parse error']} parse errors, "
                + ", ".join(f"{x} {k}" for k, x in ks.most_common() if x and k != "tool-call parse error"))

    def deepseek_cv2n1():
        x = cells[("deepseek-r1-70b+default", "coder_v2_n1")]
        return f"deepseek coder_v2_n1 {x['pass']} of {x['attempts']}"

    th = N["panel_c_thinking"]

    def matched(m):
        return th[m]["variants_with_data"] >= 2

    def think_desc(m):
        t = th[m]
        rows = [r for r in t["variants"] if r["matched_attempts"]]
        by = ", ".join(f"{x} with {k}" for k, x in sorted(t["operations_by_attempts"].items(),
                                                          key=lambda kv: int(kv[0])))
        return (f"{m} matched on {t['matched_on']} attempts over {t['operations_n']} operations ({by}); pass rate as "
                f"Rule 2's mean of the operations' shares: "
                + ", ".join(f"{r['thinking']} {f1(r['op_mean_pass_rate_pct'])} (95% interval "
                            f"{f1(r['op_boot95_lo'])} to {f1(r['op_boot95_hi'])})" for r in rows))
    gr = cs["generator_reasoning_by_variant"]

    def reasoning_desc():
        out = []
        for v in ("gpt-oss-20b+low", "gpt-oss-20b+medium", "gpt-oss-20b+high"):
            r = gr.get(v)
            if r:
                out.append(f"{VTHINK[v]} {c(r['returned_reasoning_text'])} of {c(r['generator_calls'])}"
                           + (f" ({f1(100 * r['returned_reasoning_text'] / r['generator_calls'])}%)"
                              if v.endswith("low") else ""))
        return "Generator calls that returned reasoning text: " + ", ".join(out)

    def machines_desc():
        by = defaultdict(list)
        for v, ms in cs["attempts_by_machine"].items():
            for k, x in ms.items():
                by[k.split()[0]].append((v, x))
        lap = by.get("laptop", [])
        return (", ".join(f"{lab(v)} ({x} attempts)" for v, x in lap) + " ran on the laptop; the other "
                f"{len(by.get('studio', []))} variants with records on the Studio")

    def ref_desc(ds):
        r = cs["reference_values_op1"]
        if ds == "airway":
            x = r["airway_1_dimensions"]
            return f"{x['samples']} samples, {c(x['genes'])} genes"
        x = r["lung_1_dimensions"]
        return f"{x['n_patients']} patients, {x['n_variables']} variables"

    def ref_genes():
        return c(cs["reference_values_op1"]["airway_1_dimensions"]["genes"])

    def tiers():
        t = cs["operations"]["by_complexity"]
        return ", ".join(str(t.get(k, 0)) for k in ("simple", "medium", "complex"))

    def no_code_cells():
        xs = cs["cells_where_no_record_produced_code"]
        return (f"{len(xs)} cell{'s' if len(xs) != 1 else ''} so far ("
                + ", ".join(f"{lab(v)} {s}, {k} records" for v, s, k in xs) + ")")

    rpm = cs["records_per_model"]

    def stored_models(ms):
        return ", ".join(str(rpm[m]["stored"]) for m in ms)

    def models_incomplete(ms):
        return sum(1 for m in ms if rpm[m]["stored"] < rpm[m]["design"])

    def fields(key):
        return " / ".join(f1(cs[key][f]) for f in ("judge_score", "passed", "field_results", "exec_error"))

    def temps_desc():
        by = defaultdict(list)
        for v, t in cs["best_of_3_candidate_temperature_sent"].items():
            for k in t:
                by[k].append(v)
        return ", ".join(f"{k} ({'all others' if len(vs) == max(len(x) for x in by.values()) else group(vs)})"
                         for k, vs in sorted(by.items()))

    def best3_stored():
        return sum(x["attempts"] for (v, s), x in cells.items() if s == "free_form_n3_best")

    def dates(prov):
        lo, hi = N["records"]["generator_call_dates_by_provider"][prov]
        fmt = lambda s: dt.datetime.fromisoformat(s).strftime("%-d %b %Y %H:%M")
        return f"{fmt(lo)} to {fmt(hi)}"

    ns = {"N": N, "cs": cs, "np": N["provenance"], "stamp": N["stamp"], "n": n, "T": T, "NV": len(d_vs),
          "nc": len(done), "ni": len(incomplete), "c": c, "f1": f1, "f2": f2, "sgn": sgn, "sm": sm,
          "top_strategy": top_strategy, "mc": mc, "outside": outside, "outside_pair": outside_pair,
          "stored": stored, "pooled": pooled, "plate_c": plate_c, "strategies_desc": strategies_desc, "owes": owes,
          "rer_d80": rer_d80, "rer_d81": rer_d81, "d80_commits": d80_commits, "s445_s4": s445_s4,
          "incomplete_desc": incomplete_desc, "complete_desc": group(done), "gain_range": gain_range,
          "gains_grouped": gains_grouped, "lowest_four": lowest_four, "no_code_desc": no_code_desc,
          "best_structured": best_structured, "kind": kind, "deepseek_structured": deepseek_structured,
          "deepseek_cv2n1": deepseek_cv2n1, "matched": matched, "think_desc": think_desc,
          "reasoning_desc": reasoning_desc, "machines_desc": machines_desc, "ref_desc": ref_desc,
          "ref_genes": ref_genes, "tiers": tiers, "no_code_cells": no_code_cells, "stored_models": stored_models,
          "models_incomplete": models_incomplete, "fields": fields, "temps_desc": temps_desc,
          "best3_stored": best3_stored, "dates": dates,
          "ds_desc": ", ".join(f"{d.replace('_cancer', '')} {k}" for d, k in cs["operations"]["by_dataset"].items()),
          "n_ollama": sum(1 for v in d_vs if not v.startswith("gemini")),
          "n_gemini": sum(1 for v in d_vs if v.startswith("gemini")),
          "chi_desc": (f"chi-square({N['interaction_chi2']['df']}) = {f1(N['interaction_chi2']['chi2'])}, "
                       f"P = {f2(N['interaction_chi2']['p'])}") if N["interaction_chi2"] else "none",
          "sinks": len(json.loads(MANIFEST.read_text())["runs"]),
          "written": utc_now(),
          "dirty": " (the script uncommitted)" if N["provenance"]["script_dirty_vs_head"] else ""}
    # the largest provisional gaps: (row, claim, text value, provisional value), sorted by the size of the gap; the
    # gap is the exact provisional value less the text's (exact(), so 54.25 - 33.2 = 21.05 prints +21.1), rounded once
    smo = cs["strategy_mean_over_complete_variants"]
    pooled_ = N["pooled_structured_vs_free_form"]
    hc = c_row("gpt-oss-20b+high")
    gl = [("A25", "gpt-oss high at 24,576 (now 131,072); plate c's value", 33.2,
           hc["op_mean_pass_rate_pct"] if hc else None,
           f" (plate c, Rule 2, {hc['matched_attempts']} matched attempts; pooled over the "
           f"{V['gpt-oss-20b+high']['attempts']} stored, {f1(V['gpt-oss-20b+high']['pass_rate_pct'])}%)" if hc
           else ""),
          ("A26", "top of the introspection range", 35.0, max(gains.values()), ""),
          ("A26", "bottom of the introspection range", -15.0, min(gains.values()), ""),
          ("A17", "free-form combined", 57.0, smo["free_form_n3_combined"], ""),
          ("A13", "error-recovery introspection", 62.7, smo["error_recovery_introspect"], ""),
          ("L6", "free-form family pooled", 61.9, pooled_["free_form_family"]["pass_rate_pct"], ""),
          ("A11", "best-of-3", 65.0, smo["free_form_n3_best"], ""),
          ("L6", "structured output pooled", 49.9, pooled_["structured_family"]["pass_rate_pct"], ""),
          ("A12", "free-form", 63.7, smo["free_form"], ""),
          ("A22", "gpt-oss medium outside structured (not drawn; plate c draws the matched rate)", 60.0,
           cs["outside_structured_by_variant"]["gpt-oss-20b+medium"]["pass_rate_pct"],
           f" ({cs['outside_structured_by_variant']['gpt-oss-20b+medium']['attempts']} of 140)"),
          ("A21", "gpt-oss low outside structured (not drawn; plate c draws the matched rate)", 72.9,
           cs["outside_structured_by_variant"]["gpt-oss-20b+low"]["pass_rate_pct"], "")]
    gl = [g for g in gl if g[3] is not None]
    gl.sort(key=lambda g: -abs(g[3] - g[2]))
    pct_rows = {"A26"}
    ns["gaps_table"] = "\n".join(
        ["| Row | Claim | Text | Provisional | Gap |", "|---|---|---|---|---|"]
        + [f"| {r} | {what} | {sgn(t) if r in pct_rows else f1(t) + '%'} | "
           f"{(sgn(p) if r in pct_rows else f1(p) + '%') + extra} | {sgn(exact(p) - exact(t))} |"
           for r, what, t, p, extra in gl[:10]])

    tpl = CLAIMS_TEMPLATE.read_text()

    def ev(m):
        return str(eval(m.group(1), {"__builtins__": {"str": str, "len": len, "max": max, "min": min}}, ns))
    ns["summary"] = "{{summary}}"
    body = re.sub(r"\{\{(.+?)\}\}", lambda m: "{{summary}}" if m.group(1) == "summary" else ev(m), tpl)
    # the summary, counted from the rendered rows: each row once, under the first status its Status cell gives
    statuses = {"not yet measurable": r"not yet measurable", "no longer applies": r"no longer applies",
                "matches": r"\bmatch(es)?\b", "differs": r"\bdiffers\b"}
    first, second = defaultdict(list), []
    for ln in body.split("\n## Summary")[0].splitlines():
        m = re.match(r"^\| ([AMLSR]\d+) \|", ln)
        if not m:
            continue
        cell = ln.rstrip().rstrip("|").rsplit("|", 1)[1].strip()
        hits = sorted((x.start(), st) for st, rx in statuses.items() for x in re.finditer(rx, cell))
        if not hits:
            raise SystemExit(f"row {m.group(1)}: no status in {cell!r}")
        first[hits[0][1]].append(m.group(1))
        if len({s for _, s in hits}) > 1:
            second.append(f"{m.group(1)} ({', '.join(dict.fromkeys(s for _, s in hits[1:]))})")
    rows_n = sum(len(x) for x in first.values())
    summary = "\n".join(
        [f"{rows_n} claims, each counted once under its first status:", "",
         "| Status | Rows | Which |", "|---|---|---|"]
        + [f"| {s} | {len(first[s])} | {' '.join(first[s])} |" for s in ("matches", "differs", "not yet measurable",
                                                                         "no longer applies")]
        + ["", f"Rows that also carry a second status: {', '.join(second) if second else 'none'}."])
    body = body.replace("{{summary}}", summary)
    if "{{" in body:
        raise SystemExit("a placeholder is left unrendered")
    (OUT / "claims.md").write_text(body)
    print(f"claims.md: {rows_n} rows from {CLAIMS_TEMPLATE.relative_to(ROOT)}, data stamp {N['stamp']}; "
          + ", ".join(f"{s} {len(first[s])}" for s in ("matches", "differs", "not yet measurable",
                                                      "no longer applies")))


# ---------------------------------------------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------------------------------------------
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=["mirror", "draw", "figure", "claims", "selftest"])
    ap.add_argument("--final", action="store_true", help="figure: name the files 'Figure 6' (refused unless every "
                                                          "attempt of the design is stored: design_of())")
    ap.add_argument("--view-dir", type=Path, help=f"draw: the folder of the working view, outside the repository "
                                                  f"(default {VIEW_DIR}; D92 Q195)")
    ap.add_argument("--from-copy", type=Path, help="mirror: read the four clones' sinks from this local copy (S468's "
                                                   "layout, with copy_log.tsv and SHA256SUMS) instead of the clones")
    ap.add_argument("--complete-only", action="store_true", help="mirror (with --from-copy): only the variants with "
                                                                 "all 220 attempts stored (D114 Q30 O-a)")
    args = ap.parse_args(argv)
    if args.step == "mirror":
        mirror(argv, args.from_copy, args.complete_only)
    elif args.step == "draw":
        draw(argv, args.view_dir)
    elif args.step == "claims":
        claims(argv)
    elif args.step == "selftest":
        selftest(argv)
    else:                                         # D138 (25 October): Figure 6 is S481's plate; this one would
        raise SystemExit("S447 figure is superseded by D138: Figure 6 and its Supplementary figures are drawn by "
                         "uv run --frozen python scripts/S481_fig6_d138.py all (this step's plate, panels a to d "
                         "of 16 October, would overwrite them; its code stays for selftest)")


if __name__ == "__main__":
    main()
