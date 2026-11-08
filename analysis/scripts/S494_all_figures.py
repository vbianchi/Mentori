#!/usr/bin/env python3
"""S494 - D155: the one command that rebuilds every figure of the revision from the frozen inputs and checks each file
byte for byte against the committed plate.

WHY. D155 (Valerio, 26 October): "I want them to be a single script to run to reproduce all the figures in one go
[...] Whatever you do, it should be all reproducible." Each figure script already rebuilds its own plate from the
frozen inputs in one command (recorded in its docstring by the D155 build agents); this script runs them all, in
dependency order, into a fresh folder, and holds every output file to the committed one.

    uv run python scripts/S494_all_figures.py [--out DIR] [--tars DIR] [--only NAME ...] [--write] [--no-audit]

  --out DIR   where the rebuild goes (default: a fresh temporary folder, removed at the end unless --keep). Must be
              new or empty, and outside findings/figures_provisional/.
  --tars DIR  the folder holding the frozen tars (env FROZEN_TARS for every step; default
              ~/Mentori_scratch_keep/frozen_2026-10-26, or the folder the Zenodo deposit's tars were downloaded to).
  --only NAME one step (repeatable): frozen, d181, fig1, fig3, fig4, fig5, fig6, supp2, supp4, supp5, supp7, supp8,
              supp9, supp10_11, supp14_16, supp17, numbers, need_map, supp1 (d181 under --out only, see D201 Q9 below). A step that reads the committed outputs of a step not run gets a note:
              those outputs are held to git HEAD only, not proven by a rebuild. Without frozen among them the frozen
              inputs are not checked, and a run whose steps all pass ends "PARTIAL" and exits 1 (audit 27 Oct F8).
  --write     rebuild in place (into findings/figures_provisional/ and findings/recompute/) instead of --out; the
              comparison is then against git HEAD. Never needed to check reproducibility.
  --keep      keep the temporary --out folder.
  --no-audit  run without the read audit; the run then ends "NOT VERIFIED" and exits 1 even when every file is equal.

  uv run python scripts/S494_all_figures.py manifest [--check]
              writes (or checks) findings/figures_provisional/MANIFEST.sha256: the sha256 of every committed plate
              file, read from git HEAD, one "<sha256>  <path under findings/figures_provisional>" line each.

WHAT IT DOES, in order; nothing is written outside --out except the gitignored extraction folder
findings/recompute/frozen_inputs/extracted/ (fig_repro.frozen()) and, when it is missing or differs from its lock,
experiments/rlm_ref/.venv (D4):
  1. frozen: every line of findings/recompute/frozen_inputs/SHA256SUMS: a committed file has its sha256; a tar has its
     sha256 and is extracted and checked file by file through fig_repro.frozen(), against the committed
     findings/recompute/frozen_inputs/members/<tar>.sha256 (none missing, none extra); findings/recompute/fig6_inputs/
     is checked against its own SHA256SUMS.
  2. each figure's build command, as its script's docstring gives it (STEPS below; Supplementary numbers are D302's,
     the manuscript's order of first citation, 7 Nov): Figure 3 and Supplementary Figure 6 (S522's 3f rows, 3e
     before D218; S463 rebuild, S523), Supplementary 5 (S532, after Figure 3),
     Supplementary 8 (S476 rebuild: S474 L2, then T1_L2 and G4_fig3c, then the plate), Figure 4 (S480 recount, then
     S472), 5 (S497, D166), 6 (draw_B.py's anchor, then S481 figure), Supplementary 2 (S461), Figure 1 (S456, after the
     plates whose legend drafts it reads: under --out it reads them at git HEAD, under --write from the working tree
     the steps before it have just written, so one --write pass suffices; audit 27 Oct F1b), Supplementary 17 (S457 rebuild),
     7 (S459, after
     experiments/rlm_ref/.venv is checked with `uv sync --frozen --check` there, made with `uv sync --frozen` when the
     check fails, and refused when it still fails), 14 to 16 (S481 supplementary), 10 and 11 (S524 frame),
     4 (S541), 9 (S590, the pipeline drawn from the code) (the depth fit, S485, removed 2 Nov; S481 B1b removed 3 Nov; D302 dropped
     the uncited 16, 17 and 20 to 24 of D257: S463's score-3 plate, S484, S544 and three of S481's);
     then the number scripts
     S486 to S492 and distiller_count_g3_d1, each its own unit; then S526, S527 and S519 --check, one unit, after the
     plates they read; then Supplementary Figure 1 (S496, D160 (9)), which reads S492's registry and Figure 1's
     provenance. Figure 2 and Supplementary Figure 3 have no step (build order F9): they are frames from S531, and
     S531 --raters 0 rebuilds them. S456 and the number scripts S487 to S492 take no
     --out: they run through this script's "_call", which imports the script and points its output global (OUT,
     OUT_DIR) at --out before calling its main().
     THE READ AUDIT (D5, on by default). Every command runs with scripts/fig_read_audit_site first on PYTHONPATH and
     FIG_READ_AUDIT_DIR set, so every Python process of the step (children included) logs each file it opens, lists or
     globs, and every child process it starts with the paths on its command line (scripts/fig_read_audit.py). A step
     fails when it reads outside the repository and the allowed folders (the tars SHA256SUMS names, fig_repro's
     extracted folder, the interpreter, site-packages, the venvs, the uv cache, matplotlib's font cache, /dev,
     temporary folders the step makes, this run's --out; operating-system fonts, time zone and MIME files are allowed
     and listed), or reads a repository file that git HEAD does not hold or that differs from HEAD in the working tree
     (git ls-tree HEAD and git diff --name-only HEAD, computed again before each step, so a file changed during the
     run fails every later read of it); when it writes into the repository during an --out run (outside __pycache__,
     the venvs and the extracted folder); and when it starts a child process not on the audit's allow list
     (fig_read_audit section 3; audit 27 Oct F3): a child is accepted only in the environment its parent started
     with (fig_read_audit.CHILD_ENV_MAY_CHANGE names the six variables a build may change), and only as a Python of the repository's venvs (or uv run --frozen python) without -I, -E or -S, which
     loads the hook itself; git with a listed read-only subcommand and option (init, add and commit only in a folder
     the step made); or a shell string pinned by sha256 in fig_read_audit.REVIEWED_SHELL, run in a folder the step
     made. Any other program, wrapper word (env, nice, time), unpinned shell string (os.system, shell=True) or
     changed environment fails the step as unaudited. An accepted child's path arguments are judged as reads; git
     show or cat-file <rev>:<path> is a read of <path> (so the step is blocked by the step that owns it, F1b); at
     HEAD, of a file an earlier step of this run rewrote, it is a violation (the step read the version before); and
     at any rev that does not resolve to HEAD's commit or an ancestor of it (the index ':<path>', a stash, another
     branch, a rev that does not resolve) it is a violation, content not committed on main (audit 27 Oct R4, R5).
     Under --write, a read of a file an earlier step of the same run rewrote is that step's output, judged by the
     blocked rule. The audit is a check against accidental reads of uncommitted or outside files, not a sandbox
     against code written to evade it (fig_read_audit WHAT IT IS and LIMITS).
  3. every output file is compared byte for byte with the committed file (git HEAD), and a plate's files also with
     findings/figures_provisional/MANIFEST.sha256. A committed file the step does not write is listed as not rebuilt;
     a file the step writes that is not committed is listed as new (also when git HEAD holds nothing at that path);
     an output neither committed nor written is listed as absent. Each of these fails the step. A json file that
     differs gets the paths of the keys that differ.
  4. S448 (with --supplementary for a Supplementary figure) on each rebuilt plate, under the step's read audit; a
     plate passes only when every rule FIGURE_LOCK.toml tags for S448 (R1 to R12) reports PASS or WARN and none FAILs.
  5. BLOCKED. A step that reads (by the audit) a committed output of a step that failed, or was itself blocked, is
     reported "blocked by <step>" instead of compared: its rebuild used an output nobody proved. Repeated until
     nothing changes. When the frozen inputs fail, every step is blocked.
  6. one table: figure, files, byte-equal (or "blocked by"), S448, audit (reads judged violations), seconds; then
     every difference, violation and block with the step's own last lines.
Exit 0 only when every frozen input checks, every step exits 0 with no audit violation, every file is byte-equal,
S448 passes and the audit was on.

D201 Q9 O1 (Valerio, 2 November 2026; findings/audits/tracked_scripts_2026-11-01/README.md row 3). The concept recall and
panel c values the plates draw sit in five folders no step rebuilt, because S505's import changes two KMP_* variables the
audit refused in git children (fig_read_audit.CHILD_ENV_MAY_CHANGE now names them, with the reason). Step d181 runs their
tracked writers from the frozen inputs: S471 --d181 --frozen, S474 --d181 --frozen, S474 --d181 --frozen-d135, S514 t1 and
S514 g4c. Two limits, both on purpose. (1) It compares every rows and tables file (D181_FILES) and no header.json: L3's
header stores its write time and commit, the S474 headers store the command with its --outdir, and S514's store whether
each script equalled HEAD, so a header cannot come out byte-equal; S514 t1 --check draws the same line. (2) It runs under
--out only. Under --write it is left out, and `--write --only d181` is refused: S463 and S497 pin L3_d181/header.json by
sha256, so rewriting it in place would make both refuse. New output of S514 g4c therefore goes in by that command itself.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = "scripts/S494_all_figures.py"
FIG = ROOT / "findings" / "figures_provisional"
REC = ROOT / "findings" / "recompute"
MANIFEST = FIG / "MANIFEST.sha256"
MANIFEST_SKIP = {"MANIFEST.sha256", "README.md"}           # this script's own files in FIG, not plate files
SUMS = REC / "frozen_inputs" / "SHA256SUMS"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
UV = ["uv", "run", "--frozen", "python"]
RLM_REF = ROOT / "experiments" / "rlm_ref"   # Supplementary Figure 7's package venv (D4): ensure_rlm_ref_venv

# Committed files in an output folder that the step READS, not writes: written by an earlier command of their script
# (a mirror from the Studio, S447's draw, D149's anchor) and checked by the step against its own record. S494 holds each
# to git HEAD (working copy and MANIFEST) and lists it as an input; it is not regenerated from the frozen inputs here.
INPUTS = {
    "findings/recompute/G4_fig3c/anchor_d149_rlm10.json": "S476 anchor: D149's RLM-10 reading, g4c's anchor",
    "findings/recompute/G4_fig3c/anchor_pre_d156_grid.json": "S476 anchor-pre-d156: panel c's grid before D156 (D160 Q18)",
    "findings/figures_provisional/fig6/claims.md": "S447 draw, from S447_fig6_claims_template.md",
    "findings/figures_provisional/fig6/fig6_cells.csv": "S447 draw anchor (S481 reads it; header records build time)",
    "findings/figures_provisional/fig6/fig6_numbers.json": "S447 draw anchor (S481 reads it; records build time)",
    "findings/figures_provisional/fig6/records_manifest.json": "S447 mirror of the s2 records (S447 checks the tar)",
    "findings/figures_provisional/supp_fig17_outcomes/records_manifest.json": "S457 mirror (S457: an input, not written)",
}


# Step d181's rows and tables files, the bytes the plates draw; header.json is left out (module docstring, D201 Q9).
D181_FILES = {"L3_d181": ("concept_recall.jsonl",),
              "L2_d181": ("cap_tables.json", "cap_tables.md", "concept_recall.jsonl"),
              "L2_d135_d181": ("cap_tables.json", "cap_tables.md", "concept_recall.jsonl"),
              "T1_L2_d181": ("cap_tables.json", "concept_recall.jsonl"),
              "G4_fig3c_d185": ("absent_group.json", "grid_pairs.jsonl", "grid_tables.json", "left_out.json",
                                "noise_pairs.jsonl", "noise_tables.json", "other_noise_pairs.jsonl", "other_pairs.jsonl",
                                "q66_tables.json", "refusal_tables.json", "v25_differences.json", "verdicts.json")}


class OutPath(type(Path())):
    """A path outside the repository given to a script whose rel() or print calls relative_to(ROOT): the path itself
    instead of a ValueError. Only the printed text changes; every file a script writes is the same."""

    def relative_to(self, other, *a, **k):  # noqa: D102
        try:
            return Path(str(self)).relative_to(other, *a, **k)
        except ValueError:
            return Path(str(self))


# ---------------------------------------------------------------------------------------------------------------
# The steps. Each command is the one its script's docstring records (D155 build agents, commits 4dce3537 to 14fe4f62).
# A "plate" is (figure number, supplementary?, rebuilt folder relative to the step's out, committed folder).
# A "derived" is (rebuilt path relative to the step's out, committed path): a file or a folder.
# ---------------------------------------------------------------------------------------------------------------
def py(script, *args):
    return [*UV, script, *args]


def call(script, sets: dict, args=(), argv0=False, strs: dict | None = None):
    """Run script's main() through this script, with its output globals pointed at sets' paths and its string globals
    set to strs' values."""
    spec = [*UV, SCRIPT, "_call", script] + [f"--set={k}={v}" for k, v in sets.items()] + \
        [f"--setstr={k}={v}" for k, v in (strs or {}).items()]
    return spec + (["--argv0"] if argv0 else []) + ["--", *args]


