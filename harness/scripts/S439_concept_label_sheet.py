#!/usr/bin/env python3
"""S439 - the blind label sheet for the concept matchers (D17, O71; notes/DECISIONS_2026-10-13.md), and the
scoring of each matcher against the labels once the sheet is filled.

WHY. Concept recall is the share of the answer key's concepts that an answer contains. Three rules decide "contains":
the exact one (the concept's text is a substring of the answer), the loose one (scripts/concept_match_loose.py) and
the candidate that adds word stems to the loose one (scripts/concept_match_stem.py). D17: Valerio labels by hand
whether each concept of 36 sampled exp04 answers is stated in the answer, on a sheet that shows no matcher's
verdict, and each matcher is then scored against his labels. --build makes the sheet and the key file that holds
what the sheet hides. --analyze reads the filled sheet and writes the rates. Neither mode calls a model or opens a
connection, and neither names a matcher to use.

    uv run python scripts/S439_concept_label_sheet.py --build
    uv run python scripts/S439_concept_label_sheet.py --analyze [--sheet <a filled copy saved under another name>]

POPULATION (both modes read it the same way, population()). judged_ledger.load("exp04"), group "answerable": 516
answers, 6 strategies x 86 questions. The text of an answer is the deposit row the ledger key names, through the
loader's own resolver (judged_ledger._resolve, which holds the row to the ledger's question and answer length) and
S374's answer(). The concepts, the question and the expected answer of a question are those of the v1-format key
(S373.AS_V1) as the loader's checked context holds them. One pair is one answer with one concept of its question:
3,426 pairs.

MATCHERS, one verdict per pair each (verdicts()):
  exact       the concept's lower-cased text is a substring of the lower-cased answer
  exact_o30   the deposited exp04 scorer's compute_concept_recall, called on the one concept, returns 1.0. This is
              how O30 reads rule 1 of the loose matcher for exp04; the function is lifted by S382.deposited_scorer(),
              S382 being imported through phase3_common.published (its main is not called)
  loose       concept_match_loose.concept_recall_loose finds the concept (found_by "exact" or "loose")
  loose_o30   loose or exact_o30: the verdict behind S382's concept_recall_loose_v22
  stem        concept_match_stem.concept_recall_stem finds the concept (found_by "exact", "loose" or "stem")
  stem_o30    stem or exact_o30

THE DRAW (draw()). 36 answers, 6 per strategy. The answers of a strategy are split in two strata: "stem_adds", the
answers with at least one concept that stem finds and loose does not (both as the two modules decide, with the plain
exact rule as rule 1), and "no_stem_add", the others. The quota is 3 answers per stratum; a stratum that holds
fewer than 3 answers gives what it holds and the other stratum of the strategy gives the rest (quotas()). The 516
answers, in the order strategy then question id, each get a number from random.Random("S439 draw <SEED>").random()
and are sorted by it. Going down that order, an answer is taken when its stratum still lacks one and no answer to
the same question was taken before; the pass stops when every quota is full (select()). Should a quota stay short
at the end of the order, what it lacks is taken from the other stratum of the strategy in a second pass, and only
if that fails too is the rule on questions dropped in a third; the outputs say which passes the draw used. The
sampled answers are then put in the sheet's order by a second stream, random.Random("S439 order <SEED>").

INCLUSION PROBABILITY. The rule on questions makes the chance of an answer depend on which other answers share its
question, so it is not quota / stratum size, and this script computes no formula for it. It is estimated: select() is run
on N_SIM orders drawn from numpy.random.RandomState(SEED) (the legacy generator, whose stream numpy keeps fixed),
and an answer's inclusion probability is the share of those draws that take it. The key file holds that share, its
Monte Carlo standard error sqrt(p(1-p)/N_SIM) and, beside them, quota / stratum size.

THE SHEET, response/concept_match_labels/concept_labels_v1.xlsx (the one file this script writes outside
findings/recompute/). Sheet "How to label": at most twelve sentences and six examples. The examples are entries of
EXAMPLES, written by hand on 13 October: the first two per label whose question has no answer in the sample (failing
that, whose answer is not in the sample), each held to the key and to its answer's text. Sheet "labels": one row per pair
of the sampled answers, the concepts of an answer together in the key's order. Columns: row id, answer id,
question, concept, expected answer, answer, "stated?" (a list of yes, partly, no) and comment, both empty. The
question, the expected answer and the answer are one merged cell over the rows of their answer. An answer longer
than ANSWER_CELL characters continues in further "answer (continued ...)" columns, cut after a line end where one
fits. A character that a workbook cannot hold (a control character other than tab and line feed, a lone surrogate,
U+FFFE, U+FFFF) is shown as U+FFFD, and a carriage return as a line feed; the matchers read the deposit's text, not
the shown one, and the key file counts the characters replaced. The sheet holds no strategy, stratum, verdict,
ledger key or question id.
The workbook is built in memory with a fixed creation date and fixed archive time stamps, so two builds give the
same bytes. It is written to <name>.tmp, read back and renamed onto its target by this script's own code
(write_all), since phase3_common.write_outputs takes targets under findings/recompute/ only; the key file and the
report go through write_outputs, and when that fails the earlier sheet is put back. A build refuses to replace a
sheet that holds a label or a comment.

THE KEY FILE, findings/recompute/S439_concept_label_key.json: per row id the ledger key, question id, strategy,
concept index, the six verdicts, the candidate's detail for the concept, the stratum, the inclusion probability and
the sha256 of the concept and of the shown answer; per answer the same and the sha256 of the deposit's text; the
population table (pairs by pattern of the six verdicts), the sample table, the seed and the provenance.
findings/recompute/S439_concept_label_sheet.md describes the design.

GATES of --build, all before anything is written (a failure is one sentence, nothing written):
  B1  the two matcher modules' own cases hold (spec_failures() of each)
  B2  the population is KNOWN's 516 answers (6 strategies x 86 questions, one deposit file) and 3,426 pairs
  B3  loose finds KNOWN's 1,774 pairs; exact is the loose module's found_by "exact" on every pair; every pair exact
      finds, exact_o30 and loose find, and every pair loose finds, stem finds
  B4  findings/recompute/S382_exp04_objective_v22.csv records the present key and answers file, and on each of the
      516 answers its concept_recall_v22 is exact_o30's found share and its concept_recall_loose_v22 loose_o30's
  B5  the draw: 36 answers, 6 per strategy, each stratum at its quota unless the second pass moved one, select()
      run a second time gives the same answers, and no question twice unless the third pass was used
  B6  the simulated inclusion probabilities: every answer of the population was taken at least once in N_SIM draws,
      and they sum to 36
  B7  six examples, two per label, each on an answer outside the sample, its concept in the key and its quotation
      in that answer's text as the sheet would show it (runs of white space read as one space)
  B8  the plan: every sampled answer has each of its concepts on one row, no text holds a character or an escape
      sequence a workbook would change or is longer than a cell, the pieces of each answer joined are its text, and
      the sheet "How to label" has at most twelve sentences
  B9  the workbook's bytes, read back with openpyxl: the two sheets, every cell equal to the plan, no cell beyond
      the planned rows and columns, the label and comment cells empty, the planned merged cells and list
  B10 blindness: the archive holds the two sheets and no part outside PARTS (so no comment, drawing or custom
      property part), no defined name but the filter's, both sheets visible, no cell comment, the document
      properties are the fixed ones, and each strategy name, the deposit file's name (part of every ledger key),
      each stratum name, each O30 verdict name and the words found_by and inclusion occur in the archive exactly as
      often as in the shown texts

--analyze. Refused in one sentence: a sheet or key file that cannot be read; a row id of the key file that the
sheet lacks, or one it holds twice or does not know; a concept or an answer text whose sha256 is not the key
file's for that row; a "stated?" cell that is empty or holds another value than yes, partly or no (read after
strip and lower case), with the row id; verdicts that the present matcher modules no longer give for a sampled
pair, or another shown text or stratum for its answer. It reports, for each of the six matchers, under two
readings of "partly" (counted as stated; counted as not stated), unweighted on the sample and weighted by
1 / inclusion probability:
  found among stated     the share of the stated concepts that the matcher finds
  not stated among found the share of the concepts the matcher finds that are not stated
each with its counts and a 95% interval; the same on the pairs that stem finds and loose does not; the counts of
the three labels; and every row where the stem verdict and the label differ (a row labelled partly is listed under
either verdict). The interval is a bootstrap over the sampled answers, so the concepts of one answer stay
together: in each of N_BOOT replicates, from numpy.random.RandomState(SEED + 1), each stratum of the draw gives
n - 1 of its n sampled answers with replacement, each draw weighted by n / (n - 1), so that the expected weight of
a sampled answer is 1 (with n - 1 draws the replicates' variance of a stratum mean is s^2 / n, the usual estimate;
with n draws it would be (n - 1) / n of it, a third too small at n = 3; a stratum with one sampled answer keeps
it), and the interval is the 2.5th to 97.5th percentile of the replicates in which the rate has a denominator.
It writes findings/recompute/S439_concept_label_analysis.json and .md.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True                         # a run leaves no cache file in the repository
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nltk  # noqa: E402
import numpy as np  # noqa: E402
import openpyxl  # noqa: E402
from openpyxl.formatting.rule import FormulaRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402
from openpyxl.writer.excel import ExcelWriter  # noqa: E402
import concept_match_loose as cml  # noqa: E402
import concept_match_stem as cms  # noqa: E402
import judged_ledger as jl  # noqa: E402
import phase3_common as p3  # noqa: E402

ME = "S439"
SCRIPT = "scripts/S439_concept_label_sheet.py"
SHEET = p3.ROOT / "response/concept_match_labels/concept_labels_v1.xlsx"
OUT_KEY = p3.RECOMPUTE / "S439_concept_label_key.json"
OUT_MD = p3.RECOMPUTE / "S439_concept_label_sheet.md"
OUT_AN_JSON = p3.RECOMPUTE / "S439_concept_label_analysis.json"
OUT_AN_MD = p3.RECOMPUTE / "S439_concept_label_analysis.md"
S382_MODULE = "S382_exp04_objective_v22"
S382_CSV = p3.RECOMPUTE / "S382_exp04_objective_v22.csv"

SEED = 20261013                                        # the day of D17; fixed before the first draw
N_SIM = 1_000_000                                      # simulated draws behind the inclusion probabilities
SIM_BATCH = 20_000
N_BOOT = 10_000                                        # bootstrap replicates of --analyze
KNOWN = {"answers": 516, "strategies": 6, "questions": 86, "pairs": 3426, "loose_found": 1774}   # D17's counts
PER_STRATEGY, PER_STRATUM = 6, 3
STEM_ADDS, NO_STEM_ADD = "stem_adds", "no_stem_add"
STRATA = (STEM_ADDS, NO_STEM_ADD)
MATCHERS = ("exact", "exact_o30", "loose", "loose_o30", "stem", "stem_o30")
MATCHER_TEXT = {
    "exact": "the concept's text is a substring of the answer, both in lower case",
    "exact_o30": "the deposited exp04 scorer finds the concept (rule 1 as O30 reads it)",
    "loose": "the loose matcher, scripts/concept_match_loose.py",
    "loose_o30": "loose, or the deposited exp04 scorer (O30)",
    "stem": "the candidate with word stems, scripts/concept_match_stem.py",
    "stem_o30": "stem, or the deposited exp04 scorer (O30)"}
LABELS = ("yes", "partly", "no")
READINGS = {"partly_as_stated": ("yes", "partly"), "partly_as_not_stated": ("yes",)}
READING_TEXT = {"partly_as_stated": "partly counted as stated", "partly_as_not_stated": "partly counted as not stated"}
SUBSETS = {"all_pairs": "every pair of the sample", "stem_adds_beyond_loose": "the pairs stem finds and loose does not"}

# the sheet
HOWTO, DATA = "How to label", "labels"
COLUMNS = ("row id", "answer id", "question", "concept", "expected answer (answer key)", "answer", "stated?", "comment")
MORE = "answer (continued {n})"                        # a further column for an answer longer than one cell
WIDTH = {"row id": 7, "answer id": 8, "question": 22, "concept": 26, "expected answer (answer key)": 60, "answer": 90,
         "stated?": 10, "comment": 22}
MERGED = ("question", "expected answer (answer key)", "answer")       # one cell per answer
ANSWER_CELL = 32_000                                   # a cell holds at most 32,767 characters
LINE_PT, MIN_ROW_PT, MAX_ROW_PT = 15.0, 30.0, 409.0    # a line of 11 pt text; the tallest row a workbook takes
ZOOM = 80
FIXED_DATE = datetime.datetime(2026, 10, 13)           # the workbook's created and modified properties
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
PROPERTIES = {"creator": SCRIPT.rsplit("/", 1)[1], "title": "Concept labels v1"}
PARTS = frozenset({"[Content_Types].xml", "_rels/.rels", "docProps/app.xml", "docProps/core.xml", "xl/workbook.xml",
                   "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/theme/theme1.xml", "xl/sharedStrings.xml",
                   "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"})
_UNSHOWABLE = re.compile("[^\t\n\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")
_ESCAPE = re.compile(r"_x[0-9A-Fa-f]{4}_")             # a workbook reads this as a character code

SENTENCES = (
    "Each row of the sheet \"labels\" pairs one answer with one concept of its question.",
    "A concept is a short phrase from the answer key: one point that a complete answer to the question should make.",
    "Read the answer, then choose in the column \"stated?\" whether the answer states the concept of that row.",
    "The wording does not matter and the meaning does: a synonym, a paraphrase or another word order counts, and the "
    "same words used with another meaning do not.",
    "Choose yes when the answer states the concept, partly when it states part of it or something close to it, and no "
    "when it does not.",
    "The column \"expected answer\" shows the answer key's full answer to the question, so that a concept can be read in "
    "its context.",
    "The six examples below come from answers that are not in the sheet.",
    "The sheet does not show what any automatic matcher decided, and it does not show which system wrote an answer.",
    "The answers are in random order, and a long answer may go beyond what its cell shows: select the cell to read all "
    "of it in the formula bar.",
    "About an hour was planned for the {rows} rows; the {answers} answers hold about {words} words, so it may take longer.",
    "The column \"comment\" is for anything you want to note and can stay empty; every row needs a label before the "
    "sheet is analysed.",
)
EXAMPLE_HEAD = ("label", "concept", "what the answer says")
# Written by hand on 13 October 2026 from exp04 answers: (label, question id, strategy, concept as the key writes
# it, a quotation of the answer). Gate B7 holds each to the key and to the deposit's text; examples() takes the
# first two per label that lie outside the sample.
EXAMPLES = (
    ("yes", "19_hpai_canada_FR1", "verified_pass", "Over 7 million birds", "more than seven million birds were culled in Canada"),
    ("yes", "01_sarek_FR1", "verified_pass", "about 1.4 TB",
     "approximately **1.4 TB** is allocated for BAM files, annotated VCF files, and CNV files"),
    ("yes", "05_multiqc_FR1", "single_pass", "aligners, processing tools and QC programs",
     "including aligners, processing tools, and quality control (QC) programs"),
    ("yes", "08_deseq2_FR1", "verified_pass", "shrunken LFC estimates",
     "using shrunken Log Fold Change (LFC) estimates improves the overlap of the top 100 genes"),
    ("partly", "16_ppr_ethiopia_FR1", "verified_pass", "9.6% (53 outbreaks)",
     "there were a total of 53 PPR outbreak reports identified in the Borena zone"),
    ("partly", "15_rabies_tanzania_TE3", "multi_hop", "97.5% pruning threshold", "combined with **pruning thresholds** (95% or 99%)"),
    ("partly", "11_asf_burkina_faso_TE3", "verified_pass", "MUSCLE as implemented in MEGA software version 7", "**Software:** Mega 7"),
    ("partly", "18_fmd_review_FR1", "multi_hop", "epithelial crypts of the oropharyngeal tonsils",
     "the **nasopharyngeal mucosa** in cattle and the **oropharyngeal tonsils** in pigs"),
    ("no", "02_snakemake_FR1", "verified_pass", "37 seconds",
     "there is no information regarding the specific time and memory requirements for the Snakemake scheduler to compute a "
     "graph of 90,000 jobs"),
    ("no", "20_lsd_review_TE3", "verified_pass", "approximately 96%",
     "the goat pox vaccine provides a cross-protection rate of **60% to 70%** against lumpy skin disease (LSD)"),
    ("no", "13_lsd_nepal_CO2", "single_pass", "dry cattle",
     "the cattle group most affected by the lumpy skin disease (LSD) outbreak in terms of mortality was **heifers**"),
    ("no", "17_brucellosis_ethiopia_FR1", "verified_pass", "Goro Baqaqsa", "but does not list the names of specific districts"),
)


def sha(data) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def need(ok: bool, message: str) -> None:
    if not ok:
        p3.refuse(ME, message)


def file_bytes(path: Path) -> bytes:
    """The file's bytes; a file that is missing or cannot be read is a refusal that names it."""
    try:
        return Path(path).read_bytes()
    except OSError as e:
        p3.refuse(ME, f"{p3.shown(Path(path))} cannot be read ({type(e).__name__}: {e.strerror or e})")


