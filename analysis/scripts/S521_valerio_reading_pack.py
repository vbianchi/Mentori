#!/usr/bin/env python3
"""S521: one reading pack for Valerio (D200: "you have to point me to all of these things I have to rate").

WHAT IT WRITES. Into --out (default ~/Mentori_scratch_keep/valerio_reading_pack_2026-11), nothing in the repository:
  valerio_reading_pack.xlsx                the workbook, sheets A False premise, B Examples, C Claims
  README.md                                one page, written so he can start cold
  valerio_reading_pack_KEY.csv             row id -> answer, strategy, score, kept apart so sheets A and C stay blind
  valerio_reading_pack_meta.json           inputs with sha256, rules, counts, the options for sheet C

WHAT EACH SHEET HOLDS.
  A  The draw-level answers of the six strategies to the 10 false-premise questions (6 x 10 x 3 = 180) whose judge
     correctness (call (a), read through scripts/judge_rows_v25.py, so the key v2.5 row where one exists) is below 4.
     No score and no strategy on the sheet; rows in the order of sha256(salt | answer key).
  B  The three answers of D200 (S.2 a): question, answer, the retrieved passages whole, the source papers whole, the
     nine scores of facts_behind_notes.txt:445.
  C  The S08 rule (scripts/S08_make_adjudication_sheet.py:66-67) redone on the re-run: among draw-1 answers of answerable
     questions with a MiniCheck value against the papers (findings/recompute/fig5_1028_inputs/l1, S470's papers stage,
     draw 1 only), judge faithfulness with passages (call (b)) equal to 5 and precision at or below the 33.33rd
     percentile of that population (pandas quantile, linear, as S08). Every claim of a picked answer is a row, with the
     passages its generator saw (experiments/scorers/records.py read_run, resolved through ~/k1_inputs/store).
  --selection d172 applies D172 A5-Q1 and FF20 (a) to the stored labels first: a claim marks.py calls a source-list line
  or a heading leaves the answer, precision is recomputed from the stored labels (no model call), the same rule runs on
  those values, and sheet C lists only the claims left. The default, "stored", uses the precision L1 stored, and column
  D of sheet C names such lines so nothing is removed.

WHAT IT REFUSES. Every file opened in the process passes sys.addaudithook's guard (FORBIDDEN): the rater folders, S354,
early-look outputs, T2's and the second judge's folders. A row of any run but G1's six is refused (RUN_IDS). judge rows
go through judge_rows_v25's check_v24 and check_v25, which refuse a row with a "judge" field (a second judge). No rating
is read. No model, no Ollama port, no ssh.

REPRODUCE BEFORE WRITING (README.md:75-79). Before the workbook is written the run must give: S08's 116 answers and its
cut from findings/recompute/master_join.csv; the 180 false-premise answers split 148, 15, 14, 3 and the strategy passes
of facts_behind_notes.txt:485,489; the nine scores of facts_behind_notes.txt:447,448,450; every stored L1 precision equal
to supported over claims, and every stored claim equal to the first 300 characters of the deposited decomposer's claim.

S6G1's rows are the frozen set findings/recompute/fig3_s6_inputs/ (scripts/S528_freeze_fig3_s6.py, after phase 3 ended on
1 November), each file held to that set's SHA256SUMS through fig_repro.frozen(); s3_guard collect runs on a copy of its
files, and the row counts per status go into the meta file. --s6-root reads another folder of that shape instead.

    uv run --frozen python scripts/S521_valerio_reading_pack.py [--out DIR] [--selection stored|d172]
    uv run --frozen python scripts/S521_valerio_reading_pack_test.py [--pack DIR]
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
DEFAULT_OUT = HOME / "Mentori_scratch_keep/valerio_reading_pack_2026-11"
XLSX, README, KEYFILE, METAFILE = ("valerio_reading_pack.xlsx", "README.md", "valerio_reading_pack_KEY.csv",
                                   "valerio_reading_pack_meta.json")

FIG2 = ROOT / "findings/recompute/fig2_inputs"                 # G1's key v2.4 outs and collect (committed)
S6_SET = "fig3_s6"                                             # S6G1's judge rows, frozen and committed (S528)
K1_INPUTS = HOME / "k1_inputs"                                 # G1's answers and the index they read
G1R15_INPUTS = HOME / "s3_inputs/g1r15"                        # the 15 reruns of 18 October
L1 = ROOT / "findings/recompute/fig5_1028_inputs/l1"           # MiniCheck rows, committed
L3 = ROOT / "findings/recompute/L3_d181/concept_recall.jsonl"  # concept recall, final key, committed
KEY25 = ROOT / "data/ground_truth_v2/ground_truth_v2_5_as_v1.json"
KEY24_SOURCE = ROOT / "data/ground_truth_v2/all_v2_4.json"     # question_issues, the key's own words on each false premise
PAPERS = ROOT / "findings/recompute/S18_evidence_docs.jsonl"
K1_ARCHIVE = HOME / "mentori_archive/scratch_2026-10-30.tar.gz"   # the 28 Oct pull, facts_behind_notes.txt:460
NOT_FROZEN = ROOT / "findings/recompute/fig5_1028_inputs/NOT_FROZEN.tsv"
MASTER_JOIN = ROOT / "findings/recompute/master_join.csv"
S08_META = ROOT / "findings/recompute/S08_adjudication_meta.json"
MARKS = ROOT / "scripts/minicheck_marks.py"                    # the measured rules, kept byte for byte in a tracked script

CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
RUN_IDS = {f"exp_01__{c}__exp_v4_s20_n0": c for c in CONFIGS}
NAMES = {"single_pass": "Single pass", "multi_hop": "Multi-hop", "verified_pass": "Verified pass", "rlm_5": "RLM-5",
         "rlm_10": "RLM-10", "rlm_20": "RLM-20"}
INDEX = "exp_v4_s20_n0"
SALT = "S521|2026-11-01"
TERCILE_Q = 1.0 / 3.0                                          # S08_make_adjudication_sheet.py:59
PASS_AT = 4                                                    # facts_behind_notes.txt:485
PART_LINES, PART_WIDTH = 30, 120                               # what one cell shows at the row height and width used
CELL_MAX = 32000                                               # Excel holds 32,767 characters in a cell
WPM = 240                                                      # facts_behind_notes.txt:500
CALLS_C = ("supported", "partly", "not")
CALLS_A = ("refutes", "hedges", "accepts")

EXAMPLES = (  # facts_behind_notes.txt:447,448,450, D200: 1, 2 and 4
    {"n": 1, "config": "multi_hop", "q": "11_asf_burkina_faso_FR1", "why": "Concepts and MiniCheck against the key are low, every other score is high.",
     "want": {"jc": 5, "jf": 5, "mc": 1.0, "mc_n": (1, 1), "f1": 0.0, "cc": (0, 2), "rf": 1.0, "rc": 1.0, "cf": 1.0, "c1": 1.0}},
    {"n": 2, "config": "multi_hop", "q": "04_fastp_FR1", "why": "MiniCheck against the papers and against the key are low, the judge and concepts are high.",
     "want": {"jc": 5, "jf": 5, "mc": 0.0, "mc_n": (0, 1), "f1": 0.0, "cc": (2, 2), "rf": 1.0, "rc": 0.57, "cf": 1.0, "c1": 0.33}},
    {"n": 4, "config": "verified_pass", "q": "CD_018", "why": "The judge's correctness is 0, passage-only scores are high, key-based scores are low.",
     "want": {"jc": 0, "jf": 5, "mc": 0.86, "mc_n": (6, 7), "f1": 0.2, "cc": (1, 7), "rf": 0.75, "rc": 0.07, "cf": 0.95, "c1": 0.10}},
)
FP_STATES = {5: 148, 4: 15, 3: 14, 0: 3}                       # facts_behind_notes.txt:485
FP_PASS = {"single_pass": 30, "multi_hop": 28, "verified_pass": 28, "rlm_5": 26, "rlm_10": 25, "rlm_20": 26}   # :489

FORBIDDEN = (r"response/human_eval_v22", r"response/rater_packets", r"response/internal_review",
             r"response/human_eval_sheet_full_answers", r"S354", r"response/ground_truth_v2/all_v2_1_signoff\.xlsx",
             r"resubmission/11_internal_review", r"response/concept_match_labels", r"findings/recompute/S50[01]",
             r"findings/recompute/S51[07]", r"\.config/mentori-runs", r"(^|/)out(_s6)?_t2", r"/s3_inputs/t2",
             r"second_judge", r"out_second", r"s6-second")
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN))


class Refused(Exception):
    pass


def is_forbidden(path) -> bool:
    return bool(FORBIDDEN_RE.search(os.fsdecode(path) if isinstance(path, (bytes, os.PathLike)) else str(path)))


_guard_on = False


def install_guard() -> None:
    """From here on, opening a FORBIDDEN path or starting a process that names one raises in this process."""
    global _guard_on
    if _guard_on:
        return

    def hook(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)) and is_forbidden(args[0]):
            raise Refused(f"guard: {os.fsdecode(args[0])} is closed to this script")
        if event == "subprocess.Popen" and any(is_forbidden(a) for a in (args[1] or []) if isinstance(a, (str, bytes))):
            raise Refused(f"guard: a process naming a closed path: {args[1]}")

    sys.addaudithook(hook)
    _guard_on = True


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "surrogatepass")).hexdigest()


def read_jsonl(p: Path) -> list[dict]:
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


# ---------------------------------------------------------------- pure rules (scripts/S521_..._test.py)

def discordant(rows: list[dict]) -> tuple[float, list[dict]]:
    """S08's rule, S08_make_adjudication_sheet.py:66-67: the cut is the 33.33rd percentile of precision over every row
    that has one (pandas quantile, linear); a row is picked when its faithfulness is 5 and its precision is at or
    below the cut. rows: {"precision", "faith"}; a row with no precision is outside the cut and never picked."""
    import pandas as pd
    v = pd.Series([r["precision"] for r in rows], dtype=float)
    cut = float(v.quantile(TERCILE_Q))
    return cut, [r for r in rows if r["precision"] is not None and r["faith"] == 5 and r["precision"] <= cut]


def parts(text: str, limit: int) -> list[str]:
    """text in pieces of at most limit characters, broken after white space where one is in reach; "".join gives text
    back exactly, so nothing is cut."""
    if limit < 2:
        raise ValueError("limit")
    out, i = [], 0
    while i < len(text):
        j = min(i + limit, len(text))
        if j < len(text):
            k = max(text.rfind(c, i + limit // 2, j) for c in " \n\t")
            if k > i:
                j = k + 1
        out.append(text[i:j])
        i = j
    return out or [""]


def read_parts(text: str, width: int = PART_WIDTH, max_lines: int = PART_LINES) -> list[str]:
    """text in pieces that each fit a row 400 points high: at most max_lines lines at width characters, counting a long
    line as the lines it wraps to. Line breaks stay (a paper's tables need them); "".join gives text back exactly."""
    out, cur, n = [], "", 0
    for ln in text.splitlines(keepends=True):
        for piece in parts(ln, width * max_lines):
            m = max(1, math.ceil(len(piece) / width))
            if cur and n + m > max_lines:
                out.append(cur)
                cur, n = "", 0
            cur, n = cur + piece, n + m
    return out + [cur] if cur or not out else out


def flow(text: str) -> str:
    """A passage with its line breaks turned into spaces, so one passage fits one cell. PDF text breaks every 80
    characters or so; no word changes (the test holds it equal to text under whitespace collapse)."""
    return re.sub(r"[ \t]*\n[ \t\n]*", " ", text).strip()


def ranks(keys: list) -> dict:
    """Each key's place, from 1, in the order of sha256(SALT | key): a fixed order nobody chose by looking."""
    return {k: i for i, k in enumerate(sorted(keys, key=lambda k: sha(f"{SALT}|{k}")), 1)}


def line_kind(claim: str, md_heads: set, m) -> str:
    """marks.py's two rules (the only ones measured; findings/scratch_archive/2026-10-30/reports/minicheck_marks):
    'source-list line' by source_kind, 'heading' by heading_kind, '' otherwise."""
    if m.source_kind(claim):
        return "source-list line"
    if m.heading_kind(claim, md_heads):
        return "heading"
    return ""


def md_headings(answer: str, decompose) -> set:
    """The claims the decomposer makes of the answer's '#' lines (minicheck_marks/prep.py:92-95)."""
    out = set()
    for ln in answer.splitlines():
        if re.match(r"^\s*#+\s+", ln):
            out.update(decompose(ln.strip()))
    return out


def hours(minutes: float) -> str:
    return f"{minutes / 60:.1f}"


def cell_text(text):
    """A cell's text with the control characters Excel files cannot hold made visible (U+FFFD), nothing removed."""
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    return ILLEGAL_CHARACTERS_RE.sub("�", text) if isinstance(text, str) else text


def put(ws, r: int, c: int, value) -> None:
    """One cell. Text stays text: a string that opens with "=" is not a formula. A string over Excel's limit is refused,
    never cut."""
    value = cell_text(value)
    if isinstance(value, str) and len(value) > 32767:
        raise Refused(f"a cell of {len(value)} characters; use parts()")
    cell = ws.cell(row=r, column=c, value=value)
    if isinstance(value, str):
        cell.data_type = "s"


def table(ws, cols: list[tuple[str, float]], rows: list[list], freeze: str, row_height: float, calls: dict) -> None:
    """A sheet: a header row, one row per entry, wrapped, the left columns frozen so a rating cell stays in view while
    the passages scroll. calls: {column number: allowed values} become drop-down lists."""
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter as L
    from openpyxl.worksheet.datavalidation import DataValidation
    head = Font(name="Arial", size=9, bold=True)
    body = Font(name="Arial", size=9)
    wrap = Alignment(wrap_text=True, vertical="top")
    rate = PatternFill("solid", fgColor="FFF2CC")
    line = Side(style="thin", color="BFBFBF")
    box = Border(left=line, right=line, top=line, bottom=line)
    for j, (h, w) in enumerate(cols, 1):
        put(ws, 1, j, h)
        ws.cell(1, j).font, ws.cell(1, j).alignment = head, wrap
        ws.column_dimensions[L(j)].width = w
    for i, row in enumerate(rows, 2):
        for j, v in enumerate(row, 1):
            if v is None or v == "":
                continue
            put(ws, i, j, v)
            ws.cell(i, j).font, ws.cell(i, j).alignment = body, wrap
        ws.row_dimensions[i].height = row_height
    for j, allowed in calls.items():
        dv = DataValidation(type="list", formula1='"' + ",".join(allowed) + '"', allow_blank=True)
        dv.error, dv.errorTitle = "Pick one from the list", "Your call"
        ws.add_data_validation(dv)
        dv.add(f"{L(j)}2:{L(j)}{len(rows) + 1}")
    for j in blank_columns(cols):
        for i in range(2, len(rows) + 2):
            ws.cell(i, j).fill, ws.cell(i, j).border = rate, box
    ws.freeze_panes = freeze
    ws.auto_filter.ref = f"A1:{L(len(cols))}{len(rows) + 1}"


def share_strings(path: Path) -> dict:
    """openpyxl writes every text cell inline, so the same passage on 80 rows is stored 80 times (64 MB, 185 MB of XML).
    This rewrites the sheets to Excel's ordinary shared-string table: same cells, each distinct text stored once."""
    index, total = {}, 0
    pat = re.compile(r'<c ([^>]*?)t="inlineStr"([^>]*)><is><t(?: xml:space="preserve")?>(.*?)</t></is></c>', re.S)

    def sub(m):
        nonlocal total
        total += 1
        i = index.setdefault(m.group(3), len(index))
        return f'<c {m.group(1)}t="s"{m.group(2)}><v>{i}</v></c>'

    tmp = path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(path) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        names = zi.namelist()
        for n in names:
            if n.startswith("xl/worksheets/sheet"):
                zo.writestr(n, pat.sub(sub, zi.read(n).decode("utf-8")))
        sst = "".join(f'<si><t xml:space="preserve">{t}</t></si>' for t in index)
        zo.writestr("xl/sharedStrings.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<sst xmlns="http://schemas.openxmlformats.org/'
                    f'spreadsheetml/2006/main" count="{total}" uniqueCount="{len(index)}">{sst}</sst>')
        add = {"[Content_Types].xml": ('</Types>', '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.'
                                                   'openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>'),
               "xl/_rels/workbook.xml.rels": ('</Relationships>', '<Relationship Type="http://schemas.openxmlformats.org/office'
                                              'Document/2006/relationships/sharedStrings" Target="sharedStrings.xml" Id="rId99"/>'
                                              '</Relationships>')}
        for n in names:
            if n.startswith("xl/worksheets/sheet") or n == "xl/sharedStrings.xml":
                continue
            b = zi.read(n)
            if n in add:
                b = b.decode("utf-8").replace(*add[n]).encode("utf-8")
            zo.writestr(n, b)
    tmp.replace(path)
    return {"text_cells": total, "distinct_texts": len(index)}


def blank_columns(cols: list[tuple[str, float]]) -> list[int]:
    return [j for j, (h, _) in enumerate(cols, 1) if h.startswith("Your ")]


def check_blank(wb) -> list[str]:
    """Every "Your ..." cell of every sheet is empty; returns the cells that are not."""
    bad = []
    for ws in wb.worksheets:
        head = [c.value for c in ws[1]]
        for j, h in enumerate(head, 1):
            if isinstance(h, str) and h.startswith("Your "):
                bad += [f"{ws.title}!{ws.cell(i, j).coordinate}" for i in range(2, ws.max_row + 1)
                        if ws.cell(i, j).value not in (None, "")]
    return bad


# ---------------------------------------------------------------- inputs

def deps():
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
    import judge_rows_v25 as JR
    from experiments.scorers import records as R
    import S19_minicheck_regrounded as S19
    return JR, R, S19


def marks():
    spec = importlib.util.spec_from_file_location("minicheck_marks", MARKS)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def frozen_s6() -> Path:
    """The frozen S6 set's folder, every file held to its SHA256SUMS."""
    sys.path[:0] = [str(ROOT / "scripts")]
    import fig_repro as FR
    return FR.frozen(S6_SET)


def snapshot_s6(dest: Path, s6_root: Path) -> dict:
    """A copy of S6G1's judge files, whole lines only, so that a --s6-root still being written cannot break the read."""
    copied = {}
    for out in ("out_s6_g1", "out_s6_g1r15"):
        for f in sorted((s6_root / out).glob("judge/*/judge_passages*.jsonl")):
            if f.name not in ("judge_passages.jsonl", "judge_passages_headers.jsonl"):
                continue
            t = dest / out / "judge" / f.parent.name / f.name
            t.parent.mkdir(parents=True, exist_ok=True)
            b = f.read_bytes()
            t.write_bytes(b[:b.rfind(b"\n") + 1])
            copied[f"{out}/judge/{f.parent.name}/{f.name}"] = sha256_file(t)
    return copied


def judge_choice(JR, s6_root: Path, tmp: Path) -> dict:
    """{(run, config, q, draw): row} for G1's 2,430 answers through judge_rows_v25: the key v2.5 row where one exists,
    else key v2.4's, with the reader's checks; and the state of S6G1."""
    snap = tmp / "s6"
    copied = snapshot_s6(snap, s6_root)
    reruns = [x.strip() for x in (G1R15_INPUTS / "keys.txt").read_text().splitlines() if x.strip()]
    src24 = JR.sources(FIG2, "G1")[0]
    L24 = JR.read_source(src24, FIG2 / "g1_collect.jsonl", replace_keys=reruns)
    s6 = JR.sources(snap, "G1")[1]
    if not s6["present"]:
        raise Refused(f"S6G1 folders missing: {s6['missing']}")
    dest = tmp / "s6g1_collect.jsonl"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = JR.guard().collect(s6["outs"], s6["replace"], dest, s6["set"])
    if rc:
        raise Refused(f"s3_guard collect refused S6G1: {buf.getvalue()[-300:]}")
    L25 = JR.read_source(s6, dest, replace_keys=reruns)
    qs = sorted({k[2] for k in L24.rows})
    if len(qs) != 135:
        raise Refused(f"{len(qs)} questions in G1's collect, not 135")
    ans = [{"run_id": r, "config": c, "question_id": q, "draw": d, "answer_key": f"{INDEX}|{c}|{q}|d{d}"}
           for r, c in RUN_IDS.items() for q in qs for d in (1, 2, 3)]
    ch = JR.choose(ans, [L24, L25], all_draws=True)
    rep = JR.report(ch, all_draws=True)
    if rep["awaiting_s6"]["count"] or rep["answers"] != 2430:
        raise Refused(f"reader: {rep['answers']} answers, awaiting S6 {rep['awaiting_s6']['count']}")
    rows = {(r, c, q, d): v for (r, c, q, d), v in ((k, v) for k, v in ch.items() if k != "_sources")}
    for k, v in rows.items():
        if v["row"] is None:
            raise Refused(f"no judge row for {k}")
    state = {"rows_read": len(L25.rows), "call_b_status": dict(Counter(d["b"]["status"] for d in L25.rows.values())),
             "call_b_status_by_draw": {str(dr): dict(Counter(d["b"]["status"] for k, d in L25.rows.items() if k[3] == dr))
                                       for dr in (1, 2, 3)},
             "by_source": rep["by_source"], "snapshot_sha256": copied, "run_sha256": rep["run_sha256"]}
    return {"rows": rows, "state": state, "questions": qs, "reruns": reruns}


def answers_of(R, reruns: list[str]) -> dict:
    """answer key -> the record, G1's frozen copy, the 15 reruns from their own copy; passage ids resolved to text."""
    store = K1_INPUTS / "store"
    out = {}
    for run in RUN_IDS:
        for x in R.read_run(K1_INPUTS / "runs" / run, store=store, immutable=True):
            out[x["answer_key"]] = x
    n = 0
    for run in RUN_IDS:
        p = G1R15_INPUTS / "runs" / run
        if not p.is_dir():
            continue
        for x in R.read_run(p, store=store, immutable=True):
            if x["answer_key"] in reruns:
                out[x["answer_key"]] = x
                n += 1
    if n != len(reruns) or len(out) != 2430:
        raise Refused(f"{n} of {len(reruns)} reruns read, {len(out)} answers")
    return out


def l1_rows(stage: str) -> dict:
    out = {}
    for f in sorted((L1 / stage).glob(f"{stage}.shard*.jsonl")):
        for r in read_jsonl(f):
            if r["run_id"] not in RUN_IDS:
                raise Refused(f"L1 row of another run: {r['run_id']}")
            if r["answer_key"] in out:
                raise Refused(f"L1 {stage}: {r['answer_key']} twice")
            out[r["answer_key"]] = r
    return out


def k1_rows(keys: set) -> dict:
    """The RAGAS and RAGChecker rows of keys from the 28 Oct pull in the archive, each file checked against
    NOT_FROZEN.tsv; only those ten member files are read."""
    want = {}
    for ln in NOT_FROZEN.read_text().splitlines():
        if ln.startswith(("#", "path\t")):
            continue
        p, s = ln.split("\t")[:2]
        if p.endswith(("ragas/ragas.jsonl", "ragchecker/ragchecker.jsonl")):
            want[f"fig5_pull_1028/{p}"] = s
    got, seen = {}, set()
    with tarfile.open(K1_ARCHIVE) as t:
        for m in t:
            if m.name not in want:
                continue
            b = t.extractfile(m).read()
            if hashlib.sha256(b).hexdigest() != want[m.name]:
                raise Refused(f"{m.name}: sha256 differs from NOT_FROZEN.tsv")
            seen.add(m.name)
            kind = "ragas" if m.name.endswith("ragas.jsonl") else "ragchecker"
            for ln in b.decode().splitlines():
                d = json.loads(ln)
                if d.get("answer_key") in keys:
                    if d["run_id"] not in RUN_IDS:
                        raise Refused(f"K1 row of another run: {d['run_id']}")
                    if (d["answer_key"], kind) in got:
                        raise Refused(f"K1: {d['answer_key']} {kind} twice")
                    got[(d["answer_key"], kind)] = d
    if seen != set(want):
        raise Refused(f"K1 files missing from the archive: {sorted(set(want) - seen)}")
    return got


# ---------------------------------------------------------------- reproduce first

def gate_s08() -> dict:
    """S08's selection, this script's discordant() on S08's own table."""
    import pandas as pd
    m = pd.read_csv(MASTER_JOIN)
    a = m[m["answerable"] == True]  # noqa: E712
    rows = [{"precision": None if pd.isna(p) else float(p), "faith": None if pd.isna(f) else int(f)}
            for p, f in zip(a["mc_precision"], a["judge_faithfulness"])]
    cut, picked = discordant(rows)
    want = json.loads(S08_META.read_text())
    if len(picked) != want["n_discordant_answers"] or round(cut, 6) != want["discordant_rule"]["tercile_cut_value"]:
        raise Refused(f"S08 not reproduced: {len(picked)} answers, cut {cut}; meta {want['n_discordant_answers']}, "
                      f"{want['discordant_rule']['tercile_cut_value']}")
    return {"answers": len(picked), "cut": round(cut, 6), "of": len(rows)}


def fp_rows(J: dict, R) -> list[dict]:
    """The 180: judge correctness of call (a) per answer. An answer with no text would score 0 (Rule 10); a judge
    failure is refused here rather than given a score."""
    out = []
    for (run, c, q, d), v in J["rows"].items():
        if R.group_of(q) != "false_premise":
            continue
        a = v["row"]["a"]
        if a.get("status") != "ok":
            raise Refused(f"false-premise answer {c} {q} d{d}: call (a) status {a.get('status')}")
        out.append({"config": c, "question_id": q, "draw": d, "answer_key": f"{INDEX}|{c}|{q}|d{d}",
                    "score": a["scores"]["correctness"], "source": v["source"], "status": v["status"]})
    states = Counter(r["score"] for r in out)
    passes = Counter(r["config"] for r in out if r["score"] >= PASS_AT)
    if dict(states) != FP_STATES or dict(passes) != FP_PASS or len(out) != 180:
        raise Refused(f"the 180 not reproduced: {dict(states)}, {dict(passes)}")
    return out


def scores_of(ex: dict, ch: dict, pap: dict, key: dict, l3: dict, k1: dict) -> dict:
    """The nine scores of one example, with the parts behind them; refused unless they equal the facts file."""
    c, q, ak = ex["config"], ex["q"], f"{INDEX}|{ex['config']}|{ex['q']}|d1"
    row = ch[(f"exp_01__{c}__exp_v4_s20_n0", c, q, 1)]["row"]
    p, kk, l, rg, rc = pap[ak], key[ak], l3[ak], k1[(ak, "ragas")], k1[(ak, "ragchecker")]
    pc = p["detail"]["per_claim"]
    s = {"jc": row["a"]["scores"]["correctness"], "jf": row["faithfulness_b"], "mc": p["signals"]["precision"],
         "mc_n": (sum(x["supported"] for x in pc), len(pc)), "f1": kk["signals"]["f1"], "cc": (l["found"], l["n_counted"]),
         "rf": rg["scores"]["faithfulness"], "rc": rg["scores"]["factual_correctness"],
         "cf": rc["metrics"]["faithfulness"], "c1": rc["metrics"]["f1"]}
    w = ex["want"]
    same = all(s[k] == w[k] if k in ("jc", "jf", "mc_n", "cc") else abs(s[k] - w[k]) < 0.0051 for k in w)
    if not same:
        raise Refused(f"example {ex['n']} not reproduced: {s}, facts {w}")
    return s


# ---------------------------------------------------------------- sheet C's population

def claim_population(J: dict, A: dict, pap: dict, m, decompose, key25: dict, R) -> dict:
    """Every draw-1 answer of an answerable question with a MiniCheck value, its judge row, its claims whole and each
    claim's line kind. Refused where a stored precision is not supported over claims, or a stored claim is not the
    first 300 characters of the deposited decomposer's claim."""
    pop, no_value, faith_missing = [], [], Counter()
    for r, c in RUN_IDS.items():
        for q in J["questions"]:
            if R.group_of(q) != "answerable":
                continue
            if not key25[q]["answerable"]:
                raise Refused(f"{q}: answerable in the D5 key, not in key v2.5")
            ak = f"{INDEX}|{c}|{q}|d1"
            p = pap.get(ak)
            if p is None or p["signals"].get("precision") is None:
                no_value.append({"answer_key": ak, "why": "no L1 papers row" if p is None else
                                 (p.get("null_reasons") or {}).get("precision")})
                continue
            jr = J["rows"][(r, c, q, 1)]
            x = A[ak]
            if sha(x["answer"]) != p["answer_sha256"]:
                raise Refused(f"{ak}: the answer read is not the one L1 scored")
            if x["passages_kind"] != "ids":
                raise Refused(f"{ak}: passages kind {x['passages_kind']}")
            pc = p["detail"]["per_claim"]
            full = decompose(x["answer"])
            if [y[:300] for y in full] != [y["claim"] for y in pc]:
                raise Refused(f"{ak}: stored claims are not the decomposer's")
            sup = sum(y["supported"] for y in pc)
            if round(sup / len(pc), 4) != p["signals"]["precision"]:
                raise Refused(f"{ak}: stored precision is not supported over claims")
            heads = md_headings(x["answer"], decompose)
            kinds = [line_kind(y, heads, m) for y in full]
            kept = [y for y, k in zip(pc, kinds) if not k]
            st = (jr["row"].get("b") or {}).get("status")
            if jr["row"].get("faithfulness_b") is None:
                faith_missing[str(st)] += 1
            pop.append({"answer_key": ak, "config": c, "question_id": q, "precision": p["signals"]["precision"],
                        "faith": jr["row"].get("faithfulness_b"), "source": jr["source"], "status": jr["status"],
                        "claims": full, "per_claim": pc, "kinds": kinds, "n_kept": len(kept),
                        "precision_kept": round(sum(y["supported"] for y in kept) / len(kept), 4) if kept else None})
    return {"pop": pop, "no_value": no_value, "faith_missing": dict(faith_missing)}


def select(P: dict) -> dict:
    """Both selections: the stored precision, and D172's on the stored labels (a row with no claim left has no value).
    The options for sheet C are counted here; none of them is applied."""
    pop = P["pop"]
    cut, picked = discordant(pop)
    pk = [dict(r, precision=r["precision_kept"]) for r in pop]
    cutk, pickedk = discordant(pk)
    n_all = sum(len(r["claims"]) for r in picked)
    flag = sum(1 for r in picked for k in r["kinds"] if k)
    cap = lambda rows, n, f: sum(min(n, (r["n_kept"] if f else len(r["claims"]))) for r in rows)   # noqa: E731
    return {"population": len(pop), "cut": cut, "picked": picked, "cut_d172": cutk, "picked_d172": pickedk,
            "counts": {"answers": len(picked), "claims": n_all, "flagged_lines": flag, "kept_claims": n_all - flag,
                       "answers_d172": len(pickedk), "claims_d172": sum(r["n_kept"] for r in pickedk),
                       "cap5_per_answer": cap(picked, 5, False), "cap5_per_answer_d172": cap(pickedk, 5, True)}}


def claim_rows(picked: list[dict], A: dict, d172: bool, cap: int = 0) -> tuple[list[dict], dict]:
    """The rows of sheet C in their sheet order: answers by ranks(), claims in the answer's order. cap > 0 (O3, D226)
    keeps an answer's first cap claims by ranks() over that answer's claims (column I's fixed order), still shown in
    the answer's order."""
    aid = ranks([r["answer_key"] for r in picked])
    rows = []
    for r in sorted(picked, key=lambda r: aid[r["answer_key"]]):
        ix = [i for i, k in enumerate(r["kinds"]) if not (d172 and k)]
        if cap > 0:
            rk = ranks([f"{r['answer_key']}|{i}" for i in ix])
            ix = [i for i in ix if rk[f"{r['answer_key']}|{i}"] <= cap]
        for i in ix:
            rows.append({"answer_id": f"A{aid[r['answer_key']]:02d}", "r": r, "i": i, "k": ix.index(i) + 1, "n": len(ix),
                         "ck": f"{r['answer_key']}|{i}"})
    over = ranks([x["ck"] for x in rows])
    within = {}
    for r in picked:
        cks = [x["ck"] for x in rows if x["r"] is r]
        within.update(ranks(cks))
    for j, x in enumerate(rows, 1):
        x.update(row_id=f"C{j:04d}", over=over[x["ck"]], within=within[x["ck"]])
    return rows, {r["answer_key"]: f"A{aid[r['answer_key']]:02d}" for r in picked}


def passage_cell(p: dict) -> str:
    chunk = "" if p.get("chunk_idx") is None else f", chunk {p['chunk_idx']}"
    return f"[{p.get('source')}{chunk}]\n{flow(p['text'])}"


# ---------------------------------------------------------------- workbook

def sheet_a(wb, fp: list[dict], A: dict, key25: dict, issues: dict) -> list[dict]:
    low = [r for r in fp if r["score"] < PASS_AT]
    order = ranks([r["answer_key"] for r in low])
    low.sort(key=lambda r: order[r["answer_key"]])
    pieces = [read_parts(A[r["answer_key"]]["answer"]) for r in low]
    k = max(len(x) for x in pieces)
    ws = wb.create_sheet("A False premise")
    cols = [("Row", 7), ("Your call: refutes / hedges / accepts", 13), ("Your note", 22), ("Question", 45),
            ("The false premise, as the key states it", 55), ("The key's correct answer", 55)] + \
           [(f"Answer, part {i}" if k > 1 else "Answer", 90) for i in range(1, k + 1)]
    rows = []
    for j, (r, ps) in enumerate(zip(low, pieces), 1):
        q = r["question_id"]
        r["row_id"] = f"F{j:02d}"
        rows.append([r["row_id"], None, None, key25[q]["question"], issues[q], key25[q]["expected_answer"], *ps])
    table(ws, cols, rows, "D2", 400, {2: CALLS_A})
    return low


def sheet_b(wb, shown: list[dict]) -> None:
    pass_n = max(len(s["passages"]) for s in shown)
    ans_n = max(len(s["answer_parts"]) for s in shown)
    pap_n = max(len(s["paper_parts"]) for s in shown)
    ws = wb.create_sheet("B Examples")
    cols = [("Example", 8), ("Question", 38), ("Your call: who is right?", 24), ("Your note", 24), ("Why this example", 30),
            ("Strategy, draw", 12), ("Judge correctness", 10), ("Judge faithfulness", 10), ("MiniCheck against papers", 12),
            ("MiniCheck against key (F1)", 10), ("Concepts", 9), ("RAGAS faithfulness", 10), ("RAGAS factual correctness", 10),
            ("RAGChecker faithfulness", 11), ("RAGChecker F1", 11), ("The judge's reason", 50),
            ("MiniCheck's claims and labels", 50), ("The key's concepts", 40), ("The key's expected answer", 50)] + \
           [(f"Answer, part {i}" if ans_n > 1 else "Answer", 70) for i in range(1, ans_n + 1)] + \
           [(f"Passage {i}", 90) for i in range(1, pass_n + 1)] + \
           [(f"Source paper, part {i}", 90) for i in range(1, pap_n + 1)]
    rows = []
    for s in shown:
        v = s["scores"]
        rows.append([f"Example {s['ex']['n']}", s["question"], None, None, s["ex"]["why"],
                     f"{NAMES[s['ex']['config']]}, draw 1", v["jc"], v["jf"],
                     f"{v['mc']:.2f} ({v['mc_n'][0]} of {v['mc_n'][1]} claim{'' if v['mc_n'][1] == 1 else 's'})", f"{v['f1']:.2f}",
                     f"{v['cc'][0]} of {v['cc'][1]}", f"{v['rf']:.2f}", f"{v['rc']:.2f}", f"{v['cf']:.2f}", f"{v['c1']:.2f}",
                     s["reason"], s["labels"], s["concepts"], s["expected"],
                     *(s["answer_parts"] + [None] * (ans_n - len(s["answer_parts"]))),
                     *(s["passages"] + [None] * (pass_n - len(s["passages"]))),
                     *s["paper_parts"]])
    table(ws, cols, rows, "E2", 400, {})


def sheet_c(wb, rows: list[dict], A: dict, key25: dict) -> None:
    n_pass = max(len(A[x["r"]["answer_key"]]["passages"]) for x in rows)
    ans_parts = {x["r"]["answer_key"]: parts(A[x["r"]["answer_key"]]["answer"], CELL_MAX) for x in rows}
    n_ans = max(len(v) for v in ans_parts.values())
    ws = wb.create_sheet("C Claims")
    cols = [("Row", 7), ("Answer", 6), ("Claim no.", 8), ("Line kind", 10), ("Claim", 42),
            ("Your call: supported / partly / not", 11), ("Your note", 14), ("Rank, all claims", 7), ("Rank in this answer", 7),
            ("Question", 40)] + [("The whole answer" if i == 1 else f"The whole answer, continued {i}", 50) for i in range(1, n_ans + 1)] + \
           [(f"Passage {i}", 90) for i in range(1, n_pass + 1)]
    out = []
    for x in rows:
        r, i = x["r"], x["i"]
        ak = r["answer_key"]
        ps = [passage_cell(p) for p in A[ak]["passages"]]
        ap = ans_parts[ak]
        out.append([x["row_id"], x["answer_id"], f"{x['k']} of {x['n']}", r["kinds"][i], r["claims"][i], None, None, x["over"],
                    x["within"], key25[r["question_id"]]["question"], *(ap + [None] * (n_ans - len(ap))), *ps])
    table(ws, cols, out, "H2", 400, {6: CALLS_C})


def verify(path: Path, low: list[dict], claim: list[dict], A: dict) -> dict:
    """Reads the workbook back: row counts, every rating cell blank, the whole answers and passages in their cells, no
    strategy name in a blind sheet's cells outside the answers themselves."""
    import openpyxl
    wb = openpyxl.load_workbook(path)
    bad = check_blank(wb)
    if bad:
        raise Refused(f"rating cells not blank: {bad[:5]}")
    a, c = wb["A False premise"], wb["C Claims"]
    if a.max_row - 1 != len(low) or c.max_row - 1 != len(claim) or wb["B Examples"].max_row != 4:
        raise Refused(f"row counts: {a.max_row - 1}, {c.max_row - 1}, {wb['B Examples'].max_row - 1}")
    ha = [x.value for x in a[1]]
    first = ha.index("Answer, part 1") if "Answer, part 1" in ha else ha.index("Answer")
    for i, r in enumerate(low, 2):
        got = "".join(a.cell(i, j).value or "" for j in range(first + 1, a.max_column + 1))
        if got != cell_text(A[r["answer_key"]]["answer"]):
            raise Refused(f"sheet A row {i}: the answer is not whole")
    hc = [x.value for x in c[1]]
    p1 = hc.index("Passage 1") + 1
    for i, x in enumerate(claim, 2):
        if c.cell(i, 5).value != cell_text(x["r"]["claims"][x["i"]]):
            raise Refused(f"sheet C row {i}: claim differs")
        want = [cell_text(passage_cell(p)) for p in A[x["r"]["answer_key"]]["passages"]]
        got = [c.cell(i, p1 + j).value for j in range(len(want))]
        if got != want or (p1 + len(want) <= c.max_column and c.cell(i, p1 + len(want)).value is not None):
            raise Refused(f"sheet C row {i}: passages differ")
    heads = " ".join(str(h) for h in ha + hc).lower()
    for w in ("judge", "strategy", "minicheck", "score"):
        if w in heads:
            raise Refused(f"a blind sheet's header says {w!r}")
    return {"sheet_a_rows": a.max_row - 1, "sheet_b_rows": 3, "sheet_c_rows": c.max_row - 1, "columns_c": c.max_column}


def write_key(path: Path, low: list[dict], claim: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet", "row", "answer_id", "answer_key", "strategy", "question_id", "draw", "judge_correctness_a",
                    "judge_row_key", "claim_index", "minicheck_supported", "minicheck_probability", "judge_faithfulness_b",
                    "precision_stored", "line_kind"])
        for r in low:
            w.writerow(["A", r["row_id"], "", r["answer_key"], NAMES[r["config"]], r["question_id"], r["draw"], r["score"],
                        r["status"], "", "", "", "", "", ""])
        for x in claim:
            r, i = x["r"], x["i"]
            y = r["per_claim"][i]
            w.writerow(["C", x["row_id"], x["answer_id"], r["answer_key"], NAMES[r["config"]], r["question_id"], 1, "",
                        r["status"], i + 1, y["supported"], y["probability"], r["faith"], r["precision"], r["kinds"][i]])