def steps(out: Path | None) -> list[dict]:
    """The build, in dependency order. out None means --write (each script's default folder)."""
    def o(step, *parts):
        return None if out is None else out / step / Path(*parts) if parts else out / step

    def opt(flag, p):
        return [] if p is None else [flag, str(p)]

    s = []
    if out is not None:                                # D201 Q9 O1: under --out only (module docstring)
        s.append({"name": "d181", "label": "Concept recall and panel c on key v2.5",
                  "cmds": [py("scripts/S471_l3_concept_recall.py", "--d181", "--frozen", "--outdir", str(o("d181", "L3_d181"))),
                           py("scripts/S474_l2_concept_recall.py", "--d181", "--frozen",
                              "--outdir", str(o("d181", "L2_d181"))),
                           py("scripts/S474_l2_concept_recall.py", "--d181", "--frozen-d135",
                              "--outdir", str(o("d181", "L2_d135_d181"))),
                           py("scripts/S514_fig3_d185.py", "t1", "--out", str(o("d181", "T1_L2_d181"))),
                           py("scripts/S514_fig3_d185.py", "g4c", "--out", str(o("d181", "G4_fig3c_d185")))],
                  "derived": [(f"{d}/{f}", f"findings/recompute/{d}/{f}") for d, fs in D181_FILES.items() for f in fs]})
    # S522 reads the committed G4_fig3c_d185 (S514 g4c, in step d181 under --out). S463 rebuild (Supplementary Figure 16,
    # score 3, dropped by D302, so not written) reads the committed fig3e folder (Figure 3f's rows since D218), which this step's own S522 is held to
    s.append({"name": "fig3", "label": "Figure 3 and Supplementary Figure 6",
              "cmds": [py("scripts/S522_fig3e_rows.py", *opt("--out", o("fig3", "fig3e"))),
                       py("scripts/S463_fig2_ranking.py", "rebuild", *opt("--out", o("fig3", "fig3_strategies"))),
                       py("scripts/S523_supp_fig7_replication.py", *opt("--out", o("fig3", "supp_fig6_replication")))],
              "plates": [(3, False, "fig3_strategies", "fig3_strategies"),
                         (6, True, "supp_fig6_replication", "supp_fig6_replication")],
              # tables.json only: S522's header.json stores the command with its --out, so it cannot come out byte-equal
              "derived": [("fig3e/tables.json", "findings/recompute/fig3e/tables.json")]})
    s.append({"name": "supp5", "label": "Supplementary Figure 5",
              "cmds": [py("scripts/S532_supp4_false_premise.py", "plate",
                          *opt("--out", o("supp5", "supp_fig5_false_premise")))],
              "plates": [(5, True, "supp_fig5_false_premise", "supp_fig5_false_premise")]})
    # D283 (6 Nov): S476 draws main Figure 4 (depth, a and b) beside Supplementary Figure 8 (corpus size, the grid)
    s.append({"name": "supp8", "label": "Figure 4 and Supplementary Figure 8",
              "cmds": [py("scripts/S476_fig3_d123.py", "rebuild", *opt("--out", o("supp8")))],
              "plates": [(4, False, "fig4_depth", "fig4_depth"), (8, True, "supp_fig8_depth", "supp_fig8_depth")],
              "derived": [("L2", "findings/recompute/L2"), ("T1_L2", "findings/recompute/T1_L2"),
                          ("G4_fig3c", "findings/recompute/G4_fig3c")]})
    s.append({"name": "fig4", "label": "Figure 5 (folder fig4; D283)",
              # S472 reads the committed recount (its provenance records the recount's repository path), so the
              # rebuilt recount is compared with it before the plate is drawn
              "cmds": [py("scripts/S480_fig4_recount.py", *opt("--out", o("fig4", "S480_fig4_recount.json"))),
                       py("scripts/S472_fig4_panels.py", "figure", *opt("--out", o("fig4", "fig4")),
                          *opt("--steps-out", o("fig4", "S472_supp12a_steps.json")))],
              "plates": [(5, False, "fig4", "fig4")],
              "derived": [("S480_fig4_recount.json", "findings/recompute/S480_fig4_recount.json"),
                          ("S472_supp12a_steps.json", "findings/recompute/S472_supp12a_steps.json")]})   # D250: S12 a
    # D166 (28 October): Figure 5 is the locked plate S497 draws (S473 draws only its 26 October design, into --out)
    s.append({"name": "fig5", "label": "Figure 6 (folder fig5; D283)",
              "cmds": [py("scripts/S497_fig5_d166.py", "figure", *opt("--out", o("fig5", "fig5")))],
              "plates": [(6, False, "fig5", "fig5")]})
    s.append({"name": "fig6", "label": "Figure 7 (folder fig6; D283)",
              "cmds": [py("findings/recompute/fig6_options_2026-10-25/draw_B.py", *opt("--out", o("fig6", "draw_B"))),
                       py("scripts/S481_fig6_d138.py", "figure", *opt("--out", o("fig6")))],
              "plates": [(7, False, "fig6", "fig6")],
              "derived": [("draw_B/B_numbers.json", "findings/recompute/fig6_options_2026-10-25/B_numbers.json")]})
    s.append({"name": "supp2", "label": "Supplementary Figure 2",
              "cmds": [py("scripts/S461_supp_fig2_retrieval.py", *opt("--out", o("supp2", "supp_fig2")))],
              "plates": [(2, True, "supp_fig2", "supp_fig2")]})
    # Figure 1 after the plates whose legend drafts it reads (Figures 3 to 6, Supplementary Figure 2; S456 LEGENDS, whose
    # Figure 2 legend has no step here, F9, and is read as committed):
    # audit 27 Oct F1b. S456 reads them at git HEAD (git cat-file), so under --out the committed legends, which those
    # steps' rebuilds are held to (and Figure 1 is blocked by a step that fails); under --write it reads them from the
    # working tree (LEGENDS_AT worktree), where the steps before it have just written them, so one --write pass gives
    # Figure 1 the legends it is committed with
    s.append({"name": "fig1", "label": "Figure 1",
              "cmds": [call("scripts/S456_fig1_design.py", {} if out is None else {"OUT": o("fig1", "fig1")},
                            ["figure"], strs={"LEGENDS_AT": "worktree"} if out is None else None)],
              "plates": [(1, False, "fig1", "fig1")]})
    # D302 (Valerio, 7 Nov, "Q1: drop them"): S484's corpus plate (Supplementary Figure 17 before) is not built
    s.append({"name": "supp17", "label": "Supplementary Figure 17",
              "cmds": [py("scripts/S457_fig2_panels.py", "rebuild", *opt("--out", o("supp17", "supp_fig17_outcomes")))],
              "plates": [(17, True, "supp_fig17_outcomes", "supp_fig17_outcomes")]})
    s.append({"name": "supp7", "label": "Supplementary Figure 7", "prepare": "rlm_ref_venv",
              "cmds": [py("scripts/S459_fig3_rlm_ref_caps.py", *opt("--out", o("supp7", "supp_fig7_package_caps")))],
              "plates": [(7, True, "supp_fig7_package_caps", "supp_fig7_package_caps")]})
    # S481 B1b ("best_of_3", Supplementary Figure 22 before D257) dropped, 3 Nov (D222): its values are rows of Figure
    # 6d's sheet, not drawn. D302 (7 Nov): S481's plates are 14, 15 and 16, all cited; difficulty, operations and cost
    # (21, 22 and 24 before) dropped (Valerio, "Q1: drop them")
    fig6_supp = [(14, "failures"), (15, "pairs"), (16, "models")]
    s.append({"name": "supp14_16", "label": "Supplementary Figures 14 to 16",
              "cmds": [py("scripts/S481_fig6_d138.py", "supplementary", *opt("--out", o("supp14_16")))],
              "plates": [(n, True, f"supp_fig{n}_fig6_{slug}", f"supp_fig{n}_fig6_{slug}") for n, slug in fig6_supp]})
    # The depth fit (S485, Supplementary Figure 11 until 2 Nov) removed, 2 Nov (Valerio: "I think is redundant. We should
    # remove this figure."): Supplementary Figure 8 carries the same cap curves. D257: the numbers closed up, 5 Nov
    s.append({"name": "supp10_11", "label": "Supplementary Figures 10 and 11",
              # T3 ran and froze 4 Nov: figure on that set (frame drew "0 of" planned rows, the plate before T3 had
              # run), read from count_records_20261106.tar (D281), whose 142 files equal findings/runs' copy
              "cmds": [py("scripts/S524_t3_s12_s13.py", "figure", "--t3", "findings/recompute/frozen_inputs/extracted/"
                          "count_records_20261106/count_records_20261106/t3/T3_frozen_20261104T131439Z",
                          # D287 O3: the reproduction's 8 exp07 files from the committed tar, not the deposit outside
                          "--results", "findings/recompute/exp07_bench_20261107/exp07_bench_20261107.tar",
                          *opt("--out", o("supp10_11")))],
              "plates": [(10, True, "supp_fig10_components", "supp_fig10_components"),
                         (11, True, "supp_fig11_distiller_prompts", "supp_fig11_distiller_prompts")]})
    s.append({"name": "supp4", "label": "Supplementary Figure 4",
              "cmds": [py("scripts/S541_supp_judge_pair.py", "figure", *opt("--out", o("supp4", "supp_fig4_judge_pair")))],
              "plates": [(4, True, "supp_fig4_judge_pair", "supp_fig4_judge_pair")]})
    # D257 (Valerio, 5 Nov, "Q1: O1"): Mentor::i's question-answering pipeline, drawn from the code (no data)
    s.append({"name": "supp9", "label": "Supplementary Figure 9",
              "cmds": [py("scripts/S590_supp_fig9_pipeline.py", *opt("--out", o("supp9", "supp_fig9_pipeline")))],
              "plates": [(9, True, "supp_fig9_pipeline", "supp_fig9_pipeline")]})

    def num(script, sets, argv0=False, args=()):
        return call(script, {} if out is None else {k: o("numbers", *v) for k, v in sets.items()}, args, argv0)

    s.append({"name": "numbers", "label": "Numbers S486 to S492", "independent": True,
              "cmds": [py("scripts/S486_faithfulness_paired.py", *opt("--out", o("numbers", "S486_faithfulness_paired"))),
                       num("scripts/S487_kendall_grounded.py",
                           {"OUT_DIR": ["S487_kendall_grounded"],
                            "OUT": ["S487_kendall_grounded", "S487_kendall_grounded.json"]}),
                       num("scripts/S488_fig6_heterogeneity.py",
                           {"OUT": ["S488_fig6_heterogeneity", "S488_fig6_heterogeneity.json"]}, argv0=True),
                       num("scripts/S489_fig4_by_question_type.py", {"OUT": ["S489_fig4_by_question_type"]}),
                       num("scripts/S490_fig3_plateau.py", {"OUT": ["S490_fig3_plateau"]}),
                       num("scripts/S491_fig6_owed_reruns.py",
                           {"OUT": ["S491_fig6_owed_reruns", "S491_fig6_owed_reruns.json"]}, argv0=True),
                       num("scripts/S492_answer_registry.py", {"OUT": ["S492_answer_registry"]}),
                       py("scripts/distiller_count_g3_d1.py", *opt("--out", o("numbers", "distiller_count_g3_d1")))],
              "derived": [(d, f"findings/recompute/{d}") for d in
                          ["S486_faithfulness_paired", "S487_kendall_grounded", "S488_fig6_heterogeneity",
                           "S489_fig4_by_question_type", "S490_fig3_plateau", "S491_fig6_owed_reruns",
                           "S492_answer_registry", "distiller_count_g3_d1"]]})
    # After the plates and numbers: S527 hashes the committed outputs it reads (its folder, not S526's inputs/, is rebuilt)
    s.append({"name": "need_map", "label": "Instrument swaps and the need map",
              "cmds": [py("scripts/S526_instrument_swaps.py", *opt("--out", o("need_map", "S526_instrument_swaps"))),
                       py("scripts/S527_need_map.py", *opt("--out", o("need_map", "S527_need_map"))),
                       py("scripts/S519_flat_wide_plan.py", "--check")],
              "derived": [("S526_instrument_swaps/results.json", "findings/recompute/S526_instrument_swaps/results.json"),
                          ("S526_instrument_swaps/results.md", "findings/recompute/S526_instrument_swaps/results.md"),
                          ("S527_need_map", "findings/recompute/S527_need_map")]})
    # Supplementary Figure 1, the experiment graph (D160 (9)), last: it reads S492's registry (numbers) and Figure 1's
    # design facts (fig1/figure1_provenance.json), so it is blocked when either fails
    s.append({"name": "supp1", "label": "Supplementary Figure 1",
              "cmds": [py("scripts/S496_supp_fig1_experiment_graph.py", *opt("--out", o("supp1", "supp_fig1")))],
              "plates": [(1, True, "supp_fig1", "supp_fig1")]})
    return s


