#!/usr/bin/env python3
"""S456 - plan row A0 (D82): Figure 1's provisional plate, panels a (the signals) and b (the design; D307), read
from the design files.

WHY. Figure 1 shows no data: what the study varies, by pipeline stage, and how each result is measured. The submitted
plate (manuscript/submission/figures/Figure_1.svg, scripts/S162_figure1_final.py) fails the figure lock (D87): its body
type is 2.12 mm = 6 pt (S162:94) against FIGURE_LOCK.toml [type] font_min_pt 8, and its JUDGE row still names
qwen3-coder:30b / gpt-oss:120b (S162:132; experiments/LIST.md "Figure 1"). D33 adds a code-generation row under
GENERATE (11 strategies, the models of Figure 6) and updates the JUDGE row; D85 makes the judges devstral-small-2:24b
(main) and qwen3.8:27b (second); Q164 (D83) has every numeral read from the files that define the design, so a
design change moves the plate instead of slipping past a typed copy.

    uv run --frozen python scripts/S456_fig1_design.py figure
    uv run --frozen python scripts/S456_fig1_design.py selftest     the checks below, on throwaway copies

writes into findings/figures_provisional/fig1/ (files of an earlier state, "Figure 1*" and "Source Data Fig. 1*",
deleted first):
  Figure 1 (provisional, 2 of 2).{pdf,svg,png}   D307 (Valerio, 8 Nov): the design of Figure 1 alt2
                         (findings/recompute/fig1_alt_drafts/draw_fig1_alt2.py), drawn here from this script's own rows.
                         One page under experiments/FIGURE_LOCK.toml: [page] width_double_mm wide, at most height_max_mm
                         high; text at PT_TEXT (10 pt), the answer, signal names and totals line at PT_HEAD (12 pt), stage
                         names at PT_STAGE (11 pt), the tool line at [type] font_min_pt, panel letters at panel_letter_pt
                         and panel_letter_weight, all in the first of [type] font_families (TrueType, pdf.fonttype 42);
                         every box border and arrow black (Valerio, 8 Nov); no title, stamp or caption on the plate (E5);
                         house_style.check_figure_colours, then S457.finish_plate (build order F4: no text off the
                         page or on another, the PNG the PDF rasterised by MuPDF at 600 dpi, as S448 R7 compares them)
  Source Data Fig. 1 (provisional, 2 of 2).xlsx  sheet "Fig. 1a": one row per readout of panel a (name, signal,
                         reference, tool, clause, the readout printed, rated, figures, figures as printed, full definition,
                         source); sheet "Fig. 1b": one row per logical line of panel b's setting (stage, axis, levels, how
                         levels is made up, the word for each factor, the line's text, figure, plan row, the design files
                         it is read from), so every level list and model name that is not on the plate stays here, then
                         two rows for the totals printed under the stages: the answers (S492) and the model calls (S520);
                         no creation or modification time and fixed zip dates, so a re-run on the same inputs is
                         byte-identical
  figure1_numbers.json   the same sheets as JSON, and "printed": every level, readout, reference, tool and total by its
                         SVG group id, with the sheet row and format it is written from (S448 R8 (6))
  Source Data Fig. 1 caption (provisional, 2 of 2).md, legend_draft.md, figure1_provenance.json (every input's
                         sha256, both locks' sha256, every output's sha256, the data stamp)

"2 of 2" counts panels (D153 Q8, 26 Oct, with F2 and F4 of 25 Oct): b is drawn under a. The stamp and the Source Data
caption carry no run status (D154), except that the stamp says "total of LLM calls pending" while the slot stands.

D307 (Valerio, 8 Nov, "let's make it official"): the panels swapped. Before it, panel a was the design (one lollipop per
setting on a log axis, with a make-up column) and panel b the measures.

PANEL a (alt2): the answer, one stem down from it forking at right angles into three arrows, one per signal box (Judge,
Concepts, Papers; figure_names.SIGNALS). Each box gives the signal, its reference, what scores it (the judges from
LOCK.toml [judge], word matching, MiniCheck) and, under a grey rule, one readout line per measure row of that signal
(MEASURES, READOUT). The arrowheads end at the boxes: the signals are reported one by one, never pooled. The measures
outside the signals (human rating, execution, mean reciprocal rank) are not drawn since D307. MEASURES are still checked
against the figures' legend drafts (LEGENDS: every figure a measure names must name it, no other may; RAGAS and
RAGChecker left out, D136 Q6 and D33). The draws (DRAW_PARTS, read from draws.csv's draws column) have been drawn by
Supplementary Figure 1 (S496) since D183 FD6 B, from the draw kinds this script records in figure1_provenance.json
("draw_kinds"); they are still read and checked here (every tripwire stays). Valerio, 23 Oct: no draws in the legend.

PANEL b (alt2): the four pipeline stages left to right, each with its settings and their number of levels (bold, right
aligned); a black arrow between stages. Under the stages, the totals line "<answers> answers | <model calls> model
calls": the answers are S492's today.total_counted (findings/recompute/S492_answer_registry/registry.json, read at HEAD;
one generation row per question, configuration and draw, every stored draw counted, plus the April model-selection and
retrieval rows), the model calls S520's "figure1_legend_total", read from its committed summary at HEAD (with that file
not committed the plate prints the slot "n model calls"; TOTAL_ON_PLATE False takes the line off the plate). Model
names, level lists and the make-up of each count are not on the plate; they are in sheet Fig. 1b, and the names in
Supplementary Table 2. The legend says Supplementary Figure 1 gives the calls per experiment only while
frozen_inputs/SHA256SUMS lists S520's inputs, which is when S496 prints them.

PANEL b, every value read at build time (nothing typed here but labels for config names, each refused if a config
appears that has no label):
  INDEX     Corpus scale          exp_02 CORE_SIZES x NOISE_RATIOS (G4); G4's g4_lib.sh ORDER must hold the same
                                  12 indexes and experiment.py SCALING_CORE_SIZES the same sizes
            Embedding model       exp01_embedding_latest.json, the committed copy of the raw file in
                                  findings/recompute/upstream_inputs/publication/results (TRUSTED; not re-run):
                                  config models x corpus_sizes, equal to its results count
            Chunking              exp03a_chunking_latest.json: configs_tested x runs, equal to its results count;
                                  each run scored its own query set (per_query ids differ between runs A, B, C, and
                                  the run stops if two are the same), so the plate says "query sets", not "repeat runs"
  RETRIEVE  Search strategy       exp02_search_latest.json: configs_tested x corpus_sizes, equal to its results
            Retrieval depth       exp_06 DEFAULT_DEPTHS (G5; g5_lib.sh SMOKE_OPTS must name the same depths) x two
                                  RLMs: the authors' RLM (experiments/rlm_ref/run_rlm_ref.py FIGURE2_CAPS and
                                  DEPTH_SWEEP_CAPS, whose union must be DEFAULT_DEPTHS); + T1 (D153 Q8, F1 of 25 Oct):
                                  T1_runs/assignment.toml's caps x its models less check_t1.py HELD, equal to
                                  draws.csv's T1 design
  GENERATE  Generation model      exp_common GEN_MODEL (G1's) + T2's generators: check_t2.py GENERATORS, which must be
                                  the generators t2_lib.sh's case accepts, none of them G1's; T2 runs check_t2.py
                                  CONFIGS (= exp_01's six) on N_QUESTIONS (= the 135). Panel b's draws for them: the
                                  runner's Figure 2 draws, less a generator's subset draws (check_t2.py subset_draws, run
                                  from its source per config: a Gemini generator's 2 and 3 on d98_subset.json, a third
                                  of the 135; a local generator's RLM set-ups at every draw, D175 Q3, D176),
                                  not draws.csv's one T2 text; draws.csv's T2 design is held to the code once it no
                                  longer reads "design to come"
            Generation strategy   exp_01 CONFIG_NAMES (G1) + MATCHED_BUDGET (G2) + the authors' RLM at FIGURE2_CAPS (G6)
            System configuration  exp_03 CONFIG_NAMES that are not orchestrator set-ups, and full_orchestrator
            Orchestrator set-up   exp_03 ORCHESTRATOR_CONFIGS in G3's WAVE1 and STRESS_CONFIG_NAMES (G9, while
                                  draws.csv says done); WAVE2's two distiller set-ups are left out by D154 as amended
                                  (Rule 12's zero branch: the distiller count on the full pipeline's draw 1 is 0, and
                                  they were never in April's results); the run also stops while draws.csv G3 no longer
                                  says wave 2 has not run (a tripwire on that text). WAVE1 + WAVE2 + rlm_10 must equal
                                  exp_03 CONFIG_NAMES
            Code-generation       the harness's 11 CONFIG_NAMES (exp_v2_8_coder_benchmark.py) in Figure 6's order
            strategy              and labels (S447 STRATEGIES) x Figure 6's variants: exp_05's variants(), run here
                                  from its own source on the lock (16 variants of its 10 FIG6_MODELS), less S447's
                                  IF_TIME (D100) and REMOVED (D116) variants (fig6_design(); 11 variants of 7
                                  models), whose count must give draws.csv S2 answers
  JUDGE     Judge model           LOCK.toml [judge] model and second_model, through the runner's lock.judges(); the
                                  second drawn on the generation strategies only (D153 Q8): S483_d85_check's record
                                  must be a passed D85 check of that model under this lock, and S483 must run G1 alone
Levels is the number of configurations of a row's setting; where a setting was run across a second factor, the
first line of its text says how the number is made up ("4 models x 5 corpus sizes"), as S162 did.

REPRODUCE FIRST (README.md:75-79): before anything is written, the rows whose design is unchanged must give the
submitted plate's numerals (S162 STAGES: corpus scale 12, embedding 20, chunking 24, search 35, 10 depths,
6 strategies), the runner's variant list must equal S447 VARIANTS and give the runner's 3,520 attempts (D71, S447
TOTAL), Figure 6's design (less D100's if-time and D116's removed variants) must give draws.csv S2 answers (2,420),
and every count must equal the design column of experiments/draws.csv where that file states it. Panel b's draws
read draws.csv's draws column for each drawn setting (DRAW_PARTS; D98), and a part whose rows do not all read "3", all
D98's text or all one draw stops the run. Any difference stops the run (exit 2) with nothing written.

INPUTS (D155): committed files only. Every file S456 reads itself is read at its committed version (the blob at git
HEAD; outside a git checkout, the file as it is), so an uncommitted edit in the working copy neither moves the plate
nor its recorded sha256; the one exception is S494 --write, which sets LEGENDS_AT "worktree" so the other figures'
legend drafts, just rewritten by the steps before Figure 1, are read from the working tree (audit 27 Oct F1b; the
check run then holds them to HEAD). Every check and tripwire above reads these files at HEAD (the design as it stands today):
draws.csv's design, draws and status columns, G3's "wave 2 not run", G9's "done", T2's "design to come", plan.csv, the
run code, S162, S447 and the legend drafts. The design files (DESIGN_FILES: plan.csv, draws.csv, the run code, the
launch libraries, check_t1.py, S162, S447, S483 and its D85 record) are also read a second time as they stood at
DESIGN_AT (9ba614d2, the commit that records D175 Q3 and D176, the local T2 generators' RLM set-ups on D98's third;
3f4db8ff until then, 7e4a13f9 before that), for two uses only (audit
27 Oct F1, as S459 does; corrected 27 Oct, part 4): (a) inputs_sha256 records each design file's sha256 at DESIGN_AT,
its name carrying "@<DESIGN_AT>", because plan.csv and draws.csv change with every dashboard update and the run code
with every new run, and a sha256 of today's text would move the plate's stamp, legend and provenance with nothing
drawn changed; (b) every value the plate draws or records from them (panel a's rows, the design facts in the
provenance) is computed from both versions and must be equal, or the run stops and names the values that differ
(then move DESIGN_AT to a commit holding the new design, and run S494 --write). The one exception is plan.csv's T2
status, run status recorded only in the provenance's not_drawn, which is taken at DESIGN_AT. The files it reads
through an import (IMPORTED: the runner, the authors' RLM module, LOCK.toml, the answer keys, the judge's system
prompt) must equal HEAD or the run stops; of these, experiment.py, lock.py and run_rlm_ref.py are recorded at
DESIGN_AT, and every top-level definition S456 uses from them (IMPORT_USES, with the definitions those reach) must be
the same at HEAD as at DESIGN_AT, or the run stops (a change elsewhere in those files, a new run's code, does not).
The three submitted retrieval runs are the
committed frozen set findings/recompute/upstream_inputs (fig_repro.frozen, then check_committed against
frozen_inputs/SHA256SUMS); no sibling checkout, no machine.RESULTS. The stamp, caption, legend draft, numbers and
provenance carry no HEAD, working-copy state or write time: the stamp names the inputs by inputs_digest, the sha256 of
their sorted "<sha256>  <name>" lines, so the same committed inputs give the same files under the conditions the
figures README names (Python 3.13.11, .python-version; macOS with /System/Library/Fonts/Helvetica.ttc): the
provenance records the interpreter's version, and the plate's font bytes are the system Helvetica's.

No model call; no Ollama or Gemini contact; reads files only.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import math
import platform
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import figure_names                                                           # noqa: E402
import fig_design                                                             # noqa: E402
from fig_repro import FrozenInputError, check_committed, frozen, frozen_label   # noqa: E402
from experiments.runner import experiment as ex                              # noqa: E402
from experiments.runner.lock import load as load_lock                        # noqa: E402
import pinned_history as PH                                                   # noqa: E402  (O3)

N = 1                                             # the figure
OUT = ROOT / "findings" / "figures_provisional" / "fig1"
LOCK = ROOT / "experiments" / "LOCK.toml"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
PUB = ROOT / "experiments" / "mentori" / "publication" / "scripts"
UPSTREAM_SET, UPSTREAM_REL = "upstream", "publication/results"    # upstream_inputs/publication/results
UPSTREAM = ROOT / "findings" / "recompute" / f"{UPSTREAM_SET}_inputs" / UPSTREAM_REL
F = {
    "exp_01": PUB / "exp_01_generation.py",
    "exp_02": PUB / "exp_02_scaling_factorial.py",
    "exp_03": PUB / "exp_03_orchestration_ablation.py",
    "exp_05": PUB / "exp_05_coder_benchmark.py",
    "exp_06": PUB / "exp_06_depth_sweep.py",
    "v2_8": ROOT / "experiments" / "mentori" / "tests" / "experiments_v2" / "exp_v2_8_coder_benchmark.py",
    "v4_common": ROOT / "experiments" / "mentori" / "tests" / "experiments_v4" / "exp_common.py",
    "rlm_ref": ROOT / "experiments" / "rlm_ref" / "run_rlm_ref.py",
    "rlm_ref_pyproject": ROOT / "experiments" / "rlm_ref" / "pyproject.toml",
    "experiment": ROOT / "experiments" / "runner" / "experiment.py",
    "lock_py": ROOT / "experiments" / "runner" / "lock.py",
    "g3_preflight": ROOT / "findings" / "recompute" / "G3_runs" / "preflight.sh",
    "g4_lib": ROOT / "findings" / "recompute" / "G4_runs" / "g4_lib.sh",
    "g5_lib": ROOT / "findings" / "recompute" / "G5_runs" / "g5_lib.sh",
    # D2 (Valerio, 8 Nov): figures are built from data only. draws.csv, plan.csv and the human-evaluation protocol are
    # working files; the build reads the values S456 takes from them out of findings/recompute/fig_design_inputs/
    # (S616 extract, from the files at HEAD, which equal DESIGN_AT's for every value read: draws.csv and the protocol
    # byte for byte, plan.csv's T2 feeds and status), and S616 check holds them to the working files
    "draws": fig_design.DRAWS,
    "design_facts": fig_design.FACTS,
    "s162": ROOT / "scripts" / "S162_figure1_final.py",
    "s447": ROOT / "scripts" / "S447_fig6_panels.py",
    "key_v24": ex.KEY_V24,
    "key_d5": ex.KEY_D5,
    # D155: the committed copies of the submitted retrieval runs (findings/recompute/upstream_inputs, each listed in
    # frozen_inputs/SHA256SUMS; checked through fig_repro.frozen and check_committed in check_inputs()), never
    # machine.RESULTS, which resolved to the sibling checkout ~/projects/Mentori-paper
    "exp01_raw": UPSTREAM / "exp01_embedding_latest.json",
    "exp02_raw": UPSTREAM / "exp02_search_latest.json",
    "exp03a_raw": UPSTREAM / "exp03a_chunking_latest.json",
    "coder_gt": ROOT / "experiments" / "mentori" / "tests" / "experiments_v2" / "datasets" / "coder_ground_truth.json",
    "t1_assignment": ROOT / "findings" / "recompute" / "T1_runs" / "assignment.toml",
    "t1_check": ROOT / "findings" / "recompute" / "T1_runs" / "check_t1.py",
    "d85_check": ROOT / "findings" / "recompute" / "S483_d85_check" / "repro_check.json",
    "s483": ROOT / "scripts" / "S483_second_judge.py",
    # the generation-model row (T2, D160 (2) and (15) S2): T2's generators and draws as its run code holds them
    "check_t2": ROOT / "findings" / "recompute" / "T2_runs" / "check_t2.py",
    "t2_lib": ROOT / "findings" / "recompute" / "T2_runs" / "t2_lib.sh",
    "d98_subset": ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json",
    # the human ratings row (D183 FD7 a): its item count and rating scale, from the human-evaluation protocol's two
    # lines in design_facts.json (s08b_protocol, from findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md; D2)
    # the total of LLM calls (D199, D200): read at HEAD, not a design file; absent from the inputs while not committed
    "s520_summary": ROOT / "findings" / "recompute" / "S520_llm_calls" / "summary.json",
    # D307 (alt2): the answer count under panel b, S492's today.total_counted, read at HEAD (not a design file)
    "s492_registry": ROOT / "findings" / "recompute" / "S492_answer_registry" / "registry.json",
}
# the legends panel a's measures are checked against (each measure's figures must name it, the others must not)
FIG_DIR = ROOT / "findings" / "figures_provisional"
LEGENDS = {"2": FIG_DIR / "fig2_human" / "legend_draft.md", "3": FIG_DIR / "fig3_strategies" / "legend_draft.md",
           "4": FIG_DIR / "fig4_depth" / "legend_draft.md", "5": FIG_DIR / "fig4" / "legend_draft.md",   # D283: the folders
           "6": FIG_DIR / "fig5" / "legend_draft.md", "7": FIG_DIR / "fig6" / "legend_draft.md",          # keep their names
           "Supp. 2": FIG_DIR / "supp_fig2" / "legend_draft.md"}
F.update({f"legend_fig{k.replace('Supp. ', 's')}": v for k, v in LEGENDS.items()})
# Audit 27 Oct F1 (D155): DESIGN_AT is the commit whose files give every sha256 the committed plate recorded (checked
# 27 Oct: the 27 repository files among figure1_provenance.json's 36 inputs, the 3 frozen runs and the 6 legend drafts
# aside, all equal at 7e4a13f9). D160 (15) S2 (27 Oct): moved to 3f4db8ff, the commit that records D160 (2)'s roster;
# its check_t2.py and t2_lib.sh hold T2's four generators, unchanged since 790b4760 (the local lane, the first commit
# with all four), and the generation-model row draws them. D183 FD6 B (30 Oct): moved to 9ba614d2, the commit that
# records D175 Q3 and D176 (check_t2.py subset_draws(config, generator): the local generators' RLM set-ups on D98's
# third at every draw, the draw kind "rlm45"); at 3f4db8ff the design facts draws_by, draws_figures and t2_draws gave
# the local generators 3 draws, so the run stopped as drawn_moved() intends. Between 9ba614d2 and the commit that adds
# the human ratings row, the design files differ only in the protocol (S08b, amendment 9's draft; the two values read
# from it are the same at both) and T2_runs/start_local.sh, which S456 does not read.
# B1 part 2 (2 November): moved to 457bb3ef, the commit whose draws.csv holds the renumbered figure column (FF3 a). That
# column feeds the design fact draws_figures, which the provenance records and the plate does not draw, so the run stopped
# as drawn_moved() intends; 457bb3ef gives drawn_moved empty against HEAD and imports_unchanged empty, every other row and
# fact equal. spec/fig1.md said a label change leaves DESIGN_AT alone; this one did not.
# plan.csv and draws.csv change with every dashboard update and the run code with every
# new run; their sha256 at HEAD changed the plate's stamp, legend, caption, numbers and provenance with nothing in the
# design changed. So inputs_sha256 records the design files at DESIGN_AT, and the values drawn from them are computed
# at DESIGN_AT too and must equal those computed at HEAD (design_pinned(), drawn_moved()). Every check and tripwire
# reads HEAD (design() with _PIN False): pinning moved them onto DESIGN_AT until the fix of 27 Oct, part 4.
# A284 (7 November): moved to f83c10b4, the commit whose draws.csv gives G5 the draws '3' (D284: draws 2 and 3 on all 86,
# 2,580 of 2,580 stored), so panel b's draw kind of "RLM with gemini-3-flash-preview" moved from 'd98' to '3', the one
# value that differed (drawn_moved() stopped the run as it intends).
DESIGN_AT = "f83c10b4"
DESIGN_KEYS = ("exp_01", "exp_02", "exp_03", "exp_05", "exp_06", "v2_8", "v4_common", "rlm_ref", "rlm_ref_pyproject",
               "experiment", "lock_py", "g3_preflight", "g4_lib", "g5_lib", "s162", "s447",
               "coder_gt", "t1_assignment", "t1_check", "d85_check", "s483", "check_t2", "t2_lib", "d98_subset")
# D2: draws.csv, plan.csv and the protocol left DESIGN_KEYS for the data files F "draws" and "design_facts", read at
# HEAD like any other input: they hold no dashboard text that changes with a run, so nothing needs pinning
DESIGN_FILES = {F[k] for k in DESIGN_KEYS}
# the files of DESIGN_FILES that S456 also imports, and the top-level names it uses from each (ex.<name>, load_lock,
# depth_sweep86_questions, module_const): each name's definition, and every top-level definition it reaches, must be
# the same at HEAD as at DESIGN_AT (imports_unchanged()), so the values the import gives are the design read at
# DESIGN_AT. The rest of these files (a new run's code) may change.
IMPORT_USES = {
    "experiment": ("SCALING_CORE_SIZES", "KEY_V24", "KEY_D5", "questions", "N_QUESTIONS", "N_PER_SIZE", "DRAWS",
                   "draws", "ExperimentError"),
    "lock_py": ("load",),
    "rlm_ref": ("FIGURE2_CAPS", "DEPTH_SWEEP_CAPS", "depth_sweep86_questions"),
}
TIMES = "×"                                  # the multiplication sign, as S162 writes it
SEP = " / "                                       # every list on the plate (S162: commas and slashes not mixed)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------------------------
# D155: every input is a committed file. A design file S456 reads itself is read at its committed version (the blob at
# git HEAD), so an uncommitted edit in the working copy (another agent's, or a run in progress) can neither move the
# plate nor change a recorded sha256; outside a git checkout (an archive of the repository) the file on disk is the
# committed version and is read as it is. A file S456 reads through an import (the runner, the authors' RLM module,
# the lock, the answer keys) cannot be read at HEAD, so it must equal HEAD or the run stops (check_inputs()).
# ---------------------------------------------------------------------------------------------------------------
IMPORTED = ["experiments/runner", "experiments/rlm_ref/__init__.py", "experiments/rlm_ref/run_rlm_ref.py",
            "experiments/LOCK.toml", "data/ground_truth_v2", "data/judge_system_prompts"]
_BLOBS: dict = {}
_PIN = False          # True only inside design_pinned(): the design files are then read at DESIGN_AT
# Where the other figures' legend drafts (LEGENDS) are read: "HEAD" (the committed blob), or "worktree", set only by
# S494 --write (its _call --setstr), which runs Figure 1 after the steps that have just rewritten those legends in the
# working tree, so one --write pass records the legends the plates are committed with (audit 27 Oct F1b). A check run
# (S494 --out) reads HEAD, the legends its rebuilt plates are held to.
LEGENDS_AT = "HEAD"


def in_git(root: Path = ROOT) -> bool:
    r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def at_of(p: Path, root: Path = ROOT) -> str:
    """The commit p is read at: HEAD, except a design file of this repository (DESIGN_FILES) inside design_pinned(),
    which is read at DESIGN_AT, and a legend draft under LEGENDS_AT "worktree" (S494 --write), read from the working
    tree ("WORKTREE"). Every check and tripwire runs with _PIN False, so it reads HEAD."""
    if Path(root) == ROOT and _PIN and Path(p) in DESIGN_FILES:
        return DESIGN_AT
    if Path(root) == ROOT and LEGENDS_AT == "worktree" and Path(p) in set(LEGENDS.values()):
        return "WORKTREE"
    return "HEAD"


def committed_bytes(p: Path, root: Path = ROOT, at: str | None = None) -> bytes:
    """p's bytes at commit `at` (default at_of(p): HEAD, or DESIGN_AT for a design file inside design_pinned();
    refused when p is outside root or not committed there); outside a git checkout, p as on disk. O3 (8 Nov): a file
    of this repository at a commit other than HEAD (DESIGN_AT) is read from its copy pinned in the tree, held to the
    blob id git gave it (scripts/pinned_history.py), never from the history; another root (the selftest's own
    repository) is still read with git cat-file there."""
    p = Path(p)
    at = at or at_of(p, root)
    key = (str(root), str(p), at)
    if key in _BLOBS:
        return _BLOBS[key]
    try:
        r_ = p.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        stop(f"{p} is outside the repository: S456 reads committed files only (D155)")
    if Path(root) == ROOT and at not in ("HEAD", "WORKTREE"):
        try:
            data = PH.show(at, r_)
        except PH.PinError as e:
            stop(f"{r_} is not committed (no blob at {at}): S456 reads committed files only (D155; {e})")
    elif not in_git(root) or at == "WORKTREE":
        data = p.read_bytes()
    else:
        r = subprocess.run(["git", "cat-file", "blob", f"{at}:{r_}"], cwd=root, capture_output=True)
        if r.returncode != 0:
            stop(f"{r_} is not committed (no blob at {at}): S456 reads committed files only (D155)")
        data = r.stdout
    _BLOBS[key] = data
    return data


def recorded_at(p: Path) -> str:
    """The version inputs_sha256 records p at: DESIGN_AT for a design file (DESIGN_FILES), else as read (at_of)."""
    return DESIGN_AT if Path(p) in DESIGN_FILES else at_of(p)


def input_name(p: Path) -> str:
    """p's name in inputs_sha256: its frozen label, with "@<DESIGN_AT>" for a design file recorded there."""
    return frozen_label(p) + (f"@{DESIGN_AT}" if recorded_at(p) == DESIGN_AT else "")


