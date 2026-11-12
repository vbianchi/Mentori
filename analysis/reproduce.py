#!/usr/bin/env python3
"""reproduce.py (source: Mentori-reanalysis scripts/S608_reproduce.py, copied unchanged by S608_release_analysis.py into
Mentori-paper analysis/reproduce.py) - the one command that rebuilds the paper's figures, tables and numbers from the
released data and holds every output to the released copy.

    uv run --frozen python reproduce.py --data DIR [--work DIR] [--only STAGE ...] [--keep]
    uv run --frozen python reproduce.py --data DIR --download [--zenodo-url URL]
    uv run --frozen python reproduce.py --selftest     # the D316 mapping, hash module and held judgement; runs nothing

  --data DIR        the data root (env MENTORI_DATA): DIR/frozen/<the frozen tars>, DIR/analysis_inputs.tar and
                    DIR/stripped_records.tsv (D316), the names, sizes and sha256 DATA_FILES.tsv lists. Every file is checked against DATA_FILES.tsv first;
                    any file missing or with another sha256 stops the run before anything is built. One row is
                    optional (folder "optional"): DIR/ratings.tar, the anonymised rating rows (D313 R-Q1 O1). Absent,
                    Figure 2 and Supplementary Figure 3 are held by sha256; present with another sha256, the run stops.
  --download        fetch every file DATA_FILES.tsv lists that DIR does not hold yet, from
                    <zenodo-url>/files/<name>?download=1, into DIR (a .part file, renamed once its sha256 is right).
  --zenodo-url URL  the record's base URL. Default ZENODO_URL below, whose record id is TO FILL AFTER DEPOSIT.
  --work DIR        where the work copy goes (default: DIR/work). Must be new or empty.
  --only STAGE      s494, numbers or held (repeatable). Default: all three.
  --keep            keep the work copy (default: removed after a run whose stages all pass; kept after a failure).
  --skip-producer NAME   do not run producer NAME of the numbers stage (repeatable), e.g. S565, whose 20 fits of
                    10,000 bootstrap refits each took 45,000 s in all on 8 cores (about 12.5 hours; boot_seconds in
                    findings/recompute/S565_corpus_interaction/model.json). Its row is FAIL "not run", so a run
                    with a skip never ends REPRODUCED.

WHAT IT DOES
  1. Checks the data root against DATA_FILES.tsv (sha256 of every file; with --download, fetches the missing ones).
  2. Makes a work copy: this folder (without .venv, __pycache__ and earlier work copies), then analysis_inputs.tar
     unpacked into it at its repository paths. Then `git init`, `git add -A` and one commit with a fixed author and
     date, because S494 compares every output with git HEAD and its read audit fails any read of a file HEAD does not
     hold. Nothing in the analysis code is edited. With ratings.tar, its files are unpacked into the work copy and
     listed in its .gitignore, so none enters its git (D168); a member the tree already holds must have the same
     bytes. RATED's read audit allows exactly those paths.
  3. Stage s494: `uv run --frozen python scripts/S494_all_figures.py --out <work>_s494 --tars <DIR>/frozen` in the
     work copy, unchanged (its --out folder sits beside the work copy, outside it). It checks the frozen inputs, rebuilds every plate and number step it knows, compares each file
     byte for byte with the released copy, runs S448 on each plate, and judges every read (scripts/S494_all_figures.py
     docstring). Its own table is printed and each of its rows becomes a row of the pass table.
  4. Stage numbers: every producer in NUMBERS, run in the work copy by the command its docstring gives, one at a time,
     under the same read audit (scripts/fig_read_audit.py). A producer that writes in place is compared with git HEAD
     through `git status` (a tracked file it changed differs; an untracked file it left is new); one given an --out
     folder is compared file by file with its committed folder. A producer's "env" sets its environment variables:
     S534 t9 gets MENTORI_RUNS, the t3 folder of count_records_20261106.tar as fig_repro.frozen extracts it in the work
     copy. With ratings.tar, RATED runs last: S530 then S531 --raters 2, by their committed commands, under one audit,
     S530 with MENTORI_GENERATED_AT set to ratings.tar's findings/recompute/S530_human_signals/generated_at.txt (D315:
     the time of the run the released plates record, so the results.json whose sha256 their provenance files record is
     rebuilt byte for byte; a ratings.tar without that member leaves it unset, S530 stamps the current time, and the
     two provenance files then differ in that sha256 alone, shown as differing, never masked),
     each plate folder S531 writes (git-ignored in the work copy) compared file by file with its committed folder. A producer that compares no file fails ("compared no
     file"), so a command that writes nothing cannot pass. After each producer the work copy is reset to HEAD
     (`git checkout -- .`, `git clean -fdq`), so every producer reads the released inputs, as S494's steps do. A
     difference is never masked: the row shows the files that differ, and for a json file the key paths that differ.
  5. Stage held: every file of HELD (tier 3: needs a model call, a person, the rating rows or data not in the release)
     against its sha256 in expected/MANIFEST.sha256, each printed with the reason it is not rebuilt. RATED_HELD's
     entries (Figure 2, Supplementary Figure 3) are left out when RATED rebuilt them.
     No producer of NUMBERS or RATED opens the chunk store (S511 and S578 read env MENTORI_L1_STORE, default
     ~/l1_inputs/store, but S511 is in no stage and S578 --from-rows reads its committed rows), so reproduce.py sets no
     MENTORI_L1_STORE; a store read would show as an audit violation.
  6. One pass table, and the platform record (Python, the Helvetica the plates were drawn with). Exit 0 only when
     every stage passes.

THE PAPERS' TEXT (D316, Valerio 11 Nov: "we don't ship the papers"). The data record's frozen tars and its
analysis_inputs.tar are stripped (Mentori-reanalysis scripts/S627_strip_records.py): text sent to a model that carried
passages, and the retrieved passages and citation quotes, are each replaced by {"stripped": true, "sha256", "chars",
"passage_ids"}; model-written text stays. DATA_FILES.tsv pins the stripped files by their own sha256 and pins
stripped_records.tsv, one row per tar (empty member: the tar itself) and per member: original sha256, stripped sha256,
fields replaced. The analysis code is unchanged and pins the originals in many places (fig_repro.frozen(), the
members lists, committed manifests and provenance files, the tars' own checksum lists), so:
  - STRIPPED MEMBERS STAND FOR THEIR ORIGINALS IN HASH CHECKS. After the work copy is made, reproduce.py runs
    `uv sync --frozen` there and writes one module and one .pth file into the work copy's .venv site-packages
    (STRIP_MODULE). In every Python process of that venv, hashlib's sha256 then reports, for bytes whose sha256 is a
    stripped sha256 of stripped_records.tsv, the original's sha256 from the same row; every other input hashes as it
    is. Only these exact values are mapped, so any other change to a member still fails every pin. The venv is
    reproduce.py's own work copy; the analysis tree is not edited. A run without stripped_records.tsv in
    DATA_FILES.tsv (the originals) installs nothing.
  - OUTPUTS COMPUTED FROM A REPLACED FIELD ARE HELD, NOT REBUILT (D316). STRIPPED_HELD lists each, with the field it
    reads and the reason (measured by running every producer but S565 on the stripped and on the original data:
    resubmission/08_reproducibility/stripped_reads.json in Mentori-reanalysis). Such a file is checked by its sha256 in
    expected/MANIFEST.sha256 in the stage held. Where S494 rebuilds it, S494 runs once with every step (its rows show
    the difference in that file, never masked) and the rows whose only differences are STRIPPED_HELD files pass with
    the note "held (D316)"; the steps S494 then reported blocked by such a row are run again in a second S494 pass with
    --only (the held step left out, so its committed outputs stand, as S494 does for any step not run), and their rows
    are taken from that pass. A producer of the numbers stage whose only differences are STRIPPED_HELD files passes
    the same way; every other difference fails as before.

THE FIDELITY RULE (README.md, "What 100% means"). Numbers, tables and Source Data: byte-equal. Plates: byte-equal
with the font the plates were made with (PLATE_FONT); with another font or none, a plate row that differs is
reported with the note "font differs", never as reproduced. Held values: equal sha256.

Standard library only (it runs before anything else is installed); it imports scripts/fig_read_audit.py from the
work copy for the numbers stage.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZENODO_URL = "https://zenodo.org/records/TO-FILL-AFTER-DEPOSIT"   # TO FILL AFTER DEPOSIT: the record's id
DATA_FILES = HERE / "DATA_FILES.tsv"
EXPECTED = HERE / "expected" / "MANIFEST.sha256"
UV = ["uv", "run", "--frozen", "python"]
# The font every plate was drawn with (S494's platform list: /System/Library/Fonts/Helvetica.ttc, macOS); its sha256
# as read on the machine that made the committed plates (S608 records it at build time).
PLATE_FONT = "/System/Library/Fonts/Helvetica.ttc"
PLATE_FONT_SHA256 = "25eceb458d4baf628ee0b6a135a9f8ac5ec7b2826646720834bd2bf00dfc825a"
GIT_ENV = {"GIT_AUTHOR_NAME": "reproduce.py", "GIT_AUTHOR_EMAIL": "reproduce@localhost",
           "GIT_COMMITTER_NAME": "reproduce.py", "GIT_COMMITTER_EMAIL": "reproduce@localhost",
           "GIT_AUTHOR_DATE": "2026-11-08T00:00:00Z", "GIT_COMMITTER_DATE": "2026-11-08T00:00:00Z"}
WORK_IGNORE = """.venv/
__pycache__/
*.pyc
.DS_Store
/findings/recompute/frozen_inputs/extracted/
/findings/recompute/S530_human_signals/
/findings/recompute/S531_plates/
"""
# ratings.tar (D313 R-Q1 O1, built by Mentori-reanalysis scripts/S626_release_extras.py ratings_entries and staged by
# S610): the anonymised rating rows S530 --ratings reads, S08's v2.2 results S530's gate reproduces, the master sheet
# they were collected on, the rating protocol, and the Supplementary Figure 3 data file and caption (also in this tree,
# the same bytes). DATA_FILES.tsv lists it in folder "optional": when the data root holds it with that sha256, make_work
# unpacks it into the work copy and the numbers stage redraws Figure 2 and Supplementary Figure 3 (RATED); when it is
# absent, or DATA_FILES.tsv has no row for it, the two plates are held by sha256 (HELD, RATED_HELD).
RATINGS_TAR = "ratings.tar"
RATINGS_MEMBERS = {"findings/recompute/S354_v22_human_ratings.csv",     # S530 --ratings (D168: never in git)
                   "findings/recompute/S08_v22_results.json",           # S530's gate reproduces it
                   "response/human_eval_v22/human_eval_master_v22.csv",  # the master, every rating cell blank
                   "findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md"}          # the protocol, its decision rule
# D315 Q4 O2: one line, S530's "generated" time in the run the released plates record. Optional: an older ratings.tar
# lacks it, and RATED then runs S530 without MENTORI_GENERATED_AT (its provenance files then differ, never masked).
GENERATED_AT_MEMBER = "findings/recompute/S530_human_signals/generated_at.txt"

# ---------------------------------------------------------------------------------------------------------------
# Tier 2: the producers of the numbers and tables outside S494. Each: name, what it makes, the command (as its
# docstring gives it), and, when the command takes an --out folder ("{out}"), the committed folder it is held to.
# ---------------------------------------------------------------------------------------------------------------
NUMBERS = [
    # the three plates are drawn into --out and held to their committed folder file by file: in place, each draws into a
    # .staging folder it then renames, so the comparison by git status saw no written released file and the audit
    # flagged the staged PNG as a read outside HEAD (S608 measure, 9 Nov)
    {"name": "S543", "label": "Supplementary Figure 12",
     "cmd": ["scripts/S543_supp_signal_pairs.py", "figure", "--out", "{out}"],
     "committed": "findings/figures_provisional/supp_fig12_signal_pairs"},
    {"name": "S570", "label": "Supplementary Figure 13", "cmd": ["scripts/S570_supp_i2_reuse.py", "figure", "--out", "{out}"],
     "committed": "findings/figures_provisional/supp_fig13_i2_reuse"},
    {"name": "S542", "label": "Supplementary Figure 18", "cmd": ["scripts/S542_supp_evaluators.py", "figure", "--out", "{out}"],
     "committed": "findings/figures_provisional/supp_fig18_evaluators"},
    {"name": "S583", "label": "Supplementary Table 1", "cmd": ["scripts/S583_judge_calibration_table.py"]},
    {"name": "S534 t1", "label": "Supplementary Table answer counts", "cmd": ["scripts/S534_si_tables.py", "t1"]},
    # t9 reads the T3 frozen set from env MENTORI_RUNS (Q5 O1, D313): the folder holding T3_frozen_20261104T131439Z,
    # here count_records_20261106.tar's t3/ as fig_repro.frozen extracts it inside the work copy ("{frozen:SET:REL}")
    {"name": "S534 t9", "label": "Supplementary Table 3", "cmd": ["scripts/S534_si_tables.py", "t9"],
     "env": {"MENTORI_RUNS": "{frozen:count_records_20261106:count_records_20261106/t3}"}},
    {"name": "S533", "label": "Supplementary Table 66 questions", "cmd": ["scripts/S533_table_66_questions.py"]},
    {"name": "S535", "label": "Supplementary Table human evaluation grid (frame)",
     "cmd": ["scripts/S535_table_human_grid.py", "frame"]},
    {"name": "S582", "label": "Supplementary Data 1 (the answer key)", "cmd": ["scripts/S582_answer_key_table.py"]},
    {"name": "S520", "label": "language-model call counts", "cmd": ["scripts/S520_llm_calls.py", "report", "--frozen"]},
    {"name": "S603", "label": "tokens and cost", "cmd": ["scripts/S603_tokens_cost.py", "report"]},
    {"name": "S575", "label": "G17 contrasts", "cmd": ["scripts/S575_g17_contrasts.py"]},
    {"name": "S576", "label": "D249 hypotheses", "cmd": ["scripts/S576_d249_hypotheses.py"]},
    # S578 and S595 --from-rows: the reproduce-only check, then the table, contrasts and hypotheses of the committed
    # reading (reading.md: Supplementary Note 5) computed again from its per-answer rows, which are held (their sinks,
    # judge folders and chunk store are not released); S612: --reproduce-only alone compared no file
    {"name": "S578", "label": "G19 reading (from the committed rows)",
     "cmd": ["scripts/S578_g19_reading.py", "--from-rows", "--r-collect-t2x",
             "findings/recompute/S518_inputs/gemma3/t2x_collect.jsonl", "--out", "{out}"],
     "committed": "findings/recompute/G19_reading"},
    {"name": "S595", "label": "G20 reading (from the committed rows)",
     "cmd": ["scripts/S595_g20_reading.py", "--from-rows", "--r-collect-t2x",
             "findings/recompute/S518_inputs/qwen3-coder/t2x_collect.jsonl", "--out", "{out}"],
     "committed": "findings/recompute/G20_reading"},
    {"name": "S518", "label": "T2 split confirmation (reference)",
     "cmd": ["scripts/S518_split_confirmation.py", "reference"]},
    {"name": "S566", "label": "answer length and concept recall", "cmd": ["scripts/S566_length_recall.py"]},
    {"name": "S580", "label": "code generation passages", "cmd": ["scripts/S580_codegen_passages.py"]},
    {"name": "S581", "label": "depth logistic fit", "cmd": ["scripts/S581_depth_logistic.py"]},
    {"name": "S591", "label": "routing fix by draw", "cmd": ["scripts/S591_routing_fix_by_draw.py"]},
    {"name": "S525", "label": "Figure 7 S4 check", "cmd": ["scripts/S525_fig6_s4_check.py"]},
    {"name": "S565", "label": "strategy by corpus size interaction",
     "cmd": ["scripts/S565_corpus_interaction.py", "run", "--out", "{out}"],
     "committed": "findings/recompute/S565_corpus_interaction"},
    {"name": "S596", "label": "windowed BERTScore (roberta-large, an encoder)",
     "cmd": ["scripts/S596_windowed_bertscore.py", "run", "--out", "{out}"],
     "committed": "findings/recompute/S596_windowed_bertscore"},
    # S602 (the Supplementary Information PDF and .docx) is not here (D2, Valerio, 8 Nov): it builds a document from
    # the agreed manuscript text (resubmission/06_supplementary/si_text_from_doc_20261107.md), an editorial step run in
    # Mentori-reanalysis; the release ships no document and reads none. content_equal (fidelity rule 3) stays for a
    # producer that needs it.
]

# Run only when the data root holds ratings.tar (RATINGS_TAR): S530 then S531, each by the command its committed run
# recorded (findings/recompute/S530_human_signals/results.json _provenance.command; the plates' *_provenance.json
# command), so the rebuilt files carry the same commands. "cmds" run in order under one audit; "compare" holds each
# folder the chain writes (inside the work copy, git-ignored there, removed after the comparison) to its committed
# folder, file by file. The upstream files S530 reads through S08 (exp04_generation_latest.json, exp04_minicheck_latest
# .json, analysis_human_eval_20260310.key.json) are in analysis_inputs.tar under data/upstream/publication/results/.
RATED = [
    {"name": "S530+S531", "label": "Figure 2 and Supplementary Figure 3 (from ratings.tar)",
     # D315: env "from_file" values are read from the work copy before the scratch folders are emptied
     "env_from_file": {"MENTORI_GENERATED_AT": GENERATED_AT_MEMBER},
     "cmds": [["scripts/S530_human_signals.py", "--raters", "2", "--ratings",
               "findings/recompute/S354_v22_human_ratings.csv"],
              ["scripts/S531_fig2_s3_plates.py", "--raters", "2"]],
     "compare": [("findings/recompute/S531_plates/fig2_human", "findings/figures_provisional/fig2_human"),
                 ("findings/recompute/S531_plates/supp_fig3", "findings/figures_provisional/supp_fig3")],
     "scratch": ["findings/recompute/S530_human_signals", "findings/recompute/S531_plates"]},
]

# ---------------------------------------------------------------------------------------------------------------
# Tier 3: held by sha256, each with the reason it is not rebuilt here. Paths are files or folders (every file under).
# ---------------------------------------------------------------------------------------------------------------
HELD = [
    ("Figure 2", "findings/figures_provisional/fig2_human",
     "drawn by S531 from S530's reading of the rating rows; the data root holds no ratings.tar with the sha256 "
     "DATA_FILES.tsv gives (RATED redraws it when it does)"),
    ("Supplementary Figure 3", "findings/figures_provisional/supp_fig3",
     "drawn by S531 from the rating rows, as Figure 2"),
    ("judge lock check", "findings/recompute/S440_judge_lock_check.md", "S440 calls the judge through Ollama"),
    ("judge lock check", "findings/recompute/S440_judge_lock_check.jsonl", "S440 calls the judge through Ollama"),
    ("judge lock check, Beelink", "findings/recompute/S440_judge_lock_check_beelink.md",
     "S440 calls the judge through Ollama"),
    ("judge lock check, Beelink", "findings/recompute/S440_judge_lock_check_beelink.jsonl",
     "S440 calls the judge through Ollama"),
    ("judge lock check, laptop", "findings/recompute/S440_judge_lock_check_laptop.md",
     "S440 calls the judge through Ollama"),
    ("judge lock check, laptop", "findings/recompute/S440_judge_lock_check_laptop.jsonl",
     "S440 calls the judge through Ollama"),
    ("unsupported claim types", "findings/recompute/S606_prediction.md", "S606 runs MiniCheck and calls Ollama"),
    ("unsupported claim types", "findings/recompute/S606_units.json", "S606 runs MiniCheck and calls Ollama"),
    ("refusal check by a person", "findings/recompute/S607_refusal_person_check",
     "S607 reads a sheet a person filled in; its per-row readings are not released (D306)"),
    ("RLM reading (G17)", "findings/recompute/S571_rlm_reading",
     "S571 reads the chunk store ~/l1_inputs/store/chroma.sqlite3, which is not in this release (Q2, Q5)"),
    ("judge calibration", "findings/recompute/S376_calibration_analysis.json",
     "S376b reads the submission's deposit in data/upstream/ (doi 10.5281/zenodo.19476756), not in this release"),
    ("judge calibration", "findings/recompute/S376_calibration_analysis.md", "as S376_calibration_analysis.json"),
    ("judge calibration, extended", "findings/recompute/S404",
     "S404 --analyze reads data/upstream/ (the submission's deposit), not in this release"),
    ("judge choice evidence", "findings/recompute/S405_judge_choice_evidence.json",
     "S405 reads data/upstream/ (the submission's deposit), not in this release"),
    ("judge choice evidence", "findings/recompute/S405_judge_choice_evidence.md", "as the .json"),
    ("question-aware matcher", "findings/recompute/S505_question_aware",
     "S505 reads data/upstream/ (the submission's deposit), not in this release"),
    ("selection concept recall v2.5", "findings/recompute/S432_selection_concept_recall_v25.json",
     "S432 reads the merged ledger findings/recompute/S388_rejudge_v22, which is not committed"),
    ("selection concept recall v2.5", "findings/recompute/S432_selection_concept_recall_v25.md", "as the .json"),
    ("judge evidence v2.5", "findings/recompute/S18f_v25_results.md",
     "S18f analyze reads the judge run folders; reproduce.py does not run it (not tried)"),
    ("judge evidence v2.5", "findings/recompute/S18f_v25_results.json", "as the .md"),
    ("Supplementary Table 2", "findings/figures_provisional/supp_tables/Supplementary Table 2.xlsx",
     "S534 t7 lists findings/recompute/I2_runs/sinks, which is not committed"),
    ("Supplementary Table 2", "findings/figures_provisional/supp_tables/Supplementary Table 2.md", "as the .xlsx"),
    ("baseline strategy rank", "findings/recompute/S597_baseline_strategy_rank",
     "S597 at the release commit stops on the committed Figure 3 Source Data (KeyError 'row_kind')"),
    ("signal run time", "findings/recompute/S598_signal_run_time",
     "S598 at the release commit stops on the committed Figure 6 Source Data (KeyError 'Fig. 5e')"),
    ("key v2.5 curation hours", "findings/recompute/S599_key_v25_curation_hours",
     "S599 reads the answer key's review and sign-off workbooks in response/ground_truth_v2/, which are not released "
     "(D168: response/ stays out)"),
    ("retrieval sweep provenance", "findings/recompute/S601_retrieval_sweep_provenance",
     "S601 reads the git history of the sibling repository Mentori-backup, not in this release"),
]
RATED_HELD = {"findings/figures_provisional/fig2_human", "findings/figures_provisional/supp_fig3"}   # RATED rebuilds

# ---------------------------------------------------------------------------------------------------------------
# D316: the stripped data. STRIPPED_TSV is the mapping DATA_FILES.tsv pins; STRIPPED_HELD the outputs that read a
# replaced field: (label, path, step or producer that writes it, reason). Each is checked by its sha256 in
# expected/MANIFEST.sha256 (stage held) and its difference, where a stage rebuilds it, is shown and not failed.
# ---------------------------------------------------------------------------------------------------------------
STRIPPED_TSV = "stripped_records.tsv"
ACTIVE_HELD: list[dict] = []      # STRIPPED_HELD when the data root is stripped (main sets it), else nothing is held
STRIP_MODULE = "_d316_stripped_sha256"
# Measured 12 Nov (Mentori-reanalysis resubmission/08_reproducibility/stripped_reads.json): every producer but S565
# (not run: its 10,000-refit run takes 12.5 h; it reads judge scores and committed numbers) run on the stripped and on the original data, in a
# work copy made as below; these files, and only these, differ.
_RAW = ("answers.json .results[].generation.steps[].raw_content, a pipeline step's tool output, replaced by the "
        "stripped object: the script takes its len(), which is 4 (the object's keys), not the text's length")
STRIPPED_HELD: list[dict] = [
    {"label": "Supplementary Figure 12a step rows", "path": "findings/recompute/S472_supp12a_steps.json",
     "stage": "s494", "step": "fig4", "by": "S494 step fig4 (scripts/S472_fig4_panels.py)", "field": _RAW,
     "reason": "each step row's output length (rows[][5]) and the totals after it are computed from the replaced "
               "text; the stripped object's chars field holds that length, which the script does not read"},
    {"label": "Figure 5 provenance", "path": "findings/figures_provisional/fig4/figure5_provenance.json",
     "stage": "s494", "step": "fig4", "by": "S494 step fig4 (scripts/S472_fig4_panels.py)", "field": _RAW,
     "reason": "q82.<setup>.largest_chars and the largest step output it reproduces are computed from the replaced "
               "text; the plate and Source Data Fig. 5 rebuild byte-equal"},
    {"label": "distiller firing count, draw 1", "path": "findings/recompute/distiller_count_g3_d1/distiller_count_g3_d1.json",
     "stage": "s494", "step": "numbers", "by": "S494 step numbers (scripts/distiller_count_g3_d1.py)", "field": _RAW,
     "reason": "largest_step_output.chars and the check against RUNNING.md's 26 Oct count are computed from the "
               "replaced text"},
]



# ---------------------------------------------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def data_files() -> list[dict]:
    """DATA_FILES.tsv: name, bytes, sha256, folder under the data root ("frozen" or "."), description."""
    rows = []
    for line in DATA_FILES.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("name\t"):
            continue
        name, size, sha, folder, desc = line.split("\t", 4)
        rows.append({"name": name, "bytes": int(size), "sha256": sha, "folder": folder, "desc": desc})
    return rows


def where(data: Path, row: dict) -> Path:
    """Folder "." and "optional" (a file the run uses when present, ratings.tar) sit at the data root."""
    return data / row["name"] if row["folder"] in (".", "optional") else data / row["folder"] / row["name"]


def download(url: str, dest: Path, row: dict) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    print(f"  fetching {row['name']} ({row['bytes']:,} bytes) from {url}", flush=True)
    with urllib.request.urlopen(url) as r, open(part, "wb") as fh:
        shutil.copyfileobj(r, fh, 1 << 20)
    got = sha256_file(part)
    if got != row["sha256"]:
        part.unlink()
        raise SystemExit(f"REFUSED: {row['name']} downloaded with sha256 {got}, DATA_FILES.tsv gives {row['sha256']}")
    part.rename(dest)


def check_data(data: Path, fetch: bool, base_url: str) -> tuple[list[str], set[str]]:
    """Every row's file checked by sha256; returns the lines to print and the optional files present and equal. An
    optional file that is absent is printed and skipped (with --download it is fetched like any other); one present
    with another sha256 refuses the run, as any other file does."""
    lines, bad, optional = [], [], set()
    for row in data_files():
        p = where(data, row)
        if row["folder"] == "optional" and not p.is_file() and not fetch:
            lines.append(f"{row['name']}: absent (optional): what it rebuilds is held by sha256")
            continue
        if not p.is_file() and fetch:
            if "TO-FILL-AFTER-DEPOSIT" in base_url:
                raise SystemExit("REFUSED: the Zenodo record id is not filled in yet: give --zenodo-url")
            download(f"{base_url.rstrip('/')}/files/{row['name']}?download=1", p, row)
        if not p.is_file():
            bad.append(f"{p} is missing (DATA_FILES.tsv: {row['name']}, {row['bytes']:,} bytes)")
            continue
        got = sha256_file(p)
        if got != row["sha256"]:
            bad.append(f"{p}: sha256 {got[:12]}, DATA_FILES.tsv {row['sha256'][:12]}")
        else:
            lines.append(f"{row['name']}: sha256 {got[:12]} equal")
            if row["folder"] == "optional":
                optional.add(row["name"])
    if bad:
        raise SystemExit("REFUSED: the data root does not match DATA_FILES.tsv:\n  " + "\n  ".join(bad))
    return lines, optional


def strip_map(data: Path) -> dict[str, str]:
    """D316: stripped sha256 -> original sha256, from the data root's stripped_records.tsv (checked by sha256 in
    check_data). Empty when DATA_FILES.tsv lists no STRIPPED_TSV (a data root of originals). Each tar row's stripped
    sha256 must be the sha256 DATA_FILES.tsv pins for that tar, so the mapping is the one for these very files."""
    rows = {r["name"]: r for r in data_files()}
    if STRIPPED_TSV not in rows:
        return {}
    lines = where(data, rows[STRIPPED_TSV]).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].split("\t") != ["tar", "member", "original_sha256", "stripped_sha256", "fields_stripped"]:
        raise SystemExit(f"REFUSED: {STRIPPED_TSV} has not the columns tar, member, original_sha256, stripped_sha256, "
                         "fields_stripped")
    out, tars, bad = {}, set(), []
    hexa = re.compile(r"[0-9a-f]{64}")
    for ln in lines[1:]:
        if not ln.strip():
            continue
        tar, member, orig, stripped, _ = ln.split("\t", 4)
        if not (hexa.fullmatch(orig) and hexa.fullmatch(stripped)):
            bad.append(f"{tar}!{member}: not two sha256 values")
            continue
        if not member:
            tars.add(tar)
            if tar not in rows or rows[tar]["sha256"] != stripped:
                bad.append(f"{tar}: its stripped sha256 {stripped[:12]} is not DATA_FILES.tsv's pin")
        if orig != stripped:
            if out.get(stripped, orig) != orig:
                bad.append(f"{tar}!{member}: one stripped sha256 stands for two originals")
            out[stripped] = orig
    missing = [n for n, r in rows.items() if r["name"].endswith(".tar") and r["folder"] != "optional"
               and n not in tars]
    if missing:
        bad.append(f"{STRIPPED_TSV} has no row for {missing}")
    if bad:
        raise SystemExit("REFUSED: " + STRIPPED_TSV + ":\n  " + "\n  ".join(bad[:10]))
    return out


STRIP_SHIM = '''# Written by reproduce.py (D316) into its work copy's venv only; see reproduce.py "THE PAPERS' TEXT".
# hashlib.sha256 reports a stripped member's (or tar's) original sha256, from the data root's stripped_records.tsv;
# every other input hashes as it is.
import hashlib as _h

_JSON = %r
_MAP = None
_raw = _h.sha256
_new = _h.new


def _m():
    global _MAP
    if _MAP is None:
        import json
        _MAP = json.loads(_JSON)
    return _MAP


class _Sha256:
    name, digest_size, block_size = "sha256", 32, 64

    def __init__(self, data=b"", **kw):
        self._o = _raw(data, **kw)

    def update(self, data):
        self._o.update(data)

    def hexdigest(self):
        x = self._o.hexdigest()
        return _m().get(x, x)

    def digest(self):
        return bytes.fromhex(self.hexdigest())

    def copy(self):
        c = _Sha256.__new__(_Sha256)
        c._o = self._o.copy()
        return c


def _sha256(data=b"", **kw):
    return _Sha256(data, **kw)


def _hnew(name, data=b"", **kw):
    if str(name).lower().replace("-", "").replace("_", "") == "sha256":
        return _Sha256(data, **kw)
    return _new(name, data, **kw)


_h.sha256 = _sha256
_h.new = _hnew
'''


def install_strip_map(work: Path, mapping: dict[str, str], log: Path) -> str:
    """D316: `uv sync --frozen` in the work copy, then STRIP_MODULE.py and STRIP_MODULE.pth into its venv's
    site-packages. Returns a line for the run's log."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    with open(log, "w") as fh:
        rc = subprocess.run(["uv", "sync", "--frozen"], cwd=work, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
    if rc:
        raise SystemExit(f"REFUSED: `uv sync --frozen` in the work copy exited {rc} (log {log})")
    r = subprocess.run([*UV, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], cwd=work, env=env,
                       capture_output=True, text=True, check=True)
    site = Path(r.stdout.strip().splitlines()[-1]).resolve()
    if work.resolve() not in site.parents:
        raise SystemExit(f"REFUSED: the work copy's site-packages {site} is not inside the work copy")
    (site / f"{STRIP_MODULE}.py").write_text(STRIP_SHIM % json.dumps(mapping, sort_keys=True), encoding="utf-8")
    (site / f"{STRIP_MODULE}.pth").write_text(f"import {STRIP_MODULE}\n", encoding="utf-8")
    code = (f"import sys, hashlib; print('{STRIP_MODULE}' in sys.modules, hashlib.sha256(b'').hexdigest() == "
            "'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')")
    got = subprocess.run([*UV, "-c", code], cwd=work, env=env, capture_output=True, text=True).stdout.split()
    if got != ["True", "True"]:
        raise SystemExit(f"REFUSED: the stripped-sha256 module did not load in the work copy's venv ({site})")
    return f"{len(mapping):,} stripped sha256 values stand for their originals in the work copy's venv ({site.name})"


def unpack_ratings(work: Path, tar: Path) -> list[str]:
    """ratings.tar into the work copy. A member the analysis tree already holds (the Supplementary Figure 3 data file
    and caption) must have the same bytes and is not written again; any other difference refuses. Every member of
    RATINGS_MEMBERS must be there. Returns the paths written: make_work lists them in the work copy's .gitignore, so no
    rating file enters its git (D168), and RATED's read audit allows exactly these paths ("allowed"). No member's
    content is printed."""
    with tarfile.open(tar) as t:
        members = t.getmembers()
        names = {m.name for m in members if m.isfile()}
        if RATINGS_MEMBERS - names:
            raise SystemExit(f"REFUSED: {tar} lacks {len(RATINGS_MEMBERS - names)} of the files S530 reads, e.g. "
                             f"{sorted(RATINGS_MEMBERS - names)[0]}")
        new = []
        for m in members:
            if m.name.startswith("/") or ".." in Path(m.name).parts or not (m.isfile() or m.isdir()):
                raise SystemExit(f"REFUSED: {tar} member {m.name!r} is not a plain relative file")
            if not m.isfile():
                continue
            if (work / m.name).exists():
                if (work / m.name).read_bytes() != t.extractfile(m).read():
                    raise SystemExit(f"REFUSED: {tar} member {m.name} differs from the analysis tree's copy")
                continue
            new.append(m)
        t.extractall(work, members=new, filter="data")
    return sorted(m.name for m in new)


def make_work(work: Path, data: Path, ratings: Path | None = None) -> list[str]:
    """The work copy; returns the paths unpacked from ratings (empty without it), git-ignored there."""
    def ignore(d, names):
        skip = {".venv", "__pycache__", ".DS_Store"}
        here = Path(d).resolve()
        return [n for n in names if n in skip or (here / n).resolve() in (work.resolve(), data.resolve())]
    shutil.copytree(HERE, work, ignore=ignore, symlinks=False, dirs_exist_ok=True)
    tar = data / "analysis_inputs.tar"
    with tarfile.open(tar) as t:
        members = t.getmembers()
        for m in members:
            if m.name.startswith("/") or ".." in Path(m.name).parts or not (m.isfile() or m.isdir()):
                raise SystemExit(f"REFUSED: {tar} member {m.name!r} is not a plain relative file")
            if m.isfile() and (work / m.name).exists():
                raise SystemExit(f"REFUSED: {tar} member {m.name} would overwrite a file of the analysis tree")
        t.extractall(work, members=members, filter="data")
    unpacked = unpack_ratings(work, ratings) if ratings is not None else []
    if ratings is not None:
        print(f"  {ratings.name}: {len(unpacked)} files unpacked into the work copy, git-ignored there", flush=True)
    (work / ".gitignore").write_text(WORK_IGNORE + "".join(f"/{p}\n" for p in unpacked))
    env = {**os.environ, **GIT_ENV}
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "reproduce.py work copy"]):
        subprocess.run(cmd, cwd=work, env=env, check=True)
    return unpacked