# ---------------------------------------------------------------------------------------------------------------
# Hashing and the committed record (git HEAD)
# ---------------------------------------------------------------------------------------------------------------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def head_files(rel: str) -> list[str]:
    """Repository paths git HEAD holds at rel (a file or a folder)."""
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", rel], cwd=ROOT, capture_output=True,
                       text=True, check=True)
    return [x for x in r.stdout.splitlines() if x]


def head_blobs(paths: list[str]) -> dict[str, bytes]:
    """The HEAD content of each path, through one git cat-file --batch."""
    if not paths:
        return {}
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data, _ = proc.communicate("".join(f"HEAD:{p}\n" for p in paths).encode())
    out, i = {}, 0
    for p in paths:
        nl = data.index(b"\n", i)
        head = data[i:nl].decode()
        if head.endswith("missing"):
            raise SystemExit(f"git HEAD has no {p}")
        size = int(head.split()[2])
        out[p] = data[nl + 1: nl + 1 + size]
        i = nl + 1 + size + 1
    return out


def plate_manifest() -> dict[str, str]:
    """sha256 of every plate file git HEAD holds under findings/figures_provisional (relative path -> sha256)."""
    base = FIG.relative_to(ROOT).as_posix()
    paths = [p for p in head_files(base) if Path(p).name not in MANIFEST_SKIP or Path(p).parent.as_posix() != base]
    paths = [p for p in paths if "/__pycache__/" not in p]
    blobs = head_blobs(paths)
    return {p[len(base) + 1:]: sha256_bytes(b) for p, b in sorted(blobs.items())}