def applied(m: dict) -> str:
    """The one line saying which of the options below this pack applied (D226: O2 and O3)."""
    o = (["O2 (D172's filter: headings and source-list lines left out)"] if m["selection_mode"] == "d172" else []) + \
        ([f"O3 (at most {m['cap_per_answer']} claims per answer, column I's order)"] if m.get("cap_per_answer") else [])
    return ("**Applied in this pack:** " + " and ".join(o) + f". Sheet C has {m['sheets']['C']:,} rows.") if o else \
        "**Applied in this pack:** none of the options; every claim is a row."


def readme(m: dict) -> str:
    c, t, g, sel = m["counts"], m["time_hours"], m["sheets"], m["selection"]
    no = sel["no_minicheck_value"]
    return f"""# Valerio's reading pack, November 2026

Everything you have to rate is in `{XLSX}`. Fill in only the yellow columns, save under the same name, and tell Claude when a sheet is done. Do not open `{KEYFILE}` until you have finished: it names each answer's strategy and scores.

| Sheet | What you do | Rows | Hours (estimate) |
|---|---|---|---|
| A False premise | Say whether each answer refutes, hedges or accepts | {g['A']} | {t['A']} |
| B Examples | Say who is right, for Supplementary 17 | {g['B']} | {t['B']} |
| C Claims | Say whether the passages support each claim | {g['C']:,} | {t['C']} |

A and B: {WPM} words a minute, plus 1 minute an answer (A) or 5 minutes an example (B). C: one minute a claim.

## Sheet A

Rule: of the 180 answers from the six strategies to the 10 false-premise questions (three draws each), the {g['A']} whose judge correctness is below 4 on the final key. No score or strategy is shown, and a hash sets the order. Refutes: the answer says the premise is wrong. Hedges: it neither rejects nor accepts it. Accepts: it treats the premise as true. A long answer runs on into the next column.

## Sheet B

Examples 1, 2 and 4 (D200): 11_asf_burkina_faso_FR1, 04_fastp_FR1 and CD_018, draw 1. Each row holds the nine scores, the passages and the whole source paper, split over columns so it can be read. Find (Cmd+F) reaches a table.

## Sheet C

Rule: the protocol's (findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md:102-104) on your choice S.5 a. Of the {sel['population']} draw-1 answers to answerable questions with a MiniCheck value, those where the judge reading the passages gives faithfulness 5, on the final key, and MiniCheck against the papers is in its lowest third (at or below {sel['cut']:.4f}). That is **{c['answers']} answers and {c['claims']:,} claims**, and every claim is a row. {len(no)} answers have no MiniCheck value ({sum(1 for x in no if x['why'] == 'no L1 papers row')} have no row yet), and {sum(sel['no_faithfulness_in_population'].values())} have no faithfulness because the judge call failed, so none of these can be picked.

The claim stays on the left while you scroll right through every passage the system saw. Line breaks in a passage became spaces so it fits its cell; no word changed. Judge only from the passages. Supported: they state or plainly imply the claim. Partly: only some of it is there. Not: it is absent or contradicted. This wording is Claude's; change it before you start if you prefer.

{applied(m)}

## Decide before starting sheet C

{t['C']} hours is too much for one person before 14 November. Claude did not cut it, because the protocol names no cap. Any cut is your amendment, dated before the first rating and reported as a departure (S08b:98).

- **O1, rate everything.** {c['claims']:,} claims, {t['C']} hours. The protocol as written.
- **O2, apply your own decision first.** D172 and FF20 took source lists and headings out of MiniCheck's claims, but that filter is unbuilt. {c['flagged_lines']:,} rows are such lines (column D, by the only rule measured so far, which misses split pieces of a source list). Recounting MiniCheck from its stored labels and running the same rule gives {c['answers_d172']} answers and {c['claims_d172']:,} claims, {hours(c['claims_d172'])} hours. Claude rebuilds the sheet in one command; the filter must be the one Figure 5 uses.
- **O3, cap each answer.** Up to 5 claims per answer, column I's fixed order: {c['cap5_per_answer']} claims, {hours(c['cap5_per_answer'])} hours. With O2: {c['cap5_per_answer_d172']} claims, {hours(c['cap5_per_answer_d172'])} hours.
- **O4, a random sample.** Column H up to 300: 5.0 hours. Claims from one answer are alike, so it says less than 300 suggests.

Advice: O2 with O3. O2 applies your own rule, so you do not rate lines that are not claims. O3 keeps every picked answer in, and the check is about answers. The check stays descriptive either way (S08b:96, 104).
"""