# ---------------------------------------------------------------------------------------------------------------
# Stage s494
# ---------------------------------------------------------------------------------------------------------------
def parse_s494_table(text: str) -> list[dict]:
    """The rows of S494's table (between its dashes line and the blank line after it), by column position."""
    lines = text.splitlines()
    rows = []
    for i, line in enumerate(lines):
        if re.match(r"^-{20,}\s+-{3,}", line):
            spans = [(m.start(), m.end()) for m in re.finditer(r"-+", line)]
            for row in lines[i + 1:]:
                if not row.strip():
                    break
                cells = []
                for k, (a, _) in enumerate(spans):
                    b = spans[k + 1][0] if k + 1 < len(spans) else None
                    cells.append(row[a:b].strip() if b else row[a:].strip())
                rows.append(dict(zip(["figure", "files", "equal", "s448", "audit", "secs"], cells)))
            break
    return rows


def row_ok(r: dict) -> bool:
    eq = r["equal"]
    if r["figure"] == "frozen inputs":
        return eq == "checked"
    m = re.match(r"(\d+) of (\d+)", eq)
    good = bool(m) and m.group(1) == m.group(2)
    s448 = r["s448"]
    good &= (not s448) or ("FAIL" not in s448 and "not" not in s448 and "exit" not in s448)
    return good and r["audit"] in ("0", "")