def input_sha256(p: Path) -> str:
    """p's sha256 in inputs_sha256: at DESIGN_AT for a design file, else as read (HEAD, or the working tree for a
    legend draft under S494 --write)."""
    return sha256_bytes(committed_bytes(p, ROOT, recorded_at(p)))


def top_level_closure(src: str, names) -> dict:
    """{name: [ast.dump of each top-level statement defining it]} for the named top-level definitions of a module's
    source and every top-level definition they reach by name (functions, classes, assignments, imports; an import is
    compared as its statement, not the module it names). ast.dump leaves out line numbers, so moved code is equal."""
    defs = {}
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            got = [n.name]
        elif isinstance(n, ast.Assign):
            got = [t.id for t in n.targets if isinstance(t, ast.Name)] + \
                  [e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name)]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            got = [n.target.id]
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            got = [(a.asname or a.name).split(".")[0] for a in n.names]
        else:
            got = []
        for x in got:
            defs.setdefault(x, []).append(n)
    seen, todo = set(), list(names)
    while todo:
        x = todo.pop()
        if x in seen or x not in defs:
            continue
        seen.add(x)
        todo += [s.id for n in defs[x] for s in ast.walk(n) if isinstance(s, ast.Name) and s.id in defs]
    return {x: [ast.dump(n) for n in defs[x]] for x in sorted(seen)}


def imports_unchanged(root: Path = ROOT, at: str = DESIGN_AT, uses=None) -> list:
    """The problems, [] if none: for each imported design file (IMPORT_USES), a used name missing at DESIGN_AT, or a
    definition S456 uses (or one it reaches) that differs between DESIGN_AT and HEAD. [] outside a git checkout."""
    if not in_git(root):
        return []
    probs = []
    for k, names in (uses or IMPORT_USES).items():
        p = F[k] if isinstance(k, str) and k in F else Path(k)
        old = committed_bytes(p, root, at).decode("utf-8")
        new = committed_bytes(p, root, "HEAD").decode("utf-8")
        if old == new:
            continue
        a, b = top_level_closure(old, names), top_level_closure(new, names)
        missing = sorted(set(names) - set(a))
        if missing:
            probs.append(f"{p.name} at {at} defines no {missing}")
        diff = sorted(x for x in set(a) | set(b) if a.get(x) != b.get(x))
        if diff:
            probs.append(f"{p.name}: {diff} differ between {at} and HEAD")
    return probs


def read_text(p: Path) -> str:
    return committed_bytes(p).decode("utf-8")


def imported_dirty(root: Path = ROOT, paths=None) -> list:
    """The files S456 reads through an import that differ from HEAD (git status, tracked files only); [] outside git."""
    if not in_git(root):
        return []
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", *(paths or IMPORTED)], cwd=root,
                       capture_output=True, text=True)
    return [ln[3:] for ln in r.stdout.splitlines() if ln.strip()]


def check_inputs():
    """D155, before anything is read: the submitted retrieval runs are the committed frozen copies (fig_repro.frozen
    and check_committed against frozen_inputs/SHA256SUMS), and every file read through an import equals HEAD."""
    for k in ("exp01_raw", "exp02_raw", "exp03a_raw"):
        try:
            got = check_committed(frozen(UPSTREAM_SET, f"{UPSTREAM_REL}/{F[k].name}"))
        except FrozenInputError as e:
            stop(f"frozen input: {e}")
        if got.resolve() != F[k].resolve():
            stop(f"{F[k]}: fig_repro.frozen gives {got}")
    dirty = imported_dirty()
    if dirty:
        stop(f"files S456 reads through an import differ from HEAD, so the plate would not be the committed design's: "
             f"{dirty} (commit them or run in a clean clone)")
    moved = imports_unchanged()
    if moved:
        stop(f"what S456 imports is no longer the design read at DESIGN_AT {DESIGN_AT}: {'; '.join(moved)} (move "
             f"DESIGN_AT to a commit that holds the new design, then S494 --write)")


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p.resolve())


def stop(msg: str, code: int = 2):
    if _PIN:
        msg = f"(the design files read at DESIGN_AT {DESIGN_AT}, design_pinned()) {msg}"
    print(f"S456 REFUSED: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------------------------------------------
# Reading the design files
# ---------------------------------------------------------------------------------------------------------------
def module_const(path: Path, name: str):
    """A module-level constant of a Python file, read from its syntax tree (the module is not imported: the
    experiment scripts import Mentori's backend). Only a literal is accepted."""
    tree = ast.parse(read_text(path), filename=str(path))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) \
            else []
        if any(isinstance(t, ast.Name) and t.id == name for t in targets) and node.value is not None:
            return ast.literal_eval(node.value)
        for t in targets:                         # a tuple assignment, "N_OPS, N_DRAWS = 20, 1"
            if isinstance(t, ast.Tuple) and isinstance(node.value, ast.Tuple) and len(t.elts) == len(node.value.elts):
                for el, val in zip(t.elts, node.value.elts):
                    if isinstance(el, ast.Name) and el.id == name:
                        return ast.literal_eval(val)
    stop(f"{rel(path)} has no module-level literal {name}")


def module_functions(path: Path, names, ns: dict) -> dict:
    """The named top-level functions of a Python file, compiled from its own source into ns (so the runner's code is
    what runs, not a copy of it)."""
    tree = ast.parse(read_text(path), filename=str(path))
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if sorted(n.name for n in found) != sorted(names):
        stop(f"{rel(path)} lacks {sorted(set(names) - {n.name for n in found})}")
    exec(compile(ast.Module(body=found, type_ignores=[]), str(path), "exec"), ns)
    return ns


def module_names(path: Path) -> list:
    """The names a Python file binds at its top level by assignment (a tuple assignment's names included)."""
    out = []
    for node in ast.parse(read_text(path), filename=str(path)).body:
        for t in node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) \
                else []:
            out += [t.id] if isinstance(t, ast.Name) else [e.id for e in t.elts if isinstance(e, ast.Name)] \
                if isinstance(t, ast.Tuple) else []
    return out


def shell_var(path: Path, name: str) -> str:
    m = re.search(rf'^{name}="([^"]*)"', read_text(path), re.M)
    if not m:
        stop(f"{rel(path)} sets no {name}=\"...\"")
    return m.group(1)


def csv_rows(path: Path):
    return list(csv.DictReader(io.StringIO(read_text(path), newline="")))


def ints(s: str):
    return [int(x) for x in re.findall(r"\d+", s.replace(",", ""))]


def fig6_variants(lock_path=LOCK):
    """exp_05's variants() run from its own source on the lock: every (model, thinking) variant of Figure 6."""
    from typing import Any, Dict, List, Optional, Tuple, Union
    ns = {"ex": ex, "load_lock": lambda: load_lock(lock_path), "FIG6_MODELS": module_const(F["exp_05"], "FIG6_MODELS"),
          "Any": Any, "Dict": Dict, "List": List, "Optional": Optional, "Tuple": Tuple, "Union": Union}
    module_functions(F["exp_05"], ["_split", "_sent", "variants"], ns)
    return ns["variants"](ns["FIG6_MODELS"]), ns["FIG6_MODELS"]


def t2_generators() -> list:
    """T2's generators, "provider::model", in check_t2.py GENERATORS' order: the dict's keys are names bound to string
    literals at the module's top level (HAIKU, GEMINI_25_PRO = "...", "..."), each read with module_const."""
    tree = ast.parse(read_text(F["check_t2"]))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GENERATORS" for t in node.targets) \
                and isinstance(node.value, ast.Dict):
            out = []
            for k in node.value.keys:
                v = module_const(F["check_t2"], k.id) if isinstance(k, ast.Name) else \
                    k.value if isinstance(k, ast.Constant) else None
                if not isinstance(v, str) or "::" not in v:
                    stop(f"check_t2.py GENERATORS key {ast.dump(k)}: not a provider::model string")
                out.append(v)
            return out
    stop("check_t2.py defines no GENERATORS dict")


