#!/usr/bin/env python3
"""S472 - Figure 4 (orchestration): the provisional plate of D132 with G9's two stress set-ups (D163), drawn from G3's
and G9's draw-1 answer records, S3's judge rows of those answers, and RLM-10's draw-1 answers and judge rows (G1,
Figure 3's answers). Figure 4's spec: findings/audits/figure_design_2026-11-01/spec/fig4.md.

WHY. Valerio, 22 October: "update now all the figures so I can start reviewing them". D82 (experiments/README.md): a
panel is drawn as soon as its data exist, by a committed script from the raw records, stamped with how much data it
holds; the final panel is the same script run again. D84: exploratory phase, the results are drawn as they are and no
analysis rule is written here; every statistic below is one LIST.md already states, cited where it is computed. G3
(plan row G3; findings/recompute/G3_runs/README.md) answered Figure 4's eight wave-1 set-ups on draw 1 (D98 stopped
each at the end of draw 1; raw_gemini and naive_rag hold all three draws). S3 judged G3's draw 1 (collect of 24
October). D132 (Valerio, 24 October, "Figure 4 all recommended but for F alt 2") chose the panels drawn here.
D188 (Valerio, 31 October: every figure moves to key v2.5): every judge row drawn is read through
scripts/judge_rows_v25.py. RLM-10's rows come from S463.judge_rows with the frozen set findings/recompute/fig3_s6_inputs
(S528: out_s6_g1 with out_s6_g1r15 after phase 3, the rows Figure 3 reads), and read_rlm refuses a set that leaves any
of its answers of changed questions on key v2.4. G3's rows take an answer's key v2.5 row (S512's re-judging: out_s6_g3,
frozen in findings/recompute/fig3_s6_inputs by S528 --add, D203, 2 November) where one exists, else its key v2.4 row; an
answer still read from key v2.4 is counted as awaiting S6 in the stamp, the legend draft and the provenance
(judge.judge_rows_v25).

WHAT IS DRAWN (D132; all on draw 1, D98's analysis rule: main estimates from draw 1 on all questions). Eleven set-ups:
no retrieval, naive RAG, the full pipeline, no analyser, no planner, no supervisor, no synthesizer, the routing fix
(G3), always distil and always distil F1 (G9; D163, no test), and RLM-10 (G1; D83 Q148). G9's rows read
findings/recompute/g9_inputs, the frozen answers.json of each set-up; their judge rows (S3, set G3, 27 October) and
their retrievals.jsonl are in findings/recompute/fig4_g9_inputs (this script's pull-judge and pull --g9-retrievals of
3 November, frozen with their own SHA256SUMS), so a, c and d draw them. A plate built from a collect with no G9 rows,
or with no retrievals given, still prints "judge rows not copied" in a and c and "search time not copied" in d; those
two texts must not reach the submitted plate. D219 (Valerio, 3 November): the panel of words per answer is dropped
(no paragraph of the story uses it); model calls and own time move up from e and f to d and e. D250 (Valerio, 4 November
22:47, the layout of option 2b approved): old 4b moves to Supplementary Figure 10a, a goes full width, the refusal tiles
lose their margin and false-premise column, the cost panel moves up beside them, and G17 takes the bottom row. Sheets
keep their internal keys (a, b, c, d, e, f) in this script; PLATE_LETTER maps them to the plate's letters (a, -, b, c,
d, e), and sheet b goes to STEPS_OUT for Supplementary Figure 10a, not into Figure 4's workbook. Panels by internal key,
with the plate letter:
  a  (P-1) the 86 answerable questions by set-up as tiles in one shared column order (most set-ups passing at score 4
     on the left, then at score 3, then the question id), each tile coloured by the judge's correctness in three
     cividis levels, the larger score the lighter (D171 (1): 4 or 5 yellow; 3; 2 or less, or no answer, dark); a tile
     whose judge call gave no score would be grey. At the right: the pass rate at score 4 or more with Rule 2's 95%
     interval (S463.summarise). Source Data only, not drawn (Valerio's note of 2 November on a): each orchestrator
     set-up, each stress set-up and RLM-10 minus the full pipeline at score 4 with its Rule 2 interval (S463.pairs,
     S463.pair); P, the exact two-sided sign-flip test (Rule 3), Holm-adjusted over the five orchestrator set-ups
     (Rule 12's zero branch) and unadjusted for RLM-10 (claim P1, on its own); vs_full_text writes the legend's
     sentence on them from their values, in Rule 11's words ("detected", with the interval). The two baselines get no
     difference and no P (Rule 12: descriptive); the two stress set-ups get a difference and no P (D163; FAMILY stays
     the five). Score 3, the relaxed threshold (D154; pass rate, interval, difference, P), and the gained, lost and
     same counts are in Source Data only (FF17: no plate). Once S6G7G3 has been copied beside the G3 outs, the sheet
     also holds 66 'draw' rows (FF30, read_draw_rows, draw_rows): passed and questions per set-up, draw 1 to 3 and
     threshold 4 and 3, on the 29 answerable questions of D98's 45. Until then they stay out and the stamp says so.
  b  (F-2; on no plate of Figure 4 since D250) the cumulative share of the plan step attempts of the six orchestrator
     set-ups, pooled, at or under each raw output length (characters), with the distiller threshold (0.40 x LOCK
     num_ctx x 4 = 209,712; experiments/mentori/orchestrator/distiller_firing.py). Its rows are written to STEPS_OUT
     (steps_file), which scripts/S524_t3_s12_s13.py draws as Supplementary Figure 10a. G9's step counts are in the
     provenance only (stress_steps).
  c  (plate b; R-1 as D250 set it) the 39 out-of-scope questions by set-up as tiles in one shared column order (most
     set-ups refusing on the left, then the question id), light when refused (refusal accuracy 3 or more, Rule 9;
     S463.REFUSAL_T), dark when not (D171 (1)); a dot where the analyser sent the question to a direct answer
     (generation.analysis.decision == "direct_answer"; no dot for no retrieval, naive RAG, RLM-10, and for no
     analyser, whose records carry generation.analysis.status "switched_off" and whose stored decision is therefore
     not read as a routing). Right of them, the 10 false-premise questions as tiles of their own, white, a pass
     (correctness 4 or more, Rule 9 as D160 (11) set it) outlined in vermillion (D250: "color the single tile of
     question with red outline for false premise pass"). The refusal rate with Rule 2's interval and the one-sided
     bounds of a 0 or a 100% (S463.full_bound, O2 of 24 October) stay in the sheet, no longer drawn (D250). The sent
     and refused counts are in Source Data only (variant A1 of fig4-Q1), with 110 'fp_tile' rows, one per set-up and
     false-premise question.
  d  (plate c; first author, 4 November 2026: the d and e of D219 merged into one cost panel; D250: moved up beside
     the refusal tiles, on their set-up rows, which label it) per set-up, two box columns: at the left, model calls per answer (G3 and G9: generation.llm_calls,
     equal to its call records; RLM-10: its generation.calls entries, equal to llm_calls); at the right, each
     answer's own time (D83 Q150): its model calls' wall_s plus its search time, read from the sink's retrievals.jsonl
     between the answer's generation.retrievals_bytes offsets as exp_03's answer_search_s() states (re-implemented
     here: answer_search_s below, the same rule; exp_03 imports Mentori and is not loaded). exp_03's rule for RLM-10 is
     the sum of search_s over generation.rlm.metadata.retrievals, but G1's frozen records hold no search_s in any
     entry of that log, so RLM-10 has no time: its row of the time column prints "no search time". Each column: the
     house box (hs.boxplot: median, first and third quartile, whiskers to the smallest and largest value; no mean)
     over one grey dot per answer, placed apart by hs.swarm, on a log axis; above it the answers drawn, from sheet d's
     'total' row of that measure. Failed calls (a status other than ok and length, Rule 10) and calls cut at the
     output limit (length), counted in calls, were two number columns at d's right until 4 November; they are in
     sheet d only. Words per answer stay computed (compute, fn["answers"]) because S480's recount compares them
     (stress_records); they are in no sheet and on no panel.
  e  (plate d; D250, option 2b of findings/recompute/fig4_g17_drafts; G17, D240, D239 amended: the ablation as an
     investigative tool, descriptive, no ranking) concept recall per answerable question, each question's mean over
     draws 1 to 3, for RLM-10 (Mentori's, rerun), the Zhang RLM-10 (G6's draws, as S576 reads them), search tools
     off and quality gate off (D293: that order, no word "control"), one house box per arm and question type (one-paper left, many-paper right): median
     line, box Q1 to Q3, whiskers to the range, every question a dot in the arm's colour and shape; no mean, no
     interval. Read from S571's g17_d123 reading through S576.per_answer and question_means (read_g17), which first
     requires S576's file to name the reading and S575's contrasts by sha256 and its descriptive contrasts and arm
     means on draws 1 to 3 to equal S576.evaluate() and arm_means() run again. The legend quotes S576's paired
     differences of each arm minus the control on concept recall (sheet d's 'difference' rows, Source Data only).
  f  (plate e; D250, option 2b) per draw-1 answer, the sub-calls that returned paper text and the distinct papers
     read, the same boxes, on an axis linear to 2 and logarithmic above (matplotlib's symlog, linthresh 2, drawn in
     its own units so hs.swarm's spacing holds).
Not drawn (pending, listed in legend_draft.md): the component benchmarks and distiller prompts (T3, scripts/
S524_t3_s12_s13.py, Supplementary Figures 10b to 10d and 11).

THE ONE COMMAND (D155) that rebuilds the committed plate from the frozen inputs, every file byte for byte (S494 calls
it; scripts/S480_fig4_recount.py's one command first, since this plate checks its counts against S480's output):

  uv run --frozen python scripts/S472_fig4_panels.py figure

  With no input path given, figure reads the frozen copies through scripts/fig_repro.frozen() (FROZEN below):
    --records      fig4_records_1023.tar, folder fig4_records_1023 (this script's pull of 23 October)
    --collect      findings/recompute/fig4_g9_inputs/g3_collect.jsonl (pull-judge of 3 November: G3's collect with G9's
                   270 rows, out_g3 beside it; the set's own SHA256SUMS). The collect of 24 October (fig4_inputs,
                   41d3105d) stays the anchor of pull-judge's and reproduce_new's reproduction
    --g9-retrievals findings/recompute/fig4_g9_inputs/g9_retrievals/findings/runs (pull --g9-retrievals of 3 November)
    --rlm-collect  findings/recompute/fig2_inputs/g1_collect.jsonl (G1's collect of 23 October, out and out_g1r15)
    --rlm-answers  fig2_g1r15_inputs.tar, folder fig2_g1r15_inputs/runs (MANIFEST.sha256 beside it)
    --g9           findings/recompute/g9_inputs (G9's two answers.json, PULL.json; S1 of the pull of 26 October)
    --s6-g1        findings/recompute/fig3_s6_inputs (S528: RLM-10's key v2.5 rows, checked against its own SHA256SUMS)
  A tar is read from env FROZEN_TARS (default ~/Mentori_scratch_keep/frozen_2026-10-26; after the deposit, the folder
  its tars were downloaded to), checked against findings/recompute/frozen_inputs/SHA256SUMS and extracted once into
  the gitignored findings/recompute/frozen_inputs/extracted/. Before anything is read: every pinned file (FROZEN_PIN:
  PULL.json, both collects and sidecars, RLM-10's MANIFEST and answers files) must have the sha256 the committed plate
  of 26 October recorded, and the committed sets fig4_inputs, fig2_inputs and g9_inputs must equal SHA256SUMS file by
  file (else it stops, nothing written). The collects' sidecars name the folders collect read, in the session
  scratch; figure reads them as the folders of the same names beside each frozen collect (collect_view). The outputs
  carry no time: the workbook through fig_repro.deterministic_xlsx, the PDF and SVG checked by fig_repro (no date;
  S457's plate_rc fixes the SVG ids), the provenance with no write time, HEAD or working-tree state (each input and
  output by sha256).
  The design documents and run code the plate reads or records (DESIGN_DOCS: plan.csv, experiments/LIST.md and
  README.md, exp_03, distiller_firing.py, the main text and the letter) are read as they stand in the working tree by
  every check and lookup: reproduce (2) reads plan.csv's row G3, claims.md finds each claim in the main text, the
  letter and LIST.md as they stand, and distiller_firing.py is imported from the working tree. Only inputs_sha256
  records them as they stood at DESIGN_AT (96936742, the commit whose files give every sha256 the committed plate
  recorded; git show, read only), their names carrying "@96936742": those files change with every dashboard update,
  decision and letter round, and their sha256 at HEAD changed figure4_provenance.json with nothing in the figure
  changed (audit 27 Oct F1). The values the plate draws from them must be the same as at DESIGN_AT, or the run stops:
  exp_03's STRESS_CONFIG_NAMES (the planned answers), and distiller_firing.py's code less its docstring (reproduce
  (3)). A design change reaches the plate only when DESIGN_AT is moved (then S494 --write). Until 27 Oct, part 4,
  the checks and the claims list also read DESIGN_AT, which switched them off for later edits; they read the working
  tree again, as before the audit.

COMMANDS, from the repository root (uv run only; no model call; nothing on the Studio is written):

  pull     uv run --frozen python scripts/S472_fig4_panels.py pull --to <new dir> [--g9-retrievals]
           Reads G3's records on the Studio through stdin scripts only (ssh <host> bash -s < script): first a listing
           (the clone's HEAD read from its .git files, no git command (D155, the 23 October guards; INVENTORY.md A8),
           each file's sha256, size and mtime), then a tar of the same files on stdout, unpacked
           here with Python's tarfile into <dir>. Each copy must equal the listing's sha256. Files: per wave-1
           set-up, its sink's answers.json, run_identity.json, index_identity.jsonl and retrievals.jsonl (when it
           exists); G3_runs' start, end, launch and relaunch records, g3_draw1_stop.log and smoke_check.json. With
           --g9-retrievals only G9's two retrievals.jsonl (figure reads each answer's own draw-1 offsets, so the lines
           G7 appended later are not read). Writes <dir>/PULL.json. <dir> must be new or empty and is never under
           findings/runs. Not run live when --g9-retrievals was written (2 November).
  pull-judge  uv run --frozen python scripts/S472_fig4_panels.py pull-judge --to <new dir> [--from-copy <out_g3>]
           D155 (INVENTORY.md A6): the G3 judge pull of 24 October, then made by hand (a tar of the S3 clone's
           out_g3 and a local s3_guard.py collect), as a command. REPRODUCES FIRST: s3_guard.py collect --set G3 on
           the frozen fig4_inputs/out_g3 must give the frozen g3_collect.jsonl byte for byte (41d3105d) and its
           sidecar less paths and time (else exit 2, nothing written). Then copies
           ~/projects/mentori-runs-s3/findings/recompute/S3_runs/out_g3 from the Studio through stdin scripts (a
           listing with the clone's HEAD from .git and each file's sha256, then a tar of the listed files), or with
           --from-copy a local out_g3 folder (offline, no ssh), into <dir>/out_g3, checks every copy against the
           listing, runs collect into <dir>/g3_collect.jsonl and writes <dir>/PULL_JUDGE.json. <dir> must be new or
           empty and is never under findings/runs or a frozen set. Not run live when written (26 October): tested
           offline on the frozen copy only. Next: figure --collect <dir>/g3_collect.jsonl.
  figure   uv run --frozen python scripts/S472_fig4_panels.py figure [--records <dir>] [--collect <g3_collect.jsonl>] \
               [--rlm-collect <g1_collect.jsonl>] [--rlm-answers <g1r15_inputs/runs>] [--g9 <g9_inputs>] \
               [--g9-retrievals <dir>] [--s6-g1 <dir>] [--recount <S480 recount>] [--out <folder>] \
               [--steps-out <json>]
           --g9-retrievals: a folder holding <run>/retrievals.jsonl of each stress set-up (default its frozen copy in
           fig4_g9_inputs). Each input not given is its frozen copy (above); one given is read from that path, with no
           pin (a later pull). --out writes the plate into another folder (default findings/figures_provisional/fig4).
           Runs selftest, reads the copies (each sha256 against PULL.json) and checks them. Reads G3's judge rows
           (s3_guard.py collect output, set G3) with the checks of S463.read_collect, written for G3 in
           read_g3_collect(): the sidecar's rows, set and run_sha256, one run_sha256, D88's lock on every row, one
           row per answer, each row a G3 answer judged with its group's prompt, every draw-1 answer present (G9's two
           set-ups too when the collect holds any row of theirs; a collect given by path, or a frozen collect other
           than 41d3105d, must hold them), and S463.check_units() on the judging units the sidecar names. Reads RLM-10's
           judge rows with S463.read_collect() itself (G1's collect, its reruns and units) and RLM-10's records with
           S463.read_answers() (the folder's MANIFEST.sha256); G1's and G3's rows must carry one run_sha256 (one judge
           set-up). D188, after those checks of the v2.4 collects: g3_judge_rows reads G3's draw-1 answers through
           judge_rows_v25 (check_v24 on the collect and out_g3; out_s6_g3, when present beside out_g3, collected by
           s3_guard.py, check_v25 and S463.check_units; choose with G3's per-configuration rule, draw 1 of the G3 and G9
           set-ups read, every other row set aside), and merge_g3 makes each cell again from its v2.5 row (the v2.4
           cells must be the rows read); RLM-10's cells go through S463.judge_rows (G1, every draw) on --s6-g1. The cells
           of the v2.4 rows are kept beside the chosen ones. Joins each answer to its row (draw 1 only, D98): same
           answer key, and a judge "no_answer" exactly where the record has no text (a failed answer: a fail, and not
           refused, Rule 10); an unscored row is left out of that question's share (S463.shares). REPRODUCES FIRST
           (README.md:75-79; any difference exits 2 with nothing written): (1) g3_draw1_stop.log's draw-1 and later key
           counts of each orchestrator set-up; (2) plan.csv row G3's "raw_gemini and naive_rag hold all three draws"
           (135 answers in each of draws 1, 2, 3); (3) distiller_firing.count() on the full pipeline's answers.json, the
           module gate_distiller.sh runs, against this script's own count of the same steps; (4) every set-up's counts
           against --recount (default findings/recompute/S480_fig4_recount.json, written by
           scripts/S480_fig4_recount.py, which imports neither this script nor S463 nor S457 and counts the same
           raw files by plain counting; O1 of 24 October). First, the recount must have been written by S480 as it
           stands at HEAD (D136 Q12: the sha256 in its provenance against git show HEAD:, so S480 is committed before
           the plate is built), and its inputs must be the files this run read: the ten answers.json, two collects,
           two sidecars, RLM-10's answers.jsonl and the SHA256SUMS of --s6-g1, each with the sha256 of the file read
           here (else exit 2, "recount made from other files"). D188: the counts of the v2.4 cells must equal the
           recount's counts_v24 (its plain count of the collects), then the counts of the cells drawn its counts (its
           count of the rows judge_rows_v25 chose: the row selection is that shared module's, so on the rows chosen
           the recount is independent of this script's counting, not of the selection; only the v2.4 rows are held to
           the row each collect gave); a recount without counts_v24 is refused. Then, per set-up, the pass counts at
           score 4 and 3 on the answerable questions and the questions with a share, the refused count and the
           questions with a share on the 39, the false-premise questions passed at 4 and 3 and judged, the answers
           judged no_answer, the unscored rows and the not-answerable questions sent to a direct answer must equal
           the recount's (else exit 2, naming the set-up and the count). G9's answers, no-text answers, words, calls,
           failed and cut calls and direct answers must equal the recount's stress_records, and the 'draw' rows, once
           they exist, the recount's draw_counts. Also before writing (reproduce_new): every row of the frozen collect
           41d3105d is in the collect read, equal, and the nine set-ups' statistics are equal with and without the
           stress set-ups (with no stress judge rows, nothing to compare, and the provenance says so). G17 (D250): read_g17
           reproduces S576 on the d123 reading (above, panel e). After drawing, check_drawn reads every mark back
           against its sheet row. (The step curve's PDF read-back moved with the panel to S524, D250.) Then writes
           into --out, findings/figures_provisional/fig4/ by default (an earlier S472 plate there is removed first):
             Figure 4 (provisional, <n> of <N>).{pdf,svg,png}, Source Data Fig. 4 (...).xlsx and its caption,
             figure4_numbers.json (S448 R8: every sheet, and every printed number tied to its sheet and row),
             figure4_provenance.json, legend_draft.md, claims.md, records_manifest.json;
           and into --steps-out (default findings/recompute/S472_supp12a_steps.json) old panel 4b's rows, the input
           of Supplementary Figure 10a (D250).
           n = the draw-1 answers drawn in c (G3's, G9's and RLM-10's); N = the answers Figure 4's written plan
           holds under D98 (planned() below).
  selftest uv run --frozen python scripts/S472_fig4_panels.py selftest
           Synthetic records through the calculations (values worked by hand), the stress set-ups (in the collect, a
           missing row refused, no P, a third gap, the 'draw', 'fp_tile' and 'total' rows, the flipped levels),
           answer_search_s on a built retrievals file (an earlier attempt's line, another item's line, a partial line),
           the reproduction refusing a stop log that disagrees; a synthetic G3 collect with its judging units (start
           file, rows, header, recheck lines, as judge_passages.py and run_s3.sh write them) read by read_g3_collect,
           and altered copies it must refuse; an analyser switched off read as no analyser (and a mix refused); RLM-10's
           per-answer checks (rlm_answer) on a built answer and altered copies it must refuse (the G1 collect and
           MANIFEST readers are S463's and are exercised only by the real run); the judge join, the statistics on
           built cells (pass counts, a failed answer as a fail, an unscored row left out, refusals, a zero's and a
           100%'s one-sided bound, false premise, Holm); vs_full_text (nothing detected; a difference detected);
           draw_rows_keep; b's false-premise tiles through check_drawn (outlined where the sheet passes them; a pass
           without its outline, a fail outlined, a missing tile or a tile off its column flagged); G17 (D250): sheets
           d and e from the committed reading, and an S576 file altered or made from another reading refused; the
           claims' bound text; and the recount gate (4): an equal recount passes, a recount with one count changed is refused, a
           recount with one input sha256 changed is refused, a recount of another S480 is refused; stress_records and
           draw_counts compared; D188: counts_v24 compared when asked and a recount without it refused; merge_g3 on a
           built choice (a v2.5 row's cell made from it, the v2.4 cells kept, the counts) and its refusals (a v2.5 row
           of the other prompt, a v2.4 row not the one read, no row chosen, an answer missing; judge_rows_v25 itself is
           tested by scripts/judge_rows_v25_test.py and exercised here only by the real run); reproduce_new on the
           frozen collect and an altered copy. D155: HEAD_SH on built .git layouts and no git command in either pull;
           collect_view on a copied collect and its refusals; check_committed and check_pins on built sets (a changed,
           added or missing file refused); side_core.
           Last line "selftest: <k> of <k> checks pass".
"""
import argparse
import contextlib
import datetime as dt
import hashlib
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
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import S457_fig2_panels as S457  # noqa: E402  (FIGURE_LOCK's values, plate_rc, finish_plate, half_up, wcag)
import fig_repro as FR  # noqa: E402  (D155: frozen inputs, deterministic xlsx, PDF and SVG checks)
import figure_names as FN  # noqa: E402  (build order A4: one constant per printed name)
import house_style as hs  # noqa: E402  (the plate's marks, keys and colours)
import judge_rows_v25 as JR  # noqa: E402  (D188: the key v2.5 judge row where one exists, else key v2.4's)

SCRIPT = "scripts/S472_fig4_panels.py"
FIG_N = FN.FIG_PIPELINE                           # D283 (6 November 2026): 4 until then; the folder stays fig4
OUT = ROOT / "findings" / "figures_provisional" / "fig4"
STUDIO = "10.15.212.253"
G3_CLONE = "projects/mentori-runs-g3"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
INDEX = "exp_v4_s20_n0"
PLAN = ROOT / "experiments" / "plan.csv"
# G3's preflight.sh as committed (sha256 01b8a87a, git blob 2d0799dc), frozen (D155): the plate reads its WAVE1 and
# WAVE2 only. The working copy in findings/recompute/G3_runs/ is not read: on 27 October it held uncommitted edits
# (outside WAVE1 and WAVE2), and a plate's record must not depend on a working tree.
PREFLIGHT = ROOT / "findings" / "recompute" / "fig4_repo_inputs" / "G3_runs" / "preflight.sh"
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"
DISTILLER = ROOT / "experiments" / "mentori" / "orchestrator" / "distiller_firing.py"
EXP03 = ROOT / "experiments" / "mentori" / "publication" / "scripts" / ("exp_0" + "3_orchestration_ablation.py")
LOCK = ROOT / "experiments" / "LOCK.toml"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
LIST_MD = ROOT / "experiments" / "LIST.md"
README_EXP = ROOT / "experiments" / "README.md"
# Audit 27 Oct F1 (fig4_6, infra; D155): inputs_sha256 records the design documents and run code (DESIGN_DOCS) as they
# stood at DESIGN_AT, and a value drawn from them must be the same there; every check and the claims list read them as
# they stand (corrected 27 Oct, part 4). DESIGN_AT is the commit whose files give every sha256 the committed plate
# recorded (checked 27 Oct: all 13 repository inputs of
# figure4_provenance.json equal at 96936742). Read at HEAD, the dashboard commit fc3b67d5 (plan.csv) and the README
# decisions after it changed figure4_provenance.json with nothing in the figure changed (S494: 9 of 10 files equal).
DESIGN_AT = "96936742"
# The live documents moved to resubmission/ on 4 Nov 2026 (Valerio; doc_paths); at DESIGN_AT the main text was at its
# old path, so design_bytes reads it there (at DESIGN_AT the new path held S347's packed copy, which the plate never
# recorded). The letter's path is unchanged: the plate recorded it at DESIGN_AT, where it held the packed copy.
from doc_paths import LETTER, doc  # noqa: E402
DESIGN_PATH_BEFORE_MOVE = {"resubmission/04_manuscript/02_Main_Text.docx": "manuscript/submission/02_Main_Text.docx"}
LOCK_WANT = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"   # D88; G3's start records name it
LOCKS_OK = __import__("lock_equiv").EQUIVALENT   # D205: D88 and the locks lock_equiv proves equal to it in every sent setting
TZ = "Europe/Amsterdam"          # D155: the stamp's local time of the records, fixed (was the machine's time zone)

# D155: the frozen inputs `figure` reads when no path is given, as fig_repro.frozen(set, rel) returns them
# (findings/recompute/frozen_inputs/README.md; INVENTORY.md A1 and A2).
FROZEN = {"records": ("fig4_records_1023", "fig4_records_1023"),          # tar; S472 pull of 23 October
          "collect": ("fig4_g9", "g3_collect.jsonl"),                      # committed; pull-judge of 3 November (G9 judged)
          "g9_retrievals": ("fig4_g9", "g9_retrievals/findings/runs"),     # committed; pull --g9-retrievals, 3 November
          "rlm_collect": ("fig2", "g1_collect.jsonl"),                     # committed; G1's collect of 23 October
          "rlm_answers": ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs"),  # tar; G1R15's answers, MANIFEST beside
          "g9": ("g9", "."),                                               # committed; G9's two answers.json
          "s6_g1": ("fig3_s6", ".")}                                       # committed (S528); RLM-10's key v2.5 rows
# The sha256 the committed plate of 26 October (03acb915) recorded for each, checked before anything is read: a frozen
# input with another sha256 is refused (figure4_provenance.json judge.g3_collect, judge.g1_collect, judge.rlm_answers;
# S480_fig4_recount.json known_inputs.rlm_manifest). PULL.json's own sha256 was not recorded; its content equals the
# committed records_manifest.json less "what" and "copied_to" (checked 26 October), and read_records() checks every
# record against it, so pinning it pins the records (figure4_provenance.json records.sha256 lists the same values).
FROZEN_PIN = {
    ("fig4_records_1023", "fig4_records_1023/PULL.json"):
        "23b1360f37aad4e0b2450d9234aa7ffbce180e6a1124b866fb0c311b5c4efe7e",
    ("fig4", "g3_collect.jsonl"): "41d3105db493fa05fe6fc702ce315c4c4417f528699dc51b05da5b9240e7ec37",
    ("fig4", "g3_collect.jsonl.json"): "8ad99ba4071eb289166ca16b9ff48c541f7208cc55f2bbf151d893ec9b1451c7",
    ("fig2", "g1_collect.jsonl"): "f5ff75bc244cda492a48e7e11f54f2007ed7d586a8f49e78921edd7244b28965",
    ("fig2", "g1_collect.jsonl.json"): "04996e9dd9c3cca49177068f0143fbe0d1c7fa265a4eb6f617d24551f501f895",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/MANIFEST.sha256"):
        "60c1f703d7b5853ec7bd5aebaecec9ac50ea3cb078b1f44741c5964427635b2e",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs/exp_01__verified_pass__exp_v4_s20_n0/answers.jsonl"):
        "1ce4b1052912d8592b912da29ed987df9c2a4baca575cf80cc2b9d33334f8148",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs/exp_01__rlm_5__exp_v4_s20_n0/answers.jsonl"):
        "cc10c9eb881fa9618ff2fb8ec7a3f1bb9cf58662827cd67b326e47f67b51d42c",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl"):
        "ecb6de5343d172894fd56d57997e3301d70ca3fb509ae2cd65f8e47eb8c268b7",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs/exp_01__rlm_20__exp_v4_s20_n0/answers.jsonl"):
        "1e5b124d8bbd98640c87051916305ed0c04d668447967c60a08d6945fca32c62",
    ("g9", "PULL.json"): "e7f9abed14cee406c3c1934af3ea0257bfc06da9d1401213ce5fd913384f61f9",   # SHA256SUMS' line
    # 3 November: G9's judge rows and retrievals, frozen with the set's own SHA256SUMS (pull-judge and pull
    # --g9-retrievals; 1924 rows = the 1654 of 41d3105d, every one equal, and G9's 270)
    ("fig4_g9", "g3_collect.jsonl"): "527fd71e53f30ca77f6ca050be58206a08e99b55b87e8d58887f5486bbdd4bae",
    ("fig4_g9", "g3_collect.jsonl.json"): "047a84919456d72557d581d83d6584ac8440158201a1ebec067be6b26d03b297",
    ("fig4_g9", "g9_retrievals/PULL.json"): "034a9c5a2ed4352e829f216508d912e3b01693c819dada576127ee4ba2d3b252",
}
FROZEN_COLLECT_RIGHT = "41d3105db493fa05fe6fc702ce315c4c4417f528699dc51b05da5b9240e7ec37"   # reproduce_new's anchor
FROZEN_RIGHT = ("fig4", "g3_collect.jsonl")      # where that collect stays, once FROZEN["collect"] moves
FROZEN_SUMS = ROOT / "findings" / "recompute" / "frozen_inputs" / "SHA256SUMS"
# The judging units each collect names (s3_guard.py collect's sidecar, _provenance.inputs), read by S463.check_units:
# committed beside their collect, every file checked against FROZEN_SUMS (the freeze's record, 8082cc23).
FROZEN_UNITS = {"fig4": ["out_g3"], "fig2": ["out", "out_g1r15"], "g9": []}
OWN_SUMS = ("fig3_s6", "fig4_g9")                         # build order F3: a committed set with its own SHA256SUMS (FR.frozen)
EXAMPLE_OUT_OF_SCOPE = "OOD_012"                 # the legend's example question, read from the D5 key (FF7)
ALPHA = 0.05                                     # Rule 11: two-sided alpha

# Figure 4's set-ups as G3 ran them (preflight.sh WAVE1), with the plate's labels (LIST.md Figure 4, D52, Rule 12)
SETUPS = [("raw_gemini", FN.NO_RETRIEVAL), ("naive_rag", FN.NAIVE_RAG), ("full_orchestrator", FN.FULL_PIPELINE),
          ("orch_no_analyser", FN.NO_ANALYSER), ("orch_no_planner", FN.NO_PLANNER),
          ("orch_no_supervisor", FN.NO_SUPERVISOR), ("orch_no_synthesiser", FN.NO_SYNTHESIZER),
          ("orch_factual_to_documents", FN.ROUTING_FIX)]
LABEL = dict(SETUPS)
CONFIGS = [c for c, _ in SETUPS]
ORCH = CONFIGS[2:]
BASELINES = CONFIGS[:2]
RLM = "rlm_10"                                   # Figure 3's RLM-10 (G1), the ninth row (D83 Q148, D132)
LABEL[RLM] = FN.RLM_10
STRESS = ["orch_distil_every_step", "orch_distil_every_step_f1"]   # G9 (D163): descriptive, one draw, no test
LABEL.update({STRESS[0]: FN.ALWAYS_DISTIL, STRESS[1]: FN.ALWAYS_DISTIL_F1})
G3_ALL = CONFIGS + STRESS                        # the set-ups exp_03 answered and the G3 collect may hold
PIPED = ORCH + STRESS                            # the set-ups with an orchestrator (an analyser and plan steps)
ALL = CONFIGS + STRESS + [RLM]
NINE = CONFIGS + [RLM]                           # the set-ups of the plate before G9, every anchor's
FULL = "full_orchestrator"
FAMILY = ORCH[1:]                                # Rule 12's zero branch: the five set-ups Holm runs over
N_Q = 135
GROUPS = [("answerable", "answerable"), ("false_premise", "false premise"), ("not_answerable", FN.OUT_OF_SCOPE_QUESTIONS)]
GROUP_N = {"answerable": 86, "false_premise": 10, "not_answerable": 39}   # Rule 8 (LIST.md), from the D5 key
PASS_T = 4                                       # D132, D154: the pass rate is at judge score 4 or more (3 relaxed)
PASS_RELAXED = 3                                 # D154: the relaxed threshold, Source Data only (D160 (8))
FP_T = 4                                         # Rule 9 (D160 (11)): a false-premise question passes at correctness 4+
FP_RELAXED = 3                                   # Rule 9 (D160 (11), as D154): the relaxed threshold, Source Data only

# Rule 10 with D83 Q145 (O1, O2), D89, D90, D92 Q188: the Gemini call statuses (experiments/runner/gemini_client.py)
GOOGLE_STOP = ("blocked", "recitation")                                    # "stopped by Google"
OTHER_RETURNED = ("empty", "malformed_function_call", "malformed_response", "language", "other",
                  "unexpected_tool_call", "too_many_tool_calls")         # the other statuses a caller returns
CALL_ERROR = ("error", "stalled")                                          # raised in the caller
CUT = ("length",)                                                          # cut at the output limit, text kept
KNOWN_STATUS = {"ok", *GOOGLE_STOP, *OTHER_RETURNED, *CALL_ERROR, *CUT}


class Refused(SystemExit):
    pass