def read_manifest() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    rows = {}
    for line in MANIFEST.read_text().splitlines():
        if line.strip():
            sha, rel = line.split("  ", 1)
            rows[rel] = sha
    return rows


def cmd_manifest(check: bool) -> int:
    m = plate_manifest()
    text = "".join(f"{sha}  {rel}\n" for rel, sha in m.items())
    if check:
        ok = MANIFEST.exists() and MANIFEST.read_text() == text
        print(f"{MANIFEST.relative_to(ROOT)} {'equals' if ok else 'DIFFERS from'} the plates at git HEAD "
              f"({len(m)} files)")
        return 0 if ok else 1
    MANIFEST.write_text(text)
    print(f"wrote {MANIFEST.relative_to(ROOT)}: {len(m)} plate files at git HEAD")
    return 0


# ---------------------------------------------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------------------------------------------
def json_diff(a, b, path="", out=None, limit=12):
    """Key paths where two parsed json values differ (at most limit)."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append(f"{path}/{k} (new)")
            elif k not in b:
                out.append(f"{path}/{k} (gone)")
            elif a[k] != b[k]:
                json_diff(a[k], b[k], f"{path}/{k}", out, limit)
            if len(out) >= limit:
                break
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                json_diff(x, y, f"{path}[{i}]", out, limit)
            if len(out) >= limit:
                break
    else:
        out.append(path or "/")
    return out


def text_diff(a: bytes, b: bytes, limit=3) -> list[str]:
    try:
        la, lb = a.decode().splitlines(), b.decode().splitlines()
    except UnicodeDecodeError:
        return [f"binary, {len(a)} bytes committed, {len(b)} rebuilt"]
    diffs = [f"line {i + 1}: committed {x[:90]!r} / rebuilt {y[:90]!r}" for i, (x, y) in enumerate(zip(la, lb))
             if x != y][:limit]
    if len(la) != len(lb):
        diffs.append(f"{len(la)} lines committed, {len(lb)} rebuilt")
    return diffs


def why(name: str, committed: bytes, rebuilt: bytes) -> list[str]:
    if name.endswith(".json"):
        try:
            return ["keys " + ", ".join(json_diff(json.loads(committed), json.loads(rebuilt)))]
        except ValueError:
            pass
    if name.endswith((".md", ".csv", ".txt", ".jsonl", ".tsv")):
        return text_diff(committed, rebuilt)
    return [f"{len(committed)} bytes committed, {len(rebuilt)} rebuilt"]


def compare(rebuilt: Path, committed_rel: str, manifest: dict | None, manifest_prefix: str | None) -> dict:
    """Compare a rebuilt file or folder with git HEAD's committed_rel (and with the manifest for a plate)."""
    committed = head_files(committed_rel)
    single = len(committed) == 1 and committed[0] == committed_rel
    blobs = head_blobs(committed)
    if not committed:
        # git HEAD holds nothing at committed_rel (audit 27 Oct F4): what was written is new, nothing written is absent
        pairs = {}
        made = ({f.relative_to(rebuilt).as_posix() for f in rebuilt.rglob("*")
                 if f.is_file() and "__pycache__" not in f.parts} if rebuilt.is_dir()
                else {Path(committed_rel).name} if rebuilt.is_file() else set())
    elif single:
        pairs = {Path(committed_rel).name: (committed_rel, rebuilt)}
        made = {Path(committed_rel).name} if rebuilt.is_file() else set()
    else:
        pairs = {p[len(committed_rel) + 1:]: (p, rebuilt / p[len(committed_rel) + 1:]) for p in committed}
        made = ({f.relative_to(rebuilt).as_posix() for f in rebuilt.rglob("*")
                 if f.is_file() and "__pycache__" not in f.parts} if rebuilt.is_dir() else set())
    res = {"equal": [], "differ": [], "not_rebuilt": [], "new": sorted(made - set(pairs)), "manifest": [],
           "inputs": [], "inputs_changed": [], "notes": {},
           "absent": [Path(committed_rel).name] if not committed and not made else []}
    for name, (repo_path, f) in sorted(pairs.items()):
        want = blobs[repo_path]
        if manifest is not None:
            key = f"{manifest_prefix}/{name}"
            if manifest.get(key) != sha256_bytes(want):
                res["manifest"].append(name)
        if repo_path in INPUTS:                          # read by the step: the working copy must be HEAD's
            w = ROOT / repo_path
            (res["inputs"] if w.is_file() and w.read_bytes() == want else res["inputs_changed"]).append(name)
            continue
        if name not in made:
            res["not_rebuilt"].append(name)
            continue
        got = f.read_bytes()
        if got == want:
            res["equal"].append(name)
        else:
            res["differ"].append(name)
            res["notes"][name] = why(name, want, got)
    return res