def fig6_design(variants):
    """Figure 6's variants (S447 design_of() as it stands with no if-time variant complete): the runner's variants
    less S447's IF_TIME (D100: stopped before completion or not run) and REMOVED (D116: nemotron-3-nano:30b dropped
    from every experiment). Returns (kept, {run id extra: decision} of those left out)."""
    out_ = {**module_const(F["s447"], "IF_TIME"), **module_const(F["s447"], "REMOVED")}
    known = {v["extra"] for v in variants}
    if set(out_) - known:
        stop(f"S447 IF_TIME or REMOVED names a variant exp_05 does not run: {sorted(set(out_) - known)}")
    return [v for v in variants if v["extra"] not in out_], {v["extra"]: out_[v["extra"]] for v in variants
                                                              if v["extra"] in out_}


# the decisions S447 sets a variant outside Figure 6's design by (a decision not listed here stops the run). D154: the
# caption says what is drawn, not why a variant is not (D100: if-time variants; D116: nemotron-3-nano:30b removed).
LEFT_OUT_DECISIONS = ("D100", "D116")

# Panel b, draws (D153 Q8 with F4 of 25 Oct): the draws each drawn setting is designed with, read from draws.csv's
# draws column. Each part: its name on the plate and the draws.csv rows (plan row, a word of its experiment column) that
# hold it. RLM-10 in system configuration is Figure 2's RLM-10, so generation strategy covers it; the full orchestrator
# is the orchestrator set-up "as built" (G3's pipeline ablation). Valerio, 23 Oct: no draws in the legend, so they were
# drawn here; D183 FD6 B (30 Oct): Supplementary Figure 1 draws them, from DRAW_KINDS and RUN_ONCE as recorded in the
# provenance ("draw_kinds"), and Figure 1 keeps the checks.
DRAW_PARTS = [("generation strategy", [("G1", "generation strategies"), ("G2", "matched")]),
              (figure_names.PACKAGE_RLM, [("G6", "caps 5 10 20"), ("G6", "depth caps")]),
              ("no retrieval and naive RAG", [("G3", "naive")]),
              ("corpus scale", [("G4", "corpus scaling")]),
              (f"{figure_names.MENTORI_RLM} with gemini-3-flash-preview", [("G5", "retrieval depth")]),
              ("the 6 orchestrator set-ups", [("G3", "pipeline ablation")]),
              ("the 2 stress set-ups", [("G9", "every step")]),
              ("the local models", [("T1", "local models")]),
              ("code-generation strategy", [("S2", "code generation")])]
D98_DRAWS = "1, and 2 and 3 on a fixed third (D98)"     # draws.csv's draws text for a D98 experiment
DRAW_KINDS = [("3", "3 draws", "every question answered three times"),
              ("d98", "1 + 2 draws", "every question answered once, and a fixed third of them twice more"),
              ("rlm45", "3 draws, RLM on a third", "every question answered three times, except by the RLM set-ups, "
               "which answer a fixed third of them three times"),   # D175 Q3, D176: T2's local generators
              ("1", "1 draw", "every question answered once")]
RUN_ONCE = ("1 run", "each retrieval query scored once")       # the retrieval settings (D154: a count, not a history)

# Panel b, measures (D153 Q8 with F2 of 25 Oct; FC7: each measure says which figure reports it). D33: RAGAS only if
# Figure 5 uses it; D136 Q6 (Fig5.Q1 O-a) moved RAGAS and RAGChecker to a Supplementary figure, so neither is here.
# (name, text, figures, regex, signal, reference, clause, rated). A measure's figures are checked against the figures'
# legend drafts (LEGENDS): every figure named must name the measure (the regex, case ignored) and no other figure may,
# else the run stops. If a legend words a measure otherwise, change the regex, never the figure list (spec/fig1.md): Figure
# 2's legend says "the judge's and the raters' scores" and "Faithfulness: share of each judge band". Signal and reference
# fill panel a's signal boxes (READOUT, D307), clause and rated the sheet's columns (FF6, plan_final.json:291); text is the full definition, for the sheet.
# Human rating's {items}, {lo}, {hi} and {scales} are read from the protocol in design(), and it is an ordinary row since
# Figure 2's legend is committed. The literal stays evaluable: S497_fig5_d200_test.py reads it from this source.
MEASURES = [("Judge correctness", "each answer scored against the expert answer key; pass at score 4 or more; relaxed, "
             "3 or more", ["2", "3", "5", "6"], r"judge(?:'s)? (?:correctness|score)|the judge's and the raters' scores",
             figure_names.JUDGE, "against key and passages", "pass 4+, relaxed 3+", "yes"),
            ("Judge refusal", "each answer to an out-of-scope question scored for refusal; refused at 3 or more",
             ["3", "5"], r"refusal score", figure_names.JUDGE, "against key and passages", "refused 3+", "no"),
            ("Judge faithfulness", "each answer scored by the plain call, without passages, or the call with passages; "
             "the raters check the plain call only", ["2", "6"],
             r"faithfulness score|Faithfulness: share of each judge band", figure_names.JUDGE,
             "against key and passages", "with or without passages", "part"),
            ("Concept recall", "share of the key's expected concepts that a concept matcher finds in the answer; a "
             "concept's content words that also occur in the question are not counted", ["2", "4", "5", "6"], r"concept recall",
             figure_names.CONCEPTS, "against the key", "concepts found", "yes"),
            (figure_names.PAPERS_PRECISION, "share of the answer's claims that MiniCheck finds supported by the key's "
             "source papers; Figure 2 uses the same tool against the key", ["2", "6"], figure_names.PAPERS_MEASURE_RE,
             figure_names.PAPERS, "against sources", "claims supported", "part"),
            ("Human rating", "each of {items} answers of the submitted run rated {lo} to {hi} by expert raters for "
             "{scales}", ["2"], r"\bhuman ratings?\b|\braters?\b", "", "", "{items} answers rated {lo} to {hi}", ""),
            ("Execution", "an attempt passes when its code returns values matching the reference; no judge", ["7"],
             r"returns values matching the reference", "", "", "code output; no judge", ""),
            ("Mean reciprocal rank", "the reciprocal of the first relevant result's rank, mean over the retrieval queries",
             ["Supp. 2"], r"mean reciprocal rank|\bMRR\b", "", "", "retrieval", "")]
# the scales the protocol's analyses read (its amendments 1 and 4: overall counts for none); each must be one of the
# protocol's. D183 FD7 a: no row for the published or simple evaluators (D136 Q6).
HUMAN_SCALES = ("correctness", "completeness", "faithfulness")
# Valerio, 2 November: "There should be a one word per type", small and grey under each make-up. One word per number of
# levels_as, same order, same operators (factor_words()). Code generation's second factor is a model variant: 11 variants
# of 7 models, so "model" would miscount it. "stress" carries what the grey label beside the dot said.
FACTORS = {"Corpus scale": f"size {TIMES} distractor", "Embedding model": f"model {TIMES} size",
           "Chunking": f"chunking {TIMES} queries", "Search strategy": f"strategy {TIMES} size",
           "Retrieval depth": f"cap {TIMES} RLM + cap {TIMES} model", "Generation model": "main + replication",
           "Generation strategy": "strategy + reference", "System configuration": "system",
           "Orchestrator set-up": "set-up + stress", "Code-generation strategy": f"strategy {TIMES} variant",
           "Judge model": "judge"}
# the figures each setting's row reports to (new numbers; spec/fig1.md panel a)
# D283 (6 November 2026): retrieval depth is main Figure 4, the pipeline 5, the signals 6 and code generation 7; the
# judges score Figures 2, 3, 5 and 6 (the depth figure is concept recall alone)
SETTING_FIGURE = {"Corpus scale": "Figure 3", "Embedding model": "Supplementary Figure 2",
                  "Chunking": "Supplementary Figure 2", "Search strategy": "Supplementary Figure 2",
                  "Retrieval depth": f"Figure {figure_names.FIG_DEPTH}", "Generation model": "Figure 3",
                  "Generation strategy": "Figure 3", "System configuration": f"Figure {figure_names.FIG_PIPELINE}",
                  "Orchestrator set-up": f"Figure {figure_names.FIG_PIPELINE}",
                  "Code-generation strategy": f"Figure {figure_names.FIG_CODE}", "Judge model": "Figures 2, 3, 5 and 6"}


# labels for config names, refused when a config appears without one (the plate never shows a raw config id)
GEN_LABEL = {"single_pass": "single pass", "multi_hop": "multi-hop", "verified_pass": "verified pass",
             "matched_budget": "single pass at matched budget"}
SYS_LABEL = {"raw_gemini": "no retrieval (model alone)", "naive_rag": "naive RAG", "rlm_10": "RLM-10",
             "full_orchestrator": "full orchestrator"}
ORCH_LABEL = {"full_orchestrator": "as built", "orch_no_distiller": "no distiller",
              "orch_distiller_f1": "distiller prompt F1", "orch_no_analyser": "no analyser",
              "orch_no_planner": "no planner", "orch_no_supervisor": "no supervisor",
              "orch_no_synthesiser": "no synthesizer", "orch_factual_to_documents": "factual questions to documents",
              "orch_distil_every_step": "distiller on every step",
              "orch_distil_every_step_f1": "distiller prompt F1 on every step"}
SEARCH_LABEL = {"dense": "dense", "bm25_standard": "BM25 standard", "bm25_scientific": "BM25 scientific",
                "hybrid_fixed": "hybrid fixed", "hybrid_adaptive": "hybrid adaptive", "rrf": "RRF",
                "rrf_reranker": "RRF + reranker"}


def label(table, key, what):
    if key in table:
        return table[key]
    m = re.fullmatch(r"rlm_(\d+)", key)
    if m:
        return f"RLM-{m.group(1)}"
    stop(f"{what} config {key!r} has no plate label in S456 (add one; the plate never shows a raw id)")


def model_name(ident: str) -> str:
    return ident.partition("::")[2] or ident