# Panels d and e (D250, Valerio, 4 November 22:47: option 2b of findings/recompute/fig4_g17_drafts, built once G17
# draws 2 and 3 were judged). The G17 ablation as an investigative tool, descriptive, no ranking (D240, D239 amended).
# d: concept recall per answerable question, each question's mean over draws 1 to 3; e: per draw-1 answer, the
# sub-calls that returned paper text and the distinct papers read. Boxes Q1 to Q3, median line, whiskers to the range,
# no mean or interval (the house box). Read only from S571's reading of draws 1 to 3 (g17_d123) through S576's own
# per_answer and question_means, and S576's paired differences of it (findings/recompute/S576_d249/s576_d249.json),
# which the legend quotes. The package arm's draws are G6's (cap 10), as S576 reads them.
G17_READING = ROOT / "findings" / "recompute" / "S571_rlm_reading" / "g17_d123" / "g17_reading.json"
G17_S576 = ROOT / "findings" / "recompute" / "S576_d249" / "s576_d249.json"
G17_CONTRASTS = ROOT / "findings" / "recompute" / "S575_g17_contrasts" / "contrasts.json"   # S576 reproduces it
G17_CTRL = "ctrl"                                # S576.ARMS: Mentori RLM-10 run on today's code, the control
# the four arms, left to right in each question type (option 2b), with their colour and shape; D293 (Valerio, 7 Nov):
# RLM-10 (no "control"), Zhang RLM-10, search tools off, quality gate off, in that order in the key, the boxes and legend
G17_ARMS = [(G17_CTRL, FN.MENTORI_RLM_N.format(n=10)), ("package", FN.PACKAGE_RLM_N.format(n=10)),
            ("search_off", "search tools off"), ("gate_off", "quality gate off")]
G17_ARM_LABEL = dict(G17_ARMS)
G17_COL = {G17_CTRL: hs.OKABE["blue"], "search_off": hs.OKABE["sky blue"], "gate_off": hs.OKABE["reddish purple"],
           "package": hs.OKABE["vermillion"]}
G17_MK = {G17_CTRL: "o", "search_off": "s", "gate_off": "D", "package": "^"}
G17_GROUPS = [("one", "one paper"), ("many", "many papers")]   # the two question types, left to right
G17_N = {"all": 86, "one": 60, "many": 26}
G17_DRAWS = (1, 2, 3)                            # d: each question's mean over these (D250)
G17_F_DRAW = 1                                   # e: one answer per question, draw 1, as option 2b drew it
G17_F = [("sub_calls_with_paper_text", "Sub-calls that returned\npaper text"), ("n_papers", "Distinct papers read")]
G17_F_TICKS = [0, 1, 2, 4, 8, 16, 32, 64]
G17_SYMLOG = dict(base=10, linthresh=2, linscale=0.6)   # e: linear up to 2, logarithmic above (option 2b)
G17_F_TOP = 100                                  # e's axis top (the package's largest count of draw 1 is 87)
# the legend's paired differences (S576's descriptive contrasts on the mean of draws 1 to 3): part id in S576
G17_LEGEND_PARTS = [("package", "H1"), ("search_off", "H2a"), ("gate_off", "H3")]   # G17_ARMS's order (D293)
PLATE_LETTER = {"a": "a", "c": "b", "d": "c", "e": "d", "f": "e"}   # D250: internal sheet key -> plate letter (b to Supp 10a)
STEPS_OUT = ROOT / "findings" / "recompute" / "S472_supp12a_steps.json"   # D250: old 4b's rows, read by S524 (12a)
D_XLABEL = {"model_calls": "Model calls", "own_time_s": "Time (s)"}   # D293: n = ... answers above says per answer


def sheet_name(L: str) -> str:
    return f"Fig. {FIG_N}{PLATE_LETTER[L]}"


def s576():
    """S576 (D249): its per_answer, question_means and evaluate are the one definition panel d and the legend read."""
    import S576_d249_hypotheses as m
    return m


def _named(shas: dict, path: Path):
    """The sha256 a provenance's inputs_sha256 records for path (keys may be absolute or repository-relative)."""
    hits = [v for k, v in shas.items() if k == str(path) or k == rel(path)]
    return hits[0] if len(hits) == 1 else None


def read_g17(reading: Path = G17_READING, s576_json: Path = G17_S576, contrasts: Path = G17_CONTRASTS) -> dict:
    """G17's per-answer rows of draws 1 to 3 (S571's g17_d123 reading) and S576's paired differences of them.
    REPRODUCES FIRST: S576's file must name the reading read here and S575's contrasts file by sha256, and its
    descriptive contrasts on the mean of draws 1 to 3 and its arm means must equal S576.evaluate() and S576's
    arm_means run again on the reading (every number), else Refused and nothing is written. Each arm needs one
    answer per question at each draw (S576.per_answer); e's draw-1 fields must all be present."""
    m = s576()
    d = json.loads(reading.read_text())
    s = json.loads(s576_json.read_text())
    shas = (s.get("_provenance") or {}).get("inputs_sha256", {})
    for p in (reading, contrasts):
        if _named(shas, p) != sha256_file(p):
            raise Refused(f"S576's paired differences were made from a {rel(p)} of sha256 "
                          f"{str(_named(shas, p))[:12]}, not the one read here ({sha256_file(p)[:12]})")
    if d.get("decision") != "D249" or d.get("draws") != list(G17_DRAWS) or not (
            d.get("judged") and d.get("concept_recall_given")):
        raise Refused("S571's G17 reading is not D249's draws 1, 2 and 3 with the judge and concept recall")
    try:
        ans, unscored = m.per_answer(d["answers"], G17_DRAWS)
    except m.Refused as e:
        raise Refused(f"S576.per_answer refused the reading: {e}")
    if set(ans) != set(G17_ARM_LABEL):
        raise Refused(f"S576's arms {sorted(ans)} are not panel d's {sorted(G17_ARM_LABEL)}")
    means = m.question_means(ans, G17_DRAWS)
    for a, x in means.items():
        if Counter(r["group"] for r in x.values()) != Counter({g: G17_N[g] for g, _ in G17_GROUPS}):
            raise Refused(f"G17 {a}: not 86 questions, 60 one-paper and 26 many-paper")
    again = json.loads(json.dumps(m.evaluate(means, verdict=False)))
    if again != s["descriptive_draws_1_3"]:
        raise Refused("S576's descriptive contrasts on draws 1 to 3 are not what S576.evaluate() gives on the reading")
    if json.loads(json.dumps(m.arm_means(means))) != s["arm_means"]["draws_1_3"]:
        raise Refused("S576's arm means on draws 1 to 3 are not what S576.arm_means() gives on the reading")
    raw = {a: {} for a in G17_ARM_LABEL}
    for r in d["answers"]:
        a = next((k for k, v in m.ARMS.items() if v == r["strategy"]), None)
        if a is None or r["draw"] != G17_F_DRAW:
            continue
        if any(r.get(k) is None for k, _ in G17_F):
            raise Refused(f"G17 {a} {r['question_id']} draw {G17_F_DRAW}: no {[k for k, _ in G17_F if r.get(k) is None]}")
        raw[a][r["question_id"]] = r
    for a, x in raw.items():
        if set(x) != set(means[a]):
            raise Refused(f"G17 {a}: {len(x)} draw-{G17_F_DRAW} answers, not one per question of the 86")
    parts = {p["part"]: p for h in s["descriptive_draws_1_3"].values() for p in h["parts"]}
    return {"means": means, "per_draw": ans, "raw": raw, "unscored": unscored, "parts": parts,
            "reading": rel(reading), "reading_sha256": sha256_file(reading),
            "s576": rel(s576_json), "s576_sha256": sha256_file(s576_json),
            "contrasts_path": rel(contrasts), "contrasts_sha256": sha256_file(contrasts),
            "s576_code_sha256": s["_provenance"].get("code_sha256"), "boot": s["_provenance"].get("boot"),
            "seed": s["_provenance"].get("seed")}


def g17_tf():
    """e's axis transform (linear to 2, logarithmic above) and its inverse, as plain functions of one value."""
    import matplotlib.scale as mscale
    tr = mscale.SymmetricalLogTransform(**G17_SYMLOG)
    inv = tr.inverted()
    return (lambda v: float(tr.transform([v])[0])), (lambda v: float(inv.transform([v])[0]))


def g17_sheets(g17: dict) -> tuple[list, list]:
    """Sheets d and e (internal keys e and f). d: one 'box' row per arm and question type (n, range, quartiles and
    median of the per-question means of concept recall over draws 1 to 3, in %; whether the box is flat), then one
    'question' row per arm and question (concept recall at each draw and the mean, in %), then one 'difference' row
    per paired contrast S576 gives on the mean of draws 1 to 3 (Source Data only; the legend quotes those of each arm
    minus the control). e: one 'box' row per measure, arm and question type over the draw-1 answers, then one 'answer'
    row per arm and question with both measures."""
    d_rows, e_rows = [], []
    for a, lab in G17_ARMS:
        for g, glab in G17_GROUPS:
            v = [100.0 * x["cr"] for q, x in sorted(g17["means"][a].items()) if x["group"] == g]
            b = hs.box_stats(v, "range")
            d_rows.append({"row": "box", "arm": lab, "arm_key": a, "question_type": glab, "group_key": g,
                           "n": len(v), "minimum": b["whisker_low"], "q1": b["q1"], "median": b["median"],
                           "q3": b["q3"], "maximum": b["whisker_high"], "flat": "yes" if b["q1"] == b["q3"] else "no"})
    for a, lab in G17_ARMS:
        for q, x in sorted(g17["means"][a].items()):
            row = {"row": "question", "arm": lab, "arm_key": a, "question_id": q,
                   "question_type": dict(G17_GROUPS)[x["group"]], "group_key": x["group"]}
            for dr in G17_DRAWS:
                row[f"concept_recall_draw_{dr}"] = 100.0 * g17["per_draw"][a][(q, dr)]["cr"]
            row["concept_recall_mean"] = 100.0 * x["cr"]
            d_rows.append(row)
    for pid, p in g17["parts"].items():
        k = 100.0 if p["metric"] == "cr" else 1.0          # S576 gives pass at 4 in points, concept recall as a share
        two = p["kind"] == "diff"
        d_rows.append({"row": "difference", "part": pid, "arm": G17_ARM_LABEL.get(p["a"], p["a"]), "arm_key": p["a"],
                       "minus": G17_ARM_LABEL.get(p["b"], p["b"]), "minus_key": p["b"],
                       "question_type": p["group"], "measure": "concept recall" if p["metric"] == "cr" else
                       f"pass at {PASS_T}", "metric_key": p["metric"], "questions": p["n_questions"],
                       "mean_arm": k * p["mean_a"] if two else None, "mean_minus": k * p["mean_b"] if two else None,
                       "difference": k * p["diff"], "interval_low": k * p["ci95"][0],
                       "interval_high": k * p["ci95"][1],
                       "questions_arm_higher": p.get("a_higher"), "questions_minus_higher": p.get("b_higher"),
                       "drawn": "Source Data only"})
    for f, flab in G17_F:
        for a, lab in G17_ARMS:
            for g, glab in G17_GROUPS:
                v = [float(r[f]) for q, r in sorted(g17["raw"][a].items()) if r["group"] == g]
                b = hs.box_stats(v, "range")
                e_rows.append({"row": "box", "measure": flab.replace("\n", " "), "measure_key": f, "arm": lab,
                               "arm_key": a, "question_type": glab, "group_key": g, "n": len(v),
                               "minimum": b["whisker_low"], "q1": b["q1"], "median": b["median"], "q3": b["q3"],
                               "maximum": b["whisker_high"], "flat": "yes" if b["q1"] == b["q3"] else "no"})
    for a, lab in G17_ARMS:
        for q, r in sorted(g17["raw"][a].items()):
            e_rows.append({"row": "answer", "arm": lab, "arm_key": a, "question_id": q, "draw": G17_F_DRAW,
                           "question_type": dict(G17_GROUPS)[r["group"]], "group_key": r["group"],
                           **{f: r[f] for f, _ in G17_F}})
    return d_rows, e_rows


def run_of(c):
    return f"exp_0{3}__{c}__{INDEX}"


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


_DESIGN: dict = {}


def design_bytes(p: Path, at: str | None = None, root: Path | None = None) -> bytes:
    """A design document's bytes as it stood at DESIGN_AT (git show, read only); refused when git cannot give it."""
    at, root = at or DESIGN_AT, Path(root or ROOT)
    key = (str(root), str(p), at)
    if key not in _DESIGN:
        r_ = Path(p).resolve().relative_to(root.resolve()).as_posix()
        r_ = DESIGN_PATH_BEFORE_MOVE.get(r_, r_) if root.resolve() == ROOT.resolve() else r_
        r = subprocess.run(["git", "-C", str(root), "show", f"{at}:{r_}"], capture_output=True)
        if r.returncode:
            raise Refused(f"git show {at}:{r_} failed: {r.stderr.decode(errors='replace')[:200]}")
        _DESIGN[key] = r.stdout
    return _DESIGN[key]


def code_tree(src: str) -> str:
    """A module's syntax tree less its docstring (ast.dump: no line numbers, no comments): equal when only the
    docstring, comments or layout changed."""
    import ast
    body = ast.parse(src).body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return ast.dump(ast.Module(body=body, type_ignores=[]))


def distiller_moved(now_src: str | None = None, at_src: str | None = None) -> bool:
    """True when the distiller_firing.py imported (the file on disk) differs in code from its DESIGN_AT version."""
    now_src = DISTILLER.read_text() if now_src is None else now_src
    at_src = design_bytes(DISTILLER).decode() if at_src is None else at_src
    return code_tree(now_src) != code_tree(at_src)


def fmt_int(n) -> str:
    return f"{int(n):,}"


def s463():
    """S463 (Figure 3's ranking), whose readers and statistics this plate reuses."""
    import S463_fig2_ranking as m
    return m


@contextlib.contextmanager
def s463_configs(configs):
    """S463's statistics run over its module-level CONFIGS; for this plate's nine set-ups they are set for the call
    and put back after it."""
    m = s463()
    old = m.CONFIGS
    m.CONFIGS = list(configs)
    try:
        yield m
    finally:
        m.CONFIGS = old


def s463_call(fn, *a, **kw):
    """An S463 function whose refusal (S463.Refused) is this script's refusal."""
    m = s463()
    try:
        return fn(*a, **kw)
    except m.Refused as e:
        raise Refused(f"S463.{fn.__name__}: {e}") from None


# ---------------------------------------------------------------------------------------------------------------
# pull: stdin scripts only
# ---------------------------------------------------------------------------------------------------------------
def files_to_pull(g9_retrievals: bool = False) -> list[str]:
    """The files `pull` lists: G3's by default; with g9_retrievals G9's two retrievals.jsonl only (fig4.md section 4,
    step 1; figure reads each answer's own draw-1 offsets, so lines G7 appended later are not read)."""
    if g9_retrievals:
        return [f"findings/runs/{run_of(c)}/retrievals.jsonl" for c in STRESS]
    out = []
    for c in CONFIGS:
        s = f"findings/runs/{run_of(c)}"
        out += [f"{s}/answers.json", f"{s}/run_identity.json", f"{s}/index_identity.jsonl", f"{s}/retrievals.jsonl"]
    return out


# D155 (INVENTORY.md A8, ported here too): the 23 October guards allow no git command on the Studio, so a clone's HEAD
# is read from its .git files, as refresh_pull.py's _head() did at run time for S463 and S473: .git a folder or a
# "gitdir:" file (a worktree), HEAD a "ref:" line or a detached hash, the ref a loose file, under commondir, or a
# packed-refs line. Full hash, or "unknown". selftest checks it on built .git layouts.
HEAD_SH = r"""head_of() {
  g=.git
  if [ -f "$g" ]; then g=$(sed -n 's/^gitdir: *//p' .git); fi
  h=$(cat "$g/HEAD" 2>/dev/null || echo unknown)
  case "$h" in
    "ref: "*)
      r=${h#ref: }
      if [ -f "$g/$r" ]; then cat "$g/$r"; return 0; fi
      cg=$g
      if [ -f "$g/commondir" ]; then
        c=$(cat "$g/commondir")
        case "$c" in /*) cg=$c ;; *) cg="$g/$c" ;; esac
      fi
      if [ -f "$cg/$r" ]; then cat "$cg/$r"; return 0; fi
      if [ -f "$cg/packed-refs" ]; then
        awk -v r="$r" '$2 == r {print $1; f = 1} END {if (!f) print "unknown"}' "$cg/packed-refs"
      else
        echo unknown
      fi ;;
    *) echo "$h" ;;
  esac
}
"""

LIST_SH = r"""set -e
cd ~/__CLONE__
""" + HEAD_SH + r"""echo "HEAD $(head_of)"
echo "NOW $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for f in __FILES__ findings/recompute/G3_runs/g3_*.start.json findings/recompute/G3_runs/g3_*.end.json \
         findings/recompute/G3_runs/launch_wave1.json findings/recompute/G3_runs/launch_relaunch_*.json \
         findings/recompute/G3_runs/g3_*_attempt_*/*.json findings/recompute/G3_runs/g3_draw1_stop.log \
         findings/recompute/G3_runs/smoke_check.json; do
  [ -f "$f" ] || continue
  echo "FILE $(shasum -a 256 "$f" | cut -d' ' -f1) $(stat -f '%z %m' "$f") $f"
done
"""

G9_LIST_SH = r"""set -e
cd ~/__CLONE__
""" + HEAD_SH + r"""echo "HEAD $(head_of)"
echo "NOW $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for f in __FILES__; do
  [ -f "$f" ] || continue
  echo "FILE $(shasum -a 256 "$f" | cut -d' ' -f1) $(stat -f '%z %m' "$f") $f"
done
"""

TAR_SH = r"""set -e
cd ~/__CLONE__
tar -cf - __LIST__
"""


def ssh_stdin(script: str, binary=False):
    r = subprocess.run(SSH + [STUDIO, "bash", "-s"], input=script.encode(), capture_output=True)
    if r.returncode:
        raise Refused(f"ssh {STUDIO} (stdin script): exit {r.returncode}: {r.stderr.decode(errors='replace')[:300]}")
    return r.stdout if binary else r.stdout.decode()


def pull(args):
    to = Path(args.to).expanduser().resolve()
    if to.is_relative_to(ROOT / "findings" / "runs"):
        raise Refused(f"{to}: never copy records under findings/runs")
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    to.mkdir(parents=True, exist_ok=True)
    g9 = getattr(args, "g9_retrievals", False)
    listing = ssh_stdin((G9_LIST_SH if g9 else LIST_SH).replace("__CLONE__", G3_CLONE)
                        .replace("__FILES__", " ".join(files_to_pull(g9))))
    head = re.search(r"^HEAD (\w+)$", listing, re.M).group(1)
    now = re.search(r"^NOW (\S+)$", listing, re.M).group(1)
    files = {}
    for m in re.finditer(r"^FILE ([0-9a-f]{64}) (\d+) (\d+) (.+)$", listing, re.M):
        files[m.group(4)] = {"sha256": m.group(1), "size": int(m.group(2)), "mtime": int(m.group(3))}
    for f in (files_to_pull(True) if g9 else [f"findings/runs/{run_of(c)}/answers.json" for c in CONFIGS]):
        if f not in files:
            raise Refused(f"{STUDIO}:~/{G3_CLONE}: no {f}")
    blob = ssh_stdin(TAR_SH.replace("__CLONE__", G3_CLONE).replace("__LIST__", " ".join(sorted(files))), binary=True)
    with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
        names = tf.getnames()
        if sorted(names) != sorted(files) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise Refused(f"the tar holds other files than the listing: {sorted(set(names) ^ set(files))[:5]}")
        tf.extractall(to, filter="data")
    bad = [f for f, v in files.items() if sha256_file(to / f) != v["sha256"]]
    if bad:
        raise Refused(f"{len(bad)} copies differ from the Studio's sha256 (written meanwhile?): {bad[:3]}; pull again")
    (to / "PULL.json").write_text(json.dumps({"from": f"{STUDIO}:~/{G3_CLONE}", "clone_head": head,
                                              "listed_utc": now, "files": files,
                                              "how": "stdin scripts (ssh <host> bash -s): a listing, then a tar"},
                                             indent=1) + "\n")
    print(f"pulled {len(files)} files from {STUDIO}:~/{G3_CLONE} (HEAD {head[:7]}, listed {now}) into {to}")
    print(f"next: uv run --frozen python {SCRIPT} figure --g9-retrievals {to}/findings/runs" if g9 else
          f"next: uv run --frozen python {SCRIPT} figure --records {to}")


# ---------------------------------------------------------------------------------------------------------------
# pull-judge (D155, INVENTORY.md A6): the G3 judge pull of 24 October, done then by hand (a tar of out_g3 and a local
# s3_guard.py collect), as a command. Never run live while writing it: tested offline (--from-copy) on the frozen copy.
# ---------------------------------------------------------------------------------------------------------------
S3_CLONE = "projects/mentori-runs-s3"           # run_s3.sh REPO's default; S3 judged G3 there on 11455 (RUNNING.md 23 Oct)
S3_RUNS = "findings/recompute/S3_runs"          # run_s3.sh's D; the set's out is <D>/<SETS["G3"]["out"]>
G3_JUDGE_OUT = "out_g3"                         # s3_guard.py SETS["G3"]["out"]
S3_GUARD = ROOT / S3_RUNS / "s3_guard.py"

JLIST_SH = r"""set -e
cd ~/__CLONE__
""" + HEAD_SH + r"""echo "HEAD $(head_of)"
echo "NOW $(date -u +%Y-%m-%dT%H:%M:%SZ)"
cd __RUNS__
find __OUT__ -type f | LC_ALL=C sort | while IFS= read -r f; do
  echo "FILE $(shasum -a 256 "$f" | cut -d' ' -f1) $(stat -f '%z %m' "$f") $f"
done
"""

JTAR_SH = r"""set -e
cd ~/__CLONE__/__RUNS__
tar -cf - __LIST__
"""


def refuse_frozen_dest(to: Path):
    """A pull never writes into findings/runs or into a frozen set (findings/recompute/<set>_inputs, frozen_inputs)."""
    rc = ROOT / "findings" / "recompute"
    if to.is_relative_to(ROOT / "findings" / "runs"):
        raise Refused(f"{to}: never copy records under findings/runs")
    if to.is_relative_to(rc) and any(p.endswith("_inputs") for p in to.relative_to(rc).parts):
        raise Refused(f"{to}: inside a frozen input set (findings/recompute/*_inputs); pull into a new folder")


def side_core(side: dict) -> dict:
    """A collect sidecar without what depends on where and when collect ran: _provenance (its time and the absolute
    input folders) dropped, each "from" key written relative to its input folder's parent (out_g3/judge/...)."""
    ins = (side.get("_provenance") or {}).get("inputs") or []
    frm = {}
    for k, n in (side.get("from") or {}).items():
        x = next((x for x in ins if k.startswith(x.rstrip("/") + "/")), None)
        if x is None:
            raise Refused(f"the sidecar's from key {k} is under none of its inputs {ins}")
        frm[Path(x).name + k[len(x.rstrip("/")):]] = n
    return {**{k: v for k, v in side.items() if k not in ("_provenance", "from")}, "from": frm}