# ---- the population and the six verdicts ---------------------------------------------------------------------

def scorer() -> tuple:
    """(the deposited compute_concept_recall, the strategies in S382's order, the files it was lifted from). S382 is
    imported through phase3_common.published and its deposited_scorer() executes the deposited definitions."""
    s382 = p3.published(S382_MODULE)
    try:
        files = [Path(s382.SCORER), Path(s382.HARNESS_COMMON)]
        for f in files:
            p3.sha256_file(ME, f)                      # a missing file is a refusal that names it
        ns, _sources, _sink = s382.deposited_scorer()
        return ns["compute_concept_recall"], list(s382.CONFIGS), files
    except (OSError, SyntaxError, ValueError, KeyError, TypeError, AttributeError) as e:
        p3.refuse(ME, f"{S382_MODULE}.deposited_scorer() did not lift the deposited scorer ({type(e).__name__}: {e})")


def verdicts(answer: str, concepts: list, scorer_cr) -> list:
    """Per concept of the list, in its order: the six verdicts of MATCHERS as booleans, and under "stem_detail" what
    concept_recall_stem returns for the concept (found_by, content_words, matched_by, need)."""
    low = answer.lower()
    _, per_loose = cml.concept_recall_loose(answer, concepts, detail=True)
    _, per_stem = cms.concept_recall_stem(answer, concepts, detail=True)
    out = []
    for c, lo, st in zip(concepts, per_loose, per_stem):
        single = scorer_cr(answer, [c])
        need(lo["concept"] == c and st["concept"] == c and single in (0.0, 1.0),
             f"a matcher's detail does not follow the concept list, or the deposited scorer returned {single!r} on one concept")
        dep, loose, stem = single == 1.0, lo["found_by"] is not None, st["found_by"] is not None
        out.append({"exact": c.lower() in low, "exact_o30": dep, "loose": loose, "loose_o30": loose or dep,
                    "stem": stem, "stem_o30": stem or dep, "loose_found_by": lo["found_by"],
                    "stem_detail": {"found_by": st["found_by"], "content_words": list(st["content_words"]),
                                    "matched_by": dict(st["matched_by"]), "need": st["need"]}})
    return out