def design():
    """Every row of panel a, from the design files, with the checks that tie the files to each other."""
    lock = load_lock(LOCK)
    draws = csv_rows(F["draws"])
    by_row = {}
    for r in draws:
        by_row.setdefault(r["plan_row"], []).append(r)
    probs = []

    def need(cond, msg):
        if not cond:
            probs.append(msg)

    def drawn_design(plan_row, experiment_word):
        rows = [r for r in by_row.get(plan_row, []) if experiment_word.lower() in r["experiment"].lower()]
        if len(rows) != 1:
            probs.append(f"draws.csv: want one {plan_row} row naming {experiment_word!r}, found {len(rows)}")
            return None
        return rows[0]

    # ---- INDEX: corpus scale (G4)
    core = module_const(F["exp_02"], "CORE_SIZES")
    noise = module_const(F["exp_02"], "NOISE_RATIOS")
    idx = [f"exp_v4_s{c}_n{n}" for c in core for n in noise]          # exp_02 get_index_name(), ALL_INDEXES
    need(sorted(shell_var(F["g4_lib"], "ORDER").split()) == sorted(idx),
         f"g4_lib.sh ORDER is not exp_02's {len(idx)} indexes")
    need(tuple(core) == tuple(ex.SCALING_CORE_SIZES), "experiment.py SCALING_CORE_SIZES differs from exp_02")
    g1_strats = module_const(F["exp_01"], "CONFIG_NAMES")
    g4_strats = module_const(F["exp_02"], "CONFIG_NAMES")
    need(g4_strats == g1_strats, "exp_02's strategies differ from exp_01's")
    d = drawn_design("G4", "corpus scaling")
    if d:
        need(ints(d["design"])[:2] == [len(idx), len(g4_strats)], f"draws.csv G4 design {d['design']!r}")

    # ---- INDEX and RETRIEVE: the submitted retrieval runs (raw, not re-run)
    e1 = json.loads(read_text(F["exp01_raw"]))
    e2 = json.loads(read_text(F["exp02_raw"]))
    e3 = json.loads(read_text(F["exp03a_raw"]))
    emb_models, emb_sizes = e1["config"]["models"], e1["config"]["corpus_sizes"]
    need(len(e1["results"]) == len(emb_models) * len(emb_sizes), "exp01: results count is not models x sizes")
    s_cfg, s_sizes = e2["config"]["configs_tested"], e2["config"]["corpus_sizes"]
    need(len(e2["results"]) == len(s_cfg) * len(s_sizes), "exp02: results count is not configs x sizes")
    need(s_sizes == emb_sizes, "exp02's corpus sizes differ from exp01's (the plate says 'the same 5')")
    c_cfg, c_runs = e3["config"]["configs_tested"], e3["config"]["runs"]
    need(len(e3["results"]) == len(c_cfg) * len(c_runs), "exp03a: results count is not configs x runs")
    c_label = {r["config"]: r["config_label"] for r in e3["results"]}
    chunk_groups = {}
    for c in c_cfg:
        kind, size = c.rsplit("_", 1)
        unit = {"tok": "tokens", "char": "characters"}.get(c_label[c].split()[2] if len(c_label[c].split()) > 2
                                                            else "", None)
        if unit is None:
            stop(f"exp03a config {c!r} label {c_label[c]!r}: no unit (tok or char) to print")
        chunk_groups.setdefault((kind, unit), []).append(size)
    # the query count of each run, as each result row records it (the chunking runs differ: run A 28, B and C 27)
    q_emb = sorted({r["n_queries"] for r in e1["results"]})
    q_search = sorted({r["n_queries"] for r in e2["results"]})
    q_chunk = {run: sorted({r["n_queries"] for r in e3["results"] if r["run"] == run}) for run in c_runs}
    need(len(q_emb) == 1 and len(q_search) == 1 and q_emb == q_search and all(len(v) == 1 for v in q_chunk.values()),
         f"query counts: embedding {q_emb}, search {q_search}, chunking per run {q_chunk}")
    # the chunking runs are scored on different query sets, not repeats of one: each run's query ids (per_query id),
    # the same in every config of that run, and no two runs with the same ids, prefix (B_, C_) removed or not.
    # The plate says "query sets"; if two runs ever held the same set, that word would be wrong, so the run stops.
    ids_run = {}
    for r in e3["results"]:
        ids = tuple(q["id"] for q in r["per_query"])
        need(len(ids) == r["n_queries"], f"exp03a {r['config']} run {r['run']}: {len(ids)} per_query ids, "
                                         f"n_queries {r['n_queries']}")
        need(ids_run.setdefault(r["run"], ids) == ids, f"exp03a run {r['run']}: configs scored different queries")
    bare = {run: frozenset(re.sub(rf"^{run}_", "", i) for i in ids) for run, ids in ids_run.items()}
    need(len(set(ids_run.values())) == len(c_runs) and len(set(bare.values())) == len(c_runs),
         "exp03a: two chunking runs hold the same query ids; the plate's 'query sets' would be wrong")
    d = [r for r in draws if r["submitted_id"] == "exp01-exp03"]
    need(len(d) == 1 and d[0]["design"] == "not re-run", "draws.csv: retrieval optimisation is not 'not re-run'")
    # panel b's "1 run" (D154): each retrieval configuration is scored once over its queries. Read from the raw files:
    # no two result rows share a configuration (embedding: model and corpus size; search: config and corpus size;
    # chunking: config and query set), and with the counts above (rows = configs x second factor) each is there once.
    once = {"embedding model": [(r["model"], r["corpus_size"]) for r in e1["results"]],
            "chunking": [(r["config"], r["run"]) for r in e3["results"]],
            "search strategy": [(r["config"], r["corpus_size"]) for r in e2["results"]]}
    for axis, keys in once.items():
        need(len(set(keys)) == len(keys), f"{axis}: a configuration has more than one result row (not 1 run)")
    runs_once = list(once)

    # ---- RETRIEVE: depth (G5 and G6)
    depths = module_const(F["exp_06"], "DEFAULT_DEPTHS")
    smoke = shell_var(F["g5_lib"], "SMOKE_OPTS")
    need([int(x) for x in re.search(r"--depths ([\d ]+)", smoke).group(1).split()] == depths,
         "g5_lib.sh SMOKE_OPTS depths differ from exp_06 DEFAULT_DEPTHS")
    cap2 = module_const(F["rlm_ref"], "FIGURE2_CAPS")
    capd = module_const(F["rlm_ref"], "DEPTH_SWEEP_CAPS")
    need(sorted(set(cap2) | set(capd)) == sorted(depths) and not set(cap2) & set(capd),
         "the authors' RLM caps (FIGURE2_CAPS + DEPTH_SWEEP_CAPS) are not exp_06's depths")
    from experiments.rlm_ref.run_rlm_ref import depth_sweep86_questions
    q86 = {q["id"] for q in depth_sweep86_questions()}
    n86 = len(q86)
    need(q86 <= {q["id"] for q in ex.questions()}, "depth_sweep86 holds questions outside the 135")
    d = drawn_design("G5", "retrieval depth")
    if d:
        need(ints(d["design"])[:2] == [len(depths), n86], f"draws.csv G5 design {d['design']!r}")
    d = [r for r in by_row.get("G6", []) if "depth caps" in r["experiment"].lower()]
    need(len(d) == 1 and ints(d[0]["design"])[0] == len(capd) and ints(d[0]["design"])[1:1 + len(capd)] == list(capd),
         "draws.csv G6 depth caps row differs from DEPTH_SWEEP_CAPS")
    rlms = re.search(r'"rlms==([\d.]+)"', read_text(F["rlm_ref_pyproject"]))
    need(rlms is not None, "experiments/rlm_ref/pyproject.toml pins no rlms version")
    # T1 (D97, D118, D119, D121; Figure 3b, D123): Mentori's RLM on the local models, read from T1's assignment.toml
    # (every machine's models, its caps, its question order) less check_t1.py HELD (models admit refuses: D83 Q167,
    # Q181, D121); the caps must be a subset of exp_06's, and draws.csv's T1 row must state the same design.
    t1 = tomllib.loads(read_text(F["t1_assignment"]))
    t1_held = module_const(F["t1_check"], "HELD")
    t1_all = [m for mach in t1.get("machine", {}).values() for m in mach.get("models", [])]
    t1_models = [m for m in t1_all if m not in t1_held]
    t1_caps = list(t1["depths"])
    t1_q = len(t1["question_order"])
    need(t1.get("status") == "agreed" and t1.get("depths_status") == "agreed",
         "T1 assignment.toml status or depths_status is not 'agreed'")
    need(set(t1_caps) <= set(depths) and t1_caps == sorted(t1_caps), "T1's caps are not exp_06 depths in order")
    need(len(set(t1["question_order"])) == t1_q, "T1's question order names a question twice")
    d = drawn_design("T1", "local models")
    if d:
        m = re.fullmatch(r"(\d+) local models \(.*?\) x (\d+) caps \(([\d, ]+)\) x (\d+) questions", d["design"])
        need(m is not None and int(m.group(1)) == len(t1_models) and int(m.group(2)) == len(t1_caps)
             and [int(x) for x in m.group(3).split(",")] == t1_caps and int(m.group(4)) == t1_q,
             f"draws.csv T1 design {d['design']!r}, T1's files: {len(t1_models)} models x {t1_caps} x {t1_q}")

    # ---- GENERATE: strategies (G1, G2, G6)
    mb = module_const(F["exp_01"], "MATCHED_BUDGET")
    questions = ex.questions()
    need(len(questions) == ex.N_QUESTIONS, "experiment.questions() count differs from N_QUESTIONS")
    d = drawn_design("G1", "generation strategies")
    if d:
        need(ints(d["design"])[:2] == [len(g1_strats), len(questions)], f"draws.csv G1 design {d['design']!r}")
    d = drawn_design("G2", "matched")
    if d:
        need(ints(d["design"])[0] == 1, f"draws.csv G2 design {d['design']!r}")
    d = [r for r in by_row.get("G6", []) if "caps 5 10 20" in r["experiment"].lower()]
    need(len(d) == 1 and ints(d[0]["design"])[:2] == [len(cap2), len(questions)],
         "draws.csv G6 Figure 2 caps row differs from FIGURE2_CAPS x 135")
    gen_model = model_name(module_const(F["v4_common"], "GEN_MODEL"))

    # ---- GENERATE: system configuration and orchestrator set-ups (G3)
    e3c = module_const(F["exp_03"], "CONFIG_NAMES")
    orch = module_const(F["exp_03"], "ORCHESTRATOR_CONFIGS")
    stress = module_const(F["exp_03"], "STRESS_CONFIG_NAMES")
    system = [c for c in e3c if c not in orch or c == "full_orchestrator"]
    w1 = shell_var(F["g3_preflight"], "WAVE1").split()
    w2 = shell_var(F["g3_preflight"], "WAVE2").split()
    need(sorted(w1 + w2 + ["rlm_10"]) == sorted(e3c), "G3 WAVE1 + WAVE2 + rlm_10 is not exp_03 CONFIG_NAMES")
    # D154 as amended (README.md:1002-1006): D52's eight are wave 1's six and wave 2's two distiller set-ups; the two
    # are not drawn by Rule 12's zero branch (the distiller count on the full pipeline's draw 1 is 0, and they were
    # never in April's results), and G9's two Q82 stress set-ups (D75 Q82, A1 of 24 Oct) are drawn, as not Mentori's
    # default. The code still stops when draws.csv no longer says wave 2 has not run, or G9 is not done (a tripwire on
    # that text, read at HEAD by the live pass; audit 27 Oct F13 changed this comment, not the check).
    d52 = [c for c in orch if c not in stress]
    orch_run = [c for c in d52 if c in w1]
    need(all(c in e3c for c in d52), "an orchestrator set-up is not in exp_03 CONFIG_NAMES")
    need(sorted(c for c in d52 if c not in w1) == sorted(w2), "G3 WAVE2 is not D52's set-ups outside WAVE1")
    d = drawn_design("G3", "pipeline ablation")
    if d:
        need(ints(d["design"])[0] == len(d52), f"draws.csv G3 design {d['design']!r}, D52's {len(d52)} set-ups")
        need(re.search(r"wave 2 \(the 2 distiller set-ups\) not run", d["status"]) is not None and len(w2) == 2,
             f"draws.csv G3 status {d['status']!r} no longer says wave 2 has not run: draw the set-ups that ran")
    d = drawn_design("G9", "every step")
    if d:
        need(ints(d["design"])[0] == len(stress), f"draws.csv G9 design {d['design']!r}, {len(stress)} stress set-ups")
        need(d["status"].startswith("done"), f"draws.csv G9 status {d['status']!r}: the stress set-ups have not run")
        need("not Mentori's default" in d["basis"], "draws.csv G9 basis no longer says 'not Mentori's default'")
    orch_setups = orch_run + list(stress)
    d = drawn_design("G3", "naive")
    if d:
        need(ints(d["design"])[0] == len([c for c in system if c not in ("full_orchestrator", "rlm_10")]),
             f"draws.csv G3 baselines {d['design']!r}")

    # ---- GENERATE: code generation (S2)
    runner_variants, runner_models = fig6_variants()
    variants, left_out = fig6_design(runner_variants)          # D100, D116: Figure 6's variants
    fig6_models = [m for m in runner_models if any(v["model"] == m for v in variants)]
    need(all(d in LEFT_OUT_DECISIONS for d in left_out.values()), f"S447 leaves out variants by a decision S456 "
         f"does not know: {sorted(set(left_out.values()) - set(LEFT_OUT_DECISIONS))}")
    cg = module_const(F["v2_8"], "CONFIG_NAMES")
    s447_strats = module_const(F["s447"], "STRATEGIES")
    need(sorted(k for k, _ in s447_strats) == sorted(cg), "S447 STRATEGIES are not the harness's CONFIG_NAMES")
    n_ops = module_const(F["exp_05"], "N_TASKS")
    gt_path = F["coder_gt"]
    need(sha256_bytes(committed_bytes(gt_path)) == module_const(F["exp_05"], "GT_SHA256"),
         "coder_ground_truth.json is not exp_05's pin")
    gt = json.loads(read_text(gt_path))
    gt_ops = [op for ds in gt["datasets"].values() for op in ds["operations"]]
    need(len(gt_ops) == n_ops, f"coder_ground_truth.json holds {len(gt_ops)} operations, exp_05 N_TASKS {n_ops}")
    fig6_draws = ex.draws(6)
    d = drawn_design("S2", "code generation")
    if d:
        # the design column states the runner's list; the answers column Figure 6's design (D100, D116)
        need(ints(d["design"])[:3] == [len(runner_variants), len(cg), n_ops], f"draws.csv S2 design {d['design']!r}")
        need(int(d["answers"]) == len(variants) * len(cg) * n_ops * len(fig6_draws),
             f"draws.csv S2 answers {d['answers']!r}, Figure 6's design {len(variants) * len(cg) * n_ops} "
             f"({len(variants)} variants, D100 and D116 applied)")
    per_model = {}
    for v in variants:
        per_model.setdefault(model_name(v["model"]), []).append(v["thinking"])

    # ---- JUDGE
    judges = lock.judges()
    jt = lock.d["judge"].get("temperature")
    # the second judge as built (D153 Q8; audit 25 Oct FCV1): D85's repeat check passed (26 Oct 17:52, on the
    # Beelink; its record names the lock's second_model, this lock's sha256 and every one of its calibration answers
    # equal in two passes), and the one run built for it is S483's on G1, the six generation strategies (D142's scope
    # also names T2's answers, which no code runs yet). So the plate draws it on the generation strategies only; when
    # S483 runs another set, or the check record changes, the run stops.
    import lock_equiv
    j2 = json.loads(read_text(F["d85_check"]))
    need(len(judges) == 2 and j2.get("passed") is True and j2.get("model") == judges[1]
         and (j2.get("lock_sha256") == sha256_bytes(committed_bytes(LOCK))
              or (j2.get("lock_sha256") in lock_equiv.EQUIVALENT                  # D204: d66daa28 but for the
                  and sha256_bytes(committed_bytes(LOCK)) in lock_equiv.EQUIVALENT))  # second judge's machines
         and j2.get("full_sample") is True
         and j2.get("equal_scores") == j2.get("n"),
         f"{rel(F['d85_check'])}: not a passed D85 check of {judges[1:]} under this lock")
    j2_check = j2.get("n")
    j2_sets = sorted(set(re.findall(r'"S3_SET": "([^"]+)"', read_text(F["s483"]))))
    need(j2_sets == ["G1"], f"S483 runs the second judge on {j2_sets}, not G1 alone: redraw its scope")
    # the lowest thinking setting of each model whose 'off' variant is not thinking off (LOCK.toml [gemini]
    # thinking_off); every other 'off' variant must be think "off" in its [sampling.models] row
    g_low = dict(lock.d["gemini"]["thinking_off"])
    smod = lock.d["sampling"]["models"]
    for v in variants:
        m = model_name(v["model"])
        if v["thinking"] == "off" and m not in g_low:
            row = smod.get(m) or smod.get(m.partition(":")[0])
            need(row is not None and row.get("think") == "off",
                 f"{m}: an 'off' variant, but LOCK.toml [sampling.models] does not set think 'off' for it")

    # ---- GENERATE: the generation model (G1's, and T2's other generators; D160 (2) and (15) S2). T2's roster is
    # check_t2.py GENERATORS (the generators its checks admit) and must be the generators t2_lib.sh's case accepts;
    # T2 runs exp_01's six strategies (check_t2.py CONFIGS) on the 135 questions; its draws are the runner's Figure 2
    # draws, of which a generator's subset draws (check_t2.py subset_draws, run from its own source: a Gemini
    # generator's draws 2 and 3, a local generator's RLM set-ups at every draw, D175 Q3 and D176) run on D98's fixed
    # third (d98_subset.json).
    plan = json.loads(read_text(F["design_facts"]))["plan_csv"]          # D2: plan.csv's T2 row (feeds, status)
    t2 = plan.get("T2", {})
    t2_gens = t2_generators()
    t2_configs = module_const(F["check_t2"], "CONFIGS")
    need(sorted(t2_configs) == sorted(g1_strats), f"check_t2.py CONFIGS {t2_configs} are not exp_01's strategies")
    need(module_const(F["check_t2"], "N_QUESTIONS") == len(questions), "check_t2.py N_QUESTIONS is not the 135")
    case = re.search(r"case \$T2_GENERATOR in\n(.*?)\nesac", read_text(F["t2_lib"]), re.S)
    lib_gens = sorted(g for m in re.finditer(r"^\s*([a-z]+::[^\s)]+)\)", case.group(1) if case else "", re.M)
                      for g in m.group(1).split("|"))
    need(lib_gens == sorted(t2_gens), f"t2_lib.sh accepts {lib_gens}, check_t2.py GENERATORS {sorted(t2_gens)}")
    need(gen_model not in [model_name(g) for g in t2_gens], f"{gen_model} (G1) is also a T2 generator")
    # subset_draws(generator) until D175 Q3, subset_draws(config, generator) since (a local generator's RLM set-ups on
    # D98's third at every draw, D175 Q3 and D176): the signature read from the source, so the files at DESIGN_AT and
    # at HEAD both compile. Its globals are the module-level literals it names (module_const, which stops on one that
    # is not a literal), GENERATOR aside: every call here names the generator.
    ns = {"GENERATOR": None}
    module_functions(F["check_t2"], ["subset_draws"], ns)
    fn = ns["subset_draws"]
    for name in sorted(set(fn.__code__.co_names) & set(module_names(F["check_t2"])) - set(ns)):
        ns[name] = module_const(F["check_t2"], name)
    by_config = "config" in fn.__code__.co_varnames[:fn.__code__.co_argcount]
    d98 = json.loads(read_text(F["d98_subset"]))
    need(len(d98["ids"]) == d98["n"] and 3 * d98["n"] == len(questions) and set(d98["ids"]) <= {q["id"] for q in questions},
         f"d98_subset.json: {d98['n']} ids, not a third of the {len(questions)} questions")
    rlm_configs = tuple(c for c in t2_configs if c.startswith("rlm_"))
    t2_draws = {}
    for g in t2_gens:
        sub = {c: tuple(ns["subset_draws"](c, g) if by_config else ns["subset_draws"](g)) for c in t2_configs}
        kinds = {
            "3": all(v == () for v in sub.values()),
            "d98": all(v == (2, 3) for v in sub.values()),
            "rlm45": bool(rlm_configs) and all(v == ((1, 2, 3) if c in rlm_configs else ()) for c, v in sub.items())}
        kind = [k for k, ok in kinds.items() if ok]
        need(len(kind) == 1 and tuple(ex.draws(2)) == (1, 2, 3),
             f"T2 {g}: draws {ex.draws(2)}, subset draws by config {sub}: not 3 draws, D98's 1 + 2, nor 3 draws "
             f"with the RLM set-ups {rlm_configs} on D98's third")
        t2_draws[model_name(g)] = kind[0] if len(kind) == 1 else None
    d = drawn_design("T2", "replication")
    if d and "design to come" not in d["design"]:      # draws.csv T2 still had D9's placeholder on 27 Oct
        need(ints(d["design"])[:3] == [len(t2_gens), len(t2_configs), len(questions)],
             f"draws.csv T2 design {d['design']!r}, the T2 code: {len(t2_gens)} generators x {len(t2_configs)} "
             f"strategies x {len(questions)} questions")

    # ---- draws per drawn setting (panel b), from draws.csv's draws column: "3"; D98's one draw of every question
    # with draws 2 and 3 on a fixed third (G3's set-ups, G4, G5); or one draw ("1", or "1 (...)" whose note is not
    # D98's subset: G9's "1 (D98)", T1's "1 (draws 2 and 3 only if ...)"). The runner's DRAWS still gives 3 to Figures
    # 2 to 4, so it cannot say this. Each part's rows must all read one kind, else the run stops.
    def draw_kind(t):
        if t is None:
            return None
        return "3" if t == "3" else "d98" if t == D98_DRAWS else "1" if re.fullmatch(r"1( \(.*\))?", t) else None
    draws_by, draws_fig = {}, {}
    for part, keys in DRAW_PARTS:
        texts, figs = [], set()
        for plan_row, word in keys:
            dd = drawn_design(plan_row, word)
            texts.append(dd["draws"].strip() if dd else None)
            if dd:
                figs.add(dd["figure"].strip())
        kinds = {draw_kind(t) for t in texts}
        need(len(kinds) == 1 and None not in kinds, f"draws.csv draws for {part}: {texts!r}, want all '3', all "
             f"{D98_DRAWS!r} or all '1'")
        draws_by[part] = kinds.pop()
        draws_fig[part] = sorted({re.sub(r"^Fig ", "", f) for f in figs})
    # T2's generators (read from its code above, not from draws.csv's one T2 draws text, which gives D98's design to
    # every generator): the largest group by kind "the other generation models", each other group named
    by_kind = {}
    for m, k in t2_draws.items():
        by_kind.setdefault(k, []).append(m)
    if len(by_kind) == 1:
        draws_by["the generation models"] = next(iter(by_kind))
    else:
        groups = sorted(by_kind.items(), key=lambda kv: (len(kv[1]), str(kv[0])))
        need(len(groups[-1][1]) > len(groups[-2][1]), f"T2's generators: no one draw kind holds the most ({by_kind}): "
             "name them in S456")
        draws_by["the other generation models"] = groups[-1][0]
        for k_few, few in groups[:-1]:
            draws_by["generation model " + " and ".join(few)] = k_few
    t2_parts = [k for k in draws_by if "generation model" in k]       # placed after "generation strategy"
    order = [k for k in draws_by if k not in t2_parts]
    i = order.index("generation strategy") + 1 if "generation strategy" in order else len(order)
    draws_by = {k: draws_by[k] for k in order[:i] + sorted(t2_parts, key=lambda k: "other" not in k) + order[i:]}
    for k in t2_parts:
        draws_fig[k] = sorted({re.sub(r"^Fig ", "", f) for f in [t2.get("feeds", "")] if f})

    # ---- measures (panel a since D307) against the figures' legend drafts: every figure a measure names must name it, and no
    # other drawn figure may (the legend's own paragraph, from its "**Figure N |" or "**Supplementary Figure N" line)
    legend_text = {}
    for k, path in LEGENDS.items():
        t = read_text(path)
        head = r"^\*\*Supplementary Figure 2\b" if k.startswith("Supp") else rf"^\*\*Figure {k} \|"
        m = re.search(head, t, re.M)
        need(m is not None, f"{rel(path)}: no legend paragraph for figure {k}")
        legend_text[k] = t[m.start():] if m else ""
    for name, _, figs, rx, *_rest in MEASURES:
        named = sorted((k for k, t in legend_text.items() if re.search(rx, t, re.I)), key=list(LEGENDS).index)
        need(named == figs, f"measure {name!r}: panel a says figures {figs}, the legends name it in {named}")
    # the human ratings row (D183 FD7 a): the protocol's item count and scale
    proto = "\n".join(json.loads(read_text(F["design_facts"]))["s08b_protocol"]["lines"])   # D2
    m_items = re.findall(r"^- \*\*(\d+) items\*\*", proto, re.M)
    m_scales = re.findall(r"^- \*\*Scales\*\*: [^\n]*?(\d+) to (\d+) for ([^.\n]+?), plus notes", proto, re.M)
    need(len(m_items) == 1 and len(m_scales) == 1, f"{rel(F['design_facts'])} s08b_protocol: want one '**N items**' line and one "
         f"'**Scales**' line, found {len(m_items)} and {len(m_scales)}")
    hr_n = int(m_items[0]) if len(m_items) == 1 else None
    hr_lo, hr_hi, hr_all = (int(m_scales[0][0]), int(m_scales[0][1]), m_scales[0][2]) if len(m_scales) == 1 \
        else (None, None, "")
    proto_scales = [x.strip() for x in re.split(r",| and ", hr_all) if x.strip()]
    need(set(HUMAN_SCALES) <= set(proto_scales), f"{rel(F['design_facts'])} s08b_protocol: scales {proto_scales}, S456 names "
         f"{list(HUMAN_SCALES)}")

    if probs:
        stop("the design files disagree: " + "; ".join(p for p in probs if p))

    def gen_items():
        return [label(GEN_LABEL, c, "exp_01") for c in g1_strats]

    rows = [
        ("INDEX", "Corpus scale", len(core) * len(noise), f"{len(core)} {TIMES} {len(noise)}", SETTING_FIGURE["Corpus scale"], "G4",
         [SEP.join(map(str, core)) + f" core papers {TIMES} distractor ratio " + SEP.join(map(str, noise))],
         "exp_02 CORE_SIZES, NOISE_RATIOS; g4_lib.sh ORDER"),
        ("INDEX", "Embedding model", len(e1["results"]), f"{len(emb_models)} {TIMES} {len(emb_sizes)}",
         SETTING_FIGURE["Embedding model"], "",
         [f"{len(emb_models)} models {TIMES} {len(emb_sizes)} corpus sizes ({SEP.join(map(str, emb_sizes))} papers)",
          [m.split("/")[-1] for m in emb_models]],
         "exp01_embedding_latest.json config.models, config.corpus_sizes, results"),
        ("INDEX", "Chunking", len(e3["results"]), f"{len(c_cfg)} {TIMES} {len(c_runs)}",
         SETTING_FIGURE["Chunking"], "",
         [f"{len(c_cfg)} chunkings {TIMES} {len(c_runs)} query sets"]
         + [f"{kind} " + SEP.join(sizes) + f" {unit}" for (kind, unit), sizes in chunk_groups.items()],
         "exp03a_chunking_latest.json config.configs_tested, config.runs, results"),
        ("RETRIEVE", "Search strategy", len(e2["results"]), f"{len(s_cfg)} {TIMES} {len(s_sizes)}",
         SETTING_FIGURE["Search strategy"], "",
         [f"{len(s_cfg)} strategies {TIMES} the same {len(s_sizes)} corpus sizes",
          [label(SEARCH_LABEL, c, "exp02") for c in s_cfg]],
         "exp02_search_latest.json config.configs_tested, config.corpus_sizes, results"),
        ("RETRIEVE", "Retrieval depth", 2 * len(depths) + len(t1_caps) * len(t1_models),
         f"{len(depths)} {TIMES} 2 + {len(t1_caps)} {TIMES} {len(t1_models)}", SETTING_FIGURE["Retrieval depth"],
         "G5, G6, T1",
         [f"{len(depths)} turn caps {TIMES} 2 RLMs ({figure_names.MENTORI_RLM}, {figure_names.PACKAGE_RLM}), {gen_model}",
          SEP.join(map(str, depths)) + " turns",
          f"+ {len(t1_caps)} turn caps ({SEP.join(map(str, t1_caps))}) {TIMES} {len(t1_models)} local models, "
          f"{figure_names.MENTORI_RLM}", [model_name(m) for m in t1_models]],
         "exp_06 DEFAULT_DEPTHS; g5_lib.sh SMOKE_OPTS; run_rlm_ref.py FIGURE2_CAPS, DEPTH_SWEEP_CAPS; T1 "
         "assignment.toml models, depths, less check_t1.py HELD"),
        ("GENERATE", "Generation model", 1 + len(t2_gens), f"1 + {len(t2_gens)}",
         SETTING_FIGURE["Generation model"], "G1, T2",
         # D161 (4) N4 O-b: two lines like the other rows, the sum first, then T2's generators
         [f"{gen_model} + {len(t2_gens)} replication models", [model_name(g) for g in t2_gens]],
         "experiments_v4/exp_common.py GEN_MODEL (G1); T2_runs/check_t2.py GENERATORS (= t2_lib.sh's case), CONFIGS"),
        ("GENERATE", "Generation strategy", len(g1_strats) + 1 + len(cap2), f"{len(g1_strats)} + {1 + len(cap2)}",
         SETTING_FIGURE["Generation strategy"], "G1, G2, G6",
         [f"{len(g1_strats)} strategies + {1 + len(cap2)} reference arms", gen_items(),
          # D161 (4): the authors' caps as one item, so the reference arms fit one printed line (they took two)
          ["reference arms: " + label(GEN_LABEL, mb, "exp_01"),
           figure_names.PACKAGE_RLM + " at caps " + " ".join(str(c) for c in cap2)]],     # as Supplementary Figure 1; no comma (SEP)
         "exp_01 CONFIG_NAMES, MATCHED_BUDGET; run_rlm_ref.py FIGURE2_CAPS"),
        ("GENERATE", "System configuration", len(system), f"{len(system)}",
         SETTING_FIGURE["System configuration"], "G3",
         [[label(SYS_LABEL, c, "exp_03") for c in system]],
         "exp_03 CONFIG_NAMES (those not in ORCHESTRATOR_CONFIGS, and full_orchestrator); G3 preflight.sh WAVE1"),
        ("GENERATE", "Orchestrator set-up", len(orch_setups), f"{len(orch_run)} + {len(stress)}",
         SETTING_FIGURE["Orchestrator set-up"], "G3, G9",
         [f"{len(orch_run)} set-ups + {len(stress)} stress set-ups (not Mentor::i's default)",
          [label(ORCH_LABEL, c, "exp_03") for c in orch_run],
          ["stress: " + label(ORCH_LABEL, stress[0], "exp_03")] + [label(ORCH_LABEL, c, "exp_03") for c in stress[1:]]],
         "exp_03 ORCHESTRATOR_CONFIGS in G3 preflight.sh WAVE1, and STRESS_CONFIG_NAMES (G9)"),
        ("GENERATE", "Code-generation strategy", len(cg) * len(variants), f"{len(cg)} {TIMES} {len(variants)}",
         SETTING_FIGURE["Code-generation strategy"], "S2",
         [f"{len(cg)} strategies {TIMES} {len(variants)} model variants ({len(fig6_models)} models at their "
          f"thinking settings)", [lab for _, lab in s447_strats],
          [model_name(m) for m in fig6_models]],
         "exp_v2_8_coder_benchmark.py CONFIG_NAMES (labels: S447 STRATEGIES); exp_05 FIG6_MODELS, variants() on "
         "LOCK.toml"),
        ("JUDGE", "Judge model", len(judges), f"{len(judges)}", SETTING_FIGURE["Judge model"], "S3",
         [[f"{judges[0]} (main)"] + [f"{j} (second, on the generation strategies)" for j in judges[1:]]],
         "LOCK.toml [judge] model, second_model (lock.judges()); S483_d85_check/repro_check.json; S483 S3_SET G1"),
    ]
    facts = {"core": core, "noise": noise, "per_size": dict(ex.N_PER_SIZE), "g4_strats": len(g4_strats),
             "emb_models": emb_models, "chunk": e3["config"], "queries": q_emb[0],
             "queries_chunk": {run: v[0] for run, v in q_chunk.items()},
             "retrieval_dates": sorted({e1["timestamp"][:8], e2["timestamp"][:8], e3["timestamp"][:8]}),
             "depths": depths, "n86": n86, "cap2": list(cap2), "capd": list(capd), "rlms": rlms.group(1),
             "n_questions": len(questions), "gen_model": gen_model, "draws_fig": {k: list(v) for k, v in ex.DRAWS.items()},
             "matched_budget": mb, "system": system, "orch_setups": orch_setups, "orch_run": orch_run,
             "stress": list(stress), "wave2": w2, "t1_models": [model_name(m) for m in t1_models],
             "t1_held": sorted(t1_held), "t1_held_why": dict(sorted(t1_held.items())), "t1_caps": t1_caps, "t1_questions": t1_q, "judge2_sets": j2_sets,
             "draws_figures": draws_fig, "runs_once": runs_once,
             "n_ops": n_ops, "variants": len(variants), "per_model": per_model, "fig6_models": len(fig6_models),
             "judges": list(judges), "judge_temperature": jt, "judge2_check_n": j2_check,
             "t2_generators": [model_name(g) for g in t2_gens], "t2_providers": [g.partition("::")[0] for g in t2_gens],
             "t2_configs": len(t2_configs), "t2_draws": t2_draws, "d98_n": d98["n"],
             "rlm_configs": list(rlm_configs),
             "human_rating": {"items": hr_n, "scale": [hr_lo, hr_hi], "scales": list(HUMAN_SCALES),
                              "protocol_scales": proto_scales,
                              "figures": next(m[2] for m in MEASURES if m[0] == "Human rating")},
             # the providers of every model name the plate prints (a name without "provider::" is an Ollama tag)
             "providers": sorted({(m.partition("::")[0] if "::" in m else "ollama") for m in
                                  [module_const(F["v4_common"], "GEN_MODEL"), *t2_gens, *t1_models, *judges,
                                   *[v["model"] for v in variants]]}),
             "gemini_lowest": g_low, "t2_status": t2.get("status", "missing"), "cg": len(cg), "draws_by": draws_by,
             "runner_variants": len(runner_variants), "left_out": {model_name(v["model"]) + " " + v["thinking"]:
                                                                   left_out[v["extra"]] for v in runner_variants
                                                                   if v["extra"] in left_out}}
    return rows, facts