def recollect(out_dir: Path, dest: Path) -> dict:
    """s3_guard.py collect --set G3 on out_dir into dest (the step done by hand on 24 October); returns the sidecar."""
    r = subprocess.run([sys.executable, str(S3_GUARD), "collect", "--out", str(out_dir), "--dest", str(dest),
                        "--set", "G3"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise Refused(f"s3_guard.py collect on {out_dir}: exit {r.returncode}: {(r.stdout + r.stderr)[-400:]}")
    return json.loads(dest.with_name(dest.name + ".json").read_text())


def reproduce_judge_collect() -> dict:
    """REPRODUCES FIRST (README.md:75-79): collect on the frozen out_g3 (fig4_inputs, checked against FROZEN_SUMS)
    must give the frozen g3_collect.jsonl byte for byte (41d3105d) and its sidecar less paths and time."""
    sums = read_sums(FROZEN_SUMS)
    try:
        base = FR.frozen("fig4")
    except FR.FrozenInputError as e:
        raise Refused(str(e)) from None
    check_committed(base, sums)
    with tempfile.TemporaryDirectory(prefix="S472_rc_") as td:
        dest = Path(td) / "g3_collect.jsonl"
        side = recollect(base / G3_JUDGE_OUT, dest)
        got = sha256_file(dest)
    want = FROZEN_PIN[("fig4", "g3_collect.jsonl")]
    if got != want:
        raise Refused(f"REPRODUCTION FAILED, nothing written: collect on the frozen out_g3 gives sha256 {got[:12]}, the "
                      f"frozen g3_collect.jsonl is {want[:12]}")
    frozen_side = json.loads((base / "g3_collect.jsonl.json").read_text())
    if side_core(side) != side_core(frozen_side):
        diff = sorted(k for k in set(side_core(side)) | set(side_core(frozen_side))
                      if side_core(side).get(k) != side_core(frozen_side).get(k))
        raise Refused(f"REPRODUCTION FAILED, nothing written: the sidecar of collect on the frozen out_g3 differs from "
                      f"the frozen one in {diff}")
    return {"collect_sha256": got, "rows": side.get("rows"), "run_sha256": side.get("run_sha256"),
            "sidecar": "equal to the frozen sidecar less _provenance and the from keys' folder"}


def pull_judge(args):
    """Copies G3's judge out (out_g3) from the S3 clone on the Studio through stdin scripts (a listing with each file's
    sha256, then a tar of the listed files), or with --from-copy from a local out_g3 folder (offline), into
    <to>/out_g3, checks every copy against the listing, and runs s3_guard.py collect --set G3 on it into
    <to>/g3_collect.jsonl (sidecar beside it), the layout of findings/recompute/fig4_inputs. First reproduces the
    frozen collect (reproduce_judge_collect); on any failure nothing is written. Writes <to>/PULL_JUDGE.json."""
    to = Path(args.to).expanduser().resolve()
    refuse_frozen_dest(to)
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    try:
        reproduced = reproduce_judge_collect()
    except Refused as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    created = not to.exists()
    to.mkdir(parents=True, exist_ok=True)
    try:
        if args.from_copy:
            src = Path(args.from_copy).expanduser().resolve()
            if not src.is_dir():
                raise Refused(f"--from-copy {src}: not a folder")
            files = {f"{G3_JUDGE_OUT}/{f.relative_to(src).as_posix()}":
                     {"sha256": sha256_file(f), "size": f.stat().st_size, "mtime": int(f.stat().st_mtime)}
                     for f in sorted(src.rglob("*")) if f.is_file()}
            shutil.copytree(src, to / G3_JUDGE_OUT)
            head, now = None, None
            where = f"offline copy of {rel(src)}"
            how = "--from-copy: a local folder copied (no ssh)"
        else:
            listing = ssh_stdin(JLIST_SH.replace("__CLONE__", S3_CLONE).replace("__RUNS__", S3_RUNS)
                                .replace("__OUT__", G3_JUDGE_OUT))
            head = re.search(r"^HEAD (\w+)$", listing, re.M).group(1)
            now = re.search(r"^NOW (\S+)$", listing, re.M).group(1)
            files = {}
            for m in re.finditer(r"^FILE ([0-9a-f]{64}) (\d+) (\d+) (.+)$", listing, re.M):
                files[m.group(4)] = {"sha256": m.group(1), "size": int(m.group(2)), "mtime": int(m.group(3))}
            if not files:
                raise Refused(f"{STUDIO}:~/{S3_CLONE}/{S3_RUNS}/{G3_JUDGE_OUT}: no file listed")
            odd = [f for f in files if re.search(r"\s", f) or ".." in Path(f).parts
                   or not f.startswith(G3_JUDGE_OUT + "/")]
            if odd:
                raise Refused(f"listed names this pull does not tar safely: {odd[:3]}")
            blob = ssh_stdin(JTAR_SH.replace("__CLONE__", S3_CLONE).replace("__RUNS__", S3_RUNS)
                             .replace("__LIST__", " ".join(sorted(files))), binary=True)
            with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
                names = [m.name for m in tf.getmembers() if m.isfile()]
                if sorted(names) != sorted(files):
                    raise Refused(f"the tar holds other files than the listing: {sorted(set(names) ^ set(files))[:5]}")
                tf.extractall(to, filter="data")
            where = f"{STUDIO}:~/{S3_CLONE}/{S3_RUNS}/{G3_JUDGE_OUT}"
            how = "stdin scripts (ssh <host> bash -s): a listing (HEAD read from .git, no git command), then a tar"
        bad = [f for f, v in files.items() if sha256_file(to / f) != v["sha256"]]
        if bad:
            raise Refused(f"{len(bad)} copies differ from the listing's sha256 (written meanwhile?): {bad[:3]}; "
                          f"pull again")
        side = recollect(to / G3_JUDGE_OUT, to / "g3_collect.jsonl")
        (to / "PULL_JUDGE.json").write_text(json.dumps({
            "from": where, "s3_clone_head": head, "listed_utc": now, "how": how, "files": files,
            "collect": {"sha256": sha256_file(to / "g3_collect.jsonl"), "rows": side.get("rows"),
                        "run_sha256": side.get("run_sha256"), "status_a": side.get("status_a")},
            "reproduced_first": reproduced}, indent=1) + "\n")
    except BaseException:
        shutil.rmtree(to, ignore_errors=True)              # nothing written: the folder was new or empty
        if not created:
            to.mkdir(parents=True, exist_ok=True)
        raise
    print(f"reproduced first: collect on the frozen out_g3 gives {reproduced['collect_sha256'][:12]} "
          f"({reproduced['rows']} rows), the frozen g3_collect.jsonl")
    print(f"pulled {len(files)} files from {where} into {to}/{G3_JUDGE_OUT}; collect {side.get('rows')} rows, "
          f"sha256 {sha256_file(to / 'g3_collect.jsonl')[:12]}")
    print(f"next: uv run --frozen python {SCRIPT} figure --collect {to}/g3_collect.jsonl")


# ---------------------------------------------------------------------------------------------------------------
# frozen inputs (D155): pinned sha256, the committed sets checked file by file, the collects' folders mapped
# ---------------------------------------------------------------------------------------------------------------
def read_sums(path: Path) -> dict:
    """{path: sha256} from a sha256sum-style file ("<sha256>  <path>"); a malformed line is refused."""
    out = {}
    for n, ln in enumerate(path.read_text().splitlines(), 1):
        if not ln.strip() or ln.startswith("#"):
            continue
        m = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", ln)
        if not m:
            raise Refused(f"{path}:{n}: not a '<sha256>  <path>' line")
        out[m.group(2)] = m.group(1)
    return out


def check_committed(folder: Path, sums: dict, base: Path = ROOT) -> dict:
    """{path: sha256} of every file under folder (paths relative to base), each equal to its line in sums, with no
    file of sums under folder missing and no file there that sums does not list."""
    folder = Path(folder).resolve()
    pre = folder.relative_to(base.resolve()).as_posix() + "/"
    want = {k: v for k, v in sums.items() if k.startswith(pre)}
    got = {}
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        k = f.relative_to(base.resolve()).as_posix()
        if k not in want:
            raise Refused(f"{k}: in a frozen set but not in {FROZEN_SUMS.name} (a file added to the set)")
        h = sha256_file(f)
        if h != want[k]:
            raise Refused(f"{k}: sha256 {h[:12]} differs from {FROZEN_SUMS.name}'s {want[k][:12]} (the frozen copy "
                          f"was changed)")
        got[k] = h
    missing = sorted(set(want) - set(got))
    if missing:
        raise Refused(f"{len(missing)} files of {FROZEN_SUMS.name} under {pre} are missing, first {missing[0]}")
    return got


def check_pins(pins: dict, frozen=None) -> dict:
    """Each pinned frozen file (set, rel) must have its pinned sha256; returns {"<set>:<rel>": sha256}."""
    frozen = frozen or FR.frozen
    out = {}
    for (s, r), want in pins.items():
        try:
            got = sha256_file(frozen(s, r))
        except FR.FrozenInputError as e:
            raise Refused(str(e)) from None
        if got != want:
            raise Refused(f"frozen input {s}:{r} has sha256 {got[:12]}, the committed plate recorded {want[:12]}: "
                          f"not the input the plate was drawn from; nothing written")
        out[f"{s}:{r}"] = got
    return out


def frozen_inputs(names) -> tuple[dict, dict]:
    """The frozen copies of the inputs named (keys of FROZEN), each checked before it is read: the pinned files of
    its set (FROZEN_PIN), a committed set file by file against FROZEN_SUMS, a tarred set by fig_repro.frozen() (the
    tar's sha256, then every extracted file). Returns ({name: path}, {"pinned", "files"}) for the provenance."""
    paths, pinned, files = {}, {}, {}
    sums = read_sums(FROZEN_SUMS)
    for name in names:
        s, r = FROZEN[name]
        pinned.update(check_pins({k: v for k, v in FROZEN_PIN.items() if k[0] == s}))
        try:
            paths[name] = FR.frozen(s, r)
            top = FR.frozen(s)
        except FR.FrozenInputError as e:
            raise Refused(str(e)) from None
        if s in OWN_SUMS:                               # FR.frozen checked every file against the set's own sums
            files[f"{s}:SHA256SUMS"] = sha256_file(top / "SHA256SUMS")
        elif s in FROZEN_UNITS:
            files.update(check_committed(top, sums))
        else:
            files.update({f"{s}.tar:{f.relative_to(top).as_posix()}": sha256_file(f)
                          for f in sorted(top.rglob("*")) if f.is_file() and f.name != FR.EXTRACT_RECORD})
    return paths, {"pinned": pinned, "files": files}


def collect_view(collect: Path, tmp: Path) -> Path:
    """The collect to read: s3_guard.py collect writes the absolute folders it read into its sidecar
    (_provenance.inputs and the keys of "from"), and S463.read_collect and check_units read those folders. A collect
    copied elsewhere (the frozen fig4_inputs and fig2_inputs, or a pull-judge folder moved after collect ran) still
    names the old place, which for the frozen sets is the session scratch. The input folders all sat in one folder;
    each is the folder of the same name beside collect now. When they are already there, collect itself is returned;
    else a view in tmp: collect linked, the sidecar rewritten with the folders beside collect (nothing else changed).
    Refuses inputs in more than one folder, a "from" key under none of them, or a folder missing beside collect."""
    side_p = collect.with_name(collect.name + ".json")
    if not side_p.is_file():
        return collect                                  # read_g3_collect / read_collect refuse it with their message
    side = json.loads(side_p.read_text())
    ins = [x.rstrip("/") for x in ((side.get("_provenance") or {}).get("inputs") or [])]
    if not ins:
        return collect
    parents = {str(Path(x).parent) for x in ins}
    if len(parents) != 1:
        raise Refused(f"{side_p.name}: its input folders sit in {len(parents)} folders {sorted(parents)}; a copied "
                      f"collect is read only when they sat in one, beside it")
    here = collect.parent.resolve()
    if parents == {str(here)}:
        return collect
    new = {x: str(here / Path(x).name) for x in ins}
    for x, y in new.items():
        if not Path(y).is_dir():
            raise Refused(f"{side_p.name} names {x}; its copy {y} is not beside {collect.name}")
    frm = {}
    for k, n in (side.get("from") or {}).items():
        x = next((x for x in ins if k.startswith(x + "/")), None)
        if x is None:
            raise Refused(f"{side_p.name}: from key {k} is under none of its input folders")
        frm[new[x] + k[len(x):]] = n
    side2 = {**side, "_provenance": {**side["_provenance"], "inputs": [new[x] for x in ins]}, "from": frm}
    tmp.mkdir(parents=True, exist_ok=True)
    view = tmp / collect.name
    view.symlink_to(collect.resolve())
    view.with_name(view.name + ".json").write_text(json.dumps(side2, indent=1) + "\n")
    return view


def rel_keys(d) -> dict:
    """A dict whose keys are paths, with each key written relative to the repository (provenance only)."""
    return {rel(Path(k)): v for k, v in (d or {}).items()}


def rel_units(u):
    """S463.check_units' result with its folder and start-file paths relative to the repository."""
    return None if u is None else {k: rel_keys(v) if isinstance(v, dict) else v for k, v in u.items()}


def command_of(given: dict, recount_p: Path) -> str:
    """The command that writes this plate: with every input frozen, the one command (D155); else the paths given."""
    parts = ["uv", "run", "--frozen", "python", SCRIPT, "figure"]
    for k, flag in (("records", "--records"), ("collect", "--collect"), ("rlm_collect", "--rlm-collect"),
                    ("rlm_answers", "--rlm-answers"), ("g9", "--g9"), ("g9_retrievals", "--g9-retrievals"),
                    ("s6_g1", "--s6-g1")):
        if given.get(k) is not None:
            parts += [flag, rel(Path(given[k]).expanduser())]
    if recount_p != RECOUNT.resolve():
        parts += ["--recount", rel(recount_p)]
    return " ".join(parts)


# ---------------------------------------------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------------------------------------------
def questions_of() -> list:
    """The D5 key's questions, as the runner pins them."""
    from experiments.runner.experiment import questions
    return questions()


def key_groups() -> dict:
    """{question id: Rule 8 group}, from the D5 key the runner pins (as S463 reads it)."""
    from experiments.scorers.records import GROUP_OF_TYPE
    qs = questions_of()
    g = {q["id"]: GROUP_OF_TYPE[q["answer_type"]] for q in qs}
    if len(g) != N_Q or Counter(g.values()) != Counter(GROUP_N):
        raise Refused(f"the D5 key gives {len(g)} questions {dict(Counter(g.values()))}, want {N_Q} {GROUP_N}")
    return g, {q["id"]: q["answer_type"] for q in qs}, [q["id"] for q in qs]


def check_run(c: str, d: dict):
    """One set-up's answers.json checked whole: every key stored once, in results and completed_keys alike, every
    result of this run, set-up and index, no setup error."""
    R = d["results"]
    keys = [r["answer_key"] for r in R]
    if len(set(keys)) != len(keys) or set(keys) != set(d["completed_keys"]) \
            or len(d["completed_keys"]) != len(set(d["completed_keys"])):
        raise Refused(f"{c}: results and completed_keys disagree, or a key is stored twice")
    if any(r["run_id"] != run_of(c) or r["config"] != c or r["index_name"] != INDEX for r in R):
        raise Refused(f"{c}: a result of another run, set-up or index")
    if d.get("setup_errors"):
        raise Refused(f"{c}: {len(d['setup_errors'])} setup errors stored (Rule 10: re-run after the fix)")


def read_records(rec: Path):
    """Every copy checked against PULL.json; each set-up's answers.json checked whole."""
    pj = json.loads((rec / "PULL.json").read_text())
    for f, v in pj["files"].items():
        if sha256_file(rec / f) != v["sha256"]:
            raise Refused(f"{rec / f}: not the file PULL.json lists (sha256 differs)")
    data = {}
    for c in CONFIGS:
        d = json.loads((rec / "findings" / "runs" / run_of(c) / "answers.json").read_text())
        check_run(c, d)
        data[c] = d
    return pj, data


def read_g9(g9: Path, retrievals: Path | None = None):
    """G9's two set-ups (R1), read_records' checks on findings/recompute/g9_inputs: each answers.json against its line
    in that folder's PULL.json, then check_run. retrievals, when given, is a folder holding <run>/retrievals.jsonl of
    both set-ups; with none (g9_inputs took answers.json only) own time is not computed. Returns (the sha256 of each
    answers.json, {set-up: answers.json}, {set-up: retrievals bytes})."""
    pj = json.loads((g9 / "PULL.json").read_text())
    data, shas, retr = {}, {}, {}
    for c in STRESS:
        f = f"runs/{run_of(c)}/answers.json"
        if f not in pj["files"] or sha256_file(g9 / f) != pj["files"][f]["sha256"]:
            raise Refused(f"{g9 / f}: not the file PULL.json lists")
        shas[c] = pj["files"][f]["sha256"]
        data[c] = json.loads((g9 / f).read_text())
        check_run(c, data[c])
    if retrievals is not None:
        for c in STRESS:
            p = Path(retrievals) / run_of(c) / "retrievals.jsonl"
            if not p.is_file():
                raise Refused(f"{p}: no retrievals.jsonl for {c}")
            retr[c] = p.read_bytes()
    return shas, data, retr


# ---------------------------------------------------------------------------------------------------------------
# reproduce first (README.md:75-79)
# ---------------------------------------------------------------------------------------------------------------
def stop_log_counts(text: str) -> dict:
    out = {}
    for m in re.finditer(r"^\S+ (\w+) stopped after draw 1 \(draw-1 keys, later keys: (\d+) (\d+);", text, re.M):
        out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


def plan_g3_note(plan_path: Path = PLAN) -> str:
    """plan.csv's row G3, plan.csv as it stands (a check: never read at DESIGN_AT; audit 27 Oct F1, part 4)."""
    import csv
    with open(plan_path, newline="") as f:
        for row in csv.reader(f):
            if row and row[0] == "G3":
                return " | ".join(row)
    raise Refused(f"{rel(plan_path)}: no row G3")


def stress_names(src: str) -> list:
    """exp_03's STRESS_CONFIG_NAMES, read from its source text."""
    return re.findall(r'"(\w+)"', re.search(r"^STRESS_CONFIG_NAMES = \[([^\]]+)\]", src, re.M).group(1))


def stress_drawn(now_src: str | None = None, at_src: str | None = None) -> list:
    """exp_03's STRESS_CONFIG_NAMES as it stands, which must equal DESIGN_AT's (whose sha256 the provenance records):
    the planned answers draw it (audit 27 Oct F1, part 4). Refused when they differ."""
    now = stress_names(EXP03.read_text() if now_src is None else now_src)
    pin = stress_names(design_bytes(EXP03).decode() if at_src is None else at_src)
    if now != pin:
        raise Refused(f"{rel(EXP03)} STRESS_CONFIG_NAMES is {now}, {pin} at DESIGN_AT {DESIGN_AT}, whose sha256 the "
                      f"provenance records: move DESIGN_AT, then S494 --write")
    return now


def reproduce(rec: Path, data: dict, own_q82: dict, stop_log: str | None = None, plan_note: str | None = None):
    """(1) the stop log's key counts, (2) plan.csv's three draws of the two baselines, (3) the Q82 count by the module
    gate_distiller.sh runs. Returns what was compared; raises Refused (exit 2 in figure) on any difference."""
    probs, done = [], {}
    stop_log = stop_log if stop_log is not None else \
        (rec / "findings" / "recompute" / "G3_runs" / "g3_draw1_stop.log").read_text()
    logc = stop_log_counts(stop_log)
    if sorted(logc) != sorted(ORCH):
        probs.append(f"g3_draw1_stop.log names {sorted(logc)}, not the six orchestrator set-ups")
    for c in ORCH:
        d = Counter(r["draw"] for r in data[c]["results"])
        got = (d.get(1, 0), sum(v for k, v in d.items() if k != 1))
        if logc.get(c) != got:
            probs.append(f"{c}: the stop log reads draw-1 and later keys {logc.get(c)}, the records hold {got}")
        done[c] = {"stop_log": logc.get(c), "records": got}
    note = plan_note if plan_note is not None else plan_g3_note()
    if "raw_gemini and naive_rag hold all three draws" not in note:
        probs.append("plan.csv row G3 no longer states 'raw_gemini and naive_rag hold all three draws'")
    for c in BASELINES:
        d = Counter(r["draw"] for r in data[c]["results"])
        if dict(d) != {1: N_Q, 2: N_Q, 3: N_Q}:
            probs.append(f"{c}: plan.csv says all three draws, the records hold {dict(sorted(d.items()))}")
        done[c] = {"plan_csv": "all three draws", "records": dict(sorted(d.items()))}
    full_answers = rec / "findings" / "runs" / run_of("full_orchestrator") / "answers.json"
    if not full_answers.is_file():
        probs.append(f"{full_answers}: no full pipeline answers for distiller_firing.count()")
        raise Refused("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs))
    if distiller_moved():
        probs.append(f"{rel(DISTILLER)}'s code differs from DESIGN_AT {DESIGN_AT}'s: move DESIGN_AT, then S494 --write")
        raise Refused("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs))
    sys.path.insert(0, str(DISTILLER.parent))
    import distiller_firing
    mod = distiller_firing.count(full_answers)
    mine = own_q82["full_orchestrator"]
    for k_mod, k_own in (("answers", "answers"), ("step_attempts", "step_attempts"),
                         ("steps_over_threshold", "over_threshold"), ("threshold_chars", "threshold_chars")):
        if mod[k_mod] != mine[k_own]:
            probs.append(f"Q82 count: distiller_firing.count() {k_mod} {mod[k_mod]}, this script {mine[k_own]}")
    if mod["largest_step_output"]["chars"] != mine["largest_chars"]:
        probs.append(f"Q82 count: largest step output {mod['largest_step_output']['chars']} against "
                     f"{mine['largest_chars']}")
    done["q82_distiller_firing_count"] = {k: mod[k] for k in ("answers", "step_attempts", "steps_over_threshold",
                                                               "threshold_chars", "distill_status",
                                                               "largest_step_output")}
    if probs:
        raise Refused("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs))
    return done


# ---------------------------------------------------------------------------------------------------------------
# the numbers
# ---------------------------------------------------------------------------------------------------------------
def answer_search_s(retrievals: bytes, r: dict) -> float:
    """exp_03's answer_search_s() (Q150, D83), the same rule on the copied retrievals.jsonl bytes: the sum of search_s
    over the whole lines between the answer's generation.retrievals_bytes offsets whose run_id, item_id and run_draw
    are the answer's. A line without search_s raises (KeyError), as there."""
    a, b = r["generation"]["retrievals_bytes"]
    if b <= a or not retrievals:
        return 0.0
    data = retrievals[max(a - 1, 0):b]
    if a > 0:
        data = data[1:] if data[:1] == b"\n" else data[data.find(b"\n") + 1:] if b"\n" in data else b""
    key = (r["run_id"], r["question_id"], r["draw"])
    total = 0.0
    for line in data.decode("utf-8").split("\n")[:-1]:
        if line.strip():
            x = json.loads(line)
            if (x.get("run_id"), x.get("item_id"), x.get("run_draw")) == key:
                total += x["search_s"]
    return round(total, 6)


def threshold_chars() -> int:
    """observation_distiller's threshold as distiller_firing.py computes it from the lock (0.40 x num_ctx x 4)."""
    import tomllib
    return int(tomllib.loads(LOCK.read_text())["generation"]["num_ctx"] * 0.40) * 4


def quartiles(v):
    """Minimum, first quartile, median, third quartile, maximum (numpy's linear interpolation)."""
    import numpy as np
    a = np.asarray(v, dtype=float)
    return {"n": int(a.size), "minimum": float(a.min()), "q1": float(np.percentile(a, 25)),
            "median": float(np.percentile(a, 50)), "q3": float(np.percentile(a, 75)), "maximum": float(a.max()),
            "mean": float(a.mean())}


A_FLAGS = ("no_text", "any_failed_call", "stopped_by_google", "other_returned", "call_error", "cut_at_length")


def compute(data: dict, retrievals: dict, groups: dict, types: dict, order: list, thr: int, setups=None):
    """The judge-free rows from draw 1 of each of setups (default the eight G3 set-ups; with G3_ALL G9's two join
    fn["answers"], fn["a"], fn["b"] and fn["analyser"]: their step rows stay out of fn["f"] and q82, and
    fn["stress_steps"] holds their step counts). A stress set-up with no retrievals has own_time_s and search_s None.
    fn["answers"] (one row per answer: words, calls by status,
    own time, the analyser's decision, None where the set-up has no analyser or it is switched off), fn["analyser"]
    ({set-up: True when it has an analyser that is on}; a set-up mixing switched-off and working analysers is
    refused), fn["a"] (answers per set-up with each Rule 10 flag), fn["b"] (per set-up with its analyser on and
    Rule 8 group, the questions sent to a direct answer), fn["c"], fn["d"], fn["e"] (words, model calls,
    own time: per set-up quartiles, then per answer) and fn["f"] (every plan step attempt's raw output length, then
    per set-up quartiles), and q82 (Mentori's distiller count per orchestrator set-up). Refuses a draw 1 that is not
    the 135 questions once each."""
    fn = {k: [] for k in "abcdef"}
    fn["answers"] = []
    fn["analyser"] = {}                              # {config: True when the set-up has an analyser that is on}
    fn["stress_steps"] = {}                          # {stress set-up: step attempts by distiller status}
    q82 = {}
    for c in (CONFIGS if setups is None else setups):
        R = [r for r in data[c]["results"] if r["draw"] == 1]
        if sorted(r["question_id"] for r in R) != sorted(order):
            raise Refused(f"{c}: draw 1 is not the {N_Q} questions of the D5 key, once each")
        bad = [r["question_id"] for r in R if r["answer_type"] != types[r["question_id"]]]
        if bad:
            raise Refused(f"{c}: answer types that differ from the D5 key: {bad[:3]}")
        R.sort(key=lambda r: order.index(r["question_id"]))
        cnt = Counter()
        for r in R:
            g = r["generation"]
            st = Counter(x.get("status") for x in g.get("calls") or [])
            text = (r.get("generated_answer") or "")
            flags = {"no_text": not text.strip(),
                     "stopped_by_google": any(st[s] for s in GOOGLE_STOP),
                     "other_returned": any(st[s] for s in OTHER_RETURNED),
                     "call_error": any(st[s] for s in CALL_ERROR),
                     "cut_at_length": any(st[s] for s in CUT)}
            unknown = set(st) - KNOWN_STATUS
            if unknown:
                raise Refused(f"{r['answer_key']}: call statuses outside Rule 10's list: {sorted(unknown)}")
            failed = sum(v for s, v in st.items() if s not in ("ok", "length"))
            if failed != (g.get("failed_calls") or 0):
                raise Refused(f"{r['answer_key']}: {failed} failed calls by status, the record says {g.get('failed_calls')}")
            flags["any_failed_call"] = failed > 0
            for k, v in flags.items():
                cnt[k] += bool(v)
            no_search = c in STRESS and c not in retrievals      # g9_inputs holds no retrievals.jsonl
            search = None if no_search else answer_search_s(retrievals.get(c, b""), r) if c != "raw_gemini" else 0.0
            if not no_search and c != "raw_gemini" and g["retrievals_bytes"][1] > g["retrievals_bytes"][0] \
                    and c not in retrievals:
                raise Refused(f"{c}: retrievals_bytes name lines of a retrievals.jsonl that was not copied")
            calls_wall = g.get("sum_call_wall_s")
            if calls_wall is None or abs(calls_wall - round(sum(x.get("wall_s") or 0 for x in g["calls"]), 3)) > 1e-6:
                raise Refused(f"{r['answer_key']}: sum_call_wall_s does not add up from its calls")
            if g.get("llm_calls") != len(g.get("calls") or []):
                raise Refused(f"{r['answer_key']}: llm_calls {g.get('llm_calls')} is not its {len(g['calls'])} calls")
            words = len(text.split())
            if words != (g.get("word_count") if g.get("word_count") is not None else words):
                raise Refused(f"{r['answer_key']}: word_count {g.get('word_count')} is not the answer's {words} words")
            an_status = (g.get("analysis") or {}).get("status") if c in PIPED else None
            off = an_status == "switched_off"           # no analyser (D52): its stored decision is a default
            decision = (g.get("analysis") or {}).get("decision") if c in PIPED and not off else None
            steps = (g.get("steps") or []) if c in PIPED else []
            fn["answers"].append({
                "setup": LABEL[c], "config": c, "question_id": r["question_id"], "group": groups[r["question_id"]],
                "answer_type": r["answer_type"], "answer_key": r["answer_key"], "words": words,
                "model_calls": g["llm_calls"], "failed_calls": failed,
                "call_statuses": ", ".join(f"{s} {v}" for s, v in sorted(st.items())),
                "prompt_tokens": g.get("prompt_tokens"), "output_tokens": g.get("output_tokens"),
                "calls_wall_s": calls_wall, "search_s": search,
                "own_time_s": None if search is None else round(calls_wall + search, 6),
                "clock_time_s": g.get("answer_wall_s"), "analyser_decision": decision,
                "analyser_status": an_status,
                "answer_source": g.get("answer_source"), "plan_status": g.get("plan_status"),
                "step_attempts": len(steps), "cut_calls": st.get("length", 0),
                "google_calls": sum(st[s] for s in GOOGLE_STOP),
                "other_returned_calls": sum(st[s] for s in OTHER_RETURNED),
                "call_error_calls": sum(st[s] for s in CALL_ERROR),
                **{k: int(bool(v)) for k, v in flags.items()}})
            if c in STRESS:
                fn["stress_steps"].setdefault(c, Counter()).update(
                    (s.get("distill") or {}).get("status") or "not_asked" for s in steps)
                continue
            for s in steps:
                n = len(s.get("raw_content") or "")
                over = s["over_distill_threshold"] if "over_distill_threshold" in s else n > thr
                fn["f"].append({"setup": LABEL[c], "config": c, "row": "step", "answer_key": r["answer_key"],
                                "step_id": s.get("step_id"), "attempt_no": s.get("attempt_no"),
                                "tool_name": s.get("tool_name"),
                                "routing_strategy": (s.get("routing") or {}).get("strategy"),
                                "value": n, "over_threshold": int(bool(over)),
                                "distill_status": (s.get("distill") or {}).get("status") or "not_asked"})
        fn["a"].append({"setup": LABEL[c], "config": c, "answers_n": len(R), **{k: cnt[k] for k in A_FLAGS}})
        offs = Counter(x["analyser_status"] == "switched_off" for x in fn["answers"] if x["config"] == c)
        if offs[True] and offs[False]:
            raise Refused(f"{c}: the analyser is switched off on {offs[True]} answers and on on {offs[False]}")
        fn["analyser"][c] = c in PIPED and not offs[True]
        if fn["analyser"][c]:
            for gk, _ in GROUPS:
                Rg = [r for r in R if groups[r["question_id"]] == gk]
                dec = Counter((r["generation"].get("analysis") or {}).get("decision") for r in Rg)
                k = dec.get("direct_answer", 0)
                fn["b"].append({"setup": LABEL[c], "config": c, "group": gk, "questions_n": len(Rg),
                                "direct_answer_n": k, "plan_n": dec.get("needs_plan", 0),
                                "other_decision_n": len(Rg) - k - dec.get("needs_plan", 0),
                                "direct_answer_pct": 100.0 * k / len(Rg)})
        if c in ORCH:
            st_rows = [x for x in fn["f"] if x["config"] == c]
            vals = [x["value"] for x in st_rows]
            q = quartiles(vals)
            over = sum(x["over_threshold"] for x in st_rows)
            q82[c] = {"answers": len(R), "step_attempts": len(st_rows), "over_threshold": over,
                      "threshold_chars": thr, "largest_chars": int(q["maximum"]) if vals else 0}
            fn["f"].append({"setup": LABEL[c], "config": c, "row": "setup", "n": q["n"], "minimum": q["minimum"],
                            "q1": q["q1"], "median": q["median"], "q3": q["q3"], "maximum": q["maximum"],
                            "over_threshold_n": over, "threshold_chars": thr, "answers_n": len(R)})
        for L, field in (("c", "words"), ("d", "model_calls"), ("e", "own_time_s")):
            if c in STRESS:
                continue
            vals = [x[field] for x in fn["answers"] if x["config"] == c]
            q = quartiles(vals)
            fn[L].append({"setup": LABEL[c], "config": c, "row": "setup", "n": q["n"], "minimum": q["minimum"],
                          "q1": q["q1"], "median": q["median"], "q3": q["q3"], "maximum": q["maximum"],
                          "mean": q["mean"]})
    # the per-answer rows after the per-set-up rows (one sheet per panel, S448 R8 reads each whole)
    for L, field in (("c", "words"), ("d", "model_calls"), ("e", "own_time_s")):
        for x in fn["answers"]:
            if x["config"] in STRESS:
                continue
            fn[L].append({"setup": x["setup"], "config": x["config"], "row": "answer", "n": None,
                          "minimum": None, "q1": None, "median": None, "q3": None, "maximum": None, "mean": None,
                          "question_id": x["question_id"], "value": x[field]})
    return fn, q82
# ---------------------------------------------------------------------------------------------------------------
# the plan's answers (the plate's "of N")
# ---------------------------------------------------------------------------------------------------------------
def planned(q82_full_over: int) -> dict:
    """The answers Figure 4's written plan holds under D98, each part from its file:
    the two baselines, 3 draws x 135 (D79 Q134, answered before D98); the six other wave-1 set-ups (preflight.sh WAVE1),
    draw 1 on the 135 and draws 2 and 3 on the D98 subset (S464, 45); the two distiller set-ups (WAVE2) only if the
    Q82 count is above zero (Rule 12's zero branch), read here on the full pipeline's draw 1; the two G9 stress
    set-ups (exp_03 STRESS_CONFIG_NAMES; D94 F-a, D163: they run when the count stays zero), as the other wave-1
    set-ups, since G7 gave them draws 2 and 3 on D98's 45 (fig4.md C4);
    and RLM-10, Figure 3's 135 x 3 answers (G1; D83 Q148), reused, not answered in G3."""
    try:
        FR.check_committed(PREFLIGHT)                    # D155: the frozen copy, its sha256 in SHA256SUMS
    except FR.FrozenInputError as e:
        raise Refused(str(e)) from None
    pre = PREFLIGHT.read_text()
    wave1 = re.search(r'^WAVE1="([^"]+)"', pre, re.M).group(1).split()
    wave2 = re.search(r'^WAVE2="([^"]+)"', pre, re.M).group(1).split()
    stress = stress_drawn()
    if wave1 != CONFIGS:
        raise Refused(f"{rel(PREFLIGHT)} WAVE1 is {wave1}, not this plate's set-ups {CONFIGS}")
    if stress != STRESS:
        raise Refused(f"{rel(EXP03)} STRESS_CONFIG_NAMES is {stress}, not this plate's {STRESS}")
    sub = json.loads(D98_SUBSET.read_text())
    n_sub = len(sub["ids"])
    if n_sub != sub["n"]:
        raise Refused(f"{rel(D98_SUBSET)}: {n_sub} ids, n says {sub['n']}")
    per_d98 = N_Q + 2 * n_sub
    parts = {"baselines (3 draws each, D79 Q134)": 2 * 3 * N_Q,
             "six wave-1 set-ups (draw 1 + D98 subset draws 2 and 3)": (len(wave1) - 2) * per_d98,
             "distiller set-ups (WAVE2)": 0 if q82_full_over == 0 else len(wave2) * per_d98,
             "G9 stress set-ups (draw 1 + D98 subset draws 2 and 3)": len(stress) * per_d98 if q82_full_over == 0 else 0,
             "RLM-10 (G1, Figure 3's answers, D83 Q148)": 3 * N_Q}
    return {"parts": parts, "N": sum(parts.values()), "subset_n": n_sub, "wave2": wave2, "stress": stress,
            "zero_branch": q82_full_over == 0}


# ---------------------------------------------------------------------------------------------------------------
# the judge's rows (S3's collect output) and RLM-10's records
# ---------------------------------------------------------------------------------------------------------------
def judge_cell(r: dict, group: str) -> dict:
    """One collect row as a cell, by S463.read_collect's mapping: (a) "ok" with the Rule 8 metric's number = scored;
    "ok" without it, or a judge failure (S463.JUDGE_FAILED) = unscored (left out); "no_answer" = failed (Rule 10: a
    fail, and not refused). Any other status is refused."""
    m = s463()
    st = (r.get("a") or {}).get("status")
    if st == "ok":
        v = (r["a"].get("scores") or {}).get(m.METRIC[group])
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return {"kind": "scored", "score": v}
        return {"kind": "unscored", "why": f"ok, no {m.METRIC[group]} score"}
    if st == "no_answer":
        return {"kind": "failed", "why": r.get("error") or "no answer stored"}
    if st in m.JUDGE_FAILED:
        return {"kind": "unscored", "why": st}
    raise Refused(f"{r.get('answer_key')}: (a) status {st!r} is none of ok, no_answer, {sorted(m.JUDGE_FAILED)}")


def read_g3_collect(collect: Path, groups: dict, check_units: bool = True, need_stress: bool = False) -> dict:
    """G3's judge rows of draw 1: S463.read_collect's checks, written for set G3 (read_collect itself is bound to G1's
    strategies, its reruns and its replace pass, which G3 does not have). Refuses: no sidecar, or one whose rows, set
    (G3) or run_sha256 differ from the file; a replace pass (G3 has none); rows under more than one run_sha256 or a
    lock other than D88's; a row twice; a row that is not a G3 answer (configuration, run id, question, draw, answer
    key); a row judged with the other group's prompt; a draw-1 answer with no row, the two stress set-ups' included
    when the collect holds any row of theirs or need_stress is set (the frozen 41d3105d holds none: "stress_judged"
    False). Then S463.check_units() on the
    judging units the sidecar names (start files under D88's lock, the lock's judge and digest in each header, each
    unit's recheck equal and complete for draw 1's phase)."""
    m = s463()
    side_p = collect.with_name(collect.name + ".json")
    if not collect.is_file():
        raise Refused(f"{collect} does not exist")
    if not side_p.is_file():
        raise Refused(f"{side_p.name} missing: collect writes it beside its output; without it the rows cannot be tied "
                      f"to one run_sha256")
    side = json.loads(side_p.read_text())
    rows = [json.loads(x) for x in collect.read_text().splitlines() if x.strip()]
    if side.get("rows") != len(rows):
        raise Refused(f"{side_p.name} says {side.get('rows')} rows, {collect.name} holds {len(rows)}")
    if side.get("set") != "G3":
        raise Refused(f"{side_p.name}: set {side.get('set')!r}, not 'G3' (s3_guard.py collect --set G3)")
    if side.get("replaced", 0) or side.get("added_by_replace", 0):
        raise Refused(f"{side_p.name}: {side.get('replaced')} rows replaced, {side.get('added_by_replace')} added by a "
                      f"replace pass; G3 has no rerun pass to read")
    runs = Counter(r.get("run_sha256") for r in rows)
    if len(runs) != 1:
        raise Refused(f"the rows carry {len(runs)} run_sha256 values (another lock, code or judge setting): "
                      + "; ".join(f"{str(k)[:12]} {n} rows" for k, n in runs.most_common()))
    run_sha = next(iter(runs))
    if side.get("run_sha256") != run_sha:
        raise Refused(f"the sidecar's run_sha256 {str(side.get('run_sha256'))[:12]} is not the rows' {run_sha[:12]}")
    if m.LOCK_WANT != LOCK_WANT:
        raise Refused(f"S463 judges under {m.LOCK_WANT[:8]}, this plate's records under {LOCK_WANT[:8]}")
    locks = Counter(r.get("lock_sha256") for r in rows)
    if not locks or not set(locks) <= LOCKS_OK:
        raise Refused(f"the rows carry lock_sha256 {', '.join(f'{str(k)[:8]} ({n} rows)' for k, n in locks.items())}; "
                      f"D88 judges under {LOCK_WANT[:8]} only")
    seen, cells, bad, other = {}, {}, [], Counter()
    for i, r in enumerate(rows, 1):
        c, q, d = r.get("config"), r.get("question_id"), r.get("draw")
        k = (c, q, d)
        if k in seen:
            raise Refused(f"rows {seen[k]} and {i} are both {k}: collect writes one row per answer")
        seen[k] = i
        if c not in G3_ALL or r.get("run_id") != run_of(c) or q not in groups or d not in (1, 2, 3) \
                or r.get("answer_key") != f"{INDEX}|{c}|{q}|d{d}":
            bad.append(f"row {i} {k}: not a G3 answer (run_id {r.get('run_id')!r}, answer_key {r.get('answer_key')!r})")
            continue
        if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
            bad.append(f"row {i} {k}: judged with the {'answerable' if r.get('answerable_prompt') else 'decline'} "
                       f"prompt, Rule 8's group is {groups[q]}")
            continue
        if d != 1:
            other[d] += 1
            continue
        cells[k] = {**judge_cell(r, groups[q]), "key": r["answer_key"], "item_sha256": r.get("item_sha256"),
                    "at": r.get("at")}
    if bad:
        raise Refused(f"{len(bad)} rows refused, first: {bad[0]}")
    stress_judged = need_stress or any(c in STRESS for c, _, _ in seen)
    missing = [(c, q) for c in (G3_ALL if stress_judged else CONFIGS) for q in sorted(groups) if (c, q, 1) not in cells]
    if missing:
        per = Counter(c for c, _ in missing)
        raise Refused(f"{len(missing)} draw-1 answers have no judge row: "
                      + "; ".join(f"{LABEL[c]} {n}" for c, n in per.items()))
    units = None
    if check_units:
        ins = [Path(x) for x in ((side.get("_provenance") or {}).get("inputs") or [])]
        if not ins:
            raise Refused(f"{side_p.name} names no input folder: the judging units cannot be checked")
        units = s463_call(m.check_units, ins, run_sha, [1])
    return {"cells": cells, "rows": len(rows), "rows_other_draws": dict(other), "run_sha256": run_sha,
            "lock_sha256": LOCK_WANT, "set": side.get("set"), "collect_at": (side.get("_provenance") or {}).get("at"),
            "stress_judged": stress_judged, "units": units, "outs_here": [str(x) for x in ((side.get("_provenance") or {}).get("inputs") or [])]}


def g3_read_only(d: dict) -> bool:
    """D188: the G3 judge rows this plate reads, draw 1 of its eight set-ups and G9's two (D98); judge_rows_v25.choose
    sets every other row aside (draws 2 and 3)."""
    return d.get("draw") == 1 and d.get("config") in G3_ALL


def merge_g3(cells: dict, choice: dict, groups: dict) -> tuple[dict, dict]:
    """D188: G3's draw-1 cells as judge_rows_v25.choose picked their rows. A cell whose answer has a key v2.5 row is
    made again from that row (judge_cell, with read_g3_collect's prompt check: the row's answerable_prompt must be the
    Rule 8 group's); every other cell must be the v2.4 row chosen (same item_sha256). A cell with no row chosen is
    refused. Returns (the new cells, the count of cells from v2.5 and of those still on v2.4 awaiting S6)."""
    out, n25, awaiting, bad = {}, 0, 0, []
    for k in sorted(cells, key=lambda t: (G3_ALL.index(t[0]), t[1], t[2])):
        c, q, d = k
        cell = cells[k]
        ch = choice.get((run_of(c), c, q, d))
        if ch is None:
            bad.append(f"{k}: no entry in the choice")
            continue
        if ch["status"] == "v2.5":
            r = ch["row"]
            if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
                bad.append(f"{k}: the v2.5 row was judged with the "
                           f"{'answerable' if r.get('answerable_prompt') else 'decline'} prompt, Rule 8's group is "
                           f"{groups[q]}")
                continue
            if r.get("answer_key") != cell["key"]:
                bad.append(f"{k}: the v2.5 row is {r.get('answer_key')}, the cell {cell['key']}")
                continue
            out[k] = {**judge_cell(r, groups[q]), "key": r["answer_key"], "item_sha256": r.get("item_sha256"),
                      "at": r.get("at"), "key_version": "v2.5"}
            n25 += 1
        elif ch["status"] in ("v2.4", "v2.4 awaiting S6"):
            if (ch["row"] or {}).get("item_sha256") != cell.get("item_sha256"):
                bad.append(f"{k}: the v2.4 row chosen is not the collect's row read")
                continue
            out[k] = cell
            awaiting += ch["status"] == "v2.4 awaiting S6"
        else:
            bad.append(f"{k}: no judge row chosen ({ch['status']})")
    if bad:
        raise Refused(f"judge_rows_v25 (G3): {len(bad)} cells refused, first: {bad[0]}")
    return out, {"cells_from_v25": n25, "awaiting_s6": awaiting}


def g3_judge_rows(g3: dict, collect: Path, groups: dict, answers: list, s6_root: Path | None = None) -> dict:
    """D188: G3's draw-1 cells read through scripts/judge_rows_v25.py, after read_g3_collect's checks of the v2.4
    collect (the reproduction made first). The v2.4 source is the collect read_g3_collect read, held to the out it read
    (out_g3; judge_rows_v25.check_v24: key_hash on all_v2_4.json, the headers' run_sha256 recomputed). The v2.5 source
    is out_s6_g3 under s6_root (default: the folder holding out_g3), present when that folder is: s3_guard.py collect
    run on it into a temporary file, then check_v25 (S512's key_hash, pins, run_sha256, the 132) and S463.check_units
    on its draw-1 units. out_s6_g7_g3 (G7, draws 2 and 3) is not read: this plate draws draw 1 (D98). choose takes
    G3's per-configuration rule (g7_configs) and reads draw 1 of the ten set-ups only (g3_read_only); merge_g3 makes
    the cells. Returns the cells and the counts the outputs record ("provisional" while an answer of the 132 is still
    read from key v2.4)."""
    ins = [Path(x) for x in g3.get("outs_here") or []]
    if len(ins) != 1 or ins[0].name != G3_JUDGE_OUT:
        raise Refused(f"judge_rows_v25 (G3): the collect read {[str(x) for x in ins]}, not one {G3_JUDGE_OUT} folder")
    v24_root = ins[0].parent
    try:
        srcs = JR.sources(v24_root, "G3")
        src24, s6 = srcs[0], JR.sources(Path(s6_root) if s6_root is not None else v24_root, "G3")[1]
        if [str(o) for o in src24["outs"]] != [str(ins[0])]:
            raise Refused(f"judge_rows_v25 (G3): the reader's v2.4 out {src24['outs']} is not the out collect read "
                          f"({ins[0]})")
        info = {"G3": {"kind": JR.V24, "present": True}, "S6G3": {"kind": JR.V25_CHANGED, "present": s6["present"],
                                                                 "missing": [Path(m).name for m in s6["missing"]]},
                "S6G7G3": {"kind": JR.V25_ALL, "present": None, "read": False,
                           "why": "draws 2 and 3 (G7) are not drawn in this plate (D98)"}}
        loaded = [JR.read_source(src24, collect)]
        units25 = None
        if s6["present"]:
            with tempfile.TemporaryDirectory(prefix="S472_s6_") as t:
                dest = Path(t) / "s6g3_collect.jsonl"
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    rc = JR.guard().collect(s6["outs"], None, dest, s6["set"])
                if rc:
                    raise Refused(f"judge_rows_v25 (G3): s3_guard collect refused S6G3: {buf.getvalue().strip()[-300:]}")
                L25 = JR.read_source(s6, dest)
            units25 = s463_call(s463().check_units, list(s6["outs"]), L25.run_sha256, [1])
            loaded.append(L25)
        ans = [{"run_id": run_of(x["config"]), "config": x["config"], "question_id": x["question_id"], "draw": 1,
                "answer_key": x["answer_key"]} for x in answers if (x["config"], x["question_id"], 1) in g3["cells"]]
        # D203: S6G3 also judged G9's two set-ups; since fig4_g9_inputs their draw-1 cells are in the G3 collect, so
        # their key v2.5 rows are read like G3's; any S6G3 row of a cell outside the plate is set aside, never read
        have = {(c, q) for (c, q, _) in g3["cells"]}
        choice = JR.choose(ans, loaded, g7_configs=JR.g7_configs("G3"),
                           read_only=lambda d: g3_read_only(d) and (d.get("config"), d.get("question_id")) in have)
        rep = JR.report(choice)
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25 (G3): {e}") from None
    for L in loaded:
        info[L.name].update(run_sha256=L.run_sha256, rows=len(L.rows),
                            rows_set_aside=choice["_sources"][L.name]["set_aside"])
    cells, n = merge_g3(g3["cells"], choice, groups)
    nq = len({q for (_, q, _) in cells if q in set(JR.S512.changed_ids())})
    status = (f"awaiting S6: {n['awaiting_s6']:,} of the {len(cells):,} G3 answers read (the {nq} questions of S512's "
              f"132 changed ones that G3 asks) are read from key v2.4 until S6G3 judges them on key v2.5"
              if n["awaiting_s6"] else f"key v2.5 for every G3 answer of the 132 changed questions ({n['cells_from_v25']:,})")
    return {"cells": cells, "record": {
        "reader": "scripts/judge_rows_v25.py (D188): an answer's key v2.5 row (S512, out_s6_g3) where one exists, else "
                  "its key v2.4 row (out_g3); draw 1 of the G3 and G9 set-ups read, every other row set aside",
        "sources": info, "status": status, "provisional": bool(n["awaiting_s6"]), "answers_read": len(cells),
        "cells_from_v25": n["cells_from_v25"], "awaiting_s6_read": n["awaiting_s6"], "by_status": rep["by_status"],
        "units_v25": rel_units(units25)}}


def rlm_answer(q: str, key: str, cell: dict, rec: dict, raw: dict, groups: dict):
    """One RLM-10 answer's checks and row (read_rlm, tested by selftest on altered copies): a judge "failed" exactly
    where S463.read_answers' record is not "ok"; the raw line is the answer judged; llm_calls equal to its calls and
    to S457.exp01_row's count (rec["cost"]["calls"]); every call status in Rule 10's list. Returns (cell, row)."""
    if (cell["kind"] == "failed") != (rec["status"] != "ok"):
        raise Refused(f"{key}: judge {cell['kind']}, record status {rec['status']} ({rec['source']})")
    if raw.get("answer_key") != key:
        raise Refused(f"{rec['source']}: holds {raw.get('answer_key')}, not {key}")
    g = raw.get("generation") or {}
    calls = g.get("calls") or []
    if g.get("llm_calls") != len(calls) or rec["cost"]["calls"] != len(calls):
        raise Refused(f"{key}: llm_calls {g.get('llm_calls')}, S457.exp01_row {rec['cost']['calls']}, "
                      f"{len(calls)} calls")
    st = Counter(x.get("status") for x in calls)
    if set(st) - KNOWN_STATUS:
        raise Refused(f"{key}: call statuses outside Rule 10's list: {sorted(set(st) - KNOWN_STATUS)}")
    text = rec["answer"] or ""
    cell_out = {"kind": cell["kind"], "score": cell.get("score"), "key": key, "item_sha256": cell.get("item_sha256")}
    row = {"setup": LABEL[RLM], "config": RLM, "question_id": q, "group": groups[q], "answer_key": key,
           "words": len(text.split()) if text.strip() else None, "no_text": int(not text.strip()),
           "model_calls": len(calls),
           "failed_calls": sum(v for s, v in st.items() if s not in ("ok", "length")),
           "cut_calls": st.get("length", 0), "google_calls": sum(st[s] for s in GOOGLE_STOP),
           "other_returned_calls": sum(st[s] for s in OTHER_RETURNED),
           "call_error_calls": sum(st[s] for s in CALL_ERROR),
           "call_statuses": ", ".join(f"{s} {v}" for s, v in sorted(st.items())),
           "own_time_s": None, "analyser_decision": None, "record": rec["source"]}
    return cell_out, row


def read_rlm(collect: Path, answers_dir: Path, groups: dict, s6_root: Path) -> dict:
    """RLM-10's draw 1: its judge rows by S463.read_collect (G1's collect, with its checks: sidecar, one run_sha256,
    D88's lock, every G1 draw-1 answer present, G1's 15 reruns from their own pass, the judging units), then, D188, by
    S463.judge_rows (scripts/judge_rows_v25.py, as Figure 3 reads them: an answer's key v2.5 row, out_s6_g1 with
    out_s6_g1r15 under s6_root, where one exists, else its key v2.4 row). No key v2.4 fallback: every RLM-10 answer of a
    changed question must have its key v2.5 row, else refused. Its records by
    S463.read_answers (each answers file against its MANIFEST.sha256, each key's last line). Each record must be the
    answer judged, on the row read_collect read (cells_v24, the v2.4 anchor) and on the row judge_rows chose (cells):
    the same answer key, and a judge "no_answer" exactly where the record is not "ok" (no text or an error). Per
    answer: words (the answer split on white space; None when it has no text), model calls (the entries of
    generation.calls, which must equal llm_calls and S457.exp01_row's count), and its calls by status (every status
    in Rule 10's list)."""
    m = s463()
    reruns = s463_call(m.rerun_keys)
    got = s463_call(m.read_collect, collect, [1], groups, reruns)
    v24 = {k: dict(v) for k, v in got["cells"].items()}
    jr = s463_call(m.judge_rows, got, collect, groups, reruns, [1], s6_root=s6_root)   # a v2.5 row replaces a cell
    recs, inputs, _ = s463_call(m.read_answers, [answers_dir])
    cells, cells24, rows, lines = {}, {}, {}, {}
    for q in sorted(groups):
        key = f"{INDEX}|{RLM}|{q}|d1"
        cell, cell24 = got["cells"].get((RLM, q, 1)), v24.get((RLM, q, 1))
        if cell is None or cell["key"] != key or cell24 is None or cell24["key"] != key:
            raise Refused(f"RLM-10 {q}: no judge row with key {key}")
        rec = recs.get(key)
        if rec is None:
            raise Refused(f"{key}: no record in {answers_dir}")
        path, ln = rec["source"].rsplit(":", 1)
        if path not in lines:
            lines[path] = Path(path).read_text().splitlines()
        raw = json.loads(lines[path][int(ln) - 1])
        cells24[q], _ = rlm_answer(q, key, cell24, rec, raw, groups)
        cells[q], rows[q] = rlm_answer(q, key, cell, rec, raw, groups)
    n25 = sum(1 for q in groups if got["cells"][(RLM, q, 1)].get("key_version") == "v2.5")
    nch = sum(1 for q in groups if q in set(JR.S512.changed_ids()))
    if n25 != nch:
        raise Refused(f"RLM-10: {n25} of its {nch} draw-1 answers of changed questions have a key v2.5 row in "
                      f"{rel(s6_root)}: this plate reads RLM-10 on key v2.5 only (D188), no key v2.4 fallback")
    rec_jr = {**m.judge_rows_record(jr), "rlm_10_draw_1": {"cells_from_v25": n25, "changed_questions": nch,
                                                           "awaiting_s6": 0, "frozen_set": rel(s6_root)}}
    rec_jr["units_v25"] = rel_units(rec_jr.get("units_v25"))
    return {"cells": cells, "cells_v24": cells24, "rows": rows, "run_sha256": got["run_sha256"],
            "units": got["units"], "answers_inputs": inputs,
            "collect_at": (got["side"].get("_provenance") or {}).get("at"), "rows_read": got["rows"],
            "judge_rows": rec_jr}


def join_judge(fn: dict, g3: dict, rlm: dict, groups: dict) -> dict:
    """Each draw-1 answer of G3 and G9 joined to its judge row (prep.py's join): the same answer key, and a judge
    "failed" exactly where the record has no text. Returns the cells, {(config, question, 1): cell}: every set-up's,
    less G9's two while the collect holds no row of theirs (g3["stress_judged"] False; their answers keep their rows,
    with judge_kind and judge_score None)."""
    cells = {}
    stress_judged = g3.get("stress_judged", False)
    for x in fn["answers"]:
        k = (x["config"], x["question_id"], 1)
        if x["config"] in STRESS and not stress_judged:
            x.update(judge_kind=None, judge_score=None)
            continue
        cell = g3["cells"].get(k)
        if cell is None:
            raise Refused(f"{x['answer_key']}: no judge row")
        if cell["key"] != x["answer_key"]:
            raise Refused(f"{x['answer_key']}: the judge row is {cell['key']}")
        if (cell["kind"] == "failed") != bool(x["no_text"]):
            raise Refused(f"{x['answer_key']}: judge {cell['kind']}, record no_text {x['no_text']}")
        x.update(judge_kind=cell["kind"], judge_score=cell.get("score"))
        cells[k] = {"kind": cell["kind"], "score": cell.get("score")}
    for q, cell in rlm["cells"].items():
        cells[(RLM, q, 1)] = {"kind": cell["kind"], "score": cell.get("score")}
    want = {(c, q, 1) for c in (ALL if stress_judged else NINE) for q in groups}
    if set(cells) != want:
        raise Refused(f"{len(want - set(cells))} of the set-ups' draw-1 answers have no cell")
    return cells


# ---------------------------------------------------------------------------------------------------------------
# the statistics (LIST.md Rules 2, 3, 9, 10, 12), with S463's own functions
# ---------------------------------------------------------------------------------------------------------------
def holm(ps: dict) -> dict:
    """Holm's step-down adjustment (Rule 12): the i-th smallest P (from 0) times (m - i), capped at 1, kept from
    falling below the one before it."""
    out, run, order = {}, 0.0, sorted(ps, key=lambda c: (ps[c], c))
    for i, c in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[c]))
        out[c] = run
    return out


def judged_setups(cells: dict, order: list) -> list:
    """The set-ups with judge rows, in plate order."""
    return [c for c in ALL if (c, order[0], 1) in cells]


def statistics(cells: dict, groups: dict, order: list) -> dict:
    """On draw 1 of the set-ups with judge rows (D98): per threshold 4 and 3, on the 86 answerable questions, each set-up's pass
    count, pass rate and Rule 2 interval (S463.shares, S463.summarise; a failed answer a fail, an unscored row left out)
    and each set-up minus the full pipeline (S463.pairs, S463.pair: mean difference, Rule 2 interval, exact two-sided
    sign-flip P), Holm over the five orchestrator set-ups; on the 39, each set-up's refused count, refusal rate and
    interval at S463.REFUSAL_T (Rule 9; a zero or a 100% with its one-sided bound); on the 10, false-premise questions passed at
    correctness FP_T or more and at FP_RELAXED or more (Rule 9, counts only)."""
    by = {g: [q for q in order if groups[q] == g] for g, _ in GROUPS}
    out = {"pass": {}, "vs_full": {}, "pass_shares": {}}
    setups = judged_setups(cells, order)
    with s463_configs(setups) as m:
        for t in (PASS_T, PASS_RELAXED):
            sh = m.shares(cells, by["answerable"], [1], t)
            sm = m.summarise(sh, by["answerable"], [1])
            pr = m.pairs(sh, by["answerable"])
            vs = {c: dict(m.pair(pr, c, FULL)) for c in setups if c != FULL}
            for c, p in holm({c: vs[c]["p"] for c in FAMILY}).items():
                vs[c]["p_holm"] = p
            out["pass"][t] = {c: {"passed": sum(1 for q in by["answerable"] if sh[c][q][0] == 1),
                                  **{k: sm[c][k] for k in ("rate", "lo", "hi", "questions_with_share")}}
                              for c in setups}
            out["vs_full"][t] = vs
            out["pass_shares"][t] = sh
        shr = m.shares(cells, by["not_answerable"], [1], m.REFUSAL_T)
        smr = m.summarise(shr, by["not_answerable"], [1])
        out["refusal"] = {c: {"refused": sum(1 for q in by["not_answerable"] if shr[c][q][0] == 1),
                              **{k: smr[c][k] for k in ("rate", "lo", "hi", "questions_with_share", "zero_bound",
                                                        "full_bound")}}
                          for c in setups}
        out["refusal_shares"] = shr
        out["refusal_t"] = m.REFUSAL_T
        fp = m.shares(cells, by["false_premise"], [1], FP_T)
        out["false_premise"] = {c: {"passed": sum(1 for q in by["false_premise"] if fp[c][q][0] == 1),
                                    "n": sum(1 for q in by["false_premise"] if fp[c][q][0] is not None)}
                                for c in setups}
        fp3 = m.shares(cells, by["false_premise"], [1], FP_RELAXED)
        out["false_premise_relaxed"] = {c: {"passed": sum(1 for q in by["false_premise"] if fp3[c][q][0] == 1),
                                            "n": sum(1 for q in by["false_premise"] if fp3[c][q][0] is not None)}
                                        for c in setups}
    out["unscored"] = {c: sum(1 for (cc, _, _), v in cells.items() if cc == c and v["kind"] == "unscored")
                       for c in setups}
    out["failed"] = {c: sum(1 for (cc, _, _), v in cells.items() if cc == c and v["kind"] == "failed") for c in setups}
    return out


RECOUNT = ROOT / "findings" / "recompute" / "S480_fig4_recount.json"


def read_inputs_sha(rec: Path, collect: Path, rlm_collect: Path, rlm_answers: Path, rlm: dict, g9_sha: dict,
                    s6_g1: Path) -> dict:
    """The sha256 of each file this run read that the recount also reads, under the recount's names: the eight
    answers.json (hashed here), G9's two (read_g9's sha256 of the files it read), the two collects and their sidecars
    (hashed here), RLM-10's answers.jsonl (the sha256 S463.read_answers computed of the file it read), and the
    SHA256SUMS of the frozen set holding RLM-10's key v2.5 rows (s6_g1_sums, which names every file of that set)."""
    side = lambda p: p.with_name(p.name + ".json")                     # noqa: E731
    out = {f"answers_json:{c}": sha256_file(rec / "findings" / "runs" / run_of(c) / "answers.json") for c in CONFIGS}
    out.update({f"answers_json:{c}": g9_sha[c] for c in STRESS})
    out.update({"g3_collect": sha256_file(collect), "g3_collect_sidecar": sha256_file(side(collect)),
                "g1_collect": sha256_file(rlm_collect), "g1_collect_sidecar": sha256_file(side(rlm_collect)),
                "s6_g1_sums": sha256_file(s6_g1 / "SHA256SUMS")})
    jl = str(rlm_answers / f"exp_01__{RLM}__{INDEX}" / "answers.jsonl")
    if jl not in rlm["answers_inputs"]:
        raise Refused(f"S463.read_answers read no {jl}")
    out["rlm_answers_jsonl"] = rlm["answers_inputs"][jl]
    return out


def my_counts(st: dict, fn: dict, groups: dict) -> dict:
    """This run's counts under the recount's names (S480_fig4_recount.py's docstring defines each)."""
    out = {}
    for c in st["pass"][PASS_T]:
        on = c in PIPED and fn["analyser"].get(c)
        out[c] = {f"answerable_pass_{PASS_T}": st["pass"][PASS_T][c]["passed"],
                  f"answerable_pass_{PASS_RELAXED}": st["pass"][PASS_RELAXED][c]["passed"],
                  "answerable_judged": st["pass"][PASS_T][c]["questions_with_share"],
                  "not_answerable_refused_3": st["refusal"][c]["refused"],
                  "not_answerable_judged": st["refusal"][c]["questions_with_share"],
                  f"false_premise_pass_{FP_T}": st["false_premise"][c]["passed"],
                  f"false_premise_pass_{FP_RELAXED}": st["false_premise_relaxed"][c]["passed"],
                  "false_premise_judged": st["false_premise"][c]["n"],
                  "judged_no_answer": st["failed"][c], "unscored": st["unscored"][c],
                  "not_answerable_direct_answer": sum(1 for x in fn["answers"] if x["config"] == c
                                                      and groups[x["question_id"]] == "not_answerable"
                                                      and x.get("analyser_decision") == "direct_answer")
                  if on else None}
    return out


def stress_counts(fn: dict, groups: dict) -> dict:
    """G9's two set-ups as the answer records give them, under the names of the recount's stress_records."""
    out = {}
    for c in STRESS:
        rows = [x for x in fn["answers"] if x["config"] == c]
        if rows:
            out[c] = {"answers": len(rows), "no_text": sum(x["no_text"] for x in rows),
                      "words": sum(x["words"] for x in rows), "model_calls": sum(x["model_calls"] for x in rows),
                      "failed_calls": sum(x["failed_calls"] for x in rows),
                      "cut_calls": sum(x["cut_calls"] for x in rows),
                      "not_answerable_direct_answer": sum(1 for x in rows if groups[x["question_id"]] == "not_answerable"
                                                          and x.get("analyser_decision") == "direct_answer")}
    return out


def s480_head_sha() -> str:
    """The sha256 of scripts/S480_fig4_recount.py at HEAD (git show, read only)."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:scripts/S480_fig4_recount.py"], capture_output=True)
    if r.returncode:
        raise Refused(f"git show HEAD:scripts/S480_fig4_recount.py failed: {r.stderr.decode(errors='replace')[:200]}")
    return hashlib.sha256(r.stdout).hexdigest()


def check_recount_script(recount: dict, want: str, where: str = "HEAD"):
    """D136 Q12: the recount must come from S480 as it stands at HEAD. want is that file's sha256; where names it."""
    got = (recount.get("provenance") or {}).get("script_sha256")
    if got != want:
        raise Refused(f"REPRODUCTION FAILED, nothing written: the recount was written by S480 sha256 {str(got)[:12]}, "
                      f"S480 at {where} is {want[:12]}: run scripts/S480_fig4_recount.py first")
    return {"script_sha256": got, "equal_to": where}


def reproduce_new(collect: Path, st: dict, cells: dict, groups: dict, order: list, frozen: Path) -> dict:
    """Two checks before writing (fig4.md section 5): every row of frozen collect 41d3105d is in the collect read,
    equal; and the nine set-ups' statistics (pass and difference at 4 and 3, refusal, false premise) are equal with and
    without the stress set-ups. Refused on any difference."""
    if sha256_file(frozen) != FROZEN_COLLECT_RIGHT:
        raise Refused(f"REPRODUCTION FAILED, nothing written: {rel(frozen)} is not the frozen collect "
                      f"{FROZEN_COLLECT_RIGHT[:8]}")
    key = lambda r: (r.get("config"), r.get("question_id"), r.get("draw"))       # noqa: E731
    new = {key(r): r for r in map(json.loads, Path(collect).read_text().splitlines())}
    old = list(map(json.loads, frozen.read_text().splitlines()))
    moved = [key(r) for r in old if new.get(key(r)) != r]
    if moved:
        raise Refused(f"REPRODUCTION FAILED, nothing written: {len(moved)} rows of collect "
                      f"{FROZEN_COLLECT_RIGHT[:8]} differ or are gone in the collect read, first {moved[0]}")
    done = {"frozen_collect_rows_equal": len(old), "collect_rows": len(new)}
    if not any(c in STRESS for c in st["pass"][PASS_T]):
        done["nine_with_and_without_stress"] = "no stress judge rows yet: the two statistics are one call"
        return done
    st9 = statistics({k: v for k, v in cells.items() if k[0] in NINE}, groups, order)
    probs = []
    for c in NINE:
        for t in (PASS_T, PASS_RELAXED):
            if st9["pass"][t][c] != st["pass"][t][c]:
                probs.append(f"{c}: pass at {t}")
            if c != FULL and st9["vs_full"][t][c] != st["vs_full"][t][c]:
                probs.append(f"{c}: difference at {t}")
        for part in ("refusal", "false_premise", "false_premise_relaxed"):
            if st9[part][c] != st[part][c]:
                probs.append(f"{c}: {part}")
    if probs:
        raise Refused("REPRODUCTION FAILED, nothing written: the nine set-ups moved when the stress set-ups were "
                      "added: " + "; ".join(probs[:5]))
    done["nine_with_and_without_stress"] = "equal"
    return done


def reproduce_recount(st: dict, fn: dict, groups: dict, recount: dict, read_sha: dict, key: str = "counts") -> dict:
    """Reproduction (4), O1: the recount (S480) must be made from the files this run read, every input it records
    with the sha256 of the file read here and no input missing on either side ("recount made from other files");
    then every count my_counts() gives must equal the recount's under key, per set-up. D188: figure calls it twice,
    key "counts_v24" with the statistics of the v2.4 cells (S480's plain recount of the collects, the anchor), then
    "counts" with those of the cells judge_rows_v25 chose (S480's count of the same choice). A recount without key
    (one S480 wrote before D188) is refused. G9's answer counts (stress_counts) must equal the recount's
    stress_records. Returns what was compared."""
    ins = recount.get("inputs") or {}
    other = sorted(set(ins) ^ set(read_sha)) + sorted(k for k in set(ins) & set(read_sha)
                                                      if (ins[k] or {}).get("sha256") != read_sha[k])
    if other:
        raise Refused("REPRODUCTION FAILED, nothing written: recount made from other files: "
                      + "; ".join(f"{k} recount {str((ins.get(k) or {}).get('sha256'))[:12]}, read here "
                                  f"{str(read_sha.get(k))[:12]}" for k in other))
    if key not in recount:
        raise Refused(f"REPRODUCTION FAILED, nothing written: the recount holds no {key!r} (written by S480 before "
                      f"D188?); run scripts/S480_fig4_recount.py first")
    mine, theirs, probs = my_counts(st, fn, groups), recount.get(key) or {}, []
    for c, v in stress_counts(fn, groups).items():
        if (recount.get("stress_records") or {}).get(c) != v:
            probs.append(f"{LABEL[c]}: {v} here, the recount {(recount.get('stress_records') or {}).get(c)}")
    for c in mine:
        if c not in theirs:
            probs.append(f"{LABEL[c]}: not in the recount")
            continue
        for k, v in mine[c].items():
            if theirs[c].get(k, "absent") != v:
                probs.append(f"{LABEL[c]} {k}: {v} here, the recount {theirs[c].get(k, 'absent')} ({key})")
    if probs:
        raise Refused("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs))
    return {c: mine[c] for c in mine}


# ---------------------------------------------------------------------------------------------------------------
# the panels' rows (Source Data, one sheet per panel)
# ---------------------------------------------------------------------------------------------------------------
LEVELS = [("4 or 5", 1.0), ("3", 0.5), ("2 or less, or no answer", 0.0)]   # a's tile levels, cividis positions (D171 (1))
YES_POS, NO_POS = 1.0, 0.0                                                   # c: refused light, not refused dark
NO_SCORE = "#D9D9D9"                                                         # S463's tile for a judge with no score
FP_PASS = hs.OKABE["vermillion"]                                             # b: a false-premise pass, its tile's outline (D250)
# a, c and e print these only on a plate built from a collect with no G9 rows or with no G9 retrievals given; the
# frozen inputs hold both (findings/recompute/fig4_g9_inputs, copied 3 November), so the committed plate prints neither
NOT_JUDGED = "judge rows not copied"                                         # a, c: a set-up with no judge rows
NO_SEARCH = "search time not copied"                                         # d: a stress set-up with no retrievals
NO_TIME = "no search time recorded"                                          # d: RLM-10 (sheet note)
NO_TIME_PLATE = "no search time"                                             # d: RLM-10's time row, as printed
D_MEASURES = (("model_calls", "model calls"), ("own_time_s", "own time (s)"))   # d's two columns, left to right


def p_level(cell) -> int | None:
    """a's tile level of a cell: 0 for score 4 or 5, 1 for 3, 2 for 2 or less or a failed answer; None unscored."""
    if cell["kind"] == "unscored":
        return None
    s = cell["score"] if cell["kind"] == "scored" else 0
    return 0 if s >= 4 else 1 if s >= 3 else 2


def role(c):
    return ("baseline (descriptive, Rule 12)" if c in BASELINES else "reference" if c == FULL else
            "RLM-10 (claim P1, on its own)" if c == RLM else
            "stress set-up (G9; descriptive, no test)" if c in STRESS else
            "orchestrator set-up (Holm family of five)")


def draw_rows(cells_d: dict, groups: dict, subset: list) -> list:
    """Sheet Fig. 4a's 'draw' rows (FF30): per set-up, draw 1 to 3 and threshold (4, 3), on the answerable questions of
    D98's subset, the questions passed and the questions with a row (a failed answer counts, an unscored row or an
    answer with no row does not). cells_d: {(config, question, draw): cell}."""
    aq = [q for q in subset if groups[q] == "answerable"]
    out = []
    for c in ALL:
        for d in (1, 2, 3):
            for t in (PASS_T, PASS_RELAXED):
                n = k = 0
                for q in aq:
                    cell = cells_d.get((c, q, d))
                    if cell is None or cell["kind"] == "unscored":
                        continue
                    n += 1
                    k += cell["kind"] == "scored" and cell["score"] >= t
                out.append({"row": "draw", "setup": LABEL[c], "config": c, "role": role(c), "draw": d, "threshold": t,
                            "passed": k, "questions": n})
    return out


def draw_rows_keep(d: dict, subset, g7) -> bool:
    """read_draw_rows' read_only rule for judge_rows_v25.choose, on an answer or a source row: a G3 or G9 set-up on a
    question of D98's subset; of a source row at draw 2 or 3 of a G7 set-up, only a row of S6G7G3 (questions "all"), so
    no v2.4 or changed-mode row of orch_no_supervisor's 34 draw-2 answers is read (N19; judge_rows_v25.py:36-40)."""
    if d.get("config") not in G3_ALL or d.get("question_id") not in subset:
        return False
    return not ("a" in d and d.get("config") in g7 and d.get("draw") in (2, 3) and d.get("questions") != "all")


def read_draw_rows(g3_collect: Path, rlm_collect: Path, groups: dict, g3_root: Path, s6_g1: Path) -> dict | None:
    """R4, the 'draw' rows' cells, or None while out_s6_g7_g3 is not under g3_root (S6G7G3 not copied). g3_collect and
    rlm_collect are the views collect_view returned (a frozen collect's sidecar names a folder that no longer exists),
    g3_root the folder holding out_g3, out_s6_g3 and out_s6_g7_g3, s6_g1 RLM-10's frozen set. On the questions of D98's
    subset. The eight orchestrator and G9 set-ups: draw 1 by judge_rows_v25's rule, draws 2 and 3 from S6G7G3's rows
    only (draw_rows_keep). The two baselines: out_g3 with out_s6_g3, at every draw. RLM-10: G1 through S463.judge_rows at
    draws 1, 2 and 3. out_s6_g3's and out_s6_g7_g3's judging units pass S463.check_units for the draws they give. Every
    set-up must have its draw-1 rows, else refused. Not run on real rows when written (2 November): S6G7G3 is on the
    Studio."""
    srcs = JR.sources(g3_root, "G3")
    if not srcs[2]["present"]:
        return None
    sub = json.loads(D98_SUBSET.read_text())["ids"]
    g7 = set(JR.g7_configs("G3"))
    if g7 != set(ORCH + STRESS):
        raise Refused(f"judge_rows_v25: G3's G7 set-ups are {sorted(g7)}, not this plate's {sorted(ORCH + STRESS)}")
    m = s463()
    ans = [{"run_id": run_of(c), "config": c, "question_id": q, "draw": d, "answer_key": f"{INDEX}|{c}|{q}|d{d}"}
           for c in G3_ALL for q in sub for d in (1, 2, 3)]
    units = {}
    try:
        loaded = [JR.read_source(srcs[0], g3_collect)]
        with tempfile.TemporaryDirectory(prefix="S472_draws_") as t:
            for s_, draws in ((srcs[1], [1, 2, 3]), (srcs[2], [2, 3])):
                if not s_["present"]:
                    raise Refused(f"judge_rows_v25 (G3): {s_['name']} is not under {g3_root}")
                dest = Path(t) / f"{s_['name']}.jsonl"
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    rc = JR.guard().collect(s_["outs"], None, dest, s_["set"])
                if rc:
                    raise Refused(f"judge_rows_v25 (G3): s3_guard collect refused {s_['name']}: "
                                  f"{buf.getvalue().strip()[-300:]}")
                L = JR.read_source(s_, dest)
                units[s_["name"]] = rel_units(s463_call(m.check_units, list(s_["outs"]), L.run_sha256, draws))
                loaded.append(L)
        choice = JR.choose(ans, loaded, g7_configs=g7, read_only=lambda d: draw_rows_keep(d, sub, g7))
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25 (G3): {e}") from None
    cells = {}
    for a in ans:
        ch = choice[(a["run_id"], a["config"], a["question_id"], a["draw"])]
        if ch["row"] is not None:
            cells[(a["config"], a["question_id"], a["draw"])] = judge_cell(ch["row"], groups[a["question_id"]])
    short = [c for c in G3_ALL for q in sub if (c, q, 1) not in cells]
    if short:
        raise Refused(f"'draw' rows: {len(short)} draw-1 answers have no judge row, first of {short[0]}")
    reruns = s463_call(m.rerun_keys)
    got = s463_call(m.read_collect, rlm_collect, [1, 2, 3], groups, reruns)
    s463_call(m.judge_rows, got, rlm_collect, groups, reruns, [1, 2, 3], s6_root=s6_g1)
    cells.update({k: v for k, v in got["cells"].items() if k[0] == RLM and k[1] in sub})
    return {"cells": cells, "subset": sub, "units": units,
            "sources": {k: {x: y for x, y in v.items() if x != "rows"} for k, v in choice["_sources"].items()}}


def panel_rows(fn, q82, st, cells, rlm, groups, order, thr, draws=None, g17=None) -> dict:
    """Every panel's rows, in plate order: a pass (P-1), b distiller (F-2), c refusal (R-1), d cost (model calls and own
    time per answer, one panel since 4 November), e G17 (read_g17; empty when g17 is None, as in the selftest). Each
    sheet holds its 'setup' (or 'pooled', or 'difference') rows first, the rows the printed numbers point at, then its
    tile, step, answer or question rows; d holds one 'total' row per measure after that measure's 'setup' rows, the
    line printed above its column. A set-up with no judge rows keeps every row of a and c, its judge values blank.
    draws: the 'draw' rows of sheet a, none until S6G7G3 is copied."""
    S = {L: [] for L in "abcdef"}
    by = {g: [q for q in order if groups[q] == g] for g, _ in GROUPS}
    ans = fn["answers"] + [rlm["rows"][q] for q in order]
    judged = list(st["pass"][PASS_T])
    # a: pass
    z = lambda x: x + 0.0                       # S463.pair negates a stored pair: -0.0 is written as 0.0
    for t in (PASS_T, PASS_RELAXED):
        for c in ALL:
            if c not in judged:
                S["a"].append({"row": "setup", "setup": LABEL[c], "config": c, "role": role(c), "threshold": t})
                continue
            s, v = st["pass"][t][c], st["vs_full"][t].get(c)
            desc = c in BASELINES
            S["a"].append({"row": "setup", "setup": LABEL[c], "config": c, "role": role(c), "threshold": t,
                           "passed": s["passed"], "questions": s["questions_with_share"], "pass_rate": s["rate"],
                           "interval_low": s["lo"], "interval_high": s["hi"],
                           "minus_full": None if v is None or desc else z(v["d"]),
                           "minus_full_low": None if v is None or desc else z(v["lo"]),
                           "minus_full_high": None if v is None or desc else z(v["hi"]),
                           "gained": None if v is None else v["a_higher"], "lost": None if v is None else v["b_higher"],
                           "same": None if v is None else v["questions"] - v["a_higher"] - v["b_higher"],
                           "p_sign_flip": None if v is None or desc or c in STRESS else v["p"],
                           "p_holm": v["p_holm"] if c in FAMILY else None,
                           "p_drawn": v["p_holm"] if c in FAMILY else v["p"] if c == RLM else None,
                           "p_drawn_is": ("Holm-adjusted over the five orchestrator set-ups" if c in FAMILY else
                                          "unadjusted (claim P1, on its own)" if c == RLM else "")})
    pass_of = lambda c, q, t: st["pass_shares"][t][c][q][0] == 1
    a_order = sorted(by["answerable"], key=lambda q: (-sum(pass_of(c, q, PASS_T) for c in judged),
                                                      -sum(pass_of(c, q, PASS_RELAXED) for c in judged), q))
    for c in ALL:
        for j, q in enumerate(a_order):
            cell = cells.get((c, q, 1))
            row = {"row": "tile", "setup": LABEL[c], "config": c, "question_id": q, "column": j + 1}
            if cell is not None:
                lv = p_level(cell)
                row.update(judge_kind=cell["kind"], correctness=cell.get("score"),
                           level=LEVELS[lv][0] if lv is not None else "no score")
            S["a"].append(row)
    S["a"].extend(draws or [])
    # b: distiller
    steps = sorted((x for x in fn["f"] if x["row"] == "step" and x["config"] in ORCH),
                   key=lambda x: (x["value"], x["config"], x["answer_key"], str(x["step_id"]), str(x["attempt_no"])))
    for c in ORCH:
        q = q82[c]
        S["b"].append({"row": "setup", "setup": LABEL[c], "config": c, "attempts": q["step_attempts"],
                       "over_threshold": q["over_threshold"], "longest_chars": q["largest_chars"],
                       "threshold_chars": thr})
    longest = steps[-1]
    S["b"].append({"row": "pooled", "setup": "the six orchestrator set-ups", "config": "pooled",
                   "attempts": len(steps), "over_threshold": sum(x["over_threshold"] for x in steps),
                   "longest_chars": longest["value"], "longest_setup": longest["setup"],
                   "threshold_chars": thr, "longest_pct_of_threshold": 100.0 * longest["value"] / thr})
    for i, x in enumerate(steps, 1):
        S["b"].append({"row": "step", "setup": x["setup"], "config": x["config"], "answer_key": x["answer_key"],
                       "step_id": x["step_id"], "attempt_no": x["attempt_no"], "tool_name": x["tool_name"],
                       "value": x["value"], "rank": i, "cumulative_pct": 100.0 * i / len(steps),
                       "over_threshold": x["over_threshold"], "distill_status": x["distill_status"]})
    # c: refusal
    dec = {(x["config"], x["question_id"]): x.get("analyser_decision") for x in ans}
    ref_of = lambda c, q: st["refusal_shares"][c][q][0] == 1
    for c in ALL:
        row = {"row": "setup", "setup": LABEL[c], "config": c}
        if c in judged:
            r = st["refusal"][c]
            row.update(questions=r["questions_with_share"], refused=r["refused"], refusal_rate=r["rate"],
                       interval_low=r["lo"], interval_high=r["hi"], zero_bound_one_sided=r["zero_bound"],
                       full_bound_one_sided=r["full_bound"])
        row["analyser"] = "yes" if fn["analyser"].get(c) else "switched off" if c in ORCH else "no analyser"
        if c in judged:
            row.update(fp_threshold=FP_T, fp_passed=st["false_premise"][c]["passed"], fp_n=st["false_premise"][c]["n"],
                       fp_relaxed_threshold=FP_RELAXED, fp_passed_relaxed=st["false_premise_relaxed"][c]["passed"],
                       fp_n_relaxed=st["false_premise_relaxed"][c]["n"])
        if fn["analyser"].get(c):
            for g, _ in GROUPS:
                row[f"direct_{g}_n"] = sum(1 for q in by[g] if dec[(c, q)] == "direct_answer")
            sent = [q for q in by["not_answerable"] if dec[(c, q)] == "direct_answer"]
            planned_ = [q for q in by["not_answerable"] if dec[(c, q)] != "direct_answer"]
            row["direct_answer_n"] = len(sent)
            if c in judged:
                row["refused_of_direct"] = sum(ref_of(c, q) for q in sent)
            row["not_direct_n"] = len(planned_)
            if c in judged:
                row["refused_of_not_direct"] = sum(ref_of(c, q) for q in planned_)
        S["c"].append(row)
    c_order = sorted(by["not_answerable"], key=lambda q: (-sum(ref_of(c, q) for c in judged), q))
    for c in ALL:
        for j, q in enumerate(c_order):
            cell = cells.get((c, q, 1))
            row = {"row": "tile", "setup": LABEL[c], "config": c, "question_id": q, "column": j + 1}
            if cell is not None:
                row.update(judge_kind=cell["kind"], refusal_accuracy=cell.get("score"),
                           refused=None if cell["kind"] == "unscored" else int(ref_of(c, q)))
            row["analyser_decision"] = dec[(c, q)]
            S["c"].append(row)
    for c in ALL:                                # FF: the per-question false-premise rows the plan promises
        for j, q in enumerate(by["false_premise"]):
            cell = cells.get((c, q, 1))
            row = {"row": "fp_tile", "setup": LABEL[c], "config": c, "question_id": q, "column": j + 1}
            if cell is not None:
                row.update(judge_kind=cell["kind"], correctness=cell.get("score"))
                if cell["kind"] != "unscored":
                    hit = lambda t: int(cell["kind"] == "scored" and cell["score"] >= t)   # noqa: E731
                    row.update(fp_pass=hit(FP_T), fp_pass_relaxed=hit(FP_RELAXED))
            S["c"].append(row)
    # d: cost, model calls and own time per answer in one panel (first author, 4 November: the two panels of D219
    # merged, so e can hold G17). One 'setup' and one 'total' row per measure; one 'answer' row holds both measures.
    for field, meas in D_MEASURES:
        n0 = len(S["d"])
        for c in ALL:
            rows_c = [x for x in ans if x["config"] == c]
            vals = [x[field] for x in rows_c if x[field] is not None]
            row = {"row": "setup", "measure": meas, "setup": LABEL[c], "config": c, "answers": len(rows_c),
                   "n": len(vals)}
            if vals:
                q = quartiles(vals)
                row.update({k: q[k] for k in ("minimum", "q1", "median", "q3", "maximum")})
            else:
                row.update(minimum=None, q1=None, median=None, q3=None, maximum=None,
                           note=("no value" if field != "own_time_s" else NO_SEARCH if c in STRESS else NO_TIME))
            if field == "model_calls":
                row.update(calls_total=sum(x["model_calls"] for x in rows_c),
                           failed_calls=sum(x["failed_calls"] for x in rows_c),
                           cut_calls=sum(x["cut_calls"] for x in rows_c),
                           stopped_by_google_calls=sum(x["google_calls"] for x in rows_c),
                           other_returned_calls=sum(x["other_returned_calls"] for x in rows_c),
                           call_error_calls=sum(x["call_error_calls"] for x in rows_c),
                           answers_with_failed_call=sum(1 for x in rows_c if x["failed_calls"]),
                           answers_with_cut_call=sum(1 for x in rows_c if x["cut_calls"]),
                           answers_no_text=sum(x["no_text"] for x in rows_c))
            S["d"].append(row)
        mine = S["d"][n0:]
        S["d"].append({"row": "total", "measure": meas, "setup": "all set-ups drawn", "config": "all",
                       "answers": sum(r["answers"] for r in mine), "n": sum(r["n"] for r in mine),
                       "set_ups": sum(1 for r in mine if r["n"])})
    for x in ans:
        S["d"].append({"row": "answer", "setup": x["setup"], "config": x["config"], "question_id": x["question_id"],
                       "answer_key": x["answer_key"], "model_calls": x["model_calls"],
                       "failed_calls": x["failed_calls"], "cut_calls": x["cut_calls"],
                       "call_statuses": x["call_statuses"], "no_text": x["no_text"],
                       "analyser_decision": x.get("analyser_decision"), "own_time_s": x["own_time_s"],
                       "calls_wall_s": x.get("calls_wall_s"), "search_s": x.get("search_s")})
    # e, f (plate letters d, e; D250): G17, the Mentori RLM-10 ablation, from S571's d123 reading and S576 only
    S["e"], S["f"] = g17_sheets(g17) if g17 else ([], [])
    return {"sheets": S, "a_order": a_order, "c_order": c_order, "fp_order": by["false_premise"], "judged": judged,
            "stress_steps": fn["stress_steps"]}


def sheets_of(P):
    """Figure 4's Source Data sheets in plate order, each named by its plate letter (PLATE_LETTER). Sheet b, the plan
    step attempts, left Figure 4 for Supplementary Figure 10a (D250): its rows go to STEPS_OUT (steps_file)."""
    out = []
    for L, rows in sorted(((L, r) for L, r in P["sheets"].items() if L in PLATE_LETTER),
                          key=lambda x: PLATE_LETTER[x[0]]):
        cols = []
        for r in rows:
            for c in r:
                if c not in cols:
                    cols.append(c)
        out.append((sheet_name(L), cols, [[r.get(c) for c in cols] for r in rows]))
    return out


def steps_file(P) -> dict:
    """Old panel 4b's rows (D250: Supplementary Figure 10a): sheet b's 'setup', 'pooled' and 'step' rows, as columns
    and rows, the form S524 reads."""
    rows = P["sheets"]["b"]
    cols = []
    for r in rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    return {"what": "the plan step attempts of the six orchestrator set-ups of Figure 4 (G3, draw 1) at or under each "
                    "raw output length, with the distiller threshold: Figure 4b until D250 (Valerio, 4 November), "
                    "now Supplementary Figure 10a, drawn by scripts/S524_t3_s12_s13.py",
            "columns": cols, "rows": [[r.get(c) for c in cols] for r in rows]}


# ---------------------------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------------------------
CALL_TICKS = [2 ** k for k in range(0, 8)]       # d: 1 to 128 by doubling (D129's form, as C-2)
P_GAP = 0.45                                     # a: rows of space between baselines, pipeline, stress, RLM-10
R_GAP_MM = 1.2                                   # c: the same gaps in mm (R-1)
GAP_BEFORE = (FULL, STRESS[0], RLM)              # the row each of the three gaps sits above (fig4.md, Rows)


def p_ypos(c):
    i = ALL.index(c)
    return i + 0.5 + P_GAP * sum(i >= ALL.index(g) for g in GAP_BEFORE)


def draw(P, paths):
    """The plate in the house style (fig4.md section 3), in D250's layout (Valerio, 4 November): a full width; b, the
    refusal tiles with the false-premise questions as tiles of their own (a pass outlined in vermillion; no refusal
    rate margin and no false-premise column), and c, the cost (two box columns, model calls and own time per answer,
    on b's set-up rows), side by side; d and e, G17 (option 2b), at the bottom. a's and b's keys centred above their
    panels, no key on c (D147: the legend defines the box), the arms' key above d and e. House boxes on a log axis are
    drawn as log10 on a linear one (so hs.swarm places the dots apart in millimetres). Old 4b, the plan step attempts,
    is Supplementary Figure 10a (S524), from steps_file()."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import colormaps
    from matplotlib.colors import to_hex
    from matplotlib.font_manager import FontProperties
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.textpath import TextToPath
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

    plt.rcParams.update(hs.rc("S472"))
    PT, MMP = hs.PT, hs.MM_PT
    t2p = TextToPath()

    def tw(s_):
        fp = FontProperties(family=hs.FONT, size=PT)
        return max(t2p.get_text_width_height_descent(x, fp, ismath=False)[0] for x in str(s_).split("\n")) * MMP

    S = P["sheets"]
    judged = P["judged"]
    CIV = colormaps[S457.FLOCK["colour"]["continuous"]]
    LEVEL_COL = [to_hex(CIV(v)).upper() for _, v in LEVELS]
    YES, NO = to_hex(CIV(YES_POS)).upper(), to_hex(CIV(NO_POS)).upper()
    W, M = hs.PAGE_W_MM, 1.5
    LINE = PT * MMP * 1.2
    TICK_LAB = 2 * MMP + 3.5 * MMP                    # tick length and matplotlib's tick label pad
    XAX1 = TICK_LAB + LINE + 2 * MMP + LINE           # ticks, one line of tick labels, a one-line axis label
    XAX2 = XAX1 + LINE                                # the same with a two-line axis label
    GAP = 2.4                                         # between the plate's rows
    KEY_BASE = 2.9                                    # from a row's top: the key's (and the letter's) baseline
    PA, PR, PC = 2.8, 2.75, 3.0                       # row pitch of a, c and d, e (mm; d, e 3.0 so e's two-line axis labels fit)
    LAB = max(tw(LABEL[c]) for c in ALL)
    YLAB0 = 2 * MMP + LAB + 0.6                       # row labels as tick labels with no tick (a, c)
    YLAB = TICK_LAB + LAB + 0.6                       # row labels with ticks (d, e)
    n_a, n_c = len(P["a_order"]), len(P["c_order"])

    # ---- the layout in mm, top to bottom (D250): a full width; b (refusal tiles) and c (cost) side by side on the
    # same set-up rows; d and e (G17) at the bottom
    top_a = M
    body_a = top_a + KEY_BASE + 2.4
    ylim_a = len(ALL) + len(GAP_BEFORE) * P_GAP
    HA = ylim_a * PA
    top_c = body_a + HA + XAX2 + GAP
    body_c = top_c + KEY_BASE + 2.4
    ys_c, y = {}, 0.0
    for c in ALL:
        if c in GAP_BEFORE:
            y += R_GAP_MM
        ys_c[c] = y + PR / 2
        y += PR
    HR = y
    top_e = body_c + HR + XAX2 + GAP
    let_e = top_e + KEY_BASE                          # d, e: the letters, and the arms' key on the next line
    key_e = let_e + LINE + 0.4
    body_e = key_e + 3.0
    AX_E = 33.0                                       # d, e: the plot height (option 2b)
    H = body_e + AX_E + 1.0 + 2 * LINE + M            # the question types' two-line labels under the axes
    if H > S457.FIG_H_MAX_MM - 0.5:
        raise SystemExit(f"Figure {FIG_N}: the page would be {H:.1f} mm high, over [page] height_max_mm less 0.5")
    fig = hs.figure(W, H)
    pg = fig.add_axes([0, 0, 1, 1])
    pg.set_axis_off()
    pg.set_xlim(0, W)
    pg.set_ylim(H, 0)
    printed, rb = {}, defaultdict(list)

    def num(artist, entry):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    def fixed(artist, why):
        return num(artist, {"fixed": artist.get_text(), "why": why})

    def sheet_index(L, **kw):
        hits = [i for i, r in enumerate(S[L]) if all(r.get(k) == v for k, v in kw.items())]
        if len(hits) != 1:
            raise SystemExit(f"{L}: {len(hits)} sheet rows match {kw}")
        return hits[0], S[L][hits[0]]

    def axes_mm(x, y_, w, h):
        return fig.add_axes([x / W, 1 - (y_ + h) / H, w / W, h / H])

    def text(x, y_, s_, **kw):
        return pg.text(x, y_, s_, **{"va": "center", "ha": "left", **kw})

    def letter(x, y_, L):
        pg.text(x, y_, S457.LETTER_CASE(PLATE_LETTER[L]), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT,
                va="baseline", ha="left")

    def dot(ax, x, y_, d_mm, col, z=4):
        ax.plot([x], [y_], ls="none", marker="o", ms=d_mm / MMP, mfc=col, mew=0, zorder=z, clip_on=False)

    def key(items, centre_x, y_, title=None):
        """hs.key, centred; every key text holding a digit registered as fixed words (S448 R8)."""
        before = set(map(id, fig.texts))
        out = hs.key(fig, items, centre_x=centre_x, y=y_, title=title)
        for t in fig.texts:
            if id(t) not in before and re.search(r"\d", t.get_text()):
                fixed(t, "a key's words")
        return out

    def strip(ax, keep=("bottom",)):
        for s_ in ("top", "right", "left", "bottom"):
            ax.spines[s_].set_visible(s_ in keep)

    def interval(ax, y_, lo, hi, mid):
        hs.estimate(ax, y_, mid, lo if hi > lo else None, hi if hi > lo else None)

    # ================================================================ a: pass (P-1), the full width (D250)
    xh = M + YLAB0
    WR, GR = 20.0, 5.5                                # the rate column, and a gap clear of the "86" tick label
    rows_a = [r for r in S["a"] if r["row"] == "setup" and r["threshold"] == PASS_T and r["config"] in judged]
    WH = W - M - tw("100") / 2 - 0.3 - WR - GR - xh  # the tiles take what is left; half the last "100" past the axis
    if WH / n_a < 0.5:
        raise SystemExit(f"a: {WH:.1f} mm for {n_a} questions")
    ya_key = top_a + KEY_BASE
    letter(M, ya_key, "a")
    ax = axes_mm(xh, body_a, WH, HA)
    ax.set_xlim(0, n_a)
    ax.set_ylim(ylim_a, 0)
    strip(ax)
    for c in ALL:
        yc = p_ypos(c)
        if c not in judged:
            ax.text(n_a / 2, yc, NOT_JUDGED, ha="center", va="center")
            rb["not_judged"].append(("a", c))
            continue
        for j, q in enumerate(P["a_order"]):
            ri, row = sheet_index("a", row="tile", config=c, question_id=q)
            lv = [k for k, (lab, _) in enumerate(LEVELS) if lab == row["level"]]
            col = LEVEL_COL[lv[0]] if lv else NO_SCORE
            ax.add_patch(Rectangle((j, yc - 0.42), 1, 0.84, fc=col, ec=col, lw=0.35))   # edge: no seam
            rb["a_tile"].append((c, q, col, j + 1, row["column"], row["level"]))
    ax.set_yticks([p_ypos(c) for c in ALL], [LABEL[c] for c in ALL])
    ax.tick_params(axis="y", length=0, pad=2)
    ax.set_xticks([0.5, n_a - 0.5], ["1", str(n_a)])
    ax.set_xlabel("Answerable question,\nsame order in every row", labelpad=1.5)
    lev_items = [("swatch", LEVEL_COL[k], lab) for k, (lab, _) in enumerate(LEVELS)]
    if any(r.get("level") == "no score" for r in S["a"] if r["row"] == "tile"):
        lev_items.append(("swatch", NO_SCORE, "no score"))
    # the pass rate at 4
    xr = xh + WH + GR
    ar = axes_mm(xr, body_a, WR, HA)
    lo_r = min(r["interval_low"] for r in rows_a) * 100
    xr0 = 20 if lo_r >= 20 else 0
    ar.set_xlim(xr0, 100)
    ar.set_ylim(ylim_a, 0)
    strip(ar)
    for r in rows_a:
        interval(ar, p_ypos(r["config"]), 100 * r["interval_low"], 100 * r["interval_high"], 100 * r["pass_rate"])
        rb["a_rate"].append((r["config"], ar.lines[-1].get_xdata()[0], 100 * r["pass_rate"]))
    ar.set_yticks([])
    ar.set_xticks([xr0, (xr0 + 100) // 2, 100])
    fixed(ar.set_xlabel(f"Pass rate {PASS_T}+ (%)", labelpad=1.5), "the axis label (PASS_T)")
    # a's key, centred over a's plotting area (the tiles to the rate column)
    key(lev_items + [("estimate", None, "pass rate, 95% interval")], (xh + xr + WR) / 2, ya_key, title="Judge score:")

    # ================================================================ b (sheet c): refusal tiles (R-1), D250: no
    # refusal rate margin and no false-premise column; the 10 false-premise questions as tiles of their own, right of
    # the 39, a pass at FP_T+ outlined in vermillion (Valerio: "color the single tile of question with red outline")
    yc_key = top_c + KEY_BASE
    letter(M, yc_key, "c")
    gx = M + YLAB0
    WD, GAP_COL, GAP_CD, FP_GAP = 26.0, 4.0, 6.0, 2.0   # c's two columns, the gaps, the space before the false premise
    xd0 = W - M - (2 * WD + GAP_COL)                  # c's first column
    n_fp = len(P["fp_order"])
    tile = (xd0 - GAP_CD - gx - FP_GAP) / (n_c + n_fp)
    ag = axes_mm(gx, body_c, n_c * tile, HR)
    xfp = gx + n_c * tile + FP_GAP
    afp = axes_mm(xfp, body_c, n_fp * tile, HR)
    for ax_, n_ in ((ag, n_c), (afp, n_fp)):
        ax_.set_xlim(0, n_)
        ax_.set_ylim(HR, 0)
        strip(ax_)
    for c in ALL:
        yc = ys_c[c]
        if c not in judged:
            ag.text(n_c / 2, yc, NOT_JUDGED, ha="center", va="center")
            rb["not_judged"].append(("c", c))
            continue
        for j, q in enumerate(P["c_order"]):
            _, row = sheet_index("c", row="tile", config=c, question_id=q)
            col = NO_SCORE if row["refused"] is None else YES if row["refused"] else NO
            ag.add_patch(Rectangle((j, yc - PR * 0.42), 1, PR * 0.84, fc=col, ec=col, lw=0.35))
            has_dot = row["analyser_decision"] == "direct_answer"
            if has_dot:
                dot(ag, j + 0.5, yc, 0.8, hs.ink_on(col))
            rb["c_tile"].append((c, q, col, row["refused"], has_dot, row["analyser_decision"]))
        for j, q in enumerate(P["fp_order"]):
            _, row = sheet_index("c", row="fp_tile", config=c, question_id=q)
            passed = row.get("fp_pass")
            fc = NO_SCORE if passed is None else hs.WHITE
            ins = 0.12                                    # inset, so a pass's outline never touches its neighbour's
            afp.add_patch(Rectangle((j + ins, yc - PR * 0.42 + ins * tile), 1 - 2 * ins, PR * 0.84 - 2 * ins * tile,
                                    fc=fc, ec=FP_PASS if passed else hs.GREY["line"],
                                    lw=hs.LW["median"] if passed else hs.LW["box"], joinstyle="miter"))
            rb["fp_tile"].append((c, q, FP_PASS if passed else None, passed, row["column"], j + 1))
    ag.set_yticks([ys_c[c] for c in ALL], [LABEL[c] for c in ALL])
    ag.tick_params(axis="y", length=0, pad=2)
    ag.set_xticks([0.5, n_c - 0.5], ["1", str(n_c)])
    ag.set_xlabel("Out-of-scope question,\nsame order in every row", labelpad=1.5)
    afp.set_yticks([])
    afp.set_xticks([0.5, n_fp - 0.5], ["1", str(n_fp)])
    afp.set_xlabel("False\npremise", labelpad=1.5)
    # D293: the direct-answer key shows what the plate draws, the dot on the tile it sits on (every direct answer is
    # on a not-refused tile, so a dot in ink_on(NO) on a NO swatch); refused if one ever sits on a YES tile
    da_fills = {c[2] for c in rb["c_tile"] if c[4]}
    if da_fills - {NO}:
        raise SystemExit(f"b: direct-answer dots on fills {sorted(da_fills - {NO})}; the key shows them on {NO} only")
    before_art = set(map(id, fig.artists))
    key([("swatch", YES, "yes"), ("swatch", NO, "no"), ("swatch", NO, "sent to a direct answer"),
         ("outline", FP_PASS, "false premise passed")], gx + n_c * tile / 2, yc_key, title="Refused:")
    sw = [a_ for a_ in fig.artists if id(a_) not in before_art and isinstance(a_, Rectangle)][2]
    (bx0, by0), (bx1, by1) = sw.get_bbox().get_points()
    fig.add_artist(Line2D([(bx0 + bx1) / 2], [(by0 + by1) / 2], transform=fig.transFigure, ls="none", marker="o",
                          ms=0.8 / MMP, mfc=hs.ink_on(NO), mew=0, zorder=5))

    # ================================================================ c (sheet d): cost (C-2, A-3; D219), calls and
    # time in one panel, on b's set-up rows (D250: d moved up beside the tiles; one row per set-up reads across)
    xs_d = [xd0, xd0 + WD + GAP_COL]
    letter(xd0 - 3.0, yc_key, "d")
    n = len(ALL)
    for k, (field, meas) in enumerate(D_MEASURES):
        x0 = xs_d[k]
        ri, tot = sheet_index("d", row="total", measure=meas)
        num(text(x0 + WD / 2, yc_key, f"n = {tot['n']:,} answers", va="baseline", ha="center"),
            {"sheet": sheet_name("d"), "row": ri, "format": "n = {n:,} answers"})
        ax = axes_mm(x0, body_c, WD, HR)
        ax.set_ylim(HR, 0)
        ax.yaxis.set_major_locator(FixedLocator([ys_c[c] for c in ALL]))
        ax.yaxis.set_major_formatter(FixedFormatter([""] * n))
        ax.yaxis.set_minor_locator(NullLocator())
        setup = {r["config"]: r for r in S["d"] if r["row"] == "setup" and r["measure"] == meas}
        drawn = [c for c in ALL if setup[c]["n"]]
        lo = max(min(setup[c]["minimum"] for c in drawn), 0.5)
        hi = max(setup[c]["maximum"] for c in drawn)
        # a log axis drawn as log10 on a linear one, so hs.swarm places the dots apart in millimetres
        if field == "model_calls":
            ticks = [t for t in CALL_TICKS[::2] if t <= hi * 1.3]   # 1, 4, 16, 64: a narrow column
            xl = (math.log10(0.8), math.log10(hi * 1.3))
            labs = [f"{t:g}" for t in ticks]
        else:
            ticks = [10 ** e for e in range(-1, 7) if lo / 1.5 <= 10 ** e <= hi * 1.5]
            xl = (math.log10(lo / 1.5), math.log10(hi * 1.5))
            labs = [fmt_int(t) if t >= 1 else f"{t:g}" for t in ticks]
        ax.set_xlim(*xl)
        ax.xaxis.set_major_locator(FixedLocator([math.log10(t) for t in ticks]))
        ax.xaxis.set_major_formatter(FixedFormatter(labs))
        ax.xaxis.set_minor_locator(NullLocator())
        n_dots = 0
        for c in ALL:
            v = np.array([r[field] for r in S["d"] if r["row"] == "answer" and r["config"] == c
                          and r[field] is not None], float)
            if v.size:
                if (v <= 0).any():
                    raise SystemExit(f"c {meas} {c}: {int((v <= 0).sum())} values at or under 0 on a log axis")
                s = setup[c]
                st = {"q1": math.log10(s["q1"]), "median": math.log10(s["median"]), "q3": math.log10(s["q3"]),
                      "whisker_low": math.log10(s["minimum"]), "whisker_high": math.log10(s["maximum"])}
                art = hs.boxplot(ax, ys_c[c], values=list(np.log10(v)), stats=st, orient="h", slot=PR)
                art["median"].set_gid(f"s472_d_{field}_box_{c}")
                rb["box"].append((meas, c, float(10 ** art["median"].get_xdata()[0]), s["median"]))
                rb["overlap"].append((meas, c, art.get("overlapping", 0)))
                rb["d_n"].append((meas, c, int(len(art["dots"].get_xdata())), setup[c]["n"]))
                n_dots += int(len(art["dots"].get_xdata()))
            else:
                rb["d_n"].append((meas, c, 0, setup[c]["n"]))
                note = NO_TIME_PLATE if setup[c].get("note") == NO_TIME else (setup[c].get("note") or "")
                ax.text(sum(ax.get_xlim()) / 2, ys_c[c], note, ha="center", va="center")
                rb["d_note"].append((meas, c, note))
        rb["total"].append((meas, n_dots, tot["n"], len(drawn), tot["set_ups"]))
        ax.set_xlabel(D_XLABEL[field], labelpad=2)

    # ================================================================ d, e (sheets e, f): G17 (D250, option 2b)
    # One house box per arm (colour and shape as the key) and question type, one-paper on the left of each panel,
    # many-paper on the right: median line, box Q1 to Q3, whiskers to the range, every value a dot under the lines in
    # the arm's colour and shape (hs.boxplot, swarm, no jitter); no mean and no interval. d: each question's concept
    # recall, mean of draws 1 to 3. e: each draw-1 answer's sub-calls that returned paper text and distinct papers read,
    # on an axis linear to 2 and logarithmic above (drawn in its own units, so the swarm's mm spacing holds).
    tf, inv = g17_tf()
    XE, WE, XF_L, XF, WF_ = 14.0, 60.0, 80.0, (93.0, 142.0), 38.0   # option 2b's block, mm from the left
    letter(M, let_e, "e")
    letter(XF_L, let_e, "f")
    key([("mark", (G17_COL[a], G17_MK[a]), lab) for a, lab in G17_ARMS], (XE + XF[1] + WF_) / 2, key_e)

    def g17_positions(gap=0.8):
        pos, centres, x = {}, [], 0.0
        for g, _ in G17_GROUPS:
            xs = []
            for a, _ in G17_ARMS:
                pos[(g, a)] = x
                xs.append(x)
                x += 1.0
            centres.append(sum(xs) / len(xs))
            x += gap
        return pos, centres, x - gap - 1.0

    def g17_panel(L, ax, get_rows, key_kw, t=lambda v: v, tinv=lambda v: v):
        pos, centres, last = g17_positions()
        ax.set_xlim(-0.6, last + 0.6)
        ax.set_xticks([])
        for (g, glab), cx in zip(G17_GROUPS, centres):
            for a, _ in G17_ARMS:
                vals = get_rows(a, g)
                ri, b = sheet_index(L, row="box", arm_key=a, group_key=g, **key_kw)
                st_t = {"q1": t(b["q1"]), "median": t(b["median"]), "q3": t(b["q3"]),
                        "whisker_low": t(b["minimum"]), "whisker_high": t(b["maximum"])}
                art = hs.boxplot(ax, pos[(g, a)], [t(v) for v in vals], stats=st_t, orient="v", slot=1.0,
                                 dot_colour=G17_COL[a], dot_marker=G17_MK[a])
                rb["g17_box"].append((L, key_kw.get("measure_key", "cr"), a, g, tinv(art["median"].get_ydata()[0]),
                                      b["median"], len(art["dots"].get_ydata()), b["n"], art["drawn"]["collapsed"],
                                      b["flat"] == "yes"))
                rb["overlap"].append((f"{PLATE_LETTER[L]} {key_kw.get('measure_key', 'cr')} {g}", a,
                                      art.get("overlapping", 0)))
            ri, b0 = sheet_index(L, row="box", arm_key=G17_ARMS[0][0], group_key=g, **key_kw)
            num(ax.text(cx, -0.03, f"{glab}\nn = {b0['n']}", transform=ax.get_xaxis_transform(), ha="center",
                        va="top", multialignment="center"),
                {"sheet": sheet_name(L), "row": ri, "format": "{question_type}\nn = {n}"})

    ae = axes_mm(XE, body_e, WE, AX_E)
    ae.set_ylim(-3, 103)
    ae.set_yticks([0, 25, 50, 75, 100])
    ae.set_ylabel("Concept recall (%)")
    g17_panel("e", ae, lambda a, g: [r["concept_recall_mean"] for r in S["e"] if r["row"] == "question"
                                     and r["arm_key"] == a and r["group_key"] == g], {})
    for i, (f, flab) in enumerate(G17_F):
        ax = axes_mm(XF[i], body_e, WF_, AX_E)
        ax.set_ylim(tf(-0.3), tf(G17_F_TOP))
        g17_panel("f", ax, lambda a, g, f=f: [float(r[f]) for r in S["f"] if r["row"] == "answer"
                                              and r["arm_key"] == a and r["group_key"] == g],
                  {"measure_key": f}, tf, inv)
        top = max(r["maximum"] for r in S["f"] if r["row"] == "box" and r["measure_key"] == f)
        if top > G17_F_TOP:
            raise SystemExit(f"e {f}: a value of {top} is over the axis top {G17_F_TOP}")
        ax.yaxis.set_major_locator(FixedLocator([tf(t) for t in G17_F_TICKS]))
        ax.yaxis.set_major_formatter(FixedFormatter([str(t) for t in G17_F_TICKS]))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_ylabel(flab)

    bad_col = hs.check_figure_colours(fig)
    if bad_col:
        raise SystemExit(f"Figure {FIG_N}: colours outside the house palette {bad_col}")
    S457.finish_plate(fig, W, H, paths, title=f"Figure {FIG_N}")
    return W, H, printed, rb


def check_drawn(rb, P):
    """Every drawn mark read back from its artist (or the value it was drawn from) against the Source Data rows
    (internal sheet keys; plate letters in PLATE_LETTER): a's tiles (colour of the sheet's level, column order) and
    its rate dots; b's tiles (sheet c: colour of refused or not, a dot exactly where the analyser sent the question to
    a direct answer) and its false-premise tiles (outlined exactly where the sheet's fp_pass is 1, in sheet order);
    c's medians, dot counts, printed totals and the note of a set-up with no value (sheet d); d's and e's box medians
    (read back through e's axis transform), flat boxes and dot counts against sheets e and f, every box drawn once;
    and a set-up with no judge rows printing NOT_JUDGED in a and b, and no other."""
    from matplotlib import colormaps
    from matplotlib.colors import to_hex
    CIV = colormaps[S457.FLOCK["colour"]["continuous"]]
    lev_col = {lab: to_hex(CIV(v)).upper() for lab, v in LEVELS}
    lev_col["no score"] = NO_SCORE
    yes, no = to_hex(CIV(YES_POS)).upper(), to_hex(CIV(NO_POS)).upper()
    bad, n = [], 0
    for c, q, col_drawn, col_col, col_sheet, level in rb["a_tile"]:
        n += 1
        if col_drawn != lev_col[level] or col_col != col_sheet:
            bad.append(f"a tile {c} {q}: {col_drawn} at column {col_col}, sheet {level} at {col_sheet}")
    for c, got, want in rb["a_rate"]:
        n += 1
        if abs(got - want) > 1e-9:
            bad.append(f"a_rate {c}: drawn {got}, Source Data {want}")
    if "judged" in P:
        n += 1
        want_nj = {(L, c) for L in "ac" for c in ALL if c not in P["judged"]}
        if set(rb.get("not_judged", [])) != want_nj:
            bad.append(f"'{NOT_JUDGED}' printed on {sorted(rb.get('not_judged', []))}, the sheet says {sorted(want_nj)}")
    for c, q, col, refused, has_dot, decision in rb["c_tile"]:
        n += 1
        want = NO_SCORE if refused is None else yes if refused else no
        if col != want or has_dot != (decision == "direct_answer"):
            bad.append(f"b tile {c} {q}: {col} dot {has_dot}, sheet refused {refused} decision {decision}")
    fp = {(r["config"], r["question_id"]): r for r in P["sheets"]["c"] if r["row"] == "fp_tile"}
    for c, q, edge, passed, col_sheet, col_drawn in rb.get("fp_tile", []):
        n += 1
        r = fp[(c, q)]
        if (edge == FP_PASS) != (r.get("fp_pass") == 1) or passed != r.get("fp_pass") or col_sheet != col_drawn:
            bad.append(f"b false-premise tile {c} {q}: outline {edge}, sheet fp_pass {r.get('fp_pass')}")
    if "judged" in P and len(rb.get("fp_tile", [])) != sum(1 for (c, _) in fp if c in P["judged"]):
        bad.append(f"b: {len(rb.get('fp_tile', []))} false-premise tiles drawn, the sheet holds "
                   f"{sum(1 for (c, _) in fp if c in P['judged'])} of judged set-ups")
    for L, c, got, want in rb["box"]:
        n += 1
        if abs(got - want) > 1e-9 * max(1.0, abs(want)):
            bad.append(f"c {L} {c}: median drawn {got}, Source Data {want}")
    for L, c, drawn, want in rb.get("d_n", []):
        n += 1
        if drawn != want:
            bad.append(f"c {L} {c}: {drawn} dots, Source Data n {want}")
    rows_d = {(r["measure"], r["config"]): r for r in P["sheets"].get("d", []) if r["row"] == "setup"}
    for L, c, note in rb.get("d_note", []):             # a set-up with no value prints its sheet note
        n += 1
        want = NO_TIME_PLATE if rows_d[(L, c)].get("note") == NO_TIME else rows_d[(L, c)].get("note")
        if rows_d[(L, c)]["n"] or note != want:
            bad.append(f"c {L} {c}: printed {note!r}, the sheet's n {rows_d[(L, c)]['n']}, note {want!r}")
    for L, dots, n_tot, setups, setups_tot in rb.get("total", []):
        n += 1
        if (dots, setups) != (n_tot, setups_tot):
            bad.append(f"c {L} total: {dots} dots in {setups} set-ups, the sheet {n_tot} in {setups_tot}")
    # d, e (G17): each box's median as drawn against its 'box' row, its dots against the row's n, a flat box drawn as
    # its median line exactly where the sheet says flat; every box row drawn once
    seen = []
    for L, mkey, a, g, med_drawn, med_sheet, dots, n_sheet, collapsed, flat in rb.get("g17_box", []):
        n += 1
        seen.append((L, mkey, a, g))
        if abs(med_drawn - med_sheet) > 1e-6 * max(1.0, abs(med_sheet)) or dots != n_sheet or collapsed != flat:
            bad.append(f"{PLATE_LETTER[L]} {mkey} {a} {g}: median drawn {med_drawn}, sheet {med_sheet}; {dots} dots, "
                       f"n {n_sheet}; flat drawn {collapsed}, sheet {flat}")
    want_boxes = sorted([("e", "cr", r["arm_key"], r["group_key"]) for r in P["sheets"].get("e", []) if r["row"] == "box"]
                        + [("f", r["measure_key"], r["arm_key"], r["group_key"]) for r in P["sheets"].get("f", [])
                           if r["row"] == "box"])
    if sorted(seen) != want_boxes:
        bad.append(f"d, e: {len(seen)} boxes drawn, the sheets hold {len(want_boxes)} (or not each once)")
    return bad, n


# ---------------------------------------------------------------------------------------------------------------
# legend, caption, claims
# ---------------------------------------------------------------------------------------------------------------
def pct1(x):
    return S457.half_up(100 * x, 1)


def vs_full_text(S: dict) -> str:
    """The legend's sentence on the set-ups against the full pipeline, computed from sheet a's rows at PASS_T (each row
    with a P: the five orchestrator set-ups and RLM-10). It names the test, n, sidedness, alpha and the adjustment
    (FIGURE_LOCK [statistics] test_reporting) and states no outcome: a legend describes what is drawn, not the results
    (FIGURE_LOCK [legend] depicts_not_results; Valerio, 7 November, S3). Each difference, interval and exact P is in
    the sheet's minus_full, p_sign_flip, p_holm and p_drawn."""
    rows = [r for r in S["a"] if r["row"] == "setup" and r["threshold"] == PASS_T and r.get("p_drawn") is not None]
    ns = {r["questions"] for r in rows}
    if len(ns) != 1:
        raise Refused(f"sheet a: the set-ups with a P have {sorted(ns)} questions: reword the legend's n; nothing written")
    five = {5: "five"}.get(len(FAMILY), len(FAMILY))
    # 8 Nov legend trim (Valerio: "too long"): the five set-ups' names are panel a's row labels
    return (f"Each set-up minus the full pipeline: two-sided exact sign-flip test, alpha {ALPHA}, n = {ns.pop()} "
            f"questions, Holm-adjusted over {five} pipeline set-ups, unadjusted for RLM-10, others untested; "
            f"results in Source Data.")


def stress_text(S: dict) -> str:
    """The legend's clause on G9's two rows (D163: descriptive, no test): each pass rate at PASS_T with its Rule 2
    interval, as panel a's margin draws them, from sheet a's rows; empty while the rows are not judged."""
    a = {r["config"]: r for r in S["a"] if r["row"] == "setup" and r["threshold"] == PASS_T}
    if any(a.get(c, {}).get("pass_rate") is None for c in STRESS):
        return ""
    return ": " + ", ".join(f"{LABEL[c]} {pct1(a[c]['pass_rate'])}% ({pct1(a[c]['interval_low'])} to "
                            f"{pct1(a[c]['interval_high'])})" for c in STRESS)


def legend_and_caption(P, st, n, N, plan, stamp, extra, command=None):
    # the legend's one threshold sentence covers panel a's pass rate (PASS_T) and panel c's false-premise passes (FP_T)
    if (FP_T, FP_RELAXED) != (PASS_T, PASS_RELAXED):
        raise Refused(f"the legend names one pass threshold for panels a and c, but PASS_T {PASS_T}/{PASS_RELAXED} "
                      f"and FP_T {FP_T}/{FP_RELAXED} differ: reword it before writing; nothing written")
    A, B, C, D, E = (f"**{S457.LETTER_CASE(PLATE_LETTER[x])}**" for x in "acdef")
    S = P["sheets"]
    calls = {r["config"]: r for r in S["d"] if r["row"] == "setup" and r["measure"] == D_MEASURES[0][1]}
    parts = "; ".join(f"{k} {fmt_int(v)}" for k, v in plan["parts"].items())
    def stored_none(c):
        k = calls[c]["answers_no_text"]
        return f"stored no text for {k} answer{'s' if k > 1 else ''}"
    unscored = sum(st["unscored"].values())
    failed_txt = ", ".join(f"{LABEL[c]} {k}" for c, k in st["failed"].items() if k) or "none"
    stress_open = [c for c in STRESS if c not in P["judged"]]
    own = {r["config"]: r for r in S["d"] if r["row"] == "setup" and r["measure"] == D_MEASURES[1][1]}
    no_time = [c for c in STRESS if not own[c]["n"]]
    # d's notes, one per set-up (4 November review F5): a set-up with no search time and answers with no text says both
    # the plate prints "no search time" on such a row, so the legend names only answers with no text (6 Nov trim)
    d_notes = [f"{LABEL[c]} {stored_none(c)}" for c in ALL if calls[c]["answers_no_text"]]
    g17 = extra["g17"]
    ng = {g: sum(1 for r in S["e"] if r["row"] == "question" and r["arm_key"] == G17_CTRL and r["group_key"] == g)
          for g, _ in G17_GROUPS}
    pts1 = lambda x: hs.fmt_num(100 * x, 1)                                              # noqa: E731
    paired = []
    for a, pid in G17_LEGEND_PARTS:
        p_ = g17["parts"][pid]
        if (p_["a"], p_["b"], p_["group"], p_["metric"], p_["kind"]) != (a, G17_CTRL, "all", "cr", "diff"):
            raise Refused(f"S576's part {pid} is not {a} minus the control on concept recall, all questions")
        paired.append(f"{G17_ARM_LABEL[a]} {pts1(p_['diff'])} ({pts1(p_['ci95'][0])} to {pts1(p_['ci95'][1])})")
    head = [
        f"# Figure {FIG_N}, title and legend (draft)", "",
        # audit 27 Oct F5 (fig4_6): the command that made the plate, as the provenance records it (command_of)
        f"Written by `{command or f'uv run --frozen python {SCRIPT} figure'}` from the plotted numbers. "
        f"Data stamp: {stamp}.", "",
        f"**Records.** G3's sinks on the Studio (~/{G3_CLONE}, clone at {extra['clone_head'][:7]}), copied by "
        f"`{SCRIPT} pull` through stdin scripts on {extra['listed_utc']}; every set-up's start record names commit "
        f"{', '.join(sorted(extra['commits']))} and lock {', '.join(sorted(x[:8] for x in extra['locks']))}. "
        f"Draw 1 only (D98: main estimates from draw 1 on all questions). Also held and not drawn: draws 2 and 3 of "
        f"no retrieval and naive RAG (270 answers each) and {extra['nosup_d2']} draw-2 answers of no supervisor "
        f"({extra['nosup_d2_subset']} of them on D98 subset questions). G9's two set-ups: findings/recompute/g9_inputs "
        f"(answers.json of each){extra['g9_more']}. G9's plan step attempts, all outside Supplementary Figure 10a: "
        + "; ".join(f"{LABEL[c]} {sum(v.values())} ({', '.join(f'{k} {x}' for k, x in sorted(v.items()))})"
                    for c, v in P["stress_steps"].items()) + ".", "",
        f"**Judge.** S3's rows (devstral-small-2:24b, plain call (a), run_sha256 {extra['run_sha256'][:12]}): G3's "
        f"collect of {extra['g3_collect_at']} ({extra['g3_rows']} rows, {extra['g3_rows_other']} of draws 2 and 3 not "
        f"read) and G1's collect of {extra['g1_collect_at']} (RLM-10's draw 1). Key (D188): RLM-10's "
        f"{fmt_int(extra['n_v25_rlm'])} answers of changed questions on key v2.5 from {extra['s6_g1_path']} (S528, S6G1 "
        f"after phase 3, the rows Figure 3 reads); G3's answers from their key v2.5 row (out_s6_g3, read through "
        f"scripts/judge_rows_v25.py) where one exists, else key v2.4: {fmt_int(extra['n_v25_g3'])} on key v2.5, "
        f"{fmt_int(extra['n_await'])} answers of changed questions still on key v2.4 until S6G3 is pulled. Unscored "
        f"judge rows: {unscored}. "
        f"Answers with no text, not scored and counted as a fail: {failed_txt}. "
        f"On the key v2.4 rows and on the rows chosen, every judged set-up's counts equal those of S480's recount "
        f"({extra['recount_path']}, written by "
        f"scripts/S480_fig4_recount.py, which imports neither this script nor S463 and counts the same files, on "
        f"the rows chosen by scripts/judge_rows_v25.py, shared with this script; each "
        f"of its inputs has the sha256 of the file read here): passes at score {PASS_T} and {PASS_RELAXED} and "
        f"questions with a share, refused, false-premise passed at {FP_T} and {FP_RELAXED} with their questions, "
        f"answers judged no_answer, unscored rows and out-of-scope questions sent to a direct answer. Passed at "
        f"{PASS_T}, refused, false premise passed at {FP_T}: {extra['known']}.", "",
        f"**The plan's N.** {fmt_int(N)} answers: {parts}. The distiller set-ups are counted as not run because "
        f"the Q82 count on the full pipeline's draw 1 is {extra['q82_full_over']} (Rule 12's zero branch, so Holm "
        f"runs over five); the checkpoint script (gate_distiller.sh) wants 405 answers and has not run (D98 left 135).",
        "",
        f"**G17 (panels {D} and {E}, D250).** S571's reading of draws 1 to 3 ({g17['reading']}, sha256 "
        f"{g17['reading_sha256'][:12]}), read through S576's per_answer and question_means; the Zhang RLM-10's "
        f"draws are G6's (cap 10), as S576 reads them. The legend's paired differences are S576's descriptive contrasts "
        f"on the mean of draws 1 to 3 ({g17['s576']}, sha256 {g17['s576_sha256'][:12]}), each computed again from the "
        f"reading before anything was written. Unscored judge cells counted as not passing: "
        + ", ".join(f"{G17_ARM_LABEL[a]} {k}" for a, k in g17["unscored"].items()) + ".", "",
        f"**Moved (D250):** old panel b, the plan step attempts against the distiller threshold, is Supplementary "
        f"Figure 10a (its rows in {rel(STEPS_OUT)}). Not drawn: the component benchmarks and distiller prompts (T3, "
        f"Supplementary Figures 10 and "
        f"11). {' '.join(x for x in (extra['g9_state'], extra['draws_state']) if x)} In Source Data only: each set-up minus the full pipeline, its "
        f"interval and P (Valerio, 2 November); the relaxed threshold's (score {PASS_RELAXED}) pass rate, interval, "
        f"difference and P; the false-premise questions passed at the relaxed threshold (score {FP_RELAXED}, D160 (8) "
        f"and (11)); each set-up's questions gained, lost and the same against the full pipeline (no plate, FF17); "
        f"questions sent to a direct answer and refused (A1); the refusal rate with its interval (D250); calls by "
        f"failure kind; the analyser's routing of the answerable and false-premise questions; G17's paired "
        f"differences (D250; in Source Data, not the legend, since S3 of 7 November).", "",
    ]
    legend = (
        f"**Figure {FIG_N} | Judge pass rate, refusal and cost of orchestration set-ups, and an "
        f"{FN.MENTORI_RLM_N.format(n=10)} ablation.** "
        f"gemini-3-flash answered {N_Q} questions once (n = {N_Q} per set-up) over one "
        # 8 Nov legend trim (Valerio: "too long", 323 words): "in every role", RLM-10's origin, the distiller prompts, the time
        # measure's parts, the set-ups' definitions and panel c's answers with no text (sheet d's answers_no_text)
        # go to Supplementary Note 5 and Source Data; d_notes is kept computed, unprinted
        f"20-paper index under {len(ALL)} set-ups (Supplementary Note 5). A pass is a judge score of {PASS_T}+. "
        + (f"{unscored} judge rows gave no score and are left out. " if unscored else "")
        + (f"The two always-distil rows hold no judge scores or search times yet. " if stress_open and no_time else
           f"The two always-distil rows hold no search times yet. " if no_time else "") +
        f"{A}, Judge score of each answerable question (n = {GROUP_N['answerable']}). "
        f"Right: pass rate, two-sided 95% percentile interval over 10,000 question resamples. {vs_full_text(S)} "
        f"{B}, Each out-of-scope question (n = {GROUP_N['not_answerable']}), refused (refusal score 3+) or not; dot, "
        f"sent to a direct answer. Right: each false-premise question (n = {GROUP_N['false_premise']}); outlined, "
        f"passed. "
        f"{C}, Model calls and time per answer; log axes. "
        f"{D}, {E}, {G17_ARM_LABEL[G17_CTRL]} (rerun), {G17_ARM_LABEL['package']} and {G17_ARM_LABEL[G17_CTRL]} "
        f"with {G17_ARM_LABEL['search_off']} or {G17_ARM_LABEL['gate_off']}, on one-paper and many-paper answerable "
        f"questions. "
        f"{D}, Concept recall (share of key concepts stated), each question's mean over {len(G17_DRAWS)} draws "
        f"(n = {ng['one']} and {ng['many']} questions per box). {E}, Per draw-{G17_F_DRAW} answer (n = {ng['one']} and "
        f"{ng['many']} answers per box): sub-calls returning paper text and distinct papers read; axes linear to "
        f"2, logarithmic above. Boxes, median and quartiles; whiskers, range; dots, one answer ({C}, {E}) or "
        f"question ({D}).")
    cap = (f"# Source Data Fig. {FIG_N}, caption\n\n**Source Data Fig. {FIG_N} | Numerical values plotted in Figure "
           f"{FIG_N}.** Provisional: drawn from {fmt_int(n)} of the {fmt_int(N)} answers in this figure's written "
           f"plan (draw 1 of eight G3 set-ups, of G9's two set-ups and of RLM-10). Data stamp: {stamp}. One sheet per "
           f"panel. "
           f"The pass rate is the share of answers the judge scores {PASS_T} or more; {PASS_RELAXED} or more is the "
           f"relaxed threshold. "
           f"Sheet Fig. {FIG_N}a: one 'setup' row per set-up and threshold ({PASS_T}, then {PASS_RELAXED}) with the "
           f"questions passed, the questions with a share, the pass rate and its 95% interval, the set-up minus the "
           f"full pipeline with its interval (none for the two baselines), the questions gained, lost and the same "
           f"against the full pipeline (no plate, FF17, 1 November), the exact two-sided sign-flip P, the Holm P and "
           f"the P the legend reads (Holm over the five pipeline set-ups, unadjusted for RLM-10; none for the "
           f"baselines and the stress set-ups); then one 'tile' row per set-up and answerable question (column, judge "
           f"kind, correctness, level drawn); and, once S6G7G3 is copied, one 'draw' row per set-up, draw and threshold "
           f"on the 29 answerable questions of D98's 45 (questions passed, questions; none yet: "
           f"{'present' if extra['draws_present'] else 'S6G7G3 not copied'}). A set-up with no judge rows keeps its "
           f"rows with their values blank. Sheet {sheet_name('c')}: one 'setup' row per "
           f"set-up (questions, refused, refusal rate, interval, one-sided bound of a 0 or a 100%, Source Data only "
           f"since D250; false-premise questions passed at correctness {FP_T} or more of n, and at the relaxed "
           f"{FP_RELAXED} or more of n; for the orchestrator set-ups the questions of each group sent to a direct "
           f"answer and the refused among those sent and not sent), then one 'tile' row per set-up and out-of-scope "
           f"question (column, judge kind, refusal score, refused, the analyser's decision), then one 'fp_tile' row "
           f"per set-up and false-premise question (column, judge kind, correctness, passed at {FP_T}, outlined on the "
           f"plate, and at {FP_RELAXED}). Sheet {sheet_name('d')}, for each measure (model calls, then own time in "
           f"seconds): one 'setup' row per set-up with the "
           f"answers, n drawn, minimum, first quartile, median, third quartile and maximum (model calls also the "
           f"calls, failed calls, cut calls and calls by failure kind; a set-up with no value its note), and one "
           f"'total' row (the answers, n drawn and set-ups drawn; the plate prints n drawn above each column); then "
           f"one 'answer' row per answer: model calls with failed and cut calls and the count of calls by status, own "
           f"time in seconds with the calls' seconds and the search seconds. Sheet {sheet_name('e')} (G17, D250): "
           f"one 'box' row per arm and question type (n, minimum, first quartile, median, third quartile, maximum of "
           f"the per-question concept recall in %, the mean of draws 1 to {len(G17_DRAWS)}; whether the box is flat), "
           f"then one 'question' row per arm and answerable question (concept recall at each draw and their mean, in "
           f"%), then one 'difference' row per paired contrast of {extra['g17']['s576']} on the mean of draws 1 to "
           f"{len(G17_DRAWS)} (Source Data only: arm, the arm it is minus, question type, measure, questions, the two "
           f"means, the mean difference and its two-sided 95% percentile interval over 10,000 question resamples, in "
           f"points, and the questions where each is higher). Sheet {sheet_name('f')} (G17, draw {G17_F_DRAW}): one "
           f"'box' row per measure (sub-calls that returned paper text, distinct papers read), arm and question type, "
           f"then one 'answer' row per arm and question with both measures. Old panel b's rows, the plan step "
           f"attempts, are Supplementary Figure 10a's (D250). Generated by "
           f"`uv run --frozen python {SCRIPT} figure` from G3's and G9's run records, S3's judge rows, G1's RLM-10 "
           f"records, and S571's G17 reading of draws 1 to {len(G17_DRAWS)} with S576's paired differences of it.\n\n"
           f"Proposed Data Availability sentence: \"The source data for Figure {FIG_N} is in Supplementary Data "
           f"{FIG_N + 1}.\"\n")   # D303: Data n + 1 (D302)
    return "\n".join(head) + "\n" + legend + "\n", cap


DOCS = {"main text": doc("02_Main_Text.docx"),
        "letter": LETTER,
        "LIST.md": LIST_MD}
# recorded in inputs_sha256 at DESIGN_AT; read as they stand by every check and the claims list (audit 27 Oct F1, part 4)
DESIGN_DOCS = (PLAN, LIST_MD, README_EXP, EXP03, DISTILLER, *DOCS.values())
# D304 (8 Nov): the claims list reads the agreed text (Claude Docs rev 3688) as the live documents read with every mark
# accepted: the main text, the Figure 5 legend (04_Figures_Tables) and the Supplementary Notes as S602 wrote them from the
# same export; the letter with every mark accepted (its round will be rebuilt, so the letter's anchor is provisional).
# DOCS above stays as DESIGN_AT recorded it (inputs_sha256); only the claims list reads these.
CLAIM_DOCS = {"main text": doc("02_Main_Text.docx"), "legend": doc("04_Figures_Tables.docx"),
              "SI": ROOT / "resubmission/06_supplementary/Supplementary_Information.docx", "letter": LETTER}
# (document, section to search under, fragment as the document prints it, what the plate gives now). D304 re-anchored
# every row on the agreed text; rows 8 to 10 were LIST.md findings until then and are now the sentences of the main text
# and Supplementary Note 5 that state them.
CLAIMS = [
    ("legend", "Figure 5 legend, 'Figure 5 | Judge pass rate, refusal and cost of orchestration set-ups'",
     "answered 135 questions once (n = 135 per set-up) over one 20-paper index under 11 set-ups",
     "{n_setups} set-ups, 135 questions (D48), {n_drawn} draw-1 answers drawn, judged"),
    ("main text", "Results, 'One routing decision sets refusal', 'To find what each part of Mentor::i's multi-agent "
     "pipeline contributes'", "Without retrieval, gemini-3-flash passed 37.2% of the 86 answerable questions",
     "panels a, b: no retrieval passes {raw_pass} of 86 at score 4 ({raw_rate}%, {raw_lo} to {raw_hi}); refuses "
     "{raw_ref}; descriptive (Rule 12)"),
    ("main text", "the same paragraph", "and naive RAG, one call over the 10 passages the retriever returns, raised "
     "this to 83.7%",
     "panel a: naive RAG passes {rag_pass} of 86 at score 4 ({rag_rate}%, {rag_lo} to {rag_hi}); descriptive, rate "
     "and interval only (Rule 12, D96 Q209)"),
    ("SI", "Supplementary Note 5, 'Set-ups and references'", "RLM-10 passed 74.4% (64 of 86), also refusing all 39",
     "panel a: RLM-10 passes {rlm_pass} of 86 at score 4 ({rlm_rate}%, {rlm_lo} to {rlm_hi}); minus the full "
     "pipeline {rlm_d} points ({rlm_dlo} to {rlm_dhi}), P {rlm_p} (claim P1, on its own)"),
    ("main text", "the same paragraph as row 2", "The full pipeline passed 75.6% (95% CI: 66.3% to 84.9%; Fig. 5a)",
     "panel a: the full pipeline passes {full_pass} of 86 at score 4 ({full_rate}%, {full_lo} to {full_hi}); the "
     "five set-ups against it, Holm P {holm}"),
    ("main text", "Results, 'Tested one at a time outside the pipeline with six models'",
     "the distiller kept only 38.1% to 59.2% of the numbers in its input",
     "not on this plate: the component benchmarks are Supplementary Figure 10's (S524, step supp10_11)"),
    ("letter", "Reviewer 3, Major Point 4b, 'The revised experiments also show where refusal comes from'",
     "and naive RAG refused all 39. The full Mentor::i pipeline refused only 2.",
     "panel b: refused {rag_ref} by naive RAG, {full_ref} by the full pipeline (Rule 9)"),
    ("main text", "Results, 'The one large effect was on refusal'",
     "The analyser sent 37 of the 39 out-of-scope questions to a direct answer from the model's memory, so the full "
     "pipeline refused only 2 of them",
     "panel b: full pipeline {fp_direct} of 39 to a direct answer on draw 1, {fp_ref_direct} of those refused; "
     "routing fix {fix_direct} of 39, refuses {fix_ref}"),
    ("main text", "Results, 'No single component changed accuracy detectably'",
     "The distiller never ran unless forced (the longest step output reached 32.2% of its 209,712-character trigger)",
     "Supplementary Figure 10a (old 4b, D250): {q82_over} of {steps} step attempts of the six pipeline set-ups over {thr:,} characters; longest "
     "{longest:,} ({longest_pct}% of the threshold)"),
    ("SI", "Supplementary Note 5, 'Single components'",
     "Forced onto every step, the distiller lowered the pass rate: the always-distil set-up passed 62.8% (54 of 86)",
     "G9, descriptive, one draw: always distil {g9_a_steps} step attempts, always distil F1 {g9_f_steps}, status "
     "{g9_status}; median model calls {g9_a_calls}, {g9_f_calls}; {g9_judged}"),
]

def docx_text(p) -> str:
    """A .docx's paragraphs as text; p a path or the file's bytes."""
    import zipfile
    x = zipfile.ZipFile(io.BytesIO(p) if isinstance(p, bytes) else p).read("word/document.xml").decode()
    return "\n".join("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group()))
                     for m in re.finditer(r"<w:p[ >].*?</w:p>", x, re.S))


def refused_of(r) -> str:
    """'<refused> of <questions>', with a 0's one-sided 95% upper bound (Rule 9) or a 100%'s lower bound (O2) as
    sheet c records it (Source Data only since D250)."""
    b = (f" (one-sided 95% upper bound {pct1(r['zero_bound_one_sided'])}%)" if r["zero_bound_one_sided"] is not None
         else f" (one-sided 95% lower bound {pct1(r['full_bound_one_sided'])}%)" if r["full_bound_one_sided"] is not None
         else "")
    return f"{r['refused']} of {r['questions']}{b}"


def claim_values(P, st, n):
    S = P["sheets"]
    a = {r["config"]: r for r in S["a"] if r["row"] == "setup" and r["threshold"] == PASS_T}
    c = {r["config"]: r for r in S["c"] if r["row"] == "setup"}
    pooled = next(r for r in S["b"] if r["row"] == "pooled")
    v = {"n_setups": len(ALL), "n_drawn": fmt_int(n), "thr": pooled["threshold_chars"],
         "q82_over": pooled["over_threshold"], "steps": pooled["attempts"], "longest": pooled["longest_chars"],
         "longest_pct": S457.half_up(pooled["longest_pct_of_threshold"], 1)}
    for k, cf in (("raw", "raw_gemini"), ("rag", "naive_rag"), ("rlm", RLM), ("full", FULL)):
        r = a[cf]
        v.update({f"{k}_pass": r["passed"], f"{k}_rate": pct1(r["pass_rate"]), f"{k}_lo": pct1(r["interval_low"]),
                  f"{k}_hi": pct1(r["interval_high"]), f"{k}_ref": refused_of(c[cf])})
    r = a[RLM]
    v.update(rlm_d=S457.half_up(100 * r["minus_full"], 1), rlm_dlo=S457.half_up(100 * r["minus_full_low"], 1),
             rlm_dhi=S457.half_up(100 * r["minus_full_high"], 1), rlm_p=S457.half_up(r["p_drawn"], 2))
    hp = [a[cf]["p_holm"] for cf in FAMILY]
    lo_, hi_ = S457.half_up(min(hp), 2), S457.half_up(max(hp), 2)
    v["holm"] = f"{lo_} for all five" if lo_ == hi_ else f"{lo_} to {hi_}"
    calls = {r["config"]: r for r in S["d"] if r["row"] == "setup" and r["measure"] == D_MEASURES[0][1]}
    steps = P["stress_steps"]
    v.update(g9_a_steps=sum(steps[STRESS[0]].values()), g9_f_steps=sum(steps[STRESS[1]].values()),
             g9_status=", ".join(sorted({k for x in steps.values() for k in x})),
             g9_a_calls=S457.half_up(calls[STRESS[0]]["median"], 0), g9_f_calls=S457.half_up(calls[STRESS[1]]["median"], 0),
             g9_judged=(f"passed at {PASS_T}: {a[STRESS[0]]['passed']} and {a[STRESS[1]]['passed']} of "
                        f"{a[STRESS[0]]['questions']} ({pct1(a[STRESS[0]]['pass_rate'])}%, "
                        f"{pct1(a[STRESS[1]]['pass_rate'])}%); refused {c[STRESS[0]]['refused']} and "
                        f"{c[STRESS[1]]['refused']} of {c[STRESS[0]]['questions']}"
                        if STRESS[0] in P["judged"] else NOT_JUDGED))
    v.update(fp_direct=c[FULL]["direct_answer_n"], fp_ref_direct=c[FULL]["refused_of_direct"],
             fix_direct=c["orch_factual_to_documents"]["direct_answer_n"],
             fix_ref=refused_of(c["orch_factual_to_documents"]))
    return v


def claims_md(P, st, n, stamp):
    # each document as it stands (a claim deleted or reworded shows NOT FOUND); inputs_sha256 alone records DESIGN_AT
    # (audit 27 Oct F1, part 4: reading DESIGN_AT here made the header's "as it stands" false)
    texts = {k: (docx_text(p) if p.suffix == ".docx" else p.read_text()) for k, p in CLAIM_DOCS.items()}
    vals = claim_values(P, st, n)
    lines = [f"# Figure {FIG_N}: claims list (D82)", "",
             f"Written by `{SCRIPT}`. Data stamp: {stamp}. Each claim the documents make about Figure {FIG_N}, found by "
             f"its words in the document as it stands (found / NOT FOUND), with what this plate gives now (draw 1, "
             f"provisional). No verdict word (Rule 11) is given; the Results and letter wording waits for draws 2 and "
             f"3 and the question-type split (D132 Q5, Q6). D304 (8 November): every row is anchored on the agreed "
             f"text (Claude Docs rev 3688, the live documents with every mark accepted); the letter's row on the letter "
             f"with every mark accepted, provisional until the letter round is rebuilt.", "",
             "| # | document | where | claim (as printed) | found | now |", "|---|---|---|---|---|---|"]
    for i, (doc, where, frag, now) in enumerate(CLAIMS, 1):
        found = frag in texts[doc]
        lines.append(f"| {i} | {doc} | {where} | {' '.join(frag.split())} | {'found' if found else 'NOT FOUND'} "
                     f"| {now.format(**vals)} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------------------------
# figure
# ---------------------------------------------------------------------------------------------------------------
OWNED = (f"Figure {FIG_N}*", f"Source Data Fig. {FIG_N}*", f"figure{FIG_N}_numbers.json",
         f"figure{FIG_N}_provenance.json", "legend_draft.md", "claims.md", "records_manifest.json")


def load(rec: Path):
    pj, data = read_records(rec)
    groups, types, order = key_groups()
    retr = {}
    for c in CONFIGS:
        p = rec / "findings" / "runs" / run_of(c) / "retrievals.jsonl"
        if p.is_file():
            retr[c] = p.read_bytes()
    return pj, data, groups, types, order, retr


def figure(args):
    if not selftest(quiet=True):
        raise SystemExit("selftest failed: nothing written (run `selftest` to see which check)")
    S457.figure_lock_agreed()
    given = {k: getattr(args, k) for k in FROZEN}
    fpaths, frozen_rec = frozen_inputs([k for k, v in given.items() if v is None])   # D155: checked before reading
    ins = {k: Path(v).expanduser().resolve() if v is not None else fpaths[k] for k, v in given.items()}
    recount_p = Path(args.recount).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    view_tmp = Path(tempfile.mkdtemp(prefix="S472_view_"))
    try:
        return _figure(args, ins, recount_p, out, given, frozen_rec, view_tmp)
    finally:
        shutil.rmtree(view_tmp, ignore_errors=True)


def check_draw_counts(draws: list | None, recount: dict) -> dict | None:
    """The 'draw' rows against the recount's draw_counts ({config|draw|threshold: [passed, questions]}): both absent,
    or equal, else refused."""
    mine = None if draws is None else {f"{r['config']}|{r['draw']}|{r['threshold']}": [r["passed"], r["questions"]]
                                       for r in draws}
    theirs = recount.get("draw_counts")
    if mine != theirs:
        raise Refused(f"REPRODUCTION FAILED, nothing written: the 'draw' rows here hold {len(mine or {})} counts, the "
                      f"recount {len(theirs or {})}, or a count differs")
    return None if mine is None else {"rows": len(mine), "equal_to": "the recount's draw_counts"}


def _figure(args, ins, recount_p, out, given, frozen_rec, view_tmp):
    steps_out = Path(getattr(args, "steps_out", None) or STEPS_OUT).expanduser().resolve()
    rec, collect, rlm_collect, rlm_answers, g9, s6_g1 = (ins[k] for k in ("records", "collect", "rlm_collect",
                                                                         "rlm_answers", "g9", "s6_g1"))
    pj, data, groups, types, order, retr = load(rec)
    g9_sha, g9_data, g9_retr = read_g9(g9, ins["g9_retrievals"])
    data.update(g9_data)
    retr.update(g9_retr)
    thr = threshold_chars()
    fn, q82 = compute(data, retr, groups, types, order, thr, setups=G3_ALL)
    try:
        reproduced = reproduce(rec, data, q82)
    except Refused as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    # the collects' sidecars name the folders collect read; read through a view naming the copies beside each collect
    # (collect_view); every sha256 below is of the files themselves, not of a view
    g3_view = collect_view(collect, view_tmp / "g3")
    g1_view = collect_view(rlm_collect, view_tmp / "g1")
    g3 = read_g3_collect(g3_view, groups, need_stress=given["collect"] is not None or FROZEN["collect"] != FROZEN_RIGHT)
    rlm = read_rlm(g1_view, rlm_answers, groups, s6_g1)
    if g3["run_sha256"] != rlm["run_sha256"]:
        raise Refused(f"G3's judge rows are under run_sha256 {g3['run_sha256'][:12]}, RLM-10's under "
                      f"{rlm['run_sha256'][:12]}: not one judge set-up, so RLM-10 cannot be set against the full "
                      f"pipeline")
    # D188: the v2.4 cells first (the anchor, as the frozen collects give them), then the cells judge_rows_v25 chose
    fn24 = json.loads(json.dumps(fn))
    cells24 = join_judge(fn24, g3, {"cells": rlm["cells_v24"]}, groups)
    jr3 = g3_judge_rows(g3, g3_view, groups, fn["answers"], s6_root=s6_g1)   # D203: out_s6_g3 frozen beside S6G1
    cells = join_judge(fn, {**g3, "cells": jr3["cells"]}, rlm, groups)
    plan = planned(q82[FULL]["over_threshold"])
    if not plan["zero_branch"]:
        raise Refused(f"the Q82 count is {q82[FULL]['over_threshold']}: Rule 12's family is seven set-ups, and the "
                      f"two distiller set-ups are not drawn here")
    st = statistics(cells, groups, order)
    st24 = st if cells24 == cells else statistics(cells24, groups, order)
    dr = read_draw_rows(g3_view, g1_view, groups, Path(g3["outs_here"][0]).parent, s6_g1)
    draws = draw_rows(dr["cells"], groups, dr["subset"]) if dr else None
    try:
        recount = json.loads(recount_p.read_text())
        reproduced["s480_at_head"] = check_recount_script(recount, s480_head_sha())    # D136 Q12
        read_sha = read_inputs_sha(rec, collect, rlm_collect, rlm_answers, rlm, g9_sha, s6_g1)
        reproduced["s480_recount_v24"] = reproduce_recount(st24, fn24, groups, recount, read_sha, key="counts_v24")
        reproduced["s480_recount"] = reproduce_recount(st, fn, groups, recount, read_sha)
        reproduced["s480_draw_counts"] = check_draw_counts(draws, recount)
        reproduced["new_rows"] = reproduce_new(collect, st, cells, groups, order, FR.frozen(*FROZEN_RIGHT))
    except Refused as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    judge_rows = {"g3": jr3["record"], "rlm_10": rlm["judge_rows"],
                  "provisional": jr3["record"]["provisional"] or rlm["judge_rows"]["rlm_10_draw_1"]["awaiting_s6"] > 0,
                  "cells_differ_from_v24": sum(1 for k in cells if cells[k] != cells24[k])}
    n_await = jr3["record"]["awaiting_s6_read"]
    n_v25_g3, n_v25_rlm = jr3["record"]["cells_from_v25"], rlm["judge_rows"]["rlm_10_draw_1"]["cells_from_v25"]
    try:
        g17 = read_g17()                                  # REPRODUCES S576 first (read_g17), else nothing written
    except Refused as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    reproduced["g17_s576"] = (f"S576's descriptive contrasts and arm means on draws 1 to {len(G17_DRAWS)} "
                              f"({g17['s576']}) equal S576.evaluate() and arm_means() run again on {g17['reading']}; "
                              f"S576 names the reading and {g17['contrasts_path']} by the sha256 read here")
    P = panel_rows(fn, q82, st, cells, rlm, groups, order, thr, draws=draws, g17=g17)
    n, N = len(fn["answers"]) + len(rlm["rows"]), plan["N"]
    G3 = rec / "findings" / "recompute" / "G3_runs"
    starts = [json.loads(p.read_text()) for p in sorted(G3.glob("g3_*.start.json"))]
    starts += [json.loads(p.read_text()) for p in sorted(G3.glob("g3_*_attempt_*/g3_*.start.json"))]
    commits = {s["commit"][:7] for s in starts}
    locks = {s["lock_sha256"] for s in starts}
    if not locks or not locks <= LOCKS_OK:
        raise Refused(f"G3's start records name locks {sorted(locks)}, not D88's {LOCK_WANT[:8]}")
    sub = set(json.loads(D98_SUBSET.read_text())["ids"])
    nosup2 = [r for r in data["orch_no_supervisor"]["results"] if r["draw"] == 2]
    newest = max(pj["files"][f"findings/runs/{run_of(c)}/answers.json"]["mtime"] for c in CONFIGS)
    when = dt.datetime.fromtimestamp(newest, ZoneInfo(TZ)).strftime("%Y-%m-%d %H:%M %Z")
    # nothing of G9 is pending once both its judge rows and its retrievals are read, so the sentence is then empty
    g9_state = "" if g3["stress_judged"] and g9_retr else (
                (f"G9's two set-ups are judged. " if g3["stress_judged"] else
                 f"G9's two set-ups: their judge rows are not copied, so a and c print '{NOT_JUDGED}'. ") +
                (f"Their retrievals are read." if g9_retr else
                 f"Their retrievals are not copied, so e prints '{NO_SEARCH}'."))
    draws_state = ("The 'draw' rows of sheet a are in." if draws else
                   "The 'draw' rows of sheet a stay out until S6G7G3 is copied.")
    stamp = (f"PROVISIONAL: {fmt_int(n)} of {fmt_int(N)} answers, draw 1 of eight G3 set-ups (records of {when}, copied "
             f"{pj['listed_utc']}, judged by S3, G3 collect of {g3['collect_at']}), of RLM-10 (G1, G1 collect of "
             f"{rlm['collect_at']}) and of G9's two set-ups ({'judged' if g3['stress_judged'] else 'judge rows not copied'}"
             f", {'retrievals read' if g9_retr else 'retrievals not copied'}); key v2.5 judge rows: RLM-10's "
             f"{fmt_int(n_v25_rlm)} from S6G1 after phase 3 (frozen fig3_s6_inputs, S528), G3's {fmt_int(n_v25_g3)}; "
             f"{fmt_int(n_await)} G3 answers of changed questions still on key v2.4 (D188, awaiting S6G3); 'draw' rows "
             f"{'in' if draws else 'out until S6G7G3 is copied'}; T3 not drawn; d, e: G17 (D250), concept recall the mean "
             f"of draws 1 to {len(G17_DRAWS)}, reading paper text draw {G17_F_DRAW}, S571's reading "
             f"{g17['reading_sha256'][:8]}, S576's differences {g17['s576_sha256'][:8]}")
    tag = f" (provisional, {n} of {N})"
    example = next(q["question"] for q in questions_of() if q["id"] == EXAMPLE_OUT_OF_SCOPE)
    if groups[EXAMPLE_OUT_OF_SCOPE] != "not_answerable":
        raise Refused(f"{EXAMPLE_OUT_OF_SCOPE} is not an out-of-scope question in the D5 key")
    extra = {"clone_head": pj["clone_head"], "listed_utc": pj["listed_utc"], "commits": commits, "locks": locks,
             "nosup_d2": len(nosup2), "nosup_d2_subset": sum(r["question_id"] in sub for r in nosup2),
             "run_sha256": g3["run_sha256"], "g3_collect_at": g3["collect_at"], "g3_rows": g3["rows"],
             "g3_rows_other": sum(g3["rows_other_draws"].values()), "g1_collect_at": rlm["collect_at"],
             "q82_full_over": q82[FULL]["over_threshold"], "judge_rows": judge_rows, "n_await": n_await,
             "n_v25_g3": n_v25_g3, "n_v25_rlm": n_v25_rlm, "s6_g1_path": rel(s6_g1),
             "recount_path": rel(recount_p), "g9_state": g9_state, "draws_state": draws_state,
             "g9_more": ("; their judge rows in the G3 collect read and their retrievals.jsonl in "
                         f"{rel(ins['g9_retrievals'])}" if g3["stress_judged"] and g9_retr else ""),
             "draws_present": bool(draws), "example_question": example, "g17": g17,
             "known": "; ".join(f"{LABEL[c]} {v[f'answerable_pass_{PASS_T}']}, {v['not_answerable_refused_3']}, "
                                f"{v[f'false_premise_pass_{FP_T}']}" for c, v in reproduced["s480_recount"].items())}
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*_provenance.json"):
        other = json.loads(p.read_text()).get("script")
        if other != SCRIPT:
            raise Refused(f"{rel(out)} holds {p.name} written by {other!r}, not {SCRIPT}")
    stage = Path(tempfile.mkdtemp(prefix="S472_", dir=out.parent))
    try:
        paths = {x: stage / f"Figure {FIG_N}{tag}.{x}" for x in ("pdf", "svg", "png")}
        W, H, printed, rb = draw(P, paths)
        bad, n_checked = check_drawn(rb, P)
        if bad:
            raise Refused("check_drawn FAILED, nothing written: " + "; ".join(bad[:5]))
        sheets = sheets_of(P)
        sd = stage / f"Source Data Fig. {FIG_N}{tag}.xlsx"
        S457.write_source_data(sheets, sd)
        FR.deterministic_xlsx(sd)                       # D155: no write time in the workbook
        FR.check_pdf_deterministic(paths["pdf"])        # D155: no creation or modification date
        FR.check_svg_deterministic(paths["svg"])
        numbers = stage / f"figure{FIG_N}_numbers.json"
        numbers.write_text(json.dumps({"stamp": stamp, "what": "every number the plate draws, sheet by sheet as "
                                       f"Source Data Fig. {FIG_N} holds them (S448 R8 compares the workbook with "
                                       "this file)", "sheets": {nm: {"columns": cols, "rows": rows}
                                                                for nm, cols, rows in sheets},
                                       "printed": printed, "printed_what": "every number printed on the plate: the "
                                       "SVG group id of its text, and the Source Data sheet, row and format it is "
                                       "written from (or fixed, with why)"}, indent=1, default=str) + "\n")
        command = command_of(given, recount_p)
        legend, cap = legend_and_caption(P, st, n, N, plan, stamp, extra, command)
        (stage / "legend_draft.md").write_text(legend)
        capf = stage / f"Source Data Fig. {FIG_N} caption{tag}.md"
        capf.write_text(cap)
        (stage / "claims.md").write_text(claims_md(P, st, n, stamp))
        manifest = {"what": "the G3 records this plate reads, copied read-only from the Studio by S472 pull",
                    "copied_to": (f"frozen (D155): {FROZEN['records'][0]}.tar, folder {FROZEN['records'][1]} (the tar's "
                                  f"sha256 in {rel(FROZEN_SUMS)})" if given["records"] is None else
                                  rel(rec) if rec.is_relative_to(ROOT) else "outside the repository (pull --to)"),
                    **pj}
        (stage / "records_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        repo_inputs = [PLAN, PREFLIGHT, D98_SUBSET, DISTILLER, EXP03, LOCK, FIGURE_LOCK, LIST_MD, README_EXP,
                       ROOT / "scripts" / "S457_fig2_panels.py", ROOT / "scripts" / "S463_fig2_ranking.py",
                       ROOT / "scripts" / "judge_rows_v25.py", ROOT / "scripts" / "house_style.py",
                       ROOT / "scripts" / "figure_names.py", ROOT / "scripts" / "S575_g17_contrasts.py",
                       ROOT / "scripts" / "S576_d249_hypotheses.py", G17_READING, G17_S576, G17_CONTRASTS,
                       *DOCS.values()]
        side = lambda p: p.with_name(p.name + ".json")
        # D155: no build time, HEAD or working-tree state (each made two builds of the same inputs differ); the
        # script, every input and every output are named by sha256 instead
        prov = {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                "command": command,
                "python": platform.python_version(),
                "frozen_inputs": {"sums": {"path": rel(FROZEN_SUMS), "sha256": sha256_file(FROZEN_SUMS)},
                                  "read_by_default": {k: f"{s_}:{r_}" for k, (s_, r_) in FROZEN.items()
                                                      if given[k] is None},
                                  **frozen_rec},
                "records": {"from": pj["from"], "clone_head": pj["clone_head"], "listed_utc": pj["listed_utc"],
                            "sha256": {f: v["sha256"] for f, v in pj["files"].items()}},
                "judge": {"g3_collect": {"path": rel(collect), "sha256": sha256_file(collect),
                                         "sidecar_sha256": sha256_file(side(collect)), "rows": g3["rows"],
                                         "rows_other_draws": g3["rows_other_draws"], "units": rel_units(g3["units"])},
                          "g1_collect": {"path": rel(rlm_collect), "sha256": sha256_file(rlm_collect),
                                         "sidecar_sha256": sha256_file(side(rlm_collect)), "rows": rlm["rows_read"],
                                         "units": rel_units(rlm["units"])},
                          "rlm_answers": rel_keys(rlm["answers_inputs"]), "run_sha256": g3["run_sha256"],
                          "unscored": st["unscored"], "failed": st["failed"],
                          "judge_rows_v25": judge_rows,
                          "s6_g1": {"path": rel(s6_g1), "sums_sha256": sha256_file(s6_g1 / "SHA256SUMS")},
                          "draw_rows": ({"units": dr["units"], "sources": dr["sources"]} if dr else
                                        "out_s6_g7_g3 is not beside out_g3: the 'draw' rows stay out")},
                "g17": {"decision": "D250 (layout), D240 (G17)", "reading": g17["reading"],
                        "reading_sha256": g17["reading_sha256"], "s576": g17["s576"],
                        "s576_sha256": g17["s576_sha256"], "s576_code_sha256": g17["s576_code_sha256"],
                        "s575_contrasts": g17["contrasts_path"], "s575_contrasts_sha256": g17["contrasts_sha256"],
                        "resamples": g17["boot"], "seed": g17["seed"], "unscored_cells": g17["unscored"],
                        "drawn": f"d: concept recall per question, mean of draws {list(G17_DRAWS)}; e: sub-calls that "
                                 f"returned paper text and distinct papers read per draw-{G17_F_DRAW} answer; four "
                                 f"arms, one-paper and many-paper questions, house boxes",
                        "source_data_only": "S576's paired differences on the mean of draws 1 to 3 (the legend "
                                            "quotes each arm minus the control on concept recall)"},
                "g9": {"path": rel(g9), "answers_sha256": g9_sha, "judged": g3["stress_judged"],
                       "retrievals": sorted(g9_retr), "stress_steps": fn["stress_steps"]},
                "recount": {"path": rel(recount_p), "sha256": sha256_file(recount_p),
                            "script": (recount.get("provenance") or {}).get("script"),
                            "script_sha256": (recount.get("provenance") or {}).get("script_sha256"),
                            "inputs_checked": sorted(recount.get("inputs") or {})},
                "inputs_sha256": {(f"{rel(p)}@{DESIGN_AT}" if p in DESIGN_DOCS else rel(p)):
                                  (hashlib.sha256(design_bytes(p)).hexdigest() if p in DESIGN_DOCS else sha256_file(p))
                                  for p in repo_inputs},
                "inputs_read": f"every input as it stands in the working tree, every check and the claims list on "
                               f"those; inputs_sha256 records the design documents (DESIGN_DOCS) as they stood at "
                               f"DESIGN_AT {DESIGN_AT} (git show), under names carrying @{DESIGN_AT}; exp_03's "
                               f"STRESS_CONFIG_NAMES and distiller_firing.py's code (less its docstring) required "
                               f"the same as at DESIGN_AT",
                "model_calls": 0, "stamp": stamp, "page_mm": [W, H],
                "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK),
                                "status": S457.FLOCK["status"]},
                "run_lock_now": {"path": rel(LOCK), "sha256": sha256_file(LOCK)},
                "g3_start_records": {"commits": sorted(commits), "lock_sha256": sorted(locks), "n": len(starts)},
                "reproduced": reproduced, "planned_answers": plan, "q82": q82,
                "drawn_check": f"check_drawn(): {n_checked} drawn marks equal their Source Data",
                "dots_overlapping": {f"{L} {LABEL.get(c) or G17_ARM_LABEL[c]}": k for L, c, k in rb["overlap"] if k},
                "held_not_drawn": {"baselines draws 2 and 3": {c: 2 * N_Q for c in BASELINES},
                                   "orch_no_supervisor draw 2": extra["nosup_d2"],
                                   "of which on D98 subset questions": extra["nosup_d2_subset"]},
                "panels": {"a": "P-1 (D132), full width (D250): the 86 answerable questions by set-up, tiles in "
                                "three cividis levels (4 or 5, 3, 2 or less or no answer) in one shared order; pass "
                                "rate at 4 with the Rule 2 interval. Difference from the full pipeline and P: Source "
                                "Data only (Valerio, 2 November)",
                           "b": "R-1 (D132) as D250 set it: the 39 out-of-scope questions by set-up, tiles refused "
                                "or not, a dot where the analyser sent the question to a direct answer; the 10 "
                                "false-premise questions as tiles of their own, a pass at 4 outlined in vermillion; "
                                "no refusal rate margin (Source Data only) and no false-premise column (sheet b)",
                           "c": "C-2 and A-3 (D132), moved up beside b (D250): per set-up, on b's rows, model calls "
                                "per answer (log axis by doubling) and own time per answer (calls' wall_s + search_s, "
                                "log axis) as two box columns, each box over one grey dot per answer; RLM-10's time "
                                "row prints that no search time was recorded; each column's answers above it; failed "
                                "and cut calls in sheet c only (sheet d inside this script)",
                           "d": "G17 (D250, option 2b): concept recall per answerable question, each question's mean "
                                "over draws 1 to 3, one house box per arm and question type, dots one question each",
                           "e": "G17 (D250, option 2b): per draw-1 answer, sub-calls that returned paper text and "
                                "distinct papers read, house boxes on an axis linear to 2 and logarithmic above",
                           "moved": "old b (F-2, the plan step attempts against the distiller threshold) is "
                                    "Supplementary Figure 10a (S524), from " + rel(STEPS_OUT)},
                "colours": {"a, b": S457.FLOCK["colour"]["continuous"], "dots": S457.DOT_GREY,
                            "b false-premise pass": FP_PASS,
                            "d, e arms": {G17_ARM_LABEL[a]: G17_COL[a] for a, _ in G17_ARMS}}}
        prov["files"] = {p.name: sha256_file(p) for p in [*paths.values(), sd, capf, numbers,
                                                            stage / "legend_draft.md", stage / "claims.md",
                                                            stage / "records_manifest.json"]}
        (stage / f"figure{FIG_N}_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
        steps = steps_file(P)
        steps["provenance"] = {"script": SCRIPT, "script_sha256": prov["script_sha256"], "command": command,
                               "figure4_provenance_sha256": sha256_file(stage / f"figure{FIG_N}_provenance.json"),
                               "records_sha256": prov["records"]["sha256"]}
        for pat in OWNED:
            for old in out.glob(pat):
                old.unlink()
        for p in stage.iterdir():
            shutil.move(str(p), out / p.name)
        steps_out.parent.mkdir(parents=True, exist_ok=True)
        steps_out.write_text(json.dumps(steps, indent=1, default=str) + "\n")
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print(stamp)
    print("reproduced: g3_draw1_stop.log key counts of " + ", ".join(
        f"{c} {v['records']}" for c, v in reproduced.items() if c in ORCH)
        + "; plan.csv G3 'all three draws' for " + ", ".join(BASELINES)
        + f"; distiller_firing.count() on the full pipeline {reproduced['q82_distiller_firing_count']['steps_over_threshold']}"
          f" of {reproduced['q82_distiller_firing_count']['step_attempts']} steps over "
          f"{reproduced['q82_distiller_firing_count']['threshold_chars']:,} (this script's count equal)"
        + f"; S480's recount ({extra['recount_path']}) made from the files read here, its counts equal "
          f"(passed at {PASS_T}, refused, false premise passed at {FP_T}): " + extra["known"])
    print(f"check_drawn: {n_checked} drawn marks equal their Source Data")
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W:.0f} x {H:.1f} mm), Source Data, caption, "
          f"figure{FIG_N}_numbers.json, legend_draft.md, claims.md, records_manifest.json, "
          f"figure{FIG_N}_provenance.json into {rel(out)}")


# ---------------------------------------------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------------------------------------------
FAKE_RUN_SHA = "f1" * 32


def fixture_g3(to: Path, groups: dict, order: list, kinds: dict, mutate=None, setups=None) -> Path:
    """A synthetic G3 collect output of the real shape: <to>/out/start_1.json, per set-up a judge/<run>/ folder with
    judge_passages.jsonl, judge_passages_headers.jsonl and judge_passages_recheck.jsonl (as judge_passages.py and
    run_s3.sh write them), and <to>/g3_collect.jsonl with its sidecar. Draw 1 of setups (default the eight set-ups),
    plus naive RAG's draw 2 (rows of another draw, not read). kinds: {(config, question): "no_answer" | "error"}; every
    other row is "ok" with the score fixture_score() gives. mutate(rows, side, out) may alter them before they are
    written."""
    m = s463()
    out = to / "out"
    rows = []
    setups = CONFIGS if setups is None else setups
    for c in setups:
        for d in ((1, 2) if c == "naive_rag" else (1,)):
            for q in order:
                g = groups[q]
                st = kinds.get((c, q), "ok")
                a = {"status": st}
                if st == "ok":
                    a["scores"] = {m.METRIC[g]: fixture_score(c, q, groups, order)}
                rows.append({"question_id": q, "config": c, "draw": d, "run_id": run_of(c),
                             "answer_key": f"{INDEX}|{c}|{q}|d{d}", "answerable_prompt": g != "not_answerable",
                             "item_sha256": hashlib.sha256(f"{c}{q}{d}".encode()).hexdigest(), "a": a,
                             "lock_sha256": LOCK_WANT, "run_sha256": FAKE_RUN_SHA, "at": "2026-10-24T00:00:00"})
    side = {"_provenance": {"script": "selftest", "at": "2026-10-24T00:00:00", "inputs": [str(out)]},
            "rows": len(rows), "run_sha256": FAKE_RUN_SHA, "replaced": 0, "added_by_replace": 0, "set": "G3"}
    recheck_equal = True
    if mutate:
        recheck_equal = mutate(rows, side, out) is not False
    side["rows"] = side.get("rows_override", len(rows))
    side.pop("rows_override", None)
    (out / "judge").mkdir(parents=True, exist_ok=True)
    (out / "start_1.json").write_text(json.dumps({"lock_sha256": LOCK_WANT}))
    for c in setups:
        f = out / "judge" / run_of(c)
        f.mkdir(exist_ok=True)
        mine = [r for r in rows if r.get("config") == c]
        (f / "judge_passages.jsonl").write_text("".join(json.dumps(r) + "\n" for r in mine))
        (f / "judge_passages_headers.jsonl").write_text(json.dumps(
            {"run_sha256": FAKE_RUN_SHA, "model": m.JUDGE, "model_digest": m.JUDGE_DIGEST,
             "lock_sha256": LOCK_WANT}) + "\n")
        ok = [r for r in mine if r["draw"] == 1 and r["a"]["status"] != "no_answer"][:10]
        (f / "judge_passages_recheck.jsonl").write_text("".join(json.dumps(
            {"key": f"{run_of(c)}|{r['answer_key']}", "run_sha256": FAKE_RUN_SHA,
             "equal": recheck_equal or i > 0}) + "\n" for i, r in enumerate(ok)))
    col = to / "g3_collect.jsonl"
    col.write_text("".join(json.dumps(r) + "\n" for r in rows))
    col.with_name(col.name + ".json").write_text(json.dumps(side))
    return col


def fixture_score(c, q, groups, order):
    """The synthetic judge: answerable, correctness 5 for the full pipeline and RLM-10, else 4 except every third
    answerable question (2); not answerable, refusal 5 for the routing fix, 3 for the full pipeline's first, else 0;
    false premise, correctness 4 on the first five false-premise questions, 3 on the other five (D160 (11): 5 of 10
    pass at 4, 10 of 10 at the relaxed 3)."""
    g = groups[q]
    if g == "answerable":
        j = [x for x in order if groups[x] == "answerable"].index(q)
        return 5 if c in (FULL, RLM) else (2 if j % 3 == 0 else 4)
    if g == "not_answerable":
        first = [x for x in order if groups[x] == "not_answerable"][0]
        return 5 if c == "orch_factual_to_documents" else (3 if (c == FULL and q == first) else 0)
    return 4 if [x for x in order if groups[x] == "false_premise"].index(q) < 5 else 3


def selftest(quiet=False) -> bool:
    res = []

    def check(name, ok, detail=""):
        res.append(bool(ok))
        if not quiet or not ok:
            print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + detail if detail and not ok else ''}")

    def refused(name, f, want=""):
        try:
            f()
            check(name, False, "not refused")
        except Refused as x:
            check(name, want in str(x), str(x)[:200])

    # answer_search_s: an earlier attempt's line before a, another item's line, a partial line after b
    rid = run_of("naive_rag")
    lines = [{"run_id": rid, "item_id": "Q1", "run_draw": 1, "search_s": 9.0},      # earlier attempt
             {"run_id": rid, "item_id": "Q1", "run_draw": 1, "search_s": 1.25},
             {"run_id": rid, "item_id": "Q2", "run_draw": 1, "search_s": 7.0},      # another item
             {"run_id": rid, "item_id": "Q1", "run_draw": 1, "search_s": 0.5}]
    blob = b"".join((json.dumps(x) + "\n").encode() for x in lines)
    a = len((json.dumps(lines[0]) + "\n").encode())
    r = {"run_id": rid, "question_id": "Q1", "draw": 1, "generation": {"retrievals_bytes": [a, len(blob)]}}
    check("search: the attempt's own lines", answer_search_s(blob, r) == 1.75, str(answer_search_s(blob, r)))
    r2 = {**r, "generation": {"retrievals_bytes": [a, len(blob) - 3]}}
    check("search: a partial last line is not read", answer_search_s(blob, r2) == 1.25)
    r3 = {**r, "generation": {"retrievals_bytes": [a + 5, len(blob)]}}
    check("search: an offset inside a line skips that line", answer_search_s(blob, r3) == 0.5)
    groups, types, order = key_groups()
    check("D5 key: 86, 10, 39", Counter(groups.values()) == Counter(GROUP_N))
    aq = [q for q in order if groups[q] == "answerable"]
    na = [q for q in order if groups[q] == "not_answerable"]

    def rec_(c, q, calls, decision=None, steps=(), text="one two three"):
        g = {"llm_calls": len(calls), "failed_calls": sum(1 for s, _ in calls if s not in ("ok", "length")),
             "calls": [{"status": s, "wall_s": w} for s, w in calls],
             "sum_call_wall_s": round(sum(w for _, w in calls), 3), "retrievals_bytes": [0, 0],
             "word_count": len(text.split()), "answer_wall_s": 1.0, "prompt_tokens": 1, "output_tokens": 1,
             "analysis": ({"decision": decision, "status": "switched_off"} if c == "orch_no_analyser" else
                          {"decision": decision}) if decision else None,
             "steps": [{"step_id": f"s{i}", "raw_content": "x" * k} for i, k in enumerate(steps)]}
        return {"answer_key": f"{INDEX}|{c}|{q}|d1", "run_id": run_of(c), "config": c, "question_id": q, "draw": 1,
                "answer_type": types[q], "generated_answer": text, "generation": g, "index_name": INDEX}
    data = {}
    for c in CONFIGS:
        R = []
        for i, q in enumerate(order):
            calls = [("ok", 1.0)]
            if c == FULL and i == 0:
                calls = [("ok", 1.0), ("blocked", 2.0), ("length", 0.5)]
            if c == FULL and i == 1:
                calls = [("malformed_response", 1.0), ("error", 1.0)]
            dec = None
            if c in ORCH:
                dec = "direct_answer" if (c == FULL and q in na[:5]) else "needs_plan"
            R.append(rec_(c, q, calls, dec, steps=(10, 300000) if (c == "orch_no_planner" and i == 0) else (10,),
                          text="" if (c == "naive_rag" and q == aq[1]) else "one two three"))
        data[c] = {"results": R}
    fn, q82 = compute(data, {}, groups, types, order, 209712)
    a = {r["config"]: r for r in fn["a"]}
    check("a: counts by kind", (a[FULL]["stopped_by_google"], a[FULL]["other_returned"],
                                a[FULL]["call_error"], a[FULL]["cut_at_length"],
                                a[FULL]["any_failed_call"]) == (1, 1, 1, 1, 2), str(a[FULL]))
    check("a: no text counted", a["naive_rag"]["no_text"] == 1 and a["raw_gemini"]["no_text"] == 0)
    fa = {x["answer_key"]: x for x in fn["answers"]}
    x0 = fa[f"{INDEX}|{FULL}|{order[0]}|d1"]
    check("calls by kind per answer", (x0["failed_calls"], x0["cut_calls"], x0["google_calls"]) == (1, 1, 1), str(x0))
    b = {(r["config"], r["group"]): r for r in fn["b"]}
    check("b: direct answers", b[(FULL, "not_answerable")]["direct_answer_n"] == 5
          and b[(FULL, "answerable")]["direct_answer_n"] == 0
          and abs(b[(FULL, "not_answerable")]["direct_answer_pct"] - 500 / 39) < 1e-9)
    check("f: Q82 count", q82["orch_no_planner"]["over_threshold"] == 1 and q82[FULL]["over_threshold"] == 0
          and q82["orch_no_planner"]["largest_chars"] == 300000)
    e = {r["config"]: r for r in fn["e"] if r["row"] == "setup"}
    check("e: own time = calls' wall_s (no search)", e[FULL]["maximum"] == 3.5)
    c_ = {r["config"]: r for r in fn["c"] if r["row"] == "setup"}
    check("c: words", c_["naive_rag"]["minimum"] == 0 and c_["raw_gemini"]["median"] == 3)
    check("analyser switched off is no analyser, its default decision not read",
          fn["analyser"] == {c: c in ORCH and c != "orch_no_analyser" for c in CONFIGS}
          and all(x["analyser_decision"] is None for x in fn["answers"] if x["config"] == "orch_no_analyser")
          and not any(r["config"] == "orch_no_analyser" for r in fn["b"]), str(fn["analyser"]))
    mix = json.loads(json.dumps(data))
    mix["orch_no_analyser"]["results"][0]["generation"]["analysis"]["status"] = "ok"
    refused("refuses an analyser switched off on some answers only",
            lambda: compute(mix, {}, groups, types, order, 209712), "switched off")
    # RLM-10's per-answer checks (rlm_answer), on one built answer and altered copies
    q0 = aq[0]
    key0 = f"{INDEX}|{RLM}|{q0}|d1"
    cell0 = {"kind": "scored", "score": 4, "key": key0}
    rec0 = {"status": "ok", "answer": "a b c d", "source": "x.jsonl:1", "cost": {"calls": 3}}
    raw0 = {"answer_key": key0, "generation": {"llm_calls": 3, "calls": [{"status": "ok"}, {"status": "length"},
                                                                         {"status": "error"}]}}
    try:
        c0, r0 = rlm_answer(q0, key0, cell0, rec0, raw0, groups)
        check("RLM-10 answer: words, calls, failed and cut by hand",
              (r0["words"], r0["model_calls"], r0["failed_calls"], r0["cut_calls"], r0["no_text"]) == (4, 3, 1, 1, 0),
              str(r0))
    except Refused as x:
        check("RLM-10 answer: words, calls, failed and cut by hand", False, str(x)[:200])
    c1, r1 = rlm_answer(q0, key0, {**cell0, "kind": "failed", "score": None},
                        {**rec0, "status": "error", "answer": ""}, raw0, groups)
    check("RLM-10 answer: no text is None words and a fail", r1["words"] is None and r1["no_text"] == 1
          and c1["kind"] == "failed")
    refused("RLM-10 answer: refuses a judge fail on an ok record",
            lambda: rlm_answer(q0, key0, {**cell0, "kind": "failed"}, rec0, raw0, groups), "record status")
    refused("RLM-10 answer: refuses a judge score on a failed record",
            lambda: rlm_answer(q0, key0, cell0, {**rec0, "status": "error"}, raw0, groups), "record status")
    refused("RLM-10 answer: refuses a raw line of another answer",
            lambda: rlm_answer(q0, key0, cell0, rec0, {**raw0, "answer_key": key0 + "x"}, groups), "holds")
    refused("RLM-10 answer: refuses llm_calls unequal to its calls",
            lambda: rlm_answer(q0, key0, cell0, rec0,
                               {**raw0, "generation": {**raw0["generation"], "llm_calls": 4}}, groups), "llm_calls")
    refused("RLM-10 answer: refuses an exp01_row count unequal to its calls",
            lambda: rlm_answer(q0, key0, cell0, {**rec0, "cost": {"calls": 2}}, raw0, groups), "exp01_row")
    refused("RLM-10 answer: refuses a status outside Rule 10's list",
            lambda: rlm_answer(q0, key0, cell0, {**rec0, "cost": {"calls": 1}},
                               {**raw0, "generation": {"llm_calls": 1, "calls": [{"status": "weird"}]}}, groups),
            "Rule 10")
    bad = {**data, "raw_gemini": {"results": data["raw_gemini"]["results"][1:]}}
    refused("refuses a draw 1 short of a question", lambda: compute(bad, {}, groups, types, order, 209712))
    odd = json.loads(json.dumps(data))
    odd["naive_rag"]["results"][0]["generation"]["calls"][0]["status"] = "weird"
    refused("refuses a status outside Rule 10's list", lambda: compute(odd, {}, groups, types, order, 209712))
    log = "\n".join(f"00:00:00 {c} stopped after draw 1 (draw-1 keys, later keys: 135 {1 if c == ORCH[0] else 0}; "
                    f"file quiet 1 s; pids 1 2)" for c in ORCH)
    try:
        reproduce(Path("/nonexistent"), data, q82, stop_log=log, plan_note="")
        check("reproduce refuses a disagreeing stop log", False)
    except Refused as x:
        check("reproduce refuses a disagreeing stop log", "stop log reads" in str(x) and "all three draws" in str(x))

    # the judge's rows: a synthetic G3 collect with its judging units
    kinds = {("naive_rag", aq[1]): "no_answer", ("orch_no_planner", aq[2]): "error"}
    with tempfile.TemporaryDirectory(prefix="S472_selftest_") as td:
        td = Path(td)

        def build(name, mutate=None, k=kinds):
            return fixture_g3(td / name, groups, order, k, mutate)
        try:
            g3 = read_g3_collect(build("ok"), groups)
            ok = True
        except Refused as x:
            g3, ok = None, False
            check("G3 collect: the fixture is read", False, str(x)[:300])
        if ok:
            cl = g3["cells"]
            check("G3 collect: 1,080 draw-1 cells, draw 2 counted apart",
                  len(cl) == 8 * 135 and g3["rows_other_draws"] == {2: 135}, f"{len(cl)} {g3['rows_other_draws']}")
            check("G3 collect: no_answer is failed, error unscored, ok scored",
                  cl[("naive_rag", aq[1], 1)]["kind"] == "failed"
                  and cl[("orch_no_planner", aq[2], 1)]["kind"] == "unscored"
                  and cl[(FULL, aq[0], 1)] == {**cl[(FULL, aq[0], 1)], "kind": "scored", "score": 5}
                  and cl[(FULL, na[0], 1)]["score"] == 3)
            check("G3 collect: the units checked", g3["units"] is not None and len(g3["units"]["folders"]) == 8)

        def two_runs(rows, side, out):
            rows[5]["run_sha256"] = "e" * 64
        refused("G3 collect refuses two run_sha256", lambda: read_g3_collect(build("runs", two_runs), groups),
                "run_sha256 values")

        def lock(rows, side, out):
            rows[7]["lock_sha256"] = "0" * 64
        refused("G3 collect refuses another lock", lambda: read_g3_collect(build("lock", lock), groups), "D88")

        def twice(rows, side, out):
            rows.append(dict(rows[0]))
        refused("G3 collect refuses a row twice", lambda: read_g3_collect(build("twice", twice), groups),
                "one row per answer")

        def prompt(rows, side, out):
            r = next(x for x in rows if groups[x["question_id"]] == "not_answerable")
            r["answerable_prompt"] = True
        refused("G3 collect refuses the wrong prompt", lambda: read_g3_collect(build("prompt", prompt), groups),
                "prompt")

        def missing(rows, side, out):
            del rows[[i for i, x in enumerate(rows) if x["config"] == "orch_no_analyser"][3]]
        refused("G3 collect refuses a missing draw-1 row", lambda: read_g3_collect(build("missing", missing), groups),
                "no judge row")

        def count(rows, side, out):
            side["rows_override"] = len(rows) + 1
        refused("G3 collect refuses a sidecar of another count",
                lambda: read_g3_collect(build("count", count), groups), "rows")

        def g1(rows, side, out):
            side["set"] = "G1"
        refused("G3 collect refuses a set other than G3", lambda: read_g3_collect(build("set", g1), groups), "set")

        def other(rows, side, out):
            rows[0]["config"] = "single_pass"
        refused("G3 collect refuses a row that is not a G3 answer",
                lambda: read_g3_collect(build("other", other), groups), "not a G3 answer")

        def recheck(rows, side, out):
            return False
        refused("G3 collect refuses a unit whose recheck differs (S463.check_units)",
                lambda: read_g3_collect(build("recheck", recheck), groups), "recheck")

        if ok:
            # the join, the statistics and the recount gate on built cells
            rlm = {"cells": {q: {"kind": "scored", "score": fixture_score(RLM, q, groups, order)} for q in order}}
            try:
                cells = join_judge(json.loads(json.dumps(fn)), g3, rlm, groups)
                check("join: every answer to its row", len(cells) == 9 * 135)
            except Refused as x:
                cells = None
                check("join: every answer to its row", False, str(x)[:200])
            wrong = json.loads(json.dumps(fn))
            next(x for x in wrong["answers"] if x["config"] == "naive_rag" and x["question_id"] == aq[1])["no_text"] = 0
            refused("join refuses a judge 'no_answer' on an answer with text",
                    lambda: join_judge(wrong, g3, rlm, groups), "judge failed")
            if cells:
                st = statistics(cells, groups, order)
                p4 = st["pass"][4]
                check("pass at 4: by hand (a failed answer a fail, an unscored row left out)",
                      (p4[FULL]["passed"], p4[FULL]["questions_with_share"], p4["raw_gemini"]["passed"],
                       p4["naive_rag"]["passed"], p4["naive_rag"]["questions_with_share"],
                       p4["orch_no_planner"]["passed"], p4["orch_no_planner"]["questions_with_share"],
                       p4[RLM]["passed"]) == (86, 86, 57, 56, 86, 56, 85, 86),
                      str({c: (v["passed"], v["questions_with_share"]) for c, v in p4.items()}))
                v = st["vs_full"][4]["orch_no_analyser"]
                check("minus the full pipeline: 29 lost, d = -29/86",
                      (v["a_higher"], v["b_higher"]) == (0, 29) and abs(v["d"] + 29 / 86) < 1e-12, str(v))
                check("refusal: by hand, a zero with its one-sided bound",
                      (st["refusal"][FULL]["refused"], st["refusal"]["orch_factual_to_documents"]["refused"],
                       st["refusal"]["raw_gemini"]["refused"]) == (1, 39, 0)
                      and abs(st["refusal"]["raw_gemini"]["zero_bound"] - (1 - 0.05 ** (1 / 39))) < 1e-12)
                check("refusal: 39 of 39 with its one-sided lower bound 0.05^(1/39) (O2); 1 of 39 and 0 of 39 none",
                      abs(st["refusal"]["orch_factual_to_documents"]["full_bound"] - 0.05 ** (1 / 39)) < 1e-12
                      and st["refusal"][FULL]["full_bound"] is None and st["refusal"]["raw_gemini"]["full_bound"] is None
                      and st["refusal"]["orch_factual_to_documents"]["zero_bound"] is None)
                check("false premise (D160 (11)): 5 of 10 at correctness 4, drawn; 10 of 10 at the relaxed 3",
                      all(st["false_premise"][c] == {"passed": 5, "n": 10}
                          and st["false_premise_relaxed"][c] == {"passed": 10, "n": 10} for c in NINE),
                      str({c: (st["false_premise"][c], st["false_premise_relaxed"][c]) for c in NINE}))
                check("false premise (D160 (11)): the recount names hold 5 at 4 and 10 at 3",
                      all(v["false_premise_pass_4"] == 5 and v["false_premise_pass_3"] == 10
                          for v in my_counts(st, fn, groups).values()))
                g_, keep = globals(), FP_T
                g_["FP_T"] = 3
                try:
                    legend_and_caption(None, None, 0, 0, None, "", {})
                    fp_guard = False
                except Refused:
                    fp_guard = True
                finally:
                    g_["FP_T"] = keep
                check("D160 (11): the legend's one threshold sentence (panels a and c) is refused when FP_T and "
                      "PASS_T differ", fp_guard)
                check("Holm on the five: monotone, at most 1",
                      all(st["vs_full"][4][c]["p_holm"] >= st["vs_full"][4][c]["p"] for c in FAMILY)
                      and all(st["vs_full"][4][c]["p_holm"] <= 1 for c in FAMILY))
                shas = {f"answers_json:{c}": f"{i:064x}" for i, c in enumerate(G3_ALL)}
                shas.update({k: f"{100 + i:064x}" for i, k in enumerate(
                    ("g3_collect", "g3_collect_sidecar", "g1_collect", "g1_collect_sidecar", "rlm_answers_jsonl",
                     "s6_g1_sums"))})
                recount = {"inputs": {k: {"path": k, "sha256": v} for k, v in shas.items()},
                           "counts": json.loads(json.dumps(my_counts(st, fn, groups)))}
                check("recount: the direct answers counted where the analyser is on only (5 for the full pipeline)",
                      recount["counts"][FULL]["not_answerable_direct_answer"] == 5
                      and recount["counts"]["orch_no_analyser"]["not_answerable_direct_answer"] is None
                      and recount["counts"][RLM]["not_answerable_direct_answer"] is None)
                try:
                    reproduce_recount(st, fn, groups, recount, shas)
                    check("recount: an equal recount passes", True)
                except Refused as x:
                    check("recount: an equal recount passes", False, str(x)[:200])
                r2 = json.loads(json.dumps(recount))
                r2["counts"]["naive_rag"]["not_answerable_refused_3"] += 1
                refused("recount: one count changed is refused, naming the set-up and the count",
                        lambda: reproduce_recount(st, fn, groups, r2, shas), "naive RAG not_answerable_refused_3")
                r3 = json.loads(json.dumps(recount))
                r3["inputs"]["g1_collect_sidecar"]["sha256"] = "0" * 64
                refused("recount: one input sha256 changed is refused (made from other files)",
                        lambda: reproduce_recount(st, fn, groups, r3, shas), "recount made from other files")
                r4 = json.loads(json.dumps(recount))
                del r4["inputs"]["answers_json:raw_gemini"]
                refused("recount: an input missing from the recount is refused (made from other files)",
                        lambda: reproduce_recount(st, fn, groups, r4, shas), "recount made from other files")
                r5 = {**recount, "counts_v24": recount["counts"]}
                try:
                    reproduce_recount(st, fn, groups, r5, shas, key="counts_v24")
                    check("recount (D188): counts_v24 compared when asked", True)
                except Refused as x:
                    check("recount (D188): counts_v24 compared when asked", False, str(x)[:200])
                refused("recount (D188): a recount without counts_v24 (S480 before D188) is refused",
                        lambda: reproduce_recount(st, fn, groups, recount, shas, key="counts_v24"),
                        "holds no 'counts_v24'")
                rec_sha = {"provenance": {"script_sha256": "a" * 64}}
                check("recount (D136 Q12): the S480 sha256 at HEAD passes",
                      check_recount_script(rec_sha, "a" * 64)["equal_to"] == "HEAD")
                refused("recount (D136 Q12): a recount written by another S480 is refused",
                        lambda: check_recount_script(rec_sha, "b" * 64), "run scripts/S480_fig4_recount.py first")
                check("draw_counts: absent on both sides passes", check_draw_counts(None, {}) is None)
                dr_ = [{"config": FULL, "draw": 1, "threshold": 4, "passed": 3, "questions": 29}]
                check("draw_counts: equal counts pass",
                      check_draw_counts(dr_, {"draw_counts": {f"{FULL}|1|4": [3, 29]}})["rows"] == 1)
                refused("draw_counts: a count that differs is refused",
                        lambda: check_draw_counts(dr_, {"draw_counts": {f"{FULL}|1|4": [4, 29]}}), "draw")
                refused("draw_counts: rows the recount does not hold are refused",
                        lambda: check_draw_counts(dr_, {}), "draw")
            # D188: merge_g3 on a built choice (judge_rows_v25.choose's entries): one v2.5 row, one awaiting S6
            ch = {(run_of(c_), c_, q_, d_): {"status": "v2.4", "row": {"item_sha256": v_["item_sha256"]}}
                  for (c_, q_, d_), v_ in g3["cells"].items()}
            k1, k2 = (FULL, aq[0], 1), (FULL, aq[3], 1)
            r25 = {"answer_key": g3["cells"][k1]["key"], "answerable_prompt": True, "item_sha256": "v25",
                   "a": {"status": "ok", "scores": {"correctness": 1}}}
            ch[(run_of(FULL), FULL, aq[0], 1)] = {"status": "v2.5", "row": r25}
            ch[(run_of(FULL), FULL, aq[3], 1)]["status"] = "v2.4 awaiting S6"
            try:
                mg, nm = merge_g3(g3["cells"], ch, groups)
                check("merge_g3 (D188): the v2.5 row's cell (score 1, key v2.5), the others the v2.4 cells; 1 from "
                      "v2.5, 1 awaiting S6",
                      mg[k1]["kind"] == "scored" and mg[k1]["score"] == 1 and mg[k1]["key_version"] == "v2.5"
                      and mg[k2] == g3["cells"][k2] and all(mg[k] == g3["cells"][k] for k in mg if k != k1)
                      and nm == {"cells_from_v25": 1, "awaiting_s6": 1}, str(nm))
            except Refused as x:
                check("merge_g3 (D188): the v2.5 row's cell", False, str(x)[:200])
            na_k = (FULL, na[0], 1)
            for name, edit, want in (
                    ("a v2.5 row judged with the other group's prompt",
                     lambda c: c.__setitem__((run_of(FULL), FULL, na[0], 1), {"status": "v2.5", "row": {
                         "answer_key": g3["cells"][na_k]["key"], "answerable_prompt": True,
                         "a": {"status": "ok", "scores": {"refusal_accuracy": 5}}}}), "prompt"),
                    ("a v2.4 row that is not the collect's row read",
                     lambda c: c[(run_of(FULL), FULL, aq[1], 1)].__setitem__("row", {"item_sha256": "other"}),
                     "not the collect's row"),
                    ("an answer with no row chosen",
                     lambda c: c.__setitem__((run_of(FULL), FULL, aq[2], 1), {"status": "not judged", "row": None}),
                     "no judge row chosen"),
                    ("an answer missing from the choice", lambda c: c.pop((run_of(FULL), FULL, aq[2], 1)),
                     "no entry in the choice")):
                bad_ch = {k: dict(v) for k, v in ch.items()}
                edit(bad_ch)
                refused(f"merge_g3 (D188) refuses {name}", lambda: merge_g3(g3["cells"], bad_ch, groups), want)
        selftest_stress(check, refused, td, data, groups, types, order, rec_)
    # b's false-premise tiles read back by check_drawn (D250): outlined exactly where the sheet's fp_pass is 1
    fb, zb = 0.05 ** (1 / 39), 1 - 0.05 ** (1 / 39)
    rows_c = [{"row": "setup", "config": "naive_rag", "refused": 39, "questions": 39, "refusal_rate": 1.0,
               "zero_bound_one_sided": None, "full_bound_one_sided": fb, "interval_low": 1.0, "interval_high": 1.0},
              {"row": "setup", "config": "raw_gemini", "refused": 0, "questions": 39, "refusal_rate": 0.0,
               "zero_bound_one_sided": zb, "full_bound_one_sided": None, "interval_low": 0.0, "interval_high": 0.0},
              {"row": "setup", "config": FULL, "refused": 2, "questions": 39, "refusal_rate": 2 / 39,
               "zero_bound_one_sided": None, "full_bound_one_sided": None, "interval_low": 0.0,
               "interval_high": 5 / 39}]
    fp_rows = [{"row": "fp_tile", "config": "naive_rag", "question_id": "FP_1", "column": 1, "fp_pass": 1},
               {"row": "fp_tile", "config": "naive_rag", "question_id": "FP_2", "column": 2, "fp_pass": 0}]

    def fp_tiles(tiles):
        rb_ = {k: [] for k in ("a_tile", "a_rate", "box", "c_tile", "d_n")}
        rb_["fp_tile"] = tiles
        return [x for x in check_drawn(rb_, {"sheets": {"c": rows_c + fp_rows}, "judged": ["naive_rag"]})[0]
                if "false-premise" in x]
    ok_tiles = [("naive_rag", "FP_1", FP_PASS, 1, 1, 1), ("naive_rag", "FP_2", None, 0, 2, 2)]
    check("b: false-premise tiles outlined exactly where the sheet passes: no problem", not fp_tiles(ok_tiles),
          str(fp_tiles(ok_tiles)))
    for name, tiles in (("a pass drawn without its outline", [("naive_rag", "FP_1", None, 1, 1, 1), ok_tiles[1]]),
                        ("a fail drawn outlined", [ok_tiles[0], ("naive_rag", "FP_2", FP_PASS, 0, 2, 2)]),
                        ("a tile missing", ok_tiles[:1]),
                        ("a tile out of the sheet's column", [ok_tiles[0], ("naive_rag", "FP_2", None, 0, 2, 3)])):
        check(f"b: check_drawn flags {name}", len(fp_tiles(tiles)) == 1, str(fp_tiles(tiles)))
    check("claims: a 100% with its lower bound, a 0 with its upper bound, another rate with none",
          [refused_of(r) for r in rows_c] == ["39 of 39 (one-sided 95% lower bound 92.6%)",
                                               "0 of 39 (one-sided 95% upper bound 7.4%)", "2 of 39"],
          str([refused_of(r) for r in rows_c]))
    check("holm by hand", holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06},
          str(holm({"a": 0.01, "b": 0.04, "c": 0.03})))
    check("tile levels", [p_level(x) for x in ({"kind": "scored", "score": 5}, {"kind": "scored", "score": 3},
                                                {"kind": "scored", "score": 2}, {"kind": "failed"},
                                                {"kind": "unscored"})] == [0, 1, 2, 2, None])
    check("flip (D171 (1)): a's 4 or 5 at the light end, 2 or less at the dark end, 3 between; c's refused light",
          [v for _, v in LEVELS] == [1.0, 0.5, 0.0] and (YES_POS, NO_POS) == (1.0, 0.0))
    check("third gap: rows of a set apart above the full pipeline, the stress set-ups and RLM-10, and nowhere else",
          [c for c, b in zip(ALL[1:], ALL) if abs(p_ypos(c) - p_ypos(b) - 1) > 1e-9] == [FULL, STRESS[0], RLM])
    selftest_d155(check, refused)
    k = sum(res)
    print(f"selftest: {k} of {len(res)} checks pass")
    return k == len(res)