def parse_s494_problems(text: str) -> dict[str, list[str]]:
    """S494's DIFFERENCES AND FAILURES: block label ("* <label>") -> its lines, the block's 4-space indent removed."""
    out, cur = {}, None
    lines = text.splitlines()
    try:
        i = lines.index("DIFFERENCES AND FAILURES")
    except ValueError:
        return out
    for ln in lines[i + 1:]:
        if ln.startswith("* "):
            cur = ln[2:].strip()
            out[cur] = []
        elif cur is not None and ln.startswith("    "):
            out[cur].append(ln[4:])
        elif cur is not None and not ln.strip():
            continue
        elif cur is not None:
            break
    return out


_PROBLEM = re.compile(r"^(?:(?P<pre>.+?): )?(?:differs: (?P<f>.+)|(?P<note>\s{4}\S.*))$")


def held_in_s494(problems: dict[str, list[str]], held: list[dict]) -> dict[str, list[str]]:
    """D316: row label -> the STRIPPED_HELD paths that differ in it, for every problem block whose lines are only
    "differs: <file>" (each file a STRIPPED_HELD output), the key or line notes under them, and "note: reads ..."
    lines (a step not run in an --only pass). Any other line (an exit, an audit read, a file not rebuilt or new, S448,
    a block) leaves the block failed."""
    out: dict[str, list[str]] = {}
    for block, lines in problems.items():
        found, ok = {}, bool(lines)
        for ln in lines:
            if ln.startswith("note: reads "):
                continue
            m = _PROBLEM.match(ln)
            if not m:
                ok = False
                break
            if m.group("f") is None:
                continue
            f = m.group("f").strip()
            hit = [h["path"] for h in held if h["stage"] == "s494" and (h["path"] == f or h["path"].endswith("/" + f))]
            if not hit:
                ok = False
                break
            found.setdefault((m.group("pre") or block).strip(), []).extend(hit)
        if ok and found:
            out.update(found)
    return out