# the design fact taken at DESIGN_AT, not compared: plan.csv's T2 status is run status, recorded only in the
# provenance's not_drawn, and changes as T2 runs
PIN_ONLY = ("t2_status",)


def design_pinned():
    """design() on the design files as they stood at DESIGN_AT (audit 27 Oct F1). Its checks ran when DESIGN_AT was
    built; a stop here names DESIGN_AT."""
    global _PIN
    _PIN = True
    try:
        return design()
    finally:
        _PIN = False


def drawn_moved(rows, facts, pin_rows, pin_facts) -> list:
    """What the plate draws or records that differs between the files at HEAD and at DESIGN_AT: panel a's rows by axis,
    the design facts by key (PIN_ONLY aside). [] when equal."""
    out = []
    by_axis = {r[1]: r for r in rows}
    pin_by_axis = {r[1]: r for r in pin_rows}
    for ax in sorted(set(by_axis) | set(pin_by_axis)):
        if by_axis.get(ax) != pin_by_axis.get(ax):
            out.append(f"panel a row {ax!r}: HEAD {by_axis.get(ax)!r}, DESIGN_AT {pin_by_axis.get(ax)!r}")
    for k in sorted(set(facts) | set(pin_facts)):
        if k not in PIN_ONLY and facts.get(k) != pin_facts.get(k):
            out.append(f"design {k}: HEAD {facts.get(k)!r}, DESIGN_AT {pin_facts.get(k)!r}")
    return out


def reproduce(rows):
    """Known numbers first (README.md:75-79): the rows whose design did not change give the submitted plate's
    numerals (S162 STAGES), and the variant list gives Figure 6's 3,520 attempts as S447 counts them. Stops (exit 2)
    before anything is written."""
    old = {name: int(n) for _, axes in module_const(F["s162"], "STAGES") for name, n, _ in axes}
    mine = {r[1]: r[2] for r in rows}
    depth_as = next(r[3] for r in rows if r[1] == "Retrieval depth")      # "10 x 2 + 6 x 4": gemini's caps first
    checks = [("Corpus scale", mine["Corpus scale"], old["Corpus scale"]),
              ("Embedding model", mine["Embedding model"], old["Embedding model"]),
              ("Chunking", mine["Chunking"], old["Chunking"]),
              ("Search strategy", mine["Search strategy"], old["Search strategy"]),
              ("Retrieval depth (gemini-3-flash-preview's caps of one RLM)", ints(depth_as)[0], old["Retrieval depth"]),
              ("Generation strategy (the six, no reference arm)",
               len(module_const(F["exp_01"], "CONFIG_NAMES")), old["Generation strategy"])]
    variants, _ = fig6_variants()
    s447_v = [v for v, _, _ in module_const(F["s447"], "VARIANTS")]
    s447_total = len(module_const(F["s447"], "STRATEGIES")) * len(s447_v) * module_const(F["s447"], "N_OPS") * \
        module_const(F["s447"], "N_DRAWS")
    per_variant = len(module_const(F["v2_8"], "CONFIG_NAMES")) * module_const(F["exp_05"], "N_TASKS") * \
        len(ex.draws(6))
    cg_total = mine["Code-generation strategy"] * module_const(F["exp_05"], "N_TASKS") * len(ex.draws(6))
    s2 = [r for r in csv_rows(F["draws"]) if r["plan_row"] == "S2"]
    checks += [("Figure 6 runner variants (exp_05 variants() against S447 VARIANTS)",
                sorted(v["extra"] for v in variants), sorted(s447_v)),
               ("Figure 6 runner attempts (D71)", len(variants) * per_variant, s447_total),
               ("Figure 6 design attempts (D100, D116; draws.csv S2 answers)", cg_total,
                int(s2[0]["answers"]) if len(s2) == 1 else None)]
    bad = [f"{what}: {got!r}, known {want!r}" for what, got, want in checks if got != want]
    if bad:
        stop("reproduce-first failed, nothing written: " + "; ".join(bad))
    return [f"{what}: {got if not isinstance(got, list) else len(got)} = known" for what, got, _ in checks]


# ---------------------------------------------------------------------------------------------------------------
# The plate
# ---------------------------------------------------------------------------------------------------------------
FLOCK = tomllib.loads(read_text(FIGURE_LOCK))
PT_TEXT = 10.0                    # C11: larger type (editor row 17); inside [type] font_min_pt to font_max_pt (figure()).
#                                   11 until 5 Nov: Valerio, "1 point smaller (for the larger text) to regain some space"
PT_SMALL = float(FLOCK["type"]["font_min_pt"])    # the make-up's grey word line: the lock's floor, never under it
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER = "a" if FLOCK["type"]["panel_letter_case"] == "lowercase" else "A"
FONT = FLOCK["type"]["font_families"][0]
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])
W_MM = float(FLOCK["page"]["width_double_mm"])
H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
MM_PER_PT = 25.4 / 72
LETTER_B = "b" if LETTER == "a" else "B"
# D307 (Valerio, 8 Nov, Figure 1 alt2 adopted): panel a the three signals, panel b the settings by stage. So sheet Fig. 1a
# holds the signals' readouts and sheet Fig. 1b the settings (before D307 the other way round).
SHEET_SIG = f"Fig. {N}{LETTER}"
SHEET_SET = f"Fig. {N}{LETTER_B}"
COLUMNS_SET = ["stage", "axis", "levels", "levels_as", "factors", "line", "text", "n", "figure", "plan_row", "source"]
COLUMNS_SIG = ["name", "signal", "reference", "tool", "clause", "readout", "rated", "figure", "figure_printed", "text",
               "source"]
TOTAL_ON_PLATE = True             # C1: False takes the total off the plate; the legend's sentence stays
CALLS_LOWER_BOUND = True          # D212 Q7 (Valerio, 3 Nov): S520 frozen while runs continue, so the total is a lower bound;
                                  # refrozen 6 Nov (collects of 6 Nov 07:33Z) and 7 Nov after G5 D284 (collects of 7 Nov 05:27Z
                                  # to 05:35Z) with S520's MACHINES unchanged, so clones made
                                  # since 1 Nov are still not read and the total stays a lower bound
                                  # (plate '≥ n', legend 'At least n'); False once the real total is frozen at the end
PT_HEAD = 12.0                    # D307 (alt2): "Answer", the signal names and the totals line; inside [type] font_max_pt
PT_STAGE = 11.0                   # alt2: stage names; at 12 pt the PDF kerns "AT" in GENERATE 0.3 mm off the SVG (S448 R10)
# What each signal box prints under its rule, one line per measure row (alt2, 8 Nov): "measure" is the row's name without
# the signal's own word, "measure+clause1" adds the first part of its clause in brackets, "name" the row's name, "clause"
# its clause. A signal row (one with a signal) missing here stops the run.
READOUT = {"Judge correctness": "measure+clause1", "Judge refusal": "measure", "Judge faithfulness": "measure",
           "Concept recall": "name", figure_names.PAPERS_PRECISION: "clause"}