def population(scorer_cr, configs: list) -> dict:
    """The answerable exp04 answers in the order strategy (S382.CONFIGS), question id: {"answers": [{row, key,
    question_id, strategy, text, concepts, question, expected, verdicts}], "deposit": the one result file}.
    Refused, naming the file or the key: rows on more than one deposit file, a strategy outside configs, a question
    and strategy twice, an answer that is not text, a question whose record lacks the question, the expected answer
    or a list of concept texts that is not empty."""
    try:
        rows = [r for r in jl.load("exp04") if r.group == jl.ANSWERABLE]
    except ValueError as e:
        p3.refuse(ME, f"judged_ledger.load('exp04') gave no rows: {e}")
    records = jl._context().scope.records
    files = sorted({jl._paths().get((r.label, r.tag), "") for r in rows})
    need(len(files) == 1 and files[0] and all(r.config in configs for r in rows)
         and len({(r.config, r.question_id) for r in rows}) == len(rows),
         f"judged_ledger.load('exp04') holds {len(rows)} answerable rows on {len(files)} deposit files, where one file "
         f"and one row per question and strategy of {configs} are read")
    answers = []
    for r in sorted(rows, key=lambda r: (configs.index(r.config), r.question_id)):
        text = jl.s374_answer(jl._resolve(r.key, r.question_id, r.answer_chars)[5])
        rec = records.get(r.question_id) or {}
        concepts = rec.get("expected_concepts")
        need(isinstance(text, str) and isinstance(rec.get("question"), str) and isinstance(rec.get("expected_answer"), str)
             and isinstance(concepts, list) and bool(concepts) and all(isinstance(c, str) and c for c in concepts),
             f"{p3.shown(jl.S373.AS_V1)} or the deposit row of {r.key!r} lacks a text: the answer, the question, the "
             f"expected answer and a list of concepts that is not empty are read for {r.question_id}")
        answers.append({"row": r, "key": r.key, "question_id": r.question_id, "strategy": r.config, "text": text,
                        "concepts": list(concepts), "question": rec["question"], "expected": rec["expected_answer"],
                        "verdicts": verdicts(text, list(concepts), scorer_cr)})
    return {"answers": answers, "deposit": Path(files[0])}


def stratum_of(answer: dict) -> str:
    """stem_adds when at least one concept of the answer is found by stem and not by loose."""
    return STEM_ADDS if any(v["stem"] and not v["loose"] for v in answer["verdicts"]) else NO_STEM_ADD


def pattern_table(pairs: list) -> list:
    """Pairs by pattern of the six verdicts, the most frequent first: [{matcher: bool, ..., "pairs": n}]."""
    counts = Counter(tuple(v[m] for m in MATCHERS) for v in pairs)
    return [{**dict(zip(MATCHERS, pat)), "pairs": n} for pat, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]


# ---- the draw -------------------------------------------------------------------------------------------------

def quotas(sizes: list) -> list:
    """sizes holds, per strategy, the answers in stem_adds and in no_stem_add. The quota of a stratum is PER_STRATUM;
    a stratum with fewer answers gives what it holds and the other stratum of the strategy gives the rest of
    PER_STRATEGY, as far as it can."""
    out = []
    for a, b in zip(sizes[0::2], sizes[1::2]):
        qa, qb = min(PER_STRATUM, a), min(PER_STRATUM, b)
        qa += min(a - qa, PER_STRATUM - qb)
        qb += min(b - qb, PER_STRATEGY - qa - qb)
        out += [qa, qb]
    return out


def select(order: np.ndarray, stratum: np.ndarray, question: np.ndarray, quota: list) -> tuple:
    """order: one order of the answers per row. Going down a row, an answer is taken when its stratum still lacks
    one and no answer to its question was taken before in that row; a row is left as soon as every quota is full
    (looked at every 16th place; a full quota takes nothing more). A row with a quota still short at the end of
    its order goes down it a second time with what each stratum lacks moved to the other stratum of its strategy,
    and, if something is still lacking after that, a third time with it moved back and without the rule on
    questions; a quota is never above its stratum's size, so the third pass fills it. Returns (taken, a boolean per
    row and answer; moved, a boolean per row: the second pass was used; twice, per row: the third pass was used)."""
    n_rows, n = order.shape
    taken = np.zeros((n_rows, n), bool)
    lack = np.tile(np.asarray(quota, np.int64), (n_rows, 1))
    used = np.zeros((n_rows, int(question.max()) + 1), bool)
    moved, twice = np.zeros(n_rows, bool), np.zeros(n_rows, bool)
    for step in (1, 2, 3):
        active = np.flatnonzero(lack.any(axis=1))
        if not len(active):
            break
        if step > 1:                                   # to the other stratum of the strategy, and back
            lack[active] = lack[active].reshape(len(active), -1, 2)[:, :, ::-1].reshape(len(active), -1)
        moved[active], twice[active] = step > 1, step == 3
        for j in range(n):
            if j % 16 == 0:
                active = active[lack[active].any(axis=1)]
                if not len(active):
                    break
            a = order[active, j]
            h, q = stratum[a], question[a]
            ok = (lack[active, h] > 0) & ~taken[active, a]
            if step < 3:
                ok &= ~used[active, q]
            r, a, h, q = active[ok], a[ok], h[ok], q[ok]
            taken[r, a] = True
            lack[r, h] -= 1
            used[r, q] = True
    return taken, moved, twice