def judge_s494(text: str, held: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    """S494's table rows, each with "ok" and "note"; a row whose only differences are STRIPPED_HELD files passes,
    noted "held (D316)". Returns (rows, the held paths by row label)."""
    hmap = held_in_s494(parse_s494_problems(text), held)
    rows = []
    for r in parse_s494_table(text):
        ok = row_ok(r)
        note = r["equal"] + (f"; S448 {r['s448']}" if r["s448"] else "")
        hp = hmap.get(r["figure"])
        m = re.match(r"(\d+) of (\d+)", r["equal"])
        if not ok and hp and m and int(m.group(2)) - int(m.group(1)) == len(hp) and r["audit"] in ("0", "") \
                and not any(x in r["s448"] for x in ("FAIL", "not", "exit")):
            ok = True
            note += "; held (D316), computed from a replaced field, checked by sha256 in stage held: " + ", ".join(hp)
        rows.append({**r, "ok": ok, "note": note})
    return rows, hmap


def s494_steps(work: Path, env: dict) -> list[str]:
    """S494's step names, in its order, from the work copy's own S494 (steps() of an --out run)."""
    code = ("import sys; sys.path.insert(0, 'scripts'); import S494_all_figures as S; "
            "from pathlib import Path; print(' '.join(s['name'] for s in S.steps(Path('/nonexistent/out'))))")   # an --out
    # run: steps(None) is the --write list, which leaves out d181
    r = subprocess.run([*UV, "-c", code], cwd=work, env=env, capture_output=True, text=True)
    if r.returncode or not r.stdout.strip():
        raise SystemExit("REFUSED: could not list S494's steps in the work copy: " + (r.stderr.strip()[-300:]))
    return r.stdout.split()


def stage_s494(work: Path, data: Path, font_ok: bool) -> list[dict]:
    out = work.parent / (work.name + "_s494")              # outside the work copy: S494 judges writes into it
    log = work.parent / (work.name + "_s494.log")
    cmd = [*UV, "scripts/S494_all_figures.py", "--out", str(out), "--tars", str((data / "frozen").resolve())]
    print("$ " + " ".join(cmd), flush=True)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=work, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    text = log.read_text(errors="replace")
    print(text, flush=True)
    parsed, hmap = judge_s494(text, ACTIVE_HELD)
    second = None
    # D316: the steps S494 reported blocked by a step whose only differences are held files run again without that
    # step, so its committed outputs stand (S494 notes them "held to git HEAD only"); their rows replace the blocked ones
    held_rows = set(hmap)
    blocked = [r for r in parsed if r["equal"].startswith("blocked by")]
    if held_rows and blocked:
        held_steps = {h["step"] for h in ACTIVE_HELD if h["stage"] == "s494"}
        blockers = {b.strip() for r in blocked for b in r["equal"][len("blocked by "):].split(",")}
        # a held step that blocked other steps is left out of the second pass; only the blocked rows are taken from
        # that pass, so a row of the held step itself that failed in pass 1 for any other reason stays failed
        names = s494_steps(work, env)
        leave_out = {s for s in held_steps if s in blockers and s in names}
        only = [s for s in names if s not in leave_out and s not in ("frozen", "text")]
        out2, log2 = work.parent / (work.name + "_s494_pass2"), work.parent / (work.name + "_s494_pass2.log")
        cmd2 = [*UV, "scripts/S494_all_figures.py", "--out", str(out2), "--tars", str((data / "frozen").resolve())]
        for s_ in only:
            cmd2 += ["--only", s_]
        print("$ " + " ".join(cmd2) + "   # D316: second pass, held steps left out: " + ", ".join(sorted(leave_out)),
              flush=True)
        with open(log2, "w") as fh:
            rc2 = subprocess.run(cmd2, cwd=work, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
        text2 = log2.read_text(errors="replace")
        print(text2, flush=True)
        p2, h2 = judge_s494(text2, ACTIVE_HELD)
        second = {"rc": rc2, "rows": {r["figure"]: r for r in p2}, "left_out": leave_out, "log": log2}
    rows = []
    for r in parsed:
        if second and r["equal"].startswith("blocked by") and r["figure"] in second["rows"]:
            r2 = second["rows"][r["figure"]]
            r = {**r2, "note": r2["note"] + f"; from the second S494 pass (pass 1: {r['equal']}; "
                                            f"left out: {', '.join(sorted(second['left_out']))})"}
        ok, note = r["ok"], r["note"]
        if not ok and not font_ok and r["figure"].startswith(("Figure", "Supplementary Figure")):
            note += "; font differs from the plates' font (fidelity rule 2): not reproduced, check visually"
        rows.append({"stage": "s494", "item": r["figure"], "files": r["files"], "ok": ok, "note": note})
    if not rows:
        rows.append({"stage": "s494", "item": "S494", "files": "", "ok": False, "note": f"no table; exit {rc}"})
    others_ok = bool(parsed) and all(x["ok"] for x in rows)
    rows.append({"stage": "s494", "item": "S494 exit code", "files": "", "ok": rc == 0 or (bool(hmap) and others_ok),
                 "note": f"exit {rc} (log {log})" + (
                     f"; every difference is a held (D316) file, shown in its row" if rc and hmap and others_ok else "")
                 + (f"; second pass exit {second['rc']} (log {second['log']}; a pass with --only and without the "
                    "frozen check ends PARTIAL, exit 1)" if second else "")})
    return rows


# ---------------------------------------------------------------------------------------------------------------
# Stage numbers
# ---------------------------------------------------------------------------------------------------------------
def git(work: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=work, capture_output=True, text=True, check=True).stdout


def json_keys_differ(a, b, path="", out=None, limit=8):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k} ({'new' if k not in a else 'gone'})")
            elif a[k] != b[k]:
                json_keys_differ(a[k], b[k], f"{path}/{k}", out, limit)
            if len(out) >= limit:
                break
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                json_keys_differ(x, y, f"{path}[{i}]", out, limit)
    else:
        out.append(path or "/")
    return out


def why_differs(name: str, committed: bytes, rebuilt: bytes) -> str:
    if name.endswith(".json"):
        try:
            return "keys " + ", ".join(json_keys_differ(json.loads(committed), json.loads(rebuilt)))
        except ValueError:
            pass
    if name.endswith((".md", ".csv", ".txt", ".jsonl", ".tsv")):
        try:
            a, b = committed.decode().splitlines(), rebuilt.decode().splitlines()
            n = [i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y]
            return f"lines {n[:6]}" + (f"; {len(a)} lines committed, {len(b)} rebuilt" if len(a) != len(b) else "")
        except UnicodeDecodeError:
            pass
    return f"{len(committed):,} bytes committed, {len(rebuilt):,} rebuilt"


def content_equal(name: str, a: bytes, b: bytes) -> bool:
    """Fidelity rule 3 (S602 only): a PDF equal but for its trailer /ID; a .docx whose zip members are equal, name for
    name and byte for byte (the zip's own dates aside)."""
    if name.endswith(".pdf"):
        pat = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]")
        return pat.sub(b"/ID[]", a) == pat.sub(b"/ID[]", b)
    if name.endswith((".docx", ".xlsx")):
        import zipfile
        try:
            za, zb = zipfile.ZipFile(io.BytesIO(a)), zipfile.ZipFile(io.BytesIO(b))
            return za.namelist() == zb.namelist() and all(za.read(n) == zb.read(n) for n in za.namelist())
        except zipfile.BadZipFile:
            return False
    return False