def selftest_stress(check, refused, td: Path, data: dict, groups: dict, types: dict, order: list, rec_):
    """The stress set-ups through the join, the statistics and the sheets, on built rows; vs_full_text; draw rows."""
    na = [q for q in order if groups[q] == "not_answerable"]
    aq = [q for q in order if groups[q] == "answerable"]
    data11 = {**data, **{c: {"results": [rec_(c, q, [("ok", 1.0)], "needs_plan", steps=(10,)) for q in order]}
                         for c in STRESS}}
    fn, q82 = compute(data11, {}, groups, types, order, 209712, setups=G3_ALL)
    check("stress: compute holds 10 x 135 answers, no own time without retrievals, no step row in f or q82",
          len(fn["answers"]) == 1350 and all(x["own_time_s"] is None for x in fn["answers"] if x["config"] in STRESS)
          and not any(x["config"] in STRESS for x in fn["f"]) and not set(STRESS) & set(q82)
          and fn["stress_steps"][STRESS[0]] == {"not_asked": 135})
    kinds = {("naive_rag", aq[1]): "no_answer"}          # the record of that answer holds no text (selftest's data)
    g3s = read_g3_collect(fixture_g3(td / "stress", groups, order, kinds, setups=G3_ALL), groups, need_stress=True)
    check("stress: the collect's rows read, 1,350 draw-1 cells", g3s["stress_judged"] and len(g3s["cells"]) == 1350)
    g3n = read_g3_collect(fixture_g3(td / "nostress", groups, order, kinds), groups)
    check("stress: a collect with no row of theirs reads as not judged", not g3n["stress_judged"])
    refused("stress: a collect that must hold them and does not is refused",
            lambda: read_g3_collect(fixture_g3(td / "must", groups, order, kinds), groups, need_stress=True),
            "no judge row")

    def part(rows, side, out):
        del rows[[i for i, x in enumerate(rows) if x["config"] == STRESS[1]][3]]
    refused("stress: a missing draw-1 row of G9 is refused",
            lambda: read_g3_collect(fixture_g3(td / "part", groups, order, kinds, part, setups=G3_ALL), groups),
            "no judge row")
    row = {"setup": LABEL[RLM], "config": RLM, "group": "", "answer_key": "", "words": 3, "no_text": 0, "model_calls": 2,
           "failed_calls": 0, "cut_calls": 0, "google_calls": 0, "other_returned_calls": 0, "call_error_calls": 0,
           "call_statuses": "ok 2", "own_time_s": None, "analyser_decision": None, "record": "x"}
    rlm = {"cells": {q: {"kind": "scored", "score": fixture_score(RLM, q, groups, order)} for q in order},
           "rows": {q: {**row, "question_id": q, "group": groups[q]} for q in order}}
    cells = join_judge(fn, g3s, rlm, groups)
    check("stress: the join holds 11 x 135 cells", len(cells) == 11 * 135)
    st = statistics(cells, groups, order)
    v = st["vs_full"][4]
    check("stress: Holm stays over five; a stress set-up has a difference and no Holm P",
          sorted(c for c in v if "p_holm" in v[c]) == sorted(FAMILY) and "d" in v[STRESS[0]]
          and "p_holm" not in v[STRESS[1]])
    cells_d = {**cells, (FULL, aq[0], 2): {"kind": "failed"}, (FULL, aq[1], 2): {"kind": "unscored"}}
    draws = draw_rows(cells_d, groups, list(aq[:29]))
    check("'draw' rows: 11 set-ups x 3 draws x 2 thresholds, a fail counted, an unscored row and no row left out",
          len(draws) == 66 and next(r for r in draws if (r["config"], r["draw"], r["threshold"]) == (FULL, 2, 4))
          == {"row": "draw", "setup": LABEL[FULL], "config": FULL, "role": role(FULL), "draw": 2, "threshold": 4,
              "passed": 0, "questions": 1}, str(len(draws)))
    P = panel_rows(fn, q82, st, cells, rlm, groups, order, 209712, draws=draws)
    S = P["sheets"]
    kinds = {L: Counter(r["row"] for r in S[L]) for L in S}
    check("sheets: a 22 setup, 946 tile, 66 draw", kinds["a"] == {"setup": 22, "tile": 946, "draw": 66}, str(kinds["a"]))
    check("sheets: c 11 setup, 429 tile, 110 fp_tile", kinds["c"] == {"setup": 11, "tile": 429, "fp_tile": 110},
          str(kinds["c"]))
    check("sheets: d 2 x 11 setup, 2 total (calls, time), 1,485 answer rows each holding both; no sheet f (D219); "
          "e empty with no G17 given",
          kinds["d"] == {"setup": 22, "total": 2, "answer": 1485} and sorted(S) == list("abcdef") and S["e"] == []
          and S["f"] == []
          and all("model_calls" in r and "own_time_s" in r for r in S["d"] if r["row"] == "answer"),
          str(kinds["d"]))
    check("sheets: b filters to the six orchestrator set-ups", {r["config"] for r in S["b"] if r["row"] == "setup"} ==
          set(ORCH))
    tot = {m_: next(r for r in S["d"] if r["row"] == "total" and r["measure"] == m_) for _, m_ in D_MEASURES}
    tc, tt = (tot[m_] for _, m_ in D_MEASURES)
    check("totals: model calls 1,485 answers in 11 set-ups; own time the 8 G3 set-ups with a time, 1,080 of 1,485",
          (tc["n"], tc["set_ups"]) == (1485, 11) and (tt["answers"], tt["n"], tt["set_ups"]) == (1485, 1080, 8)
          and "failed_calls" in next(r for r in S["d"] if r["row"] == "setup" and r["measure"] == D_MEASURES[0][1])
          and next(r for r in S["d"] if r["row"] == "setup" and r["measure"] == D_MEASURES[1][1]
                   and r["config"] == RLM)["note"] == NO_TIME, str(tot))
    # d, e (sheets e, f; D250): G17 read from the committed d123 reading and S576, S576's numbers reproduced
    g17 = read_g17()
    e_rows, f_rows = g17_sheets(g17)
    ek, fk = Counter(r["row"] for r in e_rows), Counter(r["row"] for r in f_rows)
    check("d: 8 'box' rows (4 arms x 2 question types), 4 x 86 'question' rows, one 'difference' row per S576 part",
          ek == {"box": 8, "question": 344, "difference": len(g17["parts"])}, str(ek))
    check("e: 16 'box' rows (2 measures x 4 arms x 2 question types), 4 x 86 draw-1 'answer' rows",
          fk == {"box": 16, "answer": 344}, str(fk))
    q0 = next(r for r in e_rows if r["row"] == "question" and r["arm_key"] == "gate_off")
    check("d: a question's concept recall is the mean of its three draws, in %",
          abs(q0["concept_recall_mean"] - sum(q0[f"concept_recall_draw_{k}"] for k in G17_DRAWS) / 3) < 1e-9)
    b0 = next(r for r in e_rows if r["row"] == "box" and (r["arm_key"], r["group_key"]) == ("gate_off", "one"))
    v0 = sorted(r["concept_recall_mean"] for r in e_rows if r["row"] == "question" and r["arm_key"] == "gate_off"
                and r["group_key"] == "one")
    check("d: a box's n, range and median from its 60 question rows",
          (b0["n"], b0["minimum"], b0["maximum"]) == (60, v0[0], v0[-1])
          and abs(b0["median"] - (v0[29] + v0[30]) / 2) < 1e-9, str(b0))
    pkg = sum(100 * r["cr"] for r in g17["means"]["package"].values()) / 86
    want_pkg = 100 * json.loads(G17_S576.read_text())["arm_means"]["draws_1_3"]["package"]["all"]["concept_recall"]
    check("d: the package's mean of question means equals S576's arm mean (draws 1 to 3)", abs(pkg - want_pkg) < 1e-9)
    tf_, inv_ = g17_tf()
    check("e: the axis transform is linear to 2 and returns every tick through its inverse",
          abs(tf_(1) - 1 / 2 * tf_(2)) < 1e-9 and all(abs(inv_(tf_(t)) - t) < 1e-9 for t in G17_F_TICKS))
    alt = td / "s576_altered.json"
    doc_ = json.loads(G17_S576.read_text())
    doc_["descriptive_draws_1_3"]["H1"]["parts"][0]["diff"] += 0.01
    alt.write_text(json.dumps(doc_))
    refused("d: an S576 difference that S576.evaluate() does not give again is refused",
            lambda: read_g17(s576_json=alt), "are not what S576.evaluate() gives")
    doc_ = json.loads(G17_S576.read_text())
    doc_["_provenance"]["inputs_sha256"] = {k: ("0" * 64 if k.endswith("g17_reading.json") else v)
                                            for k, v in doc_["_provenance"]["inputs_sha256"].items()}
    alt.write_text(json.dumps(doc_))
    refused("d: differences made from another reading are refused", lambda: read_g17(s576_json=alt),
            "S576's paired differences were made from")
    a4 = {r["config"]: r for r in S["a"] if r["row"] == "setup" and r["threshold"] == 4}
    check("sheet a: no P on the stress set-ups or the baselines; a difference on stress, none on the baselines",
          all(a4[c]["p_sign_flip"] is None and a4[c]["p_drawn"] is None and a4[c]["minus_full"] is not None
              for c in STRESS)
          and all(a4[c]["p_drawn"] is None and a4[c]["minus_full"] is None for c in BASELINES))
    rows = [{"row": "setup", "threshold": 4, "setup": LABEL[c], "questions": 86, "p_drawn": p, "minus_full": d,
             "minus_full_low": lo, "minus_full_high": hi}
            for c, p, d, lo, hi in ((ORCH[1], 0.6, 0.01, -0.1, 0.12), (RLM, 0.2, -0.02, -0.15, 0.05))]
    txt = vs_full_text({"a": rows})
    check("vs_full_text: the test named, no outcome stated (S3, 7 Nov)",
          txt.startswith("Each set-up minus the full pipeline") and "two-sided" in txt and "alpha 0.05" in txt
          and "n = 86" in txt and "Source Data" in txt and "detected" not in txt and "\u221215.0" not in txt, txt)
    rows[1].update(p_drawn=0.01, minus_full_low=-0.15, minus_full_high=-0.01)
    check("vs_full_text: the same words whatever the outcome", vs_full_text({"a": rows}) == txt)
    rows[1]["questions"] = 85
    refused("vs_full_text: set-ups of different n are refused", lambda: vs_full_text({"a": rows}), "questions")
    g7 = set(ORCH + STRESS)
    keep = lambda **k: draw_rows_keep({"question_id": aq[0], **k}, aq, g7)    # noqa: E731
    check("draw_rows_keep: draws 2 and 3 of a G7 set-up from S6G7G3's rows only; N19's rows set aside; baselines kept",
          keep(config=FULL, draw=2, a={}, questions="all") and not keep(config=FULL, draw=2, a={})
          and not keep(config="orch_no_supervisor", draw=2, a={}, key_version="v2.5")
          and keep(config=FULL, draw=1, a={}) and keep(config="naive_rag", draw=3, a={})
          and keep(config=FULL, draw=2) and not keep(config=RLM, draw=1)
          and not draw_rows_keep({"config": FULL, "question_id": na[0], "draw": 1}, aq, g7))
    frozen = FR.frozen(*FROZEN_RIGHT)
    st9 = statistics({k: v for k, v in cells.items() if k[0] in NINE}, groups, order)
    done = reproduce_new(frozen, st9, cells, groups, order, frozen)
    check("reproduce_new: the frozen collect 41d3105d in itself; no stress rows, nothing to compare",
          done["frozen_collect_rows_equal"] == done["collect_rows"] and "no stress" in done["nine_with_and_without_stress"])
    done = reproduce_new(frozen, st, cells, groups, order, frozen)
    check("reproduce_new: the nine set-ups' statistics equal with and without the stress set-ups",
          done["nine_with_and_without_stress"] == "equal", str(done))
    moved = td / "moved.jsonl"
    lines = frozen.read_text().splitlines()
    moved.write_text("\n".join(lines[1:]) + "\n")
    refused("reproduce_new: a row of 41d3105d missing from the collect read is refused",
            lambda: reproduce_new(moved, st9, cells, groups, order, frozen), "differ or are gone")
    refused("reproduce_new: another file as the frozen collect is refused",
            lambda: reproduce_new(frozen, st9, cells, groups, order, moved), "is not the frozen collect")
    g9 = td / "g9"
    pj = {"files": {}}
    for c in STRESS:
        f = g9 / "runs" / run_of(c) / "answers.json"
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({"results": [{"answer_key": "k", "run_id": run_of(c), "config": c, "index_name": INDEX}],
                                 "completed_keys": ["k"]}))
        pj["files"][f"runs/{run_of(c)}/answers.json"] = {"sha256": sha256_file(f)}
    (g9 / "PULL.json").write_text(json.dumps(pj))
    check("read_g9: both answers.json against PULL.json", list(read_g9(g9)[0]) == STRESS)
    refused("read_g9: no retrievals.jsonl for a set-up in the folder given", lambda: read_g9(g9, g9), "no retrievals")
    (g9 / "runs" / run_of(STRESS[0]) / "answers.json").write_text("{}")
    refused("read_g9: a file that is not PULL.json's is refused", lambda: read_g9(g9), "not the file PULL.json lists")