# ---------------------------------------------------------------------------------------------------------------
# Step 1: the frozen inputs
# ---------------------------------------------------------------------------------------------------------------
def check_frozen() -> tuple[bool, list[str]]:
    import fig_repro
    lines, ok = [], True
    sums = {}
    for line in SUMS.read_text().splitlines():
        if line.strip():
            sha, name = line.split("  ", 1)
            sums[name] = sha
    files = {k: v for k, v in sums.items() if not k.endswith(".tar")}
    bad = [k for k, v in files.items() if not (ROOT / k).is_file() or sha256_file(ROOT / k) != v]
    lines.append(f"{len(files) - len(bad)} of {len(files)} committed frozen files equal SHA256SUMS")
    if bad:
        ok = False
        lines += [f"  DIFFERS or missing: {k}" for k in bad]
    tars_dir = Path(os.environ.get("FROZEN_TARS", str(fig_repro.DEFAULT_TARS))).expanduser()
    for name, want in sorted((k, v) for k, v in sums.items() if k.endswith(".tar")):
        t = tars_dir / name
        try:
            if not t.is_file():
                raise fig_repro.FrozenInputError(f"{t} is missing: download {name} from the Zenodo deposit")
            got = sha256_file(t)
            if got != want:
                raise fig_repro.FrozenInputError(f"{t} sha256 {got[:12]}, SHA256SUMS {want[:12]}")
            folder = fig_repro.frozen(name[:-4])             # extracts once, checks every extracted file each call
            n = sum(1 for f in folder.rglob("*") if f.is_file()) - 1
            lines.append(f"{name}: sha256 {want[:12]} equal; {n} extracted files equal "
                         f"frozen_inputs/members/{name[:-4]}.sha256, none missing")
        except fig_repro.FrozenInputError as e:
            ok = False
            lines.append(f"{name}: FAILED: {e}")
    try:
        own = REC / "fig6_inputs"                          # its own SHA256SUMS lists the files; README.md is not one
        listed = [x.split("  ", 1)[1] for x in (own / "SHA256SUMS").read_text().splitlines() if x.strip()]
        for rel in listed:
            fig_repro.frozen("fig6", rel)
        lines.append(f"fig6_inputs: {len(listed)} files equal its own SHA256SUMS (not listed in the shared "
                     f"SHA256SUMS)")
    except fig_repro.FrozenInputError as e:
        ok = False
        lines.append(f"fig6_inputs: FAILED: {e}")
    return ok, lines


# ---------------------------------------------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------------------------------------------
def run_cmd(cmd: list[str], log: Path, env: dict) -> int:
    with open(log, "a") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        fh.flush()
        r = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.write(f"[exit {r.returncode}]\n\n")
    return r.returncode


def ensure_rlm_ref_venv(log: Path, env: dict, folder: Path = RLM_REF) -> tuple[bool, str]:
    """D4: Supplementary Figure 7's legend cites the rlms package's METADATA in experiments/rlm_ref/.venv (S459
    PKG_METADATA). The venv is gitignored, so a clone has none: check it against experiments/rlm_ref/uv.lock with
    `uv sync --frozen --check`, make it with `uv sync --frozen` when the check fails, check again, and refuse when it
    still fails or holds no single rlms METADATA."""
    e = {k: v for k, v in env.items() if k != "VIRTUAL_ENV"}   # the repository's venv is not this project's
    rel_f = folder.relative_to(ROOT) if folder.is_relative_to(ROOT) else folder

    def uv_sync(*extra):
        r = subprocess.run(["uv", "sync", "--frozen", *extra], cwd=folder, capture_output=True, text=True, env=e)
        with open(log, "a") as fh:
            fh.write(f"$ (cd {rel_f}) uv sync --frozen {' '.join(extra)}\n{r.stdout}{r.stderr}"
                     f"[exit {r.returncode}]\n\n")
        return r

    if not (folder / "uv.lock").is_file() or not (folder / "pyproject.toml").is_file():
        return False, f"{rel_f}/pyproject.toml or uv.lock is missing: the clone is incomplete"
    try:
        made = False
        if uv_sync("--check").returncode != 0:
            r = uv_sync()
            if r.returncode != 0:
                tail_txt = " | ".join(x for x in (r.stderr or r.stdout).strip().splitlines()[-3:])
                return False, (f"{rel_f}/.venv could not be made (uv sync --frozen exit {r.returncode}: {tail_txt}); "
                               f"run `uv sync --frozen` in {rel_f} and run S494 again")
            made = True
            if uv_sync("--check").returncode != 0:
                return False, f"{rel_f}/.venv still differs from its uv.lock after uv sync --frozen (log {log})"
    except FileNotFoundError:
        return False, "uv is not on PATH: install uv (https://docs.astral.sh/uv/) and run S494 again"
    meta = sorted((folder / ".venv" / "lib").glob("python*/site-packages/rlms-*.dist-info/METADATA"))
    if len(meta) != 1:
        return False, f"{rel_f}/.venv holds {len(meta)} rlms METADATA files, S459 needs exactly 1"
    return True, f"{rel_f}/.venv {'made by uv sync --frozen, then ' if made else ''}equal to its uv.lock"


