#!/usr/bin/env python3
"""S448 - the editor's figure rules, checked on a figure's files: what can be checked automatically.

WHY. The editor's Editorial Requests Table sets rules for every main figure (display items, Source Data, figure
files, titles and captions, statistics), quoted with their rows in experiments/FIGURE_RULES.md as E1-E8, and the
journal's pages and the Nature research figure guide set more. A plate that breaks one is returned before review
(editor's letter, Reviewers_Nature_AIC/editor_review.txt:15). Both sets are mandatory (D84) and written, with their
values, in experiments/FIGURE_LOCK.toml (D87). This script reads every rule threshold from that file, refuses to run
when it is missing or its status is not "agreed", prints its sha256 first, and holds a figure's files to the part of
those rules a program can read; it lists the rest as MANUAL.

    uv run --frozen python scripts/S448_figure_rules_check.py --figure 6 --dir findings/figures_provisional/fig6

It reads, in --dir, the plate named by the lock's [files] name ("Figure <N>"; an optional " (provisional, ...)"
suffix is accepted and reported) in each format of [files] plate_files (.pdf, .svg and .png or .tif), the Source
Data named by [source_data] workbook_name ("Source Data Fig. <N>.xlsx", or a folder of one CSV per panel under its
stem), its caption "<stem> caption.md", figure<N>_numbers.json, figure<N>_provenance.json and legend_draft.md.
It prints PASS, FAIL, WARN, INFO or MANUAL per rule and exits 1 if any rule FAILs. It writes nothing.

    uv run --frozen python scripts/S448_figure_rules_check.py --figure 2 --supplementary \
        --dir findings/figures_provisional/supp_fig2

checks a Supplementary figure (D92 Q194): its plate is named by the lock's [files] supplementary_name
("Supplementary Figure <N>"), its numbers and provenance files supplementary_figure<N>_numbers.json and
supplementary_figure<N>_provenance.json, and its legend's title line "**Supplementary Figure <N> | title**". It is
held to the drawing rules: R1 to R7 and R9 to R12 as for a main figure, R1 finding its files by that name and still
holding [page] one_page and [files] file_max_mb (the journal's one-page rule names no figure kind, and its size limit
is written for Supplementary files). R8 runs its consistency parts (2) to (6) on the figure's data workbook, which S461
names "<supplementary_name> data" ("Supplementary Figure <N> data (...).xlsx", sheets "Supplementary Fig. <N>a" and so
on) with its optional caption "<that stem> caption.md" (D94 O-b); its part (1), the Source Data paperwork (the
[source_data] workbook name and formats, one sheet per panel, the caption file), a main-figure rule (editor row 20),
is not applied, nor are the E4 MANUAL line and the MANUAL [source_data] keys. The lock mutant of [files]
supplementary_name proves the name (the plate renamed and checked as a Supplementary figure; R1 then finds no plate,
so R8 does not run); --mutants with --supplementary runs the folder mutants of SUPP_MUTANTS (R8's consistency parts)
on the Supplementary folder and no lock-key mutant (those run on a main figure). Its "printed number" and "untied
number" re-hash the SVG in the provenance file, so part (3) passes and the FAIL must come from part (6), in its words.
Its "printed number" and "plate vs book" take the first printed number written with a fixed-point format (S461's
MRR values), or, on a plate that prints whole numbers only (S457's outcome table), the first written as a plain
field, which "plate vs book" moves by 1 instead of 0.1.

    uv run --frozen python scripts/S448_figure_rules_check.py --figure 6 --dir <dir> --mutants [--stale-from <dir2>]

checks the checker: it runs every rule on --dir (which must pass), then on copies of it in a temporary folder, each
copy altered once (MUTANTS below), and reports for each whether the rule built to catch it FAILs. --stale-from names
a folder of the same figure at another data state (S447 selftest's, kept with S447_SELFTEST_KEEP); its workbook and
numbers file are put beside --dir's plate. Then the lock: every key FIGURE_LOCK.toml tags "S448 R<n>" is changed in
a copy of the lock, and that rule's verdict on --dir (its status lines) must change (LOCK-KEY MUTANTS below); and the
keys the lock tags S448, the keys S448 reads (recorded as apply_lock() reads them) and the keys a mutant proves must
be one set, every other key of the value sections MANUAL. Nothing in --dir is written.

RULES (the E number is FIGURE_RULES.md's; every threshold is a key of FIGURE_LOCK.toml, named in brackets):
  R1  E5  one plate: one file of each [files] plate_files entry (a PDF, an SVG and a PNG or TIFF), all named by
          [files] name (supplementary_name with --supplementary); the PDF one page ([page] one_page); each file at
          most [files] file_max_mb (both also with --supplementary). Only a missing or doubled file stops the
          run; a page count or a size over the limit FAILs R1 and the other rules still run
  R2  E1  page: [page] width_double_mm or width_single_mm wide (within width_tol_mm), at most [page] height_max_mm
          high; the raster as wide as the PDF. The raster's dpi is held to [files] raster_dpi_min only when
          [files] upload_format is a raster format; the upload is the vector PDF, so the PNG is a preview (R7 holds
          it equal to the PDF) and its dpi is an INFO line
  R3  E1  type: every text from [type] font_min_pt to font_max_pt, in the SVG and in the PDF's text spans; with
          [type] text_as_text, an SVG or a PDF with no text fails. Every single-letter text outside matplotlib's tick
          and legend groups is a panel letter and must be [type] panel_letter_pt, panel_letter_weight and
          panel_letter_case, and in the PDF panel_letter_style (the italic flag)
  R4  E1  fonts in the PDF embedded ([type] fonts_embedded), of a family in [type] font_families, none of a type in
          font_types_refused
  R5  E3  palette: every colour in the SVG and in the PDF (fills, strokes and text) is a grey (channels within
          [colour] grey_tol), one of [colour] categorical (Okabe and Ito's eight), or within continuous_tol of an
          entry of the matplotlib colour map [colour] continuous (cividis, perceptually uniform); so no rainbow, jet
          or hsv scale. With [colour] vector_only, no raster image inside the SVG or the PDF
  R6  E1  red and green not both used: no saturated red (hue in [colour] red_hue_deg) beside a saturated green
          (hue in green_hue_deg; saturation and value at least saturated_min and value_min). Okabe-Ito's vermillion
          (27 degrees) and bluish green (164 degrees) are the colour-blind-safe pair and pass. INFO: the smallest
          colour difference (CIE76) between two category colours under simulated deuteranopia and protanopia
          (Machado, Oliveira and Fernandes 2009, severity 1)
  R7  E5  no text in the files that is not part of the figure: none of [files] forbidden_text (provisional, preliminary,
          draft, stamp, watermark, confidential, "not for citation" or "not for distribution", "do not cite",
          "records of", provenance; any case) in the SVG source (comments included), the PDF's text and metadata, or
          the PNG's text chunks. And the raster shows what the PDF shows: the PDF is rasterised again (MuPDF, at the
          raster's dpi and pixel size) and compared pixel by pixel; one pixel differing by more than [files]
          raster_delta levels in a channel fails (0: S447 writes the raster as MuPDF's rendering of the PDF, so the
          clean plate differs by 0; a stamp drawn in a grey as light as (226, 226, 226) fails). A figure builder
          therefore writes its raster by rasterising its PDF
  R8  E4, E8  Source Data and its pairing with the plate. (1) One workbook (or CSV folder), one sheet per panel
          letter on the plate, each with a header and at least one row. (2) Every value equals figure<N>_numbers.json
          (sheet names, columns, row count, each cell; numbers to 1e-9). (3) figure<N>_provenance.json, which the
          figure script writes with the plate, exists; every file it lists exists with the sha256 it records; it
          lists the PDF, the SVG, the raster, the workbook, the caption and the numbers file; and no "Figure <N>*" or
          "Source Data Fig. <N>*" file in --dir is missing from it. (4) The numbers file's "stamp" equals the
          provenance file's "stamp" (the plate's data stamp), and the caption carries that stamp. (5) The workbook's
          and the caption's names carry the same "(provisional, n of m)" as the plate's (or none, all three); a
          provisional name's "n of m" appears in the stamp, and a final name's stamp does not start "PROVISIONAL".
          (6) The plate against the workbook: the numbers file's "printed" map names, for every number printed on
          the plate, the SVG group id of its text and the workbook sheet and row (or the rows counted) and format it
          is written from; the SVG text in that group must equal the format filled from the workbook (on Figure 6
          the heatmap cell values, the "n = " labels of d and its "too few attempts (n = k)", c's "n = 20
          operations" and b's legend count); and every SVG text holding a digit must be in that map or a tick label
          (matplotlib's xtick_<k> / ytick_<k> groups). Numbers are filled as S447 prints them, rounded once half away
          from zero after rounding to 1e-9 (HalfUpFormatter). A number whose entry says where it sits is also held
          there, from the SVG's geometry: a heatmap value's centre inside the cell path drawn for its workbook row
          and column, a "n =" label of d on its own bar's row (the others are tied by id only, as the PASS line
          counts). So a workbook edited or zeroed fails (2), a workbook and
          numbers file of another data state beside the plate fail (3), (4) and (5), renamed or not, and a workbook
          and numbers file changed alike (provenance re-hashed) fail (6), as do a number added to the plate and two
          cell values or two "n =" labels that trade places. A Supplementary figure (--supplementary, D94 O-b): (2)
          to (6) on its data workbook "<supplementary_name> data" (exactly one, xlsx or a CSV folder, since (2) and
          (6) read it) and its caption when there is one, with supplementary_figure<N>_numbers.json and _provenance.json;
          (1) is not applied
  R9  E6, E7 (heuristic, on legend_draft.md): the title names no panel ([legend] title_panel_re); every panel letter on the plate is defined
          ("**a**," and so on); an "n = <number>" is present; no count is given as a range: no two numbers joined
          by "to", "or" or a dash (hyphen-minus, hyphen, non-breaking hyphen, figure dash, en dash, em dash, minus
          sign), and no "between N and M", either right after "n =" or followed within three words, separated by
          spaces, commas, semicolons, colons, round or square brackets or quotes (no other punctuation), by a count word (attempts, operations, per, samples, replicates, runs, questions,
          variants, models, records, cells, units, strategies, draws, answers, items, each); so "4-5", "4–5",
          "4 to 5 matched attempts", "4-5 (matched) attempts", "4 or 5 per" and "between 4 and 5 attempts" fail and
          "0 to 100%" passes. A range written otherwise (in words, or with its count word four or more words away)
          is not seen; the PASS line lists the forms. [statistics] sidedness_phrase ("two-sided"), or the same
          phrase with "two" read as "one" ("one-sided"), stated only where the legend describes an interval, an
          error bar or band, a test or a P value ([statistics] sidedness_when, a regex, case ignored; "no hypothesis
          test" does not count) (D122, Valerio, 23 October, Q3: editor row 46 "where appropriate"); a legend that
          draws only medians, quartiles or ranges needs none. The "n = <number>" is asked for only where the legend
          names a mean, a median, an interval, an error bar or band, or a test ([statistics] n_when, a regex, case
          ignored; D310, Valerio, 9 November, Q1); a legend that draws no statistic needs none, and a range fails
          wherever it stands. A provisional plate's legend_draft.md carries the
          provenance file's stamp; its legend need not say "provisional" (D122: the file name's suffix, R1, and the
          data stamp carry it). The panel check is [legend] panels_defined,
          the n checks [statistics] n_exact; the dashes and count words are n_range_dashes and n_count_words. The
          legend (title line to the end) under [legend] words_under words (the journal: "under 350 words", so 350
          or more is too long): a WARN on a provisional plate (D84 Q158, legends shrunk later), a FAIL on a final one
  R10 E5, E8  the SVG's text and painted shapes against the PDF's, element by element at their positions. Text: every
          non-space character, keyed by (character, size, rotation, colour, weight), at its baseline start in the
          page's coordinates (the SVG text's anchor turned into its start with the font's advance widths; PyMuPDF's
          character origins in the PDF) must have a partner within 0.25 mm (a text's first character), 0.3 mm (later
          characters) or 0.6 mm (a character after an "f": the PDF reports a ligature's second character at the
          ligature's origin). Shapes: every painted fill and stroke (SVG paths and markers, PDF drawings), keyed by
          its colour, must have a partner whose box is within 0.3 pt on each edge. So a label altered, two labels or
          two values swapped, a text added, and a shape recoloured (to a new colour or to one the plate already
          uses) fail. Not seen: a change made identically in both files (R8 (6) holds the printed numbers to the
          workbook), a change smaller than the tolerances, and what R10 does not compare: the SVG side is read from
          each <text>'s own x, y and transform and each path's own points (a transform on an enclosing group or a
          path is not composed); opacity (other than a path's own fill-opacity or stroke-opacity of 0; text opacity and the opacity property are not read), visibility, display, paint order, stroke width (other than
          0), dashes, clip paths and font family are not compared. The PNG is the PDF rasterised and R7 holds the two
          equal; the SVG is checked against the PDF for text and shape positions only. R10's tolerances are the
          checker's own (how closely the two files must agree), not figure rules, and stay in this script
  R11 E1  text contrast, in the PDF: each text span's colour against the fill painted under its centre (the last
          filled drawing before it in paint order whose box holds the centre, else the white page), WCAG 2.1 ratio
          at least [type] contrast_min_ratio (the journal: "at least 4.5:1"). Coloured text (not grey by [colour]
          grey_tol) is a WARN under [type] coloured_text "avoid", a FAIL under "none", unchecked under "allowed"
  R12 E1  line widths: every painted stroke in the PDF and in the SVG at least [lines] line_min_pt (a PDF stroke of
          width 0 is a hairline and fails)
  MANUAL E2 (every point value with error bars also shows its points; tied points spread at right angles to the
          value axis, never along it), E6/E7 wording (every n exact, every point estimate and interval defined, e.g.
          a pass rate over several attempts per unit as the mean of the units' shares, experiments/LIST.md Rule 2),
          E8 consistency (the claims list against the text), the Data Availability sentence, and every key of
          FIGURE_LOCK.toml whose comment says MANUAL (listed on the LOCK line): a person reads these.

MUTANTS (--mutants), each with the rule that must FAIL:
  faint stamp      "PROVISIONAL" drawn on the PNG in (226, 226, 226), on white paper (an     R7
                   empty box of the plate), dpi kept: every changed pixel differs by 29 levels
  stale pair       --stale-from's workbook and numbers file in place of the plate's, its    R8
                   names kept
  stale renamed    the same, the workbook renamed to the plate's "(provisional, n of m)"     R8
  zeroed value     the workbook's first non-zero number set to 0                            R8
  altered label    the first SVG text with a word of 3+ letters: that word gets an "s"      R10
                   (on Figure 6, "gemini-3-flash (default)" -> "geminis-3-flash (default)")
  added text       an SVG <text> "PRELIMINARY / NOT FOR CITATION" added                     R7, R10
  colour changed   the first SVG fill colour shifted by one level of blue                   R10
  swapped labels   two SVG texts swapped, 'low' and 'high' where both exist                 R10
  swapped values   two SVG numbers swapped, '90' and '35' where both exist                  R8, R10
  existing colour  an SVG heatmap cell recoloured to another cell's fill (a colour already  R10
                   on the plate, so R5 passes)
  plate vs book a  a printed cell of sheet a changed by 5 in the workbook and the numbers   R8
                   file alike, the provenance re-hashed (only (6) can see it)
  plate vs book d  the same on sheet d's attempts_n (the "n = " label)                      R8
  untied number    an SVG <text> "42" added outside any tick or printed group              R8
  cells in place   two heatmap value texts of different values trade positions (x, y,      R8 (at their place)
                   transform), each keeping its id and value
  d n swapped      two "n =" labels of d of different values trade positions               R8 (at their place)
  range hyphen     legend: "n = 4-5 attempts"                                              R9
  range en dash    legend: "4–5 attempts"                                                  R9
  range to         legend: "4 to 5 matched attempts"                                       R9
  range or         legend: "4 or 5 per strategy set"                                       R9
  range between    legend: "between 4 and 5 attempts"                                      R9
  range fig dash   legend: "4‒5 (matched) attempts" (figure dash, a bracket between)         R9
  range minus      legend: "4−5 runs" (minus sign)                                          R9
  low contrast     PDF text "low contrast label" in (179, 179, 179) on white, about 2.2:1   R11
  thin line pdf    a 0.1 pt line drawn into the PDF                                         R12
  thin line svg    an SVG path with stroke-width 0.1 added                                  R12
A mutant is CAUGHT when every rule it wants FAILs and, where it names a message, that rule's FAIL line says it; a
wanted rule that already FAILs on the clean folder counts only when its FAIL line changed (the mutant was seen, not a
failure that was there before).

LOCK-KEY MUTANTS (--mutants), one per key the lock tags "S448 R<n>" (lock_mutants() lists them): the key gets another
value in a copy of the lock, and the tagged rule's status lines on --dir must differ from those under the copy
without the change. A mutant may set other keys in both copies (its base: a key can only move a verdict the rest of
the lock leaves movable, so R3's panel-letter keys run with the type bounds opened to 1 to 100 pt, since a figure
whose type fails R3 fails it whatever they say), and may alter a copy of the folder for both runs, where a key matters only on
a figure that breaks its rule (a second PDF page for one_page, a font not embedded for fonts_embedded, a raster image
for vector_only, the faint stamp for raster_delta, a range in the legend for n_exact, every "n = <number>" written as
"count <number>" for n_when); sidedness_when runs with
sidedness_phrase set to a phrase no legend holds in both copies, so the trigger alone moves R9. The file_max_mb mutant also
requires the rules after R1 to have run. The last line counts both kinds and says whether the lock coverage is
complete.

No model call; no Ollama contact.
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import math
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

# Every threshold of a figure rule comes from experiments/FIGURE_LOCK.toml (D84, D87): the editor's and the journal's
# figure rules, with the lock's status. S448 refuses to run when the file is missing or its status is not "agreed",
# and prints the file's sha256 at the head of its output. R8's and R10's tolerances below are the checker's own (how
# exactly two of the figure's files must agree), not figure rules, and stay here.
FIGURE_LOCK = Path(__file__).resolve().parents[1] / "experiments" / "FIGURE_LOCK.toml"
READ = set()          # "section.key" of every lock key apply_lock() read: --mutants holds it to the lock's S448 tags


class _Section(dict):
    """A lock section that records each key read from it (READ)."""

    def __init__(self, name, d):
        super().__init__(d)
        self.name = name

    def __getitem__(self, k):
        READ.add(f"{self.name}.{k}")
        return super().__getitem__(k)


def load_lock(p: Path = FIGURE_LOCK):
    if not p.exists():
        sys.exit(f"S448 refuses to run: {p} is missing (D87: every figure is checked against the figure lock)")
    raw = p.read_bytes()
    lock = tomllib.loads(raw.decode("utf-8"))
    if lock.get("status") != "agreed":
        sys.exit(f"S448 refuses to run: {p} has status {lock.get('status')!r}, not 'agreed' (D87)")
    return lock, hashlib.sha256(raw).hexdigest()


def _one_of(sec, key, allowed):
    v = sec[key]
    if v not in allowed:
        sys.exit(f"S448 refuses to run: [{sec.name}] {key} = {v!r}, not one of {allowed}")
    return v


def apply_lock(lock, path: Path, sha: str):
    """Every rule value S448 uses, read from the lock (each read recorded in READ). Every key is read here, so a
    rule never reads the lock itself and a copy of the lock can be swapped in (--mutants)."""
    global LOCK, LOCK_PATH, LOCK_SHA256, W_DOUBLE, W_SINGLE, W_TOL, H_MAX_MM, ONE_PAGE, PT_FLOOR, PT_MAX, PT_LETTER
    global LETTER_WEIGHT, LETTER_CASE, LETTER_STYLE, FONT_FAMILIES, FONTS_EMBEDDED, FONT_TYPES_REFUSED, TEXT_AS_TEXT
    global CONTRAST_MIN, COLOURED_TEXT, LINE_MIN_PT, OKABE, CONTINUOUS, CONT_TOL, GREY_TOL, VECTOR_ONLY, RED_HUE
    global GREEN_HUE, SAT_MIN, VAL_MIN, NAME_TMPL, PLATE_FILES, UPLOAD_FORMAT, DPI_WANT, RASTER_DELTA, FILE_MAX_MB
    global STAMP, WORDS_UNDER, TITLE_PANEL, PANELS_DEFINED, N_EXACT, RANGE, SIDEDNESS, SIDED_WHEN, N_WHEN, SD_REQUIRED
    global SD_FORMATS, SD_NAME, SD_CAPTION, SUPP_NAME_TMPL
    READ.clear()
    LOCK, LOCK_PATH, LOCK_SHA256 = lock, path, sha
    pg, ty, li, co, fi, le, st, sd = (_Section(k, lock[k]) for k in ("page", "type", "lines", "colour", "files",
                                                                      "legend", "statistics", "source_data"))
    W_DOUBLE, W_SINGLE = float(pg["width_double_mm"]), float(pg["width_single_mm"])            # R2
    W_TOL, H_MAX_MM = float(pg["width_tol_mm"]), float(pg["height_max_mm"])                     # R2
    ONE_PAGE = bool(pg["one_page"])                                                             # R1
    PT_FLOOR, PT_MAX, PT_LETTER = float(ty["font_min_pt"]), float(ty["font_max_pt"]), float(ty["panel_letter_pt"])  # R3
    LETTER_WEIGHT = _one_of(ty, "panel_letter_weight", ("bold", "normal"))                      # R3
    LETTER_CASE = _one_of(ty, "panel_letter_case", ("lowercase", "uppercase"))                  # R3
    LETTER_STYLE = _one_of(ty, "panel_letter_style", ("upright", "italic"))                     # R3
    TEXT_AS_TEXT = bool(ty["text_as_text"])                                                     # R3
    FONT_FAMILIES, FONTS_EMBEDDED = list(ty["font_families"]), bool(ty["fonts_embedded"])       # R4
    FONT_TYPES_REFUSED = list(ty["font_types_refused"])                                         # R4
    CONTRAST_MIN = float(ty["contrast_min_ratio"])                                              # R11
    COLOURED_TEXT = _one_of(ty, "coloured_text", ("avoid", "none", "allowed"))                  # R11
    LINE_MIN_PT = float(li["line_min_pt"])                                                      # R12
    OKABE = [c.upper() for c in co["categorical"]]                                              # R5, R6
    CONTINUOUS, CONT_TOL, GREY_TOL = str(co["continuous"]), int(co["continuous_tol"]), int(co["grey_tol"])  # R5
    VECTOR_ONLY = bool(co["vector_only"])                                                       # R5
    RED_HUE, GREEN_HUE = [float(x) for x in co["red_hue_deg"]], [float(x) for x in co["green_hue_deg"]]  # R6
    SAT_MIN, VAL_MIN = float(co["saturated_min"]), float(co["value_min"])                       # R6
    NAME_TMPL = fi["name"]                                                                      # R1
    SUPP_NAME_TMPL = fi["supplementary_name"]                                                   # R1 (--supplementary)
    PLATE_FILES = [[x.lower() for x in e.split("|")] for e in fi["plate_files"]]                # R1
    for need in ("pdf", "svg"):
        if not any(need in e for e in PLATE_FILES):
            sys.exit(f"S448 refuses to run: [files] plate_files {fi['plate_files']} has no {need}")
    if not any(set(e) & {"png", "tif", "tiff"} for e in PLATE_FILES):
        sys.exit(f"S448 refuses to run: [files] plate_files {fi['plate_files']} has no raster (png, tif)")
    UPLOAD_FORMAT = str(fi["upload_format"]).lower()                                            # R2
    if not any(UPLOAD_FORMAT in e for e in PLATE_FILES):
        sys.exit(f"S448 refuses to run: [files] upload_format {UPLOAD_FORMAT!r} is not one of plate_files")
    DPI_WANT, RASTER_DELTA = int(fi["raster_dpi_min"]), int(fi["raster_delta"])                 # R2, R7
    FILE_MAX_MB = float(fi["file_max_mb"])                                                      # R1
    STAMP = re.compile(fi["forbidden_text"], re.I)                                              # R7
    WORDS_UNDER = int(le["words_under"])                                                        # R9
    TITLE_PANEL, PANELS_DEFINED = re.compile(le["title_panel_re"]), bool(le["panels_defined"])  # R9
    N_EXACT, SIDEDNESS = bool(st["n_exact"]), st["sidedness_phrase"]                            # R9
    # R9: the sidedness is asked for only where the legend describes an interval, an error bar or band, a test or a P
    # value (D122, Valerio, 23 October, Q3: editor row 46 "where appropriate"); case is ignored
    SIDED_WHEN = re.compile(st["sidedness_when"], re.I)                                          # R9
    # R9: "n = <number>" is asked for only where the legend names a mean, a median, an interval, an error bar or band,
    # or a test (D310, Valerio, 9 November, Q1: R9 O1); case is ignored
    N_WHEN = re.compile(st["n_when"], re.I)                                                      # R9
    # R9: a count given as a range. Two numbers joined by "to", "or", a dash of n_range_dashes, or "between N and
    # M"; a range after "n =" whatever follows, otherwise only when a count word of n_count_words follows within three
    # words, the words separated by spaces, commas, semicolons, colons, brackets or quotes (_SEP) (so "4-5 (matched)
    # attempts" and "4 to 5, per strategy" are seen, and "0 to 100%" and "kinds 8, 9 and 12" pass). A range written
    # otherwise (in words, as "four or five", or with its count word four or more words away) is not seen.
    dashes = "".join(re.escape(c) for c in st["n_range_dashes"])
    num = r"\d[\d,]*(?:\.\d+)?"
    rng = rf"(?:{num}\s*(?:[{dashes}]|\bto\b|\bor\b)\s*{num}|\bbetween\s+{num}\s+and\s+{num})"
    count = "(?:" + "|".join(st["n_count_words"]) + ")"
    sep = r"[\s,;:()\[\]'\"\u2018\u2019\u201c\u201d]+"
    RANGE = re.compile(rf"\bn\s*=\s*{rng}|{rng}(?:{sep}[\w{dashes}]+){{0,2}}?{sep}{count}\b", re.I)
    SD_REQUIRED, SD_CAPTION = bool(sd["per_main_figure"]), bool(sd["caption"])                   # R8
    SD_FORMATS, SD_NAME = [x.lower() for x in sd["formats"]], sd["workbook_name"]               # R8


_lk, _sha = load_lock()
apply_lock(_lk, FIGURE_LOCK, _sha)
AGREED = (_lk, FIGURE_LOCK, _sha)        # the agreed lock, restored after each lock mutant
RANGE_FORMS = ("N to M, N or M, N-M with a dash of [statistics] n_range_dashes, and between N and M, right after "
               "'n =' or followed within three words by a count word of n_count_words, the words separated by spaces, "
               "commas, semicolons, colons, round or square brackets or quotes; a range written otherwise is not seen")
TAG = re.compile(r"\((provisional, (\d+) of (\d+))\)")
RESULTS = []


def say(rule, status, msg):
    RESULTS.append((rule, status))
    print(f"{rule:4s} {status:6s} {msg}")


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def is_grey(rgb, tol=None):
    return max(rgb) - min(rgb) <= (GREY_TOL if tol is None else tol)


# ---------------------------------------------------------------------------------------------------------------
_SUFFIX = r"( \((provisional[^)]*)\))?"          # a provisional plate's name suffix, "(provisional, n of m)"


SUPP = False          # --supplementary: a Supplementary figure, held to the drawing rules (D92 Q194) and R8's
                      # consistency parts (2) to (6) (D94 O-b)


def plate_name(n: int) -> str:
    """The plate's file name without suffix or extension: the lock's [files] name with the figure number, or its
    supplementary_name for a Supplementary figure (--supplementary)."""
    return (SUPP_NAME_TMPL if SUPP else NAME_TMPL).format(n=n)


def side_name(n: int, what: str) -> str:
    """The numbers or provenance file the figure script writes beside the plate: figure<N>_<what>.json, or
    supplementary_figure<N>_<what>.json for a Supplementary figure (S461), so it never shares a name with main
    Figure <N>'s."""
    return f"{'supplementary_' if SUPP else ''}figure{n}_{what}.json"