FROZEN_REF = re.compile(r"\{frozen:([A-Za-z0-9][A-Za-z0-9._-]*):([^}]*)\}")


def resolve_env(work: Path, spec: dict, env: dict) -> dict:
    """A producer's own environment variables ("env"). "{frozen:SET:REL}" is the path fig_repro.frozen(SET, REL) gives in
    the work copy: the frozen tar SET extracted (sha256 checked, members checked against the committed list) into the
    work copy's git-ignored findings/recompute/frozen_inputs/extracted/, which the read audit allows. Run before the
    producer, outside its audit."""
    out = {}
    for k, v in spec.get("env", {}).items():
        m = FROZEN_REF.fullmatch(v)
        if m:
            code = ("import sys; sys.path.insert(0, 'scripts'); import fig_repro; "
                    "print(fig_repro.frozen(sys.argv[1], sys.argv[2]))")
            r = subprocess.run([*UV, "-c", code, m.group(1), m.group(2)], cwd=work, env=env, capture_output=True,
                               text=True)
            if r.returncode or not r.stdout.strip():
                raise RuntimeError(f"{k}: fig_repro.frozen({m.group(1)!r}, {m.group(2)!r}) failed: "
                                   + (r.stderr.strip().splitlines() or ["no output"])[-1][:300])
            v = r.stdout.strip().splitlines()[-1]
        out[k] = v
    return out