def selftest_d155(check, refused):
    """D155's checks on built files: the git-free HEAD read, the collect view, the frozen-set and pin checks, the
    sidecar comparison of pull-judge's reproduction."""
    with tempfile.TemporaryDirectory(prefix="S472_d155_") as td:
        t = Path(td)
        # HEAD_SH on built .git layouts (a loose ref, packed-refs, a worktree with commondir, detached, none)
        h1, h2, h3 = "1" * 40, "2" * 40, "3" * 40
        lay = {"loose": {".git/HEAD": "ref: refs/heads/main\n", ".git/refs/heads/main": h1 + "\n"},
               "packed": {".git/HEAD": "ref: refs/heads/main\n", ".git/packed-refs": f"# pack\n{h2} refs/heads/main\n"},
               "worktree": {".git": "gitdir: ../main/.git/worktrees/wt\n",
                            "../main/.git/worktrees/wt/HEAD": "ref: refs/heads/side\n",
                            "../main/.git/worktrees/wt/commondir": "../..\n",
                            "../main/.git/refs/heads/side": h3 + "\n"},
               "detached": {".git/HEAD": h2 + "\n"},
               "no ref": {".git/HEAD": "ref: refs/heads/gone\n"}}
        want = {"loose": h1, "packed": h2, "worktree": h3, "detached": h2, "no ref": "unknown"}
        got = {}
        for name, files in lay.items():
            d = t / "heads" / name.replace(" ", "_") / "wt"
            for f, txt in files.items():
                p = (d / f).resolve()
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(txt)
            r = subprocess.run(["bash", "-c", HEAD_SH + "head_of"], cwd=d, capture_output=True, text=True)
            got[name] = r.stdout.strip()
        check("D155 HEAD_SH: a loose ref, packed-refs, a worktree's commondir, a detached HEAD, a missing ref",
              got == want, str(got))
        check("D155 the pull scripts run no git command", "git " not in LIST_SH.replace("/.git", "")
              and "git " not in JLIST_SH.replace("/.git", "") and "rev-parse" not in LIST_SH + JLIST_SH)
        # collect_view: a collect copied away from where it ran, its folders beside it
        old = "/old/session/scratchpad/pull"
        here = t / "copy"
        for f in ("out/judge/r1", "out_g1r15/judge/r2"):
            (here / f).mkdir(parents=True)
        (here / "c.jsonl").write_text("{}\n")
        side = {"_provenance": {"script": "s3_guard.py collect", "at": "2026-10-23T09:41:17",
                                "inputs": [f"{old}/out", f"{old}/out_g1r15"]}, "rows": 1, "set": "G1",
                "from": {f"{old}/out/judge/r1/judge_passages.jsonl": 3, f"{old}/out_g1r15/judge/r2/judge_passages.jsonl": 1}}
        (here / "c.jsonl.json").write_text(json.dumps(side))
        v = collect_view(here / "c.jsonl", t / "view1")
        vs = json.loads(v.with_name(v.name + ".json").read_text())
        check("D155 collect_view: the folders named beside the copy, the rest of the sidecar unchanged",
              v != here / "c.jsonl" and v.resolve() == (here / "c.jsonl").resolve()
              and vs["_provenance"]["inputs"] == [str(here.resolve() / "out"), str(here.resolve() / "out_g1r15")]
              and vs["from"] == {f"{here.resolve()}/out/judge/r1/judge_passages.jsonl": 3,
                                 f"{here.resolve()}/out_g1r15/judge/r2/judge_passages.jsonl": 1}
              and {k: x for k, x in vs.items() if k not in ("_provenance", "from")}
              == {k: x for k, x in side.items() if k not in ("_provenance", "from")}
              and vs["_provenance"]["at"] == side["_provenance"]["at"], json.dumps(vs)[:300])
        (here / "c.jsonl.json").write_text(json.dumps({**side, "_provenance": {
            **side["_provenance"], "inputs": [str(here.resolve() / "out"), str(here.resolve() / "out_g1r15")]}}))
        check("D155 collect_view: a collect whose folders are already beside it is read as it is",
              collect_view(here / "c.jsonl", t / "view2") == here / "c.jsonl")
        for name, alt, want_msg in (
                ("folders in two places", {"_provenance": {"inputs": [f"{old}/out", "/elsewhere/out_g1r15"]}},
                 "sit in 2 folders"),
                ("a from key under none of them", {"from": {"/elsewhere/judge/x.jsonl": 1}}, "under none"),
                ("a folder missing beside the copy", {"_provenance": {"inputs": [f"{old}/out", f"{old}/out_g6"]}},
                 "is not beside")):
            (here / "c.jsonl.json").write_text(json.dumps({**side, **alt}))
            refused(f"D155 collect_view refuses {name}",
                    lambda: collect_view(here / "c.jsonl", t / f"view_{name.replace(' ', '_')}"), want_msg)
        # check_committed: the freeze's SHA256SUMS against a committed set, file by file
        base = t / "repo"
        st = base / "findings" / "recompute" / "x_inputs"
        (st / "sub").mkdir(parents=True)
        (st / "a.txt").write_text("a\n")
        (st / "sub" / "b.txt").write_text("b\n")
        sums = {f"findings/recompute/x_inputs/{n}": sha256_file(st / n) for n in ("a.txt", "sub/b.txt")}
        check("D155 check_committed: every file equal to its line", len(check_committed(st, sums, base)) == 2)
        (st / "sub" / "b.txt").write_text("changed\n")
        refused("D155 check_committed refuses a changed file", lambda: check_committed(st, sums, base), "differs")
        (st / "sub" / "b.txt").write_text("b\n")
        (st / "extra.txt").write_text("x\n")
        refused("D155 check_committed refuses a file the sums do not list", lambda: check_committed(st, sums, base),
                "a file added")
        (st / "extra.txt").unlink()
        (st / "a.txt").unlink()
        refused("D155 check_committed refuses a missing file", lambda: check_committed(st, sums, base), "missing")
        # check_pins: a pinned frozen file with another sha256 is refused
        fz = lambda s, r=".": st / r                                     # noqa: E731
        pins = {("x", "sub/b.txt"): sha256_file(st / "sub" / "b.txt")}
        check("D155 check_pins: a pinned file equal to its pin", list(check_pins(pins, fz)) == ["x:sub/b.txt"])
        refused("D155 check_pins refuses a frozen input whose sha256 is not the plate's",
                lambda: check_pins({("x", "sub/b.txt"): "0" * 64}, fz), "the committed plate recorded")
        # side_core: pull-judge's reproduction compares sidecars less where and when collect ran
        s2 = {**side, "_provenance": {"inputs": ["/new/out", "/new/out_g1r15"], "at": "2026-11-01T00:00:00"},
              "from": {"/new/out/judge/r1/judge_passages.jsonl": 3, "/new/out_g1r15/judge/r2/judge_passages.jsonl": 1}}
        check("D155 side_core: two collects of the same folders elsewhere and later are equal",
              side_core(side) == side_core(s2))
        check("D155 side_core: a row count changed is not equal", side_core(side) != side_core({**s2, "rows": 2}))
        refused("D155 refuse_frozen_dest: never pull into a frozen set",
                lambda: refuse_frozen_dest(ROOT / "findings" / "recompute" / "fig4_inputs" / "new"), "frozen input set")
        # audit 27 Oct F1: a design document is read at the pinned commit, not at a later HEAD; distiller_firing.py
        # may change its docstring, not its code
        repo = t / "pin"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)   # noqa: E731
        g("init", "-q")
        (repo / "plan.csv").write_text("G3,raw_gemini and naive_rag hold all three draws\n")
        g("add", "plan.csv")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c1")
        c1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
        (repo / "plan.csv").write_text("G3,running\n")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "c2")
        check("F1 design_bytes: a design document is read at the pinned commit, not at a later HEAD",
              b"all three draws" in design_bytes(repo / "plan.csv", c1, repo))
        src = '"""Q82."""\nT = 0.40\n\n\ndef count(p):\n    return int(T * 131072) * 4\n'
        check("F1 distiller_moved: a docstring-only change passes",
              not distiller_moved(src.replace("Q82.", "Q82, int(0.40 x num_ctx) x 4."), src))
        check("F1 distiller_moved: a code change is refused", distiller_moved(src.replace("0.40", "0.50"), src))
        # audit 27 Oct F1, part 4: the checks read the working tree; a drawn value must equal DESIGN_AT's
        (repo / "plan.csv").write_text("G3,raw_gemini and naive_rag hold all three draws, edited\n")
        check("F1 plan_g3_note reads plan.csv as it stands, not at DESIGN_AT",
              plan_g3_note(repo / "plan.csv").endswith("edited"))
        ex3 = 'X = 1\nSTRESS_CONFIG_NAMES = ["orch_distil_every_step", "orch_distil_every_step_f1"]\n'
        check("F1 stress_drawn: equal at DESIGN_AT passes", stress_drawn(ex3, ex3.replace("X = 1", "X = 2")) ==
              ["orch_distil_every_step", "orch_distil_every_step_f1"])
        refused("F1 stress_drawn: a stress set-up changed since DESIGN_AT is refused",
                lambda: stress_drawn(ex3.replace(', "orch_distil_every_step_f1"', ""), ex3), "move DESIGN_AT")
        import inspect
        check("F1 claims_md reads each document as it stands (no design_bytes in it)",
              "design_bytes" not in inspect.getsource(claims_md))