def main() -> int:
    install_guard()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--selection", choices=("stored", "d172"), default="stored")
    ap.add_argument("--cap-per-answer", type=int, default=0, help="O3 (D226): at most this many claims per answer; 0 keeps all")
    ap.add_argument("--s6-root", type=Path, default=None, help="default: the frozen set fig3_s6_inputs")
    a = ap.parse_args()
    JR, R, S19 = deps()
    decompose, dep_sha = S19.load_decomposer()
    M = marks()
    t0 = time.time()
    g08 = gate_s08()
    with tempfile.TemporaryDirectory(prefix="S521_") as t:
        J = judge_choice(JR, a.s6_root or frozen_s6(), Path(t))
    fp = fp_rows(J, R)
    key25 = {q["id"]: q for q in json.loads(KEY25.read_text())["questions"]}
    issues = {r["id"]: r["question_issues"] for r in json.loads(KEY24_SOURCE.read_text())["records"]
              if r.get("answer_type") == "refutation"}
    if {r["question_id"] for r in fp} != set(issues):
        raise Refused("the key's false-premise questions are not the 180's")
    A = answers_of(R, J["reruns"])
    pap, kl1 = l1_rows("papers"), l1_rows("key")
    l3 = {}
    for d in read_jsonl(L3):
        if d["answer_key"] in {f"{INDEX}|{e['config']}|{e['q']}|d1" for e in EXAMPLES}:
            l3[d["answer_key"]] = d
    ex_keys = {f"{INDEX}|{e['config']}|{e['q']}|d1" for e in EXAMPLES}
    k1 = k1_rows(ex_keys)
    docs = {d["file"]: d for d in read_jsonl(PAPERS)}
    shown = []
    for e in EXAMPLES:
        ak = f"{INDEX}|{e['config']}|{e['q']}|d1"
        run = f"exp_01__{e['config']}__exp_v4_s20_n0"
        s = scores_of(e, J["rows"], pap, kl1, l3, k1)
        x, q = A[ak], key25[e["q"]]
        text = "\n\n".join(docs[f]["text"] for f in pap[ak]["detail"]["doc_files"])
        if sha(text) != pap[ak]["detail"]["doc_sha256"]:
            raise Refused(f"{ak}: the paper text is not the one MiniCheck read")
        status = l3[ak]["concept_status"]
        shown.append({"ex": e, "scores": s, "question": q["question"], "expected": q["expected_answer"],
                      "reason": J["rows"][(run, e["config"], e["q"], 1)]["row"]["a"].get("justification") or "",
                      "labels": "\n".join(f"{'supported' if y['supported'] else 'not supported'} ({y['probability']:.2f}): {y['claim']}"
                                          for y in pap[ak]["detail"]["per_claim"]),
                      "concepts": "\n".join(f"{st}: {c}" for c, st in zip(q["expected_concepts"], status)),
                      "answer_parts": read_parts(x["answer"]), "passages": [passage_cell(p) for p in x["passages"]],
                      "paper_parts": read_parts(text), "words": len(x["answer"].split()) +
                      sum(len(p["text"].split()) for p in x["passages"]), "files": pap[ak]["detail"]["doc_files"]})
    P = claim_population(J, A, pap, M, decompose, key25, R)
    S = select(P)
    d172 = a.selection == "d172"
    picked = S["picked_d172"] if d172 else S["picked"]
    claim, _ = claim_rows(picked, A, d172, a.cap_per_answer)

    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    low = sheet_a(wb, fp, A, key25, issues)
    sheet_b(wb, shown)
    sheet_c(wb, claim, A, key25)
    a.out.mkdir(parents=True, exist_ok=True)
    wb.save(a.out / XLSX)
    shared = share_strings(a.out / XLSX)
    v = verify(a.out / XLSX, low, claim, A)
    write_key(a.out / KEYFILE, low, claim)

    words_a = sum(len(A[r["answer_key"]]["answer"].split()) for r in low)
    mins = {"A": words_a / WPM + len(low), "B": sum(s["words"] for s in shown) / WPM + 5 * len(shown), "C": float(len(claim))}
    cc = S["counts"]
    meta = {"_provenance": {"script": "scripts/S521_valerio_reading_pack.py", "script_sha256": sha256_file(Path(__file__)),
                            "commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                                     text=True).stdout.strip(),
                            "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "seconds": round(time.time() - t0, 1),
                            "inputs": {str(p.relative_to(ROOT)): sha256_file(p)
                                       for p in (KEY25, KEY24_SOURCE, PAPERS, MASTER_JOIN, S08_META, MARKS, L3,
                                                 FIG2 / "g1_collect.jsonl")},
                            "archive": {"path": str(K1_ARCHIVE), "sha256": sha256_file(K1_ARCHIVE)},
                            "deposited_decomposer_sha256": dep_sha},
            "selection_mode": a.selection, "cap_per_answer": a.cap_per_answer, "reproduced": {"s08": g08, "false_premise_states": FP_STATES,
                                                          "false_premise_passes": FP_PASS, "examples_nine_scores": "3 of 3"},
            "s6g1": J["state"], "sheets": {"A": len(low), "B": len(shown), "C": len(claim)}, "check": v, "workbook": shared,
            "time_hours": {k: hours(x) for k, x in mins.items()}, "words_sheet_a": words_a,
            "selection": {"population": S["population"], "cut": S["cut"], "cut_d172": S["cut_d172"],
                          "no_minicheck_value": P["no_value"], "no_faithfulness_in_population": P["faith_missing"],
                          "picked_by_strategy": dict(Counter(r["config"] for r in picked)),
                          "picked_by_key_row": dict(Counter(r["status"] for r in picked))},
            "counts": cc, "passages_in_sheet_c": {"answers": len(picked), "passages": sum(len(A[r["answer_key"]]["passages"]) for r in picked)}}
    (a.out / METAFILE).write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    (a.out / README).write_text(readme(meta))
    print(json.dumps({k: meta[k] for k in ("sheets", "time_hours", "counts")}, indent=0))
    print(json.dumps({k: v for k, v in meta["selection"].items() if k != "no_minicheck_value"}, indent=0))
    print("no MiniCheck value:", len(P["no_value"]), Counter(str(x["why"]) for x in P["no_value"]))
    print("S6G1:", J["state"]["rows_read"], J["state"]["call_b_status"], J["state"]["call_b_status_by_draw"])
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refused as e:
        sys.exit(f"REFUSED: {e}")