# Positions in mm (alt2, findings/recompute/fig1_alt_drafts/draw_fig1_alt2.py). Panel a: page edge, gap between the three
# signal boxes, the answer box, the signal boxes' height. Panel b: gap between stage boxes, inset, room before a numeral.
EDGE, GAP_A, ANS_W, ANS_H, BOX_A_H = 0.8, 4.6, 34.0, 9.0, 41.0
GAP_B, PAD_B, NUM_GAP = 6.0, 2.4, 2.5
LW_THIN, LW_LINE, LW_SIGNAL = 0.5, 1.0, 2.5   # the rule in a signal box; boxes, stem, fork and arrows; signal box borders
MIN_GAP_MM = 2.0                  # layout() stops when a setting's name and its numeral sit closer


def wcag_ratio(c1, c2):
    def lum(c):
        c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def grey_text(want):
    """want where it reaches [type] contrast_min_ratio on white, else the lightest grey that does (as S447)."""
    if wcag_ratio(want, "#FFFFFF") >= CONTRAST_MIN:
        return want
    return next((c for c in (f"#{v:02X}{v:02X}{v:02X}" for v in range(255, -1, -1))
                 if wcag_ratio(c, "#FFFFFF") >= CONTRAST_MIN), "#000000")


INK, GREY, WHITE, LINE_GREY = "#000000", grey_text("#595959"), "#FFFFFF", "#999999"   # house_style GREY text, line


def text_width_mm(s, bold=False, size=PT_TEXT):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    fp = FontProperties(family=FONT, size=size, weight="bold" if bold else "normal")
    return TextToPath().get_text_width_height_descent(s, fp, ismath=False)[0] * MM_PER_PT


def factor_words(axis, levels_as):
    """The grey word line under a make-up: one word per number, in order, with the same operators; refused otherwise."""
    words = FACTORS.get(axis)
    if words is None:
        stop(f"setting {axis!r} has no entry in FACTORS (Valerio, 2 November: one word per type under each make-up)")
    if re.sub(r"\d+", "#", levels_as) != re.sub(r"[A-Za-z][A-Za-z-]*", "#", words):
        stop(f"setting {axis!r}: make-up {levels_as!r} and words {words!r} do not match, number for word")
    return words


INK_FILL = "#EEEEEE"              # the stage boxes' head band (alt2), black text on it


def layout(rows, srows, total, answers, n_of=None):
    """Everything on the plate (D307, alt2), as a list of items in mm from the page's top left (a text's y is its
    centre line), with the two sheets. Items: "text", "line", "rect" (fill, edge, width) and "arrow". Panel a: the
    answer, one stem down that forks at right angles into three arrows, one per signal box (srows grouped by signal:
    name, reference, tool, a grey rule, one readout line per measure row). Panel b: the four stages left to right, each
    with its settings and number of levels, an arrow between stages; under them the totals line, answers and model
    calls. Returns items, {sheet: rows}, H, geometry. Stops when the plate passes [page] height_max_mm or panel b does
    not fit the page width."""
    items, sheet_set = [], []

    def text(x, y, s_, ha="left", color=INK, size=PT_TEXT, bold=False, tie=None):
        it = dict(kind="text", x=x, y=y, s=s_, ha=ha, color=color, size=size, bold=bold)
        if tie:
            it.update(sheet=tie[0], row=tie[1], fmt=tie[2])
        items.append(it)

    def line(xs, ys, lw, color=INK, cap="butt"):
        items.append(dict(kind="line", xs=xs, ys=ys, lw=lw, color=color, cap=cap))

    def rect(x, y, w, h, fc, ec, lw):
        items.append(dict(kind="rect", x=x, y=y, w=w, h=h, fc=fc, ec=ec, lw=lw))

    def arrow(x0, y0, x1, y1):
        items.append(dict(kind="arrow", xs=[x0, x1], ys=[y0, y1], lw=LW_LINE, color=INK))

    # the settings sheet, one row per logical line, then the two totals
    stages = []
    for stg, axis, levels, levels_as, fig, plan_row, logical, source in rows:
        words = factor_words(axis, levels_as)
        if not stages or stages[-1][0] != stg:
            stages.append((stg, []))
        stages[-1][1].append((axis, levels, len(sheet_set)))
        for j, it in enumerate(logical):
            sheet_set.append({"stage": stg, "axis": axis, "levels": levels, "levels_as": levels_as,
                              "factors": words if j == 0 else "", "line": j + 1,
                              "text": SEP.join(it) if isinstance(it, list) else it,
                              "n": (n_of or {}).get(axis, "") if j == 0 else "", "figure": fig, "plan_row": plan_row,
                              "source": source})
    sheet_set.append({"stage": "ALL", "axis": "Answers, whole study", "levels": None, "levels_as": "", "factors": "",
                      "line": 1, "text": f"{answers:,}", "n": "", "figure": f"Figure {N}", "plan_row": "",
                      "source": f"S492 {rel(F['s492_registry'])} today.total_counted"})
    total_text = (f"≥ {total:,}" if CALLS_LOWER_BOUND else f"{total:,}") if total is not None else "n"
    sheet_set.append({"stage": "ALL", "axis": "Model calls, whole study", "levels": None, "levels_as": "",
                      "factors": "", "line": 1, "text": total_text, "n": "", "figure": f"Figure {N}", "plan_row": "",
                      "source": "S520 figure1_legend_total"})

    # vertical layout (alt2)
    y_a, y_ans = 2.2, 1.0
    y_box = y_ans + ANS_H + 10.0
    y_b = y_box + BOX_A_H + 8.0
    y_st = y_b + 3.0
    n_max = max(len(r) for _, r in stages)
    st_h = 10.5 + 5.0 * n_max + 0.5
    y_total = y_st + st_h + 6.5
    H = round(y_total + 3.5, 1)
    if H > H_MAX_MM:
        stop(f"panels a and b need {H} mm, over [page] height_max_mm {H_MAX_MM}; no plate is drawn")

    # panel a: the answer and the three signals that read it, each on its own
    text(EDGE, y_a, LETTER, size=PT_LETTER, bold=LETTER_WEIGHT == "bold")
    wbox = (W_MM - 2 * EDGE - 2 * GAP_A) / 3
    xc = W_MM / 2
    rect(xc - ANS_W / 2, y_ans, ANS_W, ANS_H, WHITE, INK, LW_LINE)
    text(xc, y_ans + ANS_H / 2, "Answer", ha="center", size=PT_HEAD, bold=True)
    y_fork = y_ans + ANS_H + 4.0
    cxs = [EDGE + i * (wbox + GAP_A) + wbox / 2 for i in range(3)]
    line([xc, xc], [y_ans + ANS_H, y_fork], LW_LINE)
    line([cxs[0], cxs[-1]], [y_fork, y_fork], LW_LINE, cap="projecting")
    for cx in cxs:
        arrow(cx, y_fork, cx, y_box - 0.6)
    by = {}
    for i, m in enumerate(srows):
        by.setdefault(m["signal"], []).append(i)
    if list(by) != list(figure_names.SIGNALS):
        stop(f"panel {LETTER}'s signals are {list(by)}, want {list(figure_names.SIGNALS)} in that order")
    for k, sig in enumerate(figure_names.SIGNALS):
        x0 = EDGE + k * (wbox + GAP_A)
        first = srows[by[sig][0]]
        rect(x0, y_box, wbox, BOX_A_H, WHITE, INK, LW_SIGNAL)
        rect(x0, y_box, wbox, 3.0, INK, "none", 0)
        xi = x0 + 2.5
        text(xi, y_box + 8.2, sig, size=PT_HEAD, bold=True)
        text(xi, y_box + 13.6, first["reference"], tie=(SHEET_SIG, by[sig][0], "{reference}"))
        text(xi, y_box + 18.2, first["tool"], size=PT_SMALL, color=GREY, tie=(SHEET_SIG, by[sig][0], "{tool}"))
        line([xi, x0 + wbox - 2.5], [y_box + 21.6, y_box + 21.6], LW_THIN, LINE_GREY)
        for j, i in enumerate(by[sig]):
            text(xi, y_box + 26.4 + 5.0 * j, srows[i]["readout"], bold=True, tie=(SHEET_SIG, i, "{readout}"))
        widest = max(text_width_mm(srows[i]["readout"], bold=True) for i in by[sig])
        widest = max(widest, text_width_mm(first["reference"]), text_width_mm(first["tool"], size=PT_SMALL),
                     text_width_mm(sig, bold=True, size=PT_HEAD))
        if widest > wbox - 5.0:
            stop(f"signal box {sig!r}: a line {widest:.1f} mm wide does not fit the box's {wbox - 5.0:.1f} mm")
        if y_box + 26.4 + 5.0 * (len(by[sig]) - 1) + 3.0 > y_box + BOX_A_H:
            stop(f"signal box {sig!r}: {len(by[sig])} readouts do not fit its height")

    # panel b: the settings varied, by the stage they act on
    text(EDGE, y_b, LETTER_B, size=PT_LETTER, bold=LETTER_WEIGHT == "bold")
    need = []
    for st, rs in stages:
        w_row = max(text_width_mm(a_) + NUM_GAP + text_width_mm(str(v), bold=True) for a_, v, _ in rs)
        need.append(max(w_row, text_width_mm(st, size=PT_STAGE, bold=True)) + 2 * PAD_B)
    spare = W_MM - 2 * EDGE - (len(stages) - 1) * GAP_B - sum(need)
    if spare < 0:
        stop(f"panel {LETTER_B} needs {-spare:.1f} mm more than the page width")
    widths = [w + spare / len(need) for w in need]
    x0, gaps = EDGE, []
    for j, ((st, rs), w) in enumerate(zip(stages, widths)):
        rect(x0, y_st, w, st_h, WHITE, INK, LW_LINE)
        rect(x0, y_st, w, 8.0, INK_FILL, INK, LW_LINE)
        text(x0 + w / 2, y_st + 4.0, st, ha="center", size=PT_STAGE, bold=True)
        for k, (a_, v, row) in enumerate(rs):
            yk = y_st + 13.0 + 5.0 * k
            text(x0 + PAD_B, yk, a_)
            text(x0 + w - PAD_B, yk, str(v), ha="right", bold=True, tie=(SHEET_SET, row, "{levels}"))
            gaps.append((round(w - 2 * PAD_B - text_width_mm(a_) - text_width_mm(str(v), bold=True), 2), a_))
        if j < len(stages) - 1:
            arrow(x0 + w + 0.8, y_st + st_h / 2, x0 + w + GAP_B - 0.8, y_st + st_h / 2)
        x0 += w + GAP_B
    tight = min(gaps)
    if tight[0] < MIN_GAP_MM:
        stop(f"panel {LETTER_B}: {tight[1]!r} sits {tight[0]} mm from its numeral, under {MIN_GAP_MM}")
    # the totals line, centred: answers, a bar, model calls; each count tied to its row of the settings sheet
    if TOTAL_ON_PLATE:
        s_ans, s_calls = f"{answers:,} answers", f"{total_text} model calls"
        full = f"{s_ans} | {s_calls}"
        w_full = text_width_mm(full, bold=True, size=PT_HEAD)
        w_ans = text_width_mm(s_ans, bold=True, size=PT_HEAD)
        w_calls = text_width_mm(s_calls, bold=True, size=PT_HEAD)
        w_bar = text_width_mm("|", bold=True, size=PT_HEAD)
        xl = W_MM / 2 - w_full / 2
        text(xl, y_total, s_ans, size=PT_HEAD, bold=True, tie=(SHEET_SET, len(sheet_set) - 2, "{text} answers"))
        text(xl + w_ans + (w_full - w_ans - w_calls - w_bar) / 2, y_total, "|", size=PT_HEAD, bold=True)
        text(xl + w_full, y_total, s_calls, ha="right", size=PT_HEAD, bold=True,
             tie=(SHEET_SET, len(sheet_set) - 1, "{text} model calls"))
    return items, {SHEET_SIG: srows, SHEET_SET: sheet_set}, H, {
        "signal_boxes": [round(EDGE + k * (wbox + GAP_A), 2) for k in range(3)], "signal_box_w": round(wbox, 2),
        "stage_boxes_w": [round(w, 2) for w in widths], "y_signal_boxes": y_box, "y_stage_boxes": y_st,
        "tightest_gap_panel_b": tight[0]}


def draw(items, H, paths):
    """The plate from layout()'s items: one page axes in mm; each sheet-tied text gets a group id for S448 R8 (6).
    house_style.check_figure_colours, then S457.finish_plate writes the three files."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import house_style as hs
    import S457_fig2_panels as S457
    plt.rcParams.update({**S457.plate_rc("S456"), "font.size": PT_TEXT})
    fig = plt.figure(figsize=(W_MM / 25.4, H / 25.4), facecolor="#FFFFFF")
    pg = fig.add_axes([0, 0, 1, 1])
    pg.set_xlim(0, W_MM)
    pg.set_ylim(H, 0)
    pg.axis("off")
    printed = {}
    for it in items:
        if it["kind"] == "text":
            base = it["y"] + 0.36 * it["size"] * MM_PER_PT       # the baseline that centres cap height on the line
            t = fig.text(it["x"] / W_MM, 1 - base / H, it["s"], ha=it["ha"], va="baseline", fontsize=it["size"],
                         fontweight="bold" if it["bold"] else "normal", color=it["color"], family=FONT)
            if "fmt" in it:
                gid = f"s448num_{len(printed)}"
                t.set_gid(gid)
                printed[gid] = {"sheet": it["sheet"], "row": it["row"], "format": it["fmt"]}
        elif it["kind"] == "line":
            pg.plot(it["xs"], it["ys"], lw=it["lw"], color=it["color"], solid_capstyle=it["cap"], clip_on=False)
        elif it["kind"] == "rect":                               # a Rectangle, never a hatch (R1d a)
            pg.add_patch(Rectangle((it["x"], it["y"]), it["w"], it["h"], fc=it["fc"], ec=it["ec"], lw=it["lw"]))
        elif it["kind"] == "arrow":
            pg.annotate("", xy=(it["xs"][1], it["ys"][1]), xytext=(it["xs"][0], it["ys"][0]),
                        arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.3", lw=it["lw"],
                                        color=it["color"], shrinkA=0, shrinkB=0))
    bad = hs.check_figure_colours(fig)
    if bad:
        plt.close(fig)
        stop(f"colours outside the lock on the plate: {bad}")
    try:
        S457.finish_plate(fig, W_MM, H, paths, title=f"Figure {N}")
    except SystemExit as e:
        stop(str(e))
    return printed


# ---------------------------------------------------------------------------------------------------------------
# Legend, caption, Source Data
# ---------------------------------------------------------------------------------------------------------------
def say_list(xs):
    xs = [str(x) for x in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def signal_tool(f, signal):
    """What scores a signal, the line under its head (Valerio, 5 Nov: the heads parallel, in small letters on the next
    line): the judges from LOCK.toml [judge] (lock.judges()), the concept matcher, MiniCheck; "" for the lower row."""
    return {figure_names.JUDGE: ", ".join(f["judges"]), figure_names.CONCEPTS: "word matching",
            figure_names.PAPERS: "MiniCheck"}.get(signal, "")


def readout(m) -> str:
    """The line a measure row prints in its signal box (READOUT; alt2): its name, its name without the signal's word,
    that with the first part of its clause in brackets, or its clause; first letter upper case."""
    how = READOUT.get(m["name"])
    if how is None:
        stop(f"signal row {m['name']!r} has no READOUT entry (D307: every signal row prints one line in its box)")
    measure = m["name"].removeprefix(m["signal"]).strip()
    v = {"name": m["name"], "measure": measure, "clause": m["clause"],
         "measure+clause1": f"{measure} ({m['clause'].split(',')[0]})"}[how]
    return v[0].upper() + v[1:]


def signal_rows(f):
    """Panel a's rows (D307): one per measure of MEASURES that belongs to a signal (figures checked against the legends
    in design()), as the sheet's dicts, each with the readout line it prints. The measures outside the signals (human
    rating, execution, mean reciprocal rank) are not drawn since D307 and are recorded in the provenance's not_drawn.
    The draws (DRAW_KINDS, RUN_ONCE) are drawn by Supplementary Figure 1 since D183 FD6 B (draw_kinds_record())."""
    out = []
    for name, text, figs, _, signal, reference, clause, rated in MEASURES:
        if not signal:
            continue
        printed = ("Supp. Fig. " + ", ".join(x.replace("Supp. ", "") for x in figs)) if figs[0].startswith("Supp") \
            else "Fig. " + ", ".join(figs)
        m = {"name": name, "signal": signal, "reference": reference, "tool": signal_tool(f, signal), "clause": clause,
             "rated": rated, "figure": ", ".join(figs), "figure_printed": printed, "text": text,
             "source": "S456 MEASURES and READOUT; legend drafts of Figure " + ", ".join(figs)}
        m["readout"] = readout(m)
        out.append(m)
    return out


def not_drawn_measures() -> list:
    """The measures of MEASURES outside the signals, not drawn since D307."""
    return [m[0] for m in MEASURES if not m[4]]


def draw_kinds_record(f) -> list:
    """The draws block as Supplementary Figure 1 draws it (D183 FD6 B): each draw kind in use, its name and what it
    means, the settings of that kind (draws_by) and, last, the retrieval settings' 1 run (RUN_ONCE)."""
    out = [{"key": kind, "name": name, "means": means, "settings": [p for p, k in f["draws_by"].items() if k == kind]}
           for kind, name, means in DRAW_KINDS if kind in f["draws_by"].values()]
    return out + [{"key": "run", "name": RUN_ONCE[0], "means": RUN_ONCE[1], "settings": list(f["runs_once"])}]