def run_producer(work: Path, spec: dict, logs: Path, tars: Path | None) -> dict:
    """Run one producer (one command, or a chain of "cmds" under one audit) in the work copy under the read audit;
    compare; reset the work copy to HEAD."""
    sys.path.insert(0, str(work / "scripts"))
    import fig_read_audit as fa                     # the work copy's own audit module
    name = spec["name"].replace(" ", "_").replace("+", "_")
    adir = logs / "audit" / name
    adir.mkdir(parents=True, exist_ok=True)
    outdir = logs / "out" / name if spec.get("committed") else None
    cmds = [[*UV, *[str(outdir) if x == "{out}" else x for x in c]] for c in (spec.get("cmds") or [spec["cmd"]])]
    cmd = cmds[0]
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    if tars is not None:
        env["FROZEN_TARS"] = str(tars.resolve())
    head = set(git(work, "ls-tree", "-r", "--name-only", "-z", "HEAD").split("\0")) - {""}
    t0 = time.time()
    rc, env_note = 0, None
    scratch = [os.path.realpath(str(work / d)) for d in spec.get("scratch", [])]
    env_file_notes = []
    for k, rel_ in spec.get("env_from_file", {}).items():   # D315: before the scratch folders are emptied
        f = work / rel_
        if f.is_file():
            env[k] = f.read_text(encoding="ascii").strip()
            env_file_notes.append(f"{k}={env[k]} (from {rel_})")
        else:
            env.pop(k, None)
            env_file_notes.append(f"{k} not set: {rel_} is not in the work copy (a ratings.tar without it); S530 "
                                  "stamps the current time, so its results.json and the two plates' provenance files "
                                  "that record its sha256 differ")
    for d in scratch:                       # empty before the run: whatever is read in them, the chain wrote
        shutil.rmtree(d, ignore_errors=True)
    try:
        env.update(resolve_env(work, spec, env))
    except RuntimeError as e:
        rc, env_note = 98, str(e)
    with open(logs / f"{name}.log", "w") as fh:
        if env_note:
            fh.write(env_note + "\n")
        for n in env_file_notes:
            fh.write(n + "\n")
        for k in spec.get("env", {}):
            if k in env:
                fh.write(f"{k}={env[k]}\n")
        for cmd in cmds if not rc else []:
            fh.write("$ " + " ".join(cmd) + "\n")
            fh.flush()
            rc = subprocess.run(cmd, cwd=work, stdout=fh, stderr=subprocess.STDOUT,
                                env=fa.env_for(env, adir)).returncode
            if rc:
                break
    secs = time.time() - t0
    ev = fa.read_logs(adir)
    allowed = [work / p for p in spec.get("allowed", [])]    # RATED: ratings.tar's git-ignored files, by exact path
    ctx = fa.Context(work, tars if tars is not None else work, head, set(), extra_allowed=[logs, *allowed], uv_dirs=[],
                     write_run=True, changed=set())
    j = fa.judge(ev, ctx)
    wrote = {os.path.realpath(p) for p in ev["write"] | ev["update"]}
    viol, notes = [], [n for n in env_file_notes if " not set: " in n]   # D315: shown in the row, never failed alone
    for p, why_ in j["violations"]:
        if p.startswith("[") or "child process" in why_:
            notes.append(f"audit note: {p[:120]}: {why_[:120]}")     # a read-only git child, listed, not failed
        elif os.path.realpath(os.path.join(str(work), p)) in wrote or p == "<unknown>":
            continue                                          # a file the producer itself wrote and read back
        elif any(os.path.realpath(os.path.join(str(work), p)).startswith(d + "/") for d in scratch):
            continue                                          # in a scratch folder emptied before the run (RATED)
        else:
            viol.append(f"{p}: {why_}")
    differ, equal, new, missing, same_content = [], [], [], [], []
    if spec.get("compare"):
        # each folder the chain wrote inside the work copy (git-ignored there) against its committed folder, file by
        # file; then any tracked file changed or untracked file left (git status) differs or is new, as below
        for made_rel, committed_rel in spec["compare"]:
            made_dir = work / made_rel
            committed = [p for p in head if p.startswith(committed_rel + "/")]
            made = ({f.relative_to(made_dir).as_posix() for f in made_dir.rglob("*") if f.is_file()}
                    if made_dir.is_dir() else set())
            for p in sorted(committed):
                rel_ = p[len(committed_rel) + 1:]
                if rel_ not in made:
                    missing.append(p)
                    continue
                want = subprocess.run(["git", "show", f"HEAD:{p}"], cwd=work, capture_output=True, check=True).stdout
                got = (made_dir / rel_).read_bytes()
                (equal if got == want else differ).append(p)
                if got != want:
                    notes.append(f"{p}: {why_differs(p, want, got)}")
            new += [f"{committed_rel}/{x}" for x in sorted(made - {p[len(committed_rel) + 1:] for p in committed})]
        for s in git(work, "status", "--porcelain", "-z", "-uall").split("\0"):
            if s and s[:2].strip() == "??":
                new.append(s[3:])
            elif s:
                differ.append(s[3:])
                notes.append(f"{s[3:]}: a released file the chain changed in place")
        for d in spec.get("scratch", []):
            shutil.rmtree(work / d, ignore_errors=True)
        subprocess.run(["git", "checkout", "--", "."], cwd=work, check=True)
        subprocess.run(["git", "clean", "-fdq"], cwd=work, check=True)
    elif outdir is not None:
        committed = [p for p in head if p.startswith(spec["committed"] + "/")]
        made = {f.relative_to(outdir).as_posix() for f in outdir.rglob("*") if f.is_file()} if outdir.is_dir() else set()
        for p in sorted(committed):
            rel = p[len(spec["committed"]) + 1:]
            if rel not in made:
                missing.append(p)
                continue
            want = subprocess.run(["git", "show", f"HEAD:{p}"], cwd=work, capture_output=True, check=True).stdout
            got = (outdir / rel).read_bytes()
            (equal if got == want else differ).append(p)
            if got != want:
                notes.append(f"{p}: {why_differs(p, want, got)}")
        new = [f"{spec['committed']}/{x}" for x in sorted(made - {p[len(spec['committed']) + 1:] for p in committed})]
    else:
        status = git(work, "status", "--porcelain", "-z", "-uall").split("\0")
        for s in status:
            if not s:
                continue
            code, p = s[:2], s[3:]
            if code.strip() == "??":
                new.append(p)
                continue
            want = subprocess.run(["git", "show", f"HEAD:{p}"], cwd=work, capture_output=True).stdout
            got = (work / p).read_bytes() if (work / p).is_file() else b""
            if spec.get("content_equal") and content_equal(p, want, got):
                same_content.append(p)
                notes.append(f"{p}: content-equal (fidelity rule 3), bytes differ")
            else:
                differ.append(p)
                notes.append(f"{p}: {why_differs(p, want, got)}")
        written = sorted({os.path.relpath(p, os.path.realpath(work)) for p in wrote
                          if p.startswith(os.path.realpath(work) + "/") and "__pycache__" not in p
                          and "/frozen_inputs/extracted/" not in p})
        equal = [p for p in written if p in head and p not in differ and p not in same_content]
        subprocess.run(["git", "checkout", "--", "."], cwd=work, check=True)
        subprocess.run(["git", "clean", "-fdq"], cwd=work, check=True)
    compared = len(equal) + len(same_content) + len(differ) + len(missing)
    held_d = [d for d in differ if d in {h["path"] for h in ACTIVE_HELD}]        # D316: shown, not failed
    for d in held_d:
        notes.append(f"{d}: held (D316), computed from a replaced field, checked by sha256 in stage held")
    ok = rc == 0 and not viol and not (set(differ) - set(held_d)) and not new and not missing and compared > 0
    if not compared:
        notes.append("compared no file: a producer must rebuild at least one released file to pass (S612)")
    if env_note:
        notes.append(env_note)
    if rc:
        tail = [x for x in (logs / f"{name}.log").read_text(errors="replace").splitlines() if x.strip()][-3:]
        notes.append(f"exit {rc}: " + " | ".join(tail)[:400])
    return {"stage": "numbers", "item": f"{spec['label']} ({spec['name']})",
            "files": str(compared), "ok": ok,
            "note": ("compared no file, " if not compared else "") + (f"{len(equal)} byte-equal" + (f", {len(same_content)} content-equal" if same_content else "")
                     + (f", {len(differ)} differ" if differ else "")
                     + (f" ({len(held_d)} held, D316)" if held_d else "")
                     + (f", {len(missing)} not rebuilt" if missing else "") + (f", {len(new)} new" if new else "")
                     + (f", {len(viol)} audit violations" if viol else "") + f", {secs:.0f} s"),
            "details": viol + notes + [f"new: {x}" for x in new] + [f"not rebuilt: {x}" for x in missing],
            "reads": sorted(j["repo_reads"]), "writes": equal + same_content + differ}