def find_files(d: Path, n: int):
    exts = "|".join(sorted({x for e in PLATE_FILES for x in e}))
    pat = re.compile(rf"^{re.escape(plate_name(n))}{_SUFFIX}\.({exts})$", re.I)
    figs = [p for p in d.iterdir() if p.is_file() and pat.match(p.name)]
    return figs, pat


def sd_stem(n: int) -> str:
    """The Source Data name without extension: the lock's [source_data] workbook_name with the figure number; for a
    Supplementary figure (--supplementary) "<supplementary_name> data", the data workbook S461 writes (Source Data is
    a main-figure rule, so R8 holds a Supplementary figure to its consistency parts only; D94 O-b)."""
    if SUPP:
        return f"{plate_name(n)} data"
    return re.sub(r"\.[A-Za-z0-9]+$", "", SD_NAME.format(n=n))


def sd_files(d: Path, n: int):
    """(workbooks, CSV folders, captions) named after sd_stem(): [source_data] workbook_name, or for a Supplementary
    figure "<supplementary_name> data"; each with an optional suffix."""
    stem = re.escape(sd_stem(n))
    wb = re.compile(rf"^{stem}{_SUFFIX}\.xlsx$", re.I)
    fo = re.compile(rf"^{stem}{_SUFFIX}$", re.I)
    ca = re.compile(rf"^{stem} caption{_SUFFIX}\.md$", re.I)
    items = sorted(d.iterdir())
    return ([p for p in items if p.is_file() and wb.match(p.name)], [p for p in items if p.is_dir() and fo.match(p.name)],
            [p for p in items if p.is_file() and ca.match(p.name)])


def r1(figs, pat, n):
    """One plate: one file of each [files] plate_files entry, all of one name; the PDF one page when [page] one_page;
    each file at most [files] file_max_mb. Only a missing or doubled file stops the run: a page count or a size over
    the limit FAILs and the other rules still run on the files. The same for a Supplementary figure, its name read
    from [files] supplementary_name: one_page cites journal 2.1, which does not limit it to main figures, and
    file_max_mb's journal limit is written for Supplementary files (FIGURE_LOCK.toml [files])."""
    by_kind = {"|".join(e): [p for p in figs if p.suffix.lower().lstrip(".") in e] for e in PLATE_FILES}
    stems = {p.stem for p in figs}
    if not (all(len(v) == 1 for v in by_kind.values()) and len(stems) == 1):
        say("R1", "FAIL", f"want one file of each of the lock's plate_files {['|'.join(e) for e in PLATE_FILES]}, "
                          f"named {plate_name(n)!r} (an optional provisional suffix); found "
                          f"{sorted(p.name for p in figs)}")
        return None
    one = {k: v[0] for k, v in by_kind.items()}
    kind = lambda want: next(p for k, p in one.items() if want & set(k.split("|")))
    pdf, svg, raster = kind({"pdf"}), kind({"svg"}), kind({"png", "tif", "tiff"})
    prov = pat.match(figs[0].name).group(2)
    import fitz
    pages = fitz.open(pdf).page_count
    probs = []
    if ONE_PAGE and pages != 1:
        probs.append(f"the PDF has {pages} pages; a figure is one page ([page] one_page)")
    size_mb = {p.name: p.stat().st_size / 1e6 for p in one.values()}
    big = [f"{k} {v:.3g} MB" for k, v in size_mb.items() if v > FILE_MAX_MB]
    if big:
        probs.append(f"over the lock's {FILE_MAX_MB:g} MB per file: {big}")
    say("R1", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"one plate '{figs[0].stem}' as " + ", ".join(p.suffix[1:].upper() for p in one.values()) +
        f"{', named by [files] supplementary_name (a Supplementary figure)' if SUPP else ''}"
        f"; the PDF {pages} page{'s' if pages != 1 else ''}; largest file {max(size_mb.values()):.3g} MB; lock: "
        f"{'one page, ' if ONE_PAGE else ''}each file at most {FILE_MAX_MB:g} MB")
    if prov:
        say("R1", "WARN", f"the file name carries '({prov})': it must read {plate_name(n)!r} alone at submission "
                          "(editorial table, 'Figures' row)")
    return {"pdf": pdf, "svg": svg, "raster": raster, "provisional": bool(prov)}