def drawn_sentence(f):
    """What the code-generation row draws, one sentence (D154: what is drawn, not why a variant is not)."""
    return (f"Code-generation strategy draws the {f['variants']} model variants of Figure {figure_names.FIG_CODE}'s design "
            f"({f['fig6_models']} models; scripts/S447_fig6_panels.py). ")


def local_rlm_clause(f) -> str:
    """E7 (n per setting) after D175 Q3 and D176: the count of T2 generators whose RLM set-ups answer only D98's fixed
    third (draw kind "rlm45"), with their n; "" when none does. The draws are Supplementary Figure 1's (D183 FD6 B)."""
    few = [m for m, k in f["t2_draws"].items() if k == "rlm45"]
    if not few:
        return ""
    return f" ({len(few)} of them: n = {f['d98_n']} with the {len(f['rlm_configs'])} RLM strategies)"


def s520_total():
    """S520's "figure1_legend_total" from its committed summary, or None while the file is not committed (the plate then
    prints the slot). Refused when the summary left a machine unread or holds no count above 0."""
    p = F["s520_summary"]
    if in_git():                         # cat-file, as committed_bytes (which stops on a missing file); S494's read audit
        r = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel(p)}"], cwd=ROOT, capture_output=True)   # allows it
        if r.returncode != 0:
            return None
        raw = r.stdout
    elif p.exists():
        raw = p.read_bytes()
    else:
        return None
    got = json.loads(raw)
    total = got.get("figure1_legend_total")
    if got.get("machines_not_read") or not isinstance(total, int) or total <= 0:
        stop(f"{rel(p)}: figure1_legend_total {total!r}, machines not read {got.get('machines_not_read')!r}")
    return total


def s1_prints_calls() -> bool:
    """True when frozen_inputs/SHA256SUMS at HEAD lists S520's inputs, which is when S496 prints calls per box."""
    sums = ROOT / "findings" / "recompute" / "frozen_inputs" / "SHA256SUMS"
    return b"findings/recompute/S520_inputs/" in committed_bytes(sums)


def calls_sentence(total) -> str:
    """The legend's sentence on the total (C1), for what S520's rules count: run tier only; checks, smokes and the three
    dropped models (nemotron by D116; deepseek-r1:70b and glm-4.7-flash:bf16 by D265, S520 DROPPED_RUNS) sit outside it
    (rule 7), April's work has no call logs (rule 8)."""
    # Valerio, 8 Nov evening ("too long"): the clause after the answer count, without the counting date (the date
    # stays in S520's summary and in the Source Data caption's total row)
    head = (f"at least {total:,} model calls" if CALLS_LOWER_BOUND else f"{total:,} model calls") \
        if total is not None else "the model calls"
    tail = "; Supplementary Figure 1 gives them per experiment" if s1_prints_calls() else ""
    return f"{head}, excluding those runs and checks, smoke tests and dropped models{tail}."


def answers_sentence(answers) -> str:
    """The legend's sentence on the answer count under panel b (D307): S492's unit, one generation row per question,
    configuration and draw, every stored draw counted, plus the April model-selection and retrieval rows it keeps."""
    return f"{answers:,} answers, all draws, including the model-selection and retrieval runs;"


def s492_answers() -> int:
    """S492's today.total_counted from its committed registry (D307: the answer count under panel b); refused when the
    file is not committed or the count is not a positive integer."""
    got = json.loads(committed_bytes(F["s492_registry"]))
    n = (got.get("today") or {}).get("total_counted")
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        stop(f"{rel(F['s492_registry'])}: today.total_counted is {n!r}, not a positive count")
    return n


def setting_n(f) -> dict:
    """The n behind each setting of panel b, by setting name, for sheet SHEET_SET's "n" column (first line of each
    setting). Valerio, 8 Nov evening: the legend's per-setting n list moved here, word for word, and since 8 Nov 20:45Z
    (editor row 45: an n only where statistics are derived) the legend gives no n for Figure 1. The judge model has no n of its own: it scores the other settings'
    answers."""
    chunk_q = f["queries_chunk"]
    retr = f"n = {f['queries']} retrieval queries"
    gen = (f"n = {f['n_questions']} questions with the main generation model, and with each of the "
           f"{len(f['t2_generators'])} other generation models on the {f['t2_configs']} generation "
           f"strategies{local_rlm_clause(f)}")
    return {"Embedding model": retr, "Search strategy": retr,
            "Chunking": f"{retr} ({len(chunk_q)} query sets of n = {say_list(chunk_q.values())})",
            "Corpus scale": (f"n = {f['n_questions']} questions asked at every index and the questions in scope at each "
                             f"size (n = {say_list(f['per_size'][c] for c in f['core'])} at {say_list(f['core'])} "
                             f"core papers)"),
            "Retrieval depth": (f"n = {f['n86']} questions at each turn cap with the main generation model and "
                                f"n = {f['t1_questions']} with each local model"),
            "Generation model": gen, "Generation strategy": gen, "System configuration": gen,
            "Orchestrator set-up": gen,
            "Code-generation strategy": (f"n = {f['n_ops']} operations per strategy and model variant (a model at one "
                                         f"thinking setting)")}


def legend_and_caption(rows, f, stamp, tag, total, answers):
    A, B = f"**{LETTER}**", f"**{LETTER_B}**"
    # a model whose 'off' variant is its lowest thinking setting (LOCK.toml [gemini] thinking_off) is grouped and
    # described apart from the models whose 'off' is thinking off (S447's legend: "at their lowest setting")
    low = f["gemini_lowest"]
    by_settings = {}
    for m, t in f["per_model"].items():
        by_settings.setdefault((tuple(t), "off" in t and m in low), []).append(m)
    multi = []
    for (t, lowest), ms in by_settings.items():
        if len(t) < 2:
            continue
        if lowest:
            # D153 Q8 (b): named as Figure 6 names it (D138: "Call gemini off as low"; S481: "Gemini low: the
            # lowest thinking setting the model allows"), not by the values LOCK.toml [gemini] thinking_off sends
            ts = [x if x != "off" else "low" for x in t]
            multi.append(f"{say_list(ms)} at {say_list(ts)} (low: the lowest thinking setting the model allows)")
        else:
            multi.append(f"{say_list(ms)} at {say_list(t)}")
    n_single = sum(len(ms) for (t, _), ms in by_settings.items() if len(t) == 1)
    total_source = ("The total of LLM calls is pending: S520's summary is not committed. " if total is None else
                    "The total of LLM calls is S520's committed summary"
                    + (". " if s1_prints_calls() else ", whose call-log inputs are not frozen yet, so its report cannot "
                       "be rerun from the repository and the count stops at the day the logs were read. "))
    prov = (f"Provisional. "
            f"{drawn_sentence(f)}"
            f"Thinking settings: {'; '.join(multi)}; the other {n_single} models at their default. "
            f"Retrieval depth's local models are T1's {len(f['t1_models'])} ({say_list(f['t1_models'])})"
            + t1_out_sentence(f["t1_held_why"]) + ". "
            f"The second judge, {f['judges'][1]}, scores the answers of the generation strategies (G1) at the main "
            f"judge's settings (LOCK.toml [judge]) and gives the same score twice on {f['judge2_check_n']} of "
            f"{f['judge2_check_n']} calibration answers (D85). "
            f"Panel {LETTER} leaves out RAGAS and RAGChecker: D136 Q6 moved them to a Supplementary figure, and D33 "
            f"shows RAGAS only if Figure {figure_names.FIG_SIGNALS} uses it. Since D307 panel {LETTER} draws the three "
            f"signals alone, without {say_list(m.lower() for m in not_drawn_measures())}. The answer count is S492's "
            f"committed registry (today.total_counted). {total_source}")
    # Valerio, 22 Oct (figures review): the legend is written as for the complete figure, under the journal's 350
    # words, with no sentence on what is not drawn or not run yet; that state stays in the data stamp and in the
    # Source Data caption (prov). Valerio, 23 Oct: the legend describes the image only (what each line means, the n
    # behind each setting). D307 (Valerio, 8 Nov): alt2's legend (findings/recompute/fig1_alt_drafts/legend_alt2.md),
    # panel a the signals, panel b the settings and the totals line. Valerio, 8 Nov evening ("too long"; his own
    # text, with O1 scopes, O2 n clause, O3 sentence split): the per-setting n list moved to sheet SHEET_SET's "n"
    # column (setting_n), and the derivation pointer, the stress set-up and second-judge sentence and the counting
    # date left the legend; the plate's panel b still marks the stress set-ups and the second judge.
    # Valerio, 8 Nov 20:40Z: no "n = " tag in any legend; each count once, in plain words, with its unit.
    # Valerio, 8 Nov 20:45Z (editor row 45): an n only on a panel that shows derived statistics. Figure 1 shows none,
    # so it carries no n and no count added only to give one: the 244-questions sentence and its Source Data pointer
    # left the legend (the per-setting n stays in sheet SHEET_SET's "n" column and the Source Data caption).
    legend = (
        f"{A}, Each answer is read by three signals, each against its own reference and reported on its own; under "
        f"each, the tool that scores it and its readouts. Judge: correctness, pass at a score of 4 or more; refusal of an "
        f"out-of-scope question, refused at 3 or more; faithfulness, scored without or with the retrieved passages. "
        f"Concepts: share of the key's expected concepts found in the answer; a concept's content words that also "
        f"occur in the question are not counted. Papers: MiniCheck's share of the answer's claims supported by the "
        f"key's source papers. "
        f"{B}, The settings varied, by the pipeline stage they act on: indexing (INDEX), retrieval (RETRIEVE), generation "
        f"(GENERATE) and judging (JUDGE). Each number is a setting's number of levels. "
        f"{answers_sentence(answers)} {calls_sentence(total)} Supplementary Table 2 names the models.")
    title = "The three signals that read every answer, and what the study varied"
    lines = [f"# Figure {N}, title and legend (draft)", "",
             f"Written by `scripts/S456_fig1_design.py figure` from the design files. Data stamp: {stamp}.", "",
             f"**Figure {N} | {title}.** {legend}", ""]
    cap = [f"# Source Data Fig. {N}, caption", "",
           (f"**Source Data Fig. {N} | The measures and configurations drawn in Figure {N}.** {prov}Data stamp: "
            f"{stamp}. Sheet {SHEET_SIG}: one row per readout of panel {LETTER}: its name, signal, reference, the tool "
            f"that scores it, its clause, the readout line printed in its signal's box, whether the expert ratings check "
            f"it, the figures that report it, those figures as printed, its full definition and where it is read from. "
            f"Sheet {SHEET_SET}: one row per logical line of panel {LETTER_B}'s setting: its stage, setting, number of "
            f"levels, how that number is made up, the word for each factor, the line's text, the n behind the setting (on its "
            f"first line; the judge model has none of its own), the figure that reports the "
            f"setting, the plan row of its run and the design files it is read from; the last two rows hold the totals "
            f"printed under the stages, the answers (S492) and the model calls (S520). Generated by "
            f"`uv run --frozen python scripts/S456_fig1_design.py figure`."), "",
           f"Proposed Data Availability sentence: \"The source data for Figure {N} is in Supplementary Data {N + 1}.\"",   # D303 (D302)
           ""]
    return "\n".join(lines), "\n".join(cap)