def draw(pop: dict, configs: list) -> dict:
    """The sample and the simulated inclusion probabilities (module docstring, THE DRAW and INCLUSION
    PROBABILITY)."""
    answers = pop["answers"]
    n = len(answers)
    questions = sorted({a["question_id"] for a in answers})
    cell = [(configs.index(a["strategy"]), STRATA.index(stratum_of(a))) for a in answers]
    stratum = np.array([2 * s + t for s, t in cell])
    question = np.array([questions.index(a["question_id"]) for a in answers])
    sizes = [int((stratum == h).sum()) for h in range(2 * len(configs))]
    quota = quotas(sizes)
    rng = random.Random(f"{ME} draw {SEED}")
    numbers = [rng.random() for _ in range(n)]
    order = np.array([sorted(range(n), key=numbers.__getitem__)])
    taken, moved, twice = select(order, stratum, question, quota)
    again = select(order, stratum, question, quota)[0]
    sample = [int(i) for i in np.flatnonzero(taken[0])]
    rs, counts, n_moved, n_twice = np.random.RandomState(SEED), np.zeros(n, np.int64), 0, 0
    for _ in range(N_SIM // SIM_BATCH):
        t, m, w = select(np.argsort(rs.random_sample((SIM_BATCH, n)), axis=1, kind="stable"), stratum, question, quota)
        counts += t.sum(axis=0)
        n_moved += int(m.sum())
        n_twice += int(w.sum())
    done = (N_SIM // SIM_BATCH) * SIM_BATCH
    pi = counts / done
    shuffle = random.Random(f"{ME} order {SEED}")
    places = [shuffle.random() for _ in sample]
    in_sheet = [i for _, i in sorted(zip(places, sample))]
    return {"sample": sample, "in_sheet_order": in_sheet, "stratum": [int(h) for h in stratum], "sizes": sizes,
            "quota": quota, "same_twice": bool((taken == again).all()), "moved": bool(moved[0]), "twice": bool(twice[0]),
            "pi": [float(x) for x in pi], "pi_se": [float(np.sqrt(x * (1 - x) / done)) for x in pi],
            "nominal": [quota[h] / sizes[h] if sizes[h] else 0.0 for h in stratum], "simulated": done,
            "simulated_moved": n_moved, "simulated_twice": n_twice, "never_taken": int((counts == 0).sum())}


# ---- the shown texts and the plan of the sheet ------------------------------------------------------------

def shown_text(text: str) -> tuple:
    """(the text as the sheet shows it, the characters replaced): a carriage return with its line feed, or alone,
    becomes a line feed; then every character a workbook cannot hold (outside tab, line feed and the ranges XML 1.0
    allows from U+0020) becomes U+FFFD."""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    return _UNSHOWABLE.sub("\ufffd", t), len(_UNSHOWABLE.findall(t)) + text.count("\r")


def chunks(text: str) -> list:
    """The text in pieces of at most ANSWER_CELL characters, each cut after the last line feed that fits (at
    ANSWER_CELL when the piece holds none); the pieces joined are the text."""
    out = []
    while len(text) > ANSWER_CELL:
        cut = text.rfind("\n", 0, ANSWER_CELL) + 1 or ANSWER_CELL
        out.append(text[:cut])
        text = text[cut:]
    return out + [text]


def lines(text: str, width: int) -> int:
    """An estimate of the lines a text takes in a wrapped column of this width: per line of the text, its length
    over the width, rounded up, and at least one."""
    return sum(max(1, -(-len(x) // width)) for x in text.split("\n"))


def examples(pop: dict, sample: list) -> tuple:
    """(the six examples for the sheet, problems). For each label the first two entries of EXAMPLES whose question
    has no answer in the sample; failing that, whose answer is not in the sample. An entry is a problem when its
    answer or concept is not in the population or its quotation is not in the deposit's text as shown, runs of
    white space read as one space."""
    by = {(a["question_id"], a["strategy"]): i for i, a in enumerate(pop["answers"])}
    in_sample = set(sample)
    sampled_q = {pop["answers"][i]["question_id"] for i in sample}
    problems, usable = [], {lab: [] for lab in LABELS}
    for label, qid, strategy, concept, says in EXAMPLES:
        i = by.get((qid, strategy))
        a = pop["answers"][i] if i is not None else None
        if label not in LABELS or a is None or concept not in a["concepts"] \
                or " ".join(says.split()) not in " ".join(shown_text(a["text"])[0].split()):
            problems.append(f"{qid} {strategy} {concept!r}")
            continue
        if i not in in_sample:
            whole = " ".join(says.split()) == " ".join(shown_text(a["text"])[0].split())
            usable[label].append({"label": label, "question_id": qid, "strategy": strategy, "concept": concept,
                                  "says": says if whole else f"... {says} ...", "question_in_sample": qid in sampled_q})
    picked = []
    for label in LABELS:
        first = sorted(usable[label], key=lambda e: e["question_in_sample"])[:2]      # stable: EXAMPLES' order kept
        if len(first) < 2:
            problems.append(f"{len(first)} of 2 examples for {label!r} lie outside the sample")
        picked += first
    return picked, problems


def plan(pop: dict, d: dict) -> dict:
    """What the sheet holds, built from the population and the draw: blocks (one per sampled answer, in the sheet's
    order), rows (one per pair) and the grid of the sheet "labels" (grid[r][c], None for an empty cell)."""
    blocks, rows = [], []
    for n, i in enumerate(d["in_sheet_order"], 1):
        a = pop["answers"][i]
        text, replaced = shown_text(a["text"])
        block = {"answer_id": f"A{n:02d}", "index": i, "answer": a, "text": text, "replaced": replaced,
                 "pieces": chunks(text), "first_row": len(rows) + 2, "rows": []}
        for k, c in enumerate(a["concepts"]):
            block["rows"].append(f"R{len(rows) + 1:03d}")
            rows.append({"row_id": block["rows"][-1], "block": block, "concept_index": k, "concept": c})
        blocks.append(block)
    more = max(len(b["pieces"]) for b in blocks) - 1
    at = COLUMNS.index("answer") + 1
    columns = list(COLUMNS[:at]) + [MORE.format(n=k + 2) for k in range(more)] + list(COLUMNS[at:])
    grid = [list(columns)]
    for r in rows:
        b = r["block"]
        top = r["row_id"] == b["rows"][0]
        line = {"row id": r["row_id"], "answer id": b["answer_id"], "concept": r["concept"]}
        if top:
            line.update({"question": b["answer"]["question"], "expected answer (answer key)": b["answer"]["expected"]})
            line.update({columns[at - 1 + k]: piece for k, piece in enumerate(b["pieces"])})
        grid.append([line.get(c) for c in columns])
    words = sum(len(b["text"].split()) for b in blocks)
    return {"blocks": blocks, "rows": rows, "columns": columns, "grid": grid, "words": words,
            "merged_columns": [c for c in columns if c in MERGED or c.startswith("answer (")]}


def howto(pl: dict, picked: list) -> list:
    """The grid of the sheet "How to label": the title, the sentences, the head of the examples and the examples."""
    fill = {"rows": len(pl["rows"]), "answers": len(pl["blocks"]), "words": f"{round(pl['words'], -2):,}"}
    out = [[HOWTO, None, None]] + [[s.format(**fill), None, None] for s in SENTENCES] + [[None, None, None]]
    return out + [list(EXAMPLE_HEAD)] + [[e["label"], e["concept"], e["says"]] for e in picked]


# ---- the workbook ---------------------------------------------------------------------------------------------

def workbook(pl: dict, how: list) -> bytes:
    """The workbook's bytes: the two sheets from their grids, every text cell stored as text, with the layout (widths,
    wrapped and top-aligned cells, merged cells per answer, row heights from lines(), a grey band on every second
    answer, the list on "stated?", a fill on its empty cells, the head row frozen, a filter). The archive is written
    once by openpyxl and then again with one fixed time stamp per part, stored without compression."""
    wrap = Alignment(wrap_text=True, vertical="top")
    edge = Side(style="thin", color="BFBFBF")
    box = Border(left=edge, right=edge, top=edge, bottom=edge)
    head, band = PatternFill("solid", fgColor="D9D9D9"), PatternFill("solid", fgColor="F3F3F3")

    def put(ws, r: int, c: int, value, bold: bool = False, fill=None):
        cell = ws.cell(row=r, column=c)
        if value is not None:
            cell.value = value
            cell.data_type = "s"                       # text, also when it starts with "=" or reads as an error code
        cell.alignment, cell.border = wrap, box
        if bold:
            cell.font = Font(bold=True)
        if fill is not None:
            cell.fill = fill
        return cell

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = HOWTO
    for letter, width in zip("ABC", (12, 45, 110)):
        ws.column_dimensions[letter].width = width
    n_text = 1 + len(SENTENCES)
    for r, line in enumerate(how, 1):
        table = r > n_text + 1
        for c, value in enumerate(line, 1):
            if table or c == 1:
                cell = put(ws, r, c, value, bold=r in (1, n_text + 2), fill=head if r == n_text + 2 else None)
                if not table:
                    cell.border = Border()
        if not table and line[0] is not None:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
            ws.row_dimensions[r].height = LINE_PT * lines(line[0], 150) + 6
        elif table:
            ws.row_dimensions[r].height = LINE_PT * max(lines(line[1] or "", 45), lines(line[2] or "", 110)) + 6
    ws["A1"].font = Font(bold=True, size=14)

    ds = wb.create_sheet(DATA)
    columns, n_rows = pl["columns"], len(pl["rows"])
    width = {c: WIDTH["answer" if c.startswith("answer (") else c] for c in columns}
    for c, name in enumerate(columns, 1):
        ds.column_dimensions[get_column_letter(c)].width = width[name]
        put(ds, 1, c, name, bold=True, fill=head)
    for b_no, b in enumerate(pl["blocks"]):
        fill = band if b_no % 2 else None
        first, last = b["first_row"], b["first_row"] + len(b["rows"]) - 1
        tall = LINE_PT * max(lines(pl["grid"][first - 1][c] or "", width[name]) for c, name in enumerate(columns)
                             if name in pl["merged_columns"]) + 6
        for r in range(first, last + 1):
            for c, name in enumerate(columns, 1):
                put(ds, r, c, pl["grid"][r - 1][c - 1], fill=fill)
            own = LINE_PT * lines(pl["grid"][r - 1][columns.index("concept")], width["concept"]) + 6
            ds.row_dimensions[r].height = min(MAX_ROW_PT, max(MIN_ROW_PT, own, tall / len(b["rows"])))
        if last > first:
            for name in pl["merged_columns"]:
                c = columns.index(name) + 1
                ds.merge_cells(start_row=first, start_column=c, end_row=last, end_column=c)
    stated = get_column_letter(columns.index("stated?") + 1)
    cells = f"{stated}2:{stated}{n_rows + 1}"
    dv = DataValidation(type="list", formula1='"' + ",".join(LABELS) + '"', allow_blank=True, showErrorMessage=True,
                        errorTitle="stated?", error="Choose one of: " + ", ".join(LABELS))
    dv.add(cells)
    ds.add_data_validation(dv)
    todo = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    ds.conditional_formatting.add(cells, FormulaRule(formula=[f"ISBLANK(${stated}2)"], fill=todo))
    ds.freeze_panes = "A2"
    ds.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{n_rows + 1}"
    ds.sheet_view.zoomScale = ZOOM
    wb.active = 0
    wb.properties.creator, wb.properties.title = PROPERTIES["creator"], PROPERTIES["title"]
    wb.properties.created = wb.properties.modified = FIXED_DATE

    first_write = io.BytesIO()
    ExcelWriter(wb, zipfile.ZipFile(first_write, "w", zipfile.ZIP_DEFLATED)).save()
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(first_write.getvalue())) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as dst:
        for name in src.namelist():
            dst.writestr(zipfile.ZipInfo(name, date_time=ZIP_DATE), src.read(name))
    return out.getvalue()


def open_workbook(raw: bytes, name: str):
    """The workbook of these bytes; a file openpyxl cannot read is a refusal that names it."""
    try:
        return openpyxl.load_workbook(io.BytesIO(raw))
    except Exception as e:                             # openpyxl raises many types on a file that is no workbook
        p3.refuse(ME, f"{name} cannot be read as a workbook ({type(e).__name__}: {str(e)[:120]})")


def grid_of(ws) -> list:
    """Every cell of a sheet, from A1 to its last row and column, None for an empty cell."""
    return [[ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)] for r in range(1, ws.max_row + 1)]


def read_back(raw: bytes, pl: dict, how: list) -> list:
    """What gates B9 and B10 test, read from the workbook's bytes: [(gate, what was tested, whether it holds)]."""
    wb = open_workbook(raw, "the workbook built in memory")
    names = wb.sheetnames
    if names != [HOWTO, DATA]:
        return [("B9", f"the sheets are {names}", False), ("B10", "not tested", False)]
    ws, ds = wb[HOWTO], wb[DATA]
    n_rows, columns = len(pl["rows"]), pl["columns"]
    got = grid_of(ds)
    width3 = [line + [None] * (3 - len(line)) for line in grid_of(ws)]
    stated, comment = columns.index("stated?"), columns.index("comment")
    merged = {str(m) for m in ds.merged_cells.ranges}
    want_merged = {f"{get_column_letter(columns.index(c) + 1)}{b['first_row']}:"
                   f"{get_column_letter(columns.index(c) + 1)}{b['first_row'] + len(b['rows']) - 1}"
                   for b in pl["blocks"] if len(b["rows"]) > 1 for c in pl["merged_columns"]}
    lists = [(str(v.sqref), v.type, v.formula1) for v in ds.data_validations.dataValidation]
    col = get_column_letter(stated + 1)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    book = parts.get("xl/workbook.xml", b"").decode("utf-8", "replace")
    defined = re.findall(r"<definedName\b[^>]*\bname=\"([^\"]*)\"", book)
    texts = [v for g in (pl["grid"], how) for line in g for v in line if isinstance(v, str)]
    tokens = sorted({x for b in pl["blocks"] for x in (b["answer"]["strategy"], b["answer"]["row"].tag)} | set(STRATA)
                    | set(MATCHERS[1::2]) | {"found_by", "inclusion"})
    in_archive = {t: sum(p.count(t.encode("utf-8")) for p in parts.values()) for t in tokens}
    in_texts = {t: sum(v.count(t) for v in texts) for t in tokens}
    props = wb.properties
    return [
        ("B9", f"the sheet \"{DATA}\" holds {len(got)} rows and {ds.max_column} columns (planned {n_rows + 1} and {len(columns)})",
         len(got) == n_rows + 1 and ds.max_column == len(columns)),
        ("B9", "every cell equals the plan", got == pl["grid"]),
        ("B9", "every text cell is stored as text",
         all(ds.cell(row=r, column=c).data_type == "s" for r in range(1, len(got) + 1) for c in range(1, ds.max_column + 1)
             if got[r - 1][c - 1] is not None)),
        ("B9", "the label and comment cells are empty", all(line[stated] is None and line[comment] is None for line in got[1:])),
        ("B9", "the merged cells are the planned ones", merged == want_merged),
        ("B9", "one list of yes, partly, no on the column stated?",
         lists == [(f"{col}2:{col}{n_rows + 1}", "list", '"' + ",".join(LABELS) + '"')]),
        ("B9", f"the sheet \"{HOWTO}\" equals its plan", width3 == how and ws.max_column <= 3),
        ("B10", f"the archive's {len(parts)} parts are the two sheets and parts of the expected kinds",
         set(parts) <= PARTS and {"xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"} <= set(parts)),
        ("B10", f"no defined name but the filter's ({', '.join(defined) or 'none'})", all(n == "_xlnm._FilterDatabase" for n in defined)),
        ("B10", "both sheets visible and no cell comment",
         all(x.sheet_state == "visible" for x in (ws, ds))
         and not any(cell.comment for x in (ws, ds) for line in x.iter_rows() for cell in line)),
        ("B10", "the document properties are the fixed ones",
         (props.creator, props.title, props.created, props.modified, props.lastModifiedBy, props.description, props.subject,
          props.keywords, props.category) == (PROPERTIES["creator"], PROPERTIES["title"], FIXED_DATE, FIXED_DATE, None, None,
                                              None, None, None)),
        ("B10", f"each of {len(tokens)} names of the key file (the strategies, the deposit file of the ledger keys, the strata, "
                f"the O30 verdicts, found_by, inclusion) occurs in the archive as often as in the shown texts "
                f"({sum(in_texts.values())} occurrences in all)", in_archive == in_texts)]


def labels_on_disk(path: Path) -> int:
    """The cells that are not empty in the columns stated? and comment of the sheet on disk; 0 when no file is
    there. A file that is there and cannot be read as this script's sheet is a refusal: it is not replaced."""
    if not path.exists():
        return 0
    wb = open_workbook(file_bytes(path), p3.shown(path))
    if DATA not in wb.sheetnames:
        p3.refuse(ME, f"{p3.shown(path)} holds no sheet \"{DATA}\", so it is not this script's sheet and is not replaced")
    got = grid_of(wb[DATA])
    at = [c for c, name in enumerate(got[0] if got else []) if name in ("stated?", "comment")]
    need(len(at) == 2, f"{p3.shown(path)} lacks the columns stated? and comment, so it is not this script's sheet and is not replaced")
    return sum(line[c] not in (None, "") for line in got[1:] for c in at)


def write_all(sheet_raw: bytes, outputs: dict) -> None:
    """The sheet by this script's own write (response/ is outside what phase3_common.write_outputs takes): the
    folder is made when it is absent, the bytes go to <name>.tmp, are read back, the sheet that is there is kept as
    <name>.old.tmp and <name>.tmp is renamed onto the target. Then the outputs under findings/recompute/ go through
    write_outputs; when that refuses, the earlier sheet is put back (a sheet put where there was none is removed)."""
    tmp, old = SHEET.with_name(SHEET.name + ".tmp"), SHEET.with_name(SHEET.name + ".old.tmp")
    had = False
    try:
        SHEET.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(sheet_raw)
        if tmp.read_bytes() != sheet_raw:
            raise OSError("the bytes read back are not the bytes written")
        old.unlink(missing_ok=True)
        if SHEET.is_file():
            os.link(SHEET, old)
            had = True
        os.replace(tmp, SHEET)
    except OSError as e:
        for t in (tmp, old):
            t.unlink(missing_ok=True)
        p3.refuse(ME, f"{p3.shown(SHEET)} could not be written ({type(e).__name__}: {e}); nothing is written")
    try:
        p3.write_outputs(ME, outputs)
    except BaseException:
        if had:
            os.replace(old, SHEET)
        else:
            SHEET.unlink(missing_ok=True)
        raise
    finally:
        old.unlink(missing_ok=True)


# ---- --build --------------------------------------------------------------------------------------------------

def pc(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def csv_gate(pop: dict) -> tuple:
    """Gate B4's counts: (answers whose exact_o30 share is concept_recall_v22 of S382's csv, answers whose loose_o30
    share is its concept_recall_loose_v22, whether the csv records the present key and answers file)."""
    name = p3.shown(S382_CSV)
    comments, rows = p3.read_csv_rows(ME, S382_CSV, ("question_id", "config", "group", "n_concepts_v22",
                                                     "concept_recall_v22", "concept_recall_loose_v22"))
    try:
        head = json.loads(comments[0][2:]) if comments and comments[0].startswith("# {") else {}
        cells = {(r["question_id"], r["config"]): (int(r["n_concepts_v22"]), float(r["concept_recall_v22"]),
                                                  float(r["concept_recall_loose_v22"]))
                 for r in rows if r["group"] == jl.ANSWERABLE}
    except (ValueError, RecursionError) as e:
        p3.refuse(ME, f"{name} is not S382's file: its first line or a cell cannot be read ({type(e).__name__}: {e})")
    answers = {(a["question_id"], a["strategy"]): a for a in pop["answers"]}
    need(set(cells) == set(answers), f"{name} holds {len(cells)} answerable rows, {len(set(cells) & set(answers))} of them "
                                     f"among the {len(answers)} answers of the population")
    ok = [0, 0]
    for k, a in answers.items():
        n = len(a["concepts"])
        for i, m in enumerate(("exact_o30", "loose_o30")):
            ok[i] += n == cells[k][0] and round(sum(v[m] for v in a["verdicts"]) / n, 4) == cells[k][1 + i]
    same = isinstance(head, dict) and head.get("key_sha256") == jl._context().scope.sha256 \
        and head.get("answers_sha256") == p3.sha256_file(ME, pop["deposit"])
    return ok[0], ok[1], same


def build() -> int:
    filled = labels_on_disk(SHEET)
    need(filled == 0, f"{p3.shown(SHEET)} holds {filled} labels or comments, which a build would replace; move the file "
                      "away to build again")
    g = p3.Gates(ME)
    try:
        fails = cms.spec_failures() + cml.spec_failures()
    except Exception as e:                             # whatever a matcher's own checks raise
        p3.refuse(ME, f"the matchers' spec_failures() could not run ({type(e).__name__}: {e})")
    g.gate("B1", not fails, f"{len(cms.SPEC_CASES)} cases of concept_match_stem and {len(cml.SPEC_CASES)} of "
                            "concept_match_loose hold" if not fails else f"{len(fails)} cases fail, the first: {fails[0]}")
    scorer_cr, configs, lifted = scorer()
    pop = population(scorer_cr, configs)
    answers = pop["answers"]
    pairs = [v for a in answers for v in a["verdicts"]]
    found = {m: sum(v[m] for v in pairs) for m in MATCHERS}
    got = {"answers": len(answers), "strategies": len({a["strategy"] for a in answers}),
           "questions": len({a["question_id"] for a in answers}), "pairs": len(pairs)}
    g.gate("B2", got == {k: KNOWN[k] for k in got} and got["answers"] == got["strategies"] * got["questions"],
           f"{got['answers']} answers ({got['strategies']} strategies x {got['questions']} questions) and {got['pairs']:,} pairs, "
           f"from {p3.shown(pop['deposit'])}")
    nested = sum((v["exact"] == (v["loose_found_by"] == "exact")) and (not v["exact"] or (v["exact_o30"] and v["loose"]))
                 and (not v["loose"] or v["stem"]) for v in pairs)
    g.gate("B3", found["loose"] == KNOWN["loose_found"] and nested == len(pairs),
           f"loose finds {found['loose']:,} pairs with the plain exact rule as rule 1 (D17 gives {KNOWN['loose_found']:,}); exact "
           f"is the loose module's found_by exact, what exact finds exact_o30 and loose find, and what loose finds stem finds, "
           f"on {nested:,} of {len(pairs):,} pairs")
    ok_dep, ok_loose, same = csv_gate(pop)
    g.gate("B4", ok_dep == ok_loose == len(answers) and same,
           f"{p3.shown(S382_CSV)}: concept_recall_v22 is exact_o30's found share on {ok_dep} of {len(answers)} answers and "
           f"concept_recall_loose_v22 loose_o30's on {ok_loose}; it records the present key and answers file: {same}")

    d = draw(pop, configs)
    sample = d["sample"]
    per_strategy = Counter(answers[i]["strategy"] for i in sample)
    per_stratum = Counter(d["stratum"][i] for i in sample)
    n_questions = len({answers[i]["question_id"] for i in sample})
    at_quota = all(per_stratum[h] == q for h, q in enumerate(d["quota"]))
    g.gate("B5", len(sample) == PER_STRATEGY * len(configs) and all(per_strategy[c] == PER_STRATEGY for c in configs)
           and (at_quota or d["moved"]) and d["same_twice"] and (n_questions == len(sample) or d["twice"]),
           f"{len(sample)} answers, {PER_STRATEGY} per strategy, "
           + (f"each stratum at its quota ({d['quota']})" if at_quota else "a stratum filled from the other of its strategy "
              f"({[per_stratum[h] for h in range(len(d['quota']))]})")
           + f", the same answers when select() is run again; {n_questions} questions, so "
           + ("no question is there twice" if n_questions == len(sample) else "a question is there twice"))
    g.gate("B6", d["never_taken"] == 0 and abs(sum(d["pi"]) - len(sample)) < 1e-6,
           f"{d['simulated']:,} simulated draws: {len(answers) - d['never_taken']} of {len(answers)} answers taken at least "
           f"once, the inclusion probabilities sum to {sum(d['pi']):.6f}; {d['simulated_moved']} draws moved a quota to the "
           f"other stratum and {d['simulated_twice']} dropped the rule on questions")
    picked, problems = examples(pop, sample)
    g.gate("B7", not problems and len(picked) == 2 * len(LABELS),
           f"{len(picked)} examples from {len(EXAMPLES)} entries, {sum(not e['question_in_sample'] for e in picked)} on a "
           "question with no answer in the sample, each concept in the key and each quotation in its answer's text"
           if not problems else f"{len(problems)} problems, the first: {problems[0]}")

    pl = plan(pop, d)
    how = howto(pl, picked)
    once = all(sorted(r["concept_index"] for r in pl["rows"] if r["block"] is b) == list(range(len(b["answer"]["concepts"])))
               for b in pl["blocks"])
    texts = [v for line in pl["grid"] + how for v in line if isinstance(v, str)]
    unsafe = sum(bool(_UNSHOWABLE.search(t) or _ESCAPE.search(t) or "\r" in t or len(t) > ANSWER_CELL) for t in texts)
    g.gate("B8", once and unsafe == 0 and all("".join(b["pieces"]) == b["text"] for b in pl["blocks"])
           and len(SENTENCES) <= 12,
           f"{len(pl['rows'])} rows: each of the {len(pl['blocks'])} sampled answers has each of its concepts on one row; "
           f"{unsafe} of {len(texts)} texts hold a character or an escape sequence a workbook would change or are longer "
           f"than a cell; {sum(b['replaced'] > 0 for b in pl['blocks'])} answers are shown with replaced characters; "
           f"{len(SENTENCES)} sentences")
    raw = workbook(pl, how)
    tested = read_back(raw, pl, how)
    for gate, what in (("B9", f"the workbook's {len(raw):,} bytes read back with openpyxl"), ("B10", "blindness")):
        mine = [(text, ok) for name, text, ok in tested if name == gate]
        g.gate(gate, all(ok for _, ok in mine), what + ": " + "; ".join(f"{text} {ok}" for text, ok in mine))
    gates = g.finish()

    w = {i: 1 / d["pi"][i] for i in sample}
    cell_name = lambda h: f"{configs[h // 2]} / {STRATA[h % 2]}"  # noqa: E731
    sample_pairs = [v for i in sample for v in answers[i]["verdicts"]]
    by_matcher = {m: {"population_found": found[m], "population_share": found[m] / len(pairs),
                      "sample_found": sum(v[m] for v in sample_pairs), "sample_share": sum(v[m] for v in sample_pairs) / len(sample_pairs),
                      "weighted_share": sum(w[i] * sum(v[m] for v in answers[i]["verdicts"]) for i in sample)
                      / sum(w[i] * len(answers[i]["verdicts"]) for i in sample)} for m in MATCHERS}
    strata = [{"strategy": configs[h // 2], "stratum": STRATA[h % 2], "answers": d["sizes"][h], "quota": d["quota"][h],
               "sampled": per_stratum[h], "quota_over_answers": d["quota"][h] / d["sizes"][h] if d["sizes"][h] else None,
               "simulated_probability_min": min((d["pi"][i] for i in range(len(answers)) if d["stratum"][i] == h), default=None),
               "simulated_probability_max": max((d["pi"][i] for i in range(len(answers)) if d["stratum"][i] == h), default=None)}
              for h in range(2 * len(configs))]
    doc_answers, doc_rows = [], {}
    for b in pl["blocks"]:
        i, a = b["index"], b["answer"]
        base = {"answer_id": b["answer_id"], "ledger_key": a["key"], "question_id": a["question_id"], "strategy": a["strategy"],
                "stratum": stratum_of(a), "inclusion_probability": d["pi"][i], "inclusion_probability_se": d["pi_se"][i],
                "quota_over_stratum_size": d["nominal"][i], "answer_sha256": sha(b["text"])}
        doc_answers.append({**base, "deposit_answer_sha256": sha(a["text"]), "characters_replaced": b["replaced"],
                            "answer_chars": len(a["text"]), "answer_words": len(b["text"].split()), "concepts": len(a["concepts"]),
                            "sheet_rows": [b["first_row"], b["first_row"] + len(b["rows"]) - 1]})
        for k, rid in enumerate(b["rows"]):
            v = a["verdicts"][k]
            doc_rows[rid] = {**base, "concept_index": k, "concept_sha256": sha(a["concepts"][k]),
                             "verdicts": {m: v[m] for m in MATCHERS}, "stem_detail": v["stem_detail"]}
    design = {"seed": SEED, "draw_stream": f"random.Random('{ME} draw {SEED}')", "order_stream": f"random.Random('{ME} order {SEED}')",
              "simulation_stream": f"numpy.random.RandomState({SEED})", "simulated_draws": d["simulated"],
              "simulated_draws_that_moved_a_quota": d["simulated_moved"],
              "simulated_draws_without_the_rule_on_questions": d["simulated_twice"], "per_strategy": PER_STRATEGY,
              "per_stratum": PER_STRATUM, "strata": {STEM_ADDS: "at least one concept that stem finds and loose does not",
                                                     NO_STEM_ADD: "every other answer"},
              "no_question_twice": n_questions == len(sample), "quota_moved_in_the_draw": d["moved"],
              "rule_on_questions_dropped_in_the_draw": d["twice"],
              "strata_not_at_three": [cell_name(h) for h in range(len(d["quota"])) if per_stratum[h] != PER_STRATUM]}
    extra = {"gates": gates, "seed": SEED,
             "matcher_modules": {p3.shown(Path(m.__file__)): p3.sha256_file(ME, m.__file__) for m in (cml, cms)},
             "answers_file": {"file": p3.shown(pop["deposit"]), "sha256": p3.sha256_file(ME, pop["deposit"])},
             "sheet": {"file": p3.shown(SHEET), "sha256": sha(raw), "bytes": len(raw)},
             "libraries": {"nltk": nltk.__version__, "numpy": np.__version__, "openpyxl": openpyxl.__version__}}
    prov = p3.provenance(__file__, f"uv run python {SCRIPT} --build",
                         [("exp04", jl.MAIN_JUDGE), pop["deposit"], *lifted, Path(jl.MANIFEST)], extra)
    added = [v for v in pairs if v["stem"] and not v["loose"]]
    doc = {"provenance": prov, "design": design, "matchers": MATCHER_TEXT,
           "population": {"answers": len(answers), "pairs": len(pairs), "found": found, "pairs_by_verdict_pattern": pattern_table(pairs),
                          "stem_finds_loose_does_not": {"pairs": len(added), "of_them_exact_o30_finds": sum(v["exact_o30"] for v in added),
                                                        "answers": sum(stratum_of(a) == STEM_ADDS for a in answers)}},
           "sample": {"answers": len(sample), "pairs": len(sample_pairs), "questions": n_questions, "strata": strata,
                      "found": by_matcher, "pairs_by_verdict_pattern": pattern_table(sample_pairs),
                      "stem_finds_loose_does_not": sum(v["stem"] and not v["loose"] for v in sample_pairs),
                      "sum_of_weights": sum(w.values()), "weighted_pairs": sum(w[i] * len(answers[i]["verdicts"]) for i in sample),
                      "answer_words": pl["words"], "expected_answer_words": sum(len(b["answer"]["expected"].split()) for b in pl["blocks"]),
                      "answers_longer_than_their_cell_shows": sum(
                          LINE_PT * lines(b["text"], WIDTH["answer"]) + 6 > MAX_ROW_PT * len(b["rows"]) for b in pl["blocks"])},
           "sheet": {"columns": pl["columns"], "rows": len(pl["rows"]), "labels": list(LABELS),
                     "examples": [{k: e[k] for k in ("label", "question_id", "strategy", "concept", "question_in_sample")} for e in picked]},
           "answers": doc_answers, "rows": doc_rows}
    write_all(raw, {OUT_KEY: json.dumps(doc, indent=1, ensure_ascii=False) + "\n", OUT_MD: build_report(doc)})
    print(f"{ME} --build: wrote {p3.shown(SHEET)} ({len(pl['rows'])} rows, sha256 {sha(raw)[:12]}), {p3.shown(OUT_KEY)} and "
          f"{p3.shown(OUT_MD)}")
    return 0


def build_report(doc: dict) -> str:
    pop, s, des, prov = doc["population"], doc["sample"], doc["design"], doc["provenance"]
    mark = lambda b: "found" if b else "-"  # noqa: E731
    L = ["# S439: the label sheet for the concept matchers", "",
         f"Written by `{SCRIPT} --build`. The sheet is `{prov['sheet']['file']}` (sha256 `{prov['sheet']['sha256'][:12]}`), "
         f"the key file `{p3.shown(OUT_KEY)}`. The sheet shows no verdict, stratum or strategy; the key file holds them. "
         "The provenance is in the key file.", "",
         "## What is labelled", "",
         f"The population is the {pop['answers']} answerable exp04 answers and every concept the answer key gives their "
         f"question: {pop['pairs']:,} pairs of one answer and one concept. {s['answers']} answers are sampled, {des['per_strategy']} "
         f"per strategy, and every concept of a sampled answer is a row: {s['pairs']} rows. Each row gets one label, yes, "
         "partly or no: does the answer state the concept.", "",
         "## The six matchers, and the pairs each finds in the population", "",
         "| matcher | rule | pairs found | share |", "|---|---|---:|---:|"]
    L += [f"| {m} | {MATCHER_TEXT[m]} | {pop['found'][m]:,} | {pc(pop['found'][m] / pop['pairs'])} |" for m in MATCHERS]
    add = pop["stem_finds_loose_does_not"]
    L += ["", f"stem finds {add['pairs']} pairs that loose does not, in {add['answers']} answers; exact_o30 finds "
              f"{add['of_them_exact_o30_finds']} of them.", "",
          "## Pairs by pattern of the six verdicts", "",
          "| " + " | ".join(MATCHERS) + " | pairs, population | pairs, sample |", "|" + "---|" * len(MATCHERS) + "---:|---:|"]
    in_sample = {tuple(p[m] for m in MATCHERS): p["pairs"] for p in s["pairs_by_verdict_pattern"]}
    L += ["| " + " | ".join(mark(p[m]) for m in MATCHERS) + f" | {p['pairs']:,} | {in_sample.get(tuple(p[m] for m in MATCHERS), 0)} |"
          for p in pop["pairs_by_verdict_pattern"]]
    L += ["", "## The draw", "",
          f"Each strategy's answers are split in two strata: `{STEM_ADDS}`, the answers with at least one concept that stem "
          f"finds and loose does not, and `{NO_STEM_ADD}`, the others. The quota is {des['per_stratum']} answers per stratum. "
          f"The {pop['answers']} answers are put in a random order (seed {des['seed']}, stream `{des['draw_stream']}`); going "
          "down the order, an answer is taken when its stratum still lacks one and no answer to the same question was "
          "taken before. "
          + (f"No question is in the sample twice: {s['questions']} questions for {s['answers']} answers. "
             if des["no_question_twice"] else f"A question is in the sample twice: {s['questions']} questions for {s['answers']} answers. ")
          + ("Strata that do not hold three sampled answers, the other stratum of the strategy filling the six: "
             + ", ".join(des["strata_not_at_three"]) + "." if des["strata_not_at_three"]
             else "Every stratum gave its three answers, so none was filled from the other."),
          "", "| strategy | stratum | answers | sampled | quota / answers | simulated inclusion probability, lowest to highest |",
          "|---|---|---:|---:|---:|---:|"]
    L += [f"| {x['strategy']} | {x['stratum']} | {x['answers']} | {x['sampled']} | " + (
        f"{x['quota_over_answers']:.4f} | {x['simulated_probability_min']:.4f} to {x['simulated_probability_max']:.4f} |"
        if x["answers"] else "n/a | n/a |") for x in s["strata"]]
    se = max(a["inclusion_probability_se"] / a["inclusion_probability"] for a in doc["answers"])
    L += ["", "## Inclusion probabilities and weights", "",
          "Because no question is taken twice, the chance of an answer depends on how many other answers share its "
          f"question, so it differs between answers of one stratum (last column above). It is estimated by running the same "
          f"draw {des['simulated_draws']:,} times on other random orders (`{des['simulation_stream']}`) and counting how often "
          f"each answer is taken; {des['simulated_draws_that_moved_a_quota']} of those draws could not fill a stratum "
          "without taking a question twice and took the answer from the other stratum of the strategy, and "
          f"{des['simulated_draws_without_the_rule_on_questions']} took a question twice. The largest "
          f"Monte Carlo standard error among the sampled answers is {100 * se:.2f}% of the probability. The weight of a "
          f"sampled answer is 1 over its probability; the {s['answers']} weights sum to {s['sum_of_weights']:.1f} (the "
          f"population holds {pop['answers']} answers), and weighted by them the sample holds {s['weighted_pairs']:,.0f} pairs "
          f"(the population holds {pop['pairs']:,}).", "",
          "| matcher | found, population | found, sample | found, sample weighted |", "|---|---:|---:|---:|"]
    L += [f"| {m} | {pc(x['population_share'])} | {x['sample_found']} of {s['pairs']} ({pc(x['sample_share'])}) | {pc(x['weighted_share'])} |"
          for m, x in s["found"].items()]
    L += ["", f"The sample holds {s['stem_finds_loose_does_not']} of the {add['pairs']} pairs that stem finds and loose does not.", "",
          "## The sheet", "",
          f"Sheet \"{HOWTO}\": {len(SENTENCES)} sentences and six examples, two per label, from answers outside the sample. "
          f"Sheet \"{DATA}\": {doc['sheet']['rows']} rows, the columns " + ", ".join(doc["sheet"]["columns"]) + ". The rows of one "
          "answer follow each other in the key's order of the concepts; the answers are in a random order of their own "
          f"(`{des['order_stream']}`). The sampled answers hold {s['answer_words']:,} words and the expected answers shown "
          f"beside them {s['expected_answer_words']:,}; by this script's estimate of lines, "
          f"{s['answers_longer_than_their_cell_shows']} answers are longer than their cell shows at once. "
          f"{sum(a['characters_replaced'] > 0 for a in doc['answers'])} answers are shown with "
          "characters replaced by U+FFFD, since a workbook cannot hold them; the matchers read the deposit's text.", "",
          "## Gates", "", "| gate | result | what was tested |", "|---|---|---|"]
    L += [f"| {x['name']} | {'ok' if x['ok'] else 'FAIL'} | {x['message']} |" for x in prov["gates"]]
    L += ["", "## After the labels", "",
          f"`uv run python {SCRIPT} --analyze` reads the filled sheet and this key file and writes "
          f"`{p3.shown(OUT_AN_JSON)}` and `.md`: per matcher, the share of the stated concepts it finds and the share of the "
          "concepts it finds that are not stated, with partly counted either way, unweighted and weighted.", ""]
    return "\n".join(L)


# ---- --analyze ------------------------------------------------------------------------------------------------

def canon(text: str) -> str:
    """A cell's text as it is hashed: a carriage return, which a spreadsheet program may put before a line feed as
    the character or as "_x000D_", is dropped."""
    return text.replace("_x000D_", "").replace("\r", "")


def read_labels(path: Path, key: dict) -> dict:
    """row id -> {"label", "comment", "concept"} from the filled sheet, each row held to the key file (module
    docstring, --analyze)."""
    name = p3.shown(path)
    wb = open_workbook(file_bytes(path), name)
    need(DATA in wb.sheetnames, f"{name} holds no sheet \"{DATA}\"")
    got = grid_of(wb[DATA])
    try:
        rows, columns = key["rows"], list(key["sheet"]["columns"])
        answers = {a["answer_id"]: a for a in key["answers"]}
        need(isinstance(rows, dict) and bool(rows) and all(r["answer_id"] in answers for r in rows.values()),
             f"{p3.shown(OUT_KEY)} lists no rows, or a row of an answer it does not list")
    except (KeyError, TypeError, AttributeError) as e:
        p3.refuse(ME, f"{p3.shown(OUT_KEY)} is not this script's key file ({type(e).__name__}: {e})")
    need(bool(got) and [str(v) if v is not None else None for v in got[0][:len(columns)]] == columns,
         f"{name}: the first row of the sheet \"{DATA}\" is not the columns {columns}")
    at = {c: i for i, c in enumerate(columns)}
    text_at = [i for i, c in enumerate(columns) if c == "answer" or c.startswith("answer (")]
    lines_by_id, texts = {}, {}
    for n, line in enumerate(got[1:], 2):
        line = list(line) + [None] * (len(columns) - len(line))
        rid = line[at["row id"]]
        if rid in (None, ""):
            continue
        rid = str(rid).strip()
        need(rid in rows, f"{name}, row {n} of the sheet holds the row id {rid!r}, which the key file does not list")
        need(rid not in lines_by_id, f"{name} holds the row id {rid} twice")
        lines_by_id[rid] = line
        text = "".join(str(line[i]) for i in text_at if line[i] is not None)
        if text:
            texts.setdefault(str(line[at["answer id"]]).strip(), set()).add(sha(canon(text)))
    missing = [rid for rid in rows if rid not in lines_by_id]
    need(not missing, f"{name} lacks {len(missing)} of the key file's {len(rows)} row ids, the first {missing[0] if missing else ''}")
    out, empty, other = {}, [], []
    for rid, rec in rows.items():
        line = lines_by_id[rid]
        aid = str(line[at["answer id"]]).strip()
        concept = "" if line[at["concept"]] is None else str(line[at["concept"]])
        off = [what for what, same in (("answer id", aid == rec["answer_id"]),
                                       ("concept", sha(canon(concept)) == rec["concept_sha256"]),
                                       ("answer text", texts.get(aid) == {rec["answer_sha256"]})) if not same]
        need(not off, f"{name}, row id {rid}: the {' and the '.join(off)} of this row is not what the key file records for "
                      "it (compared by sha256), so the sheet is not the one the key file was written with")
        raw = line[at["stated?"]]
        label = str(raw).strip().lower() if raw is not None else ""
        if not label:
            empty.append(rid)
        elif label not in LABELS:
            other.append((rid, raw))
        comment = line[at["comment"]]
        out[rid] = {"label": label, "comment": "" if comment is None else str(comment), "concept": concept}
    need(not empty, f"{name}: the \"stated?\" cell of row id {empty[0] if empty else ''} is empty ({len(empty)} of {len(rows)} "
                    "rows are without a label)")
    need(not other, f"{name}: the \"stated?\" cell of row id {other[0][0] if other else ''} holds {other[0][1] if other else ''!r}, "
                    f"which is not one of {', '.join(LABELS)} ({len(other)} such rows)")
    return out


def rate(num: np.ndarray, den: np.ndarray, w: np.ndarray, reps: np.ndarray) -> dict:
    """num and den: per sampled answer, the pairs in the numerator and in the denominator. The rate with weights w,
    its counts, and the 2.5th and 97.5th percentile of the rate over the replicates that have a denominator."""
    d = float(w @ den)
    r_den = (reps * w) @ den
    ok = r_den > 0
    values = ((reps * w) @ num)[ok] / r_den[ok]
    lo, hi = (float(x) for x in np.percentile(values, [2.5, 97.5])) if d > 0 and ok.any() else (None, None)
    return {"share": float(w @ num) / d if d > 0 else None, "numerator": int(num.sum()), "denominator": int(den.sum()),
            "weighted_numerator": float(w @ num), "weighted_denominator": d, "interval_95": [lo, hi],
            "replicates_with_a_denominator": int(ok.sum())}


def analyze(sheet: Path) -> int:
    g = p3.Gates(ME)
    key = p3.read_json(ME, OUT_KEY)
    labels = read_labels(sheet, key)
    g.gate("A1", True, f"{p3.shown(sheet)}: the {len(labels)} row ids of the key file are there once each, with the concept "
                       "and the answer text the key file records (sha256 per row), and every row has a label")
    scorer_cr, configs, lifted = scorer()
    pop = population(scorer_cr, configs)
    by_key = {a["key"]: a for a in pop["answers"]}
    stale = []
    try:
        for rid, rec in key["rows"].items():
            a = by_key.get(rec["ledger_key"])
            now = a["verdicts"][rec["concept_index"]] if a and rec["concept_index"] < len(a["verdicts"]) else None
            if now is None or {m: now[m] for m in MATCHERS} != rec["verdicts"] or stratum_of(a) != rec["stratum"] \
                    or sha(a["concepts"][rec["concept_index"]]) != rec["concept_sha256"] \
                    or sha(shown_text(a["text"])[0]) != rec["answer_sha256"]:
                stale.append(rid)
        answers = key["answers"]
        aid = [a["answer_id"] for a in answers]
        pi = np.array([float(a["inclusion_probability"]) for a in answers])
        cell = [(a["strategy"], a["stratum"]) for a in answers]
        rows = [(rid, aid.index(rec["answer_id"]), rec) for rid, rec in key["rows"].items()]
    except (KeyError, TypeError, ValueError, IndexError) as e:
        p3.refuse(ME, f"{p3.shown(OUT_KEY)} is not this script's key file ({type(e).__name__}: {e})")
    need(not stale, f"the matcher modules, the key or the deposit now give other verdicts, texts or strata than "
                    f"{p3.shown(OUT_KEY)} records on {len(stale)} rows, the first {stale[0] if stale else ''}; the sample was drawn "
                    "under the recorded ones")
    g.gate("A2", bool((pi > 0).all()) and len(set(aid)) == len(aid),
           f"the six verdicts, the shown text and the stratum of the {len(rows)} sampled pairs, computed again from the deposit "
           f"with the present modules, are the key file's; the {len(aid)} inclusion probabilities are above 0")

    n = len(answers)
    rs = np.random.RandomState(SEED + 1)
    reps = np.zeros((N_BOOT, n))
    for c in sorted(set(cell)):
        idx = [i for i in range(n) if cell[i] == c]
        if len(idx) == 1:
            reps[:, idx[0]] = 1.0
            continue
        picks = rs.randint(0, len(idx), size=(N_BOOT, len(idx) - 1))
        for k, i in enumerate(idx):
            reps[:, i] = (picks == k).sum(axis=1) * len(idx) / (len(idx) - 1)
    weights = {"unweighted": np.ones(n), "weighted": 1 / pi}

    def per_answer(test) -> np.ndarray:
        out = np.zeros(n)
        for rid, i, rec in rows:
            out[i] += bool(test(rid, rec))
        return out

    tables = []
    for subset in SUBSETS:
        inside = (lambda rec: True) if subset == "all_pairs" else (lambda rec: rec["verdicts"]["stem"] and not rec["verdicts"]["loose"])
        for reading, as_stated in READINGS.items():
            stated = lambda rid: labels[rid]["label"] in as_stated  # noqa: E731
            den_stated = per_answer(lambda rid, rec: inside(rec) and stated(rid))
            for m in MATCHERS:
                found = per_answer(lambda rid, rec: inside(rec) and rec["verdicts"][m])
                both = per_answer(lambda rid, rec: inside(rec) and rec["verdicts"][m] and stated(rid))
                for weighting, w in weights.items():
                    tables.append({"subset": subset, "reading": reading, "matcher": m, "weighting": weighting,
                                   "pairs": int(per_answer(lambda rid, rec: inside(rec)).sum()),
                                   "found_among_stated": rate(both, den_stated, w, reps),
                                   "not_stated_among_found": rate(found - both, found, w, reps)})
    counts = Counter(x["label"] for x in labels.values())
    label_counts = {lab: {"rows": counts[lab], "weighted_share": float((1 / pi) @ per_answer(lambda rid, rec: labels[rid]["label"] == lab))
                          / float((1 / pi) @ per_answer(lambda rid, rec: True))} for lab in LABELS}
    differ = [{"row_id": rid, "answer_id": rec["answer_id"], "question_id": rec["question_id"], "strategy": rec["strategy"],
               "concept": labels[rid]["concept"], "label": labels[rid]["label"], "stem": rec["verdicts"]["stem"],
               "verdicts": rec["verdicts"], "stem_detail": rec["stem_detail"], "comment": labels[rid]["comment"]}
              for rid, _, rec in rows if rec["verdicts"]["stem"] != (labels[rid]["label"] == "yes") or labels[rid]["label"] == "partly"]
    g.gate("A3", sum(counts.values()) == len(rows) and len(tables) == len(SUBSETS) * len(READINGS) * len(MATCHERS) * len(weights),
           f"{len(rows)} labels ({', '.join(f'{counts[lab]} {lab}' for lab in LABELS)}); {len(tables)} table rows; {len(differ)} "
           "rows where the stem verdict and the label differ")
    extra = {"gates": g.finish(), "seed": SEED + 1, "bootstrap_replicates": N_BOOT,
             "sheet": {"file": p3.shown(sheet), "sha256": p3.sha256_file(ME, sheet)},
             "key_file_sheet_sha256": key.get("provenance", {}).get("sheet", {}).get("sha256"),
             "libraries": {"nltk": nltk.__version__, "numpy": np.__version__, "openpyxl": openpyxl.__version__}}
    prov = p3.provenance(__file__, f"uv run python {SCRIPT} --analyze" + ("" if sheet == SHEET else f" --sheet {p3.shown(sheet)}"),
                         [("exp04", jl.MAIN_JUDGE), pop["deposit"], *lifted, Path(jl.MANIFEST), sheet], extra)
    doc = {"provenance": prov, "matchers": MATCHER_TEXT, "readings": READING_TEXT, "subsets": SUBSETS,
           "sample": {"answers": n, "pairs": len(rows), "labels": label_counts,
                      "strata_of_the_bootstrap": {f"{c[0]} / {c[1]}": cell.count(c) for c in sorted(set(cell))}},
           "tables": tables, "stem_and_label_differ": differ}
    p3.write_outputs(ME, {OUT_AN_JSON: json.dumps(doc, indent=1, ensure_ascii=False) + "\n", OUT_AN_MD: analysis_report(doc)})
    print(f"{ME} --analyze: wrote {p3.shown(OUT_AN_JSON)} and {p3.shown(OUT_AN_MD)}")
    return 0


def analysis_report(doc: dict) -> str:
    s, prov = doc["sample"], doc["provenance"]

    def cellof(x: dict) -> str:
        lo, hi = x["interval_95"]
        interval = "no interval" if lo is None else f"{pc(lo)} to {pc(hi)}"
        return f"{pc(x['share'])} ({x['numerator']} of {x['denominator']}; {interval})"

    L = ["# S439: the concept matchers against the hand labels", "",
         f"Written by `{prov['command']}` from `{prov['sheet']['file']}` (sha256 `{prov['sheet']['sha256'][:12]}`) and "
         f"`{p3.shown(OUT_KEY)}`. {s['answers']} sampled answers, {s['pairs']} pairs of one answer and one concept, each "
         "labelled by hand: does the answer state the concept (yes, partly, no). This report gives the rates and names no "
         "matcher to use.", "",
         "| label | rows | share, weighted to the population |", "|---|---:|---:|"]
    L += [f"| {lab} | {x['rows']} | {pc(x['weighted_share'])} |" for lab, x in s["labels"].items()]
    L += ["", "How to read the tables. \"found among stated\" is the share of the stated concepts that the matcher finds. "
              "\"not stated among found\" is the share of the concepts the matcher finds that are not stated. In brackets: "
              "the pairs counted, then a 95% interval from a bootstrap over the sampled answers "
              f"({prov['bootstrap_replicates']:,} replicates, seed {prov['seed']}; within each stratum of the draw, one answer "
              "fewer than sampled is redrawn with replacement, so the concepts of one answer stay together). \"weighted\" "
              "weights each answer by 1 over its inclusion probability, which undoes the larger chance the draw gave to "
              "answers where the stem matcher adds a concept; the counts in brackets are the sample's in both columns.", ""]
    for subset, text in doc["subsets"].items():
        for reading, rtext in doc["readings"].items():
            rows = [t for t in doc["tables"] if t["subset"] == subset and t["reading"] == reading]
            L += [f"## {text[0].upper() + text[1:]}, {rtext} ({rows[0]['pairs']} pairs)", "",
                  "| matcher | found among stated, unweighted | found among stated, weighted | not stated among found, unweighted | "
                  "not stated among found, weighted |", "|---|---|---|---|---|"]
            for m in MATCHERS:
                u, w = (next(t for t in rows if t["matcher"] == m and t["weighting"] == k) for k in ("unweighted", "weighted"))
                L.append(f"| {m} | {cellof(u['found_among_stated'])} | {cellof(w['found_among_stated'])} | "
                         f"{cellof(u['not_stated_among_found'])} | {cellof(w['not_stated_among_found'])} |")
            L.append("")
    L += ["## The matchers", ""] + [f"- `{m}`: {t}" for m, t in doc["matchers"].items()]
    L += ["", f"## Rows where the stem verdict and the label differ ({len(doc['stem_and_label_differ'])})", "",
          "Every row labelled partly, every row stem finds that is labelled no, and every row stem does not find that is "
          "labelled yes. \"words\" are the concept's content words with the test that matched each.", "",
          "| row | answer | question | strategy | concept | label | stem | words (needed) | other matchers that find it | comment |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for x in doc["stem_and_label_differ"]:
        det = x["stem_detail"]
        words = ", ".join(f"{w2}: {det['matched_by'].get(w2, 'no match')}" for w2 in det["content_words"]) or det["found_by"] or ""
        others = ", ".join(m for m in MATCHERS if m != "stem" and x["verdicts"][m]) or "none"
        L.append(f"| {x['row_id']} | {x['answer_id']} | {x['question_id']} | {x['strategy']} | {x['concept']} | {x['label']} | "
                 f"{'found' if x['stem'] else 'not found'} | {words} ({det['need']}) | {others} | {x['comment'].replace('|', '/')} |")
    L += ["", "## Gates", "", "| gate | result | what was tested |", "|---|---|---|"]
    L += [f"| {x['name']} | {'ok' if x['ok'] else 'FAIL'} | {x['message']} |" for x in prov["gates"]] + [""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="The blind label sheet for the concept matchers (--build) and the matchers "
                                             "scored against the labels (--analyze).")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true", help="draw the sample, write the sheet, the key file and the report")
    mode.add_argument("--analyze", action="store_true", help="read the filled sheet and write the rates per matcher")
    ap.add_argument("--sheet", type=Path, help="with --analyze: the filled sheet, when it was saved under another name "
                                               "(a path that is not absolute is taken from the repository root)")
    args = ap.parse_args()
    if args.build:
        need(args.sheet is None, "--sheet goes with --analyze")
        return build()
    return analyze((args.sheet if args.sheet.is_absolute() else p3.ROOT / args.sheet) if args.sheet else SHEET)


if __name__ == "__main__":
    raise SystemExit(main())