def svg_scale(root):
    """Millimetres per SVG user unit, from the width attribute and the viewBox."""
    w = root.get("width")
    m = re.match(r"([\d.]+)\s*(pt|mm|px|in)?", w)
    val, unit = float(m.group(1)), m.group(2) or "px"
    mm = val * {"pt": 25.4 / 72, "mm": 1.0, "px": 25.4 / 96, "in": 25.4}[unit]
    vb = [float(x) for x in root.get("viewBox").split()]
    h = root.get("height")
    m2 = re.match(r"([\d.]+)\s*(pt|mm|px|in)?", h)
    hmm = float(m2.group(1)) * {"pt": 25.4 / 72, "mm": 1.0, "px": 25.4 / 96, "in": 25.4}[m2.group(2) or "px"]
    return mm / vb[2], mm, hmm


def r2(f):
    import fitz
    from PIL import Image
    pg = fitz.open(f["pdf"])[0].rect
    pw, ph = pg.width * 25.4 / 72, pg.height * 25.4 / 72
    root = ET.parse(f["svg"]).getroot()
    _, sw, sh = svg_scale(root)
    im = Image.open(f["raster"])
    dpi = (im.info.get("dpi") or (0, 0))[0]
    rw_mm = im.size[0] / dpi * 25.4 if dpi else 0
    probs = []
    for name, w, h in (("PDF", pw, ph), ("SVG", sw, sh)):
        if min(abs(w - W_DOUBLE), abs(w - W_SINGLE)) > W_TOL:
            probs.append(f"{name} {w:.1f} mm wide, neither {W_DOUBLE:g} nor {W_SINGLE:g}")
        if h > H_MAX_MM:
            probs.append(f"{name} {h:.1f} mm high, over {H_MAX_MM:g}")
    if abs(rw_mm - pw) > W_TOL:
        probs.append(f"raster {rw_mm:.1f} mm wide at its dpi, the PDF {pw:.1f}")
    # the journal's bitmap resolution binds the file submitted: the raster only when [files] upload_format is one
    raster_up = UPLOAD_FORMAT in {"png", "tif", "tiff"}
    if raster_up and round(dpi) < DPI_WANT:
        probs.append(f"the submitted raster ({UPLOAD_FORMAT}) at {dpi:.0f} dpi, under {DPI_WANT}")
    msg = (f"PDF {pw:.1f} x {ph:.1f} mm, SVG {sw:.1f} x {sh:.1f} mm, raster {im.size[0]} x {im.size[1]} px at "
           f"{dpi:.0f} dpi ({rw_mm:.1f} mm); lock: width {W_DOUBLE:g} or {W_SINGLE:g} mm (within {W_TOL:g}), height "
           f"at most {H_MAX_MM:g} mm" + (f", the submitted raster at least {DPI_WANT} dpi" if raster_up else ""))
    say("R2", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") + msg)
    if not raster_up:
        say("R2", "INFO", f"the raster is a preview at {dpi:.0f} dpi (R7 holds it equal to the PDF); the upload is "
                          f"the {UPLOAD_FORMAT.upper()} ([files] upload_format), so the journal's {DPI_WANT} dpi for "
                          f"a submitted bitmap ([files] raster_dpi_min) is reported, not failed"
                          + (f": this raster is under it" if round(dpi) < DPI_WANT else ""))


def svg_texts(root):
    """(size in pt, weight "bold" or "normal", text, fill, in a tick or legend group) for every <text>, with style
    inherited from enclosing groups. The last field is True inside a group whose id is matplotlib's xtick_<k>,
    ytick_<k> or legend_<k>."""
    k, _, _ = svg_scale(root)
    out = []

    def style_of(el):
        return dict(kv.split(":", 1) for kv in (el.get("style") or "").split(";") if ":" in kv)

    def walk(el, inh, aside):
        st = {**inh, **{a.strip(): b.strip() for a, b in style_of(el).items()}}
        for attr in ("font-size", "font-weight", "fill"):
            if el.get(attr):
                st[attr] = el.get(attr)
        aside = aside or bool(re.fullmatch(r"[xy]tick_\d+|legend_\d+", el.get("id") or ""))
        if el.tag.endswith("}text") or el.tag == "text":
            fs = st.get("font-size")
            weight = "bold" if st.get("font-weight", "") in ("700", "bold") else "normal"
            if fs is None:
                out.append((None, weight, "".join(el.itertext()), st.get("fill"), aside))
            else:
                v = float(re.match(r"[\d.]+", fs).group(0))
                pt = v * k * 72 / 25.4
                out.append((pt, weight, "".join(el.itertext()).strip(), st.get("fill"), aside))
        for ch in el:
            walk(ch, st, aside)
    walk(root, {}, False)
    return out


def r3(f):
    """Type, in the SVG and in the PDF's text spans: every text from [type] font_min_pt to font_max_pt; text kept as
    text ([type] text_as_text: an SVG or a PDF with no text fails). Panel letters: every single-letter text outside
    the tick labels and the legends is taken as a panel letter and must be [type] panel_letter_pt, of
    panel_letter_weight and panel_letter_case, and in the PDF of panel_letter_style (the italic flag)."""
    root = ET.parse(f["svg"]).getroot()
    texts = svg_texts(root)
    probs = []
    if any(t[0] is None for t in texts):
        probs.append(f"{sum(t[0] is None for t in texts)} SVG text elements with no font size")
    sized = [t for t in texts if t[0] is not None]
    if not sized and TEXT_AS_TEXT:
        probs.append("no text in the SVG: text converted to paths can be neither read nor edited ([type] text_as_text)")
    lo = min((t[0] for t in sized), default=None)
    hi = max((t[0] for t in sized), default=None)
    if lo is not None and lo < PT_FLOOR - 0.01:
        probs.append(f"smallest SVG text {lo:.2f} pt, under the lock's {PT_FLOOR:g}")
    if hi is not None and hi > PT_MAX + 0.01:
        probs.append(f"largest SVG text {hi:.2f} pt, over the lock's {PT_MAX:g}")
    case_ok = str.islower if LETTER_CASE == "lowercase" else str.isupper
    letters = [t for t in sized if re.fullmatch(r"[A-Za-z]", t[2]) and not t[4]]
    bad_letters = [t for t in letters if not (abs(t[0] - PT_LETTER) < 0.05 and t[1] == LETTER_WEIGHT
                                              and case_ok(t[2]))]
    if bad_letters:
        probs.append(f"single letters (panel letters) that are not {PT_LETTER:g} pt {LETTER_WEIGHT} {LETTER_CASE}: "
                     f"{[(round(t[0], 2), t[1], t[2]) for t in bad_letters][:5]}")
    panel = sorted(t[2] for t in letters if t not in bad_letters)
    # the PDF, as printed
    import fitz
    spans = []
    for b in fitz.open(f["pdf"])[0].get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                if s["text"].strip():
                    spans.append((s["size"], s["text"].strip(), bool(s["flags"] & 16), bool(s["flags"] & 2)))
    if not spans and TEXT_AS_TEXT:
        probs.append("no text in the PDF ([type] text_as_text)")
    plo = min((s[0] for s in spans), default=None)
    phi = max((s[0] for s in spans), default=None)
    if plo is not None and plo < PT_FLOOR - 0.01:
        probs.append(f"smallest PDF text {plo:.2f} pt")
    if phi is not None and phi > PT_MAX + 0.01:
        probs.append(f"largest PDF text {phi:.2f} pt")
    # the PDF's panel letters: single-letter spans that are a panel letter of the SVG at that letter's size
    want_italic = LETTER_STYLE == "italic"
    sv = {(t[2], round(t[0], 1)) for t in letters}
    p_style = [s[1] for s in spans if (s[1], round(s[0], 1)) in sv and s[3] != want_italic]
    if p_style:
        probs.append(f"PDF panel letters not {LETTER_STYLE}: {p_style}")
    sizes = sorted({round(t[0], 2) for t in sized})
    span_rng = f"PDF {plo:.2f} to {phi:.2f} pt" if spans else "no PDF text"
    say("R3", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"SVG sizes {sizes} pt over {len(sized)} text elements, {span_rng}; lock: every text {PT_FLOOR:g} to "
        f"{PT_MAX:g} pt, panel letters {PT_LETTER:g} pt {LETTER_WEIGHT} {LETTER_STYLE} {LETTER_CASE}: "
        f"{', '.join(panel) or 'none'}")
    return panel


def r4(f):
    import fitz
    doc = fitz.open(f["pdf"])
    fonts = doc[0].get_fonts(full=True)
    probs = []
    not_emb = [x[3] for x in fonts if x[1] == "n/a"]
    if not_emb and FONTS_EMBEDDED:
        probs.append(f"not embedded: {not_emb}")
    refused = [f"{x[3]} ({x[2]})" for x in fonts if x[2] in FONT_TYPES_REFUSED]
    if refused:
        probs.append(f"font type refused by the lock ({', '.join(FONT_TYPES_REFUSED)}): {refused}")
    fam = [x[3] for x in fonts if not any(f.lower() in x[3].lower() for f in FONT_FAMILIES)]
    if fam:
        probs.append(f"not {' or '.join(FONT_FAMILIES)}: {fam}")
    say("R4", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"{len(fonts)} font(s): " + ", ".join(sorted({f'{x[3]} ({x[2]})' for x in fonts})) +
        f"; lock: {'embedded, ' if FONTS_EMBEDDED else ''}{' or '.join(FONT_FAMILIES)}, no "
        f"{', '.join(FONT_TYPES_REFUSED)}")


def svg_colours(svg_text):
    cols = set()
    for m in re.finditer(r'(?:fill|stroke|stop-color|color)\s*[:=]\s*"?\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b',
                         svg_text):
        cols.add("#" + "".join(f"{c:02X}" for c in hex_rgb(m.group(1))))
    return cols


def pdf_colours(pdf):
    """Every fill, stroke and text colour on the PDF's page, as #RRGGBB, and the number of raster images on it."""
    import fitz
    pg = fitz.open(pdf)[0]
    cols = set()
    for d in pg.get_drawings():
        for key in ("fill", "color"):
            c = d.get(key)
            if c is not None and len(c) == 3:
                cols.add("#" + "".join(f"{round(x * 255):02X}" for x in c))
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                if sp["text"].strip():
                    cols.add(f"#{sp['color']:06X}")
    return cols, len(pg.get_images(full=True))


def r5(f):
    from matplotlib import colormaps
    import numpy as np
    s = Path(f["svg"]).read_text()
    scols = svg_colours(s)
    pcols, p_img = pdf_colours(f["pdf"])
    cols = scols | pcols
    probs = []
    try:
        cmap = colormaps[CONTINUOUS]
    except KeyError:
        say("R5", "FAIL", f"[colour] continuous {CONTINUOUS!r} is not a matplotlib colour map")
        return [], sorted(cols)
    cont = (np.array(cmap(np.linspace(0, 1, 256)))[:, :3] * 255).round()
    okabe = {c.upper() for c in OKABE}
    kinds, outside = {"grey": [], "okabe": [], "continuous": []}, []
    for c in sorted(cols):
        rgb = hex_rgb(c)
        if c in okabe:
            kinds["okabe"].append(c)
        elif is_grey(rgb):
            kinds["grey"].append(c)
        elif np.abs(cont - np.array(rgb)).max(axis=1).min() <= CONT_TOL:
            kinds["continuous"].append(c)
        else:
            outside.append(c)
    n_img = len(re.findall(r"<image\b", s))
    if outside:
        where = lambda c: "SVG and PDF" if c in scols and c in pcols else ("PDF only" if c in pcols else "SVG only")
        probs.append(f"{len(outside)} colour(s) outside grey, the lock's categorical palette and {CONTINUOUS}: "
                     f"{[f'{c} ({where(c)})' for c in outside[:8]]}")
    if VECTOR_ONLY and n_img:
        probs.append(f"{n_img} raster image(s) inside the SVG")
    if VECTOR_ONLY and p_img:
        probs.append(f"{p_img} raster image(s) inside the PDF")
    say("R5", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"{len(cols)} colours over SVG ({len(scols)}) and PDF ({len(pcols)}): {len(kinds['okabe'])} categorical "
        f"(Okabe-Ito), {len(kinds['continuous'])} {CONTINUOUS}, {len(kinds['grey'])} grey; " +
        (f"{n_img} image(s) in the SVG and {p_img} in the PDF" if n_img or p_img else
         "vector only (no image in the SVG or the PDF)") +
        f"; lock: {'vector only' if VECTOR_ONLY else 'images allowed'} ([colour] vector_only)")
    return kinds["okabe"], outside


def _lin(c):
    c = c / 255
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def _lab(rgb_lin):
    import numpy as np
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    x, y, z = M @ rgb_lin / np.array([0.95047, 1.0, 1.08883])
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def r6(okabe_used, other):
    import numpy as np
    reds, greens = [], []
    for c in okabe_used + other:
        r, g, b = (x / 255 for x in hex_rgb(c))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h *= 360
        if s >= SAT_MIN and v >= VAL_MIN and (h <= RED_HUE[1] or h >= RED_HUE[0]):
            reds.append(c)
        if s >= SAT_MIN and v >= VAL_MIN and GREEN_HUE[0] <= h <= GREEN_HUE[1]:
            greens.append(c)
    say("R6", "FAIL" if reds and greens else "PASS",
        f"saturated red {reds or 'none'}, saturated green {greens or 'none'}")
    # INFO: category colours under simulated colour-vision deficiency (Machado et al. 2009, severity 1.0)
    sims = {"deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413],
                                      [-0.011820, 0.042940, 0.968881]]),
            "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216],
                                    [-0.003882, -0.048116, 1.051998]])}
    cat = [c for c in okabe_used if c != "#000000"]
    if len(cat) < 2:
        return
    worst = []
    for name, M in sims.items():
        labs = {}
        for c in cat:
            lin = np.clip(M @ np.array([_lin(x) for x in hex_rgb(c)]), 0, 1)
            labs[c] = _lab(lin)
        pairs = [(float(np.linalg.norm(labs[a] - labs[b])), a, b) for i, a in enumerate(cat) for b in cat[i + 1:]]
        d, a, b = min(pairs)
        worst.append(f"{name}: closest pair {a} / {b}, delta E {d:.1f}")
    say("R6", "INFO", "; ".join(worst))


def r7(f):
    hits = []
    s = Path(f["svg"]).read_text()
    for m in STAMP.finditer(s):
        hits.append(f"SVG: ...{s[max(0, m.start() - 20):m.end() + 20]!r}...")
    import fitz
    doc = fitz.open(f["pdf"])
    txt = "".join(p.get_text() for p in doc)
    for m in STAMP.finditer(txt):
        hits.append(f"PDF text: {txt[max(0, m.start() - 20):m.end() + 20]!r}")
    for k, v in (doc.metadata or {}).items():
        if v and STAMP.search(str(v)):
            hits.append(f"PDF metadata {k}: {v!r}")
    from PIL import Image
    import numpy as np
    im = Image.open(f["raster"])
    for k, v in (getattr(im, "text", None) or im.info).items():
        if isinstance(v, str) and STAMP.search(v):
            hits.append(f"raster text chunk {k}")
    # the raster against the PDF rasterised again at the raster's dpi
    dpi = (im.info.get("dpi") or (0, 0))[0]
    pix = doc[0].get_pixmap(dpi=round(dpi), alpha=False) if dpi else None
    if pix is None:
        hits.append("the raster states no dpi, so it cannot be compared with the PDF")
        cmp = "no comparison"
    elif (pix.width, pix.height) != im.size:
        hits.append(f"the raster is {im.size[0]} x {im.size[1]} px; the PDF at {dpi:.0f} dpi is {pix.width} x "
                    f"{pix.height} px (write the raster by rasterising the PDF)")
        cmp = "sizes differ"
    else:
        a = np.asarray(im.convert("RGB"), dtype=np.int16)
        b = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
        d = np.abs(a - b.astype(np.int16)).max(axis=2)
        n_bad = int((d > RASTER_DELTA).sum())
        cmp = (f"raster against the PDF rasterised again at {dpi:.0f} dpi: {n_bad} of {d.size:,} pixels differ by "
               f"more than {RASTER_DELTA} level{'s' if RASTER_DELTA != 1 else ''} (none allowed), largest difference "
               f"{int(d.max())}")
        if n_bad:
            ys, xs = np.nonzero(d > RASTER_DELTA)
            hits.append(cmp + f", in the box x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()} px: the raster shows "
                              f"something the PDF does not")
    say("R7", "FAIL" if hits else "PASS",
        "; ".join(hits[:4]) if hits else "no stamp, provenance or caption text inside the PDF, SVG or raster "
                                         f"(text, comments, metadata); {cmp}")