def write_source_data(sheets, path):
    """sheets: {sheet name: (columns, rows)}, one sheet per panel."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, (cols, rows_) in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rows_:
            ws.append([r[c] for c in cols])
    # byte-reproducible: openpyxl's save writes the time of saving twice (docProps/core.xml dcterms:created and
    # dcterms:modified, the latter set to now inside save_workbook; and every zip member's date). The workbook is
    # rewritten member by member with the zip's earliest date and without the two core-property times, so a re-run on
    # the same inputs gives the same sha256 and figure1_provenance.json changes only when a cell does.
    import io
    import zipfile
    buf = io.BytesIO()
    wb.save(buf)
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as zin, \
            zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = re.sub(rb"<dcterms:(created|modified)\b[^>]*>[^<]*</dcterms:\1>", b"", data)
                if b"dcterms:created" in data or b"dcterms:modified" in data:
                    stop("Source Data workbook: a creation or modification time is left in docProps/core.xml")
            zi = zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, info.external_attr
            zout.writestr(zi, data)


def t1_out_sentence(held: dict) -> str:
    """Audit 27 Oct F14 (fig1_2_5): of check_t1.py HELD, the caption names only a model a decision put out of T1 (its
    reason reads "out of T1", e.g. D121 for gpt-oss:20b), as design; the other entries are steps pending before admit
    (D83 Q167, Q181), run status that D154 keeps out of the caption, and are recorded in the provenance's
    design.t1_held_why."""
    out = {m: (re.match(r"(D\d+)", why) or [None])[0] for m, why in held.items() if "out of T1" in why}
    if not out:
        return ""
    return "; " + "; ".join(f"{m} is out of T1 by design ({d})" if d else f"{m} is out of T1 by design"
                            for m, d in out.items())


def figure(argv):
    if FLOCK.get("status") != "agreed":
        stop(f"{rel(FIGURE_LOCK)} status {FLOCK.get('status')!r}, not 'agreed' (D87): no plate is drawn")
    if not float(FLOCK["type"]["font_min_pt"]) <= PT_TEXT <= float(FLOCK["type"]["font_max_pt"]):
        stop(f"PT_TEXT {PT_TEXT} is outside [type] font_min_pt to font_max_pt")
    check_inputs()
    rows, facts = design()                  # every check and tripwire on the files at HEAD
    reproduced = reproduce(rows)            # at HEAD too
    # audit 27 Oct F1 (corrected 27 Oct, part 4): what the plate draws is also computed from the design files at
    # DESIGN_AT, whose sha256 inputs_sha256 records, and must be equal
    pin_rows, pin_facts = design_pinned()
    moved = drawn_moved(rows, facts, pin_rows, pin_facts)
    if moved:
        stop(f"the design files at HEAD give the plate other values than at DESIGN_AT {DESIGN_AT}, whose sha256 the "
             f"provenance records: {'; '.join(moved)} (move DESIGN_AT to a commit that holds the new design, then "
             f"S494 --write)")
    facts.update({k: pin_facts[k] for k in PIN_ONLY})
    # D155: the stamp names the inputs by their sha256, not by the repository's HEAD, its uncommitted changes or a
    # write time, so the same committed inputs give the same caption, legend draft, numbers and provenance on any
    # machine. inputs_digest is the sha256 of the inputs' "<sha256>  <name>" lines, sorted by name (sha256sum style).
    total = s520_total()
    inputs = {input_name(p): input_sha256(p) for p in [LOCK, FIGURE_LOCK, *F.values()]
              if p != F["s520_summary"] or total is not None}
    digest = sha256_bytes("".join(f"{h}  {k}\n" for k, h in sorted(inputs.items())).encode())
    tag = " (provisional, 2 of 2)"
    if total is None and "provisional" not in tag:
        stop("the total of LLM calls is still a slot: a plate with a final name cannot print it")
    answers = s492_answers()
    srows = signal_rows(facts)
    stamp = (f"PROVISIONAL: 2 of 2 panels (panel {LETTER}, the signals; panel {LETTER_B}, the design), "
             f"{len(rows)} settings read from the design files"
             + (", total of LLM calls pending" if total is None else "") + f" (inputs sha256 {digest[:12]})")
    items, sheets, H, geom = layout(rows, srows, total, answers, setting_n(facts))
    cols = {SHEET_SIG: COLUMNS_SIG, SHEET_SET: COLUMNS_SET}
    OUT.mkdir(parents=True, exist_ok=True)
    for old in list(OUT.glob(f"Figure {N}*")) + list(OUT.glob(f"Source Data Fig. {N}*")):
        old.unlink()
    paths = {x: OUT / f"Figure {N}{tag}.{x}" for x in ("pdf", "svg", "png")}
    printed = draw(items, H, paths)
    sd = OUT / f"Source Data Fig. {N}{tag}.xlsx"
    write_source_data({k: (cols[k], v) for k, v in sheets.items()}, sd)
    numbers = OUT / f"figure{N}_numbers.json"
    numbers.write_text(json.dumps({
        "stamp": stamp, "what": f"every value Figure {N} prints, as Source Data Fig. {N} holds it (S448 R8)",
        "sheets": {k: {"columns": cols[k], "rows": [[r[c] for c in cols[k]] for r in v]} for k, v in sheets.items()},
        "printed": printed,
        "printed_what": "every numeral and level line printed on the plate: the SVG group id of its text and the "
                        "Source Data row and format it is written from (S448 R8 (6))"}, indent=1) + "\n")
    legend, cap = legend_and_caption(rows, facts, stamp, tag, total, answers)
    (OUT / "legend_draft.md").write_text(legend)
    capf = OUT / f"Source Data Fig. {N} caption{tag}.md"
    capf.write_text(cap)
    prov = {"script": "scripts/S456_fig1_design.py", "script_sha256": sha256_file(Path(__file__)),
            "command": "uv run --frozen python scripts/S456_fig1_design.py " + " ".join(argv),
            "python": platform.python_version(),
            "inputs_read": "every file at its committed version (the blob at git HEAD; the file itself outside a "
                           "git checkout), every check and tripwire on those; each design file (DESIGN_FILES) read "
                           f"again as it stood at DESIGN_AT {DESIGN_AT} (git cat-file), its sha256 there recorded "
                           f"in inputs_sha256 under a name carrying @{DESIGN_AT}, and every value drawn or recorded "
                           "from them required equal at HEAD and at DESIGN_AT (plan.csv's T2 status taken at "
                           f"DESIGN_AT); the files read through an import (" + ", ".join(IMPORTED) + ") required "
                           "equal to HEAD, and the "
                           "definitions S456 uses from experiment.py, lock.py and run_rlm_ref.py (IMPORT_USES) "
                           f"required the same at HEAD as at {DESIGN_AT}; the submitted retrieval runs from the "
                           "committed frozen set "
                           f"{UPSTREAM_SET} (findings/recompute/{UPSTREAM_SET}_inputs, checked against "
                           "findings/recompute/frozen_inputs/SHA256SUMS). S520's summary is read at HEAD for its "
                           "total alone, and recorded while committed. No write time, HEAD or working-copy state is "
                           "recorded (D155).",
            "inputs_sha256": inputs, "inputs_digest": digest, "model_calls": 0,
            "lock": {"path": rel(LOCK), "sha256": inputs[rel(LOCK)]},
            "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": inputs[rel(FIGURE_LOCK)], "status": FLOCK["status"]},
            "reproduced": reproduced, "stamp": stamp, "page_mm": [W_MM, H], "geometry_mm": geom,
            "type_pt": {"panel letter (bold)": PT_LETTER, "the tool line in a signal box": PT_SMALL,
                        "answer, signal names and the totals line": PT_HEAD, "stage names": PT_STAGE,
                        "all other text": PT_TEXT},
            "font": FONT, "colours": {"text, box borders, stem, fork, arrows and signal bands": INK,
                                      "box fills": WHITE, "the tool line": GREY, "the rule in a signal box": LINE_GREY,
                                      "stage head bands": INK_FILL},
            "llm_calls_total": total, "answers_total": answers,
            "design": {k: v for k, v in facts.items()},
            "rows": [{"stage": r[0], "axis": r[1], "levels": r[2], "levels_as": r[3], "figure": r[4],
                      "plan_row": r[5], "source": r[7]} for r in rows],
            "panel_a": [{"name": b["name"], "signal": b["signal"], "readout": b["readout"], "figure": b["figure"],
                         "source": b["source"]} for b in srows],
            # D183 FD6 B: the draws block, drawn by Supplementary Figure 1 (S496 reads this field)
            "draw_kinds": draw_kinds_record(facts),
            "not_drawn": {"RAGAS and RAGChecker": "D136 Q6 (Fig5.Q1 O-a): a Supplementary figure; D33 shows RAGAS "
                                                  f"only if Figure {figure_names.FIG_SIGNALS} uses it",
                          "distiller set-ups": f"G3 wave 2 ({', '.join(facts['wave2'])}): D154 as amended, Rule 12's "
                                               f"zero branch (distiller count 0 on the full pipeline's draw 1)",
                          "draws": "D183 FD6 B: the draws per setting are drawn in Supplementary Figure 1 "
                                   "(scripts/S496_supp_fig1_experiment_graph.py, from draw_kinds)",
                          "published and simple evaluators": "D183 FD7 a: no panel a row (D136 Q6)",
                          "measures outside the signals": f"D307 (alt2): {', '.join(not_drawn_measures())} not drawn; "
                                                          "panel a draws the three signals alone"}}
    prov["files"] = {p.name: sha256_file(p) for p in [*paths.values(), sd, capf, numbers, OUT / "legend_draft.md"]}
    (OUT / f"figure{N}_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    print("reproduced: " + "; ".join(reproduced))
    print(stamp)
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W_MM:g} x {H:g} mm), {sd.name}, {capf.name}, "
          f"{numbers.name}, legend_draft.md, figure{N}_provenance.json into {rel(OUT)}")
    for r in rows:
        print(f"  {r[0]:9s} {r[1]:25s} {r[2]:>4}  ({r[3]})  {r[7]}")


def selftest():
    """D155's checks, each on a throwaway copy: (1) a committed file is read at HEAD, not as edited; an uncommitted or
    outside file is refused; (2) an import-read file that differs from HEAD is caught; (3) an altered frozen copy of a
    submitted retrieval run is refused; (4) two builds are byte-equal and no output names HEAD or a write time; (5) a
    design file is read at HEAD by the checks and at the pinned commit by design_pinned() and for inputs_sha256, a
    drawn value that differs between the two stops the run, and an imported design file passes a later commit only
    when the definitions used are unchanged (audit 27 Oct F1, corrected 27 Oct, part 4); (6) a legend draft is read
    at HEAD, and from the working tree only under LEGENDS_AT "worktree" (S494 --write; audit 27 Oct F1b); (7) the plate as
    D307 (alt2) draws it: panel a the three signal boxes, black-bordered, Judge, Concepts and Papers
    left to right, one arrow from the answer's fork into each, every readout tied to sheet Fig. 1a; panel b the stages in
    pipeline order with black borders and arrows, every setting with its levels tied to sheet Fig. 1b, the totals line
    answers then model calls; the words refused when they do not match the make-up; (8) with no committed S520 summary
    the total is the slot "n model calls", and the stamp says it is pending."""
    import shutil
    import tempfile
    global OUT
    res = []

    def refused(fn):
        try:
            fn()
        except (SystemExit, FrozenInputError):
            return True
        return False

    with tempfile.TemporaryDirectory(prefix="S456_selftest_") as td:
        td = Path(td)
        repo = td / "repo"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)   # noqa: E731
        g("init", "-q")
        (repo / "a.txt").write_text("committed\n")
        g("add", "a.txt")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t")
        (repo / "a.txt").write_text("edited\n")
        (repo / "b.txt").write_text("untracked\n")
        res.append(("(1) a tracked file edited in the working copy is read at HEAD",
                    committed_bytes(repo / "a.txt", repo) == b"committed\n"))
        res.append(("(1) an untracked file is refused", refused(lambda: committed_bytes(repo / "b.txt", repo))))
        res.append(("(1) a file outside the repository is refused",
                    refused(lambda: committed_bytes(td / "outside.txt", repo))))
        res.append(("(2) an import-read file that differs from HEAD is caught",
                    imported_dirty(repo, ["a.txt"]) == ["a.txt"]))
        (repo / "a.txt").write_text("committed\n")
        res.append(("(2) and passes once it equals HEAD", imported_dirty(repo, ["a.txt"]) == []))
        # (5) audit 27 Oct F1: a design file is read at the pinned commit, and an imported one passes a later commit
        # that leaves the definitions used alone, and stops at one that changes them
        mod = repo / "mod.py"
        mod.write_text("X = 1\n\n\ndef f():\n    return X\n\n\ndef g():\n    return 2\n")
        g("add", "mod.py")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c1")
        c1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
        mod.write_text("X = 1\n\n\ndef f():\n    return X\n\n\ndef g():\n    return 3\n")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "c2")
        _BLOBS.clear()
        res.append(("(5) a file is read at the pinned commit, not at a later HEAD",
                    b"return 2" in committed_bytes(mod, repo, c1) and b"return 3" in committed_bytes(mod, repo)))
        res.append(("(5) a later commit that changes only a definition not used passes",
                    imports_unchanged(repo, c1, {mod: ("f",)}) == []))
        mod.write_text("X = 5\n\n\ndef f():\n    return X\n\n\ndef g():\n    return 3\n")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "c3")
        _BLOBS.clear()                            # the cache holds HEAD's blobs by name; HEAD moved
        res.append(("(5) a later commit that changes a definition the used one reaches is refused",
                    imports_unchanged(repo, c1, {mod: ("f",)}) != []))
        # (5) part 4: the checks read HEAD; only design_pinned() and inputs_sha256 read DESIGN_AT
        global _PIN
        res.append(("(5) a design file is read at HEAD outside design_pinned()",
                    at_of(F["exp_01"]) == "HEAD" and at_of(F["g4_lib"]) == "HEAD"))
        global LEGENDS_AT
        res.append(("(6) a legend draft is read at HEAD by default", at_of(LEGENDS["2"]) == "HEAD"))
        LEGENDS_AT = "worktree"
        try:
            leg = (at_of(LEGENDS["2"]), at_of(F["exp_01"]), recorded_at(LEGENDS["2"]), input_name(LEGENDS["2"]))
        finally:
            LEGENDS_AT = "HEAD"
        res.append(("(6) under S494 --write (LEGENDS_AT worktree) a legend draft is read and recorded from the "
                    "working tree, under its plain name; a design file is not", leg == (
                        "WORKTREE", "HEAD", "WORKTREE", frozen_label(LEGENDS["2"]))))
        _PIN = True
        try:
            pinned_at = (at_of(F["exp_01"]), at_of(LOCK))
        finally:
            _PIN = False
        res.append(("(5) inside design_pinned() a design file is read at DESIGN_AT, any other file at HEAD",
                    pinned_at == (DESIGN_AT, "HEAD")))
        res.append(("(5) inputs_sha256 records a design file at DESIGN_AT, any other file at HEAD",
                    input_name(F["exp_01"]).endswith(f"@{DESIGN_AT}") and recorded_at(LOCK) == "HEAD"))
        r_ = [("INDEX", "Corpus scale", 12)]
        res.append(("(5) drawn_moved: equal rows and facts pass, a T2 status change alone passes",
                    drawn_moved(r_, {"core": [1], "t2_status": "done"}, r_, {"core": [1], "t2_status": "running"})
                    == []))
        res.append(("(5) drawn_moved: a changed row or fact is named",
                    len(drawn_moved([("INDEX", "Corpus scale", 13)], {"core": [2]}, r_, {"core": [1]})) == 2))
        # (7) and (8): the plate's items, on the design at HEAD (D307, alt2)
        rows7, facts7 = design()
        srows7 = signal_rows(facts7)
        items7, sheets7, H7, _ = layout(rows7, srows7, 1234567, 51441)
        texts7 = [it for it in items7 if it["kind"] == "text"]
        letters7 = {it["s"]: it["y"] for it in texts7 if it["size"] == PT_LETTER and it["s"] in (LETTER, LETTER_B)}
        sig7 = [it for it in texts7 if it["s"] in figure_names.SIGNALS and it["size"] == PT_HEAD]
        boxes7 = [it for it in items7 if it["kind"] == "rect" and it["lw"] == LW_SIGNAL]
        stage7 = [it for it in texts7 if it["size"] == PT_STAGE]
        res.append(("(7) panel a the three signals, panel b the settings: letter a above the signal boxes, letter b "
                    "between them and the stage boxes",
                    set(letters7) == {LETTER, LETTER_B}
                    and letters7[LETTER] < min(b_["y"] for b_ in boxes7) < letters7[LETTER_B]
                    < min(it["y"] for it in stage7)))
        res.append(("(7) three signal boxes, Judge, Concepts and Papers left to right, black borders",
                    [it["s"] for it in sorted(sig7, key=lambda t: t["x"])] == list(figure_names.SIGNALS)
                    and len(boxes7) == 3 and all(b_["ec"] == INK for b_ in boxes7)))
        arrows7 = [it for it in items7 if it["kind"] == "arrow"]
        res.append(("(7) one stem from the answer forks into one black arrow per signal box, each ending at its top",
                    sum(1 for it in texts7 if it["s"] == "Answer") == 1
                    and sorted(round(a_["xs"][1], 2) for a_ in arrows7 if a_["ys"][1] < letters7[LETTER_B])
                    == sorted(round(b_["x"] + b_["w"] / 2, 2) for b_ in boxes7)
                    and all(abs(a_["ys"][1] - (boxes7[0]["y"] - 0.6)) < 1e-9 for a_ in arrows7
                            if a_["ys"][1] < letters7[LETTER_B])
                    and all(a_["color"] == INK for a_ in arrows7)))
        res.append(("(7) every signal row prints its readout in its box, tied to sheet Fig. 1a",
                    sorted(it["row"] for it in texts7 if it.get("fmt") == "{readout}") == list(range(len(srows7)))
                    and all(it["sheet"] == SHEET_SIG for it in texts7 if it.get("fmt") == "{readout}")
                    and len(srows7) == len(sheets7[SHEET_SIG])))
        stages7 = list(dict.fromkeys(r[0] for r in rows7))
        res.append(("(7) the stages left to right in pipeline order, every box border black, a black arrow between "
                    "stages",
                    [it["s"] for it in sorted(stage7, key=lambda t: t["x"])] == stages7
                    and all(it["ec"] == INK for it in items7 if it["kind"] == "rect" and it["ec"] != "none")
                    and sum(1 for a_ in arrows7 if a_["ys"][1] > letters7[LETTER_B]) == len(stages7) - 1))
        lv7 = [it for it in texts7 if it.get("fmt") == "{levels}"]
        res.append(("(7) every setting drawn once with its levels, tied to its first row of sheet Fig. 1b",
                    len(lv7) == len(rows7) and all(it["sheet"] == SHEET_SET
                                                   and sheets7[SHEET_SET][it["row"]]["levels"] == int(it["s"])
                                                   for it in lv7)))
        res.append(("(7) the totals line: answers, then model calls, each tied to its ALL row of sheet Fig. 1b",
                    [it["s"] for it in texts7 if it["size"] == PT_HEAD and it["y"] > letters7[LETTER_B]]
                    == ["51,441 answers", "|", "≥ 1,234,567 model calls"]
                    and [r["stage"] for r in sheets7[SHEET_SET][-2:]] == ["ALL", "ALL"]))
        res.append(("(7) a word line that does not match its make-up is refused (the Fig. 1b factors column)",
                    refused(lambda: factor_words("Corpus scale", f"4 {TIMES} 3 {TIMES} 2"))
                    and refused(lambda: factor_words("No such setting", "4"))))
        items8, sheets8, _, _ = layout(rows7, srows7, None, 51441)
        res.append(("(8) with no summary the plate prints the slot and the sheet holds n",
                    any(it["s"] == "n model calls" for it in items8 if it["kind"] == "text")
                    and sheets8[SHEET_SET][-1]["text"] == "n" and sheets8[SHEET_SET][-1]["stage"] == "ALL"))
        res.append(("(3) and (8) the summary is committed, so the total is a count",
                    isinstance(s520_total(), int)))
        # (3) the frozen set, copied with its SHA256SUMS lines
        root = td / "findings" / "recompute"
        rel_dir = f"{UPSTREAM_SET}_inputs/{UPSTREAM_REL}"
        (root / rel_dir).mkdir(parents=True)
        (root / "frozen_inputs").mkdir()
        sums = (ROOT / "findings" / "recompute" / "frozen_inputs" / "SHA256SUMS").read_text().splitlines()
        lines = [ln for ln in sums if f"findings/recompute/{rel_dir}/" in ln]
        (root / "frozen_inputs" / "SHA256SUMS").write_text("\n".join(lines) + "\n")
        name = F["exp01_raw"].name
        shutil.copyfile(F["exp01_raw"], root / rel_dir / name)
        res.append(("(3) the committed copy passes", not refused(
            lambda: check_committed(frozen(UPSTREAM_SET, f"{UPSTREAM_REL}/{name}", root=root), root=root))))
        b = bytearray((root / rel_dir / name).read_bytes())
        b[-2] ^= 1
        (root / rel_dir / name).write_bytes(bytes(b))
        res.append(("(3) a copy altered by one bit is refused", refused(
            lambda: check_committed(frozen(UPSTREAM_SET, f"{UPSTREAM_REL}/{name}", root=root), root=root))))
        # (4) two builds
        keep = OUT
        try:
            outs = [td / "build1", td / "build2"]
            for o in outs:
                OUT = o
                figure(["figure"])
        finally:
            OUT = keep
        names = sorted(p.name for p in outs[0].iterdir())
        res.append((f"(4) two builds byte-equal ({len(names)} files)",
                    names == sorted(p.name for p in outs[1].iterdir())
                    and all((outs[0] / n).read_bytes() == (outs[1] / n).read_bytes() for n in names)))
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        # DESIGN_AT is a fixed, recorded commit and may be HEAD itself right after it is moved (D160: 3f4db8ff), so
        # it is taken out before HEAD is looked for
        texts = [(outs[0] / n).read_text().replace(DESIGN_AT, "") for n in names if n.endswith((".md", ".json"))]
        stale = r"repo_head|repository HEAD|dirty|written_utc|uncommitted|\d{4}-\d\d-\d\dT\d\d:\d\d"
        res.append(("(4) no output names HEAD, a working-copy state or a write time",
                    bool(head) and not any(head[:7] in t or re.search(stale, t) for t in texts)))
    for what, ok in res:
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
    n_ok = sum(ok for _, ok in res)
    print(f"S456 selftest: {n_ok} of {len(res)} PASS")
    sys.exit(0 if n_ok == len(res) else 1)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["selftest"]:
        selftest()
    if argv[:1] != ["figure"]:
        print("usage: uv run --frozen python scripts/S456_fig1_design.py figure | selftest")
        sys.exit(2)
    figure(argv)


if __name__ == "__main__":
    main()
