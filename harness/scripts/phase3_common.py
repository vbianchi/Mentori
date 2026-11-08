#!/usr/bin/env python3
"""phase3_common - what the phase 3 scripts (the paper's analyses on ground truth v2.4 under the main judge) share:
refusals, readers of input files, the provenance block, the output writer, gate bookkeeping, the reader of S406's
exp04 table and the list of published-state scripts that are not run. It computes no statistic.

    import phase3_common as p3
    g = p3.Gates("S410")
    known = p3.read_json("S410", p3.RECOMPUTE / "S281_tables.json")      # a refusal names the file
    table = p3.exp04_table()                                              # S406's rows, checked, numbers parsed
    g.gate("G1", p3.close(got, known["x"], 1e-9, "x of S281_tables.json", "S410"), "x reproduced")
    prov = p3.provenance(__file__, COMMAND, [("exp04", jl.MAIN_JUDGE)], {"gates": g.finish()})
    p3.write_outputs("S410", {OUT_JSON: json_text, OUT_MD: md_text})      # all written, or none replaced

STOPS. Every function stops with SystemExit("<script> REFUSED: <one sentence>") that names the file or the value.
<script> is the label the caller passes; exp04_table(), published() and close() without a label use "phase3_common",
provenance() the script's file name up to its first underscore. judged_ledger's and key_scope's refusals pass
through as they are, and provenance() and exp04_table() call judged_ledger's checked context, which refuses when
the merged ledgers of S388 are not on disk. A path that is not absolute is taken from the repository root, as
machine.shown takes it. read_json and read_csv_rows keep the sha256 of the bytes they parsed, which provenance()
lists without being told; a file they read twice with two contents is a refusal.

SELF-TEST. Every function on files of a temporary directory; exp04_table() on the present S406 files and on altered
copies; provenance() on the present keys and S388's record; published() on S45_depth_balanced (its import-time
statements are imports and constants) and on a temporary module that writes at import; the line each DO_NOT_RUN
entry cites, read in the working copy and, where that fails, in the copy git holds at HEAD (git show). One line per
check, each test with its own True or False; exit 1 if one fails. It writes in the temporary directory only.

    uv run python scripts/phase3_common.py
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib
import io
import json
import math
import numbers
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True                   # the self-test leaves no cache file in the repository
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import judged_ledger as jl  # noqa: E402
from machine import RECOMPUTE, ROOT, shown  # noqa: E402
from doc_paths import LETTER_REL, doc_rel  # noqa: E402  the live documents, resubmission/ (Valerio, 4 Nov)

MODULE = "phase3_common"
TIME_FIELD = "written_utc"                           # the field of a provenance block that differs between two runs
S406_CSV = RECOMPUTE / "S406_exp04_per_answer_v24.csv"
S406_JSON = RECOMPUTE / "S406_exp04_per_answer_v24.json"
_T0 = time.time()                                    # when this module was imported (provenance: code modified later)
_SEEN: dict = {}                                     # file -> sha256 of the bytes read_json or read_csv_rows parsed
_LEDGERS: set = set()                                # the merged ledgers exp04_table() read through the loader
_RECORDERS: list = []                                # every Gates recorder of the process
_SHA = re.compile(r"sha256 ([0-9a-f]{64})")
_WRITE = re.compile(r"""\.write_text\(|\.save\(|savefig\(|ggsave\(|writeLines\(|\bwrite\(|os\.replace\(|\.to_excel\("""
                    r"""|(open|ZipFile)\([^#]*["']w["']""")           # the calls the cited lines of DO_NOT_RUN hold


def refuse(script: str, message: str):
    """Stop in the repository's form: SystemExit("<script> REFUSED: <message>")."""
    raise SystemExit(f"{script} REFUSED: {message}")


def _abs(path) -> Path:
    p = Path(path)
    return (p if p.is_absolute() else ROOT / p).resolve()


def _bytes(script: str, path, note: bool = False) -> bytes:
    """The file's bytes; a file that is missing or cannot be read is a refusal that names it. With note, their
    sha256 is kept in _SEEN for provenance(), and a read that sees other bytes than an earlier one is refused."""
    p = _abs(path)
    try:
        raw = p.read_bytes()
    except OSError as e:
        refuse(script, f"{shown(p)} cannot be read ({type(e).__name__}: {e.strerror or e})")
    sha = hashlib.sha256(raw).hexdigest()
    if note and _SEEN.setdefault(p, sha) != sha:
        refuse(script, f"{shown(p)} changed during this run (sha256 {_SEEN[p][:12]} at its first read, {sha[:12]} now)")
    return raw


def sha256_file(script: str, path) -> str:
    """The sha256 of the file's bytes, read once. A file that is missing or cannot be read is a refusal that names it."""
    return hashlib.sha256(_bytes(script, path)).hexdigest()


def _no_constant(name: str):
    raise ValueError(f"{name} is not a JSON number")


def read_json(script: str, path, kind: type | None = dict):
    """The parsed JSON of a file. Refused, naming the file: a file that is missing or cannot be read; bytes that are
    not JSON (text that is not UTF-8, nesting past the interpreter's recursion limit, NaN or Infinity); a top level
    that is not a kind (a dict unless another type is passed; None accepts any)."""
    name, raw = shown(_abs(path)), _bytes(script, path, note=True)
    try:
        doc = json.loads(raw, parse_constant=_no_constant)
    except (ValueError, RecursionError) as e:
        refuse(script, f"{name} is not JSON ({type(e).__name__}: {str(e)[:120]})")
    if kind is not None and not isinstance(doc, kind):
        refuse(script, f"{name} holds a JSON {type(doc).__name__} at its top level, where a {kind.__name__} is read")
    return doc


def read_csv_rows(script: str, path, columns=()) -> tuple[list, list]:
    """(the leading lines that start with "#", the rows as dicts of text) of a CSV whose provenance is in leading
    "#" lines. A line that starts with "#" after the header is a row; blank lines are skipped, as csv.DictReader
    skips them. Refused, naming the file: a file that is missing, cannot be read or is not UTF-8 CSV; no header
    line; a column name that is blank or repeated; a name of columns that the header lacks; a row with another
    number of cells than the header; no row."""
    name, raw = shown(_abs(path)), _bytes(script, path, note=True)
    try:
        lines = list(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        n = next((i for i, x in enumerate(lines) if not x.startswith("#")), len(lines))
        table = [r for r in csv.reader(lines[n:]) if r]
    except (UnicodeDecodeError, csv.Error) as e:
        refuse(script, f"{name} is not a UTF-8 CSV file ({type(e).__name__}: {e})")
    head = table[0] if table else []
    lacking = [c for c in columns if c not in head]
    if not head or "" in head or len(set(head)) != len(head) or lacking:
        refuse(script, f"{name} " + (f"lacks the column {', '.join(lacking)}" if head and lacking
                                     else "has no header line of distinct column names after its '#' lines"))
    ragged = [i for i, r in enumerate(table[1:], 1) if len(r) != len(head)]
    if ragged or len(table) < 2:
        refuse(script, f"{name} holds " + (f"{len(ragged)} rows with another number of cells than its {len(head)} columns, "
                                           f"the first at row {ragged[0]}" if ragged else "no row"))
    return [x.rstrip("\r\n") for x in lines[:n]], [dict(zip(head, r)) for r in table[1:]]


# ---- provenance and outputs ---------------------------------------------------------------------------------

def provenance(script_path, command: str, inputs, extra: dict | None = None) -> dict:
    """The provenance block of an output, a dict of:
      script, script_sha256    script_path as machine.shown writes it, and the sha256 of its bytes at this call
      command, python          the command as given; the interpreter's version
      written_utc              the UTC time of this call (TIME_FIELD), the field same_but_time() leaves out
      key                      jl.S373.KEY and jl.S373.AS_V1, each with the sha256 that judged_ledger's checked context
                               (jl._context()) holds for it
      inputs_sha256            every file read_json or read_csv_rows parsed in this process (the two files of
                               exp04_table() among them) with the sha256 of the bytes parsed, and every file of inputs,
                               hashed at this call unless one of the two readers read it
      merged_ledgers           sha256: the value S388's record (listed_in) lists for each merged ledger named in
                               inputs, as (experiment, judge) with a name of jl.EXPERIMENTS or as a path under jl.TREE,
                               and for the ledger exp04_table() checked its rows against. No ledger is opened here;
                               judged_ledger compares that value with the ledger's bytes (judged_ledger.py:25-28)
      imported_modules_sha256  every .py file under scripts/ loaded as a module at this call, script_path left out:
                               judged_ledger, the modules it imports, this module and what the caller imported
      and the keys of extra. Paths are machine.shown's: repository-relative, deposit/ for the upstream data.
    Refused: inputs that is one path; a file that cannot be read; a pair or a path that names no ledger of S388's
    record; ledgers named whose number is not the number judged_ledger parsed in this process (the cache of
    jl._ledger), so that a ledger read and not named, or named and not read, stops the run; script_path or a loaded
    module modified after this module was imported, since its sha256 would not be that of the code that ran; a key
    of extra that the block holds.
    Not covered: what judged_ledger opens beyond the keys and the ledgers named, that is S388's record itself,
    data/upstream/MANIFEST.sha256, the result files it reads through S374's reader and the other merged ledgers
    its check hashes. A script that wants those in its block passes their paths in inputs."""
    script = _abs(script_path)
    label = script.stem.split("_")[0]
    if isinstance(inputs, (str, bytes, os.PathLike)):
        refuse(label, "provenance() takes inputs as a list of paths and (experiment, judge) pairs")
    ctx = jl._context()
    record, tree = ctx.provenance["outputs"], jl.TREE.resolve()
    files, ledgers = dict(_SEEN), set(_LEDGERS)
    for item in inputs:
        if isinstance(item, tuple):
            if len(item) != 2 or item[0] not in jl.EXPERIMENTS:
                refuse(label, f"inputs holds {item!r}, which is not (experiment, judge) with a name of jl.EXPERIMENTS")
            name = f"{jl.S388.LABEL_TO_SLUG[jl.EXPERIMENTS[item[0]]]}/{item[1]}.jsonl"
        elif tree in _abs(item).parents:
            name = _abs(item).relative_to(tree).as_posix()
        else:
            if _abs(item) not in files:
                files[_abs(item)] = sha256_file(label, item)
            continue
        if name not in record:
            refuse(label, f"{shown(jl.PROVENANCE)} lists no merged ledger {name}, which inputs names")
        ledgers.add(name)
    parsed = jl._ledger.cache_info().currsize
    if parsed != len(ledgers):
        refuse(label, f"inputs names {len(ledgers)} merged ledgers ({', '.join(sorted(ledgers)) or 'none'}) and judged_ledger "
                      f"parsed {parsed} in this run: every ledger read through the loader is named, and no other")
    mods = {Path(f).resolve() for m in list(sys.modules.values()) if (f := getattr(m, "__file__", None))} - {script}
    mods = sorted(f for f in mods if f.suffix == ".py" and HERE in f.parents)
    block = {"script": shown(script), "script_sha256": sha256_file(label, script), "command": command,
             TIME_FIELD: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "python": platform.python_version(),
             "key": {"file": shown(jl.S373.KEY), "sha256": ctx.key_sha256,
                     "v1_format_file": shown(jl.S373.AS_V1), "v1_format_sha256": ctx.scope.sha256},
             "inputs_sha256": {shown(p): h for p, h in sorted(files.items(), key=lambda x: shown(x[0]))},
             "merged_ledgers": {"listed_in": shown(jl.PROVENANCE),
                                "sha256": {shown(jl.TREE / n): record[n]["sha256"] for n in sorted(ledgers)}},
             "imported_modules_sha256": {shown(f): sha256_file(label, f) for f in mods}}
    late = [shown(f) for f in (script, *mods) if f.stat().st_mtime > _T0]
    if late:
        refuse(label, f"{late[0]} was modified after this run began, so its sha256 would not be that of the code that ran")
    twice = sorted(set(block) & set(extra or {}))
    if twice:
        refuse(label, f"extra holds the key {twice[0]}, which the provenance block holds itself")
    return {**block, **(extra or {})}


def write_outputs(script: str, outputs: dict) -> None:
    """outputs: path -> its whole content (text, written as UTF-8, or bytes), built before this call. Refused before
    a file is touched: no Gates recorder of this script label, or one whose finish() has not passed since its last
    gate; no output; a target that is not under findings/recompute/ of the repository; one target twice; content
    that is neither text nor bytes. Then every content is written to <name>.tmp beside its target and read back.
    Then, target by target, the file that is there is kept as <name>.old.tmp (a hard link) and <name>.tmp is renamed
    onto the target. When a step fails with an OSError, or the run is interrupted, each target whose rename was
    begun gets its earlier file back by a rename (a file put where there was none is removed), so the earlier
    outputs are as they were, modification time included. The .tmp and .old.tmp files are removed in every case,
    and the failure is a refusal that names the file. No folder is created."""
    mine = [g for g in _RECORDERS if g.script == script]
    if not mine or not all(g.finished for g in mine):
        refuse(script, "write_outputs needs a Gates recorder of this script whose finish() has passed; nothing is written")
    data = {}
    for path, content in outputs.items():
        p = _abs(path)
        if RECOMPUTE.resolve() not in p.parents or p in data or not isinstance(content, (str, bytes)):
            refuse(script, f"{shown(p)} is not an output to write (a target under {shown(RECOMPUTE)}, named once, with text "
                           f"or bytes as its content; this content is a {type(content).__name__}); nothing is written")
        data[p] = content.encode("utf-8") if isinstance(content, str) else content
    if not data:
        refuse(script, "write_outputs was given no output")
    tmp = {p: p.with_name(p.name + ".tmp") for p in data}
    old = {p: p.with_name(p.name + ".old.tmp") for p in data}
    begun, kept, failed, left, at, complete = [], set(), "", [], next(iter(data)), False
    try:
        for p, raw in data.items():
            at = p
            tmp[p].write_bytes(raw)
            if tmp[p].read_bytes() != raw:
                raise OSError("the bytes read back are not the bytes written")
        for p in data:
            at = p
            old[p].unlink(missing_ok=True)
            if p.is_file():
                os.link(p, old[p])
                kept.add(p)
            begun.append(p)
            os.replace(tmp[p], p)
        complete = True
    except OSError as e:
        failed = f"{shown(at)} could not be written ({type(e).__name__}: {e})"
    finally:
        for p in (() if complete else reversed(begun)):                  # a failure or an interrupt: put back
            try:
                if p in kept:
                    os.replace(old[p], p)
                elif p.is_file():
                    p.unlink()
            except OSError:
                left.append(shown(p))
        for t in (*tmp.values(), *old.values()):
            try:
                t.unlink(missing_ok=True)
            except OSError:
                left.append(shown(t))
    if failed or left:
        refuse(script, (failed or "the outputs are written")
               + (f"; not put back or not removed: {', '.join(left)}" if left else "; every target is as it was before the call"))


def same_but_time(a, b) -> bool:
    """Whether two versions of an output (text or bytes) are equal apart from the time stamp, for the check that
    two runs give the same files. Two JSON texts are compared as parsed, after TIME_FIELD is taken out of the
    object under "provenance" in each; contents that are not JSON are compared as bytes."""
    def stripped(x):
        try:
            doc = json.loads(x)
        except (ValueError, RecursionError):
            return x.encode("utf-8") if isinstance(x, str) else x
        if isinstance(doc, dict) and isinstance(doc.get("provenance"), dict):
            doc["provenance"].pop(TIME_FIELD, None)
        return doc
    return stripped(a) == stripped(b)


# ---- gates ----------------------------------------------------------------------------------------------------

def close(a, b, tol, what: str = "a compared value", script: str = MODULE) -> bool:
    """abs(a - b) <= tol. Refused, with what in the sentence and script as its label: a, b or tol that is not a
    finite number (a bool, a text, None, NaN and an infinity are refused), and a negative tol. So a malformed
    committed value stops the run with a sentence and raises no TypeError."""
    for v in (a, b, tol):
        if isinstance(v, bool) or not isinstance(v, numbers.Real) or not math.isfinite(v):
            refuse(script, f"{what}: {v!r} is not a finite number, so it is not compared")
    if tol < 0:
        refuse(script, f"{what}: the tolerance {tol!r} is negative")
    return bool(abs(a - b) <= tol)


class Gates:
    """The gates of one script. gate() prints one line and stores name, ok and message; finish() refuses, listing
    the failed gates, and otherwise returns the records for the JSON. write_outputs refuses until finish() passed."""

    def __init__(self, script: str):
        self.script, self.records, self.finished = script, [], False
        _RECORDERS.append(self)

    def gate(self, name: str, ok, message: str) -> bool:
        """Record one gate and print its line; returns ok. Refused: a name already recorded, and ok that is not a
        bool (a list or a number would pass as true)."""
        twice = any(r["name"] == name for r in self.records)
        if twice or type(ok).__name__ not in ("bool", "bool_"):
            refuse(self.script, f"gate {name} " + ("is recorded twice" if twice else f"has the result {ok!r}, not True or False"))
        self.finished = False
        self.records.append({"name": name, "ok": bool(ok), "message": message})
        print(f"  {'ok  ' if ok else 'FAIL'} {name}  {message}", flush=True)
        return bool(ok)

    def finish(self) -> list:
        """The records as a list of dicts. Refused: no gate recorded, and any failed gate (all are listed)."""
        bad = [r["name"] for r in self.records if not r["ok"]]
        if bad or not self.records:
            refuse(self.script, (f"{len(bad)} of {len(self.records)} gates failed ({', '.join(bad)})" if bad
                                 else "no gate was recorded") + "; nothing is written")
        self.finished = True
        return [dict(r) for r in self.records]


# ---- the exp04 per-answer table ---------------------------------------------------------------------------

def _cell(text: str):
    """A cell as S406 writes it (S406 cell()): None for a blank; an int or a float when the text is exactly Python's
    repr of it; the text when float() does not read it. ValueError for a text float() reads that repr does not
    write so ("0.80", "1e5", "nan"), so that no number comes back as text or rounded."""
    for kind in (int, float):
        try:
            v = kind(text)
        except ValueError:
            continue
        if repr(v) == text and (kind is int or math.isfinite(v)):
            return v
        if kind is float:
            raise ValueError(f"{text!r} is a number that Python's repr does not write so")
    return None if text == "" else text


def exp04_table() -> list[dict]:
    """The rows of S406's exp04 per-answer table (S406_CSV), in the file's order, as dicts over the columns the
    file's header names: None for a blank cell, int or float for a number exactly as written, text otherwise.
    Refused, naming the file, unless: the sha256 of the CSV is the one S406's JSON records for it
    (provenance.outputs_sha256); its one "# key" line holds the sha256 of the v1-format key and, where it holds a
    second one, of the v2.4 key, as judged_ledger's checked context has them; its ledger_key column holds each key
    of jl.load("exp04") once and no other; its group column is the loader's Row.group of that key; every cell
    that float() reads is written as repr writes it; no column holds both numbers and text."""
    name = shown(S406_CSV)
    doc = read_json(MODULE, S406_JSON)
    comments, raw = read_csv_rows(MODULE, S406_CSV, ("ledger_key", "group"))
    have = _SEEN.get(_abs(S406_CSV))
    try:
        recorded = doc["provenance"]["outputs_sha256"][name]
    except (KeyError, TypeError):
        recorded = None
    if recorded is None or recorded != have:
        refuse(MODULE, f"{name} has sha256 {str(have)[:12]} and {shown(S406_JSON)} records {str(recorded)[:12]} under "
                       "provenance.outputs_sha256: the two files are not of one run of S406")
    ctx = jl._context()
    key_lines = [c for c in comments if c.startswith("# key ")]
    hashes = _SHA.findall(key_lines[0]) if len(key_lines) == 1 else []
    if not hashes or hashes != [ctx.scope.sha256, ctx.key_sha256][:len(hashes)]:
        refuse(MODULE, f"{name} does not carry one '# key' line with the sha256 of the present key "
                       f"({ctx.scope.sha256[:12]}, v2.4 key {ctx.key_sha256[:12]}): it was scored on another key")
    try:
        ledger = {r.key: r for r in jl.load("exp04")}
    except ValueError as e:
        refuse(MODULE, f"judged_ledger gave no exp04 rows to check {name} against: {e}")
    keys = [r["ledger_key"] for r in raw]
    if len(set(keys)) != len(keys) or set(keys) != set(ledger):
        refuse(MODULE, f"{name} holds {len(keys)} rows on {len(set(keys))} ledger keys, and jl.load('exp04') holds "
                       f"{len(ledger)}; {len(set(keys) - set(ledger))} keys are in the file only and "
                       f"{len(set(ledger) - set(keys))} in the ledger only")
    off = [r["ledger_key"] for r in raw if r["group"] != ledger[r["ledger_key"]].group]
    if off:
        refuse(MODULE, f"{name} gives {len(off)} rows another group than judged_ledger, the first {off[0]!r}")
    rows = []
    for i, r in enumerate(raw, 1):
        try:
            rows.append({c: _cell(v) for c, v in r.items()})
        except ValueError as e:
            refuse(MODULE, f"{name}, row {i} ({r['ledger_key']!r}): {e}")
    mixed = [c for c in rows[0] if len({isinstance(r[c], str) for r in rows if r[c] is not None}) > 1]
    if mixed:
        refuse(MODULE, f"{name} holds both numbers and text in the column {mixed[0]}")
    _LEDGERS.add(f"{jl.S388.LABEL_TO_SLUG[jl.EXPERIMENTS['exp04']]}/{jl.MAIN_JUDGE}.jsonl")
    return rows


# ---- the published-state scripts that are not run ---------------------------------------------------------

def _e(stem: str, line: int, *writes: str) -> tuple:
    return stem, writes, f"scripts/{stem if stem.endswith('.R') else stem + '.py'}:{line}"


# The letter and 03_Methods.docx moved to resubmission/ on 4 Nov 2026; the scripts below still write their old paths
# (response/, manuscript/submission/), so the live paths are watched here instead.
_LETTER, _DRAFT = LETTER_REL, "response/Point_by_point_response_DRAFT_P1.docx"
_BLOCKS, _CAPTIONS = "paper_changes/manuscript_text_blocks.md", "S298_caption_hashes.json"
_SUPP, _FIGS = "manuscript/submission/supplementary/", "manuscript/submission/figures/"
# (script stem, the files its run writes, path:line of one of those writes): 55 scripts (56 until D304), each read in the code on
# 13 October 2026, every file named tracked by git (of a folder: files in it). It is not every script of scripts/
# that writes: the other published-state scripts rewrite their own findings/recompute outputs when run and are not
# listed. A name without "/" is under findings/recompute/; a name that ends in "/" is a folder the script writes
# files into. The line cited is the first of the listed writes a run reaches, or the write of the document, in the
# file as git holds it at HEAD.
# Backup copies are not listed. Written only under a flag: the .xlsx of S21e (--write); the letter, 03_Methods.docx
# and the blocks file of S225, S237, S239, S272 and S276 (--apply; their JSON files are written under --dry-run too).
# S278 writes nothing under --check (S337, retired 8 Nov by D304, refuses to run and its folder is gone, so it is no longer listed). S05 writes under S05.OUTDIR, which is findings/recompute unless the
# caller rebinds it. The six R figure scripts write _CAPTIONS through their write_caption.
DO_NOT_RUN = (
    # the 22 the phase 3 rules name
    _e("S72_deployment_recommendation", 184, "S72_deployment_evidence.json", _DRAFT),
    _e("S88_ed_table_pairings", 418, "S88_pairings.json", "response/Extended_Data_Table_rev2_Q3.xlsx"),
    _e("S92_rlm_compatibility", 203, "S92_rlm_compatibility.json", "S92_rlm_compatibility.md",
       "response/Extended_Data_Table_rev2_Q3b.xlsx"),
    _e("S80_ed_tables_r2q2", 155, "response/Extended_Data_Table_rev2_Q2.xlsx"),
    _e("S69_ed_table_r2q1", 115, "response/Extended_Data_Table_rev2_Q1.xlsx"),
    _e("S225_mp2_round", 529, "S225_mp2_facts.json", "S225_mp2_edits.json", "S225_mp2_methods_edits.json", _LETTER,
       doc_rel("03_Methods.docx"), _BLOCKS),
    _e("S127_r3_evalmode_table", 314, _LETTER),
    _e("S21e_table_rev13", 196, "S21_table_rev13.json", "response/Extended_Data_Table_rev1_1.3.xlsx"),
    _e("S26_pca_visual_rev", 199, "S26_signal_redundancy.png", "S26_signal_redundancy.pdf", "S26_signal_redundancy.json"),
    _e("S116_signal_venn", 122, "S116_signal_venn.png", "S116_signal_profiles.png", "S116_signal_venn.md"),
    _e("S117_signal_regions", 97, "S117_signal_regions.png", "S117_signal_regions.pdf", "S117_signal_regions.md"),
    _e("S11_prep", 67, "S11_exp05_tidy.csv", "S11_cellcounts.csv"),
    _e("S49_corpus_rejudged", 160, "S11_exp05_tidy_rejudged.csv", "S49_corpus_rejudged.json", "S49_corpus_rejudged.md"),
    _e("S11_corpus_mixed_model.R", 133, "S11_fig3d_subset_panel.csv", "S11_corpus_scaling.json", "S11_corpus_scaling.md"),
    _e("S10_depth_refit", 310, "S10_fig3a_source.csv", "S10_depth_refit.json", "S10_depth_refit.md"),
    _e("S45_depth_balanced", 151, "S45_depth_balanced.json", "S45_depth_balanced.md"),
    _e("S184_depth_share_2x2", 159, "S184_depth_share_2x2.json", "S184_depth_share_2x2.md"),
    _e("S283_depth_tidy", 98, "S283_depth_tidy.csv", "S283_depth_tidy.json"),
    _e("S300_depth_refit_clean", 152, "S300_depth_tidy_clean.csv", "S300_depth_fits_clean.json"),
    _e("S308_depth_by_run", 130, "S308_depth_by_run.json", "S308_depth_by_run.md"),
    _e("S66_corpus_grid", 549, "S66_corpus_grid.json", "S66_corpus_grid.md"),
    _e("S68_r2q1_manifest", 174, "S68_r2q1_manifest.json", "S68_r2q1_manifest.md"),
    # the rules' own line on doctor.py
    _e("doctor", 344, "doctor_report.json"),
    # 32 (33 until D304 retired S337) named as writers in the hazards or NOT MOVED sections of plan_A4 to plan_A8, or in their cross-check
    _e("S05_evalmode_table", 562, "evalmode_table.json", "evalmode_table.md"),
    _e("S08_make_adjudication_sheet", 149, "S08_adjudication_sheet.csv", "S08_adjudication_meta.json"),
    _e("S67_corpus_two_axis_model.R", 368, "S67_corpus_two_axis_model.json", "S67_corpus_two_axis_model.md"),
    _e("S73_fig_corpus_grid", 130, "S73_corpus_grid_legend.md", "S73_corpus_grid.png", "S73_corpus_grid.pdf"),
    _e("S76_r2q1_decisions", 203, _DRAFT),
    _e("S124_r2_tables", 397, _LETTER),
    _e("S125_r2_prose", 251, _LETTER),
    _e("S141_tidy_corrected", 117, "S141_phase5_tidy_corrected.csv"),
    *(_e(stem, line, _SUPP) for stem, line in (                     # the Supplementary sheets and Supplementary Fig. N7
        ("S197_supp_N6", 685), ("S198_supp_N7", 427), ("S199_supp_N8", 604), ("S200_supp_N9", 393),
        ("S201_supp_N10", 248), ("S202_supp_N11", 278), ("S210_supp_N12", 186))),
    _e("S237_c12_wording", 121, "S237_c12_edits.json", _LETTER, _BLOCKS),
    _e("S239_c13_wording", 115, "S239_c13_edits.json", _LETTER),
    _e("S272_remaining_sections_round", 176, "S272_remaining_edits.json", _LETTER),
    _e("S276_comment_1_1_round", 123, "S276_comment_1_1_edits.json", _LETTER),
    _e("S278_figure3d", 158, _FIGS, "S278_figure3d.json"),
    *(_e(stem, line, _FIGS, _CAPTIONS) for stem, line in (("S282_figure2.R", 229), ("S284_figure3.R", 331), ("S286_figure4.R", 219))),
    *(_e(stem, line, _SUPP, _CAPTIONS) for stem, line in (("S292_supp_ED3.R", 240), ("S294_supp_ED4.R", 163), ("S297_supp_ED2.R", 141))),
    _e("S310_params_vs_ceiling", 91, "S310_params_vs_ceiling.json", "S310_params_vs_ceiling.md"),
    _e("S318_statistics_ledger", 103, "S318_statistics_ledger.json", "S318_statistics_ledger.csv", "S318_statistics_ledger.md"),
    _e("S320_replication_tidy", 86, "S320_replication_two_tidy.csv"),
    _e("S320_strategy_replication.R", 144, "S320_strategy_replication.json", "S320_strategy_replication.md"),
    _e("S382_exp04_objective_v22", 695, "S382_exp04_objective_v22.csv", "S382_exp04_objective_v22.md"),
    _e("S403_judge_calibration_workbook", 338, "S403_judge_calibration_v24.xlsx"),
)


def _place(written: str) -> Path:
    return ROOT / written if "/" in written else RECOMPUTE / written


def _stamps(module_name: str) -> dict:
    """file -> (modification time in ns, size) of the files published() watches for module_name: the files its
    DO_NOT_RUN entry names (for a folder, the files directly in it) and the files directly in findings/recompute/
    whose name starts with the module's name up to its first underscore, then "_". Folders are listed and os.stat
    is called; no file is opened."""
    paths = set(RECOMPUTE.glob(module_name.split("_")[0] + "_*"))
    for written in next((e[1] for e in DO_NOT_RUN if e[0] == module_name), ()):
        p = _place(written)
        paths |= set(p.iterdir()) if written.endswith("/") and p.is_dir() else {p}
    out = {}
    for p in paths:
        try:
            st = p.stat()
        except OSError:
            continue                                   # not there at this moment: absent from the snapshot
        if p.is_file():
            out[p] = (st.st_mtime_ns, st.st_size)
    return out


def published(module_name: str):
    """A published-state module of scripts/, imported for its functions (its main() is not called here). Refused:
    a module that cannot be imported or raises at import (an R script of DO_NOT_RUN is no module), and an import
    after which a watched file (_stamps) has another modification time or size, appeared or is gone, which is what
    a write at import does to it. A write at import to a file outside that list is not seen, and a module already
    loaded is returned as it is: no code of it runs again. A SystemExit of the module passes through."""
    before = _stamps(module_name)
    try:
        module = importlib.import_module(module_name)
    except Exception as e:                             # whatever the module's own code raises at import
        refuse(MODULE, f"the published-state module {module_name} cannot be imported ({type(e).__name__}: {e})")
    after = _stamps(module_name)
    changed = sorted(shown(p) for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    if changed:
        refuse(MODULE, f"importing {module_name} changed {changed[0]}" + (f" and {len(changed) - 1} more files" if changed[1:] else "")
               + ": the module writes at import, so it is not imported for its functions")
    return module


# ---- self-test ------------------------------------------------------------------------------------------------

def _refused(fn, *needles: str) -> bool:
    """True when fn() stops with a refusal whose sentence holds every needle."""
    try:
        fn()
    except SystemExit as e:
        return " REFUSED: " in str(e) and all(n in str(e) for n in needles)
    return False


def _cited(where: str, at_head: bool = False) -> str:
    """The line a DO_NOT_RUN entry cites, in the working copy or (at_head) in the copy git holds at HEAD; "" if none."""
    path, _, line = where.rpartition(":")
    try:
        text = (subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout
                if at_head else (ROOT / path).read_text(encoding="utf-8"))
        return text.splitlines()[int(line) - 1]
    except (OSError, ValueError, IndexError, subprocess.CalledProcessError):
        return ""


def _checks(tmp: Path, check) -> None:
    """The checks of the self-test, on files of tmp. It rebinds RECOMPUTE, S406_CSV, S406_JSON and DO_NOT_RUN for the
    tests that need copies; self_test() puts them back."""
    global RECOMPUTE, S406_CSV, S406_JSON, DO_NOT_RUN
    real, me, here = (RECOMPUTE, S406_CSV, S406_JSON, DO_NOT_RUN), "S999", Path(__file__)
    sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731

    def put(name: str, content) -> Path:
        (tmp / name).write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return tmp / name

    check("T1 refuse", {"the form": _refused(lambda: refuse(me, "x.json is missing"), "S999 REFUSED: x.json is missing")})
    check("T2 sha256_file", {
        "sha256 of b'abc'": sha256_file(me, put("a.bin", b"abc")) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "a missing file refused by name": _refused(lambda: sha256_file(me, tmp / "none.bin"), "none.bin"),
        "a folder refused by name": _refused(lambda: sha256_file(me, tmp), tmp.name)})
    good = put("good.json", '{"a": [1, 2.5]}')
    bad = {"a missing file": tmp / "no.json", "a file cut short": put("cut.json", '{"a": '), "NaN": put("nan.json", '{"a": NaN}'),
           "bytes that are not UTF-8": put("latin.json", b'{"a": "\xff"}'), "nesting 100,000 deep": put("deep.json", "[" * 100000),
           "a list at the top": put("list.json", "[1]")}
    t3 = {"an object read": read_json(me, good) == {"a": [1, 2.5]},
          "a list read with kind=list": read_json(me, bad["a list at the top"], list) == [1],
          **{f"{k} refused by name": _refused(lambda p=p: read_json(me, p), p.name) for k, p in bad.items()}}
    put("good.json", '{"a": 0}')
    check("T3 read_json", {**t3, "other bytes at a second read refused": _refused(lambda: read_json(me, good), "good.json", "changed")})
    bad = {"a column the header lacks": (put("c1.csv", "# c\na,b\n1,2\n"), ("a", "z")), "a missing file": (tmp / "no.csv", ()),
           "a repeated column": (put("c2.csv", "a,a\n1,2\n"), ()), "a row of another length": (put("c3.csv", "a,b\n1,2,3\n"), ()),
           "no row": (put("c4.csv", "# c\na,b\n"), ()), "no header": (put("c5.csv", "# c\n"), ()),
           "bytes that are not UTF-8": (put("c6.csv", b"a,b\n\xff,2\n"), ())}
    check("T4 read_csv_rows", {
        "leading comments, a cell with a line break, a row that starts with #, a blank line":
            read_csv_rows(me, put("ok.csv", '# made by x\n# key k\na,b\n1,"two\nlines"\n\n#3,4\n'), ("a", "b"))
            == (["# made by x", "# key k"], [{"a": "1", "b": "two\nlines"}, {"a": "#3", "b": "4"}]),
        **{f"{k} refused by name": _refused(lambda p=p, c=c: read_csv_rows(me, p, c), p.name) for k, (p, c) in bad.items()}})
    bad = {"a bool": True, "a text": "0.5", "None": None, "NaN": float("nan"), "a list": [0.5]}
    check("T5 close", {
        "equal within the tolerance": close(1.0, 1.0 + 1e-12, 1e-9), "apart": close(1, 2, 0.5) is False,
        **{f"{k} refused, value and label named": _refused(lambda v=v: close(0.5, v, 1e-9, "x of f.json", me), "S999 REFUSED: x of f.json")
           for k, v in bad.items()},
        "a negative tolerance refused": _refused(lambda: close(1, 1, -1), "negative")})

    RECOMPUTE = tmp / "recompute"
    RECOMPUTE.mkdir()
    one, two, g, w = RECOMPUTE / "one.json", RECOMPUTE / "two.md", Gates(me), Gates("S997")
    with contextlib.redirect_stdout(io.StringIO()) as printed:
        t6 = {"write_outputs refused before finish()": _refused(lambda: write_outputs(me, {one: "{}"}), "finish()"),
              "a gate that passes": g.gate("G1", True, "one"), "a gate that fails": g.gate("G2", False, "two") is False,
              "a result that is no bool refused": _refused(lambda: g.gate("G3", [1], "three"), "G3", "[1]"),
              "a repeated name refused": _refused(lambda: g.gate("G1", True, "again"), "G1 is recorded twice"),
              "finish() refused, naming the failed gate": _refused(g.finish, "1 of 2", "G2"),
              "finish() of an empty recorder refused": _refused(Gates("S998").finish, "no gate"),
              "a gate of a second recorder": w.gate("G1", True, "passes")}
    lines = printed.getvalue().splitlines()
    check("T6 Gates", {**t6, "finish() returns the records": w.finish() == [{"name": "G1", "ok": True, "message": "passes"}],
                       "one line printed per gate": lines == ["  ok   G1  one", "  FAIL G2  two", "  ok   G1  passes"]})
    state = lambda: (one.read_bytes(), one.stat().st_mtime_ns) if one.is_file() else None  # noqa: E731
    write_outputs("S997", {one: '{"v": 1}\n', two: b"first\n"})
    first = state()
    (RECOMPUTE / "blocked.md").mkdir()                       # a folder under the second target's name: the rename onto it fails
    bad = {"a rename that fails on the second output": ({one: '{"v": 2}\n', RECOMPUTE / "blocked.md": "x"}, "blocked.md"),
           "a write that fails (no such folder)": ({one: '{"v": 3}\n', RECOMPUTE / "none" / "x.json": "{}"}, "x.json"),
           "a target outside findings/recompute": ({one: '{"v": 4}\n', tmp / "out.json": "{}"}, "out.json"),
           "content that is a dict": ({one: {"v": 5}}, "dict"), "no output": ({}, "no output")}
    check("T7 write_outputs", {
        "text and bytes written": (first[0], two.read_bytes()) == (b'{"v": 1}\n', b"first\n"),
        **{f"{k} refused by name": _refused(lambda o=o: write_outputs("S997", o), n) for k, (o, n) in bad.items()},
        "after them the first output as it was, modification time too": state() == first,
        "no temporary file left": sorted(p.name for p in RECOMPUTE.iterdir()) == ["blocked.md", "one.json", "two.md"]})
    RECOMPUTE = real[0]
    j = lambda t, v: json.dumps({"provenance": {TIME_FIELD: t, "command": "c"}, "v": v})  # noqa: E731
    check("T8 same_but_time", {
        "two runs that differ in the time stamp": same_but_time(j("t1", 1), j("t2", 1).encode()),
        "two runs that differ in a value": same_but_time(j("t1", 1), j("t1", 2)) is False,
        "a time stamp outside the provenance block": same_but_time(json.dumps({TIME_FIELD: 1}), json.dumps({TIME_FIELD: 2})) is False,
        "text that is not JSON, equal and not": same_but_time("a\n", b"a\n") and not same_but_time("a\n", "b\n")})

    table = exp04_table()
    text = real[1].read_text(encoding="utf-8")
    body = [x for x in text.splitlines() if not x.startswith("#")]
    loader = {r.key: r for r in jl.load("exp04")}
    kinds = {k: sum(type(v).__name__ == k for r in table for v in r.values()) for k in ("int", "float", "str", "NoneType")}
    back = [{c: "" if v is None else v if isinstance(v, str) else repr(v) for c, v in r.items()} for r in table]
    check("T9 exp04_table", {
        f"{len(table)} rows of {len(table[0])} columns, one per row of jl.load('exp04')": len(table) == len(loader),
        f"each cell written back (repr of {kinds['int']} int and {kinds['float']} float, {kinds['str']} texts, {kinds['NoneType']} blanks) "
        "is csv.DictReader's text": back == list(csv.DictReader(body)),
        "passed and score are the loader's Row.passed and Row.score": all(
            (r["passed"], r["score"]) == (int(loader[r["ledger_key"]].passed), loader[r["ledger_key"]].score) for r in table)})

    src, name = put("input.txt", "x"), f"{jl.load('exp04')[0].slug}/{jl.load('exp04')[0].judge}.jsonl"
    record = read_json(me, jl.PROVENANCE)["outputs"]         # S388's record, parsed here a second time
    prov = provenance(here, "uv run python scripts/phase3_common.py", [src], {"seed": 7})
    bad = {"a missing input": (here, [tmp / "gone.csv"], None, "gone.csv"),
           "an unknown experiment": (here, [("exp99", jl.MAIN_JUDGE)], None, "exp99"),
           "a ledger S388's record does not list": (here, [("exp04", "nobody")], None, "nobody.jsonl"),
           "a ledger named that the loader did not parse": (here, [("naive", jl.MAIN_JUDGE)], None, "parsed 1"),
           "a key of extra that the block holds": (here, [], {"command": "x"}, "command"),
           "inputs that is one path": (here, src, None, "inputs"),
           "a script written after the run began": (put("S996_late.py", "x = 1\n"), [], None, "S996_late.py")}
    check("T10 provenance", {
        "the script and the sha256 of its bytes": (prov["script"], prov["script_sha256"])
        == ("scripts/phase3_common.py", sha(here.read_bytes())),
        "the two key files as hashed here": (prov["key"]["sha256"], prov["key"]["v1_format_sha256"])
        == (sha(jl.S373.KEY.read_bytes()), sha(jl.S373.AS_V1.read_bytes())),
        "the exp04 ledger as S388's record lists it": prov["merged_ledgers"]["sha256"] == {shown(jl.TREE / name): record[name]["sha256"]},
        "the files the readers parsed and the file of inputs": {shown(real[1]), shown(real[2])} <= set(prov["inputs_sha256"])
        and prov["inputs_sha256"][shown(src)] == "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881",
        "judged_ledger, key_scope and machine among the modules, the script not": prov["script"] not in prov["imported_modules_sha256"]
        and {"scripts/judged_ledger.py", "scripts/key_scope.py", "scripts/machine.py"} <= set(prov["imported_modules_sha256"]),
        "the time in UTC and extra": bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", prov[TIME_FIELD])) and prov["seed"] == 7,
        **{f"{k} refused": _refused(lambda s=s, i=i, x=x: provenance(s, "c", i, x), n) for k, (s, i, x, n) in bad.items()}})

    def altered(i: int, new: str, rec: str | None = None):
        global S406_CSV, S406_JSON
        S406_CSV = put(f"t{i}.csv", new)
        S406_JSON = put(f"t{i}.json", json.dumps({"provenance": {"outputs_sha256": {shown(S406_CSV): rec or sha(new.encode("utf-8"))}}}))
        return exp04_table

    def first_row(change) -> str:                            # the table with one cell of its first row changed
        cells, out = dict(next(csv.DictReader(body))), io.StringIO()
        change(cells)
        csv.writer(out, lineterminator="").writerow(cells.values())
        return text.replace(body[1], out.getvalue(), 1)

    key_line = next(x for x in text.splitlines() if x.startswith("# key "))
    a_float = next((c for c, v in table[0].items() if isinstance(v, float)), "")
    bad = {"a table that S406's JSON does not record": (text, "0" * 64, "not of one run"),
           "a key line of another key": (text.replace(key_line, key_line.replace(prov["key"]["v1_format_sha256"], "0" * 64)), None,
                                         "another key"),
           "a row less than the ledger": (text.replace(body[1] + "\n", "", 1), None, "1 in the ledger only"),
           "another group than the loader's": (first_row(lambda c: c.update(group="not_answerable")), None, "another group"),
           "a number not written as repr writes it": (first_row(lambda c: c.update({a_float: c.get(a_float, "") + "0"})), None, "repr"),
           "a text in a column of numbers": (first_row(lambda c: c.update({a_float: "n/a"})), None, a_float)}
    t11 = {f"{k} refused": _refused(altered(i, new, rec), f"t{i}.csv", n) for i, (k, (new, rec, n)) in enumerate(bad.items())}
    S406_JSON = put("bare.json", "{}")
    t11["S406's JSON without the record refused"] = _refused(exp04_table, "bare.json", "not of one run")
    S406_JSON = tmp / "none.json"
    check("T11 exp04_table on altered copies", {**t11, "S406's JSON missing refused by name": _refused(exp04_table, "none.json")})
    S406_CSV, S406_JSON = real[1], real[2]

    at_head = [e[0] for e in DO_NOT_RUN if not _WRITE.search(_cited(e[2])) and _WRITE.search(_cited(e[2], at_head=True))]
    off = [e[0] for e in DO_NOT_RUN if e[0] not in at_head and not _WRITE.search(_cited(e[2]))
           or not e[1] or not all(_place(x).exists() for x in e[1])]
    check("T12 DO_NOT_RUN", {
        f"each of the {len(DO_NOT_RUN)} cited lines holds a write and every file or folder named exists (off: {off or 'none'}; "
        f"line found at HEAD only, the working copy being modified: {at_head or 'none'})": not off,
        "no script twice": len({e[0] for e in DO_NOT_RUN}) == len(DO_NOT_RUN)})

    put("p3c_writer.py", "from pathlib import Path\nPath(__file__).with_name('p3c_written.txt').write_text('x')\n")
    sys.path.insert(0, str(tmp))
    DO_NOT_RUN = real[3] + (("p3c_writer", (str(tmp / "p3c_written.txt"),), "p3c_writer.py:2"),)
    watched = len(_stamps("S45_depth_balanced"))
    check("T13 published", {
        f"S45_depth_balanced imported for its functions, {watched} watched files unchanged":
            watched >= 2 and callable(getattr(published("S45_depth_balanced"), "fit", None)),
        "a module that writes at import refused, naming the file": _refused(lambda: published("p3c_writer"), "p3c_written.txt"),
        "an R script of the list refused": _refused(lambda: published("S11_corpus_mixed_model.R"), "S11_corpus_mixed_model.R"),
        "a name that is no module refused": _refused(lambda: published("p3c_no_such_module"), "p3c_no_such_module")})


def self_test() -> int:
    global RECOMPUTE, S406_CSV, S406_JSON, DO_NOT_RUN
    real, fails = (RECOMPUTE, S406_CSV, S406_JSON, DO_NOT_RUN), []

    def check(name: str, tests: dict) -> None:
        ok = all(v is True for v in tests.values())
        print(f"  {'ok  ' if ok else 'FAIL'} {name}: " + "; ".join(f"{k} {v is True}" for k, v in tests.items()), flush=True)
        fails.extend([] if ok else [name.split()[0]])

    print(f"phase3_common self-test: {shown(S406_CSV)}, {shown(jl.PROVENANCE)}, {len(DO_NOT_RUN)} DO_NOT_RUN entries")
    with tempfile.TemporaryDirectory() as td:
        try:
            _checks(Path(td).resolve(), check)
        except SystemExit as e:                              # a refusal outside a test, for example S406's files mid-rewrite
            print(f"  FAIL the self-test was stopped: {e}")
            fails.append("stopped")
        finally:
            RECOMPUTE, S406_CSV, S406_JSON, DO_NOT_RUN = real
            sys.path[:] = [p for p in sys.path if p != str(Path(td).resolve())]
            sys.modules.pop("p3c_writer", None)
    print(f"\n{'PASSED' if not fails else 'FAILED ' + ' '.join(fails)}; nothing written in the repository")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