def s448_required_rules() -> list[str]:
    """Every rule experiments/FIGURE_LOCK.toml tags "S448 R<n>" (R1 to R12 on 27 October): each must report PASS or
    WARN on every plate (audit 27 Oct F3: an S448 that reported no rule and exited 0 passed)."""
    text = FIGURE_LOCK.read_text(encoding="utf-8")
    tags = re.findall(r"S448 (R\d+(?:,? (?:and )?R\d+)*)", text)
    return [f"R{n}" for n in sorted({int(x) for g in tags for x in re.findall(r"R(\d+)", g)})]


def s448(n: int, supp: bool, folder: Path, log: Path, env: dict, audit_dir: Path | None = None) -> tuple[str, bool]:
    """S448 on one rebuilt plate; under the read audit when audit_dir is given (audit F3: its reads are judged with
    the step's, so an uncommitted edit to S448 or FIGURE_LOCK fails the step). Passes only when it exits 0, no rule
    FAILs and every rule of s448_required_rules() reports PASS or WARN."""
    import fig_read_audit
    cmd = py("scripts/S448_figure_rules_check.py", "--figure", str(n), "--dir", str(folder))
    if supp:
        cmd.append("--supplementary")
    run_env = fig_read_audit.env_for(env, audit_dir) if audit_dir is not None else env
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=run_env)
    with open(log, "a") as fh:
        fh.write("$ " + " ".join(cmd) + "\n" + r.stdout + r.stderr + f"[exit {r.returncode}]\n\n")
    verdicts = re.findall(r"^(R\d+)\s+(PASS|FAIL|WARN)\b", r.stdout, flags=re.M)
    fails = {rule for rule, v in verdicts if v == "FAIL"}
    npass = len({rule for rule, v in verdicts if v == "PASS"} - fails)
    nfail = len(fails)
    nwarn = sum(1 for _, v in verdicts if v == "WARN")
    reported = {rule for rule, v in verdicts if v in ("PASS", "WARN")} | fails
    missing = [rule for rule in s448_required_rules() if rule not in reported]
    ok = r.returncode == 0 and nfail == 0 and not missing
    txt = (f"{npass} PASS" + (f", {nfail} FAIL" if nfail else "") + (f", {nwarn} warn" if nwarn else "")
           + (f", {len(missing)} not reported ({', '.join(missing)})" if missing else ""))
    return (txt if r.returncode == 0 or nfail else f"{txt}, exit {r.returncode}"), ok


def tail(log: Path, n=6) -> list[str]:
    try:
        return [x for x in log.read_text(errors="replace").splitlines() if x.strip()][-n:]
    except OSError:
        return []


# ---------------------------------------------------------------------------------------------------------------
# The read audit (D5) and the blocked rule
# ---------------------------------------------------------------------------------------------------------------
def git_state() -> tuple[set[str], set[str]]:
    """Computed once per run: every path git HEAD holds, and every path whose working copy differs from HEAD."""
    head = subprocess.run(["git", "ls-tree", "-r", "--name-only", "-z", "HEAD"], cwd=ROOT, capture_output=True,
                          check=True).stdout.decode().split("\0")
    dirty = subprocess.run(["git", "diff", "--name-only", "-z", "HEAD"], cwd=ROOT, capture_output=True,
                           check=True).stdout.decode().split("\0")
    return {x for x in head if x}, {x for x in dirty if x}


