#!/usr/bin/env python3
"""reproduce.py (source: Mentori-reanalysis scripts/S608_reproduce.py, copied unchanged by S608_release_analysis.py into
Mentori-paper analysis/reproduce.py) - the one command that rebuilds the paper's figures, tables and numbers from the
released data and holds every output to the released copy.

    uv run --frozen python reproduce.py --data DIR [--work DIR] [--only STAGE ...] [--keep]
    uv run --frozen python reproduce.py --data DIR --download [--zenodo-url URL]

  --data DIR        the data root (env MENTORI_DATA): DIR/frozen/<the 14 frozen tars> and DIR/analysis_inputs.tar, the
                    names, sizes and sha256 DATA_FILES.tsv lists. Every file is checked against DATA_FILES.tsv first;
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
PLATE_FONT_SHA256 = "@PLATE_FONT_SHA256@"
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
    rows = []
    for r in parse_s494_table(text):
        ok = row_ok(r)
        note = r["equal"] + (f"; S448 {r['s448']}" if r["s448"] else "")
        if not ok and not font_ok and r["figure"].startswith(("Figure", "Supplementary Figure")):
            note += "; font differs from the plates' font (fidelity rule 2): not reproduced, check visually"
        rows.append({"stage": "s494", "item": r["figure"], "files": r["files"], "ok": ok, "note": note})
    if not rows:
        rows.append({"stage": "s494", "item": "S494", "files": "", "ok": False, "note": f"no table; exit {rc}"})
    rows.append({"stage": "s494", "item": "S494 exit code", "files": "", "ok": rc == 0,
                 "note": f"exit {rc} (log {log})"})
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
    ok = rc == 0 and not viol and not differ and not new and not missing and compared > 0
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


def stage_held(work: Path, rated: bool = False) -> list[dict]:
    """HELD by sha256; with rated, RATED_HELD's entries are left to RATED (rebuilt in the numbers stage)."""
    exp = expected_manifest()
    rows = []
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


def main(argv=None) -> int:
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
    unpacked = make_work(work, data, (data / RATINGS_TAR) if rated else None)
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
        rows += stage_held(work, rated=rated and "numbers" in stages)
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