def stage_numbers(work: Path, data: Path | None, only: list[str] | None = None,
                  skip: list[str] | None = None, rated: list[str] | None = None) -> list[dict]:
    """NUMBERS, then RATED when the work copy holds ratings.tar's files (rated: the paths make_work unpacked)."""
    logs = work.parent / (work.name + "_numbers_logs")
    logs.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in NUMBERS + ([{**x, "allowed": rated} for x in RATED] if rated is not None else []):
        if only and spec["name"] not in only:
            continue
        if skip and spec["name"] in skip:
            rows.append({"stage": "numbers", "item": f"{spec['label']} ({spec['name']})", "files": "", "ok": False,
                         "note": "not run (--skip-producer): not reproduced", "details": [], "reads": [], "writes": []})
            print(f"-- {spec['label']} ({spec['name']}): not run (--skip-producer)", flush=True)
            continue
        print(f"-- {spec['label']} ({spec['name']})", flush=True)
        r = run_producer(work, spec, logs, (data / "frozen") if data is not None else None)
        print(f"   {'ok' if r['ok'] else 'NOT EQUAL'}: {r['note']}", flush=True)
        for d in r["details"][:12]:
            print(f"     {d}", flush=True)
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------------------------------------------
# Stage held
# ---------------------------------------------------------------------------------------------------------------
def expected_manifest() -> dict[str, str]:
    rows = {}
    for line in EXPECTED.read_text(encoding="utf-8").splitlines():
        if line.strip():
            sha, rel = line.split("  ", 1)
            rows[rel] = sha
    return rows


def stage_held(work: Path, rated: bool = False, strip: bool = False) -> list[dict]:
    """HELD by sha256; with rated, RATED_HELD's entries are left to RATED (rebuilt in the numbers stage); with strip
    (a stripped data root, D316), STRIPPED_HELD's outputs too."""
    exp = expected_manifest()
    rows = []
    for h in ACTIVE_HELD if strip else []:
        k = h["path"]
        good = k in exp and (work / k).is_file() and sha256_file(work / k) == exp[k]
        rows.append({"stage": "held", "item": f"{h['label']}: {k}", "files": "1", "ok": good,
                     "note": ("sha256 equal" if good else "not in expected/MANIFEST.sha256 or sha256 differs")
                     + f"; not rebuilt (D316): written by {h['by']}, which reads {h['field']}; {h['reason']}"})
    for label, path, reason in HELD:
        if rated and path in RATED_HELD:
            continue
        keys = [k for k in exp if k == path or k.startswith(path + "/")]
        bad = [k for k in keys if not (work / k).is_file() or sha256_file(work / k) != exp[k]]
        rows.append({"stage": "held", "item": f"{label}: {path}", "files": str(len(keys)), "ok": bool(keys) and not bad,
                     "note": (f"{len(keys) - len(bad)} of {len(keys)} sha256 equal" if keys else
                              "not in expected/MANIFEST.sha256") + f"; not rebuilt: {reason}"})
    return rows