def uv_dirs() -> list[str]:
    out = []
    for args in (["uv", "cache", "dir"], ["uv", "python", "dir"]):
        try:
            r = subprocess.run(args, capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                out.append(r.stdout.strip())
        except FileNotFoundError:
            pass
    return out


def units_of(step_list: list[dict]) -> list[dict]:
    """The units S494 judges: one per step, or one per command for an "independent" step (the number scripts, each
    with its own derived output). Each holds the step, its command indices, and the plates and derived outputs it
    owns."""
    units = []
    for st in step_list:
        if st.get("independent"):
            for i, cmd in enumerate(st["cmds"]):
                script = next(x for x in cmd if x.endswith(".py") and x != SCRIPT)
                units.append({"name": f"{st['name']}:{Path(script).stem}", "short": Path(script).stem.split("_")[0],
                              "label": st["label"], "step": st, "idx": [i], "plates": [],
                              "derived": [st["derived"][i]]})
        else:
            units.append({"name": st["name"], "short": st["name"], "label": st["label"], "step": st,
                          "idx": list(range(len(st["cmds"]))), "plates": st.get("plates", []),
                          "derived": st.get("derived", [])})
    return units


def owners(units: list[dict]) -> list[tuple[str, str]]:
    """(committed path or folder prefix, unit name) for every output a unit writes; INPUTS are not outputs."""
    rows = []
    for u in units:
        for _, _, _, committed_dir in u["plates"]:
            rows.append((f"{FIG.relative_to(ROOT).as_posix()}/{committed_dir}/", u["name"]))
        for _, committed_rel in u["derived"]:
            rows.append((committed_rel if Path(committed_rel).suffix else committed_rel + "/", u["name"]))
    return rows


def owner_of(rel: str, table: list[tuple[str, str]]) -> str | None:
    if rel in INPUTS:
        return None
    for prefix, name in table:
        if rel == prefix or (prefix.endswith("/") and rel.startswith(prefix)):
            return name
    return None


def resolve_blocked(units: list[dict], table: list[tuple[str, str]], frozen_failed: bool) -> None:
    """Set each run unit's "status": "ok", "failed" (its own exit, read audit, comparison or S448) or "blocked",
    with "blocked_by" {unit: the path that ties them}: a unit that reads (by the audit) a committed output of a failed
    or blocked unit, or any unit when the frozen inputs failed, is blocked instead of compared. Repeated until nothing
    changes, so a block propagates. A read of a unit not run in this invocation (--only) goes to "unchecked_deps"."""
    by_name = {u["name"]: u for u in units}
    for u in units:
        u["deps"], u["unchecked_deps"] = {}, {}
        for rel in u["repo_reads"]:
            o = owner_of(rel, table)
            if o and o != u["name"]:
                (u["deps"] if o in by_name else u["unchecked_deps"]).setdefault(o, rel)
        u["status"] = "ok" if u["own_ok"] else "failed"
        u["blocked_by"] = {}
        if frozen_failed:
            u["status"], u["blocked_by"] = "blocked", {"frozen": "the frozen inputs did not check"}
    changed = True
    while changed:
        changed = False
        for u in units:
            bad = {d: rel for d, rel in u["deps"].items() if by_name[d]["status"] != "ok"}
            new = {**({"frozen": u["blocked_by"]["frozen"]} if "frozen" in u["blocked_by"] else {}), **bad}
            if new and (u["status"] != "blocked" or new != u["blocked_by"]):
                u["status"], u["blocked_by"] = "blocked", new
                changed = True


def label_of(name: str, units: list[dict]) -> str:
    return next((u["short"] for u in units if u["name"] == name), name)


def cmd_run(a) -> int:
    t_all = time.time()
    if a.tars:
        os.environ["FROZEN_TARS"] = str(Path(a.tars).expanduser().resolve())
    env = dict(os.environ)
    manifest = read_manifest()
    if not manifest:
        print(f"{MANIFEST.relative_to(ROOT)} is missing: run `uv run python {SCRIPT} manifest` first")
        return 2
    if a.write:
        out = None
        logs = Path(tempfile.mkdtemp(prefix="S494_logs_"))
    else:
        tmp = a.out is None
        out = Path(tempfile.mkdtemp(prefix="S494_")) if tmp else Path(a.out).expanduser().resolve()
        if out.exists() and any(out.iterdir()):
            print(f"--out {out} is not empty: give a new or empty folder")
            return 2
        if out == FIG or FIG in out.parents or out in FIG.parents:
            print("--out must be outside findings/figures_provisional (use --write to rebuild in place)")
            return 2
        out.mkdir(parents=True, exist_ok=True)
        logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    import fig_read_audit
    import fig_repro
    audit_on = not a.no_audit
    head_set, dirty = git_state()
    tars = Path(env.get("FROZEN_TARS", str(fig_repro.DEFAULT_TARS))).expanduser()
    uvd = uv_dirs()

    def context(state: tuple[set[str], set[str]]):
        """The read audit's allowances for one step, with the git state measured just before it ran (audit F2)."""
        return fig_read_audit.Context(ROOT, tars, state[0], dirty | state[1],
                                      extra_allowed=[x for x in (out, logs) if x], uv_dirs=uvd, write_run=out is None,
                                      changed=state[1] - dirty)
    print(f"S494: rebuilding into {'the repository (--write)' if out is None else out}; logs in {logs}; "
          f"FROZEN_TARS={env.get('FROZEN_TARS', '(default)')}; read audit {'on' if audit_on else 'OFF'} "
          f"({len(dirty)} files differ from git HEAD in this working tree)", flush=True)

    wanted = set(a.only or [])
    frozen_row, problems, frozen_failed = None, [], False

    if not wanted or "frozen" in wanted:
        t0 = time.time()
        ok, lines = check_frozen()
        frozen_failed = not ok
        for x in lines:
            print("  " + x, flush=True)
        frozen_row = ("frozen inputs", "", "checked" if ok else "FAILED", "", "", f"{time.time() - t0:.0f}")
        if not ok:
            problems.append(("frozen inputs", ["a frozen input is missing or altered (lines above)"]))

    # Run every unit, in step order.
    every = units_of(steps(out))
    units: list[dict] = [dict(u) for u in every if not wanted or u["step"]["name"] in wanted]
    prepared: dict[str, str | None] = {}
    for u in units:
        st = u["step"]
        log = logs / f"{st['name']}.log"
        if st["name"] not in prepared:
            print(f"-- {st['label']}", flush=True)
            prepared[st["name"]] = None
            if st.get("prepare") == "rlm_ref_venv":
                ok, msg = ensure_rlm_ref_venv(log, env)
                print(f"   {msg}", flush=True)
                prepared[st["name"]] = None if ok else msg
        u.update({"rc": 0, "failed": None, "log": log, "audit_dirs": [], "prep": prepared[st["name"]],
                  "git_state": git_state()})
        t1 = time.time()
        if u["prep"]:
            u["rc"], u["failed"] = 2, ["S494 prepare: " + u["prep"]]
        for i in ([] if u["prep"] else u["idx"]):
            adir = logs / "audit" / st["name"] / str(i)
            adir.mkdir(parents=True, exist_ok=True)
            u["audit_dirs"].append(adir)
            r = run_cmd(st["cmds"][i], log, fig_read_audit.env_for(env, adir) if audit_on else env)
            if r:
                u["rc"], u["failed"] = r, st["cmds"][i]
                break
        u["secs"] = time.time() - t1
        print(f"   {u['name']}: {u['secs']:.0f} s, exit {u['rc']}", flush=True)

    # Judge each unit: S448 on its plates (under the unit's audit), its reads, its outputs against git HEAD.
    platform: dict[str, set[str]] = {}
    for u in units:
        base = out / u["step"]["name"] if out is not None else None
        checks, s448_dirs = {}, []
        for n_fig, supp, rebuilt_rel, committed_dir in u["plates"]:
            rebuilt = (base / rebuilt_rel) if base is not None else FIG / committed_dir
            if rebuilt.is_dir() and not u["rc"]:
                adir = logs / "audit" / u["step"]["name"] / f"S448_{'supp' if supp else 'fig'}{n_fig}"
                adir.mkdir(parents=True, exist_ok=True)
                s448_dirs.append(adir)
                checks[(n_fig, supp)] = s448(n_fig, supp, rebuilt, u["log"], env, adir if audit_on else None)
            else:
                checks[(n_fig, supp)] = ("not run", False)
        ev = fig_read_audit.new_events()
        n_build = 0
        for d in u["audit_dirs"] + (s448_dirs if audit_on else []):
            e = fig_read_audit.read_logs(d)
            n_build += len(e["argv"]) if d in u["audit_dirs"] else 0
            for k in ev:
                ev[k] = ev[k] + e[k] if isinstance(ev[k], list) else ev[k] | e[k]
        j = fig_read_audit.judge(ev, context(u["git_state"]))
        u["violations"], u["repo_reads"] = j["violations"], j["repo_reads"]
        u["n_proc"] = n_build                           # the build's own processes; S448's do not count (F7)
        for p in j["platform"]:
            platform.setdefault(p, set()).add(u["short"])
        u["rows"] = []
        own_ok = not u["rc"] and not u["violations"] and (not audit_on or u["n_proc"] > 0)
        for rebuilt_rel, committed_rel in u["derived"]:
            rebuilt = (base / rebuilt_rel) if base is not None else ROOT / committed_rel
            c = compare(rebuilt, committed_rel, None, None)
            good = not (c["differ"] or c["not_rebuilt"] or c["new"] or c["inputs_changed"] or c["absent"])
            own_ok &= good
            u["rows"].append({"label": f"  {committed_rel.replace('findings/recompute/', '')}", "c": c, "good": good,
                              "s448": "", "s448_ok": True})
        for n_fig, supp, rebuilt_rel, committed_dir in u["plates"]:
            rebuilt = (base / rebuilt_rel) if base is not None else FIG / committed_dir
            c = compare(rebuilt, f"{FIG.relative_to(ROOT).as_posix()}/{committed_dir}", manifest, committed_dir)
            s448_txt, s448_ok = checks[(n_fig, supp)]
            good = (not (c["differ"] or c["not_rebuilt"] or c["new"] or c["manifest"] or c["inputs_changed"]
                         or c["absent"]) and s448_ok)
            own_ok &= good
            u["rows"].append({"label": ("Supplementary Figure " if supp else "Figure ") + str(n_fig), "c": c,
                              "good": good, "s448": s448_txt, "s448_ok": s448_ok})
        u["own_ok"] = bool(own_ok)
    resolve_blocked(units, owners(every), frozen_failed)

    # The table and the problems.
    rows = [frozen_row] if frozen_row else []
    for u in units:
        nv = len(u["violations"])
        aud = "off" if not audit_on else ("not run" if not u["audit_dirs"] else (f"{nv} reads" if nv else "0"))
        blocked = ("blocked by " + ", ".join(label_of(d, units) for d in u["blocked_by"])) if u["status"] == "blocked" \
            else None
        if not u["rows"]:
            rows.append((u["label"], "", blocked or ("exit " + str(u["rc"]) if u["rc"] else ""), "", aud,
                         f"{u['secs']:.0f}"))
        for k, r in enumerate(u["rows"]):
            c = r["c"]
            n = len(c["equal"]) + len(c["differ"]) + len(c["not_rebuilt"])         # outputs; inputs apart
            eq = blocked or f"{len(c['equal'])} of {n}" + inputs_note(c)
            rows.append((r["label"], str(n), eq, r["s448"], aud, f"{u['secs']:.0f}" if k == 0 else "(above)"))
        lines = []
        if u["rc"]:
            lines.append(f"command exit {u['rc']}: {' '.join(u['failed'])}")
            lines += tail(u["log"])
        if audit_on and u["audit_dirs"] and u["n_proc"] == 0:
            lines.append("the audit recorded no Python process: the hook did not load (PYTHONPATH ignored?)")
        for path, why_ in u["violations"]:
            lines.append(f"read audit: {path}: {why_}")
        if u["status"] == "blocked":
            for d, rel in u["blocked_by"].items():
                lines.append(f"blocked by {label_of(d, units)}: reads {rel}, an output of a step that failed or "
                             f"was blocked; this step's outputs are not compared" if d != "frozen" else
                             f"blocked by the frozen inputs: {rel}")
        else:
            for r in u["rows"]:
                pre = f"{r['label'].strip()}: " if len(u["rows"]) > 1 else ""
                if not r["good"]:
                    lines += [pre + x for x in describe(r["c"])]
                    if not r["s448_ok"]:
                        lines.append(f"{pre}S448: {r['s448']} (log {u['log']})")
        for d, rel in u["unchecked_deps"].items():
            lines.append(f"note: reads {rel}, an output of {label_of(d, every)}, which this run (--only) did not "
                         f"rebuild; it is held to git HEAD only")
        if lines and (u["status"] != "ok" or u["unchecked_deps"]):
            problems.append((u["label"] if u["plates"] or not u["rows"] else u["rows"][0]["label"].strip(), lines))

    total = time.time() - t_all
    widths = [max(len(r[i]) for r in rows + [HEAD]) for i in range(len(HEAD))]
    print()
    for r in [HEAD, tuple("-" * w for w in widths)] + rows:
        print("  ".join(x.ljust(w) if i == 0 else x.rjust(w) if i in (1, 5) else x.ljust(w)
                        for i, (x, w) in enumerate(zip(r, widths))))
    print(f"\ntotal {total:.0f} s ({total / 60:.1f} min); seconds = the step's build commands; '+k in' = k committed "
          f"inputs in the folder, equal to git HEAD, not rebuilt:")
    for k, v in INPUTS.items():
        print(f"  {k}: {v}")
    print("audit = reads outside the repository and the allowed folders, or of a repository file that git HEAD does "
          "not hold or that differs from HEAD in this working tree (scripts/fig_read_audit.py); 'blocked by X' = the "
          "step reads an output of X, which failed or was blocked, so its own outputs are not compared")
    if platform:
        print("operating-system files read (allowed, fig_read_audit.PLATFORM):")
        for p, who in sorted(platform.items()):
            print(f"  {p}  ({', '.join(sorted(who))})")
    deps_txt = sorted({(u["short"], label_of(d, units)) for u in units for d in u.get("deps", {})})
    if deps_txt:
        print("reads between steps (audit): " + "; ".join(f"{a_} reads {b_}" for a_, b_ in deps_txt))
    if problems:
        print("\nDIFFERENCES AND FAILURES")
        for what, lines in problems:
            print(f"* {what}")
            for x in lines:
                print(f"    {x}")
    steps_ok = all(u["status"] == "ok" for u in units)
    frozen_checked = frozen_row is not None
    all_ok = frozen_checked and not frozen_failed and audit_on and steps_ok
    verdict = "ALL EQUAL AND PASSING" if all_ok else (
        "NOT VERIFIED: read audit off" if not audit_on and steps_ok and not frozen_failed
        else "PARTIAL: the frozen inputs were not checked (--only without frozen); the steps run are equal and "
             "passing" if not frozen_checked and steps_ok
        else "NOT ALL EQUAL OR PASSING")
    print(f"\n{verdict}; logs in {logs}")
    if out is not None and a.out is None and not a.keep:
        if all_ok:
            shutil.rmtree(out, ignore_errors=True)
            print(f"(temporary folder {out} removed; --keep keeps it)")
        else:
            print(f"(temporary folder {out} kept for the differences)")
    return 0 if all_ok else 1


HEAD = ("figure", "files", "byte-equal", "S448", "audit", "seconds")


def inputs_note(c: dict) -> str:
    return f" +{len(c['inputs']) + len(c['inputs_changed'])} in" if c["inputs"] or c["inputs_changed"] else ""


def describe(c: dict) -> list[str]:
    lines = []
    for name in c["differ"]:
        lines.append(f"differs: {name}")
        lines += [f"    {x}" for x in c["notes"].get(name, [])]
    lines += [f"not rebuilt (committed, not written by the step): {x}" for x in c["not_rebuilt"]]
    lines += [f"new (written, not committed): {x}" for x in c["new"]]
    lines += [f"absent (neither committed at git HEAD nor written by the step): {x}" for x in c.get("absent", [])]
    lines += [f"input changed in the working copy (differs from git HEAD): {x}" for x in c["inputs_changed"]]
    lines += [f"MANIFEST.sha256 does not hold the committed sha256 of: {x}" for x in c["manifest"]]
    return lines


# ---------------------------------------------------------------------------------------------------------------
# _call: run a script's main() with its output globals pointed elsewhere
# ---------------------------------------------------------------------------------------------------------------
def cmd_call(argv: list[str]) -> int:
    script = Path(argv[0])
    sets, argv0, rest = {}, False, []
    i = 1
    while i < len(argv):
        x = argv[i]
        if x == "--":
            rest = argv[i + 1:]
            break
        if x.startswith("--set="):
            k, v = x[len("--set="):].split("=", 1)
            sets[k] = OutPath(v)
        elif x.startswith("--setstr="):
            k, v = x[len("--setstr="):].split("=", 1)
            sets[k] = v
        elif x == "--argv0":
            argv0 = True
        i += 1
    path = (ROOT / script).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    sys.argv = [str(script), *rest]
    spec.loader.exec_module(mod)
    for k, v in sets.items():
        if not hasattr(mod, k):
            raise SystemExit(f"{script} has no global {k}")
        setattr(mod, k, v)
        if k.startswith("OUT") and isinstance(v, Path):
            (v if v.suffix == "" else v.parent).mkdir(parents=True, exist_ok=True)
    if callable(getattr(mod, "rel", None)):              # rel(p) = p relative to the repository: a path under --out
        inner = mod.rel                                  # prints as itself (Path(p) inside rel drops OutPath)

        def rel(p, *a, **k):
            try:
                return inner(p, *a, **k)
            except ValueError:
                return str(p)
        mod.rel = rel
    rc = mod.main(sys.argv) if argv0 else (mod.main(rest) if mod.main.__code__.co_argcount else mod.main())
    return int(rc or 0)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["_call"]:
        return cmd_call(argv[1:])
    if argv[:1] == ["manifest"]:
        return cmd_manifest("--check" in argv[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out")
    ap.add_argument("--tars")
    ap.add_argument("--only", action="append",
                    choices=["frozen", "d181", "fig1", "fig3", "fig4", "fig5", "fig6", "supp2", "supp5", "supp8",
                             "supp17", "supp7", "supp14_16", "supp10_11", "supp4", "supp9", "numbers", "need_map",
                             "supp1"])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--no-audit", action="store_true")
    a = ap.parse_args(argv)
    if a.write and a.out:
        ap.error("--write rebuilds in place; give --out or --write, not both")
    if a.write and "d181" in (a.only or ()):
        ap.error("d181 runs under --out only: S463 and S497 pin L3_d181/header.json, so --write must not rewrite it")
    return cmd_run(a)


if __name__ == "__main__":
    raise SystemExit(main())