def main(argv=None):
    ap = argparse.ArgumentParser(description=f"Figure {FIG_N}'s provisional plate from G3's records, S3's judge rows and "
                                             "RLM-10's (no model call)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--to", required=True)
    p.add_argument("--g9-retrievals", action="store_true", help="G9's two retrievals.jsonl only (fig4.md section 4)")
    j = sub.add_parser("pull-judge", help="G3's judge out from the S3 clone, then s3_guard.py collect (D155 A6)")
    j.add_argument("--to", required=True, help="a new or empty folder (never findings/runs or a frozen set)")
    j.add_argument("--from-copy", help="offline: a local out_g3 folder instead of the Studio (no ssh)")
    f = sub.add_parser("figure")
    f.add_argument("--records", help="the folder S472 pull wrote; default the frozen copy (fig4_records_1023.tar)")
    f.add_argument("--collect", help="s3_guard.py collect output of set G3 (its .json sidecar beside it); default "
                                     "the frozen findings/recompute/fig4_g9_inputs/g3_collect.jsonl (G9 judged)")
    f.add_argument("--rlm-collect", help="s3_guard.py collect output of set G1 (RLM-10's judge rows); default the "
                                         "frozen findings/recompute/fig2_inputs/g1_collect.jsonl")
    f.add_argument("--rlm-answers",
                   help="a runs folder holding exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl, MANIFEST.sha256 beside it; "
                        "default the frozen copy (fig2_g1r15_inputs.tar)")
    f.add_argument("--g9", help="G9's answers (runs/<run>/answers.json, PULL.json); default the frozen "
                                "findings/recompute/g9_inputs")
    f.add_argument("--g9-retrievals", help="a folder holding <run>/retrievals.jsonl of G9's two set-ups; default the "
                                           "frozen findings/recompute/fig4_g9_inputs/g9_retrievals/findings/runs")
    f.add_argument("--s6-g1", help="the folder holding out_s6_g1 and out_s6_g1r15, RLM-10's key v2.5 rows; default the "
                                   "frozen findings/recompute/fig3_s6_inputs (S528)")
    f.add_argument("--recount", default=str(RECOUNT),
                   help="S480's recount (scripts/S480_fig4_recount.py), made from the same files; default "
                        "findings/recompute/S480_fig4_recount.json")
    f.add_argument("--out", default=str(OUT), help="the plate's folder; default findings/figures_provisional/fig4")
    f.add_argument("--steps-out", default=str(STEPS_OUT),
                   help="old panel 4b's rows for Supplementary Figure 10a (D250); default " + rel(STEPS_OUT))
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    if args.cmd == "pull":
        pull(args)
    elif args.cmd == "pull-judge":
        pull_judge(args)
    elif args.cmd == "figure":
        figure(args)
    else:
        sys.exit(0 if selftest() else 1)


if __name__ == "__main__":
    main()