def sha256_file(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tag_of(name: str):
    """The '(provisional, n of m)' a file name carries, or None."""
    m = TAG.search(name)
    return m.group(1) if m else None


def r8(d: Path, n: int, panels, f):
    """R8. A main figure: parts (1) to (6). A Supplementary figure (SUPP; D94 O-b): (2) to (6) on its data workbook,
    part (1), the Source Data paperwork of [source_data], not applied."""
    import json
    if not SD_REQUIRED and not SUPP:
        say("R8", "INFO", "[source_data] per_main_figure is false: Source Data not checked")
        return
    provisional = f["provisional"]
    xs, folders, caps = sd_files(d, n)
    if not SD_CAPTION and not SUPP:
        caps = []
    found = [(p, "xlsx") for p in xs] + [(p, "csv") for p in folders]
    accepted = found if SUPP else [(p, k) for p, k in found if k in SD_FORMATS]
    want = [f"Fig. {n}{x}" for x in panels]
    probs, sheets = [], {}
    if len(accepted) != 1:
        say("R8", "FAIL", (f"want one data workbook named {sd_stem(n)!r} (xlsx, or a CSV folder by that name) for "
                           f"the consistency parts (2) to (6), which compare it with the numbers file and the plate (a "
                           f"Supplementary figure, D94 O-b)" if SUPP else
                           f"want one Source Data named {SD_NAME.format(n=n)!r} ([source_data] workbook_name; a CSV "
                           f"folder by its stem) in the lock's formats {SD_FORMATS}")
            + f"; found {[f'{p.name} ({k})' for p, k in found]}")
        return
    xs = [p for p, k in accepted if k == "xlsx"]
    if xs:
        from openpyxl import load_workbook
        wb = load_workbook(xs[0], read_only=True)
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            sheets[ws.title] = rows
        src = xs[0].name
    else:
        import csv
        fo = accepted[0][0]
        for p in sorted(fo.glob("*.csv")):
            with open(p) as fh:
                sheets[p.stem] = list(csv.reader(fh))
        src = fo.name + "/"
    if not SUPP:                                   # (1): one sheet per panel, each with a header and a data row
        if sorted(sheets) != sorted(want):
            probs.append(f"sheets {sorted(sheets)}, want one per panel {want}")
        for name, rows in sheets.items():
            if len(rows) < 2 or not all(rows[0]):
                probs.append(f"sheet {name}: no header or no data row")
    nf = d / side_name(n, "numbers")
    checked = 0
    numbers_stamp = None
    if not nf.exists():
        probs.append(f"{nf.name} missing: the Source Data values cannot be checked against the figure's numbers")
    else:
        nj = json.loads(nf.read_text())
        numbers_stamp = nj.get("stamp")
        want_sheets = nj["sheets"]
        if sorted(want_sheets) != sorted(sheets):
            probs.append(f"{nf.name} has sheets {sorted(want_sheets)}, the workbook {sorted(sheets)}")
        for name in sorted(set(want_sheets) & set(sheets)):
            w, rows = want_sheets[name], sheets[name]
            if list(rows[0]) != w["columns"]:
                probs.append(f"sheet {name}: columns differ from {nf.name}")
                continue
            if len(rows) - 1 != len(w["rows"]):
                probs.append(f"sheet {name}: {len(rows) - 1} rows, {nf.name} {len(w['rows'])}")
                continue
            bad = []
            for i, (got, exp) in enumerate(zip(rows[1:], w["rows"]), 2):
                for col, g, e in zip(w["columns"], got, exp):
                    checked += 1
                    if not same_value(g, e):
                        bad.append(f"row {i} {col}: {g!r} against {e!r}")
            if bad:
                probs.append(f"sheet {name}: {len(bad)} value(s) differ from {nf.name}, e.g. {bad[:2]}")
    if SD_CAPTION and not SUPP and len(caps) != 1:     # (1): the caption file
        probs.append(f"want one caption file {sd_stem(n) + ' caption'!r}.md ([source_data] caption), found "
                     f"{[c.name for c in caps]}")
    if SD_CAPTION and not SUPP and provisional and not any("rovisional" in c.read_text() for c in caps):
        probs.append("the plate is provisional and the caption does not say so")
    if SUPP and len(caps) > 1:                          # (3) to (5) read one caption
        probs.append(f"more than one caption file {sd_stem(n) + ' caption'!r}.md: {[c.name for c in caps]}")
    # (3) the provenance file: every file it lists, with its sha256; the plate, workbook, caption and numbers listed;
    # no figure or Source Data file outside it
    pf = d / side_name(n, "provenance")
    plate_stamp, n_hashed = None, 0
    if not pf.exists():
        probs.append(f"{pf.name} missing: the workbook cannot be tied to the plate")
    else:
        pj = json.loads(pf.read_text())
        plate_stamp = pj.get("stamp")
        listed = pj.get("files") or {}
        for name, h in sorted(listed.items()):
            p = d / name
            if not p.exists():
                probs.append(f"{pf.name} lists {name!r}, which is not in the folder")
            elif sha256_file(p) != h:
                probs.append(f"{name!r} differs from the sha256 {pf.name} records ({h[:12]})")
            else:
                n_hashed += 1
        need = [f["pdf"].name, f["svg"].name, f["raster"].name, nf.name] + [x.name for x in xs] + \
            [c.name for c in caps]
        unlisted = [x for x in need if x not in listed]
        stray = sorted(p.name for p in d.iterdir() if p.name.startswith((plate_name(n), sd_stem(n)))
                       and p.name not in listed)
        if unlisted:
            probs.append(f"{pf.name} does not list {unlisted}")
        stray = [x for x in stray if x not in unlisted]
        if stray:
            probs.append(f"files of the figure that {pf.name} does not list: {stray}")
    # (4) one data stamp: the numbers file's is the plate's, and the caption carries it
    if plate_stamp is not None and numbers_stamp != plate_stamp:
        probs.append(f"{nf.name} stamp {numbers_stamp!r} is not the plate's ({pf.name}) {plate_stamp!r}")
    if plate_stamp and caps and plate_stamp not in caps[0].read_text():
        probs.append(f"the caption does not carry the plate's data stamp {plate_stamp!r}")
    # (5) the names carry the plate's data state
    ptag = tag_of(f["pdf"].name)
    for p in xs + caps:
        if tag_of(p.name) != ptag:
            probs.append(f"{p.name!r} carries {tag_of(p.name)!r}, the plate {ptag!r}")
    if plate_stamp:
        if ptag:
            k, m = TAG.search(f["pdf"].name).group(2, 3)
            if not any(f"{a} of {b}" in plate_stamp for a, b in ((k, m), (f"{int(k):,}", f"{int(m):,}"))):
                probs.append(f"the plate's name says {k} of {m}, its stamp {plate_stamp!r}")
        elif plate_stamp.upper().startswith("PROVISIONAL"):
            probs.append(f"the plate is named final and its stamp reads {plate_stamp!r}")
    # (6) every number printed on the plate against the workbook: through the numbers file's "printed" map (SVG group
    # id of the text -> sheet, row or rows counted, format), each such text must read what the workbook gives, and
    # every SVG text holding a digit must be a tick label or in the map
    n_printed, n_other, n_pos, n_id = 0, 0, 0, 0
    if nf.exists():
        p6, n_printed, n_other, n_pos, n_id = printed_check(f["svg"], json.loads(nf.read_text()).get("printed"),
                                                            sheets)
        probs += p6
    say("R8", "FAIL" if probs else "PASS", "; ".join(probs[:6]) + (f" (and {len(probs) - 6} more)" if len(probs) > 6
                                                                    else "") + (" | " if probs else "") +
        ("a Supplementary figure, parts (2) to (6) only (D94 O-b): " if SUPP else "") +
        f"{src}: {', '.join(f'{k} ({len(v) - 1} rows)' for k, v in sheets.items())}; {checked} values compared "
        f"with {nf.name}; {n_hashed} files equal to the sha256 {pf.name} records; {n_printed} numbers printed on "
        f"the plate equal to the workbook cells they are written from (rounded half away from zero), {n_pos} of them "
        f"also at their place (a heatmap value inside its cell, a 'n =' label on its bar's row) and {n_id} tied by "
        f"id only, {n_other} other digit-bearing texts tick labels or declared fixed" +
        ("" if probs else f"; the numbers file, the provenance file and the caption carry one stamp; the plate, "
                          f"workbook and caption names carry {ptag!r}; caption "
                          f"{caps[0].name if caps else ('none (not required of a Supplementary figure)' if SUPP else 'not required ([source_data] caption false)')}"))


FIELD = re.compile(r"\{(\w+)(:[^{}]*)?\}")


def half_up(x, nd=1, sign=False):
    """A number as the figure scripts print it, rounded once: to 1e-9 first (so 54.25000000000001 is 54.25), then to
    nd decimals half away from zero (69.25 -> 69.3, 12.5 -> 13). The same rule as S447's half_up()."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    return f"{q:+.{nd}f}" if sign and q != 0 else f"{q:.{nd}f}"


class HalfUpFormatter(__import__("string").Formatter):
    """str.format, with half_up() for every fixed-point field ("{x:.0f}", "{x:+.1f}"): R8 (6) fills a printed
    number's format this way, as S447 writes it, so an exact quarter or a value with float noise is expected as the
    plate prints it."""

    def format_field(self, value, spec):
        m = re.fullmatch(r"(\+?)\.(\d+)f", spec)
        if m and isinstance(value, (int, float)) and not isinstance(value, bool):
            return half_up(value, int(m.group(2)), sign=bool(m.group(1)))
        return format(value, spec)


HALF_UP = HalfUpFormatter()


def printed_check(svg, printed, sheets):
    """R8 (6). printed: {svg group id: entry}, entry {"sheet", "row" (0-based data row), "format"} (the format filled
    from that workbook row), {"sheet", "where": {column: value}, "format"} ("{count}" = rows matching), {"sheet",
    "distinct": column, "format"} ("{count}" = distinct values of the column) or {"fixed": text, "why"}. The SVG
    text(s) in the group, joined by a line break, must equal the filled format. Every SVG <text> holding a digit must
    sit in a printed group or in a tick group (matplotlib's xtick_<k> / ytick_<k>). An entry may also say where its
    text must sit, checked from the SVG's geometry: "inside": {"gid", "path"}, the text's centre inside the box of the
    path-th <path> of the group with that id (Figure 6a: the heatmap cell drawn for the workbook row and column), or
    "on_row": {"gid"}, the text's vertical centre within the vertical extent of the element with that id (Figure 6d:
    the "n =" label on its own bar's row). The text's centre is its anchor turned into the middle of its advance
    width, and 0.35 of its font size above its baseline (the middle of a digit's height in Helvetica); positions are
    the text's own x, y and translate and the path's own points (no transform of an enclosing group is composed;
    S447 writes none). Returns (problems, numbers checked, other digit texts allowed, numbers checked at their place,
    numbers tied by id only)."""
    probs = []
    if not printed:
        return [f"the numbers file has no 'printed' map: the plate's printed numbers cannot be tied to the workbook"], 0, 0
    rows = {name: [dict(zip(r[0], x)) for x in r[1:]] for name, r in sheets.items() if r}
    root = ET.parse(svg).getroot()
    groups, loose, text_el = {}, [], {}

    def walk(el, ids):
        gid = el.get("id")
        ids = ids + [gid] if gid else ids
        if el.tag == SVG_NS + "text":
            txt = "".join(el.itertext())
            own = next((i for i in reversed(ids) if i in printed), None)
            if own:
                groups.setdefault(own, []).append(txt)
                text_el.setdefault(own, el)
            elif re.search(r"\d", txt):
                if any(re.fullmatch(r"[xy]tick_\d+", i) for i in ids):
                    loose.append(("tick", txt))
                else:
                    loose.append(("loose", txt))
            return
        for c in el:
            walk(c, ids)
    walk(root, [])
    untied = [t for k, t in loose if k == "loose"]
    if untied:
        probs.append(f"{len(untied)} text(s) holding a digit on the plate tied to no Source Data cell and not a tick "
                     f"label: {untied[:4]}")
    bad, n = [], 0
    for gid, e in printed.items():
        got = "\n".join(groups.get(gid, []))
        if gid not in groups:
            bad.append(f"{gid}: not on the plate")
            continue
        if "fixed" in e:
            if got != e["fixed"]:
                bad.append(f"{gid}: {got!r}, declared fixed {e['fixed']!r}")
            continue
        fmt = e.get("format", "")
        if FIELD.sub("", fmt).count("{") or FIELD.sub("", fmt).count("}"):
            bad.append(f"{gid}: format {fmt!r} not a plain field format")
            continue
        sh = rows.get(e.get("sheet"))
        if sh is None:
            bad.append(f"{gid}: sheet {e.get('sheet')!r} not in the workbook")
            continue
        try:
            if "row" in e:
                vals = sh[e["row"]]
            elif "where" in e:
                vals = {"count": sum(1 for r in sh if all(same_value(r.get(c), v) for c, v in e["where"].items()))}
            else:
                vals = {"count": len({r.get(e["distinct"]) for r in sh})}
            want = HALF_UP.format(fmt, **{k: ("" if v is None else v) for k, v in vals.items()})
        except (IndexError, KeyError, ValueError, TypeError) as x:
            bad.append(f"{gid}: cannot fill {fmt!r} from the workbook ({x!r})")
            continue
        n += 1
        if got != want:
            bad.append(f"{gid}: the plate reads {got!r}, the workbook ({e['sheet']}"
                       f"{', row ' + str(e['row'] + 2) if 'row' in e else ''}) gives {want!r}")
    if bad:
        probs.append(f"{len(bad)} printed number(s) differ from the workbook, e.g. {bad[:3]}")
    # where each number sits: inside its cell, or on its bar's row
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}
    misplaced, n_pos = [], 0
    for gid, e in printed.items():
        where = e.get("inside") or e.get("on_row")
        if not where or gid not in text_el:
            continue
        tgt = by_id.get(where.get("gid"))
        boxes = [b for b in (_path_box(p) for p in (tgt.iter(SVG_NS + "path") if tgt is not None else [])) if b]
        cx, cy = _text_centre(text_el[gid])
        if "inside" in e:
            k = where.get("path", 0)
            if k >= len(boxes):
                misplaced.append(f"{gid}: no path {k} in group {where.get('gid')!r}")
                continue
            x0, y0, x1, y1 = boxes[k]
            ok = x0 <= cx <= x1 and y0 <= cy <= y1
            what = f"outside path {k} of {where.get('gid')!r}, its cell"
        else:
            if not boxes:
                misplaced.append(f"{gid}: no element {where.get('gid')!r} to sit beside")
                continue
            y0, y1 = min(b[1] for b in boxes), max(b[3] for b in boxes)
            ok = y0 <= cy <= y1
            what = f"off the row of {where.get('gid')!r}, its bar"
        n_pos += 1
        if not ok:
            misplaced.append(f"{gid} ({groups[gid][0]!r}) centred at ({cx * MM:.1f}, {cy * MM:.1f}) mm, {what}")
    if misplaced:
        probs.append(f"{len(misplaced)} printed number(s) not at their place, e.g. {misplaced[:3]}")
    n_fixed = sum(1 for e in printed.values() if "fixed" in e)
    return probs, n, len(loose) - len(untied) + n_fixed, n_pos, n - n_pos


def _path_box(p):
    """The box (x0, y0, x1, y1) of a <path>'s own points, in SVG user units (pt), or None."""
    v = [float(x) for x in re.findall(r"-?[\d.]+(?:e-?\d+)?", p.get("d") or "")]
    if len(v) < 2:
        return None
    xs, ys = v[0::2], v[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def _text_centre(el):
    """The middle of a <text> in SVG user units: its anchor (x, y and a translate) turned into the middle of its
    advance width (matplotlib's metrics of its font), and 0.35 of its font size above the baseline."""
    st = _style(el)
    fs = float(re.match(r"[\d.]+", st.get("font-size", el.get("font-size", "0"))).group(0))
    x, y = float(el.get("x", 0)), float(el.get("y", 0))
    m = re.search(r"translate\(\s*([-\d.e]+)[ ,]+([-\d.e]+)\s*\)", el.get("transform") or "")
    if m:
        x, y = x + float(m.group(1)), y + float(m.group(2))
    txt = "".join(el.itertext())
    w = _width_pt(txt.split("\n")[0], st.get("font-family", "Helvetica").strip("'\""), fs,
                  st.get("font-weight", "") in ("700", "bold"))
    f = {"start": 0.5, "middle": 0.0, "end": -0.5}.get(st.get("text-anchor", "start"), 0.5)
    return x + f * w, y - 0.35 * fs


def same_value(got, exp):
    """A workbook cell against the numbers file: an empty cell is None; numbers equal to 1e-9; a CSV cell is text."""
    if got in (None, "") and exp in (None, ""):
        return True
    if isinstance(exp, bool) or isinstance(got, bool):
        return got == exp
    if isinstance(exp, (int, float)):
        try:
            g = float(got)
        except (TypeError, ValueError):
            return False
        return abs(g - exp) <= 1e-9 * max(1.0, abs(exp))
    return str(got) == str(exp)


def r9(d: Path, n: int, panels, provisional):
    p = d / "legend_draft.md"
    if not p.exists():
        say("R9", "FAIL", "legend_draft.md missing")
        return
    s = p.read_text()
    m = re.search(rf"\*\*{re.escape(plate_name(n))} \|\s*(.+?)\*\*", s)
    probs = []
    if not m:
        probs.append(f"no '**{plate_name(n)} | title**' line")
        title = ""
    else:
        title = m.group(1)
        if TITLE_PANEL.search(title):
            probs.append(f"the title names a panel: {title!r}")
    body = s[m.end():] if m else s
    missing = [x for x in panels if f"**{x}**," not in body]
    if PANELS_DEFINED and missing:
        probs.append(f"panels not defined: {missing}")
    n_trigger = N_WHEN.search(body)
    if N_EXACT and n_trigger and not re.search(r"\bn = \d", body):
        probs.append(f"no 'n = <number>', and the legend names a statistic ({n_trigger.group(0)!r}; "
                     f"[statistics] n_when)")
    ranges = [m.group(0) for m in RANGE.finditer(body)] if N_EXACT else []
    if ranges:
        probs.append(f"n given as a range: {ranges[:3]}")
    # the sidedness, where the legend draws an interval or a test (D122): sidedness_phrase, or the same phrase with
    # "two" read as "one" (editor row 46 asks "one-sided or two-sided"; a one-sided test says "one-sided")
    trigger = SIDED_WHEN.search(body)
    sided = (SIDEDNESS, SIDEDNESS.replace("two", "one", 1))
    if trigger and not any(x in body for x in sided):
        probs.append(f"'{SIDEDNESS}' not stated, and the legend describes an interval or a test "
                     f"({trigger.group(0)!r}; [statistics] sidedness_when)")
    # the legend's length: the title line to the end of legend_draft.md (the lines above it are the file's header).
    # The journal: "Legends should be under 350 words each", so a legend of words_under words or more is too long
    n_words = len((s[m.start():] if m else s).split())
    too_long = n_words >= WORDS_UNDER
    long_msg = f"the legend has {n_words} words; the lock wants under {WORDS_UNDER} ([legend] words_under)"
    if too_long and not provisional:
        probs.append(long_msg)
    # a provisional plate need not say "provisional" in its legend (D122, Q3): the file name's suffix (R1) and the
    # data stamp below carry it
    pf = d / side_name(n, "provenance")
    if provisional and pf.exists():
        import json
        st = json.loads(pf.read_text()).get("stamp")
        if st and st not in s:
            probs.append(f"legend_draft.md does not carry the plate's data stamp {st!r}")
    say("R9", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"(heuristic) title {title!r}" + ("" if probs else
                                          (f"; panels {', '.join(panels)} defined" if PANELS_DEFINED else "") +
                                          ((f"; an 'n = <number>' present ({n_trigger.group(0)!r})" if n_trigger
                                            else "; no mean, median, interval or test named, so no 'n =' asked") +
                                           f"; no count as a range in the forms seen ({RANGE_FORMS})" if N_EXACT else "") +
                                          (f"; {next(x for x in sided if x in body)} stated "
                                           f"({trigger.group(0)!r})" if trigger else
                                           "; no interval or test described, so no sidedness asked") +
                                          f"; {n_words} words"))
    if too_long and provisional:
        say("R9", "WARN", long_msg + " (a provisional plate: legends are shrunk later, D84 Q158; a final plate fails)")


SVG_NS, XLINK = "{http://www.w3.org/2000/svg}", "{http://www.w3.org/1999/xlink}href"
MM = 25.4 / 72                                     # mm per pt (the SVG user unit and the PDF unit are both pt)
TEXT_TOL_FIRST_MM, TEXT_TOL_MM, TEXT_TOL_LIG_MM, SHAPE_TOL_PT = 0.25, 0.3, 0.6, 0.3


def _style(el):
    return {a.strip(): b.strip() for a, b in (kv.split(":", 1) for kv in (el.get("style") or "").split(";")
                                                if ":" in kv)}


def _hexn(c):
    if c is None or c.strip() in ("none", ""):
        return None
    return "#" + "".join(f"{x:02X}" for x in hex_rgb(c.strip()))


_T2P = None


def _width_pt(s, family, size, bold):
    """The advance width of s in pt, with matplotlib's metrics of the named font (the font the PDF embeds)."""
    global _T2P
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    _T2P = _T2P or TextToPath()
    w, _, _ = _T2P.get_text_width_height_descent(s, FontProperties(family=family, weight="bold" if bold else "normal",
                                                                   size=size), ismath=False)
    return w


def svg_chars(root):
    """Every non-space character of every SVG <text>: (char, x, y, size pt, rotation deg, colour, bold, index in
    its text, the character before it), x and y the baseline start of the character in pt from the page's top left. A text's anchor
    (text-anchor start, middle or end, at x/y or a translate) is turned into its start point with the font's advance
    widths; each later character is placed at the start plus the width of the text before it."""
    k, _, _ = svg_scale(root)
    out = []

    def walk(el, inh):
        if el.tag in (SVG_NS + "defs", SVG_NS + "clipPath"):
            return
        st = {**inh, **_style(el)}
        for attr in ("font-size", "font-weight", "fill", "font-family", "text-anchor"):
            if el.get(attr):
                st[attr] = el.get(attr)
        if el.tag == SVG_NS + "text":
            txt = "".join(el.itertext())
            fs = float(re.match(r"[\d.]+", st.get("font-size", "0")).group(0)) * k / MM
            fam = st.get("font-family", "Helvetica").strip("'\"")
            bold = st.get("font-weight", "") in ("700", "bold")
            tr = el.get("transform") or ""
            x, y, rot = float(el.get("x", 0)), float(el.get("y", 0)), 0.0
            m = re.search(r"translate\(\s*([-\d.e]+)[ ,]+([-\d.e]+)\s*\)", tr)
            if m:
                x, y = x + float(m.group(1)), y + float(m.group(2))
            m = re.search(r"rotate\(\s*([-\d.e]+)", tr)
            if m:
                rot = -float(m.group(1))
            col = _hexn(st.get("fill", "#000000"))
            f = {"start": 0.0, "middle": 0.5, "end": 1.0}.get(st.get("text-anchor", "start"), 0.0)
            ca, sa = math.cos(math.radians(rot)), -math.sin(math.radians(rot))
            w = _width_pt(txt, fam, fs, bold) if f else 0.0
            x0, y0 = (x - f * w * ca) * k / MM, (y - f * w * sa) * k / MM
            n = 0
            for i, ch in enumerate(txt):
                if ch.isspace():
                    continue
                p = _width_pt(txt[:i], fam, fs, bold) if i else 0.0
                out.append((ch, x0 + p * ca, y0 + p * sa, round(fs, 2), round(rot) % 360, col, bold, n,
                            txt[i - 1] if i else ""))
                n += 1
            return
        for c in el:
            walk(c, st)
    walk(root, {})
    return out


def pdf_chars(pdf):
    """Every non-space character on the PDF's page: (char, x, y, size pt, rotation deg, colour, bold), x and y its
    baseline origin in pt from the page's top left (PyMuPDF rawdict)."""
    import fitz
    out = []
    for b in fitz.open(pdf)[0].get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            rot = round(math.degrees(math.atan2(-ln["dir"][1], ln["dir"][0]))) % 360
            for sp in ln["spans"]:
                for c in sp["chars"]:
                    if not c["c"].isspace():
                        out.append((c["c"], c["origin"][0], c["origin"][1], round(sp["size"], 2), rot,
                                    f"#{sp['color']:06X}", bool(sp["flags"] & 16)))
    return out


def svg_shapes(root):
    """Every painted SVG path or marker (<use>), split into its fill and its stroke: (colour, 'f' or 's', x0, y0, x1,
    y1), the box of the path's points in pt. A paint with opacity 0, or a stroke of width 0, is not painted."""
    defs = {el.get("id"): el for el in root.iter() if el.tag == SVG_NS + "path" and el.get("id")}
    out = []

    def pts(d):
        v = [float(x) for x in re.findall(r"-?[\d.]+(?:e-?\d+)?", d)]
        return list(zip(v[0::2], v[1::2]))

    def walk(el, inh):
        if el.tag in (SVG_NS + "defs", SVG_NS + "clipPath", SVG_NS + "text"):
            return
        st = {**inh, **_style(el)}
        for attr in ("fill", "stroke"):
            if el.get(attr):
                st[attr] = el.get(attr)
        if el.tag in (SVG_NS + "path", SVG_NS + "use"):
            if el.tag == SVG_NS + "use":
                ref = defs.get((el.get(XLINK) or "").lstrip("#"))
                ox, oy = float(el.get("x", 0)), float(el.get("y", 0))
                P = [(x + ox, y + oy) for x, y in pts(ref.get("d"))] if ref is not None else []
            else:
                P = pts(el.get("d") or "")
            fill, stroke = _hexn(st.get("fill", "#000000")), _hexn(st.get("stroke"))
            num = lambda key: float(re.match(r"-?[\d.]+", st[key]).group(0)) if st.get(key) else None
            if num("stroke-width") == 0 or num("stroke-opacity") == 0:
                stroke = None
            if num("fill-opacity") == 0:
                fill = None
            if P:
                box = (min(p[0] for p in P), min(p[1] for p in P), max(p[0] for p in P), max(p[1] for p in P))
                if fill:
                    out.append((fill, "f") + box)
                if stroke:
                    out.append((stroke, "s") + box)
        for c in el:
            walk(c, st)
    walk(root, {})
    return out


def pdf_shapes(pdf):
    """Every PDF drawing (PyMuPDF get_drawings), split as svg_shapes splits them."""
    import fitz
    out = []
    h = lambda c: "#" + "".join(f"{round(x * 255):02X}" for x in c)
    for d in fitz.open(pdf)[0].get_drawings():
        r, t = d["rect"], d["type"]
        if "f" in t and d.get("fill") is not None and (d.get("fill_opacity") is None or d["fill_opacity"] > 0):
            out.append((h(d["fill"]), "f", r.x0, r.y0, r.x1, r.y1))
        if "s" in t and d.get("color") is not None and (d.get("stroke_opacity") is None or d["stroke_opacity"] > 0):
            out.append((h(d["color"]), "s", r.x0, r.y0, r.x1, r.y1))
    return out


def _match(A, B, key, dist, tol):
    """Pair each element of A with the nearest unpaired element of B carrying the same key, within tol. Returns the
    unpaired of A, the unpaired of B and the largest distance paired."""
    from collections import defaultdict
    pool = defaultdict(list)
    for b in B:
        pool[key(b)].append(b)
    miss, worst = [], 0.0
    for a in A:
        cand = pool.get(key(a), [])
        best = min(cand, key=lambda b: dist(a, b), default=None)
        if best is None or dist(a, best) > tol(a):
            miss.append(a)
            continue
        worst = max(worst, dist(a, best))
        cand.remove(best)
    return miss, [b for v in pool.values() for b in v], worst


R10_SCOPE = ("compared: each character's (character, size, rotation, fill colour, weight) and baseline position from "
             "the <text>'s own x, y and translate or rotate, and each painted fill and stroke's colour and the box of "
             "the path's own points; not compared: transforms of enclosing groups or of paths, opacity (a path's or "
             "marker's own fill-opacity or stroke-opacity of 0 removes that paint; text opacity and the opacity property are "
             "not read), visibility, display, paint order, stroke width (other than 0), dashes, clip paths, font family. The "
             "PDF and PNG are held equal by R7; the SVG is checked against the PDF for text and shape positions only")


def r10(f):
    """The SVG's text and painted shapes against the PDF's, element by element and position by position. Text: every character
    keyed by (character, size, rotation, colour, weight) must have its partner at the same place on the other page,
    within TEXT_TOL_FIRST_MM for a text's first character and TEXT_TOL_MM for later ones (the SVG side places later
    characters with matplotlib's advance widths, which differ from the PDF's by kerning, up to 0.22 mm on Figure 6 of
    17 October), TEXT_TOL_LIG_MM for a character after an "f" (the PDF reports the second character of an "fl" or
    "fi" ligature at the ligature's origin, 0.56 mm from where the SVG's advance widths put it). Shapes:
    every fill and every stroke keyed by its colour must have a partner of that colour whose box is within
    SHAPE_TOL_PT on each edge. So a swapped pair of labels or values, a label altered, a text added and a shape
    recoloured, even to a colour the plate already uses, fail.
    WHAT IS COMPARED, exactly (R10_SCOPE). The SVG side is read from each <text>'s own x, y and transform (translate,
    rotate) and each <path>'s own points (a <use>'s x and y); a transform on an enclosing group, or on a path, is not
    composed. Not compared: opacity (other than a path's or marker's own fill-opacity or stroke-opacity of 0, which removes that paint; text opacity and the opacity property are not read), visibility
    and display, paint order, stroke width (other than 0), dashes, clip paths, and font family. So an edit made in an
    SVG editor through one of these can pass R10. The PNG is the PDF rasterised (R7 holds them equal pixel by pixel);
    the SVG is held to the PDF for its text and shape positions only. The gates aim at a builder's faults and a
    figure workflow's edits (matplotlib output, a stale file, a mis-mapped number), not every hand edit."""
    root = ET.parse(f["svg"]).getroot()
    sc, pc = sorted(svg_chars(root), key=lambda c: c[7]), pdf_chars(f["pdf"])
    d_ch = lambda a, b: math.hypot(a[1] - b[1], a[2] - b[2]) * MM
    ms, mp, wc = _match(sc, pc, lambda c: c[0:1] + c[3:7], d_ch,
                        lambda a: TEXT_TOL_FIRST_MM if a[7] == 0 else TEXT_TOL_LIG_MM if a[8] == "f" else TEXT_TOL_MM)
    ss, ps = svg_shapes(root), pdf_shapes(f["pdf"])
    d_sh = lambda a, b: max(abs(a[i] - b[i]) for i in (2, 3, 4, 5))
    ns, np_, wsh = _match(ss, ps, lambda e: e[:2], d_sh, lambda a: SHAPE_TOL_PT)
    probs = []
    fmt_c = lambda c: f"{c[0]!r} at ({c[1] * MM:.1f}, {c[2] * MM:.1f}) mm {c[5]}"
    fmt_s = lambda e: f"{e[1]} {e[0]} box ({e[2] * MM:.1f}, {e[3] * MM:.1f})-({e[4] * MM:.1f}, {e[5] * MM:.1f}) mm"
    if ms or mp:
        probs.append(f"text: {len(ms)} SVG character(s) with no PDF partner at their place, e.g. "
                     f"{[fmt_c(c) for c in ms[:3]]}; {len(mp)} PDF character(s) unpaired, e.g. "
                     f"{[fmt_c(c) for c in mp[:3]]}")
    if ns or np_:
        probs.append(f"shapes: {len(ns)} SVG fill(s) or stroke(s) with no PDF partner of that colour at that box, "
                     f"e.g. {[fmt_s(e) for e in ns[:2]]}; {len(np_)} PDF unpaired, e.g. {[fmt_s(e) for e in np_[:2]]}")
    say("R10", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"{len(sc)} SVG and {len(pc)} PDF characters paired by (character, size, rotation, colour, weight) and "
        f"position (largest distance {wc:.2f} mm; allowed {TEXT_TOL_FIRST_MM} mm for a text's first character, "
        f"{TEXT_TOL_MM} mm after it, {TEXT_TOL_LIG_MM} mm after an 'f'); {len(ss)} SVG and {len(ps)} PDF fills "
        f"and strokes paired by colour and box (largest edge difference {wsh:.3f} pt, allowed {SHAPE_TOL_PT} pt). "
        f"Scope: {R10_SCOPE}")


def _rel_lum(rgb01):
    """WCAG 2.1 relative luminance of an sRGB colour given as three values from 0 to 1."""
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb01]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _rgb3(c):
    if c is None:
        return None
    c = tuple(c)
    return c * 3 if len(c) == 1 else (c if len(c) == 3 else None)


def r11(f):
    """Text contrast, in the PDF as printed: each text span's colour against the fill painted under its centre (the
    last filled drawing before it in the page's paint order whose box holds the span's centre; the page white where
    none does). The WCAG 2.1 ratio must be above the lock's contrast_min_ratio. Coloured text (not grey, black or
    white) is a WARN: the guide asks to avoid it unless colour carries meaning. R10 holds the SVG's text colours and
    positions to the PDF's, so the PDF is read alone."""
    import fitz
    pg = fitz.open(f["pdf"])[0]
    fills = sorted(((d["seqno"], d["rect"], _rgb3(d["fill"])) for d in pg.get_drawings()
                    if "f" in d["type"] and _rgb3(d.get("fill")) is not None
                    and (d.get("fill_opacity") is None or d["fill_opacity"] > 0)), key=lambda t: t[0])
    low, coloured, worst, n = [], set(), None, 0
    for sp in pg.get_texttrace():
        txt = "".join(chr(c[0]) for c in sp["chars"]).strip()
        fg = _rgb3(sp["color"])
        if not txt or fg is None:
            continue
        n += 1
        x0, y0, x1, y1 = sp["bbox"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bg = (1.0, 1.0, 1.0)
        for seq, r, col in fills:
            if seq > sp["seqno"]:
                break
            if r.x0 <= cx <= r.x1 and r.y0 <= cy <= r.y1:
                bg = col
        la, lb = _rel_lum(fg), _rel_lum(bg)
        ratio = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
        h = lambda c: "#" + "".join(f"{round(x * 255):02X}" for x in c)
        if worst is None or ratio < worst[0]:
            worst = (ratio, txt, h(fg), h(bg))
        if ratio < CONTRAST_MIN:
            low.append(f"{txt[:24]!r} {h(fg)} on {h(bg)} {ratio:.2f}:1")
        if not is_grey(tuple(round(x * 255) for x in fg)):
            coloured.add(h(fg))
    say("R11", "FAIL" if low else "PASS",
        (f"{len(low)} text span(s) under the lock's {CONTRAST_MIN:g}:1 against what is painted under them, e.g. "
         f"{low[:4]} | " if low else "") +
        f"{n} text spans; lowest contrast {worst[0]:.2f}:1 ({worst[1][:24]!r}, {worst[2]} on {worst[3]}); lock: at least "
        f"{CONTRAST_MIN:g}:1" if worst else "no text in the PDF")
    if coloured and COLOURED_TEXT != "allowed":
        say("R11", "WARN" if COLOURED_TEXT == "avoid" else "FAIL",
            f"coloured text {sorted(coloured)}: the guide asks for black or white text unless colour carries meaning "
            f"([type] coloured_text {COLOURED_TEXT!r})")


def r12(f):
    """Line widths: every painted stroke at least the lock's line_min_pt, in the PDF (a stroke of width 0 is a
    hairline, the thinnest the device draws, and fails) and in the SVG (stroke-width read with inheritance, 1 user
    unit where none is set; a width of 0 there paints nothing)."""
    import fitz
    thin_p, wp = [], []
    for d in fitz.open(f["pdf"])[0].get_drawings():
        if "s" in d["type"] and d.get("color") is not None and (d.get("stroke_opacity") is None
                                                                   or d["stroke_opacity"] > 0):
            w = d.get("width") or 0.0
            wp.append(w)
            if w < LINE_MIN_PT - 1e-6:
                thin_p.append(round(w, 3))
    root = ET.parse(f["svg"]).getroot()
    k, _, _ = svg_scale(root)
    thin_s, ws = [], []

    def walk(el, inh):
        if el.tag in (SVG_NS + "defs", SVG_NS + "clipPath", SVG_NS + "text"):
            return
        st = {**inh, **_style(el)}
        for attr in ("stroke", "stroke-width", "stroke-opacity"):
            if el.get(attr):
                st[attr] = el.get(attr)
        if el.tag in (SVG_NS + "path", SVG_NS + "use", SVG_NS + "line", SVG_NS + "polyline", SVG_NS + "rect",
                      SVG_NS + "circle", SVG_NS + "ellipse", SVG_NS + "polygon"):
            num = lambda key, dflt: float(re.match(r"-?[\d.]+", st[key]).group(0)) if st.get(key) else dflt
            if _hexn(st.get("stroke")) and num("stroke-opacity", 1.0) > 0 and num("stroke-width", 1.0) > 0:
                w = num("stroke-width", 1.0) * k / MM
                ws.append(w)
                if w < LINE_MIN_PT - 1e-6:
                    thin_s.append(round(w, 3))
        for c in el:
            walk(c, st)
    walk(root, {})
    probs = []
    if thin_p:
        probs.append(f"{len(thin_p)} PDF stroke(s) under the lock's {LINE_MIN_PT:g} pt: widths {sorted(set(thin_p))}")
    if thin_s:
        probs.append(f"{len(thin_s)} SVG stroke(s) under {LINE_MIN_PT:g} pt: widths {sorted(set(thin_s))}")
    say("R12", "FAIL" if probs else "PASS", "; ".join(probs) + (" | " if probs else "") +
        f"{len(wp)} PDF and {len(ws)} SVG strokes, thinnest {min(wp, default=0):.3f} pt and {min(ws, default=0):.3f} "
        f"pt; lock: every line at least {LINE_MIN_PT:g} pt")


def manual_keys():
    """[section] key of every line of FIGURE_LOCK.toml whose comment says MANUAL: the rules a person checks."""
    out, sec = [], ""
    for ln in LOCK_PATH.read_text().splitlines():
        m = re.match(r"\[(\w+)\]", ln)
        if m:
            sec = m.group(1)
        m = re.match(r"(\w+)\s*=.*#.*\bMANUAL\b", ln)
        if m:
            out.append(f"{sec}.{m.group(1)}")
    return out


def check(d: Path, n: int, quiet=False):
    """Every rule on one folder. Returns the rules that FAIL."""
    global RESULTS
    RESULTS = []
    if not quiet:
        print(f"S448 figure rules, {plate_name(n)}, {d}" + (" (a Supplementary figure: the drawing rules, D92 Q194, "
                                                             "and R8's consistency parts, D94 O-b)" if SUPP else ""))
        print(f"lock {FIGURE_LOCK.relative_to(FIGURE_LOCK.parents[1])} sha256 {LOCK_SHA256}, status "
              f"{LOCK['status']!r}")
    figs, pat = find_files(d, n)
    f = r1(figs, pat, n)
    if f is None:
        return ["R1"]
    r2(f)
    panels = r3(f)
    r4(f)
    okabe_used, other = r5(f)
    r6(okabe_used, other)
    r7(f)
    r8(d, n, panels, f)                     # a Supplementary figure: parts (2) to (6) only (D94 O-b)
    r9(d, n, panels, f["provisional"])
    r10(f)
    r11(f)
    r12(f)
    for rule, what in (("E2", "every point value drawn with error bars also shows its individual points (or is a "
                                "box or dot plot); tied points are spread at right angles to the value axis, never "
                                "along it, so each sits at its exact value"),
                       ("E6", "the legend is informative, clear and not unnecessarily long"),
                       ("E7", "every n is the precise value with its unit, never a range (several units with "
                              "different counts are listed, e.g. '20 operations: 15 with 4 attempts, 5 with 5'); "
                              "every point estimate, interval and test is defined (a pass rate over several attempts "
                              "per unit is the mean of the units' shares, experiments/LIST.md Rule 2)"),
                       ("E8", "the plate, its legend and the text agree (the figure's claims list, each cited "
                              "sentence mapped to the redraw's panel)"),
                       ("E4", "the Data Availability statement carries the Source Data sentence"),
                       ("LOCK", "the keys FIGURE_LOCK.toml marks MANUAL: " + ", ".join(
                           k for k in manual_keys() if not (SUPP and k.startswith("source_data."))))):
        if SUPP and rule == "E4":
            continue                              # Source Data and its sentence: main figures only (D92 Q194)
        say(rule, "MANUAL", what)
    return list(dict.fromkeys(r for r, st in RESULTS if st == "FAIL"))


# ---------------------------------------------------------------------------------------------------------------
# --mutants: the checker checked. Each mutant alters one copy of the folder once; the rule built for it must FAIL
# ---------------------------------------------------------------------------------------------------------------
def _plate(d: Path, n: int, ext):
    return next(p for p in d.iterdir() if re.match(rf"^{re.escape(plate_name(n))}{_SUFFIX}\.{ext}$", p.name))


def m_faint_stamp(d, n, stale):
    """'PROVISIONAL' in (226, 226, 226) on white paper: an empty white box of the plate is found, so every pixel the
    stamp changes differs by 29 levels, under the 32 that R7 allowed until round 3."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    p = _plate(d, n, "png")
    im = Image.open(p)
    dpi = im.info.get("dpi")
    im = im.convert("RGB")
    try:
        font = ImageFont.load_default(size=120)
    except TypeError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(im)
    x0, y0, x1, y1 = draw.textbbox((0, 0), "PROVISIONAL", font=font)
    w, h = x1 - x0 + 40, y1 - y0 + 40
    ink = (np.asarray(im.convert("L")) < 255).astype(np.int64)
    S = np.pad(ink.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    spot = None
    for y in range(0, ink.shape[0] - h, 25):
        for x in range(0, ink.shape[1] - w, 25):
            if S[y + h, x + w] - S[y, x + w] - S[y + h, x] + S[y, x] == 0:
                spot = (x, y)
                break
        if spot:
            break
    if spot is None:
        return None
    before = np.asarray(im, dtype=np.int16).copy()
    draw.text((spot[0] + 20 - x0, spot[1] + 20 - y0), "PROVISIONAL", fill=(226, 226, 226), font=font)
    diff = np.abs(np.asarray(im, dtype=np.int16) - before).max(axis=2)
    im.save(p, dpi=dpi)
    old = (diff > 32).sum() / diff.size > 1e-5
    return (f"'PROVISIONAL' drawn on the PNG in (226, 226, 226) on white paper at x {spot[0]}, y {spot[1]} px, the "
            f"PNG's dpi kept: {int((diff > 0).sum())} pixels changed, largest change {int(diff.max())} levels, so the "
            f"earlier tolerance (more than 0.001% of pixels over 32 levels) would {'FAIL' if old else 'PASS'} it")


def m_stale(d, n, stale, rename=False):
    if stale is None:
        return None
    for p in sd_files(d, n)[0] + [d / side_name(n, "numbers")]:
        p.unlink()
    wb = sd_files(stale, n)[0][0]
    name = wb.name
    if rename:
        ptag = tag_of(_plate(d, n, "pdf").name)
        name = TAG.sub(f"({ptag})", name) if ptag else name
    import shutil
    shutil.copy2(wb, d / name)
    shutil.copy2(stale / side_name(n, "numbers"), d / side_name(n, "numbers"))
    return f"{stale.name}'s workbook {wb.name!r} (as {name!r}) and its {side_name(n, 'numbers')} in place of the plate's"


def m_zeroed(d, n, stale):
    from openpyxl import load_workbook
    p = sd_files(d, n)[0][0]
    wb = load_workbook(p)
    for ws in wb.worksheets:
        for row in ws.iter_rows(min_row=2):
            for c in row:
                if isinstance(c.value, (int, float)) and not isinstance(c.value, bool) and c.value != 0:
                    old, c.value = c.value, 0
                    wb.save(p)
                    return f"sheet {ws.title} cell {c.coordinate}: {old} set to 0"
    return None


def m_altered_label(d, n, stale):
    p = _plate(d, n, "svg")
    s = p.read_text()
    m = re.search(r"(<text\b[^>]*>)([^<]*[A-Za-z]{3,}[^<]*)(</text>)", s)
    old = m.group(2)
    new = re.sub(r"[A-Za-z]{3,}", lambda w: w.group(0) + "s", old, count=1)
    p.write_text(s[:m.start(2)] + new + s[m.end(2):])
    return f"SVG text {old.strip()!r} changed to {new.strip()!r}"


def m_added_text(d, n, stale):
    p = _plate(d, n, "svg")
    s = p.read_text()
    i = s.rfind("</svg>")
    p.write_text(s[:i] + '<text x="10" y="20" style="font: 7px \'Helvetica\'; fill: #000000">PRELIMINARY / NOT FOR '
                         'CITATION</text>\n' + s[i:])
    return "SVG <text> 'PRELIMINARY / NOT FOR CITATION' added"


def m_colour(d, n, stale):
    p = _plate(d, n, "svg")
    s = p.read_text()
    m = re.search(r"fill:\s*(#[0-9a-fA-F]{6})", s)
    old = m.group(1)
    r, g, b = hex_rgb(old)
    new = "#{:02X}{:02X}{:02X}".format(r, g, b + 1 if b < 255 else b - 1)
    p.write_text(s[:m.start(1)] + new + s[m.end(1):])
    return f"the first SVG fill {old} changed to {new}"


def _swap_texts(d, n, pick):
    """Swap the contents of two SVG <text> elements chosen by pick(list of contents) -> (i, j)."""
    p = _plate(d, n, "svg")
    s = p.read_text()
    ms = list(re.finditer(r"(<text\b[^>]*>)([^<]*)(</text>)", s))
    ij = pick([m.group(2) for m in ms])
    if ij is None:
        return None
    i, j = sorted(ij)
    a, b = ms[i], ms[j]
    s = s[:a.start(2)] + b.group(2) + s[a.end(2):b.start(2)] + a.group(2) + s[b.end(2):]
    p.write_text(s)
    return f"SVG texts {a.group(2)!r} and {b.group(2)!r} swapped (their positions kept)"


def m_swap_labels(d, n, stale):
    def pick(ts):
        if "low" in ts and "high" in ts:
            return ts.index("low"), ts.index("high")
        words = [i for i, t in enumerate(ts) if re.fullmatch(r"[a-z]+", t)]
        return next(((i, j) for i in words for j in words if ts[i] != ts[j]), None)
    return _swap_texts(d, n, pick)


def m_swap_values(d, n, stale):
    def pick(ts):
        if "90" in ts and "35" in ts:
            return ts.index("90"), ts.index("35")
        nums = [i for i, t in enumerate(ts) if re.fullmatch(r"\d+", t)]
        return next(((i, j) for i in nums for j in nums if ts[i] != ts[j]), None)
    return _swap_texts(d, n, pick)


def m_existing_colour(d, n, stale):
    """A heatmap cell (a path filled and stroked white) recoloured to the fill of another such cell: a colour the
    plate already uses, so R5 and a colour-set comparison pass."""
    p = _plate(d, n, "svg")
    s = p.read_text()
    ms = list(re.finditer(r'<path d="[^"]*"[^>]*style="fill: (#[0-9a-fA-F]{6}); stroke: #ffffff', s))
    a = ms[0] if ms else None
    b = next((m for m in ms if a is not None and m.group(1).lower() != a.group(1).lower()), None)
    if b is None:
        return None
    p.write_text(s[:a.start(1)] + b.group(1) + s[a.end(1):])
    return f"an SVG cell filled {a.group(1)} recoloured to {b.group(1)}, a fill the plate already uses"


def _rehash(d, n, names):
    import json
    pf = d / side_name(n, "provenance")
    pj = json.loads(pf.read_text())
    for nm in names:
        pj["files"][nm] = sha256_file(d / nm)
    pf.write_text(json.dumps(pj, indent=1))


def _consistent_edit(d, n, sheet_pick, col, change):
    """Change one printed cell in the workbook and the numbers file alike, and record both files' new sha256 in
    the provenance file: (1) to (5) of R8 still pass, so only (6), the plate against the workbook, can catch it."""
    import json
    from openpyxl import load_workbook
    nf = d / side_name(n, "numbers")
    nj = json.loads(nf.read_text())
    entry = next((e for e in nj.get("printed", {}).values() if e.get("sheet") == sheet_pick and "row" in e
                  and "{" + col in e.get("format", "")), None)
    if entry is None:
        return None
    sh = nj["sheets"][sheet_pick]
    ci, ri = sh["columns"].index(col), entry["row"]
    old = sh["rows"][ri][ci]
    new = change(old)
    sh["rows"][ri][ci] = new
    nf.write_text(json.dumps(nj, indent=1))
    wbp = sd_files(d, n)[0][0]
    wb = load_workbook(wbp)
    wb[sheet_pick].cell(row=ri + 2, column=ci + 1).value = new
    wb.save(wbp)
    _rehash(d, n, [wbp.name, nf.name])
    return f"sheet {sheet_pick} row {ri + 2} {col}: {old} -> {new} in the workbook and the numbers file alike " \
           f"(provenance re-hashed), the plate unchanged"


def m_untied_number(d, n, stale):
    p = _plate(d, n, "svg")
    s = p.read_text()
    i = s.rfind("</svg>")
    p.write_text(s[:i] + '<g id="text_extra"><text x="300" y="20" style="font: 7px \'Helvetica\'; fill: #000000">'
                         '42</text></g>\n' + s[i:])
    return "SVG <text> '42' added in a group of its own (no tick, no printed id)"


def _swap_positions(d, n, which):
    """Two printed numbers (by the numbers file's map) of different values trade positions: the x, y and transform
    attributes of their <text> elements are exchanged, each text keeping its group id and its value."""
    import json
    printed = json.loads((d / side_name(n, "numbers")).read_text()).get("printed") or {}
    p = _plate(d, n, "svg")
    s = p.read_text()
    pat = lambda gid: re.compile(rf'(<g id="{gid}">\s*<text\b)([^>]*)(>)([^<]*)(</text>)')
    cands = []
    for gid, e in printed.items():
        if which in e:
            m = pat(gid).search(s)
            if m:
                cands.append((gid, m))
    pair = next(((a, b) for i, a in enumerate(cands) for b in cands[i + 1:] if a[1].group(4) != b[1].group(4)), None)
    if pair is None:
        return None
    (ga, ma), (gb, mb) = pair
    pos = lambda attrs: {k: re.search(rf'\b{k}="([^"]*)"', attrs).group(1) for k in ("x", "y", "transform")
                         if re.search(rf'\b{k}="', attrs)}
    pa, pb = pos(ma.group(2)), pos(mb.group(2))

    def put(attrs, new):
        for k, v in new.items():
            attrs = re.sub(rf'\b{k}="[^"]*"', f'{k}="{v}"', attrs)
        return attrs
    for m, new in sorted(((ma, pb), (mb, pa)), key=lambda t: -t[0].start(2)):
        s = s[:m.start(2)] + put(m.group(2), new) + s[m.end(2):]
    p.write_text(s)
    return (f"SVG texts {ga} ({ma.group(4)!r}) and {gb} ({mb.group(4)!r}) trade positions, each keeping its id and "
            f"value")


def m_low_contrast(d, n, stale):
    """A light grey label written into the PDF on white paper: contrast about 2.2:1."""
    import fitz
    import os
    p = _plate(d, n, "pdf")
    doc = fitz.open(p)
    doc[0].insert_text((6, 12), "low contrast label", fontsize=8, color=(0.7, 0.7, 0.7))
    tmp = p.with_suffix(".tmp.pdf")
    doc.save(tmp)
    doc.close()
    os.replace(tmp, p)
    return "PDF text 'low contrast label' in (179, 179, 179) on white added"


def m_thin_line_pdf(d, n, stale):
    import fitz
    import os
    p = _plate(d, n, "pdf")
    doc = fitz.open(p)
    doc[0].draw_line(fitz.Point(6, 6), fitz.Point(60, 6), color=(0, 0, 0), width=0.1)
    tmp = p.with_suffix(".tmp.pdf")
    doc.save(tmp)
    doc.close()
    os.replace(tmp, p)
    return "PDF line 0.1 pt wide added"


def m_thin_line_svg(d, n, stale):
    p = _plate(d, n, "svg")
    s = p.read_text()
    i = s.rfind("</svg>")
    p.write_text(s[:i] + '<path d="M 6 6 L 60 6" style="fill: none; stroke: #000000; stroke-width: 0.1"/>\n' + s[i:])
    return "SVG path with stroke-width 0.1 pt added"


def _legend_range(phrase):
    def m(d, n, stale):
        p = d / "legend_draft.md"
        s = p.read_text()
        i = s.find("No hypothesis test")
        if i < 0:
            return None
        p.write_text(s[:i] + phrase + " " + s[i:])
        return f"legend_draft.md: {phrase!r} inserted"
    return m


MUTANTS = [("faint stamp", m_faint_stamp, {"R7"}),
           ("stale pair", m_stale, {"R8"}),
           ("stale renamed", lambda d, n, s: m_stale(d, n, s, rename=True), {"R8"}),
           ("zeroed value", m_zeroed, {"R8"}),
           ("altered label", m_altered_label, {"R10"}),
           ("added text", m_added_text, {"R7", "R10"}),
           ("colour changed", m_colour, {"R10"}),
           ("swapped labels", m_swap_labels, {"R10"}),
           ("swapped values", m_swap_values, {"R8", "R10"}),
           ("existing colour", m_existing_colour, {"R10"}),
           ("plate vs book a", lambda d, n, s: _consistent_edit(d, n, f"Fig. {n}a", "pass_rate_pct",
                                                                lambda v: v - 5 if v >= 5 else v + 5), {"R8"}),
           ("plate vs book d", lambda d, n, s: _consistent_edit(d, n, f"Fig. {n}d", "attempts_n",
                                                                lambda v: v + 1), {"R8"}),
           ("untied number", m_untied_number, {"R8"}),
           ("cells in place", lambda d, n, s: _swap_positions(d, n, "inside"), {"R8"}, "not at their place"),
           ("d n swapped", lambda d, n, s: _swap_positions(d, n, "on_row"), {"R8"}, "not at their place"),
           ("range hyphen", _legend_range("Each operation holds n = 4-5 attempts."), {"R9"}),
           ("range en dash", _legend_range("Each operation holds 4–5 attempts."), {"R9"}),
           ("range to", _legend_range("Each operation holds 4 to 5 matched attempts."), {"R9"}),
           ("range or", _legend_range("Each operation holds 4 or 5 per strategy set."), {"R9"}),
           ("range between", _legend_range("Each operation holds between 4 and 5 attempts."), {"R9"}),
           ("range fig dash", _legend_range("Each operation holds 4‒5 (matched) attempts."), {"R9"}),
           ("range minus", _legend_range("Each operation holds 4−5 runs."), {"R9"}),
           ("low contrast", m_low_contrast, {"R11"}),
           ("thin line pdf", m_thin_line_pdf, {"R12"}),
           ("thin line svg", m_thin_line_svg, {"R12"})]


FIXED_POINT = r"\{(\w+):[+]?\.\d+f\}"            # a printed number written with a fixed-point format ("{mrr:.2f}")
PLAIN_FIELD = r"\{(\w+)\}"                        # a printed whole number written as it is ("{answers_n}")


def _printed_entries(d, n):
    """The numbers file's printed entries tied to a workbook row, those with a fixed-point format first, then those
    written as a plain field (a plate printing only whole numbers, as S457's outcome table), each with its column."""
    import json
    printed = json.loads((d / side_name(n, "numbers")).read_text()).get("printed") or {}
    out = []
    for pat in (FIXED_POINT, PLAIN_FIELD):
        for gid, e in printed.items():
            m = re.search(pat, e.get("format", ""))
            if m and "row" in e:
                out.append((gid, e, m.group(1), pat == FIXED_POINT))
    return out


def m_printed_number(d, n, stale):
    """A number printed on the plate changed in the SVG only: the first digit of the first text the numbers file maps
    to a fixed-point format (else to a plain field) moved up by one (R8 (6) reads it against the workbook, R10 against
    the PDF)."""
    p = _plate(d, n, "svg")
    s = p.read_text()
    for gid, e, _, _ in _printed_entries(d, n):
        m = re.search(rf'(<g id="{gid}">\s*<text\b[^>]*>)([^<]*\d[^<]*)(</text>)', s)
        if m:
            old = m.group(2)
            new = re.sub(r"\d", lambda x: str((int(x.group(0)) + 1) % 10), old, count=1)
            p.write_text(s[:m.start(2)] + new + s[m.end(2):])
            return f"SVG text {gid} {old!r} changed to {new!r}, the plate only"
    return None


def _consistent_edit_any(d, n):
    """_consistent_edit() on the first printed entry written with a fixed-point format, that cell moved by 0.1, or
    else on the first written as a plain field, that cell moved by 1 (as "plate vs book d"; a whole number moved by
    0.1 would print the same), in the workbook and the numbers file alike (a Supplementary figure's sheets and columns
    are its own)."""
    for _, e, col, fixed in _printed_entries(d, n):
        return _consistent_edit(d, n, e["sheet"], col, (lambda v: v + 0.1) if fixed else (lambda v: v + 1))
    return None


def _svg_rehashed(fn):
    """fn, then the SVG's new sha256 recorded in the provenance file, so R8's part (3) still passes and only part (6),
    the plate against the workbook, can catch the change (review of 18 October T4)."""
    def m(d, n, stale):
        what = fn(d, n, stale)
        if what is not None:
            _rehash(d, n, [_plate(d, n, "svg").name])
            what += " (provenance re-hashed)"
        return what
    return m


# --mutants --supplementary (D94 O-b): R8's consistency parts on a Supplementary folder (no lock-key mutants: those run
# on a main figure), each with the rule that must FAIL and, where a part is targeted, the words its FAIL line must hold
SUPP_MUTANTS = [("zeroed value", m_zeroed, {"R8"}),
                ("printed number", _svg_rehashed(m_printed_number), {"R8"}, "the plate reads"),
                ("plate vs book", lambda d, n, s: _consistent_edit_any(d, n), {"R8"}, "the plate reads"),
                ("untied number", _svg_rehashed(m_untied_number), {"R8"}, "tied to no Source Data cell"),
                ("no data workbook", lambda d, n, s: _alt_no_workbook(d, n), {"R8"})]


# ---------------------------------------------------------------------------------------------------------------
# Lock-key mutants: each key FIGURE_LOCK.toml tags "S448 R<n>" is changed in a copy of the lock, and the tagged
# rule's verdict (its status lines, in order) must change. A mutant may set other keys in both copies (base), so the
# rule's verdict can move on this folder (a figure whose type fails R3 fails it whatever the panel-letter keys say), and may
# alter a copy of the folder for both runs (alter), where a key matters only on a figure that breaks its rule.
# ---------------------------------------------------------------------------------------------------------------
VALUE_SECTIONS = ("page", "type", "lines", "colour", "files", "legend", "statistics", "source_data", "display_items")


def _toml(v):
    import json
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml(x) for x in v) + "]"
    raise TypeError(v)


def lock_with(text, changes):
    """The lock's text with the line of each "section.key" replaced by key = value (its comment dropped)."""
    lines = text.splitlines()
    for sk, v in changes.items():
        sec, key = sk.split(".")
        cur, hit = "", None
        for i, ln in enumerate(lines):
            m = re.match(r"\[(\w+)\]\s*$", ln)
            if m:
                cur = m.group(1)
            elif cur == sec and re.match(rf"{re.escape(key)}\s*=", ln):
                hit = i
                break
        if hit is None:
            raise KeyError(f"no key {sk} in the lock")
        lines[hit] = f"{key} = {_toml(v)}"
    return "\n".join(lines) + "\n"


def lock_tags(text):
    """{"section.key": (rules the key's comment tags "S448 R<n>", MANUAL or not)} for every key of the value
    sections. Neither tag string occurs in a value, so the whole line is searched."""
    out, sec = {}, ""
    for ln in text.splitlines():
        m = re.match(r"\[(\w+)\]\s*$", ln)
        if m:
            sec = m.group(1)
            continue
        m = re.match(r"(\w+)\s*=", ln)
        if m and sec in VALUE_SECTIONS:
            t = re.search(r"\bS448 (R\d+(?:, R\d+)*)", ln)
            out[f"{sec}.{m.group(1)}"] = (tuple(t.group(1).split(", ")) if t else (), bool(re.search(r"\bMANUAL\b",
                                                                                                        ln)))
    return out


def _pdf_edit(d, n, fn):
    import fitz
    import os
    p = _plate(d, n, "pdf")
    doc = fitz.open(p)
    fn(doc, fitz)
    tmp = p.with_suffix(".tmp.pdf")
    doc.save(tmp)
    doc.close()
    os.replace(tmp, p)


def _alt_two_pages(d, n):
    _pdf_edit(d, n, lambda doc, fz: doc.new_page())
    return "a blank second page added to the PDF"


def _alt_unembedded(d, n):
    _pdf_edit(d, n, lambda doc, fz: doc[0].insert_text((6, 12), "x", fontname="helv", fontsize=8))
    return "a text in PDF base-14 Helvetica, not embedded, added to the PDF"


def _alt_coloured(d, n):
    _pdf_edit(d, n, lambda doc, fz: doc[0].insert_text((6, 12), "coloured label", fontsize=8,
                                                       color=(0, 0x72 / 255, 0xB2 / 255)))
    return "a text in Okabe-Ito blue #0072B2 on white added to the PDF"


def _alt_pdf_image(d, n):
    def put(doc, fz):
        pix = fz.Pixmap(fz.csRGB, fz.IRect(0, 0, 8, 8), False)
        pix.clear_with(200)
        doc[0].insert_image(fz.Rect(4, 4, 12, 12), pixmap=pix)
    _pdf_edit(d, n, put)
    return "an 8 x 8 px raster image placed in the PDF"


def _alt_svg_no_text(d, n):
    p = _plate(d, n, "svg")
    s, k = re.subn(r"<text\b.*?</text>", "", p.read_text(), flags=re.S)
    p.write_text(s)
    return f"all {k} <text> elements removed from the SVG"


def _alt_drop_panel(d, n):
    p = d / "legend_draft.md"
    s = p.read_text()
    m = re.search(r"\*\*([a-z])\*\*,", s)
    if not m:
        return None
    p.write_text(s[:m.start()] + f"{m.group(1)}," + s[m.end():])
    return f"legend_draft.md: panel {m.group(1)!r} no longer defined ('**{m.group(1)}**,' -> '{m.group(1)},')"


def _alt_drop_n(d, n):
    p = d / "legend_draft.md"
    s = p.read_text()
    new, k = re.subn(r"\bn = (?=\d)", "count ", s)
    if not k:
        return None
    p.write_text(new)
    return f"legend_draft.md: every 'n = <number>' ({k}) written as 'count <number>'"


def _alt_no_workbook(d, n):
    xs = sd_files(d, n)[0]
    for x in xs:
        x.unlink()
    return f"the Source Data workbook removed ({len(xs)} file)"


def _alt_no_caption(d, n):
    import json
    caps = sd_files(d, n)[2]
    pf = d / side_name(n, "provenance")
    pj = json.loads(pf.read_text())
    for c in caps:
        c.unlink()
        pj.get("files", {}).pop(c.name, None)
    pf.write_text(json.dumps(pj, indent=1))
    return f"the Source Data caption removed, and from the provenance file ({len(caps)} file)"


def _alt_as_supplementary(d, n):
    """The plate's files renamed from [files] name to [files] supplementary_name (suffix and extension kept); the
    lock mutant then checks the copy as a Supplementary figure (--supplementary), in both runs."""
    figs, pat = find_files(d, n)
    if not figs:
        return None
    new = SUPP_NAME_TMPL.format(n=n)
    for p in figs:
        p.rename(p.with_name(new + p.name[len(plate_name(n)):]))
    return f"the plate's {len(figs)} files renamed to {new!r} and checked as a Supplementary figure"


ALTER = {"as supplementary": _alt_as_supplementary, "two pages": _alt_two_pages, "unembedded font": _alt_unembedded, "coloured text": _alt_coloured,
         "pdf image": _alt_pdf_image, "svg no text": _alt_svg_no_text, "drop panel": _alt_drop_panel,
         "drop n": _alt_drop_n, "no workbook": _alt_no_workbook, "no caption": _alt_no_caption,
         "faint stamp": lambda d, n: m_faint_stamp(d, n, None),
         "range hyphen": lambda d, n: _legend_range("Each operation holds n = 4-5 attempts.")(d, n, None),
         "range to": lambda d, n: _legend_range("Each operation holds 4 to 5 matched attempts.")(d, n, None)}
_ALL_FONT_TYPES = ["Type0", "Type1", "Type1C", "MMType1", "TrueType", "Type3", "CIDFontType0", "CIDFontType2"]


def lock_mutants(W):
    """(key, value in the mutant copy, base set in both copies, folder alteration or None). W: the plate's width in
    mm, so R2's base can make the width pass."""
    r2 = {"page.width_double_mm": W, "page.height_max_mm": 1000.0}
    r3 = {"type.font_min_pt": 1.0, "type.font_max_pt": 100.0}
    r4 = {"type.font_families": [""], "type.font_types_refused": [], "type.fonts_embedded": False}
    r6 = {"colour.red_hue_deg": [345.0, 30.0], "colour.green_hue_deg": [80.0, 170.0]}
    return [
        ("files.name", "Fig. {n}", {}, None),
        ("files.supplementary_name", "Supp. Fig. {n}", {}, "as supplementary"),
        ("files.plate_files", ["pdf", "svg", "png|tif|tiff", "eps"], {}, None),
        ("files.file_max_mb", 1e-6, {}, None),
        ("page.one_page", False, {}, "two pages"),
        ("page.width_double_mm", W + 10.0, r2, None),
        ("page.width_single_mm", W, {**r2, "page.width_double_mm": W + 10.0}, None),
        ("page.width_tol_mm", 2.0, {**r2, "page.width_double_mm": W + 1.0}, None),
        ("page.height_max_mm", 1.0, r2, None),
        ("files.upload_format", "png", {**r2, "files.raster_dpi_min": 100000}, None),
        ("files.raster_dpi_min", 100000, {**r2, "files.upload_format": "png", "files.raster_dpi_min": 1}, None),
        ("type.font_min_pt", 99.0, r3, None),
        ("type.font_max_pt", 1.5, r3, None),
        ("type.panel_letter_pt", 20.0, r3, None),
        ("type.panel_letter_weight", "normal", r3, None),
        ("type.panel_letter_case", "uppercase", r3, None),
        ("type.panel_letter_style", "italic", r3, None),
        ("type.text_as_text", False, r3, "svg no text"),
        ("type.font_families", ["NoSuchFont"], r4, None),
        ("type.font_types_refused", _ALL_FONT_TYPES, r4, None),
        ("type.fonts_embedded", True, r4, "unembedded font"),
        ("type.contrast_min_ratio", 22.0, {"type.contrast_min_ratio": 1.0}, None),
        ("type.coloured_text", "allowed", {"type.contrast_min_ratio": 1.0}, "coloured text"),
        ("lines.line_min_pt", 100.0, {"lines.line_min_pt": 0.0}, None),
        ("colour.categorical", ["#000000"], {}, None),
        ("colour.continuous", "viridis", {}, None),
        ("colour.continuous_tol", 255, {"colour.continuous": "viridis"}, None),
        ("colour.grey_tol", -1, {}, None),
        ("colour.vector_only", False, {}, "pdf image"),
        ("colour.red_hue_deg", [345.0, 30.0], {"colour.green_hue_deg": [80.0, 170.0]}, None),
        ("colour.green_hue_deg", [80.0, 170.0], {"colour.red_hue_deg": [345.0, 30.0]}, None),
        ("colour.saturated_min", 1.01, r6, None),
        ("colour.value_min", 1.01, r6, None),
        ("files.forbidden_text", ".", {}, None),
        ("files.raster_delta", 255, {}, "faint stamp"),
        ("source_data.per_main_figure", False, {}, "no workbook"),
        ("source_data.formats", ["csv"], {}, None),
        ("source_data.workbook_name", "Source Data Figure {n}.xlsx", {}, None),
        ("source_data.caption", False, {}, "no caption"),
        ("legend.words_under", 1, {"legend.words_under": 100000}, None),
        ("legend.title_panel_re", ".", {}, None),
        ("legend.panels_defined", False, {}, "drop panel"),
        ("statistics.n_exact", False, {}, "range hyphen"),
        ("statistics.n_range_dashes", "\u2013", {}, "range hyphen"),   # the en dash alone
        ("statistics.n_count_words", ["zzzz"], {}, "range to"),
        ("statistics.sidedness_phrase", "zzzz-sided", {}, None),
        ("statistics.sidedness_when", "(?!)", {"statistics.sidedness_phrase": "zzzz-sided"}, None),   # matches nothing
        ("statistics.n_when", "(?!)", {}, "drop n"),   # matches nothing: a legend without n then passes the n check
    ]


def _run_lock(text, folder, n, supp=False):
    """check() on folder under a copy of the lock holding text (as a Supplementary figure when supp); the agreed lock
    and the figure kind are restored after. Returns the (rule, status) list and the printed lines."""
    import contextlib
    import io
    import tempfile
    global SUPP
    was = SUPP
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "FIGURE_LOCK.toml"
        p.write_text(text)
        lk, sha = load_lock(p)
        try:
            apply_lock(lk, p, sha)
            SUPP = supp
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                check(folder, n, quiet=True)
            return list(RESULTS), buf.getvalue().splitlines()
        finally:
            SUPP = was
            apply_lock(*AGREED)


def lock_key_mutants(d: Path, n: int):
    """Every key the lock tags S448 changed once; returns (caught, missed, problems of coverage)."""
    import fitz
    import shutil
    import tempfile
    text = LOCK_PATH.read_text()
    tags = lock_tags(text)
    apply_lock(*AGREED)
    read = set(READ)
    figs, _ = find_files(d, n)
    pdf = next((p for p in figs if p.suffix.lower() == ".pdf"), None)
    if pdf is None:
        print("lock mutants SKIPPED: no PDF of the plate")
        return 0, 0, ["no PDF to measure"]
    r = fitz.open(pdf)[0].rect
    W = round(r.width * 25.4 / 72, 3)
    muts = lock_mutants(W)
    caught = missed = 0
    cache = {}
    print(f"\nlock-key mutants (each tagged key changed in a copy of {LOCK_PATH.name}; the tagged rule's verdict, "
          f"its status lines in order, must change):")
    with tempfile.TemporaryDirectory() as t:
        for key, val, base, alter in muts:
            rules = tags.get(key, ((), False))[0]
            folder, what = d, ""
            if alter:
                folder = Path(t) / alter.replace(" ", "_") / d.name
                if not folder.exists():
                    shutil.copytree(d, folder)
                    if ALTER[alter](folder, n) is None:
                        print(f"lock {key:30s} SKIPPED: the folder alteration {alter!r} found nothing to alter")
                        missed += 1
                        continue
                what = f"; folder: {alter}"
            ck = (repr(sorted(base.items())), alter)
            supp = alter == "as supplementary"
            if ck not in cache:
                cache[ck] = _run_lock(lock_with(text, base), folder, n, supp)
            res_a, out_a = cache[ck]
            res_b, out_b = _run_lock(lock_with(text, {**base, key: val}), folder, n, supp)
            va = {r_: tuple(s_ for x, s_ in res_a if x == r_) for r_ in rules}
            vb = {r_: tuple(s_ for x, s_ in res_b if x == r_) for r_ in rules}
            ok = bool(rules) and any(va[r_] != vb[r_] for r_ in rules)
            extra = ""
            if key == "files.file_max_mb":         # D2: a file over the limit FAILs R1 and the other rules still run
                ran = sorted({x for x, _ in res_b if re.fullmatch(r"R\d+", x)} - {"R1"}, key=lambda x: (len(x), x))
                ok = ok and "R12" in ran
                extra = f"; rules run after R1's size FAIL: {', '.join(ran) or 'none'}"
            caught += ok
            missed += not ok
            fmt = lambda v: "/".join(v[r_] and ",".join(v[r_]) or "none" for r_ in rules) if rules else "untagged"
            print(f"lock {key:30s} {'CAUGHT' if ok else 'MISSED'}: {_toml(val)[:40]}; {'/'.join(rules) or '-'} "
                  f"{fmt(va)} -> {fmt(vb)}" + (f"; base {', '.join(f'{k}={_toml(v)[:24]}' for k, v in base.items())}"
                                               if base else "") + what + extra)
            if ok:
                ln = next((x for x in out_b if x.split()[:1] and x.split()[0] in rules and x.split()[1] in
                           ("FAIL", "WARN", "INFO")), None)
                if ln:
                    print(f"    {ln[:300]}")
    # coverage: what the lock tags, what S448 reads and what a mutant proves are one set
    tagged = {k for k, (r_, _) in tags.items() if r_}
    manual = {k for k, (_, m) in tags.items() if m}
    proved = {k for k, *_ in muts}
    probs = []
    for label, a, b in (("tagged S448 but not read", tagged, read), ("read but not tagged S448", read, tagged),
                        ("tagged S448 but no mutant", tagged, proved), ("a mutant but not tagged S448", proved, tagged)):
        if a - b:
            probs.append(f"{label}: {sorted(a - b)}")
    untagged = sorted(set(tags) - tagged - manual)
    if untagged:
        probs.append(f"neither tagged S448 nor MANUAL: {untagged}")
    both = sorted(tagged & manual)
    if both:
        probs.append(f"tagged both S448 and MANUAL: {both}")
    print(f"\nlock coverage: {len(tags)} keys in the value sections, {len(tagged)} tagged S448, {len(manual)} MANUAL; "
          f"S448 reads {len(read)}; {len(proved)} lock mutants: " + ("; ".join(probs) if probs else
                                                                     "the keys tagged S448, read and proved are one "
                                                                     "set, and every other key is MANUAL"))
    return caught, missed, probs


def mutants(d: Path, n: int, stale):
    import contextlib
    import io
    import shutil
    import tempfile
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        clean = check(d, n)
    print(buf.getvalue(), end="")
    clean_lines = {ln.split()[0]: ln for ln in buf.getvalue().splitlines() if ln.split()[1:2] == ["FAIL"]}
    print(f"\nclean: {'FAIL ' + ', '.join(clean) if clean else 'every automatic rule PASSES'}")
    bad = bool(clean)
    tally = {"CAUGHT": 0, "MISSED": 0, "SKIPPED": 0}
    folder_mutants = SUPP_MUTANTS if SUPP else MUTANTS
    for name, fn, want, *say_ in folder_mutants:
        with tempfile.TemporaryDirectory() as t:
            m = Path(t) / d.name
            shutil.copytree(d, m)
            what = fn(m, n, stale)
            if what is None:
                print(f"mutant {name:16s} SKIPPED (needs --stale-from)" if name.startswith("stale") else
                      f"mutant {name:16s} SKIPPED (nothing to alter)")
                tally["SKIPPED"] += 1
                bad = True
                continue
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                fails = check(m, n, quiet=True)
            lines = {ln.split()[0]: ln for ln in buf.getvalue().splitlines() if ln.split()[1:2] == ["FAIL"]}
            # a rule that already FAILs on the clean folder counts only when its FAIL line changed: the mutant was
            # seen, not merely a failure that was there before
            moved = all(r not in clean_lines or lines.get(r) != clean_lines[r] for r in want)
            caught = want <= set(fails) and all(say_[0] in lines.get(r, "") for r in want if say_) and moved
            tally["CAUGHT" if caught else "MISSED"] += 1
            bad |= not caught
            pre = sorted(r for r in want if r in clean_lines)
            print(f"mutant {name:16s} {'CAUGHT' if caught else 'MISSED'}: {what}; FAIL {', '.join(fails) or 'none'} "
                  f"(want {', '.join(sorted(want))}" + (f", saying {say_[0]!r}" if say_ else "") + ")" +
                  (f"; {', '.join(pre)} already FAILs on the clean folder, its FAIL line "
                   f"{'changed' if moved else 'unchanged'}" if pre else ""))
            for r in sorted(want):
                if r in lines:
                    print(f"    {lines[r][:400]}")
    print(f"\nfolder mutants: {tally['CAUGHT']} of {len(folder_mutants)} caught, {tally['MISSED']} missed, "
          f"{tally['SKIPPED']} skipped")
    if SUPP:                                # the lock keys are proved on a main figure (D94 O-b)
        print(f"\nmutants (a Supplementary figure, SUPP_MUTANTS; no lock-key mutants): folder {tally['CAUGHT']} of "
              f"{len(folder_mutants)} caught, {tally['MISSED']} missed, {tally['SKIPPED']} skipped; the clean folder "
              f"{'FAILS ' + ', '.join(clean) if clean else 'passes'}: " + ("every mutant caught" if not bad else "FAILED"))
        return not bad
    lc, lm, cov = lock_key_mutants(d, n)
    bad |= bool(lm) or bool(cov)
    print(f"\nmutants: folder {tally['CAUGHT']} of {len(MUTANTS)} caught, {tally['MISSED']} missed, {tally['SKIPPED']} "
          f"skipped; lock keys {lc} of {lc + lm} caught; lock coverage {'complete' if not cov else 'INCOMPLETE'}; "
          f"the clean folder {'FAILS ' + ', '.join(clean) if clean else 'passes'}: "
          + ("every mutant caught" if not bad else "FAILED"))
    return not bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--figure", type=int, required=True)
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--mutants", action="store_true", help="check the checker on altered copies (nothing written)")
    ap.add_argument("--stale-from", type=Path, help="--mutants: a folder of the figure at another data state")
    ap.add_argument("--supplementary", action="store_true",
                    help="--figure is a Supplementary figure: files named by [files] supplementary_name, the drawing "
                         "rules (R1 finds the files by that name; D92 Q194) and R8's consistency parts (2) to (6) on "
                         "its data workbook (D94 O-b); with --mutants, SUPP_MUTANTS only")
    a = ap.parse_args(argv)
    global SUPP
    SUPP = a.supplementary
    if a.mutants:
        sys.exit(0 if mutants(a.dir, a.figure, a.stale_from) else 1)
    fails = check(a.dir, a.figure)
    print(f"\n{'FAIL: ' + ', '.join(fails) if fails else 'every automatic rule PASSES'}"
          f" ({sum(1 for _, st in RESULTS if st == 'WARN')} warning(s), "
          f"{sum(1 for _, st in RESULTS if st == 'MANUAL')} rules for a person)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