# ---------------------------------------------------------------------------------------------------------------
def platform_lines() -> tuple[list[str], bool]:
    font = Path(PLATE_FONT)
    got = sha256_file(font) if font.is_file() else None
    font_ok = got == PLATE_FONT_SHA256
    return ([f"python {platform.python_version()} on {platform.system()} {platform.release()} {platform.machine()}",
             f"plate font {PLATE_FONT}: " + ("absent" if got is None else f"sha256 {got[:12]}")
             + (" (the plates' font: plates are held byte for byte)" if font_ok else
                f" (the plates were drawn with sha256 {PLATE_FONT_SHA256[:12]}: plate differences are reported as "
                "'font differs', fidelity rule 2)")], font_ok)


def table(rows: list[dict]) -> str:
    w = max(len(r["item"]) for r in rows) if rows else 10
    w = min(w, 70)
    out = [f"{'stage':<8}  {'item':<{w}}  {'files':>5}  {'verdict':<8}  note", "-" * (8 + w + 30)]
    for r in rows:
        out.append(f"{r['stage']:<8}  {r['item'][:w]:<{w}}  {r['files']:>5}  {'pass' if r['ok'] else 'FAIL':<8}  "
                   f"{r['note']}")
    return "\n".join(out)


def selftest() -> int:
    """D316 pieces on made-up data, nothing run: the mapping read from stripped_records.tsv, the hash module in a
    Python child, and the held judgement of S494 rows."""
    import tempfile
    fails = []

    def check(name, cond):
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    global DATA_FILES
    h = lambda b: hashlib.sha256(b).hexdigest()
    orig_m, strip_m, orig_t, strip_t = h(b"original member"), h(b"stripped member"), h(b"orig tar"), h(b"strip tar")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tsv = ("tar\tmember\toriginal_sha256\tstripped_sha256\tfields_stripped\n"
               f"a.tar\t\t{orig_t}\t{strip_t}\t\n"
               f"a.tar\tr/calls.jsonl\t{orig_m}\t{strip_m}\tcalls.jsonl:.prompt_sent=1\n"
               f"a.tar\tr/notes.txt\t{h(b'n')}\t{h(b'n')}\t\n")
        (td / STRIPPED_TSV).write_text(tsv)
        keep = DATA_FILES
        try:
            DATA_FILES = td / "DATA_FILES.tsv"
            DATA_FILES.write_text("name\tbytes\tsha256\tfolder\tdescription\n"
                                  f"a.tar\t1\t{strip_t}\tfrozen\tx\n{STRIPPED_TSV}\t1\t{h(tsv.encode())}\t.\tx\n")
            m = strip_map(td)
            check("mapping: the stripped member and tar stand for their originals, an unchanged member is not listed",
                  m == {strip_m: orig_m, strip_t: orig_t})
            DATA_FILES.write_text("name\tbytes\tsha256\tfolder\tdescription\n"
                                  f"a.tar\t1\t{h(b'other')}\tfrozen\tx\n{STRIPPED_TSV}\t1\tx\t.\tx\n")
            try:
                strip_map(td)
                check("mapping: a tar row whose stripped sha256 is not DATA_FILES.tsv's pin is refused", False)
            except SystemExit:
                check("mapping: a tar row whose stripped sha256 is not DATA_FILES.tsv's pin is refused", True)
            DATA_FILES.write_text("name\tbytes\tsha256\tfolder\tdescription\na.tar\t1\tx\tfrozen\tx\n")
            check("mapping: a data root of originals (no stripped_records.tsv row) maps nothing", strip_map(td) == {})
        finally:
            DATA_FILES = keep
        (td / "shim.py").write_text(STRIP_SHIM % json.dumps({strip_m: orig_m}))
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import shim, hashlib, io; "
                "print(hashlib.sha256(b'stripped member').hexdigest(), hashlib.new('sha256', b'stripped member').hexdigest(),"
                " hashlib.file_digest(io.BytesIO(b'stripped member'), 'sha256').hexdigest(),"
                " hashlib.sha256(b'other').hexdigest())")
        out = subprocess.run([sys.executable, "-c", code, str(td)], capture_output=True, text=True).stdout.split()
        check("hash module: sha256, new('sha256') and file_digest report the original for a stripped member",
              out[:3] == [orig_m] * 3)
        check("hash module: any other input hashes as it is", out[3:] == [h(b"other")])
    held = [{"path": "findings/recompute/x_steps.json", "stage": "s494", "step": "figX"},
            {"path": "findings/figures_provisional/figX/figure9_provenance.json", "stage": "s494", "step": "figX"}]
    dash = "-" * 40 + "  -----  ---------------  -------  -----  -------"
    text = "\n".join([
        "figure                                    files  byte-equal       S448     audit  seconds", dash,
        "  x_steps.json                                1  0 of 1                    0            9",
        "Figure 9                                      9  8 of 9           12 PASS  0      (above)",
        "Figure 8                                      8  7 of 8           12 PASS  0            2",
        "Figure 1                                      8  blocked by figX  12 PASS  0            2", "",
        "DIFFERENCES AND FAILURES",
        "* Figure 9 (folder figX)",
        "    x_steps.json: differs: x_steps.json",
        "    x_steps.json:     keys /rows[0][5]",
        "    Figure 9: differs: figure9_provenance.json",
        "* Figure 8",
        "    differs: figure8_numbers.json",
        "* Figure 1",
        "    blocked by figX: reads findings/figures_provisional/figX/legend_draft.md, an output of a step that failed",
        ""])
    rows, hmap = judge_s494(text, held)
    ok = {r["figure"]: r["ok"] for r in rows}
    check("S494: rows whose only differences are held files pass, noted held",
          ok["x_steps.json"] and ok["Figure 9"] and "held (D316)" in rows[1]["note"])
    check("S494: a difference in a file not held fails", not ok["Figure 8"])
    check("S494: a blocked row is not passed by the first pass", not ok["Figure 1"])
    check("S494: nothing held without a held list", not any(r["ok"] for r in judge_s494(text, [])[0]))
    print(f"selftest: {'PASS' if not fails else 'FAIL'} ({len(fails)} failed)")
    return 1 if fails else 0


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=os.environ.get("MENTORI_DATA"))
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--zenodo-url", default=ZENODO_URL)
    ap.add_argument("--work")
    ap.add_argument("--only", action="append", choices=["s494", "numbers", "held"])
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--skip-producer", action="append", default=[], metavar="NAME")
    a = ap.parse_args(argv)
    if not a.data:
        ap.error("give --data DIR (or set MENTORI_DATA)")
    data = Path(a.data).expanduser().resolve()
    data.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"reproduce.py: data root {data}", flush=True)
    lines, optional = check_data(data, a.download, a.zenodo_url)
    for x in lines:
        print("  " + x, flush=True)
    rated = RATINGS_TAR in optional
    work = Path(a.work).expanduser().resolve() if a.work else data / "work"
    if work.exists() and any(work.iterdir()):
        print(f"REFUSED: the work folder {work} is not empty: give a new or empty --work")
        return 2
    print(f"making the work copy {work}", flush=True)
    mapping = strip_map(data)
    unpacked = make_work(work, data, (data / RATINGS_TAR) if rated else None)
    if mapping:
        ACTIVE_HELD[:] = STRIPPED_HELD
        print("  " + install_strip_map(work, mapping, work.parent / (work.name + "_uv_sync.log")), flush=True)
    plat, font_ok = platform_lines()
    for x in plat:
        print("  " + x, flush=True)
    stages = a.only or ["s494", "numbers", "held"]
    rows: list[dict] = []
    if "s494" in stages:
        rows += stage_s494(work, data, font_ok)
    if "numbers" in stages:
        rows += stage_numbers(work, data, skip=a.skip_producer, rated=unpacked if rated else None)
    if "held" in stages:
        rows += stage_held(work, rated=rated and "numbers" in stages, strip=bool(mapping))
    print("\nPASS TABLE")
    print(table(rows))
    for x in plat:
        print(x)
    ok = all(r["ok"] for r in rows) and set(stages) == {"s494", "numbers", "held"}
    n_bad = sum(not r["ok"] for r in rows)
    print(f"\n{len(rows)} rows, {n_bad} not passing; {time.time() - t0:.0f} s; "
          + ("REPRODUCED" if ok else "NOT REPRODUCED" if n_bad else "PARTIAL (--only)"))
    (work.parent / (work.name + "_pass_table.json")).write_text(json.dumps(
        [{k: v for k, v in r.items() if k not in ("reads", "writes")} for r in rows], indent=1))
    if ok and not a.keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"work copy kept: {work}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
